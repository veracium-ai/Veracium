# Feature spec: maintenance attribution — a consumed contributor must leave a recoverable record

Spec-Status: draft
Spec-Requires: 0006, 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft (v17, 2026-08-10) — round 13 folded (three bin-(a), classified before fixed; all
> three found in prior folds' fixes; R12-2 closed):** the complete ALTER-path
> `sqlite_master.sql` LITERAL is in §4b — authored empirically on the qualified 3.45.1,
> matching the reviewer's measured layout (columns appended before the table-level
> PRIMARY KEY), digest `326ea193…`, authorized BY THIS REVIEW as content and entering the
> v6 evidence verbatim; the migration test compares against the pre-declared literal
> (R13-1, class A — R12-1's second miss: v16 predeclared the rule but deferred the
> literal, and append-rule prose cannot determine byte layout; the check: an
> authorization artifact must be PRESENT IN the reviewed candidate, not promised by it);
> the projection is TWO sets riding `0010`'s stable historical namespace — EXCLUDED
> {id, user_id} / VERBATIM everything else including lineage and the operation reference
> (X18: lineage ids are historical and NEVER remapped, portability.py:279-291; X19: the
> operation transform is deterministic and retry-stable) — the v16 normalized set chased
> a remap that DOES NOT EXIST (the reviewer's three portability citations, all verified
> this fold) and its remap-inversion text is retired with fixture (R13-2, class G — the
> check now covers mechanisms a fix ASSUMES, not only claims it makes); and the
> environment-conditional skip inventory is GENERATED from committed
> `specs/skip_inventory.py` with a TWO-DIRECTIONAL completeness gate (every
> skip/skipif/importorskip site inventoried, every entry live — the hand-listed v16
> inventory missed the optional-MCP importorskip the reviewer caught) (R13-3, class E).
> v17 = the round-14 resubmission. Earlier (v16): round 12 folded (four bin-(a),
> classified before fixed; three
> found in v15's own fixes): the ALTER-path expectation is INDEPENDENTLY AUTHORED — a
> reviewed constant derived by hand from v5's frozen constructor DDL + SQLite's documented
> ADD COLUMN append rule, entering `accepted_digests` by review; the migration must
> BYTE-MATCH the pre-declared text, never define it — closing `0013` §4c's "a migration may
> not define its own destination" (R12-1, class A: v15 moved the circularity instead of
> removing it — "frozen" hid the question *frozen from what?*; the check: every
> authorization claim traces where the authorized value COMES FROM); the repeated-import
> fixture is FROZEN and the arithmetic corrected — 1 edge + 1 ordinary episode + 1 indexed
> output per file → two remapped imports yield 2 edges, 2 ordinary episodes, 1 indexed
> output = 3 EPISODES TOTAL, asserted as total AND split (R12-2, class D found-in-fix: v15
> grafted "one identity" onto the reviewer's probe totals without recomputing); the
> projection has THREE exact sets — EXCLUDED {id, user_id} / NORMALIZED-AND-COMPARED
> (references remap-resolved back to source ids, so a file pointing lineage at a different
> source record REJECTS while a different destination representation stays idempotent) /
> VERBATIM (everything else) — with independent membership assertions and a three-sided
> mutation oracle; "references removed" is retired (R12-3, class E found-in-fix: v15
> declared references removed while also comparing them); and the reviewer-guide gate is
> SELF-PROVING — its patterns are asserted against the original stale form and the comma/
> slash variants (the first gate matched none of them), the guide's "+3" frozen delta is
> gone, and COLLECTED.txt now carries the measured line + the NAMED environment-conditional
> skip inventory so any reviewer delta reconciles against names, not a mutable number
> (R12-4, class E found-in-fix: a gate written against a regression without proving it
> catches the regression). v16 = the round-13 resubmission. Earlier (v15): round 11 folded
> (four bin-(a), classified before fixed; three
> found in v14's own fixes): migration authorization rides accepted `0013` §4e's MANIFEST
> SET — `MANIFESTS[6]` freezes BOTH exact DDL texts byte-for-byte (fresh v6 constructor;
> v5-constructor + three-ALTER path), each with per-path evidence on the qualified runtime;
> the "digest-identical via matching defaults" claim is WITHDRAWN and the "first-ALTER
> treatment" citation corrected — accepted `0013` §4c-deferred EXPLICITLY defers that model
> to its own review round, and nothing here relies on it (R11-1, class A — a cross-spec
> mechanism cited for five rounds without reading the cited text; the check fix: every
> cross-spec citation verified against the cited spec's actual words); the re-import
> idempotency promise is SCOPED to the colliding INDEXED OUTPUT — ordinary edges/episodes
> keep the SHIPPED remap-copy semantics (2 edges / 2 episodes / ONE indexed identity,
> asserted explicitly), because collapsing legitimately distinct identical-content events
> would be an unwarranted behaviour change (R11-2, class G found-in-fix); the source-identity
> projection is MECHANICALLY CLOSED — the indexed output's JSON-mode dump minus exactly
> {id, user_id} + remapped references (lineage compared as the remap-resolved source-id
> set), with a totality test over `Episode.model_fields` and a compared/excluded
> field-by-field mutation oracle (R11-3, class E — the same freeze-the-projection medicine
> as R8-2/R9-3, applied to the new domain); and REVIEWER_GUIDE.md carries NO frozen suite
> counts — COLLECTED.txt is the authoritative expectation, the guide states the
> reconciliation RULE (+3 git-only skips in an extracted tree), and a gate test now forbids
> count triples in the guide (R11-4, class D — the guide had drifted three releases).
> v15 = the round-12 resubmission. Earlier (v14): round 10 folded (six bin-(a), classified
> before fixed; four
> trace to v13's own fixes): the receipt persists the EFFECT payload — `SupersessionResult`
> minus the runtime `replayed` flag (`schema.py:106` marks it "runtime only") — and replay
> constructs effects + `replayed=True`; the race test asserts effect equality + the flag
> flip, never whole-object equality (R10-1, class D found-in-fix — the R9-1 fix's exact-copy
> promise contradicted the shipped runtime contract); phase 1 has THREE branches — non-NULL
> match replays, non-NULL mismatch conflicts, NULL (either legal form) means identity
> UNAVAILABLE and proceeds to planning + version-selected phase 2, with public-retry tests
> against both NULL receipt forms (R10-2, class D — a two-branch phase 1 made the promised
> phase-2 comparison unreachable); the version-column DDL is frozen EXECUTABLE — `ADD COLUMN
> outcome_digest_version INTEGER NOT NULL DEFAULT 1` (the reviewer reproduced SQLite
> rejecting the bare NOT NULL on populated tables); the DEFAULT is the migration stamp, the
> v6 constructor manifest carries the identical default, new writes stamp 2 explicitly, and
> the nonempty-table migration test is named (R10-3, class A); the closed receipt-state
> triple gains a TABLE-DRIVEN exhaustive test over every legal cell and the illegal
> representatives incl. malformed/invalid-field responses (R10-4, class E); re-import
> idempotency is SOURCE-IDENTICAL over normalized source identity — the shipped remap mints
> fresh destination ids (`portability.py:173-180`), so raw record equality can never hold
> and the v13 rule would reject every true remapped re-import; uniqueness is tenant-scoped
> and the repeated `user_id=` import test is named (R10-5, class G — cited against shipped
> code this time); and the §7a surfaces bullet carries all THREE receipt columns (R10-6,
> class D — the FOURTH carrier-drift instance; the sweep now greps the COLUMN NAMES and
> checks every hit lists the full set). v14 = the round-11 resubmission. Earlier (v13):
> round 9 folded (six bin-(a), classified before fixed): the
> replayed response is DURABLE — the receipts table gains `response` (the persisted
> `SupersessionResult` json, written atomically; replay returns IT, never a reconstruction
> from the discarded plan; the O1≠O2 race test is named) (R9-1, class A — v12's replay
> promise was unimplementable against the receipt's actual columns, found-in-fix from the
> R8-1 fold); the digest projection is durably discriminated — `outcome_digest_version`
> stamps migrated rows 1 / new writes 2, comparison selects by the STORED version and the
> receipt-state triple is a CLOSED enumerated set (R9-2, classes C+F — two writers shared
> NULL); the partition is proven AT THE STORE — `test_every_snapshot_field_mismatch_aborts_
> the_plan` iterates the same field enumeration and requires an abort per mutated field,
> closing the inclusion-vs-binding gap (R9-3, class E — the third consecutive
> verifies-the-adjacent-property instance); `needs_confirmation` moves to EXACT-EQUAL —
> the shipped absorption (`graph.py:163-167`) inherits exactly valid_from/observed_at/
> confidence and never touches it; every carrier updated incl. the pre-image's vague
> "liveness/trust transfers", both retired forms in the registry (R9-4, class G — a design
> note was trusted over the shipped code, now cited by file:line); import-index uniqueness
> is defined against the DESTINATION over the origin-namespaced key (resolved origin,
> operation_id, index) with record-identical re-imports idempotent and the two-import test
> named (R9-5, class C — the quantifier stopped at one file); and §4c's "no schema DDL
> beyond the ledger table" is corrected + retired into the registry — the fact-sweep now
> greps DDL statements, not summary phrasings (R9-6, class D — the third carrier-drift
> instance of the same fact, missed because the R8-4 sweep keyed on wording). v13 = the
> round-10 resubmission. Earlier
> (v12): round 8 folded (five bin-(a)); every finding classified against
> the 7-class taxonomy BEFORE fixing, and the check that missed it fixed WITH it: phase 2 is
> REQUEST-FIRST — on a receipt hit with request identity on both sides, the store derives the
> plan's `raw_request` digest and compares REQUESTS first: match → REPLAY (the
> concurrent-preflight loser's post-commit re-plan is discarded unconsulted — the race can no
> longer resurrect the public replay defect); outcome-only comparison is reserved for receipts
> WITHOUT request identity, and the concurrent test now REQUIRES replay (R8-1, class D — the
> "replay or conflict" cell contradicted the request-stable rule, introduced by v11b's own
> matrix fix); the snapshot is COMPLETELY BOUND by an exhaustive three-class field partition
> (exact-equal / recomputed / forbidden-on-request) with a totality test over
> `Edge.model_fields`, a field-by-field mutation oracle, and BYTE-EXACT digest freezing
> (separators, raw-UTF-8 non-ASCII, float/datetime forms, NaN aborts) + frozen digest vectors
> (R8-2, classes C+F); duplicate PRESENT indices within one imported operation are REJECTED —
> partial history explains gaps, never duplicates (the v10 rule R7-3's relaxation dropped,
> reinstated; R8-3, class D found-in-fix); the bold schema summary now enumerates BOTH
> structural changes — the ledger table + indexes AND the receipts ALTER (R8-4, class D — the
> same carrier omission v11b caught in §7b, one carrier over); and the gate registry carries
> STABLE rule ids with the self-test asserting each fixture against ITS OWN entry (any-entry
> matching let a broad neighbour mask a dead one), an inverse test that every modern entry has
> a fixture (which immediately caught one unproven entry), the two live empty-payload-evasion
> phrasings replaced with the no-transfer rule, and new registry entries for both retired
> framings (R8-5, class E). v12 = the round-9 resubmission. Earlier (v11): round 7 folded
> (five bin-(a)), and the gate now provably BITES:
> the request identity is DERIVED BY THE STORE from a `raw_request` snapshot on the plan
> (caller-supplied digests are gone — the reviewer's bind-A-to-B forgery is impossible; the
> frozen digest construction, plan-consistency verification, and the forged/malformed/
> concurrent-preflight tests are named) (R7-1); §7b carries the EXACT ready-to-land `0003` §4f
> amendment text verbatim (the receipt column, the two-phase rule, the legacy policy) plus the
> I9 check extensions, landing in the same commit as the implementation — and `0003`'s wrong
> "accepted 0014" wording is fixed (R7-2); the output-index round-trips (the explicit
> exclude-none serializer exception; native-v5 outputs always carry the index; absence = the
> unprivileged legacy shape so v4→v5→v5 is lossless; contiguity is a local-op invariant, not
> an import gate; three named round-trip tests) (R7-3); the remaining live contradictions are
> fixed — found by the BROADENED gate, not by hand (R7-4); and the gate has an adversarial
> SELF-TEST (`tests/test_withdrawn_gate_bites.py`): every registry entry is proven against the
> VERBATIM retired forms the dispositions quoted, plus a tree-cleanliness assertion — both in
> the suite (R7-5). **Pre-send self-review (the classified-findings pass, at the repo owner's
> prompt) caught FOUR further instances of established classes before this package shipped:
> the §2c raw_request row CLAIMED but absent from the table (class E, the R6-6 shape); the
> §7b plan and schema rows still omitting the new fields/ALTER (class D, the exact R7-2
> shape, repeated); and the snapshot serialization leaving the field-set/null rule open
> (class F, the R7-3 ambiguity reintroduced) — all fixed in this revision and disclosed.**
> v11 = the round-8 resubmission. Earlier (v10): round 6 folded (six
> bin-(a)), and the retired-contract gate is
> now REAL — committed in `specs/withdrawn_phrases.py`, run by the suite, in the package:** the
> split receipt has ONE construction serving both rules — a PUBLIC pre-plan lookup (matching
> request digest replays with NO re-planning, so the post-commit O2 is never computed) and
> STORE-LEVEL exact-plan verification (the outcome digest governs plan resubmissions, where the
> mutation check is reachable by construction) (R6-1); the durable carriers exist — the
> receipts table gains a nullable `request_digest` column in the SAME v5→v6 migration (with
> `0013` first-ALTER treatment named), `SupersessionPlan` gains the plan-transient field, and
> the LEGACY policy is honest (NULL request digest → the pre-split outcome-match rule; the
> defect heals forward, never retroactively fabricated) with the adversarial reused-op-id
> tests (R6-2); `consolidation_output_index` has the full ownership/absence matrix — ONLY the
> consolidation primitive may set it, caller-supplied values on generic paths are REFUSED,
> omitted-when-None (never JSON null), and the v4/v5/malformed import cells are enumerated
> (R6-3); A7 carries exact SET EQUALITY in its invariant text with the three named
> omitted/duplicated/extra tests (R6-4); the seven live contradictions are fixed (R6-5); and
> R6-6's finding is conceded in full — the v9 "mechanism" was an uncommitted script; the
> 0014 rules now live in the repo's REAL `withdrawn_phrases.py` gate, whose first committed
> run found EIGHT hits including TWO in `0003` that no round had named. v10 = the round-7
> resubmission. Earlier (v9): round 5 folded (SEVEN bin-(a), incl. an EXECUTED live product
> defect), and the carrier sweep is now MECHANIZED:** A7 requires EXACT SET EQUALITY between
> absorption drafts and `absorbed_duplicate` invalidations — omitted/duplicated/extra drafts
> each abort (value verification cannot catch a MISSING draft; R5-1); `0003`'s receipt SPLITS
> into a REQUEST digest (raw submitted edge — replay identity; the reviewer executed the live
> defect where an identical public absorption retry raises instead of replaying) and an OUTCOME
> digest (audit; carries the contributions + pre-image) — a marked `0003` amendment with the
> public lost-response replay test (R5-2); the output index is an `Episode` MODEL FIELD in the
> existing json blob (the reviewer's simpler-fit ruling; the v8 SQL-column form is WITHDRAWN —
> no DDL, no sync boundary; R5-3) and, being exported, **`FORMAT_VERSION` bumps 4→5** per
> accepted `0010`'s refuse-don't-drop rule, with the older-importer refusal test (R5-4); the
> `Optional[int]`/index-0-falsey sweep enumerates EVERY consumer incl. the two failing asserts
> in `test_0010_consolidation_primitives` (R5-5); the severance-capability gate is carried into
> A4's check column, §7a, and §8 (R5-6); and the FIVE mutually-exclusive live contracts are
> resolved (§4's may-be-empty invariant text; §4c's `valid_from?`; §7's direct-restoration
> bullet; §1's pre-`0012` reinforcement description; §2's narrow list) with a MECHANIZED
> retired-phrase sweep (run clean over this revision, and caught a sixth contradiction my
> manual pass missed — the §4c single-digest paragraph) now standing pre-package (R5-7). v9 =
> the round-6 resubmission. Earlier (v8): round 4 folded (six bin-(a)), and the fold ran the found-in-fix
> checklist EXPLICITLY before packaging (which itself caught a v7 contradiction — see below):**
> absorption payloads are per-contributor `{base, contributor}` and reversal is RE-COMPUTATION
> (one incoming absorbing several priors broke the single-diff form — the 0.2-absorbs-0.8/0.9
> case) (R4-1); the pre-image is SEMANTICALLY verified — the store recomputes the expected
> post-image from pre-image + authoritative contributors and compares exactly (hashing a false
> claim only made it stable) — and gains its own §2c matrix row (R4-2); the output-index carrier
> is COMPLETE (the named `episodes.consolidation_output_index` column, the `Optional[int]`
> signature with its return-consumers enumerated, finalization immutability, the
> exported-with-episode portability split, and conflict comparison over DETERMINISTIC fields
> only) (R4-3); the transitive-prerequisite gate is structurally testable (`SiteSpec` +
> `transitive_contract` spec-anchor verification + the adversarial gate cases) (R4-4); the
> per-site survivor rule reaches §2c and §7, §7a gains the pre-image/output-index/portability
> rows, and §2's leftover narrow field list is gone (R4-5); the consolidation schema is EXACT —
> no `valid_from` on Episodes, mandatory keys named, optionals OMITTED never null (R4-6). THE
> CHECKLIST'S OWN CATCH: v7's `{}`-at-absorption was contradictory under the new total shape —
> `{}` is now an integrity error EVERYWHERE, A1 carried by the total payload. v8 = the round-5
> resubmission. Earlier (v7): round 3 folded (seven bin-(a)):** the absorption PRE-IMAGE exists
> and binds — `_build_supersession_plan` snapshots the incoming edge's original scalars BEFORE
> inheritance onto `absorption_pre_image`, the store derives `prior` from it, and it ENTERS the
> receipt digest (the 0.1/0.2-into-0.9 byte-identical-plans reproduction closed at the root)
> (R3-1); survivor binding is PER SITE — absorption: written-this-commit; consolidation: an
> existing provisional output verified bound to this operation/fence/lineage/identity (R3-2);
> `output_index` is STORE-ASSIGNED and persisted on the output row (no caller index exists), and
> an op_key conflict VERIFIES the existing row field-for-field — mismatch aborts, never a silent
> DO NOTHING (R3-3); the A2 test consumes the two-output compactor it constructs, asserts N×M on
> ROW COUNTS per output, and compares ONLY frozen digests (R3-4); §4f's candidate text is inert
> quoted history and the transitive prerequisite is a MECHANICAL registry capability field +
> gate (R3-5); the §5/§7a/§7b/§2/Q1 carriers are swept — N×M, cutover-insertion, THREE indexes,
> the widened field set (R3-6); A1's empty payload is site-scoped and A5's injection targets
> the REACHABLE derivation seams (R3-7). v7 = the round-4 resubmission. Earlier (v6): round 2
> folded (eight bin-(a), all found-in-fix cells in v5's own
> amendments):** the caller-supplied payload is GONE — the store derives absorption payloads from
> the survivor's pre/post rows and consolidation payloads from each input row, all authoritative
> (R2-1); the consolidation retry identity is PERSISTED (`op_key` + partial unique index, ON
> CONFLICT DO NOTHING — append-only preserved; `ConsolidationOutputDraft` gains `output_index`)
> (R2-2); the N×M rows insert atomically at the OUTPUTS_DURABLE cutover transition — `0010` has
> no op-wide transaction, and the cutover is the point of no return with inputs still present;
> every crash seam is specified (R2-3); consolidation payloads gain `author_of_evidence` + `date`
> and are TOTAL — `{}` at absorption *(WITHDRAWN in v8: payloads are total everywhere)*; the evidence-ref
> digest is byte-exact (UTF-8, u32be framing) with `""` DEFINED as absent (R2-5); §2c is the
> required input MATRIX (R2-6); the A2/A3 checks now bite — two outputs, N×M, the frozen digest
> construction computed inline, `source_id` supplied (R2-7); and the round-1 dispositions are
> swept across §2/§5/§7/§7a incl. the tombstone text aligned to the ruling (R2-8). v6 = the
> round-3 resubmission. Earlier (v5): round 1 folded: the reviewer ACCEPTED the two-bin protocol from
> round 1, RULED the §4f tombstone question (frozen point 5 RETAINED for v1 — no tombstone; the
> six unaffected interface points stay frozen; the point-5 change was NOT signed), and returned
> NINE bin-(a) findings, all folded:** input×output consolidation attribution with fence-keyed
> idempotent inserts (R1-1); the draft carries a TYPED consumed-row reference and the STORE
> derives identity from the authoritative row (R1-2); absorption drafts ENTER `0003`'s receipt
> digest — the derived reading is dead by counterexample (R1-3); consolidation payloads record
> each INPUT's own values and reversal is re-computation (R1-4); `survivor_type` joins the table
> key and both reads (R1-5); the tombstone is withdrawn per the ruling with transitive handling a
> named prerequisite for any future severance-capable site (R1-6); the defective test carriers
> are fixed to the v5 contract (min-batch, typed two-arg reads, digest semantics — R1-7); the
> evidence-reference digest gets its own frozen domain-separated construction and the payload a
> CLOSED per-site recursive schema (R1-8); the consumption-site set is a MECHANICAL registry +
> generated manifest + gate, and §7b gains the `0010` amendment and retention carriers (R1-9).
> v5 = the round-2 resubmission under the accepted protocol. Earlier (v4): REVIEW-READY —
> every prerequisite has LANDED.** Since v3:
> **`0006` is ACCEPTED + IMPLEMENTED** (schema v5 shipped; the shared `source_identity_digest`
> primitive is real code this spec's `identity_digest` calls — `src/veracium/source_identity.py`);
> **`0012` is ACCEPTED + IMPLEMENTED + its implementation independently REVIEWED AND ACCEPTED**
> (22 external rounds total), so the reinforcement excision in §3 is landed FACT — the two
> reinforcement tests now PASS as Design-1 attributions and the ONLY remaining attribution gaps
> in the whole suite are this spec's two strict xfails (A2/A3). v4 adds the §7b cross-spec
> carrier table (the `0012` reviews' recurring finding class, pre-empted), mechanizes the §4f
> tombstone CANDIDATE for the A→B→C transitive gap (explicitly the ONE open design question for
> round 1 — it touches frozen interface point 5, so any resolution runs the freeze protocol),
> and updates every stale prerequisite reference. **Review protocol: the two-bin boundary
> standard (accepted by the reviewer for `0012` and proven over 14+8 rounds) is PROPOSED from
> ROUND 1** — bin (a) contract-breaking, bin (b) recorded — see the review package COLLECTED.
> Earlier (v3): **DESIGN-COMPLETE mechanical contract (2026-08-08).** Matured from the v2 stub so the
> `0006`↔`0014` interface can be frozen: `0006` v3 R11 gates `0006` acceptance on `0014` reaching
> mechanical completeness, and this is that. §4 now specifies the `contribution_ledger` table
> (`SCHEMA_VERSION` v6), the `ContributionDraft` a site emits, the per-site ATOMIC write paths (riding
> 0003's plan commit and 0010's fenced txn), the two reads, and erasure/portability; §5 (growth +
> retention), §6 (A1–A10, incl. atomicity A7, append-only A8, the `revoke_source` join A9), §7
> (failure modes) and §7a are concrete. Still `draft` — acceptance needs `0006` accepted first and an
> external review of this contract; nothing implementable yet. Written from research's
> `A3-source-revocation-design.md`
> §2 finding at dev's recommendation to **decouple the record from the `revoke_source()` feature**.
> This spec establishes the RECOVERABLE ATTRIBUTION RECORD only; the revocation set-computation
> (`A3`) and the derived-view reach (`0004`) consume it. **v2 folds research's response
> (`proposals/0014-research-response.md`, 2026-08-08): Q5 CONFIRMED, and the invariant is
> re-keyed from "state transfer" to CONSULT-AND-DISCARD** — research measured that an older/weaker
> contributor leaves every survivor value unchanged (`max()` never moves) yet still vanishes, so a
> transfer-keyed rule would miss it, and that omission is an attack path (stale-but-corroborating
> input becomes the unlogged channel). Q1–Q4 resolved (§10); a `0014 → 0006` dependency is named
> (key the ledger on a **digest** of `0006`'s **`(origin, source_id)` pair** — `0006` v2, R5: identity
> is the pair, `origin` store-minted so a revocation does not reach another HONEST store's records
> (forged imports are `0005`/`0006` R7's boundary, not authenticated here); both
> `source_id` (host free-form) and `evidence_ref` are digested; `origin` is store-minted but digested
> too, as part of the one uniform key. `0014` digests the RESOLVED pair — `0006` §4.6 forbids
> digesting a stored `origin`-absent pair directly).

*Fill this in **before** implementing. See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`), from research's A3 finding |
| **Version** | **v3 (design-complete), amended 2026-08-09 for the reviewer's interface-freeze disposition** — *re-read before editing; quote the version you approve.* The CONSULT-AND-DISCARD invariant + the full mechanical contract (§4 ledger/primitives/reads, §5, §6 A1–A10, §7, §7a) are concrete. Reviewer amendments folded: **F1** `identity_digest` is NULLABLE (NULL iff `source_id` absent — never a `(origin, NULL)` pseudo-source; A4/A5/A9 reconciled); **F2** the digest is `0006`'s one shared `source_identity_digest` primitive (`0006` §4 rule 7/I12); the three stale `0006 §4.5` citations corrected to §4.6; a multi-generation transitive-attribution case (§7) carried into the full review. Still `draft`; the freeze is of the INTERFACE. Implementation waits on `0006` accepted. |
| **Status** | *canonical state is the `Spec-Status:` line at the top; this row states none of it.* |
| **Internal reviewers** | dev · **research (finding owner) — reviewed 2026-08-08, decoupling CONFIRMED, invariant sharpened** (`proposals/0014-research-response.md`) |
| **External review** | required (full — it will touch guarded files: `graph.py`, `lifecycle.py`, `store/sqlite.py`). Not yet sent. |
| **Decision + date** | — (draft) |
| **Path** | full |

---

## 1. Problem and motivation

**Ordinary maintenance silently destroys the evidence that a source contributed to a fact.**
Veracium's whole guarantee is provenance you can trust — but maintenance operations transfer
*state* (liveness, confidence, disclosure, derivation, first-known date) from a **contributor**
record into a **survivor** record, and two of the three destroy the record that the contributor
ever existed. So for any surviving fact you **cannot** answer "which sources gave this its current
liveness and confidence?", and if a source later proves compromised you **cannot** compute — let
alone reverse — its contribution. Measured, no LLM, in research's A3 provenance-chain demo
(a3_provenance_chain_demo.py; lives in `veracium-research`, not this repo).

**What happens if we do nothing:** the provenance chain the product sells as complete is not
complete — it is complete *only until the first maintenance pass*. *(Historical note: when this
section was written, reinforcement was the sharpest instance — a compromised feed could renew a
fact's liveness invisibly. `0012` Design 1 has since LANDED and closed that door: restatements
persist as their own edges and transfer nothing. The two sites BELOW remain open TODAY:
consolidation deletes its inputs' sources; absorption's contributor link is an unqueryable note
string.)* This is the **fourth instance of one pattern** — a maintenance-time operation
crossing a boundary the write path guards correctly (GHSA-r7j7-5jq9-3f5q / 0.4.1,
GHSA-hcj3-8jqc-wqrp / 0.4.4, `specs/0003`, and now this). The recurrence is the argument: point
fixes have not closed the class.

**This is NOT the revocation feature.** `revoke_source()` (research `A3`) and making a revocation
reach recall (`0004`) are the *consumers*; both are impossible while the set cannot be computed.
This spec is the **minimum that makes the class of finding go away** and has value whether or not
revocation is ever built — an attribution record that survives maintenance.

**Alternatives rejected.**
- **Fix each site independently** (patch reinforcement, patch consolidation, patch absorption).
  This is how the pattern recurred four times: three separate ad-hoc fixes with no shared invariant
  invite a fourth site to reintroduce it. A single invariant over "state transfer" is what closes
  the class.
- **Do it inside `A3`/`revoke_source`.** Couples a broadly-useful integrity property to one feature
  and one owner (`0004`); the property is worth having with no revocation feature at all (a host
  auditing "why is this fact live?" needs it). Decoupling is dev's explicit recommendation.
- **Reconstruct attribution lazily from existing fields at revocation time.** Measured to be
  impossible at the time *(WITHDRAWN premise, kept as the historical rationale: pre-`0012`
  reinforcement persisted nothing to reconstruct from — `0012` Design 1 has since landed and
  reinforcement now persists its edge; the two 0014 sites remain unreconstructable exactly as
  stated)*: consolidation deletes its inputs (their provenance is gone, only opaque ids
  remain) and absorption's link is an unqueryable note string.

---

## 2. Field contracts touched — REQUIRED, blocking

Enumerated mechanically from the interface (the method that missed three surfaces in `specs/0002`):
the maintenance ops that consult-and-discard a contributor are `graph._build_supersession_plan`
(absorption — reinforcement is no longer a site, `0012` Design 1) and `lifecycle.consolidate` (via
the 0010 fenced primitives) — see §3 for the sites and §7a for the full surface list. The **payload** fields — those *read from a
contributor and written onto a survivor* — are `Provenance.observed_at`, `Provenance.confidence`,
`Edge.valid_from`, `Provenance.disclosure`, `Provenance.derived_from`; the ledger stores their prior
and new values (the R4-1/R4-6 per-site closed sets — all store-clear scalars, Q1; TOTAL at
both sites, a no-op transfer visible in the values). The identity is
`0006`'s resolved `(origin, source_id)` pair, digested (below).

> **`0014 → 0006` dependency (research Q1/F3, and `0006` v3 R5/R7).** The ledger is keyed on **`0006`'s
> RESOLVED `(origin, source_id)` PAIR**, already the revocation key. `0006` (R5) makes identity the
> pair — `origin` store-minted — so among **HONEST** exports an imported source cannot collide with a
> local one and a revocation keyed on the pair does not reach another store's records. **NOT against
> an adversarial import (`0006` R7): `origin` is namespacing, not authenticated — forged imports are
> `0005`'s untrusted-import boundary, not a structural guarantee here.** `0014` v3 was
> design-complete; the interface was FROZEN (reviewer-signed 2026-08-09) and `0006` has since been
> ACCEPTED (2026-08-09) and IMPLEMENTED (schema v5 shipped) — the dependency is a landed fact, and
> the seven frozen points bind this spec's review (changes to a frozen point need both owners +
> the reviewer). `0006`'s "opaque"
> is a host-convention, not enforced (`0006` §8, F3), so for a content-free surface the ledger stores a
> **deterministic digest of the pair**, never the raw value. The digest stays joinable:
> `A3`/`revoke_source`, given a pair to revoke, digests it the same way. `evidence_ref` is digested
> under its OWN frozen, domain-separated, origin-scoped construction (§4a, R2-5/R1-8). This makes `0006` (source identity) a prerequisite — hence `Spec-Requires: 0006, 0007,
> 0013`, and `0014`'s table is the `SCHEMA_VERSION` AFTER `0006`'s (v6, `0006` is the no-DDL v5). The
> scalar payload — the per-site closed sets of §4a (absorption base/contributor over
> {`observed_at`, `confidence`, `valid_from`, `disclosure`, `derived_from`-if-present};
> consolidation input over {`observed_at`, `confidence`, `disclosure`, `author_of_evidence`,
> `date`, `derived_from`-if-present} + `output_index`) — is timestamps/floats/closed enums,
> store-clear, so **content-free and reversible do not conflict** (Q1 resolved).

## 2c. Untrusted inputs — REQUIRED, blocking

The contributor whose attribution we record may itself be adversarial (a compromised feed
is the motivating case). The record must therefore be **fail-closed and content-free**: it records
*that* a contributor was consumed and *what state, if any,* moved, keyed on a **digest** of
`0006`'s **RESOLVED** `(origin, source_id)` pair and a digested `evidence_ref` (`source_id`/`evidence_ref`
are host free-form; `origin` is store-minted but digested too as part of the one opaque key that need
not appear in a durable surface — `0006` F3/R5/§4.6), so a malicious contributor cannot smuggle memory content
into a durable audit surface, and a missing/absent record is treated as "attribution unknown → the
survivor is suspect", never "clean". **The adversary's cheapest evasion is the NO-TRANSFER
CONSUMPTION** — a stale-but-corroborating input that moves no `max()` — which is exactly why the
record is owed to the consumption, not the transfer (§4): the record is written even then, its
store-derived TOTAL payload showing that nothing moved.

**The input matrix (R2-6) — every draft/derived field × {empty, malformed, unrecognised,
adversarial}, each cell with its outcome and governing invariant.** The store validates BEFORE any
write; every REJECT aborts the WHOLE maintenance op (A7 — no consumption without a record):

| input | empty/absent | malformed | unrecognised | adversarial | governs |
|---|---|---|---|---|---|
| `site` | REJECT | REJECT (non-string) | REJECT — not in the closed registry | a registered-but-wrong site cannot bind: the store verifies the draft arrived through that site's own carrier (plan / cutover transition) | A4 |
| `survivor_type` / `survivor_id` | REJECT | REJECT (not 'edge'/'episode') | REJECT — fails the PER-SITE binding rule (absorption: no such row written THIS commit; consolidation: no provisional output bound to this operation/fence/lineage/identity — R3-2/R4-5) | a forged survivor fails the same per-site rule | A7, R1-2, R3-2 |
| `absorption_pre_image` (plan field) | REJECT when the plan carries absorption contributions (a missing pre-image is underivable state) | REJECT — non-scalar values, wrong types, non-canonical key order | REJECT — unknown/missing closed-set keys | a schema-valid-but-FALSE pre-image is caught by the semantic recompute-compare (R4-2): the recomputed post-image mismatches the committed survivor → abort | A7, R3-1, R4-2 |
| `contributor_type` / `contributor_id` | REJECT | REJECT | REJECT — dangling: no such row being consumed this txn | a FOREIGN-TENANT row reference → REJECT (tenant mismatch is an integrity error, never a silent cross-tenant read) | A7, R2-1 |
| payload | n/a — the caller CANNOT supply one (R2-1); store-derived | a store-derivation producing non-finite floats (NaN/±Inf in `confidence`) → REJECT the op: the SOURCE row is corrupt and consuming it must not launder the corruption into a "clean" record | n/a | n/a — derivation reads only authoritative rows | A5, A7 |
| `source_id` (read from the contributor row) | legal — `identity_digest` NULL (unknown source, recorded not revocable) | length-bounds are `0006`'s (its §4 rule 5 rejected it at WRITE time; a stored row is in-bounds by invariant) | n/a (opaque) | an adversarial value is inert: digested, never rendered; grouping is the only power it has (`0006` I5) | F1/I13, A5 |
| `origin` (resolved) | resolves to `store_identity` per `0006` §4.6 — never digested absent | a stored-absent pair reaching the digest UNRESOLVED → integrity error (`0006` §4.6) | n/a | store-minted; a forged import is `0005`'s boundary | A9 |
| `evidence_ref` (read from the row) | `""` is DEFINED as absent → digest NULL (R2-5) | non-UTF-8-encodable → REJECT the op (corrupt source row) | n/a (opaque) | inert: digested under its own domain, never rendered | A5, R2-5 |
| `SupersessionPlan.raw_request` (R7-1 — the authoritative raw-request carrier) | absent → phase-2 semantics only; the receipt's `request_digest` stays NULL but the receipt is NOT legacy-equivalent (R9-2): it stamps `outcome_digest_version` 2 and persists its `response`, so it verifies at the EXTENDED projection — only migrated pre-upgrade receipts carry version 1 | non-dict, missing closed-set fields, non-canonical encoding → the op aborts | a snapshot whose edge id/user/subject/relation differ from the plan's incoming → abort (plan-inconsistent) | a FORGED snapshot (valid shape, false values) fails the exact-equal/recomputed/forbidden field partition or the R4-2 semantic recompute (§4b, R8-2) → abort; concurrent preflight (two racing publics, same raw edge): one commits; the loser's phase-2 hit is REQUEST-FIRST (R8-1) — matching `raw_request` → REPLAYS the committed outcome, its own post-commit re-plan discarded, NEVER an outcome conflict; outcome-only comparison is reserved for receipts without request identity (legacy NULL / snapshot-less plans); never double-applies | A7, R4-2, R7-1, R8-1, R8-2 |
| `Episode.consolidation_output_index` (R6-3/R7-3 — ownership + ROUND-TRIP: only `write_consolidation_output_if_current` may SET it) | absent = None. **The serializer rule is EXPLICIT (R7-3 — default `model_dump_json()` would emit `null`): the Episode export path serializes this field with exclude-none semantics — OMITTED when None, a stated exception to the default; an explicit JSON `null` on import = malformed → REJECT.** | Boolean, coerced string, negative, non-integer → REJECT (generic insert AND import) | caller-supplied on generic paths → REFUSED. **Round-trip (R7-3): a NATIVE v5 consolidation output ALWAYS carries its index (the exporter emits it; a v5 import of a lineage-bearing output WITHOUT an index is accepted as the LEGACY shape — absence = pre-v6 history, LESS identity, never forged identity — so v4→v5→v5 round-trips losslessly: absent stays absent, present stays present).** Contiguity 0…M−1 is a LOCAL-op invariant (asserted in the primitive + tests); it is NOT an import gate — imported history may be partial, and gaps there are indistinguishable from partial export, so the absence rule governs. **UNIQUENESS survives the relaxation (R8-3 — the v10 duplicate rule, reinstated: partial history explains GAPS, never DUPLICATES) and is defined against the DESTINATION, not the file (R9-5 — per-file uniqueness lets two sequential partial imports each be locally clean while the destination accumulates duplicates): the uniqueness domain is incoming ∪ existing destination state, keyed on the ORIGIN-NAMESPACED operation identity `(resolved origin, operation_id, index)` — `0006` materializes origin on export, so operations from different source stores never collide by raw id, and the same operation re-imported IS the same identity. An incoming lineage-bearing output whose key already exists in the destination is accepted IFF it is SOURCE-IDENTICAL (R10-5: the shipped remap path MINTS FRESH destination ids on every `user_id=` invocation (`portability.py:173-180`), so raw record equality can never hold for a remapped re-import). **The idempotency promise is SCOPED to the COLLIDING INDEXED OUTPUT — never the whole file (R11-2: source-identity is defined ONLY for indexed consolidation outputs; ordinary edges/episodes follow the SHIPPED remap-copy semantics — accepted `0009`/`0010` behaviour this spec does not change — so a repeated remapped import legitimately duplicates ordinary records while the INDEXED OUTPUT's identity claim resolves idempotently; collapsing legitimately distinct identical-content events would be a behaviour change with no `0014` warrant).** **The source-identity projection is MECHANICALLY CLOSED over TWO EXACT SETS, riding accepted `0010`'s STABLE HISTORICAL NAMESPACE (R12-3 fixed by R13-2 — v16 invented a lineage remap-inversion that DOES NOT EXIST: the shipped importer's `id_map` covers only exported records (`portability.py:179-186`), remaps `edge_id`/`supersedes_episode` but never `lineage` (`:196-202`), and deliberately leaves lineage ids UNCHANGED because they are already historical (`:279-291`, X18) — consolidation lineage names DELETED input episodes that are not in any export, so no remap entry can exist for them; the v16 `edge_id=X/Y` example was also type-inconsistent, lineage carries historical EPISODE ids):** every `Episode.model_fields` member is assigned to exactly ONE of: (1) **EXCLUDED** — destination-minted, no source meaning: exactly `{id, user_id}`; mutation of the destination representation cannot affect identity by construction; (2) **VERBATIM** — every other field, compared byte-for-byte after JSON-mode dump — INCLUDING `lineage` (historical ids are STABLE across export/import by `0010` X18's design: never remapped, validated historical on entry) and the operation reference (the importer's own X19 transform is DETERMINISTIC and retry-stable — "no persisted map", the same source operation always yields the same destination-historical id — so post-import comparison is direct equality). There is NO normalized set: nothing in the shipped boundary rewrites these references, so nothing needs inverting — a second import of the same file reproduces the SAME historical lineage/operation ids and verbatim equality holds; a file whose lineage names a DIFFERENT historical episode differs verbatim and REJECTS. Membership is asserted INDEPENDENTLY (`test_source_identity_projection_sets_are_exact` pins both lists; `test_source_identity_projection_is_total` proves they partition `Episode.model_fields` — a new field breaks it until classified). The mutation oracle (`test_every_projection_field_binds_source_identity`): mutate any VERBATIM field — including a lineage member id — in the second file → REJECT; mutate an EXCLUDED field's representation → idempotent. ANY verbatim-field difference → REJECT. Uniqueness is TENANT-SCOPED: (destination user, resolved origin, operation_id, index). Named tests: `test_duplicate_output_index_within_an_imported_operation_is_rejected` · `test_duplicate_output_index_across_sequential_imports_is_rejected` · `test_repeated_remapped_import_resolves_the_indexed_output_idempotently` (R11-2/R12-2 — the FIXTURE IS FROZEN because v15's stated totals were arithmetically wrong ("2 edges / 2 episodes / 1 identity" forgot the indexed output is itself an episode): the file contains EXACTLY 1 edge + 1 ordinary episode + 1 indexed consolidation output; after TWO remapped imports the destination holds 2 edges, 2 ordinary episodes, and 1 indexed output episode — 3 EPISODES TOTAL, asserted as both the total AND the ordinary/indexed split, with the indexed output claiming no second identity).** | a host submitting a plain episode with index 0 → refused at the generic path; a v5 sender omitting an index yields the unprivileged legacy shape, not fabricated identity; two imported outputs sharing (operation_id, index) → rejected (R8-3) | R5-3, R6-3, R7-3, R8-3, A7 |
| round-trip tests (R7-3, named) | — | — | `test_v5_export_round_trips_output_indexes` (present stays present, absent stays absent) · `test_a_v4_import_then_v5_export_reimports_cleanly` (the reviewer's 4-step case) · `test_a_plain_episode_round_trips_with_no_index` | — | R7-3 |

---

## 3. The finding, at its current sites — REQUIRED, blocking

Three maintenance sites were found to transfer contributor state into a survivor; **one
(reinforcement, §3.1) is now closed by `0012` Design 1, leaving TWO for `0014` — consolidation
(§3.2) and absorption (§3.3).** Reproduce with research's A3 provenance-chain demo
(a3_provenance_chain_demo.py, `veracium-research`). Status is stated **as of 0.6.0** (0010 partially
moved §3.2 after A3 was written):

| # | site (a maintenance op that consults a contributor then discards/merges/invalidates it) | contributor recoverable today? | payload (state it may transfer) |
|---|---|---|---|
| ~~**3.1**~~ | ~~**reinforcement**~~ — **CLOSED by `0012` Design 1 — LANDED (accepted 2026-08-10, implemented, implementation-review accepted; the two reinforcement tests PASS as Design-1 attributions in `tests/test_0014_maintenance_attribution.py`). NO LONGER a `0014` site.** `0012` Design 1 PERSISTS the reinforcing edge with its own provenance (transfers nothing), so reinforcement is a consult-and-**KEEP**, not a consult-and-discard — the persisted edge IS the attribution. Finding `M9` is repointed `0002`→`0012`. The two reinforcement `xfail`s move to `0012`. | ✅ 0012 | — |
| **3.2** | **consolidation** — `lifecycle.consolidate` deletes each claimed input; the summary carries `lineage` (0010) = the whole claimed set in the historical namespace | **Partial (improved by 0010) — VERIFIED 2026-08-08.** `lineage == the whole claimed input set == exactly the deleted inputs` (`lifecycle.py:142–156`), so every deleted contributor's ID is recorded; what is lost is **id→source** (the deleted episode's provenance). Not worse than "partial" | disclosure, confidence, `derived_from`, `observed_at` |
| **3.3** | **absorption** — `graph._build_supersession_plan` absorption branch retains the absorbed prior and links it by a free-text `note = "absorbed_by:<id>"` | **Partial** — retained + linked, but as a **string in a free-text field, not a queryable relation**, and inherited `min(valid_from)`/`max(observed_at)`/`max(confidence)` cannot be un-inherited | `valid_from`, `observed_at`, `confidence` |

**3.1 is now `0012`'s, not `0014`'s (research ruling, 2026-08-08).** `0003` deliberately preserved the
reinforcement semantics (`insert_incoming=False`), so the source vanished — but the FIX is
`0012` Design 1 (persist the reinforcing edge with its own provenance), not a `0014` ledger record.
Once the edge is stored it IS the attribution, and with "transfers nothing" there is no payload to
record. So **`0014` covers TWO sites — consolidation (3.2) and absorption (3.3).** The consult-and-
discard INVARIANT (§4) is unchanged; one of its three sites simply moved to `0012`. `M9` is repointed
`0002`→`0012` (`specs/findings.py`).

**What is NOT wrong (do not "fix" it):** reinforcement, consolidation and absorption are the
INTENDED mechanisms, and the cross-class guard (`graph.py`, "identity merges never cross trust
classes") and the 0002/N9b trust-envelope inheritance (min-disclosure, min-confidence,
third-party influence) are all correct. **The defect is only that consuming a contributor is
unattributed, so it cannot be audited or reversed.** This spec adds a record; it changes no
maintenance decision.

---

## 3b. Authorization and scope — *full specs only*

- **Cross a user/tenant/scope boundary?** No. Every ledger row carries `user_id` and is tenant-scoped
  by construction (the same isolation as edges/episodes); the two reads take `user_id`; there is no
  cross-tenant query. A contribution to user A's survivor is invisible to user B.
- **Who may see the affected state?** No principal that could not already. The ledger is **Store-local
  metadata** — like the 0003 refusal inventory, it is **never surfaced to the model** (not in recall,
  answer, or the wiki) and never exported (§4e). It is inspection/audit state for the host and
  `revoke_source`, read only through `contributions()`/`contributors_of_source()`.
- **Scope change (sharing, revocation, forget)?** `forget_user` erases the user's rows (A6);
  survivor deletion drops its rows (A10). Revocation itself is `A3`/`0004`, out of scope.
- **Does anything become visible to a principal who could not see it before?** No — identities are
  digests (A5), and the surface is host-side audit, not model-facing.

---

## 4. Behaviour — the mechanical contract (v3, design-complete)

> **The invariant (a sibling of `0002`'s maintenance-provenance-invariant), CONSULT-AND-DISCARD
> keyed — research's sharpening, 2026-08-08.** *Every maintenance operation that **consults** a
> contributor record and then **discards, merges or invalidates** it MUST leave a durable,
> queryable **contribution record** naming (i) the survivor, (ii) the contributor's opaque source
> identity, and (iii) a **TOTAL, store-derived payload** (v8: the per-site closed schemas —
> base+contributor at absorption, the input's own values at consolidation; a no-op transfer is
> visible IN the recorded values, and `{}` is an integrity error) — **whether or not any of the
> survivor's values changed.***
>
> **Why keyed on the operation, not the transfer (measured).** Run an absorption with the
> contributor OLDER and WEAKER: `max()` moves nothing, the survivor's `observed_at`/`confidence`
> are unchanged — and the contributor still vanishes. A *transfer*-keyed rule need not record that,
> yet "which sources support this fact?" omits it and any blast radius under-reports. It is not
> tidiness: an attacker contributes **invisibly** simply by ensuring no `max()` moves, so
> stale-but-corroborating input becomes the unlogged path. The record is owed to the **act of
> consuming a contributor**, and the value change is only its payload.

### 4a. The ledger — one `SCHEMA_VERSION` v6 table (additive, content-free, user-linked)

```
contribution_ledger(
    id              TEXT PRIMARY KEY,     -- store-minted 'contrib-<uuid>'
    user_id         TEXT NOT NULL,        -- tenant scope; forget_user deletes by this
    survivor_type   TEXT NOT NULL,        -- 'edge' | 'episode' (R1-5: the two id namespaces
                                          --   are independent; an Edge and an Episode may
                                          --   legally share a raw id — reads and A10 deletion
                                          --   key on (user_id, survivor_type, survivor_id))
    survivor_id     TEXT NOT NULL,        -- the record that consumed the contributor
    site            TEXT NOT NULL,        -- 'absorption' | 'consolidation' — the CLOSED site
                                          --   set (validated; reinforcement is NOT a site —
                                          --   0012 Design 1; no 'severed' — §4f, the round-1
                                          --   ruling retains frozen point 5 with no tombstone)
    identity_digest TEXT,                 -- 0006 source_identity_digest(resolve(origin, source_id)); NULL iff source_id absent (unknown source — 0006 §4 rule 8, F1)
    evidence_ref_digest TEXT,             -- evidence_ref_digest(origin, evidence_ref) — §4a
                                          --   below (R1-8); NULL iff evidence_ref absent
    payload         TEXT NOT NULL,        -- the CLOSED per-site schema below (R1-8);
                                          --   STORE-derived (R2-1); TOTAL at every site
                                          --   (v8 — an empty payload aborts)
    op_key          TEXT,                 -- consolidation retry identity (R2-2):
                                          --   "<operation_id>:<output_index>:<ctype>:<cid>";
                                          --   NULL for absorption (rides 0003's receipt)
    created_at      TEXT NOT NULL
)
INDEX ix_contribution_ledger_survivor (user_id, survivor_type, survivor_id)
INDEX ix_contribution_ledger_source   (user_id, identity_digest) -- revoke_source's blast-radius join
UNIQUE INDEX ix_contribution_ledger_op_key (op_key) WHERE op_key IS NOT NULL  -- R2-2
```

**The evidence-reference digest is its OWN domain-separated construction (R1-8)** — "digest it the
same way" was not a construction: `source_identity_digest` takes a resolved pair under the
source-identity domain. Frozen, byte-exact (R2-5): `evidence_ref_digest = SHA-256( b"veracium.evidence-ref.v1" ||
u32be(byte_len(utf8(origin))) || utf8(origin) || u32be(byte_len(utf8(evidence_ref))) ||
utf8(evidence_ref) )` — UTF-8 encoding, 32-bit big-endian length prefixes, over the RESOLVED
origin (the §4.6 resolution) — origin-scoped so equal host strings in different stores never
collide. **The absence rule, complete:** `Provenance.evidence_ref` is a required field that
PERMITS `""`; the digest is **NULL iff `evidence_ref == ""`** — the empty string is DEFINED as
absent (stated, not implied), and a non-empty ref always digests. Never a digest over empty
input.

**The payload is a CLOSED, per-site, recursively-validated schema (R1-8) — never arbitrary JSON**
(arbitrary JSON cannot carry A5's content-free guarantee). The store VALIDATES on write,
fail-closed (an invalid payload aborts the whole maintenance transaction, A7):

- *absorption (R4-1 — one incoming may absorb SEVERAL priors, so a single pre→post diff
  cannot support arbitrary contributor removal; the reviewer's 0.2-absorbs-0.8-and-0.9 case):*
  each per-contributor row carries `{"base": {<name>: <v>}, "contributor": {<name>: <v>}}` —
  `base` = the plan's `absorption_pre_image` (the incoming's original values, identical across
  the op's rows) and `contributor` = THAT absorbed prior's own values, read from its
  authoritative row (which the store already reads for identity). REVERSAL IS RE-COMPUTATION
  (the same model as consolidation): remove contributor X's row, re-apply the absorption
  inheritance rules over `base` + the remaining contributors' recorded values (revoking the
  0.9 contributor recomputes `max(0.2, 0.8) = 0.8`, never a false restoration to 0.2). Mandatory
  keys per side: `observed_at`, `confidence`, `valid_from`, `disclosure`; `derived_from` is
  OMITTED when its underlying value is None — never encoded as `null` (canonical form: sorted
  keys, omitted-if-absent — this exact form feeds the receipt digest and the op-key conflict
  comparison). **An empty payload is VALID NOWHERE under this shape (the checklist pass caught the v7
  contradiction):** the A1 no-transfer case records base and contributor values like any
  other — the recorded values themselves SHOW that nothing moved, which is strictly more
  informative than an empty payload; A1's consult-and-discard principle is carried by the
  TOTAL payload, not by emptiness.
- *consolidation (R4-6 — the EXACT schema; an `Episode` HAS no `valid_from`):*
  `{"input": {<name>: <v>}, "output_index": <int>}` with MANDATORY input keys
  {`observed_at`, `confidence`, `disclosure`, `author_of_evidence`, `date`} and
  `derived_from` OMITTED when None (never `null`); `valid_from` is NOT in the consolidation
  set — it is an Edge field, and consolidation inputs are Episodes. TOTAL — never `{}` here.
  Canonical form: sorted keys, omitted-if-absent — deterministic for digesting, validation,
  recomputation, and conflict comparison alike.
- **Payloads are TOTAL at BOTH sites; `{}` is an integrity error everywhere** (v8, via the
  pre-send checklist): absorption records base+contributor always (the no-transfer case is
  visible IN the values — R4-1's shape made emptiness redundant and contradictory);
  consolidation records every input's values + `output_index` (R2-4). The store derives all of
  it, so any empty payload signals a derivation failure and aborts (A7).

**Append-only** — a row is INSERTed, never UPDATEd or REPLACEd. **Content-free** by the 0003
discipline: the only identity fields are digests (§2/A5); `payload` carries scalar field names and
their prior/new timestamp/float/enum values (store-clear, Q1), never `object`/`note`/`summary`.
`identity_digest` is `0006`'s shared `source_identity_digest(resolve(origin, source_id))` primitive
(`0006` §4 rule 7 / I12 — ONE canonical, length-framed, domain-separated construction; `0014` and
`revoke_source` call the SAME primitive so they re-derive an identical key). It is **NULL when the
contributor has no `source_id`** (`0006` §4 rule 8 / I13 — unknown source, recorded but not
groupable/revocable; never a `(origin, NULL)` pseudo-source). The resolution `0006` §4.6 mandates
happens before the digest, so `revoke_source` (which digests the same resolved pair) joins on
`ix_contribution_ledger_source`. `payload` is TOTAL at every site (v8 — the base+contributor/input shapes always carry
values; A1's no-transfer case is visible IN the recorded values, and `{}` aborts as a
derivation failure).

### 4b. `ContributionDraft` — what a site emits

A site hands the store a `ContributionDraft(site, survivor_type, survivor_id,
contributor_type, contributor_id)` — **references ONLY; there is NO caller-supplied payload
(R2-1).** The STORE, inside the same transaction and BEFORE the contributor row is
deleted/invalidated: reads the referenced contributor row (identity →
`identity_digest`/`evidence_ref_digest`; values → the consolidation payload), derives the
absorption payload per the pre-image rule below, mints the ledger id and `created_at`, and
INSERTs. Every payload value is store-derived from authoritative material; the closed §4a schema
is what the store PRODUCES, validated as a self-check, never a caller contract. A draft whose
`contributor_type`/`contributor_id` does not resolve to a row this transaction is consuming — or
resolves to another tenant's row — is an integrity error: the whole op aborts (A7). **And the
draft set must be COMPLETE (R5-1 — rejecting bad drafts does not catch MISSING ones):** at
absorption the store requires EXACT SET EQUALITY between the plan's contribution drafts and the
plan's `absorbed_duplicate` invalidations — one draft per absorbed prior, no omissions, no
duplicates, no extras (the reviewer's case: consuming 0.8 AND 0.9 while drafting only the 0.9
passes the semantic recompute yet loses the 0.8 attribution — set equality catches it where value
verification cannot). At consolidation the same rule binds drafts to the claimed input set × the
written outputs (N×M, already exact by construction at the cutover). Each violation aborts;
omitted, duplicated, and extra drafts are each a named A7 injection case.

**Receipt identity is REQUEST-STABLE; outcome verification is a DIFFERENT phase at a
DIFFERENT layer (R5-2 + R6-1 — the two rules are compatible because they never see the same
retry):** the construction, exactly:

- **Phase 1 — PUBLIC pre-plan receipt lookup (`apply_supersession`), THREE branches
  (R10-2 — a two-branch phase 1 made the promised phase-2 outcome comparison UNREACHABLE:
  for both legal NULL receipt states the computed public digest trivially "differs" from
  NULL, so every legacy or snapshot-less retry would conflict before planning).** BEFORE
  any planning, the public entry point computes the **request digest** over the RAW
  submitted edge and looks up the receipt by op_id:
  1. receipt exists, stored `request_digest` NON-NULL and MATCHES → **REPLAY the recorded
     response; NO re-planning occurs** — the post-commit re-plan (the reviewer's O2) is
     never computed, so no outcome comparison can reject a legitimate lost-response retry;
  2. receipt exists, stored `request_digest` NON-NULL and DIFFERS →
     `SupersessionIntegrityError` (a truly different resubmission reusing an op id);
  3. receipt exists, stored `request_digest` NULL (BOTH legal NULL forms — legacy
     version-1 and new snapshot-less version-2) → **request identity UNAVAILABLE, never
     "different": continue to planning and phase 2**, where the version-selected outcome
     comparison governs (§ the receipt-state triple). No receipt → plan and proceed.
  Named tests: a public retry against a LEGACY (NULL, 1, NULL) receipt reaches phase 2 and
  replays/conflicts by the v1 outcome rule; a public retry against a NEW snapshot-less
  (NULL, 2, json) receipt reaches phase 2 and verifies at the v2 projection.
- **Phase 2 — STORE-LEVEL verification (`apply_supersession_plan`), REQUEST-FIRST where
  request identity exists (R8-1).** On a receipt hit, the store's FIRST comparison is by
  REQUEST whenever both sides carry request identity — the receipt's stored `request_digest`
  is non-NULL and the submitted plan carries `raw_request` (from which the store derives the
  digest itself, §4b): **matching request → REPLAY the persisted effects as `replayed=True` (R10-1), the submitted
  plan's re-planned outcome DISCARDED unconsulted** — this is where the concurrent-preflight
  loser lands (both racers pass phase 1 before either commits; the loser re-plans against
  post-commit state and its legitimately-different outcome O2 must not be compared, or the
  public replay defect returns under a race); **differing request →
  `SupersessionIntegrityError`.**

  **The replayed response is DURABLE, never reconstructed (R9-1 — "replay the recorded
  response" was unimplementable as written: the receipt stored only digests + status, and
  the pre-split implementation reconstructs `SupersessionResult` fields — `inserted_incoming`,
  `invalidated`, `refused` — from the SUBMITTED plan, which request-first replay has just
  discarded; O1's `invalidated=1` is unrecoverable from O2's plan):** the receipts table
  gains `response TEXT` — the canonical JSON of the committed op's **EFFECT PAYLOAD: every
  `SupersessionResult` field EXCEPT `replayed`** (edge/episode ids and counts only;
  content-free), written ATOMICALLY with the receipt. **The runtime flag is EXCLUDED by
  construction (R10-1 — the shipped model marks `replayed` "runtime only … not a persisted
  column" (`schema.py:106`), and persisting the original's `replayed=False` while promising
  to return it exactly would contradict the contract that a replayed result carries
  `replayed=True`):** replay CONSTRUCTS its result as the persisted effect fields +
  `replayed=True` — effect identity from the durable carrier, runtime provenance from the
  call. Legacy receipts (`response` NULL after migration) never reach request-first replay
  (their `request_digest` is also NULL); their outcome-match replay keeps the pre-split
  reconstruct-from-plan behaviour, which is SOUND there because a matching outcome digest
  proves the submitted plan IS the recorded plan. Named test:
  `test_replay_returns_the_persisted_result_not_a_reconstruction` — the O1/O2 race with
  O1.invalidated=1, O2.invalidated=0: assert O1 and O2 differ in their EFFECT fields, the
  replay's effect fields equal O1's exactly, AND the replay carries `replayed=True` where
  O1 carried `False` (effect equality + the flag flip — never whole-object equality).

  **The outcome digest** (everything the pre-split digest
  bound + this spec's contributions and pre-image) governs ONLY receipts/plans WITHOUT
  request identity — legacy NULL-`request_digest` receipts and snapshot-less store-level
  plans — where the contribution-field-mutation check remains reachable by construction
  because such callers submit plans, not raw edges.

  **The digest PROJECTION is durably discriminated (R9-2 — NULL `request_digest` cannot
  identify it: a MIGRATED receipt is NULL with the PRE-SPLIT outcome projection, and a
  NEW snapshot-less store-level receipt is ALSO NULL but with the EXTENDED projection
  (contributions + pre-image); comparing the extended projection against a legacy receipt
  breaks legitimate legacy replay, and comparing the pre-split projection against a new
  receipt lets a caller mutate contribution fields undetected):** the receipts table gains
  the version column via the FROZEN EXECUTABLE DDL (R10-3 — bare `ADD COLUMN … NOT NULL`
  is REJECTED by SQLite on a non-empty table, the reviewer reproduced the
  `OperationalError`): **`ALTER TABLE supersession_operations ADD COLUMN
  outcome_digest_version INTEGER NOT NULL DEFAULT 1`** — the DEFAULT 1 both makes the
  ALTER executable on populated tables AND IS the migration stamp (every pre-upgrade row
  = 1, the pre-split projection); the v6 CONSTRUCTOR carries the IDENTICAL `DEFAULT 1` in
  its own DDL; and every post-upgrade write stamps `2` EXPLICITLY (never relying on the
  default). **AUTHORIZATION is `0013` §4e's MANIFEST SET, not digest identity (R11-1 —
  v14 wrongly claimed matching defaults make fresh-v6 and migrated-v5 stores
  digest-identical, and cited a "first-ALTER treatment" that accepted `0013` §4c-deferred
  EXPLICITLY DEFERS to its own future review round; the present contract, §5/§5c, is
  exact constructor identity + recorded path evidence, and §4e already states the ALTER
  case: "a constructor and an ALTER path legitimately produce different stored DDL," so
  `MANIFESTS[v]` is a SET):** `MANIFESTS[6]` carries BOTH exact DDL texts byte-for-byte —
  (a) the fresh v6 constructor's `sqlite_master.sql`, and (b) the v5-constructor +
  three-ALTER path's — per accepted `0013` §4e/§5c, with per-path evidence
  (`v5:constructor->v6` alongside the constructor entry).

  **The ALTER-path expectation is PREDECLARED IN THIS SPEC, reviewed HERE, never
  regenerated from the migration (R12-1/R13-1 — `0013` §4c: "a migration may not define
  its own destination"; v16 deferred the literal to "at implementation", which this
  review could not authorize, and the cited semantic rule alone was underdetermined —
  the reviewer measured that 3.45.1 inserts the columns BEFORE the table-level
  `PRIMARY KEY`, on its preceding line, a byte layout no append-rule prose determines):**
  the reviewed expected stored DDL for `supersession_operations` after the three ALTERs,
  ON THE QUALIFIED RUNTIME (SQLite 3.45.1, the runtime the shipped evidence records), is
  EXACTLY this literal — authored empirically on 3.45.1 during this revision,
  confirming the reviewer's measured layout, and authorized by THIS review as content:

  ```sql
  CREATE TABLE supersession_operations (
      user_id TEXT NOT NULL, operation_id TEXT NOT NULL,
      logical_request_digest TEXT NOT NULL, status TEXT NOT NULL, request_digest TEXT, response TEXT, outcome_digest_version INTEGER NOT NULL DEFAULT 1,
      PRIMARY KEY (user_id, operation_id)
  )
  ```

  (The fenced display carries a UNIFORM two-space block indent for this document's
  layout; the FROZEN BYTES are the display minus that offset — first line
  `CREATE TABLE supersession_operations (`, inner lines with their four-space indent
  exactly as v5's evidence records the constructor text, no trailing newline — with
  sha256 `326ea1938cd8f623093b655c61c4c10a46087ccaee5a8687061d8ef2572c3dc0` over those
  exact stored bytes; the digest is the tie-breaker if any rendering ambiguity is
  suspected.) The three new column definitions sit appended, in ALTER order, at the
  end of the `status` line, BEFORE the table-level `PRIMARY KEY` — the reviewer's
  measured 3.45.1 behaviour, now the reviewed expectation. This literal + digest enter
  the v6 evidence registry VERBATIM at implementation; they enter `accepted_digests` by
  THIS review, not by execution. The migration must PRODUCE a byte-match to the
  pre-declared literal: a mismatch means THE MIGRATION (or an unqualified runtime) IS
  WRONG — the expectation never moves to meet the output. NOTHING relies on the
  deferred structural-capability model.
  Named migration test (R10-3/R12-1): `test_v5_to_v6_migrates_a_nonempty_receipt_table`
  — a v5 store with existing receipt rows migrates; every pre-existing row reads
  version 1 / NULL response; a post-migration write reads version 2; and the final
  `sqlite_master.sql` byte-matches the PRE-DECLARED reviewed expectation (never
  compared against anything regenerated from the run). Replay comparison selects the
  projection BY THE STORED VERSION, never by NULL-ness of anything.

  **The receipt-state space is CLOSED, enumerated, and EXHAUSTIVELY EXECUTABLE (R10-4 —
  declaring three legal cells without a table-driven check leaves (digest,1,NULL),
  (NULL,2,NULL), version 0/3, and malformed responses unexercised):** (request_digest,
  outcome_digest_version, response) ∈ {(NULL, 1, NULL) legacy; (NULL, 2, json) new
  snapshot-less; (digest, 2, json) new with snapshot} — any other combination is an
  integrity error at write AND at read. Named test:
  `test_receipt_state_triple_is_closed` — TABLE-DRIVEN over every legal cell (write
  accepted, read round-trips, response deserializes into valid effect fields) and the
  illegal representatives: (digest, 1, NULL), (digest, 1, json), (NULL, 2, NULL),
  (digest, 2, NULL), version 0 and 3, non-JSON `response`, and JSON with
  missing/invalid effect fields — each REFUSED at write AND flagged at read. Plus the
  digest-behaviour tests: a legacy receipt with a MATCHING
  pre-split-projection plan replays; a legacy receipt with a conflicting plan conflicts;
  a NEW snapshot-less receipt with a contribution-field mutation CONFLICTS (the v2
  projection sees it).

  The phases compose without contradiction
  BECAUSE phase 2 is request-first: a public retry is normally settled at phase 1; the race
  that slips both callers past phase 1 is settled at phase 2 by the SAME request-stable rule
  — replay on match, never an outcome conflict. Named test (REQUIRES replay, does not permit
  conflict): `test_concurrent_public_preflight_loser_replays` — T1/T2 submit identical
  request R; T1 commits O1; T2's phase-2 hit returns O1, discards its own O2, never
  double-applies.

**The request identity is DERIVED BY THE STORE from an authoritative raw-request carrier —
never a caller-supplied digest (R7-1: a caller-constructible digest lets a store-level caller
bind outcome A to request B, making a later public submission of B falsely replay).**
`SupersessionPlan` carries `raw_request: Optional[dict]` — the CANONICAL SNAPSHOT of the raw
edge as submitted: **the COMPLETE `Edge` model dump in JSON mode — EVERY field including
defaults, `None` serialized as JSON `null` (this construction is total, so null-vs-omitted
ambiguity cannot arise — the exception R7-3 carved for the episode field does NOT apply
here), keys sorted recursively** — captured by the PUBLIC entry point BEFORE planning; there is NO `request_digest` field on the plan.

**The snapshot is COMPLETELY BOUND by an exhaustive field partition (R8-2 — comparing only
id/user/subject/relation plus the R4-2 recompute leaves every non-inherited field free, and a
forged snapshot differing only in `evidence_ref`, `source_id`, `note`, `volatility`, or an
outcome counter would recreate the outcome-A/request-B binding).** The store verifies the
snapshot against the plan's incoming edge under a partition that assigns EVERY `Edge` and
`Provenance` field to exactly one class:

- **EXACT-EQUAL (the planner never transforms these — byte-for-byte equality with the plan's
  incoming):** `id`, `user_id`, `subject`, `relation`, `object`, `note`, `volatility`,
  `needs_confirmation`, and `provenance.{source_type, author_of_evidence, evidence_ref,
  disclosure, derived_from, source_id, origin}`. **`needs_confirmation` is EXACT-EQUAL,
  not recomputed (R9-4 — v12 misclassified it: the shipped absorption inherits EXACTLY
  `valid_from`/`observed_at`/`confidence` (`graph.py:163-167`) and never touches
  `needs_confirmation`; "never cleared by dedup" means dedup does not TOUCH it, not that
  it is transformed. A recompute-from-contributors could flip an incoming `False` to
  `True`, changing shipped maintenance behaviour against §8's no-decision-change claim).**
- **RECOMPUTED (EXACTLY the three fields the shipped C′ absorption inherits —
  `graph.py:163-167` — and exactly §4b's pre-image field set):** `valid_from` (min),
  `provenance.observed_at` (max), `provenance.confidence` (max) —
  verified through the R4-2 semantic recomputation: from the snapshot's values plus the
  recorded contributors, the committed survivor's values must be reproduced.
- **FORBIDDEN on a new request (store-lifecycle fields a raw submission cannot carry):**
  `invalidated_at`, `invalidation_reason`, `supersedes`, `last_outcome`, `last_outcome_at`
  non-None, `times_used` non-zero, `outcome_counts` non-empty → the op aborts.

Any exact-equal mismatch, recompute failure, or forbidden-field presence → abort. The
partition is TOTAL and mechanically pinned: `test_raw_request_field_partition_is_total`
enumerates `Edge.model_fields` + `Provenance.model_fields` and asserts every field is
assigned to exactly one class — a future model field breaks the test until it is
classified. `test_every_snapshot_field_binds_the_digest` is the field-by-field mutation
oracle: mutate each field of a fixture snapshot in turn and assert the digest changes —
every field provably bound, none free for forgery.

**The binding is proven at the STORE, not only at the digest (R9-3 — the two tests above
prove every field has a LABEL and every field moves the HASH; neither proves the store
COMPARES every field with the plan. A verification that accidentally omits `object` would
commit a plan-for-A under snapshot-B's digest, and a later public request for B would
falsely replay A — with both v12 oracles green):**
`test_every_snapshot_field_mismatch_aborts_the_plan` iterates the SAME field enumeration
the totality test pins (`Edge.model_fields` + `Provenance.model_fields` — one source, no
second list to drift) and, per field: EXACT-EQUAL → submit a snapshot differing from the
plan's incoming in that field alone; RECOMPUTED → a value from which the recompute cannot
reproduce the committed survivor; FORBIDDEN → the field present/non-default — and asserts
`apply_supersession_plan` ABORTS for every single one. A field the store forgets to compare
fails its cell loudly.

The store then (b) computes the request digest ITSELF — frozen construction, EXACT BYTES
(R8-2 — "canonical JSON, sorted keys, UTF-8" alone lets two implementations hash a non-ASCII
edge differently and turn a valid retry into a conflict after an upgrade):
`SHA-256(b"veracium.supersession-request.v1" || bytes)` where `bytes` is the UTF-8 encoding
of `json.dumps(snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
allow_nan=False)` over the model dump in JSON mode — recursively sorted keys at every object
level; NO whitespace (the separators are frozen); non-ASCII characters as raw UTF-8, never
`\\uXXXX` escapes; datetimes as the ISO-8601 strings the JSON-mode dump emits (with explicit
UTC offset); enums as their value strings; `None` as `null`; integers as decimal literals;
floats as shortest-round-trip repr; NaN/±Infinity are unencodable and abort. The
implementation ships FROZEN DIGEST VECTORS as named tests
(`test_request_digest_frozen_vectors`): at least two complete snapshot fixtures — one ASCII,
one containing non-ASCII text, a float, and a datetime — with their exact digest hex pinned
as constants, so any serialization drift fails loudly rather than conflicting in production.
(The §2c matrix row: absent snapshot → phase-2 semantics only / NULL digest;
malformed or plan-inconsistent snapshot → the op aborts; a snapshot for a DIFFERENT edge →
abort.) Phase 1's lookup digests the raw edge it was handed directly — same construction,
same derivation, no caller assertion anywhere. Adversarial tests: a forged snapshot
(mismatching the plan) aborts; a malformed snapshot aborts; CONCURRENT PREFLIGHT — two
racing public submissions of the same raw edge: one commits; the loser is settled at
phase 2 by the REQUEST-FIRST rule (R8-1) — matching `raw_request` → REPLAYS the committed
outcome (its own post-commit re-plan discarded, never compared), never conflicts, never
double-applies. Outcome-only comparison at phase 2 is reserved for receipts WITHOUT request
identity (legacy NULL / snapshot-less store-level plans).

**Durable and upgrade carriers (R6-2, extended R9-1/R9-2, DDL frozen R10-3):** the receipts
table gains THREE
columns — nullable `request_digest TEXT` (R6-2), nullable `response TEXT` (R9-1 — the
persisted EFFECT payload: `SupersessionResult` minus the runtime `replayed` flag, R10-1),
and `outcome_digest_version INTEGER NOT NULL DEFAULT 1`
(R9-2/R10-3 — the DEFAULT both makes the ALTER executable on populated tables and IS the
migration stamp; new writes stamp 2 explicitly) — ALL part of the SAME v5→v6
migration as the ledger table (the §7a schema summary lists every one; the ALTER-path
manifest joins `MANIFESTS[6]` per accepted `0013` §4e, its evidence recorded per path —
R11-1); the stored request digest
is ALWAYS store-computed from the raw-request
snapshot (R7-1). **Legacy receipts (request_digest NULL, response NULL, version 1 after
migration):** the raw request is NOT
reliably reconstructible post-commit, so no request digest is backfilled — a legacy-receipt
op_id hit replays IFF the VERSION-1 outcome digest matches (the pre-split semantics, preserved
honestly: the R5-2 replay defect HEALS FORWARD for receipts written after the upgrade and is
NOT retroactively fixed; stating otherwise would fabricate identity). Adversarial tests: a
reused op_id with a different request on a NEW receipt (conflict), on a LEGACY receipt
(outcome-digest rule), and the public lost-response replay on a new receipt (replays).

**The absorption pre-image (R3-1 — the survivor's pre-state does not otherwise EXIST):** at
absorption the survivor IS the incoming edge — a NEW row whose fields the planner has already
mutated by inheritance (EXACTLY `valid_from = min`, `observed_at = max`, `confidence = max` —
the shipped C′ set, `graph.py:163-167`; nothing else transfers, R9-4) before the store ever sees
it, so there is no "row as read" to diff against, and two different pre-images can yield
byte-identical plans (the reviewer's 0.1/0.2-into-0.9 reproduction). Rule:
`_build_supersession_plan` SNAPSHOTS the incoming edge's original scalar values over the closed
field set BEFORE any inheritance mutation, onto a new plan field
`absorption_pre_image: dict[field, scalar] | None` (plan-transient — never persisted as such;
canonical key order). The store derives the absorption payload as `prior` = the pre-image value,
`new` = the incoming edge as written — both authoritative — and **the pre-image ENTERS the
OUTCOME digest of `0003`'s split receipt (R5-2/R6-1)** (closing the byte-identical-plans replay hole at its root; part of
the same marked `0003` amendment). A plan carrying absorption contributions with a missing or
field-incomplete pre-image is an integrity error: the op aborts (A7). **And the pre-image is
SEMANTICALLY verified, not merely receipt-bound (R4-2 — hashing a false claim only makes it
stable):** the store RECOMPUTES the expected post-image — the absorption inheritance rules
applied to the pre-image plus the authoritative contributor rows it reads — and compares it
EXACTLY to the survivor as committed; any mismatch (the reviewer's 0.95-pre/0.9-committed case,
where `max()` must preserve 0.95) aborts the whole op. A pre-image that survives both the
schema check and the recompute-compare is consistent with everything authoritative by
construction.

**Survivor binding is PER SITE (R3-2 — one rule cannot serve both):** at ABSORPTION the survivor
must be a record the SAME commit writes (the CAS plan's incoming edge). At CONSOLIDATION the
outputs were legitimately committed EARLIER as provisional rows, so the cutover-transaction rule
is: the survivor must be an EXISTING PROVISIONAL output row correctly bound to THIS operation —
same `operation_id`, current fence, `lineage` = the claimed set, and the store-assigned persisted
output identity (§4c) — anything else (missing, non-provisional, foreign-op, unbound) is an
integrity error: the transition aborts.

### 4c. The write path — one commit with the maintenance op it attributes (atomic, per site)

The record MUST commit in the SAME transaction as the maintenance op, or a crash leaves a
consumption with no record (or a record for a consumption that rolled back). Each site already has an
atomic carrier; the draft rides it:

- **3.3 absorption** → `SupersessionPlan` (specs/0003 §4f) gains a
  `contributions: list[ContributionDraft]` field. `graph._build_supersession_plan` populates it (one
  draft per absorbed prior, referencing the absorbed row by type+id), and `apply_supersession_plan`
  derives+INSERTs inside its existing single-commit CAS transaction. **The contributions ENTER
  the OUTCOME digest of `0003`'s split receipt (R1-3, as re-shaped by R5-2's request/outcome
  separation — a marked amendment on accepted `0003`): the round-1 counterexample killed the
  "derivable" reading — two absorptions with different pre-transfer `observed_at` values can
  yield byte-identical final plans while their required base values differ, so an outcome
  record must bind the contributions explicitly. The OUTCOME digest binds each contribution's
  complete outcome (site, survivor type+id, contributor type+id, the store-derived canonical
  payload — R2-1 removed caller payloads) alongside everything it already binds; REPLAY
  identity is the separate REQUEST digest over the raw submitted edge (R5-2, §4b).**
  Absorption keeps its `note` for back-compat but the LEDGER is the queryable path (A3).
  *(Reinforcement — the former 3.1 — is `0012`'s: it persists the edge, which is the attribution.)*
- **3.2 consolidation — the relation is INPUT × OUTPUT (R1-1), inserted atomically AT the
  VISIBILITY CUTOVER (R2-3), with a PERSISTABLE unique retry key (R2-2).** A consolidation may
  write SEVERAL outputs, and `0010` X8 binds EVERY output's `lineage` to the WHOLE claimed set —
  attribution is the full cross product: M outputs × N claimed inputs = **N×M rows**, each output
  enumerating every contributor (A2/A4).
  **WHERE the rows commit (R2-3 — `0010` has no single op-wide transaction):** output writing
  commits provisional episodes SEPARATELY from cutover, so inserting rows at output-write time
  could leave durable ledger rows for a consumption that never completes. The rows therefore
  INSERT in the SAME SQLite transaction as the **`OUTPUTS_DURABLE` cutover transition**
  (`transition_consolidation_if_current` — a marked additive amendment on accepted `0010`, §7b):
  at that point every output and its index is known, the claimed inputs STILL EXIST (deletion is
  X2-later), and the transition is the op's point of no return. Crash BEFORE the transition → no
  rows exist, and `0010`'s abandonment path has nothing to clean (specified: pre-cutover
  abandonment touches no ledger state). Crash AFTER → the rows are durable AND `0010` X2/X13
  recovery rolls the op FORWARD to completion — rows and consumption stay consistent. The
  ledger-write failure aborts the transition itself (A7).
  **The output identity is STORE-ASSIGNED and PERSISTED — as an `Episode` MODEL FIELD (R5-3,
  the reviewer's simpler-fit ruling adopted; the v8 SQL-column form is WITHDRAWN — episodes
  persist as `(id, user_id, date, json)` and a parallel column would need DDL, ALTER, JSON
  synchronization, and `0013` first-ALTER treatment the spec never provided):** `Episode` gains
  `consolidation_output_index: Optional[int] = None`, serialized inside the existing `json`
  blob like every other Episode field — ONE authoritative representation, NO DDL OF ITS OWN
  (R9-6: the Episode field adds none; the migration's DDL — the ledger table + indexes AND
  the separate receipts ALTERs, §7a — exists regardless of this field and is not contradicted
  here), no synchronization boundary. `write_consolidation_output_if_current`
  ASSIGNS it (the count of outputs already written for this operation, sequential from 0) and
  sets it on the output episode it writes. The Store signature becomes
  `write_consolidation_output_if_current(operation_id, fence, owner, draft) -> Optional[int]` —
  the assigned index on success, **`None` on fence loss — and index 0 is FALSEY, so every
  consumer must test `is None` / `is not None`, never truthiness (R5-5)**;
  `ConsolidationOutputDraft` does NOT carry an index. Finalization leaves the field untouched
  (immutable once written). Generic episode inserts/imports VALIDATE it (int ≥ 0 or absent).
  PORTABILITY: the field exports with the episode — see the FORMAT_VERSION rule below (R5-4).
  **Conflict comparison is over the DETERMINISTIC fields only (R4-3):** `(user_id,
  survivor_type, survivor_id, site, identity_digest, evidence_ref_digest, canonical payload,
  op_key)` — the store-minted `id` and `created_at` are EXCLUDED (a literal full-row comparison
  would reject every true retry). A match on all deterministic fields = idempotent no-op;
  any deterministic-field mismatch aborts.
  **The retry key is PERSISTED and uniquely constrained (R2-2), and a conflict VERIFIES, never
  ignores (R3-3):** the ledger gains a nullable `op_key TEXT` column — canonical
  `"<operation_id>:<output_index>:<contributor_type>:<contributor_id>"` for consolidation rows,
  NULL for absorption (which rides `0003`'s CAS/receipt idempotency) — with
  `UNIQUE INDEX ix_contribution_ledger_op_key ON (op_key) WHERE op_key IS NOT NULL`. On a key
  conflict the store READS the existing row and VERIFIES it matches the row it would have
  written, field for field (survivor, digests, payload): a true retry is an idempotent no-op —
  **append-only preserved (A8)** — and ANY mismatch is an integrity error aborting the
  transition (a silent DO NOTHING would let a mis-keyed second output lose its attribution
  invisibly — the fail-open the reviewer named). A takeover under a NEW fence follows `0010`'s
  recovery rules; the op_key is fence-independent, so a recovered op's rows are found and
  verified, not duplicated.
  **The payload is STORE-DERIVED from each input (R1-4 + R2-4), TOTAL — `{}` is NOT legal at
  consolidation:** `{"input": {observed_at, confidence, disclosure, derived_from?,
  author_of_evidence, date}, "output_index": i}` — `author_of_evidence` (closed enum) because
  recomputing `third_party_influenced` requires it; the episode `date` because output date
  ranges derive from it. Reversal is RE-COMPUTATION: drop the revoked contributor's rows,
  re-derive every reduction (trust floor, min confidence, weakest disclosure, influence,
  date range) over the remaining recorded inputs — the recorded set is sufficient by
  construction. §7/§8's reversibility claim is stated in exactly those terms.

**Failure rule (mirrors 0003 §4f):** if the maintenance op rolls back, its ledger rows roll back with
it — no partial state. A site that cannot emit atomically MUST NOT perform the consumption.

### 4d. The reads (Store-local, the exact queries the consumers need)

- `contributions(user_id, survivor_type, survivor_id) -> list[ContributionRecord]` — every
  contributor consumed into a survivor, newest first (type-keyed, R1-5 — an Edge and an Episode
  sharing a raw id never merge). The "why is this fact live?" audit (§1) and A4.
- `contributors_of_source(user_id, identity_digest) -> list[ContributionRecord]` — every survivor a
  source contributed to. **`revoke_source`'s blast-radius join** (`A3`) — given a `(origin, source_id)`
  to revoke, it resolves+digests and calls this. Read-only; `0014` computes no blast radius itself.

### 4e. Erasure and portability (Store-local metadata, like the 0003 refusal inventory)

`forget_user` deletes the user's ledger rows (A6). Export/import EXCLUDE it — a contribution is a
fact about *this store's* maintenance history, not the memory; importing one would assert a
consumption that never happened here. The ledger itself forces no format change; the `Episode.consolidation_output_index` field DOES — `FORMAT_VERSION` 4→5 (R5-4, §7a).

**Explicitly OUT of scope (the decoupling):** actually reversing a transfer, computing a source's
blast radius, and making a revocation reach recall — those are `A3` / `0004`. `0014` guarantees the
record exists, is atomic with the consumption, and is queryable by the two reads above; acting on it
is theirs.

---

### 4f. The transitive gap — RESOLVED round 1: frozen point 5 retained; transitive handling is a
### named PREREQUISITE for any future severance-capable site

**RESOLVED — the round-1 ruling (reviewer, 2026-08-10): FROZEN POINT 5 IS RETAINED for v1;
there is NO tombstone.** The reviewer's grounds, accepted in full: (i) the proposed tombstone was
not mechanically viable — its join could not identify the deleted survivor (`identity_digest` is a
many-to-one SOURCE key and may be NULL; the payload carried no lineage field), the `severed` site
was absent from §4a's closed set, A5's grammar had no tombstone shape, and the reads had no
structured incomplete status; (ii) **the B→C severance path is PRESENTLY UNREACHABLE** — accepted
`0010` excludes consolidation outputs from later consolidation, so no v1 site can consume a
survivor that itself has contributors. **The standing REQUIREMENT this ruling creates:** any
future spec that adds a consumption site capable of consuming a survivor-with-contributors MUST
first land transitive handling (with typed contributor-record links and a defined query-result
status) as a named prerequisite — recorded in §7, §8, and the A4 site registry, so the gap cannot
arrive silently. The candidate text below is retained as REJECTED-FOR-V1 history.*

The gap, for the record: `source A → survivor B → consolidation into survivor C` — B's
hard-deletion would drop the `(survivor=B, contributor=A)` rows (A10), making A undiscoverable
from C. **In v1 this state is UNREACHABLE** (accepted `0010` excludes consolidation outputs from
re-consolidation), which is a ground of the ruling.

> *Historical, REJECTED — no clause below is normative (R3-5).* The v4 candidate proposed a
> severance tombstone (`site='severed'`, a deleting-transaction row retained by the downstream
> survivor, "incomplete: N links severed" reads) with a retain-more alternative rejected outright.
> The round-1 review found the tombstone not mechanically viable — its join could not identify the
> deleted survivor, the site/grammar/status carriers were absent — and ruled as §4f's header
> records. The former "acceptance criteria" paragraph is WITHDRAWN with the candidate: no
> multi-generation case gates v1 (there is no reachable multi-generation state to test).

**The prerequisite, MECHANICALLY TESTABLE (R3-5 + R4-4):** the registry is
`CONSUMPTION_SITES: dict[str, SiteSpec]` with
`SiteSpec(consumes_survivors_with_contributors: bool, transitive_contract: Optional[str])` —
both v1 entries `(False, None)`. The gate (named in A4's check column) asserts, structurally:
for EVERY entry with the capability `True`, `transitive_contract` names a spec anchor
`"NNNN-<name>.md#<section>"` such that the referenced file exists under `specs/`, carries
`Spec-Status: accepted`, and contains the named section anchor — all machine-checkable, no
judgement call. The gate's ADVERSARIAL case registers a synthetic `True` site with a missing /
draft / anchor-less contract reference inside the test and asserts the gate FAILS each variant.
A future spec flips the field only by landing an accepted contract the gate can see.

## 5. Regime analysis — where does this behave differently?

- **Growth is the regime that matters.** The ledger gains one row per maintenance CONSUMPTION —
  absorption fires ~one `remember()` apart, consolidation once per `maintain()` batch (N×M rows:
  claimed inputs × outputs, R1-1/R3-6). Over a long-lived, high-write store this **accumulates without
  bound** if never pruned. **Retention rule (frozen): a ledger row is kept while its `survivor_id`
  exists; when the survivor is hard-deleted (`forget_user`, or a future hard-delete) its rows go**
  — the same "kept while the thing it describes exists" rule as the 0003 refusal inventory. This
  bounds the ledger to live survivors, not to all history. A row is never pruned merely for age: an
  old contribution is exactly what a late `revoke_source` needs.
- **Per-op cost is O(1)–O(batch).** Absorption adds one INSERT to an already-atomic
  supersession commit; consolidation adds N×M INSERTs (claimed inputs × outputs, R1-1) at the cutover
  transaction. No new round-trip, no budget/cap/recompile-threshold interaction (the ledger is off the
  recall and wiki paths entirely).
- **The regime a single-op test misses — and MUST reach (A4):** the NOTHING-TRANSFERRED consumption
  (absorption where no `max()` moves, A1) and the delete-then-recover case (consolidation, A2). A
  test that only exercises a value-moving absorption would pass while the attack path (empty
  payload) stayed open — so A4 injects at every declared site INCLUDING a consumption whose
  recorded values show no transfer (the total payload makes that visible). This is a
  **stable (on-by-default)** behaviour, so that regime blocks: A1/A2/A4 are required, not optional.
- **Cold vs warm store:** identical — the ledger does not touch the wiki cache or retrieval scoring.
- **Concurrency:** the ledger inherits the atomicity of the carrier it rides (0003's CAS commit,
  0010's fence) — two concurrent maintenance ops on the same survivor each write their own row under
  their own commit; rows are append-only and never contend (§6 A8).

## 6. Invariants and executable checks — REQUIRED, blocking

*The invariant names are frozen (v3). Per PROCESS §4a they become mandatory implementation/release
gates once the design is `accepted`; they are prospective here (unbuilt), like `0003`'s I1–I9 were.*

| | invariant | executable check |
|---|---|---|
| **A1** | a consumption is recorded **EVEN WHEN NOTHING TRANSFERS** — an older/weaker contributor that moves no `max()` is still recorded (the consult-and-discard key; closes the attack path). Payloads are TOTAL at both sites (v8): the no-transfer case is recorded with base+contributor values that themselves show nothing moved — strictly more informative than the retired empty-payload form; the consult-and-discard PRINCIPLE is general and the record always total. *(Reinforcement MOVED to `0012`.)* | `test_absorption_records_the_contributor_even_when_no_value_moves` — an older/weaker absorbed prior moves no `max()` yet is recorded, its base+contributor payload showing the no-op transfer · the consolidation branch is A2's N×M case |
| **A2** | a consolidated summary's contributor SOURCES are recoverable after input deletion (not only the `lineage` ids) — over the FULL INPUT×OUTPUT relation (R1-1): with N claimed inputs and M outputs, EVERY output enumerates all N contributors (N×M rows) | `test_consolidation_contributors_survive_input_deletion` (`xfail` today; the flip asserts the cross product on a MULTI-output op — ≥ `consolidate_min_batch` inputs, 2 outputs, 2×N rows) |
| **A3** | absorption's contributor link is queryable via `contributions()`, not only a `note` string | `test_absorption_link_is_a_queryable_contribution` (`xfail` today) |
| **A4** | for any survivor, `contributions(user_id, survivor_type, survivor_id)` enumerates every CONSUMED CONTRIBUTOR (whether or not anything transferred — the total payload records either way) across every `0014` site — and the site set is a MECHANICAL registry, not a remembered list (R1-9): a `CONSUMPTION_SITES` constant in code + a GENERATED consumption manifest (`specs/generated/0014-consumption-manifest.md`, the 0002 audit-manifest pattern) enumerating every code path that INSERTs a ledger row — incl. a branch inside an existing store mutator — with a gate test that fails when the code and the manifest disagree. A contributor with **no `source_id`** is still enumerated, `identity_digest` NULL (F1/I13) | `test_every_consumed_contributor_is_enumerable` — inject at each registered site incl. an absent-`source_id` contributor (NULL digest asserted) · `test_the_consumption_manifest_matches_the_code` — the generated-manifest gate: every ledger INSERT site is registered; an unregistered INSERT fails the gate · `test_the_severance_capability_gate_binds` (R5-6) — every `SiteSpec` with `consumes_survivors_with_contributors=True` must name a `transitive_contract` anchor that exists under `specs/`, is `Spec-Status: accepted`, and contains the section; the adversarial cases (missing / draft / anchor-less on a synthetic True site) each FAIL; both v1 sites assert False |
| **A5** | content-free — `identity_digest` via the shared `0006` primitive; `evidence_ref_digest` via the frozen §4a evidence-reference construction (its OWN domain, origin-scoped, NULL iff absent — R1-8); `payload` VALIDATES against the CLOSED per-site recursive schema (§4a) — unknown keys/types/nesting REJECTED, the whole op aborting (A7); no `object`/`note`/`summary` ever | `test_contribution_records_are_content_free` · `test_a_corrupt_derivation_seam_aborts_the_op` (R3-7 — callers cannot supply payloads, so the injection targets the REACHABLE seams): a contributor row with non-finite `confidence` (NaN/±Inf), a non-UTF-8-encodable `evidence_ref`, a store-derivation self-check failure at each site, and ANY empty payload at either site (`{}` signals a derivation failure — v8) — each aborts the whole op |
| **A6** | `forget_user` erases the user's ledger rows; export/import EXCLUDE the ledger (§4e) | `test_forget_user_erases_the_contribution_ledger` · `test_export_excludes_the_contribution_ledger` |
| **A7** | the record is ATOMIC with the maintenance op AND **COMPLETE — exact set equality between absorption drafts and the plan's `absorbed_duplicate` invalidations, and between consolidation rows and the claimed-inputs × outputs product (R5-1/R6-4)**: if the op rolls back, its rows roll back; no consumption without a record, no record without a consumption, and no consumption MISSING from the record | `test_a_rolled_back_maintenance_op_writes_no_ledger_row` — inject a failure after the op's writes but before commit at each site · `test_an_omitted_absorption_draft_aborts` — consume 0.8 AND 0.9, draft only the 0.9: the op aborts (the value-verification blind spot, closed by set equality) · `test_a_duplicated_absorption_draft_aborts` · `test_an_extra_absorption_draft_aborts` — a draft for a row the plan does not invalidate |
| **A8** | the ledger is APPEND-ONLY — a row is never UPDATEd or REPLACEd; concurrent ops each write their own row | `test_ledger_rows_are_append_only` · `test_concurrent_consumptions_each_write_one_row` |
| **A9** | `identity_digest` is the shared `source_identity_digest` over the RESOLVED pair (F2/I12) and JOINS with `revoke_source` — a source digested for revocation finds exactly its contribution rows. Applies to **COMPLETE identities only**: a NULL-digest (unknown-source) row NEVER joins a revocation (F1/I13) | `test_contributors_of_source_joins_a_revocation_pair` — write via a site, then look up by `source_identity_digest(resolve(origin, source_id))`; assert the row is found, and that an unknown-source row is NOT returned by any revocation join |
| **A10** | a ledger row is kept while its `(survivor_type, survivor_id)` exists and dropped when the survivor is (retention, §5; type-keyed — R1-5: an Edge and an Episode sharing a raw id delete independently) | `test_ledger_row_is_dropped_with_its_survivor` — incl. the same-raw-id Edge+Episode pair: deleting one leaves the other's rows |

**A4 is the one that decides whether the class is closed** — exhaustive over the declared sites *keyed on
consumption, not value change*, so neither a fourth site nor a nothing-transferred consumption (A1) can
reintroduce the finding. **A7 is what makes it crash-safe**; **A9 is what makes it usable by
`revoke_source`.**

## 7. Failure modes and reversibility

- **🔴 Silent failure — a NEW consumption site added later that does not emit.** This is the exact
  failure this spec exists to close, one level up: if a fourth maintenance path that consults-and-
  discards a contributor is added without emitting a draft, the finding returns and nothing complains.
  **Mitigation: the set of consumption sites is DECLARED, not remembered** — mirror the 0002 audit
  manifest, which enumerates every store mutator so a new one cannot hide. A4 iterates that declared
  set; adding a consumption path without registering it fails A4. First visible symptom otherwise: a
  survivor with a value that moved but `contributions()` empty.
- **Partial failure — a consumption without a record, or a record without a consumption.** Prevented
  by A7: the row commits in the SAME transaction as the op (0003's CAS commit / 0010's fenced txn), so
  a crash mid-op rolls back both. A site that cannot write the row atomically MUST NOT perform the
  consumption. (Permanent write errors must surface, never degrade to a silent success.)
- **Reversibility (as amended R4-1 — ONE model, both sites).** Reversal is RE-COMPUTATION
  everywhere: at ABSORPTION the rows carry `{base, contributor}` (the pre-image plus each
  absorbed prior's own values) — drop the revoked contributor's row and re-apply the
  inheritance rules over base + the remaining contributors (the multi-prior case that killed
  the WITHDRAWN restore-the-recorded-prior model); at CONSOLIDATION the rows carry each input's own values — re-derive the
  reductions over the remainder. `0014` guarantees the ledger is SUFFICIENT for recomputation;
  performing it is `A3`/`0004`, not this spec (the decoupling).
- **Transitive attribution across generations — RULED, round 1 (R1-6/R2-8; see §4f).** The A→B→C
  severance question was ruled by the external review (2026-08-10): **frozen point 5 is RETAINED
  for v1; there is NO tombstone** (the earlier candidate was not mechanically viable — §4f records
  the grounds); **the B→C path is presently UNREACHABLE** (accepted `0010` excludes consolidation
  outputs from later consolidation, so no v1 site can consume a survivor that itself has
  contributors); and **transitive handling is a NAMED PREREQUISITE for any future spec that adds a
  severance-capable site** — recorded in §4f, §8, and the A4 site registry, so the gap cannot
  arrive silently. No multi-generation case gates v1 acceptance (there is no reachable
  multi-generation state to test); the prerequisite binds the future spec that creates one.
- **New attack surface.** (a) A caller forging `survivor_id` or a foreign identity — blocked by
  the PER-SITE binding rule (R3-2/R4-5): at absorption the survivor must be a record the same CAS
  commit writes; at consolidation an existing provisional output verified bound to this
  operation/fence/lineage/identity; the store resolves+digests every identity itself (§4b). (b) Memory content smuggled into the ledger — blocked: identities are digests,
  `payload` is scalar field names + timestamp/float/enum values (A5). (c) An attacker staying invisible
  by ensuring no `max()` moves — closed by the consult-and-discard key (A1). (d) Unbounded ledger
  growth as resource exhaustion — bounded by survivor-existence retention (§5, A10); a consumption of a
  survivor that is later deleted takes its rows with it.

## 7a. Surfaces touched — the honest list

- `src/veracium/schema.py` — new `ContributionDraft` (references only), `ContributionRecord`,
  `SiteSpec` + the `CONSUMPTION_SITES` registry (incl. the capability + `transitive_contract`
  anchor fields, their gate and its adversarial tests — R5-6); `SupersessionPlan` gains
  `contributions: list[ContributionDraft]`, `absorption_pre_image: Optional[dict]` (R3-1 —
  plan-transient, receipt-bound, semantically verified per R4-2), AND
  `raw_request: Optional[dict]` (R7-1 — the canonical raw-edge snapshot the store derives
  the request digest from); `Episode` gains `consolidation_output_index` (R5-3)
  (§4b/§4c/§4f).
- `src/veracium/graph.py` — `_build_supersession_plan` populates `plan.contributions` for
  absorption (3.3) — one draft per consumed prior. No new mutator call site: it rides the existing
  `apply_supersession_plan`. (Reinforcement (3.1) is NOT a site — `0012` Design 1 persists the edge.)
- `src/veracium/lifecycle.py` / the 0010 consolidation primitives — `consolidate` (3.2) writes one
  N×M row set (inputs × outputs, R1-1) atomically at the OUTPUTS_DURABLE cutover transition
  (R2-3), while the claimed inputs still exist, with the persisted op_key retry identity (R2-2).
- `src/veracium/store/base.py` / `store/sqlite.py` — `apply_supersession_plan` extended to INSERT
  `plan.contributions` in its existing commit; a NEW public receipt-lookup surface
  (`lookup_supersession_receipt(op_id, raw_edge)` — the store digests the raw edge itself,
  R7-1) serving phase 1; the receipts table's `request_digest`, `response`, and `outcome_digest_version` columns (R10-6 — all three, the same carrier set as the schema bullets); the consolidation primitive extended likewise; the two
  reads `contributions()` / `contributors_of_source()`; `forget_user` erases the ledger;
  `store_mutator` accounting for the new writes (0002 audit manifest). `identity_digest` is computed
  via `0006`'s single shared `source_identity_digest` primitive (F2/I12) — the SAME one `revoke_source`
  uses — and is NULL when the contributor has no `source_id` (F1/I13).
- `src/veracium/store/schema_version.py`, `store/migration.py` — the additive `contribution_ledger`
  table + its THREE indexes (survivor, source, and the partial unique op_key — R2-2/R3-6) AND the receipts table's THREE new columns — nullable `request_digest` (R6-2), nullable `response` (R9-1, the persisted replay result), `outcome_digest_version INTEGER NOT NULL DEFAULT 1` (R9-2/R10-3 — the DEFAULT makes the ALTER executable on populated tables AND is the migration stamp; new writes stamp 2 explicitly; the v6 constructor manifest carries the identical default) — additive ALTERs whose expected resulting DDL is an INDEPENDENTLY AUTHORED reviewed constant forming the second member of `MANIFESTS[6]` per accepted `0013` §4e/§4c (per-path evidence; the migration must byte-match the pre-declared expectation, never define it — R11-1/R12-1) as `SCHEMA_VERSION` **v5→v6** (`0006` takes v5; `Spec-Requires: 0006, 0007,
  0013`), the v5→v6 migration, and evidence regeneration.
- `src/veracium/portability.py` — export/import EXCLUDE the ledger (§4e). The NEW
  `Episode.consolidation_output_index` field EXPORTS with the episode — and per accepted
  `0010`'s rule (a new exported Episode field requires a new format so older importers REFUSE
  rather than silently drop it — the reviewer measured the current v4 parser dropping it),
  **`FORMAT_VERSION` bumps 4→5 (R5-4)**. Named tests: an older importer REFUSES a v5 export;
  the current build round-trips the field intact; a v4 import (no field) remains accepted;
  duplicate present indices within one imported operation are REJECTED (R8-3 — gaps are
  partial history, duplicates never are), and against the DESTINATION across sequential
  imports over the tenant-scoped origin-namespaced key; a source-identical INDEXED OUTPUT
  resolves idempotently — scoped to the indexed output ONLY, ordinary records keep the
  shipped remap-copy semantics (R9-5/R10-5/R11-2), via the mechanically closed projection
  with its totality test + mutation oracle over the two-set projection riding `0010`'s
  stable historical namespace (R11-3/R12-3/R13-2; incl. the repeated
  `user_id=` import test on the frozen fixture — 2 edges, 3 episodes total of which 1
  indexed, R12-2).

**Schema:** **yes — the one v5→v6 migration carries the ledger table AND the receipt ALTERs (R8-4/R9-1/R9-2 — a summary omitting any of them yields an implementation missing a durable carrier):** (1) the new content-free, user-linked `contribution_ledger` table + THREE indexes (survivor, source, partial-unique op_key); (2) `ALTER TABLE supersession_operations` adding `request_digest TEXT` nullable (the request-identity carrier, §4b), `response TEXT` nullable (the persisted replay result — R9-1), and `outcome_digest_version INTEGER NOT NULL DEFAULT 1` (the DEFAULT is the migration stamp and makes the ALTER executable on populated tables — R10-3; new writes stamp 2 explicitly; the projection discriminator — R9-2) — the ALTER path's expected DDL an INDEPENDENTLY AUTHORED reviewed constant, the second `MANIFESTS[6]` member per accepted `0013` §4e/§4c, with per-path evidence; the migration must byte-match the pre-declared text, never define it (R11-1/R12-1; the deferred structural-capability model is NOT relied on). `SCHEMA_VERSION` v5→v6
(after `0006`'s v5). The TABLE is the same additive shape as 0003's refusal inventory; the ALTER is
a column addition to an existing table and is NOT (R8-4) — which is why its resulting DDL
is an independently authored reviewed constant forming the second accepted manifest per `0013` §4e/§4c (R11-1/R12-1). The cost — another store
version + migration — is accepted (§10 Q3): the ledger cannot attribute a consumption that happened
before it existed, so deferring the schema **permanently loses the interval**, not just the work.

---

## 7b. Cross-spec carriers — what asserts TODAY'S behaviour and must move in the SAME commit

*The `0012` reviews' single most recurring finding class was carrier drift — a fix landing while
some test, docstring, or sibling-spec sentence still asserted the superseded behaviour. This table
pre-empts it: every known carrier of pre-`0014` behaviour, each to be inverted/extended in the SAME
implementation commit as the behaviour it describes.*

| carrier (asserts TODAY) | today's assertion | the same-commit disposition |
|---|---|---|
| `tests/test_0014_maintenance_attribution.py::test_consolidation_contributors_survive_input_deletion` | **strict xfail** — lineage ids resolve to nothing after input deletion (A2's finding, executably) | the marker comes OFF; the helper `_summary_contributor_sources` already prefers `store.contributions()` — the assertion flips to the recovered source set |
| `::test_absorption_link_is_a_queryable_contribution` | **strict xfail** — the contributor link is only the free-text `note` back-pointer (A3's finding) | the marker comes OFF; `_absorption_contributor_queryable` already probes `contributions()` — flips to the queryable record. **The `note` back-pointer STAYS** (presentation; the render-history exclusion keys on it) — the ledger row is the QUERYABLE record beside it, not a replacement |
| `src/veracium/store/schema_version.py` `SCHEMA_VERSION` + `accepted_digests` + the evidence files; every test pinning the head symbolically | head = v5 (`0006`) | v5→v6 with the additive `contribution_ledger` + THREE indexes (survivor, source, partial-unique op_key) AND the receipts table's THREE column ALTERs — `request_digest`, `response`, `outcome_digest_version NOT NULL DEFAULT 1` (R6-2/R7-2/R9-1/R9-2/R10-3/R11-1/R12-1 — `MANIFESTS[6]` is the `0013` §4e SET: the fresh-constructor DDL generated as usual, the ALTER-path expectation independently authored + reviewed, per-path evidence; the migration byte-matches, never defines); migration + regenerated evidence (the `0006` v4→v5 carrier path, plus the ALTER evidence) |
| `specs/generated/0002-audit-manifest.md` + `specs/audit_dispositions.py` | no ledger INSERT sites exist | the extended `apply_supersession_plan` / consolidation-primitive writes get dispositions; the manifest regenerates (a NEW mutator cannot hide — the same declared-set discipline §7 requires of consumption sites) |
| `src/veracium/portability.py` + its tests | a v4 export's content set; the v4 parser silently DROPS unknown Episode fields | export/import EXCLUDE the ledger (a test asserts the export byte-set is unchanged by ledger rows) — and `FORMAT_VERSION` bumps 4→5 for the exported `Episode.consolidation_output_index` field (R5-4): older-importer refusal + round-trip + v4-still-accepted tests |
| `SupersessionPlan` docstring + `specs/0003` §4f plan-shape text | the plan carries incoming/upserts/invalidations/refusals | gains `contributions: list[ContributionDraft]`, `absorption_pre_image: Optional[dict]` (R3-1), AND `raw_request: Optional[dict]` (R7-1) — BOTH carriers state all three same-commit (the marked additive amendment on accepted `0003`; the store INSERTs the contributions inside the existing CAS commit, derives the payloads and the request digest, and verifies the pre-image/snapshot — A7/R4-2/R7-1) |
| `0003` §4f (freezes `supersession_operations(... logical_request_digest, status)`, same-digest→replay / different→conflict, "no existing table or field changes"), `0003` I9 (tests only the single-digest plan-level receipt), + the public replay path | ONE outcome-bound digest; no pre-plan lookup API; no request/outcome distinction; a public lost-response absorption retry RAISES instead of replaying (the R5-2 live defect) | **the EXACT marked amendment, ready to land AT `0014` ACCEPTANCE (R7-2/R8-1/R9-1/R9-2/R10-1/R10-2/R10-3 — the text `0003` §4f gains, verbatim):** *"AMENDED by `0014` (R5-2/R6-1/R7-1/R8-1/R9-1/R9-2/R10-1/R10-2/R10-3): `supersession_operations` gains nullable `request_digest` (store-computed from the plan's `raw_request` snapshot), nullable `response` (the committed op's EFFECT payload — `SupersessionResult` minus the runtime `replayed` flag — as canonical JSON, written atomically with the receipt; replay returns these effects with `replayed=True`, never a reconstruction from the submitted plan), and `outcome_digest_version` NOT NULL DEFAULT 1 (the DEFAULT is the migration stamp — 1 = the pre-amendment digest projection; 2 = the extended projection with contributions + `absorption_pre_image`, stamped explicitly on every new write; comparison selects the projection by the STORED version, never by NULL-ness) — v5→v6 ALTERs. Public `apply_supersession` performs a PRE-PLAN receipt lookup with THREE branches: op_id + non-NULL matching request digest → replay the persisted effects (`replayed=True`) with no re-planning; non-NULL differing digest → conflict; NULL stored digest (either legal NULL form) → request identity unavailable, proceed to planning and phase-2 outcome comparison at the stored projection version. Store-level `apply_supersession_plan` is REQUEST-FIRST on a receipt hit when both the receipt's `request_digest` and the plan's `raw_request` exist: matching request → replay the persisted effects as `replayed=True` (the submitted plan's outcome discarded — the concurrent-preflight loser replays, never conflicts); differing request → conflict. Outcome-digest verification governs only receipts/plans WITHOUT request identity, at the receipt's stored projection version. Legacy receipts (request_digest NULL, response NULL, version 1) keep the pre-amendment outcome-match rule with reconstruct-from-plan replay — sound there because a matching outcome digest proves the submitted plan is the recorded plan (heals forward)."* — **and I9's check column gains**: the public lost-response absorption replay test, the reused-op-id-different-request tests (new + legacy receipts), the concurrent-preflight loser-replays test (R8-1), the persisted-result-not-reconstruction race test (R9-1), the projection-version tests — legacy-matching, legacy-conflicting, new-snapshot-less contribution-mutation (R9-2) — the NULL-identity phase-1 continuation tests (R10-2), the nonempty-table migration test (R10-3), the table-driven receipt-state test (R10-4), and the forged/malformed-snapshot aborts. Both land in the SAME commit as the implementation; `0003`'s "no table changes" sentence is amended with them |
| accepted `0010` `write_consolidation_output_if_current` + `transition_consolidation_if_current` + their X-invariant tests | the output primitive writes one provisional output + lineage; the transition moves state; no ledger, no output index | a marked ADDITIVE amendment (R1-1/R1-9/R2-3/R3-3): the OUTPUT primitive ASSIGNS and PERSISTS `output_index` (store-sequential; the return surfaces it); the CUTOVER transition (`OUTPUTS_DURABLE`) derives-and-INSERTs the N×M ledger rows atomically with the transition, verify-on-conflict under the persisted `op_key`; the X-suite gains the retry/takeover/verify-mismatch ledger cases; **the return-type change (`bool` → `Optional[int]`) with INDEX 0 FALSEY (R5-5) sweeps EVERY consumer**: `lifecycle.consolidate`; `store/base.py`'s docstring (says `bool` today); accepted `0010`'s API carrier text (a marked amendment line); `tests/test_0010_consolidation_primitives.py` — which contains BOTH a truthiness `assert write_...(...)` AND an `... is False` fence-loss assertion, EACH failing under the new contract — and every `test_0010_visibility_reservation` call site. The rule everywhere: failure asserts `is None`; success asserts the EXACT sequential index (0, 1, …) through finalization |
| the store deletion/retention paths (`forget_user`, `invalidate_edge`, hard-delete, consolidation input deletion) + their tests | delete records without touching any ledger | A10's retention rides them: survivor deletion drops the survivor's rows (type-keyed); the deletion tests gain the ledger assertions (R1-9) |
| `CHANGELOG.md` + the release upgrade note | v5 store, one-call migration | the v6 note + the pending upgrade-recommendation release line (the platform point rides this) |

## 8. Claims and limits

**Claims:** every maintenance-time *consumption of a contributor* — value change or not — becomes
auditable and (with a consumer) reversible — by RE-COMPUTATION at BOTH sites (R4-1: over
base + the remaining contributors' recorded values at absorption; over the remaining
inputs' recorded values at consolidation); the recurring maintenance-provenance-loss pattern is
closed by one consult-and-discard invariant rather than three point fixes, and the no-transfer
consumption — the cheapest evasion — is recorded with it.

**Does NOT claim:** it does not revoke a source, compute a blast radius, or make a revocation reach
recall (`A3`/`0004`); it does not change any maintenance *decision* (reinforcement still reinforces,
consolidation still consolidates); it does not authenticate the contributor's provenance labels
(that is the ingest boundary); it does not restore already-lost attribution in existing stores —
the migration starts the ledger empty and records transfers from v5 forward (pre-v5 loss is
unrecoverable, an honest limit to state loudly); and **transitive attribution is OUT of v1
(R5-6, the round-1 ruling as a stated limit): the A→B→C severance state is unreachable in
v1, no tombstone exists, and any future severance-capable site is gated on a landed
transitive-handling contract by the A4 capability gate — a blast radius computed today is
complete over the sites that exist, and the gate is what keeps that statement true.**

---

## 10. Open questions

*All five resolved by research 2026-08-08 (`proposals/0014-research-response.md`); kept here with
their rulings so the reasoning survives into design lock.*

- **Q1 — reversibility vs content-freeness — RESOLVED: no conflict.** The scalar payload
  (`observed_at`/`confidence`/`valid_from`/`disclosure`/`derived_from`/`author_of_evidence`/`date`
  + prior values — the R2-4 widened set) is
  timestamps/floats/closed enums — store-clear. `evidence_ref` and `source_id` are host free-form and
  are **digested**; `origin` is **store-minted** (`0006` §4.1) — not a content risk, but digested too
  as part of the one opaque key so a single `digest` covers the whole identity (`0006` F3/R5). The
  digest is over the **RESOLVED** pair — `0006` §4.6 forbids digesting a stored `origin`-absent pair —
  and stays joinable for `revoke_source`. Keying on `digest(resolved (origin, source_id))` names the
  `0014 → 0006` dependency (§2).
- **Q2 — scope — RESOLVED: stop at the record.** All reversal / blast-radius / reach defers to
  `A3` / `0004`.
- **Q3 — new store version justified by attribution alone? — RESOLVED: yes, land now.** Deferring
  does NOT save the v5 bump — the ledger only attributes consumptions that happen *after* it exists,
  so waiting **permanently loses the interval** (and §1 already establishes history is not
  reconstructible). The audit value stands alone.
- **Q4 — interaction with `0012` — RESOLVED: do NOT block on it.** Under the consult-and-discard
  wording the invariant is *independent* of `0012`'s outcome — `0012` changes only the *payload*
  (whether reinforcement transfers liveness), not *whether a contributor was consumed*. (A
  transfer-keyed invariant WOULD have made `0014` `0012`-dependent — a concrete cost of the original
  wording, now avoided.)
- **Q5 — ownership / framing — RESOLVED: decoupling CONFIRMED**, and research judged dev's
  recurrence + standalone-audit arguments stronger than A3's original bundling. The one change —
  re-key to consult-and-discard — is folded into §4/§6. The v3 remainder is MET as of v4: the mechanical contract is full (§4/§6/§7a/§7b), and `0006` is accepted + implemented — nothing gates the external review.

---

## 11. Review history

| version | verdict | findings | full disposition |
|---|---|---|---|
| v1 (stub) | draft — dev framing from research `A3` §2 | — | this document |
| **v2 (stub)** | **research reviewed: decoupling CONFIRMED; invariant re-keyed to consult-and-discard; Q1–Q5 resolved; `0014 → 0006` named** | 1 (the transfer-vs-consume sharpening) | `proposals/0014-research-response.md`; this document |
| **v3** | **design-complete mechanical contract; the `0006`↔`0014` interface FROZEN (reviewer-signed 2026-08-09; seven points; F1 nullable digest / F2 shared primitive / F3 §4.6 folded); the A→B→C transitive gap recorded against frozen point 5** | — | this document; the `0006` §11 closure |
| **v4** | **review-ready maturation (2026-08-10): prerequisites LANDED (`0006` accepted+implemented; `0012` accepted+implemented+impl-review-accepted — reinforcement excision is fact); §7b carrier table added; §4f tombstone CANDIDATE mechanized as the round-1 design question; two-bin protocol proposed from round 1** | — | this document |
| **v5** | **round 1 EXTERNAL (2026-08-10): the two-bin protocol ACCEPTED; the §4f question RULED (frozen point 5 retained, no tombstone, transitive handling = prerequisite for future severance-capable sites); NINE bin-(a) findings returned and folded (R1-1…R1-9)** | 9 | `specs/reviews.py`; this document |
| **v6** | **round 2 EXTERNAL (2026-08-10): EIGHT bin-(a) found-in-fix cells in v5's amendments, all folded (R2-1…R2-8 — store-derived payloads; persisted retry identity; cutover-atomic inserts; total consolidation payloads; byte-exact digest framing; the §2c matrix; biting N×M digest tests; the carrier sweep)** | 8 | `specs/reviews.py`; this document |
| **v7** | **round 3 EXTERNAL (2026-08-10): SEVEN bin-(a) folded (R3-1…R3-7 — the absorption pre-image exists and binds; per-site survivor binding; store-assigned output identity + verify-on-conflict; the row-cardinality A2 test; inert §4f history + the mechanical capability gate; the carrier sweep; reachable-seam injections)** | 7 | `specs/reviews.py`; this document |
| **v8** | **round 4 EXTERNAL (2026-08-10): SIX bin-(a) folded (R4-1…R4-6 — per-contributor absorption payloads + recomputation reversal; semantic pre-image verification; the complete output-index carrier; the structurally-testable capability gate; the sweep; the exact consolidation schema) + the EXPLICIT pre-send checklist pass, which caught the v7 `{}` contradiction and the return-type consumers** | 6 | `specs/reviews.py`; this document |
| **v9** | **round 5 EXTERNAL (2026-08-10): SEVEN bin-(a) folded (R5-1…R5-7 — draft/invalidation set equality; the request/outcome receipt SPLIT closing an EXECUTED live replay defect; the Episode-field output index; FORMAT_VERSION 4→5; the falsey-zero consumer sweep; the gate carried into A4/§7a/§8; five live contradictions resolved) + the retired-phrase sweep MECHANIZED (caught a sixth)** | 7 | `specs/reviews.py`; this document |
| **v10** | **round 6 EXTERNAL (2026-08-10): SIX bin-(a) folded (R6-1…R6-6 — the two-phase replay construction; durable receipt carriers + the honest legacy policy; the output-index ownership matrix; A7 set-equality tests named; seven contradictions fixed; and the gate made REAL in `withdrawn_phrases.py` — its first committed run found 8 hits incl. 2 in `0003` no round had named)** | 6 | `specs/reviews.py`; this document |
| **v11** | **round 7 EXTERNAL (2026-08-10): FIVE bin-(a) folded (R7-1…R7-5 — the store-derived raw-request carrier; the verbatim ready-to-land `0003` amendment + I9 extensions; the lossless round-trip construction; the gate-found contradictions fixed; the adversarial gate self-test in the suite)** | 5 | `specs/reviews.py`; this document |
| **v12** | **round 8 EXTERNAL (2026-08-10): FIVE bin-(a) folded, each classified against the 7-class taxonomy before fixing, the missing check fixed WITH the finding (R8-1…R8-5 — request-first phase 2, the concurrent loser REPLAYS; the exhaustive snapshot field partition + byte-exact digest + mutation oracle + frozen vectors; duplicate imported indices rejected (the dropped v10 rule reinstated); the schema summary carries the ALTER; the gate registry gains stable rule ids with per-entry fixture proof + the inverse unproven-entry test)** | 5 | `specs/reviews.py`; this document |
| **v13** | **round 9 EXTERNAL (2026-08-10): SIX bin-(a) folded, classified first (R9-1…R9-6 — the persisted replay `response` column (the promise was unimplementable against the receipt's columns); the `outcome_digest_version` discriminator + the closed receipt-state triple; the store-level per-field abort oracle (inclusion ≠ binding); `needs_confirmation` → EXACT-EQUAL per the shipped `graph.py:163-167` with every carrier swept; destination-state import uniqueness over the origin-namespaced key; the §4c DDL-scope carrier corrected + retired — the sweep now greps facts, not phrasings)** | 6 | `specs/reviews.py`; this document |
| **v14** | **round 10 EXTERNAL (2026-08-10): SIX bin-(a) folded, classified first, four found-in-fix from v13 (R10-1…R10-6 — the persisted EFFECT payload + `replayed=True` construction; three-branch phase 1 (NULL = identity unavailable, never "different"); the executable `DEFAULT 1` DDL with the nonempty-table migration test; the table-driven closed-state test; SOURCE-IDENTICAL re-import over normalized identity, tenant-scoped, cited against the shipped remap; the §7a surfaces carrier — the sweep now greps column names)** | 6 | `specs/reviews.py`; this document |
| **v15** | **round 11 EXTERNAL (2026-08-10): FOUR bin-(a) folded, classified first, three found in v14's fixes (R11-1…R11-4 — `MANIFESTS[6]` as `0013` §4e's manifest SET, the deferred first-ALTER model NOT relied on and the digest-identity claim withdrawn; the re-import no-op scoped to the indexed output with shipped copy semantics for ordinary records; the mechanically closed source-identity projection with totality + mutation oracles; REVIEWER_GUIDE carries no frozen counts — COLLECTED.txt authoritative, the +3-git-skip reconciliation rule stated, a gate test forbidding count triples)** | 4 | `specs/reviews.py`; this document |
| **v16** | **round 12 EXTERNAL (2026-08-10): FOUR bin-(a) folded, classified first, three found in v15's fixes (R12-1…R12-4 — the independently authored ALTER-path expectation (the migration byte-matches, never defines — `0013` §4c honoured at last); the frozen repeated-import fixture with corrected arithmetic (3 episodes total, split asserted); the three-set projection (excluded / normalized-and-compared / verbatim) with the three-sided oracle; the self-proving reviewer-guide gate + the named environment-conditional skip inventory in COLLECTED)** | 4 | `specs/reviews.py`; this document |
| **v17** | **round 13 EXTERNAL (2026-08-10): THREE bin-(a) folded, classified first, all found in prior folds' fixes; R12-2 closed (R13-1…R13-3 — the complete ALTER-path DDL literal + digest IN the spec, authored on the qualified runtime, authorized by the review itself; the two-set projection riding `0010`'s stable historical namespace after the invented lineage remap was retired; the generated skip inventory with the two-directional completeness gate)** | 3 | `specs/reviews.py`; this document |
