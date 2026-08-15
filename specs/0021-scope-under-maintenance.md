# Feature spec: scope under derivation and consolidation (S2)

Spec-Status: draft
Spec-Requires: 0014, 0020

*Companion to 0020 (S1, read-time). This spec owns the WRITE- and
MAINTAIN-time half: what scope means to every operation that combines,
retires, or re-renders records. Source: research's design proposal §S2 +
the ratified operation matrix (dev cell, §7 addendum @ 9f6fb286).*

## 1. Problem and motivation

The benchmark campaign's direct contribution: **maintenance is the
laundering site** — both historical advisories were maintenance-time
laundering, and the completed baselines program localized the production
systems' amplification to LLM cross-record consolidation. The general
form (ratified at N-3): *every LLM re-rendering the scope machinery
doesn't control is a laundering site.* A scope that recall enforces but
derivation ignores leaks across principals through synthesis — the
GHSA-hcj3 shape with scope in place of trust.

0020 without this spec is a boundary with an unlocked back door. They are
separable specs but ONE release story (§7b).

## 2. Field contracts touched

| field | read / written | documented contract | consumers | change here |
|---|---|---|---|---|
| consolidation candidate selection | changed | today: store-wide within trust class | maintenance | **partitions by scope by default** — merge candidates are drawn within a scope; cross-scope records do not co-consolidate (v1: cross-scope merge REFUSED outright — Q4's simpler arm, strictly widenable later per the 0011 §3 pattern) |
| write-time absorption (graph.py) | changed | same-class subsumption merge | apply_supersession | same partition: a cross-scope prior is NOT an absorption candidate (the incoming and prior accumulate as separate edges — today's cross-class behaviour, extended to scope) |
| supersession | UNTOUCHED | 0003 ladder, store-global | apply_supersession | **scope-blind by design** (0020 §3): truth is global; a newer value supersedes per authority regardless of scope; VISIBILITY of the result is 0020's N-2 |
| 0012 reinforcement | untouched | mutates nothing | — | scope-safe BY CONSTRUCTION (a restatement is its own edge with its own identity); stated so the matrix is total |
| lifecycle expiry / staleness | untouched | per-edge aging | — | scope-blind, trivially (no cross-record combination) |
| 0014 contribution ledger | read only | contributor rows key the digested resolved pair | audit | already scope-attributable with shipped machinery — the ledger join is STATED here, not built: a cross-scope derivation (if ever enabled) is reconstructable from contributor identities |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | cell | governing rule |
|---|---|---|
| identity fields on merge candidates | absent identity | absent-identity records form their OWN non-scope: they co-consolidate with each other (today's behaviour among unidentified records) but never absorb into, nor absorb, an identified scope's records — absent==absent is never SAME-scope for restriction-exception purposes (0020 C3), but unidentified material also must not launder INTO a scope |
| a writer omitting identity to make content mergeable everywhere | adversarial | it achieves the opposite: absent-identity records reach only the shared-visible pool and merge only among themselves; nothing crosses INTO a scope |
| host policy enabling cross-scope merge (future) | out of v1 | v1 REFUSES cross-scope merges outright; the recorded future form is intersection-scoped visibility (`min` over parents, the 0014 shape) with empty-intersection → refusal — restrict-only either way |

## 3. The operation matrix — TOTAL, one row per combining operation

| operation | timing | scope rule | why |
|---|---|---|---|
| absorption | write-time | partition: cross-scope priors are not candidates | a merge inherits lineage; cross-scope inheritance is laundering |
| supersession | write-time | scope-BLIND (global truth) | per-scope truths would diverge; visibility is 0020's job |
| reinforcement | write-time | no-op by construction (0012) | mutates nothing |
| consolidation | maintain-time | partition; cross-scope co-consolidation REFUSED in v1 | the amplification site itself |
| expiry / decay / staleness | maintain-time | scope-blind | no combination occurs |
| wiki compilation | maintain-time | v1: unchanged store-wide compile; the wiki never reaches principal-bearing recall (0020 §4d). Per-scope compilation is THE recorded widening, cost-gated | the second synthesis path |

Totality is the invariant: a NEW combining operation must add its row
before it ships (`test_scope_operation_matrix_is_total` pins the list
against the code's combining sites).

## 4. Behaviour

Consolidation candidate grouping gains the scope key exactly where it
groups by trust class today — the shipped idiom ("identity merges never
cross trust classes") extended by one key. No new machinery; a partition
key on existing loops.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| all records one scope (or none identified) | byte-identical to today |
| mixed scopes, maintenance runs | each scope consolidates internally; cross-scope pairs untouched (parallel edges persist — 0020 renders them per policy) |
| repeated cross-scope restatement of one value | accumulates as parallel per-scope edges; no merge, no laundering; the D-extension cross-principal probe measures exactly this |

## 6. Invariants and executable checks — REQUIRED, blocking

**Status: STAGE-5 OBLIGATIONS — none exists yet (draft).**

| invariant | executable check |
|---|---|
| W1 consolidation never merges across scopes (v1 refusal) | `test_consolidation_partitions_by_scope` |
| W2 absorption never absorbs across scopes | `test_absorption_partitions_by_scope` |
| W3 the matrix is total against the code's combining sites | `test_scope_operation_matrix_is_total` |
| W4 absent-identity records merge only among themselves | `test_unidentified_pool_is_closed` |
| W5 supersession stays scope-blind (a scoped store's lifecycle equals an unscoped clone's) | `test_supersession_is_scope_blind` |
| W6 value-level cross-principal leak probe (the D-extension form): a value written under A never surfaces in B's post-maintenance recall | `test_no_cross_principal_leak_through_maintenance` |

## 7. Failure modes and reversibility

Additive partition keys; no schema change; disabling scope policy restores
today's merge behaviour. The refusal-first v1 posture means every future
widening (intersection-scoped merge, per-scope wikis) is a spec amendment
with its own review, never a silent relaxation.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `graph.py` (absorption), consolidation path | the partition key |
| `compile.py` | untouched in v1 (the recorded widening lives here if ever) |
| docs | the one-release-story note with 0020 |

### 7b. Cross-spec carriers

| spec | touchpoint | disposition |
|---|---|---|
| 0020 | the boundary this spec closes the back door of | ships in the SAME release (one story) or 0020 ships with the §4d wiki exclusion carrying the whole synthesis burden — stated so partial shipping is a decision, not an accident |
| 0014 | the ledger join for any future cross-scope derivation | stated, not built |
| the consolidation-audit direction (0019 §8 successor) | same code path | sequence together when that work lands — one consolidation story covering grounding AND scope |

## 8. Claims and limits

**Claim:** after this spec, no maintenance or write-time combining
operation moves content across scope boundaries; scope survives synthesis.

**Limits:** same C2 honesty as 0020 (isolation, not authentication);
absent-identity material is uniformly shared and unprotected; the wiki
remains store-wide (excluded from scoped recall, not scoped itself).

## 9. Brief for the external reviewer

n/a — internal review first; completed at external packaging.

## 10. Open questions

| # | question | state |
|---|---|---|
| Q1 | cross-scope merge: refusal vs intersection | RESOLVED for v1: refusal (Q4 of the design round); intersection is the recorded widening |
| Q2 | per-scope wiki compilation | DEFERRED, cost-gated (0020 §4d) |
