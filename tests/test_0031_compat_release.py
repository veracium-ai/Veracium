"""0.18.1 — the designated COMPAT release for specs/0031 Phase A rollback
(punch-list I4; Quentin's ruling 2026-09-04).

Two properties, each the negation of a behaviour the Phase A before-receipts
record (research's harness, `cases/tier8_before_receipts.json`, digest
`ebfabbfd2300679c…`, a frozen historical capture at commit 91cbdcd7): a
rollback to this release must NOT bring back (G2) `stored_author="user"` on an
authorless MCP write, nor (P3-3) `derived_from="user"` reaching `mentionable`.
Plus the recognition rule: `direct` refuses to start, so a deployment that
attested under 0.19 cannot run un-attested here while believing it attests.
"""
from __future__ import annotations

import asyncio
import json

import pytest

from veracium import Memory, MemoryConfig
from veracium.mcp_server import (_refuse_attestation, build_server,
                                 remember_impl)
from veracium.schema import Disclosure, EvidenceAuthor

U = "u"
TRIPLE = {"subject": "user", "relation": "has_diet", "object": "avoids dairy",
          "volatility": "durable"}


class Fake:
    def __init__(self, scripts):
        self._s = list(scripts); self.i = 0
    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        out = self._s[self.i % len(self._s)]; self.i += 1
        return out if isinstance(out, str) else json.dumps(out)


def _mem(tmp_path, name):
    return Memory(llm=Fake([{"triples": [TRIPLE], "episode": "diet noted"}]),
                  config=MemoryConfig(db_path=f"{tmp_path}/{name}.db",
                                      wiki_recompile_after_writes=0))


def _edge(mem):
    edges = mem.store.edges(U, active_only=False, include_quarantined=True)
    assert len(edges) == 1
    return edges[0]


def test_direct_refuses_to_start_here():
    """Recognised, not implemented: unset and "none" run; direct, the empty
    string and any other value raise naming the variable and the release
    that implements attestation."""
    _refuse_attestation(None)
    _refuse_attestation("none")
    for bad in ("direct", "", "bogus", "DIRECT", 123):
        with pytest.raises(ValueError, match="does not implement host attestation"):
            _refuse_attestation(bad)


def test_build_server_and_main_refuse_direct(tmp_path, monkeypatch):
    pytest.importorskip("mcp")
    from veracium import mcp_server as M
    mem = _mem(tmp_path, "srv")
    try:
        build_server(mem, default_user=U)
        build_server(mem, default_user=U, capability="none")
        with pytest.raises(ValueError):
            build_server(mem, default_user=U, capability="direct")
    finally:
        mem.close()
    seen = {}

    class _Srv:
        def run(self):
            seen["ran"] = True

    def fake_build_server(mem, *, default_user, capability=None):
        _refuse_attestation(capability)
        seen["capability"] = capability
        return _Srv()

    monkeypatch.setattr(M, "build_memory", lambda: object())
    monkeypatch.setattr(M, "build_server", fake_build_server)
    monkeypatch.delenv("VERACIUM_MCP_CAPABILITY", raising=False)
    M.main([])
    assert seen == {"capability": None, "ran": True}
    monkeypatch.setenv("VERACIUM_MCP_CAPABILITY", "direct")
    with pytest.raises(SystemExit, match="refusing to start"):
        M.main([])


def test_g2_is_not_restored_an_authorless_write_stores_third_party(tmp_path):
    """Before-receipt G2 (0.18.0): stored_author="user" on an authorless
    write. Here: third_party, the conservative baseline."""
    mem = _mem(tmp_path, "g2")
    try:
        remember_impl(mem, U, "(scripted)")
        e = _edge(mem)
        assert e.provenance.author_of_evidence is EvidenceAuthor.THIRD_PARTY
        assert e.provenance.disclosure is Disclosure.USE_ONLY and not e.assertable
    finally:
        mem.close()


def test_p3_3_is_not_restored_derived_from_user_does_not_elevate(tmp_path):
    """Before-receipt P3-3 (0.18.0): derived_from="user" → mentionable /
    assertable. Here: the derived leg takes the ingest floor; use_only."""
    mem = _mem(tmp_path, "p33")
    try:
        remember_impl(mem, U, "(scripted)", derived_from="user")
        e = _edge(mem)
        assert e.provenance.derived_from is EvidenceAuthor.THIRD_PARTY
        assert e.provenance.disclosure is Disclosure.USE_ONLY and not e.assertable
    finally:
        mem.close()


@pytest.mark.parametrize("author", ["user", "assistant", "third_party"])
@pytest.mark.parametrize("derived", [None, "user", "third_party"])
def test_supplied_values_are_validated_then_inert(tmp_path, author, derived):
    mem = _mem(tmp_path, f"inert-{author}-{derived}")
    try:
        kw = {"author": author}
        if derived is not None:
            kw["derived_from"] = derived
        remember_impl(mem, U, "(scripted)", **kw)
        e = _edge(mem)
        assert e.provenance.author_of_evidence is EvidenceAuthor.THIRD_PARTY
        assert e.provenance.derived_from is EvidenceAuthor.THIRD_PARTY
    finally:
        mem.close()
    mem = _mem(tmp_path, f"bad-{author}-{derived}")
    try:
        for bad in ("system", "", "bogus", 123):
            with pytest.raises(ValueError):
                remember_impl(mem, U, "x", author=bad)
            with pytest.raises(ValueError):
                remember_impl(mem, U, "x", derived_from=bad)
        assert mem.store.edges(U, active_only=False, include_quarantined=True) == []
    finally:
        mem.close()


def test_the_tool_surface_is_the_0_18_0_one(tmp_path):
    """The compat release keeps the OLD tool schemas (user_id on the tools)
    so clients configured for 0.18 keep working; only `author` loses its
    default. The Phase A schema (no user_id) is 0.19's."""
    pytest.importorskip("mcp")
    mem = _mem(tmp_path, "surface")
    try:
        server = build_server(mem, default_user=U)
        tools = {t.name: t.model_dump() for t in asyncio.run(server.list_tools())}
        assert sorted(tools) == ["answer", "maintain", "recall", "remember"]
        schema = tools["remember"].get("inputSchema") or tools["remember"].get("input_schema")
        assert schema is not None
        assert set(schema["properties"]) == {"text", "user_id", "author", "event_type",
                                             "date", "derived_from"}
        assert schema["properties"]["author"].get("default") is None
        flat = json.dumps(tools)
        assert "capability" not in flat
    finally:
        mem.close()


def test_historical_records_keep_their_meaning_after_rollback(tmp_path):
    """I4's second rollback invariant: a record written under 0.19's
    `direct` semantics keeps its stored provenance and its derived
    disclosure when the store is opened by this line. 0.19's
    `remember_impl(capability=direct)` resolves to the LIBRARY write
    `Memory.remember(..., context=EvidenceContext.direct())`, which this line
    ships unchanged — so the same write is made here through that path, the
    store closed, and re-opened by a fresh 0.18.1 `Memory`: author USER,
    derivation None, MENTIONABLE, assertable, byte-for-byte what was written.
    Provenance is a fact about its write, not a view over configuration."""
    from veracium.schema import EvidenceContext
    db = f"{tmp_path}/rollback.db"
    mem = Memory(llm=Fake([{"triples": [TRIPLE], "episode": "diet noted"}]),
                 config=MemoryConfig(db_path=db, wiki_recompile_after_writes=0))
    try:
        mem.remember(U, "(scripted)", author=EvidenceAuthor.USER,
                     context=EvidenceContext.direct())        # a 0.19 `direct` write
        before = _edge(mem)
        written = (before.provenance.author_of_evidence, before.provenance.derived_from,
                   before.provenance.disclosure, bool(before.assertable))
        assert written == (EvidenceAuthor.USER, None, Disclosure.MENTIONABLE, True)
    finally:
        mem.close()
    # the reopened memory's extractor yields a DIFFERENT relation, so the new
    # write coexists with the old record instead of contending for it
    other = {"subject": "user", "relation": "has_pet", "object": "a cat",
             "volatility": "durable"}
    reopened = Memory(llm=Fake([{"triples": [other], "episode": "pet noted"}]),
                      config=MemoryConfig(db_path=db, wiki_recompile_after_writes=0))
    try:
        after = _edge(reopened)
        assert (after.provenance.author_of_evidence, after.provenance.derived_from,
                after.provenance.disclosure, bool(after.assertable)) == written
        assert after.id == before.id and after.provenance == before.provenance
        # ...and a NEW write on this line takes the conservative baseline
        # beside it — the old record is not dragged down, the new one is not
        # lifted up
        remember_impl(reopened, U, "(scripted)", author="user")
        authors = sorted(e.provenance.author_of_evidence.value
                         for e in reopened.store.edges(U, active_only=False,
                                                       include_quarantined=True))
        assert authors == ["third_party", "user"]
    finally:
        reopened.close()
