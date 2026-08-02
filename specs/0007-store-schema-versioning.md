# Feature spec: on-disk store schema versioning

Spec-Status: in review

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v4)** — opened 2026-08-01. **Round 2 deferred v3 and answered
> S-Q4.** The answer changes the design rather than extending it: **stop trying
> to recognise semantically equivalent schemas; accept only what a known
> constructor or migration produces.** v4 also fixes the version-zero upgrade
> path, which worked only while `SCHEMA_VERSION == 1`. **It is the
> `Spec-Requires:` prerequisite of `0006`, `0008`, `0009` and `0010`** —
> including an `accepted` `0008` that cannot be implemented until this one is.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v4 |
| **Status** | *see `Spec-Status:` — canonical.* Deliberately small and separable: it is a **prerequisite** of `0006`, not a part of it. |
| **Internal reviewers** | research — pending |
| **External review** | required — `store/sqlite.py` is guarded and a bad migration makes stores unopenable |
| **Review history** | *see `specs/STATUS.md`, generated from `specs/reviews.py`. No counts are stated here; a hand-maintained count drifted in `0008` and was found by the reviewer.* |
| **Decision + date** | — |
| **Path** | full |
| **Measuring instrument** | `specs/schema_manifest.py` — runs today, against real files |
| **Generated evidence** | `specs/generated/legacy_stores.json` — 23 releases, tag + commit sha + digest, `--check` in CI |

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
| **`MANIFESTS`** | **NEW** — **generated** from the constructors, one canonical manifest per version | the exact object set a store must have *at* that version | open, migrate |
| **`LEGACY_DIGESTS`** | **NEW** — generated from `specs/generated/legacy_stores.json` | which base version an *unstamped* shape corresponds to | the version-zero path |
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
| **a stamped-but-wrong store** | — | — | — | stamp a foreign file `1` to bypass adoption entirely | **S16** — every version validates its manifest, not only version zero |
| **a schema that is *equivalent* but not identical** | — | — | **a `CHECK`, a `COLLATE`, a view, a custom-collation index** | any of the four round-2 counterexamples | **S28** — exact-match against known manifests; equivalence is **not** attempted (§4a) |
| **a migration callback** | — | — | — | `commit()` then `BEGIN IMMEDIATE` — `in_transaction` reads `True` again | **S22** — a restricted executor, so transaction control is unreachable rather than forbidden |
| **an audit sink** | — | — | — | blocks, or re-enters the same store under the write lock | **§4e** — bounded time, must not access the store; the guarantee is named `attempted` / `committed` |
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
| **all 23 released versions build an identical store** | `specs/schema_manifest.py --releases --write` | **23/23 identical · 0 unbuildable · sqlite 3.45.1**, recorded with tag + commit sha in `specs/generated/legacy_stores.json` |
| **v3's signature accepted four non-equivalent databases** | `specs/schema_manifest.py --selfcheck` | reproduced all four; the manifest catches all four. **12/12 as specified** |
| **`commit()` then `BEGIN` restores `in_transaction`** | measured | `True` — so post-hoc inspection cannot detect a broken transaction |
| **reopening `":memory:"` yields a different database** | `signature(":memory:")` on an open in-memory store | **empty manifest**, silently — not an error |
| ~~"`_SCHEMA` is `IF NOT EXISTS` — every table"~~ | v1 | **wrong: 7 = 4 tables + 3 indices** |
| ~~"names + declared types is the strictest option"~~ | v2 | **wrong, and the reviewer built the counterexample** — §11 |
| ~~"a semantic signature bounds the comparison"~~ | v3 | **wrong: four more counterexamples passed it.** The bound is known-constructor equality — §4a, §12 |

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
`2147483648` to `0`, i.e. into the adoption path). `MANIFESTS` maps every
supported version to the canonical schema manifest of that version (§4a), and
`LEGACY_DIGESTS` maps the digest of each *unstamped* historical shape to the
version it corresponds to (§4a-iv).

On open, exactly one of — **and the table is total over the integers**:

| state | condition | action |
|---|---|---|
| **invalid** | `user_version < 0` | **REFUSE** `reason="invalid-version"` |
| **new** | `user_version = 0` **and no non-internal object at all** — no table, view, trigger or index | create schema, validate the result against `MANIFESTS[SCHEMA_VERSION]` (**S25**), stamp |
| **legacy** | `user_version = 0` **and the digest is in `LEGACY_DIGESTS`** | **resolve the base version**, then take the *older* path from it — migrate, validate, stamp |
| **foreign** | `user_version = 0` **and anything else** | **REFUSE** `reason="foreign-shape"` |
| **current** | `user_version = SCHEMA_VERSION` **and the manifest matches** | repair index drift if any (§4a-iii), open |
| **stamped-wrong** | `user_version = SCHEMA_VERSION` **and it does not** | **REFUSE** `reason="stamped-shape-mismatch"` |
| **older** | `0 < user_version < SCHEMA_VERSION` | validate `MANIFESTS[found]`, migrate step by step validating each destination, stamp (§4d) |
| **newer** | `user_version > SCHEMA_VERSION` | **REFUSE** `reason="newer"` |

### 4-i. Why the *legacy* row is not simply "adopt"

**v3's legacy row adopted a store whose signature matched
`SIGNATURES[SCHEMA_VERSION]` — which works only while the current version *is*
the legacy version.** Round 2's finding 1, and it is decisive:

```
old installation:  pre-0007, user_version = 0, shape = version 1
new installation:  SCHEMA_VERSION = 2 (0006 has landed)

the user upgrades directly, skipping the versioning-only release
  presented:  user_version = 0, digest = digest of version 1
  v3 rule:    digest != SIGNATURES[2]  ->  "foreign"  ->  REFUSED
```

**A user cannot be required to install every intermediate release**, and
refusing them contradicts the reason for landing the mechanism before its first
real use. So version zero **resolves to a base version and then re-enters the
normal migration path** — adoption is a *stamping* step, not a bypass of
migration.

Under `SCHEMA_VERSION = 1` the resolved base is 1 and the chain is empty, so
today's behaviour is unchanged. **The difference appears at version 2, which is
exactly where v3 broke.** **S26** proves it by injecting `SCHEMA_VERSION = 2`
and migrating an unstamped version-1 fixture directly.

### 4a. The schema manifest — known constructors, not equivalence

**S-Q4 is answered, and the answer came from the reviewer.** v2 compared names
and declared types. v3 replaced that with a richer "semantic signature". **Both
were the same mistake in different sizes: trying to decide whether an arbitrary
third-party schema is *equivalent* to ours.**

The evidence that it was open-ended is that each round produced fresh
counterexamples that passed. Round 2 built four against v3, **and I reproduced
all four**:

| database | v3 signature | why it matters |
|---|---|---|
| `edges.active` gains `CHECK(active = 0)` | **matched** | `INSERT … active=1` fails with `CHECK constraint failed` |
| `edges.id` becomes `TEXT COLLATE NOCASE PRIMARY KEY` | **matched** | id equality changes; `INSERT OR REPLACE` replaces different rows |
| an extra persistent `VIEW` | **matched** | the instrument inventoried only tables and triggers |
| a non-unique index on a host-defined collation | **matched** | reopening without the collation makes an ordinary insert fail: `no such collation sequence: MYCOLL` |

**The last one also refutes v3's own reasoning.** v3 argued non-unique indexes
were "performance only" and therefore outside the comparison. An index using a
collation the process has not registered **stops writes from succeeding at
all.**

**The bound is not a longer list. It is a different question:**

> **A store is understood when its persistent schema is exactly what one of this
> build's known schema constructors or migrations produces.**

Veracium does not need to decide whether an arbitrary SQLite schema is
semantically equivalent to its own. That is an open-ended SQL-equivalence
problem and it is unnecessary. **The acceptance model is exact-match against
known manifests**, implemented in `specs/schema_manifest.py`:

1. Build a reference database with each supported constructor and migration.
2. Inventory **every** non-internal persistent object — tables, views, indexes,
   triggers — from `sqlite_master`.
3. Canonicalise each: the stored DDL with whitespace collapsed, plus
   `table_xinfo` column data for tables.
4. Digest the set with sha256. Compare digests exactly.
5. Exclude **only** SQLite-owned objects (`sqlite_*`).

**Exact set equality is no longer a separate rule — it falls out.** An extra
view, an unknown index, a foreign table and a trigger all change the digest, so
none of them needs to be enumerated anywhere.

**The cost, stated because it is real and it is a real loss.** A third-party
database that is genuinely equivalent but differently written is refused. **That
is an availability failure** — loud, and fixable by an explicit offline import
tool. **v3 argued that false refusals invite bypasses; round 2 answered that
this is a deployment concern, not grounds to accept schemas whose semantics have
not been proven, and that there is no runtime widening switch in this design
anyway. That is right, and v3's argument is withdrawn.**

**Canonicalisation is deliberately minimal — whitespace only.** Every
normalisation beyond that is a claim that two different texts mean the same
thing, which is the equivalence problem this design exists to stop solving.
SQLite already strips `IF NOT EXISTS` when it stores DDL, so the text is stable
across the constructor.

#### 4a-i. Excluding sqlite's own objects — v2's SQL was wrong

**The v2 form quoted here is WITHDRAWN** — it is shown to record what it did.
v2 specified `name NOT LIKE 'sqlite\_%'`. **Backslash is not a `LIKE` escape in
SQLite without an explicit `ESCAPE` clause**, so the underscore stayed a
wildcard — and a wildcard matches `sqlite_stat1`, so the exclusion silently did
nothing. Measured after `ANALYZE`:

```
# WITHDRAWN, first line only -- kept to show the failure
NOT LIKE 'sqlite\_%'              -> edges, episodes, sqlite_stat1, wiki, write_counter
NOT LIKE 'sqlite\_%' ESCAPE '\'   -> edges, episodes, wiki, write_counter
NOT GLOB 'sqlite_*'               -> edges, episodes, wiki, write_counter
```

**`GLOB` is specified** — case-sensitive, no escape ambiguity to get wrong a
second time. **S10 must execute the production query**, not a restatement of
intent: v2's invariant would have passed while the shipped SQL failed.

**A conflation worth recording:** v2's supporting text cited
`sqlite_autoindex_*` as the thing being excluded. Those are *indexes* and can
never appear in a query restricted to `type='table'`. The manifest now covers
every object type, so both are excluded by the same clause — and
`sqlite_autoindex_*` entries carry no stored DDL in any case.

#### 4a-ii. `table_info` is not sufficient

**`PRAGMA table_info` omits generated columns.** Measured: adding
`leak TEXT GENERATED ALWAYS AS (subject||object) VIRTUAL` to `edges` leaves
`table_info` reporting the original 8 columns. **`table_xinfo` is specified**,
which reports it with a nonzero hidden flag.

**Table names discovered in a foreign file are untrusted identifiers**, passed
as *values* to `pragma_table_xinfo(?)`, never interpolated (**S18**).

#### 4a-iii. Acceleration indexes — outside the digest, not ignored

Three non-unique indexes are Veracium-owned and are **the only objects outside
the digest**, because they are rebuilt from canonical definitions rather than
trusted. **v2's reason for excluding indexes was wrong twice over** — it called
them a performance property (refuted by the collation case above), and claimed
re-applying `_SCHEMA` restores a missing one. Measured: `CREATE INDEX IF NOT
EXISTS` **silently keeps a same-named index with a different definition**,
including a UNIQUE one that changes which writes succeed.

**Excluding them from the digest is not the same as ignoring them, and v3
conflated those.** A store already stamped at the current version never goes
through adoption, so nothing would rebuild its indexes — and a UNIQUE index
sharing one of these names changes accepted writes. So there are **two
dimensions**:

| | |
|---|---|
| **digest** | every object except the three named acceleration indexes |
| **drift** | a named acceleration index that is missing, or whose DDL is not byte-identical to its canonical definition |

**Drift is repaired, not refused** — dropped and recreated inside the §4c
transaction — and it is checked on **every** path, not only adoption (**S12**).
Drift being separately computable is why a clean store can open without a write.

#### 4a-iv. The adoption premise, as a durable artifact

v2 rested adoption on *"the schema has never changed"*. v3 measured it but
reported a prose count over mutable tag names, in a package with no git
metadata, so **the reviewer could not re-run it** (round 2, finding 9).

`specs/schema_manifest.py --releases --write` now emits
**`specs/generated/legacy_stores.json`**: for each release, the **tag, the
resolved commit sha, and the manifest digest**, plus the head digest and the
sqlite version. Regenerated under the corrected manifest:

```
23/23 identical to HEAD · 0 unbuildable · sqlite 3.45.1
head digest 7d6f1013ab40ee599164e395e619ccc6e624f871a7acc73660f10bb77c8236ad
```

**`--check` is a CI gate** and fails if a digest changes, a tag moves to a
different commit, a recorded tag disappears, or a new release is missing from
the artifact. **A tag is a mutable name; recording where it pointed is half the
evidence.**

`LEGACY_DIGESTS` is **generated from this artifact**, not transcribed: today
every release maps to base version 1.

**This is why `allow_adopt=True` is defensible as a default**, and the claim is
bounded exactly: *every store created by a released version of veracium has the
v1 manifest.* It says nothing about a store some other tool wrote — which is
what the manifest check, not this evidence, is for.

**An unbuildable release fails the tool**, because it is a gap in the evidence
rather than a pass.

### 4b. The public contract, frozen

```python
SCHEMA_VERSION: int = 1                        # constrained to 1 … 2147483647
MANIFESTS: dict[int, Manifest]                 # generated, one per version
LEGACY_DIGESTS: dict[str, int]                 # unstamped digest -> base version

class StoreVersionError(RuntimeError):
    # The store on disk is not a shape this build can open.
    path: str            # the file we refused
    found: int           # user_version read from the file (0 = unstamped)
    expected: int        # SCHEMA_VERSION of this build
    reason: str          # closed set, below
    diff: str | None     # for shape reasons: which objects differ

class SqliteStore(Store):
    def __init__(self, path: str | Path = "veracium.db", *,
                 allow_adopt: bool = True,
                 audit_sink: Callable[[dict], None] | None = None,
                 busy_timeout_ms: int = 5000) -> None: ...
```

**`reason` is a closed set** — `"invalid-version"`, `"newer"`,
`"foreign-shape"`, `"stamped-shape-mismatch"`, `"migration-gap"`,
`"migration-source-mismatch"`, `"migration-result-mismatch"`,
`"adoption-refused"`, `"locked"`. Closed because hosts will branch on it.

**`allow_adopt=False`** resolves **S-Q2**; default `True`, justified by §4a-iv
and not before it. **It can only narrow.**

**`diff` is populated for the shape reasons** — a refusal a user cannot act on
becomes a bug report.

### 4c. The transaction — lock before read, on the live connection

**`executescript` cannot carry the transaction.** Measured: it issues an
implicit `COMMIT` before running, so an implementation that keeps
`executescript(_SCHEMA)` and adds a stamp around it has **no transaction at
all**. *Independently confirmed by the reviewer, along with `PRAGMA
user_version` rolling back inside an explicit transaction.*

**The decision must be made under the write lock:**

```
BEGIN IMMEDIATE                  -- take the write lock FIRST
  re-read user_version
  re-read the manifest           -- on THIS connection, see below
  decide from the locked state
  execute the DDL / migration    -- statement by statement, never executescript
  repair index drift if any
  stamp user_version
COMMIT
```

**`BEGIN IMMEDIATE` before the read is the load-bearing word.** A deferred
transaction takes the write lock at the first write, which is after the decision.

**The manifest is computed on the already-open, already-locked connection —
never by reopening the path.** v3's instrument reopened `self._path` read-only,
which is wrong twice over: `SqliteStore(":memory:")` is a supported constructor
today, and reopening `":memory:"` yields **a different, empty database** —
measured, and the instrument returned an empty manifest rather than failing.
Reopening any path also inspects a database the lock does not cover. **S27**
covers an in-memory store end to end. Paths are never reconstructed into a
`file:` URI.

**`database is locked` has defined behaviour**: `busy_timeout_ms` (default
5000), then **refuse loudly** with `reason="locked"`. A startup failure that
manifests as a hang is worse than one that manifests as an error.

**Scope:** S5 tests threads; **S20 tests processes**, because the product
boundary is a file multiple processes can open.

### 4d. The migration registry — one source of truth

Round 2, finding 5: v3 embedded expected source and destination signatures *in
each migration*, duplicating what `MANIFESTS` already declares, so the two could
disagree. **The migration type is smaller and the planner reads shapes only from
`MANIFESTS`:**

```python
Migration = namedtuple("Migration", "from_version migrate to_version")
```

| check | reason | invariant |
|---|---|---|
| the chain from `found` to `SCHEMA_VERSION` is contiguous | a gap means an unwritten step | **S4** |
| the file matches `MANIFESTS[found]` **before** the first step | a downgraded counter, or a partly-modified source | **S15** |
| the file matches `MANIFESTS[step.to_version]` **after each** step | a migration that produced only part of its target | **S21** |
| the schema constructor's own output equals `MANIFESTS[SCHEMA_VERSION]` | `_SCHEMA` changed and nobody regenerated | **S23** |
| every migration's versions are adjacent keys of `MANIFESTS` | a step pointing at a version that does not exist | **S24** |
| creation and adoption validate the destination **before** stamping | stamping a shape that was never checked | **S25** |
| the whole chain runs in the single §4c transaction | a partial chain must not be observable | **S5** |

**`MANIFESTS` is generated from the constructors, not transcribed.** S23 is what
makes that true rather than aspirational: a contributor who edits `_SCHEMA`
without regenerating fails the build instead of stamping a store whose real
shape is not the shape declared for its version.

**Migration callbacks do not get a `sqlite3.Connection`.** v3 forbade
`commit()`, `rollback()` and `executescript()`, and proposed detecting a direct
`commit()`. Round 2's finding 7 is right that this is not enough:

```python
conn.commit(); conn.execute("BEGIN IMMEDIATE")   # in_transaction is True again
```

Measured: `in_transaction` reads `True` after that pair, **and atomicity is
already gone.** Post-hoc inspection cannot detect it. So a migration receives a
**restricted executor** that accepts individual migration statements and rejects
transaction control — `commit`, `rollback`, `executescript` and `BEGIN` /
`COMMIT` / `ROLLBACK` / `SAVEPOINT` in statement text are **not reachable**
rather than forbidden. **Atomicity is enforced by construction.** S22 covers all
five evasions.

### 4e. The adoption audit — what a callback can honestly prove

v3 called the sink inside the transaction before `COMMIT` and claimed that made
adoption and audit atomic. **It does not.** Round 2, finding 8: it prevents
*adopted-but-unrecorded* and creates *recorded-but-not-adopted*, because the
commit can still fail afterwards. A plain Python callback is outside SQLite's
transaction and cannot participate in it.

**So the events are named for what they can prove:**

| event | when | proves |
|---|---|---|
| `adoption_attempted` | inside the transaction, before `COMMIT` | the decision was made; **a sink that raises aborts adoption** |
| `adoption_committed` | after a successful `COMMIT` | the database change is durable |

**A host that needs a truly atomic audit needs a two-phase sink, or a record
participating in the same database transaction. This design provides neither,
and says so** rather than implying otherwise. **`allow_adopt=False` is the
option for a host that cannot accept that.**

**Sink contract:** a **versioned, closed event schema**; **must not access the
same store** — it is called under the write lock, so re-entering deadlocks;
**bounded execution time**; **cannot modify the decision**. Where no sink is
supplied, adoption is written to the module logger at `INFO` and **the
durability claim is not made**.

**Not a table inside the store** — that would change the shape being adopted,
which is circular.

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

**`specs/schema_manifest.py` is the exception** — it exists, it runs, and every
measurement in §4a is made through it today. `specs/generated/legacy_stores.json`
is generated by it and gated by `--check`.

| invariant | executable check |
|---|---|
| **S1** a fresh store is stamped | `test_new_store_is_stamped` |
| **S2** a newer store is refused | `test_a_newer_store_is_refused` — write `SCHEMA_VERSION + 1` directly |
| **S3** adoption verifies signature, not counter | `test_a_foreign_store_at_version_zero_is_refused` |
| **S4** migrations are forward-only; a gap refuses | `test_a_missing_migration_refuses` — injected registry |
| **S5** the decision is made under the write lock | `test_first_open_locks_before_reading` — assert `BEGIN IMMEDIATE` precedes the version read |
| **S6** an existing store keeps working, no data change | `test_legacy_store_is_adopted_losslessly` — every edge/episode byte-identical after adoption |
| **S7** `FORMAT_VERSION` is untouched | `test_export_format_version_is_independent` |
| **S8** exact set equality (falls out of the digest) | `test_a_store_with_extra_tables_is_refused` |
| **S9** adoption is recorded, and a failing sink aborts it | `test_adoption_audit_sink_failure_aborts` — sink raises, assert **not** stamped |
| **S10** the **production** internal-exclusion query excludes `sqlite_stat1` | `test_analyze_does_not_make_a_store_foreign` — `ANALYZE`, reopen, assert adopted. **Must call the shipped query** |
| **S11** no code depends on column order | `test_every_statement_names_its_columns` — no `SELECT *` (except aggregates), **every `INSERT` names its destination columns** |
| **S12** index drift is repaired on **every** path | `test_drifted_acceleration_index_is_rebuilt` — replace with a UNIQUE index on an already-**stamped** store, reopen, assert the canonical definition |
| **S13** the stamp is transactional in the installed sqlite | `test_user_version_rolls_back` |
| **S14** a negative version refuses; `SCHEMA_VERSION` is in range | `test_a_negative_user_version_is_refused` |
| **S15** the source signature is validated before migrating | `test_migration_refuses_a_mismatched_source` |
| **S16** a stamped store validates its manifest | `test_a_stamped_store_with_the_wrong_shape_is_refused` |
| **S17** an unstamped file with any foreign object is not "new" | `test_a_database_with_only_an_unrelated_table_is_refused` |
| **S18** foreign table names are never interpolated | `test_a_hostile_table_name_is_passed_as_a_value` — a name containing a quote and a semicolon |
| **S19** generated columns are seen | `test_a_generated_column_makes_a_store_foreign` |
| **S23** the constructor's output **is** `MANIFESTS[SCHEMA_VERSION]` | `test_schema_constructor_matches_its_declared_manifest` — edit `_SCHEMA` without regenerating and the build fails |
| **S24** every migration names adjacent existing `MANIFESTS` keys | `test_migration_versions_are_adjacent_and_known` |
| **S25** creation and adoption validate **before** stamping | `test_creation_validates_before_stamping` |
| **S26** an unstamped v1 store migrates **directly** to v2 | `test_legacy_store_upgrades_across_a_skipped_release` — inject `SCHEMA_VERSION = 2`; **the case v3 refused** |
| **S27** an in-memory store works end to end | `test_in_memory_store_is_versioned` — create, stamp, use; manifest read from the live connection |
| **S28** the four round-2 counterexamples are refused | `test_equivalent_but_not_identical_schemas_are_refused` — CHECK, COLLATE, VIEW, custom-collation index |
| **S29** the historical artifact is current | `specs/schema_manifest.py --check` in CI |
| **S20** concurrent first open across **processes** stamps once | `test_concurrent_first_open_across_processes` |
| **S21** the destination signature is validated after migrating | `test_migration_refuses_a_partial_result` |
| **S22** a migration **cannot reach** transaction control | `test_migration_executor_rejects_transaction_control` — direct `commit`; `commit` then `BEGIN`; `rollback` then `BEGIN`; `executescript`; `BEGIN` in statement text. **Five evasions, one restricted executor** |

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

**Reversibility, and the limit that cannot be fixed here.** Adoption writes one
integer and no data, so downgrading to a pre-0007 build works — that build
ignores `user_version` entirely.

**That is also the hole.** A build released before 0007 has no version check: it
ignores the stamp, applies `CREATE TABLE IF NOT EXISTS`, and opens the file.
**No value stored inside the database can make code that never reads that value
refuse to open it.** Once `0006` or another schema-changing feature lands,
downgrading to an already-released binary recreates the original failure mode.

**This is unavoidable when retrofitting versioning after releases exist**, and
§8 narrows the claim accordingly rather than implying protection that does not
exist. **A declaration that a migration is "one-way" is not a fence.** The first
schema-changing release must therefore carry an operational downgrade contract:
a pre-migration backup, no downgrade to a pre-0007 binary, installer fencing
where the packaging supports it, loud release documentation, and a recovery path
from the backup. **`0006` owns that contract**; this spec's job is to say the
guarantee stops here.

---

## 8. Claims and limits

**Claim, narrowed in v4:** **every *version-aware* build — that is, every
release from the one implementing 0007 onward — refuses to open a store it does
not understand**, at every version and not only at adoption.

**The narrowing is not cosmetic.** v3 claimed "a veracium build refuses…", which
is false of the 23 builds already released: none of them reads `user_version` at
all. The claim can only ever cover code that performs the check.

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
- **No protection against a pre-0007 downgrade** (§7). Those binaries exist and
  ignore the stamp. Operational fencing is the only remedy and it belongs to the
  first schema-changing release.
- **Not equivalence.** A genuinely equivalent third-party schema written
  differently is **refused** (§4a). That is a deliberate trade of availability
  for the guarantee, and an offline import tool is the right place to accept
  such a database.
- **The audit is not transactional with an external sink** (§4e). The events are
  `adoption_attempted` and `adoption_committed`, and neither is a two-phase
  commit.
- **The historical evidence covers veracium's own releases only** (§4a-iv). A
  store written by another tool is exactly what the signature check is for.

---

## 9. Brief for the external reviewer

**Round 2 deferred v3 with 10 blocking findings and answered S-Q4. All 10 are
taken. I reproduced every measurable one first**, and one of them twice — my
first attempt at the `CHECK` and `COLLATE` counterexamples was a hand-written
near-copy that differed in some *other* way, so it was caught for the wrong
reason and I nearly reported a real finding as unconfirmed. Rebuilding them by
changing exactly one thing in `_SCHEMA` reproduced both. **`--selfcheck` now
derives them that way so the mistake cannot recur.**

**The two structural changes**, rather than the ten local ones:

1. **S-Q4's answer replaced the design, not extended it** (§4a). v2 compared
   names and types; v3 compared a "semantic signature"; both were attempts to
   decide equivalence, and each round produced new counterexamples that passed.
   **The manifest compares exact known-constructor output.** Exact set equality
   stops being a rule and becomes a consequence.
2. **The version-zero path resolves a base version and re-enters migration**
   (§4-i). v3's adoption worked only while `SCHEMA_VERSION == 1`; a user
   skipping the versioning-only release would have been refused as *foreign*.

**Where I am least confident now:**

- **`REBUILDABLE` is a hand-maintained list of three index names** (§4a-iii). It
  is the one place the design still says "these objects are special" by
  enumeration. It should be derived from the constructor, and I have not found a
  clean way to do that without re-introducing a parse of the DDL.
- **§4d's restricted executor** removes transaction control by construction,
  which is right, but I have specified the *policy* rather than the mechanism.
  A statement-text check for `BEGIN` is a blacklist, and blacklists are what
  §4a just abandoned.
- **§4e still leaves a real gap.** `adoption_attempted` / `adoption_committed` is
  honest, but a host wanting a genuine atomic audit gets `allow_adopt=False` and
  nothing else.

**What I deliberately did not do:** no offline import tool (named as the right
home for equivalent-but-different databases, not built); no cross-process
*migration* locking (pushed to `0006` and stated as a limit); no veracium
exception base class.

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~S-Q1~~ | **RULED 2026-08-01, revised 2026-08-02:** names+types **withdrawn** after round 1; the comparison is the semantic signature in §4a. | resolved | research → external | — |
| ~~S-Q2~~ | **RULED 2026-08-02: `allow_adopt: bool = True`**, §4b — and the default is now justified by §4a-iv rather than by convenience. | resolved | dev | — |
| ~~S-Q4~~ | **ANSWERED by round 2, 2026-08-02: known-constructor equality, not semantic equivalence.** It was a list that grew — v3's signature admitted four more counterexamples. §4a. | resolved | external | — |
| **S-Q5** | `REBUILDABLE` (§4a-iii) is three index names maintained by hand — the last place the design privileges objects by enumeration. Can it be derived from the constructor without re-parsing DDL? | `pre-release` | dev | before implementation |
| **S-Q3** | Does anything other than `SqliteStore` need this? `base.py` is an interface; a Postgres store would need its own mechanism. **Not in scope, recorded so it is not assumed covered.** | `deferred` | dev | — |

---

## 11. Round 1 review disposition

**Verdict: design direction approved; v2 deferred.** 12 blocking findings.
**All 12 are taken.** Nothing is argued down.

| # | finding | closed by |
|---|---|---|
| 1 | `NOT LIKE 'sqlite\_%'` does not escape; `sqlite_stat1` survives | **§4a-i** — `NOT GLOB 'sqlite_*'`, both forms measured. S10 must execute the **production** query. The `sqlite_autoindex_*` conflation is corrected and recorded |
| 2 | names+types miss PK, NOT NULL, unique, generated, triggers | **§4a** — semantic signature, implemented in `specs/schema_manifest.py`. I rebuilt your counterexample; it matched v2 and is now caught. §4a names the four places `sqlite.py` depends on those constraints |
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

---

## 12. Round 2 review disposition

**Verdict: direction approved; v3 deferred.** 10 blocking findings. **All 10
taken.** Two changed the design rather than the document.

| # | finding | closed by |
|---|---|---|
| 1 | version-zero adoption breaks once `SCHEMA_VERSION > 1` | **§4-i** — version zero resolves a base version from `LEGACY_DIGESTS` and re-enters the migration path. **S26** injects `SCHEMA_VERSION = 2` and migrates an unstamped v1 store directly |
| 2 | the semantic signature has material false negatives | **§4a** — all four reproduced (`CHECK`, `COLLATE NOCASE`, `VIEW`, custom-collation index) and all four now refused. The collation case also refutes v3's "indexes are performance only" |
| 3 | the bound is known-constructor equivalence | **Adopted wholesale, and it is the better design.** §4a compares exact manifests; equivalence is not attempted. **v3's "false refusals invite bypasses" argument is withdrawn** — availability failure is loud, silent misinterpretation is not |
| 4 | object inventory and instrument disagree | **One inventory**, `sqlite_master` with `NOT GLOB 'sqlite_*'`, covering tables, views, indexes and triggers, used on every path. The extra `VIEW` passed v3 precisely because the instrument inventoried only tables and triggers |
| 5 | `SIGNATURES`, `_SCHEMA` and migrations can drift | **§4d** — `Migration(from_version, migrate, to_version)`; the planner reads shapes **only** from `MANIFESTS`, which is generated. **S23, S24, S25** |
| 6 | pre-0007 downgrades cannot be prevented | **§8 claim narrowed to *version-aware builds*, and §7 carries the operational contract.** v3's claim was false of all 23 released builds |
| 7 | migration callbacks are not transaction-contained | **§4d** — measured: `commit()` then `BEGIN IMMEDIATE` restores `in_transaction`, so inspection cannot detect it. A **restricted executor** makes transaction control unreachable. S22 covers five evasions |
| 8 | the audit cannot be atomic with an external callback | **§4e** — `adoption_attempted` / `adoption_committed`, sink contract stated, and **the atomicity claim withdrawn** rather than restated |
| 9 | the historical evidence is not durable | **§4a-iv** — `specs/generated/legacy_stores.json`: tag, **resolved commit sha**, digest, head digest, sqlite version. `--check` gates it in CI. Regenerated under the corrected manifest: **23/23** |
| 10 | in-memory stores and path reopening | **§4c** — the manifest is computed on the live, locked connection. Measured: reopening `":memory:"` returned an **empty manifest silently**. S27 |

**On the stall at `test_every_guarded_surface_actually_trips_the_gate`:** that
test shells out to `git` per guarded file in a temporary clone. The package
README now runs it in its own invocation with a timeout, and names it.
