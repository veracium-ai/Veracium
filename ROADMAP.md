# Roadmap

Grounded in the `agent-memory` research findings. v0.1 ships the write-path spine
and graph recall; the items below complete the validated design.

## v0.1 — done
- [x] Schema: provenance-carrying edges + episodes, volatility, quarantine.
- [x] Embedded `SqliteStore` behind a `Store` interface; per-user isolation.
- [x] BYO `Complete`/`Embed` interface + Anthropic reference provider.
- [x] Write path: LLM extraction → typed edges + episode, functional
      supersession-with-history, structural third-party quarantine.
- [x] Graph recall: entity-matched subgraph + recent episodes, provenance-flagged.
- [x] Offline smoke test (scripted LLM).

## v0.2 — the curated view (finding 20) — done
- [x] `compile.py`: LLM cartographer compiles a budgeted wiki from edges+episodes,
      cached in the store, recompiled after N writes (`wiki_recompile_after_writes`).
      Claims are excluded from the compiled body and appended as a fixed,
      un-rephrasable quarantine block (finding 23-C: the leak is the episode, so
      the compiler must not weave claims into assertable prose).
- [x] `recall()` uses the wiki + per-query subgraph (the hybrid-v2 winner).

## v0.3 — the abstention gate (finding 23) — done
- [x] `gate.py`: before returning context, mark any answer path whose only
      support is a third-party-authored episode/claim as "no basis / unverified".
      Fixes both the confabulation-on-failure problem (D) and the residual
      episodic injection leak (C) — the two failures that shared one root cause.
- [x] Expose `mem.answer(user, query)` convenience that applies the gate, for
      hosts that want engram to answer rather than just supply context.

## v0.4 — lifecycle (findings 9/11/19)
- [ ] Volatility-driven expiry: transient facts confirm/decay/lapse on schedule.
- [ ] Offline consolidation job: compact cold episodes into summaries (retain
      first-occurrences of failures/illnesses/dates — the compaction-loss guard).
- [ ] Tenure-aware wiki budget so read cost stays bounded as history grows
      (finding 22: the graph/wiki read cost grows with the store otherwise).

## v0.5 — MCP server & packaging
- [ ] `engram.mcp_server`: `remember` / `recall` (and `answer`) tools; per-session
      user scoping; the host's own LLM wired as the `Complete` callable where
      possible.
- [ ] Publish; CI running the smoke + eval suites.

## v0.6 — regression suite from the research harness
- [ ] Port the synthetic-corpus generator + judge as `tests/eval/`; assert
      engram meets the research numbers (supersession ~100%, injection 0 asserts
      on the ladder, confabulation bounded once the gate lands).

## Deferred / research-tracked
- Neo4j / Postgres `Store` adapters (interface already in place).
- Graded relationship-aware source trust (finding B: the tension is milder than
  thought; content-quarantine already covers the main attack — low priority).
- Cross-family model eval (avoid monoculture in the internal LLM roles).
