# Feature spec: on-disk store migrations

Spec-Status: in review
Spec-Requires: 0007

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v2)** — opened 2026-08-03; **v2 adds the concrete v1→v2
> migration the round-9 M-Q1 ruling requires** — `0008`'s `confirmations`
> table, executable in `specs/migrations_0013.py` — and **proposes the M-Q2
> answer**: SQLite's write lock *is* the single-process enforcement, under the
> same lock-before-read protocol `0007` shipped. This spec still authorises
> nothing; the instrument is draft-side, and the store contains no migration
> code.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v2 |
| **Status** | *see `Spec-Status:` — canonical.* **Prerequisite of every schema-changing spec:** `0006`, `0008`, `0009`, `0010`. |
| **Internal reviewers** | research — pending |
| **External review** | required — a bad migration makes stores unopenable |
| **Decision + date** | — |
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

**The destination requirement is independent of the migration**, and it is
**structural capability, not identical DDL text** — comparing text byte-for-byte
rejects a correct `ALTER TABLE … ADD COLUMN`, which is the case the accepted-set
model exists to permit:

| | |
|---|---|
| every declared object exists, of the right kind | a rebuildable one may be **absent** — repairable drift |
| every declared **column** matches | name, declared type, nullability, default, primary-key position, generated flag — via `table_xinfo`, **not DDL text** |
| no extra column on a required table | and no unapproved persistent object |
| non-table objects match their DDL | an index, view or trigger has no structure apart from its definition |

**Exact DDL text remains what `0007`'s digest records.** Capability *authorises*
an output to become an accepted manifestation; the digest *identifies* it.

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

---

## 5. The concrete migration — v1 → v2, the `confirmations` table

**Per the M-Q1 ruling, this spec is reviewed against a real migration.** The
first schema change is `0008`'s audit table, derived field-by-field from its
§6b–§6d:

```sql
CREATE TABLE confirmations (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, edge_id TEXT NOT NULL,
    confirmed_at TEXT NOT NULL, actor TEXT NOT NULL, call_path TEXT NOT NULL,
    correlation_id TEXT, request_digest TEXT NOT NULL,
    UNIQUE(user_id, correlation_id)
);
CREATE INDEX ix_confirmations_edge ON confirmations(user_id, edge_id);
```

| decision | from `0008` |
|---|---|
| `confirmed_at` stores the **normalised instant** | §6c — never the caller's string |
| `actor`, `call_path` are closed-enum **values** | §6c — free text in either was the bypass `actor` demonstrated |
| `correlation_id` **nullable**; `UNIQUE(user_id, correlation_id)` | §6c — omitted means no replay protection; SQLite treats NULLs as distinct, so unprotected confirmations coexist while a reused pair conflicts, **tenant-scoped, not global** |
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

**Executable**: `specs/migrations_0013.py` (draft instrument, imports the
production kernel, implements §4a–§4d against this migration) and
`tests/test_migrations_0013.py` (16 tests: destination contract with the real
table, confinement re-proven, registry validation, the M-Q2 race, and `0008`'s
uniqueness semantics holding in the migrated schema).

## 5b. M-Q2 proposed: the write lock is the enforcement

**Proposed answer for review — this was the remaining blocking question.**

`0007` §4c already takes `BEGIN IMMEDIATE` before reading anything. Extending
the same protocol with the *older* row gives migration mutual exclusion **from
SQLite itself**:

```
open:  BEGIN IMMEDIATE            <- serialises ALL openers
       read user_version
       found == 2  ->  open as current
       found == 1  ->  apply_migration; validate destination; stamp 2; COMMIT
```

A concurrent opener blocks on the lock (bounded by `busy_timeout`, then a loud
`locked` refusal), acquires it after the winner commits, **re-reads under its
own lock**, and finds the store already migrated. Measured in
`test_mq2_concurrent_migration_runs_exactly_once`: five racing openers, one
`migrated`, four `current`, zero errors, zero duplicate work.

**Why not the alternatives:** a lock *table* changes the shape being migrated —
circular; an advisory *file* is not a guarantee and adds a second consistency
domain. **The caveat is the contract:** a migration must fit in one
transaction. The additive v2 trivially does; the single-step model (§4d) makes
that reviewable per step, and a future migration too large for one transaction
is a design problem to be caught at *its* review, not an operational surprise.

## 6. Invariants and executable checks — REQUIRED, blocking

**The store contains no migration code — `0013` authorises nothing.** The
rows below marked with test names now run against the **draft instrument**
(`specs/migrations_0013.py`) and the concrete migration; they become store
tests at implementation.

| invariant | executable check |
|---|---|
| **M1** a declared step runs inside the caller's transaction | exercised by every instrument test via `open_or_migrate` |
| **M2** transaction control in a declared statement is denied | `test_transaction_control_and_pragmas_are_denied` — **measured today**, six forms |
| **M3** temp objects are refused | `test_a_temp_object_is_refused` — **measured today** |
| **M4** pragmas are refused | `test_transaction_control_and_pragmas_are_denied` — **measured today** |
| **M5** the authorizer is restored after failure | `test_the_authorizer_is_restored_after_failure` — **measured today** |
| **M6** an empty migration cannot authorise its output | `test_an_empty_migration_cannot_authorize_its_output` — **measured today**, against the real `confirmations` requirement |
| **M7** a correct migration reaches its declared destination | `test_the_concrete_migration_reaches_the_v2_constructor_output` — **measured today**; output byte-identical to the constructor |
| **M8** a partial or wrong-shape result is rejected | `test_a_partial_migration_is_rejected` — **measured today** |
| **M9** the registry is well-formed | `test_m9_the_draft_registry_is_well_formed` · `test_a_gap_refuses` — **measured today** |
| **M10** a skipped release still upgrades | at implementation: version-zero resolution (`0007` §4-i) feeds the *older* path. The instrument's `open_or_migrate` demonstrates the stamped-v1 half |
| **M11** every migration path is keyed individually | at implementation — `0007`'s evidence gains per-path entries |
| **M12** runtime evidence covers every declared path | at implementation |
| **M13** migration runs exactly once under concurrency | `test_mq2_concurrent_migration_runs_exactly_once` — **measured today**: five racers, one migrates, four open current. §5b |

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

**Claim:** a store created by any supported released version can be brought to
the current version without installing intermediate releases, or is refused.

**Limits:**

- **Not multi-process.** Migration must be run by one process (**M13**).
  `0007`'s S20 covers concurrent *first open*, not concurrent migration.
- **Not a sandbox.** §4b's authorizer defends against an accidental declared
  statement. **Migration statements are trusted code.**
- **Not equivalence.** A third-party database that is equivalent but differently
  written is refused, per `0007` §4a.
- **Bounded by the qualified runtimes.** `0007`'s runtime gate applies; a
  migration path's output must be recorded per qualified runtime.

---

## 9. Brief for the external reviewer

**This is `0013`'s first review, and per your M-Q1 ruling it arrives with the
real migration**: `0008`'s `confirmations` table, two `CREATE` statements,
executable in `specs/migrations_0013.py` and exercised by 16 tests. `0007` is
`accepted` and implemented, so the migration runs against the real kernel.

**The three things to review hardest:**

1. **The table DDL against `0008` §6b–§6d** (§5). Every column decision cites
   its clause; if I have mistranslated the frozen contract into DDL, this is
   the round to catch it — `0008`'s implementation will inherit this shape.
2. **The M-Q2 proposal** (§5b): the write lock is the enforcement, and the
   one-transaction caveat is the contract. Measured under a five-way race. If
   this is wrong, everything downstream of the *older* row is wrong with it.
3. **The convergence caveat** (§5): this migration's output is byte-identical
   to the constructor's, so it does NOT exercise the `ALTER`-divergence case
   the accepted-set model exists for. I have said so rather than presenting
   the convergence as evidence. **Generalising only what this migration
   demonstrates — your ruling — means the set model's divergence handling
   stays unproven until the first `ALTER`**, and I would like that recorded as
   accepted residual risk rather than discovered later.

**What this spec still does not do:** authorise implementation (it is not
`accepted`); ship migration code in the store (the instrument is spec-side);
extend runtime evidence with per-path entries (M11/M12 land with
implementation).

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~M-Q1~~ | **RULED by round 9, 2026-08-03: wait.** `0013` must not reach `accepted` before it is reviewed **against an actual migration** — that is the principle that justified the `0007` scope cut, and it applies equally to the replacement. **The first case is `0008`'s `confirmations` table**: accepted, simple, additive, already blocked on `0013`, and independent of `0006`'s unresolved source-identity design. **`0013` may generalise only what that real migration demonstrates.** | resolved | external | — |
| **M-Q2** | **PROPOSED in §5b, awaiting external ruling:** SQLite's write lock under the §4c lock-before-read protocol is the enforcement; the caveat (one transaction per migration) is the contract. Measured with five racing openers. | `blocking → proposed` | external | this review |
| ~~M-Q3~~ | **RULED by round 9: yes, it belongs here.** The capability comparison exists to decide whether a *migration result* satisfies its destination despite differing DDL, so it is `0013`'s. `0007` retains exact manifestation identity, digest comparison, rebuildable drift and candidate resolution — and `capability_problems()` has been removed from its kernel. | resolved | external | — |
