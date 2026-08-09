# Feature spec: who may renew a fact's currency

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft (v4, 2026-08-09) — round-1 external review RETURNED v3 for amendment (6 findings + a
> package blocker, all verified by dev against the code); v4 folds all of them.** The ruled
> Design 1 stands ("directionally coherent" — reviewer): **reinforcement transfers NOTHING**; the
> incoming edge is persisted with its own provenance. v4's amendments: **F1** §1 re-measured at
> the REACHABLE doors (reinforcement is same-DISCLOSURE only — the real attackers are
> `SYSTEM`/`mentionable`, `third_party`→`third_party`, and the MCP `author` impersonation route;
> the literal third-party-on-user scenario was already blocked by the 0.4.1 cross-class guard);
> **F2** §3b now STATES the model-suppliable MCP `author` parameter as a host-integrity
> limitation instead of denying it; **F3** §7b enumerates the cross-spec carriers Design 1
> contradicts (`0003` §4f's frozen `insert_incoming=False`, the `SupersessionPlan` docstring, two
> passing tests) with their required same-commit updates; **F4** the `0003` receipt digest now
> binds the complete logical outcome — fixed at ROOT under `specs/0003`, test passing today;
> **F5** absent-`source_id` groupability stated honestly; **F6** §5 costs corrected (O(N) per
> ingest, O(N²) cumulative; wiki/recall amplification) and mitigated by the new REQUIRED
> read-path collapse **I8** + regime pin **I9**. 🔗 Design 1 closes `0014` §3.1 + `M9` (§11).
> Still `draft` — v4 is the round-2 resubmission.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v4** — *round-1 external amendments folded (F1–F6 + the package blocker; I8/I9 added, I5 re-scoped, §7b cross-spec carriers). v3 matured the ruled design to a full mechanical contract; v2 folded the O-Q1/O-Q2/O-Q3 rulings; Design 1 (transfers nothing) frozen.* |
| **Status** | *see `Spec-Status:` — canonical.* Holds `0008`'s deferred liveness scope. **`0008` does not depend on this.** |
| **Internal reviewers** | research — the O-Q1/O-Q2/O-Q3 ruling round (2026-08-08, `proposals/0012-rulings.md`; recorded in `specs/reviews.py`) |
| **External review** | required — **round 1 (2026-08-09): return for amendment**, 6 findings + a package blocker, all dev-verified against the code; v4 folds all (ledger: `specs/reviews.py`) |
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
| **restatement volume** (a flood) | — | — | N restatements/day to grow the store | the growth cost §5 states: bounded per-edge by volatility expiry for lapsing volatilities, and bounded on the READ paths by I8's same-class collapse (value-key based — it does NOT depend on source identity). Each edge is separately visible and non-assertable if third-party. **Groupability by `0006`'s `(origin, source_id)` applies ONLY when the host supplies `source_id` — the default MCP stream supplies NONE, so its duplicates are unknown-source: not groupable, not revocable-by-source (`0006`'s unknown-is-the-floor rule, honestly inherited here; round-1 external F5).** Connector hosts SHOULD supply `source_id`. No per-call amplification: one ingest call → one edge |

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

**4c. Rendering and the read paths (O-Q2, ruled; REQUIRED collapse added in v4 — round-1
external F6).** Any collapsing of same-value edges happens at **render/selection time, never at
write time** (the O-Q2 ruling's rule — I8 is an instance of exactly what it permits). v4 makes
the read-path behaviour a requirement rather than "as today":

- **Same-class duplicates COLLAPSE at read (I8):** query recall's subgraph selection and the
  wiki compiler's input each present **at most one representative per `(subject, relation,
  value_key, disclosure)`** — the freshest (`max observed_at`). The store keeps every edge
  (diagnostic, attributable); this is presentation, decides no trust question (the candidates
  are same-class *by construction*), and is what keeps the recall edge budget and the compiler
  prompt from being consumed by N copies of one fact (§5).
- **Cross-class same-value still renders BOTH** — that is the O-Q2 ruling's own example
  (*"stated by you (Jan); also reported by a third party (Aug)"*): cross-class corroboration is
  informative; same-class repetition is not.

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
- **Read-path amplification exists and is MITIGATED by I8, not denied (F6).** Without I8, the
  wiki compiler renders every active grounded edge into its prompt (token cost linear in N) and
  query recall's bounded edge budget can be spent on N copies of one fact. With I8 (required),
  both read paths see at most one representative per `(subject, relation, value_key,
  disclosure)`; the residual costs are the O(N) SQL row scan feeding the collapse and the
  storage itself. "Cold vs warm identical" is therefore claimed only ABOVE I8's collapse — the
  raw row counts differ and §6's I9 measures the collapsed surfaces, not the store.
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
| **I8** | **(F6)** the READ paths collapse same-class duplicates: query recall's selection and the wiki compiler's input each present at most ONE representative per `(subject, relation, value_key, disclosure)` — the freshest — while the store keeps every edge; cross-class same-value still renders both (§4c) | `test_read_paths_collapse_same_class_duplicates` — N same-class restatements; assert recall context and the compiler input carry the fact once, the edge budget is not consumed by duplicates, and a cross-class same-value pair still surfaces both |
| **I9** | **(F6)** the high-restatement regime is pinned, not assumed: at N=25 same-class restatements the write path stays correct and the read surfaces stay bounded | `test_the_high_restatement_regime_stays_correct_and_bounded` — 25 restatements: every ingest applies cleanly (no contention artifacts, no PLAN_STALE exhaustion), the prior is untouched throughout, `expire()` still flags it, and the I8-collapsed recall/compiler surfaces are the same size as at N=1 |

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

**Enumeration rule:** at implementation, grep `insert_incoming` and `reinforc` across `src/` +
`tests/` + `specs/`; every hit is a carrier to disposition against this table.

## 7a. Surfaces touched — the honest list (v4)

- `src/veracium/graph.py` — `_build_supersession_plan`'s reinforcement branch: action changes
  from *refresh-prior-and-drop-incoming* to *persist-incoming-untouched* (§4a); and the recall
  subgraph selection gains the I8 same-class collapse.
- `src/veracium/compile.py` — the wiki compiler's input applies the same I8 collapse (derived
  view; its inputs are guarded upstream).
- `src/veracium/lifecycle.py` — docstring only (`expire()` code untouched; I3 pins the per-edge
  contract it already implements).
- `src/veracium/schema.py` — the `SupersessionPlan` docstring carrier (§7b); no field change.
- `src/veracium/store/sqlite.py` — **already landed at root (F4)**: the receipt digest binds the
  complete logical outcome, under `Spec: specs/0003`.
- `tests/` — the I1–I9 checks; the two `0012`-attributed `xfail`s in
  `tests/test_0014_maintenance_attribution.py` flip and migrate; the §7b inversions.
- **NOT touched:** the store schema (no DDL, no `SCHEMA_VERSION` bump, no migration),
  `ingest.py`, `gate.py`, `portability.py` (`FORMAT_VERSION` unchanged), `proactive.py`.

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
  (§5).** The READ paths are bounded by I8's required collapse; the store and the CAS scope scan
  are not — that trade is accepted with I9 pinning the regime.
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
