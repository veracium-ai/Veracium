# Feature spec: on-disk store migrations

Spec-Status: draft
Spec-Requires: 0007

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — opened 2026-08-03. **This spec exists because cutting `0007`'s
> scope broke the gate that protected `0008`.** `0007` v10 moved the migration
> contract out; `0008` is `accepted`, adds a `confirmations` table, and declared
> only `Spec-Requires: 0007` — so accepting `0007` would have **authorised a
> schema-changing implementation whose migration design was unresolved.** Found
> by the round-8 external reviewer, and it is the most serious defect the scope
> cut introduced.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 |
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
0013  requires 0007          (versioning must exist before shape changes)
0006  requires 0013
0008  requires 0013          <- the accepted spec whose gate the cut broke
0009  requires 0013
0010  requires 0013
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

## 5. Regime analysis

**The regime `0007` could never reach:** a store at a *lower* version. `0007`
v10 has `SCHEMA_VERSION = 1`, so no positive integer is below it and the *older*
row of its decision table cannot occur. **This spec is where that row becomes
reachable**, and it is reachable by a real store rather than an injected
fixture — which is the difference that motivated the split.

---

## 6. Invariants and executable checks — REQUIRED, blocking

**Nothing here is implemented, and no test below exists.** The v9 archive
contains working implementations of most of them, written against `0007`'s
instrument; they are a starting point, not evidence.

| invariant | executable check |
|---|---|
| **M1** a declared step runs inside the caller's transaction | `test_a_migration_runs_in_the_open_transaction` |
| **M2** transaction control in a declared statement is denied | `test_transaction_control_is_denied` — `COMMIT`, `END`, `END TRANSACTION`, `ROLLBACK`, `SAVEPOINT`, `RELEASE`, `ATTACH` |
| **M3** temp objects are refused | `test_a_temp_object_is_refused` — the manifest cannot see one |
| **M4** pragmas are refused | `test_a_pragma_is_refused` |
| **M5** the authorizer is restored after failure | `test_the_authorizer_is_restored_after_a_failed_migration` |
| **M6** an empty migration cannot authorise its output | `test_an_empty_migration_is_rejected` |
| **M7** a correct `ALTER` reaches an accepted destination | `test_a_normal_alter_is_accepted` |
| **M8** an `ALTER` omitting the column is still rejected | `test_a_partial_alter_is_rejected` |
| **M9** the registry is well-formed | `test_the_migration_registry_is_well_formed` — adjacency, reachability, `SCHEMA_VERSION` binding |
| **M10** a skipped release still upgrades | `test_an_unstamped_v1_store_migrates_directly_to_v2` — **the round-1 requirement** |
| **M11** every migration path is keyed individually | `test_every_path_is_keyed` |
| **M12** runtime evidence covers every declared path | `test_incomplete_path_coverage_disqualifies_a_runtime` |
| **M13** migration is single-process | `test_concurrent_migration_refuses` |

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

**This spec exists because of a defect in the previous round's scope cut, and
that is the first thing to check.** `0007` v10 moved the migration contract into
`0006` §0b. `0008` is `accepted`, adds a `confirmations` table, and required
only `0007` — so accepting `0007` would have unlocked a schema-changing
implementation with no migration design. `0013` makes the dependency
expressible: every schema-changing spec requires it directly.

**What is carried forward and what is not.** §4 states the eight conclusions
that survived seven rounds of `0007` review, **in full rather than by reference
to an uncommitted archive**. They have not been reviewed *as this spec*, and I
am not claiming their prior approval transfers — several were approved only
"directionally", and §4c in particular changed shape in the last round before
the cut.

**Where I am least confident:**

1. **§4c's capability comparison is a third structural model** alongside
   `0007`'s digest and drift. Three ways of comparing schemas across two specs
   is a smell I flagged before the cut and have not resolved.
2. **This spec has no first migration yet.** It is opened against `0008`'s
   `confirmations` table and `0006`'s new column, but neither is written. **The
   whole argument for the cut was that a migration mechanism needs a real
   migration** — so `0013` should probably not reach `accepted` before one of
   those specs is concrete enough to hold it to.
3. **M13 is unspecified beyond its name.** Cross-process migration locking was
   pushed forward from `0007` three times without being designed.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| **M-Q1** | Should `0013` reach `accepted` **before** a concrete first migration exists, or wait for `0008`'s `confirmations` table? §9 argues for waiting. | `blocking` | external | before acceptance |
| **M-Q2** | How is single-process migration enforced (**M13**)? A lock table changes the shape being migrated; an advisory file is not a guarantee. | `blocking` | dev | before implementation |
| **M-Q3** | Does `0007`'s capability comparison belong here instead, leaving `0007` with digest and drift only? | `pre-release` | external | before implementation |
