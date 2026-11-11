"""The two model-facing wordings for the held minor release (research's adoption probes 2 and 3, 2026-10-29).

Probe 3: under `none` every event is third-party, so the grounded part of a recall is empty while an UNVERIFIED section
follows. The block opened "(no memory yet for this user)" (the library) or, through the compiler, "No grounded facts …
Document is empty pending user information" (model prose over an input of `(none)` / `(none)`), and both drivers then
told the user their memory was empty. The header is now deterministic and true of the VIEW: no VERIFIED facts in
this view (SR1-03, shipped-changes round 1: "no verified facts yet" was false when a query's selection left a stored
assertable fact out).

Probe 2: nothing the model read said that the user's own words in the conversation outrank a stored memory; recall's
MCP description now says so.
"""

import json
import tempfile

import pytest

from veracium import EvidenceAuthor, Memory, MemoryConfig
from veracium import compile as _compile
from veracium.compile import compile_wiki
from veracium.schema import DEFAULT_RELATIONS


class Fake:
    def __init__(self):
        self.compile_calls = 0

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            return json.dumps({"triples": [{"subject": "user", "relation": "located_at", "object": "Denver"}],
                               "episode": "Someone said the user lives in Denver."})
        if role == "compile":
            self.compile_calls += 1
            return "No grounded facts are available. Document is empty pending user information."
        return ""


def _mem(d, llm, *, wiki=True):
    cfg = dict(require_source_id=False, db_path=f"{d}/t.db")
    if not wiki:
        cfg["wiki_recompile_after_writes"] = 0          # the wiki layer off: recall's own placeholder path
    return Memory(llm=llm, config=MemoryConfig(**cfg))


NO_VERIFIED = "(no verified facts in this view)"


def test_only_unverified_memory_is_not_headed_as_no_memory_on_either_path():
    """Both carriers of the header, wiki on (the compiler's body) and wiki off (recall's placeholder)."""
    for wiki in (True, False):
        with tempfile.TemporaryDirectory() as d:
            llm = Fake()
            m = _mem(d, llm, wiki=wiki)
            m.remember("u", "I live in Denver.", date="2026-10-01", author=EvidenceAuthor.THIRD_PARTY)
            ctx = m.recall("u", "where does the user live").context
            assert "no memory yet" not in ctx.lower() and "empty" not in ctx.lower(), (wiki, ctx)
            assert ctx.startswith(NO_VERIFIED), (wiki, ctx)
            assert "## UNVERIFIED THIRD-PARTY CLAIMS" in ctx and "Denver" in ctx
            assert llm.compile_calls == 0, (wiki, "the model was asked to compile an empty grounded input")


def test_a_user_with_nothing_stored():
    """Wiki off: nothing grounded and nothing unverified is still "(no memory yet for this user)", which is true.
    Wiki on: the fixed body, and the model is not called."""
    with tempfile.TemporaryDirectory() as d:
        assert _mem(d, Fake(), wiki=False).recall("u", "anything").context == "(no memory yet for this user)"
    with tempfile.TemporaryDirectory() as d:
        llm = Fake()
        ctx = _mem(d, llm).recall("u", "anything").context
        assert ctx.startswith(NO_VERIFIED) and "empty" not in ctx.lower(), ctx
        assert llm.compile_calls == 0


def test_the_compiler_is_not_asked_to_narrate_an_empty_grounded_input():
    """With no grounded edge and no grounded episode, the body is the fixed line, the model is not called, and the
    code-owned marker is still the final line (the +0/+0 case)."""
    with tempfile.TemporaryDirectory() as d:
        llm = Fake()
        m = _mem(d, llm)
        m.remember("u", "I live in Denver.", date="2026-10-01", author=EvidenceAuthor.THIRD_PARTY)
        before = llm.compile_calls
        wiki = compile_wiki(m.store, llm, "u", DEFAULT_RELATIONS)
        assert llm.compile_calls == before, "the model was asked to compile an empty grounded input"
        lines = wiki.splitlines()
        assert getattr(_compile, "EMPTY_GROUNDED_BODY", None) == NO_VERIFIED == lines[0], lines[0]
        assert lines[-1].startswith("[[veracium-wiki-compile:") and "+0 facts / +0 episodes" in lines[-1]
        assert "empty" not in wiki.lower()


def test_the_recall_tool_says_the_users_words_outrank_a_memory():
    pytest.importorskip("mcp")       # the built server needs the optional SDK (the pydantic-floor lane has none)
    from veracium.mcp_server import build_server
    with tempfile.TemporaryDirectory() as d:
        server = build_server(_mem(d, Fake()), default_user="u")
        tools = {t.name: t for t in server._tool_manager.list_tools()}
        desc = tools["recall"].description
        assert "own words" in desc and "outrank" in desc, desc


class _ReviewerScripted:
    def __init__(self, s):
        self.s = list(s)

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role != "distill":
            return ""
        ts, ep = self.s.pop(0)
        return json.dumps({"triples": [{"subject": s, "relation": r, "object": o, "volatility": "durable"}
                                       for s, r, o in ts], "episode": ep, "instructions": []})


def test_sr1_03_the_reviewers_regression(tmp_path):
    """SR1-03 (shipped-changes round 1), the reviewer's regression with its assertions verbatim: a stored assertable
    fact (Berlin) outside the query's lexical selection and outside a one-episode recent slice. The view holds no
    verified fact; the store does. The header says only what the view holds."""
    from veracium import EvidenceContext
    scripts = [([("person:alice", "located_at", "Berlin")], "Alice lives in Berlin."),
               ([("user", "works_on", "unicorn project")], "An external document describes the unicorn project.")]
    m = Memory(llm=_ReviewerScripted(scripts), config=MemoryConfig(db_path=str(tmp_path / "empty.db"),
               require_source_id=False, wiki_recompile_after_writes=0, max_recent_episodes=1))
    m.remember("u", "Alice lives in Berlin.", date="2026-10-01", context=EvidenceContext.direct())
    m.remember("u", "The user works on the unicorn project.", date="2026-10-02", author=EvidenceAuthor.THIRD_PARTY)
    assert any(e.assertable and e.object == "Berlin" for e in m.store.edges("u", include_quarantined=True))
    r = m.recall("u", "unicorn project", semantic=False)
    assert "Berlin" not in r.context and r.unverified
    assert "(no verified facts yet)" not in r.context, "a query-local empty view claimed that no verified facts exist yet"
    assert "in this view" in r.grounded
    m.close()


def _scoped_view(d, *, with_hidden_data):
    """A scope policy of one team (agent-1). With data, the store's only record is an assertable USER fact from
    agent-2, outside agent-1's scope; without, the store is empty. agent-1 is the principal."""
    from veracium.schema import Disclosure, Edge, Provenance
    from veracium.scope import Identity
    a1 = Identity(None, "agent-1")
    m = Memory(llm=lambda *a, **k: "", config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=0,
                                                           scope_groups={"team-a": [a1]}, require_source_id=False))
    if with_hidden_data:
        m.store.add_edge(Edge(id="e-other", user_id="u", subject="dentist appointment", relation="deadline",
                              object="2026-12-01", ungrounded=False, provenance=Provenance(
                                  author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-other",
                                  disclosure=Disclosure.MENTIONABLE, source_id="agent-2")))
        assert any(e.assertable for e in m.store.edges("u", active_only=False, include_quarantined=True))
    return m, a1


def test_sr1_03_a_principals_empty_view_never_says_no_memory_and_never_varies_with_the_store():
    """SR1-03's sibling (research's stage 1, marked A): "(no memory yet for this user)" is a claim about the STORE.
    Under a principal whose scope hides every record it was false, and it must not differ from what the same principal
    reads over an EMPTY store (0020: that difference is the cross-scope signal). Both view-worded lines, the pair
    byte-identical, wiki off and on."""
    for wiki in (0, 1):
        got = []
        for hidden in (True, False):
            with tempfile.TemporaryDirectory() as d:
                m, a1 = _scoped_view(d, with_hidden_data=hidden)
                if wiki:
                    m.config.wiki_recompile_after_writes = 1
                got.append(m.recall("u", "dentist appointment", principal=a1, semantic=False).context)
                m.close()
        assert got[0] == got[1] == "(no memory in this view)", (wiki, got)
        assert not any("no memory yet" in c or "no verified facts yet" in c for c in got), got


def test_an_unscoped_user_whose_only_record_is_redacted_reads_the_view_wording():
    """The condition's other half: without a principal, "(no memory yet for this user)" needs a user with NO record at
    all (test_a_user_with_nothing_stored holds that case). A user whose only episode was redacted at their request
    (0041) still holds a record, the redaction's tombstone, and their view is empty: the view wording, not "yet"."""
    from veracium import EvidenceContext

    class Hello:
        def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
            if role == "distill":
                return json.dumps({"triples": [], "episode": "The user said hello.", "instructions": []})
            return ""
    with tempfile.TemporaryDirectory() as d:
        m = Memory(llm=Hello(), config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db",
                                                    wiki_recompile_after_writes=0))
        m.remember("u", "Hello.", date="2026-10-01", context=EvidenceContext.direct())
        m.store.redact("u", episode_id=m.store.episodes("u")[0].id, reason="subject_request")
        assert m.store.episodes("u", limit=1) and not m.store.edges("u", active_only=False, include_quarantined=True)
        assert m.recall("u", "anything", semantic=False).context == "(no memory in this view)"
        m.close()


def _revoked_user(d, triples):
    """A user whose only event came from source "s1", then revoked (0022): its episode is retired (hidden from an
    ordinary read) and any edge it wrote stays stored, inactive. Research's stage 2 on 974a6122, P3 and P4."""
    from veracium import EvidenceContext

    class One:
        def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
            if role == "distill":
                return json.dumps({"triples": [{"subject": s, "relation": r, "object": o, "volatility": "durable"}
                                               for s, r, o in triples], "episode": "The user said something.",
                                   "instructions": []})
            return ""
    m = Memory(llm=One(), config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=0))
    m.remember("u", "USER: " + " ".join(f"I {r} {o}." for _s, r, o in triples) if triples else "USER: Hello.",
               date="2026-10-01", source_id="s1", context=EvidenceContext.direct())
    m.revoke_source("u", None, "s1", "erroneous_capture")
    return m


def test_r2s_1_a_revoked_user_whose_episode_held_no_fact_reads_the_view_wording():
    """R2S-1 (research's stage 2 on 974a6122, P4): the store holds one RETIRED episode and no edge. The emptiness check
    read episodes() with its default, which hides retired episodes, so this user read "(no memory yet for this user)"
    although un-revoking the source brings the episode back: the store held it throughout. A retired record counts."""
    with tempfile.TemporaryDirectory() as d:
        m = _revoked_user(d, [])
        assert not m.store.episodes("u") and m.store.episodes("u", include_retired=True)
        assert not m.store.edges("u", active_only=False, include_quarantined=True)
        assert m.recall("u", "anything", semantic=False).context == "(no memory in this view)"
        m.unrevoke_source("u", None, "s1", "revoked_in_error")
        assert m.store.episodes("u"), "the episode was in the store throughout"
        m.close()


def test_a_revoked_user_with_a_fact_reads_the_view_wording():
    """Research's P3: a revoked user whose event wrote a fact. The episode is retired and the edge stored INACTIVE; with
    R2S-1 the retired episode is already a record, so this cell holds the case end to end, and the edge half on its own
    is held by test_r2s_3_a_user_whose_only_record_is_an_inactive_edge_reads_the_view_wording."""
    with tempfile.TemporaryDirectory() as d:
        m = _revoked_user(d, [("user", "lives_in", "Lisbon")])
        edges = m.store.edges("u", active_only=False, include_quarantined=True)
        assert edges and not any(e.active for e in edges)
        assert m.recall("u", "anything", semantic=False).context == "(no memory in this view)"
        m.close()


def test_r2s_3_a_user_whose_only_record_is_an_inactive_edge_reads_the_view_wording():
    """R2S-3, the edge half on its own: after R2S-1 a retired episode already counts, so a revoked user's inactive edge
    is no longer what decides. Here the store holds ONE edge, inactive, and no episode at all (written at the store, as
    the scoped cell writes its hidden record): only an edge check over inactive edges sees a record."""
    from datetime import datetime, timezone

    from veracium.schema import Disclosure, Edge, Provenance
    with tempfile.TemporaryDirectory() as d:
        m = Memory(llm=lambda *a, **k: "", config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=0,
                                                               require_source_id=False))
        m.store.add_edge(Edge(id="e-old", user_id="u", subject="user", relation="lives_in", object="Lisbon",
                              ungrounded=False, invalidated_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
                              provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-old",
                                                    disclosure=Disclosure.MENTIONABLE)))
        assert not m.store.episodes("u", include_retired=True)
        assert [e.active for e in m.store.edges("u", active_only=False, include_quarantined=True)] == [False]
        assert m.recall("u", "anything", semantic=False).context == "(no memory in this view)"
        m.close()
