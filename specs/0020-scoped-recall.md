# Feature spec: scoped recall — the principal boundary (S1)

Spec-Status: accepted
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
     derived FROM THE LEDGER's typed `contributor_ref` link by the
     CANONICAL-CLASS algorithm (`derive_absorbed_by`, normative in the
     reverse-link bullet below: exactly one canonical direct/reparented
     row → its survivor; zero → omit; multiple → the export refuses —
     R12-2 caught this sentence still carrying the pre-R9 naive lookup,
     which has multiple answers under flattening) —
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
| atomic writer (operation context) | operation-ID domain | site | payload subset | canonical? | in the exact set? | per-row key form |
|---|---|---|---|---|---|---|
| `apply_supersession_plan` (native — accepted 0003 §4f CAS plan, accepted 0014 rows) | `sup-{edge.id}` (the shipped idiom; unrestricted suffix) | `absorption` | {base, contributor} (the accepted closed schema — NOT amended) | YES (direct link) | YES — the accepted direct-invalidation equality counts exactly these | the accepted native idiom, unchanged |
| `apply_supersession_plan` (native, post-0021 — the §4c flattening rides the SAME plan) | `sup-{edge.id}` | `scope-attribution` | {"flattened": true} ONLY | NO (flattened copy) | NO — structurally excluded | native_row_op_key(op_id, survivor, contributor) — the ALL-FRAMED digest form (the native op id embeds unrestricted text, so it is framed INTO the digest, never a prefix) |
| `commit_outcome_import_plan` (import — accepted 0009 §4c, purpose-built; rows derive ONLY from `reconstruct_absorption_rows`) | `op-<12hex>` (minted once per import) | `imported-absorption` | {"reconstructed": true} EXACTLY | YES (direct link) | NO — never counted | row_op_key(import_op, "imported-absorption", …) |
| `commit_outcome_import_plan` (import — transitive copies) | `op-<12hex>` | `scope-attribution` | {"flattened": true, "reconstructed": true} ONLY | NO (flattened copy) | NO — structurally excluded | row_op_key(import_op, "scope-attribution", …) |
| `apply_retention_prune_plan` (FUTURE — the retention contract's primitive, NAMED here; minted as its own 0009-family §4 amendment at implementation; no shipped path prunes today) | `op-<12hex>` (minted once per prune) | `scope-attribution` | {"reparented_from": <id>} · {"closure": "incomplete"} ONLY | ONLY the reparented class; markers NEVER | NO — structurally excluded | row_op_key(prune_op, "scope-attribution", …) |
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

## Review closure

*(PROCESS §4a — one row per finding. The rounds were COUPLED with 0021, so
every finding of every round is listed here with its OWNER: an omission and
a hand-off must not look alike. `evidence` names the artifact that closes
the row — a spec section for a design ruling, and additionally a vector,
harness, test or commit wherever code exists. Round reports are verbatim in
`specs/reviews/0020-0021/round-N.md`; the compressed per-round dispositions
are `specs/reviews.py`, which is the source the STATUS index renders from.
Rounds: internal 1, external 1–14 (findings 7→7→5→3→4→3→4→3→5→5→5→3→1→0),
plus one POST-ACCEPTANCE self-found defect.

**Two counts, two bases — stated because they differ and a reader who sums
the wrong one will think the other is a typo.** The series above is PER
ROUND: the number of distinct findings that round's report raised, which is
what the verbatim reports in `specs/reviews/0020-0021/` say. `specs/reviews.py`
sums PER SPEC, and the rounds were COUPLED, so a finding landing on both
specs is recorded in both rows and its per-spec total is necessarily larger
(round 1: 7 distinct findings, recorded 5 + 6). The table below lists one row
per finding PER OWNER, so it tracks the per-spec basis. No single number is
"the" count; the round reports are authoritative for what was raised, this
table for what closed it.)*

| round | finding | class | owner | disposition | evidence |
|---|---|---|---|---|---|
| int-1 | R1 derived-record scope membership UNDEFINED and defaulted to a leak — maintenance is itself a producer of absent-identity records | BLOCKING | both | **folded (v2):** when a record's own identity is absent, membership evaluates over the CONTRIBUTORS' resolved identities (the 0014 ledger join); C3's floor only for no-identified-contributor derivatives; no new field (Q1 survives) | v2 §4a-iii; `reference_scope.membership` |
| ext-1 | F1 the derivative-membership rule contradicted the implementation and failed across portability (`_derive_output_metadata` copies `inputs[0].provenance` without clearing identity; export/import strips the ledger) | G+C, executed | 0020 (+0021) | **folded (v3): the membership-evidence HIERARCHY** — ledger evidence complete → membership, else UNRESOLVED and fail-closed; the populations enumerated; the identity-clearing obligation lands in 0021 W8 | v3 §4a-iii; V13 `test_unresolved_derivative_fail_closed` |
| ext-1 | F2 the new public types and grammars had no mechanical definition (Identity, ScopePolicy, decision table, filter grammar) | A+F | 0020 | **folded (v3):** the 0019 reference discipline — `specs/evidence/0020/reference_scope.py` + pinned vectors, V10 binding the shipped surface | `vector_harness.py` (131/131); V10 `test_scope_reference_vectors` |
| ext-1 | F3 the read-surface inventory was incomplete (`answer()`, queryless recall→proactive, the STRUCTURED carriers) | C (the §3b observation-surface class) | 0020 | **folded (v3):** the §4f inventory + a GENERATED manifest; N-1 restated over the FULL `Recall` value; answer/proactive threading; operator surfaces ruled unscoped-by-decision | §4f; V3/V11/V12 — `specs/read_surfaces.py --check`, `specs/generated/0020-read-surfaces.md` |
| ext-1 | F4 0021's consolidation construction rested on a false reach assertion | G | 0021 | folded in 0021 (v3): the pool construction, thresholds, failure/recovery, and the mechanical `COMBINING_SITES` registry | 0021 §4a/§4b |
| ext-1 | F5 per-process policy conflicts with shared-store maintenance | C+D | 0021 | **folded (v3): policy is READ-SIDE ONLY** — maintenance partitions on IDENTITY alone, so no host policy can widen or narrow what the store merges; 0020 carries the two-hosts cell and the restated reversibility | §2 (policy row), §7 |
| ext-1 | F6 the coupling was prose-only and 0014 was undeclared | E+D | both | **folded (v3):** `Spec-Requires: 0006, 0014, 0021`, MUTUAL with 0021 → atomic acceptance (the 0016/0018 precedent), machine-checked by the existing gate | the `Spec-Requires` header; `specs/check_spec_reference.py` |
| ext-1 | F7 the sealed archive failed its own package verifier | E | archive | folded (v2→v3): COLLECTED-first sealing with the packaged-state gate RUN and RECORDED | the seal machinery; `verify_package.py` |
| ext-2 | R2-1 the reference VIOLATED accepted 0006 absence semantics (only `(None,None)` unidentified vs I13) plus widening paths and a false coverage claim | G+B+E, executed | 0020 | **folded (v4):** I13/I3 verbatim (groupable ⇔ `source_id` present; principals require it), strict-typed validation, recursively-frozen policies with a mutation oracle, `resolve()` uniform per I9 | §4a-ii; the mutation-oracle vectors; V6 `test_unknown_identity_is_not_a_principal` |
| ext-2 | R2-2 contradictory semantics for a principal supplied WITHOUT policy rules | D | 0020 | **RULED (v4):** feature-disabled REFUSES a principal-bearing call (never silently unscoped); CONFIGURED-EMPTY defined as a valid state | §4a-ii; `test_a_principal_without_a_policy_refuses` |
| ext-2 | R2-3 the record→membership resolver was unspecified at the central seam (and the recovery row was wrong for OUTPUTS_DURABLE) | A+C, executed | 0020 | **folded (v4):** `membership(...)` NORMATIVE and total over every 0010 state; the legacy predicate normative and vectored; the source_id-filter-vs-cleared-derivative cell named | §4a-ii; `test_membership_is_total_over_the_closed_operation_state_set` |
| ext-2 | R2-4 0020's zero-change claim contradicted 0021's policy-independent maintenance rule | D | both | **folded (v4):** the claim narrowed to READS over a FIXED store state, cross-referencing 0021's disclosed maintenance change | §8; V1 `test_no_principal_is_byte_identical` |
| ext-2 | R2-5 0021's per-pool failure and public-result construction incomplete | C | 0021 | folded in 0021 (v4) | 0021 §4b |
| ext-2 | R2-6 0021 lacked a mixed-version shared-store regime | C | 0021 | folded in 0021 (v4) | 0021 §5 |
| ext-2 | R2-7 the archive's sealed-state fix introduced new packaging defects | E | archive | folded (v4): cache artifacts, bytecode, UID/GID and the stale COLLECTED inventory all corrected in the seal | the seal machinery |
| ext-3 | R3-1 policy validation remained BYPASSABLE (direct construction; sets accepted as sequences; vector-coverage gaps) | B+E, executed | 0020 | **folded (v5):** `__post_init__` enforces the canonical frozen shapes (direct construction RAISES), `classify` revalidates at consumption, sets REFUSED, the shipped 512-char bounds mirrored, direct-construction-oracle vectors | §4a-ii; `test_a_mutated_policy_refuses_even_after_resealing` |
| ext-3 | R3-2 the resolver consumed a ledger shape 0014 does not provide (Identity pairs vs nullable one-way digests; a fictional `consolidate:` prefix) | G+A, store-probed | 0020 | **folded (v5): membership moved to DIGEST SPACE** — the reference mirrors the shipped digest construction byte-for-byte; real row shapes with store-derived denominators; `is_legacy_derivative` fixed to the REAL `op-<12hex>` form | §4a-ii; `test_digest_agrees_with_the_shipped_0006_primitive` |
| ext-3 | R3-3 legacy absorption defeated the mixed-version read-safety claim (a pre-0021 survivor carries identity A while its ledger says B) | G, executed | 0020 | **folded (v5): the ABSORPTION-SURVIVOR rule** — every absorption row is checked against the record's OWN digest; any cross-digest (or None-vs-digest) contributor → UNRESOLVED | §4a-iii; V14; the absorption-survivor cells of `test_unresolved_derivative_fail_closed` |
| ext-3 | R3-4 the per-pool result schema could not represent the shared pool, and contradicted identity-free byte identity | F+D | both | **folded (v5), 0020 half:** the reserved shared-pool key `pool:unidentified` (digests are 64 hex — collision impossible); the §8/V1 narrowing extended to `maintain()`'s additive-superset return | §4a-ii; `test_shared_pool_key_cannot_collide_with_digest_space` |
| ext-3 | R3-5 the promised audit/telemetry carrier sweep was not a mechanical contract | C | 0021 | folded in 0021 (v5→v6) | 0021 §4b/§7a |
| ext-4 | R4-1 policy sealing STILL bypassable — a canonical-LOOKING inconsistent digest map classified a foreign identity as OWN; `object.__setattr__` flips passed; caller-owned backing dicts stayed mutable | B+E, executed | 0020 | **folded (v6): the SEALED policy** — a seal over the ENTIRE canonical projection with a module-private nonce, no retained caller state, recomputation at every consumption; the three executed bypasses became refusal vectors BY NAME | §4a-ii; the bypass vectors |
| ext-4 | (self-found, same round) an absorption survivor crossing export/import loses its ledger rows and would resolve by its claimed identity | G | 0020 | **closed (v6):** the import-time RECONSTRUCTION rule; cross-identity → UNRESOLVED on the destination; the residual (priors pruned before export) stated | §4a-iii; `store_adapter_harness.py` |
| ext-4 | R4-2 0021's identity-free compatibility claim contradicted its result schema (the shipped robustness consumer rejects the pools dict) | D+C, executed | 0021 | folded in 0021 (v6) | 0021 §4b |
| ext-4 | R4-3 0021's audit carrier mechanically incomplete (cardinality; a free-text error field can echo memory text) | C+B | 0021 | folded in 0021 (v6) | 0021 §4b/W12 |
| ext-5 | R5-1 COLLECTED claimed the import reconstruction closed while the harness asserted nothing and called the same behaviour a residual | D (own carrier contradiction, owned) | 0020 | **folded (v7):** `reconstruct_absorption_rows` EXECUTABLE in the reference; the real-store harness ASSERTS UNRESOLVED for the imported cross-identity survivor; atomic row-writing named as an implementation obligation | `store_adapter_harness.py` (recorded result) |
| ext-5 | R5-2 the R4-1 seal was RE-SIGNABLE (`_seal` and its nonce are reachable module attributes; flip + re-sign → CROSS_VISIBLE) | B, executed | 0020 | **folded (v7): the VALIDATOR-OWNED REGISTRY is the authority** — refusal on ANY divergence from the registered snapshot, so re-signing achieves nothing; PLUS the threat claim narrowed honestly (accidental-misuse-proof and forgery-evident, not adversarial-caller-proof) | §4a-ii; the `resign_after_flip` vector; `test_registry_snapshot_leaves_are_primitive_strings` |
| ext-5 | R5-3 the identity-free byte-identity claim survived the narrowing in both §5 tables | D | 0021 | folded (v7): the claim corrected in both carriers | §5; 0021 §4b |
| ext-5 | R5-4 `verify_package.py` did not verify every declared manifest hash (a tampered result file passed) | E, executed | verifier | folded (v7): generic traversal + fresh-vs-recorded comparison, single adapter run | `verify_package.py`; `verify_package_selftest.py` |
| ext-6 | R6-1 import reconstruction failed SUPPORTED inputs (a `user_id` remap changes ids without rewriting notes; whitespace ids; untagged `absorbed_duplicate`) | G, executed | 0020 | **folded (v8):** remap-aware reconstruction parameterized by the importer's own old→new table; the ANCHORED grammar; FAIL-CLOSED linkage (missing/unresolvable → WHOLE-IMPORT REFUSAL) | §4a-iii; `test_0021_import_linkage.py` |
| ext-6 | R6-2 "writing real ledger rows" was NOT IMPLEMENTABLE under the governing contracts (missing fields; the 0014 total-payload rule; the primitive carries only edges and episodes) | A+C | both | **folded (v8):** a NAMED 0014 amendment with a distinct imported-evidence SITE and its own integrity semantics, plus the 0009 §4c primitive extension | §4a-iii; 0021 §7b; `ledger_plan_harness.py` |
| ext-6 | R6-3 policy carrier wording internally stale (an "immutable" registry storing mutable dicts; a docstring describing seal recomputation the registry no longer performs) | D | 0020 | **folded (v8):** the snapshot is RECURSIVELY immutable (primitive leaves) and the docstring rewritten — the seal is tamper-evidence, not authority | `test_a_leaf_mutation_does_not_touch_the_snapshot` |
| ext-7 | R7-1 TRANSITIVE absorption bypassed scope membership — A(scope-a)→B(scope-b)→C(scope-b) leaves C's direct row equal to C's own scope | C+A, executed on a real store chain | 0020 (+0021) | **folded (v9): the DUAL transitive contract** — write-time FLATTENING (0021 §4c) + read-time CLOSURE (`close_absorption_rows`; unwalkable/cyclic → None, and **None IS UNRESOLVED**); the 0014 §4f premise corrected | §4a-iii; V14/V15; the closure vectors; the transitive cell of `test_unresolved_derivative_fail_closed` |
| ext-7 | R7-2 the note REGEX rejected valid native exports and demanded incidental tags resolve against its own last-tag rule; the "full import matrix" claim was false | F+E, executed | 0020 | **folded (v9):** the regex RETIRED for id-set-anchored DECIDABLE resolution (last tag governs; exactly one candidate; zero/multiple REFUSE); reconstruction PRE-COMMIT; execution-mode labels so COLLECTED cannot overstate | §4a-iii; V16; `test_0021_import_linkage.py` |
| ext-7 | R7-3 the imported-ledger atomic contract was descriptive, not constructive | A | both | **folded (v9):** complete rows (site, digests, typed `contributor_ref`, per-row op key) persisted atomically with the records — the 0009 §4c primitive amendment | 0021 §7b; `ledger_plan_harness.py` |
| ext-7 | R7-4 "recursively immutable" and carrier-cleanup claims were still false | E | 0020 | **folded (v9):** primitive-leaf snapshots; the claims restated to what the code does | `test_registry_snapshot_leaves_are_primitive_strings` |
| ext-8 | R8-1 retention pruning erases the intermediate record AND its note — the only closure link — so the walk LOOKED complete while an ancestor's foreign digest was gone | C (found-in-fix of R7-1), executed | 0020 | **folded (v10): closure BY CONSTRUCTION** — the SURVIVOR'S OWN flattened row set carries its ancestry and lives exactly as long as the survivor; the read-side walk survives only as OPPORTUNISTIC verification; the retention contract governs any future prune. **Own catch, disclosed:** accepted 0014 A10 makes the ledger survivor-lifetime-keyed, so "absence = leaf" was unsound and was corrected BEFORE sealing | §4a-iii; V17; `close_absorption_rows`; the pruned-legacy cells |
| ext-8 | R8-2 `absorbed_by_id` had NO durable write-time source and THREE carriers contradicted | A+D×3, reviewer-printed | 0020 | **folded (v10):** the exporter derives the field from the LEDGER's `contributor_ref` (never the note); the FORMAT rider rides the ONE 0018 D2 window with the SCHEMA-v8 columns and 0021's Q4 enforcement | §4a-iii; §7b; `specs/evidence/0020/linkage_carriers.md`; `portability.py` |
| ext-8 | R8-3 the "exact" import contribution amendment could not construct or store its rows | A | both | **folded (v10→v11):** the row plan constructed against the REAL DDL, per-row injective keys, idempotent re-import | V18; `ledger_plan_harness.py` (14 checks) |
| ext-9 | R9-1 flattening made the `absorbed_by_id` reverse derivation NON-UNIQUE (two answers before a prune, zero after) | C+A, executed | 0020 | **folded (v11): `derive_absorbed_by` is the exact normative algorithm** — canonical = DIRECT or REPARENTED, plain flattened copies never; one → the survivor, ZERO → omit, >1 → `ExportLinkageError` and the whole export refuses. The retention contract gains insert-only REPARENTING | §4a-iii; V19; `test_0021_import_linkage.py`; `ledger_plan_harness.py` |
| ext-9 | R9-2 the per-row op-key encoding was not injective (`'a:b'+'c' == 'a'+'b:c'`) | F (a recurrence of R7-2's delimiter class, in our own key — disclosed) | 0020 | **folded (v11):** `row_op_key` — colon-free prefix plus ONE framed domain-separated digest over the id pair; injective outright; the colliding cases are vectors AND real-DDL inserts | V18; `test_framing_makes_the_pair_injective`; `ledger_plan_harness.py` |
| ext-9 | R9-3 import row identity and exact equality did not bind the full logical record | C | both | **folded (v11):** NULL-digest dedup by the one canonical plan id; history/evidence drift never skips as equal | V18; `ledger_plan_harness.py` |
| ext-9 | R9-4 the D2 rider still conflicted with the accepted frozen schema | D | both | **folded (v11→v12):** the complete FINAL-FORM 0019 SCHEMA rider (v8 carries the two columns) rather than a delta | §7b; 0021 §7b; `schema_v8_evidence.py` |
| ext-9 | R9-5 runtime-verifier defects were mislabeled as environment skips | E | verifier | folded (v11): qualification errors are FATAL, never skips | `verify_package.py` |
| ext-10 | R10-1 prune-time reparenting MUTATED a ledger row (accepted 0014: rows are inserted, never updated), and the payload classes were never legal against the native site's closed schema — demonstrated only by bypassing the store validator with raw SQL | A+D, owned | both | **folded (v12): the `scope-attribution` SITE** — every derived row lives at a new site with its OWN closed payload vocabulary; every accepted schema untouched; reparenting is an INSERTION; the exact-set partition becomes STRUCTURAL | §4a-iii SITE-MATRIX; `prune_absorbed_record`; `ledger_plan_harness.py` (INSERT + A10-DELETE only) |
| ext-10 | R10-2 the closure-incompleteness marker LAUNDERED into a clean `absorbed_by_id` | C, executed | 0020 | **folded (v12):** canonical is CLASS-TOTAL (`_is_canonical`) — markers and plain copies are never canonical; the missing-copy prune path executed end-to-end | V19; `test_0021_import_linkage.py` |
| ext-10 | R10-3 `validate_row_plan` was not total over the amended logical row | C | both | folded (v12) — presence-required validation over every field | `validate_row_plan`; `ledger_plan_harness.py` |
| ext-10 | R10-4 the 0019 rider was still a delta, not the requested final schema construction | D | both | folded (v12): both measured manifestations generated and parity proven | `schema_v8_evidence.py` |
| ext-10 | R10-5 invalid qualification results still became successful skips | E | verifier | folded (v12) | `verify_package.py` |
| ext-11 | R11-1 the new site split was CONTRADICTORY across normative carriers (the 0009-amendment text still described the pre-split design, plus four satellite carriers) | D (carrier-completeness) | both | **folded (v13): the AUTHORITATIVE SITE MATRIX** — `reference_scope.SITE_MATRIX` is the ONE source, `render_site_matrix()` emits the table, and the block is embedded VERBATIM between markers in every carrier; **the seal byte-compares the block across all of them**, so drift fails the seal | §4a-iii (SITE-MATRIX markers); the seal |
| ext-11 | R11-2 `validate_row_plan` still not total | C (found-in-fix) | both | folded (v13): totality over the amended row, deletion cells included | `ledger_plan_harness.py` |
| ext-11 | R11-3 the insert-only regression contained an always-passing assertion (`... or True`) | E, owned plainly | both | **folded (v13):** the regression BYTE-COMPARES the flattened copy's full stored tuple by op key, before vs after the prune | `ledger_plan_harness.py` |
| ext-11 | R11-4 "fresh-vs-recorded" verification compared only the final line | E | verifier | folded (v13): full-output normalized verification | `verify_package.py` |
| ext-11 | R11-5 package metadata did not mirror the candidate | E | archive | folded (v13): header-derived manifest dependencies | the seal machinery |
| ext-12 | R12-1 the round-11 matrix itself assigned WRITERS across atomic-primitive boundaries (native flattened copies and future prune rows routed through the import primitive) | D+C, executed | both | **folded (v14): THE WRITER-SPLIT MATRIX** — one row per ATOMIC WRITER × site, with `validate_row_plan` CONTEXT-REQUIRED over the closed (site, payload-class) cells and cross-context refusals executed | §4a-iii SITE-MATRIX; §7a; `validate_row_plan`; `ledger_plan_harness.py` |
| ext-12 | R12-2 one pre-R9 sentence survived — the naive reverse-link lookup in the durable-source bullet | D | 0020 | **folded (v14):** replaced with the canonical-class algorithm reference, and the retired formulation joined a FORBIDDEN-PHRASE list the shipped verifier scans | §4a-iii; `specs/lint_withdrawn.py`; `verify_package.py` |
| ext-12 | R12-3 the advertised matrix/dependency seal was not shipped or invoked | E | verifier | folded (v14): the gates ship IN the one-command verifier with mutation self-tests — externally reproduced (the reviewer mutated the matrix, fixed the hash, and verification exited 1) | `verify_package.py`; round-13 report |
| ext-13 | R13-1 the writer context was not bound to the row's operation key | C | both | **folded (v15):** the OPERATION-AWARE constructor — keys are DERIVED from the writer context, never selected; CLOSED with the reviewer's own independent oracle (they constructed and inserted all five valid cells: 5/5) | `construct_plan_row`; `ledger_plan_harness.py` (14 checks) |
| ext-14 | — ACCEPTED (0020 Accept · 0021 Accept · seam Accept · verifier PASS · archive PASS); no blocking findings | — | both | TWO NON-BLOCKING obligations, BOTH SHIPPED SAME-DAY: the five-valid-cell constructor-to-real-DDL oracle now runs in the ledger harness, and every operation-id validation switched `re.match` → `re.fullmatch` | `ledger_plan_harness.py`; `vector_harness.py` |
| post-acceptance | `prune_absorbed_record` NON-TERMINATING on a record that is its own canonical absorber — found by DIFFERENTIAL FUZZING of the production port against the accepted reference (89 of 800 random ledgers) | implementation defect vs this spec's OWN contract (corrupt linkage REFUSES) | 0020 | **fixed and DISCLOSED, in both implementations:** self-absorption refuses (`ExportLinkageError`) and the iteration is over a snapshot. Then DOMAIN-CLOSED under research's 0018 R1-4 challenge — guarding only n=1 was bounded-wrong (a 2-cycle terminated but manufactured a self-absorbing row), so both now walk the whole canonical-absorber chain and refuse ANY revisit | commits `cd5285b`, `2596f4f`; vectors 129/130/131; `test_a_self_absorbing_record_refuses_the_prune_instead_of_looping` |

**Implementation state, kept separate from disposition** (the 0002 lesson —
"closed" silently meaning both was itself a finding): slice A landed the
normative core (`veracium.scope`, V10 bound); slice B landed the READ
surfaces (V1–V9, V11–V13); the 0021 write/maintain half (V14/V15/V17/V18 and
W1–W18) is not yet implemented, and V16/V19 are carried by the portability
riders already on main.
