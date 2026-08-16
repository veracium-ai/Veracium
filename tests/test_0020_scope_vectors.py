"""specs/0020 V10 — `test_scope_reference_vectors`: THE SHIPPED SURFACE
matches the normative reference on EVERY pinned vector.

`specs/evidence/0020/vector_harness.py` executes
`specs/evidence/0020/vectors.json` against the REFERENCE
(`reference_scope.py`). This module executes THE SAME FILE against the
SHIPPED implementation (`veracium.scope` + `veracium.scope_linkage`),
reproducing the harness's per-kind dispatch exactly — same policies table,
same local origin, same expectation decoding. Two independent executions
of one vector file are what binds production to the reference; a
divergence surfaces as a failing vector here while the harness stays
green.

Tests may import from `specs/`; PRODUCTION NEVER DOES — nothing under
`src/` imports this file's fixtures, and the dispatch below reaches only
`veracium.*`.

TOTALITY (the point of V10, not a nicety): `_dispatch` REFUSES a vector
whose kind has no shipped-surface handler, and
`test_every_vector_executes_against_the_shipped_surface` asserts the
EXECUTED count equals the vector file's length. A vector added to the
file that production does not satisfy therefore fails; it cannot be
silently skipped, and neither can a whole new vector KIND.
"""

from __future__ import annotations

import json
import pathlib
import re
from types import MappingProxyType

import pytest

from veracium import scope
from veracium.scope import (SHARED, SHARED_POOL_KEY, SITE_ATTRIBUTION,
                            UNRESOLVED, Identity, ImportLinkageError,
                            ScopeError, ScopePolicy, apply_filters, classify,
                            close_absorption_rows, digest_of,
                            derive_absorbed_by, ExportLinkageError,
                            import_row_op_key, membership,
                            native_row_op_key, plan_row_id,
                            prune_absorbed_record,
                            reconstruct_absorption_rows, row_op_key,
                            same_identity, validate_filters, validate_policy,
                            validate_row_plan)

VECTORS_PATH = (pathlib.Path(__file__).resolve().parents[1] / "specs" /
                "evidence" / "0020" / "vectors.json")
VECTORS = json.loads(VECTORS_PATH.read_text())

#: the harness's own constants, verbatim — the vectors are written against
#: exactly these
LOCAL = "org-local-1234"
A1 = {"origin": "org-a", "source_id": "agent-1"}
A2 = {"origin": "org-a", "source_id": "agent-2"}


def I(d):                                                     # noqa: E743
    return Identity(**d)


def _policies():
    """The harness's POLICIES table, built fresh per test so a vector that
    mutates a policy (the direct-construction attacks) cannot leak into
    another vector's inputs."""
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


def _expect_err(fn):
    """The harness's refusal probe, against the SHIPPED error class —
    `ScopeError` IS the reference's `PolicyError` (one class, two
    names)."""
    try:
        fn()
        return "expected ScopeError, none raised"
    except ScopeError:
        return None


def _want_membership(expect, got):
    if isinstance(expect, dict):
        want = digest_of(I(expect["digest_of"]), LOCAL)
        return None if got == want else f"got {got!r}, expected {want!r}"
    want = {"SHARED_POOL": SHARED, "UNRESOLVED": UNRESOLVED}[expect]
    return None if got == want else f"got {got!r}, expected {want!r}"


# ---- the per-kind handlers (the harness's dispatch, shipped-side) ----------

def _k_classify(v, policies):
    pr = None if v["principal"] is None else I(v["principal"])
    pol = None if v["policy"] is None else policies[v["policy"]]
    expect = v["expect"]
    if expect == "PolicyError":
        return _expect_err(lambda: classify(_evidence(v), pr, pol, LOCAL))
    got = classify(_evidence(v), pr, pol, LOCAL)
    return None if got == expect else f"got {got}, expected {expect}"


def _k_same_identity(v, policies):
    got = same_identity(I(v["a"]), I(v["b"]), LOCAL)
    return None if got is v["expect"] else f"got {got}"


def _k_validate_policy(v, policies):
    def build():
        groups = {}
        for name, members in v["groups"].items():
            ids = [I(m) for m in members]
            groups[name] = (set(ids) if v.get("member_container") == "set"
                            else ids)
        validate_policy(groups, v["cross_scope_visible"], local_origin=LOCAL)
    if v["expect"] == "PolicyError":
        return _expect_err(build)
    build()
    return None


def _k_direct_construction(v, policies):
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
            ScopePolicy(groups=MappingProxyType({"t": [I(A1)]}),
                        cross_scope_visible=False,
                        group_digests=ok.group_digests)
        elif a == "inconsistent_digest_map":
            # canonical-LOOKING groups with a digest map claiming B is in
            # A's group — construction may pass shape checks; CONSUMPTION
            # must refuse
            ok = validate_policy({"ga": [I(A1)]}, False, local_origin=LOCAL)
            forged = ScopePolicy(
                groups=ok.groups, cross_scope_visible=False,
                group_digests=MappingProxyType(
                    {"ga": frozenset({digest_of(I(A1), LOCAL),
                                      digest_of(I({"origin": "org-b",
                                                   "source_id": "agent-9"}),
                                                LOCAL)})}),
                seal=ok.seal)
            classify(digest_of(I({"origin": "org-b",
                                  "source_id": "agent-9"}), LOCAL),
                     I(A1), forged, LOCAL)
        elif a == "backing_map_mutation":
            ok = validate_policy({"ga": [I(A1)]}, False, local_origin=LOCAL)
            backing = {"ga": ok.groups["ga"]}
            mutated = ScopePolicy(groups=MappingProxyType(backing),
                                  cross_scope_visible=False,
                                  group_digests=ok.group_digests,
                                  seal=ok.seal)
            backing["gb"] = (I(A2),)          # mutate AFTER construction
            classify(digest_of(I(A2), LOCAL), I(A1), mutated, LOCAL)
        elif a == "resign_after_flip":
            # the round-5 executed attack VERBATIM: flip the bool AND
            # re-sign with the module's OWN _seal — the registry, not the
            # seal, is the authority, so this must STILL refuse
            ok = validate_policy({"ga": [I(A1)]}, False, local_origin=LOCAL)
            object.__setattr__(ok, "cross_scope_visible", True)
            object.__setattr__(ok, "seal",
                               scope._seal(dict(ok.groups), True, LOCAL))
            classify(digest_of(I({"origin": "org-b",
                                  "source_id": "agent-9"}), LOCAL),
                     I(A1), ok, LOCAL)
        elif a == "setattr_flip":
            ok = validate_policy({"ga": [I(A1)]}, False, local_origin=LOCAL)
            object.__setattr__(ok, "cross_scope_visible", True)
            classify(digest_of(I({"origin": "org-b",
                                  "source_id": "agent-9"}), LOCAL),
                     I(A1), ok, LOCAL)
        elif a == "leaf_identity_mutation":
            # the round-7 attack: mutate an Identity LEAF shared through
            # the policy. The snapshot must hold PRIMITIVE strings —
            # asserted STRUCTURALLY here — and the mutated policy must
            # then refuse at consumption.
            ok = validate_policy({"ga": [I(A1)]}, False, local_origin=LOCAL)
            snap_groups = scope._REGISTRY[ok][0]
            for _name, _members in snap_groups:
                for _leaf in _members:
                    assert isinstance(_leaf, tuple) and all(
                        isinstance(p, (str, type(None))) for p in _leaf), \
                        "registry snapshot leaks non-primitive leaves"
            member = ok.groups["ga"][0]
            object.__setattr__(member, "source_id", "agent-evil")
            classify(digest_of(I(A1), LOCAL), I(A1), ok, LOCAL)
        else:
            raise AssertionError(f"unknown attempt {a}")

    return _expect_err(attempt)


def _k_mutation_oracle(v, policies):
    pol = policies["policy"]
    refused = 0
    try:
        pol.groups["x"] = ()
    except TypeError:
        refused += 1
    try:
        pol.groups["team-a"] += (I(A1),)
    except TypeError:
        refused += 1
    try:
        pol.cross_scope_visible = True
    except Exception:
        refused += 1
    return None if refused == 3 else f"only {refused}/3 refused"


def _k_membership(v, policies):
    rows = None if v["rows"] == "none" else v["rows"]
    if v["expect"] == "PolicyError":
        return _expect_err(lambda: membership(
            v["record"], rows, v["op_state"], LOCAL,
            expected_contributors=v.get("expected_contributors")))
    got = membership(v["record"], rows, v["op_state"], LOCAL,
                     expected_contributors=v.get("expected_contributors"))
    return _want_membership(v["expect"], got)


def _k_closure(v, policies):
    def _rows(rr):
        out = []
        for x in rr:
            row = {"site": x["site"],
                   "identity_digest": (digest_of(I(x["identity"]), LOCAL)
                                       if x.get("identity") else None),
                   "op_key": x.get("op_key")}
            if "contributor_ref" in x:
                row["contributor_ref"] = x["contributor_ref"]
            if x.get("payload"):
                row["payload"] = x["payload"]
            elif x.get("flattened"):
                row["payload"] = {"flattened": True}
            out.append(row)
        return out

    ledger = {k: _rows(rw) for k, rw in v["ledger_rows"].items()}
    links = {k: tuple(ids) for k, ids in v.get("legacy_links", {}).items()}
    digs = {k: (digest_of(I(x), LOCAL) if x else None)
            for k, x in v.get("legacy_digests", {}).items()}
    closed = close_absorption_rows(v["survivor"], ledger, links, digs)
    # the contract: a None closure IS UNRESOLVED, before membership runs
    got = (UNRESOLVED if closed is None
           else membership(v["record"], closed, v["op_state"], LOCAL))
    return _want_membership(v["expect"], got)


def _k_reconstruction(v, policies):
    expect = v["expect"]

    def build():
        return reconstruct_absorption_rows(
            v["records"], LOCAL, id_remap=v.get("id_remap"),
            import_op=v["op_key"])

    if expect in ("ImportLinkageError", "PolicyError"):
        try:
            build()
            return f"expected {expect}, none raised"
        except ImportLinkageError:
            return (None if expect == "ImportLinkageError"
                    else "ImportLinkageError raised where a plain "
                         "ScopeError was expected")
        except ScopeError:
            # ImportLinkageError subclasses ScopeError; reaching here
            # means a NON-linkage refusal (e.g. the import_op rule)
            return (None if expect == "PolicyError"
                    else "ScopeError raised where ImportLinkageError "
                         "was expected")
    got = build()
    want = {s: sorted(((digest_of(I(x), LOCAL) if x else None) for x in dl),
                      key=lambda z: z or "")
            for s, dl in expect["rows"].items()}
    norm = {s: sorted((r["identity_digest"] for r in rows),
                      key=lambda z: z or "")
            for s, rows in got.items()}
    if norm != want:
        return f"got {norm!r}, expected {want!r}"
    # the STRUCTURAL total-row check: per-row INJECTIVE op keys
    # (recomputed independently, per site token), typed contributor_ref,
    # the closed per-site payload, direct links at imported-absorption and
    # transitive copies at scope-attribution, and the cross-field
    # validator green on every emitted row
    seen_keys = set()
    for surv, rows in got.items():
        for r in rows:
            want_key = row_op_key(v["op_key"], r.get("site"), surv,
                                  r.get("contributor_ref") or "")
            try:
                validate_row_plan(r, "import", op=v["op_key"],
                                  survivor_id=surv)
            except ScopeError as e:
                return f"emitted row fails its own validator: {e}"
            flattened = (r.get("payload") or {}).get("flattened", False)
            want_site = (SITE_ATTRIBUTION if flattened
                         else "imported-absorption")
            if (r["site"] != want_site
                    or r.get("contributor_ref") is None
                    or r["op_key"] != want_key
                    or r["op_key"] in seen_keys
                    or not (r.get("payload") or {}).get("reconstructed")):
                return f"row not fully populated/canonical: {r!r}"
            seen_keys.add(r["op_key"])
    return None


def _k_derivation(v, policies):
    """The exact reverse-link algorithm, with the retention contract's
    INSERT-ONLY prune-time reparenting applied in order."""
    def _rows(rr):
        out = []
        for x in rr:
            payload = x.get("payload", {})
            site = x.get("site") or (SITE_ATTRIBUTION if payload
                                     else "absorption")
            out.append({"site": site,
                        "identity_digest": (digest_of(I(x["identity"]), LOCAL)
                                            if x.get("identity") else None),
                        "op_key": x.get("op_key"),
                        "evidence_ref_digest": None,
                        "contributor_ref": x.get("contributor_ref"),
                        "payload": payload})
        return out

    ledger = {k: _rows(rw) for k, rw in v["ledger_rows"].items()}
    expect = v["expect"]
    try:
        for n, pid in enumerate(v.get("prune", [])):
            ledger = prune_absorbed_record(pid, ledger,
                                           prune_op=f"op-{n:012x}")
        got = derive_absorbed_by(v["query"], ledger)
    except ExportLinkageError:
        return (None if expect == "ExportLinkageError"
                else "ExportLinkageError raised unexpectedly")
    if expect == "ExportLinkageError":
        return "expected ExportLinkageError, none raised"
    return None if got == expect else f"got {got!r}, expected {expect!r}"


def _k_row_identity(v, policies):
    """THE ONE canonical logical-row projection — semantic drift must
    change the id; contradictory rows must refuse. The handler DERIVES
    each row's op_key from the vector's context/op (callers never select
    keys); `"raw": true` suppresses injection so the key-binding refusal
    cells exercise the validator itself."""
    ctx = v.get("context", "import")
    op = v.get("op", "sup-fixture-edge" if ctx == "native"
               else "op-abcdef012345")

    def build(which):
        row = dict(v[which])
        side_op = v.get(f"op_{which}", op)
        if row.get("op_key") == "__DERIVE_FOR_OTHER__":
            row["op_key"] = row_op_key(side_op, row["site"],
                                       "OTHER-SURVIVOR",
                                       row["contributor_ref"])
        if not v.get("raw") and "op_key" not in row \
                and isinstance(row.get("contributor_ref"), str) \
                and row.get("site"):
            try:
                row["op_key"] = (
                    native_row_op_key(side_op, v.get("survivor", "S"),
                                      row["contributor_ref"])
                    if ctx == "native"
                    else row_op_key(side_op, row["site"],
                                    v.get("survivor", "S"),
                                    row["contributor_ref"]))
            except ScopeError:
                pass               # let the validator report it
        return plan_row_id(v.get("user", "u1"), "edge",
                           v.get("survivor", "S"), row, ctx, op=side_op)

    expect = v["expect"]
    if expect == "PolicyError":
        return _expect_err(lambda: build("a"))
    ida, idb = build("a"), build("b")
    if expect == "differ":
        return None if ida != idb else "ids EQUAL under semantic drift"
    return None if ida == idb else "ids differ for the same logical row"


def _k_op_key_injective(v, policies):
    keys = [import_row_op_key(v["op"], s, c) for s, c in v["cases"]]
    return (None if len(set(keys)) == len(keys)
            else f"COLLISION among {keys!r}")


def _k_validate_filters(v, policies):
    if v["expect"] == "PolicyError":
        return _expect_err(lambda: validate_filters(v["filters"]))
    validate_filters(v["filters"])
    return None


def _k_apply_filters(v, policies):
    got = apply_filters(v["records"], v["filters"])
    return (None if got == v["records"][:1]
            else f"got {len(got)} records")


def _k_shared_pool_key(v, policies):
    ok = (SHARED_POOL_KEY == v["expect"]
          and not re.fullmatch(r"[0-9a-f]{64}", SHARED_POOL_KEY))
    return None if ok else "reserved key collides with digest space"


_HANDLERS = {
    "classify": _k_classify,
    "same_identity": _k_same_identity,
    "validate_policy": _k_validate_policy,
    "direct_construction": _k_direct_construction,
    "mutation_oracle": _k_mutation_oracle,
    "membership": _k_membership,
    "closure": _k_closure,
    "reconstruction": _k_reconstruction,
    "derivation": _k_derivation,
    "row_identity": _k_row_identity,
    "op_key_injective": _k_op_key_injective,
    "validate_filters": _k_validate_filters,
    "apply_filters": _k_apply_filters,
    "shared_pool_key": _k_shared_pool_key,
}


def _dispatch(vector, policies):
    """Run ONE vector against the shipped surface. A kind with no handler
    is a HARD FAILURE, never a skip — that is what keeps the executed
    count honest when the vector file grows."""
    handler = _HANDLERS.get(vector["kind"])
    if handler is None:
        raise AssertionError(
            f"vector {vector['name']!r} has kind {vector['kind']!r} with NO "
            f"shipped-surface handler — V10 requires EVERY vector to execute "
            f"against src; add the handler, never a skip")
    return handler(vector, policies)


# ---- V10 ------------------------------------------------------------------

@pytest.mark.parametrize("vector", VECTORS, ids=[v["name"] for v in VECTORS])
def test_scope_reference_vectors(vector):
    """V10, per vector: the SHIPPED surface satisfies the pinned vector."""
    why = _dispatch(vector, _policies())
    assert why is None, f"{vector['name']} ({vector['kind']}): {why}"


def test_every_vector_executes_against_the_shipped_surface():
    """V10's totality clause: the EXECUTED count equals the vector file's
    length — no vector is skipped, and a vector of an unhandled kind
    fails loudly rather than passing by omission."""
    names = [v["name"] for v in VECTORS]
    assert len(set(names)) == len(names), "duplicate vector names"
    policies = _policies()
    executed, failures = 0, []
    for v in VECTORS:
        why = _dispatch(v, policies)      # raises on an unhandled kind
        executed += 1
        if why is not None:
            failures.append((v["name"], why))
    assert not failures, f"{len(failures)} vector(s) failed: {failures}"
    assert executed == len(VECTORS), (
        f"executed {executed} of {len(VECTORS)} vectors — every vector in "
        f"the file MUST run against the shipped surface")
    assert executed > 0
