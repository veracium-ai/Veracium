# Changelog

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
  provider (`engram[anthropic]`).
- **MCP server** (`engram[mcp]`): `remember` / `recall` / `answer` / `maintain`
  tools for any MCP-compatible agent.
- **Telemetry** (opt-in, off by default): anonymous, content-free usage
  statistics with explicit consent (`engram telemetry`), a weekly in-process
  flush (`mem.flush_telemetry()`), and a whitelist-enforced content-free
  payload. See `docs/telemetry.md`.
- **Self-check** (`engram selfcheck` / `mem.self_check()`): runs the load-bearing
  guarantees (supersession, injection defense, abstention) against a throwaway
  synthetic memory and self-scores them structurally (no LLM judge); the counters
  feed telemetry's content-free `selfcheck` event.
- **Diagnostics** (opt-in error reporting; `engram diagnostics`): genuine errors are
  logged to a local, user-owned rotating file and re-raised unchanged; the log is
  sent for diagnosis only with consent (advance permission or a per-incident yes),
  redacted, previewable, anonymous, and bounded. No endpoint shipped. See
  `docs/diagnostics.md`.
- **Docs**: `docs/concepts.md`, `docs/api.md`, `docs/mcp.md`; acceptance eval
  (`tests/eval/`) holding the library to the research claims (5/5, 0 injection
  asserts on the live run).
