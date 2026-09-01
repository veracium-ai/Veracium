"""Seam model — the 0029 ALLOCATION SCHEDULE, executable (round-3 F4).

The finding: "max+1 inside the write transaction" never said WHEN the writer
lock is acquired. Under SQLite's default DEFERRED transactions the lock
arrives at the first write, so two connections both read the same maxima and
the second dies `database is locked` mid-batch — the reviewer reproduced it,
and this model keeps that reproduction as the NEGATIVE CONTROL.

The required schedule (0029 §4a, round-3): `BEGIN IMMEDIATE` before ANY
allocation read; txn, seq and the batch `recorded_at` minted AFTER the lock;
busy → whole-transaction retry-or-loud-refusal under `busy_timeout` (0007
§4c). The `(user_id, seq)` PK is a BACKSTOP only.

RULE ZERO (both seats): every assertion ships with a negative control that
makes it fail, in this file.
"""
from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass, field
from typing import List, Optional

# 0029 §4a's pinned DDL, verbatim shape (the columns this model needs).
DDL = """
CREATE TABLE IF NOT EXISTS edge_event (
    user_id     TEXT    NOT NULL,
    seq         INTEGER NOT NULL,
    txn         INTEGER NOT NULL,
    edge_id     TEXT    NOT NULL,
    kind        TEXT    NOT NULL,
    reason      TEXT,
    state       TEXT    NOT NULL,
    recorded_at TEXT    NOT NULL,
    PRIMARY KEY (user_id, seq)
);
"""


@dataclass
class BatchResult:
    txn: Optional[int] = None
    seqs: List[int] = field(default_factory=list)
    error: Optional[str] = None
    maxima_read: Optional[int] = None  # max(txn) observed before allocating


def _connect(path: str, busy_timeout_ms: int) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=0, check_same_thread=False)
    conn.execute(f"PRAGMA busy_timeout = {busy_timeout_ms}")
    conn.isolation_level = None  # explicit BEGIN — never implicit
    return conn


def immediate_batch(conn: sqlite3.Connection, user: str, n_events: int,
                    recorded_at: str, *, hold: Optional[threading.Event] = None,
                    proceed: Optional[threading.Event] = None) -> BatchResult:
    """THE REQUIRED SCHEDULE: lock first, then read, allocate, mint, write.

    `hold`/`proceed` let the driver force the adversarial interleaving.
    """
    r = BatchResult()
    try:
        conn.execute("BEGIN IMMEDIATE")           # the lock, BEFORE any read
        cur = conn.execute(
            "SELECT COALESCE(MAX(txn),0), COALESCE(MAX(seq),0) "
            "FROM edge_event WHERE user_id=?", (user,))
        max_txn, max_seq = cur.fetchone()
        r.maxima_read = max_txn
        if hold is not None:
            hold.set()                            # signal: maxima read
        if proceed is not None:
            proceed.wait(timeout=10)              # let the driver interleave
        r.txn = max_txn + 1
        for i in range(1, n_events + 1):          # one clock read per batch:
            seq = max_seq + i                     # recorded_at is a parameter,
            conn.execute(                          # minted after the lock
                "INSERT INTO edge_event VALUES (?,?,?,?,?,?,?,?)",
                (user, seq, r.txn, f"e{seq}", "mutated", None, "{}", recorded_at))
            r.seqs.append(seq)
        conn.execute("COMMIT")
    except sqlite3.OperationalError as e:
        r.error = str(e)
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
    return r


def deferred_batch(conn: sqlite3.Connection, user: str, n_events: int,
                   recorded_at: str, *, hold: Optional[threading.Event] = None,
                   proceed: Optional[threading.Event] = None) -> BatchResult:
    """THE FORBIDDEN SCHEDULE, kept as the negative control: BEGIN (deferred)
    reads under a shared lock, so two connections can read the SAME maxima —
    then the second writer dies. This is the round-3 reviewer's reproduction."""
    r = BatchResult()
    try:
        conn.execute("BEGIN")                     # DEFERRED — no writer lock yet
        cur = conn.execute(
            "SELECT COALESCE(MAX(txn),0), COALESCE(MAX(seq),0) "
            "FROM edge_event WHERE user_id=?", (user,))
        max_txn, max_seq = cur.fetchone()
        r.maxima_read = max_txn
        if hold is not None:
            hold.set()
        if proceed is not None:
            proceed.wait(timeout=10)
        r.txn = max_txn + 1
        for i in range(1, n_events + 1):
            seq = max_seq + i
            conn.execute(
                "INSERT INTO edge_event VALUES (?,?,?,?,?,?,?,?)",
                (user, seq, r.txn, f"e{seq}", "mutated", None, "{}", recorded_at))
            r.seqs.append(seq)
        conn.execute("COMMIT")
    except sqlite3.OperationalError as e:
        r.error = str(e)
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
    return r


def run_two_connection_schedule(path: str, schedule, *, busy_timeout_ms: int):
    """Force the adversarial interleaving: connection 1 reads its maxima and
    PAUSES; connection 2 then runs its whole batch; connection 1 resumes.

    Under IMMEDIATE, connection 2 cannot even read until 1 commits, so the
    pause serializes cleanly (2 waits on the lock, within busy_timeout).
    Under DEFERRED, both read the same maxima and the loser dies locked.
    """
    boot = sqlite3.connect(path)
    boot.executescript(DDL)
    boot.close()
    c1 = _connect(path, busy_timeout_ms)
    c2 = _connect(path, busy_timeout_ms)
    r1_read = threading.Event()
    r1_go = threading.Event()
    out: dict = {}

    def first():
        out["r1"] = schedule(c1, "u", 2, "2026-08-31T23:00:00Z",
                             hold=r1_read, proceed=r1_go)

    def second():
        r1_read.wait(timeout=10)                  # start only after 1 has read
        out["r2"] = schedule(c2, "u", 2, "2026-08-31T23:00:01Z")
        r1_go.set()                               # then let 1 finish

    t1 = threading.Thread(target=first)
    t2 = threading.Thread(target=second)
    t1.start(); t2.start()
    # Under IMMEDIATE, thread 2 blocks on BEGIN until thread 1 commits — but
    # thread 1 waits for `proceed`, which thread 2 only sets after finishing.
    # Break the cycle the way a real store does: bounded wait, then release.
    if not r1_go.wait(timeout=2.0):
        r1_go.set()                               # 2 is lock-blocked: release 1
    t1.join(timeout=15); t2.join(timeout=15)
    c1.close(); c2.close()
    return out["r1"], out["r2"]
