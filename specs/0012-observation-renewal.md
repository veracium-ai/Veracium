# Feature spec: who may renew a fact's currency

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — split out of `0008` on 2026-08-02, **after its second external
> review showed that liveness renewal needs an observation model `0008` cannot
> carry.** The defect is real and measured; the fix is a design.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 |
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

## 2. Why it could not stay in `0008`

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
| **1** | **No reinforcement transfers liveness.** The incoming same-value edge is persisted with its own `observed_at`; the prior ages honestly. The fact stays live *through the new edge*. | two active edges per restatement — dedup, rendering and functional semantics all need answers |
| **2** | **A dedicated `reobserve()` entry point**, capability-gated like `confirm()`. Follows `0008`'s own principle: *an act through a protected path is evidence; a field is not.* | a host that never calls it sees facts lapse that it thinks are live |
| **3** | **Defer entirely** until authenticated source identity or call-path provenance exists (`0006`, `0011` E4). | the bypass stays open, documented and measured |

**Dev leans 1**, because it is the only one that needs no new trust primitive
and no host cooperation — the fact remains fresh through evidence that actually
arrived, rather than by laundering currency onto an older assertion. **Its cost
is real and is the reason this needs review rather than a decision here.**

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| **O-Q1** | Which of the three designs? | **blocking** | research | before design |
| **O-Q2** | Under design 1, do two same-value active edges violate functional-relation semantics — and is that `0011` E3's contested state again? | **blocking** | dev | before design |
| **O-Q3** | Does `expire()` age against the newest edge for a `(subject, relation)` rather than per-edge, which would make design 1 work with no rendering change? | `pre-release` | dev | before design |
