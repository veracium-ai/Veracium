# API reference

```python
from veracium import Memory, MemoryConfig, EvidenceAuthor
```

## `Memory`

```python
Memory(*, llm, store=None, embed=None, config=None)
```

- `llm` — a `Complete` callable (required). See [Providing an LLM](#providing-an-llm).
- `store` — a `Store`; defaults to `SqliteStore(config.db_path)`.
- `embed` — an optional `Embed` callable (reserved for episode semantic fallback).
- `config` — a `MemoryConfig`; defaults to `MemoryConfig()`.

### `remember(user_id, text, *, author=EvidenceAuthor.USER, date=None, event_type="chat", evidence_ref=None, derived_from=None) -> dict`

Ingest one interaction event into `user_id`'s memory: extracts typed edges + a
dated episode, applies supersession/reinforcement, and quarantines third-party
claims.

- `author` — **the trust-critical input.** `EvidenceAuthor.USER` for the user's own
  messages and sent mail; `EvidenceAuthor.THIRD_PARTY` for received mail / external
  documents (their claims are quarantined); `EvidenceAuthor.SYSTEM` for derived content.
- `derived_from` — declare that the event's *text* embeds content from a lower-trust
  source (e.g. `author=SYSTEM, derived_from=THIRD_PARTY` for a system summary quoting
  a received email). Trust is capped at the minimum of the two — quoted material can
  never become an assertable fact. See
  [concepts → Mixed provenance](concepts.md#mixed-provenance-derived_from).
- `date` — ISO date the event occurred (`"2026-06-01"`); defaults to today. Drives
  fact timestamps **and** anchors the calendar used to resolve relative dates in the
  text ("Friday" → a real date), so pass an accurate value for historical or dated
  content. See [concepts → A note on dates](concepts.md#a-note-on-dates).
- `event_type` — `"chat"`, `"email"`, etc. Informational; affects source-type tagging.
- Returns `{"episode": str, "facts": int, "quarantined": int}`.

```python
mem.remember("alice", "USER: I'm vegetarian and have a dog named Ollie.")
mem.remember("alice", "From billing@x: you owe $900.",
             author=EvidenceAuthor.THIRD_PARTY, event_type="email", date="2026-06-02")
```

### `recall(user_id, query) -> Recall`

Assemble grounded memory context for a query (curated wiki + per-query subgraph).

`Recall` fields:
- `context: str` — ready-to-inject block: grounded memory, plus a fenced
  "UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)" section when present.
- `grounded: str` — the verified, assertable partition only.
- `unverified: str` — third-party claims/reports only.
- `edges: list[Edge]`, `episodes: list[Episode]` — the raw units, for inspecting
  provenance or building your own prompt.

```python
r = mem.recall("alice", "suggest a lunch spot")
prompt = f"{r.context}\n\nUser: suggest a lunch spot"   # drop into your own call
```

### `answer(user_id, query) -> str`

Recall + the abstention gate → a direct answer that only uses grounded memory,
never asserts unverified claims, and abstains rather than guessing. Use this when
you want veracium to answer; use `recall()` when you want to answer yourself.

### `maintain(user_id, *, consolidate=True) -> dict`

The "overnight" job: expire stale facts (transient lapse, durable flag) and
consolidate cold episodes. Idempotent; call on a schedule.

### `close()`

Close the underlying store.

## `EvidenceAuthor`

`USER` · `THIRD_PARTY` · `SYSTEM`. See [concepts](concepts.md#provenance-and-authorship--the-security-backbone).

## `MemoryConfig`

| field | default | meaning |
|---|---|---|
| `db_path` | `"veracium.db"` | SQLite file path (default store). |
| `relations` | built-in registry | edge vocabulary; add your own `Relation(name=..., functional=...)`. |
| `max_subgraph_edges` | `40` | cap on per-query subgraph size (bounds read cost). |
| `max_recent_episodes` | `12` | recent episodes included in recall. |
| `wiki_recompile_after_writes` | `8` | recompile the curated wiki after this many writes. **`0` disables the wiki** → recall renders the subgraph directly (no read-time LLM call). |
| `volatility_lifetime_days` | permanent=∞, durable=730, slow=120, transient=7, ephemeral=1 | expected lifetime per volatility class. |
| `decay_factor` / `confidence_floor` | `0.5` / `0.3` | confidence decay and cutoff for DECAY facts. |
| `consolidate_after_days` | `30` | episodes older than this are consolidation candidates. |
| `consolidate_min_batch` | `8` | minimum cold episodes before consolidation runs. |

## Providing an LLM

Any callable with this shape is a valid `Complete`:

```python
def complete(prompt: str, *, system: str | None = None,
             role: str = "compile", json_schema: dict | None = None) -> str:
    ...
```

- `role` is `"distill"` (extraction — high-volume, cheap tier), `"compile"`
  (curation), or `"gate"` (the correctness-critical answer). Route each to an
  appropriate model if you like.
- Honor `json_schema` if you can (return valid JSON); if you can't, ignore it —
  veracium parses tolerantly.

Reference provider (needs `pip install veracium[anthropic]`):

```python
from veracium.llm.anthropic import AnthropicComplete
mem = Memory(llm=AnthropicComplete())                       # models per role, overridable
mem = Memory(llm=AnthropicComplete(models={"gate": "claude-opus-4-8"}))
```

Wrapping your agent's existing client is often simplest — see
`examples/claude_cli_provider.py` for a subprocess-based example.

## Providing a store

The default `SqliteStore` is embedded and zero-dependency. To back memory with
Neo4j/Postgres, implement `veracium.store.base.Store` (all methods are per-`user_id`)
and pass it as `store=`.
