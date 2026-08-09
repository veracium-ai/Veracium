# Feature spec: who may renew a fact's currency

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft (v11, 2026-08-09) — round-8 external review returned five gaps; v11 closes them:
> per-surface ENVELOPE-DERIVED floors validated at every budget source (a global 64 cannot
> contain the wiki's ~254-token scaffold) + bounded data-dependent framing deferring to
> `0003`'s contested truncation (R8-1, I10e); the category precedence now MIRRORS the surface
> order — query-relevant and unrelated warnings split around the claim flag, and
> classification never moves an item across the gate partition (R8-2, I10f); compile-drop
> markers get an exact serialization rule — computed at input selection, appended BY CODE
> post-LLM, persisted as cached-wiki FRAMING that the query-time share clamp can never sever
> (R8-3); the v10 `compile_wiki` signature change is WITHDRAWN — the wiki pipeline stays
> string-valued end-to-end, hot/cold identical, the in-body markers being the machine-
> parseable signal (R8-4); and the network guard installs at conftest IMPORT (before test-
> module imports), with the proof claim scoped to that window (R8-5) — the reviewer
> independently reproduced the suite this round (1055/16/4xfail, zero failures). Earlier
> (v10):** round-7 external review confirmed R6-1/R6-4 coherent and
> returned on five mechanical gaps in the I10 machinery (R7-1…R7-5); v10 closed all five:
> budget FLOORS with loud below-floor rejection and the cap-covers-framing-plus-content
> resolution (I10e, carriers dispositioned §7b-ii incl. the `token_budget=1` test inversion);
> the query-matched unverified claim-flag priority RESTORED to today's safety-load-bearing
> behaviour (I10h — v9 had silently demoted it); CATEGORY-ASSIGNMENT PRECEDENCE making the
> total order total, variancy never demoting (I10f); ENVELOPE reservation so the bound governs
> the complete serialized prompt incl. fixed scaffolding (I10g); and the phantom "compile
> record" replaced by in-body deterministic markers + a transient structured return, no DDL
> (R7-5). The suite's no-network property is now EXECUTABLE: `VERACIUM_FORBID_NETWORK=1` arms
> a socket kill-switch and the full suite passes with it (1069/2/4xfail in-repo).** Earlier:
> round-6 closed R5-1…R5-4 for rendered text; v9 closed the four cross-carrier gaps. The ruled Design 1
> stands: **reinforcement transfers NOTHING**; the incoming edge is persisted with its own
> provenance. v9's amendments: **R6-1** I10's scope is now EXPLICIT — it bounds the RENDERED
> model-facing text surfaces; the structured carriers (`Recall.edges`/`contested`, host
> queries, `introspect()`) deliberately carry complete records under accepted `0003`'s
> contracts and are outside I10, stated as a §8 limit (a host forwarding them verbatim owns
> their bounding); **R6-2** item rendering is bounded CONTENT inside NON-TRUNCATABLE safety
> framing — labels like `[third-party-reported; unconfirmed]` render as suffixes, so a naive
> prefix clamp would keep attacker text and delete its label; framing is charged first and
> never severed (I10c, tested per disclosure class); **R6-3** the per-surface orders now cover
> the COMPLETE item taxonomy — the cached wiki body (share-clamped), episodes, recent history,
> and the gate's unverified/quarantined partition (placement unmodified) — with I10a/I10b
> extended to oversized/overflowing episodes and wiki bodies; **R6-4** v7–v8's proactive
> "contested-preservation first" tier is WITHDRAWN — it conflicted with accepted `0003`'s
> no-new-reach rule; a contested grounded member enters proactive only via the ordinary
> categories, and fenced members never (I10d). — v8 made I10 mechanical; v7 added budgets; v6
> folded R3; v5 folded R2; v4 folded round 1 (F4 fixed at root under `0003`). 🔗 Design 1
> closes `0014` §3.1 + `M9` (§11). Still `draft` — v11 is the round-9 resubmission.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v11** — *round-8 folded: envelope-derived per-surface floors (I10e), precedence↔order alignment + partition preservation (I10f), the marker serialization rule, the signature change WITHDRAWN, import-time network guard.* v10 — *round-7 amendments folded: budget floors + cap semantics (I10e), claim-flag priority restored (I10h), category precedence (I10f), envelope reservation (I10g), in-body wiki markers replacing the phantom compile record; §7b-ii behaviour-change carriers. v9:* *round-6 amendments folded: I10 scoped to rendered model-facing text with the structured-carrier limit stated (R6-1); non-truncatable safety framing charged first (R6-2, I10c); the complete per-surface item taxonomy incl. wiki body, episodes, recent history, and the gate partition (R6-3; I10a/I10b extended); the proactive contested tier WITHDRAWN as conflicting with accepted `0003` no-new-reach (R6-4, I10d). v8 made I10 mechanical; v7 added budgets; v6 folded R3; v5 folded R2; v4 folded round 1; v3 matured the ruled design; v2 folded the rulings; Design 1 (transfers nothing) frozen.* |
| **Status** | *see `Spec-Status:` — canonical.* Holds `0008`'s deferred liveness scope. **`0008` does not depend on this.** |
| **Internal reviewers** | research — the O-Q1/O-Q2/O-Q3 ruling round (2026-08-08, `proposals/0012-rulings.md`; recorded in `specs/reviews.py`) |
| **External review** | required — **round 1: return**, 6 findings + a package blocker → v4. **Round 2: F1–F5 + blocker CLOSED; return on F6** (R2-1…R2-4) → v5. **Round 3: R2-2 + proactive carrier CLOSED; return on 4 collapse defects** (R3-1…R3-4) → v6. **Round 4: R3-2 + named R3 cases CLOSED; return on the boundedness conflict + 3 cells** (R4-1…R4-4) → v7 (budgets). **Round 5: R4-2/3/4 CLOSED, budget architecture affirmed; return on I10 mechanics** (R5-1…R5-4) → v8. **Round 6: R5s substantially CLOSED; return on 4 cross-carrier gaps** (R6-1…R6-4) → v9. **Round 7: R6-1/R6-4 coherent; return on 5 I10-machinery gaps** (R7-1…R7-5) → v10. **Round 8 (2026-08-09): suite independently REPRODUCED at last (kill-switch armed); return on 5 gaps** (R8-1…R8-5, incl. a v10 precedence↔order self-contradiction and the withdrawn signature change) → v11. All dev-verified (ledger: `specs/reviews.py`) |
| **Decision + date** | — |
| **Path** | full |

---

## 1. The defect, measured (v4 — re-measured after round-1 external F1)

**A repeated SAME-DISCLOSURE restatement keeps a fact permanently fresh — and raises its
confidence — so the staleness flag never fires and trust inflates.** `expire()` ages against
`observed_at` and the reinforcement branch advances the prior's `observed_at` AND `confidence`
with `max()` unconditionally *within a disclosure class*.

**Reachability, measured precisely (round-1 external F1 corrected the v1–v3 claim):**
reinforcement considers only priors of the **same `Disclosure`** (the 0.4.1 cross-trust
identity-merge guard), and ingest routes third-party evidence to `use_only`/`quarantined` while
a user fact is `mentionable`. So the v1 scenario as literally written — four `THIRD_PARTY`
restatements refreshing a `USER` fact — **does NOT reach the branch**: re-measured, the user
edge's date and confidence are byte-unchanged and the flag fires normally. The doors that ARE
open, measured:

```
USER edge, MENTIONABLE, 200 days old, confidence 0.7

4 THIRD_PARTY (use_only) restatements  -> prior UNTOUCHED (cross-class guard holds)
1 SYSTEM (mentionable) restatement     -> observed_at 200d -> 1d, confidence 0.7 -> 0.95
```

**The reachable attackers are same-disclosure:** (a) a **`SYSTEM`-authored `mentionable`**
restatement — any host pipeline event that re-derives the fact — silently renews a `USER`
edge's currency and **raises its confidence** (a lower-authority author lifting a
higher-authority edge's trust fields, invisibly, with no record the contributor existed —
finding `M9`); (b) **`third_party` → `third_party`** within `use_only` — adversarial material
keeping *itself* fresh and lifting its own confidence; and (c) the sharpest form: **the MCP
`remember` tool exposes `author` as a free model-suppliable parameter** (§2c, §3b), so a model
claiming `author="user"` mints `mentionable` evidence that reaches a genuine user fact's
reinforcement directly. A party that cannot *clear* the flag does not need to — it can prevent
the flag appearing. **`0008` closes the clearing path; this is the other door.**

---

## 1b. Why it could not stay in `0008`

**`0008` v2 tried, using recorded effective authority from `0003`, and the
second external review rejected it — correctly.**

> **Authority answers *how strongly may this evidence affect trust decisions*.
> It does not answer *did the source of this assertion observe it again*.**

**That is the same error `0008` exists to fix, one level up.** `0008` rejected
same-author-class because unrelated sources share a class; **replacing class
equality with authority comparison does not establish source continuity
either.** Two unrelated `SYSTEM` processes both score 2. Two unrelated third
parties both score 0.

**It also contradicted `0008`'s own matrix**, verifiably:

| case | authority rule | matrix |
|---|---|---|
| `third_party` → `third_party` | **renew** (0 ≥ 0) | deny |
| `third_party` → `user` | **renew** (3 ≥ 0) | deny |

**And it took a dependency on `0003`, which is not accepted** — a "frozen" rule
resting on an unfinished one.

---

## 3. What the fix actually needs

**Reinforcement discards the incoming edge today.** `graph.py`'s reinforcement
branch updates the prior and returns; the restatement is never persisted. So
*"store the incoming observation as its own evidence"* is **a new
representation**, not a smaller version of the current one — which is why this
is a spec rather than an amendment.

**Three coherent designs, and the choice is the spec's subject:**

| # | design | cost |
|---|---|---|
| **1 ✅ RULED (research, 2026-08-08)** | **Reinforcement transfers NOTHING** — not liveness (`observed_at`), not confidence, **not `valid_from`**. The incoming same-value edge is persisted with its OWN provenance; the prior ages honestly. The fact stays live *through the new edge*. | two active edges per restatement — dedup, rendering and functional semantics answered below (O-Q2/O-Q3) |
| **2** | **A dedicated `reobserve()` entry point**, capability-gated like `confirm()`. | a host that never calls it sees facts lapse it thinks are live. **NOT rejected on merits — the recorded successor** if hosts ever need to assert *"this source observed it again"* |
| **3 🛑 REJECTED** | **Defer entirely** until authenticated source identity exists. | it defers to authenticated identity, which `0006` R7 explicitly declined for v1 — so it would leave the measured bypass open **indefinitely** |

> **RULING O-Q1 — DESIGN 1 (research, 2026-08-08; `proposals/0012-rulings.md`).** Dev's lean confirmed,
> **with one load-bearing strengthening.** The v1 §3 said *"no reinforcement transfers LIVENESS"* — but
> that is only half the transfer: `graph.py:107-110` moves **`observed_at` AND `confidence`**. Leaving
> the `confidence` max would close the currency door and leave a **trust door ajar** — a third party
> could not keep a fact fresh but could still **raise a user-authored edge's confidence by restating
> it** (the same defect, one field over). **Frozen: reinforcement transfers NOTHING** — the incoming
> edge is persisted with its own provenance, and neither `observed_at`, `confidence`, nor `valid_from`
> moves onto the prior.

---

## 2. Field contracts touched — REQUIRED, blocking

**No new field, no schema change, no migration.** Design 1 changes *when existing fields are
written*, not what is stored:

| field | today (reinforcement) | under Design 1 |
|---|---|---|
| `Provenance.observed_at` (prior) | advanced to `max(prior, incoming)` | **never written by reinforcement** — the prior ages against its own history |
| `Provenance.confidence` (prior) | raised to `max(prior, incoming)` | **never written by reinforcement** — the trust door closes with the currency door |
| `Edge.valid_from` (prior) | untouched | untouched (stated because the ruling names it: *nothing* moves) |
| the incoming `Edge` (whole record) | **discarded** — never persisted (`insert_incoming=False`) | **persisted with byte-unchanged provenance** — its own author, dates, confidence, disclosure, `source_id` |
| `Edge.needs_confirmation` (prior) | not cleared (`specs/0008`) | not cleared, now trivially — the prior is not written at all (I4 pins it independently) |
| `Edge.note` / `Edge.supersedes` | untouched | untouched — reinforcement is not absorption and not supersession (I6) |

The absorption branch's within-class inheritance (`min(valid_from)` / `max(observed_at)` /
`max(confidence)` when a MORE specific value wins) is **deliberately out of scope** — it is the
reviewed T2/N9b trust-envelope contract, and `0014` §3.3 records its attribution gap.

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | adversarial | handling |
|---|---|---|---|---|
| **the restatement's value/content** | no triple → no edge | ingest's contract | third-party text restating a user fact | governed at ingest (author → disclosure routing); the persisted edge is `use_only`/quarantined and **not assertable** — persisting it grants nothing (the `specs/0006` groups-never-grants discipline) |
| **the incoming `confidence`** | default | bounded by `Provenance` | inflated to 1.0 to lift the prior | stays on the incoming edge **only** — under Design 1 there is no transfer for it to ride (I2/I5) |
| **the incoming event date** | absent = now | ingest REJECTS malformed | future-dated to keep the pair fresh forever | ingest's date contract rejects future dates; a BACK-dated restatement makes the *new* edge old, which only hastens its own expiry — the prior is unaffected either way |
| **`author` / `derived_from`** (round-1 external F2 — the trust-critical input v3 omitted) | ingest requires `author` | fail-closed: the MCP tool rejects unrecognised authors; `"system"` is not exposed | **a model calls `remember(…, author="user")` over MCP** — unauthenticated impersonation minting `mentionable` evidence that reaches a user fact's reinforcement | **NOT closed here, stated as a host-integrity obligation (§3b).** Pre-existing path; Design 1 changes its FOOTPRINT from an invisible `max()` mutation of the genuine edge into a separate, attributable, individually-invalidatable persisted edge. Closing it requires an authenticated entry point (the `confirm()` pattern) — a successor, not this spec |
| **restatement volume** (a flood) | — | — | N restatements/day to grow the store | the growth cost §5 states: bounded per-edge by volatility expiry for lapsing volatilities, and bounded on the READ paths by I10's hard per-surface budgets (the collapse improves what fits but bounds nothing against variants — R4-1/R5-1; neither depends on source identity). Each edge is separately visible and non-assertable if third-party. **Groupability by `0006`'s `(origin, source_id)` applies ONLY when the host supplies `source_id` — the default MCP stream supplies NONE, so its duplicates are unknown-source: not groupable, not revocable-by-source (`0006`'s unknown-is-the-floor rule, honestly inherited here; round-1 external F5).** Connector hosts SHOULD supply `source_id`. No per-call amplification: one ingest call → one edge |

## 3b. Authorization and scope — *full specs only*

- **No new entry point and no capability change.** Restatement arrives through the existing
  `remember()`/ingest path under the existing author contract; Design 1 changes what the plan
  *does* with it, not who may do it.
- **No tenant/scope crossing.** The persisted edge inherits the ingest call's `user_id` exactly as
  any edge does.
- **⚠️ The `author` field IS model-suppliable over MCP — stated, not denied (round-1 external
  F2; v3 claimed the opposite and the claim was false).** `mcp_server.py`'s `remember` is a
  model-called tool with `author` as a free parameter: unrecognised values fail closed and
  `"system"` is deliberately absent, but a model can claim `author="user"` and mint
  `mentionable` evidence — an **unauthenticated impersonation path that PREDATES this spec**
  (it is `0012` §0's own observation: *an act through a dedicated entry point is evidence; a
  field asserting who acted is not* — and `remember` is exactly not such an entry point for
  `author`). This is a **host-integrity obligation**: a deployment that lets an untrusted model
  call `remember` unmediated has no authenticated author boundary, with or without `0012`.
  **What Design 1 changes about it:** today an impersonated same-value restatement's effect is
  an **invisible mutation of the genuine user edge** (the `max()` transfer — no record the
  contributor existed); under Design 1 it is a **separate persisted edge with its own
  `evidence_ref`** — visible, inspectable, individually invalidatable, and attributable after
  the fact. Design 1 does not close impersonation (out of scope — closing it is an
  authenticated-entry-point design, the `0008`/`confirm()` pattern); it converts the
  impersonation's footprint from an unattributed transfer into an auditable record. §2c carries
  the adversarial row.
- **Who may see the new state?** No one new — the persisted edge is subject to the same gate and
  disclosure rules as every edge; a third-party restatement is `use_only`/quarantined as before.

---

## 4. Behaviour — the mechanical contract (v3)

The whole change is inside `graph.py`'s plan builder (`_build_supersession_plan`), which computes
one atomic `SupersessionPlan` per incoming edge (`specs/0003` §4f — CAS-applied, PLAN_STALE retry).

**4a. The branch keeps its guard predicate and position; only its ACTION changes.**

- **Predicate (unchanged):** an active **same-class** prior whose `_value_key` **equals or
  subsumes** the incoming key (the incoming is the same or a *less specific* form — the same
  evidentiary event, not a new fact).
- **Position (unchanged, load-bearing):** BEFORE absorption and BEFORE the functional branch.
  Deleting the branch instead of changing its action would mis-route the subsumed case: `_subsumes`
  is strict (equal keys never absorb), so a shorter restatement (`"Miso"` after `"cat Miso"`)
  would fall through to the FUNCTIONAL branch as a *differing* value and contend with — or
  supersede — its own fact. **I6 pins that a same-or-subsumed value never contends, never absorbs,
  never supersedes.**
- **Action (changed):** return a plan that **persists the incoming edge with byte-unchanged
  provenance and touches nothing else** — `insert_incoming=True`, no `prior_upserts`, no
  invalidations, no refusals, no `supersedes` pointer. The prior is not read-modified-written;
  the `max()` transfers are deleted, not relocated.

**4b. What stays exactly as it is.** Absorption (incoming strictly more specific — §2's out-of-
scope note); functional supersession/refusal (fires only on a CHANGED value, so two same-value
edges never reach it — O-Q2); the CAS plan machinery (`0003`'s n-way contention already handles a
later changed value contending against *several* active same-value edges); `expire()` (per-edge by
I3 — the fix is that reinforcement stops feeding it a refreshed `observed_at`); `confirm()`
(`specs/0008` — still the only flag-clearing path).

**4c. Rendering and the read paths (O-Q2, ruled; collapse added v4, redesigned v5, HARDENED in
v6 — round-3 external R3-1…R3-4 found four found-in-fix defects in v5's contract).** Any
collapsing of same-value edges happens at **render/selection time, never at write time** (the
O-Q2 ruling's rule — I8 is an instance of exactly what it permits). **The governing principle,
stated after three rounds taught it: the collapse SUPPRESSES ONLY STRICT REDUNDANCY. It never
synthesizes a representation, never guesses between incomparable values, and never hides a
member that carries information any consumer reads.** The v6 contract:

- **Scope: ACTIVE edges only (R2-2, closed round 3).** Invalidated/superseded edges are the
  historical record — never collapsed, with an active edge or with each other. The `Acme →
  Beta → Acme` superseded interval renders beside the current value (recall deliberately reads
  `active_only=False`; the collapse must not undo that).
- **Group key: `(subject, relation, disclosure, author_of_evidence, derived_from)` ×
  value-grouping (R2-1 + R3-2).** The key carries the COMPLETE effective-authority envelope —
  `0003`'s rule is `min(author, derived_from)`, so author alone is not the trust identity: a
  direct `USER` edge (effective 3) and a `USER`-derived-from-`SYSTEM` edge (effective 2) are
  different trust facts and NEVER collapse together (v5's key omitted `derived_from` and
  surfaced the lower-authority member — R3-2's reproducer). Bounded: ≤ |authors × derivations|
  representatives per value, in practice a handful.
- **Value grouping: UNIQUE-ANCHOR, never transitive closure (R3-1), with ALL THREE anchor
  cells specified (R4-2).** Equality-or-subsumption is not an equivalence relation, so its
  transitive closure bridges incomparable values: with active `cat Miso`, `dog Miso`, and
  `Miso`, the bare `Miso` connects both and closure merges ALL THREE — one genuine pet
  disappears. Construction: the group ANCHORS are the maximal values (subsumed by no other
  active member of the key). For every non-maximal value, the anchored-by count has exactly
  three cells, and each is specified:
  **anchored-by 1** → joins that anchor's group (the only collapsing cell);
  **anchored-by ≥2 incomparable anchors** → AMBIGUOUS, surfaces on its own — the collapse never
  guesses which fact a short form belongs to;
  **anchored-by 0** (R4-2 — reachable via a sequential token-dropping chain 20→18→…→2, where
  each member subsumes only its immediate successor and the sole maximal anchor directly
  subsumes only the first drop) → **surfaces on its own**, same as ambiguous — "never hides"
  outranks grouping, and the resulting extra surface items are bounded by the budget rule
  below, not by the collapse. (v6 specified only the {1, ≥2} cells — the enumeration gap the
  found-in-fix checklist names.)
- **Survivor selection is DETERMINISTIC and precedes suppression (R4-4).** v6 evaluated
  suppression "against the anchor's note/volatility/outcomes" without ever choosing WHICH
  stored edge the anchor is when several share the maximal key — and because the note predicate
  is asymmetric (empty may hide behind nonempty, never the reverse), store order could change
  the surfaced set. v7: within a group, the SURVIVOR edge is chosen first by a total order —
  **note-bearing over empty-note, then most specific value, then freshest `observed_at`, then
  lexicographic edge id** — and the suppression predicate is evaluated relative to that one
  stored edge. The surfaced set is **invariant under store order/permutation** (the same
  determinism contract `0003` demanded of contested rendering). Flagged members are handled by
  the flag rule below, outside this order.
- **Suppression predicate: STRICT REDUNDANCY ONLY (R3-3).** A member may be suppressed behind
  the survivor only when it adds NO carrier-visible information beyond it: `note` empty or
  byte-equal to the survivor's; same `volatility`; no outcome metadata (`outcome_counts`,
  `last_outcome`, `times_used` at their defaults or equal); not flagged (see below). A member
  differing in ANY of these SURFACES — a dated-commitment `note` is never lost behind a fresher
  empty-note duplicate, and a `durable` fact is never represented by its `transient`
  restatement. There is NO synthesized representative: every surfaced item is a real stored
  edge, verbatim. The one presentation-level aggregate permitted: render-time labels computed
  truthfully from the group (the earliest `valid_from` for "since …"; the flagged-member count
  for "×N") — mutating nothing.
- **Per-surface ordering (R3-3):** query recall SCORES every member first and collapses
  after (among scored members of one group, the query-matching member survives) — collapsing
  before scoring could erase the only query-matching `note`; collapsing after protects the edge
  budget at selection, which is where the budget is spent. Proactive assembly categorizes
  per-member (commitments, confirmations, context) and collapses within category.
- **Flagged members: one confirmable owner at a time, surface size pinned (R2-1 + R3-4 +
  R4-3).** A flag is never synthesized onto an unflagged edge (v5's defect — no confirmable
  owner; `0008` C2). The group's warning carrier is a real flagged edge. **With N > 1 flagged
  members in one group, exactly ONE surfaces per recall — the freshest flagged — regardless of
  N** (25 flagged duplicates produce ONE confirmation prompt, not 25); the prompt MAY carry the
  truthful render-time count ("×N restatements need confirmation"). `confirm(surfaced.id)`
  clears exactly that edge (`0008`'s per-edge contract untouched); if other flagged members
  remain, the next-freshest surfaces on the NEXT recall — **sequential clearing is the
  specified contract**, stated rather than implied: N flagged edges take N confirmations, the
  surface never shows more than one at a time, and after the last confirmation the group
  surfaces its unflagged survivor normally. (A single-confirm-clears-group semantic would
  modify accepted `0008`'s clearing rule and is deliberately NOT proposed.)
- **Coverage: EVERY model-facing read path (R2-3)** — query recall's subgraph selection, the
  wiki compiler's input, AND `proactive.py`'s session-start assembly.
- **🔴 HARD per-surface budgets — boundedness comes from BUDGETS, not from the collapse
  (R4-1), and the budget contract is MECHANICAL (R5-1…R5-3).** The strict-redundancy predicate
  and the surface-everything cells above mean the collapse alone cannot bound the surfaces
  (`note`/`volatility` are extractor-influenced; a variant flood evades suppression —
  reviewer-reproduced). The complete budget contract:

  **(i) Scope, units and defaults (R5-1 + R6-1).** **I10 governs the RENDERED, MODEL-FACING
  TEXT surfaces** — the recall `context` string, the wiki compiler's prompt, and proactive
  assembly's text. The STRUCTURED API carriers (`Recall.edges`, `Recall.contested`, host
  queries, `introspect()`) are host-facing programmatic surfaces governed by accepted `0003`'s
  identity/partition/reach contracts, and are **explicitly OUTSIDE I10's token bounds** — they
  carry complete stored records by design (that is their purpose), and a host that forwards a
  structured carrier to a model verbatim owns its bounding (§8 states this limit; `0003`'s
  carriers are not modified here). Budgets are in **estimated tokens** (the existing `chars/4`
  estimator), NOT item counts — an edge count is not a size bound when
  `Edge.object`/`Edge.note` are unbounded (one 500K-char note sailed through the 40-edge
  budget as ~125K tokens, reviewer-reproduced). Exact bounds, host-tunable via
  `MemoryConfig` with these spec'd defaults: query-recall context ≤ **4,000** est. tokens;
  wiki-compiler input ≤ **8,000** est. tokens total AND ≤ **4 variants** per collapse group;
  proactive assembly ≤ **1,200** est. tokens **by default when the caller sets no
  `token_budget`** (a caller-supplied value overrides).
  **Budget FLOORS — per-surface, envelope-derived, validated at EVERY source (R7-1 + R8-1).**
  A budget too small to carry one framed, clamped item plus the reserved marker cannot satisfy
  I10 and I10c simultaneously (`token_budget=1` is accepted today and its test requires an
  item to survive it — that contract cannot coexist with non-truncatable framing). And a
  single global constant is not a floor (R8-1): the wiki compiler's EMPTY fixed scaffold is
  already ~254 est. tokens, so a host-configured 64-token wiki-input budget could never
  contain its own envelope. v11: each surface's floor is **DERIVED from its serialized
  envelope** — `floor(surface) = envelope_cost(surface) + min_item_allowance (64) +
  marker_reserve` — and EVERY budget source is validated against it: the caller-supplied
  `token_budget`, AND each host-tunable `MemoryConfig` bound (query context, wiki input,
  proactive default, item cap), checked at configuration time and again at surface build (the
  envelope is measured, not assumed). A below-floor value from ANY source is **REJECTED
  loudly** (`ValueError` naming the surface, the floor, and its derivation) — never served
  best-effort, never silently raised. Behaviour-change carriers dispositioned in §7b-ii.
  **Data-dependent framing is itself BOUNDED (R8-1).** Framing whose size grows with data —
  the n-way contested renderer lists every exposed member and author label in one line —
  could otherwise exceed any cap regardless of floors. Rule: every framing form must have a
  bounded rendering. For the contested block that bound ALREADY EXISTS and governs — accepted
  `0003` defines its deterministic finite-budget truncation, and `0012` charges the contested
  block at its `0003`-truncated size. Every `0012`-added framing (trust labels, elision and
  count markers) is constant-size by construction; a data-dependent framing form without a
  bounded rendering is a spec violation, not a runtime surprise.
  **(ii) The per-ITEM clamp, with NON-TRUNCATABLE safety framing (R5-1 + R6-2).** An item's
  rendering is **bounded CONTENT embedded inside immutable control FRAMING**: the trust and
  state labels — `[possibly stale — …]`, `[third-party-reported; unconfirmed]`, `CONTESTED`
  markers, due/overdue dates and confirmation instructions — are FRAMING, charged to the
  budget FIRST and **never truncatable**; only the content inside them is clamped. This closes
  the label-severing seam: several labels render as SUFFIXES after untrusted content, so a
  naive prefix clamp would keep attacker-controlled text while deleting exactly the label that
  tells the model how to treat it. **The per-item cap (**512** est. tokens, config-tunable)
  covers FRAMING PLUS CONTENT together (R7-1 resolved the v9 ambiguity in I10c's favour):**
  framing is charged first and the content is clamped to what remains (`cap − framing_cost`),
  with the elision marker inside the content ("… [content truncated; full record via
  introspect()]") — never emitted whole, never silently dropped, never label-stripped. A
  configured cap that framing alone would exceed is below the §4c(i) floor and rejected
  there. An item that exceeds the REMAINING budget: a safety item is clamped to fit (framing
  intact); a non-safety item is dropped and counted in the surface's truncation marker. The
  oversized-FIRST-item seam is closed by charging the estimator BEFORE emission, always.
  **(iii) ENVELOPE reservation — the whole serialized surface, not just markers (R5-3 +
  R7-4).** Every fixed, non-item cost of a surface's serialized output is **reserved off the
  top before item selection**: the truncation markers, AND the surface's fixed scaffolding —
  `COMPILE_SYSTEM` and the fixed portion of `COMPILE_PROMPT` for the wiki compiler; section
  headings, partition fences, separators, and count markers for recall and proactive. The
  bound governs the **complete serialized model-facing text** (`len(prompt)/4 ≤ bound`), not
  the dynamic payload alone — v9's wiki rule budgeted only facts + episodes, so a full
  dynamic payload produced a prompt LARGER than its bound (reviewer-identified). Nothing
  reserved can ever be the thing that doesn't fit.
  **(iv) The per-surface TOTAL order over the COMPLETE item taxonomy (R5-3 + R6-3),
  deterministic to the last tie.** v8's orders listed only edge classes while every surface
  also carries other prompt-consuming item types (the cached wiki body, episodes, the
  unverified/quarantined partition, recent history) — a bound over an incomplete taxonomy is
  not a bound. The full taxonomies, composing with accepted `0003` (whose contested block
  holds FIRST claim on recall budget — that rule is `0003`'s and is not modified here):
  *query recall (the `context` string):* `0003` contested block → query-relevant flagged
  warnings → **query-matched UNVERIFIED/QUARANTINED claim-flag lines (R7-2 — this is the
  EXISTING priority, restored: today's `_fit_to_budget` and its test place a query-matched
  claim flag ahead of the wiki and episodes, and that is safety-load-bearing — under a tight
  budget the fenced "unverified claim about X exists" line is precisely the counter-injection
  signal; v9's order would have spent the budget before it, a silent demotion of an existing
  safety behaviour, withdrawn)** → other flagged warnings (most-overdue first: oldest
  `observed_at`) → dated commitments (nearest date first) → the cached WIKI BODY, clamped to
  a configured share of the context budget (default ≤ 1/3) → relevance-ranked grounded
  edges → recent EPISODES (newest first, each clamped per (ii)) → the REMAINING
  unverified/quarantined partition in the gate's placement (`0003`/gate-owned, unmodified;
  items clamped and dropped-with-count like any class) → same-group variants last;
  *proactive:* flagged warnings (most-overdue first) → dated commitments (nearest first) →
  current transient context → recent history (newest first) → variants last. **The v7–v8
  "contested-preservation first" tier is WITHDRAWN (R6-4)** — it conflicted with accepted
  `0003`, which freezes that proactive recall gives contested material NO NEW REACH: fenced
  members are never volunteered, and a grounded contested member participates only exactly as
  the corresponding non-contested fact would. A contested grounded member enters proactive
  ONLY through the ordinary categories above — an otherwise-ineligible contested fact does
  NOT appear, and no `use_only`/quarantined member ever does;
  *wiki input:* one survivor per group first (all groups, deterministic `(subject, relation)`
  order) → per-group variants up to the cap → the compactor's EPISODE inputs (newest first,
  each clamped per (ii)), all within the total bound per (iii)'s envelope rule. **Dropped
  counts are signaled by DETERMINISTIC markers with an exact serialization rule (R7-5,
  completed in v11 per R8-3/R8-4).** The drops occur while constructing the compiler INPUT,
  but the wiki body is LLM OUTPUT — an instruction to the model to include markers would not
  be deterministic. Rule: the markers ("+N facts / +M episodes not compiled") are computed at
  input selection and **appended BY CODE to the compiled body AFTER the LLM call**, then
  persisted with the cached body (no schema change). They are NOT part of the compiler-input
  envelope (they never go to the model at compile time); they are **cached-wiki FRAMING**: on
  recall render they are charged BEFORE wiki content per (ii)/(iii) and are non-truncatable —
  the query-time share clamp clamps wiki CONTENT, never the markers, so a suffix marker can
  never be severed (the same label-severing seam, closed the same way). **The v10 "transient
  structured return" is WITHDRAWN (R8-4 — it was carrier-incomplete: `ensure_wiki()` returns
  `compile_wiki()` directly as `Optional[str]` while a cache hit returns a plain string, so a
  tuple would have reached `Memory._recall` on cold paths only).** The wiki pipeline stays
  STRING-VALUED end-to-end, hot and cold identical; the in-body markers ARE the
  machine-parseable drop signal (fixed grammar), I10b parses them, and `introspect()` can
  recompute full drop detail from the store.
  **CATEGORY-ASSIGNMENT PRECEDENCE (R7-3, aligned with the order in v11 per R8-2) — the
  order is total only if every item has exactly ONE class, and the precedence must MATCH the
  surface order.** v10's precedence collapsed "flagged warning" into one class ABOVE claim
  flags while the query order placed unrelated warnings BELOW them — under a one-item budget
  the two rules disagreed. v11's precedence mirrors the order exactly, with query-relevance
  splitting the warning class: **contested member > QUERY-RELEVANT flagged warning >
  query-matched unverified claim flag > UNRELATED flagged warning > dated commitment >
  transient context / grounded fact > variant.** **Variancy NEVER demotes** (a flagged
  variant renders in its warning tier; a dated variant in the commitment tier), and
  **classification NEVER moves an item across the gate partition (R8-2)**: a quarantined
  item classified as a claim flag still renders in its fenced, non-assertable form — the
  class decides PRIORITY, the gate decides PRESENTATION, always. (Today's proactive code
  classifies due-before-flag; it inverts to flag-first at implementation — a dispositioned
  carrier, §7a.)
  Within every class the tie-break is `observed_at` DESC then lexicographic edge id — the
  bounded selection is **permutation-invariant end-to-end** (I8j's property, extended to the
  budget). **Safety-only overflow is defined, not assumed away (R5-3):** when safety items
  ALONE exceed a bound, the order above still decides — contested first (`0003`), then
  warnings before commitments, most-overdue/nearest-first within class — and the marker
  reports the dropped safety count distinctly ("+N warnings not shown") so a safety overflow
  is never silent. Query relevance never outranks the contested block; it DOES outrank
  *unrelated* warnings only in the query-relevant-flagged tier above (an unrelated warning
  still surfaces before ordinary facts).
  **(v) Signaling carriers (R5-2).** `Recall.truncated` becomes the surface's truncation
  signal for EVERY cause (edge-cap, token-budget, per-item clamp) — not only when the caller
  passed `token_budget`; the selection layer must therefore RETURN dropped-count information
  (a structured selection result, not a bare edge list), and contested-preservation edges
  appended after selection are counted INSIDE the global bound, not on top of it. The
  carriers this touches are enumerated in §7a. What is truncated remains in the store,
  visible to `introspect()`.
- **Cross-class same-value still renders BOTH** — the O-Q2 ruling's own example (*"stated by
  you (Jan); also reported by a third party (Aug)"*): cross-class corroboration is informative;
  same-key repetition is not.

## 5. Regime analysis — where does this behave differently?

- **Growth is the honest cost (the ruling's stated trade), and it compounds on the WRITE path
  (round-1 external F6 — v3's "O(1) per-op" described only the final insert and was wrong).**
  Every restatement persists an edge: N restatements → N active same-value edges. Each ingest of
  that `(user, subject, relation)` then loads the COMPLETE active scope, fingerprints it, and
  the store re-reads and re-fingerprints it inside the CAS — so one ingest is **O(N)** and a
  sequence of N restatements is **cumulatively O(N²)** in scope work. Storage bounds per
  volatility: `transient`/`ephemeral` edges LAPSE individually once stale (each ages against its
  own `observed_at` — I3), so their accumulation is self-limiting; `durable`/`slow` edges flag
  individually and stay; `permanent` edges accumulate without bound. **Accepted for v1 with a
  pinned regime test (I9)**: each edge is visible, attributable (it IS the `M9` attribution),
  and non-assertable when third-party; grouping by `(origin, source_id)` applies **only when the
  host supplies `source_id`** (§2c — the default MCP stream does not). If a real host hits the
  quadratic wall, the recorded successors are an attributed same-class merge (a
  `0014`-recorded consumption) or Design 2 (`reobserve()`).
- **Read-path amplification is bounded by BUDGETS (I10), improved by the collapse (I8) —
  claimed in that order (F6 → R4-1 corrected v6's over-claim).** The collapse alone cannot
  bound the surfaces: its suppression predicate deliberately surfaces distinct-note /
  distinct-volatility / outcome-bearing / ambiguous / zero-anchor members, and those fields are
  extractor-influenced — so an adversarial variant flood defeats collapse by construction. The
  HARD bound on every model-facing surface is its budget (§4c: recall's edge budget, the wiki
  input caps, proactive's default budget), which holds at any N with safety-first priority and
  a signaled truncation. The collapse determines what FITS WELL within the budget (strictly
  redundant members never waste it); it is an optimization of surface quality, not the
  boundedness mechanism. Residual costs: the O(N) SQL row scan feeding selection, and storage.
  "Cold vs warm identical" is claimed only for the BUDGETED surfaces — raw row counts differ,
  and §6's I9/I10 measure the surfaces, not the store.
- **Concurrency.** The plan rides `0003`'s CAS (`expected_state` → PLAN_STALE → recompute). Two
  concurrent restatements each insert their own edge — no shared row to race on (today they race
  on the prior's `observed_at`/`confidence`; Design 1 removes that write). The CAS scope
  revalidation is where the O(N) write-path cost above lands.
- **The regime a single-op test misses (I5, re-measured for F1):** the §1 sequence — a
  SAME-disclosure contributor (`SYSTEM`/`mentionable`, or an MCP `author="user"` impersonation)
  restating a 200-day user fact, then `expire()`. Today one restatement yields
  `needs_confirmation=False` and a RAISED confidence; under Design 1 the sequence MUST yield
  `True` and an untouched prior. One restatement also cannot exercise I8/I9's collapse — the
  N-deep sequence can.

## 6. Invariants and executable checks — REQUIRED, blocking

*Prospective (unbuilt) — per PROCESS §4a they become mandatory implementation gates on
acceptance, exactly as `0003`'s pre-acceptance invariant surface did. The two `0012`-attributed `xfail` regressions live today in
`tests/test_0014_maintenance_attribution.py` and flip to passing (and move here) at
implementation.*

| | invariant | executable check |
|---|---|---|
| **I1** | a reinforcement PERSISTS the incoming edge with its own provenance, byte-unchanged from what ingest constructed — author, `observed_at`, `confidence`, `disclosure`, `source_id` all its own. *Precondition SATISFIED at root (round-1 external F4): the `0003` receipt digest now binds the COMPLETE logical outcome, so a same-`operation_id` resubmission with different provenance raises an integrity conflict instead of silently replaying — fixed under `specs/0003` with the exhaustive changed-field-vs-exact-replay test `test_a_differing_resubmission_conflicts_field_by_field`, which passes today* | `test_reinforcement_persists_the_incoming_edge_unmodified` |
| **I2** | the PRIOR is byte-identical after a reinforcement — no `observed_at`, `confidence`, `valid_from`, `note`, or flag movement | `test_reinforcement_leaves_the_prior_byte_identical` — serialize the prior before/after; assert equality |
| **I3** | **(frozen, O-Q3)** `expire()`/staleness ages each edge against **its own** `observed_at`, never the newest edge in a `(subject, relation)` group | `test_a_stale_user_edge_flags_despite_a_fresher_same_value_edge` — a 200-day user edge + a fresh third-party same-value edge; `expire()` still sets `needs_confirmation=True` on the user edge |
| **I4** | reinforcement never clears `needs_confirmation` (`specs/0008` preserved — pinned independently of I2 so a future rewrite of the branch cannot lose it silently) | the existing `0008` same-class-restatement test stays green under Design 1 |
| **I5** | **the §1 bypass is closed, measured at the REACHABLE doors (re-scoped for round-1 external F1)** — a SAME-disclosure restatement (`SYSTEM`/`mentionable`, a `third_party`→`third_party` `use_only` pair, and the MCP `author="user"` impersonation route) no longer keeps a fact fresh OR raises its confidence; the cross-class case is pinned as ALREADY-closed so the 0.4.1 guard cannot silently regress | `test_restatements_no_longer_defeat_staleness` — the §1 sequence per door: prior byte-unchanged, `expire()` flags; plus `test_cross_class_restatement_still_touches_nothing` (the guard held BEFORE Design 1 and must hold after) |
| **I6** | a same-or-subsumed value NEVER contends, absorbs, or supersedes — no refusal record, no `absorbed_duplicate`, no `supersedes` pointer, no invalidation from a reinforcement | `test_a_same_value_restatement_produces_no_contention_artifacts` — incl. the SUBSUMED form (`"Miso"` after `"cat Miso"`), the mis-routing seam §4a names |
| **I7** | the persisted restatement IS the attribution — after reinforcement, the contributing source's edge is queryable with its own provenance (closes `M9`; `0014` §3.1) | `test_reinforcement_attributes_the_contributing_source` (today an `xfail` in `tests/test_0014_maintenance_attribution.py`; flips at implementation) |
| **I8** | **(F6; v5 per R2-1…R2-4; HARDENED v6 per R3-1…R3-4)** every model-facing read path — query recall selection, the wiki compiler input, AND proactive assembly — suppresses ONLY strictly-redundant ACTIVE duplicates, per the §4c contract: full effective-authority key (incl. `derived_from`), unique-anchor value grouping, strict-redundancy predicate, flagged-member surfacing, per-surface ordering; no synthesized representative ever; the store keeps every edge | `test_read_paths_collapse_same_class_duplicates` — N strictly-redundant same-key restatements; the fact renders once per surface, cross-class/cross-author/cross-derivation pairs still render both |
| **I8a** | **(R2-1)** the collapse never hides a trust distinction or a staleness signal: a stale, flagged `USER`/`mentionable` edge is NOT hidden by a fresh `SYSTEM`/`mentionable` duplicate — both surface, the flag visible | `test_collapse_preserves_author_and_confirmation` — stale flagged USER + fresh SYSTEM same value: both rendered, the possibly-stale marker present |
| **I8b** | **(R2-2)** history survives the collapse: an `A → B → A` sequence keeps its superseded first-`A` interval rendering beside the current `A` | `test_history_survives_the_collapse` — supersede `Acme` (2020) with `Beta` (2022), then `Acme` (2024); recall renders BOTH `Acme` edges, the old one marked superseded with its interval |
| **I8c** | **(R2-3)** proactive/session-start recall is inside the collapse contract: duplicates render once and never displace unrelated content under a `token_budget` | `test_proactive_collapses_duplicates_within_budget` — 4 duplicate transient edges → one line; a dated commitment and a stale-confirmation prompt still surface with the budget set |
| **I8d** | **(R2-4)** exact-and-uniquely-subsumed variants cannot mint fresh groups: a token-dropped variant subsumed by exactly one anchor joins that anchor's group, most-specific representative | `test_subsumed_variants_share_one_group` — a 20-token value plus token-dropped variants each subsumed only by it: ONE representative (the full form), not one per variant |
| **I8e** | **(R3-1)** grouping never bridges incomparable values: a value subsumed by TWO OR MORE incomparable anchors is AMBIGUOUS and surfaces on its own — no transitive closure, no guessing | `test_incomparable_anchors_are_never_merged` — active `cat Miso` + `dog Miso` + `Miso` (nonfunctional `has_pet`): BOTH specific pets surface, and `Miso` surfaces separately; nothing disappears |
| **I8f** | **(R3-2)** the collapse key carries the COMPLETE effective-authority envelope: members differing in `derived_from` never collapse, systematically over `author × derived_from` | `test_collapse_respects_the_authority_envelope` — table-driven over the `0003` ladder: for every pair of `(author, derived_from)` combinations with different `effective()`, both members surface; equal-envelope pairs collapse |
| **I8g** | **(R3-3)** no carrier-visible information is lost to suppression: a member with a distinct `note`, different `volatility`, or outcome metadata SURFACES; query scoring runs BEFORE collapse | `test_collapse_never_drops_carrier_fields` — older duplicate with `note="due 2026-08-10"`/durable + fresher empty-note/transient: the dated commitment still renders in proactive AND a query matching the note text still finds it |
| **I8h** | **(R3-4 + R4-3)** a surfaced possibly-stale warning has a CONFIRMABLE OWNER, and the warning surface is PINNED AT ONE regardless of how many members flag: with N > 1 flagged duplicates, exactly one (freshest flagged) surfaces per recall; `confirm(surfaced.id)` clears that edge; the next-freshest surfaces on the next recall; after the Nth confirmation no warning remains | `test_confirming_the_surfaced_warning_clears_it` (1+1 case) · `test_n_flagged_duplicates_surface_one_owner_at_a_time` — 25 flagged duplicates: ONE prompt (optionally "×25"), never 25; confirm it → next owner surfaces; iterate to zero warnings; surface size 1 throughout |
| **I8i** | **(R4-2)** all three anchored-by cells behave as specified — {0 → surfaces alone, 1 → collapses, ≥2 → surfaces alone}; a zero-anchor chain member is never silently suppressed and never merged upward past `_subsumes`' bound | `test_a_token_dropping_chain_surfaces_its_unanchored_members` — the 20→18→…→2 sequential chain: the maximal anchor collapses only its directly-subsumed member; every zero-anchor interior member surfaces (within I10's budget), none vanishes |
| **I8j** | **(R4-4)** the surfaced set is DETERMINISTIC and store-order invariant: the survivor is chosen by the §4c total order (note-bearing → specificity → freshest → edge id) BEFORE suppression is evaluated | `test_surfaced_set_is_permutation_invariant` — insert one group's members in several store orders (incl. the asymmetric empty-note/nonempty-note pair both ways): identical surfaced set every time |
| **I10** | **(R4-1, made mechanical in v8 per R5-1…R5-3)** every model-facing read surface carries a HARD budget in ESTIMATED TOKENS (never item counts) with the §4c(i) defaults, a per-ITEM clamp with in-item elision, marker cost reserved off the top, the §4c(iv) per-surface total order (composing with `0003`'s contested first-claim, unmodified), defined safety-only overflow, and truncation SIGNALED for every cause | `test_read_surfaces_are_hard_bounded_against_variant_floods` — 25 distinct-note variants: every surface within its token bound, warning + commitment retained, marker present and deterministic |
| **I10a** | **(R5-1, extended v9 per R6-3)** ONE oversized item cannot break a budget — for EVERY item type in the §4c(iv) taxonomy: a 500K-char edge note/object, an oversized EPISODE summary, and an oversized cached WIKI BODY are each clamped at their cap with the in-item elision marker; an oversized item never sails through whole, never yields `truncated=False`, and an oversized SAFETY item is clamped-to-fit rather than dropped | `test_a_single_oversized_item_is_clamped_not_emitted` — one 500K-char member of each item type (edge, episode, wiki body) under each surface: rendered size ≤ the bound, elision marker present, `truncated` set; repeated as the FIRST item under a tiny `token_budget` |
| **I10b** | **(R5-3, extended v9 per R6-3)** overflow is ordered, deterministic, and NEVER silent across the FULL taxonomy: when safety items alone — or episodes/wiki body alongside them — exceed a bound, the §4c(iv) order decides (contested first per `0003`; wiki within its share; warnings most-overdue-first; commitments nearest-first; episodes newest-first; ties `observed_at` DESC then edge id), and markers report dropped counts per class, SAFETY distinctly | `test_safety_overflow_is_ordered_and_reported` — more flagged groups + commitments + a contested pair + episodes + a large wiki body than the bound admits: selection matches the total order exactly, is permutation-invariant, and the per-class markers render within budget |
| **I10c** | **(R6-2)** trust/state labels are NON-TRUNCATABLE framing charged before content: clamping can never sever `[possibly stale — …]`, `[third-party-reported; unconfirmed]`, `CONTESTED` markers, or due/confirmation instructions from the content they govern — attacker-controlled text is never retained while its label is dropped | `test_clamping_never_severs_the_safety_label` — an oversized item of EACH class (mentionable, use_only, quarantined, stale-flagged, dated commitment, contested member): the label renders intact in every case, the content is clamped, and the label+clamped-content pair stays within the item cap |
| **I10d** | **(R6-4)** proactive recall gives contested material NO NEW REACH — accepted `0003`'s rule, restated here because v7–v8 violated it with a contested-first tier (WITHDRAWN): a grounded contested member enters proactive only via the ordinary categories (flagged/due/transient/recent); an otherwise-ineligible contested member does NOT appear; a fenced (`use_only`/quarantined) member is NEVER volunteered | `test_proactive_grants_contested_no_new_reach` — a durable, unflagged, undated, non-transient contested grounded pair: absent from proactive output; the same fact when flagged appears via the WARNING tier (not a contested tier); a fenced challenger never appears |
| **I10e** | **(R7-1 + R8-1)** budget floors are PER-SURFACE, ENVELOPE-DERIVED, and enforced loudly at EVERY source: `floor(surface) = measured envelope + 64-token item allowance + marker reserve`; a below-floor caller `token_budget` OR host-configured bound (query/wiki/proactive/item-cap) is REJECTED with a `ValueError` naming the surface, floor, and derivation; the per-item cap covers framing PLUS content; data-dependent framing must have a bounded rendering (the contested block at its `0003`-truncated size) | `test_below_floor_budgets_are_rejected_loudly` — `token_budget=1`, a 32-token item cap, AND a 64-token wiki-input config (below the wiki's ~254-token measured envelope) each raise with the derivation; a just-above-floor budget renders one framed clamped item + marker within bound (the §7b-ii inversion of the old survival test) |
| **I10f** | **(R7-3 + R8-2)** category assignment is a PRECEDENCE that MIRRORS the surface order (contested > query-relevant flagged > query-matched claim flag > UNRELATED flagged > commitment > context/grounded > variant); VARIANCY NEVER DEMOTES; and classification never moves an item across the gate partition — class decides priority, the gate decides presentation | `test_overlapping_classifications_take_the_highest_class` — one edge stale-flagged + dated + a variant renders once in its warning tier; PLUS the R8-2 case: one UNRELATED flagged warning vs one query-matched quarantined claim under a one-item budget → the claim flag wins AND renders fenced |
| **I10g** | **(R7-4)** the bound governs the COMPLETE serialized model-facing text — fixed scaffolding (`COMPILE_SYSTEM`, the fixed prompt portions, headings, fences, separators, markers) is reserved before item selection, so a full dynamic payload can never push the serialized prompt past its bound | `test_the_serialized_prompt_never_exceeds_its_bound` — fill each surface to saturation: `len(final_prompt)/4 ≤ bound` for the wiki compiler call, the recall context, and proactive output, measured on the actual serialized strings |
| **I10h** | **(R7-2)** the query-matched unverified/quarantined claim-flag line KEEPS its existing priority over the wiki and episodes under overflow — the fenced "unverified claim exists" signal is safety-load-bearing and is never displaced by a tight budget | `test_query_matched_claim_flag_survives_overflow` — a query about a quarantined debt claim with overflowing grounded + wiki + episode material at a tight (≥-floor) budget: the fenced claim-flag line is present in the rendered context |
| **I9** | **(F6, extended v5 + v7)** the high-restatement regime is pinned, not assumed — over EXACT, SUBSUMED, **and adversarial-variant** repetitions (distinct notes, mixed volatilities, outcome-bearing members) | `test_the_high_restatement_regime_stays_correct_and_bounded` — 25 restatements MIXING exact, token-dropped, and distinct-note/volatility forms: every ingest applies cleanly (no contention artifacts, no PLAN_STALE exhaustion), the prior is untouched throughout, `expire()` still flags it, and every surface obeys I10's bound with the safety items retained |

## 7. Failure modes and reversibility

- **The seam a naive implementation hits (§4a):** deleting the branch instead of changing its
  action mis-routes subsumed values into functional contention. I6's subsumed-form case exists
  precisely for this.
- **The regression that will be proposed later (O-Q3, twice over):** (a) someone "optimizes"
  expiry to age a `(subject, relation)` group against its newest member — I3 fails, the §1 bypass
  reproduces; (b) someone "restores" the `max()` transfer as a dedup optimisation — I2/I5 fail.
  Both are one-line-looking changes that remove the fix, not the cost; that is why both are
  frozen invariants rather than notes.
- **Partial failure:** none new on the apply path — the reinforcement plan is one atomic insert
  under `0003`'s CAS; it either commits or returns PLAN_STALE and recomputes; no multi-row
  transfer is left to half-apply. **The replay seam round-1 F4 found is closed at root**: the
  receipt digest previously bound only a subset of fields, so a same-`operation_id`
  resubmission with DIFFERENT provenance replayed silently (the store kept the first
  submission's provenance while reporting success) — the digest now binds the complete logical
  outcome (fixed under `specs/0003`; `test_a_differing_resubmission_conflicts_field_by_field`).
- **Reversibility:** better than today. A persisted restatement can be individually inspected,
  expired, or (future) revoked by source; today's `max()` transfer is unattributed and
  irreversible — the prior's history is overwritten with no record of the contributor (`M9`).
- **Growth (the accepted risk):** §5. First visible symptom if it bites: many active same-value
  edges on one fact. Mitigations exist at render (collapse), lifecycle (per-edge lapse), and
  future attributed merge; none is load-bearing for v1 correctness.

## 7b. Cross-spec supersession — the carriers that assert TODAY'S behaviour (round-1 external F3)

**Design 1 contradicts frozen text and passing tests in two ACCEPTED specs.** v3 claimed the
only change was one `graph.py` branch; that was carrier-incomplete. Every carrier below asserts
the current *refresh-and-discard* behaviour and MUST be updated **in the same implementation
commit** (the carrier-completeness rule), with the spec-side amendments landing on `0012`'s
acceptance:

| carrier | what it says today | required change |
|---|---|---|
| **`specs/0003` §4f** — *"reinforcement → `insert_incoming = False`; update the existing prior, insert nothing"* (round-7 blocker 3) | freezes the OLD action | on `0012` acceptance, `0003` §4f gains a marked amendment: the reinforcement row is **superseded by `0012` Design 1** (WITHDRAWN-marker discipline; the plan TYPE and every other row stand). A change to an accepted spec's frozen text — recorded on both sides, this table being `0012`'s side |
| **`SupersessionPlan` docstring** (`schema.py`) — *"reinforcement refreshes an existing prior and inserts NOTHING (`False`)"* | same promise, in the carrier that stands in for the spec at the call site | reworded in the implementation commit (docs change to a guarded file, riding the `Spec: specs/0012` commit) |
| **`test_reinforcement_plan_inserts_no_duplicate`** (`tests/test_0003_supersession_store.py`) | asserts only the prior remains after a reinforcement plan | inverted: asserts the incoming is persisted and the prior untouched (becomes an I1/I2 check) |
| **`test_reinforcement_still_advances_observed_at`** (`tests/test_staleness_clearing_0008.py`) | asserts the prior's `observed_at` ADVANCES — its own docstring already flags *"whether it should at all"* as deferred to this spec | inverted into I2's byte-identical assertion; `0008`'s C3 spec text already carries the forward-note |
| **`graph.py` branch comments** + **`lifecycle.py` docstring** | describe refresh-and-discard | rewritten in the implementation commit (`lifecycle.py` note already forward-references the ruling) |

**§7b-ii. The I10 behaviour-change carriers (round 7).** The budget floors and category
precedence change EXISTING contracts; each carrier is dispositioned here rather than left to
collide at implementation:

| carrier | today | v10 disposition |
|---|---|---|
| `test_recall_token_budget` | requires an item to SURVIVE `token_budget=1` | inverts: `token_budget=1` (below the 64-token floor) asserts the loud `ValueError`; a ≥-floor case keeps the survival assertion |
| `recall()` docstring + the MCP `recall` tool description | document best-effort truncation at any budget | state the minimum render budget and the rejection |
| proactive's classifier | classifies a DUE edge before checking its confirmation flag | inverts to flag-first per the §4c(iv) precedence |
| `_fit_to_budget`'s query-matched claim-flag priority | claim flags outrank wiki + episodes | **PRESERVED** (R7-2 restored the v9 order to match it) — the carrier constrains the spec here, not the reverse |
| `compile_wiki()` / `ensure_wiki()` return | both string-valued (`ensure_wiki` returns `compile_wiki()` directly; a cache hit returns the cached string) | **UNCHANGED — the v10 signature change is WITHDRAWN (R8-4)**: the pipeline stays string-valued end-to-end, hot/cold identical; the in-body markers (fixed grammar, appended by code post-LLM) are the machine-parseable drop signal |

**Enumeration rule:** at implementation, grep `insert_incoming` and `reinforc` across `src/` +
`tests/` + `specs/`; every hit is a carrier to disposition against this table.

## 7a. Surfaces touched — the honest list (v4)

- `src/veracium/graph.py` — `_build_supersession_plan`'s reinforcement branch: action changes
  from *refresh-prior-and-drop-incoming* to *persist-incoming-untouched* (§4a); and the recall
  subgraph selection gains the I8 collapse (active-only; keyed on the full authority envelope
  incl. `derived_from`; unique-anchor value grouping with all three anchored-by cells;
  deterministic survivor order — §4c) and RETURNS a structured selection result carrying
  dropped counts (R5-2 — a bare edge list cannot signal truncation).
- `src/veracium/compile.py` — the wiki compiler's input applies the I8 collapse AND gains the
  I10 per-group + total input caps (it previously had NO input bound — R4-1). Derived view; its
  inputs are guarded upstream.
- `src/veracium/proactive.py` — session-start assembly joins the I8 contract (R2-3) and gains
  a DEFAULT I10 budget even when the caller omits `token_budget` (previously unbounded —
  R4-1); safety-first priority so duplicates never displace commitments or confirmations.
- `src/veracium/lifecycle.py` — docstring only (`expire()` code untouched; I3 pins the per-edge
  contract it already implements).
- `src/veracium/schema.py` — the `SupersessionPlan` docstring carrier (§7b); no field change.
- `src/veracium/store/sqlite.py` — **already landed at root (F4)**: the receipt digest binds the
  complete logical outcome, under `Spec: specs/0003`.
- `src/veracium/__init__.py` — **(R5-2, guarded)** `Memory._recall` counts contested-
  preservation edges INSIDE the global bound (today they are appended after selection, so
  `max_subgraph_edges` is not a global cap); `Recall.truncated` is set for EVERY truncation
  cause, and its docstring corrected (today it documents token_budget-only truncation);
  proactive gains its default budget wiring.
- `src/veracium/config.py` — **(R5-2)** the I10 limits as host-tunable `MemoryConfig` fields
  with the §4c spec'd defaults (context/wiki/proactive token bounds, per-item clamp, per-group
  variant cap).
- `tests/` — the I1–I10 checks; the two `0012`-attributed `xfail`s in
  `tests/test_0014_maintenance_attribution.py` flip and migrate; the §7b inversions.
- **NOT touched:** the store schema (no DDL, no `SCHEMA_VERSION` bump, no migration),
  `ingest.py`, `gate.py`, `portability.py` (`FORMAT_VERSION` unchanged).

## 8. Claims and limits

- **Closes:** the §1 measured currency bypass at its REACHABLE doors — same-disclosure renewal
  and the confidence door the ruling named; finding `M9` and `0014` §3.1 (the persisted edge is
  the attribution — §11). The cross-class door was already closed (0.4.1) and is pinned so it
  stays closed (I5).
- **Does NOT close MCP `author` impersonation (§3b/§2c).** That path predates this spec and
  survives it; Design 1 changes its footprint (an auditable persisted edge instead of an
  invisible transfer), not its existence. Closing it is an authenticated-entry-point successor.
- **Does NOT establish source continuity.** Whether the *same source* observed the fact again is
  Design 2's question (`reobserve()`, the recorded successor). Design 1 makes restatement honest
  — each observation stands on its own provenance — it does not verify anything.
- **Does NOT deduplicate storage, and the write path pays O(N) per ingest under accumulation
  (§5).** The READ paths are bounded by their BUDGETS (I10), with the collapse improving what
  fits (I8) — the collapse alone bounds nothing against adversarial variants (R4-1, stated
  plainly); the store and the CAS scope scan are unbounded — that trade is accepted with I9
  pinning the regime.
- **Does NOT bound the STRUCTURED carriers (R6-1, stated as a limit).** `Recall.edges`,
  `Recall.contested`, host queries and `introspect()` deliberately carry complete stored
  records — that is their contract under accepted `0003` and it is untouched here. I10 bounds
  RENDERED model-facing text only; a host that forwards a structured carrier to a model
  verbatim owns its bounding.
- **Does NOT touch absorption's within-class inheritance** — deliberate scope (§2); its
  attribution gap is `0014` §3.3's.
- **Depends on nothing unaccepted.** The plan machinery it rides (`0003`) is accepted and
  shipped — including the F4 receipt-digest fix, which landed under `0003` and passes today;
  `0008`'s clearing rule is accepted and shipped. (v1 of this spec died partly for resting on
  then-unaccepted `0003` — stated so the reviewer can check the dependency direction is now
  sound.)

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~**O-Q1**~~ | **RULED: Design 1 (§3), strengthened to "transfers NOTHING" incl. `confidence`.** Design 3 rejected (defers to authenticated identity `0006` declined for v1); Design 2 (`reobserve()`) recorded as the deliberate successor. | **resolved** | research | — |
| ~~**O-Q2**~~ | **RULED: no functional violation.** The functional branch fires only on a CHANGED value (`graph.py`), so two SAME-value inputs never reach it. Any collapsing of the two same-value edges happens at **RENDER time, never at write time** (`graph.py:83`, *"dedup must not make trust decisions"*). And **rendering both may BEAT collapsing** — `_origin_label` already labels origin, so *"stated by you (Jan); also reported by a third party (Aug)"* is more informative than one laundered line. Not `0011` E3's contested state (values agree). | **resolved** | research | — |
| ~~**O-Q3**~~ | **🔴 RULED: NO — `expire()` MUST stay PER-EDGE. Grouping to the newest edge would REINTRODUCE the bypass this spec closes.** Verified `lifecycle.py:37-46` ages each edge against its OWN `observed_at`. Under Design 1 + per-edge: the user's 200-day edge flags, the third party's fresh edge is `USE_ONLY`/not assertable → the flag fires, **bypass closed**. Under grouped-to-newest: the third party becomes the newest member and drags the group's currency → the flag never fires, and §1's measured four-restatement bypass reproduces. **Frozen as an INVARIANT (below): the next person to see two same-value edges will have this idea, and it removes the FIX, not the cost.** | **resolved (invariant)** | dev + research | — |

**Invariant (O-Q3, frozen):** `expire()`/staleness ages each edge against **its own** `observed_at`,
never against the newest edge in a `(subject, relation)` group. A test must pin that under Design 1 a
stale user edge still flags even when a fresher same-value non-assertable edge exists.

**No open question blocks this spec.**

---

## 11. Cross-spec effect — Design 1 closes `0014` §3.1

**Design 1 persists the reinforcing edge, so `0014`'s reinforcement site stops being a
consult-and-DISCARD.** `0014` §3.1 ("reinforcement — the source vanishes") is *open only because*
`ingest.py:194` hands `apply_supersession` an unpersisted edge the reinforcement branch never writes.
Under Design 1 the incoming edge **is stored**, and *the edge is the attribution* — with "transfers
nothing" there is no payload to record either. **So `0012` Design 1 CLOSES `0014` §3.1** (and the
finding `M9`), leaving `0014` to cover consolidation + absorption only. `0014`'s consult-and-discard
INVARIANT is unchanged — one of its three sites simply disappears. This argues for **landing `0012`
before `0014`** (research, 2026-08-08).
