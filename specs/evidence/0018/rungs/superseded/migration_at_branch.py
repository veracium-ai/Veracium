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

import hashlib
import json
import logging
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Callable, NamedTuple, Optional

from pydantic import BaseModel, TypeAdapter

from ..schema import Episode
from .schema_version import (RUNTIME_STATUSES, SCHEMA_VERSION, SCHEMAS, OpenResult,
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


# ---- specs/0013 §4f (v33, internal finding 0013-PA1): every step's output is checked AT THE STEP -----------------

def _clock() -> datetime:
    """THE migration's clock (0013 §4f, M119–M121): `_apply_forward` reads it ONCE, and that one value fills a legacy
    episode's missing `observed_at`, stamps every v13 baseline event and starts the store epoch — so the value that
    filled `observed_at` is recorded (`store_epoch.started_at`). A module function so a test can inject a clock."""
    return datetime.now(timezone.utc)


class MigrationPostconditionError(StoreVersionError):
    """A migration step's postcondition failed (0013 §4f, M123): reason `unsupported-migration`, `step` naming the
    step EXACTLY. Raised inside the migration's transaction, so the store is left as it was."""

    def __init__(self, base: int, step: str, problems: list):
        self.step = step
        self.problems = list(problems)
        super().__init__("", base, SCHEMA_VERSION, "unsupported-migration",
                         diff=f"postcondition {step}: " + "; ".join(self.problems[:5])
                              + (f" (+{len(self.problems) - 5} more)" if len(self.problems) > 5 else ""))


# The STEP names a postcondition refusal carries (MigrationPostconditionError.step): fixed words, one per step.
STEP_STAMP, STEP_IDENTITY, STEP_EPOCH = "stamp", "store-identity", "store-epoch"
STEP_BASELINE, STEP_CHAINS, STEP_WIKI = "v13-baseline", "v2-v3-outcome-chains", "v3-v4-wiki-drop"
STEP_ACT_COLUMNS, STEP_ACT_COUNTER, STEP_REGISTRY = "v16-act-columns", "v16-act-counter", "v16-registry-backfill"
STEP_NOTICE_STATE = "v16-notice-state"
STEP_ARITY_ERA, STEP_ARITY_INVENTORY, STEP_REFUSAL_INVENTORY = "v16-arity-era", "v16-arity-inventory", "v16-refusal-inventory"
STEP_ARITY_EDGES = "v16-arity-edges-unchanged"

# 0013 §4f / M-Q6 (RULED by accepted 0016 D2): a raw key no current model declares is REFUSED, except these — fields a
# released schema declared and HEAD no longer does, dropped on read by every load since their deletion. Bound by
# tests/test_0013_pa1_retired_keys.py to the derivation over every release tag (Provenance.source_type, v0.1.0–v0.10.0).
RETIRED_EPISODE_KEYS = frozenset({("provenance", "source_type")})
_CHAIN_FIELDS = {"seq": 1, "supersedes_episode": None, "judgment_time_known": False}


def _refuse_unless(base: int, step: str, problems: list) -> None:
    with _SITE_MIGRATION_POSTCONDITION.consult():
        if problems:
            raise _SITE_MIGRATION_POSTCONDITION.fire(MigrationPostconditionError(base, step, problems), step)


def _nested_models(model) -> dict:
    """The fields of `model` typed as a pydantic model, DERIVED from the annotations (0013 §4f "at any depth")."""
    return {k: f.annotation for k, f in model.model_fields.items()
            if isinstance(f.annotation, type) and issubclass(f.annotation, BaseModel)}


_ADAPTERS: dict = {}


def _typed(field, value):
    a = _ADAPTERS.get(id(field))
    if a is None:
        a = _ADAPTERS[id(field)] = (field, TypeAdapter(field.annotation))     # the field kept alive: its id stays its own
    return a[1].validate_python(value)


def _compare_converted(raw: dict, new: dict, model, path: tuple, now: datetime, out: list) -> None:
    """0013 §4f's v2→v3 postcondition, one level: `raw` is the row's RAW legacy JSON (never a model load of it), `new`
    the row as the step wrote it. Present keys equal AS THEIR DECLARED FIELD TYPE; keys the dump ADDED equal their
    declared constant default (the chain fields their new values; `provenance.observed_at` the migration's one clock
    read); a raw key no model declares is refused unless retired; nested models compared key by key, recursively."""
    fields, nested = model.model_fields, _nested_models(model)
    for k in raw:
        if k not in fields and (path + (k,)) not in RETIRED_EPISODE_KEYS:
            out.append(f"{'.'.join(path + (k,))}: a key no model declares, not a retired one (0016 D2)")
    for k in new:
        if k not in fields:
            out.append(f"{'.'.join(path + (k,))}: the converted row carries a key no model declares")
    for k, f in fields.items():
        where = ".".join(path + (k,))
        if k not in new and (f.is_required() or f.default_factory is not None):
            out.append(f"{where}: a field with no constant default is missing from the converted row")
            continue
        if k in nested:
            if not isinstance(new[k], dict) or (k in raw and not isinstance(raw[k], dict)):
                out.append(f"{where}: not an object")
                continue
            _compare_converted(raw.get(k, {}), new[k], nested[k], path + (k,), now, out)
            continue
        try:
            # a key the model's serializer OMITS (0037 §2: the procedural markers are absent, not null, on a declarative
            # record) reads as its declared default — so a raw value the dump lost still compares, and fails
            got = _typed(f, new[k]) if k in new else _typed(f, f.default)
            if not path and k in _CHAIN_FIELDS:
                want = _typed(f, _CHAIN_FIELDS[k])
            elif k in raw:
                want = _typed(f, raw[k])
            elif path == ("provenance",) and k == "observed_at":
                want = _typed(f, now)
            elif f.default_factory is not None:
                out.append(f"{where}: a default_factory field other than provenance.observed_at — this step's "
                           f"contract does not cover it (0013 §4f)")
                continue
            else:
                want = _typed(f, f.default)
        except Exception as x:                                  # noqa: BLE001 — an unparseable value is a failure
            out.append(f"{where}: does not parse as its declared type ({type(x).__name__})")
            continue
        if got != want:
            out.append(f"{where}: {new.get(k, '<absent>')!r} != the expected {want!r}")


def _raw_object(blob):
    """A stored episode json as a dict, or None when it does not parse as a JSON object."""
    try:
        d = json.loads(blob)
    except (ValueError, TypeError):
        return None
    return d if isinstance(d, dict) else None


def _check_outcome_chains(conn: sqlite3.Connection, base: int, before: dict, now: datetime) -> None:
    """The v2→v3 postcondition. Which rows are legacy OUTCOME rows is decided HERE, from the `before` snapshot's raw
    `kind` (research's stage-2 F1): taking that set from the step would trust a value the step computed and kept, so a
    row the step misclassified would be neither converted nor reported (M123)."""
    problems = []
    kind_default = Episode.model_fields["kind"].default
    outcome_ids = set()
    for eid, blob in before.items():
        raw = _raw_object(blob)
        if raw is None:
            problems.append(f"episode {eid!r}: its pre-migration json is not a JSON object")
        elif raw.get("kind", kind_default) == "outcome":
            outcome_ids.add(eid)
    after = dict(conn.execute("SELECT id, json FROM episodes").fetchall())
    if set(after) != set(before):
        problems.append(f"the episode id set changed ({len(before)} rows before, {len(after)} after)")
    converted = 0
    for eid, blob in before.items():
        if eid not in after:
            continue
        if eid not in outcome_ids:
            if after[eid] != blob:
                problems.append(f"non-outcome episode {eid!r} changed")
            continue
        converted += 1
        old, new = _raw_object(blob), _raw_object(after[eid])
        if old is None or new is None:                    # stage-2 F2: an unparseable row is a FAILED check, never a raise
            problems.append(f"episode {eid!r}: the converted json is not a JSON object")
            continue
        out = []
        _compare_converted(old, new, Episode, (), now, out)
        problems += [f"episode {eid!r}: {o}" for o in out]
    if converted != len(outcome_ids):
        problems.append(f"converted {converted} outcome rows, the legacy count is {len(outcome_ids)}")
    _refuse_unless(base, STEP_CHAINS, problems)


def _rows(conn, sql, params=()) -> list:
    return [tuple(r) for r in conn.execute(sql, params).fetchall()]


def _migrate_outcome_chains(conn: sqlite3.Connection, now: Optional[datetime] = None) -> set:
    """specs/0009 §4f — convert every legacy outcome episode into an honest chain
    ROOT: `seq=1`, `supersedes_episode=None`, `judgment_time_known=False`. Its `date`
    is the original USE date (the old in-place upgrade path never updated it), NOT a
    known judgment time, so it is carried forward unchanged and honestly labelled
    unknown. Group by identity FIRST: >1 legacy outcome for one chain → REFUSE
    (`DuplicateOutcomeChainError`), never two roots. Runs INSIDE the migration
    transaction, so a refusal rolls the whole migration back (`0013` failure contract)."""
    now = now if now is not None else _clock()
    groups: dict = {}
    outcome_rows: list = []
    kind_default = Episode.model_fields["kind"].default
    for eid, blob in conn.execute("SELECT id, json FROM episodes").fetchall():
        raw = json.loads(blob)
        if raw.get("kind", kind_default) != "outcome":        # classified from the RAW row (0013 §4f), never a load
            Episode.model_validate_json(blob)                 # still validated, as before: a malformed row refuses
            continue
        prov = raw.get("provenance")
        if isinstance(prov, dict) and "observed_at" not in prov:
            prov["observed_at"] = now.isoformat()             # the ONE stated clock read, never a per-row default
        ep = Episode.model_validate(raw)
        outcome_rows.append((eid, ep))
        groups.setdefault(
            (ep.user_id, ep.edge_id, ep.provenance.evidence_ref), []).append(eid)
    for gk, ids in groups.items():
        with _SITE_DUPLICATE_OUTCOME_CHAIN.consult():
            if len(ids) > 1:
                raise _SITE_DUPLICATE_OUTCOME_CHAIN.fire(DuplicateOutcomeChainError(
                    f"v2→v3 migration: {len(ids)} legacy outcome episodes for chain {gk} "
                    f"({', '.join(ids)}) — refuse rather than branch; resolve the "
                    f"duplicate identities and retry (specs/0009 §4f)"))
    for eid, ep in outcome_rows:
        converted = ep.model_copy(update={"seq": 1, "supersedes_episode": None,
                                          "judgment_time_known": False})
        conn.execute("UPDATE episodes SET json=? WHERE id=?",
                     (converted.model_dump_json(), eid))
    return {eid for eid, _ in outcome_rows}


def _drop_wiki_cache(conn: sqlite3.Connection) -> None:
    """specs/0003 §7a — the v3→v4 migration invalidates every wiki cache. Deleting the
    rows (rather than an ALTER) keeps the migration additive at the schema level while
    still expiring caches compiled under pre-0003 read semantics. `ensure_wiki` treats a
    missing cache as "recompile", so the next recall rebuilds under the contention
    contract. Runs INSIDE the migration transaction, so a rollback restores the caches."""
    conn.execute("DELETE FROM wiki")


class MigrationRuntime(NamedTuple):
    """The migrating build (0013 INV-SA11; 0007 §4g): its SQLite version, `sqlite_source_id()` and the status the
    open gate MEASURED — `attested` or `verified` (a `refused` build never migrates)."""
    sqlite_version: str
    source_id: str
    status: str


class MigrationAuditEvent(NamedTuple):
    """The audit payload of one offline migration. `migration_committed` repeats
    `migration_attempted` bar `event`/`occurred_at`, so a sink can process either
    in isolation. `path` is capped at 4096 bytes — a limit, not a truncation: a
    shortened path in an audit record is a falsified audit record. `runtime` (0013
    INV-SA11) is the LAST field, so a host that reads the first six by position is
    unaffected; it rides both events, so either is still processable alone."""
    event: str                 # "migration_attempted" | "migration_committed"
    migration_id: str
    path: str
    from_version: int
    to_version: int
    occurred_at: str           # RFC 3339, UTC
    runtime: MigrationRuntime


# INV-SA11's subfields each have their OWN closed grammar, by fullmatch (research's stage-1 read, item 1(c)): the audit
# token grammar `_TOKEN_RE` admits no space, and a real `sqlite_source_id()` has two (`2024-01-30 16:01:20 e876…alt1`,
# 84 characters, a 64-character tail that is 60 hex plus a distribution's `altN`).
_SQLITE_VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?")
_SOURCE_ID_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} [0-9a-z]{64}")
_MIGRATING_STATUSES = frozenset(RUNTIME_STATUSES) - {"refused"}


def migration_runtime(status) -> MigrationRuntime:
    """INV-SA11's value from the gate's ONE `runtime_status()` reading, each subfield checked against its grammar at
    the write: a value that fails refuses the audit record rather than carrying prose."""
    from .schema_version import RuntimeStatus
    if not isinstance(status, RuntimeStatus):
        raise ValueError(f"audit field runtime.status: {type(status).__name__} is not a measured RuntimeStatus")
    rt = MigrationRuntime(status.sqlite_version, status.source_id, status.status)  # the gate's ONE read, not a second
    if type(rt.sqlite_version) is not str or not _SQLITE_VERSION_RE.fullmatch(rt.sqlite_version):
        raise ValueError(f"audit field runtime.sqlite_version {rt.sqlite_version!r} is not a SQLite version")
    if type(rt.source_id) is not str or not _SOURCE_ID_RE.fullmatch(rt.source_id):
        raise ValueError(f"audit field runtime.source_id {rt.source_id!r} is not a sqlite_source_id()")
    if rt.status not in _MIGRATING_STATUSES:
        raise ValueError(f"audit field runtime.status {rt.status!r} is not one a migrating build can have")
    return rt


def _mig_event(kind: str, mid: str, path: str, from_v: int,
               to_v: int, runtime: MigrationRuntime) -> MigrationAuditEvent:
    if len(str(path).encode("utf-8", "surrogateescape")) > _AUDIT_STRING_CAP:
        raise ValueError(f"audit field 'path' exceeds {_AUDIT_STRING_CAP} bytes; "
                         f"refusing rather than truncating an audit record")
    if type(runtime) is not MigrationRuntime:
        raise TypeError("the audit runtime must be exactly a MigrationRuntime (0013 INV-SA11)")
    return MigrationAuditEvent(
        event=kind, migration_id=mid, path=str(path), from_version=from_v,
        to_version=to_v, occurred_at=datetime.now(timezone.utc).isoformat(), runtime=runtime)


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
    with _SITE_MIGRATION_VERSION.consult():
        if base not in SCHEMAS or base >= SCHEMA_VERSION:
            raise _SITE_MIGRATION_VERSION.fire(StoreVersionError(
                "", base, SCHEMA_VERSION, "unsupported-migration",
                diff=f"no migration path from base {base} to head {SCHEMA_VERSION} "
                     f"is defined"), "unsupported-base")
        # 0013 §4f (B1): the migration's ONE clock read, before any step — the v2→v3 fill, the v13 baseline and the
        # store epoch all carry this value, so `store_epoch.started_at` records what filled `observed_at`.
        now = _clock()
        now_iso = now.isoformat()
        base_keys = {o.key for o in SCHEMAS[base]}
        for o in SCHEMAS[SCHEMA_VERSION]:
            if o.key not in base_keys:                     # only what the head ADDS over base
                conn.execute(o.ddl)
        # specs/0009 §4f: crossing INTO v3 from below also transforms legacy outcome
        # episodes into honest chain roots (a DATA migration the additive DDL cannot do).
        # Guarded to base<3<=head so a future v3→v4 bump never re-roots valid v3 chains.
        if base < 3 <= SCHEMA_VERSION:
            before = dict(conn.execute("SELECT id, json FROM episodes").fetchall())
            _migrate_outcome_chains(conn, now)
            _check_outcome_chains(conn, base, before, now)
        # specs/0003 §4c-ii / §7a: crossing INTO v4 must invalidate every wiki cache. A v3
        # store may hold a wiki compiled under pre-0003 "one current value" semantics over a
        # pair that is now a contention (§4e reorders PRE-EXISTING contentions), and the
        # additive-table migration would leave that cache judged fresh. Dropping the cached
        # rows forces recompilation on the first recall after migration, not eight writes
        # later. A DATA step the additive DDL cannot express — the same shape as the outcome
        # re-rooting above. Guarded base<4<=head so it fires exactly once, on the v3→v4 cross.
        if base < 4 <= SCHEMA_VERSION:
            _drop_wiki_cache(conn)
            left = conn.execute("SELECT COUNT(*) FROM wiki").fetchone()[0]
            _refuse_unless(base, STEP_WIKI, [f"wiki holds {left} row(s) after the drop"] if left else [])
        # specs/0006 §4.2 / Migration: crossing INTO v5 mints the durable `store_identity`
        # origin singleton, transactionally, in the SAME migration transaction. A DATA step
        # the additive `store_identity` table DDL cannot express (the table is empty until
        # its one row exists). No per-record change and NO backfill — existing edge rows keep
        # `origin` absent and resolve to this singleton at read (§4 rule 6). Guarded
        # base<5<=head so it fires exactly once, on the v4→v5 cross.
        if base < 5 <= SCHEMA_VERSION:
            pre = _rows(conn, "SELECT id, origin FROM store_identity")
            _mint_store_identity(conn)
            _refuse_unless(base, STEP_IDENTITY, _identity_problems(pre, _rows(conn, "SELECT id, origin FROM store_identity")))
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
                raise _SITE_MIGRATION_VERSION.fire(StoreVersionError(
                    "", base, SCHEMA_VERSION, "unsupported-migration",
                    diff="the v5->v6 ALTER produced DDL that does not byte-match the "
                         "reviewed expectation (0014 §4b) — the migration or runtime is "
                         "wrong; the expectation never moves"), "v6-alter-path")
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
                raise _SITE_MIGRATION_VERSION.fire(StoreVersionError(
                    "", base, SCHEMA_VERSION, "unsupported-migration",
                    diff="the v7->v8 ALTER produced DDL that does not byte-match the "
                         "recorded evidence (0019 rider C2 / 0021 §7b) — the migration "
                         "or runtime is wrong; the expectation never moves"), "v8-alter-path")
        # specs/0025 §4b-v (the confirmed 0014 amendment): crossing INTO v10
        # ALTERs `supersession_operations` — the nullable cross-era domain
        # column. Same shape as the v6/v8 blocks: the table's typed key exists
        # in the base (v4+), its CHANGED DDL is invisible to the additive diff,
        # and the ONE ADD COLUMN's measured result must byte-match a frozen
        # expectation. TWO accepted expectations exist because v9 stores hold
        # the table in two accepted DDL variants (fresh-constructor vs the
        # v5->v6 ALTER path); the migration may not define its own destination.
        # Migrated rows keep request_digest_domain NULL — §4b-v's dual-domain
        # comparison row; the migration NEVER fabricates a domain.
        if 4 <= base < 10 <= SCHEMA_VERSION:
            from .schema_version import (ALTER_PATH_V10_FROM_CONSTRUCTOR_SQL,
                                         ALTER_PATH_V10_FROM_V6_ALTERPATH_SQL,
                                         ALTERS_V9_TO_V10)
            for stmt in ALTERS_V9_TO_V10:
                conn.execute(stmt)
            stored = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' "
                "AND name='supersession_operations'").fetchone()[0]
            if stored not in (ALTER_PATH_V10_FROM_CONSTRUCTOR_SQL,
                              ALTER_PATH_V10_FROM_V6_ALTERPATH_SQL):
                raise _SITE_MIGRATION_VERSION.fire(StoreVersionError(
                    "", base, SCHEMA_VERSION, "unsupported-migration",
                    diff="the v9->v10 ALTER produced DDL matching NEITHER frozen "
                         "expectation (0025 §4b-v) — the migration or runtime is "
                         "wrong; the expectations never move"), "v10-alter-path")
        # specs/0029 §4e: crossing INTO v13 journals the EPOCH BASELINE — every
        # pre-existing edge row once, as found (bytes), reason NULL, one batch per
        # user — and mints the per-store `store_epoch` row, in THIS transaction
        # with the stamp: partial states are unrepresentable and a crash-retry
        # (base still 12) mints exactly one baseline. A DATA step the additive
        # DDL cannot express, the `store_identity` mint's shape. Guarded
        # base<13<=head so it fires exactly once, on the v12→v13 cross.
        if base < 13 <= SCHEMA_VERSION:
            from .edge_events import journal_baselines, mint_store_epoch
            edges = _rows(conn, "SELECT user_id, id, json FROM edges")
            events_before = _rows(conn, "SELECT rowid FROM edge_event")
            journal_baselines(conn, now_iso)                    # the migration's ONE clock read (B1)
            _refuse_unless(base, STEP_BASELINE, _baseline_problems(conn, edges, {r[0] for r in events_before}, now))
            pre = _rows(conn, "SELECT id, started_at, schema_at FROM store_epoch")
            mint_store_epoch(conn, now_iso, 13)
            _refuse_unless(base, STEP_EPOCH, _epoch_problems(pre, _rows(conn, "SELECT id, started_at, schema_at FROM store_epoch"), now))
        # specs/0041 §4b/§4b-ii (v15): crossing INTO v15 adds `episode_event` and `redactions`
        # — an attestation or an episode event exists only once the operation that writes
        # them runs on an open v15 store, so there is no data step; rows already holding the
        # marker bytes are UNATTESTED markers, admitted, neither refused nor quarantined
        # (ruled v7) and enumerated by `unattested_marker_report` for the operator.
        # specs/0027 §4g (v14): crossing INTO v14 adds the `policy_receipt` table
        # and its index through the generic additive apply above and NOTHING else
        # — a receipt is written only by a recall on an open v14 store, so there is
        # no pre-existing data to carry and no row to mint. Stated here so the
        # absence of a v14 step reads as a decision, not an omission.
        # specs/0008 v7 §2a/§6f/§6g (amendment `0047/0008-request-registry`): crossing INTO v16 — the request
        # registry, the act counter and the confirmations act columns, ONE step with three guarded blocks in the
        # order (a) ALTER, (b) mint, (c) backfill. `request_registry` and `act_counter` were created EMPTY by the
        # additive diff above on every path. Each block owes a postcondition (0013 §4f) read against the step's OWN
        # pre-read, never against what the step wrote:
        #   (a) bases 2..15 hold `confirmations` in SCHEMA_V2's DDL and cross the six ADD COLUMNs, byte-matched
        #       against the frozen measured literal; base 1 had no table, and the additive diff created it in its
        #       v16 CONSTRUCTOR form (the v6/v8 precedent), which is equally accepted;
        #   (b) the counter's one row (1, 1): no legacy act receives a position (§6f), so the counter starts here;
        #   (c) one `confirm` registry row per existing confirmation — its id, its edge, its digest BYTE-COPIED (the
        #       marker where 0041 already redacted it), result_ref = the confirmation id, written_at = the
        #       migration's one clock read (a write time, the same meaning for every verb; the original request's
        #       time stays on the confirmation through result_ref).
        # Then (research's B1): every pre-existing confirmation is byte-equal in its eight v15 columns, `local`, and
        # NULL in the five others — an act recorded before the column existed has an UNKNOWN position, never a
        # synthesized one — and the counter still reads (1, 1): the backfill takes no position.
        if base < 16 <= SCHEMA_VERSION:
            from .schema_version import ALTER_PATH_V16_CONFIRMATIONS_SQL, ALTERS_V15_TO_V16, mint_act_counter
            conf_before = _rows(conn, f"SELECT {_CONF_V15_COLS} FROM confirmations") if base >= 2 else []
            if base >= 2:
                for stmt in ALTERS_V15_TO_V16:
                    conn.execute(stmt)
                stored = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name='confirmations'").fetchone()[0]
                if stored != ALTER_PATH_V16_CONFIRMATIONS_SQL:
                    raise _SITE_MIGRATION_VERSION.fire(StoreVersionError(
                        "", base, SCHEMA_VERSION, "unsupported-migration",
                        diff="the v15->v16 ALTER produced DDL that does not byte-match the frozen measured "
                             "expectation (0008 §2a) — the migration or runtime is wrong; the expectation never "
                             "moves"), "v16-alter-path")
            counter_before = _rows(conn, "SELECT id, next_seq FROM act_counter")
            mint_act_counter(conn)
            _refuse_unless(base, STEP_ACT_COUNTER,
                           _act_counter_problems(counter_before, _rows(conn, "SELECT id, next_seq FROM act_counter")))
            registry_before = _rows(conn, f"SELECT {_REGISTRY_COLS} FROM request_registry")
            conn.execute(
                "INSERT INTO request_registry(user_id, correlation_id, verb, target_edge_id, request_digest, "
                "result_ref, written_at) SELECT user_id, correlation_id, 'confirm', edge_id, request_digest, id, ? "
                "FROM confirmations", (now_iso,))
            _refuse_unless(base, STEP_REGISTRY, _registry_backfill_problems(
                conf_before, registry_before, _rows(conn, f"SELECT {_REGISTRY_COLS} FROM request_registry"), now))
            _refuse_unless(base, STEP_ACT_COLUMNS, _act_column_problems(
                conf_before, _rows(conn, f"SELECT {_CONF_V15_COLS}, {_CONF_ACT_COLS} FROM confirmations")))
            _refuse_unless(base, STEP_ACT_COUNTER,
                           _act_counter_problems(counter_before, _rows(conn, "SELECT id, next_seq FROM act_counter")))
            # specs/0041 §11.6.6 (T4): every redaction row gets its NOTICE STATE, by the rule today's readers already
            # apply — `standing` iff it has no event and a source identity (the pre-v16 `_STANDING_SQL`), `applied`
            # otherwise (a row with no event and no source counted as attested before v16, and still does). No row is
            # `pending`: the v15 hotfix's default path wrote none. Only a base-15 store holds the table (it entered at
            # v15) and crosses the ALTER; below it the additive diff created it, empty, in its v16 form.
            from .schema_version import ALTER_PATH_V16_REDACTIONS_SQL, ALTERS_V15_TO_V16_REDACTIONS
            red_before = _rows(conn, f"SELECT {_RED_V15_COLS} FROM redactions") if base >= 15 else []
            if base >= 15:
                for stmt in ALTERS_V15_TO_V16_REDACTIONS:
                    conn.execute(stmt)
                stored = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name='redactions'").fetchone()[0]
                if stored != ALTER_PATH_V16_REDACTIONS_SQL:
                    raise _SITE_MIGRATION_VERSION.fire(StoreVersionError(
                        "", base, SCHEMA_VERSION, "unsupported-migration",
                        diff="the v15->v16 ALTER of redactions produced DDL that does not byte-match the frozen measured "
                             "expectation (0041 §11.6.6) — the migration or runtime is wrong; the expectation never "
                             "moves"), "v16-alter-path")
            conn.execute("UPDATE redactions SET state='standing' WHERE event_ref IS NULL AND source_origin IS NOT NULL")
            _refuse_unless(base, STEP_NOTICE_STATE, _notice_state_problems(
                red_before, _rows(conn, f"SELECT {_RED_V15_COLS}, state, pending_reason FROM redactions")))
            # specs/0044 §4f / 0018 amendment §4a (T5): the ARITY ERA and its two INVENTORIES, in this transaction, after
            # the notice-state block (nothing here reads coverage, N1). They are the operation-era boundary: what was
            # retired `superseded` under the three default names, and every refusal, when THIS transaction commits —
            # never decided from a timestamp (§4f: `invalidated_at` is a valid-time endpoint, not a commit time). Each
            # block's postcondition reads the database's own bytes, independently of what the block wrote, and the
            # step changes no edge and no journal event (INV-I24), checked after every block.
            from .lifetime import RECLASSIFIED_RELATIONS, SUPERSEDED, retirement
            from .schema_version import mint_arity_era
            edges_pin = _rows(conn, "SELECT * FROM edges ORDER BY id")
            events_pin = _rows(conn, "SELECT rowid, * FROM edge_event ORDER BY rowid")

            def _edges_unchanged(block: str) -> None:
                post_e = _rows(conn, "SELECT * FROM edges ORDER BY id")
                post_v = _rows(conn, "SELECT rowid, * FROM edge_event ORDER BY rowid")
                _refuse_unless(base, STEP_ARITY_EDGES,
                               ([f"{block}: the edges table changed"] if post_e != edges_pin else [])
                               + ([f"{block}: the edge journal changed"] if post_v != events_pin else []))
            # step 7: the era, the migration's ONE clock read (D5)
            era_before = _rows(conn, "SELECT id, effective_at FROM arity_era")
            mint_arity_era(conn, now_iso)
            _refuse_unless(base, STEP_ARITY_ERA,
                           _arity_era_problems(era_before, _rows(conn, "SELECT id, effective_at FROM arity_era"), now))
            _edges_unchanged(STEP_ARITY_ERA)
            # step 8: the arity inventory, selected by the DEFAULT NAMES; the predicate is `lifetime.retirement`. The
            # selection reads the relation COLUMN OR the json's relation (research's T5 S2 N3): a row whose two disagree
            # is SEEN, so the check below refuses it (F2's column = json rule) instead of the step passing it by
            marks = ",".join("?" * len(RECLASSIFIED_RELATIONS))
            named = f"(relation IN ({marks}) OR json_extract(json, '$.relation') IN ({marks}))"
            named_args = tuple(RECLASSIFIED_RELATIONS) * 2
            inv_before = _rows(conn, "SELECT edge_id FROM arity_inventory")
            for eid, uid, blob in _rows(conn, f"SELECT id, user_id, json FROM edges WHERE {named} ORDER BY id",
                                        named_args):
                ret = retirement(json.loads(blob))
                if ret is not None and ret[1] == SUPERSEDED:
                    conn.execute("INSERT INTO arity_inventory(edge_id, user_id, pre_invalidated_at, pre_reason) "
                                 "VALUES(?, ?, ?, ?)", (eid, uid, ret[0], ret[1]))
            _refuse_unless(base, STEP_ARITY_INVENTORY, _arity_inventory_problems(
                inv_before,
                _rows(conn, f"SELECT id, user_id, relation, active, json FROM edges WHERE {named}", named_args),
                _rows(conn, "SELECT edge_id, user_id, pre_invalidated_at, pre_reason FROM arity_inventory")))
            _edges_unchanged(STEP_ARITY_INVENTORY)
            # step 9: the refusal inventory — EVERY refusal that exists (0044 §4f, 0018 §4a; research's R3: §4d gates
            # retention on the three names, so the inventory is not filtered by them)
            ref_before = _rows(conn, "SELECT refusal_id FROM refusal_inventory")
            conn.execute("INSERT INTO refusal_inventory(refusal_id, user_id) "
                         "SELECT refusal_id, user_id FROM supersession_refusals")
            _refuse_unless(base, STEP_REFUSAL_INVENTORY, _refusal_inventory_problems(
                ref_before, _rows(conn, "SELECT refusal_id, user_id FROM supersession_refusals"),
                _rows(conn, "SELECT refusal_id, user_id FROM refusal_inventory")))
            _edges_unchanged(STEP_REFUSAL_INVENTORY)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        stamped = conn.execute("PRAGMA user_version").fetchone()[0]
        _refuse_unless(base, STEP_STAMP, [f"user_version reads {stamped}, not {SCHEMA_VERSION}"]
                       if stamped != SCHEMA_VERSION else [])


# the v16 step's columns, by name and in a fixed order: `confirmations`' eight v15 columns, its six act columns
# (§2a's inventory), and the registry's seven
_CONF_V15_COLS = "id, user_id, edge_id, confirmed_at, actor, call_path, correlation_id, request_digest"
_CONF_ACT_COLS = "origin, recorded_correlation_id, origin_store, origin_user, origin_act_id, act_seq"
_REGISTRY_COLS = "user_id, correlation_id, verb, target_edge_id, request_digest, result_ref, written_at"
_RED_V15_COLS = ("id, user_id, target_kind, target_id, fields, marker_version, reason, store_version_before, "
                 "store_version_after, event_ref, recorded_at, source_body, source_origin, source_user, source_event_ref")


def _typed_row(row) -> tuple:
    """A row as (type, value) pairs: BYTE-equal, not merely ==-equal (an INTEGER 1 is not the TEXT '1')."""
    return tuple((type(v), v) for v in row)


def _act_counter_problems(pre: list, post: list) -> list:
    if pre:
        return [] if post == pre else [f"act_counter changed: {pre!r} -> {post!r}"]
    if [_typed_row(r) for r in post] != [_typed_row((1, 1))]:
        return [f"act_counter holds {post!r}, not exactly the one row (1, 1)"]
    return []


def _registry_backfill_problems(conf_before: list, registry_before: list, post: list, now: datetime) -> list:
    """(c): exactly one `confirm` row per pre-read confirmation, field for field, written_at the clock read."""
    out = []
    if registry_before:
        out.append(f"request_registry held {len(registry_before)} row(s) before the backfill")
    want = {(r[1], r[6]): r for r in conf_before}                     # (user_id, correlation_id) -> confirmation
    got = {}
    for r in post:
        if (r[0], r[1]) in got:
            out.append(f"request_registry holds ({r[0]!r}, {r[1]!r}) twice")
        got[(r[0], r[1])] = r
    if len(post) != len(conf_before):
        out.append(f"request_registry holds {len(post)} row(s) for {len(conf_before)} confirmation(s)")
    for key in sorted(set(want) | set(got), key=repr):
        c, g = want.get(key), got.get(key)
        if c is None:
            out.append(f"registry row {key!r} has no confirmation")
            continue
        if g is None:
            out.append(f"confirmation {c[0]!r} has no registry row")
            continue
        cid, user, edge, _at, _actor, _path, corr, digest = c
        if _typed_row(g[:6]) != _typed_row((user, corr, "confirm", edge, digest, cid)):
            out.append(f"registry row {key!r} is {g[:6]!r}, not its confirmation {c!r}")
        if not _same_instant(g[6], now):
            out.append(f"registry row {key!r} written_at {g[6]!r} is not the migration's clock read")
    return out


def _act_column_problems(conf_before: list, post: list) -> list:
    """B1: every pre-existing confirmation is byte-equal in its v15 columns, `local`, and position-less (§6f: an act
    recorded before the column existed has an UNKNOWN position — never a synthesized one). Base 1's pre-read is the
    EMPTY case, asserted, not skipped: the table must still be empty."""
    out = []
    before = {r[0]: r for r in conf_before}
    after = {r[0]: r for r in post}
    if len(post) != len(conf_before) or set(before) != set(after):
        out.append(f"confirmations went from {sorted(before)!r} to {sorted(after)!r}")
    for cid in sorted(set(before) & set(after)):
        a = after[cid]
        if _typed_row(a[:8]) != _typed_row(before[cid]):
            out.append(f"confirmation {cid!r} changed: {before[cid]!r} -> {a[:8]!r}")
        if _typed_row(a[8:]) != _typed_row(("local", None, None, None, None, None)):
            out.append(f"confirmation {cid!r} act columns are {a[8:]!r}, not ('local', NULL x5)")
    return out


def _notice_state_problems(before: list, post: list) -> list:
    """T4: every redaction row byte-equal in its fifteen v15 columns, its state DERIVED by the pre-v16 rule from the
    pre-read (event_ref NULL and a source identity -> `standing`; else `applied`), `pending_reason` NULL, and no row
    added or lost. Base < 15's pre-read is the EMPTY case, asserted: the table must still be empty."""
    out = []
    b = {r[0]: r for r in before}
    a = {r[0]: r for r in post}
    if len(post) != len(before) or set(a) != set(b):
        out.append(f"redactions went from {sorted(b)!r} to {sorted(a)!r}")
    for rid in sorted(set(a) & set(b)):
        row, pre = a[rid], b[rid]
        if _typed_row(row[:15]) != _typed_row(pre):
            out.append(f"redaction {rid!r} changed: {pre!r} -> {row[:15]!r}")
        want = "standing" if pre[9] is None and pre[12] is not None else "applied"
        if _typed_row(row[15:]) != _typed_row((want, None)):
            out.append(f"redaction {rid!r} reads {row[15:]!r}, not ({want!r}, NULL)")
    return out


def _same_instant(v, now: datetime) -> bool:
    """`v` (as stored) is the migration's clock read, as an instant; an unparseable value is simply not it."""
    try:
        return (datetime.fromisoformat(v) if isinstance(v, str) else v) == now
    except (ValueError, TypeError):
        return False


def _arity_era_problems(pre: list, post: list, now: datetime) -> list:
    """step 7: exactly the one row `(1, the migration's clock read)`; a row present before is unchanged."""
    if pre:
        return [] if post == pre else [f"arity_era changed: {pre!r} -> {post!r}"]
    if len(post) != 1 or _typed_row(post[0][:1]) != _typed_row((1,)):
        return [f"arity_era holds {post!r}, not exactly one row id=1"]
    return [] if _same_instant(post[0][1], now) else [f"arity_era.effective_at {post[0][1]!r} is not the migration's clock read"]


def _arity_inventory_problems(pre: list, edges: list, post: list) -> list:
    """step 8, from the edges' own bytes (research's T5 F2): the inventory is SET-EQUAL to the rows under the three
    default names whose json retirement is `superseded`, each row TUPLE-EQUAL to its edge's json; the table was empty
    before; and for every edge under those names the `active` column mirrors the json (`active = 0` iff
    `invalidated_at` is set) — a row where they disagree refuses the step rather than being mis-inventoried."""
    from .lifetime import SUPERSEDED
    out = []
    if pre:
        out.append(f"arity_inventory held {len(pre)} row(s) before the step")
    want = {}
    for eid, uid, rel, active, blob in edges:
        d = json.loads(blob)
        at = d.get("invalidated_at")
        if (active == 0) != (at is not None):
            out.append(f"edge {eid!r}: active={active!r} disagrees with its json invalidated_at={at!r}")
        if d.get("relation") != rel:
            out.append(f"edge {eid!r}: the relation column {rel!r} is not its json relation {d.get('relation')!r}")
        if at is not None and d.get("invalidation_reason") == SUPERSEDED:
            want[eid] = (eid, uid, at, SUPERSEDED)
    got = {}
    for r in post:
        if r[0] in got:
            out.append(f"arity_inventory holds {r[0]!r} twice")
        got[r[0]] = tuple(r)
    for eid in sorted(set(want) | set(got)):
        if eid not in got:
            out.append(f"edge {eid!r} is retired `superseded` under a reclassified name and is not inventoried")
        elif eid not in want:
            out.append(f"arity_inventory names {eid!r}, which is not a `superseded` retirement under the three names")
        elif _typed_row(got[eid]) != _typed_row(want[eid]):
            out.append(f"arity_inventory row {got[eid]!r} is not its edge's retirement {want[eid]!r}")
    return out


def _refusal_inventory_problems(pre: list, refusals: list, post: list) -> list:
    """step 9: SET-EQUAL to every refusal's (refusal_id, user_id), no duplicate, the table empty before."""
    out = [f"refusal_inventory held {len(pre)} row(s) before the step"] if pre else []
    if len(post) != len({r[0] for r in post}):
        out.append("refusal_inventory holds a refusal id twice")
    if {_typed_row(r) for r in post} != {_typed_row(r) for r in refusals}:
        out.append(f"refusal_inventory ({len(post)} row(s)) is not every refusal ({len(refusals)} row(s))")
    return out


def _identity_problems(pre: list, post: list) -> list:
    if pre:
        return [] if post == pre else [f"store_identity changed: {pre!r} -> {post!r}"]
    if len(post) != 1 or post[0][0] != 1:
        return [f"store_identity holds {post!r}, not exactly one row id=1"]
    origin = post[0][1]
    try:
        u = uuid.UUID(origin)
        ok = str(u) == origin and u.version == 4
    except (ValueError, TypeError, AttributeError):
        ok = False
    return [] if ok else [f"store_identity origin {origin!r} is not a canonical UUIDv4"]


def _epoch_problems(pre: list, post: list, now: datetime) -> list:
    if pre:
        return [] if post == pre else [f"store_epoch changed: {pre!r} -> {post!r}"]
    if len(post) != 1 or post[0][0] != 1:
        return [f"store_epoch holds {post!r}, not exactly one row id=1"]
    _id, started, schema_at = post[0]
    out = []
    if not _same_instant(started, now):
        out.append(f"store_epoch.started_at {started!r} is not the migration's clock read")
    if schema_at != 13:
        out.append(f"store_epoch.schema_at {schema_at!r} is not 13")
    return out


def _baseline_problems(conn, edges: list, rowids_before: set, now: datetime) -> list:
    added = [r for r in _rows(conn, "SELECT rowid, user_id, txn, seq, edge_id, kind, reason, state, recorded_at "
                                    "FROM edge_event ORDER BY rowid") if r[0] not in rowids_before]
    out = []
    if len(added) != len(edges):
        out.append(f"{len(added)} baseline event(s) written for {len(edges)} edge row(s)")
    by_edge = {}
    for _rid, user, txn, seq, edge_id, kind, reason, state, at in added:
        by_edge.setdefault(edge_id, []).append((user, txn, seq, kind, reason, state, at))
    for user, eid, blob in edges:
        evs = by_edge.get(eid, [])
        if len(evs) != 1:
            out.append(f"edge {eid!r}: {len(evs)} baseline events, not exactly one")
            continue
        euser, _txn, _seq, kind, reason, state, at = evs[0]
        if kind != "baseline" or reason is not None or state != blob or euser != user or not _same_instant(at, now):
            out.append(f"edge {eid!r}: its baseline event is not (baseline, NULL reason, the row's bytes, its user, "
                       f"the migration's clock read)")
    per_user = {}
    for _rid, user, txn, seq, *_ in added:
        per_user.setdefault(user, []).append((txn, seq))
    for user, ts in per_user.items():
        if len({t for t, _ in ts}) != 1:
            out.append(f"user {user!r}: baseline events span {len({t for t, _ in ts})} txns, not one")
        seqs = [s for _, s in ts]
        if seqs != list(range(seqs[0], seqs[0] + len(seqs))):
            out.append(f"user {user!r}: baseline seq is not contiguous")
    return out


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

        def _older(c, spath, found, objs, base, *, runtime):
            _apply_forward(c, base)
            pending["from_v"] = base
            pending["runtime"] = migration_runtime(runtime)
            attempted = _mig_event("migration_attempted", mid, spath, base,
                                   SCHEMA_VERSION, pending["runtime"])
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
                                   pending.get("from_v", 0), SCHEMA_VERSION, pending["runtime"])
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


# --------------------------------------------------------------------------
# The 0018 release-migration orchestrator (specs/0018 §7a): implemented in the
# sibling `release_migration` module and re-exported here as the public
# surface. `migrate_store` above stays 0013's ordinary audited operation; the
# orchestrator wraps it with the preflight matrix, mint/retry, attestation,
# result carrier, terminal readback, and the loud audit escapes.
from .release_migration import (  # noqa: E402
    MigrationAttestation, MigrationAuditReadError, MigrationAuditWriteError,
    MigrationAuthority, MigrationResult, MintError, PreflightResolution,
    ReadbackResult, TerminalFacts, mint_release_authority, read_terminal,
    run_release_migration)
# specs/0018 §4i: the per-user data-migration operation BESIDE the orchestrator (0044's restoration), same surface
from .data_migration import (  # noqa: E402
    DataMigrationResult, DataMigrationStatus, ReceiptRow, data_migration_receipt,
    data_migration_status, run_data_migration)
from ..census import declare_site

# specs/0042 (tranche 5): the enforcement points of this module, each a declared site the
# decision is returned THROUGH — consult() brackets the decision, fire() wraps the value
_SITE_MIGRATION_VERSION = declare_site("store.migration.version")
_SITE_DUPLICATE_OUTCOME_CHAIN = declare_site("store.migration.duplicate-outcome-chain")
_SITE_MIGRATION_POSTCONDITION = declare_site("store.migration.postcondition")   # specs/0013 §4f (v33, 0013-PA1)


def unattested_marker_report(store) -> list:
    """specs/0041 §4b (ruled v7): every stored record holding the marker byte string in a carrier with NO redaction
    record attesting that (record, field) — an UNATTESTED marker: bytes that carry no user content and confer no
    redacted status. Named per row AND per field, because a report that names the row without the carrier cannot
    be acted on (round 5, finding 3). A read: it changes nothing, refuses nothing, and never defaults."""
    import json as _json
    from .. import redaction as _red
    conn = store._conn
    attested = set()
    if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='redactions'").fetchone():
        for kind, tid, fields in conn.execute("SELECT target_kind, target_id, fields FROM redactions"):
            for f in _json.loads(fields):
                attested.add((kind, tid, f))
    rows = []
    for table, kind in (("edges", "edge"), ("episodes", "episode")):
        for rid, js in conn.execute(f"SELECT id, json FROM {table}"):
            for field in _red.marker_fields(_json.loads(js)):
                if (kind, rid, field) not in attested:
                    rows.append({"target_kind": kind, "target_id": rid, "field": field})
    return rows
