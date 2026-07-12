# Changelog

## Unreleased

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
