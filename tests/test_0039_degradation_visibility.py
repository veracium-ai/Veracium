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
    # TWO since specs/0025 §4b(1)'s wider normalization (2026-09-10): §1a path iii's
    # retry reset (`reps = []` on a non-list) and the primary site's twin, which is
    # the amendment itself — every non-list `triples` normalized to no triples rather
    # than iterated or raised. specs/0039 v14 names the second site; the census's own
    # rule is that a new site of this shape fails until the spec names it.
    assert len(resets) == 2, f"guarded literal-reset branches over parsed provider output: {resets} (the spec names TWO)"


# ------------------------------------------------------- V-ANSWER-MATRIX -----
_PRIMARY_ROWS = [
    # (row, primary raw, expected degrade kinds in order, raises)
    (1, _main([GOOD]), [], None),
    (2, _main([]), [], None),
    (3, json.dumps({"note": "none"}), [("primary_failed", "no_triples_key")], None),
    (4, _main("user uses Vim"), [("primary_failed", "shape")], None),
    (5, _main({"triples": [GOOD]}), [("primary_failed", "shape")], None),
    # rows 6 and 7 FLIPPED by the WIDER normalization rule (specs/0025 §4b(1) amended
    # 2026-09-10): every non-list `triples` is one recorded `shape` and yields no
    # triples, so these three now return zero facts exactly as rows 4 and 5 always did
    # instead of raising `TypeError` out of the loop.
    (6, _main(None), [("primary_failed", "shape")], None),
    (7, _main(3), [("primary_failed", "shape")], None),
    (7, _main(True), [("primary_failed", "shape")], None),
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
    # a provider that RETURNS None (a contract violation, not a raise): the extractor
    # is the line that raises, so the cause is `no_json` over the answer's str form —
    # never `provider_error` over the extractor's message (the handler keyed on
    # `retry_raw is None` and conflated the two; ocr review of v0.21.0, 2026-09-11)
    (11, None, [("retry_failed", "no_json")]),
    # rows 8 and 9 FLIPPED by §2e's 0025 amendment (2026-09-10): the retry now wraps a
    # bare array as the first extraction does, so these mirror primary rows 8 and 9 —
    # a bare array of dicts is a recovery attempt (measured: recovered 0 -> 1, residual
    # 1 -> 0, no record), and a bare array of scalars skips its members exactly as the
    # primary path does. Before the amendment both were ONE `retry_failed/bare_array`.
    (8, json.dumps([GOOD]), []),
    (9, json.dumps(["triples"]), [("member_skipped", "1")]),
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
    result dict and the raised class. The one asymmetric pair the matrix carried
    — rows 8 and 9, where the retry recorded `bare_array` while the first
    extraction normalized — was SETTLED by §2e's 0025 amendment (2026-09-10):
    both cells now read the same, which is the amendment's proof."""
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
def test_a_degrade_record_written_before_an_error_stays_before_it(tmp_path):
    """V-RECORD-ORDER-ON-ERROR (frozen at acceptance) — RE-INSTANCED, and that is the
    disclosure. The invariant was written for the three primary shapes that wrote a
    record and then raised `TypeError` from the loop; the WIDER normalization rule
    (specs/0025 §4b(1), amended 2026-09-10) removed that raise, so NO provider answer
    reaches this ordering any more. The property is not gone with its instance: any
    error after a degrade record in the same call must still find that record already
    in the log, ahead of it. Instanced here by failing the STORE after the record is
    written, which is a genuine error rather than a shape the amendment settled."""
    # half one: the shapes that used to raise now return, with exactly ONE record
    for i, raw in enumerate([_main(None), _main(3), _main(True)]):
        rep = _reporter(tmp_path, f"n{i}.log")
        r = _remember(_mem(tmp_path, Stub(raw, retry_raw=_main([])), rep, f"n{i}"))
        assert r["facts"] == 0, raw
        recs = _records(rep)
        assert len(recs) == 1 and recs[0][0] == "WARNING", recs
        assert recs[0][1]["degrade"] == "primary_failed" and recs[0][1]["cause"] == "shape"
        assert "TypeError" not in rep.config.resolved_log_path().read_text()
    # half two: the ordering itself, on a call that records and THEN fails. The retry
    # writes its record before the parse loop reaches the store, so failing the edge
    # write puts a genuine error after a genuine degrade record in one call.
    def _ordered(reporter, name):
        mem = _mem(tmp_path, Stub(_main([OFF]), retry_raw="cannot"), reporter, name)
        with pytest.MonkeyPatch.context() as mp:
            def fail(*a, **k):
                raise RuntimeError("store failure after the record")
            mp.setattr(ingest_mod, "apply_supersession", fail)
            with pytest.raises(RuntimeError):
                _remember(mem)
    rep = _reporter(tmp_path, "order.log")
    _ordered(rep, "order")
    recs = _records(rep)
    assert len(recs) == 2, recs
    assert recs[0][0] == "WARNING" and recs[0][1]["degrade"] == "retry_failed"
    assert recs[1][0] == "ERROR" and recs[1][1]["op"] == "remember"
    assert "RuntimeError" in rep.config.resolved_log_path().read_text()
    # and with no reporter the error propagates identically, nothing written
    _ordered(None, "none")


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
    # `bare_array` stays in §2a's CLOSED vocabulary (the spec is accepted and frozen)
    # but §2e's 0025 amendment made it unproducible: it was the label for an
    # `AttributeError` from `.get` on a list, and no list now reaches that call.
    # Asserted, not assumed — see test_the_retry_normalizes_a_bare_array_as_the_first_extraction_does.
    assert ("retry_failed", "bare_array") not in seen


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

def _changelog_section_carrying_0039():
    """The CHANGELOG section a HOST reads for this change: the top section, which is
    `Unreleased` until the release that carries it is cut and that release's
    `<version> — <date>` heading afterwards. Binding the heading's TEXT made the two
    carrier tests fail by construction at the 0.21.0 cut (2026-09-11); what the tests
    guard is the section's CONTENT, so the heading is checked for FORM only."""
    changelog = (ROOT / "CHANGELOG.md").read_text()
    section = changelog.split("\n## ", 2)[1]
    heading = section.split("\n", 1)[0]
    assert heading == "Unreleased" or re.fullmatch(r"\d+\.\d+\.\d+ — \d{4}-\d{2}-\d{2}", heading), (
        "the top CHANGELOG section is neither Unreleased nor a release heading: %r" % heading)
    assert "`extraction_unusable`" in section, (
        "the top CHANGELOG section (%s) does not carry the 0039/0025 change" % heading)
    return heading, section


def test_the_changelog_section_helper_refuses_a_foreign_heading_and_a_missing_change(tmp_path, monkeypatch):
    """Negative controls for `_changelog_section_carrying_0039`: a top section whose
    heading is neither Unreleased nor a release heading is refused, and a release-shaped
    heading over a section that does not carry the field is refused too. Both mutants
    are planted in a copy; the real file is read once to prove the helper passes it."""
    real = (ROOT / "CHANGELOG.md").read_text()
    heading, section = _changelog_section_carrying_0039()
    assert heading == "Unreleased" or heading[0].isdigit()
    top = real.split("\n## ", 2)
    for label, mutant in (
        ("foreign heading", real.replace("\n## " + heading, "\n## Notes for hosts", 1)),
        ("release heading, change missing",
         "\n## ".join([top[0], "9.9.9 — 2099-01-01\n\nnothing here", top[2]])),
    ):
        (tmp_path / "CHANGELOG.md").write_text(mutant)
        monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
        try:
            with pytest.raises(AssertionError):
                _changelog_section_carrying_0039()
        finally:
            monkeypatch.undo()
    assert _changelog_section_carrying_0039()[0] == heading


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
    # The bound is derived from the CI MATRIX, not from this machine: across 3.10-3.13
    # the smallest error record measured anywhere was 439 bytes over 7 lines against a
    # 155-byte largest degrade record, a factor of 2.8; the largest was 714 over 12
    # lines. A bound read off one interpreter is how this assertion was wrong the first
    # time. (The instance moved on 2026-09-10 — the amendment removed the raise those
    # measurements came from, so the error record now comes from a provider exception,
    # a deeper traceback still — and the bound is deliberately left at the older,
    # tighter figure rather than re-tightened to today's machine.)
    assert m["error_record_bytes"] >= 2 * m["largest"], (
        m["error_record_bytes"], m["largest"])
    assert m["error_record_lines"] >= 5, m["error_record_lines"]
    heading, section = _changelog_section_carrying_0039()
    bullets = ("\n## " + section).split("\n- **")
    bullet = next((b for b in bullets if b.startswith("Log retention")), None)
    assert bullet is not None, f"the CHANGELOG section {heading!r} states no retention bullet (§7)"
    text = bullet.replace("–", "-").replace("—", "-").replace("\n", " ")
    for figure in (f"{m['smallest']}-{m['largest']} bytes",
                   f"{m['window_bytes']:,} bytes",
                   f"{m['records_at_largest']:,} records",
                   f"{m['records_at_smallest']:,}"):
        assert figure in text, f"the CHANGELOG's retention bullet does not state {figure!r}"


# ------------------------------- specs/0025 §4b(1) as amended (0039 §2e) -----
_BARE_ARRAYS = {
    "empty": [],
    "of repairs": [GOOD],
    "of scalars": ["triples"],
    "of several scalars": [1, 2],
    "of empty dicts": [{}],
}


def test_the_retry_normalizes_a_bare_array_as_the_first_extraction_does(tmp_path):
    """specs/0025 §4b(1), AMENDED 2026-09-10 (drafted as specs/0039 §2e, on the owner's
    word). `extract_json` returns a bare JSON array "as a fallback for the caller to
    normalize"; the first extraction normalized it and the retry did not, so one of the
    function's two callers did not honour the documented obligation of the function it
    calls. Three things are asserted here, all measured:

    (a) THE REPAIR NOW LANDS. A retry answering with a bare array of repairs recovers
        the failing triple and the STORED relation is the registry member the retry
        named, where before the amendment it was `unclassified` with `recovered=0`.
        This is the outcome the amendment exists for -- 0025 §4b(1) is "where the 35%
        is actually recovered" -- and it is a stored-state change, not a log change.
    (b) THE TWO CALLERS AGREE on the wrapping and on what follows from it, for every
        bare-array shape but one, and that one is a DESIGNED difference rather than a
        surviving asymmetry: a dict member matching no failing occurrence is a DISCARD
        under 0025's discard rule ("the retry may repair relations, never add facts"),
        so `[{}]` skips a member on the first extraction and discards on the retry.
    (c) `cause=bare_array` IS NOW UNPRODUCIBLE. It labelled an `AttributeError` from
        `.get` on a list; no list reaches that call. Asserted against a forced list
        return, not only against answers that happen to parse as one."""
    def _run(primary, retry, name):
        rep = _reporter(tmp_path, f"{name}.log")
        mem = _mem(tmp_path, Stub(primary, retry_raw=retry), rep, name)
        r = _remember(mem)
        rels = sorted(x[0] for x in mem.store._conn.execute("SELECT relation FROM edges"))
        return r, rels, _kinds(_degrades(rep))

    # (a)
    r, rels, recs = _run(_main([OFF]), json.dumps([GOOD]), "a")
    assert (r["recovered"], r["residual"]) == (1, 0), r
    assert rels == ["uses_tool"], rels
    assert "unclassified" not in rels
    assert recs == [], recs

    # (b)
    designed_difference = {"of empty dicts"}
    for name, shape in _BARE_ARRAYS.items():
        _, _, primary_recs = _run(json.dumps(shape), _main([]), f"p-{name}")
        _, _, retry_recs = _run(_main([OFF]), json.dumps(shape), f"r-{name}")
        assert not any(c == "bare_array" for _, c in retry_recs), (name, retry_recs)
        if name in designed_difference:
            assert primary_recs == [("member_skipped", "1")] and retry_recs == [], (
                name, primary_recs, retry_recs)
        else:
            assert primary_recs == retry_recs, (name, primary_recs, retry_recs)

    # (c) any list the extractor can return is wrapped, not just the ones a real
    # answer produces: force the callee to return a list of a shape no provider
    # would emit and the retry still records nothing about a bare array
    for forced in ([], [GOOD], [{"a": 1}], [None]):
        rep = _reporter(tmp_path, f"c{len(forced)}{forced!r:.4}.log")
        mem = _mem(tmp_path, Stub(_main([OFF]), retry_raw=_main([])), rep, f"c{forced!r:.4}")
        with pytest.MonkeyPatch.context() as mp:
            calls = {"n": 0}
            real = ingest_mod.extract_json
            def fake(text):
                calls["n"] += 1
                return forced if calls["n"] > 1 else real(text)   # the retry's call only
            mp.setattr(ingest_mod, "extract_json", fake)
            _remember(mem)
            assert calls["n"] == 2, "the retry did not reach the extractor"
        assert not any(c == "bare_array" for _, c in _kinds(_degrades(rep))), forced


# ------------------- specs/0025 §4c as amended: the DEFAULT host's carrier ----
def _default_host(tmp_path, primary, name):
    """A host exactly as the library documents its default: no diagnostics reporter,
    no callback. This is what an embedding host gets unless it opts in."""
    mem = _mem(tmp_path, Stub(primary, retry_raw=_main([])), None, name)
    return _remember(mem)


def test_a_default_host_can_tell_a_malformed_answer_from_an_empty_one(tmp_path):
    """specs/0025 §4c, AMENDED for 0039 round-5 R5-1 (the owner's word, 2026-09-11:
    "Go with the new field"). The round-5 reviewer showed the narrow fix's flag meant
    neither thing it could mean: an all-invalid list stayed silent, and the flag fired
    on a response whose triples were usable but which 0038's instructions rule
    rejected. `extraction_unusable` is the OUTCOME, present on every path as a bool:
    the primary extraction produced no shape-valid triple — the answer rejected whole,
    a missing or non-list `triples`, or a non-empty list none of whose members passed
    the shape guard. A legitimately empty list is False. `unparseable` is narrow again.

    Every row the reviewer tabled, plus the one they stated in prose, plus the two
    edges that bound the definition: a MIXED list (one usable member) is False, and a
    list whose members passed the shape guard but were all refused for another reason
    is False — those have their own counters and are not this field's claim."""
    def r(primary, name):
        return _default_host(tmp_path, primary, name)
    empty = r(_main([]), "empty")
    good = r(_main([GOOD]), "good")
    assert empty["extraction_unusable"] is False and empty["facts"] == 0
    assert good["extraction_unusable"] is False and good["facts"] == 1
    assert "unparseable" not in empty and "unparseable" not in good
    # the reviewer's table, and the prose row
    unusable = {
        "all-invalid list": _main([{}, "junk", 7, None]),
        "missing triples": json.dumps({"note": 1}),
        "non-list: null": _main(None), "non-list: number": _main(5),
        "non-list: boolean": _main(True), "non-list: string": _main("x"),
        "non-list: dict": _main({"a": 1}),
        "no JSON at all": "I refuse.",
        "usable triples, rejected by the instructions rule": _main([GOOD], instructions="x"),
    }
    for name, raw in unusable.items():
        res = r(raw, name.replace(" ", "_").replace(":", "").replace(",", ""))
        assert res["facts"] == 0, name
        assert res["extraction_unusable"] is True, f"{name}: not marked"
    # `unparseable` is narrow again: only the two rejected-whole rows carry it
    assert r("I refuse.", "u1").get("unparseable") is True
    assert r(_main([GOOD], instructions="x"), "u2").get("unparseable") is True
    assert "unparseable" not in r(_main([{}, "junk"]), "u3")
    assert "unparseable" not in r(_main(None), "u4")
    # the definition's edges: a mixed list has a usable member; an all-refused list
    # (subjects off the grammar) passed the shape guard and is counted elsewhere
    mixed = r(_main([GOOD, "junk", 7]), "mixed")
    assert mixed["extraction_unusable"] is False and mixed["facts"] == 1
    refused = r(_main([dict(GOOD, subject="user|person:x")]), "refused")
    assert refused["extraction_unusable"] is False and refused["facts"] == 0
    assert refused["subject_refused"] == 1
    # research's fourth row, the most plausible place for a later silent flip: some
    # members passed the guard and were REFUSED, others FAILED the guard, and nothing
    # was stored. False, correctly — a shape-valid triple existed, so X17's True clause
    # does not apply, and the counters carry why. Anyone who reads "nothing stored and
    # every member skipped or refused" as unusable would change this row.
    both = r(_main([dict(GOOD, subject="user|person:x"), "junk"]), "refused-and-skipped")
    assert both["extraction_unusable"] is False and both["facts"] == 0
    assert both["subject_refused"] == 1
    # three more guard-failure member shapes, each alone in a list, each True: a LIST
    # member, a dict missing a key, and a dict of EMPTY strings — the last passes the
    # type half of the guard and fails only its truthiness half, which is the row that
    # proves the guard is both tests rather than the type test alone
    for name, member in (("list member", [GOOD]), ("missing key", {"subject": "user", "relation": "uses_tool"}),
                         ("empty strings", {"subject": "", "relation": "", "object": ""})):
        res = r(_main([member]), name.replace(" ", "_"))
        assert res["extraction_unusable"] is True and res["facts"] == 0, name
    # present on EVERY path, as a bool — 0025 §4c: an absent key is not a zero
    for res in (empty, good, mixed, refused, both):
        assert isinstance(res["extraction_unusable"], bool)


def test_the_new_field_reaches_the_mcp_host_and_not_telemetry(tmp_path):
    """Two consumers, dispositioned: the MCP tool result CARRIES the field (an MCP
    host is exactly a default host, and 0031 §4d strips counters a model could learn
    to probe from, not a boolean that says an answer was unusable — `unparseable` was
    never stripped either); the opt-in telemetry event does NOT carry it and its
    `unparseable` counter keeps the narrow meaning (0 for an all-invalid list), which
    is the widening the reviewer refused, reverted and pinned."""
    from veracium import mcp_server as m
    import veracium as v
    mem = _mem(tmp_path, Stub(_main([{}, "junk"]), retry_raw=_main([])), None, "mcp")
    tool = m.remember_impl(mem, USER, TEXT)
    assert tool["extraction_unusable"] is True
    assert "unparseable" not in tool
    # V-MCP-RESULT-CARRIES-ONE (0039 v17, replacing the retired V-MCP-RESULT-UNCHANGED,
    # whose inherited check asserted only that the counters are STRIPPED and so stayed
    # green while a field was gained): the tool result's key set is EXACTLY the ingest
    # result's keys minus the operator counters — a second added field fails here, and
    # the new field's presence and every counter's absence are asserted, not inherited
    full = _remember(_mem(tmp_path, Stub(_main([{}, "junk"]), retry_raw=_main([])), None, "full"))
    assert set(tool) == set(full) - set(m._OPERATOR_ONLY), sorted(set(tool) ^ (set(full) - set(m._OPERATOR_ONLY)))
    assert "extraction_unusable" in tool and not (set(m._OPERATOR_ONLY) & set(tool))
    seen = []
    class _Collector:
        def record(self, event, fields, **kw):
            seen.append((event, fields))
        def __getattr__(self, name):
            return lambda *a, **k: None
    mem2 = v.Memory(llm=Stub(_main([{}, "junk"]), retry_raw=_main([])),
                    config=MemoryConfig(db_path=str(tmp_path / "t.db"), wiki_recompile_after_writes=0),
                    telemetry=_Collector())
    _remember(mem2)
    fields = [f for e, f in seen if e == "ingest"][0]
    assert fields["unparseable"] == 0 and "extraction_unusable" not in fields


# --------------------- round-5 R5-2: records survive a later store failure ----
def _fail_at(monkeypatch, where):
    """Force a genuine error at a named effectful store seam. The seam MATTERS: an
    override placed after the emission point exonerates a broken ordering (research's
    first attempt failed `add_episode` and the records appeared), so the seam is named
    in every case rather than left to the reader."""
    def boom(*a, **k):
        raise RuntimeError(f"store failure at {where}")
    if where == "apply_supersession":
        monkeypatch.setattr(ingest_mod, "apply_supersession", boom)
    elif where == "add_episode":
        real_init = SqliteStore.__init__
        def init(self, *a, **k):
            real_init(self, *a, **k)
            self.add_episode = boom
        monkeypatch.setattr(SqliteStore, "__init__", init)
    else:
        raise ValueError(where)


def test_counted_records_are_written_before_the_first_store_write(tmp_path, monkeypatch):
    """Round-5 R5-2 (the reviewer's counterexample, reproduced at the pin before a line
    moved): `member_skipped` and `volatility_defaulted` were emitted AFTER the storage
    loop, so a store failure inside it — a genuine error `_on_error` records with its
    traceback — took the promised degrade record with it: V-DEGRADE-RECORDED's one
    record per occurrence was ZERO on that path, and V-RECORD-ORDER-ON-ERROR was
    instanced only on the early-emitted retry site. Every degrade record is now
    computed and emitted before the first effectful store operation. Asserted at the
    seam the reviewer used (the edge write) AND at the one before it (the episode
    write), which the reviewer did not test and which the class includes."""
    # every answer carries an episode, so the episode seam actually WRITES (an answer
    # with no episode never reaches add_episode, and a seam that never fires reads as
    # a pass — the first draft of this test did exactly that)
    cases = [
        ("member_skipped", _main([GOOD, "junk"], episode="I use Vim."), "1"),
        ("volatility_defaulted", _main([dict(GOOD, volatility="banana")], episode="I use Vim."), "1"),
        ("primary_failed", _main({"a": 1}, episode="I use Vim."), "shape"),
    ]
    for where in ("apply_supersession", "add_episode"):
        for kind, raw, detail in cases:
            if where == "apply_supersession" and kind == "primary_failed":
                continue        # a dict `triples` reaches no edge write; the episode seam covers it
            with pytest.MonkeyPatch.context() as mp:
                _fail_at(mp, where)
                rep = _reporter(tmp_path, f"{where}-{kind}.log")
                mem = _mem(tmp_path, Stub(raw, retry_raw=_main([])), rep, f"{where}-{kind}")
                with pytest.raises(RuntimeError):
                    _remember(mem)
            recs = _records(rep)
            assert [r[0] for r in recs] == ["WARNING", "ERROR"], (where, kind, recs)
            assert recs[0][1]["degrade"] == kind and recs[0][1].get("count", recs[0][1].get("cause")) == detail, (where, kind, recs[0])
            assert recs[1][1]["op"] == "remember"
    # the control: the same inputs with no failure still write exactly one record each
    for kind, raw, detail in cases:
        rep = _reporter(tmp_path, f"ok-{kind}.log")
        _remember(_mem(tmp_path, Stub(raw, retry_raw=_main([])), rep, f"ok-{kind}"))
        assert _kinds(_degrades(rep)) == [(kind, detail)], kind


# ------------------ round-6 R6-1: the carriers agree with the implementation ----
def _lint_module():
    """The register AND the lint's own normaliser, loaded by path: the test matches
    the way `specs/lint_withdrawn.py` matches (punctuation-insensitive, whitespace
    collapsed) or the two checks over one artifact could disagree."""
    import importlib.util, sys
    if str(ROOT / "specs") not in sys.path:
        sys.path.insert(0, str(ROOT / "specs"))
    spec = importlib.util.spec_from_file_location("lint_withdrawn", ROOT / "specs" / "lint_withdrawn.py")
    lint = importlib.util.module_from_spec(spec); spec.loader.exec_module(lint)
    spec2 = importlib.util.spec_from_file_location("withdrawn_phrases", ROOT / "specs" / "withdrawn_phrases.py")
    reg = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(reg)
    reg._normalise = lint._normalise
    return reg


def _alternatives(pattern):
    """Split a regex on its TOP-LEVEL `|` only (depth 0, outside character classes,
    escapes honoured) — the branches a reader sees as separate entries."""
    out, cur, depth, esc, in_class = [], "", 0, False, False
    for ch in pattern:
        if esc:
            cur += ch; esc = False; continue
        if ch == "\\":
            cur += ch; esc = True; continue
        if in_class:
            cur += ch; in_class = ch != "]"; continue
        if ch == "[":
            in_class = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "|" and depth == 0:
            out.append(cur); cur = ""; continue
        cur += ch
    return out + [cur]


def test_the_alternation_splitter_splits_only_at_depth_zero():
    assert _alternatives("a|b") == ["a", "b"]
    assert _alternatives("(a|b)c|d[|]e") == ["(a|b)c", "d[|]e"]
    assert _alternatives(r"x\|y|z") == [r"x\|y", "z"]
    assert _alternatives("single") == ["single"]


def test_the_withdrawn_entries_for_this_spec_fire_on_a_marker_stripped_copy(tmp_path):
    """The positive control the register's own discipline demands at a spec's first
    registration: an entry that cannot fire is indistinguishable from one that is
    satisfied. Strip every WITHDRAWN/OBSOLETE marker from a copy of the spec, so its
    history quotes become live text, and every 0039 entry must match at least once;
    and against the REAL spec, none may match a live (unmarked) paragraph — which is
    the assertion `specs/lint_withdrawn.py` makes over the whole tree, run here on this
    file alone so the binding is local to the spec it protects."""
    mod = _lint_module()
    entries = [e for e in mod.WITHDRAWN if e[0].startswith("0039-")]
    # three at v17; round 7 added the subject-scoped variants and the conditional-raise
    # wording — five, each named so a silently dropped entry is a red here
    assert sorted(e[0] for e in entries) == sorted([
        "0039-non-list-triples-still-raise", "0039-bare-array-retry-attributeerror",
        "0039-mcp-result-gains-no-field", "0039-result-surface-unchanged-variants",
        "0039-conditional-raise-after-record"]), [e[0] for e in entries]
    spec_text = (ROOT / "specs" / "0039-degradation-visibility.md").read_text()
    stripped = mod._normalise(spec_text.replace("OBSOLETE", "").replace("WITHDRAWN", ""))
    for rid, pat, _why, _where in entries:
        assert re.search(pat, stripped), f"{rid}: fires nowhere even with the history markers stripped — a dead entry"
    # PER-BRANCH, for the entries that quote HISTORY (the variants entries are open
    # backstops and may name wording that never appeared): an alternation whose branch
    # cannot fire is a dead entry hiding inside a live one — the bare-array entry
    # carried two such branches for three rounds (ocr review of v0.21.0, 2026-09-11)
    for rid, pat, _why, _where in entries:
        if rid in ("0039-bare-array-retry-attributeerror", "0039-non-list-triples-still-raise",
                   "0039-conditional-raise-after-record"):
            for branch in _alternatives(pat):
                assert re.search(branch, stripped, re.I), f"{rid}: dead branch {branch!r}"
    # the live half: no unmarked paragraph of the real spec matches, under the lint's normalisation
    for para in re.split(r"\n\s*\n", spec_text):
        if "OBSOLETE" in para or "WITHDRAWN" in para:
            continue
        flat = mod._normalise(para)
        for rid, pat, _why, _where in entries:
            m = re.search(pat, flat)
            assert not m, f"{rid} matches LIVE text: {m.group(0)!r}"


def test_the_host_facing_carriers_state_the_current_contract(tmp_path):
    """Round-6 R6-1, the half the house lint cannot reach: `specs/lint_withdrawn.py`
    reads specs/ and tests/, and the two carriers a HOST reads — the CHANGELOG's
    Unreleased section and docs/api.md — are outside it. Both must state the new field
    with its semantics, and neither may carry the superseded claims that stood beside
    the new ones at round 6 ("gain no field", "still raises"). The absent-phrase half is
    checked against the register's own patterns so the two halves cannot drift apart."""
    mod = _lint_module()
    entries = [e for e in mod.WITHDRAWN if e[0].startswith("0039-")]
    heading, unreleased = _changelog_section_carrying_0039()
    api = (ROOT / "docs" / "api.md").read_text()
    for name, text in ((f"CHANGELOG {heading}", unreleased), ("docs/api.md", api)):
        assert "`extraction_unusable`" in text, f"{name}: the field is not stated"
        assert "no shape-valid triple" in text, f"{name}: the field's semantics are not stated"
        assert "legitimately empty" in text, f"{name}: the False case is not stated"
        for rid, pat, _why, _where in entries:
            m = re.search(pat, mod._normalise(text))
            assert not m, f"{name}: superseded claim {rid} still stated: {m.group(0)!r}"
        # the two literal phrasings the reviewer quoted, beyond the register
        for obsolete in ("gain no field", "gains no field", "still raises (a", "non-list path still raises"):
            assert obsolete not in text, f"{name}: {obsolete!r}"
    # the CHANGELOG is ONE account: the MCP result is described once and consistently
    assert "MCP `remember`\n  tool result" in unreleased or "MCP `remember` tool result" in unreleased


# ---- round-7 R7-1 / round-8 R8-1: the result surface — DERIVED census, DECLARED classes ----
# v18 verified eight hand-chosen anchors and never that they were the complete set:
# closed by assertion, not by construction (round 8's finding, research's words about
# research's own proposal). This is the ratchet's pattern instead: DERIVE every value
# occurrence from the live text, DECLARE what is excluded as history and WHY, CLASSIFY
# each occurrence's site by its FORM under §2e's carrier rule, FAIL on the rest.
_VALUE_VOCAB = re.compile(
    r"extraction_unusable|outcome boolean|one outcome|carries exactly ONE field|carries that one field|"
    r"gains? one (field|key)|key set gains", re.I)
# WITHDRAWN phrases, listed here to be REFUSED — this comment is the house lint's marker
_SUBJECT_VOCAB = re.compile(
    r"what (the |its |every )?(ingest |tool )?results? carr(y|ies)|tool result|result's key set|"
    r"return values?|what (it|the host) learns from the result", re.I)
# history, excluded from the LIVE text — each exclusion with its reason
_HISTORY = [
    ("OBSOLETE/WITHDRAWN spans", r"\(\*(?:OBSOLETE|WITHDRAWN).*?\*\)", "a marked verbatim quote asserts what was said, not what is"),
    ("struck invariant rows", r"^\| ~~\*\*V-[^\n]*$", "a retired row is history by construction"),
    ("the header table", r"^\| \*\*(Version|Author / session|Status|Internal reviewers|External review)\*\* \|[^\n]*$", "the arc's record, not the contract"),
    ("the generated closure block", r"<!-- GENERATED:review-closure -->.*?<!-- /GENERATED:review-closure -->", "generated from the ledger; findings quote old text"),
]
# the three ASSERTING forms (§2e's carrier rule): the site may carry the value
# the two contract matrices ONLY — §1's behaviour table is a dated measurement (history), not a
# fourth form: admitting it by form would admit an undated restatement there too (research, round 8)
_ASSERTING_SECTIONS_WITH_TABLES = ("2c-i.", "2c-ii.")


def _live_spec_text():
    text = (ROOT / "specs" / "0039-degradation-visibility.md").read_text()
    for _name, pat, _why in _HISTORY:
        text = re.sub(pat, "", text, flags=re.S | re.M)
    return text


def _sites(text):
    """Every paragraph of the live text with its section heading; table rows are their
    own sites (a row asserts on its own, and one table mixes asserting rows with none)."""
    sec = "(preamble)"
    for para in re.split(r"\n\s*\n", text):
        head = re.search(r"^(#+ .*)$", para, re.M)
        if head:
            sec = head.group(1).strip("# ")
        if para.lstrip().startswith("|"):
            for row in para.split("\n"):
                if row.startswith("|") and not row.startswith("|---"):
                    yield sec, row
        else:
            yield sec, para


def _asserts_the_surface(sec, site):
    """The carrier rule, as a function of a site's FORM — never a list of anchors."""
    if "**THE RESULT SURFACE, STATED ONCE" in site:
        return True                                        # §2e's statement itself
    if re.match(r"^\| \*\*V-[A-Z0-9-]+\*\* \|", site):
        return True                                        # a §6 invariant row asserts a property
    if site.startswith("|") and any(sec.startswith(s) for s in _ASSERTING_SECTIONS_WITH_TABLES):
        return True                                        # a behaviour-table / matrix row asserts an outcome
    return False


def _census(text):
    """(occurrences that may carry the value, occurrences that may NOT) — derived."""
    allowed, refused = [], []
    for sec, site in _sites(text):
        for m in _VALUE_VOCAB.finditer(site):
            (allowed if _asserts_the_surface(sec, site) else refused).append((sec, m.group(0), site[:100]))
    return allowed, refused


def test_the_result_surface_is_stated_once_and_every_other_site_points_to_it():
    """Round-8 R8-1. Two halves, RANKED by what each is keyed on (research, round 8,
    reversing their round-7 ranking): PRIMARY — the value census, keyed on an IDENTIFIER.
    `extraction_unusable` has one spelling, so a token set over the field's name is
    complete by construction: every occurrence is DERIVED from the live text and must
    sit in an asserting form (§2e's statement, a §6 invariant row, a behaviour-table or
    matrix row) or the test fails and names it. BACKSTOP — the must-point check, keyed
    on PROSE: a live discussion that names the result surface must point to §2e, and
    "names the result surface" is an English judgement no token list closes — a
    paragraph saying "what callers receive" escapes it. Incomplete by construction,
    kept because it is cheap, ranked second so its green is not read as proof. The
    general rule under both rounds: a check is closed when it keys on an identifier and
    open when it keys on English. THE CHECKER'S OWN LIMIT: it tests the rule's
    CONSEQUENCE — a site's FORM — not the rule; form is a proxy for assertion-ness. An
    invariant row that merely mentions the field in passing is admitted here and
    violates §2e's rule; a green census says every occurrence sits in an asserting form,
    never that every occurrence is load-bearing. The history exclusions are declared
    with reasons."""
    text = _live_spec_text()
    assert text.count("**THE RESULT SURFACE, STATED ONCE") == 1
    assert text.count("**THE CARRIER RULE (v19") == 1
    allowed, refused = _census(text)
    assert allowed, "the census found no asserting site at all — the vocabulary or the rule moved"
    assert not refused, "value restated outside an asserting site:\n" + "\n".join(f"  [{s}] {tok!r}: {site!r}" for s, tok, site in refused)
    # the positive half: discussions that name the subject point to §2e
    unpointed = []
    for sec, site in _sites(text):
        if _asserts_the_surface(sec, site):
            continue
        if _SUBJECT_VOCAB.search(site) and "§2e" not in site:
            unpointed.append((sec, site[:100]))
    assert not unpointed, "a discussion names the result surface without pointing to §2e:\n" + "\n".join(f"  [{s}] {site!r}" for s, site in unpointed)


def test_the_census_refuses_a_planted_restatement_and_admits_a_planted_invariant():
    """RULE ZERO, the reviewer's mutation, both directions: the census is judging the
    criterion's consequence, not a list. A value planted into a §8 prose paragraph must
    FAIL it; the same value planted into a new `| **V-…** |` row must be ADMITTED by
    it — which proves the checker admits invariant rows, NOT that it admits only
    asserting ones (see the docstring above: form is a proxy); and the history
    exclusion is exercised — the same value inside an OBSOLETE span is not counted."""
    text = _live_spec_text()
    _, refused0 = _census(text)
    assert not refused0
    # (a) a prose restatement in §8
    i = text.index("## 8. Claims and limits")
    planted = text[:i] + "## 8. Claims and limits\n\nThe result now carries `extraction_unusable: True` on every failure.\n\n" + text[i + len("## 8. Claims and limits"):]
    _, refused = _census(planted)
    assert any(tok.lower() == "extraction_unusable" and s.startswith("8.") for s, tok, _ in refused), refused
    # (b) a new invariant row that carries the value: admitted by the rule, not by a list
    j = text.index("| **V-RESULT-SHAPE-EXACT** |")
    planted2 = text[:j] + "| **V-PLANTED** | the result carries `extraction_unusable` | a check | a node |\n" + text[j:]
    allowed2, refused2 = _census(planted2)
    assert not refused2 and any(site.startswith("| **V-PLANTED**") for _, _, site in allowed2)
    # (c) the history exclusion: an OBSOLETE span carrying the value is not counted
    raw = (ROOT / "specs" / "0039-degradation-visibility.md").read_text()
    k = raw.index("## 8. Claims and limits")
    planted3 = raw[:k] + "## 8. Claims and limits\n\nHistory: (*OBSOLETE at v13: \"gains one field, `extraction_unusable`\"*) — and nothing live.\n\n" + raw[k + len("## 8. Claims and limits"):]
    stripped = planted3
    for _name, pat, _why in _HISTORY:
        stripped = re.sub(pat, "", stripped, flags=re.S | re.M)
    _, refused3 = _census(stripped)
    assert not refused3, refused3
