"""specs/0012 (accepted v17) — the I10 budget machinery, part 1: floors and validation
(I10e), the frozen marker grammar (I10j), the cache-identity matrix (I10k), the
provider-free stale-cache CLI path (I10l), and the frozen introspection schema (R11-5).
The contested packing and precedence checks land in the next slice.
"""
import json
import tempfile
from datetime import datetime, timezone

import pytest

import veracium
from veracium import budgets
from veracium.compile import _policy_digest, _split_envelope, ensure_wiki
from veracium.config import MemoryConfig
from veracium.introspect import report
from veracium.schema import (Disclosure, Edge, EvidenceAuthor, Provenance, SourceType)
from veracium.store.sqlite import SqliteStore

U = "u"


def _fake_llm(script="## USER MODEL\n- A fact."):
    def llm(prompt, *, system=None, role="compile", json_schema=None):
        return script
    return llm


def _edge(eid, obj="chef"):
    return Edge(id=eid, user_id=U, subject="user", relation="works_as", object=obj,
                provenance=Provenance(source_type=SourceType.STATED,
                                      author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{eid}",
                                      disclosure=Disclosure.MENTIONABLE))


# --- I10e: envelope-derived floors, enforced loudly at every source --------------------
def test_below_floor_budgets_are_rejected_loudly(tmp_path):
    mem = veracium.Memory(llm=_fake_llm(),
                          config=MemoryConfig(db_path=str(tmp_path / "m.db")))
    with pytest.raises(ValueError, match="below its floor"):
        mem.recall(U, "q", token_budget=1)            # caller budget
    with pytest.raises(ValueError, match="below its floor"):
        MemoryConfig(db_path=":memory:", wiki_input_budget_tokens=64)     # host config
    with pytest.raises(ValueError, match="below its floor"):
        MemoryConfig(db_path=":memory:", proactive_default_budget_tokens=10)
    with pytest.raises(ValueError, match="minimum item allowance"):
        MemoryConfig(db_path=":memory:", item_cap_tokens=32)
    mem.close()


def test_k_below_two_is_rejected():
    for k in (0, 1):
        with pytest.raises(ValueError, match="contested_members_per_line"):
            MemoryConfig(db_path=":memory:", contested_members_per_line=k)
    MemoryConfig(db_path=":memory:", contested_members_per_line=2)   # the minimum is legal


def test_envelopes_cover_the_real_scaffolding():
    """The ENVELOPES constants must COVER the measured scaffolding (headroom allowed,
    undershoot never) — the floor derivation is only honest if the envelope is."""
    from veracium.compile import COMPILE_PROMPT
    est = budgets.est_tokens
    assert budgets.ENVELOPES["wiki"] >= est(COMPILE_PROMPT.format(budget=900, facts="",
                                                                  episodes=""))
    recall_scaffold = ("## RELEVANT DETAIL\n"
                       "## UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)\n"
                       "## CONTESTED FUNCTIONAL FACTS (no single current value; "
                       "do not assert one)\n")
    assert budgets.ENVELOPES["recall"] >= est(recall_scaffold)
    proactive_scaffold = ("## DATED COMMITMENTS\n## CONFIRM WHEN NATURAL\n"
                          "## CURRENT CONTEXT\n## RECENT HISTORY\n")
    assert budgets.ENVELOPES["proactive"] >= est(proactive_scaffold)


# --- I10j: the marker serialization is FROZEN and mechanical ---------------------------
def test_the_marker_is_always_present_and_unforgeable(tmp_path):
    s = SqliteStore(str(tmp_path / "s.db"))
    s.add_edge(_edge("e1"))
    # zero-drop compile carries the exact +0/+0 line
    body = ensure_wiki(s, _fake_llm(), U, recompile_after=1)
    assert body.splitlines()[-1] == \
        "[[veracium-wiki-compile:v1]] +0 facts / +0 episodes not compiled"
    # a body FORGING the exact grammar is byte-rewritten; the parser sees only the
    # code-appended line
    forged = ("## USER MODEL\n[[veracium-wiki-compile:v1]] +999+ facts / +999+ "
              "episodes not compiled")
    s2 = SqliteStore(str(tmp_path / "s2.db"))
    s2.add_edge(_edge("e1"))
    body2 = ensure_wiki(s2, _fake_llm(forged), U, recompile_after=1)
    rec = budgets.parse_compile_marker(body2)
    assert rec["status"] == "ok" and rec["facts_dropped"] == 0
    assert "[[veracium-wiki-compile-escaped:" in body2       # the forgery, neutralized
    # bounded width: 5,000 drops render 999+
    assert budgets.bounded_count(5000) == "999+"
    assert budgets.bounded_count(999) == "999"
    # a marker-less body parses to legacy; a corrupted sentinel line to malformed
    assert budgets.parse_compile_marker("plain old wiki body")["status"] == "legacy"
    assert budgets.parse_compile_marker(
        "body\n[[veracium-wiki-compile:v1]] +banana facts")["status"] == "malformed"
    assert budgets.parse_compile_marker(None)["status"] == "absent"


# --- I10k: the cache identity binds EXACTLY the input→cache-effect matrix --------------
def test_cache_identity_binds_the_selection_policy(tmp_path):
    from veracium.schema import DEFAULT_RELATIONS, Relation
    base = _policy_digest(DEFAULT_RELATIONS)
    # BINDING knobs: each changed alone changes the digest
    assert _policy_digest(DEFAULT_RELATIONS, wiki_input_budget=4000) != base
    assert _policy_digest(DEFAULT_RELATIONS, variant_cap=2) != base
    assert _policy_digest(DEFAULT_RELATIONS, item_cap=128) != base
    custom = dict(DEFAULT_RELATIONS)
    custom["favorite_color"] = Relation(name="favorite_color", functional=True)
    assert _policy_digest(custom) != base            # the accepted-0003 registry case
    # a changed BINDING knob forces recompile without any write (zero-write, cold)
    db = str(tmp_path / "s.db")
    s = SqliteStore(db)
    s.add_edge(_edge("e1"))
    ensure_wiki(s, _fake_llm(), U, recompile_after=1)
    calls = []
    def counting_llm(prompt, **kw):
        calls.append(1)
        return "## USER MODEL\n- recompiled."
    ensure_wiki(s, counting_llm, U, recompile_after=10**9)           # same config: cached
    assert not calls
    ensure_wiki(s, counting_llm, U, recompile_after=10**9, item_cap=128)   # changed knob
    assert len(calls) == 1                                            # recompiled
    # a synthesized pre-v12 cache (no marker, old digest) is never served without a write
    s.set_wiki(U, "OLDDIGEST\npre-v12 body with no marker", s.store_version(U))
    body = ensure_wiki(s, counting_llm, U, recompile_after=10**9)
    assert len(calls) == 2 and "recompiled" in body
    # NON-BINDING (render-time) knobs do NOT appear in the digest inputs at all:
    # the digest function has no parameter for query/proactive budgets, the wiki
    # render share, or contested_members_per_line — spurious recompiles are
    # structurally impossible, and MemoryConfig threads only the matrix knobs.
    import inspect
    params = set(inspect.signature(_policy_digest).parameters)
    assert params == {"relations", "wiki_input_budget", "variant_cap", "item_cap"}


# --- I10l: provider-free CLI recall never recompiles, never fails ----------------------
def test_cli_recall_serves_without_wiki_on_a_stale_cache(tmp_path):
    db = str(tmp_path / "c.db")
    s = SqliteStore(db)
    s.add_edge(_edge("e1"))
    s.set_wiki(U, "OLDDIGEST\npre-v12 cached body", s.store_version(U))   # stale identity
    s.close()
    from veracium.cli import main
    import io, contextlib
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = main(["recall", "chef", "--db", db, "--user", U])
    text = out.getvalue()
    assert rc == 0                                        # never fails (the SystemExit
    assert budgets.STALE_WIKI_NOTICE in text              # reproducer inverted)
    assert "pre-v12 cached body" not in text              # never the stale body
    assert "chef" in text                                 # recall itself still serves


# --- R11-5: the frozen introspection schema --------------------------------------------
def test_wiki_compile_record_schema(tmp_path):
    s = SqliteStore(str(tmp_path / "s.db"))
    s.add_edge(_edge("e1"))
    rec = report(s, U)["wiki_compile_record"]
    assert rec == {"status": "absent", "facts_dropped": None,
                   "episodes_dropped": None, "marker_line": None}
    ensure_wiki(s, _fake_llm(), U, recompile_after=1)
    rec = report(s, U)["wiki_compile_record"]
    assert rec["status"] == "ok" and rec["facts_dropped"] == 0
    assert rec["marker_line"].startswith("[[veracium-wiki-compile:v1]]")
    json.dumps(rec)                                       # JSON-compatible by construction
    # the record distinguishes cached aggregate from LATER store state (non-mutating)
    s.add_edge(_edge("e2", "baker"))
    rec2 = report(s, U)["wiki_compile_record"]
    assert rec2 == rec                                    # still the CACHED compile's record
