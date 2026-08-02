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
  `--check`       verify that artifact still matches, for CI.
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


def digest(objs: dict, version: int = 1) -> str:
    """sha256 over every object except the rebuildable ones, by typed identity.

    Exact set equality falls out rather than being a separate rule: an extra
    view, an unknown index, a foreign table and a trigger all change the digest.
    **A trigger named like one of our indexes is no longer excluded**, because
    the exclusion is `("index", name)` and the trigger is `("trigger", name)`."""
    skip = rebuildable_keys(version)
    scoped = {f"{k[0]}:{k[1]}": v for k, v in objs.items() if k not in skip}
    return hashlib.sha256(
        json.dumps(scoped, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def digest_of_path(path: str) -> str:
    conn = sqlite3.connect(path)
    try:
        return digest(manifest(conn))
    finally:
        conn.close()


def accepted_digests(version: int) -> set:
    """**The closed set of manifests accepted at a version** -- round 3,
    finding 1.

    v4 declared one manifest per version, generated from the destination
    constructor, and required every migration result to equal it. Those rules
    are incompatible: an `ALTER TABLE edges ADD COLUMN source_id TEXT` produces
    a database whose `table_xinfo` is identical to a fresh constructor's but
    whose stored DDL differs in whitespace placement -- `... json TEXT NOT NULL
    , source_id TEXT)` against `... json TEXT NOT NULL, source_id TEXT )`.
    Measured: different digests, structurally correct migration, destination
    validation fails.

    So a version accepts a **set**: the constructor's output plus the output of
    every supported migration path reaching it. The set is generated, closed,
    and recorded in `specs/generated/schema_versions.json`. Today version 1 has
    exactly one member because there are no migrations."""
    return {v["digest"] for v in _version_records()[str(version)]["accepted"]}


def _version_records() -> dict:
    if MANIFEST_ARTIFACT.exists():
        return json.loads(MANIFEST_ARTIFACT.read_text())["versions"]
    return {}


def build_version_artifact() -> dict:
    """Regenerate the current version's entry; never rewrite an older one.

    **Old entries are immutable** (round 3, finding 5). Once `_SCHEMA` moves to
    version 2, the current constructor can no longer produce version 1, and a
    digest alone cannot support the object-level `diff` 0007 §4b promises. The
    full canonical object records for every version therefore have to be kept,
    not regenerated."""
    existing = {}
    if MANIFEST_ARTIFACT.exists():
        existing = json.loads(MANIFEST_ARTIFACT.read_text()).get("versions", {})
    out = dict(existing)
    for version in sorted(SCHEMAS):
        conn = sqlite3.connect(":memory:")
        create(conn, version)
        objs = manifest(conn)
        record = {
            "provenance": f"constructor v{version}",
            "digest": digest(objs, version),
            "objects": {f"{k[0]}:{k[1]}": v for k, v in sorted(objs.items())},
        }
        prior = existing.get(str(version), {}).get("accepted", [])
        keep = [a for a in prior if a["provenance"] != record["provenance"]]
        out[str(version)] = {"accepted": [record] + keep}
        conn.close()
    return {"manifest_algorithm": 3, "versions": out}


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
    row = {"tag": ref, "commit": sha, "digest": None, "result": None}
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
        row["digest"] = digest_of_path(db)
        row["result"] = "ok"
        return row
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=ROOT, capture_output=True)


def _resolve_version(dg: str, records: dict) -> int | None:
    """Which schema version a digest corresponds to, or None if unknown.

    **The inversion must be unambiguous** (round 3, finding 5). If two versions
    ever declare the same persistent shape, this returns None rather than
    guessing, and the version-zero resolver in 0007 §4-i needs an explicit rule
    instead of a dictionary inversion."""
    hits = {int(v) for v, rec in records.items()
            for a in rec["accepted"] if a["digest"] == dg}
    return hits.pop() if len(hits) == 1 else None


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

    unknown, broken = [], []
    for r in rows:
        if r["result"] != "ok":
            broken.append(r)
            r["store_schema_version"] = None
        else:
            r["store_schema_version"] = _resolve_version(r["digest"], records)
            if r["store_schema_version"] is None:
                unknown.append(r)
    head_version = _resolve_version(head["digest"], records)

    for r in rows:
        v = r["store_schema_version"]
        mark = (r["result"] if r["result"] != "ok"
                else f"schema v{v}" if v is not None else "** UNKNOWN MANIFEST **")
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
            # Pre-versioning releases carry no stamp; this is the base version
            # the version-zero resolver maps their digest to (0007 §4-i).
            "legacy_base_versions": sorted(
                {r["store_schema_version"] for r in rows
                 if r["store_schema_version"] is not None}),
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
    return 0


def check() -> int:
    """CI: the stored artifact must still describe reality.

    Compares the per-release digests and their resolved commit shas -- a tag is
    a mutable name, so recording where it pointed is half the evidence. The
    recorded `sqlite_version` is informational and reported rather than failed:
    the digest is what carries the claim."""
    if not ARTIFACT.exists():
        print(f"{ARTIFACT.name} missing — run --releases --write", file=sys.stderr)
        return 1
    stored = json.loads(ARTIFACT.read_text())
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        head = _probe_at("HEAD", work)
        fresh_rows = {r["tag"]: r for r in (_probe_at(t, work) for t in _tags())}
    bad = []
    # NOT "HEAD must equal the recorded head digest" -- that is what round 3's
    # finding 4 showed becomes unsatisfiable at version 2. What must hold is
    # that HEAD still resolves to a KNOWN version.
    records = build_version_artifact()["versions"]
    if _resolve_version(head["digest"], records) is None:
        bad.append("HEAD matches no known manifest — regenerate with "
                   "--releases --write, and bump SCHEMA_VERSION if the schema "
                   "actually changed")
    for row in stored["releases"]:
        now = fresh_rows.get(row["tag"])
        if now is None:
            bad.append(f"{row['tag']}: recorded but no longer a tag")
        elif now["commit"] != row["commit"]:
            bad.append(f"{row['tag']}: tag moved {row['commit'][:12]} → {now['commit'][:12]}")
        elif now["digest"] != row["digest"]:
            bad.append(f"{row['tag']}: digest changed — a released tag's store shape "
                       f"cannot change; either the tag moved or the manifest "
                       f"algorithm did")
        elif _resolve_version(now["digest"], records) is None:
            bad.append(f"{row['tag']}: no longer resolves to a known schema version")
    for t in _tags():
        if t not in {r["tag"] for r in stored["releases"]}:
            bad.append(f"{t}: released since the artifact was generated")
    if stored.get("sqlite_version") != sqlite3.sqlite_version:
        print(f"note: artifact gathered with sqlite {stored.get('sqlite_version')}, "
              f"this environment has {sqlite3.sqlite_version}")
    for b in bad:
        print(b, file=sys.stderr)
    if bad:
        print(f"\n{len(bad)} problem(s) — run --releases --write", file=sys.stderr)
        return 1
    versions = sorted({r.get("store_schema_version") for r in stored["releases"]}
                      - {None})
    print(f"legacy store evidence current — {len(stored['releases'])} releases, "
          f"schema version(s) {versions}, HEAD at "
          f"v{_resolve_version(head['digest'], records)}")
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

    # R3 finding 4: the evidence must survive the first schema change. Simulate
    # version 2 without touching the artifact, and check that a version-1 store
    # -- an old release -- still resolves, while HEAD resolves to 2.
    v2 = SCHEMA_V1 + (SchemaObject(
        "table", "sources",
        "CREATE TABLE sources (id TEXT PRIMARY KEY, label TEXT)", REQUIRED),)
    SCHEMAS[2] = v2
    try:
        sim = build_version_artifact()["versions"]
        c1 = sqlite3.connect(":memory:"); create(c1, 1)
        c2 = sqlite3.connect(":memory:"); create(c2, 2)
        d1, d2 = digest(manifest(c1), 1), digest(manifest(c2), 2)
        row("R3: a v1 store still resolves once HEAD is v2",
            _resolve_version(d1, sim) == 1 and _resolve_version(d2, sim) == 2)
        row("R3: an unknown shape resolves to nothing, not to a guess",
            _resolve_version("0" * 64, sim) is None)
        c1.close(); c2.close()
    finally:
        del SCHEMAS[2]

    # R2 finding 10: an in-memory store is a supported constructor.
    mem = SqliteStore(":memory:")
    mem_objs = manifest(mem._conn)
    row("in-memory store, via its own connection",
        digest(mem_objs) == good and not drift(mem_objs))

    total = len(cases) + 8
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
