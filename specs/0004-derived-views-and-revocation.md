# Feature spec: derived views must not outlive a revoked trust decision

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — split out of `0002` on 2026-08-01. Finding and fix were both
> already verified there; this document exists so the fix has a spec it can
> close, rather than waiting behind an unrelated retrospective.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 |
| **Status** | *see `Spec-Status:` — canonical.* Split from `0002` §M8/§11c, unchanged in substance. |
| **Internal reviewers** | research — **found the defect**; fix verified by dev |
| **External review** | required — touches `compile.py` and the store write path |
| **Decision + date** | — |
| **Path** | full |

> **Why this is its own spec.** It was filed in `0002` because that is where the
> maintenance audit found it. `0002` is a **retrospective for a shipped hotfix**
> and must be closeable; M8 is a **proposal** and is not. Keeping them together
> meant an unshipped fix held a finished record open, and everything citing
> `0002` waited behind both. **The finding is unchanged — only its home is.**

---

## 1. Problem and motivation

**Found by research, reproduced here.** §3 marks `compile.py` clean and the
architectural note covers *a correct filter defeated by upstream corruption of
its input*. **This is a third failure shape: the filter is correct, its input is
correct, and the OUTPUT is cached across subsequent trust changes.**

`compile.py:74` recompiles only after `wiki_recompile_after_writes` store
versions (**default 8**), and `__init__.py:225` appends the wiki to
**`grounded_parts`**. So a revocation takes effect on the edge immediately and
**not on the wiki**:

```
default wiki_recompile_after_writes = 8
wiki built: True
after dispute():
  edge active       : [False]
  'Acme' in GROUNDED: True      <-- disputed fact still asserted
```

**A user's explicit trust action is silently ineffective on the one surface that
matters — what the model reads.** Same for a late supersession, correction or
quarantine.

**Reachability, measured rather than inferred.** `cli.py:198` sets
`wiki_recompile_after_writes = 10**9 if has_wiki else 0`, so **once a wiki
exists the CLI never recompiles**. But `dispute` and `correct` are **not CLI
verbs** — `grep -n "add_parser" src/veracium/cli.py` lists telemetry ·
selfcheck · diagnostics · export · import · forget · recall · remember ·
introspect. **So the unbounded case is not "CLI user disputes and nothing
happens"; it is the mixed path: a host revokes through the API, an operator
later reads the same store with `veracium recall`, and that path never
recompiles — so the revoked fact stays in the grounded block indefinitely.**
Narrower than "the CLI is unbounded", and still real.

**Fix costs nothing and fails closed: a trust-reducing event DROPS the wiki
rather than recompiling it.** `invalidate_edge` with reason in
`{disputed, corrected, superseded}`, and any quarantine, empties the cache. No
LLM call, no latency; you lose curated breadth until the next natural recompile
and never assert revoked content.

**Finding for the spec, not an advisory** — attacker-free, and self-healing
within 8 writes on the library default. But it is **the same shape as both
advisories**: a derived artifact preserving a trust decision after the decision
changed.

---

## 3. Trust-class matrix

**Not applicable in the usual direction, and that is the finding.** No trust
class is mis-assigned here: the filter is correct, its input is correct, and the
**output is cached across a subsequent trust change**. Every class is affected
identically, because the wiki is compiled from the grounded set and then frozen.

| edge state at compile | trust change after | served? | correct? |
|---|---|---|---|
| active, assertable | `dispute()` | **yes** | **NO** |
| active, assertable | `correct()` | **yes** | **NO** |
| active, assertable | superseded by a later ingest | **yes** | **NO** |
| active, assertable | `lapsed` / `decayed` | yes | acceptable — staleness, not revocation |

**This is a third failure shape**, distinct from both advisories: 0.4.1 and
0.4.4 were *a correct filter defeated by corruption of its input*. Here nothing
upstream is corrupt. **A derived view that outlives its inputs is not downstream
of them** — the sentence that falsified `compile.py`'s guarded-list exclusion.

---

## 4. Behaviour

**Where.** `store.invalidate_edge`. **Verified to be a real single choke point**
— every invalidation in the codebase goes through it:

```
$ grep -rn "invalidate_edge(" --include=*.py src/veracium/
lifecycle.py:45  "lapsed"     lifecycle.py:49  "decayed"
graph.py:136     "absorbed_duplicate"   graph.py:141  "superseded"
__init__.py:462  "disputed"   __init__.py:612  "corrected"
```

**Putting it in `Memory.dispute()`/`correct()` would miss `graph.py`'s
supersession**, which is the path an attacker reaches — so the store layer is
not a stylistic preference here.

**Which reasons drop the wiki:** `disputed` · `corrected` · `superseded`.
**Not** `lapsed` / `decayed` — those are time-based staleness, not a revoked
trust decision, and dropping curated breadth on every decay cycle pays a real
cost for no trust gain. `absorbed_duplicate` is **arguable and currently
excluded**: the content survives in the surviving edge, so the wiki is not
serving anything revoked. Flagged rather than decided.

**Drop, do not recompile** — no LLM call, no latency, fails closed. Curated
breadth is lost until the next natural recompile; revoked content is never
asserted.

### ⚠️ Correction to the M8 finding: one clause is unreachable

The original text says the fix covers *"and any quarantine."* **There is no
post-ingest quarantine path.** Verified mechanically rather than recalled:

```
$ grep -rn "disclosure\s*=" --include=*.py src/veracium/
ingest.py:117   disclosure = _disclosure_for(author, relation, derived_from)
ingest.py:128   disclosure=disclosure, ...
```

`disclosure` is written in **exactly one place**, at ingest, and never lowered
afterwards. The clause describes an event that cannot occur, and it is **struck
rather than implemented** — building a handler for it would have produced dead
code that reads as coverage.

**Worth naming as a method note:** this is the third time in this spec that a
claim survived because it sounded right. It came from my own summary of
research's finding, not from research.

**Checks.** `test_dispute_drops_the_wiki` (the reproducer becomes the fixture) ·
`test_third_party_supersession_drops_the_wiki` (the `graph.py` path, which is
why the fix is in the store) · `test_decay_does_not_drop_the_wiki` (the
exclusion is deliberate, so it is pinned).

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **W1** a revoking invalidation empties the wiki cache | `test_dispute_drops_the_wiki` — the measured reproducer becomes the fixture | CI |
| **W2** the drop covers the **supersession** path, not just the `Memory` verbs | `test_third_party_supersession_drops_the_wiki` | CI |
| **W3** staleness does **not** drop it | `test_decay_does_not_drop_the_wiki` — pins a deliberate exclusion so it cannot erode into "drop on everything" | CI |
| **W4** no LLM call on the drop path | `test_wiki_drop_makes_no_llm_call` — a `Complete` that raises if invoked | CI |

**W2 is the one that matters** and is the reason the fix sits in the store.
A fix in `Memory.dispute()`/`correct()` passes W1 and W3 and **fails W2
silently** — the tests would be green and the attacker path open.

---

## 7. Failure modes and reversibility

**Failure mode is loss of curated breadth**, never assertion of revoked content.
The wiki is an optimisation; recall works without it. Reversible by reverting —
nothing is written that a later compile cannot rebuild.

**The cost is real and bounded:** on the library default
(`wiki_recompile_after_writes = 8`) breadth returns within 8 writes. On the CLI
path it does not, because `cli.py:198` sets `10**9` once a wiki exists — so a
CLI operator loses the wiki until something else triggers a compile. **That is
the correct trade** and it is the same asymmetry that governs T1: missing
breadth is inspectable, asserting a revoked fact is not.

---

## 8. Claims and limits

**Claim:** a trust-reducing event takes effect on every surface the model reads,
not only on the edge.

**Limit, stated because it is the honest one:** this makes the wiki *fail
closed*, it does not make it *incremental*. A large store loses its whole
curated view because one fact was disputed. Incremental invalidation is the
better answer and is deliberately **not** in scope — it needs a dependency map
from wiki text back to edges, which does not exist.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| **W-Q1** | Should `absorbed_duplicate` drop the wiki? The content survives in the surviving edge, so nothing revoked is served — **currently excluded**. Flagged rather than decided. | `pre-release` | research | before implementation |
| **W-Q2** | Should the CLI's `10**9` recompile threshold be revisited, given it makes the breadth loss unbounded there? Out of scope for the fix; in scope for whether the trade is acceptable. | `deferred` | dev | own round |
