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
from restriction_derivation import (CurrentState, autocommit_variant,  # noqa: E402
                                    control_affected_misses_the_direct_case,
                                    control_bare_id_fails_open,
                                    control_lift_flips_with_no_row_rewrite,
                                    control_token_moves_on_mutation,
                                    current_state, source_restricted)
from veracium.scope import Identity, validate_policy  # noqa: E402

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
    assert got is True, "the F2 cell is not restricted"
    # round-4 F4: a BOOLEAN, deliberately — the collective sweep proves the
    # verdict, not per-digest attribution; a digests return would overclaim
    assert isinstance(got, bool)
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
    assert rd.source_restricted(store, U, e.id) is False


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
    assert cs.current_raw is not None and cs.source_restricted is True
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
    assert cs.source_restricted is False
    assert (cs.user_id, cs.edge_id) == (U, "e-never-existed")


# --------------------------------------- round-4 F1: the one consistent read

def test_autocommit_straddle_is_real__the_round4_control(store, tmp_path):
    """The reviewer's reproduction, made a permanent negative control: the
    ROUND-3 design (consecutive autocommit reads) returns a MIXED WORLD when
    a second store instance commits between the reads."""
    e = _edge("Boston")
    store.add_edge(e)
    t0 = current_state(store, U, e.id).read_token
    import json
    from veracium import SqliteStore as _S
    other = _S(str(store._path))
    try:
        def between():
            other.invalidate_edge(e.id, AT, "superseded")
        cs = autocommit_variant(store, U, e.id, between=between)
    finally:
        other.close()
    row_state = json.loads(cs.current_raw)
    assert cs.read_token == t0, "token was read before the foreign write"
    assert row_state["invalidated_at"] is not None, \
        "row was read after it — the straddle is no longer reproducible " \
        "and this control is vacuous"


def test_transactional_read_is_one_world__forced_interleaving(store):
    """Round-4 F1, option (a), PROVEN not asserted: a foreign writer forced
    in immediately BEFORE the scope decision (the reviewer's required
    point) is EXCLUDED for the window — it refuses busy rather than
    interleaving — and every carried value (row, restriction, token, scope
    cell) describes ONE world. After the window closes the same write
    succeeds and a fresh read sees the new world with a moved token."""
    import json
    e = _edge("Boston")
    store.add_edge(e)
    from veracium import SqliteStore as _S
    import sqlite3 as _sq
    other = _S(str(store._path), busy_timeout_ms=50)
    attempted = {}
    def interleave():
        try:
            other.invalidate_edge(e.id, AT, "superseded")
            attempted["outcome"] = "succeeded"
        except _sq.OperationalError as ex:
            attempted["outcome"] = f"refused: {ex}"
    try:
        policy = validate_policy({}, cross_scope_visible=False,
                                 local_origin=store.local_origin())
        cs = current_state(store, U, e.id,
                           principal=Identity(origin=None, source_id="mb-a"),
                           policy=policy, _interleave=interleave)
        assert "refused" in attempted.get("outcome", ""), \
            f"foreign writer was not excluded: {attempted}"
        row_state = json.loads(cs.current_raw)
        assert row_state["invalidated_at"] is None, "row from another world"
        assert cs.source_restricted is False
        assert cs.scope_cell is not None, "scope cell computed in-txn"
        # the window is CLOSED now: the same write succeeds...
        other.invalidate_edge(e.id, AT, "superseded")
        cs2 = current_state(store, U, e.id)
        assert json.loads(cs2.current_raw)["invalidated_at"] is not None
        assert cs2.read_token > cs.read_token, "token moved with the world"
    finally:
        other.close()
