"""specs/0010 §4c/§6 — read visibility (X9) and the store-hygiene fence (X18/X19/X21).

Slice 3b: episodes() shows EXACTLY ONE representation across every op phase, and the
generic mutators cannot touch a reserved id, fabricate operational state, or mint a
historical id. The consolidate()/recovery/export/import layers land in Slice 3c.
"""
from datetime import datetime, timedelta, timezone

import pytest

from veracium.schema import (ConsolidationOutputDraft, ConsolidationState, Episode,
                             EvidenceAuthor, Provenance, SourceType)
from veracium.store.sqlite import SqliteStore


class Clock:
    def __init__(self):
        self.t = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t = self.t + timedelta(seconds=s)


def _ep(i, uid="u"):
    return Episode(id=f"e{i}", user_id=uid, date=f"2026-01-{i:02d}", summary=f"s{i}",
                   provenance=Provenance(source_type=SourceType.STATED,
                                         author_of_evidence=EvidenceAuthor.USER,
                                         evidence_ref=f"r{i}"))


@pytest.fixture
def store(tmp_path):
    clk = Clock()
    s = SqliteStore(str(tmp_path / "t.db"), clock=clk)
    s._clk = clk
    return s


def _seed(store, n=3):
    for i in range(1, n + 1):
        store.add_episode(_ep(i))


def _draft():
    return ConsolidationOutputDraft(summary="merged", date_start="2026-01-01",
                                    date_end="2026-01-03")


def _ids(store, uid="u"):
    return {e.id for e in store.episodes(uid)}


# --- X9: every ordinary read sees exactly one representation ----------------

def test_every_read_sees_exactly_one_representation(store):
    _seed(store, 2)
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    # CLAIMED: inputs visible, no output
    assert _ids(store) == {"e1", "e2"}
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "generating")
    store.write_consolidation_output_if_current(op.operation_id, op.fence, "w1", _draft())
    # GENERATING: inputs still visible, provisional output HIDDEN (never both/neither)
    assert _ids(store) == {"e1", "e2"}
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "outputs_durable")
    # OUTPUTS_DURABLE: inputs HIDDEN, output visible — exactly one representation
    visible = store.episodes("u")
    assert len(visible) == 1 and visible[0].lineage
    store.delete_claimed_inputs_if_current(op.operation_id, op.fence)
    store.transition_consolidation_if_current(op.operation_id, op.fence, None, "finalized")
    # FINALIZED: inputs gone, output visible
    visible = store.episodes("u")
    assert len(visible) == 1 and visible[0].lineage


def test_never_neither_representation_at_any_phase(store):
    _seed(store, 2)
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    for step in (None, "generating", "outputs_durable"):
        if step == "generating":
            store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "generating")
            store.write_consolidation_output_if_current(op.operation_id, op.fence, "w1", _draft())
        elif step == "outputs_durable":
            store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "outputs_durable")
        assert store.episodes("u"), f"a read saw NEITHER representation at {step}"


def test_abandoned_op_inputs_are_visible_again(store):
    _seed(store, 2)
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    store._clk.advance(120)
    store.abandon_consolidation_if_current(op.operation_id, op.fence)
    assert _ids(store) == {"e1", "e2"}   # released inputs, no orphan output


# --- X21: a claimed id is reserved; generic add/delete refuse ---------------

def test_generic_delete_of_a_claimed_input_is_refused(store):
    _seed(store)
    store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    with pytest.raises(ValueError, match="X21"):
        store.delete_episode("e1")


def test_generic_replace_of_a_claimed_input_is_refused(store):
    _seed(store)
    store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    with pytest.raises(ValueError, match="X21"):
        store.add_episode(_ep(1))            # same id "e1" — a replace of a claimed input


def test_generic_add_of_a_deleted_reserved_id_before_finalized_is_refused(store):
    # the OUTPUTS_DURABLE→FINALIZED seam: inputs physically deleted, still reserved
    _seed(store, 2)
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "generating")
    store.write_consolidation_output_if_current(op.operation_id, op.fence, "w1", _draft())
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "outputs_durable")
    store.delete_claimed_inputs_if_current(op.operation_id, op.fence)   # inputs gone
    # reservation SURVIVES the physical delete until FINALIZED
    with pytest.raises(ValueError, match="X21"):
        store.add_episode(_ep(1))
    store.transition_consolidation_if_current(op.operation_id, op.fence, None, "finalized")
    # after FINALIZED the id is free again
    store.add_episode(_ep(1))
    assert any(e.id == "e1" for e in store.episodes("u"))


# --- X18: add_episode cannot fabricate operational state --------------------

def test_add_episode_cannot_create_operational_state(store):
    for extra in ({"claimed_by": "op-x"}, {"operation_id": "op-x"},
                  {"lineage": ["hist:e9"]}):
        ep = _ep(9).model_copy(update=extra)
        with pytest.raises(ValueError, match="X18"):
            store.add_episode(ep)


# --- X19: a live episode id can never inhabit the historical namespace -------

def test_live_add_episode_cannot_take_a_historical_lineage_id_after_finalization(store):
    # finalize a generation so hist:e1/hist:e2 become its output's lineage ids
    _seed(store, 2)
    op = store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "generating")
    store.write_consolidation_output_if_current(op.operation_id, op.fence, "w1", _draft())
    store.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "outputs_durable")
    store.delete_claimed_inputs_if_current(op.operation_id, op.fence)
    store.transition_consolidation_if_current(op.operation_id, op.fence, None, "finalized")
    out = next(e for e in store.episodes("u") if e.lineage)
    assert out.lineage == ["hist:e1", "hist:e2"]
    # a live episode can NEVER be minted into that historical namespace → no collision
    with pytest.raises(ValueError, match="X19"):
        store.add_episode(Episode(id="hist:e1", user_id="u", date="2026-02-01",
                                  summary="x",
                                  provenance=Provenance(source_type=SourceType.STATED,
                                                        author_of_evidence=EvidenceAuthor.USER,
                                                        evidence_ref="r")))
