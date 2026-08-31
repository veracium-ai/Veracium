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
| **Version** | v1 |
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
| NEW `edge_event(user_id, seq, edge_id, kind, reason, content_digest, recorded_at)` | WRITTEN | append-only store-minted audit log; never exported; erases with the user | 0028 v2, 0030, future audit surfaces | additive; store-schema v13 |
| NEW `store_epoch` row (in `store_identity`'s pattern) | WRITTEN ONCE | the instant transaction-time recording began for this store | the fail-closed epoch rule (§4e) | additive |
| `Store` interface | EXTENDED | `+ edge_events(user_id, edge_id=None, until=None)` read API | 0028 v2 / 0030 / introspection | additive |

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

### 4a. The event model
One row per edge-state transition, written by the store, inside the
mutation's transaction:

`edge_event(user_id TEXT, seq INTEGER, edge_id TEXT, kind TEXT,
reason TEXT NULL, content_digest TEXT NULL, recorded_at TEXT)`
— PRIMARY KEY `(user_id, seq)`; `seq` monotone per user (max+1 under the
store lock, in-transaction); `recorded_at` ISO-8601 UTC, store-minted,
monotone-guarded per user (never earlier than the user's previous event; a
clock step backwards writes the previous value — order is `seq`, wall time
is best-effort telemetry, stated).

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

| kind | written by (site, from the manifest) | payload |
|---|---|---|
| `created` | `add_edge`; `apply_supersession_plan` (insert_incoming, absorption survivor); import commit | `content_digest` of the new row |
| `content_mutated` | any same-id edge-row replace whose §0027-digest changed — via `_upsert_edge_row` (note-append, recompute, absorption restate) or `confirm_edge`'s raw json rewrite | old + new digests (two columns or `reason`-packed — implementation picks ONE, spec pins it at v2) |
| `invalidated` | `invalidate_edge` / `_invalidate_edge_row` (plan invalidations, lifecycle expiry, dispute, revocation sweep) | `reason` — validated against `DISPOSITIONED_REASONS`, the AUTHORITATIVE seven; an unregistered reason refuses the WRITE (fail-closed at the source, so §4b totality is derived, not hoped) |
| `reinstated` | `_reinstate_edge_row` (0022 revocation lift) | — |
| `erased` | NOT a kind: erasure deletes the user's events (§4f); a tombstone would defeat erasure | — |

**Stated silence (internal-I-1):** a same-id re-upsert whose §0027 digest is
UNCHANGED — counter/metadata-only rewrites (`times_used`, `outcome_counts`,
confidence moves) — intentionally emits NO event: usage telemetry is outside
the valid-time knowledge axis this carrier records. Disclosed as a design
property, not discovered as a gap. (`append_outcome_if_head` itself writes
EPISODES only — internal review removed it from this table; when counters do
reach the edge row it is through the generic re-upsert path above, where the
digest predicate correctly stays silent.)

A mutator added later that writes `edges` without declaring its event
handling fails **V-TOTAL**'s gate — the same generated-manifest mechanism
that already refuses an undispositioned mutation site (0002).

### 4c. Minting discipline
`recorded_at` is minted INSIDE the store, at write, from the store's clock.
No public API accepts it; `observed_at` (caller-suppliable) is contrast, not
input. This is the load-bearing difference from every existing timestamp in
the system, and it is what makes the axis TRUSTWORTHY as transaction time.

### 4d. Read API (v1 minimal)
`Store.edge_events(user_id, *, edge_id=None, until=None) -> [EdgeEvent]` —
typed rows, `seq` order, optionally bounded to one edge and/or events with
`recorded_at ≤ until`. `until` earlier than the store epoch REFUSES
(§4e). No recall/context/MCP surface; `introspect` MAY gain a counts-only
summary (open, §10).

### 4e. Schema, migration, epoch
Additive v13: the `edge_event` table + `ix_edge_event_lookup(user_id,
edge_id, seq)` + the epoch row, registered per 0013/0018 with the FULL
accepted-shape matrix (constructor + every migrated form — the 0027 v12
inheritance pattern, all shapes carrying the additive diff). **No backfill
and no fabricated history:** at migration the store mints its
transaction-time EPOCH; every pre-existing edge gets NO retroactive events.
`edge_events(until=T)` with `T < epoch` refuses — the store cannot say what
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
| **V-TOTAL** every site that writes `edges` writes its §4b event in the same transaction — DERIVED from the mutator registry + write-target manifest; a new site without an event ruling fails the gate | `test_every_edge_writing_site_carries_an_event_ruling` | CI |
| **V-ATOMIC** mutation and event commit atomically; injected fault between them → neither persisted | `test_event_and_mutation_are_one_transaction` | CI |
| **V-APPEND** no code path updates or deletes an event except erasure; `seq` strictly monotone per user | `test_event_log_is_append_only_and_monotone` | CI |
| **V-MINT** no public surface accepts a transaction time; `recorded_at` is store-minted; the monotone guard holds under a backwards clock step | `test_recorded_at_is_store_minted_and_monotone` | CI |
| **V-KIND** the kind vocabulary is closed and derived; `invalidated` events validate `reason` against `DISPOSITIONED_REASONS` (all SEVEN); an unregistered reason refuses the write | `test_event_kinds_closed_and_reasons_authoritative` | CI |
| **V-EPOCH** `until` before the store epoch refuses; a migrated store fabricates no pre-epoch knowledge | `test_pre_epoch_queries_fail_closed` | CI |
| **V-ERASE** after `forget_user`, zero events for the user remain (same transaction) | `test_forget_user_erases_events` | CI |
| **V-INERT** events reach no recall/context/export/MCP surface; the schema policy is REQUIRED (absence = damage, not drift) | `test_events_are_store_local_and_required` | CI |
| **V-COMPAT** with no consumer, every existing surface reproduces the frozen pre-feature oracle byte-identically | `test_no_consumer_behavior_identical` | CI |

### 6a. Acceptance measurement — REQUIRED, FINITE

A CORRECTNESS gate (exact expected event logs), deterministic, no model:
- **Corpus:** `tests/eval/edge_events/` — a frozen scripted-scenario manifest
  (pinned ids, per-position instants — the 0027 v2.2 topology discipline
  from round 7, applied from the start): create, supersede, BACKDATED
  correction (the 0028 R1-2 counterexample verbatim), confirm, note-append,
  absorb, dispute, revocation-retire + reinstate, lifecycle expiry, import,
  erase — each scenario naming its exact expected event sequence (kind,
  reason, digest-transitions, seq order).
- **Pass criteria (pre-committed):** (1) exactness — every scenario's event
  log equals the expected sequence, 100%; (2) the R1-2 backdated-correction
  scenario shows the invalidation's `recorded_at` at the CORRECTION's write
  time, not its valid-time — the carrier answering what 0028 could not;
  (3) V-ATOMIC's injected-fault scenario leaves neither write.
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
   — the gate's blind spot is the spec's blind spot. The live example the
   internal round surfaced: THREE raw `UPDATE edges` sites exist today
   outside the `_upsert_edge_row` path (`confirm_edge`'s json rewrite,
   sqlite.py:191; `_invalidate_edge_row`, :252; `_reinstate_edge_row`,
   :300) — the derivation must grep the WRITES, not the callers' names, or
   a fourth raw site added later hides from it.
2. **V-ATOMIC under real fault schedules.** The event rides the mutation's
   transaction — inject at every seam (the 0013 gate family's method) and
   find a schedule where one lands without the other.
3. **The epoch rule's honesty.** Is fail-closed-before-epoch consistently
   enforced across every read path, and does the migration mint exactly one
   epoch under crash-retry?
4. **§4b's `content_mutated` trigger.** Digest-change detection under the
   same-id replace path: can a semantic change slip through digest-equal
   (it cannot — the digest is over the §0027 canonical content projection —
   but verify), and is `append_outcome_if_head`'s counter mutation honestly
   an edge-state change?

## 10. Open questions

- **Episode/wiki events:** out of v1 (edges are the trust-bearing state);
  extend later?
- **`content_mutated` payload shape:** old+new digests as columns vs packed;
  pin at v2 with the reviewer's preference.
- **Retention:** unbounded v1; a future retention policy must never
  silently truncate (an explicit, evented compaction if ever).
- **`introspect` counts-only summary:** expose event counts to operators?
- **0030 composition:** which event kinds feed assertable-as-of-T (0030's
  call, on this carrier).

## Review closure

*n/a — draft; populated before `accepted`, one row per external finding,
evidence openable/executable.*
