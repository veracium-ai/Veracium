# Feature spec: on-disk store migrations

Spec-Status: in review
Spec-Requires: 0007

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v3)** — first external round: *architecture approved
> directionally, v2 deferred, 7 findings*, all taken. **The DDL is corrected**
> (`correlation_id` NOT NULL — an omitted id is *generated*, per `0008` §6c —
> and `id` NOT NULL), **this CREATE-only migration is authorised by exact
> constructor identity** rather than the column-only capability check the
> review bypassed, **and the M-Q2 ruling is adopt-with-conditions**: the write
> lock serialises cooperating openers and does NOT fence an already-running v1
> process — the quiescence contract in §5b is load-bearing and measured.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v3 |
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
(21 tests, including the wrong-UNIQUE and missing-index cases as regressions,
the strict registry, and the stale-connection hazard below).

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

**Enforceability is an implementation obligation** for the first migrating
release (`0008`'s), stated here so it cannot be quietly narrowed: release
tooling must make the quiescence condition checkable, not aspirational.

*(v2's §8 said "not multi-process" while §5b demonstrated five concurrent
openers — the contradiction is resolved as above: concurrent **cooperating**
openers are serialised by the lock; **stale** openers are the operational
contract's problem.)*

## 5c. The path-evidence record, frozen before implementation

Round 2: `v<base>:constructor-><dest>` is insufficient once a source version
has more than one accepted manifestation, and M11/M12's artifact contract is
load-bearing — frozen now, reviewed here, implemented with `0008`:

```
runtime build identity          (0007 §4a-viii)
from_version
source manifestation digest
to_version
output manifestation digest
migration declaration digest    (sha256 over the statement tuple)
```

**Capability is necessary; only recorded evidence authorises** — the migrated
manifestation must be accepted for this source × path × runtime before a stamp.

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
| **M10** a skipped release still upgrades | **NOT demonstrated, and not claimed** (round 2, finding 7). `0013` today authorises the concrete adjacent v1→v2 only; the multi-step planner is reviewed at the first spec needing two real steps |
| **M11** every migration path is keyed individually | at implementation — `0007`'s evidence gains per-path entries |
| **M12** runtime evidence covers every declared path | at implementation |
| **M13** migration runs exactly once among cooperating openers | `test_mq2_concurrent_migration_runs_exactly_once`, and the reviewer's independent five-**process** run. **The stale-opener hazard is measured, not solved** — §5b's quiescence contract. |

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

**Round 2 of this spec. All 7 round-1 findings taken; every executable one
reproduced first** — the NULL-accepting `id`, the wrong-UNIQUE stamping, the
unrepaired index, the stale-connection write, the stray 2→3 step.

**The corrections that matter most:**

1. **The DDL now says what `0008` §6c says** — `correlation_id NOT NULL`
   because an omitted id is *generated and returned as `str`*, `id NOT NULL`
   because a rowid `TEXT PRIMARY KEY` accepts NULLs (measured), tenant-scoped
   uniqueness — **and `0008` §6d's contradictory global line is corrected in
   `0008` itself, dated and attributed to your finding.** An accepted spec
   carrying an internal contradiction is worse than a dated correction.
2. **Exact constructor identity authorises this migration** (§5). Your
   wrong-UNIQUE and missing-index cases are regressions now: both roll back,
   nothing stamps. Capability survives as context only; **the general model is
   deferred to the first real `ALTER` for its own external review**, per your
   acceptance-bar answer — not banked as residual risk.
3. **M-Q2 is recorded as you ruled it** (§5b): the lock serialises cooperating
   openers — your five-process verification is cited — and does not fence a
   stale v1 process. **The hazard is a test now**, and the quiescence contract
   is spec text with enforceability named as an implementation obligation for
   the first migrating release.
4. **The path-evidence record is frozen** (§5c): runtime identity ×
   from/source-digest × to/output-digest × migration-declaration digest.
   M11/M12 implement it; the contract is reviewable in this round.

**Bounded, per your finding 7:** `0013` authorises the concrete adjacent v1→v2
migration and freezes the one-step transaction contract. Skipped-release
upgrading is a mandatory requirement that the first two-step spec must
demonstrate; **it is not claimed today.**

**Also corrected from your package verification:** v2's README misdescribed
what happens on an unqualified runtime — ordinary `SqliteStore` tests *refuse*,
they do not skip. This package's README states the actual behaviour and the
sanctioned path (regenerate runtime evidence on that runner), which is what you
did.

**Where I am least confident:**

1. **The quiescence contract is prose until `0008`'s release tooling exists.**
   I have made it load-bearing spec text with a measured hazard behind it, but
   "release tooling must make it checkable" is a promissory note, and you have
   seen what happens to those here.
2. **Whether the narrowed acceptance bar is now met.** Against your list:
   adjacent additive transactional migration ✓ · exact constructor
   manifestation after repair ✓ · corrected DDL ✓ · exact registry ✓ · path
   evidence frozen (not implemented) · operational fencing specified (not
   enforced). **The last two are the open judgement.**

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~M-Q1~~ | **RULED by round 9, 2026-08-03: wait.** `0013` must not reach `accepted` before it is reviewed **against an actual migration** — that is the principle that justified the `0007` scope cut, and it applies equally to the replacement. **The first case is `0008`'s `confirmations` table**: accepted, simple, additive, already blocked on `0013`, and independent of `0006`'s unresolved source-identity design. **`0013` may generalise only what that real migration demonstrates.** | resolved | external | — |
| **M-Q2** | **PROPOSED in §5b, awaiting external ruling:** SQLite's write lock under the §4c lock-before-read protocol is the enforcement; the caveat (one transaction per migration) is the contract. Measured with five racing openers. | `blocking → proposed` | external | this review |
| ~~M-Q3~~ | **RULED by round 9: yes, it belongs here.** The capability comparison exists to decide whether a *migration result* satisfies its destination despite differing DDL, so it is `0013`'s. `0007` retains exact manifestation identity, digest comparison, rebuildable drift and candidate resolution — and `capability_problems()` has been removed from its kernel. | resolved | external | — |

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
