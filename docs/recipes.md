# Recipes

Short, copy-pasteable examples — one per capability. Each assumes:

```python
from veracium import Memory, EvidenceAuthor
mem = Memory(llm=your_complete_callable)   # see api.md → Providing an LLM
```

## Quarantine content your agent merely read

```python
# The user's own words: trusted facts.
mem.remember("alice", "USER: I'm vegetarian.")

# A received email: its claims are stored AS claims, never as facts.
mem.remember("alice", "From billing@x: you owe $900.",
             author=EvidenceAuthor.THIRD_PARTY, event_type="email")

print(mem.answer("alice", "Do I owe anyone money?"))
# -> declines to assert the $900; flags it as an unverified claim
```

## Declare mixed provenance (`derived_from`)

Your own tool's output that *quotes* untrusted text — a triage verdict, a
summary of a received document — must not launder that text into facts:

```python
mem.remember("alice",
             f"Triage classified the mail (subject: {subject!r}) as spam.",
             author=EvidenceAuthor.SYSTEM,
             derived_from=EvidenceAuthor.THIRD_PARTY,   # caps trust at the source
             event_type="triage")
```

## Fit recall into a prompt budget

```python
r = mem.recall("alice", "what matters for this email?", token_budget=300)
prompt_block = r.context          # facts first, claim flags kept, wiki/history trimmed
print(r.tokens_estimated, r.truncated)
```

## Let the user see and correct their memory

```python
edges = mem.recall("alice", "my job").edges          # inspect: raw facts + provenance
fact = next(e for e in edges if e.relation == "works_as")

mem.dispute("alice", fact.id, reason="I never said that")   # out of recall, kept as history
mem.confirm("alice", fact.id)                               # "yes, still true" — refreshes it
```

## Move memory between systems (and inherit it)

```bash
veracium export alice.jsonl --user alice --db veracium.db
veracium import alice.jsonl --user bob   --db other.db     # remap = inheritance
```

The export carries *everything* — superseded history, quarantined claims, full
provenance. Importing under a new id is how a new project inherits a team's
accumulated experience.

## Erase a user (compliance)

```python
mem.export_memory("alice", "alice-backup.jsonl")   # optional: no undo below
mem.forget("alice")                                # edges, episodes, wiki, counters — gone
```

## Keep an operation audit log

```python
from veracium.audit import AuditLog
mem = Memory(llm=..., audit=AuditLog("memory-audit.jsonl"))
# one content-free line per operation: timestamp, op, user_id, counters
print(AuditLog("memory-audit.jsonl").entries(op="forget"))
```

## See which entities have memory, and what's new

```python
mem.list_entities()                     # [{"user_id": ..., "edges": n, "episodes": n}]
mem.edges_since("vendor:acme", "2026-07-01")   # learned since July — incl. claims
```

## Run fully local (no API bill)

```python
# examples/openai_provider.py wraps any OpenAI-compatible endpoint:
from openai_provider import OpenAIComplete
mem = Memory(llm=OpenAIComplete(base_url="http://localhost:11434/v1",
                                models={"distill": "llama3.1",
                                        "compile": "llama3.1",
                                        "gate": "llama3.1"}))
```
