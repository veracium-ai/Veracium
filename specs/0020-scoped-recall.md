# Feature spec: scoped recall — the principal boundary (S1)

Spec-Status: draft
Spec-Requires: 0006

*From research's design proposal
(`veracium-research/proposals/scoped-recall-design-proposal.md` @ f9a5fb9b,
§7 addendum @ 9f6fb286, §8 addendum @ d808282b) — the two-round dev/research
cell inventory is folded here in full. Companion: spec 0021 (scope under
derivation and consolidation). S3 (authenticated principals) is deliberately
OUT of this spec — see §8.*

## 1. Problem and motivation

Veracium's identity half shipped in 0006: every record can carry a durable
`(origin, source_id)` — which connector, agent, or device produced it,
revocation-joinable. The missing half is the PRINCIPAL BOUNDARY: *which
recalling party sees which records, and whose testimony is assertable to
whom.* Hosts running memory per-agent or per-session have no isolation —
every principal recalls every record with full assertability (the demand
signal, COORDINATION 2026-08-15: no agent/session/run scoping while the
ecosystem treats it as table stakes).

Done as machinery this is a trust feature on our own axis; done as a tag it
is the inert-field trap A1 names. This spec ships the machinery and adds NO
field.

## 2. Field contracts touched

| field | read / written | documented contract | consumers | change here |
|---|---|---|---|---|
| `Provenance.origin`, `Provenance.source_id` | read only | 0006: opaque namespacing identity; **groups, never grants** (R3/I5); **not authenticated** (R7) | identity digest, revocation join | become the SCOPE KEY: policy rules key on the RESOLVED pair (0006 I9 — absent origin resolves to the local singleton before any comparison, the same read path the digest uses). **NO new per-record field** (Q1: policy-over-identity; a per-record ACL field is only justified by demonstrated per-record-sharing demand, must satisfy A1/C6 day one, and rides the 0018 breaking window — none of which v1 needs) |
| `recall(user_id, query, token_budget)` | signature widened | today: no principal notion | hosts, MCP | gains `principal: Optional[Identity] = None` and the §4e filter parameters. **`principal=None` is byte-identical to today — the migration invariant, test-named** |
| gate / `assertable` partition | read only today | disclosure-keyed routing | gate, proactive, render | assertability becomes a RELATION between record provenance and recalling principal — RESTRICT-ONLY (§4b). The gate change leaves a NAMED SEAM for 0011's subject dimension (§7b) |
| the compiled wiki | read by `recall` | the grounded working view, compiled store-wide | recall's grounded block | **EXCLUDED from principal-bearing recall in v1 (§4d)** — the second synthesis path |
| scope POLICY | NEW — host-supplied, per-process | none today | recall, gate | lives beside the relations registry in `MemoryConfig`: **the store carries no policy; the host does.** Consequence stated plainly: two hosts opening the same store with different configs see different visibility — correct for honest-host ISOLATION (the host owns its process), and a named cell, not a discovery |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| `principal` (host-supplied at recall) | None → unscoped call, byte-identical to today | non-Identity shape → refused (closed predicate) | an identity no record carries → sees only shared-visible records | **a host names another agent's identity as its principal** | C2 verbatim-class: `(origin, source_id)` is NAMESPACING, NOT AUTHENTICATED (0006 R7). S1's boundary is honest-host ISOLATION — context-bleed, confused deputy, cross-agent leakage — never a security boundary against a caller who forges identity. Authentication is S3, a separate spec. The threat model section of any host-facing doc states this in these words |
| records with ABSENT identity (the default MCP stream supplies none) | — | — | — | a writer omits identity to reach every scope | **unknown is the floor** (C3): absent-identity records are SHARED-VISIBLE, gate unchanged — scoping is not a promise we can keep for records the host never identified, and shared-visible grants nothing beyond today's behaviour. **absent == absent is never SAME-scope** (two unknown-identity records are not one principal; groups-never-grants) — a named test |
| scope policy rules (host config) | no rules → every principal sees shared-visible + own-scope | malformed rule → refuse at config time, never at recall time | — | a rule that tries to WIDEN (grant cross-scope assertability above today's gate) | **RESTRICT-ONLY (C1, the governing invariant):** scope machinery only ever refuses or demotes. The named refused cell: same-principal re-assertability — "A's own use_only inference is assertable back to A" — is a GRANT and is REFUSED; `test_same_scope_grants_nothing` fails if anyone builds it. Any grant wants a 0006 amendment conversation, not this spec |
| filter parameters (§4e) | absent → no filtering | unknown field/op → refused (closed grammar) | — | a filter referencing out-of-scope attributes as an oracle | M-2: filters apply AFTER scope, within the visible set — narrow only, never widen; leak-free by construction |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | expected result |
|---|---|---|
| no principal notion exists at recall today | `grep -n "principal" src/veracium/__init__.py src/veracium/gate.py` | no hits on the recall path |
| identity resolution is the shipped read path | `grep -n "resolve_origin" src/veracium/source_identity.py` | the 0006 I9 primitive |
| the wiki reaches recall's context today | `grep -n "wiki" src/veracium/__init__.py \| head` | the grounded-block assembly |
| nothing filters recall by metadata today | `grep -n "def recall" src/veracium/__init__.py` | `user_id, query, token_budget` only |

*(Re-run at implementation; commands recorded per the 0005 rule.)*

## 3. Trust-class matrix — REQUIRED, blocking

**No trust class moves.** Scope is orthogonal to author/derivation and can
only subtract visibility/assertability:

| operation | scope consequence |
|---|---|
| unscoped recall (`principal=None`) | byte-identical to today, every record, every store (the migration invariant) |
| scoped recall, own-scope record | visible; assertability exactly as today's gate gives |
| scoped recall, cross-scope record | visibility per policy; **assertability at most today's** — the concrete v1 rule: cross-scope testimony renders with the same non-assertable disclosure third-party testimony gets |
| scoped recall, absent-identity record | shared-visible, gate unchanged (C3) |
| any write path | UNTOUCHED — this spec changes no write, no lifecycle transition (0021 owns derivation/consolidation) |

**Write-time or maintain-time?** Neither — S1 is READ-time only. Lifecycle
stays scope-blind (a newer value supersedes per the 0003 ladder regardless
of scope; the store's truth is GLOBAL and scope filters VISIBILITY — the
alternative, per-scope divergent truths, is a different and worse product).
The full operation matrix (absorption, supersession, reinforcement,
consolidation, expiry) is 0021's §3.

## 3b. Authorization and scope

- **Who supplies the principal:** the HOST, per recall call — same trust
  domain as every other host input (a host writing to its own store already
  owns its bytes). No Veracium-mediated surface invents one; MCP passes the
  host's declared principal through or nothing.
- **What it reveals:** scoped responses reveal LESS. The two disclosure
  cells are pinned in §4c (N-1: no existence signal; N-2: lifecycle status
  without content).
- **The stated line (N-1 vs N-2/M-3, once, so it never reads as
  inconsistency):** *lifecycle truth about YOUR VISIBLE records renders
  (supersession status, contention linkage — content of invisible parties
  stripped); metadata about what scope WITHHELD does not exist on the
  principal surface (it is operator/telemetry material, 0017's consent
  framework as carrier); metadata about the VISIBLE set may render (M-3).*

## 4. Behaviour

### 4a. The principal model

A principal IS an `(origin, source_id)`-class identity — the shipped
namespace; one identity model, one revocation join. Policy rules are
host-supplied per-process (`MemoryConfig`, the relations-registry
precedent) and evaluated over RESOLVED identity (0006 I9), never raw
fields.

**Derived records (internal R1 — the producer sweep both design rounds
missed):** hosts are not the only producers of absent-identity records —
MAINTENANCE is: a consolidation output is store-authored (resolved origin
= the local singleton, `source_id` absent), so under identity-only policy
it would resolve shared-visible and leak scope-A content to B as an
ordinary synthesized record. The rule: **when a record's own identity is
absent, policy consults its LINEAGE — scope membership evaluates over the
CONTRIBUTORS' resolved identities** (the 0014 ledger join, load-bearing in
v1; the same lineage shape `min(author, derived_from)` already uses for a
derivative's trust). All contributors one scope → the derivative belongs
to that scope. C3's shared-visible floor applies ONLY to records with no
identified contributors (the closed pool's derivatives stay in the pool).
Still no new field; Q1 survives. The partition rule and its test (W7)
live in 0021.

### 4b. Scoped assertability — restrict-only

The gate's assertable predicate becomes a relation
`assertable_to(record, principal)`:

- own-scope: exactly today's `assertable`.
- cross-scope: at most today's; v1 pins it to the third-party-testimony
  disclosure shape (rendered non-assertable, attribution preserved).
- **no promotion path exists**: same-scope status never raises trust,
  never clears `ungrounded`/`needs_confirmation`, never lifts disclosure.
  `test_same_scope_grants_nothing` enumerates the tempting cells (the
  own-inference re-assertability cell by name) and fails on any grant.

### 4c. Response-surface disclosure — the two pinned cells

- **N-1, existence non-leakage:** a principal-facing response is
  INDISTINGUISHABLE between nothing-exists and everything-withheld —
  response bytes identical for an empty store vs an all-out-of-scope store
  on the same query (test-named). Withholding counts/rates are
  OPERATOR-side only (0017 consent carrier). Composition sentence, kept
  verbatim: *a scope-blinded agent saying "no record" is isolation
  WORKING, not abstention failing.*
- **N-2, superseded-by-invisible:** supersession STATUS is global truth
  and renders (supersede-never-erase; hiding it would show a stale value
  as current). The superseding record's CONTENT and ATTRIBUTION follow
  scope and do not render. Residual accepted with eyes open: the bare
  status reveals that out-of-scope testimony exists — the price of global
  truth, stated so a reviewer finds it rather than discovers it.
  **Precedent: accepted 0003 §4c-ii/Corr-A** — the unseen fenced
  challenger renders as content-free linkage; 0020 cites, not re-derives.
  The contested-facts surface gets the same row: a cross-scope contention
  renders as own member + content-free contention status, challenger
  content/attribution scoped out.

### 4d. The wiki — the second synthesis path (N-3)

The compiled wiki is a store-wide LLM re-rendering; scope machinery does
not control it, so scope enforced at the subgraph and ignored by the
compiler would leak cross-scope content wholesale (the GHSA-hcj3 shape
through `compile.py`; the general rule, recorded: **every LLM re-rendering
the scope machinery doesn't control is a laundering site**; the 0019 F4
precedent — a code-owned property cannot survive an uncontrolled
re-rendering). **V1: principal-bearing recall EXCLUDES the shared wiki**
(subgraph-only assembly); the wiki remains the no-principal surface's
view. Per-scope wiki compilation is a recorded option for the 0021 era,
cost-gated (compile spend × principal count). Named test: no wiki content
in any principal-bearing recall.

### 4e. Metadata filtering (the folded demand signal (b))

A convenience API on the same surface, under four rails (research §8):

- **M-1** filters SELECT, never STRIP — the narrowest result still renders
  full disclosure (markers, superseded status, `ungrounded`, attribution).
- **M-2** filters apply AFTER scope, within the visible set; narrow only.
- **M-3** empty-result reporting IS principal-facing here ("your filter
  matched 0 of the records visible to you") — safe because computed within
  the visible set; the §3b line governs.
- **M-4** source-field filters evaluate over resolved identity; the filter
  grammar is closed, documented, deterministic — no interpretation layer.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| store with no identities, no principals ever | byte-identical to today, forever |
| principals adopted, unscoped call | byte-identical to today (the shared view) |
| scoped call, mixed store | own-scope full; cross-scope per policy (visibility) + third-party-shaped (assertability); absent-identity shared-visible |
| scoped call, everything out of scope | indistinguishable from an empty store (N-1) |
| cross-scope supersession of a visible record | status renders; superseding content/attribution do not (N-2) |
| scoped call + filters | scope first, then narrow (M-2); M-3 reporting |
| MCP default stream (no identities supplied) | NO isolation exists — adoption-path honesty: scoping is opt-in by supplying identity; the docs and marketing rail say so plainly |

## 6. Invariants and executable checks — REQUIRED, blocking

**Status: STAGE-5 OBLIGATIONS — none exists yet (draft).**

| invariant | executable check |
|---|---|
| V1 unscoped calls byte-identical to today on every fixture store | `test_no_principal_is_byte_identical` |
| V2 restrict-only, by enumerated temptation (incl. own-inference re-assertability) | `test_same_scope_grants_nothing` |
| V3 empty-vs-withheld indistinguishability, response bytes | `test_existence_non_leakage` |
| V4 superseded-by-invisible: status yes, content/attribution no; contested row per 0003 | `test_cross_scope_supersession_rendering` |
| V5 no wiki content in principal-bearing recall | `test_scoped_recall_excludes_wiki` |
| V6 absent==absent never SAME-scope | `test_unknown_identity_is_not_a_principal` |
| V7 policy over resolved identity (I9 path; raw-field comparison fails the test) | `test_policy_evaluates_resolved_identity` |
| V8 filter rails M-1..M-4, each a named cell | `test_filter_rails` |
| V9 the 0011 gate seam: the relation signature carries the reserved subject slot untouched | `test_gate_seam_reserved_for_0011` |

## 7. Failure modes and reversibility

- **Misconfigured policy** fails at config load, never mid-recall.
- **Forged principal** (honest-host breach): out of threat model by C2 —
  stated, not hidden; S3 is the upgrade path.
- **Reversibility:** v1 adds no field, no schema/format change, no
  migration — dropping the policy from config restores today's behaviour
  byte-for-byte. This is why Q1's policy answer also de-risks shipping.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `MemoryConfig` | scope policy (host-supplied rules; closed validation) |
| `recall()` / MCP recall surface | `principal=` + filter params (§4e) |
| `gate.py` | the assertability relation + the 0011-reserved seam |
| `compile.py` | untouched (the v1 exclusion lives on the recall path) |
| docs (`concepts.md`, `api.md`) | the isolation-vs-boundary split (C2, verbatim-class); the adoption path (no identities → no isolation) |
| telemetry | withholding rates as operator-side material — a FUTURE consent-versioned field, deferred and recorded (the 0019 telemetry-deferral pattern) |
| CHANGELOG / marketing rail | never parity-chasing; claimable only as isolation until S3 |

### 7b. Cross-spec carriers

| spec | touchpoint | disposition |
|---|---|---|
| 0006 | identity, resolution, groups-never-grants, R7 non-authentication | inherited wholesale; any grant semantics = a 0006 amendment, refused here |
| 0003 | §4c-ii content-free linkage | cited as N-2's precedent; the contested row extends it |
| 0011 (draft) | the subject dimension | orthogonal in v1; the gate relation reserves its slot (V9) so 0011 composes without rewriting |
| 0021 | the operation matrix, consolidation partition, per-scope wiki option | companion — S1 read-time, 0021 write/maintain-time |
| 0017 | the operator-side withholding channel | future consent-versioned field; deferred, recorded |
| 0018 | the breaking window | NOT needed by v1 (no field); recorded so its absence is a decision |

## 8. Claims and limits

**Claim:** with a scope policy configured and identities supplied, a
recalling principal sees its own scope fully, sees cross-scope material
only as policy admits and never as assertable testimony, and cannot learn
what was withheld — at zero change to unscoped stores.

**Limits:** (1) isolation, not a boundary — C2 verbatim; S3 is the
boundary. (2) No identities → no isolation (the shipped MCP default);
adoption is opt-in. (3) Scope shards visibility, not truth — lifecycle is
global (N-2's residual). (4) The wiki is excluded, not scoped, in v1.
(5) Policy is per-process: two differently-configured hosts see
differently — the host owns its process.

## 9. Brief for the external reviewer

n/a — internal review first (research, the standing path); this section is
completed at external-round packaging per PROCESS.

## 10. Open questions

| # | question | state |
|---|---|---|
| Q1 | field vs policy | RESOLVED in design review: policy, no field (research §7 ratified) |
| Q2 | absent-identity default | RESOLVED: shared-visible, gate unchanged (C3) |
| Q3 | 0011 interaction in v1 | RESOLVED: none; seam reserved (V9) |
| Q4 | per-scope wiki compilation | DEFERRED to the 0021 era, cost-gated, recorded §4d |
