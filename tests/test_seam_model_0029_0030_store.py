"""Seam model driver — dev's halves (allocation schedule + restriction
derivation + CurrentState), against the REAL store, sweep and projection.

RULE ZERO: every assertion has a negative control proving it CAN fail, and
the controls are themselves asserted (a control that stops discriminating is
a test failure, not a silent green).

Scope note, stated rather than discovered: the TRANSITIVE restriction case
(an edge in `reach` — retired while in neither `direct` nor `affected`) is
exercised by the 0022 sweep vectors (54, shipped); this model proves the
MEMBERSHIP TEST's shape over the heterogeneous retire population, not the
sweep's closure, which is accepted 0022 ground.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

SEAM = Path(__file__).resolve().parents[1] / "specs" / "evidence" / "0029-0030" / "seam_model"
sys.path.insert(0, str(SEAM))

from allocation_schedule import (deferred_batch, immediate_batch,  # noqa: E402
                                 run_two_connection_schedule)
from restriction_derivation import (CurrentState, control_affected_misses_the_direct_case,  # noqa: E402
                                    control_bare_id_fails_open,
                                    control_lift_flips_with_no_row_rewrite,
                                    control_token_moves_on_mutation,
                                    current_state, source_restricted)

from veracium import EvidenceAuthor, SqliteStore  # noqa: E402
from veracium.schema import Edge, Provenance  # noqa: E402
from veracium.scope_linkage import identity_digest_of  # noqa: E402
from veracium.store import revocation as rv  # noqa: E402

U = "u"
AT = "2026-08-31T00:00:00Z"


def _edge(obj, *, source="feed-1"):
    return Edge(id=f"e-{uuid.uuid4().hex[:8]}", user_id=U, subject="user",
                relation="located_at", object=obj,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}",
                                      source_id=source))


@pytest.fixture()
def store(tmp_path):
    s = SqliteStore(str(tmp_path / "seam.db"))
    yield s


# ------------------------------------------------------- allocation (F4) --

def test_immediate_schedule_serializes__deferred_is_the_control(tmp_path):
    """The required schedule yields distinct whole batches with ZERO
    allocation refusals; the forbidden DEFERRED schedule reproduces the
    round-3 reviewer's failure (same maxima read, second dies locked)."""
    ok1, ok2 = run_two_connection_schedule(
        str(tmp_path / "imm.db"), immediate_batch, busy_timeout_ms=5000)
    assert ok1.error is None and ok2.error is None, (ok1.error, ok2.error)
    assert ok1.txn != ok2.txn, "two batches shared a txn"
    assert ok1.maxima_read != ok2.maxima_read, \
        "both connections read the same maxima — the lock came too late"
    assert not (set(ok1.seqs) & set(ok2.seqs)), "seq ranges overlap"

    # NEGATIVE CONTROL — the reviewer's reproduction, kept failing forever:
    bad1, bad2 = run_two_connection_schedule(
        str(tmp_path / "def.db"), deferred_batch, busy_timeout_ms=0)
    losers = [r for r in (bad1, bad2) if r.error is not None]
    assert losers and "locked" in losers[0].error, \
        "the DEFERRED schedule no longer fails — control is vacuous"
    assert bad1.maxima_read == bad2.maxima_read, \
        "deferred no longer reads the same maxima — control is vacuous"


# ---------------------------------------------- restriction (F1/F2, X-1) --

def _revoked_superseded_fixture(store):
    """The F2 cell: an INACTIVE superseded edge whose source stands revoked.
    revoke_source SWEEPS but retires only ACTIVE rows (:734), so the edge's
    reason stays `superseded` — the row carries no trace of the restriction."""
    e = _edge("Boston")
    store.add_edge(e)
    store.invalidate_edge(e.id, AT, "superseded")
    d = identity_digest_of(None, "feed-1", store.local_origin())
    rv.revoke_source(store, U, d, "revoke", "seam-model", AT)
    return e, d


def test_typed_membership_restricts__bare_id_is_the_control(store):
    e, d = _revoked_superseded_fixture(store)
    got = source_restricted(store, U, e.id)
    assert got == frozenset({d}), "the F2 cell is not restricted"
    # row untouched: reason is still superseded (history never rewrites)
    import json
    row = store._conn.execute("SELECT json FROM edges WHERE id=?", (e.id,)).fetchone()[0]
    assert json.loads(row)["invalidation_reason"] == "superseded"
    # NEGATIVE CONTROL — round-3 F1's fail-open, permanent:
    assert control_bare_id_fails_open(store, U, e.id), \
        "bare-id membership no longer fails open — control is vacuous"


def test_direct_case_is_in_retire__affected_misses_it(store):
    """X-1's live demonstration: the simplest F2 shape (own source revoked)
    is caught by `retire` and can be entirely absent from `affected`."""
    e, _ = _revoked_superseded_fixture(store)
    assert source_restricted(store, U, e.id)
    assert control_affected_misses_the_direct_case(store, U, e.id), \
        "affected now covers the direct case — retire it as a control " \
        "only with a fixture where it still discriminates"


def test_no_standing_case_is_defined_and_calls_no_sweep(store, monkeypatch):
    """The reviewer's named case: no standing restrictions => frozenset(),
    with ZERO sweep calls — asserted by making any call fail."""
    e = _edge("Paris")
    store.add_edge(e)
    import restriction_derivation as rd
    monkeypatch.setattr(rd, "sweep",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("sweep called with no standing set")))
    assert rd.source_restricted(store, U, e.id) == frozenset()


def test_lift_flips_the_input_without_touching_the_row(store):
    e, _ = _revoked_superseded_fixture(store)
    assert control_lift_flips_with_no_row_rewrite(store, U, e.id, AT), \
        "lift no longer flips the input with the row untouched"


# ------------------------------------------------ CurrentState (F2, one read)

def test_current_state_is_bound_and_token_moves(store):
    e, d = _revoked_superseded_fixture(store)
    cs = current_state(store, U, e.id)
    assert isinstance(cs, CurrentState)
    assert (cs.user_id, cs.edge_id) == (U, e.id), "carrier identity unbound"
    assert cs.current_raw is not None and cs.source_restricted == frozenset({d})
    # NEGATIVE CONTROL — the token must move on ANY user mutation; this
    # assertion fails the day a mutator skips the write-counter bump:
    assert control_token_moves_on_mutation(
        store, U, e.id, lambda: store.add_edge(_edge("Lyon"))), \
        "a mutation did not advance the read token"


def test_missing_row_is_a_defined_carrier_state(store):
    """Defensive totality: no row -> current_raw is None, restriction still
    computed, identity still bound (absence never grants; 0030 owns the
    classification of this shape)."""
    cs = current_state(store, U, "e-never-existed")
    assert cs.current_raw is None
    assert cs.source_restricted == frozenset()
    assert (cs.user_id, cs.edge_id) == (U, "e-never-existed")
