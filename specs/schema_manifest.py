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

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARTIFACT = ROOT / "specs" / "generated" / "legacy_stores.json"

# Only SQLite's own objects are excluded, and only these. `sqlite_stat1` appears
# after ANALYZE; `sqlite_autoindex_*` are implicit indexes with no stored DDL.
# GLOB, not LIKE: backslash is not a LIKE escape without an explicit ESCAPE
# clause, so `LIKE 'sqlite\_%'` excluded nothing (0007 §4a-i, measured).
_OBJECTS = ("SELECT type, name, tbl_name, sql FROM sqlite_master "
            "WHERE name NOT GLOB 'sqlite_*' ORDER BY type, name")

# Veracium-owned acceleration indexes: the ONLY objects outside the digest,
# because they are rebuilt from these canonical definitions rather than trusted.
# Every other object, including any index NOT named here, is inside the digest,
# so an unknown index is a refusal without needing its own rule.
#
# **Excluding them from the digest is not the same as ignoring them.** A store
# already stamped at the current version never goes through adoption, so nothing
# would ever rebuild its indexes -- and a UNIQUE index sharing one of these names
# changes which writes are accepted. `drift()` is the second dimension: a
# rebuildable index that is missing or not byte-identical to its canonical
# definition must be dropped and recreated before the store is used. Two
# dimensions, because one digest cannot both ignore an object and police it.
REBUILDABLE = {
    "ix_edges_user_active":
        "CREATE INDEX ix_edges_user_active ON edges(user_id, active)",
    "ix_edges_subj_rel":
        "CREATE INDEX ix_edges_subj_rel ON edges(user_id, subject, relation, active)",
    "ix_episodes_user":
        "CREATE INDEX ix_episodes_user ON episodes(user_id, date)",
}


def drift(objs: dict) -> list[str]:
    """Rebuildable indexes that are missing, or present with the wrong DDL.

    Non-empty means a write is required before the store may be used. Empty
    means the fast path can open without one -- which is why this is a separate
    function rather than an unconditional rebuild on every open."""
    return sorted(name for name, sql in REBUILDABLE.items()
                  if objs.get(name, {}).get("sql") != sql)


def _canonical_sql(sql: str | None) -> str | None:
    """Whitespace-collapsed DDL, exactly as SQLite stored it.

    Deliberately minimal. Every normalisation beyond whitespace is a claim that
    two different texts mean the same thing -- which is the equivalence problem
    this module exists to stop solving. SQLite already strips `IF NOT EXISTS`
    when storing the DDL, so the text is stable across the constructor."""
    return None if sql is None else " ".join(sql.split())


def manifest(conn: sqlite3.Connection) -> dict:
    """Every non-internal persistent object in the database behind `conn`.

    **Takes an open connection, not a path.** v3's instrument reopened
    `self._path` read-only, which cannot work for `SqliteStore(":memory:")` -- a
    supported constructor today. Reopening `":memory:"` silently yields a
    *different, empty* database, so the instrument reported an empty manifest
    rather than failing (round 2, finding 10). The production check must run on
    the already-open, already-locked connection too, or it inspects a different
    database than the one it is about to stamp."""
    objs = {}
    for typ, name, tbl, sql in conn.execute(_OBJECTS).fetchall():
        entry = {"type": typ, "table": tbl, "sql": _canonical_sql(sql)}
        if typ == "table":
            # Structured column data as well as the DDL text: `table_xinfo`
            # rather than `table_info`, because the latter omits generated
            # columns entirely (0007 §4a-ii, measured). The name is passed as a
            # VALUE to the table-valued pragma -- a table name read out of a
            # foreign file is an identifier chosen by whoever wrote that file.
            entry["columns"] = [
                [r[1], (r[2] or "").upper(), int(r[3]),
                 None if r[4] is None else str(r[4]), int(r[5]), int(r[6])]
                for r in conn.execute(
                    "SELECT * FROM pragma_table_xinfo(?)", (name,))]
        objs[name] = entry
    return objs


def digest(objs: dict) -> str:
    """sha256 over every object except the rebuildable acceleration indexes.

    Exact set equality falls out of this rather than being a separate rule: an
    extra view, an unknown index, a foreign table and a trigger all change the
    digest, so all are refused without being enumerated anywhere."""
    scoped = {k: v for k, v in objs.items() if k not in REBUILDABLE}
    return hashlib.sha256(
        json.dumps(scoped, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def digest_of_path(path: str) -> str:
    conn = sqlite3.connect(path)
    try:
        return digest(manifest(conn))
    finally:
        conn.close()


# --------------------------------------------------------------------------
# historical evidence


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


def releases(write: bool) -> int:
    tags = _tags()
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        head = _probe_at("HEAD", work)
        if head["result"] != "ok":
            print(f"HEAD: {head['result']}", file=sys.stderr)
            return 1
        rows = [_probe_at(t, work) for t in tags]

    matched = sum(1 for r in rows if r["digest"] == head["digest"])
    broken = [r for r in rows if r["result"] != "ok"]
    for r in rows:
        mark = ("identical" if r["digest"] == head["digest"]
                else r["result"] if r["result"] != "ok" else "** DIFFERS **")
        print(f"  {r['tag']:<10} {r['commit'][:12]}  {mark}")
    print(f"\n{matched}/{len(rows)} identical to HEAD · {len(broken)} unbuildable "
          f"· sqlite {sqlite3.sqlite_version}")
    print(f"head digest {head['digest']}")

    if write:
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(json.dumps({
            "head_digest": head["digest"],
            "sqlite_version": sqlite3.sqlite_version,
            "manifest_version": 2,
            "releases": rows,
        }, indent=2) + "\n")
        print(f"wrote {ARTIFACT.relative_to(ROOT)}")
    if broken:
        print("\nAn unbuildable release is NOT evidence of compatibility — it is a "
              "gap in the evidence, and 0007 §4a-iv must say so.", file=sys.stderr)
        return 1
    if matched != len(rows):
        print("\nA differing release means adoption cannot be unconditional.",
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
    if head["digest"] != stored["head_digest"]:
        bad.append(f"HEAD digest changed: {stored['head_digest'][:16]}… → "
                   f"{head['digest'][:16]}… — the schema changed, so SCHEMA_VERSION "
                   f"must too, and every legacy signature must be re-derived")
    for row in stored["releases"]:
        now = fresh_rows.get(row["tag"])
        if now is None:
            bad.append(f"{row['tag']}: recorded but no longer a tag")
        elif now["commit"] != row["commit"]:
            bad.append(f"{row['tag']}: tag moved {row['commit'][:12]} → {now['commit'][:12]}")
        elif now["digest"] != row["digest"]:
            bad.append(f"{row['tag']}: digest changed")
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
    print(f"legacy store evidence current — {len(stored['releases'])} releases, "
          f"all identical to HEAD")
    return 0


# --------------------------------------------------------------------------
# selfcheck


def selfcheck() -> int:
    """Build every counterexample and report whether the manifest sees it.

    **Rows marked R2 are round 2's four false negatives against v3's
    signature.** The two negative rows are the ones to read sceptically -- they
    assert the manifest does NOT fire, and a check that refuses stores which are
    genuinely fine gets bypassed."""
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
        for s in sql:
            c.execute(s)
        c.commit()
        c.close()
        return p

    def variant(old: str, new: str) -> str:
        """One change against the REAL schema text.

        Hand-writing a near-copy is how I first failed to reproduce two of round
        2's counterexamples: the reconstruction differed in some *other* way, so
        it was caught for the wrong reason and I nearly reported a real finding
        as unconfirmed. Deriving from `_SCHEMA` changes exactly one thing."""
        s = _SCHEMA.replace(old, new)
        assert s != _SCHEMA, f"variant did not apply: {old!r}"
        p = tempfile.mktemp(suffix=".db")
        c = sqlite3.connect(p)
        c.executescript(s)
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

    # (name, digest must differ, drift expectation, path)
    # drift is `None` where the digest already differs: the store is refused
    # before anything is rebuilt, so its index state is not a question.
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
        ("R2: index with a host-defined collation", True, None, mutate(
            ["CREATE INDEX ix_custom ON edges(subject COLLATE MYCOLL)"], collation=True)),
        ("wrong same-named UNIQUE index", False, True, mutate(
            ["DROP INDEX ix_edges_subj_rel",
             "CREATE UNIQUE INDEX ix_edges_subj_rel ON edges(user_id, subject)"])),
        ("ANALYZE — must NOT differ", False, False, mutate(["ANALYZE"])),
        ("missing acceleration index — drift only", False, True, mutate(
            ["DROP INDEX ix_edges_subj_rel"])),
    ]

    bad = 0
    print(f"{'case':<46}{'digest':>9}{'drift':>7}   result")
    for name, should_differ, should_drift, path in cases:
        conn = sqlite3.connect(path)
        objs = manifest(conn)
        conn.close()
        differs, drifted = digest(objs) != good, bool(drift(objs))
        ok = differs == should_differ and (should_drift is None or drifted == should_drift)
        bad += not ok
        print(f"  {name:<44}{'differs' if differs else 'same':>9}"
              f"{('n/a' if should_drift is None else 'yes' if drifted else 'no'):>7}"
              f"   {'ok' if ok else '** WRONG **'}")

    # An in-memory store is a supported constructor and must be inspectable
    # through its own connection -- v3's path-reopening instrument reported an
    # empty manifest for it (round 2, finding 10).
    mem = SqliteStore(":memory:")
    mem_objs = manifest(mem._conn)
    mem_ok = digest(mem_objs) == good and not drift(mem_objs)
    print(f"  {'in-memory store, via its own connection':<44}"
          f"{'same' if digest(mem_objs) == good else 'differs':>9}"
          f"{'yes' if drift(mem_objs) else 'no':>7}   {'ok' if mem_ok else '** WRONG **'}")
    bad += not mem_ok

    total = len(cases) + 1
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
