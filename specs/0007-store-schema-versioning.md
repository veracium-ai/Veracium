# Feature spec: on-disk store schema versioning

Spec-Status: in review

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v7)** — opened 2026-08-01. **Round 5 approved the architecture a
> fourth time, deferred again, and answered a question I had asked: the
> instrument should be smaller.** v7 splits it into a `schema_model` kernel,
> declarative migrations, and evidence generation, and **moves every adversarial
> counterexample into the real test suite**. It also **withdraws the migration
> containment claim** — name mangling is not access control — replaces it with
> migrations that carry no connection at all, and derives the SQLite gate from
> an evidence artifact instead of a hand-edited tuple. **It is the
> `Spec-Requires:` prerequisite of `0006`, `0008`, `0009` and `0010`.**

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v7 |
| **Status** | *see `Spec-Status:` — canonical.* Deliberately small and separable: it is a **prerequisite** of `0006`, not a part of it. |
| **Internal reviewers** | research — pending |
| **External review** | required — `store/sqlite.py` is guarded and a bad migration makes stores unopenable |
| **Review history** | *see `specs/STATUS.md`, generated from `specs/reviews.py`. No counts are stated here; a hand-maintained count drifted in `0008` and was found by the reviewer.* |
| **Decision + date** | — |
| **Path** | full |
| **Measuring instrument** | `specs/schema_model.py` (kernel) · `schema_migrations.py` · `schema_evidence.py`; every counterexample lives in `tests/test_schema_model.py` and is counted by collection |
| **Generated evidence** | `legacy_stores.json` (per-release stamp + resolved version) · `schema_versions.json` (immutable manifests per version) · `schema_policy.json` (reviewed policies) · `sqlite_runtimes.json` (qualified runtimes), all gated by `schema_evidence.py --check` |

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
| **`MANIFESTS`** | **NEW** — **generated** by executing each constructor and every declared migration path | the **closed set** of object sets accepted *at* that version | open, migrate |
| **`LEGACY_BASE_VERSIONS`** | **NEW** — `frozenset[int]`, generated from release evidence | the **only** candidate versions the version-zero path may try | the version-zero path |
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
| **a migration** | — | — | — | v5's callback recovered the connection via `_MigrationExecutor__conn` | **S22/S43** — migrations are **declarative statement tuples**; there is no connection-bearing object to escape through (§4d) |
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
supported version to the **set** of manifests accepted at that version (§4a-v),
and
`LEGACY_BASE_VERSIONS` is the set of versions whose release evidence shows a
genuinely **unstamped** store (§4a-iv) — and the *only* candidates version-zero
resolution may try.

On open, exactly one of — **and the table is total over the integers**:

| state | condition | action |
|---|---|---|
| **invalid** | `user_version < 0` | **REFUSE** `reason="invalid-version"` |
| **new** | `user_version = 0` **and no non-internal object at all** — no table, view, trigger or index | create schema, validate the result against `MANIFESTS[SCHEMA_VERSION]` (**S25**), stamp |
| **legacy** | `user_version = 0` **and the manifest matches exactly one version in `LEGACY_BASE_VERSIONS`** (§4a-vii) | **resolve that base version**, then take the *older* path from it — migrate, validate, stamp |
| **foreign** | `user_version = 0` **and anything else** | **REFUSE** `reason="foreign-shape"` |
| **unsupported runtime** | this runtime is not qualified by `sqlite_runtimes.json` (§4a-viii) | **REFUSE** `reason="unsupported-sqlite"` — checked **before** any of the rows below |
| **current** | `user_version = SCHEMA_VERSION` **and the manifest is in `MANIFESTS[SCHEMA_VERSION]`** | repair index drift if any (§4a-iii), **revalidate**, open |
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
3. Record each **by typed identity `(type, name)`**, with the stored DDL
   **byte-for-byte** and `table_xinfo` column data for tables.
4. Digest the set with sha256, and compare against the **closed set of manifests
   accepted at that version** (§4a-v).
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

**There is no canonicalisation at all, and v4's was actively unsafe.** *(The v4
form quoted in this paragraph is WITHDRAWN.)* v4
collapsed whitespace with `" ".join(sql.split())`, described as a
whitespace-only transformation. **It is not one in SQL: it rewrites the inside
of quoted string literals.** Round 3 built two schemas differing only in

```sql
CHECK(object <> 'a  b')      vs      CHECK(object <> 'a b')
```

**identical digests, exactly opposite accept/reject behaviour.** Reproduced:
each schema rejects the value the other accepts. For an exact-known-output
design the safe normalisation is **none**, so the stored DDL is kept
byte-for-byte. SQLite strips `IF NOT EXISTS` itself and preserves the rest
verbatim, so the constructor's output is stable without help.

#### 4a-0. Objects are identified by `(type, name)`, never by name

**SQLite lets a trigger and an index share a name**, and v4 keyed its manifest
by name alone. Round 3's finding 3, reproduced exactly:

```
CREATE TRIGGER ix_edges_subj_rel AFTER INSERT ON edges
  BEGIN UPDATE edges SET active=0 WHERE id=NEW.id; END

sqlite_master now holds:  index ix_edges_subj_rel   +   trigger ix_edges_subj_rel
v4 result:  digest == clean-store digest      <- an arbitrary trigger, invisible
            drift  == ['ix_edges_subj_rel']
```

The trigger overwrote the index in the dictionary, and the digest then skipped
the key because the **name** was on the exclusion list. **A store carrying an
arbitrary trigger digested identical to a clean store** — a total bypass of the
guarantee, produced by exactly the kind of name-keyed exception §4a claims to
have abolished.

**Only `("index", <canonical name>)` may be excluded or repaired.** A trigger,
view or table sharing that name is an unknown object and refuses. And because
drift is now typed, the same-named trigger is **a digest failure rather than
index drift** — v4 would have sent an implementation off to repair an index
that was never broken.

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

**Drift is keyed by `(type, name)`** (§4a-0), so a repair can only ever drop an
*index*. **And after any repair the complete manifest is recomputed and both
conditions must hold — digest accepted *and* drift empty — before the store is
stamped or opened** (**S33**). Repairing and then trusting the pre-repair
reading is how a same-named trigger would have survived: v4 reported it *as*
index drift, so an implementation would have dropped and recreated the index,
recomputed nothing, and opened a store with an unknown trigger in it.

#### 4a-iv. The adoption premise, as version-aware durable evidence

v2 rested adoption on *"the schema has never changed"*. v3 measured it but
reported a prose count over mutable tag names. **v4 made it durable and made it
brittle**: it required every release to equal HEAD, so `--releases` would fail
and `--check` would demand an impossible regeneration **the moment the schema
changed** — the exact event this spec exists to enable (round 3, finding 4).

**A release now resolves to a known schema version. Differing from HEAD is
expected; matching no known manifest is the failure.**

```
23/23 resolve to a known schema version · 0 unbuildable · sqlite 3.45.1
HEAD resolves to schema v1
```

Two generated artifacts, both checked in:

| artifact | contents |
|---|---|
| `specs/generated/legacy_stores.json` | per release: tag, **resolved commit sha**, digest, `store_schema_version`, **`on_disk_user_version`**; plus the legacy base versions and the tested SQLite set |
| `specs/generated/schema_versions.json` | per version: the **full canonical object records**, the accepted digests, and provenance |

**The second exists because a digest is not enough** (round 3, finding 5). Once
`_SCHEMA` moves to version 2 the current constructor can no longer produce
version 1, migrations do not reconstruct the old constructor, and the
object-level `diff` §4b promises has nothing to diff against. **Old version
entries are immutable**; CI regenerates only the current constructor's entry.

**Only genuinely unstamped stores are legacy candidates.** v5 derived the legacy
set from every release's *resolved shape*, with no record of what was actually
in the file header (round 4, finding 4). Once post-0007 releases exist they will
write valid stamps, and their shapes would have been reinterpreted as legacy
candidates. Each release row now records `on_disk_user_version`; **only rows
reading `0` feed the legacy set**, and a version-aware release whose stamp
disagrees with its shape is an error rather than a data point.

**Every field is classified, and the classification is the fix.** v6 said the
gate re-derived everything; an artifact with `head_digest="BAD"`,
`head_schema_version=999`, `legacy_base_versions=[999]`, `sqlite_version="0.0.0"`
and every release `result="fabricated"` passed with **rc 0** (round 5, finding 4,
measured). The rule now is: **a field kept as evidence must be checked; a field
that cannot be checked must not be kept as evidence.**

| class | fields | treatment |
|---|---|---|
| **authoritative** | `tag`, `commit`, `on_disk_user_version`, `store_schema_version`, `digest`, `result` | re-derived per release and compared |
| **summary** | `legacy_base_versions`, `head_digest`, `head_schema_version` | **recomputed** from the authoritative fields |
| **structural** | `manifest_algorithm`, the policy artifact, the runtime artifact | compared against what this build generates |

`sqlite_version` is gone from the release artifact: it was informational, it was
never checked, and the runtime artifact now carries the qualified identity
properly.

**Deleting a historical version is an error too.** v6 detected a *changed*
historical entry but iterated only the versions currently declared, so running
the generator with version 1 dropped from the registry emitted an artifact
without it — silently (round 5, finding 5, measured). Generation is also bound
to a **declared `SCHEMA_VERSION`** rather than `max(SCHEMAS)`, so adding or
removing a registry entry can no longer change which version gets mutable
treatment.

**The gate re-derives every authoritative field.** v5's `--check` verified only
that a digest resolved to *some* version; a synthetic artifact claiming
`store_schema_version: 999` for all 23 releases passed with **rc 0**. That number
selects the migration base for unstamped stores, so an unchecked one is a live
wrong answer.

**Historical manifests are immutable, and now actually are.** v5 said so and its
generator looped over every version replacing each constructor record —
measured, `old_v1_preserved? False`. Regenerating a version below the current
one and getting a different answer is now an **error**, not a silent rewrite; a
manifest-algorithm change needs a separately reviewed artifact migration.

**Digest → version inversion must be unambiguous.** If two versions ever declare
the same persistent shape, the resolver returns *nothing* rather than guessing,
and §4-i needs an explicit rule. **S34** simulates a version 2 and proves a
version-1 store still resolves while HEAD resolves to 2 — the case v4's gate
could not express.

**This bounds `allow_adopt=True`:** *every store created by a released version
of veracium resolves to a known schema version.* It says nothing about a store
another tool wrote.

**An unbuildable release fails the tool**, because it is a gap in the evidence
rather than a pass.

#### 4a-v. A version accepts a **set** of manifests, not one

**v4 promised known-constructor-*or-migration* acceptance and implemented
known-constructor-only.** Round 3's finding 1, and it rejects an ordinary
correct migration. Measured on the likeliest first one:

```sql
ALTER TABLE edges ADD COLUMN source_id TEXT
```

against a fresh constructor whose `edges` carries the same final column.
`table_xinfo` is identical; the stored DDL is not:

```
fresh constructor:  ... json TEXT NOT NULL, source_id TEXT )
ALTER TABLE:        ... json TEXT NOT NULL , source_id TEXT)
```

**Different digests. The migration is structurally correct and destination
validation fails.**

**Ruled: the multiple-known-output model.**

```python
MANIFESTS: dict[int, frozenset[Manifest]]     # constructor + every migration path
```

The alternative — requiring every migration to rebuild affected tables so its
output is byte-identical to a fresh constructor — was rejected: SQLite's
table-rebuild procedure is twelve steps, and making every future migration
perform one to satisfy a *comparison* puts the risk in the wrong place. **The
accepted set is generated, closed, and recorded** in
`specs/generated/schema_versions.json`. Version 1 has exactly one member today
because there are no migrations.

**The cost, stated:** the set must be regenerated whenever a migration path is
added, and a path nobody generated is a refusal. That is the intended direction
— a shape this build cannot *name* is not a shape it should open.

#### 4a-vi. The schema is a structured registry — S-Q5 resolved

**S-Q5 is resolved, and round 3's finding 8 is the answer.** v4's `REBUILDABLE`
was three bare index names — the last place the design privileged objects by
enumeration, and the thing that made §4a-0's bypass possible.

The schema is declared once, as data:

```python
SchemaObject(kind="index", name="ix_edges_subj_rel",
             ddl="CREATE INDEX ...", policy=REBUILDABLE)
```

One registry generates the creation statements, the manifest expectation, the
typed rebuildable identities, the repair statements and the drift check.
**`--selfcheck` proves the registry reproduces `_SCHEMA`'s database exactly**
rather than assuming it — **S23**, executable today.

**Policies are compared against an independently reviewed artifact, not against
the registry itself.** v6's check computed the expected rebuildable set *from
the same registry it was checking*, so it was tautological: flipping
`ix_edges_subj_rel` from `REBUILDABLE` to `REQUIRED` left conformance empty
(round 5, finding 2, measured). **A policy is not a comment** — it decides
whether an object is excluded from the acceptance digest, whether drift is
repaired or refused, and how candidate matching behaves. It cannot be
self-certifying. `specs/generated/schema_policy.json` is that second
declaration, and changing it is a reviewable diff.

**The honest end state is that the product schema is generated from this
registry**, at which point there is no second declaration to compare and the
artifact can go. That belongs to implementation, and until then the duplication
is real and is stated rather than glossed.

**And S23 compares complete typed records, not the acceptance digest.** v5's did
use the digest, **which excludes every rebuildable index**, so it passed while
the registry declared `CREATE UNIQUE INDEX ix_edges_subj_rel ON edges(user_id)`
— a materially different index the registry would have instructed an
implementation to install. Measured: `digest_equal True`, `drift []`. **A
conformance check may not use the check that deliberately looks away.** The
acceptance digest may exclude repairable indexes; the registry comparison covers
every object, its policy, and drift.

**I do not claim this removes every hand-maintained fact**; it removes the
duplicated one. The DDL text still lives in two places — `_SCHEMA` in the
product and the registry in `specs/` — and the check that they agree is what
makes that safe, until the product itself is built from the registry.

#### 4a-vii. Resolving an unstamped store — candidates, not a default

**The digest of a store is not its identity, and v5 treated it as one.** Which
objects the digest excludes depends on that version's rebuildable policy — and
resolving an unstamped store means not knowing the version yet. Round 4,
finding 3, measured on a simulated version 2 carrying its own rebuildable index:

```
digest of a v2 store under v1's policy:  4b250945…   -> resolves to NOTHING
digest of a v2 store under v2's policy:  754ec416…   -> resolves to 2
```

v5's release probe computed the digest with the **default** version 1 and then
asked which version it was: *need the version to compute the digest, need the
digest to find the version.* It worked only because one version exists.

**Ruled: candidate matching.** The typed inventory is taken **once**, and each
permitted candidate version applies **its own** rebuildable policy to it:

```
raw = every typed object, nothing excluded
for each candidate version v:
    if digest(raw, policy of v) ∈ MANIFESTS[v]:  v is a match
accept only a UNIQUE match
```

**More than one match resolves to nothing**, not to a guess — if two versions
ever declare the same persistent shape, §4-i needs an explicit rule.

#### 4a-viii. The SQLite runtime — qualified by evidence, not by a tuple

**S-Q6's answer stands; v6's implementation of it did not.** Gating rather than
declaring a range is right. But the WITHDRAWN `TESTED_SQLITE` was a hand-edited tuple: adding
`"3.99.0"` made an untested runtime supported with **no manifest, no probe and
no CI result behind it** (round 5, measured). The document even admitted nothing
enforced the evidence requirement — which made it an intention, not a gate.

**A runtime is qualified only if `specs/generated/sqlite_runtimes.json` records
it and this process reproduces that record:**

| recorded | why |
|---|---|
| `sqlite_version` | the release number |
| **`sqlite_source_id()`** | **a version names a release, not a build.** Two builds of `3.45.1` can differ in compile options, authorizer availability and DDL support — all of which exact matching leans on |
| feature probes | generated columns, authorizer availability, `STRICT` tables, verbatim DDL storage — the behaviours the manifest actually depends on |
| constructor digests | the accepted manifest *this runtime produces*, per version |

`runtime_supported()` matches version **and** source id **and** probes, then
**re-derives the constructor digests here** and compares. Anything else is
refused with `reason="unsupported-sqlite"`, **before** any version or shape
decision.

**Adding a runtime now means running the generator on it.** There is no edit
that qualifies a runtime without producing its evidence — which is the property
v6 claimed and did not have.

**This remains deliberately narrow**, and narrow in the direction that fails
loudly. **S-Q7** stays open for the CI matrix that would widen it.

### 4b. The public contract, frozen

```python
SCHEMA_VERSION: int = 1                        # constrained to 1 … 2147483647
MANIFESTS: dict[int, frozenset[Manifest]]      # generated; constructor + migrations
LEGACY_BASE_VERSIONS: frozenset[int]           # generated from release evidence

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
`"adoption-refused"`, `"locked"`, **`"unsupported-sqlite"`**. Closed because
hosts will branch on it — and v6 introduced the last one in the state table
while leaving it out of this list, so a host branching on the *closed* set would
have met an undocumented value.

**`allow_adopt=False`** resolves **S-Q2**; default `True`, justified by §4a-iv
and not before it. **It can only narrow.**

**`diff` is populated for the shape reasons, against a deterministically chosen
candidate.** A version now has a *set* of accepted manifests, so "which one do
we differ from" needs an answer: **the minimum-distance accepted candidate,
ties broken by provenance in declaration order — constructor first, then
migration paths in registry order.** `diff` names the candidate it chose. A
refusal a user cannot act on becomes a bug report, and a refusal that diffs
against an arbitrary member of a set is worse than none.

```python
class PostCommitAuditError(RuntimeError):
    # The store WAS adopted; the audit sink raised afterwards.
    path: str
    adoption_id: str
    committed: bool = True      # always True; the name is the point
    __cause__: BaseException    # the sink's own exception
```

**Deliberately not a `StoreVersionError`** (§4e). It is raised from `__init__`
after a successful commit, so **the connection is closed before it is raised**
and the half-built object is not handed out. **Retrying the constructor is the
supported way to obtain a usable store** — the retry sees a current store and
correctly does not re-adopt.

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

### 4d. Migrations are declarative, and the containment claim is withdrawn

*(The v5/v6 phrasing quoted here is WITHDRAWN.)* **v5 and v6 claimed a migration
could not reach transaction control, "enforced by construction". That claim was
false**, and round 5 disproved it in one line:

```python
def migration(executor):
    conn = executor._MigrationExecutor__conn      # name mangling is not access control
    conn.set_authorizer(None)
    conn.commit()
```

Measured: **raw connection recovered, outer transaction gone.** An arbitrary
in-process Python callback cannot be sandboxed behind a private attribute, and
**a false containment claim is worse than an admitted trusted one** — it invites
exactly the code it pretends to contain.

**So a migration receives nothing connection-bearing. It declares statements,
and the planner executes them:**

```python
class Migration(NamedTuple):
    from_version: int
    to_version: int
    statements: tuple[str, ...]      # executed in order, by the planner alone
```

There is no object to escape through. **The authorizer stays, with its role
honestly restated:** it denies `SQLITE_TRANSACTION`, `SQLITE_SAVEPOINT`,
`SQLITE_ATTACH` and `SQLITE_DETACH` so that a *declared statement* cannot end
the transaction — `END`, `END TRANSACTION` and `RELEASE` all commit, and a
keyword blacklist missed all three (measured). **It is defence against an
accidental statement, not a sandbox around hostile code.** It is restored in
`finally`: left installed it breaks the planner's own commit; left off after a
failure it drops containment for whatever runs next.

#### 4d-i. The single-step model

Round 5, finding 7: a version accepting a *set* of manifests needs a route
contract, and v6 had none — nothing said whether two migrations could leave the
same version, which one ran, or whether one migration had to work for every
accepted source.

**Ruled: exactly one migration from `n` to `n+1`, generated and validated
against every accepted manifest of `n`.** Route selection, cycles, non-adjacent
steps and duplicate edges are then *unrepresentable* rather than rejected. What
remains checkable is adjacency, that both versions have registry entries, and
that **every version below the current one has a route forward** — an accepted
source manifest with no path to the current version can never be opened, and
`validate_registry()` fails the build for it.

| check | invariant |
|---|---|
| the chain from `found` to `SCHEMA_VERSION` is contiguous | **S4** |
| the file matches an accepted manifest of `found` **before** the first step | **S15** |
| the file matches an accepted manifest of `to_version` **after each** step | **S21** |
| the constructor's own output is an accepted manifest of its version | **S23** |
| every step is adjacent, unique, and reachable | **S24** |
| creation and adoption validate **before** stamping | **S25** |
| the whole chain runs in the single §4c transaction | **S5** |

The registry is **empty** in this change; the test suite generates a simulated
`v1->v2` path so that "empty" never means "untested".

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

**Every ordering has a defined outcome** (round 3, finding 7). v4 named the two
events and left the interesting failure unspecified:

| ordering | outcome |
|---|---|
| `adoption_attempted` raises | **abort and roll back.** Nothing is stamped |
| the database `COMMIT` fails | no `adoption_committed` is emitted; the store is not adopted |
| **`adoption_committed` raises** | **the store *is* adopted.** The exception is wrapped in `PostCommitAuditError`, which is **not** a `StoreVersionError` and must not be mistaken for a failure to open. A caller that retries sees a current store and correctly does not re-adopt |

**Both events carry one opaque `adoption_id`** so a host can pair them.

**The event is now actually frozen.** v6 called it "a versioned, closed event
schema" and specified only two names and a shared id — which cannot be
implemented or compatibility-tested (round 5, finding 8):

```python
class AdoptionAuditEvent(NamedTuple):
    schema_version: Literal[1]
    event: Literal["adoption_attempted", "adoption_committed"]
    adoption_id: str            # uuid4, identical across the pair
    path: str                   # the store path, verbatim
    from_version: int           # 0 for an unstamped store
    to_version: int
    source_manifest_digest: str
    matched_provenance: str     # e.g. "constructor v1"
    occurred_at: str            # RFC 3339, UTC, normalised by veracium
```

`adoption_committed` **repeats every field** of its `attempted` partner except
`event` and `occurred_at`, so a sink can process either in isolation. String
fields are capped at 4096 bytes.

**`path` may contain host-sensitive information** — usernames, deployment
layout — and it is passed verbatim because a truncated path is useless for
audit. **A sink that persists or forwards events is handling that**, and this is
stated so the decision is the host's rather than an accident.

**Sink contract:** **must not access the same store** — it is called under the
write lock, so re-entering deadlocks; **cannot modify the decision**. **Bounded execution time is a host obligation,
not something a `Callable` can enforce** — stated as an obligation rather than
implied as a guarantee. Where no sink is supplied, adoption is written to the
module logger at `INFO` and **the durability claim is not made**.

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

**The measuring instrument is the exception, and in v7 it is three small
modules plus a test file** — `schema_model.py` (identity, digest, drift,
candidate matching), `schema_migrations.py` (declarative steps, planner-owned
execution), `schema_evidence.py` (tag probing and artifacts). **Only the kernel
would be shared with production**; git probing and presentation are outside the
trust boundary.

**Every counterexample is now a pytest test** in `tests/test_schema_model.py`,
**and that is what fixed the last reporting defect**: the old harness printed 30
result rows and reported `28/28`, because its total was a hand-maintained
arithmetic expression. A tool whose purpose is truthful evidence was miscounting
its own evidence. **The count now comes from collection**, and the counterexamples
run in CI with everything else rather than in a bespoke script.

**Invariants are named for what they actually test**, per round 5's non-blocking
note: S36 tests evidence-backed qualification (not tuple membership), S37 covers
DDL *and* policy, S41 covers every authoritative field, S43 is replaced by the
declarative model.

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
| **S10** the **production** internal-exclusion query excludes `sqlite_stat1` | `test_analyze_does_not_change_the_digest` — `ANALYZE`, reopen, assert adopted. **Must call the shipped query** |
| **S11** no code depends on column order | `test_every_statement_names_its_columns` — no `SELECT *` (except aggregates), **every `INSERT` names its destination columns**. *(Round 4: this is now a **general quality lint**, not a justification. v5 still described it as licensing an "unordered column comparison"; the manifest stores ordered `table_xinfo` rows and byte-for-byte DDL, so nothing about acceptance rests on it.)* |
| **S12** index drift is repaired on **every** path | `test_drifted_acceleration_index_is_rebuilt` — replace with a UNIQUE index on an already-**stamped** store, reopen, assert the canonical definition |
| **S13** the stamp is transactional in the installed sqlite | `test_user_version_rolls_back` |
| **S14** a negative version refuses; `SCHEMA_VERSION` is in range | `test_a_negative_user_version_is_refused` |
| **S15** the source signature is validated before migrating | `test_migration_refuses_a_mismatched_source` |
| **S16** a stamped store validates its manifest | `test_a_stamped_store_with_the_wrong_shape_is_refused` |
| **S17** an unstamped file with any foreign object is not "new" | `test_a_database_with_only_an_unrelated_table_is_refused` |
| **S18** foreign table names are never interpolated | `test_a_hostile_table_name_is_passed_as_a_value` — a name containing a quote and a semicolon |
| **S19** generated columns are seen | `test_a_non_identical_schema_is_refused` |
| **S23** the constructor's output **is** `MANIFESTS[SCHEMA_VERSION]` | `test_the_registry_reproduces_the_product_schema` — edit `_SCHEMA` without regenerating and the build fails |
| **S24** every migration names adjacent existing `MANIFESTS` keys | `test_the_migration_registry_is_well_formed` |
| **S25** creation and adoption validate **before** stamping | `test_creation_validates_before_stamping` |
| **S26** an unstamped v1 store migrates **directly** to v2 | `test_legacy_store_upgrades_across_a_skipped_release` — inject `SCHEMA_VERSION = 2`; **the case v3 refused** |
| **S27** an in-memory store works end to end | `test_in_memory_store_is_versioned` — create, stamp, use; manifest read from the live connection |
| **S28** the four round-2 counterexamples are refused | `test_a_non_identical_schema_is_refused` — CHECK, COLLATE, VIEW, custom-collation index |
| **S29** the historical artifact is current | `specs/schema_manifest.py --check` in CI |
| **S30** a normal `ALTER` migration reaches an **accepted** destination | `test_a_migrated_store_is_accepted_at_its_destination` — measured today in `--selfcheck` |
| **S31** canonicalisation preserves quoted-literal semantics | `test_two_literal_variants_are_not_the_same_schema` — **measured today**; they accept opposite values |
| **S32** a `(type, name)` collision cannot hide an object | `test_a_trigger_named_like_an_index_is_not_mistaken_for_drift` — **measured today**; v4 digested it as clean |
| **S33** drift repair is followed by **complete revalidation** | `test_repair_revalidates_before_stamping` — digest accepted **and** drift empty |
| **S34** the evidence supports multiple schema versions | `test_a_v1_store_still_resolves_once_head_is_v2` — **measured today** by simulating version 2 |
| **S35** post-commit audit failure has the specified result | `test_committed_sink_failure_leaves_the_store_adopted` — raises `PostCommitAuditError`, not `StoreVersionError` |
| **S36** the runtime is qualified by recorded evidence | `test_this_runtime_is_qualified_by_evidence` — version **and** source id **and** probes **and** reproduced constructor digests |
| **S37** conformance covers rebuildable **DDL** | `test_a_wrong_rebuildable_ddl_fails_conformance` — v5's digest-based S23 passed it |
| **S38** migration outputs are **generated** into the accepted set | `test_the_migration_path_is_generated_not_preserved` — **measured today** against a simulated `v1->v2` |
| **S39** legacy resolution is candidate-based | `test_resolution_does_not_use_a_default_version_digest` — **measured today** |
| **S40** only unstamped releases feed the legacy set | `test_resolution_is_restricted_to_legacy_base_versions` |
| **S41** the gate re-derives every **authoritative** field | `schema_evidence.py --check` in CI. *(Manual probe, not a suite test: it rebuilds 23 worktrees. The fabricated-artifact result is recorded in §15, not claimed as an automated check.)* |
| **S42** historical manifests are immutable | `test_deleting_a_historical_version_is_an_error` — **measured today** |
| **S43** a migration **carries no connection at all** | `test_a_migration_cannot_reach_the_connection` — the declarative model has no object to escape through; `test_transaction_control_in_a_declared_statement_is_denied` covers all seven forms, `test_the_authorizer_is_restored_after_a_failed_migration` the `finally` |
| **S44** flipping only a **policy** fails conformance | `test_flipping_only_a_policy_fails_conformance` — **v6's check was tautological** |
| **S45** version-zero tries only `LEGACY_BASE_VERSIONS` | `test_resolution_is_restricted_to_legacy_base_versions` |
| **S46** deleting a historical version is an error | `test_deleting_a_historical_version_is_an_error` |
| **S47** a runtime is qualified by **evidence** | `test_an_unrecorded_runtime_is_not_qualified` · `test_a_matching_version_with_different_features_is_not_qualified` |
| **S48** the migration registry is well-formed | `test_the_migration_registry_is_well_formed` — adjacency, uniqueness, reachability |
| **S49** the audit event payload is the frozen type | `test_adoption_event_payload_is_typed` — §4e, both events, paired `adoption_id`. **Not yet written**; needs the store |
| **S20** concurrent first open across **processes** stamps once | `test_concurrent_first_open_across_processes` |
| **S21** the destination signature is validated after migrating | `test_migration_refuses_a_partial_result` |
| **S22** a migration **cannot reach** transaction control | `test_transaction_control_in_a_declared_statement_is_denied` — direct `commit`; `commit` then `BEGIN`; `rollback` then `BEGIN`; `executescript`; `BEGIN` in statement text. **Five evasions, one restricted executor** |

**S6 is the one that protects users** and is why adoption is specified before it
is convenient: everyone who has a store today goes through that path exactly
once, silently, on upgrade.

**S11 is a lint, not a behavioural test**, and its former justification is
withdrawn: §4a compares ordered `table_xinfo` rows and byte-for-byte DDL, so
acceptance no longer depends on column order being irrelevant. It is kept as a
general quality rule about the source, and labelled as one.

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
  commit. A sink that raises *after* commit leaves the store adopted, by design
  and by name.
- **SQLite support is the tested set, not a range** (§4a-viii). `3.45.1` and
  `3.46.1` are what has been observed to agree; **anything else is refused**
  with `unsupported-sqlite`. v5 declared `3.35 ≤ sqlite < 4` on those same two
  observations, which was a claim rather than a contract. **This is narrow, and
  narrow in the direction that fails loudly** — the honest end state is a tested
  matrix, and §9 says what that would take.
- **The historical evidence covers veracium's own releases only** (§4a-iv). A
  store written by another tool is exactly what the signature check is for.

---

## 9. Brief for the external reviewer

**Round 5 approved the architecture a fourth time, deferred v6, and answered a
question I had asked. The answer was yes — the instrument should be smaller —
and the decomposition offered was better than the one I would have chosen.** All
8 blocking findings and both non-blocking ones are taken. Every executable probe
was reproduced first.

**The most important change is not on the findings list.** The instrument is now
three small modules and a pytest file:

```
schema_model.py       identity, digest, drift, candidate matching   <- the kernel
schema_migrations.py  declarative steps, planner-owned execution
schema_evidence.py    tag probing and the generated artifacts
tests/test_schema_model.py   every counterexample, 41 tests
```

**Only the kernel would be shared with production.** And moving the
counterexamples into pytest is what actually fixed the reporting defect: the old
harness printed 30 rows and reported `28/28` because its total was a
hand-maintained arithmetic expression. **The count now comes from collection.**
A tool whose purpose is truthful evidence should not be able to miscount itself.

**Two claims are withdrawn rather than repaired:**

1. **Migration containment.** `executor._MigrationExecutor__conn` recovers the
   connection in one line — name mangling is not access control, and I should
   have known that when I wrote it. *(The WITHDRAWN v5/v6 phrasing is quoted in
   §15.)* Migrations are now
   **declarative**: a closed tuple of statements the planner executes. There is
   no object to escape through. The authorizer stays, with its role restated as
   defence against an *accidental* statement, not a sandbox around hostile code.
2. **`LEGACY_DIGESTS`.** It described a digest→version map, which is the
   circular design §4a-vii had already rejected. Replaced by
   `LEGACY_BASE_VERSIONS`, and — your finding 3 — resolution is now *restricted*
   to it, so release history is an authorization boundary rather than a printed
   summary.

**A new gate, because this class of error has recurred.** A spec row that claims
a check is "measured today" must cite a test that exists;
`test_a_spec_claiming_a_test_is_measured_today_must_have_it` fails the build
otherwise. It currently guards seven rows, and I verified it fires. **After the
module split, several rows in this document still cited pre-split test names** —
exactly the drift you have caught twice by hand.

**Where I am least confident:**

1. **The registry still duplicates DDL with `_SCHEMA`**, now with a reviewed
   policy artifact as a second declaration alongside it. **That is two
   duplications where v6 had one**, and it is only justified while the product
   is not generated from the registry. Generating it is the right fix and it
   belongs to implementation — but I want to flag that I have added a moving
   part to close a hole, which is the trade this spec has been making for five
   rounds.
2. **S-Q7 remains open**: the runtime gate is now evidence-derived, but the
   evidence is still one machine. Qualifying a second runtime requires running
   the generator there, and I have no CI that does it.
3. **`AdoptionAuditEvent.path` is passed verbatim** and may carry host-sensitive
   information. I chose that over truncation because a truncated path is useless
   for audit, and stated it so the decision is the host's.

**What I deliberately did not do:** no offline import tool; no CI matrix; no
generation of `_SCHEMA` from the registry.

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~S-Q1~~ | **RULED 2026-08-01, revised 2026-08-02:** names+types **withdrawn** after round 1; the comparison is the semantic signature in §4a. | resolved | research → external | — |
| ~~S-Q2~~ | **RULED 2026-08-02: `allow_adopt: bool = True`**, §4b — and the default is now justified by §4a-iv rather than by convenience. | resolved | dev | — |
| ~~S-Q4~~ | **ANSWERED by round 2, 2026-08-02: known-constructor equality, not semantic equivalence.** It was a list that grew — v3's signature admitted four more counterexamples. §4a. | resolved | external | — |
| ~~S-Q5~~ | **RESOLVED by round 3, 2026-08-02: a structured schema registry.** `SchemaObject(kind, name, ddl, policy)` generates creation, expectation, typed rebuildable identities, repair and drift from one declaration. §4a-vi. **It was blocking, and it was the cause of the `(type, name)` bypass.** | resolved | external | — |
| ~~S-Q6~~ | **RESOLVED by round 4, refined by round 5:** gate the runtime, and **derive qualification from evidence** rather than a hand-edited list. §4a-viii. | resolved | external | — |
| **S-Q7** | **Should the qualified-runtime set be widened by a CI matrix before release?** The gate is evidence-derived now, but the evidence is still one machine: qualifying a second runtime means running the generator there. | `pre-release` | dev | before release |
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

---

## 13. Round 3 review disposition

**Verdict: architectural direction approved; v4 deferred.** 9 blocking findings.
**All 9 taken**; 8 closed, **1 (S36 / S-Q6) explicitly not closed** and named as
such rather than argued down.

| # | finding | closed by |
|---|---|---|
| 1 | one manifest per version rejects a correct `ALTER` migration | **§4a-v** — `MANIFESTS: dict[int, frozenset]`. Reproduced: `table_xinfo` identical, stored DDL differs in whitespace placement, digests differ. The rebuild-every-table alternative was considered and rejected in the text |
| 2 | whitespace collapsing creates semantic collisions | **§4a** — **no normalisation at all.** Reproduced: `'a  b'` and `'a b'` schemas shared a digest and accept opposite values. **S31** |
| 3 | name-only object identity hides objects | **§4a-0** — identity is `(type, name)`; only `("index", …)` may be excluded or repaired. Reproduced: an arbitrary trigger digested **identical to a clean store**. Drift is typed, so it is now a digest failure rather than false index drift. **S32**, and **S33** for post-repair revalidation |
| 4 | the evidence generator cannot survive version 2 | **§4a-iv** — releases resolve to a *known version*, not to HEAD. **S34** simulates version 2 and proves a v1 store still resolves |
| 5 | per-version manifests are not durably specified | **§4a-iv** — `specs/generated/schema_versions.json` carries full canonical object records per version, immutable for prior versions. Ambiguous digest→version inversion returns **nothing**, not a guess |
| 6 | the executor is a blacklist and misses `END` / `RELEASE` | **§4d** — authorizer-backed. Measured: `END` commits; the authorizer denies `SQLITE_TRANSACTION`, `SQLITE_SAVEPOINT`, `SQLITE_ATTACH`, `SQLITE_DETACH` while allowing migration DDL/DML, transaction intact. **S22** extended to `END`, `END TRANSACTION`, `RELEASE`, comments and literals |
| 7 | post-commit audit failure is undefined | **§4e** — every ordering has an outcome; `PostCommitAuditError` is deliberately **not** a `StoreVersionError`; both events carry one `adoption_id`. Bounded execution restated as a **host obligation** rather than a guarantee |
| 8 | S-Q5 needs a structured constructor | **§4a-vi** — adopted as proposed. One registry generates six consumers, and `--selfcheck` proves it reproduces `_SCHEMA` |
| 9 | tested under only one SQLite runtime | **NOT CLOSED.** §8 declares 3.35 ≤ sqlite < 4; **two agreeing data points is not a matrix.** Recorded as **S36 / S-Q6**, and named in §9 as the thing I most want pushed on |

---

## 14. Round 4 review disposition

**Verdict: architecture approved; v5 deferred for a truthful generator.** 8
blocking findings plus 4 specification corrections. **All taken.**

**The framing is the finding.** Round 4's real observation is that the spec
claimed the instrument proved things it did not implement. Every item below is
a gap between a sentence in this document and the code that was supposed to
back it.

| # | finding | closed by |
|---|---|---|
| 1 | S23 ignored rebuildable definitions | **§4a-vi** — conformance compares complete typed records, policies and drift, **never the acceptance digest**. Measured: a registry declaring `CREATE UNIQUE INDEX … ON edges(user_id)` passed v5 with `digest_equal True, drift []`; it now yields exactly one conformance problem. **S37** |
| 2 | migration outputs were not generated | **§4a-v** — `MIGRATIONS` drives generation; every accepted record is produced by executing a declaration, and preserved JSON is not an authorization source. `--selfcheck` generates a simulated `v1->v2`. **S38** |
| 3 | legacy resolution was circular | **§4a-vii** — one inventory, each candidate version's own rebuildable policy, unique match required. Measured: a v2 store digests `4b250945…` under v1's policy and resolves to **nothing**. **S39** |
| 4 | evidence could not tell stamped from unstamped | **§4a-iv** — every release row records `on_disk_user_version`; **only rows reading `0` feed the legacy set**, and a stamp disagreeing with the shape is an error. **S40** |
| 5 | CI did not verify the recorded version | **§4a-iv** — the gate re-derives version, digest, stamp, algorithm and tested-SQLite set. Measured: the 999 artifact passed v5 with **rc 0**, and now yields **23 problems**. **S41** |
| 6 | "immutable" history was rewritten | **§4a-iv** — regenerating a version below the current one and getting a different answer is an **error**. Measured: `old_v1_preserved? False` under v5. **S42** |
| 7 | a raw cursor re-exposes the connection | **§4d** — `execute` returns an inert `MigrationResult`; the cursor is closed and never escapes; the authorizer is restored in `finally`. Measured: the direct `COMMIT` was denied and the cursor route succeeded. **S43** |
| 8 | S36 expressly unresolved | **§4a-viii — resolved by narrowing.** `TESTED_SQLITE` is the contract; anything else refuses with `unsupported-sqlite`. **S-Q7** opens for the CI matrix that would widen it |

**Specification corrections, all applied:** `MANIFESTS` is plural everywhere it
is normative; `diff` names a deterministic candidate-selection rule (§4b); S11's
justification is withdrawn and it is relabelled a general quality lint;
`PostCommitAuditError` has a public contract, and the connection is closed
before it is raised.

**On the package defect:** `--check` needed git and said so only obliquely. It
now exits `2` with an explicit message when there is no checkout, and the README
lists it with `--releases` and `render_index --check` as archive-unrunnable.

---

## 15. Round 5 review disposition

**Verdict: architecture approved; v6 deferred.** 8 blocking findings, 2
non-blocking, and an answer to my own question. **All taken.**

| # | finding | closed by |
|---|---|---|
| 1 | a migration recovers the raw connection | **§4d — the containment claim is withdrawn**, and the callback model with it. Migrations are declarative statement tuples; there is no connection-bearing object. Measured: `executor._MigrationExecutor__conn` then `set_authorizer(None)` then `commit()` ended the transaction |
| 2 | registry conformance did not verify policy | **§4a-vi** — policies compare against `schema_policy.json`, independently reviewed. v6's check computed the expectation from the registry it was checking; flipping `REBUILDABLE`→`REQUIRED` left it empty. **S44** |
| 3 | the legacy contract contradicted candidate resolution | **§4-i, §4b** — `LEGACY_DIGESTS` withdrawn; `LEGACY_BASE_VERSIONS` **restricts** resolution. Measured: v6 resolved an unstamped v2 shape to 2. **S45** |
| 4 | the gate did not re-derive every field | **§4a-iv** — fields classified authoritative / summary / structural; `sqlite_version` removed from the release artifact rather than kept unchecked. Measured: the fabricated artifact passed v6 with rc 0 |
| 5 | a historical version could be deleted | **§4a-iv** — a recorded version this build no longer declares is an error; generation binds to a declared `SCHEMA_VERSION`, not `max(SCHEMAS)`. **S46** |
| 6 | the SQLite gate was hand-authorized | **§4a-viii** — qualification requires a recorded runtime whose **source id** and feature probes match and whose constructor digests reproduce here. `unsupported-sqlite` added to the closed reason set, which v6 had introduced in the state table only. **S47** |
| 7 | multiple migration routes had no contract | **§4d-i — the single-step model.** Exactly one migration `n`→`n+1`, validated against every accepted manifest of `n`. Cycles, non-adjacent steps and duplicate edges become unrepresentable. **S48** |
| 8 | the audit event had no frozen schema | **§4e** — `AdoptionAuditEvent` typed in full, `committed` repeats its partner's fields, string caps stated, and `path` sensitivity named as the host's decision. **S49** |

**Non-blocking, both taken:** the self-check summary undercounted its own rows —
fixed by deleting the harness and moving the counterexamples into pytest, where
the count comes from collection; and the overstated "already executable" claims
are renamed to the property each check actually tests, **with a new gate that
fails the build when a row claims present-tense evidence it does not have.**

**"Should the instrument be smaller?" — yes, and the split is adopted as
proposed.** `schema_model` / `schema_migrations` / `schema_evidence` /
`tests/test_schema_model.py`, with only the kernel inside the trust boundary.
