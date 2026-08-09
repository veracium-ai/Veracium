# Feature spec: who may renew a fact's currency

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft (v3, review-ready) — the ruled Design 1 matured to a full mechanical contract.** Split
> out of `0008` after its second external review showed liveness renewal needs an observation model
> `0008` cannot carry. **Ruling (research, 2026-08-08; `proposals/0012-rulings.md`): Design 1 —
> reinforcement transfers NOTHING** (not `observed_at`, not `confidence`, not `valid_from`; the
> incoming edge is persisted with its own provenance). O-Q2 (no functional violation; render both)
> and O-Q3 (`expire()` stays PER-EDGE — frozen as invariant I3) are resolved. **v3 adds the
> full-path sections** — §2/§2c field + untrusted-input contracts, §3b, the §4 mechanical contract
> (the branch keeps its guard position, only its ACTION changes — deleting it would mis-route a
> subsumed value into functional contention, I6), §5 regime (growth stated honestly), §6 invariants
> I1–I7 with executable checks, §7/§7a, §8. **No schema change, no migration, no new entry point.**
> 🔗 **Design 1 closes `0014` §3.1 + finding `M9` (§11), which argues for landing `0012` before
> `0014`.** Still `draft` — needs an external review of the chosen design before `accepted`.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v3 (review-ready)** — *the ruled design (v2) matured to a full mechanical contract: §2/§2c/§3b/§4/§5/§6 (I1–I7)/§7/§7a/§8 added; §1/§3/§10/§11 unchanged in substance. v2 folded the O-Q1/O-Q2/O-Q3 rulings; Design 1 (transfers nothing) frozen.* |
| **Status** | *see `Spec-Status:` — canonical.* Holds `0008`'s deferred liveness scope. **`0008` does not depend on this.** |
| **Internal reviewers** | — |
| **External review** | required |
| **Decision + date** | — |
| **Path** | full |

---

## 1. The defect, measured

**A repeated restatement keeps a fact permanently fresh, so the staleness flag
never fires.** `expire()` ages against `observed_at` (`lifecycle.py:41`) and
reinforcement advances `observed_at` unconditionally (`graph.py:107`):

```
SLOW relation, lifetime 120 days, edge 200 days old

control, no restatement       -> needs_confirmation = True
4 THIRD_PARTY restatements    -> needs_confirmation = False
```

**The restatements are `THIRD_PARTY`.** A party that cannot *clear* the flag
does not need to — it can prevent the flag appearing. **`0008` closes the
clearing path; this is the other door.**

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
| **restatement volume** (a flood) | — | — | N restatements/day to grow the store | the growth cost §5 states: bounded per-edge by volatility expiry; each edge is separately visible, groupable by `0006`'s `source_id`, and non-assertable if third-party. No amplification: one ingest call → one edge |

## 3b. Authorization and scope — *full specs only*

- **No new entry point and no capability change.** Restatement arrives through the existing
  `remember()`/ingest path under the existing author contract; Design 1 changes what the plan
  *does* with it, not who may do it.
- **No tenant/scope crossing.** The persisted edge inherits the ingest call's `user_id` exactly as
  any edge does.
- **Nothing becomes model-suppliable.** The model still cannot set `author`, `source_id`, `origin`,
  or any trust field; persisting the restatement adds no channel (it is the same edge ingest
  already constructs).
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

**4c. Rendering (O-Q2, ruled).** Any collapsing of same-value edges happens at **render time,
never at write time**. v1 requires no rendering change: two same-value edges render as today.
Rendering both with origin labels (*"stated by you (Jan); also reported by a third party (Aug)"*)
is recorded as the better presentation and may land as a pure rendering follow-up.

## 5. Regime analysis — where does this behave differently?

- **Growth is the honest cost (the ruling's stated trade).** Every restatement persists an edge:
  N restatements → N active same-value edges. Bounds, per volatility: `transient`/`ephemeral`
  edges LAPSE individually once stale (each ages against its own `observed_at` — I3), so their
  accumulation is self-limiting; `durable`/`slow` edges flag individually and stay; `permanent`
  edges accumulate. A restatement-heavy host grows linearly in restatements for non-lapsing
  volatilities. **Accepted for v1**: each edge is visible, attributable (it IS the `M9`
  attribution), groupable by `0006`'s `(origin, source_id)`, and non-assertable when third-party.
  A future attributed merge would be a `0014`-recorded consumption; Design 2 (`reobserve()`)
  remains the recorded successor if hosts need renewal without accumulation.
- **Per-op cost is O(1).** The reinforcement plan carries one insert and zero updates — strictly
  less write work than today's read-modify-write of the prior.
- **Concurrency.** Unchanged: the plan rides `0003`'s CAS (`expected_state` → PLAN_STALE →
  recompute). Two concurrent restatements each insert their own edge; there is no shared row to
  race on (today they race on the prior's `observed_at`/`confidence` — Design 1 removes that
  write entirely).
- **Cold vs warm store:** identical. Same-value inserts change no wiki semantics (values agree —
  no contention, no contested surface); the ordinary write counter drives recompilation as for
  any write.
- **The regime a single-op test misses (I5):** the §1 measured scenario — FOUR third-party
  restatements across 200 days, then `expire()`. Today it yields `needs_confirmation=False`; under
  Design 1 it MUST yield `True`. One restatement cannot distinguish the designs; the sequence can.

## 6. Invariants and executable checks — REQUIRED, blocking

*Prospective (unbuilt) — per PROCESS §4a they become mandatory implementation gates on
acceptance, exactly as `0003`'s pre-acceptance invariant surface did. The two `0012`-attributed `xfail` regressions live today in
`tests/test_0014_maintenance_attribution.py` and flip to passing (and move here) at
implementation.*

| | invariant | executable check |
|---|---|---|
| **I1** | a reinforcement PERSISTS the incoming edge with its own provenance, byte-unchanged from what ingest constructed — author, `observed_at`, `confidence`, `disclosure`, `source_id` all its own | `test_reinforcement_persists_the_incoming_edge_unmodified` |
| **I2** | the PRIOR is byte-identical after a reinforcement — no `observed_at`, `confidence`, `valid_from`, `note`, or flag movement | `test_reinforcement_leaves_the_prior_byte_identical` — serialize the prior before/after; assert equality |
| **I3** | **(frozen, O-Q3)** `expire()`/staleness ages each edge against **its own** `observed_at`, never the newest edge in a `(subject, relation)` group | `test_a_stale_user_edge_flags_despite_a_fresher_same_value_edge` — a 200-day user edge + a fresh third-party same-value edge; `expire()` still sets `needs_confirmation=True` on the user edge |
| **I4** | reinforcement never clears `needs_confirmation` (`specs/0008` preserved — pinned independently of I2 so a future rewrite of the branch cannot lose it silently) | the existing `0008` same-class-restatement test stays green under Design 1 |
| **I5** | **the §1 bypass is closed, measured** — repeated third-party restatements no longer keep a fact fresh OR raise its confidence | `test_restatements_no_longer_defeat_staleness` — the §1 scenario (4 restatements, 200 days, SLOW) now yields `needs_confirmation=True` and an unchanged prior confidence |
| **I6** | a same-or-subsumed value NEVER contends, absorbs, or supersedes — no refusal record, no `absorbed_duplicate`, no `supersedes` pointer, no invalidation from a reinforcement | `test_a_same_value_restatement_produces_no_contention_artifacts` — incl. the SUBSUMED form (`"Miso"` after `"cat Miso"`), the mis-routing seam §4a names |
| **I7** | the persisted restatement IS the attribution — after reinforcement, the contributing source's edge is queryable with its own provenance (closes `M9`; `0014` §3.1) | `test_reinforcement_attributes_the_contributing_source` (today an `xfail` in `tests/test_0014_maintenance_attribution.py`; flips at implementation) |

## 7. Failure modes and reversibility

- **The seam a naive implementation hits (§4a):** deleting the branch instead of changing its
  action mis-routes subsumed values into functional contention. I6's subsumed-form case exists
  precisely for this.
- **The regression that will be proposed later (O-Q3, twice over):** (a) someone "optimizes"
  expiry to age a `(subject, relation)` group against its newest member — I3 fails, the §1 bypass
  reproduces; (b) someone "restores" the `max()` transfer as a dedup optimisation — I2/I5 fail.
  Both are one-line-looking changes that remove the fix, not the cost; that is why both are
  frozen invariants rather than notes.
- **Partial failure:** none new — the reinforcement plan is one atomic insert under `0003`'s CAS;
  it either commits or returns PLAN_STALE and recomputes. There is no multi-row transfer left to
  half-apply.
- **Reversibility:** better than today. A persisted restatement can be individually inspected,
  expired, or (future) revoked by source; today's `max()` transfer is unattributed and
  irreversible — the prior's history is overwritten with no record of the contributor (`M9`).
- **Growth (the accepted risk):** §5. First visible symptom if it bites: many active same-value
  edges on one fact. Mitigations exist at render (collapse), lifecycle (per-edge lapse), and
  future attributed merge; none is load-bearing for v1 correctness.

## 7a. Surfaces touched — the honest list

- `src/veracium/graph.py` — `_build_supersession_plan`'s reinforcement branch: action changes
  from *refresh-prior-and-drop-incoming* to *persist-incoming-untouched* (§4a). **The only
  behavioural code change.**
- `src/veracium/lifecycle.py` — docstring only: the "reinforcement refreshes liveness — NOT YET
  IMPLEMENTED forward-note" comes out; `expire()`'s code is untouched (I3 pins the per-edge
  contract it already implements).
- `tests/` — the I1–I7 checks; the two `0012`-attributed `xfail`s in
  `tests/test_0014_maintenance_attribution.py` flip and migrate.
- **NOT touched:** `schema.py` (no field change), the store (no DDL, no `SCHEMA_VERSION` bump, no
  migration), `ingest.py`, `gate.py`, `portability.py` (`FORMAT_VERSION` unchanged), the wiki
  compiler, `proactive.py`.

## 8. Claims and limits

- **Closes:** the §1 measured currency bypass; the confidence door the ruling named; finding
  `M9` and `0014` §3.1 (the persisted edge is the attribution — §11).
- **Does NOT establish source continuity.** Whether the *same source* observed the fact again is
  Design 2's question (`reobserve()`, the recorded successor). Design 1 makes restatement honest
  — each observation stands on its own provenance — it does not verify anything.
- **Does NOT deduplicate storage.** Growth is the accepted cost (§5); render-time collapse is
  presentation, not a claim.
- **Does NOT touch absorption's within-class inheritance** — deliberate scope (§2); its
  attribution gap is `0014` §3.3's.
- **Depends on nothing unaccepted.** The plan machinery it rides (`0003`) is accepted and
  shipped; `0008`'s clearing rule is accepted and shipped. (v1 of this spec died partly for
  resting on then-unaccepted `0003` — stated so the reviewer can check the dependency direction
  is now sound.)

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
