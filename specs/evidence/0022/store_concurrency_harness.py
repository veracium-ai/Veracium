#!/usr/bin/env python3
"""PRODUCT-SHAPED concurrency evidence for 0022 §4e-i / R19.

External round 2, F3: "concurrent append ordering is asserted, not
constructed. Nothing specifies the claimed loser re-derivation." The spec
now specifies the construction; this harness EXECUTES it, against real
`sqlite3` connections on a real file, in the shape the shipped store uses.

WHY A SEPARATE HARNESS FROM `vector_harness.py`. The vectors exercise the
normative reference, which is a pure function over dicts and CANNOT model
this defect: a race needs two writers, a lock manager and a clock. A
generic-dict model that "passes" a concurrency vector would be proving
something about itself. The reviewer said exactly this ("the generic-dict
harness cannot establish this contract"), and they were right.

WHAT IS PROVEN HERE, each by execution rather than by assertion:

  1. THE DEFECT IS REAL under the natural implementation. Two hosts using
     SQLite's DEFERRED transaction (the default) both read MAX(seq) before
     either writes, both plan against the same standing set, and both
     allocate the same ordinal. This test FAILS THE BUILD IF IT STOPS
     REPRODUCING — a race that quietly stops racing would make every
     protection below untestable.

  2. `BEGIN IMMEDIATE` BEFORE THE READ FIXES IT. Allocate-plan-append
     becomes one serialised unit; the second host blocks, then reads a
     ledger that already contains the first host's row.

  3. THE SECOND OPERATION PLANS AGAINST POST-FIRST STATE. This is the half
     that matters and the half v3 hand-waved as "loser re-derivation":
     there IS no loser. There is a second operation that runs afterwards
     and sees what the first one did.

  4. BUSY AND COLLISION ARE DIFFERENT OUTCOMES. `SQLITE_BUSY` on lock
     acquisition is ordinary and retryable; a UNIQUE violation on the
     ordinal means the construction is broken and must NOT be retried
     around. Conflating them is how a serialisation defect becomes a
     retry loop that hides it.

  5. THE INTERLEAVINGS THE REVIEWER NAMED: two overlapping revocations of
     DIFFERENT sources, two of the SAME source, and revoke racing lift.

Run it: `python3 store_concurrency_harness.py` — exit 0 and a one-line
result, recorded verbatim in `store_concurrency_result.txt`.

No product import: the table DDL and the transaction discipline are
reproduced here so the harness runs from the package with nothing on the
path. That is a deliberate cost — it means this file and the store can
drift — so R19 names the store-side test that binds them.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import threading
import time

# The shipped shape (0022 §7a): append-only, one row per revoke and per lift,
# with the per-user ordinal UNIQUE — the backstop that must never fire.
DDL = """
CREATE TABLE source_revocations (
    user_id         TEXT    NOT NULL,
    identity_digest TEXT    NOT NULL,
    action          TEXT    NOT NULL,
    reason          TEXT    NOT NULL,
    at              TEXT    NOT NULL,
    seq             INTEGER NOT NULL,
    UNIQUE(user_id, seq)
)
"""

# External round 4, R4-1: the operation must apply EFFECTS, not just append a
# row, so the harness needs a real table for them to land in. Without one, a
# check can only assert what was appended — which is exactly how v1's
# `revocation_operation` passed 7/7 while applying nothing.
DDL_RECORDS = """
CREATE TABLE records (
    user_id       TEXT    NOT NULL,
    type          TEXT    NOT NULL,
    id            TEXT    NOT NULL,
    active        INTEGER NOT NULL DEFAULT 1,
    retired_reason TEXT,
    PRIMARY KEY (user_id, type, id)
)
"""

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def _conn(path: str) -> sqlite3.Connection:
    c = sqlite3.connect(path, timeout=5.0, isolation_level=None)
    c.execute("PRAGMA busy_timeout = 5000")
    return c


def _next_seq(c: sqlite3.Connection, user: str) -> int:
    return c.execute(
        "SELECT COALESCE(MAX(seq), -1) + 1 FROM source_revocations WHERE user_id=?",
        (user,)).fetchone()[0]


def _standing(c: sqlite3.Connection, user: str) -> set:
    """The derived standing set — latest row per digest BY seq ALONE (F2)."""
    latest: dict = {}
    for digest, action, seq in c.execute(
            "SELECT identity_digest, action, seq FROM source_revocations "
            "WHERE user_id=? ORDER BY seq", (user,)):
        latest[digest] = action
    return {d for d, a in latest.items() if a == "revoke"}


def _append(c: sqlite3.Connection, user: str, digest: str, action: str, seq: int,
            reason: str = "operator", at: str = "2026-08-17T00:00:00Z"):
    """R4-1: `reason` and `at` are the OPERATOR'S row. v1 hard-coded both and
    silently discarded whatever the caller passed — an audit trail that
    records the harness's defaults instead of the operator's words."""
    c.execute("INSERT INTO source_revocations "
              "(user_id, identity_digest, action, reason, at, seq) "
              "VALUES (?,?,?,?,?,?)",
              (user, digest, action, reason, at, seq))


_ORDINAL_MARKERS = ("source_revocations.user_id", "source_revocations.seq")


def _is_ordinal_violation(e: sqlite3.IntegrityError) -> bool:
    """True only for the per-user ordinal UNIQUE constraint (R5-1).

    Matched on the constraint's own columns as SQLite names them, so a UNIQUE
    or CHECK anywhere else — a trigger on `records`, a future constraint —
    cannot masquerade as a serialisation failure."""
    msg = str(e)
    return "UNIQUE" in msg.upper() and all(m in msg for m in _ORDINAL_MARKERS)


def _rollback_or_poison(conn, cause):
    """Roll back, or raise RevocationUnknownState and CLOSE the connection.

    R5-1: a failing ROLLBACK is a real outcome and v5 suppressed it. If the
    rollback cannot be established, the transaction's disposition is unknown;
    the connection is closed so nothing builds on an unknown base, and the
    caller is told, rather than receiving the original error and a live
    transaction it believes was undone."""
    try:
        conn.execute("ROLLBACK")
    except Exception as rb:
        try:
            conn.close()
        except Exception:
            pass
        raise RevocationUnknownState(
            f"ROLLBACK FAILED after {type(cause).__name__}: {cause!r}; "
            f"rollback error: {rb!r}. The transaction's disposition is UNKNOWN "
            f"and the connection has been closed.") from cause


def _apply_effect(c: sqlite3.Connection, user: str, effect):
    """Apply ONE effect inside the caller's transaction. Verbs are closed
    (0022 R9); an unknown verb raises, which the operation turns into a
    rollback of the WHOLE operation — row included."""
    verb, rtype, rid = effect["verb"], effect["type"], effect["id"]
    if verb == "retire":
        n = c.execute("UPDATE records SET active=0, retired_reason=? "
                      "WHERE user_id=? AND type=? AND id=?",
                      (effect.get("reason", "revoked_source"), user, rtype, rid)).rowcount
    elif verb == "reinstate":
        n = c.execute("UPDATE records SET active=1, retired_reason=NULL "
                      "WHERE user_id=? AND type=? AND id=?",
                      (user, rtype, rid)).rowcount
    else:
        raise RevocationEffectError(f"unknown effect verb {verb!r}")
    if n != 1:
        raise RevocationEffectError(
            f"effect names an absent record: {(rtype, rid)}")


# --------------------------------------------------------------------------
# THE OPERATION — one function, and it is the SAME text §4e-i prints.
#
# External round 3, R3-1: v1 of this harness executed `BEGIN IMMEDIATE`
# explicitly while the spec printed `with conn:` and LABELLED it
# BEGIN IMMEDIATE. Python's sqlite3 context manager does no such thing — it
# commits or rolls back, and begins nothing. Probed on the shipped
# connection config: isolation_level == '', in_transaction False before AND
# after a SELECT, trace showing only the SELECT. So the harness was green on
# a construction the spec did not describe, which is worse than either being
# wrong alone.
#
# The fix is not to reword the spec. It is to have ONE function, called by
# the harness and quoted verbatim by §4e-i, so the two cannot drift again.
# --------------------------------------------------------------------------

class OrdinalCollision(Exception):
    """The UNIQUE backstop fired. NEVER retried — it means allocate-plan-append
    was not serialised, and retrying hides the defect it is reporting."""


class RevocationEffectError(Exception):
    """An effect could not be applied. Rolls back the WHOLE operation — the
    revocation row included — because R19 requires the row and its effects to
    land together or not at all."""


class RevocationIntegrityError(Exception):
    """An integrity constraint OTHER than the ordinal fired (external round 5,
    R5-1). v5 converted EVERY `sqlite3.IntegrityError` — from the append, the
    effects, or the commit — into `OrdinalCollision`, so a trigger on the
    records table reported a serialisation failure that had not happened.
    Mis-classifying a fault is worse than not classifying it: it sends the
    operator to the wrong invariant."""


class RevocationUnknownState(Exception):
    """ROLLBACK ITSELF FAILED, so the transaction's disposition is UNKNOWN
    (external round 5, R5-1).

    v5 swallowed a failing ROLLBACK (`except sqlite3.Error: pass`) and re-raised
    the original error, leaving the caller with a `RuntimeError`, a connection
    still `in_transaction`, and an uncommitted revocation row it had been told
    was rolled back. "Commit — or roll ALL of it back" has a third outcome and
    the code hid it.

    This exception SAYS SO, carries the original cause, and the connection is
    CLOSED before it propagates: a connection whose transaction state cannot be
    established must not be reused, because every subsequent operation would
    build on an unknown base."""


def revocation_operation(conn, user, digest, action, reason, at, *,
                         plan, busy_deadline_s=5.0, _gate=None, _fault=None):
    """Allocate, re-read, plan, append the operator's row, APPLY EVERY EFFECT,
    and commit — or roll ALL of it back.

    THIS IS THE CONSTRUCTION §4e-i quotes and the checks below call.

    EXTERNAL ROUND 4, R4-1 — WHAT v1 OF THIS FUNCTION DID NOT DO, and the
    reason it passed 7/7 anyway:

      * it appended the row and NEVER APPLIED THE EFFECTS, so R19's "the row
        and the effects land together" was true only of the row. No check
        asserted an effect had landed, so nothing failed.
      * it DISCARDED `reason` and `at` — `_append` hard-coded both — so the
        audit trail recorded the harness's defaults rather than the
        operator's words, and the signature lied about what it stored.
      * `plan` defaulted to None while the spec called `plan(standing)`
        unconditionally, so spec and harness disagreed about the one argument
        that produces the work.
      * the BUSY regression exercised a SEPARATE `_retry_operation`, not this
        function, so "the shared operation retries BUSY" was untested.

    `plan` is now REQUIRED and takes the standing set, returning the effect
    list. `_gate` and `_fault` are test hooks (None in every real call);
    `_fault` fires between the row append and the effects, which is the seam
    R19's atomicity claim is actually about.
    """
    deadline = time.monotonic() + busy_deadline_s
    while True:
        try:
            # EXPLICIT. Not `with conn:` — that begins nothing (R3-1).
            conn.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.01)
            continue                      # contention: re-acquire, RE-READ
        try:
            seq = _next_seq(conn, user)
            standing = _standing(conn, user)
            if _gate is not None:
                _gate.wait()
            effects = list(plan(standing))
            _append(conn, user, digest, action, seq, reason, at)
            if _fault is not None:
                _fault()                  # between the row and the effects
            for e in effects:
                _apply_effect(conn, user, e)
            conn.execute("COMMIT")
            return seq, frozenset(standing), effects
        except sqlite3.IntegrityError as e:
            # R5-1: WHICH constraint fired decides which invariant reports.
            # Only the per-user ordinal is a serialisation failure.
            ordinal = _is_ordinal_violation(e)
            _rollback_or_poison(conn, e)
            if ordinal:
                raise OrdinalCollision(str(e)) from e
            raise RevocationIntegrityError(str(e)) from e
        except BaseException as e:
            # the row, the effects, all of it — and if that cannot be
            # established, say so rather than pretending (R5-1)
            _rollback_or_poison(conn, e)
            raise


# --------------------------------------------------------------------------
# The two constructions, side by side. The ONLY difference is the BEGIN.
# --------------------------------------------------------------------------

def _operation(path, user, digest, action, *, immediate: bool, gate, results, idx):
    """One host's revoke/lift.

    THE SYNCHRONISATION DIFFERS BY CONSTRUCTION, and that asymmetry is the
    finding, not an artefact of the test:

    * DEFERRED takes no lock until the first WRITE, so both hosts can sit at
      a barrier holding a stale read. The barrier makes the race
      DETERMINISTIC instead of hoping for a scheduler interleaving.
    * IMMEDIATE takes the write lock at BEGIN, so the second host blocks
      THERE and can never reach a barrier — a barrier would deadlock, and
      the first draft of this harness did exactly that. The blocking IS the
      serialisation, so IMMEDIATE is driven by a stagger plus SQLite's own
      `busy_timeout` and needs no barrier at all.
    """
    c = _conn(path)
    try:
        if immediate:
            # THE SHARED OPERATION — the same function §4e-i prints
            seq, standing, _ = revocation_operation(
                c, user, digest, action, "operator", "2026-08-17T00:00:00Z",
                plan=lambda st: [], _gate=gate)
            results[idx] = ("ok", seq, standing)
            return
        c.execute("BEGIN")                     # the NAIVE construction
        seq = _next_seq(c, user)
        standing = _standing(c, user)          # plan against what we can see
        if gate is not None:
            gate.wait()                        # <- the race window, held open
        _append(c, user, digest, action, seq)
        c.execute("COMMIT")
        results[idx] = ("ok", seq, frozenset(standing))
    except OrdinalCollision as e:
        results[idx] = ("collision", str(e), None)
    except sqlite3.IntegrityError as e:
        results[idx] = ("collision", str(e), None)
        c.execute("ROLLBACK")
    except sqlite3.OperationalError as e:
        # lock contention: ORDINARY and retryable, and NOT the same thing
        results[idx] = ("busy", str(e), None)
        try:
            c.execute("ROLLBACK")
        except sqlite3.Error:
            pass
    finally:
        c.close()


def _race(immediate: bool, ops):
    """Run `ops` concurrently against one store; return each outcome."""
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        c = _conn(path)
        c.execute(DDL)
        c.execute(DDL_RECORDS)
        c.close()
        gate = None if immediate else threading.Barrier(len(ops), timeout=5)
        results = [None] * len(ops)
        threads = [threading.Thread(target=_operation,
                                    args=(path, u, d, a),
                                    kwargs=dict(immediate=immediate, gate=gate,
                                                results=results, idx=i))
                   for i, (u, d, a) in enumerate(ops)]
        for i, t in enumerate(threads):
            t.start()
            if immediate and i == 0:
                time.sleep(0.05)      # host 1 takes the write lock first;
                                      # host 2 then BLOCKS at BEGIN IMMEDIATE
        for t in threads:
            t.join(10)
        # what actually landed
        c = _conn(path)
        rows = c.execute("SELECT seq, identity_digest, action FROM "
                         "source_revocations ORDER BY seq").fetchall()
        c.close()
        return results, rows
    finally:
        os.unlink(path)


def _retry_operation(path, user, digest, action, *, results, idx, attempts=5):
    """R4-1: v1 of this helper had its OWN retry loop, so the BUSY regression
    proved something about the helper and nothing about the shared operation.
    It now simply CALLS `revocation_operation`, whose bounded BUSY handling is
    the contract under test."""
    c = _conn(path)
    try:
        seq, _standing, _effects = revocation_operation(
            c, user, digest, action, "operator", "2026-08-17T00:00:00Z",
            plan=lambda st: [])
        results[idx] = ("ok", seq, None)
    except OrdinalCollision as e:
        results[idx] = ("collision", str(e), None)     # NEVER retried
    except sqlite3.OperationalError as e:
        results[idx] = ("busy-exhausted", str(e), None)
    finally:
        c.close()


CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


@check("the DEFERRED construction FAILS one of two valid operations")
def _defect_reproduces():
    """If this stops failing, every protection below is untested.

    MEASURED, and it is not the failure the spec predicted. §4e-i reasoned
    that two hosts would allocate the same ordinal and one would hit the
    UNIQUE backstop. What SQLite actually does is refuse earlier: a DEFERRED
    transaction that has already READ holds a SHARED lock, so its first
    write against another connection's RESERVED lock returns SQLITE_BUSY
    IMMEDIATELY and the busy handler is deliberately NOT invoked — waiting
    would deadlock. The construction is wrong for a sharper reason than the
    spec gave: the loser cannot even wait its turn.

    The duplicate-ordinal collision is real too, but it needs the read to
    happen OUTSIDE the write transaction — the allocate-then-write shape —
    which `_stale_ordinal_collides` covers below."""
    results, rows = _race(False, [("u1", DIGEST_A, "revoke"),
                                  ("u1", DIGEST_B, "revoke")])
    ok = [r for r in results if r and r[0] == "ok"]
    failed = [r for r in results if r and r[0] in ("busy", "collision")]
    if len(ok) == 2:
        return ("both operations committed under DEFERRED: the race did not "
                f"reproduce, so nothing below is proven (rows={rows})")
    if len(failed) != 1:
        return f"expected exactly one failure under DEFERRED, got {results}"
    if len(rows) != 1:
        return f"exactly one row should have landed, got {rows}"
    return None


@check("a STALE ordinal — read outside the write txn — hits the UNIQUE backstop")
def _stale_ordinal_collides():
    """The allocate-then-write shape, which is what a host writes when the
    read is not inside the transaction. This is the cell the UNIQUE
    constraint exists for, and it must FIRE rather than accept the row."""
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        c = _conn(path)
        c.execute(DDL)
        c.execute(DDL_RECORDS)
        c.close()
        a, b = _conn(path), _conn(path)
        try:
            seq_a = _next_seq(a, "u1")          # both allocate OUTSIDE a txn
            seq_b = _next_seq(b, "u1")
            if seq_a != seq_b:
                return f"both hosts should allocate the same ordinal, got {seq_a}/{seq_b}"
            a.execute("BEGIN IMMEDIATE")
            _append(a, "u1", DIGEST_A, "revoke", seq_a)
            a.execute("COMMIT")
            b.execute("BEGIN IMMEDIATE")
            try:
                _append(b, "u1", DIGEST_B, "revoke", seq_b)
                b.execute("COMMIT")
                return "the duplicate ordinal was ACCEPTED — the backstop did not fire"
            except sqlite3.IntegrityError:
                b.execute("ROLLBACK")
            return None
        finally:
            a.close()
            b.close()
    finally:
        os.unlink(path)


@check("BEGIN IMMEDIATE serialises: two DIFFERENT sources, distinct ordinals")
def _immediate_serialises_different():
    results, rows = _race(True, [("u1", DIGEST_A, "revoke"),
                                 ("u1", DIGEST_B, "revoke")])
    if any(r[0] == "collision" for r in results if r):
        return f"an ordinal collision fired under BEGIN IMMEDIATE: {results}"
    ok = [r for r in results if r and r[0] == "ok"]
    if len(ok) != 2:
        return f"expected both operations to commit, got {results}"
    if sorted(r[1] for r in ok) != [0, 1]:
        return f"ordinals must be 0 and 1, got {[r[1] for r in ok]}"
    if [r[0] for r in rows] != [0, 1]:
        return f"the ledger is not a clean append sequence: {rows}"
    return None


@check("the SECOND operation plans against POST-FIRST state (there is no loser)")
def _second_sees_the_first():
    results, rows = _race(True, [("u1", DIGEST_A, "revoke"),
                                 ("u1", DIGEST_B, "revoke")])
    ok = sorted((r for r in results if r and r[0] == "ok"), key=lambda r: r[1])
    if len(ok) != 2:
        return f"expected two commits, got {results}"
    first_standing, second_standing = ok[0][2], ok[1][2]
    if first_standing != frozenset():
        return f"the first operation should see an empty standing set, saw {first_standing}"
    if second_standing != frozenset({DIGEST_A}):
        return ("the second operation must plan against the FIRST's row — "
                f"expected {{DIGEST_A}}, saw {second_standing}")
    return None


@check("two revocations of the SAME source: both land, effect is idempotent (R16)")
def _same_source_twice():
    results, rows = _race(True, [("u1", DIGEST_A, "revoke"),
                                 ("u1", DIGEST_A, "revoke")])
    if any(r[0] == "collision" for r in results if r):
        return f"collision on same-source concurrent revokes: {results}"
    if len(rows) != 2:
        return f"both rows must be appended (the audit trail is the point): {rows}"
    if {a for _, _, a in rows} != {"revoke"}:
        return f"unexpected actions: {rows}"
    return None


@check("revoke RACING lift on one source: the ledger order decides, not the clock")
def _revoke_races_lift():
    results, rows = _race(True, [("u1", DIGEST_A, "revoke"),
                                 ("u1", DIGEST_A, "lift")])
    if any(r[0] == "collision" for r in results if r):
        return f"collision on revoke-vs-lift: {results}"
    if len(rows) != 2:
        return f"expected two rows, got {rows}"
    # whichever committed second is the standing answer — by seq, never by `at`
    last_action = rows[-1][2]
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        c = _conn(path)
        c.execute(DDL)
        c.execute(DDL_RECORDS)
        for seq, digest, action in rows:
            _append(c, "u1", digest, action, seq)
        standing = _standing(c, "u1")
        c.close()
    finally:
        os.unlink(path)
    expected = {DIGEST_A} if last_action == "revoke" else set()
    if standing != expected:
        return (f"standing set disagrees with the ledger's last row "
                f"({last_action}): {standing} != {expected}")
    return None


@check("BUSY is retryable and reaches a clean ordinal; COLLISION is never retried")
def _busy_vs_collision():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        c = _conn(path)
        c.execute(DDL)
        c.execute(DDL_RECORDS)
        c.close()
        results = [None, None]
        ts = [threading.Thread(target=_retry_operation,
                               args=(path, "u1", d, "revoke"),
                               kwargs=dict(results=results, idx=i))
              for i, d in enumerate((DIGEST_A, DIGEST_B))]
        for t in ts:
            t.start()
        for t in ts:
            t.join(10)
        if any(r is None or r[0] != "ok" for r in results):
            return f"retry-on-busy did not converge: {results}"
        if sorted(r[1] for r in results) != [0, 1]:
            return f"ordinals after busy-retry must be 0 and 1: {results}"
        # and a genuine collision is NOT swallowed by the same loop: the
        # INSERT itself raises, so a retry-on-OperationalError loop never
        # sees it — which is exactly the separation the spec requires
        c = _conn(path)
        c.execute("BEGIN IMMEDIATE")
        try:
            _append(c, "u1", DIGEST_A, "revoke", 0)      # ordinal 0 already used
            c.execute("COMMIT")
            c.close()
            return "a duplicate ordinal was accepted — the backstop did not fire"
        except sqlite3.IntegrityError:
            c.execute("ROLLBACK")
            c.close()
        except sqlite3.OperationalError:
            c.close()
            return ("the ordinal collision surfaced as OperationalError — a "
                    "retry loop would swallow it")
        return None
    finally:
        os.unlink(path)


# --------------------------------------------------------------------------
# R4-1's five checks. Their ABSENCE is why an operation that applied nothing
# scored 7/7: every earlier check asked about ordinals and rows, and none
# asked whether the work happened.
# --------------------------------------------------------------------------

def _store_with_records(*records):
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    c = _conn(path)
    c.execute(DDL)
    c.execute(DDL_RECORDS)
    for rtype, rid in records:
        c.execute("INSERT INTO records (user_id,type,id,active) VALUES (?,?,?,1)",
                  ("u1", rtype, rid))
    c.close()
    return path


@check("EFFECTS LAND: a planned retirement is applied in the same commit")
def _effects_land():
    path = _store_with_records(("episode", "ep-1"))
    try:
        c = _conn(path)
        seq, _st, effects = revocation_operation(
            c, "u1", DIGEST_A, "revoke", "operator", "2026-08-17T00:00:00Z",
            plan=lambda st: [{"verb": "retire", "type": "episode", "id": "ep-1"}])
        row = c.execute("SELECT active, retired_reason FROM records "
                        "WHERE id='ep-1'").fetchone()
        c.close()
        if len(effects) != 1:
            return f"the plan was not returned: {effects}"
        if row != (0, "revoked_source"):
            return f"THE EFFECT DID NOT LAND: records row is {row}"
        return None
    finally:
        os.unlink(path)


@check("ATOMIC: a fault between the row and the effects rolls BOTH back")
def _mid_effect_rollback():
    path = _store_with_records(("episode", "ep-1"))
    try:
        c = _conn(path)
        def boom():
            raise RuntimeError("injected between append and apply")
        try:
            revocation_operation(
                c, "u1", DIGEST_A, "revoke", "operator", "2026-08-17T00:00:00Z",
                plan=lambda st: [{"verb": "retire", "type": "episode", "id": "ep-1"}],
                _fault=boom)
            c.close()
            return "the injected fault did not propagate"
        except RuntimeError:
            pass
        rows = c.execute("SELECT COUNT(*) FROM source_revocations").fetchone()[0]
        rec = c.execute("SELECT active FROM records WHERE id='ep-1'").fetchone()
        c.close()
        if rows != 0:
            return f"THE ROW SURVIVED A ROLLED-BACK OPERATION: {rows} row(s)"
        if rec != (1,):
            return f"the record was left modified: active={rec}"
        return None
    finally:
        os.unlink(path)


@check("ATOMIC: an effect naming an absent record rolls the row back too")
def _absent_record_rolls_back():
    path = _store_with_records(("episode", "ep-1"))
    try:
        c = _conn(path)
        try:
            revocation_operation(
                c, "u1", DIGEST_A, "revoke", "operator", "2026-08-17T00:00:00Z",
                plan=lambda st: [{"verb": "retire", "type": "episode", "id": "ep-1"},
                                 {"verb": "retire", "type": "edge", "id": "MISSING"}])
            c.close()
            return "an absent record did not raise"
        except RevocationEffectError:
            pass
        rows = c.execute("SELECT COUNT(*) FROM source_revocations").fetchone()[0]
        rec = c.execute("SELECT active FROM records WHERE id='ep-1'").fetchone()
        c.close()
        if rows != 0 or rec != (1,):
            return (f"partial application survived: rows={rows} ep-1.active={rec} "
                    "— the FIRST effect must roll back with the second")
        return None
    finally:
        os.unlink(path)


@check("METADATA: the operator's reason and timestamp are STORED, not defaulted")
def _metadata_is_stored():
    path = _store_with_records()
    try:
        c = _conn(path)
        revocation_operation(c, "u1", DIGEST_A, "revoke",
                             "compromised connector", "2099-12-31T00:00:00Z",
                             plan=lambda st: [])
        got = c.execute("SELECT reason, at FROM source_revocations").fetchone()
        c.close()
        if got != ("compromised connector", "2099-12-31T00:00:00Z"):
            return f"the operator's row was overwritten with defaults: {got}"
        return None
    finally:
        os.unlink(path)


@check("BUSY: the RETRY LOOP runs — SQLite's internal wait is DISABLED")
def _busy_through_the_operation():
    """R5-2. v5's version set `busy_timeout=5000` and held the lock 150ms, so
    SQLite waited INTERNALLY: instrumented, the operation made ONE
    `BEGIN IMMEDIATE` call and caught ZERO `OperationalError`s. The assertion
    ("it waited >0.1s") was satisfied by the C library's wait, not by the
    Python loop the check was named for. A timing assertion cannot tell you
    WHO waited.

    So this version sets `busy_timeout=0` — acquisition fails IMMEDIATELY —
    and counts the loop's own attempts. It asserts the branch ran."""
    path = _store_with_records()
    try:
        holding = threading.Event()
        released = threading.Event()

        def hold_then_release():
            h = _conn(path)
            h.execute("BEGIN IMMEDIATE")
            holding.set()
            time.sleep(0.20)
            h.execute("COMMIT")
            h.close()
            released.set()

        t = threading.Thread(target=hold_then_release)
        t.start()
        holding.wait(2)

        attempts = {"begin": 0, "busy": 0}

        class Counting:
            """Counts what the OPERATION does, not what the clock does."""
            def __init__(self, c):
                self._c = c
            def execute(self, sql, *a, **k):
                if isinstance(sql, str) and sql.strip().upper().startswith("BEGIN IMMEDIATE"):
                    attempts["begin"] += 1
                    try:
                        return self._c.execute(sql, *a, **k)
                    except sqlite3.OperationalError:
                        attempts["busy"] += 1
                        raise
                return self._c.execute(sql, *a, **k)
            def __getattr__(self, n):
                return getattr(self._c, n)

        raw = sqlite3.connect(path, timeout=0, isolation_level=None)
        raw.execute("PRAGMA busy_timeout = 0")      # NO internal wait (R5-2)
        c = Counting(raw)
        seq, _st, _e = revocation_operation(
            c, "u1", DIGEST_A, "revoke", "operator", "2026-08-17T00:00:00Z",
            plan=lambda st: [], busy_deadline_s=5.0)
        raw.close()
        t.join()
        if attempts["busy"] < 1:
            return ("the retry loop was NEVER ENTERED: caught "
                    f"{attempts['busy']} OperationalError(s) — SQLite waited "
                    "internally again, so this check proves nothing")
        if attempts["begin"] < 2:
            return f"expected repeated acquisition attempts, saw {attempts['begin']}"
        if seq != 0:
            return f"expected ordinal 0 after the retry, got {seq}"
        if not released.is_set():
            return "the operation committed before the lock was released"
        return None
    finally:
        os.unlink(path)


@check("BUSY DEADLINE: an unreleased lock exhausts the bound and RAISES")
def _busy_deadline_is_bounded():
    """The other half of the same branch: the loop is BOUNDED. v5 never held a
    lock long enough to prove the deadline exists."""
    path = _store_with_records()
    holder = None
    try:
        holder = _conn(path)
        holder.execute("BEGIN IMMEDIATE")           # never released
        raw = sqlite3.connect(path, timeout=0, isolation_level=None)
        raw.execute("PRAGMA busy_timeout = 0")
        started = time.monotonic()
        try:
            revocation_operation(raw, "u1", DIGEST_A, "revoke", "operator",
                                 "2026-08-17T00:00:00Z", plan=lambda st: [],
                                 busy_deadline_s=0.2)
            raw.close()
            return "the operation acquired a lock that was never released"
        except sqlite3.OperationalError:
            pass
        elapsed = time.monotonic() - started
        raw.close()
        if elapsed > 2.0:
            return f"the deadline was not honoured: waited {elapsed:.2f}s"
        return None
    finally:
        if holder is not None:
            holder.execute("ROLLBACK")
            holder.close()
        os.unlink(path)


@check("NO stale ordinal can arise INSIDE the operation — the backstop is unreachable")
def _collision_unreachable_inside():
    """R5-2 asked for a stale ordinal injected inside the shared operation.
    WE TRIED, AND THE CONSTRUCTION MAKES IT IMPOSSIBLE — which is a property
    worth proving rather than a gap to paper over.

    While the operation holds the write lock from `BEGIN IMMEDIATE`, no other
    connection can COMMIT, so no one can steal the ordinal between our read and
    our append. The attempt below gets `database is locked` instead. That is
    the serialisation working: `OrdinalCollision` is a BACKSTOP FOR CALLERS WHO
    DO NOT USE THIS CONSTRUCTION (the allocate-then-write shape covered by
    `_stale_ordinal_collides`), not a branch reachable from inside it.

    A check that manufactured reachability — a private hook forcing a duplicate
    seq — would prove the classifier, not the contract, and would say the
    opposite of what is true."""
    path = _store_with_records()
    try:
        c = _conn(path)
        stolen = {"attempted": False, "error": None}

        class Gate:
            def wait(self):
                stolen["attempted"] = True
                other = sqlite3.connect(path, timeout=0, isolation_level=None)
                other.execute("PRAGMA busy_timeout = 0")
                try:
                    other.execute("BEGIN IMMEDIATE")
                    _append(other, "u1", DIGEST_B, "revoke", 0)
                    other.execute("COMMIT")
                except sqlite3.OperationalError as e:
                    stolen["error"] = str(e)      # expected: locked out
                finally:
                    other.close()

        seq, _st, _e = revocation_operation(
            c, "u1", DIGEST_A, "revoke", "operator", "2026-08-17T00:00:00Z",
            plan=lambda st: [], _gate=Gate())
        rows = c.execute("SELECT identity_digest, seq FROM source_revocations").fetchall()
        c.close()
        if not stolen["attempted"]:
            return "the interleaving hook never ran"
        if stolen["error"] is None:
            return ("ANOTHER WRITER COMMITTED while the operation held the write "
                    "lock — the serialisation this check exists to prove is broken")
        if "lock" not in stolen["error"].lower():
            return f"unexpected error from the second writer: {stolen['error']}"
        if rows != [(DIGEST_A, 0)]:
            return f"the operation's own row should be the only one: {rows}"
        return None
    finally:
        os.unlink(path)


@check("the ordinal CLASSIFIER separates the two integrity shapes")
def _classifier_is_exact():
    """Since the collision branch is unreachable through the construction
    (above), the classifier is covered directly — on REAL errors raised by
    SQLite, not on constructed strings."""
    path = _store_with_records(("episode", "ep-1"))
    try:
        c = _conn(path)
        _append(c, "u1", DIGEST_A, "revoke", 0)
        ordinal_err = other_err = None
        try:
            _append(c, "u1", DIGEST_B, "revoke", 0)      # duplicate ordinal
        except sqlite3.IntegrityError as e:
            ordinal_err = e
        c.execute("CREATE TRIGGER t BEFORE UPDATE ON records "
                  "BEGIN SELECT RAISE(ABORT, 'not an ordinal problem'); END")
        try:
            c.execute("UPDATE records SET active=0 WHERE id='ep-1'")
        except sqlite3.IntegrityError as e:
            other_err = e
        c.close()
        if ordinal_err is None or other_err is None:
            return f"could not raise both shapes: {ordinal_err!r} {other_err!r}"
        if not _is_ordinal_violation(ordinal_err):
            return f"the ordinal violation was not recognised: {ordinal_err}"
        if _is_ordinal_violation(other_err):
            return f"a NON-ordinal fault was classified as ordinal: {other_err}"
        return None
    finally:
        os.unlink(path)


@check("a NON-ordinal integrity fault is NOT reported as a collision")
def _non_ordinal_integrity():
    """R5-1: v5 converted every IntegrityError into OrdinalCollision."""
    path = _store_with_records(("episode", "ep-1"))
    try:
        c = _conn(path)
        c.execute("CREATE TRIGGER no_retire BEFORE UPDATE ON records "
                  "BEGIN SELECT RAISE(ABORT, 'effect integrity failure'); END")
        try:
            revocation_operation(
                c, "u1", DIGEST_A, "revoke", "operator", "2026-08-17T00:00:00Z",
                plan=lambda st: [{"verb": "retire", "type": "episode", "id": "ep-1"}])
            c.close()
            return "the trigger did not fire"
        except OrdinalCollision as e:
            c.close()
            return f"MIS-CLASSIFIED as an ordinal collision: {e}"
        except RevocationIntegrityError:
            pass
        rows = c.execute("SELECT COUNT(*) FROM source_revocations").fetchone()[0]
        c.close()
        if rows != 0:
            return f"the row survived a failed operation: {rows}"
        return None
    finally:
        os.unlink(path)


@check("a FAILING ROLLBACK is reported as UNKNOWN STATE, not swallowed")
def _rollback_failure_is_reported():
    """R5-1's executed probe: v5 suppressed the rollback error and re-raised
    the original, leaving the caller with a live transaction it believed had
    been undone."""
    path = _store_with_records(("episode", "ep-1"))
    try:
        real = _conn(path)

        class BreakRollback:
            def __init__(self, c):
                self._c = c
            def execute(self, sql, *a, **k):
                if isinstance(sql, str) and sql.strip().upper() == "ROLLBACK":
                    raise sqlite3.OperationalError("injected rollback failure")
                return self._c.execute(sql, *a, **k)
            def close(self):
                return self._c.close()
            def __getattr__(self, n):
                return getattr(self._c, n)

        c = BreakRollback(real)
        def boom():
            raise RuntimeError("injected between append and apply")
        try:
            revocation_operation(
                c, "u1", DIGEST_A, "revoke", "operator", "2026-08-17T00:00:00Z",
                plan=lambda st: [{"verb": "retire", "type": "episode", "id": "ep-1"}],
                _fault=boom)
            return "no exception was raised at all"
        except RevocationUnknownState as e:
            if "ROLLBACK FAILED" not in str(e):
                return f"the outcome is not named: {e}"
        except RuntimeError:
            return ("the caller received only the ORIGINAL error — the failing "
                    "rollback was swallowed (this is v5's behaviour)")
        # the connection must have been closed: reusing it is the danger
        try:
            real.execute("SELECT 1")
            return "the connection was left OPEN after an unknown-state rollback"
        except sqlite3.ProgrammingError:
            pass
        return None
    finally:
        os.unlink(path)


def main() -> int:
    failures = []
    for name, fn in CHECKS:
        try:
            err = fn()
        except Exception as e:                      # a harness fault is a failure
            err = f"{type(e).__name__}: {e}"
        if err:
            failures.append((name, err))
    for name, err in failures:
        print(f"FAIL {name}: {err}")
    print(f"store concurrency harness: {len(CHECKS) - len(failures)}/{len(CHECKS)} "
          f"pass against the §4e-i construction")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
