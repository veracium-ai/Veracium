# Changelog

## Unreleased

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
