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
import types
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
    # Round 20, finding 3: an internal defect can occur after ANY physical state
    # was established, and the terminal fallback preserves whichever was frozen.
    "internal-error": {"destination", "source", "missing", "unaccepted",
                       "unknown"},
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


def _activate_wrong_binding():
    """Publish a valid row bound to a DIFFERENT store, then return a normal
    receipt (round 17, finding 1)."""
    real = m._AUDIT.activate

    def wrong(a, output_digest):
        return real(a._replace(store_path="/tmp/wrong-binding.db"), output_digest)
    m._AUDIT.activate = wrong
    return lambda: setattr(m._AUDIT, "activate", real)


def _terminal_wrong_payload():
    """Publish an individually-valid but DIFFERENT terminal payload than the one
    requested, then return a normal receipt (round 17, finding 2)."""
    real = m._AUDIT.record_terminal

    def wrong(operation_id, event, payload):
        bad = dict(payload)
        bad.update(outcome="current", store_changed=False,
                   transaction_committed=False)
        return real(operation_id, event, bad)
    m._AUDIT.record_terminal = wrong
    return lambda: setattr(m._AUDIT, "record_terminal", real)


def _write_error_any(res, exc):
    return (None if isinstance(exc, m.MigrationAuditWriteError)
            else f"want MigrationAuditWriteError, got res={res!r} exc={exc!r}")


# --- round 18: verify the COMPLETE record, both atomic parts ----------------

def _activate_corrupt_attempted():
    """Publish the real activation, then corrupt the attempted EVENT while
    keeping its (operation_id, migration_attempted) key (round 18, finding 1:
    v19 verified the attempted event only by key existence)."""
    real = m._AUDIT.activate

    def wrong(a, output_digest):
        r = real(a, output_digest)
        st = m._AUDIT._state
        evs = dict(st.events)
        evs[(a.operation_id, "migration_attempted")] = m._freeze({
            "event_id": "ev-00000000-0000-4000-8000-ffffffffffff",
            "operation_id": "op-00000000-0000-4000-8000-ffffffffffff",
            "event": "wrong", "occurred_at": "not-a-time"})
        m._AUDIT._state = st._replace(events=m._readonly(evs))
        return r
    m._AUDIT.activate = wrong
    return lambda: setattr(m._AUDIT, "activate", real)


def _terminal_leaves_attempted():
    """Publish the terminal event but leave the operation row `attempted` — a
    valid payload with no state transition (round 18, finding 2)."""
    real = m._AUDIT.record_terminal

    def wrong(operation_id, event, payload):
        rec = real(operation_id, event, payload)
        st = m._AUDIT._state
        ops = dict(st.ops)
        ops[operation_id] = {**dict(ops[operation_id]), "state": "attempted"}
        m._AUDIT._state = st._replace(ops=m._readonly(ops))
        return rec
    m._AUDIT.record_terminal = wrong
    return lambda: setattr(m._AUDIT, "record_terminal", real)


def _terminal_reuses_event_id():
    """Publish a terminal event that reuses the attempted event's `event_id` —
    a primary-key collision (round 18, finding 2)."""
    real = m._AUDIT.record_terminal

    def wrong(operation_id, event, payload):
        st = m._AUDIT._state
        att = st.events[(operation_id, "migration_attempted")]
        evs = dict(st.events)
        evs[(operation_id, event)] = {
            "event_id": att["event_id"], "operation_id": operation_id,
            "event": event, **payload}
        ops = dict(st.ops)
        ops[operation_id] = {**dict(ops[operation_id]), "state": "terminal"}
        m._AUDIT._state = st._replace(ops=m._readonly(ops),
                                      events=m._readonly(evs), seq=st.seq + 1)
        return m.TerminalReceipt("recorded", operation_id, event,
                                 audit_committed=True)
    m._AUDIT.record_terminal = wrong
    return lambda: setattr(m._AUDIT, "record_terminal", real)


def _on_committed_false_then_real():
    """Fire a false `current`/(F,F) publication before the genuine
    `migrated`/(T,T) (round 18, finding 3)."""
    real = m._make_on_committed

    def double(state, to_v):
        sink = real(state, to_v)
        fired = []

        def wrap(r):
            if not fired:
                fired.append(1)
                sink(sv.OpenResult("current", store_changed=False,
                                   transaction_committed=False,
                                   resulting_version=to_v))
            return sink(r)
        return wrap
    m._make_on_committed = double
    return lambda: setattr(m, "_make_on_committed", real)


def _terminal_receipt(**over):
    """Publish the real terminal event, then return a receipt overriding chosen
    fields (round 18, finding 4 / correction A)."""
    real = m._AUDIT.record_terminal

    def wrong(operation_id, event, payload):
        real(operation_id, event, payload)
        base = dict(status="recorded", operation_id=operation_id, event=event,
                    audit_committed=True)
        base.update(over)
        return m.TerminalReceipt(base["status"], base["operation_id"],
                                 base["event"], base["audit_committed"])
    m._AUDIT.record_terminal = wrong
    return lambda: setattr(m._AUDIT, "record_terminal", real)


class _HostileStatus:
    def __eq__(self, o):
        raise RuntimeError("hostile __eq__")

    def __ne__(self, o):
        raise RuntimeError("hostile __ne__")


# --- round 19: durable proof over receipts; prior records preserved ----------

def _terminal_deletes_attempted():
    """Publish the terminal event but DELETE the attempted event (round 19,
    correction A: prior records must be preserved through terminalization)."""
    real = m._AUDIT.record_terminal

    def wrong(operation_id, event, payload):
        rec = real(operation_id, event, payload)
        st = m._AUDIT._state
        evs = dict(st.events)
        evs.pop((operation_id, "migration_attempted"), None)
        m._AUDIT._state = st._replace(events=m._readonly(evs))
        return rec
    m._AUDIT.record_terminal = wrong
    return lambda: setattr(m._AUDIT, "record_terminal", real)


def _terminal_mutates_row():
    """Publish the terminal event but rewrite the operation row's store_path and
    add an extra field (round 19, correction A)."""
    real = m._AUDIT.record_terminal

    def wrong(operation_id, event, payload):
        rec = real(operation_id, event, payload)
        st = m._AUDIT._state
        ops = dict(st.ops)
        ops[operation_id] = {**dict(ops[operation_id]),
                             "store_path": "/wrong/store.db", "extra": 1}
        m._AUDIT._state = st._replace(ops=m._readonly(ops))
        return rec
    m._AUDIT.record_terminal = wrong
    return lambda: setattr(m._AUDIT, "record_terminal", real)


def _activate_drops_event_index():
    """Publish the real activation but empty the `event_ids` index, so the
    attempted event's id is not indexed (round 19, correction C)."""
    real = m._AUDIT.activate

    def wrong(a, output_digest):
        r = real(a, output_digest)
        m._AUDIT._state = m._AUDIT._state._replace(event_ids=frozenset())
        return r
    m._AUDIT.activate = wrong
    return lambda: setattr(m._AUDIT, "activate", real)


# --- round 20: strongest durable evidence on the activation path -------------

def _activate_publishes_then_lies():
    """Publish the complete activation, then return an INVALID `activated`
    receipt (round 20, finding 1a)."""
    real = m._AUDIT.activate

    def wrong(a, output_digest):
        real(a, output_digest)
        return m.ActivationReceipt("activated", a.operation_id, False, False)
    m._AUDIT.activate = wrong
    return lambda: setattr(m._AUDIT, "activate", real)


def _activate_publishes_then_raises_false():
    """Publish the complete activation, then raise a contradictory
    `committed=False` (round 20, finding 1b: v22 advertised a safe retry)."""
    real = m._AUDIT.activate

    def wrong(a, output_digest):
        real(a, output_digest)
        raise m.AuditStorageUnavailable("response lost", committed=False)
    m._AUDIT.activate = wrong
    return lambda: setattr(m._AUDIT, "activate", real)


def _terminal_publishes_then_raises_false():
    """Publish the complete terminal transition, then raise a contradictory
    `committed=False` (round 20, finding 2)."""
    real = m._AUDIT.record_terminal

    def wrong(operation_id, event, payload):
        real(operation_id, event, payload)
        raise m.AuditStorageUnavailable("response lost", committed=False)
    m._AUDIT.record_terminal = wrong
    return lambda: setattr(m._AUDIT, "record_terminal", real)


# (id, install -> cleanup, expect(res, exc) -> error message or None)
_INJECTIONS = [
    # --- round 18: the COMPLETE record, both atomic parts, full state ------
    # A malformed attempted EVENT under the right key (round 18 f1).
    ("activate-corrupts-attempted-event",
     _activate_corrupt_attempted,
     _outcome_is("internal-error")),
    # A terminal event with no state transition (round 18 f2).
    ("record_terminal-leaves-state-attempted",
     _terminal_leaves_attempted,
     _write_error_any),
    # A terminal event reusing the attempted event_id (round 18 f2).
    ("record_terminal-reuses-attempted-event-id",
     _terminal_reuses_event_id,
     _write_error_any),
    # A false uncommitted publication suppressing a real commit (round 18 f3).
    ("on_committed-false-current-then-real-migrated",
     _on_committed_false_then_real,
     _outcome_is("internal-error")),
    # A recorded receipt claiming the audit did not commit (round 18 corr A) —
    # AND round 19 finding 1: the exception's audit fact follows the durable
    # transition (which committed), not the lying receipt, so it is True.
    ("record_terminal-recorded-but-not-committed",
     lambda: _terminal_receipt(audit_committed=False),
     _write_error(True)),
    # round 19, correction A: the terminal sink must preserve prior records.
    ("record_terminal-deletes-attempted-event",
     _terminal_deletes_attempted,
     _write_error_any),
    ("record_terminal-rewrites-operation-row",
     _terminal_mutates_row,
     _write_error_any),
    # round 19, correction C: the attempted id must be in the event index.
    ("activate-drops-attempted-id-from-index",
     _activate_drops_event_index,
     _outcome_is("internal-error")),
    # round 20, finding 1: a durable activation with a lying carrier is consumed
    # (internal-error with a terminal event), never left attempted-only.
    ("activate-publishes-then-invalid-receipt",
     _activate_publishes_then_lies,
     _outcome_is("internal-error")),
    ("activate-publishes-then-raises-committed-false",
     _activate_publishes_then_raises_false,
     _outcome_is("internal-error")),
    # round 20, finding 2: a terminal sink exception cannot override a durable
    # commit — the write error carries audit_committed=True.
    ("record_terminal-publishes-then-raises-committed-false",
     _terminal_publishes_then_raises_false,
     _write_error(True)),
    # An un-committable audit flag that the exception constructor rejects (f4).
    ("record_terminal-audit_committed-non-bool",
     lambda: _terminal_receipt(audit_committed=1),
     _write_error_any),
    # A receipt whose status equality raises (round 18 f4).
    ("record_terminal-hostile-status-equality",
     lambda: _terminal_receipt(status=_HostileStatus()),
     _write_error_any),
    # --- round 17: content binding, not just existence ---------------------
    # A row published for a DIFFERENT store than the authority (round 17 f1).
    ("activate-binds-wrong-store",
     _activate_wrong_binding,
     _outcome_is("internal-error")),
    # A terminal event with a DIFFERENT payload than requested (round 17 f2).
    ("record_terminal-wrong-payload",
     _terminal_wrong_payload,
     _write_error_any),
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


# Round 18, correction C: the content gate verified a SUBSET (store_path, the
# terminal outcome, counts). It now verifies the COMPLETE durable state — every
# authority-row field, the attempted-event contents, the operation-row
# terminal transition, and event-ID uniqueness — written FLAT here, NOT through
# the instrument's own binding helpers, so a bug in those helpers cannot hide.

_AUTHORITY_ROW_FIELDS = ("release_ref", "backup_ref", "store_path",
                         "from_version", "to_version", "source_digest",
                         "migration_digest", "evidence_digest",
                         "issued_at", "expires_at")
_ATTEMPTED_FIELDS = {"event_id", "operation_id", "event", "occurred_at"}
_TERMINAL_EVENT_FIELDS = {"event_id", "operation_id", "event", "outcome",
                          "store_changed", "transaction_committed",
                          "resulting_version", "resulting_state", "occurred_at"}


def _is_mapping(x):
    return isinstance(x, (dict, types.MappingProxyType))


def _success_durable_problems(auth, res):
    """A SUCCESS outcome (`migrated`/`current`) must leave a COMPLETE, correct
    durable audit — the whole state, not a subset (round 18, correction C).
    Asserted ONLY for a success: the injected-corruption seams deliberately
    leave bad durable state and the instrument correctly REFUSES (a non-success
    outcome), so integrity is a claim about what a success proves, not about the
    store after a hostile sink ran. Verified here FLAT, not through the
    instrument's binding helpers:

      * the operation row binds EVERY authority field and is `terminal`;
      * the attempted event is complete, bound, and its `occurred_at` matches
        the row (round 18, finding 1);
      * exactly one terminal event, a completed `attempted → terminal`
        transition, with a valid, UNIQUE, non-reused `event_id` (round 18,
        finding 2), the complete field set, and the outcome at the destination.
    """
    events = m._AUDIT._events
    row = m._AUDIT._ops.get(auth.operation_id)
    if not _is_mapping(row):
        return [f"success {res!r} but no operation row"]
    probs = []
    for f in _AUTHORITY_ROW_FIELDS:
        if row.get(f) != getattr(auth, f):
            probs.append(f"row {f}={row.get(f)!r} != authority "
                         f"{getattr(auth, f)!r}")
    # round 19, correction C: the row field set is exactly the schema (no extra
    # fields), and the row is `terminal` for a completed success.
    if set(row) != set(m._AUDIT_OPERATION_FIELDS):
        probs.append(f"row fields {sorted(row)} are not the exact schema")
    if row.get("state") != "terminal":
        probs.append(f"row state={row.get('state')!r} != 'terminal'")
    att = events.get((auth.operation_id, "migration_attempted"))
    if not _is_mapping(att):
        probs.append("no attempted event")
        att = {}
    else:
        if set(att) != _ATTEMPTED_FIELDS:
            probs.append(f"attempted event fields {sorted(att)} incomplete")
        if att.get("operation_id") != auth.operation_id \
                or att.get("event") != "migration_attempted":
            probs.append("attempted event is not bound to this operation")
        if att.get("occurred_at") != row.get("attempted_at"):
            probs.append("attempted occurred_at != row attempted_at")
        # round 19, correction C: the attempted id is in the reference index.
        if att.get("event_id") not in m._AUDIT._state.event_ids:
            probs.append("attempted event_id is absent from the event index")
    terminals = [(k, v) for k, v in events.items()
                 if k[0] == auth.operation_id and k[1] in _TERMINAL_KINDS]
    if len(terminals) != 1:
        probs.append(f"success {res!r} has {len(terminals)} terminal events "
                     f"(must be exactly one)")
    term = events.get((auth.operation_id, "migration_completed"))
    if not _is_mapping(term):
        probs.append(f"success {res!r} but no completed event")
    else:
        if set(term) != _TERMINAL_EVENT_FIELDS:
            probs.append(f"completed event fields {sorted(term)} incomplete")
        eid = term.get("event_id")
        if not (isinstance(eid, str) and m._EVENT_ID_RE.fullmatch(eid)):
            probs.append(f"completed event_id {eid!r} is not the grammar")
        if eid == att.get("event_id"):
            probs.append("completed event_id reuses the attempted event_id")
        # event_id uniqueness across THIS operation's events.
        op_ids = [v.get("event_id") for (k, v) in events.items()
                  if k[0] == auth.operation_id and _is_mapping(v)]
        if len(op_ids) != len(set(op_ids)):
            probs.append("event_id collision within the operation")
        if term.get("outcome") != res or term.get("resulting_state") != \
                "destination":
            probs.append(f"completed event {term.get('outcome')!r}/"
                         f"{term.get('resulting_state')!r} does not match the "
                         f"{res!r} success at the destination")
    return probs


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
    # RECORD COMPLETENESS: an operation never has more than one terminal event
    # (round 16, correction B) — universal, op-scoped.
    n_terminal = sum(1 for (oid, ev) in m._AUDIT._events
                     if oid == auth.operation_id and ev in _TERMINAL_KINDS)
    if n_terminal > 1:
        errors.append(f"{n_terminal} terminal events for one operation")
    # (The "never left attempted-only" property — a durable activation consumed
    # despite a lying carrier still writes its terminal event — is verified by
    # the dedicated instrument regressions, round 20 finding 1: a published-but-
    # corrupted row here is NOT a valid activation, so it is honestly refused
    # without a terminal, which a blanket sweep invariant cannot distinguish.)
    # CONTENT BINDING for a SUCCESS (round 17 corr C; round 18 corr C): the
    # COMPLETE durable state — every authority-row field, the attempted-event
    # contents, the terminal transition, event-ID integrity, the outcome at the
    # destination — not a subset. Asserted only for a success, since the
    # corrupting seams deliberately leave bad state and the instrument REFUSES.
    if res in ("migrated", "current"):
        errors += _success_durable_problems(auth, res)
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
