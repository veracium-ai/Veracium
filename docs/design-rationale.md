# Design rationale

Veracium makes a few deliberate choices that differ from what the agent-memory
category has converged on. This page says what they are, why, and what the
equivalent affordance is — plus what's genuinely on the roadmap. It exists so
you can tell a *missing* feature from a *refused* one.

## Refused by design

### No `update()` / `delete()` on memories

Most memory APIs let callers mutate or remove items by id. Veracium doesn't,
on purpose: **memory changes through evidence, not edits.** When the user
re-states a fact, the new value supersedes the old one and the old value is
retained with its validity window — so "what does the user prefer *now*?" and
"what did they prefer *before*?" are both answerable, and an audit trail is a
side effect of the data model rather than a bolted-on log. In-place mutation
(the "last write wins" pattern) is the single most common failure mode in this
category: it silently destroys history, breaks provenance, and makes
contradictions unresolvable after the fact.

What replaces each verb:

| You want | Veracium's way |
|---|---|
| update a fact | `remember()` the new statement — functional supersession links and retains the old value |
| re-affirm a fact | `remember()` the re-statement — reinforcement refreshes validity and clears staleness |
| retract as wrong | supersession with the correction; the wrong value stays visible *as history* |
| remove a user entirely | compliance erasure (`forget`, roadmap) — a data-subject right, deliberately distinct from day-to-day memory ops |

### No LLM-free extraction mode

Some tools offer template or local-NLP extraction so you can skip LLM calls.
Veracium requires a `Complete` callable, because its guarantees are made **at
extraction time**: deciding that a sentence is a *third-party claim about the
user* rather than a user fact, routing it to quarantine, picking the
supersession target, assigning volatility. Pattern-matching extraction cannot
make those calls — a template-extracted store would look like veracium while
silently lacking the properties this project exists to provide. We won't ship
a mode whose failure is invisible.

The honest version of "cheap/offline extraction" is already here: `Complete`
is any callable, so a **local model** (e.g. Ollama or vLLM via
`examples/openai_provider.py`, or any llama-class model) gives you zero-API-cost,
fully offline extraction *with* the guarantees intact — the cost is compute,
not correctness.

### No score-decay deletion / TTL purging

Facts age by **volatility class**, assigned per fact at extraction
(permanent / durable / slow / transient / ephemeral, each with a configurable
lifetime): transient facts lapse from recall, long-lived facts get flagged
possibly-stale for confirmation — but nothing is destroyed by aging. Decay
affects *visibility and ranking*, never data. A six-year-old fact is exactly
as retrievable-on-request as yesterday's.

## Already here, sometimes under a different name

- **Temporal conflict resolution** — functional supersession-with-history is
  the core write path, not an add-on (see above).
- **Per-type lifecycle** — volatility classes are per-*fact*, which is finer
  than per-*type* half-lives.
- **Trust levels** — provenance carries `author_of_evidence` × `disclosure` ×
  `derived_from`, which caps trust per *content source within a single event*
  (see [concepts → Mixed provenance](concepts.md#mixed-provenance-derived_from));
  a per-item trust enum can't express "my event, quoting their text."
- **Multi-tenant isolation** — per-`user_id`, enforced at the store layer and
  fuzz-tested against a real 1M-conversation corpus (0 leaks). Ids are opaque
  strings, so scopes compose by convention (`"team:backend"`).
- **Hybrid retrieval** — recall is entity-graph + curated wiki + recent
  episodes; in the research this project distills, that combination beat
  vector-similarity retrieval on every question type tested. (An embedding
  fallback for non-entity queries is a reserved hook in the interface.)
- **"What worked" memory** — episodes record failures, fixes, and dated
  commitments, and consolidation is required to preserve first occurrences of
  each; the relation registry (`uses_tool`, `source_reliable`,
  `source_dead_end`, …) is host-extensible via `MemoryConfig(relations=...)`.
- **Corrections and confirmations** — re-stating *is* correcting (supersession)
  and re-affirming *is* confirming (reinforcement); explicit `dispute()` /
  `confirm()` verbs are on the roadmap for hosts that want them as API calls
  with actor provenance.

## On the roadmap (real gaps, agreed)

See [ROADMAP.md](../ROADMAP.md) for status:

- **Token-budget-aware recall** — `recall(query, token_budget=...)` with
  adaptive rendering; today's recall is internally bounded but the caller
  can't set the budget.
- **Portable export/import** — a documented JSONL interchange format carrying
  full provenance and disclosure, so memory is never locked in.
- **Explicit feedback verbs** — `dispute()` / `confirm()`.
- **Compliance erasure** — `forget(user_id)`: bulk, irreversible, logged;
  deliberately separate from lifecycle.
- **Opt-in operation audit log** — who called what, when, over which user.
- Research-tracked: procedural outcome-tracking (times-used / last-outcome
  ranking), access scopes & sensitivity tags for multi-principal hosts,
  the embedding fallback for non-entity recall.
