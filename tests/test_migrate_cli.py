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


@pytest.fixture(autouse=True)
def _mktemp_under_tmp_path(tmp_path):
    """Every `tempfile` name this module mints lands under the test's own
    `tmp_path`, which pytest removes.

    2026-09-16: `tempfile.mktemp(suffix=".db")` at 1 site in this file wrote
    into the system temp directory and deleted nothing. Across the suite that was
    413 stray stores per run and 53,230 in /tmp over three days (4 GB), measured
    before the clean-up. The call sites sit inside module helpers as well as
    tests, so redirecting `tempfile` for the module fixes both without changing a
    single signature or assertion — the shape the doctor-CLI test already uses to
    own its own temp root.

    Set and restored DIRECTLY rather than through `monkeypatch`. A test that calls
    `monkeypatch.undo()` mid-body undoes every patch on that fixture, including one
    another fixture installed, so the `monkeypatch.setattr(tempfile, "tempdir", …)`
    version of this redirect was silently lifted for the rest of those tests and
    three stores per run still escaped. Measured across the seven files: 27+ before,
    3 with the monkeypatch form, 0 with this one. Two of the seven call `undo()`
    mid-body — `tests/test_0018_orchestrator.py` (three times inside one test) and
    `tests/test_migrations_0013.py` — so this is a live hazard here, not a
    precaution. Do not simplify it back to `monkeypatch`.
    """
    previous = tempfile.tempdir
    tempfile.tempdir = str(tmp_path)
    try:
        yield
    finally:
        tempfile.tempdir = previous

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
    assert f"rung v{MINT_BASE} -> v{HEAD}: migrated (operation op-" in out
    assert "rungs committed by this walk: 1 (op-" in out
    # the store's own state at the end, from structured fields, never words inferred from the label (0013 r8-f3)
    assert "outcome: current" in out
    assert f"resulting_version: {HEAD}" in out
    assert "action: done" in out and f"store version: v{HEAD}" in out


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

def test_an_unstamped_v1_store_walks_every_rung(capsys):
    """I34: fifteen rungs, each its own operation, under one command."""
    p = _legacy_v1_store(rows=5)
    rc = main(["migrate", "--db", p] + FLAGS)
    out = capsys.readouterr().out
    assert rc == 0
    assert out.count(" -> v") == HEAD - 1 and f"rungs committed by this walk: {HEAD - 1} (" in out
    assert len({line.split("operation ")[1] for line in out.splitlines() if line.startswith("rung v")}) == HEAD - 1
    assert _user_version(p) == HEAD
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
    e.rung_context = None
    if route is not None:
        e.readback_route = route
        e.recorded_facts = facts
        e.rung_context = ("op-escape", MINT_BASE, HEAD)
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

    def raising(path, *, host_attestation, expect_base=None):
        raise _package_exc(route, facts)
    monkeypatch.setattr(rm, "run_release_rung", raising)
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
    import veracium.store.release_migration as rm
    p = _store_at(MINT_BASE)

    def kernel_boom(*a, **kw):
        raise PackageConsistencyError("post-mint break")
    monkeypatch.setattr(rm, "_run_rung", kernel_boom)
    rc = main(["migrate", "--db", p] + FLAGS)
    err = capsys.readouterr().err
    assert rc == 3
    assert "resulting_state: unknown (recorded)" in err
    assert _user_version(p) == MINT_BASE           # the kernel never ran


# --- the walk (0018 §4j.6.4g, I34, I35) --------------------------------------

def _walk(monkeypatch, on_call):
    """Wrap the real rung. `on_call(n, real)` gets the 1-based call number and a zero-argument real call; what it returns is the report."""
    real, calls = rm.run_release_rung, []

    def wrapped(path, *, host_attestation, expect_base=None):
        calls.append((host_attestation, expect_base))
        return on_call(len(calls), lambda: real(path, host_attestation=host_attestation, expect_base=expect_base))
    monkeypatch.setattr(rm, "run_release_rung", wrapped)
    return calls


OP_OTHER = "op-1b4e28ba-2fa1-41d2-883f-0016d3cca427"
OP_TWO = "op-6ba7b810-9dad-41d1-80b4-00c04fd430c8"


def _delegated(op, b, t, outcome, changed, state, version):
    return rm.RungReport("delegated", rm.MigrationResult(outcome, changed, changed, state, version, "injected"), b, b, op, b, t, b)


def _ids_line(text):
    return next(line for line in text.splitlines() if line.startswith("rungs committed by this walk: "))


def test_a_v13_store_walks_three_rungs_with_three_ids_and_three_records(capsys):
    p = _store_at(13)
    assert main(["migrate", "--db", p] + FLAGS) == 0
    out = capsys.readouterr().out
    ids = [line.split("operation ")[1].rstrip(")") for line in out.splitlines() if line.startswith("rung v")]
    assert len(ids) == len(set(ids)) == 3 and "rungs committed by this walk: 3 (" + ", ".join(ids) + ")" in out
    apath = rm.audit_trail_path(p)
    assert [rm.read_terminal(i, audit_path=apath).kind for i in ids] == ["record"] * 3


def test_a_store_at_head_makes_no_rung(capsys):
    p = _store_at(HEAD)
    assert main(["migrate", "--db", p] + FLAGS) == 0
    out = capsys.readouterr().out
    assert "rung v" not in out and "rungs committed by this walk: 0 (none)" in out


def test_one_attestation_object_is_admitted_at_every_call(monkeypatch):
    calls = _walk(monkeypatch, lambda n, real: real())
    assert main(["migrate", "--db", _store_at(13)] + FLAGS) == 0
    assert len(calls) == 4 and len({id(a) for a, _ in calls}) == 1
    assert [e for _, e in calls] == [None, 14, 15, 16]


def test_a_store_moved_down_between_rungs_stops_before_a_second_mint(capsys, monkeypatch):
    p = _store_at(13)
    mints = []
    mint = rm.mint_release_authority
    monkeypatch.setattr(rm, "mint_release_authority", lambda *a, **k: (mints.append(1), mint(*a, **k))[1])

    def on_call(n, real):
        if n == 2:
            q = _store_at(13)
            with open(q, "rb") as src, open(p, "wb") as dst:
                dst.write(src.read())
        return real()
    _walk(monkeypatch, on_call)
    assert main(["migrate", "--db", p] + FLAGS) == 1
    out = capsys.readouterr().out
    assert "outcome: unexpected-base: observed v13 where v14 was expected" in out
    assert "action: rerun-when-quiescent" in out and "rungs committed by this walk: 1 (" in out and len(mints) == 1


def test_an_unchanged_current_at_the_target_continues_and_is_not_counted(capsys, monkeypatch):
    p = _store_at(MINT_BASE)

    def on_call(n, real):
        if n == 1:
            real()                                 # another operation reached the target, so this report is unchanged
            return _delegated(OP_OTHER, MINT_BASE, HEAD, "current", False, "destination", HEAD)
        return real()
    _walk(monkeypatch, on_call)
    assert main(["migrate", "--db", p] + FLAGS) == 0
    out = capsys.readouterr().out
    assert f"rung v{MINT_BASE} -> v{HEAD}: current (operation {OP_OTHER})" in out
    assert "rungs committed by this walk: 0 (none)" in out


def test_a_pre_mint_escape_after_two_rungs_reuses_no_earlier_id(capsys, monkeypatch):
    def on_call(n, real):
        if n == 3:
            raise _package_exc()
        return real()
    _walk(monkeypatch, on_call)
    assert main(["migrate", "--db", _store_at(13)] + FLAGS) == 3
    err = capsys.readouterr().err
    assert "unavailable (pre-mint: no operation minted)" in err and "operation_id" not in err
    assert "rungs committed by this walk: 2 (" in err and "action: repair-build" in err


def test_a_committed_error_is_counted_once_and_stops_the_walk(capsys, monkeypatch):
    """I34, R2-01: counting comes before the continuation decision, so a committed error is in the count and is not a success. A
    committed `package-inconsistent` reaches the walk only through E4, whose cells are below: no delegated result carries it."""
    outcome = "internal-error"
    def on_call(n, real):
        if n == 2:
            return _delegated(OP_TWO, 14, 15, outcome, True, "destination", 15)
        return real()
    calls = _walk(monkeypatch, on_call)
    assert main(["migrate", "--db", _store_at(13)] + FLAGS) == 1
    out = capsys.readouterr().out
    assert len(calls) == 2 and "action: stop-inspect-committed" in out
    line = _ids_line(out)
    assert line.startswith("rungs committed by this walk: 2 (") and line.count(OP_TWO) == 1
    assert f"store version: v15, recorded: committed with {outcome}" in out


def test_a_write_error_with_committed_facts_is_counted_once(capsys, monkeypatch):
    monkeypatch.setattr(rm, "_write_terminal", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    assert main(["migrate", "--db", _store_at(MINT_BASE)] + FLAGS) == 3
    err = capsys.readouterr().err
    assert "rungs committed by this walk: 1 (op-" in err and "action: rerun-resumes-store" in err
    assert "action: audit-record-not-published" in err and f"store version: v{HEAD}" in err


@pytest.mark.parametrize("facts, counted, shown", [
    (rm.TerminalFacts("package-inconsistent", MINT_BASE, HEAD, True, True, "destination", HEAD), 1, f"store version: v{HEAD}, recorded"),
    (rm.TerminalFacts("package-inconsistent", MINT_BASE, HEAD, False, False, "source", MINT_BASE), 0, f"store version: v{MINT_BASE}, recorded"),
    (rm.TerminalFacts("package-inconsistent", 13, 14, True, True, "destination", 14), 0, "store version: unavailable (readback: mismatched)"),
    (rm.TerminalFacts("migrated", MINT_BASE, HEAD, True, True, "destination", HEAD), 0, "store version: unavailable (readback: mismatched)"),
], ids=["bound committed", "bound unchanged", "another rung", "another outcome"])
def test_a_post_mint_package_escape_counts_only_a_bound_committed_readback(capsys, monkeypatch, facts, counted, shown):
    def raising(path, *, host_attestation, expect_base=None):
        raise _package_exc("recorded", facts)
    monkeypatch.setattr(rm, "run_release_rung", raising)
    assert main(["migrate", "--db", _store_at(MINT_BASE)] + FLAGS) == 3
    err = capsys.readouterr().err
    assert f"rungs committed by this walk: {counted} (" in err and shown in err


def test_unknown_facts_print_unknown_never_the_previous_rungs_version(capsys, monkeypatch):
    def on_call(n, real):
        if n == 2:
            return _delegated(OP_TWO, 14, 15, "internal-error", None, "unknown", None)
        return real()
    _walk(monkeypatch, on_call)
    assert main(["migrate", "--db", _store_at(13)] + FLAGS) == 1
    out = capsys.readouterr().out
    assert "store version: unknown" in out and "action: stop-inspect-unknown" in out
    assert "rungs committed by this walk: 1 (" in out


def test_a_read_error_prints_its_state_as_a_state_and_the_version_as_unknown(capsys, monkeypatch):
    monkeypatch.setattr(rm, "_write_terminal", lambda *a, **k: None)
    assert main(["migrate", "--db", _store_at(MINT_BASE)] + FLAGS) == 3
    err = capsys.readouterr().err
    assert "store version: unknown" in err and "action: inspect-audit-trail" in err
    assert "rungs committed by this walk: 0 (none)" in err and f"may be at v{HEAD} regardless" in err


def test_state_unknown_says_query_the_id_before_any_rerun(capsys, monkeypatch):
    def on_call(n, real):
        return rm.RungReport("delegated", rm.MigrationResult("migration-audit-state-unknown", False, False, "unknown", None, "injected"),
                             13, 13, OP_TWO, 13, 14, None)
    _walk(monkeypatch, on_call)
    assert main(["migrate", "--db", _store_at(13)] + FLAGS) == 1
    out = capsys.readouterr().out
    assert "action: query-id-first" in out and "rerun: NO" in out and "store version: unknown" in out


def test_a_postcondition_failure_at_rung_two_leaves_rung_one_whole_and_a_repaired_build_resumes(capsys, monkeypatch):
    """I35 (iv): the walk stops at v14, stamped and accepted, with rung 1's record intact and rung 2 unchanged; with the fault gone,
    a rerun walks on. The fault is one postcondition, at one target."""
    import veracium.store.migration as mig
    p = _store_at(13)
    real = mig._check_stamp

    def faulty(conn, run):
        if run.target == 15:
            mig._refuse_unless(run, mig.STEP_STAMP, ["injected"])
        real(conn, run)
    monkeypatch.setattr(mig, "_check_stamp", faulty)
    assert main(["migrate", "--db", p] + FLAGS) == 1
    out = capsys.readouterr().out
    assert "outcome: unsupported-migration" in out and "action: no-rerun-this-build" in out
    assert "rungs committed by this walk: 1 (" in out and "rung v13 -> v14: migrated" in out
    assert _user_version(p) == 14
    monkeypatch.setattr(mig, "_check_stamp", real)
    assert main(["migrate", "--db", p] + FLAGS) == 0
    out = capsys.readouterr().out
    assert "rung v14 -> v15: migrated" in out and "rung v15 -> v16: migrated" in out and _user_version(p) == HEAD
