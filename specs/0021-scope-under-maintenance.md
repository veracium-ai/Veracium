# Feature spec: scope under derivation and consolidation (S2)

Spec-Status: draft
Spec-Requires: 0014, 0020

*Companion to 0020 (S1, read-time); the coupling is MUTUAL in
`Spec-Requires` (external F6) so acceptance is atomic. This spec owns the
WRITE- and MAINTAIN-time half: what scope means to every operation that
combines, retires, or re-renders records. v3 folds external round 1
(F1/F4/F5 land here).*

## 1. Problem and motivation

The benchmark campaign's direct contribution: **maintenance is the
laundering site** — the completed baselines program localized the
production systems' amplification to LLM cross-record consolidation. The
general form (N-3): *every LLM re-rendering the scope machinery doesn't
control is a laundering site.* A scope that recall enforces but derivation
ignores leaks across principals through synthesis.

0020 without this spec is a boundary with an unlocked back door. The
mutual requires-edge makes shipping them separately impossible to do by
accident (external F6).

## 2. The governing rule — identity partitioning is POLICY-INDEPENDENT (external F5)

External F5 exposed a real hole in v2: per-process READ policy plus
policy-conditional maintenance meant an honest unscoped host could run
maintenance on a shared store and co-consolidate A and B while a scoped
host assumed isolation. **The enforceable model, chosen: maintenance
partitions by RESOLVED IDENTITY, always, policy or no policy.** Policy is
a read-side concept (0020); no process's configuration can change what the
store MERGES. Consequences, stated:

- W1 becomes unconditional — no host's missing policy defeats it.
- **Behaviour change, disclosed:** an identity-BEARING store gets
  partitioned consolidation even if no host ever configures a policy
  (previously global). Stores with NO identities are byte-identical to
  today (the migration invariant) — partitioning needs identities to
  partition on, so the unidentified world never changes.
- **Reversibility, restated honestly (the reviewer's cell):**
  "config-only reversibility" applies to READ visibility only (0020 §7).
  Maintenance conduct is not configuration, and consolidation's effects —
  deleted inputs, persisted derivatives — are PERMANENT once run. There is
  no un-consolidate; there never was.

## 2b. Field contracts touched

| field | read / written | documented contract | consumers | change here |
|---|---|---|---|---|
| consolidation candidate selection (`lifecycle.consolidate`) | changed | **today: ONE global cold pool, one min-batch threshold, one LLM call, one whole-set claim (external F4 — v2's "groups by trust class today" claim was FALSE for consolidation; that idiom is absorption's)** | maintenance | the per-scope construction of §4b — partition, per-scope thresholds, per-scope ops |
| consolidation output identity (`_derive_output_metadata`) | changed — IMPLEMENTATION OBLIGATION (external F1) | **today: copies `inputs[0].provenance` WITHOUT clearing `origin`/`source_id` — a mixed A+B derivative claims identity A (reviewer-executed)** | scope membership, 0006 identity | **outputs CLEAR inherited identity: `origin=None` (resolves local at read, I9), `source_id=None` — store-authored means store-identified.** The reviewer's mixed-scope probe is the regression (W8) |
| write-time absorption (`graph.py`) | changed | same-class subsumption merge | apply_supersession | partition: a cross-scope prior is NOT an absorption candidate (extends the shipped same-class idiom — this one IS absorption's, verified) |
| supersession | UNTOUCHED | 0003 ladder, store-global | apply_supersession | scope-BLIND: truth is global; visibility is 0020's N-2 |
| 0012 reinforcement | untouched | mutates nothing | — | scope-safe by construction |
| lifecycle expiry / staleness | untouched | per-edge aging | — | scope-blind, trivially |
| 0014 contribution ledger | READ, load-bearing | contributor rows key the digested resolved pair; exact-set completeness at write | scope membership (0020 §4a-iii) | the MEMBERSHIP join; the CROSS-scope reconstruction use remains stated-not-built (v1 refuses cross-scope derivation) |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | cell | governing rule |
|---|---|---|
| identity fields on merge candidates — **PRODUCERS: hosts AND the store's own outputs** | absent identity | HOST-produced identity-less records form the closed shared pool (merge only among themselves; nothing crosses INTO a scope). STORE-produced derivatives take the 0020 §4a-iii evidence hierarchy; **UNRESOLVED derivatives are never merge candidates in any pool (W9)** |
| a writer omitting identity to make content mergeable everywhere | adversarial | achieves the opposite: the shared pool only |
| pre-0021 store state (external F1's populations) | legacy | LEGACY derivatives (identity copied from `inputs[0]`, pre-fix) are detected by the NORMATIVE `is_legacy_derivative` predicate (0020 §4a-ii's resolver — system-authored + consolidation-shaped `evidence_ref` + a still-groupable identity; vectored) and treated as UNRESOLVED — never trusted as scope-A evidence merely because they claim A |
| imported derivatives | portability | the ledger is LOCAL and does not travel (0014): an imported derivative arrives without membership evidence → UNRESOLVED (the reviewer's export/import probe). Materializing membership at export is a recorded widening (FORMAT change, not v1) |
| in-flight pre-feature operations at upgrade | recovery | 0010 recovery completes or abandons them under its own rules. **CORRECTED (external R2-3, reviewer-executed): recovery CANNOT clear an already-OUTPUTS_DURABLE output — it was written pre-feature with the copied identity and recovery only finalizes.** Such outputs keep their stale identity and are caught by the NORMATIVE legacy-derivative predicate (0020 §4a-ii's resolver — by shape, not by recovery); membership → UNRESOLVED. GENERATING-state pre-feature ops that recovery abandons leave no output (0010). Recovery never fabricates membership |
| host policy enabling cross-scope merge (future) | out of v1 | v1 REFUSES cross-scope merges outright; the recorded future form is intersection-scoped visibility with empty-intersection refusal |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | expected result |
|---|---|---|
| absorption groups by trust class today (the idiom §4c extends) | `grep -n "same_class\|never cross trust classes" src/veracium/graph.py` | the class-partitioned candidate loops |
| **consolidation is ONE GLOBAL POOL today (external F4 — the claim v2 got wrong, asserted correctly now)** | `grep -n "cold = \|consolidate_min_batch" src/veracium/lifecycle.py` | one `cold` list, one threshold, no grouping |
| **outputs copy the first input's identity today (the W8 defect)** | `grep -n "inputs\[0\].provenance" src/veracium/store/sqlite.py` | `_derive_output_metadata`'s base line |
| the ledger keys contributors by resolved identity | `grep -n "identity_digest" src/veracium/store/sqlite.py \| head -3` | the 0014 join |
| the ledger is local-only | `grep -n "settled outputs portable" specs/0014-maintenance-attribution.md \| head -1` | the locality rule the import population inherits |

*(Re-run at implementation; commands recorded per the 0005 rule.)*

## 3. The operation matrix — TOTAL, one row per combining operation

| operation | timing | scope rule | why |
|---|---|---|---|
| absorption | write-time | partition by resolved identity (policy-independent) | a merge inherits lineage |
| supersession | write-time | scope-BLIND (global truth) | per-scope truths would diverge |
| reinforcement | write-time | no-op by construction (0012) | mutates nothing |
| consolidation | maintain-time | partition (§4b); cross-scope co-consolidation REFUSED; outputs cleared-identity + ledger membership (W7/W8) | the amplification site |
| expiry / decay / staleness | maintain-time | scope-blind | no combination occurs |
| wiki compilation | maintain-time | v1: store-wide compile unchanged; the wiki never reaches principal-bearing responses (0020 §4d); per-scope compilation the recorded widening | the second synthesis path |

**Totality is MECHANICAL (external F4): the code carries a
`COMBINING_SITES` registry (the 0014 `CONSUMPTION_SITES` precedent) and a
generated manifest (`specs/generated/0021-combining-sites.md`); a
combining code path absent from the registry fails
`test_scope_operation_matrix_is_total`.** "Combining" is defined for the
registry: any operation that writes a record derived from, or mutates a
record because of, MORE THAN ONE existing record.

## 4. Behaviour

### 4a. Output identity (external F1 — implementation obligation)

`_derive_output_metadata` clears inherited identity on every consolidation
output: `origin=None`, `source_id=None` on the derived provenance —
store-authored means store-identified; membership travels through the
ledger, never through a copied identity. The reviewer's two probes are the
regressions: (1) mixed-scope inputs → output identity is CLEARED, not A's
(W8); (2) export→import of a derivative → UNRESOLVED, never
false-identity-A (W9's import cell).

### 4b. Per-scope consolidation (external F4 — specified against the real shape)

Today's `consolidate` builds one global cold pool with one threshold and
one claim. The v1 construction replaces it:

1. **Partition** the cold candidates by membership evidence: one pool per
   resolved scope identity; one pool for the host-produced unidentified;
   UNRESOLVED derivatives excluded from every pool (W9).
2. **Thresholds are PER POOL:** `consolidate_min_batch` applies to each
   pool independently — four A records + four B records with
   `min_batch=8` is a NO-OP (the reviewer's cell, answered; no global
   trigger exists).
3. **Deterministic order:** eligible pools consolidate in sorted order of
   their scope's identity digest (the unidentified pool last) — one 0010
   operation PER POOL, each with its own claim, lease, crash-safety, and
   recovery; a pool's failure or contention affects no other pool.
4. **Continuation and partial success (external R2-5, the frozen
   contract):** pool failures are CAUGHT AND CONTINUED — a later pool
   always runs regardless of an earlier pool's outcome. The RESULT SCHEMA,
   frozen: `{"pools": {<scope-digest>: {"status": "ok" | "failed" |
   "contended" | "below-threshold", "consolidated": int, "into": int,
   "error": str?}}, "totals": {"consolidated": int, "into": int,
   "pools_ok": int, "pools_failed": int}, "recovered": int}` — "A
   committed, B failed, C/D ran anyway" is representable and tested by a
   FAULT-INJECTION MATRIX over every pool phase (claim / generate / write
   / finalize) × later-pool continuation (W12). The CARRIER SWEEP, per the
   found-in-fix rule: `Memory.maintain`'s public return carries the schema
   verbatim; the audit sink receives one event per pool op (the existing
   per-op machinery — nothing aggregated away); docs/api.md documents the
   schema; telemetry is UNCHANGED in v1 (no new fields — the 0019
   deferral pattern, recorded).
5. **Concurrency:** two hosts consolidating concurrently contend per-pool
   through the existing 0010 claim machinery — no new locking; a contended
   pool reports `"contended"` and later pools continue.
6. **Recovery of pre-feature ops:** §2c's corrected in-flight row —
   recovery finalizes what is durable (stale identity, caught by the
   legacy predicate → UNRESOLVED) and abandons what is not; outputs enter
   the evidence hierarchy like any others.

### 4c. Absorption partition

Extends the shipped same-class idiom (verified at 2c-ii): the candidate
loops additionally require same-scope membership evidence. A cross-scope
or UNRESOLVED prior accumulates as a separate edge — today's cross-class
behaviour, extended.

### 4d. Mixed-version shared stores (external R2-6)

No schema/format/feature marker prevents a PRE-0021 process from opening
the same store during a rolling upgrade and running today's GLOBAL
consolidation — new processes partition; old ones do not. **W1's claim is
therefore NARROWED to stores operated exclusively by 0021-capable
processes, and the deployment requirement is stated plainly: upgrade
every writer before relying on the partition invariant** (reads are safe
throughout — a pre-0021 global merge produces a mixed derivative that the
legacy/evidence machinery classifies UNRESOLVED, so scoped reads stay
fail-closed even during the window; what is lost is the merge-prevention
half, not the visibility half). **The ENFORCEMENT upgrade is recorded
(Q4): a store-version bump refusing pre-0021 writers — it rides the 0018
D2 breaking window (SCHEMA v8) rather than minting its own break; until a
release takes it, W1 carries the operational narrowing in its own text.**

## 5. Regime analysis

| regime | behaviour |
|---|---|
| identity-free store | byte-identical to today, policy or none (the migration invariant) |
| identity-bearing store, NO policy anywhere | **consolidation partitions anyway (§2 — the disclosed behaviour change)**; recall unchanged (0020: no policy → unscoped views) |
| mixed scopes, maintenance runs | each pool consolidates internally per §4b; cross-scope pairs untouched |
| four A + four B, min_batch=8 | NO-OP — thresholds are per-pool |
| legacy/imported/recovered derivatives | UNRESOLVED: excluded from every pool, invisible to scoped principals (0020), visible unscoped; remedy = re-derivation/restatement |
| repeated cross-scope restatement of one value | parallel per-scope edges; no merge, no laundering; the D-extension cross-principal probe measures exactly this |
| pool B's LLM call raises mid-run | A's commit stands (permanent); B reports "failed" with the error; C/D run anyway; the schema carries all four (R2-5) |
| a pre-0021 process consolidates during a rolling upgrade | its global merge produces a mixed derivative → UNRESOLVED at read (fail-closed); the partition half of W1 is narrowed per §4d until every writer upgrades |

## 6. Invariants and executable checks — REQUIRED, blocking

**Status: STAGE-5 OBLIGATIONS — none exists yet (draft).**

| invariant | executable check |
|---|---|
| W1 consolidation never merges across scopes — policy-independent, **on stores operated exclusively by 0021-capable processes (§4d — the mixed-version narrowing; scoped READS stay fail-closed even during a rolling upgrade)** | `test_consolidation_partitions_by_scope` *(offline)* |
| W2 absorption never absorbs across scopes | `test_absorption_partitions_by_scope` *(offline)* |
| W3 the operation matrix is total via the `COMBINING_SITES` registry + generated manifest | `test_scope_operation_matrix_is_total` *(offline)* |
| W4 host-produced unidentified records merge only among themselves | `test_unidentified_pool_is_closed` *(offline)* |
| W5 supersession stays scope-blind | `test_supersession_is_scope_blind` *(offline)* |
| W6 value-level cross-principal leak probe | `test_no_cross_principal_leak_through_maintenance` *(live / D-ext form)* |
| W7 a derivative's membership comes from the ledger evidence hierarchy | `test_derivative_inherits_partition_scope` *(offline)* |
| W8 output identity CLEARED — the reviewer's mixed-scope probe verbatim (external F1) | `test_output_identity_cleared` *(offline)* |
| W9 UNRESOLVED fail-closed, per population (legacy / imported / recovered / incomplete-ledger): excluded from every merge pool, invisible scoped, visible unscoped | `test_unresolved_populations_fail_closed` *(offline)* |
| W10 per-pool thresholds: the 4A+4B/min-8 no-op cell + per-pool trigger independence | `test_per_scope_thresholds` *(offline)* |
| W11 partitioning is policy-independent: an identity-bearing store with NO policy partitions identically to the same store with one | `test_partition_is_policy_independent` *(offline)* |
| W12 the fault-injection matrix (R2-5): every pool phase × later-pool continuation; the frozen result schema representable and returned verbatim by `Memory.maintain` | `test_per_pool_fault_matrix` *(offline)* |

## 7. Failure modes and reversibility

Per-pool ops fail independently under 0010's crash machinery. **No
config-only reversibility exists for maintenance effects (external F5):**
consolidation deletions and derivatives are permanent; disabling READ
policy changes visibility only. The refusal-first posture means every
widening (cross-scope merge, per-scope wikis, membership export) is a spec
amendment, never a silent relaxation.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `lifecycle.consolidate` | the §4b per-pool construction + per-pool reporting |
| `store/sqlite._derive_output_metadata` | identity clearing (W8) |
| `graph.py` (absorption) | the same-scope candidate requirement |
| `COMBINING_SITES` + `specs/generated/0021-combining-sites.md` | the mechanical totality carrier (F4) |
| docs | the behaviour change for identity-bearing stores; the UNRESOLVED operator remedies |

### 7b. Cross-spec carriers

| spec | touchpoint | disposition |
|---|---|---|
| 0020 | **MUTUAL `Spec-Requires` (external F6)** — atomic acceptance, the 0016/0018 precedent | 0020's claim is CONDITIONAL on this spec wherever maintenance runs; neither accepts alone |
| 0014 | the ledger | the MEMBERSHIP join is load-bearing v1 (0020 §4a-iii); cross-scope reconstruction stated-not-built |
| 0010 | per-pool operations | each pool's op uses the shipped claim/lease/recovery machinery unchanged |
| 0006 | output identity | cleared-identity outputs resolve to the local singleton at read (I9) — the store-authored shape 0020's hierarchy expects |
| the consolidation-audit direction | same code path | sequence together when it lands |

## 8. Claims and limits

**Claim:** after this spec, on a store operated exclusively by
0021-capable processes, no maintenance or write-time combining operation
moves content across scope boundaries, under ANY process's configuration;
derivatives carry honest membership evidence or fail closed; scoped READS
are fail-closed even under mixed-version operation (§4d); scope survives
synthesis.

**Limits:** C2 honesty as ever (isolation, not authentication);
host-produced unidentified material is uniformly shared; UNRESOLVED
derivatives are a real operator cost (invisible to scoped principals until
re-derived) — the fail-closed price, stated; the wiki remains store-wide
(excluded, not scoped); maintenance effects are permanent.

## 9. Brief for the external reviewer

The seam we are LEAST certain of: **the UNRESOLVED class's operator
economics.** Fail-closed is clearly right against silent sharing, but on a
real upgraded store EVERY pre-0021 derivative lands UNRESOLVED at once —
invisible to every scoped principal until re-derived. If you can
construct a store state where that cliff pushes an operator toward the
unscoped surface as a workaround (defeating the boundary socially rather
than technically), we want that finding now. Second seam: the legacy
DETECTION shape in §2c (store-authored `evidence_ref` + non-cleared
identity) — if a host-written record can imitate that shape and thereby
get its identity treated as unreliable (a self-inflicted demotion, so
restrict-only holds, but a correctness wart), name it.

## 10. Open questions

| # | question | state |
|---|---|---|
| Q1 | cross-scope merge: refusal vs intersection | RESOLVED for v1: refusal; intersection is the recorded widening |
| Q2 | per-scope wiki compilation | DEFERRED, cost-gated (0020 §4d) |
| Q3 | membership materialization at export (FORMAT change) | DEFERRED — recorded widening; would move imported derivatives out of UNRESOLVED |
| Q4 | mixed-version ENFORCEMENT: the pre-0021-writer refusal bump | DEFERRED to the 0018 D2 breaking window (SCHEMA v8) — until then W1 carries the §4d operational narrowing |
