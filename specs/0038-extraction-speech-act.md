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
| **Version** | **v2 — THE FIRST-READER FOLD** (dev, PROCESS §3a, 2026-09-07, Quentin's ledger word line 782). v1 had ONE reader, its author; dev returned eight findings and **three were blocking**. **F1: §2b's "DROPPED, not coerced" was a PROMPT INSTRUCTION described as a store mechanism** — nothing in the store could tell a triple came from an instruction, `prefers` stayed legal, and the only thing producing the outcome was a RULES sentence gpt-4.1 at T=0 happened to obey 66/66. **The class 0037 was externally returned for twice, in the spec written to fix a related one.** v2 takes dev's option (b): the extraction JSON gains `instructions`, the store counts it as `instructions_dropped` and stores none of it — an invisible omission becomes an observable, countable refusal, which also answers §10 Q1. **F2: V-NO-PRACTICE-RELATION tested the wrong property and was wrong twice** — FALSE TODAY on descriptions (`has_diet`: "dietary practice or restriction") and failing the day 0037 ships `follows_procedure`, while §2b stayed correct; and research had "verified" it with **a hand-made set of practice-words — a hand-maintained list inside the check written to remove a hand-maintained list.** Now **V-NO-PROCEDURAL-IN-PROMPT-VOCAB**, asserting on `render_prompt_relations` (`ingest.py:204`) by `relation_kind`, reusing 0037's V-EXTRACTOR-BLIND — a permanent property, not the registry's current contents. **F3:** the corpus was in the peer tree and unbound (0037 round-2 B3 verbatim); it goes in the repo at `tests/eval/extraction_speech_act/`, digest on a single `corpus sha256:` line, bound both directions by a pin test in `test_0037_corpus_pin.py`'s shape INCLUDING the golden vector. **F4 was worse than found:** the frozen rows carried `n_edges` but NOT the triples, so the coercion baseline could not be DERIVED from the corpus at all — the derived-basis rule inside the corpus written to enforce it. Captured and re-frozen: **31/66 = 47%** (`prefers` 14, `works_on` 15, `uses_tool` 2), **higher than the 29% completed-action rate**, so the fact level leads §1. **F5:** the RULES rule and the episode FIELD DESCRIPTION change in ONE commit — a rule contradicting the field's own description leaves the model two instructions. **F6:** §7 added, **PROSPECTIVE ONLY** — existing stores hold fabricated records today and no migration is attempted, because a migration would have to classify stored text, the same inference that caused the defect. **F7:** V-THIRD-PARTY-UNTOUCHED names node ids. **v2 also fixed a contradiction the fold itself introduced:** §2c still said "no field, no schema version" while §2b now adds one — 0028's §5.1-vs-Q3 shape, inside the fold correcting that class. **SECOND-READ FOLD, same day: F3 WAS NEVER IN THE BODY.** The v2 cell claimed the corpus binding and §6a still pointed at the research tree's own working directory — a peer-tree path, in backticks, with no repo path, no digest line and no pin test named anywhere. (The offending path is described rather than reproduced: a spec in the repo should not carry a live-looking peer-tree reference even inside its own errata.) **0037 round-2 B3 verbatim, plus its cell-vs-carrier disagreement**, written by the seat enforcing *the file is the artifact*. Dev found it by grepping the body for what the cell claimed. Now landed: the corpus at `tests/eval/extraction_speech_act/`, one `corpus sha256:` line, `spec_version` + `spec_pin` in the manifest, `tests/test_0038_corpus_pin.py` in 0037's shape INHERITING its golden vector and exactly-one assertion. Also: **V-NO-COERCED named THREE relations where the manifest's `disposition_set` is FIVE — it would have passed while `avoids_tool` or `has_diet` was coerced into**, so it now derives the set from the artifact and cites the measured 31/66 as its baseline; and its condition is F2's rather than the premise F2 replaced. **Still NOT packageable: the new text has ONE reader.** |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | — (research only; **this text has had ONE reader**) |
| **External review** | REQUIRED — changes what the product stores from a given input |
| **Decision + date** | — |
| **Path** | full |

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

**2b. An instruction is FILED, COUNTED and NOT STORED — never coerced into a
triple.** The extraction JSON gains one field:

```
"instructions": ["<the instruction, verbatim>", …]     # NEW; may be empty
```

`EXTRACT_SCHEMA` is `additionalProperties: False` with `required: [triples,
episode]`, so this is a schema change — small, and the mechanism is the point.
The prompt directs an instruction **there** and never into `triples`. The store
reads the field, **counts it into the ingest report** as `instructions_dropped`
beside the existing `invalid` counter (`ingest.py:265`, `:454`), and **stores
none of it**. The episode still records that the instruction was given.

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

*This also answers §10 Q1 — the drop is no longer invisible. `instructions_dropped`
is the `withheld`-with-a-count shape, at the ingest report rather than the read
surface.*

**2c. What changes, stated exactly.** The reference prompt's RULES block and its
episode field description (§2a, §2c-i); `EXTRACT_SCHEMA` gains `instructions`
(§2b); `ingest.py` reads that field, counts it and stores none of it. **NO
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

The untrusted input is the event text, unchanged from today. This spec **narrows
what may be STORED from it** and cannot widen it: 2b routes instructions into a
field the store reads, counts and discards, so the set of things that can become
a record strictly shrinks. The new field is a REPORTING surface, not a storage
one — nothing in `instructions` is ever persisted, which is what makes the
narrowing structural rather than promised. The third-party discipline at `prompts.py:41` is untouched and still governs its
own case; 2a is its **user-authored counterpart** and belongs beside it in the
RULES block, where the existing rule lives.

**AND THE EPISODE FIELD'S OWN DESCRIPTION CHANGES IN THE SAME COMMIT** (dev's
F5). `prompts.py:29` — *"what happened / was decided / was attempted, with
outcomes"* — is the sentence that CAUSED the defect, and research's own A/B
changed exactly that clause. A RULES-block rule contradicting the field's own
description leaves the model two instructions and no way to rank them. **Both
sites, one commit**: the field describes what an episode records, the rule
forbids asserting performance.

## 3. Trust-class matrix — REQUIRED, blocking

Unchanged. This spec emits **fewer** records and weaker claims; it upgrades
nothing. An episode that previously asserted an action now reports a statement —
strictly less assertive. A triple that previously asserted a disposition is now
absent.

## 6. Invariants and executable checks — REQUIRED, blocking

| id | invariant | check |
|---|---|---|
| **V-NO-FABRICATED-ACTION** | no bare instruction is stored as a completed action | the frozen 66 bare procedural inputs: **0/66**, against the measured 19/66 baseline |
| **V-NO-COERCED-DISPOSITION** | no instruction becomes a disposition fact | zero edges on the frozen 66 whose relation is in the manifest's `disposition_set` — **derived from the artifact, not listed here** (today 5: `avoids_tool`, `has_diet`, `prefers`, `uses_tool`, `works_on`; v1's row named three and would have passed while `avoids_tool` or `has_diet` was coerced into). Measured against the manifest's `coerced_into_a_disposition_relation.rate` — **31/66 = 47%**. Condition is F2's: the vocabulary handed to the prompt carries no procedural relation (v1's row said "where no procedural relation is registered", the premise F2 replaced) |
| **V-EVENT-RETAINED** | dropping the triple does not drop the event | every one of the 66 still yields exactly one episode |
| **V-THIRD-PARTY-UNTOUCHED** | `prompts.py:41`'s third-party rule is unchanged in behaviour | the 0001 and 0023 third-party tests by NODE ID, not "the existing suite" — P4 wants ids, and "passes unchanged" over an unnamed set is a claim nobody can re-run |
| **V-NO-PROCEDURAL-IN-PROMPT-VOCAB** | §1a's cause B holds: the vocabulary handed to the extraction prompt carries no procedural relation | assert on `render_prompt_relations(reg)` (`ingest.py:204`) that no rendered relation has `relation_kind="procedural"` — **on the KIND, never on names or descriptions**. Reuses 0037's V-EXTRACTOR-BLIND rather than restating it. *v1 asserted "no relation in the registry denotes a practice", which is FALSE TODAY on descriptions (`has_diet`: "dietary practice or restriction") and would fail the day 0037 ships `follows_procedure` while §2b stayed correct — and research "verified" it with a hand-made set of practice-words, a hand-maintained list inside the check written to remove one.* Mutant: assert on names or on the registry rather than the rendered vocabulary |
| **V-NON-REGRESSION-CHARACTERISED** | the 412-text capture's non-fabricating summaries do not silently degrade | diff before/after; the change must be a **named class**, not merely small (§6a) |

### 6a. Acceptance measurement — REQUIRED, FINITE

**THE CORPUS LIVES IN THE REPO AND IS BOUND BOTH WAYS.**

  `tests/eval/extraction_speech_act/MANIFEST.json`   — research-authored, byte-copied by dev
  `tests/eval/extraction_speech_act/bare_procedural_66.jsonl`     — the acceptance set
  `tests/eval/extraction_speech_act/capture_412.jsonl`            — the non-regression set

The manifest's sha256 is carried on **one** line of this spec:

```
corpus sha256: d878502d1b0211aae3400539cf52390bfe8b7d4fbd69ac5f69a26eb34f1433af
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

1. **Does 2b's drop want a disclosure?** A dropped triple is invisible; the
   episode retains the event, but nothing tells a caller that procedural content
   was seen and not stored. 0037's `withheld`-with-a-named-outcome shape is the
   obvious model. Deliberately not specified here — it is a surface, not a fix.
2. **Does the episode rule generalise beyond instructions?** The capture only
   probed procedural inputs. Whether declarative inputs also gain unsupported
   speech acts is unmeasured, and the 412-set can answer it.

## Reviewer checklist

- [ ] every claim in §1 is reproducible from the frozen corpus, not from prose
- [ ] the fix is in the RULES block beside the third-party rule, not in a field description
- [ ] 2b DROPS rather than coerces, and no new relation is introduced
- [ ] the non-regression set is scored on **what changed**, not on what stayed
- [ ] no production frequency is claimed anywhere
