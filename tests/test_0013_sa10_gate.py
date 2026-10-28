"""INV-SA10's commit-time gate (0013 §5f.1; 0007 v17 I1): specs/evidence/0013/sa10_gate.py and its comparator
specs/evidence/0013/sa10_digest.py.

The clean ladder passes on every path and both entries (C1–C3, and the release orchestrator's own connections); the
action table is a closed partition of the 33 codes; each classification rule refuses its case and admits its
legitimate one; the proxy is a closed allowlist that records every refusal, in both directions against dir(); the
statement cache is off; and replay equivalence catches each unrecorded route (stage-1 read item 5's six controls),
each run against the SUPERSEDED proxy shape (every unknown name forwarded to the real connection, as the census
instruments at 58dd7f6 did), so the allowlist is not what catches them, and again against the gate's own proxy.
§5f.1's negative cells N1–N12 and stage-1's N13–N15 run END TO END (0007 I2): each statement is issued by the ladder's
own connection inside `_apply_forward`, after the stamp postcondition, and the gate refuses it for its named reason;
the clean control admits a nested table-valued pragma's two traces; a write two steps claim is refused. Each cell's
demonstration against the gate mutant §5f.1 names beside it is specs/evidence/0013/sa10_mutants.py's table.
"""
from __future__ import annotations

import ast
import importlib.util
import os
import pathlib
import sqlite3
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "specs" / "evidence" / "0013"


def _load(stem):
    name = f"veracium_{stem}"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, EVIDENCE / f"{stem}.py")
        m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return sys.modules[name]


g = _load("sa10_gate")


# ---- the clean ladder ---------------------------------------------------------------------------------------------
def test_the_gate_passes_the_clean_ladder_on_every_path_and_entry(tmp_path):
    from veracium.store import schema_version as sv
    gate = _load("sa10_gate")
    report = gate.run_gate(str(tmp_path))
    assert report["problems"] == [], "\n".join(report["problems"][:40])
    paths = {(p["entry"], p["path"]): p for p in report["paths"]}
    labels = [lab for lab, *_ in gate._pa1().lib()["paths"]()]
    base15 = [lab for lab, b, *_ in gate._pa1().lib()["paths"]() if b == sv.SCHEMA_VERSION - 1]
    assert len(labels) >= 48 and base15
    for lab in labels:                                                  # C1: every PA1 fixture migrates
        assert paths[("migrate_store", lab)]["outcome"] == "migrated", paths[("migrate_store", lab)]
    for lab in base15:                                                  # the orchestrator mints only for head-1
        assert paths[("release", lab)]["outcome"] == "migrated", paths[("release", lab)]
    for entry in ("migrate_store", "release"):
        c2, c3 = paths[(entry, "C2-wrong")], paths[(entry, "C3-missing")]
        assert c2["outcome"] == c3["outcome"] == "current"
        assert c2["b2_with_drop_index"] >= 1 and c2["classes"].get("b1", 0) >= 1          # C2: a real (b2)
        assert c3["classes"].get("b2-noop", 0) >= 1 and c3["b2_with_drop_index"] == 0     # C3: (b2) no-ops only
    for p in report["paths"]:                                           # every migrating path stamps exactly once
        assert p["classes"].get("stamp", 0) == (1 if p["outcome"] == "migrated" else 0), p
        assert p["classes"].get("OUTSIDE", 0) == 0
    # the seam reaches release_migration's own connections, and site coverage counts its functions
    cov = report["site_coverage"]
    assert cov["unobserved"] == [] and cov["functions"] >= 16, cov
    assert report["classes"]["row"] > 0 and report["classes"]["a"] > 0 and report["classes"]["b1"] > 0
    print({"paths": len(report["paths"]), "classes": report["classes"], "site_coverage": cov})


def test_release_migration_opens_its_connections_through_the_seam(tmp_path):
    """Stage-1 item 4(d), decision 5: `_observe` and `_repair_current` open their own connections, and the seam is
    EXTENDED to them (not excluded). Each is recorded with its site, and `_repair_current`'s connection carries the
    repair's (b2) and (b1) statements."""
    from veracium.store import schema_version as sv
    base15 = next(lab for lab, b, *_ in g._pa1().lib()["paths"]() if b == sv.SCHEMA_VERSION - 1)
    builders = {lab: b for lab, e, b in g.gate_paths() if e == "release"}
    r = g.run_path(base15, "release", builders[base15], str(tmp_path / "a"))
    assert r["problems"] == [] and r["outcome"] == "migrated", r["problems"]
    fns = {c.site[1] for c in r["calls"] if c.site and c.site[0] == "veracium/store/release_migration.py"}
    assert "_observe" in fns, fns
    rc = g.run_path("C2-wrong", "release", builders["C2-wrong"], str(tmp_path / "b"))
    assert rc["problems"] == [] and rc["outcome"] == "current", rc["problems"]
    repair = [c for c in rc["calls"] if getattr(c, "cls", None) in ("b1", "b2")]
    assert repair and {c.site[1] for c in repair} == {"_repair_drift"}
    # the repair ran on the connection _repair_current opened, not on one migrate_store opened
    census_connects = [c for c in rc["calls"] if c.cls in ("b1", "b2")]
    assert len({c.cid for c in census_connects}) == 1


# ---- the closed action table --------------------------------------------------------------------------------------
def test_the_action_table_is_a_closed_partition_of_the_33_codes_and_any_other_code_refuses():
    assert len(g.ACTION_CLASS) == 33
    values = [getattr(sqlite3, n) for n in g.ACTION_CLASS]
    assert sorted(values) == list(range(1, 34))                     # distinct, and exactly 1..33 (0 is not exposed)
    import collections
    assert collections.Counter(g.ACTION_CLASS.values()) == {"schema": 5, "row": 3, "reindex": 1, "pragma": 1,
                                                             "txn": 2, "read": 4, "refused": 17}
    for code in (0, 34, 99):
        cls, probs = _classify(sql="SELECT 1", acts=[(code, None, None, None, None), _SEL])
        assert any(f"action code {code} is not in the closed table" in p for p in probs), probs


# ---- classification cells -------------------------------------------------------------------------------------------
_SEL = (sqlite3.SQLITE_SELECT, None, None, None, None)
_DECLARED = ("veracium/store/migration.py", "_apply_forward", 1, 2)
_UNDECLARED = ("veracium/store/migration.py", "_older", 1, 2)


def _classify(sql, acts, site=_DECLARED, how="execute", outcome=("ok",), traces=("t",)):
    from veracium.store import schema_version as sv
    pa1 = g._pa1()
    rec = g.Call(0, how, sql, (), g.Site(site) if site else None)
    rec.acts, rec.traces, rec.outcome = list(acts), list(traces), outcome
    return g.classify(rec, g.text_classes(), pa1._steps(), pa1.lib()["_kind"], sv.SCHEMA_VERSION)


def _head(kind):
    from veracium.store import schema_version as sv
    return next(o for o in sorted(sv.SCHEMAS[sv.SCHEMA_VERSION]) if o.key[0] == kind)


def _cases():
    from veracium.store import schema_version as sv
    head = sv.SCHEMA_VERSION
    A = sqlite3
    t, i = _head("table"), _head("index")
    reb = next(o for o in sorted(sv.SCHEMAS[head]) if o.key[0] == "index" and o.policy == sv.REBUILDABLE)
    b2 = f"DROP INDEX IF EXISTS {reb.key[1]}"
    mk_t = [(A.SQLITE_INSERT, "sqlite_master", None, "main", None), (A.SQLITE_CREATE_TABLE, t.key[1], None, "main", None)]
    mk_i = [(A.SQLITE_INSERT, "sqlite_master", None, "main", None),
            (A.SQLITE_CREATE_INDEX, i.key[1], "x", "main", None), (A.SQLITE_REINDEX, i.key[1], None, "main", None)]
    drop_t = [(A.SQLITE_DELETE, "sqlite_master", None, "main", None), (A.SQLITE_DROP_TABLE, "episodes", None, "main", None),
              (A.SQLITE_DELETE, "episodes", None, "main", None)]
    chains = ("veracium/store/migration.py", "_migrate_outcome_chains", 1, 2)
    return [
        # (id, sql, acts, site, expected class, expected problem substring or None)
        ("b1 table at a declared site", t.ddl, mk_t, _DECLARED, "b1", None),
        ("b1 index with its REINDEX", i.ddl, mk_i, _DECLARED, "b1", None),
        ("b1 text at an UNDECLARED site", t.ddl, mk_t, _UNDECLARED, "b1", "not declared to issue DDL"),
        ("N1: DROP TABLE at a declared site", "DROP TABLE episodes", drop_t, _DECLARED, "OUTSIDE",
         "not class (a) or (b) by its text"),
        ("N1: DROP TABLE is a row write as well", "DROP TABLE episodes", drop_t, _DECLARED, "OUTSIDE",
         "maps to 0 steps"),
        ("b1 text with row effects", t.ddl, mk_t + [(A.SQLITE_DELETE, "episodes", None, "main", None)], _DECLARED,
         "b1", "with row effects"),
        ("N12: a schema-table write with no schema action", "DELETE FROM sqlite_master WHERE name='episodes'",
         [(A.SQLITE_DELETE, "sqlite_master", None, "main", None)], _DECLARED, "read", "direct write to the schema table"),
        ("REINDEX without its CREATE_INDEX", "REINDEX x", [(A.SQLITE_REINDEX, "x", None, "main", None)], _DECLARED,
         "read", "without CREATE_INDEX"),
        ("N9: PRAGMA writable_schema", "PRAGMA writable_schema=ON",
         [(A.SQLITE_PRAGMA, "writable_schema", "ON", None, None)], _DECLARED, "pragma-read", "not on the read vocabulary"),
        ("a read pragma, by name and shape", "SELECT * FROM pragma_table_xinfo(?)",
         [_SEL, (A.SQLITE_PRAGMA, "table_xinfo", "episodes", None, None)], _DECLARED, "pragma-read", None),
        ("a read pragma with another argument shape", "PRAGMA table_xinfo('a b')",
         [(A.SQLITE_PRAGMA, "table_xinfo", "a b", None, None)], _DECLARED, "pragma-read", "not on the read vocabulary"),
        ("a pragma off the vocabulary", "PRAGMA journal_mode",
         [(A.SQLITE_PRAGMA, "journal_mode", None, None, None)], _DECLARED, "pragma-read", "not on the read vocabulary"),
        ("the stamp at head", f"PRAGMA user_version = {head}", [(A.SQLITE_PRAGMA, "user_version", str(head), None, None)],
         _DECLARED, "stamp", None),
        ("a stamp below head", f"PRAGMA user_version = {head - 1}",
         [(A.SQLITE_PRAGMA, "user_version", str(head - 1), None, None)], _DECLARED, "stamp", "not the head"),
        ("a pragma on another database", "PRAGMA temp.user_version",
         [(A.SQLITE_PRAGMA, "user_version", None, "temp", None)], _DECLARED, "pragma-read", "on database 'temp'"),
        ("ATTACH is refused outright", "ATTACH ':memory:' AS x", [(A.SQLITE_ATTACH, ":memory:", None, None, None)],
         _DECLARED, "read", "refused action SQLITE_ATTACH"),
        ("a temp trigger is refused outright", "CREATE TEMP TRIGGER x ...",
         [(A.SQLITE_CREATE_TEMP_TRIGGER, "x", "episodes", "temp", None)], _DECLARED, "read",
         "refused action SQLITE_CREATE_TEMP_TRIGGER"),
        ("a write naming the temp database", "INSERT INTO t VALUES(1)", [(A.SQLITE_INSERT, "t", None, "temp", None)],
         chains, "row", "names database 'temp'"),
        ("a row write mapped to exactly one step", "UPDATE episodes SET json = ? WHERE id = ?",
         [(A.SQLITE_UPDATE, "episodes", "json", "main", None)], chains, "row", None),
        ("a row write mapped to no step", "UPDATE episodes SET json = ? WHERE id = ?",
         [(A.SQLITE_UPDATE, "episodes", "json", "main", None)], _UNDECLARED, "row", "maps to 0 steps"),
        ("N7: a CTE-prefixed DELETE (the label says READ)", "WITH doomed AS (SELECT 1) DELETE FROM episodes",
         [(A.SQLITE_DELETE, "episodes", None, "main", None)], chains, "row", "the prefix label says READ"),
        ("N6: a comment-prefixed DROP", "/* repair */ DROP TABLE episodes", drop_t, _DECLARED, "OUTSIDE",
         "the prefix label says READ"),
        ("C3: a (b2) text with no action is the one legitimate no-op", b2, [], _DECLARED, "b2-noop", None),
        ("another DDL text with no action refuses", "DROP INDEX IF EXISTS ix_not_rebuildable", [], _DECLARED, "read",
         "the prefix label says DDL"),
        ("a TXN call with a write action", None, [(A.SQLITE_INSERT, "episodes", None, "main", None)], _DECLARED, "txn",
         "non-transaction actions"),
        # I1: the vocabulary is frozen by name AND argument shape: a listed name with another WELL-FORMED shape (no
        # argument where the list says one identifier) refuses, so the shape is not implied by the name
        ("a listed pragma with another well-formed argument shape", "PRAGMA table_xinfo",
         [(A.SQLITE_PRAGMA, "table_xinfo", None, None, None)], _DECLARED, "pragma-read",
         "PRAGMA table_xinfo(None) is not on the read vocabulary"),
        # rule 4's pairing is by NAME: a REINDEX of one index beside the CREATE_INDEX of another is not legitimate
        # (research's stage-1 read of the round-3 drafts: "pair REINDEX by any CREATE_INDEX" had no cell to fail)
        ("a REINDEX of another index beside a CREATE_INDEX", i.ddl,
         mk_i[:2] + [(A.SQLITE_REINDEX, i.key[1] + "_other", None, "main", None)], _DECLARED, "b1",
         "without CREATE_INDEX of the same name"),
    ]


@pytest.mark.parametrize("case", range(27))
def test_each_classification_rule_refuses_its_case_and_admits_its_legitimate_one(case):
    cases = _cases()
    assert len(cases) == 27
    name, sql, acts, site, want_cls, want = cases[case]
    how = "commit" if sql is None else "execute"
    cls, probs = _classify(sql=sql, acts=acts, site=site, how=how, traces=() if how == "commit" else ("t",))
    assert cls == want_cls, (name, cls, probs)
    if want is None:
        assert probs == [], (name, probs)
    else:
        assert any(want in p for p in probs), (name, probs)


def test_the_heartbeat_refuses_a_call_that_ran_with_the_instrument_removed():
    t = _head("table")
    cls, probs = _classify(sql="WITH doomed AS (SELECT 1) DELETE FROM episodes", acts=[], traces=())
    assert cls == "read"                                    # the action table alone would read it as a read
    assert any("traced nothing" in p for p in probs) and any("no authorizer action" in p for p in probs), probs
    # a statement that did not run owes no heartbeat; one that ran owes both
    assert _classify(sql="SELECT x", acts=[], traces=(), outcome=("raise", "OperationalError"))[1] == []
    assert _classify(sql=t.ddl, acts=[], traces=())[1] != []


# ---- the proxy: a closed allowlist ----------------------------------------------------------------------------------
def _census(tmp_path, factory=None):
    store = str(tmp_path / "s.db")
    with sqlite3.connect(store) as c:
        c.execute("CREATE TABLE episodes(id INTEGER PRIMARY KEY, json TEXT)")
        c.execute("INSERT INTO episodes(json) VALUES('{\"a\": 1}')")
    c.close()
    census = g.Census(store, factory)
    return census, census.connect(store, (), {})


_REFUSED_ROUTES = {
    # N13–N15's channels (stage-1 item 4), the routes back to the real connection (4(f), (g)), and the rest by name
    "connection.blobopen": lambda conn: conn.blobopen("episodes", "json", 1),
    "connection.backup": lambda conn: sqlite3.connect(":memory:").backup(conn.backup),
    "connection.set_authorizer": lambda conn: conn.set_authorizer(None),
    "connection.set_trace_callback": lambda conn: conn.set_trace_callback(None),
    "connection.executescript": lambda conn: conn.executescript("SELECT 1; DROP TABLE episodes"),
    "connection.cursor": lambda conn: conn.cursor(),
    "connection.setconfig": lambda conn: conn.setconfig(1, True),
    "connection.deserialize": lambda conn: conn.deserialize(b""),
    "connection._real": lambda conn: conn._real,
    "connection.__dict__": lambda conn: conn.__dict__,
    "setting connection.autocommit": lambda conn: setattr(conn, "autocommit", True),
    "setting connection._real": lambda conn: setattr(conn, "_real", None),
    "deleting connection.isolation_level": lambda conn: delattr(conn, "isolation_level"),
    "cursor.connection": lambda conn: conn.execute("SELECT 1").connection,
    "cursor.connection (through iter)": lambda conn: iter(conn.execute("SELECT 1")).connection,
    "cursor.execute": lambda conn: conn.execute("SELECT 1").execute("DELETE FROM episodes"),
    "cursor.executescript": lambda conn: conn.execute("SELECT 1").executescript("DELETE FROM episodes"),
    "setting cursor.row_factory": lambda conn: setattr(conn.execute("SELECT 1"), "row_factory", None),
    "connection.blobopen (through with)": lambda conn: _with_blobopen(conn),
}


def _with_blobopen(conn):
    with conn as c:
        assert c is conn                                    # __enter__ returns the WRAPPER, never the real connection
        return c.blobopen("episodes", "json", 1)


@pytest.mark.parametrize("route", sorted(_REFUSED_ROUTES))
def test_the_proxy_refuses_each_route_and_records_the_refusal(tmp_path, route):
    census, conn = _census(tmp_path)
    before = len(census.refusals)
    try:
        _REFUSED_ROUTES[route](conn)
        raised = None
    except Exception as exc:  # noqa: BLE001 - any other outcome is the observation, asserted below
        raised = exc
    assert isinstance(raised, g.ChannelRefused), f"{route} was not refused by the census proxy: {raised!r}"
    assert len(census.refusals) == before + 1, census.refusals
    want = route.split(" (")[0]
    assert census.refusals[-1][0] == want, census.refusals[-1]


def test_a_swallowed_refusal_is_still_recorded(tmp_path):
    census, conn = _census(tmp_path)
    assert getattr(conn, "blobopen", None) is None
    assert not hasattr(conn, "_real")
    assert [r[0] for r in census.refusals] == ["connection.blobopen", "connection._real"]


class _Constructed(sqlite3.Connection):
    """A connection factory whose constructor would run outside the census (SA-R3-01): it records that it ran."""
    ran = []

    def __init__(self, *a, **k):
        _Constructed.ran.append(1)
        super().__init__(*a, **k)


_CONNECT_FORMS = {   # SA-R3-01 (round 3): (args, kw) that connect must refuse BEFORE sqlite3.connect runs
    "factory-keyword": ((), {"factory": _Constructed}),          # the reviewer's route
    "factory-positional": ((5.0, 0, None, True, _Constructed), {}),
    "another-keyword": ((), {"detect_types": sqlite3.PARSE_DECLTYPES}),
    "a-str-timeout": ((), {"timeout": "5"}),
}


@pytest.mark.parametrize("form", sorted(_CONNECT_FORMS))
def test_connect_refuses_a_factory_or_any_extra_argument_before_anything_runs(tmp_path, form):
    """SA-R3-01: `Census.connect` forwarded the caller's arguments, `factory` included, to the real sqlite3.connect,
    so a factory's constructor ran before the authorizer and the trace were installed, and replay re-invoked it. Now
    anything but the path and a numeric timeout is refused and recorded, and no constructor runs. Control: the
    seamed callers' own forms (path; path and timeout) still connect."""
    census, conn = _census(tmp_path)
    conn.close()
    _Constructed.ran.clear()
    args, kw = _CONNECT_FORMS[form]
    with pytest.raises(g.ChannelRefused):
        census.connect(census.store, args, kw)
    assert _Constructed.ran == [] and len(census.reals) == 1, (_Constructed.ran, census.reals)
    assert census.refusals[-1][0].startswith("connect with "), census.refusals
    census.connect(census.store, (), {"timeout": 5.0}).close()
    census.connect(census.store, (), {}).close()
    assert len(census.reals) == 3 and len(census.refusals) == 1


def _runtime_sqlite3_names(path):
    """Every `sqlite3.<name>` a module READS at run time: annotations (unevaluated under `from __future__ import
    annotations`) excluded."""
    tree = ast.parse(pathlib.Path(path).read_text())
    skip = set()
    for node in ast.walk(tree):
        for ann in ([a.annotation for a in (node.args.args + node.args.kwonlyargs + node.args.posonlyargs)]
                    + [node.returns] if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else
                    [node.annotation] if isinstance(node, ast.AnnAssign) else []):
            if ann is not None:
                skip |= {id(n) for n in ast.walk(ann)}
    return {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and id(n) not in skip
            and isinstance(n.value, ast.Name) and n.value.id == "sqlite3"}


def test_the_module_seam_exposes_connect_and_what_the_ladder_reads_and_nothing_else(tmp_path):
    """SA-R3-01, research's stage-1 read: the seam forwarded the whole sqlite3 module, so `sqlite3.Connection(path)`
    wrote with no census. Now it exposes `connect` (the census) and SEAM_ATTRS; every other name is refused and
    recorded. SEAM_ATTRS is checked against what the seamed modules actually read, by AST, so a new use fails here by
    name rather than at a migration."""
    census, conn = _census(tmp_path)
    seam = g._Seam(census)
    assert all(getattr(seam, n) is getattr(sqlite3, n) for n in g.SEAM_ATTRS)
    for name in ("Connection", "Cursor", "Row", "Blob", "complete_statement", "sqlite_version"):
        with pytest.raises(g.ChannelRefused):
            getattr(seam, name)
        assert census.refusals[-1][0] == f"sqlite3.{name} through the module seam"
    used = set().union(*(_runtime_sqlite3_names(ROOT / "src" / "veracium" / "store" / m)
                         for m in ("migration.py", "release_migration.py")))
    assert used == g.SEAM_ATTRS | {"connect"}, used


@pytest.mark.parametrize("name,value,ok", [
    pytest.param("isolation_level", None, True, id="isolation_level-None"),
    pytest.param("isolation_level", "", True, id="isolation_level-empty"),
    pytest.param("isolation_level", "DEFERRED", True, id="isolation_level-DEFERRED"),
    pytest.param("isolation_level", "BOGUS", False, id="isolation_level-BOGUS"),
    pytest.param("row_factory", None, True, id="row_factory-None"),
    pytest.param("row_factory", sqlite3.Row, True, id="row_factory-Row"),
    pytest.param("row_factory", lambda cur, row: row, False, id="row_factory-function"),
    pytest.param("text_factory", str, True, id="text_factory-str"),
    pytest.param("text_factory", lambda b: b.decode(), False, id="text_factory-function"),
])
def test_a_settable_attribute_takes_only_its_closed_values(tmp_path, name, value, ok):
    """Research's stage-1 read, in SA-R3-01's closure's letter: replay re-ran `setattr` with the recorded VALUE, so a
    Python row or text factory is caller code executed twice. A value now comes from a closed set (by identity for a
    callable); anything else is refused and recorded, and never recorded as a set."""
    census, conn = _census(tmp_path)
    if ok:
        setattr(conn, name, value)
        assert census.refusals == [] and [e.name for e in census.events if e.kind == "set"] == [name]
        return
    with pytest.raises(g.ChannelRefused):
        setattr(conn, name, value)
    assert census.refusals[-1][0].startswith(f"setting connection.{name} to ")
    assert [e for e in census.events if e.kind == "set"] == []


@pytest.mark.parametrize("forged", ["connect-factory", "connect-positional", "set-function"])
def test_replay_never_runs_recorded_caller_behaviour(tmp_path, forged):
    """SA-R3-01's closure: replay must not execute opaque caller-supplied behaviour as inert input. A recorded connect
    with a factory or a positional extra, or a recorded set to a Python function, is refused by replay itself (the
    census no longer records one; this is the second check), and nothing in it runs."""
    copy = _db(str(tmp_path / "copy.db"), ["CREATE TABLE episodes(id INTEGER PRIMARY KEY, json TEXT)"])
    called = []
    ok_connect = g.Event("connect", 0, args=(), kw={"cached_statements": 0})
    events = {"connect-factory": [g.Event("connect", 0, args=(), kw={"factory": _Constructed, "cached_statements": 0})],
              "connect-positional": [g.Event("connect", 0, args=(5.0,), kw={"cached_statements": 0})],
              "set-function": [ok_connect, g.Event("set", 0, name="row_factory",
                                                   value=lambda cur, row: called.append(row) or row)]}[forged]
    _Constructed.ran.clear()
    problems = g.replay(events, copy)
    assert problems and problems[-1].startswith("replay refuses connection 0's recorded"), problems
    assert _Constructed.ran == [] and called == []
    assert g.replay([ok_connect, g.Event("set", 0, name="isolation_level", value=None)], copy) == []      # control


def test_no_allowed_name_hands_back_a_real_connection_cursor_or_blob(tmp_path):
    census, conn = _census(tmp_path)
    forbidden = (sqlite3.Connection, sqlite3.Cursor, sqlite3.Blob)
    values = [conn.execute("SELECT * FROM episodes"), conn.executemany("INSERT INTO episodes(json) VALUES(?)", [("x",)])]
    cur = conn.execute("SELECT * FROM episodes")
    values += [iter(cur), cur.fetchone(), cur.fetchmany(1), cur.fetchall(), cur.rowcount, cur.lastrowid,
               cur.description, cur.close()]
    values += [getattr(conn, n) for n in sorted(g.CONN_READ_ATTRS)]
    values += [conn.commit(), conn.rollback()]
    with conn as entered:
        values.append(entered)
    for v in values:
        assert not isinstance(v, forbidden), v
        if isinstance(v, list):
            assert not any(isinstance(x, forbidden) for x in v)
    assert conn.__class__ is type(conn) and cur.__class__ is type(cur) and not isinstance(conn, sqlite3.Connection)
    assert census.refusals == []
    # and the type check itself refuses a real object, whichever wrapper would have returned it
    with pytest.raises(g.ChannelRefused):
        census.checked(sqlite3.connect(":memory:"), "a forged return")
    with pytest.raises(g.ChannelRefused):
        census.checked([sqlite3.connect(":memory:").cursor()], "a forged list")
    assert len(census.refusals) == 2
    conn.close()


def test_every_public_name_of_connection_and_cursor_is_allowed_or_refused():
    """The faithful-by-a-list rule, both directions: a public name on this interpreter that is in neither set fails
    here, and the sets are disjoint. The proxies define no dunder the real classes would otherwise lend them."""
    pub = lambda cls: {n for n in dir(cls) if not n.startswith("_")}            # noqa: E731
    conn_allowed = g.CONN_METHODS | g.CONN_READ_ATTRS
    cur_allowed = g.CURSOR_METHODS | g.CURSOR_READ_ATTRS
    assert not (conn_allowed & g.CONN_REFUSED) and not (cur_allowed & g.CURSOR_REFUSED)
    assert pub(sqlite3.Connection) - conn_allowed - g.CONN_REFUSED == set()
    assert pub(sqlite3.Cursor) - cur_allowed - g.CURSOR_REFUSED == set()
    assert g.CONN_SET_ATTRS <= g.CONN_READ_ATTRS
    census = g.Census(":memory:")
    real = sqlite3.connect(":memory:")
    conn = g.connection_proxy(real, census, 0)
    cur = g.cursor_proxy(real.execute("SELECT 1"), census, g.Call(0, "execute"))
    book = {"__module__", "__qualname__", "__slots__", "__doc__", "__static_attributes__", "__firstlineno__"}
    extra = lambda obj: set(vars(type(obj))) - book                             # noqa: E731
    assert extra(conn) == {"__getattribute__", "__setattr__", "__delattr__", "__enter__", "__exit__", "__repr__"}
    assert extra(cur) == {"__getattribute__", "__setattr__", "__delattr__", "__iter__", "__next__", "__repr__"}
    with pytest.raises(TypeError):
        conn("SELECT 1")                                        # Connection.__call__ is not lent to the proxy


def test_the_census_disables_the_statement_cache(tmp_path):
    census, conn = _census(tmp_path)
    for _ in range(2):
        conn.execute("SELECT json FROM episodes").fetchall()
    calls = [e for e in census.events if e.kind == "call"]
    assert [bool(c.acts) for c in calls] == [True, True]          # PREPARE ran twice: the authorizer fired twice
    # the control that makes the cell non-vacuous: with Python's default cache, the second run gives no callback
    seen = []
    c = sqlite3.connect(str(tmp_path / "s.db"))
    c.set_authorizer(lambda *a: (seen.append(a), 0)[1])
    n = []
    for _ in range(2):
        seen.clear(); c.execute("SELECT json FROM episodes").fetchall(); n.append(len(seen))
    c.close()
    assert n[0] > 0 and n[1] == 0, n


def test_an_orphan_callback_and_a_cross_connection_callback_are_refusals(tmp_path):
    census, conn = _census(tmp_path)
    other = census.connect(census.store, (), {})
    census.reals[1].execute("SELECT 1")                         # a statement around the proxy: N11's shape
    assert {(k, cid) for k, cid, _ in census.orphans} == {("auth", 1), ("trace", 1)}
    n = len(census.orphans)
    with census.attribute(g.Call(0, "execute")):
        census.reals[1].execute("SELECT 1")                     # a callback on connection 1 during a call on 0
    # BOTH callbacks are orphans: neither the authorizer's nor the trace's may join another connection's call
    assert {(k, cid) for k, cid, _ in census.orphans[n:]} == {("auth", 1), ("trace", 1)}
    other.close(); conn.close()


# ---- replay equivalence: the six controls (stage-1 item 5) -------------------------------------------------------------
def _forwarding_proxy(real, census, cid):
    """The superseded shape (the census proxies at 58dd7f6): execute and the TXN calls recorded, every other name
    forwarded to the real connection, `_real` an instance attribute. The gate mutant 'forward unknown attributes'."""
    class Forwarding:
        def __init__(self):
            object.__setattr__(self, "_real", real)

        def __getattr__(self, n):
            return getattr(real, n)

        def __setattr__(self, n, v):
            census.set_attr(cid, n, v)
            setattr(real, n, v)

        def __enter__(self):
            return real.__enter__()

        def __exit__(self, *a):
            return real.__exit__(*a)

        def execute(self, sql, params=()):
            p = tuple(params)
            return census.call(cid, "execute", sql, p, lambda: real.execute(sql, p))

        def commit(self):
            return census.call(cid, "commit", None, None, real.commit)

        def rollback(self):
            return census.call(cid, "rollback", None, None, real.rollback)

        def close(self):
            return census.call(cid, "close", None, None, real.close)
    return Forwarding()


def _blob(conn, store):
    rowid = conn.execute("SELECT rowid FROM episodes ORDER BY rowid LIMIT 1").fetchone()[0]
    b = conn.blobopen("episodes", "json", rowid)
    b.write(b"Q")
    b.close()


def _backup(conn, store):
    sqlite3.connect(":memory:").backup(conn._real)


def _unauthorized_delete(conn, store):
    conn.set_authorizer(None)
    conn.set_trace_callback(None)
    conn.execute("WITH doomed AS (SELECT 1) DELETE FROM episodes")
    conn.commit()


def _real_write(conn, store):
    r = conn._real
    r.set_authorizer(None)
    r.set_trace_callback(None)
    r.execute("DELETE FROM episodes")
    r.commit()


def _raw_row(conn, store):
    data = pathlib.Path(store).read_bytes()
    assert data.count(b"weight 81") >= 1
    with open(store, "r+b") as f:
        f.seek(data.index(b"weight 81"))
        f.write(b"weight 82")


def _raw_index(conn, store):
    """One character of one key inside an index's root page: the table pages are untouched."""
    c = sqlite3.connect(store)
    try:
        ps = c.execute("PRAGMA page_size").fetchone()[0]
        data = pathlib.Path(store).read_bytes()
        for name, tbl, root in c.execute("SELECT name, tbl_name, rootpage FROM sqlite_master WHERE type='index' "
                                         "AND sql IS NOT NULL ORDER BY name").fetchall():
            col = [r[2] for r in c.execute(f"PRAGMA index_info({name})")][0]
            page = data[(root - 1) * ps: root * ps]
            for (v,) in c.execute(f"SELECT DISTINCT {col} FROM {tbl}"):
                if isinstance(v, str) and len(v) >= 4 and page.count(v.encode()) == 1:
                    at = (root - 1) * ps + page.index(v.encode())
                    break
            else:
                continue
            break
        else:
            raise AssertionError("no index page holds a unique key value")
    finally:
        c.close()
    with open(store, "r+b") as f:
        f.seek(at + 1)
        f.write(b"#")


# channel -> (the problem the forwarding run must report, a problem it must NOT report, the allowlist's refusal)
CONTROLS = {
    "blobopen write": (_blob, "replay equivalence: table:episodes differs", "orphan", "connection.blobopen"),
    "backup into the ladder's connection": (_backup, "replay equivalence: schema differs", "orphan",
                                            "connection._real"),
    "set_authorizer(None), then a DELETE through execute": (_unauthorized_delete, "traced nothing", None,
                                                            "connection.set_authorizer"),
    "a write on the real connection, instrument removed": (_real_write, "replay equivalence: table:episodes differs",
                                                           "orphan", "connection._real"),
    "raw file I/O changing a row": (_raw_row, "replay equivalence: table:", "orphan", None),
    "raw file I/O corrupting only an index page": (_raw_index, "integrity_check on the census file",
                                                   "replay equivalence", None),
}


def _control_run(tmp_path, monkeypatch, channel, factory):
    import veracium.store.migration as mig
    real_ov = mig.open_versioned
    store = str(tmp_path / "w" / "store.db")

    def open_versioned(conn, path, **kw):
        r = real_ov(conn, path, **kw)                       # the migration has committed; then the channel
        if channel is not None:
            channel(conn, store)
        return r

    monkeypatch.setattr(mig, "open_versioned", open_versioned)
    builders = {lab: b for lab, e, b in g.gate_paths() if e == "migrate_store"}
    return g.run_path("v1#0", "migrate_store", builders["v1#0"], str(tmp_path / "w"), proxy_factory=factory)


@pytest.mark.parametrize("factory", ["forwarding", "allowlist"])
def test_the_control_harness_is_green_without_a_channel(tmp_path, monkeypatch, factory):
    r = _control_run(tmp_path, monkeypatch, None, _forwarding_proxy if factory == "forwarding" else None)
    assert r["problems"] == [] and r["outcome"] == "migrated", r["problems"]


@pytest.mark.parametrize("name", sorted(CONTROLS))
def test_replay_equivalence_catches_each_unrecorded_route_with_the_allowlist_removed(tmp_path, monkeypatch, name):
    channel, must, must_not, _refusal = CONTROLS[name]
    r = _control_run(tmp_path, monkeypatch, channel, _forwarding_proxy)
    assert any(must in p for p in r["problems"]), (name, r["problems"])
    if must_not:
        assert not any(must_not in p for p in r["problems"]), (name, r["problems"])


@pytest.mark.parametrize("name", sorted(CONTROLS))
def test_the_allowlist_refuses_each_connection_route_and_replay_still_sees_the_file_routes(tmp_path, monkeypatch,
                                                                                          name):
    channel, must, _must_not, refusal = CONTROLS[name]
    r = _control_run(tmp_path, monkeypatch, channel, None)
    if refusal is None:                                     # no connection is involved: the proxy cannot see it
        assert any(must in p for p in r["problems"]), (name, r["problems"])
    else:
        assert any(p.startswith(f"refused {refusal} at ") for p in r["problems"]), (name, r["problems"])


# ---- the negative cells N1–N15, end to end (0013 §5f.1's table; 0007 I2) --------------------------------------------
# Each statement is issued by the ladder's own connection INSIDE `_apply_forward`, after the stamp postcondition: what
# a statement added after migration.py's `_refuse_unless(base, STEP_STAMP, ...)` would issue, at that declared site.
# The census attributes it to `_apply_forward` because the issuer is the nearest src frame. Each cell is demonstrated
# red against the gate mutant §5f.1 names beside it by specs/evidence/0013/sa10_mutants.py.
_AF = "veracium/store/migration.py:_apply_forward:"


def _after_stamp(monkeypatch, act):
    import veracium.store.migration as mig
    real = mig._refuse_unless

    def hooked(base, step, problems):
        real(base, step, problems)
        if step == mig.STEP_STAMP:
            act(sys._getframe(1).f_locals["conn"])
    monkeypatch.setattr(mig, "_refuse_unless", hooked)


def _n_run(tmp_path, monkeypatch, act, reals=None):
    """PA1 path v1#0 through migrate_store with `act` after the stamp; `reals`, if given, collects the real
    connections the seam opens (the test's own handle for N11/N12, which go around the proxy by construction)."""
    _after_stamp(monkeypatch, act)

    def factory(real, census, cid):
        reals[cid] = real
        return g.connection_proxy(real, census, cid)

    builders = {lab: b for lab, e, b in g.gate_paths() if e == "migrate_store"}
    return g.run_path("v1#0", "migrate_store", builders["v1#0"], str(tmp_path / "n"),
                      proxy_factory=factory if reals is not None else None)


def _outside(sql):
    return f"execute {sql!r:.90} at {_AF}"


def _episodes_ddl():
    from veracium.store import schema_version as sv
    return next(o.ddl for o in sv.SCHEMAS[sv.SCHEMA_VERSION] if o.key == ("table", "episodes"))


def _op_key_index():
    from veracium.store import schema_version as sv
    return next(o for o in sv.SCHEMAS[sv.SCHEMA_VERSION] if o.key == ("index", "ix_contribution_ledger_op_key"))


def _run_all(*stmts):
    return lambda conn: [conn.execute(s) for s in stmts]


def test_n1_the_reviewers_drop_and_recreate_at_a_declared_site_is_refused(tmp_path, monkeypatch):
    """N1 (SA-R1-01's mutant): DROP TABLE episodes, then episodes' own constructor, after the stamp postcondition, at
    a site declared to issue DDL. Gate mutant: admit every schema write at a declared site."""
    r = _n_run(tmp_path, monkeypatch, _run_all("DROP TABLE episodes", _episodes_ddl()))
    want = _outside("DROP TABLE episodes")
    assert any(p.startswith(want) and p.endswith("a schema write that is not class (a) or (b) by its text")
               for p in r["problems"]), r["problems"]
    assert not any(p.startswith(_outside(_episodes_ddl())) for p in r["problems"]), r["problems"]   # (b1) by its text


def test_n2_a_count_preserving_rebuild_is_refused_statement_by_statement(tmp_path, monkeypatch):
    """N2: CREATE ... AS SELECT, DROP, ALTER ... RENAME: all three outside. Gate mutants: match (b1) by prefix; a
    row-count postcondition in place of the list. The rebuild PRESERVES every count it touches (asserted here, from
    the files, independently of the gate), so a count check is satisfied by construction and only the frozen list can
    refuse it."""
    stmts = ("CREATE TABLE episodes_rebuild AS SELECT * FROM episodes", "DROP TABLE episodes",
             "ALTER TABLE episodes_rebuild RENAME TO episodes")
    r = _n_run(tmp_path, monkeypatch, _run_all(*stmts))
    counts = []
    for f in ("pre.db", "store.db"):
        c = sqlite3.connect(str(tmp_path / "n" / f))
        try:
            counts.append(c.execute("SELECT count(*) FROM episodes").fetchone()[0])
            assert c.execute("SELECT count(*) FROM sqlite_master WHERE name = 'episodes_rebuild'").fetchone()[0] == 0
        finally:
            c.close()
    assert counts[0] == counts[1] >= 1, counts                 # the count-preserving premise holds on the files
    for s in stmts:
        assert any(p.startswith(_outside(s)) and p.endswith("not class (a) or (b) by its text")
                   for p in r["problems"]), (s, r["problems"])


def test_n3_dropping_and_recreating_the_op_key_unique_index_is_refused_on_the_drop(tmp_path, monkeypatch):
    """N3: the op_key UNIQUE index is REQUIRED, not rebuildable, so its `DROP INDEX IF EXISTS` is not (b2); the
    recreate is (b1). Gate mutant: widen (b2) to every index."""
    ix = _op_key_index()
    drop = f"DROP INDEX IF EXISTS {ix.key[1]}"
    r = _n_run(tmp_path, monkeypatch, _run_all(drop, ix.ddl))
    assert any(p.startswith(_outside(drop)) and p.endswith("not class (a) or (b) by its text")
               for p in r["problems"]), r["problems"]
    assert not any(p.startswith(_outside(ix.ddl)) for p in r["problems"]), r["problems"]


@pytest.mark.parametrize("cell,script", [("N4", "DROP TABLE episodes; {ddl}"), ("N8", "SELECT 1; DROP TABLE episodes")],
                         ids=["N4", "N8"])
def test_n4_n8_a_script_on_the_ladders_connection_is_refused_outright(tmp_path, monkeypatch, cell, script):
    """N4 (N1's two statements as one script) and N8 (a script whose FIRST statement is a read): rule 4 refuses
    `executescript` itself. Gate mutant: allow executescript and classify a script by its first statement."""
    text = script.format(ddl=_episodes_ddl())
    r = _n_run(tmp_path, monkeypatch, lambda conn: conn.executescript(text))
    assert any(p.startswith(f"refused connection.executescript at {_AF}") for p in r["problems"]), r["problems"]
    assert r["outcome"].startswith("raised "), r["outcome"]


def _head_variant(monkeypatch, ddl_of):
    from veracium.store import schema_version as sv
    head = sv.SCHEMA_VERSION
    monkeypatch.setitem(sv.SCHEMAS, head, tuple(o._replace(ddl=ddl_of(o)) if o.key == ("table", "episodes") else o
                                                for o in sv.SCHEMAS[head]))


@pytest.mark.parametrize("cell", ["N5", "N10"])
def test_n5_n10_a_head_constructor_that_is_not_a_plain_create_fails_the_gate(tmp_path, monkeypatch, cell):
    """N5 (CREATE TABLE ... AS SELECT) and N10 (IF NOT EXISTS, which would make a recreate a SECOND silent no-op beside
    (b2)'s): run_gate's constructor assertion refuses. Gate mutant: drop the assertion from the gate."""
    variant = {"N5": lambda o: "CREATE TABLE episodes AS SELECT * FROM sqlite_master",
               "N10": lambda o: o.ddl.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1)}[cell]
    _head_variant(monkeypatch, variant)
    report = g.run_gate(str(tmp_path), paths=[])                # no path: the assertion runs on the gate's own
    assert any(p.startswith("head constructor: table episodes: ") for p in report["problems"]), report["problems"]


def test_n6_a_comment_prefixed_drop_is_classified_by_its_actions(tmp_path, monkeypatch):
    """N6: SQLite reports DROP_TABLE and a DELETE on episodes; the prefix label says READ. Gate mutant: classify by
    the leading keyword."""
    sql = "/* repair */ DROP TABLE episodes"
    r = _n_run(tmp_path, monkeypatch, _run_all(sql, _episodes_ddl()))
    mine = [p for p in r["problems"] if p.startswith(_outside(sql))]
    assert any(p.endswith("not class (a) or (b) by its text") for p in mine), r["problems"]
    assert any(p.endswith("the prefix label says READ, SQLite's actions say DDL") for p in mine), r["problems"]


def test_n7_a_cte_prefixed_delete_at_no_step_is_refused(tmp_path, monkeypatch):
    """N7: a row write mapped to no step, which the prefix label calls a read. Gate mutants: classify by the leading
    keyword; a write complement over labelled DML only."""
    sql = "WITH doomed AS (SELECT 1) DELETE FROM episodes"
    r = _n_run(tmp_path, monkeypatch, _run_all(sql))
    mine = [p for p in r["problems"] if p.startswith(_outside(sql))]
    assert any("a row write on ['episodes'] maps to 0 steps" in p for p in mine), r["problems"]
    assert any(p.endswith("the prefix label says READ, SQLite's actions say DML") for p in mine), r["problems"]


def test_n9_writable_schema_at_a_declared_site_is_off_the_pragma_vocabulary(tmp_path, monkeypatch):
    """N9. Gate mutant: treat every pragma other than the stamp as a read."""
    r = _n_run(tmp_path, monkeypatch, _run_all("PRAGMA writable_schema=ON", "PRAGMA writable_schema=OFF"))
    assert any(p.startswith(_outside("PRAGMA writable_schema=ON"))
               and p.endswith("PRAGMA writable_schema('ON') is not on the read vocabulary") for p in r["problems"]), \
        r["problems"]


def test_n11_a_statement_around_the_proxy_is_an_orphan(tmp_path, monkeypatch):
    """N11: a READ on the real connection inside the path, so replay cannot see it and only the orphan check can.
    Gate mutant: skip the orphan check."""
    reals = {}

    def around(conn):
        assert len(reals) == 1
        next(iter(reals.values())).execute("SELECT count(*) FROM episodes").fetchall()
    r = _n_run(tmp_path, monkeypatch, around, reals)
    assert any(p.startswith("orphan auth on connection 0: ") for p in r["problems"]), r["problems"]
    assert any(p.startswith("orphan trace on connection 0: ") for p in r["problems"]), r["problems"]


def test_n12_setconfig_writable_schema_then_a_schema_table_delete_is_refused_twice_over(tmp_path, monkeypatch):
    """N12: setconfig (no callback, no trace) on the real connection, then `DELETE FROM sqlite_master` through the
    proxy. Gate mutants: a schema-table-only write read as a read; the getconfig assertion dropped."""
    reals = {}
    sql = "DELETE FROM sqlite_master WHERE name='episodes'"

    def n12(conn):
        next(iter(reals.values())).setconfig(sqlite3.SQLITE_DBCONFIG_WRITABLE_SCHEMA, True)
        conn.execute(sql)
    r = _n_run(tmp_path, monkeypatch, n12, reals)
    mine = [p for p in r["problems"] if p.startswith(_outside(sql))]
    assert any(p.endswith("a direct write to the schema table (['SQLITE_DELETE'])") for p in mine), r["problems"]
    assert any(p.endswith("SQLITE_DBCONFIG_WRITABLE_SCHEMA is on after the call") for p in r["problems"]), \
        r["problems"]


_N13_15 = {
    "N13 blobopen": ("connection.blobopen",
                     lambda conn: conn.blobopen("episodes", "json", conn.execute(
                         "SELECT rowid FROM episodes ORDER BY rowid LIMIT 1").fetchone()[0]).write(b"Q")),
    "N14 backup into the connection": ("connection.cursor",
                                       lambda conn: sqlite3.connect(":memory:").backup(conn.cursor().connection)),
    "N15 set_authorizer(None), then DELETE": ("connection.set_authorizer",
                                              lambda conn: (conn.set_authorizer(None),
                                                            conn.execute("DELETE FROM episodes"))),
}


@pytest.mark.parametrize("cell", sorted(_N13_15))
def test_n13_n15_a_zero_callback_channel_at_a_declared_site_is_refused(tmp_path, monkeypatch, cell):
    """N13–N15 (stage-1 item 4): channels that write with no authorizer callback, at the declared site. N14's handle
    on the real connection is the one a forwarding proxy lends (`conn.cursor().connection`). Gate mutant: forward
    unknown attributes to the real connection."""
    refusal, act = _N13_15[cell]
    r = _n_run(tmp_path, monkeypatch, act)
    assert any(p.startswith(f"refused {refusal} at {_AF}") for p in r["problems"]), r["problems"]


def test_the_clean_control_admits_a_call_whose_nested_pragma_traces_twice(tmp_path, monkeypatch):
    """§5f.1 rule 3: `SELECT * FROM pragma_table_xinfo(?)` traces twice in one call, and the clean control must not
    fail on it (a per-call trace count refused it 1,904 times at 58dd7f6)."""
    r = _control_run(tmp_path, monkeypatch, None, None)
    nested = [c for c in r["calls"] if len(c.traces) >= 2]
    assert nested and {c.sql for c in nested} >= {"SELECT * FROM pragma_table_xinfo(?)"}, {c.sql for c in nested}
    assert r["problems"] == [], r["problems"]


def test_a_row_write_two_steps_both_claim_is_refused():
    """Exact-one write ownership (INV-SA10's 'a write that two steps' matchers both claim')."""
    from veracium.store import schema_version as sv
    pa1 = g._pa1()
    steps = dict(pa1._steps())
    chains = ("veracium/store/migration.py", "_migrate_outcome_chains", 1, 2)
    rec = g.Call(0, "execute", "UPDATE episodes SET json = ? WHERE id = ?", (), g.Site(chains))
    rec.acts, rec.traces, rec.outcome = [(sqlite3.SQLITE_UPDATE, "episodes", "json", "main", None)], ["t"], ("ok",)
    args = (g.text_classes(), steps, pa1.lib()["_kind"], sv.SCHEMA_VERSION)
    owner = [n for n, pred in steps.items() if pred({"kind": "DML", "sql": rec.sql, "by": rec.site.by})]
    assert len(owner) == 1 and g.classify(rec, *args)[1] == []
    steps["a second matcher"] = steps[owner[0]]
    cls, probs = g.classify(rec, *args)
    assert cls == "row" and any("maps to 2 steps" in p for p in probs), probs


def test_execute_hands_back_the_cursor_wrapper_never_the_real_cursor(tmp_path):
    census, conn = _census(tmp_path)
    cur = conn.execute("SELECT 1")
    assert not isinstance(cur, sqlite3.Cursor) and type(cur).__name__ == "CursorProxy"
    cur = conn.executemany("INSERT INTO episodes(json) VALUES(?)", [("x",)])
    assert not isinstance(cur, sqlite3.Cursor) and type(cur).__name__ == "CursorProxy"
    conn.close()


# ---- the comparator --------------------------------------------------------------------------------------------------
def _db(path, stmts):
    c = sqlite3.connect(path)
    for s in stmts:
        c.execute(*s) if isinstance(s, tuple) else c.execute(s)
    c.commit()
    c.close()
    return path


def test_the_comparator_refuses_another_build_and_names_each_section(tmp_path):
    script = EVIDENCE / "sa10_digest.py"
    assert script.name == "sa10_digest.py" and g.DIGEST_SCRIPT == script
    version, source = g.build_identity()
    base = ["CREATE TABLE a(x)", "CREATE TABLE b(y)", "INSERT INTO a VALUES('one')", "INSERT INTO b VALUES(2)"]
    p0 = _db(str(tmp_path / "p0.db"), base)
    d0 = g.digest(p0)
    assert "refused" not in d0 and d0["integrity"] == ["ok"] and d0["source_id"] == source
    # the build is ASSERTED: the census's source id with one character changed refuses
    forged = source[:-1] + ("0" if source[-1] != "0" else "1")
    run = lambda *a: subprocess.run([sys.executable, "-I", str(script), *a], capture_output=True, text=True)  # noqa
    r = run(p0, version, forged)
    assert r.returncode == 4 and "the census ran" in r.stdout, (r.returncode, r.stdout)
    assert run(p0, "0.0.0", source).returncode == 4
    assert run(p0, version).returncode == 2                    # no normalisation option exists; nor a short argv
    # each section moves on its own change, and only it
    differs = lambda p: sorted(k for k in d0["sections"] if g.digest(p)["sections"].get(k) != d0["sections"][k])  # noqa
    assert differs(_db(str(tmp_path / "p1.db"), base[:2] + ["INSERT INTO a VALUES('onf')", base[3]])) == ["table:a"]
    assert differs(_db(str(tmp_path / "p2.db"), base[:2] + [("INSERT INTO a VALUES(?)", (b"one",)), base[3]])) == [
        "table:a"]                                             # TEXT and BLOB of the same bytes differ (typeof)
    assert differs(_db(str(tmp_path / "p3.db"), base + ["PRAGMA user_version = 3"])) == ["pragmas"]
    assert differs(_db(str(tmp_path / "p4.db"), base + ["CREATE INDEX ia ON a(x)"])) == ["pragmas", "schema"]
    # rootpage is physical placement, not content: the same tables created in the other order digest equal
    assert differs(_db(str(tmp_path / "p5.db"), [base[1], base[0], base[2], base[3]])) == []
    import math                                               # a REAL is compared exactly, not to 15 digits
    f1 = g.digest(_db(str(tmp_path / "f1.db"), ["CREATE TABLE f(x)", ("INSERT INTO f VALUES(?)", (0.1,))]))
    f2 = g.digest(_db(str(tmp_path / "f2.db"), ["CREATE TABLE f(x)", ("INSERT INTO f VALUES(?)", (math.nextafter(0.1, 1),))]))
    assert [m for m in g.compare(f1, f2) if "table:f" in m]
    # refusals: a leftover journal, a table without a rowid, and integrity is reported, not normalised
    p7 = _db(str(tmp_path / "p7.db"), base)
    pathlib.Path(p7 + "-journal").write_bytes(b"x")
    assert run(p7, version, source).returncode == 3
    p8 = _db(str(tmp_path / "p8.db"), ["CREATE TABLE w(k PRIMARY KEY, v) WITHOUT ROWID"])
    assert run(p8, version, source).returncode == 5
    # the isolated interpreter cannot be reached through PYTHONPATH: a planted json.py on it is not imported
    plant = tmp_path / "plant"
    plant.mkdir()
    (plant / "json.py").write_text("raise SystemExit('PLANTED')\n")
    r = subprocess.run([sys.executable, "-I", str(script), p0, version, source], capture_output=True, text=True,
                       env={**os.environ, "PYTHONPATH": str(plant)})
    assert r.returncode == 0 and "PLANTED" not in r.stdout + r.stderr


# ---- head constructors (N5, N10 at the assertion) -------------------------------------------------------------------
def test_the_head_constructors_are_plain_creates_and_the_assertion_refuses_each_variant():
    from veracium.store import schema_version as sv
    head = list(sv.SCHEMAS[sv.SCHEMA_VERSION])
    assert g.constructor_problems() == []
    t, i = _head("table"), _head("index")
    name = t.key[1]
    variants = {
        "AS SELECT": (t, f"CREATE TABLE {name} AS SELECT * FROM sqlite_master"),
        "AS SELECT, spelled with a column list": (t, f"CREATE TABLE {name} (a) AS SELECT 1"),
        "IF NOT EXISTS": (t, t.ddl.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1)),
        "TEMP": (t, t.ddl.replace("CREATE TABLE", "CREATE TEMP TABLE", 1)),
        "another table's name": (t, t.ddl.replace(name, name + "_x", 1)),
        "an index IF NOT EXISTS": (i, i.ddl.replace("INDEX", "INDEX IF NOT EXISTS", 1)),
        "a constructor that does not run": (t, f"CREATE TABLE {name} (a,,)"),
    }
    for label, (obj, ddl) in variants.items():
        objs = [o._replace(ddl=ddl) if o == obj else o for o in head]
        probs = g.constructor_problems(objs)
        assert len(probs) >= 1 and all(f" {obj.key[1]}: " in p for p in probs), (label, probs)
    assert any("does not run on an empty database" in p for p in g.constructor_problems(
        [o._replace(ddl=f"CREATE TABLE {name} (a,,)") if o == t else o for o in head]))


# ---- the gate's own checks, each against the mutant that would remove it ------------------------------------------------
def test_a_narrowed_path_set_refuses_loudly(tmp_path):
    """One PA1 path alone: the (b2) sites, the C2/C3 cells and the repair's declared DDL site go unobserved, and each
    is a refusal, so a gate run over fewer paths can never read as the gate."""
    one = [p for p in g.gate_paths() if p[:2] == ("v1#0", "migrate_store")]
    report = g.run_gate(str(tmp_path), paths=one)
    probs = report["problems"]
    assert any("declared DDL site never observed issuing DDL: ('veracium/store/schema_version.py', '_repair_drift')"
               in p for p in probs), probs
    for entry in ("migrate_store", "release"):
        assert f"{entry} C2: no (b2) statement carrying a DROP_INDEX action was observed" in probs
        assert f"{entry} C3: no (b2) no-op was observed" in probs


def test_site_coverage_reports_an_unobserved_site_in_a_function_the_census_entered():
    import veracium.store.release_migration as rm
    import inspect
    first = rm._observe.__code__.co_firstlineno
    rel = "veracium/store/release_migration.py"
    sites = g._function_sites(inspect.getsource(rm), "_observe", first)
    assert len(sites) >= 2, sites
    seen = g.Call(0, "execute", "BEGIN IMMEDIATE", (), g.Site((rel, "_observe", first, sites[0][0])))
    cov = g.site_coverage([seen])
    assert cov["functions"] == 1 and len(cov["unobserved"]) == len(sites) - 1, cov
    assert cov["unobserved"][0] == f"{rel}:_observe:{sites[1][0]}"
    # open_versioned is the one stated exclusion: entering it owes nothing
    from veracium.store import schema_version as sv
    ov = g.Call(0, "execute", "BEGIN", (), g.Site(("veracium/store/schema_version.py", "open_versioned",
                                                    sv.open_versioned.__code__.co_firstlineno, 1)))
    assert g.site_coverage([ov]) == {"functions": 0, "sites": 0, "unobserved": []}


def test_the_configuration_guard_sees_setconfig_which_no_statement_shows(tmp_path, monkeypatch):
    """N12's channel: setconfig fires no callback and no trace, so the census reads getconfig after every call."""
    def n12(conn, store):
        conn.setconfig(sqlite3.SQLITE_DBCONFIG_WRITABLE_SCHEMA, True)
        conn.execute("SELECT 1").fetchall()

    def defensive(conn, store):
        conn.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, not conn.getconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE))
        conn.execute("SELECT 1").fetchall()

    r = _control_run(tmp_path / "a", monkeypatch, n12, _forwarding_proxy)
    assert any("SQLITE_DBCONFIG_WRITABLE_SCHEMA is on after the call" in p for p in r["problems"]), r["problems"]
    r = _control_run(tmp_path / "b", monkeypatch, defensive, _forwarding_proxy)
    assert any("SQLITE_DBCONFIG_DEFENSIVE changed during the call" in p for p in r["problems"]), r["problems"]
    r = _control_run(tmp_path / "c", monkeypatch, n12, None)
    assert any(p.startswith("refused connection.setconfig at ") for p in r["problems"]), r["problems"]


def test_parameters_are_recorded_by_value_and_replay_compares_every_outcome(tmp_path):
    census, conn = _census(tmp_path)
    params = ["{\"b\": 2}"]
    conn.execute("INSERT INTO episodes(json) VALUES(?)", params)
    params[0] = "mutated after the call"
    assert census.events[-1].params == ("{\"b\": 2}",)
    conn.commit()
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("SELECT nope FROM episodes")
    conn.close()
    calls = [e for e in census.events if e.kind == "call"]
    assert [c.outcome for c in calls] == [("ok",), ("ok",), ("raise", "OperationalError"), ("ok",)]
    copy = str(tmp_path / "copy.db")
    _db(copy, ["CREATE TABLE episodes(id INTEGER PRIMARY KEY, json TEXT)",
               "INSERT INTO episodes(json) VALUES('{\"a\": 1}')"])
    assert g.replay(census.events, copy) == []
    assert g.compare(g.digest(census.store), g.digest(copy)) == []
    # a recorded outcome the replay does not reproduce is a refusal, in either direction
    calls[2].outcome = ("ok",)
    calls[0].outcome = ("raise", "IntegrityError")
    copy2 = str(tmp_path / "copy2.db")
    _db(copy2, ["CREATE TABLE episodes(id INTEGER PRIMARY KEY, json TEXT)"])
    probs = g.replay(census.events, copy2)
    assert len(probs) == 2 and all(p.startswith("replay: ") for p in probs), probs


def test_the_context_manager_replays_commit_and_rollback_and_a_foreign_connect_is_refused(tmp_path):
    census, conn = _census(tmp_path)
    with conn:
        conn.execute("INSERT INTO episodes(json) VALUES('kept')")
    with pytest.raises(ZeroDivisionError):
        with conn:
            conn.execute("INSERT INTO episodes(json) VALUES('rolled back')")
            1 / 0
    conn.close()
    exits = [e for e in census.events if e.kind == "call" and e.how == "__exit__"]
    assert [e.ok for e in exits] == [True, False]
    copy = str(tmp_path / "copy.db")
    _db(copy, ["CREATE TABLE episodes(id INTEGER PRIMARY KEY, json TEXT)",
               "INSERT INTO episodes(json) VALUES('{\"a\": 1}')"])
    assert g.replay(census.events, copy) == []
    assert g.compare(g.digest(census.store), g.digest(copy)) == []
    with sqlite3.connect(census.store) as c:
        assert [r[0] for r in c.execute("SELECT json FROM episodes ORDER BY id")] == ['{"a": 1}', "kept"]
    c.close()
    other = str(tmp_path / "other.db")
    census.connect(other, (), {}).close()
    assert any(p.startswith(f"connect to {other!r}") and p.endswith("not the store") for p in census.problems)


# ---- 0013 v37 §5f.1: the pre-3.41 declare_vtab sequence, attributed only under all three conditions ---------------------
_SEL = (sqlite3.SQLITE_SELECT, None, None, None, None)
_XINFO = "SELECT * FROM pragma_table_xinfo(?)"


def _vtab_call(census, cid=0, seq=None, sql=_XINFO, phase=0):
    """A recorded call whose actions are SELECT then `seq` (default: the measured six), each at trace phase `phase`."""
    seq = list(g.DECLARE_VTAB_SEQ if seq is None else seq)
    rec = g.Call(cid, "execute", sql, ("t",), g.Site(_DECLARED))
    rec.acts = [_SEL] + seq + [(sqlite3.SQLITE_READ, "t", "a", "main", None)]
    rec.act_phase = [0] + [phase] * len(seq) + [0]
    census._attribute_declare_vtab(cid, rec)
    return rec


def test_the_declare_vtab_probe_needs_the_exact_sequence_and_no_change():
    """v37 condition (3)'s decision: the measured six callbacks right after a SELECT AND schema_version, data_version,
    total_changes() and the sqlite_master rows unchanged. Mutant: the no-change check dropped (phrase 16)."""
    state = (7, 1, 1, [("table", "t", "t", 2, "CREATE TABLE t(a)")])
    acts = [_SEL, *g.DECLARE_VTAB_SEQ]
    assert g.declare_vtab_probe_result(acts, state, state) is True
    assert g.declare_vtab_probe_result([_SEL], state, state) is False                      # a 3.41+ build
    changed = (8, *state[1:])
    assert g.declare_vtab_probe_result(acts, state, changed) is False                       # something changed


def test_the_declare_vtab_sequence_is_attributed_on_a_reproducing_build_and_classifies_as_a_read(monkeypatch):
    """v37: on a build whose probe reproduces, a first use's exact sequence in the prepare is bookkeeping: removed from
    the call's actions and named, so the read classifies clean; unattributed, the same call is a direct write."""
    monkeypatch.setattr(g, "_DECLARE_VTAB_PROBE", True)
    rec = _vtab_call(g.Census(":memory:"))
    assert rec.bookkeeping == ["declare_vtab"] and g.DECLARE_VTAB_SEQ[0] not in rec.acts
    from veracium.store import schema_version as sv
    pa1 = g._pa1()
    _cls, problems = g.classify(rec, g.text_classes(), pa1._steps(), pa1.lib()["_kind"], sv.SCHEMA_VERSION)
    assert not [p for p in problems if "direct write to the schema table" in p], problems
    raw = _classify(_XINFO, [_SEL, *g.DECLARE_VTAB_SEQ])
    assert any("direct write to the schema table" in p for p in raw[1]), raw


def test_the_declare_vtab_sequence_is_a_write_on_a_build_whose_probe_does_not_reproduce(monkeypatch):
    """v37 condition (3) (phrase 12): a build whose own probe does not reproduce the sequence attributes nothing."""
    monkeypatch.setattr(g, "_DECLARE_VTAB_PROBE", False)
    rec = _vtab_call(g.Census(":memory:"))
    assert rec.bookkeeping == [] and rec.acts[1] == g.DECLARE_VTAB_SEQ[0]


@pytest.mark.parametrize("variant", ["sixth-column", "another-table", "another-database", "trigger-argument"])
def test_a_variant_of_the_declare_vtab_sequence_stays_a_write(monkeypatch, variant):
    """v37 condition (1) (phrase 13): only the EXACT six callbacks."""
    monkeypatch.setattr(g, "_DECLARE_VTAB_PROBE", True)
    seq = list(g.DECLARE_VTAB_SEQ)
    if variant == "sixth-column":
        seq.insert(5, (sqlite3.SQLITE_UPDATE, "sqlite_master", "extra", "main", None))
    elif variant == "another-table":
        seq = [(a[0], "t", a[2], a[3], a[4]) for a in seq]
    elif variant == "another-database":
        seq = [(a[0], a[1], a[2], "temp", a[4]) for a in seq]
    else:
        seq = [(a[0], a[1], a[2], a[3], "a_trigger") for a in seq]
    rec = _vtab_call(g.Census(":memory:"), seq=seq)
    assert rec.bookkeeping == [], variant


def test_the_declare_vtab_sequence_is_bookkeeping_only_on_a_connections_first_use(monkeypatch):
    """v37 condition (2) (phrase 14): a second use of the same pragma module on one connection attributes nothing."""
    monkeypatch.setattr(g, "_DECLARE_VTAB_PROBE", True)
    census = g.Census(":memory:")
    assert _vtab_call(census).bookkeeping == ["declare_vtab"]
    assert _vtab_call(census).bookkeeping == []                  # the same connection, the same module, again
    assert _vtab_call(census, cid=1).bookkeeping == ["declare_vtab"]                  # another connection: its first


def test_the_declare_vtab_sequence_outside_a_prepare_stays_a_write(monkeypatch):
    """v37 condition (2) (phrase 15): only in the PREPARE, before the call's first trace."""
    monkeypatch.setattr(g, "_DECLARE_VTAB_PROBE", True)
    assert _vtab_call(g.Census(":memory:"), phase=1).bookkeeping == []
