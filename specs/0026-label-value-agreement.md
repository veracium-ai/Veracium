# Feature spec: label/value agreement check

Spec-Status: draft
Spec-Requires: 0005, 0023, 0024, 0025

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — the current revision is stated ONCE, in the **Version** row
> below (the 0001 R10-2 lesson adopted at birth: the opening block carries
> no revision). Research proposed this check 2026-08-21 as the product-side
> instance of the presumed-faking rule; Quentin queued it as dev task #107,
> post-release; the 0024 A1 amendment names it as Q5's completion
> instrument.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v3** — the pre-send audit (2026-08-24, dev): **`Spec-Requires` completed with `0023`** — this spec consumes its single-write-site discipline, its standing-revocation floor ordering and its §4i asymmetry while declaring independence of it (the F1 class); §2c-ii **Assertions about reach** and §2d **Trust-class matrix** written, both REQUIRED by TEMPLATE and both absent; the §9 brief addressed to the EXTERNAL reviewer with the internal rounds and research's rulings recorded as fair game. Every command in §2c-ii was RUN and its real output recorded — including dev's recomputation showing the B02/B07 motivating cells survived `0024`'s landing unchanged. *Prior:* **v2** — internal round 1 folded (research, 2026-08-23, PASS WITH AMENDMENTS; delivered early on Quentin's word): **M-1** the census figures corrected to the shipped script's exact output (183,417 / 1,644 = 41.7% over cache `654e336a`; v1 carried prose-propagated pre-correction values — the drift recorded in §1 as the spec's thesis in miniature), **M-2** §8's promise scoped to the LEXICON with the coverage denominator riding the §6a run, **Q1 RATIFIED** with the dominance argument + NAMED DIRECTIONAL cells blocking-grade (first-person-outbound never matches), **Q2 RATIFIED** (the 2% bar stands because pre-committed; FP direction-split reported), **Q3 RATIFIED** (+ `Edge.agreement` travels in export so Q5's corpus survives portability), m-3 the floor position stated once via monotonicity, m-4 the B02 prior-evidence pointer on V-Q1, m-5 the dash-agnostic figure sweep. *Prior:* **v1** — the design (2026-08-23) |
| **Status** | *see `Spec-Status:` — canonical.* Draft authorises nothing |
| **Internal reviewers** | research — round 1 PASS WITH AMENDMENTS 2026-08-23 (2 moderates + 3 minors, all three §9 questions ruled; the census re-derived from the cache), folded in v2; **round 2 PASS 2026-08-24 (diff-verified 824dd03..e60206e, no new findings) — READY FOR EXTERNAL at Quentin's discretion** |
| **External review** | required — adds a disclosure floor on the ingest write path |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation — the third axis, measured

The trust pipeline now checks two structural axes of every extracted
triple: **membership** (`0025` — is the relation in the closed
vocabulary?) and **coherence** (`0024` — does the quarantine label
contradict its own claimant slot?). Nothing checks **agreement**: whether
the record's structural LABEL and the value-side evidence the extractor
itself wrote — the `note` and the `object` text — tell the same
provenance story. When they disagree, today the label wins silently.
That is the A17 failure class an external production operator
independently reported (relayed by Quentin 2026-08-21), with the same
fix shape research adopted as the **presumed-faking rule**
(`D_EXTENSION` §VII): a value-evidence layer beneath the schema.

Three measured artifacts say the disagreement population is real, in
BOTH directions:

- **The laundering direction (dangerous).** In the 0024 baseline
  (48 probes, main @ `1015e41`): **2/16 genuine relays bypassed
  quarantine entirely** — B02 ("my doctor said my cholesterol is
  borderline") stored as `health_state`/MENTIONABLE and B07 ("the vet
  said Rex is allergic to chicken") as `has_diet`/MENTIONABLE, **B07's
  note reading "as stated by the vet" while the relation launders the
  relay**, and the answer asserting ("This was confirmed by the vet").
  When the extractor picks a concrete relation, `_disclosure_for` never
  sees a quarantine-triggering label at all; `0024`'s decision-order
  work is orthogonal to this path by construction (its own §7 says so),
  and `0025`'s vocabulary enforcement makes it MORE likely a relay
  lands on a concrete registry relation. The post-A1 paired run
  confirmed the same two cells unchanged.
- **The demotion direction (the L1 census).** Of **183,417** cached
  triples, **3,945 (2.15%)** carry `third_party_claim`; on **1,644
  (41.7%)** of those the extractor's own note names the USER as the
  source ("price stated by user") — the note testifying against the
  label. *(Figures are the shipped script's exact output —
  `corpus_counts.py` over cache `654e336a`, re-run at internal round 1.
  v1 carried 183,416 / 1,637 / 41.5%: research's summary prose carried
  the drifted value, and this spec CITED it without re-derivation — the
  drift and the trusting citation are BOTH the failure mode this check
  exists for, recorded rather than silently fixed; internal M-1, the
  symmetric wording research's round 2 supplied.)* `0024`/A1 addresses the 40.7% whose SUBJECT slot is literally
  `user`; the note-only remainder stays quarantined with its
  disagreement unrecorded.
- **The evidence bound.** Of the four genuine relays the A1 measurement
  caught moving, **2 of 4 carry EMPTY notes** — value evidence is
  PARTIAL. Any rule built on it must treat marker ABSENCE as no
  evidence, never as agreement.

## 2. The design spine — prose may only lower

`0024` §4a rejected the note as a re-disposition trigger because "the
note is free text … prose an LLM wrote and nothing constrains it", and
chose the structural slot. That ruling stands, and this spec does not
reopen it, because the two uses are asymmetric:

- **Using prose to RAISE a disposition** hands assertion to an
  unconstrained channel — the injection surface every accepted spec
  closes. Never done here.
- **Using prose to LOWER a disposition** is fail-safe: a false positive
  costs assertion of one genuinely-own fact (recall), never integrity —
  the same trade `0024` §7 already accepts for its own narrowness
  ("failing narrow costs recall, never assertion").

**Every rule in this spec is therefore restrict-or-record: the check can
floor a disclosure at `USE_ONLY`, and it can record a disagreement; it
can never raise, and it can never assert.** (`0005` C1's no-grant rule
is honored by construction, unlike the cell 0024 v7 had to defend.)

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| the extractor's `note` | absent/empty → NO evidence (never agreement — the 2/4 empty-note movers) | any prose → scanned by the closed marker lexicon only | text outside the lexicon → no match, no claim | note crafted to AVOID markers ("relay hiding") | **V2**: absence of a marker is absence of evidence; the check widens no assertion path, so hiding buys the attacker nothing they lack today |
| the extractor's `object` text | — | same lexicon scan | same | object crafted to EMBED inbound markers on a genuinely-own fact ("my own view — but as my doctor said, rest matters"); the OUTBOUND phrasing ("as I told my doctor") is a directional non-match by contract (§3a) | **V3**: a false relay match FLOORS at USE_ONLY — recall cost, bounded, measured before acceptance (§6a); never an integrity cost |
| the marker lexicon itself | empty lexicon REFUSED at load (a vacuous checker that passes everything is the presumed-faking rule's target) | a malformed entry refuses at load — closed, versioned, code-owned (the `0025` registry pattern) | — | a host supplying a custom lexicon | **V4**: the lexicon is NOT host-configurable in v1 — one code-owned surface, one measured false-positive rate |

### 2c-ii. Assertions about reach — REQUIRED

**Every command was RUN in this repository on 2026-08-24 and the result
column records its real output.**

| assertion | command | result (RUN 2026-08-24) |
|---|---|---|
| **the laundering mechanism is real in the shipped code**: a CONCRETE relation never reaches the quarantine branch, so a relay filed under one is grounded by the author rules alone | `python -c "from veracium.ingest import _disclosure_for; from veracium.schema import EvidenceAuthor as A; print(_disclosure_for(A.USER,'has_diet',None), _disclosure_for(A.USER,'third_party_claim',None))"` | `mentionable` · `quarantined` — B07's exact shape: `has_diet` grounds, the quarantine label would not have |
| **`Edge.agreement` does not exist today** — §3d is a construction, and its None-omitted pattern has a shipped precedent in `original_relation` | `python -c "from veracium.schema import Edge; print([f for f in Edge.model_fields if 'agree' in f])"` | `[]` |
| **`note` is unconstrained free text** — the channel §2 refuses to let RAISE anything | `python -c "from veracium.schema import Edge; print(Edge.model_fields['note'].annotation)"` | `<class 'str'>` — no validator, no vocabulary |
| **`0024`'s mechanism is SHIPPED as amended, and it is orthogonal to this check** — the floor added here composes with a live pipeline, not a planned one | `grep 'Disclosure.USE_ONLY if row.get("redisposition")' src/veracium/ingest.py` | present — A1's uniform disposition, landed 2026-08-24 |
| **the B02/B07 cells survived `0024`'s landing unchanged**, so this check's motivating population is still there | dev's recomputation of research's A1 paired records (`a1_records.jsonl`) | B02 `health_state`/mentionable, B07 `has_diet`+`has_pet`/mentionable — the only two cell-B probes still assertable; cell B non-assertable 14/16 |
| **the demotion-direction population is measured, from the script, not recalled** | `corpus_counts.py` over cache `654e336a` | 183,417 triples; 3,945 `third_party_claim`; **1,644 (41.7%)** whose note names the user as source |

*(The first row is the whole spec in one line: the trust decision that
should have quarantined B07 was never consulted, because the extractor
chose a relation that routes around it. Nothing in `0024` or `0025`
reaches that path — one checks the label's coherence, the other its
membership; neither checks whether the VALUE agrees with either.)*

## 2d. Trust-class matrix — REQUIRED, blocking

**Scope:** rows state the FINAL disclosure for a triple whose value
evidence carries an INBOUND relay marker naming a non-user source
(§3a's directional contract; outbound first-person phrasing is a
non-match by contract and appears as its own row). The floor added
here only ever LOWERS (§2), so every accepted floor still applies
after — the standing-revocation row is the case that matters.

| relation | value evidence | author | today | after | why |
|---|---|---|---|---|---|
| CONCRETE (registry, non-reserved) | inbound marker, non-user source | USER | MENTIONABLE — asserted | **USE_ONLY** | **the B02/B07 class, and the reason this spec exists.** The extractor's own words name a third-party source while the relation launders it |
| CONCRETE | inbound marker | THIRD_PARTY / derived | USE_ONLY | **USE_ONLY** | unchanged — the author floor already reached the same place; no cell moves |
| CONCRETE | **outbound** first-person ("as I told my doctor") | USER | MENTIONABLE | **MENTIONABLE** | the directional contract: the user recounting what they said is first-person testimony. §6a's false-positive bar lives here |
| CONCRETE | no marker (empty or unmatched note+object) | any | per author rules | **unchanged** | **V2**: absence of a marker is absence of evidence — never agreement |
| `third_party_claim` | note names the USER as source | any | QUARANTINED | **QUARANTINED**, disagreement RECORDED + counted | §3c: the demotion direction changes no disposition; the record is Q5's evidence corpus |
| `unclassified` (a `0024` re-disposition) | any | any | USE_ONLY (A1) | **USE_ONLY** | already at the floor this check can impose; no interaction |
| any | any | any, **source standing-revoked** | QUARANTINED | **QUARANTINED** | `0023` N1 wins over everything; this floor may only lower, never lift |

**No cell in this table raises a disclosure**, which is `0005` C1
honoured by construction rather than by argument — the property `0024`
had to defend at length is unavailable here by design.

## 3. Behaviour

### 3a. The detector (V1)

`relay_markers(note, object_text) -> frozenset[str]` — a pure function
over a **closed, versioned, code-owned marker lexicon** (attribution
verbs and source-naming patterns: *said / told / stated / according to /
confirmed by / per &lt;entity&gt;* …; the exact set is a code artifact with
its own tests, not a spec table, so it cannot drift from prose). It
consumes the SAME canonical strings the write path stores. It makes no
LLM call — the check must not ask the component under suspicion to
audit itself (the presumed-faking rule applied to the checker).

**The lexicon contract carries NAMED DIRECTIONAL cells, blocking-grade
(internal round 1, Q1 ruling): inbound attribution ("my doctor said…",
"according to the vet", "as stated by the vet") MATCHES;
first-person-OUTBOUND phrasing ("I told my doctor…", "as I said to…")
must NEVER match — the user recounting what they said is first-person
testimony, and §6a's 2% false-positive bar will be won or lost on
exactly this distinction.** The directional cells are part of the
lexicon's own test surface (V1), not left to lexicon-entry judgement.

### 3b. The laundering floor (V3) — the one disposition change

At ingest: **a triple whose relation is a CONCRETE (non-reserved)
registry member and whose value evidence carries an inbound relay
marker naming a non-user source is FLOORED at `USE_ONLY`** — may
inform, never assert; the marker set is recorded in the typed field
`Edge.agreement` (§3d). The floor runs as ONE MORE MEMBER of `0025`
§4b-iii step 3's accepted-floor set — and because floors only LOWER,
order WITHIN the floor set is irrelevant by monotonicity (internal
round 1, m-3: v1 described the position two ways; this is the one
description). The single write-site discipline `0023` N2 pins is
untouched — the floor is inside the same establishment path. B02 and B07 are the named regression
vectors, verbatim from the baseline records.

### 3c. The demotion-direction RECORD (V5) — no disposition change

A `third_party_claim` triple whose note names the USER as the source is
a disagreement in the other direction. **v1 records it and changes
nothing**: raising on prose is forbidden (§2), and A1's Q5 says
assertion completion needs content evidence judged by its own review
round. The record — the typed disagreement plus the counter — IS the
evidence corpus Q5's future round will be argued from. (This is `0024`
Q2's resolution honored: a flag nobody consumes is a field, not a
mechanism — here the named consumer is Q5's round, and the operator
counter is consumed by telemetry from day one.)

### 3d. The carrier (V6)

`Edge.agreement: frozenset[str] | None` — None-omitted from every
serialization exactly like `original_relation` (`0025` F6's pattern), so
unaffected edges stay byte-identical. **The field TRAVELS in export
(`0005`/`0014` portability): Q5's future evidence corpus must survive a
store migration, so the record is a portable fact, not a local one
(internal round 1, Q3 ruling's rider).** The ingest result gains
`agreement_floored` and `agreement_recorded` counters, present on every
path (zeros included — an absent key is not a zero); `Memory.remember`
passes through; the MCP surface STRIPS them with the other operator
counts; telemetry whitelists them under the consent contract.

## 4. What is deliberately NOT done

- **No LLM judge in the write path.** The lexicon is dumb, closed and
  measurable; a model grading model output re-opens the surface this
  check exists to close.
- **No retroactive sweep** (`0024` Q1's reasoning, unchanged).
- **No assertion completion.** The demotion-direction record feeds
  `0024` Q5's future round; nothing here raises.
- **No host-tunable lexicon in v1** (V4) — one measured surface first.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| a store whose notes/objects never carry relay markers | byte-identical (V7 pins it) |
| ordinary chat, first-person facts | unchanged unless a marker names a non-user source on a concrete relation |
| the B02/B07 class (relay under a concrete relation) | TODAY: MENTIONABLE, asserted. AFTER: USE_ONLY, attributed — the answer may still say "the vet said…", it may no longer assert it as fact |
| the L1 note-vs-label class (user-sourced note under `third_party_claim`) | unchanged disposition; disagreement recorded + counted |
| revoked sources (`0023`) | the standing floor still wins — QUARANTINED caps everything |
| import (`0005`) | unchanged; the cap runs on written records |

## 6. Invariants — REQUIRED, blocking (V1–V7)

| # | invariant | check |
|---|---|---|
| **V1** | the detector is pure, total over (None/empty/any-str)², lexicon-closed — no LLM call, no network, no host input — and DIRECTIONAL: the §3a inbound cells match, the first-person-outbound cells never match (blocking-grade, internal round 1) | `test_relay_detector_is_pure_and_total` — the directional cells enumerated |
| **V2** | marker ABSENCE never changes anything: empty/absent note+object → no floor, no record, byte-identical edge | `test_absence_is_no_evidence` |
| **V3** | the B02/B07 class floors at USE_ONLY — the two baseline vectors verbatim; and the floor NEVER raises (a quarantined edge stays quarantined) | `test_laundered_relay_floors_use_only` |
| **V4** | an empty or malformed lexicon refuses at load; the lexicon has exactly one definition site | `test_lexicon_is_closed_and_refuses_vacuous` |
| **V5** | the demotion-direction disagreement is recorded and counted with NO disposition change | `test_demotion_direction_records_only` |
| **V6** | `Edge.agreement` is None-omitted everywhere; both counters present on every result path; MCP strips; telemetry consent-gated | `test_agreement_carriers_complete` |
| **V7** | a marker-free store is byte-identical before and after | `test_no_markers_is_byte_identical` |

### 6a. The acceptance measurement gate

Before this spec is accepted, the lexicon's false-positive rate is
MEASURED on the existing extraction cache (research's corpus, counts
only — the cache never ships): the share of GENUINELY-OWN facts the
lexicon would floor. The spec pre-commits: **if that rate exceeds 2%
of grounded first-person triples, the lexicon narrows before v1
ships** — the recall cost is bounded by measurement, not hope. The
same run reports the false-positive count SPLIT BY DIRECTION (the
inbound/outbound cells of §3a — internal round 1, Q2: the bar will be
won or lost on the directional distinction) and the M-2 coverage
denominator; research co-verifies the run (their standing offer). And per
the presumed-faking rule, the check itself graduates by CATCHING: B02/
B07 are planted passes (mechanism); its bite claim waits for a catch
nobody planted, and §8 may not say otherwise.

## 7. Failure modes and reversibility

- **Too-narrow lexicon**: launders survive — today's behaviour, minus
  the ones it does catch. Failing narrow costs nothing new.
- **Too-broad lexicon**: own-facts land USE_ONLY — recall cost, bounded
  by §6a's measured gate, reversible by narrowing the lexicon (a code
  change with `rule_version` semantics, not a data migration).
- **Reversibility**: write-time floor + additive typed field; reverting
  restores prior behaviour for future writes; written records keep
  their disclosure (`0023` §4i's declared asymmetry, again).

## 8. Claims and limits

We will say: *a relayed claim whose note or value matches the
versioned marker lexicon is never asserted as the user's fact, whatever
relation it was filed under* — the promise is scoped to the LEXICON, a
mechanical surface, not to "names its source" as a semantic judgement
(internal round 1, M-2: a lexical mechanism may not carry a semantic
promise). The claim ships WITH ITS DENOMINATOR: the §6a measurement run
also reports the lexicon's coverage over the cache's source-naming note
population, so "matches the lexicon" is a measured fraction of the
naming population, not an implied whole. We will NOT say the check
catches relays that name nothing (the 2/4 empty-note movers bound that
honestly), will not call it extractor correctness, and will not claim
bite before an unplanted catch (§6a).

## 9. Brief for the external reviewer

*(Internal review is complete: research — who proposed this check —
ran two rounds, round 1 PASS WITH AMENDMENTS with all three questions
ruled and round 2 PASS with no new findings, both folded. The questions
below are what we most want you to attack; research's rulings on them
are recorded in the Version row and are themselves fair game.)*

1. **The asymmetry argument (§2)** — is restrict-only sufficient to
   make prose a safe input, or does even a lowering rule on an
   unconstrained channel create a denial lever (an attacker floors the
   user's own facts by seeding marker-shaped text)? Research ratified
   the bound with a dominance argument (§2c's row: any position that
   reaches the value channel of a grounded triple already writes
   user-authored event text and can already assert, which strictly
   dominates flooring). Attack that dominance claim — it is the load
   the whole spine rests on.
2. **The lexicon as instrument** — §VII demands components pass unseen
   data. Is §6a's measurement gate the right graduation, and is 2% the
   right pre-commitment?
3. **The demotion-direction record** — is record-without-consequence
   honest mechanism or a flag nobody consumes? We claim Q5 + telemetry
   are the named consumers.

## 10. Open questions

| # | question | state |
|---|---|---|
| **V-Q1** | should the answer surface RENDER the attribution for floored records ("per the vet: …") rather than the generic use-only treatment? | design — the L3 qualified-answer lever's territory; needs the gate's owner. Prior evidence when that round runs (internal round 1, m-4): the baseline's B02 answer already rendered content-derived attribution ("as reported by their doctor") while the edge sat MENTIONABLE — the floor plus existing prose attribution may be most of the answer |
| **V-Q2** | does the agreement record ever feed `0024` Q5's assertion completion, and under what evidence standard? | deferred to Q5's own round, by A1's design |
