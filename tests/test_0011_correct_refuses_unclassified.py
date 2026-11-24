"""specs/0011 §4e, amendment `0011/correct-refuses-unclassified` (invariant 0011-UNCL), with its 0031 §4c
cross-reference.

`correct()` refuses a prior whose relation is 0025's reserved `unclassified` with the closed reason
`correction_of_unclassified`, before any plan and inside the write transaction: the store's bytes are unchanged and
the prior is as it was. `correct_fact` returns `{"ok": false, "refusal": "correction_of_unclassified"}`, its detail
naming the remedy (remember the corrected statement). A prior under any other relation is corrected as before (the
permission half). Both ways a fact reaches `unclassified` are driven through the real ingest: 0025's re-disposition
of an incoherent `third_party_claim` about the user (USE_ONLY), and the vocabulary fallback of an off-vocabulary
relation (MENTIONABLE).

RED is tracked here, not in a scratch copy: `test_0011_uncl_red_without_the_check` removes the check (the site's
predicate patched to never match) and asserts that the library assertions below FAIL and that the defect the check
prevents appears: an active, user-authored, MENTIONABLE edge under `unclassified`.
"""
from __future__ import annotations

import hashlib
import json

import pytest

import veracium
from veracium import Memory, MemoryConfig
from veracium import graph
from veracium import mcp_server as M
from veracium.schema import (Disclosure, EvidenceAuthor, EvidenceContext, QUARANTINE_RELATION,
                             UNCLASSIFIED_RELATION)

U = "u-uncl"


class _Stub:
    """The main extraction returns `triples`; a retry returns nothing, so an off-vocabulary relation falls back."""

    def __init__(self, triples):
        self.triples = triples

    def __call__(self, prompt, **kw):
        if kw.get("role") == "distill-retry":
            return json.dumps({"triples": []})
        return json.dumps({"triples": self.triples, "episode": "the day's summary"})


def _mem(tmp_path, triples):
    tmp_path.mkdir(parents=True, exist_ok=True)
    return Memory(llm=_Stub(triples),
                  config=MemoryConfig(db_path=str(tmp_path / "v.db"), require_source_id=False,
                                      wiki_recompile_after_writes=0))


#: the two ways a fact reaches `unclassified`, each with the disclosure 0024/0025 give it
PATHS = {
    # 0025 §4b-iii / 0024 A1: an incoherent third_party_claim about the user is re-dispositioned, USE_ONLY
    "redisposition": ({"subject": "user", "relation": QUARANTINE_RELATION, "object": "carpenter"},
                      Disclosure.USE_ONLY),
    # 0025 §4b: an off-vocabulary relation that the (empty) retry does not repair falls back, MENTIONABLE
    "vocabulary-fallback": ({"subject": "user", "relation": "ThirdPartyClaim", "object": "carpenter"},
                            Disclosure.MENTIONABLE),
}
COHERENT = {"subject": "user", "relation": "works_as", "object": "baker"}


def _ingest(tmp_path, triple):
    m = _mem(tmp_path, [triple, COHERENT])
    m.remember(U, "event text", author=EvidenceAuthor.USER, context=EvidenceContext.direct())
    by_obj = {e.object: e for e in m.store.edges(U, active_only=False, include_quarantined=True)}
    return m, by_obj["carpenter"], by_obj["baker"]


def _digest(m) -> str:
    return hashlib.sha256("\n".join(m.store._conn.iterdump()).encode()).hexdigest()


def _assert_library_refuses(m, uncl):
    """0011-UNCL's library half: the closed refusal, nothing written, the prior as it was."""
    before, prior = _digest(m), uncl.model_dump()
    with pytest.raises(graph.CorrectionOfUnclassified) as ei:
        m.correct(U, uncl.id, "joiner")
    assert ei.value.reason == "correction_of_unclassified"
    assert isinstance(ei.value, ValueError) and not isinstance(ei.value, graph.CorrectionRefused)
    assert "remember the corrected statement" in str(ei.value)
    assert _digest(m) == before
    after = next(e for e in m.store.edges(U, active_only=False, include_quarantined=True) if e.id == uncl.id)
    assert after.model_dump() == prior
    assert not [e for e in m.store.edges(U, active_only=False, include_quarantined=True)
                if e.relation == UNCLASSIFIED_RELATION and e.object == "joiner"]


@pytest.mark.parametrize("path", sorted(PATHS))
def test_0011_uncl_correct_refuses_an_unclassified_prior(tmp_path, path):
    triple, disc = PATHS[path]
    m, uncl, _ = _ingest(tmp_path, triple)
    try:
        assert uncl.relation == UNCLASSIFIED_RELATION and uncl.active
        assert uncl.provenance.disclosure is disc          # the fixture is the path it names
        _assert_library_refuses(m, uncl)
    finally:
        m.close()


@pytest.mark.parametrize("path", sorted(PATHS))
def test_0011_uncl_the_permission_half_a_coherent_fact_is_corrected_as_before(tmp_path, path):
    """A prior under any other relation is corrected as before, in the same store as the refused one."""
    m, uncl, coherent = _ingest(tmp_path, PATHS[path][0])
    try:
        out = m.correct(U, coherent.id, "pastry chef")
        assert out["corrected"] == coherent.id
        edges = {e.id: e for e in m.store.edges(U, active_only=False, include_quarantined=True)}
        assert not edges[coherent.id].active and edges[coherent.id].invalidation_reason == "corrected"
        new = edges[out["replacement"]]
        assert (new.relation, new.object, new.active) == ("works_as", "pastry chef", True)
        assert edges[uncl.id].active                       # the fenced claim is untouched
    finally:
        m.close()


@pytest.mark.parametrize("path", sorted(PATHS))
def test_0011_uncl_correct_fact_returns_the_named_refusal(tmp_path, path):
    """0031 §4c: `correct_fact` surfaces the library's refusal under its own reason, never `refused` (which hides
    the remedy) and never `correction_refused` (the COMMITTED refusal); the store is unchanged."""
    m, uncl, _ = _ingest(tmp_path, PATHS[path][0])
    try:
        before = _digest(m)
        out = M.correct_fact_report(m, U, uncl.id, "joiner", capability="direct")
        assert out["ok"] is False and out["refusal"] == "correction_of_unclassified", out
        assert "remember the corrected statement" in out["detail"] and len(out["detail"]) <= 200
        assert _digest(m) == before
        impl = M.correct_fact_impl(m, U, uncl.id, "joiner", capability="direct")
        assert impl["ok"] is False and impl["refusal"] == "correction_of_unclassified", impl
        assert _digest(m) == before
    finally:
        m.close()


def test_0011_uncl_the_reason_is_in_the_closed_vocabulary():
    from veracium.trust_tools import REFUSALS
    assert "correction_of_unclassified" in REFUSALS
    assert graph.CorrectionOfUnclassified.reason in REFUSALS


def test_0011_uncl_red_without_the_check(tmp_path, monkeypatch):
    """RED: with the check removed (the relation test never matches), the library assertions above fail, and the
    defect the check exists for appears: an active, user-authored, MENTIONABLE fact under `unclassified`."""
    m, uncl, _ = _ingest(tmp_path, PATHS["redisposition"][0])
    try:
        monkeypatch.setattr(veracium.schema, "UNCLASSIFIED_RELATION", "\x00never-a-relation")
        with pytest.raises(pytest.fail.Exception):
            _assert_library_refuses(m, uncl)
        minted = [e for e in m.store.edges(U) if e.relation == UNCLASSIFIED_RELATION and e.object == "joiner"]
        assert len(minted) == 1
        assert minted[0].provenance.author_of_evidence is EvidenceAuthor.USER
        assert minted[0].provenance.disclosure is Disclosure.MENTIONABLE
    finally:
        m.close()


def test_0011_uncl_through_the_mcp_transport(tmp_path):
    """The served tool over the MCP SDK's own call path returns the refusal as data, never raised to the transport."""
    pytest.importorskip("mcp")
    import asyncio
    m, uncl, _ = _ingest(tmp_path, PATHS["redisposition"][0])
    try:
        before = _digest(m)
        server = M.build_server(m, default_user=U, capability="direct")
        res = asyncio.run(server.call_tool("correct_fact", {"edge_id": uncl.id, "corrected_value": "joiner"}))
        out = json.loads(res[0].text)
        assert out.get("ok") is False and out.get("refusal") == "correction_of_unclassified", out
        assert _digest(m) == before
    finally:
        m.close()
