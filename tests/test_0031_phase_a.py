"""specs/0031 Phase A — the host attestation capability (§3a, §4a, §4b-iii, §4d, §6).

Every invariant here carries the test NAME the accepted spec's §6 table
binds it to, and each is asserted against the SHIPPED machinery (stored
provenance, `authority.effective`, `scope_fingerprint` + the store's
`PLAN_STALE` refusal, `Edge.assertable`, the framework's REFLECTED tool
schema) — never restated from the spec's prose.

The behavioural matrix is a second, independent derivation of the pinned
§3a bridge table (research's tier-8 instrument is the first, frozen before
this code existed): {none, direct} × {author absent, user, assistant,
third_party} × {derived_from absent, user, third_party}.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import logging

import pytest

from veracium import Memory, MemoryConfig
from veracium import authority
from veracium.authority import scope_fingerprint
from veracium.mcp_server import (HostCapability, _BASELINE_AUTHOR, _AUTHOR,
                                 _OPERATOR_ONLY, _resolve_capability,
                                 build_server, remember_impl, remember_report)
from veracium.schema import (Disclosure, EvidenceAuthor, EvidenceContext,
                             SupersessionPlan)
from veracium.store.base import PLAN_STALE

U = "u"
TRIPLE = {"subject": "user", "relation": "has_diet", "object": "avoids dairy",
          "volatility": "durable"}
AUTHORS = (None, "user", "assistant", "third_party")
DERIVED = (None, "user", "third_party")
# restrictiveness order of the disclosure enum (schema.Disclosure)
_RESTRICT = {Disclosure.MENTIONABLE: 0, Disclosure.USE_ONLY: 1,
             Disclosure.QUARANTINED: 2}


class Fake:
    def __init__(self, scripts):
        self._s = list(scripts); self.i = 0
    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        out = self._s[self.i % len(self._s)]; self.i += 1
        return out if isinstance(out, str) else json.dumps(out)


def _mem(tmp_path, name, scripts=None):
    scripts = scripts or [{"triples": [TRIPLE], "episode": "diet noted"}]
    return Memory(llm=Fake(scripts),
                  config=MemoryConfig(db_path=f"{tmp_path}/{name}.db",
                                      wiki_recompile_after_writes=0))


def _write(tmp_path, name, cap, author=None, derived=None, *, spy=None):
    """One MCP write under `cap`; returns (report, stored edge, memory)."""
    mem = _mem(tmp_path, name)
    if spy is not None:
        orig = mem.remember
        def spying(*a, **k):
            spy.update(k)
            return orig(*a, **k)
        mem.remember = spying
    kw = {}
    if author is not None:
        kw["author"] = author
    if derived is not None:
        kw["derived_from"] = derived
    rep = remember_report(mem, U, "(scripted)", capability=cap, **kw)
    edges = mem.store.edges(U, active_only=False, include_quarantined=True)
    assert len(edges) == 1, edges
    return rep, edges[0], mem


def _stored(edge):
    pv = edge.provenance
    return (pv.author_of_evidence, pv.derived_from, edge.provenance.disclosure,
            bool(edge.assertable))


# --------------------------------------------------------------------------- #
# A. the capability, pinned (V-CAP-DEFAULT; A1–A7)
# --------------------------------------------------------------------------- #

def test_capability_absence_is_the_untrusted_cell(tmp_path):
    """V-CAP-DEFAULT: only ABSENCE resolves to `none`; EVERY supplied invalid
    value — the empty string included — raises at construction. The enum
    call is the one validator (§4a F3)."""
    assert _resolve_capability(None) is HostCapability.NONE
    assert _resolve_capability("none") is HostCapability.NONE
    assert _resolve_capability("direct") is HostCapability.DIRECT
    assert _resolve_capability(HostCapability.DIRECT) is HostCapability.DIRECT
    for bad in ("", "bogus", "DIRECT", " direct", "Direct", 123, 0, False, [], {}):
        with pytest.raises(ValueError):
            _resolve_capability(bad)
    pytest.importorskip("mcp")
    mem = _mem(tmp_path, "cap")
    try:
        build_server(mem, default_user=U)                  # absent → none
        build_server(mem, default_user=U, capability=None)
        build_server(mem, default_user=U, capability="direct")
        for bad in ("", "bogus", "DIRECT", 123):
            with pytest.raises(ValueError):
                build_server(mem, default_user=U, capability=bad)
    finally:
        mem.close()
    # the enum's closed set is exactly the two ruled values
    assert {c.value for c in HostCapability} == {"none", "direct"}
    # keyword-only, `None` default — the pinned constructor (§4a)
    p = inspect.signature(build_server).parameters["capability"]
    assert p.kind is inspect.Parameter.KEYWORD_ONLY and p.default is None


def test_build_server_never_reads_the_environment(tmp_path, monkeypatch):
    """A6 precedence: `build_server(capability=...)` is authoritative and the
    function never consults the environment — `main()` reads it ONCE and
    passes the value. An env var set to `direct` beside an absent kwarg
    must NOT elevate."""
    pytest.importorskip("mcp")
    monkeypatch.setenv("VERACIUM_MCP_CAPABILITY", "direct")
    mem = _mem(tmp_path, "env")
    try:
        server = build_server(mem, default_user=U)
        asyncio.run(server.call_tool("remember", {"text": "(scripted)"}))
        e = mem.store.edges(U, active_only=False, include_quarantined=True)[0]
        assert e.provenance.author_of_evidence is EvidenceAuthor.THIRD_PARTY, (
            "an environment variable reached build_server — it must be passed, "
            "never read")
    finally:
        mem.close()


def test_main_reads_the_environment_once_and_refuses_a_supplied_invalid(tmp_path, monkeypatch):
    """A3/A6 at the entry point: unset → absence (None) → none; set →
    passed through; set EMPTY → supplied-and-invalid → refuse to start with
    a message naming the variable. `main()` is exercised with the memory and
    the server stubbed, so only its environment handling is under test."""
    pytest.importorskip("mcp")
    from veracium import mcp_server as M
    seen = {}

    class _Srv:
        def run(self):
            seen["ran"] = True

    def fake_build_server(mem, *, default_user, capability=None):
        seen["capability"] = capability
        _resolve_capability(capability)          # the real validator, kept
        return _Srv()

    monkeypatch.setattr(M, "build_memory", lambda: object())
    monkeypatch.setattr(M, "build_server", fake_build_server)
    monkeypatch.delenv("VERACIUM_MCP_CAPABILITY", raising=False)
    M.main([])
    assert seen["capability"] is None and seen["ran"]
    monkeypatch.setenv("VERACIUM_MCP_CAPABILITY", "direct")
    M.main([])
    assert seen["capability"] == "direct"
    monkeypatch.setenv("VERACIUM_MCP_CAPABILITY", "")
    with pytest.raises(SystemExit, match="VERACIUM_MCP_CAPABILITY"):
        M.main([])
    monkeypatch.setenv("VERACIUM_MCP_CAPABILITY", "bogus")
    with pytest.raises(SystemExit, match="refusing to start"):
        M.main([])


def test_capability_is_immutable_after_construction(tmp_path, monkeypatch):
    """A7: resolved once, retained by the tool closures; a later environment
    change does not alter an already-constructed server (one server lifetime
    cannot span two baselines)."""
    pytest.importorskip("mcp")
    mem = _mem(tmp_path, "immut")
    try:
        server = build_server(mem, default_user=U, capability="direct")
        monkeypatch.setenv("VERACIUM_MCP_CAPABILITY", "none")
        asyncio.run(server.call_tool("remember", {"text": "(scripted)"}))
        monkeypatch.delenv("VERACIUM_MCP_CAPABILITY")
        e = mem.store.edges(U, active_only=False, include_quarantined=True)[0]
        assert e.provenance.author_of_evidence is EvidenceAuthor.USER
    finally:
        mem.close()


def test_the_startup_diagnostic_is_operator_only(tmp_path, caplog):
    """I3, two-sided: the effective capability appears in the operator log at
    construction and in NO model-visible surface (schemas, results)."""
    pytest.importorskip("mcp")
    mem = _mem(tmp_path, "diag")
    try:
        with caplog.at_level(logging.INFO, logger="veracium.mcp"):
            server = build_server(mem, default_user=U, capability="direct")
        assert any("host capability 'direct'" in r.getMessage() for r in caplog.records)
        tools = asyncio.run(server.list_tools())
        assert "capability" not in json.dumps([t.model_dump() for t in tools])
        res = remember_impl(mem, U, "(scripted)", capability="direct")
        assert "capability" not in json.dumps(res)
    finally:
        mem.close()


# --------------------------------------------------------------------------- #
# B. author loses its default (V-AUTHOR-BASELINE)
# --------------------------------------------------------------------------- #

def test_author_has_no_default_of_its_own(tmp_path):
    """V-AUTHOR-BASELINE: absent `author` resolves to the capability baseline
    and NEVER to "user"; the shipped default is gone from both signatures."""
    for fn in (remember_impl, remember_report):
        assert inspect.signature(fn).parameters["author"].default is None
    _, e_none, m1 = _write(tmp_path, "b-none", "none")
    _, e_direct, m2 = _write(tmp_path, "b-direct", "direct")
    m1.close(); m2.close()
    assert e_none.provenance.author_of_evidence is EvidenceAuthor.THIRD_PARTY
    assert e_direct.provenance.author_of_evidence is EvidenceAuthor.USER
    assert _BASELINE_AUTHOR == {HostCapability.NONE: "third_party",
                                HostCapability.DIRECT: "user"}
    # the tool's own signature (the REFLECTED default) — no "user" anywhere
    pytest.importorskip("mcp")
    mem = _mem(tmp_path, "b-tool")
    try:
        server = build_server(mem, default_user=U)
        rem = [t for t in asyncio.run(server.list_tools()) if t.name == "remember"][0]
        author = _schema(rem, "input")["properties"]["author"]
        assert author.get("default") is None
    finally:
        mem.close()


# --------------------------------------------------------------------------- #
# C. inert-under-none: ordering, discard, count (§2c-i; §4d)
# --------------------------------------------------------------------------- #

def test_malformed_values_raise_regardless_of_capability(tmp_path):
    """Pipeline step 2: a SUPPLIED value outside its closed set RAISES under
    both capabilities — invalid strings, the empty string, wrong JSON types —
    and nothing is written."""
    for cap in ("none", "direct"):
        for bad in ("bogus", "", "USER", "system", 123, 1.5, [], {}, True):
            mem = _mem(tmp_path, f"mal-{cap}-{abs(hash(repr(bad)))}")
            try:
                with pytest.raises(ValueError):
                    remember_report(mem, U, "x", author=bad, capability=cap)
                with pytest.raises(ValueError):
                    remember_report(mem, U, "x", derived_from=bad, capability=cap)
                assert mem.store.edges(U, active_only=False,
                                       include_quarantined=True) == []
            finally:
                mem.close()


@pytest.mark.parametrize("cap,author,derived,expected", [
    ("none", None, None, 0),
    ("none", "user", None, 1),            # attempted elevation
    ("none", "assistant", None, 1),       # the round-1 F1 cell
    ("none", "third_party", None, 0),     # equal restatement — not a raise
    ("none", None, "user", 1),            # the P3-3 mechanism
    ("none", None, "third_party", 0),     # equal restatement on the derived leg
    ("none", "user", "user", 2),          # per VALID SUPPLIED FIELD, not per request
    ("none", "assistant", "third_party", 1),
    ("direct", None, None, 0),
    ("direct", "assistant", None, 0),     # restriction honoured — not counted
    ("direct", "third_party", None, 0),
    ("direct", "user", None, 0),          # equal restatement of the top
    ("direct", None, "third_party", 0),
    ("direct", None, "user", 0),
])
def test_discard_counter_counts_per_valid_field_attempted_elevation(tmp_path, cap, author, derived, expected):
    """C2, pinned: `provenance_raises_discarded` increments once per VALID
    SUPPLIED FIELD discarded as an attempted elevation — not per request;
    invalid values raised uncounted; equal restatements and honoured
    restrictions uncounted."""
    rep, _, mem = _write(tmp_path, f"cnt-{cap}-{author}-{derived}", cap, author, derived)
    mem.close()
    assert rep["provenance_raises_discarded"] == expected


def test_counter_present_as_zero_on_every_returned_path(tmp_path):
    """The shipped `agreement_floored` shape: an absent key is not a zero. The
    key is present on the normal path AND on ingest's unparseable path (the
    extractor returning garbage)."""
    rep, _, mem = _write(tmp_path, "z-normal", "none")
    mem.close()
    assert rep["provenance_raises_discarded"] == 0
    mem = _mem(tmp_path, "z-unparseable", scripts=["not json at all"])
    try:
        rep = remember_report(mem, U, "(scripted)", capability="none")
        assert rep.get("unparseable") is True
        assert rep["provenance_raises_discarded"] == 0
    finally:
        mem.close()


def test_counter_and_capability_never_reach_the_tool_result(tmp_path):
    """§4d: a model that learns how often its elevation attempts are refused
    learns to probe. The tool result carries neither the counter nor the
    capability; every operator counter in the strip list is absent too."""
    assert "provenance_raises_discarded" in _OPERATOR_ONLY
    for cap, author, derived in (("none", "user", "user"), ("direct", None, None)):
        mem = _mem(tmp_path, f"strip-{cap}")
        try:
            res = remember_impl(mem, U, "(scripted)", author=author,
                                derived_from=derived, capability=cap)
            flat = json.dumps(res)
            assert "provenance_raises_discarded" not in flat
            assert "capability" not in flat
            for k in _OPERATOR_ONLY:
                assert k not in res
            # ...while the library-level report still carries them all
            rep = remember_report(mem, U, "(scripted)", author=author,
                                  derived_from=derived, capability=cap)
            assert "provenance_raises_discarded" in rep
        finally:
            mem.close()


# --------------------------------------------------------------------------- #
# D. the bridge — the §3a PINNED table, one test per row (V-ONE-CARRIER)
# --------------------------------------------------------------------------- #

def test_capability_maps_to_one_carrier():
    """V-ONE-CARRIER: passing both carriers raises — asserted on the SHIPPED
    `ValueError` from `_resolve_context`, not restated."""
    from veracium.ingest import _resolve_context
    for x in (EvidenceAuthor.USER, EvidenceAuthor.ASSISTANT, EvidenceAuthor.THIRD_PARTY):
        with pytest.raises(ValueError, match="EITHER context= OR the legacy derived_from"):
            _resolve_context(EvidenceContext.direct(), x)
    # the first-party cell, verified as §3a's closing line states it
    assert _resolve_context(EvidenceContext.direct(), None) is None
    assert authority.effective(EvidenceAuthor.USER, None) == 3


def test_bridge_row_1_direct_and_nothing_mints_direct(tmp_path):
    spy = {}
    _, e, mem = _write(tmp_path, "row1", "direct", spy=spy)
    mem.close()
    assert spy["context"] == EvidenceContext.direct() and "derived_from" not in spy
    assert _stored(e) == (EvidenceAuthor.USER, None, Disclosure.MENTIONABLE, True)


@pytest.mark.parametrize("x,expect", [
    ("third_party", (EvidenceAuthor.USER, EvidenceAuthor.THIRD_PARTY, Disclosure.USE_ONLY, False)),
    ("user", (EvidenceAuthor.USER, EvidenceAuthor.USER, Disclosure.MENTIONABLE, True)),
    ("assistant", (EvidenceAuthor.USER, EvidenceAuthor.ASSISTANT, Disclosure.USE_ONLY, False)),
])
def test_bridge_row_2_direct_and_supplied_x_mints_derived_x(tmp_path, x, expect):
    """ONE carrier, `derived(X)`, the descent recorded IN it — the restriction
    honoured THROUGH the declaration, never beside it."""
    spy = {}
    _, e, mem = _write(tmp_path, f"row2-{x}", "direct", derived=x, spy=spy)
    mem.close()
    assert spy["context"] == EvidenceContext.derived(_AUTHOR[x])
    assert "derived_from" not in spy
    assert _stored(e) == expect


@pytest.mark.parametrize("author", AUTHORS)
@pytest.mark.parametrize("derived", DERIVED)
def test_bridge_row_3_none_is_the_absent_context_floor(tmp_path, author, derived):
    """Under `none`: no context and no derived_from, whatever the model
    supplies — the absent-context floor at the ingest site."""
    spy = {}
    _, e, mem = _write(tmp_path, f"row3-{author}-{derived}", "none", author, derived, spy=spy)
    mem.close()
    assert spy["context"] is None and "derived_from" not in spy
    assert _stored(e) == (EvidenceAuthor.THIRD_PARTY, EvidenceAuthor.THIRD_PARTY,
                          Disclosure.USE_ONLY, False)


# --------------------------------------------------------------------------- #
# E. the Phase-A invariants, FOUR obligations asserted separately
# --------------------------------------------------------------------------- #

def _baseline_and_cells(tmp_path, cap):
    _, base, m = _write(tmp_path, f"base-{cap}", cap)
    m.close()
    cells = {}
    for a in AUTHORS:
        for d in DERIVED:
            _, e, m = _write(tmp_path, f"cell-{cap}-{a}-{d}", cap, a, d)
            m.close()
            cells[(a, d)] = e
    return base, cells


@pytest.mark.parametrize("cap", ("none", "direct"))
def test_disclosure_descends_only(tmp_path, cap):
    """V-DESCEND-DISCLOSURE: no model-supplied value yields a LESS restrictive
    disclosure than the capability baseline."""
    base, cells = _baseline_and_cells(tmp_path, cap)
    for k, e in cells.items():
        assert _RESTRICT[e.provenance.disclosure] >= _RESTRICT[base.provenance.disclosure], (cap, k)


@pytest.mark.parametrize("cap", ("none", "direct"))
def test_authority_descends_only(tmp_path, cap):
    """V-DESCEND-AUTHORITY: no model-supplied value yields a HIGHER effective
    supersession authority than the baseline (the round-1 counterexample's
    axis), measured by the shipped `authority.edge_effective`."""
    base, cells = _baseline_and_cells(tmp_path, cap)
    for k, e in cells.items():
        assert authority.edge_effective(e) <= authority.edge_effective(base), (cap, k)


@pytest.mark.parametrize("cap", ("none", "direct"))
def test_shaping_restricts_only(tmp_path, cap):
    """V-RESTRICT-SHAPING: the shaped record under a model-supplied value
    withholds at least what the baseline withholds — measured on the gate's
    shared predicate `Edge.assertable` (0023 §4a-iv): a record the baseline
    withholds is withheld under every supplied value."""
    base, cells = _baseline_and_cells(tmp_path, cap)
    for k, e in cells.items():
        assert (not base.assertable) <= (not e.assertable), (cap, k)   # withholds ⊇


@pytest.mark.parametrize("cap", ("none", "direct"))
def test_fingerprint_preserve_or_invalidate(tmp_path, cap):
    """V-FINGERPRINT-STABLE-OR-STALE: a model-supplied value either leaves the
    record's contribution to `scope_fingerprint` unchanged, OR every plan
    computed against the old fingerprint refuses as `PlanStale` — asserted
    through the store's own `apply_supersession_plan`, which returns the
    shipped `PLAN_STALE` sentinel. The invariant asserts NO ordering."""
    base, cells = _baseline_and_cells(tmp_path, cap)
    fp_base = scope_fingerprint([base])
    for k, e in cells.items():
        if scope_fingerprint([e]) == fp_base:
            continue                                   # preserved
        # invalidate: a plan computed against the OLD scope state refuses
        mem = _mem(tmp_path, f"stale-{cap}-{k[0]}-{k[1]}")
        try:
            remember_report(mem, U, "(scripted)", capability=cap)          # old state
            old = scope_fingerprint(mem.store.edges(U, subject="user", relation="has_diet",
                                                    active_only=True, include_quarantined=True))
            remember_report(mem, U, "(scripted)", capability=cap,
                            **({"author": k[0]} if k[0] else {}),
                            **({"derived_from": k[1]} if k[1] else {}))   # the supplied write
            edges = mem.store.edges(U, active_only=True, include_quarantined=True)
            plan = SupersessionPlan(incoming_edge=edges[-1], insert_incoming=False,
                                    operation_id="stale-probe", expected_state=old)
            assert mem.store.apply_supersession_plan(plan) is PLAN_STALE, (cap, k)
        finally:
            mem.close()


def test_none_baseline_is_the_bottom_element(tmp_path):
    """V-INERT-UNDER-NONE: under `none` EVERY supplied author/derived_from
    value leaves the stored record identical to the baseline — the case F1
    was made of: `assistant` must not reach authority 1."""
    base, cells = _baseline_and_cells(tmp_path, "none")
    for k, e in cells.items():
        assert _stored(e) == _stored(base), k
        assert authority.edge_effective(e) == 0, k
    assert authority.edge_effective(cells[("assistant", None)]) == 0


def test_no_umbrella_ordering_claim():
    """V-OBLIGATIONS-SEPARATE: the four obligations are checked by FOUR
    invariants, never one umbrella — this module carries them as four
    distinct tests, and no test here claims a single order across them."""
    import sys
    mod = sys.modules[__name__]
    four = ("test_disclosure_descends_only", "test_authority_descends_only",
            "test_shaping_restricts_only", "test_fingerprint_preserve_or_invalidate")
    fns = [getattr(mod, n) for n in four]
    assert len({id(f) for f in fns}) == 4
    umbrella = [n for n, f in vars(mod).items()
                if n.startswith("test_") and callable(f) and n not in four
                and "restrict_only" in n and "shaping" not in n]
    assert not umbrella, f"an umbrella restrict-only test appeared: {umbrella}"


# --------------------------------------------------------------------------- #
# E2 / E3 / V-NO-USER-ID-ARG — the REFLECTED surface (discovered, not listed)
# --------------------------------------------------------------------------- #

def _schema(tool, which: str) -> dict:
    """The reflected schema, SDK-version-tolerant (mcp 1.x spells it
    `inputSchema`, 2.x `input_schema`) — and ASSERTED present for inputs:
    a sweep over a missing key passes vacuously, which is how the first
    branch CI run found this test sweeping nothing under the 2.x SDK."""
    d = tool if isinstance(tool, dict) else tool.model_dump()
    for k in (f"{which}Schema", f"{which}_schema"):
        if d.get(k) is not None:
            return d[k]
    if which == "input":
        raise AssertionError(f"no input schema reflected for tool {d.get('name')!r}: {sorted(d)}")
    return {}


def _reflected(tmp_path, cap=None):
    pytest.importorskip("mcp")
    mem = _mem(tmp_path, f"reflect-{cap}")
    try:
        server = build_server(mem, default_user=U, capability=cap)
        return [t.model_dump() for t in asyncio.run(server.list_tools())]
    finally:
        mem.close()


def test_capability_is_host_only(tmp_path):
    """V-CAPABILITY-HOST-ONLY (E2): `capability` and the discard counter appear
    in NO model-visible surface — every reflected input AND output schema of
    every REGISTERED tool, under both capabilities."""
    for cap in (None, "direct"):
        tools = _reflected(tmp_path, cap)
        assert tools, "no tools registered"
        for t in tools:
            flat = json.dumps({"in": _schema(t, "input"), "out": _schema(t, "output"),
                               "desc": t.get("description")})
            assert "properties" in _schema(t, "input") or t["name"] == "maintain"
            assert "capability" not in flat, (t["name"], cap)
            assert "provenance_raises_discarded" not in flat, (t["name"], cap)


def test_tool_schemas_omit_identity_arguments(tmp_path):
    """V-NO-USER-ID-ARG (§4b-iii, pinned; research's adjudication 2026-09-04:
    EVERY served tool): no tool schema exposes `user_id`, `proposer`,
    `resolver` or a turn identifier — absent BY SCHEMA, asserted against the
    built server's reflected schema of every registered tool, no allowlist.
    A model-suppliable `user_id` on recall would be a cross-principal READ."""
    tools = {t["name"]: t for t in _reflected(tmp_path)}
    props = {n: set(_schema(t_, "input").get("properties", {})) for n, t_ in tools.items()}
    assert props["remember"] == {"text", "author", "event_type", "date", "derived_from"}
    assert props["recall"] == {"query", "token_budget"}
    assert props["answer"] == {"query"}
    assert props["maintain"] == set()
    for name, t_ in tools.items():
        flat = json.dumps({"in": _schema(t_, "input"), "out": _schema(t_, "output")})
        for forbidden in ("user_id", "proposer", "resolver", "turn_id", "principal"):
            assert forbidden not in flat, (name, forbidden)


def test_a_smuggled_user_id_is_inert_on_every_read_tool(tmp_path):
    """Research's red-team probe (2026-09-04), made permanent: absence-by-
    schema is the mechanism, and this is its INERTNESS demonstrated rather
    than asserted. With the deployment principal's fact written, a call that
    smuggles `user_id="mallory"` through the framework (which drops unknown
    arguments rather than refusing) returns the DEPLOYMENT principal's data,
    and the foreign id's store holds nothing — on recall, answer and
    maintain alike. The identity boundary holds by construction; a
    conformant transport that refuses instead of dropping is stricter, and
    also fine."""
    pytest.importorskip("mcp")
    mem = _mem(tmp_path, "smuggle", scripts=[
        {"triples": [TRIPLE], "episode": "diet noted"}, "no"])
    try:
        server = build_server(mem, default_user=U, capability="direct")
        asyncio.run(server.call_tool("remember", {"text": "(scripted)"}))
        assert len(mem.store.edges(U)) == 1
        for tool, args in (("recall", {"query": "diet"}), ("answer", {"query": "diet?"}),
                           ("maintain", {})):
            try:
                out = asyncio.run(server.call_tool(tool, dict(args, user_id="mallory")))
            except Exception as e:                       # a refusing transport is stricter, also fine
                assert "user_id" in str(e) or "unexpected" in str(e).lower(), e
                continue
            if tool == "recall":
                assert "dairy" in json.dumps(out, default=str)
        assert mem.store.edges("mallory", active_only=False, include_quarantined=True) == []
        assert len(mem.store.edges(U)) == 1
    finally:
        mem.close()


def test_phase_a_inventory(tmp_path):
    """V-PHASE-A-INVENTORY (E3): the registered tools, discovered from the
    built server, are exactly the four pre-Phase-A tools — no proposal,
    resolution, correction, confirmation, deletion or trust-mutation
    operation was added. Identity, not name-words: the set is pinned."""
    names = sorted(t["name"] for t in _reflected(tmp_path))
    assert names == ["answer", "maintain", "recall", "remember"]


# --------------------------------------------------------------------------- #
# V-COMPAT (narrowed, F6): identical except the required flips, ENUMERATED
# --------------------------------------------------------------------------- #

def _old_mcp_mapping(mem, author, derived):
    """The PRE-Phase-A `remember_impl` mapping, executed through the shipped
    library path (which Phase A does not touch): `author` defaulted to
    "user"; `derived_from` passed straight through; no context."""
    return mem.remember(U, "(scripted)",
                        author=_AUTHOR[author or "user"],
                        derived_from=_AUTHOR[derived] if derived else None)


def test_no_capability_behaviour_identical_except_the_required_flips(tmp_path):
    """V-COMPAT: capability `none` ⇒ every cell identical to the pre-Phase-A
    behaviour EXCEPT the changes §6a requires, each difference attributed to
    exactly one of them: (1) the stored `author_of_evidence` is the baseline
    `third_party` rather than the model's say-so — the spec names the
    no-explicit-author cell; V-INERT-UNDER-NONE extends the same change to
    every supplied author (the F1 cell); (2) P3-3's flip — a model-supplied
    `derived_from="user"` no longer elevates (stored derivation, disclosure
    and assertability follow). No third kind of difference exists."""
    kinds = set()
    for a in AUTHORS:
        for d in DERIVED:
            old_mem = _mem(tmp_path, f"old-{a}-{d}")
            try:
                old_rep = dict(_old_mcp_mapping(old_mem, a, d))
                old_e = old_mem.store.edges(U, active_only=False, include_quarantined=True)[0]
            finally:
                old_mem.close()
            new_rep, new_e, m = _write(tmp_path, f"new-{a}-{d}", "none", a, d)
            m.close()
            # the write's own receipt (counts) is identical
            for k in ("facts", "quarantined", "unparseable"):
                assert old_rep.get(k) == new_rep.get(k), (a, d, k)
            o, n = _stored(old_e), _stored(new_e)
            if o == n:
                continue
            if o[0] is not n[0]:
                kinds.add("stored-author-is-the-baseline")
                assert n[0] is EvidenceAuthor.THIRD_PARTY
            if o[1] is not n[1]:
                kinds.add("P3-3-derived-user-no-longer-elevates")
                assert d == "user" and n[1] is EvidenceAuthor.THIRD_PARTY
            # disclosure/assertability differences must be CONSEQUENCES of the two
            if o[2] is not n[2] or o[3] != n[3]:
                assert (o[0] is not n[0]) or (o[1] is not n[1]), (a, d)
    assert kinds == {"stored-author-is-the-baseline",
                     "P3-3-derived-user-no-longer-elevates"}


def test_the_s2_interaction_direct_plus_future_date_is_stored_not_assertable(tmp_path):
    """H3 — the exact scenario the ordering precondition existed for: under
    `direct` an inside-skew future date is STORED, `valid_from` in the
    future, NOT assertable, and grounds by itself when the clock arrives
    (specs/0032)."""
    from datetime import date, timedelta
    from veracium import schema
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    mem = _mem(tmp_path, "s2")
    try:
        remember_report(mem, U, "(scripted)", capability="direct", date=tomorrow)
        e = mem.store.edges(U, active_only=False, include_quarantined=True)[0]
        assert e.provenance.disclosure is Disclosure.MENTIONABLE
        assert not e.valid_now and not e.assertable
        assert e.active and not e.quarantined and not e.use_only
    finally:
        mem.close()
