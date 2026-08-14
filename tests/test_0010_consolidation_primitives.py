"""specs/0010 §6 — the fenced/leased Store primitives (Slice 3a).

These test the crash-safe state machine at the Store boundary: the atomic
all-or-nothing claim, the cooperative-owner + store-clock lease, the visibility
cutover's store_version bump, cleanup-before-fence takeover, the X20/X22/X23
cutover/output guards, recovery discovery, and the linearizable quiescent
snapshot. The consolidate()/recovery/visibility layers (X1–X3, X5–X6, X8–X9,
X16, X18–X19, X21) land with Slices 3b/3c.
"""
from datetime import datetime, timedelta, timezone

import pytest

from veracium.schema import (ConsolidationOutputDraft, ConsolidationState, Disclosure, Episode, EvidenceAuthor, Provenance)
from veracium.schema import _SourceType as SourceType  # specs/0016 D1: internal tests bind the private name
from veracium.store.base import NON_QUIESCENT
from veracium.store.sqlite import SqliteStore

S = ConsolidationState


class Clock:
    def __init__(self):
        self.t = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        return self.t

    def advance(self, secs):
        self.t = self.t + timedelta(seconds=secs)


def _ep(i, *, conf=0.9, disc=Disclosure.MENTIONABLE, author=EvidenceAuthor.USER,
        derived=None, uid="u"):
    return Episode(
        id=f"e{i}", user_id=uid, date=f"2026-01-{i:02d}", summary=f"s{i}",
        provenance=Provenance(source_type=SourceType.STATED, author_of_evidence=author,
                              evidence_ref=f"r{i}", confidence=conf, disclosure=disc,
                              derived_from=derived,
                              observed_at=datetime(2026, 1, i, tzinfo=timezone.utc)))


@pytest.fixture
def store(tmp_path):
    clk = Clock()
    s = SqliteStore(str(tmp_path / "t.db"), clock=clk)
    s._clk = clk                       # test handle
    return s


def _seed(store, n=3):
    for i in range(1, n + 1):
        store.add_episode(_ep(i))


def _draft(summary="merged", ds="2026-01-01", de="2026-01-03"):
    return ConsolidationOutputDraft(summary=summary, date_start=ds, date_end=de)


def _physical(store, uid="u"):
    """Physical rows, bypassing X9 ordinary-read visibility — a provisional output is
    hidden from episodes() while GENERATING but physically present (spec distinguishes
    the two). Tests that assert on provisional rows must look physically."""
    return [Episode.model_validate_json(r[0]) for r in
            store._conn.execute("SELECT json FROM episodes WHERE user_id=?", (uid,))]


def _to_durable(store, op, owner="w1"):
    """Drive op CLAIMED→GENERATING→(write output)→OUTPUTS_DURABLE."""
    assert store.transition_consolidation_if_current(op.operation_id, op.fence, owner, "generating")
    assert store.write_consolidation_output_if_current(op.operation_id, op.fence, owner, _draft())
    assert store.transition_consolidation_if_current(op.operation_id, op.fence, owner, "outputs_durable")


# --- X4 / X11: the claim is atomic over the whole set -----------------------

def test_concurrent_consolidation_claims_all_or_nothing(store):
    _seed(store)
    a = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    b = store.create_or_takeover_consolidation("u", ["e2", "e3"], "w2", 60)
    assert a is not None and b is None, "exactly one overlapping claim wins"
    assert len(store.pending_consolidations("u")) == 1


def test_partial_claim_is_impossible(store):
    _seed(store)
    store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    loser = store.create_or_takeover_consolidation("u", ["e2", "e3"], "w2", 60)
    assert loser is None
    # e3 was never claimed — no partial new claim left behind
    e3 = next(e for e in store.episodes("u") if e.id == "e3")
    assert e3.claimed_by is None and e3.operation_id is None


# --- X7 / X10: preemption needs an expired store-clock lease -----------------

def test_a_live_lease_is_not_preempted(store):
    _seed(store)
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    store._clk.advance(50)
    assert store.renew_consolidation_lease(op.operation_id, op.fence, "w1")  # heartbeat
    store._clk.advance(50)             # 100s elapsed, but renewed at 50 → still live
    assert store.create_or_takeover_consolidation("u", ["e2"], "w2", 60) is None
    assert store.abandon_consolidation_if_current(op.operation_id, op.fence) is False


def test_a_worker_passing_its_own_identity_is_rejected_on_a_peer_op(store):
    _seed(store)
    op = store.create_or_takeover_consolidation("u", ["e1"], "w1", 60)
    # w2 (a well-behaved peer passing its own identity) cannot act on w1's op
    assert store.transition_consolidation_if_current(op.operation_id, op.fence, "w2", "generating") is False
    assert store.renew_consolidation_lease(op.operation_id, op.fence, "w2") is False


def test_a_preempted_worker_cannot_write_or_delete(store):
    _seed(store)
    op1 = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    store._clk.advance(120)            # lease expires
    op2 = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w2", 60)
    assert op2.fence > op1.fence
    # the preempted worker holds the STALE fence: every fenced action fails
    assert store.transition_consolidation_if_current(op1.operation_id, op1.fence, "w1", "generating") is False
    assert store.write_consolidation_output_if_current(op1.operation_id, op1.fence, "w1", _draft()) is False
    assert store.delete_claimed_inputs_if_current(op1.operation_id, op1.fence) is False


# --- X13: recovery discovery is exactly the recovery-pending states ----------

def test_pending_returns_only_recovery_pending(store):
    _seed(store, 4)
    # an OUTPUTS_DURABLE op IS discovered
    live = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    _to_durable(store, live)
    # a quiescent ABANDONED op is NOT
    ab = store.create_or_takeover_consolidation("u", ["e3"], "w2", 60)
    store._clk.advance(120)
    assert store.abandon_consolidation_if_current(ab.operation_id, ab.fence)
    pending = store.pending_consolidations("u")
    ids = {o.operation_id for o in pending}
    assert live.operation_id in ids
    assert ab.operation_id not in ids
    assert all(o.state in (S.CLAIMED, S.GENERATING, S.OUTPUTS_DURABLE) for o in pending)


# --- X14: the visibility cutover bumps store_version; a claim does not --------

def test_claim_does_not_bump_store_version(store):
    _seed(store)
    v0 = store.store_version("u")
    store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    assert store.store_version("u") == v0, "a claim changes only operational metadata"


def test_visibility_cutover_bumps_store_version(store):
    _seed(store)
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "generating")
    store.write_consolidation_output_if_current(op.operation_id, op.fence, "w1", _draft())
    v0 = store.store_version("u")
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "outputs_durable")
    assert store.store_version("u") > v0, "the cutover is a representation change"


# --- X15: a new fence issues only from a clean ABANDONED state ---------------

def test_takeover_requires_clean_abandoned(store):
    _seed(store)
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    # a LIVE op cannot be taken over / revived
    assert store.create_or_takeover_consolidation("u", ["e1", "e2"], "w2", 60) is None


def test_takeover_of_expired_generating_cleans_first(store):
    _seed(store)
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "generating")
    store.write_consolidation_output_if_current(op.operation_id, op.fence, "w1", _draft())
    # a provisional (hidden) output row physically exists now
    assert any(e.lineage for e in _physical(store))
    store._clk.advance(120)            # lease expires while GENERATING
    op2 = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w2", 60)
    assert op2 is not None and op2.fence > op.fence
    # the expired op was abandoned FIRST — its provisional row is gone, no coexistence
    assert not any(e.lineage for e in _physical(store)), \
        "old-generation provisional rows must not survive into the new fence"


# --- X17: linearizable quiescent snapshot + forget_user erasure --------------

def test_quiescent_snapshot_is_linearizable_vs_a_new_claim(store):
    _seed(store)
    assert store.quiescent_episode_snapshot("u") is not NON_QUIESCENT   # all quiescent
    store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    assert store.quiescent_episode_snapshot("u") is NON_QUIESCENT, \
        "a live claim makes the snapshot non-quiescent — never a dangling claimed_by"


def test_forget_user_erases_consolidation_ops(store):
    _seed(store)
    store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    assert store.pending_consolidations("u")
    store.forget_user("u")
    assert store.pending_consolidations("u") == []


# --- X20: FINALIZED is unreachable until inputs are deleted ------------------

def test_finalize_refuses_before_inputs_deleted(store):
    _seed(store)
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    _to_durable(store, op)
    # inputs still present → FINALIZED refuses
    assert store.transition_consolidation_if_current(op.operation_id, op.fence, None, "finalized") is False
    assert store.delete_claimed_inputs_if_current(op.operation_id, op.fence)
    assert store.transition_consolidation_if_current(op.operation_id, op.fence, None, "finalized")


# --- X22: bound output; cutover refuses with none; INSERT never replaces -----

def test_output_is_bound_to_the_fenced_operation(store):
    _seed(store)
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "generating")
    store.write_consolidation_output_if_current(op.operation_id, op.fence, "w1", _draft())
    out = next(e for e in _physical(store) if e.lineage)
    assert out.operation_id == op.operation_id
    assert out.lineage == ["hist:e1", "hist:e2"]        # the whole claimed set
    assert out.claimed_by is None


def test_cutover_refuses_with_no_bound_output(store):
    _seed(store)
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "generating")
    assert store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "outputs_durable") is False


def test_output_write_cannot_replace_an_existing_episode(store):
    _seed(store)
    # the draft structurally has no id — a forged row identity is impossible
    assert "id" not in ConsolidationOutputDraft.model_fields
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "generating")
    before = {e.id: e.model_dump() for e in _physical(store)}
    store.write_consolidation_output_if_current(op.operation_id, op.fence, "w1", _draft())
    after = {e.id: e for e in _physical(store)}
    for eid, blob in before.items():                    # no existing row was replaced
        assert after[eid].model_dump() == blob
    assert len(after) == len(before) + 1                # exactly one new row inserted


# --- X23: derived fields are Store-computed from the claimed set -------------

def test_output_trust_is_the_whole_set_minimum(store):
    store.add_episode(_ep(1, conf=0.9, disc=Disclosure.MENTIONABLE))
    store.add_episode(_ep(2, conf=0.2, disc=Disclosure.USE_ONLY,
                          author=EvidenceAuthor.THIRD_PARTY,
                          derived=EvidenceAuthor.THIRD_PARTY))
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "generating")
    store.write_consolidation_output_if_current(op.operation_id, op.fence, "w1", _draft())
    out = next(e for e in _physical(store) if e.lineage)
    assert out.provenance.confidence == 0.2                  # min across the set
    assert out.provenance.disclosure is Disclosure.USE_ONLY  # weakest
    assert out.provenance.third_party_influenced             # influence retained (N9b)
    assert out.provenance.author_of_evidence is EvidenceAuthor.SYSTEM
    assert out.provenance.model_dump()["source_type"] == "inferred"


def test_output_date_range_is_store_derived_not_llm(store):
    _seed(store, 3)                    # dates 2026-01-01 .. 2026-01-03
    op = store.create_or_takeover_consolidation("u", ["e1", "e2", "e3"], "w1", 60)
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "generating")
    # the draft LIES about the range; the store must ignore it and use the inputs
    store.write_consolidation_output_if_current(
        op.operation_id, op.fence, "w1",
        _draft(ds="1999-01-01", de="2099-12-31"))
    out = next(e for e in _physical(store) if e.lineage)
    assert out.date_start == "2026-01-01" and out.date_end == "2026-01-03"
    assert out.date == out.date_start                        # compat sort key
