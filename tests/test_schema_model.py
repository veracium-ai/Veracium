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

import json
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "specs"))

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
    monkeypatch.setattr(ev, "SCHEMA_VERSION", 2)
    monkeypatch.setattr("schema_model.SCHEMA_VERSION", 2)
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
    try:
        with pytest.raises(SystemExit, match="no longer declares it"):
            ev.build_version_artifact(strict=True)
    finally:
        pass


# --- runtime qualification ------------------------------------------------

def test_the_recorded_runtimes_are_internally_valid():
    """**This is the check that must run everywhere.**

    Round 6, finding 3: v7 asserted `runtime_supported()` unconditionally, so the
    whole adversarial suite failed on the reviewer's SQLite 3.46.1 — a runtime
    the document *claimed* was observed but the shipped artifact did not record.
    The package made a false claim and then failed its own test proving it.

    Two questions, separated: is the recorded evidence complete and
    self-consistent (always), and is *this* runner one of the recorded runtimes
    (environment-dependent, below)."""
    import schema_evidence as ev
    records = ev.qualified_runtimes()
    assert records, "no runtime evidence recorded"
    for r in records:
        assert ev.runtime_record_problems(r) == [], (r["sqlite_version"],
                                                     ev.runtime_record_problems(r))


def test_this_runtime_is_qualified_or_explicitly_is_not():
    """Environment-dependent by design, and **skipping is the correct outcome**
    on an unqualified runtime — not a failure of the schema model."""
    import schema_evidence as ev
    if not ev.runtime_supported():
        pytest.skip(
            f"sqlite {sqlite3.sqlite_version} is not a qualified runtime. That is "
            f"the gate working: record it with "
            f"`python3 specs/schema_evidence.py --runtime --write`.")
    assert ev.runtime_supported()


def test_an_unrecorded_runtime_is_not_qualified(monkeypatch):
    import schema_evidence as ev
    monkeypatch.setattr(ev, "qualified_runtimes", lambda: [])
    assert not ev.runtime_supported()


def test_a_matching_version_with_different_features_is_not_qualified(monkeypatch):
    """A version number names a release, not a build."""
    import schema_evidence as ev
    rec = ev.build_runtime_record()
    rec["features"] = dict(rec["features"],
                           strict_tables=not rec["features"]["strict_tables"])
    monkeypatch.setattr(ev, "qualified_runtimes", lambda: [rec])
    assert not ev.runtime_supported()


def test_an_empty_digest_map_does_not_qualify_vacuously(monkeypatch):
    """Round 6, finding 4: `all(...)` over an empty mapping is True, so a record
    with no constructor digests qualified."""
    import schema_evidence as ev
    rec = ev.build_runtime_record()
    rec["constructor_digests"] = {}
    monkeypatch.setattr(ev, "qualified_runtimes", lambda: [rec])
    assert ev.runtime_record_problems(rec)
    assert not ev.runtime_supported()


def test_writing_runtime_evidence_actually_writes(tmp_path, monkeypatch):
    """Round 6, finding 5: `--runtime --write` was documented and ignored."""
    import schema_evidence as ev
    art = tmp_path / "sqlite_runtimes.json"
    monkeypatch.setattr(ev, "RUNTIMES", art)
    monkeypatch.setattr(ev, "GENERATED", tmp_path)
    assert ev.write_runtime() == 0
    assert art.exists() and json.loads(art.read_text())["runtimes"]


def test_missing_legacy_evidence_authorizes_nothing(monkeypatch, tmp_path):
    """Round 6, finding 7: v7 returned {SCHEMA_VERSION}, authorising adoption
    using the very evidence that was missing."""
    import schema_evidence as ev
    monkeypatch.setattr(ev, "RELEASES", tmp_path / "absent.json")
    assert ev.legacy_base_versions() == frozenset()


def test_a_policy_typo_is_a_build_error():
    """Round 7, finding 6: `policy` was an open string, so a typo created a
    third, unchecked behaviour."""
    from schema_model import validate_schema_registry
    bad = SCHEMA_V1 + (SchemaObject("table", "sources",
                                    "CREATE TABLE sources (id TEXT)", "requried"),)
    SCHEMAS[99] = bad
    try:
        problems = validate_schema_registry()
        assert any("policy" in p for p in problems), problems
    finally:
        del SCHEMAS[99]


def test_a_rebuildable_non_index_is_a_build_error():
    from schema_model import validate_schema_registry
    SCHEMAS[99] = (SchemaObject("table", "t", "CREATE TABLE t (a)", REBUILDABLE),)
    try:
        assert any("rebuildable" in p for p in validate_schema_registry())
    finally:
        del SCHEMAS[99]


def test_an_unattested_foreign_runtime_contributes_nothing(monkeypatch):
    """Round 9, finding 1: a record's objects agreeing with its own digest
    proves internal consistency, **not provenance**. Until a job on that runtime
    regenerates it, a foreign record contributes no accepted manifest.

    This replaces an earlier test that asserted the opposite — the union was
    unconditional, which is what let a self-consistent fabrication in."""
    import schema_evidence as ev
    foreign = dict(ev.build_runtime_record())
    foreign["sqlite_version"] = "9.9.9"
    objs = dict(ev._constructor_objects(1))
    key = next(k for k in objs if k.startswith("table:wiki"))
    objs[key] = dict(objs[key], sql=objs[key]["sql"] + " -- other runtime")
    foreign["manifestations"] = {"constructor v1": objs}
    foreign["constructor_digests"] = {"1": ev._digest_of_identity(objs, 1)}
    monkeypatch.setattr(ev, "qualified_runtimes", lambda: [foreign])
    records = ev.build_version_artifact(strict=False)["versions"]
    assert not any("9.9.9" in a["provenance"] for a in records["1"]["accepted"])


def test_a_self_consistent_fabrication_is_rejected():
    """Round 9, finding 1a: v11 checked only that a manifestation hashed to its
    recorded digest, so updating both together passed."""
    import copy

    import schema_evidence as ev
    rec = copy.deepcopy(ev.build_runtime_record())
    objs = dict(rec["manifestations"]["constructor v1"])
    objs["trigger:evil"] = {
        "type": "trigger", "table": "edges",
        "sql": "CREATE TRIGGER evil AFTER INSERT ON edges BEGIN DELETE FROM edges; END"}
    rec["manifestations"]["constructor v1"] = objs
    rec["constructor_digests"]["1"] = ev._digest_of_identity(objs, 1)
    problems = ev.runtime_record_problems(rec)
    assert any("undeclared object" in p for p in problems), problems


def test_conflicting_runtime_identities_reject_the_artifact():
    """Round 9, finding 1b: two individually valid records with the same
    identity and different output both passed. One build cannot produce two."""
    import copy

    import schema_evidence as ev
    good = copy.deepcopy(ev.build_runtime_record())
    other = copy.deepcopy(good)
    other["constructor_digests"] = {"1": "0" * 64}
    assert ev.artifact_problems([good, other])


def test_a_duplicate_runtime_record_is_rejected():
    import copy

    import schema_evidence as ev
    rec = ev.build_runtime_record()
    assert ev.artifact_problems([copy.deepcopy(rec), copy.deepcopy(rec)])


def test_the_release_result_is_rederived():
    """Round 7, finding 7: the gate inspected the stored value."""
    import schema_evidence as ev
    assert "result" in ev.AUTHORITATIVE


def test_the_strict_table_probe_uses_valid_sql():
    """Round 7, finding 5: the probe was invalid SQL and recorded False on a
    runtime that supports strict tables."""
    import schema_evidence as ev
    assert ev.runtime_identity()["features"]["strict_tables"] is True


def test_the_ddl_probe_asserts_body_preservation():
    """And this one only checked that a row existed."""
    import schema_evidence as ev
    f = ev.runtime_identity()["features"]
    assert f["preserves_ddl_body"] is True and f["xinfo_exposes_generated"] is True


# --- round 8: runtime-record validation ----------------------------------

def _valid_record():
    import schema_evidence as ev
    return ev.build_runtime_record()


def test_a_fabricated_manifestation_is_rejected():
    """Round 8, finding 2 — a demonstrated bypass. An added trigger became an
    accepted version-1 shape while the validator returned no problems."""
    import copy

    import schema_evidence as ev
    rec = copy.deepcopy(_valid_record())
    objs = dict(rec["manifestations"]["constructor v1"])
    objs["trigger:evil"] = {
        "type": "trigger", "table": "edges",
        "sql": "CREATE TRIGGER evil AFTER INSERT ON edges BEGIN DELETE FROM edges; END"}
    rec["manifestations"]["constructor v1"] = objs
    assert ev.runtime_record_problems(rec)


def test_a_record_without_manifestations_is_rejected():
    import copy

    import schema_evidence as ev
    rec = copy.deepcopy(_valid_record())
    del rec["manifestations"]
    assert ev.runtime_record_problems(rec)


def test_an_extra_manifestation_is_rejected():
    import copy

    import schema_evidence as ev
    rec = copy.deepcopy(_valid_record())
    rec["manifestations"]["constructor v9"] = {}
    assert ev.runtime_record_problems(rec)


def test_an_invalid_record_beside_a_valid_one_contributes_nothing(monkeypatch):
    """`build_version_artifact()` imported manifestations from every record
    without first validating it."""
    import copy

    import schema_evidence as ev
    good = copy.deepcopy(_valid_record())
    bad = copy.deepcopy(good)
    bad["sqlite_version"] = "9.9.9"
    objs = dict(bad["manifestations"]["constructor v1"])
    objs["table:sneaky"] = {"type": "table", "table": "sneaky",
                            "sql": "CREATE TABLE sneaky (x)", "columns": []}
    bad["manifestations"]["constructor v1"] = objs
    monkeypatch.setattr(ev, "qualified_runtimes", lambda: [good, bad])
    sneaky = ev._digest_of_identity(objs, 1)
    records = ev.build_version_artifact(strict=False)["versions"]
    assert not any(a["digest"] == sneaky for a in records["1"]["accepted"])


def test_the_capability_validator_is_not_in_the_0007_kernel():
    """Round 8, finding 4: it is a migration destination validator with no
    caller here. `specs/0013` owns it."""
    import schema_model
    assert not hasattr(schema_model, "capability_problems")


# --- round 10: publication and artifact-level checks ----------------------

def _isolate(monkeypatch, tmp_path):
    """Point the evidence artifacts at a scratch directory."""
    import schema_evidence as ev
    monkeypatch.setattr(ev, "GENERATED", tmp_path)
    monkeypatch.setattr(ev, "RUNTIMES", tmp_path / "sqlite_runtimes.json")
    monkeypatch.setattr(ev, "VERSIONS", tmp_path / "schema_versions.json")
    return ev


def test_a_conflicting_artifact_disqualifies_the_runtime(monkeypatch):
    """Round 10, finding 1: `build_version_artifact()` caught the conflict but
    the production-facing predicate did not — and that is where it matters."""
    import copy

    import schema_evidence as ev
    good = ev.build_runtime_record()
    other = copy.deepcopy(good)
    other["constructor_digests"] = {"1": "0" * 64}
    monkeypatch.setattr(ev, "qualified_runtimes", lambda: [good, other])
    assert not ev.runtime_supported()


def test_the_recorded_artifact_has_no_conflicts():
    """The always-running check, asserted at artifact level rather than
    record by record."""
    import schema_evidence as ev
    assert ev.artifact_problems(ev.qualified_runtimes()) == []


def test_two_active_runtime_identities_are_refused():
    """Round 10, finding 2: `0007` supports exactly one active runtime. The
    cross-runtime union was described but could not be constructed."""
    import copy

    import schema_evidence as ev
    a = ev.build_runtime_record()
    b = copy.deepcopy(a)
    b["sqlite_version"] = "9.9.9"
    assert any("exactly one" in p for p in ev.artifact_problems([a, b]))


def test_a_staging_failure_publishes_nothing(monkeypatch, tmp_path):
    """Round 10: the rollback path had no test at all."""
    import json

    ev = _isolate(monkeypatch, tmp_path)
    ev.RUNTIMES.write_text(json.dumps({"runtimes": []}, indent=2) + "\n")
    real = Path.write_text

    def boom(self, *a, **k):
        if self.name.startswith("schema_versions"):
            raise OSError("simulated disk failure")
        return real(self, *a, **k)

    monkeypatch.setattr(Path, "write_text", boom)
    assert ev.write_runtime() == 1
    assert json.loads(ev.RUNTIMES.read_text())["runtimes"] == []


def test_a_failed_publish_rolls_the_first_file_back(monkeypatch, tmp_path):
    import json

    ev = _isolate(monkeypatch, tmp_path)
    ev.RUNTIMES.write_text(json.dumps({"runtimes": []}, indent=2) + "\n")
    real = Path.replace

    def boom(self, target):
        if Path(target).name.startswith("schema_versions"):
            raise OSError("simulated rename failure")
        return real(self, target)

    monkeypatch.setattr(Path, "replace", boom)
    assert ev.write_runtime() == 1
    assert json.loads(ev.RUNTIMES.read_text())["runtimes"] == []


def test_staged_temporaries_are_not_left_behind(monkeypatch, tmp_path):
    """v12 left `sqlite_runtimes.json.tmp` behind and it shipped in the review
    package."""
    ev = _isolate(monkeypatch, tmp_path)
    assert ev.write_runtime() == 0
    assert not list(tmp_path.glob("*.tmp")), list(tmp_path.glob("*.tmp"))


def test_the_repository_has_no_stray_staged_artifacts():
    assert not list((ROOT / "specs" / "generated").glob("*.tmp"))


# --- round 11 ------------------------------------------------------------

def test_one_canonical_identity_is_used_everywhere(monkeypatch):
    """Round 11, finding 1: three keys were in use — five fields for
    attestation, `version + source_id` for the one-active check and for
    replacement. Two records agreeing on version and source id but disagreeing
    on probes passed everything."""
    import copy

    import schema_evidence as ev
    a = ev.build_runtime_record()
    b = copy.deepcopy(a)
    b["features"] = dict(b["features"],
                         strict_tables=not b["features"]["strict_tables"])
    assert ev._identity_key(a) != ev._identity_key(b)
    assert any("one build cannot have two" in p for p in ev.artifact_problems([a, b]))
    monkeypatch.setattr(ev, "qualified_runtimes", lambda: [a, b])
    assert not ev.runtime_supported()


def test_a_modified_rebuildable_ddl_disqualifies_the_runtime(monkeypatch):
    """Round 11, finding 2: the acceptance digest excludes rebuildable indexes,
    so a record claiming a UNIQUE index on the same name reproduced its digest
    exactly — while describing an index that changes which writes succeed."""
    import copy

    import schema_evidence as ev
    rec = copy.deepcopy(ev.build_runtime_record())
    objs = dict(rec["manifestations"]["constructor v1"])
    key = "index:ix_edges_subj_rel"
    objs[key] = dict(objs[key],
                     sql="CREATE UNIQUE INDEX ix_edges_subj_rel ON edges(user_id)")
    rec["manifestations"]["constructor v1"] = objs
    assert ev._digest_of_identity(objs, 1) == rec["constructor_digests"]["1"]
    monkeypatch.setattr(ev, "qualified_runtimes", lambda: [rec])
    assert not ev.runtime_supported()


def test_a_missing_rebuildable_index_disqualifies_the_runtime(monkeypatch):
    import copy

    import schema_evidence as ev
    rec = copy.deepcopy(ev.build_runtime_record())
    del rec["manifestations"]["constructor v1"]["index:ix_edges_subj_rel"]
    monkeypatch.setattr(ev, "qualified_runtimes", lambda: [rec])
    assert not ev.runtime_supported()


def test_schema_version_must_match_the_registry():
    """Round 11, finding 3 — a regression from the scope cut. The guard lived in
    the deleted migrations module, and the round-6 disposition still claimed
    S53 enforced it."""
    from schema_model import validate_schema_registry
    SCHEMAS[2] = SCHEMA_V1
    try:
        problems = validate_schema_registry()
        assert any("SCHEMA_VERSION" in p for p in problems), problems
    finally:
        del SCHEMAS[2]


def test_the_registry_versions_are_contiguous():
    from schema_model import validate_schema_registry
    SCHEMAS[3] = SCHEMA_V1
    try:
        assert validate_schema_registry()
    finally:
        del SCHEMAS[3]


def test_a_missing_versions_artifact_fails_the_gate(monkeypatch, tmp_path):
    """Round 11 correction: `--check` compared the file only when it existed.

    **Skips outside a git checkout.** `check()` returns 2 there — the documented
    "release probing needs git" status — before it can reach the missing-file
    condition. Asserting 1 unconditionally made this pass in the repo and fail
    in the extracted review package, which is the environment-dependence class
    round 10 objected to."""
    import subprocess

    import schema_evidence as ev
    if subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT,
                      capture_output=True).returncode:
        pytest.skip("no git checkout: check() returns 2 before reaching this")
    monkeypatch.setattr(ev, "VERSIONS", tmp_path / "absent.json")
    monkeypatch.setattr(ev, "_tags", lambda: [])
    monkeypatch.setattr(ev, "_probe_at",
                        lambda ref, work: {"tag": ref, "commit": "x",
                                           "on_disk_user_version": 0,
                                           "store_schema_version": 1,
                                           "digest": None, "result": "ok",
                                           "_objects": {}})
    assert ev.check() == 1
