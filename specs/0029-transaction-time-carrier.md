# Feature spec: transaction-time carrier

Spec-Status: draft

*Candidate authored by dev (2026-08-31) on Quentin's word ("start 0029
spec"), grounded in the shipped store — every registry and totality claim
below is derived from the authoritative source (the `@store_mutator`
interface, the generated 0002 audit manifest, `DISPOSITIONED_REASONS`),
never a comment (the 0028 R1-1 lesson, front-loaded). Internal reviewer:
research (roles inverted from 0027). This is SUBSTRATE for the paused 0028
arc (the owner's hold-for-the-bigger-shape ruling) and for 0030
(time-relative classification): it records WHEN the store learned each
edge-state change, which nothing durable does today. See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | dev; internal review research |
| **Version** | **v4** — the pre-dispatch co-check fold (research's seal-check both-check, all three verified against code before folding): **F-A** the PER-WRITE KIND RULE — kind is a property of the write (prior row presence × serialization delta), not the site; no site→kind mapping can be total, and the import commit's presence-admitting raw replace is the reachable instance, so the machine-regeneration obligation is defined over WRITES; **F-B** the V-TOTAL sweep's interpolated-table blind spot pinned as a checkable property (event-owed edges writes name the table literally; the sweep scans interpolated forms — erasure's f-string DELETE the benign extant instance); **F-C** the fourth site cited at its UPDATE statement (sqlite.py:334). *Prior:* **v3** — the joint round-1 fold, on the owner's F1 ruling: RECONSTRUCTABLE STATE. F1: event payloads carry the edge's FULL canonical serialization (EdgeStateAt(K) derivable; the change-detection narrowing refused). F3: transaction-batch cursor — per-user `txn` allocated per event-emitting write transaction, `seq` the ordering authority, whole-batch reads (a cutoff can never split an atomic mutation; `recorded_at` demoted to telemetry). F4: V-TOTAL re-based on the FULL-STATE projection (any serialization change ⇒ event), and the FOURTH raw `UPDATE edges` site named (`_recompute_edge_row`, wrongly filed under `_upsert_edge_row` in v2 — it replaces valid_from/observed_at/confidence, which the 0027 digest never sees). F5: the schema pinned exactly (full snapshots dissolve the old/new-digest question). F8: version-header discipline. §6a re-seeded with the reviewer's eight joint scenarios. (v2 folded internal I-1/I-2.) |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research · dev |
| **External review** | REQUIRED — store schema + a new durable audit surface. Not yet sent |
| **Decision + date** | — |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0007 / 0013 / 0018** — schema versioning, additive migration, the
  release-migration orchestrator: `edge_event` registers as the v13 additive
  objects (the 0027 v12 pattern); constructor + all migrated shapes recorded.
- **0002** — the audit manifest: §4b's totality is DERIVED from the
  `@store_mutator` registry and the generated per-site write-target manifest
  — the same machinery that already enumerates every mutation site.
- **0003 / 0011 / 0022** — supersession, correction, revocation/reinstate:
  the state transitions whose transaction time this spec records
  (`invalidate`, `correct`'s plan application, `reinstate`).
- **0008** — `forget_user` erasure: events are user data and erase with the
  user, in the same transaction (the 0027 V-ERASE shape).
- **0005** — the import boundary: events are NOT exported (store-local audit;
  an importing store's knowledge of an edge begins at ITS import — recorded
  as that store's `created` event).
- **0014** — supersession receipts: untouched; receipts answer "was this
  operation committed", events answer "when did edge state change become
  known" — different carriers, non-overlapping writes (§4f states the
  non-disturbance obligation).
- **0027** — precedent only: the additive-table + accepted-shape-matrix
  migration pattern this spec repeats at v13.

---

## 1. Problem and motivation

The store is bi-temporal in VALID time only. `provenance.observed_at` exists
but is **caller-suppliable** (`Field(default_factory=utcnow)`) — a backdated
ingestion legitimately writes a past `observed_at`, so it is observation
metadata, not transaction time. `invalidated_at` is a valid-time endpoint
(0028 R1-2: a correction observed in June with `valid_from` March stamps the
prior's `invalidated_at` to March — WHEN the store learned of the
invalidation is recorded nowhere). Same-id mutations (`_upsert_edge_row` is
`INSERT OR REPLACE`; note-append, confirm, recompute) retain no prior
version and no timestamp of the change. Consequences, measured by 0028's
round-1 return: `known_as_of` is unimplementable; "full bitemporal audit" is
an overclaim; and a class of audit questions ("what did this store hold last
Tuesday?") has no honest answer.

**If we do nothing:** 0028 v2 (assertable history + bitemporal) stays
blocked on its R1-2 finding, and every future audit surface rebuilds this
carrier ad hoc.

**Alternatives rejected.** (a) *Row versioning* (every mutation writes a new
edge row version) — rejected: restructures the `edges` primary key, breaks
the 0007 shape machinery and every reader, maximal blast radius for the same
information. (b) *A `recorded_at` column on `edges`* — rejected: one column
cannot carry multiple transitions per edge (create → mutate → invalidate →
reinstate). (c) *Reusing `supersession_operations`* — rejected: receipts are
an idempotency/integrity carrier for ONE operation family; overloading them
couples 0014's frozen contract to every other mutator. Chosen: **an
append-only, store-minted EVENT LOG — one additive table, written in the
same transaction as the mutation it records.**

## 2. Field contracts touched

`grep -rn` at author time (re-run at implementation):

| field | read / written | documented contract | other consumers | preserves? |
|---|---|---|---|---|
| `edges` table (all columns) | UNCHANGED | — | everything | YES — no reader or writer of `edges` changes |
| `provenance.observed_at` | READ (contrast only) | caller-suppliable observation time | provenance, recency | YES — explicitly NOT the transaction axis (§4c) |
| NEW `edge_event(user_id, seq, txn, edge_id, kind, reason, state, recorded_at)` | WRITTEN | append-only store-minted STATE JOURNAL — `state` is the edge's full canonical serialization AFTER the mutation (F1: reconstructable, not merely dated); never exported; erases with the user | 0028 v2, 0030, future audit surfaces | additive; store-schema v13 |
| NEW `store_epoch` row (in `store_identity`'s pattern) | WRITTEN ONCE | the instant transaction-time recording began for this store | the fail-closed epoch rule (§4e) | additive |
| `Store` interface | EXTENDED | `+ edge_events(user_id, edge_id=None, until_txn=None)` + `edge_state_at(user_id, edge_id, until_txn)` (the EdgeStateAt(K) reconstruction) | 0028 v2 / 0030 / introspection | additive |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant** |
|---|---|---|---|---|---|
| `recorded_at` | n/a — STORE-MINTED, never a parameter | n/a | n/a | a caller attempting to supply it | **V-MINT** — no public surface accepts a transaction time; the store's clock writes it, monotone-guarded per user (§4c) |
| an event-log read with `until` before the store's epoch | — | non-datetime → typed refuse | — | probing pre-epoch knowledge | **V-EPOCH** — refuses (fail-closed), never fabricates "nothing was known" |
| the event `kind` on read | — | a kind outside the closed §4b set | — | — | **V-KIND** — closed vocabulary derived from the mutator surface; unknown kinds refuse at read (the store never writes one) |
| a crash between mutation and event | — | — | — | — | **V-ATOMIC** — same transaction: both commit or neither |

### 2c-ii. Assertions about reach — REQUIRED

| claim | invariant |
|---|---|
| "every edge-state mutation writes its event in the same transaction" | **V-TOTAL** — derived from the authoritative mutator registry + per-site write-target manifest, not a hand list; the gate diffs event-writing sites against every site that writes the `edges` table |
| "the log is append-only" | **V-APPEND** — no UPDATE/DELETE path exists except §4f erasure; `seq` is monotone per user |
| "events change no existing behavior" | **V-COMPAT** — with no consumer reading the log, every existing surface is byte-identical (frozen pre-feature oracle, the 0027 V10 pattern) |
| "events are trust-inert and store-local" | **V-INERT** — no trust class, never in recall/context/export/MCP; the 0005 boundary |
| "erasure is total" | **V-ERASE** — `forget_user` deletes the user's events in the same transaction |

## 3. Trust-class matrix — REQUIRED, blocking

| entity | trust class | how this spec touches it |
|---|---|---|
| an `edge_event` row | **none** — audit metadata | records that a state change happened and when the store learned it; carries a content DIGEST, never content; never evidence, never assertable, never rendered |
| the `edges` table | unchanged | not one reader or writer changes |
| `recorded_at` | store fact | minted by the store clock; no caller influence |

**Load-bearing statement:** the event log answers exactly one question —
*when did this store's knowledge change* — and answers it to OPERATORS and
FUTURE SPECS (0028 v2, 0030), never to the model or a principal surface.
Policy: `REQUIRED`, not `REBUILDABLE` — an audit record is not derivable
from current state, so its absence is damage, not drift (the inverse of
0027's regenerable index, stated so the schema police the difference).

## 3b. Authorization and scope — full specs only

The log is an OPERATOR/substrate surface (the `export`/`forget` row's shape,
0020 §2): `edge_events` takes no principal and is not reachable from any
principal-bearing or model-facing path in v1. When 0028 v2/0030 consume it
through principal-bearing surfaces, THEIR specs own the 0020/0021
composition (the 0028 R1-5 lesson is theirs to answer on this foundation —
stated here so the seam is named, not discovered).

## 4. Behaviour

### 4a. The event model — a reconstructable state journal (F1, F3, F5)
One row per edge-state transition, written by the store, inside the
mutation's transaction. The schema, pinned EXACTLY (F5 — no deferred
choices):

```sql
CREATE TABLE edge_event (
    user_id     TEXT    NOT NULL,
    seq         INTEGER NOT NULL,   -- per-user, monotone: THE ordering authority
    txn         INTEGER NOT NULL,   -- per-user transaction batch id (F3)
    edge_id     TEXT    NOT NULL,
    kind        TEXT    NOT NULL,   -- closed set, §4b
    reason      TEXT,               -- non-NULL iff kind='invalidated'; registry-validated
    state       TEXT    NOT NULL,   -- the edge's FULL canonical serialization AFTER
                                    -- this mutation (model_dump_json, the shipped
                                    -- None-omitting form) — the reconstruction payload
    recorded_at TEXT    NOT NULL,   -- ISO-8601 UTC, store-minted; TELEMETRY, not order
    PRIMARY KEY (user_id, seq)
);
CREATE INDEX ix_edge_event_lookup ON edge_event(user_id, edge_id, seq);
CREATE INDEX ix_edge_event_txn    ON edge_event(user_id, txn);
```

- **`state` is the payload rule (F1):** every event carries the complete
  post-mutation serialization. Old values are never lost to an overwrite —
  the previous event's `state` holds them. No digest columns: any digest is
  derivable from `state` (the v2 old/new-digest question DISSOLVES).
- **`txn` is the atomicity carrier (F3):** one event-emitting store write
  transaction allocates ONE per-user `txn` (max+1, under the store lock,
  in-transaction); every event that transaction emits shares it. A
  supersession that invalidates A and creates B is ONE `txn` — a cutoff can
  include or exclude it only WHOLE, so no read can reconstruct a state that
  never existed. The composite cursor is `(recorded_at, txn)` for display;
  **`seq`/`txn` are the ordering authority** — `recorded_at` is store-minted
  wall-clock TELEMETRY (two transactions may legitimately share an instant;
  nothing orders by it).

### 4b. The closed kind set — the GATE is authoritative; this table is illustrative
Kinds cover exactly the operations that write the `edges` table. The
AUTHORITATIVE derivation is V-TOTAL's gate — the `@store_mutator` registry ×
the generated 0002/0021 per-site write-target manifests, swept over RAW SQL
writes as well as `_upsert_edge_row` callers — and the printed table below
is ILLUSTRATIVE of what that derivation yields at authoring time
(internal-I-2: a hand-transcribed row for a pure episodes-writer proved the
snapshot was authored, not derived — the row is removed and this obligation
recorded). **Regenerate-at-implementation obligation:** the moment code
exists, this table is machine-regenerated from the gate's own derivation
and byte-bound to it, so the printed list can never drift from what the
gate enforces.

The TRIGGER basis is the FULL-STATE projection (F4): an event is owed
whenever the edge's complete canonical serialization changes — never a
narrower digest. (v2's basis was the 0027 semantic-text digest
{subject,relation,object,note}; the joint reviewer showed
`_recompute_edge_row` — the FOURTH raw `UPDATE edges` site, wrongly filed
under `_upsert_edge_row` in v2 — replaces `valid_from`/`observed_at`/
`confidence` without touching that digest, and same-id replaces can move
disclosure or scope provenance the same way. Classification-relevant
changes must never be digest-invisible.)

| kind | written by (site, from the manifest) | `state` payload |
|---|---|---|
| `created` | `add_edge`; `apply_supersession_plan` (insert_incoming, absorption survivor); the import commit's replace when NO row was present | the new edge, serialized |
| `mutated` | ANY same-id row write whose full-state serialization changed: `_upsert_edge_row` (note-append, absorption restate, counter-bearing re-upserts), `confirm_edge`'s raw json rewrite (sqlite.py:191), **`_recompute_edge_row`'s raw rewrite (statement at sqlite.py:334 — the fourth site)**; the import commit's replace when a row WAS present and the serialization changed (F-A) | the post-mutation edge, serialized |
| `invalidated` | `invalidate_edge` / `_invalidate_edge_row` (:252; plan invalidations, lifecycle expiry, dispute, revocation sweep) | the post-invalidation edge, serialized; `reason` — validated against `DISPOSITIONED_REASONS`, the AUTHORITATIVE seven; an unregistered reason refuses the WRITE |
| `reinstated` | `_reinstate_edge_row` (:300; 0022 revocation lift) — the pre-reinstatement `invalidated_at`/`reason` live in the PRIOR event's `state`, which is exactly the F1 point: reinstatement ERASES them from the row, and only the journal can answer a cutoff between revocation and reinstatement | the post-reinstatement edge, serialized |
| `erased` | NOT a kind: erasure deletes the user's events (§4f); a tombstone would defeat erasure | — |

**KIND IS A PROPERTY OF THE WRITE, NOT THE SITE (internal F-A —
research's both-check, the round-1 fourth-site class one level up):** a
site can yield EITHER kind depending on prior row presence, so no site→kind
mapping can be total — `created` when no row existed for the id,
`mutated` when one did and the serialization changed. The load-bearing
instance: `commit_outcome_import_plan` writes a raw
`INSERT OR REPLACE INTO edges` (sqlite.py:1400) NOT via `_upsert_edge_row`,
and its preflight ADMITS an already-present destination
(`expected_destination_state` refuses only a presence MISMATCH — an
`expect_present=True` import proceeds to the replace), so a changed-bytes
same-id import is caller-reachable and owes a `mutated` event. The
machine-regeneration obligation is defined over WRITES accordingly:
per-write prior-presence + serialization-delta decide the kind; the table
above illustrates sites, the rule decides.

**The v2 counter-silence is WITHDRAWN under the full-state basis (F4
supersedes internal-I-1's disposition):** counter and confidence rewrites DO
change the full-state serialization and now emit `mutated` events — under
F1's ruling every reconstructable-state change is journaled, and consumers
that care only about classification-relevant fields filter on read.
(`append_outcome_if_head` remains an EPISODES-writer and emits nothing —
that half of I-1 stands.)

### 4b-ii. Reconstruction — EdgeStateAt (F1)
`edge_state_at(user_id, edge_id, until_txn)` = deserialize the `state` of
the LAST event for the edge with `txn ≤ until_txn`; no such event and the
edge absent from the journal → `None` for a post-epoch cutoff, REFUSAL for
a pre-epoch one (§4e — the store cannot speak for time before it recorded).
Because every event carries the full serialization, reconstruction is a
single lookup — no delta replay, no fabrication, and the recompute/
reinstate erasures the joint review named are recoverable by construction.
What 0029 reconstructs is "the belief the store HELD at K"; whether it may
be ASSERTED now is 0030's classification under the joint F2 rule — current
revocation and current scope are OUTER CAPS applied by consumers, never
time-traveled by this carrier (§8).

A mutator added later that writes `edges` without declaring its event
handling fails **V-TOTAL**'s gate — the same generated-manifest mechanism
that already refuses an undispositioned mutation site (0002).

### 4c. Minting discipline
`recorded_at` is minted INSIDE the store, at write, from the store's clock.
No public API accepts it; `observed_at` (caller-suppliable) is contrast, not
input. This is the load-bearing difference from every existing timestamp in
the system, and it is what makes the axis TRUSTWORTHY as transaction time.

### 4d. Read API
- `Store.edge_events(user_id, *, edge_id=None, until_txn=None) ->
  [EdgeEvent]` — typed rows in `seq` order; `until_txn` bounds by WHOLE
  transaction batches (F3: a batch is included or excluded entire, never
  split). A cutoff earlier than the store epoch REFUSES (§4e).
- `Store.edge_state_at(user_id, edge_id, until_txn) -> Edge | None` — the
  §4b-ii reconstruction.
- Cutoff tokens are `txn` values; a caller holding a `(recorded_at, txn)`
  composite cursor uses the `txn` component for every read decision.
- No recall/context/MCP surface; `introspect` MAY gain a counts-only
  summary (open, §10).

### 4e. Schema, migration, epoch
Additive v13: the `edge_event` table (§4a's pinned DDL, BOTH indexes) +
the epoch row, registered per 0013/0018 with the FULL
accepted-shape matrix (constructor + every migrated form — the 0027 v12
inheritance pattern, all shapes carrying the additive diff). **No backfill
and no fabricated history:** at migration the store mints its
transaction-time EPOCH; every pre-existing edge gets NO retroactive events.
`edge_events(until_txn=K)` (or `edge_state_at`) with a pre-epoch cutoff refuses — the store cannot say what
it knew before it started recording, and fail-closed beats fabrication
(V-EPOCH). Down-migration: `DROP TABLE` (reversible; the audit axis is lost
and says so — §7).

### 4f. Erasure, receipts, atomicity
`forget_user` deletes the user's `edge_event` rows in the SAME transaction
as the edges (V-ERASE; the 0027 pattern). `supersession_operations` receipts
are untouched — no shared columns, no shared writes; the §4b `created`/
`invalidated` events for a plan application ride the plan's existing
transaction, beside (not through) its receipt. Every event write shares its
mutation's transaction; a fault injected between mutation and event commit
leaves NEITHER (V-ATOMIC; the seam joins the 0013 fault-injection gate
family).

## 5. Regime analysis

- **No consumer (v1 shipped state):** write-only log; every read surface
  byte-identical (V-COMPAT). Cost: one row + one digest per edge mutation.
- **High-churn user:** log grows with mutation count, not edge count;
  unbounded by design (an audit log); erasure is the one shrink; a retention
  policy is future work (§10), never silent truncation.
- **Migrated store:** epoch-bounded knowledge; pre-epoch queries refuse.
- **Import:** imported edges get `created` events at import time — the
  importing store's knowledge began there (honest, and stated).
- **Clock anomalies:** monotone guard per user (§4a); ordering authority is
  `seq`.

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **V-TOTAL** every site that writes `edges` writes its §4b event in the same transaction, and the trigger basis is the FULL-STATE serialization (any change ⇒ event; nothing classification-relevant is digest-invisible — F4) — DERIVED from the mutator registry + write-target manifest swept over RAW SQL (four raw sites today, `_recompute_edge_row` included); a new site without an event ruling fails the gate | `test_every_edge_writing_site_carries_an_event_ruling` | CI |
| **V-ATOMIC** mutation and event commit atomically; injected fault between them → neither persisted | `test_event_and_mutation_are_one_transaction` | CI |
| **V-APPEND** no code path updates or deletes an event except erasure; `seq` strictly monotone per user | `test_event_log_is_append_only_and_monotone` | CI |
| **V-RECON** `edge_state_at(user, edge, K)` returns byte-exactly the serialization the edge held after the last `txn ≤ K` — driven across the recompute-erasure and reinstate-erasure cases the joint review named (the row forgets; the journal must not) | `test_edge_state_at_reconstructs_byte_exact` | CI |
| **V-BATCH** one event-emitting write transaction = one `txn`; a multi-edge mutation (supersession's invalidate-A + create-B) shares it, and every `until_txn` read includes or excludes the batch WHOLE — no reachable cutoff reconstructs a state that never existed; two batches sharing a `recorded_at` stay distinct by `txn` | `test_transaction_batches_never_split` | CI |
| **V-MINT** no public surface accepts a transaction time; `recorded_at` is store-minted; the monotone guard holds under a backwards clock step | `test_recorded_at_is_store_minted_and_monotone` | CI |
| **V-KIND** the kind vocabulary is closed and derived; `invalidated` events validate `reason` against `DISPOSITIONED_REASONS` (all SEVEN); an unregistered reason refuses the write | `test_event_kinds_closed_and_reasons_authoritative` | CI |
| **V-EPOCH** `until` before the store epoch refuses; a migrated store fabricates no pre-epoch knowledge | `test_pre_epoch_queries_fail_closed` | CI |
| **V-ERASE** after `forget_user`, zero events for the user remain (same transaction) | `test_forget_user_erases_events` | CI |
| **V-INERT** events reach no recall/context/export/MCP surface; the schema policy is REQUIRED (absence = damage, not drift) | `test_events_are_store_local_and_required` | CI |
| **V-COMPAT** with no consumer, every existing surface reproduces the frozen pre-feature oracle byte-identically | `test_no_consumer_behavior_identical` | CI |

### 6a. Acceptance measurement — REQUIRED, FINITE

A CORRECTNESS gate (exact expected event logs), deterministic, no model:
- **Corpus:** `tests/eval/edge_events/` — a frozen scripted-scenario
  manifest (pinned ids, per-position instants — the 0027 v2.2 topology
  discipline). The skeleton is the JOINT reviewer's eight scenarios,
  verbatim as the shared 0029/0030 acceptance surface, each with its exact
  expected event sequence AND its `edge_state_at` reconstruction:
  1. backdated correction with K before and after its recorded transaction;
  2. source revocation then reinstatement, K between them (the erased
     `invalidated_at`/`reason` recovered from the journal);
  3. `valid_from` changed by recompute after K (the fourth-site case);
  4. same-text replacement changing disclosure or scope provenance (the
     digest-invisible class, now full-state-visible);
  5. multi-edge supersession with a cutoff at the transaction boundary
     (whole-batch, both sides);
  6. two transactions sharing one `recorded_at` (txn distinguishes);
  7. a later correction/dispute/revocation applied to an earlier snapshot
     (0029 reconstructs the held belief; the 0030/F2 caps govern
     assertion — the JOINT half of the scenario);
  8. a malformed edge hidden from the querying principal (0029 journals it
     like any state; 0030's outer-visibility rule owns the classification).
  Plus the v2 scenarios retained: create/supersede/confirm/note-append/
  absorb/dispute/expiry/import/erase.
- **Pass criteria (pre-committed):** (1) exactness — every scenario's event
  sequence AND every named reconstruction equal the expected values, 100%;
  (2) scenario 1 shows the invalidation's transaction at the CORRECTION's
  write, not its valid-time — the carrier answering what 0028 could not;
  (3) V-ATOMIC's injected-fault case leaves neither write; (4) scenario 5's
  boundary cutoffs never observe a half-applied supersession.
- Recorded results land in `## Review closure` at acceptance. (Correctness
  gate — deterministic pass/fail; the figure-disclosure question does not
  arise, and the no-public-number habit stands anyway.)

## 7. Failure modes and reversibility

- **Fully reversible:** additive table + epoch row; `DROP TABLE` returns
  the v12 store; what is lost is the audit axis itself, which the drop
  makes visible (the epoch goes with it).
- **Log growth:** unbounded by design; erasure shrinks; retention is §10.
- **Clock trouble:** order survives via `seq`; wall-clock quality degrades
  visibly (equal `recorded_at` runs), never silently reorders.
- **The absent-consumer risk:** a write-only log can rot unread; §6a's gate
  reads it on every CI run by construction.

## 8. Claims and limits

- **Claim:** after v13, every edge-state change carries a durable,
  store-minted transaction time, atomically recorded, epoch-bounded, erasure-
  complete. *Limit:* knowledge before the epoch is unrecorded and REFUSES;
  episode/wiki state is out of scope (§10); this spec provides the CARRIER
  only — historical assertability (0030) and query semantics (0028 v2) build
  on it, and their claims are theirs.
- **Field contrast:** the tracked systems' as-of implementations (GENOME,
  Mem0-Platform) run valid-time interval math with no transaction axis at
  all; an auditable "what did the system know at T" is absent field-wide.
  This carrier + 0030 is the substrate for the position none of them can
  take. *(Design-read fidelity, research's five-system basis.)*
- *Where we may overstate:* "every edge-state change" is exactly §4b's
  derived table — the reviewer should attack the DERIVATION (a site that
  writes `edges` outside the manifest's sight), not take the enumeration on
  faith.

## 9. Brief for the external reviewer

The spine: a store-minted, append-only, epoch-bounded transaction-time log,
written in the mutation's own transaction, derived-total over the mutator
surface. Attack hardest:
1. **V-TOTAL's derivation.** Find an edge-state write the registry/manifest
   machinery cannot see (a raw SQL site, a future mutator, an import path)
   — the gate's blind spot is the spec's blind spot. The standing lesson,
   now twice-proven: the internal round surfaced three raw `UPDATE edges`
   sites, and the JOINT round found the FOURTH (`_recompute_edge_row` —
   its UPDATE statement at sqlite.py:334) that the "three sites" claim
   itself had missed — grep the WRITES, not the callers' names, and never
   trust a counted list over the sweep (the four statements today: :191,
   :252, :300, :334). AND the sweep must resolve INTERPOLATED table
   targets (internal F-B): erasure writes `f"DELETE FROM {table}"`
   (sqlite.py:1775), invisible to a literal `FROM edges` grep — benign
   today (erasure is deliberately not-a-kind), but the V-TOTAL derivation
   either resolves f-string table names or pins "every edges write names
   the table literally" as its own checkable property. This spec pins the
   LATTER for the event-owed writes, and the sweep additionally scans
   interpolated forms to enforce it.
2. **V-ATOMIC under real fault schedules.** The event rides the mutation's
   transaction — inject at every seam (the 0013 gate family's method) and
   find a schedule where one lands without the other.
3. **The epoch rule's honesty.** Is fail-closed-before-epoch consistently
   enforced across every read path, and does the migration mint exactly one
   epoch under crash-retry?
4. **§4b's `mutated` trigger under the FULL-STATE basis.** Can any same-id
   write change the row while leaving the complete canonical serialization
   byte-identical (it should be impossible by definition — but attack the
   serialization's canonicality: field ordering, None-omission, float
   formatting), and does the whole-serialization trigger over-fire anywhere
   a consumer would treat as noise?

## 10. Open questions

- **Episode/wiki events:** out of v1 (edges are the trust-bearing state);
  extend later?
- ~~`content_mutated` payload shape~~ — RESOLVED at v3 (F1/F5): full-state
  payloads; digests derivable; no packing question remains.
- **Retention:** unbounded v1; a future retention policy must never
  silently truncate (an explicit, evented compaction if ever).
- **`introspect` counts-only summary:** expose event counts to operators?
- **0030 composition:** which event kinds feed assertable-as-of-T (0030's
  call, on this carrier).

## Review closure

*n/a — draft; populated before `accepted`, one row per external finding,
evidence openable/executable.*
