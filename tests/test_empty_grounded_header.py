"""The two model-facing wordings for the held minor release (research's adoption probes 2 and 3, 2026-10-29).

Probe 3: under `none` every event is third-party, so the grounded part of a recall is empty while an UNVERIFIED section
follows. The block opened "(no memory yet for this user)" (the library) or, through the compiler, "No grounded facts …
Document is empty pending user information" (model prose over an input of `(none)` / `(none)`), and both drivers then
told the user their memory was empty. The header is now deterministic and true: no VERIFIED facts yet.

Probe 2: nothing the model read said that the user's own words in the conversation outrank a stored memory; recall's
MCP description now says so.
"""

import json
import tempfile

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


NO_VERIFIED = "(no verified facts yet)"


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
    from veracium.mcp_server import build_server
    with tempfile.TemporaryDirectory() as d:
        server = build_server(_mem(d, Fake()), default_user="u")
        tools = {t.name: t for t in server._tool_manager.list_tools()}
        desc = tools["recall"].description
        assert "own words" in desc and "outrank" in desc, desc
