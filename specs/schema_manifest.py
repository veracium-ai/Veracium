#!/usr/bin/env python3
"""The canonical schema manifest of a SQLite store, and the durable historical
evidence for adopting one.

**This module answers S-Q4, and the answer came from round 2 of external
review.** `specs/0007` v2 compared names and declared types; v3 replaced that
with a richer "semantic signature". Both were the same mistake in different
sizes: **trying to decide whether an arbitrary third-party schema is
*equivalent* to ours.** That is an open-ended SQL-equivalence problem, and the
proof it was open-ended is that each round produced fresh counterexamples that
passed -- v3's signature accepted a `CHECK` constraint that rejects legitimate
writes, a `COLLATE NOCASE` primary key, an extra `VIEW`, and an index using a
host-defined collation that makes ordinary inserts fail with `no such collation
sequence` once the collation is gone. **All four measured.**

The bound is not a longer list of things to compare. It is a different question:

    A store is understood when its persistent schema is EXACTLY what one of
    this build's known schema constructors or migrations produces.

So this module does not model SQL semantics at all. It inventories **every**
non-internal persistent object -- tables, views, indexes, triggers -- canonicalises
each, and digests the set. A store matches a version or it does not.

**The cost, stated because it is real:** a third-party database that is
genuinely equivalent but differently written is refused. That is an
*availability* failure -- loud, and fixable by an explicit import tool. The
alternative is silent misinterpretation of persisted trust data, which is the
worst failure mode this project has.

  `--selfcheck`   build every counterexample and report what the manifest sees.
                  Needs no git, so it runs inside an extracted review archive.
  `--releases`    build a store with **every released tag's own code**; with
                  `--write`, record the durable artifact
                  `specs/generated/legacy_stores.json` -- tag, commit sha,
                  sqlite version, digest. A prose count over mutable tag names
                  is not evidence (round 2, finding 9).
  `--check`       verify that artifact still matches, for CI. **Needs a git
                  checkout** -- it rebuilds a store from every released tag, so
                  it exits 2 with an explicit message inside an extracted
                  review archive rather than reporting every tag as missing.
  `--digest <db>` print one file's manifest and digest.

Nothing here is an implementation of 0007. It is the measuring instrument the
spec is written against, and it runs today, against real files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARTIFACT = ROOT / "specs" / "generated" / "legacy_stores.json"
MANIFEST_ARTIFACT = ROOT / "specs" / "generated" / "schema_versions.json"

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

    **This registry is the structured constructor round 3 asked for, and it
    resolves S-Q5.** v4 kept a bare tuple of three index *names* and excluded
    them from the digest by name alone. That is what made round 3's finding 3
    possible: SQLite allows a trigger and an index to share a name, the
    name-keyed dict let the trigger overwrite the index entry, and the digest
    then skipped the key because the *name* was on the exclusion list -- so a
    store carrying an arbitrary trigger digested **identical to a clean store**.
    Measured.

    Declaring `kind` alongside `name` makes the exclusion typed, and every
    consumer -- creation, expectation, repair, drift, docs -- reads this one
    registry instead of restating the list."""
    kind: str          # "table" | "index" | "view" | "trigger"
    name: str
    ddl: str
    policy: str        # REQUIRED (in the digest) | REBUILDABLE (repaired, not digested)

    @property
    def key(self) -> tuple:
        return (self.kind, self.name)


# The v1 schema, declared structurally. **`ddl` is byte-identical to what
# SQLite stores in `sqlite_master.sql`**, which is not the same as what
# `_SCHEMA` says: SQLite strips `IF NOT EXISTS` and preserves everything else
# exactly, whitespace included. `--selfcheck` proves this registry reproduces
# `_SCHEMA`'s database rather than trusting that it does.
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


def rebuildable_keys(version: int = 1) -> set:
    """Typed identities, never bare names (round 3, finding 3)."""
    return {o.key for o in SCHEMAS[version] if o.policy == REBUILDABLE}


def create(conn: sqlite3.Connection, version: int = 1) -> None:
    """Build a database from the registry, statement by statement.

    Never `executescript`: it issues an implicit COMMIT, so it cannot run inside
    the open transaction 0007 §4c requires (measured, and independently
    confirmed by the reviewer)."""
    for o in SCHEMAS[version]:
        conn.execute(o.ddl)


def drift(objs: dict, version: int = 1) -> list:
    """Rebuildable objects that are missing, or present with the wrong DDL.

    Keyed by `(kind, name)`. Returns typed keys so a caller cannot repair an
    index by dropping a same-named trigger."""
    out = []
    for o in SCHEMAS[version]:
        if o.policy != REBUILDABLE:
            continue
        if objs.get(o.key, {}).get("sql") != o.ddl:
            out.append(o.key)
    return sorted(out)


def manifest(conn: sqlite3.Connection) -> dict:
    """Every non-internal persistent object, keyed by **(type, name)**.

    **Takes an open connection, not a path.** v3's instrument reopened
    `self._path` read-only, which cannot work for `SqliteStore(":memory:")` -- a
    supported constructor today. Reopening `":memory:"` silently yields a
    *different, empty* database, so the instrument reported an empty manifest
    rather than failing (round 2, finding 10).

    **The stored DDL is kept byte-for-byte.** v4 collapsed whitespace with
    `" ".join(sql.split())`, which is not a whitespace-only transformation in
    SQL: it also rewrites the inside of quoted string literals. Round 3 built
    two schemas differing only in `CHECK(object <> \'a  b\')` versus
    `\'a b\'` -- opposite accept/reject behaviour, **identical digests**.
    Reproduced. For an exact-known-output design the safe normalisation is
    none."""
    objs = {}
    for typ, name, tbl, sql in conn.execute(_OBJECTS).fetchall():
        entry = {"type": typ, "table": tbl, "sql": sql}
        if typ == "table":
            # `table_xinfo`, not `table_info`: the latter omits generated
            # columns entirely (round 1). The name is passed as a VALUE to the
            # table-valued pragma -- a table name read out of a foreign file is
            # an identifier chosen by whoever wrote that file.
            entry["columns"] = [
                [r[1], (r[2] or "").upper(), int(r[3]),
                 None if r[4] is None else str(r[4]), int(r[5]), int(r[6])]
                for r in conn.execute(
                    "SELECT * FROM pragma_table_xinfo(?)", (name,))]
        objs[(typ, name)] = entry
    return objs




MIGRATIONS: dict = {}
"""from_version -> list of (to_version, callable(executor)).

**Empty today**, which is the point: the mechanism lands with zero migrations so
its first real use in `0006` is not also its first execution. `--selfcheck`
exercises path generation against a simulated version 2 so "empty" never means
"untested"."""


class MigrationResult(NamedTuple):
    """What a migration statement returns. **Never a `sqlite3.Cursor`.**

    Round 4, finding 7: a raw cursor exposes `cursor.connection`, and from there
    `set_authorizer(None)` followed by `commit()` ends the outer transaction.
    Measured: the direct `COMMIT` is denied and the cursor route succeeds. A
    proxy that only hides the connection attribute does not make the connection
    unreachable -- the *result type* has to be inert."""
    rowcount: int
    rows: tuple
    lastrowid: int | None


class MigrationExecutor:
    """The only thing a migration function receives.

    No connection, no `commit`, no `rollback`, no `executescript`, and no cursor.
    The authorizer denies transaction and schema-attachment operations outright,
    so containment is structural rather than a keyword blacklist -- v4's
    blacklist missed `END`, `END TRANSACTION` and `RELEASE`, all measured."""

    _DENIED = (sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_SAVEPOINT,
               sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH)

    def __init__(self, conn: sqlite3.Connection):
        self.__conn = conn          # name-mangled; not part of the interface

    def execute(self, sql: str, params=()) -> MigrationResult:
        cur = self.__conn.execute(sql, params)
        try:
            rows = tuple(cur.fetchall())
            return MigrationResult(cur.rowcount, rows, cur.lastrowid)
        finally:
            cur.close()             # the cursor never escapes


def run_migration(conn: sqlite3.Connection, fn) -> None:
    """Run `fn` under the authorizer, and **restore it in `finally`**.

    Leaving a denying authorizer installed would break the planner's own commit;
    leaving it off after a failure would silently drop containment for whatever
    ran next."""
    def auth(action, *_rest):
        return (sqlite3.SQLITE_DENY if action in MigrationExecutor._DENIED
                else sqlite3.SQLITE_OK)
    conn.set_authorizer(auth)
    try:
        fn(MigrationExecutor(conn))
    finally:
        conn.set_authorizer(None)


# --------------------------------------------------------------------------
# SQLite runtime policy -- round 4, finding 8 / S-Q6

TESTED_SQLITE = ("3.45.1", "3.46.1")
"""Runtimes for which an accepted manifest has actually been observed.

3.45.1 here; 3.46.1 in the round-3 review environment, which agreed. **That is
two observations, not a matrix**, and v5 declared `3.35 <= sqlite < 4` on the
strength of it. Round 4 is right that a declared range with neither evidence nor
enforcement is not a contract.

**Ruled: the runtime-gated model.** Support is the tested set; anything else is
refused with `unsupported-sqlite` rather than silently assumed compatible.
Widening happens by adding evidence, not by widening the sentence."""


def sqlite_supported(version: str | None = None) -> bool:
    return (version or sqlite3.sqlite_version) in TESTED_SQLITE


def identity(objs: dict) -> dict:
    """The version-independent record: every typed object, nothing excluded.

    **`digest()` cannot be the identity of a store**, because which objects it
    excludes depends on the version's rebuildable policy -- and resolving an
    unstamped store means not knowing the version yet. Round 4, finding 3,
    measured: a simulated version 2 with its own rebuildable index digests to
    `4b250945...` under version 1's policy and `754ec416...` under version 2's,
    and only the second is in version 2's accepted set. The default-to-version-1
    digest resolved to **nothing**.

    So identity is computed once, and each *candidate* version applies its own
    policy to it."""
    return {f"{k[0]}:{k[1]}": v for k, v in sorted(objs.items())}


def digest(objs: dict, version: int = 1) -> str:
    """sha256 over every object except the rebuildable ones **of `version`**.

    Exact set equality falls out rather than being a separate rule: an extra
    view, an unknown index, a foreign table and a trigger all change the digest.
    A trigger named like one of our indexes is not excluded, because the
    exclusion is `("index", name)` and the trigger is `("trigger", name)`."""
    skip = rebuildable_keys(version)
    scoped = {k: v for k, v in identity(objs).items()
              if tuple(k.split(":", 1)) not in skip}
    return hashlib.sha256(
        json.dumps(scoped, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def digest_of_path(path: str, version: int = 1) -> str:
    conn = sqlite3.connect(path)
    try:
        return digest(manifest(conn), version)
    finally:
        conn.close()


def resolve(objs: dict, records: dict) -> int | None:
    """Which schema version this store is, by trying each candidate's policy.

    Returns None when nothing matches **or when more than one version matches**
    -- if two versions ever declare the same persistent shape the answer is
    ambiguous, and §4-i needs an explicit rule rather than a dictionary
    inversion that silently picks one."""
    hits = set()
    for v, rec in records.items():
        version = int(v)
        try:
            dg = digest(objs, version)
        except KeyError:
            continue                # a version this build no longer constructs
        if any(a["digest"] == dg for a in rec["accepted"]):
            hits.add(version)
    return hits.pop() if len(hits) == 1 else None


def full_records(objs: dict) -> dict:
    """Identity plus the policy each object is held under -- the S23 comparison.

    v5's S23 compared `digest()`, **which excludes every rebuildable index**. So
    it passed while the registry declared
    `CREATE UNIQUE INDEX ix_edges_subj_rel ON edges(user_id)` -- a materially
    different index the registry would have instructed an implementation to
    install. Measured: `digest_equal True`, `drift []`. **A conformance check
    may not use the acceptance digest.**"""
    return identity(objs)


def registry_conformance(version: int = 1) -> list:
    """Differences between the registry's database and the product's `_SCHEMA`.

    Compares **complete typed records including rebuildable objects**, plus the
    rebuildable identities and drift. Empty list means conformant."""
    sys.path.insert(0, str(ROOT / "src"))
    from veracium.store.sqlite import SqliteStore
    probe = tempfile.mktemp(suffix=".db")
    SqliteStore(probe)
    pconn = sqlite3.connect(probe)
    rconn = sqlite3.connect(":memory:")
    create(rconn, version)
    prod, reg = manifest(pconn), manifest(rconn)
    problems = []
    pf, rf = full_records(prod), full_records(reg)
    for key in sorted(set(pf) | set(rf)):
        if pf.get(key) != rf.get(key):
            problems.append(f"{key}: registry {rf.get(key)!r} != product {pf.get(key)!r}")
    if drift(reg, version):
        problems.append(f"registry drifts against itself: {drift(reg, version)}")
    expected = {o.key for o in SCHEMAS[version] if o.policy == REBUILDABLE}
    if expected != rebuildable_keys(version):
        problems.append("rebuildable identities disagree with the registry")
    pconn.close()
    rconn.close()
    return problems


def accepted_digests(version: int) -> set:
    """**The closed set of manifests accepted at a version** -- round 3,
    finding 1.

    v4 declared one manifest per version, generated from the destination
    constructor, and required every migration result to equal it. Those rules
    are incompatible: `ALTER TABLE edges ADD COLUMN source_id TEXT` produces a
    database whose `table_xinfo` matches a fresh constructor's but whose stored
    DDL differs in whitespace placement. Measured: different digests,
    structurally correct migration, destination validation fails.

    So a version accepts a **set**: the constructor's output plus the output of
    every declared migration path reaching it, **generated by running them**."""
    return {a["digest"] for a in _version_records()[str(version)]["accepted"]}


def _version_records() -> dict:
    if MANIFEST_ARTIFACT.exists():
        return json.loads(MANIFEST_ARTIFACT.read_text())["versions"]
    return {}


def _paths_to(version: int) -> list:
    """Every declared migration path reaching `version`, as version chains."""
    chains = []
    def walk(v, acc):
        for to_v, fn in MIGRATIONS.get(v, ()):
            if to_v == version:
                chains.append(acc + [(v, to_v, fn)])
            elif to_v < version:
                walk(to_v, acc + [(v, to_v, fn)])
    for start in sorted(SCHEMAS):
        if start < version:
            walk(start, [])
    return chains


def build_version_artifact(strict: bool = True) -> dict:
    """Regenerate accepted manifests. **Prior versions are immutable.**

    Round 4, finding 6: v5 looped over every entry in `SCHEMAS` and replaced
    each version's constructor record, so a changed version-1 constructor
    silently rewrote history. Measured: `old_v1_preserved? False`.

    Policy now:

      version <  current : byte-for-byte immutable; a difference is an ERROR
      version == current : regenerate the constructor output AND every declared
                           migration-path output

    Round 4, finding 2: v5 preserved whatever records happened to be in the JSON
    and called them accepted, without ever running a migration. Preserved JSON
    cannot be an authorization source, so every record for the current version
    is produced by executing a declared constructor or path."""
    existing = {}
    if MANIFEST_ARTIFACT.exists():
        existing = json.loads(MANIFEST_ARTIFACT.read_text()).get("versions", {})
    current = max(SCHEMAS)
    out, problems = {}, []

    for version in sorted(SCHEMAS):
        accepted = []
        conn = sqlite3.connect(":memory:")
        create(conn, version)
        accepted.append({"provenance": f"constructor v{version}",
                         "digest": digest(manifest(conn), version),
                         "objects": identity(manifest(conn))})
        conn.close()
        for chain in _paths_to(version):
            base = chain[0][0]
            mc = sqlite3.connect(":memory:")
            create(mc, base)
            label = f"v{base}"
            for frm, to_v, fn in chain:
                run_migration(mc, fn)
                label += f"->v{to_v}"
            accepted.append({"provenance": f"migration {label}",
                             "digest": digest(manifest(mc), version),
                             "objects": identity(manifest(mc))})
            mc.close()
        record = {"accepted": accepted}
        if version < current and str(version) in existing:
            if existing[str(version)] != record:
                problems.append(
                    f"version {version} is historical and its regenerated record "
                    f"differs from the checked-in one. Historical manifests are "
                    f"immutable; a manifest-algorithm change needs a separately "
                    f"reviewed artifact migration.")
            out[str(version)] = existing[str(version)]
        else:
            out[str(version)] = record

    if problems and strict:
        raise SystemExit("\n".join(problems))
    return {"manifest_algorithm": 4, "versions": out,
            "tested_sqlite": list(TESTED_SQLITE)}


def _tags() -> list[str]:
    out = subprocess.run(["git", "tag"], cwd=ROOT, capture_output=True, text=True).stdout
    return sorted((t for t in out.split() if t.startswith("v")),
                  key=lambda t: [int(x) for x in t.lstrip("v").split(".")])


def _probe_at(ref: str, work: pathlib.Path) -> dict:
    """Build a store with the code at `ref` and return its row of evidence.

    **The code that creates the file is that release's own code.** A fixture
    generated by the code under test proves only that today's schema matches
    today's schema -- which is what round 1 correctly refused."""
    sha = subprocess.run(["git", "rev-list", "-n1", ref], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    row = {"tag": ref, "commit": sha, "on_disk_user_version": None,
           "store_schema_version": None, "digest": None, "result": None}
    wt = work / ref.replace("/", "_")
    r = subprocess.run(["git", "worktree", "add", "-q", "--detach", str(wt), ref],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        row["result"] = f"worktree failed: {r.stderr.strip()[:100]}"
        return row
    try:
        db = str(wt / "probe.db")
        r = subprocess.run(
            [sys.executable, "-c",
             f"from veracium.store.sqlite import SqliteStore; SqliteStore({db!r})"],
            cwd=wt, env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"},
            capture_output=True, text=True)
        if r.returncode:
            row["result"] = f"unbuildable: {r.stderr.strip().splitlines()[-1][:100]}"
            return row
        # Round 4, finding 4: the artifact could not tell a genuinely
        # unstamped legacy store from a version-aware release that wrote a
        # valid stamp -- and only the former may feed LEGACY_DIGESTS. Record
        # what is actually in the header.
        probe = sqlite3.connect(db)
        row["on_disk_user_version"] = probe.execute("PRAGMA user_version").fetchone()[0]
        row["objects"] = identity(manifest(probe))
        probe.close()
        row["result"] = "ok"
        return row
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=ROOT, capture_output=True)




def releases(write: bool) -> int:
    """Every released tag, built by its own code, resolved to a schema version.

    **v4 required every release to equal HEAD, which stops working the moment
    the schema changes** -- the exact event 0007 exists to enable (round 3,
    finding 4). Once version 2 lands, old releases legitimately carry the
    version-1 shape, and `--releases --write` would have returned failure while
    `--check` demanded a regeneration that could not succeed.

    A release now resolves to *a known version*. Differing from HEAD is expected
    and fine; **not matching any known manifest is the failure.**"""
    version_artifact = build_version_artifact()
    records = version_artifact["versions"]
    tags = _tags()
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        head = _probe_at("HEAD", work)
        if head["result"] != "ok":
            print(f"HEAD: {head['result']}", file=sys.stderr)
            return 1
        rows = [_probe_at(t, work) for t in tags]

    def _resolved(row):
        """Candidate-based, never a default-version digest (finding 3)."""
        objs = {tuple(k.split(":", 1)): v for k, v in row["objects"].items()}
        v = resolve(objs, records)
        row["store_schema_version"] = v
        row["digest"] = None if v is None else digest(objs, v)
        row.pop("objects", None)
        return v

    unknown, broken, mismatched = [], [], []
    for r in rows:
        if r["result"] != "ok":
            broken.append(r)
            continue
        v = _resolved(r)
        if v is None:
            unknown.append(r)
        elif r["on_disk_user_version"] not in (0, v):
            # A version-aware release must stamp what it built.
            mismatched.append(r)
    head_version = _resolved(head)

    for r in rows:
        v = r["store_schema_version"]
        stamp = r["on_disk_user_version"]
        mark = (r["result"] if r["result"] != "ok"
                else f"schema v{v}, " + ("unstamped (legacy)" if stamp == 0
                                         else f"stamped {stamp}")
                if v is not None else "** UNKNOWN MANIFEST **")
        print(f"  {r['tag']:<10} {r['commit'][:12]}  {mark}")
    print(f"\n{len(rows) - len(unknown) - len(broken)}/{len(rows)} resolve to a known "
          f"schema version · {len(broken)} unbuildable · sqlite {sqlite3.sqlite_version}")
    print(f"HEAD resolves to schema v{head_version}")

    if write:
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(json.dumps({
            "head_digest": head["digest"],
            "head_schema_version": head_version,
            "sqlite_version": sqlite3.sqlite_version,
            "manifest_algorithm": version_artifact["manifest_algorithm"],
            "tested_sqlite": list(TESTED_SQLITE),
            # Pre-versioning releases carry no stamp; this is the base version
            # the version-zero resolver maps their digest to (0007 §4-i).
            # ONLY genuinely unstamped stores are legacy candidates.
            "legacy_base_versions": sorted(
                {r["store_schema_version"] for r in rows
                 if r["store_schema_version"] is not None
                 and r["on_disk_user_version"] == 0}),
            "releases": rows,
        }, indent=2) + "\n")
        MANIFEST_ARTIFACT.write_text(json.dumps(version_artifact, indent=2) + "\n")
        print(f"wrote {ARTIFACT.relative_to(ROOT)} and "
              f"{MANIFEST_ARTIFACT.relative_to(ROOT)}")
    if broken:
        print("\nAn unbuildable release is NOT evidence of compatibility — it is a "
              "gap in the evidence, and 0007 §4a-iv must say so.", file=sys.stderr)
        return 1
    if unknown:
        print("\nA release matching no known manifest means adoption cannot be "
              "unconditional: that store's shape is not one this build can name.",
              file=sys.stderr)
        return 1
    if mismatched:
        for r in mismatched:
            print(f"\n{r['tag']}: stamped {r['on_disk_user_version']} but its shape "
                  f"is v{r['store_schema_version']}", file=sys.stderr)
        return 1
    return 0


def check() -> int:
    """CI: the stored artifact must still describe reality, field by field.

    **Round 4, finding 5: v5 checked that a digest resolved to *some* version,
    not to the *recorded* one.** A synthetic artifact claiming
    `store_schema_version: 999` for every release passed with rc 0 -- measured.
    That number selects the migration base for unstamped stores, so an unchecked
    one is a live wrong answer, not a cosmetic drift."""
    if subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT,
                      capture_output=True).returncode:
        print("--check needs a git checkout: it rebuilds a store from every "
              "released tag. An extracted archive has no git metadata.",
              file=sys.stderr)
        return 2
    if not ARTIFACT.exists():
        print(f"{ARTIFACT.name} missing — run --releases --write", file=sys.stderr)
        return 1
    stored = json.loads(ARTIFACT.read_text())
    records = build_version_artifact()["versions"]

    bad = []
    if stored.get("manifest_algorithm") != build_version_artifact()["manifest_algorithm"]:
        bad.append(f"manifest algorithm changed: artifact says "
                   f"{stored.get('manifest_algorithm')}, this build computes "
                   f"{build_version_artifact()['manifest_algorithm']} — historical "
                   f"records need a reviewed migration, not a silent rewrite")
    if sorted(stored.get("tested_sqlite", [])) != sorted(TESTED_SQLITE):
        bad.append(f"tested sqlite set changed: {stored.get('tested_sqlite')} → "
                   f"{list(TESTED_SQLITE)}")
    if MANIFEST_ARTIFACT.exists():
        on_disk = json.loads(MANIFEST_ARTIFACT.read_text())
        if on_disk.get("versions") != records:
            bad.append("schema_versions.json does not match what this build "
                       "generates — regenerate, or restore the historical record")

    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        head = _probe_at("HEAD", work)
        fresh = {r["tag"]: r for r in (_probe_at(t, work) for t in _tags())}

    def _res(row):
        objs = {tuple(k.split(":", 1)): v for k, v in row.get("objects", {}).items()}
        v = resolve(objs, records)
        return v, (None if v is None else digest(objs, v))

    hv, _ = _res(head)
    if hv is None:
        bad.append("HEAD matches no known manifest — regenerate with "
                   "--releases --write, and bump SCHEMA_VERSION if the schema "
                   "actually changed")

    for row in stored["releases"]:
        now = fresh.get(row["tag"])
        if now is None:
            bad.append(f"{row['tag']}: recorded but no longer a tag")
            continue
        if now["commit"] != row["commit"]:
            bad.append(f"{row['tag']}: tag moved {row['commit'][:12]} → "
                       f"{now['commit'][:12]}")
            continue
        v, dg = _res(now)
        # Every recorded field is re-derived and compared. Verifying only that
        # the digest resolves to *something* is what let 999 through.
        if dg != row["digest"]:
            bad.append(f"{row['tag']}: digest changed — a released tag's store "
                       f"shape cannot change; either the tag moved or the "
                       f"manifest algorithm did")
        if v != row.get("store_schema_version"):
            bad.append(f"{row['tag']}: recorded schema version "
                       f"{row.get('store_schema_version')} but resolves to {v}")
        if now["on_disk_user_version"] != row.get("on_disk_user_version"):
            bad.append(f"{row['tag']}: recorded stamp "
                       f"{row.get('on_disk_user_version')} but reads "
                       f"{now['on_disk_user_version']}")

    for t in _tags():
        if t not in {r["tag"] for r in stored["releases"]}:
            bad.append(f"{t}: released since the artifact was generated")

    if stored.get("sqlite_version") != sqlite3.sqlite_version:
        print(f"note: artifact gathered with sqlite {stored.get('sqlite_version')}, "
              f"this environment has {sqlite3.sqlite_version}")
    if not sqlite_supported():
        bad.append(f"sqlite {sqlite3.sqlite_version} is not in the tested set "
                   f"{list(TESTED_SQLITE)} — see 0007 §8, runtime-gated support")

    for b in bad:
        print(b, file=sys.stderr)
    if bad:
        print(f"\n{len(bad)} problem(s) — run --releases --write", file=sys.stderr)
        return 1
    legacy = sorted({r["store_schema_version"] for r in stored["releases"]
                     if r.get("on_disk_user_version") == 0})
    print(f"legacy store evidence current — {len(stored['releases'])} releases, "
          f"unstamped legacy base version(s) {legacy}, HEAD at v{hv}, "
          f"sqlite {sqlite3.sqlite_version}")
    return 0


# --------------------------------------------------------------------------
# selfcheck


def selfcheck() -> int:
    """Build every counterexample and report whether the manifest sees it.

    **R1/R2/R3 mark which review round constructed each case.** The rows that
    must NOT fire are the ones to read sceptically: a check that refuses stores
    which are genuinely fine gets bypassed."""
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from veracium.store.sqlite import SqliteStore, _SCHEMA
    except ImportError:
        print("needs the veracium package importable: PYTHONPATH=src", file=sys.stderr)
        return 1

    def fresh() -> str:
        p = tempfile.mktemp(suffix=".db")
        SqliteStore(p)
        return p

    def mutate(sql, collation=False) -> str:
        p = fresh()
        c = sqlite3.connect(p)
        if collation:
            c.create_collation("MYCOLL", lambda a, b: (a > b) - (a < b))
        for stmt in sql:
            c.execute(stmt)
        c.commit()
        c.close()
        return p

    def variant(old: str, new: str) -> str:
        """One change against the REAL schema text.

        Hand-writing a near-copy is how I first failed to reproduce two of round
        2's counterexamples: the reconstruction differed in some *other* way, so
        it was caught for the wrong reason and I nearly reported a real finding
        as unconfirmed. Deriving from `_SCHEMA` changes exactly one thing."""
        t = _SCHEMA.replace(old, new)
        assert t != _SCHEMA, f"variant did not apply: {old!r}"
        p = tempfile.mktemp(suffix=".db")
        c = sqlite3.connect(p)
        c.executescript(t)
        c.commit()
        c.close()
        return p

    good = digest_of_path(fresh())

    stripped = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(stripped)
    c.executescript(
        "CREATE TABLE edges (id TEXT, user_id TEXT, subject TEXT, relation TEXT,"
        " object TEXT, active INTEGER, quarantined INTEGER, json TEXT);"
        "CREATE TABLE episodes (id TEXT, user_id TEXT, date TEXT, json TEXT);"
        "CREATE TABLE wiki (user_id TEXT, text TEXT, store_version INTEGER);"
        "CREATE TABLE write_counter (user_id TEXT, n INTEGER);")
    c.commit()
    c.close()

    # (label, digest must differ, drift expectation or None, path)
    cases = [
        ("R1: constraint-stripped clone", True, None, stripped),
        ("R1: generated column on edges", True, None, mutate(
            ["ALTER TABLE edges ADD COLUMN leak TEXT "
             "GENERATED ALWAYS AS (subject||object) VIRTUAL"])),
        ("R1: unrelated table beside ours", True, None, mutate(
            ["CREATE TABLE unrelated_application_data (x)"])),
        ("R1: trigger on a protected table", True, None, mutate(
            ["CREATE TRIGGER t AFTER INSERT ON edges "
             "BEGIN UPDATE edges SET active=0; END"])),
        ("R2: CHECK(active = 0) on edges", True, None, variant(
            "active INTEGER NOT NULL,", "active INTEGER NOT NULL CHECK(active = 0),")),
        ("R2: COLLATE NOCASE primary key", True, None, variant(
            "id TEXT PRIMARY KEY", "id TEXT COLLATE NOCASE PRIMARY KEY")),
        ("R2: extra persistent VIEW", True, None, mutate(
            ["CREATE VIEW v AS SELECT * FROM edges"])),
        ("R2: index on a host-defined collation", True, None, mutate(
            ["CREATE INDEX ix_custom ON edges(subject COLLATE MYCOLL)"], collation=True)),
        ("R3: CHECK literal, two-space", True, None, variant(
            "object TEXT,", "object TEXT CHECK(object <> 'a  b'),")),
        # R3 finding 3: a trigger sharing an index's name. v4 digested this
        # IDENTICAL to a clean store.
        ("R3: trigger named like an index", True, None, mutate(
            ["CREATE TRIGGER ix_edges_subj_rel AFTER INSERT ON edges "
             "BEGIN UPDATE edges SET active=0 WHERE id=NEW.id; END"])),
        ("drifted same-named UNIQUE index", False, True, mutate(
            ["DROP INDEX ix_edges_subj_rel",
             "CREATE UNIQUE INDEX ix_edges_subj_rel ON edges(user_id, subject)"])),
        ("ANALYZE — must NOT differ", False, False, mutate(["ANALYZE"])),
        ("missing acceleration index — drift only", False, True, mutate(
            ["DROP INDEX ix_edges_subj_rel"])),
    ]

    bad = 0
    print(f"{'case':<48}{'digest':>9}{'drift':>7}   result")
    for name, should_differ, should_drift, path in cases:
        conn = sqlite3.connect(path)
        objs = manifest(conn)
        conn.close()
        differs, drifted = digest(objs) != good, bool(drift(objs))
        ok = differs == should_differ and (should_drift is None or drifted == should_drift)
        bad += not ok
        print(f"  {name:<46}{'differs' if differs else 'same':>9}"
              f"{('n/a' if should_drift is None else 'yes' if drifted else 'no'):>7}"
              f"   {'ok' if ok else '** WRONG **'}")

    def row(label, ok):
        nonlocal bad
        bad += not ok
        print(f"  {label:<46}{'':>9}{'':>7}   {'ok' if ok else '** WRONG **'}")

    # The registry must reproduce the production schema, or every expectation
    # above is measured against the wrong reference (0007 S23).
    ref = sqlite3.connect(":memory:")
    create(ref)
    row("registry reproduces _SCHEMA exactly", digest(manifest(ref)) == good)

    # R3 finding 1: a normal ALTER migration must reach an accepted manifest.
    altered = mutate(["ALTER TABLE edges ADD COLUMN source_id TEXT"])
    con = sqlite3.connect(":memory:")
    create(con)
    con.execute("ALTER TABLE edges ADD COLUMN source_id TEXT")
    row("ALTER migration is reproducible as an accepted output",
        digest_of_path(altered) == digest(manifest(con)))
    fresh_with_col = tempfile.mktemp(suffix=".db")
    c2 = sqlite3.connect(fresh_with_col)
    c2.executescript(_SCHEMA.replace("json TEXT NOT NULL\n)",
                                     "json TEXT NOT NULL, source_id TEXT\n)"))
    c2.commit()
    c2.close()
    row("ALTER output differs from the fresh constructor — hence a SET per version",
        digest_of_path(altered) != digest_of_path(fresh_with_col))

    # R3 finding 2, the actual claim: two schemas differing ONLY inside a
    # quoted literal must not collide. They accept and reject exactly opposite
    # values, and v4's `" ".join(sql.split())` gave them the same digest.
    two = variant("object TEXT,", "object TEXT CHECK(object <> 'a  b'),")
    one = variant("object TEXT,", "object TEXT CHECK(object <> 'a b'),")
    row("R3: 'a  b' and 'a b' are NOT the same schema",
        digest_of_path(two) != digest_of_path(one))

    # R3 finding 3, second half: a trigger sharing an index's name must be
    # caught by the DIGEST, and must NOT be mistaken for index drift -- v4
    # reported drift on it, which would have sent an implementation off to
    # "repair" an index that was never broken.
    poisoned = mutate(["CREATE TRIGGER ix_edges_subj_rel AFTER INSERT ON edges "
                       "BEGIN UPDATE edges SET active=0 WHERE id=NEW.id; END"])
    pc = sqlite3.connect(poisoned)
    pobjs = manifest(pc)
    row("R3: the same-named trigger is a digest failure, not index drift",
        digest(pobjs) != good and not drift(pobjs))
    pc.close()

    # R3 finding 4 + R4 findings 2 and 3, together, because they are the same
    # experiment: simulate version 2 WITH a migration and a version-2-only
    # rebuildable index, then check resolution, path generation and immutability.
    v2 = SCHEMA_V1 + (
        SchemaObject("table", "sources",
                     "CREATE TABLE sources (id TEXT PRIMARY KEY, label TEXT)", REQUIRED),
        SchemaObject("index", "ix_sources",
                     "CREATE INDEX ix_sources ON sources(id)", REBUILDABLE))

    def migrate_1_to_2(ex):
        ex.execute("CREATE TABLE sources (id TEXT PRIMARY KEY, label TEXT)")
        ex.execute("CREATE INDEX ix_sources ON sources(id)")

    SCHEMAS[2] = v2
    MIGRATIONS[1] = [(2, migrate_1_to_2)]
    try:
        sim = build_version_artifact(strict=False)["versions"]
        prov = [a["provenance"] for a in sim["2"]["accepted"]]
        row("R4: the migration path is GENERATED into the accepted set",
            "migration v1->v2" in prov and "constructor v2" in prov)

        c1 = sqlite3.connect(":memory:"); create(c1, 1)
        c2 = sqlite3.connect(":memory:"); create(c2, 2)
        o1, o2 = manifest(c1), manifest(c2)
        row("R3: a v1 store still resolves once HEAD is v2",
            resolve(o1, sim) == 1 and resolve(o2, sim) == 2)
        # R4 finding 3: the v1-policy digest of a v2 store resolves to nothing.
        # Candidate matching must not depend on knowing the answer first.
        row("R4: resolution does not depend on a default-version digest",
            digest(o2, 1) != digest(o2, 2)
            and not any(a["digest"] == digest(o2, 1) for a in sim["2"]["accepted"])
            and resolve(o2, sim) == 2)
        # the migrated store must itself be accepted at v2
        mc = sqlite3.connect(":memory:"); create(mc, 1)
        run_migration(mc, migrate_1_to_2)
        row("R4: a migrated store is accepted at its destination version",
            resolve(manifest(mc), sim) == 2)
        row("R3: an unknown shape resolves to nothing, not to a guess",
            resolve({("table", "nope"): {"type": "table", "table": "nope",
                                        "sql": "CREATE TABLE nope (x)",
                                        "columns": []}}, sim) is None)
        c1.close(); c2.close(); mc.close()
    finally:
        del SCHEMAS[2]
        MIGRATIONS.pop(1, None)

    # R4 finding 1: the registry-conformance check must compare complete typed
    # records, including rebuildable indexes -- the acceptance digest excludes
    # them, so it cannot serve as a conformance check.
    row("R4: registry conformance covers rebuildable definitions",
        registry_conformance(1) == [])
    saved = SCHEMAS[1]
    SCHEMAS[1] = tuple(o._replace(ddl="CREATE UNIQUE INDEX ix_edges_subj_rel "
                                      "ON edges(user_id)")
                       if o.name == "ix_edges_subj_rel" else o for o in saved)
    row("R4: a wrong rebuildable definition FAILS conformance",
        len(registry_conformance(1)) == 1)
    SCHEMAS[1] = saved

    # R4 finding 7: nothing a migration receives may reach the connection.
    esc = {}
    probe = sqlite3.connect(":memory:")
    probe.isolation_level = None
    probe.execute("CREATE TABLE t(a)")
    probe.execute("BEGIN IMMEDIATE")

    def escape_attempt(ex):
        res = ex.execute("SELECT 1")
        esc["cursor"] = hasattr(res, "connection")
        for stmt in ("COMMIT", "END", "END TRANSACTION", "ROLLBACK",
                     "SAVEPOINT s", "RELEASE s", "ATTACH ':memory:' AS x"):
            try:
                ex.execute(stmt)
                esc[stmt] = "ALLOWED"
            except sqlite3.DatabaseError:
                pass

    run_migration(probe, escape_attempt)
    row("R4: the migration result exposes no connection, and no escape allowed",
        esc.get("cursor") is False and len(esc) == 1 and probe.in_transaction)
    probe.execute("COMMIT")          # authorizer restored in finally
    row("R4: the authorizer is restored after the migration", not probe.in_transaction)
    probe.close()

    # R4 finding 8 / S-Q6: runtime-gated support, not a declared range.
    row("R4: the running sqlite is in the tested set",
        sqlite_supported() and sqlite3.sqlite_version in TESTED_SQLITE)
    row("R4: an untested runtime is refused, not assumed", not sqlite_supported("3.99.0"))

        # R2 finding 10: an in-memory store is a supported constructor.
    mem = SqliteStore(":memory:")
    mem_objs = manifest(mem._conn)
    row("in-memory store, via its own connection",
        digest(mem_objs) == good and not drift(mem_objs))

    total = len(cases) + 15
    print(f"\n{total - bad}/{total} as specified")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--releases", action="store_true")
    ap.add_argument("--write", action="store_true",
                    help="with --releases: write the durable artifact")
    ap.add_argument("--check", action="store_true", help="CI: the artifact still matches")
    ap.add_argument("--digest", metavar="DB")
    a = ap.parse_args()
    if a.selfcheck:
        return selfcheck()
    if a.releases:
        return releases(a.write)
    if a.check:
        return check()
    if a.digest:
        conn = sqlite3.connect(a.digest)
        objs = manifest(conn)
        print(json.dumps(objs, indent=2))
        print(f"\ndigest {digest(objs)}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
