# engram

A provenance-aware memory plug-in for agentic systems. Give any agent durable,
per-user memory that recalls facts about the user, past interactions, and what
worked — while structurally resisting the injection and confabulation failures
that plague naive memory.

Engram is the production distillation of an evaluation-driven research project
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
  systems handle worst; engram's strongest.)*
- **Representation is a security control.** Third-party claims (received email,
  external docs) are quarantined *structurally* — stored as `third_party_claim`
  edges with the claimant as subject, never as user facts. Content-type quarantine
  catches obligation/debt/renewal claims regardless of how plausible they look.
  *(Held against a full plausibility ladder incl. contact-impersonation.)*
- **Bring your own model.** Engram never owns your API keys or model choice; it
  calls a `Complete` callable you supply. A reference Anthropic provider ships in
  the box.
- **Embedded by default.** Zero external services: one SQLite file. Swap in
  Neo4j/Postgres later via the `Store` interface.

## Install

```bash
pip install engram            # core (pydantic + stdlib only)
pip install engram[anthropic] # + reference LLM provider
pip install engram[mcp]       # + MCP server
```

## Use (library)

```python
from engram import Memory, EvidenceAuthor
from engram.llm.anthropic import AnthropicComplete

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

## Use (MCP)

`engram-mcp` exposes `remember` / `recall` tools to any MCP-compatible agent
(status: in progress — see Roadmap).

## Status

v0.1 — write path (extraction → typed edges + episodes, supersession, structural
quarantine) and graph-based recall are implemented and tested. See `ROADMAP.md`.

## License

MIT
