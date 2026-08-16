# Feature spec: the `ungrounded` flag — evidence-grounding at ingest

Spec-Status: accepted
Spec-Requires: 0005, 0008, 0014, 0016, 0018

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **ACCEPTED v6 (2026-08-14, round 4 — approved on a finite boundary; the
> three pre-flip obligations folded in the flip commit)** — v5: round 3 (deterministic atomic spans;
> the canonical resolution table with anchored month-day pairing; the
> structural rationales; the v4-deleted 0014 rider RESTORED N-ary; the
> shipped rider-verification executable). v4: external round 2 folded (the resolution-set date rule;
> the portable normative reference + verified vectors; the N-ary OR; the
> total replace guard; the carrier sweep; complete final-form riders).
> v3: external round 1 folded (the 0014 amendment made real
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
| **Version** | v6 (ACCEPTED) — ROUND 4: APPROVED ON A FINITE BOUNDARY with three mandatory pre-flip obligations, all folded here: (1) LONGEST-MATCH PRECEDENCE — a weekday token inside a next|last|this span is consumed by it ("next Friday" resolves only forward; the reviewer's executed 2026-08-07 case is a pinned FLAGGED vector); the full regression matrix (next/last/this × member × the coexistence cell) joins U3 and the vectors (30 total, four-seed-verified). (2) every current false-positive number replaced by UNKNOWN-until-U3b (the superseded predicate keeps its historical figures, labeled). (3) BOTH reductions propagated through every carrier — §2's gate row, §7's failure modes, the honest rollback statement (disabling the check is NOT full rollback: existing True flags stay consumed by both filters), and the restore forging matrix/U7 covering proactive AND wiki eligibility. Cleanups: the duplicated tokenizer heading; the reference's stale v4 label. THE FLIP IS ATOMIC: the 0014 rider, Rider A (0016), Rider B (0018), and the CHANGELOG correcting note land in this commit under the round-4 cross-spec sign-off; the numeral-sweep output is in the commit message. *(v5: round 3. v4: round 2. v3: round 1. v2: internal. v1: draft.)* |
| **Status** | *see `Spec-Status:` — canonical.* |
| **Internal reviewers** | research (they built and measured the instrument; the ask records research+dev aligned on option A) |
| **External review** | required — `schema.py`, `ingest.py`, `gate.py`/render, `portability.py` are guarded; this adds a stored field and a rendered marker |
| **Decision + date** | **ACCEPTED 2026-08-14 — external round 4, APPROVED ON A FINITE BOUNDARY** (findings 7/6/5/3-obligations; the frozen surface is §§2–5, U1–U9/U3b, the N-ary pre-insert absorption OR, the total same-ID transition guard, the exact two-consumer reduction set, and §7b's complete riders). **The separate cross-spec sign-off for the 0014 and 0016/0018 riders was GRANTED at round 4** (the rider-verification executable passing); the three riders + the CHANGELOG correcting note land in THIS flip commit — the atomic pattern. The three mandatory pre-flip obligations are folded in this same commit (longest-match weekday precedence + the regression matrix; unknown-until-U3b for every current false-positive number; both reductions propagated through §2c/§7/§8-limit-6/U7 with the honest rollback statement). Implementation gated on U1–U9 + U3b's pre-ship re-measurement |
| **Path** | full |
| **Spec-Requires** | `0005` (accepted — the import boundary this flag crosses verbatim, §2c/§7b), `0008` (accepted — `needs_confirmation` untouched; its §6d store guard is the F3 precedent), **`0014` (accepted — FORMALLY AMENDED: the flag joins the RECOMPUTED absorption class; the request digest shifts → `outcome_digest_version` era bump; verbatim rider in §7b, R1-F1)**, **`0016` + `0018` (accepted — the complete verbatim renumbering amendments now IN §7b, R1-F2)** |

> **Why a spec, not a patch.** The flag is one boolean, but its surface is
> not: a stored schema field, an export format field, a rendered marker the
> model sees, an import-boundary row, and a clearing-condition question that
> collides with two accepted contracts (0008's staleness semantics, 0009's
> append-not-mutate). Every one of those is a carrier; this month's reviews
> exist because carriers get missed.

---

> **Amended by 0020/0021 (same-commit with the coupled acceptance flip,
> 2026-08-16; external sign-off at review round 14; research's cross-spec
> sign-off at `veracium-research/proposals/0020-0021-rider-signoff.md` @
> 023e11a9; the drafted rider row of 0021 §7b, landed verbatim).** >
> **Amended by 0020/0021.** (C1) Rider A(A3)'s SCHEMA clause, final: D2 ships
> SCHEMA v7→v8 **CARRYING DDL** — `contribution_ledger` gains
> `contributor_type TEXT` and `contributor_ref TEXT` (nullable; legacy rows
> NULL) — replacing the no-DDL characterization. The refusal-bump semantics
> are RETAINED (a v8 store refuses on pre-D2 builds — back up first); FORMAT
> 6→7 and the receipt-era rules (A1/A2) are UNCHANGED. (C2) THE v8
> MANIFESTATIONS — GENERATED NOW, not promised (R10-4: the previous clause
> deferred them): `specs/evidence/0020/schema_v8_evidence.py` reads the
> SHIPPED `SCHEMA_V7` constructor (never retyped), emits (i) the LITERAL v8
> CONSTRUCTOR (the v7 text + the two columns appended after `created_at`) and
> (ii) the MEASURED ALTER-path stored DDL (a real database built from v7, the
> two ALTERs run, sqlite_master read back — byte-distinct from the
> constructor per the 0014 supersession_operations precedent), PROVES
> table_info parity between them, and sha-pins both texts and both migration
> steps; the recorded output (`schema_v8_evidence.txt`) ships in this package
> and its shas are the review anchor. At the acceptance flip the same
> generator runs on the QUALIFIED runtime and its output enters
> `specs/schema_evidence.py`'s generated evidence — regenerated, never
> hand-authored. (C3) THE MIGRATION CONTRACT: v7→v8 runs ONLY under the 0018
> orchestrator (0019 U-Q3 condition 2 unchanged — D2 is the orchestrator's);
> the migration's 0013-declared steps are EXACTLY the two ALTER statements,
> sha-pinned IN THE RECORDED EVIDENCE (per 0013's declared-step contract —
> the 0016 declared-no-op-step precedent, upgraded to real steps); rollback
> is 0018's attestation/backup contract, unchanged. (C4) THE 0007 CLAUSE: v8
> is a STAMPED version whose shape evidence includes BOTH manifestations;
> unstamped resolution rules unchanged. (C5) the 0019 R2-6 executable numeral
> sweep RE-RUNS at the flip commit with every "no-DDL" hit disposed — each
> carries this rider's replacement or is historical-marked; the sweep output
> ships in the flip commit's message.

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
| `assertable` / gate partition | read only | disclosure-keyed routing | gate, proactive, render | **UNCHANGED — flag-never-refuse extends to flag-never-demote (§4c).** The rationale is STRUCTURAL, not numeric (R3-3): at any precision materially below 1, demotion silently buries real facts — which is refusal wearing a different hat; the design spends false positives on a marker plus exactly the two withholding reductions (§4c: proactive suppression; wiki exclusion) — never on refusal or demotion |
| `FORMAT_VERSION` | written: 5 → **6** | export carries every Edge field | `portability.py` | the flag exports; an older importer REFUSES a v6 file rather than silently dropping the field (the accepted 0014 R5-4 / 0010 refuse-don't-drop rule). **Collides with 0016 D2's claimed numbering — §7b** |
| `SCHEMA_VERSION` | written: 6 → **7** (no DDL — the field lives in `edges.json`, the 0006 v4→v5 precedent) | 0007: an older build refuses a newer store | `store/schema_version.py` | an older build silently DROPPING the flag on rewrite would erase a fabrication signal; refusal is the honest failure. **Collides with 0016 D2's claimed v7 — §7b** |

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| the event text (the grounding CORPUS for the check) | empty text → every specific ungrounded → flag set | — | — | **an attacker who authors the event text controls the grounding corpus** — they can make their OWN fabricated specifics "grounded" by writing them into the text | **by design: the check verifies extraction fidelity, never truth.** An attacker-grounded lie is a TRUST problem, fully handled by the existing levers (author/derived_from/disclosure); this flag adds a signal about the DISTILLER, not about the source. Stated as §8 limit 1 |
| the distiller output (the CHECKED object) | no specifics in the object → vacuously grounded, no flag | — | — | a fabricated value phrased without specifics ("a large amount") evades the specifics-only check | accepted by design: the specifics-only class catches the VALUE-SHAPED fabrications (the ones that damage functional facts) — the class choice was measured on the superseded form (§4b provenance note); the candidate's own operating point comes from U3b; common-noun fabrication is the offline full predicate's territory (§8 limit 2) |
| an import file's `ungrounded` values (edges) | absent → `False` (see the adversarial cell — on restore this is a REAL eligibility grant, §8 limit 6) | **non-bool → `StrictBool` raises — coercive inputs ("false", "yes", 0, 1) REFUSE, never coerce (F7; the exhaustive cell list in U7)** | **pre-v6 envelope carrying the field → STRIPPED, never trusted (the 0006 I10 rule)** | a hand-written file sets `ungrounded=False` on fabricated content — or `True` on genuine content | **the flag grants no TRUST — no consumer raises trust, assertability, or authority on it (I5-class groups-never-grants) — but absence is NOT behaviourally inert on the restore path (the matrix below; the superseded blanket absence-grants-nothing claim is WITHDRAWN, R2-5).** **The forging matrix, honest (F6):** on the DEFAULT path, forging either value gains nothing — 0005 caps disclosure to `use_only`, so the record is proactive-ineligible regardless of the flag (immunity by COMPOSITION, stated not assumed). On the RESTORE path, a forged or absent `False` DOES obtain BOTH flag-keyed eligibilities — proactive volunteering AND wiki-compiler membership — that a truthful `True` would not have — accepted as §8 limit 6 under 0005 §8's own posture: restore is the operator's explicit whole-file trust assertion, and the flag rides inside that assertion like every other preserved field. Forging `True` remains a self-inflicted narrowing. Carried VERBATIM on both 0005 paths (§7b) — it is extraction-fidelity metadata, not a trust lever, so the cap neither reads nor writes it |
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

**Write-time or maintain-time?** Write-time only — stated precisely
(R2-5): ingest DERIVES the flag, and write-time ABSORPTION (which fires on
fresh evidence, `graph.py:98` — it is not maintenance) computes the new
survivor's N-ary OR pre-insert. MAINTAIN-TIME machinery (consolidation,
expiry) neither reads nor writes the flag; consolidation outputs are
system-authored summaries with their own §8 disposition (limit 3).

## 3b. Authorization and scope

- **Who can set it (F3, made ENFORCEABLE by R2-4):** no VERACIUM-MEDIATED
  surface sets it — not `remember`'s inputs, not the model, not MCP, not
  import grants. A host writing DIRECTLY to its own store owns its bytes
  (it can already write `author=USER`; the store boundary is the host's
  own trust domain — the standing posture). The store enforces exactly the
  invariant that needs no authority discriminator: **the same-ID replace
  path refuses EVERY `ungrounded` transition, in BOTH directions**
  (mirroring the shipped 0008 §6d guard shape at `sqlite.py:116`). No
  exception exists to discriminate, because shipped absorption NEVER
  replaces same-ID: it inserts a NEW survivor row whose flag is the N-ary
  OR computed pre-insert (R2-3) — the strengthening happens before the row
  exists, so the persistence layer sees only immutable flags. Every
  backend carries the guard: `SqliteStore` implements it; the `Store` base
  contract documents it as a persistence-path obligation (U4).
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
  text — with ONE class-aware exception, REBOUND AGAIN at external round 2
  (R2-1, found-in-fix of R1-F5: the v3 grammar-exists+window form still
  grounded a fabricated deadline when an UNRELATED date expression existed
  anywhere — "I met Bob Friday. The project deadline is undecided" +
  fabricated `2026-09-01` passed): **the RESOLUTION-SET rule** — an ISO date
  token is exempt from verbatim grounding IFF it is a MEMBER of the
  resolution set: the union, over every date expression the §4b grammar
  finds in the event text, of that expression's DETERMINISTIC resolutions
  against the session date. The fabricated date must EQUAL the resolution of
  a specific source expression; proximity to the session date grounds
  nothing by itself.
- **THE CANONICAL RESOLUTION TABLE (R3-2 — one table, and the normative
  reference implements exactly it; the v4 prose contradicted its own
  reference in three places and is REPLACED whole):** with session date S,
  `delta = (weekday_index − S.weekday()) mod 7`:

  | expression class (anchored — the grammar below) | resolutions |
  |---|---|
  | weekday name W | `S + (delta or 7)` and `S − ((7 − delta) mod 7 or 7)`; PLUS `S` itself iff `delta == 0` — **two members normally, THREE when the session falls on W** (e.g. "Friday" at session `2026-08-14`, itself a Friday: {`2026-08-07`, `2026-08-14`, `2026-08-21`})  **LONGEST-MATCH PRECEDENCE (round-4 obligation 1): a weekday token inside a `next|last|this <weekday>` span is CONSUMED by that span — the bare-weekday members do NOT apply to it** ("We meet next Friday" at session `2026-08-14` resolves ONLY `2026-08-21`); a separate bare occurrence of the same weekday elsewhere contributes its members normally |
  | today / tonight | `S` |
  | tomorrow / yesterday | `S ± 1` |
  | "next/last/this" + weekday/week/month/year | the single arithmetic resolution (next=+1 unit, last=−1, this=0; month arithmetic clamps the day to the target month's length) |
  | ANCHORED month-day pair — `"<month> <d>(st|nd|rd|th)?"` or `"<d>(st|nd|rd|th)? (of )?<month>"`, adjacency REQUIRED in the raw text (span-bound: "July had 12 projects" pairs nothing) | that (month, d) in the session year and both adjacent years |
  | a bare month name with NO anchored day | **NO resolutions** — month granularity cannot deterministically resolve to any day, day 1 included |
  | numeric date pattern `\d{1,4}[-/.]\d{1,2}([-/.]\d{1,4})?` | its calendar completions (Y-M-D / D-M-Y / M-D-Y readings; 2-digit years +2000; M-D and D-M readings across the session year ±1) |

  Every resolution is window-filtered to ±366 days of S. **The grammar IS
  this table's expression-class column — enumerated here, nowhere else**
  (the v4 text pointed at a "§4b grammar" it no longer contained).
- **Determinism (R3-1):** ISO date spans in the OBJECT are parsed and
  judged ATOMICALLY by character position — a digit token belongs to a span
  iff it lies inside that span's character range, never by shared-token
  membership over an unordered set (the round-3 nondeterminism, executed
  across `PYTHONHASHSEED` values). Multi-date objects and hash-seed
  regressions are pinned vectors; the reference is seed-independent by
  construction.
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
- Zero LLM calls; deterministic. **The measurement provenance, stated
  honestly (R2-2): the 0.47% / ~40–50% figures were measured over the
  SUPERSEDED window-only predicate and justify only the OPTION-A CLASS
  CHOICE (specifics-only over full), not the current predicate's operating
  point.** The resolution-set form is strictly tighter on dates (its flag
  set is a superset), so 0.47% is a lower bound on the flag rate; precision
  is UNKNOWN until re-measured. The shipped predicate's numbers come
  exclusively from U3b's pre-ship re-measurement, recorded beside the
  reference before acceptance-pinned figures are quoted anywhere.
- **The normative reference is `specs/evidence/0019/reference_predicate.py`
  (R2-2): a PORTABLE, PURE implementation of exactly this section — no
  external paths, no I/O, no corpus dependency — with the pinned vectors in
  `specs/evidence/0019/vectors.json` (both reviewer cases included as
  FLAGGED vectors). The historical `phase1f_*` files remain as clearly
  headed SUPERSEDED provenance for the option-A measurement; they are not
  the candidate.**
- **Predicate changes are spec changes.** Loosening or tightening the token
  classes, the date window, or the grounding rule re-enters review; the
  measured numbers are part of the contract.

### 4c. Consumers — flag-never-refuse, flag-never-demote, always-visible

- **Gate/partition: UNCHANGED.** A flagged fact keeps its disclosure-derived
  partition. Rationale (structural, R3-3): at any precision materially below 1, a
  flag may be a false positive; demotion would silently bury real memories,
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
  user asked for; proactive would VOLUNTEER AN UNPROMPTED ALARM whose reliability is, structurally, the flag's own.
  A flagged fact is never proactively surfaced; it remains fully recallable
  by query. **The flag keys exactly TWO behavioural reductions — this
  suppression and the wiki exclusion (the closed list, §8 limit 5a) — and
  both WITHHOLD rather than grant** (§2c states the forging consequences
  precisely; the restore-path absence exposure is §8 limit 6).
- **Introspect:** the summary gains an `ungrounded` count; categories render
  the marker.
- **Answer/abstention, supersession, outcomes, staleness:** all UNCHANGED.
  (The wiki compiler is NOT unchanged — its input excludes flagged facts,
  the F4 bullet above; the superseded v2 claim that the compiler "treats
  the marker as content" is WITHDRAWN, R2-5.)
- **Telemetry: NO new field in v1.** An `ungrounded` count would be a new
  whitelisted field requiring consent version 4 under the 0015 regime;
  deferred, recorded in §7a — the flag ships with zero telemetry surface.

### 4d. The clearing condition: there is none — the flag is MONOTONE

The flag describes THE EXTRACTION EVENT — "the source text did not contain
these specifics" — and the extraction event never changes. Rounds 1–2
refined "immutable" to the exact shipped-machinery form: **a STORED row's
flag never changes at all** (the same-ID replace path refuses every
transition, R2-4); strengthening exists only PRE-PERSIST — the N-ary
absorption OR computes the NEW survivor's flag before its row is inserted.
Nothing ever clears `True` anywhere. Consequences:

- **`confirm()` does not clear it.** A user confirming a flagged fact
  vouches for the fact's TRUTH — recorded exactly as today (confirmation
  episode, validity refresh, confidence) — but cannot retroactively make the
  source text contain what it did not contain. Both facts are true and both
  stay visible: "the user confirmed this" and "the extraction was not
  grounded". A host wanting a clean record has the same answer 0005 §4d
  gives: an affirmation is new user-authored evidence and belongs in
  `remember()` — the restatement lands as a NEW, grounded edge, and the
  ordinary supersession/reinforcement machinery does the rest.
- **The absorption OR, N-ARY on the shipped mechanism (R2-3 — the reviewer
  executed a one-incoming-absorbs-TWO-priors case; "pair" was wrong):**
  shipped absorption retires EVERY absorbed prior as `absorbed_duplicate`
  and the WINNER inherits validity/confidence maxima — a pre-persist
  winner-inheritance transform over the whole contributor set, not a
  stored-row mutation. `ungrounded` joins that inheritance: **the winner is
  flagged iff the raw incoming OR ANY absorbed contributor is flagged** —
  the OR over `{incoming} ∪ absorbed`, independent of iteration order,
  computed pre-persist BEFORE the new survivor row is inserted (R2-4). No
  post-snapshot mutation exists; the 0014 receipt machinery sees exactly
  this transform through the RECOMPUTED class (§7b). Once ungrounded, the
  surviving representation stays flagged; a merge never launders the
  signal. U2c tests zero, one, and many contributors, in every
  flag-placement permutation. (0012 reinforcement mutates NOTHING and is
  untouched: a restatement is its own edge with its own honestly-derived
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
| an ISO date matching a resolution of a specific anchored source expression | grounded (the §4b RESOLUTION-SET rule — membership, never proximity) |
| an ISO date with NO anchored source expression, or near one it does not resolve from | flagged (both reviewer cases are pinned vectors) |
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
| **U2b** the 0014 rider holds mechanically: `ungrounded` sits in `RECOMPUTED_EDGE_FIELDS`; post-0019 receipts stamp `outcome_digest_version` 3 and the validated set is {1,2,3}; **the verifier RECOMPUTES the N-ary OR from the plan's full contributor set (R3-4 — the transform is contributor-set-bound, not pairwise)** and aborts any other flag difference; the partition-totality test passes with the new field classified | `test_ungrounded_joins_the_recomputed_class` | obligation — impl commit |
| **U2c** the N-ary absorption OR (R2-3/R3-4): with ZERO absorbed contributors the incoming flag passes through; with ONE and with MANY, the winner is flagged iff the raw incoming or ANY contributor is — asserted over every flag-placement PERMUTATION of a three-contributor case and independent of contributor iteration order; 0012 reinforcement leaves every record's flag byte-untouched | `test_absorption_or_nary_permutations` | obligation — impl commit |
| **U3** the predicate matches the in-repo reference (`specs/evidence/0019/`) on the pinned vectors — incl. one per §1 defect class, the reviewer's F5 case (unprompted ISO date, NO date expression → FLAGGED), a grammar-positive resolution case ("Friday" + in-window ISO → grounded), and the position-0 tokenizer cells (`Orange juice` vs `Orange County`), **and the round-4 longest-match REGRESSION MATRIX (next/last/this × {past, session, forward} members + the qualified-and-bare coexistence cell)** | `test_predicate_matches_the_pinned_vectors` | obligation — impl commit |
| **U3b** the RE-MEASUREMENT (F5): the rebound predicate re-measured against the same 93,342-object corpus BEFORE the flag ships; the acceptance-pinned numbers are the re-measured ones, recorded in `specs/evidence/0019/` beside the reference | measurement obligation — pre-ship | obligation — impl commit |
| **U4** stored flags never change and the store enforces it TOTALLY (R2-4/R3-4): confirm/dispute/supersession/outcome/maintenance/import leave stored flags byte-unchanged; the same-ID replace path REFUSES EVERY `ungrounded` transition in BOTH directions — no exception exists (absorption inserts a NEW survivor with the N-ary OR computed pre-insert, so no discriminator is needed); host-set-at-insert (accepted), host-clear-attempt (refused), host-flag-attempt-on-replace (refused), import, and supersession-plan paths all tested; every backend carries the guard (SqliteStore + the Store base contract) | `test_ungrounded_total_replace_guard` | obligation — impl commit |
| **U5** the marker is never severed on every CODE-RENDERED surface (the 0012 clamp rule), AND the wiki EXCLUSION holds (F4): flagged facts never enter the compiler input — tested with a compiler-fake that deliberately drops/rephrases markers, proving the guarantee never depended on LLM cooperation; the cached wiki contains no flagged fact and no orphaned marker | `test_marker_surfaces_and_wiki_exclusion` | obligation — impl commit |
| **U6** proactive never volunteers a flagged fact; query recall returns it | `test_proactive_suppression` | obligation — impl commit |
| **U7** the import boundary: verbatim carriage both paths; pre-v6 strip; **`StrictBool` refuses "false"/"yes"/0/1/null/containers and accepts only JSON true/false (F7, the exhaustive cell list)**; the F6 forging matrix asserted — default-path forged values inert BY COMPOSITION (capped→use_only→proactive-ineligible), restore-path forged/absent False obtains BOTH eligibilities — proactive volunteering AND wiki membership — asserted for each consumer separately (the documented §8 limit 6) | `test_import_strictbool_and_forging_matrix` | obligation — impl commit |
| **U8** version honesty: FORMAT 6 refused by older importers; SCHEMA v7 refused by older builds; the migration is additive-only | `test_version_gates_and_migration` | obligation — impl commit |
| **U9** introspect reports the count; MCP results carry no new field beyond the rendered marker | `test_observation_surfaces` | obligation — impl commit |

---

## 7. Failure modes and reversibility

- **False positives (rate UNKNOWN until the U3b re-measurement — round-4 obligation 2; the superseded predicate measured ~50–60%, historical only):** the designed
  cost ceiling — a marker on a true fact, plus the two §4c withholding
  reductions (proactive volunteering suppressed; the fact excluded from the
  wiki-compiler input), never refusal or demotion. Rate bounds come from
  U3b's re-measurement (the superseded form measured ~1 in 400 objects;
  the candidate's own rate is pinned there before ship).
- **False negatives:** specifics-free fabrications pass (§2c; §8 limit 2).
  The offline full predicate remains the audit net.
- **Reversibility:** the behaviour is additive. Rolling back the BUILD:
  a v7 store refuses on an older build (backup first — the 0007 posture).
  Disabling the CHECK (if ever wanted) stops NEW flags but is NOT full
  rollback (round-4 obligation 3, stated honestly): existing `True` flags
  remain consumed by BOTH reductions — the proactive filter and the wiki
  exclusion keep acting on them, and no clearing path exists (§4d). A host
  wanting flagged facts back in those surfaces restates them (the §4d
  remedy); nothing else keys on the flag.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `schema.py` `Edge` | `ungrounded: StrictBool = False` (F7 — never plain `bool`) |
| `graph.py` (absorption) | the N-ary OR over `{incoming} ∪ absorbed`, computed pre-insert on the new survivor (R2-3/R2-4) |
| `contribution.py` | `RECOMPUTED_EDGE_FIELDS` gains `ungrounded`; the verifier accepts exactly the N-ary OR transform; `outcome_digest_version` 3 (the 0014 rider, §7b) |
| `compile.py` | the wiki-compiler INPUT filter: flagged facts excluded (F4) |
| `store/sqlite.py` + `store/base.py` | the same-ID replace guard: EVERY `ungrounded` transition refused (R2-4); the base contract documents the obligation |
| `specs/evidence/0019/` | the normative `reference_predicate.py` + `vectors.json` + the superseded-labeled phase-1f provenance + `rider_verification.py` with its output artifact; **the U3b re-measurement record DOES NOT EXIST YET (R3-3) — it is created by the implementation before ship, and no acceptance-time claim rests on it** |
| same-commit amendment surfaces | `specs/0014-maintenance-attribution.md` §2c (the rider), `specs/0016-sourcetype-deletion.md` (Rider A), `specs/0018-release-migration-orchestrator.md` (Rider B), the Unreleased-CHANGELOG correcting note — all land with the acceptance flip |
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
| **0014 — FORMALLY AMENDED (external R1-F1, RESTORED at R3-5: the v4 table edit deleted this row while every cross-reference still claimed it — the round-3 reviewer caught the absence; restored with the transform upgraded to the R2-3 N-ary form)** | the receipt snapshot, the verification partition (`EXACT_EQUAL_*` / `RECOMPUTED_*` / `FORBIDDEN_*`), `outcome_digest_version` | **The rider, verbatim (lands in `specs/0014-maintenance-attribution.md` §2c in the same commit as this spec's acceptance flip; separate cross-spec sign-off requested):** <br><br> > **Amended by 0019 (same-commit with 0019's acceptance):** `Edge.ungrounded` joins the receipt machinery as follows. (1) The raw-request snapshot remains COMPLETE (`model_dump_json`, unchanged rule) and therefore includes the field; post-0019 receipts stamp **`outcome_digest_version = 3`** and the validated closed set extends to {1, 2, 3}; pre-0019 receipts follow the existing era rule unchanged. (2) In the verification partition, `ungrounded` is classified **RECOMPUTED** (`RECOMPUTED_EDGE_FIELDS` gains it): absorption's winner-inheritance may change it from the raw submission by EXACTLY the N-ary OR over `{the raw incoming} ∪ {every absorbed contributor}` — order-independent, the same pre-persist shape as the shipped validity/confidence maxima — and the verifier accepts precisely that transform (recomputing the OR from the plan's full contributor set) and aborts on any other difference. (3) The totality test's forced classification is thereby satisfied; no FORBIDDEN or EXACT_EQUAL semantics change. <br><br> The 0014 projection remains untouched (an Edge field; the projection partitions Episode fields). U2b pins the RECOMPUTED membership, the N-ary transform, and the version-3 stamp |
| **0016 D2 / 0018 — THE COMPLETE FINAL-FORM AMENDMENTS (R2-6: the v3 riders were still deltas — "replace occurrences" and "remainder unchanged" are not amendments a freeze can sign; every affected table is now restated WHOLE, final numbers only)** | 0016 D2's version/format/receipt rows; 0018's fifteen-row preflight table, base rows, and I13 | **Rider A → `specs/0016-sourcetype-deletion.md` (same-commit with 0019's acceptance flip; the full final form):** <br> > **Amended by 0019.** (A1) THE RECEIPT-VERSION TABLE, final: `outcome_digest_version` 1 = legacy pre-0014-split receipts (migrated reads); 2 = 0014-era writers; **3 = 0019-era writers (the `ungrounded`-bearing snapshot)**; **4 = post-D2 writers (the `source_type`-less snapshot)**. The validated closed set is {1,2,3} from 0019's release and {1,2,3,4} from D2's. (A2) THE D2 ERA BOUNDARY, final: at and after D2, **a receipt with version < 4 refuses UNCONDITIONALLY ON SIGHT at both phases — no digest is computed, no comparison branch exists** (`ReceiptSchemaBoundaryError(SupersessionIntegrityError)`, never benign); a version-4 receipt follows the ordinary 0014 contract. The pre-D2 exploding-sentinel regression enumerates the legal pre-D2 states over versions {1,2,3}. (A3) THE VERSION NUMBERS, final: D2 ships **FORMAT 6→7** (a FORMAT-7 file omits `source_type`; an older importer refuses a 7-file; a ≤6 file's `source_type` key is dropped on import post-D2) and **SCHEMA v7→v8** (the no-DDL refusal bump; a v8 store refuses on pre-D2 builds — back up first). (A4) D1 (released in 0.9.0) is textually unaffected; the released CHANGELOG's stale "format 6 / schema v7" D1-entry numerals receive a correcting note in the Unreleased section in this same commit. <br><br> **Rider B → `specs/0018-release-migration-orchestrator.md` (same commit; the full final form of every numeral-bearing frozen carrier):** <br> > **Amended by 0019.** (B1) §4a, final: the preflight intercepts everything except resolved base **7**; bases **1–6** → `unsupported-base` with the ladder diagnostic (bases 1–5: "migrate to v6 on a ≤0.8.x release, then to v7 on a 0.9.x/0019-era release, then run this release's migration"; base 6: "migrate to v7 on a 0019-era release, then run this release's migration"); already-current **v8** clean → `current`; already-current **v8** with rebuildable drift → `current` with the repair facts; resolved base **7** ALONE proceeds to minting and delegates to `migrate_store`. (B2) §4e, THE LITERAL TABLE, final and whole: `unsupported-base` (False, False, `source`, the resolved base **1–6**) · `current` clean (False, False, `destination`, **8**) · `current` with repair (True, True, `destination`, **8**) · `migration-source-missing`/nothing-at-path (False, False, `missing`, None) · `migration-source-missing`/empty-user_version-0 (False, False, `unaccepted`, None) · `store-unopenable` (False, False, `unknown`, None) · `invalid-store` (False, False, `unknown`, None) · `locked` (False, False, `unknown`, None) · `unsupported-sqlite` (False, False, `unknown`, None) · `foreign-shape` (False, False, `unaccepted`, None) · `newer` (False, False, `unaccepted`, None) · `invalid-version` (False, False, `unaccepted`, None) · `stamped-shape-mismatch` (False, False, `unaccepted`, None) · `invalid-request` (False, False, `unknown`, None) · `mint-contention` (False, False, `unknown`, None); the delegated rows keep the DEFERENCE law verbatim (base-7 facts from accepted 0013's `TerminalFacts.problems()`, unmodified). (B3) I13, final: parametrized over bases **1–6**; `test_below_v6_base_refuses_with_the_ladder_message` becomes below-v7 over all six bases; `test_below_v6_open_unchanged` reads below-v7. (B4) Every other 0018 frozen surface (attestation, mint/retry, result carrier fields, readback, CLI exits, fingerprint) carries no version numerals and is restated as UNCHANGED — asserted by the executable numeral sweep below, not by declaration. <br><br> **The executable carrier sweep (R2-6):** the acceptance-flip commit runs `grep -nE "\b(FORMAT 5→6|FORMAT.?6|v6→v7|version.?<.?3|\{1, ?2, ?3\}|bases 1–5|base.?6|v7)\b" specs/0016-sourcetype-deletion.md specs/0018-release-migration-orchestrator.md` and disposes EVERY hit: each numeral-bearing line either carries the rider's replacement or is pre-0019-historical (review-ledger/D1-released text, marked so). The sweep's output ships in the flip commit's message; the round-3 seal asserts the riders' tables enumerate EXACTLY the source tables' outcome labels (a mechanical row-count + label comparison) |
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
5. **The false-positive share is UNKNOWN until U3b** (the superseded form's ~half is historical only — round-4 obligation 2); whatever it measures, the design
   spends that on a marker plus the two behavioural reductions below, never
   on refusal or demotion.
5a. **The two behavioural reductions (complete list):** proactive
   volunteering is suppressed (§4c), and flagged facts are excluded from
   the wiki-compiler input (F4 — a code-owned marker cannot survive an LLM
   re-rendering it does not control; the fact stays query-recallable with
   its marker). Nothing else keys on the flag.
6. **On the restore path, a forged or absent `False` obtains BOTH
   flag-keyed eligibilities** a truthful `True` would not have — proactive
   volunteering AND wiki-compiler membership (round-4 obligation 3: the two
   consumers travel together everywhere). The default path is immune by
   composition with 0005's cap for the proactive half and by the same cap's
   grounding consequences for the wiki half; the restore exposure sits
   inside the operator's whole-file trust assertion (0005 §8 limit 1's
   posture) and is accepted rather than patched with a tri-state.

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
| ext-2 | R2-1 the date exemption still unbound (unrelated expression + window passed a fabricated date) | A+C (found-in-fix of R1-F5) | **folded (v4): the RESOLUTION-SET rule** — exemption iff the date EQUALS a deterministic resolution of a specific source expression; per-class resolutions pinned; both reviewer cases pinned FLAGGED vectors | v4 §4b; U3 |
| ext-2 | R2-2 the evidence didn't implement the candidate (unportable, old predicate, no vectors, superseded measurement cited as justification) | G+E | **folded (v4):** the normative portable pure reference + 16 verified vectors in-repo; phase-1f relabeled SUPERSEDED; the measured figures re-scoped to the class choice; candidate numbers from U3b only | v4 §4b; specs/evidence/0019/ |
| ext-2 | R2-3 absorption is N-ary; the pairwise OR under-defined (reviewer-executed) | C | **folded (v4):** OR over `{incoming} ∪ absorbed`, order-independent, pre-insert; zero/one/many + permutation tests | v4 §4d; U2c |
| ext-2 | R2-4 the replace-path exception had no enforceable discriminator | A+B (found-in-fix of R1-F3) | **folded (v4):** every same-ID transition refused, both directions; the OR happens pre-insert on the NEW survivor — no exception to discriminate | v4 §3b, §4d; U4 |
| ext-2 | R2-5 the round-1 folds not swept through all carriers (four standing contradictions; §7a incomplete) | D | **folded (v4):** all four contradictions resolved with superseded claims WITHDRAWN; §7a completed (seven added carriers) | v4 §2c, §3, §4c, §7a |
| ext-2 | R2-6 the riders were deltas, not amendments (the third iteration of the class) | D+F | **folded (v4):** complete final-form riders (the whole receipt-version table; the whole fifteen-row table; I13); the executable numeral sweep pinned; the seal compares rider tables to source tables mechanically | v4 §7b |
| ext-3 | R3-1 the reference nondeterministic (hash-seed-dependent token-to-date attribution) | A+C | **folded (v5):** atomic ISO-span judgment by character position; multi-date + four-seed vectors; seed-independent by construction | v5 §4b; reference; vectors |
| ext-3 | R3-2 the i±2 proximity search recreated the unrelated-number defect; three prose/reference contradictions; the grammar un-enumerated | A+D (found-in-fix of R2-1) | **folded (v5):** anchored span-bound month-day patterns; THE CANONICAL RESOLUTION TABLE (one table, the reference implements exactly it); bare month = no resolutions; the wrong Friday arithmetic corrected | v5 §4b |
| ext-3 | R3-3 the measurement closure false (no U3b artifact; superseded figures driving current-behavior claims) | D+E | **folded (v5):** all number-resting rationales rewritten structural; §7a states the U3b record does not exist yet | v5 §2, §2c, §4c, §7, §7a, §8 |
| ext-3 | R3-4 the check surface encoded the rejected v3 contract | C+D | **folded (v5):** U2c N-ary+permutations; U4 total guard; U2b contributor-set transform; §5 resolution-set rows | v5 §5, §6 |
| ext-3 | R3-5 the v4 edit DELETED the 0014 rider (a `||` row merge); the mechanical comparison had no shipped executable | D+F | **folded (v5):** the rider RESTORED N-ary; three structurally separate rows; `rider_verification.py` + output artifact SHIPPED and run at every seal | v5 §7b; specs/evidence/0019/ |
| ext-4 | APPROVED ON A FINITE BOUNDARY — three mandatory pre-flip obligations + two cleanups; cross-spec sign-off GRANTED for all riders | — | **the atomic flip (this commit):** obligations folded (longest-match precedence + matrix; unknown-until-U3b; both reductions through every carrier + honest rollback); `Spec-Status: accepted`; the 0014 rider + Rider A + Rider B landed in their target specs; the CHANGELOG correcting note; the numeral sweep run and disposed in the commit message | this commit |
