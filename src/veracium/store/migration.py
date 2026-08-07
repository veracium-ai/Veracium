"""Offline store migration — the `specs/0013` operation, in production.

`specs/0013` §5b (ruled M-Q2): a migration is **offline** and owned by the
deployment authority — *ordinary opening cannot initiate it*. A build that opens a
store below its head version REFUSES (`StoreVersionError`, reason
`migration-required`); the host quiesces all access and runs `migrate_store()`
explicitly. This is where `specs/0013`'s accepted migration design and `specs/0008`'s
`confirmations` table (the v1→v2 migration) meet production.

The migration audit follows `specs/0007`'s adoption model: events flow through a
caller-supplied `audit_sink` callback — `migration_attempted` INSIDE the write
transaction (a raising sink aborts, so an unrecorded migration cannot exist) and
`migration_committed` after commit via `open_versioned`'s `on_committed` seam, so a
post-commit cleanup failure can never erase a proven commit (`specs/0013` round 11).
"""
from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Callable, NamedTuple, Optional

from .schema_version import (SCHEMA_VERSION, SCHEMAS, OpenResult,
                             PostCommitAuditError, StoreVersionError,
                             _AUDIT_STRING_CAP, open_versioned)

log = logging.getLogger(__name__)


class MigrationAuditEvent(NamedTuple):
    """The audit payload of one offline migration. `migration_committed` repeats
    `migration_attempted` bar `event`/`occurred_at`, so a sink can process either
    in isolation. `path` is capped at 4096 bytes — a limit, not a truncation: a
    shortened path in an audit record is a falsified audit record."""
    event: str                 # "migration_attempted" | "migration_committed"
    migration_id: str
    path: str
    from_version: int
    to_version: int
    occurred_at: str           # RFC 3339, UTC


def _mig_event(kind: str, mid: str, path: str, from_v: int,
               to_v: int) -> MigrationAuditEvent:
    if len(str(path).encode("utf-8", "surrogateescape")) > _AUDIT_STRING_CAP:
        raise ValueError(f"audit field 'path' exceeds {_AUDIT_STRING_CAP} bytes; "
                         f"refusing rather than truncating an audit record")
    return MigrationAuditEvent(
        event=kind, migration_id=mid, path=str(path), from_version=from_v,
        to_version=to_v, occurred_at=datetime.now(timezone.utc).isoformat())


def _apply_forward(conn: sqlite3.Connection, base: int) -> None:
    """Bring a `base`-version store to the current version, INSIDE the open write
    transaction. Every migration so far is purely ADDITIVE — new whole objects, never
    an ALTER of an existing row/table: v1→v2 adds the `confirmations` table
    (`specs/0008` §6d); v2→v3 adds the `consolidation_ops` table (`specs/0010` §4a) and
    carries `specs/0009`'s new Episode fields in the existing `episodes.json` blob. So a
    below-head store is brought forward by applying exactly the objects the head schema
    has and `base` lacks (keyed by typed key), then stamping. A store two versions back
    (v1→v3) gets BOTH deltas in one apply, because the object set is diffed against the
    actual base, not a fixed step. `open_versioned` revalidates the result against the
    head validator before committing, so a wrong DDL cannot land."""
    if base not in SCHEMAS or base >= SCHEMA_VERSION:
        raise StoreVersionError(
            "", base, SCHEMA_VERSION, "unsupported-migration",
            diff=f"no migration path from base {base} to head {SCHEMA_VERSION} "
                 f"is defined")
    base_keys = {o.key for o in SCHEMAS[base]}
    for o in SCHEMAS[SCHEMA_VERSION]:
        if o.key not in base_keys:                     # only what the head ADDS over base
            conn.execute(o.ddl)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def migrate_store(path: str, *,
                  audit_sink: Optional[Callable[[MigrationAuditEvent], None]] = None
                  ) -> OpenResult:
    """Migrate a below-head store forward to the current version and return the
    `OpenResult`. **Offline** (`specs/0013` §5b): the caller MUST have quiesced all
    other access to the store. A store already at the head version opens `current`
    (this is safe to call unconditionally after quiescing). A store whose shape is
    neither the head nor a known migratable base refuses exactly as ordinary opening
    would. `audit_sink`, if given, receives `migration_attempted` (inside the
    transaction) and `migration_committed` (after commit); with no sink the
    migration is logged and no durability is claimed."""
    conn = sqlite3.connect(path)
    closed = False
    try:
        mid = str(uuid.uuid4())
        pending: dict = {}

        def _older(c, spath, found, objs, base):
            _apply_forward(c, base)
            pending["from_v"] = base
            attempted = _mig_event("migration_attempted", mid, spath, base,
                                   SCHEMA_VERSION)
            if audit_sink is not None:
                audit_sink(attempted)                  # inside txn: raising aborts
            else:
                log.info("migrating store %s v%s→v%s (%s); no audit sink "
                         "configured, so no durability is claimed",
                         spath, base, SCHEMA_VERSION, mid)

        result = open_versioned(conn, path, older=_older)
        # The committed audit event is emitted AFTER the commit, mirroring
        # adoption (schema_version.py): a sink that fails here is a POST-commit
        # failure — the store IS migrated — surfaced as `PostCommitAuditError`
        # (committed=True), never a rollback. A retry sees `current` and does not
        # re-migrate.
        if str(result) == "migrated" and audit_sink is not None:
            committed = _mig_event("migration_committed", mid, str(path),
                                   pending.get("from_v", 0), SCHEMA_VERSION)
            try:
                audit_sink(committed)
            except BaseException as exc:
                conn.close()
                closed = True
                raise PostCommitAuditError(str(path), mid, exc) from exc
        return result
    finally:
        if not closed:
            conn.close()
