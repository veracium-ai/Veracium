# API reference

```python
from veracium import Memory, MemoryConfig, EvidenceAuthor
```

## `Memory`

```python
Memory(*, llm, store=None, embed=None, config=None,
       telemetry=None, diagnostics=None, audit=None)
```

- `llm` — a `Complete` callable (required). See [Providing an LLM](#providing-an-llm).
- `store` — a `Store`; defaults to `SqliteStore(config.db_path)`.
- `embed` — an optional `Embed` callable (reserved for episode semantic fallback).
- `config` — a `MemoryConfig`; defaults to `MemoryConfig()`.
- `telemetry` / `diagnostics` / `audit` — optional sinks, all off by default:
  a consented content-free stats collector (`veracium.telemetry`), a local
  error-log reporter (`veracium.diagnostics`), and an **operation audit log**
  (`veracium.audit.AuditLog(path)`): one append-only JSONL line per operation —
  UTC timestamp, op, `user_id`, content-free counters; no memory text ever.
  Sink failures never break memory operations.

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

### `recall(user_id, query, *, token_budget=None) -> Recall`

Assemble grounded memory context for a query (curated wiki + per-query subgraph).

- `token_budget` — cap the rendered context at approximately this many tokens
  (heuristic: chars/4 — Veracium is tokenizer-agnostic, so treat the budget as
  approximate). Selection priority when trimming: query-matched facts, then
  unverified-claim flags (a host reasoning near a claim must see it flagged),
  then the wiki, then recent episodes; best-effort minimum of one item. `None`
  (default) = unbudgeted.

`Recall` fields:
- `context: str` — ready-to-inject block: grounded memory, plus a fenced
  "UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)" section when present.
- `grounded: str` — the verified, assertable partition only.
- `unverified: str` — third-party claims/reports only.
- `edges: list[Edge]`, `episodes: list[Episode]` — the raw units, for inspecting
  provenance or building your own prompt (always complete; the budget shapes
  the rendered context, not the raw material).
- `tokens_estimated: int`, `truncated: bool` — budget accounting.

```python
r = mem.recall("alice", "suggest a lunch spot")
prompt = f"{r.context}\n\nUser: suggest a lunch spot"   # drop into your own call
```

### `answer(user_id, query) -> str`

Recall + the abstention gate → a direct answer that only uses grounded memory,
never asserts unverified claims, and abstains rather than guessing. Use this when
you want Veracium to answer; use `recall()` when you want to answer yourself.

### `maintain(user_id, *, consolidate=True) -> dict`

The "overnight" job: expire stale facts (transient lapse, durable flag) and
consolidate cold episodes. Idempotent; call on a schedule.

### `dispute(user_id, edge_id, *, reason="", actor="user") -> dict` / `confirm(user_id, edge_id, *, actor="user", date=None) -> dict`

Explicit user-feedback verbs (get `edge_id`s from `Recall.edges`):

- **`dispute`** — the user challenges a fact. Non-destructive: the edge is
  invalidated (reason `"disputed"`) — immediately out of every assertable
  surface, retained as queryable history — and the dispute itself is recorded
  as an episode with the actor and reason. If the fact was right after all, it
  re-enters as new evidence via `remember()`.
- **`confirm`** — the user validates a fact: refreshes its validity (clears the
  possibly-stale flag, so it won't lapse), boosts confidence, records the
  confirmation episode. Only **assertable** facts can be confirmed — elevating
  a quarantined claim by "confirmation" would be a laundering vector; a user
  affirming a claim is new user-authored evidence and belongs in `remember()`.

Neither verb is exposed over MCP (an agent-callable suppress/validate verb is a
prompt-injection target) — wire them to real user actions in your host. Note
`correct` and `elaborate` need no verb: they *are* `remember()` (supersession /
accumulation).

### `forget(user_id) -> dict`

**Compliance erasure** — irreversibly removes everything stored for the user:
all edges (superseded history and quarantined claims included), all episodes,
the wiki cache, and counters. The data-subject right, deliberately distinct
from lifecycle: `maintain()` never deletes, `forget()` never preserves. No
undo — `export_memory` first if a recoverable copy is wanted. Also on the CLI
with a confirmation prompt: `veracium forget --user alice`. **Deliberately not
an MCP tool** — an irreversible-wipe verb callable by an agent is a standing
prompt-injection target; erasure is a host/operator action.

### `export_memory(user_id, path) -> dict` / `import_memory(path, *, user_id=None) -> dict`

Portable memory: one JSONL file per user carrying the **complete** store of
record — every edge (superseded history and quarantined claims included) and
episode with full provenance, disclosure, and validity windows. Import is
idempotent (existing ids are skipped, never overwritten); `user_id=` remaps the
records. Also available without code: `veracium export out.jsonl --user alice`
/ `veracium import out.jsonl [--user bob]`.

Trust note: provenance in an export file is *data* — import only from sources
you trust as much as the database file itself.

### `close()`

Close the underlying store.

## `EvidenceAuthor`

`USER` · `THIRD_PARTY` · `SYSTEM`. See [concepts](concepts.md).

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
  Veracium parses tolerantly.

Reference provider (needs `pip install veracium[anthropic]`):

```python
from veracium.llm.anthropic import AnthropicComplete
mem = Memory(llm=AnthropicComplete())                       # models per role, overridable
mem = Memory(llm=AnthropicComplete(models={"gate": "claude-opus-4-8"}))
```

Wrapping your agent's existing client is often simplest — see
`examples/claude_cli_provider.py` for a subprocess-based example, or
`examples/openai_provider.py` for an OpenAI-compatible one (OpenAI, vLLM,
Ollama's `/v1` endpoint). It attempts `json_schema` as structured output and
falls back to a plain call — no error — if the endpoint doesn't support it.

## Providing a store

The default `SqliteStore` is embedded and zero-dependency. To back memory with
Neo4j/Postgres, implement `veracium.store.base.Store` (all methods are per-`user_id`)
and pass it as `store=`.
