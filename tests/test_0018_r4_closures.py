"""0018 adjacent rungs, external round 4's closures (R4-01, R4-02, R4-03), at the first, a middle and the last rung.

Every fault is a runtime patch on a temporary store, and every case runs the REAL walk (`cli._migrate_walk`) or the real rung
(`run_release_rung`), so what is asserted is what an operator would read and what the durable sidecar holds afterwards.
R4-04's closure is in tests/test_0018_rungs_t5.py (`_Trace.acts`).
"""
from __future__ import annotations

import json
import os
import sqlite3

import pytest

import veracium.cli as cli
import veracium.store.release_migration as rm
import veracium.store.schema_version as sv

HEAD = sv.SCHEMA_VERSION
RUNGS = (1, 13, 15)        # the first rung, a middle one, and the last, whose target is head
ATTESTATION = rm.MigrationAttestation(quiesced=True, backup_ref="r4-closures")


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


def _trail(path):
    ap = rm.audit_trail_path(str(path))
    if not os.path.exists(ap):
        return {}
    with open(ap, encoding="utf-8") as f:
        return json.load(f)


def _walk(path, capsys):
    code = cli._migrate_walk(str(path), ATTESTATION)
    out = capsys.readouterr()
    return code, out.out, out.err


def _minted(monkeypatch, after=None):
    """Record every operation id the mint returns; `after(authority)` runs once the authority exists."""
    ids, mint = [], rm.mint_release_authority

    def observed(*a, **k):
        authority = mint(*a, **k)
        ids.append(authority.operation_id)
        if after is not None:
            after(authority)
        return authority
    monkeypatch.setattr(rm, "mint_release_authority", observed)
    return ids


def _replace_fault(monkeypatch, path, *, which, rename, readable=True):
    """Fail the FIRST `os.replace` onto the sidecar whose new content is `which` ("attempted" or "terminal"): with `rename` the
    rename takes effect and then raises (a lost response); without it, it raises and nothing moves. With `readable=False` the trail
    cannot be read once the fault has fired, so nothing about the publication can be established."""
    ap, real, fired = rm.audit_trail_path(str(path)), os.replace, []

    def replace(src, dst):
        if str(dst) == ap and not fired:
            with open(src, encoding="utf-8") as f:
                entries = json.load(f).values()
            new = "terminal" if any("terminal" in e for e in entries) else "attempted"
            if new == which:
                fired.append(True)
                if rename:
                    real(src, dst)
                raise OSError(f"injected: {which} rename {'took effect' if rename else 'not performed'}")
        return real(src, dst)
    monkeypatch.setattr(rm.os, "replace", replace)
    if not readable:
        load = rm._load_audit

        def unreadable(p):
            if fired:
                raise OSError("injected: the trail cannot be read")
            return load(p)
        monkeypatch.setattr(rm, "_load_audit", unreadable)
    return fired


def _fsync_fault(monkeypatch, *, nth):
    """Fail the `nth` fsync in the sidecar writer: before its `os.replace` is ever called."""
    real, calls = os.fsync, []

    def fsync(fd):
        calls.append(fd)
        if len(calls) == nth:
            raise OSError("injected: fsync failed before the rename")
        return real(fd)
    monkeypatch.setattr(rm.os, "fsync", fsync)
    return calls


# ---- R4-01: the attempted sink --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("fault", ["fsync-before-rename", "rename-not-performed"])
@pytest.mark.parametrize("b", RUNGS)
def test_an_attempted_write_proven_unpublished_is_n1(tmp_path, monkeypatch, capsys, b, fault):
    """N1 only with proof: the write failed before `os.replace` was called, or the rename raised and a successful read-back shows no
    attempted record for this id. The transaction rolled back, the sidecar holds no attempted record, and a rerun is offered."""
    p = _store(tmp_path / "s.db", b)
    ids = _minted(monkeypatch)
    if fault == "fsync-before-rename":
        _fsync_fault(monkeypatch, nth=1)
    else:
        fired = _replace_fault(monkeypatch, p, which="attempted", rename=False)
    code, out, err = _walk(p, capsys)
    if fault == "rename-not-performed":
        assert fired == [True]
    assert code == 1 and "outcome: migration-audit-unavailable" in out and "action: rerun: " in out, (out, err)
    assert len(ids) == 1 and not any("attempted" in e for e in _trail(p).values()) and _stamp(p) == b


@pytest.mark.parametrize("b", RUNGS)
def test_an_attempted_record_published_by_a_failed_rename_is_n2_and_its_id_is_printed(tmp_path, monkeypatch, capsys, b):
    """The rename took effect and then raised: the attempted record is durable although the kernel rolled back. That is N2: the
    authority MAY be consumed, a rerun is not offered, and the walk prints the id the prescribed inquiry needs."""
    p = _store(tmp_path / "s.db", b)
    ids = _minted(monkeypatch)
    fired = _replace_fault(monkeypatch, p, which="attempted", rename=True)
    code, out, err = _walk(p, capsys)
    assert fired == [True] and len(ids) == 1
    assert code == 1 and "outcome: migration-audit-state-unknown" in out and "action: query-id-first: " in out, (out, err)
    assert f"operation_id: {ids[0]}" in out.splitlines() and "rerun: NO" in out and "action: rerun: " not in out
    trail = _trail(p)
    assert trail[ids[0]]["attempted"]["from_version"] == b and "terminal" not in trail[ids[0]]
    assert _stamp(p) == b


@pytest.mark.parametrize("b", RUNGS)
def test_an_attempted_publication_that_cannot_be_read_back_is_n2(tmp_path, monkeypatch, capsys, b):
    """The rename raised and did NOT take effect, but the trail cannot be read afterwards, so absence is true and unproven: N2."""
    p = _store(tmp_path / "s.db", b)
    ids = _minted(monkeypatch)
    fired = _replace_fault(monkeypatch, p, which="attempted", rename=False, readable=False)
    code, out, err = _walk(p, capsys)
    assert fired == [True] and len(ids) == 1
    assert code == 1 and "outcome: migration-audit-state-unknown" in out and f"operation_id: {ids[0]}" in out.splitlines(), (out, err)
    assert _stamp(p) == b


@pytest.mark.parametrize("b", RUNGS)
def test_an_append_once_refusal_is_n2_never_nothing_consumed(tmp_path, monkeypatch, capsys, b):
    """Append-once refuses before any write, but the record that refuses it IS this id's attempted record: never N1."""
    p = _store(tmp_path / "s.db", b)
    ap = rm.audit_trail_path(p)

    def preexisting(authority):
        with open(ap, "w", encoding="utf-8") as f:
            json.dump({authority.operation_id: {"attempted": {"event": "migration_attempted"}}}, f)
    ids = _minted(monkeypatch, after=preexisting)
    code, out, err = _walk(p, capsys)
    assert len(ids) == 1
    assert code == 1 and "outcome: migration-audit-state-unknown" in out and f"operation_id: {ids[0]}" in out.splitlines(), (out, err)
    assert _stamp(p) == b


# ---- R4-01: the terminal sink -------------------------------------------------------------------------------------------
_TERMINAL_CASES = {
    # case: (how the terminal write fails, the carrier's audit_committed, the sentence printed, read_terminal's kind afterwards)
    "fsync-before-rename": (False, "the terminal record was not published", "absent"),
    "rename-not-performed": (False, "the terminal record was not published", "absent"),
    "rename-took-effect": (True, "the terminal record was published; its write reported a failure", "record"),
    "rename-took-effect-unreadable": (None, "the terminal record may not have been published", None),
    # append-once refuses because this id already holds a terminal record: never "not published"
    "terminal-present-equal": (True, "the terminal record was published; its write reported a failure", "record"),
    "terminal-present-other": (None, "the terminal record may not have been published", "record"),
}


@pytest.mark.parametrize("case", sorted(_TERMINAL_CASES))
@pytest.mark.parametrize("b", RUNGS)
def test_a_failed_terminal_write_reports_what_it_established(tmp_path, monkeypatch, capsys, b, case):
    """E1 in every case, with the committed rung counted and the same store-side action; only the publication disclosure differs,
    and it is never stronger than what was established. `True` needs a valid record equal to the facts written."""
    want_committed, sentence, readback = _TERMINAL_CASES[case]
    p = _store(tmp_path / "s.db", b)
    ids = _minted(monkeypatch)
    carried = []
    delegate = rm._delegate

    def observe(*a, **k):
        try:
            return delegate(*a, **k)
        except rm.MigrationAuditWriteError as e:
            carried.append(e)
            raise
    monkeypatch.setattr(rm, "_delegate", observe)
    if case == "fsync-before-rename":
        _fsync_fault(monkeypatch, nth=3)          # attempted, the committed marker, then the terminal record
    elif case.startswith("terminal-present"):
        # a terminal record for this id before the rung runs: the facts this rung will write, or another lawful cell
        same = rm.TerminalFacts("migrated", b, b + 1, True, True, "destination", b + 1)
        other = rm.TerminalFacts("current", b, b + 1, False, False, "destination", b + 1)
        ap = rm.audit_trail_path(p)
        monkeypatch.setattr(rm, "mint_release_authority", _seed_terminal(rm.mint_release_authority, ap,
                                                                           same if case.endswith("equal") else other))
    else:
        fired = _replace_fault(monkeypatch, p, which="terminal", rename=case.startswith("rename-took-effect"),
                               readable=not case.endswith("unreadable"))
    code, out, err = _walk(p, capsys)
    if case != "fsync-before-rename" and not case.startswith("terminal-present"):
        assert fired == [True]
    assert len(ids) == 1 and len(carried) == 1 and carried[0].audit_committed is want_committed, (case, err)
    assert code == 3 and f"(operation {ids[0]}): its {sentence[4:]}" in err and f"action: audit-record-not-published: {sentence}" in err
    assert f"audit_committed: {want_committed}" in err
    assert f"rungs committed by this walk: 1 ({ids[0]})" in err and "action: rerun-resumes-store: " in err
    assert _stamp(p) == b + 1
    if readback is not None:
        rb = rm.read_terminal(ids[0], audit_path=rm.audit_trail_path(p))
        assert rb.kind == readback
        if readback == "record":
            assert (tuple(rb.facts) == tuple(carried[0].facts)) is (want_committed is True)


def _seed_terminal(mint, ap, facts):
    """Wrap the (already observed) mint: once the authority exists, write a terminal record for its id, as the real writer does."""
    def seeded(*a, **k):
        authority = mint(*a, **k)
        rm._write_terminal(ap, authority.operation_id, facts)
        return authority
    return seeded


# ---- R4-02: ordinary readback binds outcome AND endpoints ----------------------------------------------------------------
def _after_mint(path, state):
    """What the store becomes between the mint and the rung, so the kernel reports a lawful no-version fact."""
    def change(authority):
        os.unlink(path)
        if state == "unaccepted":                  # an empty database where a source is attested
            sqlite3.connect(path).close()
        elif state == "unknown":                   # something that exists and will not open
            os.mkdir(path)
    return change


_ORDINARY = {"missing": ("migration-source-missing", "missing"), "unaccepted": ("migration-source-missing", "unaccepted"),
             "unknown": ("store-unopenable", "unknown")}


@pytest.mark.parametrize("wrong", [False, True], ids=["this-rung", "another-rung"])
@pytest.mark.parametrize("state", sorted(_ORDINARY))
@pytest.mark.parametrize("b", RUNGS)
def test_an_ordinary_record_binds_only_at_the_minted_rung(tmp_path, monkeypatch, capsys, b, state, wrong):
    """A durable, lawful record under this id with the kernel's outcome but ANOTHER rung's endpoints is not this rung's fact
    source: MigrationAuditReadError(mismatched), exit 3, nothing counted, no recorded version. `resulting_version` is None in every
    case, so nothing but the endpoints can expose the wrong rung."""
    outcome, resulting_state = _ORDINARY[state]
    p = str(tmp_path / "s.db")
    _store(p, b)
    _minted(monkeypatch, after=_after_mint(p, state))
    write = rm._write_terminal
    written = []

    def terminal(apath, op, facts):
        if wrong:
            other = 13 if b == 1 else 1
            facts = facts._replace(from_version=other, to_version=other + 1)
        assert rm.TerminalFacts.problems(facts) == []
        written.append(facts)
        return write(apath, op, facts)
    monkeypatch.setattr(rm, "_write_terminal", terminal)
    with pytest.raises(rm.MigrationAuditReadError) if wrong else _nothing() as raised:
        report = rm.run_release_rung(p, host_attestation=ATTESTATION)
    assert [(f.outcome, f.resulting_state, f.resulting_version) for f in written] == [(outcome, resulting_state, None)]
    if wrong:
        assert raised.value.failure == "mismatched" and raised.value.rung_context[1:] == (b, b + 1)
    else:
        assert report.result.outcome == outcome and report.result.resulting_state == resulting_state
        assert "(recorded)" in report.result.diagnostic


@pytest.mark.parametrize("b", RUNGS)
def test_the_walk_refuses_a_record_from_another_rung(tmp_path, monkeypatch, capsys, b):
    """The same, through the walk: exit 3, the read error's row, and no rung counted."""
    p = str(tmp_path / "s.db")
    _store(p, b)
    ids = _minted(monkeypatch, after=_after_mint(p, "unaccepted"))
    write = rm._write_terminal
    other = 13 if b == 1 else 1
    monkeypatch.setattr(rm, "_write_terminal",
                        lambda apath, op, facts: write(apath, op, facts._replace(from_version=other, to_version=other + 1)))
    code, out, err = _walk(p, capsys)
    assert code == 3 and "MigrationAuditReadError" in err and "mismatched" in err, (out, err)
    assert "rungs committed by this walk: 0 (none)" in err and "store version: unknown" in err and ids[0] in err


class _nothing:
    def __enter__(self):
        return None

    def __exit__(self, *exc):
        return False


# ---- R4-03: the named escape keeps its route inside the mint ----------------------------------------------------------------
@pytest.mark.parametrize("b", RUNGS)
def test_a_package_inconsistency_inside_the_mint_is_the_pre_mint_escape(tmp_path, monkeypatch, capsys, b):
    """Raised after source observation and before any authority returns: the same exception, `rung_context` None, no readback, no
    record, and the walk's exit 3 with E3's repair-build, exactly as at preflight."""
    p = _store(tmp_path / "s.db", b)
    marker = sv.PackageConsistencyError("injected inside the mint")

    def digest(base, target):
        raise marker
    monkeypatch.setattr(rm, "_declared_migration_digest", digest)
    with pytest.raises(sv.PackageConsistencyError) as e:
        rm.run_release_rung(p, host_attestation=ATTESTATION)
    assert e.value is marker and e.value.rung_context is None and not hasattr(e.value, "readback_route")
    assert _trail(p) == {} and _stamp(p) == b
    code, out, err = _walk(p, capsys)
    assert code == 3 and "action: repair-build: " in err and "pre-mint: no operation minted" in err, (out, err)
    assert "operation_id" not in out + err and "(operation op-" not in out + err


@pytest.mark.parametrize("b", (1, 13))
def test_a_mint_escape_after_a_committed_rung_reuses_no_earlier_id(tmp_path, monkeypatch, capsys, b):
    """The first rung commits; the second rung's mint raises. The escape is pre-mint: it carries no context, and the first rung's id
    appears only where that rung is counted."""
    p = _store(tmp_path / "s.db", b)
    ids = _minted(monkeypatch)
    real = rm._declared_migration_digest

    def digest(base, target):
        if base == b + 1:
            raise sv.PackageConsistencyError("injected inside the second mint")
        return real(base, target)
    monkeypatch.setattr(rm, "_declared_migration_digest", digest)
    code, out, err = _walk(p, capsys)
    assert code == 3 and len(ids) == 1 and _stamp(p) == b + 1, (out, err)
    assert f"rungs committed by this walk: 1 ({ids[0]})" in err and "pre-mint: no operation minted" in err
    assert "action: repair-build: " in err and (out + err).count(ids[0]) == 2       # the rung's own line, and its count
