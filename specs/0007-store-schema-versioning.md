# Feature spec: on-disk store schema versioning

Spec-Status: in review

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v14) — SCOPE CUT.** Opened 2026-08-01; **narrowed 2026-08-03 on
> the product owner's decision.** Seven external rounds produced ~63 findings,
> and the large majority lived in **migration machinery with no users** —
> `MIGRATIONS` was empty and `SCHEMAS` had one member. **`0007` is now
> stamp · refuse-newer · adopt-v1.** The migration contract moves to
> **`specs/0013`**, a dedicated store-migrations spec. *(v10 first moved it to
> `0006`; round 8 showed that could not express the dependency, and `0013`
> replaced it.)* Nothing is discarded — `0013` §4 states the inherited
> conclusions in full.
> **It remains the `Spec-Requires:` prerequisite of `0006`, `0008`, `0009` and
> `0010`.**

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v14 |
| **Status** | *see `Spec-Status:` — canonical.* Deliberately small and separable: it is a **prerequisite** of `0013` and of every schema-changing spec, not a part of any of them. |
| **Internal reviewers** | research — pending |
| **External review** | required — `store/sqlite.py` is guarded and a wrong adoption makes stores unopenable |
| **Review history** | *see `specs/STATUS.md`, generated from `specs/reviews.py`. No counts are stated here; a hand-maintained count drifted in `0008` and was found by the reviewer.* |
| **Decision + date** | — |
| **Path** | full |
| **Measuring instrument** | `specs/schema_model.py` (kernel) · `schema_evidence.py`; every counterexample lives in `tests/test_schema_model.py` and is counted by collection |
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
one, **and the next schema change is `0008`'s `confirmations` table**, which is
why this is being fixed
now rather than alongside. Landing versioning *with* the change that needs it
means the migration mechanism gets its first exercise on the same commit that
first needs to be correct.

**If we do nothing:** a schema-changing spec bumps the store shape, an older build opens a newer
store, `CREATE TABLE IF NOT EXISTS` silently no-ops on tables it thinks it
understands, and reads return partial data with no error. **Silent
misinterpretation of persisted trust data is the worst failure mode this project
has.**

---

## 2. Field contracts touched

| field | read / written | contract | consumers |
|---|---|---|---|
| **`PRAGMA user_version`** | **NEW** — written on create and adopt, read on every open | the integer shape-id of this store file | `SqliteStore.__init__` only |
| **`MANIFESTS`** | **NEW** — **generated** by executing each constructor | the **closed set** of object sets accepted *at* that version. A *set*, because `0013` will add migration outputs | open |
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
| **a lower `user_version`** | — | — | — | downgrade to skip validation | **cannot arise at `SCHEMA_VERSION = 1`**; recorded here because `0013` must handle it (§4f) |
| **a stamped-but-wrong store** | — | — | — | stamp a foreign file `1` to bypass adoption entirely | **S16** — every version validates its manifest, not only version zero |
| **a schema that is *equivalent* but not identical** | — | — | **a `CHECK`, a `COLLATE`, a view, a custom-collation index** | any of the four round-2 counterexamples | **S28** — exact-match against known manifests; equivalence is **not** attempted (§4a) |
| ~~a migration~~ | — | — | — | *(out of scope from v10 — `0013`, §4f)* | — |
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
| **all 23 released versions build a known store** | `specs/schema_evidence.py --releases --write` | **23/23 identical · 0 unbuildable · sqlite 3.45.1**, recorded with tag + commit sha in `specs/generated/legacy_stores.json` |
| **v3's signature accepted four non-equivalent databases** | `pytest tests/test_schema_model.py` | reproduced all four; all four refused |
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
| **legacy** | `user_version = 0` **and the manifest matches exactly one version in `LEGACY_BASE_VERSIONS`** (§4a-vii) | **adopt**: repair index drift, stamp. **Today that is always version 1** |
| **foreign** | `user_version = 0` **and anything else** | **REFUSE** `reason="foreign-shape"` |
| **unsupported runtime** | this runtime is not qualified by `sqlite_runtimes.json` (§4a-viii) | **REFUSE** `reason="unsupported-sqlite"` — checked **before** any of the rows below |
| **current** | `user_version = SCHEMA_VERSION` **and the manifest is in `MANIFESTS[SCHEMA_VERSION]`** | repair index drift if any (§4a-iii), **revalidate**, open |
| **stamped-wrong** | `user_version = SCHEMA_VERSION` **and it does not** | **REFUSE** `reason="stamped-shape-mismatch"` |
| **older** | `0 < user_version < SCHEMA_VERSION` | **cannot arise while `SCHEMA_VERSION = 1`.** When it can, `0013` owns it — see §4f |
| **newer** | `user_version > SCHEMA_VERSION` | **REFUSE** `reason="newer"` |

### 4-i. Version zero, and what `0013` owns

**Under `SCHEMA_VERSION = 1` the version-zero path is a stamping step.** The
store's shape is resolved against `LEGACY_BASE_VERSIONS` — the versions whose
release evidence shows a genuinely *unstamped* store — index drift is repaired,
and the stamp is written. Today that set is `{1}`, so adoption is: recognise the
one historical shape, or refuse.

**Missing evidence authorises nothing.** An earlier draft returned
`{SCHEMA_VERSION}` when the artifact was absent, silently authorising adoption
on the strength of the very evidence that was missing. It returns the empty set,
so **a nonempty unstamped store is refused when the evidence is unverified.**
`allow_adopt=False` may narrow that further; nothing may broaden it. **S54**.

#### 4f. What `0013` owns, and why

**Round 1 established the requirement that survives the cut:** a user who
upgrades across a schema change **must not be required to install every
intermediate release**. A store presenting `user_version = 0` with a version-1
shape to a version-2 build must resolve to base 1 and then migrate forward —
not be refused as foreign.

**That requirement is owned by `specs/0013`**, a dedicated store-migrations
spec. The scope cut first put it in `0006` §0b, and **that was wrong**: `0006`
is a `draft` whose §3 is falsified, and the gate reads a spec's *direct*
`Spec-Requires:` entries — it cannot infer that adding a table needs migration
work living inside a source-identity spec. Round 8 caught it. The design work is not lost:
**seven review rounds of it are preserved in
`specs/archives/0007-v9-20260803T0056Z.tar.gz`**, and the conclusions that
survived review are listed in `0013` §4 — the single-step model, declarative
statements rather than callbacks, effects confined to persistent `main` schema,
capability-not-DDL-text destination validation, and per-path runtime evidence.

**The dependency graph, repaired.** `0013` requires `0007`; **`0006`, `0008`,
`0009` and `0010` each require `0007` and `0013`.** Verified: a commit citing
the `accepted` `0008` is refused by name for **both** unresolved prerequisites.
**Without this, accepting `0007` would have authorised implementing `0008`'s
`confirmations` table with no migration design** — `0008`'s own C12 names that
exact failure. That is the most serious defect the scope cut introduced, and it
was mine.

**Why the cut.** Seven rounds produced ~63 findings. The large majority were in
migration and migration-driven runtime machinery, **for a registry that was
empty**. That is not a reflection on the reviews — every finding was real, and
two were total bypasses. It is a statement about designing a mechanism with no
users: each round I rewrote code nothing called, and each rewrite introduced a
defect the next round found. **`0007` now covers what a store needs today**;
`0013` will carry the rest when it has a concrete migration to hold it to.

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
> build's known schema constructors produces.**

*(`0013` widens that to "constructors or migrations" when migrations exist. At
`SCHEMA_VERSION = 1` there are none — which is why `MANIFESTS` is already a
**set** per version: it has room for the widening without a later change.)*

Veracium does not need to decide whether an arbitrary SQLite schema is
semantically equivalent to its own. That is an open-ended SQL-equivalence
problem and it is unnecessary. **The acceptance model is exact-match against
known manifests**, implemented in `specs/schema_model.py`:

1. Build a reference database with each supported constructor. *(`0013` adds
   migration outputs.)*
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

**This bounds `allow_adopt=True`, and the bound is narrower than it reads:**
*every released codebase, probed under the qualified SQLite runtime, produced
the accepted manifestation.* It says nothing about a store another tool wrote —
**and nothing about a store a user created under a different SQLite runtime.**
Such a store is refused unless its actual manifest matches, which is a safety
property; **the availability of adoption for it is not established.**

**An unbuildable release fails the tool**, because it is a gap in the evidence
rather than a pass.

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
it *completely* and this process reproduces that record.** v7 checked
`all(constructor_digest == recorded)` — and `all()` over an **empty** mapping is
`True`, so a record with no digests qualified vacuously (round 6, finding 4,
measured). Completeness is now a precondition and the key set must **equal** the
declared schema versions:

| recorded | why |
|---|---|
| `sqlite_version` | the release number |
| **`sqlite_source_id()`** | **a version names a release, not a build.** Two builds of `3.45.1` can differ in compile options, authorizer availability and DDL support — all of which exact matching leans on |
| feature probes | **behavioural, not nominal** (round 7, finding 5), and **only the ones schema matching needs**: a valid strict table, **body-preservation of submitted DDL**, and `table_xinfo` exposing a generated column with a nonzero hidden flag. v8's `STRICT` probe used invalid SQL — a strict table's column must declare a datatype — so it recorded "unsupported" on a runtime that supports it; the DDL probe only checked that a row existed. **The authorizer/confinement probe moved to `0013`** with the code that needs it |
| constructor digests | the accepted manifest *this runtime produces*, per version — key set **equal to** the declared versions, and non-empty |
| ~~migration-path digests~~ | **`0013`'s**, not `0007`'s. DDL rewriting is why a version can have several accepted manifests, so a runtime agreeing on constructors could still disagree on an `ALTER` path — but at `SCHEMA_VERSION = 1` there are no paths and this build records none |
| manifest algorithm, schema version | a record generated under a different algorithm or schema version qualifies nothing |

`runtime_supported()` matches version **and** source id **and** probes, then
**re-derives the constructor digests here** and compares. Anything else is
refused with `reason="unsupported-sqlite"`, **before** any version or shape
decision.

**The constructor key set must equal what the registry declares** — not merely
contain no extras. *(Historical, and `0013`'s to carry: v8 keyed migration
digests by destination version and returned after the first viable base, so only
one path per destination could be recorded, while different bases can produce
different exact output at the same destination. `0007` records no migration
paths, so it makes no claim about their coverage.)*

**`0007` supports exactly one active runtime** (round 10, finding 2). v9
described accepted manifests as a union across qualified runtimes and v12
narrowed contribution to records this process reproduces — which made the union
undescribable: on runtime A only A contributes, on B only B, and nothing
persists an attestation that A was reproduced by its own job. `write_runtime()`
then refused a second differing runtime outright, because it required every
valid prospective manifestation to be in an accepted set that excluded it.
**A half-built union is worse than an honest single-runtime contract**, so the
union claim is withdrawn: a second active identity is refused, and **S-Q7 owns
widening it with durable per-runtime attestation.** The historical reasoning
that motivated the union follows.

*(Historical, and the reason `MANIFESTS` is a set:)* accepted manifests were
described as a union across every qualified runtime (round 7, finding 4).
v8 regenerated the current version solely from the runtime running the command,
so a second qualified runtime whose DDL differed would be marked qualified while
the stores it creates were **not** in `MANIFESTS` — and regenerating there would
delete the first runtime's manifestation. Measured: an inserted foreign
manifestation was silently dropped. Runtime records now carry **full object
records, not only digests** — a digest cannot reconstruct the object-level
`diff` §4b promises — and adding a runtime **merges, never replaces**. **S58**.

**Adding a runtime means running `schema_evidence.py --runtime --write` on it**,
which **now actually writes**: v7 documented that workflow and ignored the flag
on that path, so the stated route to qualifying a second runtime did not exist
(round 6, finding 5, measured — the artifact checksum was unchanged). It refuses
to write an incomplete record. **S55**.

**And the WITHDRAWN claim that 3.46.1 was qualified is retracted.** v7's text said 3.45.1
and 3.46.1 had been observed to agree while the shipped artifact recorded only
3.45.1 — so the package failed its own runtime test in the reviewer's
environment, on a runtime the document called qualified. **Only 3.45.1 is
recorded, because only 3.45.1 has been run through the generator.**

**An unqualified runtime is a skip, not a suite failure.** v7 asserted
`runtime_supported()` unconditionally, so the entire adversarial schema suite
failed on an unrecorded SQLite. Those are two different questions and they are
now two different tests: *is the recorded evidence complete and self-consistent*
(always runs), and *is this runner one of the recorded runtimes* (skips, with
the command to fix it in the message). **S56**.

**This remains deliberately narrow**, and narrow in the direction that fails
loudly. **S-Q7** stays open for the CI matrix that would widen it.

### 4b. The public contract, frozen

```python
SCHEMA_VERSION: int = 1                        # constrained to 1 … 2147483647
MANIFESTS: dict[int, frozenset[Manifest]]      # generated; a set, because 0013 will add migration outputs
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
                 audit_sink: Callable[[AdoptionAuditEvent], None] | None = None,
                 busy_timeout_ms: int = 5000) -> None: ...
```

**`reason` is a closed set** — `"invalid-version"`, `"newer"`,
`"foreign-shape"`, `"stamped-shape-mismatch"`, `"adoption-refused"`,
`"locked"`, `"unsupported-sqlite"`. **The three `migration-*` reasons are
withdrawn with the scope cut — `0013` adds what it needs.** Closed because
hosts will branch on it — and v6 introduced the last one in the state table
while leaving it out of this list, so a host branching on the *closed* set would
have met an undocumented value.

**`allow_adopt=False`** resolves **S-Q2**; default `True`, justified by §4a-iv
and not before it. **It can only narrow.**

**`diff` is populated for the shape reasons, against a deterministically chosen
candidate.** A version now has a *set* of accepted manifests, so "which one do
we differ from" needs an answer — **and the metric has to be frozen too, or two
implementations produce different diagnostics.**

> **Distance** = the number of typed keys `(type, name)` on which the two
> manifests disagree, counting a key present in one and absent from the other as
> one disagreement, and a key present in both with any differing field as one.
> **Ties break by provenance in declaration order** — constructor first, then
> migration paths in registry order.

`diff` names the candidate it chose and its provenance. A
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
  create the schema             -- statement by statement, never executescript
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
`event` and `occurred_at`, so a sink can process either in isolation.

**On the 4096-byte cap, which v7 stated inconsistently alongside "verbatim":**
the cap is a **validation limit, not a truncation** — a `path` longer than 4096
bytes raises rather than being silently shortened, because a silently truncated
path in an audit record is a falsified audit record. `path` is otherwise
verbatim. The two statements are now compatible.

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

**The migration regime is out of scope from v10** (§4f). Earlier versions
carried invariants that injected a fake registry to reach it, and stated that
the alternative was invariants which silently test nothing. That was true — and
the deeper problem was that the regime had no users at all. **`0013` owns it**,
where a real migration reaches it without a fixture.

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

**The measuring instrument is the exception, and after the scope cut it is two
modules plus a test file** — `schema_model.py` (identity, digest, drift,
candidate matching) and `schema_evidence.py` (tag probing and artifacts).
**The shared production boundary is `schema_model` + runtime-evidence
validation**; only git probing, release enumeration and presentation are
outside it. **`specs/0013` extends both** — its migration declarations and
execution confinement join the shared kernel, and runtime evidence gains
per-path entries — **when migrations exist.**

**Every counterexample is now a pytest test** in `tests/test_schema_model.py`,
**and that is what fixed the last reporting defect**: the old harness printed 30
result rows and reported `28/28`, because its total was a hand-maintained
arithmetic expression. A tool whose purpose is truthful evidence was miscounting
its own evidence. **The count now comes from collection**, and the counterexamples
run in CI with everything else rather than in a bespoke script.

**Invariants are named for what they actually test**, per round 5's non-blocking
note: S36 tests evidence-backed qualification (not tuple membership), S37 covers
DDL *and* policy, S41 covers every authoritative field.

| invariant | executable check |
|---|---|
| **S1** a fresh store is stamped | `test_new_store_is_stamped` |
| **S2** a newer store is refused | `test_a_newer_store_is_refused` — write `SCHEMA_VERSION + 1` directly |
| **S3** adoption verifies signature, not counter | `test_a_foreign_store_at_version_zero_is_refused` |
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
| **S16** a stamped store validates its manifest | `test_a_stamped_store_with_the_wrong_shape_is_refused` |
| **S17** an unstamped file with any foreign object is not "new" | `test_a_database_with_only_an_unrelated_table_is_refused` |
| **S18** foreign table names are never interpolated | `test_a_hostile_table_name_is_passed_as_a_value` — a name containing a quote and a semicolon |
| **S19** generated columns are seen | `test_a_non_identical_schema_is_refused` |
| **S23** the constructor's output **is** `MANIFESTS[SCHEMA_VERSION]` | `test_the_registry_reproduces_the_product_schema` — edit `_SCHEMA` without regenerating and the build fails |
| **S25** creation and adoption validate **before** stamping | `test_creation_validates_before_stamping` |
| **S27** an in-memory store works end to end | `test_in_memory_store_is_versioned` — create, stamp, use; manifest read from the live connection |
| **S28** the four round-2 counterexamples are refused | `test_a_non_identical_schema_is_refused` — CHECK, COLLATE, VIEW, custom-collation index |
| **S29** the historical artifact is current | `specs/schema_evidence.py --check` in CI |
| **S31** canonicalisation preserves quoted-literal semantics | `test_two_literal_variants_are_not_the_same_schema` — **measured today**; they accept opposite values |
| **S32** a `(type, name)` collision cannot hide an object | `test_a_trigger_named_like_an_index_is_not_mistaken_for_drift` — **measured today**; v4 digested it as clean |
| **S33** drift repair is followed by **complete revalidation** | `test_repair_revalidates_before_stamping` — digest accepted **and** drift empty |
| **S34** the evidence supports multiple schema versions | `test_a_v1_store_still_resolves_once_head_is_v2` — **measured today**; the resolver is version-aware even though only one version exists, because `0013` will add the second |
| **S35** post-commit audit failure has the specified result | `test_committed_sink_failure_leaves_the_store_adopted` — raises `PostCommitAuditError`, not `StoreVersionError` |
| **S36** the runtime is qualified by recorded evidence | `test_this_runtime_is_qualified_or_explicitly_is_not` — version **and** source id **and** probes **and** reproduced constructor digests |
| **S37** conformance covers rebuildable **DDL** | `test_a_wrong_rebuildable_ddl_fails_conformance` — v5's digest-based S23 passed it |
| **S39** legacy resolution is candidate-based | `test_resolution_does_not_use_a_default_version_digest` — **measured today** |
| **S40** only unstamped releases feed the legacy set | `test_resolution_is_restricted_to_legacy_base_versions` |
| **S41** the gate re-derives every **authoritative** field | `schema_evidence.py --check` in CI. *(Manual probe, not a suite test: it rebuilds 23 worktrees. The fabricated-artifact result is recorded in §15, not claimed as an automated check.)* |
| **S42** historical manifests are immutable | `test_deleting_a_historical_version_is_an_error` — **measured today** |
| **S44** flipping only a **policy** fails conformance | `test_flipping_only_a_policy_fails_conformance` — **v6's check was tautological** |
| **S45** version-zero tries only `LEGACY_BASE_VERSIONS` | `test_resolution_is_restricted_to_legacy_base_versions` |
| **S46** deleting a historical version is an error | `test_deleting_a_historical_version_is_an_error` |
| **S47** a runtime is qualified by **evidence** | `test_an_unrecorded_runtime_is_not_qualified` · `test_a_matching_version_with_different_features_is_not_qualified` |
| **S49** the audit event payload is the frozen type | `test_adoption_event_payload_is_typed` — §4e, both events, paired `adoption_id`. **Not yet written**; needs the store |
| **S54** missing legacy evidence authorises nothing | `test_missing_legacy_evidence_authorizes_nothing` — **measured today** |
| **S55** runtime evidence can actually be written | `test_writing_runtime_evidence_actually_writes` — **measured today**; v7's flag was ignored |
| **S56** recorded runtimes are internally valid | `test_the_recorded_runtimes_are_internally_valid` (always) · `test_this_runtime_is_qualified_or_explicitly_is_not` (skips) · `test_an_empty_digest_map_does_not_qualify_vacuously` — **measured today** |
| **S58** an **unattested** runtime contributes nothing | `test_an_unattested_foreign_runtime_contributes_nothing` — **measured today**. Internal consistency is not provenance |
| **S65** the **production predicate** rejects a conflicting artifact | `test_a_conflicting_artifact_disqualifies_the_runtime` · `test_the_recorded_artifact_has_no_conflicts` — **measured today**; v12 checked this only in the generator |
| **S66** exactly one active runtime identity | `test_two_active_runtime_identities_are_refused` · `test_one_canonical_identity_is_used_everywhere` — **measured today**. **One canonical five-field key** is used for uniqueness, one-active enforcement, replacement, attestation and reporting |
| **S69** the predicate attests the **complete** manifestation | `test_a_modified_rebuildable_ddl_disqualifies_the_runtime` · `test_a_missing_rebuildable_index_disqualifies_the_runtime` — **measured today**; the acceptance digest excludes rebuildable objects, so digests alone attest nothing about them |
| **S70** `SCHEMA_VERSION` is bound to the registry | `test_schema_version_must_match_the_registry` · `test_the_registry_versions_are_contiguous` — **measured today**. *(This invariant existed before the scope cut, regressed when the module holding it was deleted, and the round-6 disposition went on claiming it. The citation gate now catches that class.)* |
| **S71** a missing versions artifact fails the gate | `test_a_missing_versions_artifact_fails_the_gate` — **measured today** |
| **S67** a failed publish leaves nothing published | `test_a_staging_failure_publishes_nothing` · `test_a_failed_publish_rolls_the_first_file_back` — **measured today**; v12 claimed rollback with no test |
| **S68** staged temporaries are cleaned up | `test_staged_temporaries_are_not_left_behind` · `test_the_repository_has_no_stray_staged_artifacts` — **measured today**; v12 shipped a `.tmp` in the review package |
| **S63** a self-consistent fabrication is rejected | `test_a_self_consistent_fabrication_is_rejected` — **measured today**; a manifestation may hold only declared objects |
| **S64** conflicting runtime identities reject the artifact | `test_conflicting_runtime_identities_reject_the_artifact` · `test_a_duplicate_runtime_record_is_rejected` — **measured today** |
| **S59** the policy vocabulary is closed | `test_a_policy_typo_is_a_build_error` · `test_a_rebuildable_non_index_is_a_build_error` — **measured today**; a typo disabled validation entirely |
| **S61** the release `result` is re-derived | `test_the_release_result_is_rederived` — **measured today**; v8 read the stored value |
| **S62** feature probes assert their behaviour | `test_the_strict_table_probe_uses_valid_sql` · `test_the_ddl_probe_asserts_body_preservation` — **measured today** |
| **S20** concurrent first open across **processes** stamps once | `test_concurrent_first_open_across_processes` |

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
opens today refuse to open tomorrow. **The refused population is not claimed to
be empty** — §4a-iv establishes only that every released *codebase*, probed
under the qualified runtime, produced the accepted manifestation. A store
created under a different SQLite runtime may not match, and would be refused.
The blast radius of that is "the application will not start", which is loud and
recoverable by installing a matching build.

**Reversibility, and the limit that cannot be fixed here.** Adoption writes one
integer and no data, so downgrading to a pre-0007 build works — that build
ignores `user_version` entirely.

**That is also the hole.** A build released before 0007 has no version check: it
ignores the stamp, applies `CREATE TABLE IF NOT EXISTS`, and opens the file.
**No value stored inside the database can make code that never reads that value
refuse to open it.** Once a schema-changing feature lands,
downgrading to an already-released binary recreates the original failure mode.

**This is unavoidable when retrofitting versioning after releases exist**, and
§8 narrows the claim accordingly rather than implying protection that does not
exist. **A declaration that a migration is "one-way" is not a fence.** The first
schema-changing release must therefore carry an operational downgrade contract:
a pre-migration backup, no downgrade to a pre-0007 binary, installer fencing
where the packaging supports it, loud release documentation, and a recovery path
from the backup. **`0013` owns that contract**; this spec's job is to say the
guarantee stops here.

---

## 8. Claims and limits

**Claim, narrowed in v4 and again in v10:** **every *version-aware* build — every
release from the one implementing 0007 onward — refuses to open a store it does
not recognise.** With `SCHEMA_VERSION = 1` the recognised shapes are: a store
this build created, and the one historical unstamped shape every released
version produces. **Everything else is refused.**

**The narrowing is not cosmetic.** v3 claimed "a veracium build refuses…", which
is false of the 23 builds already released: none of them reads `user_version` at
all. The claim can only ever cover code that performs the check.

**Limits:**

- **Not integrity, not authentication.** Nothing detects tampering or
  corruption; `user_version` is advisory metadata a writer can set to anything.
  Against an adversary with write access to the file this proves nothing — **and
  that adversary already owns everything.** The signature raises the cost of a
  *mistake*, not of an attack.
- **No migrations.** `SCHEMA_VERSION = 1` and there is nothing to migrate from.
  **`0013` owns the migration contract** (§4f), including one-process-only
  execution and the skipped-release upgrade path round 1 established.
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
- **SQLite support is the recorded set, and it currently has one member**
  (§4a-viii). **`3.45.1` is the only runtime run through the generator**;
  everything else is refused with `unsupported-sqlite`. v7's text named a second
  runtime the artifact did not record, and the package then failed its own test
  on it. **One recorded runtime is a narrow contract but a true one**, and it
  fails loudly. The honest end state is a tested matrix — **S-Q7**, and §9 says
  what it would take.
- **The historical evidence covers veracium's own releases only** (§4a-iv). A
  store written by another tool is exactly what the signature check is for.

---

## 9. Brief for the external reviewer

**Round 11: three findings, all reproduced, all fixed. No architectural change,
as you asked.**

**Finding 1 — I had three definitions of one thing.** `_identity_key()` used
five fields for attestation; the one-active check used `version + source_id`;
replacement used the same pair. Two records agreeing on version and source id
but disagreeing on feature probes therefore passed every check. **One canonical
key is now used for uniqueness, one-active enforcement, replacement, attestation
and reporting**, and two records describing one build inconsistently reject the
artifact.

*(Fixing it deadlocked once, and the fix is worth stating: re-qualifying a build
must supersede **its own** previous record — including one written under an
older manifest algorithm, which is how a bump is cleared. Keying replacement on
the full identity meant the new and superseded records shared a build, so the
new "one build cannot have two" check blocked the very write that removes the
old one. Replacement is by build; a **different** build is kept and then refused
as a second active identity, which is the behaviour you asked for.)*

**Finding 2 — digests attest nothing about rebuildable objects, by design.** The
acceptance digest deliberately excludes them, so a record claiming
`CREATE UNIQUE INDEX ix_edges_subj_rel ON edges(user_id)` reproduced its digest
exactly. **`runtime_supported()` now compares the complete constructor
manifestation**, and the record's key set must *equal* the declared set rather
than merely contain no extras. **S69.**

This is the third time the same shape has appeared — a check living in the
generator while the store-facing path had none. I have no structural answer
beyond noticing it faster.

**Finding 3 — a regression I introduced, and my own gate should have caught
it.** The `SCHEMA_VERSION`/`SCHEMAS` guard lived in the module the scope cut
deleted, and the round-6 disposition went on claiming it was enforced.
Restored in `validate_schema_registry()` where it belongs — it is a consistency
condition of `0007`'s own registry, not migration machinery. **S70.**

**And the citation gate now catches that class**: writing the new invariant's
note as "the former S53" failed the build, because S53 no longer exists. That is
exactly the drift you found by hand, caught mechanically the first time it
recurred.

**Corrections.** The migration-path coverage paragraph is now historical and
attributed to `0013`; the manifest procedure is constructor-only; a **missing**
`schema_versions.json` fails the gate instead of passing silently (**S71**); and
`strict_tables` is recorded as identity but explicitly **not** required, since
nothing in `0007`'s matching uses it — stated rather than listed among required
behaviours and left unenforced.

**Where I am least confident:**

1. **Nothing new this round.** The three findings were narrow, and the fixes are
   local. If that is also your read, the remaining question is whether
   `SCHEMA_VERSION = 1` with one qualified runtime is enough to authorise
   implementation — which is a judgement about scope rather than correctness.
2. **S-Q7 unchanged**, and now a gate users hit.

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

---

## 16. Round 6 review disposition

**Verdict: architecture approved; v7 deferred.** 8 blocking findings and 3
specification corrections. **All taken.** **Two were design defects, not
instrument defects** — the first time since round 3.

| # | finding | closed by |
|---|---|---|
| 1 | migration output authorises itself | **§4d-0** — the destination requirement is independent of the migration; a failing result is a build error, not a new accepted manifest. Measured: an empty `v1->v2` was accepted as a valid version 2. **S50** |
| 2 | declared SQL acts outside the manifest | **§4d-i** — authorizer denies `SQLITE_PRAGMA` and anything outside `main`; `sqlite_temp_master` asserted empty. Measured: a `TEMP TRIGGER` left the manifest byte-identical and deleted every inserted row; `writable_schema` stayed on. **S51, S52** |
| 3 | the package fails its own runtime test | **§4a-viii** — the 3.46.1 claim is **withdrawn**, and the two questions are split: recorded-evidence validity always runs, *this runner is qualified* skips. **My README claimed 41 passed; on your runtime it was 40 passed, 1 failed.** **S56** |
| 4 | qualification can succeed with no evidence | **§4a-viii** — completeness is a precondition; key set must **equal** the declared versions; migration-path digests recorded too. Measured: `all()` over an empty mapping is `True` |
| 5 | `--runtime --write` does not write | **Implemented**, refuses incomplete records, and tested. Measured: the artifact checksum was unchanged. **S55** |
| 6 | `SCHEMA_VERSION` not bound to the registry | **§4d-ii** — `validate_registry()` requires it to equal `max(SCHEMAS)` over a contiguous range, and no migration at or beyond it. **S53** |
| 7 | missing legacy evidence fails open | **§4-i** — the empty set, so a nonempty unstamped store is refused when the evidence is unverified. **S54** |
| 8 | the shared kernel is too narrow | **Widened**: `schema_model` **and** `schema_migrations` **and** runtime-evidence validation. Only git probing, release enumeration and presentation stay outside |

**Specification corrections, all applied:** three stale `schema_manifest.py`
references removed **and gated** by a new check; `audit_sink` typed as
`Callable[[AdoptionAuditEvent], None]`; the 4096-byte cap defined as a
**validation limit, not truncation**, which resolves the "verbatim" conflict;
and the `diff` distance metric frozen as typed-key disagreement count with
declaration-order tie-breaking.

**Not adopted, and flagged rather than argued:** the typed
migration-operation model. §4d-i closes both measured holes with confinement;
the algebra is a larger design than this round should carry, and §9 asks
directly whether that is the wrong call.

---

## 17. Round 7 review disposition

**Verdict: architecture approved; v8 deferred.** 8 blocking findings and 4
corrections. **All taken.**

| # | finding | closed by |
|---|---|---|
| 1 | the destination contract rejects a normal `ALTER` | **§4d-0 — capability, not DDL text.** Structural comparison via `table_xinfo`; the digest still records exact text. Measured: a correct `ALTER` was rejected by v8. **S57** |
| 2 | migration evidence qualifies vacuously | **§4a-viii** — the migration key set must **equal** the declared paths. Measured: `{}` and `{"999": "bad"}` both passed. **S60** |
| 3 | only one path per destination can be recorded | **§4a-viii** — paths keyed `v<base>:constructor->v<dest>`, all enumerated. **S60** |
| 4 | a second runtime's manifests cannot be preserved | **§4a-viii** — accepted manifests are the **union** across qualified runtimes; records carry full object records, and adding merges rather than replaces. Measured: v8 dropped a foreign manifestation. **S58** |
| 5 | feature probes do not test the named behaviour | **§4a-viii** — behavioural probes. The `STRICT` probe used invalid SQL; the DDL probe checked only row existence; the authorizer probe checked only callability. **S62** |
| 6 | the policy vocabulary is open, and a typo bypasses validation | **Closed enums**, validated before generation, `rebuildable` only for indexes. Measured: `"requried"` plus incompatible DDL gave **no problems at all**. **S59** |
| 7 | the release `result` is not re-derived | **`AUTHORITATIVE` includes it**, and the gate compares the freshly probed value. `write_runtime()`'s return code is propagated. **S61** |
| 8 | the production boundary still contradicts itself | **One statement, in all three places** — shared: registry, matching, migration declarations and confinement, runtime-evidence validation |

**Corrections applied:** S30's stale `--selfcheck` reference removed and its
claim narrowed to what it tests (S57 covers the `ALTER` case); the rebuildable
absence rule reconciled — absence is repairable drift and the accepted
manifestation is captured **after** repair; migration runs only on a
Veracium-owned connection with no pre-existing authorizer, stated because Python
exposes no portable getter for a prior callback; S-Q7 remains a release gate.

---

## 18. Scope cut, 2026-08-03

**Not a review round. A product decision.**

Asked for and granted after seven external rounds produced ~63 findings, the
large majority in migration machinery with **no users**: `MIGRATIONS` empty,
`SCHEMAS` with one member.

| | |
|---|---|
| **`0007` keeps** | stamp on create · refuse newer/invalid/foreign/stamped-wrong · adopt the one historical unstamped shape · index drift repair · runtime qualification · the audit events |
| **inherited by** | `0013` — a dedicated spec. *(v10 first put it in `0006` §0b; round 8 showed the gate could not express that dependency.)* |
| **Preserved** | `specs/archives/0007-v9-20260803T0056Z.tar.gz` — full v9 text, the migrations module and its tests. **The conclusions themselves are stated in full in `specs/0013` §4**, not left in an uncommitted archive (round 8, non-blocking) |
| **Deleted here** | §4d and subsections · the `migration-*` reasons · sixteen migration-borne invariants · the `schema_migrations` module · the migration tests |

**What the cut does not change:** the acceptance model, typed object identity,
the digest and drift split, candidate-based resolution, the structured registry,
runtime qualification by evidence, and the lock-before-read protocol. **Six
rounds of architectural approval stand.**

**Why it was right, stated plainly rather than defensively.** Landing a
mechanism before its first user meant every round found defects in code nothing
called, and fixing them introduced the next round's defects. Round 7's finding 1
— a correct `ALTER` rejected by the check added in round 6 to protect it — is
the clearest example. **`0013` will hold the migration contract to a real
migration**, which is the thing this spec could never do.

---

## 19. Round 8 review disposition

**Verdict: scope cut approved; v10 deferred.** 5 blocking findings, 2
non-blocking. **All taken.**

| # | finding | closed by |
|---|---|---|
| 1 | the cut broke `0008`'s prerequisite | **`specs/0013`** — `0013` requires `0007`; `0006`/`0008`/`0009`/`0010` require both. **Verified against a clone**: the accepted `0008` is refused by name for both. **The most serious defect the cut introduced** |
| 2 | a fabricated manifestation is accepted | **`runtime_record_problems()` validates `manifestations`** — exact key set, and each must hash to its recorded digest; `build_version_artifact()` consumes only passing records; `--check` validates every stored record. Re-probed: rejected |
| 3 | qualification is not atomic | **both artifacts written or neither**, with the runtime file restored on failure. A stale-algorithm record is *superseded, not fraudulent* — reported, contributes nothing, does not deadlock regeneration |
| 4 | the cut was incomplete | `capability_problems()` removed from the kernel; normative text corrected; **the module gate widened to bare names**, which caught the stale reference immediately |
| 5 | the historical claim is overstated | narrowed to *every released codebase, probed under the qualified runtime*; the refused population is no longer claimed empty |

**Non-blocking, both taken:** S-Q7 remains a release gate, not an acceptance
blocker, and is stated as such; and **the inherited conclusions are stated in
full in `0013` §4** rather than depending on an uncommitted archive.

---

## 20. Round 9 review disposition

**Verdict: narrowed design approved; v11 deferred.** 3 blocking findings, 4
corrections, 4 rulings. **All taken.**

| # | finding | closed by |
|---|---|---|
| 1 | a self-consistent fabrication is still accepted; conflicting identities undetected | **three layers** — a declared-objects check on every manifestation, artifact-level identity uniqueness, and **attestation**: a record contributes only if this process reproduces it. Both cases re-probed and now rejected. **S58 renamed**, **S63**, **S64** |
| 2 | qualification is not atomic; the claim is false | **validate in memory, stage both, rename back to back, roll back the first if the second fails.** Reproduced with a simulated disk failure; re-probed clean. **The residual two-rename window is stated**, with the git commit as the honest boundary |
| 3 | migration ownership is contradictory | **`0013` throughout** — header, field contracts, decision table, §4-i, §4f, claims, disposition, `schema_model`. Historical passages are past-tense |

**Corrections:** the acceptance-model wording is constructor-only in current
sections; `PRAGMA user_version` is "written on create and adopt", not "migrate";
artifact-level uniqueness has its own invariant; and `write_runtime()` reports
active, superseded and invalid records separately instead of counting
superseded ones as qualified.

**Rulings recorded in `0013` §10:** M-Q1 — **wait for `0008`'s `confirmations`
table**; M-Q3 — the capability comparison belongs in `0013`, and
`capability_problems()` is already out of `0007`'s kernel. Stale-versus-invalid
approved directionally. S-Q7 remains a release gate — **and is now load-bearing
for correctness**, since the matrix is what would attest a second runtime.

---

## 21. Round 10 review disposition

**Verdict: core design approved; v12 deferred.** 3 blocking findings, 4
corrections. **All taken.**

| # | finding | closed by |
|---|---|---|
| 1 | the runtime predicate ignores artifact conflicts | **`runtime_supported()` validates the artifact first.** The generator caught it; the store opening a shipped artifact did not. **S65** |
| 2 | the union cannot be constructed | **one active runtime identity**, a second refused, the union claim withdrawn and S-Q7 given the widening. `SystemExit` also escaped the handler written to catch it. **S66** |
| 3 | the constructor-only pass is incomplete | migration-path digests and confinement probes out of the runtime table; feature probes scoped to schema matching; every present-tense `0006` ownership statement now `0013` |

**Corrections:** the publication rollback had **no test** and v12 shipped a
stray `.tmp` inside the review package — both now covered, and the claim
narrowed to **best-effort working-tree rollback**; reporting distinguishes
attested / unattested / superseded; and the historical-coverage wording is
narrowed in both places, with the availability limit stated.

---

## 22. Round 11 review disposition

**Verdict: core specification approved; v13 deferred.** 3 blocking findings and
3 corrections. **All taken.**

| # | finding | closed by |
|---|---|---|
| 1 | three incompatible definitions of runtime identity | **one canonical five-field key** for uniqueness, one-active enforcement, replacement, attestation and reporting; two records describing one build inconsistently reject the artifact. Replacement is by build, so a bump can be cleared; a different build is refused. **S66** |
| 2 | the predicate attests digests, not manifestations | **complete constructor manifestation compared**, exact key set required. The acceptance digest excludes rebuildable objects by design, so digests alone attested nothing about them. **S69** |
| 3 | the `SCHEMA_VERSION`/`SCHEMAS` guard regressed in the cut | **restored in `validate_schema_registry()`** — a consistency condition of `0007`'s own registry. **S70**. The citation gate caught the stale reference to its retired predecessor on the first attempt |

**Corrections:** the migration-path coverage paragraph is historical and
attributed to `0013`; the manifest procedure is constructor-only; a missing
`schema_versions.json` fails the gate (**S71**); `strict_tables` is identity,
explicitly not a required behaviour.
