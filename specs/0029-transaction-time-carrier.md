# Feature spec: transaction-time carrier

Spec-Status: accepted

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
| **Version** | **v9** — one carrier correction, found by EXECUTING at the seam-model adoption (the round's own lesson applied to this spec's own text): §4a described the `state` payload as "the shipped None-omitting form" — FALSE. Executed: `model_dump_json` serializes Nones (`invalidated_at: null` present; 18 keys at authoring). The parenthetical now states the executed truth and names the dead claim, because an implementer following the old text would have written an omitting serializer and broken byte-fidelity (V-RECON/V-VERBATIM) against every shipped payload. Also this fold: the RUNNABLE JOINT SEAM MODEL landed (`specs/evidence/0029-0030/seam_model/`, 27 tests in the ordinary suite) — dev halves execute F4's both-schedule allocation and the F1/X-1 restriction derivation against the real sweep; research halves (mutation-tested their side, mutation 1 re-proven at adoption) execute the F3 adapter and five-leg binding; rule zero throughout (every assertion carries an asserted negative control). *Prior:* **v8** — the joint round-3 fold, dev's half (external F4): the allocation LOCKING SCHEDULE specified — v7 said "inside the write transaction" without saying WHEN the writer lock is acquired, and the reviewer executed the gap (two DEFERRED transactions both read max=1, both allocate txn 2, the second dies `database is locked` — contradicting §6a's zero-refusals cell). §4a now REQUIRES **`BEGIN IMMEDIATE` before any allocation read** (the shipped house pattern, cited: 0022 R3-1's "`BEGIN IMMEDIATE`, never `with conn:`" at revocation.py:6, and schema_version.py:1501's lock-before-the-reads); `txn`, `seq`, and the batch `recorded_at` are all minted AFTER that lock; a busy refusal retries the WHOLE transaction under the 0007 §4c `busy_timeout` discipline (bounded wait, then refuse loudly — never a partial batch); the `(user_id, seq)` PK is explicitly demoted to backstop-ONLY (it enforces neither batch ownership nor one-timestamp-per-batch — the schedule does). §6a scenario 10 re-pinned: the IMMEDIATE schedule is the positive case (distinct whole batches, ZERO allocation refusals); the DEFERRED schedule joins as the NEGATIVE control, reproducing the reviewer's same-max/busy failure. *Prior:* **v7** — C-4's 0029 half (research's re-cross-check of v6; the audit-the-fix's-own-state class, third instance today): C-2 made row identity AUTHORITATIVE but the payload EMBEDS its own `id`/`user_id` copy, and nothing required the two halves to agree — so §4b-ii and V-VERBATIM now state the payload's embedded identity is **UNVERIFIED at this surface**: the consumer MUST verify payload-vs-row agreement (0030's V-CARRIER-AGREES; current-leg disagreement fails hidden so a foreign payload's scope fields never reach a visibility decision). Without the clause, "identity is authoritative from the row" reads as "the store reconciled them," which it deliberately does not. *Prior:* **v6** — the round-2 CROSS-CHECK fold (research's C-1/C-2/C-3, both blocking findings AT THE SEAM — text-vs-mapping, invisible to either seat alone): **C-2** `RawEdgeState` gains `edge_id`/`user_id` sourced from the event ROW columns, never the payload — identity binding becomes parse-independent, so a corrupt payload is correctly BOUND first, then refused (V-VERBATIM sharpened: the PAYLOAD is verbatim; the IDENTITY is authoritative from the row). **C-1** the parse is OWNED: `state` is TEXT, parsing is the CONSUMER's (0030), and a parse failure is a consumer-classified outcome (MALFORMED/SCOPE_HIDDEN per 0030's rules), never a 0029 read error — the journal-outlives-its-writer argument applies to the text as much as the field values, and neither spec had assigned the step between text and mapping. **C-3** §4b states generally that the event `reason` COLUMN records the EVENT's reason and is never a classifier input (the state's own `invalidation_reason` lives inside the payload). §4e adopts the sharper epoch_txn=0 framing (pre-epoch `until_txn < 0` is unsatisfiable over non-negative txns). *Prior:* **v5** — the joint round-2 fold, dev's half (F1, F5 carrier half, F6, F8a): **F1** EPOCH BASELINE SNAPSHOTS — the v13 migration journals every pre-existing edge's state as found, one `baseline` batch per user (the user's EPOCH TXN); §4e re-scoped from "no backfill" to "no fabricated history" — the baseline records the state actually present when journaling began, and nothing before it is ever synthesized. **F6** the epoch becomes a TXN value (pre-epoch = `until_txn < epoch_txn(user)`, same integer domain, mechanically comparable; the §2c cutoff row re-typed); txn/seq allocation moved to DATABASE-level serialization (max+1 inside the writing transaction under the DB's single-writer lock — the instance-local Python lock is named insufficient across two `SqliteStore` instances; the `(user_id, seq)` PK is the refusing backstop); `recorded_at` minted ONCE per batch. **F5 (carrier half)** `edge_state_at` returns a RAW snapshot carrier — journal payload verbatim, no deserialization at the 0029 surface; validation belongs wholly to the consumer (0030 rules 3–4, seam S4) because an append-only journal can outlive the model that wrote it. **F8a** carrier sweep — the journal is CONTENT-BEARING (the §3 "digest, never content" row and §5 "one digest" cost were v2 residue); data-handling and retention stated honestly. §6a gains the migrated-edge-at-epoch and concurrent-allocation scenarios (the other five round-2 joint cases live in 0030 §6a on the shared corpus). New invariants V-BASELINE, V-TXN-ALLOC, V-VERBATIM. *Prior:* **v4** — the pre-dispatch co-check fold (research's seal-check both-check, all three verified against code before folding): **F-A** the PER-WRITE KIND RULE — kind is a property of the write (prior row presence × serialization delta), not the site; no site→kind mapping can be total, and the import commit's presence-admitting raw replace is the reachable instance, so the machine-regeneration obligation is defined over WRITES; **F-B** the V-TOTAL sweep's interpolated-table blind spot pinned as a checkable property (event-owed edges writes name the table literally; the sweep scans interpolated forms — erasure's f-string DELETE the benign extant instance); **F-C** the fourth site cited at its UPDATE statement (sqlite.py:334). *Prior:* **v3** — the joint round-1 fold, on the owner's F1 ruling: RECONSTRUCTABLE STATE. F1: event payloads carry the edge's FULL canonical serialization (EdgeStateAt(K) derivable; the change-detection narrowing refused). F3: transaction-batch cursor — per-user `txn` allocated per event-emitting write transaction, `seq` the ordering authority, whole-batch reads (a cutoff can never split an atomic mutation; `recorded_at` demoted to telemetry). F4: V-TOTAL re-based on the FULL-STATE projection (any serialization change ⇒ event), and the FOURTH raw `UPDATE edges` site named (`_recompute_edge_row`, wrongly filed under `_upsert_edge_row` in v2 — it replaces valid_from/observed_at/confidence, which the 0027 digest never sees). F5: the schema pinned exactly (full snapshots dissolve the old/new-digest question). F8: version-header discipline. §6a re-seeded with the reviewer's eight joint scenarios. (v2 folded internal I-1/I-2.) |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research · dev |
| **External review** | COMPLETE — four joint rounds (1–3 RETURN, folded same-day; round 4 ACCEPT). Every round's verdict verbatim in the round archives' prior-rounds/ |
| **Decision + date** | ACCEPTED — externally, joint round 4, 2026-09-01 ("Accept 0029 v9 on specification substance"). The same verdict returned 0030 v15 + the joint seam and ruled "the pair should not advance together yet" — so IMPLEMENTATION remains coupled to 0030's acceptance and starts only on Quentin's word |
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
| NEW `edge_event(user_id, seq, txn, edge_id, kind, reason, state, recorded_at)` | WRITTEN | append-only store-minted STATE JOURNAL — `state` is the edge's full canonical serialization AFTER the mutation (F1: reconstructable, not merely dated); never exported; erases with the user | 0028 v2, 0030, 0031 Phase B reversal (its §4c-iii reads the journal — the seam's SECOND consumer, so the read contract freezes here, not per-consumer), future audit surfaces | additive; store-schema v13 |
| NEW `store_epoch` row (in `store_identity`'s pattern) | WRITTEN ONCE | the INSTANT journaling began — display/telemetry; the MECHANICAL epoch is per-user, a TXN value (§4e): the user's baseline batch txn, `0` for users whose whole life is journaled | the fail-closed epoch rule (§4e) | additive |
| `Store` interface | EXTENDED | `+ edge_events(user_id, edge_id=None, until_txn=None)` + `edge_state_at(user_id, edge_id, until_txn)` — returns the RAW snapshot carrier (§4b-ii), never a validated `Edge` | 0028 v2 / 0030 / introspection | additive |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant** |
|---|---|---|---|---|---|
| `recorded_at` | n/a — STORE-MINTED, never a parameter | n/a | n/a | a caller attempting to supply it | **V-MINT** — no public surface accepts a transaction time; the store's clock writes it, monotone-guarded per user (§4c) |
| the `until_txn` cutoff | `None` → unbounded (whole log) | non-integer or negative → typed refuse (the cutoff domain is txn integers — F6; no datetime is ever a cutoff) | — | probing pre-epoch knowledge: `until_txn < epoch_txn(user)` | **V-EPOCH** — a pre-epoch cutoff refuses (fail-closed), never fabricates "nothing was known"; the comparison is integer-to-integer in ONE domain, mechanically total |
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
| an `edge_event` row | **none** — audit record | records that a state change happened, when the store learned it, and the edge's FULL post-mutation serialization — the journal is CONTENT-BEARING (F8a; the v2 "digest, never content" claim died with the v3 full-state ruling and this row now says so): every payload is user content at rest, held to the same data-handling class as the `edges` table itself; never evidence, never assertable, never rendered |
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
                                    -- this mutation: the shipped model_dump_json form,
                                    -- EXECUTED not recalled (v9): Nones PRESENT
                                    -- (invalidated_at: null serializes), 18 keys at
                                    -- authoring — the earlier "None-omitting" claim
                                    -- was false — the reconstruction payload
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
- **`txn` is the atomicity carrier (F3), allocated at the DATABASE level
  (F6) under a SPECIFIED LOCKING SCHEDULE (round-3 F4):** one
  event-emitting store write transaction allocates ONE per-user `txn` —
  and the writer lock is acquired FIRST: the transaction opens with
  **`BEGIN IMMEDIATE`**, and only then are `max(txn)` and `max(seq)`
  read, the new values allocated, and the batch `recorded_at` minted
  (one clock read, after the lock). "Inside the write transaction" alone
  is NOT enough — under SQLite's default DEFERRED transactions the writer
  lock arrives at the first write, so two connections can both read the
  same maxima and the second dies `database is locked` mid-batch (the
  round-3 reviewer executed exactly this). This is the shipped house
  pattern, not an invention: 0022 R3-1 pinned "`BEGIN IMMEDIATE`, never
  `with conn:`" (revocation.py:6), and the 0007 version gate takes the
  lock BEFORE its reads (schema_version.py:1501). A busy refusal at
  BEGIN retries or refuses the WHOLE transaction under the 0007 §4c
  `busy_timeout` discipline — bounded wait, then a loud typed refusal;
  never a partially-allocated batch, never a re-used clock read. An
  instance-local Python lock remains INSUFFICIENT and named so: two
  `SqliteStore` instances on one file each hold their own lock (the
  round-2 finding). The `(user_id, seq)` primary key is a BACKSTOP ONLY —
  it enforces neither unique batch ownership nor one-timestamp-per-batch
  (the schedule does); it exists so any defect in the schedule becomes a
  constraint refusal, never a silent duplicate. Every event that
  transaction emits shares its `txn` and its `recorded_at`. A
  supersession that invalidates A and creates B is ONE `txn` — a cutoff can
  include or exclude it only WHOLE, so no read can reconstruct a state that
  never existed. The composite cursor is `(recorded_at, txn)` for display;
  **`seq`/`txn` are the ordering authority** — `recorded_at` is store-minted
  wall-clock TELEMETRY (two transactions may legitimately share an instant;
  nothing orders by it).

### 4b. The closed kind set — the GATE is authoritative; this table is illustrative
Kinds cover exactly the operations that write the `edges` table, plus the
one non-mutator kind: `baseline`, written only by the v13 migration and
recording found state rather than a mutation (F1 — it is in the closed set
so V-KIND stays total, and the gate proves no runtime site can emit it). The
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
| `baseline` | ONLY the v13 migration (§4e) — never a runtime mutator; one event per pre-existing edge, all of a user's baselines in ONE batch (the user's epoch txn) | the edge's state AS FOUND when journaling began, serialized; `reason` column NULL (the found state's own `invalidation_reason`, if any, lives inside `state` — the column records the EVENT's reason, and a baseline has none) |
| `erased` | NOT a kind: erasure deletes the user's events (§4f); a tombstone would defeat erasure | — |

**THE `reason` COLUMN IS THE EVENT'S REASON, NEVER A CLASSIFIER INPUT
(C-3):** the column records why THIS EVENT happened (non-NULL iff
kind=`invalidated`); the state's own `invalidation_reason` — what 0030
classifies on — lives inside the `state` payload. The two carry the same
string only on the `invalidated` event itself; on every later event for
that edge they diverge (column NULL, payload still carrying the reason).
Wiring the column into a classifier is an adjacent-name error that reads
correct in review — and with F1's baselines it is SYSTEMATIC, not
occasional: a migrated INACTIVE edge's `baseline` event carries column
NULL while its payload carries the found `invalidation_reason`, so a
column-wired classifier would silently read the ENTIRE pre-upgrade
inactive population as active-with-no-reason — over-assertion at scale,
producing a plausible answer rather than an error. 0030 pins this as
V-COLUMN-NOT-INPUT; the seam manifest carries the same line on the
consumer side.

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

### 4b-ii. Reconstruction — EdgeStateAt (F1) — returns a RAW carrier (F5)
`edge_state_at(user_id, edge_id, until_txn)` = the `state` payload of the
LAST event for the edge with `txn ≤ until_txn`, returned as a **RAW
SNAPSHOT CARRIER** — `RawEdgeState(edge_id, user_id, state: str, txn,
seq, kind, recorded_at)`. **Identity comes from the event ROW columns,
never from the payload (C-2):** binding a snapshot to its envelope must
not depend on payload integrity — a corrupt payload is correctly BOUND
first, then refused by the consumer, and a mismatched-id probe stays
distinguishable from a parse failure. **`state` is TEXT, verbatim
(C-1):** the journal payload is never deserialized into a validated
`Edge` at this surface, and PARSING IT IS THE CONSUMER'S STEP — a parse
failure (malformed JSON, truncation, at-rest corruption, a payload from
an older model) is a consumer-classified outcome under 0030's rules
(MALFORMED, or hidden-fail-closed), NEVER a 0029 read error. A future
implementer reading only this spec must not assume a mapping crosses
the seam: text does. **And the payload's own embedded `id`/`user_id`
copy is UNVERIFIED at this surface (C-4):** the row is authoritative,
but 0029 never reconciles the two halves — a payload holding edge B's
content can sit under edge A's row (at-rest corruption, exactly what
the raw carrier exists to survive), so the CONSUMER must verify
payload-vs-row agreement before using any payload field (0030's
V-CARRIER-AGREES; its current-leg disagreement fails hidden so a
foreign payload's scope fields never decide another edge's
visibility). The reason is structural, not
convenience: the shipped deserializer REJECTS payloads its current model
does not admit, and an append-only journal can outlive the model that
wrote it (version drift, at-rest corruption) — so a typed return would
make historical reads fail-explosive at exactly the seam whose consumer
(0030 rules 3–4) owns malformed-state classification. 0029 promises byte
fidelity (V-VERBATIM) and NOTHING about payload validity at read time;
ALL validation belongs to the consumer (seam S4). No event with
`txn ≤ until_txn` → `None` for a post-epoch cutoff — and because the
migration baselines every pre-existing edge (F1, §4e), `None` now honestly
means "this store held no such edge at any `txn ≤ K`"; a pre-epoch cutoff
REFUSES (§4e — the store cannot speak for time before it recorded).
Because every event carries the full serialization, reconstruction is a
single lookup — no delta replay, no fabrication, and the recompute/
reinstate erasures the joint review named are recoverable by construction.
A migrated edge resolves to its `baseline` payload for every cutoff from
the epoch txn up to its first post-upgrade mutation — the round-2 gap
(`None` before first mutation, pre-mutation state lost after) is closed
by the baseline batch, not by relaxing the epoch rule.
What 0029 reconstructs is "the belief the store HELD at K"; whether it may
be ASSERTED now is 0030's classification under the joint F2 rule — current
revocation and current scope are OUTER CAPS applied by consumers, never
time-traveled by this carrier (§8).

A mutator added later that writes `edges` without declaring its event
handling fails **V-TOTAL**'s gate — the same generated-manifest mechanism
that already refuses an undispositioned mutation site (0002).

### 4c. Minting discipline
`recorded_at` is minted INSIDE the store, ONCE PER BATCH (F6 — one clock
read per event-emitting transaction; every event in the batch carries the
same instant, so a batch can never straddle two wall-clock values), from
the store's clock.
No public API accepts it; `observed_at` (caller-suppliable) is contrast, not
input. This is the load-bearing difference from every existing timestamp in
the system, and it is what makes the axis TRUSTWORTHY as transaction time.

### 4d. Read API
- `Store.edge_events(user_id, *, edge_id=None, until_txn=None) ->
  [EdgeEvent]` — typed rows in `seq` order; `until_txn` bounds by WHOLE
  transaction batches (F3: a batch is included or excluded entire, never
  split). A cutoff earlier than the store epoch REFUSES (§4e).
- `Store.edge_state_at(user_id, edge_id, until_txn) -> RawEdgeState | None`
  — the §4b-ii reconstruction; the RAW carrier, never a validated `Edge`
  (F5). `edge_events` rows likewise carry `state` as verbatim text.
- Cutoff tokens are `txn` values — non-negative integers, the ONE cutoff
  domain (F6; no read surface accepts a datetime cutoff). Non-integer or
  negative → typed refusal. A caller holding a `(recorded_at, txn)`
  composite cursor uses the `txn` component for every read decision.
- No recall/context/MCP surface; `introspect` MAY gain a counts-only
  summary (open, §10).

### 4e. Schema, migration, epoch — baseline snapshots (F1), epoch as txn (F6)
Additive v13: the `edge_event` table (§4a's pinned DDL, BOTH indexes) +
the epoch row, registered per 0013/0018 with the FULL
accepted-shape matrix (constructor + every migrated form — the 0027 v12
inheritance pattern, all shapes carrying the additive diff).

**The epoch BASELINE (F1):** inside the migration's transaction, for each
user the store journals EVERY existing edge as one `baseline` event —
state as found, serialized — all in ONE batch whose `txn` IS that user's
**epoch txn**. This is the round-2 re-scope, "no backfill" → **no
FABRICATED history**: the baseline is not backfill — it records the state
actually present when journaling began (the reviewer's framing, adopted) —
and nothing BEFORE the epoch is ever synthesized. Without it a migrated
edge reconstructed to `None` until its first post-upgrade mutation, and
its pre-mutation state was permanently unrecoverable after — the exact
round-2 gap. Crash-retry mints exactly one baseline: the baseline batch, the epoch
row, AND the v13 schema stamp commit in ONE transaction — the spec
REQUIRES this, so the partial states (baselines without an epoch, an
epoch without baselines, a stamped store without either) are
UNREPRESENTABLE by construction, not merely unlikely; a failed migration
leaves NO baselines and NO epoch, and the retry starts clean (V-ATOMIC's
discipline at the migration seam; V-BASELINE checks per-edge
exactly-once).

**The epoch is a TXN value (F6):** `epoch_txn(user)` = the user's baseline
batch `txn` for users predating v13; `0` for users whose entire life is
journaled (fresh stores, post-migration users). The pre-epoch test is
`until_txn < epoch_txn(user)` — integer against integer, ONE domain,
mechanically expressible and total (the round-2 objection was that an
instant-typed epoch could not be compared to an integer cursor; it no
longer exists on the read path). The `store_epoch` INSTANT remains as
display/telemetry only. A pre-epoch cutoff refuses — the store cannot say
what it knew before it started recording, and fail-closed beats
fabrication (V-EPOCH); note a fully-journaled user's `epoch_txn = 0`
makes the pre-epoch test `until_txn < 0` — UNSATISFIABLE over
non-negative txns, so no cutoff refuses for them and a post-migration
new user with no baseline batch correctly gets `None` ("held no such
edge") rather than a refusal: the zero removes a special case instead
of adding one. There is no unrecorded era to protect. `until_txn = epoch_txn(user)` on a migrated
user answers with the baseline states — the earliest honest answer.
Down-migration: `DROP TABLE` (reversible; the audit axis is lost
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

**Data-handling, stated plainly (F8a):** the journal is a CONTENT-BEARING,
unbounded historical store. Superseded, corrected, and revoked content
REMAINS READABLE from prior events by design — that is what an audit
journal is — until user erasure, which is the ONLY removal and is total.
This retention is acceptable precisely because the surface is
operator/substrate-only (V-INERT): no recall, context, export, or MCP path
reaches it, so historical content never re-enters any trust-bearing or
model-facing flow. A future consumer that widens reach owns the 0020/0021
composition for it (§3b).

## 5. Regime analysis

- **No consumer (v1 shipped state):** write-only log; every read surface
  byte-identical (V-COMPAT). Cost: one row carrying the edge's FULL
  serialization per mutation (F8a — the "one digest" figure was v2
  residue): the log scales with mutation count × serialized edge size,
  a content-bearing historical store, not a fingerprint index.
- **High-churn user:** log grows with mutation count, not edge count;
  unbounded by design (an audit log); erasure is the one shrink; a retention
  policy is future work (§10), never silent truncation.
- **Migrated store:** epoch-bounded knowledge WITH a baseline floor: every
  pre-existing edge reconstructs from its `baseline` event at the epoch
  txn onward; strictly pre-epoch cutoffs refuse (F1 + F6).
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
| **V-RECON** `edge_state_at(user, edge, K)` returns byte-exactly the serialization the edge held after the last `txn ≤ K` — driven across the recompute-erasure and reinstate-erasure cases the joint review named (the row forgets; the journal must not), and across a migrated edge's baseline-to-first-mutation span | `test_edge_state_at_reconstructs_byte_exact` | CI |
| **V-VERBATIM** the read surface returns journal payloads VERBATIM as the raw carrier — no parse, no deserialization, no validation, no normalization at the 0029 surface (F5, C-1); a payload the current model rejects (or cannot even parse) still traverses the interface intact; the carrier's `edge_id`/`user_id` are authoritative FROM THE ROW COLUMNS and byte-equal to them, never derived from the payload (C-2); the payload's own embedded identity copy is UNVERIFIED at this surface — 0029 never reconciles the halves, and the consumer must check agreement (C-4; 0030's V-CARRIER-AGREES) | `test_snapshot_carrier_is_raw_and_verbatim` + `test_carrier_identity_comes_from_row_not_payload` | CI |
| **V-BASELINE** after v13 migration every pre-existing edge has EXACTLY ONE `baseline` event, in its user's epoch batch, payload equal to the state found at migration; no runtime path can emit the kind; crash-retry never doubles a baseline | `test_migration_baselines_every_existing_edge_exactly_once` | CI |
| **V-TXN-ALLOC** txn/seq allocation follows the SPECIFIED SCHEDULE: `BEGIN IMMEDIATE` acquired before ANY allocation read; txn, seq, and the batch `recorded_at` minted after the lock; busy → whole-transaction retry-or-loud-refusal (0007 §4c), never a partial batch. Under this schedule two `SqliteStore` instances on one file produce distinct whole batches with ZERO allocation refusals; the DEFERRED schedule is the checked NEGATIVE control (same maxima read twice, `database is locked` — the round-3 reproduction); the (user_id, seq) PK is backstop-only and never fires under the IMMEDIATE schedule | `test_concurrent_allocation_across_two_store_instances` + `test_deferred_schedule_negative_control` | CI |
| **V-BATCH** one event-emitting write transaction = one `txn`; a multi-edge mutation (supersession's invalidate-A + create-B) shares it, and every `until_txn` read includes or excludes the batch WHOLE — no reachable cutoff reconstructs a state that never existed; two batches sharing a `recorded_at` stay distinct by `txn` | `test_transaction_batches_never_split` | CI |
| **V-MINT** no public surface accepts a transaction time; `recorded_at` is store-minted; the monotone guard holds under a backwards clock step | `test_recorded_at_is_store_minted_and_monotone` | CI |
| **V-KIND** the kind vocabulary is closed and derived; `invalidated` events validate `reason` against `DISPOSITIONED_REASONS` (all SEVEN); an unregistered reason refuses the write | `test_event_kinds_closed_and_reasons_authoritative` | CI |
| **V-EPOCH** `until_txn < epoch_txn(user)` refuses — integer domain, mechanically total (F6); a migrated store fabricates no pre-epoch knowledge, and a fully-journaled user (`epoch_txn = 0`) never spuriously refuses | `test_pre_epoch_queries_fail_closed` | CI |
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
     like any state; the RAW carrier lets it traverse the interface —
     0030's outer-visibility rule owns the classification);
  9. **(round 2)** a migrated pre-existing edge AT the epoch and around
     its first post-upgrade mutation: pre-epoch cutoff refuses; cutoff at
     the epoch txn returns the baseline payload (state as found, exact);
     cutoffs between epoch and first mutation still return the baseline;
     after the mutation, the mutated payload — the pre-mutation state is
     never `None` and never lost; CONTRAST cell in the same scenario: a
     user created after migration has `epoch_txn = 0` IN THE EXPECTED
     OUTCOMES (the literal zero, not prose) and no cutoff refuses for
     them;
  10. **(round 2; schedule pinned round 3)** concurrent transaction
     allocation from TWO store connections (two `SqliteStore` instances,
     one file, interleaved event-emitting writes), BOTH schedules:
     (a) POSITIVE — the required `BEGIN IMMEDIATE` schedule: all batches
     whole and distinct, txns unique per user, seq gapless-monotone per
     the append order the database serialized, ZERO allocation refusals
     and zero PK firings; (b) NEGATIVE CONTROL — the DEFERRED schedule
     the spec forbids: both connections read the same maxima and the
     second fails `database is locked` (the round-3 reviewer's
     reproduction, kept as the cell that proves the requirement is
     load-bearing rather than stylistic).
  The remaining five round-2 joint cases (superseded-then-restricted
  source; open-at-K-superseded-later with T past the current interval;
  same-ID semantic replacement after K; mismatched identities; malformed
  state through the real load path, hidden AND visible) are CLASSIFICATION
  cells and are specified in 0030 §6a over this same corpus — one shared
  acceptance surface, each half owned where its behaviour lives.
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
  store-minted transaction time, atomically recorded, epoch-bounded (with
  a baseline floor: pre-existing state is journaled AS FOUND at the
  epoch), erasure-complete. The journal is content-bearing and retains
  superseded/corrected/revoked content until erasure — stated in §3/§4f,
  not discoverable by surprise. *Limit:* knowledge before the epoch is unrecorded and REFUSES;
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
3. **The epoch rule's honesty, now with the baseline (round 2).** Is
   `until_txn < epoch_txn(user)` enforced across every read path; does the
   migration journal EVERY pre-existing edge exactly once (find an edge
   shape the baseline sweep misses, or a crash-retry schedule that doubles
   or drops a baseline); and is the baseline honestly "state as found" —
   never a synthesized pre-epoch narrative?
4. **§4b's `mutated` trigger under the FULL-STATE basis.** Can any same-id
   write change the row while leaving the complete canonical serialization
   byte-identical (it should be impossible by definition — but attack the
   serialization's canonicality: field ordering, None-omission, float
   formatting), and does the whole-serialization trigger over-fire anywhere
   a consumer would treat as noise?
5. **The allocator's locking schedule (round 2; pinned round 3).** The
   schedule is now exact: `BEGIN IMMEDIATE` before any allocation read,
   everything minted after the lock, whole-transaction retry under
   `busy_timeout`. Attack the schedule itself: a WAL-mode subtlety, a
   retry path that re-uses a stale clock read or half-allocated seq, a
   connection that reaches an allocation read through a path that never
   took the IMMEDIATE lock (the V-TOTAL sweep should make that
   structurally impossible — check that it does), or a busy-timeout
   interaction that turns the loud refusal back into a hang.
6. **The raw carrier's honesty (round 2).** V-VERBATIM promises payloads
   traverse unvalidated; find a read path (edge_events, edge_state_at, a
   future introspect summary) that normalizes, re-serializes, or rejects
   what the journal holds.

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

**ACCEPTED at joint round 4, 2026-09-01** — "Accept 0029 v9 on
specification substance." The same verdict returned 0030 v15 + the joint
seam and ruled the pair does not advance together; implementation is
coupled to 0030's acceptance and starts on the owner's word. One row per
EXTERNAL finding against 0029 (the internal both-check and cross-check
findings — I-1/I-2, F-A/F-B/F-C, C-1..C-4, the adoption-found v9
correction — live in the Version cell's lineage; every round's verdict is
verbatim in the round archives' `prior-rounds/`):

| round | finding | disposition | evidence |
|---|---|---|---|
| 1 | F1 — EdgeStateAt unreconstructable | owner ruled option (a): RECONSTRUCTABLE STATE — full-serialization payloads, single-lookup reconstruction | v3 §4a/§4b-ii; V-RECON; seam-model oracle shape (manifest S1) |
| 1 | F3 — a cutoff can split a mutation | per-user `txn` batch id, whole-batch reads, `seq` the ordering authority, `recorded_at` demoted to telemetry | v3 §4a; V-BATCH |
| 1 | F4 — V-TOTAL's basis too narrow + the FOURTH raw site | trigger re-based to the FULL-STATE serialization; `_recompute_edge_row` cited at its UPDATE (sqlite.py:334); grep-the-writes lesson in §9 | v3 §4b; V-TOTAL |
| 1 | F5 — schema unresolved | DDL pinned exactly in §4a; no deferred choices | v3 §4a |
| 1 | F8 (0029 half) — version-header drift | header discipline restored; later made mechanical in /pre-seal | v3; the round-2 F8 hold record |
| 2 | F1 — migrated edges lacked reconstructable epoch state | EPOCH BASELINE: migration journals every pre-existing edge AS FOUND (`baseline` kind, per-user epoch batch); baselines + epoch row + schema stamp in ONE transaction, partial states unrepresentable | v5 §4e; V-BASELINE; §6a scenario 9 |
| 2 | F5 (carrier half) — malformed states could not traverse | RAW carrier: `RawEdgeState`, payload verbatim TEXT, row-sourced identity, parse and validation consumer-owned; payload's embedded identity copy stated UNVERIFIED | v5→v7 §4b-ii; V-VERBATIM; seam manifest S1/S4/S6 |
| 2 | F6 — epoch/txn domains incomplete; allocator instance-local | epoch became a TXN value (`until_txn < epoch_txn(user)`, one integer domain; 0 unsatisfiable for fully-journaled users); allocation moved to the DATABASE level | v5 §4e/§2c; V-EPOCH, V-TXN-ALLOC |
| 2 | F8a — carrier sweep (digest-only residue) | journal stated CONTENT-BEARING in §3/§5; retention + data-handling in §4f | v5 |
| 3 | F4 — the locking schedule unspecified | `BEGIN IMMEDIATE` before ANY allocation read (house pattern cited: 0022 R3-1, schema_version.py:1501); everything minted after the lock; whole-transaction retry; PK backstop-only; DEFERRED kept as the §6a negative control | v8 §4a; `specs/evidence/0029-0030/seam_model/allocation_schedule.py` + `tests/test_seam_model_0029_0030_store.py` (executable, both schedules) |
| 4 | — (accepted; no 0029 findings) | package feedback only: portable tar ownership at the next assembly | this row |

**Executable evidence:** the joint seam model
(`specs/evidence/0029-0030/seam_model/`, in the ordinary suite) executes
the allocation schedule (both schedules), the restriction derivation, the
raw carrier's binding, and the reconstruction carrier shape — every
assertion with an asserted negative control; seven mutations proven, three
cross-machine. §6a's full acceptance corpus (the fifteen joint scenarios)
is an implementation obligation, frozen model-free before the first run
per the house pattern.

**§6a corpus FROZEN (2026-09-05, before the first choke-point commit):**
research — the seat that does not implement — derived every expectation
from this spec's text alone and froze `tests/eval/edge_events/MANIFEST.json`,
sha256 `820cabee48112d8e674bfbff1917a0eca22d58d6b8bfebd7a101ff2a147f6f81`
(ten named scenarios with event sequences and reconstructions, scenario 9's
literal `epoch_txn = 0` cell, scenario 10's both schedules, the five
0030-owned classification cells, the nine retained v2 scenarios, the four
pass criteria copied from §6a). Two mechanism questions are marked OPEN
there rather than guessed (scenario 6's equal `recorded_at`; scenario
10(b)'s failure surface) and are answered by dev's builder, which lives
beside the manifest (`tests/eval/edge_events/corpus_runner.py`, run on
every CI run by `test_0029_acceptance_corpus.py`). **Amendment 1** (research,
same day, after dev's answers): the two questions moved to
`OPEN_QUESTIONS_CLOSED` with the declared mechanisms; NO expectation
changed; sha256 `c844523962fecdf8ea369312e86a9756a505001f674bc017e8bf2363a1c6da8b`
supersedes `820cabee…` as the shipped text, and the runner pins it.
*Implementation note (2026-09-05):* the carrier's code moved 0031's LIVE
attribute-partition row (an implementation consideration under its
governing rule, not a design change): dotted/dataflow 4,604 → 4,687,
module-plain 251 → 253, module-protected 35 → 43, data-dunders 96 → 97;
regenerated from the census walker and bound in
`specs/evidence/0031/connection_census.py`. **V-COMPAT's pre-feature oracle:**
`specs/evidence/0029/pre_feature_oracle/pre_feature_capture.json`, sha256
`186a0909df6ac11dc20801800b59d1778e7073fa728f0e42f88a93f398edb947`,
captured at main `1fc357f4` (four surfaces; two measured non-behaviour
exclusions named in `CAPTURE.md`).

**Structured record:** the joint arc's ONE generated ledger — every finding
of all eighteen rounds, each row naming its target artifact (`→ 0029` for
the rows above) — lives in specs/0030 `## Review closure`, validated by
`specs/render_closure.py` against `specs/reviews.py` (research's ruling,
2026-09-04). The narrative here stays; the machine-checkable half is there.
