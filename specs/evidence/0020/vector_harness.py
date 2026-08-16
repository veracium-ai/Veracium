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
- closure:         (R7-1/R8-1) {"survivor": id, "record": {...},
                    "op_state": s, "ledger_rows": {id: [rows]},
                    "legacy_links": {id: [ids]}?, "legacy_digests":
                    {id: identity-source|null}?}; rows may carry
                    "contributor_ref" and "flattened"; a None closure is
                   UNRESOLVED by contract before membership runs;
                   expect = {"digest_of": id} | "SHARED_POOL" | "UNRESOLVED"
- reconstruction:  (R7-2/R8-3) {"records": [...], "id_remap": {}|null,
                    "op_key": str = the minted import op id}; records carry
                   raw origin/source_id/evidence_ref;
                   expect = {"rows": {survivor: [digest-source|null]}}
                          | "ImportLinkageError" | "PolicyError"
                   (the harness ALSO structurally checks every emitted row:
                   per-row canonical op_key, contributor_ref, payload)
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
                             UNRESOLVED, apply_filters, classify,
                             close_absorption_rows, digest_of,
                             ImportLinkageError, membership,
                             reconstruct_absorption_rows, same_identity,
                             validate_filters, validate_policy, ScopePolicy)

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
        from reference_scope import classify as _cl, digest_of as _dg
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
            elif a == "inconsistent_digest_map":
                # R4-1 (executed by the reviewer): canonical-LOOKING groups
                # with a digest map claiming B is in A's group — the
                # construction may pass shape checks; CONSUMPTION must refuse
                from types import MappingProxyType
                ok = validate_policy({"ga": [I(A1)]}, False,
                                     local_origin=LOCAL)
                forged = ScopePolicy(
                    groups=ok.groups, cross_scope_visible=False,
                    group_digests=MappingProxyType(
                        {"ga": frozenset({_dg(I(A1), LOCAL),
                                          _dg(I({"origin": "org-b",
                                                 "source_id": "agent-9"}),
                                              LOCAL)})}),
                    seal=ok.seal)
                _cl(_dg(I({"origin": "org-b", "source_id": "agent-9"}),
                        LOCAL), I(A1), forged, LOCAL)
            elif a == "backing_map_mutation":
                from types import MappingProxyType
                ok = validate_policy({"ga": [I(A1)]}, False,
                                     local_origin=LOCAL)
                backing = {"ga": ok.groups["ga"]}
                mutated = ScopePolicy(groups=MappingProxyType(backing),
                                      cross_scope_visible=False,
                                      group_digests=ok.group_digests,
                                      seal=ok.seal)
                backing["gb"] = (I(A2),)          # mutate AFTER construction
                _cl(_dg(I(A2), LOCAL), I(A1), mutated, LOCAL)
            elif a == "resign_after_flip":
                # ROUND-5's executed attack VERBATIM: flip the bool AND
                # re-sign with the module's own _seal — the registry, not
                # the seal, is the authority, so this must still refuse
                import reference_scope as _rs
                ok = validate_policy({"ga": [I(A1)]}, False,
                                     local_origin=LOCAL)
                object.__setattr__(ok, "cross_scope_visible", True)
                object.__setattr__(ok, "seal",
                                   _rs._seal(dict(ok.groups), True, LOCAL))
                _cl(_dg(I({"origin": "org-b", "source_id": "agent-9"}),
                        LOCAL), I(A1), ok, LOCAL)
            elif a == "setattr_flip":
                ok = validate_policy({"ga": [I(A1)]}, False,
                                     local_origin=LOCAL)
                object.__setattr__(ok, "cross_scope_visible", True)
                _cl(_dg(I({"origin": "org-b", "source_id": "agent-9"}),
                        LOCAL), I(A1), ok, LOCAL)
            elif a == "leaf_identity_mutation":
                # ROUND-7 (R7-4): mutate an Identity LEAF shared through
                # the policy. v8's snapshot held the SAME instances, so
                # this mutated both references; v9's snapshot is primitive
                # strings — assert that structurally, THEN prove the
                # mutated policy refuses at consumption.
                import reference_scope as _rs
                ok = validate_policy({"ga": [I(A1)]}, False,
                                     local_origin=LOCAL)
                snap_groups = _rs._REGISTRY[ok][0]
                for _name, _members in snap_groups:
                    for _leaf in _members:
                        assert isinstance(_leaf, tuple) and all(
                            isinstance(p, (str, type(None))) for p in _leaf), \
                            "registry snapshot leaks non-primitive leaves"
                member = ok.groups["ga"][0]
                object.__setattr__(member, "source_id", "agent-evil")
                _cl(_dg(I(A1), LOCAL), I(A1), ok, LOCAL)
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
    if kind == "closure":
        def _rows(rr):
            out = []
            for x in rr:
                row = {"site": x["site"],
                       "identity_digest": (digest_of(I(x["identity"]), LOCAL)
                                           if x.get("identity") else None),
                       "op_key": x.get("op_key")}
                if "contributor_ref" in x:
                    row["contributor_ref"] = x["contributor_ref"]
                if x.get("flattened"):
                    row["payload"] = {"flattened": True}
                out.append(row)
            return out
        ledger = {k: _rows(rw) for k, rw in v["ledger_rows"].items()}
        links = {k: tuple(ids)
                 for k, ids in v.get("legacy_links", {}).items()}
        digs = {k: (digest_of(I(x), LOCAL) if x else None)
                for k, x in v.get("legacy_digests", {}).items()}
        closed = close_absorption_rows(v["survivor"], ledger, links, digs)
        # the contract: a None closure IS UNRESOLVED, before membership runs
        got = (UNRESOLVED if closed is None
               else membership(v["record"], closed, v["op_state"], LOCAL))
        if isinstance(expect, dict):
            want = digest_of(I(expect["digest_of"]), LOCAL)
            return None if got == want else f"got {got!r}"
        want = {"SHARED_POOL": SHARED, "UNRESOLVED": UNRESOLVED}[expect]
        return None if got == want else f"got {got!r}"
    if kind == "reconstruction":
        def build():
            return reconstruct_absorption_rows(
                v["records"], LOCAL, id_remap=v.get("id_remap"),
                import_op=v["op_key"])
        if expect in ("ImportLinkageError", "PolicyError"):
            try:
                build()
                return f"expected {expect}, none raised"
            except ImportLinkageError:
                return None if expect == "ImportLinkageError" else \
                    "ImportLinkageError raised where plain PolicyError expected"
            except PolicyError:
                # ImportLinkageError subclasses PolicyError; reaching here
                # means a NON-linkage PolicyError (e.g. the import_op rule)
                return None if expect == "PolicyError" else \
                    "PolicyError raised where ImportLinkageError expected"
        got = build()
        want = {s: sorted(((digest_of(I(x), LOCAL) if x else None)
                           for x in dl), key=lambda z: z or "")
                for s, dl in expect["rows"].items()}
        norm = {s: sorted((r["identity_digest"] for r in rows),
                          key=lambda z: z or "")
                for s, rows in got.items()}
        if norm != want:
            return f"got {norm!r}, expected {want!r}"
        # R8-3/R9-2: STRUCTURAL total-row check — per-row INJECTIVE op
        # keys (the framed-digest form recomputed independently), typed
        # contributor_ref, the closed payload, and the cross-field
        # validator green on every row
        from reference_scope import import_row_op_key, validate_row_plan
        seen_keys = set()
        for surv, rows in got.items():
            for r in rows:
                want_key = import_row_op_key(v["op_key"], surv,
                                             r.get("contributor_ref") or "")
                try:
                    validate_row_plan(r)
                except PolicyError as e:
                    return f"emitted row fails its own validator: {e}"
                if (r["site"] != "imported-absorption"
                        or r.get("contributor_ref") is None
                        or r["op_key"] != want_key
                        or r["op_key"] in seen_keys
                        or not (r.get("payload") or {}).get("reconstructed")):
                    return f"row not fully populated/canonical: {r!r}"
                seen_keys.add(r["op_key"])
        return None
    if kind == "derivation":
        # R9-1: the exact reverse-link algorithm, with the retention
        # contract's prune-time reparenting applied in order
        from reference_scope import (derive_absorbed_by,
                                     prune_absorbed_record,
                                     ExportLinkageError)
        def _rows(rr):
            out = []
            for x in rr:
                row = {"site": x.get("site", "absorption"),
                       "identity_digest": (digest_of(I(x["identity"]), LOCAL)
                                           if x.get("identity") else None),
                       "op_key": x.get("op_key"),
                       "evidence_ref_digest": None,
                       "contributor_ref": x.get("contributor_ref"),
                       "payload": x.get("payload", {})}
                out.append(row)
            return out
        ledger = {k: _rows(rw) for k, rw in v["ledger_rows"].items()}
        try:
            for pid in v.get("prune", []):
                ledger = prune_absorbed_record(pid, ledger)
            got = derive_absorbed_by(v["query"], ledger)
        except ExportLinkageError:
            return (None if expect == "ExportLinkageError"
                    else "ExportLinkageError raised unexpectedly")
        if expect == "ExportLinkageError":
            return "expected ExportLinkageError, none raised"
        return None if got == expect else f"got {got!r}, expected {expect!r}"
    if kind == "row_identity":
        # R9-3: THE ONE canonical logical-row projection — semantic drift
        # must change the id; contradictory rows must refuse
        from reference_scope import plan_row_id
        def build(which):
            return plan_row_id(v.get("user", "u1"), "edge",
                               v.get("survivor", "S"), v[which])
        if expect == "PolicyError":
            return _expect_err(lambda: build("a"))
        ida, idb = build("a"), build("b")
        if expect == "differ":
            return None if ida != idb else "ids EQUAL under semantic drift"
        return None if ida == idb else "ids differ for the same logical row"
    if kind == "op_key_injective":
        # R9-2: delimiter-bearing ids must not collide
        from reference_scope import import_row_op_key
        keys = [import_row_op_key(v["op"], s, c) for s, c in v["cases"]]
        return (None if len(set(keys)) == len(keys)
                else f"COLLISION among {keys!r}")
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
