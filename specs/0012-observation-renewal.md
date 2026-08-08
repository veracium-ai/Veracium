# Feature spec: who may renew a fact's currency

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft (v2) — the three open questions are RULED (research, 2026-08-08;
> `proposals/0012-rulings.md`).** Split out of `0008` after its second external review showed
> liveness renewal needs an observation model `0008` cannot carry. **Ruling: Design 1 — reinforcement
> transfers NOTHING** (not `observed_at`, not `confidence`, not `valid_from`; the incoming edge is
> persisted with its own provenance). O-Q2 (no functional violation; render both, don't collapse) and
> O-Q3 (`expire()` stays PER-EDGE — grouping would reintroduce the bypass; frozen as an invariant) are
> resolved. **No open question blocks the spec.** 🔗 **Design 1 closes `0014` §3.1 + finding `M9`
> (§11), which argues for landing `0012` before `0014`.** Still `draft` — needs an external review of
> the chosen design before `accepted`.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v2** — *O-Q1/O-Q2/O-Q3 ruled; Design 1 (transfers nothing) frozen.* |
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
