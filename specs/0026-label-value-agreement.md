# Feature spec: label/value agreement check

Spec-Status: accepted
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
| **Version** | **v16 (ACCEPTED)** — external round 12 (2026-08-30): 🏁 APPROVED FOR ACCEPTANCE, the exact package `0026-v12` (sha 233d03af…), THE DESIGN FROZEN on the V1–V7/V6a invariant surface; R11-1 closed (all six checks exist and execute; mechanical absence proof; no resolution-guard exemption; V6a a deliberate failing tripwire until its matrix lands). Three non-blocking IMPLEMENTATION OBLIGATIONS recorded in §22 (V5 counter assertion, V6 surface-stripping assertion, V7 frozen pre-feature oracle). The status flip is authorized by the verdict; §Review closure is the generated per-round ledger. Twelve external + fourteen internal rounds, every fold same-day. *Prior:* **v15** — the ROUND-11 EXTERNAL FOLD (2026-08-30; §21 maps the one finding; the reviewer: the design surface REMAINS ready, NO FURTHER DESIGN ROUND NEEDED — the acceptance condition stated and met). R11-1: the six implementation-time V-checks EXIST as standing ABSENCE-AWARE tests — vacuity proven mechanically in the draft state (the proof flips when src/ gains the mechanism), behavioral cells activate at graduation, and the resolution guard exempts nothing. *Prior:* **v14** — the ROUND-10 EXTERNAL FOLD (2026-08-30; §20 maps both findings; THE DESIGN SURFACE IS READY — no new semantic issue, all six v9 corrections holding). PACKAGE-R10-1: the last numeric restatements removed — the R8-2 closure row is version-neutral and the boundary diagnostic derives from the shape. PRIVACY-R10-2: the sweep's undocumented 8MB skip removed — total scope at bounded memory (streamed text, chunked byte fallback); the R9-2 closure evidence runs both halves. Reviewer suggestion recorded as a forward renderer item: draft-time review-closure preview. *Prior:* **v13** — the ROUND-9 EXTERNAL FOLD (2026-08-30; §19 maps all three findings). R9-1: ONE canonical AgreementRecord — the shape matches §3d's stored enum exactly (user_source legal, the lexicon-internal 'outbound' refuses, empty markers refuse per V2); the §18 restatement corrected visibly, prose no longer carries the numbers. PRIVACY-R9-2: fchmod explicit (pre-existing permissive worklists end 0600, regression standing); the package sweep reads every line of every decodable file under specs/ with its scope stated. EVIDENCE-R9-3: the duplicate-cache regression is PROBATIVE (matching peer, exit-3 bootstrap required, the exact '1 unparseable' asserted). *Prior:* **v12** — the ROUND-8 EXTERNAL FOLD (2026-08-30; §18 maps all four findings; narrow verdict, ALL FOUR round-7 closures held). EVIDENCE-R8-1: duplicate JSON members refuse at parse at every evidence boundary (the 0011 R9-1 class refound — decoder precedence resolved ambiguous census records). R8-2: the AgreementRecord shape is EXECUTABLE data with a running reference validator, byte-bound into §3d, every bound driven at the limit and one beyond. EVIDENCE-R8-3: bootstrap output paths resolve and cross-check before any write — aliases and output-names-input refuse. PRIVACY-R8-4: the full-content worklist is mechanically LOCAL-ONLY (in-tree paths refuse, mode 0600, a standing package sweep refuses worklist-shaped artifacts under specs/). *Prior:* **v11** — the ROUND-7 EXTERNAL FOLD (2026-08-30; §17 maps all four findings; narrow verdict, the v6 digest-nonce attack confirmed DEAD). EVIDENCE-R7-1: the bootstrap deadlock closed — measurement reaches a distinct OVER-NEEDS-ADJUDICATION state (aggregate + full-content worklist emitted, acceptance never claimed) and the end-to-end pipeline runs over the shipped synthetic e2e_fixture through the real entry points. EVIDENCE-R7-2: independent co-verification is MECHANICALLY BOUND — two census manifests, fail-closed fp-union decision, host-only refuses. R7-1: grammar membership is VERSION-SCOPED — foreign-version markers are opaque closed shapes; out-of-grammar raises only under the current version. PACKAGE-R7-1: operational prose swept; the one-carrier claim constrained (current derives, history names its own round). *Prior:* **v10** — the ROUND-6 EXTERNAL FOLD (2026-08-30; §16 maps all four findings; NARROW verdict, architecture stable, four round-5 closures confirmed). EVIDENCE-R6-1: SAMPLING ENDS — every adjudication is a CENSUS (schema 6; face eight of the selection class: fire_digests was itself a host-produced identifier; eight faces proved no sampling construction over a host-produced population survives; the draw/seed/size/Wilson machinery is removed). R6-1: the restore/foreign-version cell RULED verbatim and carried through both generated projections. PACKAGE-R6-1: the half-swept-carrier class closed structurally — ADJUDICATION_SCHEMA is the one generated carrier of the revision, the example's generator ships and is byte-identity-tested, and the v9 entry below carries its visible correction. EVIDENCE-R6-2: the zero-denominator cell guarded. *Prior:* **v9** — the ROUND-5 EXTERNAL FOLD (2026-08-29; §15 maps all five findings; three round-4 closures confirmed holding). EVIDENCE-R5-1: the seed basis leaves the aggregate *[PACKAGE-R6-1 correction: this entry originally said the seed came from the sealed archive's committed sidecar — that interim form was replaced by the projection seed BEFORE the v6 seal (research's round-5 pre-seal completion, §15) and this row was not re-swept; the sealed v9 shipped the projection seed, schema 5]* (any host-produced byte in a selection basis is a nonce; the reviewer drove a decision-irrelevant field and swung the draw). R5-1: §2c is a true PROJECTION of the one matrix, with the source-level co-movement mutation standing. PACKAGE-R5-1: the 'SHIPPED manifest' overclaim corrected visibly in every carrier; the worked synthetic example ships and validates from disk. EVIDENCE-R5-2: the doc's coverage denominator derived, not hard-coded. EVIDENCE-R5-3: undecodable bytes are structured refusals. *Prior:* **v8** — the ROUND-4 EXTERNAL FOLD (2026-08-29; §14 maps all five findings; the round's shape: every round-3 example fixed, every new closure MECHANISM seamed — answered with GENERATED carriers). R4-1: lex-10 REMOVES the artifact carve-out (ownership is not authorship — 'my own record reported a diagnosis' laundered); no noun class carries an authorship inference; ownership-vs-authorship oracle axis + relapse mutant; re-measured identical (0.64%). R4-2: import_matrix.py is the ONE decision table — §2c and §3d are both generated from it, byte-bound. EVIDENCE-R4-1 (the signature defect's sixth face): the adjudication is RECORD-BOUND — fire_digests population, a shipped labelled manifest opened and hashed, counts DERIVED by counting labels, accept on the Wilson-95 UPPER bound (research's forward notes made live). EVIDENCE-R4-2: the §6a claim is a GENERATED block, byte-bound at the verify entry point (the lex-8-over-lex-9 headline and both reviewer mutations refuse). PACKAGE-R4-1: the Internal-reviewers row is rendered from the ledger; static readiness claims refused. *Prior:* **v7** — the ROUND-3 EXTERNAL FOLD (2026-08-29; §13 maps all five findings). R3-1: lex-9 — `or` coordination + the ARTIFACT-vs-ENTITY self-possessive split over a closed artifact set; oracle axes added; measured identical (0.64%). R3-2: the AgreementRecord joins §2c, and restore-malformed RAISES with nothing written (the R1-4 ruling on the restore path; validation before any write). EVIDENCE-R3-1: the adjudication is an EXECUTABLE DECISION — closed verdict enum, computed adjudicated rate vs the gate, sample minimum, digest binding to the exact aggregate; the reviewer's REJECT-passes case is the standing refusal. EVIDENCE-R3-2: the candidate spec's §6a figures bind to the aggregate at the verify entry point (217-vs-220 re-derived). PACKAGE-R3-1: §9's round count derives from the ledger, standing-tested. *Prior:* **v6** — the ROUND-2 EXTERNAL FOLD (2026-08-29; §12 maps all five findings). 0026-R2-1: the subject is resolved by HEAD CONSTRUCTION (lex-7) — modifiers inert, coordinated co-heads with determiners, Unicode possessives normalized — with the GENERATED grammar-oracle corpus (expectations derived from constructions; it caught two further defects during its own construction); §6a RE-MEASURED at 0.64% (439/68,479). 0026-R2-2: the import boundary is MODE-SPLIT (restore trust-field-faithful per 0005 P2; default recomputes) and export rides a FORMAT_VERSION bump per 0025. 0026-R2-3: the deferral swept to every carrier with a whole-file test. EVIDENCE-R2-1: the GATE is part of aggregate validity (over-gate refuses absent an adjudication artifact) and the measurement doc is mechanically bound to the aggregate. PACKAGE-R2-1: closure figures derive from one source; research's pass is structured internal rounds 3-4. *Prior:* **v5** — the ROUND-1 EXTERNAL FOLD (2026-08-29; §11 maps all five findings; the restrict-only spine untouched). 0026-R1-1: direction is a GRAMMAR, not proximity — agent governs, passive recipients inert, clause-bounded subjects, ambiguous pronouns restrict with a counted conservative outcome; the five executed counterexamples ride verbatim; §6a RE-MEASURED at 0.70% (481/68,479 under lex-6: the lex-4 grammar pre-empting research's coordination/nesting shapes, plus their red-team's recall-driven verb expansion — `claimed` et al — with the nominal homographs narrowed by reading the fires; RECALL now measured via held matrix cells), gate cleared. 0026-R1-2: `Edge.agreement` is a STRUCTURED record (markers + direction + lexicon version) with a total import matrix — recomputation governs, incoming values are diagnostic only. 0026-R1-3: telemetry DEFERRED (no whitelisting without a 0015-conformant amendment). EVIDENCE-R1-1: the aggregate is bound — closed validator, cross-artifact manifest anchor, verify mode, the reviewer's tamperings as matrix cells, RECORDED-ONLY labels, the lex-1 claim narrowed. PACKAGE-R1-1: candidate revision is a structured SENT-row field bound by the identity gate; the internal-first miss acknowledged. *Prior:* **v4** — §6a MEASURED and §3a amended by what the measurement found (2026-08-26, dev): the false-positive gate is CLEARED at 0.61% of a 2% bar after the first lexicon came in at 8.20% and narrowed, per §6a's own pre-commitment; and §3a's OUTBOUND cells are restated over the attributing SUBJECT rather than the first-person pronoun — measured, the first-person form suppressed 0 of 68,479 triples because the extractor narrates the user in the third person, so every *\"user confirmed…\"* was being read as somebody else's claim. Evidence: `specs/evidence/0026/FP-MEASUREMENT.md`. *Prior:* **v3** — the pre-send audit (2026-08-24, dev): **`Spec-Requires` completed with `0023`** — this spec consumes its single-write-site discipline, its standing-revocation floor ordering and its §4i asymmetry while declaring independence of it (the F1 class); §2c-ii **Assertions about reach** and §2d **Trust-class matrix** written, both REQUIRED by TEMPLATE and both absent; the §9 brief addressed to the EXTERNAL reviewer with the internal rounds and research's rulings recorded as fair game. Every command in §2c-ii was RUN and its real output recorded — including dev's recomputation showing the B02/B07 motivating cells survived `0024`'s landing unchanged. *Prior:* **v2** — internal round 1 folded (research, 2026-08-23, PASS WITH AMENDMENTS; delivered early on Quentin's word): **M-1** the census figures corrected to the shipped script's exact output (183,417 / 1,644 = 41.7% over cache `654e336a`; v1 carried prose-propagated pre-correction values — the drift recorded in §1 as the spec's thesis in miniature), **M-2** §8's promise scoped to the LEXICON with the coverage denominator riding the §6a run, **Q1 RATIFIED** with the dominance argument + NAMED DIRECTIONAL cells blocking-grade (first-person-outbound never matches), **Q2 RATIFIED** (the 2% bar stands because pre-committed; FP direction-split reported), **Q3 RATIFIED** (+ `Edge.agreement` travels in export so Q5's corpus survives portability), m-3 the floor position stated once via monotonicity, m-4 the B02 prior-evidence pointer on V-Q1, m-5 the dash-agnostic figure sweep. *Prior:* **v1** — the design (2026-08-23) |
| **Status** | *see `Spec-Status:` — canonical.* Draft authorises nothing |
| **Internal reviewers** | research — **14 internal rounds** (GENERATED from `specs/reviews.py`, the structured ledger — round history, verdicts and closures live there, never in this static row; latest: internal round 14, 2026-08-30). 12 external rounds returned so far, so external-readiness is the ledger's state to derive, not this row's to claim |
| **External review** | required — adds a disclosure floor on the ingest write path |
| **Decision + date** | **ACCEPTED 2026-08-30** — external round 12, APPROVED FOR ACCEPTANCE on package `0026-v12`; implemented the same day (`3b60e65`, on Quentin's word) |
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
| an imported `AgreementRecord` (§3d) | absent → default mode: RECOMPUTED under the current lexicon (the V6a matrix above); floor runs; mismatches counted; restore: restored VERBATIM, disclosure included (`0005` P2); recomputation diagnostic-only (absent stays absent) | malformed → default: treated as absent; the recomputation governs (the V6a row above); restore: **RAISES, nothing written** — the two modes DIFFER by design (PROJECTED with the §3d matrix from `import_matrix.py`, the one carrier) | foreign `lexicon` version → default mode: RECOMPUTED under the current lexicon (the V6a matrix above); floor runs; mismatches counted (incoming version diagnostic only); restore: restored VERBATIM (0026-R6-1: both modes stated — the cell was default-only) | forged markers on marker-free text → default mode: RECOMPUTED under the current lexicon (the V6a matrix above); floor runs; mismatches counted; restore: restored VERBATIM, disclosure included (`0005` P2); recomputation diagnostic-only | **V6a**: default mode recomputes so a forged record cannot enter Q5's corpus; restore is 0005-P2-faithful for VALID fields only, with validation ordered BEFORE any write |
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
"according to the vet", "as stated by the vet") MATCHES; OUTBOUND
phrasing — the user as the one doing the attributing — must NEVER
match, because the user recounting what they said is first-person
testimony, and §6a's false-positive bar is won or lost on exactly this
distinction.**

**The test is WHOSE SPEECH IS BEING REPORTED, not which pronoun carries
it (§6a measurement, 2026-08-26).** The outbound cells were first
written in the first person alone — *"I told my doctor…"*, *"as I said
to…"* — and measured against the extraction cache that form suppressed
**exactly 0 of 68,479 grounded first-person triples**, because the
extractor does not write in the user's voice. It narrates them:
*"user confirmed no dietary restrictions"*, *"project mentioned by
user"*. Every one of those was being read as INBOUND — the user's own
word treated as somebody else's claim, which is the failure the bar
exists to prevent, and it would have been shipped as a clean result.
**The direction is decided by a GRAMMAR, not by proximity (external
round 1, 0026-R1-1).** The lex-2 rule scanned four preceding tokens for
a user reference, and proximity is not authorship: the reviewer
executed five counterexamples — a passive recipient mistaken for the
speaker (*"I was told by my doctor…"* read outbound), a passive with a
named third-party agent (*"user was told by the vet…"* read outbound),
the spec's own demotion example inverted (*"price stated by user"* read
inbound), an embedded clause inheriting the outer subject (*"user said
their doctor confirmed…"* read both verbs outbound), and a pronoun
silently assumed to be the user (*"she said the user needs
medication"*). The grammar (lex-4 — lex-3 closed the five; lex-4 adds coordinator transparency and the coordinated-co-source rule, pre-empting the coordination/elision/nesting shapes named for the pre-seal red-team pass), in precedence order:

1. **A post-verbal `by <agent>` phrase governs** — passive (*"told by
   my doctor"* → inbound) and reduced passive (*"price stated by
   user"* → outbound) alike; the recipient before the verb is inert.
2. **A passive auxiliary with no agent is conservatively inbound** —
   *"I was told…"* is a relay from an unstated source.
3. **The active subject is resolved inside its own clause** — the scan
   stops at another attribution verb or a complementizer, so *"user
   said their doctor confirmed…"* classifies `said` outbound and
   `confirmed` inbound, independently.
4. **Ambiguous pronouns (he/she/they, bare him/her/them) are their own
   class with an explicit conservative outcome**: never silently the
   user; they RESTRICT (over-restriction is the safe failure in a
   restrict-only design, bounded by §6a's bar) and are COUNTED
   separately in the measurement so the ambiguity is visible, not
   hidden in either bucket.
5. **No subject at all attributes nothing** — a bare participle
   (*"recommended brand"*).

The outbound cells (the user as source): first-person subject, the
user in the third person (*"user confirmed no allergies"* — the
extractor's actual voice), the user named in a frame or as a
post-verbal agent, and the first-person self-possessive. A possessive
attached to a THIRD PARTY stays inbound — *"my doctor said"* is the
commonest relay shape there is.

**The verb list is scoped and its RECALL is measured (research
red-team, pre-seal — the FN direction).** lex-2 through lex-4 measured
false positives only, so verb-list completeness WAS the check's recall,
unmeasured — and `claimed`, the name of the very relation `0024`
quarantines, was missing. lex-6's verb classes, stated: reporting
(said/told/stated/mentioned/reported/confirmed/informed and
inflections), assertion (claimed/alleged/argued/insisted/testified/
acknowledged), transmission (wrote/texted/emailed/replied/warned/
explained/noted), and professional judgment (diagnosed/prescribed) —
RULED IN, because they attribute a professional's factual claim, which
is the B02/B07 laundering class exactly. The ADVICE class
(advised/recommended/suggested) stays OUT, with the reason on record:
it attributes a recommendation rather than a fact, and it was 79% of
lex-1's measured false fires. Nominal homographs are excluded by
evidence, not guess: lex-5 added notes/added/adds/emails and reading
the fires showed every sampled one nominal ("taking notes", "adds
flavor", "checking emails"), so lex-6 keeps only the unambiguous
inflections (noted, emailed). Verb completeness is MEASURED two ways:
held RECALL cells in the lexicon matrix (known relays across the verb
classes MUST fire — removing `claimed` alone is a red matrix), and the
§6a re-measurement pricing every addition.

The directional cells — the five counterexamples verbatim plus the
generated cross-product of voice × identity × clause — are part of the
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
counter is a LOCAL operator surface; its telemetry consumption is
DEFERRED per §3d [carrier swept, 0026-R2-3: this sentence previously
said "consumed by telemetry from day one", contradicting the §3d
deferral].)

### 3d. The carrier (V6)

`Edge.agreement: AgreementRecord | None` — a STRUCTURED record, not a
bare marker set (external round 1, 0026-R1-2: a set of strings carried
no version and no direction, so a stored record could not say which
lexicon produced it or which way it pointed). `AgreementRecord` binds
three fields: `markers` (the matched set), `direction`
(`"inbound" | "ambiguous" | "user_source"` — §3b's floor evidence and
§3c's demotion-direction record share the carrier, disambiguated here),
and `lexicon` (the producing `LEXICON_VERSION`, so a store holding
records from several lexicon generations — there is no retroactive
sweep — stays interpretable per record). None-omitted from every
serialization exactly like `original_relation` (`0025` F6's pattern),
so unaffected edges stay byte-identical. **The field's export rides a
FORMAT_VERSION bump (external round 2, 0026-R2-2 — v5 said an old
reader "ignores the unknown key", which contradicts accepted `0025`'s
portability rule: a new exported field bumps the format so an old
reader REFUSES rather than silently drops it).** An export from a store
holding any agreement-bearing record is stamped with the bumped format;
an old reader refuses that file outright, so the
new-export → old-reader → re-export cycle that would have silently
shed Q5's evidence carrier cannot begin. A new reader over an
old-format file finds the field absent and fabricates nothing. The
field's addition rides the same `rule_version` bump as the §3b floor
itself (§7). **The field TRAVELS in export (`0005`/`0014`
portability): Q5's future evidence corpus must survive a store
migration (internal round 1, Q3 ruling's rider).**

**The import boundary (V6a — external round 1, 0026-R1-2; mode-split
external round 2, 0026-R2-2).** The boundary has TWO modes with
opposite trust contracts, and v5 wrongly gave them one rule:

* **`restore=True` is TRUST-FIELD-FAITHFUL, per accepted `0005` P2**:
  the `agreement` field AND the record's disclosure restore VERBATIM —
  the §3b floor does NOT re-run (it ran, or legitimately did not run,
  at the source store's original establishment, and a restore that
  re-floors changes a disclosure `0005` promises to reproduce). The
  current lexicon's recomputation runs only as a DIAGNOSTIC: the
  `agreement_import_mismatches` counter increments on disagreement and
  nothing is stored from it.
* **default mode is the untrusted-import path**: the imported field is
  UNTRUSTED INPUT, and the lexicon is pure over the same stored text —
  so import RECOMPUTES; the stored value is the current lexicon's
  output over the imported note/object, and the §3b floor runs as one
  more member of the `0025` §4b-iii establishment it already belongs
  to. The matrix below is this mode's:

| imported field vs text | outcome |
|---|---|
| absent, text carries markers | recomputed and STORED — the record is repaired, and the repair counted |
| present, text carries no markers (forged) | recomputation stores None — the forgery is DISCARDED and counted |
| malformed (wrong shape, unknown keys, entries outside the current lexicon) | treated as absent; recomputation governs; counted |
| foreign `lexicon` version | recomputation under the CURRENT lexicon governs; the incoming version is diagnostic only |
| direction disagrees with the text | recomputation governs; the disagreement counted |

In default mode the incoming field value is never consumed for any
decision — compared for the diagnostic counter, then discarded in
favor of the recomputation: a forged marker cannot smuggle a
restriction record into Q5's corpus, and a stripped one cannot launder
a relay past the floor. The COMPLETE boundary,
{format era × mode × field state}:

<!-- GENERATED:import-matrix (import_matrix.py — the ONE carrier; do not hand-edit) -->
| format | mode | imported field | outcome |
|---|---|---|---|
| old (pre-agreement) | either | absent by construction | no fabrication; default mode floors at establishment as for any write; restore reproduces the old store verbatim |
| new | default | any state (absent/present/forged/malformed/foreign-version) | RECOMPUTED under the current lexicon (the V6a matrix above); floor runs; mismatches counted |
| new | restore | present AND VALID, or absent | restored VERBATIM, disclosure included (`0005` P2); recomputation diagnostic-only |
| new | restore | present, well-typed, FOREIGN lexicon version (markers OPAQUE: e.g. markers=['future_marker'] under lexicon='0026-lex-999') | restored VERBATIM — the version field exists to mark provenance, and recomputation stays diagnostic-only. GRAMMAR MEMBERSHIP IS VERSION-SCOPED (0026-R7-1): under a foreign version the reader CANNOT know that lexicon's vocabulary, so markers are validated as OPAQUE closed shapes only — nonempty bounded strings, bounded count, closed record types — never for membership; the malformed row's out-of-grammar rule applies ONLY under the CURRENT version, where the vocabulary is known (0026-R6-1: a well-typed foreign record is not garbage, and refusing it would break restore round-trips of old exports; readers recompute under the current lexicon at consumption) |
| new | restore | present but MALFORMED (wrong types, unknown keys, or — under the CURRENT lexicon version only — markers outside its grammar; foreign-version membership is unknowable and handled by the opaque rule above, 0026-R7-1) | **RAISES, nothing written** — verbatim restore into a typed carrier is impossible for garbage, and flooring it would silently accept a corrupt export (the R1-4 ruling, applied to the restore path); validation runs BEFORE any write, so a refused record leaves no partial state |
| new | default | present but MALFORMED | treated as absent; the recomputation governs (the V6a row above) — default mode never consumed the value anyway, so refusal is unnecessary and recomputation is total |
| new file, old reader | — | — | the reader REFUSES the bumped format (`0025`'s rule) — no silent field loss is reachable |
<!-- /GENERATED:import-matrix -->

The closed record shape, EXECUTABLE (0026-R8-2 — "bounded" with no bounds let conforming implementations accept different inputs; `import_matrix.agreement_shape_problems` is the running reference the implementation must match, with every bound driven at the limit and one beyond by a standing test):

<!-- GENERATED:agreement-shape (import_matrix.py — the one carrier; do not hand-edit) -->
| shape rule | value |
|---|---|
| record keys (CLOSED; unknown keys REFUSE) | `markers, direction, lexicon` |
| markers collection | JSON array of strings, 1–8 entries (V2: no markers means no record) |
| marker string length | 1–64 characters |
| duplicate markers | REFUSE |
| direction (CLOSED) | `inbound, ambiguous, user_source` |
| lexicon version | 1–64 chars matching `[0-9a-z][0-9a-z.\-]*` |
<!-- /GENERATED:agreement-shape -->

The ingest result gains `agreement_floored` and `agreement_recorded`
counters, present on every path (zeros included — an absent key is not
a zero); `Memory.remember` passes through; the MCP surface STRIPS them
with the other operator counts. **Telemetry consumption is DEFERRED
(external round 1, 0026-R1-3): accepted `0015` requires consent text, a
consent-schema version, minimum field version, display-and-accept
transition, record-time gating and replay/rollback semantics for every
new payload field, and none of that is constructed here — so v1 ships
the counters as local operator surface ONLY, and a conforming
implementer MUST NOT whitelist them into any telemetry payload. A
future amendment that consumes them adds `0015` to `Spec-Requires` and
specifies the complete consent construction; until then the counters'
telemetry story is the same as any other unwhitelisted field's:
absent.**

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
| **V1** | the detector is pure, total over (None/empty/any-str)², lexicon-closed — no LLM call, no network, no host input — and DIRECTIONAL BY GRAMMAR (0026-R1-1): agent governs, passive recipients are inert, clauses classify independently, ambiguous pronouns restrict with a counted outcome, outbound never matches | **CURRENT** — the §3a five counterexamples verbatim + the GENERATED grammar-oracle corpus (attachment × coordination × Unicode possessives, expectations derived from the construction) in `validate_lexicon.py` and `tests/test_0026_relay_lexicon.py` |
| **V2** | marker ABSENCE never changes anything: empty/absent note+object → no floor, no record, byte-identical edge | **IMPLEMENTATION-TIME, ABSENCE-AWARE** — `test_absence_is_no_evidence` EXISTS and stands NOW (0026-R11-1): in the draft state it PROVES the invariant holds vacuously (no agreement machinery in `src/`, mechanically checked) and its behavioral cells activate automatically at graduation; the resolution guard exempts nothing |
| **V3** | the B02/B07 class floors at USE_ONLY — the two baseline vectors verbatim; and the floor NEVER raises (a quarantined edge stays quarantined) | **IMPLEMENTATION-TIME, ABSENCE-AWARE** — `test_laundered_relay_floors_use_only` stands now; vacuity proven pre-graduation, behavioral cells activate with `src/` |
| **V4** | an empty or malformed lexicon refuses at load; the lexicon has exactly one definition site | **CURRENT** — `test_the_lexicon_refuses_a_vacuous_table_at_load` (0026-I13: the previous name had DRIFTED from the real test) |
| **V5** | the demotion-direction disagreement is recorded and counted with NO disposition change | **IMPLEMENTATION-TIME, ABSENCE-AWARE** — `test_demotion_direction_records_only` stands now; vacuity proven pre-graduation, behavioral cells activate with `src/` |
| **V6** | `Edge.agreement` is a structured record (markers + direction + lexicon version), None-omitted everywhere; both counters present on every result path; MCP strips; telemetry consumption DEFERRED (0026-R1-3 — no whitelisting without a 0015-conformant amendment) | **IMPLEMENTATION-TIME, ABSENCE-AWARE** — `test_agreement_carriers_complete` stands now (and the SHAPE is executable today via `agreement_shape_problems`); vacuity proven pre-graduation, behavioral cells activate with `src/` |
| **V6a** | the import boundary is MODE-SPLIT (0026-R2-2): default mode RECOMPUTES under the current lexicon (the §3d matrix — forged/malformed/foreign inputs resolve to the recomputation, counted, never consumed) and the floor runs at establishment; `restore=True` is trust-field-faithful per accepted `0005` P2 — field and disclosure verbatim, recomputation diagnostic-only; the field's export rides a FORMAT_VERSION bump per accepted `0025`, so an old reader refuses rather than silently drops | **IMPLEMENTATION-TIME, ABSENCE-AWARE** — `test_agreement_import_recomputes` stands now (the MATRIX itself is executable data today, byte-bound into both projections); vacuity proven pre-graduation; at graduation it FAILS LOUDLY until the full matrix drive is written — the one V-test that demands work at that moment, by design |
| **V7** | a marker-free store is byte-identical before and after | **IMPLEMENTATION-TIME, ABSENCE-AWARE** — `test_no_markers_is_byte_identical` stands now; vacuity proven pre-graduation, behavioral cells activate with `src/` |

### 6a. The acceptance measurement gate

The quantitative claim is GENERATED from the aggregate — data to data,
nothing to hand-edit or drift (0026-EVIDENCE-R4-2: round 3 shipped a
217-vs-220 drift with no binder; round 4 shipped a lex-8 headline over
a lex-9 aggregate because the binder searched two substrings anywhere
in the file — the block below is byte-bound at the verify entry point):

<!-- GENERATED:fp-claim (measure_false_positives.py — byte-bound to fp_aggregate.json; do not hand-edit) -->
**MEASURED, under lexicon `0026-lex-10` (adjudication schema 7, census-only): 439 fires of 68,479 grounded first-person triples = 0.64% at the bound; the 2% gate is CLEARED (UNDER); 0 fires restrict via the ambiguous class only; 287 suppressed by the directional rule; coverage (the M-2 reach diagnostic, not recall) 220 of 3,898 = 5.6%.**
<!-- /GENERATED:fp-claim -->

Re-measured at every lexicon revision (rounds 1-4); lex-7 through
lex-10 measure identically on this corpus — each round's shapes are
absent from the own-use population, which for lex-9's artifact
carve-out is exactly why it bought nothing and was pure laundering
risk (R4-1: removed in lex-10). The head construction IMPROVED the
bound — nearest-token misreads of user subjects had been counted as
fires. The GATE itself is part of aggregate validity
(0026-EVIDENCE-R2-1): an over-gate record refuses absent a separately
validated adjudication artifact, and FP-MEASUREMENT.md's shipped
figures are mechanically bound to the aggregate at the verify entry
point. **The live over-gate path is CREATABLE (0026-EVIDENCE-R7-1:
measurement used to validate before emitting, so an over-2% result
demanded the adjudication its own outputs exist to enable — a
bootstrap deadlock, executed by the reviewer):** fresh measurement
validates in BOOTSTRAP mode — structural problems still refuse, but
an over-gate rate is a reported STATE (`OVER — NEEDS ADJUDICATION`,
its own exit code), the aggregate and the census worklist are
emitted, and acceptance is never claimed; the `--aggregate` verify
entry keeps refusing an over-gate record absent the bound
adjudication and co-verification. The end-to-end pipeline —
measurement → emission → worklist → both censuses → final
verification — is exercised through the real entry points by a
standing test over the shipped synthetic fixture (`e2e_fixture/`,
the reviewer's requested artifact). The cross-anchor is not silently
substitutable on the verify path: `--peer-anchor` there requires the
explicit `--fixture` declaration, which brands the run's output as
NOT acceptance evidence (research's round-7 pre-seal: a
documentation-only guarantee — the round-5 `archives_dir` class —
made mechanical).
The pre-commitment fired a third time on the way: lex-5's verb
expansion measured at 1.24% and READING THE FIRES showed the nominal
homographs (notes/added/adds/emails) were noise — lex-6 keeps their
unambiguous inflections and the rate settled at 0.70%. RECALL is now
measured, not enumerated: held relay cells across the verb classes in
the lexicon matrix must fire, and removing `claimed` alone is a red
matrix. The pre-commitment fired on the way here twice: lex-1 came in at
8.20% and NARROWED; lex-2 cleared at 0.61% and was then found
directionally unsound by external round 1 (proximity, not authorship)
and REWRITTEN as a grammar. **The lex-1 claim is NARROWED honestly
(0026-EVIDENCE-R1-1): lex-1's implementation was never committed — its
8.20% figure and cause analysis are recorded PROSE HISTORY in
`FP-MEASUREMENT.md` and in `relay_lexicon.py`'s header, not a
reproducible artifact; lex-2 through lex-4's implementations and
aggregates are the reproducible record.** What ships:
`measure_false_positives.py` (measure mode AND `--aggregate` verify
mode), the detector, its adversarial cell matrix, and a counts-only
`fp_aggregate.json` under a CLOSED validator — schema and types closed,
internal consistency enforced (fires ≤ population, splits ≤ fires,
coverage numerators ≤ denominators, the lexicon version must be the
shipped one), and the cache manifest CROSS-CHECKED against the
0011/0025 subject aggregate, which was derived from the same cache by
a different script and ships beside this one. **The whole-corpus
figures themselves (fires, suppressed, coverage) are RECORDED ONLY:
they reproduce with `--cache` on the measuring host and NOT from the
archive alone** — the archive verifies shape, consistency and the
manifest anchor, and says so in its own output. The measured rate is
an UPPER BOUND, not an estimate — every fire is a *candidate* false
positive, and deciding which of its own fires are false with the
detector would be self-assertion; hand-labelling a sample puts the
true rate well under the bound. The M-2 coverage figure (in the
generated block above — the block is the ONE carrier of every §6a
figure) is itself a lower bound on the source-naming share M-2 names,
since that subset cannot be identified without labelling the whole
population. **Scoped precisely (research,
pre-seal read-forward): this figure is a lexicon-reach diagnostic over
the `third_party_claim` NOTE population — records that are already
quarantined. It is NOT recall over the check's real target, the
concrete-relation laundering population (the B02/B07 class that
bypasses quarantine), whose recall has a different denominator no
archive-local number measures. A laundering-recall probe joins the
evidence when a labelled corpus for that population exists; until
then, nobody may read 5.6% as "the check catches 5.6% of relays".**

**The adjudication path is RECORD-BOUND and confidence-bounded
(0026-EVIDENCE-R4-1, discharging research's round-3 forward notes —
external round 4 made both blocking: schema 2 accepted
true_positive=100/false_positive=-50 because labels only had to sum to
size, and the sample digest was regex-checked but never opened).**
What SHIPS is the CONSTRUCTION — the validator, its standing attack
cells, and a worked, clearly-synthetic end-to-end example under
`specs/evidence/0026/adjudication_example/` — never live artifacts:
the shipped aggregate is UNDER the gate, so no live adjudication
exists or can exist, and the live `fp_adjudication_sample.jsonl` +
`fp_adjudication.json` MATERIALIZE only if the gate is ever exceeded
(0026-PACKAGE-R5-1: a round-4 carrier said the manifest "ships",
which overstated a dormant path — swept). When the path activates:
the aggregate carries `fire_digests` — a content-free one-way digest
per fire — and the manifest labels members OF that population, one
`{"fire": <sha256>, "label": "tp"|"fp"}` line each. The verifier
OPENS the manifest (undecodable bytes are a structured refusal, never
a crash — 0026-EVIDENCE-R5-3), hashes it against `sample_sha256`,
checks membership and uniqueness, and DERIVES the counts by counting
labels — the record carries no count carriers to disagree with, and a
derived count cannot be negative or exceed the sample. **There is NO
selection construction left to attack: every adjudication is a
CENSUS (0026-EVIDENCE-R6-1, ending the selection class at face
EIGHT). The class history earned this: round 4's seed hashed the
whole host-produced aggregate (a decision-irrelevant field was a
nonce); round 5's archive-sidecar seed rested on an unguaranteed
non-precomputable first seal; the projection seed enumerated and
justified every basis byte — and the reviewer showed `fire_digests`
itself is a host-produced identifier, shape-checked but never
recomputed from the cache, so varying ONE digest while holding the
semantic population fixed still shopped the draw. "Decision-read"
does not make a host-produced identifier non-choosable. Eight faces
across three review streams establish the class result: no sampling
construction over a host-produced population survives. So the
manifest labels EVERY fire, exactly — no draw, seed, size choice, or
confidence bound exists.** The decision is the EXACT labelled share:
`accept` requires bound × share ≤ 2%. The residual trust surface is
exactly two things. (1) The per-fire LABELS — and because a census
makes the honest and the fraudulent adjudication cost the SAME
labour, cost pressure tempts mislabelling rather than
labour-skipping. Independent label co-verification is therefore
MECHANICALLY BOUND, not a protocol promise (0026-EVIDENCE-R7-2 made
the round-6 rider checkable: a host-only all-tp census validated
clean): the adjudication record binds TWO census manifests — the
host's and an independent co-verifier's, same grammar, each opened,
hashed, and population-checked — and the decision runs on the
FAIL-CLOSED UNION of their fp labels (the host's incentive is to
under-label fp, so either party's fp counts), with disagreements
counted. A record without the co-verification manifest refuses:
host-only labels are not an adjudication. **What the binding does NOT
establish (research's round-7 pre-seal, the arc's own lesson turned
on itself): co-verifier INDEPENDENCE. Both manifests sit beside the
record, and nothing mechanical stops one party writing both — the
union then protects nothing. Independence is a PROCESS guarantee,
stated precisely like label honesty: the co-verification census is
produced by a party the measuring host does not control (in this
programme, research), and that separation is witnessed by the review
ledger, not by the validator. A signature apparatus for a dormant
path would itself become attack surface; if the path ever goes live
under adversarial hosting, an identity binding becomes its own
amendment.** Judgeability is provided by
the FULL-CONTENT worklist (`--worklist`): one line per fire — digest
plus rel/note/obj verbatim — LOCAL-ONLY corpus content, never
shipped (truncated previews had made distinct fires
indistinguishable). (2) The population's correspondence to the cache — each fire digest
is the sha256 of its canonical rel/note/obj triple plus an occurrence
ordinal (order-invariant: the ordinal enumerates occurrences of each
distinct triple, so the digest set does not depend on cache traversal
order), and the RE-RUN POPULATION CO-VERIFICATION with `--cache` on
the measuring host is the sole population↔cache check and is likewise
REQUIRED, never optional. The population is a deterministic function
of the cross-anchored cache and the versioned lexicon: it cannot be
shopped without changing the cache (the cross-anchor catches) or the
lexicon (versioned).

The standing rule, unchanged: before this spec is accepted, the
lexicon's false-positive rate is MEASURED on the existing extraction
cache (research's corpus, counts
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
promise). **Scoped further to the STATED VERB SET (research red-team):
the §3a classes — reporting, assertion, transmission, professional
judgment — and their held recall cells; a relay using a verb outside
them is a stated limit, not a silent one, and adding a verb is a
lexicon version with a re-measured §6a rate.** The claim ships WITH ITS DENOMINATOR: the §6a measurement run
also reports the lexicon's coverage over the cache's source-naming note
population, so "matches the lexicon" is a measured fraction of the
naming population, not an implied whole. We will NOT say the check
catches relays that name nothing (the 2/4 empty-note movers bound that
honestly), will not call it extractor correctness, and will not claim
bite before an unplanted catch (§6a).

## 9. Brief for the external reviewer

*(Internal review is CONTINUOUS and its authoritative record is the
structured ledger in `specs/reviews.py` — seven internal rounds at
the time of the round-4 pre-seal fold [0026-PACKAGE-R3-1: this brief previously said
"two rounds", frozen at the pre-external state while research's four
post-fold pre-seal passes went unnarrated here; the count is now bound
to the ledger by a standing test, so this prose cannot silently
underclaim again]. Rounds 1–2 were the pre-external design reviews
(PASS WITH AMENDMENTS with all three questions ruled; PASS
diff-verified); rounds 3–7 are research's pre-seal red-team passes on
the round-1 through round-4 folds, each with its own findings and
closure rows. The questions below are what we most want you to attack;
research's rulings are recorded in the Version row and are themselves
fair game.)*

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
   honest mechanism or a flag nobody consumes? We claim Q5's future
   round is the named consumer, and the operator counter is a local
   surface until a 0015-conformant amendment [carrier swept,
   0026-R2-3: this row previously claimed telemetry as a consumer].

## 10. Open questions

| # | question | state |
|---|---|---|
| **V-Q1** | should the answer surface RENDER the attribution for floored records ("per the vet: …") rather than the generic use-only treatment? | design — the L3 qualified-answer lever's territory; needs the gate's owner. Prior evidence when that round runs (internal round 1, m-4): the baseline's B02 answer already rendered content-derived attribution ("as reported by their doctor") while the edge sat MENTIONABLE — the floor plus existing prose attribution may be most of the answer |
| **V-Q2** | does the agreement record ever feed `0024` Q5's assertion completion, and under what evidence standard? | deferred to Q5's own round, by A1's design |

## 11. Changes in v5 — the round-1 fold (2026-08-29)

External round 1 returned FOR MAJOR AMENDMENT: three specification gaps
and two evidence/package failures, none touching the restrict-only
spine, which the reviewer called promising. Every finding reproduced
before fixing.

**0026-R1-1 — the directional detector confused proximity with
authorship.** All five executed counterexamples confirmed at the shipped
code. §3a is restated as a directional GRAMMAR (agent governs; passive
recipients inert; clause-bounded subjects; ambiguous pronouns restrict
with a counted, explicitly conservative outcome; bare participles
attribute nothing), the five counterexamples ride verbatim in the
lexicon's cell matrix (53 cells) and the test surface carries the
generated voice × identity × clause cross-product. The mutation matrix
was updated with the fix rather than around it: one lex-2 mutant became
harmless by construction under the grammar (the possessive-as-subject
mutation — the scan resolves the noun head) and was RETIRED with its
reason stated, replaced by mutants of the new load-bearing rules (agent
neutered, skip-tokens dropped, ambiguity dropped — the last made
killable by teaching the validator to check the CLASS of a restriction,
since ambiguous-vs-inbound is invisible at the match-bool surface). §6a
re-measured: 0.70% (481/68,479 under lex-6 — the lex-4 grammar pre-empting research's coordination/elision/nesting shapes, plus the recall-driven verb expansion their red-team then required: `claimed` and the assertion/transmission/professional-judgment classes, the advice class ruled OUT with its reason, and the nominal homographs narrowed by reading the lex-5 fires per the §6a discipline; recall is now MEASURED via held matrix cells and the claimed-removal mutant), gate still cleared.

**0026-R1-2 — the portable carrier had no import-boundary contract.**
`Edge.agreement` is redesigned as a structured record binding markers,
DIRECTION and LEXICON VERSION, and §3d's import matrix is total:
recomputation under the current lexicon governs every row (absent,
forged, malformed, foreign-version, direction-disagreeing), the
incoming value is diagnostic only (counted, then discarded), and the
outcome is fail-closed in both directions.

**0026-R1-3 — telemetry did not satisfy 0015's consent contract.**
DEFERRED, not constructed: v1 ships the counters as local operator
surface only, a conforming implementer MUST NOT whitelist them, and
the widening risk the reviewer named (payload growth on
already-consented installations) is closed by there being no payload
membership to widen. A future amendment that consumes them adds 0015
to Spec-Requires with the complete consent construction.

**0026-EVIDENCE-R1-1 — the measurement was self-asserted.** The
aggregate now has a closed validator (schema, types, internal
consistency, the shipped-lexicon version pin) with the cache manifest
cross-checked against the 0011/0025 subject aggregate — same cache,
different script, ships beside it; `--aggregate` is a real verify mode
on the entry point; the reviewer's three executed tamperings (fires→0,
coverage→10⁶, lexicon→lex-999) are the mutation matrix's first three
cells and all refuse; whole-corpus figures are labelled RECORDED ONLY;
marker-table KEYS must be members of the shipped closed lexicon (the
census C3 lesson, privacy and correctness in one rule: a foreign key
could carry corpus content into the shipped record, and a marker
outside the lexicon cannot have fired); and the lex-1 "both passes
ship" claim is NARROWED honestly — lex-1's implementation was never
committed, so its 8.20% is prose history, not a reproducible artifact.

**0026-PACKAGE-R1-1 — candidate identity was contradictory yet
verified.** The round-1 SENT row is corrected in place with the
correction visible; candidate revision is now a STRUCTURED
`candidate=` field on SENT rows, bound to `package_identity.py`'s
record by the identity gate (disagreement refuses; standing test); and
the internal-first miss is acknowledged rather than papered over: the
v4 measurement amendment went external without a fresh internal pass —
this v5 fold is queued for research's red-team pass before its seal
(their standing offer; currently deadline-deferred).

## 12. Changes in v6 — the round-2 fold (2026-08-29)

External round 2 returned FOR MAJOR AMENDMENT: each round-1 closure had
a material seam. Every finding reproduced before fixing.

**0026-R2-1 — the "grammar" still used token proximity.** All three
executed counterexamples confirmed: a modifier's object read as the
subject (*"the doctor treating the user said"*), a determiner-separated
conjunct losing its co-source (*"the doctor and the user said"*), and a
curly apostrophe defeating tokenization (*"confirmed by the user's
doctor"*). lex-7 replaces the nearest-token scan with an explicit HEAD
CONSTRUCTION (§3a): forward clause reading, first-noun-after-
determiners/possessives as head, post-head modifiers inert, coordinated
co-heads determiners and all, Unicode apostrophes normalized, relative
pronouns as modifier-openers. The reviewer's requested GRAMMAR-ORACLE
CORPUS is generated, not hand-picked: a cross-product of subject-head ×
modifier × conjunct × apostrophe form with expectations DERIVED from
the constructions — and it earned its keep immediately, catching two
further defects during its own construction (relative pronouns misfiled
as clause breakers; the scan window beheading long subjects). §6a
re-measured under lex-7: 0.64% (439/68,479) — the head construction
improved the bound.

**0026-R2-2 — portability contradicted accepted contracts.** The
import boundary is MODE-SPLIT: `restore=True` is trust-field-faithful
per accepted `0005` P2 (field and disclosure verbatim, recomputation
diagnostic-only, no re-flooring), default mode recomputes and floors;
and the field's export rides a FORMAT_VERSION bump per accepted `0025`,
so an old reader REFUSES rather than silently drops — the
new→old→re-export cycle that would shed Q5's carrier cannot begin. The
full {format era × mode × field state} matrix is in §3d.

**0026-R2-3 — the deferral was not carrier-complete.** §3c's "consumed
by telemetry from day one" and §9's "Q5 + telemetry" swept with visible
correction notes; the deferral test now scans EVERY carrier (a
whole-file occurrence check tolerating only quoted sweep notes), not
§3d alone.

**0026-EVIDENCE-R2-1 — the gate and the doc are bound.** The validator
now computes the rate and REFUSES an over-gate record absent a
separately validated adjudication artifact (the reviewer's fires=2,000
tampering is the standing test); FP-MEASUREMENT.md's shipped figures
(headline, pass-table column, coverage) are mechanically compared to
the aggregate at the verify entry point; every stale passage the
reviewer named is swept. One live catch during the sweep: a coverage
figure typed from memory (219) refused against the artifact (220) — the
binder gained the coverage facts in the same commit.

**Research's round-2 pre-seal pass (structured as internal rounds 5–6
in `reviews.py`)** found two more, both folded before this seal:
comitative quasi-coordinators (*"the user, along with her vet, said…"*
— three genuine relays silently unrestricted; the co-source class one
syntactic layer up, and exactly the generator-axis gap: the oracle
could not catch what it did not generate; lex-8 adds the closed
comitative set to the head scan AND the comitative axis to the
generator, with the third-person self-possessive consistency fix
riding) — and **the adjudication-artifact bypass, this arc's signature
defect landed in this fold's own new gate**: the over-2% clause CLAIMED
"separately validated" and CHECKED `is_file()`, so an empty `{}` beside
a 5%-fires aggregate produced "aggregate VALID". The adjudication is
now READ and VALIDATED — closed schema, non-vacuous labelled sample,
blank-verdict refusal — and BOUND to this exact aggregate's lexicon
version and fire count, so a stale verdict cannot carry a different
record; the empty-file and stale-binding cases are standing tests, and
the legitimate labelled bypass is proven alive.

**0026-PACKAGE-R2-1 — one source for measurements; internal history
structured.** The stale closure row (lex-3/32 cells/0.60%) now derives
its figures from the aggregate and validator rather than restating
them; research's v5 pre-seal pass is recorded as structured internal
rounds 3 and 4 (question (a) clean; question (b) blocked-folded-
re-verified), not SENT-row narration.

## 13. Changes in v7 — the round-3 fold (2026-08-29)

External round 3 returned FOR MAJOR AMENDMENT: five findings, each a
seam in a round-2 closure. Every finding reproduced before fixing.

**0026-R3-1 — the head grammar still laundered two shapes.** `or` was
not a coordinator ("the user or the doctor said…" — a POSSIBLE
third-party speaker restricts), and lex-8's self-possessive fix
over-generalized: "my own doctor" is a possessed third-party PERSON,
not a user-authored artifact. lex-9: `or` joins the coordinators, and
the self-possessive rule is split ARTIFACT-vs-ENTITY over a closed
artifact set (note/account/words/message…), applied in both the
subject scan and the agent/frame path. The oracle gained the
disjunction axis and the own-entity subject heads; re-measured
identical (439/68,479 = 0.64% — the shapes are absent from the
own-use population).

**0026-R3-2 — the import matrix's restore-malformed cells.** An
imported `AgreementRecord` joined §2c's untrusted-input table, and the
§3d matrix gained the cells the "complete" claim lacked: a new-format
`restore=True` record with a MALFORMED field RAISES with nothing
written (verbatim restore into a typed carrier is impossible for
garbage — the R1-4 ruling applied to the restore path; validation
ordered BEFORE any write), while default-mode malformed stays
treated-as-absent (recomputation is total there anyway).

**0026-EVIDENCE-R3-1 — the adjudication path is a DECISION now.** The
reviewer supplied a verdict reading "REJECT: … remains over the 2%
gate" and it carried the record — the validator checked shape and
blankness, never meaning. Schema 2: `verdict` is the closed enum
{accept, reject}; the ADJUDICATED rate (bound × labelled-FP share) is
COMPUTED and must clear the gate — an accept that disagrees with its
own numbers refuses; the sample has a minimum (50, or every fire when
fewer); and the artifact is digest-bound to the exact aggregate's
canonical bytes plus the local labelled-sample file. The reviewer's
REJECT case, the free-text case, the lying-accept, the tiny sample and
the wrong-digest are all standing refusals, with the legitimate
labelled bypass still proven alive.

**0026-EVIDENCE-R3-2 — the candidate spec is a bound carrier.** §6a
carried 217 beside the aggregate's 220 — the binder covered the
measurement doc and not the spec. Re-derived, and `spec_problems`
binds the §6a headline rate and coverage figure to the aggregate at
the verify entry point, with the bite proven in a standing test.

**0026-PACKAGE-R3-1 — the round count derives from the ledger.** §9
said "two rounds" beside a six-round structured ledger. Swept with the
correction visible, and a standing test binds the stated count to
`reviews.py`, so the prose cannot silently underclaim again.

## 14. Changes in v8 — the round-4 fold (2026-08-29)

External round 4 returned five findings: every named round-3 example
was fixed, and each new closure MECHANISM carried a blocking seam. The
common shape, named so the next fold cannot repeat it: three of the
five were checks that verified PROSE NEAR the property instead of the
property (substring binders, a half-swept header, a self-asserted
sample), and the fold answers with GENERATED carriers — a figure or a
matrix that is rendered from its artifact cannot drift from it.

**0026-R4-1 — ownership is not authorship (lex-10).** lex-9's closed
artifact set read every owned noun as user-authored; "my own record
reported a diagnosis of cancer" went outbound with no restricting
marker, though a record the user OWNS is routinely produced by a
doctor or a bank — semantic authorship inference, reintroduced one
rung up, in the laundering direction. lex-10 REMOVES the carve-out
entirely: no noun class carries an authorship inference; a possessed
head restricts whoever possesses it, artifacts included. "My own
notes say…" now over-restricts — priced, counted, reversible — and
the ownership-vs-authorship axis joins the oracle with the reviewer's
cells verbatim plus a standing behavioral relapse mutant. Re-measured:
439 of 68,479 = 0.64%, identical to lex-7/8/9 — the own-artifact
shapes are absent from the own-use population, which is why the
carve-out bought nothing and was pure risk.

**0026-R4-2 — one decision table, two generated carriers.** §2c and
§3d disagreed about default-mode malformed imports (RAISES vs
recompute) with §2c's columns displaced, and the matrix test checked
substrings. `import_matrix.py` is the ONE structured table now; the
§2c row and the §3d boundary table are both GENERATED from it and
byte-bound, so the representations cannot diverge.

**0026-EVIDENCE-R4-1 — the adjudication is record-bound (the
signature defect's sixth face).** Schema 2 accepted
`true_positive=100, false_positive=-50` (labels only had to sum to
size) and its sample digest was regex-checked, never dereferenced.
Schema 3 compares data to data: the aggregate ships `fire_digests`
(one content-free digest per fire), the labelled sample is an
ON-DISK manifest *(round 5 corrected this passage's original "SHIPPED"
— no live manifest can exist while the aggregate is under-gate; the
construction plus a worked synthetic example ship, 0026-PACKAGE-R5-1)*
whose bytes are opened and hashed against `sample_sha256`,
membership and uniqueness are checked against the population, the
counts are DERIVED by counting labels — no count carriers exist to
lie — and `accept` requires bound × Wilson-95 UPPER confidence ≤ 2%,
never the point estimate (research's round-3 forward notes, made
live; the at-the-bar cell where the point estimate passes and the UCB
refuses is a standing test). The reviewer's exact bypass and seven
sibling attacks are standing refusals; the legitimate binding is
proven alive.

**0026-EVIDENCE-R4-2 — the §6a claim is generated.** The binder
searched two substrings anywhere in the file; the headline still said
lex-8 over a lex-9 aggregate and 9,999/lex-999 mutations passed. §6a
now carries a GENERATED block rendered from the aggregate
(`render_spec_claim`), byte-bound at the verify entry point and
required to sit inside §6a; the prose figure carriers are swept into
the block's custody.

**0026-PACKAGE-R4-1 — the header row is generated.** Round 3's
verdict named the Internal-reviewers header AND §9; the fold swept
only §9 — a half-swept carrier set, the carrier-completeness class.
The front-matter row is now rendered from the structured ledger
(`reviews.internal_reviewers_row`) and byte-bound, and a static
"READY FOR EXTERNAL" claim is refused outright: readiness is the
ledger's state to derive.

**Package feedback applied:** the record-bound label-manifest
CONSTRUCTION the reviewer has asked for since round 2 now exists, with
a verifier that opens the manifest and reproduces the decision
*(round 5 corrected this passage's original "now EXISTS as a…
manifest": no live manifest can exist under-gate — what ships is the
construction and, since round 5, the worked synthetic example in
`adjudication_example/`, 0026-PACKAGE-R5-1)*; and the change manifest
marks concurrent guarded 0011 implementation files as out-of-scope
for this line's review.

**Pre-seal fold (research's round-4 red-team, internal round 7 —
2026-08-29, before the v5 seal):** **0026-I7-1 (blocking)** — schema 3
closed label-honesty but not SAMPLE SELECTION: the seed was recorded,
never re-drawn or bound, so a hand-picked honestly-labelled sample
voided the Wilson gate. Closed with the CANONICAL seeded draw above;
the hand-picked and seed-shopping attacks are standing refusals.
**Addendum
(research's co-verify, folded same-day rather than fast-followed):**
size was the last host-chosen selection input — each size is a
different canonical draw, so a host could size-shop the multiple
comparisons. Research MEASURED it inert on this aggregate (best
shoppable UCB 0.134 vs honest census 0.137) but measured-inert is
exactly what five external rounds turned into findings: size is
CANONICAL now (census up to the fixed limit, else the limit), the
census branch decides on the exact share, and the size-shopping and
short-census attacks are standing refusals. The fixpoint order is
confirmed required: the canonical seed hashes the AGGREGATE-ONLY
bytes — including the adjudication would be circular
(seed→draw→manifest→adjudication→seed) — so the draw is fixed the
moment measurement ends and the adjudication is strictly downstream.
**0026-I7-2 (moderate)** — the byte-equality binders verified drift,
not renderer correctness: an off-by-one renderer re-renders byte-equal
and passes. Every renderer now has an INDEPENDENT oracle test that
computes the figures straight from the artifact, with the off-by-one
renderer shown caught. **lex-10 verified CLEAN by monotonicity** — the
carve-out only ever spared, so its removal only adds inbound.

## 15. Changes in v9 — the round-5 fold (2026-08-29)

External round 5 confirmed three round-4 closures hold (lex-10, the
§6a generated claim, the ledger-derived header) and returned five
findings — three blocking. The recurring lesson sharpened twice: ANY
host-produced byte in a selection basis is a nonce, and a "generated"
claim is only as true as the projection actually coded.

**0026-EVIDENCE-R5-1 — the seed basis leaves the aggregate (face
seven of the selection-freedom class).** Round 4's "canonical" seed
hashed the ENTIRE host-produced aggregate, so a decision-irrelevant
field (`suppressed_by_direction_only`, executed by the reviewer) was
a nonce: vary it, hold population and labels fixed, and swing the
draw from an accepting sample (167/500 FP) to a refusing one
(232/500). §14's "fixpoint order confirmed required" reasoned about
the right ordering over the WRONG basis — the whole aggregate is
host-produced. The seed is EXTERNAL and POST-COMMITMENT now: derived
from the committed sha256 sidecar of the sealed archive that first
shipped the aggregate (schema 4: `sealed_archive` joins the record;
name grammar checked before any path is built; the aggregate↔archive
pairing is the reviewer's extraction check, stated as protocol). The
nonce-invariance, missing-witness and traversal-name attacks are
standing cells.

**0026-R5-1 — §2c is a PROJECTION now.** Round 4's `render_2c_row`
hard-coded its text beside `MATRIX` while claiming generation — the
name-vs-behavior class: a mutated matrix regenerated §3d, §2c stayed
contradictory, and the binder returned clean. Every mode-dependent
§2c clause is now built from the matrix rows' own operative text, and
the source-level mutation test drives a changed outcome through BOTH
renderings and both binder halves.

**0026-PACKAGE-R5-1 — the "SHIPPED manifest" claim corrected
visibly.** No live adjudication artifacts can exist while the
aggregate is under-gate, yet three carriers said the manifest "ships"
/ "now EXISTS". Every carrier now states the accurate claim — the
CONSTRUCTION ships; live artifacts materialize over-gate — and the
worked, clearly-synthetic end-to-end example
(`adjudication_example/`: demo aggregate, v0 witness, census
manifest, schema-4 record) ships and is validated FROM DISK by a
standing test.

**0026-EVIDENCE-R5-2 — the doc denominator is derived.** The doc
binder hard-coded `3,898`; a 9,999 denominator validated clean
everywhere while the doc still said 3,898. The needle now derives
numerator, denominator AND percentage from the aggregate; the
reviewer's mutation is a standing cell.

**0026-EVIDENCE-R5-3 — undecodable bytes refuse, never crash.** A
hash-bound manifest containing invalid UTF-8 raised an uncaught
UnicodeDecodeError. Both adjudication files now return structured
refusals on decode failure, with standing cells for each.

**Pre-seal completion (research's round-5 pass, folded same-day —
2026-08-29, before the v6 seal):** their pass CLEARED the seal and
named two forward hardenings, both folded rather than fast-followed
(two consecutive rounds converted signed-off seed mechanisms; a
stated gap does not ride into a sealed package). (1) The
archive-sidecar seed's first-seal pre-selection gap: replaced by the
NONCE-FREE PROJECTION seed above (schema 5) — simpler, no archive
apparatus, precomputable-but-harmless since every basis byte is
decision-read or cross-anchored; the nonce-invariance and
population-sensitivity cells stand. (2) The §2c head-projection's
untested invariant: heads must be pairwise distinct or the projection
under-distinguishes rows — `_assert_heads_distinct` refuses a
colliding matrix at render time, with the collision cell standing.
Research also confirmed the shipped corpus needs no seed at all (439
fires is a census, the draw seed-independent) and the v0 demo witness
question is moot (the example carries no witness under schema 5).

## 16. Changes in v10 — the round-6 fold (2026-08-30)

External round 6 narrowed the verdict (NARROW amendment; the
trust-model architecture stable; four round-5 closures confirmed) and
returned two blocking seams plus two defects. Both blocking closures
are terminal simplifications rather than ninth patches.

**0026-EVIDENCE-R6-1 — sampling ENDS; every adjudication is a CENSUS
(face eight of the selection class).** The projection seed enumerated
and justified every basis byte, but `fire_digests` is itself a
host-produced identifier — shape-checked, never recomputed from the
cache — and varying ONE digest while holding the semantic population
and labels fixed swung 159/500 FP (accepted) vs 234/500 (refused).
The reviewer's sentence is the class lesson verbatim: "decision-read"
does not make a host-produced identifier non-choosable. Of their two
offered closures, census-every-population deletes the attack surface
outright: schema 6 carries `{"size"}` only, the manifest must label
exactly the population, the decision is the exact labelled share, and
the draw/seed/size/Wilson machinery is REMOVED (everything three
rounds of hardening built — the right outcome; eight faces proved no
sampling construction over a host-produced population survives). The
census boundary cells stand: partial census, under-labelled census,
swapped member, smuggled seed, and the exact-share bar driven from
both sides (1370/3423 refuses at 2.0014%, 1369 accepts at 1.9999%).

**0026-R6-1 — the restore/foreign-version cell is SPECIFIED.** A
well-typed record with current-valid markers under a foreign lexicon
version and `restore=True` was unrecognised but not malformed — no
stated outcome. RULED: restored VERBATIM — the version field exists
to mark provenance, recomputation stays diagnostic-only, and refusing
would break restore round-trips of exports made under older
lexicons. The cell joins `MATRIX` (the one carrier) and both
generated projections carry it.

**0026-PACKAGE-R6-1 — the half-swept-carrier class, closed
structurally.** The Version row still described the discarded
archive-sidecar seed, the round-6 SENT row still said v0
witness/schema 4, and the example README claimed a generator the
package did not ship. All corrected VISIBLY (here, in the Version
row, and in the ledger); and the reviewer's structural fix is
adopted: the adjudication revision has ONE generated carrier —
`ADJUDICATION_SCHEMA` in `measure_false_positives.py` — read by the
validator, the example's now-SHIPPED generator
(`adjudication_example/generate_example.py`, byte-identity-tested
against the shipped artifacts), the §6a generated claim block (which
now names the schema), and the packaged tests. Prose carriers no
longer number the revision.

**0026-EVIDENCE-R6-2 — the zero-denominator cell.** The round-5
denominator fix divided unguarded; `doc_problems` on a
zero-denominator aggregate crashed where the renderer guarded. The
needle uses the same guarded derivation and the zero cell stands.

**Pre-seal fold (research's round-6 pass, internal round 8 — folded
same-day, 2026-08-30, before the v7 seal):** their pass CLEARED the
seal, verified the census (decision exact, no dead sampling code) and
the digest derivation's order-invariance, endorsed the
expensive-escape-hatch incentive design, and found one moderate plus
two riders, all folded: **0026-I8-1** — the next half-swept carrier
after the one-schema fix is PROSE THAT RESTATES MECHANISMS, and it
was drifting already (`_validate_adjudication`'s docstring still said
"Schema 3" and "Wilson" two revisions after both were gone). The
docstring now names the mechanism's carriers instead of restating
them, and the live-prose sweep ran (history sections stand as
history). **The two riders** are §6a's explicit non-optional protocol
obligations above: re-run population co-verification (the sole
population↔cache check), and independent label co-verification — the
honest and the fraudulent census cost the same labour, so
co-verification is what separates them.

## 17. Changes in v11 — the round-7 fold (2026-08-30)

External round 7 (narrow; the v6 digest-nonce attack confirmed DEAD;
the foreign-version cell, generator byte-identity and zero-guard all
confirmed) returned three blocking findings and one moderate.

**0026-EVIDENCE-R7-1 — the bootstrap deadlock.** Fresh measurement
validated BEFORE emitting, so an over-2% result demanded the
adjudication that the emitted aggregate and worklist exist to enable
— the live over-gate census could never be created (executed: exit 1,
nothing emitted). Measurement now validates in bootstrap mode and an
over-gate rate is a distinct reported STATE (exit 3, aggregate +
worklist emitted, acceptance never claimed); the verify entry keeps
refusing. The end-to-end regression drives the real `main()` over the
shipped synthetic `e2e_fixture/` through every stage, and the
adjudication is looked for BESIDE the aggregate under verification.

**0026-EVIDENCE-R7-2 — co-verification is bound, not promised.** The
round-6 rider was a protocol sentence; the reviewer showed a host-only
all-tp census validating clean, truncated previews making distinct
fires indistinguishable, and a hashes-only manifest from which content
cannot be recovered. Schema 7: the record binds BOTH census manifests
(host + independent co-verifier, one shared grammar/reader), the
decision runs on the fail-closed fp-UNION with disagreements counted,
a missing co-verification refuses, and `--worklist` emits the
full-content local-only worklist that makes labelling judgeable.

**0026-R7-1 — foreign-marker validity is mechanical.** GRAMMAR
MEMBERSHIP IS VERSION-SCOPED: under a foreign lexicon version the
vocabulary is unknowable, so markers validate as OPAQUE closed shapes
only (the reviewer's exact `markers=['future_marker']` case is named
in the matrix cell); the malformed row's out-of-grammar rule applies
only under the CURRENT version. Both projections carry it.

**0026-PACKAGE-R7-1 — operational prose swept; the claim
constrained.** The `--sample` help still said "draw N fires"; two
test comments still said projection-seed and v0-witness; and summary
prose hard-coded "schema 6" while claiming prose never numbers
revisions. Swept, and the one-carrier claim is now stated precisely:
CURRENT-summary carriers derive from `ADJUDICATION_SCHEMA` or omit
the number; HISTORICAL prose names the schema of its own round.

**Pre-seal fold (research's round-7 pass, internal round 9 — folded
same-day, 2026-08-30, before the v8 seal):** their pass CLEARED the
seal, ENDORSED the fp-union (false refusal is the safe failure
direction; a hostile co-verifier maximizes counted disagreements — a
loud signal with the third-labeller escape), and verified the
bootstrap state unreachable from verify. Two hardenings folded:
(1) co-verifier INDEPENDENCE stated precisely as a process guarantee
(above) — the mechanical binding proves two manifests exist, not that
two parties wrote them; (2) `--peer-anchor` on the verify path now
requires the explicit `--fixture` declaration and brands its output
as non-evidence — the guarantee is mechanical, not documentation.
Their optional rider (an over-gate state marker inside the aggregate)
is DECLINED with the reason recorded: a field derived from the
aggregate's own fires/total would be a second carrier of the same
fact, and duplicate carriers that can disagree are the drift class
this line spent six rounds killing; the verify gate computes the
state from the figures themselves.

## 18. Changes in v12 — the round-8 fold (2026-08-30)

External round 8 (narrow; ALL FOUR round-7 closures held — the new
findings are seams in the round-7 machinery itself).

**0026-EVIDENCE-R8-1 — census records are unambiguous.** The manifest
reader used plain `json.loads`, which keeps the LAST duplicate member:
`"label":"fp","label":"tp"` passed as tp, and hash binding
authenticated the ambiguous bytes without resolving their meaning —
the fp-union could be reduced. This is the 0011 EVIDENCE-R9-1 class
refound in new code. Duplicate members now REFUSE at parse
(`_strict_json`, an object-pairs hook) at every evidence boundary —
both manifests and the adjudication record — with duplicate-label and
duplicate-fire regressions.

**0026-R8-2 — the shape has numbers.** "Nonempty bounded strings" with
no bounds let conforming implementations accept different inputs. The
shape is DATA (`AGREEMENT_SHAPE`) with a RUNNING reference validator
(`agreement_shape_problems`) the future implementation must match:
closed keys, a bounded marker array, duplicates refused, the closed
direction enum, a bounded lexicon version under a closed pattern —
the EXACT numbers live only in §3d's byte-bound generated shape block
*(round 9 corrected this passage: it originally restated "16 markers"
beside an executable bound the I10-1 fold had measured down to 8 —
the restatement class, in the very section describing its closure;
prose no longer carries the numbers)* — with every bound driven at
the limit and one beyond by a standing test.

**0026-EVIDENCE-R8-3 — output paths cannot collide.** The bootstrap
wrote the aggregate, then opened the worklist with truncation —
`--emit-aggregate X --worklist X` destroyed the aggregate, either
output could overwrite `--cache`, and exit 3 was reachable without
both artifacts retained. Every path is resolved and cross-checked
BEFORE any write; aliases (relative or absolute) refuse; the
regressions drive same-path, relative-alias, and output-names-input.

**0026-PRIVACY-R8-4 — LOCAL-ONLY is enforced, not documented.** The
worklist now refuses any path inside the package tree, is written
mode 0600, and a standing package sweep refuses ANY .jsonl under
specs/ carrying the worklist line shape — a protection no rename can
evade, unlike the .gitignore pattern it supplements.

**Pre-seal fold (research's round-8 pass, internal round 10 — folded
same-day, 2026-08-30, before the v9 seal):** their pass RETURNED one
blocking finding — the NINTH face, asked for and delivered:
**0026-I10-1** — the R8-1 fold routed the two manifests through the
strict decoder but left plain `json.loads` at THREE evidence-boundary
reads (aggregate verify; peer cross-anchor; and the CACHE read, whose
raw-vs-parsed split — a raw-byte sha anchor over last-wins parsing —
was the genuinely exploitable form). The class recurred 11 days after
0011 closed it AND the closing fold missed three sites: vigilance
failed twice, so per research's ruling the unsafe form is now
UNREACHABLE — every evidence read routes through `_strict_json` (a
duplicate-key cache row counts unparseable), and a standing gate
refuses plain `json.load(s)` anywhere under `specs/evidence/` outside
a reasoned allowlist (legacy lines frozen at their current counts,
new files at zero). Their secondaries folded with it: the path-alias
guard compares `(st_dev, st_ino)` so a HARDLINK to the cache refuses;
and the shape bounds now carry their MEASURED basis — max distinct
markers per record is 2 over the full cache (2,349 records at 1, 64
at 2), so the count bound is 8 = measured ×4, and the longest shipped
member is 'on the advice of' at 16 characters, so the length bound 64
is ×4 (the §6a discipline applied to shape bounds: measured, never
taste).

**Second pre-seal fold (research's co-verify, internal round 11 —
folded same-day, 2026-08-30):** the I10-1 mechanism verified clean;
the GATE itself returned one finding — **0026-I11-1**: its allowlist
carried three slots of headroom in the very file it was built to
protect (a regex miscount: the implementation line was skipped and
the cited docstring mentions never matched, so 0026's true count was
0 against a cap of 3). Closed with research's two fixes: the gate is
EXACT-MATCH now — a count above OR below its pin trips, so a
miscalibrated allowlist catches itself, the same no-headroom
discipline every other carrier obeys — and AST-BASED, resolving
calls through import aliases (including bare `from json import
loads`) and judging safety per-call by the `object_pairs_hook`
keyword rather than per-line. The AST recount immediately corrected
one legacy pin the regex had undercounted — the rebuild proving
itself on first run. 0026's own pin is 0. Research's co-verify PASSED
and named one optional tenth-face hardening, taken same-day: the
safety predicate judged hook PRESENCE, not STRICTNESS —
`object_pairs_hook=dict` keeps the last duplicate and passed the gate
while staying vulnerable (demonstrated). The gate now accepts only
KNOWN-STRICT hooks by name (`_strict_pairs`, 0011's
`_no_dup_pairs`); any other hook counts as plain.

## 19. Changes in v13 — the round-9 fold (2026-08-30)

External round 9 (narrow; archive sound, all packaged tests passing).

**0026-R9-1 — one canonical AgreementRecord.** The carriers disagreed
in the machinery built to prevent it: §3d's stored direction enum is
`inbound | ambiguous | user_source` (user_source IS §3c's
demotion-direction record) while `AGREEMENT_SHAPE` said
`inbound | outbound | ambiguous` — the lexicon's INTERNAL reading
names, not the stored vocabulary. The shape now matches §3d exactly
(with the mapping stated: the lexicon's 'outbound' reading is stored
as user_source; 'outbound' itself refuses), `markers` has a minimum
of 1 (V2: no markers means no record — an empty array refuses), the
§18 prose that still said "16 markers" beside the executable 8
carries a visible correction and no longer restates numbers, and the
three inputs the reviewer named — user_source, outbound, the empty
array — are independent standing cells.

**0026-PRIVACY-R9-2 — the mode and the sweep both real.** O_TRUNC
applies 0600 only on CREATE, so a pre-existing 0644 worklist kept its
mode while the program reported 0600 — fchmod is explicit now, with
a pre-existing-file regression. The package sweep read only the first
line of `*.jsonl`; it now reads EVERY line of every UTF-8-decodable
file under specs/ whatever the suffix, with its scope stated
precisely (binary archives skip on decode failure).

**0026-EVIDENCE-R9-3 — the regression is probative.** The
duplicate-cache test passed on `returncode != 0`, which the peer
mismatch it introduced already guaranteed. It now builds a MATCHING
peer for the modified cache, requires the bootstrap state (exit 3),
and asserts the exact "1 unparseable" count — proving the
duplicate-key row was counted, not that something failed.

**Pre-seal fold (research's round-9 pass, internal round 12 — folded
same-day, 2026-08-30, before the v10 seal):** their pass CLEARED the
seal (R9-3 confirmed probative — it fails if the strict cache read
reverts; R9-2's fchmod verified) and named the R9-1 CLASS residual:
§3d and the shape were bound to each other, but the LEXICON reading
domain and the STORED enum were still two independent definitions
bridged by a prose comment — their mutant (a), executed: add a
lexicon reading value and nothing trips. Folded, though non-blocking
on the draft: `LEXICON_DIRECTIONS` declares the reading domain in the
lexicon itself; `LEXICON_TO_STORED` is an executable TOTAL mapping
(the 'outbound' reading stores as `user_source`; 'none' produces no
record); the shape's direction enum is DERIVED as the mapping's
image, never hand-listed; and the domain-equality test is the
standing form of the mutant — a new reading value with no mapping row
fails there instead of re-splitting the carriers. Their ask-2
carrier REGISTRY is built as consolidation + discipline: every
GENERATED marker in the spec must have a registered binder that runs
clean, so an unbound generated block is conspicuous by absence
("no fact unregistered" is a stated discipline; the mechanical half
is that no generated block escapes a binder). Their mutant (c)
folded: the package sweep's undecodable-file skip was itself an
evasion — a byte-level four-key fallback now flags undecodable
worklist-shaped content.

## 20. Changes in v14 — the round-10 fold (2026-08-30)

External round 10: **the design surface is READY — no new semantic
issue**; all six v9 corrections confirmed holding. Two package
moderates, both remnants of the restatement class v13 declared
closed:

**0026-PACKAGE-R10-1** — the R8-2 closure row still recorded "at most
16 markers" (written when the bound was 16, never re-swept after the
I10-1 measurement moved it to 8), and the boundary test's diagnostic
literal said "17 markers must refuse" beside a case that derives from
the shape. The closure row is version-neutral now (the exact numbers
live only in the generated §3d block, and the row says so), and the
diagnostic derives from `markers_max_count`.

**0026-PRIVACY-R10-2** — the "every line of every decodable file"
sweep silently skipped files over 8,000,000 bytes: an undocumented
exclusion a large worklist-shaped file evades. The size cap is
REMOVED — text files stream line by line and undecodable files
byte-scan in bounded 1MB chunks with an overlap window, so the scope
is total at bounded memory. The R9-2 closure evidence now runs BOTH
halves (the file-mode regression and the package sweep).

**Recorded, not silent (the reviewer's suggestion):** a draft-time
rendered preview of the eventual review-closure block would surface
closure-source drift before acceptance — a shared-renderer change
(`render_closure` currently generates blocks for accepted specs
only), noted here as a forward item for the next renderer amendment
rather than smuggled into this line's fold.

**Pre-seal fold (research's round-10 pass, internal round 13 — folded
same-day, 2026-08-30, before the v11 seal; run as the requested
read-as-the-ACCEPT-reviewer):** their pass CLEARED the seal and named
the one thing that would stop an ACCEPT — **0026-I13-1**: the §6
V-invariant check column was not S-list-honest. Six of seven named
tests did not exist: V4's name had DRIFTED from the real
`test_the_lexicon_refuses_a_vacuous_table_at_load`, and
V2/V3/V5/V6/V6a/V7 are IMPLEMENTATION-TIME obligations — 0026 is a
draft with no agreement mechanism in `src/` — presented as standing
checks. The design being ready is not the acceptance artifact being
honest. Folded: every §6 row is marked CURRENT vs
IMPLEMENTATION-TIME (graduating with `src/`), V4's name is corrected,
and one standing guard closes the restatement class's five bitten
carriers: every test name cited in the spec's live zone must resolve
to a real function (marked obligations exempt), and the shape-bound
digits may appear in marker/character context only inside generated
blocks.

## 21. Changes in v15 — the round-11 fold (2026-08-30)

External round 11: RETURN FOR NARROW ACCEPTANCE-GATE AMENDMENT — the
design surface REMAINS ready, both round-10 findings verified closed,
and the acceptance condition stated in terms: **no further design
round is needed.**

**0026-R11-1 — the six named checks EXIST now, absence-aware.**
Accurate IMPLEMENTATION-TIME labels were not enough: the resolution
guard exempted those rows, so the suite passed with none of the six
named tests existing — and PROCESS.md makes an invariant without an
executable check a hard gate. Per the reviewer's stated condition:
`test_absence_is_no_evidence`, `test_laundered_relay_floors_use_only`,
`test_demotion_direction_records_only`,
`test_agreement_carriers_complete`, `test_agreement_import_recomputes`
and `test_no_markers_is_byte_identical` are standing tests today. In
the draft state each PROVES its invariant holds vacuously — a
mechanical sweep that no agreement machinery exists in `src/`, which
FLIPS the moment implementation begins — and the behavioral cells
against the spec'd API activate automatically at graduation (V6a
fails loudly at that moment until the full matrix drive is written,
by design: it is the one obligation that demands work then). The
IMPLEMENTATION-TIME exemption is REMOVED from the resolution guard:
every test name the live spec cites must resolve, no exceptions.

The reviewer's suggestion — a generated §6 report mapping each
invariant to a collected test node — is recorded as a forward item
alongside the round-10 draft-preview note; the resolution guard
already binds name→function mechanically, and the report form waits
on the shared-renderer amendment.

**Pre-seal fold (research's round-11 pass, internal round 14 —
2026-08-30, before the v12 seal):** their verdict: **PASS — "I would
sign ACCEPT."** R11-1 met exactly; no landmines in the dormant
behavioral cells (every assertion verified against §3); the
field-name activation gate ruled load-bearing and correct
(token-choice is not an evasion surface — the token-grep is a
redundant tripwire in the safe direction); the restatement class
ruled mechanically closed. Two minor graduation-time refinements
folded same-day: V6's counters are exercised on the MARKERLESS path
too (both present at zero — an absent key is not a zero there
either), and V3's second clause is tested — a quarantined claim
carrying a marker stays QUARANTINED, because the floor never raises:
restrict-only means down or nowhere.

## 22. Acceptance (2026-08-30, external round 12)

**APPROVED FOR ACCEPTANCE — the design is FROZEN on the V1–V7/V6a
invariant surface.** R11-1 closed: all six named checks exist and
execute; the draft-state absence proof is mechanical; the resolution
guard carries no implementation-time exemption; V6a deliberately
becomes a failing tripwire until its full matrix is implemented.

**Implementation obligations (the reviewer's non-blocking note —
obligations, not another design round), owed when the mechanism
lands, alongside the standing S-list contract:**

1. strengthen V5's dormant branch with the counter assertion;
2. strengthen V6's dormant branch with the MCP surface-stripping
   assertion;
3. give V7 a FROZEN pre-feature oracle for byte identity (an export
   captured before the mechanism exists, so post-feature byte
   identity is proven against a fixed artifact rather than against
   the feature's own output).

Twelve external rounds and fourteen internal rounds, every fold
same-day. The Spec-Status flip to `accepted` in this revision is
authorized by the round-12 verdict.

## Review closure

*(Generated from `specs/reviews.py` and `specs/closure_findings.py` —
the per-round ledger, rendered; hand-edits are overwritten.)*

<!-- GENERATED:review-closure -->

**14 internal round(s) and 12 external round(s) with a returned VERDICT are recorded for `0026`; 12 package(s) were dispatched** — counted from `specs/reviews.py`, which is the source this block is generated from. A round appearing here and not there, or the reverse, is impossible by construction. **SENT rows are dispatch records, not outcomes**, and are labelled below so the two are never summed.

| round | date | findings raised (from `raised=`) | verdict (compressed) |
|---|---|---|---|
| internal 1 (verdict) | 2026-08-24 | 5 | PASS WITH AMENDMENTS (research) — the design is right and honours every discipline it inherits; two moderates, three minors, all three §9 questions ruled. The census was RE-DERIVED from the cache with the shipped script rather than recognised. M-1: §1's figures were the pre-correction values (183,41… |
| internal 2 (verdict) | 2026-08-24 | 0 | PASS (research) — diff-verified fold @ e60206e, no new findings; the provenance note took research's symmetric wording (both the drift and the trusting citation named as the failure mode). External-ready |
| internal 3 (verdict) | 2026-08-29 | 0 | RESEARCH PRE-SEAL RED-TEAM, question (a) — the fp_aggregate false-PASS surface: CLEAN, verified at code (closed typed schema, internal consistency, marker keys pinned to the shipped lexicon, lexicon_version pin, the 0011 cross-artifact manifest anchor refusing on absence AND mismatch; corpus-depende… |
| internal 4 (verdict) | 2026-08-29 | 1 | RESEARCH PRE-SEAL RED-TEAM, question (b) — BLOCKED the v2 seal: the verb list omitted `claimed` (the name of the relation 0024 quarantines) and high-frequency attribution verbs; §6a measures FP only and every matrix inbound cell used an in-list verb, so recall was unmeasured in two places at once. F… |
| internal 5 (verdict) | 2026-08-29 | 1 | RESEARCH ROUND-2 PRE-SEAL RED-TEAM (grammar half) — BLOCKED the v3 seal: COMITATIVE quasi-coordinators (along with / together with / as well as) introduce a co-speaker the lexical coordinator set cannot see; three genuine relays silently unrestricted, and exactly the generator-axis gap the pre-seal … |
| internal 6 (verdict) | 2026-08-29 | 1 | RESEARCH ROUND-2 PRE-SEAL RED-TEAM (binding half) — wiring and doc binding verified CLEAN, but the new 2% gate had a PROVEN false-PASS, this arc's signature defect in the fold's own machinery: the over-bar clause claimed 'separately validated' and checked is_file(), so an EMPTY {} beside a 5%-fires … |
| internal 7 (verdict) | 2026-08-29 | 2 | RETURN FOR AMENDMENT (research, round-4 pre-seal red-team at 41c4c14; 81 passed; _wilson_upper verified numerically; lex-10 CLEAN by monotonicity — the carve-out only ever SPARED, so removal only ADDS inbound; research owned both round-3 misses: the inverted safe-by-construction argument and the unv… |
| internal 8 (verdict) | 2026-08-30 | 1 | PASS — SEAL CLEARED (research, round-6 pre-seal pass at 03a5881; 84 passed; census verified: decision exact, seen != population refuses, size == fires, no dead sampling code; the digest derivation confirmed ORDER-INVARIANT so --cache reproduction is robust; the expensive-escape-hatch incentive desig… |
| internal 9 (verdict) | 2026-08-30 | 0 | PASS — SEAL CLEARED (research, round-7 pre-seal pass at 4774a06; 86 passed). Fp-union ENDORSED (false refusal is the safe direction; disagreements counted make a hostile co-verifier loud; third-labeller escape). Bootstrap state verified unreachable from verify (keyword-only, no CLI flag). Two harden… |
| internal 10 (verdict) | 2026-08-30 | 1 | RETURN FOR NARROW AMENDMENT (research, round-8 pre-seal pass at 7eedffe; all four round-7 closures held; suite 2033 masked the find — no gate on the unsafe primitive). I10-1 BLOCKING, the NINTH face of the duplicate-key class asked for and delivered: the R8-1 fold routed the manifests through _stric… |
| internal 11 (verdict) | 2026-08-30 | 1 | RETURN FOR NARROW AMENDMENT (research, co-verify of the I10-1 fold at 3d6df81; the MECHANISM verified clean — all three json.loads sites strict, the raw-vs-parsed cache split dead, shape bounds measured in source, hardlink guard live). I11-1, blocking-for-the-gate: the gate's own allowlist DEFEATED … |
| internal 12 (verdict) | 2026-08-30 | 0 | PASS — SEAL CLEARED (research, round-9 pre-seal pass at 5693331; 92 passed; R9-1 fixed, R9-3 confirmed PROBATIVE — it fails if the strict cache read reverts — and R9-2's fchmod closes the O_TRUNC-on-create gap). One structural recommendation, folded same-day though non-blocking on the draft: the R9-… |
| internal 13 (verdict) | 2026-08-30 | 1 | PASS FOR THE SEAL, ACCEPT-BLOCKER NAMED (research, round-10 pre-seal pass at 1400d96, run as the requested read-as-the-ACCEPT-reviewer; both package moderates verified folded). I13-1: the §6 V-invariant check column was not S-list-honest — six of seven named tests did not exist (V4's name had DRIFTE… |
| internal 14 (verdict) | 2026-08-30 | 0 | PASS — 'I WOULD SIGN ACCEPT' (research, round-11 pre-seal pass at 403d988; suite 2045 under both interpreters). R11-1 met exactly; NO landmines in the dormant behavioral cells (every assertion verified against §3); the field-name activation gate (agreement in Edge.model_fields, the §3d contract fiel… |
| external 1 (SENT) | 2026-08-26 | — | SENT (package `0026-v1`, candidate draft v4 [CORRECTED 2026-08-29, 0026-PACKAGE-R1-1: this row's opening said v3 while its own measurement sentence said v4; the package carried v4, as package_identity.py records — the structured candidate= field now binds this and the gate refuses disagreement] — th… |
| external 1 (verdict) | 2026-08-29 | 5 | RETURN FOR MAJOR AMENDMENT (package `0026-v1`, sha 87f10c89 verified; archive safety 488 members; extracted 1835/22 reconciling with sealed 1849/8; the restrict-only design spine called promising). R1-1: the directional detector CONFUSES PROXIMITY WITH AUTHORSHIP — five executed counterexamples: 'I … |
| external 2 (verdict) | 2026-08-29 | 5 | RETURN FOR MAJOR AMENDMENT (package `0026-v2`, sha 497bf05e verified; 518 safe members; extracted 1959/22 reconciling exactly with sealed 1973/8; the restrict-only design remains promising, each round-1 closure has a material seam). R2-1: the grammar still uses TOKEN PROXIMITY — 'the doctor treating… |
| external 2 (SENT) | 2026-08-29 | — | SENT (package `0026-v2`, candidate draft v5 — the round-1 fold; §11 maps all five findings; the restrict-only spine untouched). R1-1 closed as a directional GRAMMAR (lex-4): post-verbal agent governs, passive recipients inert, clause-bounded subjects, ambiguous pronouns restrict with a counted conse… |
| external 3 (verdict) | 2026-08-29 | 5 | RETURN FOR MAJOR AMENDMENT (package `0026-v3`, sha 6770c417 verified; 519 members; exact v2 predecessor verified; extracted 1960/22 reconciling exactly with sealed 1974/8; telemetry deferral substantively carrier-complete; the restrict-only architecture sound). R3-1: the head grammar still LAUNDERS … |
| external 3 (SENT) | 2026-08-29 | — | SENT (package `0026-v3`, candidate draft v6 — the round-2 fold; §12 maps all five findings). R2-1 closed with lex-7's HEAD CONSTRUCTION (forward clause reading, first noun after determiners/possessives as head, post-head modifiers inert whatever they name, coordinated co-heads determiners and all, U… |
| external 4 (SENT) | 2026-08-29 | — | SENT (package `0026-v4`, candidate draft v7 — the round-3 fold; §13 maps all five findings). R3-1 closed as lex-9: `or` joins the coordinators and the self-possessive splits ARTIFACT-vs-ENTITY over a closed artifact set, in both the subject scan and the agent path; oracle axes added; measured identi… |
| external 4 (verdict) | 2026-08-29 | 5 | RETURN FOR MAJOR AMENDMENT (package `0026-v4`, sha a122aaa3 verified; 521 members; exact v3 predecessor verified; extracted 1983/22 reconciling exactly with sealed 1997/8; the original or/own-doctor examples confirmed fixed; telemetry closed; every named round-3 example fixed but each new closure me… |
| external 5 (SENT) | 2026-08-29 | — | SENT (package `0026-v5`, candidate draft v8 — the round-4 fold; §14 maps all five findings; the round's shape named: every round-3 example fixed, every new closure mechanism seamed, answered with GENERATED carriers). R4-1 closed by REMOVAL: lex-10 drops the artifact carve-out — ownership is not auth… |
| external 5 (verdict) | 2026-08-29 | 5 | RETURN FOR MAJOR AMENDMENT (package `0026-v5`, sha 7d1314c4 verified; 524 members; exact v4 predecessor; diff reconciled incl. the 25 marked concurrent 0011 files; focused 0026 suite 82 passed; qualified offline suite reconciled). THREE round-4 closures HOLD: lex-10, the §6a generated claim, the led… |
| external 6 (SENT) | 2026-08-29 | — | SENT (package `0026-v6`, candidate draft v9 — the round-5 fold; §15 maps all five findings; three round-4 closures confirmed holding by the reviewer). EVIDENCE-R5-1 closed by the NONCE-FREE PROJECTION SEED (schema 5; research's pre-seal pass found the interim archive-sidecar form rested on an unguar… |
| external 6 (verdict) | 2026-08-30 | 4 | RETURN FOR NARROW AMENDMENT (package `0026-v6`, sha e89958b1 verified; 530 members; exact v5 predecessor; diff 9 changed/5 added/0 concurrent; focused suite 84 passed; qualified offline suite reconciled; trust-model architecture stable). CONFIRMED closed: §2c/§3d co-movement, the 9,999-denominator m… |
| external 7 (SENT) | 2026-08-30 | — | SENT (package `0026-v7`, candidate draft v10 — the round-6 fold; §16 maps all four findings; the two blocking closures are terminal simplifications, not ninth patches). EVIDENCE-R6-1 closed by ENDING SAMPLING: every adjudication is a CENSUS (schema 6 — sample carries size only; the manifest must lab… |
| external 7 (verdict) | 2026-08-30 | 4 | RETURN FOR NARROW AMENDMENT (package `0026-v7`, sha b62675e2 verified; 532 members; exact v6 predecessor; diff 11 changed/2 added/0 concurrent; focused 85 passed; qualified extracted suite reconciled to all 2036 collected; the v6 digest-nonce attack CONFIRMED DEAD — no sampling symbol survives; the … |
| external 8 (SENT) | 2026-08-30 | — | SENT (package `0026-v8`, candidate draft v11 — the round-7 fold; §17 maps all four findings). EVIDENCE-R7-1 closed: the bootstrap deadlock — measurement validates in bootstrap mode and an over-gate rate is a distinct reported STATE (own exit code; aggregate + FULL-CONTENT local-only worklist emitted… |
| external 8 (verdict) | 2026-08-30 | 4 | RETURN FOR NARROW AMENDMENT (package `0026-v8`, both uploads byte-identical at 55e5c0a1; 538 members; exact v7 predecessor; delta 13 changed/5 added; focused 86 passed; qualified extracted suite reconciled; ALL FOUR round-7 closures held — R7-1 closed for distinct valid paths, R7-2 substantially clo… |
| external 9 (SENT) | 2026-08-30 | — | SENT (package `0026-v9`, candidate draft v12 — the round-8 fold; §18 maps all four findings; all four round-7 closures held, the new seams were in the round-7 machinery itself). EVIDENCE-R8-1 closed: duplicate JSON members REFUSE at parse at every evidence boundary (_strict_json object-pairs hook; b… |
| external 9 (verdict) | 2026-08-30 | 3 | RETURN FOR NARROW AMENDMENT (package `0026-v9`, sha a1d56a4f verified; 539 members; exact v8 parent; focused 92 passed; full extracted suite 2021/22 exit 0; archive layout needs no change). R9-1 BLOCKING: the AgreementRecord carriers DISAGREE — §3d defines direction as inbound\|ambiguous\|user_sourc… |
| external 10 (SENT) | 2026-08-30 | — | SENT (package `0026-v10`, candidate draft v13 — the round-9 fold; §19 maps all three findings). R9-1 closed: ONE canonical AgreementRecord — AGREEMENT_SHAPE matches §3d's stored enum exactly (inbound\|ambiguous\|user_source; user_source IS §3c's demotion-direction record; the lexicon-internal 'outbo… |
| external 10 (verdict) | 2026-08-30 | 2 | RETURN FOR NARROW PACKAGE AMENDMENT (package `0026-v10`, sha 23533a67 verified; 540 members; exact v9 parent; focused 95 passed; full extracted 2024/22 exit 0; THE DESIGN SURFACE IS READY — no new semantic issue; all six v9 corrections confirmed holding incl. the executable total lexicon->stored map… |
| external 11 (SENT) | 2026-08-30 | — | SENT (package `0026-v11`, candidate draft v14 — the round-10 fold; §20 maps both findings; the reviewer's verdict: THE DESIGN SURFACE IS READY, no new semantic issue). PACKAGE-R10-1 closed: the last numeric restatements removed — the R8-2 closure row is version-neutral (exact numbers live only in th… |
| external 11 (verdict) | 2026-08-30 | 1 | RETURN FOR NARROW ACCEPTANCE-GATE AMENDMENT (package `0026-v11`, sidecar matched; 541 members; exact v10 parent; focused 96 passed; complete extracted 2025/22 exit 0; the V1-V7/V6a design surface REMAINS READY; both round-10 package findings closed and verified; NO FURTHER DESIGN ROUND NEEDED). R11-… |
| external 12 (SENT) | 2026-08-30 | — | SENT (package `0026-v12`, candidate draft v15 — the round-11 fold; §21 maps the one finding; the reviewer's stated acceptance condition met: no further design round needed). R11-1 closed: the six implementation-time V-checks EXIST as standing ABSENCE-AWARE tests — in the draft state each mechanicall… |
| external 12 (verdict) | 2026-08-30 | 0 | APPROVED FOR ACCEPTANCE (package `0026-v12`, sidecar matched; 542 members; exact v11 parent; identity/header/collection/reconciliation/closure checks passed; all prerequisites accepted; focused 102 passed; complete extracted 2031/22 exit 0, differences reconciling to documented environment condition… |

**Per-finding closure ledger — PROCESS §4a.** **57 finding(s) for `0026`; 277 across the 7 tracked specs** — every number here is DERIVED from the rows below (external round 7, R7-1: the manifest claimed 26 while the ledgers held 31, and 0023 said 9/9 above a 10-row table). Generated from `specs/closure_findings.py` and validated against `specs/reviews.py` on `(spec, kind, round, id)` EXACTLY — extras, duplicates, wrong rounds and empty evidence all fail the build.

| finding | round | what it was | closed in | evidence (runnable) |
|---|---|---|---|---|
| **0026-I1-M1** | internal 1 | §1's census figures were the PRE-correction values (183,416 / 1,637 / 41.5%); the shipped script over the cache says 183,417 / 1,644 / 41.7% — a value that drifted from its source artifact and was consumed by label, which is this spec's own thesis in miniature | exact script output in both carriers, with the drift itself recorded as the provenance note | `grep -c '183,417' specs/0026-label-value-agreement.md && grep -c '41.7' specs/0026-label-value-agreement.md` |
| **0026-I1-M2** | internal 1 | §8 promised a SEMANTIC property — a relayed claim that names its source is never asserted — delivered by a LEXICAL mechanism, so a note reading 'the vet mentioned this' falsifies the claim while every V-invariant stays green | the §8 sentence is scoped to the lexicon (a mechanical surface) and §6a's run reports the coverage denominator, so the claim ships as a measured fraction of the naming population rather than an implied whole | `grep -n 'the promise is scoped to the LEXICON' specs/0026-label-value-agreement.md && grep -n 'coverage denominator' specs/0026-label-value-agreement.md` |
| **0026-I1-m3** | internal 1 | §3b described the floor's position two ways (after the pipeline and before the accepted floors, versus as one more accepted floor in step 3), reading as two different positions | monotonicity dissolves it — floors only LOWER, so order within the floor set is irrelevant; the spec says that and picks one description | `grep -n 'floors only LOWER' specs/0026-label-value-agreement.md` |
| **0026-I1-m4** | internal 1 | a POINTER, not a defect: when the L3 round takes the render question, research's baseline records are prior evidence — B02's answer already rendered attribution from content while the edge sat MENTIONABLE | recorded against V-Q1 so the L3 round starts from the existing evidence; no spec change was required and none was made | `grep -n 'V-Q1' specs/0026-label-value-agreement.md` |
| **0026-I1-m5** | internal 1 | the stale 183,416 appeared once more in the demotion bullet — the M-1 sweep had to catch EVERY carrier, not the first | swept; the only surviving occurrences are inside the provenance note that quotes the old figures deliberately, which this command allows for by name rather than by pretending the string is gone | `! grep -n '183,416' specs/0026-label-value-agreement.md \| grep -v 'v1 carried' \| grep -v '0026-I1-'` |
| **0026-R1-1** | external 1 | the directional detector confused proximity with authorship: a 4-token lookback misclassified all five executed counterexamples (passive recipients as speakers, the post-verbal agent never consulted, embedded clauses inheriting the outer subject, she/he/they silently the user) | the shipped lexicon is a directional grammar — agent governs, passive recipients inert, head-constructed subjects, ambiguous pronouns restrict with a counted conservative outcome; the five counterexamples ride verbatim in the hand matrix plus the generated grammar oracle; the CURRENT figures (lexicon version, cell count, rate) are DERIVED from fp_aggregate.json and validate_lexicon.py, never restated here (0026-PACKAGE-R2-1: this row once carried lex-3/32 cells/0.60% while the candidate shipped lex-6/53/0.70% — one source now) | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_reviewers_five_counterexamples_verbatim tests/test_0026_relay_lexicon.py::test_relay_lexicon_mutation_matrix -q -p no:randomly` |
| **0026-R1-2** | external 1 | the portable agreement carrier had no import-boundary contract: absent, forged, malformed, foreign-version and direction-disagreeing imported fields were all undefined, and no version or direction carrier existed despite §7's rule_version promise | Edge.agreement is a structured record (markers + direction + lexicon version); §3d's import matrix is total — recomputation under the current lexicon governs every row, the incoming value is compared for a diagnostic counter and discarded, fail-closed both directions (V6a; implementation lands with acceptance like the rest of §3) | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_import_matrix_is_total_in_the_spec -q -p no:randomly` |
| **0026-R1-3** | external 1 | 'consent-gated' was not a construction: 0015's consent text/schema-version/display-transition/record-gating requirements were absent, 0015 was not in Spec-Requires, and a conforming implementer could widen an already-consented payload | telemetry consumption DEFERRED: the counters are local operator surface only, whitelisting is forbidden without a future 0015-conformant amendment that adds 0015 to Spec-Requires and specifies the complete consent construction | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_telemetry_deferral_is_bound -q -p no:randomly` |
| **0026-EVIDENCE-R1-1** | external 1 | the acceptance measurement was self-asserted: nothing read fp_aggregate.json — fires 415 to 0, coverage to 0 and lexicon 0026-lex-999 all passed header, identity, lexicon validator and the full spec gate; lex-1 did not ship despite the claim | a closed validator (schema, types, internal consistency, shipped-lexicon pin) with the cache manifest cross-checked against the 0011/0025 subject aggregate; --aggregate is a real verify mode; the reviewer's three tamperings are the mutation matrix's first cells; whole-corpus figures labelled RECORDED ONLY; the lex-1 claim narrowed honestly | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_fp_aggregate_validator_matrix tests/test_0026_relay_lexicon.py::test_the_real_entry_point_verifies_and_refuses -q -p no:randomly` |
| **0026-PACKAGE-R1-1** | external 1 | candidate identity was contradictory yet verified VALID: the SENT row said v3 and v4 in one verdict; the v4 amendment postdated both internal reviews with no structured co-verification row | the round-1 SENT row corrected in place with the correction visible; candidate revision is a structured SENT-row field bound to package_identity.py by the gate (disagreement refuses); the internal-first miss acknowledged, with the v5 fold queued for research's pre-seal red-team pass | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_structured_candidate_field_binds_to_the_package_record -q -p no:randomly` |
| **0026-R2-1** | external 2 | the grammar still used token proximity: a modifier's object read as the subject, a determiner-separated conjunct lost its co-source, and a curly apostrophe defeated tokenization — the hand cells stayed green because they omitted the shapes | lex-7 head construction (forward clause reading, post-head modifiers inert, coordinated co-heads, Unicode normalization, relative pronouns as modifier-openers) plus the GENERATED grammar-oracle corpus with expectations derived from the constructions; §6a re-measured, bound improved | `$PY specs/evidence/0026/validate_lexicon.py` |
| **0026-R2-2** | external 2 | portability contradicted accepted contracts: ignore-unknown-key vs 0025's format bump, and always-recompute-and-floor vs 0005 P2's trust-field-faithful restore | mode-split import boundary (restore verbatim incl. disclosure, recomputation diagnostic-only; default recomputes and floors) and a FORMAT_VERSION bump on export, with the full format x mode x field matrix in §3d | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_import_matrix_is_total_in_the_spec -q -p no:randomly` |
| **0026-R2-3** | external 2 | the telemetry deferral was not carrier-complete: §3c still said 'consumed by telemetry from day one', §9 still named telemetry a consumer, and the deferral test inspected §3d alone | both carriers swept with visible correction notes; the test scans EVERY carrier via a whole-file occurrence check that tolerates only quoted sweep notes | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_telemetry_deferral_is_bound -q -p no:randomly` |
| **0026-EVIDENCE-R2-1** | external 2 | the acceptance result was still not bound: fires tampered to 2,000 (2.92%, over the 2% gate) verified as aggregate VALID, and the measurement doc retained stale figures beside the current result | the gate is part of aggregate validity (over-gate refuses absent a separately validated adjudication artifact); the doc's shipped figures are mechanically compared to the aggregate at the verify entry point; a hand-typed 219-vs-220 coverage figure was refused by the binder during the sweep itself | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_gate_and_the_doc_are_bound -q -p no:randomly` |
| **0026-PACKAGE-R2-1** | external 2 | governance carriers disagreed: the closure row said lex-3/32 cells/0.60% while the candidate shipped lex-6/53/0.70%, and the v5 research pass existed only as SENT-row narration | closure measurement figures derive from the aggregate and validator (one source); research's v5 pre-seal pass is recorded as structured internal rounds 3 and 4 | `$PY specs/render_closure.py --check` |
| **0026-I4-1** | internal 4 | the verb list omitted `claimed` (the name of the relation 0024 quarantines) and high-frequency attribution verbs; §6a measures FP only and every matrix inbound cell used an in-list verb, so recall was unmeasured in two places at once | the assertion/transmission/professional-judgment verb classes added with the professional-judgment ruling stated; nominal homographs narrowed by reading the fires; held recall cells and the claimed-removal mutant make completeness MEASURED; §8 scoped to the stated verb set; re-verified by research at 5ccccae | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_relay_lexicon_mutation_matrix -q -p no:randomly` |
| **0026-I5-1** | internal 5 | comitative quasi-coordinators (along with / together with / as well as) introduce a co-speaker the lexical coordinator set cannot see — three genuine relays silently unrestricted, the co-source class one syntactic layer up, and the generator's coordination axis could not catch what it did not generate | lex-8: the closed comitative set joins the head scan as co-source introducers, the generator gains the comitative axis (measured, not patched), research's three misses ride verbatim as cells, the comitative-drop mutant stands, and the third-person self-possessive consistency fix rides | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_relay_lexicon_mutation_matrix -q -p no:randomly` |
| **0026-I6-1** | internal 6 | the new 2% gate claimed 'separately validated' and checked is_file(): an empty {} beside a 5%-fires aggregate produced 'aggregate VALID' — the arc's signature defect (prose asserting more than the code) inside the fold's own binding machinery | the adjudication artifact is read and validated — closed schema, labelled sample summing to size, non-blank verdict — and BOUND to the exact aggregate's lexicon version and fire count; empty-file and stale-binding refusals stand as tests and the legitimate labelled bypass is proven alive | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_gate_and_the_doc_are_bound -q -p no:randomly` |
| **0026-R3-1** | external 3 | the head grammar still laundered: or-disjunction was not coordination, and the self-possessive fix read 'my own doctor' — a possessed person — as the user; the oracle omitted both axes so every packaged test stayed green | lex-9: `or` joins the coordinators; the self-possessive splits artifact-vs-entity over a closed artifact set in both the subject scan and the agent path; the oracle gains the disjunction axis and own-entity heads; re-measured identical | `$PY specs/evidence/0026/validate_lexicon.py` |
| **0026-R3-2** | external 3 | the import matrix was incomplete: AgreementRecord absent from §2c's untrusted-input table, and restore mode had no cell for a malformed new-format record — verbatim-and-typed is impossible for garbage | the AgreementRecord row joins §2c; restore-malformed RAISES with nothing written (the R1-4 ruling on the restore path, validation ordered before any write); default-malformed stays treated-as-absent; the structural test binds the new cells | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_import_matrix_is_total_in_the_spec -q -p no:randomly` |
| **0026-EVIDENCE-R3-1** | external 3 | the adjudication path was decision-free: a verdict literally reading REJECT carried a 5.00% aggregate to 'aggregate VALID' — shape and blankness were checked, meaning never was, and nothing digest-bound the aggregate or sample | the decision is executable: closed verdict enum, the adjudicated rate computed and required under the gate, a sample minimum, and digest binding to the exact aggregate bytes; REJECT, free-text, lying-accept, tiny-sample and wrong-digest all stand as refusals with the legitimate bypass proven alive | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_gate_and_the_doc_are_bound -q -p no:randomly` |
| **0026-EVIDENCE-R3-2** | external 3 | the candidate spec's §6a said 217 beside the aggregate's 220 — the binder covered the measurement doc and not the spec carrying the acceptance claim | spec_problems binds the §6a headline rate and coverage figure to the aggregate at the verify entry point; the drift re-derived; the bite standing-tested | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_spec_binder_and_round_count_are_bound -q -p no:randomly` |
| **0026-PACKAGE-R3-1** | external 3 | the header and §9 said research ran two internal rounds beside a six-round structured ledger — prose frozen at the pre-external state | §9 swept with the correction visible and the stated count bound to reviews.py by a standing test, so the prose cannot silently underclaim again | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_spec_binder_and_round_count_are_bound -q -p no:randomly` |
| **0026-R4-1** | external 4 | OWNERSHIP mistaken for AUTHORSHIP: lex-9's _SELF_ARTIFACTS read every owned artifact as user-authored — 'my own record reported a diagnosis of cancer' went outbound with no marker, though the record's producer can be a doctor or a bank; laundering, the FN direction, and the oracle tested only the intended senses | lex-10 REMOVES the carve-out — no noun class carries an authorship inference; a possessed head restricts whoever possesses it, artifacts included ('my own notes' over-restricting is priced and reversible; laundering is not); the ownership-vs-authorship axis joins the oracle (all four reviewer cells) and the relapse is a standing behavioral mutant; re-measured 439/68,479 = 0.64% — identical, which is why the carve-out bought nothing and was pure risk | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_relay_lexicon_mutation_matrix -q -p no:randomly` |
| **0026-R4-2** | external 4 | the §2c AgreementRecord row said malformed-under-EITHER-mode raises while §3d said default-mode malformed recomputes, with the §2c columns displaced — and the matrix test checked substrings, not agreement between the carriers | import_matrix.py is the ONE structured decision table now: both spec representations are GENERATED from it and byte-bound at the packaged test, so the carriers cannot diverge — there is nothing left to hand-edit into contradiction | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_spec_binder_and_round_count_are_bound -q -p no:randomly` |
| **0026-EVIDENCE-R4-1** | external 4 | the adjudication remained SELF-ASSERTED (the signature defect's sixth face, at the surface the fifth hunt cleared): true_positive=100/false_positive=-50 summed to size and passed; sample_sha256 was regex-checked, never opened or hashed; the decision used a point estimate | schema 3 is RECORD-BOUND, data to data: the aggregate ships fire_digests (a content-free digest per fire), the labelled sample is an on-disk record-bound manifest (live only over-gate; a worked synthetic example ships) whose bytes are hashed against sample_sha256, membership and uniqueness are checked against the population, the counts are DERIVED by counting labels (no count carriers exist to lie), and accept requires bound x Wilson-95 UPPER confidence <= 2% — the reviewer's exact bypass and seven sibling cells are standing refusals, with the legitimate binding proven alive | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_gate_and_the_doc_are_bound -q -p no:randomly` |
| **0026-EVIDENCE-R4-2** | external 4 | the spec binder searched two substrings anywhere in the file — the §6a headline still said lex-8 over a lex-9 aggregate, and 9,999/lex-999 mutations passed | the §6a claim is a GENERATED block (render_spec_claim), byte-bound to the aggregate at the verify entry point and required to sit inside §6a — the reviewer's both mutations and an in-block figure edit are standing refusals; prose figure carriers swept into the block's custody | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_spec_binder_and_round_count_are_bound -q -p no:randomly` |
| **0026-PACKAGE-R4-1** | external 4 | round 3's verdict named the Internal-reviewers header AND §9; the fold swept only §9 — the header still listed rounds 1-2 and READY FOR EXTERNAL, and its test found 'six internal rounds' anywhere in the file | the front-matter row is GENERATED from the ledger (reviews.internal_reviewers_row) and byte-bound; static readiness claims are refused outright — a generated row cannot be half-swept | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_spec_binder_and_round_count_are_bound -q -p no:randomly` |
| **0026-I7-1** | internal 7 | SAMPLE SELECTION voided the Wilson gate: the seed was recorded but never re-drawn or bound, so a host could ship any >=50 real fires, label the cleanest honestly (fp=0 -> UCB 0.071), and pass accept up to ~28% — Wilson-95 bounds a RANDOM sample; over a selected one it guarantees nothing | the seed is CANONICAL (derived from the aggregate's own bytes — not choosable, closing seed-shopping too) and the validator RE-DRAWS random.Random(seed).sample over the sorted population, requiring the manifest to label EXACTLY the drawn set; --sample prints that draw; per the co-verify ADDENDUM the SIZE is canonical too (census up to the fixed 500 limit, else the limit; a census decides on the EXACT share, no Wilson needed) — size-shopping closed structurally, not just measured inert; hand-picked, non-canonical-seed, size-shopped and short-census attacks are standing refusals; the residual trust boundary is the per-fire LABELS, where it belongs | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_gate_and_the_doc_are_bound -q -p no:randomly` |
| **0026-I7-2** | internal 7 | byte-equality binders verified DRIFT, not renderer CORRECTNESS: an off-by-one renderer produces wrong-but-self-consistent bytes and re-render passes — the suite mutated shipped text and the aggregate, never a renderer | every renderer has an INDEPENDENT oracle now: the test computes the figures straight from the artifact (never by re-invoking the renderer) and requires the rendering to carry them, both gate branches driven, the off-by-one renderer shown caught, and the cross-carrier malformed-mode facts asserted in both import-matrix renderings | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_renderers_agree_with_independent_oracles -q -p no:randomly` |
| **0026-EVIDENCE-R5-1** | external 5 | the 'canonical' seed hashed the ENTIRE host-produced aggregate, so a decision-irrelevant field was a NONCE: varying only suppressed_by_direction_only swung the draw from 167/500 FP (accepted) to 232/500 (refused) — seed-shopping survived, face seven of the selection-freedom class | the seed basis is the NONCE-FREE PROJECTION (schema 5, completed at research's round-5 pre-seal pass — the interim archive-sidecar form rested on an unguaranteed non-precomputable first seal): derived from exactly the cross-anchored and decision-read fields (fire_digests + fires + manifest), each byte enumerated and justified; shopping the draw requires moving the measurement or tripping the anchor, so precomputability is harmless; nonce-invariance and population-sensitivity cells stand; the shipped corpus is a census and needs no seed at all [SUPERSEDED at round 6: EVIDENCE-R6-1 showed fire_digests itself is a host-produced identifier — sampling ENDED entirely; every adjudication is a census, schema 6] | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_gate_and_the_doc_are_bound -q -p no:randomly` |
| **0026-R5-1** | external 5 | render_2c_row hard-coded its text BESIDE the matrix while the spec claimed both carriers were generated from it — a mutated matrix regenerated §3d, §2c stayed contradictory, the binder returned clean (the name-vs-behavior class) | every mode-dependent §2c clause is PROJECTED from the matrix rows' own operative text; the source-level mutation test drives a changed outcome through BOTH renderings and both binder halves | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_import_matrix_carriers_move_together -q -p no:randomly` |
| **0026-PACKAGE-R5-1** | external 5 | the spec and ledger said the adjudication manifest was SHIPPED and 'now EXISTS' while the archive contained neither artifact — no live adjudication can exist under-gate; the claim overstated a dormant path | every carrier corrected VISIBLY (the construction ships; live artifacts materialize over-gate), and the worked clearly-synthetic end-to-end example ships in adjudication_example/ and is validated from disk by a standing test | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_worked_adjudication_example_validates_from_disk -q -p no:randomly` |
| **0026-EVIDENCE-R5-2** | external 5 | doc_problems hard-coded the 3,898 coverage denominator — a 9,999 denominator (internally valid, spec block regenerated) validated clean everywhere while the doc still said 3,898 | the doc needle derives numerator, denominator AND percentage from the aggregate; the reviewer's denominator mutation is a standing cell | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_gate_and_the_doc_are_bound -q -p no:randomly` |
| **0026-EVIDENCE-R5-3** | external 5 | a correctly hash-bound manifest containing invalid UTF-8 raised an uncaught UnicodeDecodeError instead of a structured refusal | both adjudication files return structured refusals on decode failure, with a standing cell for each | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_gate_and_the_doc_are_bound -q -p no:randomly` |
| **0026-EVIDENCE-R6-1** | external 6 | fire_digests remained a host-controlled seed nonce: digests are shape-checked, never recomputed from or bound to the cache, so varying ONE digest while holding the semantic population and labels fixed swung 159/500 FP accepted vs 234/500 refused — 'decision-read' does not make a host-produced identifier non-choosable (face EIGHT of the selection class) | sampling ENDS: every adjudication is a CENSUS (schema 6 — sample carries size only; manifest must label exactly the population; decision is the exact labelled share; draw/seed/size/Wilson all REMOVED — eight faces proved no sampling construction over a host-produced population survives); boundary cells stand incl. the exact-share bar from both sides; the digest-to-cache derivation is recorded protocol, reproducible with --cache | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_gate_and_the_doc_are_bound -q -p no:randomly` |
| **0026-R6-1** | external 6 | the restore-mode foreign-version cell was UNSPECIFIED: a well-typed record with current-valid markers and a foreign lexicon version under restore=True was unrecognised but not malformed — no stated outcome, and §2c's unrecognised cell stated only the default mode | RULED verbatim: the version field exists to mark provenance, recomputation stays diagnostic-only, and refusing would break restore round-trips of old exports; the cell joins MATRIX (the one carrier) and both generated projections carry it | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_renderers_agree_with_independent_oracles -q -p no:randomly` |
| **0026-PACKAGE-R6-1** | external 6 | the half-swept-carrier class AGAIN: the Version row described the discarded archive-sidecar seed, the round-6 SENT row said v0 witness/schema 4 while the archive shipped schema 5 with the projection seed, and the example README claimed a generator the package did not ship | closed STRUCTURALLY per the reviewer's fix: ADJUDICATION_SCHEMA is the one generated carrier of the CURRENT revision (validator, shipped generator, §6a claim block and tests all read it; current-summary prose derives or omits the number — HISTORICAL prose names the schema of its own round, a constraint round 7 made explicit); generate_example.py ships and the standing test requires byte-identical regeneration; the Version row and SENT row carry visible corrections | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_worked_adjudication_example_validates_from_disk -q -p no:randomly` |
| **0026-EVIDENCE-R6-2** | external 6 | the round-5 denominator fix divided unguarded: doc_problems on a zero-denominator aggregate raised ZeroDivisionError while render_spec_claim guarded the same derivation | the doc needle uses the renderer's guarded derivation; the zero-denominator cell refuses structurally and stands | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_gate_and_the_doc_are_bound -q -p no:randomly` |
| **0026-I8-1** | internal 8 | the next half-swept carrier after the one-schema fix is PROSE THAT RESTATES MECHANISMS: _validate_adjudication's docstring still said 'Schema 3' and 'Wilson' two revisions after both were deleted — natural-language prose is the one carrier the generated-schema pattern cannot bind | the docstring names the mechanism's carriers (the code below it, ADJUDICATION_SCHEMA, the spec's per-round history) instead of restating rules; the live-prose sweep ran with history sections standing as history; the drift is named IN the docstring as its own cautionary case | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_live_prose_names_carriers_not_mechanisms -q -p no:randomly` |
| **0026-EVIDENCE-R7-1** | external 7 | the live over-gate census could not be CREATED: measurement validated before emitting, and an over-2% result demanded the adjudication that the emitted aggregate and worklist exist to enable — a bootstrap deadlock (executed: fresh over-gate cache, exit 1, nothing emitted); the synthetic example never exercised the path because its generator hand-builds every artifact | measurement validates in BOOTSTRAP mode: structural problems refuse, an over-gate rate is a distinct reported STATE (exit 3, aggregate + worklist emitted, acceptance never claimed); the verify entry keeps refusing; the adjudication is looked for beside the aggregate under verification; the shipped synthetic e2e_fixture drives every stage through the real main() as a standing regression | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_over_gate_pipeline_end_to_end -q -p no:randomly` |
| **0026-EVIDENCE-R7-2** | external 7 | independent label co-verification was neither judgeable nor bound: --sample truncated note/object so distinct fires displayed identically, the manifest is hashes-only so content cannot be recovered, and a host-only all-tp census returned [] with no co-verifier evidence required | schema 7 BINDS both censuses (host + independent co-verifier, one shared reader); the decision runs on the fail-closed fp-UNION with disagreements counted; a missing co-verification refuses (host-only labels are not an adjudication); --worklist emits the full-content LOCAL-ONLY worklist keyed by fire digest | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_the_gate_and_the_doc_are_bound -q -p no:randomly` |
| **0026-R7-1** | external 7 | foreign-version MARKER validity was undefined: markers=['future_marker'] under lexicon=0026-lex-999/restore is well-typed, but the reader cannot know that lexicon's vocabulary — the foreign row said verbatim while the malformed row said out-of-grammar raises | grammar membership is VERSION-SCOPED, mechanically: foreign-version markers validate as OPAQUE closed shapes (nonempty bounded strings, bounded count, closed types), never for membership; the malformed row's out-of-grammar rule applies only under the CURRENT version; the reviewer's exact case is named in the matrix cell and both projections carry the rule | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_renderers_agree_with_independent_oracles -q -p no:randomly` |
| **0026-PACKAGE-R7-1** | external 7 | the half-swept-carrier class persisted in OPERATIONAL prose: --sample help said 'draw N fires' (census flag), test comments said projection-seed and v0-witness, and summary prose hard-coded 'schema 6' while claiming prose never numbers revisions | operational prose swept; the one-carrier claim CONSTRAINED precisely: current-summary carriers derive from ADJUDICATION_SCHEMA or omit the number, historical prose names the schema of its own round | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_live_prose_names_carriers_not_mechanisms -q -p no:randomly` |
| **0026-EVIDENCE-R8-1** | external 8 | census records were not unambiguous: json.loads keeps the LAST duplicate member, so 'label:fp,label:tp' passed as tp — hash binding authenticated ambiguous bytes without resolving meaning, and both censuses shared the reader so the fp-union could be reduced (the 0011 EVIDENCE-R9-1 class refound in new code) | duplicate JSON members REFUSE at parse via _strict_json (an object-pairs hook) at every evidence boundary — both manifests and the adjudication record — with duplicate-label and duplicate-fire regressions standing | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_census_manifests_refuse_ambiguous_records -q -p no:randomly` |
| **0026-R8-2** | external 8 | the foreign-version shape lacked an EXECUTABLE definition — 'nonempty bounded strings' and 'bounded count' with no bounds let conforming implementations accept different inputs | AGREEMENT_SHAPE is data with the running reference validator agreement_shape_problems (closed keys; a bounded marker array; duplicates refuse; the closed direction enum; a bounded lexicon version under a closed pattern — the EXACT numbers live only in the generated §3d shape block and moved with the I10-1 measurement; this row is version-neutral per PACKAGE-R10-1, which caught it restating the pre-measurement bound), rendered byte-bound into §3d; every bound driven at the limit and one beyond by a standing test | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_agreement_shape_bounds_at_the_limit_and_beyond -q -p no:randomly` |
| **0026-EVIDENCE-R8-3** | external 8 | bootstrap output paths could overwrite one another or the input: --emit-aggregate X --worklist X destroyed the aggregate, either output could name --cache, and exit 3 was reachable without both artifacts retained | every path resolves and cross-checks BEFORE any write; aliases (relative or absolute) and output-names-input refuse with the source proven preserved; the good path retains both artifacts | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_bootstrap_paths_cannot_alias_and_worklists_stay_local -q -p no:randomly` |
| **0026-PRIVACY-R8-4** | external 8 | LOCAL-ONLY was documentation: --worklist accepted any path with ordinary permissions, and .gitignore covered fp_worklist* while the packaged test wrote worklist.jsonl | mechanically enforced: a worklist path inside the package tree refuses before any write, the file is written mode 0600, and a standing package sweep refuses ANY .jsonl under specs/ carrying the worklist line shape — rename-proof | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_no_full_content_worklist_ships_in_the_package -q -p no:randomly` |
| **0026-I10-1** | internal 10 | the ninth face: the R8-1 fold routed the manifests through the strict decoder but left plain json.loads at THREE evidence boundaries — aggregate verify, peer cross-anchor, and the CACHE read whose raw-vs-parsed split (raw-sha anchor vs last-wins enumeration) was genuinely exploitable; vigilance failed twice (11-day class recurrence + three missed sites in the closing fold). Secondary: the alias guard missed hardlinks; markers_max_count was taste not measurement | every evidence-boundary read routes through _strict_json (a duplicate-key cache row counts unparseable, never last-wins); the structural gate makes the unsafe form UNREACHABLE — a standing test refuses plain json.load(s) under specs/evidence/ outside a reasoned allowlist (legacy lines capped at their current counts, new files at zero); the alias guard compares (st_dev, st_ino) so hardlinks refuse; the shape bounds carry their MEASURED basis (max distinct markers per record = 2 over the full cache -> count bound 8 = measured x4; longest member 16 chars -> length bound 64 = x4) | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_no_plain_json_load_at_evidence_boundaries -q -p no:randomly` |
| **0026-I11-1** | internal 11 | the gate's own allowlist defeated it for the file it protects: 0026's cap was 3 while the matched count was 0 (regex miscount — the impl line skipped, the docstrings never matched), leaving three slots of headroom for reintroduced plain json.loads | the gate is EXACT-MATCH (a count above OR below its pin trips — self-catching, no headroom anywhere) and AST-BASED (calls resolved through import aliases incl. bare `from json import loads`; safety judged per-call by the object_pairs_hook keyword, not per-line) — the AST recount immediately corrected one legacy pin the regex had undercounted, proving the rebuild on its first run; 0026's own pin is 0; the co-verify's tenth-face hardening taken same-day — only KNOWN-STRICT hooks by name count as safe (object_pairs_hook=dict counts as plain) | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_no_plain_json_load_at_evidence_boundaries -q -p no:randomly` |
| **0026-R9-1** | external 9 | the AgreementRecord carriers DISAGREED in the machinery built to prevent it: §3d's stored direction enum is inbound|ambiguous|user_source while AGREEMENT_SHAPE said inbound|outbound|ambiguous (the lexicon's internal reading names); markers=[] was accepted against V2's no-markers-no-record rule; and §18 plus the round-9 SENT row restated 16 markers beside the executable 8 | ONE canonical enum: the shape matches §3d exactly (user_source legal — it IS §3c's demotion-direction record; 'outbound' refuses as a stored value with the lexicon-mapping stated; markers minimum 1); the three named inputs are independent standing cells; both restatements carry visible corrections and live prose no longer carries the numbers | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_agreement_shape_bounds_at_the_limit_and_beyond -q -p no:randomly` |
| **0026-PRIVACY-R9-2** | external 9 | the local-only closure covered only FRESH files: O_TRUNC applies 0600 only on create, so a pre-existing 0644 worklist kept 0644 while the program reported 0600; and the package sweep read only the first line of *.jsonl, contradicting the rename-proof claim | fchmod is explicit before any content lands (pre-existing-file regression standing); the sweep reads EVERY line of every decodable file under specs/ whatever the suffix or size, with undecodable worklist-shaped bytes flagged at the byte level (the round-10 size-cap exclusion removed) | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_bootstrap_paths_cannot_alias_and_worklists_stay_local tests/test_0026_relay_lexicon.py::test_no_full_content_worklist_ships_in_the_package -q -p no:randomly` |
| **0026-EVIDENCE-R9-3** | external 9 | the duplicate-cache regression was NON-PROBATIVE: it passed on returncode != 0, which the peer mismatch it introduced already guaranteed — nothing proved the row was counted unparseable | the regression builds a MATCHING peer for the modified cache, requires the bootstrap state (exit 3), and asserts the exact '1 unparseable' count — proving the row was COUNTED, not that something failed | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_duplicate_key_cache_rows_count_unparseable -q -p no:randomly` |
| **0026-PACKAGE-R10-1** | external 10 | numeric carrier cleanup was incomplete: the R8-2 closure row still recorded 'at most 16 markers' (never re-swept after the I10-1 measurement moved the bound to 8) and the boundary test's diagnostic literal said '17 markers must refuse' beside a derived case — contradicting v13's no-restatement claim | the closure row is version-neutral (exact numbers live only in the generated §3d block, and the row says so) and the diagnostic derives from markers_max_count | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_agreement_shape_bounds_at_the_limit_and_beyond -q -p no:randomly` |
| **0026-PRIVACY-R10-2** | external 10 | the broadened sweep silently skipped files over 8,000,000 bytes — an undocumented exclusion a large worklist-shaped file evades; and the R9-2 closure command invoked only the file-mode regression, not the package-sweep half | the size cap is REMOVED — total scope at bounded memory (text streamed line by line; undecodable files byte-scanned in 1MB chunks with an overlap window); the R9-2 closure evidence runs both halves | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_no_full_content_worklist_ships_in_the_package -q -p no:randomly` |
| **0026-I13-1** | internal 13 | the §6 V-invariant check column was not S-list-honest: six of seven named tests did not exist — V4's name had drifted from the real test, and V2/V3/V5/V6/V6a/V7 are implementation-time obligations (0026 is a draft; no agreement mechanism exists in src/) presented as standing checks; the S-list completeness check is exactly what the acceptance reviewer runs | every §6 row is marked CURRENT vs IMPLEMENTATION-TIME (graduates with src/), V4's name corrected to the real test, and the standing guard binds both halves: every test name cited in the spec's live zone must resolve to a real function (marked obligations exempt), and the shape-bound digits may appear in marker/character context only inside generated blocks — the restatement class's five bitten carriers under one guard | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_current_v_table_tests_resolve_and_no_live_restatement -q -p no:randomly` |
| **0026-R11-1** | external 11 | six §6 invariants (V2/V3/V5/V6/V6a/V7) still lacked EXECUTABLE checks: accurately labeled implementation-time, but the resolution guard exempted those rows, so the suite passed with none of the six named tests existing — PROCESS.md makes an invariant without an executable check a hard gate | the six named tests EXIST as standing ABSENCE-AWARE checks: in the draft state each mechanically proves its invariant vacuous (no agreement machinery in src/ — the sweep flips when implementation begins) and the behavioral cells against the spec'd API activate automatically at graduation (V6a fails loudly then until the matrix drive is written, by design); the exemption is removed — every cited name resolves | `$PY -m pytest tests/test_0026_relay_lexicon.py::test_absence_is_no_evidence tests/test_0026_relay_lexicon.py::test_no_markers_is_byte_identical tests/test_0026_relay_lexicon.py::test_current_v_table_tests_resolve_and_no_live_restatement -q -p no:randomly` |

<!-- /GENERATED:review-closure -->

