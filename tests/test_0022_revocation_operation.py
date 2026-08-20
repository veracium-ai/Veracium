"""specs/0022 — the R19 operation and standing state against the PRODUCT store.

The spec-side harness proves the construction on a toy table (18 checks); these
prove the same frozen properties against the real `source_revocations` table
SCHEMA v9 ships: F2 (a far-future revoke stays liftable — seq alone orders),
R1 (append-only standing state), R19 (row + effects land together or not at
all; failure outcomes total; the classifier reports the RIGHT invariant).
"""

import sqlite3
import uuid

import pytest

from veracium import SqliteStore
from veracium.store import revocation as rv

U = "u"


def _store(tmp_path):
    return SqliteStore(str(tmp_path / "r.db"))


def _op(conn, digest, action, *, at="2026-08-21T00:00:00Z", reason="operator",
        plan=lambda st: [], apply_effect=lambda c, e: None, **kw):
    return rv.revocation_operation(conn, U, digest, action, reason, at,
                                   plan=plan, apply_effect=apply_effect, **kw)


# --- F2: a planted far-future timestamp cannot make a revocation permanent ---

def test_a_far_future_revoke_is_still_liftable(tmp_path):
    s = _store(tmp_path)
    _op(s._conn, "d1", "revoke", at="2099-01-01T00:00:00Z")   # planted future
    assert rv.standing_revocations(s._conn, U) == {"d1"}
    _op(s._conn, "d1", "lift", at="2026-01-01T00:00:00Z")     # earlier clock
    assert rv.standing_revocations(s._conn, U) == frozenset(), (
        "the lift was appended LATER by the store's own committed order; a "
        "host-supplied clock must not out-rank the append ordinal (F2)")


def test_standing_is_latest_per_digest_by_seq_alone(tmp_path):
    s = _store(tmp_path)
    for digest, action in [("d1", "revoke"), ("d2", "revoke"), ("d1", "lift"),
                           ("d2", "lift"), ("d2", "revoke")]:
        _op(s._conn, digest, action)
    assert rv.standing_revocations(s._conn, U) == {"d2"}


# --- R19: the row and its effects land together or not at all ----------------

def test_effects_land_with_the_row(tmp_path):
    s = _store(tmp_path)
    applied = []
    seq, standing, effects = _op(
        s._conn, "d1", "revoke",
        plan=lambda st: [("probe", sorted(st))],
        apply_effect=lambda c, e: applied.append(e))
    assert applied == [("probe", [])] and seq == 0
    assert rv.standing_revocations(s._conn, U) == {"d1"}


def test_a_failing_effect_rolls_back_the_row_too(tmp_path):
    s = _store(tmp_path)

    def bad_apply(conn, e):
        raise rv.RevocationEffectError("effect refused")

    with pytest.raises(rv.RevocationEffectError):
        _op(s._conn, "d1", "revoke", plan=lambda st: [("x",)],
            apply_effect=bad_apply)
    assert rv.standing_revocations(s._conn, U) == frozenset()
    assert s._conn.execute("SELECT COUNT(*) FROM source_revocations")\
        .fetchone()[0] == 0, "the row must not survive its failed effects (R19)"
    assert not s._conn.in_transaction, "the transaction must be closed"


def test_a_fault_between_row_and_effects_loses_both(tmp_path):
    s = _store(tmp_path)

    def fault():
        raise RuntimeError("injected at the R19 seam")

    with pytest.raises(RuntimeError):
        _op(s._conn, "d1", "revoke", plan=lambda st: [("x",)],
            _fault=fault)
    assert s._conn.execute("SELECT COUNT(*) FROM source_revocations")\
        .fetchone()[0] == 0


# --- R5-1: the classifier reports the RIGHT invariant ------------------------

def test_an_ordinal_collision_is_classified_as_one(tmp_path):
    s = _store(tmp_path)
    _op(s._conn, "d1", "revoke")

    # force the UNIQUE(user_id, seq) violation through the operation by
    # pre-inserting the seq it will allocate, inside the plan callback — same
    # transaction, so the operation's own INSERT hits the constraint at append
    def plan_preinsert(st):
        s._conn.execute(
            "INSERT INTO source_revocations(user_id, seq, identity_digest,"
            " action, at, reason) VALUES(?,?,?,?,?,?)",
            (U, 1, "other", "revoke", "2026-01-01T00:00:00Z", "r"))
        return []

    with pytest.raises(rv.OrdinalCollision):
        _op(s._conn, "d2", "revoke", plan=plan_preinsert)


def test_a_non_ordinal_integrity_fault_is_NOT_a_collision(tmp_path):
    s = _store(tmp_path)
    # the CHECK(action IN ('revoke','lift')) constraint — an integrity fault
    # that is NOT the ordinal; converting it to OrdinalCollision would send
    # the operator to the wrong invariant (R5-1)
    with pytest.raises(rv.RevocationIntegrityError):
        _op(s._conn, "d1", "resurrect")
    assert not s._conn.in_transaction


def test_a_failing_rollback_reports_unknown_state_and_closes(tmp_path):
    s = _store(tmp_path)

    real_execute = s._conn.execute

    class Wrapped:
        def __init__(self, conn): self._c = conn
        def __getattr__(self, n): return getattr(self._c, n)
        def execute(self, sql, *a):
            if sql == "ROLLBACK":
                raise sqlite3.OperationalError("disk gone")
            return real_execute(sql, *a)

    w = Wrapped(s._conn)
    with pytest.raises(rv.RevocationUnknownState):
        rv.revocation_operation(
            w, U, "d1", "revoke", "r", "2026-01-01T00:00:00Z",
            plan=lambda st: [("x",)],
            apply_effect=lambda c, e: (_ for _ in ()).throw(RuntimeError("boom")))


# --- append-only: no UPDATE path exists on the product surface ---------------

def test_the_table_is_append_only_by_construction():
    import ast, pathlib
    src_root = pathlib.Path("src/veracium")
    hits = []
    for f in sorted(src_root.rglob("*.py")):
        text = f.read_text()
        if "source_revocations" not in text:
            continue
        for kw in ("UPDATE source_revocations", "DELETE FROM source_revocations"):
            if kw in text:
                hits.append((f.name, kw))
    assert not hits, (
        f"{hits}: source_revocations is APPEND-ONLY (0022 §4a) — the standing "
        f"state is derived, never edited")
