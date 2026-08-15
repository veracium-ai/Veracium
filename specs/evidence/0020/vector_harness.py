"""specs/0020 — the SELF-EXECUTING vector harness (external round 3's
artifact ask). Loads `vectors.json`, executes every vector against
`reference_scope.py`, and reports; the seal runs it and records the result
(`vector_harness_result.txt` ships in the package).

Vector schema, per kind (every vector: {"name", "kind", "expect", ...}):
- classify:        {"principal": id|null, "policy": key|null,
                    "evidence": digest-source | "SHARED_POOL" | "UNRESOLVED"}
                   where digest-source = {"origin","source_id"} digested at
                   run time; expect = classification | "PolicyError"
- same_identity:   {"a": id, "b": id}; expect = bool
- validate_policy: {"groups": {...}, "cross_scope_visible": any,
                    "member_container": "list"|"set"?}; expect = "ok"|"PolicyError"
- direct_construction: {"attempt": named-case}; expect = "PolicyError"
- mutation_oracle: {"attempts": [...]}; expect = "all-refused"
- membership:      {"record": {...}, "rows": [...]|"none",
                    "expected_contributors": int|null, "op_state": s};
                   expect = {"digest_of": id} | "SHARED_POOL" | "UNRESOLVED"
                          | "PolicyError"
- validate_filters:{"filters": {...}}; expect = "ok"|"PolicyError"
- apply_filters:   {"records": [...], "filters": {...}}; expect = "first-only"
- shared_pool_key: {}; expect = the reserved literal (collision-checked)

Identities in vectors are {"origin": str|null, "source_id": str|null};
policies are named keys resolved by the harness (the POLICIES table below)
so vectors stay JSON-pure.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from reference_scope import (Identity, PolicyError, SHARED, SHARED_POOL_KEY,  # noqa: E402
                             UNRESOLVED, apply_filters, classify, digest_of,
                             membership, same_identity, validate_filters,
                             validate_policy, ScopePolicy)

LOCAL = "org-local-1234"
A1 = {"origin": "org-a", "source_id": "agent-1"}
A2 = {"origin": "org-a", "source_id": "agent-2"}


def I(d):
    return Identity(**d)


def _policies():
    g = {"team-a": [I(A1), I(A2)]}
    return {
        "policy": validate_policy(dict(g), False, local_origin=LOCAL),
        "policy_xv": validate_policy(dict(g), True, local_origin=LOCAL),
        "empty": validate_policy({}, False, local_origin=LOCAL),
    }


def _evidence(v):
    ev = v["evidence"]
    if ev in (UNRESOLVED, SHARED):
        return ev
    return digest_of(I(ev), LOCAL)


def run(vectors_path=None):
    vectors = json.loads((vectors_path or HERE / "vectors.json").read_text())
    policies = _policies()
    failures = []
    for v in vectors:
        try:
            got = _run_one(v, policies)
        except AssertionError as e:
            failures.append((v["name"], str(e)))
            continue
        if got is not None:
            failures.append((v["name"], got))
    return len(vectors), failures


def _expect_err(fn):
    try:
        fn()
        return "expected PolicyError, none raised"
    except PolicyError:
        return None


def _run_one(v, policies):
    kind, expect = v["kind"], v["expect"]
    if kind == "classify":
        pr = None if v["principal"] is None else I(v["principal"])
        pol = None if v["policy"] is None else policies[v["policy"]]
        if expect == "PolicyError":
            return _expect_err(lambda: classify(_evidence(v), pr, pol, LOCAL))
        got = classify(_evidence(v), pr, pol, LOCAL)
        return None if got == expect else f"got {got}, expected {expect}"
    if kind == "same_identity":
        got = same_identity(I(v["a"]), I(v["b"]), LOCAL)
        return None if got is expect else f"got {got}"
    if kind == "validate_policy":
        def build():
            groups = {}
            for name, members in v["groups"].items():
                ids = [I(m) for m in members]
                groups[name] = (set(ids) if v.get("member_container") == "set"
                                else ids)
            validate_policy(groups, v["cross_scope_visible"],
                            local_origin=LOCAL)
        if expect == "PolicyError":
            return _expect_err(build)
        build()
        return None
    if kind == "direct_construction":
        a = v["attempt"]
        def attempt():
            if a == "raw_dict_groups":
                ScopePolicy(groups={"t": [I(A1)]}, cross_scope_visible=False,
                            group_digests={})
            elif a == "string_bool":
                ok = validate_policy({"t": [I(A1)]}, False, local_origin=LOCAL)
                ScopePolicy(groups=ok.groups, cross_scope_visible="false",
                            group_digests=ok.group_digests)
            elif a == "list_members_in_canonical_slot":
                ok = validate_policy({"t": [I(A1)]}, False, local_origin=LOCAL)
                from types import MappingProxyType
                ScopePolicy(groups=MappingProxyType({"t": [I(A1)]}),
                            cross_scope_visible=False,
                            group_digests=ok.group_digests)
            else:
                raise AssertionError(f"unknown attempt {a}")
        return _expect_err(attempt)
    if kind == "mutation_oracle":
        pol = policies["policy"]
        refused = 0
        try: pol.groups["x"] = ()
        except TypeError: refused += 1
        try: pol.groups["team-a"] += (I(A1),)
        except TypeError: refused += 1
        try: object.__setattr__; pol.cross_scope_visible = True
        except Exception: refused += 1
        return None if refused == 3 else f"only {refused}/3 refused"
    if kind == "membership":
        rows = None if v["rows"] == "none" else v["rows"]
        if expect == "PolicyError":
            return _expect_err(lambda: membership(
                v["record"], rows, v["op_state"], LOCAL,
                expected_contributors=v.get("expected_contributors")))
        got = membership(v["record"], rows, v["op_state"], LOCAL,
                         expected_contributors=v.get("expected_contributors"))
        if isinstance(expect, dict):
            want = digest_of(I(expect["digest_of"]), LOCAL)
            return None if got == want else f"got {got!r}"
        want = {"SHARED_POOL": SHARED, "UNRESOLVED": UNRESOLVED}[expect]
        return None if got == want else f"got {got!r}"
    if kind == "validate_filters":
        if expect == "PolicyError":
            return _expect_err(lambda: validate_filters(v["filters"]))
        validate_filters(v["filters"])
        return None
    if kind == "apply_filters":
        got = apply_filters(v["records"], v["filters"])
        return (None if got == v["records"][:1]
                else f"got {len(got)} records")
    if kind == "shared_pool_key":
        ok = (SHARED_POOL_KEY == expect
              and not re.fullmatch(r"[0-9a-f]{64}", SHARED_POOL_KEY))
        return None if ok else "reserved key collides with digest space"
    return f"unknown vector kind {kind!r}"


if __name__ == "__main__":
    total, failures = run()
    if failures:
        for name, why in failures:
            print(f"FAIL {name}: {why}")
        sys.exit(1)
    print(f"vector harness: {total}/{total} pass against reference_scope.py")
