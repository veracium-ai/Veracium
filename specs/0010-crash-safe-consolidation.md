# Feature spec: crash-safe consolidation

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — split out of `0002` §7e on 2026-08-02. **`0002` froze the
> acceptance contract and deliberately left two implementation strategies open.
> The third external review's point stands: acceptance authorises
> implementation, so "atomic or a state machine" would authorise two materially
> different designs without specifying either.** This spec picks one.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 |
| **Status** | *see `Spec-Status:` — canonical.* Owns the contract stated in `0002` §7e. |
| **Internal reviewers** | research — pending |
| **External review** | required — `lifecycle.py` is guarded and this changes durability semantics |
| **Decision + date** | — |
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
| **`Episode.consolidated_into`** | **NEW**, optional | the summary that absorbed this episode; retained on the input until deletion is safe |
| **`Episode.lineage`** | **NEW**, optional list | on the output: the ids it absorbed — **`0002` N9b's lineage row, made storable** |
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

**Chosen strategy: write-before-delete with a lineage-based recovery pass.**
Not a store transaction — `Store` is an interface with a Postgres implementation
contemplated (`0002` Q-carry), and requiring cross-backend atomic multi-statement
transactions would push a durability guarantee into every future backend.
**Ordering plus a recovery rule needs nothing the interface does not already
have.**

1. **Claim** — mark each input `consolidated_into = <new id>`, durable.
2. **Write** — persist the summary with `lineage = [input ids]`, durable.
3. **Delete** — remove the claimed inputs.
4. **Recover** — on the next `consolidate()`, any episode with
   `consolidated_into` pointing at an **existing** summary is a leftover from
   step 3 and is deleted; pointing at a **missing** summary means the crash
   happened between 1 and 2, and the claim is cleared.

**Every crash point lands in a recoverable state, and no state is ambiguous** —
that is the property the delete-first order cannot have at any cost.

**Cost:** one extra write per input episode, on an operation that already makes
an LLM call. **Negligible against what it buys**, and it is why this is not
worth optimising into a transaction.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **X1** an input is never deleted before its summary is durable | `test_consolidation_writes_before_deleting` — a store wrapper that raises after the write | CI |
| **X2** a crash mid-delete is recovered, not repeated | `test_recovery_completes_a_partial_delete` | CI |
| **X3** retry is idempotent by **lineage**, not by content | `test_consolidation_retry_is_idempotent` — **no summary-of-summary** | CI |
| **X4** a claimed input is not consolidated twice | `test_concurrent_consolidation_claims_once` | CI |
| **X5** no crash point loses an episode without a replacement | `test_no_crash_point_loses_data` — **parametrised over every store call in the operation**, failing at each in turn | CI |
| **X6** lineage is complete | `test_summary_lineage_lists_every_absorbed_episode` — **N9b's premise** | CI |

**X5 is the one that matters** and is written as a sweep rather than three cases,
because the defect being fixed is precisely *a crash at the one point nobody
enumerated*.

---

## 7. Failure modes and reversibility

**Failure mode is a leftover claim or a duplicate**, both detectable and both
resolved by the recovery pass. **Reversible in code**; the two new fields are
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

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| **X-Q1** | Should recovery run on **every** `consolidate()`, or on a dedicated `repair()` the host calls? Running it automatically is safer and means a read path can encounter unrecovered state between crash and next maintenance. **Dev leans automatic, plus surfacing the count in `introspect()`.** | **blocking** | research | before implementation |
| **X-Q2** | Should the wiki drop when recovery fires (`0004`)? A recovered store's episode set changed underneath a cached view. **Dev leans yes** — same argument as `0004` W1. | `pre-release` | dev | before release |
