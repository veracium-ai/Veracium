# Veracium

**Veracium is a provenance-aware memory plug-in for agentic systems** —
durable, per-user memory that resists the injection and confabulation failures
that plague naive agent memory.

```bash
pip install "veracium[anthropic]"
```

## Three failure modes of naive agent memory

1. **Poisoning** — a received email says "you owe $900"; similarity retrieval
   happily serves it back as *your* fact.
2. **Confabulation** — memory has no answer, the model invents one anyway.
3. **Staleness** — you changed jobs; memory either keeps the old employer or
   silently overwrites the history.

## Three structural properties — each with executable checks

1. **Quarantine** — third-party claims are stored as *claims by a claimant*,
   never as user facts; content that entered under lower trust can never reach
   an assertable surface — including [text your own tools quote](concepts.md#mixed-provenance-derived_from).
2. **Grounded or silent** — [`answer()`](api.md) asserts
   only verified memory, flags unverified claims explicitly, and says
   "I don't know" rather than guess.
3. **Supersession, never erasure** — new values replace old ones with the
   history retained; nothing is edited in place, nothing is destroyed by aging.

## Verify it yourself

```bash
veracium selfcheck    # runs the core regression checks against a throwaway memory
```

Or run the [live demo notebook](https://github.com/veracium-ai/Veracium/blob/main/examples/demo.ipynb)
— a scam email, a laundered triage verdict, a disputed fact, all with real
captured outputs.

## Where to go

- **[Concepts](concepts.md)** — the mental model: edges, episodes, the compiled
  wiki, provenance and trust, the abstention gate.
- **[API reference](api.md)** — `Memory`, recall with token budgets, feedback
  verbs, portability, compliance erasure.
- **[MCP server](mcp.md)** — plug memory into any MCP-compatible agent with no
  host-side Python.
- **[Design rationale](design-rationale.md)** — why there's no
  `update()`/`delete()`, no LLM-free extraction, no TTL purging — a *refused*
  feature is not a *missing* one.
- [CHANGELOG](https://github.com/veracium-ai/Veracium/blob/main/CHANGELOG.md) ·
  [ROADMAP](https://github.com/veracium-ai/Veracium/blob/main/ROADMAP.md) ·
  [PyPI](https://pypi.org/project/veracium/)
