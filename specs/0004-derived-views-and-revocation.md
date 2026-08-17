# Feature spec: derived views must not outlive a revoked trust decision

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft v2 — REFRESHED 2026-08-17 for internal review.** Split out of
> `0002` on 2026-08-01 and never reviewed; sixteen days of shipping moved the
> ground under it, so every mechanical claim below was RE-EXECUTED before this
> revision (§2c-ii carries the commands and their real output, run 2026-08-17).
> **Three things changed and are folded here:** (1) the fix is no longer new
> behaviour — `0003`'s refusal-contention rule already drops the wiki in the
> same mutation, for a NARROWER condition, so this spec now GENERALISES shipped
> code rather than introducing a mechanism; (2) `graph.py` no longer calls
> `invalidate_edge` — supersession invalidations ride the store's plan
> primitive, which *strengthens* the store-layer argument and moves its
> evidence; (3) `0020` excludes the wiki from principal-bearing recall
> entirely, so the exposure is now precisely the UNSCOPED path.
> **This spec is on `0022`'s critical path** (source revocation must reach what
> the model reads); `0022` §7b carries the drafted rider adding `revoked_source`
> to the trigger set, to land same-commit at that pair's acceptance.

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

## 2. Field contracts touched

| field | read / written | documented contract | consumers | change here |
|---|---|---|---|---|
| the compiled `wiki` cache (`get_wiki`/`set_wiki`) | read at recall, written at compile | a curated grounded view, recompiled every `wiki_recompile_after_writes` store versions | `recall()`'s grounded block (`__init__.py:595`) | DROPPED — not recompiled — whenever a trust-reducing invalidation commits |
| `invalidate_edge(edge_id, at, reason)` | written | deactivates an edge with a reason | `Memory.dispute()`/`correct()`, `lifecycle` expiry | the trust-reducing reasons additionally empty the user's wiki, in the SAME mutation |
| the supersession plan's `prior_invalidations` | written | the whole-outcome atomic plan (`0003` §4f) | `apply_supersession_plan` | same rule at the second invalidation site — this is where supersession now lives |
| `Provenance.disclosure` | UNCHANGED | written once at ingest | gate, render | untouched; see §4's corrected clause |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| the invalidation `reason` — **PRODUCERS: `Memory.dispute()`/`correct()` (host-initiated), `lifecycle` expiry/decay (the store's OWN clock-driven machinery), `apply_supersession_plan` (the store's own write path), and — post-`0022` — the revocation sweep** | no reason → treated as non-revoking, wiki retained (fail-OPEN on breadth, never on assertion) | an unknown reason string → **retained**, and the invariant that makes this safe is that the reason set is CLOSED at its producers, not validated here | a reason added by a future spec → the R5 registry check FAILS until the spec dispositions it | a caller passing `lapsed` for a genuine revocation to keep the wiki alive | the reason set is enumerated and REGISTERED (R5); a new reason cannot ship un-dispositioned |
| the wiki cache itself | absent → nothing to drop, no-op | — | — | a stale cache surviving a trust change | the whole point: the drop is unconditional on cache content |

### 2c-ii. Assertions about reach — RE-EXECUTED 2026-08-17

| assertion | command | result (run 2026-08-17) |
|---|---|---|
| the defect is STILL LIVE — a plain trust-reducing invalidation leaves the wiki served | build a store, `set_wiki`, `invalidate_edge(reason)`, `get_wiki` | wiki SURVIVES for `disputed`, `corrected` AND `superseded` — all three reproduce |
| the wiki still enters the grounded block | `grep -n "grounded_parts.append(wiki)" src/veracium/__init__.py` | `:595` (was `:225` at v1 — the citation drifted, the fact did not) |
| `compile.py` no longer carries the recompile gate | `grep -rn "wiki_recompile_after_writes" src/veracium/` | `config.py:40` (default 8) · `__init__.py:508` · `cli.py:207` (`10**9` once a wiki exists) · `selfcheck.py:43`; **`compile.py` does not appear** — v1's citation is stale |
| a wiki-drop ALREADY ships, on a narrower condition | `grep -n "DELETE FROM wiki" src/veracium/store/sqlite.py` | `:275` (in `invalidate_edge`, gated on `_edge_in_refusal`) and `:605` (in the supersession plan, gated on `touches_contention`) — **both `0003` refusal-contention rules** |
| `invalidate_edge` is still a choke point, but **`graph.py` is no longer among its callers** | `grep -rn "invalidate_edge(" --include=*.py src/veracium/` | `__init__.py:1181` (disputed) · `:1371` (corrected) · `lifecycle.py:53` (lapsed) · `:57` (decayed) · the `base.py`/`sqlite.py` definitions. Supersession moved into `apply_supersession_plan`'s `prior_invalidations` (`sqlite.py:326/505/550`) — **so the fix needs BOTH sites**, which v1 did not know |
| stored `disclosure` is still written in exactly one place | `grep -rn "disclosure\s*=" --include=*.py src/veracium/` | 7 hits, but only `ingest.py:181/199` WRITE a stored value; `scope_read.py:384` narrows a **`model_copy`** for the response and never persists; the rest are reads. The §4 correction stands, for a sharper reason |

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

**Where — TWO store-layer sites, corrected at the v2 refresh.** v1 said
`store.invalidate_edge` was a single choke point covering supersession via
`graph.py`. **Re-executed 2026-08-17, that is no longer true**: `graph.py` does
not call `invalidate_edge` at all; supersession invalidations now ride the
store's atomic plan (`apply_supersession_plan`'s `prior_invalidations`,
`sqlite.py:326/505/550`). The fix therefore lands at BOTH store sites:

* `invalidate_edge` — the `Memory.dispute()`/`correct()` and lifecycle path;
* `apply_supersession_plan` — the supersession path, inside the same transaction.

**This STRENGTHENS v1's argument rather than weakening it.** A fix in
`Memory.dispute()`/`correct()` would still miss supersession — the path an
attacker reaches — and now it would miss it via a *different* route than v1
described. The store layer is still not a stylistic preference; there are simply
two store-layer sites, and W2 is the check that proves the second one is covered.

**AND THE MECHANISM ALREADY SHIPS.** Both sites ALREADY execute
`DELETE FROM wiki` today (`sqlite.py:275` and `:605`) — gated on `0003`'s
refusal-contention condition (`_edge_in_refusal` / `touches_contention`). So this
spec does not introduce a mechanism, a code path, or a latency cost: **it
GENERALISES a shipped, reviewed drop from one trigger to the trust-reducing
set.** That is a materially smaller change than v1 proposed, and the reviewer
should hold it to that smaller claim.

**Which reasons drop the wiki:** `disputed` · `corrected` · `superseded` —
**and `revoked_source` when `0022` lands** (that spec's §7b carries the drafted
rider adding it here, to land same-commit at the `0022`/`0023` acceptance; this
spec does not define the reason, it reserves the seat).
**Not** `lapsed` / `decayed` — those are time-based staleness, not a revoked
trust decision, and dropping curated breadth on every decay cycle pays a real
cost for no trust gain. `absorbed_duplicate` is **arguable and currently
excluded**: the content survives in the surviving edge, so the wiki is not
serving anything revoked. Flagged rather than decided.

**Where the exposure now IS, after `0020` (v2 refresh).** Principal-bearing
recall EXCLUDES the compiled wiki entirely (`0020` §4d/V5 — not filtered, not
compiled), so a scoped read cannot serve a stale wiki at all. The surviving
exposure is therefore precisely the UNSCOPED path — which is every call today,
since no host passes a principal yet, and remains the default path afterwards.
The finding is unchanged in force; it is narrower in description, and stating
that narrowing is what keeps the claim honest.

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
| **W2** the drop covers the **supersession** path, not just the `Memory` verbs — and post-refresh that path is `apply_supersession_plan`'s `prior_invalidations`, NOT `graph.py` | `test_third_party_supersession_drops_the_wiki` (the second store site) | CI |
| **W3** staleness does **not** drop it | `test_decay_does_not_drop_the_wiki` — pins a deliberate exclusion so it cannot erode into "drop on everything" | CI |
| **W4** no LLM call on the drop path | `test_wiki_drop_makes_no_llm_call` — a `Complete` that raises if invoked | CI |
| **W5** the reason set is CLOSED and REGISTERED: every reason any producer can pass is dispositioned drop/retain, and a NEW reason fails the check until its spec dispositions it | `test_invalidation_reason_registry_is_total` — enumerate the reasons reachable at every producer (the §2c PRODUCERS row) and diff against the dispositioned set; an un-dispositioned reason FAILS rather than defaulting | CI |
| **W6** the generalisation does not REGRESS `0003`'s shipped refusal-contention drop — that condition still drops, in both sites | `test_refusal_contention_still_drops_the_wiki` (the shipped behaviour this spec widens, pinned so widening cannot silently replace it) | CI |

**W2 is the one that matters** and is the reason the fix sits in the store.
A fix in `Memory.dispute()`/`correct()` passes W1 and W3 and **fails W2
silently** — the tests would be green and the attacker path open.

---

## 5. Regime analysis

| regime | behaviour |
|---|---|
| library default (`wiki_recompile_after_writes = 8`) | breadth returns within 8 writes of the drop; the window where a revoked fact could have been asserted closes immediately |
| CLI path (`10**9` once a wiki exists) | the drop is effectively permanent until something else compiles — the honest cost, and W-Q2's subject |
| `selfcheck` (`= 1`) | recompiles on the next write; the drop is invisible |
| a store with NO wiki | the drop is a no-op; no path changes |
| principal-bearing recall (`0020`) | the wiki is excluded from the response ENTIRELY, so this regime is unaffected by the cache's state — the exposure is the unscoped regime |
| staleness (`lapsed`/`decayed`) | NO drop, deliberately — time-based staleness is not a revoked trust decision, and paying curated breadth on every decay cycle buys no trust |
| `absorbed_duplicate` | currently NO drop (the content survives in the surviving edge) — flagged, not decided (W-Q1) |
| post-`0022` `revoked_source` | drops, by the rider this spec reserves |

## 9. Brief for the external reviewer

The seam we are least certain of: **the reason set's closure**. The fix's whole
safety argument is "these reasons revoke, those merely age", and that partition
is defended by W5's registry rather than by anything structural — a future spec
that adds an invalidation reason and forgets to disposition it gets a FAILING
check, not a silent retention, but the check is the only thing standing there.
Attack that: is there a producer of invalidation reasons the §2c PRODUCERS row
misses? The `0022` sweep will add one, which is the first real test of the
mechanism.

Second seam: this spec makes the wiki fail closed but NOT incremental (§8's
stated limit). A large store loses its whole curated view because one fact was
disputed. We think that trade is correct and bounded; if you think the breadth
cost is understated, that is worth hearing before implementation rather than
after.

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
