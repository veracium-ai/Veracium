#!/usr/bin/env python3
"""The semantic signature of a SQLite store, and the historical evidence for
adopting one.

`specs/0007` v2 proposed comparing `{table: {(column, declared_type)}}`. The
external reviewer built a database with identical table names, column names and
declared types but **no primary keys and no NOT NULL constraints**, and it
matched. That database is not equivalent: `INSERT OR REPLACE` no longer replaces
by id, duplicate ids become possible, and the per-user write counter loses its
uniqueness. **Names and declared types are not the schema the application relies
on.** This module implements the signature v3 specifies instead.

Two uses, and they are different:

  `--signature <db>`   the signature of one file -- what an implementation of
                       0007 would compare on open.
  `--releases`         build a store with the code of **every released tag** and
                       report whether its signature matches today's. This is the
                       evidence for the adoption premise ("the schema has never
                       changed"), which 0007 v2 asserted from source inspection
                       and the reviewer correctly refused. A fixture generated
                       by the code under test is not historical evidence; a
                       store built by v0.1.0's own code is.

**Three SQLite behaviours this module exists to get right**, each measured
rather than assumed (see 0007 §4a):

  * `name NOT LIKE 'sqlite\\_%'` does **not** escape the underscore without an
    explicit ESCAPE clause, so it fails to exclude `sqlite_stat1`. `GLOB` is
    used instead -- it is case-sensitive and has no escape ambiguity.
  * `PRAGMA table_info` **omits generated columns**. `table_xinfo` reports them
    with a nonzero hidden flag. A foreign file can therefore carry a column
    `table_info` will not show.
  * Table names read out of a foreign file are **untrusted identifiers**. They
    are passed as values to `pragma_table_xinfo(?)`, never interpolated into
    SQL text.

Nothing here is an implementation of 0007. It is the measuring instrument the
spec is written against, and it runs today, against real files.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent

# `type='table'` already excludes indexes -- v2's supporting text cited
# `sqlite_autoindex_*` here, which are indexes and can never appear in this
# result. `sqlite_stat1` is the internal *table* that actually appears, after
# ANALYZE. The reviewer caught the conflation; the query is what matters.
_TABLES = ("SELECT name FROM sqlite_master WHERE type='table' "
           "AND name NOT GLOB 'sqlite_*' ORDER BY name")
_TRIGGERS = ("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger' "
             "AND name NOT GLOB 'sqlite_*' ORDER BY name")


def _table_flags(conn: sqlite3.Connection, table: str) -> list[str]:
    """WITHOUT ROWID / STRICT, read from the stored DDL.

    These change accepted data and write semantics, so they belong in the
    signature. Read from `sqlite_master.sql` because no pragma reports them.
    Normalised to a sorted list of flags rather than compared as text -- the
    whole point of a semantic signature is not to fire on formatting."""
    row = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                       (table,)).fetchone()
    tail = (row[0] or "")[(row[0] or "").rfind(")"):].upper() if row else ""
    return sorted(f for f in ("WITHOUT ROWID", "STRICT") if f in tail)


def _columns(conn: sqlite3.Connection, table: str):
    """`table_xinfo`, not `table_info` -- the latter omits generated columns.

    Passed as a *value* to the table-valued pragma. A table name discovered in
    a foreign file is untrusted input and must never be interpolated."""
    rows = conn.execute(
        "SELECT name, type, \"notnull\", dflt_value, pk, hidden "
        "FROM pragma_table_xinfo(?) ORDER BY name", (table,)).fetchall()
    return sorted(
        (name, (decl or "").upper(), int(notnull), None if dflt is None else str(dflt),
         int(pk), int(hidden))
        for name, decl, notnull, dflt, pk, hidden in rows)


def _unique_indexes(conn: sqlite3.Connection, table: str):
    """Uniqueness-bearing indexes only.

    v2 called every index a performance property. A UNIQUE index decides which
    writes are accepted, so it is semantic. Non-unique acceleration indexes stay
    out -- but see 0007 §4a-iii: they are dropped and recreated on adoption
    rather than trusted, because `CREATE INDEX IF NOT EXISTS` silently keeps a
    same-named index with a different definition (measured)."""
    out = []
    for _seq, name, unique, origin, _partial in conn.execute(
            "SELECT * FROM pragma_index_list(?)", (table,)):
        if not unique:
            continue
        cols = [r[2] for r in conn.execute(
            "SELECT * FROM pragma_index_info(?)", (name,))]
        # `origin` distinguishes a PRIMARY KEY / UNIQUE constraint ('pk'/'u')
        # from a standalone CREATE UNIQUE INDEX ('c'). The name of an
        # auto-index is generated and not stable, so it is deliberately not
        # part of the signature -- the columns and the origin are.
        out.append((origin, tuple(cols)))
    return sorted(out)


def _foreign_keys(conn: sqlite3.Connection, table: str):
    return sorted(
        (r[2], r[3], r[4], r[5], r[6])          # table, from, to, on_update, on_delete
        for r in conn.execute("SELECT * FROM pragma_foreign_key_list(?)", (table,)))


def signature(db_path: str) -> dict:
    """The semantic signature of a store file. Deterministic and JSON-able, so
    two signatures compare with `==` and a difference prints readably."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        tables = [r[0] for r in conn.execute(_TABLES)]
        sig = {"tables": {}, "triggers": []}
        for t in tables:
            sig["tables"][t] = {
                "flags": _table_flags(conn, t),
                "columns": _columns(conn, t),
                "unique": _unique_indexes(conn, t),
                "foreign_keys": _foreign_keys(conn, t),
            }
        # A trigger on a protected table can rewrite or block a write, so a
        # store carrying one is not the shape this build expects. Compared by
        # (name, table) and normalised body.
        sig["triggers"] = sorted(
            (n, tbl, " ".join((s or "").split()))
            for n, tbl, s in conn.execute(_TRIGGERS))
        return json.loads(json.dumps(sig))     # normalise tuples -> lists
    finally:
        conn.close()


def _store_signature_at(ref: str, work: pathlib.Path) -> tuple[str, dict | None, str]:
    """Build a store using the code at `ref` and return its signature.

    The whole point: **the code that creates the file is that release's code**,
    not today's. A fixture generated by the code under test proves only that
    today's schema matches today's schema."""
    wt = work / ref.replace("/", "_")
    r = subprocess.run(["git", "worktree", "add", "-q", "--detach", str(wt), ref],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        return ref, None, f"worktree failed: {r.stderr.strip()[:120]}"
    try:
        db = str(wt / "probe.db")
        code = ("from veracium.store.sqlite import SqliteStore; "
                f"SqliteStore({db!r})")
        r = subprocess.run([sys.executable, "-c", code], cwd=wt,
                           env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"},
                           capture_output=True, text=True)
        if r.returncode:
            return ref, None, f"could not build a store: {r.stderr.strip().splitlines()[-1][:120]}"
        return ref, signature(db), ""
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=ROOT, capture_output=True)


def _tags() -> list[str]:
    out = subprocess.run(["git", "tag"], cwd=ROOT, capture_output=True, text=True).stdout
    def key(t):
        return [int(x) for x in t.lstrip("v").split(".")]
    return sorted((t for t in out.split() if t.startswith("v")), key=key)


def releases() -> int:
    """Every released tag, built by its own code, compared to HEAD."""
    tags = _tags()
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        _, head_sig, err = _store_signature_at("HEAD", work)
        if head_sig is None:
            print(f"HEAD: {err}", file=sys.stderr)
            return 1
        print(f"{len(tags)} released tags · signature compared against HEAD\n")
        mismatched = unbuildable = 0
        for t in tags:
            _, sig, err = _store_signature_at(t, work)
            if sig is None:
                unbuildable += 1
                print(f"  {t:<10} SKIPPED — {err}")
            elif sig == head_sig:
                print(f"  {t:<10} identical")
            else:
                mismatched += 1
                print(f"  {t:<10} ** DIFFERS **")
                for tbl in sorted(set(sig["tables"]) | set(head_sig["tables"])):
                    a, b = sig["tables"].get(tbl), head_sig["tables"].get(tbl)
                    if a != b:
                        print(f"      {tbl}: {a} != {b}")
        print(f"\n{len(tags) - mismatched - unbuildable} identical · "
              f"{mismatched} differing · {unbuildable} unbuildable")
        if mismatched:
            print("\nA differing release means adoption cannot be unconditional: a store "
                  "created by that version is not the shape this build expects.",
                  file=sys.stderr)
            return 1
        if unbuildable:
            print("\nAn unbuildable release is NOT evidence of compatibility — it is a gap "
                  "in the evidence, and 0007 §4a-iv must say so.", file=sys.stderr)
            return 1
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--signature", metavar="DB", help="print one file's signature")
    ap.add_argument("--releases", action="store_true",
                    help="build a store with every released tag's own code and compare")
    a = ap.parse_args()
    if a.releases:
        return releases()
    if a.signature:
        print(json.dumps(signature(a.signature), indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
