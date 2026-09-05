# Feature spec: as-of / point-in-time query

Spec-Status: draft

*Candidate authored by research (2026-08-30); ADOPTED BY DEV 2026-08-31 on
Quentin's word — the review arc starts at external round 1 (the 0026
pattern: draft in-tree, reviewed to acceptance, then implemented). Written
mechanically-complete from the start, applying 0027's round-1 review
lessons proactively (exact rule, closed reason table, gate-orthogonality,
finite §6a). Sequenced deliberately AFTER 0027's acceptance — both touch
the recall pipeline, and §4c's pre-filter now composes with the ACCEPTED
0027 fused construction, not a moving target. Design rationale + field
evidence: research's `as-of-query-design.md`, bundled with every review
package (this spec is normative). Dev's internal-review pass at adoption:
PASS — the two seams the external reviewer should attack hardest are the
ones §9/§10 already flag (corrected-forward returning a value whose own
interval does not contain T; the multi-hop composition ruling). See
`PROCESS.md`.*

| | |
|---|---|
| **Author / session** | research (veracium-research); adopted by dev 2026-08-31 |
| **Version** | v1 — pre-substrate; returned at round 1 and PAUSED (see *External review*). **What v2 owes, per the accepted substrates' own hand-over:** the reason→resolution table over 0030's authoritative `DISPOSITIONED_REASONS` registry — 0030 says "a corrected edge is never groundable at any T", 0028 says "when you hit one, resolve to the corrector" (0030 scope fence: "following `corrected`→corrector or `absorbed_duplicate`→absorber is the QUERY layer's job (0028 v2's reason→resolution table)"), with unknown reasons failing CLOSED (round-1 F1's lesson); and the render of history through 0030's classifier. **Scoping DECIDED by the owner, 2026-09-05:** the `observed_at` / `known_as_of` transaction axis, now CARRIED by 0029 (0030: "the transaction axis is 0029; the query/resolution/render is 0028 v2"), goes to a **v3**; v2 is valid-time resolution only. Two design seams v2 owns (§9): a corrector whose own interval does not contain T (a third outcome, not a value and not silence), and multi-hop resolution (bounded traversal with an explicit indeterminate at the bound). |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | dev · research |
| **External review** | Round 1 (2026-08-31): RETURN — seven blocking findings, all verified real against the shipped code. **ARC PAUSED by the owner's ruling (2026-08-31): hold for the bigger shape** — the substrate (a durable transaction-time carrier; a time-relative trust classification) is specced FIRST so v2 can deliver assertable history and true bitemporal, rather than narrowing to reference-only. v2 resumes on the substrate specs' acceptance. **CONDITION CLEARED (recorded 2026-09-05, the spec-table audit):** the substrate specs are ACCEPTED — 0029 v9 and 0030 v30 at joint external round 18 (2026-09-03), 0032 (the valid-time predicate) on the owner's word (2026-09-04). v2 AUTHORING AUTHORIZED by the owner (2026-09-05, to research, with the SPLIT ruling: v2 = reason→resolution over VALID time only; v3 = the `observed_at`/`known_as_of` transaction axis); v2 is in authoring; its core and whole-spec INTERNAL rounds were given by dev 2026-09-05 (two blocking findings each, all folded). **SEQUENCING FACT established at the whole-spec round: v2's acceptance runs through 0030's IMPLEMENTATION, not merely its acceptance** — 0030's classifier (`classify_as_of`, `assertable_as_of`, the per-reason `AS_OF_DISPOSITION` mapping) exists only as spec pseudocode (zero occurrences in `src/`), and three of v2's invariants (V-NO-UPGRADE, V-NEVER-BYPASS, V-CROSS) are not finite until it ships; whether v2's external review waits for that build is the owner's call. `Spec-Status` stays `draft` because v1's body predates the substrates and v2 is not yet a candidate — it flips only through review. |
| **Decision + date** | — |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0003** — supersession authority: the reason-carrying, history-retaining
  supersession this query reads (`invalidated_at`, `invalidation_reason`).
- **0001** — recall I6: the budget/coverage/reservation, which as-of pre-filters
  before.
- **0021** — scope: as-of resolves within the principal boundary.
- **0019 / 0023 / 0026** — the gate and trust classes: UNCHANGED; time and trust
  are orthogonal (§3).
- **0011** — `correct()`: the `corrected` invalidation whose retroactive-truth
  resolution this spec defines.
- **0027** — semantic hybrid recall (ACCEPTED): §4c's as-of pre-filter hands
  the resolved candidate set to 0027's fused construction — this spec
  composes with it, changing nothing inside it. One STATED interaction: a
  historical edge whose text changed after its embedding was built is
  excluded from the semantic lane by 0027's V-FRESH while remaining
  lexically recallable, so an as-of slice can be asymmetrically covered
  across the two lanes (§4c note; acceptability is an open ruling, §10).
- **schema.py invalidation-reason registry** — the closed six-reason set this
  spec's resolution table is total over.

---

## 1. Problem and motivation

Recall returns only *current* facts (`invalidated_at is None`). There is no way
to ask "what was true at time T" — the GENOME/Mem0-Platform headline ("what was
Priya's city in May 2023?"). This is parity gap #2, and the best-ROI one: the
bi-temporal data ALREADY EXISTS (`valid_from`, `invalidated_at`, `observed_at`,
the six `invalidation_reason`s); only the query is missing. **If we do nothing:**
we lack a table-stakes temporal query every serious memory utility ships, and we
waste a differentiator we already paid for — reason-carrying history.

**Alternatives rejected.** (a) *Naive interval math* (return the record whose
`[valid_from, invalidated_at)` contains T) — rejected: it returns a CORRECTED
(never-true) fact as history, which is wrong; §4b. (b) *A new bitemporal schema*
— rejected: the fields exist; this is a query-layer feature. (c) *Do nothing.*
Chosen: **reason-aware resolution** over the existing intervals.

## 2. Field contracts touched

`grep -rn` at author time (dev re-runs at implementation):

| field | read / written | documented contract | other consumers | preserves? |
|---|---|---|---|---|
| `valid_from` (`schema.py:430`) | READ | domain time — when the fact became true | recall, combining, export | YES — read-only |
| `invalidated_at` (`:431`) | READ | when the fact ended (`None`=current); history retained | recall, supersession | YES — read-only |
| `invalidation_reason` (`:432`) | READ | closed six-reason set | maintenance, export | YES — read-only; resolution total over it |
| `observed_at` (`:118`) | READ | transaction time (ingest) | provenance, recency | YES — read-only |
| `recall`, NEW `facts_valid_at` | EXTENDED | `+ as_of` / `known_as_of` params; new lookup | callers, MCP | additive; `as_of=None` = today |

No field's meaning changes; no field is written. Pure query-layer.

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant** |
|---|---|---|---|---|---|
| `as_of` / `known_as_of` (a datetime) | `None` → current-facts behavior (V-COMPAT) | non-datetime / non-tz → typed refuse at API | any valid instant | a T crafted to surface a disputed/quarantined fact as "history" | **V-GATE** — as-of filters TIME; the gate classifies by TRUST, so a fenced fact at T returns fenced, never assertable |
| the stored `invalidation_reason` | absent (`None`=current) → the edge is the T-value | a reason OUTSIDE the closed six | — | — | **V-REASON** — resolution is TOTAL over the closed set; an unknown reason FAILS CLOSED (edge excluded, gap reported, never silently returned) |
| a broken supersession link (a `corrected`/`absorbed` edge whose target is missing) | — | dangling link | — | — | **V-CHAIN** — resolution refuses to fabricate: a broken chain yields a reported GAP, never the errored/absorbed edge |

### 2c-ii. Assertions about reach — REQUIRED

| claim | invariant |
|---|---|
| "as-of never changes a record's trust classification" | **V-GATE** — time filter is orthogonal to the gate; checked on returned records AND grounded/unverified context |
| "a corrected (never-true) fact is never returned as what was true at T" | **V-REASON** — the resolution table returns the corrector, not the error |
| "`as_of=None` reproduces today's recall exactly" | **V-COMPAT** — frozen pre-feature oracle |
| "as-of is deterministic — same store, same T, same answer" | **V-DET** — pure function of stored intervals+reasons; no LLM/embeddings |
| "a disputed or gapped period is reported truthfully, not filled by the nearest fact" | **V-GAP** — gaps and disputes return empty/fenced, never the nearest |

## 3. Trust-class matrix — REQUIRED, blocking

Time and trust are **orthogonal**; the gate is untouched:

| entity | trust class | how as-of touches it |
|---|---|---|
| the resolved as-of edge(s) | **unchanged** — the edge's existing class | filtered by TIME; then `gate.py` partitions by TRUST as always |
| the `disputed` resolution | **non-assertable** (research ruling, gate-owner to confirm) | the host revoked trust in the fact, so "what was true at T" cannot assert it: returned FENCED, resolution `disputed`, recorded-not-asserted |
| the `as_of`/`known_as_of` inputs | transient predicates | select a time slice only |

**Load-bearing statement:** as-of changes *which time slice of the history is
returned*, never *whether a record may be asserted*. Assertability stays
`gate.py`'s decision on trust class — 0019/0023/0026 — unmodified. A
third-party-relayed fact valid at T returns FENCED, not as the user's fact.
*(The `disputed`→non-assertable ruling is a trust-semantics call; per PROCESS
§3b research rules it and the gate-owner confirms — flagged §10.)*

## 3b. Authorization and scope — full specs only

As-of resolves within the principal boundary (0021): the edge history scanned
for (subject, relation) is scope-filtered first, then time-resolved. "Valid at
T" and "permitted to see" stay separate (**V-SCOPE**). Following a
correction/absorption link never crosses scope — the chain is within one
subject's history.

## 4. Behaviour

### 4a. The exact resolution (deterministic)
`facts_valid_at(user, subject, relation, T, *, known_as_of=None) -> [Resolved]`:
1. `E` = edges for (user, subject, relation), scope-filtered (0021).
2. **Transaction-time filter** (if `known_as_of` set): keep `e` with
   `observed_at ≤ known_as_of`; treat `e.invalidated_at` as effective only if
   `invalidated_at ≤ known_as_of` (else `e` is "current as of what we knew").
3. **Valid-interval filter:** candidates = `e` with `valid_from ≤ T AND
   (invalidated_at is None OR T < invalidated_at)` — half-open `[valid_from,
   invalidated_at)`.
4. **Reason resolution** (§4b) per candidate.
5. **Arity:** functional relation → the single resolved value; non-functional →
   the resolved set.
6. **Gate:** `gate.py` partitions the result by trust class (UNCHANGED).

### 4b. The reason → resolution table (closed, total over the six)
| reason (or current) | resolution at T-in-interval | `resolution` tag |
|---|---|---|
| current (`invalidated_at None`), **superseded** | return the edge — it was true then | `in-interval` |
| **lapsed**, **decayed** | return the edge, flagged stale (belief, not falsity) | `in-interval-stale` |
| **corrected** | do NOT return the error; follow the correction to the value that replaced it and return THAT value for T (the correction is retroactive in truth) | `corrected-forward from <id>` |
| **disputed** | return the edge FENCED, non-assertable (§3) | `disputed` |
| **absorbed_duplicate** | return the absorbing (canonical) edge | `absorbed-to <id>` |
| reason outside the six | EXCLUDE, report gap (V-REASON, fail-closed) | `unknown-reason-excluded` |

### 4c. API
- **Recall pre-filter:** `recall(user, query, *, as_of=None, known_as_of=None)`.
  `as_of=None` → today's current-facts recall (V-COMPAT). `as_of=T` → the
  candidate edge set is the §4a resolution at T, THEN normal recall
  (lexical/§0027 semantic + gate + budget) over it. As-of is a pre-filter;
  ranking is unchanged over the filtered set. **Stated lane asymmetry
  (composing with accepted 0027):** historical edges may carry stale
  embeddings (text mutated after the vector was built) that 0027's V-FRESH
  rightly excludes — such edges reach the as-of result through the LEXICAL
  lane only. The asymmetry is a property of composing two accepted
  behaviours, disclosed here rather than discovered; whether it is
  acceptable as-is or wants a lazy re-embed on as-of access is §10's call.
- **Direct lookup:** `facts_valid_at(user, subject, relation, T,
  known_as_of=None)` — the point-in-time value(s), no query.
- **Provenance:** each result carries `{valid_from, invalidated_at,
  invalidation_reason, resolution}` (§4b tag) — why it is the T-answer.

### 4d. Transaction-time (full bitemporal, optional)
`known_as_of=T_known` answers "what did we BELIEVE at T_known about T_valid"
(§4a step 2). `known_as_of=None` = "as of now's knowledge" — the parity
headline. The transaction axis is the audit bonus.

## 5. Regime analysis

- **`as_of=None`:** identical to today (V-COMPAT).
- **Hot subject, long history:** the interval scan wants an index on
  `(subject, relation, valid_from)` — pairs with storage-backend gap #3.
- **Deep correction chains / correction-then-supersession:** the composition is
  ruled for the single-correction case; multi-hop is §10.
- **Future `valid_from`:** a fact stated to become true later is not valid until
  then.

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **V-COMPAT** `as_of=None` reproduces the pre-feature current-facts result byte-identically | `test_as_of_none_is_pre_feature_identical` | CI |
| **V-REASON** resolution is TOTAL over the closed six reasons; a `corrected` fact returns the corrector not the error; an unknown reason fails closed (excluded + gap) | `test_reason_resolution_total_and_corrected_forward` | CI |
| **V-GATE** as-of never changes a record's assertable/restricted/quarantined/scope classification — checked on returned records AND grounded/unverified context | `test_as_of_preserves_classification` | CI |
| **V-DET** as-of is deterministic — same store + T + known_as_of → identical result; no LLM/embedding call | `test_as_of_is_deterministic_and_llm_free` | CI |
| **V-GAP** a gap or disputed period returns empty/fenced, never the nearest fact | `test_as_of_gaps_and_disputes_truthful` | CI |
| **V-CHAIN** a broken correction/absorption link yields a reported gap, never the errored/absorbed edge | `test_as_of_broken_chain_is_a_gap` | CI |
| **V-SCOPE** as-of resolves within the principal boundary; chain-following never crosses scope | `test_as_of_respects_scope` | CI |
| **V-BITEMP** `known_as_of` filters by `observed_at` correctly — a fact ingested after T_known is invisible at T_known | `test_transaction_time_axis` | CI |

### 6a. Acceptance measurement — REQUIRED, FINITE

Pre-committed BEFORE the run (R4). No public number without approval — but note
this is a CORRECTNESS gate (exact expected answers), not a quality metric, so
the pass is deterministic, not statistical.
- **Corpus:** `tests/eval/as_of/` — a NEW pinned fixture: for each of the six
  reasons, ≥3 (subject, relation, history, T, expected-resolution) cases, plus
  gap, future-valid_from, broken-chain, and transaction-time cases (≥30 total).
  Each case names its expected returned value AND `resolution` tag.
- **Determinism:** pure interval/reason logic — no external service; the fixture
  is the histories + the expected answers. Command:
  `pytest tests/eval/test_as_of_gate.py`.
- **Numeric pass criteria (pre-committed):**
  1. **Exactness:** 30/30 cases return the expected value AND `resolution` tag
     (a correctness gate — 100%, not a threshold).
  2. **Corrected-not-surfaced:** 0 cases return a `corrected` error as the
     T-value (V-REASON).
  3. **Classification unchanged:** the grounded/unverified partition over the
     trust-labelled cases is identical to a current-facts recall of the same
     resolved edges (V-GATE).
- Recorded results land in `## Review closure` at acceptance.

## 7. Failure modes and reversibility

- **Fully reversible:** `as_of=None` is today's behavior; the feature is
  additive; no schema change, so nothing to migrate or roll back.
- **Reason-registry growth:** a new invalidation reason must add a resolution
  row or the fail-closed rule excludes it (V-REASON) — the registry test
  (`schema.py:397`) already forces producers to declare a new reason; this spec
  adds "declare its as-of resolution too."
- **Cost:** a long history scan; the `(subject,relation,valid_from)` index is
  the reversible perf fix.

## 8. Claims and limits

- **Claim:** as-of returns the reason-correct value at T, gate-preserving and
  deterministic. *Limit:* multi-hop correction/supersession composition is ruled
  only for the single-correction case (§10).
- **Evidence (field contrast):** GENOME (`hybrid/temporal`) and Mem0-Platform do
  VALID-TIME INTERVAL MATH — return the interval containing T — because their
  supersession carries no reason; a corrected error and a genuine change are
  indistinguishable to their as-of, and both surface as history. Veracium's
  six-reason supersession is exactly what makes §4b possible. (Neither gates
  the as-of result by trust either — §3 is unmatched.) *(Ship the design doc's
  evidence with this spec at review.)*
- *Where we may overstate:* "more correct than the field" holds for the reasons
  we resolve; a reviewer should test `corrected-forward` and the gap cases
  (V-REASON, V-GAP), not take the table on faith.

## 9. Brief for the external reviewer

The spine: as-of is a **reason-aware time filter, orthogonal to trust**. Attack
hardest:
1. **V-REASON / §4b.** Is the reason table TOTAL and correct? Especially
   `corrected-forward`: does returning the corrector (not the error) hold when
   the corrector was itself later superseded or corrected? (single-hop ruled;
   §10 flags the composition — tell us if you think it must be ruled now.)
2. **V-GATE.** Is trust classification PROVABLY unchanged by the time filter —
   a disputed/quarantined fact valid at T returns fenced, never assertable?
3. **V-BITEMP.** Is the `observed_at ≤ known_as_of` + `invalidated_at ≤
   known_as_of` logic right for out-of-order ingestion?

## 10. Open questions

- **`disputed` → non-assertable:** research's ruling (§3); gate-owner confirms
  (V-Q1-style, like 0026). Alternative: exclude entirely.
- **Correction/supersession composition:** a fact corrected, then the corrector
  genuinely changed — which value at a T inside the original interval? Ruled
  single-hop (return the corrector valid at T); the multi-hop chain needs a
  ruling before it ships. Recommend: resolve the chain to the edge whose
  effective (retroactively-extended) interval contains T.
- **Non-functional accumulation under correction:** if one value in an
  accumulating set is corrected, does the set at T drop it? (Yes, by §4b per
  member — but confirm.)
- **Index:** `(subject, relation, valid_from)` — ships with backend gap #3 or
  now?
- **The §4c lane asymmetry** (stale-embedding history is lexically- but not
  semantically-recallable under as-of): acceptable as a disclosed property,
  or should as-of access trigger a lazy re-embed of its slice? (Dev leans
  acceptable-as-disclosed for v1 — re-embedding on a read path couples the
  read to the embedder and V6's latency posture; the reviewer may rule.)

## Review closure

**Round-1 external verdict (2026-08-31): RETURN — seven blocking
amendments.** "The reason-aware architecture is promising, but the current
specification assumes temporal and classification capabilities the shipped
model does not provide." All seven verified factually real against the
shipped code before any fold: R1-1 the registry holds SEVEN reasons
(`revoked_source`, 0022's seat) — this spec's "closed six" failed
verification against the authoritative `DISPOSITIONED_REASONS`; R1-2
`known_as_of` is unimplementable from the stated fields (`invalidated_at`
is a valid-time endpoint; no transaction-time carrier; the reviewer's
backdated-correction counterexample); R1-3 STRUCTURAL — `Edge.assertable`
requires `active`, so no historical edge can ground under the unchanged
classifier; R1-4 chain/arity mechanics undefined (backward `supersedes`,
note-carried absorption links, the `absorbed-to` row unreachable through
§4a by the empty-interval construction); R1-5 correction chains can cross
scope (source identity, not subject; 0020 owns read visibility); R1-6 the
recall baseline is misstated (`active_only=False` history already flows)
and V-DET overclaims for the composed path; R1-7 the result/gap carriers
and the acceptance corpus are not finite.

**Owner's ruling (2026-08-31): HOLD FOR THE BIGGER SHAPE.** Rather than
narrowing v1 to reference-only valid-time (dev's proposed disposition,
research concurring), the missing substrate is specced first — a durable
TRANSACTION-TIME carrier for invalidations and mutations, and a
TIME-RELATIVE trust classification with exact rules keeping corrected/
disputed/quarantined/restricted/revoked material out of grounded — so a
future v2 can deliver assertable history and true bitemporal. This arc is
PAUSED until those substrate specs are accepted; the round-1 findings then
fold into v2 on the new foundation. No implementation exists; nothing
ships from this spec meanwhile.*
