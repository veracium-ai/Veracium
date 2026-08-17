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


def _append(c: sqlite3.Connection, user: str, digest: str, action: str, seq: int):
    c.execute("INSERT INTO source_revocations "
              "(user_id, identity_digest, action, reason, at, seq) "
              "VALUES (?,?,?,?,?,?)",
              (user, digest, action, "operator", "2026-08-17T00:00:00Z", seq))


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
        c.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        seq = _next_seq(c, user)
        standing = _standing(c, user)          # plan against what we can see
        if gate is not None:
            gate.wait()                        # <- the race window, held open
        _append(c, user, digest, action, seq)
        c.execute("COMMIT")
        results[idx] = ("ok", seq, frozenset(standing))
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
    """The ONLY retry the spec permits: retry BUSY, never retry a collision."""
    for _ in range(attempts):
        c = _conn(path)
        try:
            c.execute("BEGIN IMMEDIATE")
            seq = _next_seq(c, user)
            _append(c, user, digest, action, seq)
            c.execute("COMMIT")
            results[idx] = ("ok", seq, None)
            return
        except sqlite3.OperationalError:
            time.sleep(0.02)                   # busy: back off and re-read
            continue
        except sqlite3.IntegrityError as e:
            results[idx] = ("collision", str(e), None)   # NEVER retried
            return
        finally:
            c.close()
    results[idx] = ("busy-exhausted", None, None)


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
