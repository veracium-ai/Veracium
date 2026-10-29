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
- `telemetry` / `diagnostics` / `audit` — optional sinks, all off by default (with a
  `diagnostics` reporter attached, `remember` also records the provider degrades it
  survives — see docs/diagnostics.md, "Degrade records"):
  a consented content-free stats collector (`veracium.telemetry`), a local
  error-log reporter (`veracium.diagnostics`), and an **operation audit log**
  (`veracium.audit.AuditLog(path)`): one append-only JSONL line per operation —
  UTC timestamp, op, `user_id`, content-free counters; no memory text ever.
  Sink failures never break memory operations.

### `remember(user_id, text, *, author=EvidenceAuthor.USER, date=None, event_type="chat", evidence_ref=None, derived_from=None, context=None) -> dict`

Ingest one interaction event into `user_id`'s memory: extracts typed edges + a
dated episode, applies supersession/reinforcement, and quarantines third-party
claims.

- `author` — **the trust-critical input.** `EvidenceAuthor.USER` for the user's own
  messages and sent mail; `EvidenceAuthor.THIRD_PARTY` for received mail / external
  documents (their claims are quarantined); `EvidenceAuthor.SYSTEM` for derived content.
  **One speaker per event.** Authorship is per event, and ingest does not separate
  speakers inside one: pass a conversation turn by turn — the user's turns under
  `EvidenceAuthor.USER`, the assistant's under `EvidenceAuthor.ASSISTANT` — or pass
  only the user's turns. A whole transcript passed under `author=USER` can store the
  assistant's own first-person statements ("I live in Denver") as the user's facts
  and assert them; turns with no speaker labels are the likeliest case.
- `context` — **the host's positive ingress declaration** (specs/0011 §4d).
  `EvidenceContext.direct()` attests first-party capture;
  `EvidenceContext.derived(X)` declares the content derives from class X.
  **Absent any declaration (no `context`, no `derived_from`) the content class
  floors to `derived(THIRD_PARTY)` — nothing from the event is assertable.**
  Absence stopped being the trusted cell at 0011's acceptance; `remember`
  deliberately never mints `direct()` on your behalf. A malformed context
  raises and nothing is written; passing both `context` and `derived_from`
  raises.
- `derived_from` — the legacy form of the same declaration: the event's *text*
  embeds content from a lower-trust source (e.g. `author=SYSTEM,
  derived_from=THIRD_PARTY` for a system summary quoting a received email).
  Still honoured as a positive `derived(X)` declaration. Trust is capped at
  the minimum of author and content class — quoted material can never become
  an assertable fact. See
  [concepts → Mixed provenance](concepts.md#mixed-provenance-derived_from).
- `date` — ISO date the event occurred (`"2026-06-01"`); defaults to today's UTC calendar
  date (a bare date is read as UTC midnight, so the default uses the same clock). Drives
  fact timestamps **and** anchors the calendar used to resolve relative dates in the
  text ("Friday" → a real date), so pass an accurate value for historical or dated
  content. See [concepts → A note on dates](concepts.md#a-note-on-dates).
- `event_type` — `"chat"`, `"email"`, etc. Informational; affects source-type tagging.
- Returns a summary dict for logging/telemetry. The counters are all
  present on **every** path (an absent key is never a zero), and so is one
  outcome boolean:
  `extraction_unusable` (bool, specs/0025 §4c as amended 2026-09-11 —
  **True when the provider's first answer produced no shape-valid triple**:
  rejected before any triple was read (no JSON object; an `instructions`
  value of the wrong type), a missing or non-list `triples`, or a non-empty
  list none of whose members is a well-formed `{subject, relation, object}`
  dict; **False otherwise**, including for a legitimately empty extraction
  and for a list whose members were well-formed but all refused for another
  reason, which the counters below carry. It says an answer was unusable,
  never which way — that is in the diagnostics log. A host with no
  diagnostics reporter attached reads this to tell a broken provider from a
  provider that found nothing; the MCP `remember` tool result carries it
  too, unlike the operator counters, which that surface strips) ·
  `unparseable` (bool, PRESENT ONLY on the rejected-before-any-triple path,
  where it is True — the narrower, older signal; a host may keep reading it) ·
  `episode` (str) · `facts` · `quarantined` · `supersessions` ·
  `reinforcements` · `within_episode_contested` (functional keys the event named two
  value groups for: nothing retired for them, the values held as contested; specs/0003) · the vocabulary-enforcement counters `invalid` /
  `retried` / `recovered` / `residual` (specs/0025) · `procedures` /
  `procedural_refused` (specs/0037 v16 — routines the user stated in the event,
  recorded as procedural records through the verbatim-quote gate, and
  procedural emissions refused for a missing, paraphrased or unverifiable
  quote; never rendered into context either way) · `subject_refused`
  (specs/0025 as amended 2026-09-08 — facts whose returned subject carries
  `|`, the prompt's alternation taken literally by a provider; dropped and
  never written, since a subject cannot be re-filed) · `speaker_restricted`
  (specs/0051 — facts a speaker-labelled transcript restricted: stored
  `use_only` because their value appears only in a turn labelled for an
  assistant, or not attested because only such a turn stated them; counted
  once each. A non-zero count means the host passed a mixed transcript as
  one user event: split it by speaker) ·
  `redispositioned` (specs/0024 — triples whose `third_party_claim`
  label contradicted its own claimant slot and were re-dispositioned to
  `unclassified` at `use_only`) · and the trust-state audit facts
  `quarantined_at_birth` / `birth_revocation_digest` (specs/0023).
  **The MCP tool surface strips the operator counters** — they are a
  library surface, not a tool-call surface.

```python
mem.remember("alice", "USER: I'm vegetarian and have a dog named Ollie.",
             context=EvidenceContext.direct())
mem.remember("alice", "From billing@x: you owe $900.",
             author=EvidenceAuthor.THIRD_PARTY, event_type="email", date="2026-06-02",
             source_id="billing-mailbox",     # required for third-party content
             context=EvidenceContext.direct())
```

### `record_procedure(user_id, summary, *, author, context, relation="follows_procedure", note=None, when=None, evidence_ref=None, source_id=None) -> str`

Record a **procedural** record (specs/0037) — a procedure the user follows,
a host-declared content kind that is never asserted as fact and never enters
recall's grounded or unverified context. This is the ONLY producer of a
procedural record: the extractor never sees a procedural relation. Returns
the new edge id.

- `summary` — the host's gloss-level name of the procedure, the only stored
  text `describe_procedures` ever renders. `note` holds step-level detail and
  is stored but **never rendered**.
- `author` — the authorship axis, exactly as `remember` takes it.
- `context` — **must carry a basis**: `EvidenceContext.direct(basis="stated")`
  (the user said they follow it) or `basis="observed"` (a pattern they reported
  observing), or `EvidenceContext.derived(X, basis=…)`. A context without a
  basis, or a basis outside `{stated, observed}`, raises and writes nothing.
  Basis is cap-only: absorption carries the whole-set minimum
  (`observed` ≤ `stated`) and a stored basis never changes.
- `relation` — must be registered with `relation_kind="procedural"` in this
  Memory's registry (the default registry ships `follows_procedure`), else
  `ValueError` (`relation_not_procedural`). The record is stamped
  `record_kind="procedural"` at write; a later registry change moves nothing.
- Disclosure is derived, never supplied: a standing-revoked `source_id`
  quarantines the record at birth, exactly as `remember` does.
- Every argument refuses its empty or malformed form before any write
  (`TypeError` for a wrong type, `ValueError` for a wrong value). No episode
  is written. Exports holding any procedural record are stamped format 11 —
  format 12 once any of them carries the producer stamp (specs/0037 v23: every
  procedural record written from that version says which path wrote it,
  `producer="host"` here, `"extractor"` from the quote-gated capture) — which
  older readers refuse; the default `import_memory` path refuses
  procedural records (another host's basis is its declaration) and
  `restore=True` round-trips a store's own, producer included.
  Exports from a store holding any redaction record (specs/0041) are stamped format 13
  and carry one `redaction` line per notice they may carry; older readers refuse them, and
  `import_memory` weighs each notice in the same transaction as its record (see
  "Redaction notices" under `import_memory`).

```python
mem.record_procedure("alice", "Credentials are rotated quarterly.",
                     author=EvidenceAuthor.USER,
                     context=EvidenceContext.direct(basis="stated"),
                     note="step 1: … (never rendered)")
```

**Procedures captured from `remember` (specs/0037 v16–v19).** On a user-authored event the
extractor may emit a `follows_procedure` triple carrying `quote`, the verbatim span in which the
user states a routine of their own. Ingest admits it only through ordered, refuse-only gates:
the author is the user; the quote is a whitespace-normalised substring of the event text AND one
whole sentence of it whose boundaries are ESTABLISHED at both ends (specs/0037 v24.1, fail
closed): the start or end of the user's turn, or a `?`/`!` followed by a sentence start, is a
boundary; a decimal point is inside a sentence; a sentence ending in `?` is a question and
refused; a mid-text period establishes nothing — it may end a sentence or an abbreviation ("in
env. Prod only after approval") and no list can tell — so a routine sentence before or after a
period-terminated neighbour is declined (the stated cost, specs/0037 §8: 53.6% of `?`/`!`-delimited
chunks in real turns hold more than one sentence and those chunks contain 76.3% of sentence
positions — neither a capture-loss figure; the held-out draw captured 0 of 6 positive rows —
so extractor capture reaches a routine stated as the whole turn or separated by `?`/`!`, and
`record_procedure` remains the explicit path; a parenthetical's punctuation ends nothing); a fragment lifted from inside "Imagine I
always review invoices" or after "e.g." is refused, and so are two sentences; the
summary meets `record_procedure`'s contract (normalised, at most 512 characters); the span opens
with the user asserting a current, repeated performance of their own — present simple, present
perfect continuous, or present progressive with a frequency marker, with an action verb at the
head (not a modal, an auxiliary, a cognitive/volitional verb such as "thinking of", or a
directive such as "request"), is one sentence, is not addressed to anyone in the second person, carries
no report, rejection, aspect, norm, request, aspiration, one-time or past marker, and has no
quotation frame to its left; every form not enumerated is refused; and the
stored summary IS the span, whitespace-normalised and nothing else — the extractor's own summary
for a procedural triple is discarded, so it cannot misdescribe the span, and no transformation is
applied that could change what the sentence asserts. Any failure is counted in the result's `procedural_refused` and nothing
is written; a capture counts in `procedures`. A captured procedure's `object` IS the derived span (its
note is empty, no digest is stored; describe renders the derived text after "recorded from
something you said:") and it derives `basis="stated"`. The measured residual is stated in the
spec: a span grammar cannot tell a single ongoing project from a repeating practice.

### `describe_procedures(user_id, *, query=None, principal=None, limit=None) -> DescribeResult`

Describe the user's recorded procedures. Every visible procedural record is
in exactly one of `descriptions` / `withheld`: described when it is stamped
consistently, its relation is registered, it is active and valid now, not
quarantined, not `use_only`, its basis is declared, and its summary does not
match the frozen recognition rule for imperative step text; otherwise
withheld under the **first** failing conjunct's named outcome
(`kind_conflict`, `relation_unregistered`, `inactive`, `not_yet_valid`,
`quarantined`, `use_only`, `basis_unknown`, `executable_detail`). A record
hidden from `principal` is in neither list — indistinguishable from no
match. Each `ProcedureDescription` carries the summary, its basis and an
attribution ("recorded from something you said: …" / "a pattern you reported
observing: …"), author and dates — never the note. The `stated` sentence claims
only that the user SAID it (specs/0037 v18): an extractor-captured procedure
proves utterance in the user's own message, not endorsement or currency, and a
host-declared one reads the same way because the two are indistinguishable at
read time. `query` ORDERS `descriptions`
(relevance, then `valid_from` desc, then id) and never filters either list;
`withheld` is query-blind. `limit` defaults to `max_subgraph_edges` and must
be an int in `[1, max_subgraph_edges]`; `total_describable` counts the
population before the cut and `truncated` says whether a cut happened.
Read-only.

### `recall(user_id, query=None, *, token_budget=None, principal=None, as_of=None, policy=None, **filters) -> Recall`

Assemble grounded memory context for a query (curated wiki + per-query subgraph).

**Call it with no query for proactive mode** — a session-start briefing:
dated commitments coming due or overdue (ISO dates found in fact values),
possibly-stale facts to confirm when natural, current transient state worth a
follow-up, and recent history. Proactive surfacing is *volunteering*, so
disclosure gates it: only `MENTIONABLE` facts appear — `use_only` material and
quarantined claims are never volunteered unprompted (`Recall.unverified` is
always empty in this mode). Deterministic and LLM-free. Windows are
configurable (`proactive_deadline_window_days`, `proactive_recent_days`).

Entity matching is **token-exact, not fuzzy**: the query's tokens are matched
against subject/object tokens, so `"covetrus"` does not match a subject token
`covetruspharmacy`. Key entities by exact normalized identifiers (e.g. the
full normalized sender address) and query with those — see the multi-tenant
note in [concepts](concepts.md).

- `token_budget` — cap the rendered context at approximately this many tokens
  (heuristic: chars/4 — Veracium is tokenizer-agnostic, so treat the budget as
  approximate). Selection priority when trimming: query-matched facts, then
  unverified-claim flags (a host reasoning near a claim must see it flagged),
  then the wiki, then recent episodes; best-effort minimum of one item. `None`
  (default) = unbudgeted.

- `principal` — **scoped recall (spec 0020).** A `veracium.scope.Identity`
  naming the *recalling party*. Omitted (`None`), recall is exactly what it has
  always been. Supplied, every carrier — the rendered context and
  `edges`/`episodes`/`contested` — carries only records the scope policy admits
  to that principal: own-scope records in full, cross-scope records only if
  `cross_scope_visible` and then fenced as third-party testimony that is never
  asserted, host records with no identity shared-visible, and derivatives whose
  membership evidence is missing or mixed withheld entirely (fail-closed). The
  compiled wiki is excluded from a principal-bearing response. Requires a policy
  in `MemoryConfig` (`scope_groups`); a principal with no policy configured, or
  with no `source_id`, is refused rather than silently served unscoped.
  **This is isolation between honest cooperating agents — context bleed,
  confused deputy, cross-agent leakage — not a security boundary**: the identity
  pair is namespacing, not authentication, so a caller that forges an identity
  is out of the model (see `docs/concepts.md`).
- `**filters` — narrow the result *within what is already visible*: the closed
  field set `subject`, `relation`, `author_of_evidence`, `source_id`,
  `volatility`, equality only, at most one term per field. Unknown fields raise.
  Filters select, never strip — the narrowest result still renders full
  disclosure.

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


**A host policy and its receipt (spec 0027 §4g).** `policy=PolicyLane(policy_id, policy_version,
ranks, tags_matched=())` applies one versioned, host-supplied ranking policy to this call. `policy_id`,
`policy_version` and each tag are identifiers (letters, digits and `._:-`, 1–64 characters, no
whitespace; at most 64 tags), refused otherwise — the receipt stores them verbatim, so their shape is
bounded; it is not content-free. Bounded to WHAT: letters, digits and `._:-` is the alphabet of
structured identifiers, which is the alphabet of most structured personal data — `ssn:123-45-6789`,
`dob:1974-03-02`, `dx:C50.9`, `phone:555-123-4567` all pass and are persisted verbatim in the
receipt. The rule the alphabet cannot enforce, stated in words: **a policy tag names a policy, not a
subject.** Redaction reach over the receipt is specs/0041's. `max_displaced` (spec 0027 §4h) declares the most
records the lane may displace from the returned selection — an int ≥ 0, `None` for no cap, `0` for
"reorder but never change membership"; on a breach the call returns the selection it would have
returned with no policy, and the receipt records `budget_breached=True` with `displaced` still naming
what the lane would have displaced. Every receipt carries `max_displaced_declared` (`None` when no cap
was declared). The cap's value is yours; the library enforces it and does not choose it. `ranks`
maps edge ids to ranks (≥ 1) and feeds a third fusion lane that can reorder what is returned and
can never decide what is protected (the reserve), what is a member, or what counts as covered.
When the lane fires — a rank lands on a candidate the lexical or semantic lane holds — the result
carries `policy_receipt: PolicyReceipt`: `baseline_order` (what this call would have returned with
no policy), `adjusted_order` (what it returned), `displaced` and `admitted` (the difference within
the returned length), `delta_fused` per ranked edge (at most 1/61 per lane), `budget_state`
(candidates, the cap, whether it truncated, the coverage share), the reserved ids under both
orders with `reserve_unchanged`, the policy's identity and tags, a minted `recall_id` to join
to your own logs, and `recorded_at`. Ids only: never content, never the query or a digest of it. The receipt is written on
the non-semantic path too (`semantic=False`), where `recalled_edges` is empty. An inert policy (no
rank on a held id) leaves `policy_receipt` as `None`; `policy` cannot be combined with `as_of`. The
receipt is DURABLE (schema v14): before `recall` returns, the receipt is written to the store as a
row keyed by its `recall_id`, and `memory.policy_receipts(user_id, limit=None)` (newest first) or
`memory.policy_receipt(user_id, recall_id)` reads it back field-equal to what `recall` returned (the
`recall_id` lives on `Recall.policy_receipt`, not on `Recall` itself). A store whose `policy_receipt`
table has been dropped refuses to open (the table is required by the schema manifest). A
receipt write that fails raises out of `recall` — the answer is not returned as if its trace
existed. Receipts are not part of `export_memory` (they are deployment audit, not memory) and
`forget_user` erases them with the user. Read the receipts before judging the policy, because
`displaced` is the measurement.

### `answer(user_id, query, *, principal=None, **filters) -> str`

Recall + the abstention gate → a direct answer that only uses grounded memory,
never asserts unverified claims, and abstains rather than guessing. Use this when
you want Veracium to answer; use `recall()` when you want to answer yourself.

`principal` and `filters` are threaded into the internal recall — the same
boundary as `recall()`, with no bypass. A scoped answer of "no record" is
isolation working, not abstention failing.

### `maintain(user_id, *, consolidate=True) -> dict`

The "overnight" job: expire stale facts (transient lapse, durable flag) and
consolidate cold episodes. Idempotent; call on a schedule.

**Consolidation runs PER SCOPE (spec 0021).** Cold candidates are partitioned
by their resolved source identity (`provenance.origin` + `source_id`, spec
0006) and each pool consolidates as its own operation — its own claim, lease
and crash-safety. Two consequences worth planning for:

- **Thresholds are per pool.** Four records from source A plus four from
  source B with `consolidate_min_batch=8` is a **no-op**. There is no global
  trigger to fall back on. If your store carries identities and consolidation
  seems to have stopped, this is usually why — lower `consolidate_min_batch`
  or accept the longer accumulation.
- **This happens with or without a scope policy.** Partitioning is a
  *maintenance* rule, not a *visibility* rule: `scope_groups` governs what a
  principal can read, and nothing a host configures changes what the store
  merges. A store that carries identities gets partitioned consolidation even
  if no host ever configures scope. **A store with no identities behaves
  exactly as before** — same stored state, same counter values.

The return value is an **additive superset** of the old shape. The existing
keys are preserved verbatim as roll-up totals, so anything reading them keeps
working:

```python
{"expiry": {...},
 "consolidation": {
     "consolidated": 16, "into": 5, "recovered": 0,      # unchanged keys
     "pools": {
        "<64-hex identity digest>": {"status": "ok",
                                     "consolidated": 8, "into": 3},
        "pool:unidentified":        {"status": "below-threshold",
                                     "consolidated": 0, "into": 0}},
     "pools_ok": 1, "pools_failed": 0}}
```

`status` is one of `ok` / `failed` / `contended` / `below-threshold`. A failed
pool carries `"error"`, a **closed content-free code** (`llm-error`,
`store-error`, `claim-contention`, `validation-error`, `timeout`) — never the
exception text, because a model's exception routinely quotes the prompt back
and the prompt carries memory content. **Pools fail independently:** one
pool's model error leaves every pool that already committed standing, and
later pools still run. Records with no identity share one pool under the
reserved key `pool:unidentified`.

**Records that fail closed.** A derivative whose membership evidence is
missing or contradictory — a consolidation output written before 0021 (which
copied its first input's identity), one that arrived by import (the
attribution ledger is local and does not travel), or one an interrupted
operation finalized afterwards — is **UNRESOLVED**: it joins no pool, and it
is invisible to principal-bearing reads while staying visible on the unscoped
surface. That is deliberate and it is the fail-closed price. The operator
remedy is **re-derivation** — restate or re-ingest the underlying material so
a fresh derivative is written with honest evidence. There is no flag to
believe an unverifiable claim.

**Maintenance effects are permanent.** Consolidation deletes its inputs and
writes derivatives; disabling scope configuration later changes read
visibility only. There is no un-consolidate.

### `list_entities() -> list[dict]` / `edges_since(user_id, since) -> list[Edge]`

Host/admin queries (neither is an MCP tool by design):

- **`list_entities`** — distinct ids with memory, with edge/episode counts:
  `[{"user_id": "vendor:acme", "edges": 12, "episodes": 4}, ...]`. For deciding
  what to recall proactively or auditing coverage.
- **`edges_since`** — edges *learned* after a date (`"2026-07-01"` or a
  datetime): filters on `provenance.observed_at` (when Veracium recorded it),
  not `valid_from` (when it became true). Includes superseded and quarantined
  edges so change-detection sees everything — filter on `.active`/`.assertable`.

### `introspect(user_id, *, mode="summary") -> dict`

The formatted transparency view — "what do you know about me, and where did
it come from?" — for hosts showing users their own memory. LLM-free and
store-only. `"summary"` returns counts: facts and unverified claims, an
`ungrounded` count (spec 0019 — records whose extraction was not grounded
in their source text; each renders with an inline `[possible extraction
error]` marker), by relation / evidence author / disclosure tier, lifecycle
state (`needs_confirmation`, `in_use`), retired history by reason
(superseded / disputed / absorbed), episode counts, first/last observed. `"categories"`
adds the facts themselves grouped by relation, rendered with the same
provenance markers recall uses (so an unverified claim is flagged here
exactly as the model would see it). The complete raw dump remains
`export_memory()`; erasure remains `forget()`. CLI:
`veracium introspect --user X [--categories] [--json]`. When the `Memory`'s
llm is a registered `Metered` wrapper (specs/0017), the result also carries
`"llm_usage"` — per-role calls and token counts for this user, scope
`"instance-lifetime"`, local and consent-independent, erased by `forget()`.

### A fact's biography (`veracium why`)

`veracium why --user X <edge-id>` prints everything the store recorded about
one fact, read-only and without a provider: the row with its provenance
(evidence author, disclosure tier, confidence, evidence ref, source identity
and whether a standing revocation covers it, the store's three-valued
source-restriction verdict), its lineage both ways (`supersedes` and
`superseded by`, each with the reason the retired side carries), what was
absorbed into it and what it was absorbed into (the 0014 contribution ledger),
supersessions refused with it on either side, then a timeline: every
transaction-time journal event (0029: created / mutated / invalidated /
reinstated, with the invalidation's reason, the reinstatement's (0029 v12:
`source_restored` for a lifted source revocation; an event written before v12
carries none and reads as `source_restored`) and, for a mutation, the fields
that moved), every confirmation (who, when, by which call path), every
outcome judgment (0009). `--json` returns the same as one document.
`veracium why --user X --find TEXT` lists the edges whose subject, relation or
object contains TEXT, with their ids and state, since no other verb prints
ids (`export` does). Exit 0 when found, 1 when not, 2 on usage. One limit of the history it shows, stated once: the journal lives in the same
file as the rows it describes, with no hash chain or signature, so veracium
detects inconsistency, faults and changes made outside its own interfaces, but
not changes made by the party who operates the store, who can alter both the
records and the journal; independent witnessing is not part of v1. Three reads
(`current_state`, the outcome episodes, the revocation standing) run after
the snapshot window closes and may be one write newer than the rest; the
module says so.

### An ingest dry run (`veracium remember --dry-run`)

`veracium remember --user X "text" --dry-run [--json]` reports what the ingest
WOULD write, without writing it: the real ingest runs against a snapshot copy
of the store in a private temporary directory, with a diagnostics reporter on a
temporary log, and the report is the delta — every fact that would be written
with its evidence author, disclosure tier, `quarantined` / `ungrounded` /
`needs_confirmation` flags, agreement record and the fact it supersedes; every
existing fact that would move (retired with its reason, or its liveness
advanced); the ingest's counters verbatim (`facts`, `quarantined`,
`supersessions`, `reinforcements`, `within_episode_contested`, `subject_refused`, `speaker_restricted`, `quarantined_at_birth`,
`agreement_floored`, … and `extraction_unusable`); the episode that would be
filed; and every degrade record (specs/0039) the run emitted. Because the
shipped ingest ran, the report cannot disagree with what the real write does
to the same store with the same answer. The provider IS called (a dry run of
an extraction is an extraction). The original file is never opened and is
byte-identical afterwards; the copy is deleted. Exit 0 when the extraction was
usable, 1 when it was unparseable or unusable.

### A read-only store linter (`veracium doctor`)

`veracium doctor --db X [--user U] [--json]` lints a store file without a
provider and without changing it. It copies the file into a private temporary
directory and opens the COPY through the store's own constructor (specs/0031
§4b-ii permits no second file-backed opener), so the original is never opened
and the constructor's typed refusals — below head, above head, unstamped or
foreign shape, not a database — become the first findings. On a store the
constructor accepts it runs SQLite's `quick_check`, then reports: the
`store_identity` singleton and `store_epoch`; every `edges`/`episodes` payload
parsing with `id`/`user_id` equal to the row columns, the `active` column
agreeing with `invalidated_at`, `quarantined` agreeing with the payload's
disclosure, retired edges carrying a dispositioned reason; dangling
`supersedes` links, supersession cycles, an active successor over an active
predecessor; outcome episodes, confirmations, ledger survivors and typed
contributors, embeddings and journal events naming rows that exist; edges
with no journal event (specs/0029); every third-party-AUTHORED fact or
episode carrying a `source_id` (specs/0006), since one without it has no
source identity and cannot be revoked by source — content merely derived from
a third party is not checked, because the stored payload cannot tell a declared
derivation from the default every undeclared ingest receives; the procedural
tripwire — numbers never merged: `procedural_declared` (procedural records
whose producer stamp is `host`), `procedural_captured` (producer `extractor`),
`procedural_unstamped` (procedural records with no producer stamp — the
producer is unknown: written before the stamp existed, restored from an older
export or from an envelope below format 12 where the field is stripped at
import, or written through a path other than `Memory`; specs/0037 v24.1 —
the count says the producer is unknown, not why, and declared and captured
cannot be told apart there) and `procedural_shaped`
(declarative records whose `note` matches research's census marker screen, a
screen result and never a count of procedures; notes only, never `summary`;
informational, it cannot fail the build) — there to notice an extractor that starts producing procedure-shaped
notes or hosts feeding procedures down the declarative path; and, for every
standing revocation (specs/0022), the reference sweep run over the store as it
is with no proposed action — a pending effect means the revocation is not
applied. Rebuildable
index drift is not observable this way: the constructor repairs it on the copy
at open (specs/0007). Exit 0 clean, 1 findings, 2 unreadable. It repairs
nothing; `veracium migrate` is the version path.

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
  **Retries (specs/0008 §6c, §6g).** Pass a `correlation_id` to make a retry
  safe. The same id with the same request returns the original result
  (`replayed=True`), even after the fact was invalidated. The same id with a
  different request, or an id already held by another verb, raises
  `ValueError`. Once the fact is redacted, a retry under its id raises
  `veracium.store.base.RequestRedacted` (a `ValueError`) whatever the
  payload: it is terminal and never replays. `forget_user` frees the user's
  ids.
  **A fact whose source was erased (specs/0045 §4d).** `confirm` refuses a
  `not_attested` fact (below) whose source episode was redacted, with
  `ValueError` ("state it anew"): the user's confirmation would otherwise
  promote a suggestion whose evidence they removed. It reads the source's
  redaction directly, and also through a consolidated episode whose lineage
  holds the source (the source episode is deleted at consolidation). It does
  not refuse an `attested` fact, a fact with no recorded source, a fact
  already confirmed in this store, or a fact written before this release. A
  source deleted outright (not redacted) leaves nothing to read, so confirm
  is allowed. A pending redaction notice does not refuse; an applied one does.
  **A fact the subject challenges (specs/0047 §4c).** `confirm` refuses a fact
  with an open `challenge` reply (below), with `ValueError`, until the subject
  resolves it. A retry of a confirmation completed before the challenge still
  replays.

Neither verb is exposed over MCP (an agent-callable suppress/validate verb is a
prompt-injection target) — wire them to real user actions in your host. Note
`correct` and `elaborate` need no verb: they *are* `remember()` (supersession /
accumulation).

### `reply(user_id, edge_id, *, kind, text=None, target=None, actor="user", correlation_id=None) -> dict` (specs/0047)

The subject's right of reply: a person answers a remembered fact about them,
and the answer is kept with the fact. Host API only — no MCP tool reaches it.

- **`kind`** is one of `"challenge"` ("that's wrong"), `"context"`,
  `"withdrawn-consent"`, or `"resolve"`. A `resolve` withdraws ONE challenge of
  the same fact, named by its reply id in `target`, and carries no `text`;
  every other kind carries non-empty `text` and no `target`. Only a `resolve`
  ends a challenge: `context` text never does, whatever it says.
- **The fact is never changed.** A reply does not retire, supersede, edit or
  delete it, and is never ingested as evidence. Replies are append-only.
- **`actor`** is `"user"` or `"host"` (acting on the user's behalf) — a label
  the store enforces but cannot authenticate. A `resolve` needs the same user
  and the same fact as its challenge; its actor may differ, and each row
  records its own.
- **What it changes now.** While a challenge is open, `confirm()` refuses the
  fact. A fact carrying a reply or a confirmation is never absorbed into a
  later, more specific restatement: both records stay. Redacting the fact
  replaces every reply's text and request digest with the marker.
  `forget_user` erases the user's replies (`"replies"` in its return).
  `veracium doctor` reports a reply naming a fact that does not exist for its
  user.
- **While a challenge is open, the fact is not asserted anywhere.** Recall,
  its contested block, proactive recall, as-of recall and the compiled wiki
  all withhold it, whatever its grounding (`attested` included), and so does
  `answer()`. The same holds for any **same-value restatement** of it: an
  equal value, or one that adds or drops up to two words ("cat Miso" and
  "Miso"), under the same subject and relation, from any author. That
  includes the subject's own correction ("that's wrong, it's Acme Labs",
  then "Acme Labs" arrives): it waits too. When the subject restates the
  fact, offer them `resolve` on the challenge. A restatement of a challenged
  fact that was later redacted is no longer withheld (nothing of the
  redacted value is kept to match on).
- **The withheld line.** A rendered answer that withheld anything says so:
  `[withheld: N fact(s) the subject disputes; see the host's why()]`. N counts
  this answer's candidates (the facts retrieval found for the query), before
  the token budget, so the number does not depend on the budget; proactive
  recall counts only the facts it would have volunteered. Under a
  principal, N counts only facts in the principal's view; a challenge
  outside the view still withholds an in-view restatement, and is never
  named or quoted to that principal. The residual, accepted as 0020's N-2
  accepts its own: an in-view fact that is counted and reads
  `challenge_clear=False` with an empty `withheld_by` tells the principal
  that a record outside its view holds the same value and is disputed.
- **Where the challenge is shown.** `Recall.inspection` (a dict keyed by edge
  id, an entry for every edge in `Recall.edges`), `AsOfFact.inspection` and
  `why` carry, per fact: `grounding` (g(e)),
  `attestation_version`, `open_challenges`, `latest_challenge`, the `unit`
  `[challenged by the subject: N open; latest: …]`, `challenge_clear`, and for
  a withheld restatement `withheld_by` and `waiting_on` (the challenged facts
  and their open challenge ids). **Consumer duty:** `Recall.edges` still
  contains a challenged fact. Do not assert an edge whose entry is not
  `challenge_clear`, and show the unit wherever you show the record.
  `introspect(mode="categories")` prints the unit on a challenged fact's
  line, and `[withheld: same value as challenged <id>]` on a withheld
  restatement's. Duplicate restatements are collapsed for display only when
  the hidden one carries no confirmation or reply of its own and is not
  itself withheld, on every surface, as-of recall included.
- **Refusals** raise `veracium.store.base.ReplyRefused` (a `ValueError`) with a
  closed `reason`: `kind`, `actor`, `shape`, `marker` (the redaction marker in
  the text), `unknown-edge` (absent, or another user's), `redacted-edge`,
  `procedural-edge`, `resolve-target`, `resolve-repeat`. A reply to an
  inactive or quarantined fact is admitted.
- **Request ids.** `correlation_id` is the same per-user id space `confirm()`
  and `undo_restoration()` use: an id another verb holds is refused, naming
  it. A retry of the same request returns the recorded reply with
  `replayed=True`, without reading the fact; the same id with a different
  request raises `ValueError`; after the fact's redaction a retry raises
  `RequestRedacted`. The request is `(user, fact, kind, target, text)`: the
  actor is not part of it, so a retry under another actor label replays
  (`confirm()`'s request includes its actor). Omitted, an id is generated,
  takes a registry row and is returned.

```python
c = mem.reply("u1", edge_id, kind="challenge", text="I never lived there")
# {"reply_id": "r-...", "edge_id": "...", "kind": "challenge", "target": None, "written_at": "...",
#  "correlation_id": "auto-...", "replayed": False}
mem.reply("u1", edge_id, kind="resolve", target=c["reply_id"])
```

### How a fact is known: `att`, `src`, `attv` (specs/0045)

Every declarative fact ingest writes from now on carries three fields, set once
and never changed (a same-id rewrite of any of them raises `ValueError`):

- **`att`** — `"attested"` when a fixed, versioned predicate found the fact
  stated in the user's own words in the event, in the one sentence form it
  recognises; otherwise `"not_attested"`. The predicate is ATTEST-6
  (specs/0051): ATTEST-3 over the event text and, when the event labels a turn
  for an assistant ("Assistant:", "AI:", "ChatGPT said:", …), ATTEST-3 again
  over the user's turns alone — both must find it, so a sentence only the
  assistant said is never attested. `"not_attested"` means only
  that the predicate did not find it: most true statements are phrased in ways
  it does not recognise (ATTEST-3 recognised 12 of 53 on its blind holdout,
  with 1 false attestation in 67; on 0051's blind holdout of pasted
  two-speaker transcripts ATTEST-5 attested 9 of 58, with 3 false
  attestations in 72 where ATTEST-3 had 7; ATTEST-6 answers every item of that
  holdout as ATTEST-5 does). It is **not** "unverified" — the fact is stored,
  recalled and asserted exactly as before. `"attested"` is a label, not proof,
  and carries no other privilege. Only a declared-direct USER event
  (`context=EvidenceContext.direct()`) can be attested; every other event is
  `"not_attested"`. Separately (specs/0051), in such an event a fact whose
  value appears only in a turn labelled for an assistant is stored `use_only`
  (not asserted) and counted in `remember()`'s `speaker_restricted`. Not
  covered: unlabelled transcripts, an episode's wording, sample dialogue inside
  an assistant's reply, and formats the label grammar does not recognise
  (role-play personas, API role brackets). The other direction: in a single
  exchange where the user is named once, after the assistant ("Claude: …" then
  "Sam: …"), the user's line is restricted too.
- **`src`** — the id of the episode the event wrote, or `None` when the
  extractor returned no episode text.
- **`attv`** — what produced `att`: `"ATTEST-6@ccabb664"` (the predicate's
  version and the first 8 hex digits of its source file's sha256;
  `"ATTEST-3@b1329a81"` or `"ATTEST-5@0bb7779f"` on facts a development build
  wrote earlier),
  `"non-user-effective"` (no predicate ran), or `"default-import"`.

A fact written before this release has none of them and reads as `unknown`;
nothing re-derives it. A procedural record (`record_procedure`, the quote gate)
carries none. A fact written by `correct()` carries none for now (`unknown`).
`veracium.attestation.declarative_grounding(edge, confirmation_origins)` gives
the derived value: `confirmed` once a local or restored confirmation exists,
else the stored `att`, else `unknown`.

**Where they appear.** On `Recall.edges` and `why`'s edge record, as fields of
the edge (a principal's scoped view keeps them, `src` included), and as the
derived `grounding` and `attestation_version` in `Recall.inspection`,
`AsOfFact.inspection` and `why`, which prints them with `att` and `src`. They
are not in an export yet: an export file omits them, a default
import writes `not_attested` / `None` / `default-import` on every declarative
fact whatever the file says, and `--restore` leaves them unset (`unknown`)
until the export format carries them.

### `record_outcome(user_id, edge_id, *, outcome, evidence_ref, actor="system", corrected_value=None, date=None, context_ref=None) -> dict` / `correct(user_id, edge_id, corrected_value, *, actor="user", evidence_ref=None, date=None) -> dict`

Outcome tracking — *did conclusions built on memory survive contact with
reality?* Engine-written surfaces (never MCP tools):

**A procedural record is not corrected** (specs/0037 v19): `correct()` on an edge that
carries the procedural stamp refuses with `ProcedureValueError` (`correction_of_procedure`)
and writes nothing — a correction's successor would carry the host's text under the user's
`stated` basis. Retire the record and restate the procedure through `record_procedure`, or
let the user state it again. The store also refuses any successor of a procedural record
that would drop the procedural markers, on every path.

- **`record_outcome`** judges a **use** of a fact. Outcomes:
  `unreviewed` (used, no judgment — the default; most stay here) ·
  `confirmed`/`corrected` (human, `actor="user"`) ·
  `challenged`/`concurred` (LLM judge, `actor="system"` — flags, never truth).
  Each use is a `kind="outcome"` episode (the source of truth), and the edge
  carries derived counters (`times_used`, `outcome_counts`, `last_outcome`).
  A later judgment with the same (`edge_id`, `evidence_ref`) **upgrades the
  use in place** — no double counting. **Edge-blind by design**: one run's
  `evidence_ref` may touch every fact it consulted, so `record_outcome` never
  supersedes a fact — `corrected` here records the *decision's* true value
  only. The invariant, stated precisely: **a fact's gate placement is
  unchanged by use-level outcomes** (a `use_only` fact stays `use_only`, a
  grounded fact stays grounded — "assertable" is not the invariant, since
  third-party-derived facts were never assertable to begin with).
  `challenged` sets the possibly-stale flag; counters render into recall
  as information ("(in use: 5×, 2 confirmed)") — never as gating.
  A judgment arriving *after* fact-level correction is accepted and recorded
  on the superseded edge — the episode stream keeps late judgments — but
  superseded facts don't render in recall context at all (deliberate: history
  stays compact), so late-judgment counters are invisible at recall and
  queryable via `Recall.edges` / the outcome episodes.
- **`correct`** is the explicit **fact-level** correction: the remembered value
  itself was wrong. Supersedes with `invalidation_reason="corrected"`
  (distinguishable at recall from natural change) and records the corrected
  value as a new user-authored edge. Since specs/0011 (E5) the correction
  commits through the atomic supersession plan with a
  `CorrectionAuthorisation` verified inside the transaction — an integrity
  binding (forge/replay/rebind/cross-principal all abort, nothing written),
  **not** authentication: `actor` is a caller-supplied principal, so
  `correct()` is a **protected host API** — authenticate the principal and
  establish intent before calling, and never expose it where a model can
  choose the principal. Correcting a fact about another entity on bare
  self-assertion raises `graph.CorrectionRefused` after a durable refusal
  row commits (the §4b subject rule applies to corrections).

### `forget(user_id) -> dict`

**Compliance erasure** — irreversibly removes everything stored for the user:
all edges (superseded history and quarantined claims included), all episodes,
the wiki cache, and counters. The data-subject right, deliberately distinct
from lifecycle: `maintain()` never deletes, `forget()` never preserves. No
undo — `export_memory` first if a recoverable copy is wanted. Also on the CLI
with a confirmation prompt: `veracium forget --user alice`. **Deliberately not
an MCP tool** — an irreversible-wipe verb callable by an agent is a standing
prompt-injection target; erasure is a host/operator action.

### `export_memory(user_id, path) -> dict` / `import_memory(path, *, user_id=None, restore=False) -> dict`

Portable memory: one JSONL file per user carrying the **complete** store of
record — every edge (superseded history and quarantined claims included) and
episode with full provenance, disclosure, and validity windows. Import is
idempotent (existing ids are skipped, never overwritten); `user_id=` remaps the
records. Also available without code: `veracium export out.jsonl --user alice`
/ `veracium import out.jsonl [--user bob | --restore]`.

**Absorption linkage (FORMAT 7, specs/0020 §4a-iii).** Exported absorbed
records carry `absorbed_by_id` — structured linkage derived from the
store's typed contribution ledger, never from notes. Imports reconstruct
absorption attribution **pre-commit** (structured-first; a decidable
legacy note rule covers pre-7 files; ambiguous or unresolvable linkage
refuses the whole import before any write) and persist the reconstructed
contribution rows atomically with the records. The returned dict gains
`"contributions"` (rows written) and `"contributions_existing"`
(idempotent re-import rows skipped as already recorded); a re-import
whose file asserts a *different* absorption history than the destination
already recorded refuses rather than silently merging.

**Restoration outcomes (FORMAT 14, specs/0044 §4l).** A store that ran
`run_data_migration` exports its restoration outcomes for the edges in the file
(`arity_outcome` lines) and, when it has a plan, one `arity_plan` line naming
its state; a store with neither exports as before. Import validates them whole
before any write: every outcome's edge must be in the file, one outcome per
edge, and an outcome already held is replayed only if it matches exactly (a
changed one refuses the whole import). A default import records them as
`imported` testimony (no undo, `doctor` warns); `--restore` of your own export
records them `restored`. The returned dict gains `"outcomes"`,
`"outcomes_existing"` and the arity decision below. See [Exporting and importing
restorations](#exporting-and-importing-restorations-format-14).

**Confirmations, replies and grounding (FORMAT 14, specs/0008 §6d–§6f, 0047 §4f, 0045 §4f).** The file carries
every confirmation and reply with its origin (`confirmation` / `reply` lines), and each edge's grounding (`att`,
`src`, `attv`) on its own line. The request registry never travels: a retry belongs to the store it was made to. A
default import records the acts as `imported` testimony (shown in `why`, never counted toward `confirmed`) and stamps
every fact `not_attested`; `--restore` of your own export keeps them as recorded, mapping `local` to `restored`. The
returned dict gains `"confirmations"`, `"replies"` (written), `"acts_existing"` (exact replays),
`"acts_refused_with_edge"` and `"axis_kept_default_import"`; the export's result gains `"confirmations"`, `"replies"`
and `"acts_orphaned"`. See [Exporting and importing confirmations and
replies](#exporting-and-importing-confirmations-and-replies-format-14).

**Trust boundary (specs/0005).** A **default** import caps every record's
trust: `author_of_evidence` and `derived_from` are set to `third_party` and
`disclosure` is floored to `use_only` (`quarantined` is never weakened) — so
nothing imported is assertable or rendered as the target user's own testimony,
whatever the file claims or omits. The returned dict carries `"capped"`, the
number of records the cap changed (a function of the file alone, never of
destination state). A host that wants an imported fact asserted confirms it —
that affirmation is new user-authored evidence.

`restore=True` (CLI `--restore`) preserves the file's trust fields exactly and
skips only the cap — it is the operator's assertion that **the file is this
store's own export**. It trusts every record exactly as written: use it only
on files you exported yourself or have independently verified, record by
record. `restore` must be a real bool and is mutually exclusive with
`user_id` (a restore never remaps).

**Redaction notices (specs/0041 §11.6.6).** A file's redaction notices are weighed in
the same transaction as its records, by the state of each notice's TARGET, by the
file's copy of the record, and by the mode — never by the notice's claimed origin.
A redaction row is `applied` (an attestation: this store redacted the record),
`pending` (another store's testimony that it redacted a record you hold, waiting for
you) or `standing` (a notice for a record you do not hold). Only `applied` counts as
redacted: a pending or standing notice is not in `redacted_targets()` and refuses
none of your writes.

- **Default import.** A notice for a record you already hold is recorded
  **pending** and every held byte is unchanged; it is listed in the result's
  `notices_not_applied` (`[kind, id, reason]`, reason `held-target`; the CLI prints
  them). A notice for a record you do not hold is **standing**. A record this
  import creates beside its notice is applied only if the file **shows** the
  redaction (carries the record already redacted); a record arriving unredacted
  beside its notice refuses the whole import. A later import that creates a
  standing notice's record must show the redaction, or it is refused; if it does,
  the notice becomes pending (`standing-arrival`).
- **`restore=True`.** A notice is applied to a held record when the file's copy —
  or, with no copy, the held record itself — shows the redaction; with no copy and
  a record that does not show it, the notice is pending (`record-not-in-file`); a
  file carrying the record unredacted beside its notice is refused. A standing
  notice's later arrival that shows the redaction is applied.

An untrusted file can therefore never change data you hold. A source's genuine
redaction of a record you already hold waits for you:

```python
for n in mem.pending_notices("alice"):      # {notice_id, target_kind, target_id, reason, origin, source_user, recorded_at}
    ...                                      # show the claimed source (unauthenticated testimony) to the user
mem.confirm_notice("alice", notice_id)       # -> RedactionReceipt: this store's own total redaction of the record
```

`confirm_notice` applies the notice exactly as `redact()` would redact the record
— every carrier, held confirmations and their registry rows included — and keeps
the notice's own body. Confirming an applied notice returns its receipt with
`repeated=True`. An unknown id and another user's id are refused with one
message; a standing notice and a notice whose record no longer exists are refused.
An export carries applied notices, and standing notices only when it does not
carry their record; a pending notice never travels, so restoring an export does
not reproduce pending state (re-importing the source file re-pends it).

### `close()`

Close the underlying store.

## `EvidenceAuthor`

`USER` · `THIRD_PARTY` · `SYSTEM`. See [concepts](concepts.md).

## `MemoryConfig`

| field | default | meaning |
|---|---|---|
| `db_path` | `"veracium.db"` | SQLite file path (default store). |
| `relations` | built-in registry (`DEFAULT_RELATIONS`) | edge vocabulary; add your own `Relation(name=..., arity="single" | "multi")` (`functional=` is the older spelling of `single`/`multi`; `keyed` is reserved and refused). **Replaces, does not merge:** passing your own dict drops every built-in content relation you did not copy (`prefers`, `works_as`, `located_at`, ...), so start from `{**DEFAULT_RELATIONS, **custom}` to keep them. The reserved pair is force-included whatever you pass: `third_party_claim` (the quarantine relation) and `unclassified` are always in the effective registry and the extractor's prompt. See [recipes](recipes.md#add-your-own-relations-the-registry-is-host-extensible). |
| `max_subgraph_edges` | `40` | cap on per-query subgraph size (bounds read cost). |
| `subgraph_coverage_share` | `0.0` | fraction of the subgraph budget reserved for time coverage rather than pure relevance. **Off by default and we recommend leaving it off** — it was measured under a pre-registered protocol and did not improve retrieval of answer-bearing facts. See [design rationale](design-rationale.md#measured-and-not-adopted). |
| `max_recent_episodes` | `12` | recent episodes included in recall. |
| `wiki_recompile_after_writes` | `8` | recompile the curated wiki after this many writes. **`0` disables the wiki** → recall renders the subgraph directly (no read-time LLM call). |
| `volatility_lifetime_days` | permanent=∞, durable=730, slow=120, transient=7, ephemeral=1 | expected lifetime per volatility class. |
| `decay_factor` / `confidence_floor` | `0.5` / `0.3` | confidence decay and cutoff for DECAY facts. |
| `consolidate_after_days` | `30` | episodes older than this are consolidation candidates. |
| `consolidate_min_batch` | `8` | minimum cold episodes before consolidation runs. |
| `scope_groups` | `None` | **scoped recall (spec 0020)**: `{group_name: [veracium.scope.Identity, ...]}`, the host's read-side scope policy. `None` disables the feature (a `principal=` at recall is then refused, never silently served unscoped); `{}` is the valid configured-empty state (each principal sees its own identity plus shared records). Validated when the config and the `Memory` are built — a malformed policy raises at load, never mid-recall. Read-side only: it governs what recall *shows*, never what maintenance *merges*. |
| `cross_scope_visible` | `False` | whether records outside the principal's group are visible at all. When `True` they are visible but fenced as third-party testimony — never assertable, never volunteered proactively. |
| `census_enabled` | `False` | the exercised-guarantees census (specs/0042): **opt-in, default off**. `True` turns the process-wide switch on at construction; every enforcement point then counts how often it was consulted and how often it fired, and `veracium.census.census(declaration)` reports one of six statuses per declared id (`DISABLED` · `UNDECLARED` · `UNMEASURED` · `UNREACHED` · `UNEXERCISED` · `EXERCISED`). Observation only: a site never alters a decision, and a report carries ids and integers, never content. Off, every site is a no-op and the report reads `DISABLED` per id. |
| `contested_render_share` | `0.5` | the CONTESTED FUNCTIONAL FACTS block's share of the recall budget. Before this cap the block had first claim on the whole budget and could starve the ranked detail lines that carry an answer; the first group line is still unconditional (the higher-authority prior is never dropped) and the rest of the budget goes to detail. `1.0` reproduces the pre-cap behaviour. It cannot reach carriers inside a contested group, which are removed from detail by construction. When the block is cut, it is cut from the END of an order that keeps the most-preserved groups: groups (in the block and in `Recall.contested`) are listed by the authority of the fact each preserves, then the closest contention first, then the most visible members, then `(subject, relation)` (specs/0003 §4c-iii). |

- **`require_source_id`** (`True`; specs/0006 §4 rule 9): when `True` (the default), `remember`
  refuses, before any write, third-party-authored evidence and declared third-party-
  derived content that carries no `source_id` — a record without one has no source
  identity and no revocation can ever reach it. Raises `veracium.ingest.SourceIdRequired`;
  the MCP tool returns `{"ok": false, "refusal": "source_id_required"}`. An ingest with
  no declared context (the 0011 floor) is never refused. Supply the id as
  `remember(..., source_id=)`, the CLI's `--source-id`, or the MCP deployment's host-set
  `VERACIUM_MCP_SOURCE_ID`. On by default since 0006 v8; set it `False` to restore the
  earlier accept-anything behaviour. Existing unsourced rows are untouched either way
  (no ids are invented — 0006 I1); `veracium doctor` names them.

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

`AnthropicComplete` never returns an empty string: when the model produces no text block
(the default `max_tokens=4096` spent inside a `thinking` block, a refusal, an `end_turn` with
nothing said) it raises `veracium.llm.anthropic.EmptyCompletion`, a `RuntimeError` whose message
names the stop reason, the output tokens and the block types seen, and whose fields carry them.
An empty completion is never a result — an empty gate answer would read as an abstention. Raise
`max_tokens` when the error says the budget was spent before any text.

Wrapping your agent's existing client is often simplest — see
`examples/claude_cli_provider.py` for a subprocess-based example, or
`examples/openai_provider.py` for an OpenAI-compatible one (OpenAI, vLLM,
Ollama's `/v1` endpoint). It attempts `json_schema` as structured output and
falls back to a plain call — no error — if the endpoint doesn't support it.

## Providing a store

The default `SqliteStore` is embedded and zero-dependency. To back memory with
Neo4j/Postgres, implement `veracium.store.base.Store` (all methods are per-`user_id`)
and pass it as `store=`.

**The store is an interface a host IMPLEMENTS, not a write API a host CALLS**
(specs/0006 v10, specs/0037 v23; the owner's ruling, 2026-09-14). `Memory` is
the write API: `remember`, `record_procedure`, `correct`, `retire`, the import
boundary. Every guarantee this documentation makes about a record — that a
third-party record carries a `source_id` when `require_source_id` is on, that a
procedural record was declared by the host or captured behind the verbatim-quote
gate, that its stamps were minted by the product — holds for records written
THROUGH `Memory`. `memory.store` is reachable and `Store.add_edge` is public
because a host implementing a store needs both; a record a host writes by
calling `add_edge` directly carries exactly what that host minted, and nothing
in the store re-derives or checks the `Memory`-level facts about it. A store used
with a policy lane must implement `write_policy_receipt`, `policy_receipts` and
`policy_receipt` (schema v14): the base class refuses rather than drops, so the
first recall on which a lane fires raises `NotImplementedError` against a store
that lacks them. The store's own rules still hold there (a stored stamp, basis or producer never changes on a
same-id replace; a successor of a procedural record stays procedural, with the
same producer). Provenance is a frozen model: a stamp cannot be flipped on a
built record, only minted at construction. The `doctor` sees an unsourced
third-party record through its `sources` check; a procedural record hand-minted
at `add_edge` renders like a declared one — that is the stated limit, and the
reason to write through `Memory`.

A second stated limit, beside the first because both are about what the store
can and cannot vouch for: **Veracium does not witness its own history.** The
`edge_event` journal lives in the same SQLite file as the rows it describes,
with no hash chain, no `prev_digest` and no signature, and `forget_user` erases
it with the user's rows; it is a history, not a tamper-evident record. Veracium
detects inconsistency, faults and changes made outside its own interfaces, but
not changes made by the party who operates the store, who can alter both the
records and the journal. Independent witnessing is not part of v1 (specs/0036,
the owner's ruling of 2026-09-12). A deployment that needs tamper evidence keeps
its own witness outside the file Veracium writes.

## Migrating a store (`veracium migrate`)

Release migrations are **offline** and operator-driven (specs/0013 §5b,
specs/0018): quiesce every other process using the store, take a backup, then

```
veracium migrate --db PATH --i-have-quiesced --backup REF
```

Both flags are required on the migration path — they are the operator's
explicit assertions (never prompted for): `--i-have-quiesced` states that all
other access is stopped; `--backup REF` names the pre-migration backup this
operation made (a token: 1–128 ASCII characters, no whitespace).

**Two migration paths exist, and they accept different stores.** Measured
2026-09-18 by running both on a store stamped at each base (the table is in the
0.26.1 erratum in the changelog), and again on 2026-10-24 for this release's
v14 → v16 step on a store built by the published 0.26.1:

- **`veracium migrate` (the specs/0018 orchestrator, also
  `run_release_migration`) migrates a store at the PREVIOUS schema version
  only** — on this release, v15 → v16. Any older stamped base (v1–v14)
  is refused with the closed outcome `unsupported-base` and nothing is
  touched. This is the accepted 0018 contract (the preflight passes only
  `HEAD-1` to minting). **No release shipped v15** (it existed only on
  `main` between 0.26.1 and 0.27.0), so on 0.27.0 the CLI refuses EVERY
  store a released version created, 0.26.1's v14 included — use the library
  call below. The refusal's diagnostic names the resolved base, the number
  of one-version rungs a CLI ladder would need and which of them the shipped
  release record names no release for, and the library route below.
  (0.26.1's diagnostic reported every base 7–12 as "v6" with advice from
  head v8; fixed after 0.26.1.)
- **`veracium.store.migration.migrate_store(path)` walks every stamped base
  from v1 through v15, and an unstamped legacy v1 store resolved by shape,
  to the current schema in ONE call** — the additive object diff plus each
  data step the crossed versions declare (v3's outcome-chain roots, v5's
  store identity, v6's ALTER path, v8's ledger, v10's operations column,
  v13's journal baseline, v16's request-registry backfill — one `confirm`
  row per existing confirmation — and its arity inventory). What it does NOT produce: the orchestrator's
  host attestation, its structured result over the 0018 outcome table, and
  its terminal audit record. Pass `audit_sink=` if you want the attempted
  and committed events recorded; with no sink the migration is logged and
  no durability is claimed.

**The path for a consumer upgrading from any released version, 0.26.1
included** (a store at v1–v14; a 0.13.0 host reached 0.26.1 this way on
2026-09-18, 9 → 14, counts byte-preserved; a store built by the published
0.26.1 reached v16 this way on 2026-10-24, every pre-existing row byte-equal
and a confirmation's retry replaying): quiesce every other process, take a
backup, then run the library call once, offline —

```python
from veracium.store.migration import migrate_store
str(migrate_store("veracium.db"))      # "migrated" (or "current" if already there)
```

— and reopen normally. The CLI path is for the one-version step a routine
upgrade makes; it will refuse the far-behind store with `unsupported-base`
rather than walk the chain. Its diagnostic names the library path; opening the
store before migrating does not (it raises `PackageConsistencyError`, "no
migration hook installed"), and `veracium doctor` still suggests
`veracium migrate` for every below-head store — both are corrected in a later
release, so this paragraph names the path. A store already at the head is a no-op
(`current`) on either path; a store newer than this build refuses
(`newer`); rebuildable index drift is repaired during opening and reported
honestly as a committed change.

Exit codes: **0** migrated/current · **1** every refusal (structured outcome,
facts, and diagnostic on stdout) · **2** usage / invalid attestation ·
**3** an audit failure surfaced loudly (`MigrationAuditWriteError` /
`MigrationAuditReadError` / `PackageConsistencyError`) — exit 3 means the
audit trail needs attention, never a silent success; every state printed on
stderr is labeled `recorded`, `derived-from-outcome`, or `unavailable`.

Each migration writes a durable per-store audit trail
(`<store>.migration-audit.json`): the attempted event inside the migration
transaction and an append-once terminal record carrying the operation's
validated facts.

Library callers use the same machinery directly:

```python
from veracium.store.migration import (MigrationAttestation,
                                      run_release_migration)
result = run_release_migration(
    "veracium.db",
    host_attestation=MigrationAttestation(quiesced=True, backup_ref="b-2026"))
result.outcome              # "migrated" | "current" | a closed refusal
result.resulting_version    # facts, never inferred from the label
```

## Restoring values the old single-value rule retired (`run_data_migration`)

*Upgrading to this version does not restore values that the old single-value rule retired. To restore them and get a
receipt listing each one, run `run_data_migration`. Until you do, those values stay hidden and `doctor` warns.*

`measures`, `prefers` and `health_state` no longer supersede incomparable values (`arity="multi"`, specs/0044). Under the old rule a new
value of one of them retired the previous one as `superseded`. The v16 schema step records exactly those retirements
(the store's arity inventory) and changes nothing else. Bringing them back is a separate, OPTIONAL host operation
(specs/0018 §4i). It is a bulk restoration of a known superset: a value that really was replaced comes back too, and
the receipt names what replaced it. So it asks for the same quiescence attestation and backup reference as a release
migration. No CLI verb runs it.

```python
from veracium.schema import DEFAULT_RELATIONS
from veracium.store.migration import (MigrationAttestation, data_migration_receipt,
                                      data_migration_status, run_data_migration)
att = MigrationAttestation(quiesced=True, backup_ref="b-2026")
r = run_data_migration("veracium.db", host_attestation=att, registry=YOUR_REGISTRY, op_id="restore-2026-10")
r.outcome        # a row of the closed table below
r.committed      # the users THIS call committed;  r.failed: each failing user, named
r.plan_id        # the store's plan, for the receipt
data_migration_receipt("veracium.db", r.plan_id, "user-1")   # one row per considered value
data_migration_status("veracium.db", "restore-2026-10")      # after an unknown return: cumulative commits
```

- **`registry`** is the relation registry your host passes to ingest. A relation is restored only if your
  declaration of it is the default `multi`. A host that keeps its own `single` declaration for one of the three
  keeps its supersessions. The plan is written once per store from the first call's registry. A later call whose
  declarations of those three differ returns `registry-changed` and changes nothing. A change to any other relation
  is admitted.
- **`op_id`** is your idempotency key (≤64 characters of `[A-Za-z0-9._:-]`). The same id with the same inputs
  RESUMES: it retries exactly the users that did not commit. The same id with different inputs, or in the other mode,
  is `op-id-conflict`. A call that wrote nothing holds no id.
- **One transaction per user**, continuing past a failing user. The users are those holding a recorded retirement.
  A user created after the upgrade has nothing to restore and is never processed.
- **A value from a source under standing revocation is withheld** (`withheld_revoked`), judged by the revocation
  sweep's own rule. It is never considered again under this plan, even after a lift. A redacted value is never
  considered.
- Each restored value is journaled `reinstated` with the reason `arity_reclassified`. The receipt reads its text from
  the live edge (a redacted one shows the marker) and records what it replaced: one id, several ids, or "unknown".
- `plan_only=True` writes the plan and restores nothing. It must be exactly `True` or `False`: any other value
  (`1`, `"yes"`, `None`) raises `ValueError` before anything is read, as an `op_id` outside the grammar does. A
  caller error is not one of the table's outcomes.

| outcome | store changed | meaning |
|---|---|---|
| `requires-schema-step` | no | the store is below v16 |
| `preflight-refused` | no | the attestation, path, store or registry was refused; the diagnostic names 0018's cell |
| `registry-changed` | no | a plan exists under different declarations of the three; both digests named |
| `op-id-conflict` | no | the op_id is held with different inputs or mode |
| `planned` | yes | this call wrote the plan and restored nothing (plan-only, or no user to process) |
| `already-planned` | no | plan-only, and an equal plan existed |
| `complete` | no | every user already done |
| `migrated` | yes | ≥1 user committed, none failed |
| `partial` | yes | ≥1 committed, ≥1 failed (named); re-call to retry them |
| `failed` | only if it wrote the plan | no user committed, ≥1 failed |

Two cases are this implementation's choice where the specification's table is silent. A v16 store with rebuildable
index drift is refused (`preflight-refused`, "rebuildable drift: open the store once … and re-run") rather than
repaired silently, so `store_changed` stays exact. A write lock that cannot be taken raises the store's typed lock
refusal (`sqlite3.OperationalError`, naming the site) with nothing written; a lock failure inside one user's
transaction is instead that user's `failed` entry. Any other defect outside a user's transaction raises: the table
has no internal-error row.

`doctor`'s `data-migration` check reports the operation's phase: a warning before any plan (judged by relation name
only, as it says), a warning naming the users not yet done, an `info` for an empty plan, and nothing once every user
is done.

### Exporting and importing restorations (format 14)

A value the old single-value rule retired may arrive in an import file from a store that never decided about its
restoration. The file says whether its store decided: it carries an `arity_plan` line when the exporting store has a
plan (a file without one, including any file from before this release, is read as "had not decided"). For each retired
`superseded` row under `measures`, `prefers` or `health_state` (when your registry treats the relation as multi-valued)
that this store does not already hold and that carries no restoration outcome:

| the file's store | this store | result |
|---|---|---|
| had not decided | no plan | **refused**: run `run_data_migration(path, ..., plan_only=True)` first (it writes the plan and restores nothing), then import again |
| had not decided | a plan with these relations | **converted** in the import: restored (or withheld, by the same revocation rule) with a `local` outcome; the result's `"arity_conversion"` is `"converted"`, with `"arity_restored"` / `"arity_withheld"` |
| had not decided | an empty plan | nothing converts; `"arity_conversion"` is `"nothing-to-convert"` |
| decided | any (an empty or absent plan reads the three default names) | kept retired and listed in `"arity_unknown_linkage"` — never restored by guess |

A file with no such row imports as before, whatever its format. A converting import is recorded as one
`import-convert` operation whose inputs digest is the sha256 of the file's bytes.

**A trusted restore (`--restore`) that carries such a row into a store with no plan is refused, whether the file's
store had decided or not**, with the same remedy: run `plan_only=True` first. Without it, restoring a backup into a
fresh store would lose its source's decision — the fresh store would re-export the row as undecided. The cost: restoring
a backup that holds an unexplained retirement into a fresh store needs one plan-only run. The guarantee covers rows
present at the restore; a restore with none is admitted into an unplanned store as before.

**Where an outcome's `op_id` resolves.** It names the operation that wrote the row: a `run_data_migration` call, a
converting import (both have a `migration_op` row), or, for a row a trusted restore wrote, the import itself (an
`op-…` id with no `migration_op` row). It is NULL on imported testimony. `data_migration_receipt(path, plan_id,
user_id)` lists a converting import's rows under THIS store's plan; imported and restored rows keep their source's
plan id, so they are listed under that id instead. The stated limits: a default import
trusts the file to say whether its store decided, so a file can choose conversion or `unknown-linkage` by including or
omitting that line (bounded by what an untrusted file can already do: carry the rows active), and a store that relays
another's file without a plan of its own re-exports it as undecided.

### Exporting and importing confirmations and replies (format 14)

An export writes each confirmation and reply with what it takes to recognise it in another store: its identity (the
store that first recorded it, the user, and its id there), its **position** in that store's order of acts, its origin
(`local`, `restored` or `imported`), and the id of the original request. It never writes the row id, the internal key,
or the request registry. Import reads them over the whole file and what this store already holds, and decides per act:

| the act | default import | `--restore` (your own export) |
|---|---|---|
| claims THIS store as its origin | **refused** (only a restore of your own history may carry it) | admitted |
| already held, identical (after any redaction both copies are under) | nothing written (`"acts_existing"`) | same |
| already held, different in any other field | **the whole file is refused** | same |
| new, on a fact this store already held before the import | **refused**: a file cannot act as you over your own fact | admitted if its history is consistent (below) |
| new, on a fact arriving in the same file | written `imported` | written as recorded (`local` becomes `restored`) |
| its fact is in neither the file nor this store | **the whole file is refused** | same |

An imported act never takes a request id from your id space: it is stored under an internal `#act:` key, keeps the
original request's id as evidence, and writes no registry row, so a later `confirm()` with that id is a new request. It
takes no position from this store's counter.

**Order.** A confirmation made while a challenge to the same fact was open is refused, and so is any history whose
order cannot be established: positions are ordered only within one origin, and an act recorded before this release has
no position. A challenge **resolved** in the merged history (what this store holds plus the file) needs no order. Two
different acts at one position, a challenge resolved twice, or a resolve before its own challenge refuse the whole file.
In a **trusted restore**, an act recorded before this release (no position) counts as earlier than every positioned act
of the same origin, between acts recorded `local` or `restored`. So a backup holding an old confirmation and a later
open challenge restores; a default import of the same file is refused whole, and nothing is written.

**Redacted facts.** An act arriving on a redacted fact needs a notice that covers every content field it carries (a
reply's text and request digest, a confirmation's request digest); a notice that covers some but not all, or a notice
from before replies existed, refuses the file. A covered act is written with those fields redacted, and the same file
imported again is a no-op. A default import never changes an act you hold: a notice for it waits for your
`confirm_notice`.

**Times.** Times are stored as UTC (`Z`, `+00:00` and other offsets of one instant are one time), and a time without a
timezone refuses the file. A reply's write time (the display order of challenges) is never later than the import itself:
a future-dated time is stored as the import's time. Several future-dated replies therefore share that time, and their
display order falls to their ids. A write time never decides an operation.

**Copying into another user (`user_id=`).** Each copied act is placed in an ordering of its own for that import, so a
user can be copied any number of times, into one user or several, and each copy keeps its own internal order. In a copy,
the original store shows only as a hash.

**Grounding.** A default import ignores the file's `att`, `src` and `attv` and stamps every fact `not_attested`, `src`
null, `attv` `default-import`, but a value outside its grammar (an unknown label, a malformed version, `attv` or `src`
without `att`, any of the three on a procedure) still refuses the file. A restore keeps them as recorded, any predicate
version included. A `src` naming an episode that no longer exists is kept. A restore over a fact you hold with a
different grounding is refused, except where this store stamped it `default-import`: that stamp is kept, and the fact
is listed in `"axis_kept_default_import"`.

**A record refused on its own.** A default import refuses procedure records one by one and admits the rest. An act on
such a record is refused with it and counted in `"acts_refused_with_edge"`; nothing of it is written, and the rules
above (rule 0's origin check included) do not judge it.

**An act whose fact is gone.** No verb writes one, and a fact leaves the store only with its user's acts, so such an act
means the store is damaged (`doctor` reports it). An export still writes it, and counts it in `"acts_orphaned"` (the CLI
prints a warning), rather than refusing the whole backup; importing that file is refused.

### Undoing one restoration (`undo_restoration`)

```python
mem.undo_restoration("user-1", "edge-id", correlation_id="undo-1")
# {"undone": "edge-id", "undone_at": "...", "correlation_id": "undo-1", "replayed": False, "already_undone": False}
```

This retires one restored value again, as it was before the restoration. `invalidated_at` and `invalidation_reason`
are set back from the receipt's recorded pre-state, and every other field is left as it is now, including what a
confirmation changed since. The instant is stored normalized, as at every retirement, so a pre-state written in an
older representation comes back as the same instant. It is host API only: no CLI verb and no MCP tool.

- **Request ids.** `correlation_id` is the same per-user id space `confirm()` uses. An id held by a confirmation is
  refused, naming `confirm`; an id held by an undo is refused by `confirm()`, naming `undo`. A retry under the same id
  replays the recorded result (`replayed=True`, always with `already_undone=False`) without reading the edge, so it
  answers after the edge has changed or gone. If you omit the id, one is generated (`auto-…`) and returned; there is
  nothing to retry against.
- **Already undone.** A call on a value already undone, without an id or with an id not yet used, returns
  `already_undone=True` with the recorded `undone_at`. It writes nothing and does not take the id.
- **After a redaction** of the edge, a retry under the undo's id raises `RequestRedacted`, for `undo` and for
  `confirm()` alike. The id stays held, so nothing new is admitted under it.
- **Refusals** raise `UndoRefused` (a `ValueError`) with a closed `reason`:

| `reason` | when |
|---|---|
| `no-outcome` | the data migration recorded nothing for this edge (or the user was erased) |
| `not-restored` | the value was withheld because its source is under standing revocation |
| `testimony` | the outcome was imported: another store's restoration, which this store cannot reverse |
| `not-applicable` | the restoration has ended: a later retirement by any writer, a redaction, or the edge's removal. A later source lift does not revive it |
| `edge-unavailable` | the edge is no longer held, or is redacted |
| `ambiguous-outcome` | more than one outcome row names the edge (only an outcome import could write a second row, and this release has none); no undo chooses between them |

Undo is not an act: it writes no act row and takes no act position. The undo's request id is store-local and is
never exported (specs/0044 §4g). This release exports and imports no outcome rows, so `testimony` and
`ambiguous-outcome` do not arise from its own operations.

`doctor`'s `refs` warning for an active edge whose predecessor is still active becomes an `info` when this store's
own restoration outcome explains it: `restored`, not undone, still applicable, of origin `local` or `restored`. An
imported outcome is testimony, so the warning stays and says so.
