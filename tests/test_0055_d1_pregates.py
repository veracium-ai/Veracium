"""specs/0055 §4b-ii D1 (v0.5.6): the served boundary's content-free pre-gates may refuse before §4b runs, and none
echoes any part of a value.

D1's pre-gates read no free-text content and write nothing: the capability gate and the erasure setting, the scope
configuration, the target's presence by its lookup id, a type or length check of a free-text argument, and a
closed-vocabulary check. Each refusal names the gate, the target id, the scope, or the field and its limit. This file
drives every pre-gate at every site D1 lists, with a credential-shaped value in EVERY free-text argument (and in
`source_id`, an identifier §4b screens), and asserts for each: the refusal is the gate's own (so the call did not
reach §4b and pass vacuously), the store's bytes are unchanged, and the outward result carries no 8-character window
of any shaped value. The consequence D1 states is pinned too: a shaped `corrected_value` on an unknown edge id is
`not_found_in_scope`, not `credential_refused`.

No structural test token appears literally: vectors.py assembles them at run time.
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from veracium import Memory, MemoryConfig
from veracium import mcp_server as M
from veracium.scope import Identity

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


V = _load("_0055_vectors_d1", ROOT / "specs" / "evidence" / "0055" / "vectors.py")
#: four shapes of four classes; every free-text argument of a case carries one
SHAPES = {"dburl": V.DBURL, "github": V.GH, "anthropic": V.ANTH, "jwt": V.JWT}
U = "u-d1"
WINDOW = 8


def _mem(tmp_path, **cfg):
    tmp_path.mkdir(parents=True, exist_ok=True)
    return Memory(llm=lambda *a, **k: "x",
                  config=MemoryConfig(db_path=str(tmp_path / "v.db"), require_source_id=False,
                                      wiki_recompile_after_writes=0, **cfg))


def _digest(m) -> str:
    return hashlib.sha256("\n".join(m.store._conn.iterdump()).encode()).hexdigest()


def _echoes(text: str, shaped: str) -> list:
    """Every WINDOW-character window of `shaped` found in `text`: "no part of it", not only the whole value."""
    flat = text.replace(V.ZW, "")
    return sorted({shaped[i:i + WINDOW] for i in range(len(shaped) - WINDOW + 1) if shaped[i:i + WINDOW] in flat})


UNCONF = Identity(None, "src-a")          # a principal with no scope policy configured: scope_unconfigured
UNGROUP = Identity("org", None)           # a principal with no source_id, under a configured policy


def _cases(s):
    """(site, gate, memory config, call, expected refusal). `s` is the shaped value; each call puts it in every
    free-text argument the site takes, and in source_id where the site takes one."""
    long_reason = (s + " ") * (M.DISPUTE_REASON_MAX // (len(s) + 1) + 1)
    assert len(long_reason) > M.DISPUTE_REASON_MAX
    return [
        # correct_fact_report and confirm_fact_report: capability, scope configuration, target presence
        ("correct_fact", "capability", {}, lambda m: M.correct_fact_report(
            m, U, "e-1", s, capability=None, source_id=s), "attempted_elevation"),
        ("correct_fact", "scope-unconfigured", {}, lambda m: M.correct_fact_report(
            m, U, "e-1", s, capability="direct", principal=UNCONF, source_id=s), "scope_unconfigured"),
        ("correct_fact", "scope-ungroupable", {"scope_groups": {}}, lambda m: M.correct_fact_report(
            m, U, "e-1", s, capability="direct", principal=UNGROUP, source_id=s), "principal_ungroupable"),
        # D1's stated consequence: a shaped corrected_value on an unknown id is not_found_in_scope
        ("correct_fact", "target-presence", {}, lambda m: M.correct_fact_report(
            m, U, "e-none", s, capability="direct", source_id=s), "not_found_in_scope"),
        ("confirm_fact", "capability", {}, lambda m: M.confirm_fact_report(
            m, U, "e-1", capability=None, source_id=s), "attempted_elevation"),
        ("confirm_fact", "scope-unconfigured", {}, lambda m: M.confirm_fact_report(
            m, U, "e-1", capability="direct", principal=UNCONF, source_id=s), "scope_unconfigured"),
        ("confirm_fact", "scope-ungroupable", {"scope_groups": {}}, lambda m: M.confirm_fact_report(
            m, U, "e-1", capability="direct", principal=UNGROUP, source_id=s), "principal_ungroupable"),
        ("confirm_fact", "target-presence", {}, lambda m: M.confirm_fact_report(
            m, U, "e-none", capability="direct", source_id=s), "not_found_in_scope"),
        # dispute_fact_report: capability, the reason's type and length, scope configuration, target presence
        ("dispute_fact", "capability", {}, lambda m: M.dispute_fact_report(
            m, U, "e-1", s, capability=None, source_id=s), "attempted_elevation"),
        ("dispute_fact", "reason-type", {}, lambda m: M.dispute_fact_report(
            m, U, "e-1", [s], capability="direct", source_id=s), "refused"),
        ("dispute_fact", "reason-too-long", {}, lambda m: M.dispute_fact_report(
            m, U, "e-1", long_reason, capability="direct", source_id=s), "reason_too_long"),
        ("dispute_fact", "scope-unconfigured", {}, lambda m: M.dispute_fact_report(
            m, U, "e-1", s, capability="direct", principal=UNCONF, source_id=s), "scope_unconfigured"),
        ("dispute_fact", "scope-ungroupable", {"scope_groups": {}}, lambda m: M.dispute_fact_report(
            m, U, "e-1", s, capability="direct", principal=UNGROUP, source_id=s), "principal_ungroupable"),
        ("dispute_fact", "target-presence", {}, lambda m: M.dispute_fact_report(
            m, U, "e-none", s, capability="direct", source_id=s), "not_found_in_scope"),
        # forget_fact_report: capability and erasure, scope configuration, target presence (no free text)
        ("forget_fact", "capability", {}, lambda m: M.forget_fact_report(
            m, U, edge_id="e-1", capability=None), "attempted_elevation"),
        ("forget_fact", "erasure", {}, lambda m: M.forget_fact_report(
            m, U, edge_id="e-1", capability="direct", erasure="off"), "erasure_disabled"),
        ("forget_fact", "scope-unconfigured", {}, lambda m: M.forget_fact_report(
            m, U, edge_id="e-1", capability="direct", principal=UNCONF), "scope_unconfigured"),
        ("forget_fact", "scope-ungroupable", {"scope_groups": {}}, lambda m: M.forget_fact_report(
            m, U, edge_id="e-1", capability="direct", principal=UNGROUP), "principal_ungroupable"),
        ("forget_fact", "target-presence", {}, lambda m: M.forget_fact_report(
            m, U, edge_id="e-none", capability="direct"), "not_found_in_scope"),
        # forget_everything_preview_report and forget_everything_confirm_report: capability and erasure
        ("forget_everything_preview", "capability", {}, lambda m: M.forget_everything_preview_report(
            m, U, capability=None), "attempted_elevation"),
        ("forget_everything_preview", "erasure", {}, lambda m: M.forget_everything_preview_report(
            m, U, capability="direct", erasure="off"), "erasure_disabled"),
        ("forget_everything_confirm", "capability", {}, lambda m: M.forget_everything_confirm_report(
            m, U, s, capability=None), "attempted_elevation"),
        ("forget_everything_confirm", "erasure", {}, lambda m: M.forget_everything_confirm_report(
            m, U, s, capability="direct", erasure="off"), "erasure_disabled"),
        # find_facts_report: capability, scope configuration
        ("find_facts", "capability", {}, lambda m: M.find_facts_report(
            m, U, s, capability=None), "attempted_elevation"),
        ("find_facts", "scope-unconfigured", {}, lambda m: M.find_facts_report(
            m, U, s, capability="direct", principal=UNCONF), "scope_unconfigured"),
        ("find_facts", "scope-ungroupable", {"scope_groups": {}}, lambda m: M.find_facts_report(
            m, U, s, capability="direct", principal=UNGROUP), "principal_ungroupable"),
        # record_procedure_report: the capability floor and the closed-vocabulary check
        ("record_procedure", "capability", {}, lambda m: M.record_procedure_report(
            m, U, s, "stated", note=s, source_id=s, capability=None), "attempted_elevation"),
        ("record_procedure", "closed-vocabulary-author", {}, lambda m: M.record_procedure_report(
            m, U, s, "stated", author=s, note=s, source_id=s, capability="direct"), "not_accepted"),
        ("record_procedure", "closed-vocabulary-derived_from", {}, lambda m: M.record_procedure_report(
            m, U, s, "stated", derived_from=s, note=s, source_id=s, capability="direct"), "not_accepted"),
    ]


CASE_IDS = [f"{site}:{gate}" for site, gate, *_ in _cases("x" * 16)]


@pytest.mark.parametrize("shape", sorted(SHAPES))
@pytest.mark.parametrize("case", CASE_IDS)
def test_d1_a_served_pre_gate_refusal_echoes_no_value(tmp_path, case, shape):
    s = SHAPES[shape]
    site, gate, cfg, call, expected = next(c for c in _cases(s) if f"{c[0]}:{c[1]}" == case)
    m = _mem(tmp_path, **cfg)
    try:
        before = _digest(m)
        out = call(m)
        assert out.get("ok") is False and out.get("refusal") == expected, out
        assert _digest(m) == before
        text = json.dumps(out, ensure_ascii=False)
        assert not _echoes(text, s), (case, _echoes(text, s))
    finally:
        m.close()


def _transport(m, tool, args) -> str:
    """The text the MCP SDK hands the model: the tool result's content, or the error an escaping exception becomes."""
    server = M.build_server(m, default_user=U, capability="direct")
    try:
        res = asyncio.run(server.call_tool(tool, args))
    except Exception as exc:                     # noqa: BLE001 - the SDK's error is what the model would read
        return f"{type(exc).__name__}: {exc}"
    contents = res[0] if isinstance(res, tuple) else res
    return "\n".join(getattr(c, "text", repr(c)) for c in contents)


@pytest.mark.parametrize("shape", sorted(SHAPES))
@pytest.mark.parametrize("field", ["author", "derived_from"])
def test_d1_remember_closed_vocabulary_refusal_through_the_transport_echoes_no_value(tmp_path, field, shape):
    """remember's pre-gate is the closed-vocabulary check (its capability floor discards rather than refuses):
    `remember_report` raises ArgumentRefused, and the served tool hands the model `outward_text`, field and reason
    only. Driven through the SDK's own call path, with the shaped value in `text` as well."""
    pytest.importorskip("mcp")
    s = SHAPES[shape]
    m = _mem(tmp_path)
    try:
        before = _digest(m)
        text = _transport(m, "remember", {"text": s, field: s})
        assert field in text and "credential_refused" not in text, text
        assert _digest(m) == before
        assert not _echoes(text, s), _echoes(text, s)
    finally:
        m.close()


def test_d1_the_window_check_fires():
    """The negative control: the echo detector finds a value carried whole, and a part of one."""
    s = SHAPES["github"]
    assert _echoes(json.dumps({"detail": s}), s)
    assert _echoes(json.dumps({"detail": "x" + s[5:5 + WINDOW] + "y"}), s)
    assert not _echoes(json.dumps({"detail": "no such record in this scope"}), s)
