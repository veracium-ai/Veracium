"""specs/0025 as amended 2026-09-08 — the SUBJECT GRAMMAR is enforced at
ingest, not only stated in the prompt.

The finding (research, the 0.20.0 release's provider-backed selfcheck under
an OpenAI-compatible provider): the prompt's placeholder
`user|person:<name>|org:<name>` was read as a LITERAL separator by
gpt-4o-mini, which stored `user|person:<name>|org:Acme Corp` as the subject;
"I work at Acme" and "now Globex" then landed under two different subjects,
supersession was never invoked, and the selfcheck scored 12/13 — PASS. No
test asserted the shape of a returned subject, so 325 clean subjects in the
suite proved nothing about a provider we ship an example for.
"""
from __future__ import annotations

import json

import pytest

from veracium import Memory, MemoryConfig, prompts, selfcheck
from veracium.ingest import subject_off_grammar
from veracium.schema import EvidenceContext

U = "u"


def _mem(tmp_path, llm):
    return Memory(llm=llm, config=MemoryConfig(require_source_id=False, db_path=str(tmp_path / "m.db"),  # 0006 v8: opted out — measures records that exist (rule 8 / I3 / I13), not the ingest requirement
                                              wiki_recompile_after_writes=0))


def _scripted(triples):
    def llm(prompt, **k):
        if k.get("role") == "distill-retry":
            return json.dumps({"triples": []})
        return json.dumps({"triples": triples, "episode": "x", "instructions": []})
    return llm


def test_the_prompts_subject_placeholder_carries_no_pipe():
    """The byte check, on the PLACEHOLDER VALUE (not the whole template, so
    an unrelated pipe elsewhere cannot fail it): the alternation is spelled
    out, never a `|`-joined placeholder a provider can concatenate."""
    import re
    m = re.search(r'"triples": \[\{\{"subject": "([^"]*)"', prompts.EXTRACT_PROMPT)
    assert m, "the triples template no longer opens with the subject placeholder"
    value = m.group(1)
    assert "|" not in value, value
    assert "user" in value and "person:<name>" in value and "org:<name>" in value


@pytest.mark.parametrize("subject", ["user", "User", "USER", "person:Tansy Ko", "org:Acme Corp",
                                     "task:release-cut", "place:Porto, Portugal", "Rex",
                                     "the landlord", "org:https://acme.example"])
def test_the_rule_admits_every_form_the_shipped_suite_stores(subject):
    """Exactly the defect and no wider: `user` in any case, the prompt's
    kind:name forms, a host's kinds, and a BARE entity name (the B07 relay
    shape `Rex` under `has_diet`, which 0026 governs) all keep storing."""
    assert not subject_off_grammar(subject)


@pytest.mark.parametrize("subject", ["user|person:Tansy|org:Acme Corp", "org:Acme|Globex",
                                     "user|", "|", "person:<name>|org:<name>"])
def test_the_rule_refuses_the_pipe(subject):
    assert subject_off_grammar(subject)


def test_the_claimant_slot_of_a_third_party_claim_is_exempt(tmp_path):
    """`third_party_claim`'s subject is the CLAIMANT — free text by the
    prompt's own rule and 0024's coherence step; a receipt record supersedes
    nothing, so the pipe defect cannot reach it. The exemption is by the
    RELATION, and a fact under any other relation gets no such pass."""
    mem = _mem(tmp_path, _scripted([
        {"subject": "the landlord|org:Acme", "relation": "third_party_claim", "object": "user owes $500"},
        {"subject": "the landlord|org:Acme", "relation": "located_at", "object": "Porto"},
    ]))
    r = mem.remember(U, "The landlord says I owe $500.", context=EvidenceContext.direct())
    edges = mem.store.edges(U, active_only=False)
    assert [e.relation for e in edges] == ["third_party_claim"] and r["subject_refused"] == 1
    assert edges[0].quarantined


def test_a_pipe_composed_subject_writes_nothing_and_is_counted(tmp_path):
    """The scripted provider returns exactly what gpt-4o-mini returned: a
    concatenated subject. Nothing is written under it (or any subject) and
    the report says so; a well-formed sibling triple in the same response
    is written as before."""
    mem = _mem(tmp_path, _scripted([
        {"subject": "user|person:<name>|org:Acme Corp", "relation": "works_as", "object": "analyst"},
        {"subject": "user", "relation": "located_at", "object": "Porto"},
    ]))
    r = mem.remember(U, "I am an analyst at Acme and I live in Porto.", context=EvidenceContext.direct())
    assert r["subject_refused"] == 1 and r["facts"] == 1
    edges = mem.store.edges(U, active_only=False)
    assert [e.subject for e in edges] == ["user"] and all("|" not in e.subject for e in edges)
    # the counter is present on every path — a parse failure included
    bad = _mem(tmp_path, lambda *a, **k: "not json")
    assert bad.remember(U, "x", context=EvidenceContext.direct())["subject_refused"] == 0
    # and stripped from the MCP result like the other operator counters
    from veracium import mcp_server
    assert "subject_refused" in mcp_server._OPERATOR_ONLY


def test_the_job_change_supersedes_under_a_provider_that_returns_the_admitted_forms(tmp_path):
    """The case the selfcheck exists to show, with the grammar enforced: two
    facts under ONE subject supersede — one active, one retired."""
    calls = {"n": 0}
    def llm(prompt, **k):
        if k.get("role") == "distill-retry":
            return json.dumps({"triples": []})
        if "gate" in (k.get("role") or "") or "GROUNDED" in prompt:
            return "Globex"
        calls["n"] += 1
        obj = "Acme Corp" if calls["n"] == 1 else "Globex"
        return json.dumps({"triples": [{"subject": "user", "relation": "works_as", "object": obj}],
                           "episode": "x", "instructions": []})
    mem = _mem(tmp_path, llm)
    mem.remember(U, "I work as an analyst at Acme Corp.", context=EvidenceContext.direct(), date="2026-01-05")
    mem.remember(U, "I switched jobs — now Globex.", context=EvidenceContext.direct(), date="2026-06-20")
    edges = mem.store.edges(U, active_only=False)
    assert len(edges) == 2 and sorted(e.active for e in edges) == [False, True]


def test_the_telemetry_whitelist_and_the_result_inventory_disagree_by_declaration(tmp_path):
    """§4c (v14): the ingest RESULT's counter inventory and 0017's consented
    telemetry whitelist are different sets by consent — a counter enters the
    telemetry event only by a SCHEMA_VERSION bump. The difference is DERIVED
    from a live ingest and must equal the declared set below, each member
    with its reason; a new result-only counter must be declared here (or
    bumped into the whitelist), never left to a list that reads as complete."""
    from veracium.telemetry import EVENT_FIELDS
    mem = _mem(tmp_path, _scripted([]))
    r = mem.remember(U, "hi", context=EvidenceContext.direct())
    # TWO CLASSES, so the derived difference is a detector and never a
    # backlog: a member is either AWAITING CONSENT (a counter that may enter
    # the whitelist by a SCHEMA_VERSION bump) or NEVER ELIGIBLE (content or
    # identity — admitting it would break 0017's content-free guarantee, not
    # merely need a bump). Resolving a disagreement by ADDING a never-eligible
    # member is the wrong direction, and this declaration says so per key.
    AWAITING, NEVER = "awaiting_consent", "never_eligible_content_free_event"
    declared = {
        # specs/0025 §4c as amended for 0039 round-5 R5-1 (2026-09-11): the
        # OUTCOME boolean — not content, not identity; may enter the whitelist
        # by a SCHEMA_VERSION bump on a ruling, and has not (docs/telemetry.md)
        "extraction_unusable": (AWAITING, "the §4c outcome boolean (0039 round-5 R5-1); "
                                "not content, not identity; enters the whitelist only by a "
                                "SCHEMA_VERSION bump on a ruling — docs/telemetry.md says it is not sent"),
        "episode": (NEVER, "the episode TEXT — content"),
        "quarantined_at_birth": (NEVER, "0023 Q4 audit fact — the audit sink's, whitelist-dropped by design"),
        "birth_revocation_digest": (NEVER, "0023 Q4 audit fact — an identity digest"),
        "agreement_floored": (AWAITING, "0026 §3d counter — public, outside the consented schema (v4 is 0025's counters)"),
        "agreement_recorded": (AWAITING, "0026 §3d counter — public, outside the consented schema"),
        "procedures": (AWAITING, "0037 v16 §4a-iii counter — public, outside the consented schema; not sent"),
        "procedural_refused": (AWAITING, "0037 v16 §4a-iii counter — public, outside the consented schema; not sent"),
        "instructions_dropped": (AWAITING, "0038 §2b refusal counter — public, outside the consented schema"),
        "subject_refused": (AWAITING, "0025 v14 §4b-vi refusal counter — public, outside the consented schema"),
    }
    assert all(cls in (AWAITING, NEVER) for cls, _why in declared.values())
    assert set(r) - EVENT_FIELDS["ingest"] == set(declared), \
        sorted((set(r) - EVENT_FIELDS["ingest"]) ^ set(declared))


def test_the_selfcheck_requires_the_supersession_pair_outside_the_tolerance(monkeypatch):
    """12/13 with `history_retained` false is what 0.20.0 scored under a
    documented provider — it PASSED the 90% tolerance. The pair is now
    mandatory: the same scores must FAIL, and the scorecard says why."""
    # the sibling file is loaded by PATH: `tests/` is not an importable
    # package on CI (no __init__.py), and the rootdir import that works
    # locally is exactly the difference the first CI run found
    import importlib.util
    import pathlib
    here = pathlib.Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("_sc_provider", here / "test_selfcheck.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    Provider = mod.Provider
    monkeypatch.setattr(selfcheck, "_check_supersession",
                        lambda llm, tmp, relations: (1, 2, {"current_value": True, "history_retained": False}))
    r = selfcheck.run(Provider())
    assert r["total_ok"] == 12 and r["total_n"] == 13 and r["total_ok"] / r["total_n"] >= 0.9
    assert r["injection_asserts"] == 0
    assert r["passed"] is False
    assert "supersession   1/2 (must be 2/2)" in selfcheck.format_scorecard(r)
