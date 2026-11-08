"""0018 adjacent rungs, external round 5's closures: R5-01 (with research's S1 and S2), at the first, a middle and the last rung.

R5-01: a writer's failure proves the record absent ONLY in the window where control flow proves it: the trail was read, append-once
found no record of this kind for this id, and the failure came before os.replace. Everything else is unresolved: N2 with the id at the
attempted sink; one recovery read_terminal at the terminal sink (an equal record True, a successful read with no record False, anything
else None). S2: absence is an lstat ENOENT, never os.path.exists's False, which any stat error also returns, at all four sites
0018 owns (the two trail readers, the mint, preflight). R5-02's closure is in tests/test_0018_rungs_t5.py (`_Trace`).

Every case runs the real walk or the real rung on a temporary store. Faults are runtime patches, or a real chmod where the process is not
root (as root a chmod denies nothing, so the injected EACCES variant is the one that runs everywhere).

FROZEN AT EXTERNAL ROUND 6 (2026-11-08, IMPLEMENTATION ACCEPTED; specs/0018 v9.1.1). This module is the publication-state matrix the
acceptance names. The verdict's rule forward, verbatim: "Keep the publication-state matrix, raw invocation witness and source/test-bound backward captures with later changes to these seams." A change here, or to the writers and sinks it exercises, reopens
review of the frozen surface: it is not an edit to a test.
"""
from __future__ import annotations

import builtins
import contextlib
import io
import json
import os
import sqlite3

import pytest

import veracium.cli as cli
import veracium.store.release_migration as rm
import veracium.store.schema_version as sv

RUNGS = (1, 13, 15)
ATTESTATION = rm.MigrationAttestation(quiesced=True, backup_ref="r5-closures")
REAL_WRITE_TERMINAL = rm._write_terminal
NOT_ROOT = pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="as root a chmod denies nothing; the EACCES-injected cell covers it")


def _store(path, b):
    c = sqlite3.connect(path, isolation_level=None)
    c.execute("BEGIN")
    sv.create(c, b)
    c.execute(f"PRAGMA user_version = {b}")
    c.execute("COMMIT")
    c.close()
    return str(path)


def _stamp(path):
    c = sqlite3.connect(path)
    try:
        return c.execute("PRAGMA user_version").fetchone()[0]
    finally:
        c.close()


def _walk(path, capsys):
    code = cli._migrate_walk(str(path), ATTESTATION)
    out = capsys.readouterr()
    return code, out.out, out.err


def _trail(ap):
    with open(ap, encoding="utf-8") as f:
        return json.load(f)


def _minted(monkeypatch, after=None):
    ids, mint = [], rm.mint_release_authority

    def observed(*a, **k):
        authority = mint(*a, **k)
        ids.append(authority.operation_id)
        if after is not None:
            after(authority)
        return authority
    monkeypatch.setattr(rm, "mint_release_authority", observed)
    return ids


def _unreadable_load(monkeypatch, writer_name, mode):
    """Make the trail's load fail with PermissionError once the named writer runs: `transient` fails the writer's own load only (the
    recovery read succeeds), `persistent` fails every load from then on (the recovery read fails too)."""
    load, state = rm._load_audit, {"armed": False, "fired": 0}

    def failing(apath):
        if state["armed"] and (mode == "persistent" or state["fired"] == 0):
            state["fired"] += 1
            raise PermissionError("injected: the trail cannot be read")
        return load(apath)

    writer = getattr(rm, writer_name)

    def armed(*a, **k):
        state["armed"] = True
        return writer(*a, **k)
    monkeypatch.setattr(rm, "_load_audit", failing)
    monkeypatch.setattr(rm, writer_name, armed)
    return state


def _eacces(monkeypatch, paths):
    """What an unsearchable directory does to Python's view of `paths`: stat, lstat, open and replace raise PermissionError (EACCES),
    so os.path.exists answers False. Runs as root too, where a chmod would deny nothing."""
    deny = {os.path.abspath(p) for p in paths}          # abspath, not realpath: realpath would call the patched lstat
    real_stat, real_lstat, real_open, real_replace = os.stat, os.lstat, builtins.open, os.replace

    def hit(p):
        try:
            return os.path.abspath(os.fsdecode(p)) in deny
        except TypeError:
            return False

    def stat(p, *a, **k):
        if hit(p):
            raise PermissionError(13, "Permission denied (injected)", str(p))
        return real_stat(p, *a, **k)

    def lstat(p, *a, **k):
        if hit(p):
            raise PermissionError(13, "Permission denied (injected)", str(p))
        return real_lstat(p, *a, **k)

    def opener(p, *a, **k):
        if not isinstance(p, int) and hit(p):
            raise PermissionError(13, "Permission denied (injected)", str(p))
        return real_open(p, *a, **k)

    def replace(src, dst, *a, **k):
        if hit(src) or hit(dst):
            raise PermissionError(13, "Permission denied (injected)", str(dst))
        return real_replace(src, dst, *a, **k)
    monkeypatch.setattr(os, "stat", stat)
    monkeypatch.setattr(os, "lstat", lstat)
    monkeypatch.setattr(builtins, "open", opener)
    monkeypatch.setattr(os, "replace", replace)


def _assert_e2(code, out, err, op):
    """§4f's read-error row: the trail cannot be read back, so the walk stops with E2, the operation id, and no rerun."""
    assert code == 3 and "MigrationAuditReadError" in err and "malformed" in err, (out, err)
    assert f"operation_id: {op}" in err.splitlines() and "action: inspect-audit-trail: " in err and "rerun: not until the record is inspected" in err


# ---- the attempted sink ---------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("record, load", [(r, l) for r in ("existing", "absent") for l in ("readable", "transient", "persistent")
                                          if (r, l) != ("absent", "readable")])     # absent and readable is the ordinary write
@pytest.mark.parametrize("b", RUNGS)
def test_an_attempted_write_whose_load_or_append_once_proves_nothing_is_n2(tmp_path, monkeypatch, capsys, b, record, load):
    """Every failure of the attempted writer outside the proving window is unresolved, the id printed and no rerun offered: append-once
    on a record that exists, and an initial load that fails once or every time, whether or not the record is there. The kernel rolls back.
    Where the walk's own terminal readback can read the trail (or finds none, a real ENOENT), the row is N2. Where a trail is there and
    stays unreadable, §4f routes the malformed readback to E2 (MigrationAuditReadError, inspect the trail), as for every outcome: the same
    id, no rerun, never N1."""
    p = _store(tmp_path / "s.db", b)
    ap = rm.audit_trail_path(p)

    def seed(authority):
        with open(ap, "w", encoding="utf-8") as f:
            json.dump({authority.operation_id: {"attempted": {"event": "migration_attempted"}}}, f)
    ids = _minted(monkeypatch, after=seed if record == "existing" else None)
    if load != "readable":
        state = _unreadable_load(monkeypatch, "_write_attempted", load)
    code, out, err = _walk(p, capsys)
    if load != "readable":
        assert state["fired"] >= 1
    assert len(ids) == 1 and "action: rerun: " not in out + err and "migration-audit-unavailable" not in out + err, (out, err)
    if load == "persistent" and record == "existing":         # the walk's readback cannot read the trail that is there: E2
        _assert_e2(code, out, err, ids[0])
    else:
        assert code == 1 and "outcome: migration-audit-state-unknown" in out and "action: query-id-first: " in out
        assert f"operation_id: {ids[0]}" in out.splitlines()
    assert _stamp(p) == b
    if record == "existing":
        assert _trail(ap)[ids[0]] == {"attempted": {"event": "migration_attempted"}}      # the record is still there, untouched


@pytest.mark.parametrize("fault", ["entry-build", "tmp-open", "fsync"])
@pytest.mark.parametrize("b", RUNGS)
def test_an_attempted_write_failing_after_absence_is_proven_and_before_the_rename_is_n1(tmp_path, monkeypatch, capsys, b, fault):
    """The one N1: the trail was read with no attempted record for this id, and the write failed before os.replace was called."""
    p = _store(tmp_path / "s.db", b)
    ap = rm.audit_trail_path(p)
    ids = _minted(monkeypatch)
    if fault == "entry-build":
        real = rm._write_attempted
        monkeypatch.setattr(rm, "_write_attempted", lambda apath, op, ev: real(apath, op, _UncopyableRuntime(ev)))
    elif fault == "tmp-open":
        real_open = builtins.open
        monkeypatch.setattr(builtins, "open", lambda f, *a, **k: (_ for _ in ()).throw(OSError("injected: tmp open"))
                            if isinstance(f, str) and f == ap + ".tmp" else real_open(f, *a, **k))
    else:
        real_fsync, n = os.fsync, []

        def fsync(fd):
            n.append(fd)
            if len(n) == 1:
                raise OSError("injected: fsync")
            return real_fsync(fd)
        monkeypatch.setattr(os, "fsync", fsync)
    code, out, err = _walk(p, capsys)
    assert len(ids) == 1 and code == 1, (out, err)
    assert "outcome: migration-audit-unavailable" in out and "action: rerun: " in out and "query-id-first" not in out
    assert _stamp(p) == b and not (os.path.exists(ap) and "attempted" in _trail(ap).get(ids[0], {}))


class _UncopyableRuntime:
    """The kernel's attempted event, but its runtime key cannot be copied: the writer fails while BUILDING the entry, after the read
    and the append-once check and before the tmp file."""

    def __init__(self, event):
        self._event = event

    def __getattr__(self, name):
        return getattr(self._event, name)

    @property
    def runtime(self):
        class _Key:
            def _asdict(self):
                raise ValueError("injected: the runtime key cannot be copied")
        return _Key()


# ---- the terminal sink ----------------------------------------------------------------------------------------------------------
_TERMINAL = {
    # (record, load): the carrier's audit_committed
    ("matching", "readable"): True, ("matching", "transient"): True, ("matching", "persistent"): None,
    ("different", "readable"): None, ("different", "transient"): None, ("different", "persistent"): None,
    ("absent", "transient"): False, ("absent", "persistent"): None,
}
_SENTENCE = {True: "the terminal record was published; its write reported a failure",
             False: "the terminal record was not published; this tool does not repair it",
             None: "the terminal record may not have been published; this tool does not repair it"}


@pytest.mark.parametrize("record, load", sorted(_TERMINAL))
@pytest.mark.parametrize("b", RUNGS)
def test_a_failed_terminal_write_takes_the_recovery_read_unless_absence_is_proven(tmp_path, monkeypatch, capsys, b, record, load):
    """Outside the proving window the terminal carrier is decided by one recovery read_terminal: True for a valid record equal to the
    facts, False for a successful read with no record (never after append-once), None otherwise. E1 in every case, the committed rung
    counted once, the same store-side action."""
    want = _TERMINAL[(record, load)]
    p = _store(tmp_path / "s.db", b)
    ap = rm.audit_trail_path(p)
    same = rm.TerminalFacts("migrated", b, b + 1, True, True, "destination", b + 1)
    other = rm.TerminalFacts("current", b, b + 1, False, False, "destination", b + 1)

    def seed(authority):
        REAL_WRITE_TERMINAL(ap, authority.operation_id, same if record == "matching" else other)
    ids = _minted(monkeypatch, after=seed if record != "absent" else None)
    carried, delegate = [], rm._delegate

    def observe(*a, **k):
        try:
            return delegate(*a, **k)
        except rm.MigrationAuditWriteError as e:
            carried.append(e)
            raise
    monkeypatch.setattr(rm, "_delegate", observe)
    if load != "readable":
        state = _unreadable_load(monkeypatch, "_write_terminal", load)
    code, out, err = _walk(p, capsys)
    if load != "readable":
        assert state["fired"] >= 1
    assert len(ids) == 1 and len(carried) == 1 and carried[0].audit_committed is want, (record, load, err)
    assert code == 3 and f"action: audit-record-not-published: {_SENTENCE[want]}" in err and f"audit_committed: {want}" in err
    assert f"rungs committed by this walk: 1 ({ids[0]})" in err and "action: rerun-resumes-store: " in err and _stamp(p) == b + 1


@pytest.mark.parametrize("b", RUNGS)
def test_a_terminal_write_failing_after_absence_is_proven_and_before_the_rename_is_false(tmp_path, monkeypatch, capsys, b):
    """The terminal sink's one False: the trail was read with no terminal record for this id, and staging the tmp file failed."""
    p = _store(tmp_path / "s.db", b)
    ap = rm.audit_trail_path(p)
    ids = _minted(monkeypatch)
    stage = rm._stage_audit
    monkeypatch.setattr(rm, "_stage_audit", lambda apath, data: (_ for _ in ()).throw(OSError("injected: stage"))
                        if any("terminal" in e for e in data.values()) else stage(apath, data))
    code, out, err = _walk(p, capsys)
    assert code == 3 and "audit_committed: False" in err and f"action: audit-record-not-published: {_SENTENCE[False]}" in err, err
    assert f"rungs committed by this walk: 1 ({ids[0]})" in err and _stamp(p) == b + 1
    assert rm.read_terminal(ids[0], audit_path=ap).kind == "absent"


# ---- S2: an unsearchable directory is not absence -----------------------------------------------------------------------------------
@pytest.mark.parametrize("sink", ["attempted", "terminal"])
@pytest.mark.parametrize("b", RUNGS)
def test_a_record_in_an_unsearchable_directory_is_never_read_as_absent(tmp_path, monkeypatch, capsys, b, sink):
    """EACCES on the trail and its tmp file, as an unsearchable directory gives (os.path.exists False, os.stat PermissionError), with
    this id's record present: N2 at the attempted sink, None at the terminal sink; never N1 or False."""
    p = _store(tmp_path / "s.db", b)
    ap = rm.audit_trail_path(p)
    same = rm.TerminalFacts("migrated", b, b + 1, True, True, "destination", b + 1)

    def seed(authority):
        if sink == "attempted":
            with open(ap, "w", encoding="utf-8") as f:
                json.dump({authority.operation_id: {"attempted": {"event": "migration_attempted"}}}, f)
        else:
            REAL_WRITE_TERMINAL(ap, authority.operation_id, same)
    ids = _minted(monkeypatch, after=seed)
    writer = rm._write_attempted if sink == "attempted" else rm._write_terminal

    def denied(*a, **k):
        with pytest.MonkeyPatch.context() as mp:
            _eacces(mp, [ap, ap + ".tmp"])
            assert os.path.exists(ap) is False                   # the condition the cell is about
            return writer(*a, **k)
    monkeypatch.setattr(rm, "_write_attempted" if sink == "attempted" else "_write_terminal", denied)
    if sink == "terminal":                                     # the recovery read meets the same directory
        read = rm.read_terminal

        def denied_read(*a, **k):
            with pytest.MonkeyPatch.context() as mp:
                _eacces(mp, [ap, ap + ".tmp"])
                return read(*a, **k)
        monkeypatch.setattr(rm, "read_terminal", denied_read)
    code, out, err = _walk(p, capsys)
    if sink == "attempted":                                    # only the writer's read is denied; the walk's readback reads: N2
        assert code == 1 and "outcome: migration-audit-state-unknown" in out and f"operation_id: {ids[0]}" in out.splitlines(), (out, err)
        assert "action: rerun: " not in out
    else:
        assert code == 3 and "audit_committed: None" in err and f"action: audit-record-not-published: {_SENTENCE[None]}" in err, err


@NOT_ROOT
@pytest.mark.parametrize("b", RUNGS)
def test_a_trail_in_a_real_unsearchable_directory_is_unresolved(tmp_path, monkeypatch, capsys, b):
    """The same with a real chmod 000 on a directory holding the trail (the trail moved beside the store's own directory)."""
    p = _store(tmp_path / "s.db", b)
    locked = tmp_path / "trail"
    locked.mkdir()
    ap = str(locked / "s.db.migration-audit.json")
    monkeypatch.setattr(rm, "audit_trail_path", lambda canonical: ap)

    def seed(authority):
        with open(ap, "w", encoding="utf-8") as f:
            json.dump({authority.operation_id: {"attempted": {"event": "migration_attempted"}}}, f)
        os.chmod(locked, 0)
    ids = _minted(monkeypatch, after=seed)
    try:
        code, out, err = _walk(p, capsys)
    finally:
        os.chmod(locked, 0o700)
    _assert_e2(code, out, err, ids[0])
    assert "migration-audit-unavailable" not in out + err and "action: rerun: " not in out + err
    assert _trail(ap)[ids[0]] == {"attempted": {"event": "migration_attempted"}} and _stamp(p) == b


@pytest.mark.parametrize("b", RUNGS)
def test_preflight_never_reads_a_store_it_cannot_stat_as_missing(tmp_path, monkeypatch, capsys, b):
    """At preflight, a store the process cannot stat is present: never migration-source-missing and U2's fix-the-path."""
    p = _store(tmp_path / "s.db", b)
    _eacces(monkeypatch, [p])
    assert os.path.exists(p) is False
    rep = rm.run_release_rung(p, host_attestation=ATTESTATION)
    assert rep.result.outcome != "migration-source-missing", rep


@NOT_ROOT
@pytest.mark.parametrize("b", RUNGS)
def test_a_store_in_a_real_unsearchable_directory_is_unopenable_never_missing(tmp_path, capsys, b):
    """With a real chmod 000 on the store's directory, the walk says store-unopenable and fix-access (U6), never missing (U2)."""
    d = tmp_path / "locked"
    d.mkdir()
    p = _store(d / "s.db", b)
    os.chmod(d, 0)
    try:
        code, out, err = _walk(p, capsys)
    finally:
        os.chmod(d, 0o700)
    assert code == 1 and "outcome: store-unopenable" in out and "action: fix-access-then-rerun: " in out, (out, err)
    assert "migration-source-missing" not in out and "fix-path-then-rerun" not in out and _stamp(p) == b


@pytest.mark.parametrize("b", RUNGS)
def test_the_mint_never_reads_a_store_it_cannot_stat_as_source_missing(tmp_path, monkeypatch, b):
    """At the mint, after a resolution, a store the process cannot stat is present: the mint's reason is never source-missing."""
    p = _store(tmp_path / "s.db", b)
    kind, resolved = rm._classify_or_intercept(p)
    assert kind == "mint", (kind, resolved)
    _eacces(monkeypatch, [p])
    try:
        authority = rm.mint_release_authority(resolved.canonical_path, ATTESTATION, resolved=resolved)
    except rm.MintError as e:
        assert e.reason != "source-missing", e
    else:
        assert authority.from_version == b
