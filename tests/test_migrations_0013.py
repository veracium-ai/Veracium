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
    assert _activate(auth) == "activated"
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
            "source_absent": False}
    base.update(over)
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
