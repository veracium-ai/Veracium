# Feature spec: scoped recall — the principal boundary (S1)

Spec-Status: draft
Spec-Requires: 0006, 0014, 0021

*From research's design proposal
(`veracium-research/proposals/scoped-recall-design-proposal.md` @ f9a5fb9b,
addenda 9f6fb286 / d808282b), internal round 1 (774097d0, PASS at v2),
external round 1 (RETURN, 7 findings — folded here as v3). Companion: spec
0021 (scope under derivation and consolidation). **The coupling is now
MACHINE-CHECKED (external F6): `Spec-Requires` is mutual — 0020 requires
0021 and 0021 requires 0020 — so acceptance is atomic under the existing
gate, the 0016/0018 precedent; 0014 is declared because the membership
join is load-bearing.** S3 (authenticated principals) is deliberately OUT
— see §8.*

## 1. Problem and motivation

Veracium's identity half shipped in 0006: every record can carry a durable
`(origin, source_id)` — which connector, agent, or device produced it,
revocation-joinable. The missing half is the PRINCIPAL BOUNDARY: *which
recalling party sees which records, and whose testimony is assertable to
whom.* Hosts running memory per-agent or per-session have no isolation —
every principal recalls every record with full assertability.

Done as machinery this is a trust feature on our own axis; done as a tag it
is the inert-field trap A1 names. This spec ships the machinery and adds NO
per-record field.

## 2. Field contracts touched

| field | read / written | documented contract | consumers | change here |
|---|---|---|---|---|
| `Provenance.origin`, `Provenance.source_id` | read only | 0006: opaque namespacing identity; **groups, never grants** (R3/I5); **not authenticated** (R7) | identity digest, revocation join | become the SCOPE KEY: policy rules key on the RESOLVED pair (0006 I9 — absent origin resolves to the local singleton before any comparison, the same read path the digest uses). **NO new per-record field** (Q1: policy-over-identity) |
| `recall(user_id, query, token_budget)` | signature widened | today: no principal notion | hosts, MCP | gains `principal: Optional[Identity] = None` and the §4e filter parameters. **`principal=None` is byte-identical to today — the migration invariant, test-named** |
| `answer(...)` (external F3) | signature widened | calls `recall()` internally | hosts, MCP | gains and THREADS `principal=` — an answer path that ignored the principal would be a public bypass of the whole boundary |
| queryless `recall()` → proactive assembly (external F3) | filtered | the session-start briefing | hosts | the principal filter applies to the proactive EDGE SET before assembly — same visibility relation, same code path as scoped recall |
| `Recall.edges` / `Recall.episodes` / `Recall.contested` / `ContestedGroup.exposed` (external F3) | filtered | structured records ride the response independently of rendered context | hosts, MCP | **the boundary is enforced on the STRUCTURED CARRIERS, not on rendered bytes** — every record object in a principal-bearing response satisfies the visibility relation; N-1's equivalence is over the FULL `Recall` value |
| operator surfaces: `introspect`, `export_memory`, `forget` (external F3) | unchanged, by decision | store-wide operator views | operators | take NO principal and remain unscoped in v1 — they are the OPERATOR's right-to-know/erasure surfaces, not principal surfaces. A named decision, not an omission; per-principal introspection is a recorded widening |
| gate / `assertable` partition | read only today | disclosure-keyed routing | gate, proactive, render | assertability becomes a RELATION between record provenance and recalling principal — RESTRICT-ONLY (§4b). The gate change leaves a NAMED SEAM for 0011's subject dimension (§7b) |
| the compiled wiki | read by `recall` | the grounded working view, compiled store-wide | recall's grounded block | **EXCLUDED from principal-bearing recall in v1 (§4d)** — the second synthesis path |
| scope POLICY | NEW — host-supplied, per-process | none today | recall, gate | lives beside the relations registry in `MemoryConfig`; **READ-SIDE ONLY (external F5): policy governs visibility and assertability at recall — it never governs maintenance.** Maintenance partitioning keys on IDENTITY alone (0021), so two hosts with different policies (or none) can differ only in what they SHOW, never in what the store MERGES. The store carries no policy; the host does |
| derived records | read via lineage | 0014: contributor rows key the digested resolved pair | scope membership | **the MEMBERSHIP-EVIDENCE HIERARCHY (external F1 — replaces v2's single rule):** see §4a-iii. Ledger evidence when present and complete; otherwise the derivative is UNRESOLVED and FAIL-CLOSED restricted. Missing evidence never silently means "shared" |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| `principal` (host-supplied at recall/answer) | None → unscoped call, byte-identical to today; **principal WITHOUT configured policy → REFUSED (R2-2 — feature-disabled never silently degrades to unscoped)**; source_id-less principal → REFUSED (I13) | non-Identity shape → refused (strict types) | an identity no record carries → sees only shared-visible records | **a host names another agent's identity as its principal** | C2 verbatim-class: `(origin, source_id)` is NAMESPACING, NOT AUTHENTICATED (0006 R7). S1's boundary is honest-host ISOLATION — context-bleed, confused deputy, cross-agent leakage — never a security boundary against a caller who forges identity. Authentication is S3, a separate spec |
| records with ABSENT identity — **PRODUCERS row (the internal-R1 class): the host's unidentified stream AND the store's own machinery (maintenance outputs, migration, imports)** | — | — | — | a writer omits identity to reach every scope | **unknown is the floor** (C3) for HOST-produced identity-less records: shared-visible, gate unchanged. **STORE-produced derivatives are NOT floor-defaulted — they take the §4a-iii evidence hierarchy (external F1), and unresolved evidence fails CLOSED (restricted), never open (shared)**. absent == absent is never SAME-scope (named test) |
| scope policy rules (host config) | no rules → every principal sees shared-visible + own-scope | malformed → refused at config load by the §4a-ii validator, never at recall time | — | a rule that tries to WIDEN | **RESTRICT-ONLY (C1):** the named refused cell — same-principal re-assertability — is a GRANT and is REFUSED; `test_same_scope_grants_nothing` fails if anyone builds it. Any grant wants a 0006 amendment, not this spec |
| filter parameters (§4e) | absent → no filtering | unknown field/op → refused (the closed §4a-ii grammar) | — | a filter referencing out-of-scope attributes as an oracle | M-2: filters apply AFTER scope, within the visible set — narrow only; leak-free by construction |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | expected result |
|---|---|---|
| no principal notion exists at recall today | `grep -n "principal" src/veracium/__init__.py src/veracium/gate.py` | no hits on the recall path |
| identity resolution is the shipped read path | `grep -n "resolve_origin" src/veracium/source_identity.py` | the 0006 I9 primitive |
| the READ surfaces this spec must cover (external F3) | `grep -n "def recall\|def answer\|edges\|episodes\|contested\|exposed" src/veracium/__init__.py src/veracium/schema.py \| grep -i "recall\|answer\|contested"` | the §4f inventory's carriers, no others |
| consolidation outputs today COPY the first input's identity (external F1 — the assumption v2 got wrong, now asserted as the DEFECT 0021 fixes) | `grep -n "inputs\[0\].provenance" src/veracium/store/sqlite.py` | `_derive_output_metadata`'s base line — origin/source_id inherited, not cleared |
| the ledger does not travel (portability) | `grep -n "ledger local\|settled outputs portable" src/veracium/store/sqlite.py specs/0014-maintenance-attribution.md \| head -2` | the 0014 locality rule |

*(Re-run at implementation; commands recorded per the 0005 rule.)*

## 3. Trust-class matrix — REQUIRED, blocking

**No trust class moves.** Scope is orthogonal to author/derivation and can
only subtract visibility/assertability:

| operation | scope consequence |
|---|---|
| unscoped recall/answer (`principal=None`) | byte-identical to today, every record, every store (the migration invariant) |
| scoped recall/answer, own-scope record | visible; assertability exactly as today's gate gives |
| scoped recall/answer, cross-scope record | visibility per policy; **assertability at most today's** — v1 pins the third-party-testimony disclosure shape |
| scoped recall/answer, HOST-produced absent-identity record | shared-visible, gate unchanged (C3) |
| scoped recall/answer, UNRESOLVED derivative (§4a-iii) | NOT visible to any scoped principal; visible unscoped (fail-closed, external F1) |
| any write path | UNTOUCHED — this spec changes no write, no lifecycle transition (0021 owns derivation/consolidation) |

**Write-time or maintain-time?** Neither — S1 is READ-time only, and
POLICY is read-side only (external F5): maintenance partitioning is
identity-driven and policy-independent, ruled in 0021 §3.

## 3b. Authorization and scope

- **Who supplies the principal:** the HOST, per call — same trust domain as
  every other host input. No Veracium-mediated surface invents one; MCP
  passes the host's declared principal through or nothing.
- **What it reveals:** scoped responses reveal LESS; the two disclosure
  cells are §4c.
- **The stated line (N-1 vs N-2/M-3, once):** *lifecycle truth about YOUR
  VISIBLE records renders (supersession status, contention linkage —
  content of invisible parties stripped); metadata about what scope
  WITHHELD does not exist on the principal surface (operator/telemetry
  material, 0017's consent framework as carrier); metadata about the
  VISIBLE set may render (M-3).*

## 4. Behaviour

### 4a. The principal model

A principal IS an `(origin, source_id)`-class identity — the shipped
namespace; one identity model, one revocation join. Policy rules are
host-supplied per-process (`MemoryConfig`, the relations-registry
precedent) and evaluated over RESOLVED identity (0006 I9), never raw
fields.

### 4a-ii. The normative models and grammars (external F2)

**The executable reference is `specs/evidence/0020/reference_scope.py`
with `specs/evidence/0020/vectors.json` and the SELF-EXECUTING HARNESS
`vector_harness.py` (external R3's artifact ask — the seal runs it and
ships its recorded result; each vector kind has a documented schema).
Membership lives in DIGEST SPACE (external R3-2): the reference MIRRORS
the shipped `source_identity_digest` construction byte-for-byte
(`veracium.source-id.v1`, framed — 0006 §4 rules 6/7), because the 0014
ledger carries only nullable one-way digests and deleted inputs cannot
supply original pairs — policy-side digests therefore equal store-side
digests and the resolver is implementable from real rows.** It defines,
exactly:

- **`Identity`**: `{origin: str|None, source_id: str|None}`, strict-typed
  with the SHIPPED bounds (non-empty, ≤512 chars — the Provenance field
  caps; external R3-1). `resolve(identity,
  local_origin)` — absent origin → the local singleton (I9), UNIFORMLY (no
  special cases; the v3 carve-out contradicted I9). **Groupability is
  ACCEPTED 0006's, verbatim (R2-1): an absent `source_id` yields NO
  groupable identity, REGARDLESS of origin (I13); absence never relaxes a
  rule (I3).** A non-groupable identity equals nothing, including itself;
  a PRINCIPAL must be groupable (a source_id-less principal REFUSES).
- **`ScopePolicy`**: REGISTRY-AUTHORITATIVE (external R5-2 — the R4-1
  seal was RE-SIGNABLE: `_seal` and its nonce are reachable module
  attributes, so a caller could flip a field and recompute the seal; the
  reviewer executed exactly that): `validate_policy` deposits an
  immutable canonical snapshot in a VALIDATOR-OWNED registry keyed by the
  policy instance, and `classify` refuses on ANY divergence between the
  object's visible state and the registered snapshot — re-signing does
  not help because the seal is no longer the authority. The reviewer's
  four executed bypasses are refusal vectors by name (incl.
  `resign_after_flip`, their round-5 attack verbatim). **THE THREAT
  CLAIM, NARROWED HONESTLY (R5-2's alternative, taken alongside the
  fix): in-process Python cannot defend against a caller that rewrites
  this module's own state — the construction is accidental-misuse-proof
  and forgery-evident, not adversarial-caller-proof; the adversarial
  boundary is S3's, consistent with C2.** Shape checks remain the first
  line; direct construction with raw shapes still RAISES. `validate_policy` refusals, enumerated:
  non-Identity shapes; non-groupable members (I13); resolved-DIGEST
  overlap across groups; `cross_scope_visible` not a REAL bool ("false" /
  0 / 1 refuse — actual ints vectored, R3-1); members not a LIST or TUPLE
  (SETS refused — unordered inputs are not a rule grammar); overlong
  identities (the 512 bounds). The validator retains no caller state.
  The grammar is CLOSED; wildcards/patterns are a recorded widening.
- **The two disabled-vs-empty states (external R2-2):** feature-disabled
  (no policy configured) **REFUSES a principal-bearing call** — it cannot
  honour scoping and never silently degrades to an unscoped, fully-
  assertable view. CONFIGURED-EMPTY (a policy with no groups) is a valid
  state: the principal is ungrouped — own-identity records are OWN, the
  host pool is SHARED, every other identified record is CROSS.
- **The record→membership RESOLVER (the 0020↔0021 seam, normative and
  IMPLEMENTABLE FROM REAL ROWS — external R3-2):** `membership(record,
  rows, op_state, local_origin, expected_contributors) → digest |
  SHARED_POOL | UNRESOLVED` consumes the SHIPPED `ContributionRecord`
  shape — `{site, identity_digest: str|None, op_key}` keyed by
  survivor_id — with completeness judged against the store-derived
  denominator (lineage length); no Identity reconstruction is ever
  required. Total over every 0010 state. The LEGACY-DERIVATIVE predicate
  matches the REAL operation-id form (`op-<12 hex>` — corrected from v4's
  fictional `consolidate:` prefix by the reviewer's store probe);
  recovery cannot clear an already-OUTPUTS_DURABLE output — caught by the
  predicate, by shape. **ABSORPTION SURVIVORS are resolved through their
  ledger rows (external R3-3, reviewer-executed): a pre-0021 absorption
  moves another identity's testimony and currency into a survivor that
  carries identity A with NO lineage — the resolver therefore checks
  every absorption row against the record's OWN digest, and ANY
  cross-digest (or None-vs-digest) contributor marks the survivor
  UNRESOLVED. The ledger said B; the record claims A; fail closed.**
  Membership pools are PER-DIGEST, finer than policy groups; a
  same-group-two-identity derivative is pre-feature by construction and
  UNRESOLVED (a named vector). The shared pool's reserved result key is
  `pool:unidentified` (R3-4 — digests are 64 hex chars; a colon-bearing
  literal cannot collide).
- **The visibility decision function** `classify(record_evidence,
  principal, policy) → OWN | SHARED | CROSS_* | UNRESOLVED` and its fixed
  table: OWN → visible, today's assertability; SHARED → visible, today's
  gate; CROSS → visible iff `cross_scope_visible`, third-party-shaped;
  UNRESOLVED → invisible to every scoped principal.
- **The filter grammar** (§4e): fields CLOSED to `{subject, relation,
  author_of_evidence, source_id, volatility}`; eq only; at most one term
  per field. A `source_id` filter NEVER matches a cleared derivative (its
  field is None; the ledger holds only a one-way digest — R2-3, a named
  vector). Every extension is a spec change.

The vectors (the COUNT lives in one carrier — `review_manifest.json`'s
`vector_count`, with the recorded harness result as its execution proof;
round-8 bin (b) caught this paragraph and reviews.py drifting from the
manifest, so prose carriers no longer state a number) enumerate every
`classify` cell (both refusal states), every policy-refusal cell (real
ints, sets, bounds), the DIRECT-CONSTRUCTION oracle (the reviewer's
executed bypass, cell by cell, plus the round-7 leaf-mutation attack),
the mutation oracle, the FULL resolver table over REAL row shapes
(consolidation completeness × digests × operation state, PLUS the
absorption-survivor cells including R3-3's cross-digest case), the
closure table (legacy, typed-ref, flattened, pruned, corrupt), the
reconstruction table, and every filter cell — executed by the shipped
harness, whose recorded result ships in every package.

### 4a-iii. Derived records — the membership-evidence hierarchy (external F1)

Hosts are not the only producers of identity-less records — MAINTENANCE
is. **The shipped defect, named (reviewer-executed):** consolidation
outputs today COPY the first input's provenance identity
(`_derive_output_metadata`, `inputs[0].provenance` without clearing
`origin`/`source_id`) — a mixed A+B derivative claims identity A, and
export/import then strips its ledger rows, destroying the membership
evidence while keeping the false identity. 0021 §4a makes clearing that
inherited identity an IMPLEMENTATION OBLIGATION with the reviewer's probe
as its regression (0021 W8).

Membership evidence for a record whose own resolved identity is the local
store with NO source_id (the store-authored shape), in order:

1. **Ledger evidence** (0014): the contributor rows for the derivative,
   PRESENT, COMPLETE (the exact-set property the ledger already enforces
   at write) — **and, for absorption survivors, TRANSITIVELY CLOSED
   (external R7-1, the round-7 architectural finding).** The reviewer's
   chain: `A` (scope A) absorbed by `B` (scope B), then `B` absorbed by
   `C` (scope B) — C's DIRECT row carries only B's digest, which equals
   C's own scope, so a single-level read classifies C own-scope while C
   transitively contains A's testimony. The contract is therefore dual —
   and LEDGER-RESIDENT (external R8-1, which executed the v9 form's
   fragility: the v9 walk chained through free-text `absorbed_by:` notes
   on the absorbed RECORDS, and a pruned intermediate takes its note —
   the only link — with it, leaving a walk that LOOKS complete while an
   ancestor's foreign digest is gone):
   - **Write-time flattening (0021 §4c, post-0021 stores):** an
     absorption writes onto the survivor the absorbed prior's identity
     digest AND copies of the prior's transitively CLOSED row set, in
     the same atomic operation — row sets are BORN closed (copies carry
     the `flattened` payload class: counted as evidence, never
     re-walked); and every absorption row carries the TYPED
     **`contributor_ref`** (the 0014 amendment's columns — the shipped
     absorption draft already supplies contributor_type/contributor_id;
     the store stops dropping them). **THE DURABILITY MODEL, stated
     against accepted 0014 A10 (our own pre-send catch — the ledger is
     NOT append-only: `_drop_contributions_for_survivor` drops a
     record's rows when the record is deleted):** the durable object is
     the SURVIVOR'S OWN row set, which lives exactly as long as the
     survivor does — born-closed flattening means pruning an
     intermediate touches only rows keyed to IT, and the survivor's
     ancestry is untouched. Closure is BY CONSTRUCTION, not by ledger
     immortality.
   - **Read-time closure:** `close_absorption_rows` (the normative
     reference): ref-bearing row sets stand on the write invariant
     (W14), with OPPORTUNISTIC verification where a contributor's rows
     are still present (its digests must appear among the survivor's —
     a mismatch is corrupt → None; absence proves nothing under A10 and
     fails nothing — the DISCLOSED residual: a W14-violating writer
     plus a subsequent prune is undetectable read-side, vectored as a
     statement) — with the
     note-derived link walk as the LEGACY fallback for pre-amendment
     rows, whose absorbed records' digest multiset must exactly account
     for every unattributed row. A legacy row whose contributor's record
     was pruned (R8-1's cell), an unknown linked digest, a multiset
     mismatch, one absorbed id under two absorbers, or a cyclic path
     closes to None — and **None IS UNRESOLVED**, before the resolver
     ever runs. **The DISCLOSED behaviour delta:** legacy absorption
     survivors whose contributors are unavailable are UNRESOLVED where
     the single-hop read called them own-scope — a fail-closed widening,
     remediable by re-derivation.
   - **The retention contract (R8-1; reparenting added under R9-1; made
     INSERT-ONLY under R10-1 — accepted 0014 says a ledger row is
     inserted and NEVER updated or replaced, and the v11 "upgrade" was a
     payload mutation the v11 harness could only demonstrate by
     bypassing the store validator with raw SQL):** no shipped path
     physically prunes an absorbed edge today (mechanically asserted,
     0021 §2c-ii). ANY future pruning capability MUST, before the A10
     row-drop: for every CANONICAL row on the pruned record with
     contributor X, INSERT a NEW `scope-attribution` row on the pruned
     record's own canonical absorber — payload
     `{"reparented_from": <pruned id>}`, X's digests carried, the prune
     operation's injective per-row op key — X's new canonical reverse
     link. The absorber's existing flattened copy is UNTOUCHED
     (immutable, non-canonical by class). Where even the flattened copy
     is missing (a W14 violation surfacing at prune time), the inserted
     row is the closure-incompleteness MARKER instead (identity_digest
     None, payload `{"closure": "incomplete"}`). The reference models
     the whole step (`prune_absorbed_record`, insert-only, every row
     validator-checked), and the ledger harness executes it over
     SQL-stored rows — INSERT and A10-DELETE only, no UPDATE exists —
     before AND after the prune, for both the valid-reparent and
     missing-copy states.
   - **The EXPORT reverse-link algorithm (R9-1 — v10's "find the row
     whose contributor_ref names this record" had TWO answers under
     flattening and ZERO after a prune; the canonical predicate made
     CLASS-TOTAL under R10-2):** `derive_absorbed_by` is normative.
     CANONICAL rows for a contributor are, BY SITE AND CLASS: native
     `absorption` and `imported-absorption` rows (direct links), and
     `scope-attribution` rows of the REPARENTED class. Plain flattened
     copies are NEVER canonical — **and neither is the
     closure-incompleteness marker (R10-2's executed launder: the v11
     predicate keyed only on the flattened flag, so the marker counted
     as canonical and a DETECTED W14 violation materialised a clean
     `absorbed_by_id`)**; a contributor whose only trace is the marker
     derives to None — the export OMITS, the import-side note rule
     fails closed. Exactly one canonical row → its survivor is
     `absorbed_by_id`; ZERO → the exporter OMITS the field and the
     record travels as legacy; MORE THAN ONE → `ExportLinkageError`,
     the whole export REFUSES — corrupt linkage must not become a
     portable file that looks clean.

   All contributors (over the CLOSED set) resolve to one scope → the
   derivative is that scope's. Contributors span scopes → cannot occur
   post-0021 (W1 refusal); a pre-existing mixed derivative — including a
   mixed CHAIN — is UNRESOLVED. All contributors unidentified → the
   shared pool (its derivatives stay in the pool). The stated residual is
   unchanged: pre-0014 absorptions left no rows and no links; their
   survivors resolve by own identity (0021 §4d's disclosure).
2. **No/partial ledger evidence → UNRESOLVED, fail-closed:** invisible to
   every scoped principal; visible on the unscoped surface; never a merge
   candidate (0021 W9). The populations, enumerated: LEGACY pre-0021
   outputs; IMPORTED derivatives (the ledger is local-only and does not
   travel — the reviewer's export/import probe); outputs of pre-feature
   IN-FLIGHT operations completed by recovery; any derivative whose
   ledger rows fail the completeness check. **IMPORTED ABSORPTION
   SURVIVORS — the import-time RECONSTRUCTION rule, v9 form (external
   R7-1/R7-2/R7-3 rebuilt the v8 construction):**

   - **PRE-COMMIT (R7-2):** reconstruction runs on the records AS PARSED
     FROM THE EXPORT FILE, before any destination write. A refusal
     (`ImportLinkageError`) means the importer never writes — the
     destination is byte-identical to before the attempt. (v8 stated
     whole-import refusal but ordered nothing; the reviewer committed
     three imports and only then watched reconstruction fail.)
   - **STRUCTURED LINKAGE IS THE NORMATIVE CARRIER, WITH A DURABLE
     SOURCE (R7-2, rebuilt under R8-2):** the export materializes each
     absorbed record's winner as a structured `absorbed_by_id` field
     derived FROM THE LEDGER's typed `contributor_ref` link (find the
     row whose contributor_ref names this record → its survivor) —
     NEVER from the note whose ambiguity motivated the field (R8-2's
     point: an exporter cannot reliably materialize structure from the
     same free text). The field is therefore derivable exactly for
     post-amendment absorptions; legacy absorptions export note-only and
     take the legacy rule below. **The FORMAT allocation (R8-2's
     carrier conflicts, corrected):** accepted 0016/0018/0019 freeze the
     FORMAT-7 shape, so the field lands as a DRAFTED RIDER AMENDMENT to
     that frozen shape (0021 §7b; same-commit landing at acceptance,
     the 0014-rider precedent), riding the SAME 0018 D2 breaking window
     that already carries 0021's enforcement bump (Q4) and the SCHEMA-v8
     ledger columns — one break, all three riders; linkage only, NOT the
     full-membership materialization, which stays the recorded widening.
     The v8 note REGEX is RETIRED: `Edge.id` permits the framing
     punctuation, so the regex rejected valid native exports
     (reviewer-executed, three cases). For LEGACY files the rule is the
     DECIDABLE one: the LAST `absorbed_by:` tag governs and is the only
     tag that must resolve (earlier incidental tags are ignored — v8
     contradicted its own last-tag rule); candidates are matched against
     the export's own id universe under the shipped framings; exactly
     one resolves, zero or multiple REFUSE — ambiguity is irreducible in
     free text that may embed ids, so refusal plus the structured
     carrier is the honest pair.
   - **TRANSITIVE (R7-1):** each absorbed record's digest propagates to
     its direct winner and every transitive absorber (transitive copies
     carry the `flattened` payload class) — reconstructed row sets are
     born closed, matching the write-time flattening; cyclic chains
     refuse.
   - **COMPLETE ROWS (R7-3, completed under R8-3; SITES split under
     R10-1):** every reconstructed row carries its site — DIRECT links at
     `imported-absorption` (payload exactly `{"reconstructed": true}`),
     transitive copies at `scope-attribution` (payload
     `{"flattened": true, "reconstructed": true}`) — identity_digest,
     the typed `contributor_ref` (the post-remap absorbed record id —
     the contributor BINDING that determines which exported record
     supplies the evidence digest), `evidence_ref_digest` (the shipped
     construction over the absorbed record's resolved origin +
     evidence_ref), and a PER-ROW op key in the
     INJECTIVE framed-digest form (`row_op_key`:
     `{op}:{site-token}:{sha256(framed(survivor) +
     framed(contributor))}` — R9-2 executed the v10 plain colon-join's
     collision over delimiter-bearing ids, the same class as the R7-2
     note grammar; the prefix fields are colon-free by construction and
     the id pair is framed into one fixed-width digest). v9's
     one-op-key-on-every-row violated the accepted UNIQUE partial index
     (reviewer-executed IntegrityError); `import_op` is
     the ONE `op-<12hex>` id the import operation mints. The site's 0014
     semantics are unchanged: NO absorption payload and NO REVERSAL
     (ATTRIBUTION evidence only). Persisting these rows atomically with
     the records is the 0009 §4c primitive AMENDMENT (exact text +
     stored-row construction + DDL: 0021 §7b).

<!-- SITE-MATRIX (generated by reference_scope.render_site_matrix — R11-1: ONE source; the seal byte-compares this block across every carrier) -->
| site | writers | closed payload classes | canonical? | in the exact set? | op-key form |
|---|---|---|---|---|---|
| `absorption` | the shipped store (apply_supersession) — ACCEPTED 0014, not amended | {base, contributor} (the accepted closed schema) | YES (direct link) | YES — the accepted direct-invalidation equality counts exactly these | the accepted native idiom, unchanged |
| `imported-absorption` | the import path ONLY (the amended 0009 primitive), from pre-commit reconstruction — DIRECT links | {"reconstructed": true} EXACTLY | YES (direct link) | NO — never counted | row_op_key(import_op, "imported-absorption", …) |
| `scope-attribution` | the amended 0009 primitive: write-time flattening (native + imported transitive copies) and the retention contract's prune step (reparented links, markers) — ALWAYS insert-only | {"flattened": true} · {"flattened": true, "reconstructed": true} · {"reparented_from": <id>} · {"closure": "incomplete"} | ONLY the reparented class; flattened copies and markers NEVER | NO — structurally excluded (its own site) | row_op_key(op, "scope-attribution", …) — import, absorption, or prune op |
<!-- /SITE-MATRIX -->

   The residual narrows to absorbed priors pruned before export.
   **Missing membership evidence never silently means "shared."** The
   operator remedies are restatement or re-derivation under 0021;
   materializing FULL MEMBERSHIP at export remains a recorded widening
   (distinct from the linkage field above, which carries no membership).

### 4b. Scoped assertability — restrict-only

The gate's assertable predicate becomes the relation of §4a-ii's decision
table. No promotion path exists: same-scope status never raises trust,
never clears `ungrounded`/`needs_confirmation`, never lifts disclosure.
`test_same_scope_grants_nothing` enumerates the tempting cells (the
own-inference re-assertability cell by name) and fails on any grant.

### 4c. Response-surface disclosure — the two pinned cells

- **N-1, existence non-leakage:** a principal-facing response is
  INDISTINGUISHABLE between nothing-exists and everything-withheld —
  **equality over the FULL `Recall` value (context, grounded, unverified,
  edges, episodes, contested, tokens_estimated, truncated — every
  structured carrier), not rendered bytes (external F3)** — for an empty
  store vs an all-out-of-scope store on the same query (test-named).
  Withholding counts/rates are OPERATOR-side only. Composition sentence,
  verbatim: *a scope-blinded agent saying "no record" is isolation
  WORKING, not abstention failing.*
- **N-2, superseded-by-invisible:** supersession STATUS is global truth
  and renders; the superseding record's CONTENT and ATTRIBUTION follow
  scope and do not render — on the rendered context AND the structured
  carriers (a `Recall.contested` group exposes only visible members;
  cross-scope challengers appear as content-free linkage). Precedent:
  accepted 0003 §4c-ii/Corr-A — cited, not re-derived. Residual accepted
  with eyes open: the bare status reveals that out-of-scope testimony
  exists — the price of global truth.

### 4d. The wiki — the second synthesis path (N-3)

The compiled wiki is a store-wide LLM re-rendering; the general rule,
recorded: **every LLM re-rendering the scope machinery doesn't control is
a laundering site** (the 0019 F4 precedent). **V1: principal-bearing
recall and answer EXCLUDE the shared wiki** (subgraph-only assembly); the
wiki remains the no-principal surface's view. Per-scope wiki compilation
is a recorded option for the 0021 era, cost-gated. Named test: no wiki
content in any principal-bearing response.

### 4e. Metadata filtering (the folded demand signal (b))

Under the four rails (research §8): **M-1** filters SELECT, never STRIP —
the narrowest result still renders full disclosure (markers, superseded
status, `ungrounded`, attribution). **M-2** after scope, within the
visible set; narrow only. **M-3** empty-result reporting IS
principal-facing here ("your filter matched 0 of the records visible to
you") — computed within the visible set; the §3b line governs. **M-4**
source-field filters evaluate over resolved identity; the grammar is
§4a-ii's, closed and deterministic.

### 4f. The complete read-surface inventory (external F3)

| surface | carrier(s) | scoped how |
|---|---|---|
| `recall(query, principal=…)` | rendered context + `Recall.edges/.episodes/.contested` | the visibility relation on the EDGE/EPISODE SET before rendering; structured carriers carry only visible records |
| `recall(None, principal=…)` → proactive | the briefing + the same structured carriers | the relation on the proactive edge set before categorization |
| `answer(query, principal=…)` | the answer string (built from a recall) | threads `principal` into its internal recall — never calls unscoped |
| `Recall.contested` / `ContestedGroup.exposed` | full `Edge` objects | only visible members exposed; cross-scope challengers = content-free linkage (N-2) |
| MCP tools (recall/answer-shaped) | the same values over MCP | pass the host's principal through; no new fields |
| `introspect`, `export_memory`, `forget` | operator surfaces | UNSCOPED in v1 by decision (§2); per-principal introspection is a recorded widening |
| the wiki | excluded from principal-bearing responses (§4d) | — |

The inventory is pinned by a generated PUBLIC-CARRIER MANIFEST
(`specs/generated/0020-read-surfaces.md`, the 0014 CONSUMPTION_SITES
precedent): a public read path returning records that is absent from the
manifest fails `test_read_surface_manifest_is_total`.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| store with no identities, no principals ever | READS and stored state byte-identical to today; `maintain()`'s return is the additive superset (R4-2/R5-3 — values of existing keys identical) |
| principals adopted, unscoped call | byte-identical to today (the shared view) |
| scoped call, mixed store | own-scope full; cross-scope per policy + third-party-shaped; host-produced absent-identity shared-visible; UNRESOLVED derivatives invisible |
| scoped call, everything out of scope | full-`Recall` equality with the empty store (N-1) |
| cross-scope supersession of a visible record | status renders; superseding content/attribution do not, on every carrier (N-2) |
| scoped call + filters | scope first, then narrow (M-2); M-3 reporting |
| `answer()` with a principal | identical boundary to recall — no bypass |
| MCP default stream (no identities supplied) | NO isolation exists — adoption-path honesty: scoping is opt-in by supplying identity; docs and the marketing rail say so plainly |

## 6. Invariants and executable checks — REQUIRED, blocking

**Status: STAGE-5 OBLIGATIONS — none exists yet (draft).**

| invariant | executable check |
|---|---|
| V1 unscoped READS byte-identical to today over a FIXED store state (R2-4 — maintenance deltas are 0021's disclosed change, cross-referenced) | `test_no_principal_is_byte_identical` |
| V2 restrict-only, by enumerated temptation | `test_same_scope_grants_nothing` |
| V3 empty-vs-withheld indistinguishability over the FULL `Recall` value (external F3) | `test_existence_non_leakage` |
| V4 cross-scope supersession/contention rendering on every carrier | `test_cross_scope_supersession_rendering` |
| V5 no wiki content in principal-bearing responses (recall AND answer) | `test_scoped_recall_excludes_wiki` |
| V6 absent==absent never SAME-scope | `test_unknown_identity_is_not_a_principal` |
| V7 policy over resolved identity | `test_policy_evaluates_resolved_identity` |
| V8 filter rails M-1..M-4 | `test_filter_rails` |
| V9 the 0011 gate seam | `test_gate_seam_reserved_for_0011` |
| V10 the shipped surface matches the normative reference on every vector, via the SHIPPED HARNESS (external F2/R3) | `test_scope_reference_vectors` |
| V14 absorption survivors resolve through their ledger rows OVER THE TRANSITIVELY CLOSED SET; any cross-digest contributor → UNRESOLVED (external R3-3; closure per R7-1 — the single-level read misclassified the reviewer's A→B→C chain) | `test_absorption_survivor_membership` |
| V15 three-hop absorption chains fail closed NATIVE and RESTORED: the A→B→C survivor is UNRESOLVED on the origin store (closure) and on an import destination (transitive reconstruction), including under remap and after reopen (external R7-1) | `test_transitive_absorption_chains` |
| V16 import linkage reconstruction is PRE-COMMIT: missing/unresolvable/ambiguous/cyclic linkage refuses BEFORE any destination write and the destination is byte-identical after the refused attempt (external R7-2) | `test_import_reconstruction_precommit` |
| V17 the closure survives the retention lifecycle: an A→B→C store whose intermediate is physically pruned classifies the survivor UNRESOLVED after close/reopen (typed-ref rows walk inside the ledger; a ref-less pruned legacy chain fails closed) — the R8-1 regression | `test_closure_survives_pruning` |
| V18 the ledger-row plan is storable AGAINST THE ACCEPTED DDL: multi-row single-operation inserts pass the real UNIQUE partial op_key index via per-row INJECTIVE keys (delimiter-bearing ids never collide — R9-2); NULL-digest contributors deduplicate by the ONE canonical plan id, and history/evidence drift never skips as equal (R9-3); idempotent re-import writes nothing; concurrent imports linearize (external R8-3) | `test_ledger_plan_against_real_ddl` |
| V19 the export reverse link is unique on both sides of a prune; zero canonical rows omit the field, more than one refuses the export (external R9-1) | `test_export_reverse_link_unique` |
| V11 `answer()` and proactive thread the principal; structured carriers carry only visible records (external F3) | `test_all_read_surfaces_scoped` |
| V12 the read-surface manifest is total (external F3) | `test_read_surface_manifest_is_total` |
| V13 UNRESOLVED derivatives are invisible to every scoped principal and visible unscoped (external F1) | `test_unresolved_derivative_fail_closed` |

## 7. Failure modes and reversibility

- **Misconfigured policy** fails at config load, never mid-recall.
- **Forged principal**: out of threat model by C2 — stated; S3 upgrades.
- **Reversibility (external F5, restated honestly):** READ-side behaviour
  is config-only reversible — drop the policy and recall is byte-identical
  to today. MAINTENANCE effects are NOT policy-dependent and NOT
  reversible by config: 0021's identity partitioning applies to
  identity-bearing stores regardless of policy, and consolidation's
  deletions/derivatives are permanent once run (0021 §7). **The no-change
  claim, NARROWED (external R8-2 — the blanket form contradicted the
  evidence carriers):** the READ feature itself adds no record field
  visible to hosts and no read-path migration; the COUPLED
  implementation's evidence carriers — the ledger's contributor columns
  (SCHEMA v8), the export linkage field (the FORMAT rider), and 0021's
  writer enforcement (Q4) — all ride the ONE 0018 D2 breaking window
  (0021 §7b riders), never a break of this spec's own.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `MemoryConfig` | scope policy (validated at load per §4a-ii) |
| `recall()` / `answer()` / MCP | `principal=` + filter params; proactive threading |
| `Recall` carriers | visibility-filtered record sets (§4f) |
| `gate.py` | the assertability relation + the 0011-reserved seam |
| `specs/evidence/0020/` | `reference_scope.py` + `vectors.json` (normative, F2) |
| `specs/generated/0020-read-surfaces.md` | the generated carrier manifest (F3) |
| docs | isolation-vs-boundary (C2 verbatim-class); the adoption path; the UNRESOLVED-derivative operator remedies |
| telemetry | withholding rates deferred to a future consent version (recorded) |
| CHANGELOG / marketing rail | never parity-chasing; isolation-only claims until S3 |

### 7b. Cross-spec carriers

| spec | touchpoint | disposition |
|---|---|---|
| 0006 | identity, resolution, groups-never-grants, R7 | inherited wholesale; any grant = a 0006 amendment |
| 0014 | the membership join (**declared in Spec-Requires — external F6**) | load-bearing for §4a-iii; the completeness check is the ledger's own exact-set property |
| 0003 | §4c-ii content-free linkage | cited as N-2's precedent |
| 0011 (draft) | the subject dimension | orthogonal in v1; the seam reserved (V9) |
| 0021 | **MUTUAL `Spec-Requires` (external F6)** — acceptance is atomic, the 0016/0018 precedent | 0020's §8 claim is CONDITIONAL on 0021 wherever maintenance runs; neither accepts alone |
| 0017 | the operator-side withholding channel | future consent-versioned field; deferred, recorded |
| 0018 | the breaking window | **REQUIRED by the coupled implementation (R8-2 corrected the v9 "not needed" row):** the D2 window carries the three riders — SCHEMA-v8 ledger contributor columns (the 0014 amendment + the final-form 0019 rider, 0021 §7b — accepted 0019 froze v8 no-DDL and is amended, not assumed; R9-4), the FORMAT export-linkage field (rider to the frozen v7 file shape), and 0021's writer enforcement (Q4). The READ surface alone still needs no break |

## 8. Claims and limits

**Claim:** with a scope policy configured and identities supplied, a
recalling principal sees its own scope fully, sees cross-scope material
only as policy admits and never as assertable testimony, cannot learn what
was withheld, and cannot reach withheld content through ANY public read
surface. **The zero-change guarantee is READ-SCOPED (external R2-4): an
unscoped READ over a FIXED store state is byte-identical to today.
Maintenance on an identity-BEARING store changes under 0021 §2 regardless
of policy (per-identity pools; the disclosed behaviour change), so stored
state — and therefore later reads — may lawfully differ from a
never-upgraded store. Identity-FREE stores: READS and stored STATE are
byte-identical end to end; `maintain()`'s RETURN is a compatible
ADDITIVE SUPERSET (0021 §4b — existing keys preserved verbatim, new keys
added; external R3-4 corrected the v4 claim that it was untouched).**

**Limits:** (1) isolation, not a boundary — C2 verbatim; S3 is the
boundary. (2) No identities → no isolation; adoption is opt-in.
(3) Scope shards visibility, not truth — lifecycle is global (N-2's
residual). (4) The wiki is excluded, not scoped, in v1. (5) Policy is
per-process and READ-side only; maintenance conduct is identity-driven
(0021) and no host's policy can widen or narrow it. (6) UNRESOLVED
derivatives (legacy/imported/recovered) are invisible to scoped
principals until re-derived — the fail-closed cost, stated.

## 9. Brief for the external reviewer

The seam we are LEAST certain of, per your standing request: **the §4a-ii
policy grammar's minimality.** One-group-membership with refusal-on-
overlap and eq-only filters is deliberately the smallest closed surface,
chosen so the decision table stays exhaustively vectorable — but real
hosts may need overlapping visibility sets (an auditor principal that
sees two scopes) on day one, and the recorded-widening path may be doing
load-bearing work the v1 grammar should carry. Attack the decision table
with host topologies we haven't imagined; the vectors file is the
contract. Second seam: §4a-iii's completeness check leans on the 0014
ledger's exact-set property — if you can construct a derivative whose
ledger rows PASS completeness while misrepresenting membership, that
breaks the hierarchy's first rung.

## 10. Open questions

| # | question | state |
|---|---|---|
| Q1 | field vs policy | RESOLVED: policy, no field (design review) |
| Q2 | absent-identity default | RESOLVED: shared-visible for HOST-produced; evidence hierarchy for store-produced (external F1 split the cell) |
| Q3 | 0011 interaction in v1 | RESOLVED: none; seam reserved (V9) |
| Q4 | per-scope wiki compilation | DEFERRED, cost-gated (§4d) |
| Q5 | overlapping visibility sets (auditor principals) | OPEN — the §9 seam; v1 refuses overlap; widening needs its own review |
