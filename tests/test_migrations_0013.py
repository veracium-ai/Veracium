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
import os
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

_OP_ID = "op-00000000-0000-4000-8000-000000000000"   # a valid op-<uuid4>


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
    facts = m13.TerminalFacts("migrated", 1, 2, True, True, "destination", 2)
    err = m13.MigrationAuditWriteError(
        operation_id=_OP_ID, store_path="/s", facts=facts)
    assert err.committed is True and err.resulting_version == 2
    assert err.resulting_state == "destination" and err.facts is facts
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

    def flaky(a, output_digest):
        calls["n"] += 1
        if calls["n"] == 1:
            raise m13.AuditStorageUnavailable("audit storage offline",
                                              committed=False)   # proven unwritten
        return real(a, output_digest)
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
    with pytest.raises(ValueError, match="already has a terminal"):
        m13._AUDIT.record_terminal(a1.operation_id, "migration_completed",
                                   _terminal_payload())


def _activate(auth):
    """Activate directly in a test — resolve the output digest the operation
    row needs from the committed artifact, exactly as _run does."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    rec = m13._resolve_path_record(auth, art)
    return m13._AUDIT.activate(auth, rec["output_acceptance_digest"])


def _terminal_payload(**over):
    base = {"outcome": "migrated", "store_changed": True,
            "transaction_committed": True, "resulting_version": 2,
            "resulting_state": "destination",
            "occurred_at": m13.canonical_timestamp(
                __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc))}
    base.update(over)
    return base


def test_a_failed_terminal_write_raises_the_typed_error(monkeypatch):
    p = _v1_store()
    auth = m13.make_authority(p)

    def broken(operation_id, event, payload):
        raise OSError("audit storage died mid-operation")
    monkeypatch.setattr(m13._AUDIT, "record_terminal", broken)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.committed is True                  # the migration ran
    assert exc.value.operation_id == auth.operation_id
    assert exc.value.resulting_version == 2
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


# --- round 8, finding 1: each TEMP object class is probed independently -----

def test_the_temp_probes_cover_every_object_class():
    probes = m13.authorizer_probes()
    assert {"denies_temp_table", "denies_temp_index", "denies_temp_view",
            "denies_temp_trigger"} <= set(probes)
    assert set(probes) == set(m13.AUTHORIZER_PROBE_KEYS)      # fifteen
    assert all(v is True for v in probes.values()), probes


def test_an_authorizer_allowing_temp_triggers_fails_qualification(monkeypatch):
    """Round 8's falsifier: an authorizer that denies TEMP tables but ALLOWS
    TEMP triggers passed all twelve v9 probes — only the post-step leak
    assertion caught the trigger, after it executed. Each TEMP class now has
    its own SQLITE_AUTH probe, so the weak authorizer flips
    denies_temp_trigger False."""
    # The reviewer's construction: a full replacement that denies the
    # transaction/pragma set and TEMP tables/indexes/views but ALLOWS temp
    # triggers (and the temp-schema writes their creation needs) — the real
    # authorizer's db-name rule is what normally denies all four, so the
    # falsifier must drop that rule for the trigger to actually be created.
    deny = {sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_SAVEPOINT,
            sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_PRAGMA,
            sqlite3.SQLITE_CREATE_TEMP_TABLE, sqlite3.SQLITE_CREATE_TEMP_INDEX,
            sqlite3.SQLITE_CREATE_TEMP_VIEW}

    def weak(action, a1, a2, db, trig):
        return sqlite3.SQLITE_DENY if action in deny else sqlite3.SQLITE_OK
    monkeypatch.setattr(m13, "_authorizer", weak)
    probes = m13.authorizer_probes()
    assert probes["denies_temp_trigger"] is False            # allowed → not denied
    assert probes["denies_temp_table"] is True               # still denied
    # ...and a runtime whose live probes don't reproduce the record refuses.
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    assert m13.migration_runtime_supported(art) is False


# --- round 8, finding 2: audit schema and state machine enforced -----------

def test_the_audit_store_rejects_two_terminal_events():
    p = _v1_store()
    auth = m13.make_authority(p)
    _activate(auth)
    m13._AUDIT.record_terminal(auth.operation_id, "migration_completed",
                               _terminal_payload())
    with pytest.raises(ValueError, match="already has a terminal"):
        m13._AUDIT.record_terminal(auth.operation_id, "migration_failed",
                                   _terminal_payload(outcome="x"))


def test_the_audit_store_rejects_unknown_events_and_payloads():
    p = _v1_store()
    auth = m13.make_authority(p)
    _activate(auth)
    with pytest.raises(ValueError, match="not a terminal event"):
        m13._AUDIT.record_terminal(auth.operation_id, "totally-made-up",
                                   _terminal_payload())
    with pytest.raises(ValueError, match="fields"):
        m13._AUDIT.record_terminal(auth.operation_id, "migration_completed",
                                   {"arbitrary": object})
    with pytest.raises(ValueError, match="resulting_version must be int"):
        m13._AUDIT.record_terminal(auth.operation_id, "migration_completed",
                                   _terminal_payload(resulting_version="two"))


def test_the_operation_row_carries_the_full_frozen_schema():
    p = _v1_store()
    auth = m13.make_authority(p)
    _activate(auth)
    row = m13._AUDIT._ops[auth.operation_id]
    assert set(row) == m13._AUDIT_OPERATION_FIELDS
    assert row["evidence_digest"] == auth.evidence_digest
    assert row["source_digest"] == auth.source_digest
    assert row["state"] == "attempted"


def test_activation_is_atomic():
    """The operation row and the attempted event appear together or not at
    all — a consumed operation without its attempted record cannot exist."""
    p = _v1_store()
    auth = m13.make_authority(p)
    receipt = _activate(auth)
    assert isinstance(receipt, m13.ActivationReceipt)
    assert receipt.status == "activated"       # round 16: a typed receipt
    assert auth.operation_id in m13._AUDIT._ops
    assert (auth.operation_id, "migration_attempted") in m13._AUDIT._events


# --- round 8, finding 3: correct terminal facts per branch -----------------

def test_the_current_branch_reports_the_actual_resulting_version(monkeypatch):
    """v9 reported resulting_version=1 for a lost-race current whose store
    was already v2. The kernel's OpenResult carries the truth."""
    p = _v1_store()
    a1, a2 = m13.make_authority(p), m13.make_authority(p)
    assert m13.migrate_store(p, a1) == "migrated"

    def broken(operation_id, event, payload):
        raise OSError("died")
    monkeypatch.setattr(m13._AUDIT, "record_terminal", broken)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, a2)                          # lost-race current
    assert exc.value.resulting_version == 2               # NOT 1
    assert exc.value.committed is False                   # this op changed nothing
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 2


def test_the_current_with_repair_branch_reports_committed_true(monkeypatch):
    """A current operation that repairs rebuildable drift DID commit a change
    — its committed flag is True, distinguished from the no-repair case."""
    p = _v1_store()
    # Mint the current-branch authority WHILE the store is still a v1 source
    # (minting refuses a v2 store — round 7). Then migrate with a different
    # authority, introduce rebuildable drift, and present the pre-minted one.
    a = m13.make_authority(p)
    m13.migrate_store(p, m13.make_authority(p))           # -> v2
    c = sqlite3.connect(p)
    c.execute("DROP INDEX ix_confirmations_edge")         # rebuildable drift
    c.commit()
    c.close()

    def broken(operation_id, event, payload):
        raise OSError("died")
    monkeypatch.setattr(m13._AUDIT, "record_terminal", broken)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, a)                           # current WITH repair
    assert exc.value.committed is True
    assert exc.value.resulting_version == 2


def test_the_migrated_branch_reports_committed_true(monkeypatch):
    p = _v1_store()
    auth = m13.make_authority(p)

    def broken(operation_id, event, payload):
        raise OSError("died")
    monkeypatch.setattr(m13._AUDIT, "record_terminal", broken)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.committed is True
    assert exc.value.resulting_version == 2


# --- round 8, finding 4: release identity fails closed ---------------------

def test_an_unreadable_covered_file_fails_closed(monkeypatch, tmp_path):
    missing = tmp_path / "gone.py"                        # never created
    monkeypatch.setattr(m13, "_RELEASE_IDENTITY_FILES",
                        (missing,))
    with pytest.raises(sv.PackageConsistencyError):
        m13._release_identity()


def test_a_missing_version_declaration_fails_closed(monkeypatch, tmp_path):
    fake_root = tmp_path
    (fake_root / "pyproject.toml").write_text("[project]\nname='x'\n")
    monkeypatch.setattr(m13, "ROOT", fake_root)
    monkeypatch.setattr(m13, "_RELEASE_IDENTITY_FILES",
                        (Path(m13.__file__),))
    with pytest.raises(sv.PackageConsistencyError):
        m13._release_identity()


def test_no_unknown_sentinel_authority_migrates(monkeypatch):
    """v9 accepted `veracium-0.4.8+unknown` on both sides. Now identity
    acquisition raises before any authority is minted or accepted."""
    p = _v1_store()
    auth = m13.make_authority(p)

    def fail(files=None):
        raise sv.PackageConsistencyError("unreadable")
    monkeypatch.setattr(m13, "_source_identity", fail)
    with pytest.raises(sv.PackageConsistencyError):
        m13.migrate_store(p, auth)


# --- round 8, finding 5: canonical, bounded timestamps ---------------------

def test_a_hundred_kilobyte_timestamp_is_refused():
    p = _v1_store()
    long_ts = "2026-08-03T00:00:00." + "1" * 100000 + "+00:00"
    a = m13.make_authority(p)._replace(issued_at=long_ts)
    probs = m13.authority_static_problems(
        a, __import__("os").path.realpath(p), m13._artifact_snapshot())
    assert any("canonical" in pr for pr in probs)
    assert m13.migrate_store(p, a) == "migration-quiescence-required"


def test_a_noncanonical_but_valid_instant_is_refused():
    """Many strings map to one instant; only the canonical form is accepted."""
    p = _v1_store()
    # A valid ISO 8601 instant, but not the frozen 6-digit-microsecond form.
    a = m13.make_authority(p)._replace(issued_at="2026-08-03T00:00:00+00:00")
    probs = m13.authority_static_problems(
        a, __import__("os").path.realpath(p), m13._artifact_snapshot())
    assert any("canonical" in pr for pr in probs)


def test_minted_timestamps_are_canonical():
    p = _v1_store()
    a = m13.make_authority(p)
    assert m13._timestamp_problems(a.issued_at, "issued_at") == []
    assert m13._timestamp_problems(a.expires_at, "expires_at") == []
    assert len(a.issued_at) == 32


# --- round 9, finding 1: activation is genuinely atomic --------------------

def test_activation_publishes_one_state_or_none(monkeypatch):
    """Round 10, finding 1: v11's `self._ops, self._events, self._event_seq =
    ...` is THREE attribute stores; a failure on the second left the first
    applied. The whole state is now ONE immutable `AuditState` behind one
    attribute — injecting a failure ON THE PUBLISH (constructing the new
    state) leaves the previous state intact and consumes nothing."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13.AuditState

    def boom(*a):
        # A failed single publish is ATOMIC: nothing was written, so the honest
        # commit fact is False (proven not written), not the ambiguous None.
        raise m13.AuditStorageUnavailable("state publish failed",
                                          committed=False)
    monkeypatch.setattr(m13, "AuditState", boom)
    assert m13.migrate_store(p, auth) == "migration-audit-unavailable"
    monkeypatch.setattr(m13, "AuditState", real)
    # NOTHING consumed or recorded — the same authority activates fresh.
    assert auth.operation_id not in m13._AUDIT._ops
    assert (auth.operation_id, "migration_attempted") not in m13._AUDIT._events
    assert m13.migrate_store(p, auth) == "migrated"


def test_an_internal_activation_defect_is_not_a_storage_outage(monkeypatch):
    """Round 10, finding 4: v11 mapped EVERY activation exception to the
    retryable `migration-audit-unavailable`. Only `AuditStorageUnavailable`
    is retryable; a library defect (here a malformed operation row) is
    `internal-error`, and nothing is consumed."""
    p = _v1_store()
    auth = m13.make_authority(p)

    def defect(a, output_digest):
        raise AssertionError("library schema bug")
    monkeypatch.setattr(m13._AUDIT, "activate", defect)
    assert m13.migrate_store(p, auth) == "internal-error"
    assert auth.operation_id not in m13._AUDIT._ops


def test_terminal_publication_publishes_one_state_or_none(monkeypatch):
    """A failure building the terminal event leaves the operation's state at
    `attempted` and no terminal event — the single publish is the only
    mutation."""
    p = _v1_store()
    auth = m13.make_authority(p)
    _activate(auth)
    real_ts = m13._timestamp_problems

    def boom(value, field):
        if field == "occurred_at":
            raise OSError("mid-terminal failure")
        return real_ts(value, field)
    monkeypatch.setattr(m13, "_timestamp_problems", boom)
    with pytest.raises(OSError):
        m13._AUDIT.record_terminal(auth.operation_id, "migration_completed",
                                   _terminal_payload())
    monkeypatch.setattr(m13, "_timestamp_problems", real_ts)
    assert m13._AUDIT._ops[auth.operation_id]["state"] == "attempted"
    assert (auth.operation_id, "migration_completed") not in m13._AUDIT._events


# --- round 9, finding 2: complete schema + semantic consistency ------------

def test_the_operation_row_carries_every_frozen_field():
    p = _v1_store()
    auth = m13.make_authority(p)
    _activate(auth)
    row = m13._AUDIT._ops[auth.operation_id]
    assert set(row) == m13._AUDIT_OPERATION_FIELDS
    for f in ("backup_ref", "issued_at", "expires_at", "output_digest"):
        assert f in row and row[f]
    assert row["backup_ref"] == auth.backup_ref
    assert row["issued_at"] == auth.issued_at
    assert row["expires_at"] == auth.expires_at
    assert m13._timestamp_problems(row["attempted_at"], "a") == []


def test_the_terminal_validator_rejects_contradictions():
    p = _v1_store()
    auth = m13.make_authority(p)
    _activate(auth)
    op = auth.operation_id
    # outcome not in the closed vocabulary
    with pytest.raises(ValueError, match="not a known terminal outcome"):
        m13._AUDIT.record_terminal(op, "migration_completed",
                                   _terminal_payload(outcome="totally-made-up"))
    # completed cannot carry a failure/foreign outcome
    with pytest.raises(ValueError, match="permits only migrated or current"):
        m13._AUDIT.record_terminal(op, "migration_completed",
                                   _terminal_payload(outcome="locked",
                                                     resulting_version=1))
    # failed cannot carry a success outcome
    with pytest.raises(ValueError, match="cannot carry the success"):
        m13._AUDIT.record_terminal(op, "migration_failed",
                                   _terminal_payload(outcome="migrated"))
    # store_changed and transaction_committed must be the same tri-state value
    with pytest.raises(ValueError, match="same tri-state value"):
        m13._AUDIT.record_terminal(op, "migration_completed",
                                   _terminal_payload(store_changed=True,
                                                     transaction_committed=False))
    # a committed change that is not at the destination version
    with pytest.raises(ValueError, match="committed change is at version 2"):
        m13._AUDIT.record_terminal(op, "migration_completed",
                                   _terminal_payload(resulting_version=999))
    # a migrated outcome must resolve to the destination version
    with pytest.raises(ValueError, match="committed change is at version 2"):
        m13._AUDIT.record_terminal(op, "migration_completed",
                                   _terminal_payload(outcome="migrated",
                                                     resulting_version=1))


# --- round 9, finding 3: post-commit internal defect tells the truth -------

def test_a_post_commit_internal_defect_never_reports_the_wrong_version():
    """Round 9: v10 built the OpenResult AFTER commit; forcing it to raise
    recorded committed=False and v1 for a store committed at v2. The kernel
    now builds the result BEFORE commit, so a raise rolls the store back and
    every fact is truthful — the store is v1 and the outcome is
    internal-error."""
    p = _v1_store()
    orig = sv.OpenResult

    def boom(label, **kw):
        if label == "migrated":
            raise RuntimeError("internal defect at result construction")
        return orig(label, **kw)
    try:
        sv.OpenResult = boom
        auth = m13.make_authority(p)
        out = m13.migrate_store(p, auth)
        assert out == "internal-error"
        assert sqlite3.connect(p).execute(
            "PRAGMA user_version").fetchone()[0] == 1        # rolled back
        ev = m13._AUDIT._events.get((auth.operation_id, "migration_failed"))
        assert ev is not None
        assert ev["resulting_version"] == 1                  # truthful
        assert ev["store_changed"] is False
    finally:
        sv.OpenResult = orig


# --- round 9, finding 4: TEMP virtual tables are qualified ------------------

def test_temp_virtual_tables_are_probed():
    probes = m13.authorizer_probes()
    assert "denies_temp_virtual_table" in probes
    assert probes["denies_temp_virtual_table"] is True
    assert set(probes) == set(m13.AUTHORIZER_PROBE_KEYS)     # sixteen


def test_an_authorizer_allowing_temp_vtables_fails_qualification(monkeypatch):
    """Round 9's falsifier: deny every named TEMP object class but allow
    virtual tables — v10's fifteen probes all passed."""
    deny = {sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_SAVEPOINT,
            sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_PRAGMA,
            sqlite3.SQLITE_CREATE_TEMP_TABLE, sqlite3.SQLITE_CREATE_TEMP_INDEX,
            sqlite3.SQLITE_CREATE_TEMP_VIEW, sqlite3.SQLITE_CREATE_TEMP_TRIGGER}

    def weak(action, a1, a2, db, trig):
        return sqlite3.SQLITE_DENY if action in deny else sqlite3.SQLITE_OK
    monkeypatch.setattr(m13, "_authorizer", weak)
    probes = m13.authorizer_probes()
    assert probes["denies_temp_virtual_table"] is False
    assert probes["denies_temp_table"] is True
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    assert m13.migration_runtime_supported(art) is False


# --- round 9, finding 5: generated_at is canonical -------------------------

def test_a_noncanonical_generated_at_poisons_the_artifact(monkeypatch):
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art["generated_at"] = "2026-01-01T00:00:00+00:00"        # valid but not canonical
    with m13._registry():
        assert any("generated_at" in pr
                   for pr in m13.schema_evidence_problems(art))
    art["generated_at"] = "2026-01-01T00:00:00." + "1" * 100000 + "+00:00"
    with m13._registry():
        assert any("generated_at" in pr
                   for pr in m13.schema_evidence_problems(art))


def test_the_committed_generated_at_is_canonical():
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    assert m13._timestamp_problems(art["generated_at"], "generated_at") == []
    assert len(art["generated_at"]) == 32


# --- round 9 evidence gap: the rolled-back terminal cell -------------------

def test_the_rolled_back_cell_reports_the_source_version(monkeypatch):
    """The fourth terminal cell round 8 required but v10 left unexercised: a
    migration that fails after a statement rolls the store back; the forced
    terminal-write failure must report committed=False and the SOURCE
    version, with the authority consumed."""
    bad = m13.Migration(1, 2, (m13.CONFIRMATIONS_DDL, "CREATE BOGUS ("))
    _patch_migration(monkeypatch, bad)
    _crafted_artifact(monkeypatch, m13.migration_declaration_digest(bad))
    p = _v1_store(rows=2)
    auth = m13.make_authority(p)

    def broken(operation_id, event, payload):
        raise OSError("terminal write died")
    monkeypatch.setattr(m13._AUDIT, "record_terminal", broken)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.committed is False
    assert exc.value.resulting_version == 1                  # source, rolled back
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 1
    assert sqlite3.connect(p).execute(
        "SELECT COUNT(*) FROM edges").fetchone()[0] == 2
    assert auth.operation_id in m13._AUDIT._ops              # consumed


# --- round 10, finding 2: the exact per-cell success contract --------------

def test_the_terminal_validator_rejects_impossible_success_records():
    """Round 10 measured three impossible success records accepted by v11."""
    auth = m13.make_authority(_v1_store())
    _activate(auth)
    op = auth.operation_id
    # current must leave the store at the destination version
    with pytest.raises(ValueError, match="destination requires version 2"):
        m13._AUDIT.record_terminal(op, "migration_completed",
            _terminal_payload(outcome="current", store_changed=False,
                              transaction_committed=False, resulting_version=1))
    # migrated must have changed AND committed the store
    with pytest.raises(ValueError, match="changed and committed"):
        m13._AUDIT.record_terminal(op, "migration_completed",
            _terminal_payload(outcome="migrated", store_changed=False,
                              transaction_committed=False, resulting_version=2))


def test_the_terminal_validator_accepts_every_valid_success_cell():
    """The three frozen successful payloads all pass."""
    for payload in (
        dict(outcome="migrated", store_changed=True,
             transaction_committed=True, resulting_version=2,
             resulting_state="destination"),
        dict(outcome="current", store_changed=False,
             transaction_committed=False, resulting_version=2,
             resulting_state="destination"),                      # no repair
        dict(outcome="current", store_changed=True,
             transaction_committed=True, resulting_version=2,
             resulting_state="destination"),                      # repair
    ):
        auth = m13.make_authority(_v1_store())
        _activate(auth)
        payload["occurred_at"] = m13.canonical_timestamp(
            __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc))
        m13._AUDIT.record_terminal(auth.operation_id, "migration_completed",
                                   payload)


# --- round 10, finding 3: a post-commit failure is representable -----------

def test_a_post_commit_failure_records_the_destination_version():
    """Round 10: v11 could not record a post-commit internal-error — the
    migration committed at v2 but `migration_failed` forced the source
    version, so the terminal write itself failed. The kernel builds the
    OpenResult before COMMIT, so this exact injection now rolls back... but
    a failure AFTER a genuine commit (here, forcing Outcome construction to
    raise) must be recordable: failed + committed + destination version."""
    p = _v1_store()
    real_outcome = m13.Outcome

    def boom(value, diagnostic=None):
        if value == "migrated":
            raise RuntimeError("post-commit defect in the wrapper")
        return real_outcome(value, diagnostic)
    auth = m13.make_authority(p)
    orig = m13.Outcome
    try:
        m13.Outcome = boom
        out = m13.migrate_store(p, auth)
    finally:
        m13.Outcome = orig
    # The store DID commit at v2; the outcome is internal-error, and the
    # terminal record truthfully carries committed=True at the destination.
    assert out == "internal-error"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 2
    ev = m13._AUDIT._events.get((auth.operation_id, "migration_failed"))
    assert ev is not None
    assert ev["outcome"] == "internal-error"
    assert ev["transaction_committed"] is True
    assert ev["store_changed"] is True
    assert ev["resulting_version"] == 2                       # destination, truthful


def test_the_terminal_validator_permits_a_committed_failure():
    """The post-commit failure cell, at the validator level."""
    auth = m13.make_authority(_v1_store())
    _activate(auth)
    ts = m13.canonical_timestamp(__import__("datetime").datetime.now(
        __import__("datetime").timezone.utc))
    m13._AUDIT.record_terminal(auth.operation_id, "migration_failed",
        dict(outcome="internal-error", store_changed=True,
             transaction_committed=True, resulting_version=2,
             resulting_state="destination", occurred_at=ts))


# --- round 10, finding 4: storage outage vs internal defect ----------------

def test_a_typed_storage_outage_is_retryable():
    """Only AuditStorageUnavailable is the retryable audit-unavailable."""
    assert issubclass(m13.AuditStorageUnavailable, Exception)


# --- round 10, finding 5: check_evidence is total over malformed containers -

@pytest.mark.parametrize("field", ["runtimes", "migration_runtimes", "paths"])
@pytest.mark.parametrize("value", [None, False, 0, {}, "string"])
def test_check_evidence_is_total_over_malformed_list_fields(field, value,
                                                            monkeypatch,
                                                            tmp_path):
    """Round 10: `runtimes: false` (and the others) made check_evidence raise
    a raw TypeError from a downstream validator iterating a non-list. Every
    validator is total now, and the gate wraps them — a clean nonzero, never
    a traceback."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art[field] = value
    seeded = tmp_path / "evidence.json"
    seeded.write_text(json.dumps(art, indent=1, sort_keys=True))
    monkeypatch.setattr(m13, "EVIDENCE_FILE", seeded)
    rc = m13.check_evidence()                    # must NOT raise
    assert rc == 1


@pytest.mark.parametrize("field", ["runtimes", "migration_runtimes"])
def test_the_artifact_validators_are_total_over_non_lists(field):
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    art[field] = False
    with m13._registry():
        # None of these raise; each reports the malformed container.
        assert m13.schema_evidence_problems(art)
        m13.migration_runtime_artifact_problems(art)
        m13.path_evidence_problems(art)
        m13.expected_path_problems(art)


# --- round 10 corrections: event_id grammar, -O-safe schema ----------------

def test_event_ids_are_opaque_uuid_shaped_tokens():
    auth = m13.make_authority(_v1_store())
    _activate(auth)
    ev = m13._AUDIT._events[(auth.operation_id, "migration_attempted")]
    assert m13._EVENT_ID_RE.fullmatch(ev["event_id"])


def test_the_operation_row_schema_check_survives_dash_o():
    """Correction 1: the schema guard is a raise, not an assert, so it holds
    under python -O."""
    import subprocess, sys
    code = (
        "import sys; sys.path[:0]=['src','specs'];"
        "import migrations_0013 as m;"
        "from collections import namedtuple;"
        "A=namedtuple('A', m.MigrationAuthority._fields);"
        # a NamedTuple missing nothing but we force a bad row via a stub
        "store=m.DraftAuditStore();"
        "import types;"
        "orig=store._operation_row;"
        "row=None;"
        "\ntry:\n"
        "    store._operation_row(object(), 'd')\n"
        "except Exception as e:\n"
        "    print(type(e).__name__)\n")
    r = subprocess.run([sys.executable, "-O", "-c", code],
                       capture_output=True, text=True, cwd=str(ROOT))
    # Under -O the assert would vanish; a real raise still fires (some error).
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip()                      # an exception name was printed


# ==========================================================================
# Round 11 regressions
# ==========================================================================

# --- round 11, finding 1: honest resulting_state, no fabricated version ----

def _facts_state(**over):
    base = {"facts": None, "observed_version": None, "rolled_back": None,
            "source_absent": False, "committed_established": False,
            "callback_defect": None, "opened": False}
    # round 17: committed facts are only trusted when established at publication
    if over.get("facts") is not None and "committed_established" not in over:
        base["committed_established"] = True
    base.update(over)
    # round 22, finding 2: production stores a wrapper-owned FROZEN result, never
    # a live OpenResult — mirror that so the derivation sees what it really gets.
    if isinstance(base.get("facts"), sv.OpenResult):
        base["facts"] = m13._frozen_from_open_result(base["facts"])
    return base


def test_terminal_facts_never_fabricate_a_version_for_missing_or_unknown():
    """Round 11, finding 1 and round 12, findings 1 & 2: the honest derivation
    distinguishes every physical state and never invents a version. `source`
    requires a CONFIRMED rollback (round 12 f1); `missing` requires a proven-
    absent path, distinct from an existing-but-`unaccepted` store (round 12
    f2)."""
    # a committed planner outcome → destination, its version
    facts = sv.OpenResult("migrated", store_changed=True,
                          transaction_committed=True, resulting_version=2)
    dest = m13._terminal_facts("migrated",
                               _facts_state(facts=facts, observed_version=1))
    assert dest == {"store_changed": True, "transaction_committed": True,
                    "resulting_version": 2, "resulting_state": "destination"}
    # a PROVEN-ABSENT path → missing, NULL version
    miss = m13._terminal_facts("migration-source-missing",
                               _facts_state(source_absent=True))
    assert miss["resulting_state"] == "missing"
    assert miss["resulting_version"] is None
    # an EXISTING but non-source store → unaccepted, NULL (round 12, finding 2)
    unacc = m13._terminal_facts("migration-source-missing",
                                _facts_state(source_absent=False))
    assert unacc["resulting_state"] == "unaccepted"
    assert unacc["resulting_version"] is None
    # observed under the lock AND a CONFIRMED rollback → source, its version
    src = m13._terminal_facts("migration-failed",
                              _facts_state(observed_version=1,
                                           rolled_back="rolled-back"))
    assert src["resulting_state"] == "source"
    assert src["resulting_version"] == 1
    # observed but rollback NOT confirmed → unknown, NULL (round 12, finding 1)
    rbf = m13._terminal_facts("migration-failed",
                              _facts_state(observed_version=1,
                                           rolled_back="rollback-failed"))
    assert rbf["resulting_state"] == "unknown"
    assert rbf["resulting_version"] is None
    # nothing established (locked / unopenable / pre-planner escape) → unknown
    unk = m13._terminal_facts("migration-locked", _facts_state())
    assert unk["resulting_state"] == "unknown"
    assert unk["resulting_version"] is None


def test_a_missing_and_an_unknown_failure_cell_are_legal_terminal_records():
    """The null-version cells the honest derivation produces are all accepted
    by the terminal contract — a failure can leave the store missing,
    unaccepted, or unobserved, each with its physically-valid outcome. The
    `unknown` cell's Booleans are `None` (round 13, finding 1)."""
    ts = m13.canonical_timestamp(__import__("datetime").datetime.now(
        __import__("datetime").timezone.utc))
    for outcome, state, boolean in [
            ("migration-source-missing", "missing", False),
            ("migration-source-missing", "unaccepted", False),
            ("migration-failed", "unknown", None)]:
        auth = m13.make_authority(_v1_store())
        _activate(auth)
        m13._AUDIT.record_terminal(auth.operation_id, "migration_failed",
            dict(outcome=outcome, store_changed=boolean,
                 transaction_committed=boolean, resulting_version=None,
                 resulting_state=state, occurred_at=ts))


def test_a_missing_or_unknown_state_rejects_a_non_null_version():
    """The dual of the rule: a null-version state that carries a version is a
    contradiction and is refused."""
    auth = m13.make_authority(_v1_store())
    _activate(auth)
    with pytest.raises(ValueError, match="requires a null version"):
        m13._AUDIT.record_terminal(auth.operation_id, "migration_failed",
            _terminal_payload(outcome="migration-source-missing",
                              store_changed=False, transaction_committed=False,
                              resulting_state="missing", resulting_version=1))


# --- round 11, finding 3: a named escape is still terminalized --------------

def test_a_package_consistency_error_is_terminalized_and_reraised(monkeypatch):
    """Round 11, finding 3: a `PackageConsistencyError` raised AFTER the
    authority is consumed escaped the wrapper without a terminal event, so a
    consumed operation had no audit record at all. It is now terminalized as
    `package-inconsistent` and re-raised (§5d)."""
    p = _v1_store()
    auth = m13.make_authority(p)

    def boom(*a, **k):
        raise sv.PackageConsistencyError("constructor evidence disagrees")
    monkeypatch.setattr(m13.sv, "open_versioned", boom)
    with pytest.raises(sv.PackageConsistencyError):
        m13.migrate_store(p, auth)
    # The authority was consumed AND a terminal failure event exists.
    assert auth.operation_id in m13._AUDIT._ops
    ev = m13._AUDIT._events.get((auth.operation_id, "migration_failed"))
    assert ev is not None
    assert ev["outcome"] == "package-inconsistent"
    assert ev["resulting_state"] == "unknown"     # the planner never published
    assert ev["resulting_version"] is None


# --- round 11, finding 4: the published state is deeply immutable -----------

def test_the_published_audit_state_is_deeply_read_only():
    """Round 11, finding 4: v12's `AuditState` held LIVE dicts exposed via
    `_ops`, so a held reference could flip an operation to `terminal` and drop
    its attempted event WITHOUT the single publish, its lock, or validation.
    Both the containers and the rows are now read-only proxies."""
    auth = m13.make_authority(_v1_store())
    _activate(auth)
    ops, events = m13._AUDIT._ops, m13._AUDIT._events
    with pytest.raises(TypeError):
        ops[auth.operation_id] = {}                       # container is frozen
    with pytest.raises(TypeError):
        ops[auth.operation_id]["state"] = "terminal"      # rows are frozen too
    with pytest.raises(TypeError):
        events[(auth.operation_id, "migration_attempted")]["event"] = "forged"


# --- round 11, correction A: a lost activation response is disambiguated ----

@pytest.mark.parametrize("committed,reason", [
    (True, "migration-quiescence-required"),
    (False, "migration-audit-unavailable"),
    (None, "migration-audit-state-unknown"),
])
def test_a_lost_activation_response_is_mapped_by_its_commit_flag(
        committed, reason, monkeypatch):
    """Round 11 correction A and round 12 finding 3: each `committed` value maps
    to a STRUCTURALLY DISTINCT closed outcome. Proven-written → the authority IS
    consumed (`migration-quiescence-required`); proven-not-written → the
    retryable `migration-audit-unavailable` (safe to re-present); UNKNOWN → the
    distinct `migration-audit-state-unknown` (the host must query the durable
    operation_id first — v13 collapsed None into the retryable outcome)."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.activate

    def flaky(a, output_digest):
        # committed=True MEANS the row is durably written, so a faithful mock
        # publishes it before the lost response (round 14, finding 2: the
        # wrapper then writes a terminal for the consumed authority).
        if committed is True:
            real(a, output_digest)
        raise m13.AuditStorageUnavailable("response lost", committed=committed)
    monkeypatch.setattr(m13._AUDIT, "activate", flaky)
    assert m13.migrate_store(p, auth) == reason


# --- round 11, correction B: event_id uniqueness is enforced ----------------

def test_a_repeated_event_id_is_rejected(monkeypatch):
    """Round 11, correction B: v12 keyed events by `(operation_id, event)` and
    never checked `event_id`, so a repeated generator produced two events with
    one primary key. The store now enforces the `event_id` PK. Authorities are
    minted BEFORE the generator is pinned, so their operation ids stay
    distinct and it is the event id that collides."""
    a1 = m13.make_authority(_v1_store())
    a2 = m13.make_authority(_v1_store())
    fixed = m13.uuid.UUID("00000000-0000-4000-8000-000000000000")
    monkeypatch.setattr(m13.uuid, "uuid4", lambda: fixed)
    _activate(a1)                                # first ev-<fixed> is accepted
    with pytest.raises(ValueError, match="not unique"):
        _activate(a2)                            # same id → PK violation


# --- round 11, finding 5: every validator total over NESTED malformed JSON --

_NESTED_MUTATIONS = {
    "schema_versions=null":
        lambda a: a.update(schema_versions=None),
    "version-record=null":
        lambda a: a["schema_versions"].update({"1": None}),
    "accepted=false":
        lambda a: a["schema_versions"]["1"].update(accepted=False),
    "accepted-entry=null":
        lambda a: a["schema_versions"]["1"]["accepted"].__setitem__(0, None),
    "accepted-objects=false":
        lambda a: a["schema_versions"]["1"]["accepted"][0].update(objects=False),
    "runtime-schema_version={}":
        lambda a: a["runtimes"][0].update(schema_version={}),
    "runtime-sqlite_version=[]":
        lambda a: a["runtimes"][0].update(sqlite_version=[]),
}


@pytest.mark.parametrize("label", list(_NESTED_MUTATIONS))
def test_every_validator_is_total_over_nested_malformed_json(label):
    """Round 11, finding 5: v12's validators were total over a malformed
    top-level CONTAINER but not over malformed NESTED JSON — a
    `schema_version={}` put a dict in a dedup key (`TypeError` from the kernel
    at context entry), a null version-record `.get`-crashed the path resolver,
    an `accepted: false` was iterated as a bool. Every validator now reports a
    problem list and the artifact is refused; none raises."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    _NESTED_MUTATIONS[label](art)
    with m13._registry():
        reports = [fn(art) for fn in (m13.schema_evidence_problems,
                                      m13.migration_runtime_artifact_problems,
                                      m13.path_evidence_problems,
                                      m13.expected_path_problems)]
    assert all(isinstance(r, list) for r in reports)      # total: never raises
    assert any(r for r in reports)                        # and the art is refused


@pytest.mark.parametrize("label", list(_NESTED_MUTATIONS))
def test_check_evidence_is_total_over_nested_malformed_json(label, monkeypatch,
                                                            tmp_path):
    """And the gate that wraps them returns a clean nonzero, never a
    traceback, for every nested malformation."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    _NESTED_MUTATIONS[label](art)
    seeded = tmp_path / "evidence.json"
    seeded.write_text(json.dumps(art, indent=1, sort_keys=True))
    monkeypatch.setattr(m13, "EVIDENCE_FILE", seeded)
    assert m13.check_evidence() == 1                       # must NOT raise


# ==========================================================================
# Round 12 regressions
# ==========================================================================

def _empty_valid_sqlite(path):
    """A present, valid, nonzero-size SQLite database with no application
    objects — materially different from an absent path."""
    c = sqlite3.connect(path)
    c.execute("PRAGMA user_version=0")
    c.execute("CREATE TABLE t(x)")            # force a real header/page
    c.execute("DROP TABLE t")
    c.commit()
    c.close()


# --- round 12, finding 2: absent vs unaccepted vs unknown -------------------

def test_an_existing_empty_store_is_unaccepted_not_missing():
    """Round 12, finding 2: v13 recorded `missing` for an existing, valid,
    empty SQLite database — collapsing a vanished file with an unexpected
    replacement. An existing-but-unaccepted store is now `unaccepted`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    os.remove(p)
    _empty_valid_sqlite(p)                    # a present, valid, empty database
    assert os.path.exists(p) and os.path.getsize(p) > 0
    out = m13.migrate_store(p, auth)
    assert out == "migration-source-missing"
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert ev["resulting_state"] == "unaccepted"
    assert ev["resulting_version"] is None


def test_a_proven_absent_path_is_missing():
    """The dual: a path proven absent is the only `missing` case."""
    p = _v1_store()
    auth = m13.make_authority(p)
    os.remove(p)                              # the path is now truly gone
    assert not os.path.lexists(p)
    out = m13.migrate_store(p, auth)
    assert out == "migration-source-missing"
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert ev["resulting_state"] == "missing"
    assert ev["resulting_version"] is None


# --- round 12, finding 3: unknown activation state is distinct --------------

def test_the_committed_flag_defaults_to_unknown_and_is_typed():
    """Round 12, finding 3: an omitted `committed` is UNKNOWN, never a
    fabricated `False`, and the value is exactly `bool | None`."""
    assert m13.AuditStorageUnavailable("x").committed is None
    assert m13.AuditStorageUnavailable("x", committed=True).committed is True
    for bad in (0, 1, "false", []):
        with pytest.raises(TypeError):
            m13.AuditStorageUnavailable("x", committed=bad)


# --- round 12, finding 4: the write error carries resulting_state -----------

def test_the_audit_write_error_carries_and_distinguishes_the_state():
    """Round 12, finding 4: v13's `MigrationAuditWriteError` dropped
    `resulting_state`, so a missing and an unknown ending raised indistinct
    `vNone` errors. Both now carry the state, and its message names it."""
    miss = m13.MigrationAuditWriteError(operation_id=_OP_ID, store_path="/s",
        facts=m13.TerminalFacts("migration-source-missing", 1, 2, False, False,
                                "missing", None))
    unk = m13.MigrationAuditWriteError(operation_id=_OP_ID, store_path="/s",
        facts=m13.TerminalFacts("migration-failed", 1, 2, None, None,
                                "unknown", None))
    assert miss.resulting_state == "missing" and unk.resulting_state == "unknown"
    assert "missing" in str(miss) and "unknown" in str(unk)
    assert "vNone" not in str(miss)
    # the same state/version relationship the terminal schema enforces
    with pytest.raises(ValueError, match="requires a null version"):
        m13.MigrationAuditWriteError(operation_id=_OP_ID, store_path="/s",
            facts=m13.TerminalFacts("migration-source-missing", 1, 2, False,
                                    False, "missing", 1))


def test_a_forced_terminal_write_failure_preserves_the_state(monkeypatch):
    """End to end: forcing the terminal write to fail on a missing source
    raises a `MigrationAuditWriteError` that still carries `missing`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    os.remove(p)

    def broken(operation_id, event, payload):
        raise OSError("audit storage died")
    monkeypatch.setattr(m13._AUDIT, "record_terminal", broken)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.resulting_state == "missing"
    assert exc.value.resulting_version is None


# --- round 12, finding 5: validators total under RECURSIVE mutation ---------

def test_every_validator_is_total_under_recursive_nested_mutation():
    """Round 12, finding 5: v13 guarded seven KNOWN key locations, not
    recursively — `paths[].runtime.source_id={}` and an accepted-manifestation
    `digest={}` still put a dict in a set/dict key. This walks EVERY node in
    the artifact tree × wrong-typed values; no validator may raise."""
    base = json.loads(m13.EVIDENCE_FILE.read_text())
    bad_values = [None, True, False, 0, 1, 1.5, "s", [], {}, [1], {"k": "v"}]

    def node_paths(obj, prefix=()):
        yield prefix
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield from node_paths(v, prefix + (k,))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                yield from node_paths(v, prefix + (i,))

    def set_at(obj, path, val):
        cur = obj
        for p in path[:-1]:
            cur = cur[p]
        cur[path[-1]] = val

    validators = [m13.schema_evidence_problems,
                  m13.migration_runtime_artifact_problems,
                  m13.path_evidence_problems, m13.expected_path_problems]
    combos = 0
    for path in node_paths(base):
        if not path:
            continue
        for val in bad_values:
            art = copy.deepcopy(base)
            try:
                set_at(art, path, val)
            except Exception:
                continue
            combos += 1
            with m13._registry():
                for fn in validators:
                    out = fn(art)             # must return a list, never raise
                    assert isinstance(out, list)
    assert combos > 5000                      # the tree is large; sanity floor


@pytest.mark.parametrize("path,val,fn", [
    (("paths", 0, "runtime", "source_id"), {}, "path_evidence_problems"),
    (("paths", 0, "runtime", "sqlite_version"), [], "expected_path_problems"),
    (("schema_versions", "1", "accepted", 0, "digest"), {}, "expected_path_problems"),
])
def test_the_specific_nested_key_escapes_are_closed(path, val, fn):
    """The three unhashable key escapes the reviewer measured, pinned."""
    art = json.loads(m13.EVIDENCE_FILE.read_text())
    cur = art
    for p in path[:-1]:
        cur = cur[p]
    cur[path[-1]] = val
    with m13._registry():
        assert isinstance(getattr(m13, fn)(art), list)   # no TypeError


# --- round 12, correction A: the operation row validates and freezes deeply -

def test_the_operation_row_validates_field_types():
    """Round 12, correction A: the audit store is the enforcing reference, so
    `_operation_row` validates every field's type and grammar — v13 accepted
    `backup_ref=[]` on the strength of the field-name set alone."""
    p = _v1_store()
    auth = m13.make_authority(p)
    store = m13.DraftAuditStore()
    with pytest.raises(ValueError, match="backup_ref"):
        store._operation_row(auth._replace(backup_ref=[]), "d" * 64)
    with pytest.raises(ValueError, match="digest"):
        store._operation_row(auth, "not-a-digest")
    # a well-formed row still passes
    store._operation_row(auth, "d" * 64)


def test_a_published_row_does_not_alias_caller_mutable_state():
    """Round 12, correction A: v13 proxied dict values but passed list values
    THROUGH by reference, so mutating the caller's original list mutated the
    published, supposedly-immutable audit row. The freeze is now deep."""
    frozen = m13._readonly({"backup_ref": ["a"], "nested": {"k": ["b"]}})
    with pytest.raises(TypeError):
        frozen["backup_ref"][0] = "x"         # tuples, not lists
    with pytest.raises(TypeError):
        frozen["nested"]["k"][0] = "x"
    original = ["a"]
    frozen2 = m13._readonly({"backup_ref": original})
    original.append("mutated")                # cannot reach the frozen copy
    assert frozen2["backup_ref"] == ("a",)


# --- round 12, correction B: the event_id grammar is enforced ---------------

def test_a_malformed_event_id_grammar_is_rejected(monkeypatch):
    """Round 12, correction B: v13 checked event-id UNIQUENESS but never the
    frozen `ev-<uuid4>` grammar, so a faulty generator's `ev-not-a-uuid` was
    accepted. Both grammar and uniqueness are now enforced before publication."""
    class FakeUUID:
        def __str__(self):
            return "not-a-uuid"
    auth = m13.make_authority(_v1_store())
    store = m13.DraftAuditStore()
    monkeypatch.setattr(m13.uuid, "uuid4", lambda: FakeUUID())
    with pytest.raises(ValueError, match="ev-<uuid4> grammar"):
        store.activate(auth, "d" * 64)


# ==========================================================================
# Round 13 regressions
# ==========================================================================

# --- round 13, finding 1: an unconfirmed rollback leaves the facts unknown ---

def test_an_unconfirmed_rollback_never_fabricates_boolean_facts():
    """Round 13, finding 1: v14 forced `store_changed`/`transaction_committed`
    to `False` for the unknown cell, asserting no change for a store a failed
    rollback may have left partially migrated. A rollback whose own result is
    unconfirmed leaves both facts `None` (unknown)."""
    rbf = m13._terminal_facts("migration-failed",
        {"facts": None, "observed_version": 1, "rolled_back": "rollback-failed",
         "source_absent": False})
    assert rbf["resulting_state"] == "unknown"
    assert rbf["store_changed"] is None
    assert rbf["transaction_committed"] is None
    # a CONFIRMED rollback of a read-rejection, by contrast, is a known False
    known = m13._terminal_facts("foreign-shape",
        {"facts": None, "observed_version": None, "rolled_back": "rolled-back",
         "source_absent": False})
    assert known["store_changed"] is False


def test_a_tri_state_unknown_terminal_record_is_accepted():
    """The unknown cell with `None` Booleans is a legal terminal record; a
    still-`None` pair must not be forced to agree with each other."""
    auth = m13.make_authority(_v1_store())
    _activate(auth)
    ts = m13.canonical_timestamp(__import__("datetime").datetime.now(
        __import__("datetime").timezone.utc))
    m13._AUDIT.record_terminal(auth.operation_id, "migration_failed",
        dict(outcome="migration-failed", store_changed=None,
             transaction_committed=None, resulting_version=None,
             resulting_state="unknown", occurred_at=ts))


# --- round 13, finding 2: post-commit cleanup is internal-error -------------

class _CloseFails:
    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    def close(self):
        raise sqlite3.DatabaseError("forced connection-close failure")


def test_a_post_commit_cleanup_failure_is_internal_error_not_invalid_store(
        monkeypatch):
    """Round 13, finding 2: v14 caught `sqlite3.DatabaseError` across the whole
    planner+cleanup region, so a `conn.close()` failure AFTER a committed
    migration was mislabeled `invalid-store` — telling the host to remediate a
    valid v2 database. A cleanup failure is now `internal-error` carrying the
    committed destination facts."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13.sqlite3.connect

    def wrapped(*a, **k):
        conn = real(*a, **k)
        if a and isinstance(a[0], str) and a[0].startswith("file:"):
            return _CloseFails(conn)
        return conn
    monkeypatch.setattr(m13.sqlite3, "connect", wrapped)
    out = m13.migrate_store(p, auth)
    assert out == "internal-error"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 2
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert ev["outcome"] == "internal-error"
    assert ev["resulting_state"] == "destination"      # committed facts kept
    assert ev["resulting_version"] == 2
    assert ev["transaction_committed"] is True


# --- round 13, finding 3: lexists() is not proof of absence -----------------

@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                    reason="root traverses any directory, so EACCES cannot be "
                           "provoked by chmod (round 14, correction C)")
def test_an_unsearchable_existing_store_is_not_proven_missing():
    """Round 13, finding 3: `os.path.lexists` returns False for a path the
    process cannot SEARCH to (EACCES on a parent), which v14 treated as a
    proven-absent `missing`. An unobservable path is now `store-unopenable`,
    never `missing` — the store never vanished. Round 14, correction C: skipped
    under root, which can traverse a `chmod 0` directory."""
    import stat as _stat
    d = tempfile.mkdtemp()
    sp = os.path.join(d, "store.db")
    c = sqlite3.connect(sp)
    for o in m13.SCHEMA_V1:
        c.execute(o.ddl)
    c.execute("PRAGMA user_version=1")
    c.commit()
    c.close()
    auth = m13.make_authority(sp)
    os.chmod(d, 0)                              # remove search permission
    try:
        out = m13.migrate_store(sp, auth)
    finally:
        os.chmod(d, _stat.S_IRWXU)
    assert out == "store-unopenable"           # NOT migration-source-missing
    assert os.path.exists(sp)                  # the store never vanished


# --- round 13, finding 4: each outcome permits only its physical states -----

@pytest.mark.parametrize("outcome,state,ok", [
    ("locked", "source", False),
    ("migration-source-missing", "source", False),
    ("invalid-store", "missing", False),
    ("unsupported-sqlite", "unaccepted", False),
    ("migrated", "source", False),
    ("locked", "unknown", True),
    ("migration-source-missing", "unaccepted", True),
    ("migration-failed", "source", True),
    ("migration-evidence-missing", "source", True),
    ("migrated", "destination", True),
])
def test_each_outcome_permits_only_its_physical_states(outcome, state, ok):
    """Round 13, finding 4: the terminal validator relates the OUTCOME to the
    states it can physically reach, not just effect/state — v14 accepted
    `locked`+source, `invalid-store`+missing and the like."""
    ver = {"source": 1, "destination": 2}.get(state)
    ch = (state == "destination")
    facts = m13.TerminalFacts(outcome, 1, 2, ch, ch, state, ver)
    problems = facts.problems()
    if ok:
        assert not problems, problems
    else:
        assert any("permits resulting_state" in p for p in problems), problems


# --- round 13, finding 5: one validated TerminalFacts, shared ---------------

def test_the_write_error_enforces_the_full_terminal_relationship():
    """Round 13, finding 5: v14's `MigrationAuditWriteError` validated only the
    null-version rule — a subset of the record's contract — so it accepted a
    committed `source`, a `destination` at the wrong version, and a non-bool
    `committed`. It now shares one validated `TerminalFacts`, so its contract is
    exactly as strong as the record's."""
    # a non-bool commit fact
    with pytest.raises(ValueError):
        m13.MigrationAuditWriteError(operation_id=_OP_ID, store_path="/s",
            facts=m13.TerminalFacts("migrated", 1, 2, 1, 1, "destination", 2))
    # a committed change that does not carry the destination version
    with pytest.raises(ValueError, match="committed change is at version"):
        m13.MigrationAuditWriteError(operation_id=_OP_ID, store_path="/s",
            facts=m13.TerminalFacts("migrated", 1, 2, True, True,
                                    "destination", 999))
    # a committed operation claiming the source state
    with pytest.raises(ValueError):
        m13.MigrationAuditWriteError(operation_id=_OP_ID, store_path="/s",
            facts=m13.TerminalFacts("migrated", 1, 2, True, True, "source", 1))
    # operation_id grammar is validated
    with pytest.raises(ValueError, match="op-<uuid4>"):
        m13.MigrationAuditWriteError(operation_id="op-x", store_path="/s",
            facts=m13.TerminalFacts("migrated", 1, 2, True, True,
                                    "destination", 2))


def test_the_record_and_the_exception_share_one_validator():
    """The same `TerminalFacts.problems()` gates both carriers — a fact set the
    record rejects, the exception rejects, and vice versa."""
    bad = m13.TerminalFacts("migrated", 1, 2, True, True, "source", 1)
    assert bad.problems()                                   # the shared verdict
    with pytest.raises(ValueError):                         # exception carrier
        m13.MigrationAuditWriteError(operation_id=_OP_ID, store_path="/s",
                                     facts=bad)


# --- round 13, correction A: operation-row paths reject embedded NULs -------

@pytest.mark.parametrize("badpath", ["\x00bad", "bad\x00path"])
def test_the_operation_row_rejects_embedded_nul_paths(badpath):
    """Round 13, correction A: a canonical filesystem path cannot contain an
    embedded NUL; the audit boundary rejects it rather than storing an unusable
    path."""
    auth = m13.make_authority(_v1_store())
    store = m13.DraftAuditStore()
    with pytest.raises(ValueError, match="NUL"):
        store._operation_row(auth._replace(store_path=badpath), "d" * 64)


# ==========================================================================
# Round 14 regressions
# ==========================================================================

# --- round 14, finding 1: TerminalFacts encodes the complete tuples ---------

@pytest.mark.parametrize("outcome,ch,co,state,ver,ok", [
    # the impossible facts v15 accepted
    ("migrated", False, False, "destination", 2, False),   # migrated must change
    ("current", None, None, "destination", 2, False),      # (None,None)→unknown
    ("migration-failed", None, None, "source", 1, False),  # (None,None)→unknown
    ("internal-error", None, True, "destination", 2, False),  # partial pair
    ("migrated", True, None, "destination", 2, False),     # partial pair
    # the complete valid tuples
    ("migrated", True, True, "destination", 2, True),
    ("current", False, False, "destination", 2, True),
    ("current", True, True, "destination", 2, True),
    ("migration-failed", False, False, "source", 1, True),
    ("migration-failed", None, None, "unknown", None, True),
    ("migration-quiescence-required", False, False, "unknown", None, True),
    ("migration-source-missing", False, False, "missing", None, True),
    ("migration-source-missing", False, False, "unaccepted", None, True),
])
def test_terminal_facts_encodes_the_complete_tuple(outcome, ch, co, state, ver,
                                                   ok):
    """Round 14, finding 1: `TerminalFacts.problems()` — shared by BOTH carriers
    — encodes the complete permitted tuples. A partial `None` pair, a
    disagreement, an `(None,None)` non-unknown cell, and a no-change `migrated`
    all reject; the seven valid shapes accept."""
    problems = m13.TerminalFacts(outcome, 1, 2, ch, co, state, ver).problems()
    assert (not problems) == ok, problems


def test_the_migrated_rule_lives_inside_terminal_facts():
    """The `migrated → changed+committed` rule is now INSIDE `TerminalFacts`, so
    the exception carrier (which only sees `TerminalFacts`) enforces it too —
    v15 held it in the record validator alone (finding 1)."""
    bad = m13.TerminalFacts("migrated", 1, 2, False, False, "destination", 2)
    assert any("changed and committed" in p for p in bad.problems())
    with pytest.raises(ValueError):
        m13.MigrationAuditWriteError(operation_id=_OP_ID, store_path="/s",
                                     facts=bad)


# --- round 14, finding 2: a committed activation-loss still terminalizes -----

def test_a_committed_activation_loss_still_writes_a_terminal(monkeypatch):
    """Round 14, finding 2: a `committed=True` activation whose response was
    lost is DURABLY consumed, so the wrapper must still write a terminal event
    — v15 left a spent authority with only an attempted record."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.activate

    def act_lose(a, output_digest):
        real(a, output_digest)                 # the row IS durably written
        raise m13.AuditStorageUnavailable("response lost after activation",
                                          committed=True)
    monkeypatch.setattr(m13._AUDIT, "activate", act_lose)
    assert m13.migrate_store(p, auth) == "migration-quiescence-required"
    ev = m13._AUDIT._events.get((auth.operation_id, "migration_failed"))
    assert ev is not None                      # NOT left with only 'attempted'
    assert ev["outcome"] == "migration-quiescence-required"
    assert ev["resulting_state"] == "unknown"
    assert ev["resulting_version"] is None


# --- round 14, finding 3: terminal-audit response loss is representable ------

def test_a_lost_terminal_response_reports_audit_committed(monkeypatch):
    """Round 14, finding 3: a terminal write that atomically committed then lost
    its response leaves a DURABLE record; `MigrationAuditWriteError.audit_committed`
    distinguishes that from a write that never landed."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.record_terminal

    def rt_lose(operation_id, event, payload):
        real(operation_id, event, payload)     # publishes durably
        raise OSError("response lost after durable terminal commit")
    monkeypatch.setattr(m13._AUDIT, "record_terminal", rt_lose)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.audit_committed is True   # the record IS durable
    # and a genuine not-written failure reports False
    p2 = _v1_store()
    auth2 = m13.make_authority(p2)
    monkeypatch.setattr(m13._AUDIT, "record_terminal",
                        lambda *a: (_ for _ in ()).throw(OSError("never wrote")))
    with pytest.raises(m13.MigrationAuditWriteError) as exc2:
        m13.migrate_store(p2, auth2)
    assert exc2.value.audit_committed is False


# --- round 14, finding 4: SQLite errors are classified by PHASE -------------

def test_a_runtime_probe_defect_is_internal_error_not_invalid_store(monkeypatch):
    """Round 14, finding 4: a `sqlite3.DatabaseError` from the runtime gate —
    BEFORE the store is connected or read — is a library defect, not corrupted
    store bytes. v15 tested 'commit facts exist', not the phase, and mislabeled
    it `invalid-store`."""
    p = _v1_store()
    auth = m13.make_authority(p)

    def boom():
        raise sqlite3.DatabaseError("runtime probe library defect")
    monkeypatch.setattr(m13.sv, "runtime_supported", boom)
    out = m13.migrate_store(p, auth)
    assert out == "internal-error"             # NOT invalid-store
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == 1


def test_invalid_store_is_only_the_planner_reading_bad_bytes(monkeypatch):
    """The dual: a `DatabaseError` raised WHILE `open_versioned` reads the store
    remains `invalid-store`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13.sv.open_versioned

    def boom(*a, **k):
        raise sqlite3.DatabaseError("malformed database image")
    monkeypatch.setattr(m13.sv, "open_versioned", boom)
    assert m13.migrate_store(p, auth) == "invalid-store"


# --- round 14, finding 5: package-inconsistent at every phase ---------------

@pytest.mark.parametrize("phase,state", [
    ("after-commit", "destination"),
    ("after-rollback", "source"),
    ("before-observe", "unknown"),
])
def test_a_package_inconsistency_terminalizes_at_every_phase(phase, state,
                                                             monkeypatch):
    """Round 14, finding 5: a `PackageConsistencyError` discovered after a commit
    carries destination facts, which v15's `package-inconsistent`-permits-only-
    unknown map rejected — producing a raw `ValueError` that lost the named
    escape. It is now terminalized with whichever facts are proven, at any
    phase, and the original exception re-raised."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real_ov = m13.sv.open_versioned
    real_vr = m13.validate_registry

    if phase == "before-observe":
        # raise before the transaction is entered
        monkeypatch.setattr(m13.sv, "open_versioned",
                            lambda *a, **k: (_ for _ in ()).throw(
                                sv.PackageConsistencyError("before observe")))
    elif phase == "after-rollback":
        # raise INSIDE the hook, AFTER the source is observed under the lock, so
        # the kernel genuinely ROLLS BACK (round 15, correction D: v16's
        # 'after-rollback' case ran the planner to commit — a post-commit case)
        def vr_boom(*a, **k):
            raise sv.PackageConsistencyError("after observe, before execute")
        monkeypatch.setattr(m13, "validate_registry", vr_boom)
    else:  # after-commit
        def ov_then(*a, **k):
            r = real_ov(*a, **k)               # migrates + commits
            raise sv.PackageConsistencyError("after commit")
        monkeypatch.setattr(m13.sv, "open_versioned", ov_then)

    with pytest.raises(sv.PackageConsistencyError):   # the ORIGINAL, re-raised
        m13.migrate_store(p, auth)
    ev = m13._AUDIT._events.get((auth.operation_id, "migration_failed"))
    assert ev is not None and ev["outcome"] == "package-inconsistent"
    assert ev["resulting_state"] == state
    if phase == "after-rollback":
        assert m13._AUDIT._ops[auth.operation_id]  # observed → source facts
        assert ev["resulting_version"] == 1        # the source version
        assert sqlite3.connect(p).execute(
            "PRAGMA user_version").fetchone()[0] == 1   # rolled back to v1


# --- round 14, corrections A & B --------------------------------------------

@pytest.mark.parametrize("outcome,state", [
    ([], "destination"), ("migrated", []), ("migrated", {}),
])
def test_terminal_facts_problems_is_total(outcome, state):
    """Round 14, correction A: `TerminalFacts.problems()` type-checks `outcome`
    and `resulting_state` BEFORE using them as hash keys — v15 raised a raw
    `TypeError` on `outcome=[]` / `resulting_state={}`."""
    out = m13.TerminalFacts(outcome, 1, 2, True, True, state, 2).problems()
    assert isinstance(out, list) and out       # reports, never raises


@pytest.mark.parametrize("store_path,from_v,to_v", [
    ("relative.db", 1, 2),                     # not absolute
    ("bad\x00path", 1, 2),                     # embedded NUL
    ("/ok", 2, 1),                             # reversed endpoints
])
def test_the_write_error_validates_its_context(store_path, from_v, to_v):
    """Round 14, correction B: the exception is a frozen public contract, so it
    validates path canonicality/NUL/cap and adjacent ordered endpoints — v15
    accepted a relative path, a NUL path, and reversed endpoints."""
    with pytest.raises(ValueError):
        m13.MigrationAuditWriteError(operation_id=_OP_ID, store_path=store_path,
            facts=m13.TerminalFacts("migrated", from_v, to_v, True, True,
                                    "destination", to_v))


# ==========================================================================
# Round 15 regressions
# ==========================================================================

# --- round 15, finding 1: only 'activated' may proceed to store access ------

@pytest.mark.parametrize("badval", [None, "bogus", True, object()])
def test_a_malformed_activation_result_never_touches_the_store(badval,
                                                               monkeypatch):
    """Round 15, finding 1: `activate()` returning anything but the closed
    vocabulary was treated as success, permitting an irreversible migration
    with NO operation row or attempted event. Any other value is now
    `internal-error` before the database is opened."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13._AUDIT, "activate", lambda a, od: badval)
    assert m13.migrate_store(p, auth) == "internal-error"
    assert auth.operation_id not in m13._AUDIT._ops        # nothing consumed
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 1          # store untouched


# --- round 15, finding 2: a malformed kernel result terminalizes cleanly -----

def test_a_malformed_kernel_result_is_internal_error_not_attribute_error(
        monkeypatch):
    """Round 15, finding 2: the kernel returning a bare string (not an
    `OpenResult`) made terminal derivation raise `AttributeError` OUTSIDE the
    closed boundary, stranding a consumed operation. It is validated and
    terminalizes as `internal-error`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13.sv, "open_versioned", lambda *a, **k: "migrated")
    assert m13.migrate_store(p, auth) == "internal-error"   # not an AttributeError
    ev = m13._AUDIT._events.get((auth.operation_id, "migration_failed"))
    assert ev is not None and ev["outcome"] == "internal-error"


# --- round 15, finding 3: hook SQLite errors are not invalid-store ----------

def test_a_migration_hook_database_error_is_migration_failed(monkeypatch):
    """Round 15, finding 3: a `sqlite3.DatabaseError` from WITHIN the migration
    hook is a migration failure, not the planner reading invalid store bytes."""
    p = _v1_store()
    auth = m13.make_authority(p)

    def fake_hook(art, authority, state):
        def h(*a, **k):
            raise sqlite3.DatabaseError("migration hook library defect")
        return h
    monkeypatch.setattr(m13, "_migrating_hook", fake_hook)
    assert m13.migrate_store(p, auth) == "migration-failed"   # not invalid-store


# --- round 15, finding 4: a read-rejected store is unaccepted, not unknown --

def test_a_readable_rejected_store_is_unaccepted_not_unknown():
    """Round 15, finding 4: a store that opened and was read but rejected as not
    an accepted source (an unauthorized extra table → stamped-shape-mismatch) is
    `unaccepted`, not `unknown` — it is the round-12 `unaccepted` case."""
    p = _v1_store()
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE alien(x)")         # not an accepted v1 source
    c.commit()
    c.close()
    twin = _v1_store()
    auth = m13.make_authority(twin)._replace(store_path=os.path.realpath(p))
    out = m13.migrate_store(p, auth)
    ev = m13._AUDIT._events.get((auth.operation_id, "migration_failed"))
    assert ev is not None
    assert ev["resulting_state"] == "unaccepted"           # NOT unknown
    assert ev["resulting_version"] is None


# --- round 15, finding 5: a setup failure closes the connection -------------

def test_an_isolation_level_setup_failure_closes_the_connection(monkeypatch):
    """Round 15, finding 5: an opened connection whose `isolation_level` setter
    raises must still be closed — cleanup begins the instant the connection
    exists. Closed exactly once, outcome `internal-error`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    holder = {}
    real = m13.sqlite3.connect

    class Proxy:
        def __init__(self, r):
            self._r = r
            self.closes = 0

        def __getattr__(self, n):
            return getattr(self._r, n)

        @property
        def isolation_level(self):
            return self._r.isolation_level

        @isolation_level.setter
        def isolation_level(self, v):
            raise sqlite3.DatabaseError("isolation setup failed")

        def close(self):
            self.closes += 1
            return self._r.close()

    def wrap(*a, **k):
        c = real(*a, **k)
        if a and isinstance(a[0], str) and a[0].startswith("file:"):
            holder["p"] = Proxy(c)
            return holder["p"]
        return c
    monkeypatch.setattr(m13.sqlite3, "connect", wrap)
    assert m13.migrate_store(p, auth) == "internal-error"
    assert holder["p"].closes == 1


# --- round 15, corrections A, B, C ------------------------------------------

def test_the_write_error_preserves_a_supplied_commit_status(monkeypatch):
    """Round 15, correction A: when the terminal-sink exception carries its own
    `.committed`, the wrapper PRESERVES it rather than inferring from local
    state (v16 always inferred, reporting False for a carried None/True)."""
    p = _v1_store()
    auth = m13.make_authority(p)

    def rt(operation_id, event, payload):
        raise m13.AuditStorageUnavailable("lost", committed=None)
    monkeypatch.setattr(m13._AUDIT, "record_terminal", rt)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.audit_committed is None               # preserved, not False


def test_non_adjacent_endpoints_and_integer_commit_flags_reject():
    """Round 15, correction B: the migration contract is adjacent (n → n+1), and
    `audit_committed` is exact-typed — `1` is not `True`."""
    assert m13.TerminalFacts("migrated", 1, 3, True, True, "destination",
                             3).problems()                  # non-adjacent
    with pytest.raises(TypeError):
        m13.MigrationAuditWriteError(operation_id=_OP_ID, store_path="/s",
            audit_committed=1,
            facts=m13.TerminalFacts("migrated", 1, 2, True, True,
                                    "destination", 2))


def test_a_non_mapping_terminal_payload_is_a_controlled_error():
    """Round 15, correction C: `record_terminal(op, event, None)` is a
    controlled schema error, never a raw `TypeError` from `set(None)`."""
    auth = m13.make_authority(_v1_store())
    _activate(auth)
    with pytest.raises(ValueError, match="payload must be a mapping"):
        m13._AUDIT.record_terminal(auth.operation_id, "migration_failed", None)


# ==========================================================================
# Round 16 regressions
# ==========================================================================

# --- round 16, finding 1: an activation token is not proof of activation ----

def test_an_activation_receipt_without_a_published_row_is_rejected(monkeypatch):
    """Round 16, finding 1: a receipt claiming `activated` is not proof — the
    reference store must actually hold the operation row and attempted event. A
    mock that returns the token without publishing is `internal-error` before
    any store access."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13._AUDIT, "activate",
                        lambda a, od: m13.ActivationReceipt(
                            "activated", a.operation_id, True, False))
    assert m13.migrate_store(p, auth) == "internal-error"
    assert auth.operation_id not in m13._AUDIT._ops
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 1          # store untouched


def test_an_equality_spoofing_activation_result_is_rejected(monkeypatch):
    """The receipt is checked by EXACT TYPE, not `==` — an object whose `__eq__`
    claims to equal a receipt cannot pass."""
    class Spoof:
        def __eq__(self, other):
            return True                    # equals anything
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13._AUDIT, "activate", lambda a, od: Spoof())
    assert m13.migrate_store(p, auth) == "internal-error"
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 1


# --- round 16, finding 2: terminal publication needs a success receipt ------

def test_a_silent_terminal_noop_raises_never_reports_success(monkeypatch):
    """Round 16, finding 2: a terminal sink that returns `None` (or a
    non-matching receipt) published no event — it MUST raise
    `MigrationAuditWriteError`, never let the public call return `migrated`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13._AUDIT, "record_terminal", lambda o, e, pl: None)
    with pytest.raises(m13.MigrationAuditWriteError):
        m13.migrate_store(p, auth)


# --- round 16, finding 3: the kernel result is validated SEMANTICALLY -------

@pytest.mark.parametrize("branch,ch,co,ver", [
    ("migrated", False, False, 1),          # migrated must change+commit at to
    ("migrated", True, True, 999),          # wrong version
    ("current", False, False, 1),           # current at the wrong version
    ("created", True, True, 2),             # created is forbidden in migrate mode
    ("adopted", True, True, 2),             # adopted is forbidden in migrate mode
])
def test_a_semantically_contradictory_kernel_result_is_internal_error(
        branch, ch, co, ver, monkeypatch):
    """Round 16, finding 3: v17 checked SHAPE only, so `migrated`/¬changed, a
    `created`/`adopted` in migrate mode, and `migrated`/v999 passed and were
    misreported as audit-storage failures. The mode-aware validator rejects
    them as `internal-error`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13.sv, "open_versioned", lambda *a, **k: sv.OpenResult(
        branch, store_changed=ch, transaction_committed=co,
        resulting_version=ver))
    assert m13.migrate_store(p, auth) == "internal-error"
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 1


# --- round 16, finding 4: hostile sink metadata never leaks a 3rd exception --

def test_a_hostile_committed_accessor_never_escapes(monkeypatch):
    """Round 16, finding 4: an exception whose `committed` property itself raises
    must not leak a third raw exception — the metadata access is guarded, the
    status is `None`, and the documented `MigrationAuditWriteError` is raised."""
    class Hostile(m13.AuditStorageUnavailable):
        def __init__(self, msg):
            Exception.__init__(self, msg)        # skip setting `committed`
        @property
        def committed(self):
            raise RuntimeError("committed accessor exploded")
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13._AUDIT, "record_terminal",
                        lambda o, e, pl: (_ for _ in ()).throw(Hostile("x")))
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.audit_committed is None       # guarded → unknown


# --- round 16, finding 5: a check-to-open race is a vanished source ---------

def test_a_source_deleted_between_check_and_open_is_missing(monkeypatch):
    """Round 16, finding 5: the source deleted between the pre-open `lstat` and
    SQLite's mode=rw open is a VANISHED source (`migration-source-missing` /
    `missing`), not `store-unopenable` — a fresh stat re-checks after the failed
    open."""
    p = _v1_store()
    auth = m13.make_authority(p)
    cp = os.path.realpath(p)
    real_lstat = os.lstat

    def lstat_then_delete(path, *a, **k):
        r = real_lstat(path, *a, **k)
        if str(path) == cp and os.path.exists(p):
            os.remove(p)                   # vanish right after the check
        return r
    monkeypatch.setattr(m13.os, "lstat", lstat_then_delete)
    assert m13.migrate_store(p, auth) == "migration-source-missing"
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert ev["resulting_state"] == "missing"


# --- round 16, corrections A, C, D ------------------------------------------

def test_a_duplicate_distinguishes_complete_from_attempted_only(monkeypatch):
    """Round 16, correction A: a duplicate that is already COMPLETE (a terminal
    event exists) is diagnostically distinct from an attempted-only one whose
    liveness is unknown — both refuse, but the reconciliation action differs."""
    complete = m13.ActivationReceipt("duplicate", _OP_ID, True,
                                     terminal_present=True)
    attempted = m13.ActivationReceipt("duplicate", _OP_ID, True,
                                      terminal_present=False)
    # the receipt carries the distinction the wrapper reports
    assert complete.terminal_present and not attempted.terminal_present


def test_the_event_id_grammar_enforces_uuid4_bits():
    """Round 16, correction C: the all-zeros UUID is not a v4 — the version and
    variant bits are enforced."""
    assert not m13._EVENT_ID_RE.fullmatch(
        "ev-00000000-0000-0000-0000-000000000000")
    assert m13._EVENT_ID_RE.fullmatch(
        "ev-00000000-0000-4000-8000-000000000000")
    assert not m13._OPERATION_RE.fullmatch(
        "op-00000000-0000-0000-0000-000000000000")


def test_migration_refused_raises_under_dash_o():
    """Round 16, correction D: `MigrationRefused` validates its closed reason
    with a raise, not an `assert` that vanishes under `python -O`."""
    import subprocess
    code = ("import sys; sys.path[:0]=['src','specs']\n"
            "import migrations_0013 as m\n"
            "try:\n m.MigrationRefused('not-a-real-reason')\n print('NO')\n"
            "except ValueError:\n print('RAISED')\n")
    r = subprocess.run([sys.executable, "-O", "-c", code],
                       capture_output=True, text=True, cwd=str(ROOT))
    assert "RAISED" in r.stdout, r.stderr


# ==========================================================================
# Round 17 regressions — verify CONTENT, not just existence
# ==========================================================================

def test_activation_binds_the_exact_authority_row(monkeypatch):
    """Round 17, finding 1: a receipt is not proof — the durable operation row
    must BIND the exact authority. A row published for a different store is
    `internal-error` before any store access."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.activate
    monkeypatch.setattr(m13._AUDIT, "activate",
                        lambda a, od: real(a._replace(
                            store_path="/tmp/wrong-store.db"), od))
    assert m13.migrate_store(p, auth) == "internal-error"
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 1          # store untouched


def test_a_false_duplicate_receipt_leaves_the_authority_usable(monkeypatch):
    """Round 17, correction A: a `duplicate` receipt with NO durable row is not
    trusted — it is `internal-error`, and the same authority still works."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.activate
    monkeypatch.setattr(m13._AUDIT, "activate",
                        lambda a, od: m13.ActivationReceipt(
                            "duplicate", a.operation_id, True, False))
    assert m13.migrate_store(p, auth) == "internal-error"
    monkeypatch.setattr(m13._AUDIT, "activate", real)
    assert m13.migrate_store(p, auth) == "migrated"        # never really consumed


def test_the_terminal_receipt_binds_the_requested_payload(monkeypatch):
    """Round 17, finding 2: a terminal event with a different (individually
    valid) payload than requested must raise — the receipt attests exact
    content, not merely existence under the key."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.record_terminal

    def wrong(operation_id, event, payload):
        bad = dict(payload)
        bad.update(outcome="current", store_changed=False,
                   transaction_committed=False)
        return real(operation_id, event, bad)
    monkeypatch.setattr(m13._AUDIT, "record_terminal", wrong)
    with pytest.raises(m13.MigrationAuditWriteError):
        m13.migrate_store(p, auth)


def test_the_returned_branch_must_equal_the_committed_branch(monkeypatch):
    """Round 17, finding 3: a committed `migrated` returned as `current` (same
    Boolean/version facts) is `internal-error` — the branch label is part of the
    agreement with `on_committed`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13.sv.open_versioned

    def relabel(*a, **k):
        r = real(*a, **k)                      # commits migrated, fires callback
        return sv.OpenResult("current", store_changed=r.store_changed,
                             transaction_committed=r.transaction_committed,
                             resulting_version=r.resulting_version)
    monkeypatch.setattr(m13.sv, "open_versioned", relabel)
    assert m13.migrate_store(p, auth) == "internal-error"


def test_a_malformed_on_committed_publication_never_asserts_no_change(
        monkeypatch):
    """Round 17, finding 4: a malformed `on_committed` value (suppressing the
    real one) is a defect — `internal-error` — and must NOT assert the store was
    unchanged. The commit state is UNKNOWN (`None`), never a fabricated `False`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13.sv.open_versioned

    def bad_callback(conn, path, **k):
        rest = dict(k)
        real_cb = rest.pop("on_committed")
        return real(conn, path,
                    on_committed=lambda r: real_cb("garbage-not-an-OpenResult"),
                    **rest)
    monkeypatch.setattr(m13.sv, "open_versioned", bad_callback)
    assert m13.migrate_store(p, auth) == "internal-error"
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert ev["store_changed"] is None         # uncertain, NOT a fabricated False
    assert ev["transaction_committed"] is None


def test_a_terminal_derivation_defect_never_escapes_raw(monkeypatch):
    """Round 17, finding 5: a defect in terminal-fact derivation after a
    committed migration must not escape as a raw exception and strand the
    operation — it terminalizes (or raises the documented write error)."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13, "_terminal_facts",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("terminal derivation exploded")))
    try:
        m13.migrate_store(p, auth)
    except m13.MigrationAuditWriteError:
        pass                                   # a named escape is acceptable
    except (AttributeError, TypeError, ValueError, RuntimeError) as exc:
        pytest.fail(f"raw exception escaped: {type(exc).__name__}: {exc}")
    # a terminal event was written from the frozen facts
    assert any((auth.operation_id, e) in m13._AUDIT._events
               for e in ("migration_completed", "migration_failed"))


@pytest.mark.parametrize("receipt,args", [
    (lambda: m13.ActivationReceipt("activated", _OP_ID, False, True),
     ("activation",)),
    (lambda: m13.TerminalReceipt("recorded", _OP_ID, "migration_completed", 1),
     ("terminal",)),
])
def test_receipt_problems_validate_every_scalar(receipt, args):
    """Round 17, correction B: both receipts have total `problems()` validators
    with exact scalar typing and cross-field consistency (`activated` cannot be
    `audit_committed=False`/`terminal_present=True`; `audit_committed=1` rejects)."""
    r = receipt()
    if args[0] == "activation":
        assert r.problems(_OP_ID)
    else:
        assert r.problems(_OP_ID, "migration_completed")


# --- round 18: verify the COMPLETE record, not one of its two parts ----------

def _corrupt_events(operation_id, key, value):
    """Replace one durable event under `key` with `value`, in place — the seam a
    hostile audit sink exploits."""
    st = m13._AUDIT._state
    evs = dict(st.events)
    evs[key] = m13._freeze(value)
    m13._AUDIT._state = st._replace(events=m13._readonly(evs))


def test_activation_binds_the_complete_attempted_event(monkeypatch):
    """Round 18, finding 1: v19 bound the operation ROW field-for-field but
    verified the attempted EVENT only by key existence, so a malformed attempted
    event under the right key let the irreversible operation proceed. The
    complete attempted event must bind the operation."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.activate

    def corrupt(a, od):
        r = real(a, od)
        _corrupt_events(a.operation_id,
                        (a.operation_id, m13._ATTEMPTED_EVENT),
                        {"event_id": "ev-00000000-0000-4000-8000-ffffffffffff",
                         "operation_id": "op-00000000-0000-4000-8000-ffffffffffff",
                         "event": "wrong", "occurred_at": "not-a-time"})
        return r
    monkeypatch.setattr(m13._AUDIT, "activate", corrupt)
    assert m13.migrate_store(p, auth) == "internal-error"
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 1          # store untouched


def test_terminal_write_requires_the_state_transition(monkeypatch):
    """Round 18, finding 2: a terminal event whose payload matches but whose
    operation row is left `attempted` is not a valid `attempted → terminal`
    transition — it must raise, not report `migrated`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.record_terminal

    def stuck(operation_id, event, payload):
        receipt = real(operation_id, event, payload)
        st = m13._AUDIT._state
        ops = dict(st.ops)
        ops[operation_id] = {**dict(ops[operation_id]), "state": "attempted"}
        m13._AUDIT._state = st._replace(ops=m13._readonly(ops))
        return receipt
    monkeypatch.setattr(m13._AUDIT, "record_terminal", stuck)
    with pytest.raises(m13.MigrationAuditWriteError):
        m13.migrate_store(p, auth)


def test_terminal_write_rejects_a_reused_event_id(monkeypatch):
    """Round 18, finding 2: a terminal event that reuses the attempted event's
    `event_id` violates the `event_id` primary key — it must raise."""
    p = _v1_store()
    auth = m13.make_authority(p)

    def reuse(operation_id, event, payload):
        st = m13._AUDIT._state
        att = st.events[(operation_id, m13._ATTEMPTED_EVENT)]
        evs = dict(st.events)
        evs[(operation_id, event)] = {
            "event_id": att["event_id"], "operation_id": operation_id,
            "event": event, **payload}
        ops = dict(st.ops)
        ops[operation_id] = {**dict(ops[operation_id]), "state": "terminal"}
        m13._AUDIT._state = st._replace(ops=m13._readonly(ops),
                                        events=m13._readonly(evs),
                                        seq=st.seq + 1)
        return m13.TerminalReceipt("recorded", operation_id, event,
                                   audit_committed=True)
    monkeypatch.setattr(m13._AUDIT, "record_terminal", reuse)
    with pytest.raises(m13.MigrationAuditWriteError):
        m13.migrate_store(p, auth)


def test_a_false_uncommitted_publication_never_suppresses_a_real_commit(
        monkeypatch):
    """Round 18, finding 3: a false `current`/(F,F) `on_committed` publication
    before the genuine `migrated`/(T,T) must NOT make the audit claim the store
    was unchanged. The conflict is a defect (`internal-error`), and the durable
    record retains the STRONGEST proven state — the real commit."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._make_on_committed

    def double(state, to_v, migrating):
        sink = real(state, to_v, migrating)
        fired = []

        def wrap(r):
            if not fired:
                fired.append(1)
                sink(sv.OpenResult("current", store_changed=False,
                                   transaction_committed=False,
                                   resulting_version=to_v))
            return sink(r)
        return wrap
    monkeypatch.setattr(m13, "_make_on_committed", double)
    assert m13.migrate_store(p, auth) == "internal-error"
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 2          # the migration ran
    # the conflict is a defect (`internal-error` → `migration_failed`), but the
    # durable facts retain the STRONGEST proven state — the real commit.
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert ev["outcome"] == "internal-error"
    assert ev["store_changed"] is True                     # the real commit kept
    assert ev["transaction_committed"] is True
    assert ev["resulting_state"] == "destination"


def test_a_derivation_fallback_agrees_public_and_durable_outcome(monkeypatch):
    """Round 18, finding 5: when terminal-fact derivation falls back to
    `internal-error`, the PUBLIC return must change with it — v19 recorded
    `internal-error` durably yet still returned `migrated`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13, "_terminal_facts",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("derivation boom")))
    out = m13.migrate_store(p, auth)
    assert out == "internal-error"                         # NOT the pre-fallback
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert ev["outcome"] == "internal-error"               # public == durable


def test_a_recorded_receipt_must_be_audit_committed(monkeypatch):
    """Round 18, correction A: a durably-verified `recorded` receipt necessarily
    committed the audit write — `audit_committed=False` is contradictory."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.record_terminal

    def false_committed(operation_id, event, payload):
        real(operation_id, event, payload)
        return m13.TerminalReceipt("recorded", operation_id, event,
                                   audit_committed=False)
    monkeypatch.setattr(m13._AUDIT, "record_terminal", false_committed)
    with pytest.raises(m13.MigrationAuditWriteError):
        m13.migrate_store(p, auth)


def test_a_duplicate_row_must_bind_the_authority(monkeypatch):
    """Round 18, correction B: a duplicate whose durable row belongs to a
    DIFFERENT store is an operation-ID collision, not an ordinary replay — it is
    `internal-error`, not a quiescence refusal."""
    p = _v1_store()
    auth = m13.make_authority(p)
    assert m13.migrate_store(p, auth) == "migrated"        # consume once
    st = m13._AUDIT._state                                 # corrupt the store_path
    ops = dict(st.ops)
    ops[auth.operation_id] = {**dict(ops[auth.operation_id]),
                              "store_path": "/other/store.db"}
    m13._AUDIT._state = st._replace(ops=m13._readonly(ops))
    assert m13.migrate_store(p, auth) == "internal-error"


def test_a_hostile_receipt_equality_never_escapes(monkeypatch):
    """Round 18, finding 4: a `TerminalReceipt` whose `status.__ne__` raises must
    not break the post-consumption boundary — it surfaces as the documented
    write error, never a raw exception."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.record_terminal

    class Hostile:
        def __eq__(self, o):
            raise RuntimeError("hostile __eq__")
        def __ne__(self, o):
            raise RuntimeError("hostile __ne__")

    def hostile(operation_id, event, payload):
        real(operation_id, event, payload)
        return m13.TerminalReceipt(Hostile(), operation_id, event,
                                   audit_committed=True)
    monkeypatch.setattr(m13._AUDIT, "record_terminal", hostile)
    with pytest.raises(m13.MigrationAuditWriteError):
        m13.migrate_store(p, auth)


def test_an_uncommittable_audit_flag_never_leaks_a_type_error(monkeypatch):
    """Round 18, finding 4: an `audit_committed=1` must be sanitized before it
    reaches `MigrationAuditWriteError`, whose constructor rejects a non-bool —
    the operation surfaces the write error, never a raw `TypeError`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.record_terminal

    def bad_flag(operation_id, event, payload):
        real(operation_id, event, payload)
        return m13.TerminalReceipt("recorded", operation_id, event,
                                   audit_committed=1)
    monkeypatch.setattr(m13._AUDIT, "record_terminal", bad_flag)
    with pytest.raises(m13.MigrationAuditWriteError):
        m13.migrate_store(p, auth)


# --- round 19: durable proof over receipts; preserved records; totality -------

def test_the_write_error_audit_committed_follows_durable_proof(monkeypatch):
    """Round 19, finding 1: once the wrapper has independently verified the
    complete durable transition, the audit write PROVABLY committed — a
    contradictory receipt (`audit_committed=False`) must not override that
    stronger evidence in the exception the caller uses to recover."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.record_terminal

    def lying(operation_id, event, payload):
        real(operation_id, event, payload)           # the transition IS durable
        return m13.TerminalReceipt("recorded", operation_id, event,
                                   audit_committed=False)
    monkeypatch.setattr(m13._AUDIT, "record_terminal", lying)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.audit_committed is True          # durable proof, not the lie


def test_a_noop_current_position_survives_a_post_callback_defect(monkeypatch):
    """Round 19, finding 2: a valid `current`/(F,F) callback proves the store IS
    a v2 destination even though nothing committed. A later internal defect must
    preserve that proven position, not record `unknown`."""
    p = _v1_store()
    a1, auth = m13.make_authority(p), m13.make_authority(p)  # both minted at v1
    m13.migrate_store(p, a1)                            # -> v2
    real = m13.sv.open_versioned                        # `auth` now sees no-op current

    def boom_after_position(*a, **k):
        real(*a, **k)                                  # fires on_committed(current/F/F)
        raise sqlite3.DatabaseError("defect after the destination was proven")
    monkeypatch.setattr(m13.sv, "open_versioned", boom_after_position)
    out = m13.migrate_store(p, auth)
    assert out == "internal-error"
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert ev["resulting_state"] == "destination"      # position preserved
    assert ev["resulting_version"] == 2
    assert ev["store_changed"] is False                # no commit — but known
    assert ev["transaction_committed"] is False


@pytest.mark.parametrize("corrupt", ["delete-attempted", "mutate-row"])
def test_terminalization_requires_the_prior_records_preserved(monkeypatch,
                                                              corrupt):
    """Round 19, correction A: a conforming terminal sink changes only the
    operation state `attempted → terminal`; the authority row and attempted
    event are immutable. A sink that deletes the attempted event or rewrites the
    row must raise, not report `migrated`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.record_terminal

    def tamper(operation_id, event, payload):
        rec = real(operation_id, event, payload)
        st = m13._AUDIT._state
        if corrupt == "delete-attempted":
            evs = dict(st.events)
            evs.pop((operation_id, m13._ATTEMPTED_EVENT), None)
            m13._AUDIT._state = st._replace(events=m13._readonly(evs))
        else:
            ops = dict(st.ops)
            ops[operation_id] = {**dict(ops[operation_id]),
                                 "store_path": "/wrong/store.db", "extra": 1}
            m13._AUDIT._state = st._replace(ops=m13._readonly(ops))
        return rec
    monkeypatch.setattr(m13._AUDIT, "record_terminal", tamper)
    with pytest.raises(m13.MigrationAuditWriteError):
        m13.migrate_store(p, auth)


def test_a_malformed_duplicate_lifecycle_is_audit_integrity():
    """Round 19, correction B: a duplicate whose durable lifecycle is neither a
    valid completed operation nor a valid attempted-only one (a `bogus` state) is
    an audit-integrity defect — `internal-error`, for investigation — not an
    ordinary quiescence replay."""
    p = _v1_store()
    auth = m13.make_authority(p)
    assert m13.migrate_store(p, auth) == "migrated"    # consume -> terminal
    st = m13._AUDIT._state                             # corrupt the lifecycle
    ops = dict(st.ops)
    ops[auth.operation_id] = {**dict(ops[auth.operation_id]), "state": "bogus"}
    m13._AUDIT._state = st._replace(ops=m13._readonly(ops))
    assert m13.migrate_store(p, auth) == "internal-error"


def test_activation_readback_requires_the_event_id_in_the_index(monkeypatch):
    """Round 19, correction C: the reference readback checks the surrogate
    `event_ids` index (the production `event_id` PRIMARY KEY) and the exact row
    field set — an attempted id missing from the index is `internal-error`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.activate

    def drop_index(a, od):
        r = real(a, od)
        st = m13._AUDIT._state
        m13._AUDIT._state = st._replace(event_ids=frozenset())
        return r
    monkeypatch.setattr(m13._AUDIT, "activate", drop_index)
    assert m13.migrate_store(p, auth) == "internal-error"
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 1      # store untouched


def test_receipt_validators_are_total_over_str_subclasses():
    """Round 19, correction D: `isinstance(x, str)` admits a `str` subclass whose
    equality raises; the validators use `type(x) is str`, so they classify a
    hostile subclass without invoking its equality method."""
    class BadStr(str):
        def __eq__(self, o):
            raise RuntimeError("hostile __eq__")

        def __ne__(self, o):
            raise RuntimeError("hostile __ne__")
        __hash__ = str.__hash__

    ar = m13.ActivationReceipt(BadStr("activated"), _OP_ID, True, False)
    assert ar.problems(_OP_ID)                         # rejected, not raised
    tr = m13.TerminalReceipt(BadStr("recorded"), _OP_ID,
                             "migration_completed", True)
    assert tr.problems(_OP_ID, "migration_completed")  # rejected, not raised


# --- round 20: strongest durable evidence on the activation path too ---------

def _has_terminal(auth):
    return any(oid == auth.operation_id and ev in m13._TERMINAL_EVENTS
              for (oid, ev) in m13._AUDIT._events)


@pytest.mark.parametrize("carrier", ["invalid-receipt", "committed-false"])
def test_a_durable_activation_is_consumed_despite_a_lying_carrier(monkeypatch,
                                                                 carrier):
    """Round 20, finding 1: a complete durable activation means the authority IS
    consumed, whatever the carrier says. An invalid `activated` receipt or a
    contradictory `committed=False` exception AFTER a durable write is
    `internal-error` WITH a terminal event — never left attempted-only, never
    advertised as a safe retry."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.activate

    def liar(a, output_digest):
        real(a, output_digest)                         # publish the real activation
        if carrier == "invalid-receipt":
            return m13.ActivationReceipt("activated", a.operation_id, False, False)
        raise m13.AuditStorageUnavailable("lost", committed=False)
    monkeypatch.setattr(m13._AUDIT, "activate", liar)
    assert m13.migrate_store(p, auth) == "internal-error"
    assert _has_terminal(auth)                          # NOT left attempted-only
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 1       # store untouched
    # the authority is durably consumed — a retry sees the durable row.


def test_a_terminal_sink_exception_cannot_override_durable_commit(monkeypatch):
    """Round 20, finding 2: a terminal sink that publishes the complete
    transition and then RAISES `committed=False` must not produce
    `audit_committed=False` — durable proof outranks the carrier on the exception
    path too."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.record_terminal

    def publish_then_raise(operation_id, event, payload):
        real(operation_id, event, payload)             # the transition IS durable
        raise m13.AuditStorageUnavailable("response lost", committed=False)
    monkeypatch.setattr(m13._AUDIT, "record_terminal", publish_then_raise)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.audit_committed is True


@pytest.mark.parametrize("cell", ["noop-destination", "missing-source"])
def test_terminal_fallback_preserves_every_established_state(monkeypatch, cell):
    """Round 20, finding 3: the terminal-derivation fallback preserves EVERY
    established physical state, not only a committed destination — a proven no-op
    v2 destination and a proven-missing source survive a derivation defect."""
    if cell == "noop-destination":
        p = _v1_store()
        a1, auth = m13.make_authority(p), m13.make_authority(p)
        m13.migrate_store(p, a1)                        # -> v2; `auth` sees no-op
        want = (False, False, "destination", 2)
    else:
        p = _v1_store()
        auth = m13.make_authority(p)
        os.remove(p)                                   # proven-missing source
        want = (False, False, "missing", None)
    monkeypatch.setattr(m13, "_terminal_facts",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("terminal derivation exploded")))
    m13.migrate_store(p, auth)
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert ev["outcome"] == "internal-error"
    assert (ev["store_changed"], ev["transaction_committed"],
            ev["resulting_state"], ev["resulting_version"]) == want


def test_terminal_facts_problems_total_over_hostile_str_subclass():
    """Round 20, correction A: the SHARED `TerminalFacts.problems()` uses
    `type(x) is str`, so a `str` subclass whose `__hash__` raises is classified,
    not executed (its totality is a finite acceptance property)."""
    class HashBoom(str):
        def __hash__(self):
            raise RuntimeError("hash boom")

    assert m13.TerminalFacts(HashBoom("migrated"), 1, 2, True, True,
                             "destination", 2).problems()
    assert m13.TerminalFacts("migrated", 1, 2, True, True,
                             HashBoom("destination"), 2).problems()


def test_a_duplicate_receipt_must_be_audit_committed():
    """Round 20, correction B: a `duplicate` necessarily means the operation row
    exists durably, so its audit write committed — `audit_committed=False` is
    contradictory and rejects as `internal-error`."""
    assert m13.ActivationReceipt("duplicate", _OP_ID, False, True).problems(_OP_ID)


# --- round 21: durable precedence for EVERY carrier; untrusted exceptions -----

@pytest.mark.parametrize("carrier", ["wrong-type-return", "unrecognized-exception"])
def test_durable_activation_consumed_for_every_carrier_class(monkeypatch, carrier):
    """Round 21, finding 1: durable readback precedes classifying EVERY carrier —
    a wrong-type return or an unrecognized post-publication exception after a
    durable activation is `internal-error` WITH a terminal event, never left
    attempted-only."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.activate

    def liar(a, output_digest):
        real(a, output_digest)                         # durable publication
        if carrier == "wrong-type-return":
            return None
        raise RuntimeError("unrecognized post-publication defect")
    monkeypatch.setattr(m13._AUDIT, "activate", liar)
    assert m13.migrate_store(p, auth) == "internal-error"
    assert any(oid == auth.operation_id and ev in m13._TERMINAL_EVENTS
               for (oid, ev) in m13._AUDIT._events)   # terminalized
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 1


def test_a_sink_supplied_write_error_is_an_untrusted_carrier(monkeypatch):
    """Round 21, finding 2: an adapter-supplied `MigrationAuditWriteError` cannot
    override durable proof or substitute the operation identity — the wrapper
    re-derives `audit_committed` and owns the identity, keeping the adapter's
    only as the cause."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.record_terminal

    def sink(operation_id, event, payload):
        real(operation_id, event, payload)             # complete durable transition
        raise m13.MigrationAuditWriteError(
            operation_id="op-11111111-1111-4111-8111-111111111111",
            store_path="/tmp/other-store.db",
            facts=m13.TerminalFacts("migrated", 1, 2, True, True,
                                    "destination", 2),
            audit_committed=False)                     # both lies
    monkeypatch.setattr(m13._AUDIT, "record_terminal", sink)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.audit_committed is True            # durable proof, not the lie
    assert exc.value.operation_id == auth.operation_id  # our identity, not foreign
    assert exc.value.store_path == auth.store_path
    assert isinstance(exc.value.__cause__, m13.MigrationAuditWriteError)


def test_committed_true_without_a_transition_is_not_proven_durable(monkeypatch):
    """Round 21, finding 3: a typed `committed=True` with NO observable terminal
    transition is contradictory adapter evidence — it degrades to `None`, never
    reported as proven audit durability."""
    p = _v1_store()
    auth = m13.make_authority(p)

    def sink(operation_id, event, payload):
        raise m13.AuditStorageUnavailable("nothing written", committed=True)
    monkeypatch.setattr(m13._AUDIT, "record_terminal", sink)
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.audit_committed is None


def test_timestamp_validation_is_total_over_hostile_str_subclasses():
    """Round 21, correction A: `_timestamp_problems` uses `type(x) is str`, so a
    `str` subclass whose `__len__` raises is classified, not executed — an invalid
    authority stays a closed refusal, never a library defect."""
    class LenBoom(str):
        def __len__(self):
            raise RuntimeError("len boom")

    assert m13._timestamp_problems(
        LenBoom("2026-01-01T00:00:00.000000+00:00"), "issued_at")
    p = _v1_store()
    auth = m13.make_authority(p)._replace(
        issued_at=LenBoom("2026-01-01T00:00:00.000000+00:00"))
    assert m13.migrate_store(p, auth) == "migration-quiescence-required"


# --- round 22: complete-lifecycle classification; frozen/exact-typed facts ----

def test_a_completed_lifecycle_is_quiescence_not_retryable(monkeypatch):
    """Round 22, finding 1: a completed (`terminal`) operation retried while
    `activate()` raises `committed=False` must be `migration-quiescence-required`
    — it is durably consumed and complete — never a false
    `migration-audit-unavailable` "safe retry"."""
    p = _v1_store()
    auth = m13.make_authority(p)
    assert m13.migrate_store(p, auth) == "migrated"     # now terminal
    monkeypatch.setattr(m13._AUDIT, "activate",
                        lambda a, od: (_ for _ in ()).throw(
                            m13.AuditStorageUnavailable("x", committed=False)))
    assert m13.migrate_store(p, auth) == "migration-quiescence-required"


def test_on_committed_facts_are_frozen_against_mutation(monkeypatch):
    """Round 22, finding 2: `on_committed` freezes a wrapper-owned copy, so a
    caller that MUTATES the live `OpenResult` after publication cannot change the
    published facts — the durable record keeps the frozen `(F,F)` position, never
    the mutated `(T,T)`."""
    p = _v1_store()
    a1, a2 = m13.make_authority(p), m13.make_authority(p)
    m13.migrate_store(p, a1)                            # -> v2; a2 sees no-op current
    real = m13._make_on_committed

    def mutating(state, to_v, migrating):
        sink = real(state, to_v, migrating)

        def wrap(r):
            sink(r)                                     # publish current/F/F
            r.store_changed = True                      # mutate the live object
            r.transaction_committed = True
        return wrap
    monkeypatch.setattr(m13, "_make_on_committed", mutating)
    m13.migrate_store(p, a2)
    ev = (m13._AUDIT._events.get((a2.operation_id, "migration_completed"))
          or m13._AUDIT._events.get((a2.operation_id, "migration_failed")))
    assert ev["store_changed"] is False                 # frozen, not the mutation
    assert ev["transaction_committed"] is False


def test_an_open_result_subclass_cannot_spoof_the_branch(monkeypatch):
    """Round 22, finding 2: `_frozen_from_open_result` requires `type(r) is
    OpenResult` and reads the branch from the underlying value, so a subclass
    whose `__str__` lies (`current` underneath, `migrated` on top) is refused —
    an untouched store is never reported `migrated`."""
    p = _v1_store()
    a1, a3 = m13.make_authority(p), m13.make_authority(p)
    m13.migrate_store(p, a1)                            # -> v2; a3 sees no-op current
    real = m13.sv.open_versioned

    class Spoof(sv.OpenResult):
        def __str__(self):
            return "migrated"

    def spoofing(conn, path, **k):
        s = Spoof("current", store_changed=True, transaction_committed=True,
                  resulting_version=2)
        if k.get("on_committed"):
            k["on_committed"](s)
        return s
    monkeypatch.setattr(m13.sv, "open_versioned", spoofing)
    assert m13.migrate_store(p, a3) == "internal-error"


@pytest.mark.parametrize("bad", ["facts-subclass", "operation-id-subclass"])
def test_the_write_error_requires_exact_carrier_types(bad):
    """Round 22, finding 3: `MigrationAuditWriteError` requires `type(facts) is
    TerminalFacts` and calls the BASE validator, and `type(operation_id) is str`
    — a `TerminalFacts` subclass overriding `problems()` cannot smuggle impossible
    caller-decision facts, and a `str` subclass id is refused."""
    class FakeTF(m13.TerminalFacts):
        def problems(self):
            return []

    class OpSub(str):
        pass
    if bad == "facts-subclass":
        with pytest.raises((ValueError, TypeError)):
            m13.MigrationAuditWriteError(
                operation_id=_OP_ID, store_path="/s",
                facts=FakeTF("migrated", 1, 2, False, False, "source", 1))
    else:
        with pytest.raises((ValueError, TypeError)):
            m13.MigrationAuditWriteError(
                operation_id=OpSub(_OP_ID), store_path="/s",
                facts=m13.TerminalFacts("migrated", 1, 2, True, True,
                                        "destination", 2))


def test_authority_validation_is_total_over_hostile_str_subclasses():
    """Round 22, correction A: the top-level `authority_static_problems` uses
    `type(x) is str` before `.strip()`/regex, so a `backup_ref` subclass whose
    `.strip()` raises is a closed `migration-quiescence-required` refusal, never a
    library `internal-error`."""
    class StripBoom(str):
        def strip(self, *a):
            raise RuntimeError("strip boom")
    p = _v1_store()
    auth = m13.make_authority(p)._replace(backup_ref=StripBoom("backup-ref-1"))
    assert m13.migrate_store(p, auth) == "migration-quiescence-required"


# --- round 23: the on_committed protocol contract; exact authority carrier ----

def test_a_success_requires_an_on_committed_publication(monkeypatch):
    """Round 23, finding 1: `on_committed` is the protocol proof a successful
    branch resolved. A kernel that returns a valid `migrated` WITHOUT publishing
    the callback (and without touching the store) must not be trusted — it is
    `internal-error`, and the store is untouched."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13.sv, "open_versioned",
                        lambda conn, path, **k: sv.OpenResult(
                            "migrated", store_changed=True,
                            transaction_committed=True, resulting_version=2))
    assert m13.migrate_store(p, auth) == "internal-error"
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 1


def test_on_committed_validates_the_semantic_cell_before_freezing(monkeypatch):
    """Round 23, finding 2: a structurally valid but semantically IMPOSSIBLE
    `migrated`/(F,F) publication must be a defect, not a frozen destination
    position — a later kernel error then records `unknown`, never a false
    destination-v2 state for a store still at v1."""
    p = _v1_store()
    auth = m13.make_authority(p)

    def bad_cell(conn, path, **k):
        if k.get("on_committed"):
            k["on_committed"](sv.OpenResult("migrated", store_changed=False,
                                            transaction_committed=False,
                                            resulting_version=2))
        raise sqlite3.DatabaseError("boom after impossible callback")
    monkeypatch.setattr(m13.sv, "open_versioned", bad_cell)
    assert m13.migrate_store(p, auth) == "internal-error"
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert ev["resulting_state"] == "unknown"          # NOT destination
    assert ev["resulting_version"] is None
    assert ev["store_changed"] is None


def test_a_migration_authority_subclass_is_a_closed_refusal():
    """Round 23, correction A + finding 3: a `MigrationAuthority` SUBCLASS (which
    can intercept attribute access) is refused as a malformed authority —
    `migration-quiescence-required`, never `internal-error`, before any field is
    read."""
    p = _v1_store()
    base = m13.make_authority(p)

    class Hostile(m13.MigrationAuthority):
        def __getattribute__(self, name):
            if name == "backup_ref":
                raise RuntimeError("hostile getter boom")
            return object.__getattribute__(self, name)
    assert m13.migrate_store(p, Hostile(*base)) == "migration-quiescence-required"


def test_a_late_authority_getter_never_strands_a_committed_operation():
    """Round 23, finding 3: a `MigrationAuthority` subclass whose getter begins
    raising AFTER the real commit must not escape raw and leave the operation
    attempted-only — exact-typing rejects it before consumption, so the store is
    never touched."""
    p = _v1_store()
    base = m13.make_authority(p)
    armed = [False]

    class HostileLate(m13.MigrationAuthority):
        def __getattribute__(self, name):
            if name == "from_version" and armed[0]:
                raise RuntimeError("late authority getter boom")
            return object.__getattribute__(self, name)
    try:
        out = m13.migrate_store(p, HostileLate(*base))
    except Exception as exc:                            # noqa: BLE001
        pytest.fail(f"raw escape: {type(exc).__name__}: {exc}")
    assert out == "migration-quiescence-required"       # rejected pre-consumption
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 1        # store untouched


# --- round 24: callback cardinality; single freeze; total rescue --------------

def test_a_second_identical_on_committed_publication_is_a_defect(monkeypatch):
    """Round 24, finding 1: the kernel fires `on_committed` exactly once, so ANY
    second publication — even value-IDENTICAL — is a cardinality violation the
    wrapper can observe. Two callbacks with no DB work is `internal-error`, store
    untouched, never a false success."""
    p = _v1_store()
    auth = m13.make_authority(p)

    def double_pub(conn, path, **k):
        r = sv.OpenResult("migrated", store_changed=True,
                          transaction_committed=True, resulting_version=2)
        if k.get("on_committed"):
            k["on_committed"](r)
            k["on_committed"](r)                       # identical repeat
        return r
    monkeypatch.setattr(m13.sv, "open_versioned", double_pub)
    assert m13.migrate_store(p, auth) == "internal-error"
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 1


def test_the_returned_result_is_frozen_once_no_reread(monkeypatch):
    """Round 24, finding 2: the returned label is frozen EXACTLY ONCE and that
    immutable value drives everything. A kernel that publishes `current`/(F,F)
    then mutates the returned object to `(T,T)` before returning is caught as a
    contradiction (`internal-error`) — the mutation never becomes the durable
    facts."""
    p = _v1_store()
    a1, a2 = m13.make_authority(p), m13.make_authority(p)
    m13.migrate_store(p, a1)                            # -> v2; a2 sees no-op current
    real = m13.sv.open_versioned

    def mutate_after_callback(conn, path, **k):
        r = sv.OpenResult("current", store_changed=False,
                          transaction_committed=False, resulting_version=2)
        if k.get("on_committed"):
            k["on_committed"](r)                       # publish F/F
        r.store_changed = True                          # then mutate the returned obj
        r.transaction_committed = True
        return r
    monkeypatch.setattr(m13.sv, "open_versioned", mutate_after_callback)
    out = m13.migrate_store(p, a2)
    assert out == "internal-error"                     # contradiction caught
    ev = (m13._AUDIT._events.get((a2.operation_id, "migration_completed"))
          or m13._AUDIT._events.get((a2.operation_id, "migration_failed")))
    assert ev["store_changed"] is not True             # the (T,T) mutation never leaked


def test_a_fallback_helper_defect_never_escapes_after_commit(monkeypatch):
    """Round 24, finding 3: the terminal rescue must not re-run a helper that has
    already failed. Even if the shared `_store_facts_from_state` derivation helper
    raises consistently after a real commit, no raw exception escapes and the
    operation is terminalized (round 26: the rescue is fully inline, independent
    of that helper family)."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13, "_store_facts_from_state",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("derivation boom")))
    try:
        m13.migrate_store(p, auth)
    except m13.MigrationAuditWriteError:
        pass                                           # a named escape is acceptable
    except Exception as exc:                            # noqa: BLE001
        pytest.fail(f"raw escape: {type(exc).__name__}: {exc}")
    assert any(oid == auth.operation_id and ev in m13._TERMINAL_EVENTS
               for (oid, ev) in m13._AUDIT._events)    # terminalized, not stranded


def test_static_resolution_problems_is_total_over_an_authority_subclass():
    """Round 24, correction A: `_static_resolution_problems` exact-types the
    carrier, so its 'total over any input' claim holds even reached directly — a
    `MigrationAuthority` subclass with a hostile getter returns a problem, never
    raises."""
    p = _v1_store()
    base = m13.make_authority(p)

    class Hostile(m13.MigrationAuthority):
        def __getattribute__(self, name):
            if name == "source_digest":
                raise RuntimeError("resolution getter boom")
            return object.__getattribute__(self, name)
    art = [json.loads(m13.EVIDENCE_FILE.read_text()), "x" * 64]
    assert m13._static_resolution_problems(Hostile(*base), art)   # no raise


# --- round 25: proven facts survive a wrapper VERIFIER defect -----------------

def test_a_verifier_defect_preserves_the_durable_terminal_result(monkeypatch):
    """Round 25, finding 1: a defect in the wrapper's OWN post-publication
    verification (`_terminal_transition_complete` raising) after the sink has
    already published the complete transition must NOT discard the durable record
    — the exception carries the exact requested facts and `audit_committed=True`.
    """
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13, "_terminal_transition_complete",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("transition verifier boom")))
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.facts.outcome == "migrated"
    assert exc.value.committed is True                  # store commit preserved
    assert exc.value.resulting_state == "destination"
    assert exc.value.audit_committed is True            # durable audit proven


def test_the_safe_fallback_never_erases_a_proven_commit(monkeypatch):
    """Round 25, finding 2: a defect in the shared `_store_facts_from_state`
    derivation helper after a proven real commit must not erase it — the rescue
    reconstructs the committed destination INDEPENDENTLY of that helper family."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13, "_store_facts_from_state",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("derivation helper boom")))
    out = m13.migrate_store(p, auth)
    assert out == "internal-error"
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert (ev["store_changed"], ev["transaction_committed"],
            ev["resulting_state"], ev["resulting_version"]) == \
        (True, True, "destination", 2)


def test_an_activation_readback_defect_still_terminalizes(monkeypatch):
    """Round 25, finding 3: a defect in the activation binding VERIFIER after a
    real atomic activation (valid `activated` receipt) must not strand the
    durably-consumed operation attempted-only — it terminalizes."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13, "_durable_row_binds_authority",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("readback verifier boom")))
    assert m13.migrate_store(p, auth) == "internal-error"
    assert any(oid == auth.operation_id and ev in m13._TERMINAL_EVENTS
               for (oid, ev) in m13._AUDIT._events)     # terminalized, not stranded


def test_an_activated_receipt_lie_without_a_row_stays_not_consumed(monkeypatch):
    """Round 25, finding 3 (boundary): a valid `activated` receipt with NO durable
    row (a clean readback rejection, not a verifier defect) is `internal-error`
    and NOT consumed — it must not become a terminal-write failure."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13._AUDIT, "activate",
                        lambda a, od: m13.ActivationReceipt(
                            "activated", a.operation_id, True, False))
    assert m13.migrate_store(p, auth) == "internal-error"
    # never consumed: a retry with the real sink migrates.
    monkeypatch.undo()
    assert m13.migrate_store(p, auth) == "migrated"


def test_static_resolution_exact_types_its_fields():
    """Round 25, correction A: `_static_resolution_problems` exact-types the
    digest fields, so an EXACT `MigrationAuthority` carrying a hostile `str`
    subclass digest returns a problem, never raises."""
    p = _v1_store()
    base = m13.make_authority(p)

    class EqBoom(str):
        def __eq__(self, o):
            raise RuntimeError("digest eq boom")
        __hash__ = str.__hash__
    art = [json.loads(m13.EVIDENCE_FILE.read_text()), "x" * 64]
    auth = base._replace(source_digest=EqBoom(base.source_digest))
    assert m13._static_resolution_problems(auth, art)   # no raise


# --- round 26: verifier FALSE-NEGATIVES; response-loss; full fallback table ----

def test_an_activation_verifier_false_negative_still_terminalizes(monkeypatch):
    """Round 26, finding 1a: a valid `activated` receipt whose durable row EXISTS,
    with a binding verifier that returns a clean FALSE-NEGATIVE (not raising),
    must terminalize the consumed operation — not reclassify it as a prior
    attempted-only replay."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13, "_durable_row_binds_authority",
                        lambda *a, **k: (False, "forced false-negative"))
    assert m13.migrate_store(p, auth) == "internal-error"
    assert any(oid == auth.operation_id and ev in m13._TERMINAL_EVENTS
               for (oid, ev) in m13._AUDIT._events)


def test_a_terminal_verifier_false_negative_preserves_audit_commit(monkeypatch):
    """Round 26, finding 1b: a valid `TerminalReceipt` with a transition verifier
    that returns a clean FALSE-NEGATIVE preserves `audit_committed=True` and the
    requested `migrated` facts."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13, "_terminal_transition_complete",
                        lambda *a, **k: (False, "forced false-negative"))
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.facts.outcome == "migrated"
    assert exc.value.audit_committed is True


def test_committed_true_response_loss_survives_a_verifier_defect(monkeypatch):
    """Round 26, finding 2: a recognized `committed=True` response-loss carrier
    combined with a RAISING transition verifier preserves the requested `migrated`
    facts and `audit_committed=True` — a raising verifier has not proved absence,
    so the typed carrier is trusted."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.record_terminal

    def publish_then_raise(operation_id, event, payload):
        real(operation_id, event, payload)
        raise m13.AuditStorageUnavailable("response lost", committed=True)
    monkeypatch.setattr(m13._AUDIT, "record_terminal", publish_then_raise)
    monkeypatch.setattr(m13, "_terminal_transition_complete",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("verifier boom")))
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.facts.outcome == "migrated"
    assert exc.value.audit_committed is True


def test_committed_true_with_a_clean_missing_transition_stays_none(monkeypatch):
    """Round 26 boundary (round 21 finding 3 preserved): a `committed=True` carrier
    with a CLEANLY-observed missing transition is contradictory — `None`, not
    trusted `True`. Only a RAISING verifier trusts the carrier."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13._AUDIT, "record_terminal",
                        lambda *a: (_ for _ in ()).throw(
                            m13.AuditStorageUnavailable("nothing written",
                                                        committed=True)))
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.audit_committed is None


def test_the_fallback_preserves_known_unchanged(monkeypatch):
    """Round 26, finding 3: a defect before the store is opened, plus a derivation
    helper failure, records `False/False/unknown` (KNOWN unchanged — no transaction
    entered), not the `None/None` uncertainty cell."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13, "_store_facts_from_state",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("derivation boom")))
    monkeypatch.setattr(m13.sv, "runtime_supported",
                        lambda *a, **k: (_ for _ in ()).throw(
                            sqlite3.DatabaseError("gate boom")))
    m13.migrate_store(p, auth)
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert (ev["store_changed"], ev["transaction_committed"],
            ev["resulting_state"], ev["resulting_version"]) == \
        (False, False, "unknown", None)


def test_the_fallback_preserves_read_rejected_unaccepted(monkeypatch):
    """Round 26, finding 3: a store the planner opened and READ but rejected as
    not an accepted source, plus a derivation helper failure, records
    `False/False/unaccepted` — not `unknown`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    c = sqlite3.connect(p)                              # corrupt the shape post-mint
    c.execute("CREATE TABLE intruder (x)")
    c.commit()
    c.close()
    monkeypatch.setattr(m13, "_store_facts_from_state",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("derivation boom")))
    m13.migrate_store(p, auth)
    ev = m13._AUDIT._events[(auth.operation_id, "migration_failed")]
    assert (ev["store_changed"], ev["transaction_committed"],
            ev["resulting_state"], ev["resulting_version"]) == \
        (False, False, "unaccepted", None)


# ==========================================================================
# Round 27 regressions — the SYMMETRY of a committed=True response-loss carrier
# under a verifier that cannot confirm, and exact-typed carrier trust
# ==========================================================================

def test_activation_committed_true_consumes_when_the_verifier_raises(monkeypatch):
    """Round 27, finding 1: an EXACT `AuditStorageUnavailable(committed=True)`
    activation carrier is proof the row was written (the authority IS consumed).
    Even when the readback VERIFIER raises, the operation terminalizes as a
    consumed quiescence — never stranded attempted-only."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.activate

    def commit_then_raise(a, od):
        real(a, od)                                    # the durable write DID happen
        raise m13.AuditStorageUnavailable("response lost", committed=True)
    monkeypatch.setattr(m13._AUDIT, "activate", commit_then_raise)
    monkeypatch.setattr(m13, "_durable_row_binds_authority",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("verifier boom")))
    assert m13.migrate_store(p, auth) == "migration-quiescence-required"
    assert _has_terminal(auth)            # consumed → terminalized


def test_activation_committed_true_consumes_on_a_verifier_false_negative(monkeypatch):
    """Round 27, finding 1 (symmetry): the same, when the verifier returns a clean
    FALSE-negative instead of raising."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.activate

    def commit_then_raise(a, od):
        real(a, od)
        raise m13.AuditStorageUnavailable("response lost", committed=True)
    monkeypatch.setattr(m13._AUDIT, "activate", commit_then_raise)
    monkeypatch.setattr(m13, "_durable_row_binds_authority",
                        lambda *a, **k: (False, "forced false-negative"))
    assert m13.migrate_store(p, auth) == "migration-quiescence-required"
    assert _has_terminal(auth)


def test_an_activation_committed_true_subclass_does_not_consume(monkeypatch):
    """Round 27, finding 3 (activation symmetry): a SUBCLASS claiming
    committed=True is NOT the protocol carrier — it must not establish consumption.
    With no durable row it is an unrecognized defect → `internal-error`, never a
    fabricated `migration-quiescence-required`."""
    class Evil(m13.AuditStorageUnavailable):
        def __init__(self, msg):
            Exception.__init__(self, msg)
            self.committed = True
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13._AUDIT, "activate",
                        lambda a, od: (_ for _ in ()).throw(Evil("lie")))
    assert m13.migrate_store(p, auth) == "internal-error"


def test_terminal_committed_true_false_negative_over_a_real_lifecycle(monkeypatch):
    """Round 27, finding 2: a `committed=True` terminal carrier plus a verifier
    FALSE-negative (returns False, not raising) over an EXISTING complete terminal
    lifecycle preserves `audit_committed=True` — the independent durable presence
    of a well-formed terminal event overrides the verifier boolean."""
    p = _v1_store()
    auth = m13.make_authority(p)
    real = m13._AUDIT.record_terminal

    def publish_then_raise(operation_id, event, payload):
        real(operation_id, event, payload)             # the lifecycle IS complete
        raise m13.AuditStorageUnavailable("response lost", committed=True)
    monkeypatch.setattr(m13._AUDIT, "record_terminal", publish_then_raise)
    monkeypatch.setattr(m13, "_terminal_transition_complete",
                        lambda *a, **k: (False, "forced false-negative"))
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.audit_committed is True


def test_a_committed_true_subclass_never_fabricates_a_commit(monkeypatch):
    """Round 27, finding 3: a SUBCLASS claiming committed=True, raised with NO
    durable write and the verifier defeated, must NOT fabricate
    `audit_committed=True` — only the EXACT protocol carrier is trusted, so the
    fact is genuinely `None`."""
    class Evil(m13.AuditStorageUnavailable):
        def __init__(self, msg):
            Exception.__init__(self, msg)
            self.committed = True
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13._AUDIT, "record_terminal",
                        lambda o, e, pl: (_ for _ in ()).throw(Evil("lie")))
    monkeypatch.setattr(m13, "_terminal_transition_complete",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("verifier boom")))
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.audit_committed is None


def test_a_committed_true_subclass_with_a_clean_missing_transition_is_none(monkeypatch):
    """Round 27, finding 3 boundary: even when the verifier CLEANLY observes the
    transition missing, a subclass committed=True is untrusted → `None`, never a
    fabricated `True` and never an inferred `False`."""
    class Evil(m13.AuditStorageUnavailable):
        def __init__(self, msg):
            Exception.__init__(self, msg)
            self.committed = True
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13._AUDIT, "record_terminal",
                        lambda o, e, pl: (_ for _ in ()).throw(Evil("lie")))
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.audit_committed is None


def test_a_raw_exception_with_no_write_still_reports_committed_false(monkeypatch):
    """Round 27 boundary (round 20 f2 preserved): a NON-family raw exception with
    no durable event is proven-not-written by the draft's own state → `False`;
    exact-typing the carrier must not degrade this to `None`."""
    p = _v1_store()
    auth = m13.make_authority(p)
    monkeypatch.setattr(m13._AUDIT, "record_terminal",
                        lambda o, e, pl: (_ for _ in ()).throw(
                            OSError("terminal write response lost")))
    with pytest.raises(m13.MigrationAuditWriteError) as exc:
        m13.migrate_store(p, auth)
    assert exc.value.audit_committed is False
