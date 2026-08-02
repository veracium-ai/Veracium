# Feature spec: on-disk store schema versioning

Spec-Status: in review

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v3)** — opened 2026-08-01. **Round 1 deferred the shape
> comparison and approved the direction.** v3 replaces names+declared-types with
> a **semantic signature**, validates shape at *every* version rather than only
> at adoption, and **proves the adoption premise against all 23 released
> versions** instead of asserting it. **It is the `Spec-Requires:` prerequisite
> of `0006`, `0008`, `0009` and `0010`** — including an `accepted` `0008` that
> cannot be implemented until this one is.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v3 |
| **Status** | *see `Spec-Status:` — canonical.* Deliberately small and separable: it is a **prerequisite** of `0006`, not a part of it. |
| **Internal reviewers** | research — pending |
| **External review** | required — `store/sqlite.py` is guarded and a bad migration makes stores unopenable |
| **Review history** | *see `specs/STATUS.md`, generated from `specs/reviews.py`. No counts are stated here; a hand-maintained count drifted in `0008` and was found by the reviewer.* |
| **Decision + date** | — |
| **Path** | full |
| **Measuring instrument** | `specs/schema_signature.py` — runs today, against real files |

---

## 1. Problem and motivation

**Nothing identifies the shape of an on-disk store.**

```
$ grep -rn "user_version" src/veracium/     -> (nothing)
```

`SqliteStore.__init__` connects and unconditionally runs
`executescript(_SCHEMA)` (`sqlite.py:46`), which is `CREATE TABLE IF NOT
EXISTS`. **Any build opens any store.** A build whose `_SCHEMA` has diverged
adds its missing tables to a foreign store and proceeds, reading the rest under
assumptions that no longer hold.

`FORMAT_VERSION` (`portability.py:35`, currently `2`) guards **exports** and is
version-checked on import (`portability.py:69`). **The store itself has no
equivalent**, so the file people actually keep is the one thing with no version
on it.

**Why it has not bitten yet, stated plainly so the priority is honest:** the
schema has never changed — and in v3 that is **measured across all 23 released
versions** (§4a-iv) rather than asserted. This is a latent defect, not a live
one, **and the next schema change is `0006`**, which is why it is being fixed
now rather than alongside. Landing versioning *with* the change that needs it
means the migration mechanism gets its first exercise on the same commit that
first needs to be correct.

**If we do nothing:** `0006` bumps the store shape, an older build opens a newer
store, `CREATE TABLE IF NOT EXISTS` silently no-ops on tables it thinks it
understands, and reads return partial data with no error. **Silent
misinterpretation of persisted trust data is the worst failure mode this project
has.**

---

## 2. Field contracts touched

| field | read / written | contract | consumers |
|---|---|---|---|
| **`PRAGMA user_version`** | **NEW** — written on create/adopt/migrate, read on every open | the integer shape-id of this store file | `SqliteStore.__init__` only |
| **`SIGNATURES`** | **NEW** — a constant, one semantic signature per supported version | the shape a store must have *at* that version | open, migrate |
| `_SCHEMA` | unchanged | `CREATE TABLE IF NOT EXISTS …` | unchanged; **stops being the sole definition of shape** |
| `FORMAT_VERSION` | unchanged | export/import wire format | **explicitly independent** — see §8 |

**No trust-bearing field changes.** This spec adds no capability and touches no
provenance; it constrains *when a store may be opened at all*.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant |
|---|---|---|---|---|---|
| **`user_version` in the file** | `0` → adopt-or-create, §4 | **negative, measured** — sqlite stores `-1` and `-2147483648` verbatim | **higher than ours → REFUSE** | set to `0` to force adoption of a foreign store | **S3** shape, not counter · **S14** negative → `invalid-version` |
| **the db file** | new store | sqlite rejects | — | **anyone who can write this file already owns the process** — stated, not defended | out of scope, and named so it is not mistaken for covered |
| **a lower `user_version`** | — | — | — | downgrade to re-enter an unmigrated path, or to skip validation | **S4** gap refuses · **S15** the *source* signature is validated before any migration runs |
| **a stamped-but-wrong store** | — | — | — | stamp a foreign file `1` to bypass adoption entirely | **S16** — every version validates its signature, not only version zero |
| **concurrent first open** | — | — | — | two processes decide from stale state | **S5** — `BEGIN IMMEDIATE` *before* the read, §4c |
| **extra objects in the file** | — | — | sqlite's own `sqlite_stat1` | a foreign table, view or **trigger** beside ours | **S8** exact set · **S10** internal exclusion · **S17** an unstamped file with *any* non-internal object is not "new" |
| **a table name read from a foreign file** | — | — | — | **an identifier chosen by whoever wrote the file** | **S18** — passed as a *value* to `pragma_table_xinfo(?)`, never interpolated |
| **a column `table_info` cannot see** | — | — | **generated columns, measured** | a generated column added to `edges` | **S19** — `table_xinfo`, §4a-ii |
| **a same-named index with a different definition** | — | — | — | a **UNIQUE** index that rejects legitimate writes | **S12** — measured; `CREATE INDEX IF NOT EXISTS` does *not* correct it |

## 2c-ii. Assertions about reach

**Every row was executed on this working tree on 2026-08-02 and states the
output, not the expectation.** Rows v1 and v2 got wrong are kept struck rather
than dropped — a reach table that quietly loses its own errors is not a record.

| assertion | command | result |
|---|---|---|
| no version check exists | `grep -rn "user_version" src/veracium/ tests/` | no matches — **nothing in this spec is implemented** |
| the schema is applied unconditionally | `sed -n '45,47p' src/veracium/store/sqlite.py` | `executescript(_SCHEMA)` on every open, line 46 |
| exports *are* version-checked | `portability.py:69` | newer-than-ours rejected; `FORMAT_VERSION = 2` |
| `_SCHEMA` defines **4 tables and 3 indices** | `grep -nE "CREATE (TABLE\|INDEX)"` | `edges`, `episodes`, `wiki`, `write_counter`; `ix_edges_user_active`, `ix_edges_subj_rel`, `ix_episodes_user` |
| a fresh store reads `user_version = 0` | open a store, `PRAGMA user_version` | `0` — every existing store takes the adoption path once |
| **WITHDRAWN form: `LIKE 'sqlite\_%'` does not exclude `sqlite_stat1`** | after `ANALYZE`, run both forms | `NOT LIKE 'sqlite\_%'` → `edges, episodes, **sqlite_stat1**, wiki, write_counter`; `NOT GLOB 'sqlite_*'` → the four |
| **`table_info` omits generated columns** | add a `GENERATED ALWAYS AS … VIRTUAL` column to `edges` | `table_info` → 8 columns, **no `leak`**; `table_xinfo` → 9, `leak` with hidden flag `2` |
| **`user_version` accepts negative values** | set `-1`, `-2147483648`, `2147483648` | reads back `-1`, `-2147483648`, and **`0`** — the out-of-range value wrapped to zero, i.e. **into the adoption path** |
| **`CREATE INDEX IF NOT EXISTS` keeps a wrong same-named index** | replace `ix_edges_subj_rel` with a UNIQUE index, re-run `_SCHEMA` | unchanged: `CREATE UNIQUE INDEX ix_edges_subj_rel ON edges(user_id, subject)` |
| every read **and write** names its columns | `grep -nE "SELECT\|INSERT"` | 11 `SELECT`, **no `SELECT *`**; 4 `INSERT`, **0 positional** |
| **all 23 released versions build an identical store** | `python3 specs/schema_signature.py --releases` | **23 identical · 0 differing · 0 unbuildable** |
| ~~"`_SCHEMA` is `IF NOT EXISTS` — every table"~~ | v1 | **wrong: 7 = 4 tables + 3 indices** |
| ~~"names + declared types is the strictest option"~~ | v2 | **wrong, and the reviewer built the counterexample** — see §4a and the disposition in §11 |

---

## 3. Trust-class matrix — REQUIRED, blocking

**Not applicable — no trust class is read or written.** Recorded explicitly
rather than omitted, because the template requires it and *"not applicable"*
should be a stated finding rather than a missing section.

**The trust-relevant property is different and worth naming:** this spec
protects the *integrity of the substrate* the trust model is stored in. Every
invariant in `0002`–`0006` assumes the bytes on disk mean what this build thinks
they mean. **That assumption is currently unchecked**, which makes this a
precondition of all of them rather than a peer.

---

## 3b. Authorization and scope

**Nobody is authorised by this spec.** There is no actor, no entitlement and no
party whose authority is consulted. The decision is a pure function of two
inputs — the integer in the file and the signature of the file — and neither is
attributable to a principal.

**This is stated rather than omitted because the omission would be readable as
an oversight**, given that every neighbouring spec (`0003`, `0011`, `0012`) is
about exactly who may do what. Here the answer is: **the check is not
overridable at runtime by anyone.** A host gets one construction-time choice,
`allow_adopt` (§4b), and it can only make the check **stricter** — never weaker.
That direction matches the standing rule that **configuration may narrow, never
widen**.

---

## 4. Behaviour

`SCHEMA_VERSION = 1`, constrained to `1 … 2147483647` (**S14** — sqlite wrapped
`2147483648` to `0`, i.e. into the adoption path). `SIGNATURES` maps every
supported version to its semantic signature (§4a).

On open, exactly one of — **and the table is now total over the integers**:

| state | condition | action |
|---|---|---|
| **invalid** | `user_version < 0` | **REFUSE** `reason="invalid-version"` |
| **new** | `user_version = 0` **and the file contains no non-internal object at all** — no table, view, trigger or index | create schema, stamp `SCHEMA_VERSION` |
| **legacy** | `user_version = 0` **and the signature equals `SIGNATURES[SCHEMA_VERSION]`** | **adopt**: rebuild Veracium-owned non-unique indexes (§4a-iii), stamp, **no data change** |
| **foreign** | `user_version = 0` **and any other content** | **REFUSE** `reason="foreign-shape"` |
| **current** | `user_version = SCHEMA_VERSION` **and the signature matches** | open |
| **stamped-wrong** | `user_version = SCHEMA_VERSION` **and it does not** | **REFUSE** `reason="stamped-shape-mismatch"` |
| **older** | `0 < user_version < SCHEMA_VERSION` | validate the **source** signature, migrate, validate the **destination** signature, stamp (§4d) |
| **newer** | `user_version > SCHEMA_VERSION` | **REFUSE** `reason="newer"` — this build cannot know what it does not know |

**Two of these rows are new in v3 and both were bypasses.** *stamped-wrong*:
v2 validated shape only at version zero, so stamping a foreign file `1` skipped
validation entirely — the check the whole spec exists for. *new*: v2 said "no
veracium tables", so a database containing only `unrelated_application_data`
was "new", and Veracium would add its schema beside a foreign table and stamp
it — directly contradicting the exact-set policy in S8.

### 4a. The shape comparison — a semantic signature

**v2's `{table: {(column, declared_type)}}` is withdrawn.** The reviewer built a
database with identical table names, column names and declared types, **no
primary keys and no `NOT NULL`**, and it matched. I reproduced it: it matches.

**That database is not equivalent to ours**, and the difference is not cosmetic:

- `INSERT OR REPLACE INTO edges(id,…)` (`sqlite.py:59`) **replaces by primary
  key**. With no PK it appends, so `add_edge` on an existing id silently
  duplicates instead of replacing.
- `episodes` likewise (`sqlite.py:98`), and `wiki` (`sqlite.py:150`).
- `write_counter(user_id) PRIMARY KEY` is what makes `ON CONFLICT(user_id) DO
  UPDATE SET n = n + 1` (`sqlite.py:52`) a counter. Without it the upsert has no
  conflict target and the per-user count is wrong.
- `NOT NULL` on `json` is what lets every read call
  `Edge.model_validate_json(row[0])` without a null check.

**A shape comparison that cannot see this cannot authorise adoption.** The
signature is now:

```
per table:  flags (WITHOUT ROWID, STRICT)
            columns: (name, declared type, NOT NULL, default, pk ordinal, hidden/generated)
            unique constraints and unique indexes: (origin, columns)
            foreign keys: (table, from, to, on_update, on_delete)
per file:   triggers on non-internal tables: (name, table, normalised body)
```

Implemented in **`specs/schema_signature.py`**, which runs today. Compared with
`==`; a difference prints as a diff rather than a boolean.

**Auto-index names are deliberately excluded** — SQLite generates
`sqlite_autoindex_edges_1` and the number is not a stable property. The
*origin* (`pk` / `u` / `c`) and the *columns* are what matter.

#### 4a-i. Excluding sqlite's own tables — v2's SQL was wrong

**The v2 form below is WITHDRAWN and quoted only to show what it did.** v2
specified `name NOT LIKE 'sqlite\_%'`. **Backslash is not a `LIKE` escape in
SQLite without an explicit `ESCAPE` clause**, so the underscore stayed a
wildcard — but a wildcard matches `sqlite_stat1` too, so the exclusion silently
did nothing. Measured after `ANALYZE`:

```
# WITHDRAWN, first line only -- kept to show the failure
NOT LIKE 'sqlite\_%'              -> edges, episodes, sqlite_stat1, wiki, write_counter
NOT LIKE 'sqlite\_%' ESCAPE '\'   -> edges, episodes, wiki, write_counter
NOT GLOB 'sqlite_*'               -> edges, episodes, wiki, write_counter
```

**`GLOB` is specified**, not the escaped `LIKE`: it is case-sensitive and has no
escape ambiguity to get wrong a second time. **S10 must execute the production
query**, not an independent re-statement of the intent — v2's invariant would
have passed while the shipped SQL failed.

**A conflation worth recording:** v2's supporting text cited
`sqlite_autoindex_*` as the thing being excluded. Those are *indexes* and can
never appear in a query restricted to `type='table'`. `sqlite_stat1` is the
internal table that actually appears. The measurement was real; the explanation
attached it to the wrong object.

#### 4a-ii. `table_info` is not sufficient

**`PRAGMA table_info` omits generated columns.** Measured: adding
`leak TEXT GENERATED ALWAYS AS (subject||object) VIRTUAL` to `edges` leaves
`table_info` reporting the original 8 columns, so a foreign file carries a
column the comparison cannot see. **`table_xinfo` is specified**, which reports
it with a nonzero hidden flag, and the flag is part of the signature.

**Table names discovered in a foreign file are untrusted identifiers.** They are
passed as *values* to `pragma_table_xinfo(?)`, never interpolated into SQL text
(**S18**). This is a file the process was handed; the names in it are chosen by
whoever wrote it.

#### 4a-iii. Indexes — the v2 classification was wrong

v2 called every index a performance property. **A UNIQUE index decides which
writes are accepted**, so it is semantic and is in the signature.

Non-unique indexes stay out of the signature — but v2's reason for that was also
wrong. It claimed adoption re-applying `_SCHEMA` restores a missing index.
Measured: `CREATE INDEX IF NOT EXISTS` **silently keeps a same-named index with
a different definition**, including a UNIQUE one that changes which writes
succeed.

**So adoption does not re-apply `_SCHEMA`. It drops and recreates each
Veracium-owned non-unique index by name**, which is correct whether the index
is missing, present, or present-and-wrong. **S12 tests the wrong-definition
case**, not the missing one.

#### 4a-iv. The adoption premise, measured across every release

v2 rested adoption on *"the schema has never changed"* and offered S6, which
built a store with **today's** code, cleared the stamp and reopened it. The
reviewer rejected that correctly: it proves today's schema adopts today's
schema.

`specs/schema_signature.py --releases` does the thing that is actually
evidence. For each of the 23 released tags it creates a git worktree, **builds
a store using that release's own `SqliteStore`**, and compares the signature to
HEAD:

```
23 released tags · signature compared against HEAD
  v0.1.0 … v0.4.8   identical
23 identical · 0 differing · 0 unbuildable
```

**This is why `allow_adopt=True` is defensible as the default**, and the claim
is now bounded exactly: *every store created by a released version of veracium
has the v1 signature.* It says nothing about a store some other tool wrote —
which is what the signature check, not this evidence, is for.

**The tool fails if any release is unbuildable**, because a release that cannot
be built is a *gap in the evidence*, not a pass.

### 4b. The public contract, frozen

```python
SCHEMA_VERSION: int = 1                       # constrained to 1 … 2147483647
SIGNATURES: dict[int, Signature]              # one per supported version

class StoreVersionError(RuntimeError):
    """The store on disk is not a shape this build can open."""
    path: str            # the file we refused
    found: int           # user_version read from the file (0 = unstamped)
    expected: int        # SCHEMA_VERSION of this build
    reason: str          # closed set, below
    diff: str | None     # for shape reasons: which tables/columns differ

class SqliteStore(Store):
    def __init__(self, path: str | Path = "veracium.db", *,
                 allow_adopt: bool = True,
                 audit_sink: Callable[[dict], None] | None = None,
                 busy_timeout_ms: int = 5000) -> None: ...
```

**`reason` is a closed set** — `"invalid-version"`, `"newer"`,
`"foreign-shape"`, `"stamped-shape-mismatch"`, `"migration-gap"`,
`"migration-source-mismatch"`, `"migration-result-mismatch"`,
`"adoption-refused"`, `"locked"`. Closed because hosts will branch on it;
free-form strings are the thing `0008` round 3 was deferred over.

**`allow_adopt=False`** resolves **S-Q2**: a host that would rather refuse an
unstamped store than adopt it sets it, and gets `reason="adoption-refused"`.
Default `True`, justified by §4a-iv and not before it. **It can only narrow.**

**`diff` is populated for the three shape reasons** — a refusal a user cannot
act on becomes a bug report, and the only useful remedy is knowing which table
differs.

**`StoreVersionError` derives from `RuntimeError`**, not a veracium base class.
No such base exists; introducing one is wider than this spec.

### 4c. The transaction — lock before read

**Two things v2 got wrong here, one of them measured by me and one by the
reviewer.**

**`executescript` cannot carry the transaction.** Measured: it issues an
implicit `COMMIT` before running, so an implementation that keeps
`executescript(_SCHEMA)` and adds a stamp around it has **no transaction at
all**, and a crash between the halves leaves a stamped store with no tables.
*Independently confirmed by the reviewer, along with the fact that `PRAGMA
user_version` does roll back inside an explicit transaction.*

**But an explicit transaction is not enough: the decision must be made under
the write lock.** v2 specified the transaction and left the *read* outside it,
so two connections could both inspect version and shape, both conclude "new",
and both act on stale state. The protocol is:

```
BEGIN IMMEDIATE                  -- take the write lock FIRST
  re-read user_version
  re-read the signature
  decide from the locked state
  execute the DDL / migration    -- statement by statement, never executescript
  stamp user_version
COMMIT
```

**`BEGIN IMMEDIATE` before the read is the load-bearing word.** A deferred
transaction acquires the write lock at the first write, which is after the
decision has already been made.

**`database is locked` has defined behaviour**: `busy_timeout_ms` (default
5000), then **refuse loudly** with `reason="locked"`. Not a silent retry loop —
a store that cannot be initialised is a startup failure, and a startup failure
that manifests as a hang is worse than one that manifests as an error.

**Scope, stated rather than implied:** S5 tests **threads**. The product
boundary is a file that multiple *processes* can open, so **S20 tests processes
too**. v2 claimed first-open concurrency from an in-process thread test alone,
which the reviewer flagged; either the claim is process-wide and tested that
way, or it is not made.

### 4d. The migration registry

Gap detection alone protects against almost nothing. Each step binds:

```python
Migration = namedtuple("Migration", "from_version expected_source "
                                    "migrate to_version expected_destination")
```

**The planner validates signatures, not just version continuity:**

| check | reason | invariant |
|---|---|---|
| the chain from `found` to `SCHEMA_VERSION` is contiguous | a gap means an unwritten step | **S4** |
| the file matches `expected_source` **before** the first step | a downgraded counter, or a partly-modified source | **S15** |
| the file matches `expected_destination` **after** each step | a migration that produced only part of its target | **S21** |
| the whole chain runs in the single §4c transaction | a partial chain must not be observable | **S5** |

**A migration function must not call `commit()`, `rollback()`, or
`executescript()`, and must not otherwise change transaction state.** Any of
these silently ends the outer transaction — `executescript` measurably so
(§4c). **S22 asserts this**, because the failure is invisible until a crash.

The registry is **empty** in this change: the mechanism lands with zero
migrations, so its first real use in `0006` is not also its first execution.

### 4e. The adoption audit

v2 said adoption is "logged" and claimed the decision would otherwise be
"unauditable forever after". **A claim that strong needs a destination**, and
v2 named none — not the sink, not durability, not what a logging failure does.

**Ruled: a host-supplied sink, and the strong claim is dropped when there is
none.**

| | |
|---|---|
| **sink** | `audit_sink: Callable[[dict], None]`, §4b. Called with `{path, from_version, to_version, signature_digest, at}` |
| **when** | **inside the §4c transaction, before `COMMIT`** — so a sink that raises aborts the adoption rather than leaving an unrecorded one |
| **failure** | the exception propagates; the store does not open. **Adoption without a record is the thing this exists to prevent** |
| **no sink supplied** | adoption still proceeds and is written to the module logger at `INFO` — **and the durability claim is not made**. `allow_adopt=False` is the option for a host that needs the guarantee |
| **duplicates** | impossible: adoption happens under the write lock, and a second opener sees a stamped store |

**Not a table inside the store.** That would change the shape being adopted,
which is circular.

---

## 5. Regime analysis — where does this behave differently?

**The regime no test naturally reaches:** an *older* build opening a *newer*
store. Fixtures create fresh stores at the current version, so this path is
invisible to ordinary tests — the same reason the maintenance regimes in `0002`
needed simulated clocks. **S2 reaches it by writing `user_version` directly.**

**The migration regime cannot be reached at all yet.** With `SCHEMA_VERSION = 1`
and an empty registry there is no version to migrate from, so S4, S15, S21 and
S22 **inject a registry**. Stated because the alternative is invariants that
silently test nothing — which is how `0002` shipped four rows whose checks never
ran.

**The regime v2 did not model:** a *stamped* store whose shape is wrong. It is
unreachable by any veracium code path, which is exactly why v2 assumed it away —
and exactly why it was the bypass. Reached by stamping a hand-built file.

---

## 6. Invariants and executable checks — REQUIRED, blocking

**None of these tests exist. Nothing in this spec is implemented.**
`grep -rn "user_version" src/veracium/ tests/` returns nothing today. The names
below are the contract for what must be written, not a description of what is
there. **Stated in this form because a previous manifest listed 17 rows of which
11 cited tests that did not exist.**

**`specs/schema_signature.py` is the exception** — it exists, it runs, and
§4a-i, §4a-ii, §4a-iii and §4a-iv are measured through it today.

| invariant | executable check |
|---|---|
| **S1** a fresh store is stamped | `test_new_store_is_stamped` |
| **S2** a newer store is refused | `test_a_newer_store_is_refused` — write `SCHEMA_VERSION + 1` directly |
| **S3** adoption verifies signature, not counter | `test_a_foreign_store_at_version_zero_is_refused` |
| **S4** migrations are forward-only; a gap refuses | `test_a_missing_migration_refuses` — injected registry |
| **S5** the decision is made under the write lock | `test_first_open_locks_before_reading` — assert `BEGIN IMMEDIATE` precedes the version read |
| **S6** an existing store keeps working, no data change | `test_legacy_store_is_adopted_losslessly` — every edge/episode byte-identical after adoption |
| **S7** `FORMAT_VERSION` is untouched | `test_export_format_version_is_independent` |
| **S8** the signature is exact set equality | `test_a_store_with_extra_tables_is_refused` |
| **S9** adoption is recorded, and a failing sink aborts it | `test_adoption_audit_sink_failure_aborts` — sink raises, assert **not** stamped |
| **S10** the **production** internal-exclusion query excludes `sqlite_stat1` | `test_analyze_does_not_make_a_store_foreign` — `ANALYZE`, reopen, assert adopted. **Must call the shipped query** |
| **S11** no code depends on column order | `test_every_statement_names_its_columns` — no `SELECT *` (except aggregates), **every `INSERT` names its destination columns** |
| **S12** a wrong same-named index is corrected | `test_adoption_replaces_a_wrong_same_named_index` — replace with a UNIQUE index, adopt, assert the correct definition |
| **S13** the stamp is transactional in the installed sqlite | `test_user_version_rolls_back` |
| **S14** a negative version refuses; `SCHEMA_VERSION` is in range | `test_a_negative_user_version_is_refused` |
| **S15** the source signature is validated before migrating | `test_migration_refuses_a_mismatched_source` |
| **S16** a stamped store validates its signature | `test_a_stamped_store_with_the_wrong_shape_is_refused` |
| **S17** an unstamped file with any foreign object is not "new" | `test_a_database_with_only_an_unrelated_table_is_refused` |
| **S18** foreign table names are never interpolated | `test_a_hostile_table_name_is_passed_as_a_value` — a name containing a quote and a semicolon |
| **S19** generated columns are seen | `test_a_generated_column_makes_a_store_foreign` |
| **S20** concurrent first open across **processes** stamps once | `test_concurrent_first_open_across_processes` |
| **S21** the destination signature is validated after migrating | `test_migration_refuses_a_partial_result` |
| **S22** a migration may not alter transaction state | `test_a_migration_that_commits_is_rejected` |

**S6 is the one that protects users** and is why adoption is specified before it
is convenient: everyone who has a store today goes through that path exactly
once, silently, on upgrade.

**S11 is a lint, not a behavioural test**, and worth flagging: §4a's unordered
column comparison is a *justified* choice, not a safe one, and the
justification — every read and write names its columns — is a property of the
source that a future commit can remove without noticing.

---

## 7. Failure modes and reversibility

**Failure mode is refusal to open, which is loud, safe and reversible** by
installing the matching build. **The unacceptable failure is the current one:
opening and silently misreading.**

**The cost, stated rather than minimised:** this change can make a store that
opens today refuse to open tomorrow. Under `SCHEMA_VERSION = 1` that population
should be empty — **and §4a-iv is the evidence, across all 23 releases, rather
than the assertion v2 offered.** If that evidence is wrong, the blast radius is
"the application will not start."

**Reversibility.** Adoption writes one integer and no data, so downgrading to a
pre-0007 build works — that build ignores `user_version` entirely. The index
rebuild in §4a-iii is the one exception, and it restores the *documented*
definition. **A real migration will not be reversible**, which is why the
registry is empty here and why `0006` must specify its own down-path or declare
it one-way.

---

## 8. Claims and limits

**Claim:** a veracium build refuses to open a store it does not understand — **at
every version, not only at adoption.**

**Limits:**

- **Not integrity, not authentication.** Nothing detects tampering or
  corruption; `user_version` is advisory metadata a writer can set to anything.
  Against an adversary with write access to the file this proves nothing — **and
  that adversary already owns everything.** The signature raises the cost of a
  *mistake*, not of an attack.
- **Not multi-process migration.** S20 covers concurrent *first open* across
  processes. **Migration must be run by one process**, and `0006` must say so.
- **Not a data-format guarantee.** The JSON blobs inside the rows are validated
  by pydantic on read, unchanged by this spec.
- **Not a value-type guarantee.** The signature compares *declared* types.
  SQLite does not enforce them, so a store whose `TEXT` column holds integers
  matches.
- **Not applicable to other backends.** `base.py` is an interface; a Postgres
  store needs its own mechanism (**S-Q3**).
- **The historical evidence covers veracium's own releases only** (§4a-iv). A
  store written by another tool is exactly what the signature check is for.

---

## 9. Brief for the external reviewer

**Round 1 deferred v2 with 12 blocking findings and approved the direction.
Every one is answered in §11, and I reproduced all of them first** — the `LIKE`
escape, the constraint-stripped counterexample, the generated column hidden from
`table_info`, the negative `user_version`, and `CREATE INDEX IF NOT EXISTS`
keeping a wrong same-named index. **All five reproduce exactly as reported.**

**The two structural changes**, rather than the twelve local ones:

1. **The signature is semantic** (§4a) and lives in `specs/schema_signature.py`,
   which runs today. It catches all six counterexamples I could construct, and
   deliberately does not fire on `ANALYZE` or on a missing non-unique index.
2. **Shape is validated at every version** (§4), not only at adoption. The
   *stamped-wrong* row is new and was a complete bypass of the check the spec
   exists for.

**Where I am least confident now:**

- **§4a's completeness.** I moved from names+types to a signature covering
  flags, constraints, generated columns, unique indexes, foreign keys and
  triggers — because you named those. **I still cannot argue it is complete**,
  only that it is closed under every counterexample I can build. If there is a
  principled way to bound this, I would rather adopt it than keep extending a
  list.
- **§4e's ruling.** I dropped the "unauditable forever after" claim when no sink
  is supplied rather than mandate one, on the grounds that a library cannot
  require a host to provide durable storage. That is a judgement call and it
  weakens the audit for the default configuration.
- **§4c's `busy_timeout` then refuse.** Refusing loudly is right for a startup
  path, but 5000 ms is a guess.

**What I deliberately did not do:** no veracium exception base class; no
non-unique index comparison (dropped and recreated instead, §4a-iii); no
cross-process *migration* locking (pushed to `0006`, and now stated as a limit
rather than implied).

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~S-Q1~~ | **RULED 2026-08-01, revised 2026-08-02:** names+types **withdrawn** after round 1; the comparison is the semantic signature in §4a. | resolved | research → external | — |
| ~~S-Q2~~ | **RULED 2026-08-02: `allow_adopt: bool = True`**, §4b — and the default is now justified by §4a-iv rather than by convenience. | resolved | dev | — |
| **S-Q4** | Is there a **principled bound** on the signature, or is it a list that grows each time someone builds a counterexample? §9 names this as my least confident point. | `pre-release` | external | before implementation |
| **S-Q3** | Does anything other than `SqliteStore` need this? `base.py` is an interface; a Postgres store would need its own mechanism. **Not in scope, recorded so it is not assumed covered.** | `deferred` | dev | — |

---

## 11. Round 1 review disposition

**Verdict: design direction approved; v2 deferred.** 12 blocking findings.
**All 12 are taken.** Nothing is argued down.

| # | finding | closed by |
|---|---|---|
| 1 | `NOT LIKE 'sqlite\_%'` does not escape; `sqlite_stat1` survives | **§4a-i** — `NOT GLOB 'sqlite_*'`, both forms measured. S10 must execute the **production** query. The `sqlite_autoindex_*` conflation is corrected and recorded |
| 2 | names+types miss PK, NOT NULL, unique, generated, triggers | **§4a** — semantic signature, implemented in `specs/schema_signature.py`. I rebuilt your counterexample; it matched v2 and is now caught. §4a names the four places `sqlite.py` depends on those constraints |
| 3 | `table_info` omits generated columns; identifier interpolation | **§4a-ii** — `pragma_table_xinfo(?)`, name passed as a **value**. S19, S18 |
| 4 | "new" can augment a foreign database | **§4, row *new*** — no non-internal object *at all*. S17, with the `unrelated_application_data` fixture you specified |
| 5 | the state table is not total; negative versions | **§4, row *invalid*** — `reason="invalid-version"`; `SCHEMA_VERSION` bounded. Measured, and worse than reported: `2147483648` wraps to **`0`**, i.e. into adoption. S14 |
| 6 | shape validated only at version zero | **§4, row *stamped-wrong*** — `SIGNATURES` per version, validated on every path. S16. **This was a complete bypass** |
| 7 | the migration registry has no shape contract | **§4d** — `from/expected_source/migrate/to/expected_destination`; S15, S21, S22 |
| 8 | S6 proves today adopts today | **§4a-iv** — `--releases` builds a store with **each release's own code**: **23 identical · 0 differing · 0 unbuildable**. Unbuildable counts as a *gap*, not a pass |
| 9 | no lock-before-read; threads ≠ processes | **§4c** — `BEGIN IMMEDIATE` before the read; `busy_timeout` then `reason="locked"`. **S20 tests processes** |
| 10 | the adoption audit is undefined | **§4e** — host sink, called **inside** the transaction, failure aborts adoption; **and the durability claim is dropped when no sink is supplied** |
| 11 | column-order justification covers reads, not writes | **S11 broadened** — every `INSERT` must name its columns. Measured: 4 INSERTs, 0 positional today |
| 12 | `CREATE INDEX IF NOT EXISTS` need not restore an index | **§4a-iii** — measured: a wrong same-named UNIQUE index survives untouched. Unique indexes are **in** the signature; Veracium-owned non-unique indexes are **dropped and recreated**. S12 tests the wrong-definition case |

**On the timeout:** the full suite is ~22 s here but the spec-gate tests spawn
subprocesses. The package README already splits the manifest test out; the
`--ignore=tests/longmemeval` form is the fast one, and `-p no:randomly -x` will
fail sooner if anything is broken.
