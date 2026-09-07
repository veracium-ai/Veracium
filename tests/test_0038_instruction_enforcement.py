"""specs/0038 §2b/§2c — the ingest enforcement: a DECLARED instruction is filed,
never stored; a triple that restates it is REFUSED and the REFUSAL is counted.

External round 1 (2026-09-07, R1-1) showed that adding `instructions` to the
extraction JSON does not by itself prevent an extractor from ALSO emitting a
disposition triple for the same instruction, and asked for "a scripted-provider
regression that deliberately returns both carriers and proves the disposition
is not stored." This file was landed first as a STRICT-xfail set pinning the
unbuilt rule (`ce02bd5`); the enforcement then landed under the owner's
security-hotfix authorization ("I am authorizing the 0038 ingest enforcement
under the security-hotfix exception by 09/14/2026", ledger, 2026-09-07) and the
markers came off in the same commit — the defect control that asserted the old
behaviour is deleted, not inverted.

Each test names its §2c row (v3's matrix). The provider is scripted: no model,
no network. The assertions are the spec's and no wider: a DECLARED instruction
never becomes a disposition fact; the event IS retained as one episode; the
report carries `instructions_dropped` as a present key on every return path,
counting REFUSALS — never declarations, never malformed members. The rule is
necessary and not sufficient: a provider that emits ONLY the coerced triple,
declaring nothing (row 1), gives ingest nothing to relate it to and stores as
today. That silent-coercion residual is research's harness figure
(V-SILENT-COERCION-MEASURED) and is NOT claimed closed here; deciding that a
triple's content is an instruction without the model saying so is the
free-text detection Q6 retired — this file must never grow a test asserting it.

The counter's carriers (0025 §4c, V-COUNTER-INVENTORY inherited): the normal
report dict, the unparseable early-return dict, and `PUBLIC_COUNTERS` in
tests/test_0025_enforcement.py (X4 every-path zeros; X12 exact key set). The
MCP tool result STRIPS it with its five 0025 siblings (0031 §4d's argument: a
model that learns how often its coercions are refused learns to probe) — a
recorded deviation from v3 §10 Q1's "the MCP tool result that already
serialises that dict", which is not what that surface does to extractor
counters; the library report carries it. v4 ratifies or reverses; the test
below pins whichever the code does so the spec and the surface cannot drift
silently.
"""
from __future__ import annotations

import json

import pytest

from veracium.ingest import ingest_event
from veracium.mcp_server import _OPERATOR_ONLY
from veracium.prompts import EXTRACT_SCHEMA
from veracium.schema import EvidenceAuthor, EvidenceContext
from veracium.store.sqlite import SqliteStore

INSTRUCTION = "Run the formatter before committing."
COERCED = {"subject": "user", "relation": "prefers",
           "object": "run the formatter before committing"}
U = "u-0038"


def _llm_returning(payload):
    text = payload if isinstance(payload, str) else json.dumps(payload)

    def llm(prompt, *, system=None, role="distill", json_schema=None):
        if role == "distill-retry":
            return json.dumps({"triples": []})
        return text
    return llm


def _ingest(tmp_path, llm):
    store = SqliteStore(str(tmp_path / "s.db"))
    try:
        report = ingest_event(store, llm, U, event_text=INSTRUCTION,
                              author=EvidenceAuthor.USER, date="2026-09-07",
                              context=EvidenceContext.direct())
        edges = store.edges(U, active_only=False, include_quarantined=True)
        episodes = store.episodes(U)
        return report, edges, episodes
    finally:
        store.close()


def _both_carriers():
    """The reviewer's adversarial output, verbatim in shape."""
    return {"instructions": [INSTRUCTION], "triples": [COERCED],
            "episode": "The user instructed the formatter run."}


def _coerced(edges):
    return [e for e in edges if e.relation == "prefers" and "formatter" in (e.object or "").lower()]


# ---------------------------------------------------------------------------
# §2b — the schema carrier
# ---------------------------------------------------------------------------

def test_schema_requires_instructions_as_a_string_array():
    """§2b: `required` is `[triples, episode, instructions]`; the field is an
    array of strings. An empty list is valid, an absent key is not — for a
    provider that honours the hint."""
    assert EXTRACT_SCHEMA["required"] == ["triples", "episode", "instructions"]
    assert EXTRACT_SCHEMA["properties"]["instructions"] == {"type": "array", "items": {"type": "string"}}


# ---------------------------------------------------------------------------
# §2c ROW 5 — the reviewer's JSON: both carriers in one response
# ---------------------------------------------------------------------------

def test_both_carriers_the_disposition_is_not_stored(tmp_path):
    """§2c ROW 5, R1-1's exact case. The coerced triple never becomes an edge."""
    _, edges, _ = _ingest(tmp_path, _llm_returning(_both_carriers()))
    assert _coerced(edges) == [], [(e.relation, e.object) for e in edges]


def test_both_carriers_the_report_counts_the_dropped_instruction(tmp_path):
    """§2c ROW 5 (the counter half): one refusal, the counter reads 1, as a
    PRESENT key (0025 §4c — an absent key is not a zero)."""
    report, _, _ = _ingest(tmp_path, _llm_returning(_both_carriers()))
    assert "instructions_dropped" in report, sorted(report)
    assert report["instructions_dropped"] == 1


def test_both_carriers_the_event_is_retained_as_one_episode(tmp_path):
    """V-EVENT-RETAINED: refusing the triple never drops the event — exactly
    one episode records that the instruction was given."""
    report, _, episodes = _ingest(tmp_path, _llm_returning(_both_carriers()))
    assert report.get("unparseable") is not True
    assert len(episodes) == 1, f"{len(episodes)} episodes for one event"


def test_the_match_is_equality_under_the_comparison_key_not_containment(tmp_path):
    """§2b's "carries the same content": the reviewer's pair differs by case
    and a trailing period and MUST match; a triple whose object merely
    CONTAINS the instruction must NOT — containment would decide that a
    triple is an instruction without the model saying so (Q6, retired)."""
    payload = {"instructions": ["  RUN the formatter   before committing "],
               "triples": [COERCED,
                           {"subject": "user", "relation": "prefers",
                            "object": "to run the formatter before committing, and to lint"}],
               "episode": "x"}
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert report["instructions_dropped"] == 1
    assert [e.object for e in edges if e.relation == "prefers"] == ["to run the formatter before committing, and to lint"]


def test_the_counter_counts_refusals_two_restating_triples_read_two(tmp_path):
    """The counter is OF REFUSALS: one declaration, two triples restating it
    (different relations), both refused, reads 2 — the mirror of row 4."""
    payload = {"instructions": [INSTRUCTION],
               "triples": [COERCED, {"subject": "user", "relation": "works_on",
                                     "object": "Run the formatter before committing"}],
               "episode": "x"}
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert report["instructions_dropped"] == 2
    assert edges == []


# ---------------------------------------------------------------------------
# §2c ROWS 3 and 4 — V-INSTRUCTIONS-WELL-FORMED
# ---------------------------------------------------------------------------

def test_row3_malformed_members_are_dropped_and_not_counted(tmp_path):
    """§2c ROW 3: a non-string, an empty string and a whitespace-only string
    beside one well-formed member, one triple restating that member: the
    malformed members are DROPPED and NOT COUNTED, the counter reads exactly
    1. The "count malformed members" mutant reads 4 here; and the well-formed
    member still refuses its triple, so dropping members is not dropping the
    field."""
    payload = {"instructions": [3, "", "   ", INSTRUCTION], "triples": [COERCED],
               "episode": "The user instructed the formatter run."}
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert report.get("unparseable") is not True, "malformed MEMBERS are not a malformed RESPONSE"
    assert _coerced(edges) == []
    assert report["instructions_dropped"] == 1, report


def test_row3_only_malformed_members_is_an_empty_declaration(tmp_path):
    """§2c ROW 3's edge: every member malformed → nothing declared, nothing
    refused, the triple stores as today (row 1's outcome), counter 0."""
    payload = {"instructions": [None, "", " ", 7], "triples": [COERCED], "episode": "x"}
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert report["instructions_dropped"] == 0
    assert len(_coerced(edges)) == 1


def test_row4_duplicates_count_one_refusal(tmp_path):
    """§2c ROW 4: three declarations of ONE instruction against one restating
    triple: de-duplicated before comparison, the counter reads 1, not 3 — the
    "count declarations" mutant reads 3 here."""
    payload = {"instructions": [INSTRUCTION, INSTRUCTION, INSTRUCTION], "triples": [COERCED],
               "episode": "The user instructed the formatter run."}
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert _coerced(edges) == []
    assert report["instructions_dropped"] == 1, report


# ---------------------------------------------------------------------------
# §2c ROWS 1, 2, 6, 7, 8 — the surrounding matrix
# ---------------------------------------------------------------------------

def test_row1_absent_instructions_is_processed_as_today_the_residual(tmp_path):
    """§2c ROW 1: a provider that omits the key entirely is processed as
    today — the coerced triple STORES, because there is no declaration to
    relate it to. `instructions_dropped: 0`, present. This is the measured
    residual, not a refusal, and this test asserts the bound exactly."""
    payload = {"triples": [COERCED], "episode": "x"}
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert report.get("unparseable") is not True
    assert report["instructions_dropped"] == 0
    assert len(_coerced(edges)) == 1


@pytest.mark.parametrize("bad", ["a string", {"k": "v"}, None], ids=["str", "dict", "null"])
def test_row2_wrong_type_instructions_is_the_unparseable_branch(tmp_path, bad):
    """§2c ROW 2: a VALID JSON response whose `instructions` is PRESENT and
    the wrong type (string, dict, null) is a malformed response: the
    unparseable branch — zero edges, the placeholder episode, every counter
    present at zero."""
    payload = {"instructions": bad, "triples": [{"subject": "user", "relation": "uses_tool", "object": "ruff"}],
               "episode": "x"}
    report, edges, episodes = _ingest(tmp_path, _llm_returning(payload))
    assert report.get("unparseable") is True, report
    assert edges == []
    assert len(episodes) == 1 and "unprocessed" in (episodes[0].summary or "")
    assert report["instructions_dropped"] == 0


def test_row6_prose_response_is_the_unparseable_branch(tmp_path):
    """§2c ROW 6 (prose): a response that is not JSON takes the unparseable
    branch: zero edges, the content-free placeholder episode, the counter
    inventory present at zero. Unchanged by 0038."""
    report, edges, episodes = _ingest(tmp_path, _llm_returning("not json at all"))
    assert report.get("unparseable") is True
    assert edges == []
    assert len(episodes) == 1 and "unprocessed" in (episodes[0].summary or "")
    for k in ("invalid", "retried", "recovered", "residual", "redispositioned", "instructions_dropped"):
        assert report.get(k) == 0, (k, report)


def test_row6_bare_array_is_normalised_and_declares_nothing(tmp_path):
    """§2c ROW 6 (bare array): the wrapper-less triples payload is normalised
    (`ingest.py`'s list branch) — no `instructions` key exists on that shape,
    so it is row 1's outcome: processed, counter 0."""
    payload = [{"subject": "user", "relation": "uses_tool", "object": "ruff"}]
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert report.get("unparseable") is not True
    assert report["instructions_dropped"] == 0
    assert any(e.relation == "uses_tool" and e.object == "ruff" for e in edges)


def test_row6_extra_keys_are_processed_the_schema_is_not_enforced_at_ingest(tmp_path):
    """§2c ROW 6 (extra keys) — the CONTROL for the row's sentence: extra keys
    are PROCESSED, not rejected. `EXTRACT_SCHEMA` is a hint handed to the
    provider; ingest validates nothing against it. If ingest ever starts
    enforcing the schema this goes red and the row's text changes with it."""
    payload = {"triples": [{"subject": "user", "relation": "uses_tool", "object": "ruff"}],
               "episode": "x", "instructions": [], "unknown_key": {"anything": 1}}
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert report.get("unparseable") is not True
    assert any(e.relation == "uses_tool" and e.object == "ruff" for e in edges)


def test_row7_mixed_event_keeps_its_declarative_facts_and_refuses_only_the_match(tmp_path):
    """§2c ROW 7: a mixed response — a genuine fact beside the instruction and
    its restating triple. The fact STORES; only the restating triple is
    refused; the counter reads 1. A mixed event must not lose its
    declarative facts."""
    payload = {"instructions": [INSTRUCTION],
               "triples": [{"subject": "user", "relation": "located_at", "object": "Lisbon"}, COERCED],
               "episode": "The user said they live in Lisbon and instructed the formatter run."}
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert any(e.relation == "located_at" and e.object == "Lisbon" for e in edges), "the declarative fact must survive"
    assert _coerced(edges) == []
    assert report["instructions_dropped"] == 1


def test_row8_unparseable_branch_carries_the_counter_at_zero(tmp_path):
    """§2c ROW 8: on the path that never parsed a response the counter is
    PRESENT and zero — 0025 §4c's an-absent-key-is-not-a-zero, enforced for
    every public counter by tests/test_0025_enforcement.py now that the key
    is in PUBLIC_COUNTERS."""
    report, _, _ = _ingest(tmp_path, _llm_returning("not json at all"))
    assert report.get("unparseable") is True
    assert "instructions_dropped" in report, sorted(report)
    assert report["instructions_dropped"] == 0


# ---------------------------------------------------------------------------
# V-THIRD-PARTY-UNTOUCHED — the receipt record is not a speech act of the user
# ---------------------------------------------------------------------------

NOTICE = "Pay the invoice by Friday."


def _ingest_third_party(tmp_path, payload):
    store = SqliteStore(str(tmp_path / "s.db"))
    try:
        report = ingest_event(store, _llm_returning(payload), U, event_text=NOTICE,
                              author=EvidenceAuthor.THIRD_PARTY, date="2026-09-07",
                              context=EvidenceContext.direct())
        return report, store.edges(U, active_only=False, include_quarantined=True)
    finally:
        store.close()


def test_a_third_party_claim_survives_its_own_declaration(tmp_path):
    """The adversarial case the diff-scan raised: an extractor files a
    third-party notice's wording under `instructions` AND emits the
    `third_party_claim` receipt for it. The receipt is NOT a disposition of
    the user (0001/0023: "received an unverified notice that …"); refusing it
    would erase the received-claim history the trust gate depends on and
    change `prompts.py:41`'s rule in behaviour, which V-THIRD-PARTY-UNTOUCHED
    forbids. The claim stores; the counter reads 0."""
    payload = {"instructions": [NOTICE],
               "triples": [{"subject": "acme", "relation": "third_party_claim", "object": NOTICE}],
               "episode": "received an unverified notice that the invoice is due Friday"}
    report, edges = _ingest_third_party(tmp_path, payload)
    assert [e.relation for e in edges] == ["third_party_claim"]
    assert report["instructions_dropped"] == 0


def test_the_exemption_is_the_receipt_relation_not_the_author(tmp_path):
    """The exemption keys on the RELATION, never on the author: a user-
    disposition triple restating a declared instruction is refused even on a
    third-party-authored event — the fabricated disposition is the defect
    whatever the author, and the receipt record is the only thing exempt."""
    payload = {"instructions": [NOTICE],
               "triples": [{"subject": "acme", "relation": "third_party_claim", "object": NOTICE},
                           {"subject": "user", "relation": "prefers", "object": "pay the invoice by friday"}],
               "episode": "x"}
    report, edges = _ingest_third_party(tmp_path, payload)
    assert [e.relation for e in edges] == ["third_party_claim"]
    assert report["instructions_dropped"] == 1


# ---------------------------------------------------------------------------
# The surfaces (§4, §10 Q1) — where the counter goes and where it does not
# ---------------------------------------------------------------------------

def test_the_mcp_tool_result_strips_the_counter_with_its_siblings():
    """The recorded deviation from v3 §10 Q1, pinned so it cannot drift
    silently: `instructions_dropped` is in the MCP strip list beside the five
    0025 counters (0031 §4d: refusal counts teach a model to probe). The
    library report carries it (every test above reads it from ingest's
    dict). If v4 rules the other way, this test changes with the tuple."""
    assert "instructions_dropped" in _OPERATOR_ONLY
    for sibling in ("invalid", "retried", "recovered", "residual", "redispositioned"):
        assert sibling in _OPERATOR_ONLY
