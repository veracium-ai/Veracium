# Feature spec: source revocation — the standing state and the sweep (A3a)
*(The hand-written round table that stood here is REMOVED — external round 5, R5-3. It stopped before external rounds 3-4 while claiming to be the closure ledger, and `render_closure.py --check` could not see it because it only guards the marked block. A second, unguarded summary of the same facts is the exact defect the generator was introduced to end; keeping one was the fix failing to finish. The generated ledger below is the only one.)*


Spec-Status: accepted
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
>
> **v3 — EXTERNAL round 1 folded (RETURN FOR AMENDMENT; three blocking
> findings on this spec).** **F2:** the standing state ordered by `(at, seq)`
> while `at` is host-supplied — so a planted far-future timestamp made a
> revocation **permanently unliftable**, executed by the reviewer. Ordering
> is now `seq` ALONE, `at` is audit metadata, and five clock-skew vectors
> pin it. **The instructive part: §2c had NAMED this exact attack and its
> governing rule answered a different question**, which is why §2c now
> carries a note on its own evidential status — a cell in §2c is prose, a
> cell in §2c-ii is a command and its output, and F2 lived in the gap.
> **F3:** "supersession, never edit" was true of no carrier in the product —
> the reference mutated in place against an abstract `history` list, while
> `_invalidate_edge_row` UPDATEs the edge row and §4b-ii adds mutable
> episode fields. C3 is NARROWED to retain-never-erase over reversible
> in-place state backed by the append-only `source_revocations` ledger, the
> withdrawal is stated as a withdrawal, and **Q9** opens the successor for a
> real retirement-event carrier so the narrowing cannot become permanent by
> default. **F4:** class (c) was gated on `system_authored` and so was not
> the upper bound it claimed — a pre-`0014` absorption survivor keeps the
> incoming record's user authorship while carrying transferred values no row
> names. Class (c) is now every unattributed AND unreached record, whatever
> its authorship, with a biting vector.*

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
| C3 | **retain-never-erase** (v3 — WITHDRAWN NAME quoted to retract it: this rule was called *supersede*-never-erase until external round 1's F3 — the supersede half named a carrier the product does not have) — reversible in-place record state over an append-only LEDGER | house rule | revoked records RETIRE with reason `revoked_source`; **nothing is deleted and content stays re-derivable**; `forget()` remains the separate data-subject erasure op. **This spec does NOT define retirement events, ids, links or read-time resolution — the shipped store changes record state in place (`_invalidate_edge_row`) and the append-only carrier is `source_revocations`.** §4f states the withdrawal; **Q9** holds the successor |
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
| the `source_revocations` rows the store reads back — **PRODUCERS row: the host's `revoke_source` call AND THE STORE'S OWN MACHINERY (migration, recovery, and any future importer of an operator log)** | no rows → nothing is revoked; every read path behaves exactly as today | a NULL digest, an unknown action, a missing reason, a non-int ordinal, an unknown column → **REFUSED at read**, never coerced. A NULL-digest row would be a `(resolved_origin, NULL)` pseudo-source, which 0006 forbids, and would revoke every unknown-source record in one row | an action string this version does not know → refused; a future action cannot be silently treated as "revoke" or as "lift" | a row planted with a far-future timestamp to win the latest-row rule | **R1**: `at` ORDERS NOTHING — the latest row is decided by the committed `seq` alone, so a planted timestamp cannot win a comparison it does not enter. Two rows sharing one append ordinal still make the rule undecidable and REFUSE rather than resolving by insertion order. **This cell is why F2 is the round's most instructive finding: v2 NAMED this exact attack here and its governing rule answered a DIFFERENT question** — it addressed duplicate ordinals while the reference went on comparing `(at, seq)`. The attack was written down, unaddressed, for two internal rounds |
| the 0014 contribution rows the join returns — **PRODUCERS: absorption (`apply_supersession_plan`), consolidation, the import primitive, and 0021's flattening** | a survivor with no rows → it is not reachable through contribution at all, and it is COUNTED in class (c) **whatever its authorship**, provided this sweep has not already reached it (round-1 F4; **this cell was the THIRD carrier and survived round 2's sweep — see the note below**) | a half-typed link (`contributor_ref` without `contributor_type`) → refused; legacy rows carry BOTH columns NULL, so a half link is corruption, not history | a site this version does not know → the row still counts as evidence for the sole-basis test and its class is read from the typed link, which is total over any site vocabulary | a row NAMING ITS OWN SURVIVOR, which would make a walker loop — the 0020 post-acceptance defect, found by differential fuzzing | **R8**: the closure REFUSES corrupt linkage rather than continuing past it, and the fixpoint terminates because the condemned set only grows |
| a record's own identity fields, at sweep time | absent `source_id` → unreachable by any revocation, by construction | out-of-bounds → refused by the shipped model validation before this spec sees it | an origin naming a foreign store → resolved as-is (a foreign record keeps its own origin), so it is revocable only under that pair | a writer OMITS `source_id` so its content cannot be revoked | acknowledged and stated in §8: absence buys unreachability, and it costs the writer every grouping benefit. **R12** names the cell rather than pretending the rule is closed |
| the operator's `reason` string | empty/whitespace → REFUSED. A revocation with no recorded reason is not auditable | non-str → refused | — | a reason echoing memory text into the audit sink | the reason is OPERATOR-SUPPLIED and lands in the revocation row, which is operator-facing state, never model context. **R14** keeps the whole surface off the agent-reachable paths |

**A NOTE ON THIS TABLE'S EVIDENTIAL STATUS, added at v3 because F2 turned
on it.** Every cell in §2c is a CLAIM IN PROSE. Every cell in §2c-ii below is
a COMMAND AND ITS REAL OUTPUT. F2 lived in the gap: the far-future-timestamp
row above named the attack, asserted a rule, and nothing executed the pair
together — so the spec carried an adversarial cell whose stated defence the
reference did not implement, through two internal rounds, with both sessions
reading the table and finding it convincing. **An adversarial cell without a
vector is a sentence, not a defence.** The clock-skew vectors added at v3
begin closing that; §10 **Q10** carries the general form.

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
  is written, dropped or rewritten and **no record is deleted**. Retirement
  and reinstatement UPDATE THE RECORD'S STATE IN PLACE
  (`active`/`retired_reason`); the append-only carrier is
  `source_revocations`, and record state is DERIVED from it (**R9**).
  Provenance itself is never rewritten.

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
  - revocation is REVERSIBLE — reversal recomputes the desired state from
    the new standing set and restores the record in place (**R10**) — so
    the operator is never one mistake away from an unrecoverable state;
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
identity_digest)` by `seq` ALONE — and is never stored.** There is no
`active` column and no UPDATE statement anywhere near this table.

**`at` IS AUDIT METADATA AND ORDERS NOTHING (external round 1, F2).** v2
ordered by the tuple `(at, seq)` while asserting two paragraphs later that
`seq` is *the* unique append ordinal — two claims that contradict each other
in effect. `at` is **host-supplied**, and §2c had already named a planted
far-future timestamp as adversarial input, so **the attack this spec wrote
down defeated its own reference**, executed by the reviewer:

```
seq=0  revoke  at 2099-01-01     <- a skewed or malicious clock
seq=1  lift    at 2026-08-17     <- appended LATER, by the store's own order
standing after the lift = True   <- the lift never takes
```

**A revocation became permanently unliftable — the one property this spec
promises it is not.** Ordering by the committed ordinal is not merely the
fix; it is the only ordering the store can vouch for. **A clock is an input;
the append order is a fact.** Five vectors pin it: far-future revoke,
clock rollback, identical timestamps, list order disagreeing with `seq`, and
the epoch case.

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
  guessed. **The count is EVERY record carrying no attribution rows that
  this sweep has not already reached — WHATEVER ITS AUTHORSHIP** (external
  round 1, F4; the authorship gate was withdrawn there and this carrier
  still stated it at round 2, F2). It is an **upper bound** on the
  UNREACHED population and deliberately so — over-reporting a blind spot is
  the fail-closed direction; under-reporting it is the failure C5 exists to
  prevent. The `unreached` qualifier is load-bearing: a class-(a) record is
  already found and acted on, and counting it inflates the one number whose
  job is to say what the sweep could NOT see.

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

**Class (c) is defined by MISSING LINKAGE, not by authorship (external
round 1, F4).** v2 counted only `system_authored` records with no
contribution rows and called the result an upper bound. **It was not one.**
A pre-`0014` absorption survivor keeps the INCOMING record's provenance —
routinely user-authored — while carrying values transferred from a
contributor that no ledger row names, because the linkage discipline did not
exist when it was written. That is precisely the blind spot class (c)
reports, and authorship excluded it: the reviewer re-ran the supplied
class-(c) vector with its unattributed record marked non-system-authored and
got `class-c-unattributed=0`, `complete=True` — **a store declaring itself
completely swept while unreachable derived content survived in it.**

**Authorship says who wrote the EVIDENCE, not whether the store later
combined it with anything.** The only sound predicate available is the
absence of linkage itself: a record with no rows is a record whose
derivation history the store cannot vouch for, whoever wrote it. Class (c)
is therefore **every record with no contribution rows that this sweep has
not already reached** — the unreached qualifier matters, because counting a
class-(a) record that was found and retired inflates the one number whose
entire job is to say what the sweep could NOT see.

This over-reports: an ordinary user fact that never combined with anything
is counted. **Over-reporting is the correct direction for a blind-spot
count** — a number honestly too big says "look here"; a number quietly too
small says "nothing to see" — and the size of this count is itself the
signal about the store's linkage coverage.

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

#### 4e-i. The COMMIT path's concurrency, CONSTRUCTED (external round 2, F3)

**The pseudocode above is a data-flow sketch and v3 shipped it as if it
were a concurrency contract. It is not one, and the reviewer constructed the
race:** two hosts both read `max(seq)=4`, both plan against the same standing
set, both allocate `seq=5`. The unique ordinal then rejects one *valid*
operation — or, without it, produces exactly the ambiguity **R1** refuses.
v3 asserted a winner and a loser and specified neither.

**The construction, exactly — and v3 printed something that does NOT do this
(external round 3, R3-1).** v3 wrote `with conn:` and labelled it
`BEGIN IMMEDIATE`. **Python's `sqlite3` context manager begins nothing** — it
commits or rolls back at exit. Probed on the shipped connection config
(`sqlite3.connect(path)`, `store/sqlite.py:60`):

```
isolation_level                 = ''
in_transaction BEFORE a SELECT  = False
in_transaction AFTER  a SELECT  = False
statements traced               = ['SELECT 1']       <- no BEGIN, ever
```

So the printed construction still allows two hosts to read the same next
ordinal. **And the harness was green on a DIFFERENT construction** — it
executed `BEGIN IMMEDIATE` explicitly — which is worse than either error
alone: the evidence agreed with the fix rather than with the spec.

**v4 therefore has ONE function, shown here and CALLED by the evidence** (`specs/evidence/0022/store_concurrency_harness.py`), so the two
cannot drift again:

<!-- GENERATED:r19-operation -->
*GENERATED from `specs/evidence/0022/store_concurrency_harness.py` by `specs/render_operation.py` — BYTE-FOR-BYTE, nothing stripped or reformatted, because the finding this closes (R5-2) was a spec block that differed from the executable it claimed to quote. `_gate` and `_fault` are TEST HOOKS, `None` in every non-test call; they appear here because they appear in the code, and hiding them would reintroduce exactly the divergence.*

```python
def revocation_operation(conn, user, digest, action, reason, at, *,
                         plan, busy_deadline_s=5.0, _gate=None, _fault=None):
    """Allocate, re-read, plan, append the operator's row, APPLY EVERY EFFECT,
    and commit — or roll ALL of it back.

    THIS IS THE CONSTRUCTION §4e-i quotes and the checks below call.

    EXTERNAL ROUND 4, R4-1 — WHAT v1 OF THIS FUNCTION DID NOT DO, and the
    reason it passed 7/7 anyway:

      * it appended the row and NEVER APPLIED THE EFFECTS, so R19's "the row
        and the effects land together" was true only of the row. No check
        asserted an effect had landed, so nothing failed.
      * it DISCARDED `reason` and `at` — `_append` hard-coded both — so the
        audit trail recorded the harness's defaults rather than the
        operator's words, and the signature lied about what it stored.
      * `plan` defaulted to None while the spec called `plan(standing)`
        unconditionally, so spec and harness disagreed about the one argument
        that produces the work.
      * the BUSY regression exercised a SEPARATE `_retry_operation`, not this
        function, so "the shared operation retries BUSY" was untested.

    `plan` is now REQUIRED and takes the standing set, returning the effect
    list. `_gate` and `_fault` are test hooks (None in every real call);
    `_fault` fires between the row append and the effects, which is the seam
    R19's atomicity claim is actually about.
    """
    deadline = time.monotonic() + busy_deadline_s
    while True:
        try:
            # EXPLICIT. Not `with conn:` — that begins nothing (R3-1).
            conn.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.01)
            continue                      # contention: re-acquire, RE-READ
        try:
            seq = _next_seq(conn, user)
            standing = _standing(conn, user)
            if _gate is not None:
                _gate.wait()
            effects = list(plan(standing))
            _append(conn, user, digest, action, seq, reason, at)
            if _fault is not None:
                _fault()                  # between the row and the effects
            for e in effects:
                _apply_effect(conn, user, e)
            conn.execute("COMMIT")
            return seq, frozenset(standing), effects
        except sqlite3.IntegrityError as e:
            # R5-1: WHICH constraint fired decides which invariant reports.
            # Only the per-user ordinal is a serialisation failure.
            ordinal = _is_ordinal_violation(e)
            _rollback_or_poison(conn, e)
            if ordinal:
                raise OrdinalCollision(str(e)) from e
            raise RevocationIntegrityError(str(e)) from e
        except BaseException as e:
            # the row, the effects, all of it — and if that cannot be
            # established, say so rather than pretending (R5-1)
            _rollback_or_poison(conn, e)
            raise
```
<!-- /GENERATED:r19-operation -->

**THE BLOCK ABOVE IS GENERATED FROM THE EXECUTABLE, byte for byte** (`specs/render_operation.py`, gated by `--check`). Round 5 found the spec claiming "quoted verbatim" while the two differed, and v6 withdrew the claim; v7 makes it TRUE instead and **deletes the withdrawal, which had become the stale carrier (external round 6, R6-2)** — the paragraph said the executable "differs materially" on the same page as a block generated from it, and COLLECTED said the opposite again. Three carriers, two answers. `_gate` and `_fault` are test hooks, `None` in every non-test call; they appear because they appear in the code, and hiding them would reintroduce the divergence.

**THE FAILURE OUTCOMES ARE TOTAL (R5-1), and v5's were not.** v5 suppressed a
failing `ROLLBACK` and re-raised the original error, so a caller could be told
its work was undone while holding a live transaction and an uncommitted row;
and it converted EVERY `sqlite3.IntegrityError` — append, effects, or commit —
into `OrdinalCollision`, so a trigger on the records table reported a
serialisation failure that had not happened. Three outcomes now, and they are
distinct: `OrdinalCollision` ONLY for the per-user ordinal (matched on the
constraint's own columns), `RevocationIntegrityError` for any other integrity
fault, and `RevocationUnknownState` when the rollback itself fails — which
also CLOSES the connection, because a connection whose transaction state
cannot be established must not be reused.

**AND ONE THING THE EVIDENCE ESTABLISHED THAT THE SPEC DID NOT EXPECT.**
R5-2 asked for a stale ordinal injected inside the shared operation. It cannot
be done: while the operation holds the write lock from `BEGIN IMMEDIATE`, no
other connection can COMMIT, so nothing can steal the ordinal between the read
and the append — the attempt gets `database is locked`. **`OrdinalCollision`
is therefore unreachable from inside this construction**; it is a backstop for
callers who allocate outside the transaction (the allocate-then-write shape).
That is the serialisation working, it is now a check in its own right, and the
classifier is covered directly on real errors rather than through a branch the
design makes dead.

**v4 of this function did three things this one does not, and the harness
scored 7/7 on it anyway (external round 4, R4-1).** It appended the row and
**never applied the effects**, so R19's "the row and the effects land
together" was true of the row alone. It **discarded `reason` and `at`** —
the append hard-coded both — so the audit trail recorded defaults instead of
the operator's words while the signature claimed otherwise. And `plan`
defaulted to `None` here while the spec called `plan(standing)`
unconditionally, so the two disagreed about the one argument that produces
the work. **Every earlier check asked about ordinals and rows; none asked
whether the work happened**, which is the whole reason an empty operation
passed. Six checks now cover it, and reverting the function to v4's
behaviour fails two of them.

**Where the BUSY handling lives is itself the contract.** It is INSIDE the
operation, bounded by a deadline, and it retries only lock acquisition —
after which the read happens again. v3 said "no CAS/retry loop is specified"
while R19 called BUSY retryable, and the v1 harness put a retry loop OUTSIDE
the operation; all three could not be true at once. The rule is: **retrying
the ACQUISITION is required and bounded; retrying around an unserialised
read is forbidden; an `OrdinalCollision` is never retried at all**, because
it reports that serialisation failed and a retry would hide it.

**`BEGIN IMMEDIATE` before the read is the whole fix.** SQLite's deferred
transaction takes the write lock at the first WRITE, so the read that
allocates `seq` happens outside it and two writers can allocate the same
ordinal. Taking the lock up front makes allocate-plan-append one serialised
unit: the second host blocks, then reads a ledger that already contains the
first host's row, and **plans against the standing set that actually
exists** rather than a stale one.

**MEASURED, and SQLite refuses EARLIER and for a sharper reason than the
paragraph above predicted** (`store_concurrency_harness.py`, written for
this round). The reasoning above says two hosts allocate the same ordinal
and one hits the UNIQUE backstop. What actually happens under DEFERRED is
that the second host cannot even reach the backstop: **a transaction that
has already READ holds a SHARED lock, so its first write against another
connection's RESERVED lock returns `SQLITE_BUSY` IMMEDIATELY — the busy
handler is deliberately NOT invoked, because waiting would deadlock.** The
loser cannot wait its turn. That is a stronger argument for the
construction than the one the spec reasoned to, and it was only available by
executing it.

The duplicate-ordinal collision is real too, but it needs the read to happen
OUTSIDE the write transaction — the allocate-then-write shape a host writes
when the read is "just a SELECT". Both cells are in the harness.

- **The unique constraint stays**, as a backstop that must never fire. If it
  ever does, that is a construction defect, not a race to retry around —
  `SQLITE_BUSY` on lock acquisition is the ordinary, retryable outcome, and
  the two must not be conflated. **The harness proves they are
  distinguishable in practice**: the collision surfaces as `IntegrityError`
  from the INSERT itself, so a retry loop written around
  `OperationalError` never sees it — which is the separation this rule
  needs and could otherwise only assert.
- **No retry around an UNSERIALISED READ**, ever: that is how you get two
  operations each believing they saw the final state. Serialise first, and
  the only retry left is on acquiring the lock — which is bounded and lives
  inside the operation above (R3-1).
- **The loser is not re-derived, because there is no loser** — there is a
  second operation that runs afterwards, against post-first state. A second
  revoke of an already-standing source is idempotent in effect (**R16**); a
  lift following a revoke lifts what the revoke did. Both are ordinary
  sequences, which is the point of serialising rather than arbitrating.
- **Non-SQLite stores** must provide the same guarantee — allocate, plan and
  append inside one serialised write — and **R19** states it as the contract
  rather than as SQLite trivia.

**Evidence (R19):** `specs/evidence/0022/store_concurrency_harness.py` —
seven checks against real `sqlite3` connections on a real file, exit 0,
recorded in `store_concurrency_result.txt`. It opens by proving THE DEFECT
STILL REPRODUCES under the natural construction, so a race that quietly
stopped racing would fail the build rather than silently retire every
protection below it.

**Evidence (R19), 17 checks, exit 0** — `store_concurrency_harness.py`. Six of them are R4-1's: **effects land** in the same commit; **a fault between the row and the effects rolls BOTH back**; **an effect naming an absent record rolls the row back too**; **the operator's reason and timestamp are stored, not defaulted**; **a forced lock conflict retries THROUGH this function** (not a separate helper, which is what v4's BUSY regression actually exercised); and **a collision is raised, never retried**.

**Adversarial tests (R19):** two overlapping revocations of DIFFERENT
sources interleaved; two revocations of the SAME source; revoke racing lift
on one source; and a forced `SQLITE_BUSY` proving it is retryable while a
unique-ordinal violation is not.

A preview that can diverge from its commit is the classic defect in this
shape of feature — it is the reason operators stop trusting previews, and
it fails silently, because the two paths agree on every example anyone
thinks to test. **R6** carries the invariant AND its executable check:
feed one store, run the preview, run the commit, and assert the two
statements are equal — including that the preview left the store
byte-identical, and that the planner is a pure function of its inputs
(the harness re-plans and compares).

### 4f. Reversal — DESIRED STATE, recomputed; never an undo log

`unrevoke_source(user_id, origin, source_id, reason)` appends a lifting
row. Reversibility is a threat-model requirement (C2), not a courtesy.

**The reversal is not an undo log replayed backwards. It is the SAME
computation over the new standing set**, and that is the only construction
that gets the overlapping case right: a record condemned by TWO revoked
sources must stay retired when one of them is lifted. An effect log
replayed backwards reinstates it. The desired-state form has that cell
right by construction, and it is a pinned vector.

Concretely:

- **NARROWED AT v3 (external round 1, F3), and the narrowing is a
  withdrawal, not a rewording.** v2 said retirements "REVERSE BY
  AN IN-PLACE STATE CHANGE recomputed from the standing set, never by
  deleting the record and never by a retirement event the store does not
  have". **The product has no such event.** The
  reviewer put the contradiction precisely: the normative reference
  overwrites a record under the same id and appends the former value to an
  abstract `history` list for which no product carrier exists, while
  `_invalidate_edge_row` (`sqlite.py:251`) explicitly UPDATEs the existing
  edge row and this spec's own §4b-ii adds mutable `active`/`retired_reason`
  fields to the existing episode JSON. **Three carriers, one claim, and the
  claim was true of none of them.**

  **What v3 claims instead, which is what the store actually does:**
  retirement is an **in-place, reversible STATE CHANGE** on the record —
  `active`/`retired_reason` for both record types — and the **append-only
  carrier is `source_revocations`**, the standing-state ledger. The event
  log is the ledger; record state is DERIVED from it and is never a second
  source of truth. That is a real property and it is the one that makes
  reversal work: **because state is a function of the standing set, revoke
  and lift are the same computation** (below), and no undo log exists to
  replay wrongly.

  **WITHDRAWN NAME, quoted to retract it: `supersede-never-erase` (C3)
  survives in the sense that carries the
  guarantee** — nothing is deleted, content is retained and re-derivable,
  `forget()` remains the only erasure surface — and **is withdrawn in the
  sense that overreached**: this spec does not introduce retirement events,
  ids, links or read-time resolution, and no longer implies it does. The
  effect vocabulary is still CLOSED to `{retire, recompute, reinstate}` with
  no erasing verb, and a vector still asserts the vocabulary.

  **A general retirement-event carrier is a real design and it is not this
  spec's** — see §10 **Q9**, which records it as a successor rather than
  letting the narrowing become permanent by default.
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
| **R7** the completeness statement reports all three class counts, **counts retired-synthesized separately from retired-sole-basis**, and is `complete=False` whenever the class-(b) or class-(c) population is non-empty. **Class (c) is UNATTRIBUTED AND UNREACHED — every record with no contribution rows that this sweep did not already find, WHATEVER ITS AUTHORSHIP (external round 1, F4)** | `test_completeness_statement_is_honest` + `test_retired_synthesized_counted_separately` + **`test_user_authored_unattributed_is_counted`** — a pre-`0014` absorption survivor that kept the INCOMING record's user authorship while carrying transferred values no ledger row names. The vector BITES: under the v2 predicate it counted 1, under v3 it counts 5 |
| **R8** consumption closure is TRANSITIVE and the property RECURSES (a condemned contributor is not corroboration one hop up); a self-naming row REFUSES instead of looping; the fixpoint terminates | `test_closure_is_transitive_and_recursive` |
| **R9** **retain-never-erase**: after any revoke/lift sequence **every record is still present** (none deleted, none created), **the `source_revocations` table only grew** (no row updated or removed), and no effect verb outside `{retire, recompute, reinstate}` exists. **v3 (external round 2, F1) — WITHDRAWN wording, quoted to retract it: v2 said "history only grew", which asserted a generic record-value history the store does not have, so an implementation could not satisfy R9 and §4f at once** | `test_revocation_retains_every_record` + `test_source_revocations_is_append_only` + `test_effect_verbs_are_closed` |
| **R10** a lift is DESIRED STATE, not undo: it reinstates only what `revoked_source` retired, restores recomputed values by recomputation, and leaves a record retired while a SECOND revocation still reaches it | `test_lift_is_desired_state_not_undo` |
| **R11** the shipped surface agrees with the normative reference on every pinned vector, through the SHIPPED harness | `test_revocation_reference_vectors` — today: `.venv/bin/python specs/evidence/0022/vector_harness.py`, whose recorded result ships as `vector_harness_result.txt` (the one carrier for the count) |
| **R12** a source with no `source_id` has no digest, no join and no reach: it cannot be revoked and cannot be reached by any revocation | `test_unknown_source_is_not_revocable` |
| **R13** revocation is PER USER: a revocation for one user changes nothing observable for another, including the standing state consulted at write time | `test_revocation_does_not_cross_the_user_boundary` |
| **R14** the surface is host-API only — absent from the CLI parser table and from the MCP tool registry | `test_revocation_is_not_exposed_on_the_agent_surfaces` (the §2c-ii commands, as a test) |
| **R15** a `revoked_source` retirement drops the compiled wiki, and `revoked_source` is registered in 0004's `DISPOSITIONED_REASONS` so its totality check passes | `test_revocation_drops_the_wiki` + 0004's own `test_invalidation_reason_registry_is_total` |
| **R16** the sweep is idempotent: a second revoke of a standing source appends its row and plans no further effect | `test_second_revoke_is_a_no_op` |
| **R17** every retirement the sweep performs routes through `_invalidate_edge_row`, the SOLE writer of `active=0` — no bulk update path exists, so the wiki drop is inherited by construction (§4b) | 0004's own `test_sole_active_zero_writer` (the AST sweep — a second writer FAILS the build) + `test_the_sweep_retires_through_the_sole_writer` |
| **R18** the sweep's record DOMAIN is the enumerated one (§4b-i), and EPISODES are retired by it — through ONE writer, with `store.episodes()` default-excluding retired rows so all nine readers inherit the exclusion (internal S1; v1 had no mechanism for this type at all) | `test_revocation_retires_episodes` (a revoked source's episode text must not appear in `recall()`'s rendered context — the assertion at the RENDER surface, not at the store) · `test_episode_read_seam_is_sole_path` — an AST sweep asserting every `FROM episodes` outside the dispositioned §7a list routes through `store.episodes()`, which is what stands in for the SQL-level guarantee a column would have given · `test_retired_episode_round_trips` (export/import preserve retired state rather than resurrecting it). **The VECTOR side of R18 is ALREADY SATISFIED and was before the finding: 18 of the 54 vectors carry episode-typed records, and the reference retires them with `revoked_source` exactly as it retires edges** (executed, §2c-ii) — which is precisely why S1 is a class-G finding. The evidence proved the DESIGN over both types while the product had a mechanism for only one |
| **R19** allocate-plan-append is ONE SERIALISED WRITE: the ordinal is allocated, the standing set read, the sweep planned, the row appended and the effects applied inside a single write transaction taken BEFORE the first read (`BEGIN IMMEDIATE` on SQLite). The unique ordinal is a backstop that must never fire; lock contention (`SQLITE_BUSY`) is retryable and an ordinal collision is NOT — they are different outcomes and must not be conflated (external round 2, F3) | `test_two_hosts_cannot_allocate_one_ordinal` (two overlapping revocations of different sources · two of the SAME source · revoke racing lift) + `test_busy_is_retryable_and_collision_is_not` — **adversarial interleaving, driven from two real connections, not simulated** |

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
  state reverses by appending a lifting row; **the retired records return
  by RECOMPUTATION of their desired state from the new standing set — an
  in-place update, not a supersession** (§4f, narrowed at external round 1);
  the recomputed values return by the same recomputation over the restored
  evidence. Nothing is deleted, so nothing needs restoring from
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
2. **The class-(c) upper bound — YOUR ROUND-1 F4, and this brief is what
   invited it.** (WITHDRAWN predicate, quoted to retract it.) v2 counted
   only system-authored unattributed records and
   said here that we were "not certain it cannot UNDER-count: a
   derivation-shaped record that is not system-authored would escape it."
   It did escape it, you executed exactly that case, and the predicate is
   now **every unattributed AND unreached record, any authorship**.
   **What we would still like attacked:** the new predicate over-counts
   heavily — an ordinary user fact that never combined with anything is
   counted — so the number is a bound, not an estimate, and its magnitude is
   a statement about linkage coverage rather than about revocation. If you
   think a bound that loose is useless to an operator, that is a finding we
   would take seriously.
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
| **Q6** | should a revocation's completeness statement be DURABLE (queryable later) rather than only returned? | `resolved` — **audit-event-only, APPROVED by Quentin 2026-08-20 at implementation start.** The audit event carries the counts; storing the full statement would make "what did that revocation reach" answerable months later, at the cost of a second carrier for a value the sweep can always recompute. **Leaning: audit event only — but the v1 REASON was wrong and is corrected (internal M1).** "The sweep is a pure function and can be re-run" is false across time: the function is pure over inputs that MUTATE, so a re-run months later answers *what the store looks like now*, not *what that revocation reached then*. Recomputation reproduces only the present. The leaning survives on the honest ground: **the audit event IS the durable record**, and a second stored copy of a statement the audit already carries is a second carrier to keep consistent (§3b's rule against exactly that) |
| **Q7** | should `revoke_source` accept a digest directly, for a source whose pair the operator no longer has? | `deferred` — research + dev. It would let an operator act on a digest read from `introspect` without knowing the pair, but it also lets an operator revoke something they cannot name. Not needed for v1 |
| **Q8** | should the episode retirement field (§4b-ii) be PROMOTED to an `active` COLUMN on the `episodes` table at the next schema window? | `post-v1` — recorded rather than deferred silently, because the v1 choice has a stated ceiling. **Decided for v1 (Quentin, 2026-08-17): JSON field + the `store.episodes()` read seam, no DDL** — it ships without a migration and gives every reader structural inheritance, which is the property that matters most. **The ceiling it accepts:** the guarantee is Python-level, so a future raw-SQL reader could bypass the seam where a column would let SQL filter too. **R18**'s AST sweep is what stands there, and the fourteen raw sites are all inside the store package (§2c-ii), so the check is closed rather than hopeful. Promote when a schema window opens for another reason — never open one for this alone |
| **Q9** | should the product gain a GENERAL retirement/reinstatement EVENT carrier — ids, links, provenance and read-time resolution — for edges AND episodes? | `successor spec` — **opened by external round 1's F3, and recorded here precisely because the stated risk of narrowing is that the successor never gets scheduled and the narrowing becomes permanent by default.** v3 narrows C3 to reversible in-place state over the append-only `source_revocations` ledger, which is what the shipped store does. A real event carrier would let retirement be a first-class, queryable history for both record types — and it collides with `0004`'s **W7** (sole `active=0` writer), this spec's **R17**, and the export FORMAT, so it needs its own round and its own schema window. **Not deferred silently: it is on the dev queue naming the ACT** |
| **Q10** | should EVERY adversarial cell in a §2c table be required to carry a vector or an executed check? | `process` — raised by F2, which lived in the gap between §2c (prose claims) and §2c-ii (executed commands). The template asks for the adversarial column and separately asks for executed reach assertions, and never connects them. This is a PROCESS question above any one spec, so it belongs in `PROCESS.md` and the reviewer guide rather than here — recorded so the finding's generalisable half is not lost with the round |

## Review closure

*(PROCESS §4a — one row per review finding, with evidence that is openable
or executable. *The round-by-round ledger below is GENERATED from `specs/reviews.py` (external round 4, R4-3 — it had drifted three rounds running as a hand-maintained twin: a round count that disagreed with its own rows, a placeholder claiming it had been removed, and two tables with different column counts in one document). Regenerate with `python3 specs/render_closure.py --write`; `--check` fails the build when it drifts.*

<!-- GENERATED:review-closure -->

**4 internal round(s) and 20 external round(s) with a returned VERDICT are recorded for `0022`; 21 package(s) were dispatched** — counted from `specs/reviews.py`, which is the source this block is generated from. A round appearing here and not there, or the reverse, is impossible by construction. **SENT rows are dispatch records, not outcomes**, and are labelled below so the two are never summed.

| round | date | findings raised (from `raised=`) | verdict (compressed) |
|---|---|---|---|
| internal 1 (verdict) | 2026-08-17 | 3 | RETURN FOR AMENDMENT (1 blocking + 1 required strengthening + 4 minors, across the coupled pair; the drafts called 'exceptional — the findings are completion, not correction'). S1 (BLOCKING, 0022): the sweep's RECORD DOMAIN was unenumerated — "records" meant EDGES. Executed: __init__.py:869-872 rend… |
| internal 14 (verdict) | 2026-08-18 | 1 | ⚠️ COUNTS CORRECTED BY R15-2 (2026-08-19) — the classification below was HAND-WRITTEN and its numbers were wrong: the six headings summed to 30, not 39, so NINE findings were never classified, and 'five of six re-found' was asserted rather than derived. It is now structured in specs/review_lessons.p… |
| internal 15 (verdict) | 2026-08-19 | 1 | SELF-FOUND BY CI, and only after FIVE RED RUNS — the seals for rounds 12, 13, 14 and 15 all went out with the suite failing on GitHub, because I pushed and did not look. Quentin saw it before I did. THE DEFECT: `test_the_evidence_transcript_validates_against_the_ledger` read the live transcript that… |
| internal 21 (verdict) | 2026-08-20 | 1 | SELF-FOUND — not raised by the reviewer, caught by CI on the first push of the seal-cost work. Making the evidence runner concurrent (59 commands, 4 workers, 147s serial -> 39s) exposed a latent CLASS-5 defect that serial execution had been hiding: test_the_whole_lessons_summary_is_byte_verified_by_… |
| external 1 (verdict) | 2026-08-17 | 3 | RETURN FOR AMENDMENT (three blocking findings on this spec). F2 — the standing state ordered by (at, seq) while `at` is HOST-SUPPLIED, so a planted far-future timestamp made a revocation PERMANENTLY UNLIFTABLE (executed: revoke at 2099 seq 0, lift at 2026 seq 1, the lift never takes). The instructiv… |
| external 1 (SENT) | 2026-08-17 | — | SENT (the coupled round-1 package `0004-0022-0023-v1` — ONE archive, three specs, per-spec verdicts requested; sealed AFTER this row, sha pinned on return). 0022 at v2: source revocation — the standing state and the sweep. THE LEAD SPEC. Carries the enumerated record domain (§4b-i) and the episode r… |
| external 2 (SENT) | 2026-08-17 | — | SENT (the coupled round-2 package `0004-0022-0023-v2`). 0022 at v3: THREE blocking findings folded. F2 — ordering by (at, seq) with a HOST-SUPPLIED `at` made a revocation permanently unliftable (executed: revoke at 2099 seq 0, lift at 2026 seq 1, the lift never takes); now `seq` ALONE with five cloc… |
| external 3 (verdict) | 2026-08-17 | 2 | RETURN FOR AMENDMENT (2 blocking on this spec + 2 package/process; 0004 NOT reviewed, its round-2 approval stands frozen). R3-1 — §4e-i printed `with conn:` and LABELLED it BEGIN IMMEDIATE. Python's sqlite3 context manager begins nothing; probed on the shipped config, isolation_level=='' and in_tran… |
| external 3 (verdict) | 2026-08-17 | 2 | RETURN — PACKAGE/PROCESS half (R3-4, R3-5). R3-4 — both closure sections said 'THREE ROUNDS' while enumerating four, claimed rows were below, and still carried `no review rounds yet (draft)`; 0023 had no rows at all. R3-5 — COLLECTED did not reconcile: the measured line said 1651/6 while its own dec… |
| external 3 (SENT) | 2026-08-17 | — | SENT (the coupled round-3 package `0022-0023-v3` — 0004 is NOT in it: it was APPROVED FOR ACCEPTANCE at round 2, frozen on W1-W8, and re-sending an approved spec invites re-litigation. Per-spec verdicts requested; sealed AFTER this row, staged to the outbox, sha pinned on return). 0022 at v4: F1 — r… |
| external 4 (verdict) | 2026-08-17 | 3 | RETURN FOR AMENDMENT (1 blocking on this spec + 2 package/process; 0004 not reopened). R4-1 — `revocation_operation` was NEITHER ATOMIC NOR ACTUALLY SHARED. The reviewer invoked the submitted function directly and got `applied effects: []`: it appended the row and never applied the effects, so R19's… |
| external 4 (SENT) | 2026-08-17 | — | SENT (the coupled round-4 package `0022-0023-v4`; 0004 remains OUT — approved and frozen at round 2). 0022 at v5: R3-1 folded with ONE shared `revocation_operation` quoted verbatim in §4e-i and CALLED by the harness (the spec printed `with conn:` while the harness executed BEGIN IMMEDIATE — the evid… |
| external 5 (verdict) | 2026-08-17 | 4 | RETURN FOR AMENDMENT (2 blocking on this spec + 2 package/process; 0023 semantically clear, deferred only by the mutual requires; 0004 not reopened). R5-1 — the failure outcomes were NOT TOTAL: a failing ROLLBACK was suppressed and the ORIGINAL error re-raised, so the caller held a live transaction … |
| external 5 (SENT) | 2026-08-17 | — | SENT (the coupled round-5 package `0022-0023-v5`; 0004 remains OUT — approved, frozen). 0022 at v6: R4-1 folded — the shared operation now APPLIES EVERY EFFECT in the same transaction, stores the operator's reason and timestamp, requires `plan`, and rolls the row back with the effects on any fault; … |
| external 6 (verdict) | 2026-08-17 | 4 | RETURN FOR AMENDMENT (2 blocking on this spec + 2 package/process; 0023 semantically clear but deferred by its incomplete ledger and the atomic dependency; 0004 not reopened). R6-4 — THE OFFLINE LAUNCHER CERTIFIED AN UNQUALIFIED RUNTIME. It invented its own rule (SQLite >= 3.35) while the repository… |
| external 6 (SENT) | 2026-08-17 | — | SENT (the coupled round-6 package `0022-0023-v6`; 0004 remains OUT — approved and frozen at round 2, and named as such in both carriers rather than quietly included). 0022 at v7: all four round-5 findings folded. R5-1 the failure outcomes are total (unknown-state rollback closes the connection; only… |
| external 7 (verdict) | 2026-08-18 | 2 | RETURN FOR AMENDMENT — PROCESS/PACKAGE ONLY; NO NEW SEMANTIC DEFECT IN EITHER SPEC. R7-1 — closure validation was not per-finding validation: it compared SETS OF IDS, so changing a round to 99, erasing a finding's evidence, adding an extra row and duplicating one all reported no problem; `0022 R99-1… |
| external 7 (SENT) | 2026-08-17 | — | SENT (the coupled round-7 package `0022-0023-v7`; 0004 remains OUT — approved and frozen; PRIOR EXTERNAL REPORTS ARE NOT INCLUDED, per the reviewer's explicit instruction, with the structured closure ledger as the agreed replacement). 0022 at v8: R6-1 the rollback boundary is BaseException on both s… |
| external 8 (verdict) | 2026-08-18 | 2 | RETURN FOR AMENDMENT — PROCESS/PACKAGE ONLY; both specs remain semantically clear. R8-1 — the structured closure had an ADMISSION HOLE: `raised` was read with .get(..., []), so OMITTING the field was indistinguishable from declaring no findings. A returned verdict naming R99-1 with no `raised` produ… |
| external 8 (SENT) | 2026-08-18 | — | SENT (the coupled round-8 package `0022-0023-v8`; 0004 out, approved and frozen; prior reports omitted as instructed). 0022 at v9: R7-1 structural finding identities with exact (spec, kind, round, id) validation, derived counts, and every evidence command executed by a shipped test; R7-2 the launche… |
| external 9 (verdict) | 2026-08-18 | 1 | RETURN FOR AMENDMENT — PACKAGE/PROCESS ONLY; no new semantic defect in either spec. R9-1 — EXTRACTED-ARCHIVE VERIFICATION WAS OVERSTATED. Both carriers claimed the sealer reran 'both harnesses and both verifiers from the EXTRACTED archive'; verify_archive() ran the two harnesses and nothing else, th… |
| external 9 (SENT) | 2026-08-18 | — | SENT (the coupled round-9 package `0022-0023-v9`; 0004 out, approved and frozen; prior reports omitted). 0022 at v10: R8-1 explicit `raised` declarations with omission raising and the count derived; R8-2 the harness results, the evidence split and the launcher line all MEASURED by the sealer, and th… |
| external 10 (verdict) | 2026-08-18 | 3 | RETURN FOR AMENDMENT — PACKAGE/PROCESS ONLY; no new semantic defect. R10-1 — THE REVIEWER GUIDE CONTRADICTED THE MEASURED WORKFLOW: it said measurement happens in a separate extracted git archive with no .git, so the measured line already reflected the reviewer's shape; seal_package.measure() runs w… |
| external 10 (SENT) | 2026-08-18 | — | SENT (the coupled round-10 package `0022-0023-v10`; 0004 out, approved and frozen; prior reports omitted). 0022 at v11: R9-1 folded by making the extraction run all six checks from a registry the carrier is generated from |
| external 11 (verdict) | 2026-08-18 | 2 | RETURN FOR AMENDMENT — PACKAGE/PROCESS ONLY; both specs semantically clear. R11-1 — the verifier binding was still TEXTUAL: the regression required only that the inline program CONTAIN the strings `verify_collected` and `COLLECTED`, so `python -c "pass # verify_collected COLLECTED"` with the origina… |
| external 11 (SENT) | 2026-08-18 | — | SENT (the coupled round-11 package `0022-0023-v11`; 0004 out, approved and frozen; prior reports omitted). 0022 at v12: R10-1 one canonical measurement protocol with generated context and the guard extended to the guide; R10-2 the registry pinned to argv with the no-op substitution rejected; R10-3 u… |
| external 12 (verdict) | 2026-08-18 | 2 | RETURN FOR AMENDMENT — PACKAGE/PROCESS ONLY; both specs semantically clear. R12-1 — THE SHIPPED TRANSCRIPT WAS MISPLACED AND UNVERIFIED: COLLECTED named `specs/generated/evidence_run.json` while the sealer appended it at the archive ROOT, and verify_archive() never looked at it — the reviewer REMOVE… |
| external 12 (SENT) | 2026-08-18 | — | SENT (the coupled round-12 package `0022-0023-v12`; 0004 out, approved and frozen; prior reports omitted). 0022 at v13: R11-1 named verifier scripts with full argv pinning and a corrupt-the-carrier mutation; R11-2 an allowlisted sealing environment with the evidence claim observed rather than counte… |
| external 13 (verdict) | 2026-08-18 | 3 | RETURN FOR AMENDMENT — PACKAGE/PROCESS ONLY; both specs semantically clear and byte-identical to v12. R13-1 — TRANSCRIPT FIELD VALUES WERE NOT VALIDATED, only presence and length. A counterfeit carrying all 42 ledger rows with cwd null, exit false and a 64-character non-hex digest passed validate() … |
| external 13 (SENT) | 2026-08-18 | — | SENT (the coupled round-13 package `0022-0023-v13`; 0004 out, approved and frozen; prior reports omitted). 0022 at v14: R12-1 the transcript ships at the path COLLECTED names and is verified FROM THE EXTRACTION; R12-2 one shared validator derives the count from the records and matches them to the cl… |
| external 14 (verdict) | 2026-08-18 | 1 | RETURN FOR AMENDMENT — PACKAGE/PROCESS ONLY; both specs semantically clear and byte-identical to v13. R14-1 — THE TRANSCRIPT SCHEMA STILL COERCED UNTYPED VALUES. Round 13 typed three fields; three MORE cells were coercible and the reviewer applied all of them at once, repacking an archive verify_arc… |
| external 14 (SENT) | 2026-08-18 | — | SENT (the coupled round-14 package `0022-0023-v14`; 0004 out, approved and frozen; prior reports omitted). 0022 at v15: R13-1 typed field validation with the exact counterfeit as a regression; R13-2 the hand-maintained cardinal removed; R13-3 stale selectors repointed and every -k atom gated to sele… |
| external 15 (verdict) | 2026-08-19 | 2 | RETURN FOR AMENDMENT — PACKAGE/PROCESS ONLY; both specs semantically clear and byte-identical to v14. R15-1 — THE CLOSED SCHEMA WAS CLOSED ONE LEVEL DOWN ONLY. Round 14 declared every command field and refused undeclared ones; the OBJECT HOLDING THE COMMANDS refused nothing, so `{'undeclared_top_lev… |
| external 15 (SENT) | 2026-08-18 | — | SENT (the coupled round-15 package `0022-0023-v15`; 0004 out, approved and frozen; prior reports omitted). 0022 at v16: R14-1 folded with a closed, exactly-typed transcript schema and six mutations plus a clean control |
| external 16 (verdict) | 2026-08-19 | 2 | RETURN FOR AMENDMENT — PACKAGE/PROCESS ONLY; both specs semantically clear and byte-identical to v15 before their closure sections, and both v15 findings confirmed closed. R16-1 — PACKAGE IDENTITY WAS HAND-MAINTAINED AND STALE. The archive was named v16 while COLLECTED.txt line 1 said `round-15 ... … |
| external 16 (SENT) | 2026-08-19 | — | SENT (the coupled round-16 package `0022-0023-v16`; 0004 out, approved and frozen; prior reports omitted). 0022 at v17: R15-1 the transcript schema is closed at EVERY level, with the mutation matrix DERIVED from the schema so a field or level added later cannot go untested; R15-2 the lessons taxonom… |
| external 17 (verdict) | 2026-08-19 | 2 | RETURN FOR AMENDMENT — PACKAGE/PROCESS ONLY; both specs semantically clear and byte-identical to v16 before their closure sections. R17-1 — THE IDENTITY FIX'S OWN CARRIER DOMAIN WAS INCOMPLETE. Round 16 made the package version produced rather than typed and enumerated THREE carriers of it; there we… |
| external 17 (SENT) | 2026-08-19 | — | SENT (the coupled round-17 package `0022-0023-v17`; 0004 out, approved and frozen; prior reports omitted). 0022 at v18: R16-1 the package identity is SUBSTITUTED from the requested version, the round derived from it, both cross-checked against this row, and any disagreement among the three identity … |
| external 18 (verdict) | 2026-08-19 | 2 | RETURN FOR AMENDMENT — PACKAGE/PROCESS ONLY; both specs semantically clear and byte-identical to v17 before their closure sections. R18-1 — THE STRUCTURED RECORD WAS NOT TOTAL OVER ITS CLAIMED DOMAIN, three ways, and the reviewer executed all three. (a) The candidate revisions are ALSO stated in SEN… |
| external 18 (SENT) | 2026-08-19 | — | SENT (the coupled round-18 package `0022-0023-v18`; 0004 out, approved and frozen; prior reports omitted). 0022 at v19: R17-1 the package identity is a STRUCTURED RECORD (specs/package_identity.py) — version, round and each spec's candidate revision — that every identity carrier is filled from and c… |
| external 19 (verdict) | 2026-08-20 | 2 | RETURN FOR AMENDMENT — PACKAGE/PROCESS ONLY; both specs semantically clear and byte-identical to v18 before their closure sections. BOTH FINDINGS ARE PARTIAL-FIX ESCAPES: each names the half of a carrier my previous fix did not look at. R19-1 — PARSING FIELDS OUT OF A CARRIER IS NOT CHECKING THE CAR… |
| external 19 (SENT) | 2026-08-19 | — | SENT (the coupled round-19 package `0022-0023-v19`; 0004 out, approved and frozen; prior reports omitted). 0022 at v20: R18-1 the identity record is total over its domain — contiguous governed run, prose claims cross-checked against the record, duplicate carriers counted rather than collapsed; R18-2… |
| external 20 (verdict) | 2026-08-20 | 1 | RETURN FOR AMENDMENT — PACKAGE/PROCESS ONLY; both specs semantically clear, normative bodies unchanged from v19, and the exact R19-1/R19-2 attacks confirmed closed. R20-1 — CANDIDATE IDENTITY WAS NOT BOUND TO THE CARRIER THAT STATES IT. R19-1 stopped the check comparing extracted fields and made it … |
| external 20 (SENT) | 2026-08-20 | — | SENT (the coupled round-20 package `0022-0023-v20`; 0004 out, approved and frozen; prior reports omitted). 0022 at v21: R19-1 the candidate block is compared as a rendered artifact and every declared path must be an archive member; R19-2 generated blocks carry an explicit boundary policy and the les… |
| external 21 (verdict) | 2026-08-20 | 0 | 🏁 ACCEPTED on the frozen invariant surface R1–R19 — ATOMIC with 0023 (N1–N15), and with prerequisite 0004 moved draft→accepted in this same commit per the reviewer's instruction ('acceptance is atomic: both specifications must transition together, with prerequisite 0004 also moved'). NO new semantic… |
| external 21 (SENT) | 2026-08-20 | — | SENT (the coupled round-21 package `0022-0023-v21`; 0004 out, approved and frozen; prior reports omitted). 0022 at v22: R20-1 the `specs:` field is rendered whole from the identity record and verified as one anchored artifact — exactly one field, in the header, byte-identical — with a pure-function … |

**Per-finding closure ledger — PROCESS §4a.** **51 finding(s) for `0022`; 152 across the 5 tracked specs** — every number here is DERIVED from the rows below (external round 7, R7-1: the manifest claimed 26 while the ledgers held 31, and 0023 said 9/9 above a 10-row table). Generated from `specs/closure_findings.py` and validated against `specs/reviews.py` on `(spec, kind, round, id)` EXACTLY — extras, duplicates, wrong rounds and empty evidence all fail the build.

| finding | round | what it was | closed in | evidence (runnable) |
|---|---|---|---|---|
| **F2** | external 1 | the standing state ordered by (at, seq) with a HOST-SUPPLIED `at`, so a planted far-future timestamp made a revocation permanently unliftable | §4a, R1, reference_revocation.standing_revocations | `$PY specs/evidence/0022/vector_harness.py  # 5 clock-skew vectors: standing_a_far_future_revoke_is_still_liftable, standing_a_clock_rollback_does_not_undo_the_latest_append, standing_identical_timestamps_are_ordered_by_seq_alone, standing_row_order_in_the_list_does_not_decide, standing_the_epoch_timestamp_cannot_resurrect_a_lift` |
| **F3** | external 1 | 'supersession, never edit' was true of no carrier in the product — the reference mutated in place against an abstract history list with no product analogue | §4f, C3, R9, reference_revocation.apply_effects | `$PY specs/lint_withdrawn.py  # rules 0022-retirement-is-a-new-event and 0022-history-only-grew fail the build on any live restatement` |
| **F4** | external 1 | class (c) gated on `system_authored` was not the upper bound it advertised: a pre-0014 absorption survivor keeps the incoming record's USER authorship while carrying transferred values no ledger row names | §4c, §2c, §9, R7 | `$PY specs/evidence/0022/vector_harness.py  # sweep_a_pre_0014_user_authored_absorption_survivor_is_counted — it BITES: 1 under the old predicate, 5 under the new` |
| **R3-1** | external 3 | §4e-i printed `with conn:` and labelled it BEGIN IMMEDIATE; it begins nothing, and the harness was green on a DIFFERENT construction | §4e-i, store_concurrency_harness.revocation_operation | `$PY specs/evidence/0022/store_concurrency_harness.py  # the operation is the one the spec prints` |
| **R3-2** | external 3 | the withdrawn class-(c) authorship condition was still normative in §2c, because the lint pattern matched the forward wording and not the reversed wording the cell used | §2c, withdrawn_phrases.py rule 0022-class-c-is-system-authored | `$PY specs/lint_withdrawn.py` |
| **R4-1** | external 4 | `revocation_operation` was neither atomic nor actually shared: it appended the row and NEVER APPLIED THE EFFECTS, discarded `reason` and `at`, and its BUSY regression exercised a different helper | store_concurrency_harness.revocation_operation, §4e-i | `$PY specs/evidence/0022/store_concurrency_harness.py  # EFFECTS LAND / ATOMIC (mid-effect) / ATOMIC (absent record) / METADATA` |
| **R5-1** | external 5 | the failure outcomes were not total: a failing ROLLBACK was suppressed and re-raised as the original error, and EVERY IntegrityError was converted to OrdinalCollision | store_concurrency_harness: RevocationUnknownState, RevocationIntegrityError, _is_ordinal_violation, _rollback_or_poison | `$PY specs/evidence/0022/store_concurrency_harness.py  # 'a FAILING ROLLBACK is reported as UNKNOWN STATE' and 'a NON-ordinal integrity fault is NOT reported as a collision'` |
| **R5-2** | external 5 | two claimed regressions did not exercise their named branches: the BUSY test measured SQLite's internal wait (one BEGIN, zero caught errors) and the collision test raised OrdinalCollision by hand | store_concurrency_harness: the BUSY, BUSY-DEADLINE, unreachability and classifier checks | `$PY specs/evidence/0022/store_concurrency_harness.py  # BUSY counts the loop's OWN attempts with busy_timeout=0; the collision branch is proven UNREACHABLE through the construction and the classifier is covered on REAL errors` |
| **R4-3** | external 4 | the closure ledgers had drifted for a third round — a count disagreeing with its own rows, a placeholder claiming it had been removed | specs/render_closure.py, both closure sections | `$PY specs/render_closure.py --check` |
| **R4-4** | external 4 | skip_inventory.render()'s category list was hard-coded and dropped future-obligation, so four entries reached the data and never the block | specs/skip_inventory.py render()/reconcile(), tests/test_spec_gate.py | `$PY -m pytest tests/test_spec_gate.py -k 'reconcile or silently_drop or emitted_reason'` |
| **R5-4** | external 5 | reconcile() matched pytest's EMITTED reason against SOURCE-SITE tokens, so a listed skip read as unlisted on a root host only | specs/skip_inventory.py EMITTED, tests/test_spec_gate.py | `$PY -m pytest tests/test_spec_gate.py -k emitted_reason` |
| **R5-3** | external 5 | the generated closure was one row per ROUND with a truncated verdict; PROCESS §4a requires one row per FINDING with openable evidence | specs/closure_findings.py (this file), specs/render_closure.py | `$PY specs/render_closure.py --check` |
| **S1** | internal 1 | the sweep's record DOMAIN was unenumerated — 'records' meant EDGES, while episode text renders into recall context and the episodes table has no retirement column | §4b-i (the enumerated record-type table), §4b-ii, R18 | `grep -n '4b-i' specs/0022-source-revocation.md  # every stored type with its mechanism or its EXECUTED exclusion` |
| **M1** | internal 1 | Q6's rationale was false across time: 'the sweep is a pure function and can be re-run' is pure over inputs that MUTATE, so a re-run answers the present, not what the revocation reached | §10 Q6 | `grep -n 'pure over inputs that MUTATE' specs/0022-source-revocation.md` |
| **M4** | internal 1 | complete=False is the expected steady state on any consolidation-bearing store, and operators had not been told | §8 | `grep -n 'EXPECTED STEADY STATE' specs/0022-source-revocation.md` |
| **R3-4** | external 3 | the closure ledgers said THREE ROUNDS while enumerating four, claimed rows were below, and still carried 'no review rounds yet (draft)' | specs/render_closure.py (the ledger is generated) | `$PY specs/render_closure.py --check` |
| **R3-5** | external 3 | COLLECTED did not reconcile: the decomposition implied 14 skips beside a measured line of 6, and four unconditional skips were invisible to the completeness gate's regex | specs/skip_inventory.py (reconcile + the widened site regex), tests/test_spec_gate.py | `$PY -m pytest tests/test_spec_gate.py -k 'reconcile or conditional_skip or emitted_reason'` |
| **R6-1** | external 6 | the rollback boundary was not total: _rollback_or_poison caught Exception while the operation caught BaseException, so a KeyboardInterrupt during ROLLBACK escaped as itself — connection open, in_transaction, uncommitted row surviving | store_concurrency_harness._rollback_or_poison | `$PY specs/evidence/0022/store_concurrency_harness.py  # 'a BaseException during ROLLBACK is ALSO unknown state, not a leak'` |
| **R6-2** | external 6 | §4e-i's block is generated byte-for-byte from the executable and the page still carried round 5's 'verbatim is withdrawn — the executable differs materially': three carriers, two answers | §4e-i (the withdrawal deleted) | `$PY -m pytest tests/test_spec_gate.py -k 'round5_verbatim' && $PY specs/render_operation.py` |
| **R6-3** | external 6 | the closure ledger was a HAND-MAINTAINED SECOND LIST — the thing render_closure was introduced to eliminate — at 12/17 and 3/9, with --check green because it compared the block to that same list | specs/render_closure.py completeness_problems(), tests/test_spec_gate.py | `$PY specs/render_closure.py --check  # ids EXTRACTED from reviews.py; every one must have a row` |
| **R6-4** | external 6 | the offline launcher invented its own qualification rule and CERTIFIED an unqualified runtime: SQLite 3.53.1 accepted, 660 FAILED / 951 passed / 31 errors, while runtime_supported() returned False | specs/evidence/offline/run_offline.sh | `bash specs/evidence/offline/run_offline.sh  # asks runtime_supported() and exits 2 unless it is exactly True` |
| **R7-1** | external 7 | closure validation compared SETS OF IDS, so a wrong round, an erased evidence string, an extra row and a duplicate row all passed; the cross-spec stripper ate `0022 R99-1`; counts in prose disagreed with the rows (26 claimed, 31 present); and four evidence commands did not run | specs/reviews.py (structural `raised=`), specs/render_closure.py (exact (spec, kind, round, id) validation + derived counts), specs/closure_findings.py ($PY-parameterised evidence), tests/test_spec_gate.py | `$PY specs/render_closure.py --check && $PY -m pytest tests/test_spec_gate.py -k closure_ledger_is_complete` |
| **R7-2** | external 7 | the reproduction carrier described the SQLite-floor launcher a round after the code changed, and repeated the previous round's launcher result against a different test set | specs/package/collected_header.txt, specs/seal_package.py (the sealer runs the launcher on the final tree; since C-plus the complete stdout/stderr + exit status ship as a digested capture and the header line DERIVES from that file) | `grep -q '__LAUNCHER__' specs/package/collected_header.txt && grep -q 'launcher runs on the FINAL tree' specs/seal_package.py && grep -q 'derive_launcher' specs/collected_record.py` |
| **R8-1** | external 8 | the structured closure had an ADMISSION HOLE: `raised` was read with .get(..., []), so omitting the field was indistinguishable from declaring no findings — a verdict naming R99-1 with no `raised` produced zero problems, and the displayed count came from the legacy `findings=` which disagrees with `raised` in four rows | specs/render_closure.py (omission raises; the count is derived), specs/reviews.py (0023 external 7 declares raised=[]; the legacy field documented), tests/test_spec_gate.py | `$PY -m pytest tests/test_spec_gate.py -k 'returned_verdict_must_declare or comes_from_raised'` |
| **R8-2** | external 8 | four package claims were hand-maintained and false: harness 17/17 against an 18/18 executable, 'All 31' evidence commands against a 33-row ledger, a packaged-state claim the sealer's own order contradicts, and a git-checkout blurb describing a workflow that had stopped being true | specs/seal_package.py (harnesses RUN, evidence split derived), specs/package/collected_header.txt (two-phase described), specs/skip_inventory.py (the git-checkout blurb) | `grep -q '__HARNESSES__' specs/package/collected_header.txt && grep -q '__EVIDENCE__' specs/package/collected_header.txt && grep -q 'TWO-PHASE' specs/package/collected_header.txt && ! grep -q 'measuring copy has no .git' specs/skip_inventory.py && ! grep -q 'PACKAGED-STATE' specs/skip_inventory.py && grep -q 'WITHDRAWN_CLAIMS' specs/seal_package.py` |
| **R9-1** | external 9 | both package carriers claimed the sealer reran 'both harnesses and both verifiers from the EXTRACTED archive'; verify_archive() ran the two harnesses only, the verifiers having run before the archive existed against the build tree | specs/seal_package.py EXTRACTION_CHECKS (all six run from the extraction), specs/package/collected_header.txt (__EXTRACTED__ generated from the registry), tests/test_spec_gate.py | `$PY -m pytest tests/test_spec_gate.py -k extraction_check_list` |
| **R10-1** | external 10 | the reviewer guide said measurement happens in a separate extracted archive with no .git, so the measured line already reflected the reviewer's shape; the sealer measures the author's git checkout — and the guide promised command/environment/pytest-version/node-count that COLLECTED did not carry | specs/REVIEWER_GUIDE.md (one canonical protocol), specs/seal_package.py (__CONTEXT__ generated; the guard reads the guide) | `! grep -q 'That copy has no `.git`' specs/REVIEWER_GUIDE.md && grep -q '__CONTEXT__' specs/package/collected_header.txt && grep -q 'REVIEWER_GUIDE.md' specs/seal_package.py` |
| **R10-2** | external 10 | the extraction registry bound LABELS not behaviour: swapping verify_collected's command for `python -c pass` while keeping its label was accepted, and the advertised render_operation `--check` was absent from the executed argv | specs/seal_package.py (argv), specs/render_operation.py (--check is real), tests/test_spec_gate.py (argv pinning + the no-op adversary) | `$PY -m pytest tests/test_spec_gate.py -k 'extraction_check_list or corrupting_the_packaged'` |
| **R10-3** | external 10 | git-archived members were root/root while the appended carriers carried the sealing user's uid/gid, so a plain `tar -xzf` exited 2 and --no-same-owner was needed to open the package | specs/seal_package.py (normalised TarInfo + a plain-tar extraction gate) | `grep -q 'info.uname = info.gname = .root.' specs/seal_package.py && grep -q 'plain .tar -xzf. FAILS' specs/seal_package.py` |
| **R11-1** | external 11 | the verifier binding was textual: the regression only required the inline program to CONTAIN `verify_collected` and `COLLECTED`, so `python -c "pass # verify_collected COLLECTED"` was accepted with the original label | specs/verify_extracted.py (named scripts), specs/seal_package.py (full argv, no inline -c), tests/test_spec_gate.py (argv pinning + a corrupt-the-carrier mutation) | `$PY -m pytest tests/test_spec_gate.py -k 'extraction_check_list or corrupting_the_packaged'` |
| **R11-2** | external 11 | sealing inherited the whole environment, so VERACIUM_EVIDENCE_CHILD=1 turned the evidence runner into a skip while the sealer still generated the all-commands-ran claim from the ledger's length | specs/seal_package.py sealed_env() + the observed evidence claim + refusing probes, tests/test_spec_gate.py | `$PY -m pytest tests/test_spec_gate.py -k sealed_environment && grep -q 'evidence_transcript.validate' specs/seal_package.py` |
| **R12-1** | external 12 | the transcript shipped at the archive root while COLLECTED named specs/generated/evidence_run.json, and verify_archive() never looked at it — removing it entirely still produced a passing archive | specs/seal_package.py (ships at REL_PATH; a seventh extraction check validates it), specs/evidence_transcript.py | `grep -q 'evidence_transcript.REL_PATH' specs/seal_package.py && grep -q 'evidence_transcript.py' specs/seal_package.py && $PY -m pytest tests/test_spec_gate.py -k counterfeit_or_missing` |
| **R12-2** | external 12 | the observed count was self-asserted: `ran` was trusted without requiring records, so a zero-record transcript claiming 40 satisfied the sealer and the regression alike | specs/evidence_transcript.py (count derived from len(commands); records matched to the ledger by (spec, finding, argv)), tests/test_spec_gate.py | `$PY -m pytest tests/test_spec_gate.py -k counterfeit_or_missing` |
| **R13-1** | external 13 | the transcript validator checked field PRESENCE and length, not values: `exit: false` passed because a bool is an int and False == 0, a 64-char non-hex string passed the digest check, and `cwd: null` passed presence — a fully fabricated transcript of every ledger row was accepted | specs/evidence_transcript.py (typed validation), tests/test_spec_gate.py | `$PY -m pytest tests/test_spec_gate.py -k counterfeit_or_missing` |
| **R13-2** | external 13 | COLLECTED listed seven extracted checks and called them 'the SAME six checks', in the sentence explaining that the list must not be maintained twice | specs/package/collected_header.txt (the cardinal removed) | `! grep -q 'SAME six checks' specs/package/collected_header.txt` |
| **R13-3** | external 13 | a closure selector named a test that had been replaced, so the evidence command exercised half its claim and exited 0 — satisfying the every-command-runs gate while covering nothing | specs/closure_findings.py (selectors repointed), tests/test_spec_gate.py (every -k atom must select a test) | `$PY -m pytest tests/test_spec_gate.py -k k_atom_in_the_closure` |
| **R14-1** | external 14 | the transcript schema still coerced untyped values: `ran: 45.0` passed because 45.0 == 45, a 64-digit JSON integer digest survived str() before the hex regex, and a duplicated `skipped` entry vanished into a set — all three applied at once produced an archive the verifier accepted | specs/evidence_transcript.py (a CLOSED schema with exact JSON types), tests/test_spec_gate.py (six mutations + a clean-transcript control) | `$PY -m pytest tests/test_spec_gate.py -k counterfeit_or_missing` |
| **R14-2** | internal 14 | SELF-FOUND, not raised: classifying fifteen rounds of findings by failure MECHANISM showed class 5 (self-reference) had no mechanical gate — the only class re-found after its first fix — and building that gate immediately caught R7-1's evidence selecting the evidence RUNNER, whose nested child skips on the recursion marker, so that half of the command exercised nothing while exiting 0 | specs/REVIEW_LESSONS.md (the taxonomy), tests/test_spec_gate.py (the class-5 gate), specs/closure_findings.py (R7-1's selector) | `$PY -m pytest tests/test_spec_gate.py -k reads_an_artifact` |
| **R16-1** | external 16 | package identity was HAND-MAINTAINED and stale: the archive was named v16 while both shipped carriers said v15 / external ROUND 15, because build_collected() received the requested version and never used it — `--version` controlled the FILENAME alone | specs/package/collected_header.txt + manifest.txt (identity tokenized as __VERSION__/__ROUND__/__PACKAGE__), specs/seal_package.py (substituted, round derived from the version and CROSS-CHECKED against the SENT row in reviews.py, plus identity_problems() refusing any disagreement among the three carriers), tests/test_spec_gate.py | `$PY -m pytest tests/test_spec_gate.py -k identity_carriers` |
| **R16-2** | external 16 | the lessons carrier was located with split(BEGIN, 1) and never required exactly one marker pair, so an appended second block claiming 999 findings passed --check, the gate and full archive verification — a SECOND, WEAKER COPY of the strict rule already in skip_inventory, written for 0014's identical finding | specs/generated_block.py (ONE implementation: standalone-line markers, exactly one pair, no normalization, strict on the WRITE path too), specs/skip_inventory.py + specs/review_lessons.py (both delegate), specs/seal_package.py (the lessons check added to EXTRACTION_CHECKS) | `$PY -m pytest tests/test_spec_gate.py -k marker_mutation` |
| **R17-1** | external 17 | R16-1's fix enumerated the three identity carriers the reviewer named and there were FIVE: COLLECTED lines 6-7 state each spec's own candidate revision and were still template literals, so the v17 package shipped saying `draft v16` while its SENT rows said v18, and identity verification found nothing wrong | specs/package_identity.py (the structured record: version, round, per-spec candidate revision, with exactly one SENT row required per packaged spec), specs/package/collected_header.txt (__CANDIDATES__), specs/seal_package.py (filled from the record; identity_problems() now covers the candidate carriers), tests/test_spec_gate.py | `$PY -m pytest tests/test_spec_gate.py -k identity_record_governs` |
| **R17-2** | external 17 | the lessons document stated `has not moved in eight rounds` in free text OUTSIDE the generated block — wrong (nine) and ungated, since --check compares only what is between the markers; the reviewer changed it to 999 rounds and every check still returned 0 | specs/review_lessons.py (a per-finding `scope` field, checked total, with the claim DERIVED into the block), specs/REVIEW_LESSONS.md (no quantity above the table), tests/test_spec_gate.py (the prologue gate with the reviewer's mutation, the original defect, and both controls) | `$PY -m pytest tests/test_spec_gate.py -k byte_verified` |
| **R18-1** | external 18 | the structured identity record was not total over its claimed domain in THREE ways: the candidate revisions restated in SENT prose were never cross-checked (a row could say `0022 at v999`), duplicate candidate lines collapsed through dict(re.findall(...)) so a carrier could disagree with itself, and FIRST_GOVERNED bounded the run without requiring continuity from it, so deleting the oldest governed row left the record valid | specs/package_identity.py (contiguity of the governed run; every `NNNN at vN` claim in a matching SENT row must equal the record), specs/seal_package.py (candidate lines counted before compared), tests/test_spec_gate.py (all three mutations retained) | `$PY -m pytest tests/test_spec_gate.py -k identity_record_governs` |
| **R18-2** | external 18 | the prologue control lived only in the pytest file and not in review_lessons.py --check, which is what the archive verifier runs; its scrubber also dropped every four-digit number as a spec id, so `has not moved in 9999 rounds` passed both the gate and --check | specs/review_lessons.py (the WHOLE summary — title, prologue, table, derived paragraphs — is generated and byte-verified by --check), specs/REVIEW_LESSONS.md, tests/test_spec_gate.py (the natural-language heuristic deleted; mutations now assert --check itself refuses) | `$PY -m pytest tests/test_spec_gate.py -k byte_verified` |
| **R21-1** | internal 21 | SELF-FOUND (by CI, on the first push): the byte-verification test MUTATED the shipped specs/REVIEW_LESSONS.md and restored it, which was safe only while nothing else ran at the same time — the moment the evidence runner became concurrent it raced the evidence command that reads that file, and the two commands whose evidence touches it (R15-2 and R19-2) failed in two of five CI jobs while five local runs passed | tests/test_spec_gate.py (every mutation runs on a COPY in a temp dir, with rl.DOC repointed; the shipped document is asserted unmodified at the end) | `$PY -m pytest tests/test_spec_gate.py -k byte_verified` |
| **R19-1** | external 19 | identity_problems() extracted the four-digit spec id and the revision from each candidate line and compared only those, so renaming the PATH to specs/0022-not-the-shipped-spec.md kept both fields correct, every identity check passed, and COLLECTED could direct the reviewer at a file that does not exist | specs/seal_package.py (the candidate block compared BYTE FOR BYTE against package_identity.render_candidate_lines(); nothing of that shape allowed outside it; every declared path required to be an archive MEMBER, with the member set a required argument rather than an optional one), tests/test_spec_gate.py | `$PY -m pytest tests/test_spec_gate.py -k identity_record_governs` |
| **R19-2** | external 19 | the generated summary was verified BETWEEN its markers and the text before the opening marker was unconstrained, so a prepended `# What 9999 rounds actually found` became the document's title while --check, the pytest gate and full archive verification all passed | specs/generated_block.py (a REQUIRED keyword-only at_start policy; the opening marker must be the first line when it is set), specs/review_lessons.py (at_start=True) and specs/skip_inventory.py (at_start=False, stated rather than defaulted), tests/test_spec_gate.py | `$PY -m pytest tests/test_spec_gate.py -k byte_verified` |
| **R20-1** | external 20 | the candidate block was checked for occurrence ANYWHERE in COLLECTED rather than as the reviewer-facing `specs:` field, so a package could answer `specs: none — this package has no external candidates` on the line a reviewer reads and carry the correct block lower down; the contradiction passed identity_problems() and the complete extracted verifier | specs/package_identity.py (LABEL/INDENT own the field; render_candidate_field() renders it whole), specs/package/collected_header.txt (the label removed from the template), specs/seal_package.py (exactly one `specs:` field, in the header above the inventory block, byte-identical to the rendered field), tests/test_spec_gate.py (pure-function matrix AND a full-repack regression that asserts the REASON for refusal) | `$PY -m pytest tests/test_spec_gate.py -k relocated_candidate` |
| **R15-3** | internal 15 | SELF-FOUND (by CI, five red runs before I looked): the transcript validator was a SEPARATE test reading the live file that the evidence runner writes, and `pytest-randomly` — a dev dependency that shuffles order every run — put the reader before the writer on some seeds, so the suite failed intermittently from the round-12 seal onward while every local run happened to shuffle the other way. Class 5 exactly: a check that reads what the run produces. The ledger already forbade EVIDENCE COMMANDS from reading that artifact and the rule was never carried across to test-to-test dependencies | tests/test_spec_gate.py (the separate test REMOVED; its validation now runs inside the producer, so there is no order to get wrong), specs/closure_findings.py (both selector notes) | `$PY -m pytest tests/test_spec_gate.py -k reads_an_artifact` |
| **R15-1** | external 15 | the CLOSED transcript schema was closed one level down only: commands rejected undeclared fields while the object holding them did not, so `{"undeclared_top_level": "accepted"}` passed validate(), the whole archive verifier, and a repacked archive | specs/evidence_transcript.py (undeclared keys refused at EVERY level with keys), tests/test_spec_gate.py (the mutation matrix is now DERIVED from the schema — every declared field of every level, plus an undeclared-key mutation per level, plus a coverage assertion that fails when a field or level has no mutation) | `$PY -m pytest tests/test_spec_gate.py -k counterfeit_or_missing` |
| **R15-2** | external 15 | specs/REVIEW_LESSONS.md carried two second copies of its own: it said 39 external findings collapse into six classes while the six headings summed to THIRTY (nine findings were never classified), and it restated the suite duration as ~5min beside carriers measuring 16:45, 15:06 and 1:33 | specs/review_lessons.py (a per-finding classification checked TOTAL against the closure ledger, with the table GENERATED from it), specs/REVIEW_LESSONS.md (counts and the duration removed from prose) | `$PY specs/review_lessons.py --check` |

<!-- /GENERATED:review-closure -->