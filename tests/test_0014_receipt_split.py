"""specs/0014 Slice C — the receipt split: the store-derived request digest,
the exhaustive snapshot partition (with its three oracles), the three-branch
phase 1, request-first phase 2 with persisted effects, the projection-version
discriminator, and the closed receipt-state triple.

Every named test from §4b/§7b lands here: the frozen digest vectors, the
partition totality + digest mutation + STORE-level abort oracles, the
concurrent-preflight loser-replays race (O1≠O2 with exact-effect replay + the
replayed-flag flip), the NULL-identity phase-1 continuation pair, the
reused-op-id tests on new and legacy receipts, the public lost-response replay
(the R5-2 live defect's regression), and the table-driven receipt-state test.
"""
import copy
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from veracium import contribution as C
from veracium.graph import (DEFAULT_RELATIONS, _build_supersession_plan,
                            apply_supersession)
from veracium.schema import Edge, EvidenceAuthor, Provenance, SupersessionPlan
from veracium.schema import _SourceType as SourceType  # specs/0016 D1: internal tests bind the private name
from veracium.store.base import SupersessionIntegrityError
from veracium.store.sqlite import SqliteStore

NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def _edge(uid="u1", obj="Miso", *, eid=None, conf=0.9, observed=NOW, ref="ev-1"):
    return Edge(
        id=eid or f"e-{uuid.uuid4().hex[:8]}", user_id=uid, subject="user",
        relation="pet", object=obj, valid_from=observed,
        provenance=Provenance(
            source_type=SourceType.STATED, author_of_evidence=EvidenceAuthor.USER,
            evidence_ref=ref, observed_at=observed, confidence=conf))


def _store(tmp_path):
    return SqliteStore(str(tmp_path / "s.db"))


def _plan(store, edge, op_id=None):
    p, _ = _build_supersession_plan(store, edge, DEFAULT_RELATIONS,
                                 op_id or f"op-{uuid.uuid4().hex[:8]}")
    p.raw_request = C.raw_request_snapshot(edge)
    return p


# -- the frozen digest --------------------------------------------------------

def test_request_digest_frozen_vectors():
    """R8-2: two COMPLETE snapshot fixtures — one ASCII, one with non-ASCII
    text + a float + a datetime — with their digest hex PINNED. Any
    serialization drift fails loudly here rather than conflicting in
    production. (The vectors were computed once from the frozen construction
    and are constants from that moment on.)"""
    e1 = _edge(eid="e-vector-1", obj="cat", conf=0.5,
               observed=datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc))
    e2 = _edge(eid="e-vector-2", obj="chat Miso Ω→", conf=0.123456789,
               observed=datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
    d1 = C.request_digest(C.raw_request_snapshot(e1))
    d2 = C.request_digest(C.raw_request_snapshot(e2))
    assert d1 == "8b2251cca451526dd26e11bcbd80ecb43acf311884c845718dc84851cc32835c"
    assert d2 == "679c0b36febd66ab635ec85c38e97c81f553f92493cdcc829f782232c7a3c584"


def test_request_digest_rejects_nan():
    with pytest.raises(ValueError):
        C.request_digest({"x": float("nan")})


def test_raw_request_field_partition_is_total():
    """R8-2/R9-4: every Edge and Provenance model field is assigned to exactly
    one partition class — a future model field breaks this until classified."""
    from veracium.schema import Edge as E, Provenance as P
    edge_classes = [set(C.EXACT_EQUAL_EDGE_FIELDS), set(C.RECOMPUTED_EDGE_FIELDS),
                    set(C.FORBIDDEN_EDGE_FIELDS), set(C.STRUCTURAL_EDGE_FIELDS)]
    prov_classes = [set(C.EXACT_EQUAL_PROV_FIELDS), set(C.RECOMPUTED_PROV_FIELDS)]
    assert set().union(*edge_classes) == set(E.model_fields)
    assert sum(len(c) for c in edge_classes) == len(E.model_fields)   # disjoint
    assert set().union(*prov_classes) == set(P.model_fields)
    assert sum(len(c) for c in prov_classes) == len(P.model_fields)


def test_every_snapshot_field_binds_the_digest():
    """R8-2: the field-by-field mutation oracle — mutate each field of a
    fixture snapshot in turn and the digest changes; every field provably
    bound, none free for forgery."""
    snap = C.raw_request_snapshot(_edge(eid="e-oracle"))
    base = C.request_digest(snap)
    for field in snap:
        mutated = copy.deepcopy(snap)
        if field == "provenance":
            for sub in mutated["provenance"]:
                m2 = copy.deepcopy(snap)
                m2["provenance"][sub] = "MUTATED-0014"
                assert C.request_digest(m2) != base, f"provenance.{sub} unbound"
            continue
        mutated[field] = "MUTATED-0014"
        assert C.request_digest(mutated) != base, f"{field} unbound"


def test_every_snapshot_field_mismatch_aborts_the_plan(tmp_path):
    """R9-3: the STORE-level oracle — inclusion in the digest is not binding;
    for every partition field, a snapshot mutated in that field alone must make
    apply_supersession_plan ABORT (exact-equal → differ; recomputed → recompute
    fails; forbidden → non-default present)."""
    store = _store(tmp_path)
    edge = _edge(eid="e-store-oracle")
    plan = _plan(store, edge)
    good = plan.raw_request

    def aborts(mutate):
        bad = copy.deepcopy(good)
        mutate(bad)
        p2 = plan.model_copy(deep=True)
        p2.raw_request = bad
        with pytest.raises(SupersessionIntegrityError):
            store.apply_supersession_plan(p2)

    for f in C.EXACT_EQUAL_EDGE_FIELDS:
        aborts(lambda s, f=f: s.__setitem__(f, "MUTATED"))
    for f in C.EXACT_EQUAL_PROV_FIELDS:
        aborts(lambda s, f=f: s["provenance"].__setitem__(f, "MUTATED"))
    for f in C.RECOMPUTED_EDGE_FIELDS:
        aborts(lambda s, f=f: s.__setitem__(
            f, "2001-01-01T00:00:00Z"))
    aborts(lambda s: s["provenance"].__setitem__(
        "observed_at", "2001-01-01T00:00:00Z"))
    aborts(lambda s: s["provenance"].__setitem__("confidence", 0.001))
    aborts(lambda s: s.__setitem__("invalidated_at", "2026-01-01T00:00:00Z"))
    aborts(lambda s: s.__setitem__("supersedes", "e-forged"))
    aborts(lambda s: s.__setitem__("times_used", 7))
    aborts(lambda s: s.__setitem__("outcome_counts", {"worked": 3}))
    aborts(lambda s: s.pop("object"))                      # incomplete dump
    p3 = plan.model_copy(deep=True)
    p3.raw_request = ["not", "a", "mapping"]
    with pytest.raises(SupersessionIntegrityError):
        store.apply_supersession_plan(p3)


# -- phase 1: three branches --------------------------------------------------

def test_public_lost_response_retry_replays(tmp_path):
    """The R5-2 LIVE defect's regression: an identical public retry of a
    committed absorption replays instead of raising."""
    store = _store(tmp_path)
    prior = _edge(obj="Miso", eid="e-p", conf=0.8, observed=NOW - timedelta(days=3))
    apply_supersession(store, prior, DEFAULT_RELATIONS)
    winner = _edge(obj="cat Miso", eid="e-w", conf=0.9)
    apply_supersession(store, winner, DEFAULT_RELATIONS)
    apply_supersession(store, winner, DEFAULT_RELATIONS)   # the retry: no raise
    live = [e for e in store.edges("u1", active_only=True) if e.id == "e-w"]
    assert len(live) == 1                                  # never double-applied


def test_public_reused_op_id_different_request_conflicts(tmp_path):
    """Phase-1 branch 2 on a NEW receipt: same op id, different raw edge."""
    store = _store(tmp_path)
    e1 = _edge(obj="Miso", eid="e-same-id")
    apply_supersession(store, e1, DEFAULT_RELATIONS)
    e2 = _edge(obj="COMPLETELY different", eid="e-same-id", conf=0.2)
    with pytest.raises(SupersessionIntegrityError):
        apply_supersession(store, e2, DEFAULT_RELATIONS)


def _null_receipt(store, uid, op_id, *, version, outcome_digest, response=None):
    store._conn.execute(
        "INSERT INTO supersession_operations(user_id,operation_id,"
        "logical_request_digest,status,request_digest,response,"
        "outcome_digest_version) VALUES(?,?,?,?,NULL,?,?)",
        (uid, op_id, outcome_digest, "applied", response, version))
    store._conn.commit()


def test_public_retry_against_a_legacy_null_receipt_reaches_phase_2(tmp_path):
    """R10-2 continuation test 1: (NULL, 1, NULL) — phase 1 branch 3 proceeds
    to planning; phase 2 follows the v1 outcome rule (matching → replay with
    reconstruct-from-plan)."""
    store = _store(tmp_path)
    edge = _edge(eid="e-legacy")
    plan = _plan(store, edge, "sup-e-legacy")
    v1 = store._logical_request_digest(plan)
    _null_receipt(store, "u1", "sup-e-legacy", version=1, outcome_digest=v1)
    apply_supersession(store, edge, DEFAULT_RELATIONS)     # replays, no raise
    assert not [e for e in store.edges("u1", active_only=True)
                if e.id == "e-legacy"]                     # replay: nothing applied


def test_legacy_null_receipt_with_conflicting_plan_conflicts(tmp_path):
    """R9-2 legacy-conflicting: the v1 projection still bites."""
    store = _store(tmp_path)
    edge = _edge(eid="e-legacy2")
    _null_receipt(store, "u1", "sup-e-legacy2", version=1,
                  outcome_digest="a-different-operation-entirely")
    with pytest.raises(SupersessionIntegrityError):
        apply_supersession(store, edge, DEFAULT_RELATIONS)


def test_new_snapshot_less_receipt_verifies_at_v2(tmp_path):
    """R10-2 continuation test 2 + R9-2 mutation case: (NULL, 2, json) — a
    store-level plan resubmission verifies at the EXTENDED projection, so a
    contribution-field mutation CONFLICTS (the v2 projection sees it)."""
    store = _store(tmp_path)
    edge = _edge(eid="e-snapless")
    plan, _ = _build_supersession_plan(store, edge, DEFAULT_RELATIONS, "op-snapless")
    plan.raw_request = None                                # snapshot-less
    r1 = store.apply_supersession_plan(plan)
    assert not r1.replayed
    receipt = store.supersession_receipt("u1", "op-snapless")
    assert receipt["request_digest"] is None
    assert receipt["outcome_digest_version"] == 2
    # identical resubmission → replay from persisted effects
    r2 = store.apply_supersession_plan(plan.model_copy(deep=True))
    assert r2.replayed and r2.inserted_incoming == r1.inserted_incoming
    # a contribution-field mutation → the v2 projection conflicts
    mutated = plan.model_copy(deep=True)
    mutated.absorption_pre_image = {"observed_at": "1999-01-01T00:00:00Z",
                                    "confidence": 0.1,
                                    "valid_from": "1999-01-01T00:00:00Z",
                                    "disclosure": "mentionable"}
    with pytest.raises(SupersessionIntegrityError):
        store.apply_supersession_plan(mutated)


# -- phase 2: request-first + the persisted effects ---------------------------

def test_concurrent_public_preflight_loser_replays(tmp_path):
    """R8-1, REQUIRES replay: T1/T2 submit identical request R; both pass
    phase 1 (no receipt yet); T1 commits O1; T2 re-plans post-commit and its
    phase-2 hit must return O1's effects — never an outcome conflict, never a
    double-apply."""
    store = _store(tmp_path)
    prior = _edge(obj="Miso", eid="e-p2", conf=0.8, observed=NOW - timedelta(days=3))
    apply_supersession(store, prior, DEFAULT_RELATIONS)
    winner = _edge(obj="cat Miso", eid="e-w2", conf=0.9)
    # both racers build plans BEFORE either commits (both passed phase 1)
    t1 = _plan(store, winner, "sup-e-w2")
    t2_snapshot = C.raw_request_snapshot(winner)
    o1 = store.apply_supersession_plan(t1)                  # T1 commits O1
    assert o1.invalidated == 1
    # T2 re-plans against POST-COMMIT state (the absorption already happened,
    # so its plan has nothing to invalidate — a legitimately different outcome)
    t2, _ = _build_supersession_plan(store, winner, DEFAULT_RELATIONS, "sup-e-w2")
    t2.raw_request = t2_snapshot
    o2_would_be_invalidated = len(t2.prior_invalidations)
    assert o2_would_be_invalidated == 0                     # O1 != O2, the race
    r = store.apply_supersession_plan(t2)
    assert r.replayed is True                               # the flag flip
    assert r.invalidated == o1.invalidated == 1             # O1's effects, exactly
    assert r.inserted_incoming == o1.inserted_incoming
    assert r.refused == o1.refused


def test_replay_returns_the_persisted_result_not_a_reconstruction(tmp_path):
    """R9-1/R10-1 named test: O1 and O2 differ in their EFFECT fields; the
    replay's effect fields equal O1's exactly AND carry replayed=True where O1
    carried False — effect equality + the flag flip, never whole-object
    equality."""
    store = _store(tmp_path)
    prior = _edge(obj="Miso", eid="e-p3", conf=0.8, observed=NOW - timedelta(days=3))
    apply_supersession(store, prior, DEFAULT_RELATIONS)
    winner = _edge(obj="cat Miso", eid="e-w3", conf=0.9)
    t1 = _plan(store, winner, "sup-e-w3")
    o1 = store.apply_supersession_plan(t1)
    assert o1.replayed is False and o1.invalidated == 1
    t2, _ = _build_supersession_plan(store, winner, DEFAULT_RELATIONS, "sup-e-w3")
    t2.raw_request = C.raw_request_snapshot(winner)
    assert len(t2.prior_invalidations) != o1.invalidated    # O1 != O2
    r = store.apply_supersession_plan(t2)
    assert (r.inserted_incoming, r.invalidated, r.refused) == \
           (o1.inserted_incoming, o1.invalidated, o1.refused)
    assert r.replayed is True and o1.replayed is False


def test_the_effect_payload_excludes_the_runtime_flag():
    from veracium.schema import SupersessionResult
    r = SupersessionResult(inserted_incoming=True, invalidated=2, refused=0)
    d = json.loads(C.effect_payload(r))
    assert "replayed" not in d
    assert d == {"inserted_incoming": True, "invalidated": 2, "refused": 0}


# -- the closed receipt-state triple ------------------------------------------

def test_receipt_state_triple_is_closed(tmp_path):
    """R10-4: TABLE-DRIVEN over every legal cell and the illegal
    representatives — write refused and read flagged. The write gate is the
    store's own INSERT path (new receipts are always (rd?, 2, json)); illegal
    combinations are probed at read via supersession_receipt validation."""
    store = _store(tmp_path)
    edge = _edge(eid="e-triple")
    plan = _plan(store, edge, "op-triple")
    store.apply_supersession_plan(plan)
    r = store.supersession_receipt("u1", "op-triple")
    # the legal new-with-snapshot cell, produced by the real writer
    assert r["request_digest"] is not None
    assert r["outcome_digest_version"] == 2
    effects = json.loads(r["response"])
    assert set(effects) == {"inserted_incoming", "invalidated", "refused"}

    legal = [
        (None, 1, None),                                    # legacy
        (None, 2, '{"inserted_incoming":true,"invalidated":0,"refused":0}'),
        ("d" * 64, 2, '{"inserted_incoming":true,"invalidated":0,"refused":0}'),
    ]
    illegal = [
        ("d" * 64, 1, None),
        ("d" * 64, 1, '{"inserted_incoming":true,"invalidated":0,"refused":0}'),
        (None, 2, None),
        ("d" * 64, 2, None),
        (None, 0, None),                                    # version 0
        (None, 3, None),                                    # version 3
        (None, 2, "not json"),
        (None, 2, '{"invalidated":0}'),                     # missing effect field
    ]
    for i, (rd, ver, resp) in enumerate(legal):
        assert store.validate_receipt_state(rd, ver, resp) is None
    for i, (rd, ver, resp) in enumerate(illegal):
        with pytest.raises(ValueError):
            store.validate_receipt_state(rd, ver, resp)
