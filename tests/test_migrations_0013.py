"""The 0013 draft instrument, exercised against the concrete v1→v2 migration.

These test the MEASURING INSTRUMENT (`specs/migrations_0013.py`), not the
store: `0013` is in review and authorises no implementation. They exist so the
external review of `0013` reviews a migration that runs — the round-9 M-Q1
ruling — rather than prose about one.

Round 3's architecture holds throughout: `open_or_migrate` / `migrate_store`
run the PRODUCTION `0007` planner under the draft registry, migrations are
authorised by the recorded evidence artifact, and every outcome is a member of
the closed vocabulary.
"""
from __future__ import annotations

import copy
import json
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "specs"))

import migrations_0013 as m13  # noqa: E402

from veracium.store import schema_version as sv  # noqa: E402
from veracium.store.schema_version import identity, manifest  # noqa: E402


def _v1_store(rows: int = 3, stamp: bool = True, extra: str | None = None) -> str:
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    for o in m13.SCHEMA_V1:
        c.execute(o.ddl)
    for i in range(rows):
        c.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,"
                  "quarantined,json) VALUES(?,?,?,?,?,1,0,'{}')",
                  (f"e{i}", "u", f"s{i}", "r", "o"))
    if extra:
        c.execute(extra)
    if stamp:
        c.execute("PRAGMA user_version = 1")
    c.commit()
    c.close()
    return p


def _patch_migration(monkeypatch, mig: m13.Migration) -> None:
    """A patched declaration must land in BOTH names the instrument reads."""
    monkeypatch.setattr(m13, "MIGRATION_1_TO_2", mig)
    monkeypatch.setitem(m13.MIGRATIONS_DRAFT, 1, mig)


def _patch_artifact(monkeypatch, art) -> None:
    """Install a crafted artifact as the operation snapshot. The digest is
    the REAL file's — authorities mint against the file, so evidence-digest
    binding passes while the parsed content is the crafted one (the same
    semantics the pre-snapshot seam had)."""
    real_digest = m13._artifact_snapshot()[1]
    monkeypatch.setattr(m13, "_artifact_snapshot",
                        lambda: (copy.deepcopy(art), real_digest))


def _bound_auth(target: str) -> "m13.MigrationAuthority":
    """An authority path-rebound to `target`. Round 7 made minting refuse
    unless it observes an accepted source, so tests probing NON-source
    targets (foreign shapes, malformed stamps, garbage bytes) mint against a
    valid twin and rebind only the canonical path — the planner's own
    classification is then what the test measures."""
    import os
    return m13.make_authority(_v1_store())._replace(
        store_path=os.path.realpath(target))


def _crafted_artifact(monkeypatch, declaration_digest: str) -> None:
    """The committed artifact with its one path record re-pointed at a
    DIFFERENT migration declaration, output fields untouched. This is the only
    way `migration-failed` and `migration-result-mismatch` stay reachable —
    the evidence gate otherwise refuses an altered migration before it runs —
    and it models the real hazard those outcomes exist for: recorded evidence
    whose promise the live execution does not keep."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["paths"][0]["migration_declaration_digest"] = declaration_digest
    _patch_artifact(monkeypatch, art)


# --- M6/M7-class: the destination contract, against the real migration ----

def test_the_concrete_migration_reaches_the_v2_constructor_output():
    """The additive change means the two provenances converge on one digest —
    stated in the spec as a measured property, verified here."""
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) == "migrated"
    mig = sqlite3.connect(p)
    assert identity(manifest(mig)) == m13._v2_constructor_objects()


def test_migration_preserves_every_row():
    p = _v1_store(rows=5)
    before = sqlite3.connect(p).execute(
        "SELECT id FROM edges ORDER BY id").fetchall()
    m13.migrate_store(p, m13.make_authority(p))
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


def test_the_executor_requires_an_existing_transaction():
    """Round 3, finding 4 (round 2 lineage): on autocommit, a failed migration
    left its first statement durably applied."""
    c = sqlite3.connect(tempfile.mktemp(suffix=".db"))
    c.isolation_level = None                     # autocommit, no BEGIN
    with pytest.raises(RuntimeError, match="migration-protocol"):
        m13.apply_migration(c, m13.Migration(1, 2, ("CREATE TABLE partial (x)",)))
    assert not c.execute("SELECT name FROM sqlite_master "
                         "WHERE name='partial'").fetchone()


# --- M9: the registry -----------------------------------------------------

def test_m9_the_draft_registry_is_well_formed():
    assert m13.validate_registry() == []


def test_a_gap_refuses():
    assert m13.validate_registry(
        schemas={1: m13.SCHEMA_V1, 2: m13.SCHEMA_V2}, migrations={}, current=2)


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


def test_a_list_statement_container_does_not_validate():
    probs = m13.validate_registry(
        schemas={1: m13.SCHEMA_V1, 2: m13.SCHEMA_V2},
        migrations={1: m13.Migration(1, 2, ["SELECT 1"])}, current=2)
    assert any("nonempty" in p or "tuple" in p for p in probs)


# --- M13 / M-Q2: concurrency is the write lock ----------------------------

def test_mq2_concurrent_migration_runs_exactly_once():
    """The M-Q2 answer, demonstrated: SQLite's write lock serialises the
    migration; losers re-read under their own lock and find it done."""
    p = _v1_store()
    results = []

    def worker():
        results.append(m13.migrate_store(p, m13.make_authority(p),
                                         busy_timeout_ms=10000))

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["current"] * 4 + ["migrated"], results
    c = sqlite3.connect(p)
    assert c.execute("PRAGMA user_version").fetchone()[0] == 2
    assert c.execute("SELECT COUNT(*) FROM confirmations").fetchone()[0] == 0


def test_mq2_hazard_a_stale_v1_connection_writes_after_migration():
    """Round 2, finding 5 — DEMONSTRATED, not fixed: the write lock serialises
    the migration itself, but a connection opened before it never re-runs the
    version gate, so an already-running v1 process keeps applying v1 behaviour
    to a v2 store. For 0008 that is the unaudited clearing path. This is why
    ordinary opening refuses (`migration-required`) and migration is an
    explicit offline operation whose authority attests quiescence: the library
    cannot fence what it cannot see, so the trusted deployment authority owns
    quiescence, old-binary fencing, and backup validity (§5b)."""
    p = _v1_store()
    old = sqlite3.connect(p)                       # a v1-era process
    assert m13.migrate_store(p, m13.make_authority(p)) == "migrated"
    old.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,"
                "quarantined,json) VALUES('stale','u','s','r','o',1,0,'{}')")
    old.commit()                                   # succeeds: nothing fences it
    c = sqlite3.connect(p)
    assert c.execute("SELECT COUNT(*) FROM edges WHERE id='stale'"
                     ).fetchone()[0] == 1


# --- 0008 §6c semantics hold in the migrated schema -----------------------

def test_the_0008_uniqueness_contract_holds():
    """Round 2 corrected the model: an omitted correlation id is GENERATED and
    persisted (0008 §6c returns `str`, never null), so NULL is refused, distinct
    generated ids coexist, a reused pair conflicts, and the scope is the
    tenant — another user may reuse the same id."""
    p = _v1_store()
    m13.migrate_store(p, m13.make_authority(p))
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


# --- round 3, finding 1: the full inherited 0007 planner ------------------

def test_an_empty_database_is_created_current():
    """Round 3 measured `unexpected version 0`; the shared planner's *new*
    row creates the current version."""
    p = tempfile.mktemp(suffix=".db")
    sqlite3.connect(p).close()
    assert m13.open_or_migrate(p) == "created"
    c = sqlite3.connect(p)
    assert c.execute("PRAGMA user_version").fetchone()[0] == 2
    assert identity(manifest(c)) == m13._v2_constructor_objects()
    c.close()
    assert m13.open_or_migrate(p) == "current"


def test_an_unstamped_v1_store_takes_the_older_row():
    """Round 3 measured `unexpected version 0`; candidate-restricted legacy
    resolution finds base 1, and the older row refuses ordinarily / migrates
    under authority — rows intact."""
    p = _v1_store(rows=2, stamp=False)
    assert m13.open_or_migrate(p) == "migration-required"
    assert m13.migrate_store(p, m13.make_authority(p)) == "migrated"
    c = sqlite3.connect(p)
    assert c.execute("PRAGMA user_version").fetchone()[0] == 2
    assert c.execute("SELECT COUNT(*) FROM edges").fetchone()[0] == 2


def test_a_foreign_version_zero_store_is_refused_by_both_operations():
    p = _v1_store(stamp=False, extra="CREATE TABLE alien (x)")
    assert m13.open_or_migrate(p) == "foreign-shape"
    assert m13.migrate_store(p, _bound_auth(p)) == "foreign-shape"


def test_a_malformed_stamped_source_is_not_promised_a_migration():
    """Round 3: a stamped v1 store with an unauthorized extra table answered
    `migration-required`, promising a migration path for a store that has
    none. Source classification precedes any migration statement."""
    p = _v1_store(extra="CREATE TABLE intruder (x)")
    assert m13.open_or_migrate(p) == "stamped-shape-mismatch"
    assert m13.migrate_store(p, _bound_auth(p)) == "stamped-shape-mismatch"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 1


def test_a_newer_store_is_refused():
    p = _v1_store()
    c = sqlite3.connect(p)
    c.execute("PRAGMA user_version = 3")
    c.commit()
    c.close()
    assert m13.open_or_migrate(p) == "newer"


def test_a_table_squatting_a_rebuildable_index_name_is_a_closed_refusal():
    """Round 3: the v4 current branch tried typed drift repair before
    classifying the shape and raised OperationalError. The shared planner's
    typed digest sees `table:ix_confirmations_edge` as a foreign object and
    refuses closed, before any repair statement runs."""
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    for o in m13.SCHEMA_V2:
        if o.name != "ix_confirmations_edge":
            c.execute(o.ddl)
    c.execute("CREATE TABLE ix_confirmations_edge (x)")
    c.execute("PRAGMA user_version = 2")
    c.commit()
    c.close()
    assert m13.open_or_migrate(p) == "stamped-shape-mismatch"


def test_ordinary_open_refuses_with_migration_required():
    """Ordinary opening cannot initiate migration — the offline boundary as a
    mechanism, not a convention."""
    p = _v1_store()
    assert m13.open_or_migrate(p) == "migration-required"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 1


def test_a_malformed_stamped_v2_store_is_refused():
    p = _v1_store()
    m13.migrate_store(p, m13.make_authority(p))
    c = sqlite3.connect(p)
    c.execute("ALTER TABLE confirmations ADD COLUMN sneaky TEXT")
    c.commit()
    c.close()
    assert m13.open_or_migrate(p) == "stamped-shape-mismatch"


def test_a_drifted_v2_index_is_repaired_on_current():
    p = _v1_store()
    m13.migrate_store(p, m13.make_authority(p))
    c = sqlite3.connect(p)
    c.execute("DROP INDEX ix_confirmations_edge")
    c.commit()
    c.close()
    assert m13.open_or_migrate(p) == "current"
    c = sqlite3.connect(p)
    assert c.execute("SELECT sql FROM sqlite_master WHERE "
                     "name='ix_confirmations_edge'").fetchone()


def test_the_outcome_vocabulary_is_closed():
    """`unexpected version 0` and its class are unrepresentable."""
    with pytest.raises(ValueError):
        m13.Outcome("unexpected version 0")


# --- round 3, finding 2: recorded evidence, never self-generated ----------

def test_a_data_destructive_alteration_cannot_authorize_itself(monkeypatch):
    """THE round-3 probe: `DELETE FROM edges` appended to the migration
    produced the exact v2 schema and stamped `migrated` with zero edge rows,
    because the expected record was derived from the live code. Selection is
    now over the committed artifact, keyed by the declaration digest — the
    altered migration matches nothing, refuses before executing, and the data
    and stamp are untouched."""
    _patch_migration(monkeypatch, m13.Migration(
        1, 2, m13.MIGRATION_1_TO_2.statements + ("DELETE FROM edges",)))
    p = _v1_store(rows=3)
    out = m13.migrate_store(p, m13.make_authority(p))
    assert out == "migration-evidence-missing"
    c = sqlite3.connect(p)
    assert c.execute("PRAGMA user_version").fetchone()[0] == 1
    assert c.execute("SELECT COUNT(*) FROM edges").fetchone()[0] == 3


def test_a_side_effect_free_alteration_is_still_not_evidenced(monkeypatch):
    _patch_migration(monkeypatch, m13.Migration(
        1, 2, m13.MIGRATION_1_TO_2.statements + ("SELECT 1",)))
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) \
        == "migration-evidence-missing"


def test_a_zeroed_source_hash_is_consulted_and_refuses(monkeypatch):
    """Round 3 measured the recorded source hash being generated but never
    read. It is now part of both the record's consistency rules and the
    selection key."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["paths"][0]["source_full_manifest_hash"] = "0" * 64
    _patch_artifact(monkeypatch, art)
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) \
        == "migration-evidence-missing"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 1


def test_an_absent_path_record_refuses(monkeypatch):
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["paths"] = []
    _patch_artifact(monkeypatch, art)
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) \
        == "migration-evidence-missing"


def test_a_duplicate_path_record_refuses(monkeypatch):
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["paths"].append(copy.deepcopy(art["paths"][0]))
    _patch_artifact(monkeypatch, art)
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) \
        == "migration-evidence-missing"


def test_a_stale_algorithm_record_is_superseded_not_consumed(monkeypatch):
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["paths"][0]["migration_evidence_algorithm"] = 0
    _patch_artifact(monkeypatch, art)
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) \
        == "migration-evidence-missing"


def test_a_contradictory_output_fails_the_record_consistency_rules():
    """§5c's record-level rules, directly: recorded output must hash to BOTH
    recorded hashes and resolve to an accepted destination manifestation."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    rec = copy.deepcopy(art["paths"][0])
    rec["output_full_manifest_hash"] = "f" * 64
    with m13._registry():
        probs = m13.path_record_problems(rec, art)
    assert any("full-manifest hash" in p for p in probs)
    rec = copy.deepcopy(art["paths"][0])
    del rec["output_manifestation"]["index:ix_confirmations_edge"]
    with m13._registry():
        probs = m13.path_record_problems(rec, art)
    assert probs


def test_a_tampered_accepted_manifest_poisons_the_whole_context(monkeypatch):
    """0007 round 12's rule carried over: a malformed current-algorithm
    record is evidence of tampering, and the safe reading is `unqualified` —
    everything fails closed to unsupported-sqlite."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["schema_versions"]["2"]["accepted"][0]["digest"] = "0" * 64
    _patch_artifact(monkeypatch, art)
    p = _v1_store()
    assert m13.open_or_migrate(p) == "unsupported-sqlite"


# --- round 3, finding 3: migration-runtime qualification ------------------

def test_the_migration_runtime_gate_is_independent_of_0007s(monkeypatch):
    """A runtime qualified for schema construction is NOT thereby qualified
    for migration confinement. Removing the migration-runtime record refuses
    the migration operation while ordinary opening is untouched."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["migration_runtimes"] = []
    _patch_artifact(monkeypatch, art)
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) == "unsupported-sqlite"
    assert m13.open_or_migrate(p) == "migration-required"


def test_recorded_confinement_behaviours_must_reproduce_live(monkeypatch):
    """The record is not trusted: consumption re-runs the probes and compares,
    mirroring how runtime_supported() re-derives constructor manifestations."""
    real = m13.authorizer_probes()
    lying = dict(real, denies_pragma=False)
    monkeypatch.setattr(m13, "authorizer_probes", lambda: lying)
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) == "unsupported-sqlite"


def test_a_record_with_a_failed_probe_never_qualifies():
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    rec = copy.deepcopy(art["migration_runtimes"][0])
    rec["authorizer_probes"]["denies_attach"] = False
    assert any("required confinement" in p
               for p in m13.migration_runtime_record_problems(rec))


def test_the_authorizer_probes_all_hold_on_this_runner():
    probes = m13.authorizer_probes()
    assert set(probes) == m13.AUTHORIZER_PROBE_KEYS
    assert all(v is True for v in probes.values()), probes


# --- round 3, finding 4: the closed failure model -------------------------

def test_invalid_sql_returns_migration_failed_not_an_exception(monkeypatch):
    """Round 3 measured a raw OperationalError escaping. With the declaration
    digest matching recorded evidence (crafted — the honest generator refuses
    to record a failing migration), execution fails and the caller receives
    the closed outcome; the transaction rolled back."""
    bad = m13.Migration(1, 2, (m13.CONFIRMATIONS_DDL, "CREATE BOGUS ("))
    _patch_migration(monkeypatch, bad)
    _crafted_artifact(monkeypatch, m13.migration_declaration_digest(bad))
    p = _v1_store(rows=2)
    out = m13.migrate_store(p, m13.make_authority(p))
    assert out == "migration-failed"
    c = sqlite3.connect(p)
    assert c.execute("PRAGMA user_version").fetchone()[0] == 1
    assert c.execute("SELECT COUNT(*) FROM edges").fetchone()[0] == 2


def test_a_wrong_unique_constraint_is_a_result_mismatch(monkeypatch):
    """Round 2's regression, preserved at its correct layer: evidence promises
    the true v2 output, the executed migration produces a global UNIQUE —
    violating 0008's tenant scoping — and the comparison refuses and rolls
    back before any stamp."""
    bad_ddl = m13.CONFIRMATIONS_DDL.replace("UNIQUE(user_id, correlation_id)",
                                            "UNIQUE(correlation_id)")
    bad = m13.Migration(1, 2, (bad_ddl, m13.IX_CONFIRMATIONS_DDL))
    _patch_migration(monkeypatch, bad)
    _crafted_artifact(monkeypatch, m13.migration_declaration_digest(bad))
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) \
        == "migration-result-mismatch"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 1


def test_a_missing_rebuildable_index_is_repaired_before_stamping(monkeypatch):
    """Round 2, finding 4, preserved: the evidence job records the REPAIRED
    output, so an index-less declared migration is regenerated as evidence,
    executes, is repaired, and matches — never stamped drifted."""
    _patch_migration(monkeypatch,
                     m13.Migration(1, 2, (m13.CONFIRMATIONS_DDL,)))
    art, problems = m13._generate_artifact()
    assert problems == []
    _patch_artifact(monkeypatch, art)
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) == "migrated"
    c = sqlite3.connect(p)
    ddl = c.execute("SELECT sql FROM sqlite_master WHERE "
                    "name='ix_confirmations_edge'").fetchone()
    assert ddl and ddl[0] == m13.IX_CONFIRMATIONS_DDL


def test_an_unqualified_runtime_cannot_open_or_migrate(monkeypatch):
    monkeypatch.setattr(sv, "runtime_supported", lambda: False)
    p = _v1_store()
    assert m13.open_or_migrate(p) == "unsupported-sqlite"
    assert m13.migrate_store(p, m13.make_authority(p)) == "unsupported-sqlite"


def test_the_simulator_stops_cleanly_after_a_runtime_refusal(monkeypatch, capsys):
    """Round 3: the simulator printed three refusals, then continued into
    confirmation-table operations and crashed."""
    monkeypatch.setattr(sv, "runtime_supported", lambda: False)
    rc = m13.simulate()
    assert rc == 2
    assert "unsupported-sqlite" in capsys.readouterr().out


# --- the migration authority: exact types, exact bindings ------------------

def test_a_truthy_but_untyped_authority_is_refused():
    """Round 3 measured MigrationAuthority(quiesced=1, backup_ref=object())
    migrating."""
    p = _v1_store()
    loose = m13.make_authority(p)._replace(quiesced=1, backup_ref=object())
    assert m13.migrate_store(p, loose) == "migration-quiescence-required"


def test_an_unquiesced_authority_is_refused():
    p = _v1_store()
    bad = m13.make_authority(p)._replace(quiesced=False)
    assert m13.migrate_store(p, bad) == "migration-quiescence-required"


def test_an_authority_is_bound_to_one_store():
    p1, p2 = _v1_store(), _v1_store()
    assert m13.migrate_store(p2, m13.make_authority(p1)) \
        == "migration-quiescence-required"


def test_an_authority_is_bound_to_the_reviewed_migration():
    p = _v1_store()
    bad = m13.make_authority(p)._replace(migration_digest="0" * 64)
    assert m13.migrate_store(p, bad) == "migration-quiescence-required"


def test_ordinary_open_has_no_authority_parameter():
    """The migration operation is not exposed through tenant-facing opening."""
    import inspect
    assert "authority" not in inspect.signature(m13.open_or_migrate).parameters


# --- the evidence artifact reproduces -------------------------------------

def test_the_committed_evidence_artifact_is_valid_and_reproduces():
    """`--check-evidence`'s core, as a regression: the committed artifact
    passes every validator, and on the recording runtime it reproduces
    exactly (modulo the generation timestamp)."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    with m13._registry():
        assert m13.schema_evidence_problems(art) == []
        assert m13.path_evidence_problems(art) == []
        recorded = {sv.build_identity(r)
                    for r in sv.active_records(art["runtimes"])}
        mine = sv.build_identity(sv.runtime_identity())
    if mine not in recorded:
        pytest.skip("artifact records a different runtime identity; "
                    "regenerate with --write-evidence to verify here")
    expected, problems = m13._generate_artifact()
    assert problems == []
    drop = {"generated_at", "generator"}      # volatile provenance fields
    assert {k: v for k, v in art.items() if k not in drop} \
        == {k: v for k, v in expected.items() if k not in drop}


def test_full_manifest_hash_sees_what_the_acceptance_digest_excludes():
    """Round 3, finding 2, the founding measurement: acceptance digests were
    equal while complete manifestations differed on the rebuildable index."""
    with m13._registry():
        full = m13._v2_constructor_objects()
        partial = {k: v for k, v in full.items()
                   if k != "index:ix_confirmations_edge"}
        assert sv._digest_of_identity(full, 2) \
            == sv._digest_of_identity(partial, 2)        # blind, by design
        assert m13.full_manifest_hash(full) != m13.full_manifest_hash(partial)


# --- round 4, finding 1: the failure boundary is actually total ------------

def test_a_malformed_accepted_manifestation_fails_closed(monkeypatch):
    """Round 4 measured `objects: 1` raising TypeError out of context entry.
    Any malformed nested field in the schema evidence poisons the context and
    every operation reads `unsupported-sqlite` — no exception escapes."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["schema_versions"]["1"]["accepted"][0]["objects"] = 1
    _patch_artifact(monkeypatch, art)
    p = _v1_store()
    assert m13.open_or_migrate(p) == "unsupported-sqlite"
    assert m13.migrate_store(p, m13.make_authority(p)) == "unsupported-sqlite"


def test_a_malformed_path_field_fails_closed(monkeypatch):
    """Round 4 measured a list-valued source hash raising `unhashable type`
    from selection-key construction."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["paths"][0]["source_full_manifest_hash"] = ["x"]
    _patch_artifact(monkeypatch, art)
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) \
        == "migration-evidence-missing"


def test_a_non_database_file_is_a_closed_refusal():
    """Round 4 measured `sqlite3.DatabaseError: file is not a database`
    escaping both operations. The migrating authority is path-bound to the
    garbage file: round 5 moved static authority validation ahead of any
    store access, so only a path-matching authority reaches the store at all."""
    import os
    p = tempfile.mktemp(suffix=".db")
    with open(p, "w") as f:
        f.write("these bytes are not a sqlite database")
    assert m13.open_or_migrate(p) == "invalid-store"
    bound = m13.make_authority(_v1_store())._replace(
        store_path=os.path.realpath(p))
    assert m13.migrate_store(p, bound) == "invalid-store"


def test_an_unopenable_path_is_a_closed_refusal():
    """Round 4 measured an uncaught OperationalError for a missing parent
    directory. Round 6 split the outcome by mode: ordinary opening reports
    the storage failure; the dedicated migration reports the SOURCE failure,
    because its authority attests a store that is not there."""
    import os
    p = tempfile.mktemp(suffix=".db") + "-no-such-dir/store.db"
    assert m13.open_or_migrate(p) == "store-unopenable"
    bound = m13.make_authority(_v1_store())._replace(
        store_path=os.path.realpath(p))
    assert m13.migrate_store(p, bound) == "migration-source-missing"


def test_registry_validation_is_total_over_malformed_keys():
    """Round 4: mixed key types raised TypeError from max(); a `True` key
    passed because `True == 1`."""
    probs = m13.validate_registry(
        schemas={1: m13.SCHEMA_V1, "2": m13.SCHEMA_V2},
        migrations={1: m13.MIGRATION_1_TO_2}, current=2)
    assert any("exact ints" in p for p in probs)
    probs = m13.validate_registry(
        schemas={True: m13.SCHEMA_V1, 2: m13.SCHEMA_V2},
        migrations={1: m13.MIGRATION_1_TO_2}, current=2)
    assert any("exact ints" in p for p in probs)


# --- round 4, finding 2: malformed current migration-runtime records poison -

def test_a_malformed_current_migration_runtime_record_poisons(monkeypatch):
    """Round 4 measured `{"migration_evidence_algorithm": 1}` beside the
    valid record being silently filtered while qualification held."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["migration_runtimes"].append({"migration_evidence_algorithm": 1})
    _patch_artifact(monkeypatch, art)
    assert m13.migration_runtime_supported(art) is False
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) == "unsupported-sqlite"
    assert m13.open_or_migrate(p) == "migration-required"   # ordinary open unaffected


def test_a_duplicate_migration_runtime_identity_poisons(monkeypatch):
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["migration_runtimes"].append(
        copy.deepcopy(art["migration_runtimes"][0]))
    _patch_artifact(monkeypatch, art)
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) == "unsupported-sqlite"


def test_a_missing_algorithm_field_is_malformed_not_superseded():
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    rec = copy.deepcopy(art["migration_runtimes"][0])
    del rec["migration_evidence_algorithm"]
    art["migration_runtimes"] = [art["migration_runtimes"][0], rec]
    with m13._registry():
        assert any("malformed, not" in p
                   for p in m13.migration_runtime_artifact_problems(art))


# --- round 4, finding 3: path cardinality is exact across the artifact -----

def test_a_foreign_identity_path_record_fails_the_artifact(monkeypatch):
    """Round 4 measured a duplicated path with a foreign runtime identity
    passing both validators and the migration proceeding."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    foreign = copy.deepcopy(art["paths"][0])
    foreign["runtime"]["sqlite_version"] = "99"
    foreign["runtime"]["source_id"] = "foreign"
    art["paths"].append(foreign)
    _patch_artifact(monkeypatch, art)
    with m13._registry():
        assert m13.path_evidence_problems(art)
        assert m13.expected_path_problems(art)
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) \
        == "migration-evidence-missing"


def test_a_path_runtime_must_resolve_to_both_qualifications():
    """Every current path record's identity must resolve to exactly one
    active schema-runtime record AND one valid migration-runtime record."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    rec = copy.deepcopy(art["paths"][0])
    rec["runtime"]["features"] = ["not", "a", "mapping"]
    with m13._registry():
        probs = m13.path_record_problems(rec, art)
    assert any("malformed" in p for p in probs)
    art2 = json.loads(m13.EVIDENCE_FILE.read_text())
    art2["migration_runtimes"] = []
    with m13._registry():
        probs = m13.path_record_problems(art2["paths"][0], art2)
    assert any("migration-runtime" in p for p in probs)


# --- round 4, finding 4: confinement probes require SQLITE_AUTH ------------

def test_a_permissive_authorizer_fails_every_denial_probe(monkeypatch):
    """Round 4's falsifier: with an authorizer that permits everything, v5
    still reported denies_release=True because `no such savepoint` counted
    as denial. Every denial probe must now read False."""
    monkeypatch.setattr(m13, "_authorizer",
                        lambda *_a: sqlite3.SQLITE_OK)
    probes = m13.authorizer_probes()
    denials = {k: v for k, v in probes.items() if k.startswith("denies_")}
    assert denials and not any(denials.values()), denials


def test_the_release_probe_holds_a_real_savepoint():
    """The RELEASE probe's setup creates the savepoint before the authorizer
    is installed, so the only way the statement can fail is authorization —
    and on this runner it does, for that reason specifically."""
    assert m13._denied_by_authorizer(
        ("BEGIN IMMEDIATE", "SAVEPOINT s1"), "RELEASE s1") is True
    probes = m13.authorizer_probes()
    assert set(probes) == set(m13.AUTHORIZER_PROBE_KEYS)   # twelve, w/ rollback
    assert probes["denies_rollback"] is True
    assert all(v is True for v in probes.values()), probes


# --- round 4, finding 5: the authority lifecycle ---------------------------

def test_an_unparseable_or_expired_authority_is_refused():
    p = _v1_store()
    bad = m13.make_authority(p)._replace(issued_at="not-a-time")
    assert m13.migrate_store(p, bad) == "migration-quiescence-required"
    expired = m13.make_authority(p, ttl_minutes=0)
    assert m13.migrate_store(p, expired) == "migration-quiescence-required"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 1


def test_an_authority_is_single_use_and_cannot_migrate_a_replacement():
    """Round 4's replay probe: mint, migrate, replace the file at the same
    path with a different v1 store, replay — the replacement migrated under
    an attestation that belonged to the earlier file. Consumption is
    single-use, spent on acceptance."""
    import os
    p = _v1_store(rows=1)
    auth = m13.make_authority(p)
    assert m13.migrate_store(p, auth) == "migrated"
    os.remove(p)
    replacement = _v1_store(rows=3)
    os.rename(replacement, p)
    assert m13.migrate_store(p, auth) == "migration-quiescence-required"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 1


def test_a_retargeted_symlink_unbinds_the_authority():
    """Round 4's symlink probe: authority minted for a symlink to store A,
    symlink retargeted to store B — B migrated, A stayed v1. Paths are
    canonical at mint and at consumption, so retargeting breaks the binding
    and NEITHER store is touched."""
    import os
    a_store, b_store = _v1_store(rows=1), _v1_store(rows=2)
    link = tempfile.mktemp(suffix=".db")
    os.symlink(a_store, link)
    auth = m13.make_authority(link)
    os.remove(link)
    os.symlink(b_store, link)
    assert m13.migrate_store(link, auth) == "migration-quiescence-required"
    for s in (a_store, b_store):
        assert sqlite3.connect(s).execute(
            "PRAGMA user_version").fetchone()[0] == 1


def test_an_authority_binds_the_source_manifestation():
    """A source-mismatched authority refuses. Round 7 moved the first line
    of defence to STATIC resolution: a source digest no current path record
    evidences fails as an artifact property (`migration-evidence-missing`)
    before consumption — even when the store itself is already current, the
    branch round 7 measured bypassing the source check entirely. The
    under-lock hook comparison remains as depth for the evidenced-but-
    different-store case."""
    p = _v1_store()
    unevidenced = m13.make_authority(p)._replace(source_digest="0" * 64)
    ungrammatical = m13.make_authority(p)._replace(source_digest="zz")
    current_era = m13.make_authority(p)._replace(source_digest="0" * 64)
    assert m13.migrate_store(p, unevidenced) == "migration-evidence-missing"
    assert m13.migrate_store(p, ungrammatical) \
        == "migration-quiescence-required"               # grammar layer
    assert m13.migrate_store(p, m13.make_authority(p)) == "migrated"
    # The round-7 probe: a garbage-source authority against a CURRENT store
    # read `current` in v8, bypassing source validation entirely.
    assert m13.migrate_store(p, current_era) == "migration-evidence-missing"


def test_an_authority_binds_the_step_endpoints():
    p = _v1_store()
    auth = m13.make_authority(p)._replace(from_version=2, to_version=3)
    assert m13.migrate_store(p, auth) == "migration-quiescence-required"


# --- round 5, finding 1: monotone evidence writes --------------------------

@pytest.mark.parametrize("field,future", [
    ("migration_evidence_algorithm", 2),
    ("manifest_algorithm", 14),
    ("draft_schema_version", 3),
])
def test_a_future_evidence_revision_is_never_overwritten(field, future,
                                                         monkeypatch,
                                                         tmp_path):
    """Round 5 measured write_evidence() replacing artifacts seeded with
    future revisions of every component — the downgrade class 0007's
    runtime-evidence writer already refuses. The refusal changes no byte."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art[field] = future
    seeded = tmp_path / "evidence.json"
    seeded.write_text(json.dumps(art, indent=1, sort_keys=True))
    before = seeded.read_bytes()
    monkeypatch.setattr(m13, "EVIDENCE_FILE", seeded)
    assert m13.write_evidence() == 1
    assert seeded.read_bytes() == before


def test_an_unreadable_existing_revision_refuses_regeneration(monkeypatch,
                                                              tmp_path):
    """Overwriting what cannot be identified is data loss, not regeneration —
    an explicit delete is the only way past it."""
    seeded = tmp_path / "evidence.json"
    seeded.write_text("{not json")
    before = seeded.read_bytes()
    monkeypatch.setattr(m13, "EVIDENCE_FILE", seeded)
    assert m13.write_evidence() == 1
    assert seeded.read_bytes() == before


# --- round 5, finding 2: consumption covers the complete operation ---------

def test_an_authority_finding_the_store_current_is_still_consumed():
    """THE round-5 replay: A1 migrates; A2's operation finds the store
    current (a no-op) — v6 left A2 unspent, and it later migrated a
    replacement store at the same path. Acceptance consumes, whatever the
    outcome."""
    import os
    p = _v1_store(rows=1)
    a1, a2 = m13.make_authority(p), m13.make_authority(p)
    assert m13.migrate_store(p, a1) == "migrated"
    assert m13.migrate_store(p, a2) == "current"        # no-op — but spent
    os.remove(p)
    replacement = _v1_store(rows=3)
    os.rename(replacement, p)
    assert m13.migrate_store(p, a2) == "migration-quiescence-required"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 1


def test_authorities_losing_the_concurrent_race_are_consumed():
    """The five-opener race: one migrates, four observe `current` — and all
    five authorities are spent; none can be replayed afterwards."""
    p = _v1_store()
    auths = [m13.make_authority(p) for _ in range(5)]
    results = []

    def worker(a):
        results.append(m13.migrate_store(p, a, busy_timeout_ms=10000))

    threads = [threading.Thread(target=worker, args=(a,)) for a in auths]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["current"] * 4 + ["migrated"], results
    for a in auths:
        assert m13.migrate_store(p, a) == "migration-quiescence-required"


def test_operation_consumption_is_atomic_under_concurrency():
    """Two threads racing ONE authority: exactly one acceptance consumes;
    the other reads already-consumed. The consumed set is the draft's
    compare-and-set; §5e freezes the durable equivalent."""
    p = _v1_store()
    auth = m13.make_authority(p)
    results = []

    def worker():
        results.append(m13.migrate_store(p, auth, busy_timeout_ms=10000))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["migrated", "migration-quiescence-required"], \
        results


def test_a_future_issued_authority_is_refused():
    """Round 5 measured issued_at = now + 365d validating. No clock-skew
    allowance in the draft."""
    from datetime import datetime, timedelta, timezone
    p = _v1_store()
    now = datetime.now(timezone.utc)
    fut = m13.make_authority(p)._replace(
        issued_at=(now + timedelta(days=365)).isoformat(),
        expires_at=(now + timedelta(days=365, minutes=15)).isoformat())
    assert m13.migrate_store(p, fut) == "migration-quiescence-required"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 1


def test_an_authority_lifetime_above_the_frozen_maximum_refuses():
    p = _v1_store()
    wide = m13.make_authority(p, ttl_minutes=24 * 60)
    assert m13.migrate_store(p, wide) == "migration-quiescence-required"


def test_an_authority_from_a_different_release_refuses():
    p = _v1_store()
    other = m13.make_authority(p)._replace(release_ref="veracium-0.0.1")
    assert m13.migrate_store(p, other) == "migration-quiescence-required"


def test_an_oversized_token_field_refuses():
    """Audit token fields are not prose channels — round 5's cap."""
    p = _v1_store()
    prose = m13.make_authority(p)._replace(backup_ref="x" * 300)
    assert m13.migrate_store(p, prose) == "migration-quiescence-required"


# --- round 5, finding 3: exact scalar typing -------------------------------

@pytest.mark.parametrize("field,value", [
    ("migration_evidence_algorithm", True),
    ("manifest_algorithm", 13.0),
    ("draft_schema_version", 2.0),
    ("artifact", 12345),
    ("generated_at", 99),
])
def test_coerced_top_level_scalars_poison_the_artifact(field, value,
                                                       monkeypatch):
    """Round 5: `True == 1`, `13.0 == 13`, `2.0 == 2` all passed ordinary
    equality — the class 0007 round 13 closed for its own revision fields.
    A numerically equal wrong-typed value is malformed, and malformed
    schema evidence fails the whole context closed."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art[field] = value
    with m13._registry():
        assert m13.schema_evidence_problems(art)
    _patch_artifact(monkeypatch, art)
    assert m13.open_or_migrate(_v1_store()) == "unsupported-sqlite"


def test_a_coerced_path_algorithm_poisons_the_paths(monkeypatch):
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["paths"][0]["manifest_algorithm"] = 13.0
    with m13._registry():
        assert m13.path_evidence_problems(art)
    _patch_artifact(monkeypatch, art)
    p = _v1_store()
    assert m13.migrate_store(p, m13.make_authority(p)) \
        == "migration-evidence-missing"


# --- round 5, finding 4: the genuinely outermost boundary ------------------

def test_an_embedded_nul_path_is_a_closed_outcome():
    """Round 5 measured ValueError escaping from realpath."""
    assert m13.open_or_migrate("\x00") == "store-unopenable"


def test_a_mistyped_timeout_is_a_closed_outcome():
    """Round 5 measured TypeError escaping from timeout arithmetic. Exact
    int in a frozen range; bool is not an int here either."""
    p = _v1_store()
    assert m13.open_or_migrate(p, busy_timeout_ms="x") == "invalid-request"
    assert m13.open_or_migrate(p, busy_timeout_ms=True) == "invalid-request"
    assert m13.open_or_migrate(p, busy_timeout_ms=0) == "invalid-request"
    assert m13.open_or_migrate(p, busy_timeout_ms=10 ** 9) == "invalid-request"


def test_a_non_pathlike_argument_is_a_closed_outcome():
    assert m13.open_or_migrate(12345) == "invalid-request"


def test_an_oversized_path_is_a_closed_outcome():
    p = "/tmp/" + "x" * 5000
    assert m13.open_or_migrate(p) == "store-unopenable"


# --- round 6, finding 1: a migration never creates -------------------------

def test_a_deleted_source_cannot_become_a_new_store():
    """THE round-6 probe: mint a valid authority, delete the file, migrate —
    v7 CREATED and stamped a fresh v2 store the authority never attested.
    Now: source-specific refusal, and the path stays uncreated."""
    import os
    p = _v1_store(rows=2)
    auth = m13.make_authority(p)
    os.remove(p)
    assert m13.migrate_store(p, auth) == "migration-source-missing"
    assert not os.path.exists(p)


def test_a_truncated_source_cannot_become_a_new_store():
    import os
    p = _v1_store()
    auth = m13.make_authority(p)
    with open(p, "w"):
        pass                                   # truncate to zero bytes
    assert m13.migrate_store(p, auth) == "migration-source-missing"
    assert os.path.getsize(p) == 0


def test_an_empty_database_replacement_cannot_be_migrated():
    import os
    p = _v1_store()
    auth = m13.make_authority(p)
    os.remove(p)
    sqlite3.connect(p).close()                 # empty SQLite database
    before = open(p, "rb").read()
    assert m13.migrate_store(p, auth) == "migration-source-missing"
    assert open(p, "rb").read() == before


def test_an_unstamped_current_shape_replacement_is_refused_not_adopted():
    import os
    p = _v1_store()
    auth = m13.make_authority(p)
    os.remove(p)
    c = sqlite3.connect(p)                     # unstamped v2 shape
    for o in m13.SCHEMA_V2:
        c.execute(o.ddl)
    c.commit()
    c.close()
    before = open(p, "rb").read()
    assert m13.migrate_store(p, auth) == "foreign-shape"
    assert open(p, "rb").read() == before
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 0


def test_ordinary_open_still_creates():
    """The creation seam is migrate-mode only; §4's new row is untouched for
    ordinary opening."""
    p = tempfile.mktemp(suffix=".db")
    assert m13.open_or_migrate(p) == "created"


# --- round 6, finding 2: serialized monotone publication -------------------

def test_a_concurrent_future_publication_is_not_downgraded(tmp_path,
                                                           monkeypatch):
    """Round 6's race: writer B publishes a future revision while writer A
    is past its inspection — v7's pre-generation check let A replace it.
    Inspection now happens under the same interprocess lock as publication:
    a future artifact published while this writer BLOCKS on the lock is
    seen by the re-read and refused, byte-unchanged."""
    import json as _json
    import subprocess
    import sys as _sys
    import time
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    seeded = tmp_path / "evidence.json"
    seeded.write_text(json.dumps(art, indent=1, sort_keys=True))
    monkeypatch.setattr(m13, "EVIDENCE_FILE", seeded)
    lock_path = seeded.with_suffix(".lock")
    signal = tmp_path / "holding"
    helper = f"""
import fcntl, json, pathlib, time
lock = open({str(lock_path)!r}, "w")
fcntl.flock(lock, fcntl.LOCK_EX)
pathlib.Path({str(signal)!r}).write_text("held")
art = json.loads(pathlib.Path({str(seeded)!r}).read_text())
art["migration_evidence_algorithm"] = 2
pathlib.Path({str(seeded)!r}).write_text(json.dumps(art, indent=1, sort_keys=True))
time.sleep(0.6)
fcntl.flock(lock, fcntl.LOCK_UN)
"""
    proc = subprocess.Popen([_sys.executable, "-c", helper])
    try:
        deadline = time.monotonic() + 10
        while not signal.exists():
            assert time.monotonic() < deadline, "helper never acquired lock"
            time.sleep(0.02)
        # This writer blocks on the lock, then re-reads and must refuse.
        assert m13.write_evidence() == 1
        assert _json.loads(seeded.read_text())[
            "migration_evidence_algorithm"] == 2
    finally:
        proc.wait(timeout=10)


# --- round 6, finding 3: Unicode- and PathLike-safe boundary ---------------

def test_a_non_utf8_bytes_path_works_end_to_end():
    """A valid POSIX filename with non-UTF-8 bytes — v6 raised
    UnicodeEncodeError from `canonical.encode()`. The conversions are
    filesystem-encoding-aware now, so the store simply works."""
    import os
    raw = os.fsencode(tempfile.mktemp(suffix="-\udcff.db"))
    p = os.fsdecode(raw)
    c = sqlite3.connect(p)
    for o in m13.SCHEMA_V1:
        c.execute(o.ddl)
    c.execute("PRAGMA user_version = 1")
    c.commit()
    c.close()
    assert m13.open_or_migrate(raw) == "migration-required"
    assert m13.migrate_store(p, m13.make_authority(p)) == "migrated"


def test_a_pathlike_that_raises_is_a_closed_outcome():
    class BadPath:
        def __fspath__(self):
            raise RuntimeError("boom")

        def __repr__(self):
            raise RuntimeError("repr boom")   # diagnostics must survive too
    assert m13.open_or_migrate(BadPath()) == "invalid-request"


def test_a_surrogate_token_field_is_a_closed_refusal():
    """v7's byte-cap check raised UnicodeEncodeError from `.encode()`; the
    frozen token grammar matches on the str and simply refuses."""
    p = _v1_store()
    surr = m13.make_authority(p)._replace(operation_id="op-\udcff")
    assert m13.migrate_store(p, surr) == "migration-quiescence-required"


def test_a_prose_token_field_is_refused():
    """Round 6 (non-blocking): a size cap bounds a prose channel, a grammar
    closes it."""
    p = _v1_store()
    prose = m13.make_authority(p)._replace(
        backup_ref="please restore from the tape in drawer three")
    assert m13.migrate_store(p, prose) == "migration-quiescence-required"


# --- round 6, findings 4-5: audit contract and release identity ------------

def test_the_audit_contract_is_frozen():
    """The typed escape carries the caller's decision inputs, and the
    attempted-record failure has a closed outcome with nothing consumed."""
    assert "migration-audit-unavailable" in m13.MIGRATION_FAILURES
    assert m13.Outcome("migration-audit-unavailable") == \
        "migration-audit-unavailable"
    err = m13.MigrationAuditWriteError(
        committed=True, operation_id="op-x", store_path="/s", resulting_version=2)
    assert err.committed is True and err.resulting_version == 2
    assert isinstance(err, RuntimeError)


def test_the_release_identity_is_content_derived():
    """`veracium-<version>+<source-digest>`: two builds sharing a package
    version but differing in instrument or kernel code get different
    identities."""
    import re
    ident = m13._release_identity()
    assert re.fullmatch(r"veracium-[0-9a-zA-Z.]+\+[0-9a-f]{64}", ident), ident
    assert m13._TOKEN_RE.fullmatch(ident)


def test_a_version_only_release_ref_is_refused():
    """Round 6: a mutable semantic version alone let an authority cross
    builds."""
    p = _v1_store()
    old_style = m13.make_authority(p)._replace(release_ref="veracium-0.4.8")
    assert m13.migrate_store(p, old_style) == "migration-quiescence-required"


def test_a_cross_build_authority_is_refused(monkeypatch):
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13, "_release_identity",
                        lambda: "veracium-0.4.8+aaaaaaaaaaaa")
    assert m13.migrate_store(p, auth) == "migration-quiescence-required"


def test_an_authority_binds_the_evidence_artifact(monkeypatch, tmp_path):
    """Round 6: the authority additionally binds the digest of the exact
    evidence artifact being consumed — regenerating the artifact between
    mint and consume unbinds it."""
    p = _v1_store()
    auth = m13.make_authority(p)
    changed = tmp_path / "evidence.json"
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["generated_at"] = "2026-01-01T00:00:00+00:00"
    changed.write_text(json.dumps(art, indent=1, sort_keys=True))
    monkeypatch.setattr(m13, "EVIDENCE_FILE", changed)
    assert m13.migrate_store(p, auth) == "migration-quiescence-required"


def test_check_evidence_reports_cardinality_before_the_identity_return(
        monkeypatch, tmp_path):
    """Round 6 (non-blocking): a foreign-runtime artifact with its path
    records stripped must not read 'structural checks pass'."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["paths"] = []
    stripped = tmp_path / "evidence.json"
    stripped.write_text(json.dumps(art, indent=1, sort_keys=True))
    monkeypatch.setattr(m13, "EVIDENCE_FILE", stripped)
    assert m13.check_evidence() == 1


# --- round 7, finding 1: one evidence snapshot, bound end to end -----------

def test_the_operation_consumes_the_bytes_the_authority_bound(monkeypatch,
                                                              tmp_path):
    """v8 hashed the file in one read and parsed it in another; a
    publication between them let an A-bound authority consume artifact B.
    One snapshot now feeds digest, comparison, parse and planner — an
    authority bound to a superseded artifact refuses."""
    p = _v1_store()
    auth = m13.make_authority(p)                        # binds artifact A
    art_b = json.loads(m13.EVIDENCE_FILE.read_text())
    art_b["generated_at"] = "2026-01-01T00:00:00+00:00"
    published = tmp_path / "evidence.json"
    published.write_text(json.dumps(art_b, indent=1, sort_keys=True))
    monkeypatch.setattr(m13, "EVIDENCE_FILE", published)  # B is now the file
    assert m13.migrate_store(p, auth) == "migration-quiescence-required"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 1


def test_a_nested_context_never_silently_swaps_artifacts():
    """v8's second variant: an outer context on A, a B-bound authority, and
    the nested migration silently consumed A. A pinned nested context that
    disagrees with the installed digest refuses."""
    backup = m13.EVIDENCE_FILE.read_bytes()
    try:
        with m13._draft():                               # installs A
            art_b = json.loads(backup)
            art_b["generated_at"] = "2026-01-01T00:00:00+00:00"
            m13.EVIDENCE_FILE.write_text(
                json.dumps(art_b, indent=1, sort_keys=True))
            p = _v1_store()
            auth = m13.make_authority(p)                 # binds B
            assert m13.migrate_store(p, auth) == "migration-evidence-missing"
            assert sqlite3.connect(p).execute(
                "PRAGMA user_version").fetchone()[0] == 1
    finally:
        m13.EVIDENCE_FILE.write_bytes(backup)


# --- round 7, finding 2: framed, full-length release identity --------------

def test_moving_bytes_across_the_file_boundary_changes_the_identity(tmp_path):
    """v8 concatenated raw bytes, so relocating a docstring across the file
    boundary kept the identity while both files changed. Length-framed names
    and contents make the boundary part of the digest."""
    a1, b1 = tmp_path / "a.py", tmp_path / "b.py"
    a1.write_bytes(b"AAAA" + b"DOCSTRING" * 10)
    b1.write_bytes(b"BBBB")
    one = m13._source_identity(files=(a1, b1))
    a2, b2 = tmp_path / "a2.py", tmp_path / "b2.py"
    a2.write_bytes(b"AAAA")
    b2.write_bytes(b"DOCSTRING" * 10 + b"BBBB")
    assert a1.read_bytes() + b1.read_bytes() == a2.read_bytes() + b2.read_bytes()
    two = m13._source_identity(files=(a2, b2))
    assert one != two
    # ...and the name is framed too (a2/b2 vs a/b already differ; check the
    # same names with swapped content to isolate the content framing):
    assert len(m13._source_identity()) == 64             # full digest


# --- round 7, finding 3: the executable audit state machine ----------------

def test_audit_unavailability_consumes_nothing_and_is_retryable(monkeypatch):
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.activate
    calls = {"n": 0}

    def flaky(a):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("audit storage offline")
        return real(a)
    monkeypatch.setattr(m13._AUDIT, "activate", flaky)
    assert m13.migrate_store(p, auth) == "migration-audit-unavailable"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 1
    # NOT consumed: the same authority retries successfully.
    assert m13.migrate_store(p, auth) == "migrated"


def test_a_duplicate_operation_is_consumed_not_an_audit_outage():
    """The distinction v8 conflated: a uniqueness conflict means CONSUMED."""
    p = _v1_store()
    auth = m13.make_authority(p)
    assert m13.migrate_store(p, auth) == "migrated"
    assert m13.migrate_store(p, auth) == "migration-quiescence-required"


def test_terminal_records_are_written_for_migrated_and_noop_current():
    """§5e: a spent authority with no terminal record is indistinguishable
    from a crash — the no-op current writes one too."""
    p = _v1_store()
    a1, a2 = m13.make_authority(p), m13.make_authority(p)
    assert m13.migrate_store(p, a1) == "migrated"
    assert m13.migrate_store(p, a2) == "current"
    ev = m13._AUDIT._events
    assert ev[(a1.operation_id, "migration_completed")]["outcome"] == "migrated"
    assert ev[(a2.operation_id, "migration_completed")]["outcome"] == "current"
    assert (a1.operation_id, "migration_attempted") in ev
    with pytest.raises(ValueError, match="UNIQUE"):
        m13._AUDIT.record(a1.operation_id, "migration_completed", {})


def test_a_failed_terminal_write_raises_the_typed_error(monkeypatch):
    p = _v1_store()
    auth = m13.make_authority(p)

    def broken(operation_id, event, payload):
        raise OSError("audit storage died mid-operation")
    monkeypatch.setattr(m13._AUDIT, "record", broken)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.committed is True                  # the migration ran
    assert exc.value.operation_id == auth.operation_id
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 2


# --- round 7, finding 4: minting never creates -----------------------------

def test_minting_never_creates_a_store():
    import os
    missing = tempfile.mktemp(suffix=".db")
    with pytest.raises(ValueError, match="no source store"):
        m13.make_authority(missing)
    assert not os.path.exists(missing)


def test_minting_refuses_a_non_accepted_source():
    p = _v1_store(extra="CREATE TABLE intruder (x)")
    with pytest.raises(ValueError, match="not an accepted"):
        m13.make_authority(p)


# --- round 7, finding 5: internal failures tell the truth ------------------

def test_an_internal_defect_is_not_a_store_outcome(monkeypatch):
    """v8 mapped an internal RuntimeError to invalid-store — inviting a host
    to restore a healthy database — and to migration-failed, implying a
    known rollback state."""
    def boom():
        raise RuntimeError("internal validator bug")
    monkeypatch.setattr(sv, "runtime_supported", boom)
    p = _v1_store()
    out = m13.open_or_migrate(p)
    assert out == "internal-error"
    assert "phase=" in out.diagnostic and "commit-state=" in out.diagnostic
    out = m13.migrate_store(p, m13.make_authority(p))
    assert out == "internal-error"


# --- round 7, non-blocking corrections -------------------------------------

def test_check_evidence_is_total_over_non_mapping_runtime_members(monkeypatch,
                                                                  tmp_path):
    """`[42]` in the runtimes list raised AttributeError out of
    check_evidence; the delegated accessor is now total."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["runtimes"] = [42]
    seeded = tmp_path / "evidence.json"
    seeded.write_text(json.dumps(art, indent=1, sort_keys=True))
    monkeypatch.setattr(m13, "EVIDENCE_FILE", seeded)
    assert m13.check_evidence() == 1
    assert sv.active_records([42]) == []
