# Changelog

## 0.4.6 — 2026-08-01

- **Two defects found while verifying an external review of `specs/0002` — both
  live in released 0.4.5, both fixed.** Neither was reported by the review; both
  turned up in the process of checking its claims against running code.

  **`confirm()` returned a `valid_from` it never set.** 0.4.5's M2 fix stopped
  `confirm()` moving a fact's first-known date, because `render_edges` emits
  `(since <valid_from>)` into answer context and a January preference confirmed
  in March read *"(since March)"*. The fix corrected the model's context and
  **left the same false date in the return value a host UI reads** —
  `confirm()` returned `{"valid_from": <confirmation date>}` while the edge kept
  its real one. The return now carries both `valid_from` (the real, unchanged
  first-known date) and `confirmed_at`. **A fix that missed one of its own
  surfaces; the sibling it missed is the one an integrator sees.**

  **A future-dated event was accepted, and was unrecoverable.** `date=` had no
  upper bound, so `remember(date="2099-01-01")` set both `valid_from` and
  `observed_at` to 2099. `observed_at` is only ever advanced with `max(...)` —
  which is what correctly defeats *back*-dating, and is therefore exactly what
  made *forward*-dating permanent: no later confirmation could bring it down.
  **One host-supplied date removed a fact from lapse, decay and staleness
  flagging for 73 years, with no API to undo it.** Event dates more than a day
  in the future are now rejected at `_event_dt`, the single point every event
  date passes through, so `remember()`, `confirm()`, `correct()` and
  `record_outcome()` are all covered.

  **Behaviour change:** a future `date=` now raises `ValueError` instead of
  being stored. It has no legitimate meaning — the event date records when a
  statement was made, not what it is about, so *"the contract expires in 2027"*
  is a value and never an event date. Malformed dates keep their existing
  fallback to now.

- **retrieval: coverage-aware subgraph selection was measured and stays OFF.**
  0.4.2 shipped it disabled and said *"the default will change only if a
  balanced measurement supports it."* **That measurement has now run, under a
  pre-registered protocol, and it does not support it.**

  30 items drawn stratified on distinct `valid_from` days — the variable the
  code actually branches on — with the hypothesis, primary metric, thresholds,
  analysis plan and stop rule fixed in advance and approved before any run.
  Three replicates across four arms.

  **Coverage rose on 12/12 items (+5.25 distinct sessions at the tested
  setting). The primary metric — the fraction of answer-bearing turns actually
  retrieved — improved on 2 of 12, against a pre-declared threshold of 10.**
  The mechanism does exactly what it was built to do and does not buy the thing
  it was built for. Read cost was flat, so it is not expensive — it is
  ineffective on this measure. Exploratory arms at half and double the reserve
  moved coverage monotonically (+2.75 / +7.67 sessions) and the primary metric
  not at all, so this is not a mistuned parameter.

  **`subgraph_coverage_share` keeps its default of `0.0`, and the code stays**
  — off by default, tested, and re-runnable if the storage granularity that
  bounds this result ever changes.

  **What the result does not establish.** It is evidence about day-clustered
  coverage selection **under day-granular storage**, on one benchmark and one
  metric, n=12. Seven of the twelve items were already at a perfect hit rate in
  the baseline, so more than half the sample had no room to improve and the
  pre-declared threshold was, in hindsight, unreachable from the moment the
  sample was fixed. That does not rescue the hypothesis — coverage rose
  everywhere and the metric moved almost nowhere — but "ineffective in general"
  is **not** what was shown.

  One item regressed from a perfect hit rate to zero when coverage was enabled;
  that is being investigated separately as a defect rather than folded into this
  result.

## 0.4.5

Three provenance defects, found by an audit of the maintenance-time operations
(`specs/0002-maintenance-provenance-invariant.md`).

> **Correction (2026-08-01):** this entry originally said the audit covered
> **every** maintenance-time operation. It did not. Review found
> `portability.import_memory` absent from the enumeration — a surface that
> reconstructs *every* trust-bearing field from a file and writes it straight to
> the store, bypassing the ingest path's trust machinery entirely. The word is
> withdrawn until the enumeration is mechanical rather than recalled. See
> `specs/0002` §M6. The audit was
prompted by two advisories in four days — GHSA-r7j7-5jq9-3f5q and
GHSA-hcj3-8jqc-wqrp — which are the same shape: a maintenance operation crossing
a trust boundary the write path guards correctly. **None of the three below is a
trust-boundary bypass**, so no advisory accompanies this release.

- **`confirm()` no longer moves a fact's first-known date.** It used to set
  `valid_from` to the confirmation date — **the exact defect 0.4.3 shipped C′ to
  eliminate**, in a sibling path the fix never touched. Because `render_edges`
  emits `(since <valid_from>)` into answer context, a preference stated in
  January and confirmed in March was rendered to the model as *"(since
  2026-03-01)"* — a false statement in front of the model, not merely lost
  history. **0.4.3's changelog asserted "valid_from is set at creation and never
  mutated"; that was not true of `confirm()`, and now is.** A confirmation is
  new evidence about *liveness*, so it advances `provenance.observed_at`.
  **Not repairable:** dates already moved by a prior `confirm()` are
  unrecoverable — the original is not recorded anywhere.
  *A test asserted the old behaviour, which is why C′ did not catch it.*

- **A staleness flag can no longer be cleared by a different author.**
  `needs_confirmation` renders as *"confirm before relying on it"* — a question
  addressed to the party who stated the fact. Reinforcement cleared it
  unconditionally, and the 0.4.1 same-class guard compares **disclosure** class,
  where `USER` and `SYSTEM` both sit in `MENTIONABLE`. So a system-authored
  restatement answered a question meant for the user. Now only same-author
  evidence clears it; `confirm()` remains the explicit path, and third-party
  content was already correctly blocked.

- **Outcome authorship is no longer overwritten.** `record_outcome()`'s
  upgrade-in-place path replaced the episode's `author_of_evidence` with the new
  actor's, discarding who made the earlier judgment — in a system whose stated
  principle is supersession-never-erasure. The prior author is now retained in
  the episode summary. Outcome episodes are excluded from recall, so nothing
  reached the model either way.

**Also added:** `tests/test_maintenance_invariant.py`, which states the class
rather than the instances. The load-bearing one is **N7** — *a full `maintain()`
cycle never moves an edge from the UNVERIFIED block to the GROUNDED one* —
expressed over the observable boundary rather than any field, so it catches the
next instance even when the mechanism is one nobody anticipated. **Both
advisories would have failed N7.**

## 0.4.4 — security

- **SECURITY: episode consolidation laundered third-party content into the
  grounded block.** `maintain()`'s consolidation step built the consolidated
  episode's provenance from a **single member** of the cold batch
  (`cold[0].provenance`), so a mixed batch whose first episode happened to be
  user- or system-authored collapsed to `author_of_evidence=USER` with
  `derived_from=None`. `Provenance.third_party_influenced` then reported
  `False`, and `gate.partition_parts` — which routes episodes on exactly that
  property — moved the summarised third-party text out of the UNVERIFIED block
  and into the **GROUNDED** one, where it may be asserted.

  This is the attack `gate.partition_parts` names in its own docstring (*"a
  system-authored summary quoting a received email launders attacker text into
  its episode — route by influence, never by authorship alone"*): consolidation
  was defeating the defence its own module documents. It required no
  hallucination and no prompt injection — a faithful summariser compacting a
  mixed batch was sufficient. Same class as GHSA-r7j7-5jq9-3f5q (0.4.1): a
  **maintenance-time** operation crossing a trust boundary that the write path
  guards correctly.

  **Fixed:** consolidated provenance is now computed across the **whole set** —
  `author_of_evidence=SYSTEM` (which is what the code's own comment always
  claimed it was) and `derived_from=THIRD_PARTY` if **any** member was
  third-party-influenced. The result stays in the UNVERIFIED block, matching
  pre-consolidation behaviour.

  **Affected:** every version with consolidation, through 0.4.3. **Exposure
  requires** `maintain()` to run consolidation over **≥8 cold episodes**
  (default `consolidate_min_batch`) older than **30 days** (default
  `consolidate_after_days`) with **mixed authorship** and a trusted episode
  first in store order. Deployments that never call `maintain()`, or whose
  episodes are single-author, are unaffected. **Upgrade if you ingest
  third-party content (received mail, documents, tool output) and run
  maintenance.** No store migration is required; existing consolidated
  episodes are **not** retroactively re-labelled — see the advisory for how to
  identify them.

  Found while writing the first specification under `specs/PROCESS.md`: the
  template's rule to enumerate a changed field's consumers *mechanically rather
  than from memory* surfaced `lifecycle.py` as a writer of
  `author_of_evidence`, which the memory-written list had missed.

## 0.4.3

- **telemetry: the abstention heuristic under-counted abstentions.** It existed
  twice — a narrow copy behind `answer`'s content-free `abstained` counter and a
  broader one in `selfcheck` — and the narrow copy missed the most common
  refusal phrasing the gate actually emits (*"I don't have any confirmed
  information about X"*). Abstention is the metric that most directly tracks the
  product's core guarantee, so under-reporting it was the worst place for a
  duplicated regex to drift. Now defined once as `gate.ABSTAINED` and imported
  by both; regression test uses verbatim openings from real judged answers.
  Found while hand-classifying benchmark misses, not by any test.

- **BREAKING (semantics): `valid_from` is now first-known and immutable.**
  Reinforcement used to overwrite it with the latest restatement date, so a
  fact stated in January and restated in March reported `valid_from` = March
  and the January date was unrecoverable. Because `render_edges` emits
  `(since <valid_from>)` into recall context, that was **a false statement in
  the answer context**, not merely lost history — and it violated the field's
  own documented contract (`edges_since` already distinguishes "when it became
  true" from "when veracium recorded it"). Now: `valid_from` is set at creation
  and never mutated; `provenance.observed_at` carries the latest recording (it
  already did); **`maintain()` ages liveness against `observed_at`** instead, so
  a restatement still keeps a fact alive — it refreshes the field that means
  liveness. T1 absorption's winner inherits the **earliest** `valid_from`
  (`min`, was `max`) and the latest `observed_at`; recall's recency tiebreak
  and proactive recall's "unrefreshed since" read `observed_at`.
  **`introspect()` renames `first_observed`/`last_observed` →
  `first_known`/`last_recorded`** — the old `first_observed` was computed from
  the `max()`ed field and so reported *last* observed under a "first" name.
  **Forward-fixing only:** already-collapsed `valid_from` values in existing
  stores cannot be recovered. Invariant now asserted on every write path:
  `valid_from <= observed_at`.
  Found by a LongMemEval experiment; the write-path defect, not the benchmark,
  is the reason it ships.

- **retrieval: time coverage in subgraph selection — implemented but OFF by
  default (`subgraph_coverage_share = 0.0`).** When enabled, most of the budget
  is still filled by relevance alone and a reserved tail goes to periods not
  already represented. **It ships disabled because it is unvalidated**: the
  measurement that motivated it was retracted — the benchmark sample it was
  diagnosed from proved unrepresentative on exactly the dimension involved, so
  the mechanism has never been tested on data that could exercise it. The code
  and tests are here so the experiment can run; the default will change only if
  a balanced measurement supports it. Pure top-k has no coverage
  term, so a cluster of facts sharing the question's vocabulary takes the
  whole budget and a question spanning months gets answered from a single
  day — measured on LongMemEval, where an interval question recalled 37 date
  mentions of which **one** was distinct, making the interval uncomputable
  and the abstention correct. Clusters on `valid_from`, the only temporal key
  always available (session identity is a host concept most callers never
  supply). Conservative by construction: the head is pure relevance so the
  strongest matches are never displaced, coverage only spends the reserved
  tail on candidates that already passed relevance, the tail backfills by
  relevance when there is no other period to reach, and stores below the
  budget are bit-identical to before. Set `subgraph_coverage_share=0.0` to
  restore pure relevance ranking.

  > **Outcome (2026-08-01):** the balanced measurement promised above has run.
  > **It does not support enabling this, and the default stays `0.0`** — see the
  > Unreleased entry at the top of this file. Recorded here rather than by
  > editing the text above, so the original commitment and its answer both stay
  > readable.

## 0.4.2

- **retrieval (graph): recall was query-blind on large stores.** Every
  user-subject edge carried a *constant* score, so once a store outgrew
  `max_subgraph_edges` the truncation kept whichever edges the store listed
  first and the query stopped mattering for the subject that owns most facts.
  Small stores were unaffected (everything fits), which is why fixtures never
  showed it; on a ~1,700-fact store recall returned effectively the same facts
  whatever you asked, and raising the cap only returned more of the same
  (measured: 40 → 200 edges gave **no accuracy gain at 3.8× the read cost**).
  Now: user-subject edges stay always-eligible — the "everything off the user
  node" contract is unchanged — but relevance decides which survive
  truncation, with recency as a deterministic tiebreak. Also: `relation` is
  matchable text (so "pet" reaches `has_pet`), the non-discriminating owner
  token `user` is excluded from matching, and query wording is folded to a
  fixed point over ordinary plurals ("deadlines" reaches `deadline`).
  Found by the LongMemEval pilot, whose failure taxonomy put **0 misses in
  extraction** and the rest in ranking and synthesis.

## 0.4.1

- **security (graph)**: identity merges (reinforcement + T1 absorption) are
  now confined to edges of the **same disclosure class** — previously both
  were trust-blind, so a third-party `use_only` restatement of a user fact
  could (a) retire the user's assertable edge (reason `absorbed_duplicate`),
  leaving no assertable version of a true, user-evidenced fact — a
  third-party event could silently demote user facts out of assertable
  recall (subset form new in 0.4.0's T1); and (b) refresh a USER edge's
  liveness, clear its `needs_confirmation` flag, and raise its confidence
  (exact-match form present since 0.3.0 and earlier; widened by T1).
  Cross-class restatements now accumulate as separate edges, each carrying
  its own trust — the explicit upgrade path for corroborated third-party
  material remains `confirm()`/a user restatement. Dedup never makes trust
  decisions. Found by the research session's post-merge T1 review
  (`proposals/t1-review.md`); locked by cross-trust regression tests and a
  new hard **trust-canary gate in the bench engine tier**
  (`engine.trust_canary_failures == 0`).

## 0.4.0

- **proactive recall**: `recall(user_id)` with no query returns a session-start
  briefing — dated commitments due/overdue, possibly-stale facts to confirm,
  current transient state, recent history. Volunteering is disclosure-gated:
  only `MENTIONABLE` facts surface; `use_only` and quarantined material never
  appear unprompted (the Disclosure tier doing the job it names). LLM-free,
  deterministic, budget-aware (commitments outrank history when trimming);
  MCP `recall` exposes it by omitting `query`. New config:
  `proactive_deadline_window_days` / `proactive_recent_days`.

- **introspect** (the "inspectable memory" half of a recurring demand signal;
  `dispute`/`confirm`/`correct` are the editable half): `introspect(user_id,
  mode="summary"|"categories")` — the formatted transparency view over what
  was always exposed raw. Counts by relation / evidence author / disclosure
  tier, lifecycle state, retired history by reason, episode counts;
  `categories` adds the facts grouped by relation with the same provenance
  markers recall renders. LLM-free, store-only; content-free `introspect`
  telemetry event.

- **CLI memory verbs**: `veracium recall` (no query → the proactive briefing;
  with a query → subgraph + *cached* wiki — store-only either way, never
  compiles, needs no provider), `veracium remember` (ingest one event;
  `-` reads stdin; `--author`/`--derived-from` route trust exactly like the
  API), `veracium introspect` (`--categories`, `--json`). Memory becomes
  scriptable without touching Python.

- **Claude Code hooks recipe** (`examples/claude_code_hooks/`): ambient
  memory via lifecycle hooks instead of (or alongside) MCP — a `SessionStart`
  hook injects the proactive briefing at zero schema-token cost (and again
  after context compaction), a `UserPromptSubmit` hook writes the user's
  words back through a detached `veracium remember` so extraction never
  blocks a turn. Provenance discipline documented: captured content the user
  did not author must be routed `third_party`/`derived_from`.
- **value-equivalence T1 — subset absorption** (`graph.apply_supersession`,
  per `proposals/value-equivalence.md`): a *more specific* restatement of a
  held value ("cat Miso" after "Miso") now absorbs the shorter form instead
  of accumulating a duplicate — the prior retires non-destructively (reason
  `absorbed_duplicate`, note carries `absorbed_by:<winner-id>`), the winner
  takes `max(valid_from)`/`max(confidence)` and keeps its own provenance,
  and no `supersedes` pointer is set (absorption is identity, not change —
  `render_edges` never shows an absorbed value as history, and on functional
  relations a subset-shaped restatement no longer churns a false
  supersession). A *less specific* restatement ("Miso" after "cat Miso")
  reinforces the fuller edge: validity refreshed, `needs_confirmation`
  cleared — allowed because write-time evidence just arrived. Guardrails:
  ordered-subsequence match only (the 'tea over coffee' ≠ 'coffee over tea'
  contract survives), at most 2 extra tokens, same (subject, relation) only;
  `his X`/`her X` still never merge. Exact-match reinforcement now takes
  `max(valid_from)` too, so a back-dated restatement can no longer rewind a
  fact's freshness. The S4 robustness checker and bench record classify
  absorptions in their own bucket (`absorbed`), never as `duplicated`.

## 0.3.0

- **bench**: internal benchmark suite (`bench/run_bench.py`) — engine-overhead
  medians against a zero-latency scripted model, the acceptance eval, and the
  robustness tier at `--s4-samples 50` with duplicate-shape classification
  (the value-equivalence T0 measurement), recorded per-release to
  `bench/results.jsonl` with a `--compare` regression gate. Now part of the
  maintainer release checklist. See `bench/README.md`.

- **mcp 2.0 compat**: the MCP SDK 2.0.0 renamed `FastMCP` to `MCPServer`
  (same decorator API) — `veracium-mcp` now imports whichever the installed
  SDK provides, so `mcp>=1.0` stays the supported range on both majors.

- **outcome tracking (V4)**: co-designed with the first production consumer —
  `record_outcome()` records uses and judgments of facts as `kind="outcome"`
  episodes (the source of truth) with derived edge counters
  (`times_used`/`outcome_counts`/`last_outcome`); judgments upgrade the
  matching use in place via (`edge_id`, `evidence_ref`). Vocabulary:
  `unreviewed`/`confirmed`/`corrected` (human) /`challenged`/`concurred`
  (LLM judge), actor rules enforced. Edge-blind by design: `record_outcome`
  never supersedes facts; the explicit fact-level `correct()` verb supersedes
  with reason `"corrected"`. `challenged` reuses the possibly-stale flag;
  counters render into recall as information, never gating; outcome episodes
  are excluded from the narrative recall window and from LLM consolidation.
  Portability format v2 (`"record"` marker; v1 imports unchanged). Neither
  verb is an MCP tool.

## 0.2.4

- **selfcheck UX**: `veracium selfcheck` now preflights the provider — a
  missing SDK or missing `ANTHROPIC_API_KEY` exits with one clear install
  hint instead of a traceback or, worse, a garbage `FAIL … injection
  asserts=1` scorecard (an erroring check was conservatively scored as an
  assert, which read exactly like the injection guarantee failing). If the
  provider fails every check mid-run (e.g. bad credentials), the result is
  now reported as **DID NOT RUN** (exit code 2) — an environment problem is
  never rendered as a memory-safety result.

## 0.2.3

- **MCP Registry**: README carries the `mcp-name` validation marker and
  `server.json` (current registry schema) sits at the repo root — Veracium is
  publishable to registry.modelcontextprotocol.io, which the MCP directories
  crawl. `docs/mcp.md` refreshed: PyPI install flow (the page still described
  a pre-PyPI clone install), the `remember` tool row now documents
  `derived_from`, `recall` documents `token_budget`, and the deliberately
  non-MCP verbs are listed with their rationale.

## 0.2.2

- **veracium-mcp CLI**: `--help` and `--version` now work (previously any
  argument was ignored and the stdio server booted silently — confusing on a
  first install); unknown arguments fail with a pointer to `--help`; a boot
  failure (e.g. missing `ANTHROPIC_API_KEY`) exits with a clear one-line
  message instead of a traceback.

## 0.2.1

- **host queries** (requested by the first production consumer for its
  intelligence layer): `Memory.list_entities()` — distinct ids with
  edge/episode counts, for proactive-recall planning and coverage audits — and
  `Memory.edges_since(user_id, since)` — edges learned after a date, filtered
  on `provenance.observed_at`, including superseded/quarantined material so
  change-detection sees everything. Host/admin surface; neither is an MCP tool
  (cross-user enumeration is not an agent capability). `Store` gains
  `list_users()` (non-abstract, like `forget_user`).

## 0.2.0

The launch release: the five capability gaps identified by an independent
landscape analysis, plus the display-brand and one-liner refresh.

- **branding**: display brand is capitalized **Veracium** in all prose (code
  identifiers stay lowercase); canonical one-liner applied to the PyPI summary,
  README lead, and MCP server description.
- **audit**: opt-in operation audit log — `Memory(audit=AuditLog(path))`
  appends one content-free JSONL line per operation (UTC timestamp, op,
  `user_id`, the op's counters; never memory text) covering
  remember/recall/answer/maintain/dispute/confirm/forget/export/import.
  Append-only, host-owned; sink failures never break memory.
- **feedback verbs**: `dispute(user_id, edge_id, reason=, actor=)` — the edge
  leaves every assertable surface immediately (non-destructive invalidation,
  reason `"disputed"`), and the dispute itself is remembered as an episode with
  actor and reason; `confirm(user_id, edge_id)` — refreshes validity, clears
  the possibly-stale flag, records the confirmation. `confirm` refuses
  non-assertable edges (elevating a claim by confirmation would be a laundering
  vector — affirmation is new evidence, use `remember()`). Neither is an MCP
  tool by design. Content-free `feedback` telemetry event.
- **forget** (compliance erasure): `Memory.forget(user_id)` irreversibly erases
  everything stored for a user — edges incl. superseded history and quarantined
  claims, episodes, wiki cache, counters. Distinct from lifecycle by design
  (`maintain()` never deletes; `forget()` never preserves). CLI:
  `veracium forget --user X` (confirmation prompt; `--yes` to skip).
  Deliberately not exposed over MCP — an agent-callable wipe verb is a standing
  prompt-injection target. `Store` gains `forget_user()` (non-abstract;
  custom stores keep working until they implement it).
- **portability**: JSONL export/import — `Memory.export_memory(user_id, path)`
  writes the complete store of record (all edges incl. superseded history and
  quarantined claims, all episodes, full provenance/disclosure);
  `import_memory(path, user_id=...)` is idempotent (existing ids skipped, never
  overwritten) and can remap users. CLI: `veracium export` / `veracium import`
  (store-only, no LLM needed). The wiki cache is not exported — it recompiles.
- **recall**: token-budget-aware context assembly — `recall(user_id, query,
  token_budget=N)` caps the rendered context (chars/4 heuristic; Veracium is
  tokenizer-agnostic). Trimming follows a documented priority: query-matched
  facts, then unverified-claim flags (never silently dropped below the facts
  they annotate), then the curated wiki (all-or-nothing), then recent episodes
  newest-first; best-effort minimum of one item. `Recall` gains
  `tokens_estimated`/`truncated`; the MCP `recall` tool exposes the parameter;
  the content-free telemetry `recall` event gains a `trimmed` counter.

## 0.1.7

- **security (ingest/gate/compile)**: closed the **system-event laundering**
  bypass — third-party text embedded inside a `SYSTEM`/`USER`-authored event (a
  triage verdict quoting a received email's subject, a summary of a message
  body) previously acquired the event's full trust and could surface as
  assertable user facts. `remember()` gains `derived_from`: declare
  `author=SYSTEM, derived_from=THIRD_PARTY` and trust is capped at the minimum
  of the two — edges cap at `use_only` (claims still quarantine), and the
  episode routes to the unverified channel at the gate *and* is excluded from
  the compiled wiki (episodes now route by third-party *influence*, not
  authorship alone). `Provenance` records both fields; MCP `remember` exposes
  the parameter; documented in `docs/concepts.md` ("Mixed provenance") and
  `SECURITY.md`. Found by the first production consumer on a real-mailbox
  backfill (130 laundered assertable edges); reported in
  `proposals/system-event-laundering.md` with the attack fixture now locked as
  a regression test.

- **ingest**: an `unparseable` extraction no longer leaves a history gap — the
  turn records a content-free placeholder episode ("(unprocessed <type> event —
  extraction returned no parseable JSON; content not retained)") with full
  provenance/`evidence_ref`. Deliberately not the raw event text: that would
  feed unmediated, possibly adversarial input straight into recall prompts.
- **_json**: among list fallbacks, `extract_json` now prefers a non-empty
  list of dicts (the shape of a bare triples array) over junk like `[]` or
  `[1, 2]` that happened to parse earlier in the prose.
- **graph**: `his`/`her` removed from the value-equivalence filler list — they
  can point at a third party ("his assistant" vs "her assistant") and so carry
  meaning; user-referential possessives (`my`/`our`/`their`) remain filler.
- **examples**: `openai_provider.py` — `OpenAIComplete` wraps any
  OpenAI-compatible chat-completions API (OpenAI, vLLM, Ollama's `/v1`), with
  per-role model mapping, honest structured-output fallback, and a memoized
  capability check. First outside contribution — thanks @vreddy-commits (#8).

## 0.1.6

- **security (compile)**: a third-party *inference* (`use_only`) is no longer fed
  into the compiled wiki. `recall()` places the wiki in the gate's assertable
  GROUNDED block, so a `use_only` fact reaching the wiki could be asserted through
  the wiki path — even though `gate.partition` (0.1.3) already routed such inferences
  to UNVERIFIED. `compile._grounded_inputs` now excludes `use_only` edges, mirroring
  the gate; the inference still shapes behavior via recall's unverified channel, only
  kept out of the assertable body. Completes the 0.1.3 fix (which covered only the
  subgraph path). Adds a unit lock (`test_grounded_inputs_excludes_use_only`).

## 0.1.5

- **ingest/_json**: a distill response whose first parseable JSON value is a
  *list* no longer crashes `remember()` (`'list' object has no attribute
  'get'`). `extract_json` now prefers the first JSON *object* — skipping prose
  debris like a stray `[]` before the real payload — and returns a bare array
  only as a fallback, which ingest normalizes as the triples payload with its
  wrapper omitted. Found by the robustness tier's first lmsys-chat-1m run
  (3/368 real turns crashed, all code-shaped inputs).
- **tests**: robustness tier Phase 2 — S4 (reinforcement ≠ duplication: a seeded
  sample of fact-yielding turns is re-ingested; new-edge growth is reported as a
  distribution) and S5 (every `maintain()` report must carry non-negative counts
  bounded by the store it ran over). Both soft signals; hard gates unchanged.

## 0.1.4

- **ingest**: an unparseable distill response (the extractor answering in prose —
  typically a refusal on jailbreak-shaped or degenerate input) no longer raises
  out of `remember()`; it records nothing and returns
  `{"episode": "", "facts": 0, "quarantined": 0, "unparseable": True}`, with a
  content-free `unparseable` counter in the telemetry `ingest` event. Found by
  the new robustness tier on its first run (7/19 fixture turns crashed).
- **tests**: new opt-in robustness tier (`tests/robustness/`,
  `VERACIUM_ROBUSTNESS=1`) — streams real, messy conversations through the write
  path and holds veracium's guarantees as hard invariants (no internal crashes,
  no cross-user leakage, no assertable third-party user-facts, well-formed
  persistence), plus soft distributions (yield, relation drift, latency,
  provider crash-rate). Ships a committed adversarial fixture corpus
  (`fixtures/messy.jsonl`); points at a locally exported lmsys-chat-1m for the
  full run. Reports are redacted — raw corpus text never appears.

## 0.1.3

- **gate/graph** (security): third-party *inferences* — real-looking user facts
  whose only support is third-party evidence (marked `use_only` at ingest) — were
  treated as grounded by the abstention gate and rendered as bare facts, so
  `answer()` would assert e.g. an employer learned solely from a received email.
  The `use_only` disclosure is now enforced everywhere it's read: the gate
  partitions these under UNVERIFIED (never asserted), and `render_edges` tags
  them `[third-party-reported; unconfirmed]` in recall context and the compiled
  wiki. New `Edge.assertable` / `Edge.use_only` properties expose the discipline.

## 0.1.2

- **graph**: reinforcement now matches paraphrased values ("dog named Ollie" /
  "dog Ollie" / "dog: Ollie") via order-preserving normalized-token comparison,
  instead of exact string equality — a re-stated fact whose extraction phrasing
  drifted between runs used to accumulate as a near-duplicate edge. Order still
  matters ("tea over coffee" ≠ "coffee over tea"), so functional supersession of
  genuinely new values is unaffected.

## 0.1.1

Reliability fixes surfaced by building the runnable demo notebook
(`examples/demo.ipynb`, new in this release):

- **selfcheck**: the abstention detector now recognizes natural abstention
  phrasings ("I don't have any confirmed record of ..."); previously a correct
  abstention could flakily score the check FAIL.
- **distill**: the extraction prompt now carries a one-clause gloss per relation
  (`Relation.desc`), disambiguating confusable pairs — employment occasionally
  landed under `works_on` instead of `works_as`, silently defeating supersession.
- **examples**: end-to-end scam-email demo notebook with real captured outputs
  and a Colab badge, linked from the README.

## 0.1.0

First working release — the validated layered memory design as a plug-in.

- **Store of record**: typed graph edges + dated episodes with provenance;
  embedded `SqliteStore` behind a `Store` interface; per-user isolation.
- **Write path**: LLM extraction → edges + episode, functional
  supersession-with-history, reinforcement on re-statement, structural
  third-party quarantine (claims never become user facts).
- **Curated view**: LLM-compiled wiki cached and recompiled after N writes;
  third-party claims/episodes are never fed to the compiler.
- **Recall + abstention gate**: grounded/unverified partition; `answer()` answers
  only from grounded memory, never asserts unverified claims, abstains rather than
  confabulating.
- **Lifecycle**: volatility-driven expiry (transient lapse, durable stale-flag),
  consolidation with a compaction-loss guard; `maintain()` runs both.
- **Bring-your-own LLM**: `Complete`/`Embed` callables; Anthropic reference
  provider (`veracium[anthropic]`).
- **MCP server** (`veracium[mcp]`): `remember` / `recall` / `answer` / `maintain`
  tools for any MCP-compatible agent.
- **Telemetry** (opt-in, off by default): anonymous, content-free usage
  statistics with explicit consent (`veracium telemetry`), a weekly in-process
  flush (`mem.flush_telemetry()`), and a whitelist-enforced content-free
  payload. See `docs/telemetry.md`.
- **Self-check** (`veracium selfcheck` / `mem.self_check()`): runs the load-bearing
  guarantees (supersession, injection defense, abstention) against a throwaway
  synthetic memory and self-scores them structurally (no LLM judge); the counters
  feed telemetry's content-free `selfcheck` event.
- **Diagnostics** (opt-in error reporting; `veracium diagnostics`): genuine errors are
  logged to a local, user-owned rotating file and re-raised unchanged; the log is
  sent for diagnosis only with consent (advance permission or a per-incident yes),
  redacted, previewable, anonymous, and bounded. No endpoint shipped. See
  `docs/diagnostics.md`.
- **Docs**: `docs/concepts.md`, `docs/api.md`, `docs/mcp.md`; acceptance eval
  (`tests/eval/`) holding the library to the research claims (5/5, 0 injection
  asserts on the live run).
