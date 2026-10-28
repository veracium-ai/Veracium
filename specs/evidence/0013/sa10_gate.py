#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0013_sa10_gate.py::test_the_gate_passes_the_clean_ladder_on_every_path_and_entry
"""0013 §5f.1 INV-SA10: the commit-time gate over every write the migration ladder issues (0007 v17, I1).

The ladder's connections are reached through a SEAM: `migration.sqlite3` and `release_migration.sqlite3` are both
replaced, for the length of one path, by an object whose `connect` returns a census proxy. Every connection either
module opens is then recorded, including release_migration's own two (`_observe` and `_repair_current`, stage-1 read
item 4(d), decision 5: the seam is extended, not excluded). Each real connection is opened with `cached_statements=0`
(the authorizer fires on PREPARE, so a cached statement would give no callback), with an authorizer and a trace
callback installed.

WHAT IS CHECKED, PER PATH
  1. Attribution is per proxied call. Before each call the census sets the current record and clears nothing else;
     every authorizer and trace callback lands in the record of the call that is running, on the connection it was
     opened for. A callback outside any call, or on another connection, is an ORPHAN, and an orphan is a refusal.
     commit(), rollback(), close() and the context manager's __exit__ are proxied TXN calls with their own records.
  2. Classification (`classify`) is over the call's TEMPLATE, never the traced text, and SQLite decides what is a
     write: the action codes, read through the closed 33-code table `ACTION_CLASS`. A code not in the table refuses.
     Text classification ((a) a frozen ALTERS_* member, (b1) a head table/index constructor, (b2) `DROP INDEX IF
     EXISTS` of a head rebuildable index) is separate from the site declaration (`DDL_SITES`): a schema write must
     satisfy both, and neither implies the other.
  3. A row write (INSERT/UPDATE/DELETE on a table that is not the schema table) maps to EXACTLY ONE 0013-PA1 step.
     A schema write and a row write in one call are both checked (DROP TABLE reports a DELETE on the dropped table).
  4. Schema-table bookkeeping is legitimate only beside a schema-write action in the same call; REINDEX only beside
     CREATE_INDEX of the same name; every write action names the `main` database.
  5. A PRAGMA is the stamp (`user_version` = head) or a read on the frozen vocabulary `PRAGMA_READS`, by name and
     argument shape. Anything else, `writable_schema` included, refuses.
  6. The prefix label (steptable's `_kind`) cross-checks SQLite, and a disagreement refuses, except the one
     legitimate no-op: a (b2) text whose index is already absent reports no action.
  7. The heartbeat: a call that ran must have traced, and reported an authorizer action unless its text is (b2),
     so an instrument removed between calls is a refusal, not a run of "reads". Connection configuration: after
     every call, `getconfig(SQLITE_DBCONFIG_WRITABLE_SCHEMA)` is False and
     `SQLITE_DBCONFIG_DEFENSIVE` is what it was at connect (nothing else can see `setconfig`).
  8. The proxy is a closed ALLOWLIST enforced in `__getattribute__`, with the real connection held in a closure and
     `__slots__ = ()`, so `_real`, `__dict__` and every unlisted name refuse (stage-1 item 4(b), (f), (g)). A refused
     name is RECORDED before it raises, so code that swallows the AttributeError still fails the path. `__class__`
     answers the wrapper's own class (what `type()` gives anyway, and what `isinstance()` falls back to reading). `__enter__`
     and `__iter__` return the wrapper; `execute` returns a cursor wrapper that refuses `.connection` and the
     cursor's own execute*. No value handed back through either wrapper is a real Connection, Cursor or Blob (checked
     by type on every return, so the next method of that shape needs no new rule).
  9. REPLAY EQUIVALENCE (stage-1 item 5). The calls are recorded with their parameters BY VALUE and their outcomes.
     After the path, the recorded connects, attribute sets and calls are replayed on a byte copy of the pre-path
     file, each call asserting the same outcome, and the two closed files are digested by `sa10_digest.py` in a
     fresh `python -I` subprocess, read-only, which asserts it runs the census's SQLite build (version and source
     id, passed as arguments). The digests must be equal and the real file's `integrity_check` must be `ok`. The
     comparator takes no normalisation; there is none to give at this pin.
     THE CLAIM, exactly: no store content changes during a census path except by a recorded call, against any code
     that does not write to the instrument's own objects. Two limits stay limits: influence through a recorded READ
     (read results are not recorded; NEXT-ROUND), and code that forges the record itself.

WHAT IS CHECKED, OVER THE WHOLE GATE
  - every `.execute`/`.executemany`/`.executescript` call site in every function the census saw issue a call is
    observed on at least one path (`open_versioned` excluded, §5f.1: its other sites are the create and adopt flows);
  - every declared DDL site and every frozen pragma read is observed (a stale entry widens the gate silently);
  - every head table constructor is a plain `CREATE TABLE name (...)` with no AS SELECT and no IF NOT EXISTS, and
    every head index constructor has no IF NOT EXISTS, and each table constructor runs on an empty database;
  - C2 shows at least one (b2) carrying a DROP_INDEX action and C3 at least one (b2) no-op.

THE PATHS: every 0013-PA1 fixture through `migrate_store` (C1); the two drifted HEAD stores (C2 `wrong`, C3
`missing`) through `migrate_store`; and through `run_release_migration`, every base-(head−1) fixture (the only base
the release orchestrator mints for) and both drifted HEAD stores (its `_repair_current`).

    $PY specs/evidence/0013/sa10_gate.py [--json OUT]
"""
from __future__ import annotations

import ast
import collections
import contextlib
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from typing import Optional

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DIGEST_SCRIPT = HERE / "sa10_digest.py"

# ---- the closed action table (§5f.1), by NAME: the result codes SQLITE_ERROR..SQLITE_WARNING share the values 1-28,
# and the module does not expose code 0 (SQLITE_COPY, obsolete), so a table built from the module's constants by value
# would be neither closed nor complete. A code outside this table is refused by the default branch, never by a row.
ACTION_CLASS = {
    "SQLITE_CREATE_TABLE": "schema", "SQLITE_CREATE_INDEX": "schema", "SQLITE_DROP_TABLE": "schema",
    "SQLITE_DROP_INDEX": "schema", "SQLITE_ALTER_TABLE": "schema",
    "SQLITE_INSERT": "row", "SQLITE_UPDATE": "row", "SQLITE_DELETE": "row",
    "SQLITE_REINDEX": "reindex",
    "SQLITE_PRAGMA": "pragma",
    "SQLITE_TRANSACTION": "txn", "SQLITE_SAVEPOINT": "txn",
    "SQLITE_READ": "read", "SQLITE_SELECT": "read", "SQLITE_FUNCTION": "read", "SQLITE_RECURSIVE": "read",
    "SQLITE_ATTACH": "refused", "SQLITE_DETACH": "refused", "SQLITE_ANALYZE": "refused",
    "SQLITE_CREATE_VTABLE": "refused", "SQLITE_DROP_VTABLE": "refused",
    "SQLITE_CREATE_TRIGGER": "refused", "SQLITE_DROP_TRIGGER": "refused",
    "SQLITE_CREATE_VIEW": "refused", "SQLITE_DROP_VIEW": "refused",
    "SQLITE_CREATE_TEMP_INDEX": "refused", "SQLITE_CREATE_TEMP_TABLE": "refused",
    "SQLITE_CREATE_TEMP_TRIGGER": "refused", "SQLITE_CREATE_TEMP_VIEW": "refused",
    "SQLITE_DROP_TEMP_INDEX": "refused", "SQLITE_DROP_TEMP_TABLE": "refused",
    "SQLITE_DROP_TEMP_TRIGGER": "refused", "SQLITE_DROP_TEMP_VIEW": "refused",
}
CODE_CLASS = {getattr(sqlite3, n): c for n, c in ACTION_CLASS.items()}
CODE_NAME = {getattr(sqlite3, n): n for n in ACTION_CLASS}
# the schema table, under every name the authorizer reports for it (measured at 3.45.1: `sqlite_schema` is reported
# as `sqlite_master`, `sqlite_temp_schema` as `sqlite_temp_master`; the other two are listed so nothing depends on it)
SCHEMA_TABLE_NAMES = frozenset({"sqlite_master", "sqlite_schema", "sqlite_temp_master", "sqlite_temp_schema"})

# ---- where the census expects DDL: a site declaration, by function. It never makes a statement class (b): a schema
# write needs BOTH a text class and a declared site (§5f.1, "What a site declaration still does").
DDL_SITES = frozenset({("veracium/store/migration.py", "_apply_forward"),
                       ("veracium/store/schema_version.py", "_repair_drift")})

# ---- the pragma read vocabulary, frozen by name and argument shape, enumerated from the ladder at this pin (every
# entry must be observed, so the list cannot outgrow the ladder silently). NONE: no argument; IDENT: one identifier.
NONE, IDENT = "none", "ident"
PRAGMA_READS = {"user_version": NONE, "table_xinfo": IDENT}
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# ---- the proxies' allowlist (stage-1 item 4(b), (f), (g)); the dir() census in the tests fails on a public name of
# sqlite3.Connection or sqlite3.Cursor that is in neither the allowed nor the refused set.
CONN_METHODS = frozenset({"execute", "executemany", "commit", "rollback", "close"})
CONN_READ_ATTRS = frozenset({"isolation_level", "row_factory", "text_factory", "in_transaction", "total_changes"})
CONN_SET_ATTRS = frozenset({"isolation_level", "row_factory", "text_factory"})
SET_VALUES = {"isolation_level": (None, "", "DEFERRED", "IMMEDIATE", "EXCLUSIVE"),
              "row_factory": (None, sqlite3.Row), "text_factory": (str, bytes)}
"""0007 round 3 (research's stage-1 read of SA-R3-01, in the closure's letter: "replay must not execute opaque
caller-supplied connection behavior"): a settable attribute takes a value from a CLOSED set. `isolation_level` is an
exact str or None; a factory is compared BY IDENTITY, so a Python function is never a row or text factory and replay
never re-runs one. The ladder sets only `isolation_level` (schema_version.open_versioned: None, then its prior value)."""
CONNECT_KW = frozenset({"timeout"})
"""SA-R3-01 (round 3): the census's connect admits the store path and a numeric timeout and nothing else. A `factory`
(keyword or positional), any positional extra and every other keyword are executable or connection-shaping caller
input, refused BEFORE `sqlite3.connect` runs: no constructor executes outside the authorizer and the trace, and replay
never re-invokes one. The seamed callers pass `path` (migration.py) or `path, timeout=` (release_migration.py)."""
SEAM_ATTRS = frozenset({"Error", "DatabaseError", "OperationalError"})
"""SA-R3-01, research's stage-1 read: what the module seam exposes besides `connect`, which the census runs. It was the
whole module, so `sqlite3.Connection(path)` wrote with no census at all. These three are every `sqlite3.<name>` the
seamed modules read at run time (their `sqlite3.Connection` uses are annotations under `from __future__ import
annotations`, never evaluated); any other name is refused and recorded, Connection included."""


def connect_args_problem(args, kw) -> str | None:
    """SA-R3-01: None, or what in a connect call is outside CONNECT_KW. Used by the census AND by replay."""
    if args:
        return f"{len(args)} positional argument(s) after the path (a factory, among others, can be positional)"
    extra = sorted(set(kw) - CONNECT_KW)
    if extra:
        return f"the keyword argument(s) {extra} (only {sorted(CONNECT_KW)} is admitted)"
    if "timeout" in kw and type(kw["timeout"]) not in (int, float):
        return f"a timeout of type {type(kw['timeout']).__name__}"
    return None


def set_value_ok(name, value) -> bool:
    """A value from SET_VALUES[name]: by value for an exact str (or None), by identity for anything else."""
    if type(value) is str:
        return value in SET_VALUES.get(name, ())
    return any(value is v for v in SET_VALUES.get(name, ()))
CONN_REFUSED = frozenset({
    "executescript", "cursor", "blobopen", "backup", "deserialize", "serialize", "setconfig", "getconfig",
    "setlimit", "getlimit", "set_authorizer", "set_progress_handler", "set_trace_callback", "create_aggregate",
    "create_collation", "create_function", "create_window_function", "load_extension", "enable_load_extension",
    "interrupt", "iterdump", "autocommit", "DataError", "DatabaseError", "Error", "IntegrityError", "InterfaceError",
    "InternalError", "NotSupportedError", "OperationalError", "ProgrammingError", "Warning"})
CURSOR_METHODS = frozenset({"fetchone", "fetchall", "fetchmany", "close"})
CURSOR_READ_ATTRS = frozenset({"rowcount", "lastrowid", "description"})
CURSOR_REFUSED = frozenset({"connection", "execute", "executemany", "executescript", "arraysize", "row_factory",
                            "setinputsizes", "setoutputsize"})
_FORBIDDEN_RETURN = tuple(t for t in (sqlite3.Connection, sqlite3.Cursor, getattr(sqlite3, "Blob", None)) if t)
_DBCONFIG = getattr(sqlite3, "SQLITE_DBCONFIG_WRITABLE_SCHEMA", None), getattr(sqlite3, "SQLITE_DBCONFIG_DEFENSIVE",
                                                                                None)
_SCALARS = (int, float, str, bytes, type(None))


class ChannelRefused(AttributeError):
    """A name the census proxy does not expose. Recorded before it is raised: code that swallows it still fails."""


# ---- the PA1 campaign, for its fixtures, its step matchers and steptable's prefix label --------------------------------
def _pa1():
    name = "veracium_pa1_campaign"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, HERE / "pa1_campaign.py")
        m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return sys.modules[name]


def _src_prefix() -> str:
    import veracium
    return os.path.realpath(os.path.dirname(veracium.__file__)) + os.sep


class Site(tuple):
    """(file relative to the package's parent, function, the function's first line, the calling line)."""
    __slots__ = ()

    @property
    def by(self) -> str:                      # the 0013-PA1 step matchers' form: file:function:line
        return f"{self[0]}:{self[1]}:{self[3]}"


def issuer() -> Optional[Site]:
    prefix = _src_prefix()
    f = sys._getframe(1)
    while f is not None:
        fn = os.path.realpath(f.f_code.co_filename)
        if fn.startswith(prefix):
            rel = "veracium/" + fn[len(prefix):].replace(os.sep, "/")
            return Site((rel, f.f_code.co_name, f.f_code.co_firstlineno, f.f_lineno))
        f = f.f_back
    return None


# ---- the record --------------------------------------------------------------------------------------------------------
class Call:
    """One proxied call: execute/executemany (a template and its parameters, by value) or a TXN call."""

    def __init__(self, cid, how, sql=None, params=None, site=None):
        self.kind, self.cid, self.how, self.sql, self.params, self.site = "call", cid, how, sql, params, site
        self.acts, self.traces, self.problems = [], [], []
        self.act_phase = []                       # per act: the traces seen before it (0: inside the first prepare)
        self.bookkeeping = []                     # (v37) callback sequences attributed as bookkeeping, named
        self.outcome = None
        self.ok = None                            # __exit__ only: whether it was given no exception


class Event:
    def __init__(self, kind, cid, **kw):
        self.kind, self.cid = kind, cid
        self.__dict__.update(kw)


def _snapshot(params, problems):
    """Parameters by value, at call time: a later mutation of the caller's object cannot reach the replay."""
    if isinstance(params, dict):
        out = dict(params)
        vals = out.values()
    elif isinstance(params, (list, tuple)):
        out = tuple(params)
        vals = out
    else:
        problems.append(f"parameters of type {type(params).__name__} are not snapshotted by value")
        return params
    for v in vals:
        if not isinstance(v, _SCALARS):
            problems.append(f"a parameter of type {type(v).__name__} is not snapshotted by value")
    return out


class Census:
    def __init__(self, store: str, proxy_factory=None):
        self.store = os.path.realpath(store)
        self.events = []                  # Event("connect"/"set") and Call, in the order they happened
        self.cur = None                   # the Call whose callbacks are arriving
        self.orphans = []
        self.refusals = []                # (what, by)
        self.problems = []
        self.reals = {}                   # cid -> real connection
        self.closed = set()
        self.defensive = {}
        self.proxy_factory = proxy_factory or connection_proxy
        self.vtab_used = collections.defaultdict(set)   # (v37) cid -> eponymous pragma modules used on that connection

    # -- callbacks
    def _auth(self, cid):
        def auth(code, a1, a2, db, trig):
            cur = self.cur
            if cur is None or cur.cid != cid:
                self.orphans.append(("auth", cid, (code, a1, a2, db, trig)))
            else:
                cur.acts.append((code, a1, a2, db, trig))
                cur.act_phase.append(len(cur.traces))
            return sqlite3.SQLITE_OK
        return auth

    def _trace(self, cid):
        def trace(text):
            cur = self.cur
            if cur is None or cur.cid != cid:
                self.orphans.append(("trace", cid, text))
            else:
                cur.traces.append(text)
        return trace

    def refuse(self, what: str, site=None):
        site = site or issuer()
        self.refusals.append((what, site.by if site else "?"))
        return ChannelRefused(f"the INV-SA10 census proxy does not expose {what} (0013 §5f.1)")

    # -- the seam
    def connect(self, database, args, kw):
        cid = len(self.reals) + len([e for e in self.events if e.kind == "connect-failed"])
        site = issuer()
        bad = connect_args_problem(args, kw)
        if bad:                                   # SA-R3-01: before sqlite3.connect, so no factory ever runs
            raise self.refuse(f"connect with {bad}", site)
        if not isinstance(database, (str, os.PathLike)) or os.path.realpath(database) != self.store:
            self.problems.append(f"connect to {database!r} from {site.by if site else '?'}: not the store")
        kw2 = dict(kw)
        kw2["cached_statements"] = 0
        try:
            real = sqlite3.connect(database, *args, **kw2)
        except Exception as exc:  # noqa: BLE001 - recorded, then re-raised as itself
            self.events.append(Event("connect-failed", cid, args=args, kw=dict(kw), outcome=type(exc).__name__))
            raise
        real.set_authorizer(self._auth(cid))
        real.set_trace_callback(self._trace(cid))
        self.reals[cid] = real
        if hasattr(real, "getconfig"):
            self.defensive[cid] = real.getconfig(_DBCONFIG[1])
        self.events.append(Event("connect", cid, args=args, kw=dict(kw), site=site))
        return self.proxy_factory(real, self, cid)

    def call(self, cid, how, sql, params, run):
        site = issuer()
        rec = Call(cid, how, sql, params, site)
        prev, self.cur = self.cur, rec
        try:
            r = run()
            rec.outcome = ("ok",)
        except BaseException as exc:
            rec.outcome = ("raise", type(exc).__name__)
            raise
        finally:
            self.cur = prev
            self._attribute_declare_vtab(cid, rec)
            self.events.append(rec)
            if how == "close":
                self.closed.add(cid)
            self._guards(cid, rec)
        return r

    def _attribute_declare_vtab(self, cid, rec):
        """0013 v37 §5f.1: on a pre-3.41 build, a connection's FIRST use of a table-valued pragma asks the authorizer
        about sqlite3_declare_vtab's nested, never-executed `UPDATE sqlite_master`. Those six callbacks are attributed
        as bookkeeping, and removed from the call's actions, ONLY when all three hold: (1) exactly DECLARE_VTAB_SEQ,
        immediately after the call's SELECT; (2) in the PREPARE (before the call's first trace) of a call that
        references an eponymous pragma module not yet used on this connection; (3) THIS build's probe reproduces it
        with nothing changed. Anything else stays a write. At most one sequence per first-used module."""
        if rec.how not in ("execute", "executemany"):
            return
        mods = {m.lower() for m in _EPONYMOUS.findall(rec.sql or "")}
        first = mods - self.vtab_used[cid]
        self.vtab_used[cid] |= mods
        if not first or not declare_vtab_probe():
            return
        n = len(DECLARE_VTAB_SEQ)
        for _ in range(len(first)):
            for i, a in enumerate(rec.acts):
                if (a[0] == sqlite3.SQLITE_SELECT and tuple(rec.acts[i + 1:i + 1 + n]) == DECLARE_VTAB_SEQ
                        and all(p == 0 for p in rec.act_phase[i + 1:i + 1 + n])):
                    del rec.acts[i + 1:i + 1 + n]
                    del rec.act_phase[i + 1:i + 1 + n]
                    rec.bookkeeping.append("declare_vtab")
                    break
            else:
                return

    def _guards(self, cid, rec):
        real = self.reals[cid]
        if cid in self.closed or not hasattr(real, "getconfig"):
            return
        try:
            ws, df = real.getconfig(_DBCONFIG[0]), real.getconfig(_DBCONFIG[1])
        except sqlite3.ProgrammingError:
            return
        if ws:
            rec.problems.append("SQLITE_DBCONFIG_WRITABLE_SCHEMA is on after the call")
        if df != self.defensive.get(cid):
            rec.problems.append(f"SQLITE_DBCONFIG_DEFENSIVE changed during the call ({self.defensive.get(cid)} -> {df})")

    def attribute(self, rec):
        census = self

        class _Attr:
            def __enter__(self):
                self.prev, census.cur = census.cur, rec

            def __exit__(self, *a):
                census.cur = self.prev
        return _Attr()

    def set_attr(self, cid, name, value):
        self.events.append(Event("set", cid, name=name, value=value))

    def close_all(self):
        """A connection the code left open is closed here, as its collection would close it, and recorded so the
        replay closes it at the same point."""
        for cid, real in self.reals.items():
            if cid not in self.closed:
                self.call(cid, "gc-close", None, None, real.close)

    def checked(self, value, where):
        if isinstance(value, _FORBIDDEN_RETURN):
            raise self.refuse(f"{where} returning a real {type(value).__name__}")
        if isinstance(value, list):
            for v in value:
                if isinstance(v, _FORBIDDEN_RETURN):
                    raise self.refuse(f"{where} returning a real {type(v).__name__}")
        return value


def connection_proxy(real, census: Census, cid: int):
    """The gate's connection wrapper: a closed allowlist in `__getattribute__`, the real connection in this closure."""
    def execute(sql, parameters=(), /):
        probs = []
        p = _snapshot(parameters, probs)
        census.problems.extend(probs)
        cur = census.call(cid, "execute", sql, p, lambda: real.execute(sql, p))
        return cursor_proxy(cur, census, census.events[-1])

    def executemany(sql, seq, /):
        probs = []
        ps = [_snapshot(p, probs) for p in seq]
        census.problems.extend(probs)
        cur = census.call(cid, "executemany", sql, ps, lambda: real.executemany(sql, ps))
        return cursor_proxy(cur, census, census.events[-1])

    methods = {"execute": execute, "executemany": executemany,
               "commit": lambda: census.call(cid, "commit", None, None, real.commit),
               "rollback": lambda: census.call(cid, "rollback", None, None, real.rollback),
               "close": lambda: census.call(cid, "close", None, None, real.close)}

    class ConnectionProxy:
        __slots__ = ()

        def __getattribute__(self, n):
            f = methods.get(n)
            if f is not None:
                return f
            if n in CONN_READ_ATTRS:
                return census.checked(getattr(real, n), f"connection.{n}")
            if n == "__class__":                # what type() returns anyway; isinstance() falls back to reading it
                return ConnectionProxy
            raise census.refuse(f"connection.{n}")

        def __setattr__(self, n, v):
            if n not in CONN_SET_ATTRS:
                raise census.refuse(f"setting connection.{n}")
            if not set_value_ok(n, v):
                raise census.refuse(f"setting connection.{n} to {v!r} (outside {SET_VALUES[n]!r})")
            census.set_attr(cid, n, v)
            setattr(real, n, v)

        def __delattr__(self, n):
            raise census.refuse(f"deleting connection.{n}")

        def __enter__(self):
            return self

        def __exit__(self, t, v, tb):
            r = census.call(cid, "__exit__", None, None, lambda: real.__exit__(t, v, tb))
            census.events[-1].ok = t is None
            return r

        def __repr__(self):
            return f"<INV-SA10 census connection {cid}>"

    return ConnectionProxy()


def cursor_proxy(cur, census: Census, rec: Call):
    """The cursor wrapper: the read side only; `__iter__` returns the wrapper, never the real cursor's iterator."""
    def fetch(name):
        meth = getattr(cur, name)

        def f(*a):
            with census.attribute(rec):
                r = meth(*a)
            return census.checked(r, f"cursor.{name}")
        return f

    class CursorProxy:
        __slots__ = ()

        def __getattribute__(self, n):
            if n in ("fetchone", "fetchall", "fetchmany"):
                return fetch(n)
            if n == "close":
                return cur.close
            if n in CURSOR_READ_ATTRS:
                return census.checked(getattr(cur, n), f"cursor.{n}")
            if n == "__class__":
                return CursorProxy
            raise census.refuse(f"cursor.{n}")

        def __setattr__(self, n, v):
            raise census.refuse(f"setting cursor.{n}")

        def __delattr__(self, n):
            raise census.refuse(f"deleting cursor.{n}")

        def __iter__(self):
            return self

        def __next__(self):
            with census.attribute(rec):
                row = next(cur)
            return census.checked(row, "cursor.__next__")

        def __repr__(self):
            return "<INV-SA10 census cursor>"

    return CursorProxy()


class _Seam:
    """What `migration.sqlite3` and `release_migration.sqlite3` are, for one path: `connect`, which the census runs,
    and SEAM_ATTRS. Every other name is refused and recorded (SA-R3-01: the seam forwarded the whole module, so a
    direct `sqlite3.Connection(path)` wrote with no census)."""

    def __init__(self, census: Census):
        self._census = census

    def __getattr__(self, n):
        if n in SEAM_ATTRS:
            return getattr(sqlite3, n)
        raise self._census.refuse(f"sqlite3.{n} through the module seam")

    def connect(self, database, *args, **kw):
        return self._census.connect(database, args, kw)


# ---- classification -----------------------------------------------------------------------------------------------
def text_classes():
    """The text classes from the tree's own constants: (a) ALTERS_* members, (b1) head table/index constructors,
    (b2) `DROP INDEX IF EXISTS <head rebuildable index>`."""
    from veracium.store import schema_version as sv
    head = sv.SCHEMAS[sv.SCHEMA_VERSION]
    alters = {s for n in dir(sv) if n.startswith("ALTERS_") and isinstance(getattr(sv, n), tuple)
              for s in getattr(sv, n)}
    b1 = {o.ddl for o in head if o.key[0] in ("table", "index")}
    b2 = {f"DROP INDEX IF EXISTS {o.key[1]}" for o in head if o.key[0] == "index" and o.policy == sv.REBUILDABLE}
    return alters, b1, b2


def _text_class(sql, classes):
    alters, b1, b2 = classes
    return "a" if sql in alters else "b1" if sql in b1 else "b2" if sql in b2 else None


def _write_db(code, a1, a2, db):
    """The database a write action names: ALTER_TABLE reports it first, the others fourth."""
    return a1 if code == sqlite3.SQLITE_ALTER_TABLE else db


# ---- (v37) the pre-3.41 declare_vtab sequence ----------------------------------------------------------------------
DECLARE_VTAB_SEQ = tuple((sqlite3.SQLITE_UPDATE, "sqlite_master", col, "main", None)
                         for col in ("type", "name", "tbl_name", "rootpage", "sql")) + (
    (sqlite3.SQLITE_READ, "sqlite_master", "ROWID", "main", None),)
"""Exactly the six callbacks research measured on 3.40.1 (0013 v37 §5f.1, research 46869de1): UPDATE main.sqlite_master
for five columns in that order, each with no trigger or view argument, then READ main.sqlite_master.ROWID."""
_EPONYMOUS = re.compile(r"(?<![A-Za-z0-9_])pragma_([A-Za-z_]+)\s*\(")
_DECLARE_VTAB_PROBE = None


def declare_vtab_probe_result(acts, before, after) -> bool:
    """Condition (3)'s decision, pure: the probe's recorded callbacks hold DECLARE_VTAB_SEQ immediately after a SELECT,
    AND schema_version, data_version, total_changes() and the sqlite_master rows are unchanged."""
    n = len(DECLARE_VTAB_SEQ)
    reproduces = any(a[0] == sqlite3.SQLITE_SELECT and tuple(acts[i + 1:i + 1 + n]) == DECLARE_VTAB_SEQ
                     for i, a in enumerate(acts))
    return reproduces and before == after


def _measure_declare_vtab() -> bool:
    """THIS build's probe, on a scratch database: a connection's first table-valued pragma read, recorded."""
    with tempfile.TemporaryDirectory() as d:
        c = sqlite3.connect(os.path.join(d, "probe.db"))
        try:
            c.execute("CREATE TABLE t(a)")
            c.commit()

            def state():
                return (c.execute("PRAGMA schema_version").fetchone()[0], c.execute("PRAGMA data_version").fetchone()[0],
                        c.total_changes, c.execute("SELECT type, name, tbl_name, rootpage, sql FROM sqlite_master")
                        .fetchall())
            before, acts = state(), []
            c.set_authorizer(lambda *a: acts.append(tuple(a)) or sqlite3.SQLITE_OK)
            try:
                c.execute("SELECT * FROM pragma_table_xinfo('t')").fetchall()
            finally:
                c.set_authorizer(lambda *_a: sqlite3.SQLITE_OK)
            return declare_vtab_probe_result(acts, before, state())
        finally:
            c.close()


def declare_vtab_probe() -> bool:
    """Condition (3), measured once per process, at the gate's first need (run_gate also asks at its start)."""
    global _DECLARE_VTAB_PROBE
    if _DECLARE_VTAB_PROBE is None:
        _DECLARE_VTAB_PROBE = _measure_declare_vtab()
    return _DECLARE_VTAB_PROBE


def classify(rec: Call, classes, steps, label, head: int) -> tuple:
    """(class, problems) for one recorded call. `steps` maps step name -> predicate over {"kind", "sql", "by"};
    `label` is steptable's prefix label."""
    problems = list(rec.problems)
    where = f"{rec.how} {rec.sql!r:.90} at {rec.site.by if rec.site else '?'}"
    if rec.how not in ("execute", "executemany"):
        other = [a for a in rec.acts if CODE_CLASS.get(a[0]) != "txn"]
        if other:
            problems.append(f"{where}: a TXN call reported non-transaction actions {other[:3]}")
        return "txn", problems
    by_class = collections.defaultdict(list)
    for a in rec.acts:
        cls = CODE_CLASS.get(a[0], "unknown")
        by_class[cls].append(a)
    for a in by_class["unknown"]:
        problems.append(f"{where}: action code {a[0]} is not in the closed table")
    for a in by_class["refused"]:
        problems.append(f"{where}: refused action {CODE_NAME[a[0]]} {a[1]!r}")
    schema = by_class["schema"]
    rows = [a for a in by_class["row"] if a[1] not in SCHEMA_TABLE_NAMES]
    book = [a for a in by_class["row"] if a[1] in SCHEMA_TABLE_NAMES]
    for a in schema + by_class["row"] + by_class["reindex"]:
        if _write_db(*a[:4]) != "main":
            problems.append(f"{where}: {CODE_NAME[a[0]]} names database {_write_db(*a[:4])!r}, not main")
    tc = _text_class(rec.sql, classes)
    cls = None
    if schema:
        if tc is None:
            problems.append(f"{where}: a schema write that is not class (a) or (b) by its text")
            cls = "OUTSIDE"
        else:
            cls = tc
        if rec.site is None or (rec.site[0], rec.site[1]) not in DDL_SITES:
            problems.append(f"{where}: a schema write from a site not declared to issue DDL")
        if tc in ("b1", "b2") and rows:
            problems.append(f"{where}: a class-({tc}) statement with row effects {sorted({a[1] for a in rows})}")
    if book and not schema:
        problems.append(f"{where}: a direct write to the schema table ({sorted({CODE_NAME[a[0]] for a in book})})")
    made = {a[1] for a in schema if a[0] == sqlite3.SQLITE_CREATE_INDEX}
    for a in by_class["reindex"]:
        if a[1] not in made:
            problems.append(f"{where}: REINDEX {a[1]!r} without CREATE_INDEX of the same name in the call")
    # the instrument's heartbeat: a statement that ran traced (every one does, the (b2) no-op included, measured) and
    # was authorized (every one is, except that no-op). A call that ran with neither ran with the instrument removed:
    # `set_authorizer(None)` before a write issued through the proxy's own execute leaves a RECORDED call, which
    # replay reproduces and the action table would read as a read.
    if rec.outcome == ("ok",):
        if not rec.traces:
            problems.append(f"{where}: the statement ran and traced nothing (the trace callback is not installed)")
        if not rec.acts and tc != "b2":
            problems.append(f"{where}: the statement ran and reported no authorizer action (the authorizer is not "
                            f"installed)")
    lab = label(rec.sql)
    if rows:
        w = {"kind": lab, "sql": rec.sql, "by": rec.site.by if rec.site else "?"}
        hits = [n for n, pred in steps.items() if pred(w)]
        if len(hits) != 1:
            problems.append(f"{where}: a row write on {sorted({a[1] for a in rows})} maps to {len(hits)} steps "
                            f"{hits}, not exactly one")
        cls = cls or "row"
    stamp = False
    for a in by_class["pragma"]:
        name, arg, db = (a[1] or "").lower(), a[2], a[3]
        if db not in (None, "main"):
            problems.append(f"{where}: PRAGMA {name} on database {db!r}")
        if name == "user_version" and arg is not None:
            stamp = True
            if arg != str(head):
                problems.append(f"{where}: the stamp writes {arg!r}, not the head {head}")
            continue
        shape = NONE if arg is None else IDENT if _IDENT_RE.fullmatch(arg) else None
        if PRAGMA_READS.get(name) != shape or shape is None:
            problems.append(f"{where}: PRAGMA {name}({arg!r}) is not on the read vocabulary")
    if stamp:
        if len(by_class["pragma"]) != 1:
            problems.append(f"{where}: the stamp shares its call with another pragma")
        cls = cls or "stamp"
    only_txn = rec.acts and all(CODE_CLASS.get(a[0]) == "txn" for a in rec.acts)
    cls = cls or ("txn" if only_txn else "pragma-read" if by_class["pragma"] else "read")
    want = {"a": "DDL", "b1": "DDL", "b2": "DDL", "OUTSIDE": "DDL", "row": "DML", "stamp": "STAMP",
            "txn": "TXN"}.get(cls, "READ")
    if lab != want:
        if lab == "DDL" and cls == "read" and not rec.acts and tc == "b2":
            cls = "b2-noop"                     # the one legitimate no-op: `IF EXISTS` of an index already absent
        else:
            problems.append(f"{where}: the prefix label says {lab}, SQLite's actions say {want}")
    return cls, problems


# ---- head constructors (§5f.1 (b1)): plain CREATE, no AS SELECT, no IF NOT EXISTS ---------------------------------------
_TABLE_CTOR = re.compile(r"CREATE TABLE ([A-Za-z_][A-Za-z0-9_]*)\s*\(.*\)\s*", re.S)
_INDEX_CTOR = re.compile(r"CREATE (?:UNIQUE )?INDEX ([A-Za-z_][A-Za-z0-9_]*) ON ([A-Za-z_][A-Za-z0-9_]*)\s*\(.*?\)"
                         r"(?:\s+WHERE\s.+)?\s*", re.S)        # a partial index ends in WHERE (two at schema 16)


def constructor_problems(objects=None) -> list:
    """Every head table constructor is a plain `CREATE TABLE <its name> (...)` and every index constructor a plain
    `CREATE [UNIQUE] INDEX <its name> ON <table>(...) [WHERE ...]`; neither carries IF NOT EXISTS; no table
    constructor is AS SELECT; and each table constructor runs on an empty database. (A check that a constructor
    reads no other table was written and withdrawn: every AS SELECT spelling already fails the anchored text, and
    SQLite refuses a subquery in CHECK, DEFAULT and generated columns, so no input could tell it from the text rule.)"""
    from veracium.store import schema_version as sv
    objs = list(objects if objects is not None else sv.SCHEMAS[sv.SCHEMA_VERSION])
    out = []
    for o in objs:
        kind, name = o.key[0], o.key[1]
        if kind not in ("table", "index"):
            continue
        if re.search(r"\bIF\s+NOT\s+EXISTS\b", o.ddl, re.I):
            out.append(f"{kind} {name}: the constructor carries IF NOT EXISTS")
        m = (_TABLE_CTOR if kind == "table" else _INDEX_CTOR).fullmatch(o.ddl)
        if m is None or m.group(1) != name:
            out.append(f"{kind} {name}: the constructor is not a plain CREATE {kind.upper()} {name} (...)")
        if kind == "table" and re.search(r"\bAS\s+SELECT\b", o.ddl, re.I):
            out.append(f"table {name}: the constructor is CREATE TABLE ... AS SELECT")
    with contextlib.closing(sqlite3.connect(":memory:")) as c:
        for o in sorted((o for o in objs if o.key[0] == "table"), key=lambda o: o.key):
            try:
                c.execute(o.ddl)
            except sqlite3.Error as exc:
                out.append(f"table {o.key[1]}: the constructor does not run on an empty database ({exc})")
    return out


# ---- replay and the comparator -------------------------------------------------------------------------------------
class _Replayed(Exception):
    """Stands in for the exception the real __exit__ was given: only its presence decides commit or rollback."""


def replay(events, copy_path: str) -> list:
    """Re-run the recorded connects, sets and calls on `copy_path`; every call must have the recorded outcome."""
    conns, problems = {}, []
    for ev in events:
        if ev.kind == "connect-failed":
            continue
        if ev.kind == "connect":
            kw = {k: v for k, v in ev.kw.items() if k != "cached_statements"}
            bad = connect_args_problem(ev.args, kw)
            if bad:                               # SA-R3-01: replay never runs recorded caller behaviour
                return problems + [f"replay refuses connection {ev.cid}'s recorded connect: {bad}"]
            conns[ev.cid] = sqlite3.connect(copy_path, **kw)
            continue
        c = conns[ev.cid]
        if ev.kind == "set":
            if ev.name not in CONN_SET_ATTRS or not set_value_ok(ev.name, ev.value):
                return problems + [f"replay refuses connection {ev.cid}'s recorded set of {ev.name} to {ev.value!r}"]
            setattr(c, ev.name, ev.value)
            continue
        try:
            if ev.how == "execute":
                c.execute(ev.sql, ev.params).close()
            elif ev.how == "executemany":
                c.executemany(ev.sql, ev.params).close()
            elif ev.how in ("commit", "rollback", "close"):
                getattr(c, ev.how)()
            elif ev.how == "gc-close":
                c.close()
            elif ev.how == "__exit__":
                c.__exit__(*((None, None, None) if ev.ok else (_Replayed, _Replayed(), None)))
            else:
                problems.append(f"replay: no rule for a recorded {ev.how!r}")
                continue
            out = ("ok",)
        except Exception as exc:  # noqa: BLE001 - the outcome is compared
            out = ("raise", type(exc).__name__)
        if out != ev.outcome:
            site = ev.site.by if ev.site else "?"
            problems.append(f"replay: {ev.how} {ev.sql!r:.80} at {site} gave {out}, the census run gave {ev.outcome}")
    for c in conns.values():
        c.close()
    return problems


def build_identity() -> tuple:
    with sqlite3.connect(":memory:") as c:
        return tuple(c.execute("SELECT sqlite_version(), sqlite_source_id()").fetchone())


def digest(path: str, build=None) -> dict:
    """sa10_digest.py on `path`, in a fresh isolated interpreter that cannot reach this process's patches."""
    version, source = build or build_identity()
    p = subprocess.run([sys.executable, "-I", str(DIGEST_SCRIPT), str(path), version, source],
                       capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        return {"refused": f"exit {p.returncode}: {(p.stdout + p.stderr).strip()[:400]}"}
    return json.loads(p.stdout, object_pairs_hook=_strict_pairs)


def _strict_pairs(pairs):
    """0026's evidence-boundary rule: a duplicate key in the comparator's output is a refusal, never last-wins."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r} in the comparator's output")
        out[k] = v
    return out


def compare(real: dict, rep: dict) -> list:
    out = []
    for name, d in (("the census file", real), ("the replay", rep)):
        if "refused" in d:
            out.append(f"the comparator refused {name}: {d['refused']}")
    if out:
        return out
    if real["integrity"] != ["ok"]:
        out.append(f"integrity_check on the census file: {real['integrity'][:3]}")
    for k in sorted(set(real["sections"]) | set(rep["sections"])):
        if real["sections"].get(k) != rep["sections"].get(k):
            out.append(f"replay equivalence: {k} differs (census {str(real['sections'].get(k))[:40]}, "
                       f"replay {str(rep['sections'].get(k))[:40]})")
    return out


# ---- the paths --------------------------------------------------------------------------------------------------------
def _clear(path):
    import veracium.store.release_migration as rm
    for suffix in ("", "-journal", "-wal", "-shm", rm._AUDIT_SUFFIX):
        try:
            os.remove(path + suffix)
        except FileNotFoundError:
            pass


def drifted(path: str, mode: str) -> None:
    """C2 (`wrong`: ONE rebuildable index recreated under its own name on another column, so its repair DROP reports
    DROP_INDEX) and C3 (`missing`: every rebuildable index dropped, so every repair DROP is a no-op): PA1 path v1#0
    migrated to HEAD outside the census, then drifted. The same fixtures as the C2/C3 census at 58dd7f6."""
    import veracium.store.migration as mig
    from veracium.store import schema_version as sv
    pa1 = _pa1()
    _clear(path)
    pa1.fresh_fixture(path, "v1#0")
    mig.migrate_store(path)
    rebuild = sorted(o for o in sv.SCHEMAS[sv.SCHEMA_VERSION] if o.key[0] == "index" and o.policy == sv.REBUILDABLE)
    c = sqlite3.connect(path)
    try:
        if mode == "wrong":
            o = rebuild[0]
            table = c.execute("SELECT tbl_name FROM sqlite_master WHERE type='index' AND name=?",
                              (o.key[1],)).fetchone()[0]
            cols = {r[2] for r in c.execute(f"PRAGMA index_info({o.key[1]})")}
            other = next(r[1] for r in c.execute(f"PRAGMA table_info({table})") if r[1] not in cols)
            c.execute(f"DROP INDEX {o.key[1]}")
            c.execute(f"CREATE INDEX {o.key[1]} ON {table}({other})")
        elif mode == "missing":
            for o in rebuild:
                c.execute(f"DROP INDEX {o.key[1]}")
        else:
            raise ValueError(mode)
        c.commit()
    finally:
        c.close()


def gate_paths():
    """[(label, entry, builder)]: builder(path) writes the fixture; entry is "migrate_store" or "release"."""
    from veracium.store import schema_version as sv
    pa1 = _pa1()
    labels = [lab for lab, _b, _a, _st in pa1.lib()["paths"]()]
    out = [(lab, "migrate_store", lambda p, lab=lab: (_clear(p), pa1.fresh_fixture(p, lab))) for lab in labels]
    for mode, c in (("wrong", "C2"), ("missing", "C3")):
        out.append((f"{c}-{mode}", "migrate_store", lambda p, mode=mode: drifted(p, mode)))
    for lab, b, _a, stamped in pa1.lib()["paths"]():
        if b == sv.SCHEMA_VERSION - 1:
            out.append((lab, "release", lambda p, lab=lab: (_clear(p), pa1.fresh_fixture(p, lab))))
    for mode, c in (("wrong", "C2"), ("missing", "C3")):
        out.append((f"{c}-{mode}", "release", lambda p, mode=mode: drifted(p, mode)))
    return out


def run_entry(store: str, entry: str, census: Census):
    import veracium.store.migration as mig
    import veracium.store.release_migration as rm
    seam = _Seam(census)
    saved = mig.sqlite3, rm.sqlite3
    mig.sqlite3 = rm.sqlite3 = seam
    try:
        if entry == "migrate_store":
            result = mig.migrate_store(store)
        else:
            result = rm.run_release_migration(
                store, host_attestation=rm.MigrationAttestation(quiesced=True, backup_ref="sa10-gate"))
        exc = None
    except Exception as e:  # noqa: BLE001 - the outcome is the measurement
        result, exc = None, e
    finally:
        mig.sqlite3, rm.sqlite3 = saved
        census.close_all()
    return result, exc


def outcome_of(result, exc) -> str:
    if exc is not None:
        return f"raised {type(exc).__name__}: {str(exc)[:120]}"
    return str(getattr(result, "outcome", result))


def run_path(label, entry, builder, work, *, proxy_factory=None, inject=None, build=None) -> dict:
    """One gate path. `inject`, if given, is called as inject(store) inside the seam's lifetime by the caller's own
    monkeypatching (the tests' controls); the gate itself never calls it."""
    from veracium.store import schema_version as sv
    pa1 = _pa1()
    os.makedirs(work, exist_ok=True)
    store = os.path.join(work, "store.db")
    pre = os.path.join(work, "pre.db")
    rep = os.path.join(work, "replay.db")
    builder(store)
    for suffix in ("-journal", "-wal"):
        assert not os.path.exists(store + suffix), f"{label}: the fixture left {suffix} behind"
    shutil.copyfile(store, pre)
    census = Census(store, proxy_factory)
    result, exc = run_entry(store, entry, census)
    classes, steps, label_fn = text_classes(), pa1._steps(), pa1.lib()["_kind"]
    calls = [e for e in census.events if e.kind == "call"]
    tally = collections.Counter()
    problems = list(census.problems)
    b2_with_drop = 0
    for rec in calls:
        cls, probs = classify(rec, classes, steps, label_fn, sv.SCHEMA_VERSION)
        rec.cls = cls
        tally[cls] += 1
        problems += probs
        if cls == "b2" and any(a[0] == sqlite3.SQLITE_DROP_INDEX for a in rec.acts):
            b2_with_drop += 1
    problems += [f"orphan {k} on connection {cid}: {str(x)[:100]}" for k, cid, x in census.orphans]
    problems += [f"refused {what} at {by}" for what, by in census.refusals]
    _clear_side(rep)
    shutil.copyfile(pre, rep)
    problems += replay(census.events, rep)
    problems += compare(digest(store, build), digest(rep, build))
    return {"path": label, "entry": entry, "outcome": outcome_of(result, exc), "classes": dict(sorted(tally.items())),
            "b2_with_drop_index": b2_with_drop, "problems": problems, "calls": calls}


def _clear_side(path):
    for suffix in ("", "-journal", "-wal", "-shm"):
        try:
            os.remove(path + suffix)
        except FileNotFoundError:
            pass


# ---- site coverage (§5f.1 v0.11.1) -------------------------------------------------------------------------------------
SITE_EXCLUDED = frozenset({("veracium/store/schema_version.py", "open_versioned")})
_EXEC_NAMES = frozenset({"execute", "executemany", "executescript"})


def _function_sites(src_text: str, name: str, first: int) -> list:
    """[(lineno, end_lineno)] of every .execute*/executescript call in the function `name` whose code starts at
    `first` (decorators included), nested functions' own bodies excluded."""
    tree = ast.parse(src_text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            if start != first:
                continue
            out, stack = [], list(ast.iter_child_nodes(node))
            while stack:
                n = stack.pop()
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                    continue
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in _EXEC_NAMES:
                    out.append((n.lineno, n.end_lineno))
                stack.extend(ast.iter_child_nodes(n))
            return sorted(out)
    raise LookupError(f"no function {name} starting at line {first}")


def site_coverage(all_calls) -> dict:
    """Over every path: the functions the census saw issue a call, and in each, the call sites never observed."""
    import veracium
    base = pathlib.Path(os.path.realpath(os.path.dirname(veracium.__file__))).parent
    seen = collections.defaultdict(set)
    for rec in all_calls:
        if rec.site is not None and rec.how in ("execute", "executemany"):
            seen[(rec.site[0], rec.site[1], rec.site[2])].add(rec.site[3])
    unobserved, functions = [], 0
    for (rel, name, first), lines in sorted(seen.items()):
        if (rel, name) in SITE_EXCLUDED:
            continue
        functions += 1
        for lo, hi in _function_sites((base / rel).read_text(encoding="utf-8"), name, first):
            if not any(lo <= ln <= hi for ln in lines):
                unobserved.append(f"{rel}:{name}:{lo}")
    return {"functions": functions, "sites": sum(len(_function_sites((base / r).read_text(encoding="utf-8"), n, f))
                                                for (r, n, f) in seen if (r, n) not in SITE_EXCLUDED),
            "unobserved": unobserved}


# ---- the gate ----------------------------------------------------------------------------------------------------------
def run_gate(work: str, paths=None) -> dict:
    build = build_identity()
    declare_vtab_probe()                      # (v37) condition (3), measured when the gate starts
    results = []
    for label, entry, builder in (paths if paths is not None else gate_paths()):
        d = tempfile.mkdtemp(dir=work)
        results.append(run_path(label, entry, builder, d, build=build))
    all_calls = [c for r in results for c in r["calls"]]
    problems = [f"{r['entry']} {r['path']}: {p}" for r in results for p in r["problems"]]
    cov = site_coverage(all_calls)
    problems += [f"site never observed on any path: {s}" for s in cov["unobserved"]]
    ddl_seen = {(c.site[0], c.site[1]) for c in all_calls
                if c.site and getattr(c, "cls", None) in ("a", "b1", "b2", "b2-noop", "OUTSIDE")}
    problems += [f"declared DDL site never observed issuing DDL: {s}" for s in sorted(DDL_SITES - ddl_seen)]
    pragma_seen = {(a[1] or "").lower() for c in all_calls for a in c.acts
                   if a[0] == sqlite3.SQLITE_PRAGMA and not ((a[1] or "").lower() == "user_version" and a[2])}
    problems += [f"pragma read on the frozen vocabulary never observed: {n}"
                 for n in sorted(set(PRAGMA_READS) - pragma_seen)]
    problems += [f"head constructor: {p}" for p in constructor_problems()]
    by_label = {(r["entry"], r["path"]): r for r in results}
    for entry in ("migrate_store", "release"):
        c2, c3 = by_label.get((entry, "C2-wrong")), by_label.get((entry, "C3-missing"))
        if c2 is None or c2["b2_with_drop_index"] < 1:      # a narrowed path set refuses loudly, never passes
            problems.append(f"{entry} C2: no (b2) statement carrying a DROP_INDEX action was observed")
        if c3 is None or c3["classes"].get("b2-noop", 0) < 1:
            problems.append(f"{entry} C3: no (b2) no-op was observed")
    tally = collections.Counter()
    for r in results:
        tally.update(r["classes"])
    return {"build": list(build), "paths": [{k: v for k, v in r.items() if k != "calls"} for r in results],
            "classes": dict(sorted(tally.items())), "site_coverage": cov, "problems": problems}


def main(argv) -> int:
    out = argv[argv.index("--json") + 1] if "--json" in argv else None
    work = tempfile.mkdtemp(prefix="sa10-gate-")
    try:
        report = run_gate(work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if out:
        pathlib.Path(out).write_text(json.dumps(report, indent=2, default=str) + "\n")
    summary = {"paths": len(report["paths"]), "classes": report["classes"],
               "site_coverage": {k: v for k, v in report["site_coverage"].items() if k != "unobserved"},
               "problems": len(report["problems"])}
    print(json.dumps(summary))
    for p in report["problems"][:50]:
        print("PROBLEM", p)
    return 1 if report["problems"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
