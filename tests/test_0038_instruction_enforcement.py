"""specs/0038 — the reviewer's round-1 regression (R1-1), pinned as unbuilt-by-design.

External round 1 (2026-09-07) showed that adding `instructions` to the extraction
JSON does not prevent an extractor from ALSO emitting a disposition triple for
the same instruction: a response carrying both carriers is schema-valid, ingest
counts the field and stores the triple, so the stored set shrinks only if the
model obeys the prompt. The reviewer asked for "a scripted-provider regression
that deliberately returns both carriers and proves the disposition is not
stored." This is that regression.

It is a STRICT XFAIL until the enforcement lands — `specs/REVIEWER_GUIDE.md`'s
shape for regressions pinning not-yet-implemented behaviour of the spec under
review. Strict means: the day the ingest rule is implemented and this starts
passing, the marker must be removed in the same commit, or the suite fails —
an xfail cannot silently become a decorative pass. The owner decided round 2
is implementation-first ("Go with option 1", 2026-09-07); the ingest change
itself waits on the owner's path through the spec-reference gate (only an
accepted spec, or a declared exception, authorises a guarded-surface commit —
`ingest.py` is guarded, 0038 is a draft).

WHOEVER LANDS THE ENFORCEMENT EDITS THIS FILE IN THREE PLACES, IN THE SAME
COMMIT — a fix that touches only one will be red for a reason that looks like
a broken fix and is not:
  1. remove `@pytest.mark.xfail(strict=True, …)` from
     `test_both_carriers_the_disposition_is_not_stored` — strict means an
     XPASS FAILS, so it goes red the moment the rule works;
  2. the same for `test_both_carriers_the_report_counts_the_dropped_instruction`;
  3. delete `test_today_the_coerced_disposition_is_stored_documenting_the_defect`
     — it asserts the DEFECT and becomes a false claim the moment the rule
     works.
And the counter itself has THREE sites in the product, enforced both ways by
0025's existing inventory test (`tests/test_0025_enforcement.py`: the
`PUBLIC_COUNTERS` tuple; every counter present and zero on the unparseable
path; the report's EXACT key set): `instructions_dropped` goes into the normal
report dict, into the unparseable early-return dict at `ingest.py:261`, AND
into `PUBLIC_COUNTERS` — miss one and an existing test names it. 0038 inherits
V-COUNTER-INVENTORY there rather than inventing its own.

§2c's matrix (v3, 2026-09-07) has eight rows; each row tested here names
itself, and no test was written before its row existed — a test written before
the row would be inventing the contract in the assertion. Row 1 (`instructions`
absent) is a harness measurement of the prompt, not a scripted-provider case,
and lives in research's harness. Rows 3 and 4 are V-INSTRUCTIONS-WELL-FORMED:
a non-string or empty/whitespace member is DROPPED and NOT COUNTED; duplicates
are de-duplicated before comparison; `instructions_dropped` counts REFUSALS,
never DECLARATIONS — the two mutants the row exists to kill are "count
declarations" (the figure stops meaning records prevented and starts meaning
things the model said) and "count malformed members" (malformed input inflates
the one number this spec's acceptance turns on).

The provider is scripted: no model, no network. The assertions are the spec's
(§2b as it must read after R1-1), and no wider: a DECLARED instruction — one
the extractor filed in `instructions` — never becomes a disposition fact; the
event IS retained as one episode; the report carries `instructions_dropped` as
a present key with the count (an absent key is not a zero, 0025 §4c). The rule
is necessary and not sufficient: a provider that emits ONLY the coerced triple,
declaring nothing, gives ingest nothing to relate it to and stores as today.
That silent-coercion residual is measured by research's harness as a
first-class figure and stated beside V-NO-COERCED-DISPOSITION; it is NOT
claimed closed here, and deciding that a triple's content is an instruction
without the model saying so is the free-text detection Q6 retired on
measured evidence — this file must never grow a test that asserts it.
"""
from __future__ import annotations

import json

import pytest

from veracium.ingest import ingest_event
from veracium.schema import EvidenceAuthor, EvidenceContext
from veracium.store.sqlite import SqliteStore

INSTRUCTION = "Run the formatter before committing."
U = "u-0038"


def _both_carriers_llm(prompt, *, system=None, role="distill", json_schema=None):
    """The reviewer's adversarial output, verbatim in shape: the instruction filed
    in `instructions` AND coerced into a `prefers` triple in the same response."""
    if role == "distill-retry":
        return json.dumps({"triples": []})
    return json.dumps({
        "instructions": [INSTRUCTION],
        "triples": [{"subject": "user", "relation": "prefers",
                     "object": "run the formatter before committing"}],
        "episode": "The user instructed the formatter run.",
    })


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


UNBUILT = ("specs/0038 §2b after external round 1 (R1-1): the ingest rule that refuses a "
           "disposition triple whose object matches an `instructions` member is not yet "
           "implemented — implementation-first on the owner's word, pending the gate path")


@pytest.mark.xfail(strict=True, reason=UNBUILT)
def test_both_carriers_the_disposition_is_not_stored(tmp_path):
    """§2c ROW 5. R1-1's exact case: instructions AND a prefers triple in one response. The
    triple must not become an edge. Today it does — the assertion fails, and the
    strict marker records that as the spec's unbuilt behaviour, not as a pass."""
    report, edges, _ = _ingest(tmp_path, _both_carriers_llm)
    coerced = [e for e in edges if e.relation == "prefers"
               and "formatter" in (e.object or "").lower()]
    assert coerced == [], f"the coerced disposition was stored: {[(e.relation, e.object) for e in coerced]}"


@pytest.mark.xfail(strict=True, reason=UNBUILT)
def test_both_carriers_the_report_counts_the_dropped_instruction(tmp_path):
    """§2c ROW 5 (the counter half). The counter counts REFUSALS, never declarations
    (row 4's discipline): one instruction, one matching triple refused, reads 1. It is a PRESENT key on every return path (0025 §4c's rule — an
    absent key is not a zero), and here it counts the one instruction."""
    report, _, _ = _ingest(tmp_path, _both_carriers_llm)
    assert "instructions_dropped" in report, f"report keys: {sorted(report)}"
    assert report["instructions_dropped"] == 1


def test_both_carriers_the_event_is_retained_as_one_episode(tmp_path):
    """V-EVENT-RETAINED's half that holds TODAY: dropping (or not) the triple
    never drops the event — exactly one episode records that the instruction
    was given. Not xfail: this is shipped behaviour the spec keeps."""
    report, _, episodes = _ingest(tmp_path, _both_carriers_llm)
    assert report.get("unparseable") is not True
    assert len(episodes) == 1, f"{len(episodes)} episodes for one event"


def test_today_the_coerced_disposition_is_stored_documenting_the_defect(tmp_path):
    """The control that makes the xfails mean something: on the shipped code the
    reviewer's response DOES store the disposition. When the enforcement lands
    this control must be inverted or removed in the same commit — a control
    asserting the defect cannot outlive the fix."""
    _, edges, _ = _ingest(tmp_path, _both_carriers_llm)
    assert any(e.relation == "prefers" and "formatter" in (e.object or "").lower() for e in edges), (
        "the shipped code no longer stores the coerced disposition — the enforcement has landed; "
        "remove this control and the xfail markers above in the same commit")


# ---------------------------------------------------------------------------
# §2c rows that fall out of SHIPPED paths (research's matrix, 2026-09-07: rows
# 2, 6 and 8 "need no new behaviour"). Each names its row. They pass today
# except where they assert the not-yet-existing counter, which is strict-xfail
# until it lands (row 8's key).
# ---------------------------------------------------------------------------

def _llm_returning(payload_text):
    def llm(prompt, *, system=None, role="distill", json_schema=None):
        if role == "distill-retry":
            return json.dumps({"triples": []})
        return payload_text
    return llm


@pytest.mark.xfail(strict=True, reason=UNBUILT)
@pytest.mark.parametrize("bad", ["a string", {"k": "v"}, None], ids=["str", "dict", "null"])
def test_row2_wrong_type_instructions_is_the_unparseable_branch(tmp_path, bad):
    """§2c ROW 2: a VALID JSON response whose `instructions` is the wrong type
    (string, dict, null) is treated as unparseable: zero edges, the placeholder
    episode, `unparseable: True`. NEW behaviour — on shipped code the field is
    not read at all (`data.get("triples")`), so all three are processed today
    and the triple stores; strict xfail until the type check exists. (An
    earlier draft of this test fed a non-JSON response, which is ROW 6's prose
    case wearing row 2's name — the name-is-a-claim defect, caught on the v3
    read.)"""
    payload = json.dumps({"instructions": bad,
                          "triples": [{"subject": "user", "relation": "uses_tool", "object": "ruff"}],
                          "episode": "x"})
    report, edges, episodes = _ingest(tmp_path, _llm_returning(payload))
    assert report.get("unparseable") is True, report
    assert edges == []
    assert len(episodes) == 1


def test_row6_prose_response_is_the_unparseable_branch(tmp_path):
    """§2c ROW 6 (prose): a response that is not JSON takes the unparseable
    branch today: zero edges, the content-free placeholder episode, the counter
    inventory present at zero. Shipped behaviour, unchanged by 0038."""
    report, edges, episodes = _ingest(tmp_path, _llm_returning("not json at all"))
    assert report.get("unparseable") is True
    assert edges == []
    assert len(episodes) == 1 and "unprocessed" in (episodes[0].summary or "")
    for k in ("invalid", "retried", "recovered", "residual", "redispositioned"):
        assert report.get(k) == 0, (k, report)


def test_row6_extra_keys_are_processed_today_the_schema_is_not_enforced_at_ingest(tmp_path):
    """§2c ROW 6 (extra keys) — the CONTROL for a v3 sentence: "extra keys are
    rejected by `additionalProperties: False`". They are not: `EXTRACT_SCHEMA`'s
    only use is `json_schema=prompts.EXTRACT_SCHEMA` at `ingest.py:236`, a hint
    handed to the provider; ingest validates nothing against it. An unknown key
    beside valid triples is processed and the triple stores. If ingest ever
    starts enforcing the schema this test goes red and the row's text becomes
    true — change both together."""
    payload = json.dumps({"triples": [{"subject": "user", "relation": "uses_tool", "object": "ruff"}],
                          "episode": "x", "unknown_key": {"anything": 1}})
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert report.get("unparseable") is not True
    assert any(e.relation == "uses_tool" and e.object == "ruff" for e in edges)


def test_row6_schema_ignoring_provider_bare_array_is_normalised(tmp_path):
    """§2c ROW 6: a provider that returns a bare array of triples instead of the
    object is normalised (`ingest.py:241` wraps it) — unchanged by 0038."""
    payload = json.dumps([{"subject": "user", "relation": "uses_tool", "object": "ruff"}])
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert report.get("unparseable") is not True
    assert any(e.relation == "uses_tool" and e.object == "ruff" for e in edges)


@pytest.mark.xfail(strict=True, reason=UNBUILT)
def test_row8_unparseable_branch_carries_the_counter_at_zero(tmp_path):
    """§2c ROW 8: on the path that never parsed a response the counter is PRESENT
    and zero — 0025 §4c's an-absent-key-is-not-a-zero, enforced for every
    public counter by tests/test_0025_enforcement.py once the key joins
    PUBLIC_COUNTERS. Strict xfail until `instructions_dropped` exists."""
    report, _, _ = _ingest(tmp_path, _llm_returning("not json at all"))
    assert report.get("unparseable") is True
    assert "instructions_dropped" in report, sorted(report)
    assert report["instructions_dropped"] == 0


def test_row7_mixed_event_keeps_its_declarative_facts_today(tmp_path):
    """§2c ROW 7's shipped half: a mixed response carrying a genuine fact beside
    the instruction keeps the fact. The refusal half (only the MATCHING triple
    refused) joins this test when the rule lands."""
    payload = json.dumps({
        "instructions": [INSTRUCTION],
        "triples": [{"subject": "user", "relation": "located_at", "object": "Lisbon"},
                    {"subject": "user", "relation": "prefers", "object": "run the formatter before committing"}],
        "episode": "The user said they live in Lisbon and instructed the formatter run.",
    })
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert any(e.relation == "located_at" and e.object == "Lisbon" for e in edges), "the declarative fact must survive"


# ---------------------------------------------------------------------------
# §2c rows 3 and 4 — V-INSTRUCTIONS-WELL-FORMED. The counter counts REFUSALS:
# malformed members move it by 0, repeated declarations of one instruction
# count once. Both strict-xfail until the counter exists; each is written so
# that the mutant it names FAILS it the day the rule lands.
# ---------------------------------------------------------------------------

@pytest.mark.xfail(strict=True, reason=UNBUILT)
def test_row3_malformed_members_are_dropped_and_not_counted(tmp_path):
    """§2c ROW 3: `instructions` carries a non-string, an empty string and a
    whitespace-only string beside one well-formed member; one coerced triple
    matches that member. Malformed members are DROPPED and NOT COUNTED, so the
    counter reads exactly 1 — the one refusal. The "count malformed members"
    mutant reads 4 here and fails; the well-formed member still refuses its
    triple, so dropping malformed members cannot be mistaken for dropping the
    field."""
    payload = json.dumps({
        "instructions": [3, "", "   ", INSTRUCTION],
        "triples": [{"subject": "user", "relation": "prefers",
                     "object": "run the formatter before committing"}],
        "episode": "The user instructed the formatter run.",
    })
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert report.get("unparseable") is not True, "malformed MEMBERS are not a malformed RESPONSE"
    assert not any(e.relation == "prefers" for e in edges), "the well-formed member must still refuse its triple"
    assert report.get("instructions_dropped") == 1, report


@pytest.mark.xfail(strict=True, reason=UNBUILT)
def test_row4_duplicates_count_one_refusal(tmp_path):
    """§2c ROW 4: three declarations of ONE instruction against one coerced
    triple. Duplicates are de-duplicated before comparison and the counter
    counts refusals, so it reads 1, not 3. The "count declarations" mutant
    reads 3 here and fails — the figure would have stopped meaning records
    prevented and started meaning things the model said."""
    payload = json.dumps({
        "instructions": [INSTRUCTION, INSTRUCTION, INSTRUCTION],
        "triples": [{"subject": "user", "relation": "prefers",
                     "object": "run the formatter before committing"}],
        "episode": "The user instructed the formatter run.",
    })
    report, edges, _ = _ingest(tmp_path, _llm_returning(payload))
    assert not any(e.relation == "prefers" for e in edges)
    assert report.get("instructions_dropped") == 1, report
