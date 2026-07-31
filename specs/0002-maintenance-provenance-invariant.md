# Feature spec: the maintenance provenance invariant

*Retrospective spec for **0.4.4** (GHSA-hcj3-8jqc-wqrp), discharging the
`Spec-Retrospective-Due: 2026-08-07` obligation recorded in `ea2e1ab`. Written
as an **audit of every maintenance-time operation**, because 0.4.1 and 0.4.4 are
the same shape and one fix does not close a class.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 |
| **Status** | draft — internal review not yet requested |
| **Internal reviewers** | research *(trust semantics; and paper 2 is on this exact subject — see §8)* |
| **External review** | required — full spec (touches `graph.py`, `lifecycle.py`, `__init__.py`) |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation

**Two security advisories in four days, both the same shape.** GHSA-r7j7-5jq9-3f5q
(0.4.1) and GHSA-hcj3-8jqc-wqrp (0.4.4) are both *maintenance-time* operations
crossing a trust boundary that the *write path* guards correctly. We fixed two
instances. Nobody has checked whether the class is closed.

**If we do nothing:** the pattern continues. Every maintenance operation is a
place where trust state is recomputed with **no new evidence**, and our review
attention has been on the write path, where the adversary is obvious. The audit
below found **three further defects, two of them shipped**, so the answer to
"was 0.4.4 the last one" is no.

**Alternatives rejected.** *Fix each instance as found* — that is what we have
been doing, and it produced two advisories and no rule. *A prose guideline* —
§2c of the template exists because prose guidance is answered from the same
mental model that produced the defect.

**The invariant this spec proposes:**

> **A maintenance-time operation may narrow trust. It may never widen it, and it
> may never re-derive a provenance field from anything other than new evidence
> from a party entitled to supply it.**

"Narrow" is deliberate and mirrors *configuration may narrow what is assertable,
never widen it* (spec 0001) and `derived_from` capping but never raising (0.1.7).
**Three independent rules with the same shape is not a coincidence; it is the
architecture's actual invariant, stated three times in three places.** This spec
names it once.

---

## 2. Field contracts touched

| field | read / written | its **documented** contract | consumers | preserved? |
|---|---|---|---|---|
| `Edge.valid_from` | ingest; **`confirm()`**; T1 absorption | **"first-known and immutable"** — 0.4.3 CHANGELOG: *"valid_from is set at creation and never mutated"* | `render_edges` (`(since X)` → model context), `edges_since`, E1 clustering, absorption | **NO — violated in shipped code. See M2.** |
| `Edge.needs_confirmation` | `expire()` sets; `confirm()` clears; **T1 reinforcement clears** | "possibly stale — confirm before relying on it"; `confirm()` is the sanctioned exit | `render_edges` (staleness marker), `proactive` | **NO — M3.** |
| `Episode.provenance.author_of_evidence` | ingest; consolidation; **`record_outcome` upgrade-in-place** | "who authored the evidence" | gate routing, consolidation | **NO — M4, erasure without history.** |
| `Provenance.confidence` | ingest; `expire()` decay; T1 both paths | strength of belief | `expire()` floor, T2 design | **Partly — see M5.** |

**Enumerated mechanically** (not from memory — that rule is why 0.4.4 was found):

```
$ grep -rn "\.provenance\.\(confidence\|observed_at\|disclosure\|author_of_evidence\|derived_from\)\s*=\|needs_confirmation\s*=\|\.valid_from\s*=\|model_copy" \
    src/veracium/*.py src/veracium/store/*.py | grep -v ingest.py
__init__.py:493-495   confirm(): valid_from, needs_confirmation, confidence
__init__.py:554       record_outcome(): author_of_evidence  <-- overwrite in place
__init__.py:570       record_outcome(): needs_confirmation
graph.py:107-111      T1 reinforcement: observed_at, confidence, needs_confirmation
graph.py:118-121      T1 absorption: valid_from, observed_at, confidence
lifecycle.py:54       expire() CONFIRM: needs_confirmation
lifecycle.py:114      consolidate(): whole provenance   <-- fixed in 0.4.4
```

**Nine mutation sites outside `ingest.py`. Every one is a place trust state
changes without new evidence arriving through the front door**, and until this
audit no document listed them together.

---

## 2c. Untrusted inputs

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| **host-supplied `author`** (`mcp_server.py:26`, `cli.py:299`) | rejected by enum | rejected by enum | rejected by enum | **host may claim `system`, which shares `MENTIONABLE` with `user`** — this is M3's reachability | **M3 fix: `needs_confirmation` clears only on same-author evidence or `confirm()`** |
| **host-supplied `actor`** (`record_outcome`) | defaults `user` | n/a | maps via `_OUTCOME_ACTORS` | **last writer's label silently wins** | **M4 fix: append, never overwrite** |
| **host-supplied `date`** (`confirm()`, `remember()`) | defaults today | `_event_dt` falls back to now | — | **a future or back-dated value moves `valid_from`** | **M2 fix: `valid_from` immutable; confirmation date goes to `observed_at`** |
| **cold-episode set** (consolidation) | no-op below batch | — | — | **mixed authorship** | **M1 (0.4.4): provenance derived from the whole set** |
| **older-version store data** | — | pydantic rejects unknown enum | — | — | ⚠️ **no invariant — no `PRAGMA user_version`.** Carried from spec 0001 Q3; **this empty cell is a gate on that spec, not this one** |

---

## 3. Trust-class matrix — the audit

Every maintenance-time or trust-mutating operation, against the lens:
**does it re-derive provenance, disclosure, authorship or currency from anything
other than new evidence from a party entitled to supply it?**

| operation | verdict | detail |
|---|---|---|
| `lifecycle.expire()` — LAPSE | ✅ clean | invalidates only; ages against `observed_at`, which is the C′ liveness axis |
| `lifecycle.expire()` — DECAY | ✅ clean | `confidence *= decay_factor` **narrows only**; re-add via `add_edge` is a pure upsert with no timestamp mutation (verified) |
| `lifecycle.expire()` — CONFIRM | ✅ clean | sets `needs_confirmation = True`; narrowing |
| `lifecycle.consolidate()` | ✅ **fixed 0.4.4** | **M1** — derived provenance from `cold[0]`; now whole-set, min-trust |
| `compile.py` (wiki) | ✅ clean | filters `not e.use_only` **and** `not third_party_influenced`, explicitly mirroring `gate.partition`. **But see the architectural note below** |
| `proactive.assemble()` | ✅ clean | `if not e.assertable: continue` |
| **`confirm()`** | 🔴 **M2 — shipped defect** | mutates `valid_from` |
| **T1 reinforcement** | 🟠 **M3 — shipped defect** | clears `needs_confirmation` on cross-author evidence |
| **`record_outcome()` upgrade-in-place** | 🟠 **M4 — shipped defect** | overwrites `author_of_evidence`, no history |
| **T1/T2 `confidence = max(...)`** | 🟡 **M5 — design** | raises confidence at merge time |

**Architectural note, and it is the most important line in this spec.**
`compile.py` and `gate.py` both have **correct** defences. Both were bypassed by
0.4.4 anyway, because consolidation corrupted the very field they key on
(`third_party_influenced`). **A defence in the right place is not sufficient if
an upstream maintenance operation can rewrite its input.** That is the general
form of the bug, and it is why an audit of *mutation sites* finds things an audit
of *decision sites* does not.

### M2 — `confirm()` mutates `valid_from` (shipped, 0.4.4)

`__init__.py:493` is `edge.valid_from = _event_dt(date)`. **Reproduced:**

```
stated in January.       valid_from = 2026-01-15
  renders: prefers: dark mode (since 2026-01-15) [possibly stale — confirm…]
user confirms in March.  valid_from = 2026-03-01
  renders: prefers: dark mode (since 2026-03-01)
```

**This is precisely the defect C′ shipped in 0.4.3 to eliminate**, in a sibling
path the fix did not touch. `render_edges` emits `(since X)` into answer context,
so this is **a false statement in front of the model**, not merely lost history —
C′'s own words. Worse: **0.4.3's CHANGELOG asserts *"valid_from is set at
creation and never mutated"***, which is false as shipped. We published a
BREAKING semantics change and did not honour it.

**Fix:** `valid_from` is immutable. A confirmation is new evidence about
*liveness*, so it advances `provenance.observed_at` — the same resolution C′
applied to reinforcement.

### M3 — cross-author clearing of `needs_confirmation` (shipped)

`graph.py:111` clears `needs_confirmation` on reinforcement. The 0.4.1 guard
(`graph.py:94`) compares **disclosure class**, and `USER` and `SYSTEM` **share
`MENTIONABLE`**. Reproduced: a `SYSTEM`-authored restatement clears a `USER`
fact's staleness flag.

`needs_confirmation` renders as *"[possibly stale — confirm before relying on
it]"*. It is a **question addressed to the user**. A system restatement answering
it is the same speaker/witness confusion that caused spec 0001's deferral, one
layer down. `THIRD_PARTY` is correctly blocked — the 0.4.1 guard does its job;
it just guards the wrong axis for this field.

**Not a disclosure-class crossing, so materially milder than 0.4.4** — nothing
becomes assertable that was not. It removes a caveat on someone else's
authority.

**Fix:** `needs_confirmation` clears only on evidence from the **same author
class** as the flagged edge, or via `confirm()`.

### M4 — `record_outcome` overwrites authorship without history (shipped)

`__init__.py:554`: `prior.provenance.author_of_evidence = author` on
upgrade-in-place. The last writer's `actor` label silently wins and **the prior
authorship is unrecoverable** — in a system whose stated principle is
**supersession-never-erasure**. The host controls `actor` in both directions, so
this is not privilege escalation; it is provenance destruction.

**Fix:** append a new outcome episode rather than overwriting, or retain prior
authorship in a note. Erasure is the part that is wrong, not the update.

### M5 — merge-time `confidence = max(...)` (design, partly shipped)

T1 (`graph.py:109`, `:121`) and T2's approved design both take
`confidence = max(members)`. **`max` raises**, which the invariant forbids
without new evidence. On T1 the incoming edge *is* new evidence, so it is
defensible; **on T2 dedup it is not — dedup is maintenance-time bookkeeping over
existing statements.** T2 is unshipped, so this is a design correction, not a
defect. **It must be settled before T2 lands, not during.**

---

## 3b. Authorization and scope

n/a — no operation here crosses a user, tenant or scope boundary; all are
single-`user_id` in-store transformations. Recorded rather than omitted because a
blank heading is indistinguishable from an unasked question.

---

## 4. Behaviour

| | before | after |
|---|---|---|
| confirm a fact stated in January, in March | context reads `(since March)` | `(since January)`; `observed_at` advances to March |
| system-authored restatement of a stale user fact | staleness marker removed | marker retained; only user evidence or `confirm()` clears it |
| second outcome recorded by a different actor | prior authorship overwritten | prior authorship retained |

**Interfaces:** no signature changes. **Migration:** none — no backfill. Edges
whose `valid_from` was already moved by `confirm()` **cannot be repaired**: the
original date is not recorded anywhere. That is unrecoverable and must be said in
the changelog.

---

## 5. Regime analysis

- **Duration is the regime**, and it is why these survived. Every defect here
  needs *elapsed time* to become visible: `confirm()` needs a fact old enough to
  go stale, consolidation needs 30 days and 8 episodes, expiry needs a lifetime
  to pass. **Fixtures are instantaneous.** Our test suite runs in 17 seconds and
  cannot, in principle, reach the regime where maintenance defects live.
- **Thresholds:** `consolidate_after_days` (30), `consolidate_min_batch` (8),
  `volatility_lifetime_days`, `confidence_floor`.
- **Do the tests reach it?** Only by injecting `now=`. **Release class: stable,
  so an unreachable regime blocks** — §6 checks all use explicit clock injection
  over simulated months rather than wall-clock.
- **Cold vs warm:** maintenance is where the difference *is*; a store that never
  runs `maintain()` exhibits none of this.

---

## 6. Invariants and executable checks

| invariant | executable check | where |
|---|---|---|
| **N1** `valid_from` is never mutated after creation by *any* operation | `test_valid_from_immutable_across_every_mutation_site` — parametrised over confirm / reinforce / absorb / expire / consolidate | CI |
| **N2** `confirm()` advances `observed_at`, not `valid_from` | `test_confirm_advances_liveness_not_first_known` | CI |
| **N3** `needs_confirmation` clears only on same-author evidence or `confirm()` | `test_cross_author_cannot_clear_staleness` | CI |
| **N4** no operation raises `disclosure` toward assertable | `test_no_maintenance_op_widens_disclosure` — property-based over a random op sequence | CI |
| **N5** `author_of_evidence` is never overwritten without retaining the prior value | `test_outcome_upgrade_retains_prior_authorship` | CI |
| **N6** consolidation provenance derives from the whole set (0.4.4) | existing `test_consolidation_provenance.py` | CI |
| **N7** a full `maintain()` cycle over simulated months never moves an edge from UNVERIFIED to GROUNDED | `test_maintenance_never_promotes_across_the_gate` — **the general form of both advisories** | CI + bench |

**N7 is the one that matters.** It is stated over the *observable boundary*
rather than over any field, so it catches the next instance of this class even if
the mechanism is one nobody has thought of. Both advisories would have failed it.

---

## 7. Failure modes and reversibility

- **Silent failure:** all four defects are silent by construction — they change
  provenance, and provenance is only visible through `introspect()` or a
  rendered marker most users never diff. M2's symptom is a wrong date in an
  answer; M3's is a *missing* caveat, which is invisible.
- **Reversibility:** the fixes are reversible. **The damage is not** — M2 has
  already destroyed original `valid_from` values in any store where a stale fact
  was confirmed, and consolidation has already destroyed member episodes.
- **Partial failure:** `maintain()` is idempotent and per-edge; a crash leaves a
  partially-maintained store, which is safe because every operation narrows.
- **New attack surface:** none. This spec only removes capability.

---

## 8. Claims and limits

- **What we will say:** *"0.4.5 fixes three provenance defects found by an audit
  of every maintenance-time operation, prompted by two advisories in the same
  class. `confirm()` no longer moves a fact's first-known date; a staleness flag
  can no longer be cleared by a different author; outcome authorship is no longer
  overwritten."*
- **What this does NOT establish.**
  - **Not that the class is now closed.** It establishes that nine mutation sites
    were enumerated and checked on **2026-07-31 at commit `06c6f13`**. N7 is the
    only check that generalises; the rest are instance checks.
  - Not that `expire`, `compile` and `proactive` are *correct* — only that they
    do not violate **this** invariant. `compile` and `gate` were both individually
    correct and were bypassed anyway.
  - No measurement of real-world exposure. We do not know how many deployments
    run `maintain()`.
- **⚠️ Conflict of interest, stated because nobody else will.** Research's
  **paper 2 is titled *"Maintenance Is an Attack Surface"***, is preregistered,
  and has not run. This audit produces exactly the evidence that paper wants,
  from our own codebase, found by us. **That is a reason for more caution in
  reporting it, not less.** Recommend: the paper cites the two advisories as
  public artifacts with dates, and does **not** cite this internal audit as a
  finding; and no marketing framing presents an internally-found bug count as
  evidence of the thesis. Research's call, flagged before the findings are
  written up rather than after.

---

## 9. Brief for the external reviewer

- **What we are least sure of.** (1) Whether **N7 is actually the general
  form**, or merely the general form of the two instances we happen to have seen
  — the honest answer is that we cannot tell from two. (2) Whether "same author
  class" is the right axis for M3, given that the axis error is exactly what
  deferred spec 0001. (3) Whether `expire()`'s confidence decay is genuinely
  narrowing in all cases, or only in the ones we constructed.
- **Where we suspect we have overstated.** §1's claim that three rules with the
  same shape reveal "the architecture's actual invariant" is a satisfying
  sentence and may be pattern-matching on three data points.
- **What would change our minds.** A maintenance operation that legitimately
  needs to widen trust. We could not construct one, which is either evidence for
  the invariant or a failure of imagination.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| Q1 | Is `confidence = max` acceptable for **T2 dedup**? M5 says no — dedup is maintenance-time bookkeeping. | **blocking** | research | before T2 lands |
| Q2 | Should M2/M3/M4 ship as 0.4.5 without an advisory? None is a trust-boundary bypass; M2 puts a false date in model context. | **blocking** | Quentin | before release |
| Q3 | Does the paper-2 conflict in §8 need a stated policy, or is per-case judgement enough? | `pre-release` | research | before paper 2 runs |
| Q4 | Should `needs_confirmation` be per-author rather than a single boolean? Would dissolve M3 structurally. | `deferred` | dev | own design round |
