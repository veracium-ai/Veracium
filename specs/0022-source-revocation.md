# Feature spec: source revocation — the standing state and the sweep (A3a)

Spec-Status: draft
Spec-Requires: 0004, 0006, 0014, 0020, 0021, 0023

*From research's design proposal
(`veracium-research/proposals/a3-source-revocation-design-proposal.md`,
2026-08-17, greenlit, with dev's corrections folded), decomposed by dev into
this spec (A3a — the operation) and **0023** (A3b — non-revival under
maintenance). See `## Review closure`.*

> **v2 — internal round 1 folded (research, 2026-08-17; full review at
> `veracium-research/proposals/0022-0023-internal-review.md`).** One
> BLOCKING finding, and it was a design completion rather than a prose
> fix. **S1: the sweep's record DOMAIN was unenumerated** — "records"
> meant edges, and **episodes have no retirement mechanism in the
> shipped store while their text renders straight into recall context**.
> The normative reference had it right all along (it validates
> `type in ("edge", "episode")` with `active`/`retired_reason` on both,
> and the vectors exercise episodes) — so this was a class-G
> shipped-shape mismatch, not a missing idea: **an evidence package can
> pass 54/54 against a reference the product cannot implement.** §4b-i
> now enumerates every stored type with its mechanism or its EXECUTED
> exclusion, §4b-ii specifies the episode mechanism (Quentin's decision,
> 2026-08-17: a JSON field plus the `store.episodes()` read seam, no
> DDL), **R18** pins it, and §2c-ii carries the five commands that were
> run. Also folded: **M1** (Q6's rationale was false across time — a
> pure function over MUTATING inputs reproduces the present, not the
> past), **M4** (`complete=False` is the expected steady state on any
> consolidation-bearing store, said up front), and research's suggestion
> that retired-synthesized be counted separately from
> retired-sole-basis, since only one of the two is re-derivable.
> RATIFIED unchanged: the synthesized-survivor retirement, R3/R4/R6,
> §4f's desired-state reversal, the ratchet, and R17.*

***The coupling with 0023 is MACHINE-CHECKED and acceptance is ATOMIC:
`Spec-Requires` is MUTUAL — 0022 requires 0023 and 0023 requires 0022 — so
the existing gate refuses either alone, the 0016/0018 and 0020/0021
precedent. The reason is not tidiness. This spec's sweep is a boundary
around content already in the store; without 0023 that boundary has an
UNLOCKED BACK DOOR, because revoked content re-enters through ingest,
reinforcement, absorption, consolidation and import the moment the sweep
finishes. And 0023 alone governs only the future, leaving everything the
revoked source already wrote standing. Neither half is a feature.***

**`0004` is on this spec's critical path** and is being refreshed in
parallel (v3.1, 2026-08-17). Revocation that does not reach the compiled
wiki does not reach what the model reads, which is the only surface that
matters. This spec does NOT restate that mechanism — it declares the
dependency and carries a drafted rider in §7b.

## 1. Problem and motivation

A host discovers that a source it trusted is not trustworthy: a connector
was compromised, a device was lost, a vendor feed turns out to be
generated slop, a mailbox belonged to someone who has left. Today
Veracium can *name* that source — 0006 ships `(origin, source_id)` on
every record and 0014 keys every contribution row on its digest — and can
do **nothing** with it. There is no `revoke_source`. The operator's only
tools are `forget()`, which erases the whole user, and `dispute()`, which
takes one edge at a time and requires knowing which edges to name. The
honest description of the status quo is that Veracium sells durable
provenance and offers no way to act on it.

**What happens if we do nothing:** the identity fields stay
diagnostic-only — the inert-field trap A1 names — and every deployment
that adopts source identity discovers that the feature it adopted it for
does not exist. Meanwhile the substrate keeps accruing: the 2026-08-07
analysis found revocation *unspecifiable* because maintenance destroyed
contributor attribution in two of three paths; every one of those
blockers has since shipped (0012 persists the reinforcing edge, 0014
keys contributions on the digested identity, 0021 gives absorption typed
links and transitively closed consumption). The cost of not building it
is no longer a missing feature but an unpaid dividend.

**Constraints inherited from accepted specs** (binding; the labels are
research's and are used throughout):

| # | constraint | source | consequence here |
|---|---|---|---|
| C1 | restrict-only | 0006 (identity groups, never grants) / 0020 | revocation only ever retires, quarantines or reduces. It can never promote a rival record, never clear a flag, never raise a confidence. Un-revoke RESTORES; it never grants |
| C2 | identity is namespacing, NOT authentication | 0006 (the non-authenticated-origin rule, and its own deferred authenticated-origin question) | the revocation key is unauthenticated, so the forged-source cell is real (§3b) and reversibility is a THREAT-MODEL REQUIREMENT, not a courtesy |
| C3 | supersede-never-erase | house rule | revoked records RETIRE with reason `revoked_source`; nothing is deleted; `forget()` remains the separate data-subject erasure op |
| C4 | transitively closed consumption | 0021 (the closed-consumption rule) | the blast radius is the CLOSED set over typed links; a single-level sweep is a defect by accepted rule |
| C5 | fail-closed on missing evidence | 0020 (the fail-closed membership hierarchy) | where attribution is absent, revocation REPORTS incompleteness. Every revocation returns a completeness statement. *A tool that quietly misses half the blast radius is worse than none* is hereby a design requirement, not a warning |
| C6 | ordinary-release bias | 0018 | one small append-only table plus read-side consultation is a SCHEMA bump on the ordinary migration path; no API-breaking window is needed or requested |

**Alternatives rejected.**

- **A `revoked` boolean column on the source, updated in place.** Rejected:
  it is a second, contradictory answer to a seam the ledger already
  settled (0014's rows are inserted and never updated). An UPDATE-shaped
  revocation cannot say *when* a source was revoked, cannot say *who
  lifted it*, and makes the audit trail a diff. §4a takes the append-only
  form.
- **Deleting revoked content.** Rejected by C3, and independently by the
  threat model: C2 means the operator can be tricked into revoking a
  victim, and a delete is not reversible. Retirement is.
- **A `prior_values` column recording what each survivor's transferred
  state was before the contribution.** Rejected because the machinery
  shipped underneath it while the 2026-08-07 design was waiting: 0012
  persists every contributing edge and 0014's absorption payload already
  carries both the survivor's pre-absorption `base` and the contributor's
  own `contributor` side. The surviving evidence set is on disk, so the
  transferred state is RECOMPUTED, not restored (§4d) — and the same fold
  restores it on a lift, so no column is needed in either direction.
- **A blunt per-user "quarantine everything older than attribution"
  escape hatch** for pre-0014 history (research's Q4). Rejected for v1:
  it converts a precise instrument into a shotgun. An operator reaching
  for revocation wants the records this source touched; a switch that
  quarantines every record older than a date will be reached for under
  pressure, and it retires user-authored content the revoked source never
  touched. The honest alternative is the one C5 already requires — REPORT
  the unreachable population and let the operator decide. Recorded in
  §10.
- **Store-wide revocation across all users.** Rejected for v1 (§3b): every
  join, index and operator surface in the store is user-keyed. A host
  that wants store-wide revocation loops over its users and aggregates,
  which is honest about what was actually swept.

## 2. Field contracts touched

| field | read / written | its documented contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `Provenance.origin` / `Provenance.source_id` | READ ONLY | 0006: opaque namespacing identity; **groups, never grants**; resolved at read (absent origin → the local store singleton) before any comparison | the identity digest, 0014's ledger, 0020's scope key, export | becomes the REVOCATION KEY, over the RESOLVED pair, via the one shared digest primitive. **0006's affirmative rule that identity affects NO trust/authority/disclosure/staleness/supersession decision "in v1" is AMENDED by this spec** — identity now feeds exactly ONE decision, which is RESTRICT-ONLY. Groups-never-grants is untouched; the amendment is drafted as a rider in §7b, and its CI test is named there because it would otherwise fail the day this ships |
| the invalidation reason vocabulary (`invalidate_edge(..., reason)`) | written | 0004: a closed, registered set; the runtime consults `WIKI_RETAINING_REASONS` and everything else DROPS the wiki | 0004's registry, introspect, export | gains `revoked_source`. Under 0004 v3.1's drop-by-default polarity this needs no behaviour change there at all; the rider (§7b) registers it in `DISPOSITIONED_REASONS` so the totality check passes |
| `Provenance.confidence`, `Provenance.observed_at`, `Edge.valid_from` on CORROBORATED survivors | written (reduced) | the absorption inheritance: the survivor carries `min(valid_from)`, `max(observed_at)`, `max(confidence)` over itself and its absorbed priors | recall scoring, staleness, render | RECOMPUTED over the SURVIVING evidence by the SAME transform (§4d). Monotone under contributor removal, and CLAMPED against the full-evidence fold, so the result can never exceed what the store committed at write |
| `Edge.ungrounded` | **NOT written** | 0019: the N-ary OR over the merged set; once flagged, the surviving representation stays flagged | gate, render, telemetry | **deliberately excluded from the recompute.** Re-deriving an OR over a SMALLER set can flip True→False, which is a promotion wearing a recompute's clothes. The ratchet holds (§4d) |
| `Provenance.disclosure` | **NOT written** by this spec | written exactly once, at ingest | gate, render | untouched here. Disclosure at WRITE time under a standing revocation is 0023's, at the one site that writes it |
| `contribution_ledger` rows | READ ONLY | 0014: insert-only; rows key the survivor by `(survivor_type, survivor_id)` and the contributor source by `identity_digest`; the digest join is the revocation join, named A9 in that spec and already implemented as `contributors_of_source` | 0020's membership, 0021's closure | the sweep is a READER. It writes no row, drops no row, and rewrites no payload. The ledger's insert-only discipline is inherited, not re-litigated |
| the compiled wiki | dropped | 0004: a derived view must not outlive the trust decision it was compiled under | recall's grounded block | dropped by the retirement itself, through the reason vocabulary — this spec adds no second mechanism (§7b) |
| `source_revocations` | **NEW TABLE**, append-only | none today | the sweep; 0023's write- and maintain-time gates | one row per revoke and per lift; the STANDING state is DERIVED by reading the latest row per (user, digest). No UPDATE, no `active` column (§4a) |
| `Recall` / the gate | unchanged | assertability keys on `active` and disclosure | recall, answer, proactive | revoked records leave the assertable set through the EXISTING retirement machinery. No gate change, no new field on any read surface |

Consumers were enumerated mechanically, not recalled — the commands and
their real output are §2c-ii.

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant that pins it |
|---|---|---|---|---|---|
| the revocation TARGET `(origin, source_id)` (host-supplied) | absent `source_id` → **REFUSED**: there is no digest, so there is no join and no honest sweep. 0006's own acceptance test already asserts a revocation matches neither of two source_id-less records | non-str, over-length (>512), or an origin absent alongside a present source_id → refused at the boundary, never digested half-resolved | an identity no record carries → an EMPTY blast radius is returned, with the class-(c) count still reported. A revocation of nothing is a valid, recorded, reversible act | **the forged-source DoS**: an attacker writes garbage under a victim's pair to bait an operator into revoking the victim | C2 verbatim: identity is NAMESPACING, NOT AUTHENTICATION. The mitigations and their limits are §3b; **R12** (no digest, no reach) and **R6** (dry-run before commit) |
| the `source_revocations` rows the store reads back — **PRODUCERS row: the host's `revoke_source` call AND THE STORE'S OWN MACHINERY (migration, recovery, and any future importer of an operator log)** | no rows → nothing is revoked; every read path behaves exactly as today | a NULL digest, an unknown action, a missing reason, a non-int ordinal, an unknown column → **REFUSED at read**, never coerced. A NULL-digest row would be a `(resolved_origin, NULL)` pseudo-source, which 0006 forbids, and would revoke every unknown-source record in one row | an action string this version does not know → refused; a future action cannot be silently treated as "revoke" or as "lift" | a row planted with a far-future timestamp to win the latest-row rule | **R1**: the standing state is DERIVED from validated rows; two rows sharing one append ordinal make the rule undecidable and REFUSE rather than resolving by insertion order |
| the 0014 contribution rows the join returns — **PRODUCERS: absorption (`apply_supersession_plan`), consolidation, the import primitive, and 0021's flattening** | a survivor with no rows → it is not reachable through contribution at all, and if it is system-authored it is COUNTED in class (c) | a half-typed link (`contributor_ref` without `contributor_type`) → refused; legacy rows carry BOTH columns NULL, so a half link is corruption, not history | a site this version does not know → the row still counts as evidence for the sole-basis test and its class is read from the typed link, which is total over any site vocabulary | a row NAMING ITS OWN SURVIVOR, which would make a walker loop — the 0020 post-acceptance defect, found by differential fuzzing | **R8**: the closure REFUSES corrupt linkage rather than continuing past it, and the fixpoint terminates because the condemned set only grows |
| a record's own identity fields, at sweep time | absent `source_id` → unreachable by any revocation, by construction | out-of-bounds → refused by the shipped model validation before this spec sees it | an origin naming a foreign store → resolved as-is (a foreign record keeps its own origin), so it is revocable only under that pair | a writer OMITS `source_id` so its content cannot be revoked | acknowledged and stated in §8: absence buys unreachability, and it costs the writer every grouping benefit. **R12** names the cell rather than pretending the rule is closed |
| the operator's `reason` string | empty/whitespace → REFUSED. A revocation with no recorded reason is not auditable | non-str → refused | — | a reason echoing memory text into the audit sink | the reason is OPERATOR-SUPPLIED and lands in the revocation row, which is operator-facing state, never model context. **R14** keeps the whole surface off the agent-reachable paths |

## 2c-ii. Assertions about reach — REQUIRED

**Every command below was RUN, in this repository, on 2026-08-17, and the
result column records its real output** — not a statement that it was
checked. Re-run at implementation, per the standing rule.

| assertion | command that establishes it | result (RUN 2026-08-17) |
|---|---|---|
| **the source join is already indexed in the ACCEPTED schema — this spec adds NO index** | `grep -n "ix_contribution_ledger_source" -A 2 src/veracium/store/schema_version.py` | `schema_version.py:264-266` — `CREATE INDEX ix_contribution_ledger_source ON contribution_ledger(user_id, identity_digest)`, REBUILDABLE, inside `SCHEMA_V6` and carried forward to v8 |
| **contribution rows key the SURVIVOR by type + id** (so a linkless row still identifies what to act on) | `grep -n "_CONTRIB_COLS = " -A 3 src/veracium/store/sqlite.py` | `sqlite.py:878-880` — `id,user_id,survivor_type,survivor_id,site,identity_digest,evidence_ref_digest,payload,op_key,created_at,contributor_type,contributor_ref` |
| **the blast-radius join is ALREADY IMPLEMENTED and named for this operation** | `grep -n "def contributors_of_source" -A 10 src/veracium/store/sqlite.py` | `sqlite.py:907-918` — *"every survivor a source contributed to — revoke_source's blast-radius join (A9). COMPLETE identities only: a NULL digest never joins, enforced by the NOT-NULL bind here."* The method exists, returns `[]` for a NULL digest, and has an acceptance test (`tests/test_0014_ledger.py:312`) |
| **consolidation writes NULL typed links TODAY — class (b) is not a legacy-only class** | `grep -n "contributor columns stay NULL" -A 12 src/veracium/store/sqlite.py` | `sqlite.py:854-866` — the comment states the decision (*"the 0021 §7b typed link is scoped to the draft-carried plan/absorption sites, and the R3-3 verify above compares the deterministic fields of PRE-v8 rows"*) and the INSERT binds `None, None` into `contributor_type, contributor_ref`. Populating them would break 0014's field-for-field replay verify across the v7→v8 migration, so this is a documented decision and not an omission. **Dev additionally verified this empirically against a live v8 store on 2026-08-17** |
| **no revocation surface exists today** (this spec is additive, not a change of behaviour) | `grep -rn "def revoke_source\|source_revocations" src/veracium/` | EMPTY (exit 1). The only hits anywhere are three FORWARD REFERENCES naming this operation: `source_identity.py:5`, `store/base.py:199`, `store/sqlite.py:908` |
| **revocation is not reachable from the agent surfaces** — it is a host-API-only, `confirm()`-shaped authority | `grep -n "add_parser" src/veracium/cli.py` · `grep -n "@server.tool" src/veracium/mcp_server.py` | CLI verbs are telemetry · selfcheck · diagnostics · export · import · migrate · forget · recall · remember · introspect — **no revoke verb**. `mcp_server.py` registers four tools at `:133/:150/:163/:170` — **none of them writes trust state**. Keeping it that way is **R14** |
| **the digest is the ONE shared primitive both sides must call** | `grep -n "def source_identity_digest" -A 4 src/veracium/source_identity.py` | `source_identity.py:48` — and its module docstring names this operation as the second consumer: *"a silent join miss in revocation is under-revocation"* |
| **the absorption payload already carries BOTH sides, so recompute needs no new column** | `grep -n 'payload = {"base": dict(plan.absorption_pre_image), "contributor": side}' -B 8 src/veracium/store/sqlite.py` | `sqlite.py:666`, with `side` built at `:658-665` from the contributor's authoritative row (`observed_at`, `confidence`, `valid_from`, `disclosure`) and `base` the survivor's pre-inheritance snapshot |
| **the recompute transform is the SHIPPED one, not an invention of this spec** | `grep -n "min(valid_from), max(observed_at), max(confidence)" -B 3 src/veracium/contribution.py` | `contribution.py:225-227` — the replay verifier's own words: *"from the snapshot's own values plus the recorded contributor sides, the committed survivor's values must be reproduced — min(valid_from), max(observed_at), max(confidence)"* |
| **there is exactly ONE writer of `active=0`, which is what the sweep must route through** | `grep -rn "active=0\|active = 0" --include=*.py src/veracium/` | ONE hit: `sqlite.py:251`, inside `_invalidate_edge_row` (`:242`, *"Shared by `invalidate_edge` and `apply_supersession_plan`"*). 0004 v3.1's W7 keeps it that way with an AST sweep that fails the build on a second writer |
| **EPISODE TEXT REACHES THE MODEL — the assertion that made S1 blocking, and the one v1 never ran** | `sed -n '869,872p' src/veracium/__init__.py` | `ep_lines = [clamp_item(f"[{e.date}] {e.summary}", cap) for e in episodes if not e.provenance.third_party_influenced]` — plus `tp_ep_lines` for the rest. **Episode summaries render into recall context; `third_party_influenced` only chooses WHICH SECTION.** There is no `active`, no `quarantined` and no disclosure consulted on this path |
| **episodes have NO retirement column — the mechanism genuinely did not exist** | `sed -n '134,138p' src/veracium/store/schema_version.py` | `CREATE TABLE episodes (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, date TEXT, json TEXT NOT NULL)`. Compare `edges`, which carries BOTH `active` and `quarantined`. The asymmetry is the finding |
| **`store.episodes()` is the ONE Python read path, and it ALREADY filters structurally** — so the seam this spec needs exists and is proven to carry a filter | `grep -rn "\.episodes(" src/veracium/ --include=*.py` · `sed -n '979,991p' src/veracium/store/sqlite.py` | NINE call sites, all through `store.episodes()`; the implementation already excludes provisional/hidden rows by observed `0010` op state, under the lock. A default-exclude parameter is the shipped `edges(active_only=True)` shape applied to a seam that already does this work |
| **the raw-SQL episode sites are FOURTEEN and are internal to the store** (so the disposition is bounded and enumerable, not open-ended) | `grep -rn "FROM episodes\|INTO episodes\|UPDATE episodes\|DELETE FROM episodes" src/veracium/ --include=*.py` | 14 hits, ALL in `store/sqlite.py` plus 2 in `store/migration.py`. None outside the store package — which is what makes R18's AST pin a closed check rather than a hope |
| **the vectors ALREADY cover episodes — the gap was the product's shape, not the evidence's coverage** | `python3 -c "…count vectors carrying a record with type=='episode'…"` · `.venv/bin/python specs/evidence/0022/vector_harness.py` | **18 of 54** vectors carry episode-typed records (e.g. `sweep_a_second_revoke_of_a_standing_source_is_idempotent` retires one with `retired_reason="revoked_source"`), and the harness passes **54/54**. The reference always modelled both types; the store implements one |
| **refusal records are content-free BY CONSTRUCTION, so the §4b-i exclusion is the DDL, not a claim** | `sed -n '199,204p' src/veracium/store/schema_version.py` | `supersession_refusals(refusal_id, user_id, prior_edge_id, incoming_edge_id, relation, prior_effective, incoming_effective, rule_version, created_at)` — ids, a relation name, two booleans, a version and a timestamp. No content column |
| **the normative reference and its vectors execute clean** | `.venv/bin/python specs/evidence/0022/vector_harness.py` | EXIT 0, every vector passing. **The pass/total line is recorded verbatim in `specs/evidence/0022/vector_harness_result.txt`, which is the ONE carrier for that count** — the 0020 rule, adopted here from the start: a number written into prose drifts from the artifact that measures it |

*(A cell here is a command and its output. Three of these assertions moved
the design while it was being written: the indexed join meant no new index,
the `{base, contributor}` payload killed the `prior_values` column, and the
shipped replay transform supplied the recompute rule rather than the spec
inventing one.)*

*(**A fourth assertion moved the design after the first internal round, and
it is the one this table did not originally contain.** v1 ran the
sole-`active=0`-writer command and concluded the retirement mechanism was
settled — but never asked what that writer's table WAS. It is `edges`.
Running the episode-render command shows episode summaries reaching the
model on a path with no `active`, no `quarantined` and no disclosure check,
so a whole record type was outside a sweep whose §8 claim sounded total.
The lesson generalises past this spec: **an executed assertion about a
mechanism is not an assertion about its DOMAIN** — `_invalidate_edge_row`
being sole and correct says nothing about the records it cannot reach.)*

## 3. Trust-class matrix — REQUIRED, blocking

Revocation is a **unary operation over stored records**, so this is a
state-transition table (the template's instruction for unary ops). The
classes are read from the shipped enums (`EvidenceAuthor`, `Disclosure`),
not copied from a template: revocation is **orthogonal to authorship** and
applies identically to every class, which is exactly what makes the
user-authored row below the honest one.

| record state before | the revoked source's relation to it | after | direction |
|---|---|---|---|
| active, any author, own identity = the revoked pair | direct | RETIRED, reason `revoked_source` | restrict |
| active, sole-basis contribution from the revoked source | contributor | RETIRED, reason `revoked_source` | restrict |
| active, corroborated by a DIFFERENT resolved identity, own content (a restatement) | contributor | STANDS; transferred maxima RECOMPUTED over surviving evidence (§4d) | restrict (never below the surviving evidence, never above the committed value) |
| active, corroborated, content SYNTHESIZED from the contributor set (a consolidation output) | contributor | RETIRED — corroboration does not make synthesized text safe when revoked material may be IN it. Re-derivation from the surviving inputs is a maintenance operation the operator may run; it is never something a revocation does silently | restrict |
| active, consumer of a record this sweep condemns (typed link) | transitive | the property RECURSES: the condemned contributor stops counting as evidence, so the consumer is re-classified — retired if that leaves it sole-based, recomputed if not | restrict |
| active, contribution rows exist but are LINKLESS | contributor | classified and treated exactly as above; what is LOST is its own descendants, which are REPORTED unreachable, never guessed | restrict + report |
| active, no attribution rows at all (pre-0014) | unknown | UNTOUCHED and COUNTED in class (c). Never guessed at, never swept by shape | report only |
| already retired for another reason (superseded, lapsed, decayed, absorbed) | any | UNTOUCHED. A lift never reinstates a record this operation did not retire | none |
| quarantined / `use_only` | any | the same transitions; disclosure is not read and not written here | none |

Then, explicitly:

- **Can this cause a user-asserted fact to become non-assertable?**
  **YES, and deliberately.** A user-authored record whose source is
  revoked retires like any other; that is the whole instrument. The
  danger is not the intended use but the FORGED-SOURCE case (§3b): an
  attacker who writes under the victim's `(origin, source_id)` can bait an
  operator into revoking the victim's own connector. The mitigations are
  reversibility (**R10**), restrict-only (**R4**), and the blast radius
  shown BEFORE commit (**R6**) — and their limit is stated in §8 rather
  than dressed up.
- **Can it cause non-user content to gain user-grade authority,
  confidence, or currency?** **No.** The only value this spec writes is
  the recompute, which is monotone under contributor removal and clamped
  against the full-evidence fold (**R4**). No promotion path exists;
  `test_revocation_grants_nothing` enumerates the tempting cells.
- **Can it clear `needs_confirmation`?** **No.** 0008 makes `confirm()`
  the only path, and this spec does not touch the flag. Nor does it clear
  `ungrounded` — see the ratchet, **R5**.
- **Does it merge, drop, or overwrite provenance?** **No.** No ledger row
  is written, dropped or rewritten; no record is deleted; retirement and
  reinstatement are both new events (**R9**).

**Write-time or maintain-time?** **Neither — this is OPERATOR-time**, a
third category the store already has: `forget()` and `confirm()` are its
other members. The distinction matters because the maintain-time
prohibition (bookkeeping over existing statements may not manufacture
freshness from recognition) constrains changes in the GRANTING direction;
every change here is in the opposite direction and is triggered by
EVIDENCE BEING REMOVED, not by recognition. The write-time and
maintain-time consultations of the standing state are 0023's, and are
deliberately not in this document.

## 3b. Authorization and scope

- **Who may call it.** The HOST, through the library API only — the
  `confirm()`-shaped authority. Not a CLI verb, not an MCP tool, not
  reachable by any agent or by model output (**R14**, asserted
  mechanically at §2c-ii). A revocation is a trust decision about a
  source; a surface the model can reach is a surface the model can be
  talked into.
- **Whose records.** **PER USER.** `revoke_source(user_id, origin,
  source_id, reason)`. Every join, index and operator surface in the store
  is user-keyed — the ledger's own index is `(user_id, identity_digest)` —
  and a store-wide sweep would cross the boundary every other operator
  surface respects. A host wanting store-wide revocation loops and
  aggregates, and its claim is then honestly its own (**R13**).
- **What becomes visible to whom.** Nothing new. The completeness
  statement is OPERATOR-facing and names record ids for the caller's own
  user, which the operator can already enumerate through `introspect` and
  `export_memory`. No principal, no MCP surface and no rendered context
  gains a field. Under 0020, scoped principals see strictly less after a
  revocation than before, never more.
- **Scope change.** Records that leave the assertable set leave it for
  every principal; nothing is revealed by their absence beyond what
  retirement already reveals (0020's existence-non-leakage rule governs
  the read side unchanged).
- **THE FORGED-SOURCE DoS, stated plainly.** C2 means `(origin,
  source_id)` is namespacing, not authentication. An attacker who can
  write to the host's ingest path under a victim source's pair can plant
  garbage that an operator, seeing it, revokes — taking the victim's
  genuine records with it. **This is a real cell and we do not close it.**
  What we do:
  - revocation is REVERSIBLE, and reversal restores by supersession
    (**R10**) — the operator is never one mistake away from an
    unrecoverable state;
  - it is RESTRICT-ONLY, so a forged source can never PROMOTE anything —
    the attack costs availability, never integrity;
  - the blast radius is shown BEFORE the commit, in the same computation
    the commit will run (**R6**), so "revoke and see" is not the only
    workflow;
  - `origin` is store-minted and cannot be set by a local caller, so the
    forgery requires the host's own ingest path with a chosen
    `source_id`, not merely a crafted document.
  An authenticated-source upgrade — signed exports, or import-time
  re-namespacing under a locally controlled id — belongs to S3's world
  and to 0006's own deferred question. It is not this spec's, and this
  spec does not claim it.

## 4. Behaviour

### 4a. Revocation is a STANDING STATE, derived from an APPEND-ONLY table

`source_revocations` gains one row per operator action:

```
source_revocations(user_id, identity_digest, action, at, seq, reason)
    action ∈ {revoke, lift}          seq: the per-user append ordinal, UNIQUE
```

**The standing state is DERIVED — the latest row per `(user_id,
identity_digest)` by `(at, seq)` — and is never stored.** There is no
`active` column and no UPDATE statement anywhere near this table.

**This is the explicit resolution of a seam, not an implementation
detail.** The store has two idioms for "current state": mutable rows
(`edges.active`, set by exactly one writer) and insert-only ledgers
(0014's contribution rows, which accepted policy says are inserted and
never updated or replaced). A revocation is a *decision with a history* —
who revoked, when, why, and whether it was lifted and re-applied — which
is the ledger's shape, not the flag's. Choosing the mutable form would
have put a second, contradictory answer to the same seam in the same
store, and would have made the audit trail a diff. **R1** pins it in both
directions: the derivation is tested, AND the absence of any
update/delete writer against the table is asserted mechanically, the
`test_sole_active_zero_writer` pattern 0004 v3.1 uses for its own
structural claim.

Consequences that fall out of the append-only form, all vectored:

- **revoke → lift → revoke** is an ordinary sequence; the state follows
  the last row.
- **a second revoke of a standing source is IDEMPOTENT** in effect: the
  row is appended (the reason may differ and the audit trail is the
  point) and the sweep plans nothing new (**R16**).
- **rows for another user do not revoke this user's source.**
- **two rows at one ordinal REFUSE** rather than resolving by insertion
  order — an append-only table whose latest row is ambiguous is not
  append-only.

### 4b. The sweep — one computation, stated as a function

`revoke_source` fires the sweep synchronously and returns a
**completeness statement**. The sweep is a pure function of *(the user's
records, the user's contribution rows, the standing revocation set)*:

1. **Directly-sourced records** — the record's OWN resolved identity is
   revoked → RETIRE with reason `revoked_source` (C3). **"Records" is a
   DOMAIN, and it is enumerated below rather than left to the reader.**
2. **Contributions** — the digest join (the accepted `contributors_of_source`
   read) returns every survivor the source contributed to. Per survivor,
   classify (§4c) and treat:
   - **synthesized** (a consolidation output) → RETIRE, corroborated or
     not;
   - **sole-basis restatement** → RETIRE;
   - **corroborated restatement** → STANDS, transferred state RECOMPUTED
     (§4d).
3. **The closure** — consumption is transitively closed (C4), and the
   closure is the **RECURSION OF THE PROPERTY** rather than a blanket
   retirement of every descendant: a contributor this sweep condemns
   stops counting as independent evidence one hop up, which can turn a
   survivor that read as corroborated into a sole-based one. The sweep
   iterates to a fixpoint; the condemned set only grows over a finite
   survivor set, so it terminates, and a row naming its own survivor is
   REFUSED as corrupt rather than walked (**R8**).
4. **The completeness statement** — §4c.

#### 4b-i. WHICH RECORD TYPES the sweep retires — the enumerated domain

**v1 said "records" and meant edges (internal S1, BLOCKING — and it was
right).** The word implied a domain it never stated, and the missing
member was not exotic: **episodes**, whose text reaches the model
directly.

**The precise shape of the defect, because it is sharper than "a type was
forgotten" and it is a class-G finding, not a class-C one.** The
normative reference NEVER forgot episodes: `validate_record` accepts
`type in ("edge", "episode")` and requires `active` / `retired_reason` on
both, and the vectors exercise episodes throughout. The DESIGN was
complete. What was missing sat in two other carriers: **the prose said
"records" without enumerating them**, and — the part that actually
bites — **the shipped store has no episode `active` field at all**, so
the reference presumed a mechanism the product does not have. An
evidence package can pass 54/54 against a reference whose record model
the product cannot implement. That is why §7a's shipped-shape row exists,
and it is why this finding is worth more than the type it names. Every stored type is enumerated here with its mechanism or its
EXECUTED exclusion argument; a type absent from this table is a defect in
the table, not a silent exclusion.

| stored type | does its content reach the model? | what the sweep does | mechanism |
|---|---|---|---|
| **edge** | YES — rendered claim lines | RETIRE | `_invalidate_edge_row`, the sole `active=0` writer (**R17**) |
| **episode** (`kind="chat"` etc.) | **YES — `__init__.py:869-872` renders `f"[{e.date}] {e.summary}"` straight into recall context**, split only into the third-party section, which is still rendered | **RETIRE** | **NEW, §4b-ii (**R18**)** — v1 had NO mechanism for this type |
| **episode** (`kind="outcome"`) | not into recall (`__init__.py:520-521` excludes it) — but it IS exported and counted by `introspect` | **RETIRE**, same mechanism | same; the exclusion from recall is not a reason to leave it standing in an export |
| **wiki** (derived) | YES — appended to `grounded_parts` | DROPPED, not recomputed | `0004`'s rule, inherited; `revoked_source` drops by default (§7b) |
| `contribution_ledger` | no — ids and typed links | unchanged; it is the sweep's INPUT | reading it is the join; retiring it would destroy the evidence the sweep runs on |
| `supersession_refusals` | **no — content-free BY CONSTRUCTION** (`refusal_id · user_id · prior_edge_id · incoming_edge_id · relation · two booleans · rule_version · created_at` — `schema_version.py:199`) | nothing | `0003` designed it content-free; the executed DDL is the argument |
| `confirmations` | no — ids, actor, call path, request digest | nothing | audit of a transition, carries no remembered content |
| `consolidation_ops` | no — `operation_id · fence · state · owner · lease · claimed_ids` | nothing | operational state; the CONTENT it points at is episodes, covered above |
| `store_identity` | no — the store's own singleton | nothing | `0006`'s namespace, not a record |

**The exclusions are arguments, not assertions**: each "no" above is the
executed DDL or the executed render path, recorded in §2c-ii, because
"that table has no content in it" is exactly the kind of claim that is
true until someone adds a column.

#### 4b-ii. Episode retirement — the mechanism v1 lacked (**R18**)

**Decision (Quentin, 2026-08-17): a JSON field plus ONE read seam — no
DDL.** The shape is chosen to inherit rather than to be remembered,
which is the same reasoning that moved `0004`'s fix into the sole writer:

- **The state** — `active: bool` and `retired_reason: Optional[str]` on
  the Episode model, serialised into the existing `episodes.json` blob.
  **No `ALTER TABLE`, no `SCHEMA` bump**, following the shipped precedent
  by which `0009`'s and `0010`'s episode fields landed
  (`schema_version.py` v2→v3 notes: *"serialise into the existing
  `episodes.json` blob — no episode-table ALTER"*).
  **The names are not a choice**: they are the fields the NORMATIVE
  REFERENCE already validates on every record of either type
  (`reference_revocation.py:501-503`, `_RECORD_FIELDS`), and the vectors
  already exercise episodes against them. Naming them differently in the
  product would be the cross-carrier mismatch this pair keeps catching in
  other people's designs.
- **The read seam** — `store.episodes(user_id, *, include_retired=False)`,
  **default-excluding**, exactly mirroring the shipped
  `store.edges(user_id, *, active_only=True, …)`. All **nine** Python
  readers (`compile.py` · `proactive.py` · `introspect.py` ·
  `lifecycle.py` · `portability.py` · `__init__.py`) inherit the
  exclusion **by construction** — none of them needs to remember it, and
  a reader added tomorrow inherits it too. This is the single most
  important property of the choice: the alternative was a filter every
  reader must repeat, which is the two-call-sites shape `0004` v3.1
  rejected on the write side.
- **The writer** — ONE function, mirroring `_invalidate_edge_row`, so
  the "sole writer" argument holds on this type as it does on edges.
- **The raw-SQL sites are DISPOSITIONED, not ignored.** There are
  fourteen `… FROM episodes` statements inside `store/sqlite.py`. They
  are the store's own internals and several MUST see everything —
  `forget` (erasure covers retired records too), export (`0005`
  round-trips retired state rather than dropping it), consolidation's
  claim/delete paths, the `0013` migrations. Each is dispositioned in
  §7a; the ones that must not see retired episodes route through the
  seam.

**The honest limit of this choice, stated because it is the price:** the
guarantee is **Python-level**. A future raw-SQL reader could bypass the
seam, where an `active` column would have let SQL filter too. **R18's
AST sweep is what stands there** — it asserts the seam is the only path
from `FROM episodes` to a rendered surface — and §10 **Q7** records
promoting the field to a column at the next schema window, so the
cheaper guarantee is a recorded decision rather than a silent ceiling.

**THE SWEEP RETIRES THROUGH THE SOLE WRITER OF `active=0`. This is a
CONSTRAINT ON THE DESIGN, stated with its reason, not an implementation
note.** 0004 v3.1 relocated its fix INSIDE `_invalidate_edge_row`
(`src/veracium/store/sqlite.py:242`, whose single `UPDATE edges SET
active=0` at `:251` is the only one in the tree), and its W7 pins that
with an AST sweep that FAILS THE BUILD if a second `SET active=0` writer
appears. Every retirement this sweep performs therefore goes through
`_invalidate_edge_row` — directly, or through `invalidate_edge` or the
supersession plan primitive, both of which funnel into it — **and never
through a bulk `UPDATE edges SET active=0 WHERE …` of its own**, which is
exactly what a sweep over many edges is tempted to write.

The reason is the composition this pair depends on: routing through the
sole writer is what makes the **wiki drop inherit BY CONSTRUCTION**
(§7b), rather than by this spec remembering to call it. A bulk update
would be a second writer, would bypass the drop for every edge it
touched, and would reintroduce precisely the defect 0004 exists to fix —
silently, because the retirements would look correct in every store
query. **If the sweep ever genuinely needs bulk performance, that is a
RIDER TO 0004's W7 and a reviewed decision — never a second writer added
here.** §5 records the regime that would force the question; **R17** is
the check, and it is 0004's own AST sweep, not a new one.

**THE NORMATIVE REFERENCE.** All of the above is defined executably in
`specs/evidence/0022/reference_revocation.py`, with pinned vectors in
`specs/evidence/0022/vectors.json` and the self-executing harness
`specs/evidence/0022/vector_harness.py`. The reference is PORTABLE AND
PURE — no store, no clock, no I/O — and mirrors the shipped digest
construction byte-for-byte, so reference-side digests equal store-side
digests. **R11** binds any implementation to it. This is the discipline
that let 0020's decision table survive fourteen review rounds; the
completeness classifier is the same kind of decidable core, and writing
the vectors before the prose already found two defects in this design
(the lift did not restore recomputed values, and the closure blanket-
retired descendants instead of recursing the corroboration test).

### 4c. The three completeness classes — BY CAPABILITY, NEVER BY ERA

The classes describe **what the ledger can tell us**, which is a property
of the rows in front of us, not of when they were written:

- **(a) typed-link rows** (`contributor_ref` present): the contributor
  graph WALKS. Full transitive closure; the survivor, its contributors
  and its descendants are all reachable.
- **(b) linkless rows** (`identity_digest` present, `contributor_ref`
  NULL): the SURVIVOR is identified completely — the `(user_id,
  identity_digest)` join is indexed and rows carry `survivor_type` +
  `survivor_id` — and, at the absorption site, the row's payload even
  carries the contributor's own side values, so classification and
  recompute both work. What does NOT work is the walk: the survivor's
  own DESCENDANTS cannot be enumerated. They are REPORTED unreachable.
- **(c) unattributed** (no rows at all): reported as unreachable, never
  guessed. The count is the number of system-authored records carrying no
  attribution rows, which is an **upper bound** on the population and
  deliberately so — over-reporting a blind spot is the fail-closed
  direction; under-reporting it is the failure C5 exists to prevent.

**Class (b) has a LIVE PRODUCER and is not a legacy class.**
Consolidation writes NULL contributor columns TODAY, by a documented
decision recorded at the site (populating them would break 0014's
field-for-field replay verify across the v7→v8 migration), so a store
created tomorrow still produces class-(b) rows at the consolidation site.
Dev verified this empirically against a live v8 store on 2026-08-17, and
the source assertion is executed at §2c-ii. A spec that called these
classes "eras" would have told operators the blind spot shrinks with
time; it does not.

**The sole-basis test (research's Q1, RULED as recommended).** Surviving
independent evidence requires a **DIFFERENT RESOLVED IDENTITY**. Two
consequences, both intended:

- **same-source self-corroboration must not save a record from its own
  source's revocation.** A source that restated a claim five times has
  given one source's testimony five times. This is 0012's independence
  condition — the same reasoning that stops a reinforcement from
  manufacturing currency out of repetition — applied to revocation.
- **an UNIDENTIFIED contributor (NULL digest) cannot corroborate
  either.** Otherwise omitting a `source_id` would immunise content
  against revocation, which is the adversarial cell of §2c in reverse.
  Absence never relaxes a rule (0006's own absence discipline).

**The completeness statement**, returned by every call, carries: the
target digest; whether the source stands revoked after the action; the
directly-sourced records; the affected survivors with their class and
kind; what will be retired and what recomputed; the three class counts;
whether the graph was walkable; and a single `complete` boolean that is
**FALSE whenever any class-(b) or class-(c) population is non-empty**.
An operator who revokes gets the true blast radius AND the true blind
spot (**R7**).

**Retired-synthesized is counted SEPARATELY from retired-sole-basis
(internal suggestion, adopted).** They are the same disposition and
completely different operator experiences: a sole-basis retirement is
gone because its only evidence is gone, and there is nothing to do; a
retired synthesized survivor (§4c) is gone because its text is
indecomposable, **and its content may be fully recoverable from evidence
that survived**. Lumping them hides an action behind a total. Split, the
statement can say *"N synthesized outputs retired — re-run `maintain()`
to re-derive them from surviving evidence"*, which is the one line that
makes §9.1's breadth cliff survivable in practice rather than only in
principle. The split is in the returned statement and the audit event
alike, and **R7** counts it.

### 4d. The recompute — restrict-only, and the ratchet

A corroborated restatement STANDS (the user said it too) and its
transferred state is **RECOMPUTED FROM SURVIVING EVIDENCE**, by the
transform the store already uses at write: the survivor's own
pre-absorption `base` folded with the `contributor` side of every row
whose source still stands, under `min(valid_from)`, `max(observed_at)`,
`max(confidence)`. Both halves are already in the ledger's absorption
payload, so **no `prior_values` column is needed** — the 2026-08-07
design's open question, closed by machinery that shipped in the
meantime (§2c-ii records both commands).

**Restrict-only is enforced twice, on purpose.** The transform is
monotone under contributor removal (min/max over a subset of the same
sides), and the result is then CLAMPED against the FULL-evidence fold —
which is exactly the value the store committed at write. So even an
implementation that someday changes the aggregator cannot turn a
revocation into a promotion. The clamp is a no-op under today's transform
and a guard under tomorrow's, and a vector proves it bites.

**Research's Q2 is RULED as recommended: EXACTLY the recomputed value,
never punitively below it.** A punitive lever would make revocation a
confidence weapon, and under C2 the operator can be tricked into pulling
it — the forged-source DoS gets worse the more damage each pull does.
Neutral recompute keeps the attack bounded at availability.

**The ratchet.** `ungrounded` is an N-ary OR over the merged set, so
re-deriving it over a SMALLER set can flip it True→False. That is a
promotion wearing a recompute's clothes, and it is the exact shape of
defect the found-in-fix checklist's first item exists to catch: the
recompute establishes a property (restrict-only) and the property has to
hold for EVERY field it touches, not the ones we were thinking about.
`ungrounded` is therefore excluded from the recompute by construction, and
so are `disclosure` and `derived_from` (**R5**).

### 4e. Dry-run and commit are ONE computation (research's Q3, ruled by dev)

`revoke_source(..., dry_run=True)` returns **the identical completeness
statement** without writing the revocation row and without retiring or
recomputing anything — **by running the SAME code path**. The preview and
the commit are not two implementations that agree by review; they are one
function and a boolean the function never sees:

```
statement = sweep(store, target, proposed=action)      # the ONE call
if dry_run:  return statement
append(action); apply(statement.effects); return statement
```

A preview that can diverge from its commit is the classic defect in this
shape of feature — it is the reason operators stop trusting previews, and
it fails silently, because the two paths agree on every example anyone
thinks to test. **R6** carries the invariant AND its executable check:
feed one store, run the preview, run the commit, and assert the two
statements are equal — including that the preview left the store
byte-identical, and that the planner is a pure function of its inputs
(the harness re-plans and compares).

### 4f. Reversal — DESIRED STATE, by supersession, never by edit

`unrevoke_source(user_id, origin, source_id, reason)` appends a lifting
row. Reversibility is a threat-model requirement (C2), not a courtesy.

**The reversal is not an undo log replayed backwards. It is the SAME
computation over the new standing set**, and that is the only construction
that gets the overlapping case right: a record condemned by TWO revoked
sources must stay retired when one of them is lifted. An effect log
replayed backwards reinstates it. The desired-state form has that cell
right by construction, and it is a pinned vector.

Concretely:

- retirements REVERSE BY SUPERSESSION — a new event that supersedes the
  retirement — **never by editing the retirement record and never by
  deletion** (C3). The effect vocabulary is CLOSED to `{retire,
  recompute, reinstate}` and contains no erasing verb; a vector asserts
  the vocabulary itself, because C3 is a property of the vocabulary
  before it is a property of any implementation.
- only retirements carrying reason `revoked_source` reverse. A record
  retired as superseded, lapsed or decayed is not this operation's to
  reinstate.
- recomputed values are restored **by recomputation** — the same fold
  over the restored evidence returns the same value the store committed
  at write, bounded structurally by the full-evidence fold so the restore
  can never overshoot. Recompute-not-restore, in both directions
  (**R10**).

### 4g. Interfaces, and what happens to existing stores

**New public API** (host-facing, library only):

| call | returns |
|---|---|
| `revoke_source(user_id, origin, source_id, reason, *, dry_run=False)` | the completeness statement |
| `unrevoke_source(user_id, origin, source_id, reason, *, dry_run=False)` | the completeness statement |
| `source_revocations(user_id)` | the standing set plus the append-only history, for the operator's audit view |

**Migration.** One SCHEMA bump adding one table (C6) — the ordinary 0013
migration path, no data rewrite, no back-fill, and nothing to recompute
at upgrade because the standing set of an unrevoked store is empty. A
store that never calls `revoke_source` is byte-identical in stored state
and in every read to one that never upgraded.

**What is unrecoverable.** Nothing this spec does — that is the point of
C3 and §4f. What is UNREACHABLE is a different matter and is stated
rather than fixed: class (c) records cannot be swept, and content written
by a source with no `source_id` has no digest and is not revocable at all.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| store with no identities anywhere | every sweep returns an empty radius; the class-(c) count may still be non-zero, and `complete` is then FALSE — which is the honest answer, not a bug |
| store that never revokes | stored state and every read are byte-identical to a never-upgraded store; the only difference is one empty table |
| a source with a handful of contributions | one indexed join, a closure of a few hops; the cost is dominated by the retirement writes |
| **a source responsible for MOST of the store** (the realistic connector case) | the join returns a large survivor set and the fixpoint iterates over it repeatedly. The sweep is O(passes × rows) and the pass count is bounded by the longest condemnation CHAIN, not by the row count. **The regime the tests must reach is a store with a chain deeper than 2 and a survivor set larger than one batch** — the 0020 lesson that small fixtures never truncate applies exactly: a single-level fixture cannot distinguish a correct closure from a broken one, and neither can a two-record one |
| deep absorption chains (A→B→C→…) | the recursion of the corroboration test settles at the fixpoint; the pinned vectors carry a chain cell, and **R8** names the regression |
| a store whose contributions are entirely class (b) — i.e. consolidation-heavy | every affected survivor is classified and treated, and `complete` is FALSE for every sweep. This is the LIVE case, not a legacy one |
| pre-0014 store, upgraded | class (c) dominates; the report says so; nothing is guessed |
| revoking a source that contributed nothing | empty radius, a recorded row, fully reversible. A valid act |
| **a sweep large enough to want a bulk UPDATE** | the retirement loop runs one `_invalidate_edge_row` per record. If a real store ever makes that the bottleneck, the answer is a RIDER to 0004's W7 — a reviewed second writer with the wiki drop carried into it — never a bulk path added quietly here (§4b). No such regime is measured today, and this row exists so the question is asked before the shortcut is taken |
| cold vs warm | no caches are involved except the wiki, which is DROPPED by the retirement (§7b). First call and thousandth behave alike; the second revoke of a standing source plans nothing (**R16**) |
| two hosts revoking concurrently | the append is ordinal-ordered per user; the loser's sweep re-derives from the standing set including the winner's row, so the two converge rather than racing to a stored flag. The ordinal collision case REFUSES rather than guessing (**R1**) |

## 6. Invariants and executable checks — REQUIRED, blocking

**Status: STAGE-5 OBLIGATIONS — none of the named tests exists yet
(draft).** The vectors and the harness DO exist and run today; **R11** is
the only row with a live artifact, and its evidence is
`specs/evidence/0022/vector_harness_result.txt`.

| invariant | executable check |
|---|---|
| **R1** the standing state is DERIVED from an append-only table: latest row per (user, digest) wins, no UPDATE or DELETE writer exists against `source_revocations`, and two rows at one ordinal REFUSE | `test_revocation_state_is_derived_not_stored` + `test_no_update_writer_against_source_revocations` (an AST sweep, the `test_sole_active_zero_writer` pattern) |
| **R2** a revocation retires the directly-sourced records with reason `revoked_source`, and deletes nothing | `test_revoked_source_retires_direct_records` |
| **R3** the sole-basis test requires a DIFFERENT RESOLVED IDENTITY: same-source self-corroboration does not save a record, and a NULL-digest contributor does not corroborate | `test_sole_basis_requires_a_different_identity` |
| **R4** the recompute is EXACT and RESTRICT-ONLY: exactly the surviving-evidence fold, never punitively below it, never above the full-evidence fold — with the clamp exercised against a deliberately non-monotone aggregator | `test_recompute_is_exact_and_restrict_only` + `test_revocation_grants_nothing` (the enumerated temptations) |
| **R5** the ratchet: `ungrounded` is never recomputed downward, and `disclosure`/`derived_from` are never written by a revocation | `test_revocation_never_clears_the_ungrounded_flag` |
| **R6** dry-run and commit produce the IDENTICAL statement from ONE code path; the dry run leaves the store byte-identical; the planner is a pure function of its inputs | `test_dry_run_equals_the_commit` (+ the `preview_agrees` vectors) |
| **R7** the completeness statement reports all three class counts, **counts retired-synthesized separately from retired-sole-basis** (§4c — same disposition, different operator action: synthesized output is re-derivable from surviving evidence, sole-basis is not), and is `complete=False` whenever the class-(b) or class-(c) population is non-empty | `test_completeness_statement_is_honest` + `test_retired_synthesized_counted_separately` (a store with both kinds; the two counts must not collapse into one) |
| **R8** consumption closure is TRANSITIVE and the property RECURSES (a condemned contributor is not corroboration one hop up); a self-naming row REFUSES instead of looping; the fixpoint terminates | `test_closure_is_transitive_and_recursive` |
| **R9** supersede-never-erase: after any revoke/lift sequence every record is still present, history only grew, and no effect verb outside `{retire, recompute, reinstate}` exists | `test_revocation_only_appends` |
| **R10** a lift is DESIRED STATE, not undo: it reinstates only what `revoked_source` retired, restores recomputed values by recomputation, and leaves a record retired while a SECOND revocation still reaches it | `test_lift_is_desired_state_not_undo` |
| **R11** the shipped surface agrees with the normative reference on every pinned vector, through the SHIPPED harness | `test_revocation_reference_vectors` — today: `.venv/bin/python specs/evidence/0022/vector_harness.py`, whose recorded result ships as `vector_harness_result.txt` (the one carrier for the count) |
| **R12** a source with no `source_id` has no digest, no join and no reach: it cannot be revoked and cannot be reached by any revocation | `test_unknown_source_is_not_revocable` |
| **R13** revocation is PER USER: a revocation for one user changes nothing observable for another, including the standing state consulted at write time | `test_revocation_does_not_cross_the_user_boundary` |
| **R14** the surface is host-API only — absent from the CLI parser table and from the MCP tool registry | `test_revocation_is_not_exposed_on_the_agent_surfaces` (the §2c-ii commands, as a test) |
| **R15** a `revoked_source` retirement drops the compiled wiki, and `revoked_source` is registered in 0004's `DISPOSITIONED_REASONS` so its totality check passes | `test_revocation_drops_the_wiki` + 0004's own `test_invalidation_reason_registry_is_total` |
| **R16** the sweep is idempotent: a second revoke of a standing source appends its row and plans no further effect | `test_second_revoke_is_a_no_op` |
| **R17** every retirement the sweep performs routes through `_invalidate_edge_row`, the SOLE writer of `active=0` — no bulk update path exists, so the wiki drop is inherited by construction (§4b) | 0004's own `test_sole_active_zero_writer` (the AST sweep — a second writer FAILS the build) + `test_the_sweep_retires_through_the_sole_writer` |
| **R18** the sweep's record DOMAIN is the enumerated one (§4b-i), and EPISODES are retired by it — through ONE writer, with `store.episodes()` default-excluding retired rows so all nine readers inherit the exclusion (internal S1; v1 had no mechanism for this type at all) | `test_revocation_retires_episodes` (a revoked source's episode text must not appear in `recall()`'s rendered context — the assertion at the RENDER surface, not at the store) · `test_episode_read_seam_is_sole_path` — an AST sweep asserting every `FROM episodes` outside the dispositioned §7a list routes through `store.episodes()`, which is what stands in for the SQL-level guarantee a column would have given · `test_retired_episode_round_trips` (export/import preserve retired state rather than resurrecting it). **The VECTOR side of R18 is ALREADY SATISFIED and was before the finding: 18 of the 54 vectors carry episode-typed records, and the reference retires them with `revoked_source` exactly as it retires edges** (executed, §2c-ii) — which is precisely why S1 is a class-G finding. The evidence proved the DESIGN over both types while the product had a mechanism for only one |

Standing checks that must not regress: injection asserts 0 · cross-user
leaks 0 · trust canaries 0 · supersession probes pass · malformed edges 0
· the declared read-cost ceilings.

## 7. Failure modes and reversibility

- **How it fails SILENTLY.** The dangerous failure is **under-revocation**
  — the sweep misses part of the blast radius and reports success. The
  first visible symptom would be revoked content resurfacing in an
  answer, possibly weeks later, with nothing in the audit trail saying it
  was missed. This is precisely why C5 makes the completeness statement
  non-negotiable and why `complete` is a boolean the caller cannot avoid
  reading. The counterpart failure — **over-revocation** — is loud,
  bounded and reversible.
- **Reversibility.** Full, by design and by threat model. The standing
  state reverses by appending a lifting row; the retirements reverse BY
  SUPERSESSION; the recomputed values return by RECOMPUTATION over the
  restored evidence. Nothing is deleted, so nothing needs restoring from
  a backup. What does NOT reverse: any maintenance the operator chooses
  to run in between (a re-derivation is a new record), and 0021's
  standing rule that consolidation's effects are permanent once run.
- **Partial failure.** The sweep's writes are the retirement and
  recompute effects plus the revocation row. **The row and the effects
  must land in ONE transaction**, in that order, or a crash leaves a
  store whose standing state disagrees with its records. Because the
  standing state is DERIVED and the effects are a DIFF against it,
  re-running the sweep after any crash converges: a partially applied
  sweep re-plans exactly the remainder (**R16**'s idempotence is the same
  property). This is the honest version of crash-safety here — not
  "atomic and therefore fine", but "atomic, and self-healing if the
  atomicity is ever violated".
- **New attack surface.** One: the operator-supplied `reason` string,
  which is stored and shown to operators, never to the model. The
  revocation surface itself is unreachable from ingest, MCP and the CLI
  (**R14**), so no non-user content can influence stored state through
  it. The forged-source cell (§3b) is an attack on the operator's
  JUDGEMENT, not on the mechanism, and is bounded to availability by
  restrict-only.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `veracium.Memory` (host API) | `revoke_source`, `unrevoke_source`, `source_revocations` |
| `src/veracium/store/base.py` + `store/sqlite.py` | the append-only table, its validated reads, and the one-transaction sweep application; the existing `contributors_of_source` join is CONSUMED unchanged, and every retirement routes through `_invalidate_edge_row` — **no new `active=0` writer** (§4b, **R17**) |
| `src/veracium/store/schema_version.py` | one new table (SCHEMA bump, ordinary migration). **NO episode-table `ALTER` — §4b-ii's retirement state rides `episodes.json`, the shipped `0009`/`0010` precedent** |
| **`schema.py` — the `Episode` model** | **`active: bool = True` and `retired_reason: Optional[str] = None`, named to match the normative reference's `_RECORD_FIELDS` exactly (**R18**, internal S1)** |
| **`store.episodes()` — the ONE read seam** | gains `*, include_retired: bool = False`, **default-excluding**, mirroring the shipped `store.edges(active_only=True)`. All nine Python readers inherit the exclusion; none of them changes |
| **the fourteen raw `… episodes` SQL sites in `store/sqlite.py` (+2 in `store/migration.py`) — DISPOSITIONED, not ignored** | **MUST see retired rows** (whole-set by contract): `forget` (erasure covers retired records), export (`0005` round-trips retired STATE rather than dropping it — **R18**), consolidation's claim/delete paths, the `0013`/`0018` migrations, the counters. **MUST NOT**: anything feeding a rendered surface — and those already route through the seam. The check is closed because all sixteen sites are inside the store package (§2c-ii) |
| **one episode retirement writer** | the sole writer for this type, mirroring `_invalidate_edge_row`, so the sole-writer argument holds on episodes as it does on edges |
| the invalidation reason vocabulary | `revoked_source`, registered in 0004's `DISPOSITIONED_REASONS` (§7b) |
| `specs/evidence/0022/` | `reference_revocation.py` + `vectors.json` + `vector_harness.py` + the recorded result (NORMATIVE — **R11**) |
| `audit.py` | one event per revocation and per lift, carrying the digest, the action, the class counts and `complete` — content-free by construction |
| CLI / MCP | **UNCHANGED, by decision** (**R14**) |
| docs | the operator guide: what a completeness statement means, what class (b) and class (c) cost, and the forged-source honesty |
| CHANGELOG / marketing | §8's exact wording; no claim beyond it |

### 7b. Cross-spec carriers

| spec | touchpoint | disposition |
|---|---|---|
| **0023** | **MUTUAL `Spec-Requires` — acceptance is ATOMIC** (the 0016/0018 and 0020/0021 precedent) | this spec's sweep without 0023's non-revival is a boundary with an unlocked back door; 0023 without this sweep governs only the future. Neither accepts alone, and the gate enforces it rather than a sentence |
| **0004** | **THE DRAFTED RIDER — same-commit landing at this pair's acceptance.** *0004 v3.1 (2026-08-17) made §4 DROP-BY-DEFAULT over a closed RETAIN allow-list, which changes this rider's shape and improves it* | *(the rider, verbatim)* **`revoked_source` is added to 0004's `DISPOSITIONED_REASONS` with the disposition DROP.** Under drop-by-default there is NO trigger set to add to: `revoked_source` already drops the wiki the moment the reason exists, because the runtime consults `WIKI_RETAINING_REASONS` (membership → retain; everything else → drop) and `revoked_source` is not in it. **The rider is therefore a PROCESS edit, not a behaviour one** — it registers the reason so 0004's W5 totality check, which diffs the reasons reachable at every producer against `DISPOSITIONED_REASONS`, passes. **Why this is the better shape, and the more interesting half: if the rider is FORGOTTEN ENTIRELY, the failure is a RED BUILD — W5 sees an un-dispositioned reason reachable from a producer — rather than a silently retained wiki serving revoked content.** The coupling is fail-closed in both directions, which is the property this pair wants. Two facts from 0004 v3.1 relied on here and NOT re-litigated: the two constants are distinct (`WIKI_RETAINING_REASONS` is the runtime's, `DISPOSITIONED_REASONS` is the process record; a reason missing from both still drops), and **W-Q1 is RESOLVED (research, 2026-08-17): `absorbed_duplicate` does NOT drop the wiki, because absorption is trust-preserving — the content stays backed by a live same-trust record, pinned by 0004's W8. This spec's sweep reaches absorbed contributors THROUGH THE LEDGER, and the retirement it writes carries `revoked_source`, which drops — so the exclusion shelters nothing revoked.** **And one constraint 0004 v3.1 puts on THIS spec's design, accepted here: W7 makes `_invalidate_edge_row` the sole writer of `active=0` and fails the build on a second one, so the sweep retires through it and never in bulk (§4b, R17). A bulk path would need a rider to W7, reviewed there — not a workaround here.** |
| **0006** | **THE DRAFTED AMENDMENT — same-commit landing at acceptance; separate cross-spec sign-off required** | 0006's affirmative rule that `(origin, source_id)` affects **no** trust/authority/disclosure/staleness/supersession decision *in v1* is amended to: *identity feeds exactly ONE decision — source revocation — which is RESTRICT-ONLY and operator-initiated; it still grants nothing, groups nothing new, and no read path infers trust from identity.* **The CARRIER that must move with it is its CI test**, `test_source_id_affects_no_decision`, which asserts that adding or changing `(origin, source_id)` changes no output: once revocation ships, that test is true only OUTSIDE a standing revocation, and it must be amended in the same commit or it fails the day this lands. The digest rule, the absence rule (no `source_id` ⇒ no digest ⇒ not revocable by source) and the resolve-at-read rule are INHERITED VERBATIM and are load-bearing here |
| **0014** | the ledger, the digest join, the absorption payload | CONSUMED, not amended. `contributors_of_source` is the accepted blast-radius join (named A9 there, and already implemented); the `{base, contributor}` payload is what makes recompute-not-restore true; the insert-only discipline is the precedent §4a follows. **This spec writes no ledger row** |
| **0020** | the store-authored-derivative predicate; UNRESOLVED membership | CONSUMED. This spec does not restate the predicate — the reference reads the row's SITE, a present field. An UNRESOLVED derivative is not made resolvable by revocation; it falls in class (b) or (c) and is reported |
| **0021** | transitively closed consumption; the consolidation partition; the flattening that produces typed links | the closure rule is INHERITED (C4). Post-0021 absorptions are class (a) by construction, which is what makes the walk work at all; consolidation remains class (b) |
| **0013 / 0018** | the SCHEMA bump for one new table | the ORDINARY migration path (C6). This spec asks for no breaking window and rides nobody else's |
| **0008** | `needs_confirmation` | untouched; `confirm()` remains the only clearing path |
| **0012** | the persisted reinforcing edge; the independence condition | the surviving-evidence set exists BECAUSE 0012 persists every contributor, and §4c's sole-basis test is that spec's independence condition applied to revocation |
| **0017** | operator telemetry | the class counts are content-free and would be a natural consent-versioned metric; DEFERRED and recorded, not shipped here |

## 8. Claims and limits

**What we will say** — the exact wording, in the changelog and anywhere
else:

> **Source revocation.** A host can revoke a source it no longer trusts.
> The records that came from it — **both the extracted claims and the
> stored episodes** — are retired; records it merely contributed to
> are re-derived from the evidence that survives, or retired if it was
> their only basis. Every revocation returns a completeness statement
> saying what was reached AND what could not be — and it is reversible.

**What this does NOT establish.**

- **It is not authentication.** The revocation key is namespacing (C2).
  An attacker who can write under a victim's `(origin, source_id)` can
  bait an operator into revoking the victim. Reversibility, restrict-only
  and dry-run bound that to availability; they do not close it. Signed or
  re-namespaced origins are S3's world.
- **It is not erasure.** Revoked content is RETIRED, not deleted;
  `forget()` remains the data-subject erasure surface and is unchanged.
  Do not describe revocation as deletion anywhere.
- **It is not complete, and it says so.** Class (b) survivors have
  unreachable descendants; class (c) records are unattributed and are
  reported as an upper bound, not enumerated. A revocation over a
  consolidation-heavy store returns `complete=False` — and that is the
  correct output, not a defect. **The blind spot does not shrink with
  time**, because class (b) has a live producer.
- **`complete=False` is the EXPECTED STEADY STATE on any store that has
  ever consolidated, and operators must be told so up front (internal
  M4).** The boolean is false whenever the class-(b) population is
  non-empty, and class (b) has a live producer — so a consolidation-
  bearing store will essentially never return `complete=True`. Documented
  here, in the changelog line, and in the operator-facing return, because
  a flag that is *always* false reads as a broken flag to everyone who
  was not in this conversation. **It is not a health indicator; it is a
  scope statement**, and the actionable content is in the counts beside
  it, never in the boolean.
- **It is per user.** Revoking a source for one user revokes nothing for
  another. A store-wide claim is the host's aggregation, not ours.
- **No measurement is claimed here.** The resurfacing probe that would
  measure post-revocation behaviour end to end is research's D-extension
  obligation and is not evidence this spec cites. The only executed
  evidence in this document is the §2c-ii command table and the vector
  harness result.

## 9. Brief for the external reviewer

**What we are least sure of:**

1. **The synthesized-vs-restatement split (§4c).** We rule that a
   consolidation output whose input set includes a revoked source is
   RETIRED even when other sources corroborate it, because the synthesized
   text may embed revoked material and corroboration does not launder it.
   That is the fail-closed direction, but it is also the expensive one: on
   a consolidation-heavy store a single revocation may retire a large
   share of the curated layer. If you can construct a state where this
   cliff pushes an operator toward *not* revoking — defeating the boundary
   socially rather than technically — we want that finding now. The 0021
   round-9 brief raised the same shape of concern about UNRESOLVED
   economics and it was the right question.
2. **The class-(c) upper bound.** We count system-authored records with
   no attribution rows and call it an upper bound on the unreachable
   population. It over-counts (a system-authored observation that is not a
   derivation) and, more worryingly, we are not certain it cannot
   UNDER-count: a derivation-shaped record that is not system-authored
   would escape it. Attack that predicate.
3. **The recompute's authority.** §4d assumes a surviving edge's
   `confidence`/`observed_at`/`valid_from` are set at write and moved only
   by the absorption transform, so the ledger fold is authoritative. If
   you can find a shipped path that moves any of those three outside that
   transform, the restoring pass in §4f could raise a value some other
   mechanism deliberately lowered.

**Where we suspect we have overstated:** the phrase "the true blast
radius" in §4c. It is true only of the reachable classes; the statement
says so, but the sentence is more confident than the mechanism.

**What would change our minds about the approach:** a construction where
the standing state must be consulted somewhere the derivation is too
expensive (making the derived-state choice wrong), or a demonstration
that the per-user scoping makes the common connector case unusable.

**Reviewer-safe copy:** nothing here is deployment-specific; the whole
document generalises.

## 10. Open questions

| # | question | state |
|---|---|---|
| **Q1** | sole-basis: does surviving independent evidence require a DIFFERENT resolved identity, or any surviving edge? | **RESOLVED as research recommended: a DIFFERENT RESOLVED IDENTITY** (§4c). Same-source self-corroboration must not save a record from its own source's revocation — 0012's independence condition applied to revocation — and an unidentified contributor cannot corroborate either, or omitting a `source_id` would immunise content. Pinned by **R3** and four vectors |
| **Q2** | does revocation demote confidence on corroborated records BELOW the recomputed value (punitive) or exactly to it (neutral)? | **RESOLVED as research recommended: EXACTLY to it** (§4d). Restrict-only means neutral recompute, not punishment; a punitive lever makes the forged-source DoS worse with every pull. Enforced twice — monotone transform, then the clamp — and pinned by **R4** |
| **Q3** | the dry-run / report API shape | **RESOLVED (dev): ONE COMPUTATION, TWO CALLERS** (§4e). `dry_run=True` returns the identical statement by running the same code path; the spec carries the invariant and its executable check because a preview that can diverge from its commit is the classic defect here. Pinned by **R6** and the `preview_agrees` vectors |
| **Q4** | pre-0014 unattributed history: offer a blunt per-user "quarantine everything older than attribution" escape hatch? | **RESOLVED as research recommended: NO in v1** — recorded as a REJECTED ALTERNATIVE in §1 with the reason (it converts a precise tool into a shotgun, and it retires user content the revoked source never touched). Class (c) is REPORTED instead. Revisit only if an operator with a real pre-0014 store asks for it |
| **Q5** | store-wide revocation across users | `deferred` — v1 is per user (§3b) because every join and operator surface is user-keyed. A store-wide form is a recorded widening; dev decides if a host asks |
| **Q6** | should a revocation's completeness statement be DURABLE (queryable later) rather than only returned? | `pre-release` — dev, before implementation. The audit event carries the counts; storing the full statement would make "what did that revocation reach" answerable months later, at the cost of a second carrier for a value the sweep can always recompute. **Leaning: audit event only — but the v1 REASON was wrong and is corrected (internal M1).** "The sweep is a pure function and can be re-run" is false across time: the function is pure over inputs that MUTATE, so a re-run months later answers *what the store looks like now*, not *what that revocation reached then*. Recomputation reproduces only the present. The leaning survives on the honest ground: **the audit event IS the durable record**, and a second stored copy of a statement the audit already carries is a second carrier to keep consistent (§3b's rule against exactly that) |
| **Q7** | should `revoke_source` accept a digest directly, for a source whose pair the operator no longer has? | `deferred` — research + dev. It would let an operator act on a digest read from `introspect` without knowing the pair, but it also lets an operator revoke something they cannot name. Not needed for v1 |
| **Q8** | should the episode retirement field (§4b-ii) be PROMOTED to an `active` COLUMN on the `episodes` table at the next schema window? | `post-v1` — recorded rather than deferred silently, because the v1 choice has a stated ceiling. **Decided for v1 (Quentin, 2026-08-17): JSON field + the `store.episodes()` read seam, no DDL** — it ships without a migration and gives every reader structural inheritance, which is the property that matters most. **The ceiling it accepts:** the guarantee is Python-level, so a future raw-SQL reader could bypass the seam where a column would let SQL filter too. **R18**'s AST sweep is what stands there, and the fourteen raw sites are all inside the store package (§2c-ii), so the check is closed rather than hopeful. Promote when a schema window opens for another reason — never open one for this alone |

## Review closure

*(PROCESS §4a — one row per review finding, with evidence that is openable
or executable. **This spec is a pre-review DRAFT: no round has been run, so
there are no findings and no rows.** The section exists from day one
deliberately — both 0020 and 0021 hit this gate mid-implementation and had
to reconstruct it, and the CI gate refuses an `accepted` spec without it.
When rounds begin, the rows land here and the compressed per-round
dispositions go to `specs/reviews.py`, which is what the STATUS index
renders from.*

*One convention is fixed NOW, because it is easier to adopt than to
retrofit: **rounds with 0023 will be COUPLED, so counts will have TWO
BASES** — the PER-ROUND count (how many distinct findings a round's report
raised, which is what the verbatim report says) and the PER-SPEC count
(`specs/reviews.py` sums per spec, and a finding landing on both specs is
recorded in both rows, so the per-spec totals are necessarily larger). No
single number is "the" count; the round reports are authoritative for what
was raised and this table for what closed it. That is 0020's model, and it
exists because a reader who sums the wrong basis thinks the other is a
typo.)*

| round | finding | class | owner | disposition | evidence |
|---|---|---|---|---|---|
| — | *no review rounds yet (draft)* | — | — | — | — |
