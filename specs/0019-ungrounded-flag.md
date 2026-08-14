# Feature spec: the `ungrounded` flag — evidence-grounding at ingest

Spec-Status: draft
Spec-Requires: 0005, 0008

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft v2** — internal review folded (F1: the comparison/projection/
> digest carriers ruled; the marker renamed; the D2 renumbering conditions
> pinned). v1: Quentin's option-A ruling (2026-08-14) on the PatchTest
> landing-pad ask (`proposals/patchtest-landing-pad-ask.md`; measured basis
> `patchtest/phase1_RESULTS.md`, four shadow rounds over 149k objects, the
> phase-1f gate). Ships the SPECIFICS-ONLY grounding check as a new,
> never-refusing Edge flag. The full relation-scoped predicate stays an
> offline corpus-audit tool regardless of this spec's fate.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v2 — INTERNAL REVIEW FOLDED (research, `proposals/0019-internal-review.md`, 2026-08-14; RETURN FOR AMENDMENT, 1 blocking + 3 rulings + 2 notes): **F1 (the month's carrier class, caught PROSPECTIVELY)** — a new Edge field enters every surface that COMPARES, PROJECTS, or HASHES edges, and v1 never ruled its membership → §7b now rules ALL of them: `ungrounded` is EXCLUDED from identity/digest bases (extraction-fidelity metadata, not identity — two extractions of the same fact ARE the same fact; `contribution.py:142`'s frozen 0014 field basis is UNCHANGED, avoiding a digest rider), the merge survivor takes the OR of merged flags, the 0009 record-equality composition is RULED not lucky (absent→False composes; stored-True vs incoming-absent differs → refuses honestly), and the 0014 projection is untouched (an Edge field; the projection is over Episode fields). U-Q1 ruled: proactive suppression CONFIRMED — the false-positive COST differs by surface (queried recall contextualizes the marker; proactive would volunteer an alarm at ~50% precision); suppression is the SINGLE flag-keyed behavioural reduction and it withholds, never grants. U-Q2 ruled: the marker is **`[possible extraction error]`** — 'unverified' would collide with the attribution vocabulary AND a future Veracium run would score its own markers as attribution, contaminating the measurement that vindicated the attribution design (the artifact-seam lesson applied before the seam exists). U-Q3 ruled mechanical with three conditions (§7b). N1 marker-spoofing sentence; N2 the wiki-compiler re-render cell in U5. |
| **Status** | *see `Spec-Status:` — canonical.* |
| **Internal reviewers** | research (they built and measured the instrument; the ask records research+dev aligned on option A) |
| **External review** | required — `schema.py`, `ingest.py`, `gate.py`/render, `portability.py` are guarded; this adds a stored field and a rendered marker |
| **Decision + date** | — |
| **Path** | full |
| **Spec-Requires** | `0005` (accepted — the import boundary this flag crosses verbatim, §2c/§7b), `0008` (accepted — whose `needs_confirmation` contract this spec deliberately does NOT touch, §4d) |

> **Why a spec, not a patch.** The flag is one boolean, but its surface is
> not: a stored schema field, an export format field, a rendered marker the
> model sees, an import-boundary row, and a clearing-condition question that
> collides with two accepted contracts (0008's staleness semantics, 0009's
> append-not-mutate). Every one of those is a carrier; this month's reviews
> exist because carriers get missed.

---

## 1. Problem and motivation

**Veracium audits WHO said something; nothing audits WHETHER anyone said it.**
The whole trust surface — authorship, `derived_from`, disclosure, the 0003
ladder — operates on the claim's *provenance*. But the distiller (an LLM)
sits between the event text and the stored fact, and when it fabricates, its
output inherits the event's full trust standing. The one-exhibit case, found
in our own published run artifacts: the distiller added a YEAR to a dated
third-party news claim — "1 July 2023", no year anywhere in the source — and
that fact entered the store as first-person assertable testimony.

Five defect classes of this shape were demonstrated over 149k objects from
our own artifacts (`patchtest/phase1_RESULTS.md`): **wrong-value
extraction** · **cross-window import** · **fabricated specifics** (camera
shutter specs nowhere in the source) · **answered-question-as-fact** (user
asks "what was the EBITDA margin?" → the distiller stores `43%` — a value the
window never contains) · **computed-value-as-testimony** (a synthesized sum
stored as if stated). A sixth, **anticipatory generation** (requested slides
stored as the user's facts), surfaced at the final gate.

Today NOTHING on the write path can notice any of these. This spec adds the
noticing — and only the noticing.

---

## 2. Field contracts touched

| field | read / written | documented contract | consumers | change here |
|---|---|---|---|---|
| `Edge.ungrounded` | **NEW** — written ONCE at ingest by the §4b check; immutable thereafter (§4d) | "the specifics in this fact's object were not all grounded in the event text it was extracted from" — a property of the EXTRACTION, not of the fact's truth | render (marker), proactive (suppression), introspect (count), export (carried), import (§2c) | the whole spec |
| `Edge.needs_confirmation` | read only | 0008: staleness — "possibly outdated" | staleness machinery | **untouched — deliberately (§4d).** "Possibly never said" is a different fact from "possibly outdated"; overloading would need a 0008 amendment and would let staleness-clearing paths silently clear a fabrication signal |
| `assertable` / gate partition | read only | disclosure-keyed routing | gate, proactive, render | **UNCHANGED — flag-never-refuse extends to flag-never-demote (§4c).** At ~40–50% precision, demotion would wrongly bury a real fact roughly every second flag |
| `FORMAT_VERSION` | written: 5 → **6** | export carries every Edge field | `portability.py` | the flag exports; an older importer REFUSES a v6 file rather than silently dropping the field (the accepted 0014 R5-4 / 0010 refuse-don't-drop rule). **Collides with 0016 D2's claimed numbering — §7b** |
| `SCHEMA_VERSION` | written: 6 → **7** (no DDL — the field lives in `edges.json`, the 0006 v4→v5 precedent) | 0007: an older build refuses a newer store | `store/schema_version.py` | an older build silently DROPPING the flag on rewrite would erase a fabrication signal; refusal is the honest failure. **Collides with 0016 D2's claimed v7 — §7b** |

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| the event text (the grounding CORPUS for the check) | empty text → every specific ungrounded → flag set | — | — | **an attacker who authors the event text controls the grounding corpus** — they can make their OWN fabricated specifics "grounded" by writing them into the text | **by design: the check verifies extraction fidelity, never truth.** An attacker-grounded lie is a TRUST problem, fully handled by the existing levers (author/derived_from/disclosure); this flag adds a signal about the DISTILLER, not about the source. Stated as §8 limit 1 |
| the distiller output (the CHECKED object) | no specifics in the object → vacuously grounded, no flag | — | — | a fabricated value phrased without specifics ("a large amount") evades the specifics-only check | accepted, measured: the specifics-only class catches the VALUE-SHAPED fabrications (the ones that damage functional facts) at 0.47%/~40–50% precision; common-noun fabrication is the offline full predicate's territory (§8 limit 2) |
| an import file's `ungrounded` values (edges) | absent → pydantic default `False` | non-bool → pydantic raises (v6 file) | **pre-v6 envelope carrying the field → STRIPPED, never trusted (the 0006 I10 rule)** | a hand-written file sets `ungrounded=False` on fabricated content — or `True` on genuine content | **the flag GRANTS nothing and its absence grants nothing** — no consumer raises trust, assertability, or authority on it (I5-class groups-never-grants). Forging `False` gains exactly what the file already had; forging `True` triggers only the design's single flag-keyed reduction — proactive volunteering of the forger's OWN record is withheld — a self-inflicted narrowing, never a grant. Carried VERBATIM on both 0005 paths (§7b) — it is extraction-fidelity metadata, not a trust lever, so the cap neither reads nor writes it |
| the session date (feeds date-context awareness, §4b) | absent → today (the `remember` contract) | — | — | a crafted date shifts the ±366-day resolved-date window | the window bounds PLAUSIBILITY of resolved dates, never grants trust; a shifted window at worst flags/unflags a date token — the flag grants nothing (row above) |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | expected result |
|---|---|---|
| nothing currently audits extraction fidelity | `grep -rn "grounded\|fidelity" src/veracium/ingest.py` | no check between distill output and storage |
| `needs_confirmation` is staleness-owned | `grep -n "needs_confirmation" specs/0008-staleness-clearing.md \| head -3` | the 0008 contract |
| the flag would be the first Edge-field addition since 0009 | `git log --oneline -S "ungrounded" -- src/veracium/schema.py` | empty before this spec's implementation |
| import validates edges through the model | `grep -n "Edge.model_validate" src/veracium/portability.py` | the 0005 §4c-ii step-2 site |

*(Re-run at implementation; commands recorded per the 0005 execute-shipped-claims rule.)*

---

## 3. Trust-class matrix — REQUIRED, blocking

**No trust class moves.** The flag is orthogonal to the author/derivation
axes by construction:

| operation | trust consequence of the flag |
|---|---|
| ingest, check passes | none — field `False`, byte-identical behaviour to today |
| ingest, check fails | the edge stores with `ungrounded=True`; **author, derived_from, disclosure, assertable, gate partition all UNCHANGED** |
| any read | no consumer keys a trust/authority/staleness decision on the flag (I2); render adds a marker; proactive suppresses volunteering (§4c) |
| confirm / dispute / supersession / outcome | all operate exactly as today; none reads or writes the flag (§4d) |

The four §3 questions: no new write authority; no provenance change; no
`needs_confirmation` interaction; no authority movement.

**Write-time or maintain-time?** Write-time only (ingest). Maintenance
(absorption, consolidation) is OUT of v1 scope — consolidation outputs are
system-authored summaries with their own §8 disposition (limit 3).

## 3b. Authorization and scope

- **Who can set it:** the ingest check alone. Not host-settable, not
  model-settable, not MCP-reachable; import carries a file's stored values
  (§2c) but grants nothing on them.
- **What it reveals (the observation-surfaces lens — enumerate DISPLAYS, not
  just deciders):** the marker renders wherever the flagged fact renders
  (recall, introspect categories); `introspect()` gains a count. The flag
  reveals a property of OUR OWN extraction — no new information about any
  other principal, no oracle over prior store state (set at write time from
  the write's own inputs).
- **MCP:** no new tool, no new field in tool results beyond the fact
  rendering the same marker every other surface renders.

---

## 4. Behaviour

### 4a. The rule

> At ingest, after extraction and before storage, every extracted edge's
> OBJECT is checked by the §4b predicate against the event text. A failing
> edge is stored with **`ungrounded = True`** — stored, rendered, recallable,
> **never refused, never demoted, never re-derived**. The flag is set at most
> once, at ingest, and is immutable for the record's lifetime (§4d).

### 4b. The predicate — PINNED (phase 1f, specifics-only, all relations)

The v1 predicate is the measured phase-1f `specifics-only` check, pinned here
so the shipped behaviour is the measured behaviour:

- **Specifics tokens** of the object: (i) pure-digit tokens; (ii)
  alphanumeric identifiers (letters+digits mixed: `s21`, `10k`, `v6`); (iii)
  proper-noun runs (capitalized runs from the raw string, excluding a
  sentence-leading single capitalized common word).
- **Grounded** ⇔ the token (lowercased, word-tokenized) appears in the event
  text — with ONE class-aware exception: **date-context awareness** — an ISO
  date token triplet within ±366 days of the session date is treated as a
  legitimately RESOLVED date (the date pipeline mints dates the text never
  contains: "Friday" → `2026-06-05`), checked for plausibility, not verbatim
  presence.
- **The flag** ⇔ any specifics token of the object is not grounded.
- Zero LLM calls; deterministic; the measured operating point is **0.47%
  flag rate at ~40–50% precision** over 93,342 checkable objects, catching
  the value-shaped classes (§1). The implementation vendors the phase-1f
  reference (`patchtest/phase1f_speconly.py`, the `specifics_tokens` /
  `date_ok` pair) with test vectors pinned from the classified sample.
- **Predicate changes are spec changes.** Loosening or tightening the token
  classes, the date window, or the grounding rule re-enters review; the
  measured numbers are part of the contract.

### 4c. Consumers — flag-never-refuse, flag-never-demote, always-visible

- **Gate/partition: UNCHANGED.** A flagged fact keeps its disclosure-derived
  partition. Rationale: at ~40–50% precision, roughly every second flag is a
  false positive; demotion would silently bury real memories at that rate,
  which is refusal wearing a different hat.
- **Render: the marker.** Wherever a flagged fact renders (recall context,
  introspect categories, the compiled wiki), it carries a deterministic
  inline marker — **`[possible extraction error]`** — the same never-severed
  treatment as safety labels under 0012's budget clamps (a clamp shrinks
  content, never the marker). The model sees the doubt exactly where it sees
  the fact. **The name is RULED (internal review):** "unverified" vocabulary
  would collide with the third-party-claims fence AND with the attribution
  taxonomy — a future Veracium benchmark run would score its own
  extraction-error markers as attribution, contaminating exactly the
  measurement that vindicated attributed surfacing. **Marker spoofing:**
  event text containing the marker string is DATA and renders as content
  under the same anti-spoof posture as the existing unverified-claims fence
  — the render layer's own marker placement is the only authoritative one
  (N1).
- **Proactive: suppressed (RULED, internal review).** The false-positive
  COST differs by surface: queried recall shows the marker IN CONTEXT the
  user asked for; proactive would VOLUNTEER AN ALARM at ~50% precision.
  A flagged fact is never proactively surfaced; it remains fully recallable
  by query. **Suppression is the SINGLE flag-keyed behavioural reduction in
  the design, and it WITHHOLDS rather than grants** — which is why forging
  the flag gains nothing (§2c, stated precisely there).
- **Introspect:** the summary gains an `ungrounded` count; categories render
  the marker.
- **Answer/abstention, supersession, outcomes, staleness, wiki compile:**
  all UNCHANGED (the wiki compiler input renders the marker like any other
  surface; the compiler treats it as content).
- **Telemetry: NO new field in v1.** An `ungrounded` count would be a new
  whitelisted field requiring consent version 4 under the 0015 regime;
  deferred, recorded in §7a — the flag ships with zero telemetry surface.

### 4d. The clearing condition: there is none — the flag is immutable

The flag describes THE EXTRACTION EVENT — "the source text did not contain
these specifics" — and the extraction event never changes. Consequences:

- **`confirm()` does not clear it.** A user confirming a flagged fact
  vouches for the fact's TRUTH — recorded exactly as today (confirmation
  episode, validity refresh, confidence) — but cannot retroactively make the
  source text contain what it did not contain. Both facts are true and both
  stay visible: "the user confirmed this" and "the extraction was not
  grounded". A host wanting a clean record has the same answer 0005 §4d
  gives: an affirmation is new user-authored evidence and belongs in
  `remember()` — the restatement lands as a NEW, grounded edge, and the
  ordinary supersession/reinforcement machinery does the rest.
- **The merge survivor takes the OR (F1):** when identity-equal edges merge
  (absorption/dedup), the survivor is flagged iff ANY merged record was —
  once ungrounded, the surviving record stays flagged; a merge never
  launders the signal.
- **Nothing else clears it either**: no maintenance path, no import path, no
  host API. This is append-not-mutate (0009) applied to a diagnostic:
  re-derivation or clearing would make the flag a mutable judgment; as an
  immutable extraction property it needs no authority model, no clearing
  audit, and no 0008 amendment.
- *(Flagged for internal review: the confirm-does-not-clear cell is the
  spec's most reviewer-tempting target. The §8 limit states the honest
  cost: a confirmed-true fact can carry the marker forever; the remedy is
  restatement.)*

---

## 5. Regime analysis

| regime | behaviour |
|---|---|
| ingest, all specifics grounded | `ungrounded=False`; byte-identical to today everywhere |
| ingest, a specific ungrounded | flag set; stored + rendered with the marker; partition/trust unchanged |
| ingest, object with no specifics | vacuously grounded — no flag (the §2c evasion row; measured, accepted) |
| resolved relative date ("Friday" → ISO) | date-context aware — within ±366 days of session date, grounded |
| proactive recall | flagged facts never volunteered; query recall unaffected |
| confirm on a flagged fact | confirmation recorded (episode, validity, confidence); flag UNCHANGED |
| restatement of a flagged fact | a new grounded edge via the ordinary machinery; the flagged record retires or coexists per existing supersession rules |
| export → import (default path) | flag carried verbatim; the 0005 cap neither reads nor writes it |
| export → import (restore path) | same — trust-field-faithful restore is not widened; the flag is not a trust field but rides the same verbatim rule |
| pre-v6 file carrying the field | stripped (0006 I10); post-v6 absent → `False` |
| older build, v7 store | refused (0007) — never silent flag loss |

---

## 6. Invariants and executable checks — REQUIRED, blocking

**Status of every check: STAGE-5 OBLIGATION — none exists yet** (the 0005
R1-7 rule: a draft spec claims no CI).

| invariant | executable check | status |
|---|---|---|
| **U1** the check never refuses, never demotes: ingest outcomes and gate partitions are identical with the check enabled vs a counterfactual disabled run, except the flag and its marker | `test_ungrounded_never_refuses_or_demotes` | obligation — impl commit |
| **U2** no consumer grants or moves trust/authority/staleness on the flag — a sweep by FACT over every `ungrounded` reader | `test_ungrounded_grants_nothing` | obligation — impl commit |
| **U2b** the comparison/digest bases hold the F1 ruling: the flag is absent from the frozen `contribution.py` field basis and from the 0014 projection; a NEW Edge field cannot silently join either (basis-membership pinned) | `test_ungrounded_excluded_from_identity_bases` | obligation — impl commit |
| **U2c** the merge survivor takes the OR: identity-equal merge of flagged+unflagged yields a flagged survivor, in both merge orders | `test_merge_survivor_keeps_the_flag` | obligation — impl commit |
| **U3** the predicate matches the pinned phase-1f reference on the pinned vectors (incl. one per §1 defect class and the date-resolution exemption) | `test_predicate_matches_the_pinned_vectors` | obligation — impl commit |
| **U4** the flag is immutable: confirm/dispute/supersession/outcome/maintenance/import leave it byte-unchanged on existing rows | `test_ungrounded_is_immutable` | obligation — impl commit |
| **U5** the marker is never severed from a rendered flagged fact (the 0012 clamp rule), on every rendering surface — **including THROUGH the wiki compiler's re-rendering (N2: re-rendering is where markers get lost; the compiled-surface cell is explicit)** | `test_marker_survives_every_surface_and_clamp` | obligation — impl commit |
| **U6** proactive never volunteers a flagged fact; query recall returns it | `test_proactive_suppression` | obligation — impl commit |
| **U7** the import boundary: verbatim carriage both paths; pre-v6 strip; absent→False; forged values grant nothing | `test_import_carries_but_never_grants` | obligation — impl commit |
| **U8** version honesty: FORMAT 6 refused by older importers; SCHEMA v7 refused by older builds; the migration is additive-only | `test_version_gates_and_migration` | obligation — impl commit |
| **U9** introspect reports the count; MCP results carry no new field beyond the rendered marker | `test_observation_surfaces` | obligation — impl commit |

---

## 7. Failure modes and reversibility

- **False positives (~50–60% of flags at the measured point):** the designed
  cost ceiling — a marker on a true fact, never suppression (except
  proactive volunteering). Bounded by the 0.47% flag rate: ~1 in 400
  objects carries an unnecessary marker.
- **False negatives:** specifics-free fabrications pass (§2c; §8 limit 2).
  The offline full predicate remains the audit net.
- **Reversibility:** the behaviour is additive. Rolling back the BUILD:
  a v7 store refuses on an older build (backup first — the 0007 posture).
  Disabling the CHECK (if ever wanted) leaves stored flags inert: no
  consumer decision keys on them.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `schema.py` `Edge` | `ungrounded: bool = False` |
| `ingest.py` | the §4b check between extraction and storage |
| render / `gate.py` surfaces | the `[possible extraction error]` marker |
| `proactive.py` | the suppression rule |
| `introspect.py` | the count + category markers |
| `portability.py` | FORMAT 6; pre-v6 strip row; the flag in exports |
| `store/schema_version.py` + migration | SCHEMA v7, no-DDL, additive — **ordinary open-time `migrate_store` machinery, NEVER the 0018 orchestrator** (the orchestrator is D2's; U-Q3 condition 2) |
| `docs/api.md`, `docs/concepts.md` | the flag's meaning; the restatement remedy |
| telemetry | **no change in v1** (consent v4 deferred — recorded here so the deferral is a decision, not an omission) |
| MCP | no change |
| CHANGELOG | feature entry + the FORMAT/SCHEMA notes |

### 7b. Cross-spec carriers

| accepted spec | touchpoint | disposition |
|---|---|---|
| **0016 D2 / 0018** | D2's spec text claims FORMAT 5→6 and SCHEMA v6→v7 for the removal release; this spec, shipping FIRST, takes 6 and v7 | **the numbering shifts by one for D2 (→ FORMAT 7, SCHEMA v8) — mechanical IN CLASS, with the internal review's three pinned conditions: (1) the rider RE-STATES the full numbered matrix, never deltas (bases 1–5 → 1–6; base-6-alone → base-7-alone; current-v7 → v8; I13's "1–5" → "1–6" — the R14-2 literal-table rule); (2) §7a states this spec's own v6→v7 migration is ORDINARY open-time machinery, NEVER the 0018 orchestrator — so a never-opened v6 store at D2 correctly lands `unsupported-base` with the ladder naming the intermediate release; (3) the rider lands same-commit with this spec's acceptance flip PLUS a fact-search sweep of 0016 D1's text for any version numerals — **the sweep's first catch is already recorded: the RELEASED v0.9.0 CHANGELOG's D1 entry carries the pre-0019 numbering ("format 6, schema v7"); released text is immutable, so the rider adds a correcting note to the Unreleased CHANGELOG section when it lands (re-review clearance 1b7cd6fa)** |
| **0014 — comparison/digest bases (F1, ruled)** | `contribution.py:142` enumerates Edge fields BY NAME in the frozen 0014 receipt basis; the 0014 source-identity projection partitions Episode fields | **`ungrounded` is EXCLUDED from every identity/digest basis** — it is extraction-fidelity metadata, not identity: two extractions of the same fact ARE the same fact, flag or no flag. The frozen `contribution.py:142` field list is therefore UNCHANGED (no digest rider needed — the exclusion is the rider-avoiding ruling, pinned by a basis-membership test in U2b); the 0014 projection is untouched (an Edge field; the projection is over Episode fields — stated, not assumed) |
| **0009 — record-equality composition (F1, ruled not lucky)** | import compares validated models (`Edge.model_validate` normalizes absent→`False`) | RULED: a pre-v6 record (field absent → `False`) compares equal to a stored unflagged record — idempotent re-import composes; a stored `True` vs an incoming absent/`False` DIFFERS → whole-import refusal, the honest outcome (a file claiming a clean extraction for a record we flagged is a real difference). U7 asserts both cells |
| **0005** | the import boundary carries the flag verbatim on both paths; the cap is three levers and STAYS three | §2c row + U7; no 0005 text change — its cap contract never enumerated non-trust fields |
| **0008** | `needs_confirmation` NOT reused; no staleness path touches the flag | referenced only; U2/U4 enforce |
| **0009 (append-not-mutate)** | the immutability rationale; no outcome-machinery change | referenced only |
| **0012** | the marker inherits the never-severed clamp rule | referenced; U5 |
| **0015** | telemetry deferral — a future `ungrounded` count is consent-v4 work under the 0015 regime | recorded, deferred |

---

## 8. Claims and limits

**Claim:** after this spec, a stored fact whose object carries specifics the
source text never contained is visibly marked at every surface that shows it,
at zero refusal cost and zero trust movement.

**Limits, stated plainly:**

1. **The check verifies extraction fidelity, never truth.** An attacker who
   writes lies into the event text gets grounded lies — that is the trust
   levers' territory, already handled; this flag audits the distiller.
2. **Specifics-only:** fabrications phrased without numerals, identifiers,
   or proper nouns pass. Measured trade: the value-shaped classes are the
   catch; common-noun fabrication stays with the offline full predicate.
3. **Consolidation outputs are out of v1 scope** — system-authored summaries
   compress by design; grounding them against N source episodes is a
   different predicate with its own measurement. Recorded as the natural
   successor once the D-extension's value-level containment work lands.
4. **A confirmed-true flagged fact carries the marker for life** (§4d); the
   remedy is restatement. Honest cost of an immutable diagnostic.
5. **~Half of flags are false positives** at the measured point; the design
   spends that entirely on a marker, never on suppression.

---

## 9. Brief for the external reviewer

The fastest adversarial entry points: (a) §4d — construct a path that
SHOULD clear the flag and see whether immutability survives it (confirm is
the tempting one; the §8 limit is the honest price); (b) §4b — find a
specifics token class the tokenizer mis-handles (the phase-1 rounds document
the classes already fixed: derivational stems, compound splitting,
initialisms, number-words); (c) §2c — the attacker-grounded-lie row and the
no-specifics evasion row are the two designed boundaries: check they are
stated, not hidden; (d) §7b — the D2 renumbering is the cross-spec carrier
this month's reviews keep finding half-done.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~U-Q1~~ | **RULED (internal review): proactive suppression CONFIRMED** — the false-positive cost differs by surface; suppression withholds, never grants. §4c. | resolved | research | — |
| ~~U-Q2~~ | **RULED: the marker is `[possible extraction error]`** — avoids the fence-vocabulary collision AND the benchmark artifact-seam (a future run scoring its own markers as attribution). §4c. | resolved | research | — |
| ~~U-Q3~~ | **RULED: the D2 renumbering is mechanical IN CLASS under three pinned conditions** (full re-stated matrix; ordinary-machinery migration statement; same-commit rider + numeral sweep of D1 text). §7b. | resolved | research+dev | — |
