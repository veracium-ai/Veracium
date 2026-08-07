"""The 0007 §6 invariants, against the real store.

These are the S-invariants fourteen review rounds specified before a line of
them existed. Each test names its invariant. The kernel-level counterexamples
live in `test_schema_model.py`; this file exercises `SqliteStore` itself —
the code path a host actually runs.
"""
from __future__ import annotations

import multiprocessing
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "specs"))

from veracium.store import schema_version as sv  # noqa: E402
from veracium.store.schema_version import (  # noqa: E402
    AdoptionAuditEvent, PostCommitAuditError, StoreVersionError)
from veracium.store.migration import (  # noqa: E402
    MigrationAuditEvent, migrate_store)
from veracium.store.sqlite import _SCHEMA, SqliteStore  # noqa: E402


def _tmp() -> str:
    return tempfile.mktemp(suffix=".db")


def _user_version(path: str) -> int:
    c = sqlite3.connect(path)
    try:
        return c.execute("PRAGMA user_version").fetchone()[0]
    finally:
        c.close()


_SCHEMA_V1 = ";\n".join(o.ddl for o in sv.SCHEMA_V1) + ";\n"


def _legacy_store(rows: int = 3) -> str:
    """A store as every pre-0007 release wrote it: the v1 shape, no stamp. Built
    from SCHEMA_V1 explicitly — `_SCHEMA` now tracks the CURRENT version (v2, with
    the confirmations table), which no release ever wrote. A v1 store below the
    head version is migrated by `migrate_store`, not adopted on open (0013 §5b)."""
    p = _tmp()
    c = sqlite3.connect(p)
    c.executescript(_SCHEMA_V1)
    for i in range(rows):
        c.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,"
                  "quarantined,json) VALUES(?,?,?,?,?,1,0,'{}')",
                  (f"e{i}", "u", f"s{i}", "r", "o"))
    c.commit()
    c.close()
    return p


def _unstamped_current_store() -> str:
    """An UNSTAMPED store already at the CURRENT shape (`_SCHEMA` = v2). This is the
    only shape the §4 adoption path fires for now that the head is v2 — a below-head
    v1 store takes the migration path instead."""
    p = _tmp()
    c = sqlite3.connect(p)
    c.executescript(_SCHEMA)
    c.commit()
    c.close()
    return p


# --- S1, S27: creation ----------------------------------------------------

def test_s1_a_fresh_store_is_stamped():
    p = _tmp()
    SqliteStore(p)
    assert _user_version(p) == sv.SCHEMA_VERSION


def test_s27_an_in_memory_store_works_end_to_end():
    """Round 2's finding: ':memory:' reopened by path is a different database,
    so everything must run on the live connection."""
    store = SqliteStore(":memory:")
    assert store._conn.execute("PRAGMA user_version").fetchone()[0] == sv.SCHEMA_VERSION
    objs = sv.manifest(store._conn)
    assert sv.digest(objs) in sv.accepted_digests(sv.SCHEMA_VERSION) and not sv.drift(objs)


# --- S2, S14, S16, S3/S8/S17: refusals -----------------------------------

def test_s2_a_newer_store_is_refused():
    p = _tmp()
    SqliteStore(p)
    c = sqlite3.connect(p)
    c.execute(f"PRAGMA user_version = {sv.SCHEMA_VERSION + 1}")
    c.close()
    with pytest.raises(StoreVersionError) as e:
        SqliteStore(p)
    assert e.value.reason == "newer" and e.value.found == sv.SCHEMA_VERSION + 1


def test_s14_a_negative_user_version_is_refused():
    p = _tmp()
    SqliteStore(p)
    c = sqlite3.connect(p)
    c.execute("PRAGMA user_version = -1")
    c.close()
    with pytest.raises(StoreVersionError) as e:
        SqliteStore(p)
    assert e.value.reason == "invalid-version"


def test_s16_a_stamped_store_with_the_wrong_shape_is_refused():
    """Round 2's complete bypass: stamping a foreign file skipped validation."""
    p = _tmp()
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE not_ours (x)")
    c.execute(f"PRAGMA user_version = {sv.SCHEMA_VERSION}")
    c.commit()
    c.close()
    with pytest.raises(StoreVersionError) as e:
        SqliteStore(p)
    assert e.value.reason == "stamped-shape-mismatch"
    assert e.value.diff                       # §4b: a refusal names what differs


def test_s3_a_foreign_store_at_version_zero_is_refused():
    p = _tmp()
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE edges (wrong TEXT)")   # veracium-ish, wrong shape
    c.commit()
    c.close()
    with pytest.raises(StoreVersionError) as e:
        SqliteStore(p)
    assert e.value.reason == "foreign-shape"


def test_s17_a_database_with_only_an_unrelated_table_is_refused():
    """Round 1's fixture: v2 called this 'new' and would have built our schema
    beside a foreign table."""
    p = _tmp()
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE unrelated_application_data (x)")
    c.commit()
    c.close()
    with pytest.raises(StoreVersionError) as e:
        SqliteStore(p)
    assert e.value.reason == "foreign-shape"


def test_s8_a_store_with_extra_tables_is_refused():
    p = _legacy_store()
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE extra (x)")
    c.commit()
    c.close()
    with pytest.raises(StoreVersionError) as e:
        SqliteStore(p)
    assert e.value.reason == "foreign-shape"


def test_the_runtime_gate_runs_before_any_shape_decision(monkeypatch):
    monkeypatch.setattr(sv, "runtime_supported", lambda: False)
    with pytest.raises(StoreVersionError) as e:
        SqliteStore(_tmp())
    assert e.value.reason == "unsupported-sqlite"


# --- S6, adoption ---------------------------------------------------------

def test_s6_a_legacy_store_is_migrated_losslessly():
    """0013 §5b: a below-head legacy store is not adopted on ordinary open — it
    REFUSES (migration-required) and is brought forward by the offline
    `migrate_store`, which touches no existing row (the v1→v2 change is additive)."""
    p = _legacy_store(rows=5)
    assert _user_version(p) == 0
    before = sqlite3.connect(p).execute(
        "SELECT id, json FROM edges ORDER BY id").fetchall()
    with pytest.raises(StoreVersionError) as e:
        SqliteStore(p)                         # ordinary open refuses
    assert e.value.reason == "migration-required"
    assert migrate_store(p) == "migrated"      # the offline operation
    assert _user_version(p) == sv.SCHEMA_VERSION
    after = sqlite3.connect(p).execute(
        "SELECT id, json FROM edges ORDER BY id").fetchall()
    assert after == before
    SqliteStore(p)                             # ordinary open now succeeds


def test_allow_adopt_false_refuses_an_unstamped_store(monkeypatch):
    """`allow_adopt=False` refuses the ADOPTION path (an unstamped store already at
    the head shape). The only evidenced unstamped base is v1, below the head, so a
    real unstamped store now takes the migration path; here we make the head shape
    adoptable to exercise the flag's semantics directly."""
    monkeypatch.setattr(sv, "legacy_base_versions",
                        lambda: frozenset({sv.SCHEMA_VERSION}))
    p = _unstamped_current_store()
    with pytest.raises(StoreVersionError) as e:
        SqliteStore(p, allow_adopt=False)
    assert e.value.reason == "adoption-refused"
    assert _user_version(p) == 0              # nothing stamped


def test_adoption_can_only_narrow():
    """allow_adopt=False on an already-stamped store changes nothing."""
    p = _tmp()
    SqliteStore(p)
    SqliteStore(p, allow_adopt=False)         # opens: no adoption involved


# --- S12: drift repair on every path --------------------------------------

def test_s12_a_wrong_same_named_index_is_repaired_on_a_stamped_store():
    """Round 3: `CREATE INDEX IF NOT EXISTS` keeps a wrong same-named index, so
    repair must drop and recreate — and a stamped store never adopts, which is
    why drift is checked on every path."""
    p = _tmp()
    SqliteStore(p)
    c = sqlite3.connect(p)
    c.execute("DROP INDEX ix_edges_subj_rel")
    c.execute("CREATE UNIQUE INDEX ix_edges_subj_rel ON edges(user_id, subject)")
    c.commit()
    c.close()
    SqliteStore(p)
    c = sqlite3.connect(p)
    ddl = c.execute("SELECT sql FROM sqlite_master WHERE name='ix_edges_subj_rel'"
                    ).fetchone()[0]
    assert "UNIQUE" not in ddl


def test_a_missing_acceleration_index_is_repaired_on_migration():
    """A rebuildable index missing from a legacy store is repaired during migration
    — the migration path shares `_validated_current`'s drift repair (S33)."""
    p = _legacy_store()
    c = sqlite3.connect(p)
    c.execute("DROP INDEX ix_episodes_user")
    c.commit()
    c.close()
    assert migrate_store(p) == "migrated"
    c = sqlite3.connect(p)
    assert c.execute("SELECT sql FROM sqlite_master WHERE name='ix_episodes_user'"
                     ).fetchone()


# --- S13: the stamp is transactional --------------------------------------

def test_s13_user_version_rolls_back():
    p = _tmp()
    c = sqlite3.connect(p)
    c.isolation_level = None
    c.execute("BEGIN IMMEDIATE")
    c.execute("PRAGMA user_version = 7")
    c.execute("ROLLBACK")
    assert c.execute("PRAGMA user_version").fetchone()[0] == 0


# --- S5, S20: concurrency -------------------------------------------------

def test_s5_concurrent_first_open_across_threads_stamps_once():
    p = _tmp()
    errors = []

    def opener():
        try:
            SqliteStore(p, busy_timeout_ms=10000)
        except Exception as exc:              # noqa: BLE001 — collected below
            errors.append(exc)

    threads = [threading.Thread(target=opener) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert _user_version(p) == sv.SCHEMA_VERSION


def _open_in_process(path: str, q) -> None:
    try:
        SqliteStore(path, busy_timeout_ms=10000)
        q.put("ok")
    except Exception as exc:                  # noqa: BLE001 — reported via queue
        q.put(repr(exc))


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_s20_concurrent_first_open_across_processes_stamps_once():
    """The product boundary is a file multiple PROCESSES can open (round 3)."""
    p = _tmp()
    ctx = multiprocessing.get_context("fork")
    q = ctx.Queue()
    procs = [ctx.Process(target=_open_in_process, args=(p, q)) for _ in range(4)]
    for pr in procs:
        pr.start()
    for pr in procs:
        pr.join(30)
    results = [q.get(timeout=5) for _ in procs]
    assert results == ["ok"] * 4, results
    assert _user_version(p) == sv.SCHEMA_VERSION


def test_locked_is_refused_loudly_not_hung():
    p = _tmp()
    SqliteStore(p)
    holder = sqlite3.connect(p)
    holder.isolation_level = None
    holder.execute("BEGIN IMMEDIATE")
    holder.execute("INSERT INTO write_counter(user_id, n) VALUES('u', 1)")
    with pytest.raises(StoreVersionError) as e:
        SqliteStore(p, busy_timeout_ms=100)
    assert e.value.reason == "locked"
    holder.execute("ROLLBACK")


# --- S9, S35, S49: the adoption audit -------------------------------------

def test_s49_migration_emits_the_typed_event_pair():
    events = []
    p = _legacy_store()
    migrate_store(p, audit_sink=events.append)
    assert [e.event for e in events] == ["migration_attempted", "migration_committed"]
    a, c = events
    assert isinstance(a, MigrationAuditEvent)
    assert a.migration_id == c.migration_id   # one opaque id pairs them
    assert (a.from_version, a.to_version) == (1, sv.SCHEMA_VERSION)
    # committed repeats every field except event and occurred_at
    assert a._replace(event="", occurred_at="") == c._replace(event="", occurred_at="")


def test_s9_a_sink_that_raises_on_attempted_aborts_the_migration():
    p = _legacy_store()

    def sink(event):
        raise RuntimeError("audit store down")

    with pytest.raises(RuntimeError, match="audit store down"):
        migrate_store(p, audit_sink=sink)
    assert _user_version(p) == 0              # not stamped: no unrecorded migration
    assert not sqlite3.connect(p).execute(     # confirmations was NOT left behind
        "SELECT name FROM sqlite_master WHERE name='confirmations'").fetchone()


def test_s35_a_sink_that_raises_on_committed_leaves_the_store_migrated():
    """The honest outcome. Not a StoreVersionError — a retry sees a current store
    and correctly does not re-migrate (re-open returns `current`)."""
    p = _legacy_store()

    def sink(event):
        if event.event == "migration_committed":
            raise RuntimeError("post-commit sink failure")

    with pytest.raises(PostCommitAuditError) as e:
        migrate_store(p, audit_sink=sink)
    assert not isinstance(e.value, StoreVersionError)
    assert e.value.committed is True
    assert _user_version(p) == sv.SCHEMA_VERSION
    SqliteStore(p)                            # the supported recovery: retry opens


def test_a_creation_does_not_emit_adoption_events():
    events = []
    SqliteStore(_tmp(), audit_sink=events.append)
    assert events == []


def test_an_oversized_path_is_a_validation_error_not_truncation():
    with pytest.raises(ValueError, match="4096"):
        SqliteStore("/tmp/" + "x" * 5000)


# --- packaging: the store must not depend on specs/ -----------------------

def test_the_kernel_never_imports_from_specs():
    """A wheel has no specs/. This lazily held until the 0013 package build:
    `_digest_of_identity` imported `schema_model`, the repo always had specs/
    on sys.path, and the fail-closed predicate swallowed the
    ModuleNotFoundError into `unsupported-sqlite` in any clean environment —
    a total predicate hiding a packaging bug."""
    import re
    src = (ROOT / "src" / "veracium" / "store" / "schema_version.py").read_text()
    hits = re.findall(r"^\s*(?:from|import)\s+(schema_\w+)", src, re.M)
    assert not hits, hits


def test_the_store_qualifies_without_specs_on_the_path(tmp_path):
    import subprocess
    code = ("import sys; sys.path = [p for p in sys.path if 'specs' not in p]\n"
            "from veracium.store.sqlite import SqliteStore\n"
            f"SqliteStore({str(tmp_path / 'clean.db')!r})\n"
            "print('ok')")
    r = subprocess.run([sys.executable, "-c", code],
                       env={"PYTHONPATH": str(ROOT / "src"),
                            "PATH": "/usr/bin:/bin"},
                       capture_output=True, text=True)
    assert r.returncode == 0 and "ok" in r.stdout, r.stderr


# --- 0013 round 11, finding 2: on_committed delivers before cleanup --------

class _RaiseOnIsolationRestore:
    """A connection proxy whose `isolation_level` restore (the post-commit
    `finally`) raises, while `= None` (the arming write before the transaction)
    and every other operation pass through to a real connection."""

    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    @property
    def isolation_level(self):
        return self._real.isolation_level

    @isolation_level.setter
    def isolation_level(self, value):
        if value is not None:                # the finally's restore, post-commit
            raise RuntimeError("post-commit cleanup failed")
        self._real.isolation_level = value


def test_on_committed_delivers_the_committed_result_before_cleanup():
    """0013 round 11, finding 2: every committing branch hands its `OpenResult`
    to `on_committed` the instant it commits — BEFORE the function-level
    `finally` that restores `isolation_level`. v12 built no such seam, so a
    cleanup failure on the return path discarded the return and a caller's
    audit reported v1 for a committed v2 store. Here the finally is forced to
    raise; the caller has ALREADY received committed facts."""
    p = _tmp()
    real = sqlite3.connect(p)
    try:
        seen = []
        with pytest.raises(RuntimeError, match="post-commit cleanup failed"):
            sv.open_versioned(_RaiseOnIsolationRestore(real), p,
                              on_committed=seen.append)
        assert len(seen) == 1
        assert seen[0].transaction_committed is True
        assert seen[0].store_changed is True
        assert seen[0].resulting_version == sv.SCHEMA_VERSION
        assert str(seen[0]) == "created"
    finally:
        real.close()
    # And the store did commit despite the cleanup failure.
    assert _user_version(p) == sv.SCHEMA_VERSION


# --- 0013 round 11, finding 5 (kernel): artifact_problems stays total -------

def test_artifact_problems_is_total_over_an_unhashable_identity_field():
    """0013 round 11, finding 5: a runtime record with `schema_version={}` put
    a dict into the duplicate-check key and `artifact_problems` raised
    `TypeError` at context entry, outside every exception mapping. The record
    is malformed and already reported; the keyability guard means it can no
    longer ALSO crash the by-build and duplicate checks."""
    good = sv.qualified_runtimes()[0]
    poisoned = {**good, "schema_version": {}}
    problems = sv.artifact_problems([good, poisoned])
    assert isinstance(problems, list)
    assert any("schema_version" in p for p in problems)


# --- 0013 round 12, finding 1 (kernel): rollback status is published --------

class _RollbackFails:
    """A connection proxy whose `ROLLBACK` raises, and which passes every other
    statement and attribute through to a real connection."""

    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    def execute(self, sql, *a):
        if sql.strip().upper().startswith("ROLLBACK"):
            raise sqlite3.OperationalError("rollback failed")
        return self._real.execute(sql, *a)


def test_on_rolled_back_reports_the_rollback_outcome():
    """0013 round 12, finding 1: the failure handler discarded the `ROLLBACK`
    result (`except sqlite3.Error: pass`), so a caller recording terminal facts
    could not tell a confirmed rollback from one that itself failed and left the
    store partially migrated — and then asserted the source version for a store
    never restored. The handler now PUBLISHES the outcome."""
    def boom(*a):
        raise RuntimeError("forced failure inside the transaction")

    # ROLLBACK succeeds → "rolled-back"
    p = _tmp()
    seen = []
    with pytest.raises(RuntimeError):
        sv.open_versioned(sqlite3.connect(p), p, new=boom,
                          on_rolled_back=seen.append)
    assert seen == ["rolled-back"]

    # ROLLBACK itself fails → "rollback-failed" (never silently swallowed)
    p2 = _tmp()
    real = sqlite3.connect(p2)
    seen2 = []
    try:
        with pytest.raises(RuntimeError):
            sv.open_versioned(_RollbackFails(real), p2, new=boom,
                              on_rolled_back=seen2.append)
    finally:
        real.close()
    assert seen2 == ["rollback-failed"]


# --- S7: independence -----------------------------------------------------

def test_s7_export_format_version_is_independent():
    from veracium.portability import FORMAT_VERSION
    # A separate namespace from the on-disk SCHEMA_VERSION (specs/0007 §8): it moves
    # only when the WIRE format changes. specs/0009 bumped it 2→3 for its own reason
    # (exports gained seq/supersedes_episode/judgment_time_known). Both happen to read
    # 3 today, by coincidence, not because one drives the other.
    assert FORMAT_VERSION == 3
