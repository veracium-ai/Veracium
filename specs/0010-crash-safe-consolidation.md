# Feature spec: crash-safe consolidation

Spec-Status: accepted
Spec-Requires: 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **ACCEPTED (v8)** — set `accepted` 2026-08-07 by dev on a **finite acceptance
> boundary (§18)**. Rounds 1–7 of external review each **affirmed the architecture** —
> the fenced/leased state machine, Design A (the transition is the sole completeness
> proof), one-level consolidation, read-only export, and the single-Episode-space + X21
> per-call reservation strategy — and never reopened it. **The acceptance criterion is
> "the architecture + the X1–X23 invariant surface are frozen and demonstrable" (they
> are) — NOT "the external review stops finding adjacent interface seams,"** which has
> no natural terminal on a detailed model (rounds 3–7 increasingly found seams *in the
> prior round's fix* — the 0013 executable-model pattern). The design: a fenced operation
> record + all-or-nothing batch-claim primitives + recovery-discovery + quiescent-snapshot
> reads + the full transition table (§4). Split from `0002` §7e. **What `accepted`
> authorises:** implementation of this design, validated by the X1–X23 tests. Any further
> review edge is an **implementation obligation** (§18), not a spec blocker — in
> particular the recurring store-wide **identity/fence-hygiene** class (X21 ≡ `0009` H14)
> is a Store-contract concern to settle once at implementation, not re-derived per spec.
> **Both `Spec-Requires:` prerequisites (`0007`, `0013`) are accepted AND implemented**
> (§9), so the dependency gate is satisfied. See §§11–17 (round closures) and §18.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v8 |
| **Status** | *see `Spec-Status:` — canonical.* Owns the contract stated in `0002` §7e. |
| **Internal reviewers** | research — pending |
| **External review** | complete — 7 rounds, architecture affirmed each time |
| **Decision + date** | **accepted 2026-08-07** (dev, on the finite §18 acceptance boundary — architecture + X1–X23 frozen; further edges are implementation obligations) |
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
| **consolidation operation record** | **NEW** | `user_id · operation_id · fence · state · owner · lease_duration · lease_expires_at · claimed_ids` (§4a) — **`user_id`** is on the record (round-2 Correction B): recovery is queried per-user, every `claimed_id` belongs to it, `forget_user()` erases it. **`lease_duration`** is persisted (round-4 F1; **round-5 Correction A** — it must be in this on-disk/migration carrier so renewal's `store_now + lease_duration` survives restart). **No expected-output field** — Design A makes the transition the completeness proof (§4b-ii, §11-F2). |
| **`SCHEMA_VERSION`** (on-disk) | **2 → 3** | the **on-disk store shape** (`PRAGMA user_version`) — the new `Episode` fields + the operation-record table land here. **This is what `0013` migrates.** Conditionally shared with `0009`; §9. |
| **`FORMAT_VERSION`** (export wire) | **2 → 3** | the **portable export/import representation** — the new `Episode` fields change what a `.jsonl` export carries, so an older importer must refuse rather than silently drop them. **`0007` §8 holds this is a namespace independent of `SCHEMA_VERSION`;** they are coincidentally both `2` today. Conditionally shared with `0009`; §9. |

## 2c. Untrusted inputs — REQUIRED, blocking

**No caller-supplied value reaches this operation** — `consolidate()` takes a
`user_id` and reads its own inputs from the store. The uncontrolled input here
is **the machine**, which is unusual for this spec family and worth naming
rather than leaving the section empty.

| uncontrolled input | failure | invariant |
|---|---|---|
| **crash while `GENERATING`, before the visibility transition** | provisional (hidden) output rows exist; inputs still visible | **X1** — under Design A the transition is the sole completeness proof: recovery deletes **every provisional OUTPUT row for `operation_id`** and **clears the claim fields on the INPUT rows** (never "all rows" — inputs carry `operation_id` too; §4b-ii/Correction A); the inputs simply remain visible, so there is no coexistence to reconcile and no blind delete of inputs |
| **crash after the batch-delete commits, before `FINALIZED`** | inputs gone, output present, op not finalised | **X2** — the delete is one **all-or-nothing** primitive (§4b), so there is no durable "some inputs gone"; recovery re-issues the idempotent delete and finalises |
| **crash before any write** | nothing changed | no-op, by construction |
| **concurrent `maintain()`** | two consolidations of one set | **X4** — `Episode.claimed_by` (the operation) claims an input; a second run skips claimed inputs |
| **response lost after `FINALIZED`** | outputs visible, op excluded from `pending_consolidations`, outputs' compat `date` still old → re-eligible as cold candidates | **X3** — **a consolidated output (an episode with non-empty `lineage`) is never itself a consolidation candidate** (§4e), so a re-run cannot reconsolidate its own outputs into a summary-of-summary; a *released input* stays eligible |

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
  user_id          the tenant — every claimed_id belongs to it (Correction B, round 2)
  operation_id     opaque, unique
  fence            monotonic from the store
  state            CLAIMED | GENERATING | OUTPUTS_DURABLE | FINALIZED | ABANDONED
  owner            worker identity (COOPERATIVE — §4a-ii; not an auth capability)
  lease_duration   the bounded duration renewal re-adds (persisted — round-4 finding 1)
  lease_expires_at when the claim may be preempted = (store_now at last set) + lease_duration
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

### 4a-ii. The lease protocol, the ownership model, and cleanup-before-fence takeover (round 3, finding 1; corrected round 4)

The transition table says `CLAIMED`/`GENERATING` may be acted on **only by the owner
with a live lease**, and the lease uses the store's clock. Two things must be frozen:
where renewal's duration comes from, and what `owner` actually guarantees.

> **Frozen: lease protocol (round-4 finding 1 — the duration is a durable carrier).**
> - **`lease_duration` is an exact bounded duration**, never an absolute
>   worker-computed deadline, and **it is persisted on the `ConsolidationOp`** (§4a).
>   On creation/takeover the **store** sets `lease_expires_at = store_now +
>   lease_duration`. Bounds: `0 < lease_duration <= LEASE_MAX` (one library constant);
>   outside them is rejected.
> - **`renew_consolidation_lease(op_id, fence, owner)`** reads the op's **persisted
>   `lease_duration`** and sets `lease_expires_at = store_now + lease_duration`. It
>   succeeds only for the exact current `(fence, owner)` under an **unexpired** lease;
>   it cannot resurrect an expired lease (that path is takeover). The duration is thus
>   neither re-passed nor guessed — the renewal equation has one durable source.

> **Frozen: the ownership model is COOPERATIVE identity, not an auth capability
> (round-4 finding 1b).** `owner` is a field on `ConsolidationOp` and
> `pending_consolidations` returns the record, so a caller *can* read and resubmit the
> recorded `owner`. **This is acceptable and deliberate:** consolidation workers are the
> host's own trusted maintenance processes — this is a **durability/crash-safety**
> protocol, not an injection-resistance boundary (contrast the trust-bearing fields
> elsewhere in the corpus, which the *host* must not be able to set). So:
> - `owner` is a **concurrency/diagnostic identity**; correctness assumes each worker
>   passes **its own** identity. It prevents a *well-behaved* worker from acting on an
>   op it does not own, and combined with the lease it prevents preempting a live
>   worker. It is **not** claimed to stop a hostile process that forges another's
>   identity — that is out of this spec's threat model.
> - **X7/X10 are scoped to that assumption** (no absolute "a hostile non-owner
>   mechanically cannot"). If true non-owner exclusion is ever required, it is a
>   separate change: creation returns an opaque owner capability that
>   `pending_consolidations` does **not** expose. Not needed for trusted maintenance
>   workers, and not introduced here.
>
> **Enforcement is by phase — before vs after the `OUTPUTS_DURABLE` cutover:**
> - **Pre-cutover owner actions** — `write_consolidation_output_if_current` and the
>   owner-driven `transition…` (`CLAIMED→GENERATING`, `GENERATING→OUTPUTS_DURABLE`) —
>   succeed only when the caller passes the recorded `owner` AND the lease is unexpired.
> - **`abandon_consolidation_if_current(op_id, fence)` is ownerless but succeeds ONLY
>   on an EXPIRED lease** (→ clean `ABANDONED`, §4b-iii): it will not abandon a
>   live-lease op, so a well-behaved worker cannot roll back a peer that is still
>   heartbeating (X7). The sole pre-cutover recovery action.
> - **Post-cutover roll-forward is recovery-safe and ownerless.** At `OUTPUTS_DURABLE`
>   the outputs are committed, so any worker may `transition…(→FINALIZED)` and
>   `delete_claimed_inputs…` — validated by `(op_id, fence)` + state. Same calls the
>   happy path makes; no separate recovery API.

> **Takeover selection — a new fence issues ONLY from cleanup-complete `ABANDONED`
> (round 4, finding 2 — this corrects a v4 bug).** v4 let takeover directly revive a
> *clean `ABANDONED`* **or an expired-lease** op, claiming §4b-iii made it "already
> clean." That is false for an expired **`GENERATING`** op, which can still own
> provisional output rows — reviving it under a new fence recreates the exact
> old/new-generation ambiguity X15 exists to prevent. Frozen instead, atomically:
> ```
> any requested id belongs to a LIVE-lease op        → return None (contended; X7)
> any requested id belongs to an EXPIRED pre-cutover  → ABANDON that op first
>   op (CLAIMED or GENERATING), or intersects one        (§4b-iii cleanup: delete its
>   without exactly matching                              provisional outputs, clear its
>                                                         input claims), THEN re-evaluate
> a CLEAN ABANDONED op covers exactly these ids       → revive it under a new fence
> otherwise                                           → create a new operation
> ```
> So a new fence is issued **only** from cleanup-complete `ABANDONED` (X15 intact), and
> the intersecting-but-not-equal case (an expired op owns `{A,B}`, the request is
> `{A,B,C}`) is handled by abandoning the expired op first so its inputs are clean
> before the claim proceeds. `consolidate()` runs recovery first, but a lease can expire
> *between* that pass and this claim, so the claim primitive itself carries this race
> rule. This is how a quiescent `ABANDONED` op is revived without
> `pending_consolidations` returning it.
>
> The pre-clean-abandon and the claim are each **individually atomic**; they need not be
> one transaction, because a crash **between** them leaves a safe state — the expired op
> is clean-`ABANDONED` (its provisional outputs gone, its inputs free) and no new claim
> exists, so the next `consolidate()` simply re-requests the now-clean inputs. X11's
> all-or-nothing applies to the **claim** step; the preceding abandon is recovery
> cleanup, not a partial claim.
>
> **`create_or_takeover_consolidation` is therefore a declared MULTI-PHASE operation
> (round 5, Correction C).** The abandon→claim boundary is a real crash seam, but it sits
> *inside* one nominal Store call, where §8's per-call-atomicity assumption and X5's
> Store-call-boundary crash sweep would not otherwise reach it. So the seam is made
> explicit: **X5's fault injection includes the internal abandon→claim boundary** (not
> only the outer Store-call boundaries), and this method is documented as multi-phase so
> the executable acceptance surface actually exercises the crash-between-safe argument
> above rather than assuming it.

### 4b. An explicit atomic batch-claim primitive

**Finding 9: "one conditional update" does not give all-or-nothing.** An
ordinary `UPDATE ... WHERE` claims the eligible subset and reports a smaller row
count — **a partial claim, the exact state the design called impossible.**

> **New `Store` methods.** The mutators are marked `@store_mutator`;
> `pending_consolidations` is a **read** and is not:
> ```
> create_or_takeover_consolidation(user_id, ids, owner, lease_duration) -> Op | None
> renew_consolidation_lease(operation_id, fence, owner)              -> bool
> write_consolidation_output_if_current(op_id, fence, owner, draft)  -> bool   # owner-only; draft = ConsolidationOutputDraft (no id/op fields); store mints a fresh id, binds op fields, INSERT-only (X22, round 6/7)
> transition_consolidation_if_current(op_id, fence, owner, to_state) -> bool   # owner pre-cutover; →OUTPUTS_DURABLE REFUSES with zero bound outputs (X22); →FINALIZED ownerless, REFUSES unless every claimed input is deleted (X20)
> delete_claimed_inputs_if_current(op_id, fence)                    -> bool   # post-cutover: recovery-safe, ownerless
> abandon_consolidation_if_current(op_id, fence)                     -> bool   # expired-lease only (§4a-ii)
> pending_consolidations(user_id) -> list[Op]                       -> READ — recovery-discovery
> quiescent_episode_snapshot(user_id) -> list[Episode] | NonQuiescent  # READ — atomic export snapshot (X17, round 5)
> ```
> **Every *post-creation* fenced mutator takes `(operation_id, fence)`** (Correction C
> fixes the earlier "every mutator" — creation cannot take a not-yet-minted id/fence).
> Enforcement is **by phase** (§4a-ii): pre-cutover owner actions additionally require
> the recorded `owner` under an unexpired lease; `abandon` succeeds only on an expired
> lease; post-cutover roll-forward is recovery-safe and ownerless. Each backend
> implements the atomicity; the interface states the contract.

> **`FINALIZED` is unreachable until the inputs are gone (round 5, finding 1).** The
> roll-forward order is `OUTPUTS_DURABLE → delete inputs → FINALIZED`, and X2 models the
> recoverable window (crash after the delete commits, before `FINALIZED`). But `delete`
> and `transition` are separate primitives, so a bare `transition(…, FINALIZED)` with
> inputs still present would produce a **permanently inconsistent** terminal state —
> `FINALIZED` (whose contract says inputs are deleted), excluded from
> `pending_consolidations`, with **stranded hidden input rows no recovery revisits**.
> (Not the original no-replacement loss — the outputs exist — but a state the table's own
> definition forbids.) Frozen mechanically: **`transition_consolidation_if_current(…,
> FINALIZED)` returns `False` unless every claimed input of the operation is already
> deleted.** The Store makes the invalid state unrepresentable — lifecycle *and* recovery
> call the same primitive, so ordering must not be left to caller discipline. Invariant
> **X20**.

**Recovery-discovery is a first-class Store read (finding 1, round 1; set corrected
round 3).** X-Q1 requires `consolidate()` to run recovery at its own start and surface
the count in `introspect()` — but the fenced mutators above cannot *find* the
operations to recover. After a `GENERATING → OUTPUTS_DURABLE` crash the inputs are
hidden from ordinary reads, so a cold-candidate `create_or_takeover_consolidation` can
never stumble onto them. **`pending_consolidations(user_id)` returns exactly the
recovery-pending operations — `{CLAIMED, GENERATING, OUTPUTS_DURABLE}`, NOT `FINALIZED`
and NOT `ABANDONED`** (round-3 finding 2: a clean `ABANDONED` op is **quiescent /
cleanup-complete** — not terminal, since takeover may still revive it under a new
fence, but **not recovery-pending** — so returning it would leave already-recovered
work perpetually "pending" and never let the recovery count fall to zero). Recovery
reads it, applies the §4b-ii transition table to each, and counts them. A quiescent
`ABANDONED` op is durable history, found by **takeover** through its own internal
lookup (§4a-ii), not by this recovery read.

> **The `introspect()` count is named for what it means (round 4, Correction A).**
> `pending_consolidations` deliberately includes **live** pre-cutover ops, which
> `abandon` will *not* touch while their lease is live — so the list size is not "work
> recovered." Freeze two distinct fields: **`consolidation_pending`** = count of
> **recovery-pending** ops observed (`{CLAIMED, GENERATING, OUTPUTS_DURABLE}` — round-5
> Correction B: "non-terminal" was the wrong label, since quiescent `ABANDONED` is
> non-terminal yet NOT pending), and **`consolidation_recovered`** = count it actually
> rolled forward or abandoned this pass. A live op counts toward *pending*, never
> *recovered*. Report both (or, if one is surfaced, name it exactly).

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
| `GENERATING` | owner with live lease | **visible** | **zero or more provisional rows** / hidden | `OUTPUTS_DURABLE` · `ABANDONED` | lease expired → `ABANDONED`; **delete the provisional OUTPUT rows for `operation_id`, and CLEAR `claimed_by`/`operation_id` on the claimed INPUT rows** (Design A; never "all rows" — inputs carry `operation_id` too, §4b-iii/Correction A) | `operation_id` |
| `OUTPUTS_DURABLE` | owner, or recovery | hidden | present / **visible** | `FINALIZED` **(only after inputs deleted — X20)** | **roll forward, never back** — delete claimed inputs, then transition; `→FINALIZED` refuses while any input remains (X20) | `operation_id` |
| `FINALIZED` | — | deleted | present / **visible** | — | none needed | — |
| `ABANDONED` | any worker may take over | **visible** | **none remain** / hidden | `CLAIMED` (new fence) | already clean — `ABANDONED` is only observable *after* cleanup (§4b-iii) | `operation_id` |

**`OUTPUTS_DURABLE` is the point of no return, and Design A makes the atomic
transition itself the sole completeness proof (finding 2).** All output rows
written while `GENERATING` are **provisional and invisible**. If the process
crashes at any point before the atomic `GENERATING → OUTPUTS_DURABLE` transition,
recovery deletes **every provisional OUTPUT row for `operation_id`** — *even if all
intended outputs happened to be written* — and **clears `claimed_by`/`operation_id`
on the claimed INPUT rows** (the inputs are never deleted here; they carry
`operation_id` too, so "delete all rows tagged `operation_id`" would destroy them —
Correction A, round 3). The inputs, which never stopped being visible, simply become
clean cold candidates again. Recovery therefore never has to distinguish "complete
but not transitioned" from "partial": before the transition, nothing counts; after
it, everything does. **No expected-output set is persisted** — the operation record
carries none (§4a), and there is no primitive to establish one, because Design A
needs neither. (Design B — recognising a complete pre-transition generation from a
persisted output plan — was considered and rejected in round 1: it adds
`expected_output_ids`/`_count` plus a fenced primitive for a strictly weaker
guarantee, against this spec's "cannot be got wrong by accident" ethos.)

> **The cutover must prove a correctly-bound replacement EXISTS (round 6, finding 2).**
> Design A makes the transition the sole *completeness* proof, but v6 left it able to
> prove a *false* statement: `write` accepted a fully-formed `Episode` with no binding
> check, and `GENERATING → OUTPUTS_DURABLE` succeeded with **zero** outputs — after
> which `delete inputs → FINALIZED` (X20 satisfied, inputs gone) yields
> `inputs=gone, outputs=none, FINALIZED`, losing every input with no replacement (the
> spec's top-level claim + X1, violated). This needs no expected-output plan — only a
> small **positive** proof:
> - **`write_consolidation_output_if_current` takes a `ConsolidationOutputDraft`** that
>   carries only worker-owned CONTENT and **no persisted Episode `id`, no `user_id`, no
>   `operation_id`, no `claimed_by`, no `lineage`** (round 7, finding 2 — the exact shape
>   `0009`'s `OutcomeJudgmentDraft` uses):
>   ```
>   ConsolidationOutputDraft:
>       summary / text          # the LLM's consolidation
>       date_start · date_end   # min/max of the claimed set (Store-validated, §4d-ii)
>       (NO id · NO user_id · NO operation_id · NO claimed_by · NO lineage)
>   ```
>   The store **mints a fresh Episode `id`**, BINDS the operational fields to the fenced
>   op (`user_id == op.user_id`, `operation_id == op_id`, `claimed_by` absent,
>   **`lineage == op.claimed_ids`**, valid output shape X18), and **INSERTs a new row —
>   never replaces**; a collision on the minted id is a store error, not a replace. So a
>   misbound write (`operation_id = "op-X"`) is structurally impossible, **and** a
>   caller-forged `id = "ep-existing"` can no longer overwrite unrelated history through
>   a primary-key collision (the round-6 fix removed forged *operational fields*; this
>   removes the forged *row identity* one field over).
> - **`GENERATING → OUTPUTS_DURABLE` REFUSES unless ≥1 correctly-bound provisional
>   output exists** for the operation. The transition still proves only "generation is
>   complete"; it can no longer assert "the replacement is durable" when none exists.
> Invariant **X22**. (Consolidation analogue of `0009`'s `OutcomeJudgmentDraft` — store
> owns identity and operational fields, structurally, not by convention.)

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
> `operation_id` is deleted, every input claim is released — clearing that input's
> `claimed_by` AND `operation_id` so it is clean, eligible history again (§4e) — and
> only then is the operation observably `ABANDONED`.** Therefore:
> ```
> ABANDONED  ⇒  no provisional output row for that operation remains
>            ⇒  no input remains claimed by it (claimed_by / operation_id cleared)
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

> **Frozen (candidate eligibility).** **An episode with a non-empty `lineage` — i.e.
> a consolidation OUTPUT — is NEVER selected as a consolidation candidate.** A
> finalized generation's own outputs are therefore permanently ineligible for
> reconsolidation, so a response-lost retry finds no cold candidates and is a no-op.
> Invariant **X3'/X16**.
>
> **The discriminator is `lineage`, NOT `operation_id`.** An *input* carries
> `claimed_by` and `operation_id` while it is claimed (§2 — `operation_id` is set on a
> record the consolidation "produced **or claimed**"), and F2 returns a released input
> to eligibility. Keying exclusion on `operation_id` would strand every released input
> as a permanent non-candidate — the exact data-lifecycle failure this spec exists to
> prevent. Only a genuine output carries `lineage`, so `lineage` is the one honest mark
> of "this is a summary, not raw history." **Correspondingly, releasing a claim
> (abandonment §4b-iii, or ordinary release after `FINALIZED`) clears the input's
> `claimed_by` and `operation_id`**, so a released input is clean history again and no
> **input** is left pointing at an operation that no longer exists (this is what makes
> F4's "no dangling `claimed_by`" hold). A finalized **output** is different — it keeps
> `operation_id` as historical provenance by design (X19); that is not a dangling claim.

> **Limit made explicit.** This **forbids recursive compaction** (summarising
> summaries) in v1 — a deliberate trade for mechanical retry-idempotency without a
> caller idempotency token (which `consolidate()` does not take). If recursive
> compaction is ever wanted it needs its own spec: lineage must be **flattened** into
> the new output, a new operation must distinguish legitimate later compaction from
> replay **from durable state** (not caller intent), and — if lineage equality is the
> replay key — lineage needs **canonical set semantics** (order- and
> duplicate-independent) so the absorbed-set identity is stable. None of that is in
> v1; the flat "outputs are not candidates" rule is.

> **Because `lineage` now permanently controls eligibility, its record shape is
> frozen (round 3, Correction B).** The consolidation fields are not independently
> optional — an imported or inserted episode must match **exactly one** of three
> mutually exclusive shapes, validated on store insert **and** on import (§4f), else it
> is refused (a malformed `lineage = [...]` with everything else `None` must not be
> able to acquire the permanent "never consolidate" status):
> ```
> plain episode      : lineage absent · claimed_by absent · operation_id absent
>                      · date_start/date_end absent
> claimed input      : lineage absent · claimed_by == operation_id (the claiming op)
>                      · date_start/date_end absent
> consolidated output: lineage NON-EMPTY · claimed_by absent · operation_id present
>                      · date_start present · date_end present · date == date_start
> ```
> Invariant **X18**. This adds no recursive-compaction semantics; it only makes the v3
> discriminator structurally trustworthy.

> **PORTABLE shapes ≠ storage shapes — a claimed input is never importable (round 5,
> finding 3).** `FORMAT_VERSION` is a *parser* contract, not a promise the file came from
> a conforming exporter (files can be stale, hand-edited, or malformed). Since a
> `ConsolidationOp` is deliberately **non-portable**, a shape-valid **claimed input**
> (`claimed_by == operation_id`, no op in the file) imported as-is is exactly the round-2
> **durable orphan** — claimed, no operation, no recovery, skipped forever. So import
> validates against a **narrower** set than storage:
> ```
> import: plain episode          → allow
>         settled output (X19)   → allow (historical, remapped per finding 4)
>         claimed input          → ALWAYS REFUSE (its live op is non-portable)
>         provisional output     → n/a (invisible; never exported)
> ```
> Symmetrically, **generic `Store.add_episode()` must not fabricate live operational
> state**: a *claimed input* is created only by `create_or_takeover_consolidation`, a
> *provisional output* only by `write_consolidation_output_if_current` — never by the
> ordinary insert path. Invariant **X18** (import + insert both).

> **The fence also guards EXISTING operational rows against the generic mutators
> (round 6, finding 1).** §4a claims "every write, visibility change and delete
> compares-and-sets on `(operation_id, fence)`" — but that only held for the *fenced
> primitives*; the ordinary `add_episode` (`INSERT OR REPLACE`) and `delete_episode`
> (unconditional `DELETE`) take no fence, so a plain `delete_episode("ep-A")` on a
> claimed input **deletes it before any replacement is durable** (violating X1), and a
> plain `add_episode(Episode(id="ep-A", plain-shape))` **strips its claim fields**
> without the fence — splitting the state machine's two representations. X18 caught
> *creating* operational state, not mutating/deleting an *already-operational* row.
> Frozen: **X21 is ID-RESERVATION based, not existing-row based (round 7, finding 1).**
> While an operation is in `{CLAIMED, GENERATING, OUTPUTS_DURABLE}`, **every id in
> `op.claimed_ids` is RESERVED** — and the reservation **survives the physical deletion**
> of the row (the `OUTPUTS_DURABLE → delete inputs → FINALIZED` interval, where the input
> row no longer exists but the op still reserves the id):
> ```
> generic add_episode(id ∈ reserved_ids)     → REFUSE
> generic delete_episode(id ∈ reserved_ids)  → REFUSE (except the fenced batch-delete)
> ```
> The reservation lifts only when the operation reaches `FINALIZED` or clean `ABANDONED`.
> (An existing-row-only check would miss the seam: after the fenced delete removes `ep-A`
> but before `FINALIZED`, a generic `add_episode(Episode(id="ep-A", plain))` has no live
> row to inspect, yet `ep-A` is still one of the exact inputs whose deletion defines the
> roll-forward state — resurrecting it perturbs a live operation.) `forget_user()` remains
> the deliberate exception (it atomically erases the whole user's state machine). This is
> not general multi-process coordination; it is the exact fence §4a already claims every
> operational write/delete obeys, now enforced on the whole store surface as a small
> indexed reservation check. Invariant **X21**.

> **A finalized output's `operation_id` is historical provenance, not a live reference
> (round 4, finding 4).** A consolidated output requires `operation_id` (X18), but
> export deliberately does not carry `ConsolidationOp` records — so after import the
> output's `operation_id` names an operation that does not exist locally, and X9 (which
> reads the episode *and* its operation record in one snapshot) would have no state to
> resolve. Frozen: **once an operation reaches `FINALIZED`, its outputs' `operation_id`
> is an opaque historical producer id, not an operational pointer.** A `lineage`-bearing
> output is an **independently visible settled record**: it is always visible, and X9's
> episode-plus-operation-state lookup applies **only while a matching live/local
> operation row exists** (i.e., during the pre-`FINALIZED` lifecycle). So the portable
> format stays small (no operation records travel), imported outputs are visible with no
> synthesized op, and the runtime state-machine record is explicitly local/non-portable.
> (This is why §4e's "no episode points at an operation that no longer exists" is scoped
> to *claimed inputs*, whose claim fields are cleared — a finalized output's historical
> `operation_id` is allowed to outlive its op.) Invariant **X19**.

> **Imported historical `operation_id`s get a destination-local namespace (round 5,
> finding 4).** "Historical unless a same-named local op happens to exist" lets an
> *import file* (which controls the value) collide a historical producer id with a **live
> local** `operation_id` — after which the imported settled output and a live op's
> provisional output share the same row-level discriminator, and correctness would rest
> on collision improbability. Frozen: **on import, every historical consolidation
> `operation_id` is remapped to a fresh destination-local historical id**, preserving
> grouping (several outputs from one source operation get the **same** remapped id); and
> **live-operation allocation never reuses an id that appears as a historical output
> producer id.** So an imported output's `operation_id` can never rebind to a local live
> op. Invariant **X19** (extended). (This is the consolidation analogue of `0009`'s
> cross-user `supersedes_episode` remap — an imported reference must not resolve against
> unrelated local state.)

> **The historical namespace must be retry-STABLE and cover `lineage` too (round 6,
> finding 3).** v6's "fresh destination-local id" was under-specified in two ways:
> - **3a — stable across retries/partial imports.** If the remap mints a new id per
>   invocation, a partial-then-retried import (O1 already present, O2 not) splits one
>   source operation into two producer groups (`O1→hist-A`, `O2→hist-B`), breaking the
>   grouping X19 promises. So the **source→destination historical mapping is a
>   DETERMINISTIC destination-qualified function of the source id** (round-7 Correction C
>   — this is the frozen choice, so **no persisted map table is introduced**; a
>   persisted-map implementation would be additional user-scoped durable state that would
>   then have to be declared in the §2 on-disk schema and erased by `forget_user`, which
>   the deterministic function avoids entirely). "Fresh" means *not colliding with a live
>   local id*, **not** "new random value each run."
> - **3b — historical episode/`lineage` ids live in a PERMANENTLY DISJOINT namespace
>   (round 7, finding 3).** `lineage` is the whole claimed set (N9b's provenance record);
>   at finalization those input rows are **deleted** and their ids become historical. v6
>   protected these only *at import*, but the collision recurs **after local
>   finalization**: `output.lineage = ["ep-A", …]`, `ep-A` is deleted, then an ordinary
>   `add_episode(id="ep-A")` creates an unrelated live episode, and the provenance string
>   "this summary absorbed ep-A" now resolves to a different row. Frozen (design **A** —
>   structural, preferred over a tombstone set): **a `lineage` value is a
>   `HistoricalEpisodeId` in an encoding an ordinary live Episode id can NEVER inhabit.**
>   A deleted live id is **converted to a `HistoricalEpisodeId`** as part of output
>   creation (local finalization) **and** import; the live Episode-id allocator only ever
>   produces live-domain ids, so it can never collide with a historical one. This covers
>   locally-produced lineage, imported lineage, future ordinary Episode creation, later
>   import, and re-export/re-import. (Still provenance *integrity*, not a live eligibility
>   break — nothing dereferences `lineage` for a decision — but it keeps the N9b record
>   honest for the life of the store, not just at the mint instant.)

### 4f. Export is a read-only quiescent snapshot (round 2, finding 4; read-only round 4, finding 3)

Because v2 changes the export `FORMAT_VERSION`, the portable path is now
load-bearing. In `CLAIMED`/`GENERATING` the inputs stay ordinary-read **visible**
and persist `Episode.claimed_by`; `export_memory` serializes `store.episodes(user_id)`
but **not** the `ConsolidationOp` records. So exporting mid-generation yields an
episode with `claimed_by = op-1` and no `op-1` in the export; on import into a fresh
store there is **no operation to recover**, yet X4 makes the claimed episode
ineligible for a new claim — a **durable orphan** created purely by the portable path.

> **Frozen: export is READ-ONLY and refuses non-quiescent state, in ONE atomic
> observation (round 4, finding 3 — reversing v4's settle-then-export).** v3 froze a
> deterministic *settle-then-export* algorithm; round 4 showed two problems with making
> the public backup/portability call mutate memory: (i) it couples memory maintenance to
> a filesystem write — recover/finalize can succeed and then the *disk write fail*,
> leaving memory changed but no export produced; and (ii) with several ops (one expired,
> one live) a naive pass could abandon the expired op and *then* refuse on the live one,
> mutating before failing. Export is the action recommended **before** the irreversible
> `forget()`; it should not itself be maintenance.
> ```
> every op for the user is FINALIZED or ABANDONED (quiescent) → export
> ANY op is CLAIMED / GENERATING / OUTPUTS_DURABLE             → REFUSE, mutating nothing
> ```
> The caller runs `consolidate()`/`maintain()` (which owns recovery) first and retries.
> **The quiescence check and the exported-episode snapshot MUST be ONE atomic per-user
> observation, and that is a named Store read — `quiescent_episode_snapshot(user_id) ->
> list[Episode] | NonQuiescent` (round 5, finding 2).** v5 stated the atomic-observation
> *requirement* but no listed Store method could supply it — the same interface hole
> round 1 found for recovery discovery; `export_memory` doing `pending_consolidations()`
> then `episodes()` as two ordinary reads fails, because a claim can begin between them
> (and a SQLite-only transaction in `portability.py` would be the "backend trick" the
> corpus forbids). The primitive's linearization point atomically establishes (1) **no
> `CLAIMED`/`GENERATING`/`OUTPUTS_DURABLE` op exists** for the user and (2) the returned
> episode set is the snapshot from **that same** observation; it is **read-only and
> linearizable against `create_or_takeover_consolidation`**, returning `NonQuiescent`
> otherwise. X9 does **not** cover this — it makes one `episodes()` call
> representation-consistent, not a scan-plus-later-read one transaction. **Export never
> mutates and never bumps `store_version`.** Invariant **X17** tests this primitive
> directly *and* the public export path. (`0005` owns import's trust cap; this is the
> orthogonal *completeness* rule — a claim without its operation is not importable state.)

> **Import is no longer a field-for-field "exact round-trip" for consolidation
> reference ids (round 6, Correction C).** `portability` has described export/import as
> reproducing memory exactly, but X19 deliberately **remaps** a settled output's
> `operation_id` (and its `lineage` ids) to a destination-local historical namespace on
> import — required to close the live-id collision. So the portability contract is
> restated: **import preserves logical provenance grouping and memory content; local
> reference identifiers (consolidation `operation_id`, historical `lineage` ids) may be
> remapped.** The old "exact reproduction" wording, which the accepted X19 design makes
> false for this metadata, is retired.

`Store` is an interface with a Postgres implementation contemplated. Requiring
cross-backend atomic multi-statement transactions pushes a durability guarantee
into every future backend. **`create_or_takeover_consolidation` is one primitive
with a stated contract**, which is a smaller ask than "implement transactions".

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **X1** an input is never deleted before its summary is durable | `test_consolidation_writes_before_deleting` — a store wrapper that raises after the write | CI |
| **X2** the batch-delete is all-or-nothing; a crash **after** it commits but before `FINALIZED` is recovered by an **idempotent re-delete + finalise**, never a re-consolidation | `test_recovery_finalises_after_committed_delete` — there is no durable "some inputs deleted" state to complete | CI |
| **X13** recovery is **discoverable**: `pending_consolidations(user_id)` returns exactly the recovery-pending ops `{CLAIMED, GENERATING, OUTPUTS_DURABLE}` — **not `FINALIZED`, not quiescent `ABANDONED`**; `introspect()` reports `consolidation_pending` vs `consolidation_recovered` distinctly (Correction A) | `test_pending_returns_only_recovery_pending` — an `OUTPUTS_DURABLE` op is discovered; a quiescent `ABANDONED` op is **not**; a live op counts as pending, never recovered (round-3 finding 2 + round-4 Correction A) | CI |
| **X14** the `GENERATING → OUTPUTS_DURABLE` visibility cutover **advances `store_version`** (a content/representation change); a **claim does NOT** (it changes only operational metadata compile/recall never reads — §11-F3 scoped, round-7 Correction A) | `test_visibility_cutover_bumps_store_version` + `test_claim_does_not_bump_store_version` — a cached wiki must invalidate on the cutover but not on every in-flight claim (round-1 finding 3 + round-7 Correction A) | CI |
| **X3** retry is idempotent — **no summary-of-summary**, including after a response-lost `FINALIZED` | `test_consolidation_retry_is_idempotent` + `test_finalized_outputs_are_not_reconsolidated` — a re-run over a finalized generation's own visible outputs finds no candidates (§4e) | CI |
| **X15** `ABANDONED` is cleanup-complete, and a new fence issues **only** from clean `ABANDONED` — takeover of an **expired `GENERATING`** op abandons (cleans) it *first* | `test_takeover_requires_clean_abandoned` + `test_takeover_of_expired_generating_cleans_first` — an expired op holding a provisional row is abandoned before any new fence, so old/new-generation rows never coexist (round-2 finding 2 + round-4 finding 2 bug-fix) | CI |
| **X16** an episode with non-empty `lineage` (an output) is never a consolidation candidate; a *released input* (claim cleared) **is** eligible again | `test_consolidated_output_is_not_a_candidate` — 16→8 finalized, re-run selects none of the 8; `test_released_input_is_a_candidate_again` — an abandoned op's inputs re-consolidate (keying on `operation_id` would strand them) | CI |
| **X17** export is **read-only** via the atomic Store read `quiescent_episode_snapshot(user_id)`: it exports iff every op is quiescent, else **refuses mutating nothing**; the quiescence check + episode snapshot are **one linearizable observation** (against `create_or_takeover`); export never bumps `store_version`; `forget_user()` erases operation state | `test_quiescent_snapshot_is_linearizable_vs_a_new_claim` (the Store primitive directly — a claim starting mid-snapshot yields `NonQuiescent`, never a dangling `claimed_by`) + `test_export_refuses_nonquiescent_without_mutating` + `test_forget_user_erases_consolidation_ops` (round-4 finding 3 + round-5 finding 2) | CI |
| **X18** every stored/imported episode matches exactly one frozen shape; **import refuses a claimed-input shape** (its op is non-portable) and generic `add_episode` cannot fabricate claimed/provisional state | `test_malformed_lineage_shape_is_refused` + `test_import_refuses_claimed_input_shape` (a shape-valid claimed input with no op → refuse, not orphan) + `test_add_episode_cannot_create_operational_state` (round-3 Correction B + round-5 finding 3) | CI |
| **X19** a finalized output's `operation_id` is **historical**; the `operation_id` remap is a **deterministic** destination-local function (retry-stable, no persisted-map table); **`lineage` ids are `HistoricalEpisodeId`s in a namespace no live Episode id can inhabit**, so they never collide with a live episode — on import **or** after local finalization | `test_partial_then_retried_import_keeps_one_producer_group` (3a) + `test_live_add_episode_cannot_take_a_historical_lineage_id_after_finalization` (3b — local, not just import) + `test_imported_operation_id_cannot_collide_with_a_live_local_op` (round-4/5/6/7) | CI |
| **X20** `FINALIZED` is unreachable until every claimed input is deleted — `transition(…, FINALIZED)` refuses otherwise | `test_finalize_refuses_before_inputs_deleted` — a direct `OUTPUTS_DURABLE → FINALIZED` with inputs still present returns `False`, so no terminal op strands hidden inputs (round-5 finding 1) | CI |
| **X21** every id in a non-quiescent op's `claimed_ids` is **RESERVED**; generic `add_episode`/`delete_episode` on a reserved id **REFUSE** — the reservation **survives physical deletion** until `FINALIZED`/clean `ABANDONED` (`forget_user` + the fenced batch-delete excepted) | `test_generic_delete_of_a_claimed_input_is_refused` + `test_generic_replace_of_a_claimed_input_is_refused` + `test_generic_add_of_a_deleted_reserved_id_before_finalized_is_refused` (the OUTPUTS_DURABLE→FINALIZED seam — round-6 finding 1 + round-7 finding 1) | CI |
| **X22** the output write takes a `ConsolidationOutputDraft` with **no id/user_id/operation_id/claimed_by/lineage**; the store **mints a fresh id**, binds the op fields (`lineage == op.claimed_ids`), and **INSERTs — never replaces**; `GENERATING → OUTPUTS_DURABLE` **refuses with zero bound outputs** | `test_output_is_bound_to_the_fenced_operation` + `test_cutover_refuses_with_no_bound_output` + `test_output_write_cannot_replace_an_existing_episode` (a forged id can't overwrite unrelated history — round-6 finding 2 + round-7 finding 2) | CI |
| **X23** the output's derived fields are **Store-computed from `op.claimed_ids`, not taken from the draft/LLM**: minimum trust across the whole set (confidence/disclosure/third-party floor, N9b) and `date_start = min`, `date_end = max`, `date = date_start` | `test_output_trust_is_the_whole_set_minimum` + `test_output_date_range_is_store_derived_not_llm` — the new draft/write boundary must not move a derived-field guarantee from "computed from inputs" to "whatever the draft supplied" (round-7 Correction B) | CI |
| **X4** the claim is **atomic over the whole set** | `test_concurrent_consolidation_claims_all_or_nothing` — two workers, overlapping candidate sets; exactly one wins | CI |
| **X7** a claim is preemptible only on an **expired store-clock lease**, never on fence order alone; a live-lease op is not preempted. **Owner is COOPERATIVE identity** (§4a-ii) — a *well-behaved* worker passing its own identity cannot act on a peer's op; not an anti-forgery capability (out of threat model) | `test_a_live_lease_is_not_preempted` (heartbeating worker keeps its claim) + `test_a_worker_passing_its_own_identity_is_rejected_on_a_peer_op` (round-3 finding 1; scoped round-4 finding 1b) | CI |
| **X10** a worker that has lost its fence **or (cooperatively) passes an owner ≠ the recorded owner under a live lease** cannot write, flip visibility, or delete | `test_a_preempted_worker_cannot_write_or_delete` — the fence + cooperative-owner + lease check that makes preemption safe | CI |
| **X11** the **claim step** of `create_or_takeover_consolidation` is all-or-nothing; **the losing CLAIM step makes no partial new claim** (a preceding abandon is an intentional durable side effect, not a claim — round-6 Correction B) | `test_partial_claim_is_impossible` — contend for an overlapping set; the loser installs no partial new claim (it may have cleaned an expired intersecting op first) | CI |
| **X12** every output's lineage is the **whole claimed set** | `test_lineage_is_the_whole_batch` — **a post-hoc date partition would under-attribute third-party influence** | CI |
| **X8** every output carries the **whole** claimed set as lineage | `test_lineage_is_the_whole_batch` — **there is no input→output partition**; v5's exact-partition rule contradicted whole-batch lineage | CI |
| **X9** every read sees **exactly one** complete representation — never both, **never neither** (a finalized output whose op is absent/historical is simply visible, X19 — the episode+op snapshot only applies while a local op exists) | `test_every_read_sees_exactly_one_representation` — sweeps every state and every phase boundary | CI |
| **X5** no crash point loses an episode without a replacement | `test_no_crash_point_loses_data` — **parametrised over every store call in the operation** AND the **internal abandon→claim boundary** of the multi-phase `create_or_takeover_consolidation` (round-5 Correction C), failing at each in turn | CI |
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
  spec cannot help; it assumes **each ordinary store call is atomic** — with **one
  deliberate exception: `create_or_takeover_consolidation` is multi-phase** (phase 1
  abandon = atomic · crash seam · phase 2 claim = atomic; §4a-ii, round-6 Correction A),
  and that internal seam is a fault-injection point for X5. In particular
  `delete_claimed_inputs_if_current` is **one** atomic call, so a crash cannot leave a
  durable "some inputs deleted" state — which is why X2 is framed as crash-after-commit,
  not crash-mid-delete (round-2 Correction E).
- **Not multi-process safety in general.** X4 covers the claim race for
  consolidation; nothing else in `maintain()` is coordinated.
- **Not a rollback.** A completed consolidation is not undoable — the inputs are
  gone by design. **Only the crash window is made safe.**
- **Not recursive compaction.** A consolidated output is never itself a candidate
  (§4e), so summaries are never re-summarised in v1. This is the price of mechanical
  retry-idempotency without a caller idempotency token; recursive compaction would
  need its own spec (§4e states what it would have to freeze).
- **Not export of a live consolidation.** Export is **read-only** (§4f, round 4): it
  exports only a fully quiescent user (all ops `FINALIZED`/`ABANDONED`) and otherwise
  **refuses without mutating**; the caller runs `maintain()` (which owns recovery) and
  retries. The running state machine is not itself portable — `owner`/`lease` do not
  transfer to another store.

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

> **F3 frozen invariant (scoped to recall-relevant content, round 7 Correction A).**
> *Any atomic mutation that can change the **cache/recall-relevant visible memory
> content** returned by an ordinary `episodes(user_id)` read MUST advance that user's
> `store_version` in the same atomic mutation.* This includes the `GENERATING →
> OUTPUTS_DURABLE` visibility cutover (which changes **which representation** —
> inputs vs outputs — `episodes()` returns; X14) and every recovery/abandonment
> transition that changes the visible representation. **It explicitly EXCLUDES the
> operational metadata `claimed_by`/`operation_id`**: a successful claim sets those on
> still-visible inputs, but compile/recall never reads them, so a claim need not (and
> does not) bump `store_version` — avoiding a needless cache invalidation on every
> in-flight claim. (v6's literal wording — "any change to the `episodes()` result" —
> would have forced a bump on claim, which X14 never tested; this scoping reconciles the
> rule with the X14 surface.) `@store_mutator` remains an audit-manifest marker only.

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
| **F3** | X3 promised idempotency-by-lineage but no **post-`FINALIZED`** rule existed: a response-lost finalized generation's own visible outputs (compat `date == date_start`, still old) are immediately re-eligible cold candidates → summary-of-summary | §4e freezes: **an episode with non-empty `lineage` (an output) is never a consolidation candidate**, so finalized outputs are permanently ineligible and a replay is a no-op. **Keyed on `lineage`, not `operation_id`** — an input carries `operation_id` while claimed, and abandonment clears `claimed_by`/`operation_id` to return it to eligibility (§4b-iii), so keying on `operation_id` would strand released inputs. Recursive compaction explicitly out of scope. Invariants X3'/X16. |
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

---

## 13. Review closure — round 3 (2026-08-07)

Round-3 external review: **"fenced-state-machine architecture and Design A remain
approved; v4 deferred on three load-bearing design gaps plus three contract
corrections."** The reviewer confirmed all seven round-2 closures hold and approved the
v1 non-recursive-compaction decision. The new findings are protocol edges *exposed by*
those closures — none reopens the architecture, Design A, or the flat candidate rule.
**Correction A is a carrier the round-2 pre-send pass missed:** the `operation_id`
over-broad-delete fix reached §4e but the identical "delete ALL rows tagged
`operation_id`" wording survived in the transition table and Design-A prose. Each
finding was reproduced against the spec text first.

### Blocking findings

| # | finding | root fix in v4 |
|---|---|---|
| **F1** | "owner with a live lease" was unenforceable: the fenced mutators took `(op_id, fence)` but no `owner`, and `(op_id, fence)` is **not secret** (`pending_consolidations` hands the fence to every recovery worker); lease duration/renewal semantics were also unspecified | §4a-ii freezes the lease protocol (bounded store-clock **duration**, not an absolute deadline; renewal requires exact owner+fence+unexpired) and adds `owner` to the owner-only mutators, enforced as owner+fence+unexpired-lease; recovery mutators are deliberately ownerless once the lease expires. X7/X10 updated. |
| **F2** | a clean `ABANDONED` op stayed "pending" forever — `pending_consolidations` returned "every non-`FINALIZED`", so `introspect()`'s recovery count never fell to zero and X13 broke | §4b redefines the read as exactly `{CLAIMED, GENERATING, OUTPUTS_DURABLE}`; `ABANDONED` is terminal history, found only by takeover's own claim-set lookup (§4a-ii). X13 updated. |
| **F3** | X17 authorised "settle **or** refuse" — two observably different export contracts, the exact "or" `0010` exists to eliminate | §4f freezes **one deterministic per-state algorithm** (FINALIZED/ABANDONED export as-is; OUTPUTS_DURABLE rolls forward; expired-lease claims abandon; only live-lease claims refuse). X17 rewritten; recovery mutations it runs still obey the §11-F3 `store_version` invariant. |

### Contract corrections

| # | correction | v4 |
|---|---|---|
| **A** | "delete every/ALL row tagged `operation_id`" (transition table + Design-A prose) would delete the **inputs** too, since a claimed input also carries `operation_id` — recreating the data-loss class | Made uniform everywhere: **delete the provisional OUTPUT rows for `operation_id`; CLEAR `claimed_by`/`operation_id` on the claimed INPUT rows** (§4b-ii table + prose match §4b-iii/§4e). Never "all rows." |
| **B** | `lineage` is now the permanent eligibility discriminator, but the fields were independently optional — a malformed `lineage=[...]` with everything else `None` could acquire "never consolidate" status | §4e freezes three mutually-exclusive record shapes (plain / claimed-input / consolidated-output), validated on store insert **and** import. Invariant X18. |
| **C** | "every mutator takes `(operation_id, fence)`" is false for `create_or_takeover_consolidation` (creation has no id/fence yet) | Reworded to "every **post-creation** *owner* mutator"; §4a-ii freezes how takeover identifies the abandoned op it revives — by the **claim set**, not an `operation_id`. |

**Not changed:** the fenced/leased architecture, Design A, X9 as one conformance rule,
and the v1 non-recursive-compaction limit (reviewer-approved; the maintenance docs will
state "one-level consolidation, not recursive compaction" so operators infer no
storage-bounding property). The reviewer's v4 acceptance bar is F1–F3 + A–C; all six are
closed here.

---

## 14. Review closure — round 4 (2026-08-07)

Round-4 external review: **"fenced-state-machine architecture, Design A, and one-level
consolidation remain approved; v5 deferred on four load-bearing design gaps plus two
contract corrections."** The reviewer confirmed all six round-3 closures hold. The new
findings are protocol edges — **F2 is a genuine bug v4 introduced** (the takeover
selector), which the v4 found-in-fix pass missed. Each was reproduced against the spec
text first.

### Blocking findings

| # | finding | root fix in v5 |
|---|---|---|
| **F1** | the lease had no durable **`lease_duration`** — renewal's `store_now + lease_duration` had no source — and `owner` (visible via `pending_consolidations`) is not an auth capability though X7/X10 claimed absolute non-owner exclusion | §4a persists `lease_duration` on the op (renewal reads it, revalidated vs one `LEASE_MAX`); §4a-ii states the model as **cooperative identity** (trusted maintenance workers; a durability, not injection-resistance, protocol) and **scopes X7/X10** to it (no anti-forgery claim). |
| **F2** *(v4 bug)* | takeover directly revived an **expired-lease** op, claiming §4b-iii made it clean — false for an expired `GENERATING` op still owning provisional rows, recreating the X15 ambiguity | §4a-ii: a new fence issues **only from cleanup-complete `ABANDONED`**; an intersecting expired pre-cutover op is **abandoned (cleaned) first**, then the claim re-evaluates. Intersecting-but-not-equal handled the same way. X15 extended. |
| **F3** | export (settle-then-export) had **no atomic quiescence boundary** — a new claim could start between the scan and the episode read — and mutated memory before a possible later refuse/disk-failure | §4f makes export **read-only**: exports iff every op is quiescent, else **refuses without mutating**; the quiescence check + episode snapshot are **one atomic per-user observation**. Recovery stays in `maintain()`. X17 rewritten. |
| **F4** | an imported consolidated output requires `operation_id` (X18) but export carries no `ConsolidationOp`, so its X9 visibility (episode + op snapshot) was undefined | §4e freezes: after `FINALIZED`, `operation_id` is **historical provenance**; a `lineage`-bearing output is an independently visible settled record; X9's op lookup applies only while a local op exists. Small portable format, imported outputs visible. Invariant **X19**. |

### Contract corrections

| # | correction | v5 |
|---|---|---|
| **A** | `pending_consolidations` includes live ops that recovery won't touch, so a count off the list conflates "pending" with "recovered" | §4b freezes two `introspect()` fields: `consolidation_pending` (non-terminal seen) vs `consolidation_recovered` (actually rolled forward/abandoned). A live op is pending, never recovered. X13 updated. |
| **B** | v4 called clean `ABANDONED` "terminal", but the transition table allows `ABANDONED → CLAIMED` under a new fence | Reworded to **quiescent / cleanup-complete / takeover-eligible / not recovery-pending** in the active text (§4b, X13, X15). |

**Not changed:** the fenced/leased architecture, Design A, X9 as one conformance rule,
and one-level consolidation. **Note the export reversal:** v3→v4 froze *settle-then-export*;
round 4 showed making the public backup call mutate memory couples maintenance to a
filesystem write, so v5 makes export **read-only** — the reviewer's recommended contract.
The reviewer's v5 acceptance bar is F1–F4 + A–B; all six are closed here.

---

## 15. Review closure — round 5 (2026-08-07)

Round-5 external review: **"fenced-state-machine architecture, Design A, one-level
consolidation, and read-only export remain approved; v6 deferred on four load-bearing
design gaps plus three contract corrections."** All six round-4 closures confirmed. The
new findings are narrow lifecycle/interface gaps — two are the same *interface-hole*
class round 1 found (a prose guarantee no listed Store method can supply). Each was
reproduced against the spec text first.

### Blocking findings

| # | finding | root fix in v6 |
|---|---|---|
| **F1** | `FINALIZED` was reachable before inputs were deleted — `delete` and `transition` are separate primitives, so a bare `transition(…, FINALIZED)` with inputs present strands hidden input rows in a terminal, recovery-excluded state (falsifying the table's own `FINALIZED` meaning) | Froze **`transition(…, FINALIZED)` refuses unless every claimed input is already deleted** — the Store makes the invalid state unrepresentable, not caller discipline. Transition table + Store API annotated. Invariant **X20**. |
| **F2** | X17 required an atomic quiescence+snapshot observation, but no listed Store method could supply it (two ordinary reads race a new claim; a SQLite-only txn is the forbidden backend trick) — the round-1 interface-hole class | Added the named Store read **`quiescent_episode_snapshot(user_id) -> list[Episode] \| NonQuiescent`**, read-only and linearizable against `create_or_takeover`. §4f + X17 test it directly. |
| **F3** | X18 admitted an imported **claimed-input** shape, but `ConsolidationOp` is non-portable — accepting one recreates the round-2 durable orphan; and generic `add_episode` could fabricate operational state | §4e separates **portable shapes from storage shapes**: import allows plain + settled output, **always refuses claimed input**; operational shapes are created only by their fenced primitives. X18 extended. |
| **F4** | X19 made a finalized `operation_id` "historical unless a same-named local op exists," so an import file could collide a historical id with a **live local** op and rebind to it | §4e freezes: on import, historical `operation_id`s are **remapped to a fresh destination-local namespace** (grouping preserved), and live-op allocation never reuses a historical producer id. X19 extended. |

### Contract corrections

| # | correction | v6 |
|---|---|---|
| **A** | §2's operation-record field row omitted the newly persisted `lease_duration` (the on-disk/migration carrier renewal needs after restart) | Added `lease_duration` to the §2 record contract. |
| **B** | `consolidation_pending` was defined as "non-terminal ops," which would include quiescent `ABANDONED` — contradicting X13 | Redefined as **recovery-pending** (`{CLAIMED, GENERATING, OUTPUTS_DURABLE}`). |
| **C** | the abandon→claim crash seam sat inside one nominal `create_or_takeover` call, invisible to X5's Store-call-boundary sweep | Declared `create_or_takeover_consolidation` a **multi-phase** operation and added the internal abandon→claim boundary to X5's fault injection; X11 scoped to the **claim step**. |

**Not changed:** the fenced/leased architecture, Design A, X9, one-level consolidation,
cooperative-owner identity, and read-only refuse-and-retry export (reviewer reaffirmed).
The reviewer's v6 acceptance bar is F1–F4 + A–C; all seven are closed here.

---

## 16. Review closure — round 6 (2026-08-07)

Round-6 external review: **"fenced-state-machine architecture, Design A, one-level
consolidation, and read-only export remain approved; v7 deferred on three design gaps
plus three contract corrections."** The reviewer also **reaffirmed the purpose-built
reads** (`pending_consolidations`, `quiescent_episode_snapshot`) over a general
multi-read API — two invariant-specific reads are not yet reason to widen `0010` into a
transaction API. **Two of this round's findings are more fundamental than rounds 2–5's
interface-completeness edges:** F1 and F2 are about whether the invariants hold across
the *whole* store surface, not just the consolidation primitives. Each was reproduced
against the source or spec text first.

### Blocking findings

| # | finding | root fix in v7 |
|---|---|---|
| **F1** *(latent since round 1)* | §4a claimed "every write/delete CAS on `(operation_id, fence)`", but the *generic* `add_episode` (`INSERT OR REPLACE`) and `delete_episode` (unconditional) take no fence — so a plain `delete_episode` on a claimed input deletes it before a replacement is durable (violating X1), and a plain `add_episode` strips its claim fields. X18 guarded *creating* operational state, not mutating/deleting an already-operational row | §4e freezes: **while an episode participates in a non-quiescent op, generic `add_episode(same_id)`/`delete_episode(id)` REFUSE** — only fenced primitives may (`forget_user` excepted). Invariant **X21**. |
| **F2** | the point of no return proved too much: `write` accepted a fully-formed `Episode` with no binding check, and `GENERATING → OUTPUTS_DURABLE` succeeded with **zero** outputs — after which `delete inputs → FINALIZED` loses every input with no replacement (top-level claim + X1 violated); a misbound write could also let abandonment clean the wrong rows | §4b-ii: `write_consolidation_output_if_current` takes a **`ConsolidationOutputDraft`** and the store **binds** the row (`user_id`/`operation_id`/whole-set `lineage`/shape); the cutover **refuses with zero bound outputs**. No expected-output plan. Invariant **X22**. |
| **F3** | the historical-id namespace was half frozen: (3a) "fresh per invocation" would split one source op into two producer groups on a partial/retried import, breaking X19 grouping; (3b) `lineage` member ids got no namespace, so an imported provenance id could textually match an unrelated live local episode | §4e: the source→destination historical mapping is **deterministic and retry-stable** (recovered from already-imported siblings), and **`lineage` ids are remapped through the same namespace**. X19 extended. |

### Contract corrections

| # | correction | v7 |
|---|---|---|
| **A** | §8 said "each individual store call is atomic" after v6 made `create_or_takeover` explicitly multi-phase | §8 reworded: ordinary calls atomic; `create_or_takeover` is the multi-phase exception (abandon · seam · claim), the seam an X5 fault point. |
| **B** | X11's "the loser changes nothing" was too broad — a losing claim may have cleaned an expired intersecting op (an intentional durable side effect) | X11 reworded to **"the losing CLAIM step makes no partial new claim."** |
| **C** | X19's operation-id remap makes import no longer field-for-field exact, contradicting portability's "exact reproduction" wording | §4f: import preserves **logical provenance grouping + memory content**; local reference ids may be remapped. Exact-round-trip claim retired. |

**Not changed:** the fenced/leased architecture, Design A, X9, one-level consolidation,
cooperative ownership, read-only export, and the purpose-built semantic reads. The
reviewer's v7 acceptance bar is F1–F3 + A–C; all six are closed here.

---

## 17. Review closure — round 7 (2026-08-07)

Round-7 external review: **"architecture, Design A, one-level consolidation, read-only
export, and the X21 per-call guard strategy remain approved; v8 deferred on three
identity/store-surface gaps plus three contract corrections."** The reviewer **approved
the per-call participation check over splitting operational Episodes into a second row
space** (which would only move the hard questions onto `episodes()`/X9/migration/export).
The v8 findings are identity-boundary seams *around* the v7 fixes. Each was reproduced
against the spec text first.

### Blocking findings

| # | finding | root fix in v8 |
|---|---|---|
| **F1** | X21 protected an *existing* claimed row, but after the fenced delete removes an input (the `OUTPUTS_DURABLE → delete → FINALIZED` interval) the op still reserves the id — and a generic `add_episode(old_id)` has no live row to inspect, so it could resurrect the input | §4e: X21 is now **ID-reservation based** — every `claimed_id` is reserved while the op is non-quiescent and the reservation **survives physical deletion** until `FINALIZED`/clean `ABANDONED`. Test added for the delete→`FINALIZED` seam. |
| **F2** | `ConsolidationOutputDraft` bound the operational *fields* but never froze the output Episode **id** ownership or insert-not-replace, so a draft carrying `id="ep-existing"` could overwrite unrelated history through a primary-key collision (`add_episode` is `INSERT OR REPLACE`) | §4b-ii: the draft carries **no id/user_id/operation_id/claimed_by/lineage**; the store **mints a fresh id** and **INSERTs — never replaces**. X22 extended (`test_output_write_cannot_replace_an_existing_episode`). Mirrors `0009`'s `OutcomeJudgmentDraft`. |
| **F3** | historical `lineage` ids were protected at import, but the collision recurs **after local finalization**: `output.lineage=["ep-A"]`, `ep-A` deleted, then a later `add_episode(id="ep-A")` makes the provenance string resolve to an unrelated live row | §4e (design A): `lineage` values are **`HistoricalEpisodeId`s in a namespace no live Episode id can inhabit**; deleted ids are converted to historical refs at output creation **and** import, and the live-id allocator can never produce one. X19 extended (covers local finalization, not just import). |

### Contract corrections

| # | correction | v8 |
|---|---|---|
| **A** | the literal §11-F3 rule ("any change to the `episodes()` result bumps `store_version`") also covers a claim's `claimed_by` change on still-visible inputs, but X14 only tested the cutover | §11-F3 **scoped to recall-relevant content** — operational metadata (`claimed_by`/`operation_id`) excluded, so a claim doesn't bump (compile/recall never reads it), avoiding needless invalidation. X14 updated. |
| **B** | the whole-set **minimum-trust** and `date_start`/`date_end` output derivations were normative prose but absent from X1–X22 — exactly the guarantee a new draft/write boundary can accidentally move from "computed from inputs" to "whatever the draft supplied" | New invariant **X23**: the store computes trust-floor + date range from `op.claimed_ids`, not the draft/LLM. |
| **C** | v7 allowed the historical-id map to be a deterministic function **or** a persisted table — but a persisted table is undeclared user-scoped durable state | Fixed as the **deterministic destination-qualified function** (no new table; a persisted map would have needed §2 schema + `forget_user` declaration, now avoided). |

**Not changed:** the fenced/leased architecture, Design A, X9, one-level consolidation,
cooperative ownership, read-only export, purpose-built reads, and the single-Episode-space
+ per-call reservation strategy (reviewer-approved). The reviewer's v8 acceptance bar is
F1–F3 + A–C; all six are closed here.

---

## 18. Acceptance boundary (set 2026-08-07)

`0010` is **accepted at v8** on a finite boundary — the same discipline that ended
`0013`'s non-convergence. Recording it explicitly so the criterion is unambiguous.

**Why a boundary.** Seven external rounds each **affirmed the architecture** (fenced/leased
state machine · Design A · one-level consolidation · read-only export · single-Episode-space
+ X21 reservation) and none reopened it. But on a detailed, near-executable model the
review has **no natural terminal**: rounds 3–7 increasingly surfaced seams *in the previous
round's own fix* (round 7's three blockers all refined round 6's X21/X22/X19). Continuing
to add prospective invariants in prose has diminishing value versus accepting the frozen
design and validating it in code. Acceptance is on **the six architectural properties + the
X1–X23 invariant surface being frozen and demonstrable — NOT on the reviewer running out of
adjacent seams.**

**The acceptance surface (frozen).**
- **Architecture:** the fenced operation record (§4a), the lease/cooperative-owner protocol
  (§4a-ii), the all-or-nothing batch-claim + fenced mutators + recovery-discovery +
  quiescent-snapshot reads (§4b), the full transition table (§4b-ii) under **Design A**,
  exactly-one-representation X9 (§4c), whole-batch lineage (§4d), read-only export (§4f).
- **Invariants X1–X23 (§6)** — the executable acceptance tests that MUST hold in the
  implementation. Acceptance means these are frozen in normative text; it does not assert
  code exists (none does yet — `0010` is a design spec).

**Implementation obligations (validated when code lands, not spec blockers).**
1. Every X1–X23 test passes against the SQLite `Store`.
2. The **store-wide identity/fence-hygiene** contract shared with `0009` — X21 (reserved
   claimed-ids refuse generic mutation) ≡ `0009` H14 (outcome rows refuse generic
   mutation), plus store-minted row identity on the fenced writes (X22 / `0009`
   `OutcomeJudgmentDraft`). **This is a `Store`-interface concern; settle it once** (a
   participation/reservation index + insert-only fenced writers), not per feature. A future
   `Store`-contract spec is the natural home; until then each implementing spec cites this
   obligation.
3. The `SCHEMA_VERSION 2→3` migration (shared with `0009` per §9's conditional rule) lands
   through `0013`.
4. Any further external-review edge is triaged here as an obligation, not a re-opening —
   unless it reopens one of the frozen architectural properties above.

**What `accepted` authorises:** implementation of this design (PROCESS.md §4a). Guarded-file
commits citing `Spec: specs/0010-...` are now permitted, since `Spec-Requires: 0007, 0013`
are both `accepted`.
