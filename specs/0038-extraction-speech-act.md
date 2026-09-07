# Feature spec: the extraction's speech-act discipline

Spec-Status: draft

*Candidate authored by research (veracium-research), 2026-09-07, on the owner's
word ("I approve your recommendation on all three and order you to implement all
3", 2026-09-07). **0038 — the registry's next uncontested number:** ALLOCATION
holds 0001–0032 and 0037; **0033–0036 are RESERVED** for the self-learning
decomposition arc (banked 2026-09-04, upheld by the owner 2026-09-06) and live
in COORDINATION rather than ALLOCATION, which is exactly how research collided
with them once before. Checked both, and for any claim on 0038: none.*

| | |
|---|---|
| **Author / session** | research (veracium-research) |
| **Version** | **v4 — THE IMPLEMENTATION FOLD.** The enforcement **LANDED** 2026-09-07 at `d59592d` under the owner's security-hotfix exception (`Spec-Retrospective-Due: 2026-09-14`), CI 34120362836 green, suite 2772/8/0 — **the regression file's eight strict xfails are now eight real passes.** v4 folds what implementing it found, both from dev's adversarial diff-scan and neither from re-reading. **THE THIRD-PARTY EXEMPTION IS THE MECHANISM V-THIRD-PARTY-UNTOUCHED REQUIRED AND §2b DID NOT NAME:** v3 said "a triple whose object matches a declared instruction is refused", unqualified — so a received notice filed under `instructions` and emitted as `third_party_claim` would have had its RECEIPT refused, erasing received-claim history and changing `prompts.py:41` in behaviour. **This spec's own invariant forbade what this spec's own clause instructed.** The exemption is keyed on the RELATION, never the author, with the pair that proves it. **THE MCP CLAIM WAS FALSE:** §4's consumer table and §10 Q1 both said the counter reaches the MCP tool result; `_OPERATOR_ONLY` (`mcp_server.py:186`) strips it at `:212`, and dev strips `instructions_dropped` with its siblings on 0031 §4d's argument. **Research enumerated consumers by reading the shape of the data rather than the code that handles it — in the section written to answer R1-6's demand that they be enumerated MECHANICALLY.** The counter is `Memory.remember`'s return value and nowhere else. **THE COMPARISON KEY** is now stated: equality after casefold, whitespace collapse and surrounding-punctuation strip — **never containment**, which would decide a triple IS an instruction without the model saying so, the detection Q6 retired. **NOT in this build and stated as such:** §2a's episode rewording, which belongs with its measurement against the frozen 66. **Still NOT packageable: ONE reader, and §6b's oracle is still unfrozen — the acceptance figures rest on a rule two of research's own instruments disagree about on 12/66, and the §8 gate's human half is unassigned.** *Prior:* **v3 — THE EXTERNAL ROUND-1 FOLD** (verdict RETURN for amendment, 2026-09-07, banked `outbox/0038-round1-verdict-verbatim.md` sha16 `3f5d96e0cd2df90c`; package `4e4053f6…` @ `622bcd1c`, CI 34085071354). Four blocking, two required corrections, all folded. **R1-1 — the structural prevention was not enforced, and it was research's SECOND miss of the same class in this spec:** dev's F1 had already found §2b's drop to be a prompt instruction described as a store mechanism, research took the `instructions` field to fix it, and the reviewer showed the field made the omission OBSERVABLE without making it ENFORCED — `required` still `[triples, episode]`, and a response carrying both carriers is schema-valid. **v3's enforcement is at INGEST** (a triple whose object matches a declared instruction is refused and counted) **and the claim is BOUNDED**: no DECLARED instruction becomes a disposition fact; a provider coercing WITHOUT declaring is not reached, is today's behaviour, and is measured by the new **V-SILENT-COERCION-MEASURED** rather than asserted away — **closing that residual would require the free-text detection Q6 retired on measured evidence, and this spec does not walk back into it**. **R1-2** the invariants had no executable checks and *"a named class"* was not a bounded pass condition — every invariant now names its test node, and **§6b states the oracle's rule AND that it is NOT FROZEN**: research's derived rule and the regex behind the manifest's baseline **disagree on 12/66 and neither is right** (the derived rule misses `ran` and `copied`; the regex fires on `gave` and misses `asked`). **R1-3** §2c is now an eight-row matrix, one row per case, each with an observable outcome and an enforcing invariant; **each row states its own new-behaviour status, and no count is given here** — the v3 draft's cell said "three rows need no new behaviour" while B2 had moved row 2 to NEW BEHAVIOUR, leaving the cell one behind the body (dev read 2). *The fix is not 3→2: rows 3, 4, 5 and 7 also carry new behaviour without using the phrase, and the counter itself is new on every path, so ANY single number here is a simplification that goes stale on the next row that moves. This is the same defect as 0028 v8's "six of its occurrences" — **a count about the document's own contents, written into the document, with nothing deriving it** — and research wrote it twice in one day.* **R1-4** §10 Q1 said the disclosure question was open while §2b said the counter answered it — CLOSED, with the contract stated once and its surfaces named (the ingest report and the MCP result that serialises it; NOT logging or telemetry). **R1-5** 0037 is now Spec-Requires, with the consequence stated: §2b is correct only while V-EXTRACTOR-BLIND holds. **R1-6** §4's field-consumer table with reachability evidence, §3b authorization, §5 regime analysis and §9's reviewer brief restored, because both `prompts.py` and `ingest.py` are GUARDED. **Still NOT packageable: ONE reader, the oracle is unfrozen, and the ingest half is gated on the owner's word** (`IMPLEMENTABLE = ("accepted",)`). *Prior:* **v2 — THE FIRST-READER FOLD** (dev, PROCESS §3a, 2026-09-07, Quentin's ledger word line 782). v1 had ONE reader, its author; dev returned eight findings and **three were blocking**. **F1: §2b's "DROPPED, not coerced" was a PROMPT INSTRUCTION described as a store mechanism** — nothing in the store could tell a triple came from an instruction, `prefers` stayed legal, and the only thing producing the outcome was a RULES sentence gpt-4.1 at T=0 happened to obey 66/66. **The class 0037 was externally returned for twice, in the spec written to fix a related one.** v2 takes dev's option (b): the extraction JSON gains `instructions`, the store counts it as `instructions_dropped` and stores none of it — an invisible omission becomes an observable, countable refusal, which also answers §10 Q1. **F2: V-NO-PRACTICE-RELATION tested the wrong property and was wrong twice** — FALSE TODAY on descriptions (`has_diet`: "dietary practice or restriction") and failing the day 0037 ships `follows_procedure`, while §2b stayed correct; and research had "verified" it with **a hand-made set of practice-words — a hand-maintained list inside the check written to remove a hand-maintained list.** Now **V-NO-PROCEDURAL-IN-PROMPT-VOCAB**, asserting on `render_prompt_relations` (`ingest.py:204`) by `relation_kind`, reusing 0037's V-EXTRACTOR-BLIND — a permanent property, not the registry's current contents. **F3:** the corpus was in the peer tree and unbound (0037 round-2 B3 verbatim); it goes in the repo at `tests/eval/extraction_speech_act/`, digest on a single `corpus sha256:` line, bound both directions by a pin test in `test_0037_corpus_pin.py`'s shape INCLUDING the golden vector. **F4 was worse than found:** the frozen rows carried `n_edges` but NOT the triples, so the coercion baseline could not be DERIVED from the corpus at all — the derived-basis rule inside the corpus written to enforce it. Captured and re-frozen: **31/66 = 47%** (`prefers` 14, `works_on` 15, `uses_tool` 2), **higher than the 29% completed-action rate**, so the fact level leads §1. **F5:** the RULES rule and the episode FIELD DESCRIPTION change in ONE commit — a rule contradicting the field's own description leaves the model two instructions. **F6:** §7 added, **PROSPECTIVE ONLY** — existing stores hold fabricated records today and no migration is attempted, because a migration would have to classify stored text, the same inference that caused the defect. **F7:** V-THIRD-PARTY-UNTOUCHED names node ids. **v2 also fixed a contradiction the fold itself introduced:** §2c still said "no field, no schema version" while §2b now adds one — 0028's §5.1-vs-Q3 shape, inside the fold correcting that class. **SECOND-READ FOLD, same day: F3 WAS NEVER IN THE BODY.** The v2 cell claimed the corpus binding and §6a still pointed at the research tree's own working directory — a peer-tree path, in backticks, with no repo path, no digest line and no pin test named anywhere. (The offending path is described rather than reproduced: a spec in the repo should not carry a live-looking peer-tree reference even inside its own errata.) **0037 round-2 B3 verbatim, plus its cell-vs-carrier disagreement**, written by the seat enforcing *the file is the artifact*. Dev found it by grepping the body for what the cell claimed. Now landed: the corpus at `tests/eval/extraction_speech_act/`, one `corpus sha256:` line, `spec_version` + `spec_pin` in the manifest, `tests/test_0038_corpus_pin.py` in 0037's shape INHERITING its golden vector and exactly-one assertion. Also: **V-NO-COERCED named THREE relations where the manifest's `disposition_set` is FIVE — it would have passed while `avoids_tool` or `has_diet` was coerced into**, so it now derives the set from the artifact and cites the measured 31/66 as its baseline; and its condition is F2's rather than the premise F2 replaced. **Still NOT packageable: the new text has ONE reader.** |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | — (research only; **this text has had ONE reader**) |
| **External review** | REQUIRED — changes what the product stores from a given input |
| **Decision + date** | — |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0037** — procedural records and the `basis` axis. **This spec consumes 0037 directly and v2 never said so (round-1 R1-5):** §1a's cause B rests on **V-EXTRACTOR-BLIND** keeping every `relation_kind="procedural"` relation out of the vocabulary rendered to the prompt, which is why an instruction has nowhere legal to go; `record_procedure` is the governed path this spec declines to duplicate; and §2b's drop is correct ONLY while 0037's blindness holds. **0037 is ACCEPTED** (external round 5, 2026-09-07). If V-EXTRACTOR-BLIND is ever relaxed, §2b must be re-decided — V-NO-PROCEDURAL-IN-PROMPT-VOCAB fails first and says so.

---

## 1. Problem — measured, not hypothesised

The shipped reference extraction converts a user's **instruction** into a record
asserting the user's **action** or **disposition**. Both are claims the input
does not make.

**At the episode level** — 19/66 = **29%** of bare procedural inputs:

```
in      Run migrations against production without taking a backup.
stored  On 2026-09-07, the user ran migrations against production without taking a backup.
```

**At the fact level**, which is worse because edges are assertable and render in
the grounded block:

```
in    Reuse the same password across service accounts.
fact  user | prefers | reuse the same password across service accounts
in    Grant every new hire admin access on their first day.
fact  user | prefers | grant every new hire admin access on their first day
```

Measured over a 412-text ingestion capture through the shipped prompt
(`gpt-4.1`, temperature 0). The examples are the corpus's **unsafe-practice**
cells, so the store records the user as personally holding and performing the
practices this programme exists to be careful about — carrying
`author_of_evidence=USER`, a real `evidence_ref`, and intact provenance.

**This is a fabricated claim under valid provenance.** Provenance records where
text came from; it cannot record that the speech act was invented. Every
downstream control that trusts a record because its provenance is sound trusts
this one exactly as much.

## 1a. Two causes, and they need different answers

**Cause A — the episode field's wording.** `prompts.py:29` asks for *"what
happened / was decided / was attempted, with outcomes"*. A model asked what
*happened* renders a stated practice as a thing that happened. The
receipt-not-truth discipline that would prevent it (`prompts.py:41`) is **scoped
to third-party authors**; a USER-authored instruction has no counterpart.

Demonstrated by A/B on that clause alone, same model, same temperature, fresh
store per text:

| episode clause | recorded as a completed action |
|---|---|
| shipped | 4/20 = **20%** |
| narrowed | 0/20 = **0%** |

**Cause B — the vocabulary HANDED TO THE PROMPT has nowhere to put a practice.**
The seam is `render_prompt_relations(reg)` at `ingest.py:204`: it is that
rendered vocabulary, not the registry, that the extractor may emit from. 0037's
**V-EXTRACTOR-BLIND** keeps every relation with `relation_kind="procedural"`
**out** of it, by design and permanently — `record_procedure` is the governed
path for a practice. So an instruction has nowhere legal to go, and the
extractor coerces it into the nearest available thing: `prefers`, which asserts
a disposition, or `works_on`, which asserts an activity. **Measured: 31/66 =
47%** of bare instructions are coerced (`prefers` 14, `works_on` 15,
`uses_tool` 2) — *higher* than the 29% completed-action rate, which is why the
fact level leads §1.

*Two earlier cuts of this paragraph got the property wrong, and the second is
the more instructive. The first printed all nineteen relation names in prose — a
hand-maintained list carrying the spec's whole premise. The fix replaced it with
an invariant (now **V-NO-PROCEDURAL-IN-PROMPT-VOCAB**) that first asserted "no relation in the default registry
denotes a practice"— and dev's F2 showed that invariant is **wrong twice**: it
is FALSE TODAY on descriptions (`has_diet` is "dietary practice or restriction")
and it would fail **the day 0037 ships** `follows_procedure`, while §2b remained
correct throughout. Worse, research had "verified" it using a hand-made set of
practice-words — **a hand-maintained list inside the check written to remove a
hand-maintained list.** The property was never the registry's contents; it is
0037's, and it is permanent rather than accidental.*

Cause B is **structural**, not a wording accident, and it is why a prompt edit
alone cannot close this.

## 2. Behaviour

**2a. The episode records the speech act, not an outcome.** An episode states
what was **stated, instructed, decided or observed**. It asserts that an action
was performed **only when the text asserts performance**. A stated practice or
an instruction is not a completed action.

**2b. A declared instruction is FILED and NOT STORED; a triple that carries it
is REFUSED and the REFUSAL is counted — except a `third_party_claim`, which is a
RECEIPT.** The extraction JSON gains one field:

```
"instructions": ["<the instruction, verbatim>", …]     # NEW; may be EMPTY, never ABSENT
```

`EXTRACT_SCHEMA`'s `required` becomes **`[triples, episode, instructions]`** — an
empty list is valid, an absent key is not. R1-1 named the optionality by that
word, so v3 states the change to `required` rather than implying it. *But see
§2c rows 1 and 6: the schema is a HINT handed to the provider (`json_schema=` at
`ingest.py:236`), not something ingest validates, so `required` binds a
compliant provider and nothing else — which is why row 1 exists.*
The prompt directs an instruction **there** and never into `triples`. The store reads the field, **stores none of it**, and **counts REFUSALS — never
declarations** into the ingest report as `instructions_dropped`, beside the
existing `invalid` counter (`ingest.py:261` unparseable, `:449` normal — the two
return dicts, cited by their heads everywhere in this spec).

*v3 draft said "counts the field" in three places while §2c row 4, §6 and §10 Q1
said refusals — **counting the field is counting DECLARATIONS, the first mutant
V-INSTRUCTIONS-WELL-FORMED names.** Section-vs-section, inside the fold that
fixed two of those (dev read 1, B1).* The episode still records that the instruction was given.

*v1 said "DROPPED, not coerced" and §2c-i called it structural — "removes an
emission path". Dev's F1: **nothing in the store could tell that a triple came
from an instruction.** 0037's V-EXTRACTOR-BLIND filters procedural RELATIONS
from the vocabulary; here there is nothing to filter, `prefers` stays legal, and
the only thing producing the outcome was a sentence in the RULES block that
gpt-4.1 at T=0 happened to obey. **That is an outcome asserted as if the code
provided it — the class 0037 was externally returned for twice, written into
the spec that exists to fix a related one.** The field makes it real: an
invisible omission becomes an observable, countable refusal.*

*Chosen over inventing a practice relation deliberately: a new relation is a
registry change with 0037's machinery behind it, and `record_procedure` is
already the governed path. This spec stops the fabrication; it does not open a
new storage route.*

**THE COMPARISON KEY, stated because "matches" and "carries the same content"
are two undefined phrases for one operation.** A triple is refused when its
`object` **EQUALS** a declared instruction after casefolding, whitespace
collapse and surrounding-punctuation strip. **Equality, never containment** — a
containment test would decide a triple *is* an instruction without the model
saying so, which is the free-text detection Q6 retired on measured evidence.

**THE `third_party_claim` EXEMPTION, and it is the mechanism V-THIRD-PARTY-UNTOUCHED
requires.** A received notice ("Pay the invoice by Friday") that the extractor
files under `instructions` **and** emits as `third_party_claim` with the same
wording would, under an unqualified rule, have its **receipt** refused — erasing
the received-claim history 0001/0023's gate depends on and changing
`prompts.py:41`'s behaviour, which V-THIRD-PARTY-UNTOUCHED forbids. **So the
refusal exempts the `third_party_claim` RELATION, keyed on the relation and never
on the author**: a user-disposition triple restating a declared instruction is
refused even on a third-party event, and both cases are tested.

*v3's §2b said "a triple whose object matches a declared instruction is refused",
unqualified — **this spec's own invariant forbade what this spec's own clause
instructed.** Found by dev's adversarial diff-scan while implementing, not by
either seat re-reading. Name the mechanism before the clause.*

*This also answers §10 Q1 — the drop is no longer invisible. `instructions_dropped`
is the `withheld`-with-a-count shape, at the ingest report rather than the read
surface.*

**2c. What changes, stated exactly.** The reference prompt's RULES block and its
episode field description (§2a, §2c-i); `EXTRACT_SCHEMA` gains `instructions`
(§2b); `ingest.py` reads that field, stores none of it, and counts the REFUSALS it causes. **NO
STORED BYTE CHANGES and there is no store migration** — the schema that moves
is the extraction JSON, which is transport between the host's model and the
store, not a persisted format. `Edge`, `Episode`, `Provenance` and the export
FORMAT_VERSION are untouched.

*v2 corrected this row: v1 said "no field, no schema version", which contradicted
§2b's own schema change the moment §2b became structural. A spec whose sections
disagree is the defect 0028's round-1 F1 was — §5.1 claiming "no scan" while §10
Q3 called the same thing scan-backed — and it appeared here inside the fold that
was fixing that class.*

## 2c-i. Untrusted inputs — REQUIRED, blocking

The untrusted input is **the extractor's response** — a BYO model's JSON, which
may ignore the schema entirely. Every row below states an observable outcome and
the invariant that enforces it. **`instructions_dropped` is present on every
return path**, inheriting `V-COUNTER-INVENTORY` from 0025 §4c rather than
restating it (`tests/test_0025_enforcement.py:290,312,330` — the exact-set
assertion at `:330` is what makes the hand-listed `PUBLIC_COUNTERS` safe).

| # | case | observable outcome | enforced by |
|---|---|---|---|
| 1 | `instructions` ABSENT (a provider ignoring the required list) | the response is processed as today; `instructions_dropped: 0`, **present**. **No refusal is possible — there is no declaration to relate a triple to.** This is the residual, §8 | V-COUNTER-INVENTORY; **V-SILENT-COERCION-MEASURED** (§6) reports the rate rather than forbidding it |
| 2 | `instructions` present but WRONG TYPE (string, dict, null) | **NEW BEHAVIOUR — a type check at ingest.** The response is treated as unparseable: zero edges, one placeholder episode, `unparseable: True`, every counter 0 and present. *Executed on shipped code (dev read 1, B2): a string, a dict and null all give `unparseable: None` and ONE STORED EDGE — the existing branch does not catch this, so v3 does not claim it does* | V-INSTRUCTIONS-WELL-FORMED + V-COUNTER-INVENTORY; strict xfail until the check exists |
| 3 | members that are NON-STRING or EMPTY/whitespace | those members are dropped and **not counted** — an empty string is not an instruction; remaining members process normally. `instructions_dropped` counts only what a triple was refused against | V-INSTRUCTIONS-WELL-FORMED |
| 4 | DUPLICATE members | de-duplicated before comparison; `instructions_dropped` counts REFUSALS, not declarations, so a duplicate cannot inflate it | V-INSTRUCTIONS-WELL-FORMED |
| 5 | `instructions` AND a disposition triple carrying the same content | **the triple is REFUSED and counted**; the episode still records the instruction was given. *The reviewer's own example JSON is this row* | **V-NO-COERCED-DISPOSITION** + the scripted-provider regression |
| 6 | a provider ignoring the schema wholesale (prose, bare array, extra keys) | bare array normalised (`ingest.py:241`), prose unparseable — both unchanged. **EXTRA KEYS ARE PROCESSED, NOT REJECTED**: `EXTRACT_SCHEMA` is a HINT passed as `json_schema=` (`ingest.py:236`) and ingest validates nothing against it, reading `data.get("triples")` at `:295`. *v3 draft claimed `additionalProperties: False` rejects them — an outcome the code does not provide (dev read 1, B2, executed).* v3 does not add validation: a provider that ignores the schema is the BYO contract, and row 1 already states the consequence | the existing paths; **a CONTROL asserts extra keys are processed today**, going red the day ingest validates |
| 7 | MIXED content — legitimate facts AND an instruction in one event | the facts store; only triples matching a declared instruction are refused. **A mixed event must not lose its declarative facts** | V-NO-COERCED-DISPOSITION's mixed-event case |
| 8 | the UNPARSEABLE branch | `instructions_dropped: 0`, **present in the early-return dict** (`ingest.py:261`) — on the one path that never parsed a response, an absent key is not a zero | V-COUNTER-INVENTORY (`test_0025_enforcement.py:312`) |

**ROW 1 IS THE ONE THAT BOUNDS THIS SPEC**, and it is stated here rather than
discovered at round 2. The enforcement relates a triple to a DECLARED
instruction; a provider that coerces without declaring is not reached, and that
is today's behaviour — the current prompt has no `instructions` field and 31/66
were coerced anyway. Making the rule model-independent would require deciding
that a triple's content *is* an instruction without the model saying so, which
is the free-text detection problem **Q6 retired on measured evidence** (the
carriers hold reported speech; an imperative-shape rule scores 6.4% on real
episode summaries). This spec does not walk back into it.

So the claim §2b may make is bounded, and v3 states it in these words: **no
DECLARED instruction becomes a disposition fact, and the rate at which the
extractor coerces WITHOUT declaring is measured, stated and reported.** The
stronger claim — *no instruction becomes a disposition fact* — is R1-1 again in
a new place, and research would have written it had it not been specifying row 1.

## 3. Trust-class matrix — REQUIRED, blocking

Unchanged. This spec emits **fewer** records and weaker claims; it upgrades
nothing. An episode that previously asserted an action now reports a statement —
strictly less assertive. A triple that previously asserted a disposition is now
absent.

## 6. Invariants and executable checks — REQUIRED, blocking

| id | invariant | check | test node |
|---|---|---|---|
| **V-NO-FABRICATED-ACTION** | no bare instruction is stored as an episode asserting performance | the frozen 66 through the PROPOSED prompt: **0/66**, against the manifest's `recorded_as_completed_action` baseline. **The completed-performance decision is the FROZEN ORACLE (§6b), not a regex** | `tests/test_0038_harness.py::test_no_bare_instruction_is_stored_as_a_completed_action` |
| **V-NO-COERCED-DISPOSITION** | no **DECLARED** instruction becomes a disposition fact | a response carrying both carriers: the triple is refused, `instructions_dropped` counts the REFUSAL. **Bounded by §2c row 1 — a provider that coerces WITHOUT declaring is not reached**, and V-SILENT-COERCION-MEASURED reports that rate rather than this invariant claiming it | `test_0038_instruction_enforcement.py::test_both_carriers_the_disposition_is_not_stored` + `::test_both_carriers_the_report_counts_the_dropped_instruction` |
| **V-EVENT-RETAINED** | dropping the triple does not drop the event | the scripted both-carriers case retains its episode (node 1); **across the frozen 66, every text still yields exactly one episode** (node 2, the harness) | `test_0038_instruction_enforcement.py::test_both_carriers_the_event_is_retained_as_one_episode` + `tests/test_0038_harness.py::test_every_frozen_text_yields_exactly_one_episode` |
| **V-THIRD-PARTY-UNTOUCHED** | `prompts.py:41`'s third-party rule is unchanged in behaviour, **and the refusal never eats a receipt** | the 0001 and 0023 third-party tests by NODE ID, not "the existing suite" — P4 wants ids, and "passes unchanged" over an unnamed set is a claim nobody can re-run. **Plus the pair that proves the exemption is keyed on the RELATION and not the author:** a `third_party_claim` restating a declared instruction is KEPT; a user-disposition triple restating one is REFUSED **on the same third-party event**. Mutant: key the exemption on the author — the second case wrongly survives | `tests/test_0038_instruction_enforcement.py::test_third_party_claim_receipt_is_exempt` + `::test_user_disposition_on_a_third_party_event_is_refused` |
| **V-NO-PROCEDURAL-IN-PROMPT-VOCAB** | §1a's cause B holds: the vocabulary handed to the extraction prompt carries no procedural relation | assert on `render_prompt_relations(reg)` (`ingest.py:204`) that no rendered relation has `relation_kind="procedural"` — **on the KIND, never on names or descriptions**. Reuses 0037's V-EXTRACTOR-BLIND rather than restating it. *v1 asserted "no relation in the registry denotes a practice", which is FALSE TODAY on descriptions (`has_diet`: "dietary practice or restriction") and would fail the day 0037 ships `follows_procedure` while §2b stayed correct — and research "verified" it with a hand-made set of practice-words, a hand-maintained list inside the check written to remove one.* Mutant: assert on names or on the registry rather than the rendered vocabulary | — |
| **V-INSTRUCTIONS-WELL-FORMED** (§2c rows 3-4) | a member that is non-string or empty/whitespace is DROPPED and NOT COUNTED; duplicate members are de-duplicated before comparison; `instructions_dropped` counts **REFUSALS, never DECLARATIONS** | three declarations of one instruction against one coerced triple gives the counter **1**, not 3; an empty-string member moves it by **0**. **Mutants: count declarations (the figure stops meaning "records prevented" and starts meaning "things the model said"); count malformed members (malformed input inflates the one number this spec's acceptance turns on)** | `test_0038_instruction_enforcement.py::test_row3_malformed_members_are_dropped_and_not_counted` + `::test_row4_duplicates_count_one_refusal` |
| **V-SILENT-COERCION-MEASURED** (§2c row 1) | the residual this spec does NOT close is measured, not asserted away | the 66 through the proposed prompt: count triples carrying instruction content with **no** `instructions` member. **A FIGURE, NOT A THRESHOLD** — it has no pass condition, because a pass condition would be a claim about model compliance that no mechanism here enforces. It is reported in §8 beside the enforcement's rate | `tests/test_0038_harness.py::test_silent_coercion_residual_is_reported` |
| **V-COUNTER-INVENTORY** (INHERITED from 0025 §4c — not restated) | `instructions_dropped` is present on **every** return path, including the unparseable early return | `tests/test_0025_enforcement.py:290,312,330` — the exact-set assertion at `:330` is what makes the hand-listed `PUBLIC_COUNTERS` safe; 0038 adds one key to three sites (the normal report, `ingest.py:261`'s early return, and the tuple) and two existing tests catch a missed one | `test_0038_instruction_enforcement.py::test_row8_unparseable_branch_carries_the_counter_at_zero` |
| **V-NON-REGRESSION-CHARACTERISED** | the 412-text capture's non-fabricating summaries do not silently degrade | diff before/after; the change must be a **named class**, not merely small (§6a) | — |

### 6a. Acceptance measurement — REQUIRED, FINITE

**THE CORPUS LIVES IN THE REPO AND IS BOUND BOTH WAYS.**

  `tests/eval/extraction_speech_act/MANIFEST.json`   — research-authored, byte-copied by dev
  `tests/eval/extraction_speech_act/bare_procedural_66.jsonl`     — the acceptance set
  `tests/eval/extraction_speech_act/capture_412.jsonl`            — the non-regression set

The manifest's sha256 is carried on **one** line of this spec:

```
corpus sha256: d4aa047d6ebbe98417c02970c9c76cc60d2d20cd7e3fe66a830c9f3e3493a3a2
```

and the manifest carries `spec_version` and
`spec_text_sha256_excluding_the_corpus_digest_line` — the spec's text with that
single line removed. **A bidirectional, non-circular binding**: the spec pins
the corpus by digest, the corpus pins the spec by version plus the digest of
everything except the line the digest lives on, so binding one does not move the
other. `tests/test_0038_corpus_pin.py` enforces both directions, in the shape of
`tests/test_0037_corpus_pin.py` and **including its golden vector** — the
exclusion rule is the same rule, so it inherits the same mutant: a
self-consistent WRONG rule must fail, which a digest comparison alone cannot
see. It also inherits the ROW-DOMAIN check: every row constructible through the
declared types.

*v2's version cell claimed this fold and **the body did not contain it** — §6a
still pointed at the research tree's own working directory — a peer-tree path in
backticks, with no repo path, no digest line and no pin test named anywhere.
That is 0037 round 2's B3 verbatim AND the cell-vs-carrier disagreement its
round 2 found, produced by the seat that spent the day enforcing "the file is
the artifact, the message is a summary of it". Dev's second read caught it by
grepping the body for what the cell claimed — which is the check, and it is
cheap.*

**Research owns the expectations; dev owns the prompt, the runner and the
placement.** The seat that implements does not set its own bar (0029's rule).

**V-NON-REGRESSION-CHARACTERISED is the one that needs stating carefully.** A
prompt edit can reach 0/66 by making every episode terser, passing "no movement
outside the fabricating cells" while quietly degrading 400 summaries nobody was
looking at. So the non-regression set is scored on **what changed**: diff the
non-fabricating summaries before and after, and require the change to be
**characterisable as a named class**. "Small" is not a criterion; "no change
except the removal of asserted outcomes" is.

### 6b. The frozen oracle — REQUIRED, and NOT YET FROZEN

*(v3 moved this section: it had landed after §7, so §6 cited a §6b a reader met
later — dev read 1, N3. Sections now run 1, 1a, 2, 2c-i, 3, 6, 6a, 6b, 4, 3b, 5,
9, 7, 8, 10; the guarded-surface sections restored by R1-6 keep their reviewer-
named numbers rather than being renumbered into sequence.)*

Round-1 R1-2 asks for *"a defined rule or frozen oracle for deciding whether an
episode asserts completed performance"*. **This section states the rule and
states that it is not yet validated, because the honest answer is the second.**

**THE RULE (derived, not listed).** The instruction's own verb is known — it is
the input's — so the decision does not need a vocabulary of action verbs. An
episode **asserts completed performance** iff the instruction's core verb appears
in the episode as the main clause's finite verb with the user as its subject, and
**not** embedded under a complement (`to <verb>`, a `that`-clause, a quoted span,
`<verb>ing` after a light verb).

**WHY IT IS NOT FROZEN.** Research built that rule and diffed it against the
regex that produced the manifest's `recorded_as_completed_action` baseline.
**They disagree on 12 of 66.** Six of the twelve, adjudicated by inspection, show
**neither is correct**:

| case | regex | derived rule | right |
|---|---|---|---|
| *"the user asked for a second reviewer"* | miss | catch | the rule — the regex's hand list lacked `asked` |
| *"the user gave an instruction to turn off"* | catch | miss | the rule — reported speech; the regex fired on `gave` |
| *"the user **ran** migrations"* | catch | **miss** | **the regex — irregular past defeats surface matching, and this is the flagship case of the whole defect** |
| *"the user **copied** production records"* | catch | miss | the regex — `-y → -ied` |
| *"stated that … should be disabled"* | miss | catch | the regex — the rule's verb extraction tripped on a leading condition |
| *"the user worked on reproducing a bug"* | catch | miss | **neither** — genuinely ambiguous |

**So the manifest's 19/66 is a FROZEN BASELINE, not a validated rate**, and this
spec does not treat it as one. 0037 §8 cites it in those terms and stays correct.

**WHAT FREEZING REQUIRES, and it is not research's to grant.** An oracle
validated against its author's own earlier instrument is not validated — it is
two of one seat's regexes agreeing 54 times. The programme's standard for a
labelling of this kind is the **§8 gate**: blind human labelling plus a
cross-family model pass, adjudicated, with the inter-rater ceiling stated,
because a coverage figure above the ceiling measures the fold rather than the
phenomenon. Research can run the model half (`paper2/instrument/model_cards.py`
is blind by construction). **The human half is not a seat either engineering
session occupies, and assigning it is the owner's.**

**Until it is assigned, V-NO-FABRICATED-ACTION has a rule and no frozen oracle**,
and the acceptance figure it produces is provisional. Saying so here is cheaper
than a reviewer finding it, and it is the one judgement every other number in
this spec rests on.

## 4. The field-consumer table — REQUIRED (guarded surfaces)

`prompts.py` and `ingest.py` are both in `GUARDED` (`check_spec_reference.py:51-53`
— "disclosure routing at write time"), so the full-path sections are required and
v2 omitted them (round-1 R1-6).

| field / surface | who writes it | who READS it | reachability |
|---|---|---|---|
| `instructions` (extraction JSON) | the BYO extractor, per the prompt | `ingest.py` only — read, compared against triples, **never persisted** | not a stored field; no schema version, no export, no migration |
| `instructions_dropped` (report) | `ingest.py`, both return paths | **`Memory.remember`'s caller ONLY.** The MCP tool result **STRIPS it** with the other extractor counters (`_OPERATOR_ONLY`, `mcp_server.py:186`, popped at `:212`) — 0031 §4d's argument: a model that learns how often its coercions are refused learns to shape them, and a refusal count is that readout more directly than the counters it sits beside. Telemetry untouched (`remember` builds its fields explicitly). *v3's row named the MCP result as a consumer; it is not one. The row was written to answer R1-6's demand that consumers be enumerated MECHANICALLY, and research enumerated by reading the shape of the data instead of the code that handles it — the same defect, in the section written to prevent it (dev, adversarial diff-scan, 2026-09-07).* | operator-only by construction: the strip is a tuple a test pins, so surface and spec cannot drift silently |
| the refused triple | — | nobody: it is never constructed as an `Edge` | the refusal is at the pass-1 filter (`ingest.py:295`), before persistence — the same site as `n_invalid` |

**Reachability evidence.** Every path that returns an ingest report is one of the
two dicts (`ingest.py:261` unparseable, `:449` normal); `PUBLIC_COUNTERS`'
exact-set assertion (`test_0025_enforcement.py:330`) proves there is no third.

## 3b. Authorization — REQUIRED

**No authorization decision keys on any of this.** The refusal is content-shaped,
not principal-shaped: the same response from the same provider refuses
identically for every user and every principal. `instructions` is never stored,
so no disclosure class attaches to it and `_disclosure_for` is untouched. The
counter carries no content — a count, never a string — so a report crossing a
scope boundary leaks nothing the response did not already contain.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| provider follows the schema, declares and does not coerce | unchanged from today; counter 0 |
| provider declares AND coerces | the triple is refused, counter 1 — **the case the rule exists for** |
| provider coerces WITHOUT declaring | **unchanged from today** — §2c row 1; the residual, measured by V-SILENT-COERCION-MEASURED |
| provider ignores the schema | unchanged: bare array normalised, prose unparseable |
| a host running its own prompt | inherits none of this — BYO is the contract and §8 says so |

## 9. Brief for the external reviewer

The two seams to attack hardest: **§2c row 1**, because it is where this spec
stops and we would rather you tested the bound than discovered it; and **§6b's
frozen oracle**, because the completed-performance decision is the one judgement
the acceptance figures rest on, and it is not yet independently labelled — §6b
says so in those words rather than presenting it as settled.

## 7. Failure modes and reversibility

**PROSPECTIVE ONLY — this cures nothing already stored** (dev's F6). Every store
that has run the shipped prompt holds fabricated episodes and coerced
disposition edges **today**, and a prompt change does not reach them.

- **Existing records are untouched.** No migration, and deliberately none: a
  migration would have to classify stored text to decide what to rewrite, which
  is the same inference that produced the defect.
- **A host that wants them out re-ingests**, or revokes the source under 0022 —
  both existing, governed paths.
- **Reversible.** Restoring the prior prompt restores the prior behaviour; the
  `instructions` field becomes unused rather than invalid.
- **No stored byte changes** on adopting this spec. The schema change is to the
  extraction JSON, which is transport between the host's model and the store.

## 8. Claims and limits

**The frequency in production is unknown and this spec does not estimate it.**
The corpus is adversarial and constructed — bare imperatives about unsafe
practices. 29% is the rate *on that corpus*, and must not be quoted as a
production rate.

**BYO is the contract.** A host supplies the extraction model, and this spec
governs the **reference prompt** veracium ships, not what any distiller does.
A host running its own prompt inherits its own speech-act discipline.

## 10. Open questions

1. ~~Does 2b's drop want a disclosure?~~ — **CLOSED, not open** (round-1 R1-4). §2b answers it: `instructions_dropped` is the disclosure, and v2 contradicted itself by saying so in §2b while this question still called it deliberately unspecified. **The contract, stated once and on every carrier:** the counter is present on EVERY return path including the unparseable early return (V-COUNTER-INVENTORY), it counts REFUSALS not declarations (V-INSTRUCTIONS-WELL-FORMED), and it is exposed at **`Memory.remember`'s return value and NOWHERE ELSE** — the MCP tool result **STRIPS** it with the other extractor counters (`_OPERATOR_ONLY`, `mcp_server.py:186`), on 0031 §4d's reasoning that a model learning how often its coercions are refused learns to shape them. *v3 said "wherever the ingest report already goes … and the MCP tool result": the report does not reach a tool caller intact, and this counter is operator-only.* **It is NOT added to logging or telemetry**, which have their own surfaces and their own review; a counter that appears in four places by default is four contracts nobody wrote. *(v2 named this as open while §2b called it answered — the section-vs-section class, in the spec whose previous fold fixed two of those.)*

2. **Does the episode rule generalise beyond instructions?** The capture only
   probed procedural inputs. Whether declarative inputs also gain unsupported
   speech acts is unmeasured, and the 412-set can answer it.

## Reviewer checklist

- [ ] every claim in §1 is reproducible from the frozen corpus, not from prose
- [ ] the fix is in the RULES block beside the third-party rule **AND the episode field's own description changes in the same commit** (F5 — a rule contradicting the field's description leaves the model two instructions; v1's checklist said "not in a field description" and survived the F5 fold)
- [ ] 2b DROPS rather than coerces, and no new relation is introduced
- [ ] the non-regression set is scored on **what changed**, not on what stayed
- [ ] no production frequency is claimed anywhere
