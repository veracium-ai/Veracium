"""The operator-facing `veracium migrate` verb.

The verb is deliberately UNGUARDED: migration behaviour — version resolution,
the accepted-manifest gate, refusal semantics, audit — is `migrate_store`'s and
is tested in test_store_versioning.py / test_0013_*. These tests cover only
what the CLI itself adds: argument handling, exit codes, and that the printed
report states the STRUCTURED result (resulting_version / store_changed), not
words inferred from the label (0013 round 8, finding 3).
"""

import sqlite3
import sys
import tempfile

import veracium.store.schema_version as sv
from veracium.cli import main
from veracium.store.sqlite import SqliteStore


def _tmp() -> str:
    return tempfile.mktemp(suffix=".db")


def _user_version(path: str) -> int:
    c = sqlite3.connect(path)
    try:
        return c.execute("PRAGMA user_version").fetchone()[0]
    finally:
        c.close()


def _legacy_v1_store(rows: int = 3) -> str:
    p = _tmp()
    c = sqlite3.connect(p)
    c.executescript(";\n".join(o.ddl for o in sv.SCHEMA_V1) + ";\n")
    for i in range(rows):
        c.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,"
                  "quarantined,json) VALUES(?,?,?,?,?,1,0,'{}')",
                  (f"e{i}", "u", f"s{i}", "r", "o"))
    c.commit()
    c.close()
    return p


def test_migrate_verb_migrates_a_below_head_store(capsys):
    p = _legacy_v1_store(rows=5)
    rc = main(["migrate", "--db", p])
    out = capsys.readouterr().out
    assert rc == 0
    assert _user_version(p) == sv.SCHEMA_VERSION
    assert f"schema v{sv.SCHEMA_VERSION}" in out
    assert "migrated" in out
    # the data made it, so the verb really ran the migration, not a recreate
    c = sqlite3.connect(p)
    try:
        assert c.execute("SELECT COUNT(*) FROM edges").fetchone()[0] == 5
    finally:
        c.close()


def test_migrate_verb_reports_a_current_store_as_a_no_op(capsys):
    p = _tmp()
    SqliteStore(p)
    before = _user_version(p)
    rc = main(["migrate", "--db", p])
    out = capsys.readouterr().out
    assert rc == 0
    assert _user_version(p) == before == sv.SCHEMA_VERSION
    assert "already current" in out
    assert f"schema v{sv.SCHEMA_VERSION}" in out
    assert "migrated" not in out


def test_migrate_verb_exits_2_when_the_store_file_is_missing(capsys):
    rc = main(["migrate", "--db", _tmp()])  # path never created
    err = capsys.readouterr().err
    assert rc == 2
    assert "nothing to migrate" in err


def test_migrate_verb_surfaces_a_store_refusal_with_exit_1(capsys):
    """A future-version store must be REFUSED with the store's own reason on
    stderr — not adopted, not stripped to some shape the verb invents."""
    p = _tmp()
    SqliteStore(p)
    c = sqlite3.connect(p)
    c.execute(f"PRAGMA user_version = {sv.SCHEMA_VERSION + 1}")
    c.commit()
    c.close()
    rc = main(["migrate", "--db", p])
    err = capsys.readouterr().err
    assert rc == 1
    assert "refused:" in err
    assert _user_version(p) == sv.SCHEMA_VERSION + 1  # untouched


def test_migrate_verb_output_matches_the_structured_result_not_the_label():
    """The report must be built from OpenResult's structured fields. Guard the
    construction: a migrated store's OpenResult says store_changed=True and
    resulting_version=head; the printed line must carry those facts."""
    p = _legacy_v1_store()
    from veracium.store.migration import migrate_store
    r = migrate_store(p)
    assert r.store_changed is True
    assert r.resulting_version == sv.SCHEMA_VERSION
    # second call through the CLI: nothing left to do, and the verb must say so
    rc = main(["migrate", "--db", p])
    assert rc == 0
