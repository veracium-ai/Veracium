"""On-disk store schema versioning — the `specs/0007` kernel, in production.

**This module is the implementation `0007`'s acceptance authorises**, and it is
the shared kernel fourteen external review rounds demanded: the schema registry,
manifest/digest/drift/candidate matching, runtime-evidence validation, and the
open-time decision table. `specs/schema_model.py` and `specs/schema_evidence.py`
now import from HERE — the evidence generator uses the same declarations the
store executes, which closes the divergence rounds 6 and 8 prohibited.

The evidence artifacts ship as package data in `evidence/`:

    sqlite_runtimes.json   the qualified runtime build identities
    schema_versions.json   the accepted manifests per schema version
    legacy_stores.json     release probing evidence; source of the legacy bases

**Missing or malformed evidence fails closed**: `runtime_supported()` returns
False and the store refuses with `unsupported-sqlite` before any version or
shape decision.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import pathlib
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import NamedTuple

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

SCHEMAS = {1: SCHEMA_V1, 2: SCHEMA_V2, 3: SCHEMA_V3, 4: SCHEMA_V4, 5: SCHEMA_V5,
           6: SCHEMA_V6, 7: SCHEMA_V7, 8: SCHEMA_V8}

SCHEMA_VERSION = 8
"""**Declared, not inferred.**

v6 used `max(SCHEMAS)`, so adding or removing a registry entry silently changed
which version received mutable treatment in the generated artifact (round 5,
finding 5). Bumped 1→2 for `specs/0008`'s `confirmations` table, installed by the
`specs/0013` v1→v2 offline migration."""


def rebuildable_keys(version: int = SCHEMA_VERSION) -> set:
    return {o.key for o in SCHEMAS[version] if o.policy == REBUILDABLE}


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
    c = sqlite3.connect(":memory:")
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
    c.close()
    return out


def runtime_identity() -> dict:
    return {"sqlite_version": sqlite3.sqlite_version,
            "source_id": sqlite3.connect(":memory:").execute(
                "SELECT sqlite_source_id()").fetchone()[0],
            "features": _feature_probes()}


_RUNTIME_OVERRIDE: list = []


_RUNTIME_OVERRIDE: list = []
"""While `write_runtime()` validates a prospective artifact it has not
published, it parks the candidate records here so every validator sees the
future state through the one canonical accessor below."""


def qualified_runtimes() -> list:
    """Recorded runtimes — or the prospective set during a qualification."""
    if _RUNTIME_OVERRIDE:
        return _RUNTIME_OVERRIDE[0]
    return json.loads(RUNTIMES.read_text())["runtimes"] if RUNTIMES.exists() else []


def active_records(records=None) -> list:
    """Records that are current-algorithm and internally valid. Total over
    any list content (0013 round 7: a non-mapping member raised
    AttributeError out of a validator that promises problems, not
    exceptions)."""
    records = qualified_runtimes() if records is None else records
    if not isinstance(records, list):          # round 10: total over any input
        return []
    return [r for r in records
            if isinstance(r, dict)
            and r.get("manifest_algorithm") == MANIFEST_ALGORITHM
            and not runtime_record_problems(r)]


def artifact_problems(records=None) -> list:
    """Problems visible only across the whole runtime artifact.

    **Round 9, finding 1b: two individually valid records with the SAME runtime
    identity and DIFFERENT constructor output both passed.** Measured. One
    SQLite build cannot legitimately produce two different constructor outputs,
    so the artifact is self-contradictory — and a per-record validator cannot
    see it, because each record is internally consistent.

    Duplicate identity is rejected outright rather than resolved: picking one
    would be guessing which record is the forgery."""
    records = qualified_runtimes() if records is None else records
    if not isinstance(records, list):
        return [f"runtime artifact is {type(records).__name__}, not a list"]
    problems, seen = [], {}

    def _current(r):
        """Round 13, finding 3: every production check is scoped to
        current-algorithm records. Superseded ones contribute nothing and
        cannot disqualify; `--check` reports them for repository cleanup."""
        return isinstance(r, dict) and r.get("manifest_algorithm") == MANIFEST_ALGORITHM

    for r in records:
        if not isinstance(r, dict):
            problems.append(f"runtime artifact contains a {type(r).__name__}, "
                            f"not a record")
    records = [r for r in records if isinstance(r, dict)]
    # **Round 10, finding 2: `0007` supports exactly ONE active runtime.**
    # v12 described a cross-runtime union and could not construct it: on runtime
    # A only A contributes, on B only B, and nothing persists an attestation
    # that A was reproduced by its own job. `write_runtime()` then refused a
    # second differing runtime outright, because it required every valid
    # prospective manifestation to be in an accepted set that excluded it.
    # **A half-built union is worse than an honest single-runtime contract**, so
    # the union claim is withdrawn and S-Q7 owns widening it with durable
    # per-runtime attestation.
    # **Round 12, finding 3: a malformed CURRENT-algorithm record must poison
    # the artifact, not be skipped.** A record at an older algorithm is
    # superseded and ignored; a current-algorithm record that fails validation
    # is evidence of tampering or generator breakage, and the safe reading of
    # such an artifact is "unqualified".
    for r in records:
        if not _current(r):
            continue
        for p in runtime_record_problems(r):
            problems.append(f"current-algorithm record for "
                            f"{r.get('sqlite_version')!r}: {p}")
    identities = {build_identity(r) for r in active_records(records)}
    if len(identities) > 1:
        problems.append(
            f"{len(identities)} active runtime build identities recorded "
            f"({sorted(i[0] for i in identities)}); `0007` supports exactly one. "
            f"Durable cross-runtime attestation is S-Q7.")
    # Two current-algorithm records agreeing on version+source_id but differing
    # on probes are one build described inconsistently -- one build cannot have
    # two probe results under the same probe definitions.
    by_build = {}
    for r in records:
        if not _current(r):
            continue
        if not _keyable_runtime(r):
            continue                       # already reported; cannot be keyed
        by_build.setdefault((r.get("sqlite_version"), r.get("source_id")),
                            set()).add(build_identity(r))
    for build, keys in sorted(by_build.items()):
        if len(keys) > 1:
            problems.append(
                f"runtime {build[0]!r} has {len(keys)} current-algorithm records "
                f"that disagree on probes — one build cannot have two")
    # Scoped to current-algorithm records (round 13, finding 3): a stale
    # duplicate is a cleanup item for --check, not a startup failure.
    for r in records:
        if not _current(r):
            continue
        if not _keyable_runtime(r):
            continue                       # already reported; cannot be keyed
        key = _identity_key(r)
        if key in seen:
            if seen[key] != r.get("constructor_digests"):
                problems.append(
                    f"two runtime records share identity {key[0]!r}/{key[1][:20]!r} "
                    f"but declare different constructor output — the artifact is "
                    f"self-contradictory and neither can be trusted")
            else:
                problems.append(f"duplicate runtime record for {key[0]!r}")
        seen[key] = r.get("constructor_digests")
    return problems


def manifestation_problems(objs: dict, version: int) -> list:
    """A recorded manifestation must be EXACTLY the declared object set.

    Round 9, finding 1a: a self-consistent fabrication was accepted — hashing
    proves internal consistency, not provenance, so a manifestation may contain
    only objects this build declares.

    **Round 12, finding 2: "no extras" was only half of "exact".** A record with
    a *missing* object — including a missing required table — passed the
    validator once its digest was updated to match, and only the production
    predicate's separate full-comparison recovered safety. The key set must
    equal the declaration, and every entry must have the closed field shape."""
    declared = {f"{o.kind}:{o.name}" for o in SCHEMAS[version]}
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
            declared = {o.key: o for o in SCHEMAS.get(version, ())}
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


def _structure_problems(r) -> list:
    """Type errors in a record, found before any field is USED.

    **Round 13, finding 2: the validator was not total.** `features = []` raised
    `AttributeError`, `constructor_digests = 1` raised `TypeError` — measured —
    so a malformed record beside a valid one made `runtime_supported()` escape
    with an implementation exception instead of returning False, and the caller
    never saw the closed `unsupported-sqlite` outcome.

    And the evidence-revision fields were untyped: `manifest_algorithm = 13.0`
    with `schema_version = True` passed and qualified, the same Python-equality
    class (`True == 1`, `13.0 == 13`) that round 12 fixed for features.
    **`type(v) is int`, never `isinstance`** — bool is an int subclass."""
    if not isinstance(r, dict):
        return [f"runtime record is {type(r).__name__}, not a mapping"]
    problems = []
    for field in ("sqlite_version", "source_id"):
        v = r.get(field)
        if not isinstance(v, str) or not v:
            problems.append(f"{field!r} must be a nonempty string")
    for field in ("manifest_algorithm", "schema_version"):
        if type(r.get(field)) is not int:
            problems.append(f"{field!r} must be an int, is "
                            f"{type(r.get(field)).__name__}")
    if not isinstance(r.get("features"), dict):
        problems.append(f"'features' must be a mapping, is "
                        f"{type(r.get('features')).__name__}")
    if not isinstance(r.get("constructor_digests"), dict) or not all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in (r.get("constructor_digests") or {}).items()
            if isinstance(r.get("constructor_digests"), dict)):
        problems.append("'constructor_digests' must map str to str")
    m = r.get("manifestations")
    if not isinstance(m, dict) or not all(
            isinstance(k, str) and isinstance(v, dict) for k, v in (m or {}).items()
            if isinstance(m, dict)):
        problems.append("'manifestations' must map str to mappings")
    return problems


def runtime_record_problems(r) -> list:
    """Whether a recorded runtime is complete enough to qualify anything.

    **Total**: returns problems for any input, never raises (round 13). The
    empty-mapping vacuity (round 6), exact key sets (rounds 9/11/12) and typed
    features (round 12) all live behind the structural gate."""
    problems = _structure_problems(r)
    if problems:
        return problems
    if r["manifest_algorithm"] != MANIFEST_ALGORITHM:
        problems.append(f"runtime record uses manifest algorithm "
                        f"{r['manifest_algorithm']}, build uses {MANIFEST_ALGORITHM}")
    if r["schema_version"] != SCHEMA_VERSION:
        problems.append(f"runtime record is for schema version {r['schema_version']}, "
                        f"build declares {SCHEMA_VERSION}")
    want = {str(v) for v in SCHEMAS}
    if set(r["constructor_digests"]) != want:
        problems.append(f"runtime record covers versions "
                        f"{sorted(r['constructor_digests'])}, build declares "
                        f"{sorted(want)}")
    if not r["constructor_digests"]:
        problems.append("runtime record has no constructor digests")
    if set(r["features"]) != FEATURE_KEYS:
        problems.append(f"feature keys {sorted(r['features'])} are not exactly "
                        f"{sorted(FEATURE_KEYS)}")
    for k, v in r["features"].items():
        if type(v) is not bool:
            problems.append(f"feature {k!r} is {type(v).__name__}, not bool")
    for name in ("preserves_ddl_body", "xinfo_exposes_generated"):
        if r["features"].get(name) is not True:
            problems.append(f"runtime fails a required behaviour: {name}")
    want_prov = {f"constructor v{v}" for v in SCHEMAS}
    if set(r["manifestations"]) != want_prov:
        problems.append(f"runtime manifestations {sorted(r['manifestations'])} "
                        f"are not exactly {sorted(want_prov)}")
    else:
        for v in SCHEMAS:
            objs = r["manifestations"][f"constructor v{v}"]
            recorded = r["constructor_digests"].get(str(v))
            if _digest_of_identity(objs, v) != recorded:
                problems.append(f"manifestation 'constructor v{v}' does not hash "
                                f"to its recorded digest — the object records and "
                                f"the digest disagree")
            problems.extend(manifestation_problems(objs, v))
    return problems


FEATURE_KEYS = frozenset({"generated_columns", "strict_tables",
                          "preserves_ddl_body", "xinfo_exposes_generated"})
"""The closed feature vocabulary. Every probe result is a real bool -- round 12
measured `strict_tables: 1` passing dict equality because Python's `1 == True`,
while the canonical JSON identity correctly distinguished them, so the
production predicate and the declared identity disagreed."""


def build_identity(r: dict) -> tuple:
    """**RuntimeBuildIdentity: which SQLite build this is.**

    Round 12, finding 1: v14 declared one canonical five-field key and then used
    `(version, source_id)` for replacement anyway — so a record with the same
    version and source id but *different feature results* was silently replaced,
    though the spec itself says a source id does not identify compile options.
    The reviewer's split is adopted: **build identity** (version, source id,
    canonical typed features) is what one-active enforcement, matching,
    replacement, attestation and reporting key on; **evidence revision**
    (manifest algorithm, schema version) is merely which revision of the record
    format described it."""
    return (r.get("sqlite_version"), r.get("source_id"),
            json.dumps(r.get("features"), sort_keys=True))


def _identity_key(r: dict) -> tuple:
    """Build identity plus the evidence revision — for exact-duplicate checks."""
    return build_identity(r) + (r.get("manifest_algorithm"), r.get("schema_version"))


def _keyable_runtime(r) -> bool:
    """Whether a record's identity fields can be hashed — round 4's totality
    rule (mirrored from 0013's `_keyable_path_record`): type-check before set
    membership or dict keying. A record failing this is ALREADY reported by
    `runtime_record_problems`; it must not ALSO crash the by-build and
    duplicate checks by placing a dict/list — e.g. a measured
    `schema_version={}` — into a `set`/`dict` key. Kept strictly narrower than
    full validity, so hashable-but-invalid records still get duplicate-checked
    exactly as before."""
    return (isinstance(r, dict)
            and isinstance(r.get("sqlite_version"), str)
            and isinstance(r.get("source_id"), str)
            and type(r.get("manifest_algorithm")) is int
            and type(r.get("schema_version")) is int)


def active_records(records=None) -> list:
    """Records that are current-algorithm and internally valid. Total over
    any list content (0013 round 7: a non-mapping member raised
    AttributeError out of a validator that promises problems, not
    exceptions)."""
    records = qualified_runtimes() if records is None else records
    if not isinstance(records, list):          # round 10: total over any input
        return []
    return [r for r in records
            if isinstance(r, dict)
            and r.get("manifest_algorithm") == MANIFEST_ALGORITHM
            and not runtime_record_problems(r)]


def artifact_problems(records=None) -> list:
    """Problems visible only across the whole runtime artifact.

    **Round 9, finding 1b: two individually valid records with the SAME runtime
    identity and DIFFERENT constructor output both passed.** Measured. One
    SQLite build cannot legitimately produce two different constructor outputs,
    so the artifact is self-contradictory — and a per-record validator cannot
    see it, because each record is internally consistent.

    Duplicate identity is rejected outright rather than resolved: picking one
    would be guessing which record is the forgery."""
    records = qualified_runtimes() if records is None else records
    if not isinstance(records, list):
        return [f"runtime artifact is {type(records).__name__}, not a list"]
    problems, seen = [], {}

    def _current(r):
        """Round 13, finding 3: every production check is scoped to
        current-algorithm records. Superseded ones contribute nothing and
        cannot disqualify; `--check` reports them for repository cleanup."""
        return isinstance(r, dict) and r.get("manifest_algorithm") == MANIFEST_ALGORITHM

    for r in records:
        if not isinstance(r, dict):
            problems.append(f"runtime artifact contains a {type(r).__name__}, "
                            f"not a record")
    records = [r for r in records if isinstance(r, dict)]
    # **Round 10, finding 2: `0007` supports exactly ONE active runtime.**
    # v12 described a cross-runtime union and could not construct it: on runtime
    # A only A contributes, on B only B, and nothing persists an attestation
    # that A was reproduced by its own job. `write_runtime()` then refused a
    # second differing runtime outright, because it required every valid
    # prospective manifestation to be in an accepted set that excluded it.
    # **A half-built union is worse than an honest single-runtime contract**, so
    # the union claim is withdrawn and S-Q7 owns widening it with durable
    # per-runtime attestation.
    # **Round 12, finding 3: a malformed CURRENT-algorithm record must poison
    # the artifact, not be skipped.** A record at an older algorithm is
    # superseded and ignored; a current-algorithm record that fails validation
    # is evidence of tampering or generator breakage, and the safe reading of
    # such an artifact is "unqualified".
    for r in records:
        if not _current(r):
            continue
        for p in runtime_record_problems(r):
            problems.append(f"current-algorithm record for "
                            f"{r.get('sqlite_version')!r}: {p}")
    identities = {build_identity(r) for r in active_records(records)}
    if len(identities) > 1:
        problems.append(
            f"{len(identities)} active runtime build identities recorded "
            f"({sorted(i[0] for i in identities)}); `0007` supports exactly one. "
            f"Durable cross-runtime attestation is S-Q7.")
    # Two current-algorithm records agreeing on version+source_id but differing
    # on probes are one build described inconsistently -- one build cannot have
    # two probe results under the same probe definitions.
    by_build = {}
    for r in records:
        if not _current(r):
            continue
        if not _keyable_runtime(r):
            continue                       # already reported; cannot be keyed
        by_build.setdefault((r.get("sqlite_version"), r.get("source_id")),
                            set()).add(build_identity(r))
    for build, keys in sorted(by_build.items()):
        if len(keys) > 1:
            problems.append(
                f"runtime {build[0]!r} has {len(keys)} current-algorithm records "
                f"that disagree on probes — one build cannot have two")
    # Scoped to current-algorithm records (round 13, finding 3): a stale
    # duplicate is a cleanup item for --check, not a startup failure.
    for r in records:
        if not _current(r):
            continue
        if not _keyable_runtime(r):
            continue                       # already reported; cannot be keyed
        key = _identity_key(r)
        if key in seen:
            if seen[key] != r.get("constructor_digests"):
                problems.append(
                    f"two runtime records share identity {key[0]!r}/{key[1][:20]!r} "
                    f"but declare different constructor output — the artifact is "
                    f"self-contradictory and neither can be trusted")
            else:
                problems.append(f"duplicate runtime record for {key[0]!r}")
        seen[key] = r.get("constructor_digests")
    return problems


def manifestation_problems(objs: dict, version: int) -> list:
    """A recorded manifestation must be EXACTLY the declared object set.

    Round 9, finding 1a: a self-consistent fabrication was accepted — hashing
    proves internal consistency, not provenance, so a manifestation may contain
    only objects this build declares.

    **Round 12, finding 2: "no extras" was only half of "exact".** A record with
    a *missing* object — including a missing required table — passed the
    validator once its digest was updated to match, and only the production
    predicate's separate full-comparison recovered safety. The key set must
    equal the declaration, and every entry must have the closed field shape."""
    declared = {f"{o.kind}:{o.name}" for o in SCHEMAS[version]}
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
            declared = {o.key: o for o in SCHEMAS.get(version, ())}
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


def runtime_supported() -> bool:
    """**Derived from the evidence artifact, never from a hand-edited tuple.**

    Qualification means: a *complete* recorded runtime whose identity matches
    this process, and whose recorded **complete constructor manifestations**
    reproduce here.

    **Round 11, finding 2: comparing digests was not enough.** The acceptance
    digest deliberately excludes rebuildable indexes, so a record claiming
    `CREATE UNIQUE INDEX ix_edges_subj_rel ON edges(user_id)` reproduced its
    digest exactly while describing an index that changes which writes succeed.
    Measured: the generator caught it, this predicate did not — the same
    wrong-place class round 10's finding 1 was about."""
    # **Total, fail-closed** (round 13, finding 2). Malformed JSON, a missing
    # `runtimes` member, wrong containers, or any validator escape must yield
    # False — the caller's closed outcome is `unsupported-sqlite`, never an
    # implementation exception escaping into the open path. The release check
    # is where diagnostics belong; this predicate only answers the question.
    try:
        records = qualified_runtimes()
        # Round 10, finding 1: the production-facing predicate must see
        # artifact-level conflicts, not only the generator.
        if artifact_problems(records):
            return False
        me = runtime_identity()
        for r in records:
            # Superseded records contribute nothing and cannot disqualify
            # (round 13, finding 3); malformed CURRENT records already poisoned
            # the artifact above.
            if not isinstance(r, dict) or runtime_record_problems(r):
                continue
            # Canonical build identity, never raw dict equality: `1 == True` in
            # Python, so a mistyped probe made the two disagree (round 12).
            if build_identity(r) != build_identity({**me,
                    "manifest_algorithm": MANIFEST_ALGORITHM,
                    "schema_version": SCHEMA_VERSION}):
                continue
            if any(_constructor_digest(int(v)) != d
                   for v, d in r["constructor_digests"].items()):
                return False
            # The complete manifestation, including rebuildable objects.
            return all(r["manifestations"].get(f"constructor v{v}")
                       == _constructor_objects(v) for v in SCHEMAS)
        return False
    except Exception:
        return False


def _digest_of_identity(objs: dict, version: int) -> str:
    """Digest a recorded identity mapping without rebuilding the database."""
    # This lazily imported `schema_model` from specs/ until 0013's first
    # review package build: in the repo, specs/ was always on sys.path (tests
    # and spec scripts put it there) so everything passed — while a wheel, or a
    # release-probe worktree with only PYTHONPATH=src, raised ModuleNotFoundError
    # that the fail-closed predicate swallowed into "unsupported-sqlite".
    # A total predicate must not be where packaging bugs go to hide.
    import hashlib as _h
    skip = rebuildable_keys(version)
    scoped = {k: v for k, v in objs.items() if tuple(k.split(":", 1)) not in skip}
    return _h.sha256(
        json.dumps(scoped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _constructor_objects(version: int) -> dict:
    c = sqlite3.connect(":memory:")
    create(c, version)
    o = identity(manifest(c))
    c.close()
    return o


def _constructor_digest(version: int) -> str:
    c = sqlite3.connect(":memory:")
    create(c, version)
    d = digest(manifest(c), version)
    c.close()
    return d


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


def _validated_current(conn: sqlite3.Connection, spath: str, found) -> bool:
    """The *current* row's validation: accepted-set membership, typed
    rebuildable drift repair, complete revalidation (§4a-iii, S33). Returns
    whether it repaired drift — the caller reports it as `store_changed`.

    Shared by the current branch and the post-migration re-check, so a store a
    migration hook returns is held to exactly the standard a stamped-current
    store is held to — one validator, not two."""
    accepted = accepted_digests(SCHEMA_VERSION)
    objs = manifest(conn)
    if digest(objs, SCHEMA_VERSION) not in accepted:
        raise StoreVersionError(spath, found, SCHEMA_VERSION,
                                "stamped-shape-mismatch",
                                diff=_shape_diff(objs, SCHEMA_VERSION))
    if drift(objs, SCHEMA_VERSION):
        _repair_drift(conn, SCHEMA_VERSION)
        after = manifest(conn)      # S33: complete revalidation
        if (digest(after, SCHEMA_VERSION) not in accepted
                or drift(after, SCHEMA_VERSION)):
            raise StoreVersionError(spath, found, SCHEMA_VERSION,
                                    "stamped-shape-mismatch",
                                    diff=_shape_diff(after, SCHEMA_VERSION))
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
    objs, base)` and must either raise or bring the store to the current
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

    # The runtime gate runs before ANY version or shape decision (§4a-viii).
    if not runtime_supported():
        raise StoreVersionError(
            spath, found=None, expected=SCHEMA_VERSION,
            reason="unsupported-sqlite",
            diff=f"sqlite {sqlite3.sqlite_version} is not a qualified runtime "
                 f"build identity; regenerate the evidence there "
                 f"(schema_evidence.py --runtime --write)")

    prev_isolation = conn.isolation_level
    conn.isolation_level = None              # explicit transaction control
    committed_event = None
    try:
        try:
            conn.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as exc:
            raise StoreVersionError(
                spath, found=None, expected=SCHEMA_VERSION, reason="locked",
                diff="another connection holds the write lock; refused loudly "
                     "rather than hanging (busy_timeout elapsed)") from exc

        try:
            found = conn.execute("PRAGMA user_version").fetchone()[0]
            objs = manifest(conn)
            accepted = accepted_digests(SCHEMA_VERSION)

            if found < 0:
                raise StoreVersionError(spath, found, SCHEMA_VERSION,
                                        "invalid-version")
            if found > SCHEMA_VERSION:
                raise StoreVersionError(
                    spath, found, SCHEMA_VERSION, "newer",
                    diff="this build cannot know what it does not know; "
                         "install a build whose SCHEMA_VERSION covers the store")

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
                older(conn, spath, found, objs, found)
                _validated_current(conn, spath, found)
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
                raise StoreVersionError(
                    spath, found, SCHEMA_VERSION, "foreign-shape",
                    diff=_shape_diff(objs, SCHEMA_VERSION))
            if base != SCHEMA_VERSION:
                # An unstamped store whose evidenced base is BELOW current:
                # 0013's migration path, reached through the same older-row
                # seam. Without the hook, refuse exactly as before — this
                # cannot arise while SCHEMA_VERSION == 1, because no legacy
                # base below 1 exists.
                if older is None:
                    raise StoreVersionError(
                        spath, found, SCHEMA_VERSION, "migration-required",
                        diff=f"store resolves to base version {base}, below the "
                             f"head version {SCHEMA_VERSION}; migration is OFFLINE "
                             f"(specs/0013 §5b) — quiesce access and run "
                             f"veracium.store.migration.migrate_store(path)")
                older(conn, spath, found, objs, base)
                _validated_current(conn, spath, found)
                result = OpenResult("migrated", store_changed=True,
                                    transaction_committed=True,
                                    resulting_version=SCHEMA_VERSION)
                conn.execute("COMMIT")
                if on_committed is not None:
                    on_committed(result)
                return result
            if not allow_adopt:
                raise StoreVersionError(
                    spath, found, SCHEMA_VERSION, "adoption-refused",
                    diff="allow_adopt=False: this host refuses unstamped "
                         "stores rather than adopting them")

            adoption_id = str(uuid.uuid4())
            _repair_drift(conn, SCHEMA_VERSION)
            after = manifest(conn)
            if (digest(after, SCHEMA_VERSION) not in accepted
                    or drift(after, SCHEMA_VERSION)):
                raise StoreVersionError(
                    spath, found, SCHEMA_VERSION, "foreign-shape",
                    diff=_shape_diff(after, SCHEMA_VERSION))
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

