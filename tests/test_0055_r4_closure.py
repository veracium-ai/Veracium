"""specs/0055, round 4's RETURN (build review; coordination a421b28, body sha16 6821acc3756f2082): the closure of R4-01 to
R4-06 and A1, with research's stage-1 sweeps S1 to S3 (research acacf746).

Each finding was a route or a carrier the build's checks did not list, so each fix here is held by a check that
ENUMERATES ITS DOMAIN from the code or the live schema, not by a prose list (research's addition 1):
  R4-01  every public `Memory` parameter that admits a string (§2c-ii A5's rule, read by `inspect`), driven with a
         non-`str` value: it is never admitted further than the same value as a `str`; the screened fields (read from
         the `_cred_ingress` calls themselves) refuse it before any provider call or write.
  R4-02  every read of the cached wiki (`get_wiki`, located by `ast`) is classed; the served one masks a fresh body,
         through the library, MCP and the adapter binding, with the cache path ON (`wiki_recompile_after_writes` > 0).
  R4-03  every served tool (the server's own tool list) and the library's record reports, over a store holding
         shaped ids, with positive controls: no shaped id leaves; an ordinary id is kept.
  R4-04  every string-holding column of every per-user table (the live schema) and every field of the edge and episode
         records and their journals: a planted shape is found; the store-level table set is pinned to the schema.
  R4-05  a real invalid import through the CLI, an exception with its own formatter, `__notes__`, and a caller dict key
         in a validation location: no input reaches the formatted traceback or the outward text.
  R4-06  cuts inside a structural prefix, a body, a labelled value and multibyte text: the tail sent never holds the
         remainder of a value whose recognition the cut destroyed; the payload limit holds.
  A1     the finder's report names maintain()'s pool key as a declared opaque domain.

The reviewer's 22 independent cases (15 RED at 81e33ba4, 7 controls) are carried here, adapted to this suite's
helpers. No structural test token appears literally: vectors.py assembles them at run time.
"""
from __future__ import annotations

import ast
import asyncio
import contextlib
import importlib.util
import inspect
import io
import json
import os
import sqlite3
import sys
import traceback
from pathlib import Path

import pytest

from veracium import EvidenceAuthor, EvidenceContext, Memory, MemoryConfig
from veracium import credentials as C

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


V = _load("_0055_vectors_r4", ROOT / "specs" / "evidence" / "0055" / "vectors.py")
T = _load("_0055_invariants_r4", ROOT / "tests" / "test_0055_invariants.py")
TOKEN = V.GH                     # one assembled structural token (the reviewer's fixture)


def _needs_mcp():
    """The served-surface cells (R4-02 through MCP and the adapter, R4-03's tool sweep) need the MCP SDK (the `mcp`
    extra); the pydantic-floor lane installs none, and only those cells skip there."""
    pytest.importorskip("mcp")


def _leaks(db: str, stub) -> set:
    out = set()
    if TOKEN in T._dump(db):
        out.add("store")
    if any(TOKEN in str(p) for _role, p in stub.prompts):
        out.add("provider")
    return out


# ==== R4-01: identifier admission by TYPE, over §2c-ii A5's whole census ===========================================

def _a5_rows() -> list:
    """§2c-ii A5's rule, by `inspect`: every public `Memory` method, every parameter but `self`/`user_id` whose
    annotation admits `str` (or has none). Research's script reads the same rule by `ast`."""
    rows = []
    for name, fn in sorted(inspect.getmembers(Memory, predicate=inspect.isfunction)):
        if name.startswith("_"):
            continue
        for p in inspect.signature(fn).parameters.values():
            if p.name in ("self", "user_id") or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                continue
            ann = p.annotation
            ann = "<none>" if ann is inspect.Parameter.empty else (ann if isinstance(ann, str) else repr(ann))
            if ann == "<none>" or "str" in ann.replace("Store", ""):
                rows.append((name, p.name))
    return rows


def _screened() -> dict:
    """The fields each method screens, read from its own `_cred_ingress(..., ids=..., free=...)` call (`ast`)."""
    tree = ast.parse((ROOT / "src" / "veracium" / "__init__.py").read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Memory")
    out: dict = {}
    for fn in cls.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "_cred_ingress":
                for kw in node.keywords:
                    if kw.arg in ("ids", "free"):
                        out.setdefault(fn.name, set()).update(e.elts[0].value for e in kw.value.elts)
    return out


# `record_procedure` returns `record_procedure_report(...)["summary"]`: the screen is the twin's (I20)
_DELEGATES = {"record_procedure": "record_procedure_report"}


def _callee_screened() -> dict:
    """The fields a CALLEE screens rather than the method's own `_cred_ingress` (round 5): D3's
    `_d3_legacy_source_or_refuse(user_id, origin, source_id, op)`, reached through `_source_revocation`. Read by `ast`:
    every public method that calls `_source_revocation`, with D3's own parameters (all but `self`, `user_id`, `op`)."""
    tree = ast.parse((ROOT / "src" / "veracium" / "__init__.py").read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Memory")
    fns = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
    d3 = [a.arg for a in fns["_d3_legacy_source_or_refuse"].args.args if a.arg not in ("self", "user_id", "op")]
    assert any(getattr(c.func, "attr", None) == "_d3_legacy_source_or_refuse"
               for c in ast.walk(fns["_source_revocation"]) if isinstance(c, ast.Call))
    return {name: set(d3) for name, fn in fns.items() if not name.startswith("_")
            and any(getattr(c.func, "attr", None) == "_source_revocation" for c in ast.walk(fn)
                    if isinstance(c, ast.Call))}


def _screened_by(method: str, param: str):
    """`own` (the method's own `_cred_ingress`, or its I20 twin's), `callee:D3`, or None."""
    owner = method if method in _screened() else _DELEGATES.get(method)
    if owner is not None and param in _screened().get(owner, ()):
        return "own"
    if param in _callee_screened().get(method, ()):
        return "callee:D3"
    return None


def _call(mem, tmp_path, e, method, param, value):
    from veracium.redaction import SOURCE_LIFT_REASONS, SOURCE_REVOCATION_REASONS
    from veracium.trust_tools import PreviewTokenIssuer
    iss = PreviewTokenIssuer(mem.store.local_origin(), "u")
    proc = dict(summary="I run the tests first", author=EvidenceAuthor.USER,
                context=EvidenceContext.direct(basis="stated"), relation="follows_procedure", note=None, when=None,
                evidence_ref=None, source_id=None)
    base = {
        "remember": dict(event_text="I live in Denver", date=None, event_type="chat", evidence_ref=None,
                         source_id=None, context=EvidenceContext.direct()),
        "record_procedure": proc, "record_procedure_report": proc,
        "describe_procedures": dict(query="tests", principal=None),
        "recall": dict(query="Denver", principal=None, semantic="auto", as_of=None, policy=None),
        "facts_valid_at": dict(subject="user", relation="located_at", T="2026-11-24T00:00:00+00:00", principal=None,
                               policy=None),
        "answer": dict(query="Where do I live?", principal=None),
        "introspect": dict(mode="summary"),
        "edges_since": dict(since="2026-01-01T00:00:00+00:00"),
        "dispute": dict(edge_id=e.id, reason="not true", actor="user", principal=None, source_id=None),
        "confirm": dict(edge_id=e.id, date=None, correlation_id=None, principal=None, source_id=None),
        "undo_restoration": dict(edge_id=e.id, correlation_id=None),
        "reply": dict(edge_id=e.id, kind="context", text="more context", target=None, correlation_id=None),
        "record_outcome": dict(edge_id=e.id, outcome="corrected", evidence_ref="run-1", actor="user",
                               corrected_value="Boulder", date=None, context_ref=None),
        "correct": dict(edge_id=e.id, corrected_value="Boulder", actor="user", evidence_ref=None, date=None,
                        principal=None, source_id=None),
        "forget_everything_preview": dict(issuer=iss, principal=None),
        "forget_everything_confirm": dict(issuer=iss, principal=None),
        "revoke_source": dict(origin=None, source_id="chat", reason=SOURCE_REVOCATION_REASONS[0]),
        "unrevoke_source": dict(origin=None, source_id="chat", reason=SOURCE_LIFT_REASONS[0]),
        "redact": dict(edge_id=e.id, episode_id=None, reason="operator_policy", principal=None),
        "confirm_notice": dict(notice_id="n-1"),
        "policy_receipt": dict(recall_id="r-1"),
        "export_memory": dict(path=str(tmp_path / "out.jsonl")),
        "import_memory": dict(path=str(tmp_path / "in.jsonl"), user_id=None),
    }
    kw = dict(base[method])
    if method == "forget_everything_confirm":
        kw["preview_token"] = mem.forget_everything_preview("u", issuer=iss)["preview_token"]
    if method == "import_memory":
        other = T._mem(tmp_path, "src")
        T._seed_edge(other)
        other.export_memory("u", str(tmp_path / "in.jsonl"))
        other.close()
    assert param in kw, (method, param)
    kw[param] = value
    fn = getattr(mem, method)
    return fn(**kw) if method == "import_memory" else fn("u", **kw)


def _a5_value(tmp_path, param, form):
    """The canary for one row: the token itself, or for a path parameter a path inside tmp_path ending in it (never a
    file in the working directory)."""
    text = str(tmp_path / ("p-" + TOKEN)) if param == "path" else TOKEN
    return text if form == "str" else os.fsencode(text)


def _run_a5(tmp_path, method, param, form):
    stub = T.Stub()
    sub = tmp_path / form
    sub.mkdir()
    mem = Memory(llm=stub, config=MemoryConfig(db_path=str(sub / "m.db"), wiki_recompile_after_writes=0))
    try:
        e = T._seed_edge(mem)
        if method == "unrevoke_source":         # its precondition, written BEFORE the storage snapshot
            from veracium.redaction import SOURCE_REVOCATION_REASONS
            mem.revoke_source("u", None, "chat", SOURCE_REVOCATION_REASONS[0])
        before = T._dump(str(sub / "m.db"))
        stub.prompts.clear()
        try:
            _call(mem, sub, e, method, param, _a5_value(sub, param, form))
            exc = None
        except Exception as ex:                                    # noqa: BLE001 - the outcome is recorded
            exc = ex
        return exc, _leaks(str(sub / "m.db"), stub), before == T._dump(str(sub / "m.db")), len(stub.prompts)
    finally:
        mem.close()


def test_r4_01_the_a5_census_is_whole_and_every_row_has_a_driver():
    """The census is read from the code; a parameter added later without a driver here fails, and so does a screened
    field the census does not list. RED against: a new string parameter that nobody classed."""
    rows = _a5_rows()
    assert len(rows) >= 83, len(rows)                     # 83 at the round-4 fix (A5's 77 plus the I20 twin's six)
    screened = _screened()
    for method, fields in screened.items():
        for f in fields:
            assert (method, f) in rows, (method, f)
    callee = _callee_screened()
    assert callee, "no callee-screened field found: D3's route moved?"
    for method, fields in callee.items():
        for f in fields:
            assert (method, f) in rows, (method, f)
    tree = ast.parse((ROOT / "src" / "veracium" / "__init__.py").read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Memory")
    for public, twin in _DELEGATES.items():
        fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == public)
        assert any(getattr(c.func, "attr", None) == twin for c in ast.walk(fn) if isinstance(c, ast.Call)), public


@pytest.mark.parametrize("method,param", _a5_rows(), ids=[f"{m}.{p}" for m, p in _a5_rows()])
def test_r4_01_a_non_str_value_is_admitted_no_further_than_a_str(tmp_path, method, param):
    """Every A5 row, driven with the token as bytes and as a `str`: the bytes form never reaches storage or the
    provider where the `str` form does not. A SCREENED field refuses the bytes form outright (`ArgumentRefused`,
    `not_a_string`), before any provider call, with storage unchanged. RED against: round 4's R4-01 — `event_type` and
    `evidence_ref` as bytes skipped the screen, became text downstream and were stored (the `isinstance(str)` gate)."""
    b_exc, b_leak, b_unchanged, b_calls = _run_a5(tmp_path, method, param, "bytes")
    s_exc, s_leak, _s_unchanged, _s_calls = _run_a5(tmp_path, method, param, "str")
    assert b_leak <= s_leak, (method, param, b_leak, s_leak, type(b_exc).__name__ if b_exc else None)
    # round 5: the exception's own text, too. A library exception may carry the caller's argument (E1's library
    # scope), but the bytes form may not echo the token where the str form does not. RED against: the revocation
    # rows at 7124ba95 (D3's str-only gate let bytes through to `_bounded`'s `got {value!r}`).
    if b_exc is not None and TOKEN in str(b_exc):
        assert s_exc is not None and TOKEN in str(s_exc), (method, param, type(b_exc).__name__,
                                                           type(s_exc).__name__ if s_exc else None)
    if _screened_by(method, param) is not None:
        assert isinstance(b_exc, C.ArgumentTypeRefused) and b_exc.reason == "not_a_string", repr(b_exc)
        assert isinstance(b_exc, TypeError) and isinstance(b_exc, C.ArgumentRefused)
        assert TOKEN not in str(b_exc) and TOKEN not in C.outward_text(b_exc)
        assert b_unchanged and b_calls == 0 and not b_leak


@pytest.mark.parametrize("field", ["event_type", "evidence_ref"])
@pytest.mark.parametrize("form", ["str", "bytes"])
def test_r4_01_reviewer_identifiers_are_rejected_before_conversion(tmp_path, field, form):
    """The reviewer's case, with the extractor answering non-JSON (the fallback summary interpolates `event_type`):
    both forms refused, no provider call, storage unchanged. RED against: R4-01 (the two bytes cells)."""
    calls = []

    def llm(*args, **kwargs):
        calls.append(1)
        return "not structured output"
    m = T._mem(tmp_path, llm=llm)
    try:
        before = T._dump(str(tmp_path / "m.db"))
        value = TOKEN if form == "str" else TOKEN.encode()
        with pytest.raises((C.CredentialRefused, C.ArgumentRefused)):
            m.remember("u", "Ordinary event", **{field: value})
        assert not calls and before == T._dump(str(tmp_path / "m.db"))
    finally:
        m.close()


# ==== R4-02: the cached wiki is masked on read =====================================================================

def _wiki_mem(tmp_path, shaped, *, llm=None):
    stub = llm or T.Stub()
    m = Memory(llm=stub, config=MemoryConfig(db_path=str(tmp_path / "m.db"), wiki_recompile_after_writes=100))
    from veracium import compile as WC
    T._seed_edge(m)
    WC.compile_wiki(m.store, stub if llm is None else T.Stub(), "u", m.config.relations)
    row = m.store.get_wiki("u")
    marker = TOKEN if shaped else "ordinary-cache-control"
    old_body = row[0].split("\n", 1)[0] + "\nDenver archive " + marker
    m.store._conn.execute("UPDATE wiki SET text=? WHERE user_id=?", (old_body, "u"))
    m.store._conn.commit()
    assert not WC.needs_recompile(m.store, "u", 100, m.config.relations)
    return m, stub, marker, old_body


@pytest.mark.parametrize("shaped", [False, True], ids=["ordinary-control", "legacy-shaped"])
@pytest.mark.parametrize("surface", ["library", "mcp", "adapter"])
def test_r4_02_a_fresh_cached_body_is_masked_on_every_served_read(tmp_path, shaped, surface):
    """A valid, FRESH cache whose body predates the screen: served through the library, MCP and the adapter binding,
    with the cache path ON. The read masks and never recompiles or rewrites the cache; an ordinary body reaches all
    three. RED against: R4-02, `ensure_wiki` returning the cached body unmasked (I7's test disables this path)."""
    if surface != "library":
        _needs_mcp()
    m, stub, marker, old_body = _wiki_mem(tmp_path, shaped)
    try:
        calls = len(stub.prompts)
        if surface == "library":
            out = m.recall("u", "Denver").context
        elif surface == "mcp":
            from veracium.mcp_server import build_server
            out = str(asyncio.run(build_server(m, default_user="u", capability="direct")
                                  .call_tool("recall", {"query": "Denver"})))
        else:
            from veracium.adapters._surface import Binding
            out = str(Binding(m, user_id="u", capability="direct").call("recall", {"query": "Denver"}))
        assert len(stub.prompts) == calls, "the read recompiled"
        assert m.store.get_wiki("u")[0] == old_body, "the read changed storage"
        assert (marker not in out) if shaped else (marker in out)
    finally:
        m.close()


@pytest.mark.parametrize("shaped", [False, True], ids=["ordinary-control", "legacy-shaped"])
def test_r4_02_the_provider_free_reader_of_a_fresh_cache_is_masked(tmp_path, shaped):
    """The CLI's store-only reader (`_veracium_no_llm`) of a FRESH cache takes the same cached branch."""
    from veracium import compile as WC

    def no_llm(*a, **k):
        raise AssertionError("a provider-free reader called the provider")
    no_llm._veracium_no_llm = True
    m, _stub, marker, _old = _wiki_mem(tmp_path, shaped)
    try:
        body = WC.ensure_wiki(m.store, no_llm, "u", 100, m.config.relations)
        assert (marker not in body) if shaped else (marker in body)
    finally:
        m.close()


# every function in src/ that reads the wiki cache, and what it does with the body (the inventory, by `ast`)
_WIKI_READERS = {
    ("compile.py", "ensure_wiki"): "SERVES the body: masked on read (R4-02)",
    ("compile.py", "needs_recompile"): "identity check: the envelope digest and the version; serves nothing",
    ("compile.py", "_provider_free_notice"): "picks a code-owned notice from the envelope; serves no body",
    ("compile.py", "bound_wiki"): "compares the row it was served from; serves nothing",
    ("introspect.py", "_wiki_compile_record"): "parses the code-owned compile marker into closed fields",
    ("cli.py", "_memory_verbs"): "presence only (the store-only reader's wiki switch)",
    ("credential_finder.py", "act"): "discards the row",
    ("selfcheck.py", "snap"): "selfcheck's own byte comparison across two attempts; never output",
    ("selfcheck.py", "_check_revocation"): "presence only",
}


def test_r4_02_every_reader_of_the_wiki_cache_is_classed():
    """Every call of `.get_wiki(` under src/veracium, located by `ast` with its enclosing function, is in the table
    above. RED against: a new reader that serves the cached body without the mask."""
    found = set()
    for path in (ROOT / "src" / "veracium").rglob("*.py"):
        tree = ast.parse(path.read_text())
        stack = []

        def visit(node):
            is_fn = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            if is_fn:
                stack.append(node.name)
            if (isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "get_wiki"
                    and not (path.name == "sqlite.py")):
                found.add((path.name, stack[-1] if stack else "<module>"))
            for child in ast.iter_child_nodes(node):
                visit(child)
            if is_fn:
                stack.pop()
        visit(tree)
    assert found == set(_WIKI_READERS), (sorted(found - set(_WIKI_READERS)), sorted(set(_WIKI_READERS) - found))


# ==== R4-03 and S2: every report that names records uses the locator rule ==========================================

def _shaped_store(tmp_path):
    """A store holding a shaped edge id (fact text ordinary), a shaped interaction episode id, and a shaped source
    episode of an ordinary edge (so a redaction receipt names it)."""
    from veracium.schema import Episode, Provenance
    m = T._mem(tmp_path)
    e = T._seed_edge(m)
    rid = "e-" + TOKEN
    doc = json.loads(m.store._conn.execute("SELECT json FROM edges WHERE id=?", (e.id,)).fetchone()[0])
    doc["id"] = rid
    m.store._conn.execute("UPDATE edges SET id=?, json=? WHERE id=?", (rid, json.dumps(doc), e.id))
    m.store._conn.execute("UPDATE edge_event SET edge_id=?, state=? WHERE edge_id=?", (rid, json.dumps(doc), e.id))
    m.store._conn.commit()
    m.store.add_episode(Episode(id="ep-" + TOKEN, user_id="u", date="2026-11-24", summary="I live in Denver",
                                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-x")))
    plain = T._seed_edge(m)
    m.store.add_episode(Episode(id="ep2-" + TOKEN, user_id="u", date="2026-11-24", summary="source episode",
                                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                      evidence_ref=plain.provenance.evidence_ref)))
    return m, plain


_TOOL_ARGS = {"remember": {"text": "ordinary"}, "recall": {"query": "Denver"}, "answer": {"query": "Where do I live?"},
              "maintain": {}, "record_procedure": {"basis": "stated", "summary": "I lint first"},
              "describe_procedures": {}, "find_facts": {"query": "Denver"},
              "correct_fact": {"corrected_value": "Boulder", "edge_id": "e-missing"},
              "dispute_fact": {"edge_id": "e-missing"}, "confirm_fact": {"edge_id": "e-missing"},
              "forget_fact": None, "forget_everything_preview": {}, "forget_everything_confirm": None}


@pytest.mark.parametrize("capability", [None, "direct"])
def test_r4_03_no_served_tool_names_a_shaped_record_id(tmp_path, capability):
    """Every tool the server lists (the list is read from the server; a new tool without an entry here fails), over a
    store holding shaped ids. Positive controls: `find_facts` and `forget_fact` DO name the shaped records (by ordinal),
    and an ordinary survivor keeps its id. RED against: R4-03 (`find_facts` units carried `record.id`) and the served
    redaction receipt (dev's sweep: `forget_fact`'s `surviving_derived` named a shaped source episode raw)."""
    _needs_mcp()
    from veracium.mcp_server import build_server
    m, plain = _shaped_store(tmp_path)
    try:
        srv = build_server(m, default_user="u", capability=capability)
        listed = {t.name for t in asyncio.run(srv.list_tools())}
        assert listed == set(_TOOL_ARGS), sorted(listed ^ set(_TOOL_ARGS))
        outs = {}
        for name, args in _TOOL_ARGS.items():
            if args is None:
                continue
            outs[name] = str(asyncio.run(srv.call_tool(name, args)))
        outs["forget_fact"] = str(asyncio.run(srv.call_tool("forget_fact", {"edge_id": plain.id})))
        for name, out in outs.items():
            assert TOKEN not in out, name
        if capability == "direct":
            assert "of this report" in outs["find_facts"]                       # the shaped edge, by ordinal
            assert "of this report (episode)" in outs["forget_fact"]            # the shaped survivor, by ordinal
            assert plain.id in outs["forget_fact"]                               # an ordinary id kept
    finally:
        m.close()


def test_r4_03_render_receipts_use_the_locator_on_every_exit(tmp_path):
    """`RenderReceipt.admit` is the receipt's one constructor; its library exits are `recall(query, render_receipt=True)`
    and the proactive path, `recall(None, render_receipt=True)` (MCP `find_facts` is above). A shaped id is an ordinal,
    an ordinary id is kept, on both."""
    m, plain = _shaped_store(tmp_path)
    try:
        rr = m.recall("u", "Denver", render_receipt=True).render_receipt
        ids = [u["id"] for u in rr]
        assert not any(TOKEN in str(i) for i in ids) and any("of this report" in str(i) for i in ids), ids
        assert plain.id in ids
        pr = m.recall("u", None, render_receipt=True).render_receipt
        pids = [u["id"] for u in pr]
        assert not any(TOKEN in str(i) for i in pids) and any("of this report" in str(i) for i in pids), pids
    finally:
        m.close()


@pytest.mark.parametrize("shaped", [False, True], ids=["ordinary-control", "import-shaped"])
@pytest.mark.parametrize("refusal", ["procedural", "duplicate"])
def test_r4_03_early_import_refusals_use_the_locator(tmp_path, shaped, refusal):
    """Import's procedural pass runs before §4h's screen and removes what it refuses, so its refusal list was
    returned raw. Both of its id-bearing refusals (a procedural stamp, a duplicate id) now name a shaped id by
    ordinal and keep an ordinary one. RED against: R4-03's import case."""
    path, _ = T._export_with(tmp_path)
    docs = [json.loads(line) for line in path.read_text().splitlines()]
    rid = "e-" + (TOKEN if shaped else "ordinary-import-control")
    edges = [d for d in docs if d.get("record") == "edge"]
    for d in edges:
        d["id"] = rid
        if refusal == "procedural":
            d["provenance"]["record_kind"] = "procedural"
    if refusal == "duplicate":
        docs.append(dict(edges[0]))
    path.write_text("".join(json.dumps(d) + "\n" for d in docs))
    m = T._mem(tmp_path, "target")
    try:
        r = m.import_memory(str(path))
        assert r["procedural_refused"] >= 1 and r["edges"] == 0, r
        assert (TOKEN not in json.dumps(r)) if shaped else (rid in json.dumps(r))
    finally:
        m.close()


def test_r4_03_a_restore_with_a_shaped_id_refuses_before_the_agreement_check_quotes_it(tmp_path):
    """Research's S2 classification of `portability.py`'s malformed-AgreementRecord ValueError (it quotes the record's
    id and the validation error): it runs only on a restore, after §4h's screen has refused any shaped id, so it never
    meets one. Executed: a restore holding a shaped edge id AND a malformed agreement raises the screen's refusal."""
    from veracium.portability import CredentialImportRefused
    path, _ = T._export_with(tmp_path)
    docs = [json.loads(line) for line in path.read_text().splitlines()]
    for d in docs:
        if d.get("record") == "edge":
            d["id"] = "e-" + TOKEN
            d["agreement"] = {"not": "an agreement record"}
    path.write_text("".join(json.dumps(d) + "\n" for d in docs))
    m = T._mem(tmp_path, "target")
    try:
        with pytest.raises(CredentialImportRefused) as ei:
            m.import_memory(str(path), restore=True)
        assert TOKEN not in str(ei.value)
    finally:
        m.close()


# ==== R4-04 and S1: the finder fails closed over the whole schema ==================================================

def test_r4_04_the_store_level_tables_are_exactly_the_tables_without_a_user():
    """The finder reads every table with a `user_id`; the rest must be the declared store-level set. RED against: a
    new store-level table holding user-derived text that nobody classed."""
    from veracium.store.sqlite import STORE_LEVEL_TABLES, SqliteStore
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        s = SqliteStore(os.path.join(d, "x.db"))
        try:
            no_user = {t for (t,) in s._conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT "
                                                     "LIKE 'sqlite_%'")
                       if "user_id" not in {c[1] for c in s._conn.execute(f"PRAGMA table_info({t})")}}
        finally:
            s.close()
    assert no_user == set(STORE_LEVEL_TABLES), sorted(no_user ^ set(STORE_LEVEL_TABLES))


def test_r4_04_a_shape_in_any_column_of_any_per_user_side_table_is_found(tmp_path):
    """One synthetic row per (table, column) of the LIVE schema's per-user side tables, the token in that column: the
    finder reports a hit in that table. A column the schema's own CHECK constraint closes cannot hold the token, and
    is exempt by that property (the insert is refused naming it). RED against: S1 (the finder never queried
    `supersession_refusals.relation` or `source_revocations.reason`) and every unlisted column."""
    from veracium import credential_finder as CF
    m = T._mem(tmp_path)
    con = m.store._conn
    checked = closed = 0
    import re

    def fill_for(table):
        # a valid value for every column the table's own CHECK closes (`col IN (a, b, ...)`): its first member
        sql = con.execute("SELECT sql FROM sqlite_master WHERE name=?", (table,)).fetchone()[0]
        out = {}
        for col, members in re.findall(r"(\w+)\s+IN\s*\(([^)]*)\)", sql):
            first = members.split(",")[0].strip()
            out[(table, col)] = first.strip("'") if first.startswith("'") else int(first)
        return out
    try:
        for table, cols in m.store._credential_side_tables():
            fill = fill_for(table)
            info = [c[1] for c in con.execute(f"PRAGMA table_info({table})")]
            for col in cols:
                vals = {c: fill.get((table, c), f"x-{table}-{i}") for i, c in enumerate(info)}
                vals["user_id"] = "u"
                if table == "replies":
                    # the table's cross-column CHECKs: `kind = 'resolve'` exactly when `target` is set and `text` is
                    # not; a `text` plant is a context reply, any other a resolve reply
                    vals.update({"kind": "context", "target": None} if col == "text"
                                else {"kind": "resolve", "text": None})
                vals[col] = TOKEN
                try:
                    con.execute(f"INSERT INTO {table}({','.join(vals)}) VALUES ({','.join('?' * len(vals))})",
                                list(vals.values()))
                    con.commit()
                except sqlite3.IntegrityError as exc:
                    con.rollback()
                    assert "CHECK" in str(exc) and col in str(exc), (table, col, str(exc))
                    closed += 1
                    continue
                hits = [h for h in CF.scan(m.store, "u") if h.table == table]
                assert hits, (table, col)
                con.execute(f"DELETE FROM {table}")
                con.commit()
                checked += 1
        assert checked >= 100 and closed == len([1 for t, cs in m.store._credential_side_tables() for c in cs
                                                 if (t, c) in fill_for(t)]), (checked, closed)
    finally:
        m.close()


def _record_paths(model_cls):
    """Every top-level field of a record model, as the stored JSON spells it."""
    return list(model_cls.model_fields)


@pytest.mark.parametrize("kind", ["edge", "episode"])
@pytest.mark.parametrize("where", ["current", "journal"])
def test_r4_04_a_shape_in_any_field_of_a_record_or_its_journal_is_found(tmp_path, kind, where):
    """Every top-level field of the record model (and a dict key, and a nested provenance field), planted with the token
    in the stored JSON of the current row or of its journal snapshot: the finder reports it, as removable text when a
    0041 redaction rewrites that field and as a residual otherwise. RED against: R4-04 (`invalidation_reason`, `kind`,
    `retired_reason` dropped) and any field the old fixed lists did not name."""
    from veracium import credential_finder as CF
    from veracium.redaction import carrier_paths
    from veracium.schema import Edge, Episode, Provenance
    m = T._mem(tmp_path)
    try:
        if kind == "edge":
            rec = T._seed_edge(m)
            model, table, jtable, idcol = Edge, "edges", "edge_event", "edge_id"
        else:
            rec = Episode(id="ep-review", user_id="u", date="2026-11-24", summary="Ordinary episode",
                          provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-review"))
            m.store.add_episode(rec)
            model, table, jtable, idcol = Episode, "episodes", "episode_event", "episode_id"
            if where == "journal" and not m.store._conn.execute(
                    "SELECT 1 FROM episode_event WHERE episode_id=?", (rec.id,)).fetchone():
                m.redact("u", episode_id=rec.id, reason="operator_policy")
        assert not CF.scan(m.store, "u"), "the control store already holds a shape"
        own = {p for p in carrier_paths(kind) if "." not in p}      # the record's own top-level carriers
        targets = [f for f in _record_paths(model) if f not in ("id", "user_id")] + ["<dict key>",
                                                                                     "provenance.source_id"]
        for target in targets:
            if where == "current":
                sel = (f"SELECT rowid, json FROM {table} WHERE id=?", (rec.id,))
                upd = f"UPDATE {table} SET json=? WHERE rowid=?"
            else:
                sel = (f"SELECT rowid, state FROM {jtable} WHERE {idcol}=? ORDER BY seq DESC LIMIT 1", (rec.id,))
                upd = f"UPDATE {jtable} SET state=? WHERE rowid=?"
            rowid, text = m.store._conn.execute(*sel).fetchone()
            doc = json.loads(text)
            if target == "<dict key>":
                doc["outcome_counts" if kind == "edge" else "lineage_note"] = {TOKEN: 1}
            elif target.startswith("provenance."):
                doc["provenance"]["source_id"] = TOKEN
            else:
                doc[target] = TOKEN
            m.store._conn.execute(upd, (json.dumps(doc), rowid))
            m.store._conn.commit()
            hits = CF.scan(m.store, "u")
            assert hits, (kind, where, target)
            if target in own and kind == "episode" and where == "journal":
                # an episode's journal row exists only after a redaction of it, and redacting again writes nothing:
                # its text is a residual (round 5, the carrier table), never reported removable
                assert any(h.carrier == "episode_event.after_redaction" and not h.removable for h in hits), (
                    target, [h.carrier for h in hits])
            elif target in own:
                assert any(h.removable for h in hits), (target, [h.carrier for h in hits])
            m.store._conn.execute(upd, (text, rowid))
            m.store._conn.commit()
    finally:
        m.close()


@pytest.mark.parametrize("kind", ["edge", "episode"])
def test_r4_04_an_unparseable_current_record_is_reported_not_skipped(tmp_path, kind):
    """A current row whose JSON does not parse is yielded whole, as a residual (research's S1: it was skipped, and
    the store read clean); the journal branch already yielded such a row."""
    from veracium import credential_finder as CF
    from veracium.schema import Episode, Provenance
    m = T._mem(tmp_path)
    try:
        if kind == "edge":
            rid, table = T._seed_edge(m).id, "edges"
        else:
            m.store.add_episode(Episode(id="ep-u", user_id="u", date="2026-11-24", summary="x",
                                        provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                              evidence_ref="ev-u")))
            rid, table = "ep-u", "episodes"
        m.store._conn.execute(f"UPDATE {table} SET json=? WHERE id=?", ("{not json " + TOKEN, rid))
        m.store._conn.commit()
        hits = CF.scan(m.store, "u")
        assert [h.carrier for h in hits] == [f"{kind}.unparsed"] and not hits[0].removable
    finally:
        m.close()


@pytest.mark.parametrize("carrier,field", [
    ("edges", "invalidation_reason"), ("edge_event", "invalidation_reason"),
    ("episodes", "kind"), ("episodes", "retired_reason"),
    ("episode_event", "kind"), ("episode_event", "retired_reason"),
])
def test_r4_04_reviewer_legacy_text_carriers_are_found(tmp_path, carrier, field):
    """The reviewer's six carriers, each in isolation over a clean control store. RED against: R4-04."""
    from veracium import credential_finder as CF
    from veracium.schema import Episode, Provenance
    m = T._mem(tmp_path)
    try:
        T._seed_edge(m)
        ep = Episode(id="ep-review", user_id="u", date="2026-11-24", summary="Ordinary episode",
                     provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-review"))
        m.store.add_episode(ep)
        if carrier == "episode_event":
            m.redact("u", episode_id=ep.id, reason="operator_policy")
        assert not CF.scan(m.store, "u")
        col = "state" if carrier.endswith("_event") else "json"
        changed = False
        for rowid, text in m.store._conn.execute(f"SELECT rowid, {col} FROM {carrier}").fetchall():
            try:
                doc = json.loads(text)
            except (TypeError, ValueError):
                continue
            if isinstance(doc, dict):
                doc[field] = TOKEN
                m.store._conn.execute(f"UPDATE {carrier} SET {col}=? WHERE rowid=?", (json.dumps(doc), rowid))
                changed = True
                break
        m.store._conn.commit()
        assert changed and TOKEN in T._dump(str(tmp_path / "m.db"))
        assert CF.scan(m.store, "u")
    finally:
        m.close()


def test_r4_04_credentials_redact_removes_a_legacy_invalidation_reason_end_to_end(tmp_path, capsys):
    """The reviewer's CLI observation, reversed: `veracium credentials redact --yes` over an edge whose stored
    `invalidation_reason` carries the token reports it, redacts the edge, and the database no longer holds the token;
    the second scan reports nothing left. RED against: R4-04 (the CLI reported no shape found, exited 0, and the token
    stayed)."""
    from veracium import cli
    m = T._mem(tmp_path)
    e = T._seed_edge(m)
    m.close()
    T._plant(str(tmp_path / "m.db"), e.id, invalidation_reason=TOKEN)
    rc = cli.main(["credentials", "redact", "--yes", "--db", str(tmp_path / "m.db")])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "edge.text" in out or "edge_event.state" in out, out
    assert TOKEN not in T._dump(str(tmp_path / "m.db")), "the token survived the remedy"
    assert TOKEN not in out


# ==== R4-05 and S3: the CLI's defect path and the outward formatter ================================================

def test_r4_05_a_real_invalid_import_leaves_the_cli_without_its_input(tmp_path):
    """The reviewer's case: an otherwise valid export whose provenance `confidence` is a short canary. Pydantic's
    ValidationError formats its stored errors whatever `args` holds; the CLI raises a fresh exception of the same
    name, a ValueError, carrying the original frames and type. RED against: R4-05 (the canary in the traceback)."""
    from veracium import cli
    path, _ = T._export_with(tmp_path)
    marker = "REVIEW_CANARY_01"
    docs = [json.loads(line) for line in path.read_text().splitlines()]
    for d in docs:
        if d.get("record") == "edge":
            d["provenance"]["confidence"] = marker
    path.write_text("".join(json.dumps(d) + "\n" for d in docs))
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
        with pytest.raises(ValueError) as ei:
            cli.main(["import", "--db", str(tmp_path / "target.db"), str(path)])
    exc = ei.value
    shown = "".join(traceback.format_exception(exc))
    assert marker not in shown + captured.getvalue(), shown[-400:]
    from pydantic import ValidationError
    assert isinstance(exc, ValidationError)                     # rebuilt as itself: same type and title
    assert [e["type"] for e in exc.errors()] and all(marker not in str(e) for e in exc.errors())
    assert exc.__cause__ is None and exc.__suppress_context__


def test_r4_05_an_exception_with_its_own_formatter_is_replaced_and_a_plain_one_raised_as_itself():
    """`withheld_defect`: an exception whose formatting `args` controls is raised AS ITSELF (type, attributes,
    traceback), with its `__notes__` dropped; one with its own formatter (a SyntaxError's source line, an OSError's
    filename) is replaced by a fresh instance of its own class, and one whose `__str__` prints its own state by a
    RuntimeError naming its class. Nothing formatted holds the canary. RED against: the args rewrite alone (R4-05;
    research's S3: notes survive it)."""
    canary = "CANARY_S3_77"

    class Custom(RuntimeError):
        def __str__(self):
            return "formatted from state: " + canary

    plain = TypeError(canary)
    plain.add_note("note " + canary)
    plain.marker = "kept"
    cases = [plain, Custom(canary), KeyError(canary), FileNotFoundError(2, "No such file", "/x/" + canary)]
    try:
        compile("x = (" + canary, "<input>", "exec")
    except SyntaxError as exc:
        cases.append(exc)
    for exc in cases:
        out = C.withheld_defect(exc)
        shown = "".join(traceback.format_exception(out))
        assert canary not in shown, (type(exc).__name__, shown)
        if isinstance(exc, Custom):
            assert type(out) is RuntimeError and "Custom" in str(out)
        else:
            assert type(out) is type(exc)
    assert C.withheld_defect(plain) is plain and plain.marker == "kept"


def test_r4_05_a_caller_dict_key_in_a_validation_location_is_not_echoed():
    """Research's S3, executed: `Edge.outcome_counts` is `dict[str, int]`, so a caller's key is a location segment.
    Only declared field names and indexes are printed. RED against: `outcome_counts.<key>: int_parsing`."""
    from pydantic import ValidationError
    from veracium.schema import Edge
    with pytest.raises(ValidationError) as ei:
        Edge.model_validate({"outcome_counts": {"CANARYKEY42": "x"}})
    text = C.outward_text(ei.value)
    assert "CANARYKEY42" not in text and "outcome_counts.[key]: int_parsing" in text, text


def test_r4_05_every_product_model_field_is_a_declared_name():
    """`outward_text` prints a location segment only if it is a declared field name; the product names its root models
    (it reads no class registry), so this holds the list complete: every Pydantic model defined in a `veracium` module
    has all its fields among the declared names. `mcp_server._HiddenInput` and the SDK's run-time `<tool>Arguments` models
    are validated and formatted by the SDK (E2), never by `outward_text`. RED against: a new product model left out."""
    import pkgutil
    import veracium
    from pydantic import BaseModel
    for info in pkgutil.walk_packages(veracium.__path__, "veracium."):
        try:
            __import__(info.name)
        except ImportError:
            continue
    seen, todo, models = set(), [BaseModel], []
    while todo:
        for sub in todo.pop().__subclasses__():
            if sub not in seen:
                seen.add(sub)
                todo.append(sub)
                # a model BOUND in its module (the SDK's per-tool `<tool>Arguments` models are built at run time
                # with this module's name, and are validated and formatted by the SDK, E2, never by outward_text)
                mod = sys.modules.get(sub.__module__)
                if (sub.__module__.startswith("veracium") and sub.__qualname__ != "_HiddenInput"
                        and getattr(mod, sub.__qualname__, None) is sub):
                    models.append(sub)
    declared = C._declared_field_names()
    assert len(models) >= 20, [m.__qualname__ for m in models]
    for m in models:
        assert set(m.model_fields) <= declared, (m.__module__, m.__qualname__, set(m.model_fields) - declared)


# ==== R4-06: the diagnostics tail is screened before it is cut ======================================================

def _tail(tmp_path, line: str, cap: int) -> str:
    from veracium.diagnostics import DiagnosticsConfig, Reporter
    path = tmp_path / "legacy.log"
    path.write_text(line, encoding="utf-8")
    return Reporter(DiagnosticsConfig(log_path=str(path), redact=False)).log_tail(cap)


@pytest.mark.parametrize("case", ["structural-prefix", "structural-body", "labelled-value", "multibyte"])
def test_r4_06_a_cut_never_sends_the_unscreened_rest_of_a_value(tmp_path, case):
    """An older log line (written before the screen, or by another writer) holding a credential, followed by an
    ordinary line, read with a cap that cuts inside the credential's line. The tail sent holds no part of the value,
    holds the complete ordinary line, and is within the cap. A full read masks the line (control). RED against: R4-06
    (the last `cap` bytes were cut first, so a cut inside the value dropped its recognition prefix)."""
    secret = {"structural-prefix": TOKEN, "structural-body": TOKEN,
              "labelled-value": "password: hunter2-correct-horse", "multibyte": TOKEN}[case]
    lead = "älter Eintrag – " if case == "multibyte" else "old message "
    line = f"{lead}{secret}\nlater ordinary line\n"
    full = _tail(tmp_path, line, 4096)
    assert "later ordinary line" in full and "credential withheld" in full
    tail_after = len("\nlater ordinary line\n".encode())
    cut_at = {"structural-prefix": len(secret) - 2, "structural-body": len(secret) // 2,
              "labelled-value": len(secret) - 6, "multibyte": len(secret) + 3}[case]
    cap = tail_after + cut_at
    tail = _tail(tmp_path, line, cap)
    assert len(tail.encode()) <= cap
    tail_value = secret.split(": ")[-1]
    for k in range(6, len(tail_value) + 1):
        assert tail_value[-k:] not in tail, (case, k, tail)
    assert "later ordinary line" in tail


def test_r4_06_reviewer_a_twenty_byte_tail_holds_no_part_of_the_token(tmp_path):
    from veracium.diagnostics import DiagnosticsConfig, Reporter
    path = tmp_path / "legacy.log"
    path.write_text("old message " + TOKEN + "\n")
    reporter = Reporter(DiagnosticsConfig(log_path=str(path), redact=False))
    full = reporter.log_tail(1000)
    assert TOKEN not in full and "credential withheld" in full
    assert TOKEN[-16:] not in reporter.log_tail(20)


# ==== A1: maintain()'s pool key is a declared opaque domain ========================================================

def test_a1_the_finder_report_declares_the_pool_key(tmp_path):
    """The report names `maintain()`'s `consolidate-pool` / `pool_key` destination among the declared, unvouched opaque
    domains, unconditionally (an empty store included). RED against: round 4's A1."""
    from veracium import credential_finder as CF
    m = T._mem(tmp_path)
    try:
        rep = CF.report(CF.scan(m.store, "u"))
        assert any("pool_key" in d["domain"] for d in rep["declared_opaque"])
        assert "pool_key" in CF.render(rep)
    finally:
        m.close()


# ==== Round 5: what the carrier-to-boundary table found (specs/evidence/0055/carrier_boundaries.py) ===============

#: the two value forms of a legacy date: the token alone sorts after every ISO date (an episode "not yet valid", so
#: rendered only among the non-assertable lines); behind an ISO-date prefix it sorts as a past date, is assertable, and
#: reaches the compile (`Episode.valid_now` compares the strings)
_DATE_FORMS = {"bare": TOKEN, "dated": "2020-01-01 " + TOKEN}


def _legacy_episode_date(tmp_path, form="bare"):
    """A store whose one episode holds the token in its stored `date` (a legacy row: `date` is a str in the model and
    no write path admits a shape, but a store written before 0055, or by another writer, may hold one)."""
    from veracium.schema import Episode, Provenance
    stub = T.Stub()
    m = Memory(llm=stub, config=MemoryConfig(db_path=str(tmp_path / "m.db"), wiki_recompile_after_writes=1))
    T._seed_edge(m)
    m.store.add_episode(Episode(id="ep-r5", user_id="u", date="2026-11-24", summary="Ordinary episode",
                                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-r5")))
    con = m.store._conn
    doc = json.loads(con.execute("SELECT json FROM episodes WHERE id='ep-r5'").fetchone()[0])
    doc["date"] = _DATE_FORMS[form]
    con.execute("UPDATE episodes SET json=? WHERE id='ep-r5'", (json.dumps(doc),))
    con.commit()
    return m, stub


@pytest.mark.parametrize("form", sorted(_DATE_FORMS))
@pytest.mark.parametrize("surface", ["recall", "answer", "mcp-recall", "find_facts", "wiki-compile", "briefing",
                                     "maintain"])
def test_r5_a_legacy_episode_date_reaches_no_model_and_no_result(tmp_path, surface, form):
    """The episode lines of recall, answer and the wiki compile print `[date] summary`; the summary was masked and
    the date was not, so a shaped stored date reached the provider and the served results (the carrier table's row
    `record:episode:current:date`). Both value forms: the bare token is not yet valid and reaches recall's
    non-assertable lines; behind an ISO-date prefix it is assertable and reaches recall's grounded lines and the
    compile (a mutant unmasking only the compile's line survived the bare form). The briefing's recents and
    consolidation's listing read only a date that parses as an ISO date, so neither form reaches them: those cells
    hold that it stays so. RED against: the date printed unmasked at recall's or the compile's episode line."""
    from veracium import compile as _compile
    from veracium.mcp_server import find_facts_impl, recall_impl
    m, stub = _legacy_episode_date(tmp_path, form)
    try:
        assert TOKEN in T._dump(str(tmp_path / "m.db"))
        run = {"recall": lambda: m.recall("u", "where does the user live").context,
               "answer": lambda: m.answer("u", "where does the user live"),
               "mcp-recall": lambda: recall_impl(m, "u", "where does the user live"),
               "find_facts": lambda: find_facts_impl(m, "u", "where", capability="direct"),
               "wiki-compile": lambda: _compile.compile_wiki(m.store, stub, "u", m.config.relations),
               "briefing": lambda: m.recall("u").context,
               "maintain": lambda: m.maintain("u")}[surface]
        out = json.dumps(run(), default=str)
        payloads = [p for _role, p in stub.prompts]
        if surface in ("recall", "answer", "mcp-recall", "wiki-compile"):
            assert payloads, "the surface called no provider: the cell would hold nothing"
        assert TOKEN not in out and not any(TOKEN in p for p in payloads)
        if surface in ("recall", "mcp-recall"):
            assert "[credential withheld" in out, out[:400]
    finally:
        m.close()


def _legacy_why_store(tmp_path):
    m = T._mem(tmp_path)
    e = T._seed_edge(m)
    con = m.store._conn
    doc = json.loads(con.execute("SELECT json FROM edges WHERE id=?", (e.id,)).fetchone()[0])
    doc["outcome_counts"] = {TOKEN: 1}
    doc["invalidation_reason"] = TOKEN
    con.execute("UPDATE edges SET json=? WHERE id=?", (json.dumps(doc), e.id))
    con.commit()
    m.close()
    return str(tmp_path / "m.db"), e.id


@pytest.mark.parametrize("argv", [[], ["--json"], ["--find", "Denver"], ["--json", "--find", "Denver"]],
                         ids=["why", "why-json", "find", "find-json"])
def test_r5_why_prints_no_legacy_dict_key_and_no_unmasked_find_field(tmp_path, capsys, argv):
    """`veracium why` printed an edge's `outcome_counts` with a legacy dict KEY as stored (`mask_deep` masked values,
    never keys), and `why --find --json` printed `invalidation_reason` unmasked. RED against: mask_deep's keys left as
    they are; why.find masking only its id and fact."""
    from veracium import cli
    db, eid = _legacy_why_store(tmp_path)
    rc = cli.main(["why", "--db", db, "--user", "u", *argv, *([] if "--find" in argv else [eid])])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert TOKEN not in out, out[:400]


def test_r5_mask_deep_masks_str_keys_and_keeps_two_alike_as_two():
    """A str key with a shape is masked; two keys that mask alike stay two entries; a key with no shape and a
    non-str key are kept as they are, and a dict with nothing to mask is returned as itself."""
    other = TOKEN[:-1] + ("A" if TOKEN[-1] != "A" else "B")
    assert C.scan(other)
    d = {TOKEN: 1, other: 2, "plain": 3, 7: "x"}
    out = C.mask_deep(d)
    assert len(out) == 4 and sorted(v for v in out.values() if isinstance(v, int)) == [1, 2, 3]
    assert TOKEN not in json.dumps(out) and other not in json.dumps(out)
    assert out["plain"] == 3 and out[7] == "x"
    clean = {"a": 1, "b": ["c"]}
    assert C.mask_deep(clean) is clean


@pytest.mark.parametrize("kind", ["edge", "episode"])
def test_r5_text_in_the_journal_of_an_already_redacted_record_is_residual(tmp_path, kind):
    """A journal snapshot of a record ALREADY redacted can still hold text where the store was redacted before a
    treatment covered the field; redacting again answers `repeated` and writes nothing. The finder reported it
    removable, `act` changed nothing, and the token stayed (the carrier table's `remedy` column). Now it is
    `<journal>.after_redaction`, a residual, and `forget` removes it. RED against: the class read as removable."""
    from veracium import credential_finder as CF
    from veracium.schema import Episode, Provenance
    m = T._mem(tmp_path)
    try:
        if kind == "edge":
            rid = T._seed_edge(m).id
            m.redact("u", edge_id=rid, reason="operator_policy")
            jtable, idcol = "edge_event", "edge_id"
        else:
            rid = "ep-r5j"
            m.store.add_episode(Episode(id=rid, user_id="u", date="2026-11-24", summary="Ordinary episode",
                                        provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                              evidence_ref="ev-r5j")))
            m.redact("u", episode_id=rid, reason="operator_policy")
            jtable, idcol = "episode_event", "episode_id"
        con = m.store._conn
        rowid, state = con.execute(f"SELECT rowid, state FROM {jtable} WHERE {idcol}=? ORDER BY seq DESC LIMIT 1",
                                   (rid,)).fetchone()
        doc = json.loads(state)
        doc["retired_reason" if kind == "episode" else "invalidation_reason"] = TOKEN
        con.execute(f"UPDATE {jtable} SET state=? WHERE rowid=?", (json.dumps(doc), rowid))
        con.commit()
        hits = CF.scan(m.store, "u")
        assert [h.carrier for h in hits] == [f"{jtable}.after_redaction"] and not hits[0].removable, (
            [h.carrier for h in hits])
        assert f"{jtable}.after_redaction" in CF.RESIDUAL
        m.forget("u")
        assert not CF.scan(m.store, "u") and TOKEN not in T._dump(str(tmp_path / "m.db"))
    finally:
        m.close()
