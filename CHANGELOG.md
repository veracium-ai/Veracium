# Changelog

## Unreleased

- **retrieval: time coverage in subgraph selection (E1).** When a store is
  larger than `max_subgraph_edges`, most of the budget is still filled by
  relevance alone but a reserved tail (`subgraph_coverage_share`, default
  0.25) goes to periods not already represented. Pure top-k has no coverage
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
