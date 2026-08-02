"""Every adversarial counterexample the external reviews have constructed.

(Round counts are generated -- see `specs/STATUS.md`; none is stated here.)

**These were a hand-rolled harness inside the instrument until round 5.** It
printed 30 result rows and reported `28/28`, because its total was a
hand-maintained arithmetic expression — a tool whose whole purpose is truthful
evidence, miscounting its own evidence. Moving them into pytest removes that
class of defect entirely: the count comes from collection.

Each test names the round that built the case, so a regression says which
review would have caught it.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "specs"))

from schema_migrations import (MIGRATIONS, Migration, apply_migration,  # noqa: E402
                               validate_registry)
from schema_model import (REBUILDABLE, REQUIRED, SCHEMA_V1, SCHEMAS,  # noqa: E402
                          SchemaObject, create, declared_policies, digest, drift,
                          identity, manifest, registry_conformance,
                          reviewed_policies, resolve)
from veracium.store.sqlite import SqliteStore, _SCHEMA  # noqa: E402


def _fresh() -> str:
    p = tempfile.mktemp(suffix=".db")
    SqliteStore(p)
    return p


def _objs(path: str) -> dict:
    c = sqlite3.connect(path)
    try:
        return manifest(c)
    finally:
        c.close()


def _mutate(sql, collation=False) -> str:
    p = _fresh()
    c = sqlite3.connect(p)
    if collation:
        c.create_collation("MYCOLL", lambda a, b: (a > b) - (a < b))
    for s in sql:
        c.execute(s)
    c.commit()
    c.close()
    return p


def _variant(old: str, new: str) -> str:
    """One change against the REAL schema text.

    Hand-writing a near-copy is how two of round 2's counterexamples first
    failed to reproduce: the reconstruction differed in some *other* way, so it
    was caught for the wrong reason."""
    text = _SCHEMA.replace(old, new)
    assert text != _SCHEMA, f"variant did not apply: {old!r}"
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    c.executescript(text)
    c.commit()
    c.close()
    return p


@pytest.fixture
def clean():
    return digest(_objs(_fresh()))


# --- shapes that must be REFUSED -----------------------------------------

def _stripped() -> str:
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    c.executescript(
        "CREATE TABLE edges (id TEXT, user_id TEXT, subject TEXT, relation TEXT,"
        " object TEXT, active INTEGER, quarantined INTEGER, json TEXT);"
        "CREATE TABLE episodes (id TEXT, user_id TEXT, date TEXT, json TEXT);"
        "CREATE TABLE wiki (user_id TEXT, text TEXT, store_version INTEGER);"
        "CREATE TABLE write_counter (user_id TEXT, n INTEGER);")
    c.commit()
    c.close()
    return p


REFUSED = {
    "r1_constraint_stripped_clone": _stripped,
    "r1_generated_column": lambda: _mutate(
        ["ALTER TABLE edges ADD COLUMN leak TEXT "
         "GENERATED ALWAYS AS (subject||object) VIRTUAL"]),
    "r1_unrelated_table": lambda: _mutate(["CREATE TABLE unrelated_application_data (x)"]),
    "r1_trigger_on_a_protected_table": lambda: _mutate(
        ["CREATE TRIGGER t AFTER INSERT ON edges BEGIN UPDATE edges SET active=0; END"]),
    "r2_check_constraint": lambda: _variant(
        "active INTEGER NOT NULL,", "active INTEGER NOT NULL CHECK(active = 0),"),
    "r2_collate_nocase_primary_key": lambda: _variant(
        "id TEXT PRIMARY KEY", "id TEXT COLLATE NOCASE PRIMARY KEY"),
    "r2_extra_view": lambda: _mutate(["CREATE VIEW v AS SELECT * FROM edges"]),
    "r2_host_collation_index": lambda: _mutate(
        ["CREATE INDEX ix_custom ON edges(subject COLLATE MYCOLL)"], collation=True),
    "r3_check_literal_whitespace": lambda: _variant(
        "object TEXT,", "object TEXT CHECK(object <> 'a  b'),"),
    "r3_trigger_named_like_an_index": lambda: _mutate(
        ["CREATE TRIGGER ix_edges_subj_rel AFTER INSERT ON edges "
         "BEGIN UPDATE edges SET active=0 WHERE id=NEW.id; END"]),
}


@pytest.mark.parametrize("name", sorted(REFUSED))
def test_a_non_identical_schema_is_refused(name, clean):
    assert digest(_objs(REFUSED[name]())) != clean


# --- shapes that must NOT be refused -------------------------------------
# These are the ones to read sceptically. A check that refuses stores which are
# genuinely fine gets bypassed, and a bypassed check is weaker than a narrower
# one that holds.

def test_analyze_does_not_change_the_digest(clean):
    assert digest(_objs(_mutate(["ANALYZE"]))) == clean


def test_a_missing_acceleration_index_is_drift_not_refusal(clean):
    objs = _objs(_mutate(["DROP INDEX ix_edges_subj_rel"]))
    assert digest(objs) == clean
    assert drift(objs) == [("index", "ix_edges_subj_rel")]


def test_a_wrong_same_named_index_is_drift_not_refusal(clean):
    objs = _objs(_mutate(["DROP INDEX ix_edges_subj_rel",
                          "CREATE UNIQUE INDEX ix_edges_subj_rel ON edges(user_id, subject)"]))
    assert digest(objs) == clean
    assert drift(objs) == [("index", "ix_edges_subj_rel")]


def test_a_trigger_named_like_an_index_is_not_mistaken_for_drift(clean):
    """Round 3: v4 reported it AS index drift, which would have sent an
    implementation off to repair an index that was never broken."""
    objs = _objs(REFUSED["r3_trigger_named_like_an_index"]())
    assert digest(objs) != clean
    assert drift(objs) == []


def test_an_in_memory_store_is_inspectable_through_its_own_connection(clean):
    """Round 2: reopening ':memory:' yields a different, empty database."""
    store = SqliteStore(":memory:")
    objs = manifest(store._conn)
    assert digest(objs) == clean and drift(objs) == []


def test_two_literal_variants_are_not_the_same_schema():
    """Round 3: collapsing whitespace rewrote quoted literals, so these two —
    which accept exactly opposite values — shared a digest."""
    two = digest(_objs(_variant("object TEXT,", "object TEXT CHECK(object <> 'a  b'),")))
    one = digest(_objs(_variant("object TEXT,", "object TEXT CHECK(object <> 'a b'),")))
    assert two != one


# --- the registry conforms to the product schema -------------------------

def test_the_registry_reproduces_the_product_schema():
    assert registry_conformance(SqliteStore) == []


def test_a_wrong_rebuildable_ddl_fails_conformance(monkeypatch):
    """Round 4: v5 compared the acceptance digest, which excludes exactly these."""
    bad = tuple(o._replace(ddl="CREATE UNIQUE INDEX ix_edges_subj_rel ON edges(user_id)")
                if o.name == "ix_edges_subj_rel" else o for o in SCHEMA_V1)
    monkeypatch.setitem(SCHEMAS, 1, bad)
    assert len(registry_conformance(SqliteStore)) == 1


def test_flipping_only_a_policy_fails_conformance(monkeypatch):
    """Round 5: v6's policy check compared the registry against itself, so this
    passed. A policy decides digest exclusion, drift repair and candidate
    matching — it cannot be self-certifying."""
    flipped = tuple(o._replace(policy=REQUIRED) if o.name == "ix_edges_subj_rel" else o
                    for o in SCHEMA_V1)
    monkeypatch.setitem(SCHEMAS, 1, flipped)
    problems = registry_conformance(SqliteStore)
    assert any("policy" in p for p in problems), problems


def test_the_reviewed_policy_artifact_matches_the_registry():
    assert reviewed_policies(1) == declared_policies(1)


# --- versioning across a simulated schema change -------------------------

@pytest.fixture
def simulated_v2(monkeypatch):
    """A version 2 with its own required table AND its own rebuildable index —
    the combination that exposed round 4's circular resolution."""
    import schema_evidence as ev
    v2 = SCHEMA_V1 + (
        SchemaObject("table", "sources",
                     "CREATE TABLE sources (id TEXT PRIMARY KEY, label TEXT)", REQUIRED),
        SchemaObject("index", "ix_sources",
                     "CREATE INDEX ix_sources ON sources(id)", REBUILDABLE))
    monkeypatch.setitem(SCHEMAS, 2, v2)
    monkeypatch.setitem(MIGRATIONS, 1, Migration(1, 2, (
        "CREATE TABLE sources (id TEXT PRIMARY KEY, label TEXT)",
        "CREATE INDEX ix_sources ON sources(id)")))
    monkeypatch.setattr(ev, "SCHEMA_VERSION", 2)
    monkeypatch.setattr("schema_migrations.SCHEMA_VERSION", 2)
    return ev.build_version_artifact(strict=False)["versions"]


def _built(version: int) -> dict:
    c = sqlite3.connect(":memory:")
    create(c, version)
    return manifest(c)


def test_a_v1_store_still_resolves_once_head_is_v2(simulated_v2):
    assert resolve(_built(1), simulated_v2) == 1
    assert resolve(_built(2), simulated_v2) == 2


def test_resolution_does_not_use_a_default_version_digest(simulated_v2):
    """Round 4: the digest excludes objects by the version's policy, so a
    default-version digest of a v2 store resolves to nothing."""
    v2 = _built(2)
    assert digest(v2, 1) != digest(v2, 2)
    assert not any(a["digest"] == digest(v2, 1) for a in simulated_v2["2"]["accepted"])
    assert resolve(v2, simulated_v2) == 2


def test_the_migration_path_is_generated_not_preserved(simulated_v2):
    """Round 4: v5 preserved whatever JSON was present and called it accepted."""
    prov = [a["provenance"] for a in simulated_v2["2"]["accepted"]]
    assert "migration v1->v2" in prov and "constructor v2" in prov


def test_a_migrated_store_is_accepted_at_its_destination(simulated_v2):
    c = sqlite3.connect(":memory:")
    create(c, 1)
    apply_migration(c, MIGRATIONS[1])
    assert resolve(manifest(c), simulated_v2) == 2


def test_resolution_is_restricted_to_legacy_base_versions(simulated_v2):
    """Round 5: v6 tried every known version, so an unstamped version-2 shape
    resolved to 2 even though only version 1 was ever a legitimate base."""
    assert resolve(_built(2), simulated_v2, candidates=frozenset({1})) is None
    assert resolve(_built(1), simulated_v2, candidates=frozenset({1})) == 1


def test_an_unknown_shape_resolves_to_nothing(simulated_v2):
    assert resolve({("table", "nope"): {"type": "table", "table": "nope",
                                        "sql": "CREATE TABLE nope (x)",
                                        "columns": []}}, simulated_v2) is None


def test_deleting_a_historical_version_is_an_error(simulated_v2, tmp_path, monkeypatch):
    """Round 5: v6 iterated only the versions currently in SCHEMAS, so dropping
    one silently emitted an artifact without it."""
    import json

    import schema_evidence as ev
    art = tmp_path / "schema_versions.json"
    art.write_text(json.dumps({"manifest_algorithm": ev.MANIFEST_ALGORITHM,
                               "schema_version": 2,
                               "versions": simulated_v2}))
    monkeypatch.setattr(ev, "VERSIONS", art)
    monkeypatch.setitem(SCHEMAS, 2, SCHEMAS[2])
    del SCHEMAS[2]
    MIGRATIONS.pop(1, None)
    try:
        with pytest.raises(SystemExit, match="no longer declares it"):
            ev.build_version_artifact(strict=True)
    finally:
        pass


# --- migration containment ------------------------------------------------

def test_a_migration_cannot_reach_the_connection():
    """Round 5: the callback model is withdrawn. A declared statement sequence
    has nothing to escape from — there is no object to reach through."""
    mig = Migration(1, 2, ("CREATE TABLE x (a)",))
    assert all(isinstance(s, str) for s in mig.statements)
    assert not any("conn" in f.lower() for f in Migration._fields)


@pytest.mark.parametrize("stmt", ["COMMIT", "END", "END TRANSACTION", "ROLLBACK",
                                  "SAVEPOINT s", "RELEASE s", "ATTACH ':memory:' AS x"])
def test_transaction_control_in_a_declared_statement_is_denied(stmt):
    conn = sqlite3.connect(":memory:")
    conn.isolation_level = None
    conn.execute("CREATE TABLE t (a)")
    conn.execute("BEGIN IMMEDIATE")
    with pytest.raises(sqlite3.DatabaseError):
        apply_migration(conn, Migration(1, 2, (stmt,)))
    assert conn.in_transaction, f"{stmt} ended the transaction"


def test_the_authorizer_is_restored_after_a_failed_migration():
    conn = sqlite3.connect(":memory:")
    conn.isolation_level = None
    conn.execute("CREATE TABLE t (a)")
    conn.execute("BEGIN IMMEDIATE")
    with pytest.raises(sqlite3.DatabaseError):
        apply_migration(conn, Migration(1, 2, ("COMMIT",)))
    conn.execute("COMMIT")            # the planner's own commit still works
    assert not conn.in_transaction


def test_ordinary_migration_statements_are_allowed():
    conn = sqlite3.connect(":memory:")
    conn.isolation_level = None
    conn.execute("CREATE TABLE t (a)")
    conn.execute("BEGIN IMMEDIATE")
    apply_migration(conn, Migration(1, 2, ("ALTER TABLE t ADD COLUMN b TEXT",
                                           "INSERT INTO t(a) VALUES('x')")))
    assert conn.in_transaction


def test_the_migration_registry_is_well_formed():
    assert validate_registry() == []


# --- runtime qualification ------------------------------------------------

def test_this_runtime_is_qualified_by_evidence():
    """Round 5: v6's WITHDRAWN hand-edited tuple made this trivially false —
    adding '3.99.0' to it
    made an untested runtime supported with nothing behind it."""
    import schema_evidence as ev
    assert ev.runtime_supported()


def test_an_unrecorded_runtime_is_not_qualified(monkeypatch):
    import schema_evidence as ev
    monkeypatch.setattr(ev, "qualified_runtimes", lambda: [])
    assert not ev.runtime_supported()


def test_a_matching_version_with_different_features_is_not_qualified(monkeypatch):
    """A version number names a release, not a build."""
    import schema_evidence as ev
    me = ev.runtime_identity()
    me["features"] = dict(me["features"], authorizer=not me["features"]["authorizer"])
    me["constructor_digests"] = {"1": ev._constructor_digest(1)}
    monkeypatch.setattr(ev, "qualified_runtimes", lambda: [me])
    assert not ev.runtime_supported()
