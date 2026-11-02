# Feature spec: semantic hybrid recall

Spec-Status: accepted

*ADOPTED BY DEV 2026-08-31 on Quentin's ruling (six external rounds; architecture affirmed every round; implementation in lieu of further paper rounds — the round-6 findings are code-level and are folded here as v7 plus the implementation's test surface). Research authored the candidate; v6 folds the round-5 external review (5
findings) on top of v5's round-4 fold. The load-bearing changes in v6:
**lexical-first collapse** (semantic never resurfaces a lexically-suppressed
record and never changes a lexical survivor's object/note; the OUTPUT ORDER
is fused — R7-2 retired the over-broad "never reorders" phrasing — v5's monotonic-suppression claim was reviewer-executed FALSE); the
**eval gate made finite** — entity-subject paraphrase cases (verified zero
shipped-token overlap), a pinned fixture protocol, and a frozen tuning procedure
under a **preregistered-non-blind** ruling (Quentin-approved); the scoped
**shape-merge** dispositioned + fixtured; **executable** Python defaults; and a
superseded-statement consolidation. Design + five-system evidence bundled: ship
`semantic-hybrid-recall-design.md` (synced to v6 — see its changelog) WITH this
spec at next review. See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | research (veracium-research); adopted + implemented by dev |
| **Version** | **v15.2 — 2026-11-02: the lexical lane's eligibility floor admits an obligation as it admits a subject-`user` fact** (0003 v18.2 §4c-v.6d; the 0.29.0 hold's B2: research's read of the 0.29.0 notes, `1eb722a9`). An entity's edge still must match. **Prior: v15.1 — THE RECEIPT'S COST MEASURED, NOT ESTIMATED (the owner's word in the dev session, 2026-09-18: *"C: 0027 §4g + CHANGELOG erratum"*).** §4g carried T10's ≈2.3 KB "linear in the budget" — an ESTIMATE, because until schema 14 the table did not exist to measure. Measured with the receipt test's own fixture, 200 firings per cell: 2,171 B per firing on disk at the default budget (T10 5.9% high); scales with the budget — payload ≈ 580 B + 17.5 B/unit while the budget truncates (`budget_state.truncated` true), research's blind derivation; the disk slope is page-quantised and not a law — and not with the store (100 and 1,000 edges give identical rows); and the `tags_matched` bound adds exactly ONE 4,096 B PAGE per firing, flat — 6,267 B, 2.9× the default — so "linear in the budget" was true of the default-shaped receipt only and is withdrawn as a general law (research's wording, research's withdrawal). A live number an implementer reads, corrected where it is read; the carrier claims re-derived by the second seat under the standing rule. *Prior:* **v15 — POST-ACCEPTANCE AMENDMENT: THE DISPLACEMENT BUDGET (research's candidate `0027-displacement-budget-CANDIDATE.md`, the breach behaviour ruled by the owner in the research session; the owner's word in the dev session, 2026-09-14: *"Build after round 10"* — built 2026-09-15 after the amendments line closed at round 10).** A1 had two bounds and only one existed: the lane's SCORE influence is bounded and stated (`delta_fused ≤ 1/(K+1)` per lane) while its displacement COUNT was unbounded — the reviewer's "adequate general displacement limit"; research's tier-9 enumeration proved the two are not convertible at any budget and that measurement cannot supply the count bound here (a single RRF lane's margin ceiling, 1/61 − 1/101, is below the lane's lift 1/61 by construction), so the requirement needs a DECLARED cap and an ENFORCEMENT point, not a new mechanism. `PolicyLane.max_displaced: Optional[int]` — an int ≥ 0, `bool` and negatives refused, None = no cap, 0 the strong setting (reorder, never change membership). Enforced in `fused_subgraph`, the one construction where both orders exist (V-BUDGET-AT-THE-CHOKE-POINT: a limit one entry point enforces is not a general limit; the as-of path is excluded twice over — `policy` is refused with `as_of`, and the as-of call site passes no lane). On a breach (`len(displaced) > max_displaced`, strictly) the returned selection is the ALREADY-COMPUTED baseline — never a re-run without the lane, two paths that must agree can diverge (V-DISPLACEMENT-BUDGET-ENFORCED) — and the receipt keeps what the lane WOULD have done: `displaced`, `admitted`, the lane's reserve are captured before the fallback (V-BREACH-EVIDENCE-PRESERVED: recomputed after it, `displaced` would be empty and the field that evidences the breach would be emptied by it), `adjusted_order` is what was returned, `budget_breached` True; every receipt carries `max_displaced_declared` — the cap, or None RECORDED when none was declared, never omitted (V-DISPLACEMENT-BUDGET-RECORDED: an absent field would be indistinguishable from a receipt written before this change). Stated before a reviewer states it: the bound is ENFORCED, its VALUE is the host's — a deployment may declare a cap nothing breaches; under C1 the host is the policy controller and no construction over a host-supplied lane can give a library-chosen ceiling, which would be a larger decision; what this supplies is general, declared, enforced and auditable; it does not reduce displacement. Research's acceptance probe (eight checks over the four invariants and the candidate's eight mutants, red at the pre-build tree, green after) was run by dev before and after the build and independently by research. §4h new; four rows in §6; the receipt's two fields in §4g. *Prior:* **v14.1 — v14 CORRECTED BEFORE RELEASE (research's pre-adoption read of 0041, 2026-09-14): the policy identity strings are BOUNDED, and the receipt's blob column is named for what it is.** `PolicyLane.policy_id`, `policy_version` and every `tags_matched` entry are host-supplied strings the receipt persists VERBATIM; v13/v14 checked only that the first two were non-empty and the tags not at all, so a sentence, a 400-character string or a disclosure could ride into `policy_receipt.receipt` — and schema_version's comment on the table claimed "ids only, never content" of a column that held whatever the host passed. Now each is an IDENTIFIER (letters, digits and `._:-`, 1–64 characters, no whitespace; a `bool` refused; at most 64 tags), refused otherwise at construction (V-POLICY-IDENTIFIERS-BOUNDED). Stated as the limit, not claimed away: an identifier can still be a label about a person — `diagnosis:hiv-positive` passes every rule here and is a disclosure — so the receipt's `receipt` column is bounded, not content-free: 0041's class for `evidence_ref`, `source_id` and `correlation_id`, and a SECOND blob carrier beside `edges.json` that 0041's enumeration reaches as such (0041 §2b-ii-bis). The `receipt` JSON's ranking fields remain record ids only (V-RECEIPT-IDS-ONLY, unchanged). *Prior:* **v14 — POST-ACCEPTANCE AMENDMENT: THE RECEIPT MADE DURABLE (research T1's durability half; the owner's word in the dev session, 2026-09-14: *"Release first, then v14"* — 0.25.0 shipped first).** v13 returned the receipt on the recall result and said what it did not do: store it. v14 stores it and nothing else — schema v13 → v14 adds the `policy_receipt` table (one row per recall in which the lane FIRED, keyed by the minted `recall_id`; the identity columns a reader lists by, and the receipt's JSON VERBATIM; the table REQUIRED, its time index REBUILDABLE; DDL only, no data step, no row minted) and `Memory.recall` writes the row BEFORE it returns, so the receipt the caller holds is the receipt the store reads back field-equal through `Memory.policy_receipts` (newest first) and `Memory.policy_receipt(recall_id)` (V-RECEIPT-DURABLE). A write that fails RAISES out of `recall` (V-RECEIPT-DURABLE-OR-LOUD): the answer is not returned as if its trace existed, which is correction C1's defect at the store; a store implementing `Store` without the three methods refuses at the first firing recall rather than dropping (the base class raises). A receipt is written once (the key refuses a second row). Ids only at rest as in flight. Not exported (deployment audit, not memory — a receipt names records, and an export is the records) and erased with the user (V-RECEIPT-ERASE). The schema evidence regenerated at the head (it had been stale since v13); the 0013 migration is the generic additive apply; the 0018 release-migration obligations attach to the release that ships it (a below-head store refuses to open; `veracium migrate`). NOT IN THIS REVISION, stated: retention of receipts (research T9's class — the table grows one row per firing recall, ≈2.3 KB each per T10; erasure is per user); 0041's tombstone of a receipt on redaction (D4, the owner's ruling awaited in the dev session) — a receipt naming a redacted record stays unreadable by construction and nothing here pre-empts the shape. §4g revised; V-RECEIPT-DURABLE, V-RECEIPT-DURABLE-OR-LOUD, V-RECEIPT-ERASE, V-RECEIPT-NOT-EXPORTED, V-RECEIPT-SCHEMA-14 in §6. *Prior:* **v13 — POST-ACCEPTANCE AMENDMENT: THE POLICY RECEIPT (research T1; the owner's word in the dev session, 2026-09-13: *"Do the A1 receipt"*).** v11 landed the lane and forbade its use until a receipt existed (§4a bullet 6): `recalled_edges` is filtered to survivors and written only on the semantic path, so the DISPLACED record — the whole event — left nothing, and a policy applied without a trace is the untraceable ranking change the owner's approval assumed impossible (correction C1). v13 builds the receipt and nothing else — no learning loop, no 0035, no proposal generation: `recall(policy=PolicyLane(...))` feeds the lane and, when the lane FIRES (a rank lands on a candidate the membership lanes hold), the result carries a `PolicyReceipt` recording the COUNTERFACTUAL — the selection the same inputs give with the policy term removed (Stages 4–5 over the baseline order v12 already computes), `displaced` = baseline[:n] − adjusted[:n], `admitted` the converse, the per-edge score delta (bounded by 1/(K+1) per lane), `budget_state` (below `max_subgraph_edges` nothing is truncated, so nothing can move; the deployment's `coverage_share`, without which R4-1's bound cannot be recomputed), the reserved ids under both orders (the evidence for `reserve_unchanged`, derivable not declared), a minted opaque `recall_id` as the host's join key, and never the query or its digest (a confirmation oracle). Written on the NON-SEMANTIC path too: with a policy the fused construction runs on every path (its degenerate identity IS the legacy projection, V10). Ids only, never content. An inert policy leaves no receipt; `policy` is not combinable with `as_of`. NOT IN THIS REVISION, stated: durable storage of the receipt (T10's ≈2.3 KB per firing) needs a schema bump and the 0018 release-migration obligations — the next amendment; until then the receipt is the recall result's field and the host persists it. §4g new; V-RECEIPT-ON-FIRING, V-RECEIPT-COUNTERFACTUAL, V-RECEIPT-NON-SEMANTIC-PATH, V-RECEIPT-IDS-ONLY in §6. *Prior:* **v12 — POST-ACCEPTANCE AMENDMENT: WHAT THE POLICY LANE MAY NEVER DECIDE — the I6 reserve, Stage-3 membership and the coverage tail's novelty are computed on the UNADJUSTED (baseline) fused order (the owner's word in the dev session, 2026-09-13: *"Confirm R4-2; R4-1 too"*; R4-2 first as his word to research, *"Option 1 is my decision"*).** Research's A1-replay round 4 (its own review line on the policy lane) found, and the reviewer reproduced, that v11's ruling — *"a learned adjustment never decides which evidence counts as protected"* — was implemented for the reserve's MEMBERSHIP set (`rel_ext` excludes the policy lane) and not for its SLICE: `reserved = assertable[:reserve_n]` took a prefix of the policy-ADJUSTED order, so an ELIGIBLE record (in `rel_ext`, ranked beneath the reserve) promoted to policy rank 1 entered the protected slice and evicted a protected record (R4-2; the spec said "pre-policy", the code said otherwise — the code moves). And one promotion displaced TWO records at the reviewer's configuration (R4-1): `_cover` judged day-novelty against the ADJUSTED head, so a promotion that shifts the head by one changes which periods look uncovered and the tail re-picks (research: 46 of 3,402 configurations; the round-3 claim "exactly the last record" came from a census whose fixture had one distinct `valid_from`, so the tail never ran). v12: Stage 2 computes the BASELINE order beside the adjusted one (no policy term; identical when no policy is passed, so V10 holds by identity); Stage 4 takes the reserve in the BASELINE order; the remainder's pure-rank HEAD is filled from the ADJUSTED order (the policy's one channel) and `_cover` judges novelty against the days the BASELINE head covered (research's construction B: measured 0 of 2,560 configurations displacing more than one, 2,092 of 2,092 admissions kept); and — dev's own finding from a probe written for this amendment, RED at v11 — Stage 3 walked the ADJUSTED order to add semantic-only candidates, so which of two mutually-duplicate semantic-only records SURVIVED was the policy's, against v11's own "membership unchanged by construction"; membership now walks the baseline order. Three invariants (V-RESERVE-UNADJUSTED, V-DISPLACEMENT-ONE, V-MEMBERSHIP-UNADJUSTED), each seen to FAIL at v11 before the change; the v11 boundary test restated (the displaced record is the HEAD's marginal record, never the coverage pick). Cost measured by research: 0 of 256 configurations change for A1's actual population (a zero-overlap record is never in `rel_ext`); a policy that SHOULD promote into the reserve cannot — none is proposed, and admitting one would be a new decision. *Prior:* **v11 — POST-ACCEPTANCE AMENDMENT: THE POLICY LANE (the owner's design ruling in the research session, 2026-09-12: *"I agree with this option: add a distinct policy lane parameter that feeds fused_score but not rel_ext. But implement it in the order that makes the most sense."*; the implementation word in the dev session, 2026-09-12: *"I approve the implementation of steps 3 through 5"*).** §4a Stage 2 gains a THIRD fusion lane, `Pl`, contributing `1/(K + rank_Pl(e))` to `fused_score` and NOTHING ELSE — never to the reserve's relevance set `rel_ext`, never to Stage 3 membership; `K` stays fixed; the `(0, 1/61]` bound is PER LANE, so k live lanes give at most k/61, unbounded in k (stated now, before a fourth lane makes it a discovery); the lane is inert when no policy is passed, which is why V10's byte-identity oracle still holds; and NO POLICY IS APPLIED before the receipt exists (research T1 — `recalled_edges` cannot record a displaced record), so the parameter lands first and its use waits. Why a new parameter and not `sm`: the semantic lane already has the policy lane's formula, but `rel_ext = relevant_ids ∪ sm_rank` feeds the I6 protected reserve, so a policy expressed through `sm` would decide which evidence counts as PROTECTED — the owner's standing prohibition on learning touching entitlement. The order (research's, kept): `rel_ext` had NO test; its behaviour was pinned first, then the invariant's control was SEEN TO FAIL through the `sm` route (a policy-rank-1 target lands at position 1, inside the reserve) before the parameter that satisfies it was written (with it: position reserve_n + 1). V-POLICY added to §6. Not in this amendment: the receipt, automatic acceptance, any change to `sm`, `RRF_K`, Stage 3 membership or the reserve's own rule. *Prior:* **v10 (ACCEPTED)** — round-9 external verdict: ACCEPT, 0027 is closed (this revision records the verdict; no normative change) |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | dev · research |
| **External review** | NINE rounds, CLOSED AT ACCEPTANCE (round 9, 2026-08-31): "ACCEPT — 0027 is closed" — R8-1 fully resolved, packaged artifacts byte-verified against the repository at `a25426e`, no further amendment or acceptance rerun required. Rounds 1-6 research-side (paper), 7-9 dev-side (implementation-verification) |
| **Decision + date** | ACCEPTED — externally, round 9, 2026-08-31 ("ACCEPT — 0027 is closed"), ratifying the owner's implementation ruling of the same date. The §6a pre-release gate was DISCHARGED 2026-08-31 (measured once, all three criteria PASS, rerun-confirmed on the v2.2 topology; verdict recorded in `## Review closure`, figures internal per the rider) |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0001** — recall I6: the subgraph budget, `_cover` time-coverage, and the
  assertable-slot reservation (`graph.py:680-708`). v3 makes those stages
  consume the FUSED order and an EXTENDED `relevant_ids`; their internals are
  unchanged (§4a).
- **0003** — §4e functional-contention permutation (`_permute_contention_groups`,
  `graph.py:593`) and §4c-ii refusal contentions. UNCHANGED; runs last, over
  the fused order.
- **0020** — scoped recall, **the principal boundary (S1)**. Scope is NOT a
  boolean predicate: it is `ScopeView` (`scope_read.py:280`), a **filter-and-
  shape lens** (`visible()` drops CROSS_HIDDEN/UNRESOLVED; `shape()` restricts a
  visible cross-scope record — MENTIONABLE→USE_ONLY, `derived_from`→THIRD_PARTY —
  which can make it non-assertable to the principal). BOTH lanes route
  candidates through the SAME per-call lens BEFORE ranking/collapse/I6 (§3b, §4a
  stage 0-1, **V8**). *(R3-1; corrects v3's "predicate" and the reversed S1/S2
  mapping.)*
- **0021** — scope under maintenance **(S2)**. Its `MembershipResolver` is the
  shared authority the lens consults; recall does not re-implement it.
- **0012** — I8 collapse (`collapse_for_render`, `graph.py:674,879`). Runs on
  **Lx alone**, then semantic-only members are appended (lexical-first collapse,
  §4a Stage 3) — so enabling semantic never resurfaces a lexically-suppressed
  record and never changes a lexical survivor's object/note; the OUTPUT
  order is FUSED — survivor identity/content preservation, not order
  preservation (**V-COLLAPSE**; R7-2). *(v3-v5 fed the fused union and
  variously mis-claimed monotonic suppression / a same-value bound; R5-1
  corrects the construction.)*
- **0013 / 0007 / 0018** — store schema + migrations: the additive
  `edge_embedding` table. **The release-migration authority is 0018** (the
  release-migration orchestrator — `store/release_migration.py`); the schema
  object registers under the 0013/0007 schema-version bump
  (`store/schema_version.py`). Named now, not dev-fill (R3-7). §4f gives the DDL.
- **0019 / 0023 / 0026** — the trust classes and the render-time classification
  (`_render_class`, `graph.py:283`; `Edge.assertable`, `schema.py:497`).
  UNCHANGED and downstream; this spec adds no trust class and moves no
  classification (§3, §6 V2). *(R2-6.)*
- **0022 / 0023** — revocation / non-revival. **Ordinary retirement/revocation**
  sets `active=0` and RETAINS the row as history (`sqlite.py:252`); no cascade —
  a retired edge is surfaced (if at all) with the IDENTICAL non-assertable class
  the lexical lane gives it (§4c, **V2/V9**). **This is distinct from erasure**
  (below), which DOES delete.
- **0008 / 0009 — compliance erasure (`forget_user`, `sqlite.py:1753`).** This
  path DOES delete every user edge ("wholesale erasure — never a targeted
  delete", `sqlite.py:1184`). v3's blanket "edges are never deleted" was FALSE
  for this path (R3-2): `edge_embedding` rows must be DELETED inside the
  `forget_user` transaction, or a forgotten user's vectors orphan (an erasure
  violation, even though V-FRESH would block their recall). §4f adds the
  in-transaction delete + **V-ERASE**.
- **0005** — import boundary: embeddings are NOT exported (derived index);
  imported edges re-embed locally under the local `embedder_id` (§4c).

### Changes in v9 (round-8 external review → resolution)
| # | round-8 finding | resolved by |
|---|---|---|
| **R8-1** | the normative spec still declared the superseded v2.1 digest `766c9a62…` as CURRENT in §6a and the Review closure header (the v8 fold updated the history and the change table but missed the two current-digest declarations — the same carrier class as R7-5); plus two riders: the closure said the gate holds four tests (five since R7-1), and §6a described the expected-key check as resolved-to-edge-id when the gate compares content keys directly | both current declarations now state `ca851e54…` (v2.2), with superseded digests retained ONLY in the history lineage; the gate described as FIVE tests; the expected-key check described as implemented — content-key hit test, frozen `edge_id` for construction and ranking-tiebreak only. Carrier-only: no corpus change, no acceptance rerun (the reviewer's scoping) |

### Changes in v8 (round-7 external review → resolution)
| # | round-7 finding | resolved by |
|---|---|---|
| **R7-1** | evaluation ordering unfrozen BELOW fusion: one shared timestamp left lexical ranks tie-broken by nothing (`edges()` has no contractual order; the post-fusion id tie-break cannot repair ranks assigned before it) — reviewer measured top-10 identity changes in 40/100 cases under reversed insertion; "byte-for-byte" was false | manifest **v2.2**: DISTINCT per-position timestamps (position k → base + k seconds, one calendar day), the rule normative in the fixture block; **digest re-rolled `ca851e54…` supersedes `766c9a62…`**; acceptance RERUN after the topology change (all three criteria PASS; figures internal per the rider); the gate gains a TOTALITY check (no tied lexical sort key in any of the 100 stores) and the reviewer's reversed-insertion mutant as a standing test |
| **R7-2** | the spec's Stage-3 predicate stated only `m.active` while the implementation (correctly) required BOTH records active; the test mutated only the semantic member; over-broad "never reorders" claims survived in four carriers | conjunct 1 now `m.active and survivor.active`; an inactive-SURVIVOR fixture joins the conjunct mutants; the preamble, Spec-Requires 0012 row, v6-history row and §9 brief all restated to the correct guarantee — survivor identity/content preservation with FUSED output order |
| **R7-3** | the classification-entry gate skipped targets the semantic lane never surfaced (`if sem is None: continue`) — criterion 3 could pass with ZERO semantic retrievals | the gate now ASSERTS every trust target present in `recalled_edges` with route `semantic`/`both` before comparing classification — the criterion's "via the semantic lane" half is enforced, not assumed |
| **R7-4** | live re-validation reimplemented the range checks WITHOUT the strict types: a post-construction mutation to `semantic_timeout_ms=True` or `semantic_fetch_k=200.5` passed | ONE shared validator (`MemoryConfig.validate_semantic`) at construction AND recall — strict types included, bool never passes as int, float never as fetch size; post-construction mutation tests cover all three fields |
| **R7-5** | overstated/stale text: V8's fixture claimed an exact survivor pin but accepted either edge; §6a still described runtime ids and "other cases' targets"; Stage 4 claimed a coverage-order tail the implementation (correctly, per R9-1) does not emit; the design doc still said "never reorders" | the V8 test pins the exact survivor (`mgB`, per `_collapse_survivor_order`: freshest among equals); §6a's protocol text restated to the frozen v2.2 topology; Stage 4 restated — `_cover` decides tail MEMBERSHIP, the emission is the selected subset in fused order; the design-doc item relayed to research (their carrier) |

### Changes in v7 (round-6 external review + adoption → resolution)
| # | round-6 finding | resolved by |
|---|---|---|
| **R6-1** | Stage 3's construction emitted `collapse_for_render`'s LEXICAL output order, erasing the RRF order (a bug in round 5's own paper-fix) | §4a Stage 3 rewritten: **membership from lexical, ORDER from fused** — collapse decides the survivor SET; semantic-only members are filtered by the COMPLETE `semantic_duplicate_of` predicate (five conjuncts; `_strictly_redundant` alone is within-group only); the output is the fused order filtered to kept ids. **V-COLLAPSE claims identity, not order** |
| **R6-2** | eval topology not deterministic: runtime-resolved edge ids (the final tiebreak), distractors described not named, tune distractors could draw accept content, backend unnamed | manifest v2.1 (generator + committed file): frozen `edge_id` (`e-{case_id}`) per target; **explicit per-case `distractor_ids`**, pools SPLIT- AND LABEL-PURE (tune-only pool for tune; each accept label its own 20-pool) by one cyclic rule; `backend: SqliteStore` named with the no-ORDER-BY determinism note. **Digest re-rolled: `766c9a62…` supersedes `7b7205d1…`** (`## Review closure`) |
| **R6-3** | `__post_init__` overwrote the `semantic_fetch_k=None` sentinel, losing auto-ness — `x or default` then returned a stale resolved value after a later `max_subgraph_edges` mutation | §4d: `__post_init__` only VALIDATES an explicit value; `None` survives construction; recall resolves `None` from the LIVE `max_subgraph_edges` and RE-validates an explicit value against the live range (refusing if out of range); the same live-validation applies to `semantic_min_cosine` and `semantic_timeout_ms` |
| **R6-4** | shape-merge provenance said "counted in the `hidden` aggregate" — but the aggregate is counts-only AND discarded by recall; the suppressed member's id/source_id/origin/evidence ref are GONE | V8 wording corrected: **count-only-and-discarded**, naming exactly which provenance disappears; the scoped fixture pins the exact survivor order |
| **R6-5** | superseded claims lingered in the accumulated v3-v5 changes tables and stale framing sentences | the v3-v5 tables collapsed to a one-line historical note (full history in the research bundle); §4a's touch-point count corrected to FOUR (Stage 3's construction changed too); Stage 2's "every later stage consumes order unchanged" qualified; §5 gains the `principal=None` qualifier |
| **adoption** | — | spec adopted as `specs/0027-semantic-hybrid-recall.md`; eval artifacts at `tests/eval/semantic_paraphrase/` (manifest + generator); invariant tests + implementation land under this spec's V-names |

### Changes in v6 (round-5 external review → resolution)
| # | round-5 finding | resolved by |
|---|---|---|
| **R5-1** | collapse suppression is NOT monotonic — a semantic-only member can RESURFACE a suppressed record (executed: 1-anchor→2-anchor transition) | verified (`value_groups`: a value subsumed by ≥2 anchors forms its OWN group). The monotonic-suppression claim is REMOVED. §4a Stage 3 adopts **lexical-first collapse**: collapse the lexical set exactly as today, THEN add semantic-only members (suppressing a semantic-only member only against an already-surfaced survivor) — so semantic NEVER resurfaces or reorders a lexical survivor *(the "reorders" half of this v6 claim was itself superseded at R6-1/R7-2: the guarantee is identity/content preservation with FUSED output order)*. **V-COLLAPSE** adds the 1→2-anchor fixture |
| **R5-2** | eval gate not finite: all paraphrase targets `subject="user"` (lexical already 1.0); no fixture protocol; preregistered≠blind | manifest reworked — **60 paraphrase cases now ENTITY-subject, verified zero shipped-token overlap** (new digest below); §6a pins the full **fixture-construction protocol** (isolated store, distractors, times, order, budget, empty wiki, no higher classes); **preregistered NON-BLIND (Quentin-approved 2026-08-30)** with the tuning PROCEDURE frozen (only `semantic_min_cosine`, on the tune split, before any accept run); builder made portable + `--check` |
| **R5-3** | shape-before-collapse can MERGE collapse groups (executed) — no scoped fixture | dispositioned as INTENDED (a cross-scope duplicate that shapes to the same principal-facing envelope IS redundant to the principal; shaping only narrows, so the surviving framing is safe); §4a states which provenance is suppressed; **V8** gains the exact scoped shape-merge regression fixture |
| **R5-4** | Python defaults not executable (mutable default; class-time `max()`) | §4b/§4d corrected: `recalled_edges: dict = field(default_factory=dict)`; `semantic_fetch_k: int|None = None` resolved in `__post_init__` from the instance's `max_subgraph_edges`; behaviour on later mutation defined (resolve at recall time) |
| **R5-5** | superseded statements linger in secondary carriers | consolidation pass: Spec-Requires 0012 + the R3-4 row no longer say "same-value"; §4d/§5/§8 byte-identity claims qualified to `principal=None`; the field-contract table adds `view` to `_lexical_scored`; §9 is the round-5 brief; the design doc §6 no-embedder claim gets the `principal=None` qualifier |

*Changes in v3-v5 (rounds 2-4): collapsed to this note (R6-5) — the per-round finding→resolution tables carried claims later rounds superseded (the same-value collapse bound, the fused-union collapse, the `= {}` default). The authoritative history is the research bundle (`0027-round6-review-package/`: rounds 1-5 verbatim + per-version specs); the LIVE text of this spec is the sole normative carrier.*

*Baseline correction to the round-2 reviewer:* the review recorded 0026 as
`draft`. **0026 is `accepted` and RELEASED in v0.17.0** (2026-08-30). Nothing in
v3 depends on this, but the trust-class substrate this spec sits on is shipped,
not proposed.

---

## 1. Problem and motivation

Recall is **lexical token-overlap only** (`graph.subgraph_for_query`,
`graph.py:621`); it misses paraphrase/synonym ("trip to Tokyo" not found by "my
vacation"). This is the #1 parity gap: a user who cannot find what they stored
bounces before reaching the provenance story. **If we do nothing:** the moat is
architecturally strong and commercially stranded on the first query.

**Alternatives rejected.** (a) *Replace* token-overlap with pure embeddings —
forfeits determinism/debuggability and the exact-match guarantee. (b)
*Weighted-sum fusion* (Mem0 adaptive divisor, Memoria multi-signal) —
reintroduces per-workload tuning (§8). (c) *Do nothing.* Chosen: an
**additive, RRF-fused, lexical-anchored semantic layer that changes only which
edges are candidates and their ORDER; every trust classification downstream is
untouched.**

## 2. Field contracts touched

`grep -rn` at author time (dev re-runs at implementation):

| field | read / written | documented contract | other consumers | preserves? |
|---|---|---|---|---|
| `Memory.embed` (`__init__.py:96`) | READ (first consumer) | BYO `Embed`, plumbed-unused | none | YES — activates + extends with `Embed.id()`/`Embed.dim()` (§4d) |
| `graph.subgraph_for_query` scan (`graph.py:647-670`) | REFACTORED | extract the per-edge scan into `_lexical_scored(store, user_id, query, relations, view) -> [(base:int, overlap:int, edge)]` — the `view` (scope lens, §3b) is a REQUIRED param (each candidate passes through `view.scoped()` before scoring, R3-1); returns the RAW pre-collapse scored list; for `principal=None` `view` is absent and it is exactly today's scan | recall | YES — pure extraction; the `principal=None` byte-identity oracle (V10) pins it |
| `Edge` | READ only | unchanged | recall, gate, export | YES — no field added; recall-provenance rides a parallel `RecalledEdge` (§4b) |
| NEW `edge_embedding(edge_id, user_id, embedder_id, content_digest, dim, vec, built_at)` | WRITTEN | derived-index table; **not exported**; **no FK cascade** — RETIREMENT keeps the edge (`active=0`); the ONE delete path is compliance ERASURE, handled explicitly in §4f | migration, backfill | YES — additive; store-schema bump |
| `Store` | EXTENDED | `+ semantic_candidates(user_id, query_vec, embedder_id, dim, k, scope)`; `+ upsert_embedding(...)` | SqliteStore, future PgStore | YES — additive |
| `Recall` result | EXTENDED, non-breaking | `edges: list[Edge]` UNCHANGED; `+ recalled_edges: dict[str, RecalledEdge]` (id-keyed provenance) `+ semantic_status` | callers, MCP (strips) | additive; `edge.id` contract + `Recall.edges` type/order preserved (R3-3, V10) |

### 2a. The vector's identity (R2-3/R2-5)
A row is keyed by **`(edge_id, embedder_id, content_digest)`**:
- `content_digest` = the **digest projection** of the edge's content (§4e). It
  reuses the codebase's SHIPPED canonical form (`sqlite.py:415,439`):
  `sha256(json.dumps({"subject","relation","object","note"}, sort_keys=True,
  separators=(",",":")).encode("utf-8")).hexdigest()` — a 64-char lowercase hex
  string. Because edge text CAN change under a stable id (`graph.py:475`
  note-append; `sqlite.py:191` confirm; `_recompute_edge_row`), the digest —
  not the id — binds the vector to the content: a text change makes the stored
  vector stale (digest mismatch) and it is EXCLUDED at read (**V-FRESH**) until
  re-embed.
- `embedder_id` = the host embedder's stable identity+revision, from
  `Embed.id()` (§4d). An opaque non-empty string, compared by byte-equality.
  Vectors of a different `embedder_id` never co-search (**V5**).
- `dim` = `Embed.dim()`, a positive int. A returned query/edge vector is
  validated to be exactly `dim` finite float32 values; NaN/±inf/zero-vector/
  wrong-dim → refuse (skip the candidate; §2c).

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant** |
|---|---|---|---|---|---|
| the QUERY string | empty/whitespace → no semantic candidates, lexical-only | non-str → typed refuse | any string valid | query CRAFTED to match poisoned/quarantined content (2608.21230) | **V2** — semantic only SELECTS; classification is by trust class at render (`_render_class`), so poison surfaces-but-FENCED |
| BYO embedder OUTPUT | None/empty → treat unavailable, degrade (V6) | non-vector / wrong dim / NaN / ±inf / zero-vector → refuse the vector, skip candidate | — | adversarial vectors to force recall | **V5/V6** — validated + fail-safe; still classified at render (V2) |
| embedder AVAILABILITY | down/timeout past `semantic_timeout_ms` → degrade to lexical, `semantic_status=timeout` | — | — | — | **V6/V-STATUS** — bounded-latency fail-safe, reported |
| a RETIRED / revoked / quarantined edge in the index | its vector persists (edges are retired-not-deleted); if stale it is excluded (V-FRESH), else it may be surfaced | — | — | attempt to launder a revoked source back to assertable via the semantic lane | **V2/V9** — surfaced ONLY with the identical non-assertable class the lexical lane gives it; no route makes a non-assertable edge assertable |
| ~~imported vector~~ | *n/a — embeddings are NOT exported (derived index); imported edges re-embed locally (§4c).* | | | | **V5** (re-embed under local `embedder_id`) |

### 2c-ii. Assertions about reach — REQUIRED

| claim | invariant |
|---|---|
| "semantic recall cannot change any record's trust classification" | **V2** — classification-preservation at `_render_class`/`Edge.assertable`, checked on returned records AND the final grounded/unverified context |
| "no/failed embedder → recall reproduces the lexical-only legacy projection `[e.id for e in recall.edges]` byte-identically (for `principal=None`)" | **V3/V10** — frozen legacy oracle; every degrade path reproduces it; principal-bearing recall is qualified (finding 3) |
| "an exact lexical match is treated exactly as today when semantic is off; under fusion it competes by fused rank (no special belt)" | **V1** — narrowed per R2-2; there is one reserve; displacement under fusion is possible and stated (§4a Stage 4) |
| "a retired/revoked edge cannot become assertable through the semantic lane" | **V2/V9** — retired edges keep their vector but their non-assertable class; no cascade needed |
| "a text-mutated edge never serves a stale vector" | **V-FRESH** — the stored `content_digest` must equal the live edge's projection digest, or the row is excluded |
| "the embedding never becomes assertable context" | **V4** — derived index; not in the assertable partition; a full rebuild changes no disposition |

## 3. Trust-class matrix — REQUIRED, blocking

Trust-agnostic by construction; classification stays exactly where it is today —
at render, on the edge's own properties — and is unchanged:

| entity | trust class | how semantic recall touches it |
|---|---|---|
| the edge embedding | **none** — derived INDEX | from an already-classed edge; changes no disclosure; regenerable; retained through RETIREMENT with the edge (no separate delete), but DELETED on compliance erasure (§4f); never evidence |
| the fused candidate set | **none** — a selection + an order | handed to the UNCHANGED render/classification (`_render_class`, `Edge.assertable`), which classes each edge by its existing provenance/disclosure |
| the query embedding | transient | selects/ranks candidates only |

**Load-bearing statement:** semantic recall changes *which edges are candidates
and their order*, **never a record's classification**. Classification is
`_render_class`/`Edge.assertable` reading the edge's own trust properties
(0019/0023/0026), during render, downstream and unmodified. This is
poison-surfaces-but-fenced, and it is the seam every system in §8 misses.

## 3b. Authorization and scope — the typed lens *(R3-1)*

Scope is **not a boolean predicate**. It is `ScopeView` (`scope_read.py:280`),
constructed ONCE per recall call and threaded through both lanes:
- **`view.visible(record) -> bool`** (0020 S1) — drops CROSS_HIDDEN / UNRESOLVED
  records entirely.
- **`view.shape(record) -> record`** — the RESTRICT-ONLY consequence: a VISIBLE
  cross-scope record is narrowed (MENTIONABLE→USE_ONLY; `derived_from`→
  THIRD_PARTY), which can turn an edge that is assertable in raw storage into
  one that is **non-assertable to this principal**. Shaping can only subtract.
- **`view.scoped(records)`** = `[shape(r) for r in records if visible(r)]` — the
  combined lens; `view.narrow(edges)` then applies the §4e filters within the
  visible set.
- **0021 S2** supplies the shared `MembershipResolver` the lens consults;
  recall does not re-implement membership.

**The failure v3 missed:** if a lane hands the RAW store edge to Stage 4, a
cross-scope edge assertable in raw storage can occupy an I6 assertable-reserve
slot BEFORE shaping would have demoted it — displacing an edge that IS
assertable to the principal. v4 therefore routes **both lanes' candidates
through the same per-call `view` — visibility AND shaping — before ranking,
collapse, and I6** (§4a stages 0-1). Structured carriers downstream hold
shaped, not raw, edges. "Relevant" and "permitted" stay separate concerns
(**V8**).

## 4. Behaviour

### 4a. The one total ordered retrieval-and-budget construction *(R2-3)*

This is the complete ordered construction. It is written against the SHIPPED
pipeline; every stage names its owning spec and its `graph.py` site. Semantic
recall changes the construction in **four places** (corrected again at R6-5;
v4 said "two", v6 said "three"): the two **[SEM]** points below (the sort key
and `relevant_ids`), **Stage 0's scope move** — a behavioural change for
**principal-bearing** recall (see the identity caveat) — and **Stage 3's
collapse construction** (membership from lexical, order from fused; R6-1).
Everything else is today's code, unchanged.

**Principal-bearing amendment (round-4 finding 3).** Today, principal scope is
applied AFTER `subgraph_for_query` selection (`__init__.py:536` selects, then
`:561` `view.scoped()`s). To fix the R3-1 reserve-displacement bug, v5 applies
the lens BEFORE selection (Stage 0-1). For **`principal=None`** (unscoped) this
changes nothing — the lens is absent — so V3/V10 legacy byte-identity holds
exactly there, matching 0020's own migration invariant. For a **principal-
bearing** call, v5 DELIBERATELY amends the selection order: shaping now precedes
collapse and I6, so a cross-scope edge is shaped (its `disclosure`/`derived_from`
narrowed) before it can seize a reserve slot or a collapse-group survivor
position. This is 0027 amending principal-bearing recall — stated, not hidden;
V8 and the scoped fixtures below pin it, and legacy identity is NOT claimed for
`principal≠None`.

**Scope of this construction (R2-3).** Stages 0-5 below are exactly
`graph.subgraph_for_query` — the *grounded-edge selection*. They produce ONE
class of material: the relevance-ranked grounded edges. The FINAL context is
assembled by `recall()`/`answer()` in a fixed cross-class precedence that is
**downstream of this construction and entirely unchanged** (`__init__.py:388`,
0012 §4c(iv) order): contested first, then commitments (most-overdue, then dated
nearest-first), the wiki within its render share, THEN these relevance-ranked
grounded edges, then episodes, the unverified partition, and variants last.
**Semantic fusion reorders only WITHIN the grounded-edge slot; it does not
touch, reorder, or reprioritise any other class, and it does not replace the
0012 cross-class precedence** — that is the answer to R2-3's "orders within the
budget classes vs replaces 0012 precedence": it orders within, never replaces.
A consequence stated plainly: a semantic-only edge competes only for the
grounded-edge share of the budget and CAN be legitimately crowded out by
higher-precedence classes (warnings, commitments, contested, wiki). V-SEM's
survival claim is therefore scoped to the grounded-edge budget with the other
classes empty in its fixture; V10 answers R2-3's objection that survival cannot
be promised "under a tight budget" unconditionally.

**Stage 0 — scope lens (§3b).** Construct the per-call `view` (`ScopeView`).
Both lanes' candidates are passed through `view` — visibility THEN shaping —
before any ranking. Every edge that reaches Stages 2-5 is a SHAPED edge, so the
`e.assertable` the I6 reserve reads (Stage 4) is the principal-facing
assertability, not the raw one (R3-1).

**Stage 1 — two candidate lanes, both scoped.**
- **Lexical lane:** `_lexical_scored(store, user_id, query, relations, view)` =
  the extracted `graph.py:647-670` scan over `store.edges(user_id,
  active_only=False)`, with **each candidate passed through `view.scoped()`
  (drop-if-invisible, else shape) before scoring**. For each surviving shaped
  edge: `overlap = |_tokens("{subject} {relation} {object} {note}") ∩
  _tokens(query)|`; `base = 1 + 2·overlap` for user-subject edges and, v15.2, for
  obligations (0003 §4c-v.6d's `schema.is_obligation`: relation `deadline` and a subject that, as `str(subject).strip().casefold()`, is not `user` and carries no `kind:` prefix (`^[a-z][a-z_]*:`)) (eligible even
  at overlap 0), else `3·overlap`; `+1` if active. Edges with `base>0` form
  **Lx**, ordered by `(−base, −observed_at)`. The eligibility floor rides Lx, so
  fusion preserves it automatically.
- **[SEM] Semantic lane (only if `semantic_status` reaches `ok`, §4b):**
  `semantic_candidates` applies **VISIBILITY before cosine top-k** — recall
  passes the lens's visible-id set (or an equivalent scope filter) into the
  store, so out-of-principal edges never consume a top-k slot (closing R2-1's
  "51st eligible record never fetched"). It returns up to `k=semantic_fetch_k`
  `(edge_id, cosine)` for VISIBLE in-scope edges whose stored embedding matches
  `(embedder_id, dim)` AND is fresh (V-FRESH), with `cosine ≥
  semantic_min_cosine`. Recall then **`view.shape()`s each returned edge**
  before it enters fusion. Tie-break among equal cosine (before RRF assigns
  ranks): **cosine descending, then `edge_id` ascending** — fully deterministic
  (R3-4). Result **Sm**, ordered by `(−cosine, edge_id)`. `Sm` includes
  retired/quarantined edges on the same terms as Lx.
  - **`semantic_fetch_k`** (config carrier, finding 5): default
    **`max(200, max_subgraph_edges)`**; valid range **`[max_subgraph_edges,
    max(1000, max_subgraph_edges)]`** — defined RELATIVE to `max_subgraph_edges`
    so it is never empty even when that config (an unbounded `int`, default 40)
    exceeds 1000 (v4's fixed `[max_edges, 1000]` was empty there). It is fixed
    before acceptance (it changes the candidate set and the acceptance result),
    but it lives in `MemoryConfig`, not as a bare literal (§4d config block).

**Stage 2 — [SEM] fusion → one ordered candidate list, and `relevant_ids`.**
- Union Lx ∪ Sm by `edge_id`.
- **RRF**, `K = 60` (fixed): `fused_score(e) = Σ_{L∈{Lx,Sm,Pl}, e∈L} 1/(K +
  rank_L(e))`, ranks 1-indexed descending; a list in which `e` does not appear
  contributes NO term (absence ≠ a max-rank penalty). *(`Pl`, the policy lane,
  is v11's addition — its own bullet below.)*
- **Order** the union by `(−fused_score, −observed_at)` — the SAME recency
  tiebreak the shipped scan uses; then `edge_id` ascending for full
  determinism. This ordered list REPLACES the `scored`-ordered list at
  `graph.py:670`; it is the sole input to Stage 3. **The score magnitude is
  used ONLY here, for the order.** Stages 4-5 consume ORDER exactly as today
  and need no internal change; Stage 3 is the one later stage whose
  construction changes (lexical-membership / fused-order — R6-1, below).
- **`relevant_ids`** (the reserve's relevance set, `graph.py:653`) is EXTENDED:
  `{e : overlap>0}  ∪  {e : e ∈ Sm}`. A semantic-only match is "relevant" for
  the assertable reserve. *(This is the second and last semantic touch-point;
  it is the R2-3 ruling that a semantic hit counts as relevance, not just
  eligibility.)*
- `route(e)` ∈ {`lexical`,`semantic`,`both`} by which lanes ranked it; a
  user-subject edge or an obligation (v15.2) present only via the eligibility floor (overlap 0, not in
  Sm) is `route="lexical"`, exactly its status today.
- **The policy lane `Pl` (v11, post-acceptance, the owner's ruling).** A host
  may pass `policy_rank: dict[edge_id -> rank ≥ 1]` to `fused_subgraph`. It
  adds `1/(K + rank_Pl(e))` to `fused_score(e)` and does NOTHING ELSE:
  1. **`fused_score` only.** The policy term is added in the same sum as the
     other two lanes, for an `e` that is ALREADY in `Lx ∪ Sm`; a policy id
     outside both lanes gets no term and no membership.
  2. **Never `rel_ext`.** The reserve's relevance set stays
     `{e : overlap>0} ∪ {e : e ∈ Sm}`; a policy-promoted record that is not
     lexically relevant and not a semantic entry cannot occupy a reserve
     slot, so at policy rank 1 it lands at the first position AFTER the
     reserve (`reserve_n + 1`) — the property V-POLICY asserts, observed from
     the output. Through `sm` the same record would land at position 1,
     inside protected evidence; that is the hazard the parameter exists to
     avoid, and it is pinned as an executed failure.
  3. **Never Stage 3 membership** (R6-1: membership is lexical, plus semantic
     arrivals); `route(e)` is unchanged by the policy lane.
  4. **`K` stays fixed, not tunable.** The bound `(0, 1/61]` is PER LANE:
     with k live lanes a record can reach k/61, unbounded in k — three today.
  5. **Inert when absent.** With no policy passed the construction is
     byte-identical to v10 (V10's oracle is the guard).
  6. **No policy is APPLIED without its receipt** (research T1, §3 of
     `A1-parameter-and-receipt`; v13, §4g): `recalled_edges` cannot record a
     displaced record, and a policy applied without a receipt is the
     untraceable ranking change the owner's approval assumed impossible. The
     parameter landed at v11 with its use forbidden; v13 built the receipt, so
     a policy may now be passed to `recall` and every firing is receipted.
     Automatic acceptance is later and separate.

**Stage 3 — collapse (0012 I8, `graph.py:674,879`): membership from LEXICAL,
order from FUSED (rewritten at R5-1, corrected at R6-1; v12: the semantic-only
additions are walked in the BASELINE fused order — the order without the policy
term — so which of two mutually-duplicate semantic-only candidates survives is
never the policy's; the emitted order is the ADJUSTED one, V-MEMBERSHIP-UNADJUSTED).** v3-v5 fed the fused
UNION to `collapse_for_render`. Round 5 proved (by execution) that this is not
safe: `value_groups` sends a value subsumed by ≥2 anchors to its OWN group
({0→alone, 1→joins, ≥2→alone}), so a semantic-only member can flip a
previously-suppressed member from "1 anchor → joins/suppressed" to "2 anchors →
alone/resurfaced" (A=`cat Miso`, B=`Miso` suppressed; add C=`dog Miso` → B now
subsumed by two anchors → B **resurfaces**). So suppression is **not** a
monotone set property. v6's paper-fix ran `collapse_for_render(Lx)` and emitted
its output ORDER — which is the LEXICAL order, erasing the RRF order Stage 2
just computed (R6-1, a bug in the previous round's own fix).
- **The v7 construction — collapse decides MEMBERSHIP; fused order is
  preserved:**
  1. `survivor_ids = {e.id for e in collapse_for_render(Lx)}` — collapse runs
     on the **lexical candidate set (Lx) alone**, deciding the lexical survivor
     SET exactly as today (no resurfacing, no survivor/object/note change).
  2. Semantic-only candidates (`Sm \ Lx`) are considered **in fused order**;
     each is ADDED unless `semantic_duplicate_of(m, kept_edge)` holds against
     an already-kept edge (a lexical survivor or an earlier semantic-only
     addition).
  3. `kept = survivor_ids ∪ added_ids`; **`Stage3_out = [e for e in fused_order
     if e.id in kept]`** — the FUSED order is the output order.
- **`semantic_duplicate_of(m, survivor)` — the COMPLETE suppression predicate.**
  (`_strictly_redundant` alone is a within-group test and returns true for
  unrelated default-metadata edges.) ALL five conjuncts must hold:
  1. `m.active and survivor.active` — never suppress against, or as,
     inactive history (R7-2: the prose named only `m.active` while the
     implementation — correctly — required BOTH; the text now states what
     the code enforces);
  2. identical collapse envelope `(subject, relation, disclosure,
     author_of_evidence, derived_from)`;
  3. exact value-equivalence `_value_key(m.object) == _value_key(survivor.object)`
     — a *subsuming* semantic value is DISTINCT and is added, not suppressed;
  4. `_strictly_redundant(m, survivor)`;
  5. warning-carrier preservation — `m` carries no flag/warning the survivor
     lacks (never suppress a member that would drop a warning).
- **Guarantee:** lexical survivor **identity/object/note** preserved; **order
  is fused**, not lexical — V-COLLAPSE claims IDENTITY, not order. V10 still
  holds: semantic off ⇒ `Sm=∅` ⇒ `kept = collapse(Lx)` in fused (= lexical)
  order = today's output, byte-identical.
- Trade-off, stated: a semantic-only edge that would subsume-and-reorganise a
  lexical group is NOT allowed to; it is added as its own surfaced edge (or
  suppressed if `semantic_duplicate_of` a kept one). We accept a possible
  extra near-duplicate over changing an established lexical collapse outcome.

**Stage 4 — reserve (0001 I6, `graph.py:680-708`), the SINGLE reserve.**
There is exactly ONE reserve — the 0001 I6 assertable reserve. **v2's separate
"exact-match belt" is DISSOLVED** (it created the belt∩I6 composition ambiguity
R2-3 flagged, and its guarantee was false under RRF, R2-2). If `|candidates| ≤
max_edges`, keep all (ordered). Else: `reserved` = the query-relevant assertable
edges (`e.assertable and e.id in relevant_ids`, using the EXTENDED
`relevant_ids`), capped at `⌈max_edges/4⌉`, taken in the **BASELINE fused
order** — the fused order WITHOUT the policy lane's term (v12, R4-2: the
protected slice is a prefix of an ordering the policy never wrote; with no
policy the baseline and adjusted orders are one list) — an exact lexical match
competes here by fused rank like everything else, no separate protection (V1);
`_cover(rest, max_edges − |reserved|, coverage_share,
seed_days={reserved.valid_from}, head_days={the BASELINE head's valid_from})`
fills the remainder by an ADJUSTED-order relevance HEAD (the policy's one
channel) + a `valid_from` time-coverage TAIL whose day-novelty is judged
against the days the BASELINE head covered, never the adjusted head's (v12,
R4-1, research's construction B) — so one promotion evicts at most the head's
marginal record and cannot redefine which periods look uncovered
(`graph.py:711`). **`_cover` is a SELECTOR here, not
the emitter** (corrected at R7-5; v3-v7 misdescribed the emission): `_cover`
picks the relevance head plus a `valid_from` time-coverage tail, deliberately
reaching past fused rank for uncovered days — but the EMITTED remainder is
the SELECTED SUBSET filtered back into fused order, exactly the shipped R9-1
construction ("both segments keep their scored order internally"); coverage
decides tail MEMBERSHIP, never the output order. **Reserved records DO seed time coverage**
(their `valid_from` seed the covered-day set, `graph.py:698`). Output =
`reserved + rest`. If the reserve alone would exceed the
budget it is itself truncated at `⌈max_edges/4⌉` (it cannot exceed a quarter of
the budget — R2-3's "union of reserves exceeds budget" cannot arise, there being
one reserve capped below the budget). The reserve logic is byte-for-byte
today's; only its two inputs (the fused order — the BASELINE one since v12 — and
the extended `relevant_ids`) changed, both defined in Stage 2.

**Stage 5 — functional-contention permutation (0003 §4e, `graph.py:707`),
UNCHANGED.** `_permute_contention_groups` reorders only within
functional-contention groups; unrelated positions are untouched. **`fused_rank`
is recorded at Stage 2 (fusion) and is immutable thereafter**; Stage 5 changes
an edge's final POSITION, never its recorded `fused_rank` (R2-3's "permutation
before or after fused_rank?": fused_rank first, permutation after, on position
only).

**Degenerate identity (V10), over a NAMED legacy projection, for `principal=None`
(R2-6 + round-4 finding 3):** define `legacy_projection(recall) := [e.id for e
in recall.edges]` (the ordered edge-id list — `Recall.edges` is `list[Edge]`, so
this is `e.id`, NOT `re.edge.id`; and NOT the full `Recall` value, which differs
by `recalled_edges`/`semantic_status`). **This identity is claimed ONLY for
`principal=None`.** With `principal=None` AND `semantic_status ≠ ok`, `Sm = ∅`,
`fused_score(e) = 1/(K + rank_Lx(e))` is strictly decreasing in `rank_Lx`, the
scope lens is absent, so the Stage-2 order equals the Lx order, `relevant_ids`
reverts to `{overlap>0}`, and Stages 3-5 receive byte-identical input to today.
The construction collapses to `subgraph_for_query`, so `legacy_projection` is
byte-identical to today's. For `principal≠None`, semantic-off recall equals
today's SCOPED recall only up to the deliberate order amendment (finding 3);
byte-identity is not claimed there. This is the exact fixture V10 pins.

### 4b. The recall-provenance carrier — non-breaking *(R3-3)*
**`Recall.edges: list[Edge]` is PRESERVED unchanged** (v3's change to
`list[RecalledEdge]` was breaking — it forced `edge.id` → `recalled.edge.id`,
and the I6a union appends contention-preserved edges that were never Stage-2
selected and so carry no fused metadata; `__init__.py:583-587`). Recall
provenance instead rides a PARALLEL, id-keyed field:
```
RecalledEdge = { edge_id, lexical_overlap:int, semantic_cosine:float|None,
                 fused_rank:int, fused_score:float,
                 route:"lexical"|"semantic"|"both" }
# NEW fields, APPENDED after all existing Recall fields:
recalled_edges: dict[str, RecalledEdge] = field(default_factory=dict)
semantic_status: str = "disabled"
```
**Executable, non-breaking dataclass shape (R5-4):** a dataclass rejects a
mutable literal default (`= {}`) at import — so `recalled_edges` uses
`field(default_factory=dict)` (v5's `= {}` would not import). `semantic_status`
takes the plain `"disabled"` string default. Both are APPENDED after every
existing field, so existing positional/keyword construction is unaffected, and a
caller that never touches semantic sees an empty mapping and `"disabled"`, never
a missing attribute.
- **Coverage:** `recalled_edges` contains an entry for **exactly the edges the
  ranked query selection produced** (Stages 1-5). **Contention/I6a-preserved
  additions** (edges appended to `Recall.edges` by 0003 §4c-ii even though the
  query did not select them) have **no entry** — they were never scored, so
  inventing `route`/`fused_rank`/`cosine` for them is forbidden (**V7**).
  A caller reads provenance as `recall.recalled_edges.get(e.id)` → `None` means
  "present by contention-preservation, not by ranked selection."
- **Legacy projection** (V10) is the EXISTING `[e.id for e in recall.edges]` —
  no wrapper unwrap, no contract change.
- Structured scoped carriers hold SHAPED edges (§3b), so `Recall.edges` and
  `recalled_edges` agree on the shaped, principal-facing records.

and ONE recall-level field carrying the fate of the semantic lane (a per-edge
`route` cannot express "the lane never ran"):
```
Recall.semantic_status ∈ { "ok",          # semantic lane ran and fused
                           "disabled",    # semantic=False
                           "no_embedder", # Memory.embed / Embed.id()/dim() absent
                           "unavailable", # embedder raised / storage absent
                           "timeout",     # exceeded semantic_timeout_ms
                           "degraded" }   # ran but every vector refused (V5)
```
This is a CLOSED vocabulary (**V-STATUS**). Classification is unaffected by it:
whatever `semantic_status`, each surfaced edge is classed by `_render_class`/
`Edge.assertable` on its own properties (**V2**). `Recall.edges` preserves its
id-order contract across all statuses (V10 covers the non-`ok` cases).

### 4c. Index lifecycle *(R2-4 corrected)*
- **Existing DB:** `edge_embedding` starts empty; un-embedded edges are simply
  absent from `Sm` (still found via `Lx`) until a lazy/background backfill
  embeds them. No correctness gap; recall-quality ramps with backfill.
- **Write:** the embedding is computed **OUTSIDE the store write transaction**
  (post-commit, best-effort) — an embedder failure never fails or blocks
  ingest. Persisted via idempotent `upsert_embedding` keyed on `(edge_id,
  embedder_id, content_digest)` (§4f).
- **Text update (same id):** the `content_digest` changes → the old row is now
  stale → EXCLUDED at read (V-FRESH) and re-embedded lazily. The stale row may
  linger harmlessly until a re-embed writes the new tuple or a sweep prunes it
  (optional maintenance, not a correctness invariant).
- **Retire / revoke (NOT forget):** the edge is set `active=0` and RETAINED as
  history (`sqlite.py:252`) — not deleted, so there is **nothing to
  cascade-delete** on retirement. The retired edge's vector persists; if
  surfaced it carries the identical non-assertable class the lexical lane gives
  a retired edge (**V2/V9**). Pruning retired edges' vectors is permissible
  space maintenance, never required for correctness.
- **Forget (compliance erasure) — DELETES (finding 4):** `forget_user` is a
  DIFFERENT path from retirement — it deletes the user's edges outright
  (`sqlite.py:1753`), and v5 deletes the user's `edge_embedding` rows in the
  same transaction (§4f, **V-ERASE**). Erasure is NOT grouped with
  retire/revoke; v4 wrongly listed "forget" beside "retire" as retaining.
- **Import:** embeddings are NOT in export; imported edges arrive vector-less
  and re-embed locally under the local `embedder_id`.
- **Rebuild:** the index is fully regenerable from edges; a rebuild changes no
  edge disposition (**V4**).
- **Embedder change:** rows with a stale `embedder_id` simply stop matching
  (V5) and are re-embedded; cross-`embedder_id` vectors never co-search.

### 4g. The policy receipt *(v13; research T1 — durable from v14)*

**Why it exists.** A learned or host-supplied adjustment to ORDER is admissible
only if what it did can be read back. `recalled_edges` (§4b) cannot serve: it
covers exactly the surviving ranked selection, so a record the adjustment
DISPLACED leaves nothing, and it is written only when the semantic lane ran.
The receipt records the counterfactual.

**The input.** `Memory.recall(..., policy=PolicyLane(policy_id, policy_version,
ranks, tags_matched))` — the host's application of ONE versioned policy to THIS
call: which rule acted, which host tags fired it (§2 of the A1 document: opaque
strings the host passes, never inferred), and the ranks it assigns (edge id →
rank ≥ 1; a malformed rank is refused as at v11). The library does not learn,
choose or store policies; the host is the policy controller (C1). With a policy
the fused construction (§4a) runs on EVERY path, including `semantic=False`,
whose legacy projection is the construction's degenerate identity (V10) — so
the receipt exists on the non-semantic path, the path correction C1's trace
was missing from. `policy` is not combinable with `as_of` (the 0028 path
carries no receipt and would be the untraceable case).

**The firing rule.** The lane FIRED iff at least one rank landed on a candidate
the membership lanes hold (`Lx ∪ Sm`). An inert policy contributes nothing
(v11) and leaves NO receipt: an inert policy is not an event. Without a policy
`Recall.policy_receipt` is `None` (a defaulted field, V-COMPAT).

**The nine fields (research's table), plus provenance:** `policy_id`,
`policy_version`, `tags_matched`; `baseline_order` — the ranking WITHOUT the
lane: Stages 4–5 run once more over the baseline order v12 already computes
for the reserve (`stage3_base`), the same construction, so the instrument and
the mechanism cannot disagree and research's replay uses this field as its
baseline; `adjusted_order` — what was returned; `displaced` — ids in
`baseline_order[:n]` and not in `adjusted_order[:n]`, THE measurement; `admitted`
— the converse; `delta_fused` — per ranked edge, `fused_score − base_score`,
bounded by `1/(K+1)` per lane; `budget_state` — `{candidates, max_edges,
truncated}`: below the budget nothing is truncated, so a firing lane displaces
nothing (T5's structural fact, carried per call), and `coverage_share` — the
deployment's share, without which R4-1's displacement bound
`n_promoted × (1 + int(budget × coverage_share))` cannot be recomputed from the
receipt, and whose shipped default of 0.0 means the coverage path never runs
(research: a receipt that omits it cannot tell that world from the other
afterwards); `reserved_baseline` and `reserved_adjusted` — the reserved ids
under each order, at most ⌈max_edges/4⌉ each, the EVIDENCE for
`reserve_unchanged`, which is therefore derivable from the receipt and not
declared by it (both are carried; declared and derived agreeing is itself a
check); `reserve_unchanged`; `ranks_applied`; `semantic_status`; `recall_id` —
an opaque key minted per receipt, never set by the caller, the host's join key
to its own logs (`recorded_at` alone cannot separate two recalls in one
second); `recorded_at`. **(v15)** `max_displaced_declared` — the lane's declared cap,
or None RECORDED when none was declared; `budget_breached` — whether this
recall's displacement exceeded it, in which case `adjusted_order` is the
baseline that was returned while `displaced`, `admitted` and
`reserved_adjusted` keep what the lane WOULD have done (§4h). IDS ONLY — no field carries an edge's content, the
query, or a digest of the query: a digest of user prose is a confirmation
oracle (0041 §4), and the query itself would be a new content carrier 0041's
enumeration would have to reach. A receipt that names a record later REDACTED
becomes unreadable, and that is the correct degradation.

**Durable (v14).** The receipt is a ROW before it is a return value: when the
lane fired, `Memory.recall` writes `policy_receipt(user_id, recall_id,
policy_id, policy_version, recorded_at, receipt)` — the identity columns a
reader lists by, and `receipt` the receipt's JSON with sorted keys, VERBATIM —
in its own committed write, then returns. `Memory.policy_receipts(user_id,
limit=None)` lists the user's receipts newest first (by `recorded_at`, then
`recall_id`) and `Memory.policy_receipt(user_id, recall_id)` reads one back;
both parse the verbatim text and refuse a row whose text does not carry
exactly the receipt's fields or whose columns disagree with it. The receipt
the caller holds and the receipt the store reads back are field-equal
(V-RECEIPT-DURABLE) — one serialisation, read where it was written. A write
that fails RAISES out of `recall` (V-RECEIPT-DURABLE-OR-LOUD): the recall does
not return as if its trace existed, because a trace that silently does not
exist is correction C1's defect, and a store that implements `Store` without
`write_policy_receipt` / `policy_receipts` / `policy_receipt` meets the base
class's refusal at the first firing recall, not a silent drop. The row is
written once: the key `(user_id, recall_id)` refuses a second. The table is
`REQUIRED` in 0013's policy (an audit record is not derivable from current
state; its absence is damage, not drift — the `edge_event` argument) and its
time index `REBUILDABLE` — which carries a guarantee stronger than the
write's loudness (research's behavioural verification, 2026-09-14): a store
whose `policy_receipt` table was DROPPED to silence receipts never reaches
`recall`; it refuses to OPEN as a stamped-shape mismatch naming the missing
objects. The write's raise is the propagation path for a failure inside an
intact store; the shape manifest is the guarantee against a store made
incomplete. Crossing v13 → v14 is DDL only: no receipt exists
before the table does, so the migration carries nothing and mints nothing.
Ids only at rest as in flight (V-RECEIPT-IDS-ONLY holds of the row's text)
— of the RANKING fields. The policy identity fields (`policy_id`,
`policy_version`, `tags_matched`) are the host's strings, persisted verbatim,
and are BOUNDED at `PolicyLane` to identifier shape (v14.1: letters, digits
and `._:-`, 1–64 characters each, no whitespace, at most 64 tags; refused at
construction otherwise), not content-free — an identifier can be a label
about a person, which is 0041's class for `evidence_ref` and `source_id` and
is stated in 0041 §2b-ii-bis as such — and the identifier alphabet is the
alphabet of structured personal data (`ssn:123-45-6789`, `dob:1974-03-02`,
`dx:C50.9` pass; research's read), so the rule no charset enforces is said in
words to hosts: a policy tag names a policy, not a subject. The `receipt`
column is a blob carrier 0041 enumerates beside `edges.json`, with one
difference worth claiming: its interior is SHAPED — record ids, numbers,
booleans, ISO timestamps and identifier-shaped strings — so a redaction sweep
over it can be typed, and a value of any other shape is itself a finding,
where `edges.json` holds free prose.
Not exported: `export_memory` is the user's memory and a receipt is
deployment audit about a recall of it (V-RECEIPT-NOT-EXPORTED); an import
therefore carries none. Erased with the user, in the same statement set as
the rows (V-RECEIPT-ERASE).

**What this revision does NOT do, stated.** Retention: the table grows by one
row per firing recall — **measured 2026-09-18 (v15.1): ≈2.2 KB per firing at the
default budget (`max_subgraph_edges = 40`: receipt JSON 1,280 B, row 1,384 B, 2,171 B per
firing on disk); it scales with the BUDGET — receipt payload ≈ 580 B + 17.5 B per unit of budget WHILE THE
BUDGET TRUNCATES — `budget_state.truncated` is true; once the budget exceeds the candidates the
receipt is sized by the candidates instead (three budgets, intercepts 579/580/581; research's blind derivation, reproduced by
dev) — not with the store; the on-disk figure is page-quantised (2,171 B is 106 pages amortised
over 200 firings) and its per-unit slope is not a law; and a host using the full `tags_matched` bound (64 × 64) adds exactly one
4,096 B page per firing, flat, which dominates — so budget-linearity describes the
default-shaped receipt only. T10's ≈2.3 KB estimate was 5.9% high on the default cell** —
and nothing here
prunes it — research T9's class, with erasure per user the only remover.
Redaction: 0041's D4 (tombstone the receipt on a redacted supersession; a
replay refuses) is the owner's ruling awaited in the dev session; a receipt
that names a redacted record is already unreadable by construction, and the
row shape here pre-empts nothing of D4's.

### 4d. Public API + fallback *(R2-6)*
- `recall(user, query, *, semantic: bool|"auto" = "auto")`. **Default
  `"auto"`** = attempt semantic iff `Memory.embed` is configured AND exposes
  `id()`+`dim()`; on the embed call raising OR exceeding `semantic_timeout_ms`,
  DEGRADE to lexical and return with the matching `semantic_status` (never
  raise). `semantic=True` forces the attempt (degrades the same way, reporting
  status); `semantic=False` → `semantic_status="disabled"`, lexical only.
- **Config carriers on `MemoryConfig` (finding 5 — all three, with defaults +
  ranges, so no invariant rests on an undefined value):**
  - `semantic_min_cosine: float = 0.25` (range `[0.0, 1.0]`; tuned-then-frozen,
    §6a).
  - `semantic_timeout_ms: int = 250` (range `[1, 60000]`) — the bounded-latency
    deadline; the latency invariant (V6) is now finite because the bound is a
    defined config value, not an unstated one.
  - `semantic_fetch_k: int | None = None` — a SENTINEL, not
    `max(200, max_subgraph_edges)` (which a dataclass evaluates ONCE at
    class-definition using the class default `max_subgraph_edges=40` — R5-4).
    **`__post_init__` only VALIDATES an explicit (non-`None`) value** against
    `[self.max_subgraph_edges, max(1000, self.max_subgraph_edges)]`; **it never
    overwrites `None`** (R6-3: v6 resolved the sentinel at construction, which
    lost the auto-ness — `x or default` then returned the STALE resolved value
    after a later `max_subgraph_edges` mutation). At recall:
    `k = cfg.semantic_fetch_k if cfg.semantic_fetch_k is not None else
    max(200, cfg.max_subgraph_edges)` — auto always tracks the LIVE
    `max_subgraph_edges`; an EXPLICIT value is RE-validated at recall against
    the live range and REFUSED (typed error) if a later mutation put it out of
    range. The same live-validation applies to the other mutable semantic
    fields: `semantic_min_cosine ∈ [0,1]`, `semantic_timeout_ms ∈ [1,60000]`.
- **Bounded latency:** the query-embed runs under `config.semantic_timeout_ms`;
  on breach, abandon and set `semantic_status="timeout"`. The CONTRACT: recall
  never blocks longer than `semantic_timeout_ms` on the embedder; implementation
  chooses the deadline mechanism.
- **`Embed` extension (R2-5/R3-5, exact contract).** The SHIPPED protocol is
  `Embed(Protocol)` with `__call__(self, texts: list[str]) -> list[list[float]]`
  (`llm/base.py:34`). v4 KEEPS `__call__` as the embedding call (it is NOT
  replaced) and ADDS two methods to the protocol:
  - `Embed.id() -> str` — the `embedder_id`: a non-empty string matching
    `^[A-Za-z0-9._@:+-]{1,128}$` (a `name@revision` shape is conventional).
    **One `id()` PERMANENTLY denotes one embedding behaviour** — one model, one
    revision, one preprocessing, one output space. ANY semantic change (new
    model, retrained revision, changed tokenisation/normalisation, different
    dim) MUST yield a NEW `id()`. This is stronger than "stable within one
    operation" (v3's error, R3-5): the persisted index mixes vectors across
    operations and process restarts, so reusing an id for changed behaviour
    silently mixes incompatible vectors. Compared by byte-equality.
  - `Embed.dim() -> int` — the declared dimension; the SOURCE against which
    "wrong dimension" is judged. **Strict `int` (`type(dim) is int`, `dim>0`);
    `bool` is REJECTED** (it is an `int` subclass but not a valid dimension).
  - **Embedding call:** `embedder(texts) -> list[list[float]]` via the shipped
    `__call__`; batch in, batch out, same length and order; the ONE-input query
    path is `embedder([query])[0]` (single-input return shape: a 1-element list
    of one `dim`-length vector).
  - **Malformed protocol:** if `id()` or `dim()` raises, is absent, or returns a
    malformed value (empty/pattern-violating id; non-int/≤0/bool dim) → treat
    the embedder as unusable: `semantic_status="no_embedder"` if the method is
    absent, `="unavailable"` if it raises/returns-malformed (never propagate).
  - **Accepted component scalars:** each vector component must be a real number
    (`int` or `float`), coerced to float32. **`bool` is explicitly REJECTED as a
    component** (even though `bool` is an `int` subclass in Python) — a vector
    containing `True`/`False` is refused (V5), closing R2-5's boolean case.
  - **Normalization + cosine:** vectors are NOT required to be pre-normalized;
    `cosine(a,b) = dot(a,b)/(‖a‖·‖b‖)` computed in float64; a zero-norm vector
    (‖·‖=0) is refused (V5), never divided by.
- **Provenance schema (Edge unchanged):** recall-provenance lives in
  `Recall.recalled_edges` (id-keyed, §4b), NOT on `Edge` and NOT by retyping
  `Recall.edges`; the MCP surface strips it, like the agreement counters.
- **Exactness contract:** `semantic=False`, missing embedder, invalid embedder
  output, and unavailable semantic storage each **reproduce the lexical-only
  result byte-identically for `principal=None`** (V3/V10); for principal-bearing
  recall they reproduce today's SCOPED recall up to the deliberate order
  amendment (finding 3), not byte-identity.

### 4e. The two named projections *(R2-2, R2-5)*
There are TWO distinct text derivations; v2 wrongly unified them. Both are
named and frozen:
- **Lexical projection** (for `overlap`): `_tokens(f"{subject} {relation}
  {object} {note}")` where `_tokens` is the SHIPPED tokenizer at `graph.py:588`
  — `{_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w ∉ _STOP and
  len(w)>2}`. Frozen by reference (`_tokens`, `_stem`, `_STOP`); **V-TOK** pins
  that the same `_tokens` feeds both the query and edge sides.
- **Digest projection** (for `content_digest`, the vector-binding): the SHIPPED
  canonical form `sha256(json.dumps({"subject":s,"relation":r,"object":o,
  "note":n}, sort_keys=True, separators=(",",":")).encode("utf-8")).hexdigest()`
  — identical in shape to `sqlite.py:415,439`, so v3 reuses the codebase's own
  digest convention rather than inventing a delimiter scheme. Keys fixed to
  exactly `{subject,relation,object,note}`; values are the edge's stored strings
  verbatim (no normalisation — the digest binds the BYTES that were embedded).
- **Embedded text** (what the embedder actually sees): the digest projection's
  four values joined `"{subject} {relation} {object} {note}"`. Stated so the
  digest and the embedded bytes are the same content; the digest is over the
  canonical-JSON form for stability, the embedder sees the readable join.

### 4f. Schema, concurrency, and migration *(R2-4)*
Reference DDL (SqliteStore; PgStore mirrors it with `vector(dim)`):
```sql
CREATE TABLE edge_embedding (
    edge_id        TEXT    NOT NULL,
    user_id        TEXT    NOT NULL,
    embedder_id    TEXT    NOT NULL,
    content_digest TEXT    NOT NULL,   -- 64-char sha256 hex, §4e digest projection
    dim            INTEGER NOT NULL,   -- = Embed.dim()
    vec            BLOB    NOT NULL,   -- exactly dim × float32, little-endian (4·dim bytes)
    built_at       TEXT    NOT NULL,   -- ISO-8601 UTC
    PRIMARY KEY (edge_id, embedder_id, content_digest)
);
CREATE INDEX ix_edge_embedding_lookup ON edge_embedding(user_id, embedder_id, dim);
-- NO foreign key / ON DELETE CASCADE: ordinary RETIREMENT sets active=0 and
-- retains the row (sqlite.py:252), so a cascade would never fire on retirement.
-- The ONE path that deletes edges is compliance ERASURE (forget_user,
-- sqlite.py:1753) — handled explicitly below, not via cascade (SQLite cascade
-- on a JSON-column store is unreliable and would not cover the erasure semantics).
```
- **Serialization:** `vec` is `dim` IEEE-754 float32 in little-endian order,
  length `4·dim` bytes; a blob of any other length is refused (V5). `cosine` is
  computed in float64. `dim` and `lexical_overlap` are ints; `semantic_cosine`
  is float64 or `None`.
- **Conditional, idempotent write (R2-4 races):** `upsert_embedding` writes in
  ONE transaction that (a) re-reads the live edge, (b) recomputes its §4e
  digest, and (c) inserts `ON CONFLICT(edge_id, embedder_id, content_digest) DO
  NOTHING` **only if the live digest still equals the `content_digest` of the
  vector being written**; otherwise it writes nothing. This closes the
  update-vs-worker and revoke-vs-worker races the reviewer named: a delayed
  worker holding a vector for content A, committing after the edge moved to B
  (or after a revocation that changed its text), finds `live_digest ≠ A` and
  drops its write. A re-embed of unchanged content is a no-op; concurrent
  post-commit workers race harmlessly to the same tuple. Belt-and-suspenders:
  even if a stale row exists, the READ path (V-FRESH) excludes it, so a stale
  vector can be neither written under a moved edge NOR served.
- **Freshness at read (V-FRESH):** `semantic_candidates` JOINs `edge_embedding`
  to `edges` on `edge_id`+`user_id`, loads the live edge, recomputes its §4e
  digest, and DROPS any row whose stored `content_digest` differs. It does NOT
  filter on `active` (parity with the lexical lane's `active_only=False`); the
  JOIN's only jobs are to fetch live text for the freshness check and to skip
  rows whose edge no longer exists. Cosine ≥ `semantic_min_cosine`; top-`k` by
  cosine.
- **Compliance erasure (R3-2):** `forget_user(user_id)` MUST delete this user's
  `edge_embedding` rows **inside the same transaction** that deletes the user's
  edges (`sqlite.py:1753`) — `DELETE FROM edge_embedding WHERE user_id=?` beside
  the edge delete. Erasure is deletion, not retirement; V-FRESH would block
  RECALL of an orphaned vector but does not satisfy ERASURE, which requires the
  bytes gone. The in-flight-worker case is ALREADY covered by the
  digest-conditional write (§4f conditional insert): after erasure the worker's
  re-read finds no live edge → it inserts nothing. **V-ERASE** proves no
  `edge_embedding` row for the user remains after `forget_user`.
- **Migration:** additive `CREATE TABLE` registered with the **0018**
  release-migration orchestrator under the 0013/0007 schema-version bump; no
  backfill required at migrate-time (empty table degrades to lexical);
  down-migration is `DROP TABLE edge_embedding` (fully reversible).

### 4h. The displacement budget *(v15; research's candidate; the owner's word)*

**Why it exists.** A1's score influence is bounded (`delta_fused ≤ 1/(K+1)`
per lane, §4g); its displacement COUNT — how many records the lane moves out
of the returned selection — was not, and that count is the reviewer's
"adequate general displacement limit". Research's tier-9 enumeration showed
the two bounds are not convertible at any budget and that no measurement on
the task corpus can supply the count bound at one lane, so the requirement
is met by a declared cap and an enforcement point: `PolicyReceipt.displaced`
is already computed on every firing recall and durable since v14.

**The declaration.** `PolicyLane.max_displaced: Optional[int] = None` — an int
≥ 0; a `bool` refused (`True == 1`, as `policy_rank` already refuses it); a
negative refused; `ValueError`, never a silent coercion. `None` means no cap.
`0` is the strong setting: the lane may reorder the returned set and may
never change its membership.

**Enforcement sits in `fused_subgraph`, not in `Memory.recall`.** Both orders
exist there and nowhere earlier; a limit one entry point enforces is not a
general limit. The caller inventory, derived: `fused_subgraph_with_receipt`
(whose only caller is `Memory.recall`) reaches the cap; the as-of path is
excluded twice over — `recall(policy=…)` is refused with `as_of` (§4c), AND
the as-of call site passes no lane at all — so either exclusion could be
removed without the other being noticed, and research's probe pins the
exclusivity as a standing check.

**On breach: return the baseline selection.** With `len(displaced) >
max_displaced` (strictly — a lane displacing exactly its budget is within
it), the returned selection is the one the same call gives with no lane: the
ALREADY-COMPUTED baseline order through Stages 4–5, never a re-run without
the lane (two code paths that must agree byte-for-byte are two paths that
can diverge).

**What the receipt records.** `max_displaced_declared` — the cap, or None
RECORDED when none was declared, never omitted (absence is never the trusted
cell: a receipt with no cap field would be indistinguishable from one written
before this change, and the doctor could not count unbounded recalls).
`displaced`, `admitted`, `reserved_adjusted`, `reserve_unchanged` — the
lane's effect, captured BEFORE the fallback and kept on a breach: what the
lane WOULD have done. `adjusted_order` — what was returned (the baseline on a
breach). `budget_breached`. The trap, named so the implementation cannot walk
into it: `displaced` recomputed after the fallback is the empty set, because
the returned order then equals the baseline — the field that exists to
evidence the breach would be emptied by the breach.

**What this does NOT establish.** The bound is enforced; its VALUE is the
host's. A deployment may declare a cap so large nothing breaches it. Under C1
the host is the policy controller, so no construction over a host-supplied
lane can give a library-chosen ceiling — that would be the library overriding
host policy, a larger decision. What this supplies is a limit that is general
(every caller, every recall), declared (never inferred), enforced (not
reported) and auditable (both numbers in a durable receipt). It does not
reduce displacement: a host declaring a generous cap sees exactly the prior
behaviour plus a receipt field. Degrade-not-drop (research's adoption
recommendation §5: render displaced records as headers rather than evicting
them, which bounds displacement at zero by construction) is stronger and is
not proposed here — it changes what recall returns — and nothing here
forecloses it.

## 5. Regime analysis

- **No embedder / old protocol:** identical to today for `principal=None`
  (V10); principal-bearing recall carries the deliberate Stage-0 order
  amendment (§4a). Offline hosts unaffected.
- **Small store (≤~10⁴ edges/user):** SqliteStore brute-force cosine, exact.
- **Large store:** needs PgStore/pgvector or sqlite-vec (parity gap #3) on the
  same `semantic_candidates` interface; brute-force degrades.
- **Embedder unavailable/slow at read:** bounded-latency degrade (V6),
  `semantic_status` reports which.
- **Backfill in progress:** partial semantic coverage; lexical unaffected.

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **V1** no exact-match belt (narrowed per R2-2): there is ONE reserve (I6); an exact lexical match competes in it by fused rank like any record — no separate protection. The exactness position is preserved by the lexical lane's determinism + the exact fallback (V3/V10), NOT an in-fusion guarantee; under fusion a higher-fused record (incl. semantic-only) CAN displace an exact match — stated, not hidden. The check pins that with `semantic_status≠ok` exact matches are placed exactly as today (⊆ V10) and that the reserve never exceeds `⌈max_edges/4⌉` | `test_single_reserve_no_belt_and_exact_fallback` | CI |
| **V2** classification-preservation: fusion changes membership/order but NEVER a record's class at `_render_class`/`Edge.assertable` — checked on returned records AND the final grounded/unverified context, including a poison-shaped semantic hit reaching context ONLY as fenced | `test_semantic_preserves_classification` | CI |
| **V3** exact fallback, `principal=None` (finding 3): `semantic=False`/no-embedder/invalid-output/no-storage reproduce the frozen legacy projection `[e.id for e in recall.edges]` byte-identically FOR UNSCOPED recall; for `principal≠None` the semantic-off result equals today's scoped recall up to the deliberate order amendment, not byte-identity | `test_lexical_fallback_is_pre_feature_identical_unscoped` | CI |
| **V4** derived index: embeddings carry no trust class, are absent from the assertable partition; a full rebuild changes no disposition | `test_embedding_is_a_derived_index` | CI |
| **V5** binding + pinning: a vector is `(edge_id, embedder_id, content_digest)`-bound; `semantic_candidates` never returns a cross-`embedder_id`/`dim` vector; NaN/inf/zero/wrong-length-blob refused | `test_vector_binding_and_no_cross_embedder` | CI |
| **V6** bounded-latency fail-safe: embed raise/timeout → lexical result, `semantic_status` set, no exception, within `semantic_timeout_ms` | `test_embedder_timeout_degrades` | CI |
| **V7** recall provenance, scoped to ranked selections (R3-3): `Recall.recalled_edges[e.id]` carries `{lexical_overlap, semantic_cosine, fused_rank, route}` for exactly the query-selected edges; a contention/I6a-preserved edge (in `Recall.edges`, not query-selected) has NO entry — never an invented value | `test_recalled_edges_covers_only_ranked_selections` | CI |
| **V8** scope LENS on both lanes (R3-1) + shape-merge disposition (R5-3): both lanes route candidates through the same per-call `view` — `visible()` before the semantic top-k and lexical scan, `shape()` before ranking/collapse/I6 — so Stage 4 reads SHAPED (principal-facing) `e.assertable`. TWO scoped fixtures: (a) a cross-visible edge shaping demotes cannot occupy an assertable-reserve slot; (b) shape-merge — A(`MENTIONABLE`,`derived_from=None`) and B(`USE_ONLY`,`THIRD_PARTY`) with identical collapse content+author collapse to ONE after shaping makes A's envelope match B's (INTENDED: A is redundant-to-this-principal, and shaping only narrows so the surviving USE_ONLY/THIRD_PARTY framing is safe. Provenance disposition stated exactly (R6-4): the collapse `info` aggregate is **counts-only** (`{since, hidden, flagged_hidden}`) **and recall DISCARDS it** (`surfaced, _info = collapse_for_render(...)`) — the suppressed member's `id`, `source_id`, origin and evidence ref are GONE from the result, not \"counted\"; the fixture pins the exact survivor order) | `test_scope_lens_shapes_before_reserve` + `test_scoped_shape_merge_intended` | CI |
| **V9** retire-not-delete parity: a retired/revoked edge keeps its vector but is surfaced ONLY with the identical non-assertable class the lexical lane gives it; no route makes a non-assertable edge assertable | `test_retired_edge_class_parity_across_routes` | CI |
| **V-ERASE** compliance erasure (R3-2): after `forget_user(u)`, `SELECT count(*) FROM edge_embedding WHERE user_id=u` is 0; an embedding worker in flight during erasure inserts nothing (digest-conditional write finds no live edge) | `test_forget_user_erases_embeddings` | CI |
| **V-COLLAPSE** lexical-membership collapse (R5-1, corrected R6-1): the kept lexical set — `{e.id for e in Stage3_out} ∩ {e.id for e in Lx}` — equals `{e.id for e in collapse_for_render(Lx)}` as an IDENTITY claim (enabling semantic never resurfaces a lexically-suppressed record and never changes a lexical survivor's object/note), while **Stage3_out's ORDER is the fused order, not `collapse_for_render`'s output order**; a semantic-only `semantic_duplicate_of` a kept edge is suppressed, a distinct semantic-only edge is added (incl. a SUBSUMING value — conjunct 3), an inactive or warning-carrying member is never suppressed (conjuncts 1, 5); tests the reviewer's 1-anchor→2-anchor fixture (A=`cat Miso`,B=`Miso`,C=`dog Miso`) + 0/1/≥2-anchor cases + a fused-vs-lexical order divergence fixture | `test_lexical_first_collapse_unchanged_by_semantic` | CI |
| **V10** degenerate byte-identity over the NAMED `legacy_projection`, `principal=None` (§4b, finding 3): with `principal=None` AND `semantic_status≠ok`, `[e.id for e in recall.edges]` equals the frozen `subgraph_for_query` oracle byte-for-byte; `Recall.edges` type (`list[Edge]`) and order preserved; a scoped semantic-off fixture separately pins the amended principal-bearing order | `test_legacy_projection_identical_when_semantic_off_unscoped` + `test_scoped_semantic_off_order_amended` | CI |
| **V-SEM** semantic-only survival, scoped to the grounded-edge budget (R2-3): in a pinned store with NO competing higher-precedence classes (empty commitments/wiki/contested/episodes) — A lexical-assertable, B semantic-only cosine 0.70 assertable, C noise, `max_edges=2` — B survives collapse→reserve→`_cover`, appears in `recall.edges` (an `Edge`), and **`recall.recalled_edges[B.id].route == "semantic"`** (route lives in `recalled_edges`, not on `Edge` — finding 4); the fixture states budget, competing records, expected ids, rendered output | `test_semantic_only_survives_grounded_budget_fixture` | CI |
| **V-TOK** tokenizer frozen: the lexical `overlap` on both query and edge sides uses `graph.py:588 _tokens` (and its `_stem`/`_STOP`); a change to any is a spec change | `test_lexical_tokenizer_is_pinned` | CI |
| **V-FRESH** freshness: `semantic_candidates` never returns a row whose stored `content_digest` ≠ the live edge's §4e digest (covers note-append/confirm/recompute in-place mutation) | `test_stale_vector_excluded_after_text_mutation` | CI |
| **V-STATUS** closed status vocabulary: `Recall.semantic_status` is always one of the six §4b values; every degrade path sets the correct one | `test_semantic_status_closed_vocabulary` | CI |
| **V-POLICY** the policy lane feeds `fused_score` ONLY (v11): a policy-rank-1 record outside `Lx`-relevance and `Sm` lands at exactly `reserve_n + 1`, never in a reserve slot, while a semantic entry does gain the slot and a floor-only lexical entry does not; the same control through the `sm` route is pinned FAILING (position 1) as the executed hazard; with no policy passed V10 holds | `test_a_policy_lane_entry_does_not_gain_reserve_eligibility`, `test_the_reserve_reads_the_extended_relevance_set_semantic_yes_non_entry_no`, `test_the_sm_route_grants_reserve_eligibility_the_hazard_is_real` | CI |
| **V-RESERVE-UNADJUSTED** (v12, R4-2) with the policy lane active the RESERVED SET is IDENTICAL to the reserved set computed with `policy_rank` absent — the reserve is a prefix of the BASELINE order; an ELIGIBLE record (assertable, in `rel_ext`, ranked beneath the reserve) promoted to rank 1 is admitted through the remainder and never takes a protected slot; seen to FAIL at v11 (the promoted record entered the slice and evicted a protected one) | `test_the_reserve_is_identical_with_the_policy_lane_present_and_absent` | CI |
| **V-DISPLACEMENT-ONE** (v12, R4-1) one promotion displaces at most ONE record from the selection — the pure-rank head's marginal record — because `_cover` judges day-novelty against the BASELINE head's days; the coverage tail's pick survives and the promoted record is still admitted; seen to FAIL at v11 (two departures: the head boundary and a tail re-pick, at a fixture where the promoted record's day equals the tail pick's) | `test_a_policy_promotion_displaces_at_most_one_record_even_across_the_coverage_tail`, `test_a_policy_promotion_displaces_only_the_record_at_the_budget_boundary` | CI |
| **V-RECEIPT-ON-FIRING** (v13) a `PolicyReceipt` is present iff the policy lane FIRED on the call — a rank landed on a candidate the membership lanes hold; no policy, or an inert one, leaves `policy_receipt` None; a non-`PolicyLane` policy, a malformed lane, a malformed rank, or `policy` with `as_of` is refused before anything is computed | `test_no_receipt_when_no_policy_and_none_when_the_lane_did_not_fire`, `test_no_policy_no_receipt_and_an_inert_policy_returns_the_legacy_selection`, `test_a_policy_that_is_not_a_policy_lane_is_refused`, `test_a_malformed_policy_lane_is_refused_at_construction`, `test_a_malformed_rank_is_refused_before_anything_is_computed`, `test_a_policy_is_not_combinable_with_as_of` (`tests/test_0027_policy_receipt.py`) | CI |
| **V-RECEIPT-COUNTERFACTUAL** (v13) `baseline_order` equals the selection the same call returns with no policy (the same construction, not a model of it); `displaced` = baseline[:n] − adjusted[:n] and `admitted` the converse; on R4-1's fixture displaced == [the head's marginal record] and admitted == [the promoted record]; `reserve_unchanged` is True and equals `reserved_baseline == reserved_adjusted`; `budget_state` carries `coverage_share`; `delta_fused` ≤ 1/(K+1); below the budget both lists are empty, the reserves empty and `truncated` False; `recall_id` is minted and differs between two calls | `test_the_receipt_records_the_counterfactual_displacement_and_admission`, `test_below_the_budget_the_lane_fires_and_the_receipt_proves_nothing_could_move`, `test_the_receipt_baseline_is_the_selection_the_same_call_gives_without_the_policy` | CI |
| **V-RECEIPT-NON-SEMANTIC-PATH** (v13; correction C1) with `semantic=False` and a policy, the receipt exists, `semantic_status` is "disabled", the displaced id has no `recalled_edges` entry and is absent from `edges` yet is named in the receipt; with an inert policy on that path the returned selection is the legacy selection edge for edge (V10 through `recall`) | `test_the_receipt_is_written_on_the_non_semantic_path_and_carries_ids_only`, `test_no_policy_no_receipt_and_an_inert_policy_returns_the_legacy_selection` | CI |
| **V-RECEIPT-IDS-ONLY** (v13) every list and key in the receipt is an edge id; no field carries an edge's object or note | `test_the_receipt_is_written_on_the_non_semantic_path_and_carries_ids_only` | CI |
| **V-DISPLACEMENT-BUDGET-ENFORCED** (v15) with `max_displaced` declared and `len(displaced) > max_displaced`, the returned selection is id-for-id the selection the same call gives with no policy — the already-computed baseline, `adjusted_order == baseline_order`; a lane displacing exactly its budget is within it (mutant: `>=`); a generous cap is inert; below the budget nothing is truncated, `displaced` is empty and a cap of 0 does not fire | `test_a_breached_budget_returns_the_computed_baseline_and_keeps_the_evidence`, `test_a_lane_displacing_exactly_its_budget_is_within_it`, `test_below_the_budget_nothing_is_displaced_and_a_zero_cap_does_not_fire` | CI |
| **V-DISPLACEMENT-BUDGET-RECORDED** (v15) every firing recall's receipt carries `max_displaced_declared` — the cap or None, present either way — and `budget_breached`; both survive the store; `True`, a negative, a string or a float are refused as a cap at construction | `test_an_undeclared_budget_is_recorded_as_undeclared_and_survives_the_store`, `test_the_budget_refuses_bool_negative_and_non_int` | CI |
| **V-BREACH-EVIDENCE-PRESERVED** (v15) on a breach `displaced` and `admitted` hold what the lane WOULD have displaced and admitted — the same values the uncapped call records — never the empty set the fallback would produce | `test_a_breached_budget_returns_the_computed_baseline_and_keeps_the_evidence` | CI |
| **V-BUDGET-AT-THE-CHOKE-POINT** (v15) a direct caller of `fused_subgraph` with `max_displaced` gets the fallback and the evidence with no `Memory` in the loop; the as-of path carries no lane (refused with `as_of`; its call site passes none) | `test_the_budget_is_enforced_in_the_fused_construction_itself`, `test_a_policy_is_not_combinable_with_as_of` | CI |
| **V-POLICY-IDENTIFIERS-BOUNDED** (v14.1) `PolicyLane.policy_id`, `policy_version` and each `tags_matched` entry match `^[A-Za-z0-9._:-]{1,64}$` and there are at most 64 tags; a sentence, whitespace, a 65th character, a 65th tag, an empty tag, a `bool` or a non-string is refused at construction, before any recall; an identifier-shaped disclosure (`diagnosis:hiv-positive`) is ACCEPTED and persisted — the stated limit, not a defect | `test_policy_identity_strings_are_bounded_to_identifier_shape_and_the_limit_is_stated` | CI |
| **V-RECEIPT-DURABLE** (v14) the receipt `recall` returned is read back from the store field-equal by `recall_id` and listed newest first; the row's text is the sorted-key JSON of the receipt, ids only; it survives close and reopen | `test_the_receipt_is_durable_and_reads_back_field_equal`, `test_receipts_list_newest_first_with_a_limit_and_survive_reopening`, `test_no_firing_writes_no_row` | CI |
| **V-RECEIPT-DURABLE-OR-LOUD** (v14) a receipt write that fails raises out of `recall` (the answer is not returned as if recorded); a store without the receipt methods refuses at the first firing recall through the base class, and a non-firing recall on it is unaffected; a second row for a `recall_id` is refused by the key; a row not carrying the receipt's fields, or whose columns disagree with its text, is refused at read; a store whose `policy_receipt` table was dropped refuses to OPEN (stamped-shape mismatch naming the table and its index) before any recall | `test_a_failed_receipt_write_raises_out_of_recall`, `test_a_store_without_receipt_support_refuses_the_first_firing_recall`, `test_a_receipt_row_is_written_once_and_a_foreign_row_is_refused`, `test_a_removed_receipt_table_refuses_to_open_the_store` | CI |
| **V-RECEIPT-ERASE** (v14) `forget_user` removes the user's receipts and no other user's; `policy_receipt` is in the erase-table set | `test_forget_user_erases_the_users_receipts_and_no_others` | CI |
| **V-RECEIPT-NOT-EXPORTED** (v14) no field of a receipt reaches the export file and a store built from the export holds no receipt | `test_receipts_are_not_exported_and_an_import_carries_none` | CI |
| **V-RECEIPT-SCHEMA-14** (v14) schema 14 = schema 13 + `policy_receipt` (REQUIRED) + `ix_policy_receipt_time` (REBUILDABLE), the head stamps 14 and the table's columns are the six named; a stamped v13 store migrates to 14 with its edges and journal untouched (no second baseline) and then records receipts | `test_schema_14_declares_the_receipt_table_required_and_its_index_rebuildable`, `test_a_v13_store_migrates_to_v14_with_its_rows_intact` | CI |
| **V-MEMBERSHIP-UNADJUSTED** (v12, dev's probe) Stage 3 membership is identical with the policy lane present and absent — two mutually-duplicate semantic-only candidates resolve to the same survivor whatever the policy says; seen to FAIL at v11 (the policy-ranked duplicate replaced the baseline survivor) | `test_stage_3_membership_never_depends_on_the_policy_order` | CI |

### 6a. Acceptance measurement — REQUIRED, FINITE *(R2-7)*

Pre-committed BEFORE the run (R4 — name the run beside the number). No public
number without separate approval.

**Frozen corpus + fixture protocol + tuning procedure (round-5 R5-2).** v5
committed a manifest but (a) all paraphrase targets were `subject="user"`, which
shipped lexical admits at zero overlap (`base=1+2·overlap`) so lexical was
already recall@10=1.0; (b) no fixture-construction protocol, so the harness
could determine the result after freezing; (c) "digest-pinned" is
preregistration, not blinding. v6 closes all three:

1. **Manifest committed** — `tests/eval/semantic_paraphrase/manifest.json` (generator
   `build_manifest.py` beside it, portable, `--check` mode). **Frozen digest
   (v2.2):**
   **`sha256 = ca851e542a7a4c185b30f73a1fd764f04eeef279cbca61fd43bcd0b004da847d`**
   (lineage in `## Review closure`; superseded digests live ONLY there —
   R8-1). Expected answers are CONTENT KEYS (`subject|relation|object`),
   and the gate compares the content key of each returned edge DIRECTLY
   against the top-10 (as implemented — R8-1); the frozen `edge_id` is used
   separately, for store construction and as the deterministic ranking
   tiebreak, never for the hit test.
2. **Paraphrase cases now ENTITY-subject** (R5-2 point 1) — an entity edge
   enters lexical scoring ONLY on overlap>0 (`base=3·overlap`), so a
   zero-overlap paraphrase query genuinely misses it. **All 60 paraphrase cases
   verified to have zero shipped-`_tokens` overlap with their query** (checked
   with the shipped tokenizer). The 20 exact cases keep `subject="user"`
   deliberately (they test displacement of a high-overlap match, not recovery).
3. **Fixture-construction protocol, pinned (R5-2 point 2, tightened at
   R6-2 and R7-1 — in the manifest `fixture` block, normative here):** each
   case runs in an **isolated store** = the target edge (FROZEN
   `edge_id = e-{case_id}`) + the case's **explicit 19 `distractor_ids`**
   (split- and label-pure pools; tune never draws accept content);
   **distinct per-position timestamps** — insertion position k gets
   `observed_at`=`valid_from`= `2026-01-01T00:00:00Z` **+ k seconds** (k=0
   the target, k=1..19 the listed distractors), so lexical sort keys are
   TIE-FREE before fusion and insertion order is provably irrelevant (the
   gate asserts both, including the reversed-insertion mutant); insertion
   order = target first, then the listed distractors; `token_budget=4000`;
   **empty wiki**; **no higher-priority classes**; `max_subgraph_edges=40`;
   `principal=None`; backend `SqliteStore`. So the harness cannot move the
   result after freezing — every input is fixed.
4. **Blinding disposition — PREREGISTERED NON-BLIND (Quentin-approved
   2026-08-30; R5-2 point 3).** The `accept` cases are in plaintext + digest,
   not held out of the repo. This is an internal go/no-go gate, not a public
   benchmark, and matches research's registration-before-generation discipline.
   To make it credible rather than merely convenient, the **tuning procedure is
   FROZEN**: the ONLY tunable is `semantic_min_cosine`; it is chosen on the 40
   `tune` cases; the 60 `accept` cases are not run until 0.25 is fixed; accept is
   measured ONCE and reported beside the run (R4). No other parameter is tuned
   against any case. *(Synthetic fixtures — review case quality before use; any
   edit re-rolls the digest and must precede tuning.)*

Composition (100): **40 `tune`** entity-paraphrase; **60 `accept`** = 20
held-out entity-paraphrase (recovery) + 20 exact-match (non-regression) + 20
trust-labelled (classification-entry, each with a `disclosure`).

**Determinism.** SHIP the pre-computed vectors for every manifest case (pinned
local `all-MiniLM-L6-v2`, `embedder_id` recorded) so the measurement needs no
live embedder and reproduces byte-for-byte. Command: `pytest
tests/eval/test_semantic_recall_gate.py`.

**Numeric pass criteria (pre-committed), on the `accept` split only:**
1. **Recovery:** recall@10 over the 20 held-out paraphrase cases **≥ 0.80**
   (baseline lexical-only recall@10 recorded beside it).
2. **Exact-match non-regression** (reframed after the belt was dissolved — R2-2):
   with `semantic=off`, exact-match recall@10 over the 20 exact cases = **1.0**
   (V3/V10: byte-identical to today, which finds them); with `semantic=on`, it
   is **≥ 0.95** (semantic may reorder but must not materially cost exact
   matches). This replaces the old "0 displacement" claim, which the dissolved
   belt no longer guarantees: exactness is defended by the OFF path being
   today's, and by measuring that ON does not regress it — not by an in-fusion
   guarantee. The count and identities of any ON-path displacement are recorded.
3. **Classification-entry (R2-6):** for each of the 20 trust-labelled cases,
   the edge retrieved VIA THE SEMANTIC LANE enters `_render_class`/
   `Edge.assertable` with the identical class it gets via lexical retrieval —
   i.e. the added edge is classified by the same Edge-property logic (this is
   the correct check; NOT "the partition is identical," which was v2's error).

Recorded results + the manifest sha256 land in `## Review closure` at
acceptance.

## 7. Failure modes and reversibility

- **Fully reversible:** opt-in; for `principal=None`, `semantic=False`/
  no-embedder restores today's recall byte-identically (V3/V10); for
  principal-bearing recall it restores today's SCOPED recall up to the
  deliberate order amendment (finding 3), not byte-identity; `DROP TABLE
  edge_embedding` removes the
  index.
- **Embedder drift:** the `(embedder_id, content_digest)` binding makes drift
  explicit (re-embed), never a silent mix — the failure 4/5 surveyed systems
  have (§8).
- **Latency/availability:** bounded-latency degrade (V6), not a hard
  dependency.
- **Backfill / scale:** un-embedded edges just fall back to lexical; the
  backend seam (§5) is the reversible scale path.

## 8. Claims and limits

- **Claim:** the hybrid recovers paraphrase/synonym recall the token path
  misses, without materially regressing exact-match recall (§6a #2 measures it;
  the semantic-off path is byte-identical to today for `principal=None`) and
  without changing any classification. *Limit:* quantified only at §6a; no
  public number pre-approval.
- **Evidence (design vs mature practice)** — five OSS systems read 2026-08-30
  at **published-source / design-read fidelity** (their READMEs, docs, and
  browsed source): RRF@≈k60 in 4/5; extracted-unit embedding unanimous;
  pgvector the common prod backend; cross-encoder rerank universally
  opt-in/off. **None of the five pins the embedder identity** (V5 beyond all).
  **None fences retrieved content by trust at assertion** (GENOME
  excludes-at-retrieval, Cognee weights-by-provenance — both the seams
  2608.21230 broke; three gate nothing), so V2/§3 is unmatched. *Honesty
  correction (R2-7): v2 and the design doc claimed "file:line evidence gathered
  per repo." The comparison was done at design-read fidelity, not line-anchored;
  the five repos are not cloned locally. Per-repo `.py:line` citations are a
  NAMED pending verification for implementation time (re-pull the repos), not
  asserted here. The mechanism findings above stand at design-read fidelity.*
- *Where we may overstate:* "more reproducible than pure-embedding" holds only
  under the pin AND the cache — a reviewer should test the pin (V5), not take it
  on faith.

## 9. Brief for the external reviewer (round 5)

v6 answers round 5's five findings (mapping at top): lexical-first collapse so
semantic never resurfaces/changes a lexical survivor (R5-1; the order half
superseded — the output order is fused, R6-1/R7-2); the eval gate made
finite — entity-subject paraphrase cases (zero shipped-token overlap, verified),
a pinned fixture protocol, and a frozen tuning procedure under a preregistered-
non-blind ruling (R5-2); the shape-merge dispositioned + fixtured (R5-3);
executable Python defaults (R5-4); and a superseded-statement consolidation
(R5-5). The places most likely to still need work:
1. **Lexical-first collapse vs the reserve/coverage stages.** Collapse now runs
   on Lx alone, then semantic-only members are appended. Does that appended set
   interact correctly with the I6 reserve and `_cover` (which run over the fused
   order)? Find a store where the append-after-collapse ordering changes a
   reserve/coverage outcome unexpectedly.
2. **The EXTENDED `relevant_ids` on the reserve** (the standing seam): can a
   semantic-only assertable edge claim an I6 slot ahead of a lexically-relevant
   one and regress answer-bearingness (`_cover` 34/40, `graph.py:729`)?
3. **Eval validity.** Are the entity-subject paraphrase cases actually
   recoverable by a real `all-MiniLM-L6-v2` (semantically close despite zero
   token overlap), and are the fixture distractors adversarial enough that
   recall@10 is a real bar? The cases are synthetic — attack their quality.

## 10. Open questions

- **Embed granularity:** edges only (v1); episodes later (the injection
  surface — needs a V2 regression cell before adding).
- **MMR diversity:** add greedy MMR (Memoria default) as a phase-2 option so a
  tight budget isn't spent on near-duplicate edges? Evaluate at §6a.
- **`keyize` rare-term lane** (surfaced auditing MOTH, `scans/KNOWN_IDS.md`
  2026-08-30): a third fusion lane between lexical and full semantic — extract
  discriminative rare terms — as a cheap recall boost for hosts with NO
  embedder (this spec's exact degrade case). Phase-2; would enter fusion as a
  third RRF list. *(`semantic_fetch_k` is no longer an open question — a
  `MemoryConfig` carrier, default `max(200, max_subgraph_edges)`, range
  `[max_subgraph_edges, max(1000, max_subgraph_edges)]` — §4a/§4d.)*
- **Retired-vector pruning:** ship the optional space-maintenance sweep in v1,
  or defer? (Correctness does not need it; V9/V-FRESH hold without it.)
- **Backfill trigger:** lazy-on-recall vs a maintenance job — implementation.

## Review closure

**Frozen acceptance manifest (recorded before implementation — §6a):**
- Path: `tests/eval/semantic_paraphrase/manifest.json` (generator:
  `build_manifest.py` beside it, portable, `--check`).
- **`sha256 = ca851e542a7a4c185b30f73a1fd764f04eeef279cbca61fd43bcd0b004da847d`** (v2.2 — the CURRENT frozen corpus; superseded digests
  appear only in the history below)
- 100 cases: 40 `tune` / 60 `accept` (20 entity-paraphrase + 20 exact + 20
  trust). Paraphrase targets are entity-subject, verified zero shipped-token
  overlap. Preregistered non-blind (Quentin-approved); tuning procedure frozen
  (§6a). The gate recomputes this digest and fails on any drift.
- **Digest history:** `ca851e542a7a4c185b30f73a1fd764f04eeef279cbca61fd43bcd0b004da847d`
  (v2.2, 2026-08-31 — R7-1: distinct per-position timestamps, lexical ranks
  tie-free before fusion; acceptance RERUN after the change, all three
  criteria PASS) supersedes `766c9a62…` (v2.1 — R6-2: frozen edge_ids,
  explicit split/label-pure distractor_ids, backend named) supersedes
  `7b7205d1…` (v2.0). Every topology amendment preceded the accept run made
  under it.

**Round-9 external verdict (2026-08-31): ACCEPT — 0027 is closed.** R8-1
fully resolved: both normative declarations carry the v2.2 digest
`ca851e54…` with the superseded digest historical-only; the gate count
correctly five; expected-key behaviour matches the direct content-key
comparison; `a25426e` the verified head, packaged artifacts byte-identical,
the fold commit spec-only; archive checksums, manifest regeneration and
vector verification all pass. "No further amendment or acceptance rerun is
required." NINE rounds close the arc — the external acceptance that
ratifies the adoption-time status.

**Round-8 external verdict (2026-08-31): RETURN — one focused carrier
amendment** (R8-1: the superseded digest declared current in two normative
places; test-count and expected-key-wording riders). R7-1 through R7-4
CLOSED; R7-5 partially (the digest carriers). Verification clean: archive,
checksums, `95ab40f` head, byte-identical artifacts, regenerating manifest
and vectors, oracle match, all 19 invariant tests, all five gate tests. The
reviewer's stated position: **"Once the normative digest is corrected, I
would accept 0027."** v9 is that correction, carrier-only as scoped.

**Round-7 external verdict (2026-08-31): RETURN — five focused amendments**
(R7-1 evaluation ordering below fusion; R7-2 spec weaker than the
implemented duplicate rule; R7-3 classification gate could pass without
semantic retrieval; R7-4 live validation missing strict types; R7-5
overstated/stale carriers). "The core construction is now credible; the
remaining blocker is precision between the normative text, fixture topology,
and what the tests actually guarantee." All five folded as v8 (table above);
the reviewer's own mutants (reversed insertion; inactive survivor) are
standing tests. The acceptance ask goes to round 8.

**§6a acceptance measurement — RUN ONCE 2026-08-31: ALL THREE CRITERIA
PASS against the pre-committed thresholds.** Per the §6a/§8 rider and the
owner's disclosure ruling (2026-08-31), the measured figures are held
INTERNAL and are not stated in this public carrier; the gate is
deterministic and modelless, so any reader reproduces the exact figures
with one command: `pytest tests/eval/test_semantic_recall_gate.py -s`.
- **Vectors:** `tests/eval/semantic_paraphrase/vectors.json`, sha256
  `25271db726701b06fab45270ed5ec393d8112a2d64fccc7be93ebff9ef204e00` —
  pinned `all-MiniLM-L6-v2@1110a243fdf4` (model + HF snapshot), dim 384,
  computed once in an isolated environment; the gate runs modelless.
- **Tuning (frozen procedure honored):** `semantic_min_cosine = 0.25` was
  frozen in the spec BEFORE any accept run; the tune split was measured at
  it and the value stood — no re-tune.
- **Criterion 1 — recovery:** PASS (accept paraphrase recall@10 ≥ 0.80);
  the lexical-only baseline recovers no accept paraphrase case, consistent
  with the build-time-verified zero-token-overlap construction — §9 point
  3's case-quality risk is resolved by measurement: a real MiniLM recovers
  the cases.
- **Criterion 2 — exact non-regression:** PASS both paths (OFF = 1.0 by
  construction and measured; ON ≥ 0.95) — zero displacements recorded.
- **Criterion 3 — classification-entry:** PASS — no mismatch across the 20
  trust-labelled cases.
- Gate: `pytest tests/eval/test_semantic_recall_gate.py` (FIVE tests since
  the R7-1 fold — the three criteria, the vector/projection spot-weld, and
  the tie-free/insertion-invariance topology check — in the ordinary suite;
  deterministic, reruns reproduce the run's exact figures).
- The measured figures live in the internal record only; no public number
  without separate approval (the rider stands).

**Adoption record (2026-08-31):** six external rounds complete research-side
(bundle: `0027-round6-review-package/`, rounds 1-5 verbatim); Quentin's ruling
2026-08-31 — implementation in lieu of a further paper round — confirmed
directly in the dev session. Round-6 findings are folded as v7 (table above);
the implementation's V-tests (§6) are the executable closure evidence for
R6-1/R6-3, and the §6a acceptance measurement is a REQUIRED pre-release gate:
its recorded numbers land HERE before the feature ships.*
