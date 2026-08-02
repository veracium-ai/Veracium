#!/usr/bin/env python3
"""The schema kernel: what a store's shape *is*, and which version it matches.

**This module is deliberately small, and that is round 5's answer to a question
I asked.** `specs/schema_manifest.py` had grown four responsibilities — the
manifest kernel, migration containment, git-based evidence generation, and its
own adversarial test harness — and every round found a new path by which the
measuring instrument overstated its result. The instrument is not what ships,
but the spec leans on it as the evidence for adoption safety, so its defects
are not free.

The split is:

    schema_model.py       <- this: identity, digest, drift, candidate matching
    schema_migrations.py  declarative migrations, executed only by the planner
    schema_evidence.py    tag probing and the generated artifacts
    tests/test_schema_model.py   every adversarial counterexample, in pytest

**Only this kernel is shared between production and evidence generation.** Git
probing and result presentation are not part of the trust boundary. And the
counterexamples are now pytest tests rather than a hand-rolled harness — which
is what killed the last reporting defect: the harness printed 30 rows and
reported `28/28`, because its total was a hand-maintained arithmetic expression.
A tool whose purpose is truthful evidence cannot count its own checks by hand.

The acceptance model itself (round 2, unchanged since):

    A store is understood when its persistent schema is EXACTLY what one of
    this build's known constructors or migrations produces.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
GENERATED = ROOT / "specs" / "generated"

# Only SQLite's own objects are excluded, and only these. `sqlite_stat1` appears
# after ANALYZE; `sqlite_autoindex_*` are implicit indexes with no stored DDL.
# GLOB, not LIKE: backslash is not a LIKE escape without an explicit ESCAPE
# clause, so `LIKE 'sqlite\_%'` excluded nothing (0007 §4a-i, measured).
_OBJECTS = ("SELECT type, name, tbl_name, sql FROM sqlite_master "
            "WHERE name NOT GLOB 'sqlite_*' ORDER BY type, name")

REBUILDABLE = "rebuildable"
REQUIRED = "required"


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

SCHEMAS = {1: SCHEMA_V1}

SCHEMA_VERSION = 1
"""**Declared, not inferred.**

v6 used `max(SCHEMAS)`, so adding or removing a registry entry silently changed
which version received mutable treatment in the generated artifact (round 5,
finding 5)."""

POLICY_ARTIFACT = GENERATED / "schema_policy.json"
"""The independently reviewed record of each object's policy.

**v6's policy check was tautological** — it compared the registry's rebuildable
set against a set computed from the same registry, so flipping
`ix_edges_subj_rel` from REBUILDABLE to REQUIRED left conformance empty (round
5, finding 2, measured). A policy decides whether an object is excluded from the
acceptance digest, whether drift is repaired or refused, and how candidate
matching behaves; it cannot be self-certifying.

The honest end state is that the product schema is *generated* from this
registry, at which point there is no second declaration to compare. Until then
this artifact is the second declaration, and changing it is a reviewable diff."""


def rebuildable_keys(version: int = SCHEMA_VERSION) -> set:
    return {o.key for o in SCHEMAS[version] if o.policy == REBUILDABLE}


def create(conn: sqlite3.Connection, version: int = SCHEMA_VERSION) -> None:
    """Build a database from the registry, statement by statement.

    Never `executescript`: it issues an implicit COMMIT, so it cannot run inside
    the open transaction 0007 §4c requires (measured, and independently
    confirmed by the reviewer)."""
    for o in SCHEMAS[version]:
        conn.execute(o.ddl)


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


def declared_policies(version: int = SCHEMA_VERSION) -> dict:
    return {f"{o.kind}:{o.name}": o.policy for o in SCHEMAS[version]}


def reviewed_policies(version: int = SCHEMA_VERSION) -> dict | None:
    if not POLICY_ARTIFACT.exists():
        return None
    return json.loads(POLICY_ARTIFACT.read_text()).get(str(version))


def registry_conformance(store_factory, version: int = SCHEMA_VERSION) -> list:
    """Differences between the registry and the product schema. Empty = conformant.

    Compares **complete typed records including rebuildable objects** — the
    acceptance digest excludes those, so it cannot serve as a conformance check
    (round 4) — **and the policies, against the independently reviewed
    artifact** rather than against the registry itself (round 5).

    `store_factory(path)` builds a store with the product's own schema."""
    import tempfile
    probe = tempfile.mktemp(suffix=".db")
    store_factory(probe)
    pconn, rconn = sqlite3.connect(probe), sqlite3.connect(":memory:")
    create(rconn, version)
    prod, reg = identity(manifest(pconn)), identity(manifest(rconn))
    problems = [f"{k}: registry {reg.get(k)!r} != product {prod.get(k)!r}"
                for k in sorted(set(prod) | set(reg)) if prod.get(k) != reg.get(k)]
    if drift(manifest(rconn), version):
        problems.append(f"registry drifts against itself: {drift(manifest(rconn), version)}")
    reviewed = reviewed_policies(version)
    if reviewed is None:
        problems.append(f"{POLICY_ARTIFACT.name} has no record for version {version}")
    elif reviewed != declared_policies(version):
        for k in sorted(set(reviewed) | set(declared_policies(version))):
            if reviewed.get(k) != declared_policies(version).get(k):
                problems.append(f"policy {k}: registry says "
                                f"{declared_policies(version).get(k)!r}, reviewed "
                                f"artifact says {reviewed.get(k)!r}")
    pconn.close()
    rconn.close()
    return problems
