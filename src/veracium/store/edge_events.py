"""specs/0029 — the transaction-time carrier's SQL, shared by the store (the
runtime choke point) and the migration (the epoch baseline). Lives in its own
module because `migration.py` cannot import `sqlite.py` (the store opens
through the migration) and both must write the SAME row shape.

Nothing here opens a transaction: every function runs INSIDE the caller's
already-open `BEGIN IMMEDIATE` (§4a — the allocation reads below are only
serializable because the write lock is already held; the caller proves it).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

# §4a DDL order: user_id, seq, txn, edge_id, kind, reason, state, recorded_at
EVENT_INSERT_SQL = ("INSERT INTO edge_event(user_id,seq,txn,edge_id,kind,reason,state,"
                    "recorded_at) VALUES(?,?,?,?,?,?,?,?)")


def next_txn(conn: sqlite3.Connection, user_id: str) -> int:
    """The next per-user batch id: 1 + MAX(txn). Read INSIDE the immediate
    transaction (V-TXN-ALLOC) — two connections cannot read the same maximum."""
    return 1 + conn.execute(
        "SELECT COALESCE(MAX(txn), 0) FROM edge_event WHERE user_id=?",
        (user_id,)).fetchone()[0]


def next_seq(conn: sqlite3.Connection, user_id: str) -> int:
    """The next per-user ordinal: gapless-monotone in the order the DATABASE
    serialized (the PK is a backstop only, §4a)."""
    return 1 + conn.execute(
        "SELECT COALESCE(MAX(seq), 0) FROM edge_event WHERE user_id=?",
        (user_id,)).fetchone()[0]


def mint_recorded_at(conn: sqlite3.Connection, user_id: str, now: datetime) -> str:
    """§4c: `recorded_at` is minted by the STORE from ONE clock read per batch,
    after the lock, and never goes backwards per user — under a backwards
    clock step the previous batch's value is reused (V-MINT). It is telemetry:
    `seq` orders; this orders nothing."""
    prev = conn.execute(
        "SELECT MAX(recorded_at) FROM edge_event WHERE user_id=?",
        (user_id,)).fetchone()[0]
    if prev is not None and datetime.fromisoformat(prev) > now:
        return prev
    return now.isoformat()


def append_event(conn: sqlite3.Connection, *, user_id: str, seq: int, txn: int,
                 edge_id: str, kind: str, reason: Optional[str], state: str,
                 recorded_at: str) -> None:
    conn.execute(EVENT_INSERT_SQL,
                 (user_id, seq, txn, edge_id, kind, reason, state, recorded_at))


def journal_baselines(conn: sqlite3.Connection, now_iso: str) -> int:
    """§4e — the EPOCH BASELINE, inside the migration's one transaction: every
    pre-existing edge row is journaled ONCE as a `baseline` event whose `state`
    is the row's json AS FOUND (the bytes, not a re-serialization — V-BASELINE)
    and whose `reason` is NULL always (a found `invalidation_reason` lives
    INSIDE the payload — V-COLUMN-NOT-INPUT's producer half). One batch per
    user; `epoch_txn(user)` is that batch's txn, derived at read. Returns the
    number of baselines written. Crash-retry cannot double it: the migration
    is one transaction and a retried base is still below 13."""
    n = 0
    users = [r[0] for r in conn.execute(
        "SELECT DISTINCT user_id FROM edges ORDER BY user_id")]
    for user_id in users:
        txn = next_txn(conn, user_id)
        seq = next_seq(conn, user_id)
        for edge_id, found in conn.execute(
                "SELECT id, json FROM edges WHERE user_id=? ORDER BY rowid",
                (user_id,)).fetchall():
            append_event(conn, user_id=user_id, seq=seq, txn=txn, edge_id=edge_id,
                         kind="baseline", reason=None, state=found,
                         recorded_at=now_iso)
            seq += 1
            n += 1
    return n


def mint_store_epoch(conn: sqlite3.Connection, now_iso: str, schema_at: int) -> None:
    """§4e: the per-store epoch row — when journaling began and at which
    schema. Idempotent on the fixed `id = 1` (the single-row guard is the
    SCHEMA's CHECK, `store_identity`'s pattern), so a create-then-open or a
    re-run never moves an existing epoch."""
    conn.execute(
        "INSERT OR IGNORE INTO store_epoch(id, started_at, schema_at) VALUES(1, ?, ?)",
        (now_iso, int(schema_at)))
