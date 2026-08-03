"""The 0013 draft instrument, exercised against the concrete v1→v2 migration.

These test the MEASURING INSTRUMENT (`specs/migrations_0013.py`), not the
store: `0013` is `draft` and authorises no implementation. They exist so the
first external review of `0013` reviews a migration that runs — the round-9
M-Q1 ruling — rather than prose about one.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "specs"))

import migrations_0013 as m13  # noqa: E402
from veracium.store.schema_version import identity, manifest  # noqa: E402


def _v1_store(rows: int = 3) -> str:
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    for o in m13.SCHEMA_V1:
        c.execute(o.ddl)
    for i in range(rows):
        c.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,"
                  "quarantined,json) VALUES(?,?,?,?,?,1,0,'{}')",
                  (f"e{i}", "u", f"s{i}", "r", "o"))
    c.execute("PRAGMA user_version = 1")
    c.commit()
    c.close()
    return p


# --- M6/M7-class: the destination contract, against the real migration ----

def test_the_concrete_migration_reaches_the_v2_constructor_output():
    """The additive change means the two provenances converge on one digest —
    stated in the spec as a measured property, verified here."""
    p = _v1_store()
    assert m13.open_or_migrate(p) == "migrated"
    mig = sqlite3.connect(p)
    cons = sqlite3.connect(":memory:")
    for o in m13.SCHEMA_V2:
        cons.execute(o.ddl)
    assert identity(manifest(mig)) == identity(manifest(cons))


def test_migration_preserves_every_row():
    p = _v1_store(rows=5)
    before = sqlite3.connect(p).execute(
        "SELECT id FROM edges ORDER BY id").fetchall()
    m13.open_or_migrate(p)
    after = sqlite3.connect(p).execute(
        "SELECT id FROM edges ORDER BY id").fetchall()
    assert after == before


def test_an_empty_migration_cannot_authorize_its_output():
    """0007 round 6's founding case, against the concrete destination."""
    p = _v1_store()
    c = sqlite3.connect(p)
    problems = m13.destination_problems(manifest(c), 2)
    assert any("confirmations" in pr for pr in problems)


def test_a_partial_migration_is_rejected():
    p = _v1_store()
    c = sqlite3.connect(p)
    c.execute(m13.CONFIRMATIONS_DDL)          # table but not the index — index
    c.commit()                                # is REBUILDABLE, so this passes…
    assert m13.destination_problems(manifest(c), 2) == []
    c.execute("DROP TABLE confirmations")
    c.execute("CREATE TABLE confirmations (id TEXT)")   # wrong columns
    c.commit()
    assert any("columns differ" in pr
               for pr in m13.destination_problems(manifest(c), 2))


# --- M2/M3/M4-class: confinement, with the real harness -------------------

@pytest.mark.parametrize("stmt", ["COMMIT", "END", "END TRANSACTION",
                                  "ROLLBACK", "RELEASE s",
                                  "PRAGMA writable_schema=ON"])
def test_transaction_control_and_pragmas_are_denied(stmt):
    c = sqlite3.connect(":memory:")
    c.isolation_level = None
    c.execute("CREATE TABLE t (a)")
    c.execute("BEGIN IMMEDIATE")
    with pytest.raises(sqlite3.DatabaseError):
        m13.apply_migration(c, m13.Migration(1, 2, (stmt,)))
    assert c.in_transaction


def test_a_temp_object_is_refused():
    c = sqlite3.connect(":memory:")
    c.isolation_level = None
    c.execute("CREATE TABLE t (a)")
    c.execute("BEGIN IMMEDIATE")
    with pytest.raises(sqlite3.DatabaseError):
        m13.apply_migration(c, m13.Migration(1, 2, (
            "CREATE TEMP TRIGGER x AFTER INSERT ON t BEGIN DELETE FROM t; END",)))


def test_the_authorizer_is_restored_after_failure():
    c = sqlite3.connect(":memory:")
    c.isolation_level = None
    c.execute("CREATE TABLE t (a)")
    c.execute("BEGIN IMMEDIATE")
    with pytest.raises(sqlite3.DatabaseError):
        m13.apply_migration(c, m13.Migration(1, 2, ("COMMIT",)))
    c.execute("COMMIT")                       # the planner's own commit works
    assert not c.in_transaction


# --- M9: the registry -----------------------------------------------------

def test_m9_the_draft_registry_is_well_formed():
    assert m13.validate_registry() == []


def test_a_gap_refuses():
    assert m13.validate_registry(
        schemas={1: m13.SCHEMA_V1, 2: m13.SCHEMA_V2}, migrations={}, current=2)


# --- M13 / M-Q2: concurrency is the write lock ----------------------------

def test_mq2_concurrent_migration_runs_exactly_once():
    """The M-Q2 answer, demonstrated: SQLite's write lock serialises the
    migration; losers re-read under their own lock and find it done."""
    p = _v1_store()
    results = []

    def worker():
        results.append(m13.open_or_migrate(p, busy_timeout_ms=10000))

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["current"] * 4 + ["migrated"], results
    c = sqlite3.connect(p)
    assert c.execute("PRAGMA user_version").fetchone()[0] == 2
    assert c.execute("SELECT COUNT(*) FROM confirmations").fetchone()[0] == 0


# --- 0008 §6c semantics hold in the migrated schema -----------------------

def test_the_0008_uniqueness_contract_holds():
    """Round 2 corrected the model: an omitted correlation id is GENERATED and
    persisted (0008 §6c returns `str`, never null), so NULL is refused, distinct
    generated ids coexist, a reused pair conflicts, and the scope is the
    tenant — another user may reuse the same id."""
    p = _v1_store()
    m13.open_or_migrate(p)
    c = sqlite3.connect(p)
    ins = ("INSERT INTO confirmations(id,user_id,edge_id,confirmed_at,actor,"
           "call_path,correlation_id,request_digest) VALUES(?,?,?,?,?,?,?,?)")
    c.execute(ins, ("c1", "u", "e0", "t", "user", "host_api", "gen-a", "d1"))
    c.execute(ins, ("c2", "u", "e1", "t", "user", "host_api", "gen-b", "d2"))
    with pytest.raises(sqlite3.IntegrityError):
        c.execute(ins, ("c3", "u", "e2", "t", "user", "host_api", "gen-a", "d3"))
    c.execute(ins, ("c5", "v", "e9", "t", "user", "host_api", "gen-a", "d5"))
    with pytest.raises(sqlite3.IntegrityError):     # NULL correlation refused
        c.execute(ins, ("c6", "u", "e4", "t", "user", "host_api", None, "d6"))
    with pytest.raises(sqlite3.IntegrityError):     # NULL id refused too
        c.execute(ins, (None, "u", "e5", "t", "user", "host_api", "gen-z", "d7"))


# --- round 2 of this spec's review ----------------------------------------

def test_a_wrong_unique_constraint_is_not_stamped(monkeypatch):
    """Round 2, findings 2–3: capability compared columns only, so a global
    UNIQUE(correlation_id) — violating 0008's tenant scoping — was stamped."""
    bad = m13.CONFIRMATIONS_DDL.replace("UNIQUE(user_id, correlation_id)",
                                        "UNIQUE(correlation_id)")
    monkeypatch.setattr(m13, "MIGRATION_1_TO_2",
                        m13.Migration(1, 2, (bad, m13.IX_CONFIRMATIONS_DDL)))
    p = _v1_store()
    assert m13.open_or_migrate(p).startswith("migration-result-mismatch")
    c = sqlite3.connect(p)
    assert c.execute("PRAGMA user_version").fetchone()[0] == 1   # rolled back


def test_a_missing_rebuildable_index_is_repaired_before_stamping(monkeypatch):
    """Round 2, finding 4: a migrated store must not be returned in a state
    0007 would immediately call drifted."""
    monkeypatch.setattr(m13, "MIGRATION_1_TO_2",
                        m13.Migration(1, 2, (m13.CONFIRMATIONS_DDL,)))
    p = _v1_store()
    assert m13.open_or_migrate(p) == "migrated"
    c = sqlite3.connect(p)
    ddl = c.execute("SELECT sql FROM sqlite_master WHERE "
                    "name='ix_confirmations_edge'").fetchone()
    assert ddl and ddl[0] == m13.IX_CONFIRMATIONS_DDL


def test_a_stray_step_beyond_the_current_version_is_rejected():
    """Round 2, finding 6: exact key sets, both directions."""
    probs = m13.validate_registry(
        schemas={1: m13.SCHEMA_V1, 2: m13.SCHEMA_V2},
        migrations={1: m13.MIGRATION_1_TO_2,
                    2: m13.Migration(2, 3, ("SELECT 1",))},
        current=2)
    assert any("exactly" in p for p in probs)


def test_an_empty_statement_tuple_does_not_validate():
    probs = m13.validate_registry(
        schemas={1: m13.SCHEMA_V1, 2: m13.SCHEMA_V2},
        migrations={1: m13.Migration(1, 2, ())}, current=2)
    assert any("nonempty" in p for p in probs)


def test_mq2_hazard_a_stale_v1_connection_writes_after_migration():
    """Round 2, finding 5 — DEMONSTRATED, not fixed: the write lock serialises
    the migration itself, but a connection opened before it never re-runs the
    version gate, so an already-running v1 process keeps applying v1 behaviour
    to a v2 store. For 0008 that is the unaudited clearing path. This is why
    the M-Q2 ruling is adopt-WITH-CONDITIONS: the deployment quiescence
    contract in §5b is load-bearing, and this test is the measurement that
    makes it so."""
    p = _v1_store()
    old = sqlite3.connect(p)                       # a v1-era process
    assert m13.open_or_migrate(p) == "migrated"
    old.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,"
                "quarantined,json) VALUES('stale','u','s','r','o',1,0,'{}')")
    old.commit()                                   # succeeds: nothing fences it
    c = sqlite3.connect(p)
    assert c.execute("SELECT COUNT(*) FROM edges WHERE id='stale'"
                     ).fetchone()[0] == 1