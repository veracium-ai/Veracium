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
           sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH)


def _authorizer(action, *_rest):
    return sqlite3.SQLITE_DENY if action in _DENIED else sqlite3.SQLITE_OK


def apply_migration(conn: sqlite3.Connection, mig: Migration) -> None:
    """Execute a declared step inside the caller's open transaction.

    The authorizer catches a declared statement that would end the transaction —
    `END`, `RELEASE` and friends, which a keyword blacklist missed (round 3,
    measured). **It is restored in `finally`**: left installed it would break the
    planner's own commit; left off after a failure it would drop containment for
    whatever ran next."""
    conn.set_authorizer(_authorizer)
    try:
        for stmt in mig.statements:
            conn.execute(stmt)
    finally:
        conn.set_authorizer(None)


def validate_registry() -> list:
    """Structural problems in the migration registry. Empty = well-formed.

    Under the single-step model most malformed shapes are unrepresentable; what
    remains checkable is adjacency, uniqueness of the outgoing edge, and that
    every version below the current one has a route forward."""
    problems = []
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
