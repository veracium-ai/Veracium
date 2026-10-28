# Feature spec: on-disk store migrations

Spec-Status: accepted
Spec-Requires: 0007[0013/0007-sqlite-attestation]
Folds: 0013/0007-sqlite-attestation

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **ACCEPTED (v32)** — set `accepted` 2026-08-07 by dev on the finite M-Q4
> acceptance boundary (§8a): the six gated properties are frozen in normative text
> and mechanically demonstrated (the invariants table + the two pre-send gates, all
> green). Ten external rounds (18–28, post-M-Q4-ruling) each affirmed the
> architecture and the M-Q4 boundary; the concrete v1→v2 migration, planner/evidence
> architecture, offline authority model, closed public semantics and the abstract
> audit protocol are approved. **The acceptance criterion is "the six §8a properties
> are met" (they are) — NOT "the external review stops finding draft edge cells,"
> which has no natural terminal on an executable reference model** (the reviewer's
> "next adjacent cell" method can always expose one more defensive readback, as
> M-Q4 anticipated). Round 29's findings 2 & 3 (an already-terminal lifecycle must
> beat the trusted committed=True carrier — M99/M116; and a durable but
> request-mismatched terminal write is `audit_committed=None`, not `False` — M113
> corrected) are **closed** in v32. Round 29's finding 1 — a prior attempted-only
> lifecycle needs INVOCATION-provenance to tell it from this call's fresh
> publication — is **deferred to `0008` as an explicit production obligation**
> (§8a): it requires an activation-attempt token the in-process draft cannot bind
> without racing another process, which is exactly the multiprocess/reconciliation
> machinery M-Q4 assigned to the production sink. See **`## Review closure`**. What
> `accepted` authorises: implementation of THIS spec's design. It does NOT let code
> land yet — `Spec-Requires: 0007` (still `draft`) is gate-enforced. Concrete
> migration, evidence key, release identity, source binding, one-snapshot reader,
> TEMP confinement and ordinary planner states untouched; the evidence artifact
> reproduces byte-for-byte.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v38 — 2026-10-28: the census's own input surface, as rules (the round-3 implementation verdict, SA-R3-01, banked at coordination `c1ea30b`; research's stage-1 read of its class).** The verdict measured a connection factory that writes before the census installs its callbacks, and that replay runs again: 57 of 57 paths passed with 53 changed stores. Rules 5 and 6 stated what the census records and what its connection wrapper admits, but not what `connect` accepts, what the module seam forwards, or what values a recorded set may carry; the code forwarded all three. §5f.1 rule 6 gains the census's input surface, each part a closed set refused and recorded outside it, and replay re-checks its record against the same sets. INV-SA10 gains the matching mutants. Rule 5's claim and its two stated limits are unchanged. Prior: v37 — **v37 — 2026-10-27: one callback sequence no executed statement owns (the owner's word, “Yes, build v37”).** The first branch run measured INV-SA10's gate refusing the CLEAN ladder on SQLite 3.34.1, 3.37.2, 3.40.0 and 3.40.1, because a table-valued pragma read reported `UPDATE` on `sqlite_master`. Research traced it to pre-3.41 SQLite asking the authorizer about `sqlite3_declare_vtab`'s nested, never-executed `UPDATE sqlite_master`, on a connection's first use of a pragma module. Nothing is written. §5f.1 now attributes exactly that six-callback sequence as bookkeeping, and only where the build's own probe reproduces it with nothing changed; replay equivalence is unchanged. INV-SA10 gains five mutants. Without this, four common distributions' builds could be `verified` but never attested. Prior: v36 — **v36 — 2026-10-26: two wording corrections found while implementing I3(b) (the 0013 model's runtime seam); no rule, invariant or outcome changes.** (1) §5e's v35 INV-SA11 annotation said it “changes none of its fields”, which read as forbidding the `runtime` field it locates. It now says none of the EXISTING fields, and that the model's row admits `refused`, since round 5 consumes the authority before the runtime gate refuses. (2) The M15 and M18 rows named three tests retired by v34 on lines that state their tests run, and the spec gate reads every backticked name on such a line. They now cite their replacements (A1, A10, A12 and A15) and mention the retired tests without backticks. §5f.3's retirement list still names all three. Prior: v35 — **v35 — 2026-10-26: five corrections found while implementing the SQLite attestation fold (0007 I1–I2), folded on the owner's word (2026-10-26, “Approve; fold now”). No outcome of the accepted design changes.** Each comes from research's stage-1 read of I1–I7 and was accepted by dev. (1) §5e: INV-SA11's key sits on the OPERATION row of the frozen durable model, and the events table's attempted row stays payload-free. (2) §5f.1: six gate-completeness cells, N13–N15 and W1–W3 (Connection methods that write with no authorizer callback, and the routes that hand back the real connection). They are demonstrated in INV-SA10's committed mutation table, which is now the carrier of every N-row's “demonstrated red against the gate mutant”. (3) §5f.1 rule 5: INV-SA10's “fails the suite” now rests on REPLAY EQUIVALENCE, not on proxy opacity. The claim is stated exactly, with its two limits. Recording read results is NEXT-ROUND, and the comparator's SQLite build is asserted by argv. Rule 6 records the closed allowlist kept as defence in depth, and the census seam's extension to `release_migration`. (4) §5f.3: the evidence validators refuse two accepted manifestations at one version that share an acceptance digest, so the authority keeps its frozen shape (A16). (5) The seven `schema_version.py` line citations are re-anchored as function plus line at `d427822`, the commit that deleted the module's dead duplicate definitions; the v34 numbers stay beside them. Rule 3 and INV-SA10's exact-one ownership also cite their demonstrating cells. Prior: v34 — **v34 — 2026-10-25: the SQLite attestation fold (amendment `0013/0007-sqlite-attestation`, v0.12.1, sha16 `134243c63b05845a`), its migration side.** Its design was accepted at its external round 2 (2026-10-25; verdict banked at coordination `2b84ab5`) and by the owner (2026-10-25T19:10Z). The new §5f carries it; §4f, §5c, §5e, M11, M12, M15, M18 and §8a item 2 are edited in place and point to it; the store-open side is 0007 §4g. Prior: **v33 — 2026-10-13: post-acceptance revision (internal finding 0013-PA1; no release changes behaviour; `Spec-Status` stays `accepted`). Every migration step's output is checked AT THE STEP (§4f).** A mutation campaign over the whole migration ladder (dev's instrument, research's identical re-run) found six steps whose output nothing checks, on any SQLite build: the version stamp, the `store_identity` and `store_epoch` mints, the v13 baseline journal, the v2→v3 outcome-chain conversion and the v3→v4 wiki cache drop. A wrong stamp makes `migrate_store` report `migrated` and commit a store the next open refuses. The unmutated ladder is correct; these are assurance gaps, not a wrong output in any release. §4f gives each step a postcondition checked inside the migration's transaction, before the next step; M117–M123 are the invariants, and the closure cells are the campaign's perturbations, each KILLED at its own step. The v2→v3 fill of a missing `observed_at` becomes ONE stated clock read per migration instead of a per-row side effect of loading the model. **Respun 2026-10-14 on dev's review (same version, not yet adopted):** "equal" is defined as equal AS THE DECLARED TYPE, since the dump reformats legitimate `+00:00` datetimes; the added keys are DERIVED from the models' constant defaults, 19 measured; the one released-then-removed field, `provenance.source_type`, is named as the only undeclared key the step may drop, under accepted 0016 D2 (M-Q6, closed by it); and a pre-step snapshot is the postcondition's own read. **Owner rulings, 2026-10-14 (Quentin, first-hand in the dev session):** PATH, “Fold on your word”: like the 0041 notice hotfix, internal finding 0013-PA1 is closed with a mutation table whose cells are the campaign's perturbations, each caught at its own step; it lands after review and suite, and is disclosed to the external reviewer in the next package that touches 0013 (the SQLite amendment's); external review of v33 was declined. M-Q5, “Keep the fill” (M-Q5, closed by it). Prior: v32 |
| **Status** | *see `Spec-Status:` — canonical.* **Prerequisite of every schema-changing spec:** `0006`, `0008`, `0009`, `0010`. |
| **Internal reviewers** | research — pending |
| **External review** | required — a bad migration makes stores unopenable |
| **Decision + date** | **accepted 2026-08-07** (dev, on the finite M-Q4 §8a boundary; see `## Review closure`) · **v34: the amendment's design accepted** (its round 2, 2026-10-25, and the owner's word); implementation acceptance outstanding (0007 `## Review closure`, I1–I7) |
| **Path** | full |

---

## 0. Why this is a spec and not a section of `0006`

**The scope cut put the migration contract in `0006` §0b. That was wrong, for
two reasons the reviewer named.**

1. **`0006` is a `draft` whose central mechanism (§3) is explicitly falsified.**
   Hanging every other schema-changing spec off it makes them wait on an
   unrelated, unresolved trust design.
2. **The dependency would not be expressible.** The gate reads a spec's direct
   `Spec-Requires:` entries; it cannot infer that adding a table needs migration
   work that happens to live inside a source-identity spec.

**So the graph is now:**

```
0013  requires 0007                (versioning must exist before shape changes)
0006  requires 0007, 0013
0008  requires 0007, 0013          <- the accepted spec whose gate the cut broke
0009  requires 0007, 0013
0010  requires 0007, 0013
```

**And the conclusions below are stated here in full, not cited.** The v9 archive
(`specs/archives/0007-v9-20260803T0056Z.tar.gz`) holds the working text, but the
archive policy says plainly that a hash of a file nobody kept proves nothing —
**a spec must not depend on a tarball on one developer's machine.**

---

## 1. Problem and motivation

**A schema change with no migration path strands every existing store.**

`0007` gives a store a version and refuses what it does not recognise. That is
exactly the right behaviour and it is also the problem: the first spec to change
the shape turns every store in the field into an unrecognised one. Without a
migration, `0007`'s refusal is the *only* outcome.

**The requirement that must survive**, established by `0007`'s first external
review round and never overturned since:

> **A user upgrading across a schema change must not be required to install
> every intermediate release.** A store presenting `user_version = 0` with a
> version-1 shape to a version-2 build must resolve to base 1 and migrate
> forward — not be refused as foreign.

**Why this is opening now and not with `0007`:** seven review rounds of `0007`
produced ~63 findings, the large majority in migration machinery that had **no
users** — the registry was empty and there was one schema version. Landing a
mechanism before its first user meant each rewrite introduced the next round's
defect. **`0013` is designed against a real migration**: `0008`'s
`confirmations` table, or `0006`'s new column, whichever lands first.

---

## 2. Field contracts touched

| field | read / written | contract | consumers |
|---|---|---|---|
| **`MIGRATIONS`** | **NEW** — a registry of declared steps | one step per version transition | the open path, evidence generation |
| `MANIFESTS` (`0007`) | **written to** | `0007` already declares it a **set** per version, for exactly this reason | open, migrate |
| `PRAGMA user_version` (`0007`) | unchanged | `0007` owns stamping | — |

**No trust-bearing field changes.** Like `0007`, this spec adds no capability;
it constrains how a store may change shape.

---

## 3. Trust-class matrix — REQUIRED, blocking

**Not applicable — no trust class is read or written.** Stated rather than
omitted. The trust-relevant property is `0007`'s: every invariant in
`0002`–`0006` assumes the bytes on disk mean what this build thinks they mean,
and a migration is the one operation that deliberately changes them.

---

## 4. Behaviour — the conclusions that survived external review

**Each of these cost at least one round of `0007` review to find. They are
carried forward as the starting position, not as settled law** — this spec has
had no review of its own.

### 4a. Migrations are declarative

```python
class Migration(NamedTuple):
    from_version: int
    to_version: int
    statements: tuple[str, ...]      # executed in order, by the planner alone
```

**Not a Python callback.** `0007` v5 gave migrations a proxy whose connection
was name-mangled and claimed transaction control was unreachable "by
construction". Round 5 recovered it in one line —
`executor._MigrationExecutor__conn` — and ended the outer transaction. **Name
mangling is not access control**, and a false containment claim is worse than an
admitted trusted one.

### 4b. Effects are confined to persistent `main` schema

A declared statement can act where the manifest cannot see. Both measured:

| statement | result under the loose rule |
|---|---|
| `CREATE TEMP TRIGGER … BEGIN DELETE FROM t; END` | accepted · persistent manifest **byte-identical** · every inserted row silently deleted |
| `PRAGMA writable_schema=ON` | accepted · manifest unchanged · **still set afterwards** |

**Validating the persistent shape afterwards is only a complete check if effects
are confined to the persistent shape.** So an authorizer denies
`SQLITE_TRANSACTION`, `SQLITE_SAVEPOINT`, `SQLITE_ATTACH`, `SQLITE_DETACH` and
`SQLITE_PRAGMA`, and any action outside `main`; and `sqlite_temp_master` is
asserted empty after every step.

**Its role is stated honestly: defence against an accidental declared statement,
not a sandbox around hostile code.** It is restored in `finally` — left
installed it breaks the planner's own commit; left off after a failure it drops
containment for whatever runs next. **A migration runs only on a
Veracium-owned connection with no pre-existing authorizer**, because Python
exposes no portable getter for a prior callback.

`END`, `END TRANSACTION` and `RELEASE` all commit, and a keyword blacklist
missed all three — which is why this is an authorizer and not a text filter.

### 4c. A migration may not define its own destination

The generator once added **whatever a migration produced** to the destination's
accepted set. Measured: an **empty** migration from 1 to 2 was accepted as a
valid version 2, so a store missing a required table would have passed
validation.

**The destination requirement is independent of the migration.** What
authorises an output today is stated in §5 and §5c: **exact constructor
identity plus recorded path evidence** — nothing a migration produces enters
the accepted set on its own sayso.

### 4c-deferred. The structural-capability model — first `ALTER`, own review

*(Round 3: this subsection is **explicitly deferred design**, not present
contract — v4 still said capability "authorises", which contradicted §5/§5c's
correct statement that it is context only.)* An `ALTER`-class migration will
legitimately produce DDL text that differs from the constructor's, which is
the case a byte-for-byte rule wrongly rejects. When the first real `ALTER`
arrives, the deferred model — every declared object present and of the right
kind, columns compared via `table_xinfo` rather than DDL text, no unapproved
objects, rebuildable absence as repairable drift — gets its own external
review round before anything relies on it. Until then
`destination_problems()` is non-authorizing scaffolding, exact DDL text
remains what `0007`'s digest records, and **only exact identity and recorded
evidence authorise**.

### 4d. One step per transition

**Exactly one migration from `n` to `n+1`, validated against every accepted
manifest of `n`.** Route selection, cycles, non-adjacent steps and duplicate
edges become unrepresentable rather than rejected. What remains checkable:
adjacency, both versions declared, `SCHEMA_VERSION` agreeing with the registry,
and **every version below the current one having a route forward** — an accepted
source manifest with no path to the current version can never be opened.

### 4e. A version accepts a set of manifests, and evidence is per path

A constructor and an `ALTER` path legitimately produce different stored DDL:

```
fresh constructor:  … json TEXT NOT NULL, source_id TEXT )
ALTER TABLE:        … json TEXT NOT NULL , source_id TEXT)
```

So `MANIFESTS[v]` is a **set** — `0007` already declares it so — and **runtime
evidence records every path individually**, keyed `v<base>:constructor-><dest>`.
Keying by destination alone can record only one path per destination, while
different bases producing different exact output at the same destination is the
entire reason those digests exist.

### 4f. Every step's output is checked at the step (v33, internal finding 0013-PA1)

**The finding.** A mutation campaign perturbed each write of each migration path at its execution (DDL by text, DML by
data, the stamp by value) and recorded where each perturbation was killed: 44 paths (every accepted shape at every base
v1–v14, the unstamped legacy store, a HEAD store with its rebuildable indexes dropped), 68 distinct steps, 3,318
perturbations. Three ALTER sites are checked at the step (their stored DDL byte-matches a reviewed constant, §4c); the
additive DDL is covered by the end-state check, or absorbed by drift repair and revalidation. **Six steps are checked by
nothing: every perturbation of them SURVIVED** (a value altered, a row dropped, the statement skipped; 597 data
perturbations and 43 stamp perturbations). The end-state check reads the shape, never `user_version` and never rows.
Instrument: dev's steptable.py (sha16 `5b81c3ae0d9f1b9f`); research re-ran it from its own archive of `af1e564` with an
identical result, and separately reproduced the stamp case. The unmutated ladder is correct on both SQLite builds
measured; **these are assurance gaps, not a wrong output in any release.** The worst consequence measured: a wrong
stamp makes `migrate_store` return `migrated` and commit a HEAD-shaped store stamped below HEAD, which the next ordinary
open then refuses ("stamped v14 … no migration hook"). A false success report and a store that will not open, not a
silent misread.

**The contract.** Each of the six steps gains a POSTCONDITION, checked inside the migration's transaction immediately
after the step and before the next one. A failed postcondition refuses the migration with `unsupported-migration`,
naming the step, and the transaction leaves the store as it was (the existing failure contract). Each postcondition
reads the database's own bytes, never a value the step computed and kept: a check of the step's own variable would pass
whatever the step wrote. Where a postcondition needs the state BEFORE its step (the v2→v3 rows' raw JSON, a row present
before a mint), the postcondition reads it from the database itself, before the step runs, inside the same transaction;
that snapshot is the check's own read, not a value the step kept.

| step | code at `af1e564` | postcondition |
|---|---|---|
| **the stamp** | `PRAGMA user_version = SCHEMA_VERSION` (`_apply_forward`) | `PRAGMA user_version` reads back exactly `SCHEMA_VERSION`. The end-state check also requires it |
| **`store_identity`** | `_mint_store_identity`: `INSERT OR IGNORE … VALUES(1, uuid4)` | exactly one row, `id = 1`, whose `origin` is a canonical UUIDv4 string. A row present before the step is unchanged, byte for byte |
| **`store_epoch`** | `mint_store_epoch`: `INSERT OR IGNORE … VALUES(1, now, schema_at)` | exactly one row, `id = 1`. If the step created it: `started_at` equals the migration's one clock read and `schema_at` the value passed. A row present before the step is unchanged |
| **the v13 baseline** | `journal_baselines`: one `baseline` event per pre-existing edge row | the number of `baseline` events the step wrote equals the number of `edges` rows; for every edge row, exactly one such event whose `edge_id` is its id, whose `state` is byte-equal to the row's `json`, whose `reason` is NULL and whose `recorded_at` is the migration's one clock read; within each user, one `txn` and contiguous `seq` |
| **the v2→v3 outcome chains** | `_migrate_outcome_chains`: each legacy outcome episode re-serialised with `seq = 1`, `supersedes_episode = None`, `judgment_time_known = False` | for every legacy `outcome` episode, compared with the row's RAW legacy JSON, never a model load of it (a load would refill missing fields and make the check pass vacuously): the three fields carry their new values; every other key present in the raw JSON, at any depth, carries a value EQUAL AS ITS DECLARED FIELD TYPE (below); `observed_at`, if the raw JSON lacked it, equals the migration's ONE recorded clock read, and if present is unchanged in that sense; every key the conversion ADDS is a declared field whose value equals the JSON form of its declared constant default, derived from the model, never listed by hand; a raw key the model does not declare is refused, except the retired fields named below. Non-outcome episodes are byte-unchanged; the converted count equals the legacy outcome count |
| **the v3→v4 wiki drop** | `_drop_wiki_cache`: `DELETE FROM wiki` | `wiki` has zero rows |

**One stated clock read for `observed_at`.** Today the v2→v3 step fills a missing `observed_at` as a side effect: it loads
each episode through the model, whose `observed_at` field has `default_factory=utcnow`, so each row receives its own wall
clock read. The step instead takes ONE clock read per migration, as the v13 baseline already does, passes it to the
conversion for rows lacking the field, and passes the same value to the postcondition. A bound such as "between the
migration's start and its commit" was considered and rejected: wall-clock bounds around wall-clock reads refuse a correct
migration when the clock steps backwards between them, and they miss the mutant that overwrites a row's existing value.

**What "equal" means, and the keys the dump adds** (dev's review of v33, measured by research at `7c8c905` from an
archive, through the step's own load-copy-dump):
- **Equal as the declared type, never as text.** The dump reformats legitimate values: `observed_at`
  `2026-09-03T10:00:00+00:00` and `…T10:00:00.000000+00:00` come back as `…T10:00:00Z`, and `2026-09-03 10:00:00` as
  `2026-09-03T10:00:00`. `+00:00` is what `datetime.isoformat()` emits, so older writers plausibly stored it. Both sides
  are parsed by the field's declared type and compared: a datetime as the same instant, and a naive value stays naive
  (naive never equals aware). A string comparison would refuse every such row on a correct migration.
- **Added keys are derived.** On a minimal legacy outcome row the dump adds 19 keys: 14 top-level (`claimed_by`,
  `consolidation_output_index`, `context_ref`, `date_end`, `date_start`, `edge_id`, `judgment_time_known`, `lineage`,
  `operation_id`, `outcome`, `retired_at`, `retired_reason`, `seq`, `supersedes_episode`) and 5 under `provenance`
  (`confidence`, `derived_from`, `disclosure`, `origin`, `source_id`). Three of them are the chain fields this step
  sets. Each of the other 16 equals its field's declared constant default IN JSON FORM (`disclosure` dumps as
  `"mentionable"`, not the enum). The postcondition derives that set from `Episode` and `Provenance` field defaults. A
  hand list would drift the day a field is added. `observed_at` is the one clock-sourced default (`default_factory`)
  in either model.
- **A retired field is dropped, and only a named one.** Neither model keeps undeclared keys, so the step drops any raw
  key the current model does not declare. Across the 48 release tags, ONE field was released and later removed:
  `Provenance.source_type`, declared from v0.1.0 to v0.10.0. Outcome rows reach this step only from stores at schema 1,
  written by v0.3.0 (the first release with outcome episodes) through v0.4.8 (the last to stamp schema 1), and
  `source_type` is REQUIRED in every one of those releases. Every such row carries it, and today's step drops it, on outcome rows only (other rows keep it, unread). The postcondition
  admits the drop of exactly the retired set, `provenance.source_type`, and refuses any other undeclared key. The set is
  a constant in code, bound by a test to its derivation from the release tags (a field declared in a released
  `schema.py` and absent now). **The drop itself is already ruled**: accepted 0016's D2
  (`specs/0016-sourcetype-deletion.md`) deleted the field, and historical `source_type` keys in stored JSON are dropped
  on read (the D2 note at `src/veracium/schema.py` L72–L77). This step persists what every read of every row already
  does; the constant cites 0016 D2 as its authority. M-Q6 is closed by it.

**Closure.** 0013-PA1 closes only with a mutation table whose cells are the campaign's perturbations of the six steps,
each KILLED at its own step's postcondition (not later, by a collateral error or by the end-state check), plus controls:
the unmutated ladder still migrates every path, on the qualified build and on one unattested build. The v2→v3 controls
include legacy rows in every datetime form an older writer could produce (at least `isoformat()`'s `+00:00`, pydantic's
`Z`, a space separator, and a naive value), and an outcome row of the v0.3.0–v0.4.8 shape carrying `source_type`; each
must migrate. *Instrument limit:* the campaign's legacy episodes were built from the accepted DDL with generic rows, not
written by old releases. Where an archived release can be installed, a store it writes is the better control.

**v34 (amendment `0013/0007-sqlite-attestation`):** the 0013-PA1 closure evidence gains INV-SA10's commit-time gate, which asserts that every ladder write maps to a checked step (§5f.1, §5f.4). The amendment's two annotations to this section are §5f.2.

---

## 5. The concrete migration — v1 → v2, the `confirmations` table

**Per the M-Q1 ruling, this spec is reviewed against a real migration.** The
first schema change is `0008`'s audit table, derived field-by-field from its
§6b–§6d:

```sql
CREATE TABLE confirmations (
    id TEXT NOT NULL PRIMARY KEY, user_id TEXT NOT NULL, edge_id TEXT NOT NULL,
    confirmed_at TEXT NOT NULL, actor TEXT NOT NULL, call_path TEXT NOT NULL,
    correlation_id TEXT NOT NULL, request_digest TEXT NOT NULL,
    UNIQUE(user_id, correlation_id)
);
CREATE INDEX ix_confirmations_edge ON confirmations(user_id, edge_id);
```

| decision | from `0008` |
|---|---|
| `confirmed_at` stores the **normalised instant** | §6c — never the caller's string |
| `actor`, `call_path` are closed-enum **values** | §6c — free text in either was the bypass `actor` demonstrated |
| `correlation_id` **NOT NULL**; `UNIQUE(user_id, correlation_id)` | §6c — **an omitted id is *generated* by the library and returned as `str`**, so a value is always persisted; a NULL row could never identify its record on replay. "No replay protection" comes from the caller not retaining the value, not from NULL storage. Tenant-scoped per §6c's ruling — **and §6d's contradictory global line is corrected in `0008` itself, dated** |
| `id` **NOT NULL**, store-generated (`c-<12 hex>`) | round 2 measured `TEXT PRIMARY KEY` accepting multiple NULLs in a rowid table |
| `request_digest` mandatory | §6c — replay compares the canonical request; a same-id different-payload replay is an integrity conflict, not a lookup hit |
| the index is `REBUILDABLE` | `0007` §4a-iii — non-unique acceleration; the UNIQUE constraint lives in the table DDL and is therefore in the digest |
| **the migration is two `CREATE` statements** | §4a's declarative model; nothing else changes |

**A measured property the review should weigh:** because the change is purely
additive, the migration's stored DDL is **byte-identical** to the v2
constructor's — `MANIFESTS[2]` has one digest with two provenances. The
accepted-**set** model is still exercised (both paths are generated and
compared), but the `ALTER`-class divergence `0007` measured does not occur
here. **The set model earns its keep on the first `ALTER`, not on this
migration** — stated so the convergence is not mistaken for evidence that the
set was unnecessary.

**This migration is authorised by exact constructor identity, not
capability.** Round 2 demonstrated the column-only capability check stamping a
destination with `UNIQUE(correlation_id)` — global, violating `0008`'s tenant
scoping — and stamping a store missing its rebuildable index, which `0007`
would immediately call drifted. For a CREATE-only migration the byte-identical
constructor **is** the contract, so `open_or_migrate` now: applies the declared
statements → repairs rebuildable drift → recomputes the complete manifestation
→ **requires exact equality with the v2 constructor's** → stamps. Capability
is necessary context, never authorisation. **The general structural-capability
model is deferred to the first real `ALTER` and must be externally reviewed
there** — per the round-2 acceptance-bar ruling, not as accepted residual risk.

**Executable**: `specs/migrations_0013.py` and `tests/test_migrations_0013.py`
(every review probe carried as a regression — the count is whatever pytest
collects that round, not a number embedded here to go stale, per round 12's
correction C: the full inherited planner across empty/unstamped/foreign/
malformed/newer stores, the evidence gate's adversarial records, confinement
qualification, the closed failure model, and the stale-connection hazard
below).

**And there is exactly one planner** (round 3, finding 1). The instrument owns
no version-state machine: `open_or_migrate` / `migrate_store` install the
draft registry and the draft evidence artifact into the production `0007`
kernel — the state a v2 build would ship as package data — and call
`open_versioned()`, whose **older-row hook** is the seam `0007` §4 delegates
to this spec. Ordinary opening installs a refusing hook (classify the source,
then `migration-required`); the dedicated offline operation installs the
migrating hook (§5b–§5c). Every other row — new, legacy, foreign, current
with drift repair, stamped-wrong, newer, locked, unsupported — is the
kernel's own code, which is why a stamped v1 store with an unauthorized extra
table now answers `stamped-shape-mismatch` (round 3 measured it being
promised a migration), and a table squatting a rebuildable index name is a
closed refusal via the typed digest rather than an `OperationalError` from a
repair statement.

## 5b. M-Q2 RULED: adopt with conditions — the lock serialises, it does not fence

**Round 2's ruling, recorded.** `BEGIN IMMEDIATE` under the §4c protocol is
**approved as migration mutual exclusion** — verified by the reviewer with five
separate *processes*, one `migrated`, four `current`. **It is not
mixed-version fencing**, and v2 claimed more than the lock provides.

**The hazard, measured** (`test_mq2_hazard_a_stale_v1_connection_writes_after_migration`):
a connection opened *before* the migration never re-runs the version gate, so
an already-running v1 process keeps applying v1 behaviour to the v2 store. For
`0008` that is precisely the unaudited clearing path the whole chain exists to
close.

**So the deployment quiescence contract is part of this spec, load-bearing:**

| before a migrating release is admitted | |
|---|---|
| all old application processes stopped | no old worker retains an open connection |
| migration performed before service admission | old binaries prevented from restarting against the migrated store |
| backup taken; rollback procedure in place | a "one-way" declaration is not a fence |

**The boundary is a mechanism, and its claim is exactly this** (round 3
narrowed the wording): **ordinary opening cannot initiate migration; the
trusted deployment authority owns quiescence, old-binary fencing, and backup
validity.** The stale-process race is not "gone" — the library cannot see
other processes — it is *owned*, explicitly, by the party that can.

Migration is a **dedicated operation** (`migrate_store`), never a parameter on
tenant-facing opening — `open_or_migrate` has no authority argument at all
(round 3). **And the dedicated operation is a MODE of the shared planner,
not a second state machine** (round 6, finding 1: v7's operation reached the
planner's new-row and CREATED a fresh v2 store after its attested v1 source
was deleted — likewise over an empty replacement database). In migrate mode:
an accepted older source runs the migration hook; a current destination is a
permitted no-op (`current`, the race case); **a new or empty store refuses
`migration-source-missing` and never creates** (the connection itself is
`mode=rw` and cannot materialise a file; a nonexistent path refuses with the
path left uncreated); an unstamped shape is never adopted (`allow_adopt` off
— the candidate restriction already refuses it as `foreign-shape`); foreign,
malformed and newer keep their normal closed refusals. The creation seam is
the kernel's `new=` hook, the exact mirror of the older-row hook. The `MigrationAuthority` is an **attestation the library validates
but cannot verify** — and round 4 showed that binding it to a path *string*
is not binding it to an *operation*: an authority was replayed after the
store at its path was replaced (the replacement migrated under an attestation
belonging to the earlier file), and a retargeted symlink carried an authority
minted for a different store. **The authority contract is therefore frozen
here, not left as an implementation note** (round 4's acceptance-boundary
ruling):

| field | binds | validation at consumption |
|---|---|---|
| `quiesced` | the host's quiescence assertion | exactly `True` — a truthy `1` refuses (round 3's probe) |
| `store_path` | canonical store identity | `os.path.realpath` at mint AND at consumption; a retargeted symlink is a different store and refuses |
| `from_version` · `to_version` | the step's endpoints | exact ints, equal to the selected step's |
| `source_digest` | the source manifestation being migrated | equals the acceptance digest measured under the write lock, pre-repair (rebuildable-blind, so incidental index drift does not unbind) |
| `migration_digest` | the reviewed statements | equals the declaration digest of the registered step |
| `backup_ref` | the backup this operation made | the frozen token grammar: ASCII `[A-Za-z0-9._+:/-]`, ≤ 128 chars, no whitespace — a grammar closes the prose channel a byte cap only bounded (round 6); normalization is moot because the charset admits one representation |
| `release_ref` | the minting release/deployment | must equal the RUNNING release identity — **frozen: `veracium-<version>+<source-digest>`**, the digest being the FULL sha256 (round 7: 12 hex chars were 48 bits against an adversary who constructs builds) over a **framed, domain-separated** encoding: `"veracium-release-identity-v1"` then, per file in the frozen ordered list (this instrument, the `0007` kernel), length-framed name and length-framed content — round 7 measured a docstring moved across the raw-concatenation boundary keeping the identity byte-identical, no hash collision required. Representation: the token grammar (128 chars holds it); source of truth: the running tree's own bytes, identical in editable and archive builds; comparison: exact equality; rotation: any covered-file change. Production may substitute a signed release-artifact digest |
| `operation_id` | this one migration operation | **single-use over the COMPLETE operation** (round 5) — consumed at acceptance, before any store access; an opaque `op-<uuid4>` token whose grammar enforces the version-4 and RFC-variant bits (round 16, correction C; round 18, correction D reconciles this row with the enforced grammar — the earlier "shape, not version/variant" wording predated M77 and is withdrawn) |
| `issued_at` · `expires_at` | the validity window | **the one canonical timestamp contract** (round 9, finding 5, applied uniformly): exact `str`, 32 ASCII chars, `YYYY-MM-DDTHH:MM:SS.ffffff+00:00`, UTC only, length-capped before parse, byte-equal to the reserialization of the parsed instant; `issued ≤ now < expires`; `expires − issued ≤` the frozen `MAX_AUTHORITY_LIFETIME` (1 h); **no clock-skew allowance**. EVERY persisted timestamp — `attempted_at`, `occurred_at`, and the evidence artifact's `generated_at` — uses this exact contract |
| `evidence_digest` | the exact evidence artifact consumed | sha256 of the operation's SNAPSHOT bytes (round 7: one read feeds digest, comparison, parse and planner — v8's two reads were a TOCTOU, measured); a regenerated artifact unbinds the authority |
| *(all three digests)* | — | exactly 64 lowercase hex, statically; and the authority's (from, to, source, migration) key must resolve to **exactly one current path record in the snapshot** before consumption — so even a no-op `current` operation was valid for one exact evidenced source (round 7: v8's current branch accepted a garbage source digest) |

An expired, future-issued, over-long-lived, previously consumed,
retargeted, source-mismatched, wrong-release, mistyped or unbound authority
refuses `migration-quiescence-required`; a resolution failure — bindings no
current path record evidences — is an ARTIFACT property and refuses
`migration-evidence-missing`. **Minting never creates**: `make_authority`
opens the source `mode=rw` and refuses when there is no store or the store
is not an accepted source — round 7 measured plain `connect()`
materialising a zero-byte database at a missing path and returning an
authority over the empty manifestation. A nested draft context pinned to a
different artifact digest than the installed one refuses rather than
silently sharing (round 7's second TOCTOU variant). **Consumption covers the complete
dedicated operation** (round 5): once static validation accepts an operation
id — before the store is even opened — it is spent, and EVERY subsequent
outcome spends it: `migrated`, a no-op `current`, an evidence refusal, a
lost race, even `locked`. Round 5 measured why the narrower hook-only rule
fails: an authority whose operation found the store already current was
never consumed and later migrated a replacement store at the same canonical
path; the five-opener race leaves four such authorities. The cost is stated
plainly: an operation that ends in `locked` or `store-unopenable` has spent
its authority and the host mints a fresh one — operationally correct, since
the world changed while it waited. **Consumption is in-process in the draft
and durable in production — the migration audit (§5e) is the durable
consumer.** What remains host-trust, stated rather than
hidden: a host that atomically swaps in an identical-shape store at the same
canonical path inside the validity window defeats path binding. The host is
explicitly trusted; the lifecycle exists so its assertion cannot silently
**drift** to a different operation — which is the failure round 4 measured.
`allow_adopt` never doubles as migration permission.

*(v2's §8 said "not multi-process" while §5b demonstrated five concurrent
openers — the contradiction is resolved as above: concurrent **cooperating**
openers are serialised by the lock; **stale** openers are the operational
contract's problem.)*

## 5c. Path evidence: recorded, validated, consumed — never re-derived

> **v34 — the runtime seam is replaced by §5f.3 (amendment `0013/0007-sqlite-attestation`, its §4c-iii), carrier by carrier.** Withdrawn from this section (the amendment's §4f, in 0007 §4g.6): the migration-runtime record class, and with it the single-active-runtime policy in `migration_runtime_artifact_problems`; the runtime-identity component of the path-evidence key and of its expected set; and the requirement that a path record's runtime resolve to a schema-runtime record and a migration-runtime record. Everything else here stands, as §5f.3 qualifies it.

**Round 3's central finding: v4 generated its "expected" record from the
currently loaded migration code, so an altered migration authorised itself.**
Measured — `DELETE FROM edges` appended to the declared statements produced
the exact v2 schema, stamped `migrated`, and left zero edge rows; exact schema
identity cannot detect data destruction. **The correction is architectural:
evidence is a shipped, committed artifact that the planner LOADS; the live
code contributes only a digest to match against.** *Committed, not
immutable* — round 4's distinction, adopted: the artifact is version-controlled
package data, consumed rather than re-derived, but it is **not** independently
authenticated or integrity-protected at runtime; package signing or filesystem
integrity would be a separate boundary and is not claimed here.

The artifact — `specs/generated/migration_0013_evidence.json`, the M11/M12
draft forms — is generated by `migrations_0013.py --write-evidence` on a
runtime being qualified, verified by `--check-evidence` (structural validation
plus exact re-derivation on the recording runtime), and consumed by
`migrate_store`.

**Writes are monotone over the `MigrationEvidenceRevision`** — the triple
`(migration_evidence_algorithm, manifest_algorithm, draft_schema_version)`
(round 5: the writer replaced artifacts seeded with future revisions of
every component — the downgrade class `0007`'s runtime-evidence writer
already refuses) — **and the complete write operation is serialized by an
interprocess lock** (round 6: a pre-generation inspection was a
check-then-replace race — a future artifact published while an older writer
generated was downgraded, measured with a forced interleaving). The
sequence: acquire the writer lock · re-read and validate the existing
revision UNDER it · generate · validate the complete prospective artifact ·
stage to a writer-unique temporary · publish · release. *(The draft's lock
is `fcntl` — evidence GENERATION is POSIX-only in the draft, stated as a
platform bound per round 7; production may adopt cross-platform locking.
Consumption has no platform bound.)*

**Readers take ONE byte snapshot per operation** (round 7, finding 1): the
artifact bytes are read once; the digest is computed over those bytes; the
authority's `evidence_digest` is compared against that digest; those same
bytes are parsed; and that exact object enters the planner context — nothing
re-reads the path mid-operation. Concurrent nested contexts must agree on
the installed digest or refuse. The inspection
**refuses without changing a byte** when any existing component exceeds the
tool's own, or when the existing revision is unreadable (overwriting what
cannot be identified is data loss; an explicit delete is the only way past
it). Same-revision replacement is the explicit
active-runtime policy: regenerating on a new runner replaces the whole
artifact at equal revision — the reviewer's disposable-copy workflow. The
complete prospective artifact validates before the file is replaced. Every
revision scalar is **exact-typed** (`type(v) is int` — round 5 measured
`True`, `13.0` and `2.0` passing coercive equality at the top level and in
path records; a numerically equal wrong-typed value is malformed and
poisons). The artifact also records its **generator** (tool and repository
commit, `unavailable` outside a checkout) — diagnostic provenance, never a
substitute for the declaration digest.

One path record carries:

```
migration_evidence_algorithm · manifest_algorithm · runtime build identity
from_version  · source acceptance digest · source FULL-manifest hash
to_version    · output acceptance digest · output FULL-manifest hash
              · complete output manifestation
migration declaration digest · provenance
```

**Record-level consistency rules, enforced by the validator** (round 3):

```
hash(complete output manifestation) == output full-manifest hash
digest(complete output manifestation) == output acceptance digest
source identifiers resolve to exactly ONE accepted source manifestation
output identifiers resolve to exactly ONE accepted destination manifestation
```

**Selection at migration time is over the full frozen key**: runtime build
identity × source version × source acceptance digest × source full-manifest
hash × destination version × **migration declaration digest** (sha256 over
domain-separated canonical JSON of `[from, to, [statements…]]` —
`canonical_migration_bytes()`). Exactly one record or the migration does not
run: an altered migration — even one producing the identical schema — digests
differently, matches nothing, and refuses `migration-evidence-missing` with
data and stamp untouched. **Cardinality is exact ARTIFACT-WIDE** (round 4:
v5 computed expectations only for the running process's identity, so a
foreign-identity record accumulated silently): the expected set is **every
active build identity × every declared step × every accepted source
manifestation**, actual current-record keys must equal it exactly, and every
current record's runtime must **resolve** — to exactly one active
schema-runtime record and exactly one valid migration-runtime record in the
same artifact. Missing, extra, foreign, unattested, duplicate,
stale-algorithm or contradictory records each fail closed, and each has an
adversarial test. **A missing or mistyped algorithm field is malformed, not
superseded** — only explicitly superseded algorithms are ignored (`0007`
round 12's rule, applied to every record class in this artifact).
After execution the complete output is repaired, recomputed and compared
against the record's manifestation, acceptance digest AND full-manifest hash
before any stamp — full-manifest hashes because the acceptance digest is
blind to rebuildables by design (round 2, measured).

**Migration confinement is itself runtime-qualified** (round 3, finding 3).
`0007`'s runtime identity deliberately carries no authorizer probe — migration
left its scope in v10 — so its qualification cannot attest the behaviours
§4b's confinement leans on. The artifact therefore records a
**migration-runtime qualification** per build identity: authorizer API
available; `BEGIN`/`COMMIT`/`END`/`ROLLBACK`, savepoints and `RELEASE`,
`PRAGMA`, `ATTACH`/`DETACH`, and **each TEMP object class — table, index,
view, trigger and virtual table — separately** each **observed and denied**;
restoration after rejection verified. **All SIXTEEN probes are required**
(round 8 split the single TEMP probe into per-class probes because SQLite
gives each class a distinct action code, and a weak authorizer allowing TEMP
triggers passed the one probe; round 9, finding 4 added
`denies_temp_virtual_table` after a weak authorizer allowing TEMP virtual
tables — whose constructor runs before the post-step leak assertion —
passed all fifteen). **A denial counts only when the failure is specifically
authorization** — `sqlite_errorcode == SQLITE_AUTH` (message-text fallback on
Python 3.10, which lacks the attribute). Round 4 measured why: the `RELEASE`
probe held no savepoint, so `no such savepoint` — raised under a fully
permissive authorizer — was recorded as a denial; every probe's setup is now
a valid statement sequence (the savepoint exists before the authorizer is
installed), and the permissive-authorizer falsifier flips every denial
result to False. Consumption does not trust the record: the probes are
re-run live and compared — mirroring how `0007`'s `runtime_supported()`
re-derives constructor manifestations — and **artifact-level validation
poisons the qualification** on any malformed current-algorithm record,
duplicate identity, identity without an active schema-runtime record, or
violation of the single-active-runtime policy (round 4: v5 silently filtered
a malformed record and stayed qualified on the valid one beside it).
`migrate_store` requires **both** the schema-runtime and the
migration-runtime qualification before touching the store; ordinary opening
requires only `0007`'s, because it executes no confined statement.

## 5d. The closed outcome contract

**Total over expected store, SQLite, evidence, authority and protocol
failures** — and the boundary is **genuinely outermost**: parameter
validation, path conversion, canonicalization, draft-context entry, evidence
loading, the database connection, planner execution, **the kernel-result
validation, and terminal-fact derivation** all sit inside it. **The kernel
result is a validated contract** (round 15, finding 2: v16 trusted the
`OpenResult`, so a kernel returning the bare string `"migrated"` made terminal
derivation raise `AttributeError` outside the boundary and stranded a consumed
operation) — a malformed result terminalizes as `internal-error` using the best
known facts, never escapes as `AttributeError`/`TypeError`/`ValueError`. **The
validation is COMPLETE and MODE-AWARE** (round 16, finding 3: v17 checked SHAPE
only, so `migrated`/¬changed, a `created`/`adopted` in migrate mode and
`migrated` at the wrong version passed and were misreported as audit outages) —
in migrate mode `migrated` must be changed+committed at `to_version`, `current`
must be `(¬changed,¬committed)` or `(changed,committed)` at `to_version`,
`created`/`adopted` are forbidden, and the result must agree with the
`on_committed` facts INCLUDING THE BRANCH LABEL (round 17, finding 3: v18
compared only the change/commit/version tuple, so a committed `migrated`
returned as `current` passed — the branches are not interchangeable). **The
`on_committed` sink itself VALIDATES and freezes, and distinguishes a proven
commit from a no-commit position** (round 17, finding 4; round 18, finding 3:
the kernel fires `on_committed` after its COMMIT even for a no-op `current` that
changed nothing, so (T,T) is a genuine commit that must survive a later
post-commit read error while a single (F,F) is only the store's resolved
position — the kernel fires the sink at most once, so ANY second publication —
even value-identical — is a defect (M106, round 24), and a false `current`/(F,F)
must never suppress a real `migrated`/(T,T); v19 kept whichever fired first). **Terminal-fact derivation,
receipt validation and the ENTIRE post-consumption sequence are a TOTAL
boundary** (round 17, finding 5; round 18, finding 4: v19 left timestamp
generation, a hostile receipt equality, and `MigrationAuditWriteError`
construction itself outside the protected region — a receipt whose `status.__ne__`
raised, or an `audit_committed=1` the constructor rejects, leaked a raw third
exception after commit) — every step, including audit-commit sanitization and
the exception constructor, is inside the boundary; a defect terminalizes
`internal-error` from previously-FROZEN facts, a write failure is
`MigrationAuditWriteError`, no other class escapes, and a proven commit
survives. **A derivation fallback changes the PUBLIC outcome, not only the
durable record** (round 18, finding 5: v19 recorded `internal-error` durably yet
returned `migrated`) — the terminal write returns the effective outcome, so the
caller and the audit agree for every non-named return. **The connection's
cleanup scope begins the INSTANT it is opened** (round 15, finding 5) — every
opened connection is closed exactly once.
Round 5 measured the v6 boundary starting too late — an embedded-NUL path
escaped as `ValueError` from `lstat` and a mistyped `busy_timeout_ms` as
`TypeError` from division, both BEFORE any mapping ran; a public entry point
claiming totality cannot require its callers to know which preprocessing
precedes the boundary. (Round 4, finding 1: v5's boundary started
after context entry, so a malformed nested evidence field raised `TypeError`
out of the validators, non-database bytes raised `DatabaseError`, and an
unopenable path raised `OperationalError`; round 3 had closed the
invalid-SQL and free-form-string escapes.)

| failure class | closed outcome |
|---|---|
| a malformed CALL — mistyped/out-of-range `busy_timeout_ms` (exact int, 1..600000), a non-pathlike path argument | `invalid-request` |
| the path cannot be opened, canonicalized or represented at all — missing parent, embedded NUL, over 4096 bytes | `store-unopenable` |
| the bytes are not readable as a SQLite database **WHILE `open_versioned` reads/interprets them** | `invalid-store` — classified by the READ SITE (round 13 f2, round 14 f4, round 15 f3). A `sqlite3.DatabaseError` from the runtime gate, `PRAGMA` setup, connection cleanup, or after a committed publish is `internal-error`; a `DatabaseError` from WITHIN the migration hook is `migration-failed` (round 15, finding 3: v16 still caught the whole `open_versioned` call, so a hook-raised error was mislabeled `invalid-store` on a healthy store). Only the kernel's own read of the bytes is `invalid-store` |
| lock acquisition exhausted | `locked` |
| unqualified schema- or migration-runtime; malformed or poisoned schema/runtime evidence — **at any nesting depth** | `unsupported-sqlite` |
| source not an accepted manifestation | `stamped-shape-mismatch` / `foreign-shape` |
| invalid, unbound, expired, consumed, retargeted, cross-build or evidence-unbound authority | `migration-quiescence-required` |
| the dedicated operation finds no source where its authority attests one — vanished file, empty or truncated replacement | `migration-source-missing` (the path stays uncreated). Absence is proven by an `lstat` ENOENT, NEVER by `os.path.lexists` (round 13 f3). The check is re-run FRESH on a mode=rw open failure (round 16, finding 5: the source can vanish BETWEEN the pre-open `lstat` and the open — a check-to-open race — and a confirmed post-failure ENOENT is `migration-source-missing`/`missing`, not `store-unopenable`/`unknown`) |
| the attempted audit record is PROVEN not written (production) | `migration-audit-unavailable` — nothing consumed, no store access, safe to retry |
| the attempted audit record write is UNKNOWN — neither confirmed nor disproved (production) | `migration-audit-state-unknown` — the authority MAY be consumed; the host queries the durable `operation_id` before retrying (round 12, finding 3) |
| absent, ambiguous, malformed, foreign or non-matching path evidence | `migration-evidence-missing` |
| SQL execution or protocol failure during the migration | `migration-failed` |
| executed output differs from the recorded output | `migration-result-mismatch` |
| an unforeseen failure in THIS library — never a store or migration semantic | `internal-error`, phase named in the diagnostic, commit state unknown unless the phase proves otherwise (round 7: labelling a library defect `invalid-store` invited hosts to restore a healthy database) |

**Every validator type-checks a field before iterating, hashing, sorting, or
using it as a key** — the round-4 totality rule; a validator escape at
context entry is itself treated as a malformed artifact and fails closed.

Successes are equally closed: `created` · `adopted` · `current` · `migrated`.
The entry points return an `Outcome` — a value that string-compares as its
closed member and carries diagnostics separately, and that **refuses to exist
outside the vocabulary**. Detailed exception text rides the diagnostic, never
the branch value. Exactly TWO deliberate, NAMED exceptions escape the
boundary (round 6 made both classes explicit): `PackageConsistencyError` —
the build's own pieces disagree, a property of a broken package, not of the
store — and `MigrationAuditWriteError` (§5e) — the audit of an irreversible
operation failed after the operation touched the store, and its `committed`
flag is the caller's decision input. Everything else, including whatever a
`PathLike.__fspath__` or a diagnostic `__repr__` raises, maps to the closed
vocabulary.

## 5e. The migration audit and the durable authority state machine

*(Round 4 made the audit load-bearing; round 5 requires the durable
consumption rules frozen as spec text, because they are single-use
semantics, not audit formatting.)* Migration is irreversible, so the
production migration operation appends audit records the way `0007` §4e's
adoption path does: an **attempted** record before execution and a
**completed or failed** record after, each carrying the closed outcome, the
authority's identity (`operation_id`, `release_ref`, issuance window),
source and output versions with their manifestation digests, the migration
declaration digest, and the opaque `backup_ref` — all under the frozen
opaque-token caps (§5b), so audit fields cannot become prose channels.

**v34 (INV-SA11; amendment `0013/0007-sqlite-attestation`):** a migration's `attempted` audit event carries the migrating build's `sqlite_version`, `source_id` and `runtime_status()` (§5f.4): one additive key. 0018's sidecar writer copies it.

**v35 (where that key lives in the durable model below; research's stage-1 read, item 1):** INV-SA11's key is recorded on the OPERATION row, `migration_operations`. That row already holds `attempted_at`, and it is written in one transaction with the attempted event. The events table's attempted row stays payload-free, so “payload (terminal only)” stands. This annotates the frozen model and changes none of its fields. **(v36):** “none of its fields” means none of its EXISTING fields: the `runtime` field on the operation row is v34's one additive key, which this paragraph locates. In the 0013 model the row admits `refused` as well as `attested` and `verified`, because the operation's authority is consumed before the runtime gate refuses (round 5). Production's audit event never carries `refused`, since a refused build never migrates there.

**The frozen durable model is TWO tables, not one** (round 7, finding 3: a
single append-only table whose `operation_id` is globally unique cannot hold
an attempted AND a terminal event for one operation — the previous freeze
was internally inconsistent):

```
migration_operations                    migration_audit_events
    operation_id  PRIMARY KEY               event_id       PRIMARY KEY
    release_ref · backup_ref                operation_id   FOREIGN KEY
    store_path · from_version · to_version  event  (the closed enum)
    source_digest · output_digest           occurred_at
    migration_digest · evidence_digest      payload (terminal only)
    issued_at · expires_at · attempted_at   UNIQUE(operation_id, event)
    state  attempted | terminal            ≤ one TERMINAL event per operation
```

**The COMPLETE operation-row schema** (round 9, finding 2) — every authority
binding plus the resolved destination identity; the `event_id` is an
opaque `ev-<uuid4>` token (round 10, restart-safe, no counter to resume);
the schema guard is a real check that survives `python -O`, not an
`assert`. **The audit store validates every field's TYPE and grammar, not
merely the field-name set, and freezes each value DEEPLY** (round 12,
correction A: v13 accepted `backup_ref=[]` on the strength of the name set
alone, and its `_readonly` proxied dict values but passed list values through
by reference, so mutating the caller's original list mutated the published,
supposedly-immutable row). Token grammars, 64-hex digests, canonical
timestamps, int versions and the path cap are all enforced at the store
boundary, and the published copy severs every alias to caller-held mutable
state. **The `event_id` GRAMMAR is enforced, not only its uniqueness** (round
12, correction B: v13 checked the primary-key collision but never
`ev-<uuid4>`, so a faulty generator's `ev-not-a-uuid` was accepted). **The
operation-row insert IS the compare-and-set consumption, and
the entire audit state is ONE immutable value published in ONE mutation**
(round 10, finding 1: v11's `self._ops, self._events, self._event_seq = …`
was three attribute stores, so a failure on the second left the first
applied and consumed an operation with no attempted event). The draft holds
the whole state as one `AuditState(ops, events, event_ids, seq)` behind one
attribute and publishes a new one with a single assignment; production uses
one DB transaction. A failure anywhere — construction, validation, or injected
on the publish — leaves the previous state intact.

**The published state is DEEPLY immutable, and `event_id` is enforced as a
primary key** (round 11, findings 4 and correction B): v12's `AuditState`
was a NamedTuple of LIVE dicts exposed through `_ops`, so a held reference
could flip an operation to `terminal` and drop its attempted event WITHOUT
the single publish, its lock, or validation — the atomicity the whole design
exists for. `ops` and `events` are now read-only proxies over read-only rows;
the single publish is the ONLY path that changes state. And v12 keyed events
by `(operation_id, event)` and never checked `event_id`, so a repeated
generator produced two events sharing one id; the draft carries the
`event_ids` frozenset and refuses a collision exactly as the production
table's `event_id` PRIMARY KEY would. The rules:

| rule | contract |
|---|---|
| duplicate operation id on activation | the authority IS consumed — `migration-quiescence-required` (round 7 split this from the outage case v8 conflated) |
| audit storage unavailable before activation (the typed `AuditStorageUnavailable` ONLY) | its `committed` flag maps to THREE structurally distinct outcomes (round 11, correction A + round 12, finding 3: v13 collapsed `False` and `None` into one retryable outcome, and DEFAULTED `committed` to `False` so an omitted fact was fabricated as proven-not-written). `committed=False` (PROVEN not written) → **`migration-audit-unavailable`**, nothing consumed, a retry may safely re-present the authority. `committed=None` (UNKNOWN — the default; an omitted fact is never a fabricated `False`) → **`migration-audit-state-unknown`**, the authority MAY be consumed, so the host must query the durable `operation_id` before retrying. `committed=True` (the row WAS written, response lost) → the authority IS consumed → **`migration-quiescence-required`**, mint a fresh one, **AND the wrapper still writes a terminal event** (round 14, finding 2: v15 marked the operation consumed only on the normal return path, leaving a durably-consumed authority with just an attempted record). **A library/validation defect during activation is NONE of these** — it is `internal-error` (round 10, finding 4: v11 mislabelled an `AssertionError` as retryable) |
| the activation result is not a valid receipt BOUND to the COMPLETE activation | **`internal-error` BEFORE any store access**. Activation returns a typed **`ActivationReceipt`** whose `problems()` validates every scalar (round 17 corr B: an `activated`+`audit_committed=False` is impossible), and the wrapper VERIFIES BOTH atomic records: the durable operation row BINDS the exact authority — `store_path`, release/backup refs, endpoints, ALL digests, the window, `state=attempted` — AND the durable attempted EVENT is complete and bound: the exact field set, a valid unique `event_id`, `operation_id` and `event` matching, and `occurred_at == row.attempted_at` (round 17, finding 1 bound only the row; round 18, finding 1: v19 verified the attempted event only by key existence, so a malformed attempted event under the right key let the irreversible operation proceed). `duplicate` is verified to BIND THE AUTHORITY too — a row for a different store is a collision, not a replay — and its `terminal_present` must AGREE with durable state (round 17, correction A + round 18, correction B: v19 bound the duplicate row to nothing and left `terminal_present` unvalidated) |
| the terminal write is not a COMPLETE `attempted → terminal` transition | **`MigrationAuditWriteError`**. Terminal publication returns a typed **`TerminalReceipt`** (`problems()` total, and a `recorded` receipt MUST be `audit_committed=True` — round 18, correction A: `False` is contradictory, `None` belongs to the failure path), and the wrapper VERIFIES the durable state is a complete transition: the operation row is now `terminal`, exactly ONE terminal event exists (no conflicting kind), its `event_id` is valid, unique and DISTINCT from the attempted event's, it carries the exact field set, and its payload EQUALS the request field-for-field (round 17, finding 2 verified the payload only; round 18, finding 2: v19 accepted a valid payload whose operation was still `attempted`, or whose terminal event reused the attempted `event_id`). A missing, malformed, contradictory, content-mismatched, or transition-incomplete receipt raises, never returns success |
| terminal write fails (any consumed ending) | **`MigrationAuditWriteError(operation_id, store_path, facts, audit_committed)`** carrying the SAME validated `TerminalFacts` the record would have held (round 13, finding 5). `facts.transaction_committed` (tri-state) is the STORE's commit; **`audit_committed` is the AUDIT WRITE's own commit** — `True`/`False`/`None` (round 14, finding 3). When a RECOGNIZED typed terminal-sink exception carries its own `.committed`, the wrapper PRESERVES it (round 15, correction A) — but the metadata is an UNTRUSTED seam, read under protection, so an accessor that itself raises yields `None` and NEVER leaks a third exception (round 16, finding 4: v17's bare `getattr` let a hostile `committed` property escape a raw `RuntimeError` after the store committed). `facts.resulting_state` says which of `destination`/`source`/`missing`/`unaccepted`/`unknown` the store is — `False`/`None` do NOT prove it unchanged. The exception validates its OWN context — an absolute NUL-free capped `store_path` and ADJACENT endpoints (`to == from + 1`), and `audit_committed` is exact-`bool`-or-`None`, never `1` (round 14 corr B + round 15 corr B). A terminal-write failure is ALWAYS this exception, never a raw `ValueError` (round 14, finding 5); a non-mapping payload is a controlled schema error, never a raw `TypeError` (round 15, correction C) |
| `current` with no repair | terminal record written (outcome `current`); a terminal-write failure is `committed=False` — nothing changed |
| `current` with a committed rebuildable repair | the repair transaction committed: a terminal-write failure is `committed=True`, resulting version unchanged. The kernel's `OpenResult.transaction_committed` carries this fact (round 8) — the draft demonstrates it; **the production planner must report the same fact if it repairs in a separate transaction** (§5e implementation obligation) |
| every consumed outcome, INCLUDING a named escape | writes its terminal event — a spent authority with no record is indistinguishable from a crash. Round 11, finding 3: a `PackageConsistencyError` raised after consumption escaped the wrapper WITHOUT a terminal event; it is now terminalized as the audit-only outcome `package-inconsistent` and re-raised (§5d). The one escape NOT terminalized is `MigrationAuditWriteError` — it IS the terminal-write failure. Executable in the draft: `DraftAuditStore` implements both tables, atomic activation, and terminal records measured for `migrated`, the no-op `current`, `current`-with-repair, the rolled-back cell and the terminalized named escape |

**The terminal record is the EXACT per-cell contract, validated through ONE
`TerminalFacts` value shared with `MigrationAuditWriteError`** (round 13,
finding 5: v14's exception validated only the null-version rule — a strict
subset of the record's contract — so it accepted a committed `source` and a
`destination` at the wrong version; the two carriers now share
`TerminalFacts.problems()`, so the exception is exactly as strong as the
record it replaces). A terminal payload is `outcome` · `store_changed` ·
`transaction_committed` · `resulting_version` · `resulting_state` ·
`occurred_at`, over the endpoints (`from_version`, `to_version`) the operation
row carries.

**`store_changed` and `transaction_committed` are TRI-STATE** — `True`,
`False`, or `None` (unknown) (round 13, finding 1). **They are one fact
observed twice and must be the SAME tri-state value** (round 14, finding 1:
v15 rejected only a disagreement between two KNOWN values, so it accepted a
partial `None` pair like `(None, True)` and an `(None, None)` cell paired with
a known state). A disk change is exactly a commit, and neither is known without
the other. They are `None` only when genuinely unknown — a rollback ATTEMPTED
and FAILED; a confirmed rollback or a never-entered transaction is a known
`False`.

**The complete permitted `(store_changed, transaction_committed,
resulting_state, resulting_version)` tuple is validated in ONE place** —
`TerminalFacts.problems()`, shared verbatim by the record and the exception
(round 14, finding 1: v15 kept the `migrated → changed+committed` rule OUTSIDE
it, so the exception carrier was still weaker):

```
(True,  True,  destination, to_version)      migrated · current-with-repair · post-commit failure
(False, False, destination, to_version)      current, no repair
(False, False, source,      from_version)    confirmed rollback of an observed source
(False, False, missing,     NULL)            path proven absent
(False, False, unaccepted,  NULL)            store exists, not an accepted source
(False, False, unknown,     NULL)            known unchanged, state unclassified (locked, activation loss)
(None,  None,  unknown,     NULL)            rollback attempted and FAILED — genuinely uncertain
```

`(None, None)` is the ONLY `None` cell, and it requires `resulting_state
unknown`; `(True, True)` requires `destination`. `migrated` is the one outcome
whose effect is fixed — it MUST have changed and committed.

**`resulting_state` is one of `destination`, `source`, `missing`,
`unaccepted`, `unknown`, and it FIXES the version**: `destination` →
`to_version`, `source` → `from_version`, the three null-version states → NULL.
Those three are DISTINCT physical realities (round 12, finding 2): `missing`
(a path PROVEN absent), `unaccepted` (a store EXISTS and opened but is not an
accepted source), `unknown` (never observed, or a rollback not confirmed to
have restored the source).

**Each outcome permits only the states it can PHYSICALLY reach** (round 13,
finding 4: v14 froze effect/state relationships but not the outcome/state
relationship, so it accepted `locked`+source, `invalid-store`+missing,
`unsupported-sqlite`+unaccepted). The states are the union over every site the
outcome can be raised from — an in-hook refusal fires after the source is
observed and rolled back (→ `source`) or with an unconfirmed rollback (→
`unknown`):

```
migrated / current              → destination
migration-source-missing        → missing | unaccepted
migration-failed / -result-mismatch / -evidence-missing / -quiescence-required
                                → source | unknown
internal-error                  → destination | source | missing | unaccepted | unknown
                                  (round 26, finding 3: the safe fallback reaches
                                   `missing` for a proven-absent source and
                                   `unaccepted` for a read-then-rejected store)
package-inconsistent            → destination | source | unknown   (round 14, finding 5)
foreign-shape / newer / invalid-version   → unaccepted | unknown   (round 15, finding 4)
stamped-shape-mismatch          → source | unaccepted | unknown
never-read outcomes             → unknown   (locked, store-unopenable,
  (the default)                              unsupported-sqlite, invalid-store bytes)
```

**A store that OPENED and was READ but is not an accepted source is
`unaccepted`, not `unknown`** (round 15, finding 4: v16 recorded `unknown` for a
readable existing store rejected as `foreign-shape`/`stamped-shape-mismatch`,
collapsing it with a never-observed store). `unaccepted` is reserved for a store
whose existence and non-acceptance are both PROVEN; `unknown` is a store never
read (a lock, an unopenable path, unreadable bytes).

A `package-inconsistent` escape can be discovered before a transaction
(`unknown`), after a confirmed rollback (`source`), or AFTER a commit
(`destination`) — the terminal record preserves whichever facts are already
proven (round 14, finding 5: v15 permitted only `unknown`, so a post-commit
package escape's `destination` facts were rejected, producing a raw
`ValueError` that lost the named escape and left the operation unterminated).

The unifying invariants: `store_changed` and `transaction_committed` are the
same tri-state value; `(True, True)` leaves the store at the `destination` at
`to_version`; a `migrated` operation must have changed and committed; a
`migration_failed` leaves the `source` ONLY after a CONFIRMED rollback on an
observed store, the `destination` if it committed before a post-commit defect,
and `missing`/`unaccepted`/`unknown` with a NULL version otherwise. Every
`outcome` is a closed member. `event_id` is the `ev-<uuid4>` grammar; the
`state` transitions `attempted → terminal` by
compare-and-set.

Every timestamp — `issued_at`, `expires_at`, `attempted_at`, `occurred_at` —
is the canonical 32-char form (§5b); every digest 64 lowercase hex; the
token fields the frozen grammars.

Lands with the `0008` implementation; the draft demonstrates the complete
lifecycle in-process — atomic consumption under concurrency, the typed
`MigrationAuditWriteError` contract (declared, with `committed`,
`operation_id`, store identity and resulting version), and the
`migration-audit-unavailable` outcome — so the production sink implements a
frozen contract rather than designing one.

## 5f. The SQLite attestation's migration side (v34, amendment `0013/0007-sqlite-attestation`)

> **What this section adds:** the migration side of the accepted amendment `0013/0007-sqlite-attestation` (v0.12.1, sha256 `134243c63b05845a…`; design accepted at its external round 2, 2026-10-25; the owner's acceptance 2026-10-25T19:10Z), whose store-open side is 0007 §4g: the closed classification of what a `verified` build's migration may write, INV-SA10's commit-time gate over the ladder (amending the 0013-PA1 closure evidence), two annotations to §4f, and the replacement for §5c's runtime seam, carrier by carrier, with INV-SA10 and INV-SA11. The clauses it amends are edited in place and point here: §4f, §5c, §5e's attempted audit record, M11, M12, M15, M18 and §8a item 2. **Within this section, “§4c”, “§4c-ii” and “§4c-iii” mean the subsections labelled so here; every other “§N” of the amendment (§1–§8, §4a–§4f) means the subsection labelled so in 0007 §4g**. A reference to 0013's own sections says “0013”.

### 5f.1 What a `verified` build may do with a store (the amendment's §4c)

**Everything an `attested` build may do**: create, open, adopt an unstamped legacy store (0007 §4a-iv), and migrate
(0013). Each of these is already checked against the accepted evidence at the moment it happens:
- **create** writes the constructor that verification just reproduced;
- **open and adopt** match the store's own manifest against the accepted set, through the same matcher that
  discrimination (§4b step 3) just exercised on this build;
- **migrate: along the same ladder, with the same checks, as an `attested` build (v0.11; from v0.2 to v0.10, only the
  steps shown to be verified).** Three ALTER steps byte-match their reviewed expectations
  and refuse otherwise (row 5), and `open_versioned` revalidates the migrated schema against the accepted digests
  inside the migration's transaction. **That covers what those checks see, not the whole ladder.** The ladder also
  creates tables, builds and repairs indexes, writes the stamp and runs DATA steps (the v13 journal baseline among
  them; v0.8: the measured table below has no copy-and-swap rebuild step), and revalidating the schema says nothing about the rows a data step wrote.

  **The step table, measured (v0.8).** Dev classified every step by MUTATION, not by reading: each write statement of
  each path perturbed at its execution (DDL by text, DML by data, the stamp by value), the class decided by where the
  perturbation is killed. 44 paths (every accepted shape at every base v1–v14, the unstamped legacy store, a HEAD store
  with its rebuildable indexes dropped), 68 distinct steps, 3,318 perturbations on 3.45.1, and the unperturbed ladder on
  both 3.45.1 and 3.53.1, with identical end state, data and write sequence. Instrument: specs-side, dev's
  steptable.py (sha16 `5b81c3ae0d9f1b9f`), output sha16 `a1b9b6732d5ac718`. **Research re-ran it** from its own
  archive of `af1e564` by its five documented commands: the output is identical except dev's section headers, exit
  markers and output file names (research `c52b5c3b`).

  | class | meaning | steps |
  |---|---|---|
  | **(a) checked at the step** | the step's own output is compared, at the step, to a reviewed expectation | the ALTER sites. At v0.8, three (v6, v8, v10) with six statements. **At `58dd7f6` (v0.12, C1): five** (`_apply_forward` L343, L371, L396, L454, L487), **14 statements**: `ALTERS_V5_TO_V6` 3, `ALTERS_V7_TO_V8` 2, `ALTERS_V9_TO_V10` 1, `ALTERS_V15_TO_V16` 6, `ALTERS_V15_TO_V16_REDACTIONS` 2 (research's classification of the reviewer's PA1 census) |
  | **(b) revalidated** | schema-only; a perturbation is killed by the end-state check, or absorbed by drift repair and revalidation. **(v0.12) Frozen as a closed list of statement texts (below). Revalidation is not what makes a statement class (b)** | the additive CREATE TABLEs, the unique index, the rebuildable indexes |
  | **(c) neither** | every perturbation SURVIVED: value altered, row dropped, statement skipped | six steps: the v13 baseline `edge_event` inserts; the `store_epoch` mint; the `store_identity` mint; the outcome-chain UPDATE of `episodes`; the `wiki` cache DELETE; **and the STAMP, `PRAGMA user_version`, on all 43 migrating paths** |

  **The stamp decided the rule's effect until 0013-PA1 landed.** The end-state check never reads `user_version`. Research reproduced
  it independently (research `62f76f45`): with the one stamp line mutated to write head − 1, `migrate_store` returns
  `migrated` and commits a head-shaped store stamped 14. The next ordinary open refuses it loudly ("stamped v14 …
  no migration hook"), so the failure is a false success report and a store that will not open, not a silent misread.
  **Every path ends with the stamp, so until the postconditions landed, every migration on a `verified` build would
  have refused under the rule below.**

  **This is a gap on ATTESTED builds too,** independent of SQLite: the six steps' mutants are killed by nothing on any
  build. (The unperturbed ladder is correct on both builds; these are assurance gaps, not a shipped wrong output.) It
  is raised as a **separate 0013 finding (dev)**: each class-(c) step gains a POSTCONDITION checked inside the
  migration's transaction (the end-state check reads `user_version` and requires HEAD; exactly one `store_identity`
  row, well-formed; exactly one `store_epoch` row; one baseline `edge_event` per pre-existing edge, by identity; zero
  `wiki` rows after the drop; the outcome-chain step's own invariant re-read after its UPDATE). A postcondition moves a
  step into class (a). *(v0.9: the v2→v3 step's fill of a missing `observed_at` is now checked against the migration's
  ONE clock read, which `store_epoch.started_at` records: 0013 §4f, and the owner's M-Q5 ruling.)*

  **Landed, and re-measured by research (v0.9).** The postconditions are 0013 v33 §4f (internal finding 0013-PA1,
  landed at dev's `0a89696`). Research's stage-2 read found two defects, fixed at `86522c6`: the v2→v3 check took its
  outcome rows from the step, and an unreadable converted row raised instead of refusing. At `d273f19`, research re-ran
  both instruments from its own clone:
  - **The step table** (steptable.py, sha16 `5b81c3ae0d9f1b9f`, unchanged): 3,318 perturbations, **SURVIVED 0** (507
    at `af1e564`). The 507 that survived are exactly the 507 now killed at the postcondition site (set-equal on path,
    write and mode). The unperturbed ladder is identical on 3.45.1 and 3.53.1: 88 of 88 paths, end state and write
    sequence. Outputs, in evidence-sqlite-gate: steptable-rerun-at-d273f19.out (sha16 `b8e45ec23e198e7b`), its table
    (sha16 `125035f510172c20`) and its comparison (sha16 `dbb97faca3837c87`).
  - **Instrument limit, stated.** The table's generated class column still prints (c) for those six steps. Its
    classifier knows only the byte-match sites, and reads a postcondition kill as COLLATERAL: its "(a)" means "own
    byte-match", while this amendment's class (a) means "checked at the step". The per-step judge is the next
    instrument.
  - **The 0013-PA1 campaign** (pa1_campaign.py, run with `--write` on a copy of `d273f19`): 550 cells, the 507
    survivors plus 43 cells that raise the stamp. **Each is killed at its own step**, with a positional witness and the
    store unchanged, and 17 of 17 code mutants are killed. Its cells and rows equal dev's committed table cell for
    cell; only timings and the header's commit differ. Output: specs/evidence/0007-sqlite-attestation/pa1-rerun-at-d273f19.json (sha16
    `7743b898cad06ec8`).

  So **class (c) was EMPTY at `d273f19`**.

  **At `58dd7f6` (v0.11; schema 16).** Dev re-ran the step table at HEAD, and research re-ran it from its own archive.
  The two outputs agree line for line (specs/evidence/0007-sqlite-attestation/at-58dd7f6):
  - **Paths:** 98, each with end state and write sequence identical on 3.45.1 and 3.53.1.
  - **Perturbations:** 9,636, **SURVIVED 0**. Of these, 3,697 were killed at the end state, 1,663 collaterally and
    1,623 by byte-match; 2,539 were absorbed and 114 were N/A.
  - **v16's steps:** every one has its own postcondition. The ladder has 14 named steps. 12 issue a write the
    campaign perturbs; the other two are the ALTER block (DDL, byte-matched) and the edges-unchanged check.
  - **Two v16 steps the step table cannot exercise:**
    - the notice-state backfill: on 48 paths no fixture row qualifies, so a skip is ABSORBED, and `alter` is N/A
      because the UPDATE takes no parameter;
    - **the arity-inventory INSERT:** it runs once per qualifying edge, and no step-table fixture holds one, so it is
      issued on 0 of 98 paths. (Research's census; dev's read named only the first.)

    Both have their cells in the product's 0013-PA1 campaign, whose fixtures add a standing notice and arity rows:
    144 arity-inventory cells and the 5 base-15 notice-state skips, all killed at the step. The notice-state `alter`
    class is carried by the TEMP-trigger cells in tests/test_0041_notice_state.py.

  So v0.9's standing rule is **met for v16**: every v16 step is checked at the step, with campaign cells.

  **The rule (v0.11; replaces v0.2's runtime refusal, on dev's stage-1 finding).** v0.2 to v0.10 had a `verified`
  build refuse, before its first step, any path that held a class-(c) step. At `58dd7f6` that set is **empty by
  construction**, because every writing step has its own postcondition. Nothing in the package carries the set: the
  classes come from a specs-side instrument. A runtime branch reading it would never run on any shipped path, and the
  v0.9 mutant (a data step added with no postcondition while the set stays empty) could not be killed at runtime,
  because nothing at runtime knows the step exists. **The rule is therefore enforced at COMMIT TIME, as a product
  test (INV-SA10).** Every write the migration ladder issues must satisfy one of two conditions:
  - it is DDL in class (a), byte-equal to a frozen `ALTERS_*` member and checked at its step, or in class (b), the closed list below. (v0.11 read "revalidated against the accepted digests"; round 1's reviewer showed that this admits data loss.)
  - or it maps to **exactly one** named step that is checked at the step by its own postcondition, inside the
    migration's transaction, and whose campaign cells are each killed at that step.

  A commit that adds a write meeting neither condition fails the suite, so it never reaches any build. **There is no
  runtime branch:** a `verified` build migrates exactly as an `attested` build does, because the gate makes every
  data write checked at its step, on whatever build runs it.

  **What the gate must assert that today's suite does not (research, measured at `58dd7f6`).** The 0013-PA1 campaign
  maps each recorded write to a step through a hand-written table of matchers (by function name and SQL text), and
  **skips a write that no matcher claims** (`if step is None: continue`). Its `problems()` checks that every `STEP_*`
  name has cells, not that every write has a step. Research planted one unwrapped
  `UPDATE episodes SET json = json_set(json, '$.planted', 1)` before the stamp:
  - all 48 paths migrate, with the planted key committed;
  - the write maps to no step on every path;
  - the campaign's 1,480 cells are identical to the unmutated control's.

  So a regenerated table would pass dev's own mutant (specs/evidence/0007-sqlite-attestation/at-58dd7f6, §3). **The gate must assert
  the complement:** over every campaign path, every write that is not DDL maps to exactly one step. At `58dd7f6` there
  are two censuses, each with its own fixture scope (v0.12, C1):
  - **The step table's census** covers its 49 native ladder entries, HEAD drift repair included (its 49 orchestrator
    entries carry no write arrays). 432 writes match exactly one step, and none matches two. The 1,685 writes that
    match no step are all DDL: `_apply_forward` 1,645, `_repair_drift` 40.
  - **0013-PA1's census** covers the 48 fixtures the gate runs over, which add qualifying arity and notice rows. 513
    non-DDL writes each match exactly one step, and none is unmapped or ambiguous. There are 1,645 DDL writes, all from
    `_apply_forward`, none from `_repair_drift`.
  - **Both are counts of statements a leading-keyword label called DDL or DML** (§8). Every DDL statement must be
    class (a) or class (b), as SQLite classifies it (below).

  **The census must also see every write site (v0.11.1; dev's re-read, reproduced by research).** The complement runs
  over the writes the campaign RECORDS, so a write no fixture triggers is never recorded. Dev's mutant: the same
  UPDATE behind `if conn.execute("SELECT COUNT(*) FROM episodes WHERE json LIKE '%no-fixture-holds-this%'")…`.
  - The complement passes it: 0 unmapped writes, and the 1,480 cells again equal the control's.
  - **INV-SA10 therefore also requires every `.execute`, `.executemany` and `.executescript` call site, in every
    function the ladder's connection is used from, to be observed on at least one campaign path.**
    - Reads count as observations, so the SQL text never has to be classified.
    - The scope is a property, not a list, with one stated exclusion: `open_versioned`. The ladder enters it only to
      read and commit, and its six other sites belong to the create and adopt flows and the ROLLBACK (L1985, L2027,
      L2031, L2081, L2093, L2103 at `58dd7f6`; **v35:** `open_versioned` L1800, L1842, L1846, L1896, L1908, L1918
      at `d427822`, the commit that deleted three dead duplicate definitions above them, which moved every line).
    - A narrower scope, "every function in `store/migration.py`", is wrong: `unattested_marker_report` (L836, a
      read-only 0041 operator report) is never on the ladder, so its 3 sites would refuse a correct tree.
  - At `58dd7f6` the ladder's connection is used from 16 functions across the store modules, at 40 recorded sites.
    Outside `open_versioned`, every call site in those functions is observed, migration.py's 24 sites (in 5
    functions) included. On the mutant the check reports `_apply_forward:550`.

  What it does not close is stated in §8: a write moved into a helper whose only call sits on a branch no fixture
  reaches. There the unexecuted line is the call, not the execute.

  **Class (b) is a closed list of statement texts (v0.12, SA-R1-01).** Round 1's reviewer showed that a class-(b)
  declaration admitted data loss. One added site, after the stamp postcondition, ran `DROP TABLE episodes` and then
  recreated `episodes` from its own constructor. On all 48 PA1 paths the final schema equalled the control's. All 513
  non-DDL writes still mapped to one step, and no site went unobserved. But every path lost its episodes, and the
  1,480 PA1 cells equalled the control's (reproduced by dev at `58dd7f6`). Revalidation says whether the schema is
  right, never whether the rows are there. So class (b) is no longer "DDL that revalidation would catch". It is a
  closed list of statement texts whose effects are schema-only by construction, **decided per statement, never by the
  site that issues it**:
  - **(b1) additive creation.** The text is byte-equal to the head constructor DDL `SCHEMAS[SCHEMA_VERSION][k].ddl` of
    a typed key `k` whose kind is **table or index**. The gate asserts two properties of every head constructor: each
    table constructor is a plain `CREATE TABLE … (…)`, never `AS SELECT`; and none carries `IF NOT EXISTS` (at
    `58dd7f6`, 0 of 50). Such a statement cannot lose or produce a row. SQLite refuses a CREATE for a name that
    exists, so it can only create an absent, hence empty, table, or an index, which holds no application row. A UNIQUE
    index that cannot build refuses the migration, which is fail-closed, not data loss. The only way to make an
    existing name absent is a statement outside this list.
  - **(b2) rebuildable-index repair.** The text is exactly `DROP INDEX IF EXISTS <name>`, where `<name>` is a head
    index whose policy is `rebuildable`. The schema validator already limits that policy to `REBUILDABLE_KINDS`,
    because "repairing a {kind} would destroy data". Its recreate is a (b1) statement.

  **Other kinds are outside (b1), even when additive:** trigger, view and virtual table. A trigger created before a
  later data step acts on the rows that step writes. A head constructor of a new kind needs its own review before the
  list grows.

  **Everything else that is DDL is not class (b).** It is either class (a) (unchanged: the freeze does not reopen the
  reviewed ALTERs), or it owes what any data step owes: a named step, an independent preservation or transformation
  postcondition at that step inside the transaction, and campaign cells killed there. Otherwise the commit-time gate
  refuses the commit. "Everything else" includes:
  - any `DROP TABLE`;
  - a `DROP INDEX` of an index that is not rebuildable (the `op_key` UNIQUE index decides which writes are accepted);
  - a table rebuild, even one that keeps the row count;
  - `CREATE TABLE … AS SELECT`;
  - `ALTER TABLE … RENAME` or `DROP COLUMN`.

  A row-count postcondition after the stamp would catch the reviewer's instance, but not the class: a
  recreate-and-refill keeps the count.

  **What a site declaration still does:** it says where the census expects DDL, so "issue DDL from an undeclared site"
  stays a mutant. It no longer makes a statement class (b): the reviewer's site was declared class (b), and the gate
  refuses it on the `DROP TABLE`.

  **SQLite decides what is a write, not the statement's first word (v0.12).** Before v0.12 the census took a
  statement's kind from a leading-keyword label (`specs/evidence/0013/steptable.py`, `_kind`): CREATE, ALTER or DROP
  meant DDL; INSERT, UPDATE, DELETE or REPLACE meant DML; anything else was READ. So dev's two further mutants
  walked past it, each losing every path's episodes:
  - `"/* repair */ DROP TABLE episodes"` gave a census with no `DROP TABLE` at all, and the freeze found nothing
    outside it;
  - `WITH doomed AS (SELECT 1) DELETE FROM episodes` after the stamp gave a census identical to the control's (513 /
    1,645), so the write complement was blind as well.

  The census instrument therefore installs an authorizer on the ladder's connection. It records each statement's set
  of action codes as SQLite prepares it. The instrument is specs-side and runs at commit time; production installs no
  authorizer (§4c-iii, carrier (ii)). The authorizer is already 0013's confinement mechanism, so this adds no new
  primitive. **The classification is a closed table over all 33 authorizer action codes (v0.12.1); a code not in it
  refuses** (a later SQLite may add one):

  | action codes | class |
  |---|---|
  | `CREATE_TABLE`, `CREATE_INDEX`, `DROP_TABLE`, `DROP_INDEX`, `ALTER_TABLE` | **schema write.** It must be class (a) or (b) by its text |
  | `INSERT`, `UPDATE`, `DELETE` naming a table other than `sqlite_master`, `sqlite_schema` or `sqlite_temp_master` | **row write.** It must map to exactly one named step. DROP TABLE also reports a `DELETE` naming the dropped table, so it is a row write as well |
  | `INSERT`, `UPDATE`, `DELETE` naming `sqlite_master`, `sqlite_schema` or `sqlite_temp_master` | **schema bookkeeping, legitimate only in a call whose action set also holds a schema-write action** (measured: CREATE INDEX reports `INSERT sqlite_master`; ALTER and DROP INDEX report `UPDATE`/`DELETE sqlite_master`). In any other call it is refused: a direct write to the schema table, **(v37)** except the pre-3.41 `declare_vtab` sequence below, under all three of its conditions |
  | `REINDEX` | legitimate only in a call that also holds `CREATE_INDEX` for the same name (CREATE INDEX reports it, measured); otherwise refused |
  | `PRAGMA` | **the stamp** is exactly (`user_version`, the head version). Any other pragma must be on a closed read list, enumerated from the ladder at the pin, by name and argument shape; a read can carry an argument too (`table_info`, `t`). `writable_schema`, and any pragma not on the list, is refused |
  | `TRANSACTION`, `SAVEPOINT` | the planner's own; not steps |
  | `READ`, `SELECT`, `FUNCTION`, `RECURSIVE` | reads |
  | `ATTACH`, `DETACH`, `ANALYZE`, `CREATE_VTABLE`, `DROP_VTABLE`, `CREATE_TRIGGER`, `DROP_TRIGGER`, `CREATE_VIEW`, `DROP_VIEW`, and every `CREATE_TEMP_*` and `DROP_TEMP_*` (eight codes) | **refused outright.** ANALYZE also reports `CREATE_TABLE sqlite_stat1`, so it would fall outside (b) anyway (measured) |

  **(v37) One callback sequence no executed statement owns (the first branch run's group A; research's measurement, the owner's word 2026-10-27, “Yes, build v37”).** An authorizer callback is a write only if it authorizes a statement SQLite will execute. Before SQLite 3.41, a connection's FIRST use of a table-valued pragma (`SELECT * FROM pragma_table_xinfo(?)`, `schema_version.py`, `manifest`) initialises the pragma's eponymous virtual table through `sqlite3_declare_vtab`. That parse's `sqlite3EndTable` issues a nested `UPDATE sqlite_master … WHERE rowid=…`, and in those releases `sqlite3NestedParse` clears the parse mode that suppresses the authorizer, so the user's authorizer is asked about that UPDATE. Its VDBE is discarded and never stepped. Measured on 3.40.1 against 3.45.1, both built from sqlite.org's amalgamations with identical flags:
  - the sequence is exactly six callbacks, right after the statement's `SELECT`: `UPDATE` on `main.sqlite_master` for `type`, `name`, `tbl_name`, `rootpage` and `sql`, in that order, each with no trigger or view argument, then `READ main.sqlite_master.ROWID`;
  - it comes once per connection per pragma module, and never on a later use on that connection;
  - nothing changes: `schema_version`, `data_version`, `total_changes()`, every `sqlite_master` row and the file's bytes are equal before and after;
  - 3.41.2 to 3.45.1 begin `sqlite3NestedParse` with `if( pParse->eParseMode ) return;` and do not ask; 3.40.1 lacks the line. The CI matrix measured the sequence on 3.34.1, 3.37.2, 3.40.0 and 3.40.1, and not on 3.45.1 or later.

  **The gate attributes the sequence as `declare_vtab` bookkeeping, not a write, only when all three hold:**
  1. it is that exact sequence, immediately after the call's `SELECT`;
  2. it comes in the PREPARE of a call that references an eponymous virtual table not yet used on that connection;
  3. THIS build's own probe, run when the gate starts, reproduces it on a scratch database with `schema_version`, `data_version`, `total_changes()` and the `sqlite_master` rows unchanged. That is a measured property of the build, never a version range.

  Rule 5's replay equivalence still holds for every path. Any other `UPDATE` of the schema table, or this sequence on a build whose probe does not reproduce it, is a write, as before. Priming each pragma module before the census authorizer is installed is REJECTED: it would hide a first use from the observer instead of attributing it. **The callbacks are not inert:** an authorizer that DENIES them makes the read itself fail ("not authorized") on 3.40.1, while 3.45.1 reads. Production installs no authorizer. The model's migration authorizer is installed only around declared migration statements, and none of them is a table-valued pragma (dev's census of the `set_authorizer` sites at `d587600`). Research's evidence is in the research repository at commit `46869de1` (its run1b-groupA evidence directory).

  **One channel no SQL statement shows (v0.12.1, dev's measurement).** `Connection.setconfig(SQLITE_DBCONFIG_WRITABLE_SCHEMA,
  True)` is a C-API call: it fires no authorizer callback and no trace (measured). After it, `DELETE FROM sqlite_master
  WHERE name='episodes'` reports only `DELETE` and `READ` on `sqlite_master`, which the table above refuses as a direct
  schema-table write. **The census also asserts, after every proxied call, that `getconfig(SQLITE_DBCONFIG_WRITABLE_SCHEMA)`
  is False and `SQLITE_DBCONFIG_DEFENSIVE` is unchanged**, since nothing else can see `setconfig`. Scope, as dev
  measured it: on one connection this route did not lose rows. The recreate was refused ("table episodes already
  exists", from the stale schema cache), and revalidation would see the row gone from `sqlite_master`. Across a reopen
  it did lose them. So it is a gap in the rule, closed here, not a demonstrated escape on the ladder's single
  connection.

  **Each action set belongs to one call, not to a position in the trace.** The census reaches `migrate_store`'s
  connection through 0013-PA1's existing seam (`specs/evidence/0013/pa1_campaign.py`: `mig.sqlite3 = Shim`, whose
  `connect` returns the recording proxy), opened with `cached_statements=0`. The rules:
  1. **Attribution is per proxied call.** The proxy clears an action buffer before each `execute` or `executemany`,
     and takes the buffer after. Transaction-control actions and their traces go to their own TXN records.
     Association by sequence is unsafe. Measured on a legacy-isolation connection: the INSERT's action came first,
     then the implicit BEGIN's action and its trace, then the INSERT's trace.
  2. **The class-(a)/(b) byte-equality and the step predicates compare the call's TEMPLATE,** never the traced
     text, which is expanded with the bound values.
  3. **The trace's job is completeness.** Every trace and every authorizer callback must fall inside a proxied
     call; an orphan is a refusal (a cursor obtained around the proxy, for example). There is no per-call count. A
     table-valued pragma runs a nested statement, so `SELECT * FROM pragma_table_xinfo(?)` (`schema_version.py`,
     `manifest`) traces twice in one call: on the ladder, a per-call count refused the clean control 1,904 times
     (dev's census). A two-statement string cannot reach `execute` or `executemany` at all, because both raise
     `ProgrammingError` ("You can only execute one statement at a time"). A nested statement's writes are already in
     the call's action set, because attribution is per call, not per trace. **(v35)** Cell:
     `tests/test_0013_sa10_gate.py::test_the_clean_control_admits_a_call_whose_nested_pragma_traces_twice`, red against a
     per-call trace count (mutation-table row `per-call-trace-count`).
  4. **`executescript` on the ladder's connection is refused outright.** That makes `schema_version.py`'s own rule
     ("Never `executescript`: it issues an implicit COMMIT") a gate. At `58dd7f6` no `src/veracium/store/` module
     calls `executescript` or `executemany`, and the instrument depends on neither fact.
  5. **(v35) Replay equivalence: what makes the census complete** (research's stage-1 read, item 5; built at I1, `specs/evidence/0013/sa10_gate.py` with its comparator `specs/evidence/0013/sa10_digest.py`). Rules 1–4 classify what the census records. Nothing in them proves that every write WAS recorded, and a Python proxy's opacity is not a closable domain: raw file I/O on the store goes through no connection at all. So after each census path the gate replays the recorded calls on a byte copy of the pre-path file and compares content:
     - **The record:** each call's parameters BY VALUE at call time (`executemany`'s sequence materialised) and its outcome (returned, or raised with its class). The connects, the `isolation_level` sets and the TXN calls (`commit`, `rollback`, the context manager's exit) are replayed events. Replay asserts each call's outcome, in both directions.
     - **The pre-state:** a byte copy of the fixture file, taken after the fixture build has closed its connection. Never `backup()` or `VACUUM INTO`: they re-lay pages, and they are not the pre-state the ladder saw.
     - **The comparator** runs in a fresh `python -I` subprocess, on the closed files, read-only, where the code under test cannot reach it. It digests every `sqlite_schema` row's `type`, `name`, `tbl_name` and `sql`, but not `rootpage`, which is physical placement. It digests every row of every object of type `table`, internal ones included, as (rowid, then each column's `typeof` and value) ordered by rowid. And it digests `user_version`, `application_id`, the schema cookie, `encoding`, `page_size` and `auto_vacuum`. **The real file's `PRAGMA integrity_check` must be `ok`**, because index entries are not in the row digest: a raw write can corrupt an index page while every table scan stays equal. It refuses rather than guesses on a virtual table, a table without a rowid, and a non-empty journal or WAL beside the file.
     - **The build is ASSERTED by argv, not only recorded.** The census passes its own `sqlite_version()` and `sqlite_source_id()`, and the comparator refuses when its own build differs. The control changes one character of the `source_id`. On this project's machines every interpreter loads the same system SQLite, so running the comparator under another interpreter would not vary the build.
     - **No normalisation.** The comparator accepts none, and at `a187209` the ladder needs none: no SQL-side clock or randomness (the clock is one Python read bound as a parameter, §4f), no `AUTOINCREMENT`, no `WITHOUT ROWID` table, no `INSERT … SELECT`, and no `SAVEPOINT`. A later need is shown to vary before it is normalised, and comes back as a change to this rule.

     **The gate's claim, exactly:** *no store content changes during a census path except by a recorded call, against any code that does not write to the instrument's own objects.* **Two limits, stated so nobody believes the check closes them:**
     - **Influence through a recorded read.** Suppose a hidden write W is read by the step, and a later RECORDED write overwrites W's effect. Real and replay are then equal, because replay uses the recorded parameters, which W shaped. This is no wider than code that computes the same parameters in Python, so it is the step postcondition's question, as for any data step. **NEXT-ROUND:** record read results too, and have replay assert equal results for each recorded read.
     - **Forging the record.** Code that writes into the instrument's own objects (found through `gc`, frames or closure cells) can make the record match. Such code names census internals that do not exist in production. That is the reviewer's question, not the gate's.

     Cells, at `4265dae`:
     - `tests/test_0013_sa10_gate.py::test_replay_equivalence_catches_each_unrecorded_route_with_the_allowlist_removed` covers six routes, with the allowlist (rule 6) replaced by a forwarding proxy: a `blobopen` write; `backup()` into the ladder's connection; a write on the real connection with the instrument removed; raw file I/O changing a row; raw file I/O corrupting only an index page, which `integrity_check` catches; and `set_authorizer(None)` followed by a DELETE through `execute`. That last DELETE is a recorded call, so replay reproduces it, and the heartbeat refuses it instead (a call that ran but traced nothing).
     - `test_the_allowlist_refuses_each_connection_route_and_replay_still_sees_the_file_routes` runs the same six routes with the allowlist in place.
     - The record: `test_parameters_are_recorded_by_value_and_replay_compares_every_outcome` and `test_the_context_manager_replays_commit_and_rollback_and_a_foreign_connect_is_refused`.
     - The comparator: `test_the_comparator_refuses_another_build_and_names_each_section`.
     - The clean control, with replay equal on every path and nothing normalised: `test_the_gate_passes_the_clean_ladder_on_every_path_and_entry`.
  6. **(v35) The proxy is a closed allowlist, kept as defence in depth and for its error messages** (research's stage-1 read, item 4, and dev's decisions on it). Measured on 3.45.1, three `sqlite3.Connection` methods write with no authorizer or trace callback: a `blobopen` write, `backup()` into the connection, and `set_authorizer(None)` before a `DELETE`. At `58dd7f6`, every census proxy forwarded the names it did not list to the real connection. The gate's connection wrapper admits only the names the ladder uses and refuses every other name, `_real` and `__dict__` included:
     - The allowlist is enforced in `__getattribute__`, and the real connection is held in a closure.
     - A refused name is recorded before it raises, so code that swallows the error still fails the path.
     - `__enter__` and the cursor wrapper's `__iter__` return the wrapper. `execute` returns a cursor wrapper that refuses `.connection` and the cursor's own `execute*`.
     - Nothing either wrapper hands back is a real `Connection`, `Cursor` or `Blob`: this is checked by type on every return, so the next method of that shape needs no new rule.
     - A census over `dir(sqlite3.Connection)` and `dir(sqlite3.Cursor)` fails on any public name that is neither allowed nor refused.
     - `commit()` and `rollback()` are proxied TXN calls (rule 1).

     **The seam also covers `release_migration`'s own two connections** (`_observe` and `_repair_current`), so a write added to a `release_migration` function is recorded and attributed. Replay would see that write in any case; the seam is what attributes it.

     **(v38) The census's input surface is closed too** (the round-3 verdict, SA-R3-01; research's stage-1 read). Rule 6
     closed the wrapper's names. The inputs that reach the real `sqlite3` before a wrapper exists were open, and each
     could run caller code outside the census:
     - **`connect`'s arguments.** `Census.connect` refuses, before it calls `sqlite3.connect`, any positional argument
       after the path, any keyword but `timeout`, and a `timeout` that is not exactly an `int` or a `float`. The refusal
       is recorded (“connect with …”). The seamed callers pass the path, or the path and `timeout`. The verdict's
       witness passed `factory=`: a `Connection` subclass whose constructor wrote and committed before the authorizer
       and the trace callback were installed. Replay called the same factory, so replay equalled the store on every
       path.
     - **The module seam's attributes.** The seam that stands for `sqlite3` in the seamed modules exposes `connect`,
       through the census, and `Error`, `DatabaseError` and `OperationalError`, the names those modules read at run
       time. Every other name is refused and recorded (“sqlite3.<name> through the module seam”), `Connection`
       included. A cell derives the seamed modules' run-time `sqlite3` names from their syntax, annotations excluded,
       and requires them to equal that set. Before v38 the seam forwarded every name but `connect`, so
       `sqlite3.Connection(path)` wrote with no census at all. On the path research measured, replay equalled the
       store by rule 5's first limit, and the same write made after the migration was caught.
     - **The values a set may carry.** A recorded set admits `isolation_level` as `None` or exactly one of `""`,
       `"DEFERRED"`, `"IMMEDIATE"` and `"EXCLUSIVE"`; `row_factory` as `None` or `sqlite3.Row`; and `text_factory` as
       `str` or `bytes`, the last two compared by identity. Anything else is refused and recorded (“setting
       connection.<name> to …”). The ladder sets only `isolation_level`. A Python function as `row_factory` is caller
       code that replay would run again, and SQLite calls it with the REAL cursor, whose `.connection` is the real
       connection. Research measured a `blobopen` write from there that no callback reports; the complete gate refused
       it on 50 of 57 paths, so it was not an escape, and v38 closes it by value.
     - **Replay re-checks its record.** Before it reconnects or sets anything, replay applies the same two checks to
       each recorded `connect` and set, and refuses (“replay refuses connection N's recorded …”) rather than running
       recorded behaviour.

     Cells: one product mutation per route (a factory by keyword, a factory by position, a direct `Connection`, a
     function as `row_factory`, a function as `text_factory`), each refused across the complete gate, with the clean
     ladder green on every path. INV-SA10's mutation table carries them as rows (`tree-connect-factory-keyword`,
     `tree-connect-factory-positional`, `tree-direct-connection`, `tree-row-factory-function`,
     `tree-text-factory-function`), with the gate mutants that undo each check
     (`sa-r3-01-connect-forwards-the-callers-arguments`, `sa-r3-01-the-seam-forwards-the-module`,
     `sa-r3-01-set-values-unchecked`, `sa-r3-01-replay-runs-recorded-behaviour`).

     Cells: `test_the_proxy_refuses_each_route_and_records_the_refusal` (one case per refused route), `test_a_swallowed_refusal_is_still_recorded`, `test_no_allowed_name_hands_back_a_real_connection_cursor_or_blob`, `test_every_public_name_of_connection_and_cursor_is_allowed_or_refused` and `test_release_migration_opens_its_connections_through_the_seam`, all in `tests/test_0013_sa10_gate.py`.

  The statement cache is off because the authorizer fires on PREPARE. With Python's default cache, a re-executed
  statement gives no callback (measured: 2 callbacks, then 0; with `cached_statements=0`, 2 and 2). **The
  leading-keyword label stays only as a cross-check, and it refuses in ONE direction.** A call whose action set
  shows a write the label does not call one is refused: that is the escape direction (N6, N7). The reverse, a label
  of DDL with no schema action, is allowed only for a (b2) text. `DROP INDEX IF EXISTS` of an index already gone
  (dropped with its table, on a drifted store) reports no action at all (measured), and is a (b2) no-op. Any other
  DDL text with no schema action is refused. With `IF NOT EXISTS` excluded from constructors, (b2) is the only
  legitimate no-op.

  **The gate's fixture scope.** The 48 PA1 paths issue no repair statement, so a (b2) control over them alone would be
  vacuous. The gate's path set adds two drifted HEAD stores: one with a rebuildable index present but wrongly defined,
  whose repair drop is a real (b2) statement (C2); and one with the index missing, whose repair drop is a (b2) no-op
  (C3; the step table's drifted-HEAD fixture is this case).

  **The cells.** Each is a product test at implementation, demonstrated red against the gate mutant named beside it:

  | # | cell | expected | gate mutant it kills |
  |---|---|---|---|
  | N1 | **the reviewer's mutant**: `DROP TABLE episodes`, then `episodes`' constructor, after the stamp postcondition, at a site declared class (b) | refused, naming `DROP TABLE episodes` and its site (dev's census: 48 outside) | admit every statement at a declared class-(b) site |
  | N2 | a count-preserving rebuild with no named step: `CREATE TABLE episodes_rebuild AS SELECT * FROM episodes`; `DROP TABLE episodes`; `ALTER TABLE episodes_rebuild RENAME TO episodes` | refused; all three statements are outside | match (b1) by prefix rather than byte-equality; a row-count postcondition in place of the list |
  | N3 | drop and recreate the `op_key` UNIQUE index | refused on the `DROP INDEX` | widen (b2) to every index |
  | N4 | N1's two statements as one `executescript` | refused outright (rule 4) | allow `executescript` and classify the script by its first statement |
  | N5 | a head table constructor written `CREATE TABLE … AS SELECT …` | refused by the plain-constructor assertion | drop the assertion |
  | N6 | dev's comment-prefixed DROP (`"/* repair */ DROP TABLE episodes"` in N1) | refused: SQLite reports `DROP_TABLE` and a `DELETE` on `episodes` (dev's census: 48 outside, 48 label disagreements) | classify by the leading keyword |
  | N7 | dev's `WITH doomed AS (SELECT 1) DELETE FROM episodes` after the stamp, at no step | refused: a row write mapped to no step (dev's census: 48 unmapped, 48 label disagreements) | the same; a write complement over labelled DML only |
  | N8 | `executescript("SELECT 1; DROP TABLE episodes")` on the ladder's connection | refused outright (rule 4) | classify a script by its first statement |
  | N9 | `PRAGMA writable_schema=ON` at a declared site | refused: not on the pragma read list | treat every pragma other than the stamp as a read |
  | N10 | a head constructor written `CREATE TABLE IF NOT EXISTS …` | refused by the assertion | drop the assertion (a recreate of an existing name becomes a silent no-op, a second legitimate-looking no-op beside (b2)'s) |
  | N11 | a statement run through a cursor obtained around the proxy | refused: its trace and callbacks fall outside any proxied call | attribute actions by trace sequence, or skip the orphan check |
  | N12 | `setconfig(SQLITE_DBCONFIG_WRITABLE_SCHEMA, True)`, then `DELETE FROM sqlite_master WHERE name='episodes'` | refused, twice over: the `getconfig` assertion after the `setconfig`'s call, and a schema-table write in a call with no schema-write action | classify a `sqlite_master`-only write as a read; drop the `getconfig` assertion |
  | N13 | **(v35)** a `blobopen` write to `episodes.json` at a declared site | refused at `connection.blobopen`: the name is not on the allowlist (rule 6). The channel fires no authorizer or trace callback, so rules 1–4 never see it | forward every name the proxy does not list to the real connection |
  | N14 | **(v35)** `backup()` of an empty in-memory database into the ladder's connection. Through the allowlist there is no handle on the real connection, so the cell takes the handle a forwarding proxy lends, `conn.cursor().connection` | refused at `connection.cursor` | the same |
  | N15 | **(v35)** `set_authorizer(None)`, then `DELETE FROM episodes` | refused at `connection.set_authorizer` | the same |
  | W1 | **(v35)** the context manager: `with conn as c: c.blobopen(...)` | refused: `__enter__` returns the wrapper, and `blobopen` is refused on it | `__enter__` returns the real connection's `__enter__()` |
  | W2 | **(v35)** the real connection reached through a cursor: `conn.execute(...).connection`, and the same through `iter(...)` | refused: `execute` returns a cursor wrapper that refuses `connection`, and the wrapper's `__iter__` returns the wrapper | `execute` returns the real cursor; the wrapper's `__iter__` returns the real cursor |
  | W3 | **(v35)** the wrapper's own attributes: `conn._real`, `conn.__dict__`, and setting `_real` | refused: the allowlist is enforced in `__getattribute__` and the real connection lives in a closure | the allowlist written in `__getattr__`, with the real connection stored as an instance attribute (Python consults `__getattr__` only for a name the object lacks); a `__setattr__` that forwards every name to the real connection |
  | C1 | **control: the 48 PA1 paths at `58dd7f6`** | **dev's authorizer census** (CPython 3.14.7 / SQLite 3.45.1, through the Shim, `cached_statements=0`): 0 errors, 0 paths losing episodes. Schema writes: (a) 314 + (b1) 1,331 = 1,645, equal to the label's census and to research's classification of the reviewer's. Row writes: 465, each mapped to exactly one step, which with the 48 stamps makes the 513 non-DDL writes. 0 outside, 0 unmapped, 0 orphans, 0 label disagreements | — |
  | C2 | **control: a drifted HEAD store whose rebuildable index is PRESENT with the wrong definition** (a same-named index on another column) | its repair's `DROP INDEX IF EXISTS` reports a `DROP_INDEX` action and is (b2); the recreate is (b1); 0 outside; at least one (b2) statement with a `DROP_INDEX` action. **Measured by dev's census** (fixture `wrong`): the open is `current`, with 1 (b2) carrying `DROP_INDEX` and 1 (b1), and 0 outside, disagreements or refusals | a gate with no such fixture in scope (C2 then fails as "no (b2) observed"). The step table's drifted-HEAD fixture alone does not satisfy C2: it drops every rebuildable index (`steptable.py` L799–L809), so every repair drop there is a no-op (C3) |
  | C3 | **control: a drifted fixture whose repair finds an index already absent** | `DROP INDEX IF EXISTS` reports no action and is classed a (b2) no-op, not refused. **Measured by dev's census** (fixture `missing`, every rebuildable index dropped): 20 (b2) no-ops and 20 (b1), 0 outside, disagreements or refusals | refuse every label/SQLite disagreement in both directions |

  **(v35) The cells and their demonstrations, at `4265dae`.** The cells are in `tests/test_0013_sa10_gate.py`:
  - N1–N12: one `test_n…` function per cell or pair of cells.
  - N13–N15: `test_n13_n15_a_zero_callback_channel_at_a_declared_site_is_refused`, with cases `N13 blobopen`, `N14 backup into the connection` and `N15 set_authorizer(None), then DELETE`.
  - W1–W3: `test_the_proxy_refuses_each_route_and_records_the_refusal`, with cases `connection.blobopen (through with)` (W1), `cursor.connection` and `cursor.connection (through iter)` (W2), and `connection._real`, `connection.__dict__`, `setting connection._real` and `setting connection.autocommit` (W3).

  **“Demonstrated red against the gate mutant” is carried by INV-SA10's mutation table**, `specs/evidence/0013/sa10/mutation-table.json`. Its runner is `specs/evidence/0013/sa10_mutants.py`, whose `--check` validates the committed table without re-running it, and `tests/test_0013_sa10_mutants.py` gates it. The table works as follows:
  - Each row applies one mutant to a copy of the tracked tree.
  - A row is KILLED only if every cell it names fails, and a failure counts only through a classifier whose control (an unrelated `TypeError`) must read UNCLASSIFIED.
  - The unmutated copy must be green both first and last.
  - Where a row declares a reason, that text must appear in a named cell's failure.

  **As committed at `4265dae`, the table holds 40 rows, every one KILLED: 36 gate mutants and 4 ladder mutants. The classifier control reads UNCLASSIFIED.** Research re-derived these figures from the table's rows, not from its summary. Every N-row and W-row above is named by a row:
  - N1–N12: the mutants in this table's last column.
  - N13–N15: `N13-N15-forward-unknown-attributes`.
  - W1: `enter-returns-real`.
  - W2: `execute-returns-real-cursor` and `cursor-iter-returns-real`.
  - W3: `W3-allowlist-in-getattr` and `W3-setattr-forwards`.

  The remaining gate rows remove one of the gate's own checks, among them the comparator's and replay's (rule 5).

  **The standing rule for later steps (v0.9, now mechanical).** A later schema version may add a data step, or any
  write that is not class-(a) or class-(b) DDL. Such a step owes three things before it lands: a named step, a
  postcondition at the step, and campaign cells on 0013-PA1's pattern. The gate refuses the commit otherwise. The
  step table's classifier still prints (c) for postcondition-killed steps (its stated limit). Read SURVIVED, not that
  column.

  **Not covered by the step table** (named in its output): `source_revocations` rows on 29 paths (the fixture row
  failed its CHECK; no step touches the table); adoption of an unstamped HEAD store; real third-party historical stores
  (every fixture is rebuilt from the accepted DDL); and perturbations on 3.53.1.

**Where a step cannot be verified on this build, it refuses at that step, naming the step**: the owner's "refusal
only where the schema evidence cannot be verified".

### 5f.2 Two annotations to §4f (the amendment's §4c-ii)

This package touches 0013, so it carries 0013's corrections. Neither edits the landed text.

1. **The finding's counts.** §4f says the six steps' surviving perturbations were "597 data perturbations and 43 stamp
   perturbations". **Measured, they are 421 data and 86 stamp, 507 in all**: steptable on `af1e564`, with DML 421
   (outcome chains 6, wiki 4, `store_identity` 15, baseline 297, `store_epoch` 99) and STAMP 86 (43 paths, each
   lowered and skipped). The 0013-PA1 table's 550 cells are exactly those 507, set-equal on path, write and mode, plus
   the 43 stamp-raised cells the campaign adds. The closure is complete, and only the paragraph's numbers were wrong.
   Research wrote them (research `7bbed8e4`), and cannot reconstruct their source.
2. **A key the dump omits.** §4f's v2→v3 postcondition compares present keys as their declared type, and requires
   every added key to equal its declared constant default. It does not say how a declared key ABSENT from the
   converted row reads. The rule it means, and the one implemented at `86522c6`: **a declared key absent from the
   converted row reads as its declared constant default** (the serializer omits the procedural markers when None,
   0037 §2), **and a field with no constant default (required, or `default_factory`) absent from the converted row is
   refused.** Research checked it is sound: a non-default raw value the dump loses is still refused, and an omitted
   default reads identically on every load.

### 5f.3 The replacement for §5c's runtime seam (the amendment's §4c-iii)

**Which carrier each clause binds.** 0013 §5c's seam has one carrier today (the model) and one to come (0008's
production artifact). Production's ladder is a third carrier, which does not implement the seam. At `58dd7f6`, no
`src/` module installs an authorizer or reads a migration-runtime or path-evidence record: `git grep` finds 0 hits
each for `set_authorizer`, `migration_runtime`, `authorizer_probes` and `migration_0013_evidence` (research, re-run
by dev). 0013 itself places §5c's production artifact with 0008 (M11, M12: "Production with `0008`").

| carrier | what this amendment requires of it | when |
|---|---|---|
| **(i) the 0013 model**, `specs/migrations_0013.py` | **all of this section**: live probes, the identity-free path key, `generated_on`, the cardinality change and the retirements. A1–A15, each red against its mutant | at the model's next revision, as part of implementing this amendment |
| **(ii) production `migrate_store`**, through `open_versioned` | **only the runtime gate changes:** `runtime_status()` ∈ {`attested`, `verified`} in place of `runtime_supported()`, at `schema_version.py` L1939 (`open_versioned`, at `58dd7f6`; **v35:** L1754 at `d427822`) and `release_migration.py` L1005 (`_preflight_classify`, unchanged at `d427822`). Everything else stays as at `58dd7f6`: each step's own postcondition inside `_apply_forward` (0013 §4f); the stamp (`migration.py` L549); then `_validated_current(…, require_stamp=True)` before COMMIT, which checks that the stamp reads HEAD, accepted-digest membership, typed drift repair and complete revalidation. **No authorizer, no live probe, no path record:** accepted 0013's deferral, carried unchanged, not a new limit. P1–P3 | when this amendment is implemented |
| **(iii) 0008's production artifact** | inherits (i) | when it lands, as 0013 already says |

**The consequence, stated plainly:** implementing this amendment lets a `verified` build migrate in production with
exactly the runtime confinement today's attested 3.45.1 has, which is none. Production's ladder executes only its own
reviewed statements. 0013's authorizer defends against an accidental DECLARED statement in the model's declarative
migrations ("not a sandbox", 0013 §4b). The stamp is written inside `_apply_forward`, so the revalidation runs after
it, inside the same transaction and before COMMIT. A refused revalidation rolls the stamp back with everything else.

**Measured, at `58dd7f6`** (the reviewer's runtime-contract probe, re-run by research on CPython 3.14.7, specs/evidence/0007-sqlite-attestation/r1-repro-at-58dd7f6; the
reviewer's 3.53.1 run was CPython 3.12.14). On 3.53.1, all sixteen confinement probes pass live, no migration-runtime
record matches, and the model's migration gate is false. Relaxing 0007's gate alone would therefore leave every
`verified` build unable to migrate in the model. On 3.45.1 the gate is true. A permissive authorizer leaves 1 of 16
probes true and the gate false on both builds.

**0013 §5c binds three things to one runtime build identity, and each is replaced, never merely dropped:**

| 0013 §5c obligation | replaced by | carriers | why it holds without a per-build record |
|---|---|---|---|
| schema-runtime qualification (`runtime_supported()`) | `runtime_status()` is `attested` or `verified` (§4a–§4b) | (i), (ii), (iii) | verification re-derives the accepted evidence on this build at this open, and the record was never trusted for that (S69) |
| migration-runtime qualification: a record for this identity, re-run live and compared | **the sixteen probes run LIVE on every `migrate_store`, and all sixteen must be True**, before the store is touched; otherwise `unsupported-sqlite`, naming the first failing probe | (i), (iii); not (ii), which installs no authorizer | 0013 already requires all sixteen True ("All SIXTEEN probes are required"), so a record could only say "all True". The live run decides, as it already did ("Consumption does not trust the record"). Once the required values are fixed, comparing against a record adds nothing |
| a path record keyed by runtime identity | **path records keyed WITHOUT the runtime identity:** source version × source acceptance digest × source full-manifest hash × destination version × migration declaration digest | (i), (iii); not (ii), which reads no path record | a path record's output is the ACCEPTED destination manifestation, and §4d makes that one set for every build, so the record states one fact for every build. Any build's actual output is still checked after execution, before any stamp (kept below). The runtime becomes provenance |

**(v35) In the path key, the source full-manifest hash is a function of the acceptance digest, by rule** (research's stage-1 read, item 8(a)). The authority (`MigrationAuthority`) carries four of the key's five components. The source full-manifest hash is not among them, and adding it would reopen two frozen shapes: §5b's authority contract and §5e's operation-row schema. **It need not be added. The evidence validators refuse two accepted manifestations at one schema version that share an acceptance digest.** The validators are the model's `schema_evidence_problems` and production's evidence check (`specs/schema_evidence.py`, `--check`). Under that rule, (version, acceptance digest) determines the full manifestation. The one key function then derives the authority side's full-manifest hash by lookup in the accepted set, from (`from_version`, `source_digest`), so both selectors key identically.

Measured at `a187209`, with production's `_digest_of_identity` recomputing each entry's acceptance digest (`schema_versions.json` is unchanged at `58457e6`):
- `schema_versions.json` (v1–v16) holds 58 accepted manifestations, with 58 distinct (version, acceptance digest) pairs, and no acceptance digest has two full manifestations.
- Every entry's objects include a rebuildable key of its version. The two digests could therefore diverge, so the uniqueness is not vacuous.
- The model's own artifact holds one entry each at v1 and v2.

**When the rule would bite:** a later legacy base, accepted as a separate source manifestation, that differs from an existing one only in a rebuildable object. The evidence commit then fails loudly, and the authority-shape question comes back with a concrete case. That is fail-closed. A16 is the rule's cell.

**Kept unchanged, in carriers (i) and (iii):**
- the sixteen probes and their definitions; denial means `SQLITE_AUTH` (M19); every probe's setup is a valid
  statement sequence; the permissive-authorizer falsifier;
- the authorizer is restored in `finally`, on a Veracium-owned connection only; TEMP is empty after every step;
- the declaration digest and exact-one selection: an altered migration matches nothing and refuses
  `migration-evidence-missing`, with data and stamp untouched (M14);
- the record-level consistency rules;
- the post-execution repair, recompute and compare of the complete output, by manifestation, acceptance digest AND
  full-manifest hash, before any stamp;
- one byte snapshot per operation; monotone revision writes under the writer lock; exact scalar typing;
- **a malformed current-algorithm record poisons its artifact class, and only an explicitly superseded algorithm is
  ignored** (M18);
- ordinary opening runs no confinement probe, because it executes no confined statement.

In carrier (ii), what is kept is the per-step postconditions and `_validated_current`, as in the carrier table.

**Cardinality stays exact and artifact-wide; one factor leaves it.** The expected key set is every declared step ×
every accepted source manifestation; "× every active build identity" is removed. Current-record keys must equal the
expected set exactly. Missing, extra, duplicate, stale-algorithm and contradictory records each still fail closed.
"Foreign identity" is no longer a class: an extra record is an extra KEY, and cardinality refuses it, which is what
0013's round 4 required.

**Provenance: where path evidence comes from.** Each path record carries `generated_on`: the full attestation key
(§4d) of the build that generated it. It must resolve, by KEY, to exactly one current attestation record; a path
record whose `generated_on` does not resolve is malformed and poisons the path class. This keeps 0013 round 4's "no
unattested prospective record" safeguard, at generation time.
- **Generation:** path records do not depend on the build, so they are generated ONCE per declared step. Each is
  generated on a build whose attestation record is already committed at the commit that adds the path records, never
  on one the same CI run is about to emit. A new build's first run therefore produces no path evidence.
- **Re-derivation:** `--check-evidence` runs in every CI matrix job (§4d) on any build that verifies. It must
  re-derive every path record byte-equal except `generated_on`. A build that re-derives differently is a failed
  attestation job, named, never a record. On a user's machine the post-execution compare would refuse it anyway.
- **Withdrawing the generating record:** because resolution is by key, regenerating the named record at a later
  commit keeps it resolving. A commit that removes the attestation record some `generated_on` names fails the
  commit-time gate, unless the same change regenerates those path records on another attested build. Retiring a
  runner image never silently poisons migration.

**Retired, explicitly:**
- the single-active-runtime policy in `migration_runtime_artifact_problems` (S66's withdrawal, §4f, applied to 0013);
- the requirement that the running build have a migration-runtime record;
- the requirement that a path record's runtime resolve to a schema-runtime record and a migration-runtime record. It
  is replaced by `generated_on` resolving to an attestation record.

The migration-runtime record class is withdrawn. Its probe results are carried, as provenance, on the attestation
record (§4d), where the attestation suite measured them; an attestation record with any probe result other than True
is malformed. **Deferred, unchanged:** M11 and M12's production artifact lands with 0008. This amendment changes the
key that artifact will use, not when it lands.

**What changes in 0013's invariants** (these are also §4f's "withdrawn from 0013" entries):
- **M11** "every migration path is keyed individually": kept. The key loses its runtime-identity component.
  `test_the_committed_evidence_artifact_is_valid_and_reproduces` re-derives on ANY build that is not `refused`, not
  only "on the recording runtime".
- **M12** "runtime evidence covers every declared path": kept. The expected set loses "× every active build identity".
  Its three tests (absent, duplicate, stale-algorithm) keep their meaning over the new key.
- **M15** "migration confinement is runtime-qualified, independently of 0007's gate": kept, as **live**
  qualification.
  - `test_the_migration_runtime_gate_is_independent_of_0007s` is kept; A3 is its new shape.
  - `test_the_authorizer_probes_all_hold_on_this_runner` is kept.
  - `test_recorded_confinement_behaviours_must_reproduce_live` is **retired** with the record class, replaced by A1
    and A12.
- **M18** "malformed current-algorithm records poison their artifact class; foreign records fail cardinality":
  - the poisoning rule is kept, with `test_a_missing_algorithm_field_is_malformed_not_superseded`;
  - `test_a_malformed_current_migration_runtime_record_poisons` is **retired** with the class, replaced by A12;
  - `test_a_foreign_identity_path_record_fails_the_artifact` is **replaced** by A15 and A10.

**The finite acceptance matrix.** A1–A15 are carrier (i) rows: model tests at the model's next revision, and carrier
(iii) tests when 0008's artifact lands. P1–P3 are carrier (ii) rows: product tests when this amendment is implemented. **(v35)** A16 is a row for carriers (i) and (ii) both: the model's validator and production's evidence check.
Each row is demonstrated red against the named mutant.

| # | case | expected | mutant that must fail |
|---|---|---|---|
| A1 | an unrecorded build that reproduces the accepted evidence (`verified`), all 16 probes True live, path record present | migrates; the audit event's `runtime.status` is `verified` | require a migration-runtime record for this identity (the model at `58dd7f6`) |
| A2 | the attested build, same store | migrates; `attested` | — (control) |
| A3 | `verified`, with a permissive authorizer installed | ordinary open proceeds (`verified`); `migrate_store` refuses `unsupported-sqlite`, naming the first false probe; store bytes unchanged | gate migration on `runtime_status()` alone |
| A4 | `verified`, with an authorizer allowing only TEMP triggers (0013 round 8's), and one allowing only TEMP virtual tables (round 9's) | migrate refuses, naming `denies_temp_trigger` / `denies_temp_virtual_table` | collapse the per-class TEMP probes |
| A5 | `refused` (a near-miss not told apart, or `preserves_ddl_body` False) | open and migrate both refuse `unsupported-sqlite`; store unchanged | run confinement first and migrate when it passes |
| A6 | no path record for this source × declaration | `migration-evidence-missing`; data and stamp untouched | re-derive the record from live code (0013 round 3's hole) |
| A7 | two identical current path records for one key | artifact-wide refusal (duplicate) | deduplicate silently |
| A8 | two current path records for one key with different output hashes | artifact-wide refusal (contradictory) | take the first |
| A9 | a malformed current-algorithm path record beside a valid one | the path class is poisoned; migration refuses | filter the malformed record and select the valid one (0013 round 4's hole) |
| A10 | a path record whose `generated_on` resolves to no attestation record | the path class is poisoned | ignore `generated_on` |
| A11 | two or more attested keys (for example 3.45.1 x86_64 and 3.53.1 aarch64) | valid; each attested build migrates as `attested`, an unmatched verifying build as `verified` | keep the single-active-runtime count |
| A12 | an attestation record carrying a probe result False | the attestation artifact is malformed (§4d); verification still runs; migration still runs the probes live | treat the recorded False as authority (refuse without running) or as a pass |
| A13 | a stale-algorithm path record | superseded, not consumed; cardinality counts current records only | consume it |
| A14 | an altered declaration that produces the identical schema (M14) | `migration-evidence-missing`; data and stamp untouched | drop the declaration digest from the key |
| A15 | an extra current path record for a key outside the expected set | cardinality refusal | count only expected keys |
| A16 | **(v35)** an evidence file holding two accepted manifestations at one version that share an acceptance digest and differ in a rebuildable object | refused by the evidence validator, in the model and in production | admit it (the authority's lookup then has two answers, and the two selectors can key differently) |
| P1 | production: a `verified` build migrates a base store | `migrated`, through the same `_apply_forward` and `_validated_current(require_stamp=True)` as the attested build; the `attempted` event's `runtime.status` is `verified` (INV-SA11) | keep `runtime_supported()` as the gate; skip `_validated_current` on a `verified` build |
| P2 | production: a `refused` build | `migrate_store` and `run_release_migration` both refuse `unsupported-sqlite` before touching the store | gate only `open_versioned` (the release preflight, L1005, still reads the old predicate) |
| P3 | production, on a `verified` build: the stamp written as HEAD − 1 (research's v0.8 stamp mutant) | refused by `_validated_current(require_stamp=True)` (M117); the transaction rolls back; the same on the attested build | commit before `_validated_current` on a `verified` build; pass `require_stamp=False` on one |

### 5f.4 Invariants (the amendment's §6: INV-SA10 and INV-SA11)

| | invariant | mutant that must fail |
|---|---|---|
| **INV-SA11** | **(v0.2)** a migration's `attempted` audit event carries the migrating build's `sqlite_version`, `source_id` and `runtime_status()`; **(v35)** in §5e's durable model the key sits on the operation row, and the events table's attempted row stays payload-free | omit the key; record `attested` on a `verified` build; record the build that created the store |
| **INV-SA10** | **(v0.11; a COMMIT-TIME product test, replacing v0.2's runtime refusal, §4c)** over every campaign path, every write the migration ladder issues, **(v0.12) as SQLite's authorizer classifies it, attributed per call (§4c), never by its first word,** is either DDL in class (a) (byte-equal to a frozen `ALTERS_*` member, checked at its step) or in class (b) (§4c's closed list, decided per statement by its text, never by its site; every head table constructor plain and without `IF NOT EXISTS`), or maps to EXACTLY ONE named step whose postcondition is checked at the step inside the migration's transaction and whose campaign cells are each killed at that step; **(v0.11.1)** and every `execute`/`executemany`/`executescript` call site in every function the ladder's connection is used from (reads included; `open_versioned` excluded, §4c) is observed on at least one campaign path; `attested` and `verified` builds take the same ladder with the same checks, and a mismatch leaves the store unchanged; **(v35)** and no store content changes during a census path except by a recorded call, against any code that does not write to the instrument's own objects (§5f.1 rule 5, replay equivalence, with its two stated limits); **(v38)** and nothing reaches the real `sqlite3` from a seamed module except through the census: `connect`'s arguments, the module seam's attributes and a set's values are closed sets, refused and recorded outside them, and replay runs no recorded caller behaviour (§5f.1 rule 6) | add a ladder write that maps to no step (**measured: today's campaign passes it**, §4c); **(v0.11.1)** the same write behind a condition no fixture satisfies (dev's `mutant2-conditional`; the complement passes it, the site check refuses it); narrow the site scope to one module (it then refuses a correct tree: `unattested_marker_report`); a write that two steps' matchers both claim; delete one `_refuse_unless`; make one postcondition vacuous (its problems always empty); add a `STEP_*` name with no matcher; issue DDL from an undeclared site; skip the byte-match on an unattested build; commit before revalidating; let a `verified` build migrate along a different path or with fewer checks than an `attested` one; **(v35)** the mutants of §5f.1 rules 5 and 6 and of the N13–N15 and W1–W3 rows; **(v37)** attribute the `declare_vtab` sequence as bookkeeping on a build whose own probe does not reproduce it; accept it with a sixth column, another table, another database or a trigger argument; accept it on a second use on one connection; accept it outside a prepare; drop the probe's no-change check; **(v38)** forward the caller's `connect` arguments (a connection factory writes before the callbacks are installed, and replay repeats it); forward the module (`sqlite3.Connection(path)` writes with no census); accept any set value (a function as `row_factory` or `text_factory`); let replay run what it recorded. Demonstrated in INV-SA10's mutation table, `specs/evidence/0013/sa10/mutation-table.json` (§5f.1). Of this row's earlier mutants, the table carries: a ladder write that maps to no step (`tree-unmapped-write`); the same write behind a condition no fixture satisfies (`tree-unreached-write`); DDL from an undeclared site (`tree-undeclared-ddl`, `ddl-site-ignored`); and a write that two steps' matchers both claim (`exact-one-relaxed`; cell `tests/test_0013_sa10_gate.py::test_a_row_write_two_steps_both_claim_is_refused`). It also carries a write added to a `release_migration` function (`tree-release-migration-write`). The other mutants named here are not rows of that table. **(v38)** v38's are: the product mutations `tree-connect-factory-keyword`, `tree-connect-factory-positional`, `tree-direct-connection`, `tree-row-factory-function` and `tree-text-factory-function`, and the gate mutants `sa-r3-01-connect-forwards-the-callers-arguments`, `sa-r3-01-the-seam-forwards-the-module`, `sa-r3-01-set-values-unchecked` and `sa-r3-01-replay-runs-recorded-behaviour` |

The amendment's **Gate** (0007 §4g.8) applies to both: each is a PRODUCT test at implementation, demonstrated red against its mutant.

## 6. Invariants and executable checks — REQUIRED, blocking

**The store contains no migration code — `0013` authorises nothing.** The
rows below marked with test names now run against the **draft instrument**
(`specs/migrations_0013.py`) and the concrete migration; they become store
tests at implementation.

| invariant | executable check |
|---|---|
| **M1** a declared step runs inside the caller's transaction | `test_the_executor_requires_an_existing_transaction` — **measured today**; and exercised by every instrument test via the shared `0007` planner |
| **M2** transaction control in a declared statement is denied | `test_transaction_control_and_pragmas_are_denied` — **measured today**, six forms |
| **M3** temp objects are refused | `test_a_temp_object_is_refused` — **measured today** |
| **M4** pragmas are refused | `test_transaction_control_and_pragmas_are_denied` — **measured today** |
| **M5** the authorizer is restored after failure | `test_the_authorizer_is_restored_after_failure` — **measured today** |
| **M6** an empty migration cannot authorise its output | `test_an_empty_migration_cannot_authorize_its_output` — **measured today**, against the real `confirmations` requirement |
| **M7** a correct migration reaches its declared destination | `test_the_concrete_migration_reaches_the_v2_constructor_output` — **measured today**; output byte-identical to the constructor |
| **M8** a partial or wrong-shape result is rejected | `test_a_partial_migration_is_rejected` — **measured today** |
| **M9** the registry is well-formed | `test_m9_the_draft_registry_is_well_formed` · `test_a_gap_refuses` — **measured today** |
| **M10** a skipped release still upgrades | **NOT demonstrated, and not claimed** (round 2, finding 7). `0013` today authorises the concrete adjacent v1→v2 only; the multi-step planner is reviewed at the first spec needing two real steps |
| **M11** every migration path is keyed individually | **draft form measured today**: the committed artifact keys records by runtime × source digest+hash × destination × declaration digest — `test_the_committed_evidence_artifact_is_valid_and_reproduces`. Production artifact lands with `0008` · **v34:** kept; the key loses its runtime-identity component, and the reproduction re-derives on ANY build that is not `refused` (§5f.3) |
| **M12** runtime evidence covers every declared path | **draft form measured today**: exact cardinality against the live registry — `test_an_absent_path_record_refuses` · `test_a_duplicate_path_record_refuses` · `test_a_stale_algorithm_record_is_superseded_not_consumed`. Production with `0008` · **v34:** kept; the expected set loses “× every active build identity”, and its three tests keep their meaning over the new key (§5f.3) |
| **M13** migration runs exactly once among cooperating openers | `test_mq2_concurrent_migration_runs_exactly_once`, and the reviewer's independent five-**process** run. **The stale-opener hazard is measured, not solved** — §5b's quiescence contract. |
| **M14** an altered migration cannot authorise itself | `test_a_data_destructive_alteration_cannot_authorize_itself` · `test_a_side_effect_free_alteration_is_still_not_evidenced` — **measured today**: refusal before execution, data and stamp untouched |
| **M15** migration confinement is runtime-qualified, independently of `0007`'s gate | `test_the_migration_runtime_gate_is_independent_of_0007s` · `test_the_authorizer_probes_all_hold_on_this_runner` · `test_a1_a_verified_build_migrates_and_its_row_says_verified` · `test_a12_an_attestation_record_with_a_false_probe_is_malformed_and_the_probes_still_run_live` — **measured today** · **v34:** kept, as LIVE qualification; the recorded-confinement test is retired with the record class, replaced by A1 and A12 (§5f.3) · **(v36):** the retired test is named in §5f.3's list only |
| **M16** every outcome is a member of the closed vocabulary | `test_invalid_sql_returns_migration_failed_not_an_exception` · `test_a_wrong_unique_constraint_is_a_result_mismatch` · `test_the_outcome_vocabulary_is_closed` — **measured today** |
| **M17** the failure boundary covers evidence loading, context entry and the connection | `test_a_malformed_accepted_manifestation_fails_closed` · `test_a_malformed_path_field_fails_closed` · `test_a_non_database_file_is_a_closed_refusal` · `test_an_unopenable_path_is_a_closed_refusal` — **measured today** |
| **M18** malformed current-algorithm records poison their artifact class; foreign records fail cardinality | `test_a_missing_algorithm_field_is_malformed_not_superseded` · `test_a12_an_attestation_record_with_a_false_probe_is_malformed_and_the_probes_still_run_live` · `test_a15_an_extra_current_path_record_outside_the_expected_set_is_a_cardinality_refusal` · `test_a10_a_generated_on_that_resolves_to_no_attested_record_poisons_the_paths` — **measured today** · **v34:** the poisoning rule is kept; the malformed migration-runtime-record test is retired (replaced by A12), and the foreign-identity path-record test is replaced by A15 and A10 (§5f.3) · **(v36):** the retired tests are named in §5f.3's list only |
| **M19** confinement denial means `SQLITE_AUTH`, nothing else | `test_a_permissive_authorizer_fails_every_denial_probe` · `test_the_release_probe_holds_a_real_savepoint` — **measured today** |
| **M20** an authority authorises exactly one operation, inside its window, on its canonical store | `test_an_authority_is_single_use_and_cannot_migrate_a_replacement` · `test_a_retargeted_symlink_unbinds_the_authority` · `test_an_unparseable_or_expired_authority_is_refused` — **measured today** |
| **M21** evidence writes are monotone over the `MigrationEvidenceRevision` | `test_a_future_evidence_revision_is_never_overwritten` (three components, byte-unchanged) · `test_an_unreadable_existing_revision_refuses_regeneration` — **measured today** |
| **M22** consumption covers the complete operation, atomically | `test_an_authority_finding_the_store_current_is_still_consumed` · `test_authorities_losing_the_concurrent_race_are_consumed` · `test_operation_consumption_is_atomic_under_concurrency` — **measured today** |
| **M23** the validity window is real: `issued ≤ now < expires`, lifetime-capped, release-bound | `test_a_future_issued_authority_is_refused` · `test_an_authority_lifetime_above_the_frozen_maximum_refuses` · `test_an_authority_from_a_different_release_refuses` · `test_an_oversized_token_field_refuses` — **measured today** |
| **M24** scalar typing is exact and the boundary is outermost | `test_coerced_top_level_scalars_poison_the_artifact` · `test_a_coerced_path_algorithm_poisons_the_paths` · `test_an_embedded_nul_path_is_a_closed_outcome` · `test_a_mistyped_timeout_is_a_closed_outcome` · `test_a_non_pathlike_argument_is_a_closed_outcome` · `test_an_oversized_path_is_a_closed_outcome` — **measured today** |
| **M25** a migration never creates or adopts | `test_a_deleted_source_cannot_become_a_new_store` · `test_a_truncated_source_cannot_become_a_new_store` · `test_an_empty_database_replacement_cannot_be_migrated` · `test_an_unstamped_current_shape_replacement_is_refused_not_adopted` · `test_ordinary_open_still_creates` — **measured today**; every case leaves the path uncreated or byte-unchanged |
| **M26** evidence publication is serialized and monotone under concurrency | `test_a_concurrent_future_publication_is_not_downgraded` (two-process barrier) — **measured today**; the round-5 static seeds remain |
| **M27** the boundary is Unicode- and PathLike-safe | `test_a_non_utf8_bytes_path_works_end_to_end` · `test_a_pathlike_that_raises_is_a_closed_outcome` · `test_a_surrogate_token_field_is_a_closed_refusal` — **measured today** |
| **M28** the audit contract's two named escapes exist | `test_the_audit_contract_is_frozen` — **measured today**; the enforced state machine and record schema are M36/M37 and §5e (round 8: M28/M32 no longer claim the complete lifecycle is measured — schema validation, atomic activation, terminal exclusivity and the four terminal cells are the M36/M37 evidence) |
| **M29** the release identity is immutable per build and the evidence artifact is bound | `test_the_release_identity_is_content_derived` · `test_a_version_only_release_ref_is_refused` · `test_a_cross_build_authority_is_refused` · `test_an_authority_binds_the_evidence_artifact` — **measured today** |
| **M30** one evidence snapshot per operation; nested contexts agree or refuse | `test_the_operation_consumes_the_bytes_the_authority_bound` · `test_a_nested_context_never_silently_swaps_artifacts` — **measured today** |
| **M31** the release identity binds the file boundary at full digest length | `test_moving_bytes_across_the_file_boundary_changes_the_identity` — **measured today** |
| **M32** consumption is split from audit outage; both are executable | `test_audit_unavailability_consumes_nothing_and_is_retryable` · `test_a_duplicate_operation_is_consumed_not_an_audit_outage` · `test_terminal_records_are_written_for_migrated_and_noop_current` · `test_a_failed_terminal_write_raises_the_typed_error` — **measured today**. Schema/atomicity/exclusivity/terminal-cells are M36/M37 |
| **M33** source binding is static, and minting never creates | `test_an_authority_binds_the_source_manifestation` · `test_minting_never_creates_a_store` · `test_minting_refuses_a_non_accepted_source` — **measured today** |
| **M34** internal failures are `internal-error`, never store semantics | `test_an_internal_defect_is_not_a_store_outcome` · `test_check_evidence_is_total_over_non_mapping_runtime_members` — **measured today** |
| **M35** each TEMP object class is qualified independently, `SQLITE_AUTH`-specific | `test_the_temp_probes_cover_every_object_class` · `test_an_authorizer_allowing_temp_triggers_fails_qualification` — **measured today** |
| **M36** the audit store enforces schema, event enum and one-terminal-per-operation | `test_the_audit_store_rejects_two_terminal_events` · `test_the_audit_store_rejects_unknown_events_and_payloads` · `test_the_operation_row_carries_the_full_frozen_schema` — **measured today**; single-mutation atomicity is M40 |
| **M37** terminal audit facts come from the kernel, correct on every branch | `test_the_current_branch_reports_the_actual_resulting_version` · `test_the_current_with_repair_branch_reports_committed_true` · `test_the_migrated_branch_reports_committed_true` — **measured today** |
| **M38** release identity acquisition fails closed | `test_an_unreadable_covered_file_fails_closed` · `test_a_missing_version_declaration_fails_closed` · `test_no_unknown_sentinel_authority_migrates` — **measured today** |
| **M39** every persisted timestamp is canonical and length-capped, INCLUDING the evidence artifact | `test_a_hundred_kilobyte_timestamp_is_refused` · `test_a_noncanonical_but_valid_instant_is_refused` · `test_minted_timestamps_are_canonical` · `test_a_noncanonical_generated_at_poisons_the_artifact` · `test_the_committed_generated_at_is_canonical` — **measured today** |
| **M40** audit state is one immutable value published in one mutation | `test_activation_publishes_one_state_or_none` · `test_terminal_publication_publishes_one_state_or_none` — **measured today**; a failure injected on the publish leaves the previous state intact (round 10: v11's three-attribute store could half-publish) |
| **M41** the operation row carries every frozen field; terminal records are semantically consistent | `test_the_operation_row_carries_every_frozen_field` · `test_the_terminal_validator_rejects_contradictions` — **measured today** |
| **M42** a post-commit internal defect never misreports the version | `test_a_post_commit_internal_defect_never_reports_the_wrong_version` — **measured today**; the kernel builds `OpenResult` before COMMIT |
| **M43** TEMP virtual tables are qualified; the four terminal cells including rolled-back are exercised | `test_temp_virtual_tables_are_probed` · `test_an_authorizer_allowing_temp_vtables_fails_qualification` · `test_the_rolled_back_cell_reports_the_source_version` — **measured today** |
| **M44** the audit state is one immutable value; a failure on the publish leaves the previous state | `test_activation_publishes_one_state_or_none` · `test_terminal_publication_publishes_one_state_or_none` — **measured today** |
| **M45** the terminal validator freezes the exact per-cell contract, including the post-commit failure | `test_the_terminal_validator_rejects_impossible_success_records` · `test_the_terminal_validator_accepts_every_valid_success_cell` · `test_a_post_commit_failure_records_the_destination_version` · `test_the_terminal_validator_permits_a_committed_failure` — **measured today** |
| **M46** only a typed storage outage is retryable; a library defect is `internal-error` | `test_an_internal_activation_defect_is_not_a_storage_outage` · `test_a_typed_storage_outage_is_retryable` — **measured today** |
| **M47** every evidence validator and `--check-evidence` is total over malformed JSON containers | `test_check_evidence_is_total_over_malformed_list_fields` (15 combinations) · `test_the_artifact_validators_are_total_over_non_lists` — **measured today** |
| **M48** the terminal record carries `resulting_state`, and missing/unaccepted/unknown stores are recorded without a fabricated version | `test_terminal_facts_never_fabricate_a_version_for_missing_or_unknown` · `test_a_missing_and_an_unknown_failure_cell_are_legal_terminal_records` · `test_a_missing_or_unknown_state_rejects_a_non_null_version` — **measured today**; `resulting_state` ∈ {destination, source, missing, unaccepted, unknown} fixes the version, and v12's `from_version` fabrication is refused |
| **M49** every committing branch delivers its `OpenResult` to `on_committed` BEFORE the post-commit cleanup | `test_on_committed_delivers_the_committed_result_before_cleanup` (kernel) — **measured today**; a forced `isolation_level`-restore failure cannot erase a proven commit, closing v12's discard-on-cleanup path |
| **M50** a named escape after consumption is terminalized and re-raised | `test_a_package_consistency_error_is_terminalized_and_reraised` — **measured today**; a `PackageConsistencyError` records `package-inconsistent` and re-raises, so no consumed operation lacks a terminal event |
| **M51** the published audit state is deeply read-only and `event_id` is unique | `test_the_published_audit_state_is_deeply_read_only` · `test_a_repeated_event_id_is_rejected` — **measured today**; containers and rows are read-only proxies and a repeated `event_id` is refused as the PK it stands in for |
| **M52** a lost activation response is mapped by its `committed` flag, and every validator is total over NESTED malformed JSON | `test_a_lost_activation_response_is_mapped_by_its_commit_flag` (True/False/None) · `test_every_validator_is_total_over_nested_malformed_json` · `test_check_evidence_is_total_over_nested_malformed_json` (7 nested mutations each) · `test_artifact_problems_is_total_over_an_unhashable_identity_field` (kernel) — **measured today** |
| **M53** the kernel publishes the rollback outcome, and `source` requires a CONFIRMED rollback | `test_on_rolled_back_reports_the_rollback_outcome` (kernel: rolled-back / rollback-failed) · `test_terminal_facts_never_fabricate_a_version_for_missing_or_unknown` — **measured today**; a rollback that itself fails is `unknown`, never `source` (round 12, finding 1) |
| **M54** absent, unaccepted, and unobserved stores get distinct truthful classifications | `test_an_existing_empty_store_is_unaccepted_not_missing` · `test_a_proven_absent_path_is_missing` · `test_terminal_facts_never_fabricate_a_version_for_missing_or_unknown` — **measured today**; `missing` is a path proven absent, `unaccepted` an existing non-source store (round 12, finding 2) |
| **M55** the unknown activation state is structurally distinct and `committed` defaults to unknown | `test_a_lost_activation_response_is_mapped_by_its_commit_flag` (None → `migration-audit-state-unknown`) · `test_the_committed_flag_defaults_to_unknown_and_is_typed` — **measured today** (round 12, finding 3) |
| **M56** `MigrationAuditWriteError` preserves `resulting_state`/`resulting_version` | `test_the_audit_write_error_carries_and_distinguishes_the_state` · `test_a_forced_terminal_write_failure_preserves_the_state` — **measured today**; a missing and an unknown ending are distinguishable, message names the state (round 12, finding 4) |
| **M57** every validator is total under RECURSIVE nested mutation; the operation row validates types and freezes deeply; the `event_id` grammar is enforced | `test_every_validator_is_total_under_recursive_nested_mutation` (>5000 combinations) · `test_the_specific_nested_key_escapes_are_closed` · `test_the_operation_row_validates_field_types` · `test_a_published_row_does_not_alias_caller_mutable_state` · `test_a_malformed_event_id_grammar_is_rejected` — **measured today** (round 12, finding 5 + corrections A, B) |
| **M58** an unconfirmed rollback never fabricates Boolean change/commit facts | `test_an_unconfirmed_rollback_never_fabricates_boolean_facts` · `test_a_tri_state_unknown_terminal_record_is_accepted` — **measured today**; the unknown cell's `store_changed`/`transaction_committed` are `None`, not a fabricated `False` (round 13, finding 1) |
| **M59** a post-commit SQLite cleanup failure is `internal-error`, not `invalid-store`, and keeps the committed facts | `test_a_post_commit_cleanup_failure_is_internal_error_not_invalid_store` — **measured today**; SQLite errors are classified by PHASE, not exception superclass (round 13, finding 2) |
| **M60** only a proven absence (`lstat` ENOENT) is `missing`; an unsearchable path is `store-unopenable` | `test_an_unsearchable_existing_store_is_not_proven_missing` — **measured today**; `os.path.lexists` is not proof of absence (round 13, finding 3) |
| **M61** each terminal outcome permits only the resulting_states it can physically reach | `test_each_outcome_permits_only_its_physical_states` (10 combinations) — **measured today**; `locked`+source, `invalid-store`+missing and the like reject (round 13, finding 4) |
| **M62** the terminal record and `MigrationAuditWriteError` share ONE validated `TerminalFacts`; operation-row paths reject embedded NULs | `test_the_write_error_enforces_the_full_terminal_relationship` · `test_the_record_and_the_exception_share_one_validator` · `test_the_operation_row_rejects_embedded_nul_paths` — **measured today** (round 13, finding 5 + correction A) |
| **M63** `TerminalFacts.problems()` encodes the COMPLETE permitted tuple (both carriers) and is total | `test_terminal_facts_encodes_the_complete_tuple` (13 cells) · `test_the_migrated_rule_lives_inside_terminal_facts` · `test_terminal_facts_problems_is_total` — **measured today**; a partial `None` pair, an `(None,None)` non-unknown cell and a no-change `migrated` all reject, and `outcome=[]`/`state={}` report rather than raise (round 14, finding 1 + correction A) |
| **M64** a committed activation-response loss still writes a terminal event | `test_a_committed_activation_loss_still_writes_a_terminal` — **measured today**; a durably-consumed authority is never left with only an attempted record (round 14, finding 2) |
| **M65** a terminal write's own commit status is representable | `test_a_lost_terminal_response_reports_audit_committed` — **measured today**; `MigrationAuditWriteError.audit_committed` distinguishes durable-but-response-lost from never-written (round 14, finding 3) |
| **M66** SQLite errors are classified by READ SITE, not commit-fact existence | `test_a_runtime_probe_defect_is_internal_error_not_invalid_store` · `test_invalid_store_is_only_the_planner_reading_bad_bytes` — **measured today**; a runtime-gate defect is `internal-error`, only the planner's read is `invalid-store` (round 14, finding 4) |
| **M67** a package-inconsistency terminalizes at every phase and re-raises; the write error validates its context | `test_a_package_inconsistency_terminalizes_at_every_phase` (before/after-rollback/after-commit — the after-rollback case genuinely rolls back) · `test_the_write_error_validates_its_context` — **measured today** (round 14, finding 5 + correction B; round 15, correction D) |
| **M68** only a closed activation-result member proceeds; a malformed result never touches the store | `test_a_malformed_activation_result_never_touches_the_store` (None/string/bool/object) — **measured today** (round 15, finding 1) |
| **M69** a malformed kernel result terminalizes as `internal-error`, never escapes as `AttributeError`; the connection's cleanup begins the instant it opens | `test_a_malformed_kernel_result_is_internal_error_not_attribute_error` · `test_an_isolation_level_setup_failure_closes_the_connection` — **measured today** (round 15, findings 2 & 5) |
| **M70** a migration-hook SQLite error is `migration-failed`, not `invalid-store`; a read-rejected store is `unaccepted`, not `unknown` | `test_a_migration_hook_database_error_is_migration_failed` · `test_a_readable_rejected_store_is_unaccepted_not_unknown` — **measured today** (round 15, findings 3 & 4) |
| **M71** the write error preserves a supplied commit status; endpoints are adjacent and `audit_committed` is exact-bool; a non-mapping payload is controlled | `test_the_write_error_preserves_a_supplied_commit_status` · `test_non_adjacent_endpoints_and_integer_commit_flags_reject` · `test_a_non_mapping_terminal_payload_is_a_controlled_error` — **measured today** (round 15, corrections A, B, C) |
| **M72** MECHANICAL pre-send gates: the whole `TerminalFacts` truth table vs a GENUINELY independent (hand-written, not implementation-read) oracle, and a fault at every audit/planner seam asserting universal invariants INCLUDING record completeness | `tests/test_0013_presend_gates.py` — **measured today**; proven to catch round-14 f1/f4, round-15 f1, and round-16 f1/f2 (round 16, correction B: the oracle no longer shares the implementation map, and the sweep asserts a success outcome leaves a row and exactly one terminal event) |
| **M73** activation returns a typed `ActivationReceipt` verified against the durable row; a lying or spoofing result never touches the store | `test_an_activation_receipt_without_a_published_row_is_rejected` · `test_an_equality_spoofing_activation_result_is_rejected` — **measured today** (round 16, finding 1) |
| **M74** terminal publication returns a verified `TerminalReceipt`; a silent no-op raises, never reports success | `test_a_silent_terminal_noop_raises_never_reports_success` — **measured today** (round 16, finding 2) |
| **M75** the kernel result is validated COMPLETELY and mode-aware | `test_a_semantically_contradictory_kernel_result_is_internal_error` (5 cells) — **measured today**; `migrated`/¬changed, `created`/`adopted` in migrate mode, `migrated`/wrong-version reject (round 16, finding 3) |
| **M76** hostile terminal-sink metadata never leaks a third exception; a check-to-open race is a vanished source | `test_a_hostile_committed_accessor_never_escapes` · `test_a_source_deleted_between_check_and_open_is_missing` — **measured today** (round 16, findings 4 & 5) |
| **M77** the `event_id`/`operation_id` grammar enforces UUID-4 bits; `MigrationRefused` raises under `python -O` | `test_the_event_id_grammar_enforces_uuid4_bits` · `test_migration_refused_raises_under_dash_o` — **measured today** (round 16, corrections C & D) |
| **M78** the activation receipt is BOUND to the exact authority row; a false duplicate leaves the authority usable | `test_activation_binds_the_exact_authority_row` · `test_a_false_duplicate_receipt_leaves_the_authority_usable` — **measured today** (round 17, finding 1 + correction A) |
| **M79** the terminal receipt is BOUND to the requested payload; the returned branch must equal the committed branch | `test_the_terminal_receipt_binds_the_requested_payload` · `test_the_returned_branch_must_equal_the_committed_branch` — **measured today** (round 17, findings 2 & 3) |
| **M80** a malformed `on_committed` never asserts no-change and never erases a proven commit; a terminal-derivation defect never escapes raw | `test_a_malformed_on_committed_publication_never_asserts_no_change` · `test_a_terminal_derivation_defect_never_escapes_raw` — **measured today** (round 17, findings 4 & 5) |
| **M81** both receipts have TOTAL scalar `problems()` validators; the pre-send gates assert request-to-record CONTENT binding | `test_receipt_problems_validate_every_scalar` · `tests/test_0013_presend_gates.py` (the oracle is hand-written; the sweep asserts the row binds the authority store and the terminal event carries the requested outcome) — **measured today** (round 17, corrections B & C) |
| **M82** activation binds the COMPLETE attempted event, not just the row; a duplicate binds the authority and its `terminal_present` agrees with durable state | `test_activation_binds_the_complete_attempted_event` · `test_a_duplicate_row_must_bind_the_authority` — **measured today** (round 18, finding 1 + correction B) |
| **M83** the terminal write verifies the full `attempted → terminal` transition — operation `terminal`, one terminal event, a unique non-reused `event_id` — not only the payload | `test_terminal_write_requires_the_state_transition` · `test_terminal_write_rejects_a_reused_event_id` — **measured today** (round 18, finding 2) |
| **M84** a false `current`/(F,F) never suppresses a real `migrated`/(T,T); the durable record retains the strongest proven state | `test_a_false_uncommitted_publication_never_suppresses_a_real_commit` — **measured today** (round 18, finding 3) |
| **M85** the whole post-consumption sequence is total (hostile receipt equality, a non-bool audit flag) and a derivation fallback changes the PUBLIC outcome; a `recorded` receipt must be `audit_committed=True` | `test_a_hostile_receipt_equality_never_escapes` · `test_an_uncommittable_audit_flag_never_leaks_a_type_error` · `test_a_derivation_fallback_agrees_public_and_durable_outcome` · `test_a_recorded_receipt_must_be_audit_committed` — **measured today** (round 18, findings 4 & 5 + correction A) |
| **M86** `MigrationAuditWriteError.audit_committed` follows the STRONGEST durable evidence — an observed complete transition proves `True`, never a contradictory `False` receipt; a validated no-op-`current` destination position survives a later internal defect | `test_the_write_error_audit_committed_follows_durable_proof` · `test_a_noop_current_position_survives_a_post_callback_defect` — **measured today** (round 19, findings 1 & 2) |
| **M87** terminalisation verifies the operation row and attempted event were PRESERVED (only the state changed `attempted → terminal`), not just the terminal delta | `test_terminalization_requires_the_prior_records_preserved` (delete-attempted, mutate-row) — **measured today** (round 19, correction A) |
| **M88** a malformed duplicate lifecycle is audit-integrity `internal-error`, not a replay; activation readback checks the reference `event_ids` index and exact row field set | `test_a_malformed_duplicate_lifecycle_is_audit_integrity` · `test_activation_readback_requires_the_event_id_in_the_index` — **measured today** (round 19, corrections B & C) |
| **M89** receipt validators are TOTAL over hostile `str` subclasses (`type(x) is str` before comparison) | `test_receipt_validators_are_total_over_str_subclasses` — **measured today** (round 19, correction D) |
| **M90** strongest-durable-evidence governs CONSUMPTION: a complete durable activation is consumed despite a lying carrier — an invalid `activated` receipt or a contradictory `committed=False` exception is `internal-error` WITH a terminal event, never left attempted-only, never advertised as a safe retry | `test_a_durable_activation_is_consumed_despite_a_lying_carrier` (invalid-receipt, committed-false) — **measured today** (round 20, finding 1) |
| **M91** a terminal-sink EXCEPTION cannot override a durably-observed commit — `MigrationAuditWriteError.audit_committed` follows the transition on the raise path too | `test_a_terminal_sink_exception_cannot_override_durable_commit` — **measured today** (round 20, finding 2) |
| **M92** the terminal-derivation fallback preserves EVERY established physical state (proven no-op destination, proven-missing source), not only a committed destination | `test_terminal_fallback_preserves_every_established_state` (noop-destination, missing-source) — **measured today** (round 20, finding 3) |
| **M93** the shared `TerminalFacts.problems()` is TOTAL over hostile `str` subclasses (`type(x) is str` before hashing) | `test_terminal_facts_problems_total_over_hostile_str_subclass` — **measured today** (round 20, correction A) |
| **M94** a `duplicate` activation receipt must be `audit_committed=True` (the row exists durably) | `test_a_duplicate_receipt_must_be_audit_committed` — **measured today** (round 20, correction B) |
| **M95** durable readback precedes classifying EVERY activation carrier — a wrong-type return or an unrecognized post-publication exception after a durable activation is `internal-error` WITH a terminal event, never left attempted-only | `test_durable_activation_consumed_for_every_carrier_class` (wrong-type-return, unrecognized-exception) — **measured today** (round 21, finding 1) |
| **M96** an adapter-supplied `MigrationAuditWriteError` is an UNTRUSTED carrier — the wrapper re-derives `audit_committed` and owns the identity (operation id, store path), keeping the adapter's exception only as the cause | `test_a_sink_supplied_write_error_is_an_untrusted_carrier` — **measured today** (round 21, finding 2) |
| **M97** a typed `committed=True` with no observable terminal transition is contradictory — `audit_committed` degrades to `None`, never proven `True` | `test_committed_true_without_a_transition_is_not_proven_durable` — **measured today** (round 21, finding 3) |
| **M98** timestamp/token/digest/path validators are TOTAL over hostile `str` subclasses (`type(x) is str` before length/regex/parse) — an invalid authority stays a closed refusal, never a library defect | `test_timestamp_validation_is_total_over_hostile_str_subclasses` — **measured today** (round 21, correction A) |
| **M99** the COMPLETE durable lifecycle is classified before every activation carrier — an already-`terminal` operation + `committed=False` is a consumed replay (`migration-quiescence-required`), never a false `migration-audit-unavailable` | `test_a_completed_lifecycle_is_quiescence_not_retryable` · gate `test_gate_completed_lifecycle_committed_false_is_quiescence` — **measured today** (round 22, finding 1) |
| **M100** `on_committed` FREEZES a wrapper-owned immutable copy and reads the branch from the exact underlying value — a live mutation after publication cannot change the facts, and an `OpenResult` subclass cannot spoof its branch | `test_on_committed_facts_are_frozen_against_mutation` · `test_an_open_result_subclass_cannot_spoof_the_branch` · gate `open_versioned-subclass-spoofs-branch` — **measured today** (round 22, finding 2) |
| **M101** `MigrationAuditWriteError` requires `type(facts) is TerminalFacts` and calls the BASE validator, and `type(operation_id) is str` — a subclass cannot replace the shared truth-table validator | `test_the_write_error_requires_exact_carrier_types` (facts-subclass, operation-id-subclass) — **measured today** (round 22, finding 3) |
| **M102** the TOP-LEVEL authority validator exact-types every token/digest/path/timestamp field before `.strip()`/regex — a hostile `str` subclass stays a closed refusal | `test_authority_validation_is_total_over_hostile_str_subclasses` · gate `test_gate_authority_str_subclass_is_a_closed_refusal` — **measured today** (round 22, correction A) |
| **M103** a successful migrate result REQUIRES its mandatory `on_committed` publication (equal field-for-field) — a kernel returning `migrated` without the callback is `internal-error`, store untouched, never retroactively establishing commit/position | `test_a_success_requires_an_on_committed_publication` · gate `open_versioned-success-without-callback` — **measured today** (round 23, finding 1) |
| **M104** `on_committed` validates the mode-aware SEMANTIC cell (one shared `_cell_problems`, used by the callback and the returned-result check) BEFORE freezing — a `migrated`/(F,F) publication is a defect, not a destination position | `test_on_committed_validates_the_semantic_cell_before_freezing` · gate `open_versioned-impossible-callback-cell` — **measured today** (round 23, finding 2) |
| **M105** the authority carrier must be the EXACT `MigrationAuthority` type before any field access (a subclass can intercept it) — a subclass is a closed refusal, never `internal-error` or a raw escape after commit; the initial terminal fallback is inside the total boundary | `test_a_migration_authority_subclass_is_a_closed_refusal` · `test_a_late_authority_getter_never_strands_a_committed_operation` · gates — **measured today** (round 23, finding 3 + correction A) |
| **M106** `on_committed` fires EXACTLY ONCE — ANY second publication, even value-identical, is a defect (`internal-error`), not an idempotent repeat; and the returned result is frozen EXACTLY ONCE (no re-read of the live label after validation) | `test_a_second_identical_on_committed_publication_is_a_defect` · `test_the_returned_result_is_frozen_once_no_reread` · gates `open_versioned-double-identical-callback` · `open_versioned-mutate-returned-after-callback` — **measured today** (round 24, findings 1 & 2) |
| **M107** the terminal rescue NEVER re-runs a helper that has already failed — `_safe_fallback_facts` degrades a fallback defect to a minimal valid value, so a fallback-helper defect after commit is a wrapper-owned write error, never a raw escape; `_static_resolution_problems` exact-types its carrier | `test_a_fallback_helper_defect_never_escapes_after_commit` · `test_static_resolution_problems_is_total_over_an_authority_subclass` · gate `store-fact-derivation-defect` — **measured today** (round 24, finding 3 + correction A) |
| **M108** a defect in the wrapper's OWN post-publication verification preserves the exact requested/durable terminal facts and `audit_committed=True` (a proven commit survives a wrapper-verifier defect; M-Q4 permits trusting a valid success receipt); the safe fallback reconstructs the strongest proven store state INDEPENDENTLY of the derivation-helper family, never erasing a proven commit | `test_a_verifier_defect_preserves_the_durable_terminal_result` · `test_the_safe_fallback_never_erases_a_proven_commit` · gates `terminal-transition-verifier-defect` · `store-fact-derivation-defect` — **measured today** (round 25, findings 1 & 2) |
| **M109** a valid `activated` receipt establishes PROVISIONAL consumption, so a defect in the activation binding VERIFIER still terminalizes the durably-consumed operation (never attempted-only); a clean readback rejection (a receipt lie, no durable row) stays not-consumed; `_static_resolution_problems` exact-types its digest fields | `test_an_activation_readback_defect_still_terminalizes` · `test_an_activated_receipt_lie_without_a_row_stays_not_consumed` · `test_static_resolution_exact_types_its_fields` · gate `activation-readback-verifier-defect` — **measured today** (round 25, finding 3 + correction A) |
| **M110** a wrapper verifier defect is handled SYMMETRICALLY — a valid receipt is trusted whether the verifier RAISES or returns a clean FALSE-negative: an activation-binding false-negative over an existing durable row still consumes and terminalizes (never attempted-only); a terminal-transition false-negative on a valid receipt still reports `audit_committed=True`; and a `committed=True` response-loss under a verifier that cannot observe is trusted, while a CLEANLY-observed missing transition with `committed=True` stays contradictory → `None` | `test_an_activation_verifier_false_negative_still_terminalizes` · `test_a_terminal_verifier_false_negative_preserves_audit_commit` · `test_committed_true_response_loss_survives_a_verifier_defect` · `test_committed_true_with_a_clean_missing_transition_stays_none` · gates `activation-verifier-false-negative` · `terminal-verifier-false-negative` · `committed-true-loss-plus-verifier-raise` — **measured today** (round 26, findings 1 & 2) |
| **M111** `_safe_fallback_facts` computes its FULL truth table INLINE from the frozen `state` signals — independent of the derivation-helper family — including the previously-implicit cells: a read-then-rejected store yields `False/False/unaccepted/None`, and a known-unchanged store yields `False/False/unknown/None`; the displayed `internal-error` state set therefore includes `missing` and `unaccepted` | `test_the_fallback_preserves_read_rejected_unaccepted` · `test_the_fallback_preserves_known_unchanged` — **measured today** (round 26, finding 3 + correction B) |
| **M112** an EXACT `AuditStorageUnavailable(committed=True)` activation carrier is ITSELF proof of the durable write (§5b): the authority IS consumed, so the operation terminalizes as `migration-quiescence-required` INDEPENDENT of the readback verifier — whether it raises OR returns a clean FALSE-negative — never stranded attempted-only and never collapsed into `migration-audit-state-unknown`; a subclass carrier is not the protocol type and does not consume | `test_activation_committed_true_consumes_when_the_verifier_raises` · `test_activation_committed_true_consumes_on_a_verifier_false_negative` · `test_an_activation_committed_true_subclass_does_not_consume` · gates `activation-committed-true-verifier-raises` · `activation-committed-true-verifier-false-negative` · `activation-committed-true-subclass` — **measured today** (round 27, finding 1) |
| **M113** the AUDIT-write commit fact is a truthful TRI-STATE over durable evidence, checked via the low-level primitive `_requested_transition_durable` (NOT the monkeypatchable verifier): the EXACT REQUESTED transition durable → `True` (a verifier FALSE-negative over a real lifecycle cannot erase it, round 27 f2; a DIFFERENT well-formed event, e.g. a `current` record where `migrated` was requested, does NOT prove it, round 28 f3 — v30's `_terminal_event_wellformed` compared no payload); a durable-but-MISMATCHED-or-malformed terminal write that LANDED → `None`, never `False` — an audit write occurred, just not the requested one (round 29, finding 3); a TOTAL absence of any terminal transition with a proven no-write (exact committed=False or a raw no-write failure) → `False` (round 20 f2); only the EXACT `AuditStorageUnavailable` type contributes trusted metadata, so a subclass cannot FABRICATE `True` (round 27 f3); committed=True with no exact durable transition stays contradictory → `None` (round 21 f3) | `test_terminal_committed_true_false_negative_over_a_real_lifecycle` · `test_a_different_well_formed_event_never_proves_the_requested_commit` · `test_a_durable_but_wrong_terminal_write_is_none_not_false` · `test_a_total_absence_of_any_terminal_write_stays_false` · `test_a_committed_true_subclass_never_fabricates_a_commit` · gates `committed-true-with-a-different-payload` · `committed-true-different-payload-raw-exception` — **measured today** (round 27 ff. 2 & 3; round 28 f3; round 29 f3) |
| **M114** CONSUMPTION is decided by the INDEPENDENT, request-bound `_durable_lifecycle` classifier — NOT the `_durable_row_binds_authority` verifier — so a defect in that verifier (a raise OR a clean FALSE-negative) cannot suppress it: a complete durable `attempted` activation THIS call published (a non-`duplicate`, authority-bound lifecycle) is CONSUMED and terminalizes as `internal-error` WITH a terminal event for EVERY nontrusted carrier — committed-false, committed-none, a raw exception, a wrong-type return, an invalid receipt — closing the M90/M95 gap v30 left for all carriers except the two it special-cased; a genuine `duplicate` still identifies a prior/concurrent consumer and a genuinely absent lifecycle keeps the typed retry distinction | `test_a_complete_durable_activation_terminalizes_for_every_carrier` (5 carriers × 2 verifier modes) · `test_a_prior_complete_run_stays_quiescence_not_reconsumed` · `test_a_genuinely_absent_activation_keeps_the_retry_distinction` · gates `durable-activation-*-verifier-{raises,false-negative}` — **measured today** (round 28, finding 1) |
| **M115** request-bound durable evidence survives an INVALID return too — the outer post-consumption catch preserves the exact requested `migrated` facts + `audit_committed=True` when EITHER a valid receipt was returned OR `_audit_commit_fact` independently proves the requested transition durable, so an exact transition followed by an invalid return AND a raising verifier is not discarded to fallback `internal-error`/`None` (M86/M108 are not limited to a valid receipt) | `test_an_exact_transition_survives_an_invalid_return_plus_raising_verifier` · gate `exact-transition-invalid-return-verifier-raises` — **measured today** (round 28, finding 2) |
| **M117** **(v33, 0013-PA1)** the migration stamp is read back and must equal `SCHEMA_VERSION` before commit | the 0013-PA1 mutation table: every stamp perturbation (skip; each lower or higher value) KILLED at the stamp's postcondition |
| **M118** **(v33)** after the `store_identity` step, exactly one row `id = 1` with a canonical UUIDv4 `origin`; a pre-existing row unchanged | the mutation table: row dropped, value altered, statement skipped, each KILLED at the step |
| **M119** **(v33)** after the `store_epoch` step, exactly one row `id = 1`; a created row carries the migration's one clock read and the passed `schema_at`; a pre-existing row unchanged | the mutation table, as M118 |
| **M120** **(v33)** the v13 baseline writes exactly one `baseline` event per pre-existing edge, `state` byte-equal to the edge's `json`, `reason` NULL, `recorded_at` the one clock read, one `txn` and contiguous `seq` per user | the mutation table: an event dropped, a `state` altered, the step skipped, each KILLED at the step |
| **M121** **(v33)** the v2→v3 conversion, checked against each row's RAW legacy JSON: the three chain fields set; every other present key, at any depth, equal AS ITS DECLARED TYPE (a datetime as the same instant, naive stays naive); a missing `observed_at` equal to the migration's ONE recorded clock read, a present one unchanged in that sense; every added key a declared field equal to the JSON form of its declared constant default, the set derived from the models; an undeclared raw key refused unless it is in the retired set (`provenance.source_type`); non-outcome episodes byte-unchanged | the mutation table, plus six mutants: read the legacy row through the model (the check passes vacuously); re-read the clock per row; overwrite a present `observed_at`; compare present keys as strings (control: a legacy row in `+00:00` form must migrate); add a key with a non-default value; drop an undeclared key outside the retired set |
| **M122** **(v33)** after the v3→v4 drop, `wiki` has zero rows | the mutation table: a row kept, the statement skipped, each KILLED at the step |
| **M123** **(v33)** each postcondition runs inside the migration's transaction, immediately after its step and before the next, reads the database's own bytes (a pre-step state it needs is its own read of the database before the step, never a value the step kept), and on failure refuses with `unsupported-migration` naming the step, leaving the store unchanged | a postcondition reading the step's own variable (passes whatever was written); one run only at the end; a failure that commits |
| **M116** the COMPLETE durable lifecycle is classified before EVERY activation carrier — including the trusted committed=True fast path (M99 extended): an existing valid TERMINAL lifecycle is a consumed replay already complete → `migration-quiescence-required` with NO second terminal-write attempt, never converted into a `MigrationAuditWriteError`; committed=True proves SOME activation committed, never that a pre-existing terminal operation belongs to THIS invocation. (Distinguishing a prior ATTEMPTED-only lifecycle from this call's fresh publication needs invocation-provenance — a deferred `0008` production obligation, §8a — so the draft conservatively terminalizes a non-`duplicate` attempted lifecycle) | `test_a_completed_lifecycle_beats_an_exact_committed_true_carrier` · `test_a_fresh_committed_true_activation_still_terminalizes` — **measured today** (round 29, finding 2) |

---

## 7. Failure modes and reversibility

**Failure is refusal to open, which is loud and safe.** The unacceptable failure
is opening and silently misreading — `0007`'s framing, unchanged.

**A real migration is not reversible**, and this is the spec that has to say so.
`0007` §7 already carries the operational downgrade contract: a pre-migration
backup, no downgrade to a pre-`0007` binary, installer fencing where the
packaging supports it, loud release documentation, and a recovery path from the
backup. **A declaration that a migration is "one-way" is not a fence.**

---

## 8. Claims and limits

**Claim, bounded (round 2):** a version-1 store can be brought to version 2 by
the declared migration under an explicit offline authority, or is refused with
a closed reason. **Skipped-release upgrading is not claimed** — it is the
mandatory requirement the first two-step spec must demonstrate.

**Limits:**

- **Cooperating concurrent openers are serialised** by the write lock (§5b);
  **stale old-version processes are unsupported unless quiesced** — the
  distinction round 2 required in place of v3's contradictory "not
  multi-process" line.
- **The `MigrationAuthority` is an attestation, not a verification** — ruled
  acceptable at the library boundary in round 3: a library cannot prove every
  process on the host has stopped, so it refuses without the attestation,
  validates its types and bindings exactly, and never auto-migrates. What the
  host attests, the host owns.
- **Not a sandbox.** §4b's authorizer defends against an accidental declared
  statement. **Migration statements are trusted code.**
- **Not equivalence.** A third-party database that is equivalent but differently
  written is refused, per `0007` §4a.
- **Bounded by the qualified runtimes.** `0007`'s runtime gate applies; a
  migration path's output must be recorded per qualified runtime.

---

## 8a. Acceptance boundary — M-Q4 RULED (round 19)

Round 19 ruled M-Q4 and **froze a finite acceptance boundary**: `0013` reviews
the *abstract migration design and audit protocol*; the *production audit sink*
is reviewed with `0008`. Arbitrary mutation of the in-process reference's private
immutable state can always expose one more defensive readback, so proving every
possible backend correct is **not** a finite acceptance criterion for `0013`.

**`0013` is acceptable when these finite properties are frozen in normative text
and mechanically demonstrated** (they are — see the invariants table and the two
pre-send gates):

1. **Concrete migration correctness** — the reviewed v1→v2 declaration preserves
   source data, reaches the exact v2 constructor manifestation, and stamps only
   after evidence-authorised validation (§5, M1–M12).
2. **Planner and evidence architecture** — one shared planner, one evidence
   snapshot, exact path-record selection, runtime qualification (v34: replaced carrier by carrier, §5f.3),
   source/release/
   declaration binding, no migration through ordinary opening (§5b–§5c).
3. **Closed public semantics** — every expected failure maps to the frozen
   outcome vocabulary; the two named exceptions and the `TerminalFacts` truth
   table are internally consistent (§5d, gate 1).
4. **Abstract audit protocol** — activation is one atomic compare-and-set
   creating the operation + attempted event; terminal publication is one atomic
   `attempted → terminal` transition; the duplicate, unavailable, unknown-commit,
   committed-response-loss and terminal-write-failure states are distinguished
   (§5e).
5. **Adapter conformance surface** — typed receipts and typed failures have total
   validators; public outcomes, terminal facts, and known store/audit commit
   facts cannot contradict one another (§5e, M81–M89).
6. **Independent mechanical gates** — the normative outcome/fact table and each
   named adapter return/failure class are covered without importing the
   implementation's own expected-answer tables (`tests/test_0013_presend_gates.py`).

Acceptance does **not** require the wrapper to stay correct after arbitrary direct
replacement of the reference's private immutable state, nor after an adapter
violates the frozen atomicity contract while returning a success receipt. Those
are **backend-conformance tests for `0008`'s adapter.**

**These land with `0008`'s production audit sink as explicit blocking
implementation obligations** (not residual risks silently accepted here):

- real two-table DDL with primary, foreign, uniqueness, enum and field
  constraints;
- one DB transaction for activation and one compare-and-set transaction for
  terminalisation;
- multiprocess operation-ID consumption;
- commit-status handling when the DB commits but the response is lost;
- readback from a transactionally consistent snapshot;
- preservation and immutability of the attempted record during terminalisation;
- restart-safe attempted-only reconciliation and durable lookup by operation id,
  **including invocation-provenance** — an activation-attempt token minted before
  the sink call and bound into the operation/attempted record, so the classifier
  distinguishes THIS invocation's fresh activation from a prior/concurrent
  attempted-only lifecycle (round 29, finding 1). The in-process draft cannot bind
  the current `activate()` invocation without such a token — a pre-call existence
  check races another process — so it conservatively terminalizes a non-`duplicate`
  attempted lifecycle; the production sink MUST reconcile by invocation provenance;
- detection of malformed or contradictory existing audit rows;
- **the actual `current`-with-repair `transaction_committed=True` contract** (the
  one item the draft can demonstrate but not freeze — carried since round 8);
- crash injection before commit, after commit, and during response delivery.

The draft `DraftAuditStore` remains an **executable protocol model**, not proof
that any future database adapter implements the protocol.

---

## 9. Brief for the external reviewer

> **STATUS: `accepted` 2026-08-07 on the finite M-Q4 §8a boundary — see
> `## Review closure`.** Round 29's findings 2 & 3 are closed in v32; finding 1
> (invocation-provenance) is a deferred `0008` obligation. The brief below is
> retained as the round-28 → v31/v32 record.

**Round 29 of this spec. All three round-28 blockers and both corrections are
closed; every probe reproduced first. The M-Q4 boundary (§8a) held.** Round 28
showed that v30's OWN fixes were incomplete/unsound against FROZEN invariants — so
v31 fixes the ROOT (makes the rules TOTAL) rather than special-casing a third time.
Concrete migration, evidence-selection key, release identity, source binding,
one-snapshot reader, TEMP confinement and ordinary planner states are untouched;
the evidence artifact reproduces byte-for-byte.

1. **Consumption is decided by the INDEPENDENT lifecycle classifier, not the
   verifier** (finding 1): v30 special-cased only a valid `activated` receipt and an
   exact committed=True carrier, so a complete durable activation was left
   attempted-only for EVERY other carrier (committed-false, committed-none, a raw
   exception, a wrong-type return, an invalid receipt) when
   `_durable_row_binds_authority` raised or false-negatived — reopening M90/M95. The
   consumption decision now comes from the request-bound `_durable_lifecycle`
   classifier, independent of that verifier: a non-`duplicate`, authority-bound
   `attempted` lifecycle can ONLY be this call's fresh publication, so it is CONSUMED
   and terminalized as `internal-error` WITH a terminal event, whatever the carrier
   or the verifier's health. A genuine `duplicate` still identifies a prior/
   concurrent consumer; a genuinely absent lifecycle keeps the typed retry
   distinction.
2. **Request-bound durable evidence survives an invalid return too** (finding 2):
   v30's outer post-consumption catch preserved the requested facts +
   `audit_committed=True` only on a valid receipt, so an exact requested transition
   followed by an INVALID return AND a raising verifier was discarded to fallback
   `internal-error`/`None`. It now also consults `_audit_commit_fact` (request-bound
   durable evidence); M86/M108 are not limited to a valid receipt.
3. **The audit-commit proof is REQUEST-BOUND** (finding 3): v30's M113 used
   `_terminal_event_wellformed`, which validates an event as an individually legal
   historical record but compares NO requested payload — so a durable `current`
   record (a legal `current`-with-repair cell with the same physical destination
   facts) proved that a REQUESTED `migrated` write committed, and the exception
   reported `audit_committed=True` beside `migrated` facts while the durable record
   said `current`. The proof is now the low-level primitive
   `_requested_transition_durable`, which matches the requested payload
   field-for-field and sits BELOW the monkeypatchable verifier, so a verifier defect
   still cannot suppress real evidence.

**Corrections**: **(A)** the carrier-matrix claim is narrowed until
M90/M95/M86/M108/M112–M115 coexist over the same carrier × verifier-mode matrix.
**(B)** the independent gate adds the missing cells — nontrusted activation carriers
× raising/false-negative verifier, an invalid terminal return + complete exact
transition + raising verifier, and a committed=True failure with a different
well-formed terminal payload — each proven non-vacuous by neutering its fix. The
`committed=True` failure carrier's authority is the frozen typed-failure contract of
§5e, not the success-receipt allowance.

**On the boundary.** Every finding was *inside* the six §8a properties — the
noncontradictory-facts guarantee, the total post-consumption boundary, and the
abstract lifecycle's "every consumed ending terminalizes" — and each rests on the
M-Q4 allowance to trust a valid success receipt. None required defending the
reference's private state against arbitrary corruption; that remains a `0008`
obligation.

**Where I am least confident:** unchanged — the `current`-with-repair
`committed=True` cell (§8a `0008` obligation, carried since round 8): the draft
demonstrates the kernel's `transaction_committed` contract but cannot freeze it
for a production planner that repairs in a separate transaction.

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~M-Q1~~ | **RULED by round 9, 2026-08-03: wait.** `0013` must not reach `accepted` before it is reviewed **against an actual migration** — that is the principle that justified the `0007` scope cut, and it applies equally to the replacement. **The first case is `0008`'s `confirmations` table**: accepted, simple, additive, already blocked on `0013`, and independent of `0006`'s unresolved source-identity design. **`0013` may generalise only what that real migration demonstrates.** | resolved | external | — |
| ~~M-Q2~~ | **RULED (round 1) adopt-with-conditions; condition RESOLVED (round 2) by the offline boundary; boundary APPROVED (round 3) at the library level** with the narrowed claim (§5b: ordinary opening cannot initiate migration; the trusted deployment authority owns quiescence, fencing and backup validity) and the authority binding conditions (exact types, bound to store/migration/operation; release-identity binding at implementation). | resolved | external | — |
| ~~M-Q3~~ | **RULED by round 9: yes, it belongs here.** The capability comparison exists to decide whether a *migration result* satisfies its destination despite differing DDL, so it is `0013`'s. `0007` retains exact manifestation identity, digest comparison, rebuildable drift and candidate resolution — and `capability_problems()` has been removed from its kernel. | resolved | external | — |
| ~~M-Q5~~ | **RULED by the owner, 2026-10-14: keep the fill.** Quentin chose “Keep the fill”: “Keep today's behaviour, made explicit and checked: one clock read per migration, recorded.” He declined “Leave it unknown”. The v2→v3 step fills a legacy episode's missing `observed_at` with the migration's ONE recorded clock read (§4f; M121) | semantic | — | resolved |
| ~~M-Q6~~ | **RULED by accepted 0016 D2** (raised and closed at v33's respin, 2026-10-14): `Provenance.source_type` is deleted, and historical keys in stored JSON are dropped on read. The v2→v3 step's drop of it from outcome rows persists that ruling. v33 admits exactly that key by name and refuses any other undeclared key | semantic | — | resolved |
| ~~M-Q4~~ | **RULED by round 19: the acceptance boundary is frozen (§8a).** `0013` reviews the abstract migration design and audit *protocol* against six finite, mechanically-gated properties (concrete migration correctness; planner/evidence architecture; closed public semantics; abstract atomic audit protocol; adapter conformance surface; independent gates). It does **not** require the in-process reference to defend against arbitrary direct corruption of its private immutable state, nor an adapter that violates atomicity while returning a success receipt — those are **`0008` adapter-conformance tests**. Ten production obligations (real DDL/constraints, one activation + one compare-and-set transaction, multiprocess consumption, response-loss handling, consistent-snapshot readback, attempted-record immutability, restart-safe reconciliation, malformed-row detection, the `current`-with-repair `committed=True` contract, crash injection) become explicit blocking `0008` gates. The draft is an executable protocol model, not proof that a backend implements the protocol. | resolved | external | — |

---

## 11. Round 1 review disposition

**Verdict: architecture approved directionally; v2 deferred.** 7 findings, all
taken; the acceptance bar was answered — narrow `0013` to what this migration
demonstrates, and reopen the general model at the first `ALTER`.

| # | finding | closed by |
|---|---|---|
| 1 | `correlation_id` nullable contradicts §6c; `id` accepts NULLs; `0008` §6d contradicts §6c | **DDL corrected** — both NOT NULL, generation model stated; **`0008` §6d corrected in place, dated** |
| 2 | column-only capability stamped a wrong-UNIQUE destination | **exact constructor identity** authorises this migration; regression test rolls it back |
| 3 | capability treated as authorisation; path identity too weak | **§5c freezes the evidence record** — runtime × source digest × output digest × declaration digest; capability is context only |
| 4 | missing rebuildable index stamped unrepaired | **repair before stamp**, then exact-identity revalidation; regression test |
| 5 | the write lock does not fence a stale v1 process | **M-Q2 ruled adopt-with-conditions**; hazard measured as a test; **quiescence contract is spec text**, enforceability an implementation obligation |
| 6 | a stray 2→3 step validated | **exact key sets both directions**, nonempty statement tuples; regression test |
| 7 | skipped-release not demonstrated | **claim withdrawn and bounded**: adjacent v1→v2 only; the planner is reviewed at the first two-step spec |

---

## 12. Round 2 review disposition

**Verdict: concrete migration and direction approved; v3 deferred.** 4
blockers, 4 inconsistencies, all taken.

| # | finding | closed by |
|---|---|---|
| 1 | the instrument bypassed `0007`'s gates | **integrated planner** — runtime gate first; *current* validates + repairs; malformed stamped v2 refuses. Regression tests for both probes |
| 2 | path evidence attested less than it authorised | **full-manifest hashes** (acceptance digest is rebuildable-blind, measured); defined canonical bytes; exact cardinality; complete output reproduced |
| 3 | quiescence was prose over auto-migration | **offline boundary**: `migration-required` on ordinary open; `MigrationAuthority`; closed failure model. M-Q2's condition resolved |
| 4 | one-transaction was a calling convention | **executable precondition**, re-checked per statement; the autocommit partial-migration case is a regression |

---

## 13. Round 3 review disposition

**Verdict: concrete v1→v2 approved directionally; v4 deferred for a focused
v5.** Four load-bearing guarantees were false in the executable instrument;
all four taken, plus the M-Q2 ruling and every additional correction.

| # | finding | closed by |
|---|---|---|
| 1 | the "integrated planner" was a second hand-written state machine — empty and unstamped stores answered `unexpected version 0`; a malformed stamped source was promised `migration-required`; a squatting table raised `OperationalError` | **the second machine is deleted.** The instrument installs the draft registry + evidence into the production kernel and calls `open_versioned()`; `0007` gains the older-row hook its §4 always delegated to `0013`. Adversarial tests across empty / unstamped / foreign / malformed±authority / squatting-name stores |
| 2 | path evidence was generated from the live migration code — an appended `DELETE FROM edges` authorised itself; the recorded source hash was never consulted; the record omitted the frozen contract's fields | **evidence is a committed artifact** (`migration_0013_evidence.json`): generator, validator (record-level consistency rules incl. output resolution), and consuming planner all exist in the draft; selection over the full frozen key; both alteration probes refuse `migration-evidence-missing`, data and stamp untouched |
| 3 | `0007`'s runtime qualification cannot attest authorizer behaviour | **migration-runtime qualification**: eleven required confinement probes per build identity, recorded and re-verified live at consumption; `migrate_store` requires both gates |
| 4 | the closed failure model leaked raw exceptions and free-form strings | **total mapping** to the closed vocabulary; `Outcome` refuses non-members; `migration-failed` and `migration-result-mismatch` demonstrably reachable via crafted-evidence tests; §5d states the package-consistency exception |
| M-Q2 | attestation model | **approved at the library boundary** with narrowed wording (§5b verbatim) and binding conditions: exact-typed authority bound to store, migration digest and operation; release-identity binding and freshness at implementation; no authority parameter on tenant-facing opening |
| a | §4c still said capability "authorises" | moved to §4c-deferred, present-tense claim removed |
| b | simulator crashed past its own refusal | gates first; clean `rc 2` on an unqualified runtime — regression test |
| c | README claimed five failing tests on 3.46.1 | package README states the measured behaviour and the artifact-regeneration path |
| d | §5c lacked record-level consistency rules | the four rules (plus output resolution) are spec text with adversarial tests for missing / extra / stale-algorithm / duplicate / contradictory records |

---

## 14. Round 4 review disposition

**Verdict: architecture standing — planner, evidence consumption,
qualification design and the concrete migration all approved; v5 deferred on
five falsifiable gaps.** All five taken, plus both additional corrections and
the acceptance-boundary ruling; the migration and the shared planner are
unchanged per the reviewer's v6 guidance.

| # | finding | closed by |
|---|---|---|
| 1 | the closed contract was not total — malformed nested evidence raised `TypeError` at context entry, a list-valued hash crashed selection-key construction, non-database bytes and unopenable paths escaped as raw SQLite errors | **type-checks before every iterate/hash/key**; context entry and the connection inside the boundary; two new frozen outcomes `invalid-store` / `store-unopenable` (§5d); registry key-type totality (`True == 1` measured); adversarial tests per nested field class |
| 2 | a malformed current-algorithm migration-runtime record was silently filtered while qualification held | **`migration_runtime_artifact_problems` poisons**: complete validity per current record, identity uniqueness, contradiction rejection, resolution to an active schema-runtime record, single-active-runtime policy; missing/mistyped algorithm = malformed, not superseded |
| 3 | path cardinality ignored foreign runtime identities — an unattested prospective record accumulated | **artifact-wide exact cardinality**: expected = every active identity × step × accepted source, actual keys equal it exactly; every current path record resolves to both qualifications |
| 4 | the `RELEASE` probe was a false positive (no savepoint; any `DatabaseError` counted as denial) — the qualification agreed with itself about a behaviour never established | **denial means `SQLITE_AUTH`** (error code on 3.11+, message fallback on 3.10); every setup is a valid statement sequence; `denies_rollback` added (twelve probes); the permissive-authorizer falsifier is the regression test |
| 5 | the authority was indefinitely replayable and bound to a path string — a replacement store migrated under an attestation belonging to the earlier file; a retargeted symlink migrated the wrong store | **the lifecycle contract is frozen in §5b**: canonical realpath at mint and consumption, source + step + migration binding, backup and release references, RFC 3339 issuance/expiry window, single-use consumption spent on acceptance; §5e names the audit as the durable consumer |
| a | registry validation raised on malformed keys | exact-int key typing before `max()`/`sorted()`/arithmetic, reported not raised |
| b | "immutable" overclaimed the artifact | *committed, not immutable* — §5c states exactly what is and is not claimed |
| c | `operation_id` had no durable consumer | §5e: the migration audit is load-bearing spec text and the authority's durable consumer at implementation |

---

## 15. Round 5 review disposition

**Verdict: architecture standing — planner, evidence-selection, artifact
cardinality, qualification and DDL all approved; v6 deferred on four
falsifiable gaps.** All taken; migration, planner and evidence-selection
unchanged per the reviewer's constraint.

| # | finding | closed by |
|---|---|---|
| 1 | `write_evidence` overwrote artifacts seeded with future migration/manifest/schema revisions — the downgrade class `0007`'s writer refuses | **monotone writes over `MigrationEvidenceRevision`**: inspect before generating, refuse byte-unchanged on any newer component or an unreadable revision; same-revision active-runtime replacement stated as explicit policy; three parametrized byte-identity regressions |
| 2 | consumption lived only in the older-row hook — an authority whose operation found the store current stayed spendable and migrated a replacement; future-dated authorities validated; no lifetime cap; `release_ref` unchecked | **acceptance = consumption, before any store access** — every outcome spends; `issued ≤ now < expires` with no skew allowance; frozen 1-hour `MAX_AUTHORITY_LIFETIME`; release-identity binding (draft: in-tree `pyproject.toml`); 256-byte token caps; atomic CAS measured under concurrency |
| 3 | `True`/`13.0`/`2.0` passed coercive equality at top level and in path records; `artifact`/`generated_at` accepted integers | **exact scalar typing before equality** everywhere; `artifact` exact string; `generated_at` parsed timezone-aware; numerically-equal wrong types poison; parametrized regressions |
| 4 | the boundary began after path canonicalization and timeout arithmetic — NUL path and mistyped timeout escaped raw | **genuinely outermost boundary**: parameter validation, fspath/realpath, the 4096-byte cap, context entry, connection, planner; `invalid-request` joins the vocabulary for malformed calls |
| — | durable authority semantics under-specified | **§5e frozen**: unique durable key, atomic compare-and-set insertion as consumption, refuse-before-store-access on attempted-record failure, crash-between = spent + re-mint with fresh attestation, post-commit audit failure mirrors `0007` §4e |
| a | generator provenance | `generator: {tool, repository_commit}` recorded and validated — diagnostic, never a substitute for the declaration digest |
| b | token fields as prose channels | 256-byte caps in the draft; frozen opaque-token formats at implementation (§5b/§5e) |

---

## 16. Round 6 review disposition

**Verdict: approved architecture restated in full; v7 deferred on five
load-bearing problems.** All taken; the concrete migration, path evidence,
authorizer probes and ordinary planner states untouched per the reviewer's
constraint. The pre-lock consumption point was **ruled an acceptable
conservative policy** — the defect was what a consumed operation could still
do.

| # | finding | closed by |
|---|---|---|
| 1 | the dedicated operation CREATED a v2 store where its attested v1 source had vanished (deleted file, empty replacement) | **migrate mode of the shared planner**: `mode=rw` connection (cannot materialise files), nonexistent path refuses uncreated, the kernel `new=` creation seam raises `migration-source-missing`, adoption off; five regression cases, each path uncreated or byte-unchanged |
| 2 | evidence monotonicity was a check-then-replace race — a future artifact published mid-generation was downgraded (measured, forced interleaving); the shared `.tmp` path collided | **serialized publication**: interprocess lock around inspect-generate-validate-stage-publish; inspection under the SAME lock; writer-unique staging; two-process barrier regression |
| 3 | the boundary leaked `UnicodeEncodeError` (surrogate paths, surrogate tokens) and whatever `__fspath__` raised | **fs-aware conversions end to end** (kernel caps fs-encoded; a non-UTF-8-named store works), guarded `fspath` mapping any exception to `invalid-request`, `_safe_repr` diagnostics, token grammars matching on the str; exactly two NAMED escapes (`PackageConsistencyError`, `MigrationAuditWriteError`) |
| 4 | no representable post-commit audit-failure outcome; four state-machine cells undefined | **§5e completed**: `migration-audit-unavailable` (attempted record; nothing consumed), `MigrationAuditWriteError(committed=False/True)` for the rolled-back and committed cases, no-op `current` writes its record, frozen typed-and-capped record schema |
| 5 | `release_ref` was a mutable package version — an authority crossed builds sharing `0.4.8` | **content-derived identity** `veracium-<version>+<source-digest>` with representation/charset/size/source/comparison/rotation frozen; `evidence_digest` binds the exact artifact consumed |
| a | `--check-evidence` said "structural checks pass" for a foreign artifact with stripped paths | cardinality validation before the identity early-return — regression test |
| b | byte caps bound, not close, a prose channel | frozen token grammars (ASCII charset, `op-<uuid4>` shape); normalization moot by construction |
| c | "RFC 3339" overclaimed the parser | wording narrowed to what the parser accepts |

---

## 17. Round 7 review disposition

**Verdict: migrate-only mode, serialized writer publication and the Unicode
boundary held; v8 deferred on five issues.** All taken; the concrete
migration, path evidence, authorizer probes and ordinary planner states
untouched.

| # | finding | closed by |
|---|---|---|
| 1 | evidence-digest binding was a reader-side TOCTOU — digest from one file read, planner context from another; a nested context silently reused the outer artifact while a B-bound authority was accepted | **one byte snapshot per operation** feeding digest, comparison, parse and planner; `_draft(loaded=…)` takes the object; nested contexts pinned to a different digest refuse. Both variants are regressions |
| 2 | the release identity concatenated raw bytes — a docstring moved across the file boundary kept the identity (measured, no collision); 12 hex chars = 48 bits | **framed, domain-separated, full-length**: per-file length-framed name and content under `veracium-release-identity-v1`, frozen ordered list, full sha256; boundary-move regression |
| 3 | the audit freeze was internally inconsistent (globally unique `operation_id` vs attempted+terminal events); duplicate-vs-outage conflated; the `current`-with-repair cell undefined | **two tables** — operations (insert = CAS consumption) and events with `UNIQUE(operation_id, event)`; duplicate = consumed (`quiescence-required`), outage = `audit-unavailable` with nothing consumed (retry measured); all four terminal cells frozen; **executable `DraftAuditStore`** with terminal records measured for `migrated` and no-op `current` |
| 4 | `source_digest` was checked only in the older hook — a garbage digest passed the `current` branch; `make_authority` materialised a zero-byte database at a missing path | **static hex64 + resolution to exactly one current path record before consumption**; minting opens `mode=rw` and refuses missing paths (nothing created) and non-accepted sources |
| 5 | the residual catch-all labelled internal defects `invalid-store` / `migration-failed` — false semantics hosts act on | **`internal-error`** with phase named and commit state (`false`/`unknown`); the two named escapes remain the only escapes |
| a | `check_evidence` raised `AttributeError` on `runtimes: [42]` | the `0007` `active_records` accessor is total (both copies); regression at the `check_evidence` level |
| b | `fcntl` is POSIX-only | stated platform bound for draft evidence GENERATION; consumption unaffected |
| c | the grammar accepts any UUID-shaped value | wording: an opaque UUID-shaped operation token |

---

## 18. Round 8 review disposition

**Verdict (reviewer's, recorded verbatim in substance): architecture
standing — the concrete migration, shared planner, evidence snapshot,
static source binding and closed-outcome direction remain approved; v9
deferred on five load-bearing gaps.** The resolution-versus-refusal split
was **approved as written**. All five taken; migration, evidence selection
key and ordinary planner states untouched.

| # | finding | closed by |
|---|---|---|
| 1 | runtime qualification attested TEMP-table denial but not the TEMP-trigger behaviour the contract depends on — a weak authorizer allowing temp triggers passed all twelve probes | **per-class probes** (table, index, view, trigger), each requiring `SQLITE_AUTH`; fifteen total; weak-authorizer falsifier as regression |
| 2 | the two-table model still admitted both terminal events for one operation, arbitrary event names and payloads, and did not freeze activation as one transaction | **enforced schema + state machine**: activation is one transaction; event enum; exact terminal payload field set/types; one terminal per operation via CAS `state`; full operation-row schema |
| 3 | terminal-write failure misreported `resulting_version` for `current` (v1 for a v2 store) and could not represent a committed repair | **kernel `OpenResult`** carries `store_changed` / `transaction_committed` / `resulting_version`; the wrapper uses them; all four terminal cells tested under forced terminal-write failure |
| 4 | release identity fell open to a shared `+unknown` sentinel on unreadable inputs, re-opening the cross-build hole | **fail-closed acquisition** — unreadable covered file, unreadable/version-less pyproject, or non-grammar-safe version each raise `PackageConsistencyError` before mint or acceptance |
| 5 | `issued_at`/`expires_at` were unbounded, noncanonical audit channels (a 100 kB string validated) | **canonical 32-char grammar** capped before parse, UTC, canonical round-trip; applied to every persisted timestamp |
| a | `event_id`/`state` named but untyped in the diagram | the record schema now types every field including `event_id` and the `state` transition |
| b | `DraftAuditStore` stored a subset of the operation-row schema | the full frozen schema is asserted on insert |
| c | M28/M32 overclaimed "measured today" | reworded; M36/M37 carry the schema/atomicity/exclusivity/four-cell evidence |
| d | `make_authority` silently defaults `quiesced` and backup | documented as test-only draft convenience, outside any production host API |

---

## 19. Round 9 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, one-snapshot evidence handling,
release-identity direction and ordinary planner states remain approved; v11
deferred on five load-bearing gaps plus the rolled-back cell and stale
wording.** The resolution/refusal split remains approved. All taken;
migration, path-evidence key, release framing, one-snapshot reader and
ordinary planner states untouched.

| # | finding | closed by |
|---|---|---|
| 1 | audit activation was two independent writes, not one rollback-capable transaction — a failure between them left the operation consumed with no attempted record | **atomic swap** of the whole `_ops`/`_events` state (production: one DB transaction); forced-failure regressions for activation and terminal publication prove nothing persists |
| 2 | the operation row omitted `backup_ref`/`issued_at`/`expires_at`/output digest, and terminal records accepted contradictory outcomes | **complete operation-row schema** plus **semantic terminal validation** — closed-vocabulary outcome consistent with the event, version ∈ {source, destination}, `store_changed`⇒commit, `migrated`⇒destination |
| 3 | an internal defect after commit recorded `committed=False` and v1 for a v2 store | **kernel builds `OpenResult` before `COMMIT`**, so a raise rolls back and every fact is truthful; regression injects a post-result-build failure and checks the store stays v1 |
| 4 | the fifteen-probe vocabulary allowed TEMP virtual tables to execute before the leak assertion | **sixteenth `SQLITE_CREATE_VTABLE` probe** (fires before module resolution → `SQLITE_AUTH` on any runtime); vtable-allowing falsifier fails qualification |
| 5 | the evidence `generated_at` — inside the `evidence_digest` — was uncapped and noncanonical | **canonical `generated_at`** at generation and validation, the same 32-char contract as every persisted timestamp |
| gap | the rolled-back terminal cell was unexercised | regression: a migration failing after a statement, forced terminal-write failure → `committed=False`, source version, store rolled back, authority consumed |
| a | §5c said "twelve probes"; timestamps described as generic ISO 8601 | corrected to the sixteen-probe vocabulary and the one canonical timestamp contract |

---

## 20. Round 10 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release framing, one-snapshot reader,
source binding, TEMP virtual-table qualification and canonical evidence
timestamp remain approved; v12 deferred on five load-bearing gaps in the
audit reference.** The resolution/refusal split remains approved. All taken;
concrete migration, evidence-selection key, release identity, source
binding, one-snapshot reader and ordinary planner states untouched.

| # | finding | closed by |
|---|---|---|
| 1 | the "atomic swap" was three attribute assignments — a failure on the second half-published the state (operation consumed, no attempted event) | **one immutable `AuditState` behind one attribute**, published in a single assignment; injection on the publish leaves the previous state; regressions for activation and terminal publication |
| 2 | the terminal validator accepted impossible success records (`current`/v1, `migrated`/no-change) | **the exact per-cell contract** — `store_changed == transaction_committed`, completed leaves the destination, each of the five valid cells frozen |
| 3 | a post-commit internal defect could not be recorded — `migration_failed` was forced to the source version | **a failure that committed leaves the destination**; a post-commit `internal-error` records `committed=True`, version = destination |
| 4 | every activation exception was mapped to the retryable `migration-audit-unavailable` | **only the typed `AuditStorageUnavailable`** is retryable; a library defect propagates to `internal-error`, nothing consumed |
| 5 | `check_evidence` raised a raw `TypeError` on `runtimes: false` and other malformed containers | **`_artifact_list` + total `active_records`**; `check_evidence` wraps each validator — clean nonzero, never a traceback; 15 field×value regressions |
| a | the schema guard was an `assert` (vanishes under `-O`) | replaced with a raise; regression runs under `python -O` |
| b | `event_id` grammar unspecified | frozen `ev-<uuid4>` |
| c | authority timestamp comments said generic ISO 8601 | corrected to the canonical 32-char form |
| d | M36/M40 overclaimed atomicity | reworded to the single-mutation design; M44 carries the atomicity evidence |

---

## 21. Round 11 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release framing, one-snapshot reader, source
binding, TEMP virtual-table qualification and canonical evidence timestamp
remain approved; v13 deferred on five load-bearing gaps in the audit
reference plus two corrections.** The resolution/refusal split remains
approved. All taken; concrete migration, evidence-selection key, release
identity, source binding, one-snapshot reader and ordinary planner states
untouched; the evidence artifact reproduces byte-for-byte (no probe
vocabulary changed).

| # | finding | closed by |
|---|---|---|
| 1 | the terminal record fabricated `resulting_version = from_version` for every non-kernel ending, so a missing or unobserved store was recorded at the source version | **`resulting_state` ∈ {destination, source, missing, unknown}** fixes the version (destination→to, source→from, missing/unknown→NULL); the validator refuses a null-version state carrying a version and a versioned state carrying the wrong one (M48) |
| 2 | the function-level `finally` restoring `isolation_level` runs on the return path and can raise, discarding the committed `OpenResult` — the caller's audit then reported v1 for a v2 store | **every committing kernel branch delivers the `OpenResult` to an infallible `on_committed` sink BEFORE the cleanup**; a forced restore-failure still delivers committed facts (kernel regression, M49) |
| 3 | a `PackageConsistencyError` raised after consumption escaped the wrapper with no terminal event | **terminalized as the audit-only outcome `package-inconsistent` and re-raised**; `MigrationAuditWriteError` remains the one non-terminalized escape (M50) |
| 4 | `AuditState` held LIVE dicts exposed through `_ops`, so a held reference could flip an operation to `terminal` and drop its attempted event outside the single publish | **read-only proxies over read-only rows**; the single publish is the only mutation path (M51) |
| 5 | validators were total over a malformed top-level container but NOT over nested malformed JSON — `schema_version={}` put a dict in a dedup key (kernel `TypeError`), a null version-record `.get`-crashed the path resolver, `accepted: false` was iterated as a bool | **a keyability guard in the kernel** (round-4 rule) and **nested-container guards in the path resolver and expected-set builder**; seven nested mutations × four validators return problem lists, `--check-evidence` a clean nonzero each (M52) |
| A | every lost `AuditStorageUnavailable` response was mapped to "not consumed", so a response lost after a durable activation invited a retry that then saw `duplicate` | **the `committed` flag decides**: proven-written → `migration-quiescence-required`; not-proven/unknown → the retryable `migration-audit-unavailable` (M52) |
| B | events were keyed by `(operation_id, event)` with `event_id` never checked, so a repeated generator produced two events with one id | **`AuditState.event_ids` enforces the `event_id` PRIMARY KEY**; a collision is refused (M51) |

---

## 22. Round 12 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP confinement qualification, named-escape direction and canonical
evidence timestamp remain approved; v14 deferred on five load-bearing gaps plus
three corrections.** The resolution/refusal split and the bounded
adjacent-migration claim remain approved. All taken; concrete migration,
evidence-selection key, release identity, source binding, one-snapshot reader
and ordinary planner states untouched; the evidence artifact reproduces
byte-for-byte.

| # | finding | closed by |
|---|---|---|
| 1 | the kernel discarded the `ROLLBACK` result, so the wrapper recorded a confirmed `source` for a store a failed rollback left partially migrated | **the kernel PUBLISHES the rollback outcome** through an infallible `on_rolled_back` sink (`rolled-back`/`rollback-failed`); `source` requires a CONFIRMED rollback, an unconfirmed one is `unknown` (M53) |
| 2 | `resulting_state=missing` conflated a vanished file with an existing, valid, empty database | **`missing` reserved for a path PROVEN absent**; an existing non-source store is `unaccepted` — distinct null-version states for distinct physical realities (M54) |
| 3 | `committed=None` was collapsed into the retryable `migration-audit-unavailable`, and `committed` defaulted to a fabricated `False` | **new closed outcome `migration-audit-state-unknown`** for the unknown case (query the durable operation first); `committed` defaults to `None` and is typed `bool | None` (M55) |
| 4 | `MigrationAuditWriteError` dropped the new `resulting_state`, so a missing and an unknown ending were indistinguishable `vNone` errors | **the exception carries `resulting_state`/`resulting_version`**, validated against the terminal schema's relationship; the message names the state (M56) |
| 5 | validators were total over seven KNOWN nested locations, not recursively — `runtime.source_id={}` and an accepted-manifest `digest={}` still put a dict in a key | **key construction guarded by the CONSTRUCTED KEY's hashability** — total over any malformed component at any depth; a recursive walk of every node × wrong-typed values raises nothing (M57) |
| A | `_operation_row` validated only the field-NAME set (`backup_ref=[]` accepted) and `_readonly` aliased caller-held lists | **every field validated to type and grammar** at the store boundary, and the published copy is frozen DEEPLY (M57) |
| B | the `event_id` grammar was declared but only uniqueness was checked | **`ev-<uuid4>` grammar enforced before publication**, alongside uniqueness (M57) |
| C | the spec embedded a `170 tests` count that went stale (the archive ran 193) | the count is no longer embedded — it is whatever pytest collects that round |

---

## 23. Round 13 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP confinement qualification, named-escape direction and canonical
evidence timestamp remain approved; v15 deferred on five load-bearing gaps plus
three corrections.** The resolution/refusal split and the bounded
adjacent-migration claim remain approved. All taken; concrete migration,
evidence-selection key, release identity, source binding, one-snapshot reader
and ordinary planner states untouched; the evidence artifact reproduces
byte-for-byte.

| # | finding | closed by |
|---|---|---|
| 1 | the unknown cell still asserted `store_changed=False`/`transaction_committed=False` even when a failed rollback may have committed partial changes | **tri-state facts**: `store_changed`/`transaction_committed` are `True`/`False`/`None`; a rollback attempted-and-failed leaves both `None`, a confirmed rollback or never-entered transaction a known `False` (M58) |
| 2 | a post-commit `conn.close()` `DatabaseError` was mislabelled `invalid-store`, telling the host to remediate a valid v2 database | **classify by PHASE**: a cleanup-phase or post-committed-facts `DatabaseError` is `internal-error` carrying the committed facts; `invalid-store` is only for bytes failing WHILE read (M59) |
| 3 | `os.path.lexists` (False on `EACCES`) was treated as proof a path was absent | **`os.lstat`**: only an explicit `FileNotFoundError` is `missing`; an unsearchable path is `store-unopenable` (M60) |
| 4 | the terminal validator accepted outcome/state pairs the outcome cannot produce (`locked`+source, `invalid-store`+missing, …) | **a per-outcome allowed-state map**, the union over every raise site; records outside it reject (M61) |
| 5 | `MigrationAuditWriteError` enforced only the null-version rule — a subset of the record's contract | **one validated `TerminalFacts`** shared by the record and the exception, carrying outcome/endpoints/tri-state facts/state/version; the exception's contract is now identical to the record's (M62) |
| A | the operation-row store path accepted embedded NULs | rejected, along with explicit filesystem-encoding failures (M62) |
| B | M48, the §5d table and the lifecycle rows omitted newly-frozen states | reconciled — `unaccepted`, `migration-audit-state-unknown` and `resulting_state` now appear where they belong |
| C | "confirmed rollback re-established the source" overclaimed | narrowed to "`ROLLBACK` returned successfully"; the draft does not re-hash the source manifestation |

---

## 24. Round 14 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP confinement qualification and canonical timestamp contract remain
approved; v16 deferred on five load-bearing gaps plus three corrections.** The
resolution/refusal split and the bounded adjacent-migration claim remain
approved. All taken; concrete migration, evidence-selection key, release
identity, source binding, one-snapshot reader and ordinary planner states
untouched; the evidence artifact reproduces byte-for-byte.

| # | finding | closed by |
|---|---|---|
| 1 | `TerminalFacts` was weaker than the record — it accepted partial `None` pairs, `(None,None)` non-unknown cells, and a no-change `migrated` (that rule lived only in the record validator) | **the COMPLETE tuple validated in `TerminalFacts.problems()`**: change and commit are the same tri-state value; `(None,None)`→unknown, `(True,True)`→destination; `migrated`→changed+committed — shared verbatim by both carriers (M63) |
| 2 | a `committed=True` activation-response loss left a durably-consumed operation with only an attempted event | **`_consume_authority` marks the operation consumed the instant consumption is PROVEN**, so the wrapper writes its terminal event (M64) |
| 3 | a terminal write that committed then lost its response was indistinguishable from one that never landed | **`MigrationAuditWriteError.audit_committed`** (`True`/`False`/`None`) carries the AUDIT write's own commit status, distinct from the store's (M65) |
| 4 | SQLite errors were classified by "commit facts exist", so a runtime-gate `DatabaseError` before any read became `invalid-store` | **classified by READ SITE**: only a `DatabaseError` inside `open_versioned`'s read is `invalid-store`; everything else is `internal-error` (M66) |
| 5 | a post-commit `package-inconsistent` carried `destination` facts the permits-only-unknown map rejected, escaping as a raw `ValueError` and losing the named escape | **`package-inconsistent` permits `destination`/`source`/`unknown`**; it terminalizes with the proven facts at any phase and re-raises the original escape; a terminal-write failure is always `MigrationAuditWriteError` (M67) |
| A | `TerminalFacts.problems()` raised `TypeError` on `outcome=[]`/`resulting_state={}` | type-checked before set membership — total (M63) |
| B | the write-error carrier accepted a relative/NUL/oversized path and reversed endpoints | validates its own context: absolute NUL-free capped path, adjacent ordered endpoints (M67) |
| C | the permission-denial regression failed under root (which traverses `chmod 0`) | skipped when effective UID is zero |

---

## 25. Round 15 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP-confinement qualification and canonical timestamp contract remain
approved; v17 deferred on five load-bearing gaps plus four corrections.** The
resolution/refusal split and the bounded adjacent-migration claim remain
approved. All taken; concrete migration and approved elements untouched; the
evidence artifact reproduces byte-for-byte.

| # | finding | closed by |
|---|---|---|
| 1 | an invalid audit-activation return value (`None`, wrong type, unknown string) was treated as success, permitting a migration with no operation row or attempted event | **only `activated` proceeds**; any other value is `internal-error` BEFORE the store is opened (M68) |
| 2 | a malformed kernel result escaped the terminal wrapper as `AttributeError`, stranding a consumed operation | **the kernel result is validated**; a malformed return terminalizes as `internal-error`, and terminal derivation is inside the outermost boundary (M69) |
| 3 | a `sqlite3.DatabaseError` from migration-hook code was mislabelled `invalid-store` | **converted at the hook to `migration-failed`**; only the kernel's own read is `invalid-store` (M70) |
| 4 | a readable existing store rejected as foreign/malformed was audited `unknown`, not `unaccepted` | **`unaccepted`** for a store that opened and was read but is not an accepted source; outcome-state map updated (M70) |
| 5 | an `isolation_level` setup failure leaked the opened connection | **the cleanup scope begins the instant the connection opens** — closed exactly once (M69) |
| A | the write error inferred audit-commit status from local state, ignoring the sink exception's own `.committed` | **preserves a supplied `.committed`**; only a carrier-less exception is inferred (M71) |
| B | non-adjacent endpoints and an integer `audit_committed` were accepted | **adjacency (`to == from + 1`)** at the row, `TerminalFacts` and the write error; `audit_committed` is exact-`bool`-or-`None` (M71) |
| C | `record_terminal(op, event, None)` raised a raw `TypeError` | a non-mapping payload is a controlled schema error (M71) |
| D | the `after-rollback` package regression actually ran to commit | rewritten to inject inside the hook so the kernel genuinely rolls back (M67) |

---

## 26. Round 16 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP-confinement qualification and canonical timestamp contract remain
approved; v18 deferred on five load-bearing gaps plus four corrections.** The
resolution/refusal split and the bounded adjacent-migration claim remain
approved. All taken; concrete migration and approved elements untouched; the
evidence artifact reproduces byte-for-byte.

| # | finding | closed by |
|---|---|---|
| 1 | an activation success TOKEN was not proof — an `__eq__` spoof and a no-op returning the token both migrated with no operation row | **a typed `ActivationReceipt`** required by exact type + identity, AND the durable row/attempted event verified before proceeding (M73) |
| 2 | terminal publication had no success receipt, so a no-op sink reported `migrated` with no terminal event | **a typed `TerminalReceipt`** required and the landed event verified; a silent no-op raises `MigrationAuditWriteError` (M74) |
| 3 | the kernel-result validator checked SHAPE, not semantics — `migrated`/¬changed, `created`/`adopted` in migrate mode, `migrated`/v999 passed | **one mode-aware `OpenResult` contract**, compared with `on_committed`; a contradiction is `internal-error`, never an audit-store call reported as an outage (M75) |
| 4 | inspecting a sink exception's `committed` could leak a third raw exception | **guarded metadata read for a recognized type only** → `None` on any failure; the documented exception always escapes (M76) |
| 5 | the source could vanish between the pre-open `lstat` and the mode=rw open, misclassified `store-unopenable`/`unknown` | **a FRESH post-failure presence check** — a confirmed ENOENT is `migration-source-missing`/`missing` (M76) |
| A | attempted-only duplicate reconciliation was unspecified | the receipt's `terminal_present` distinguishes an already-complete operation from an attempted-only one to reconcile via the durable id (M73) |
| B | the "independent" gate oracle read the implementation map, and the seam sweep did not assert record completeness | the oracle is hand-written (a wrong map disagrees); the sweep asserts a success outcome leaves a row and exactly one terminal event — now catches f1/f2 (M72) |
| C | the UUID4 grammar accepted non-v4 values | version-4 and RFC-variant bits enforced on `event_id` and `operation_id` (M77) |
| D | `MigrationRefused` relied on an `assert` that vanishes under `-O` | replaced with an explicit raise (M77) |

---

## 27. Round 17 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP-confinement qualification and canonical timestamp contract remain
approved; v19 deferred on five load-bearing gaps plus three corrections.** The
resolution/refusal split and the bounded adjacent-migration claim remain
approved. All taken; concrete migration and approved elements untouched; the
evidence artifact reproduces byte-for-byte. The unifying theme — verify CONTENT,
not existence — is adopted throughout.

| # | finding | closed by |
|---|---|---|
| 1 | the activation receipt proved only that some row existed under the id — a sink could bind a DIFFERENT store | **the durable row is verified to BIND the exact authority** field-for-field before store access (M78) |
| 2 | the terminal receipt proved only that some event existed under the key — a different valid payload passed | **the durable event is verified to EQUAL the requested payload** field-for-field (M79) |
| 3 | the returned `OpenResult` could change the committed branch (`migrated`→`current`) when the fact tuple was equal | **the branch LABEL is part of the `on_committed` agreement** (M79) |
| 4 | a malformed `on_committed` value erased a proven commit and was still treated as non-null commit evidence | **the sink validates and freezes**; a defect leaves the commit state UNKNOWN, never a fabricated `False`, and never erases a valid receipt (M80) |
| 5 | terminal-fact derivation was outside the total boundary — a defect stranded a committed operation with a raw exception | **derivation/validation/publication after consumption is a total boundary** — `internal-error` from frozen facts or `MigrationAuditWriteError`, nothing else (M80) |
| A | a false `duplicate` receipt was trusted without durable proof, leaving the authority usable | duplicates are verified against the durable row; `terminal_present` is derived from durable state (M78) |
| B | receipt scalar fields were not fully validated and could leak a raw `TypeError` | both receipts have total `problems()` validators with exact typing and cross-field consistency (M81) |
| C | the mechanical gates asserted counts/local validity, not request-to-record binding | the seam sweep asserts the row binds the authority store and the terminal event carries the requested outcome; two content-mismatch seams added (M81) |

---

## 28. Round 18 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP-confinement qualification and canonical timestamp contract remain
approved; v20 deferred on five load-bearing gaps plus four corrections.** The
resolution/refusal split and the bounded adjacent-migration claim remain
approved. All taken; concrete migration and approved elements untouched; the
evidence artifact reproduces byte-for-byte. The unifying theme — verify the
COMPLETE record, both atomic parts and the whole resulting state — is adopted
throughout.

| # | finding | closed by |
|---|---|---|
| 1 | activation bound the operation ROW but verified the attempted EVENT only by key existence — a malformed attempted event under the right key let the operation proceed | **both atomic records are verified** — the attempted event's exact field set, unique `event_id`, binding and `occurred_at == row.attempted_at` (M82) |
| 2 | the terminal write verified the payload but not the `attempted → terminal` transition — a valid payload with the operation still `attempted`, or a reused `event_id`, passed | **the full transition is verified** — operation `terminal`, one terminal event, a valid unique non-reused `event_id`, the exact field set (M83) |
| 3 | `on_committed` accepted a `current`/(F,F) that says no commit, so a false one suppressed a real `migrated`/(T,T) and the audit claimed no change | **the sink distinguishes a proven commit (T,T) from a no-commit position**; a conflicting second publication is a defect and the strongest proven state is retained (M84) |
| 4 | timestamp generation, receipt equality and the exception constructor sat outside the total boundary — a hostile `__ne__` or an `audit_committed=1` leaked a raw exception after commit | **the whole post-consumption sequence is total** — exact-typed receipt validators, audit-flag sanitization, guarded construction (M85) |
| 5 | a derivation fallback recorded `internal-error` durably but the public call still returned `migrated` | **the terminal write returns the effective outcome** — public and durable agree for every non-named return (M85) |
| A | a `recorded` terminal receipt could claim `audit_committed=False` | a durably-verified `recorded` receipt must be `audit_committed=True`; `False` is contradictory, `None` is the failure path (M85) |
| B | a duplicate receipt was not bound to the authority, and `terminal_present` was unvalidated | duplicates bind the authority (a different-store row is a collision); `terminal_present` must agree with durable state (M82) |
| C | the content gate verified a subset of the durable state | the gate now asserts the COMPLETE state for a success — all authority-row fields, attempted-event contents, the transition, `event_id` integrity — with seven new content-mismatch seams; reverting any round-18 fix fails a gate (M82–M85) |
| D | the operation-id prose contradicted the enforced UUID4 grammar | the row is reconciled — `op-<uuid4>` with version-4/variant bits; the earlier "shape, not version/variant" wording is withdrawn (M77) |

---

## 29. Round 19 review disposition

**Verdict: M-Q4 RULED — the acceptance boundary is frozen (§8a). `0013` is
acceptable on six finite, mechanically-gated properties of the abstract migration
design and audit protocol; ten production obligations move to `0008` as explicit
blocking gates. Architecture standing; v22 deferred on two load-bearing semantic
gaps plus four reference-scope corrections — all closed.** The reviewer ruled
that arbitrary corruption of the reference's private immutable state is not a
finite acceptance criterion, and that production transactionality, multiprocess
durability, response-loss reconciliation, historical-row integrity and the
`current`-with-repair commit fact are `0008` adapter obligations. The two
semantic gaps were both a *verified fact overridden by a weaker one*. The bounded
adjacent-migration claim and resolution/refusal split remain approved.

| # | finding | closed by |
|---|---|---|
| M-Q4 | where does review of the abstract design end and `0008` implementation review begin? | **RULED — §8a**: six finite acceptance properties are gated in the draft; ten production obligations are explicit `0008` blocking gates; the draft is an executable protocol model, not proof a backend implements it |
| 1 | a rejected terminal receipt could still set `MigrationAuditWriteError.audit_committed=False` after the wrapper's own readback proved the write committed | **the audit fact follows the STRONGEST durable evidence** — an observed complete transition is `True`; `False` arises only from a typed sink that says definitely-not-written with no durable transition; all else `None` (M86) |
| 2 | a valid no-op `current`/(F,F) callback followed by an internal `sqlite3` defect lost its proven destination position and recorded `unknown` | **`position_established` is tracked separately from `write_commit_established`** — a proven destination survives a later defect: `internal-error`/`False`/`False`/`destination`/v2 (M86) |
| A | terminalisation verified the terminal delta but not that the operation row and attempted event were preserved | **the row and attempted event are snapshotted at activation and verified immutable** (only the state changes); the premise is frozen in §5e text and enforced in `0008` (M87) |
| B | a malformed duplicate lifecycle was treated as an ordinary consumed replay | **a malformed/contradictory lifecycle is audit-integrity `internal-error`**, distinct from a valid completed or attempted-only replay (M88) |
| C | activation readback omitted the reference `event_ids` index and exact row field-set checks | **both are checked** in the readback and the pre-send gate; §8a names the production PK/schema constraints as the `0008` equivalent (M88) |
| D | receipt validators used `isinstance(x, str)`, not total over a hostile `str` subclass | **`type(x) is str` before comparison** — a subclass whose equality raises is classified, not executed (M89) |

---

## 30. Round 20 review disposition

**Verdict: M-Q4 boundary respected and applied as ruled; architecture standing;
v23 deferred on three load-bearing semantic gaps plus two corrections — all
closed.** No finding relied on arbitrary private-state corruption or reopened a
`0008` obligation. Every gap was the same class: the STRONGEST durable evidence
was not applied on *every* path, so a weaker carrier could override a verified
fact. The bounded adjacent-migration claim, resolution/refusal split, and finite
M-Q4 acceptance framework remain approved.

| # | finding | closed by |
|---|---|---|
| 1 | a complete durable activation could be treated as unconsumed when the sink returned an invalid receipt or raised `AuditStorageUnavailable(committed=False)` — leaving an attempted-only operation and (in the latter case) falsely advertising a safe retry | **strongest-evidence precedence on activation** — a durable row means consumed regardless of the carrier: `internal-error` WITH a terminal event; only a genuinely absent row trusts the typed flag (M90) |
| 2 | a terminal sink that published the complete transition and then raised a contradictory typed exception still produced `MigrationAuditWriteError.audit_committed=False` | **one `_audit_commit_fact` helper governs BOTH the return and raise paths** — an observed complete transition is `True` (M91) |
| 3 | terminal-derivation fallback discarded established non-commit states, recording `unknown` for a proven current-v2 destination or a proven-missing source | **the fallback reconstructs via the canonical `_store_facts_from_state`** (no divergent copy) and preserves every established physical state; `internal-error` permits the full state set (M92) |
| A | the shared `TerminalFacts.problems()` was non-total over a hostile `str` subclass (`__hash__` raises) | **`type(x) is str` before hashing/membership** (M93) |
| B | a `duplicate` activation receipt could claim `audit_committed=False`, contradicting the durable row | **a `duplicate` must be `audit_committed=True`** — `False` rejects as `internal-error` (M94) |

---

## 31. Round 21 review disposition

**Verdict: M-Q4 boundary respected and applied as ruled; architecture standing;
v24 deferred on three load-bearing semantic gaps plus two corrections — all
closed.** No finding relied on private-state corruption or reopened a `0008`
obligation. Each gap was the round-20 principle not yet applied to *every*
carrier: strongest durable evidence, and validator totality, held for the
recognized carriers but not the unrecognized ones. The bounded adjacent-migration
claim, resolution/refusal split, and finite M-Q4 acceptance framework remain
approved.

| # | finding | closed by |
|---|---|---|
| 1 | a complete durable activation was left attempted-only when the adapter returned a non-receipt or raised an unrecognized post-publication exception (consumption was established only inside selected carrier branches) | **durable readback precedes classifying EVERY carrier** — a `duplicate` alone means "someone else consumed it"; every other carrier over a durable row is `internal-error` WITH a terminal event (M95) |
| 2 | an adapter-supplied `MigrationAuditWriteError` was re-raised unchanged, letting it override durable proof and substitute a foreign operation id / store path | **it is an untrusted carrier** — the wrapper re-derives `audit_committed`, owns the identity, and keeps the adapter's exception only as the cause (M96) |
| 3 | a typed terminal `committed=True` with no observable transition was reported as proven audit durability | **`_audit_commit_fact` implements its exact three-way precedence** — `committed=True` with no transition degrades to `None` (M97) |
| A | timestamp validation was non-total over a hostile `str` subclass (`__len__` raises), misclassifying an invalid authority as `internal-error` | **`type(x) is str` before length/regex/parse** across the timestamp/token/digest/path validators; an invalid authority stays a closed refusal (M98) |
| B | the pre-send seam gate omitted the new carrier combinations | **added** — wrong-type return, unrecognized exception, sink-supplied write error, `committed=True`-no-transition (M95–M97) |

---

## 32. Round 22 review disposition

**Verdict: M-Q4 boundary respected and applied as ruled; architecture standing;
v25 deferred on three load-bearing semantic gaps plus two corrections — all
closed.** No finding relied on private-state corruption or reopened a `0008`
obligation. Each gap was a value or carrier trusted by SHAPE (`isinstance`, an
overridable `str()`/`problems()`, a live mutable object, a partial lifecycle
predicate) rather than by EXACT identity. The bounded adjacent-migration claim,
resolution/refusal split, and finite M-Q4 acceptance framework remain approved.

| # | finding | closed by |
|---|---|---|
| 1 | a completed (`terminal`) operation + `AuditStorageUnavailable(committed=False)` was falsely reported `migration-audit-unavailable` (safe retry) because readback recognised only a fresh `attempted` activation | **`_durable_lifecycle` classifies the complete lifecycle before every carrier** — terminal/attempted → consumed replay (`quiescence`); malformed → `internal-error`; only a genuinely absent row → `unavailable` (M99) |
| 2 | `on_committed` stored a live mutable `OpenResult` and read the branch from overridable `str()`, so a post-publication mutation or a branch-spoofing subclass made an untouched v1 store appear committed at v2 | **`_FrozenResult`** — exact `type(r) is OpenResult`, branch from the underlying value, fields copied; returned result exact-typed and compared field-for-field with no identity shortcut (M100) |
| 3 | `MigrationAuditWriteError` accepted a `TerminalFacts` subclass and invoked its overridable `problems()`, admitting impossible caller-decision facts | **`type(facts) is TerminalFacts` + `TerminalFacts.problems(facts)` (base) + `type(operation_id) is str`** (M101) |
| A | the top-level authority validator called `.strip()`/regex before exact-type rejection, so a hostile `str` subclass was `internal-error` | **exact-type every token/digest/path/timestamp field first** — a closed refusal, never a library defect (M102) |
| B | the independent gate omitted the five new cases | **added** — completed-lifecycle retry, on_committed mutation, OpenResult-subclass spoof, TerminalFacts subclass, authority `str` subclass (M99–M102) |

---

## 33. Round 23 review disposition

**Verdict: M-Q4 boundary respected and applied as ruled; architecture standing;
v26 deferred on three load-bearing semantic gaps plus two corrections — all
closed.** No finding relied on private-state corruption or reopened a `0008`
obligation. The gaps concerned the `on_committed` protocol contract (a success
trusted without its mandatory publication; a publication frozen before its cell
was validated) and the exact authority carrier type (a subclass that could
intercept attribute access). The bounded adjacent-migration claim, resolution/
refusal split, and finite M-Q4 acceptance framework remain approved.

| # | finding | closed by |
|---|---|---|
| 1 | a semantically valid `OpenResult` was accepted without any `on_committed` publication, letting an untouched v1 store be reported migrated at v2 | **a successful migrate result requires exactly one valid publication equal to it**; its absence is `internal-error` from independently-established facts (M103) |
| 2 | the callback freezer exact-typed and copied but did not apply the migrate-mode semantic table before establishing position — a `migrated`/(F,F) callback followed by a kernel error recorded a false destination-v2 state | **one shared `_cell_problems` validates the mode-aware cell at BOTH the callback and the returned result, before any fact is established** (M104) |
| 3 | the top-level authority gate accepted `MigrationAuthority` subclasses; one could begin raising after the real commit and escape from the initial fallback outside the terminal `try`, stranding the operation attempted-only | **`type(a) is MigrationAuthority` before any field access** (a subclass is a closed refusal); **the initial fallback moved inside the total boundary** (M105) |
| A | a simpler hostile authority subclass was misclassified `internal-error` before consumption | closed by the same exact-carrier-type check — a malformed authority is `migration-quiescence-required` (M105) |
| B | the independent gate omitted the three fresh cases | **added** — success-without-callback, impossible-callback-cell, authority subclass (M103–M105) |

---

## 34. Round 24 review disposition

**Verdict: M-Q4 boundary respected and applied as ruled; architecture standing;
v27 deferred on three load-bearing semantic gaps plus two corrections — all
closed.** No finding relied on private-state corruption or reopened a `0008`
obligation. The gaps were the callback protocol's cardinality (a second identical
publication accepted), the single-freeze guarantee (the returned result re-read
after validation), and the total post-consumption boundary (the rescue re-ran a
failed helper). The bounded adjacent-migration claim, resolution/refusal split,
and finite M-Q4 acceptance framework remain approved.

| # | finding | closed by |
|---|---|---|
| 1 | a value-identical second `on_committed` publication was accepted as idempotent, so two callbacks could accompany a false success | **ANY second publication is a defect** (`internal-error`); the strongest proven state is still preserved for terminal recovery (M106) |
| 2 | the returned mutable `OpenResult` was frozen once for validation then read and frozen again, letting its facts change between comparison and terminalisation | **frozen EXACTLY ONCE** — one `_frozen_result_problems` over the frozen value drives validation, equality, state, branch and terminal derivation; no re-read of the live label (M106) |
| 3 | failure of `_fallback_terminal_facts` was caught only to invoke the same failing helper again, leaking a raw exception after commit and stranding the operation attempted-only | **`_safe_fallback_facts` never re-runs a failed helper** — a fallback defect degrades to a minimal valid value, so the rescue is a wrapper-owned write error (M107) |
| A | `_static_resolution_problems` claimed totality while admitting a hostile authority subclass | **`type(a) is MigrationAuthority`** inside the helper — the totality claim holds even reached directly (M107) |
| B | the independent gate omitted the three fresh cases | **added** — double-identical callback, returned-result mutation, fallback-helper defect (M106–M107) |

---

## 35. Round 25 review disposition

**Verdict: M-Q4 boundary respected and applied as ruled; architecture standing;
v28 deferred on three load-bearing semantic gaps plus two corrections — all
closed.** No finding relied on private-state corruption or reopened a `0008`
obligation. Each gap was an already-proven fact (a durable record, a proven
commit, a consumed authority) discarded by a defect in the wrapper's OWN
verification helper — and each closure rests on M-Q4's explicit allowance to
trust a conforming adapter's success receipt. The bounded adjacent-migration
claim, resolution/refusal split, and finite M-Q4 acceptance framework remain
approved.

| # | finding | closed by |
|---|---|---|
| 1 | a verifier defect after the sink published the complete `migrated`/(T,T) transition replaced the exception's facts with `internal-error` and reported `audit_committed=None` | **track the requested facts + a valid receipt** — a wrapper-verifier defect after a valid receipt raises with the exact requested facts and `audit_committed=True` (M108) |
| 2 | a defect in the shared `_store_facts_from_state` helper after a proven commit caused `_safe_fallback_facts` to erase it to `unknown` | **the safe fallback reconstructs the strongest proven state INLINE**, independent of the derivation-helper family (M108) |
| 3 | a defect in the activation binding verifier after a real activation left the durably-consumed operation attempted-only | **a valid `activated` receipt provisionally consumes BEFORE the readback**, so a verifier defect terminalizes; a clean rejection (no row) stays not-consumed (M109) |
| A | `_static_resolution_problems` claimed totality while an exact `MigrationAuthority` could carry a hostile `str`-subclass digest | **exact-type the digest fields** (M109) |
| B | the independent gate omitted the three fresh cases | **added** — terminal-transition-verifier defect, store-fact-derivation defect, activation-readback-verifier defect (M108–M109) |

---

## 36. Round 26 review disposition

**Verdict: M-Q4 boundary respected; architecture standing; v29 deferred on three
load-bearing semantic gaps plus three corrections — all closed.** No finding
relied on private-state corruption or reopened a `0008` obligation. The theme was
the **symmetry** of a verifier defect: round 25 hardened the case where the
wrapper's OWN verifier RAISES, and round 26 found the sibling cells where it
returns a clean FALSE-negative — the recurring "checks X but not X′" shape, this
round applied to my own round-25 fixes. Each closure covers the full truth-table
matrix so the sibling cell stops leaking. The bounded adjacent-migration claim,
resolution/refusal split, and finite M-Q4 acceptance framework remain approved.

| # | finding | closed by |
|---|---|---|
| 1a | an activation-binding verifier returning a clean `(False, …)` over an existing durable row after a valid `activated` receipt stranded the operation attempted-only (round 25 handled only the RAISE) | **provisional consumption on a valid `activated` receipt with an existing durable row** covers the returns-False case too; a valid receipt with NO row stays not-consumed (M110) |
| 1b | a terminal-transition verifier returning a clean FALSE-negative on a VALID receipt reported `audit_committed=None` on the `if rprob or not tok` path | **a valid receipt sets `audit_committed=True`** regardless of a false-negative verifier (M110) |
| 2 | a `committed=True` response-loss accompanied by a RAISING transition verifier produced `audit_committed=None` (the verifier could not observe, and the typed carrier was ignored) | **`_audit_commit_fact` guards the verifier and trusts a typed `committed=True` when `ok is None`**; a cleanly-observed missing transition (`ok` False) stays contradictory → `None` (M110) |
| 3 | `_safe_fallback_facts` omitted its `False/False/unaccepted` (read-then-rejected) and `False/False/unknown` (known-unchanged) cells | **the full truth table is computed INLINE** from the frozen `state` signals (M111) |
| A | §5d prose said only a "second, DIFFERENT" publication is a defect, contradicting M106 | **prose aligned** — ANY second publication, even value-identical, is a defect |
| B | the displayed `internal-error` state set omitted `missing`/`unaccepted`, now reachable via the fallback | **added** to the state table (M111) |
| C | the independent gate omitted the three fresh verifier-false-negative seams | **added** — `activation-verifier-false-negative`, `terminal-verifier-false-negative`, `committed-true-loss-plus-verifier-raise`, each proven non-vacuous |

---

## 37. Round 27 review disposition

**Verdict: M-Q4 boundary respected; architecture standing; v30 deferred on three
load-bearing semantic gaps plus two corrections — all closed.** No finding relied
on private-state corruption or reopened a `0008` obligation. The theme extended
round 26's verifier-defect symmetry to the **`committed=True` response-loss carrier
when the verifier cannot confirm** — the recurring "handles X but not X′" shape,
here the sibling of round 26's fixes: round 26 trusted a valid *receipt* under a
verifier defect, and round 27 does the same for the *`committed=True` carrier*.
Findings 2 and 3 (the durable-presence precedence and exact-typed carrier trust)
are protocol-semantic and transfer directly to `0008`'s response-loss handling;
finding 1 aligns the code to the already-specified §5b outcome. The bounded
adjacent-migration claim, resolution/refusal split, and finite M-Q4 acceptance
framework remain approved.

| # | finding | closed by |
|---|---|---|
| 1 | an exact `AuditStorageUnavailable(committed=True)` activation carrier did not consume when the readback verifier raised or false-negatived — stranding the durably-consumed operation attempted-only, or collapsing `committed=True` into `migration-audit-state-unknown` | **the carrier is trusted as proof of the durable write BEFORE the readback** (§5b): committed=True → consumed → `migration-quiescence-required` + terminal event, whatever the verifier does; a subclass does not consume (M112) |
| 2 | a `committed=True` terminal carrier + a verifier FALSE-negative over a real complete lifecycle reported `audit_committed=None` | **the independent durable presence of a well-formed terminal event is checked FIRST** — above the verifier boolean — so a false-negative cannot erase a real commit; a genuinely-absent transition stays contradictory → `None` (M113) |
| 3 | `AuditStorageUnavailable` was recognised by `isinstance`, so a subclass overriding `committed` could FABRICATE `audit_committed=True` with no durable write | **`_trusted_carrier_committed` requires `type(exc) is AuditStorageUnavailable`** — only the exact protocol carrier is trusted; a subclass → `None`, never fabricated `True` (M113) |
| A | the round-26 "full matrix" wording was broader than the carrier matrix actually gated | **narrowed** to the mechanically-covered cross-product |
| B | the independent gate omitted the four fresh carrier combinations | **added** — activation committed=True under a raising and a false-negative verifier, a terminal committed=True false-negative, and the typed-failure subclass at both seams, each proven non-vacuous |

---

## 38. Round 28 review disposition

**Verdict: M-Q4 acceptance boundary approved and applied as ruled; architecture
standing; v31 deferred on three load-bearing semantic gaps plus two corrections —
all closed at the ROOT.** No finding relied on private-state corruption or reopened
a `0008` obligation. This round was materially different from the prior siblings:
the reviewer showed that v30's OWN fixes were **incomplete or unsound against
FROZEN invariants** — finding 1 reopened M90/M95 for every carrier v30 did not
special-case; finding 3 showed v30's M113 proof was request-UNbound, so a durable
`current` record proved a `migrated` commit. v31 therefore fixes the ROOT — making
the durable-evidence rule TOTAL via the independent lifecycle classifier and the
commit proof REQUEST-BOUND — rather than special-casing a third carrier. The bounded
adjacent-migration claim, resolution/refusal split, and finite M-Q4 acceptance
framework remain approved.

| # | finding | closed by |
|---|---|---|
| 1 | a complete durable activation was left attempted-only (no terminal event) when `_durable_row_binds_authority` raised or false-negatived beside a committed-false, committed-none, raw, wrong-type, or invalid-receipt carrier — reopening M90/M95 for every carrier v30 did not special-case | **consumption is decided by the INDEPENDENT, request-bound `_durable_lifecycle` classifier**, not the verifier: a non-`duplicate`, authority-bound `attempted` lifecycle is this call's fresh publication → consumed → `internal-error` WITH a terminal event, whatever the carrier or verifier health (M114); a genuine `duplicate`/absent lifecycle keeps its distinctions |
| 2 | a complete exact terminal transition was reduced to `audit_committed=None` + fallback `internal-error` facts when the sink returned an invalid carrier and the transition verifier raised | **the outer post-consumption catch consults request-bound durable evidence** (`_audit_commit_fact`), not only a valid receipt — the exact requested `migrated` facts + `audit_committed=True` are preserved (M115) |
| 3 | M113's proof accepted any individually well-formed terminal event, so a durable `current` event proved a REQUESTED `migrated` commit (`audit_committed=True` beside `migrated` facts while the durable record said `current`) | **the proof is the request-bound primitive `_requested_transition_durable`** — an exact field-for-field payload match, below the monkeypatchable verifier; a different event never proves the requested commit (M113 corrected) |
| A | the "carrier matrix actually gated" claim was still incomplete; the `committed=True` carrier was grounded in the success-receipt allowance | **narrowed** until M90/M95/M86/M108/M112–M115 coexist over the matrix; the failure carrier's authority is the frozen §5e typed-failure contract |
| B | the independent gate omitted the fresh carrier × verifier-mode cells | **added** — nontrusted activation carriers × raising/false-negative verifier, invalid terminal return + exact transition + raising verifier, committed=True + a different well-formed payload, each proven non-vacuous |

---

## 39. Round 29 review disposition — and acceptance

**Verdict: M-Q4 acceptance boundary approved and applied as ruled; architecture
standing. Findings 2 & 3 closed in v32; finding 1 deferred to `0008` as an explicit
production obligation. `0013` set `accepted` on the finite §8a boundary.** Round 29
confirmed what the prior two rounds implied: on an executable reference model the
reviewer's "next adjacent cell" method has no natural terminal — finding 1 was a
sibling of v31's own (deliberate) root fix. Per M-Q4, the acceptance criterion is
the six §8a gated properties (all met), not the absence of further draft edge
cells. Findings 2 & 3 were closable in the draft and are closed; finding 1 requires
invocation-provenance machinery that the in-process draft cannot bind without
racing another process — the multiprocess/reconciliation obligation M-Q4 already
assigned to `0008`. The bounded adjacent-migration claim, resolution/refusal split,
and finite M-Q4 framework remain approved.

| # | finding | disposition |
|---|---|---|
| 1 | a prior ATTEMPTED-only lifecycle can be terminalized by a later call whose sink returns a wrong type / raw exception / committed=False — because `_durable_lifecycle` binds the authority but not the current `activate()` INVOCATION | **deferred to `0008`** (§8a): a robust protocol mints an activation-attempt token before the sink call and binds it into the operation/attempted record, so the classifier tells this invocation's fresh publication from a prior/concurrent one. A pre-call existence check races another process, so the in-process draft cannot solve it; it conservatively terminalizes a non-`duplicate` attempted lifecycle. Added to the §8a `0008` obligation list |
| 2 | exact activation `committed=True` bypassed an already-terminal lifecycle, converting a consumed replay into a second-terminal `MigrationAuditWriteError` | **closed** — the COMPLETE durable lifecycle is classified before EVERY carrier, including the committed=True fast path: an existing terminal lifecycle → `migration-quiescence-required`, no second terminal write (M116/M99) |
| 3 | a durable but request-mismatched terminal write (`current` where `migrated` was requested) was reported `audit_committed=False`, though an audit write plainly landed | **closed** — the commit fact is a truthful tri-state: a landed-but-wrong or malformed transition → `None`, never `False`; `False` is reserved for a total absence of any terminal write (M113 corrected) |
| A | "request-bound root" / "total" wording overstated while M99 and M114 did not yet coexist over the matrix, and finding 1's provenance gap remained | **narrowed** — v32 does not claim a total invocation-bound classifier; finding 1's invocation-provenance is an explicit `0008` obligation, and M116 subordinates the committed=True carrier to lifecycle classification |
| B | the independent gate omitted the fresh cells | **added** — a durable request-mismatched terminal write + a raw exception (`audit_committed=None`); finding 2's prior-terminal cell needs a pre-existing lifecycle the fresh-v1 sweep cannot stage, so it is covered by a dedicated instrument test |

---

## Review closure

**Set `accepted` 2026-08-07 by dev, under `PROCESS.md` §4a (external review is
required; dev sets the status once the review's ruled acceptance criterion is
met).** The criterion is not the external reviewer's assent — round 29 still
deferred — but the **finite M-Q4 boundary (§8a)** it ruled in round 19: six gated
properties, frozen in normative text and mechanically demonstrated. All six are
met (the invariants table M1–M116 + the two pre-send gates, all green across
Python 3.10–3.13).

**Twelve external rounds (18–29 post-ruling). The architecture and the M-Q4
boundary were affirmed in every one**; each deferral was about the *draft
reference instrument's* handling of an adjacent adapter-failure edge cell, not the
design. That is expected: an executable model of a protocol has effectively
unbounded edge cells, and the reviewer's method has no natural terminal on one —
as M-Q4 anticipated when it made "the six §8a properties" the criterion rather than
"the reviewer stops finding things."

**What `accepted` does and does not mean here.** It authorises implementation of
**this spec's design** (the concrete v1→v2 migration, the planner/evidence
architecture, the abstract audit protocol, the closed public semantics). It does
**not** let code land: `Spec-Requires: 0007` is gate-enforced and `0007` is
`draft`. The residual reference-instrument findings and the ten §8a production
obligations — most saliently **invocation-provenance for attempted-only
reconciliation (round 29, finding 1)**, multiprocess consumption, the
`current`-with-repair `committed=True` contract, and crash injection — are explicit
BLOCKING gates for `0008`'s production audit sink, not risks silently accepted here.

**Rounds 18–29 — every finding is closed with something openable** (an invariant,
a test, a gate, or an explicit `0008` obligation); the per-round dispositions are
§§11–39 above and the invariant provenance is the M-column of the invariants
table. Round 29's findings 2 & 3 are closed by M116 and the M113 tri-state
correction; finding 1 is the last row of the §8a `0008` obligation list.
