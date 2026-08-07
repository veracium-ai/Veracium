# Feature spec: crash-safe consolidation

Spec-Status: in review
Spec-Requires: 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v1)** — submitted for external review 2026-08-07. Split out
> of `0002` §7e on 2026-08-02. **`0002` froze the acceptance contract and
> deliberately left two implementation strategies open. The third external review's
> point stands: acceptance authorises implementation, so "atomic or a state
> machine" would authorise two materially different designs without specifying
> either.** This spec picks one — the fenced operation record + all-or-nothing
> batch-claim primitives + the full transition table (§4). **Both open questions
> are ruled** (X-Q1 inputs stay visible until outputs are durable; X-Q2 recovery
> invalidates the cached wiki via the existing `store_version` mechanism), and
> **both `Spec-Requires:` prerequisites (`0007`, `0013`) are now accepted AND
> implemented** (§9).

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 |
| **Status** | *see `Spec-Status:` — canonical.* Owns the contract stated in `0002` §7e. |
| **Internal reviewers** | research — pending |
| **External review** | required — `lifecycle.py` is guarded and this changes durability semantics |
| **Decision + date** | **submitted for external review 2026-08-07** (round 1) |
| **Path** | full |

---

## 1. Problem and motivation

**`consolidate()` deletes every input before writing any output.**

```python
for e in cold:  store.delete_episode(e.id)     # lifecycle.py
for r in new:   store.add_episode(...)
```

**A crash between the loops loses the whole batch with no replacement** — not a
partial state, a total one. `consolidate_min_batch` defaults to 8, so the
smallest possible loss is eight episodes.

**`0002` claimed the opposite and had to withdraw it.** §7 read *"a crash leaves
a partially-maintained store, which is safe because every operation narrows."*
**Narrowing trust is not crash consistency.** `expire()` is per-edge and
idempotent so the claim holds there; **`consolidate()` is the one maintenance
operation that destroys rather than retires**, and it is exactly the one the
claim was wrong about.

**Retry is not a mitigation.** Re-running `consolidate()` after a crash
re-consolidates whatever survived, producing a summary of a summary with no
record that inputs are missing. **The second run cannot tell it is a retry.**

**Why this is not an advisory.** No trust boundary is crossed and no attacker is
involved: it needs a crash during `maintain()`. It is a durability defect in a
data-destroying operation, which is a different axis from the trust defects this
spec family otherwise tracks — and worth stating, because "not an advisory" has
been said four times now and should not become reflexive.

---

## 2. Field contracts touched

| field | change | contract |
|---|---|---|
| `Episode` records | **write-before-delete** | no input is destroyed before its replacement is durable |
| **`Episode.claimed_by`** | **NEW**, optional | the **operation** that claimed this input — one operation may produce several summaries, so this cannot name "the summary" as v5 had it |
| **`Episode.lineage`** | **NEW**, optional list | on the output: **the whole claimed set** it absorbed — `0002` N9b's lineage row, made storable |
| **`Episode.operation_id`** | **NEW**, optional | the consolidation that produced or claimed this record |
| **consolidation operation record** | **NEW** | `operation_id · fence · state · owner · lease_expires_at · claimed_ids` (§4a) |
| `FORMAT_VERSION` | **2 → 3** | shares the bump with `0009`; see §9 |

## 2c. Untrusted inputs — REQUIRED, blocking

**No caller-supplied value reaches this operation** — `consolidate()` takes a
`user_id` and reads its own inputs from the store. The uncontrolled input here
is **the machine**, which is unusual for this spec family and worth naming
rather than leaving the section empty.

| uncontrolled input | failure | invariant |
|---|---|---|
| **crash between write and delete** | inputs and output both present | **X1** — the output is durable first; duplicates are resolved by lineage, never by deleting blindly |
| **crash mid-delete** | some inputs gone, output present | **X2** — recovery completes the delete; lineage says which |
| **crash before any write** | nothing changed | no-op, by construction |
| **concurrent `maintain()`** | two consolidations of one set | **X4** — `consolidated_into` claims an episode; a second run skips claimed inputs |
| **retry after a crash** | summary-of-summary | **X3** — idempotent by lineage, not by episode content |

## 2c-ii. Assertions about reach

| assertion | command | result |
|---|---|---|
| delete precedes write | read `lifecycle.py`'s `consolidate` | `for e in cold: delete` then `for r in new: add` |
| the minimum loss is 8 | `grep -n consolidate_min_batch src/veracium/config.py` | default `8` |
| the store has no transaction API | `grep -nE "def (begin|commit|transaction)" src/veracium/store/base.py` | none — see §4 |

---

## 3. Trust-class matrix

**No trust class is read or written**, and every class is affected identically —
the operation destroys episodes regardless of authorship. **Recorded as a
finding rather than omitted**, per `0002`'s template rule.

**What is trust-relevant:** `0002` N9b requires the output to retain **any**
third-party influence in the set, and **that guarantee is void if part of the
set is lost.** A summary that silently absorbed 8 episodes and kept 5 is a
whole-set-minimum-trust claim computed over a subset. **This spec is what makes
N9b's premise true.**

---

## 4. Behaviour

**Rewritten after the fourth external review of `0002` showed the first draft
was not implementable.** Three gaps, each real: multiple summaries had no
input→output mapping, the claim was not atomic, and recovery could not tell a
crash from a live writer mid-LLM-call.

### 4a. A persistent operation record, not a fence alone

**Fifth review, finding 8: a fence orders; it does not prove liveness.** A
lower-fenced worker may still be running a slow LLM call, so "higher fence wins"
permits a live worker's inputs to be stolen. **Preemption is only safe if the
preempted worker can no longer write anything.**

```
ConsolidationOp:
  operation_id     opaque, unique
  fence            monotonic from the store
  state            CLAIMED | GENERATING | OUTPUTS_DURABLE | FINALIZED | ABANDONED
  owner            worker identity
  lease_expires_at when the claim may be preempted
  claimed_ids      the exact input set
```

> **Every write, visibility change and delete compares-and-sets on
> `(operation_id, fence)`.** A worker that has lost its fence **cannot write an
> output, cannot change visibility, and cannot delete an input** — its
> operations fail rather than racing.

**Preemption requires an expired lease, not merely a higher number.** A
heartbeat extends the lease while an LLM call is genuinely in flight; an expired
lease is evidence of abandonment in a way a fence is not.

### 4b. An explicit atomic batch-claim primitive

**Finding 9: "one conditional update" does not give all-or-nothing.** An
ordinary `UPDATE ... WHERE` claims the eligible subset and reports a smaller row
count — **a partial claim, the exact state the design called impossible.**

> **New `Store` methods, all marked `@store_mutator`:**
> ```
> create_or_takeover_consolidation(user_id, ids, owner, lease) -> Op | None
> renew_consolidation_lease(operation_id, fence, owner)        -> bool
> write_consolidation_output_if_current(op_id, fence, episode) -> bool
> transition_consolidation_if_current(op_id, fence, to_state)  -> bool
> delete_claimed_inputs_if_current(op_id, fence)               -> bool
> abandon_consolidation_if_current(op_id, fence)               -> bool
> ```
> **Every one takes `(operation_id, fence)` and returns `False` if the caller no
> longer owns it.** Each backend implements the atomicity; the interface states
> the contract.

**Sixth review, finding 7:** v6 required every write, visibility change and
delete to compare-and-set on `(operation_id, fence)` and then specified **one**
new method. `add_episode` and `delete_episode` take neither, so **the design
could not enforce its most important rule** — a prose requirement that writes be
fenced does not make the interface capable of fencing them.

*(This is why `store_mutator` had to become a marker rather than a name prefix —
`claim_episode_batch` matches none of the old ones and would have been invisible
to the audit manifest while writing persistent trust state.)*

### 4b-ii. The complete transition table

**Finding 8: several states were named and none was fully defined.**

| state | who may act | inputs | outputs | permitted next | recovery | idempotency key |
|---|---|---|---|---|---|---|
| `CLAIMED` | owner with live lease | **visible** | absent | `GENERATING` · `ABANDONED` | lease expired → `ABANDONED` | `operation_id` |
| `GENERATING` | owner with live lease | **visible** | absent | `OUTPUTS_DURABLE` · `ABANDONED` | lease expired → `ABANDONED`; **partial outputs deleted by `operation_id`** | `operation_id` |
| `OUTPUTS_DURABLE` | owner, or recovery | hidden | **visible** | `FINALIZED` | **roll forward, never back** — outputs exist and are correct | `operation_id` |
| `FINALIZED` | — | deleted | **visible** | — | none needed | — |
| `ABANDONED` | any worker may take over | **visible** | absent | `CLAIMED` (new fence) | delete any output tagged `operation_id`, release claims | `operation_id` |

**`OUTPUTS_DURABLE` is the point of no return.** Before it, recovery deletes
partial outputs and releases inputs; after it, recovery only completes the
deletion. **The expected output set is persisted before the transition**, so
recovery can tell a complete write from a partial one.

**Takeover creates a new fence on the same `operation_id`**, so outputs written
by the preempted worker are identifiable and removable. **The lease clock is the
store's**, not any worker's — worker clocks disagree and a lease decided by the
holder is not a lease.

### 4c. Exactly one representation is visible

**Finding 10: hiding inputs at claim time creates a window where a read sees
neither inputs nor outputs** — the LLM call, or a crash before outputs are
durable. That is not duplication or data loss, it is **missing user history**,
and if recovery only runs at the next consolidation it can persist indefinitely.
**v5's claim that recovery timing became a non-issue was wrong.**

| state | inputs | outputs |
|---|---|---|
| `CLAIMED` / `GENERATING` | **visible** | absent |
| `OUTPUTS_DURABLE` | hidden | **visible** |
| `FINALIZED` | deleted | **visible** |

> **X9 (restated): every ordinary read sees exactly one complete
> representation** — all relevant inputs, or all committed outputs. **Never both
> and never neither.**

**Finding 9: "atomic with respect to readers" is not a read contract.**

> **`store.episodes()` reads episodes and the operation record in one
> snapshot**, and returns the representation for the state observed in that
> snapshot. A backend without snapshot reads must instead **tag each episode row
> with the operation generation** and have readers retry when the generation
> changes mid-read.

Without one of those, a transition and an ordinary query can interleave and
still expose both representations or neither — **which is the failure this
section exists to prevent, so leaving it to the backend is leaving the
guarantee unimplemented.**

### 4d. Lineage must be established before generation, not inferred after

**Finding 11, and this is the one that would have shipped a defect.** v5 had the
caller partition inputs across outputs by date range *after* a whole-batch LLM
call. **The model sees every input**, so any output may carry content derived
from any of them — and a date partition then **understates provenance**:

```
third-party-influenced input A ─┐
                                ├─ whole-batch prompt ─→ output nominally
user input B ───────────────────┘                        assigned only to B
```

**That recreates the laundering defect N9b exists to prevent, inside the spec
written to satisfy N9b.** A post-hoc partition is not evidence of influence.

> **Frozen: whole-batch lineage.** One claimed set produces outputs that **all
> inherit the entire claimed set as lineage**, and **all carry the minimum trust
> across it** (N9b). If narrower lineage is wanted, the batch must be
> **partitioned before generation**, so each model call sees only the inputs
> that will become its output's lineage.

**Chosen because it cannot be got wrong by accident.** Pre-partitioning is
strictly better provenance and more LLM calls; whole-batch is one call and a
conservative over-attribution. **Over-attributing influence is safe;
under-attributing is the laundering defect.**

### 4d-ii. A summary must not claim a single date it does not have

**Finding 10, and it is the one N9b's mixed-currency row actually needs.**
Whole-batch lineage preserves *influence*; it does not fix *visible time*. A
consolidated episode still has one `date`, chosen by the model, **rendered
directly into recall and compiled history** — and N9b already says neither the
minimum nor the maximum input time represents a mixed set honestly.

> **The output carries `date_start` and `date_end`** (the min and max of the
> claimed set's dates) and renders as a **range**. A single `date` is written
> only when the range is degenerate.

**A lineage list in storage does not stop a misleading date reaching the
model** — which is the only place any of this matters.

`Store` is an interface with a Postgres implementation contemplated. Requiring
cross-backend atomic multi-statement transactions pushes a durability guarantee
into every future backend. **`claim_episode_batch` is one primitive with a
stated contract**, which is a smaller ask than "implement transactions".

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **X1** an input is never deleted before its summary is durable | `test_consolidation_writes_before_deleting` — a store wrapper that raises after the write | CI |
| **X2** a crash mid-delete is recovered, not repeated | `test_recovery_completes_a_partial_delete` | CI |
| **X3** retry is idempotent by **lineage**, not by content | `test_consolidation_retry_is_idempotent` — **no summary-of-summary** | CI |
| **X4** the claim is **atomic over the whole set** | `test_concurrent_consolidation_claims_all_or_nothing` — two workers, overlapping candidate sets; exactly one wins | CI |
| **X7** a claim is preemptible only on an **expired lease**, never on fence order alone | `test_a_live_lease_is_not_preempted` — a heartbeating worker mid-LLM-call keeps its claim | CI |
| **X10** a worker that has lost its fence **cannot write, flip visibility, or delete** | `test_a_preempted_worker_cannot_write_or_delete` — the invariant that makes preemption safe | CI |
| **X11** `claim_episode_batch` is all-or-nothing | `test_partial_claim_is_impossible` — contend for an overlapping set; the loser changes nothing | CI |
| **X12** every output's lineage is the **whole claimed set** | `test_lineage_is_the_whole_batch` — **a post-hoc date partition would under-attribute third-party influence** | CI |
| **X8** every output carries the **whole** claimed set as lineage | `test_lineage_is_the_whole_batch` — **there is no input→output partition**; v5's exact-partition rule contradicted whole-batch lineage | CI |
| **X9** every read sees **exactly one** complete representation — never both, **never neither** | `test_every_read_sees_exactly_one_representation` — sweeps every state and every phase boundary | CI |
| **X5** no crash point loses an episode without a replacement | `test_no_crash_point_loses_data` — **parametrised over every store call in the operation**, failing at each in turn | CI |
| **X6** lineage is complete | `test_summary_lineage_lists_every_absorbed_episode` — **N9b's premise** | CI |

**X5 is the one that matters** and is written as a sweep rather than three cases,
because the defect being fixed is precisely *a crash at the one point nobody
enumerated*.

---

## 7. Failure modes and reversibility

**Failure mode is a leftover claim or a duplicate**, both detectable and both
resolved by the recovery pass. **Reversible in code**; the new fields are
additive and older builds ignore them — **which is the `0007` problem again**:
an older build would not run recovery and would not know a claim means anything.
See §9.

---

## 8. Claims and limits

**Claim:** no crash during consolidation loses an episode that has no
replacement.

**Limits:**

- **Not durability of the store itself.** If SQLite loses a committed write, this
  spec cannot help; it assumes each individual store call is atomic.
- **Not multi-process safety in general.** X4 covers the claim race for
  consolidation; nothing else in `maintain()` is coordinated.
- **Not a rollback.** A completed consolidation is not undoable — the inputs are
  gone by design. **Only the crash window is made safe.**

---

## 9. Prerequisite: `specs/0007`

Same argument as `0009`, and it is now the **third** spec to need it.
`Episode.model_config["extra"]` is pydantic's default `ignore`, so an older
build reading a consolidating store **silently drops `consolidated_into` and
`lineage`** — it would see claimed-but-undeleted inputs as ordinary episodes and
would never run recovery. **Silent misinterpretation, not failure.**

> **UPDATE 2026-08-07: the prerequisite is SATISFIED.** `0007` is `accepted`
> (2026-08-03) **and implemented** — the store carries `PRAGMA user_version`, so an
> older build opening a store written by this change refuses (`newer`) instead of
> silently dropping the operation record and skipping recovery. `0013` (migrations)
> is `accepted` (2026-08-07) **and implemented** (via `0008`), so the new `Episode`
> fields + the `ConsolidationOp` record land through the accepted offline v→v+1
> migration — and this spec SHARES the `FORMAT_VERSION 2→3` / schema bump with
> `0009` (§2), so if both land together it is one migration, not two. Both
> `Spec-Requires:` deps are met.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~X-Q1~~ | **ANSWERED, and v5's answer was wrong.** v5 said hiding claimed inputs made recovery timing a non-issue; the sixth review showed that leaves a window where a read sees **neither** inputs nor outputs. §4c now keeps inputs **visible** until outputs are durable, so **recovery timing is a liveness question, not a correctness one** — run it at the start of each `consolidate()` and surface the count in `introspect()`. | resolved | dev | — |
| ~~X-Q2~~ | **RULED 2026-08-07 (dev): YES — recovery invalidates the cached wiki**, same principle as `0004` W1 (a derived view must not outlive a change to its inputs). Recovery changes the episode set — it completes a delete, or removes a preempted worker's partial outputs — so a wiki compiled from the pre-recovery set is stale. **The mechanism already exists and requires no special drop:** every recovery mutation goes through the fenced `@store_mutator` primitives (`write_consolidation_output_if_current`, `delete_claimed_inputs_if_current`, …), which bump the per-user `store_version` write counter like any mutation; recall reads `store_version` to detect a stale cached wiki and recompiles. So the requirement is simply that **recovery's writes and deletes are ordinary counter-bumping mutations** (they are, being `@store_mutator`), and the invalidation falls out. `0004` owns the general derived-view-invalidation contract; this spec only asserts recovery is a change its inputs, not an exception to it. | resolved | dev | — |
