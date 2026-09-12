"""specs/0037 v16 — CAPTURE reopened, RENDER still closed (the owner's word,
dev session 2026-09-12: "0037 procedural capture reopening", on research's
proposal `procedural-capture-reopening.md` in its repaired §2a form).

The extractor may RECORD a routine the user EXPRESSED; it may not CONCLUDE
one. The line is mechanical, never a field the model fills: a procedural
triple must carry a `quote` — the verbatim span of the event text in which
the user states the routine — and ingest verifies the quote against the
event text it already holds. A verified quote DERIVES basis `stated`; a
missing, empty or unverifiable quote is REFUSED and counted, never filed as
`unclassified`, never stamped. `observed` stays host-only; `inferred` does
not exist. The record is stamped and excluded from model context exactly as
a host-declared procedure is (the render exclusion is untouched).

Written BEFORE the spec amendment and the code, as the failing controls
(research's order, the policy-lane precedent): every test here is red at
0037 v15, where the procedural relation is not in the vocabulary and an
emitted procedural name takes 0025's residual path."""

import json
import pathlib

import pytest

from veracium import Memory, MemoryConfig, gate
from veracium.registry import effective_registry, render_prompt_relations
from veracium.schema import (DEFAULT_RELATIONS, EvidenceAuthor, EvidenceContext, Relation,
                             is_procedural)

U = "u"
PROC = "follows_procedure"
TEXT = ("I run the formatter before committing, every time. "
        "Unrelated: I like tea.")
QUOTE = "I run the formatter before committing, every time"
ROOT = pathlib.Path(__file__).resolve().parent.parent


def _cfg(tmp_path, name="m.db", relations=None):
    kw = {} if relations is None else {"relations": relations}
    return MemoryConfig(db_path=str(tmp_path / name), wiki_recompile_after_writes=0,
                        scope_groups={}, **kw)


def _llm_emitting(triples, instructions=None):
    def llm(prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            return json.dumps({"triples": triples, "episode": "The user described a routine.",
                               "instructions": instructions if instructions is not None else []})
        if role == "distill-retry":
            return json.dumps({"triples": []})
        return "## USER MODEL\n- test wiki"
    return llm


def _proc_triple(quote=QUOTE, **over):
    t = {"subject": "user", "relation": PROC,
         "object": "Runs the formatter before committing", "quote": quote}
    t.update(over)
    return t


# ---------------------------------------------------------------- V-QUOTE-GATED (positive)
def test_a_quoted_user_routine_is_recorded_as_a_procedure_and_never_rendered(tmp_path):
    """The user states a routine; the extractor emits the procedural triple
    WITH the verbatim span; the quote verifies against the event text; one
    procedural record is written with basis DERIVED `stated`, the quote kept
    in `note` (the field 0037 never renders), the event's own provenance;
    the episode is written as on every ordinary ingest; and the record is
    excluded from model context at the choke point, as any procedure is."""
    # 0038 files the same practice under `instructions` — the drop rule must
    # exempt the procedural carrier (the quote IS the declared instruction)
    mem = Memory(llm=_llm_emitting([_proc_triple()], instructions=[QUOTE]),
                 config=_cfg(tmp_path))
    r = mem.remember(U, TEXT, author=EvidenceAuthor.USER, context=EvidenceContext.direct())
    assert r["procedures"] == 1 and r["procedural_refused"] == 0
    assert r["instructions_dropped"] == 0 and r["invalid"] == 0 and r["facts"] == 0
    edges = mem.store.edges(U, active_only=False)
    assert len(edges) == 1
    e = edges[0]
    assert e.relation == PROC and is_procedural(e)
    assert e.provenance.record_kind == "procedural" and e.provenance.basis == "stated"
    assert e.note == QUOTE
    assert e.provenance.author_of_evidence is EvidenceAuthor.USER
    assert len(mem.store.episodes(U)) == 1
    # RENDER STAYS CLOSED: the choke point excludes it in both blocks; recall
    # never carries it; describe sees exactly one describable record
    g, u = gate.partition([e], [])
    assert g == "" and u == ""
    rc = mem.recall(U, "formatter")
    assert rc.edges == [] and "formatter" not in rc.context.lower()
    assert mem.describe_procedures(U).total_describable == 1
    mem.close()


# ---------------------------------------------------------------- V-QUOTE-GATED (refusals)
@pytest.mark.parametrize("case, triple, author", [
    ("no quote", {k: v for k, v in _proc_triple().items() if k != "quote"}, EvidenceAuthor.USER),
    ("empty quote", _proc_triple(quote=""), EvidenceAuthor.USER),
    ("quote not in the text", _proc_triple(quote="I always deploy on Fridays"), EvidenceAuthor.USER),
    ("quote is a paraphrase", _proc_triple(quote="I run the formatter before every commit"), EvidenceAuthor.USER),
    ("not the user's own words", _proc_triple(), EvidenceAuthor.THIRD_PARTY),
])
def test_a_procedural_emission_without_a_verifying_user_quote_is_refused_and_counted(tmp_path, case, triple, author):
    """No quote, an empty one, one not in the source, a paraphrase, or a quote
    from an event the user did not author: REFUSED, COUNTED, nothing
    procedural written — and NOT filed as `unclassified` either (the name is
    in the vocabulary now; the residual path is for names that are not)."""
    mem = Memory(llm=_llm_emitting([triple]), config=_cfg(tmp_path))
    kw = {"author": author}
    if author is EvidenceAuthor.USER:
        kw["context"] = EvidenceContext.direct()
    else:
        kw["source_id"] = "mail-1"       # 0006 v8: third-party content needs a source id
    r = mem.remember(U, TEXT, **kw)
    assert r["procedural_refused"] == 1 and r["procedures"] == 0, case
    assert r["invalid"] == 0 and r["residual"] == 0, case
    edges = mem.store.edges(U, active_only=False, include_quarantined=True)
    assert all(e.relation != PROC and not is_procedural(e) for e in edges), case
    assert all(e.original_relation != PROC for e in edges), case
    assert mem.describe_procedures(U).total_describable == 0, case
    mem.close()


# ------------------------------------------------ the converse of the byte-identity property
def test_the_prompt_vocabulary_carries_the_procedural_relation(tmp_path):
    """v15 guaranteed the prompt bytes equal with and without a procedural
    relation registered; v16 replaces that property with its CONVERSE: a
    registered procedural relation is rendered into the vocabulary, for the
    default registry and for a host registry, so the model can emit it."""
    reg = effective_registry(DEFAULT_RELATIONS)
    assert f"- {PROC}" in render_prompt_relations(reg)
    without = {n: r for n, r in DEFAULT_RELATIONS.items() if r.relation_kind != "procedural"}
    assert render_prompt_relations(effective_registry(without)) != render_prompt_relations(reg)
    host = dict(DEFAULT_RELATIONS)
    host["runs_playbook"] = Relation(name="runs_playbook", relation_kind="procedural", desc="p")
    assert "- runs_playbook" in render_prompt_relations(effective_registry(host))


# ---------------------------------------------------------------- the retry cannot mint one
def test_the_retry_cannot_mint_a_procedure(tmp_path):
    """A repair landing on the procedural relation is not a recovery: the
    retry carries no quote and can verify nothing, so the failing triple
    stays residual and no procedural record appears (unchanged from v15)."""
    def llm(prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            return json.dumps({"triples": [{"subject": "user", "relation": "does_a_thing",
                                            "object": "Runs the formatter before committing"}],
                               "episode": "x", "instructions": []})
        if role == "distill-retry":
            return json.dumps({"triples": [{"subject": "user", "relation": PROC,
                                            "object": "Runs the formatter before committing"}]})
        return "## USER MODEL\n- test wiki"
    mem = Memory(llm=llm, config=_cfg(tmp_path))
    r = mem.remember(U, TEXT, author=EvidenceAuthor.USER, context=EvidenceContext.direct())
    assert r["invalid"] == 1 and r["retried"] == 1 and r["recovered"] == 0 and r["residual"] == 1
    assert r["procedures"] == 0
    edges = mem.store.edges(U, active_only=False)
    assert all(e.relation != PROC and not is_procedural(e) for e in edges)
    mem.close()
