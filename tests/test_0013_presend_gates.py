"""Pre-send gates for `specs/0013`'s audit reference — the two MECHANICAL
checks that catch the class of defect the external reviewer keeps finding one
round late, BEFORE a candidate goes out:

  1. An EXHAUSTIVE truth table for `TerminalFacts.problems()`, checked against
     an INDEPENDENT legality oracle (flat boolean logic, written separately
     from the validator's problem-accumulation). Enumerating the whole domain
     has no blind spot to miss a cell — which is exactly how the partial-`None`
     and `(None,None)` cells slipped through hand-written examples (round 14,
     finding 1). It also PINS the entire truth table, so any future change to a
     single cell fails loudly here.

  2. A SYSTEMATIC fault-injection sweep: a fault at every audit/planner seam,
     asserting the UNIVERSAL invariants — the result is a closed outcome OR one
     of the two named escapes (nothing else), every terminal record is a valid
     `TerminalFacts`, and the label matches the PHASE (a pre-read defect is
     never `invalid-store`). This generalizes the reviewer's per-seam probes and
     guards the "the fix's name is a claim" failure mode (round 14, finding 4:
     "classify by phase" that actually tested "commit facts exist").

These run in the ordinary suite, so they are part of every round's green bar.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "specs"))

import migrations_0013 as m  # noqa: E402
from veracium.store import schema_version as sv  # noqa: E402


def _v1_store():
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    for o in m.SCHEMA_V1:
        c.execute(o.ddl)
    c.execute("PRAGMA user_version=1")
    c.commit()
    c.close()
    return p


# ==========================================================================
# Gate 1: the complete TerminalFacts truth table vs an independent oracle
# ==========================================================================

_FROM, _TO = 1, 2
_KNOWN = set(m.OUTCOMES) | set(m._AUDIT_ONLY_OUTCOMES)
_STATES = set(m._RESULTING_STATES)

# INDEPENDENT copy of the outcome→state map (round 16, correction B: the oracle
# must NOT read `m._OUTCOME_TERMINAL_STATES`, or a wrong map appears identically
# in validator and oracle and cannot disagree). This is a separate, hand-written
# specification; when the contract changes, update BOTH and let the exhaustive
# diff confirm they still agree. A wrong implementation map now DISAGREES here.
_ORACLE_OUTCOME_STATES = {
    "migrated": {"destination"},
    "current": {"destination"},
    "migration-source-missing": {"missing", "unaccepted"},
    "migration-failed": {"source", "unknown"},
    "migration-result-mismatch": {"source", "unknown"},
    "migration-evidence-missing": {"source", "unknown"},
    "migration-quiescence-required": {"source", "unknown"},
    "internal-error": {"destination", "source", "unknown"},
    "package-inconsistent": {"destination", "source", "unknown"},
    "foreign-shape": {"unaccepted", "unknown"},
    "newer": {"unaccepted", "unknown"},
    "invalid-version": {"unaccepted", "unknown"},
    "stamped-shape-mismatch": {"source", "unaccepted", "unknown"},
}


def _oracle(outcome, ch, co, state, ver):
    """Independent specification of a LEGAL terminal-facts tuple — flat rules,
    not the validator's accumulation. Endpoints fixed at (1, 2)."""
    if outcome not in _KNOWN:
        return False
    if state not in _STATES:
        return False
    if ch != co:                         # one fact observed twice — must match
        return False
    if ch is None:                       # genuinely unknown
        if not (state == "unknown" and ver is None):
            return False
    elif ch is True:                     # a committed change
        if not (state == "destination" and ver == _TO):
            return False
    else:                                # known unchanged
        if state == "destination":
            if ver != _TO:
                return False
        elif state == "source":
            if ver != _FROM:
                return False
        else:                            # missing / unaccepted / unknown
            if ver is not None:
                return False
    if outcome == "migrated" and not (ch is True and co is True):
        return False
    if state not in _ORACLE_OUTCOME_STATES.get(outcome, {"unknown"}):
        return False
    return True


def test_terminal_facts_matches_the_independent_oracle():
    """Every (outcome, store_changed, transaction_committed, resulting_state,
    resulting_version) in the whole small domain: the validator's verdict must
    equal the independent oracle's. A disagreement is a bug in one of them,
    found before external review — and this pins the entire truth table."""
    outcomes = sorted(_KNOWN) + ["totally-made-up"]
    states = sorted(_STATES) + ["bogus-state"]
    tri = [True, False, None]
    vers = [None, _FROM, _TO, 999]
    disagreements = []
    total = 0
    for outcome in outcomes:
        for ch in tri:
            for co in tri:
                for state in states:
                    for ver in vers:
                        total += 1
                        got = not m.TerminalFacts(
                            outcome, _FROM, _TO, ch, co, state, ver).problems()
                        want = _oracle(outcome, ch, co, state, ver)
                        if got != want:
                            disagreements.append(
                                (outcome, ch, co, state, ver, got, want))
    assert total > 5000                  # the domain is genuinely enumerated
    assert not disagreements, (
        f"{len(disagreements)} validator/oracle disagreements, e.g. "
        f"{disagreements[:5]}")


# ==========================================================================
# Gate 2: a systematic fault at every seam preserves the invariants
# ==========================================================================

_NAMED_ESCAPES = (sv.PackageConsistencyError, m.MigrationAuditWriteError)


def _raiser(exc):
    def f(*a, **k):
        raise exc
    return f


class _CloseFails:
    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    def close(self):
        raise sqlite3.DatabaseError("forced connection-close failure")


def _install_attr(obj, name, fn):
    real = getattr(obj, name)
    setattr(obj, name, fn)
    return lambda: setattr(obj, name, real)


def _real_then(obj, name, after):
    real = getattr(obj, name)

    def wrap(*a, **k):
        r = real(*a, **k)
        after()
        return r
    setattr(obj, name, wrap)
    return lambda: setattr(obj, name, real)


def _connect_close_fails():
    real = m.sqlite3.connect

    def wrap(*a, **k):
        c = real(*a, **k)
        return _CloseFails(c) if (a and isinstance(a[0], str)
                                  and a[0].startswith("file:")) else c
    m.sqlite3.connect = wrap
    return lambda: setattr(m.sqlite3, "connect", real)


def _activate_lose(committed, publish):
    real = m._AUDIT.activate

    def flaky(a, output_digest):
        if publish:
            real(a, output_digest)
        raise m.AuditStorageUnavailable("response lost", committed=committed)
    m._AUDIT.activate = flaky
    return lambda: setattr(m._AUDIT, "activate", real)


def _record_terminal_lose(publish):
    real = m._AUDIT.record_terminal

    def flaky(operation_id, event, payload):
        if publish:
            real(operation_id, event, payload)
        raise OSError("terminal write response lost")
    m._AUDIT.record_terminal = flaky
    return lambda: setattr(m._AUDIT, "record_terminal", real)


def _outcome_is(want):
    return lambda res, exc: (None if res == want
                             else f"want outcome {want!r}, got {res!r}")


def _raises_pkg(res, exc):
    return (None if isinstance(exc, sv.PackageConsistencyError)
            else f"want PackageConsistencyError, got res={res!r} exc={exc!r}")


def _write_error(audit_committed):
    def check(res, exc):
        if not isinstance(exc, m.MigrationAuditWriteError):
            return f"want MigrationAuditWriteError, got res={res!r} exc={exc!r}"
        if exc.audit_committed is not audit_committed:
            return f"want audit_committed={audit_committed}, got {exc.audit_committed}"
        return None
    return check


class _IsoFails:
    """A connection proxy whose `isolation_level` setter raises — a setup
    failure the instant after the connection exists (round 15, finding 5)."""

    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    @property
    def isolation_level(self):
        return self._real.isolation_level

    @isolation_level.setter
    def isolation_level(self, value):
        raise sqlite3.DatabaseError("isolation-level setup failed")

    def close(self):
        return self._real.close()


def _connect_iso_fails():
    real = m.sqlite3.connect

    def wrap(*a, **k):
        c = real(*a, **k)
        return _IsoFails(c) if (a and isinstance(a[0], str)
                                and a[0].startswith("file:")) else c
    m.sqlite3.connect = wrap
    return lambda: setattr(m.sqlite3, "connect", real)


def _hook_raises(exc):
    real = m._migrating_hook

    def fake(art, authority, state):
        def h(*a, **k):
            raise exc
        return h
    m._migrating_hook = fake
    return lambda: setattr(m, "_migrating_hook", real)


def _returns(obj, name, value):
    return lambda: _install_attr(obj, name, lambda *a, **k: value)


def _write_error_any(res, exc):
    return (None if isinstance(exc, m.MigrationAuditWriteError)
            else f"want MigrationAuditWriteError, got res={res!r} exc={exc!r}")


# (id, install -> cleanup, expect(res, exc) -> error message or None)
_INJECTIONS = [
    # --- round 16: a lying receipt / a silent no-op sink --------------------
    # A receipt claiming 'activated' without publishing the row (round 16 f1).
    ("activate-lies-without-publishing",
     lambda: _install_attr(m._AUDIT, "activate",
                           lambda a, od: m.ActivationReceipt(
                               "activated", a.operation_id, True, False)),
     _outcome_is("internal-error")),
    # A terminal sink that returns None (no receipt, no event) (round 16 f2).
    ("record_terminal-silent-noop",
     _returns(m._AUDIT, "record_terminal", None),
     _write_error_any),
    # --- round 15: bad RETURN values (not just raises) ----------------------
    ("activate-returns-None",
     _returns(m._AUDIT, "activate", None),
     _outcome_is("internal-error")),
    ("activate-returns-unknown-string",
     _returns(m._AUDIT, "activate", "bogus"),
     _outcome_is("internal-error")),
    ("activate-returns-bool",
     _returns(m._AUDIT, "activate", True),
     _outcome_is("internal-error")),
    ("open_versioned-returns-bad-type",
     _returns(m.sv, "open_versioned", "migrated"),
     _outcome_is("internal-error")),
    ("migration-hook-DatabaseError",
     lambda: _hook_raises(sqlite3.DatabaseError("hook defect")),
     _outcome_is("migration-failed")),
    ("isolation_level-DatabaseError",
     _connect_iso_fails,
     _outcome_is("internal-error")),
    ("runtime-gate-DatabaseError",
     lambda: _install_attr(m.sv, "runtime_supported",
                           _raiser(sqlite3.DatabaseError("probe defect"))),
     _outcome_is("internal-error")),
    ("migration-runtime-DatabaseError",
     lambda: _install_attr(m, "migration_runtime_supported",
                           _raiser(sqlite3.DatabaseError("probe defect"))),
     _outcome_is("internal-error")),
    ("open_versioned-read-DatabaseError",
     lambda: _install_attr(m.sv, "open_versioned",
                           _raiser(sqlite3.DatabaseError("malformed image"))),
     _outcome_is("invalid-store")),
    ("open_versioned-post-commit-PackageConsistencyError",
     lambda: _real_then(m.sv, "open_versioned",
                        _raiser(sv.PackageConsistencyError("post-commit"))),
     _raises_pkg),
    ("open_versioned-pre-commit-PackageConsistencyError",
     lambda: _install_attr(m.sv, "open_versioned",
                           _raiser(sv.PackageConsistencyError("pre-commit"))),
     _raises_pkg),
    ("activate-committed-True",
     lambda: _activate_lose(True, True),
     _outcome_is("migration-quiescence-required")),
    ("activate-committed-False",
     lambda: _activate_lose(False, False),
     _outcome_is("migration-audit-unavailable")),
    ("activate-committed-None",
     lambda: _activate_lose(None, False),
     _outcome_is("migration-audit-state-unknown")),
    ("activate-generic-defect",
     lambda: _install_attr(m._AUDIT, "activate",
                           _raiser(AssertionError("library bug"))),
     _outcome_is("internal-error")),
    ("record_terminal-OSError-published",
     lambda: _record_terminal_lose(True),
     _write_error(True)),
    ("record_terminal-OSError-not-published",
     lambda: _record_terminal_lose(False),
     _write_error(False)),
    ("conn.close-DatabaseError-cleanup",
     _connect_close_fails,
     _outcome_is("internal-error")),
]


def _terminal_facts_problems(auth):
    """Every terminal event this operation recorded must be a valid
    TerminalFacts — the producer never writes an impossible record."""
    op = m._AUDIT._ops.get(auth.operation_id)
    if op is None:
        return []
    problems = []
    for (oid, ev), pl in m._AUDIT._events.items():
        if oid != auth.operation_id or ev == "migration_attempted":
            continue
        tf = m.TerminalFacts(pl["outcome"], op["from_version"],
                             op["to_version"], pl["store_changed"],
                             pl["transaction_committed"], pl["resulting_state"],
                             pl["resulting_version"])
        problems += [f"{ev}: {x}" for x in tf.problems()]
    return problems


@pytest.mark.parametrize("name,install,expect",
                         _INJECTIONS, ids=[i[0] for i in _INJECTIONS])
def test_every_fault_seam_preserves_the_invariants(name, install, expect):
    """Inject a fault at one seam and assert the universal invariants: the
    result is a closed outcome OR one of the two named escapes (nothing else
    leaks), every terminal record is a valid TerminalFacts, and the outcome
    matches the phase the fault occurred in."""
    p = _v1_store()
    auth = m.make_authority(p)
    cleanup = install()
    res, exc = None, None
    try:
        res = m.migrate_store(p, auth)
    except BaseException as e:               # noqa: BLE001 — the point is to catch all
        exc = e
    finally:
        cleanup()

    errors = []
    if exc is not None and not isinstance(exc, _NAMED_ESCAPES):
        errors.append(f"UN-NAMED escape {type(exc).__name__}: {exc}")
    if res is not None and res not in m.OUTCOMES:
        errors.append(f"outcome {res!r} is not a closed member")
    tp = _terminal_facts_problems(auth)
    if tp:
        errors.append("invalid terminal facts: " + "; ".join(tp))
    # RECORD-COMPLETENESS invariants (round 16, correction B: the sweep must
    # assert audit completeness UNIVERSALLY, or a false success / silent no-op
    # slips through). An operation never has more than one terminal event, and a
    # SUCCESS outcome must leave a durable operation row AND exactly one.
    n_terminal = sum(1 for (oid, ev) in m._AUDIT._events
                     if oid == auth.operation_id and ev in _TERMINAL_KINDS)
    if n_terminal > 1:
        errors.append(f"{n_terminal} terminal events for one operation")
    if res in ("migrated", "current"):
        if auth.operation_id not in m._AUDIT._ops:
            errors.append(f"success outcome {res!r} but NO operation row")
        if n_terminal != 1:
            errors.append(f"success outcome {res!r} but {n_terminal} terminal "
                          f"events (must be exactly one)")
    spec = expect(res, exc)
    if spec:
        errors.append(spec)
    assert not errors, f"[{name}] " + " | ".join(errors)


_TERMINAL_KINDS = ("migration_completed", "migration_failed")


class _CountsCloses:
    """A connection proxy that counts `close()` calls and fails a chosen setup
    step, to prove every opened connection is closed exactly once."""

    def __init__(self, real, fail_isolation=False):
        self._real = real
        self._fail_isolation = fail_isolation
        self.closes = 0

    def __getattr__(self, name):
        return getattr(self._real, name)

    @property
    def isolation_level(self):
        return self._real.isolation_level

    @isolation_level.setter
    def isolation_level(self, value):
        if self._fail_isolation:
            raise sqlite3.DatabaseError("isolation-level setup failed")
        self._real.isolation_level = value

    def close(self):
        self.closes += 1
        return self._real.close()


def test_a_connection_setup_failure_closes_the_connection_exactly_once():
    """Round 15, finding 5: an opened connection whose `isolation_level` setup
    fails must still be closed — the cleanup scope starts the instant the
    connection exists. The connection is closed exactly once."""
    p = _v1_store()
    auth = m.make_authority(p)
    holder = {}
    real = m.sqlite3.connect

    def wrap(*a, **k):
        c = real(*a, **k)
        if a and isinstance(a[0], str) and a[0].startswith("file:"):
            proxy = _CountsCloses(c, fail_isolation=True)
            holder["proxy"] = proxy
            return proxy
        return c
    m.sqlite3.connect = wrap
    try:
        out = m.migrate_store(p, auth)
    finally:
        m.sqlite3.connect = real
    assert out == "internal-error"
    assert holder["proxy"].closes == 1        # opened, and closed exactly once


def test_non_adjacent_endpoints_reject_at_every_carrier():
    """Round 15, correction B: the migration contract is adjacent (n → n+1).
    Non-adjacent endpoints reject in TerminalFacts (hence both carriers)."""
    assert m.TerminalFacts("migrated", 1, 3, True, True, "destination", 3).problems()
    with pytest.raises(ValueError):
        m.MigrationAuditWriteError(
            operation_id="op-00000000-0000-4000-8000-000000000000",
            store_path="/s",
            facts=m.TerminalFacts("migrated", 1, 3, True, True, "destination", 3))
