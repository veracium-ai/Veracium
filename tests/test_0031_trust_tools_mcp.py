"""specs/0031 §4f: the seven trust tools on the MCP surface and at their `*_report` / `*_impl` pairs. INV-TT1, TT2,
TT4, TT5 (over MCP), TT6, TT7, TT11, TT13, TT17 and TT22. The framework adapters answer through the same `*_impl`
functions, and 0053's conformance suite (specs/evidence/0053/adapter_conformance, the trust tools' K-rows) proves
each adapter's result equals the `*_impl` result under the same bindings (INV-TT15); this file tests the impls and
the server's own wiring. Every mutating case runs on its own fresh store.
"""
import asyncio
import hashlib
import json

import pytest

from veracium import Memory, MemoryConfig
from veracium import mcp_server as M
from veracium.schema import ConfirmationCallPath as C, Edge, Episode, EvidenceAuthor, Provenance
from veracium.scope import Identity
from veracium.trust_tools import NOT_FOUND_DETAIL, PreviewTokenIssuer

@pytest.fixture(autouse=True)
def _needs_the_mcp_sdk():
    """Each cell needs the optional MCP SDK; skipped per cell, never the module at collection."""
    pytest.importorskip("mcp")


U = "alice"
TOOLS = ("find_facts", "correct_fact", "dispute_fact", "confirm_fact", "forget_fact", "forget_everything_preview",
         "forget_everything_confirm")
FORBIDDEN = {"user_id", "actor", "call_path", "date", "evidence_ref", "capability", "erasure", "principal",
             "source_id"}


def _mem(tmp_path, **cfg):
    tmp_path.mkdir(parents=True, exist_ok=True)
    return Memory(llm=lambda *a, **k: "x",
                  config=MemoryConfig(db_path=str(tmp_path / "v.db"), require_source_id=False,
                                      wiki_recompile_after_writes=0, **cfg))


def _edge(m, eid, obj="tea", user=U, **prov):
    m.store.add_edge(Edge(id=eid, user_id=user, subject="user", relation="likes", object=obj,
                          provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=f"ev-{eid}",
                                                **prov)))


def _episode(m, eid, user=U):
    m.store.add_episode(Episode(id=eid, user_id=user, date="2026-11-01", summary="said something",
                                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=f"ev-{eid}")))


def _digest(m) -> str:
    return hashlib.sha256("\n".join(m.store._conn.iterdump()).encode()).hexdigest()


def _call(server, name, args=None):
    out = asyncio.run(server.call_tool(name, args or {}))
    return json.loads(out[0].text)


def _args(name, eid="e-1", epid="ep-1"):
    return {"find_facts": {"query": "tea"}, "correct_fact": {"edge_id": eid, "corrected_value": "coffee"},
            "dispute_fact": {"edge_id": eid, "reason": "no"}, "confirm_fact": {"edge_id": eid},
            "forget_fact": {"edge_id": eid}, "forget_everything_preview": {},
            "forget_everything_confirm": {"preview_token": "tt1.x.y"}}[name]


def _report(name, m, user, args, **kw):
    fn = getattr(M, f"{name}_report")
    a = dict(args)
    if name == "correct_fact":
        return fn(m, user, a["edge_id"], a["corrected_value"], **kw)
    if name == "dispute_fact":
        return fn(m, user, a["edge_id"], a.get("reason", ""), **kw)
    if name == "confirm_fact":
        return fn(m, user, a["edge_id"], **kw)
    if name == "forget_fact":
        return fn(m, user, a.get("edge_id"), a.get("episode_id"), **kw)
    if name == "forget_everything_confirm":
        return fn(m, user, a["preview_token"], **kw)
    if name == "find_facts":
        return fn(m, user, a.get("query"), **kw)
    return fn(m, user, **kw)


def _kw(name, **extra):
    """the keywords each report takes, beyond its capability"""
    k = {}
    if name in ("forget_fact", "forget_everything_preview", "forget_everything_confirm"):
        k["erasure"] = extra.get("erasure")
    if name.startswith("forget_everything"):
        k["issuer"] = extra.get("issuer")
    if "principal" in extra:
        k["principal"] = extra["principal"]
    return k


# ------------------------------------------------------------------ INV-TT1: under `none`, every tool refuses
@pytest.mark.parametrize("capability", [None, "none"])
@pytest.mark.parametrize("name", TOOLS)
def test_under_none_every_report_refuses_counted_and_writes_nothing(tmp_path, capability, name):
    """Mutants: the gate removed from one *_report; the count omitted from the report; the count left in the result."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    before = _digest(m)
    rep = _report(name, m, U, _args(name), capability=capability,
                  **_kw(name, issuer=PreviewTokenIssuer(m.store.local_origin(), U)))
    assert rep.get("ok") is False and rep.get("refusal") == "attempted_elevation" \
        and rep.get("provenance_raises_discarded") == 1, rep
    assert _digest(m) == before
    server = M.build_server(m, default_user=U, capability=capability)
    out = _call(server, name, _args(name))
    assert out.get("refusal") == "attempted_elevation" and "provenance_raises_discarded" not in out, out
    assert _digest(m) == before


# ------------------------------------------------------------------ INV-TT2: the schemas, and ignored extras
def test_no_trust_tool_schema_has_a_bound_parameter(tmp_path):
    m = _mem(tmp_path)
    tools = {t.name: t for t in asyncio.run(M.build_server(m, capability="direct").list_tools())}
    for name in TOOLS:
        props = set(tools[name].inputSchema.get("properties", {}))
        assert not props & FORBIDDEN, (name, props & FORBIDDEN)
    assert "reason" not in tools["forget_fact"].inputSchema["properties"]


@pytest.mark.parametrize("source", [None, "chat-app"])
def test_an_extra_argument_cannot_override_a_binding_over_mcp(tmp_path, source):
    """INV-TT2 (TT-R2-03) and INV-TT5 over MCP at the configured source's default and set: attempted `actor`,
    `source_id`, `principal` and `capability` overrides are ignored; the persisted provenance carries the server's
    source and `mcp_direct`. Mutant: an extra argument reaching the call."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    server = M.build_server(m, default_user=U, capability="direct", source_id=source)
    extra = {"actor": "host", "source_id": "forged", "principal": "someone", "capability": "none", "user_id": "bob",
             "call_path": "host_api", "date": "2020-01-01"}
    out = _call(server, "dispute_fact", {"edge_id": "e-1", "reason": "no", **extra})
    assert out["ok"] is True
    ep = next(e for e in m.store.episodes(U) if e.provenance.evidence_ref == "dispute:e-1")
    assert ep.provenance.source_id == source and ep.provenance.call_path is C.MCP_DIRECT
    assert ep.summary.startswith("(user) disputed")


# ------------------------------------------------------------------ INV-TT4 over MCP
def test_confirm_fact_over_mcp_records_mcp_direct_in_the_row_and_the_episode(tmp_path):
    """Mutants: the library default left in place; the episode left unlabelled."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    out = _call(M.build_server(m, default_user=U, capability="direct"), "confirm_fact", {"edge_id": "e-1"})
    assert out["ok"] is True
    assert m.store.confirmations_for(U, "e-1")[0].call_path is C.MCP_DIRECT
    ep = next(e for e in m.store.episodes(U) if e.provenance.evidence_ref == "confirm:e-1")
    assert ep.provenance.call_path is C.MCP_DIRECT


# ------------------------------------------------------------------ INV-TT6: the reason is fixed
@pytest.mark.parametrize("target", ["edge", "episode"])
def test_forget_fact_always_redacts_with_subject_request(tmp_path, target):
    """Every schema-admitted input; the schema has no `reason`, and an extra one is ignored. Mutant: the reason taken
    from an argument."""
    m = _mem(tmp_path)
    _edge(m, "e-1"); _episode(m, "ep-1")
    args = {"edge_id": "e-1"} if target == "edge" else {"episode_id": "ep-1"}
    out = _call(M.build_server(m, default_user=U, capability="direct"), "forget_fact",
                {**args, "reason": "imported_notice"})
    assert out["ok"] is True and out["reason"] == "subject_request"
    assert "surviving_derived" in out                     # the full receipt with no principal (INV-TT12)


# ------------------------------------------------------------------ INV-TT12: no cascade; the list whole on the host path
def _rows(m, kind, ids):
    table = "edges" if kind == "edge" else "episodes"
    return {i: m.store._conn.execute(f"SELECT json FROM {table} WHERE id=?", (i,)).fetchone()[0] for i in ids}


@pytest.mark.parametrize("target", ["edge", "episode", "restored-consolidation-input"])
def test_forget_fact_does_not_cascade_and_names_every_derived_record(tmp_path, target):
    """§4d: per-fact forget redacts ONE record. Its derived records — an edge's source episode and the outcome
    episode that quotes it; the fact extracted from an episode — are left exactly as they were, and with no principal
    the receipt names every one of them (`surviving_derived` whole). A consolidation output stands beside its LIVE
    input only after a restore (consolidation consumes its inputs: 0041's
    test_a_consumed_consolidation_input_cannot_be_redacted), so the third case is 0041's restore pair
    (test_the_receipt_names_a_restored_output_whose_lineage_consumed_the_redacted_episode) driven through the TOOL:
    the output whose lineage consumed the input is named, `via` lineage, and left untouched. Mutants: a cascade
    added; the list dropped on the host path."""
    m = _mem(tmp_path)
    if target == "restored-consolidation-input":
        import json as _json
        from datetime import datetime, timezone
        from veracium.lifecycle import consolidate
        from veracium.portability import export_memory, import_memory
        src = _mem(tmp_path / "src")
        for i in range(8):
            src.store.add_episode(Episode(id=f"ep-{i}", user_id=U, date=f"2026-01-{i + 1:02d}", summary=f"day {i}",
                                          provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                                evidence_ref=f"ev-day-{i}")))
        export_memory(src.store, U, tmp_path / "before.jsonl")
        consolidate(src.store, lambda p, system=None, role=None: _json.dumps(
            {"records": [{"date": "2026-01-01", "summary": "week"}]}), U, src.config,
            now=datetime(2026, 9, 1, tzinfo=timezone.utc))
        export_memory(src.store, U, tmp_path / "after.jsonl")
        import_memory(m.store, tmp_path / "before.jsonl", restore=True)
        import_memory(m.store, tmp_path / "after.jsonl", restore=True)
        (cons,) = [e for e in m.store.episodes(U) if e.lineage]
        args, derived = {"episode_id": "ep-3"}, {("episode", cons.id)}
    elif target == "edge":
        _edge(m, "e-1")
        m.store.add_episode(Episode(id="ep-src", user_id=U, date="2026-11-01", summary="I like tea",
                                    provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                          evidence_ref="ev-e-1")))
        from veracium.schema import Outcome, OutcomeJudgmentDraft
        out_ep = m.store.append_outcome_if_head(U, "e-1", "run-1", None, OutcomeJudgmentDraft(
            author=EvidenceAuthor.USER, event_timestamp="2026-11-02", outcome=Outcome.CONFIRMED, summary="tea, yes"))
        args, derived = {"edge_id": "e-1"}, {("episode", "ep-src"), ("episode", out_ep.id)}
    else:
        _episode(m, "ep-1")
        m.store.add_edge(Edge(id="e-x", user_id=U, subject="user", relation="likes", object="tea",
                              provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-ep-1")))
        args, derived = {"episode_id": "ep-1"}, {("edge", "e-x")}
    before = {k: _rows(m, k, [i for kk, i in derived if kk == k]) for k in ("edge", "episode")}
    out = _call(M.build_server(m, default_user=U, capability="direct"), "forget_fact", args)
    assert out.get("ok") is True, out
    assert {(d["kind"], d["id"]) for d in out.get("surviving_derived", [])} == derived, out
    if target == "restored-consolidation-input":
        assert [d["via"] for d in out["surviving_derived"]] == ["lineage"], out
    for k in ("edge", "episode"):
        assert _rows(m, k, list(before[k])) == before[k], k          # no derived record touched
        assert not set(before[k]) & set(m.store.redacted_targets(U, k)), k


# ------------------------------------------------------------------ INV-TT7: another user's id is an unknown id
@pytest.mark.parametrize("name", ["correct_fact", "dispute_fact", "confirm_fact", "forget_fact"])
def test_another_users_id_and_an_unknown_id_give_one_response(tmp_path, name):
    """Mutants: a lookup by id without the user scope; a distinct detail for the other user."""
    out = {}
    for case in ("other", "unknown"):
        m = _mem(tmp_path / case)
        _edge(m, "e-bob", user="bob")
        before = _digest(m)
        server = M.build_server(m, default_user=U, capability="direct")
        out[case] = _call(server, name, _args(name, eid="e-bob" if case == "other" else "e-none"))
        assert _digest(m) == before
        m.close()
    assert out["other"] == out["unknown"] == {"ok": False, "refusal": "not_found_in_scope",
                                              "detail": NOT_FOUND_DETAIL}


def test_find_facts_writes_only_the_conditional_wiki_cache_row(tmp_path):
    """Round 2's witness `lookup_writes_and_keyset_replay`, its lookup half (TT-R2-02): find_facts is not write-free.
    On an empty user with the default configuration, the recall it runs publishes the code-owned empty wiki body: ONE
    write statement, into `wiki`, and no other table changes. The write is CONDITIONAL: a second find_facts, the cache
    now fresh, executes no write at all. Mutant: the cache freshness check ignored (every lookup republishes)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    m = Memory(llm=lambda *a, **k: pytest.fail("find_facts called a model"),
               config=MemoryConfig(db_path=str(tmp_path / "v.db"), require_source_id=False))
    server = M.build_server(m, default_user=U, capability="direct")
    tables = [r[0] for r in m.store._conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]

    def snap():
        return {t: sorted(map(repr, m.store._conn.execute(f'SELECT * FROM "{t}"'))) for t in tables}

    def writes_of(args):
        sql = []
        m.store._conn.set_trace_callback(sql.append)
        try:
            out = _call(server, "find_facts", args)
        finally:
            m.store._conn.set_trace_callback(None)
        assert out.get("ok") is True, out
        return [s for s in sql if s.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE", "REPLACE"))]

    a = snap()
    first = writes_of({"query": "empty"})
    b = snap()
    assert [t for t in tables if a[t] != b[t]] == ["wiki"] and len(b["wiki"]) == 1, (first, b["wiki"])
    assert len(first) == 1 and "INTO wiki" in first[0], first
    assert writes_of({"query": "empty"}) == []                  # the cache is fresh: the second lookup writes nothing


def test_find_facts_lists_only_the_deployments_user(tmp_path):
    m = _mem(tmp_path)
    _edge(m, "e-mine", "tea"); _edge(m, "e-bob", "tea too", user="bob")
    out = _call(M.build_server(m, default_user=U, capability="direct"), "find_facts", {"query": "tea"})
    ids = {u["id"] for u in out["units"]}
    assert "e-mine" in ids and "e-bob" not in ids and out["path"] == "query"


# ------------------------------------------------------------------ INV-TT11: refusals are data; failures raise
class _Boom(Memory):
    pass


@pytest.mark.parametrize("exc", [ValueError("v"), TypeError("t")])
def test_a_library_refusal_returns_serialized_and_never_raises(tmp_path, monkeypatch, exc):
    m = _mem(tmp_path)
    _edge(m, "e-1")
    monkeypatch.setattr(m, "dispute", lambda *a, **k: (_ for _ in ()).throw(exc))
    out = M.dispute_fact_impl(m, U, "e-1", "", capability="direct")
    # specs/0055 §4g E1: `detail` is the outward formatter's text (the class and the reason), never str(exc)
    from veracium.credentials import outward_text
    assert out == {"ok": False, "refusal": "refused", "detail": outward_text(exc)}


def test_a_scope_error_is_a_refusal_too(tmp_path, monkeypatch):
    from veracium.scope_linkage import ScopeError
    m = _mem(tmp_path)
    _edge(m, "e-1")
    monkeypatch.setattr(m, "confirm", lambda *a, **k: (_ for _ in ()).throw(ScopeError("s")))
    assert M.confirm_fact_impl(m, U, "e-1", capability="direct")["refusal"] == "refused"


def test_an_internal_failure_raises_and_is_never_turned_into_a_refusal(tmp_path, monkeypatch):
    """Mutant: a post-commit failure turned into a refusal."""
    import sqlite3
    m = _mem(tmp_path)
    _edge(m, "e-1")
    monkeypatch.setattr(m, "_record", lambda *a, **k: (_ for _ in ()).throw(sqlite3.OperationalError("disk")))
    with pytest.raises(sqlite3.OperationalError):
        M.dispute_fact_impl(m, U, "e-1", "", capability="direct")
    assert any(e.provenance.evidence_ref == "dispute:e-1" for e in m.store.episodes(U))   # it had committed


@pytest.mark.parametrize("principal", [None, "unconfigured", "ungroupable"])
def test_scope_configuration_refusals_return_serialized_and_write_nothing(tmp_path, principal):
    m = _mem(tmp_path, **({"scope_groups": {}} if principal == "ungroupable" else {}))
    _edge(m, "e-1")
    if principal is None:
        return
    p = Identity(None, "src-a") if principal == "unconfigured" else Identity("org", None)
    before = _digest(m)
    for name in TOOLS[:5]:
        out = _report(name, m, U, _args(name), capability="direct", principal=p,
                      **({"erasure": None} if name == "forget_fact" else {}))
        assert out["refusal"] == ("scope_unconfigured" if principal == "unconfigured" else "principal_ungroupable")
    assert _digest(m) == before


def test_correction_refused_is_a_committed_refusal_kept_through_the_tool(tmp_path):
    """TT-R2-02: an edge about another subject, corrected as the user, reaches the OTHER-subject refusal; the refusal
    plan is kept (supersession_refusals, supersession_operations, write_counter), the target stays active.
    Mutant: the committed refusal rolled back by an outer transaction."""
    m = _mem(tmp_path)
    m.store.add_edge(Edge(id="e-alice", user_id=U, subject="person:bob", relation="located_at", object="Rome",
                          provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev")))
    n = {t: m.store._conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
         for t in ("supersession_refusals", "supersession_operations")}
    try:
        out = _call(M.build_server(m, default_user=U, capability="direct"), "correct_fact",
                    {"edge_id": "e-alice", "corrected_value": "Oslo"})
    except Exception as exc:                      # a refusal raised to the transport is the defect, asserted below
        out = {"raised": f"{type(exc).__name__}: {exc}"}
    assert out.get("ok") is False and out.get("refusal") == "correction_refused", out
    for t, k in n.items():
        assert m.store._conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] > k, t
    assert next(e for e in m.store.edges(U) if e.id == "e-alice").active


# ------------------------------------------------------------------ INV-TT13: the gate order and the switch
FORGET = ("forget_fact", "forget_everything_preview", "forget_everything_confirm")


@pytest.mark.parametrize("erasure", [None, "on", "off"])
@pytest.mark.parametrize("name", FORGET)
def test_capability_first_then_erasure_then_principal(tmp_path, name, erasure):
    """Under `none` every tool returns attempted_elevation whatever `erasure`; under `direct` with `off` the three
    forget tools refuse erasure_disabled (also under a principal: `principal_scoped` never comes first) and the store
    is byte-identical. Mutants: the switch checked only in forget_everything_*; principal_scoped before
    erasure_disabled."""
    m = _mem(tmp_path, scope_groups={})
    _edge(m, "e-1")
    iss = PreviewTokenIssuer(m.store.local_origin(), U)
    before = _digest(m)
    none = _report(name, m, U, _args(name), capability=None, **_kw(name, erasure=erasure, issuer=iss))
    assert none.get("refusal") == "attempted_elevation", none
    if erasure == "off":
        for p in (None, Identity(None, "src-a")):
            out = _report(name, m, U, _args(name), capability="direct",
                          **_kw(name, erasure=erasure, issuer=iss, principal=p))
            assert out.get("refusal") == "erasure_disabled", (p, out)
        assert _digest(m) == before


@pytest.mark.parametrize("name", ["find_facts", "correct_fact", "dispute_fact", "confirm_fact"])
def test_erasure_off_leaves_the_other_four_working(tmp_path, name):
    m = _mem(tmp_path)
    _edge(m, "e-1")
    server = M.build_server(m, default_user=U, capability="direct", erasure="off")
    assert _call(server, name, _args(name))["ok"] is True


def test_absence_means_on_and_a_supplied_invalid_value_raises_at_construction(tmp_path):
    """Mutants: absence defaulting to off; an invalid value read as on."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    assert _call(M.build_server(m, default_user=U, capability="direct"), "forget_fact",
                 {"edge_id": "e-1"})["ok"] is True
    for bad in ("", "OFF", "no"):
        with pytest.raises(ValueError):
            M.build_server(m, default_user=U, capability="direct", erasure=bad)


# ------------------------------------------------------------------ INV-TT17 at the impls
@pytest.mark.parametrize("name", ["forget_everything_preview", "forget_everything_confirm"])
def test_the_whole_user_tools_refuse_any_principal_after_capability_and_erasure(tmp_path, name):
    """Mutants: the refusal on the preview only; the refusal skipped when erasure is on."""
    m = _mem(tmp_path, scope_groups={})
    _edge(m, "e-1")
    iss = PreviewTokenIssuer(m.store.local_origin(), U)
    preview = M.forget_everything_preview_impl(m, U, capability="direct", issuer=iss)
    assert "preview_token" in preview, preview          # absence of the erasure setting means ON (INV-TT13)
    tok = preview["preview_token"]
    before = _digest(m)
    args = {} if name == "forget_everything_preview" else {"preview_token": tok}
    out = _report(name, m, U, args, capability="direct", **_kw(name, erasure="on", issuer=iss,
                                                                 principal=Identity(None, "src-a")))
    assert out.get("refusal") == "principal_scoped" and _digest(m) == before, out


# ------------------------------------------------------------------ the two steps over MCP, one server's issuer
def test_the_erase_over_mcp_and_a_reconstructed_server_voids_the_token(tmp_path):
    m = _mem(tmp_path)
    _edge(m, "e-1"); _edge(m, "e-bob", user="bob")
    server = M.build_server(m, default_user=U, capability="direct")
    p = _call(server, "forget_everything_preview")
    assert set(p) == {"ok", "counts", "expires_at", "preview_token", "warning"}, p
    assert p["counts"]["edges"] == 1
    other = M.build_server(m, default_user=U, capability="direct")
    refused = _call(other, "forget_everything_confirm", {"preview_token": p["preview_token"]})
    assert refused.get("refusal") == "preview_unknown", refused
    done = _call(server, "forget_everything_confirm", {"preview_token": p["preview_token"]})
    assert done.get("ok") is True and done.get("edges") == 1, done
    assert m.store.edges(U, active_only=False) == [] and len(m.store.edges("bob")) == 1


# ------------------------------------------------------------------ INV-TT22: dispute's reason
@pytest.mark.parametrize("reason, ok", [("", True), ("é" * 1024, True), ("é" * 1025, False)])
def test_the_reason_cap_is_1024_code_points_and_refuses_before_any_mutation(tmp_path, reason, ok):
    """Mutants: truncation instead of refusal; the cap counted in bytes ('é' is two UTF-8 bytes)."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    before = _digest(m)
    out = M.dispute_fact_impl(m, U, "e-1", reason, capability="direct", call_path=C.MCP_DIRECT)
    if ok:
        assert out["ok"] is True
        ep = next(e for e in m.store.episodes(U) if e.provenance.evidence_ref == "dispute:e-1")
        assert reason in ep.summary
    else:
        assert out.get("refusal") == "reason_too_long" and _digest(m) == before, out


def test_a_malformed_reason_is_the_frameworks_schema_error(tmp_path):
    m = _mem(tmp_path)
    _edge(m, "e-1")
    with pytest.raises(Exception):
        asyncio.run(M.build_server(m, default_user=U, capability="direct").call_tool(
            "dispute_fact", {"edge_id": "e-1", "reason": {"not": "a string"}}))


def test_a_non_string_reason_on_the_adapters_path_is_refused_before_any_mutation(tmp_path):
    """INV-TT22's malformed input on the path the framework adapters call (`dispute_fact_impl`; over MCP the served
    schema refuses first, above): §4a gate 4, the tool's own type check. Mutant: the check removed (a list then
    passes the cap and reaches the library)."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    before = _digest(m)
    out = M.dispute_fact_impl(m, U, "e-1", ["not", "a string"], capability="direct", call_path=C.MCP_DIRECT)
    assert out == {"ok": False, "refusal": "refused", "detail": "reason must be a string"}, out
    assert _digest(m) == before


# ------------------------------------------------------------------ §4a gate 4: forget_fact's one target (INV-TT11)
@pytest.mark.parametrize("surface", ["mcp", "impl"])
@pytest.mark.parametrize("target", ["both", "neither"])
def test_forget_fact_takes_exactly_one_target_and_refuses_before_any_mutation(tmp_path, target, surface):
    """§4a gate 4: exactly one of `edge_id` and `episode_id`. Both and neither are `invalid_target`, serialized, writing
    nothing, over MCP and on the adapters' `*_impl` path. Mutants: the check removed; only `both` refused (`neither`
    then falls through to the target lookup and reads as `not_found_in_scope`)."""
    m = _mem(tmp_path)
    _edge(m, "e-1")
    _episode(m, "ep-1")
    before = _digest(m)
    args = {"edge_id": "e-1", "episode_id": "ep-1"} if target == "both" else {}
    out = (_call(M.build_server(m, default_user=U, capability="direct"), "forget_fact", args) if surface == "mcp"
           else M.forget_fact_impl(m, U, capability="direct", **args))
    assert out == {"ok": False, "refusal": "invalid_target", "detail": "exactly one of edge_id and episode_id"}, out
    assert _digest(m) == before
