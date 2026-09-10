"""specs/0039 — degradation visibility: the sixteen OWED nodes, one per invariant
of the frozen §6 surface (accepted at external round 4, 2026-09-10).

The scripted provider and the answer shapes are the evidence script's own
(`specs/evidence/0039/answer_shapes.py`), imported by path so the matrix the
spec froze and the shapes these tests drive are one artifact.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import pathlib
import re
import sqlite3
import sys

import pytest

from veracium import Memory, MemoryConfig
from veracium import ingest as ingest_mod
from veracium.diagnostics import DiagnosticsConfig, Reporter
from veracium.ingest import ingest_event
from veracium.schema import EvidenceAuthor, EvidenceContext
from veracium.store.sqlite import SqliteStore

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("answer_shapes", ROOT / "specs" / "evidence" / "0039" / "answer_shapes.py")
shapes = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(shapes)
Stub, MainRaises, GOOD, OFF = shapes.Stub, shapes.MainRaises, shapes.GOOD, shapes.OFF

TEXT = "I use Vim for editing."
USER = "u"
_LINE = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d+ (WARNING|ERROR|INFO) (.*)$")


# ---------------------------------------------------------------- helpers ----
def _reporter(tmp_path, name="v.log", **cfg):
    return Reporter(DiagnosticsConfig(log_path=str(tmp_path / name), report_enabled=False, **cfg))


def _mem(tmp_path, llm, reporter, name="m"):
    return Memory(llm=llm, config=MemoryConfig(db_path=str(tmp_path / f"{name}.db"), wiki_recompile_after_writes=0),
                  diagnostics=reporter)


def _remember(mem):
    return mem.remember(USER, TEXT, author=EvidenceAuthor.USER, date="2026-09-01", context=EvidenceContext.direct())


def _records(reporter):
    """Every log LINE that is a record (WARNING degrade records and ERROR records);
    traceback continuation lines are not records. Returns [(level, fields)]."""
    path = reporter.config.resolved_log_path()
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        m = _LINE.match(line)
        if not m:
            continue
        level, rest = m.group(1), m.group(2)
        fields = {}
        for tok in rest.split():
            if "=" in tok:
                k, v = tok.split("=", 1); fields[k] = v
        out.append((level, fields))
    return out


def _degrades(reporter):
    return [f for lvl, f in _records(reporter) if lvl == "WARNING" and "degrade" in f]


def _main(triples, **extra):
    return json.dumps({"triples": triples, **extra})


# ------------------------------------------------------------- V-CENSUS ------
def test_the_census_names_every_continuing_handler():
    """V-CENSUS (frozen): ingest.py has exactly the three continuing exception
    handlers §1 names and every other handler re-raises; PLUS exactly the one
    guarded literal-reset branch of §1a path iii inside ingest_event. A new site
    of either shape fails until the spec names it. The census answers a SHAPE
    question (§6 states the limit); V-ANSWER-MATRIX tests the outcome."""
    src = (ROOT / "src" / "veracium" / "ingest.py").read_text()
    tree = ast.parse(src)
    continuing, reraising = [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            raises = any(isinstance(n, ast.Raise) for b in node.body for n in ast.walk(b))
            (reraising if raises else continuing).append(node.lineno)
    assert len(reraising) == 1, reraising                      # the event-date parser
    # §2c names a fourth continuing handler by construction: `_emit_degrade`'s
    # own `except Exception: pass`, the containment itself — it is inside the
    # helper and nowhere else; the three DEGRADE handlers §1 names are the rest
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_emit_degrade")
    in_helper = {n.lineno for n in ast.walk(helper) if isinstance(n, ast.ExceptHandler)}
    assert len(in_helper) == 1, in_helper
    continuing = [ln for ln in continuing if ln not in in_helper]
    assert len(continuing) == 3, continuing                    # unparseable, retry, volatility
    lines = src.splitlines()
    kinds = {"unparseable": False, "retry": False, "volatility": False}
    for ln in continuing:
        window = "\n".join(lines[ln - 1: ln + 40])
        if "unparseable" in window: kinds["unparseable"] = True
        if "reps = []" in window: kinds["retry"] = True
        if "Volatility.DURABLE" in window: kinds["volatility"] = True
    assert all(kinds.values()), kinds
    # the second shape: an If inside ingest_event whose test is isinstance/truthiness
    # over a name bound from extract_json, whose body assigns an empty/default literal
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "ingest_event")
    bound = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
            f = n.value.func
            if (isinstance(f, ast.Name) and f.id == "extract_json") or (isinstance(f, ast.Attribute) and f.attr == "get"):
                for tgt in n.targets:
                    if isinstance(tgt, ast.Name): bound.add(tgt.id)
    resets = []
    for n in ast.walk(fn):
        if not isinstance(n, ast.If): continue
        test = n.test
        guarded = (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)) or \
                  (isinstance(test, ast.Call) and isinstance(test.func, ast.Name) and test.func.id == "isinstance") or \
                  (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not) and isinstance(test.operand, ast.Call))
        if not guarded: continue
        names = {x.id for x in ast.walk(test) if isinstance(x, ast.Name)}
        if not (names & bound): continue
        for b in n.body:
            # an EMPTY or DEFAULT literal (§6: `[]`, `{}`, `None`) — the bare-array
            # WRAP `data = {"triples": data}` is a normalization, not a discard,
            # and assigns a non-empty dict; it is not this shape
            v = b.value if isinstance(b, ast.Assign) else None
            empty = (isinstance(v, (ast.List, ast.Dict)) and not (v.elts if isinstance(v, ast.List) else v.keys)) or \
                    (isinstance(v, ast.Constant) and v.value in (None, "", 0))
            if isinstance(b, ast.Assign) and empty and any(isinstance(t, ast.Name) and t.id in bound for t in b.targets):
                resets.append(b.lineno)
    assert len(resets) == 1, f"guarded literal-reset branches over parsed provider output: {resets} (the spec names ONE, §1a path iii)"


# ------------------------------------------------------- V-ANSWER-MATRIX -----
_PRIMARY_ROWS = [
    # (row, primary raw, expected degrade kinds in order, raises)
    (1, _main([GOOD]), [], None),
    (2, _main([]), [], None),
    (3, json.dumps({"note": "none"}), [("primary_failed", "no_triples_key")], None),
    (4, _main("user uses Vim"), [("primary_failed", "shape")], None),
    (5, _main({"triples": [GOOD]}), [("primary_failed", "shape")], None),
    (6, _main(None), [("primary_failed", "shape")], TypeError),
    (7, _main(3), [("primary_failed", "shape")], TypeError),
    (7, _main(True), [("primary_failed", "shape")], TypeError),
    (8, json.dumps([GOOD]), [], None),
    (9, json.dumps(["triples", 1]), [("member_skipped", "2")], None),
    (10, _main([GOOD, "junk", 7, None]), [("member_skipped", "3")], None),
    (10, _main([{}, {}]), [("member_skipped", "2")], None),
    (11, json.dumps("hello"), [("unparseable", "no_json")], None),
    (11, "I cannot help with that.", [("unparseable", "no_json")], None),
    (12, _main([GOOD], instructions="x"), [("unparseable", "instructions_type")], None),
]
_RETRY_ROWS = [
    # (row, retry raw / raise, expected degrade kinds)
    (13, RuntimeError("boom"), [("retry_failed", "provider_error")]),
    (11, "cannot", [("retry_failed", "no_json")]),
    (8, json.dumps([GOOD]), [("retry_failed", "bare_array")]),            # the CURRENT state; §2e's amendment flips this row
    (9, json.dumps(["triples"]), [("retry_failed", "bare_array")]),
    (4, _main("x"), [("retry_failed", "shape")]),
    (5, _main({}), [("retry_failed", "shape")]),
    (6, _main(None), [("retry_failed", "shape")]),
    (7, _main(3), [("retry_failed", "shape")]),
    (3, json.dumps({"repairs": [GOOD]}), [("retry_failed", "no_triples_key")]),
    (2, _main([]), []),
    (1, _main([GOOD]), []),
    (10, _main([GOOD, "junk"]), [("member_skipped", "1")]),
    (11, "42", [("retry_failed", "no_json")]),
    (12, _main([GOOD], instructions="x"), []),                             # the field is not read on the retry
]


def _kinds(degrades):
    return [(d["degrade"], d.get("cause", d.get("count"))) for d in degrades]


def test_the_answer_matrix_holds_on_both_call_sites(tmp_path):
    """V-ANSWER-MATRIX (frozen): §2c-ii — every row's first-extraction cell and
    retry cell hold by exact equality on the records written (or not), the
    result dict and the raised class. Asymmetric rows are asserted AS
    asymmetric: the retry's bare-array cell is `bare_array` today, and §2e's
    0025 amendment must flip that assertion in its own commit."""
    for i, (row, raw, expected, raises) in enumerate(_PRIMARY_ROWS):
        rep = _reporter(tmp_path, f"p{i}.log")
        mem = _mem(tmp_path, Stub(raw, retry_raw=_main([])), rep, f"p{i}")
        if raises is None:
            _remember(mem)
        else:
            with pytest.raises(raises):
                _remember(mem)
        assert _kinds(_degrades(rep)) == expected, f"primary row {row}: {raw[:40]!r}"
    for i, (row, retry, expected) in enumerate(_RETRY_ROWS):
        rep = _reporter(tmp_path, f"r{i}.log")
        llm = Stub(_main([OFF]), retry_raw=None if isinstance(retry, Exception) else retry,
                   retry_raises=retry if isinstance(retry, Exception) else None)
        mem = _mem(tmp_path, llm, rep, f"r{i}")
        r = _remember(mem)
        assert r["retried"] == 1, f"retry row {row}: the retry did not fire"
        assert _kinds(_degrades(rep)) == expected, f"retry row {row}: {retry!r}"


# ------------------------------------------------- V-CALLBACK-CONTAINED ------
def test_no_site_calls_the_callback_directly():
    """Static half: no Call in ingest.py names `on_degrade` outside `_emit_degrade`."""
    tree = ast.parse((ROOT / "src" / "veracium" / "ingest.py").read_text())
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_emit_degrade")
    inside = {id(x) for x in ast.walk(helper)}
    direct = [n.lineno for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "on_degrade" and id(n) not in inside]
    assert direct == [], f"on_degrade called directly at lines {direct}"
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_emit_degrade"]
    assert len(calls) >= 5, "the five sites invoke the helper"


def _equivalent_run(tmp_path, monkeypatch, raw, retry_raw, callback, name):
    """§2c-iii, the deterministic fixture: ids from a counter, the store's clock=
    seam fixed, fixed dates, a fresh store; the comparison over CANONICAL LOGICAL
    CONTENTS, never file bytes; the callback's invocations observed."""
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from veracium.store import schema_version as sv
    counter = {"n": 0}
    def _uid(prefix):
        counter["n"] += 1
        return f"{prefix}-{counter['n']:04d}"
    monkeypatch.setattr(ingest_mod, "_uid", _uid)
    # "control every nondeterministic input" (§2c-iii) reaches PAST ingest: creating
    # a store mints a random origin (specs/0006 §4.2, `uuid.uuid4`) and stamps the
    # journaling epoch from the wall clock (specs/0029 §4e) — two columns that differ
    # between any two runs and would make the comparison unfalsifiable-by-noise. Both
    # are pinned at the module's own names, so the real minting code still runs.
    fixed = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
    origins = {"n": 0}
    def _uuid4():
        origins["n"] += 1
        return f"00000000-0000-4000-8000-{origins['n']:012d}"
    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed
    monkeypatch.setattr(sv, "uuid", SimpleNamespace(uuid4=_uuid4))
    monkeypatch.setattr(sv, "datetime", _FixedDatetime)
    store = SqliteStore(str(tmp_path / f"{name}.db"), clock=lambda: datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc))
    calls = []
    cb = None if callback is None else (lambda kind, payload: (calls.append(kind), callback(kind, payload)))
    llm = Stub(raw, retry_raw=retry_raw)
    result = ingest_event(store, llm, USER, event_text=TEXT, author=EvidenceAuthor.USER, date="2026-09-01",
                          context=EvidenceContext.direct(), on_degrade=cb)
    conn = store._conn
    tables = sorted(r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT GLOB 'sqlite_*'"))
    dump = {}
    for table in tables:
        cur = conn.execute(f"SELECT * FROM {table} ORDER BY rowid")
        cols = [d[0] for d in cur.description]
        dump[table] = [dict(zip(cols, row)) for row in cur.fetchall()]
    return result, json.dumps(dump, sort_keys=True, default=str), calls


def test_a_raising_callback_changes_nothing_at_any_site(tmp_path, monkeypatch):
    """Dynamic half: at each of the five sites, a raising callback returns the
    same dict, leaves the same canonical logical contents, and was invoked."""
    def raising(kind, payload):
        raise RuntimeError("callback failure")
    sites = [
        ("primary", json.dumps({"note": "none"}), _main([]), "primary_failed"),
        ("member", _main([GOOD, "junk"]), _main([]), "member_skipped"),
        ("retry", _main([OFF]), "cannot", "retry_failed"),
        ("unparseable", "prose", _main([]), "unparseable"),
        ("volatility", _main([dict(GOOD, volatility="banana")]), _main([]), "volatility_defaulted"),
    ]
    for site, raw, retry_raw, kind in sites:
        r_none, s_none, _ = _equivalent_run(tmp_path, monkeypatch, raw, retry_raw, None, f"{site}-none")
        r_raise, s_raise, hits = _equivalent_run(tmp_path, monkeypatch, raw, retry_raw, raising, f"{site}-raise")
        assert r_raise == r_none, site
        assert s_raise == s_none, site
        assert kind in hits, (site, hits)
    # The control, and it must run OUTSIDE the fixture's patches: with `_uid` still
    # counting, two runs differ because the counter advanced, not because ids are
    # random — a control that passes for the wrong reason is the vacuous class.
    monkeypatch.undo()
    a = SqliteStore(str(tmp_path / "x1.db")); b = SqliteStore(str(tmp_path / "x2.db"))
    ingest_event(a, Stub(_main([GOOD]), retry_raw=_main([])), USER, event_text=TEXT, author=EvidenceAuthor.USER, date="2026-09-01", context=EvidenceContext.direct())
    ingest_event(b, Stub(_main([GOOD]), retry_raw=_main([])), USER, event_text=TEXT, author=EvidenceAuthor.USER, date="2026-09-01", context=EvidenceContext.direct())
    ids_a = [r[0] for r in a._conn.execute("SELECT id FROM edges")]; ids_b = [r[0] for r in b._conn.execute("SELECT id FROM edges")]
    assert ids_a != ids_b, "the control: uncontrolled ids differ between identical runs"
    # and the store identity the fixture pins is itself uncontrolled here (the second
    # half of what the comparison would otherwise be reading as noise)
    o_a = a._conn.execute("SELECT origin FROM store_identity").fetchone()[0]
    o_b = b._conn.execute("SELECT origin FROM store_identity").fetchone()[0]
    assert o_a != o_b, "the control: uncontrolled store origins differ between identical runs"


# ------------------------------------------------------ V-NO-INLINE-SEND -----
def test_record_degrade_never_sends_inline(tmp_path, monkeypatch):
    """With advance permission, an endpoint and an elapsed interval, record_degrade
    performs no network I/O; record_error in the same configuration sends once
    (the control)."""
    from veracium import diagnostics as diag
    posts = []
    monkeypatch.setattr(diag, "_post", lambda endpoint, payload: posts.append(endpoint))
    cfg = DiagnosticsConfig(log_path=str(tmp_path / "v.log"), report_enabled=True, endpoint="https://example.invalid/x",
                            report_min_interval_s=0, last_report=None)
    monkeypatch.setattr(DiagnosticsConfig, "save", lambda self: None)
    rep = Reporter(cfg)
    mem = _mem(tmp_path, Stub(_main([OFF]), retry_raises=RuntimeError("boom")), rep)
    _remember(mem)                                     # retry_failed → record_degrade
    mem2 = _mem(tmp_path, Stub("prose", retry_raw=_main([])), rep, "m2")
    _remember(mem2)                                    # unparseable → record_degrade
    assert posts == [], "record_degrade must not send inline"
    assert rep.has_pending()
    rep.record_error("remember", RuntimeError("x"), {"user_hash": "abc"})   # the control
    assert posts == ["https://example.invalid/x"]


# ------------------------------------------------------- V-CAUSE-BOUNDED -----
_CAUSES = {"provider_error", "no_json", "instructions_type", "shape", "no_triples_key", "bare_array"}


def test_cause_is_a_closed_vocabulary_and_a_provider_exception_name_never_reaches_the_log(tmp_path):
    sentinel = "ZQXJ-SENTINEL-77"
    class Boom(Exception):
        pass
    Boom.__name__ = f"Provider{sentinel}Error"
    exc = Boom(f"message {sentinel}")
    exc.detail = sentinel
    exc.__cause__ = RuntimeError(sentinel)   # a carrier on every interpreter we support
    if hasattr(exc, "add_note"):             # notes are 3.11+; CI's floor is 3.10
        exc.add_note(sentinel)
    rep = _reporter(tmp_path)
    mem = _mem(tmp_path, Stub(_main([OFF]), retry_raises=exc), rep)
    _remember(mem)
    d = _degrades(rep)
    assert [x["cause"] for x in d] == ["provider_error"]
    assert sentinel not in rep.config.resolved_log_path().read_text()
    assert d[0]["msg_len"] == str(len(str(exc).encode())) and d[0]["msg_sha16"] == hashlib.sha256(str(exc).encode()).hexdigest()[:16]
    # every cause seen across the matrix is in the closed set
    seen = set()
    for i, (row, retry, expected) in enumerate(_RETRY_ROWS):
        seen |= {c for k, c in expected if k == "retry_failed"}
    assert seen <= _CAUSES


# --------------------------------------------------- V-DEGRADE-RECORDED ------
def test_retry_failure_writes_one_record(tmp_path):
    rep = _reporter(tmp_path)
    _remember(_mem(tmp_path, Stub(_main([OFF]), retry_raises=RuntimeError("boom")), rep))
    assert _kinds(_degrades(rep)) == [("retry_failed", "provider_error")]


def test_unparseable_writes_one_record(tmp_path):
    rep = _reporter(tmp_path)
    _remember(_mem(tmp_path, Stub("I cannot help with that.", retry_raw=_main([])), rep))
    assert _kinds(_degrades(rep)) == [("unparseable", "no_json")]
    rep2 = _reporter(tmp_path, "w.log")
    _remember(_mem(tmp_path, Stub(_main([GOOD], instructions="x"), retry_raw=_main([])), rep2, "m2"))
    assert _kinds(_degrades(rep2)) == [("unparseable", "instructions_type")]


def test_drifted_volatility_writes_one_record_with_the_count(tmp_path):
    rep = _reporter(tmp_path)
    triples = [dict(GOOD, object=f"tool{i}", volatility="banana") for i in range(4)]
    _remember(_mem(tmp_path, Stub(_main(triples), retry_raw=_main([])), rep))
    assert _kinds(_degrades(rep)) == [("volatility_defaulted", "4")]


def test_an_absent_volatility_key_writes_nothing(tmp_path):
    rep = _reporter(tmp_path)
    t = {k: v for k, v in GOOD.items() if k != "volatility"}
    r = _remember(_mem(tmp_path, Stub(_main([t]), retry_raw=_main([])), rep))
    assert r["facts"] == 1 and _degrades(rep) == []
    # a PRESENT null is a drift (row 5), distinct from absence (row 6)
    rep2 = _reporter(tmp_path, "n.log")
    _remember(_mem(tmp_path, Stub(_main([dict(GOOD, volatility=None)]), retry_raw=_main([])), rep2, "m2"))
    assert _kinds(_degrades(rep2)) == [("volatility_defaulted", "1")]


# ------------------------------------------------ V-RECORD-ORDER-ON-ERROR ----
def test_the_raising_primary_shapes_log_the_degrade_then_the_error(tmp_path):
    for i, raw in enumerate([_main(None), _main(3), _main(True)]):
        rep = _reporter(tmp_path, f"o{i}.log")
        mem = _mem(tmp_path, Stub(raw, retry_raw=_main([])), rep, f"o{i}")
        with pytest.raises(TypeError):
            _remember(mem)
        recs = _records(rep)
        assert len(recs) == 2, recs
        assert recs[0][0] == "WARNING" and recs[0][1]["degrade"] == "primary_failed" and recs[0][1]["cause"] == "shape"
        assert recs[1][0] == "ERROR" and recs[1][1]["op"] == "remember"
        assert "TypeError" in rep.config.resolved_log_path().read_text()
    # with no reporter the TypeError propagates identically and nothing is written
    mem = _mem(tmp_path, Stub(_main(None), retry_raw=_main([])), None, "none")
    with pytest.raises(TypeError):
        _remember(mem)


# ------------------------------------------------- V-NO-CONTENT-IN-LOG -------
def test_the_record_carries_no_content(tmp_path):
    sentinel = "QWERTYUIOP-SENTINEL"
    text = f"Alice moved to Berlin {sentinel}"
    class Echo(Exception): pass
    rep = _reporter(tmp_path)
    # a provider whose exception message AND whose answers echo the event text
    llm = Stub(_main([dict(GOOD, object=text, volatility=text)]), retry_raw=None, retry_raises=Echo(f"echo: {text}"))
    mem = _mem(tmp_path, llm, rep)
    mem.remember(USER, text, author=EvidenceAuthor.USER, date="2026-09-01", context=EvidenceContext.direct())
    # and one whose primary answer is prose containing the text
    mem2 = _mem(tmp_path, Stub(f"I refuse: {text}", retry_raw=_main([])), rep, "m2")
    mem2.remember(USER, text, author=EvidenceAuthor.USER, date="2026-09-01", context=EvidenceContext.direct())
    log = rep.config.resolved_log_path().read_text()
    assert _degrades(rep), "records were written"
    assert sentinel not in log and "Berlin" not in log and "Alice" not in log
    for tok in text.split():
        if len(tok) > 3:
            assert tok not in log, tok


# ------------------------------------------------ V-ONE-RECORD-PER-CALL ------
def test_volatility_records_aggregate_per_call(tmp_path):
    rep = _reporter(tmp_path)
    triples = [dict(GOOD, object=f"tool{i}", volatility="banana") for i in range(10)]
    _remember(_mem(tmp_path, Stub(_main(triples), retry_raw=_main([])), rep))
    assert _kinds(_degrades(rep)) == [("volatility_defaulted", "10")]


# ------------------------------------------------ V-RECORD-FIELDS-TOTAL ------
_FIELDS = {
    ("retry_failed", "provider_error"): {"op", "degrade", "user_hash", "cause", "msg_len", "msg_sha16"},
    ("retry_failed", "no_json"): {"op", "degrade", "user_hash", "cause", "answer_len", "answer_sha16"},
    ("retry_failed", "shape"): {"op", "degrade", "user_hash", "cause", "answer_len", "answer_sha16"},
    ("retry_failed", "no_triples_key"): {"op", "degrade", "user_hash", "cause", "answer_len", "answer_sha16"},
    ("retry_failed", "bare_array"): {"op", "degrade", "user_hash", "cause", "answer_len", "answer_sha16"},
    ("primary_failed", "shape"): {"op", "degrade", "user_hash", "cause", "answer_len", "answer_sha16"},
    ("primary_failed", "no_triples_key"): {"op", "degrade", "user_hash", "cause", "answer_len", "answer_sha16"},
    ("unparseable", "no_json"): {"op", "degrade", "user_hash", "cause", "answer_len", "answer_sha16"},
    ("unparseable", "instructions_type"): {"op", "degrade", "user_hash", "cause", "answer_len", "answer_sha16"},
    ("volatility_defaulted", None): {"op", "degrade", "user_hash", "count"},
    ("member_skipped", None): {"op", "degrade", "user_hash", "count"},
}


def test_each_record_carries_exactly_its_declared_fields(tmp_path):
    runs = [
        (Stub(_main([OFF]), retry_raises=RuntimeError("b")), None),
        (Stub(_main([OFF]), retry_raw="cannot"), None),
        (Stub(_main([OFF]), retry_raw=_main("x")), None),
        (Stub(_main([OFF]), retry_raw=json.dumps({"repairs": []})), None),
        (Stub(_main([OFF]), retry_raw=json.dumps([GOOD])), None),
        (Stub(_main("x"), retry_raw=_main([])), None),
        (Stub(json.dumps({"note": 1}), retry_raw=_main([])), None),
        (Stub("prose", retry_raw=_main([])), None),
        (Stub(_main([GOOD], instructions="x"), retry_raw=_main([])), None),
        (Stub(_main([dict(GOOD, volatility="banana")]), retry_raw=_main([])), None),
        (Stub(_main([GOOD, "junk"]), retry_raw=_main([])), None),
    ]
    seen = set()
    for i, (llm, _) in enumerate(runs):
        rep = _reporter(tmp_path, f"f{i}.log")
        _remember(_mem(tmp_path, llm, rep, f"f{i}"))
        for d in _degrades(rep):
            cls = (d["degrade"], d.get("cause"))
            assert set(d) == _FIELDS[cls], (cls, set(d) ^ _FIELDS[cls])
            seen.add(cls)
    assert seen == set(_FIELDS), set(_FIELDS) - seen


# --------------------------------------------- V-NEVER-RAISED-BY-RECORDING ---
def test_recording_never_changes_the_outcome(tmp_path):
    providers = [
        lambda: Stub(_main([OFF]), retry_raises=RuntimeError("b")),
        lambda: Stub("prose", retry_raw=_main([])),
        lambda: Stub(_main([dict(GOOD, volatility="banana")]), retry_raw=_main([])),
        lambda: Stub(json.dumps({"note": 1}), retry_raw=_main([])),
        lambda: Stub(_main([GOOD, "junk"]), retry_raw=_main([])),
    ]
    unwritable = pathlib.Path(tmp_path / "dir-not-file"); unwritable.mkdir()
    for i, mk in enumerate(providers):
        r_none = _remember(_mem(tmp_path, mk(), None, f"n{i}"))
        r_rep = _remember(_mem(tmp_path, mk(), _reporter(tmp_path, f"r{i}.log"), f"r{i}"))
        bad = Reporter(DiagnosticsConfig(log_path=str(unwritable / "x" / "v.log"), report_enabled=False))
        r_bad = _remember(_mem(tmp_path, mk(), bad, f"b{i}"))
        for r in (r_rep, r_bad):
            assert {k: v for k, v in r.items() if k != "episode"} == {k: v for k, v in r_none.items() if k != "episode"}, i


# ------------------------------------------------------- V-CLI-ATTACHES ------
def test_every_cli_memory_construction_attaches_a_reporter():
    tree = ast.parse((ROOT / "src" / "veracium" / "cli.py").read_text())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Memory"]
    assert len(calls) == 2, len(calls)
    for c in calls:
        kw = {k.arg: k.value for k in c.keywords}
        assert "diagnostics" in kw, "a CLI Memory(...) without diagnostics="
        v = kw["diagnostics"]
        assert isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr == "load_reporter"


# ------------------------------------------- §6a, the manual CLI exercise -----
def _normalize_manual(text):
    """The transcript's two run-local axes: absolute scratch paths and log
    timestamps. Everything else — the command lines, the CLI's own stdout, the
    exit codes, and every field of every degrade record — is content."""
    out = []
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        line = re.sub(r"^(\s*)\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d+ ", r"\1", line)
        line = " ".join("<path>" if tok.startswith("/") else tok for tok in line.split(" "))
        out.append(line)
    return [l for l in out if l.strip()]


def test_the_manual_cli_transcript_reproduces(tmp_path):
    """§6a's transcript is a MEASUREMENT, so it is re-run, not narrated: driving
    `specs/evidence/0039/manual_cli_driver.py` again — the shipped CLI entry point,
    the provider replaced only at the CLI's own seam — reproduces the committed
    transcript line for line once the run-local paths and timestamps are removed.
    A narrated measurement nobody asserts is the class that went stale in 0031's
    round 16; this one fails the suite instead."""
    import os
    import subprocess
    driver = ROOT / "specs" / "evidence" / "0039" / "manual_cli_driver.py"
    committed = ROOT / "specs" / "evidence" / "0039" / "manual-cli-transcript.txt"
    env = dict(os.environ)
    env.update({"XDG_STATE_HOME": str(tmp_path / "state"), "XDG_CONFIG_HOME": str(tmp_path / "config"),
                "XDG_DATA_HOME": str(tmp_path / "data"), "DB": str(tmp_path / "cli.db"),
                "PYTHONPATH": str(ROOT / "src")})
    r = subprocess.run([sys.executable, str(driver)], cwd=str(ROOT), env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert _normalize_manual(r.stdout) == _normalize_manual(committed.read_text()), (
        "the shipped CLI no longer produces the transcript §6a records:\n"
        + "\n".join(_normalize_manual(r.stdout)))
    # the normalizer is not swallowing the content: the fields it keeps are there
    kept = "\n".join(_normalize_manual(committed.read_text()))
    for token in ("degrade=retry_failed", "cause=provider_error", "msg_len=20",
                  "degrade=volatility_defaulted", "count=2", "user_hash=2bd806c97f0e"):
        assert token in kept, token


# ------------------------------------------------- §7, retention figures -----
def test_the_retention_figures_are_measured_not_recalled():
    """§7 sends the DERIVED figures to the CHANGELOG rather than stating them, so the
    binding is here: `specs/evidence/0039/retention_measurement.py` is re-run, its
    committed transcript must reproduce, and every figure the CHANGELOG's retention
    bullet quotes must be one this run produced. A figure that drifts fails the suite
    instead of standing in prose (CLAUDE.md item 11; the class cost this arc a wrong
    range once already). If a later change moves the record's size, this reds: the fix
    is to regenerate the transcript and write the new figures into a NEW CHANGELOG
    note, never to edit a released one."""
    import importlib.util
    path = ROOT / "specs" / "evidence" / "0039" / "retention_measurement.py"
    spec = importlib.util.spec_from_file_location("retention_measurement", path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    m = mod.measure()
    transcript = (ROOT / "specs" / "evidence" / "0039"
                  / "retention-measurement-transcript.txt")
    assert mod.render(m) == transcript.read_text(), (
        "the measurement no longer reproduces its committed transcript:\n" + mod.render(m))
    assert len(m["rows"]) == 10 and m["smallest"] < m["largest"]
    # The error record is asserted by PROPERTY, never by byte count: its traceback's
    # size is the interpreter's format and the checkout's path lengths (measured across
    # CI at 7, 8, 9 and 12 lines on 3.10-3.13), so a pinned number would bind this
    # evidence to one machine. What IS ours: an error record is a multi-line traceback
    # several times a degrade record, which is why degrade VOLUME is the retention
    # question (§7) and the counted kinds are one record per call.
    assert m["error_record_smallest"] >= 3 * m["largest"], (
        m["error_record_smallest"], m["largest"])
    assert m["error_record_lines"] >= 5, m["error_record_lines"]
    changelog = (ROOT / "CHANGELOG.md").read_text()
    head = changelog.split("\n## ", 2)
    assert head[1].startswith("Unreleased"), "no Unreleased section to check"
    bullets = ("\n## " + head[1]).split("\n- **")
    bullet = next((b for b in bullets if b.startswith("Log retention")), None)
    assert bullet is not None, "the Unreleased section states no retention bullet (§7)"
    text = bullet.replace("–", "-").replace("—", "-").replace("\n", " ")
    for figure in (f"{m['smallest']}-{m['largest']} bytes",
                   f"{m['window_bytes']:,} bytes",
                   f"{m['records_at_largest']:,} records",
                   f"{m['records_at_smallest']:,}"):
        assert figure in text, f"the CHANGELOG's retention bullet does not state {figure!r}"
