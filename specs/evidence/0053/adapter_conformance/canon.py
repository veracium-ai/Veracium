# Mutation-Matrix: tests/test_0053_adapter_conformance.py::test_the_canonicaliser_catches_each_of_its_mutants
"""specs/0053 §3a: K5's canonical store comparison.

A store is read as LEAVES: every user table by name, rows in `rowid` order, columns in schema order, and a cell holding
JSON text (an object or an array) flattened to its scalar leaves by path. A PLACE is (table, row ordinal, column, path);
a PATTERN is a place without its row, list indices written `*`. Ids live inside JSON as well as in columns (an edge's
`evidence_ref` exists only inside `edges.json`), so the declared lists are lists of patterns, not of columns.

- Generated values at a declared ID pattern are renamed `<id:N>`, N their first appearance in the walk. One map covers
  the store, and a mapped value is replaced wherever it appears: as a whole leaf, or inside a string leaf. A
  reference to a row stays a reference to that row. "Generated" includes values computed from generated ones (a
  request digest over an operation's ids): opaque, compared by their equality structure.
- Values at a declared CLOCK pattern are left out of the digest and compared as an ORDER: red only for a strict
  reversal (two places strictly ordered one way in one store and the other way in the other). A tie on either side is
  tolerated.
- Every other leaf is compared as stored.

`varying` measures the patterns whose raw values differ between two stores of the same shape: the measured lists.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

def _strict_pairs(pairs):
    """0026's evidence-boundary rule: a duplicate JSON key is a refusal, never last-wins."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r}")
        out[k] = v
    return out


_MIN_ID = 8   # a mapped value shorter than this is never substituted inside a string (it would match by accident)


def _flatten(value, path=()):
    if isinstance(value, dict):
        if not value:
            yield path, {}
        for k in value:
            yield from _flatten(value[k], path + (str(k),))
    elif isinstance(value, list):
        if not value:
            yield path, []
        for i, v in enumerate(value):
            yield from _flatten(v, path + (i,))
    else:
        yield path, value


def _cell_leaves(cell):
    if isinstance(cell, str) and cell[:1] in "{[":
        try:
            parsed = json.loads(cell, object_pairs_hook=_strict_pairs)   # a duplicate key: compared as stored
        except ValueError:
            parsed = None
        if isinstance(parsed, (dict, list)):
            yield from _flatten(parsed, ("$",))
            return
    yield (), cell


def leaves(db_path: str) -> list[tuple]:
    """[(table, ordinal, column, path, value)] in the fixed walk order."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        out = []
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for t in tables:
            cols = [r[1] for r in con.execute(f'PRAGMA table_info("{t}")')]
            try:
                rows = con.execute(f'SELECT {", ".join(chr(34) + c + chr(34) for c in cols)} FROM "{t}" '
                                   f'ORDER BY rowid').fetchall()
            except sqlite3.OperationalError as exc:
                raise AssertionError(f"table {t!r} has no rowid order ({exc}): the walk is undefined, so the "
                                     f"canonical form refuses it") from exc
            for n, row in enumerate(rows):
                for c, cell in zip(cols, row):
                    if isinstance(cell, bytes):
                        cell = "bytes:" + cell.hex()
                    for path, v in _cell_leaves(cell):
                        out.append((t, n, c, path, v))
        return out
    finally:
        con.close()


def _scalar(v) -> bool:
    """A value an id map may hold: a string or a number, never a bool (True == 1 would alias an id 1)."""
    return isinstance(v, (str, int, float)) and not isinstance(v, bool)


def pattern(table, column, path) -> tuple:
    return (table, column, tuple("*" if isinstance(k, int) else k for k in path))


def _clock(value, where):
    if not isinstance(value, str):
        raise AssertionError(f"a declared clock at {where} holds {value!r}, not a timestamp")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AssertionError(f"a declared clock at {where} holds {value!r}, not a timestamp") from exc
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class Canon:
    def __init__(self, ids, clocks):
        self.ids = frozenset(ids)
        self.clocks = frozenset(clocks)
        both = self.ids & self.clocks
        if both:
            raise AssertionError(f"patterns declared both id and clock: {sorted(both)}")

    def form(self, db_path: str):
        """(digest, the canonical non-clock leaves, {place: clock value})."""
        ls = leaves(db_path)
        idmap: dict = {}
        for t, n, c, path, v in ls:
            if pattern(t, c, path) in self.ids and _scalar(v):
                idmap.setdefault(v, f"<id:{len(idmap)}>")
        subs = sorted((k for k in idmap if isinstance(k, str) and len(k) >= _MIN_ID), key=len, reverse=True)

        def rename(v):
            if _scalar(v) and v in idmap:
                return idmap[v]
            if isinstance(v, str):
                for k in subs:
                    if k in v:
                        v = v.replace(k, idmap[k])
            return v

        canon, clocks = [], {}
        for t, n, c, path, v in ls:
            place = (t, n, c, path)
            if pattern(t, c, path) in self.clocks:
                clocks[place] = None if v is None else _clock(v, place)
                canon.append((t, n, c, list(path), "<clock>" if v is not None else None))
            else:
                canon.append((t, n, c, list(path), rename(v)))
        digest = hashlib.sha256(json.dumps(canon, sort_keys=True, default=repr).encode()).hexdigest()
        return digest, canon, clocks

    def differences(self, a: str, b: str, *, limit: int = 5) -> list[str]:
        """[] when the two stores match under the canonical comparison; otherwise each difference, named."""
        da, ca, ka = self.form(a)
        db, cb, kb = self.form(b)
        out = []
        if da != db:
            if len(ca) != len(cb):
                out.append(f"leaf count {len(ca)} != {len(cb)}")
            for x, y in zip(ca, cb):
                if x != y:
                    out.append(f"leaf differs: {x!r} != {y!r}")
                    if len(out) >= limit:
                        break
            return out or ["canonical digests differ"]
        out.extend(reversals(ka, kb, limit=limit))
        return out


def reversals(ka: dict, kb: dict, *, limit: int = 5) -> list[str]:
    """Strict reversals between two clock maps over the same places; ties on either side are tolerated."""
    places = [p for p in ka if ka[p] is not None and kb.get(p) is not None]
    out = []
    for i, p in enumerate(places):
        for q in places[i + 1:]:
            sa = (ka[p] > ka[q]) - (ka[p] < ka[q])
            sb = (kb[p] > kb[q]) - (kb[p] < kb[q])
            if sa * sb < 0:
                out.append(f"clock reversal: {p} and {q} are ordered one way in one store and the other way in "
                           f"the other")
                if len(out) >= limit:
                    return out
    return out


def varying(a: str, b: str) -> set:
    """The patterns whose raw values differ between two stores of the same shape (the measured lists' input)."""
    la, lb = leaves(a), leaves(b)
    if [x[:4] for x in la] != [x[:4] for x in lb]:
        raise AssertionError("the two runs left stores of different shapes (rows or JSON paths): a twin pair must "
                             "differ only in values")
    return {pattern(x[0], x[2], x[3]) for x, y in zip(la, lb) if x[4] != y[4]}
