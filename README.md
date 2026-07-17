# Veracium

<!-- mcp-name: io.github.veracium-ai/veracium -->

[![tests](https://github.com/veracium-ai/Veracium/actions/workflows/test.yml/badge.svg)](https://github.com/veracium-ai/Veracium/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/veracium)](https://pypi.org/project/veracium/)
[![Python](https://img.shields.io/pypi/pyversions/veracium)](https://pypi.org/project/veracium/)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Veracium is a provenance-aware memory plug-in for agentic systems** —
durable, per-user memory that resists the injection and confabulation failures
that plague naive agent memory. It remembers facts about the user, past
interactions, and what worked, with provenance on every fact.

Veracium is the production distillation of an evaluation-driven research project
(`agent-memory`): every design choice below traces to a measured finding, and the
research's synthetic-corpus harness is reused as the regression suite.

## Why it's shaped this way

- **Typed graph + dated episodes are the store of record.** Entity facts live as
  relational edges (with unforgeable provenance); interaction history lives as
  dated episodes. A curated "wiki" view is compiled from them and cached — never
  the source of truth. *(The layered design won on both short and 9-week horizons;
  flat stores each failed one regime.)*
- **Supersession, never erasure.** Functional facts (preference, employer,
  deadline) keep one current value with the prior value retained as history —
  "what did X used to be?" stays answerable. *(The category commercial memory
  systems handle worst; Veracium's strongest.)*
- **Representation is a security control.** Third-party claims (received email,
  external docs) are quarantined *structurally* — stored as `third_party_claim`
  edges with the claimant as subject, never as user facts. Content-type quarantine
  catches obligation/debt/renewal claims regardless of how plausible they look.
  *(Held against a full plausibility ladder incl. contact-impersonation.)*
- **Bring your own model.** Veracium never owns your API keys or model choice; it
  calls a `Complete` callable you supply. A reference Anthropic provider ships in
  the box.
- **Embedded by default.** Zero external services: one SQLite file. Swap in
  Neo4j/Postgres later via the `Store` interface.

## Install

```bash
pip install "veracium[anthropic]"   # core + the reference LLM provider
```

Extras: `[mcp]` adds the MCP server, `[dev]` adds pytest. The core alone depends
only on `pydantic`. To work from source instead:

```bash
git clone https://github.com/veracium-ai/Veracium.git && cd Veracium
pip install -e ".[anthropic,dev]"
```

Links: [docs](https://veracium-ai.github.io/Veracium/) · [veracium.ai](https://veracium.ai) · [PyPI](https://pypi.org/project/veracium/)

## Use (library)

```python
from veracium import Memory, EvidenceAuthor
from veracium.llm.anthropic import AnthropicComplete

mem = Memory(llm=AnthropicComplete())   # or pass your own Complete callable

# Remember interactions. `author` is the trust-critical input.
mem.remember("alice", "USER: I'm vegetarian and have a dog named Ollie.")
mem.remember("alice", "From billing@scam: you owe $900.",
             author=EvidenceAuthor.THIRD_PARTY, event_type="email")

# Recall grounded, provenance-flagged context for a prompt.
ctx = mem.recall("alice", "suggest a lunch spot")
print(ctx.context)   # states the vegetarian constraint; the $900 "claim" is
                     # rendered under a never-assert flag, not as a fact.
```

No Anthropic API key? `AnthropicComplete` is just a convenience — Veracium calls any
`Complete` callable you supply. To run without SDK/key setup, wrap a client you
already have; `examples/claude_cli_provider.py` wraps the `claude` CLI as a
drop-in provider (`from claude_cli_provider import ClaudeCLIComplete`), and
`examples/openai_provider.py` wraps any OpenAI-compatible chat-completions API
(OpenAI itself, vLLM, Ollama's `/v1` endpoint) via `OpenAIComplete` — point it
at a local server with `OpenAIComplete(base_url=...)` and override `models` with
whatever model name your server serves.

## Use (MCP)

`veracium-mcp` exposes `remember` / `recall` / `answer` / `maintain` tools to any
MCP-compatible agent (Claude Desktop/Code, others) with no host-side Python. See
[docs/mcp.md](docs/mcp.md) for the config JSON and tool reference.

## Documentation

Hosted docs: **[veracium-ai.github.io/Veracium](https://veracium-ai.github.io/Veracium/)**

- **[examples/demo.ipynb](examples/demo.ipynb)** — the scam-email injection demo,
  runnable end to end ([open in Colab](https://colab.research.google.com/github/veracium-ai/Veracium/blob/main/examples/demo.ipynb)).
- **[examples/langchain_memory.py](examples/langchain_memory.py)** — Veracium as
  the long-term memory layer of a LangChain chat app (session-keyed hybrid:
  LangChain buffers recent turns, Veracium holds durable facts with provenance
  and quarantine; your existing LangChain model powers both sides).
- **[docs/concepts.md](docs/concepts.md)** — the mental model: edges vs episodes
  vs the compiled wiki, provenance & authorship, quarantine, the abstention gate,
  lifecycle.
- **[docs/api.md](docs/api.md)** — the public API: `Memory`, `MemoryConfig`,
  `EvidenceAuthor`, providing your own LLM callable or store.
- **[docs/mcp.md](docs/mcp.md)** — running and registering the MCP server.
- **[docs/design-rationale.md](docs/design-rationale.md)** — why there's no
  `update()`/`delete()`, no LLM-free extraction, no TTL purging — and what's
  genuinely on the roadmap.
- **[docs/telemetry.md](docs/telemetry.md)** — the opt-in, anonymous, content-free usage statistics (off by default).
- **[docs/diagnostics.md](docs/diagnostics.md)** — opt-in error reporting: local-first error log, consented + redacted send.
- **[ROADMAP.md](ROADMAP.md)** · **[CHANGELOG.md](CHANGELOG.md)**

## Status

The validated layered design is implemented, tested (44 offline tests, plus
opt-in live tiers: the acceptance eval and a real-corpus robustness harness),
and passes its own research-claim bar (5/5, 0 injection asserts). Roadmap
v0.1–v0.7 complete, plus opt-in telemetry, a self-check, consented error
reporting, and an operation audit log. See [ROADMAP.md](ROADMAP.md).

## License

MIT
