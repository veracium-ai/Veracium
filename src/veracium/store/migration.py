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

from ..schema import Episode
from .schema_version import (SCHEMA_VERSION, SCHEMAS, OpenResult,
                             PostCommitAuditError, StoreVersionError,
                             _AUDIT_STRING_CAP, _mint_store_identity, open_versioned)

log = logging.getLogger(__name__)


class DuplicateOutcomeChainError(Exception):
    """specs/0009 §4f: the v2→v3 migration found more than one legacy outcome
    episode for one `(user_id, edge_id, evidence_ref)` identity. The pre-v3 store
    never enforced one outcome per chain, and there is no trustworthy information to
    reconstruct which superseded which — so the migration REFUSES rather than
    fabricating an order or branching the chain (two roots / two heads, H3 false).
    Raised inside the write transaction, so nothing is partially converted; the
    operator resolves the duplicate identities and retries."""


def _migrate_outcome_chains(conn: sqlite3.Connection) -> None:
    """specs/0009 §4f — convert every legacy outcome episode into an honest chain
    ROOT: `seq=1`, `supersedes_episode=None`, `judgment_time_known=False`. Its `date`
    is the original USE date (the old in-place upgrade path never updated it), NOT a
    known judgment time, so it is carried forward unchanged and honestly labelled
    unknown. Group by identity FIRST: >1 legacy outcome for one chain → REFUSE
    (`DuplicateOutcomeChainError`), never two roots. Runs INSIDE the migration
    transaction, so a refusal rolls the whole migration back (`0013` failure contract)."""
    groups: dict = {}
    outcome_rows: list = []
    for eid, blob in conn.execute("SELECT id, json FROM episodes").fetchall():
        ep = Episode.model_validate_json(blob)
        if ep.kind != "outcome":
            continue
        outcome_rows.append((eid, ep))
        groups.setdefault(
            (ep.user_id, ep.edge_id, ep.provenance.evidence_ref), []).append(eid)
    for gk, ids in groups.items():
        if len(ids) > 1:
            raise DuplicateOutcomeChainError(
                f"v2→v3 migration: {len(ids)} legacy outcome episodes for chain {gk} "
                f"({', '.join(ids)}) — refuse rather than branch; resolve the "
                f"duplicate identities and retry (specs/0009 §4f)")
    for eid, ep in outcome_rows:
        converted = ep.model_copy(update={"seq": 1, "supersedes_episode": None,
                                          "judgment_time_known": False})
        conn.execute("UPDATE episodes SET json=? WHERE id=?",
                     (converted.model_dump_json(), eid))


def _drop_wiki_cache(conn: sqlite3.Connection) -> None:
    """specs/0003 §7a — the v3→v4 migration invalidates every wiki cache. Deleting the
    rows (rather than an ALTER) keeps the migration additive at the schema level while
    still expiring caches compiled under pre-0003 read semantics. `ensure_wiki` treats a
    missing cache as "recompile", so the next recall rebuilds under the contention
    contract. Runs INSIDE the migration transaction, so a rollback restores the caches."""
    conn.execute("DELETE FROM wiki")


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
    # specs/0009 §4f: crossing INTO v3 from below also transforms legacy outcome
    # episodes into honest chain roots (a DATA migration the additive DDL cannot do).
    # Guarded to base<3<=head so a future v3→v4 bump never re-roots valid v3 chains.
    if base < 3 <= SCHEMA_VERSION:
        _migrate_outcome_chains(conn)
    # specs/0003 §4c-ii / §7a: crossing INTO v4 must invalidate every wiki cache. A v3
    # store may hold a wiki compiled under pre-0003 "one current value" semantics over a
    # pair that is now a contention (§4e reorders PRE-EXISTING contentions), and the
    # additive-table migration would leave that cache judged fresh. Dropping the cached
    # rows forces recompilation on the first recall after migration, not eight writes
    # later. A DATA step the additive DDL cannot express — the same shape as the outcome
    # re-rooting above. Guarded base<4<=head so it fires exactly once, on the v3→v4 cross.
    if base < 4 <= SCHEMA_VERSION:
        _drop_wiki_cache(conn)
    # specs/0006 §4.2 / Migration: crossing INTO v5 mints the durable `store_identity`
    # origin singleton, transactionally, in the SAME migration transaction. A DATA step
    # the additive `store_identity` table DDL cannot express (the table is empty until
    # its one row exists). No per-record change and NO backfill — existing edge rows keep
    # `origin` absent and resolve to this singleton at read (§4 rule 6). Guarded
    # base<5<=head so it fires exactly once, on the v4→v5 cross.
    if base < 5 <= SCHEMA_VERSION:
        _mint_store_identity(conn)
    # specs/0014 §4b/§7a: crossing INTO v6 ALTERs `supersession_operations` — the repo's
    # FIRST ALTER of an existing table, which the additive diff-by-key above cannot
    # express (the table's typed key exists in the base, so its CHANGED DDL is invisible
    # to the object diff). The three ADD COLUMNs run in the frozen order; the DEFAULT 1
    # on `outcome_digest_version` both makes the ALTER legal on a populated table and IS
    # the migration stamp (every pre-upgrade receipt reads version 1 — the pre-split
    # digest projection; post-upgrade writes stamp 2 explicitly). The resulting stored
    # DDL must byte-match the REVIEWED constant `ALTER_PATH_V6_SQL` (0014 §4b): the
    # expectation was authored independently and authorized by review — a mismatch here
    # means this migration (or the runtime) is wrong, and `open_versioned`'s
    # revalidation against `accepted_digests(6)` (which carries the reviewed ALTER-path
    # manifest per `0013` §4e) refuses the result rather than adopting it.
    # Guarded 4 <= base: `supersession_operations` entered the schema at v4, so only
    # v4/v5 bases carry a table to ALTER — for bases 1-3 the additive diff above already
    # created the table in its v6 CONSTRUCTOR form (columns inline), and those paths
    # land on the CONSTRUCTOR manifest, which is equally accepted.
    if 4 <= base < 6 <= SCHEMA_VERSION:
        from .schema_version import ALTERS_V5_TO_V6, ALTER_PATH_V6_SQL
        for stmt in ALTERS_V5_TO_V6:
            conn.execute(stmt)
        stored = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' "
            "AND name='supersession_operations'").fetchone()[0]
        if stored != ALTER_PATH_V6_SQL:
            raise StoreVersionError(
                "", base, SCHEMA_VERSION, "unsupported-migration",
                diff="the v5->v6 ALTER produced DDL that does not byte-match the "
                     "reviewed expectation (0014 §4b) — the migration or runtime is "
                     "wrong; the expectation never moves")
    # 0019 rider (as amended by 0020/0021, C1–C3) / 0021 §7b: crossing INTO v8 ALTERs
    # `contribution_ledger` — the typed contributor link (`contributor_type TEXT`,
    # `contributor_ref TEXT`, nullable; legacy rows NULL). The same shape as the v6
    # block above: the table's typed key exists in the base, so its CHANGED DDL is
    # invisible to the additive object diff. The two ADD COLUMNs are the migration's
    # 0013-declared steps, sha-pinned in the RECORDED evidence
    # (`specs/evidence/0020/schema_v8_evidence.txt` [4]); the resulting stored DDL
    # must byte-match the recorded ALTER-path manifestation (`ALTER_PATH_V8_SQL`,
    # evidence [2]) — the expectation was recorded independently and the migration may
    # not define its own destination (0013 §4c); `open_versioned`'s revalidation
    # against `accepted_digests(8)` refuses a mismatched result rather than adopting
    # it. Guarded 6 <= base: `contribution_ledger` entered the schema at v6, so only
    # v6/v7 bases carry a table to ALTER — for bases ≤5 the additive diff above
    # already created the table in its v8 CONSTRUCTOR form (columns inline), and
    # those paths land on the CONSTRUCTOR manifest, which is equally accepted.
    if 6 <= base < 8 <= SCHEMA_VERSION:
        from .schema_version import ALTERS_V7_TO_V8, ALTER_PATH_V8_SQL
        for stmt in ALTERS_V7_TO_V8:
            conn.execute(stmt)
        stored = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' "
            "AND name='contribution_ledger'").fetchone()[0]
        if stored != ALTER_PATH_V8_SQL:
            raise StoreVersionError(
                "", base, SCHEMA_VERSION, "unsupported-migration",
                diff="the v7->v8 ALTER produced DDL that does not byte-match the "
                     "recorded evidence (0019 rider C2 / 0021 §7b) — the migration "
                     "or runtime is wrong; the expectation never moves")
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
