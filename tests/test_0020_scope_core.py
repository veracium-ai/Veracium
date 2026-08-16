"""specs/0020 §4a-ii/§4a-iii — the scope core's properties the pinned
vectors do NOT reach.

The 128 vectors (`tests/test_0020_scope_vectors.py`) bind the shipped
surface to the normative reference on every enumerated input. What they
cannot express, and what this module asserts adversarially:

- the registry snapshot's LEAVES ARE PRIMITIVE strings — asserted
  STRUCTURALLY, over a multi-group policy, walking to the bottom (the
  round-7 finding was an "immutable" snapshot that was an immutable
  container of SHARED `Identity` instances; a vector can only observe the
  refusal, not the shape that makes it hold);
- a policy mutated at ANY carrier — the bool, a leaf, the digest map,
  the backing dict — refuses at consumption EVEN AFTER RE-SEALING with
  the module's own `_seal`, because the registry is the authority and the
  seal is only compared;
- the identity digest is the SHIPPED 0006 primitive, ONE implementation
  reached through `scope_linkage`, not a byte-compatible copy — asserted
  by value over a matrix AND structurally (the domain literal exists
  exactly once in `src/`, and the digest function object is shared);
- the error surface is ONE class (`ScopeError`, aliased `PolicyError`),
  with the linkage errors beneath it and `ValueError` above it;
- `DECISION_TABLE` is total over `classify`'s range, and `membership` is
  total over the closed 0010 state set.
"""

from __future__ import annotations

import gc
import pathlib
import re

import pytest

from veracium import scope, scope_linkage, source_identity
from veracium.scope import (DECISION_TABLE, SHARED, SHARED_POOL_KEY,
                            UNRESOLVED, Identity, PolicyError, ScopeError,
                            ScopePolicy, classify, close_absorption_rows,
                            decide, digest_of, membership, resolve,
                            validate_policy)

LOCAL = "org-local-1234"
A1 = Identity("org-a", "agent-1")
A2 = Identity("org-a", "agent-2")
B1 = Identity("org-b", "agent-9")
SRC = pathlib.Path(__file__).resolve().parents[1] / "src"


def _policy(**kw):
    """FRESH `Identity` instances every call: several tests below mutate a
    member leaf, and the suite runs in randomized order — a module-level
    instance shared into a policy would carry a mutation into whatever
    test ran next (and would silently disarm the leaf-mutation assertion
    itself)."""
    return validate_policy({"team-a": [Identity("org-a", "agent-1"),
                                       Identity("org-a", "agent-2")],
                            "team-b": [Identity("org-b", "agent-9")]},
                           kw.pop("cross_scope_visible", False),
                           local_origin=LOCAL)


# ---- the registry snapshot: PRIMITIVE leaves, structurally ----------------

def test_registry_snapshot_leaves_are_primitive_strings():
    """The snapshot must be immutable DOWN TO ITS LEAVES: no `Identity`
    instance may be shared between the policy and the validator's record
    of it, or a single `object.__setattr__` mutates both and the
    divergence check sees nothing (the round-7 executed attack)."""
    pol = _policy()
    snapshot = scope._REGISTRY[pol]
    groups, xv, digests, seal = snapshot

    live_ids = {id(m) for members in pol.groups.values() for m in members}
    assert live_ids, "fixture built no members"

    seen_leaves = 0
    assert isinstance(groups, tuple)
    for name, members in groups:
        assert isinstance(name, str)
        assert isinstance(members, tuple)
        for leaf in members:
            seen_leaves += 1
            # a leaf is the PRIMITIVE pair, never the object the policy holds
            assert type(leaf) is tuple and len(leaf) == 2, repr(leaf)
            assert not isinstance(leaf, Identity)
            assert id(leaf) not in live_ids
            for part in leaf:
                assert part is None or type(part) is str, repr(part)
    assert seen_leaves == 3, "the walk did not reach every member"

    assert type(xv) is bool
    assert isinstance(digests, tuple)
    for name, digs in digests:
        assert type(name) is str and type(digs) is frozenset
        assert all(type(d) is str for d in digs)
    assert type(seal) is str

    # and NOTHING reachable in the snapshot is a live policy object
    assert id(groups) != id(pol.groups)
    assert id(digests) != id(pol.group_digests)


def test_registry_is_weakly_keyed_and_a_dropped_policy_refuses():
    """The registry is validator-owned and WEAK: a discarded policy leaves
    no entry behind (it is not an unbounded leak), and any policy the
    registry does not know refuses at consumption — a `ScopePolicy` built
    outside `validate_policy` can never be validated by existing."""
    pol = _policy()
    ref = scope._weakref.ref(pol)
    assert scope._REGISTRY.get(pol) is not None
    del pol
    gc.collect()
    assert ref() is None, "the policy outlived its only strong reference"

    live = _policy()
    forged = ScopePolicy(groups=live.groups,
                         cross_scope_visible=live.cross_scope_visible,
                         group_digests=live.group_digests, seal=live.seal)
    assert scope._REGISTRY.get(forged) is None
    with pytest.raises(ScopeError):
        classify(digest_of(B1, LOCAL), A1, forged, LOCAL)


# ---- mutation + RE-SEALING refuses at every carrier -----------------------

@pytest.mark.parametrize("carrier", ["bool", "leaf", "seal_only"])
def test_a_mutated_policy_refuses_even_after_resealing(carrier):
    """Re-signing does not help: the seal is COMPARED against the
    registered value, never recomputed as authority. Every mutable
    carrier of the policy's visible state is exercised, and each is
    re-sealed with the module's OWN `_seal` after the mutation."""
    pol = _policy()
    evidence = digest_of(B1, LOCAL)
    assert classify(evidence, A1, pol, LOCAL) == "CROSS_HIDDEN"

    if carrier == "bool":
        object.__setattr__(pol, "cross_scope_visible", True)
    elif carrier == "leaf":
        object.__setattr__(pol.groups["team-a"][0], "source_id", "agent-evil")
    else:
        # no state change at all — just a re-signature with a LIE about
        # cross_scope_visible; the registry comparison still catches it
        object.__setattr__(pol, "seal",
                           scope._seal(dict(pol.groups), True, LOCAL))

    # re-sign the mutated object with the module's own sealer
    if carrier != "seal_only":
        object.__setattr__(
            pol, "seal", scope._seal(dict(pol.groups),
                                     pol.cross_scope_visible, LOCAL))

    with pytest.raises(ScopeError):
        classify(evidence, A1, pol, LOCAL)
    with pytest.raises(ScopeError):
        classify(digest_of(A1, LOCAL), A1, pol, LOCAL)   # every call site


def test_a_leaf_mutation_does_not_touch_the_snapshot():
    """The complement of the refusal: after mutating a live member, the
    validator's record still carries the ORIGINAL primitive pair — proof
    the divergence is observable rather than mirrored."""
    pol = _policy()
    before = scope._REGISTRY[pol][0]
    object.__setattr__(pol.groups["team-a"][0], "source_id", "agent-evil")
    assert scope._REGISTRY[pol][0] == before
    assert ("agent-evil" not in
            {p for _n, ms in scope._REGISTRY[pol][0] for m in ms for p in m})


# ---- ONE digest implementation -------------------------------------------

@pytest.mark.parametrize("origin,source_id", [
    ("org-a", "agent-1"),
    (None, "agent-1"),                       # I9: resolves to the singleton
    ("org-a", None),                         # I13: no digest at all
    (None, None),
    ("órg-ü", "agent-ünïcode"),
    ("o" * 512, "s" * 512),                  # the shipped bounds, exactly
    ("a:b", "c"), ("a", "b:c"),              # framing, not concatenation
])
def test_digest_agrees_with_the_shipped_0006_primitive(origin, source_id):
    """`scope.digest_of` IS the shipped `source_identity_digest` over the
    RESOLVED pair — the same function, so a policy-side digest equals a
    store-side digest by construction rather than by coincidence."""
    got = digest_of(Identity(origin, source_id), LOCAL)
    want = source_identity.source_identity_digest(
        source_identity.resolve_origin(origin, LOCAL), source_id)
    assert got == want
    if source_id is None:
        assert got is None                   # I13 — no groupable identity
    else:
        assert re.fullmatch(r"[0-9a-f]{64}", got)


def test_framing_makes_the_pair_injective():
    assert (digest_of(Identity("a:b", "c"), LOCAL)
            != digest_of(Identity("a", "b:c"), LOCAL))
    assert (digest_of(Identity("ab", "c"), LOCAL)
            != digest_of(Identity("a", "bc"), LOCAL))


def test_the_identity_digest_has_exactly_one_implementation_in_src():
    """Structural, not behavioural: the 0006 domain literal must exist in
    exactly ONE production file. A second (byte-compatible) copy is the
    failure 0006 F2 exists to prevent — two implementations drift
    silently and a join miss in revocation is UNDER-revocation."""
    hits = sorted(p.relative_to(SRC).as_posix() for p in SRC.rglob("*.py")
                  if "veracium.source-id.v1" in p.read_text())
    assert hits == ["veracium/source_identity.py"], hits
    # and the module the scope core reaches through holds the SAME object
    assert (scope_linkage.source_identity_digest
            is source_identity.source_identity_digest)


def test_resolve_is_the_shipped_resolve_at_read_chokepoint():
    assert resolve(Identity(None, "s"), LOCAL) == Identity(LOCAL, "s")
    assert resolve(Identity("org-a", "s"), LOCAL) == Identity("org-a", "s")
    for bad in ("", None, 7):
        with pytest.raises(ScopeError):
            resolve(Identity(None, "s"), bad)


# ---- ONE error class ------------------------------------------------------

def test_the_scope_error_surface_is_a_single_class():
    assert PolicyError is ScopeError
    assert scope.ScopeError is scope_linkage.ScopeError
    assert issubclass(ScopeError, ValueError)
    for cls in (scope.ImportLinkageError, scope.ExportLinkageError):
        assert issubclass(cls, ScopeError)
    # the linkage validators refuse under the SAME class the core does
    with pytest.raises(ScopeError):
        scope.row_op_key("not-an-op", "imported-absorption", "S", "C")
    with pytest.raises(ScopeError):
        validate_policy({"g": [Identity("org-a", None)]}, False,
                        local_origin=LOCAL)


# ---- totality -------------------------------------------------------------

def test_decision_table_is_total_over_classify_range():
    """Every classification `classify` can produce has a table entry, and
    the table has no cell `classify` cannot produce — enumerated, so no
    cell can be overlooked."""
    pol = _policy(cross_scope_visible=False)
    pol_xv = _policy(cross_scope_visible=True)
    produced = {
        classify(digest_of(A1, LOCAL), None, None, LOCAL),          # OWN
        classify(digest_of(A1, LOCAL), A1, pol, LOCAL),             # OWN
        classify(SHARED, A1, pol, LOCAL),                           # SHARED
        classify(digest_of(B1, LOCAL), A1, pol, LOCAL),        # CROSS_HIDDEN
        classify(digest_of(B1, LOCAL), A1, pol_xv, LOCAL),    # CROSS_VISIBLE
        classify(UNRESOLVED, A1, pol, LOCAL),                  # UNRESOLVED
    }
    assert produced == set(DECISION_TABLE)
    for name, (visible, shape) in DECISION_TABLE.items():
        assert isinstance(visible, bool)
        assert (shape is None) is (not visible)
    # UNRESOLVED and CROSS_HIDDEN are the invisible cells — fail closed
    assert decide(UNRESOLVED, A1, pol, LOCAL) == (False, None)
    assert decide(digest_of(B1, LOCAL), A1, pol, LOCAL) == (False, None)


def test_membership_is_total_over_the_closed_operation_state_set():
    record = {"author": "user", "origin": "org-a", "source_id": "agent-1",
              "evidence_ref": "ev-1", "lineage": False}
    own = digest_of(A1, LOCAL)
    for state in scope.OP_STATES:
        if state == "abandoned":
            with pytest.raises(ScopeError):
                membership(record, None, state, LOCAL)
            continue
        got = membership(record, None, state, LOCAL)
        assert got == (UNRESOLVED if state == "generating" else own)
    with pytest.raises(ScopeError):
        membership(record, None, "no-such-state", LOCAL)


def test_none_closure_means_unresolved_and_markers_are_never_links():
    """`close_absorption_rows` returning None IS the UNRESOLVED signal —
    the caller may not read it as "no evidence, therefore own scope".
    A closure-incompleteness marker is skipped, never walked as a link,
    and its None digest then fails membership CLOSED."""
    marker = {"site": scope.SITE_ATTRIBUTION, "identity_digest": None,
              "contributor_ref": "GONE", "payload": {"closure": "incomplete"},
              "op_key": None}
    closed = close_absorption_rows("S", {"S": [marker]})
    assert closed == [marker]                # skipped as a link, still a row
    record = {"author": "user", "origin": "org-a", "source_id": "agent-1",
              "evidence_ref": "ev-1", "lineage": False}
    assert membership(record, closed, "none", LOCAL) == UNRESOLVED

    # a ref-less legacy row with NO links is unwalkable → None → UNRESOLVED
    legacy = {"site": "absorption", "identity_digest": digest_of(A2, LOCAL),
              "op_key": None}
    assert close_absorption_rows("S", {"S": [legacy]}) is None


def test_a_self_absorbing_record_refuses_the_prune_instead_of_looping():
    """The corrupt-linkage domain for the prune walk, closed at EVERY
    cycle length. History, because it is the lesson: a canonical row on X
    naming contributor X made the accepted reference NON-TERMINATING (it
    appended reparented rows — themselves canonical — to the list it was
    iterating). Found by differential fuzzing, fixed in both
    implementations. Research then asked the domain question (the 0018
    R1-4 lens): self-absorption is the cycle of length 1, so what does
    n>=2 do? Executed answer: it TERMINATED but MANUFACTURED a
    self-absorbing row on the absorber — bounded-wrong, which is still
    wrong. The guard now walks the whole absorber chain and refuses any
    revisit. If a future edit reintroduces the unbounded append this test
    hangs the suite rather than passing."""
    d = digest_of(Identity("org-a", "agent-1"), LOCAL)
    ledger = {"B": [{"site": "absorption", "identity_digest": d,
                     "op_key": None, "evidence_ref_digest": None,
                     "contributor_ref": "B", "payload": {}},
                    {"site": scope.SITE_ATTRIBUTION, "identity_digest": d,
                     "op_key": None, "evidence_ref_digest": None,
                     "contributor_ref": "B",
                     "payload": {"flattened": True}}]}
    with pytest.raises(ScopeError, match="CYCLIC"):
        scope.prune_absorbed_record("B", ledger, prune_op="op-000000000001")
    assert ledger["B"][0]["payload"] == {}, "the input was mutated"

    # ...and the same refusal at every longer cycle (n = 2..5): each ring
    # has a canonical row on each member naming the next, so the absorber
    # chain returns to the start. Before the generalization, n>=2 silently
    # wrote a {"closure": "incomplete"} self-absorbing row instead.
    for n in range(2, 6):
        ids = [f"c{i}" for i in range(n)]
        ring = {ids[i]: [
            {"site": "absorption", "identity_digest": d, "op_key": None,
             "evidence_ref_digest": None, "contributor_ref": ids[(i + 1) % n],
             "payload": {}},
            {"site": scope.SITE_ATTRIBUTION, "identity_digest": d,
             "op_key": None, "evidence_ref_digest": None,
             "contributor_ref": ids[(i + 1) % n],
             "payload": {"flattened": True}}] for i in range(n)}
        with pytest.raises(ScopeError, match="CYCLIC"):
            scope.prune_absorbed_record(ids[0], ring,
                                        prune_op="op-000000000002")

    # the ordinary two-record prune still reparents, unchanged
    plain = {"B": [{"site": "absorption", "identity_digest": d,
                    "op_key": None, "evidence_ref_digest": None,
                    "contributor_ref": "A", "payload": {}}],
             "C": [{"site": "absorption", "identity_digest": d,
                    "op_key": None, "evidence_ref_digest": None,
                    "contributor_ref": "B", "payload": {}},
                   {"site": scope.SITE_ATTRIBUTION, "identity_digest": d,
                    "op_key": None, "evidence_ref_digest": None,
                    "contributor_ref": "A",
                    "payload": {"flattened": True}}]}
    after = scope.prune_absorbed_record("B", plain,
                                        prune_op="op-000000000001")
    assert "B" not in after                       # the A10 drop
    assert scope.derive_absorbed_by("A", after) == "C"


def test_shared_pool_key_cannot_collide_with_digest_space():
    assert SHARED_POOL_KEY == "pool:unidentified"
    assert not re.fullmatch(r"[0-9a-f]{64}", SHARED_POOL_KEY)
    assert SHARED == "SHARED_POOL" and UNRESOLVED == "UNRESOLVED"
    assert not re.fullmatch(r"[0-9a-f]{64}", SHARED)
    assert not re.fullmatch(r"[0-9a-f]{64}", UNRESOLVED)
