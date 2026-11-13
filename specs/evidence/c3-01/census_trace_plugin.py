"""A pytest plugin for I6d's dynamic writers' census (specs/0003 §4c-ii v18.9): every SqliteStore connection's SQL is
traced, each statement attributed to the innermost src/veracium function that issued it, and every `_bump` call is
recorded by its caller. At session end it writes one JSON record (path in $C301_CENSUS_OUT) that
tests/test_c3_01_writers_census.py judges: the committed transactions, with the tables each wrote and its writers, and
the bump call sites reached.

It runs over EXISTING test modules that already build the states each writer needs (a restoration, an undo, an
outcome import, a consolidation, an expiry), so the census's reach is measured, not staged by hand
(research's stage 2 on 35610a8a, B1: a single scenario reached 6 of 15 bump sites).

    PYTHONPATH=specs/evidence/c3-01 C301_CENSUS_OUT=<file> pytest -p census_trace_plugin <test modules>
"""
from __future__ import annotations

import json
import os
import re
import sys

_WRITE = re.compile(r'\b(?:INSERT(?:\s+OR\s+\w+)?\s+INTO|UPDATE|DELETE\s+FROM|REPLACE\s+INTO)\s+"?([A-Za-z_][A-Za-z0-9_]*)',
                    re.I)
_bufs: dict = {}
_reached: set = set()


def _src_frame(f):
    """The innermost frame inside src/veracium (never this plugin, never a test)."""
    while f is not None:
        path = f.f_code.co_filename
        i = path.find("/src/veracium/")
        if i >= 0:
            return path[i + len("/src/veracium/"):], f.f_code.co_name
        f = f.f_back
    return None


def pytest_configure(config):
    from veracium.store import sqlite as S
    orig_init, orig_bump = S.SqliteStore.__init__, S.SqliteStore._bump

    def init(self, *a, **k):
        orig_init(self, *a, **k)
        buf = _bufs.setdefault(id(self._conn), [])

        def trace(sql):
            buf.append((sql, _src_frame(sys._getframe(1))))
        self._conn.set_trace_callback(trace)

    def bump(self, user_id):
        site = _src_frame(sys._getframe(1))
        if site:
            _reached.add(site)
        return orig_bump(self, user_id)

    S.SqliteStore.__init__ = init
    S.SqliteStore._bump = bump


def _segments(stmts):
    out, cur = [], None
    for sql, fn in stmts:
        head = sql.lstrip().upper()
        if head.startswith("BEGIN"):
            cur = []
        elif head.startswith(("COMMIT", "END")) and cur is not None:
            out.append((cur, "COMMIT"))
            cur = None
        elif head.startswith("ROLLBACK") and cur is not None:
            out.append((cur, "ROLLBACK"))
            cur = None
        elif cur is not None:
            cur.append((sql, fn))
        elif head.startswith(("INSERT", "UPDATE", "DELETE", "REPLACE")):
            out.append(([(sql, fn)], "AUTOCOMMIT"))
    return out


def pytest_sessionfinish(session, exitstatus):
    txns = []
    for stmts in _bufs.values():
        for seg, end in _segments(stmts):
            if end == "ROLLBACK":
                continue
            writes = sorted({(t, f"{fn[0]}:{fn[1]}" if fn else "") for sql, fn in seg for t in _WRITE.findall(sql)})
            if not writes:
                continue
            deletes_counter = any(re.search(r"DELETE\s+FROM\s+write_counter", sql, re.I) for sql, _ in seg)
            txns.append({"end": end, "writes": writes, "deletes_counter": deletes_counter})
    out = {"exitstatus": int(exitstatus), "transactions": txns,
           "reached": sorted(f"{f}:{n}" for f, n in _reached)}
    with open(os.environ["C301_CENSUS_OUT"], "w") as fh:
        json.dump(out, fh)
