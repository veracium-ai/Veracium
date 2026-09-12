"""specs/0006 §4 rule 9 / I15 (v7) — `require_source_id`, the owner's staged ruling
(option C, stage 2, 2026-09-12). Default OFF: every existing 0006 test is the
guard that nothing moved. ON: third-party-AUTHORED evidence and DECLARED
third-party-derived content without a `source_id` are refused BEFORE ANY WRITE;
the 0011 §4d floor is spared; a sourced ingest is accepted. The MCP deployment's
binding is host-set and never a tool argument; the refusal carries its name."""

import json
import sqlite3
import tempfile

import pytest

from veracium import Memory, MemoryConfig, EvidenceAuthor
from veracium.cli import main as cli_main
from veracium.ingest import SourceIdRequired
from veracium.schema import EvidenceContext


class Fake:
    def __init__(self, answer):
        self.answer = answer
        self.calls = 0

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            self.calls += 1
            return json.dumps(self.answer)
        return "## USER MODEL\n- test wiki"


U = "ida"
CLAIM = {"triples": [{"subject": "org:acme", "relation": "third_party_claim", "object": "user owes $10"}],
         "episode": "A collection email."}
FACT = {"triples": [{"subject": "user", "relation": "likes", "object": "tea"}], "episode": "A chat."}


def _counts(db):
    c = sqlite3.connect(db)
    out = tuple(c.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("edges", "episodes", "edge_event"))
    c.close()
    return out


def _mem(db, answer, *, require=True):
    return Memory(llm=Fake(answer), config=MemoryConfig(db_path=db, wiki_recompile_after_writes=0,
                                                       require_source_id=require))


def test_require_source_id_refuses_unsourced_third_party_before_any_write():
    with tempfile.TemporaryDirectory() as d:
        db = f"{d}/t.db"
        mem = _mem(db, CLAIM)
        before = _counts(db)
        # third-party AUTHORED, no source id: refused, named, nothing written, the LLM not called
        with pytest.raises(SourceIdRequired, match="source_id is required"):
            mem.remember(U, "mail", author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        assert mem.llm.calls == 0 and _counts(db) == before
        # DECLARED third-party-derived, no source id: refused the same way, both declaration forms
        with pytest.raises(SourceIdRequired):
            mem.remember(U, "a summary quoting the mail", context=EvidenceContext.derived(EvidenceAuthor.THIRD_PARTY))
        with pytest.raises(SourceIdRequired):
            mem.remember(U, "a summary quoting the mail", derived_from=EvidenceAuthor.THIRD_PARTY)
        assert mem.llm.calls == 0 and _counts(db) == before
        # the same ingests WITH a source id are accepted and stored with it
        r = mem.remember(U, "mail", author=EvidenceAuthor.THIRD_PARTY, event_type="email", source_id="acme-inbox")
        assert r["quarantined"] == 1
        e = next(e for e in mem.store.edges(U, include_quarantined=True) if e.relation == "third_party_claim")
        assert e.provenance.source_id == "acme-inbox"
        assert SourceIdRequired.reason == "source_id_required"
        mem.close()


def test_require_source_id_spares_the_floor_and_the_default_off_store():
    with tempfile.TemporaryDirectory() as d:
        # ON: an ingest with NO declared context takes the 0011 §4d floor
        # (derived_from=third_party by absence) and is NOT refused — absence of a
        # declaration is not a claim about the source
        db = f"{d}/on.db"
        mem = _mem(db, FACT)
        r = mem.remember(U, "I like tea")
        assert r["facts"] == 1
        e = mem.store.edges(U)[0]
        assert e.provenance.derived_from == EvidenceAuthor.THIRD_PARTY and e.provenance.source_id is None
        # and a declared-direct user ingest needs no source id either
        assert mem.remember(U, "I like tea too", context=EvidenceContext.direct())["facts"] >= 0
        mem.close()
        # OFF (the default): third-party without a source id is accepted exactly as before v7
        db2 = f"{d}/off.db"
        mem2 = _mem(db2, CLAIM, require=False)
        assert MemoryConfig().require_source_id is False
        r2 = mem2.remember(U, "mail", author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        assert r2["quarantined"] == 1
        mem2.close()


def test_the_mcp_source_binding_is_host_set_and_the_refusal_is_named():
    from veracium import mcp_server as m
    with tempfile.TemporaryDirectory() as d:
        # the served `remember` tool exposes no source_id argument (0006 I1)
        import inspect
        mem = _mem(f"{d}/a.db", CLAIM, require=False)
        server = m.build_server(mem, default_user=U, capability="direct", source_id="mailbox-7")
        tools = {t.name: t for t in server._tool_manager.list_tools()} if hasattr(server, "_tool_manager") else None
        if tools is not None:
            params = tools["remember"].parameters.get("properties", {})
            assert "source_id" not in params, "the model must never supply a source id"
        # the binding threads through the adapter to the stored provenance
        out = m.remember_impl(mem, U, "mail", author="third_party", event_type="email", date=None,
                              derived_from=None, source_id="mailbox-7", capability="direct")
        assert out.get("ok", True) is not False
        e = next(e for e in mem.store.edges(U, include_quarantined=True) if e.relation == "third_party_claim")
        assert e.provenance.source_id == "mailbox-7"
        mem.close()
        # with the flag ON and no binding, the adapter returns the NAMED refusal (the 0037 shape)
        mem2 = _mem(f"{d}/b.db", CLAIM, require=True)
        out2 = m.remember_impl(mem2, U, "mail", author="third_party", event_type="email", date=None,
                               derived_from=None, source_id=None, capability="direct")
        assert out2["ok"] is False and out2["refusal"] == "source_id_required"
        assert _counts(f"{d}/b.db") == (0, 0, 0)
        mem2.close()


def test_the_cli_source_id_flag_threads_through(monkeypatch, capsys):
    import veracium.cli as cli
    with tempfile.TemporaryDirectory() as d:
        db = f"{d}/t.db"
        monkeypatch.setattr(cli, "_build_llm", lambda *a, **k: Fake(CLAIM))
        assert cli_main(["remember", "--user", U, "mail", "--author", "third_party", "--event-type", "email",
                         "--source-id", "acme-inbox", "--db", db]) == 0
        capsys.readouterr()
        mem = Memory(llm=Fake(CLAIM), config=MemoryConfig(db_path=db))
        e = next(e for e in mem.store.edges(U, include_quarantined=True) if e.relation == "third_party_claim")
        assert e.provenance.source_id == "acme-inbox"
        mem.close()
