# Changelog

## Unreleased

## 0.10.0 — 2026-08-15

- **The `ungrounded` flag — extraction-fidelity marking at ingest**
  (accepted spec 0019). Every extracted fact's specifics (digits,
  identifiers, proper nouns, ISO dates) are checked against the event text
  they came from; a fact carrying specifics the source never contained
  stores with `Edge.ungrounded=True` — never refused, never demoted, and
  fully recallable, but marked `[possible extraction error]` wherever it
  renders, never volunteered proactively, and excluded from the compiled
  wiki (the flag's only two behavioural reductions; both withhold, never
  grant). The flag is immutable for the record's life — `confirm()` cannot
  clear it (the remedy is restatement); absorption merges strengthen it by
  an N-ary OR and never launder it. Deterministic, zero LLM calls; dates
  ground through a pinned resolution-set rule ("next Friday" grounds its
  arithmetic resolution, proximity grounds nothing). **Export format 5→6**
  (older importers refuse rather than silently dropping the flag) and
  **store SCHEMA v6→v7** (no DDL — the ordinary `veracium migrate` /
  open-time migration applies; older builds refuse a v7 store, so back up
  before upgrading). Supersession receipts stamp `outcome_digest_version 3`
  (spec 0014 as amended). `introspect()` gains an `ungrounded` count. No
  telemetry change (deferred to a future consent version, recorded in the
  spec).

- *Correction to the 0.9.0 `SourceType`-deprecation entry (released text is
  immutable):* that entry said stage D2 ships "export format 6, store schema
  v7". Accepted spec 0019 takes format 6 and schema v7 first; **D2's numbers
  are now format 7 and schema v8** (spec 0016, as amended by 0019 — sign-off
  granted at 0019's round 4).

## 0.9.0 — 2026-08-14

- **`SourceType` is deprecated and will be removed in the next API-breaking
  release** (accepted spec 0016, stage D1 — warning-only, no behaviour
  change). It has never influenced any decision. On ingest-derived records it
  restates `author_of_evidence`; directly-constructed records may carry any
  value, which nothing reads. Accessing the enum through the package or
  `veracium.schema` (including `import *` and pickling) warns, and reading
  `provenance.source_type` on an edge warns once per access. NOT warned, by
  design: model metadata only (`model_fields`, `get_type_hints`) — those and
  only those. Hosts reading the field from exports should stop. Dependency
  note: the minimum supported pydantic rises to **2.7** (the
  `Field(deprecated=...)` floor), enforced by a dedicated CI job at the exact
  floor. Stage D2 (the removal, export format 6, store schema v7) executes
  only through the accepted 0018 release-migration orchestrator in the next
  API-breaking release.

- **Token-usage telemetry over the `Metered` wrapper** (accepted spec 0017 —
  15 external review rounds). Wrap your `Complete` in
  `veracium.llm.metered.Metered(fn, counter=your_tokenizer)` and Veracium now
  attributes per-operation token usage: the wrapper carries an affirmative
  capability (`veracium-metered-v1`) and a listener protocol; `Memory`
  registers a fail-closed listener that attributes each provider call's
  counts to exactly the operation (and user) that made it — exact under
  concurrency, shared wrappers, nested operations, and copied contexts.
  Where the numbers go: the local audit sink and `introspect(user)["llm_usage"]`
  (instance-lifetime, consent-independent, erased by `forget()`); the
  telemetry payload gains eight per-operation token fields ONLY under the new
  consent text (version 3 — existing installs keep sending exactly their old
  field set until telemetry is re-enabled against the updated text, per the
  0015 machinery). No counter → no token fields anywhere (character counts
  stay host-side and are never sent). A failed operation records nothing;
  `self_check` is excluded; MCP surfaces carry no usage. No schema change,
  no migration.

- **BEHAVIOUR CHANGE: default imports now cap trust** (accepted spec 0005 —
  "import has no trust boundary"). Every `import_memory()` / `veracium import`
  without `--restore` sets `author_of_evidence` and `derived_from` to
  `third_party` and floors `disclosure` to `use_only` on every imported record
  (`quarantined` is never weakened), so imported content is never assertable
  or rendered as the target user's own testimony. The return dict and the CLI
  line gain a `capped` count. `--restore` (new, mutually exclusive with
  `--user`; API `restore=True`, strict bool) preserves trust fields exactly —
  for restoring **your own** exports only; the refusal message on an own-store
  default re-import explains the distinction. **Upgrade note for hosts that
  script imports:** a same-store re-import of a pre-0005 export now refuses on
  the default path — pass `restore=True` for backup-restore flows; seeding a
  project from another principal's export keeps working and now lands capped
  (confirm a fact to assert it). One narrow amendment to the 0014
  source-identity projection rides along: on the default path the comparison
  runs over capped records, so identity claims differing only within a cap
  equivalence class skip (inserting nothing) instead of refusing; any content
  difference still refuses. No schema change, no format change, no migration.

## 0.8.0 — 2026-08-13

- **Opt-in telemetry can now report how often values are superseded and
  reinforced** (accepted spec 0015) — the counters the consent dialog's
  "aggregate counters" always intended. Counted at the planner from committed
  results only; consent-gated at record time; stripped from the MCP tool
  result (a per-write count is a supersession oracle). Installs that
  consented before this version keep sending exactly the old field set until
  telemetry is re-enabled against the updated consent text. A process that
  started with telemetry disabled begins collecting at its next process start
  after consent, not mid-run. Consent transitions are serialized under an
  OS-exclusive lock with a persisted transition epoch; deleting
  `telemetry.json` is the consent-erasure mechanism and is never undone by
  telemetry code.
  (`specs/0015`, accepted after 11 external review rounds + implemented.)
- **`veracium migrate` — an operator-facing CLI verb** wrapping the store's offline
  `migrate_store(path)`: migrates a below-head store to the current schema, reports the
  structured result (resulting version, whether anything changed), and refuses
  future-version stores with the store's own reason. Exit 0 migrated/current, 1 refusal,
  2 no file.
- **The `measures` relation** joins the default registry — a functional relation for
  changing quantities (weight, reading progress, balance, score): one current value,
  history kept. `docs/recipes.md` now shows how hosts extend `MemoryConfig.relations`.
- **`veracium.llm.metered.Metered`** — an opt-in wrapper for any `Complete` callable:
  per-role call counts, token counts when the host supplies a counter, honestly-labelled
  character counts when it does not. Totals stay host-side; `docs/telemetry.md`'s stale
  token-totals claim is corrected to what the code actually sends.

## 0.7.0 — 2026-08-11

> **Upgrade recommended for consumers ingesting third-party content**: this release
> ships `specs/0006` source identity and `specs/0014` maintenance attribution —
> trust-surface improvements that make third-party contributions durably attributable
> and revocation-joinable. One offline `migrate_store()` call advances a v3/v4/v5
> store to schema v6; an older build refuses a v6 store rather than misreading it.

- **Maintenance attribution — a consumed contributor now leaves a recoverable record**
  (`specs/0014`, accepted after 16 external review rounds + implemented). When maintenance
  consumes a contributor — absorption folding a duplicate into a more specific restatement, or
  consolidation compacting cold episodes into a summary — the store now writes a durable,
  content-free `contribution_ledger` row in the SAME transaction: who was consumed (as
  domain-separated digests of the resolved source identity and evidence reference — never raw
  refs), into which survivor, at which site, with a store-derived payload recording the exact
  values consulted (total at every site — a stale-but-corroborating input that moves nothing is
  still recorded, closing the invisible-contribution path). Reversal is RE-COMPUTATION over the
  recorded values; `revoke_source` gains its blast-radius join (`contributors_of_source`).
  - **The supersession receipt splits into request and outcome identity**: public
    `apply_supersession` now performs a pre-plan receipt lookup and a lost-response retry
    REPLAYS the persisted effects instead of raising (a live defect executed during review);
    the request digest is STORE-derived from a complete raw-request snapshot under a frozen
    byte-exact construction with pinned test vectors, verified against the plan by an
    exhaustive field partition with store-level per-field abort oracles; the
    concurrent-preflight loser replays, never conflicts.
  - **Consolidation outputs gain durable identity**: `Episode.consolidation_output_index`,
    store-assigned only (caller-supplied values refused); exported per the exclude-none rule.
  - ⚠️ **`SCHEMA_VERSION` v5→v6** — the ledger table + three indexes AND the repo's first
    ALTER of an existing table (`supersession_operations` gains `request_digest`, `response`,
    `outcome_digest_version NOT NULL DEFAULT 1`); `MANIFESTS[6]` accepts BOTH the constructor
    and the reviewed ALTER-path manifest per `0013` §4e (the ALTER-path DDL is an
    independently authored reviewed constant the migration must byte-match). Migrated
    receipts read version 1 (legacy semantics preserved honestly); new receipts stamp 2.
  - ⚠️ **`FORMAT_VERSION` 4→5** — exports carry the output index; older importers refuse a
    v5 file rather than dropping the field; v4 files stay accepted (a pre-v5 index field is
    stripped, never trusted, per `0006` I10). Import enforces indexed-output identity against
    destination state (tenant-scoped, origin-namespaced); a source-identical re-import
    resolves idempotently.
  - `specs/0003` §4f is amended in the same commit (the verbatim `0014` §7b text + eleven new
    I9 checks). The round-16 bin-(b) obligation (carrier-verifier byte-vs-text exactness) is
    dispositioned as the narrowed text-exact claim, recorded in the §12 acceptance ledger.

- **Fact-currency renewal — a restatement can no longer silently renew a fact's currency**
  (`specs/0012`, accepted after 14 external review rounds + implemented; the implementation
  itself independently reviewed and ACCEPTED after 8 further rounds). Reinforcement now
  transfers NOTHING: a re-stated fact is persisted as its own edge with its own provenance, and
  the prior is left byte-untouched — closing a measured bypass where same-class restatements
  (e.g. a system feed re-asserting a user fact) kept a stale fact perpetually fresh and silently
  raised its confidence, and closing finding M9 (the contributing source now leaves a recoverable
  record: the edge itself). Each edge ages against its own `observed_at`; only `confirm()` clears
  the possibly-stale flag.
  - **Read-path collapse**: every model-facing surface (query recall, the wiki compiler input,
    proactive assembly) suppresses only *strictly redundant* active duplicates — full
    authority-envelope grouping, deterministic survivors, one confirmable stale-warning owner at
    a time ("×N restatements need confirmation"), never a synthesized value, and the store keeps
    every edge.
  - **Hard token budgets** on all rendered surfaces: envelope-derived floors (a below-floor
    `token_budget` now raises `ValueError` instead of best-effort rendering), per-item clamps
    that shrink content but never sever safety labels, deterministic precedence under overflow
    (safety and warnings before breadth), a truncation report line with per-class counts, and
    budget-aware packing of contested groups.
  - **The wiki compile-drop marker**: every compiled wiki ends with an authoritative, forge-proof
    `[[veracium-wiki-compile:v1]] +N facts / +M episodes not compiled` line; `introspect()`
    exposes it as `wiki_compile_record` (status ok/absent/legacy/malformed), and the CLI prints
    a one-line summary.
  - ⚠️ **The wiki cache identity now binds the compiler policy** (version `0012-v1` + budgets +
    the marker grammar): an existing cache recompiles once on first use after upgrade. The
    store-only CLI (`veracium recall`) never recompiles — with a stale cache it serves recall
    without the wiki plus an explicit notice, instead of failing.
  - ⚠️ `MemoryConfig` gains seven budget fields (all validated); `0003`'s reinforcement plan
    action and `0008`'s C3 liveness-refresh are amended accordingly (marked in both specs).

- **Source identity — record *which source* a fact came from** (`specs/0006`, accepted +
  implemented). Provenance gains an optional `(origin, source_id)` pair: `source_id` is an opaque,
  host-supplied identifier for the source that produced an event (a mailbox, a connector instance, a
  device), passed via `Memory.remember(..., source_id="…")`; `origin` is a store-minted collision
  namespace so two stores' identical `source_id`s never merge on import. It is **diagnostic only —
  it groups records for dedup/inspection/attribution but grants no trust and changes no answer**, and
  it is host-supplied only, never model-derived. Under the hood: a canonical, shared
  `source_identity_digest` primitive (so future consumers re-derive one key), a durable per-store
  `store_identity` singleton, and resolve-at-read so a local record and its own export round-trip
  count as one source.
  - ⚠️ **On-disk store schema advances to v5** (one new `store_identity` singleton; no per-record
    change). A v1–v4 store migrates forward in one `migrate_store()` call; an older build refuses a
    v5 store rather than misreading it.
  - ⚠️ **Export/import `FORMAT_VERSION` advances to 4** — a v4 export is self-describing (each record
    carries its resolved origin); a v4 import rejects a record with no origin and ignores
    source-identity fields smuggled into an older-format file. Older builds refuse a v4 export.

## 0.6.0 — 2026-08-08

- **Supersession authority — third-party content can no longer retire your facts**
  (`specs/0003`, implemented). Until now the functional-supersession loop retired *any*
  differing value for a fact regardless of who reported it, so an incoming email extracted
  as `works_as: unemployed` could silently retire your own `works_as: CFO` and erase it from
  recall. Retirement is now governed by an **authority ladder** capped by provenance (who the
  evidence is from, and what it was derived from): `USER > SYSTEM > ASSISTANT > THIRD_PARTY`,
  with `effective = min(author, derived_from)` — so a `SYSTEM` summary of an attacker's email
  scores as third-party and retires nothing. A differing value supersedes the prior **only**
  when its effective authority is greater than or equal to the prior's; otherwise the
  retirement is **refused**: both values stay active and visible, and a durable, **content-free**
  refusal record (opaque edge ids, the relation, two authority levels — never your memory
  content) is kept so the guard's behaviour is observable and later policy can re-evaluate it.
  `Memory.supersessions_refused(user_id)` and `Memory` recall now expose this.

- **A refused update no longer disappears from recall.** Keeping both edges in the store is
  not enough if retrieval then drops the older one, so recall was hardened to match: within a
  contested functional group, recorded authority is ordered ahead of relevance and recency
  (a permutation — unrelated facts keep their place); the contested pair is kept **out of the
  one-value curated wiki** so it can't be collapsed there; and the higher-authority value is
  surfaced in a deterministic **CONTESTED FUNCTIONAL FACTS** block that gets first claim on the
  recall token budget. `Recall` gains a structured `contested` field; a lower-trust challenger
  that ordinary retrieval didn't surface appears only as content-free linkage, never as
  assertable content. The abstention gate still asserts only grounded memory.

- **On-disk store schema is now v4.** Two new content-free, per-user tables (the refusal
  inventory and a crash-safe operation receipt) are added additively. v1/v2/v3 stores migrate
  via one `migrate_store()` call, which also drops any wiki cache compiled under the old
  "one current value" semantics. ⚠️ **Consumers:** as with the v3 bump, a bare dependency-pin
  bump will not open an un-migrated older store — run the deployment-authority migration first;
  an older build opening a v4 store refuses rather than losing the refusal inventory.
  `apply_supersession` is applied as one atomic, compare-and-set-linearized plan, so concurrent
  updates to the same fact cannot branch it into two current values.

- **`correct()` is unchanged and remains out of scope** (tracked in `specs/0011`): it is a
  separate replacement path and is not governed by the authority ladder in this release.

## 0.5.0 — 2026-08-07

- **Outcome-authorship history is append-only** (`specs/0009`, implemented).
  `record_outcome` no longer overwrites a prior judgment: every use-and-judgment of a
  fact — keyed by `(edge_id, evidence_ref)` — becomes a new link in an append-only
  chain, so **who judged what, and when, is never destroyed** (the previous behaviour
  kept only the latest judgment, silently losing the earlier author). The edge's
  `times_used`/`outcome_counts` are now **derived from the chain heads**, not mutated
  in place. `Store` gains an atomic compare-and-set writer `append_outcome_if_head`
  (the only sanctioned way to extend a chain) and a whole-file
  `commit_outcome_import_plan`; the generic `add_episode`/`delete_episode` refuse
  outcome-chain rows. Portable import validates-or-refuses an incoming chain (never
  repairs), remaps cross-user references, and is idempotent on record equality; the
  offline migration converts each legacy outcome episode into an honest chain root,
  marked **`judgment_time_known = False`** (its stored date is the original use date,
  not a fabricated judgment time), and refuses rather than branching on a duplicate
  identity. `Episode` gains `seq` / `supersedes_episode` / `judgment_time_known`.

- **Crash-safe consolidation** (`specs/0010`, implemented). Memory consolidation is now
  a **fenced, leased, crash-recoverable** operation. Inputs are claimed atomically over
  the whole batch; the consolidated summary is written and made durable **before any
  input is deleted**; and a crash at *any* point is recovered on the next
  `consolidate()` — rolled forward (idempotent re-delete + finalize) or cleanly
  abandoned — so **no episode is ever lost without a replacement** (the previous path
  deleted every input before writing any summary, a total-loss window on a mid-operation
  crash). Every ordinary read sees **exactly one** complete representation — all inputs
  or all outputs, never both and never neither. A consolidated output carries its
  **whole** input set as lineage and the **minimum trust across that set** (a summary of
  third-party-influenced material stays third-party-influenced), and renders a date
  **range** rather than a single misleading date. `Store` gains the consolidation
  operation record and its fenced primitives; a claimed input is **reserved** (the
  generic mutators refuse it) until the operation finalizes. `export_memory` is now a
  **read-only quiescent snapshot** that refuses to export mid-consolidation (mutating
  nothing) rather than emitting a claimed input whose operation cannot travel with it.
  `Episode` gains `claimed_by` / `operation_id` / `lineage` / `date_start` / `date_end`.

- **The on-disk store schema advances to v3.** The new `Episode` fields (`0009` + `0010`)
  ride the existing episode JSON blob and `0010`'s operation record lands as a new
  `consolidation_ops` table — a purely additive change. A store below the head (an
  unstamped v1 store from any released veracium, **or** a v2 store) is brought forward in
  **one** offline `veracium.store.migration.migrate_store(path)` call (`specs/0013`); an
  older build opening a v3 store refuses loudly rather than silently misreading it.

- **`confirm()` is the only thing that clears the "possibly stale" flag**
  (`specs/0008`, implemented). Reinforcement — a re-statement of a fact already
  known — no longer clears `needs_confirmation`; it refreshes liveness only. The
  0.4.5 behaviour cleared the flag whenever a re-statement's author *class* matched
  (USER and SYSTEM share a disclosure class), so a system-authored restatement
  silently answered a "confirm before relying on this" question meant for the user.
  Now only an explicit `Memory.confirm()` clears it, atomically: the flag, liveness,
  confidence, the confirmation episode, and a **mandatory confirmation record** all
  commit together — if the record cannot be written the confirmation fails and the
  flag stays set. `confirm()` gains closed-enum `actor`/`call_path` (audit metadata,
  granting nothing) and an optional `correlation_id` for replay-safe retries; it
  returns `{confirmed, valid_from, confirmed_at, correlation_id, replayed}`.
  `Store` gains an atomic `confirm_edge` mutator and a `confirmations_for()` audit
  read; `add_edge` now refuses to clear the flag or change an edge's owner through
  the upsert path. A cross-user `import(..., user_id=…)` now mints fresh ids (a copy,
  never an ownership transfer). **The store schema advances to v2** (the
  `confirmations` table) via the offline `specs/0013` migration:
  `veracium.store.migration.migrate_store(path)` — a store below the head version
  refuses ordinary open (`migration-required`) and is brought forward by this
  explicit, deployment-authority-owned operation, per `0013` §5b.

- **On-disk store migrations** (`specs/0013`, accepted 2026-08-07 after 12 external
  review rounds post-M-Q4-ruling) — the abstract migration design and audit
  *protocol* for evolving a stamped store across schema versions, reviewed against
  the concrete v1→v2 `confirmations`-table migration. Accepted on the finite M-Q4
  acceptance boundary (spec §8a): the six gated properties are frozen and
  mechanically demonstrated (concrete migration correctness; planner/evidence
  architecture; closed public semantics; the abstract atomic audit protocol;
  the adapter-conformance surface; independent mechanical gates). The design is a
  prerequisite of `0006`/`0008`/`0009`/`0010`. **No production behaviour ships
  yet**: `Spec-Requires: 0007` (still `draft`) is gate-enforced, and the
  production audit sink — with its explicit blocking obligations (real two-table
  DDL, multiprocess consumption, invocation-provenance reconciliation, the
  `current`-with-repair `committed=True` contract, crash injection) — lands with
  `0008`. The in-process reference instrument (`specs/migrations_0013.py`) is a
  draft measuring model, not shipped code.
- **On-disk store schema versioning** (`specs/0007`, accepted after 14 external
  review rounds). A store now carries `PRAGMA user_version`; on open the store
  is recognised exactly or refused loudly, replacing the previous unconditional
  `CREATE TABLE IF NOT EXISTS` that opened any file and silently added missing
  tables to foreign ones. Concretely:
  - a **new** store is created and stamped in one `BEGIN IMMEDIATE` transaction;
  - every store written by any released veracium (all are unstamped) is
    **adopted losslessly** on first open — data unchanged, drifted acceleration
    indexes repaired, stamp written — with optional typed audit events
    (`audit_sink=`) and an `allow_adopt=False` opt-out;
  - anything else — newer stamps, foreign schemas, stamped-but-wrong shapes,
    negative versions — raises `StoreVersionError` with a closed `reason` and a
    diff naming the nearest accepted shape;
  - the running SQLite must match the packaged runtime evidence
    (`unsupported-sqlite` otherwise; 3.45.1 is the qualified build identity).
  `SqliteStore` gains keyword-only `allow_adopt`, `audit_sink`,
  `busy_timeout_ms`. The schema is now derived from a single registry shared
  with the spec tooling, and the evidence artifacts ship as package data.
  `open_versioned()` now returns which branch ran (`"current"` / `"created"` /
  `"adopted"` / `"migrated"`) and exposes two delegation seams for
  `specs/0013` as keyword-only hooks — `older=` (the §4 older row) and `new=`
  (creation, so a dedicated migration mode can refuse to create); with no
  hooks (the production default while `SCHEMA_VERSION == 1`) behaviour is
  unchanged. Package-consistency impossibilities now raise the named
  `PackageConsistencyError` (a `RuntimeError` subclass), and path/audit
  string caps measure filesystem bytes, so stores at non-UTF-8 POSIX
  filenames work.


## 0.4.8 — 2026-08-02

- **Consolidation wrote internally false provenance.** A summary reported
  `author_of_evidence=SYSTEM` while carrying `source_type=STATED` and the
  **first input's** `evidence_ref`, because both were inherited from `cold[0]`.
  A system-authored summary is not a stated fact and its evidence is not one
  arbitrary member. Now `INFERRED`, with an `evidence_ref` naming the
  consolidation.

  This is the 0.4.4 `cold[0]` defect surviving on two fields the 0.4.7 test
  never inspected.

- **An offset-bearing `date=` failed through `remember()`.** 0.4.7 taught
  `_event_dt` to convert offsets, then handed the **raw string** to the prompt
  builder, which parses with `date.fromisoformat` and rejects them — so
  `remember(date="2026-01-01T12:00:00+05:30")` raised `Invalid isoformat
  string`. Every public entry point now normalises once and passes the
  normalised value on.

- **The unparseable-extraction path recorded the wrong instant.** When
  extraction returned no parseable JSON, `observed_at` was re-derived from the
  already-reduced date, so `12:30+05:30` was stored as **midnight** rather than
  07:00 UTC. Both branches now reuse the accepted instant.

- **`veracium-mcp --version` no longer fails outside an installed package.** It
  reported `PackageNotFoundError` from a bare source tree; it now says so and
  continues. Deliberately without a `__version__` constant — `pyproject.toml`
  stays the single source of the version.

## 0.4.7 — 2026-08-02

- **An offset-bearing event date was relabelled UTC instead of converted.**
  `_event_dt` did `datetime.fromisoformat(x).replace(tzinfo=utc)`, which
  **discards** an existing offset rather than converting the instant. A
  timestamp written `...T20:00:00-12:00` was checked as if it were 20:00 UTC
  when the instant it names is 08:00 the following day — **measured at 12 hours
  of future-skew bypass, and up to 26 across the legal offset range.** It
  partially defeated the future-date rejection shipped in 0.4.6.

  Offset-bearing values are now converted with `astimezone(utc)`; a naive value
  still means UTC, which is the documented contract for a bare date.

- **Consolidation manufactured confidence, disclosure and currency.**
  `consolidate()` set `confidence = 0.9` unconditionally and inherited the first
  input's disclosure, so **a batch containing a 0.2 episode produced a summary at
  0.9**, and a batch containing one `use_only` episode could produce a
  `mentionable` summary. A summary is now **no stronger than its weakest input**
  across every trust-bearing field: `confidence = min`, `disclosure = weakest`,
  `observed_at = max(inputs)` and never *now*.

  This is the same rule that governs T2 deduplication — **recognition is not
  observation, and a summary of old material is not new evidence.**

  Found by external review of `specs/0002`, against an invariant that spec had
  itself added while the code violated it.

- **A malformed `date=` is now rejected instead of silently becoming *now*.**
  `_event_dt` fell back to the current time on any unparseable date. That is the
  same manufacture 0.4.6 removed for *future* dates, in a quieter form: **a
  malformed statement about when an event happened is not evidence that it
  happened now.** The fallback could refresh a stale fact, relieve lifecycle
  pressure through a later `observed_at`, and write an audit record attributing
  an invented time to a caller that believed it had supplied one.

  **Absence is now the only thing that means now** — omit `date=` and you get
  the current time, as before.

  Ingest validates through the same function before building its prompt, so a
  bad date fails with the reason rather than with `date_context`'s raw
  `Invalid isoformat string`. **One input had two parsers and two error
  contracts.**

  Found by external review of `specs/0002`; the reviewer noted §7f rejected
  future dates while retaining the malformed fallback, which violates the
  principle that section exists to enforce.

## 0.4.6 — 2026-08-01

- **Two defects found while verifying an external review of `specs/0002` — both
  live in released 0.4.5, both fixed.** Neither was reported by the review; both
  turned up in the process of checking its claims against running code.

  **`confirm()` returned a `valid_from` it never set.** 0.4.5's M2 fix stopped
  `confirm()` moving a fact's first-known date, because `render_edges` emits
  `(since <valid_from>)` into answer context and a January preference confirmed
  in March read *"(since March)"*. The fix corrected the model's context and
  **left the same false date in the return value a host UI reads** —
  `confirm()` returned `{"valid_from": <confirmation date>}` while the edge kept
  its real one. The return now carries both `valid_from` (the real, unchanged
  first-known date) and `confirmed_at`. **A fix that missed one of its own
  surfaces; the sibling it missed is the one an integrator sees.**

  **A future-dated event was accepted, and was unrecoverable.** `date=` had no
  upper bound, so `remember(date="2099-01-01")` set both `valid_from` and
  `observed_at` to 2099. `observed_at` is only ever advanced with `max(...)` —
  which is what correctly defeats *back*-dating, and is therefore exactly what
  made *forward*-dating permanent: no later confirmation could bring it down.
  **One host-supplied date removed a fact from lapse, decay and staleness
  flagging for 73 years, with no API to undo it.** Event dates more than a day
  in the future are now rejected at `_event_dt`, the single point every event
  date passes through, so `remember()`, `confirm()`, `correct()` and
  `record_outcome()` are all covered.

  **Behaviour change:** a future `date=` now raises `ValueError` instead of
  being stored. It has no legitimate meaning — the event date records when a
  statement was made, not what it is about, so *"the contract expires in 2027"*
  is a value and never an event date. Malformed dates keep their existing
  fallback to now.

- **retrieval: coverage-aware subgraph selection was measured and stays OFF.**
  0.4.2 shipped it disabled and said *"the default will change only if a
  balanced measurement supports it."* **That measurement has now run, under a
  pre-registered protocol, and it does not support it.**

  30 items drawn stratified on distinct `valid_from` days — the variable the
  code actually branches on — with the hypothesis, primary metric, thresholds,
  analysis plan and stop rule fixed in advance and approved before any run.
  Three replicates across four arms.

  **Coverage rose on 12/12 items (+5.25 distinct sessions at the tested
  setting). The primary metric — the fraction of answer-bearing turns actually
  retrieved — improved on 2 of 12, against a pre-declared threshold of 10.**
  The mechanism does exactly what it was built to do and does not buy the thing
  it was built for. Read cost was flat, so it is not expensive — it is
  ineffective on this measure. Exploratory arms at half and double the reserve
  moved coverage monotonically (+2.75 / +7.67 sessions) and the primary metric
  not at all, so this is not a mistuned parameter.

  **`subgraph_coverage_share` keeps its default of `0.0`, and the code stays**
  — off by default, tested, and re-runnable if the storage granularity that
  bounds this result ever changes.

  **What the result does not establish.** It is evidence about day-clustered
  coverage selection **under day-granular storage**, on one benchmark and one
  metric, n=12. Seven of the twelve items were already at a perfect hit rate in
  the baseline, so more than half the sample had no room to improve and the
  pre-declared threshold was, in hindsight, unreachable from the moment the
  sample was fixed. That does not rescue the hypothesis — coverage rose
  everywhere and the metric moved almost nowhere — but "ineffective in general"
  is **not** what was shown.

  One item regressed from a perfect hit rate to zero when coverage was enabled;
  that is being investigated separately as a defect rather than folded into this
  result.

## 0.4.5

Three provenance defects, found by an audit of the maintenance-time operations
(`specs/0002-maintenance-provenance-invariant.md`).

> **Correction (2026-08-01):** this entry originally said the audit covered
> **every** maintenance-time operation. It did not. Review found
> `portability.import_memory` absent from the enumeration — a surface that
> reconstructs *every* trust-bearing field from a file and writes it straight to
> the store, bypassing the ingest path's trust machinery entirely. The word is
> withdrawn until the enumeration is mechanical rather than recalled. See
> `specs/0002` §M6. The audit was
prompted by two advisories in four days — GHSA-r7j7-5jq9-3f5q and
GHSA-hcj3-8jqc-wqrp — which are the same shape: a maintenance operation crossing
a trust boundary the write path guards correctly. **None of the three below is a
trust-boundary bypass**, so no advisory accompanies this release.

- **`confirm()` no longer moves a fact's first-known date.** It used to set
  `valid_from` to the confirmation date — **the exact defect 0.4.3 shipped C′ to
  eliminate**, in a sibling path the fix never touched. Because `render_edges`
  emits `(since <valid_from>)` into answer context, a preference stated in
  January and confirmed in March was rendered to the model as *"(since
  2026-03-01)"* — a false statement in front of the model, not merely lost
  history. **0.4.3's changelog asserted "valid_from is set at creation and never
  mutated"; that was not true of `confirm()`, and now is.** A confirmation is
  new evidence about *liveness*, so it advances `provenance.observed_at`.
  **Not repairable:** dates already moved by a prior `confirm()` are
  unrecoverable — the original is not recorded anywhere.
  *A test asserted the old behaviour, which is why C′ did not catch it.*

- **A staleness flag can no longer be cleared by a different author.**
  `needs_confirmation` renders as *"confirm before relying on it"* — a question
  addressed to the party who stated the fact. Reinforcement cleared it
  unconditionally, and the 0.4.1 same-class guard compares **disclosure** class,
  where `USER` and `SYSTEM` both sit in `MENTIONABLE`. So a system-authored
  restatement answered a question meant for the user. Now only same-author
  evidence clears it; `confirm()` remains the explicit path, and third-party
  content was already correctly blocked.

- **Outcome authorship is no longer overwritten.** `record_outcome()`'s
  upgrade-in-place path replaced the episode's `author_of_evidence` with the new
  actor's, discarding who made the earlier judgment — in a system whose stated
  principle is supersession-never-erasure. The prior author is now retained in
  the episode summary. Outcome episodes are excluded from recall, so nothing
  reached the model either way.

**Also added:** `tests/test_maintenance_invariant.py`, which states the class
rather than the instances. The load-bearing one is **N7** — *a full `maintain()`
cycle never moves an edge from the UNVERIFIED block to the GROUNDED one* —
expressed over the observable boundary rather than any field, so it catches the
next instance even when the mechanism is one nobody anticipated. **Both
advisories would have failed N7.**

## 0.4.4 — security

- **SECURITY: episode consolidation laundered third-party content into the
  grounded block.** `maintain()`'s consolidation step built the consolidated
  episode's provenance from a **single member** of the cold batch
  (`cold[0].provenance`), so a mixed batch whose first episode happened to be
  user- or system-authored collapsed to `author_of_evidence=USER` with
  `derived_from=None`. `Provenance.third_party_influenced` then reported
  `False`, and `gate.partition_parts` — which routes episodes on exactly that
  property — moved the summarised third-party text out of the UNVERIFIED block
  and into the **GROUNDED** one, where it may be asserted.

  This is the attack `gate.partition_parts` names in its own docstring (*"a
  system-authored summary quoting a received email launders attacker text into
  its episode — route by influence, never by authorship alone"*): consolidation
  was defeating the defence its own module documents. It required no
  hallucination and no prompt injection — a faithful summariser compacting a
  mixed batch was sufficient. Same class as GHSA-r7j7-5jq9-3f5q (0.4.1): a
  **maintenance-time** operation crossing a trust boundary that the write path
  guards correctly.

  **Fixed:** consolidated provenance is now computed across the **whole set** —
  `author_of_evidence=SYSTEM` (which is what the code's own comment always
  claimed it was) and `derived_from=THIRD_PARTY` if **any** member was
  third-party-influenced. The result stays in the UNVERIFIED block, matching
  pre-consolidation behaviour.

  **Affected:** every version with consolidation, through 0.4.3. **Exposure
  requires** `maintain()` to run consolidation over **≥8 cold episodes**
  (default `consolidate_min_batch`) older than **30 days** (default
  `consolidate_after_days`) with **mixed authorship** and a trusted episode
  first in store order. Deployments that never call `maintain()`, or whose
  episodes are single-author, are unaffected. **Upgrade if you ingest
  third-party content (received mail, documents, tool output) and run
  maintenance.** No store migration is required; existing consolidated
  episodes are **not** retroactively re-labelled — see the advisory for how to
  identify them.

  Found while writing the first specification under `specs/PROCESS.md`: the
  template's rule to enumerate a changed field's consumers *mechanically rather
  than from memory* surfaced `lifecycle.py` as a writer of
  `author_of_evidence`, which the memory-written list had missed.

## 0.4.3

- **telemetry: the abstention heuristic under-counted abstentions.** It existed
  twice — a narrow copy behind `answer`'s content-free `abstained` counter and a
  broader one in `selfcheck` — and the narrow copy missed the most common
  refusal phrasing the gate actually emits (*"I don't have any confirmed
  information about X"*). Abstention is the metric that most directly tracks the
  product's core guarantee, so under-reporting it was the worst place for a
  duplicated regex to drift. Now defined once as `gate.ABSTAINED` and imported
  by both; regression test uses verbatim openings from real judged answers.
  Found while hand-classifying benchmark misses, not by any test.

- **BREAKING (semantics): `valid_from` is now first-known and immutable.**
  Reinforcement used to overwrite it with the latest restatement date, so a
  fact stated in January and restated in March reported `valid_from` = March
  and the January date was unrecoverable. Because `render_edges` emits
  `(since <valid_from>)` into recall context, that was **a false statement in
  the answer context**, not merely lost history — and it violated the field's
  own documented contract (`edges_since` already distinguishes "when it became
  true" from "when veracium recorded it"). Now: `valid_from` is set at creation
  and never mutated; `provenance.observed_at` carries the latest recording (it
  already did); **`maintain()` ages liveness against `observed_at`** instead, so
  a restatement still keeps a fact alive — it refreshes the field that means
  liveness. T1 absorption's winner inherits the **earliest** `valid_from`
  (`min`, was `max`) and the latest `observed_at`; recall's recency tiebreak
  and proactive recall's "unrefreshed since" read `observed_at`.
  **`introspect()` renames `first_observed`/`last_observed` →
  `first_known`/`last_recorded`** — the old `first_observed` was computed from
  the `max()`ed field and so reported *last* observed under a "first" name.
  **Forward-fixing only:** already-collapsed `valid_from` values in existing
  stores cannot be recovered. Invariant now asserted on every write path:
  `valid_from <= observed_at`.
  Found by a LongMemEval experiment; the write-path defect, not the benchmark,
  is the reason it ships.

- **retrieval: time coverage in subgraph selection — implemented but OFF by
  default (`subgraph_coverage_share = 0.0`).** When enabled, most of the budget
  is still filled by relevance alone and a reserved tail goes to periods not
  already represented. **It ships disabled because it is unvalidated**: the
  measurement that motivated it was retracted — the benchmark sample it was
  diagnosed from proved unrepresentative on exactly the dimension involved, so
  the mechanism has never been tested on data that could exercise it. The code
  and tests are here so the experiment can run; the default will change only if
  a balanced measurement supports it. Pure top-k has no coverage
  term, so a cluster of facts sharing the question's vocabulary takes the
  whole budget and a question spanning months gets answered from a single
  day — measured on LongMemEval, where an interval question recalled 37 date
  mentions of which **one** was distinct, making the interval uncomputable
  and the abstention correct. Clusters on `valid_from`, the only temporal key
  always available (session identity is a host concept most callers never
  supply). Conservative by construction: the head is pure relevance so the
  strongest matches are never displaced, coverage only spends the reserved
  tail on candidates that already passed relevance, the tail backfills by
  relevance when there is no other period to reach, and stores below the
  budget are bit-identical to before. Set `subgraph_coverage_share=0.0` to
  restore pure relevance ranking.

  > **Outcome (2026-08-01):** the balanced measurement promised above has run.
  > **It does not support enabling this, and the default stays `0.0`** — see the
  > Unreleased entry at the top of this file. Recorded here rather than by
  > editing the text above, so the original commitment and its answer both stay
  > readable.

## 0.4.2

- **retrieval (graph): recall was query-blind on large stores.** Every
  user-subject edge carried a *constant* score, so once a store outgrew
  `max_subgraph_edges` the truncation kept whichever edges the store listed
  first and the query stopped mattering for the subject that owns most facts.
  Small stores were unaffected (everything fits), which is why fixtures never
  showed it; on a ~1,700-fact store recall returned effectively the same facts
  whatever you asked, and raising the cap only returned more of the same
  (measured: 40 → 200 edges gave **no accuracy gain at 3.8× the read cost**).
  Now: user-subject edges stay always-eligible — the "everything off the user
  node" contract is unchanged — but relevance decides which survive
  truncation, with recency as a deterministic tiebreak. Also: `relation` is
  matchable text (so "pet" reaches `has_pet`), the non-discriminating owner
  token `user` is excluded from matching, and query wording is folded to a
  fixed point over ordinary plurals ("deadlines" reaches `deadline`).
  Found by the LongMemEval pilot, whose failure taxonomy put **0 misses in
  extraction** and the rest in ranking and synthesis.

## 0.4.1

- **security (graph)**: identity merges (reinforcement + T1 absorption) are
  now confined to edges of the **same disclosure class** — previously both
  were trust-blind, so a third-party `use_only` restatement of a user fact
  could (a) retire the user's assertable edge (reason `absorbed_duplicate`),
  leaving no assertable version of a true, user-evidenced fact — a
  third-party event could silently demote user facts out of assertable
  recall (subset form new in 0.4.0's T1); and (b) refresh a USER edge's
  liveness, clear its `needs_confirmation` flag, and raise its confidence
  (exact-match form present since 0.3.0 and earlier; widened by T1).
  Cross-class restatements now accumulate as separate edges, each carrying
  its own trust — the explicit upgrade path for corroborated third-party
  material remains `confirm()`/a user restatement. Dedup never makes trust
  decisions. Found by the research session's post-merge T1 review
  (`proposals/t1-review.md`); locked by cross-trust regression tests and a
  new hard **trust-canary gate in the bench engine tier**
  (`engine.trust_canary_failures == 0`).

## 0.4.0

- **proactive recall**: `recall(user_id)` with no query returns a session-start
  briefing — dated commitments due/overdue, possibly-stale facts to confirm,
  current transient state, recent history. Volunteering is disclosure-gated:
  only `MENTIONABLE` facts surface; `use_only` and quarantined material never
  appear unprompted (the Disclosure tier doing the job it names). LLM-free,
  deterministic, budget-aware (commitments outrank history when trimming);
  MCP `recall` exposes it by omitting `query`. New config:
  `proactive_deadline_window_days` / `proactive_recent_days`.

- **introspect** (the "inspectable memory" half of a recurring demand signal;
  `dispute`/`confirm`/`correct` are the editable half): `introspect(user_id,
  mode="summary"|"categories")` — the formatted transparency view over what
  was always exposed raw. Counts by relation / evidence author / disclosure
  tier, lifecycle state, retired history by reason, episode counts;
  `categories` adds the facts grouped by relation with the same provenance
  markers recall renders. LLM-free, store-only; content-free `introspect`
  telemetry event.

- **CLI memory verbs**: `veracium recall` (no query → the proactive briefing;
  with a query → subgraph + *cached* wiki — store-only either way, never
  compiles, needs no provider), `veracium remember` (ingest one event;
  `-` reads stdin; `--author`/`--derived-from` route trust exactly like the
  API), `veracium introspect` (`--categories`, `--json`). Memory becomes
  scriptable without touching Python.

- **Claude Code hooks recipe** (`examples/claude_code_hooks/`): ambient
  memory via lifecycle hooks instead of (or alongside) MCP — a `SessionStart`
  hook injects the proactive briefing at zero schema-token cost (and again
  after context compaction), a `UserPromptSubmit` hook writes the user's
  words back through a detached `veracium remember` so extraction never
  blocks a turn. Provenance discipline documented: captured content the user
  did not author must be routed `third_party`/`derived_from`.
- **value-equivalence T1 — subset absorption** (`graph.apply_supersession`,
  per `proposals/value-equivalence.md`): a *more specific* restatement of a
  held value ("cat Miso" after "Miso") now absorbs the shorter form instead
  of accumulating a duplicate — the prior retires non-destructively (reason
  `absorbed_duplicate`, note carries `absorbed_by:<winner-id>`), the winner
  takes `max(valid_from)`/`max(confidence)` and keeps its own provenance,
  and no `supersedes` pointer is set (absorption is identity, not change —
  `render_edges` never shows an absorbed value as history, and on functional
  relations a subset-shaped restatement no longer churns a false
  supersession). A *less specific* restatement ("Miso" after "cat Miso")
  reinforces the fuller edge: validity refreshed, `needs_confirmation`
  cleared — allowed because write-time evidence just arrived. Guardrails:
  ordered-subsequence match only (the 'tea over coffee' ≠ 'coffee over tea'
  contract survives), at most 2 extra tokens, same (subject, relation) only;
  `his X`/`her X` still never merge. Exact-match reinforcement now takes
  `max(valid_from)` too, so a back-dated restatement can no longer rewind a
  fact's freshness. The S4 robustness checker and bench record classify
  absorptions in their own bucket (`absorbed`), never as `duplicated`.

## 0.3.0

- **bench**: internal benchmark suite (`bench/run_bench.py`) — engine-overhead
  medians against a zero-latency scripted model, the acceptance eval, and the
  robustness tier at `--s4-samples 50` with duplicate-shape classification
  (the value-equivalence T0 measurement), recorded per-release to
  `bench/results.jsonl` with a `--compare` regression gate. Now part of the
  maintainer release checklist. See `bench/README.md`.

- **mcp 2.0 compat**: the MCP SDK 2.0.0 renamed `FastMCP` to `MCPServer`
  (same decorator API) — `veracium-mcp` now imports whichever the installed
  SDK provides, so `mcp>=1.0` stays the supported range on both majors.

- **outcome tracking (V4)**: co-designed with the first production consumer —
  `record_outcome()` records uses and judgments of facts as `kind="outcome"`
  episodes (the source of truth) with derived edge counters
  (`times_used`/`outcome_counts`/`last_outcome`); judgments upgrade the
  matching use in place via (`edge_id`, `evidence_ref`). Vocabulary:
  `unreviewed`/`confirmed`/`corrected` (human) /`challenged`/`concurred`
  (LLM judge), actor rules enforced. Edge-blind by design: `record_outcome`
  never supersedes facts; the explicit fact-level `correct()` verb supersedes
  with reason `"corrected"`. `challenged` reuses the possibly-stale flag;
  counters render into recall as information, never gating; outcome episodes
  are excluded from the narrative recall window and from LLM consolidation.
  Portability format v2 (`"record"` marker; v1 imports unchanged). Neither
  verb is an MCP tool.

## 0.2.4

- **selfcheck UX**: `veracium selfcheck` now preflights the provider — a
  missing SDK or missing `ANTHROPIC_API_KEY` exits with one clear install
  hint instead of a traceback or, worse, a garbage `FAIL … injection
  asserts=1` scorecard (an erroring check was conservatively scored as an
  assert, which read exactly like the injection guarantee failing). If the
  provider fails every check mid-run (e.g. bad credentials), the result is
  now reported as **DID NOT RUN** (exit code 2) — an environment problem is
  never rendered as a memory-safety result.

## 0.2.3

- **MCP Registry**: README carries the `mcp-name` validation marker and
  `server.json` (current registry schema) sits at the repo root — Veracium is
  publishable to registry.modelcontextprotocol.io, which the MCP directories
  crawl. `docs/mcp.md` refreshed: PyPI install flow (the page still described
  a pre-PyPI clone install), the `remember` tool row now documents
  `derived_from`, `recall` documents `token_budget`, and the deliberately
  non-MCP verbs are listed with their rationale.

## 0.2.2

- **veracium-mcp CLI**: `--help` and `--version` now work (previously any
  argument was ignored and the stdio server booted silently — confusing on a
  first install); unknown arguments fail with a pointer to `--help`; a boot
  failure (e.g. missing `ANTHROPIC_API_KEY`) exits with a clear one-line
  message instead of a traceback.

## 0.2.1

- **host queries** (requested by the first production consumer for its
  intelligence layer): `Memory.list_entities()` — distinct ids with
  edge/episode counts, for proactive-recall planning and coverage audits — and
  `Memory.edges_since(user_id, since)` — edges learned after a date, filtered
  on `provenance.observed_at`, including superseded/quarantined material so
  change-detection sees everything. Host/admin surface; neither is an MCP tool
  (cross-user enumeration is not an agent capability). `Store` gains
  `list_users()` (non-abstract, like `forget_user`).

## 0.2.0

The launch release: the five capability gaps identified by an independent
landscape analysis, plus the display-brand and one-liner refresh.

- **branding**: display brand is capitalized **Veracium** in all prose (code
  identifiers stay lowercase); canonical one-liner applied to the PyPI summary,
  README lead, and MCP server description.
- **audit**: opt-in operation audit log — `Memory(audit=AuditLog(path))`
  appends one content-free JSONL line per operation (UTC timestamp, op,
  `user_id`, the op's counters; never memory text) covering
  remember/recall/answer/maintain/dispute/confirm/forget/export/import.
  Append-only, host-owned; sink failures never break memory.
- **feedback verbs**: `dispute(user_id, edge_id, reason=, actor=)` — the edge
  leaves every assertable surface immediately (non-destructive invalidation,
  reason `"disputed"`), and the dispute itself is remembered as an episode with
  actor and reason; `confirm(user_id, edge_id)` — refreshes validity, clears
  the possibly-stale flag, records the confirmation. `confirm` refuses
  non-assertable edges (elevating a claim by confirmation would be a laundering
  vector — affirmation is new evidence, use `remember()`). Neither is an MCP
  tool by design. Content-free `feedback` telemetry event.
- **forget** (compliance erasure): `Memory.forget(user_id)` irreversibly erases
  everything stored for a user — edges incl. superseded history and quarantined
  claims, episodes, wiki cache, counters. Distinct from lifecycle by design
  (`maintain()` never deletes; `forget()` never preserves). CLI:
  `veracium forget --user X` (confirmation prompt; `--yes` to skip).
  Deliberately not exposed over MCP — an agent-callable wipe verb is a standing
  prompt-injection target. `Store` gains `forget_user()` (non-abstract;
  custom stores keep working until they implement it).
- **portability**: JSONL export/import — `Memory.export_memory(user_id, path)`
  writes the complete store of record (all edges incl. superseded history and
  quarantined claims, all episodes, full provenance/disclosure);
  `import_memory(path, user_id=...)` is idempotent (existing ids skipped, never
  overwritten) and can remap users. CLI: `veracium export` / `veracium import`
  (store-only, no LLM needed). The wiki cache is not exported — it recompiles.
- **recall**: token-budget-aware context assembly — `recall(user_id, query,
  token_budget=N)` caps the rendered context (chars/4 heuristic; Veracium is
  tokenizer-agnostic). Trimming follows a documented priority: query-matched
  facts, then unverified-claim flags (never silently dropped below the facts
  they annotate), then the curated wiki (all-or-nothing), then recent episodes
  newest-first; best-effort minimum of one item. `Recall` gains
  `tokens_estimated`/`truncated`; the MCP `recall` tool exposes the parameter;
  the content-free telemetry `recall` event gains a `trimmed` counter.

## 0.1.7

- **security (ingest/gate/compile)**: closed the **system-event laundering**
  bypass — third-party text embedded inside a `SYSTEM`/`USER`-authored event (a
  triage verdict quoting a received email's subject, a summary of a message
  body) previously acquired the event's full trust and could surface as
  assertable user facts. `remember()` gains `derived_from`: declare
  `author=SYSTEM, derived_from=THIRD_PARTY` and trust is capped at the minimum
  of the two — edges cap at `use_only` (claims still quarantine), and the
  episode routes to the unverified channel at the gate *and* is excluded from
  the compiled wiki (episodes now route by third-party *influence*, not
  authorship alone). `Provenance` records both fields; MCP `remember` exposes
  the parameter; documented in `docs/concepts.md` ("Mixed provenance") and
  `SECURITY.md`. Found by the first production consumer on a real-mailbox
  backfill (130 laundered assertable edges); reported in
  `proposals/system-event-laundering.md` with the attack fixture now locked as
  a regression test.

- **ingest**: an `unparseable` extraction no longer leaves a history gap — the
  turn records a content-free placeholder episode ("(unprocessed <type> event —
  extraction returned no parseable JSON; content not retained)") with full
  provenance/`evidence_ref`. Deliberately not the raw event text: that would
  feed unmediated, possibly adversarial input straight into recall prompts.
- **_json**: among list fallbacks, `extract_json` now prefers a non-empty
  list of dicts (the shape of a bare triples array) over junk like `[]` or
  `[1, 2]` that happened to parse earlier in the prose.
- **graph**: `his`/`her` removed from the value-equivalence filler list — they
  can point at a third party ("his assistant" vs "her assistant") and so carry
  meaning; user-referential possessives (`my`/`our`/`their`) remain filler.
- **examples**: `openai_provider.py` — `OpenAIComplete` wraps any
  OpenAI-compatible chat-completions API (OpenAI, vLLM, Ollama's `/v1`), with
  per-role model mapping, honest structured-output fallback, and a memoized
  capability check. First outside contribution — thanks @vreddy-commits (#8).

## 0.1.6

- **security (compile)**: a third-party *inference* (`use_only`) is no longer fed
  into the compiled wiki. `recall()` places the wiki in the gate's assertable
  GROUNDED block, so a `use_only` fact reaching the wiki could be asserted through
  the wiki path — even though `gate.partition` (0.1.3) already routed such inferences
  to UNVERIFIED. `compile._grounded_inputs` now excludes `use_only` edges, mirroring
  the gate; the inference still shapes behavior via recall's unverified channel, only
  kept out of the assertable body. Completes the 0.1.3 fix (which covered only the
  subgraph path). Adds a unit lock (`test_grounded_inputs_excludes_use_only`).

## 0.1.5

- **ingest/_json**: a distill response whose first parseable JSON value is a
  *list* no longer crashes `remember()` (`'list' object has no attribute
  'get'`). `extract_json` now prefers the first JSON *object* — skipping prose
  debris like a stray `[]` before the real payload — and returns a bare array
  only as a fallback, which ingest normalizes as the triples payload with its
  wrapper omitted. Found by the robustness tier's first lmsys-chat-1m run
  (3/368 real turns crashed, all code-shaped inputs).
- **tests**: robustness tier Phase 2 — S4 (reinforcement ≠ duplication: a seeded
  sample of fact-yielding turns is re-ingested; new-edge growth is reported as a
  distribution) and S5 (every `maintain()` report must carry non-negative counts
  bounded by the store it ran over). Both soft signals; hard gates unchanged.

## 0.1.4

- **ingest**: an unparseable distill response (the extractor answering in prose —
  typically a refusal on jailbreak-shaped or degenerate input) no longer raises
  out of `remember()`; it records nothing and returns
  `{"episode": "", "facts": 0, "quarantined": 0, "unparseable": True}`, with a
  content-free `unparseable` counter in the telemetry `ingest` event. Found by
  the new robustness tier on its first run (7/19 fixture turns crashed).
- **tests**: new opt-in robustness tier (`tests/robustness/`,
  `VERACIUM_ROBUSTNESS=1`) — streams real, messy conversations through the write
  path and holds veracium's guarantees as hard invariants (no internal crashes,
  no cross-user leakage, no assertable third-party user-facts, well-formed
  persistence), plus soft distributions (yield, relation drift, latency,
  provider crash-rate). Ships a committed adversarial fixture corpus
  (`fixtures/messy.jsonl`); points at a locally exported lmsys-chat-1m for the
  full run. Reports are redacted — raw corpus text never appears.

## 0.1.3

- **gate/graph** (security): third-party *inferences* — real-looking user facts
  whose only support is third-party evidence (marked `use_only` at ingest) — were
  treated as grounded by the abstention gate and rendered as bare facts, so
  `answer()` would assert e.g. an employer learned solely from a received email.
  The `use_only` disclosure is now enforced everywhere it's read: the gate
  partitions these under UNVERIFIED (never asserted), and `render_edges` tags
  them `[third-party-reported; unconfirmed]` in recall context and the compiled
  wiki. New `Edge.assertable` / `Edge.use_only` properties expose the discipline.

## 0.1.2

- **graph**: reinforcement now matches paraphrased values ("dog named Ollie" /
  "dog Ollie" / "dog: Ollie") via order-preserving normalized-token comparison,
  instead of exact string equality — a re-stated fact whose extraction phrasing
  drifted between runs used to accumulate as a near-duplicate edge. Order still
  matters ("tea over coffee" ≠ "coffee over tea"), so functional supersession of
  genuinely new values is unaffected.

## 0.1.1

Reliability fixes surfaced by building the runnable demo notebook
(`examples/demo.ipynb`, new in this release):

- **selfcheck**: the abstention detector now recognizes natural abstention
  phrasings ("I don't have any confirmed record of ..."); previously a correct
  abstention could flakily score the check FAIL.
- **distill**: the extraction prompt now carries a one-clause gloss per relation
  (`Relation.desc`), disambiguating confusable pairs — employment occasionally
  landed under `works_on` instead of `works_as`, silently defeating supersession.
- **examples**: end-to-end scam-email demo notebook with real captured outputs
  and a Colab badge, linked from the README.

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
  provider (`veracium[anthropic]`).
- **MCP server** (`veracium[mcp]`): `remember` / `recall` / `answer` / `maintain`
  tools for any MCP-compatible agent.
- **Telemetry** (opt-in, off by default): anonymous, content-free usage
  statistics with explicit consent (`veracium telemetry`), a weekly in-process
  flush (`mem.flush_telemetry()`), and a whitelist-enforced content-free
  payload. See `docs/telemetry.md`.
- **Self-check** (`veracium selfcheck` / `mem.self_check()`): runs the load-bearing
  guarantees (supersession, injection defense, abstention) against a throwaway
  synthetic memory and self-scores them structurally (no LLM judge); the counters
  feed telemetry's content-free `selfcheck` event.
- **Diagnostics** (opt-in error reporting; `veracium diagnostics`): genuine errors are
  logged to a local, user-owned rotating file and re-raised unchanged; the log is
  sent for diagnosis only with consent (advance permission or a per-incident yes),
  redacted, previewable, anonymous, and bounded. No endpoint shipped. See
  `docs/diagnostics.md`.
- **Docs**: `docs/concepts.md`, `docs/api.md`, `docs/mcp.md`; acceptance eval
  (`tests/eval/`) holding the library to the research claims (5/5, 0 injection
  asserts on the live run).
