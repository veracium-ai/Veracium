# Feature spec: crash-safe consolidation

Spec-Status: in review
Spec-Requires: 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v3)** — rounds 1 and 2 both **approved the fenced-state-machine
> architecture**. Round 1 deferred on 3 gaps + 5 corrections (all closed in v2, §11);
> round 2 deferred on 4 more gaps + 3 corrections (all closed in v3, §12): the
> `SCHEMA_VERSION`/`FORMAT_VERSION` namespace split (§9a), abandonment as
> cleanup-complete before takeover (§4b-iii), the post-`FINALIZED` retry rule —
> consolidated outputs are never candidates (§4e), quiescent-snapshot export (§4f),
> plus `user_id` on the operation record + `forget_user()` erasure, the date
> written-vs-rendered fix, and X1 realigned to Design A. The design: a fenced
> operation record + all-or-nothing batch-claim primitives + a recovery-discovery
> read + the full transition table (§4), under **Design A** (the transition is the
> sole completeness proof). Split out of `0002` §7e on 2026-08-02. **Both open
> questions ruled** (X-Q1/X-Q2); **both `Spec-Requires:` prerequisites (`0007`,
> `0013`) accepted AND implemented** (§9).

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v3 |
| **Status** | *see `Spec-Status:` — canonical.* Owns the contract stated in `0002` §7e. |
| **Internal reviewers** | research — pending |
| **External review** | required — `lifecycle.py` is guarded and this changes durability semantics |
| **Decision + date** | **rounds 1 & 2 returned 2026-08-07: architecture approved both times; v2 closed round 1 (§11), v3 closes round 2 (§12) — 4 gaps + 3 corrections** |
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
| **`Episode.date_start`** | **NEW**, optional | on a consolidated output: the **minimum** date across the claimed set (§4d-ii). Persisted, not rendered-only — it is in the schema/migration contract, and recall reads it. |
| **`Episode.date_end`** | **NEW**, optional | on a consolidated output: the **maximum** date across the claimed set. Invariant `date_start <= date_end`. |
| **`Episode.date`** (compatibility) | unchanged, required | a plain episode keeps its single `date`. A consolidated output sets `date := date_start` for backward sort/compat and renders a **single date only when `date_start == date_end`** (degenerate range), else a range (§4d-ii). Plain and consolidated episodes sort together on `date`. |
| **consolidation operation record** | **NEW** | `user_id · operation_id · fence · state · owner · lease_expires_at · claimed_ids` (§4a) — **`user_id` is on the record** (Correction B, round 2): recovery is queried per-user, every `claimed_id` must belong to `user_id`, and `forget_user()` erases the operation/claim state atomically. **No expected-output field** — Design A makes the transition the completeness proof (§4b-ii, §11-F2). |
| **`SCHEMA_VERSION`** (on-disk) | **2 → 3** | the **on-disk store shape** (`PRAGMA user_version`) — the new `Episode` fields + the operation-record table land here. **This is what `0013` migrates.** Conditionally shared with `0009`; §9. |
| **`FORMAT_VERSION`** (export wire) | **2 → 3** | the **portable export/import representation** — the new `Episode` fields change what a `.jsonl` export carries, so an older importer must refuse rather than silently drop them. **`0007` §8 holds this is a namespace independent of `SCHEMA_VERSION`;** they are coincidentally both `2` today. Conditionally shared with `0009`; §9. |

## 2c. Untrusted inputs — REQUIRED, blocking

**No caller-supplied value reaches this operation** — `consolidate()` takes a
`user_id` and reads its own inputs from the store. The uncontrolled input here
is **the machine**, which is unusual for this spec family and worth naming
rather than leaving the section empty.

| uncontrolled input | failure | invariant |
|---|---|---|
| **crash while `GENERATING`, before the visibility transition** | provisional (hidden) output rows exist; inputs still visible | **X1** — under Design A the transition is the sole completeness proof: recovery deletes **every** row tagged `operation_id` and the inputs (never hidden pre-transition) simply remain; there is no visible coexistence to reconcile, and no blind delete of inputs |
| **crash after the batch-delete commits, before `FINALIZED`** | inputs gone, output present, op not finalised | **X2** — the delete is one **all-or-nothing** primitive (§4b), so there is no durable "some inputs gone"; recovery re-issues the idempotent delete and finalises |
| **crash before any write** | nothing changed | no-op, by construction |
| **concurrent `maintain()`** | two consolidations of one set | **X4** — `Episode.claimed_by` (the operation) claims an input; a second run skips claimed inputs |
| **response lost after `FINALIZED`** | outputs visible, op excluded from `pending_consolidations`, outputs' compat `date` still old → re-eligible as cold candidates | **X3** — **a consolidated output (any episode carrying `lineage`/`operation_id`) is never itself a consolidation candidate** (§4e), so a re-run cannot reconsolidate its own outputs into a summary-of-summary |

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
  user_id          the tenant — every claimed_id belongs to it (Correction B)
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

**`user_id` is on the record, and the operation is user-scoped erasable state
(Correction B, round 2).** Recovery is queried by `pending_consolidations(user_id)`,
so the tenant must be first-class, not inferred by joining through claimed/output
rows that a delete may already have removed. Every `claimed_id` MUST belong to
`user_id`. The operation record is per-user persistent data, so **`forget_user()`
deletes the operation and its claim/provisional-output state atomically with the
rest of that user's memory** — the store's existing "erase everything for the user"
contract now explicitly covers consolidation state.

### 4b. An explicit atomic batch-claim primitive

**Finding 9: "one conditional update" does not give all-or-nothing.** An
ordinary `UPDATE ... WHERE` claims the eligible subset and reports a smaller row
count — **a partial claim, the exact state the design called impossible.**

> **New `Store` methods.** The six mutators are marked `@store_mutator`;
> `pending_consolidations` is a **read** and is not:
> ```
> create_or_takeover_consolidation(user_id, ids, owner, lease) -> Op | None
> renew_consolidation_lease(operation_id, fence, owner)        -> bool
> write_consolidation_output_if_current(op_id, fence, episode) -> bool
> transition_consolidation_if_current(op_id, fence, to_state)  -> bool
> delete_claimed_inputs_if_current(op_id, fence)               -> bool
> abandon_consolidation_if_current(op_id, fence)               -> bool
> pending_consolidations(user_id) -> list[Op]     # READ — recovery-discovery
> ```
> **Every mutator takes `(operation_id, fence)` and returns `False` if the caller no
> longer owns it.** Each backend implements the atomicity; the interface states
> the contract.

**Recovery-discovery is a first-class Store read (finding 1, round 1).** X-Q1
requires `consolidate()` to run recovery at its own start and surface the count in
`introspect()` — but the fenced mutators above cannot *find* the operations to
recover. After a `GENERATING → OUTPUTS_DURABLE` crash the inputs are hidden from
ordinary reads, so a cold-candidate `create_or_takeover_consolidation` can never
stumble onto them. `pending_consolidations(user_id)` returns every operation not in
`{FINALIZED}` — the interface through which the normative recovery pass is
implementable **without backend-private access.** Recovery reads it, applies the
§4b-ii transition table to each, and counts them for `introspect()`.

*(The claim primitive has exactly one name across this spec —
`create_or_takeover_consolidation` — and the input-claim field has exactly one
name — `Episode.claimed_by`. Earlier drafts also wrote `claim_episode_batch` /
`consolidated_into`; those synonyms are retired, since the names appear in the
migration and Store API and a stray synonym in normative text is a defect.)*

**Sixth review, finding 7:** v6 required every write, visibility change and
delete to compare-and-set on `(operation_id, fence)` and then specified **one**
new method. `add_episode` and `delete_episode` take neither, so **the design
could not enforce its most important rule** — a prose requirement that writes be
fenced does not make the interface capable of fencing them.

*(This is why `store_mutator` had to become a marker rather than a name prefix —
`create_or_takeover_consolidation` matches none of the old `add_`/`delete_`/`set_`
prefixes and would have been invisible to the audit manifest while writing
persistent trust state. **Note the marker is only an audit-manifest tag — it does
NOT advance `store_version`; that is a separate explicit `_bump`, see §11-F3.**)*

### 4b-ii. The complete transition table

**Finding 8: several states were named and none was fully defined.**

The **outputs** column is *ordinary-read visibility*, not physical presence:
provisional output rows may physically exist while `GENERATING` (they are written
one at a time), but they are absent from every ordinary read until the atomic
transition into `OUTPUTS_DURABLE` flips visibility (Correction D).

| state | who may act | inputs (visible) | outputs (physical rows / ordinary-read) | permitted next | recovery | idempotency key |
|---|---|---|---|---|---|---|
| `CLAIMED` | owner with live lease | **visible** | none / hidden | `GENERATING` · `ABANDONED` | lease expired → `ABANDONED` | `operation_id` |
| `GENERATING` | owner with live lease | **visible** | **zero or more provisional rows** / hidden | `OUTPUTS_DURABLE` · `ABANDONED` | lease expired → `ABANDONED`; **delete ALL rows tagged `operation_id`** (Design A), release claims | `operation_id` |
| `OUTPUTS_DURABLE` | owner, or recovery | hidden | present / **visible** | `FINALIZED` | **roll forward, never back** — the transition committed, so outputs are complete and correct | `operation_id` |
| `FINALIZED` | — | deleted | present / **visible** | — | none needed | — |
| `ABANDONED` | any worker may take over | **visible** | **none remain** / hidden | `CLAIMED` (new fence) | already clean — `ABANDONED` is only observable *after* cleanup (§4b-iii) | `operation_id` |

**`OUTPUTS_DURABLE` is the point of no return, and Design A makes the atomic
transition itself the sole completeness proof (finding 2).** All output rows
written while `GENERATING` are **provisional and invisible**. If the process
crashes at any point before the atomic `GENERATING → OUTPUTS_DURABLE` transition,
recovery deletes **every** row tagged `operation_id` — *even if all intended
outputs happened to be written* — and re-exposes the inputs (which never stopped
being visible). Recovery therefore never has to distinguish "complete but not
transitioned" from "partial": before the transition, nothing counts; after it,
everything does. **No expected-output set is persisted** — the operation record
carries none (§4a), and there is no primitive to establish one, because Design A
needs neither. (Design B — recognising a complete pre-transition generation from a
persisted output plan — was considered and rejected in round 1: it adds
`expected_output_ids`/`_count` plus a fenced primitive for a strictly weaker
guarantee, against this spec's "cannot be got wrong by accident" ethos.)

**Takeover creates a new fence on the same `operation_id`**, so outputs written
by the preempted worker are identifiable and removable. **The lease clock is the
store's**, not any worker's — worker clocks disagree and a lease decided by the
holder is not a lease.

### 4b-iii. Abandonment is cleanup-complete before a new fence issues (round 2, finding 2)

**Provisional output rows carry only `operation_id`, and there is no output
generation/fence on a row.** So if a new fence could become current while the old
generation's provisional rows still existed, a delete-by-`operation_id` could not
tell them apart — it would either destroy the new generation's work or leave the
old generation's stale rows to surface beside it at the next `OUTPUTS_DURABLE`
transition. Reusing `operation_id` across fences is only safe if the old generation
is **provably gone** before the new one starts.

> **Frozen.** `abandon_consolidation_if_current(op_id, fence)` is **one atomic
> primitive** whose success means, together: **every provisional output row tagged
> `operation_id` is deleted, every input claim is released, and only then is the
> operation observably `ABANDONED`.** Therefore:
> ```
> ABANDONED  ⇒  no provisional output row for that operation remains
>            ⇒  no input remains claimed by it
> ```
> **`create_or_takeover_consolidation` may advance the fence ONLY from that clean
> `ABANDONED` state** — never from a live `CLAIMED`/`GENERATING` op, and never
> before cleanup commits. This keeps Design A's minimalism (no per-row fence, no
> output-generation field): the clean-state invariant, not a row tag, is what makes
> `operation_id` reuse unambiguous. Invariant **X15**.

### 4c. Exactly one representation is visible

**Finding 10: hiding inputs at claim time creates a window where a read sees
neither inputs nor outputs** — the LLM call, or a crash before outputs are
durable. That is not duplication or data loss, it is **missing user history**,
and if recovery only runs at the next consolidation it can persist indefinitely.
**v5's claim that recovery timing became a non-issue was wrong.**

The **outputs** column is ordinary-read visibility (Correction D): "hidden" means
no ordinary read returns those rows, whether or not provisional rows physically
exist.

| state | inputs (ordinary read) | outputs (ordinary read) |
|---|---|---|
| `CLAIMED` / `GENERATING` | **visible** | hidden (provisional rows may exist physically) |
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

> **X9 is a conformance requirement, not a suggestion (round 1, §4c question).**
> The spec freezes the *observable contract* — every ordinary read sees exactly one
> complete representation — and permits either mechanism (a transactionally
> consistent snapshot, or generation-tagged rows with reader retry) as a
> backend-internal means of producing it. **A backend that provides neither is
> non-conforming with `0010`; X9 is required of every Store backend that implements
> this schema.** This is not the rejected `0002` "atomic or a state machine" fork —
> that left the consolidation protocol itself undefined; here there is one
> externally visible read result and only the means of producing it is
> backend-specific, exactly as different databases implement the same atomic Store
> primitive differently.

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
> claimed set's dates) and renders as a **range**. **`date` is ALWAYS persisted as
> `date_start`** (the §2 compatibility/sort contract); a single date is **rendered**
> only when the range is degenerate (`date_start == date_end`), else the range is
> rendered (Correction A, round 2 — "written" was wrong; the stored `date` is always
> `date_start`, only the *rendering* is conditional).

**A lineage list in storage does not stop a misleading date reaching the
model** — which is the only place any of this matters.

### 4e. A consolidated output is never itself a consolidation candidate (round 2, finding 3)

The state machine makes every *pre*-finalization crash safe, but **response loss
after `FINALIZED`** is a distinct cell X3 must cover. Say 16 cold episodes compress
to 8 outputs; the batch delete commits, the op reaches `FINALIZED`, then the worker
dies before the caller sees completion. On the next `consolidate(user_id)`:
`pending_consolidations` excludes `FINALIZED`, the 8 outputs are visible, their
compat `date` is `date_start` (still old), and `consolidate_min_batch` is 8 — so all
8 are immediately re-eligible as cold candidates and reconsolidate into a
summary-of-summary. The transition table keys idempotency on `operation_id`, not
lineage, so an implementer can satisfy it and still fail X3 here.

> **Frozen (candidate eligibility).** **An episode that carries consolidation
> provenance — a non-empty `lineage` or an `operation_id` naming a consolidation —
> is NEVER selected as a consolidation candidate.** A finalized generation's own
> outputs are therefore permanently ineligible for reconsolidation, so a
> response-lost retry finds no cold candidates and is a no-op. Invariant **X3'/X16**.

> **Limit made explicit.** This **forbids recursive compaction** (summarising
> summaries) in v1 — a deliberate trade for mechanical retry-idempotency without a
> caller idempotency token (which `consolidate()` does not take). If recursive
> compaction is ever wanted it needs its own spec: lineage must be **flattened** into
> the new output, a new operation must distinguish legitimate later compaction from
> replay **from durable state** (not caller intent), and — if lineage equality is the
> replay key — lineage needs **canonical set semantics** (order- and
> duplicate-independent) so the absorbed-set identity is stable. None of that is in
> v1; the flat "outputs are not candidates" rule is.

### 4f. Export is a logical quiescent snapshot (round 2, finding 4)

Because v2 changes the export `FORMAT_VERSION`, the portable path is now
load-bearing. In `CLAIMED`/`GENERATING` the inputs stay ordinary-read **visible**
and persist `Episode.claimed_by`; `export_memory` serializes `store.episodes(user_id)`
but **not** the `ConsolidationOp` records. So exporting mid-generation yields an
episode with `claimed_by = op-1` and no `op-1` in the export; on import into a fresh
store there is **no operation to recover**, yet X4 makes the claimed episode
ineligible for a new claim — a **durable orphan** created purely by the portable path.

> **Frozen.** Export is a **logical quiescent snapshot**: before it serializes,
> every live consolidation for that user MUST be driven to a settled state —
> **recovered forward (`FINALIZED`) or abandoned (clean)** — **or the export refuses.**
> **Transient claim metadata is never exported without the durable operation state
> that gives it meaning:** an exported episode never carries a dangling `claimed_by`.
> (Exporting the live state machine itself is rejected — `owner`/`lease` semantics do
> not transfer to another store.) The `FORMAT_VERSION` acceptance test exercises
> export/import from **every** consolidation state, not just finalized outputs.
> Invariant **X17**. (`0005` owns import's trust cap; this is the orthogonal
> *completeness* rule — a claim without its operation is not importable state.)

`Store` is an interface with a Postgres implementation contemplated. Requiring
cross-backend atomic multi-statement transactions pushes a durability guarantee
into every future backend. **`create_or_takeover_consolidation` is one primitive
with a stated contract**, which is a smaller ask than "implement transactions".

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **X1** an input is never deleted before its summary is durable | `test_consolidation_writes_before_deleting` — a store wrapper that raises after the write | CI |
| **X2** the batch-delete is all-or-nothing; a crash **after** it commits but before `FINALIZED` is recovered by an **idempotent re-delete + finalise**, never a re-consolidation | `test_recovery_finalises_after_committed_delete` — there is no durable "some inputs deleted" state to complete | CI |
| **X13** recovery is **discoverable**: `pending_consolidations(user_id)` returns every non-`FINALIZED` operation, including one stranded in `OUTPUTS_DURABLE` whose inputs are hidden | `test_recovery_discovers_a_stranded_durable_operation` — a cold-candidate claim could never find it (finding 1) | CI |
| **X14** the `GENERATING → OUTPUTS_DURABLE` visibility cutover **advances `store_version`** in the same atomic mutation, though it changes no episode row | `test_visibility_cutover_bumps_store_version` — a cached wiki compiled from the still-visible inputs must not read fresh after the cutover (finding 3) | CI |
| **X3** retry is idempotent — **no summary-of-summary**, including after a response-lost `FINALIZED` | `test_consolidation_retry_is_idempotent` + `test_finalized_outputs_are_not_reconsolidated` — a re-run over a finalized generation's own visible outputs finds no candidates (§4e) | CI |
| **X15** `ABANDONED` is cleanup-complete: no provisional output row and no claim survive it, and a new fence can only advance from that clean state | `test_takeover_requires_clean_abandoned` — a stale provisional row tagged `operation_id` cannot coexist with a new fence's rows (finding 2) | CI |
| **X16** an episode carrying `lineage`/`operation_id` is never a consolidation candidate | `test_consolidated_output_is_not_a_candidate` — 16→8 finalized, re-run selects none of the 8 (finding 3) | CI |
| **X17** export is a quiescent snapshot: a live claim is settled or export refuses; no exported episode carries a dangling `claimed_by`; `forget_user()` erases operation state | `test_export_refuses_or_settles_live_consolidation` + `test_forget_user_erases_consolidation_ops` (findings 4 + Correction B) | CI |
| **X4** the claim is **atomic over the whole set** | `test_concurrent_consolidation_claims_all_or_nothing` — two workers, overlapping candidate sets; exactly one wins | CI |
| **X7** a claim is preemptible only on an **expired lease**, never on fence order alone | `test_a_live_lease_is_not_preempted` — a heartbeating worker mid-LLM-call keeps its claim | CI |
| **X10** a worker that has lost its fence **cannot write, flip visibility, or delete** | `test_a_preempted_worker_cannot_write_or_delete` — the invariant that makes preemption safe | CI |
| **X11** `create_or_takeover_consolidation` is all-or-nothing | `test_partial_claim_is_impossible` — contend for an overlapping set; the loser changes nothing | CI |
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

**Failure mode is a stranded operation** — a leftover claim with hidden provisional
outputs (pre-transition) or an un-`FINALIZED` `OUTPUTS_DURABLE` (post-transition) —
**discovered by `pending_consolidations(user_id)` and resolved by the recovery pass**
(roll back before the cutover, roll forward after; §4b-ii). Under Design A there is
never a *visible* input+output duplicate to reconcile. **Reversible in code**; the new
fields are additive and older builds ignore them — **which is the `0007` problem
again**: an older build would not run recovery and would not know a claim means
anything. See §9.

---

## 8. Claims and limits

**Claim:** no crash during consolidation loses an episode that has no
replacement.

**Limits:**

- **Not durability of the store itself.** If SQLite loses a committed write, this
  spec cannot help; it assumes each individual store call is atomic. In
  particular `delete_claimed_inputs_if_current` is **one** such atomic call, so a
  crash cannot leave a durable "some inputs deleted" state — which is why X2 is
  framed as crash-after-commit, not crash-mid-delete (Correction E).
- **Not multi-process safety in general.** X4 covers the claim race for
  consolidation; nothing else in `maintain()` is coordinated.
- **Not a rollback.** A completed consolidation is not undoable — the inputs are
  gone by design. **Only the crash window is made safe.**
- **Not recursive compaction.** A consolidated output is never itself a candidate
  (§4e), so summaries are never re-summarised in v1. This is the price of mechanical
  retry-idempotency without a caller idempotency token; recursive compaction would
  need its own spec (§4e states what it would have to freeze).
- **Not export of a live consolidation.** Export is a quiescent snapshot (§4f): a
  live operation is settled or export refuses. The running state machine is not
  itself portable — `owner`/`lease` do not transfer to another store.

---

## 9. Prerequisite: `specs/0007`

Same argument as `0009`, and it is now the **third** spec to need it.
`Episode.model_config["extra"]` is pydantic's default `ignore`, so an older
build reading a consolidating store **silently drops `claimed_by`, `operation_id`
and `lineage`** — it would see claimed-but-undeleted inputs as ordinary episodes
and would never run recovery. **Silent misinterpretation, not failure.**

> **UPDATE 2026-08-07: the prerequisite is SATISFIED.** `0007` is `accepted`
> (2026-08-03) **and implemented** — the store carries `PRAGMA user_version`, so an
> older build opening a store written by this change refuses (`newer`) instead of
> silently dropping the operation record and skipping recovery. `0013` (migrations)
> is `accepted` (2026-08-07) **and implemented** (via `0008`), so the new `Episode`
> fields + the operation-record table land through the accepted offline **`SCHEMA_VERSION`**
> `v→v+1` migration. Both `Spec-Requires:` deps are met.

### 9a. Two version namespaces, not one (round 2, finding 1)

**`SCHEMA_VERSION` and `FORMAT_VERSION` are different counters and `0010` changes
both.** Round-1 correction B spoke only of "`FORMAT_VERSION 2→3`" — but `0007` §8
holds these are **independent namespaces**, and `0013` migrates the **on-disk**
one:

| counter | what it versions | source | `0010`'s change | who migrates it |
|---|---|---|---|---|
| **`SCHEMA_VERSION`** | on-disk store shape (`PRAGMA user_version`) | `store/schema_version.py` (`= 2`) | the new `Episode` columns + the operation-record table | **`0013`** (offline `v→v+1`) |
| **`FORMAT_VERSION`** | portable export/import wire format | `portability.py` (`= 2`) | the new `Episode` fields in a `.jsonl` export | `portability.py` version guard |

They are **coincidentally both `2` today**; that coincidence is not identity. The
`0013` migration prose refers to **`SCHEMA_VERSION`**, never `FORMAT_VERSION`.

**Each namespace has its OWN conditional-share rule with `0009` (Correction B,
round 1 — now applied per-namespace).** `0009` independently changes the same two
counters; nothing in the dependency gate forces co-landing, and `0010` does **not**
make `0009` a prerequisite. So, **for each version space that a spec changes,
independently:**

> If `0009` and `0010` co-implement in one release, their fields compose into
> **one** `SCHEMA_VERSION` step **and** one `FORMAT_VERSION` revision.
>
> If either ships first, **that spec owns the next value in each version space it
> changes**, and the later sibling takes the following value in that space. **A
> released `SCHEMA_VERSION` is never redefined in place, and a released
> `FORMAT_VERSION` is likewise never redefined.**

This keeps "one shared migration / one shared format bump" an optimisation available
only on genuine co-implementation, and prevents an accidental same-value mutation in
*either* namespace.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~X-Q1~~ | **ANSWERED, and v5's answer was wrong.** v5 said hiding claimed inputs made recovery timing a non-issue; the sixth review showed that leaves a window where a read sees **neither** inputs nor outputs. §4c now keeps inputs **visible** until outputs are durable, so **recovery timing is a liveness question, not a correctness one** — run it at the start of each `consolidate()` and surface the count in `introspect()`. **Round 1 made the discovery surface explicit:** recovery finds its work through the `pending_consolidations(user_id)` Store read (§4b), not by stumbling on hidden inputs as cold candidates. | resolved | dev | — |
| ~~X-Q2~~ | **RULED 2026-08-07 (dev), CORRECTED round 1: YES — the cutover and recovery invalidate the cached wiki**, same principle as `0004` W1 (a derived view must not outlive a change to its inputs). **The round-1 mechanism claim was wrong and is retracted:** `@store_mutator` is only an audit-manifest marker (`fn.__store_mutator__ = True`) — it does **not** advance `store_version`; each SQLite mutator bumps *explicitly* via `_bump()`, and `set_wiki` is itself `@store_mutator` yet deliberately does not bump, proving the two are not equivalent. Worse, the load-bearing `GENERATING → OUTPUTS_DURABLE` transition changes **no episode row at all** — it only flips which representation `episodes()` returns — so nothing would bump unless we say so. **The corrected rule is the frozen invariant in §11-F3:** *any atomic mutation that can change the result of an ordinary `episodes(user_id)` read must advance that user's `store_version` in the same atomic mutation* — which includes the visibility cutover and every recovery/abandonment transition that changes the visible representation. With that frozen, X-Q2 is discharged by the existing cache mechanism and `@store_mutator` stays what it is: an audit marker. `0004` owns the general derived-view-invalidation contract; this spec only asserts the cutover is a change to recall's inputs. | resolved | dev | — |

---

## 11. Review closure — round 1 (2026-08-07)

Round-1 external review: **"architecture direction approved; v2 deferred on three
load-bearing design gaps plus five contract corrections."** The reviewer withdrew
its earlier round (the reviewer's guide reframed the boundary: `0010` is a design
spec, X1–X14 are the prospective implementation acceptance surface not pre-existing
tests, `0007`/`0013` prerequisites are accepted, and §4c snapshot-vs-generation is a
backend choice beneath one X9 contract). The central fenced-state-machine direction
was approved and carries forward unchanged. v2 closes all eight items at root; each
was reproduced against the source or spec text first.

### Blocking findings

| # | finding | root fix in v2 |
|---|---|---|
| **F1** | recovery is required (X-Q1) but the Store surface exposed no way to **discover** unfinished operations — after `GENERATING→OUTPUTS_DURABLE` the inputs are hidden, so a cold-candidate claim can never rediscover them | Added `pending_consolidations(user_id) -> list[Op]` — a first-class Store **read** returning every non-`FINALIZED` operation (§4b). Recovery reads it, applies the transition table, counts for `introspect()`. New invariant **X13**. |
| **F2** | recovery prose required a **persisted expected-output set** that neither the operation record nor any primitive could represent — an unresolved Design A/B "or" of exactly the kind `0010` exists to forbid | Chose **Design A**: the atomic transition is the sole completeness proof; all pre-transition outputs are provisional/invisible and deleted wholesale on crash. Deleted the persisted-output-set claim; the operation record carries no output plan (§4a, §4b-ii). Design B recorded as considered-and-rejected. |
| **F3** | X-Q2 attributed `store_version` advancement to `@store_mutator`, but the decorator is only an audit marker (`__store_mutator__ = True`); `_bump()` is explicit, and `set_wiki` is a mutator that deliberately does not bump. The `GENERATING→OUTPUTS_DURABLE` cutover changes no episode row, so the cached wiki could read falsely fresh | Froze the real invariant (**F3 invariant**, below); corrected X-Q2 to rely on it, not the decorator. New invariant **X14**. |

> **F3 frozen invariant.** *Any atomic mutation that can change the result of an
> ordinary `episodes(user_id)` read MUST advance that user's `store_version` in the
> same atomic mutation.* This unambiguously includes the `GENERATING →
> OUTPUTS_DURABLE` visibility cutover (which changes no episode row but changes what
> `episodes()` returns) and every recovery/abandonment transition that changes the
> visible representation. `@store_mutator` remains an audit-manifest marker only.

### Contract corrections

| # | correction | v2 |
|---|---|---|
| **A** | `date_start`/`date_end` were normative persisted data but absent from §2 | Added both to the §2 field-contract table with `date_start <= date_end`, degenerate-range single-date rendering, and `date`-compatibility/sort semantics — in the schema/migration contract, not rendering prose. |
| **B** | the shared `FORMAT_VERSION 2→3` with still-draft `0009` had no implementation-order rule | §9 freezes the same-version-**iff**-co-implemented rule; ship-first owns v3, the sibling takes v4, a released version is never redefined in place. Does not make `0009` a prerequisite. |
| **C** | the claim primitive had two names (`create_or_takeover_consolidation`/`claim_episode_batch`) and the claim field two (`claimed_by`/`consolidated_into`) | One name each, everywhere; synonyms retired (§4b note, X4). |
| **D** | "outputs absent" in `GENERATING` conflated physical absence with read-invisibility, contradicting "partial outputs deleted by `operation_id`" | §4b-ii and §4c now say *physical rows: zero or more provisional; ordinary-read visibility: none*. |
| **E** | X2's "crash mid-delete → complete the remainder" conflicted with the single all-or-nothing `delete_claimed_inputs_if_current` primitive and §8's per-call-atomicity assumption | X2 reframed around **crash after the batch-delete commits, before `FINALIZED`**: idempotent re-delete + finalise; no durable partial-delete state exists. |

The §4c reviewer question (does leaving snapshot-vs-generation to the backend leave
X9 unimplemented?) was answered **no** and a conformance clause added: a backend
providing neither mechanism is non-conforming; X9 is required of every backend
implementing this schema. That is not the rejected `0002` fork.

---

## 12. Review closure — round 2 (2026-08-07)

Round-2 external review: **"fenced-state-machine architecture remains approved; v3
deferred on four load-bearing design gaps plus three contract corrections."** The
reviewer confirmed v2's round-1 fixes hold (recovery-discovery, Design A, the
`store_version` invariant independent of `@store_mutator`, X9 as one conformance
rule, atomic batch-delete, conditional `0009` coordination) and endorsed the Design-A
judgment. The four new gaps are all at the **edges** of the state machine, not its
centre; none requires redesigning the fenced/leased direction or replacing Design A.
Each was reproduced against source or spec text first.

### Blocking findings

| # | finding | root fix in v3 |
|---|---|---|
| **F1** | the spec used **`FORMAT_VERSION 2→3`** for what is really an on-disk shape change — but `0007` §8 holds `FORMAT_VERSION` (export wire) and `SCHEMA_VERSION` (`PRAGMA user_version`) are independent namespaces, and `0013` migrates the latter. `0010` changes **both** (new columns *and* new export fields) | §9a splits them: a table mapping each counter to its source and migrator; `0013` prose refers to `SCHEMA_VERSION`; the conditional-`0009`-share rule now applies **per-namespace**; §2 lists both bumps. Verified: `schema_version.py:167 SCHEMA_VERSION=2`, `portability.py:36 FORMAT_VERSION=2`. |
| **F2** | takeover could admit a **new fence before the old generation was proven clean** — provisional rows carry only `operation_id` (no per-row fence), so old- and new-generation rows tagged `op-1` are indistinguishable to a delete-by-`operation_id` | §4b-iii freezes `abandon_consolidation_if_current` as one atomic primitive whose success **means cleanup-complete** (no provisional row, no claim survives), and `create_or_takeover_consolidation` may advance the fence **only from that clean `ABANDONED` state**. Preserves Design A minimalism (no output-generation field). Invariant X15. |
| **F3** | X3 promised idempotency-by-lineage but no **post-`FINALIZED`** rule existed: a response-lost finalized generation's own visible outputs (compat `date == date_start`, still old) are immediately re-eligible cold candidates → summary-of-summary | §4e freezes: **an episode carrying `lineage`/`operation_id` is never a consolidation candidate**, so finalized outputs are permanently ineligible and a replay is a no-op. Recursive compaction explicitly out of scope (with the full list of what it *would* have to freeze). Invariants X3'/X16. |
| **F4** | portable **export can orphan a live claim**: `export_memory` serializes visible `CLAIMED`/`GENERATING` inputs (carrying `claimed_by`) but **not** `ConsolidationOp` records, so import yields an episode claimed by a non-existent operation — X4 then makes it ineligible forever | §4f freezes export as a **logical quiescent snapshot**: a live consolidation is settled (finalized/abandoned) or export **refuses**; no exported episode carries a dangling `claimed_by`. The `FORMAT_VERSION` acceptance test covers export/import from every state. Invariant X17. |

### Contract corrections

| # | correction | v3 |
|---|---|---|
| **A** | §2 said `date := date_start` is always persisted while §4d-ii said a single `date` is **written** only for a degenerate range — a contradiction | §4d-ii now says `date` is **always persisted as `date_start`**; only the **rendering** is conditional (single date iff `date_start == date_end`, else a range). "written" → "rendered". |
| **B** | `ConsolidationOp` carried no `user_id`, though recovery is queried per-user and `forget_user()` must erase all user-scoped state | §4a adds `user_id` to the record; every `claimed_id` must belong to it; `forget_user()` erases the operation/claim/provisional-output state atomically. §2 row updated. |
| **C** | X1 still described the **pre-Design-A** "duplicates resolved by lineage" mechanism | §2c X1 rewritten to the Design-A rule: pre-transition outputs are hidden and deleted wholesale, inputs never hidden — there is no visible coexistence to reconcile. |

**Not changed:** the approved fenced/leased state-machine direction and Design A both
carry forward. The reviewer's own acceptance bar for v3 is items F1–F4 + A–C above;
all seven are closed here.
