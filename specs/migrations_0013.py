#!/usr/bin/env python3
"""The 0013 measuring instrument: the concrete v1→v2 confirmations migration.

**Draft-status instrument, not production.** `0013` is `draft`; only `accepted`
authorises implementation, so nothing here is imported by the store. It exists
because the round-9 M-Q1 ruling requires `0013` to be reviewed **together with
a real migration** — `0008`'s `confirmations` table — and a migration you
cannot run is not reviewable.

What it carries:

  * the eight review-tested conclusions from `0007` rounds 1–7, as code again
    (the v10 scope cut deleted `schema_migrations.py`; `0013` §4 kept the
    conclusions in prose, and this restores the executable form **against a
    real migration** rather than an empty registry);
  * `SCHEMA_V2` and `MIGRATION_1_TO_2` — the concrete proposal, derived
    field-by-field from `0008` §6b–§6d;
  * `open_or_migrate()` — the §4c protocol extended with the *older* row, which
    is the piece `0007` v10 cut and this spec restores;
  * `simulate()` — end-to-end demonstration on a populated store.

Run:  PYTHONPATH=src python3 specs/migrations_0013.py --simulate
"""
from __future__ import annotations

import pathlib
import sqlite3
import sys
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from veracium.store.schema_version import (  # noqa: E402
    REBUILDABLE, REQUIRED, SCHEMA_V1, SchemaObject, create, digest, drift,
    identity, manifest)

# --------------------------------------------------------------------------
# the concrete schema change, derived from 0008 §6b–§6d

CONFIRMATIONS_DDL = """CREATE TABLE confirmations (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, edge_id TEXT NOT NULL,
    confirmed_at TEXT NOT NULL, actor TEXT NOT NULL, call_path TEXT NOT NULL,
    correlation_id TEXT, request_digest TEXT NOT NULL,
    UNIQUE(user_id, correlation_id)
)"""
# Field-by-field from 0008 §6c: `confirmed_at` is the NORMALISED instant, never
# the caller's string; `actor` and `call_path` are closed-enum values;
# `correlation_id` is nullable — omitted means no replay protection, and SQLite
# UNIQUE treats NULLs as distinct, so unprotected confirmations coexist while a
# reused (user_id, correlation_id) pair conflicts, tenant-scoped exactly as
# §6c's "not global" ruling requires; `request_digest` is the canonical-request
# digest replay compares against, so a same-id different-payload replay is an
# integrity conflict, not a lookup miss.

IX_CONFIRMATIONS_DDL = ("CREATE INDEX ix_confirmations_edge "
                        "ON confirmations(user_id, edge_id)")
# 0008 §6d: "indexed on edge_id" for confirmations_for(user_id, edge_id).
# Non-unique acceleration ⇒ REBUILDABLE under 0007 §4a-iii; the UNIQUE
# constraint above lives in the table DDL and is therefore in the digest.

SCHEMA_V2 = SCHEMA_V1 + (
    SchemaObject("table", "confirmations", CONFIRMATIONS_DDL, REQUIRED),
    SchemaObject("index", "ix_confirmations_edge", IX_CONFIRMATIONS_DDL,
                 REBUILDABLE),
)


class Migration(NamedTuple):
    """One declared step, n → n+1. Statements only — the callback model was
    withdrawn in 0007 round 5 (name mangling is not access control) and stays
    withdrawn."""
    from_version: int
    to_version: int
    statements: tuple


MIGRATION_1_TO_2 = Migration(1, 2, (CONFIRMATIONS_DDL, IX_CONFIRMATIONS_DDL))
# **The whole migration is two CREATE statements**, and that is a measured
# property worth the review's attention: because the change is purely additive,
# the migration's stored DDL is byte-identical to the constructor's, so
# MANIFESTS[2] has ONE digest with TWO provenances. The accepted-SET model
# (0007 §4a-v) is still exercised — both paths are generated and compared —
# but the ALTER-class divergence 0007 measured does not occur here.

SCHEMAS_DRAFT = {1: SCHEMA_V1, 2: SCHEMA_V2}
MIGRATIONS_DRAFT = {1: MIGRATION_1_TO_2}


# --------------------------------------------------------------------------
# the review-tested execution rules (0007 rounds 3, 5–7; 0013 §4a–§4d)

_DENIED = (sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_SAVEPOINT,
           sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_PRAGMA)


def _authorizer(action, _a1, _a2, db_name, _trigger):
    """Deny transaction control, pragmas, and anything outside `main`.

    `END`, `END TRANSACTION` and `RELEASE` all commit and a keyword blacklist
    missed all three; a TEMP trigger passed shape validation while silently
    deleting rows. Both measured in 0007's rounds. Defence against an
    *accidental declared statement* — migration statements are trusted code."""
    if action in _DENIED:
        return sqlite3.SQLITE_DENY
    if db_name not in (None, "main"):
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def apply_migration(conn: sqlite3.Connection, mig: Migration) -> None:
    """Execute a declared step inside the caller's open transaction.

    Authorizer installed around the statements and restored in `finally`;
    `sqlite_temp_master` asserted empty afterwards — an effect the persistent
    manifest cannot see is exactly what round 6 exploited."""
    conn.set_authorizer(_authorizer)
    try:
        for stmt in mig.statements:
            conn.execute(stmt)
    finally:
        conn.set_authorizer(None)
    leaked = [r[0] for r in conn.execute("SELECT name FROM sqlite_temp_master")]
    if leaked:
        raise RuntimeError(f"migration left temporary objects {leaked}")


def destination_problems(objs: dict, to_version: int,
                         schemas=None) -> list:
    """Structural capability, not DDL text (0007 round 7): a migration may not
    define its own destination (round 6), and byte-comparing DDL rejects a
    correct ALTER. Every REQUIRED object present with matching structure, every
    REBUILDABLE present-or-drift, nothing unapproved."""
    schemas = SCHEMAS_DRAFT if schemas is None else schemas
    declared = {o.key: o for o in schemas[to_version]}
    ref = sqlite3.connect(":memory:")
    for o in schemas[to_version]:
        ref.execute(o.ddl)
    want = identity(manifest(ref))
    ref.close()
    have = identity(objs) if not isinstance(next(iter(objs.values()), {}), dict) \
        else {f"{k[0]}:{k[1]}": v for k, v in objs.items()}
    problems = []
    for key, o in declared.items():
        skey = f"{key[0]}:{key[1]}"
        got = have.get(skey)
        if got is None:
            if o.policy == REBUILDABLE:
                continue
            problems.append(f"v{to_version} requires {skey}, absent")
        elif key[0] == "table":
            if got.get("columns") != want[skey].get("columns"):
                problems.append(f"{skey} columns differ from the declaration")
        elif got.get("sql") != o.ddl:
            problems.append(f"{skey} differs from its declaration")
    for skey in have:
        if tuple(skey.split(":", 1)) not in declared:
            problems.append(f"unapproved persistent object {skey}")
    return problems


def validate_registry(schemas=None, migrations=None, current=2) -> list:
    """Single-step model: adjacency, bound SCHEMA_VERSION, every version below
    current reachable. Cycles and duplicate routes are unrepresentable."""
    schemas = SCHEMAS_DRAFT if schemas is None else schemas
    migrations = MIGRATIONS_DRAFT if migrations is None else migrations
    problems = []
    if max(schemas) != current:
        problems.append(f"current {current} != max declared {max(schemas)}")
    if set(schemas) != set(range(1, current + 1)):
        problems.append(f"versions {sorted(schemas)} not contiguous 1..{current}")
    for frm, mig in sorted(migrations.items()):
        if (mig.from_version, mig.to_version) != (frm, frm + 1):
            problems.append(f"step {frm}: not adjacent")
    for v in range(1, current):
        if v not in migrations:
            problems.append(f"version {v} has no route forward")
    return problems


# --------------------------------------------------------------------------
# the open path with the *older* row restored (0013's addition to 0007 §4)

def open_or_migrate(path: str, busy_timeout_ms: int = 5000) -> str:
    """The §4c protocol with migration: the answer to M-Q2 is that **SQLite's
    write lock is the single-process enforcement.**

    `BEGIN IMMEDIATE` before any read serialises openers. The winner reads
    `user_version`, migrates, validates the destination, stamps, commits — one
    transaction. A concurrent opener blocks on the lock (up to `busy_timeout`),
    then acquires it, RE-reads under its own lock, and finds the store already
    migrated — so it opens as current. No lock table (that would change the
    shape being migrated), no advisory file (not a guarantee). **The caveat is
    the contract**: a migration must fit in one transaction, which the additive
    v2 does, and which the single-step model makes reviewable per step."""
    conn = sqlite3.connect(path, timeout=busy_timeout_ms / 1000)
    conn.isolation_level = None
    try:
        conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
        try:
            conn.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError:
            return "locked"
        found = conn.execute("PRAGMA user_version").fetchone()[0]
        if found == 2:
            conn.execute("COMMIT")
            return "current"
        if found == 1:
            apply_migration(conn, MIGRATION_1_TO_2)
            problems = destination_problems(manifest(conn), 2)
            if problems:
                conn.execute("ROLLBACK")
                return f"migration-result-mismatch: {problems[0]}"
            conn.execute("PRAGMA user_version = 2")
            conn.execute("COMMIT")
            return "migrated"
        conn.execute("ROLLBACK")
        return f"unexpected version {found}"
    finally:
        conn.close()


def simulate() -> int:
    """End to end, on a populated store: v1 → migrate → v2, data intact,
    constructor and migration outputs compared, 0008's uniqueness demonstrated."""
    import tempfile
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    for o in SCHEMA_V1:
        c.execute(o.ddl)
    for i in range(4):
        c.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,"
                  "quarantined,json) VALUES(?,?,?,?,?,1,0,'{}')",
                  (f"e{i}", "u", f"s{i}", "r", "o"))
    c.execute("PRAGMA user_version = 1")
    c.commit()
    c.close()

    print(f"open_or_migrate: {open_or_migrate(p)}")
    print(f"reopen:          {open_or_migrate(p)}")

    c = sqlite3.connect(p)
    rows = c.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    print(f"edges preserved: {rows}/4")

    cons = sqlite3.connect(":memory:")
    for o in SCHEMA_V2:
        cons.execute(o.ddl)
    same = identity(manifest(c)) == identity(manifest(cons))
    print(f"migration output byte-identical to constructor: {same}")

    # 0008 §6c uniqueness semantics, demonstrated in the migrated schema
    c.execute("INSERT INTO confirmations VALUES('c1','u','e0','t','user',"
              "'host_api',NULL,'d1')")
    c.execute("INSERT INTO confirmations VALUES('c2','u','e1','t','user',"
              "'host_api',NULL,'d2')")          # second NULL correlation: fine
    try:
        c.execute("INSERT INTO confirmations VALUES('c3','u','e0','t','user',"
                  "'host_api','corr-1','d3')")
        c.execute("INSERT INTO confirmations VALUES('c4','u','e2','t','user',"
                  "'host_api','corr-1','d4')")
        dup = "ACCEPTED (wrong)"
    except sqlite3.IntegrityError:
        dup = "rejected (correct)"
    print(f"NULL correlations coexist; duplicate (user, correlation): {dup}")
    return 0 if same and rows == 4 else 1


if __name__ == "__main__":
    if "--simulate" in sys.argv:
        raise SystemExit(simulate())
    print(__doc__)
