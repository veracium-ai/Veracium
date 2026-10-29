"""On-disk store schema versioning — the `specs/0007` kernel, in production.

**This module is the implementation `0007`'s acceptance authorises**, and it is
the shared kernel fourteen external review rounds demanded: the schema registry,
manifest/digest/drift/candidate matching, runtime-evidence validation, and the
open-time decision table. `specs/schema_model.py` and `specs/schema_evidence.py`
now import from HERE — the evidence generator uses the same declarations the
store executes, which closes the divergence rounds 6 and 8 prohibited.

The evidence artifacts ship as package data in `evidence/`:

    sqlite_runtimes.json   the attestation records (0007 §4g.6 4d): CI-measured builds; a record only removes the warning
    schema_versions.json   the accepted manifests per schema version
    legacy_stores.json     release probing evidence; source of the legacy bases

**Missing or malformed ACCEPTED evidence (`schema_versions.json`) fails closed**:
`runtime_status()` is `refused`, and the store refuses with
`unsupported-sqlite` before any version or shape decision. A missing or
malformed `sqlite_runtimes.json` only blocks attestation: the build is
`verified` (0007 §4g.3, a record can only remove the warning).
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import os
import pathlib
import platform
import re
import sqlite3
import struct
import sys
import uuid
import warnings
from datetime import datetime, timezone
from typing import NamedTuple, Optional
from ..census import declare_site

# specs/0042 (tranche 5): the enforcement points of this module, each a declared site the
# decision is returned THROUGH — consult() brackets the decision, fire() wraps the value
_SITE_OPEN_UNACCEPTED_SHAPE = declare_site("store.open.unaccepted-shape")
_SITE_OPEN_RUNTIME_UNSUPPORTED = declare_site("store.open.runtime-unsupported")
_SITE_OPEN_LOCKED = declare_site("store.open.locked")
_SITE_OPEN_INVALID_VERSION = declare_site("store.open.invalid-version")
_SITE_OPEN_NEWER = declare_site("store.open.newer")
_SITE_OPEN_LEGACY = declare_site("store.open.legacy")
_SITE_RUNTIME_REFUSED = declare_site("store.runtime-refused", declines=True)   # 0007 §4g.6 4a: both gates' ONE decision

log = logging.getLogger(__name__)

EVIDENCE_DIR = pathlib.Path(__file__).resolve().parent / "evidence"
RUNTIMES = EVIDENCE_DIR / "sqlite_runtimes.json"
VERSIONS = EVIDENCE_DIR / "schema_versions.json"
RELEASES = EVIDENCE_DIR / "legacy_stores.json"

MANIFEST_ALGORITHM = 13


_OBJECTS = ("SELECT type, name, tbl_name, sql FROM sqlite_master "
            "WHERE name NOT GLOB 'sqlite_*' ORDER BY type, name")

REBUILDABLE = "rebuildable"
REQUIRED = "required"
POLICIES = frozenset({REQUIRED, REBUILDABLE})
KINDS = frozenset({"table", "index", "view", "trigger"})
REBUILDABLE_KINDS = frozenset({"index"})
"""Only an index may be repaired by dropping and recreating it. Repairing a
table would destroy data; repairing a trigger or view silently changes
behaviour."""


class SchemaObject(NamedTuple):
    """One persistent object, declared once.

    `kind` is part of the identity because SQLite lets a trigger and an index
    share a name: keyed by name alone, a trigger overwrote a same-named index
    and the digest then skipped the key because the *name* was on the exclusion
    list, so a store carrying an arbitrary trigger digested identical to a clean
    store (round 3, measured)."""
    kind: str          # "table" | "index" | "view" | "trigger"
    name: str
    ddl: str
    policy: str        # REQUIRED (in the digest) | REBUILDABLE (repaired)

    @property
    def key(self) -> tuple:
        return (self.kind, self.name)


def validate_schema_registry() -> list:
    """Closed vocabularies, checked before anything is generated.

    **Round 7, finding 6: `policy` was an unrestricted string**, and the
    destination validator only enforced DDL when `policy == REQUIRED`. A typo —
    `"requried"` — therefore silently created a *third* behaviour that checked
    nothing. Measured: a `sources` table declared `CREATE TABLE sources (id TEXT
    PRIMARY KEY)` and migrated as `CREATE TABLE sources (id INTEGER)` produced
    **no destination problems at all**. A policy artifact records the typo just
    as faithfully, so artifact-versus-registry equality does not catch it.

    Unknown values are build errors, never implicit third behaviours."""
    problems, seen = [], []
    # **Round 11, finding 3: this guard regressed during the scope cut.** It
    # lived in the deleted `schema_migrations` module, and the round-6
    # disposition still claimed S53 enforced it. Declaring `SCHEMAS[2]` while
    # `SCHEMA_VERSION` stayed 1 produced an artifact declaring itself version 1
    # while authorising records for version 2. Measured. This is a consistency
    # condition of `0007`'s own registry, not migration machinery -- `0013` adds
    # route adjacency and reachability on top.
    if not 1 <= SCHEMA_VERSION <= 2147483647:
        problems.append(f"SCHEMA_VERSION {SCHEMA_VERSION} is outside 1..2147483647")
    if SCHEMAS and max(SCHEMAS) != SCHEMA_VERSION:
        problems.append(f"SCHEMA_VERSION is {SCHEMA_VERSION} but the registry "
                        f"declares up to {max(SCHEMAS)}; a schema above the "
                        f"current version must not exist")
    if set(SCHEMAS) != set(range(1, SCHEMA_VERSION + 1)):
        problems.append(f"registry versions {sorted(SCHEMAS)} are not the "
                        f"contiguous range 1..{SCHEMA_VERSION}")
    seen = set()
    for version, objs in sorted(SCHEMAS.items()):
        for o in objs:
            where = f"v{version} {o.kind}:{o.name}"
            if o.kind not in KINDS:
                problems.append(f"{where}: kind {o.kind!r} is not one of {sorted(KINDS)}")
            if o.policy not in POLICIES:
                problems.append(f"{where}: policy {o.policy!r} is not one of "
                                f"{sorted(POLICIES)}")
            if o.policy == REBUILDABLE and o.kind not in REBUILDABLE_KINDS:
                problems.append(f"{where}: only {sorted(REBUILDABLE_KINDS)} may be "
                                f"rebuildable — repairing a {o.kind} would destroy "
                                f"data or silently change behaviour")
            if (version, o.key) in seen:
                problems.append(f"{where}: duplicate typed key")
            seen.add((version, o.key))
    return problems


# The v1 schema, declared structurally. `ddl` is byte-identical to what SQLite
# stores in `sqlite_master.sql`, which is not the same as what `_SCHEMA` says:
# SQLite strips `IF NOT EXISTS` and preserves everything else exactly.
SCHEMA_V1 = (
    SchemaObject("table", "edges", """CREATE TABLE edges (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, subject TEXT, relation TEXT,
    object TEXT, active INTEGER NOT NULL, quarantined INTEGER NOT NULL, json TEXT NOT NULL
)""", REQUIRED),
    SchemaObject("index", "ix_edges_user_active",
                 "CREATE INDEX ix_edges_user_active ON edges(user_id, active)", REBUILDABLE),
    SchemaObject("index", "ix_edges_subj_rel",
                 "CREATE INDEX ix_edges_subj_rel ON edges(user_id, subject, relation, active)",
                 REBUILDABLE),
    SchemaObject("table", "episodes", """CREATE TABLE episodes (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, date TEXT, json TEXT NOT NULL
)""", REQUIRED),
    SchemaObject("index", "ix_episodes_user",
                 "CREATE INDEX ix_episodes_user ON episodes(user_id, date)", REBUILDABLE),
    SchemaObject("table", "wiki", """CREATE TABLE wiki (
    user_id TEXT PRIMARY KEY, text TEXT, store_version INTEGER
)""", REQUIRED),
    SchemaObject("table", "write_counter", """CREATE TABLE write_counter (
    user_id TEXT PRIMARY KEY, n INTEGER NOT NULL
)""", REQUIRED),
)

# v2 adds the `confirmations` audit table (`specs/0008` §6d) — the mandatory
# record of every `confirm_edge` transition. The DDL is byte-identical to the
# `specs/0013` v1→v2 migration that installs it: `correlation_id` is NOT NULL (an
# omitted id is generated and persisted, else replay could not find the row);
# `UNIQUE(user_id, correlation_id)` is tenant-scoped (§6c "not global"); the index
# on `(user_id, edge_id)` accelerates `confirmations_for()` and is REBUILDABLE.
SCHEMA_V2 = SCHEMA_V1 + (
    SchemaObject("table", "confirmations", """CREATE TABLE confirmations (
    id TEXT NOT NULL PRIMARY KEY, user_id TEXT NOT NULL, edge_id TEXT NOT NULL,
    confirmed_at TEXT NOT NULL, actor TEXT NOT NULL, call_path TEXT NOT NULL,
    correlation_id TEXT NOT NULL, request_digest TEXT NOT NULL,
    UNIQUE(user_id, correlation_id)
)""", REQUIRED),
    SchemaObject("index", "ix_confirmations_edge",
                 "CREATE INDEX ix_confirmations_edge "
                 "ON confirmations(user_id, edge_id)", REBUILDABLE),
)

# v3 adds the `consolidation_ops` table — the `specs/0010` fenced operation record
# (§4a): `user_id · operation_id · fence · state · owner · lease_duration ·
# lease_expires_at · claimed_ids`. It is the durable state machine for crash-safe
# consolidation; `pending_consolidations`/takeover query it by `(user_id, state)`.
# `specs/0009`'s new Episode fields (`seq`, `supersedes_episode`, `judgment_time_known`,
# and `specs/0010`'s `claimed_by`/`operation_id`/`lineage`/`date_start`/`date_end`)
# serialise into the existing `episodes.json` blob — no episode-table ALTER, so v2→v3
# stays a byte-identical additive-table migration (co-implemented: one v2→v3 bump
# carries both specs, per `0009` §9a / `0010` §9).
SCHEMA_V3 = SCHEMA_V2 + (
    SchemaObject("table", "consolidation_ops", """CREATE TABLE consolidation_ops (
    operation_id TEXT NOT NULL PRIMARY KEY, user_id TEXT NOT NULL,
    fence INTEGER NOT NULL, state TEXT NOT NULL, owner TEXT NOT NULL,
    lease_duration INTEGER NOT NULL, lease_expires_at TEXT NOT NULL,
    claimed_ids TEXT NOT NULL
)""", REQUIRED),
    SchemaObject("index", "ix_consolidation_ops_user_state",
                 "CREATE INDEX ix_consolidation_ops_user_state "
                 "ON consolidation_ops(user_id, state)", REBUILDABLE),
)

# v4 adds the two `specs/0003` supersession tables. Both are content-free and
# user-linked (opaque edge ids, relation, authority levels — never subject/object/
# note), so `forget_user` erases them and export/import exclude them (§4f). Neither is
# created opportunistically on open (round-6 blocker 2): they advance the on-disk store
# version v3→v4, a fresh store is built at v4, and a below-head store is brought forward
# by the offline `0013` migration (`Spec-Requires: 0007, 0013`).
#   - `supersession_refusals`: the durable, content-free refusal inventory (§4b). Carries
#     BOTH edge ids so `0011` can enumerate exactly which edges contended (v4 recorded only
#     the relation + authority pair and could not — fifth-round finding).
#   - `supersession_operations`: the durable whole-plan idempotency receipt (§4f, round-9
#     blocker 3). `UNIQUE(user_id, operation_id)` is tenant-scoped; a committed op REPLAYs
#     rather than re-applying after a lost response + restart.
SCHEMA_V4 = SCHEMA_V3 + (
    SchemaObject("table", "supersession_refusals", """CREATE TABLE supersession_refusals (
    refusal_id TEXT NOT NULL PRIMARY KEY, user_id TEXT NOT NULL,
    prior_edge_id TEXT NOT NULL, incoming_edge_id TEXT NOT NULL, relation TEXT NOT NULL,
    prior_effective INTEGER NOT NULL, incoming_effective INTEGER NOT NULL,
    rule_version TEXT NOT NULL, created_at TEXT NOT NULL
)""", REQUIRED),
    SchemaObject("index", "ix_supersession_refusals_user",
                 "CREATE INDEX ix_supersession_refusals_user "
                 "ON supersession_refusals(user_id)", REBUILDABLE),
    SchemaObject("table", "supersession_operations", """CREATE TABLE supersession_operations (
    user_id TEXT NOT NULL, operation_id TEXT NOT NULL,
    logical_request_digest TEXT NOT NULL, status TEXT NOT NULL,
    PRIMARY KEY (user_id, operation_id)
)""", REQUIRED),
)

# v5 adds the `specs/0006` `store_identity` singleton — the ONE piece of durable DDL
# that spec adds (R8). It holds this store's persistent `origin` (a CSPRNG UUIDv4, 122
# random bits, §4.2), the value an absent local record-`origin` resolves to at read
# (§4 rule 6). `CHECK(id = 1)` makes it a true singleton — at most one row. The
# `source_id`/`origin` PROVENANCE fields need no DDL (they serialise into `edges.json`);
# this table exists only so the local origin survives close-reopen and backup-restore
# (I11). The row is minted once — at store creation and at the offline v4→v5 migration
# (`store/migration.py::_mint_store_identity`), transactionally — never opportunistically
# per-record, and there is NO backfill (existing rows keep `origin` absent and resolve).
SCHEMA_V5 = SCHEMA_V4 + (
    SchemaObject("table", "store_identity", """CREATE TABLE store_identity (
    id INTEGER PRIMARY KEY CHECK(id = 1), origin TEXT NOT NULL
)""", REQUIRED),
)

# v6 (specs/0014) makes TWO structural changes in one migration: the additive
# `contribution_ledger` table + its three indexes, and — the repo's FIRST ALTER of an
# existing table — three new columns on `supersession_operations` (`request_digest`,
# `response`, `outcome_digest_version NOT NULL DEFAULT 1`; the DEFAULT both makes the
# ALTER executable on populated tables and IS the migration stamp — 0014 R10-3). The
# op_key UNIQUE index is REQUIRED, not rebuildable: a UNIQUE index decides which writes
# are accepted (0007 R1). Because a fresh constructor and the ALTER path legitimately
# produce DIFFERENT stored DDL for the same table, `MANIFESTS[6]` is a SET per accepted
# `0013` §4e: the constructor entry below is generated as usual, and the ALTER-path
# entry is the REVIEWED CONSTANT `ALTER_PATH_V6_SQL` (0014 §4b — authored on the
# qualified runtime, authorized by the 0014 acceptance review; the migration must
# byte-match it, never define it — `0013` §4c).
SCHEMA_V6 = tuple(
    o if o.name != "supersession_operations" else
    SchemaObject("table", "supersession_operations", """CREATE TABLE supersession_operations (
    user_id TEXT NOT NULL, operation_id TEXT NOT NULL,
    logical_request_digest TEXT NOT NULL, status TEXT NOT NULL,
    request_digest TEXT, response TEXT,
    outcome_digest_version INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (user_id, operation_id)
)""", REQUIRED)
    for o in SCHEMA_V5
) + (
    SchemaObject("table", "contribution_ledger", """CREATE TABLE contribution_ledger (
    id TEXT NOT NULL PRIMARY KEY, user_id TEXT NOT NULL,
    survivor_type TEXT NOT NULL, survivor_id TEXT NOT NULL,
    site TEXT NOT NULL,
    identity_digest TEXT, evidence_ref_digest TEXT,
    payload TEXT NOT NULL, op_key TEXT,
    created_at TEXT NOT NULL
)""", REQUIRED),
    SchemaObject("index", "ix_contribution_ledger_survivor",
                 "CREATE INDEX ix_contribution_ledger_survivor "
                 "ON contribution_ledger(user_id, survivor_type, survivor_id)", REBUILDABLE),
    SchemaObject("index", "ix_contribution_ledger_source",
                 "CREATE INDEX ix_contribution_ledger_source "
                 "ON contribution_ledger(user_id, identity_digest)", REBUILDABLE),
    SchemaObject("index", "ix_contribution_ledger_op_key",
                 "CREATE UNIQUE INDEX ix_contribution_ledger_op_key "
                 "ON contribution_ledger(op_key) WHERE op_key IS NOT NULL", REQUIRED),
)

# The REVIEWED ALTER-path stored DDL for `supersession_operations` (0014 §4b, verbatim —
# columns appended in ALTER order at the end of the `status` line, BEFORE the table-level
# PRIMARY KEY: the measured + reviewed SQLite 3.45.1 layout). The 0014 acceptance review
# authorized THIS text as content; `specs/schema_evidence.py` emits it as the second
# accepted v6 manifest (provenance `v5:constructor->v6`) after checking its sha256
# against `ALTER_PATH_V6_SHA256` — the migration must produce a byte-match, and a
# mismatch means the migration (or an unqualified runtime) is wrong, never the constant.
ALTER_PATH_V6_SQL = (
    "CREATE TABLE supersession_operations (\n"
    "    user_id TEXT NOT NULL, operation_id TEXT NOT NULL,\n"
    "    logical_request_digest TEXT NOT NULL, status TEXT NOT NULL,"
    " request_digest TEXT, response TEXT,"
    " outcome_digest_version INTEGER NOT NULL DEFAULT 1,\n"
    "    PRIMARY KEY (user_id, operation_id)\n"
    ")"
)
ALTER_PATH_V6_SHA256 = \
    "326ea1938cd8f623093b655c61c4c10a46087ccaee5a8687061d8ef2572c3dc0"

# The three ALTER statements, in the frozen order (0014 §4b/§7a). Shared by the v5->v6
# migration step; the resulting stored DDL must equal ALTER_PATH_V6_SQL byte-for-byte.
ALTERS_V5_TO_V6 = (
    "ALTER TABLE supersession_operations ADD COLUMN request_digest TEXT",
    "ALTER TABLE supersession_operations ADD COLUMN response TEXT",
    "ALTER TABLE supersession_operations ADD COLUMN "
    "outcome_digest_version INTEGER NOT NULL DEFAULT 1",
)

# The RECORDED ALTER-path stored DDL for `contribution_ledger` (the 0019 rider as
# amended by 0020/0021, C2; 0021 §7b — byte-identical to the recorded evidence
# `specs/evidence/0020/schema_v8_evidence.txt` [2]: a real database built from the
# v7 constructor, the two rider ALTERs run, sqlite_master read back on the
# qualified 3.45.1 — the 0014 `supersession_operations` precedent). The v7→v8
# migration must byte-match this text, never define it (`0013` §4c); a mismatch
# means the migration (or an unqualified runtime) is wrong, never the constant.
ALTER_PATH_V8_SQL = (
    "CREATE TABLE contribution_ledger (\n"
    "    id TEXT NOT NULL PRIMARY KEY, user_id TEXT NOT NULL,\n"
    "    survivor_type TEXT NOT NULL, survivor_id TEXT NOT NULL,\n"
    "    site TEXT NOT NULL,\n"
    "    identity_digest TEXT, evidence_ref_digest TEXT,\n"
    "    payload TEXT NOT NULL, op_key TEXT,\n"
    "    created_at TEXT NOT NULL\n"
    ", contributor_type TEXT, contributor_ref TEXT)"
)
ALTER_PATH_V8_SHA256 = \
    "027b5ca31adc2761e0fc20ebc2214021b419043e6883e7852661675146fc8174"

# The two ALTER statements, in the frozen order — the D2 migration's 0013-declared
# steps, sha-pinned in the recorded evidence ([4]: 40b66f30…, 51305388…). Shared by
# the v7->v8 migration step; the resulting stored DDL must equal ALTER_PATH_V8_SQL
# byte-for-byte (0019 rider C2/C3; 0021 §7b).
ALTERS_V7_TO_V8 = (
    "ALTER TABLE contribution_ledger ADD COLUMN contributor_type TEXT",
    "ALTER TABLE contribution_ledger ADD COLUMN contributor_ref TEXT",
)

# specs/0019: v7 is a NO-DDL bump — the `ungrounded` flag lives in
# `edges.json` (the 0006 v4→v5 precedent), so the object set is v6's,
# byte-identical. The version exists for REFUSAL honesty alone: an older
# build silently DROPPING the flag on rewrite would erase a fabrication
# signal; a v7 store refuses on pre-0019 builds instead (0007).
SCHEMA_V7 = SCHEMA_V6

# v8 (the 0019 rider as amended by 0020/0021 — C1/C2; 0021 §7b, the 0014
# amendment clause 3): `contribution_ledger` gains the TYPED CONTRIBUTOR LINK —
# `contributor_type TEXT` and `contributor_ref TEXT`, both nullable (legacy rows
# NULL; populated on every new native absorption row from the fields the shipped
# `ContributionDraft` already carries). The constructor text below is the v7 text
# with the two columns appended after `created_at` — byte-identical to the
# RECORDED evidence (`specs/evidence/0020/schema_v8_evidence.txt` [1],
# constructor sha a19bc3bf…). The refusal-bump semantics of the version are
# retained: a v8 store refuses on pre-D2 builds (0007). As at v6, the fresh
# constructor and the ALTER path legitimately produce DIFFERENT stored DDL for
# the same table, so `MANIFESTS[8]` is a SET per accepted `0013` §4e.
SCHEMA_V8 = tuple(
    o if o.key != ("table", "contribution_ledger") else
    SchemaObject("table", "contribution_ledger", """CREATE TABLE contribution_ledger (
    id TEXT NOT NULL PRIMARY KEY, user_id TEXT NOT NULL,
    survivor_type TEXT NOT NULL, survivor_id TEXT NOT NULL,
    site TEXT NOT NULL,
    identity_digest TEXT, evidence_ref_digest TEXT,
    payload TEXT NOT NULL, op_key TEXT,
    created_at TEXT NOT NULL,
    contributor_type TEXT, contributor_ref TEXT
)""", REQUIRED)
    for o in SCHEMA_V7
)

# v9 (specs/0022 §4a, accepted at external round 21): `source_revocations` —
# the APPEND-ONLY (between erasures: forget_user deletes the user's rows, specs/0008
# §6g) standing-state ledger. No UPDATE but 0041 v15's reason treatment, no `active`
# column, no row edited in place: the standing state is DERIVED as the latest row per
# (user, identity_digest) by `seq` ALONE. `seq` is the store-allocated
# per-user append ordinal; PRIMARY KEY(user_id, seq) makes an ordinal
# collision an IntegrityError the R19 operation classifies rather than a
# silent overwrite. `at` is HOST-SUPPLIED AUDIT METADATA AND ORDERS NOTHING
# (F2: a planted far-future timestamp must not make a revocation permanent —
# the append order is a fact, a clock is an input). A NEW table, so the fresh
# constructor and the additive-diff migration produce IDENTICAL stored DDL —
# one manifestation, no ALTER path.
SCHEMA_V9 = SCHEMA_V8 + (
    SchemaObject("table", "source_revocations", """CREATE TABLE source_revocations (
    user_id TEXT NOT NULL, seq INTEGER NOT NULL,
    identity_digest TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('revoke','lift')),
    at TEXT NOT NULL, reason TEXT NOT NULL,
    PRIMARY KEY (user_id, seq)
)""", REQUIRED),
    SchemaObject("index", "ix_source_revocations_user_digest",
                 "CREATE INDEX ix_source_revocations_user_digest "
                 "ON source_revocations(user_id, identity_digest)", REBUILDABLE),
)

# v10 (specs/0025, accepted v13; the CONFIRMED 0014 interface amendment): ONE
# nullable column on `supersession_operations` — `request_digest_domain TEXT`,
# the cross-era receipt carrier (§4b-v). The write rule stamps it iff the
# receipt carries a digest (NEW WRITES ONLY); migrated rows stay NULL — the
# dual-domain comparison row. The fresh constructor carries it inline:
SCHEMA_V10 = tuple(
    o if o.name != "supersession_operations" else
    SchemaObject("table", "supersession_operations", """CREATE TABLE supersession_operations (
    user_id TEXT NOT NULL, operation_id TEXT NOT NULL,
    logical_request_digest TEXT NOT NULL, status TEXT NOT NULL,
    request_digest TEXT, response TEXT,
    outcome_digest_version INTEGER NOT NULL DEFAULT 1,
    request_digest_domain TEXT,
    PRIMARY KEY (user_id, operation_id)
)""", REQUIRED)
    for o in SCHEMA_V9
)

# The v9->v10 ALTER, in the v6 convention. The table exists at v9 in TWO
# accepted DDL variants (fresh-constructor and the v5->v6 ALTER path), so the
# ALTER's measured result is TWO frozen literals — both authored EMPIRICALLY
# on the qualified SQLite 3.45.1 (columns appended at the end of the last
# column line, BEFORE the table-level PRIMARY KEY; the 0014 round-13
# discipline: the expectation is present in the reviewed tree, never derived
# by the migration).
ALTERS_V9_TO_V10 = (
    "ALTER TABLE supersession_operations ADD COLUMN request_digest_domain TEXT",
)
ALTER_PATH_V10_FROM_CONSTRUCTOR_SQL = (
    "CREATE TABLE supersession_operations (\n"
    "    user_id TEXT NOT NULL, operation_id TEXT NOT NULL,\n"
    "    logical_request_digest TEXT NOT NULL, status TEXT NOT NULL,\n"
    "    request_digest TEXT, response TEXT,\n"
    "    outcome_digest_version INTEGER NOT NULL DEFAULT 1,"
    " request_digest_domain TEXT,\n"
    "    PRIMARY KEY (user_id, operation_id)\n"
    ")"
)
ALTER_PATH_V10_FROM_CONSTRUCTOR_SHA256 = \
    "336b762fdcdac380e337785dfa8d693f4bcb7b7c7c8d9870424912c9f076c62b"
ALTER_PATH_V10_FROM_V6_ALTERPATH_SQL = (
    "CREATE TABLE supersession_operations (\n"
    "    user_id TEXT NOT NULL, operation_id TEXT NOT NULL,\n"
    "    logical_request_digest TEXT NOT NULL, status TEXT NOT NULL,"
    " request_digest TEXT, response TEXT,"
    " outcome_digest_version INTEGER NOT NULL DEFAULT 1,"
    " request_digest_domain TEXT,\n"
    "    PRIMARY KEY (user_id, operation_id)\n"
    ")"
)
ALTER_PATH_V10_FROM_V6_ALTERPATH_SHA256 = \
    "a788a8671946c5a99b311e4a0105da7fe5e867982e95d9f1be280ddddecacbe6"

# specs/0001 I13a (candidate): the v11 bump is SEMANTIC — byte-identical
# schema (the 0019 SCHEMA_V7 = SCHEMA_V6 precedent); the stamp activates
# 0007's refusal for pre-ASSISTANT readers.
SCHEMA_V11 = SCHEMA_V10

# specs/0027 §4f — the additive `edge_embedding` derived-index table (semantic
# hybrid recall). A row is a vector keyed (edge_id, embedder_id, content_digest);
# the digest — the §4e digest projection of the edge's content — binds the
# vector to the BYTES that were embedded, because edge text can change under a
# stable id. NO foreign key / ON DELETE CASCADE: ordinary retirement sets
# active=0 and RETAINS the edge row, so a cascade would never fire on it; the
# ONE path that deletes edges is compliance erasure (`forget_user`), which
# deletes this user's embedding rows explicitly inside the same transaction
# (0027 V-ERASE). The table is a regenerable derived INDEX — never exported,
# never evidence; the index is REBUILDABLE, the table REQUIRED (its absence
# would silently disable the semantic lane on a stamped-v12 store).
SCHEMA_V12 = SCHEMA_V11 + (
    SchemaObject("table", "edge_embedding", """CREATE TABLE edge_embedding (
    edge_id        TEXT    NOT NULL,
    user_id        TEXT    NOT NULL,
    embedder_id    TEXT    NOT NULL,
    content_digest TEXT    NOT NULL,
    dim            INTEGER NOT NULL,
    vec            BLOB    NOT NULL,
    built_at       TEXT    NOT NULL,
    PRIMARY KEY (edge_id, embedder_id, content_digest)
)""", REQUIRED),
    SchemaObject("index", "ix_edge_embedding_lookup",
                 "CREATE INDEX ix_edge_embedding_lookup "
                 "ON edge_embedding(user_id, embedder_id, dim)", REBUILDABLE),
)

# specs/0029 §4a/§4e — the additive v13: the `edge_event` transaction-time
# carrier (the §4a DDL, pinned EXACTLY — the SQL comments of the spec's block
# are documentation and are not carried into sqlite_master; the column shapes,
# the PK and BOTH indexes are the pinned artifact) plus the `store_epoch` row
# "in store_identity's pattern" (spec :88) — a checked single-row table whose
# guard lives in the SCHEMA, minted inside the v13 migration's ONE transaction
# beside the baseline batch and the stamp (§4e). Policies: the table REQUIRED
# ("an audit record is not derivable from current state, so its absence is
# damage, not drift" — V-INERT); the indexes REBUILDABLE (the 0027 precedent;
# the PK is the ordering backstop, the indexes are lookup accelerators).
# `epoch_txn(user)` is DERIVED from the user's `baseline` events, never stored
# (co-check 2026-09-05: a stored per-user epoch would be a second source of
# truth for something the events already determine).
SCHEMA_V13 = SCHEMA_V12 + (
    SchemaObject("table", "edge_event", """CREATE TABLE edge_event (
    user_id     TEXT    NOT NULL,
    seq         INTEGER NOT NULL,
    txn         INTEGER NOT NULL,
    edge_id     TEXT    NOT NULL,
    kind        TEXT    NOT NULL,
    reason      TEXT,
    state       TEXT    NOT NULL,
    recorded_at TEXT    NOT NULL,
    PRIMARY KEY (user_id, seq)
)""", REQUIRED),
    SchemaObject("index", "ix_edge_event_lookup",
                 "CREATE INDEX ix_edge_event_lookup ON edge_event(user_id, edge_id, seq)",
                 REBUILDABLE),
    SchemaObject("index", "ix_edge_event_txn",
                 "CREATE INDEX ix_edge_event_txn ON edge_event(user_id, txn)",
                 REBUILDABLE),
    SchemaObject("table", "store_epoch", """CREATE TABLE store_epoch (
    id INTEGER PRIMARY KEY CHECK(id = 1), started_at TEXT NOT NULL, schema_at INTEGER NOT NULL
)""", REQUIRED),
)

# specs/0027 §4g (v14, research T1's durability half) — the additive v14: the
# `policy_receipt` table. One row per recall in which a policy lane FIRED,
# keyed by the minted `recall_id`; the identity columns (policy, version,
# recorded_at) are what a reader lists by, and `receipt` is the receipt's
# JSON VERBATIM as `Memory.recall` returned it. Its ranking fields are record
# ids only (V-RECEIPT-IDS-ONLY); its policy identity fields (`policy_id`,
# `policy_version`, `tags_matched`) are HOST-SUPPLIED strings, bounded to
# identifier shape at `PolicyLane` (v14.1) and persisted verbatim — bounded,
# not content-free, 0041's class for `evidence_ref` and `source_id`; the
# `receipt` column is therefore a second blob carrier beside `edges.json`
# that 0041's enumeration must reach as such (research's pre-adoption read
# of 0041, 2026-09-14: the earlier wording here claimed "never content" of a
# column that held whatever the host passed). Policies: the table REQUIRED (an audit
# record is not derivable from current state — the 0029 `edge_event`
# argument; its absence is damage, not drift); the time index REBUILDABLE
# (a lookup accelerator; the PK is the identity). DDL only: crossing INTO
# v14 adds the objects and nothing else — no receipt exists before the table
# does — so `migrate_store` needs no data step and the constructor no row.
SCHEMA_V14 = SCHEMA_V13 + (
    SchemaObject("table", "policy_receipt", """CREATE TABLE policy_receipt (
    user_id        TEXT NOT NULL,
    recall_id      TEXT NOT NULL,
    policy_id      TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    recorded_at    TEXT NOT NULL,
    receipt        TEXT NOT NULL,
    PRIMARY KEY (user_id, recall_id)
)""", REQUIRED),
    SchemaObject("index", "ix_policy_receipt_time",
                 "CREATE INDEX ix_policy_receipt_time ON policy_receipt(user_id, recorded_at)",
                 REBUILDABLE),
)

# specs/0041 §4b / §4b-ii (v15, tranche 2, 2026-09-19) — the additive v15: two tables. `episode_event` is the
# episode journal, the same shape as `edge_event` (0029's transaction-time journal: seq/txn allocated by the
# same allocator, `state` the episode's json as found, `reason` D1's closed vocabulary), so an episode redaction is
# durable in the record AND visible in the journal — the asymmetry round 2's F3 named. `redactions` is THE
# ATTESTATION RECORD: a field is redacted iff a row here names that record and that field (§4b v7's rule; the
# marker bytes alone confer nothing). Its `fields` column is the JSON list of the carriers treated (REPLACE /
# CLEAR / DELETE), `reason` D1's vocabulary, the store version before and after, and `event_ref` the journal
# event the redaction wrote. Policies: both tables REQUIRED (an attestation or an event is not derivable from
# current state — the `edge_event` argument; absence is damage, not drift); the indexes REBUILDABLE. DDL only:
# crossing INTO v15 adds the objects and nothing else — no redaction exists before the table does — so
# `migrate_store` needs no data step and the constructor no row.
# Round 10 (R9-04/R9-05, before any release carried v15): `source_body` holds a WITNESSED redaction's foreign notice
# body — the source's field names, marker version, reason, time and store versions, canonical JSON — immutable once
# written, so a repeat import is compared against it and a relay re-exports it unchanged; NULL for a redaction this
# store originated. The local columns stay this store's own application facts.
# Round 11 (R10-03, still before any release carried v15): a witnessed redaction's SOURCE IDENTITY is held as three
# structured columns — `source_origin`, `source_user`, `source_event_ref` — compared EXACTLY, never parsed out of
# a separator-joined row id (which collided, failed to decode, and was matched by a substr prefix NUL defeated).
# NULL, all three, for a redaction this store originated. A store created from an unreleased main checkout at the
# earlier v15 shape is not supported across this change: no release ever carried v15.
SCHEMA_V15 = SCHEMA_V14 + (
    SchemaObject("table", "episode_event", """CREATE TABLE episode_event (
    user_id     TEXT    NOT NULL,
    seq         INTEGER NOT NULL,
    txn         INTEGER NOT NULL,
    episode_id  TEXT    NOT NULL,
    kind        TEXT    NOT NULL,
    reason      TEXT,
    state       TEXT    NOT NULL,
    recorded_at TEXT    NOT NULL,
    PRIMARY KEY (user_id, seq)
)""", REQUIRED),
    SchemaObject("index", "ix_episode_event_lookup",
                 "CREATE INDEX ix_episode_event_lookup ON episode_event(user_id, episode_id, seq)",
                 REBUILDABLE),
    SchemaObject("table", "redactions", """CREATE TABLE redactions (
    id                   TEXT NOT NULL PRIMARY KEY,
    user_id              TEXT NOT NULL,
    target_kind          TEXT NOT NULL,
    target_id            TEXT NOT NULL,
    fields               TEXT NOT NULL,
    marker_version       INTEGER NOT NULL,
    reason               TEXT NOT NULL,
    store_version_before INTEGER NOT NULL,
    store_version_after  INTEGER NOT NULL,
    event_ref            TEXT,
    recorded_at          TEXT NOT NULL,
    source_body          TEXT,
    source_origin        TEXT,
    source_user          TEXT,
    source_event_ref     TEXT
)""", REQUIRED),
    SchemaObject("index", "ix_redactions_target",
                 "CREATE INDEX ix_redactions_target ON redactions(user_id, target_kind, target_id)",
                 REBUILDABLE),
)

# specs/0008 v7 §2a (amendment `0047/0008-request-registry`; the owner's ruling "One bump, v15->v16", 2026-10-14:
# the programme's ONE schema step, amended in place until it ships): the per-user REQUEST REGISTRY — every verb of
# the correlation-id space (`confirm`; 0047's `reply` and 0044's `undo` when they land) writes one row in its own
# transaction, read FIRST, before any read of live edge state (§6c); the store-wide, never-reset ACT COUNTER, the
# source of an act's position `act_seq` (§6f); and `confirmations` gains the act columns (§2a's inventory). The
# registry and the counter are additive objects; the act columns are an ALTER of an existing table, so a migrated
# store's `confirmations` DDL differs from the constructor's (the v6/v8/v10 shape) — in ONE variant, because every
# accepted v15 shape holds the table in SCHEMA_V2's single DDL (installed byte-identically by the v1->v2 step).
_CONFIRMATIONS_V16_SQL = """CREATE TABLE confirmations (
    id TEXT NOT NULL PRIMARY KEY, user_id TEXT NOT NULL, edge_id TEXT NOT NULL,
    confirmed_at TEXT NOT NULL, actor TEXT NOT NULL, call_path TEXT NOT NULL,
    correlation_id TEXT NOT NULL, request_digest TEXT NOT NULL,
    origin TEXT NOT NULL DEFAULT 'local', recorded_correlation_id TEXT,
    origin_store TEXT, origin_user TEXT, origin_act_id TEXT, act_seq INTEGER,
    UNIQUE(user_id, correlation_id)
)"""
# specs/0041 §11.6.6 (amendment `0047/0041-replies`; the owner's ruling "Columns on redactions", 2026-10-14): a
# redaction row's NOTICE STATE — `applied` (an attestation: this store treated the record), `pending` (a witnessed
# notice over a record this store holds, awaiting the user's `confirm_notice`; `pending_reason` says why), `standing`
# (a witnessed notice whose record this store does not hold). Only `applied` attests. Two ALTER columns on v15's one
# `redactions` DDL; the closed values are validated at the one writer (`SqliteStore._set_notice_state`), not by CHECK.
_REDACTIONS_V16_SQL = """CREATE TABLE redactions (
    id                   TEXT NOT NULL PRIMARY KEY,
    user_id              TEXT NOT NULL,
    target_kind          TEXT NOT NULL,
    target_id            TEXT NOT NULL,
    fields               TEXT NOT NULL,
    marker_version       INTEGER NOT NULL,
    reason               TEXT NOT NULL,
    store_version_before INTEGER NOT NULL,
    store_version_after  INTEGER NOT NULL,
    event_ref            TEXT,
    recorded_at          TEXT NOT NULL,
    source_body          TEXT,
    source_origin        TEXT,
    source_user          TEXT,
    source_event_ref     TEXT,
    state                TEXT NOT NULL DEFAULT 'applied',
    pending_reason       TEXT
)"""
_V16_REPLACED = {"confirmations": _CONFIRMATIONS_V16_SQL, "redactions": _REDACTIONS_V16_SQL}
SCHEMA_V16 = tuple(
    o if o.name not in _V16_REPLACED else SchemaObject("table", o.name, _V16_REPLACED[o.name], REQUIRED)
    for o in SCHEMA_V15
) + (
    SchemaObject("table", "request_registry", """CREATE TABLE request_registry (
    user_id        TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    verb           TEXT NOT NULL,
    target_edge_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    result_ref     TEXT NOT NULL,
    written_at     TEXT NOT NULL,
    UNIQUE(user_id, correlation_id)
)""", REQUIRED),
    # non-unique, a lookup for §6g's redaction (the registry's UNIQUE is the TABLE constraint, inside the REQUIRED
    # table), so REBUILDABLE on the ix_confirmations_edge precedent: correctness never depends on it
    SchemaObject("index", "ix_request_registry_target",
                 "CREATE INDEX ix_request_registry_target ON request_registry(user_id, target_edge_id)",
                 REBUILDABLE),
    # specs/0047 §2 (T10a; the plan's one v16 step, amended in place): the subject's REPLIES, append-only, one row per
    # act, with the 0008 amendment's act columns exactly as `confirmations` carries them (§2a: `origin`, the original
    # request's id, `act_uid` = (origin_store, origin_user, origin_act_id) NULL for a local act and derived at export,
    # the position's `act_seq`). The two CHECKs are §4b's closed request shape (a target iff `resolve`, text NULL iff
    # `resolve`); `UNIQUE(user_id, correlation_id)` is C8's backstop, as on `confirmations` (research's T10a Q2).
    SchemaObject("table", "replies", """CREATE TABLE replies (
    id                      TEXT NOT NULL PRIMARY KEY,
    user_id                 TEXT NOT NULL,
    edge_id                 TEXT NOT NULL,
    kind                    TEXT NOT NULL CHECK (kind IN ('challenge', 'context', 'withdrawn-consent', 'resolve')),
    target                  TEXT,
    text                    TEXT,
    actor                   TEXT NOT NULL,
    correlation_id          TEXT NOT NULL,
    request_digest          TEXT NOT NULL,
    origin                  TEXT NOT NULL CHECK (origin IN ('local', 'imported', 'restored')),
    recorded_correlation_id TEXT,
    origin_store            TEXT,
    origin_user             TEXT,
    origin_act_id           TEXT,
    act_seq                 INTEGER,
    written_at              TEXT NOT NULL,
    CHECK ((kind = 'resolve') = (target IS NOT NULL)),
    CHECK ((kind = 'resolve') = (text IS NULL)),
    UNIQUE(user_id, correlation_id)
)""", REQUIRED),
    # the reads by edge (the gate, render, doctor, redaction): a lookup, so REBUILDABLE on the ix_request_registry_target
    # precedent
    SchemaObject("index", "ix_replies_edge",
                 "CREATE INDEX ix_replies_edge ON replies(user_id, edge_id)", REBUILDABLE),
    # §4b: a challenge is resolved AT MOST ONCE — an invariant, so REQUIRED, not a performance index (research's T10a
    # Q3): it holds against any writer, not only under the verb's lock
    SchemaObject("index", "ux_replies_resolve",
                 "CREATE UNIQUE INDEX ux_replies_resolve ON replies(user_id, target) WHERE kind = 'resolve'",
                 REQUIRED),
    SchemaObject("table", "act_counter", """CREATE TABLE act_counter (
    id       INTEGER NOT NULL PRIMARY KEY CHECK (id = 1),
    next_seq INTEGER NOT NULL
)""", REQUIRED),
) + (
    # specs/0044 §4e–§4i / 0018 amendment §4a (T5; research's R2: EVERY table the step names lands with the step, so
    # v16's DDL is read once and T6 never changes it under stores already at v16). The ERA: the step's commit time,
    # one row (D5). The two INVENTORIES are the operation-era boundary (§4f, R2-01): what was retired `superseded`
    # under the three default names, and every refusal, when the step's transaction committed — never decided from
    # a timestamp. The other five are the 0018 amendment's operation's (T6): the outcome rows, the per-user run
    # rows, the op admission record, the plan header and its relation rows.
    SchemaObject("table", "arity_era", """CREATE TABLE arity_era (
    id           INTEGER NOT NULL PRIMARY KEY CHECK (id = 1),
    effective_at TEXT NOT NULL
)""", REQUIRED),
    SchemaObject("table", "arity_inventory", """CREATE TABLE arity_inventory (
    edge_id            TEXT NOT NULL PRIMARY KEY,
    user_id            TEXT NOT NULL,
    pre_invalidated_at TEXT NOT NULL,
    pre_reason         TEXT NOT NULL
)""", REQUIRED),
    SchemaObject("index", "ix_arity_inventory_user",
                 "CREATE INDEX ix_arity_inventory_user ON arity_inventory(user_id)", REBUILDABLE),
    SchemaObject("table", "refusal_inventory", """CREATE TABLE refusal_inventory (
    refusal_id TEXT NOT NULL PRIMARY KEY,
    user_id    TEXT NOT NULL
)""", REQUIRED),
    SchemaObject("index", "ix_refusal_inventory_user",
                 "CREATE INDEX ix_refusal_inventory_user ON refusal_inventory(user_id)", REBUILDABLE),
    SchemaObject("table", "migration_outcome", """CREATE TABLE migration_outcome (
    plan_id            TEXT NOT NULL,
    user_id            TEXT NOT NULL,
    edge_id            TEXT NOT NULL,
    outcome            TEXT NOT NULL CHECK (outcome IN ('restored', 'withheld_revoked')),
    pre_invalidated_at TEXT NOT NULL,
    pre_reason         TEXT NOT NULL,
    successor_evidence TEXT NOT NULL,
    applicable         INTEGER NOT NULL CHECK (applicable IN (0, 1)),
    origin             TEXT NOT NULL CHECK (origin IN ('local', 'restored', 'imported')),
    outcome_uid        TEXT NOT NULL UNIQUE,
    undone_at          TEXT,
    undo_request_ref   TEXT,
    op_id              TEXT,
    UNIQUE(plan_id, edge_id)
)""", REQUIRED),
    SchemaObject("index", "ix_migration_outcome_edge",
                 "CREATE INDEX ix_migration_outcome_edge ON migration_outcome(user_id, edge_id)", REBUILDABLE),
    SchemaObject("table", "migration_run", """CREATE TABLE migration_run (
    plan_id      TEXT NOT NULL,
    user_id      TEXT NOT NULL,
    op_id        TEXT NOT NULL,
    committed_at TEXT NOT NULL,
    PRIMARY KEY(plan_id, user_id)
)""", REQUIRED),
    SchemaObject("table", "migration_op", """CREATE TABLE migration_op (
    op_id         TEXT NOT NULL PRIMARY KEY,
    mode          TEXT NOT NULL CHECK (mode IN ('plan_only', 'restore', 'import-convert')),
    inputs_digest TEXT NOT NULL,
    admitted_at   TEXT NOT NULL
)""", REQUIRED),
    SchemaObject("table", "plan_header", """CREATE TABLE plan_header (
    id              INTEGER NOT NULL PRIMARY KEY CHECK (id = 1),
    plan_id         TEXT NOT NULL UNIQUE,
    effective_at    TEXT NOT NULL,
    registry_digest TEXT NOT NULL,
    op_id           TEXT NOT NULL
)""", REQUIRED),
    SchemaObject("table", "reclassification_plan", """CREATE TABLE reclassification_plan (
    plan_id    TEXT NOT NULL,
    relation   TEXT NOT NULL,
    from_arity TEXT NOT NULL CHECK (from_arity = 'single'),
    to_arity   TEXT NOT NULL CHECK (to_arity = 'multi'),
    PRIMARY KEY(plan_id, relation)
)""", REQUIRED),
)

# The v15->v16 ALTER, in the v6/v8/v10 convention: the six ADD COLUMNs of §2a's inventory in its order, and the
# MEASURED result on the qualified SQLite 3.45.1 (ADD COLUMN appends to the last column line, before the table-level
# UNIQUE) frozen as a literal — the expectation is present in the reviewed tree, never derived by the migration.
ALTERS_V15_TO_V16 = (
    "ALTER TABLE confirmations ADD COLUMN origin TEXT NOT NULL DEFAULT 'local'",
    "ALTER TABLE confirmations ADD COLUMN recorded_correlation_id TEXT",
    "ALTER TABLE confirmations ADD COLUMN origin_store TEXT",
    "ALTER TABLE confirmations ADD COLUMN origin_user TEXT",
    "ALTER TABLE confirmations ADD COLUMN origin_act_id TEXT",
    "ALTER TABLE confirmations ADD COLUMN act_seq INTEGER",
)
ALTER_PATH_V16_CONFIRMATIONS_SQL = (
    "CREATE TABLE confirmations (\n"
    "    id TEXT NOT NULL PRIMARY KEY, user_id TEXT NOT NULL, edge_id TEXT NOT NULL,\n"
    "    confirmed_at TEXT NOT NULL, actor TEXT NOT NULL, call_path TEXT NOT NULL,\n"
    "    correlation_id TEXT NOT NULL, request_digest TEXT NOT NULL,"
    " origin TEXT NOT NULL DEFAULT 'local', recorded_correlation_id TEXT,"
    " origin_store TEXT, origin_user TEXT, origin_act_id TEXT, act_seq INTEGER,\n"
    "    UNIQUE(user_id, correlation_id)\n"
    ")"
)
ALTER_PATH_V16_CONFIRMATIONS_SHA256 = \
    "a82ee8e86bb5a4730785a37998e15ed514bc497c3152e5f2243e838b4782fdc8"

# The v15->v16 ALTER of `redactions` (0041 §11.6.6; T4): only a base-15 store holds the table (it entered at v15), in
# ONE DDL; a base <= 14 gets it from the additive diff in its v16 constructor form. MEASURED on SQLite 3.45.1: with no
# table-level constraint after the last column, ADD COLUMN appends on its own line before the closing parenthesis.
ALTERS_V15_TO_V16_REDACTIONS = (
    "ALTER TABLE redactions ADD COLUMN state TEXT NOT NULL DEFAULT 'applied'",
    "ALTER TABLE redactions ADD COLUMN pending_reason TEXT",
)
ALTER_PATH_V16_REDACTIONS_SQL = (
    "CREATE TABLE redactions (\n"
    "    id                   TEXT NOT NULL PRIMARY KEY,\n"
    "    user_id              TEXT NOT NULL,\n"
    "    target_kind          TEXT NOT NULL,\n"
    "    target_id            TEXT NOT NULL,\n"
    "    fields               TEXT NOT NULL,\n"
    "    marker_version       INTEGER NOT NULL,\n"
    "    reason               TEXT NOT NULL,\n"
    "    store_version_before INTEGER NOT NULL,\n"
    "    store_version_after  INTEGER NOT NULL,\n"
    "    event_ref            TEXT,\n"
    "    recorded_at          TEXT NOT NULL,\n"
    "    source_body          TEXT,\n"
    "    source_origin        TEXT,\n"
    "    source_user          TEXT,\n"
    "    source_event_ref     TEXT\n"
    ", state TEXT NOT NULL DEFAULT 'applied', pending_reason TEXT)"
)
ALTER_PATH_V16_REDACTIONS_SHA256 = \
    "8494279ce8b1c6b8ccd8f91184978b063b89fbfd9bc9dc1ab6a447226bb01f17"

SCHEMAS = {1: SCHEMA_V1, 2: SCHEMA_V2, 3: SCHEMA_V3, 4: SCHEMA_V4, 5: SCHEMA_V5,
           6: SCHEMA_V6, 7: SCHEMA_V7, 8: SCHEMA_V8, 9: SCHEMA_V9,
           10: SCHEMA_V10,
           11: SCHEMA_V11, 12: SCHEMA_V12, 13: SCHEMA_V13, 14: SCHEMA_V14, 15: SCHEMA_V15,
           16: SCHEMA_V16}

SCHEMA_VERSION = 16
"""**Declared, not inferred.**

v6 used `max(SCHEMAS)`, so adding or removing a registry entry silently changed
which version received mutable treatment in the generated artifact (round 5,
finding 5). Bumped 1→2 for `specs/0008`'s `confirmations` table, installed by the
`specs/0013` v1→v2 offline migration."""


def rebuildable_keys(version: int = SCHEMA_VERSION) -> set:
    return {o.key for o in SCHEMAS[version] if o.policy == REBUILDABLE}


def mint_act_counter(conn: sqlite3.Connection) -> None:
    """specs/0008 v7 §6f — the store-wide act counter's ONE row, `(1, 1)`: the next act takes position 1. Idempotent
    on the fixed `id = 1` (`INSERT OR IGNORE`), so a re-attempted migration or a create-then-open never resets it.
    Only creation and the v16 migration call it; an act WRITER never does — a lost row refuses there (0008 §6f's
    never-reset rule: a re-mint would reissue positions already exported)."""
    conn.execute("INSERT OR IGNORE INTO act_counter(id, next_seq) VALUES(1, 1)")


def mint_arity_era(conn: sqlite3.Connection, effective_at: str) -> None:
    """specs/0044 §4f / 0018 amendment §4a (D5) — the arity era's ONE row, `(1, effective_at)`: the v16 step's commit
    time (the migration's one clock read), or a new store's creation time. Idempotent on the fixed `id = 1`
    (`INSERT OR IGNORE`), so a re-attempted migration or a create-then-open never moves it. Only creation and the v16
    step call it."""
    conn.execute("INSERT OR IGNORE INTO arity_era(id, effective_at) VALUES(1, ?)", (effective_at,))


def _mint_store_identity(conn: sqlite3.Connection) -> None:
    """specs/0006 §4.2 — mint the store's durable `origin` singleton if absent.

    A canonical UUIDv4 from the platform CSPRNG (`uuid.uuid4` draws from
    `os.urandom`), 122 random bits, one canonical textual encoding. Idempotent:
    `INSERT OR IGNORE` on the fixed `id = 1`, so a re-attempted migration or a
    create-then-open never changes an existing origin — the value must survive
    close-reopen and backup-restore (I11). Runs INSIDE the caller's open
    transaction (create / migrate), never opportunistically per-record, and there
    is NO backfill — existing edge rows keep `origin` absent and resolve to it."""
    conn.execute(
        "INSERT OR IGNORE INTO store_identity(id, origin) VALUES(1, ?)",
        (str(uuid.uuid4()),))


def create(conn: sqlite3.Connection, version: int = SCHEMA_VERSION) -> None:
    """Build a database from the registry, statement by statement.

    Never `executescript`: it issues an implicit COMMIT, so it cannot run inside
    the open transaction 0007 §4c requires (measured, and independently
    confirmed by the reviewer)."""
    for o in SCHEMAS[version]:
        conn.execute(o.ddl)
    # specs/0006 §4.2 — a fresh store gets its durable origin singleton at creation,
    # before any resolution can occur. Row data, not shape, so the manifest/digest
    # validation (shape-only) is unaffected.
    if version >= 5:
        _mint_store_identity(conn)
    # specs/0029 §4e: a NEW v13+ store's journaling epoch is its creation —
    # every write is journaled from the first, epoch_txn(user) = 0. Row data,
    # not shape (the runtime gate rebuilds EVERY version through here).
    if version >= 13:
        from .edge_events import mint_store_epoch
        mint_store_epoch(conn, datetime.now(timezone.utc).isoformat(), version)
    # specs/0008 v7 §6f: a NEW v16+ store's act counter starts at its creation — the first act takes position 1.
    # specs/0044 §4f (D5): a NEW v16+ store's arity era starts at its creation, with the creation clock read. Its
    # inventories are EMPTY: nothing was retired or refused under the old rule, because the store never held one.
    if version >= 16:
        mint_act_counter(conn)
        mint_arity_era(conn, datetime.now(timezone.utc).isoformat())


def manifest(conn: sqlite3.Connection) -> dict:
    """Every non-internal persistent object, keyed by `(type, name)`.

    Takes an open connection, not a path: `SqliteStore(":memory:")` is a
    supported constructor, and reopening `":memory:"` yields a *different, empty*
    database (round 2, measured).

    **The stored DDL is kept byte-for-byte.** Collapsing whitespace also rewrites
    the inside of quoted literals, and two schemas differing only in
    `CHECK(object <> 'a  b')` versus `'a b'` accept exactly opposite values
    (round 3, measured)."""
    objs = {}
    for typ, name, tbl, sql in conn.execute(_OBJECTS).fetchall():
        entry = {"type": typ, "table": tbl, "sql": sql}
        if typ == "table":
            # `table_xinfo`, not `table_info`: the latter omits generated
            # columns entirely. The name is passed as a VALUE to the
            # table-valued pragma -- a table name read out of a foreign file is
            # an identifier chosen by whoever wrote that file.
            entry["columns"] = [
                [r[1], (r[2] or "").upper(), int(r[3]),
                 None if r[4] is None else str(r[4]), int(r[5]), int(r[6])]
                for r in conn.execute(
                    "SELECT * FROM pragma_table_xinfo(?)", (name,))]
        objs[(typ, name)] = entry
    return objs


def identity(objs: dict) -> dict:
    """The version-independent record: every typed object, nothing excluded.

    `digest()` cannot be a store's identity, because which objects it excludes
    depends on the version's rebuildable policy — and resolving an unstamped
    store means not knowing the version yet (round 4, measured)."""
    return {f"{k[0]}:{k[1]}": v for k, v in sorted(objs.items())}


def digest(objs: dict, version: int = SCHEMA_VERSION) -> str:
    """sha256 over every object except the rebuildable ones *of `version`*.

    Exact set equality falls out rather than being a separate rule."""
    skip = rebuildable_keys(version)
    scoped = {k: v for k, v in identity(objs).items()
              if tuple(k.split(":", 1)) not in skip}
    return hashlib.sha256(
        json.dumps(scoped, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def drift(objs: dict, version: int = SCHEMA_VERSION) -> list:
    """Rebuildable objects that are missing, or present with the wrong DDL.

    Typed keys, so a repair can only ever drop an *index*."""
    return sorted(o.key for o in SCHEMAS[version]
                  if o.policy == REBUILDABLE and objs.get(o.key, {}).get("sql") != o.ddl)


def resolve(objs: dict, records: dict, candidates=None) -> int | None:
    """Which schema version this store is, by trying each candidate's policy.

    `candidates` restricts the search — for version-zero resolution it is
    `LEGACY_BASE_VERSIONS`, the versions whose release evidence shows an
    unstamped store, **not every version in `MANIFESTS`**. v6 tried every known
    version, so an unstamped *version-2* shape resolved to 2 even though only
    version 1 was ever a legitimate unstamped base (round 5, finding 3).

    Returns None when nothing matches **or when more than one does** — an
    ambiguous answer needs an explicit rule, not a silent pick."""
    hits = set()
    for v, rec in records.items():
        version = int(v)
        if candidates is not None and version not in candidates:
            continue
        if version not in SCHEMAS:
            continue          # a version this build no longer constructs
        if any(a["digest"] == digest(objs, version) for a in rec["accepted"]):
            hits.add(version)
    return hits.pop() if len(hits) == 1 else None


def _feature_probes() -> dict:
    """Behaviours the manifest actually depends on.

    A version number names a release, not a build. Two builds of `3.45.1` can
    differ in compile options, authorizer availability and DDL support — all of
    which the exact-match model leans on (round 5, finding 6)."""
    # Closed on every path, a raising probe included: an unclosed connection
    # surfaces as a ResourceWarning on Python >= 3.13 at every store open
    # (reported by the workflow platform, 2026-09-29).
    with contextlib.closing(sqlite3.connect(":memory:")) as c:
        out = {}
        try:
            c.execute("CREATE TABLE t (a TEXT, b TEXT GENERATED ALWAYS AS (a) VIRTUAL)")
            out["generated_columns"] = True
        except sqlite3.DatabaseError:
            out["generated_columns"] = False
        # No authorizer probe: with migrations out of 0007's scope (v10) nothing
        # here installs one. `specs/0013` owns migration confinement and should
        # probe it where it is used.
        # Round 7, finding 5: this probe used `CREATE TABLE s (a) STRICT`, which is
        # invalid -- a strict table's column must declare a datatype. It therefore
        # recorded `strict_tables: False` on a runtime that fully supports them.
        # Measured on 3.46.1. A probe that fails for the wrong reason is worse than
        # no probe: it records a false property as evidence.
        try:
            c.execute("CREATE TABLE s (a TEXT) STRICT")
            out["strict_tables"] = True
        except sqlite3.DatabaseError:
            # Recorded as part of runtime identity, but NOT required: nothing in
            # `0007`'s schema matching uses strict tables (round 11). Being explicit
            # beats listing it among required behaviours and not enforcing it.
            out["strict_tables"] = False
        # ...and this one only checked that a row existed, which cannot establish
        # that DDL is stored verbatim. Submit distinctive text and compare it.
        # Writing this probe found that "verbatim" was too strong a word for what
        # the manifest actually needs. SQLite normalises the whitespace *before* the
        # object name -- `CREATE TABLE  vp` is stored as `CREATE TABLE vp` -- while
        # preserving the body exactly. The property §4a depends on is body
        # preservation, which is why two-space and one-space CHECK literals produce
        # different digests. Probe the property, not the slogan.
        marker = ("CREATE TABLE verbatim_probe ( a   TEXT ,\n"
                  "  b TEXT DEFAULT 'x  y' , c TEXT CHECK(c <> 'p  q') )")
        c.execute(marker)
        stored = c.execute(
            "SELECT sql FROM sqlite_master WHERE name='verbatim_probe'").fetchone()[0]
        out["preserves_ddl_body"] = stored[stored.index("("):] == marker[marker.index("("):]
        # `table_xinfo` must expose a generated column with a nonzero hidden flag --
        # the property §4a-ii depends on.
        out["xinfo_exposes_generated"] = any(
            r[1] == "b" and int(r[6]) != 0
            for r in c.execute("SELECT * FROM pragma_table_xinfo('t')"))
    return out


def _probe_build() -> tuple:
    """(`sqlite_source_id()`, the sorted `PRAGMA compile_options`), read on ONE scratch connection of this module's own
    `sqlite3`, the library the store's connections use (§4d v0.7)."""
    with contextlib.closing(sqlite3.connect(":memory:")) as c:
        source_id = c.execute("SELECT sqlite_source_id()").fetchone()[0]
        options = sorted(str(r[0]) for r in c.execute("PRAGMA compile_options"))
    return source_id, options


def runtime_identity() -> dict:
    source_id, _options = _probe_build()
    return {"sqlite_version": sqlite3.sqlite_version,
            "source_id": source_id,
            "features": _feature_probes()}


FEATURE_KEYS = frozenset({"generated_columns", "strict_tables",
                          "preserves_ddl_body", "xinfo_exposes_generated"})
"""The closed feature vocabulary. Every probe result is a real bool -- round 12
measured `strict_tables: 1` passing dict equality because Python's `1 == True`,
while the canonical JSON identity correctly distinguished them, so the
production predicate and the declared identity disagreed."""


def manifestation_problems(objs: dict, version: int, schemas=None) -> list:
    """A recorded manifestation must be EXACTLY the declared object set.

    Round 9, finding 1a: a self-consistent fabrication was accepted — hashing
    proves internal consistency, not provenance, so a manifestation may contain
    only objects this build declares.

    **Round 12, finding 2: "no extras" was only half of "exact".** A record with
    a *missing* object — including a missing required table — passed the
    validator once its digest was updated to match, and only the production
    predicate's separate full-comparison recovered safety. The key set must
    equal the declaration, and every entry must have the closed field shape."""
    registry = SCHEMAS if schemas is None else schemas     # an explicit registry: the 0013 model's draft, unpatched
    declared = {f"{o.kind}:{o.name}" for o in registry[version]}
    problems = [f"manifestation for v{version} contains undeclared object {k!r}"
                for k in sorted(set(objs) - declared)]
    problems += [f"manifestation for v{version} is missing declared object {k!r}"
                 for k in sorted(declared - set(objs))]
    for k, entry in sorted(objs.items()):
        if not isinstance(entry, dict):
            problems.append(f"object {k!r} is not a mapping")
            continue
        # A genuinely closed structure: exact field set, typed fields, exact
        # column-row width. Round 13's correction — "closed" had meant only
        # "these fields are present", so arbitrary extras and mistyped values
        # passed.
        want_fields = ({"type", "table", "sql", "columns"} if k.startswith("table:")
                       else {"type", "table", "sql"})
        if set(entry) != want_fields:
            problems.append(f"object {k!r} fields {sorted(entry)} are not exactly "
                            f"{sorted(want_fields)}")
            continue
        for f in ("type", "table"):
            if not isinstance(entry[f], str):
                problems.append(f"object {k!r} field {f!r} is not a string")
                break
        else:
            # Round 14 (non-blocking): "structurally valid" now also means
            # internally consistent, not merely typed. The full attestation
            # already rejected these; the record validator should say why.
            kind, _, name = k.partition(":")
            if entry["type"] != kind:
                problems.append(f"object {k!r} declares type {entry['type']!r}, "
                                f"disagreeing with its key")
            declared = {o.key: o for o in registry.get(version, ())}
            own = declared.get((kind, name))
            if own is not None:
                want_tbl = name if kind == "table" else own.ddl.split(" ON ")[-1].split("(")[0].strip() if kind == "index" else entry["table"]
                if kind in ("table", "index") and entry["table"] != want_tbl:
                    problems.append(f"object {k!r} claims table {entry['table']!r}, "
                                    f"expected {want_tbl!r}")
        if entry["sql"] is None:
            # every object 0007 declares is explicit DDL; only sqlite's own
            # autoindexes lack stored SQL and those never enter a manifestation
            problems.append(f"object {k!r} has null SQL; declared objects are "
                            f"explicit")
        elif not isinstance(entry["sql"], str):
            problems.append(f"object {k!r} field 'sql' is not a string")
        if k.startswith("table:"):
            cols = entry["columns"]
            if not isinstance(cols, list):
                problems.append(f"table {k!r} columns is not a list")
            else:
                names = []
                for row in cols:
                    if (not isinstance(row, list) or len(row) != 6
                            or not isinstance(row[0], str) or not row[0]
                            or not isinstance(row[1], str)
                            or type(row[2]) is not int or row[2] not in (0, 1)
                            or not (row[3] is None or isinstance(row[3], str))
                            or type(row[4]) is not int or row[4] < 0
                            or type(row[5]) is not int or row[5] not in (0, 1, 2, 3)):
                        problems.append(f"table {k!r} has a malformed column row")
                        break
                    names.append(row[0])
                if len(names) != len(set(names)):
                    problems.append(f"table {k!r} has duplicate column names")
    return problems


# --------------------------------------------------------------------------
# the SQLite attestation (0007 §4g, v17): a build is `attested`, `verified` or
# `refused` BY MEASUREMENT on every open; ONE canonicaliser for the attestation
# key; records that can only remove the warning, never widen what is accepted

MACHINE_ALIASES = {"amd64": "x86_64", "arm64": "aarch64"}
"""CLOSED (§4d): once lower-cased, Windows reports `amd64`/`arm64` and macOS `arm64` for the instruction sets Linux
reports as `x86_64`/`aarch64`. Every other value is its own key: `i686` is NOT `x86_64`."""
_MACHINE_RE = re.compile(r"[a-z0-9_]+")
_SYSTEM_RE = re.compile(r"[A-Za-z0-9_]+")
LIBC_TOKENS = frozenset({"glibc", "musl", "none"})
KEY_FIELDS = ("sqlite_version", "source_id", "features", "compile_options_digest", "machine", "system", "libc")
RUNTIME_STATUSES = ("attested", "verified", "refused")
"""THE status vocabulary (§4a), one source: production's INV-SA11 grammar is it minus `refused` (a refused build never
migrates), and the 0013 model's operation row admits all three (its authority is consumed before the gate refuses)."""

CONFINEMENT_PROBE_KEYS = frozenset({
    "authorizer_api_available", "denies_begin", "denies_commit", "denies_end", "denies_rollback", "denies_savepoint",
    "denies_release", "denies_pragma", "denies_attach", "denies_detach", "denies_temp_table", "denies_temp_index",
    "denies_temp_view", "denies_temp_trigger", "denies_temp_virtual_table", "authorizer_restored"})
"""The sixteen confinement probes an attestation record carries as provenance, each True (§4d, 0013 §5f.3)."""


def canonical_machine(raw) -> str | None:
    """THE machine canonicaliser, for the running build and for a record alike: lower-cased, the closed alias map,
    by fullmatch over `[a-z0-9_]+` (a trailing newline is not admitted); anything else is unreadable (None)."""
    if not isinstance(raw, str):
        return None
    m = raw.lower()
    m = MACHINE_ALIASES.get(m, m)
    return m if _MACHINE_RE.fullmatch(m) else None


def canonical_system(raw) -> str | None:
    """`platform.system()` exactly as returned, by fullmatch over `[A-Za-z0-9_]+`; anything else is unreadable."""
    return raw if isinstance(raw, str) and _SYSTEM_RE.fullmatch(raw) else None


def canonical_libc(system, interp) -> str | None:
    """Linux: `glibc` or `musl` from the interpreter's ELF `PT_INTERP` basename (`ld-linux-*`, `ld-musl-*`), never
    `platform.libc_ver()`; no interpreter or another pattern is unreadable. Every other system: `none`."""
    if system != "Linux":
        return "none" if canonical_system(system) is not None else None
    if not isinstance(interp, str) or not interp:
        return None
    base = os.path.basename(interp)
    return "glibc" if base.startswith("ld-linux-") else "musl" if base.startswith("ld-musl-") else None


def _pt_interp(path: str) -> str | None:
    """The `PT_INTERP` path of the ELF file at `path`, or None (not ELF, static, unreadable, malformed). Total.

    It SEEKS to the program headers and to the segment, never reading a fixed window: uv's python-build-standalone
    aarch64 CPython keeps PT_INTERP at ~19.7 MiB in a 23 MB image, so the earlier 1 MiB window read b"" there and
    every uv user on arm64 Linux read libc-unreadable (0007 CI run 1, 2026-10-27; research's measurement). The
    segment's size is bounded, exactly that many bytes must be read, and they must end in one NUL: a short, empty or
    unterminated INTERP is None, never ''."""
    try:
        with open(path, "rb") as f:
            hdr = f.read(64)
            if len(hdr) < 52 or hdr[:4] != b"\x7fELF" or hdr[4] not in (1, 2) or hdr[5] not in (1, 2):
                return None
            wide, end = hdr[4] == 2, "<" if hdr[5] == 1 else ">"
            if wide:
                if len(hdr) < 64:
                    return None
                phoff, = struct.unpack_from(end + "Q", hdr, 0x20)
                phentsize, phnum = struct.unpack_from(end + "HH", hdr, 0x36)
            else:
                phoff, = struct.unpack_from(end + "I", hdr, 0x1C)
                phentsize, phnum = struct.unpack_from(end + "HH", hdr, 0x2A)
            if phentsize < (56 if wide else 32) or not 0 < phnum <= _MAX_PHNUM:
                return None
            f.seek(phoff)
            table = f.read(phentsize * phnum)
            if len(table) != phentsize * phnum:
                return None
            for i in range(phnum):
                o = i * phentsize
                if struct.unpack_from(end + "I", table, o)[0] != 3:          # PT_INTERP
                    continue
                if wide:
                    off, = struct.unpack_from(end + "Q", table, o + 8)
                    size, = struct.unpack_from(end + "Q", table, o + 32)
                else:
                    off, = struct.unpack_from(end + "I", table, o + 4)
                    size, = struct.unpack_from(end + "I", table, o + 16)
                if not 2 <= size <= _MAX_INTERP:                       # a path and its NUL, bounded
                    return None
                f.seek(off)
                raw = f.read(size)
                if len(raw) != size or raw[-1:] != b"\0" or b"\0" in raw[:-1]:
                    return None
                return raw[:-1].decode("ascii")
            return None
    except (OSError, struct.error, UnicodeDecodeError, ValueError, OverflowError):
        return None


_MAX_PHNUM = 4096
_MAX_INTERP = 4096


PROCESS_IMAGE = "/proc/self/exe"
"""Whose `PT_INTERP` names `libc` (stage-1 item 10(c), measured): the PROCESS IMAGE, never `sys.executable`. Started
through the loader (`/lib64/ld-linux-x86-64.so.2 python3`) `sys.executable` still reads glibc while the image is the
loader itself, which has no `PT_INTERP`: unreadable, so at most `verified`. The image fails closed wherever the file
`sys.executable` names is not what runs (a loader launch, an embedding host, a wrapper)."""


def canonical_platform() -> dict:
    """The running process's `machine`, `system` and `libc`, each through the one canonicaliser (None = unreadable;
    an empty `platform.machine()` fails the pattern and is unreadable too)."""
    system = canonical_system(platform.system())
    interp = _pt_interp(PROCESS_IMAGE) if system == "Linux" else None
    return {"machine": canonical_machine(platform.machine()), "system": system,
            "libc": canonical_libc(system, interp)}


def options_digest(options) -> str:
    """THE compile-options digest (§4d v0.7), the one function the CI writer imports: sha256 of the options sorted and
    newline-joined, UTF-8, no trailing newline. The order a build returns them in is not identity."""
    return hashlib.sha256("\n".join(sorted(str(o) for o in options)).encode("utf-8")).hexdigest()


def compile_options_digest() -> str:
    return options_digest(_probe_build()[1])


def attestation_identity() -> dict:
    """This build's attestation key fields (§4d): `runtime_identity()`'s three, the compile-options digest, and the
    canonical platform. A None field is unreadable: the build matches no record and is at most `verified`."""
    me = runtime_identity()
    return {"sqlite_version": me["sqlite_version"], "source_id": me["source_id"], "features": me["features"],
            "compile_options_digest": compile_options_digest(), **canonical_platform()}


def attestation_key(r) -> tuple | None:
    """The full attestation key of an identity or a record, or None when any field is missing, unreadable or
    mistyped. The features compare as a fixed-order tuple of exact bools, never by dict equality (`1 == True`,
    round 12)."""
    if not isinstance(r, dict) or any(r.get(k) is None for k in KEY_FIELDS):
        return None                                     # an unreadable field matches nothing, before any comparison
    f = r["features"]
    if not isinstance(f, dict) or set(f) != FEATURE_KEYS or any(type(v) is not bool for v in f.values()):
        return None
    if not all(isinstance(r[k], str) for k in KEY_FIELDS if k != "features"):
        return None
    return (r["sqlite_version"], r["source_id"], tuple(f[k] for k in sorted(FEATURE_KEYS)),
            r["compile_options_digest"], r["machine"], r["system"], r["libc"])


# -- verification (§4b): probes, reproduction against the ONE accepted set, discrimination --------------------------

class VerificationFailure(Exception):
    """The first failing step of §4b, worded as §4e's refusal names it."""


def _accepted_constructor_entry(version: int, records=None) -> dict:
    """The ONE accepted entry whose provenance is `constructor v{version}`; zero or several refuse (D3)."""
    rec = (version_records() if records is None else records).get(str(version))
    if not isinstance(rec, dict) or not isinstance(rec.get("accepted"), list):
        raise VerificationFailure(f"schema v{version}: no accepted evidence")
    hits = [a for a in rec["accepted"] if isinstance(a, dict) and a.get("provenance") == f"constructor v{version}"]
    if len(hits) != 1 or not isinstance(hits[0].get("objects"), dict):
        raise VerificationFailure(f"schema v{version}: {len(hits)} accepted constructor manifestations, not one"
                                  if len(hits) != 1 else f"schema v{version}: its accepted constructor entry has no "
                                                         f"objects")
    return hits[0]


def _first_difference(got: dict, want: dict) -> str:
    for k in sorted(set(got) | set(want)):
        if got.get(k) != want.get(k):
            return k
    return "(none)"


def _near_miss_objects(nm, head_version: int) -> dict:
    from . import near_misses
    variant = near_misses.head_variant(nm, SCHEMAS[head_version])
    return _built_objects(lambda c: [c.execute(ddl) for ddl in variant])


def verify_reproduction(records, schemas, build=None) -> None:
    """§4b step 2 alone, over EXPLICIT arguments: for every version `schemas` declares, its constructor DDL rebuilt in
    memory must equal the ONE accepted constructor entry of `records`, complete manifestation and digest. Reproduction
    is a property of the (build, schema) pair, so this is the step the 0013 model runs on its draft registry and its
    one byte snapshot, by argument, with nothing patched or re-read (research's stage-1 read of I3(b), B1 (α′) and its
    follow-up, condition 1); `verify_build` runs it on the production registry and evidence, through `create()`
    (`build`, research's stage 2 on 8ed96ff, F1: one constructor for the gate and the generator). `build(v)`
    returns version v's constructor objects; the default rebuilds `schemas[v]`'s DDL alone, for a registry this
    module's `create()` does not serve."""
    for v in sorted(schemas):
        entry = _accepted_constructor_entry(v, records)
        objs = (build(v) if build is not None
                else _built_objects(lambda c, ddls=[o.ddl for o in schemas[v]]: [c.execute(d) for d in ddls]))
        if objs != entry["objects"]:
            raise VerificationFailure(f"schema v{v}: {_first_difference(objs, entry['objects'])} differs from the "
                                      f"accepted manifest")
        accepted = {a.get("digest") for a in records[str(v)]["accepted"] if isinstance(a, dict)}
        if _digest_of_identity(objs, v, schemas) not in accepted:
            raise VerificationFailure(f"schema v{v}: its constructor digest is not in the accepted set")


def verify_build() -> None:
    """§4b's three steps, in order; raises VerificationFailure naming the FIRST failing step. Never consults a
    record: a record adds provenance, never replaces the measurement (INV-SA1), and the comparison is against the
    ACCEPTED evidence, digest AND complete manifestation (INV-SA3)."""
    from . import near_misses
    records = version_records()                         # read ONCE per verification: package data, parsed once
    probes = _feature_probes()
    for name in ("preserves_ddl_body", "xinfo_exposes_generated"):
        if probes.get(name) is not True:
            raise VerificationFailure(f"feature probe {name} is {probes.get(name)!r}")
    verify_reproduction(records, SCHEMAS, _constructor_objects)
    accepted_head = [a.get("objects") for a in records[str(SCHEMA_VERSION)]["accepted"] if isinstance(a, dict)]
    kinds = {nm.kind for nm in near_misses.NEAR_MISSES}
    if kinds != set(near_misses.REQUIRED_KINDS):
        raise VerificationFailure(f"the near-miss set covers {sorted(kinds)}, not every required kind")
    for nm in near_misses.NEAR_MISSES:
        objs = _near_miss_objects(nm, SCHEMA_VERSION)
        if objs in accepted_head:                       # not only != the constructor: outside EVERY accepted head shape
            raise VerificationFailure(f"near-miss {nm.name} was not told apart")


# -- attestation records (§4d; 0007 I4): the full key, any number of keys, conflicts and duplicates poison ----------

_RECORD_FIELDS = frozenset(KEY_FIELDS) | {"manifest_algorithm", "schema_version", "result_digest", "confinement",
                                          "provenance"}
_PROVENANCE_FIELDS = frozenset({"route", "runner_image", "run_id", "job_id", "commit"})
ARTIFACT_KEYS = frozenset({"attestations"})
"""The runtime artifact's CLOSED top level. 0007 v16's `runtimes` record class is retired (0007 §4g.6 4f): a build
is supported by MEASUREMENT, and an attestation record only removes the warning."""
_HEX64 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


def attestations() -> list:
    """The attestation records, read fresh (package data). Raises ValueError on an artifact whose top level is not
    exactly ARTIFACT_KEYS' members: the caller reads that as a poisoned artifact."""
    if not RUNTIMES.exists():
        return []
    data = json.loads(RUNTIMES.read_text())
    if not isinstance(data, dict) or not set(data) <= ARTIFACT_KEYS:
        raise ValueError(f"the runtime artifact's top level is not within {sorted(ARTIFACT_KEYS)}")
    out = data.get("attestations", [])
    if not isinstance(out, list):
        raise ValueError("'attestations' is not a list")
    return out


def _provenance_problems(prov) -> list:
    if not isinstance(prov, list) or not prov:
        return ["'provenance' must be a nonempty list"]
    for j in prov:
        if not isinstance(j, dict) or set(j) != _PROVENANCE_FIELDS:
            return [f"each provenance entry must have exactly {sorted(_PROVENANCE_FIELDS)}"]
        if any(not isinstance(j[k], str) or not j[k] for k in ("route", "runner_image", "run_id")):
            return ["provenance route, runner_image and run_id must be nonempty strings"]
        if type(j["job_id"]) is not int or j["job_id"] < 0:
            return ["provenance job_id must be a non-negative int (\"9\" sorts after \"10\" as a string)"]
        if not isinstance(j["commit"], str) or not _COMMIT.fullmatch(j["commit"]):
            return ["provenance commit must be a full hex commit id"]
    if prov != sorted(prov, key=lambda j: (j["route"], j["runner_image"], j["job_id"])):
        return ["'provenance' is not sorted by route, then image, then job id"]
    if len({j["commit"] for j in prov}) != 1:
        # (I4 W1; 0007 v19 "the full commit id that wrote it") ONE CI run aggregates jobs of ONE commit, and that
        # commit is what v19's cross-run order compares: a record merging several has no defined "older".
        return ["every provenance entry must name the same commit: the record's commit"]
    return []


def record_commit(r) -> str | None:
    """The record's ONE commit (I4 W1), or None when the record is malformed."""
    if not isinstance(r, dict) or _provenance_problems(r.get("provenance")):
        return None
    return r["provenance"][0]["commit"]


def attestation_record_problems(r) -> list:
    """A record's own problems, TOTAL over any input. The field set is CLOSED, and each key field must already be in
    canonical form through the canonicaliser the running build uses (INV-SA12): `AMD64` is malformed, not
    `x86_64`."""
    if not isinstance(r, dict):
        return [f"attestation record is {type(r).__name__}, not a mapping"]
    if set(r) != _RECORD_FIELDS:
        return [f"fields {sorted(r)} are not exactly {sorted(_RECORD_FIELDS)}"]
    p = []
    for f in ("sqlite_version", "source_id"):
        if not isinstance(r[f], str) or not r[f]:
            p.append(f"{f!r} must be a nonempty string")
    if not isinstance(r["features"], dict) or set(r["features"]) != FEATURE_KEYS or any(
            type(v) is not bool for v in r["features"].values()):
        p.append(f"'features' must map exactly {sorted(FEATURE_KEYS)} to bools")
    if not isinstance(r["compile_options_digest"], str) or not _HEX64.fullmatch(r["compile_options_digest"]):
        p.append("'compile_options_digest' must be 64 lower-case hex")
    if type(r["machine"]) is not str or canonical_machine(r["machine"]) != r["machine"]:
        p.append(f"'machine' {r['machine']!r} is not in canonical form")
    if type(r["system"]) is not str or canonical_system(r["system"]) != r["system"]:
        p.append(f"'system' {r['system']!r} is not in canonical form")
    if type(r["libc"]) is not str or r["libc"] not in LIBC_TOKENS or (r["libc"] == "none") != (r["system"] != "Linux"):
        p.append(f"'libc' {r['libc']!r} is not canonical for system {r['system']!r}")
    for f in ("manifest_algorithm", "schema_version"):
        if type(r[f]) is not int:
            p.append(f"{f!r} must be an int")
    if not isinstance(r["result_digest"], str) or not _HEX64.fullmatch(r["result_digest"]):
        p.append("'result_digest' must be 64 lower-case hex")
    c = r["confinement"]
    if not isinstance(c, dict) or set(c) != CONFINEMENT_PROBE_KEYS or any(v is not True for v in c.values()):
        p.append(f"'confinement' must map exactly the {len(CONFINEMENT_PROBE_KEYS)} probes to True")
    p += _provenance_problems(r["provenance"])
    return p


def attestation_revision(r, revision=None) -> str:
    """`revision` (default: this module's own (manifest algorithm, schema version)) is passed EXPLICITLY by a caller
    whose module globals may be patched (the 0013 model's draft context patches `SCHEMA_VERSION`): attestation records
    are production package data, judged at production's revision.

    `malformed` (not a mapping, or either revision field not an EXACT int: `True`, `"2"` and `2.0` are garbage,
    never a high revision — round 5's `True == 1` class, which S74 closed), else `current` (manifest algorithm AND
    schema version equal this build's), `future` (either is higher: a format this build cannot read) or `superseded`.
    A malformed or current record is validated and can poison; only a current one can attest; superseded and future
    records contribute nothing (S74's scoping)."""
    if not isinstance(r, dict):
        return "malformed"
    a, v = r.get("manifest_algorithm"), r.get("schema_version")
    if type(a) is not int or type(v) is not int:
        return "malformed"
    mine = (MANIFEST_ALGORITHM, SCHEMA_VERSION) if revision is None else revision
    if a > mine[0] or v > mine[1]:
        return "future"
    return "current" if (a, v) == mine else "superseded"


def attestation_artifact_problems(records=None, revision=None) -> list:
    """Across the artifact (§4d, INV-SA6): any number of keys; a malformed CURRENT record poisons; one key with
    different EVIDENCE (result digest, confinement) conflicts; equal evidence is a duplicate. Provenance is never
    compared. Total."""
    try:
        records = attestations() if records is None else records
    except (OSError, ValueError) as exc:
        return [f"the runtime artifact cannot be read: {exc}"]
    if not isinstance(records, list):
        return [f"'attestations' is {type(records).__name__}, not a list"]
    problems, seen = [], {}
    for i, r in enumerate(records):
        rev = attestation_revision(r, revision)
        if rev == "malformed":
            bad = ([f"'{f}'" for f in ("manifest_algorithm", "schema_version") if type(r.get(f)) is not int]
                   if isinstance(r, dict) else [])
            problems.append(f"attestation {i}: " + (f"{' and '.join(bad)} must be an exact int" if bad
                                                    else f"is a {type(r).__name__}, not a record"))
            continue
        if rev != "current":
            continue
        try:
            own = attestation_record_problems(r)
        except Exception as exc:  # noqa: BLE001 - a validator escape poisons THAT record, never the build's status
            own = [f"its validation raised {type(exc).__name__}"]
        problems += [f"attestation {i}: {x}" for x in own]
        key = None if own else attestation_key(r)
        if key is None:
            continue
        evidence = (r["result_digest"], tuple(sorted(r["confinement"].items())))
        if key in seen:
            problems.append(f"attestation {i} repeats the key of attestation {seen[key][0]} "
                            + ("with equal evidence: a duplicate" if seen[key][1] == evidence
                               else "with different evidence: the key does not identify the build"))
        else:
            seen[key] = (i, evidence)
    return problems


def attested_key(key, records=None, revision=None) -> bool:
    """THE attested predicate (§4a): an UNPOISONED attestation artifact AND exactly one current record whose full
    key is `key`. `runtime_status()`'s `attested` and the 0013 model's `generated_on` resolution both decide through
    this one function (research's stage-1 read of I3(b), B5: a record in a poisoned artifact attests nothing, for
    either). Total: an unreadable artifact or a None key attests nothing."""
    if key is None:
        return False
    try:
        records = attestations() if records is None else records
    except (OSError, ValueError):
        return False
    if attestation_artifact_problems(records, revision):
        return False
    return sum(1 for r in records if attestation_revision(r, revision) == "current" and attestation_key(r) == key) == 1


# -- the status (§4a) ---------------------------------------------------------------------------------------------

class RuntimeStatus(NamedTuple):
    status: str                    # "attested" | "verified" | "refused"
    reason: Optional[str]          # refused: the first failing step; verified: a poisoned artifact, named; else None
    key: Optional[tuple]           # the full attestation key, or None when a field is unreadable
    unreadable: tuple              # the key fields that could not be read
    # the build as measured by the SAME read (research's stage 2, F2): the refusal text, the warning and INV-SA11's
    # audit value use these, never a second measurement — when that measurement is what failed, re-reading it would
    # raise out of the gate instead of refusing. None where the one read did not get that far.
    sqlite_version: Optional[str] = None
    source_id: Optional[str] = None
    platform: tuple = (None, None, None)      # (machine, system, libc), canonical; None = unreadable


def runtime_status() -> RuntimeStatus:
    """`attested`, `verified` or `refused`, decided by MEASUREMENT on every call (§4a). Verification (§4b) runs for
    every build, attested or not, on EVERY call: §4b allows a per-process cache, and none is kept, because measured
    at 2026-10-26 the three steps cost 0.074 s against 0.084 s for the reproduction the withdrawn predicate already
    ran on every open (one evidence read per verification), and a cache is state a patched measurement can leak
    through. A record only removes the warning: `attested` needs verification AND a current record whose full key
    equals this build's. **A poisoned artifact blocks ATTESTATION, never verification** (§4g.3 "a record can only
    remove the warning"; S74): the build is `verified`, the reason naming the first problem. Total and fail-closed:
    any exception is `refused`, naming it.

    A MEASUREMENT, not an enforcement point (0042): the refusing decisions are the gates that read it, the open gate
    (`store.open.runtime-unsupported`) and the release preflight's `unsupported-sqlite` intercept."""
    ident = {}
    try:
        ident = attestation_identity()
        unreadable = tuple(k for k in ("machine", "system", "libc") if ident[k] is None)
        key = attestation_key(ident)
        build = (ident["sqlite_version"], ident["source_id"], (ident["machine"], ident["system"], ident["libc"]))
        try:
            verify_build()
        except VerificationFailure as exc:
            return RuntimeStatus("refused", str(exc), key, unreadable, *build)
        poison = attestation_artifact_problems()
        if poison:
            return RuntimeStatus("verified", f"attestation artifact: {poison[0]}", key, unreadable, *build)
        if attested_key(key, attestations()):
            return RuntimeStatus("attested", None, key, unreadable, *build)
        return RuntimeStatus("verified", None, key, unreadable, *build)
    except Exception as exc:  # noqa: BLE001 - fail closed, naming the escape
        return RuntimeStatus("refused", f"verification raised {type(exc).__name__}", None, (),
                             ident.get("sqlite_version"), ident.get("source_id"))


def runtime_refused(st: RuntimeStatus) -> bool:
    """THE decision both production gates take on the measured status (0042: a declared predicate, so the release
    preflight's `unsupported-sqlite` is as census-visible as the open gate's; research's stage 2 on ce6117f). True
    refuses."""
    with _SITE_RUNTIME_REFUSED.consult():
        return _SITE_RUNTIME_REFUSED.fire(not isinstance(st, RuntimeStatus) or st.status == "refused", "refused")


def refusal_text(st: RuntimeStatus) -> str:
    """§4e's refusal: the first failure and only remedies that ship (INV-SA8). From the status's own read: never a
    second measurement, so a failing measurement refuses rather than raising out of the gate."""
    version = st.sqlite_version or "(version unreadable)"
    source = st.source_id or "source id unreadable"
    return (f"SQLite {version} ({source}) cannot be verified for Veracium's store: {st.reason}. "
            f"The store was not opened. Use a Python whose SQLite is an attested build (`veracium doctor` lists "
            f"them), or report this build to the project.")


_WARNED: list = []


def warn_unattested(st: RuntimeStatus) -> None:
    """§4e's warning for a `verified` open, exactly ONCE per process (INV-SA7), through `warnings` and the logger."""
    if st.status != "verified" or _WARNED:
        return
    _WARNED.append(True)
    machine, system, libc = st.platform
    text = (f"SQLite {st.sqlite_version} ({(st.source_id or '')[-12:]}, {machine}, {system}, "
            f"{libc}) is not one of Veracium's attested builds. Veracium verified this build when opening "
            f"the store: it reproduces all {len(SCHEMAS)} schema versions and tells apart all {_near_miss_count()} "
            f"near-miss checks. Its CI has not run the full schema suite on this build. `veracium doctor` lists the "
            f"attested builds.")
    warnings.warn(text, UnattestedBuildWarning, stacklevel=3)
    log.warning(text)


def _near_miss_count() -> int:
    from . import near_misses
    return len(near_misses.NEAR_MISSES)


class UnattestedBuildWarning(UserWarning):
    """A `verified` build: it passed the open-time checks, but CI has not run the full schema suite on it (§4e)."""


def _digest_of_identity(objs: dict, version: int, schemas=None) -> str:
    """Digest a recorded identity mapping without rebuilding the database. `schemas` (default: the module registry)
    names the declaration whose rebuildable keys are excluded, so a caller holding another registry (the 0013
    model's draft) never needs the module patched."""
    # This lazily imported `schema_model` from specs/ until 0013's first
    # review package build: in the repo, specs/ was always on sys.path (tests
    # and spec scripts put it there) so everything passed — while a wheel, or a
    # release-probe worktree with only PYTHONPATH=src, raised ModuleNotFoundError
    # that the fail-closed predicate swallowed into "unsupported-sqlite".
    # A total predicate must not be where packaging bugs go to hide.
    import hashlib as _h
    skip = (rebuildable_keys(version) if schemas is None
            else {o.key for o in schemas[version] if o.policy == REBUILDABLE})
    scoped = {k: v for k, v in objs.items() if tuple(k.split(":", 1)) not in skip}
    return _h.sha256(
        json.dumps(scoped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _built_objects(build) -> dict:
    """The identity of a scratch database `build(conn)` creates: the one in-memory builder behind the constructor
    reproduction and the near-misses (§4b steps 2 and 3)."""
    with contextlib.closing(sqlite3.connect(":memory:")) as c:
        build(c)
        return identity(manifest(c))


def _constructor_objects(version: int) -> dict:
    return _built_objects(lambda c: create(c, version))


def _constructor_digest(version: int) -> str:
    with contextlib.closing(sqlite3.connect(":memory:")) as c:
        create(c, version)
        return digest(manifest(c), version)


def legacy_base_versions() -> frozenset:
    """Versions whose release evidence shows a genuinely **unstamped** store.

    The only candidates version-zero resolution may try (round 5, finding 3)."""
    if not RELEASES.exists():
        # **Fails closed** (round 6, finding 7). v7 returned {SCHEMA_VERSION},
        # which silently authorised adoption using the very evidence that was
        # missing. No verified legacy artifact means no adoption candidates.
        return frozenset()
    return frozenset(
        r["store_schema_version"] for r in json.loads(RELEASES.read_text())["releases"]
        if r.get("on_disk_user_version") == 0 and r.get("store_schema_version"))


def version_records() -> dict:
    """The accepted-manifest records shipped with the package, `{version: {"accepted": [...]}}`.

    Read fresh on each open rather than cached at import: the artifact is
    package data, and a stale module-level cache would survive an upgrade in a
    long-lived process. Malformed or missing evidence returns `{}`, which makes
    every acceptance check fail closed."""
    try:
        data = json.loads(VERSIONS.read_text())
        if (not isinstance(data, dict)
                or data.get("manifest_algorithm") != MANIFEST_ALGORITHM
                or not isinstance(data.get("versions"), dict)):
            return {}
        return data["versions"]
    except (OSError, ValueError):
        return {}


def accepted_digests(version: int) -> set:
    """The closed set of manifest digests accepted at `version` (0007 §4a-v)."""
    rec = version_records().get(str(version))
    if not isinstance(rec, dict) or not isinstance(rec.get("accepted"), list):
        return set()
    return {a.get("digest") for a in rec["accepted"] if isinstance(a, dict)}


def accepted_provenance(objs: dict, version: int) -> str | None:
    """Which accepted record this store matches — for the adoption audit event."""
    d = digest(objs, version)
    rec = version_records().get(str(version), {})
    for a in rec.get("accepted", []) if isinstance(rec, dict) else []:
        if isinstance(a, dict) and a.get("digest") == d:
            return a.get("provenance")
    return None


# --------------------------------------------------------------------------
# the public contract (0007 §4b) and the open-time decision table (§4, §4c, §4e)

REASONS = frozenset({"invalid-version", "newer", "foreign-shape",
                     "stamped-shape-mismatch", "adoption-refused", "locked",
                     "unsupported-sqlite", "migration-required",
                     "unsupported-migration"})
"""The closed reason set. Hosts branch on these; free-form strings are the
failure mode `0008`'s round 3 was deferred over. The `migration-*` reasons are
`specs/0013`'s: `migration-required` is raised when ordinary opening meets a store
below the head version (migration is OFFLINE, §5b — the host runs `migrate_store`);
`unsupported-migration` when no migration path from the resolved base is defined."""

_AUDIT_STRING_CAP = 4096


class StoreVersionError(RuntimeError):
    """The store on disk is not something this build may open (0007 §4b).

    `reason` is drawn from `REASONS`; `diff`, populated for the shape reasons,
    names the minimum-distance accepted candidate and what differs, so a refusal
    a user cannot act on becomes a bug report instead."""

    def __init__(self, path: str, found, expected: int, reason: str,
                 diff: str | None = None):
        assert reason in REASONS, reason
        self.path, self.found, self.expected = path, found, expected
        self.reason, self.diff = reason, diff
        msg = (f"cannot open store {path!r}: {reason} "
               f"(found={found}, this build={expected})")
        if diff:
            msg += f"\n{diff}"
        super().__init__(msg)


class PackageConsistencyError(RuntimeError):
    """The build's own pieces disagree — the constructor with its shipped
    evidence, or a decision-table row whose delegated hook is absent. A
    property of a broken PACKAGE, never of the store on disk, which is why it
    deliberately escapes the closed-outcome boundaries built on this planner
    (0013 round 6 named the class so callers can preserve exactly this and
    nothing else)."""


class PostCommitAuditError(RuntimeError):
    """The store WAS adopted; the audit sink raised afterwards (0007 §4e).

    Deliberately not a `StoreVersionError`: a caller that retries sees a
    current store and correctly does not re-adopt. The connection is closed
    before this is raised, so no half-built store object survives."""

    committed = True

    def __init__(self, path: str, adoption_id: str, cause: BaseException):
        self.path, self.adoption_id = path, adoption_id
        super().__init__(
            f"store {path!r} was adopted (adoption {adoption_id}), but the "
            f"audit sink raised on the committed event: {cause!r}. Retry the "
            f"constructor to obtain a usable store.")
        self.__cause__ = cause


class AdoptionAuditEvent(NamedTuple):
    """The frozen audit payload (0007 §4e). `adoption_committed` repeats every
    field of its `attempted` partner except `event` and `occurred_at`, so a
    sink can process either in isolation. String fields are validated against
    a 4096-byte cap — **a limit, not a truncation**: a silently shortened path
    in an audit record is a falsified audit record. `path` is verbatim and may
    carry host-sensitive information; a sink that persists events is handling
    that, stated so the decision is the host's."""
    schema_version: int
    event: str                    # "adoption_attempted" | "adoption_committed"
    adoption_id: str
    path: str
    from_version: int             # 0 for an unstamped store
    to_version: int
    source_manifest_digest: str
    matched_provenance: str
    occurred_at: str              # RFC 3339, UTC


def _event(kind: str, adoption_id: str, path: str, from_v: int, to_v: int,
           source_digest: str, provenance: str) -> AdoptionAuditEvent:
    for name, value in (("path", path), ("matched_provenance", provenance),
                        ("source_manifest_digest", source_digest)):
        if len(str(value).encode("utf-8", "surrogateescape")) > _AUDIT_STRING_CAP:
            raise ValueError(f"audit field {name!r} exceeds "
                             f"{_AUDIT_STRING_CAP} bytes; refusing rather than "
                             f"truncating an audit record")
    return AdoptionAuditEvent(
        schema_version=1, event=kind, adoption_id=adoption_id, path=path,
        from_version=from_v, to_version=to_v,
        source_manifest_digest=source_digest, matched_provenance=provenance,
        occurred_at=datetime.now(timezone.utc).isoformat())


def _shape_diff(objs: dict, version: int) -> str:
    """The deterministic diagnostic (0007 §4b): distance = number of typed keys
    on which the manifests disagree; ties break by provenance in declaration
    order. Reports the chosen candidate and up to five differing keys."""
    rec = version_records().get(str(version), {})
    accepted = [a for a in rec.get("accepted", [])
                if isinstance(a, dict) and isinstance(a.get("objects"), dict)]
    if not accepted:
        return "no accepted manifests are recorded for this version"
    mine = identity(objs)
    best, best_keys = None, None
    for a in accepted:                       # declaration order — ties keep first
        theirs = a["objects"]
        keys = sorted(k for k in set(mine) | set(theirs)
                      if mine.get(k) != theirs.get(k))
        if best_keys is None or len(keys) < len(best_keys):
            best, best_keys = a, keys
    shown = ", ".join(best_keys[:5]) + ("…" if len(best_keys) > 5 else "")
    return (f"nearest accepted manifest: {best.get('provenance')!r}; "
            f"{len(best_keys)} object(s) differ: {shown}")


def _repair_drift(conn: sqlite3.Connection, version: int) -> None:
    """Drop and recreate drifted Veracium-owned acceleration indexes (§4a-iii).

    Correct whether the index is missing, present, or present-and-wrong —
    `CREATE INDEX IF NOT EXISTS` silently keeps a same-named index with a
    different definition (measured, round 2)."""
    declared = {o.key: o for o in SCHEMAS[version]}
    for key in drift(manifest(conn), version):
        conn.execute(f"DROP INDEX IF EXISTS {key[1]}")
        conn.execute(declared[key].ddl)


class OpenResult(str):
    """The branch that ran, PLUS the structured terminal facts a caller's
    audit needs and must not infer from the string (0013 round 8, finding 3:
    the audit wrapper derived `resulting_version` from the label and reported
    v1 for a store the operation left at v2). String-compares as the label —
    every existing `== "current"` caller is unaffected — while carrying:

      store_changed          did the objects on disk change this call
      transaction_committed  did a write transaction commit this call
      resulting_version      the store's user_version on return
    """
    __slots__ = ("store_changed", "transaction_committed", "resulting_version")

    def __new__(cls, label: str, *, store_changed: bool,
                transaction_committed: bool, resulting_version: int):
        r = str.__new__(cls, label)
        r.store_changed = store_changed
        r.transaction_committed = transaction_committed
        r.resulting_version = resulting_version
        return r


def _validated_current(conn: sqlite3.Connection, spath: str, found, *, require_stamp: bool = False) -> bool:
    """The *current* row's validation: accepted-set membership, typed
    rebuildable drift repair, complete revalidation (§4a-iii, S33). Returns
    whether it repaired drift — the caller reports it as `store_changed`.

    Shared by the current branch and the post-migration re-check, so a store a
    migration hook returns is held to exactly the standard a stamped-current
    store is held to — one validator, not two. `require_stamp` (0013 §4f, M117; passed only by the two
    post-migration calls): the end state also requires `user_version` to read SCHEMA_VERSION — an ordinary open
    already compares the stamp through the version path."""
    with _SITE_OPEN_UNACCEPTED_SHAPE.consult():
        if require_stamp:
            stamped = conn.execute("PRAGMA user_version").fetchone()[0]
            if stamped != SCHEMA_VERSION:
                raise _SITE_OPEN_UNACCEPTED_SHAPE.fire(StoreVersionError(spath, found, SCHEMA_VERSION,
                                        "stamped-shape-mismatch",
                                        diff=f"the migrated store's user_version reads {stamped}, not "
                                             f"{SCHEMA_VERSION} (0013 §4f, M117)"), "stamp")
        accepted = accepted_digests(SCHEMA_VERSION)
        objs = manifest(conn)
        if digest(objs, SCHEMA_VERSION) not in accepted:
            raise _SITE_OPEN_UNACCEPTED_SHAPE.fire(StoreVersionError(spath, found, SCHEMA_VERSION,
                                    "stamped-shape-mismatch",
                                    diff=_shape_diff(objs, SCHEMA_VERSION)), "stamped")
        if drift(objs, SCHEMA_VERSION):
            _repair_drift(conn, SCHEMA_VERSION)
            after = manifest(conn)      # S33: complete revalidation
            if (digest(after, SCHEMA_VERSION) not in accepted
                    or drift(after, SCHEMA_VERSION)):
                raise _SITE_OPEN_UNACCEPTED_SHAPE.fire(StoreVersionError(spath, found, SCHEMA_VERSION,
                                        "stamped-shape-mismatch",
                                        diff=_shape_diff(after, SCHEMA_VERSION)), "drifted")
            return True
        return False


def open_versioned(conn: sqlite3.Connection, path: str, *,
                   allow_adopt: bool = True, audit_sink=None,
                   older=None, new=None, on_committed=None,
                   on_rolled_back=None) -> OpenResult:
    """The 0007 §4 decision table, executed under the write lock (§4c).

    **`on_committed`** is an infallible caller-owned sink invoked with the
    `OpenResult` the instant a branch commits, BEFORE any post-commit cleanup
    (0013 round 11, finding 2: the function-level `finally` restoring
    `conn.isolation_level` runs on the return path and CAN raise, discarding
    the return so the caller never sees the committed facts and its audit
    reported v1 for a v2 store). A caller that records migration facts uses
    this so a cleanup failure cannot erase a proven commit; ordinary opens
    pass nothing.

    **`on_rolled_back`** is the symmetric infallible sink for the FAILURE path
    (0013 round 12, finding 1: the failure handler discarded the `ROLLBACK`
    result with a bare `except: pass`, so a caller could not tell a confirmed
    rollback from a rollback that itself failed and left the store partially
    migrated — and the audit then asserted the source version for a store that
    was never restored). It is called with `"rolled-back"` when the `ROLLBACK`
    executed and `"rollback-failed"` when it raised. A caller that never sees
    the sink (a failure before the transaction, or the sink not passed) must
    treat the post-failure store state as UNKNOWN, never as the source.

    `BEGIN IMMEDIATE` is taken BEFORE the version and manifest reads — a
    deferred transaction acquires the write lock at the first write, which is
    after the decision has already been made. The manifest is computed on THIS
    connection, never by reopening the path: `":memory:"` reopened by path is a
    different, empty database (measured, round 2).

    Returns the branch that ran — `"current"`, `"created"`, `"adopted"`, or
    `"migrated"` — so callers can log or audit without re-deriving it.

    **`older` is §4's older-row seam, delegated to `specs/0013`.** The row —
    a stamped `0 < found < SCHEMA_VERSION` store, or an unstamped store whose
    evidenced base is below current — is `0013`'s migration contract, and this
    hook is where its dedicated offline operation plugs in so there is exactly
    ONE planner (round 3 of `0013`'s review: the instrument's hand-written
    second state machine omitted the new, legacy and foreign rows entirely).
    The hook runs inside the open transaction as `older(conn, path, found,
    objs, base, runtime=status)`, `status` being the gate's ONE measurement
    (0013 INV-SA11's audit identity, passed on and never re-read), and must either raise or bring the store to the current
    version; the store it returns is then revalidated by the same `current`
    validator and committed here. With no hook the row refuses exactly as
    before: both sites are unreachable while `SCHEMA_VERSION == 1`, and
    `validate_schema_registry()` keeps the declared range contiguous.

    **`new` is the creation seam** (`0013` round 6): a dedicated *migration*
    operation must never CREATE a store — an authority attests an existing
    source, and a vanished or empty file is a missing source, not a blank
    slate. When set, the hook is called as `new(conn, path, found, objs)`
    in place of creation and must raise; `None` (the default, and ordinary
    opening) keeps §4's new-row creation exactly as before."""
    spath = str(path)
    # os.fsencode, not str.encode: a valid POSIX filename with non-UTF-8
    # bytes arrives as a surrogate-escaped str, which plain UTF-8 encoding
    # rejects (0013 round 6, measured).
    if len(os.fsencode(spath)) > _AUDIT_STRING_CAP:
        raise ValueError(f"store path exceeds {_AUDIT_STRING_CAP} bytes")

    # The runtime gate runs before ANY version or shape decision (§4a-viii; 0007 §4g.6 4a, INV-SA1): the build's
    # status is MEASURED here, once, and nothing later in the open branches on it (0013 §5f.3 carrier (ii)).
    with _SITE_OPEN_RUNTIME_UNSUPPORTED.consult():
        status = runtime_status()
        if runtime_refused(status):
            raise _SITE_OPEN_RUNTIME_UNSUPPORTED.fire(StoreVersionError(
                spath, found=None, expected=SCHEMA_VERSION,
                reason="unsupported-sqlite", diff=refusal_text(status)))
    warn_unattested(status)

    prev_isolation = conn.isolation_level
    conn.isolation_level = None              # explicit transaction control
    committed_event = None
    try:
        with _SITE_OPEN_LOCKED.consult():
            try:
                conn.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError as exc:
                raise _SITE_OPEN_LOCKED.fire(StoreVersionError(
                    spath, found=None, expected=SCHEMA_VERSION, reason="locked",
                    diff="another connection holds the write lock; refused loudly "
                         "rather than hanging (busy_timeout elapsed)")) from exc

        with _SITE_OPEN_LEGACY.consult():
            try:
                found = conn.execute("PRAGMA user_version").fetchone()[0]
                objs = manifest(conn)
                accepted = accepted_digests(SCHEMA_VERSION)

                with _SITE_OPEN_INVALID_VERSION.consult():
                    if found < 0:
                        raise _SITE_OPEN_INVALID_VERSION.fire(StoreVersionError(spath, found, SCHEMA_VERSION,
                                                "invalid-version"))
                with _SITE_OPEN_NEWER.consult():
                    if found > SCHEMA_VERSION:
                        raise _SITE_OPEN_NEWER.fire(StoreVersionError(
                            spath, found, SCHEMA_VERSION, "newer",
                            diff="this build cannot know what it does not know; "
                                 "install a build whose SCHEMA_VERSION covers the store"))

                if found == SCHEMA_VERSION:
                    repaired = _validated_current(conn, spath, found)
                    # Build and validate the result BEFORE COMMIT (round 9): after
                    # COMMIT only `return` runs, so a post-commit internal defect
                    # that hides a committed store is impossible.
                    result = OpenResult("current", store_changed=repaired,
                                        transaction_committed=repaired,
                                        resulting_version=SCHEMA_VERSION)
                    conn.execute("COMMIT")
                    if on_committed is not None:
                        on_committed(result)      # facts reach the caller before
                    return result                 # any post-commit cleanup

                if 0 < found < SCHEMA_VERSION:
                    # §4's *older* row: a stamped store this build predates on.
                    # Migrating it forward is specs/0013's contract; without its
                    # hook the row is a package-consistency impossibility —
                    # unreachable while SCHEMA_VERSION == 1 — not a store property.
                    if older is None:
                        raise PackageConsistencyError(
                            f"store {spath!r} is stamped v{found} and this build "
                            f"is v{SCHEMA_VERSION} with no migration hook "
                            f"installed; migrating forward is specs/0013's "
                            f"contract")
                    older(conn, spath, found, objs, found, runtime=status)
                    _validated_current(conn, spath, found, require_stamp=True)
                    result = OpenResult("migrated", store_changed=True,
                                        transaction_committed=True,
                                        resulting_version=SCHEMA_VERSION)
                    conn.execute("COMMIT")
                    if on_committed is not None:
                        on_committed(result)
                    return result

                # found == 0 — unstamped
                if not objs:                        # §4 "new": no non-internal object
                    if new is not None:
                        new(conn, spath, found, objs)
                        raise PackageConsistencyError(
                            "the new-row hook returned instead of raising")
                    create(conn, SCHEMA_VERSION)
                    after = manifest(conn)
                    if (digest(after, SCHEMA_VERSION) not in accepted
                            or drift(after, SCHEMA_VERSION)):
                        # Not a property of the store on disk: the constructor and
                        # the shipped evidence disagree, i.e. the package is broken.
                        raise PackageConsistencyError(
                            "constructor output is not in the accepted manifest "
                            "set — the package's evidence artifacts disagree with "
                            "its schema registry")
                    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
                    result = OpenResult("created", store_changed=True,
                                        transaction_committed=True,
                                        resulting_version=SCHEMA_VERSION)
                    conn.execute("COMMIT")
                    if on_committed is not None:
                        on_committed(result)
                    return result

                # §4 "legacy" / "foreign": resolve against the evidenced bases only
                base = resolve(objs, version_records(),
                               candidates=legacy_base_versions())
                if base is None:
                    raise _SITE_OPEN_LEGACY.fire(StoreVersionError(
                        spath, found, SCHEMA_VERSION, "foreign-shape",
                        diff=_shape_diff(objs, SCHEMA_VERSION)), "foreign-shape")
                if base != SCHEMA_VERSION:
                    # An unstamped store whose evidenced base is BELOW current:
                    # 0013's migration path, reached through the same older-row
                    # seam. Without the hook, refuse exactly as before — this
                    # cannot arise while SCHEMA_VERSION == 1, because no legacy
                    # base below 1 exists.
                    if older is None:
                        raise _SITE_OPEN_LEGACY.fire(StoreVersionError(
                            spath, found, SCHEMA_VERSION, "migration-required",
                            diff=f"store resolves to base version {base}, below the "
                                 f"head version {SCHEMA_VERSION}; migration is OFFLINE "
                                 f"(specs/0013 §5b) — quiesce access and run "
                                 f"veracium.store.migration.migrate_store(path)"), "migration-required")
                    older(conn, spath, found, objs, base, runtime=status)
                    _validated_current(conn, spath, found, require_stamp=True)
                    result = OpenResult("migrated", store_changed=True,
                                        transaction_committed=True,
                                        resulting_version=SCHEMA_VERSION)
                    conn.execute("COMMIT")
                    if on_committed is not None:
                        on_committed(result)
                    return result
                if not allow_adopt:
                    raise _SITE_OPEN_LEGACY.fire(StoreVersionError(
                        spath, found, SCHEMA_VERSION, "adoption-refused",
                        diff="allow_adopt=False: this host refuses unstamped "
                             "stores rather than adopting them"), "adoption-refused")

                adoption_id = str(uuid.uuid4())
                _repair_drift(conn, SCHEMA_VERSION)
                after = manifest(conn)
                if (digest(after, SCHEMA_VERSION) not in accepted
                        or drift(after, SCHEMA_VERSION)):
                    raise _SITE_OPEN_LEGACY.fire(StoreVersionError(
                        spath, found, SCHEMA_VERSION, "foreign-shape",
                        diff=_shape_diff(after, SCHEMA_VERSION)), "foreign-shape-after")
                provenance = accepted_provenance(after, SCHEMA_VERSION) or ""
                source_digest = digest(after, SCHEMA_VERSION)
                conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

                attempted = _event("adoption_attempted", adoption_id, spath,
                                   0, SCHEMA_VERSION, source_digest, provenance)
                if audit_sink is not None:
                    # Inside the transaction: a sink that raises aborts the
                    # adoption, so an unrecorded adoption cannot exist (§4e).
                    audit_sink(attempted)
                else:
                    log.info("adopting unstamped store %s as schema v%s (%s); no "
                             "audit sink configured, so no durability is claimed",
                             spath, SCHEMA_VERSION, adoption_id)
                conn.execute("COMMIT")
                committed_event = attempted._replace(
                    event="adoption_committed",
                    occurred_at=datetime.now(timezone.utc).isoformat())
            except BaseException:
                # Round 12, finding 1: publish the rollback RESULT, do not discard
                # it. A caller that records terminal facts must not claim the store
                # was restored to its source unless the rollback is CONFIRMED.
                status = "rollback-failed"
                try:
                    conn.execute("ROLLBACK")
                    status = "rolled-back"
                except sqlite3.Error:
                    status = "rollback-failed"
                if on_rolled_back is not None:
                    on_rolled_back(status)
                raise
    finally:
        conn.isolation_level = prev_isolation

    if committed_event is not None and audit_sink is not None:
        try:
            audit_sink(committed_event)
        except BaseException as exc:
            conn.close()                      # §4e: closed before raising
            raise PostCommitAuditError(spath, committed_event.adoption_id,
                                       exc) from exc
    return OpenResult("adopted", store_changed=True,
                      transaction_committed=True,
                      resulting_version=SCHEMA_VERSION)

