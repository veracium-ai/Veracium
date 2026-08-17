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
| **Version** | **v3** — internal round 1 folded (research, 2026-08-17: R1 inverted cell, R2 the missed producer class, W-Q1 ruled) |
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
| the invalidation `reason` — **PRODUCERS: `Memory.dispute()`/`correct()` (host-initiated), `lifecycle` expiry/decay (the store's OWN clock-driven machinery), `apply_supersession_plan` (the store's own write path), and — post-`0022` — the revocation sweep** | no reason → treated as non-revoking, wiki retained (fail-OPEN on breadth, never on assertion) | an unknown reason string → **DROPS** (internal R1 — v2 had this INVERTED, and the inversion is worth naming: v2 said "retained (fail-OPEN on breadth, never on assertion)", which is backwards. Retaining on an unrecognised reason is precisely the assertion-side risk — if the unknown reason meant "revoked", a retained wiki serves revoked content. Dropping costs breadth only. A spec whose whole thesis is failing closed had a fail-OPEN cell in it) | a reason added by a future spec → drops at RUNTIME immediately, and the W5 registry check additionally FAILS until that spec dispositions it | a caller passing `lapsed` for a genuine revocation to keep the wiki alive | **two layers, in this order**: unknown-drops at runtime (the behaviour), then W5's registry (the process). v2 left W5 standing alone, which §9 itself called out as the only thing standing there |
| the wiki cache itself | absent → nothing to drop, no-op | — | — | a stale cache surviving a trust change | the whole point: the drop is unconditional on cache content |
| **`Edge.invalidation_reason` supplied AT CONSTRUCTION — the producer class v2 MISSED (internal R2; found by this spec's own §9 attack).** `invalidation_reason` is a settable field (`schema.py:249`) and `add_edge` accepts an Edge already carrying one, so the PUBLIC CONSTRUCTOR and the FORMAT-7 IMPORT round-trip both produce reason-bearing records that pass NEITHER drop site | — | — | — | a host constructing a born-invalid edge, or an import carrying one | **VERIFIED NON-TRANSITION, and the argument is now stated rather than assumed**: these producers create records that are ALREADY inactive; they never perform an active→inactive TRANSITION, and a record that was never active never contributed to a compiled wiki — no transition, no staleness. Import additionally cannot flip an existing record (its idempotency is exact-equality; a differing record REFUSES). **The defended invariant is therefore transition-form: every active→inactive transition passes the drop, and W7 enforces it structurally** |

### 2c-ii. Assertions about reach — RE-EXECUTED 2026-08-17

| assertion | command | result (run 2026-08-17) |
|---|---|---|
| the defect is STILL LIVE — a plain trust-reducing invalidation leaves the wiki served | build a store, `set_wiki`, `invalidate_edge(reason)`, `get_wiki` | wiki SURVIVES for `disputed`, `corrected` AND `superseded` — all three reproduce |
| the wiki still enters the grounded block | `grep -n "grounded_parts.append(wiki)" src/veracium/__init__.py` | `:595` (was `:225` at v1 — the citation drifted, the fact did not) |
| `compile.py` no longer carries the recompile gate | `grep -rn "wiki_recompile_after_writes" src/veracium/` | `config.py:40` (default 8) · `__init__.py:508` · `cli.py:207` (`10**9` once a wiki exists) · `selfcheck.py:43`; **`compile.py` does not appear** — v1's citation is stale |
| a wiki-drop ALREADY ships, on a narrower condition | `grep -n "DELETE FROM wiki" src/veracium/store/sqlite.py` | `:275` (in `invalidate_edge`, gated on `_edge_in_refusal`) and `:605` (in the supersession plan, gated on `touches_contention`) — **both `0003` refusal-contention rules** |
| `invalidate_edge` is still a choke point, but **`graph.py` is no longer among its callers** | `grep -rn "invalidate_edge(" --include=*.py src/veracium/` | `__init__.py:1181` (disputed) · `:1371` (corrected) · `lifecycle.py:53` (lapsed) · `:57` (decayed) · the `base.py`/`sqlite.py` definitions. Supersession moved into `apply_supersession_plan`'s `prior_invalidations` (`sqlite.py:326/505/550`) — **so the fix needs BOTH sites**, which v1 did not know |
| **`active=0` has exactly ONE writer, and BOTH drop sites funnel through it** (executed while folding internal R2 — stronger than the review's own "no third writer" formulation) | `grep -rn "SET active" --include=*.py src/veracium/` | a single hit: `sqlite.py:251`, inside `_invalidate_edge_row`, whose only callers are `invalidate_edge` (`:265`) and the supersession plan loop (`:551`). **This relocates the fix — see §4** |
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

**Where — ONE function, corrected AGAIN at v3.** Folding internal R2 turned up
a fact neither v1 nor v2 had: **`active=0` has exactly one writer in the
codebase** — `_invalidate_edge_row` (`sqlite.py:251`) — and BOTH store paths
call it (`invalidate_edge:265`, the supersession plan loop `:551`). So the fix
does not belong at two call sites that must each remember it; **it belongs
INSIDE `_invalidate_edge_row`, the single point every active→inactive
transition already passes.** It has the `reason` and the `user_id` in hand,
which is everything the rule needs.

This is strictly better than v2's two-site design, and the difference is not
stylistic: at two sites a THIRD invalidation path added later inherits nothing
and the defect returns silently; inside the sole writer, any future path
inherits the drop by construction. W7 then guards the one assumption that
makes it work — that the writer stays sole.

*(v2's reasoning, retained because it is what led here.)* **TWO store-layer
sites, corrected at the v2 refresh.** v1 said
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

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **W1** a revoking invalidation empties the wiki cache | `test_dispute_drops_the_wiki` — the measured reproducer becomes the fixture | CI |
| **W2** the drop covers the **supersession** path, not just the `Memory` verbs — and post-refresh that path is `apply_supersession_plan`'s `prior_invalidations`, NOT `graph.py` | `test_third_party_supersession_drops_the_wiki` (the second store site) | CI |
| **W3** staleness does **not** drop it | `test_decay_does_not_drop_the_wiki` — pins a deliberate exclusion so it cannot erode into "drop on everything" | CI |
| **W4** no LLM call on the drop path | `test_wiki_drop_makes_no_llm_call` — a `Complete` that raises if invoked | CI |
| **W5** the reason set is CLOSED and REGISTERED: every reason any producer can pass is dispositioned drop/retain, and a NEW reason fails the check until its spec dispositions it. **The registry is a CODE CONSTANT** (internal minor: v2 pointed at `schema.py:249`'s comment, and a comment cannot fail a check) | `test_invalidation_reason_registry_is_total` — enumerate the reasons reachable at every producer (the §2c PRODUCERS row) and diff against the dispositioned CONSTANT; an un-dispositioned reason FAILS rather than defaulting | CI |
| **W7** the transition invariant is STRUCTURAL: `_invalidate_edge_row` remains the SOLE writer of `active=0`, so every active→inactive transition inherits the drop (internal R2 — this is what makes the born-state producers safe, and it is enforced rather than grepped once) | `test_sole_active_zero_writer` — an AST sweep of `src/veracium/` asserting exactly one `SET active=0` writer and that it is `_invalidate_edge_row`; a second writer FAILS the build | CI |
| **W8** the `absorbed_duplicate` exclusion is PINNED (W-Q1, ruled by research 2026-08-17: absorption is trust-preserving by construction and the content stays backed by a live same-trust record, so the exclusion shelters nothing revoked) | `test_absorption_does_not_drop_the_wiki` — the W3 pattern, so a deliberate exclusion cannot erode into "drop on everything" | CI |
| **W6** the generalisation does not REGRESS `0003`'s shipped refusal-contention drop — that condition still drops, in both sites | `test_refusal_contention_still_drops_the_wiki` (the shipped behaviour this spec widens, pinned so widening cannot silently replace it) | CI |

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

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| **W-Q1** | Should `absorbed_duplicate` drop the wiki? | **RESOLVED 2026-08-17 (research, internal round 1): NO.** Absorption is trust-preserving by construction — the content stays backed by a live same-trust record — so the exclusion shelters nothing revoked. **The `0022` composition is closed**: the revocation sweep reaches absorbed contributors through the LEDGER, and a sole-basis survivor's retirement carries reason `revoked_source`, which drops the wiki through the seat this spec reserves. Pinned by W8. | `resolved` | research | done |
| **W-Q2** | Should the CLI's `10**9` recompile threshold be revisited, given it makes the breadth loss unbounded there? Out of scope for the fix; in scope for whether the trade is acceptable. | `deferred` | dev | own round |
