# Feature spec: generated-content trust class (`EvidenceAuthor.ASSISTANT`)

Spec-Status: draft
Spec-Requires: 0003, 0005, 0007, 0008, 0012, 0013, 0016, 0018, 0024

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — the current revision and its changelog pointer are stated ONCE, in the **Version** row below (R10-2: this opening block carried "v10" beside a v11 Version row — the third version-carrier strike, so the block now carries NO revision). Round 8 found NO new trust-model defect and named the finite-acceptance gate: *"Once those narrow items close, I would recommend finite acceptance of 0001 v9 without reopening the frozen architecture."*
>
> v5 — Round 3 (the line's first
> SEALED round) returned SIX blocking findings, every one an executed
> collision between this spec's promises and a contract that SHIPPED while
> it sat deferred: `confirm_edge` refuses the promotion v4 promised (0008),
> the on-disk guard was never activated (SCHEMA 10→11 now specified, I13),
> two operation-matrix cells were measured false against 0012/the 0.4.1
> guard, I6 named a test with no rule (the reserve rule is now exact), Q4
> rode a field 0016 deleted, and three more v2-form carriers survived the
> v4 sweep. §15 maps each finding to its fix. Earlier: v2 deferred
> 2026-07-31 (widening withdrawn); v3 deferred 2026-08-01 on the render-
> marker gate, closed in shipped code 2026-08-15; v4 (§14) recorded the
> closure, ran the currency pass, and answered the five post-v3 eras
> (§2d). The v4 lesson, now twice-learned: a currency pass must verify
> every NAME it carries still resolves, not only re-run its commands.
> deferred at external review 2026-07-31; v3 (the narrowed rewrite) was
> re-reviewed 2026-08-01 and deferred on one blocking amendment — the render
> marker keyed on `use_only` with hardcoded third-party text. **That gate
> CLOSED in shipped code 2026-08-15** (`graph._ORIGIN_LABELS` keys on the
> author, an unlabelled class fails safe to `unverified-origin`, and
> `tests/test_render_origin.py` trips on any new author class without a
> label — 6 passed on the tree this candidate ships from). v4 = v3's ruled
> content with the gate closure recorded, every mechanical claim RE-EXECUTED
> against v0.13.0+ (eleven releases of drift — §2/§2c-ii), the v2-form
> carriers §13 missed rewritten in place (§14 lists them), and the five
> specs that shipped consumers since v3 was written answered in §2d.

*Fill this in **before** implementing. See `PROCESS.md`.*

> First spec through the full process. Numbering starts at `0001`; the `0007`
> in `PROCESS.md`'s examples is illustrative, not a reservation.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v20** — the round-17 fold plus the TERMINUS QUESTION (§29, §30): the fold is unchanged from v19; this revision adds `specs/evidence/0001/TERMINUS-NOTE.md` as an ARCHIVE MEMBER (not a side-channel companion — the A1 PACKAGE-R23-1 lesson applied at birth), asking how the evidence-machinery series should close. It contests no finding. *Prior:* **v19** — the round-17 fold (§29): R17-1 the PRODUCTION path is bound to the tested one — the runner was optional, so the injected path and the production path were different paths and only the injected one was bound; a branch returning the shipped record whenever no runner was supplied left every test green while production `--verify` compared the record with itself. The runner is REQUIRED now (`_measure_with_runner(base, run)`) and `measure(base)` is a delegation and nothing else, with a regression proving it reaches the implementation carrying the requested base and the PRODUCTION runner. Three production-path mutants planted and each verified failing. *Prior:* **v18** — the round-16 fold (§28): R16-1 the PRODUCER is bound — every consumer of the results record was tested while `measure()` itself was not, so replacing its body with a read of the record made the verifier compare the shipped record with ITSELF, report exact replay in a non-git extraction, and leave the whole gate green. `measure()` now takes an injectable subprocess seam and a behavioural regression drives it with canned outputs deliberately unlike the shipped record's: the declared base must be materialised, the shipped patch applied, both exact suite commands run INSIDE the built tree, and every number and node id in the record derived from those outputs. Three producer-collapse mutants planted and each verified failing. *Prior:* **v17** — the round-15 fold (§27): R15-1 the CONNECTION from enforcement to `--verify` is bound — every link was tested separately (main() reaches the enforcement; the enforcement aborts on nonzero; `--verify` compares records) while the join was free, so dropping `--verify` from the argv ran the helper in its default measure-and-print mode, exiting 0 without comparing, with the whole gate green. The regression now asserts the EXACT invocation and working directory, proves the `--verify` branch returns nonzero on a planted record difference (with an identical-replay control), and documents by assertion that the default mode exits 0 without comparing — which is why the argv binding is load-bearing. Three connection-breaking mutants planted and each verified failing. *Prior:* **v16** — the round-14 fold (§26): R14-1 reachability is proved BEHAVIORALLY, not syntactically — the round-13 test searched main()'s AST and rejected only a literal constant-false guard, so the reviewer's `if a.version == "v0"` read as an ordinary call, disabled replay for every real package, and left both replay tests and the whole spec gate green. The test now EXECUTES main() with the current package identity, monkeypatches the enforcement to raise a sentinel and REQUIRES that sentinel to be reached, with a second sentinel on the measurement that names a bypass directly; the call itself is now an UNCONDITIONAL fail-fast precondition ahead of the measurement, so there is no condition left to falsify — only deletion, which the test also catches. Three bypass shapes planted and each verified failing. *Prior:* **v15** — the round-13 fold (§25): R13-1 the seal-time replay was sound but UNPROTECTED — a planted `if False` on its call left the named matrix and the whole spec gate green, so the only decisive guard could be removed silently. The enforcement is a NAMED, injectable seam now (`enforce_candidate_replay`) and a regression at the SEALER BOUNDARY binds three properties: `main()` calls it on a REACHABLE path (both the reviewer's `if False` and outright deletion fail the test — verified by planting each), a FAILING replay aborts the seal with a pristine control, and the comparison catches the type-valid fabrications the extraction checker deliberately cannot, including failure-IDENTITY replacement. *Prior:* **v14** — the round-12 fold (§24): R12-1 the results record is validated against a CLOSED, exactly typed schema — every claimed field, not the four the first checker's author happened to bind (the reviewer passed forty-zero base + python 0.0.0, and a duplicated failure entry, through the old projection); `failure_set` sorted/unique/node-id-shaped/cardinality-equal; the commands IMPORTED from the generator; and the base made INDEPENDENTLY REPRODUCIBLE — `measure_candidate.py --verify` regenerates the complete record from the declared base and the SEALER refuses on any field difference. *Prior:* **v13** — the round-11 fold (§23): R11-1 the candidate figures are GENERATED and BOUND — `measure_candidate.py` applies the shipped patch to a clean tree and runs both suites into `candidate_results.json` (focused 21; full 16F/1813P/20S with its failure set), `check_candidate_results.py` refuses any disagreement between record, patch bytes and the README's figures, and it runs in the sealer's extraction checks so a stale count cannot reach a package. **Round 11's verdict is FINITE DESIGN ACCEPTANCE for draft v12** — R10-1 and R10-2 verified closed, the trust-model architecture not to be reopened; this package carries the mechanical evidence-carrier correction it asked for. *Prior:* **v12** — the round-10 fold (§22): R10-1 the I6 reserve restricted to query-RELEVANT assertables (the relevance bit carried from scoring; the bananas counterexample is the regression), R10-2 the opening block carries no revision. *Prior:* **v11** — the round-9 fold (§21): R9-1 the I6 implementation CONSTRUCTED, not filtered (reserved + remainder, the non-functional placement vector, full-order dedup), R9-2 the last version carrier purged, R9-3 the measurement re-run and environment-stamped. *Prior:* **v10** — the round-8 fold (§20): the four narrow evidence items the reviewer named as the last gate before recommending FINITE ACCEPTANCE. *Re-read before editing; quote the version you approve.* |
| **Status** | *see `Spec-Status:` at the top — canonical.* v2 deferred; v3 deferred (render-marker gate, closed in code); v4 returned round 3; v5 returned round 4; v6 returned round 5; v7 returned round 6; v8 returned round 7; v9 returned round 8 (narrow); v10 returned round 9 (the acceptance candidate — R9-1 found the I6 construction defect the order vectors' own shape had masked); v11 returned round 10 (R10-1 relevance vs eligibility; C-plus ACCEPTED that round); v12 received **FINITE DESIGN ACCEPTANCE at round 11**; v13–v18 returned at rounds 12–17 (R12-1, R13-1, R14-1, R15-1, R16-1, R17-1) — the finite acceptance STANDING throughout, the architecture frozen on the complete §6 surface, and every return in the evidence layer; **v20 is the round-18 external candidate — the status flip follows the reviewer's confirmation of this reseal, which also carries the terminus note.** *(R5-5: this row is a version CARRIER and is now part of the pre-send sweep.)* |
| **Internal reviewers** | **research — reviewed 2026-07-31, accepted with amendments** · workflow-platform *(MCP surface changes)* — pending |
| **External review** | **returned 2026-07-31 — defer / major amendment.** Response: `proposals/spec-0001-external-review-response.md` |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation

An assistant turn is authored by none of the three parties we model. Today a
host must call it `SYSTEM` (→ mentionable, so **a hallucination becomes an
asserted fact**) or `THIRD_PARTY` (→ `use_only`, so **the assistant reporting
the user's own state is unusable**). Both are wrong, and we have measured the
cost of each: benchmark Arm T, which treats assistant turns as system-authored,
scored **7/8 on abstention where Arm C scored 8/8** (LongMemEval pilot, run
`20260730T174434`), and Arm C's capping produces **4 of 9 answer-misses**,
including `184da446`.

**Field demand, reported (2026-08-23):** Research's competitive scan of
Mem0's "State of AI Agent Memory 2026" report (triaged in
`veracium-research/scans/KNOWN_IDS.md` + the MEM0_DOSSIER; paraphrased
here from the scan record, not quoted — the verbatim sentence was not
re-verifiable at fold time) reads the category leader naming actor-aware
memory — separating user-stated facts from agent-generated inferences —
as a first-class need, with Sentra's founder essay (Apr 2026 per its
public page) putting provenance in episodic grounding. Neither ships an enforcement mechanism:
Mem0's is a retrieval-time filter (represent-not-enforce, in this repo's
terms). The class is therefore field-named; **this spec's contribution is
the mechanism difference — enforce at ASSERTION with the `use_only`
floor, not filter at retrieval.**

**If we do nothing:** every host embedding veracium in an assistant loop — which
is the primary deployment — makes this choice itself, silently, with no
vocabulary to describe what it chose. The `SYSTEM` branch is the dangerous one
and is also the convenient one, so it is what hosts will pick.

**Alternatives rejected.**

- **A host toggle for assistant assertability** *(dev proposed; research
  rejected — `q2-4-generated-content-answer.md`, accepted here)*. Principal–
  agent: the host sets the policy, **the user carries the risk**, and
  documenting the trade-off does not help because the party reading the docs is
  not the party paying. It would also convert an enforced guarantee into a
  configurable one, which is the exact distinction we draw against competitors.
- **A fourth `Disclosure` tier.** The tier was never the problem; the author
  was. `use_only` already means "real-looking, unverified, never asserted".
- **Reusing `SYSTEM`.** `SYSTEM` means *our own* consolidation and maintenance
  output, which we generate and can reason about. Assistant text is
  externally generated and may be adversarially influenced. Conflating them
  makes both unanalysable.
- **Letting `derived_from` express it.** Blocked by design: `derived_from` may
  only **cap** trust, never raise it (the 0.1.7 laundering defence). "The
  assistant is restating the user, therefore assertable" cannot be said with it,
  and must not be bolted on.

---

## 2. Field contracts touched

*Provenance: reinforcement silently overwrote `valid_from`, whose documented
meaning at three code sites is "when the fact became true". The renderer then
emitted `(since <that value>)` into the answer context — a false statement
injected into recall. Nobody had enumerated who reads the field.*

| field | read / written | its **documented** contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `Provenance.author_of_evidence` | written by `ingest`, read by **18 src modules** *(re-enumerated 2026-08-22 — was 8 at v3; the growth is 0003/0005/0020–0022/0025 shipping, see §2d)* | "Who authored the evidence. The core injection-resistance signal." | `ingest` (`_disclosure_for`), `authority` **(the 0003 supersession ladder — §2d.1)**, `portability` **(the 0005 import cap — §2d.2)**, `graph` **(`_ORIGIN_LABELS`, the closed v3 gate)**, `contribution`, `scope`, `scope_read`, `store/revocation`, `store/sqlite` **(consolidation min-trust at the fenced write — the old `lifecycle:101` defect's discharged home, see below)**, `lifecycle`, `introspect`, `__init__`, `compile`, `proactive`, `cli:410` **(hardcoded `choices=`, and `:414` `--derived-from` is a SECOND hardcoded list v3 predates)**, `mcp_server:38` (fail-closed host map — §2d.6), `selfcheck`, `schema`, plus **61 test files**, 5 docs and 2 examples | **Yes — extended, not redefined.** No existing member changes meaning. **But the value set is no longer closed**, which is the contract change that matters: every consumer branching on it must be re-read, not assumed — and at 18 modules that re-read is §2d, done per era. |
| `Episode.provenance.author_of_evidence` | written by `ingest`, **rewritten by `lifecycle.consolidate`** | same field, on episodes | `gate` (via episode authorship), `graph` (episode rendering) | **NO — see the defect found below.** |
| `Edge.subject` | written by `ingest`, read by `graph`, `compile` | the entity a fact is about; `"user"` is the reserved literal for the store owner (`graph.py:201`, `graph.py:295`) | `graph._cover`, `graph.render_edges`, `compile`, `introspect` | **Yes — unchanged in role** *(v5, R3-6: this cell still described v2's subject routing; under the every-subject rule the subject gates NOTHING — disclosure is author-derived, a mis-extracted subject changes rendering only)*. |
| `Provenance.disclosure` | written by `ingest._disclosure_for` | mentionable / use_only / quarantined | `Edge.assertable`, `gate`, `graph`, `proactive`, `introspect` | **Yes** — no new value; only a new way to arrive at `use_only`. |
| export `version` (`portability.FORMAT_VERSION = 8` today — *was 2 when v3 was written; 0006/0014/0016/0019/0025 each bumped it*) | written on export, checked on import | "an export version newer than this library fails closed" | `portability.load` | **Changed deliberately → 9 at implementation.** See §7: without the bump, an older library hits a pydantic `ValidationError` instead of our own message. |

**Consumers enumerated mechanically** (`grep -rn`, both `src/` and outside it —
the `src/`-only form used previously misses tests and docs that encode the
contract):

```
$ grep -rln "author_of_evidence\|EvidenceAuthor" src/ tests/ docs/ examples/ README.md   # re-run 2026-08-22
src/veracium/{schema,ingest,lifecycle,introspect,__init__,cli,mcp_server,selfcheck,
              authority,compile,contribution,graph,portability,proactive,scope,
              scope_read}.py  src/veracium/store/{revocation,sqlite}.py
tests/ (61 files)  docs/{api,concepts,design-rationale,recipes}.md  README.md
examples/{demo.ipynb,langchain_memory.py}
```

**⚠️ I first wrote this table from memory and it was wrong in both directions,
which is the rule earning itself on the first spec that used it.** I had listed
`gate.py`, `graph.py` and `portability.py` as consumers when at v3 time they
referenced the enum zero times. **Two of those three became true consumers
after v3 was written** — `graph.py` via `_ORIGIN_LABELS` (the closed v3 gate)
and `portability.py` via the 0005 import cap — which is its own lesson: a
blast-radius enumeration is a DATED measurement, not a property of the design,
and this spec's §2c-ii re-runs it at every version. `gate.py` still references
it zero times (it branches on the derived `disclosure` field).

**Consumers needing code changes, re-verified 2026-08-22:**

- **`cli.py:410`** — `--author` carries `choices=["user","third_party","system"]`,
  a hardcoded public CLI surface that silently rejects `assistant` until
  updated. **And `cli.py:414` — `--derived-from` carries the SAME hardcoded
  list**; it postdates v3 and must gain `assistant` in the same change (a
  host relaying assistant-derived content is the `derived_from` case).
- **`lifecycle.py:101` — the trust-laundering defect v3 recorded here is
  DISCHARGED.** The whole-set-minimum-trust rule (INFERRED author, min
  confidence, weakest disclosure, retained third-party influence) was the
  0.4.4 security fix and now lives at the STORE's fenced write boundary —
  `write_consolidation_output_if_current._derive_output_metadata`, required
  there by 0010 X23 so derived fields are computed from the claimed set at
  the write, not by the caller. I10's obligation survives as: the min-trust
  derivation must treat `ASSISTANT` correctly in that store-side rule (an
  assistant member caps the set at `use_only`).

**Documentation stating the old meaning, updated in this change:**
`docs/concepts.md`, `docs/api.md`, `README.md` trust-model table, the
`EvidenceAuthor` docstring, and `mcp_server.py`'s tool description.

---

## 2c-ii. Assertions about reach

*Required since the §2c-ii amendment. Every claim below carries the command that
establishes it, not a statement that it was checked — **both prior versions of
this spec failed on unverified assertions about what was reachable.***

*(re-executed 2026-08-22 against the candidate tree; the v3-era results are
struck where they moved)*

| assertion | command | result |
|---|---|---|
| `EvidenceAuthor` has exactly 3 members today | `grep -A6 "class EvidenceAuthor" src/veracium/schema.py` | `USER`, `THIRD_PARTY`, `SYSTEM` |
| a host can set the author via MCP | `grep -n "EvidenceAuthor" src/veracium/mcp_server.py` | ~~`:26`~~ `:38` `_AUTHOR` maps **`user`/`third_party` ONLY** — `system` was deliberately removed and unknown authors now **raise** (fail-closed; the silent-fallback-to-USER path is gone). §2d.6 rules how `assistant` joins. |
| the CLI `--author` list is hardcoded | `grep -n "choices" src/veracium/cli.py` | ~~`:299`~~ `:410` `["user","third_party","system"]` **and `:414` `--derived-from`, the same list — a second carrier v3 predates** |
| `import` is a shipped CLI verb with `--user` | `grep -n '"import"' src/veracium/cli.py` | `:367` `import`; `--user` on the recall/import surfaces |
| which combinations reach `use_only` | `_disclosure_for` over the enum product | user+3P · 3P+any · system+3P *(unchanged; the quarantine-relation clause precedes them — the 0024 seam, §2d.4)* |
| an older library cannot load an `assistant` edge | `Provenance(author_of_evidence='assistant')` | `pydantic.ValidationError` |
| the v3 render gate is closed | `grep -n "_ORIGIN_LABELS" src/veracium/graph.py && python -m pytest tests/test_render_origin.py -q` | `:633` author-keyed map, `:648` fail-safe `unverified-origin`; **6 passed** |
| the authority ladder pre-provisions `assistant` | `grep -n "assistant" src/veracium/authority.py` | `:41` `_RUNGS = {"user": 3, "system": 2, "assistant": 1, "third_party": 0}` — placed there by 0003 naming this spec |
| ~~no `PRAGMA user_version` guard exists~~ *(dated: true at spec time; `0007` shipped the guard in v0.5.0 — it lives in `store/schema_version.py` + `store/migration.py`, so this command still shows no match in `sqlite.py`)* | `grep -n "user_version" src/veracium/store/sqlite.py` | no match *(guard is in `store/schema_version.py` since `0007`)* |

---

## 2d. Consumers that did not exist when v3 was written — each answered

*v3 is dated 2026-08-01. Since then 0003, 0005, 0020–0023 and 0025 shipped,
and several of them branch on the author. A spec that opens this enum's value
set owes each of them an answer, not a re-count.*

1. **0003 — the supersession authority ladder (`authority.py`).**
   `_RUNGS = {"user": 3, "system": 2, "assistant": 1, "third_party": 0}` —
   0003 pre-provisioned the `assistant` rung, naming this spec in its comment.
   **v4 RATIFIES rung 1**: the assistant's own claims outrank third-party
   hearsay (it is at least an identified, in-conversation source) and rank
   below both principals. **No `RULE_VERSION` bump is needed at
   implementation**: adding a member the map already carries cannot flip any
   pair over the existing members — `effective()` and `permitted()` over
   USER/SYSTEM/THIRD_PARTY inputs are byte-unchanged. A pair involving
   `ASSISTANT` was previously unconstructible, so no historical refusal
   re-evaluates differently (the 0011 concern).
2. **0005 — the import trust boundary (`portability.py`).** A non-restore
   import caps every record: `author_of_evidence := THIRD_PARTY`. An exported
   assistant edge therefore arrives THIRD_PARTY on ordinary import — authority
   drops 1 → 0, disclosure stays `use_only` either way. **Conservative in the
   right direction and ratified as-is**: the file's claim about who authored
   a record is exactly what 0005 says an import may not assert. `restore=True`
   (the operator's explicit opt-out) preserves `ASSISTANT` faithfully.
3. **0022/0023 — source revocation.** Keyed on `source_id` identity digests,
   author-orthogonal. An assistant-authored edge with a `source_id` revokes,
   quarantines at birth, and lifts like any other; `QUARANTINED` is a stronger
   floor than this spec's `use_only`. No interaction beyond stating it.
4. **0024 — authorship before structural quarantine (accepted, implementation
   frozen).** 0024 and this spec edit the SAME function: `_disclosure_for`.
   0024 refines the author/relation precedence for `third_party_claim`
   mislabels; this spec adds an `ASSISTANT → use_only` clause. **The two edits
   are additive and commute** — both strengthen the min-trust rule, neither
   touches the other's branch — but they must be sequenced consciously at
   implementation (0024's fix lands first per its freeze protocol; this
   spec's clause rebases on it).
5. **0025 — relation-vocabulary enforcement.** Orthogonal: relations, not
   authors. An off-vocabulary relation on an assistant event lands
   `unclassified` carrying `ASSISTANT` unchanged; the reserved
   `third_party_claim` convention is about content source, which
   `derived_from` already expresses.
6. **The MCP author surface (`mcp_server.py:38`).** Since v3, `system` was
   deliberately REMOVED from the host map and unknown authors fail closed
   (the silent fallback resolved typos to USER — the highest class).
   **`assistant` JOINS the map**: unlike `system`, adding it is
   self-*demotion*, not self-elevation — a host labelling model-generated
   content `assistant` gets rung 1 and `use_only`, which is this spec's
   entire purpose. `system` stays excluded.

---

## 3. Trust-class matrix — REQUIRED, blocking

*Provenance: T1 subset-absorption merged edges without checking authorship or
disclosure, so a third-party restatement could retire a user-asserted fact out
of the assertable set and inherit its confidence. Advisory GHSA-r7j7-5jq9-3f5q.*

**Directional, because our operations are.** `apply_supersession` and T1
absorption both distinguish the **surviving/prior** edge from the
**incoming/candidate** one (`graph.py:_subsumes(pk, same)`), and the 0.4.1
defect lived exactly in that asymmetry. A single `user × assistant` cell cannot
express it, so both directions appear.

**Enumerated from code, not from memory:** `EvidenceAuthor` = `USER`,
`THIRD_PARTY`, `SYSTEM`, **`ASSISTANT`** (new); `Disclosure` = `MENTIONABLE`,
`USE_ONLY`, `QUARANTINED`.

### 3.1 Write-time disclosure — NARROWED IN v3

**v1 routed on the subject and failed. v2 tried to fail closed on a
"recognised" subject and failed differently — the predicate was unbuildable
(no entity resolution, no display name, 19,096 distinct subjects across 131,574
extracted triples, only 39.4% the literal `"user"`). v3 does not route on the
subject at all.**

| author | derived_from | disclosure |
|---|---|---|
| `ASSISTANT` | — | **`use_only`**, for **every** subject |
| `ASSISTANT` | `THIRD_PARTY` | `use_only` (existing cap; unchanged) |
| `ASSISTANT` | relation == quarantine | `quarantined` (unchanged) |

**One rule, no subject inspection, no new predicate.** Promotion is
AFFIRMATION — new USER evidence via `remember(author=USER)` (§3.2's row;
v5/R4-1 terminology: *affirmation* creates user evidence; *confirmation*
(`confirm_edge`, 0008) clears staleness on an already-assertable edge and
refuses everything else; a non-assertable assistant edge is NEVER promoted
in place).

**What this gives up, stated plainly:** the *"the test suite passed"* case stays
`use_only`, so an assistant's first-party report of its own action is not
directly assertable. **That capability now depends on the evidence-basis axis
(research's, its own design round), which is the right home for it** — a
deployment result should be groundable because an authenticated tool returned
it, not because an assistant said so.

**What it buys:** hosts stop mislabelling assistant content as `SYSTEM`, which
is the dangerous *and* convenient default, and no new persistent assertion
channel opens. **That was always the majority of the value.**

### 3.2 Operations, both directions

*(v5, R3-1/R3-3: this table is rewritten against the SHIPPED contracts it
must compose with — the 0003 authority ladder governs cross-class functional
supersession (not the 0.4.1 same-disclosure guard, which governs absorption
and reinforcement), 0012 governs same-class restatements, and 0008's
`confirm_edge` refuses every non-assertable edge BY CONTRACT. The v4 table
promised two cells the code refuses and named the wrong mechanism for a
third; the reviewer executed all three.)*

| operation | prior=USER, incoming=ASSISTANT | prior=ASSISTANT, incoming=USER | ASSISTANT × ASSISTANT | involving quarantined | involving `use_only` |
|---|---|---|---|---|---|
| **supersession** (functional relation) | **refused by the AUTHORITY LADDER** (rung 1 < rung 3; durable content-free refusal recorded, 0003 §4b) — not the disclosure guard | **allowed by the ladder** (rung 3 ≥ 1): the user's new evidence retires the assistant prior — THE AFFIRMATION PATH (see the affirmation row; *v8/R6-5: this cross-ref said `confirm()` — a live pointer to a renamed row, caught after the zero-survivor sweep because the sweep grepped the RULE'S phrases, not row NAMES*) | allowed (equal rung); same-value handling per 0012 — see the restatement row | never | ladder governs; disclosure does not block cross-class supersession |
| **T1 absorption** (subset) | **blocked** — the equal-disclosure-class restriction (0.4.1 guard) | **blocked — the SAME guard, v5 correction**: `mentionable` user evidence cannot absorb a `use_only` assistant edge; both records persist, and the functional case is handled by supersession above. *(v4 claimed "allowed; winner is the user edge" — measured false: both stay active. Cross-class absorption would also inherit max confidence and `observed_at`, letting assistant metadata alter the user survivor — the exact laundering 0.4.1 exists to stop.)* | allowed when same class | never | only within class |
| **restatement** (identical fact, same class) | n/a (cross-class — see supersession) | n/a | **the incoming restatement PERSISTS UNTOUCHED (0012): no merge, no mutation of the prior — the currency-refresh hazard Q1 named is structurally absent**, and the read path collapses strict redundancy at render (0012 §4c). *(v4 said "merge allowed, refresh blocked" — 0012's shipped model is persist-and-collapse, which delivers Q1's intent without a store-side merge.)* | never | only within class |
| **affirmation** (was: `confirm()`) | n/a | **a user affirmation is NEW USER EVIDENCE**: the host ingests it (`remember(author=USER)`). Same value: the user edge becomes the ASSERTABLE carrier; the assistant prior persists un-asserted (nothing to supersede) — **and the two records RENDER IN SEPARATE TRUST PARTITIONS** (v5/R4-2, measured: `collapse_for_render` groups by `(subject, relation, disclosure, author, derived_from)`, so cross-class records can never share a group — 0012's trust-envelope isolation, PRESERVED deliberately; a cross-class presentation rule would weaken it and is out of scope). The grounded block carries the user's fact; the unverified block still shows the attributed assistant claim. Different value: the ladder retires the prior — full supersession, audit and retry semantics for free. *(Both shapes measured: `candidate_harness.py`.)* **`confirm_edge` (0008) is NOT this path and refuses every non-assertable edge by contract — this spec PRESERVES 0008 unamended** *(v5, R3-1: v4 promised a promotion `confirm_edge` refuses; the reviewer executed the refusal)* | n/a | never — nothing elevates quarantined | affirmation supersedes it; nothing flips it in place |

**Q1 resolved — `ASSISTANT × ASSISTANT`: allow the merge, block the currency
refresh.** I had proposed blocking the merge outright on a
compounding-confidence hazard. Research showed the hazard is not confidence —
`confidence = max(members)` synthesises nothing, so two assistant statements
merging cannot manufacture a higher number than either held. **The exposure is
currency.** Reinforcement refreshes `provenance.observed_at`, which under C′ is
the liveness axis `lifecycle.expire()` ages against. So an assistant restating
its own hallucination would keep it fresh **indefinitely** — freshness-pinning
by self-repetition, which is the manufactured-freshness failure the T2 debate
settled, one trust class down.

**Rule: an assistant restating itself is deduplication, not evidence** —
and 0012 delivers this structurally: the restatement persists as its own
record, the prior is byte-untouched (no `observed_at` refresh is possible
because no mutation happens), and the render path collapses strict
redundancy. **I10a asserts the prior's byte-equality**, which is Q1's
intent expressed against the shipped mechanism. Assistant edges **age out
normally**: a statement about an action is point-in-time, not a
persistent state.

**Reinforcement across classes is blocked in *both* directions and that is
deliberate.** A user
restating an assistant claim looks like reinforcement, but under the C′
semantics reinforcement mutates `provenance.observed_at` on the **prior** edge —
so allowing it would let user evidence refresh the currency of an
assistant-authored statement while leaving it assistant-authored. The user's
statement must create a **new user edge** that then supersedes. Slightly more
storage; no laundering.

**Answering the four required questions:**

- **Can this cause a user-asserted fact to become non-assertable?** No. Every
  operation where an assistant edge is the incoming side against a user prior is
  blocked by the same-disclosure-class guard. **§6 I3 tests this rather than
  assuming it** — that guard was written for third-party edges and its behaviour
  on a new author class is exactly the kind of thing that survives review by
  looking obviously fine.
- **Can non-user content gain user-grade authority, confidence, or currency?**
  Never in place: only a user AFFIRMATION — new USER evidence carrying its
  own authority, never transferring any (v6→v7, R5-1: the third surviving
  carrier of the withdrawn rule, finally executed dead). `derived_from`
  still cannot raise trust.
- **Can it clear `needs_confirmation`?** Only 0008's confirmation on an
  already-assertable edge, unchanged (v5/R4-1: distinct from affirmation).
  Dedup and maintenance still never clear it.
- **Does it merge, drop, or overwrite provenance?** No new path. Blocked merges
  leave both edges intact and dated, which is the additive-noise side of the
  asymmetry we prefer.

**Write-time or maintain-time?** **Write-time.** Disclosure is assigned when
evidence arrives. No maintenance operation may re-derive an edge's disclosure
from its subject afterwards — that would let a rename or a re-extraction change
assertability with no new evidence, which is the manufactured-freshness failure
the T2 debate settled.

---

## 3b. Authorization and scope — *full specs only*

*Trust class answers **whose claim this is and what authority it has**. It does
not answer **which user is permitted to see it**.*

- **Does this cross a user, tenant, or scope boundary?** No. Every edge is
  written under one `user_id` and every read is scoped to it; this change adds
  an author value and does not touch scoping.
- **Who may see the affected state, and does this change that set?**
  **Unchanged set AND unchanged volume** *(v4 carrier sweep: the v2-form text
  here still described the withdrawn widening)*: under v3/v4 every assistant
  edge is `use_only`, which is never volunteered proactively and never
  asserted. Relative to the honest alternative hosts use today
  (`third_party`), nothing becomes more visible; relative to the dishonest
  one (`system`), visibility strictly narrows — which is the point.
- **Scope change (sharing, revocation, group join/leave)?** n/a — no sharing model.
- **Anything visible to a principal who could not see it before?** No new
  principal, and **no visibility widening at all** *(v5, R3-6: this bullet
  still carried v2's subject-scoped widening)* — every assistant edge is
  `use_only`, never volunteered, never asserted; the only route to an
  assertable statement of the fact is a user AFFIRMATION creating its own
  USER edge (§3.2; R5-1 sweep).

---

## 4. Behaviour

`EvidenceAuthor.ASSISTANT` becomes accepted wherever an author is accepted:
`Memory.remember(..., author=EvidenceAuthor.ASSISTANT)` and the MCP `remember`
tool's `author` string (`"assistant"`).

Observable difference, given the same text:

| host says | before | after *(v4 carrier sweep: this table still showed the withdrawn v2 widening)* |
|---|---|---|
| `author="assistant"`, *"the deploy failed"* | not expressible; `system` → asserted, or `third_party` → `use_only` | **`use_only`** — rendered in the unverified block with an honest origin label, never asserted; groundability of first-party tool results is the evidence-basis axis's question, not this spec's |
| `author="assistant"`, *"you prefer dark mode"* | same bad choice | **`use_only`** — same block; a user AFFIRMATION creates the assertable user edge (§3.2; v5/R4-1: nothing promotes in place) |

**Exact rendering change:** every assistant edge renders in the existing
unverified block, attributed per §4b; **no new sentence form is introduced**,
because rendered text becomes model context and a new phrasing is a change to
what the model reads. No assistant edge EVER reaches the grounded block —
the grounded carrier a user affirmation creates is a USER edge, and the
assistant record stays in its own partition (v5/R4-1/R4-2).

### 4b. Rendering — the decision, RESOLVED (Q5) and partly shipped

Attribution must survive into the rendered context, or the class is pointless:
the whole finding from Workstream C is that a system with nowhere to *put*
provenance loses it. Research proposed keying the marker on
`author_of_evidence`:

```python
ORIGIN_MARKER = {THIRD_PARTY: " [third-party-reported; unconfirmed]",
                 ASSISTANT:   " [assistant-generated; unverified]",
                 SYSTEM:      " [system-derived; unconfirmed]"}
```

**Their four design decisions are adopted unchanged**: the default is a *marker*
not silence, so a forgotten class yields more caution; no author maps to empty;
*generated* rather than *reported*, leaving room for the evidence-basis axis;
and it dissolves the pre-existing quarantined/inference conflation.

**But keying on author alone discards `derived_from`.** Measured — the
combinations that actually reach `use_only` today:

```
author=user         derived_from=third_party  -> use_only
author=third_party  derived_from=(any/none)   -> use_only
author=system       derived_from=third_party  -> use_only
```

**`SYSTEM` reaches `use_only` ONLY via `derived_from=THIRD_PARTY`**, so
*"system-derived"* would name the relayer as the origin when a third party is.
And **`author=USER, derived_from=THIRD_PARTY` — the Workstream C landlord
shape — is not in the map at all.** The fix for one conflation would introduce
another.

**Proposed, pending research:** key on `(author, derived_from)`, checking the
capping axis first.

```python
if e.provenance.derived_from is THIRD_PARTY:  " [third-party-derived; unconfirmed]"
elif author is THIRD_PARTY:                   " [third-party-reported; unconfirmed]"
elif author is ASSISTANT:                     " [assistant-generated; unverified]"
else:                                         " [unverified origin]"   # fail closed
```

**Q5 is resolved** — `(author, derived_from)` (research, 2026-08-01) — **and
the mechanism SHIPPED 2026-08-15** as `graph._ORIGIN_LABELS` + `_origin_label`
(the v3 release-gate fix): author-keyed today, with USER/SYSTEM mapping to
"third-party-reported" because those classes reach `use_only` only via
`derived_from=THIRD_PARTY`, and an unlabelled class failing safe to
`unverified-origin` (tripwired by `tests/test_render_origin.py`). **The
author-only shortcut is valid exactly as long as every `use_only` route
implies third-party derivation — this spec ends that**, so implementation
must key the pair as Q5 ruled: `assistant + derived_from=THIRD_PARTY` labels
third-party-derived (the capping axis first), bare `assistant` labels
assistant-generated. The tripwire already fails the build if `ASSISTANT`
lands without a label; I12 makes the pair-keying itself the tested property.

**Interfaces:** `EvidenceAuthor` gains a member (additive for callers that pass
it; **not** additive for callers that exhaustively match on it). MCP `remember`
gains `"assistant"` in its fail-closed author map and tool description
(§2d.6; `system` stays excluded). **CLI changes additively**: BOTH hardcoded
lists — `cli.py:410` `--author` and `:414` `--derived-from` — must accept
`assistant`, with help text, a parsing test and docs. *(v2 said "No CLI
change" while §2 said the opposite — the external reviewer found the
contradiction in my own document; §2 was written later and I never reconciled
them.)* Export `FORMAT_VERSION` 8 → 9 *(was "2 → 3" when v3 was written;
five specs have bumped it since)*.

**Migration:** existing stores are untouched — no edge changes author, and no
backfill runs. Nothing is unrecoverable **going forward**; the irreversible step
is **downgrade**, see §7.

---

## 5. Regime analysis — where does this behave differently?

*Provenance: recall was query-blind on any store past `max_subgraph_edges` — no
fixture ever caught it because small stores never truncate.*

- **Scale / density.** Assistant turns are the *most numerous* event type in a
  chat deployment — plausibly the majority of all events, where third-party mail
  is a minority. So this class arrives at a volume the third-party path never
  reached, and it lands entirely in **`use_only`** *(v4 carrier sweep: this
  bullet still said "mostly mentionable")*. The regime that matters is a store
  where assistant edges dominate the **unverified block's** share of the
  rendered context and the subgraph budget (`max_subgraph_edges`, default 40),
  crowding user facts by sheer count — a PROMPT-SURFACE load pattern, not an
  assertion one, but the model still reads what the block carries.
  **This is a genuinely new load pattern for the ranker, and the pilot corpus
  will not show it** — LongMemEval items average ~1,700 facts with a balanced
  mix.
- **Thresholds interacted with:** `max_subgraph_edges` (40),
  `subgraph_coverage_share` (0.0), `wiki_recompile_after_writes`.
- **Do the tests reach it?** **Not today.** A fixture-scale store cannot show
  crowd-out. **Release class: stable, so this blocks** — §6 I6 adds a
  1,000-edge assistant-dominant recall test asserting user-authored facts still
  reach the subgraph. Declaring it untested in §8 is **not** available, because
  the change ships on by default.
- **Cold vs warm / first vs thousandth call.** No difference: routing is
  per-event and stateless. The wiki recompiles on the same counter as before,
  though its *input mix* shifts toward assistant material — covered by I6.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where it runs |
|---|---|---|
| **I1** assistant + **ANY** subject → `use_only` *(v4 carrier sweep: I1/I2 still encoded the withdrawn v2 subject rule; I1 is now the every-subject form)* | `test_assistant_is_use_only_for_every_subject` (parametrized over user/other/assistant subjects) | CI |
| ~~**I2**~~ *deleted in v4 — encoded the withdrawn v2 widening (assistant + non-user subject → `mentionable`). Not narrowed: DELETED, because under v3/v4 no subject yields `mentionable` and a struck-but-present rule is the 0002 defect class. I1's every-subject form is the replacement.* | — | — |
| **I11** the disclosure rule FAILS CLOSED on the new member: `_disclosure_for` must route `author==ASSISTANT` or `derived_from==ASSISTANT` before the `mentionable` fallthrough — **without this edit the enum addition alone fails OPEN** (today's final return is `MENTIONABLE`) | `test_assistant_never_yields_mentionable` (asserts over the full author × derived_from product) | CI |
| **I12** the origin label keys the `(author, derived_from)` PAIR: `assistant+THIRD_PARTY` labels third-party-derived, bare `assistant` labels assistant-generated, and no author class inherits another's label | `test_render_origin.py` extended (the shipped tripwire already fails an unlabelled class) | CI |
| **I13** *(v5, R3-2)* the on-disk guard is ACTIVATED: a reader predating `ASSISTANT` refuses a v11 store AT OPEN with exactly `StoreVersionError(reason="newer")` — never a `ValidationError` mid-read | `test_old_reader_refuses_v11_at_open` (asserts type AND reason, before any edge loads) | CI |
| **I13a** *(v7, R5-4)* `SCHEMA_V11 == SCHEMA_V10` — the bump is semantic, byte-identical schema (the 0019 `SCHEMA_V7 = SCHEMA_V6` precedent, asserted not cited) | `test_schema_v11_is_byte_identical_to_v10` (object-list equality) | CI |
| **I13b** *(v8, R6-1)* the v10→v11 migration is STAMP-ONLY across **EVERY accepted v10 manifestation** — the executable schema authority accepts FIVE (constructor · constructor→v10 ledger-inline · constructor→v10 ledger-alter · v6→v10 ledger-inline · v6→v10 ledger-alter), and a no-DDL stamp must preserve each: schema dump byte-identical before/after, `user_version` 11 | `test_v10_to_v11_migration_is_stamp_only` **parameterized over all five shapes** | CI |
| **I13c** *(v9, R7 correction)* v11 acceptance is **EXACT INHERITANCE**: `accepted_digests(11)` is precisely the accepted v10 manifestations re-digested at 11 — **five total; the five INCLUDE the constructor** (v8's 'plus the v11 constructor' double-counted it), each with v11 provenance, regenerated per the 0007/0013 convention | `test_i13c_v11_inherits_by_digest_not_count` (digest-level set equality, count derived — a count-only check would pass five unrelated records, R7-2) | CI |
| **I13d** *(v8, R6-2)* the 0018 orchestrator FOLLOWS the bump **including its stale attestation internals**: `migration_digest` currently derives from `ALTERS_V7_TO_V8` and the ladder diagnostics hard-code bases v5/v6 with migrate-to-v6/v7 instructions (at head 10, base 8 is diagnosed as resolving to v6 — measured by the reviewer). Updating `_HEAD`/`_MINT_BASE`/the window alone does NOT fix those carriers: the implementation moves to an **edge-indexed migration-step registry** (the v10→v11 digest derives from its actual EMPTY step set) and diagnostics GENERATE from the real release ladder | `test_release_migration_derives_from_the_bumped_head` + `test_ladder_diagnostics_generate_from_the_registry` (bases 1–10 exercised, all public authority fields asserted) | CI |
| **I3** an assistant edge can never supersede, absorb, or reinforce a user edge | `test_assistant_cannot_touch_user_edge` (all three ops, both directions) | CI |
| **I4** `derived_from=THIRD_PARTY` still caps an assistant edge to `use_only` | `test_assistant_derived_from_third_party_is_capped` | CI |
| **I5** affirmation-as-new-USER-evidence is the ONLY promotion path (0008 PRESERVED: `confirm_edge` refuses every non-assertable edge by contract), and maintenance never promotes | `test_affirmation_grounds_and_confirm_edge_refuses` — asserts all four: same-value affirmation makes the fact assertable via the user edge (prior persists un-asserted), **the RENDERED result puts each record in its own trust partition** — asserted at `gate.partition_parts` + the rendered lines (the surfaces recall actually consumes); `collapse_for_render` is retained ONLY as the upstream no-collapse assertion, since it neither partitions nor renders *(v8/R6-3: this cell named the wrong mechanism while §17 said the right one)*, a differing user value retires the prior via the ladder, and `confirm_edge` on the assistant edge raises with 0008's message *(v5, R3-1/R4-2)* | CI |
| **I3b** the path §3.2 says is **allowed** actually works: user evidence SUPERSEDES an assistant prior via the authority ladder *(v5, R3-3: absorption is NOT the allowed path — cross-class absorption stays blocked by the 0.4.1 guard, and v4's claim that it worked was measured false)* | `test_user_can_correct_an_assistant_fact` (supersession, both the retire and the refusal-free path) | CI |
| **I6** THE SELECTION RULE, **scoped to UNSCOPED recall** *(v5, R4-3: v5's first form said scope filters "run upstream and are unaffected" — FALSE against shipped 0020: `Memory._recall` runs `subgraph_for_query` (cap included) BEFORE `view.scoped`, its own comments record that out-of-scope records consume slots, and the reviewer measured a principal's edge lost to an out-of-scope winner at cap 1. Applying the reserve inside `subgraph_for_query` would preserve that failure, so this invariant does not pretend otherwise)*: on UNSCOPED recall, when any query-relevant ASSERTABLE edge exists, selection reserves `min(count_relevant_assertable, ceil(max_subgraph_edges / 4))` slots for the highest-ranked **query-RELEVANT** assertable edges — relevance carried from scoring, because a user-subject edge is ELIGIBLE at baseline score with zero overlap and eligibility is not relevance (v12, R10-1: the candidate reserved every assertable in the scored set, and the reviewer's executed counterexample put an unrelated `bananas` fact ahead of a relevant one); remaining slots fill by rank regardless of class. Protected class = ASSERTABLE. COMPOSITION *(corrected v7, R5-2: the post-`_cover` form was IMPOSSIBLE — `_cover` truncates to `max_edges` before any downstream reserve could act, and with the shipped `MemoryConfig.subgraph_coverage_share=0.0` the reviewer measured `assertable_selected 0`; a reserve cannot recover a record already discarded)*: **the reserve is applied to the FULL scored, post-collapse candidate set BEFORE final truncation** — the reserved assertable records are placed first, the remaining slots fill by rank, and only then does the `max_edges` cut happen; `subgraph_coverage_share` constrains WITHIN the non-reserved remainder, **with the composition defined (v8/R6-4)**: reserved records DO seed covered-day state (they are selected records like any others — coverage sees the union), the coverage budget is computed over the remaining slots after the reserve is placed, deduplication runs over the union, and underfilled coverage backfills by rank deterministically. Vectors required beyond `coverage_share=0.0`: positive coverage with reserved-day overlap, distinct reserved days, dedup across reserve/coverage, underfill + backfill, the no-relevant-assertable vector (v12, R10-1: four relevant unverified facts + one unrelated assertable — the reserve engages for NO record and the output is exactly the four relevant facts by rank), **and reserved-record placement under a NON-functional relation with the reserved record globally LAST-ranked (v11, R9-1: a filter over the globally scored list preserved global rank and every prior order vector used functional `works_as`, where the authority permutation masked it — the output is CONSTRUCTED as `reserved + remainder`, each segment in scored order, and EVERY vector asserts the COMPLETE ordered output; survivor membership is not an order assertion).** The fixture pins `coverage_share=0.0` explicitly (the shipped config default — the function default of 0.25 masked the failure in the earlier harness). **The SCOPED path's limitation is STATED, not fixed here** (§8): scope filtering after selection can starve a principal's edges regardless of any reserve — fixing it means moving scope ahead of ranking, which is a 0020 amendment (§10 Q6, its own round). FIXTURE, exact (unscoped): 1,000 equally-relevant `use_only` assistant edges + 1 equally-relevant older assertable user edge, `max_subgraph_edges=40` → the user edge IS selected and the other 39 slots are the top-ranked assistant edges | `test_assistant_dominant_store_does_not_crowd_out_user` (the exact fixture, unscoped; asserts the user edge id in the selection) | CI |
| **I10** the store-side min-trust consolidation rule (`_derive_output_metadata`, its home since 0010 X23 — see §2) treats `ASSISTANT` correctly: any assistant member caps the derived output at `use_only`; a mixed set never yields output presented as grounded | `test_mixed_batch_with_assistant_declares_influence` | CI |
| **I10a** an assistant restatement PERSISTS UNTOUCHED per 0012 — the prior is byte-unchanged (no `observed_at` refresh is structurally possible), both records present, render collapses strict redundancy *(v5, R3-3: v4 promised a store-side merge 0012 does not perform)* | `test_assistant_restatement_does_not_refresh_currency` (prior byte-equality + persist + render collapse) | CI |
| **I7** an export containing assistant edges is rejected by an older reader **with our message, not a pydantic traceback** | `test_downgrade_export_fails_cleanly` | CI |
| **I8** injection ladder unchanged; assistant authorship grants no new write authority | existing `bench --compare`, `engine.injection_asserts == 0` | bench gate |
| **I9** trust canaries unchanged | existing `engine.trust_canary_failures == 0` | bench gate |

Standing checks that must not regress: injection asserts 0 · cross-user leaks 0
· trust canaries 0 · supersession probes pass · malformed edges 0 · declared
read-cost and latency ceilings.

**I3b exists because I only tested prohibitions.** Research's point: I3 proves
an assistant edge cannot touch a user edge, and nothing tested the *allowed*
direction. A guard written slightly too broadly would block **user corrections**,
every prohibition test would still pass, and the symptom would be a user
correction that silently does not take — which is worse than the bug the guard
prevents and would look like the guard working.

**Reproducer retention:** `184da446` is retained as a fixture asserting the
case stays **unanswered** — it is the documented cost of this design (§8), and a
future change that "fixes" it silently would be reverting a decision rather than
improving recall.

---

## 7. Failure modes and reversibility

- **Silent failure mode.** A host that labels *every* assistant turn
  `author="assistant"` including turns that merely quote the user gets those
  facts capped at `use_only`, and the symptom is **abstention where the user
  expects an answer** — visible, but easily misread as "memory did not store
  it". First symptom is a wrong abstention on a fact the user did state, delay
  of one question. Mitigation is documentation, not code: the host should attribute
  a quoted user statement to the user.
- **Reversibility.** Forward-reversible: no existing edge changes, so reverting
  the library restores prior behaviour for **new** writes. **Backward: NOT
  reversible.** Verified — an older library loading an `assistant` edge raises
  `pydantic.ValidationError: Input should be 'user', 'third_party' or 'system'`.
  A store or export containing assistant edges **cannot be read by ANY
  veracium predating `ASSISTANT`** *(v5, R3-2: "pre-0.5.0" was wrong — the
  boundary is this spec's own release, not an old one)*. For EXPORTS,
  `FORMAT_VERSION` 8 → 9 makes `portability.load` fail with our own
  "export version is newer than this library" message instead of a stack
  trace. **For the STORE, the 0007 guard exists but only fires when a newer
  store is actually STAMPED — so this spec BUMPS `SCHEMA_VERSION` 10 → 11
  as a semantic, no-DDL version step** (the exact precedent is 0019's
  `SCHEMA_V7 = SCHEMA_V6` — byte-identical schema, semantic bump; v5's
  first citation of 0006 v4→v5 was wrong, that migration ADDS the
  `store_identity` table — R4-4), with `SCHEMA_V11 = SCHEMA_V10`
  declared, the v10→v11 migration a stamp-only step in
  `store/migration.py`, and the accepted-digest evidence regenerated per
  the 0007/0013 convention (`Spec-Requires` carries 0013 — R4-4). **The
  release orchestrator is a DISPOSITIONED CONSUMER** (R4-4): 0018's
  `release_migration.py` derives `_HEAD = SCHEMA_VERSION`, `_MINT_BASE =
  _HEAD - 1` and the supported-base window from the constant, so the bump
  moves all three — the 0018 mint/preflight evidence regenerates with the
  release, and `Spec-Requires` carries 0018. An old reader then refuses AT
  OPEN with **exactly `StoreVersionError(reason="newer")`** (the shipped
  refusal, `store/schema_version.py`) — never a `ValidationError`
  mid-read; **I13** asserts the exact type and reason. NEW-reader
  postconditions: `migrate_store` takes a v10 store to v11 with byte-
  identical SQL shape, the stamp the only change, and the v11 accepted-
  manifest digest recorded in the store evidence. *(v5, R3-2: v4 said "nothing 0001-specific
  remains" of Q3 — false as measured by the reviewer: disk=10, reader=10,
  `ValidationError`. 0007 only refuses what a version bump tells it to.)*
- **Partial failure.** No new multi-step operation; nothing to leave half-done.
  Permanent errors are not retried into a silent empty success (unchanged).
- **New attack surface?** **No new assertion channel — that is v3/v4's whole
  point** *(v4 carrier sweep: this cell still described the withdrawn v2
  admission into `mentionable`)*. Every assistant edge is `use_only`; prompt
  injection that induces an assistant statement gets an edge the gate never
  asserts, whatever its subject (promotion exists only as user AFFIRMATION —
  new user evidence; v5/R4-1). **The surface that DOES grow is the fenced
  residual** (the 0023 §8 lesson, stated here so the reviewer meets it
  pre-stated): `use_only` assistant text still enters model context in the
  unverified block, attributed but present, at assistant-turn VOLUME — and
  injection does not require assertion. The bound is §5's budget analysis
  plus I6, not a fence around the prompt. AFFIRMATION remains the single
  promotion path — a user act on rendered-with-attribution text that
  creates new USER evidence; nothing promotes in place (R5-1 sweep).

  **v1 claimed this was "bounded by the fact that such a claim was already
  reaching the user directly in the same turn". That bound is deleted — it does
  not hold**, and research named the reason I had only suspected: **the turn is
  ephemeral; the store is persistent and re-injected.** The user reads the claim
  once, in a live context where it might look odd and be challenged. Memory
  asserts it into future contexts indefinitely, each one further from the turn
  that would have made it suspicious. Persistence is not a weaker version of
  utterance — it is a different exposure, and it is the one we build. The
  widening is stated as a limit in §8 rather than argued away here.

---

## 8. Claims and limits

- **What we will say**, exactly: *"veracium models assistant-generated content
  as its own evidence class. Every assistant statement — about the user or
  anything else — is held as unverified context, honestly attributed; a user
  affirmation creates user evidence that supersedes it. Configuration may
  narrow what is assertable, never widen it."* *(v5, R3-6: the previous
  sentence promised direct use of first-party assistant reports — the
  withdrawn v2 widening, surviving in the one carrier that faces the
  public.)*
- **What this does NOT establish.**
  - It does **not** improve our LongMemEval score, and is **expected not to**:
    `184da446` and its class stay unanswered by design. Any post-change score
    movement is unattributed unless a frozen protocol says otherwise.
  - It does **not** make assistant content trustworthy, and it does **not**
    make it groundable *(v4 carrier sweep: this bullet still described the
    withdrawn mentionable route)*: a first-party assistant report ("the
    deploy succeeded") stays unverified until the evidence-basis axis exists
    to ground it on the TOOL's authority rather than the assistant's word.
    What it buys is honest labelling — hosts stop calling assistant content
    `SYSTEM`.
  - The 7/8-vs-8/8 abstention figure is **one question on an 8-item abstention
    subset from a single 44-item pilot run** (`20260730T174434`). It motivated
    the direction; it does not measure this change and cannot.
  - A passing injection ladder is *"no failures observed on the frozen suite"*,
    never "safe against prompt injection".
  - **The I6 reserve does not protect SCOPED recall** (v5, R4-3): shipped
    0020 filters scope AFTER subgraph selection, so out-of-scope records can
    consume selection slots ahead of a principal's own evidence — measured
    at cap 1. Fixing that ordering is a 0020 amendment (§10 Q6), not this
    spec's rider.
  - **It does not bound the fenced residual** *(v4 carrier sweep: this bullet
    still described the withdrawn mentionable exposure and its subject-rule
    containment — both gone)*: `use_only` assistant text enters the prompt's
    unverified block at assistant-turn volume, attributed but present, and
    injection does not require assertion (0023 §8). The historical argument
    stands and generalises — the turn is ephemeral, the store is persistent
    and re-injected into contexts increasingly distant from the one that
    would have made a false statement look suspicious. The containment is
    the never-asserted gate plus the budget analysis, not a fence.
- **Measurements cited:** LongMemEval V1-S pilot, run `20260730T174434`, arm C,
  commit `ce66282`; Arm T comparison from the same pilot. Neither run is
  decision-eligible under the current policy (no freeze artifact) — cited as
  motivation, not as evidence for acceptance.

---

## 9. Brief for the external reviewer

*(Rewritten for v4 — the v3 brief asked you to scrutinise three questions
that no longer exist: subject routing was withdrawn with v2, Q1 resolved
ASSISTANT×ASSISTANT, and the `mentionable` question is moot when nothing
routes there. The old brief is in the git history; asking you to audit
dissolved questions would waste the round.)*

- **What we are least sure of** *(refreshed each round; last: v7/round 5)*.
  (1) **The assistant authority rung (§2d.1).** 0003 pre-provisioned
  `assistant` at rung 1 — above `third_party`, below `system` — and v4
  ratifies it. The argument: an in-conversation identified source outranks
  hearsay. The counter-argument we could not kill: a prompt-injected
  assistant is an ATTACKER-INFLUENCED source, and rung 1 lets its edge
  supersede a third-party-authored prior. Is "above third_party" right for
  a class whose statements an attacker can shape in-band?
  (2) **The origin label as model-visible text (§4b).** "assistant-generated"
  in the unverified block tells the model these are its own prior claims.
  Does naming the class invite self-conditioning — the model treating its
  own past output as quotable precedent — in a way an unattributed fence
  would not? (The alternative, suppressing attribution, failed review in
  0022/0023: unlabelled fenced text is worse.)
  (3) **The fenced residual at assistant-turn volume (§5, §7, §8).**
  `use_only` assistant text enters the prompt's unverified block at the
  highest event volume in the system. Injection does not require assertion.
  The bound is a budget analysis (I6), not a fence — is that enough?
- **Where we suspect we have overstated.** §2d.1's claim that ratifying the
  pre-provisioned rung needs **no `RULE_VERSION` bump** because no existing
  pair can flip. The argument is enumerative (old members' rungs untouched;
  ASSISTANT pairs previously unconstructible) — please attack it; a missed
  flip path re-opens 0011's historical-refusal re-evaluation concern.
- **What would change our minds.** Evidence that hosts cannot reliably
  attribute turns (making the whole class noise); a construction where a
  `use_only` assistant edge reaches assertion without a user affirmation —
  through
  the wiki compiler, consolidation's min-trust derivation, an import
  round-trip, or any path §2d missed; or a demonstration that rung 1
  composes badly with 0024's pending author/relation reordering.
- **Standing from the v3 round.** Your one blocking amendment is closed in
  shipped code (§12 annotation; §2c-ii carries the evidence commands). The
  I10a self-corroboration design (dedup yes, currency refresh never) stands
  unchanged from v3 — if you have watched self-corroboration fail in
  another system, that remains the part most likely to be naive.
- **Reviewer-safe copy:** not required — no competitive-audit detail or
  unpublished findings here.

---

## 10. Open questions

| # | question | class | who decides | by when |
|---|---|---|---|---|
| ~~**Q5**~~ | **RULED 0001-Q5 (research, 2026-08-01 20:06): `(author, derived_from)`.** Author-only mislabels `system+third_party` and omits `user+third_party` — the two commonest `use_only` shapes after plain third-party. **Stale here for 16 hours** while the answer sat in COORDINATION; see the reconciliation check. | resolved | research | — |
| ~~**Q1**~~ | ~~Should `ASSISTANT × ASSISTANT` merges be blocked?~~ **ANSWERED 2026-07-31 (research):** do not block the merge; block the `observed_at` refresh. The hazard is currency, not confidence. See §3.2 and I10a. | ~~blocking~~ **resolved** | research | done |
| **Q2** | Does an assistant *restating* user testimony reinforce the user's edge instead of creating an assistant edge? The elegant fix; blocked by the same-disclosure-class rule; would remove most of §8's stated cost. | `deferred` | research | own design round |
| **Q6** | *(v5, R4-3)* Should 0020's recall ordering move scope filtering AHEAD of subgraph ranking/reservation, so scoped principals get the I6 guarantee? Requires a 0020 amendment with its own review (the filter-after-selection ordering is 0020's shipped contract, and its comments record the slot-consumption behaviour as known). | `deferred` | dev + research | own design round, post-acceptance |
| ~~**Q3**~~ | **RESOLVED by `0007` (accepted; shipped in v0.5.0): the guard MECHANISM is 0007's contract** — but *(corrected v5, R4-4: the earlier strike said "nothing 0001-specific remains", which I13 contradicts)* the guard only fires when a newer store is STAMPED, so the 0001-specific remainder is exactly the `SCHEMA_VERSION` 10→11 bump §7 specifies. The strike stands for the mechanism; the activation is this spec's. | resolved | dev | — |
| ~~**Q4**~~ | **MOOT (v5, R3-5): `0016` deleted `SourceType`, `Provenance.source_type` and `ingest._source_type` outright — the field this question asks about does not exist.** The v4 currency pass re-executed §2c-ii's commands but never verified every NAME in the consumer table still resolves; the reviewer did. | resolved | — | — |

---

## 11. Changes in v2 (after research's internal review)

1. **§3.1 failed open — fixed.** v1 routed *any* non-`user` subject to
   `mentionable`, so a mangled or invented subject from an extractor we do not
   control became assertable. Now only a **recognised** distinct entity is
   mentionable; empty, pronoun, placeholder and unresolvable subjects fail
   closed to `use_only`.
2. **Q1 answered and the reasoning replaced.** `ASSISTANT × ASSISTANT` merges
   are allowed; the **currency refresh** is blocked. My compounding-confidence
   hazard was wrong — `confidence = max` synthesises nothing. The real exposure
   is `observed_at`, i.e. freshness-pinning by self-repetition. New **I10a**.
3. **I3b added.** §6 tested only prohibitions. Nothing checked that the paths
   §3.2 calls *allowed* actually work, so a too-broad guard would silently block
   user corrections with every prohibition test still green.
4. **I10 added** for the new class against the consolidation defect this spec
   discovered (fixed separately in 0.4.4, GHSA-hcj3-8jqc-wqrp).
5. **§7's injection bound deleted**, moved to §8 as an unbounded limit. The turn
   is ephemeral; the store is persistent and re-injected. Persistence is a
   different exposure, not a weaker utterance.
6. **§9 brief extended** to ask the external reviewer specifically about
   self-corroboration.
7. **Status → accepted-with-amendments (internal).** Per `PROCESS.md` this does
   **not** authorise implementation: external review is outstanding and the
   amended version needs approval.

---

## 12. External review outcome — DEFERRED (2026-07-31)

**Accepted in full. The reviewer confirms `EvidenceAuthor.ASSISTANT` is needed
and that this spec does not establish that assistant claims about non-user
subjects belong in the ordinary grounded channel.** Full response:
`proposals/spec-0001-external-review-response.md`.

**The two findings I verified, both worse than stated:**

1. **The subject rule cannot work, and not because the alias list is short.**
   *"Quentin prefers dark mode"* bypasses it — and **veracium has no
   display-name concept at all** (`user_id` is opaque; no `display_name`
   anywhere in `src/`), so the library cannot know the store owner's name. **No
   denylist is writable.** Measured over 131,574 triples from the LongMemEval
   extraction cache: **19,096 distinct subjects, only 39.4% the literal
   `"user"`**. v2 would route **60.6% of triples** to `mentionable`, through a
   long tail of bare personal names (`mother`, `lizzie`, `rachel`). Positive
   resolution to a canonical entity id is the only sound mechanism and **we have
   not built entity resolution.**
2. **Subject identity does not establish evidence authority.** *"The deploy
   failed"* has a non-user subject and nothing shows the assistant deployed
   anything. I called it *"first-party testimony about its own action"* — that
   phrase assumes the action. I generalised from research's example rather than
   its principle. The corpus agrees: `assistant` is the **second most common
   subject** (5,436), so "the assistant did X" is frequent and would have gone
   mentionable on the strength of not being the string `user`.

**Structural correction adopted:** v2 bundled *introducing accurate provenance*
with *widening assertability*. Only the first is justified today. **v3 ships
`ASSISTANT` at `use_only` for every subject, with attribution preserved in
rendering** — which delivers the actual purpose (hosts stop mislabelling
assistant content as `SYSTEM`) without opening a new persistent assertion
channel. **Cost recorded before the fact: this is more conservative than current
Arm C, so it moves our benchmark score down or nowhere, never up.**

**Also accepted:** direct fail-closed tests — the reviewer numbered these in their own scheme, which this spec never adopted, so they are described rather than cited; proactive eligibility assessed
separately from answer-context eligibility; the CLI contradiction (fixed in §4);
Q4 promoted to **blocking**; the `PRAGMA user_version` guard promoted to a
**hard release gate** *(since discharged by `0007` in v0.5.0 — see the struck
Q3 row)*; I10a widened to freeze *every* ranking-relevant field;
consolidation provenance to be specified in full, including whether one trusted
input may lift weaker ones; and I6 to carry a frozen acceptance rule.

**Reopened with research:** the fourth `Disclosure` tier. Research rejected it
("the tier was never the problem, the author was"), but the rendering analysis
shows a real expressive gap — we cannot say *"this may be discussed, but only as
something the assistant previously claimed."* Sequencing dissolves it: v3 does
not need the tier.

**~~🔴~~ ✅ v3 RELEASE GATE — CLOSED IN SHIPPED CODE 2026-08-15** *(the
paragraph below is the finding as recorded at review time; the fix is
`graph._ORIGIN_LABELS` + `_origin_label` — author-keyed labels, fail-safe
`unverified-origin` for an unlabelled class, `tests/test_render_origin.py`
as the tripwire, 6 passed on this candidate's tree. The wider
`gate.partition_parts` concern is addressed by §4b's pair-keyed labelling:
the unverified block's members carry their origin inline, so three kinds of
thing in one block are three LABELLED kinds. Found by research in the render
path and confirmed here.)*
`graph.py:305` is `tp = " [third-party-reported; unconfirmed]" if e.use_only` —
the marker keys on **`use_only`**, not on `author_of_evidence`, and its text is
**hardcoded**. Verified by construction: a `SYSTEM`-authored `use_only` edge
renders as

```
deployment uses_tool: failed (since 2026-07-31) [third-party-reported; unconfirmed]
```

Correct today, because only third-party-*derived* content reaches `use_only`.
**Under v3 it is affirmatively false** — every assistant edge would tell the
model a specific wrong origin. v3 exists so hosts stop mislabelling assistant
content as `SYSTEM`; as scoped it would swap one mislabel for a worse one,
because a wrong-but-confident provenance label is worse than a missing one.
**Blocks v3.** The gap is wider than one line: `gate.partition_parts:84` already
merges quarantined third-party *claims* with third-party `use_only` *inferences*
undifferentiated, and v3 would make that three kinds of thing in one block.

**Routed to workflow-platform:** what counts as "the assistant" in a multi-agent
deployment. Without an `author_id`, two unrelated agents mutually reinforce as
one source class, which interacts directly with §3.2's self-reinforcement rule.

---

## Reviewer checklist

- [ ] §3 has no unanswered cells
- [ ] §2 consumers were enumerated mechanically, not recalled
- [ ] Every §6 invariant has a check that actually runs
- [ ] §5 regimes are reachable by tests, or the change is experimental,
      off by default, and §8 says so
- [ ] §3b: no principal can see anything they could not see before
- [ ] §6 and §8 are filled in — `n/a — <reason>` counts, blank does not
- [ ] §10 questions each carry a class; unclassified means blocking
- [ ] §8 states what this does *not* establish
- [ ] I have said where I think the **author's conclusion is wrong**
- [ ] I re-read the current version before reviewing, and I am quoting the
      version I approve
- [ ] §9 brief is written, and external review has been sent

---

## 13. Changes in v3 (after external review deferred v2)

1. **The assertability widening is withdrawn, not re-argued.** v3 routes
   `ASSISTANT` to `use_only` for **every** subject. §3.1's subject rule is gone:
   v1 failed open, v2's "recognised subject" fix rested on a predicate the
   codebase cannot evaluate, and measurement settled it — **19,096 distinct
   subjects across 131,574 extracted triples, only 39.4% the literal `"user"`,
   and no entity resolution exists.** No subject-based rule is buildable.
2. **Speaker ≠ witness, conceded.** *"The deploy failed"* has a non-user subject
   and nothing establishes the assistant deployed anything. That capability
   moves to the **evidence-basis axis**, which is its right home — a deployment
   result should be groundable because an authenticated tool returned it.
3. **§4b added (rendering).** Research's four design decisions adopted
   unchanged; **one correction** — key on `(author, derived_from)`, because
   author alone mislabels `system+third_party` as system-derived and omits
   `user+third_party` entirely. **RULED 0001-Q5: `(author, derived_from)`.**
4. **§2c-ii added.** Every reachability claim now carries its command.
5. ~~**Q3 (store-version guard) remains a hard release gate.**~~ *(Discharged:
   the guard shipped as `0007` in v0.5.0 — see the struck Q3 row.)*
6. **Recorded before the fact:** v3 is **more conservative than current Arm C**,
   so it moves our LongMemEval score **down or nowhere, never up.**

---

## 14. Changes in v4 (the re-entry candidate, 2026-08-22)

*No design change from v3. Everything here is closure-recording, currency,
and the carrier sweep v3 owed itself.*

1. **The v3 release gate is recorded CLOSED** (shipped 2026-08-15:
   `graph._ORIGIN_LABELS`, fail-safe `unverified-origin`, the
   `test_render_origin.py` tripwire — evidence in §2c-ii). §12's gate
   paragraph annotated in place; the deferral note rewritten.
2. **The v2-form carriers §13 missed are rewritten in place** — the same
   defect class that deferred 0002 five times (the correction lived in the
   changelog while the normative text kept the old rule): §4's
   observable-difference table and rendering paragraph (assistant + non-user
   subject no longer renders grounded), §3b's visibility bullet (no
   widening remains — `use_only` is never volunteered), §6's I1/I2 (the
   `mentionable` invariant is DELETED, replaced by the every-subject form).
3. **Currency pass, every mechanical claim re-executed** (§2, §2c-ii):
   consumers 8 → 18 src modules / 16 → 61 test files; `cli.py:299` → `:410`
   plus the new second hardcoded list at `:414` (`--derived-from`);
   `mcp_server` map moved to `:38`, now fail-closed with `system` removed;
   `FORMAT_VERSION` 2 → 8 (this spec's bump becomes 8 → 9); the
   `lifecycle:101` trust-laundering defect DISCHARGED to the store's fenced
   write boundary by 0010 X23 (I10 restated against its real home).
4. **§2d added — the five eras that shipped consumers after v3**, each
   answered: the 0003 ladder's pre-provisioned `assistant` rung RATIFIED at
   1 with the no-`RULE_VERSION`-bump argument; the 0005 import cap's
   author-flattening ratified as conservative; 0022 orthogonal; the 0024
   `_disclosure_for` co-edit sequenced (additive, commutes, 0024 first);
   0025 orthogonal; the MCP map ruling (`assistant` joins — self-demotion,
   not self-elevation; `system` stays out).
5. **Two invariants added**: **I11** (fail-closed disclosure — without the
   `_disclosure_for` edit the enum addition alone fails OPEN to
   `mentionable`; the full product is asserted) and **I12** (pair-keyed
   origin labels — the author-only shortcut dies with this spec, per Q5's
   ruling).
6. **Status: `deferred` → `draft`** on Quentin's word (2026-08-22) —
   re-entering external review as the v4 candidate.

---

## 15. Changes in v5 (the round-3 fold, 2026-08-23)

*Every item is a reviewer-executed collision with a shipped contract; none
is a design reversal. The recommended option was taken wherever the verdict
offered one.*

1. **R3-1 — affirmation replaces promotion-via-`confirm()`.** 0008 is
   PRESERVED unamended: `confirm_edge` refuses every non-assertable edge by
   contract (the reviewer executed the refusal). A user affirmation is NEW
   USER EVIDENCE — ingested via `remember(author=USER)`, superseding the
   assistant prior through the 0003 ladder with full audit/retry
   semantics. §3.2's row, I5, §3b, §7 and §8's public claim all rewritten;
   `Spec-Requires` gains 0008.
2. **R3-2 — the on-disk guard is ACTIVATED.** `SCHEMA_VERSION` 10 → 11,
   semantic no-DDL stamp (the 0006 v4→v5 precedent), migration
   stamp-only step + regenerated accepted-digest evidence; a pre-ASSISTANT
   reader refuses a v11 store AT OPEN (I13). §7's "pre-0.5.0" boundary
   corrected to "any reader predating ASSISTANT"; the residual
   `FORMAT_VERSION → 3` sentence corrected to → 9.
3. **R3-3 — the operation matrix rewritten against shipped mechanisms.**
   Cross-class functional supersession is governed by the AUTHORITY LADDER
   (0003), not the 0.4.1 disclosure guard; cross-class absorption stays
   BLOCKED in both directions (v4's user-absorbs-assistant cell was
   measured false, and allowing it would launder assistant metadata into
   the user survivor); the assistant restatement PERSISTS UNTOUCHED per
   0012 (no store-side merge exists), which delivers Q1's currency intent
   structurally — I3b and I10a restated accordingly.
4. **R3-4 — I6 is a RULE, not a test name.** Reserve
   `min(count_relevant_assertable, ceil(max_subgraph_edges/4))` slots for
   the highest-ranked assertable edges; protected class = ASSERTABLE (no
   second author branch); exact 1,000+1 fixture with the expected
   selection stated.
5. **R3-5 — the deleted-field citation removed.** `ingest._source_type`
   and `SourceType` were deleted by 0016; the consumer row is corrected
   and Q4 is struck as moot. The v4 currency pass re-ran commands but
   never verified every cited NAME still resolves — recorded as the
   pass's own defect class.
6. **R3-6 — three more v2 carriers swept**: §2's `Edge.subject`
   blast-radius cell, §3b's fourth bullet, §8's public-claim sentence
   ("may be used directly"). §14's completed-sweep claim corrected by
   this section's existence.
7. **R3-7 — `Spec-Requires: 0003, 0005, 0007, 0008, 0012, 0013, 0016, 0018, 0024`**
   (0024 is an explicit ordering dependency on the `_disclosure_for`
   co-edit; the rest are contracts this design now composes with by
   name).
8. **The reviewer's standing asks:** the runnable candidate-behavior
   harness ships at `specs/evidence/0001/candidate_harness.py`
   (confirmation refusal, the matrix cells, old-reader refusal, the
   1,000-edge selection vector — measured TODAY-state, with the candidate
   deltas stated beside each); the no-`ensurepip` offline bootstrap is in
   the launcher.

---

## 16. Changes in v6 (the round-4 fold, 2026-08-23)

1. **R4-1 — the confirm() sweep COMPLETED** across the five carriers v5
   missed (§3.1, §3.2's four-questions, §4 twice, §7, §9), with the
   three-way terminology fixed everywhere: *affirmation* (new USER evidence
   via `remember`) · *confirmation* (0008's staleness-clearing on an
   already-assertable edge) · a non-assertable assistant edge is NEVER
   promoted in place. The v5 sweep was itself partial — the third partial
   sweep this spec has recorded, which is the strongest argument the
   reviewer's execute-everything method has made yet.
2. **R4-2 — render honesty**: same-value affirmation does NOT collapse
   (`collapse_for_render` groups per trust envelope; measured
   `surfaced_count=2`); the spec now states the two records render in
   SEPARATE partitions, 0012's isolation preserved deliberately; I5 asserts
   the actual rendered result; the harness measures it.
3. **R4-3 — I6 scoped to UNSCOPED recall** against shipped 0020 (scope
   filters run AFTER selection; the reviewer measured a principal's edge
   starved at cap 1); the scoped limitation stated in §8; the ordering fix
   named as a 0020 amendment (§10 Q6, deferred to its own round);
   composition with `_cover`/`subgraph_coverage_share` specified.
4. **R4-4 — the migration contract completed**: the precedent corrected to
   0019's `SCHEMA_V7 = SCHEMA_V6` (0006 v4→v5 adds a table); `SCHEMA_V11 =
   SCHEMA_V10` declared; the 0018 release orchestrator dispositioned as a
   consumer (`_HEAD`/`_MINT_BASE`/base-window all derive from the
   constant); the refusal exact (`StoreVersionError(reason="newer")`, I13
   and the harness assert type and reason); new-reader postconditions
   stated; `Spec-Requires` gains 0013 and 0018; the struck Q3 carrier's
   "nothing 0001-specific remains" corrected.

---

## 17. Changes in v7 (the round-5 fold, 2026-08-23)

1. **R5-1 — the terminology sweep, finally executed dead**: the three
   surviving `confirm()` carriers (§3.2's authority question, §3b's
   "confirm()-class", §7's "single promotion path") replaced — and the
   fold process itself corrected: every scripted replacement now REFUSES
   on a needle miss and the swept phrases are grep-verified zero before
   commit (two prior sweeps silently no-opped on wrapped text).
2. **R5-2 — I6's ordering made possible**: the reserve applies to the FULL
   scored post-collapse candidate set BEFORE final truncation (the
   post-`_cover` form was impossible — a truncated record cannot be
   recovered downstream); the fixture pins `coverage_share=0.0`, the
   shipped config default the earlier harness masked with the function
   default.
3. **R5-3 — I5 and the harness drive the REAL surface**:
   `gate.partition_parts` + the rendered lines — the user record only in
   grounded output, the assistant-class record only in the unverified
   block with its origin marker, no cross-partition leakage.
   `collapse_for_render` alone neither partitions nor renders.
4. **R5-4 — the migration contract is executable**: I13a–I13d name the
   tests for `SCHEMA_V11 == SCHEMA_V10`, the stamp-only migration
   (schema-dump byte equality), the v11 accepted-manifest evidence, and
   the 0018 orchestrator's derived constants + regenerated evidence.
5. **R5-5 — the version carriers swept**: the Status row, §9's brief
   label, and the harness's self-identification now state the current
   version; version carriers join the pre-send sweep list.

---

## 18. Changes in v8 (the round-6 fold, 2026-08-23)

1. **R6-1 — the five-manifestation matrix**: I13b/I13c parameterize over
   EVERY accepted v10 shape (the executable authority accepts five;
   "both routes" undercounted); v11 acceptance is exact inheritance with
   the count DERIVED from `accepted_digests(10)`, never typed.
2. **R6-2 — the 0018 attestation internals dispositioned**: the
   orchestrator's `migration_digest` derives from `ALTERS_V7_TO_V8` and
   its ladder diagnostics hard-code v5/v6-era bases (base 8 diagnosed as
   v6 at head 10, measured); I13d now requires the edge-indexed
   migration-step registry, the empty-step-set digest for v10→v11, and
   GENERATED diagnostics, exercised over bases 1–10.
3. **R6-3 — I5 names the real mechanism**: `gate.partition_parts` + the
   rendered lines; `collapse_for_render` retained only as the upstream
   no-collapse assertion.
4. **R6-4 — the reserve/coverage composition defined**: reserved records
   seed covered-day state, the coverage budget computes over the
   post-reserve remainder, dedup over the union, deterministic backfill
   on underfill; the vector set beyond `coverage_share=0.0` is named and
   the harness gains the positive-coverage measurement.
5. **R6-5 — the `confirm()` cross-reference**: the supersession row
   pointed at a renamed row; fixed, and the sweep lesson sharpened — a
   zero-survivor grep over RULE phrases does not cover row-NAME
   pointers; cross-references join the sweep list.
6. **The candidate-patched branch, DELIVERED** (the reviewer's
   thrice-asked artifact, authorized by the project owner):
   `specs/evidence/0001/candidate.patch` — inert data on the main
   line, applied with `patch -p1` in an extracted tree. The named trio
   runs REAL: 13 candidate tests green (I1, I5 at `gate.partition_parts`
   with the assistant marker, I6 at BOTH coverage shares, I11's full
   product, I12 pair keying, I13a-c with the five-manifestation
   inheritance — the 0007 machinery itself demanded the runtime
   re-record, which is that guard working — and the exact
   StoreVersionError reason="newer" refusal). The full branch suite
   measures the blast radius honestly: 11 failures, EVERY one a
   §2/§2d-enumerated carrier (the FORMAT-9 pin family, the MCP message
   pins, the 0018 head, the generated authority tables, the 0013 oracle
   domain, the audit manifest) — the implementation obligations
   acceptance authorises, now measured rather than asserted, and
   deliberately NOT fixed on an evidence branch.

---

## 19. Changes in v9 (the round-7 fold, 2026-08-23)

*Round 7 found no new trust-model architectural defect — every finding was
executable-evidence quality, mostly in the candidate patch the round
itself asked for, which the reviewer credits with exposing them.*

1. **R7-1 — the patch implemented the wrong I12 label**: the derived case
   returned "third-party-reported" where §4b spells "third-party-derived",
   and USER/SYSTEM inherited a label. The patch now implements the §4b
   decision order VERBATIM (derived→derived-label first, then bare-3P,
   then bare-assistant, else the fail-safe) and tests the complete
   author × derived-from matrix.
2. **R7-2 — the five-manifestation matrix, exact**: the patch's tests now
   construct each accepted v10 shape FROM the authority's own object
   records (never route proxies), compare v10-vs-v11 dumps (not
   v11-vs-v11), assert I13c at DIGEST level with derived counts, and test
   a head-10 reader (runtime-qualified, version-boundary isolated) against
   a v11 store containing real assistant data.
3. **R7-3 — `test_downgrade_export_fails_cleanly` exists and is real**:
   an assistant record round-trips at FORMAT 9 (the default import
   applying the ratified 0005 cap, restore=True faithful — both asserted),
   and a head-8 importer refuses with our message.
4. **R7-4 — the four I6 composition branches are executed**: reserved-day
   overlap, distinct reserved days, dedup-before-reserve, and
   underfill-with-deterministic-rank-backfill, each with exact-ID (and for
   backfill, exact-order twice-run) assertions. All four passed against
   the reserve implementation unchanged — the composition semantics match
   R6-4's definition as written.
5. **I13c's count corrected**: five total, the constructor included (v8
   double-counted it).
6. **§1 gains the field-demand paragraph** (Research's competitive-scan
   input, attributed as reported-by-scan — the verbatim quote was not
   re-verifiable at fold time and is therefore paraphrased, per the
   verify-before-citing rule).
7. **Package machinery this round (C7-1/C7-2, recorded in the design
   note §15)**: the deleted dispatched sidecars RESTORED from git history
   (my own reseal workflow had destroyed the witnesses the history field
   pointed at), the generated LINEAGE table with exact
   PACKAGES↔INDEX↔sidecar correspondence enforced at render and seal,
   discarded seals disclosed by name, and ONE strict predecessor selector
   whose verified Path is the diff's only input.

---

## 20. Changes in v10 (the round-8 fold, 2026-08-23)

*Round 8's closing sentence: finite acceptance recommended once these
narrow items close. All closed; nothing architectural moved.*

1. **R8-1 — the I6 vectors assert EXACT ORDERED IDs** (the reviewer's
   mutation — reversing the selection order — left the old four green):
   every vector now computes its expected ordered list by construction
   and asserts equality, including the precise dedup survivor (taken from
   `collapse_for_render`'s own survivor order) and the exact ranked
   backfill.
2. **R8-2 — the downgrade regression BITES**: a parse sentinel on
   `Edge`/`Episode.model_validate` proves no record validates before the
   newer-format refusal — the reviewer's version-check-after-parsing
   mutation now fails the test instead of passing silently.
3. **R8-3 — version-neutral candidate identity**: the artifact is
   `specs/evidence/0001/candidate.patch` (no version literal), the README
   and test module carry none, and the spec's Version row remains the ONE
   version carrier, per the standing R5-5 rule.
4. **The Sentra timing corrected**: "the same week" was not recoverable
   from the public page (which shows Apr 2026) — the claim now states
   exactly what the source shows.
5. **Package machinery (C8-1/C8-2, design note §16)**: sidecar RECORDS
   validated (digest syntax + self-consistent target), the in-flight seal
   EXPLICITLY declared (`IN_FLIGHT`) instead of frontier-inferred, and
   the predecessor boundary closed with the `NO_PRIOR` sentinel — the
   diff receives its base decided, never selecting internally.

## 21. Changes in v11 (the round-9 fold, 2026-08-23)

1. **R9-1 (blocking) — the I6 implementation violated its ordered
   contract**: the patch FILTERED the globally scored list, so order was
   global rank, not `reserved + remainder`; with the non-functional
   `has_pet` relation the reserved assertable edge surfaced fourth of
   four, and every order vector used functional `works_as`, where the
   authority permutation reorders anyway — the defect was masked by the
   vectors' own construction (the reserves were also top-ranked). The
   implementation now CONSTRUCTS `reserved + remainder` (each segment in
   scored order); the reviewer's vector is added exactly as described
   (one assertable record, globally last-ranked, non-functional relation,
   complete ordered output asserted) and is proven to fail against the
   pre-fix code; the dedup vector asserts the complete order, making
   §20's every-vector claim true. The I6 cell states the construction.
2. **R9-2 — the last version carrier**: the candidate test module's
   docstring still said `candidate/0001-v8`; it is version-neutral now
   and the R8-3 sweep greps the entire patch (zero survivors).
3. **R9-3 — the measurement is re-run, not carried**: the README's
   full-suite blast-radius count is regenerated at packaging time and
   recorded with its exact environment (python version, platform,
   command line, base commit) — a measured number without its
   environment is not reproducible evidence.

## 22. Changes in v12 (the round-10 fold, 2026-08-23)

1. **R10-1 (blocking) — the reserve protected eligibility, not
   relevance**: the spec reserves `count_relevant_assertable`, but the
   candidate reserved every assertable edge in the scored set — and
   `subgraph_for_query` deliberately seats query-unmatched user-subject
   edges there at baseline score. The reviewer's executed
   counterexample (`max_edges=4`, `coverage_share=0.0`, four relevant
   unverified facts + unrelated assertable `bananas`) produced
   `bananas, topic h0, topic h1, topic h2` — the unrelated record
   reserved first, a relevant fact dropped. The implementation now
   carries the overlap bit FROM scoring (`relevant_ids`) and reserves
   only query-relevant assertables — the reading that matches the
   spec's wording, as the reviewer ruled; the I6 cell says
   query-RELEVANT explicitly and the exact counterexample is vector
   (f), proven to fail against the pre-fix code.
2. **R10-2 — the opening block carried a revision**: `draft (v10)` +
   a §20 pointer survived beside the v11 Version row. The block now
   carries NO revision — the Version row is structurally the one
   carrier, instead of merely by claim. (Third strike for this class:
   R5-5, R9-2, R10-2 — the sweep now greps `(v` forms as well.)

## 23. Changes in v13 (the round-11 fold, 2026-08-24)

**Round 11's verdict is FINITE DESIGN ACCEPTANCE for draft v12**:
R10-1 closed (query relevance carried explicitly via `relevant_ids`;
the candidate suite 21/21; restoring the exact eligibility-only defect
produces 20 passed / 1 failed, the sole failure being the bananas
counterexample) and R10-2 closed (the opening block carries no
revision carrier). The trust-model architecture is not to be reopened.
What returned was one mechanical evidence-carrier defect:

1. **R11-1 — a carried measurement inside a "never carried" claim.**
   `CANDIDATE_README.md` said the focused suite was 20 passed while the
   branch ran 21: carried forward from v10 and incremented by
   inference, in the same paragraph claiming the measurement was
   re-run. Both figures now have exactly ONE producer.
   `specs/evidence/0001/measure_candidate.py` materialises the tree at
   the base commit, applies THE SHIPPED PATCH by its own bytes, runs
   the focused and full suites, and writes `candidate_results.json` —
   patch sha256, base commit, both measurements, the sorted FAILURE
   SET, and the environment. `specs/check_candidate_results.py`
   refuses any disagreement between that record, the patch's bytes and
   the README's stated figures, and runs in the sealer's extraction
   checks, so a stale count cannot reach a package (the reviewer's
   "so future count drift fails sealing", mechanised). Re-measured,
   not incremented: focused **21 passed**; full **16 failed / 1813
   passed / 20 skipped** at base `59cd1cf` — the old 1798/9 split
   predates 0024's landing and the gate work, which is exactly why the
   number had to be re-run rather than adjusted. The R9-3 closure
   evidence, which grepped a measurement DATE, now runs this binding.

## 24. Changes in v14 (the round-12 fold, 2026-08-24)

**Finite design acceptance STANDS** — round 12 found no semantic,
trust-boundary, migration or selection defect, confirmed the executable
candidate byte-identical to v11 apart from its README hunk, and
reconciled its own 1807/21 offline run exactly with the sealed 1820/8
through 13 declared environment-dependent transitions. One mechanical
evidence amendment:

1. **R12-1 — the checker bound a PROJECTION, not the record.** It
   validated patch hash, README focused count, README triple and
   failure-list LENGTH, while `candidate_results.json` claims base
   commit, environment, commands, focused outcome and a sorted failure
   set. The reviewer walked through both gaps: `base_commit` set to
   forty zeroes with Python `0.0.0` (README still stating the real
   ones) exited 0, and replacing one failure with a duplicate — 16
   entries, 15 unique — exited 0. The declared mutation matrix passed
   because it exercised only the four bound projections. Corrected:
   * the record is validated against a **closed, exactly typed
     schema** — every key required at every level, no extra key
     tolerated (a record that grows a field without a check is a red
     run), every value range-checked;
   * `failure_set` must be **sorted, unique, node-id shaped** and
     cardinality-equal to `full_suite.failed`;
   * the recorded commands are **imported from `measure_candidate`**,
     never retyped, so the record cannot describe a command it did not
     run; the README inside the patch is bound on focused count, full
     triple, base commit **and** Python version;
   * the mutation matrix now covers **every schema field** — each key
     deleted, an unknown key added at every level, each value corrupted
     per its type, both reviewer counterexamples verbatim, and all four
     README bindings;
   * the base is **independently reproducible**:
     `measure_candidate.py --base <committish>` materialises that tree,
     applies the shipped patch and re-runs both suites, and `--verify`
     regenerates the COMPLETE record from the base the record declares
     and refuses on any field difference. The **sealer runs it**, so a
     record that cannot be reproduced from its own declared base cannot
     be packaged. It bit on its first run: the shipped record declared
     kernel `1010-aws` and the host had moved to `1011-aws`, so the
     record was regenerated at the release commit `48cc833` (focused
     21, full 16F/1814P/20S) rather than the drift being excused.

## 25. Changes in v15 (the round-13 fold, 2026-08-24)

**Finite design acceptance remains in force** — round 13 found no new
semantic or trust-model defect and called the complete-record replay's
implementation sound. The finding was about its PROTECTION:

1. **R13-1 — the decisive guard was not regression-bound.** The
   extraction checker deliberately accepts some type-valid
   fabrications (`focused_suite.skipped` 0→1, an arbitrary nonempty
   `platform`, a failure replaced by a different validly-shaped node
   id); catching those is the REPLAY's job. But the named mutation
   matrix never invoked the replay — it tested only the extraction
   checker — so the reviewer planted `if False` on the sealer's call
   and watched the named test (1 passed) and the entire spec gate
   (88 passed, 4 skipped) stay green. The replay could have been
   removed or bypassed while every declared guard agreed, silently
   restoring R12-1. Corrected:
   * the enforcement is a NAMED function, `enforce_candidate_replay`,
     with its runner injectable — it was inline in `main()`, which is
     what made it untestable and therefore unprotected;
   * the comparison is a PURE function, `record_differences`, so the
     replay's discrimination is provable without paying for two suite
     runs;
   * `test_the_sealer_enforces_the_candidate_replay` binds three
     properties: **(a)** `main()` calls the enforcement on a REACHABLE
     path — the reviewer's `if False` and outright deletion were both
     PLANTED and both fail the test; **(b)** a failing replay aborts
     the seal (`SystemExit`), with a passing run as the pristine
     control; **(c)** the comparison catches every fabrication the
     extraction checker cannot — skipped 0→1, arbitrary platform,
     a swapped base sha, and failure-IDENTITY replacement.

## 26. Changes in v16 (the round-14 fold, 2026-08-25)

**Finite design acceptance remains in force** — no semantic or
trust-model defect; the full-record comparison was confirmed to catch
all four type-valid fabrications, and the candidate patch is
byte-identical to v13.

1. **R14-1 — "reachable path" was proved SYNTACTICALLY.** The round-13
   test walked `main()`'s AST for the enforcement call and rejected
   only a literal constant-false guard. The reviewer replaced it with
   `if a.version == "v0":` — a perfectly ordinary-looking call that is
   false for every real package — and watched both replay tests and the
   entire spec gate stay green while replay was disabled for every seal
   that matters. AST inspection was standing in for execution, which is
   the proxy class one level below where round 13 left it. Corrected:
   * the enforcement is now an **UNCONDITIONAL precondition** placed
     ahead of the measurement, so there is no longer a condition to
     make false — the only way past the line is to delete it. It also
     fails fast: a record that cannot replay now costs seconds rather
     than a full suite run;
   * `test_the_sealer_enforces_the_candidate_replay` **executes
     `main()`** with the current package identity, monkeypatches the
     enforcement to raise a sentinel, and REQUIRES that sentinel to be
     reached; a second sentinel on the measurement catches the bypass
     shape by name, so a skipped guard reports "reached the measurement
     without executing the replay" instead of timing out;
   * only main()'s clean-tree probe is stubbed (the test runs mid-edit)
     — every other call in that path executes for real, so the control
     flow under test is the real one;
   * three bypass shapes were PLANTED and each verified failing: the
     reviewer's `if a.version == "v0"`, a plausible
     `if os.environ.get("VERACIUM_STRICT")`, and outright deletion —
     with the pristine control passing after each restore.

## 27. Changes in v17 (the round-15 fold, 2026-08-25)

**Finite design acceptance remains in force; R14-1 is closed** — the
behavioral test proves `main()` reaches the enforcement, and the
impossible-version attack fails as required.

1. **R15-1 — the chain was tested link by link, never at the join.**
   Removing only `"--verify"` from the helper's argv runs
   `measure_candidate.py` in its default measure-and-print mode, which
   exits 0 without comparing the shipped record — and both replay tests
   and the entire spec gate stayed green, because the direct helper
   test injected unconditional return codes without examining the
   command, while the `main()` test replaced the helper wholesale. Every
   component was bound; the connection between them was not. Corrected,
   binding the invocation AND its behaviour:
   * the enforcement's exact command is asserted —
     `[sys.executable, <measure_candidate.py>, "--verify"]` — together
     with its working directory, since the replay needs git at the repo
     root;
   * the `--verify` branch is proven to DISCRIMINATE: with the
     expensive measurement stubbed (it is covered separately), a
     planted record difference returns nonzero and an identical replay
     returns zero;
   * the default mode is asserted to exit 0 **without** comparing —
     documenting the bypass rather than leaving it implicit, and making
     plain why the argv binding above is load-bearing;
   * that nonzero aborts sealing remains bound from round 13.
   Three connection-breaking mutants were PLANTED and each verified
   failing: the reviewer's dropped `--verify`, a wrong working
   directory, and a `--verify` branch neutered to always succeed.

## 28. Changes in v18 (the round-16 fold, 2026-08-25)

**Finite design acceptance remains in force; R15-1 is closed** — the
exact `--verify` invocation, its working directory, differing-record
refusal, identical-record success, and propagation of the nonzero
through the sealer are all bound.

1. **R16-1 — the replay PRODUCER was not regression-bound.** Every
   consumer of the results record had been bound, one round at a time,
   while `measure()` itself was tested only through monkeypatches.
   Replacing its body with `return json.loads(RECORD.read_text())` made
   the verifier compare the shipped record with itself — reporting
   exact replay in a non-git extraction — and both replay tests and the
   entire spec gate stayed green. An independent producer that can
   collapse into a copy of its own input is not independent. Corrected:
   * `measure(base, run=None)` takes an **injectable subprocess seam**,
     so the producer's behaviour is provable without two real suite
     runs;
   * `test_the_measure_producer_derives_the_record_from_real_commands`
     drives it with canned outputs chosen to be UNLIKE the shipped
     record's figures, and asserts the record is DERIVED from them —
     the focused count, the full triple, and the failure node ids all
     come from the runs' output, which a self-copy cannot satisfy;
   * and that the commands actually happened: the DECLARED BASE is
     materialised (not `HEAD`), the shipped patch is applied, both
     exact suite commands run, and each runs INSIDE the tree built from
     that base rather than in the repo;
   * three producer-collapse mutants were PLANTED and each verified
     failing — the reviewer's self-copy, a skipped patch application
     (measuring an unpatched tree), and materialising `HEAD` instead of
     the declared base.

## 29. Changes in v19 (the round-17 fold, 2026-08-25)

**Finite design acceptance remains in force; the literal R16-1
self-copy is caught** — an unconditional collapse now fails its
regression.

1. **R17-1 — the injected path was bound; the PRODUCTION path was
   not.** With the runner an optional parameter, tests injected one and
   production did not, so those were two different paths and only one
   of them was under test. A branch returning the shipped record
   whenever no runner was supplied left all three producer/replay/
   candidate tests and the entire spec gate green, while production
   `--verify` compared the record against itself and reported exact
   replay in a non-git extraction. Corrected exactly as prescribed:
   * `_measure_with_runner(base, run)` holds the implementation and its
     runner is **REQUIRED** — there is no default left to diverge, so
     the behaviour under test and the behaviour in production are the
     same code path;
   * `measure(base)` is the production entry point and is a
     **delegation and nothing else** — it holds no logic for a mutation
     to hide behind;
   * the producer regression now drives `_measure_with_runner`
     directly, and a new
     `test_the_production_measure_delegates_to_the_implementation`
     replaces the implementation with a sentinel and proves
     `measure(base)` reaches it **with the requested base and with
     `subprocess.run`** — the production runner, not a stand-in;
   * three production-path mutants were PLANTED and each verified
     failing: the reviewer's production-only self-copy, a wrapper
     handing a different runner, and a wrapper discarding the requested
     base.

## 30. The terminus question (v20, 2026-08-25)

`specs/evidence/0001/TERMINUS-NOTE.md` ships in this archive. It asks a
SCHEDULING question and contests no finding: rounds 11–17 each
identified a real bypass in the candidate-measurement machinery, each
was reproduced here before fixing, and each fix is in this package.

The note observes that those seven findings share a generator — bind a
thing, and the join to that thing becomes the next finding — and that
two facts bear on the disposition: the machinery under review exists
only to evidence a spec that is not yet implemented and is already
built to retire when the candidate folds (every component carries an
explicit absent-not-broken path), and the sixteen carrier failures that
acceptance authorises are real product work that cannot start until the
status flips. It offers three ways to close — acceptance with
evidence-maintenance status under the standing P1/P4 gates (the
reviewer's own A1 round-24 disposition), a statement of the remaining
threat model so the class closes in one round, or ruling the scaffold
out of scope for acceptance — and states plainly that if the reviewer
judges otherwise, we keep folding without asking again.
