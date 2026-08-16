"""The operator-facing `veracium migrate` verb — the 0018 §4g contract.

Re-dispositioned under specs/0018 (§7a) FROM the ce896fc direct-`migrate_store`
contract TO the release-migration orchestrator: `--i-have-quiesced` +
`--backup REF` (flags, never prompts), exits 0/1/2/3, structured-field
reporting only, and the exit-3 loud-escape stderr forms — every printed state
labeled recorded, derived, or unavailable. Orchestrator behaviour itself is
tested in test_0018_orchestrator.py; these tests cover only what the CLI
adds: flag acquisition, exit codes, and the report/stderr forms.
"""

import sqlite3
import tempfile

import pytest

import veracium.store.release_migration as rm
import veracium.store.schema_version as sv
from veracium.cli import main
from veracium.store.schema_version import PackageConsistencyError
from veracium.store.sqlite import SqliteStore

HEAD = sv.SCHEMA_VERSION
MINT_BASE = HEAD - 1
FLAGS = ["--i-have-quiesced", "--backup", "backup-1"]


def _tmp() -> str:
    return tempfile.mktemp(suffix=".db")


def _user_version(path: str) -> int:
    c = sqlite3.connect(path)
    try:
        return c.execute("PRAGMA user_version").fetchone()[0]
    finally:
        c.close()


def _store_at(version: int) -> str:
    p = _tmp()
    c = sqlite3.connect(p)
    for o in sv.SCHEMAS[version]:
        c.execute(o.ddl)
    c.execute(f"PRAGMA user_version = {version}")
    c.commit()
    c.close()
    return p


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


# --- flag acquisition: exit 2 ----------------------------------------------

def test_missing_flags_exit_2_with_usage(capsys):
    p = _store_at(MINT_BASE)
    for argv in (["migrate", "--db", p],
                 ["migrate", "--db", p, "--i-have-quiesced"],
                 ["migrate", "--db", p, "--backup", "b1"]):
        rc = main(argv)
        err = capsys.readouterr().err
        assert rc == 2
        assert "--i-have-quiesced" in err and "--backup" in err
    assert _user_version(p) == MINT_BASE          # untouched


def test_invalid_backup_token_exit_2_with_the_grammar(capsys):
    p = _store_at(MINT_BASE)
    rc = main(["migrate", "--db", p, "--i-have-quiesced", "--backup", "a b"])
    err = capsys.readouterr().err
    assert rc == 2
    assert "invalid --backup token" in err
    assert "[A-Za-z0-9]" in err                    # the grammar is STATED
    assert _user_version(p) == MINT_BASE


# --- exit 0: migrated / current --------------------------------------------

def test_migrate_verb_migrates_a_v7_store(capsys):
    p = _store_at(MINT_BASE)
    rc = main(["migrate", "--db", p] + FLAGS)
    out = capsys.readouterr().out
    assert rc == 0
    assert _user_version(p) == HEAD
    # structured fields, never words inferred from the label (0013 r8-f3)
    assert "outcome: migrated" in out
    assert "store_changed: True" in out
    assert "transaction_committed: True" in out
    assert f"resulting_version: {HEAD}" in out
    assert "resulting_state: destination" in out


def test_migrate_verb_reports_a_current_store_as_a_no_op(capsys):
    p = _tmp()
    SqliteStore(p).close()
    rc = main(["migrate", "--db", p] + FLAGS)
    out = capsys.readouterr().out
    assert rc == 0
    assert _user_version(p) == HEAD
    assert "outcome: current" in out
    assert "store_changed: False" in out


# --- exit 1: every refusal outcome -----------------------------------------

def test_below_v7_store_exits_1_with_the_ladder(capsys):
    p = _legacy_v1_store(rows=5)
    rc = main(["migrate", "--db", p] + FLAGS)
    out = capsys.readouterr().out
    assert rc == 1
    assert "outcome: unsupported-base" in out
    assert "resulting_version: 1" in out
    assert "migrate to v6 on a ≤0.8.x release" in out
    assert _user_version(p) == 0                   # unstamped, untouched
    c = sqlite3.connect(p)
    assert c.execute("SELECT COUNT(*) FROM edges").fetchone()[0] == 5
    c.close()


def test_missing_store_exits_1_as_the_missing_refusal(capsys):
    rc = main(["migrate", "--db", _tmp()] + FLAGS)  # path never created
    out = capsys.readouterr().out
    assert rc == 1
    assert "outcome: migration-source-missing" in out
    assert "resulting_state: missing" in out


def test_newer_store_exits_1(capsys):
    p = _store_at(HEAD)
    c = sqlite3.connect(p)
    c.execute(f"PRAGMA user_version = {HEAD + 1}")
    c.commit()
    c.close()
    rc = main(["migrate", "--db", p] + FLAGS)
    out = capsys.readouterr().out
    assert rc == 1
    assert "outcome: newer" in out
    assert _user_version(p) == HEAD + 1            # untouched


def test_mint_contention_exits_1(capsys, monkeypatch):
    p = _store_at(MINT_BASE)

    def failing_mint(path, attestation, *, resolved):
        raise rm.MintError("source-changed", "forced")
    monkeypatch.setattr(rm, "mint_release_authority", failing_mint)
    rc = main(["migrate", "--db", p] + FLAGS)
    out = capsys.readouterr().out
    assert rc == 1
    assert "outcome: mint-contention" in out
    assert "resulting_state: unknown" in out


# --- exit 3: the loud-escape class ------------------------------------------

def test_audit_write_error_exits_3_with_its_carried_facts(capsys, monkeypatch):
    p = _store_at(MINT_BASE)
    monkeypatch.setattr(rm, "_write_terminal",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    rc = main(["migrate", "--db", p] + FLAGS)
    err = capsys.readouterr().err
    assert rc == 3
    assert "MigrationAuditWriteError" in err
    assert "resulting_state: destination (recorded)" in err
    assert "transaction_committed: True" in err
    assert _user_version(p) == HEAD                # migrated — reported, not hidden


def test_audit_read_error_exits_3_with_the_derived_state(capsys, monkeypatch):
    p = _store_at(MINT_BASE)
    monkeypatch.setattr(rm, "_write_terminal", lambda *a, **k: None)
    rc = main(["migrate", "--db", p] + FLAGS)
    err = capsys.readouterr().err
    assert rc == 3
    assert "MigrationAuditReadError" in err
    assert "resulting_state: destination (derived-from-outcome)" in err


# the five package routes (I19, closure obligation 4), each with its exact
# stderr form: pre-mint · bound package-inconsistent (recorded facts) ·
# mismatched · missing · malformed

def _package_exc(route=None, facts=None):
    e = PackageConsistencyError("forced package break")
    if route is not None:
        e.readback_route = route
        e.recorded_facts = facts
    return e


@pytest.mark.parametrize("route,facts,expected", [
    (None, None,
     "resulting_state: unavailable (pre-mint: no operation minted)"),
    ("recorded",
     rm.TerminalFacts("package-inconsistent", MINT_BASE, HEAD, None, None,
                      "unknown", None),
     "resulting_state: unknown (recorded)"),
    ("mismatched", None, "resulting_state: unavailable (readback: mismatched)"),
    ("missing", None, "resulting_state: unavailable (readback: missing)"),
    ("malformed", None, "resulting_state: unavailable (readback: malformed)"),
], ids=["pre-mint", "recorded", "mismatched", "missing", "malformed"])
def test_package_escape_routes_exit_3(capsys, monkeypatch, route, facts,
                                      expected):
    p = _store_at(MINT_BASE)

    def raising(path, *, host_attestation):
        raise _package_exc(route, facts)
    monkeypatch.setattr(rm, "run_release_migration", raising)
    rc = main(["migrate", "--db", p] + FLAGS)
    err = capsys.readouterr().err
    assert rc == 3
    assert "PackageConsistencyError" in err
    assert expected in err
    if route == "recorded":
        assert "transaction_committed: None" in err    # the recorded facts


def test_package_escape_end_to_end_recorded_route(capsys, monkeypatch):
    """The REAL post-mint escape path: the kernel escapes after minting; the
    orchestrator terminal-records `package-inconsistent`, the escape-path
    readback binds it, and the CLI prints the RECORDED facts at exit 3."""
    import veracium.store.migration as mig
    p = _store_at(MINT_BASE)

    def kernel_boom(path, **kw):
        raise PackageConsistencyError("post-mint break")
    monkeypatch.setattr(mig, "migrate_store", kernel_boom)
    rc = main(["migrate", "--db", p] + FLAGS)
    err = capsys.readouterr().err
    assert rc == 3
    assert "resulting_state: unknown (recorded)" in err
    assert _user_version(p) == MINT_BASE           # the kernel never ran
