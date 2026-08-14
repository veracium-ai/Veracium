# Feature spec: the `ungrounded` flag — evidence-grounding at ingest

Spec-Status: draft
Spec-Requires: 0005, 0008, 0014, 0016, 0018

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft v3** — external round 1 folded (the 0014 amendment made real
> against the shipped digest construction; the renumbering amendments
> verbatim; the store guard; wiki exclusion; the date-expression-bound
> exemption; StrictBool). v2: internal review folded (F1: the comparison/projection/
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
| **Version** | v3 — EXTERNAL ROUND 1 FOLDED (7 blocking, 2026-08-14, classified first): **F1 (G+D)** the digest-exclusion ruling was FALSE against the frozen 0014 construction — `contribution.py:167/:189` snapshots the COMPLETE `model_dump_json`, so any new Edge field shifts the request digest regardless of partition membership (reviewer-executed) → the internal ruling is AMENDED BY THE CODE: `ungrounded` joins the 0014 partition as a **RECOMPUTED absorption field** (the OR is the same pre-persist winner-inheritance shape as the shipped confidence-max, `graph.py:91` — no post-snapshot mutation exists, dissolving the snapshot-conflict sub-finding), the digest shift gets era discrimination (**`outcome_digest_version` 3 — displacing D2's reserved 3 → 4**, joining the renumbering family), the verbatim 0014 rider is in §7b, and 0014 joins `Spec-Requires`. **F2 (D+F — the 0005 R3-3 class repeated with the class KNOWN, disclosed)** the D2 renumbering amendments now appear COMPLETE AND VERBATIM in §7b (both matrices re-stated per R14-2; 0016+0018 in `Spec-Requires`; separate cross-spec sign-off requested). **F3 (B+C)** the ingest-only/immutability claim had no authority mechanism — narrowed honestly + mechanized: no VERACIUM-MEDIATED surface sets the flag; a host writing its own store owns its bytes (it can already write `author=USER`); the STORE enforces the invariant that is enforceable — **the replace path refuses `ungrounded` True→False, mirroring the shipped 0008 §6d guard (`sqlite.py:116`)**; False→True is legal only as the absorption OR; every backend inventoried; the four write paths tested (U4 rewritten). **F4 (A+G)** the compiled-wiki marker guarantee was unconstructed (reviewer-executed: the fake LLM dropped the marker; the cache stored the unmarked fact) → **flagged facts are EXCLUDED from the wiki-compiler input** (the 0003 contested-exclusion precedent; the wiki is the curated grounded view) — the SECOND behavioural reduction, accounted in §4c/§8; the fact remains in query recall with its marker; U5 rewritten to the real mechanism. **F5 (A+C)** the ±366-day window grounded a fabricated date with NO date expression in the text (the reviewer's executed case) → the exemption is REBOUND: it applies ONLY when the event text contains a pinned date-expression (the §4b grammar: weekday/month names, day ordinals, numeric date patterns, relative-day terms) AND the ISO date is within the window — no expression, no exemption; the tokenizer is now normatively pinned (the exact regexes + the position-0 rule); the reference implementation and measurement excerpt ship IN-REPO (`specs/evidence/0019/`); the pinned 0.47% number is re-qualified as the window-form measurement with a pre-ship re-measurement obligation against the same 93,342-object corpus. **F6 (D+F, found-in-fix of the U-Q1 fold)** forged/absent `False` DOES grant proactive eligibility on the restore path → the honest matrix: the DEFAULT path is immune by composition (0005 caps disclosure to `use_only` → proactive-ineligible regardless of the flag); the RESTORE path exposure is accepted as a LIMIT under 0005 §8's own posture (restore is the operator's whole-file trust assertion — this included); §2c and §8 restated precisely. **F7 (F — the 0005 P13 class, and an unexecuted validation claim)** pydantic bool COERCES ("yes"→True) → **`StrictBool`** pinned; the exhaustive coercion cell list in U7. *(v2: internal review folded — carriers ruled, marker renamed, D2 conditions pinned. v1: the option-A draft.)* |
| **Status** | *see `Spec-Status:` — canonical.* |
| **Internal reviewers** | research (they built and measured the instrument; the ask records research+dev aligned on option A) |
| **External review** | required — `schema.py`, `ingest.py`, `gate.py`/render, `portability.py` are guarded; this adds a stored field and a rendered marker |
| **Decision + date** | — |
| **Path** | full |
| **Spec-Requires** | `0005` (accepted — the import boundary this flag crosses verbatim, §2c/§7b), `0008` (accepted — `needs_confirmation` untouched; its §6d store guard is the F3 precedent), **`0014` (accepted — FORMALLY AMENDED: the flag joins the RECOMPUTED absorption class; the request digest shifts → `outcome_digest_version` era bump; verbatim rider in §7b, R1-F1)**, **`0016` + `0018` (accepted — the complete verbatim renumbering amendments now IN §7b, R1-F2)** |

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
| `Edge.ungrounded` | **NEW — `StrictBool = False` (F7: pydantic's plain bool COERCES "yes"/0/1; the strict form raises on every non-boolean — the 0005 P13 closed-predicate posture)** — derived at ingest by the §4b check; MONOTONE thereafter (§4d: False→True only via the absorption OR; nothing ever clears True) | "the specifics in this fact's object were not all grounded in the event text it was extracted from" — a property of the EXTRACTION, not of the fact's truth | render (marker), proactive (suppression), introspect (count), export (carried), import (§2c) | the whole spec |
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
| an import file's `ungrounded` values (edges) | absent → `False` (see the adversarial cell — on restore this is a REAL eligibility grant, §8 limit 6) | **non-bool → `StrictBool` raises — coercive inputs ("false", "yes", 0, 1) REFUSE, never coerce (F7; the exhaustive cell list in U7)** | **pre-v6 envelope carrying the field → STRIPPED, never trusted (the 0006 I10 rule)** | a hand-written file sets `ungrounded=False` on fabricated content — or `True` on genuine content | **the flag GRANTS nothing and its absence grants nothing** — no consumer raises trust, assertability, or authority on it (I5-class groups-never-grants). **The forging matrix, honest (F6):** on the DEFAULT path, forging either value gains nothing — 0005 caps disclosure to `use_only`, so the record is proactive-ineligible regardless of the flag (immunity by COMPOSITION, stated not assumed). On the RESTORE path, a forged or absent `False` DOES obtain proactive-volunteering eligibility that a truthful `True` would not have — accepted as §8 limit 6 under 0005 §8's own posture: restore is the operator's explicit whole-file trust assertion, and the flag rides inside that assertion like every other preserved field. Forging `True` remains a self-inflicted narrowing. Carried VERBATIM on both 0005 paths (§7b) — it is extraction-fidelity metadata, not a trust lever, so the cap neither reads nor writes it |
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

- **Who can set it (F3, the honest claim):** no VERACIUM-MEDIATED surface
  sets it — not `remember`'s inputs, not the model, not MCP, not import
  grants. A host writing DIRECTLY to its own store owns its bytes (it can
  already write `author=USER`; the store boundary is the host's own trust
  domain — the standing posture). What the store DOES enforce is the
  enforceable invariant: **the replace path refuses an `ungrounded`
  True→False transition** (mirroring the shipped 0008 §6d
  `needs_confirmation` guard at `sqlite.py:116` — a flag, once earned, is
  not clearable by re-persistence); False→True on replace is refused too
  EXCEPT through the absorption OR (the one legal strengthening path).
  Every backend carries the guard: `SqliteStore` implements it; the `Store`
  base contract documents it as a persistence-path obligation (U4).
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
  text — with ONE class-aware exception, REBOUND at external round 1 (F5:
  the v2 window-only form declared a fabricated date grounded when the text
  contained NO date expression at all — the reviewer's executed case):
  **date-context awareness** — an ISO date token triplet is exempt from
  verbatim grounding IFF BOTH hold: (i) the event text contains at least one
  expression from the PINNED date-expression grammar below (something the
  date pipeline could have resolved), AND (ii) the date is within ±366 days
  of the session date (plausibility). No date expression in the text → no
  exemption → an unprompted ISO date is ungrounded.
- **The date-expression grammar, pinned (F5):** a token/phrase matching any
  of: weekday names (monday…sunday); month names (january…december, and
  three-letter forms); day ordinals (`1st`…`31st`, "the <1-31>(st|nd|rd|th)");
  numeric date patterns (`\d{1,4}[-/.]\d{1,2}([-/.]\d{1,4})?`); the
  relative-day lexicon (today, tomorrow, yesterday, tonight); and
  "next|last|this" followed by a day/week/month/year unit or weekday. The
  bare word "date" is NOT in the grammar (the reviewer's case).
- **The tokenizer, pinned normatively (F5 — two conforming implementations
  must agree):** words are `\w+` runs lowercased; a specifics token is (i) a
  pure-digit token, (ii) an identifier matching
  `^(?=.*[a-z])(?=.*\d)[a-z0-9]+$`, or (iii) a token of a capitalized run
  matching `\b[A-Z][a-zA-Z0-9]+` — EXCEPT a run that starts at string
  position 0 and ends before the first space (the sentence-leading rule:
  `Orange juice is fine` contributes nothing from "Orange"; `I like Orange
  County` contributes both words). There is NO lexicon: the position-0 rule
  is the whole disambiguation, deterministic by construction. The reference
  implementation and the final-gate measurement ship in this repo at
  `specs/evidence/0019/` (reviewer-safe, in-package).
- **The flag** ⇔ any specifics token of the object is not grounded.
- Zero LLM calls; deterministic. **The measured operating point — 0.47%
  flag rate at ~40–50% precision over 93,342 checkable objects — was
  measured under the v2 WINDOW-ONLY date exemption (F5 honesty): the
  rebound exemption is strictly TIGHTER (its flag set is a superset), so
  the shipped rate may rise. RE-MEASUREMENT against the same 93,342-object
  corpus is a PRE-SHIP implementation obligation (U3b); the numbers pinned
  at acceptance are the re-measured ones.** The implementation vendors the
  in-repo reference (`specs/evidence/0019/phase1f_reference.py`) with test
  vectors pinned from the classified sample.
- **Predicate changes are spec changes.** Loosening or tightening the token
  classes, the date window, or the grounding rule re-enters review; the
  measured numbers are part of the contract.

### 4c. Consumers — flag-never-refuse, flag-never-demote, always-visible

- **Gate/partition: UNCHANGED.** A flagged fact keeps its disclosure-derived
  partition. Rationale: at ~40–50% precision, roughly every second flag is a
  false positive; demotion would silently bury real memories at that rate,
  which is refusal wearing a different hat.
- **Render: the marker — and the wiki EXCLUSION (F4).** Wherever a flagged
  fact renders (recall context, introspect categories), it carries a
  deterministic inline marker — **`[possible extraction error]`** — the same never-severed
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
  (N1). **The compiled wiki is NOT a marker surface (F4 — reviewer-executed:
  the compiler stores an LLM's free-text output, and a code-owned marker
  cannot survive a re-rendering it does not control): flagged facts are
  EXCLUDED from the wiki-compiler INPUT** — the 0003 contested-exclusion
  precedent; the wiki is the curated grounded view, and a possibly-fabricated
  specific has no place in it. This is the design's SECOND behavioural
  reduction (with proactive suppression), accounted in §8 limit 5a; the fact
  remains fully reachable through query recall, with its marker.
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

### 4d. The clearing condition: there is none — the flag is MONOTONE

The flag describes THE EXTRACTION EVENT — "the source text did not contain
these specifics" — and the extraction event never changes. External round 1
(F1) refined "immutable" to the exact shipped-machinery form, **monotone
strengthening**: `False → True` happens in exactly ONE place — the
absorption OR (below) — and NOTHING ever clears `True`. Consequences:

- **`confirm()` does not clear it.** A user confirming a flagged fact
  vouches for the fact's TRUTH — recorded exactly as today (confirmation
  episode, validity refresh, confidence) — but cannot retroactively make the
  source text contain what it did not contain. Both facts are true and both
  stay visible: "the user confirmed this" and "the extraction was not
  grounded". A host wanting a clean record has the same answer 0005 §4d
  gives: an affirmation is new user-authored evidence and belongs in
  `remember()` — the restatement lands as a NEW, grounded edge, and the
  ordinary supersession/reinforcement machinery does the rest.
- **The absorption OR, on the SHIPPED mechanism (F1 — the internal ruling
  amended by the code):** shipped absorption (`graph.py:89-98`) retires the
  prior as `absorbed_duplicate` and the WINNER inherits validity/confidence
  as the max of the pair — a pre-persist winner-inheritance transform, not a
  stored-row mutation. `ungrounded` joins that inheritance: **the winner is
  flagged iff EITHER of the pair was** (OR), computed pre-persist exactly
  like the shipped max-inheritance — so no post-snapshot mutation exists,
  and the 0014 receipt machinery sees it through the RECOMPUTED class
  (§7b). Once ungrounded, the surviving representation stays flagged; a
  merge never launders the signal. (0012 reinforcement mutates NOTHING and
  is untouched: a restatement is its own edge with its own honestly-derived
  flag.)
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
| **U2b** the 0014 rider holds mechanically: `ungrounded` sits in `RECOMPUTED_EDGE_FIELDS`; post-0019 receipts stamp `outcome_digest_version` 3 and the validated set is {1,2,3}; the verifier accepts exactly the OR transform and aborts any other flag difference; the partition-totality test passes with the new field classified | `test_ungrounded_joins_the_recomputed_class` | obligation — impl commit |
| **U2c** the absorption OR on the shipped mechanism: flagged-prior+unflagged-incoming AND unflagged-prior+flagged-incoming both yield a flagged winner, computed pre-persist (the receipt verifies); 0012 reinforcement leaves both records' flags byte-untouched | `test_absorption_or_both_orders` | obligation — impl commit |
| **U3** the predicate matches the in-repo reference (`specs/evidence/0019/`) on the pinned vectors — incl. one per §1 defect class, the reviewer's F5 case (unprompted ISO date, NO date expression → FLAGGED), a grammar-positive resolution case ("Friday" + in-window ISO → grounded), and the position-0 tokenizer cells (`Orange juice` vs `Orange County`) | `test_predicate_matches_the_pinned_vectors` | obligation — impl commit |
| **U3b** the RE-MEASUREMENT (F5): the rebound predicate re-measured against the same 93,342-object corpus BEFORE the flag ships; the acceptance-pinned numbers are the re-measured ones, recorded in `specs/evidence/0019/` beside the reference | measurement obligation — pre-ship | obligation — impl commit |
| **U4** the flag is MONOTONE and the store enforces it (F3): confirm/dispute/supersession/outcome/maintenance/import leave stored flags byte-unchanged; the replace path REFUSES True→False (the 0008 §6d guard pattern) and refuses False→True except the absorption OR; host-set-at-insert, host-clear-attempt, import, and supersession-plan paths all tested; every backend carries the guard (SqliteStore + the Store base contract) | `test_ungrounded_monotone_store_guard` | obligation — impl commit |
| **U5** the marker is never severed on every CODE-RENDERED surface (the 0012 clamp rule), AND the wiki EXCLUSION holds (F4): flagged facts never enter the compiler input — tested with a compiler-fake that deliberately drops/rephrases markers, proving the guarantee never depended on LLM cooperation; the cached wiki contains no flagged fact and no orphaned marker | `test_marker_surfaces_and_wiki_exclusion` | obligation — impl commit |
| **U6** proactive never volunteers a flagged fact; query recall returns it | `test_proactive_suppression` | obligation — impl commit |
| **U7** the import boundary: verbatim carriage both paths; pre-v6 strip; **`StrictBool` refuses "false"/"yes"/0/1/null/containers and accepts only JSON true/false (F7, the exhaustive cell list)**; the F6 forging matrix asserted — default-path forged values inert BY COMPOSITION (capped→use_only→proactive-ineligible), restore-path forged False obtains eligibility (the documented §8 limit 6, asserted as the honest behaviour) | `test_import_strictbool_and_forging_matrix` | obligation — impl commit |
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
| **0016 D2 / 0018 — THE COMPLETE VERBATIM AMENDMENTS (external F2: v2 promised a future rider; the amendments are now IN the reviewed artifact, per the 0005 R3-3 rule; separate cross-spec sign-off requested)** | D2's frozen text claims FORMAT 5→6, SCHEMA v6→v7, `outcome_digest_version` 3, preflight bases 1–5, base-6-alone migration, current-v7 cells; 0018's result/preflight tables carry the same numerals | **Rider A → `specs/0016-sourcetype-deletion.md` (same-commit with 0019's acceptance):** <br> > **Amended by 0019:** 0019 ships FORMAT 6, SCHEMA v7, and `outcome_digest_version` 3 first. D2's numbers are re-stated in full: `Provenance.source_type` removal ships **FORMAT 6→7**; the receipt-era stamp for post-D2 receipts is **`outcome_digest_version = 4`** (the validated closed set at D2 extends to {1, 2, 3, 4}); the no-DDL refusal bump is **SCHEMA v7→v8**; every occurrence of "FORMAT 5→6", "v6→v7", and "version 3" in D2 rows reads with these replacements; D1 is unaffected (already released, no numerals). <br><br> **Rider B → `specs/0018-release-migration-orchestrator.md` (same commit):** <br> > **Amended by 0019:** the preflight interception matrix is re-stated in full — REFUSED bases: **1–6** (the ladder names the intermediate release for each; a v6-base store migrates to v7 on a 0019-era release BEFORE the D2 release); the sole audited pass-through base is **7** (was 6); the clean/with-repair CURRENT cells read **v8** (was v7); I13's "bases 1–5" reads **"bases 1–6"**. All other preflight semantics (attestation, mint, result carrier, readback) are unchanged. <br><br> Conditions honoured from the internal round: full matrices re-stated (never deltas, R14-2); §7a states 0019's own v6→v7 migration is ORDINARY open-time machinery, never the orchestrator; the released v0.9.0 CHANGELOG's stale D1 numerals get a correcting Unreleased note in the same commit || **0014 — FORMALLY AMENDED (external F1: the v2 exclusion ruling was FALSE against the shipped construction — `contribution.py:167/:189` snapshots the COMPLETE `model_dump_json`, so ANY new Edge field shifts the request digest; reviewer-executed)** | the receipt snapshot, the verification partition (`EXACT_EQUAL_*` / `RECOMPUTED_*` / `FORBIDDEN_*`), `outcome_digest_version` | **The rider, verbatim (lands in `specs/0014-maintenance-attribution.md` §2c in the same commit as this spec's acceptance flip; separate cross-spec sign-off requested):** <br><br> > **Amended by 0019 (same-commit with 0019's acceptance):** `Edge.ungrounded` joins the receipt machinery as follows. (1) The raw-request snapshot remains COMPLETE (`model_dump_json`, unchanged rule) and therefore includes the field; post-0019 receipts stamp **`outcome_digest_version = 3`** and the validated closed set extends to {1, 2, 3}; pre-0019 receipts follow the existing era rule unchanged. (2) In the verification partition, `ungrounded` is classified **RECOMPUTED** (`RECOMPUTED_EDGE_FIELDS` gains it): absorption's winner-inheritance may change it from the raw submission by exactly the OR of the pair (the same pre-persist shape as the shipped validity/confidence max) — the verifier accepts precisely that transform and aborts on any other difference. (3) The totality test's forced classification is thereby satisfied; no FORBIDDEN or EXACT_EQUAL semantics change. <br><br> The 0014 projection remains untouched (an Edge field; the projection partitions Episode fields). U2b now pins the RECOMPUTED membership + the version-3 stamp |
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
   spends that on a marker plus the two behavioural reductions below, never
   on refusal or demotion.
5a. **The two behavioural reductions (complete list):** proactive
   volunteering is suppressed (§4c), and flagged facts are excluded from
   the wiki-compiler input (F4 — a code-owned marker cannot survive an LLM
   re-rendering it does not control; the fact stays query-recallable with
   its marker). Nothing else keys on the flag.
6. **On the restore path, a forged or absent `False` obtains proactive
   eligibility** a truthful `True` would not have (F6). The default path is
   immune by composition with 0005's cap; the restore exposure sits inside
   the operator's whole-file trust assertion (0005 §8 limit 1's posture) and
   is accepted rather than patched with a tri-state.

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

---

## Review closure

*(PROCESS §4a — one row per finding.)*

| round | finding | class | disposition | evidence |
|---|---|---|---|---|
| int-1 | F1 carriers unruled (compare/project/hash surfaces) | C | folded (v2); the digest half later corrected by external F1 | v2 §7b; v3 rider |
| int-1 | U-Q1/U-Q2/U-Q3 rulings + N1/N2 | — | folded (v2) | v2 §4c/§7b |
| ext-1 | F1 the digest-exclusion ruling false vs the shipped complete-snapshot construction (reviewer-executed digest shift; the OR-vs-snapshot conflict) | G+D | **folded (v3): the internal ruling amended by the code** — RECOMPUTED-class membership, `outcome_digest_version` 3 (D2 → 4), the verbatim 0014 rider in §7b; the OR restated on the shipped winner-inheritance (no post-snapshot mutation exists); 0014 → Spec-Requires | v3 §4d, §7b; U2b/U2c |
| ext-1 | F2 the renumbering amendments absent from the artifact (the 0005 R3-3 class, repeated with the class known — disclosed) | D+F | **folded (v3):** both riders complete and verbatim in §7b (full matrices per R14-2); 0016+0018 → Spec-Requires; separate sign-off requested | v3 §7b |
| ext-1 | F3 no authority mechanism for ingest-only/immutability (store boundary omitted) | B+C | **folded (v3):** the claim narrowed honestly (no veracium-mediated surface; the host owns its bytes) + the enforceable half mechanized: the replace-path guard (the 0008 §6d pattern) refuses clearing; monotone False→True only via absorption; backends inventoried | v3 §3b, §4d; U4 |
| ext-1 | F4 the compiled-wiki marker guarantee unconstructed (reviewer-executed marker loss) | A+G | **folded (v3):** flagged facts EXCLUDED from the compiler input (the 0003 contested precedent); the second behavioural reduction accounted; U5 tests with a marker-dropping fake | v3 §4c, §8 5a; U5 |
| ext-1 | F5 the date window grounded expression-less fabricated dates; tokenizer under-specified; evidence absent | A+C | **folded (v3):** the exemption REBOUND to the pinned date-expression grammar AND the window; the tokenizer pinned normatively (incl. position-0); the reference + measurement in `specs/evidence/0019/`; the 0.47% re-qualified with the pre-ship re-measurement obligation (U3b) | v3 §4b; U3/U3b |
| ext-1 | F6 forged/absent False grants restore-path proactive eligibility (found-in-fix of the U-Q1 fold) | D+F | **folded (v3):** the honest forging matrix — default-path immunity by composition; the restore exposure accepted as §8 limit 6 under 0005's own posture | v3 §2c, §8 6; U7 |
| ext-1 | F7 pydantic bool coerces; the §2c raise claim false (unexecuted validation claim) | F | **folded (v3):** `StrictBool` pinned; the exhaustive coercion cells in U7 | v3 §2; U7 |
