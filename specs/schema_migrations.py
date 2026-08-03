#!/usr/bin/env python3
"""Declarative migrations, executed only by the planner.

**The callback model is withdrawn.** v5 gave a migration a proxy whose
connection was name-mangled and claimed transaction control was "unreachable...
enforced by construction". Round 5 recovered it in one line:

    def migration(executor):
        conn = executor._MigrationExecutor__conn
        conn.set_authorizer(None)
        conn.commit()

Measured: raw connection recovered, outer transaction gone. **Name mangling is
not access control**, and an arbitrary in-process Python callback cannot be
sandboxed behind a private attribute. The claim was false, and a false
containment claim is worse than an admitted trusted one.

So a migration does not receive anything connection-bearing. **It declares a
closed sequence of statements, and the planner executes them.** The authorizer
remains, but its role is now honestly stated: it is defence against *accidental*
transaction control in a declared statement, not a sandbox around hostile code.

Round 5's finding 7 is settled the same way — **the single-step model**:

    exactly one migration from version n to version n+1,
    generated and tested against EVERY accepted manifest of version n.

No route selection, no cycles, no non-adjacent steps, no duplicate edges,
because none of those can be expressed.
"""
from __future__ import annotations

import sqlite3
from typing import NamedTuple

from schema_model import SCHEMA_VERSION, SCHEMAS


class Migration(NamedTuple):
    """One step, n -> n+1, as data.

    `statements` is a closed tuple of SQL executed in order by the planner. No
    Python callback, no connection, no cursor — there is nothing to escape
    from."""
    from_version: int
    to_version: int
    statements: tuple


MIGRATIONS: dict = {}
"""from_version -> Migration. **Empty today**, which is the point: the mechanism
lands with zero migrations so its first real use in `0006` is not also its first
execution. The test suite exercises path generation against a simulated version
2, so "empty" never means "untested"."""

_DENIED = (sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_SAVEPOINT,
           sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH,
           # Round 6, finding 2: `PRAGMA writable_schema=ON` was accepted, left
           # the persistent manifest unchanged, and stayed set on the live
           # connection afterwards. Measured. No migration needs a pragma; the
           # planner owns `user_version`.
           sqlite3.SQLITE_PRAGMA)


def _authorizer(action, _a1, _a2, db_name, _trigger):
    """Deny transaction control, pragmas, and anything outside `main`.

    Round 6, finding 2, measured: a declared

        CREATE TEMP TRIGGER sabotage AFTER INSERT ON t BEGIN DELETE FROM t; END

    was accepted, left the persistent manifest **byte-identical**, and then
    silently deleted every inserted row. **Post-migration manifest validation
    cannot see it**, because a temp object is not in `sqlite_master`. Confining
    writes to `main` is what makes "validate the persistent shape afterwards" a
    complete check rather than a partial one."""
    if action in _DENIED:
        return sqlite3.SQLITE_DENY
    if db_name not in (None, "main"):
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def apply_migration(conn: sqlite3.Connection, mig: Migration) -> None:
    """Execute a declared step inside the caller's open transaction.

    The authorizer catches a declared statement that would end the transaction —
    `END`, `RELEASE` and friends, which a keyword blacklist missed (round 3,
    measured) — and now also pragmas and non-`main` writes (round 6).
    **It is restored in `finally`**: left installed it would break the planner's
    own commit; left off after a failure it would drop containment for whatever
    ran next.

    **`sqlite_temp_master` is asserted empty afterwards.** The authorizer is the
    guard; this is the check that the guard held, because an effect the
    persistent manifest cannot see is exactly what round 6 exploited."""
    conn.set_authorizer(_authorizer)
    try:
        for stmt in mig.statements:
            conn.execute(stmt)
    finally:
        conn.set_authorizer(None)
    leaked = [r[0] for r in conn.execute("SELECT name FROM sqlite_temp_master")]
    if leaked:
        raise RuntimeError(
            f"migration {mig.from_version}->{mig.to_version} left temporary "
            f"objects {leaked}; connection-local effects are invisible to the "
            f"persistent manifest and are not permitted")


def destination_problems(objs: dict, to_version: int) -> list:
    """Whether a migrated database satisfies the destination's **independent**
    requirement — not merely "whatever the migration produced".

    **Round 6, finding 1, and it is the most serious thing in v7.** The
    generator ran every migration and added the result to the destination's
    accepted set, with no independent destination contract. Measured: an *empty*
    migration from 1 to 2 produced a database with no `sources` table, and that
    output was accepted as a valid version 2 — **the migration defined its own
    broken output as correct.** That defeats the meaning of "understood store".

    So the accepted set records the *exact observed output* (which may
    legitimately differ in DDL text between constructor and `ALTER` paths), and
    this function enforces the *required capability* independently:

      * every `REQUIRED` object of the destination exists, with matching DDL;
      * every `REBUILDABLE` object exists or is repairable drift;
      * no unapproved persistent object is present."""
    from schema_model import REBUILDABLE, REQUIRED, SCHEMAS
    problems = []
    declared = {o.key: o for o in SCHEMAS[to_version]}
    for key, o in declared.items():
        got = objs.get(key)
        if got is None:
            problems.append(f"destination v{to_version} requires {key[0]} "
                            f"{key[1]!r}, which the migration did not create")
        elif o.policy == REQUIRED and got.get("sql") != o.ddl:
            problems.append(f"{key[0]} {key[1]!r} does not match the destination "
                            f"declaration")
    for key in objs:
        if key not in declared:
            problems.append(f"unapproved persistent object {key[0]} {key[1]!r}")
    return problems


def validate_registry() -> list:
    """Structural problems in the migration registry. Empty = well-formed.

    Under the single-step model most malformed shapes are unrepresentable; what
    remains checkable is adjacency, uniqueness of the outgoing edge, that every
    version below the current one has a route forward, and — round 6, finding 6
    — that **`SCHEMA_VERSION` agrees with the registry it claims to describe.**
    v7 made `SCHEMA_VERSION` explicit but never bound it: declaring `SCHEMAS[2]`
    while leaving `SCHEMA_VERSION = 1` passed validation and emitted an artifact
    containing a version the build did not claim to be."""
    from schema_model import SCHEMA_VERSION as _CURRENT
    problems = []
    if SCHEMAS and max(SCHEMAS) != _CURRENT:
        problems.append(f"SCHEMA_VERSION is {_CURRENT} but the registry declares "
                        f"up to {max(SCHEMAS)}; a schema above the current version "
                        f"must not exist")
    expected = set(range(1, _CURRENT + 1))
    if set(SCHEMAS) != expected:
        problems.append(f"registry versions {sorted(SCHEMAS)} are not the contiguous "
                        f"range {sorted(expected)}")
    for frm, mig in sorted(MIGRATIONS.items()):
        if mig.from_version >= _CURRENT:
            problems.append(f"migration {mig.from_version}->{mig.to_version} "
                            f"originates at or beyond the current version")
    for frm, mig in sorted(MIGRATIONS.items()):
        if mig.from_version != frm:
            problems.append(f"registry key {frm} disagrees with {mig.from_version}")
        if mig.to_version != mig.from_version + 1:
            problems.append(f"migration {mig.from_version}->{mig.to_version} is not "
                            f"adjacent; the single-step model has no multi-hop edge")
        if mig.from_version not in SCHEMAS or mig.to_version not in SCHEMAS:
            problems.append(f"migration {mig.from_version}->{mig.to_version} names a "
                            f"version with no registry entry")
    for v in sorted(SCHEMAS):
        if v < SCHEMA_VERSION and v not in MIGRATIONS:
            problems.append(f"version {v} has no route forward; an accepted source "
                            f"manifest with no path to the current version can never "
                            f"be opened")
    return problems


def chain(from_version: int, to_version: int) -> list:
    """The unique step sequence between two versions."""
    out, v = [], from_version
    while v < to_version:
        mig = MIGRATIONS.get(v)
        if mig is None:
            raise KeyError(f"no migration from version {v}")
        out.append(mig)
        v = mig.to_version
    return out
