"""specs/0022 §4e-i — the R19 revocation operation, against the product store.

The construction is the one the spec prints and the concurrency harness proves
(`specs/evidence/0022/store_concurrency_harness.py`, 18 checks): allocate,
re-read, plan, append the operator's row, APPLY EVERY EFFECT, and commit — or
roll ALL of it back. `BEGIN IMMEDIATE`, never `with conn:` (round 2, R3-1: it
begins nothing); the ordinal from `MAX(seq)` INSIDE the transaction; failure
outcomes TOTAL (round 5, R5-1) with `BaseException` on both boundaries
(round 6, R6-1).

`plan` and `apply_effect` are REQUIRED. Round 4's R4-1 found a version of this
operation that appended the row and never applied the effects — and passed,
because nothing asserted an effect had landed. Making the plan an argument the
operation cannot default away is what makes that defect unrepresentable: the
sweep (0022 §4b) is the production planner, and until it lands nothing else
can call this without saying what the effects are.
"""
from __future__ import annotations

import sqlite3
import time

# The per-user append ordinal's own columns, as SQLite names them in the
# UNIQUE/PK violation message. Matched on BOTH so a UNIQUE or CHECK anywhere
# else — a trigger, a future constraint — cannot masquerade as a
# serialisation failure (R5-1).
_ORDINAL_MARKERS = ("source_revocations.user_id", "source_revocations.seq")


class OrdinalCollision(Exception):
    """The UNIQUE backstop fired. NEVER retried — it means
    allocate-plan-append was not serialised, and retrying hides the defect it
    is reporting."""


class RevocationEffectError(Exception):
    """An effect could not be applied. Rolls back the WHOLE operation — the
    revocation row included — because R19 requires the row and its effects to
    land together or not at all."""


class RevocationIntegrityError(Exception):
    """An integrity constraint OTHER than the ordinal fired (R5-1).
    Mis-classifying a fault is worse than not classifying it: it sends the
    operator to the wrong invariant."""


class RevocationUnknownState(Exception):
    """ROLLBACK ITSELF FAILED, so the transaction's disposition is UNKNOWN
    (R5-1). The connection is CLOSED before this propagates: a connection
    whose transaction state cannot be established must not be reused."""


def _is_ordinal_violation(e: sqlite3.IntegrityError) -> bool:
    msg = str(e)
    return "UNIQUE" in msg.upper() and all(m in msg for m in _ORDINAL_MARKERS)


def _rollback_or_poison(conn, cause):
    """Roll back, or raise RevocationUnknownState and CLOSE the connection.

    BaseException, NOT Exception (R6-1): the operation catches BaseException,
    and the two boundaries must be the SAME boundary or the narrower one is a
    hole in the wider one's guarantee."""
    try:
        conn.execute("ROLLBACK")
    except BaseException as rb:
        try:
            conn.close()
        except BaseException:
            pass
        raise RevocationUnknownState(
            f"ROLLBACK failed after {type(cause).__name__}; the transaction's "
            f"disposition is unknown and the connection is closed") from rb


def standing_revocations(conn, user_id: str) -> frozenset:
    """The standing revoked set: latest row per identity_digest by seq ALONE.

    `at` is host-supplied audit metadata and ORDERS NOTHING (round 1, F2: a
    planted far-future timestamp must not make a revocation permanent — the
    append order is a fact, a clock is an input)."""
    latest: dict = {}
    for digest, action, seq in conn.execute(
            "SELECT identity_digest, action, seq FROM source_revocations "
            "WHERE user_id=? ORDER BY seq", (user_id,)):
        latest[digest] = action                    # seq-ordered: last wins
    return frozenset(d for d, a in latest.items() if a == "revoke")


def revocation_operation(conn, user_id: str, identity_digest: str,
                         action: str, reason: str, at: str, *,
                         plan, apply_effect, busy_deadline_s: float = 5.0,
                         _gate=None, _fault=None):
    """Allocate, re-read, plan, append, APPLY EVERY EFFECT, commit — or roll
    ALL of it back. Returns (seq, standing_before, effects).

    THE SOLE WRITER of `source_revocations` (the R19 product-binding gate
    sweeps for writers and holds each to this construction). `_gate`/`_fault`
    are test hooks, None in every real call; `_fault` fires between the row
    append and the effects — the seam R19's atomicity claim is about."""
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
            # the ordinal, from MAX(seq), INSIDE the transaction (R19)
            seq = 1 + (conn.execute(
                "SELECT COALESCE(MAX(seq), -1) FROM source_revocations "
                "WHERE user_id=?", (user_id,)).fetchone()[0])
            standing = standing_revocations(conn, user_id)
            if _gate is not None:
                _gate.wait()
            effects = list(plan(standing))
            conn.execute(
                "INSERT INTO source_revocations(user_id, seq, identity_digest,"
                " action, at, reason) VALUES(?,?,?,?,?,?)",
                (user_id, seq, identity_digest, action, at, reason))
            if _fault is not None:
                _fault()                  # between the row and the effects
            for e in effects:
                apply_effect(conn, e)
            conn.execute("COMMIT")
            return seq, standing, effects
        except sqlite3.IntegrityError as e:
            # WHICH constraint fired decides which invariant reports (R5-1).
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
