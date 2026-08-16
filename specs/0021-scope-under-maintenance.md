# Feature spec: scope under derivation and consolidation (S2)

Spec-Status: accepted
Spec-Requires: 0009, 0014, 0016, 0018, 0019, 0020

*Companion to 0020 (S1, read-time); the coupling is MUTUAL in
`Spec-Requires` (external F6) so acceptance is atomic. This spec owns the
WRITE- and MAINTAIN-time half: what scope means to every operation that
combines, retires, or re-renders records. v3 folds external round 1
(F1/F4/F5 land here).*

## 1. Problem and motivation

> **Amended per paper-2 registration A14 (2026-08-16):** the benchmark
> localization claimed in this section is withdrawn to exploratory
> association pending a counterbalanced rerun; the advisories
> (GHSA-r7j7 / GHSA-hcj3) and the laundering shape remain the standing
> motivation. The V/W invariant surfaces and the acceptance evidence are
> unaffected — this is a motivation-prose correction only.

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
  (previously global). Stores with NO identities: STORED STATE and the
  preserved top-level result VALUES are identical to today — **the result
  SHAPE is not (external R4-2, executed against our own robustness
  checker: the additive `pools`/`pools_ok`/`pools_failed` keys are new
  for every store, and `tests/robustness/invariants.py` as shipped
  REJECTS the dict-valued key). Every identity-free "byte-identical"
  claim is narrowed to state-and-values; the carrier sweep (§4b) now
  names the robustness checker, the exact-result lifecycle tests, and
  docs/api.md as implementation-obligation updates.**
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
| 0014 contribution ledger | READ + WRITTEN (import path) | contributor rows key the digested resolved pair; exact-set completeness at write | scope membership (0020 §4a-iii) | the MEMBERSHIP join, over TRANSITIVELY CLOSED row sets (R7-1); the amended 0009 primitive WRITES the two plan sites (`imported-absorption` direct links + `scope-attribution` derived rows — the §7b SITE MATRIX is the one source, R11-1); executable reconstruction (R7-4 swept the stale "stated-not-built" phrase this cell carried) |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | cell | governing rule |
|---|---|---|
| identity fields on merge candidates — **PRODUCERS: hosts AND the store's own outputs** | absent identity | HOST-produced identity-less records form the closed shared pool (merge only among themselves; nothing crosses INTO a scope). STORE-produced derivatives take the 0020 §4a-iii evidence hierarchy; **UNRESOLVED derivatives are never merge candidates in any pool (W9)** |
| a writer omitting identity to make content mergeable everywhere | adversarial | achieves the opposite: the shared pool only |
| pre-0021 store state (external F1's populations) | legacy | LEGACY derivatives (identity copied from `inputs[0]`, pre-fix) are detected by the NORMATIVE `is_legacy_derivative` predicate (0020 §4a-ii's resolver — system-authored + consolidation-shaped `evidence_ref` + a still-groupable identity; vectored) and treated as UNRESOLVED — never trusted as scope-A evidence merely because they claim A |
| imported derivatives | portability | the ledger is LOCAL and does not travel (0014): an imported CONSOLIDATION derivative arrives without membership evidence → UNRESOLVED. **Imported ABSORPTION survivors take the EXECUTABLE reconstruction rule (0020 §4a-iii v9): PRE-COMMIT (refusal leaves the destination byte-identical — R7-2), structured-`absorbed_by_id`-first with the DECIDABLE legacy rule (last tag governs and is the only one that must resolve; id-set candidate matching; zero/multiple candidates → whole-import REFUSAL), TRANSITIVE (ancestor digests propagate to every absorber — R7-1), COMPLETE rows (typed contributor_ref binding + evidence digest + per-row INJECTIVE op keys, the framed-digest form — R8-3/R9-2); `import_memory` writes BOTH plan sites through the amended 0009 primitive (direct links at `imported-absorption`, transitive copies at `scope-attribution` — the §7b SITE MATRIX, R11-1) — attribution only, no reversal (R6-2).** Materializing full membership at export stays a recorded widening; the LINKAGE field is the FORMAT-7 rider deriving from the ledger's contributor link (§7b — R8-2) |
| in-flight pre-feature operations at upgrade | recovery | 0010 recovery completes or abandons them under its own rules. **CORRECTED (external R2-3, reviewer-executed): recovery CANNOT clear an already-OUTPUTS_DURABLE output — it was written pre-feature with the copied identity and recovery only finalizes.** Such outputs keep their stale identity and are caught by the NORMATIVE legacy-derivative predicate (0020 §4a-ii's resolver — by shape, not by recovery); membership → UNRESOLVED. GENERATING-state pre-feature ops that recovery abandons leave no output (0010). Recovery never fabricates membership |
| host policy enabling cross-scope merge (future) | out of v1 | v1 REFUSES cross-scope merges outright; the recorded future form is intersection-scoped visibility with empty-intersection refusal |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | expected result (AS RE-RUN, 2026-08-16, at slice-C implementation) |
|---|---|---|
| absorption groups by trust class today (the idiom §4c extends) | `grep -n "same_class\|never cross trust classes" src/veracium/graph.py` | UNCHANGED — the class-partitioned candidate loops (`graph.py:105` the stated rule, `:241` the `same_class` construction, `:256`/`:297` the two loops). **Post-implementation the absorption loop additionally consults `_absorption_scope_gate` (§4c); the reinforcement loop does not need it — its action is persist-incoming-untouched, which is already "accumulates as a separate edge".** |
| **consolidation is ONE GLOBAL POOL today (external F4 — the claim v2 got wrong, asserted correctly now)** | `grep -n "cold = \|consolidate_min_batch" src/veracium/lifecycle.py` | **MOVED BY THIS IMPLEMENTATION.** Pre-slice-C: one `cold` list, one threshold, no grouping — the premise §4b was specified against. Post-slice-C the same command shows the ONE `cold` list still built once (`lifecycle.py:269`) and the threshold applied PER POOL (`:275`, `len(members) < config.consolidate_min_batch`) after `partition_cold`. The pre-state is recorded as historical, not re-asserted. |
| **outputs copy the first input's identity today (the W8 defect)** | `grep -n "inputs\[0\].provenance" src/veracium/store/sqlite.py` | **MOVED BY THIS IMPLEMENTATION.** `_derive_output_metadata`'s base line is still there (`sqlite.py:1460`) — `base` remains the source of the non-identity derived fields — but the `model_copy` below it now sets `origin=None, source_id=None`, so the copy no longer carries identity. The second hit (`:1471`) is the comment recording exactly that. |
| the ledger keys contributors by resolved identity | `grep -n "identity_digest" src/veracium/store/sqlite.py \| head -3` | UNCHANGED IN SHAPE, line numbers moved with the D2 train — the 0014 join (`:631` the import of the shipped digest primitives, `:651` the derivation, `:675` the INSERT column list) |
| the ledger is local-only | ~~`grep -n "settled outputs portable" …`~~ → **CORRECTED at re-run: that phrase does not appear in 0014 and the command returned EMPTY.** The rule's actual carrier: `grep -n "Store-local" specs/0014-maintenance-attribution.md` | `0014:567` — "The ledger is **Store-local metadata** … never surfaced to the model … and never exported (§4e)": the locality rule the import population inherits. (A grep asserting a phrase that was never written is a non-biting assertion; recorded per the 0005 execute-shipped-claims rule rather than quietly fixed.) |
| **the absorption draft ALREADY carries the typed contributor fields (R8-1's column populates from shipped data)** | `grep -n "contributor_type=\"edge\", contributor_id=prior.id" src/veracium/graph.py` | UNCHANGED — the `ContributionDraft` line (`graph.py:321`). **The D2 train already stopped the drop: `_write_contribution` persists both columns on every new native absorption row.** |
| **no shipped path physically prunes an absorbed edge (the R8-1 retention premise)** | `grep -rn "DELETE FROM edges" src/veracium/` | UNCHANGED — EMPTY. Expiry invalidates (`invalidate_edge`), consolidation deletes EPISODES, user erasure deletes per-user tables wholesale (ledger included, mooting membership). The premise still holds, so `apply_retention_prune_plan` stays FUTURE and W16/W18's post-prune halves stay deferred. |
| **the accepted op_key index admits one row per key (R8-3's IntegrityError)** | `grep -n "ix_contribution_ledger_op_key" -A 2 src/veracium/store/schema_version.py` | UNCHANGED — `schema_version.py:267-269`, `CREATE UNIQUE INDEX ix_contribution_ledger_op_key ON contribution_ledger(op_key) WHERE op_key IS NOT NULL` |
| **the shipped per-row canonical key idiom the amendment follows** | `grep -n "def consolidation_op_key" -A 3 src/veracium/contribution.py` | UNCHANGED — `contribution.py:137-140`, `{operation_id}:{output_index}:{contributor_type}:{contributor_id}` |

*(Commands recorded per the 0005 rule. RE-RUN at slice-C implementation as
this section requires; three results moved — two because this implementation
moved them, and one because the command was never biting — and each is
recorded above rather than silently refreshed.)*

## 3. The operation matrix — TOTAL, one row per combining operation

| operation | timing | scope rule | why |
|---|---|---|---|
| absorption | write-time | partition by resolved identity (policy-independent) | a merge inherits lineage |
| supersession | write-time | scope-BLIND (global truth) | per-scope truths would diverge |
| reinforcement | write-time | no-op by construction (0012) | mutates nothing |
| consolidation | maintain-time | partition (§4b); cross-scope co-consolidation REFUSED; outputs cleared-identity + ledger membership (W7/W8) | the LLM cross-record synthesis site (§1's A14 amendment: the benchmark's *amplification* localization is withdrawn to exploratory; the rule in this row is unaffected) |
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
4. **Continuation and partial success (R2-5, REVISED at external R3-4/
   R3-5): pool failures are CAUGHT AND CONTINUED, and the result is an
   ADDITIVE SUPERSET of today's shape** — the existing top-level keys
   `{"consolidated", "into", "recovered"}` are PRESERVED VERBATIM as the
   rolled-up totals (an identity-free store's values are identical to
   today's, and the SHIPPED TELEMETRY MAPPING — which reads exactly those
   keys — keeps working UNCHANGED, by construction), with the new keys
   added beside them: `{"pools": {<key>: {"status": "ok" | "failed" |
   "contended" | "below-threshold", "consolidated": int, "into": int,
   "error": str?}}, "pools_ok": int, "pools_failed": int}`. **The pool
   key is the scope's identity digest, or the RESERVED literal
   `pool:unidentified` for the shared pool (external R3-4 — 0006 digests
   a source-less identity to None, so the pool needs a non-digest key;
   the colon makes collision impossible).** "A committed, B failed, C/D
   ran anyway" is representable and tested by the FAULT-INJECTION MATRIX
   over every pool phase × later-pool continuation (W12), THROUGH BOTH
   CARRIERS (external R3-5): the AUDIT CONTRACT IS FORMALLY AMENDED
   (external R4-3 — the shipped contract is one JSON line per operation
   and `tests/test_audit.py` asserts exact sequences; a silent cardinality
   change would break both): `audit.py`'s documented contract, its tests,
   and §7a all carry the new cardinality — the aggregate `maintain` event
   PRESERVED plus one ADDITIVE per-pool event `{op: "consolidate-pool",
   pool_key, status, consolidated, into, error_code?}` per attempted
   pool. **`error_code` is a CLOSED CONTENT-FREE enum — {llm-error,
   store-error, claim-contention, validation-error, timeout} — NEVER
   `str(exc)`: an LLM exception can echo prompt or episode text, and the
   AuditLog's "no memory text ever" invariant forbids it (external R4-3's
   leak). W12 gains the ADVERSARIAL cell: a pool's exception carrying a
   planted secret episode string — the secret provably absent from the
   audit sink.** W12 asserts the sink saw N pool events + the aggregate
   AND telemetry's preserved-key mapping unchanged.
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

**Write-time FLATTENING (external R7-1; carriers completed under R8-1/
R8-3):** when an absorption commits, the survivor's new contribution rows
carry the absorbed prior's identity digest AND copies of the prior's
transitively CLOSED absorption row set — the closure the candidate check
just computed, NOT the prior's direct rows, which for a legacy prior may
themselves be unclosed (found-in-fix item 1 applied to this fix's own
construction: flattening an unclosed set would mint a row set that LOOKS
closed). Every row carries the typed **`contributor_ref`** (the 0014
amendment's columns — the shipped `ContributionDraft` already supplies
contributor_type/contributor_id; the store stops dropping them at
persist). The DIRECT contributor's row is the accepted native
`absorption` row, its `{base, contributor}` payload and op-key idiom
UNTOUCHED (R10-1: v11's flattened payload class was never legal against
that closed schema); flattened ancestor COPIES land at the NEW
**`scope-attribution`** SITE (the 0014 amendment's derived-row site)
with payload class `{"flattened": true}` and per-row INJECTIVE op keys
(`row_op_key` — the framed-digest form, R9-2). Attribution rows are
counted as evidence, never re-walked, and the 0014 exact-set partition
is STRUCTURAL: the direct-invalidation equality counts native-site rows
only, so attribution rows can never perturb it. All in the same
atomic operation —
so every post-0021 survivor's row set is the transitive closure of its
ancestry BY CONSTRUCTION, and the single-level read that misclassified
the reviewer's A→B→C chain cannot recur on records this spec writes.
Pre-0021 chains take 0020 §4a-iii's read-time closure instead. The
membership evidence a prior must present to be a CANDIDATE is likewise
the closed set: a prior whose closure is None is UNRESOLVED and never
absorbs or is absorbed.

### 4d. Mixed-version shared stores (external R2-6)

No schema/format/feature marker prevents a PRE-0021 process from opening
the same store during a rolling upgrade and running today's GLOBAL
consolidation — new processes partition; old ones do not. **W1's claim is
therefore NARROWED to stores operated exclusively by 0021-capable
processes, and the deployment requirement is stated plainly: upgrade
every writer before relying on the partition invariant** (reads are fail-closed
throughout, ON BOTH SYNTHESIS PATHS — external R3-3 corrected v4's
consolidation-only claim, and **external R7-1 corrected v8's
single-level form of THIS claim**: a pre-0021 CONSOLIDATION lands
legacy-shaped → UNRESOLVED, and a pre-0021 ABSORPTION survivor is caught
by the resolver's absorption-row rule ONLY over the TRANSITIVELY CLOSED
row set (0020 §4a-iii / `close_absorption_rows`) — the reviewer's
A→B→C chain defeats the direct-row read, because C's only direct
contributor shares C's scope while A's foreign digest sits one hop
down. Fail-closed reads during the window therefore REQUIRE the closure
at every membership consultation; an unwalkable or cyclic chain is
UNRESOLVED. **The closure is BY CONSTRUCTION on the survivor's own
rows (R8-1, corrected against accepted 0014 A10 — the ledger is
survivor-lifetime-keyed, not append-only): flattened ref-bearing row
sets live exactly as long as their survivor and are immune to
intermediate pruning; ref-less LEGACY rows fall back to the note-walk,
which requires the absorbed records to still exist — a pruned legacy
contributor closes to None → UNRESOLVED, the DISCLOSED read delta
(v9's single-hop read called such survivors own-scope), remediable by
re-derivation.** What is lost during the window is the merge-PREVENTION
half, not the visibility half. TWO residuals, stated: absorptions that
predate the 0014 ledger itself (pre-v0.7.0 events) left no rows and no
links, so their survivors resolve by own identity — a fixed, shrinking
legacy class; and a chain whose intermediate record was PRUNED before
the closure runs is unwalkable → UNRESOLVED (fail-closed, not silent)). **The ENFORCEMENT upgrade is recorded
(Q4): a store-version bump refusing pre-0021 writers — it rides the 0018
D2 breaking window (SCHEMA v8) rather than minting its own break; until a
release takes it, W1 carries the operational narrowing in its own text.**

## 5. Regime analysis

| regime | behaviour |
|---|---|
| identity-free store | stored state + preserved top-level result VALUES identical to today, policy or none (the migration invariant); the result SHAPE is the additive superset (R4-2/R5-3) |
| identity-bearing store, NO policy anywhere | **consolidation partitions anyway (§2 — the disclosed behaviour change)**; recall unchanged (0020: no policy → unscoped views) |
| mixed scopes, maintenance runs | each pool consolidates internally per §4b; cross-scope pairs untouched |
| four A + four B, min_batch=8 | NO-OP — thresholds are per-pool |
| legacy/imported/recovered derivatives | UNRESOLVED: excluded from every pool, invisible to scoped principals (0020), visible unscoped; remedy = re-derivation/restatement |
| repeated cross-scope restatement of one value | parallel per-scope edges; no merge, no laundering; the D-extension cross-principal probe measures exactly this |
| pool B's LLM call raises mid-run | A's commit stands (permanent); B reports "failed" with the error; C/D run anyway; the schema carries all four (R2-5) |
| a pre-0021 process consolidates during a rolling upgrade | its global merge produces a mixed derivative → UNRESOLVED at read (fail-closed); the partition half of W1 is narrowed per §4d until every writer upgrades |
| a pre-0021 process ABSORBS during the window (R3-3) | the survivor carries cross-digest absorption rows → UNRESOLVED at read; pre-0014 absorptions (no rows) are the stated residual |
| a CHAIN of pre-0021 absorptions (A→B→C, the R7-1 cell) | the direct row alone reads own-scope — the read-side CLOSURE walks the chain and finds A's foreign digest → UNRESOLVED; an unwalkable or cyclic chain → UNRESOLVED; post-0021 writes are flattened so the chain shape cannot recur |
| eight identity-less cold records | ONE pool under the reserved `pool:unidentified` key; today's threshold semantics; today's top-level return values (R3-4) |

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
| W12 the fault-injection matrix (R2-5/R3-5/R4-3): every pool phase × later-pool continuation, through ALL carriers — the additive-superset return, the amended audit contract (aggregate + per-pool events; closed error codes; **the planted-secret adversarial cell: an exception carrying episode text never reaches the sink**), telemetry's preserved keys, the robustness checker, and the exact-result lifecycle tests | `test_per_pool_fault_matrix` *(offline)* |
| W13 absorption survivors resolve through ledger rows OVER THE TRANSITIVELY CLOSED SET; the cross-digest cell fails closed (R3-3; closure per R7-1 — shared with 0020 V14) | `test_absorption_survivor_membership` *(offline)* |
| W14 write-time flattening: every post-0021 absorption leaves the survivor's row set transitively closed; the A→B→C chain is UNRESOLVED native and restored, under remap and after reopen (R7-1 — shared with 0020 V15) | `test_transitive_absorption_chains` *(offline)* |
| W15 the amended import primitive: pre-commit refusal leaves the destination byte-identical; rollback on mid-plan failure; idempotent re-import skips (never duplicates) rows; concurrent same-file imports linearize with no partial state; membership identical after reopen (R7-2/R7-3) | `test_import_contribution_primitive` *(offline)* |
| W16 the closure survives retention: prune the A→B→C intermediate, close/reopen, classify → UNRESOLVED (typed refs walk the ledger; ref-less pruned legacy fails closed) — shared with 0020 V17 (R8-1) | `test_closure_survives_pruning` *(offline)* |
| W17 the ledger-row plan stores against the ACCEPTED DDL: per-row INJECTIVE op keys (framed-digest form — delimiter-bearing ids never collide, R9-2) pass the real UNIQUE partial index; NULL-digest dedup by the ONE canonical plan id (history/evidence drift never skips as equal, R9-3); idempotent re-import; concurrent linearization — shared with 0020 V18 (R8-3) | `test_ledger_plan_against_real_ddl` *(offline)* |
| W18 the export reverse link is unique on BOTH sides of a prune: derive(A)=direct absorber before; the retention contract's reparenting keeps it unique after; zero canonical → the field omits; >1 → the export refuses (R9-1 — shared with 0020's derivation vectors + the ledger harness's SQL-backed group) | `test_export_reverse_link_unique` *(offline)* |

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
| `graph.py` (absorption) + `apply_supersession_plan` | the same-scope candidate requirement; post-0021 the SAME atomic plan carries the scope-attribution flattened copies (native context — R12-1; the native all-framed key form) |
| `apply_retention_prune_plan` (FUTURE — named) | the retention contract's own atomic primitive (reparented links + markers; its own 0009-family §4 amendment at implementation; no shipped path prunes today) |
| `COMBINING_SITES` + `specs/generated/0021-combining-sites.md` | the mechanical totality carrier (F4) |
| `portability.py` (import path) | the PRE-COMMIT reconstruction call (on the parsed export file, before any write — R7-2), remap via the importer's own id table, whole-import REFUSAL on missing/unresolvable/AMBIGUOUS/cyclic linkage with the destination byte-identical after a refusal; export materializes `absorbed_by_id` at the next FORMAT bump |
| `store/base.py` + `store/sqlite.py` + the contribution carrier | the `imported-absorption` site (the 0014 amendment) + the whole-import atomic primitive extended by the EXACT 0009 §4c amendment below (R7-3 — v8's "inherit the primitive's tests" claim did not follow from the unamended contract, whose expected-state checks covered edges/episodes/chain heads and nothing of ledger state) |
| `audit.py` + `tests/test_audit.py` + docs | the amended cardinality contract (aggregate + per-pool events) and the closed error-code enum (R4-3) |
| `tests/robustness/invariants.py` + lifecycle exact-result tests | updated for the additive-superset result (R4-2) |
| docs | the behaviour change for identity-bearing stores; the UNRESOLVED operator remedies |

### 7b. Cross-spec carriers

#### The authoritative ledger-site matrix (external R11-1)

<!-- SITE-MATRIX (generated by reference_scope.render_site_matrix — R11-1: ONE source; the seal byte-compares this block across every carrier) -->
| atomic writer (operation context) | operation-ID domain | site | payload subset | canonical? | in the exact set? | per-row key form |
|---|---|---|---|---|---|---|
| `apply_supersession_plan` (native — accepted 0003 §4f CAS plan, accepted 0014 rows) | `sup-{edge.id}` (the shipped idiom; unrestricted suffix) | `absorption` | {base, contributor} (the accepted closed schema — NOT amended) | YES (direct link) | YES — the accepted direct-invalidation equality counts exactly these | the accepted native idiom, unchanged |
| `apply_supersession_plan` (native, post-0021 — the §4c flattening rides the SAME plan) | `sup-{edge.id}` | `scope-attribution` | {"flattened": true} ONLY | NO (flattened copy) | NO — structurally excluded | native_row_op_key(op_id, survivor, contributor) — the ALL-FRAMED digest form (the native op id embeds unrestricted text, so it is framed INTO the digest, never a prefix) |
| `commit_outcome_import_plan` (import — accepted 0009 §4c, purpose-built; rows derive ONLY from `reconstruct_absorption_rows`) | `op-<12hex>` (minted once per import) | `imported-absorption` | {"reconstructed": true} EXACTLY | YES (direct link) | NO — never counted | row_op_key(import_op, "imported-absorption", …) |
| `commit_outcome_import_plan` (import — transitive copies) | `op-<12hex>` | `scope-attribution` | {"flattened": true, "reconstructed": true} ONLY | NO (flattened copy) | NO — structurally excluded | row_op_key(import_op, "scope-attribution", …) |
| `apply_retention_prune_plan` (FUTURE — the retention contract's primitive, NAMED here; minted as its own 0009-family §4 amendment at implementation; no shipped path prunes today) | `op-<12hex>` (minted once per prune) | `scope-attribution` | {"reparented_from": <id>} · {"closure": "incomplete"} ONLY | ONLY the reparented class; markers NEVER | NO — structurally excluded | row_op_key(prune_op, "scope-attribution", …) |
<!-- /SITE-MATRIX -->


| spec | touchpoint | disposition |
|---|---|---|
| 0020 | **MUTUAL `Spec-Requires` (external F6)** — atomic acceptance, the 0016/0018 precedent | 0020's claim is CONDITIONAL on this spec wherever maintenance runs; neither accepts alone |
| 0009 | **THE EXACT §4c PRIMITIVE AMENDMENT (external R7-3; REWRITTEN under R8-3, which executed the v9 form against the accepted schema — five-field rows could not construct a ContributionRecord, and one-op-key-per-plan raised IntegrityError on the accepted UNIQUE partial index). Drafted verbatim for same-commit landing at acceptance; 0009 now sits in `Spec-Requires` because this is a normative amendment:** | *`commit_outcome_import_plan`'s plan gains a third member, `plan["contributions"]` — ContributionRowPlan dicts, each TOTAL over the STORED ROW's full field set (ContributionRecord has TEN fields; the v9 five-field shape was underdetermined): **`id`** = `plan_row_id(...)` — THE ONE CANONICAL LOGICAL-ROW PROJECTION (R9-3: v10 carried three incompatible equality definitions; the reviewer executed direct↔flattened payload drift collapsing into one id): the deterministic framed digest over EVERY semantic field — (user_id, survivor_type, survivor_id, site, identity_digest, evidence_ref_digest, contributor_type, contributor_ref, CANONICAL PAYLOAD JSON) with None-sentinels — excluding ONLY the operational fields (the re-minted op key and the commit timestamp); the PRIMARY-KEY-riding dedup identity, so SQLite NULL-uniqueness semantics never decide anything. A cross-field VALIDATOR (`validate_row_plan`) runs before projection: PRESENCE of every semantic field is required separately from value validity (R11-2 — None is a value, absence is not; contributor_type is never defaulted), and payloads must EXACTLY match one of the row's site's closed classes (type-level literals; unknown keys refuse); and the validator is CONTEXT-AWARE (R12-1): each atomic writer may emit ONLY its own (site, payload-class) cells per the WRITER MATRIX — `commit_outcome_import_plan` writes direct imported links and imported transitive copies ONLY (its rows derive solely from `reconstruct_absorption_rows`); NATIVE flattened copies ride `apply_supersession_plan` (accepted 0003 §4f — the same atomic plan as the absorption itself, with the ALL-FRAMED native key form, since the shipped `sup-{edge.id}` op id embeds unrestricted text); reparented links and markers belong to `apply_retention_prune_plan`, the retention contract's OWN future primitive, NAMED here and minted as its own 0009-family §4 amendment at implementation — accepted 0009's import primitive stays purpose-built, never a general transaction API; cross-context cells REFUSE — and THE OPERATION BINDING (R13-1, the round-13 finding: the declared op-ID domains were never consumed and an import row projected under missing/native/garbage/null keys): `op_key` is DERIVED INSIDE the atomic primitive from its store-owned operation id and the row coordinates — `construct_plan_row` is the normative constructor and every normative row producer builds through it; callers NEVER supply a key. Validation consumes each context's operation-ID domain and requires EXACT key equality with the context's derivation, so absent, null, malformed, cross-context, and mis-derived keys all refuse BEFORE projection or storage. The executed gate is the COMPLETE 3×5 writer × payload-class product (5 valid cells built by the constructor AND inserted at the real-DDL boundary; all 10 invalid cells enumerated mechanically) plus the key-presence/domain/derivation cases — the CELL COUNT lives in ONE carrier, the recorded harness result (`ledger_plan_result.txt`; the round-11 rule: prose counts drift — research's rider sign-off caught exactly such a drift, 76 vs 77 after the acceptance-obligation newline cell); **`user_id`** = the import's target user; **`survivor_type`/`survivor_id`** = the plan record the row attributes (must name a record in THIS plan or an already-present idempotent-equal record — else preflight refuses); **`site`** = one of the TWO plan sites (R11-1 — the v12 text still said imported-absorption was the only one, contradicting the 0014 amendment and the reference): `"imported-absorption"` for DIRECT reconstructed links, `"scope-attribution"` for transitive copies (and, from the prune path, reparented links and markers) — the ONLY sites the amended primitive may write; the 0014 site registry gates both; the authoritative SITE MATRIX below is the one source every carrier embeds; **`identity_digest`** = 64-hex or None (an unidentified absorbed record); **`evidence_ref_digest`** = the shipped `evidence_ref_digest(resolved origin, evidence_ref)` construction over THE CONTRIBUTOR record the row binds (None iff its evidence_ref is empty); **`contributor_ref`** = the post-remap absorbed record id — the TYPED BINDING that determines which exported record supplies the evidence digest (R8-3's underdetermination resolved) and the durable closure link (R8-1); with `contributor_type` = "edge"; **`payload`** = the row's site's closed class (the SITE MATRIX below): direct links EXACTLY `{"reconstructed": true}`; transitive copies `{"flattened": true, "reconstructed": true}` at scope-attribution; **`op_key`** = the PER-ROW key in the INJECTIVE framed-digest form (`row_op_key`: `{op}:{site-token}:` + sha256 over the domain-separated FRAMED (survivor_id, contributor_ref) pair — the site token parameterized over both plan sites, R11-1 — R9-2: the v10 plain colon-join was not injective over unrestricted ids ('a:b'+'c' collided with 'a'+'b:c', reviewer-executed IntegrityError; the shipped `consolidation_op_key` avoids this only because its sole unrestricted field is TRAILING); colon-free prefix by construction, unique per row, satisfying `ix_contribution_ledger_op_key` (UNIQUE WHERE op_key IS NOT NULL); `import_op` is the ONE minted `op-<12hex>` id; **`created_at`** = the store clock at commit. DERIVATION, corrected from v9's "the store derives nothing": rows derive ONLY from `reconstruct_absorption_rows` over the export file, PRE-COMMIT (0020 §4a-iii); the store SUPPLIES its own clock and VALIDATES everything, and INVENTS nothing. EXPECTED STATE: `expected_destination_state` gains `contribution_state` — for every plan record carrying rows, the destination's current rows for that (user, type, id) must be ABSENT (first import) or EXACTLY EQUAL **by `plan_row_id` set equality — THE one and only equality definition (R9-3: the v10 three-field multiset phrasing is WITHDRAWN; it ignored payload and evidence, so a direct A→C history and a flattened A→B→C history would have silently skipped as equal, against accepted 0009 H4's record-equality idempotency)** (idempotent re-import — rows skip, never duplicate); anything else returns `DESTINATION_CHANGED`, writing nothing — a survivor with different recorded contributors OR a different recorded history SHAPE is a different history, refused whole. ROLLBACK: contribution rows ride the SAME single atomic commit as edges/episodes; nothing is written after a prefix. RETURN: success gains `"contributions": n` written and `"contributions_existing": m` skipped-as-equal. CONCURRENT SAME-FILE IMPORTS: the primitive linearizes; the loser's revalidation sees the winner's rows as exact-equal → skip, or `DESTINATION_CHANGED` on a conflicting race — no duplicates, no partial state. DURABILITY: ordinary ledger rows; membership identical after close/reopen (W15). THE EXECUTABLE CARRIER: `specs/evidence/0020/ledger_plan_harness.py` extracts the REAL contribution_ledger DDL from a live store, applies the amendment's ALTERs, and proves multi-row single-op inserts, NULL-digest dedup, idempotent re-import, and concurrent-connection linearization against real SQLite (V18).* |
| 0014 | the ledger + **THE NAMED AMENDMENT (external R6-2; extended R7-1/R7-3; columns R8-1/R8-3; THE `scope-attribution` SITE and INSERT-ONLY reparenting under R10-1/R10-2): TWO new sites + the typed contributor link + the transitive capability — every accepted schema UNTOUCHED** | the MEMBERSHIP join is load-bearing v1. The amendment, drafted for same-commit landing at acceptance (the 0019 rider precedent; separate cross-spec sign-off required): *(1) SITES: 0014's site set gains `imported-absorption` (DIRECT reconstructed links, written only by the import path; closed payload EXACTLY `{"reconstructed": true}`) AND **`scope-attribution`** (R10-1 — every DERIVED attribution row: flattened ancestor copies, reparented canonical links, closure-incompleteness markers; closed payload vocabulary EXACTLY `{"flattened": true}` | `{"flattened": true, "reconstructed": true}` | `{"reparented_from": <non-empty id>}` | `{"closure": "incomplete"}` — literal-True markers, no unknown keys, marker rows carry identity_digest None). The native `absorption` site's accepted `{base, contributor}` payload schema and its rows are NOT amended (v11's flattened class was never legal there — the reviewer's catch). Site registry + generated manifest entries for both; the payload validator (`validate_row_plan`, TOTAL over every field — R10-3) gates every row the amended primitive writes; these rows provide ATTRIBUTION for scope membership and explicitly NO reversal; dangling-survivor rules apply unchanged. (2) IMMUTABILITY PRESERVED (R10-1): accepted 0014's insert-only rule is NOT amended — reparenting is the INSERTION of a new scope-attribution row (the reparented class); nothing existing is ever updated or replaced; the A10 drop of the pruned record's own rows is the accepted lifecycle rule, unchanged. (3) THE TYPED CONTRIBUTOR LINK (R8-1): `contribution_ledger` gains two nullable columns — EXACT DDL and BOTH measured manifestations in the 0019 rider below: `ALTER TABLE contribution_ledger ADD COLUMN contributor_type TEXT;` `ALTER TABLE contribution_ledger ADD COLUMN contributor_ref TEXT;` — populated on every NEW plan-site row from the fields the shipped `ContributionDraft` ALREADY carries; NULL on legacy rows. THE DURABILITY MODEL, against accepted 0014 A10: the durable object is the survivor's OWN row set — born-closed flattening makes intermediate pruning harmless; the EXPORTER derives `absorbed_by_id` from the unique CANONICAL row (direct or reparented — markers and plain copies NEVER canonical, R10-2's launder closed), never from notes. (4) THE EXACT-SET PARTITION, STRUCTURAL (R8-3/R10-1): §4b's direct-invalidation exact-set equality counts NATIVE-SITE rows only — attribution rows sit at their own site and can never perturb it. (5) THE §4f PREMISE CORRECTED (R7-1): every consumer of absorption evidence MUST consume the TRANSITIVELY CLOSED set; single-level consumption is a defect. (6) THE RETENTION CONTRACT (R8-1/R10-1): any future physical pruning of an absorbed record MUST first INSERT the reparented rows (or the marker where the flattened copy is missing) on its canonical absorber — no shipped path prunes an absorbed edge today (asserted at §2c-ii).* Full-membership materialization at export stays the recorded widening |
| 0016 + 0018 | **THE FORMAT WINDOW RIDER (external R8-2 — accepted 0016/0018/0019 freeze the FORMAT-7 shape; these candidates must amend it, not assume it):** | *drafted rider to the frozen v7 export shape, same-commit landing at acceptance: exported edge records MAY carry `absorbed_by_id` (string; present iff the record is an `absorbed_duplicate` with a unique CANONICAL ledger row — direct or reparented — naming it, per 0020 §4a-iii's `derive_absorbed_by`; NEVER derived from notes); importers of v7-with-rider files consume it as 0020 §4a-iii's structured carrier; files without it take the legacy note rule. The rider rides the SAME 0018 D2 breaking window as the SCHEMA-v8 ledger columns (the 0019 rider below) and 0021's writer-version enforcement (Q4) — ONE break carries all three; none of the three mints its own window. Legacy-export refusal behaviour is 0020 §4a-iii's decidable rule (ambiguity → whole-import refusal)* |
| 0019 | **THE COMPLETE FINAL-FORM SCHEMA RIDER (external R9-4 — accepted 0019's Rider A(A3) froze D2's SCHEMA v7→v8 as the NO-DDL refusal bump; v10 silently contradicted that freeze and omitted 0019 from `Spec-Requires`, both corrected). Drafted for same-commit landing at 0020/0021 acceptance, amending 0019's own Rider A; separate cross-spec sign-off required; final form, whole clauses, per 0019's own R2-6 discipline:** | *> **Amended by 0020/0021.** (C1) Rider A(A3)'s SCHEMA clause, final: D2 ships SCHEMA v7→v8 **CARRYING DDL** — `contribution_ledger` gains `contributor_type TEXT` and `contributor_ref TEXT` (nullable; legacy rows NULL) — replacing the no-DDL characterization. The refusal-bump semantics are RETAINED (a v8 store refuses on pre-D2 builds — back up first); FORMAT 6→7 and the receipt-era rules (A1/A2) are UNCHANGED. (C2) THE v8 MANIFESTATIONS — GENERATED NOW, not promised (R10-4: the previous clause deferred them): `specs/evidence/0020/schema_v8_evidence.py` reads the SHIPPED `SCHEMA_V7` constructor (never retyped), emits (i) the LITERAL v8 CONSTRUCTOR (the v7 text + the two columns appended after `created_at`) and (ii) the MEASURED ALTER-path stored DDL (a real database built from v7, the two ALTERs run, sqlite_master read back — byte-distinct from the constructor per the 0014 supersession_operations precedent), PROVES table_info parity between them, and sha-pins both texts and both migration steps; the recorded output (`schema_v8_evidence.txt`) ships in this package and its shas are the review anchor. At the acceptance flip the same generator runs on the QUALIFIED runtime and its output enters `specs/schema_evidence.py`'s generated evidence — regenerated, never hand-authored. (C3) THE MIGRATION CONTRACT: v7→v8 runs ONLY under the 0018 orchestrator (0019 U-Q3 condition 2 unchanged — D2 is the orchestrator's); the migration's 0013-declared steps are EXACTLY the two ALTER statements, sha-pinned IN THE RECORDED EVIDENCE (per 0013's declared-step contract — the 0016 declared-no-op-step precedent, upgraded to real steps); rollback is 0018's attestation/backup contract, unchanged. (C4) THE 0007 CLAUSE: v8 is a STAMPED version whose shape evidence includes BOTH manifestations; unstamped resolution rules unchanged. (C5) the 0019 R2-6 executable numeral sweep RE-RUNS at the flip commit with every "no-DDL" hit disposed — each carries this rider's replacement or is historical-marked; the sweep output ships in the flip commit's message.* |
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

## Review closure

*(PROCESS §4a — one row per finding PER OWNER. The rounds were COUPLED with
0020, so every finding of every round is listed here with its OWNER: an
omission and a hand-off must not look alike. `evidence` names the artifact
that closes the row — a spec section for a design ruling, and additionally a
vector, harness, test or commit wherever code exists. Round reports are
verbatim in `specs/reviews/0020-0021/round-N.md`; the compressed per-round
dispositions are `specs/reviews.py`, which is the source the STATUS index
renders from. Rounds: internal 1, external 1–14 (findings 7→7→5→3→4→3→4→3→5→
5→5→3→1→0), plus one POST-ACCEPTANCE self-found defect.

**Two counts, two bases — stated because they differ and a reader who sums the
wrong one will think the other is a typo.** The series above is PER ROUND: the
number of distinct findings that round's report raised, which is what the
verbatim reports in `specs/reviews/0020-0021/` say. `specs/reviews.py` sums PER
SPEC, and the rounds were COUPLED, so a finding landing on both specs is
recorded in both rows and its per-spec total is necessarily larger (round 1: 7
distinct findings, recorded 5 under 0020 and 6 under 0021; 0021's per-spec
external series is 6→3→3→2→2→1→2→2→3→3→3→1→1→0, plus 4 internal). The table
below lists one row per finding PER OWNER, so it tracks the per-spec basis. No
single number is "the" count; the round reports are authoritative for what was
raised, this table for what closed it.)*

| round | finding | class | owner | disposition | evidence |
|---|---|---|---|---|---|
| int-1 | R1 derived-record scope membership UNDEFINED and defaulted to a leak — maintenance is itself a producer of absent-identity records | BLOCKING | both | **folded (v2):** membership evaluates over the CONTRIBUTORS' resolved identities (the 0014 ledger join); the matrix note and W7 carry it here | §3; W7 `test_derivative_inherits_partition_scope` |
| int-1 | R2 the §7b partial-shipping cell UNDERSTATED the coupling (the wiki exclusion carries none of the consolidation burden) | D | 0021 | **folded (v2), restated at true strength:** 0020's §8 claim is CONDITIONAL on this spec wherever maintenance runs; shipping 0020 alone is a boundary with an unlocked back door, and any such decision must say so in those words | §1; §7b (the 0020 row) |
| int-1 | R3 no reach assertions — the construction rested on remembered code shape | E | 0021 | folded (v2): §2c-ii, commands recorded per the 0005 rule — **and re-run at implementation, where three results moved and one command proved never to have been biting** | §2c-ii (the re-run table) |
| int-1 | R4 test tiers unmarked (offline vs live) | E | 0021 | folded (v2): every W-check carries its tier; W6 is the live/D-ext form | §6; `tests/test_0021_maintain_scope.py` (the deferral stubs) |
| ext-1 | F1 the derivative-membership rule contradicted the implementation and failed across portability (`_derive_output_metadata` copies `inputs[0].provenance` without clearing identity) | G+C, executed | 0020 (+0021) | **folded (v3) as 0020's evidence HIERARCHY; the IMPLEMENTATION OBLIGATION is this spec's:** outputs get `origin=None`/`source_id=None`, and the reviewer's mixed-scope probe is the regression | §4a; W8 `test_output_identity_cleared`; `store/sqlite._derive_output_metadata` |
| ext-1 | F2 the new public types and grammars had no mechanical definition | A+F | 0020 | folded in 0020 (v3): the reference + pinned vectors | 0020 §4a-ii; `vector_harness.py` |
| ext-1 | F3 the read-surface inventory was incomplete | C | 0020 | folded in 0020 (v3) | 0020 §4f |
| ext-1 | F4 this spec's consolidation construction rested on a FALSE reach assertion — v2 claimed consolidation "groups by trust class today"; `lifecycle.consolidate` was ONE global cold pool, one threshold, one call, one claim (the idiom claimed was absorption's; the second execute-shipped-claims miss, disclosed) | G+E+C | 0021 | **folded (v3) against the REAL shape:** §4b's per-scope pools, PER-POOL thresholds (the 4A+4B/min-8 NO-OP cell), deterministic digest order, one 0010 op per pool, independent failures, per-pool reporting, pre-feature recovery; **and W3 upgraded from prose totality to a MECHANICAL `COMBINING_SITES` registry + generated manifest with "combining" defined** | §4b; §3; W10 `test_per_scope_thresholds`; W3 `test_scope_operation_matrix_is_total`; `src/veracium/combining.py`; `specs/generated/0021-combining-sites.md` |
| ext-1 | F5 per-process READ policy conflicts with shared-store maintenance — an honest unscoped host could co-consolidate A+B while a scoped host assumed isolation | C+D | 0021 | **RULED (v3): identity partitioning is POLICY-INDEPENDENT.** Maintenance partitions by resolved identity always; policy is read-side. The behaviour change for identity-bearing stores is DISCLOSED, and config-only reversibility is WITHDRAWN for maintenance effects (permanent, stated) | §2; §7; W11 `test_partition_is_policy_independent`; `lifecycle.partition_cold` |
| ext-1 | F6 the coupling was prose-only | E+D | both | folded (v3): MUTUAL `Spec-Requires`, machine-checked | the header; `specs/check_spec_reference.py` |
| ext-1 | F7 the sealed archive failed its own package verifier | E | archive | folded (v2→v3) | the seal machinery |
| ext-2 | R2-1 the reference VIOLATED accepted 0006 absence semantics | G+B+E | 0020 | folded in 0020 (v4) | 0020 §4a-ii |
| ext-2 | R2-2 contradictory semantics for a principal without policy | D | 0020 | folded in 0020 (v4) | 0020 §4a-ii |
| ext-2 | R2-3 the recovery row was WRONG for OUTPUTS_DURABLE — recovery cannot clear an already-durable pre-feature output, it only finalizes | A+C, executed | both | **folded (v4):** such outputs keep the stale copied identity and are caught by the NORMATIVE legacy predicate BY SHAPE; GENERATING-state abandons leave no output; recovery never fabricates membership | §2c (in-flight row); §4b step 6; W9 `test_unresolved_populations_fail_closed` |
| ext-2 | R2-4 0020's zero-change claim contradicted this spec's policy-independent rule | D | both | folded (v4): the claim narrowed to READS over a fixed store state | 0020 §8; §2 |
| ext-2 | R2-5 per-pool failure semantics and the public result construction were incomplete | C+F | 0021 | **folded (v4→v5):** failures are CAUGHT AND CONTINUED; the exact result schema is representable for "A committed, B failed, C/D ran anyway"; W12 is a fault-injection matrix over every pool phase × continuation | §4b step 4; W12 `test_per_pool_fault_matrix` |
| ext-2 | R2-6 the mixed-version hole — a pre-0021 process can run global consolidation on a shared store | C | 0021 | **RULED (v4):** W1/§8 NARROWED to stores operated exclusively by 0021-capable processes, with the honest split stated (scoped READS stay fail-closed during the window; the merge-PREVENTION half needs every writer upgraded). The enforcement bump is Q4, riding the 0018 D2 window | §4d; §5; Q4; W1's own text |
| ext-2 | R2-7 the archive's sealed-state fix introduced new packaging defects | E | archive | folded (v4) | the seal machinery |
| ext-3 | R3-1 policy validation remained BYPASSABLE | B+E | 0020 | folded in 0020 (v5) | 0020 §4a-ii |
| ext-3 | R3-2 the resolver consumed a ledger shape 0014 does not provide | G+A | 0020 | folded in 0020 (v5): membership moved to DIGEST SPACE | 0020 §4a-ii |
| ext-3 | R3-3 legacy ABSORPTION defeated the mixed-version read-safety claim (a pre-0021 survivor is an Edge with NO lineage carrying identity A plus B's inherited maxima) | G, executed | both | **folded (v5):** the ABSORPTION-SURVIVOR rule — any cross-digest (or None-vs-digest) contributor → UNRESOLVED; §4d's claim corrected to cover BOTH synthesis paths; the pre-0014 residual stated, not discovered | §4d; §5; W13 `test_absorption_survivor_membership`; `test_a_pre_0021_chain_still_fails_closed` |
| ext-3 | R3-4 the frozen result schema had NO legal key for the shared pool (0006 digests a source-less identity to None) and REPLACED the public return | F+D | both | **folded (v5): the ADDITIVE-SUPERSET return** — `consolidated`/`into`/`recovered` preserved verbatim as the totals, the RESERVED `pool:unidentified` key (a colon can never collide with 64-hex), and `pools`/`pools_ok`/`pools_failed` added beside them | §4b step 4; W4 `test_unidentified_pool_is_closed`; `lifecycle.SHARED_POOL_KEY` usage; `test_lifecycle.py`'s exact-result cell |
| ext-3 | R3-5 the promised audit/telemetry carrier sweep was PROSE, not a mechanical contract | E+C | 0021 | **folded (v5→v6):** the aggregate `maintain` event PRESERVED + one additive per-pool event; telemetry's mapping reads the preserved keys UNCHANGED BY CONSTRUCTION (the superset shape is what solves it); W12 asserts through BOTH carriers | §4b step 4; §7a; W12; `audit.py`'s amended cardinality docstring |
| ext-4 | R4-1 policy sealing STILL bypassable | B+E | 0020 | folded in 0020 (v6) | 0020 §4a-ii |
| ext-4 | (self-found, ext-4) an absorption survivor crossing export/import loses its ledger rows | G | 0020 | closed in 0020 (v6): the import-time RECONSTRUCTION rule | 0020 §4a-iii |
| ext-4 | R4-2 the identity-free byte-identity claim contradicted the additive result shape FOR EVERY STORE — executed against our own robustness checker, which REJECTED the dict-valued `pools` key | D+C, executed | 0021 | **folded (v6):** every identity-free claim narrowed to STORED-STATE AND PRESERVED-VALUE compatibility, and the carrier sweep formally NAMES the robustness checker, the exact-result lifecycle tests and docs as implementation obligations — **all three updated in the implementing commit** | §2; §5; §7a; `tests/robustness/invariants.py` (`check_maintain`); `tests/test_lifecycle.py`; `tests/test_0010_consolidate_recovery.py`; `docs/api.md` |
| ext-4 | R4-3 the shipped audit contract is one JSON line per operation with exact-sequence tests, and a free-text error field can echo memory text | C+B | 0021 | **folded (v6):** a FORMAL audit-contract amendment (audit.py, its tests and §7a all carry the cardinality change) and `error_code` as a CLOSED CONTENT-FREE enum — never `str(exc)`; W12 gains the adversarial planted-secret cell | §4b step 4; §7a; `lifecycle.POOL_ERROR_CODES`; W12's `llm-secret` cell |
| ext-5 | R5-1 COLLECTED claimed the import reconstruction closed while the harness asserted nothing | D | 0020 | folded in 0020 (v7); this spec's half: the imported-absorption row moved from stated-not-built to the EXECUTABLE rule | §2c (imported row); `store_adapter_harness.py` |
| ext-5 | R5-2 the R4-1 seal was RE-SIGNABLE | B, executed | 0020 | folded in 0020 (v7) | 0020 §4a-ii |
| ext-5 | R5-3 the identity-free byte-identity phrasing SURVIVED the R4-2 narrowing in both §5 regime tables (the carrier-sweep class, again, on my own narrowing) | D | 0021 | folded (v7): both regime rows swept to stored-state + preserved-values with the additive-superset shape named | §5 (rows 1 and 9) |
| ext-5 | R5-4 `verify_package.py` did not verify every declared manifest hash | E, executed | verifier | folded (v7) | `verify_package.py` |
| ext-6 | R6-1 import reconstruction failed SUPPORTED inputs | G, executed | 0020 | folded in 0020 (v8) | 0020 §4a-iii |
| ext-6 | R6-2 "import_memory writes real ledger rows" was NOT IMPLEMENTABLE under accepted 0014 (missing fields; the total-payload rule; the primitive carries only edges+episodes) | A+C | both | **folded (v8):** the NAMED 0014 amendment — a distinct imported-evidence SITE with its own integrity semantics, ATTRIBUTION ONLY and explicitly NO reversal — plus the 0009 §4c primitive extension | §7b (0014 + 0009 rows); `ledger_plan_harness.py` |
| ext-6 | R6-3 policy carrier wording internally stale | D | 0020 | folded in 0020 (v8) | 0020 §4a-ii |
| ext-7 | R7-1 TRANSITIVE absorption bypassed scope membership — A(scope-a)→B(scope-b)→C(scope-b) leaves C's direct row equal to C's own scope | C+A, executed on a real chain | 0020 (+0021) | **folded (v9): the DUAL transitive contract.** This spec owns the WRITE half: §4c WRITE-TIME FLATTENING copies the prior's transitively CLOSED set onto the survivor in the SAME atomic operation, so a post-0021 survivor's rows are its whole ancestry by construction and the chain shape cannot recur | §4c; §4d; W14 `test_transitive_absorption_chains`; `store/sqlite._write_absorption_flattening` |
| ext-7 | R7-2 the note REGEX rejected valid native exports; the "full import matrix" claim was false | F+E, executed | 0020 | folded in 0020 (v9) | 0020 §4a-iii |
| ext-7 | R7-3 the imported-ledger atomic contract was DESCRIPTIVE, not constructive (pre-send miss: checklist item 4 — cross-module trust audited on the sunny path only) | A+C | both | **folded (v9):** THE EXACT 0009 §4c AMENDMENT drafted verbatim — plan rows, expected `contribution_state`, rollback on the one atomic commit, idempotent re-import, concurrent linearization, reopen durability | §7b (the 0009 row); W15; `tests/test_0021_import_linkage.py` |
| ext-7 | R7-4 "recursively immutable" and carrier-cleanup claims were still false | D×3 | 0020 | folded in 0020 (v9) | 0020 §4a-ii |
| ext-8 | R8-1 retention pruning erases the intermediate record AND its note — the only closure link | C (found-in-fix of R7-1) | 0020 (+0021) | **folded (v10): closure BY CONSTRUCTION.** This spec's half is the write invariant that makes it true (§4c flattening + the typed `contributor_ref`) and the RETENTION CONTRACT recorded for any future prune — asserted executably to have no shipped writer | §4c; §4d; §7b (0014 clause 6); §2c-ii row 7; W14's post-drop cell |
| ext-8 | R8-2 `absorbed_by_id` had NO durable write-time source and THREE carriers contradicted | A+D×3 | 0020 | folded in 0020 (v10); the FORMAT rider rides the ONE 0018 D2 window with the SCHEMA-v8 columns and this spec's Q4 | §7b (0016+0018 row) |
| ext-8 | R8-3 the "exact" import amendment could not construct or store its rows (five fields vs ten; one-op-key-per-plan raised IntegrityError on the accepted UNIQUE index). PRE-SEND MISS: verify-against-the-domain, fifth bite | A+F+G, executed against the accepted DDL | both | **folded (v10→v11):** the amendment rewritten over the full ten-field stored row, per-row injective keys, `plan_row_id` dedup, and the typed contributor binding | §7b (the 0009 row); `ledger_plan_harness.py` |
| ext-9 | R9-1 flattening made the reverse derivation NON-UNIQUE | C+A, executed | 0020 | folded in 0020 (v11) | 0020 §4a-iii |
| ext-9 | R9-2 the per-row op-key encoding was not injective | F | 0020 | folded in 0020 (v11): the framed-digest form — and the NATIVE variant this spec's flattening uses frames the whole `sup-{edge.id}` op id | `native_row_op_key`; W14's key assertion |
| ext-9 | R9-3 THREE incompatible equality definitions; a direct A→C history could silently skip as equal to a flattened A→B→C one | D+F, executed | both | **folded (v11):** `plan_row_id` is THE ONE canonical logical-row projection; the multiset phrasing WITHDRAWN; the walker refuses marker-only rows | §7b (the 0009 row); `ledger_plan_harness.py` |
| ext-9 | R9-4 the SCHEMA-v8 DDL contradicted accepted 0019's Rider A(A3) freeze and omitted 0019 from `Spec-Requires` | D+C (carrier-completeness) | both | **folded (v11→v12):** the COMPLETE FINAL-FORM 0019 rider (C1–C5), `Spec-Requires` += 0019 | §7b (the 0019 row); the header; `schema_v8_evidence.py` |
| ext-9 | R9-5 runtime-verifier defects were mislabeled as environment skips | E, fault-injected | verifier | folded (v11) | `verify_package.py` |
| ext-10 | R10-1 prune-time reparenting MUTATED a ledger row and the payload classes were never legal against the native site's closed schema | A+D, owned | both | **folded (v12): the `scope-attribution` SITE.** Every derived row lives at a new site with its own closed payload vocabulary; every accepted schema untouched; reparenting is an INSERTION; the exact-set partition becomes STRUCTURAL — which is why §4c's flattened copies can never perturb 0014's direct-invalidation equality | §4c; §7b SITE-MATRIX; W14 (the native `absorption` row's payload asserted UNAMENDED) |
| ext-10 | R10-2 the closure-incompleteness marker LAUNDERED into a clean `absorbed_by_id` | C, executed | 0020 | folded in 0020 (v12) | 0020 §4a-iii; `_is_canonical` |
| ext-10 | R10-3 `validate_row_plan` was not total over the amended logical row | C | both | folded (v12): strict per-field validation + an exhaustive negative matrix | `validate_row_plan`; `ledger_plan_harness.py` |
| ext-10 | R10-4 the 0019 rider was still a delta promising evidence later | C+D | both | folded (v12): both manifestations GENERATED now | `schema_v8_evidence.py` |
| ext-10 | R10-5 the verifier used truthiness and string containment | E, injected | verifier | folded (v12) | `verify_package_selftest.py` |
| ext-11 | R11-1 the new site split was CONTRADICTORY across normative carriers | D (carrier-completeness) | both | **folded (v13): the AUTHORITATIVE SITE MATRIX** — one source, rendered, embedded verbatim between markers in every carrier, byte-compared by the seal | §7b (the SITE-MATRIX block) |
| ext-11 | R11-2 `validate_row_plan` used `.get()` — deleted keys were accepted and `contributor_type` silently defaulted | F+E (found-in-fix) | both | folded (v13): PRESENCE required separately from value validity | `validate_row_plan`; `ledger_plan_harness.py` |
| ext-11 | R11-3 the insert-only regression contained an always-passing assertion | E, owned plainly | both | folded (v13) | `ledger_plan_harness.py` |
| ext-11 | R11-4 fresh-vs-recorded compared only the final line | E, executed | verifier | folded (v13) | `verify_package.py` |
| ext-11 | R11-5 the manifest omitted 0019 from this spec's requires and COLLECTED said the wrong round | D | archive | folded (v13): the dependency graph PARSED from `Spec-Requires` and gated at seal | the seal machinery |
| ext-12 | R12-1 the round-11 matrix assigned WRITERS across atomic-primitive boundaries (native flattened copies routed through the import primitive) | D+C, executed | both | **folded (v14): THE WRITER-SPLIT MATRIX** — one row per ATOMIC WRITER × site, `validate_row_plan` CONTEXT-REQUIRED, cross-context refusals executed. **This is why §4c's flattening rides `apply_supersession_plan` and not the import primitive**, and why the implementation derives the rows inside the store rather than carrying them in the plan | §7b SITE-MATRIX; §7a; `WRITER_CONTEXTS`; `_write_absorption_flattening` |
| ext-12 | R12-2 one pre-R9 sentence survived (the naive reverse-link lookup) | D | 0020 | folded in 0020 (v14); the retired formulation joined a forbidden-phrase list the shipped verifier scans | `specs/lint_withdrawn.py` |
| ext-12 | R12-3 the advertised matrix/dependency seal was NOT SHIPPED — the reviewer's negative control passed the packaged verifier with exit 0 | E (the round's sharpest) | verifier | folded (v14): `_consistency_gates` ships INSIDE `verify_package.py` and runs every time; the negative control is now our regression | `verify_package.py`; `verify_package_selftest.py` |
| ext-13 | R13-1 the writer context was not BOUND to the row's operation key — an import row projected identically under missing, native-format, garbage and null keys. PRE-SEND MISS: the name-is-a-claim item | E+F, executed | both | **folded (v15): `construct_plan_row`** — the operation-aware constructor DERIVES `op_key` inside the primitive; callers never supply one, and every normative producer builds through it. **The implementation follows it: the native flattening calls the constructor and never mints a key by hand** | §7b (the 0009 row); `construct_plan_row`; `_write_absorption_flattening`; `ledger_plan_harness.py` |
| ext-14 | — ACCEPTED (0020 Accept · 0021 Accept · seam Accept · verifier PASS · archive PASS); no blocking findings | — | both | TWO NON-BLOCKING obligations, BOTH SHIPPED SAME-DAY | `ledger_plan_harness.py`; `vector_harness.py` |
| post-acceptance | `prune_absorbed_record` NON-TERMINATING on a record that is its own canonical absorber — found by DIFFERENTIAL FUZZING | implementation defect vs 0020's own contract | 0020 | fixed and DISCLOSED in both implementations, then DOMAIN-CLOSED (the whole absorber chain, refusing any revisit) | commits `cd5285b`, `2596f4f`; vectors 129–131 |

**Implementation state, kept separate from disposition** (the 0002 lesson —
"closed" silently meaning both was itself a finding). Slice A landed 0020's
normative core; slice B landed 0020's READ surfaces; **slice C landed this
spec's WRITE and MAINTAIN halves** — W8's cleared output identity, §4c's
absorption partition with write-time flattening, §4b's per-scope consolidation
with the additive-superset result and the amended audit contract, and W3's
mechanical registry. COVERED by executable checks: W1, W2, W3, W4, W5, W7, W8,
W9, W10, W11, W12, W13, W14 and W15's durability cell. NOT COVERED, and why:
**W6** is the live / D-extension cross-principal value probe (a real model and
the benchmark harness; a simulated leak probe measures the simulation);
**W16** and **W18**'s post-prune halves have no writer, because
`apply_retention_prune_plan` is FUTURE and §2c-ii asserts executably that no
shipped path prunes an absorbed edge — their born-closed and pre-prune halves
ARE covered; **W17** is carried by the shipped evidence program
`specs/evidence/0020/ledger_plan_harness.py`, which extracts the real DDL from
a live store, rather than by a weaker pytest copy. Q1–Q4 remain open as
recorded widenings, Q4 still riding the 0018 D2 window.
