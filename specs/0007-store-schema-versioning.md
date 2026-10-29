# Feature spec: on-disk store schema versioning

Spec-Status: accepted
Folds: 0013/0007-sqlite-attestation

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **accepted 2026-08-03 15:57 UTC** — under `PROCESS.md` §4a, on the round-14 external
> verdict *"v16 approved for acceptance"*, after **14 external rounds**. The
> three non-blocking corrections named at acceptance are applied in the same
> commit. **Scope: stamp · refuse-newer · adopt-v1** — the migration contract is
> `specs/0013`'s, still `draft`, so **`0006`/`0008`/`0009`/`0010` remain blocked
> by the gate**; what `accepted` authorises is implementing **this spec's own
> versioning layer**, the first implementable spec in the corpus.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v23.2.1 — 2026-10-29: INV-SA6's mutant column gains v23.2's mutants (dev, anchoring the carriers).** v23.2 added its clause to the invariant column only, so the INV-SA table demanded no carrier for either round-4 closure; every earlier version (v19, v21, v23) added its mutants beside its clause. Eight mutants, each already in the writer or job matrix and killed. No other change. **Prior: v23.2 — 2026-10-29: the round-4 closures stated (SA-R4-01, SA-R4-02).** Two sentences the round-4 verdict found narrower in the code than in the text now carry their predicates. (1) The exit-status rule no longer lets A10's failure alone make a `bootstrap-pending` record from a suite process that did not complete: every record-producing outcome needs a completion record from a process whose `pytest.main` RETURNED (§4d). (2) "Malformed", in the fresh write's refusal, is defined as rejection by this revision's artifact validator over the ORIGINAL artifact, superseded records excepted by S74 (§4d). INV-SA6 and the cells follow. **Prior: v23.1 — 2026-10-28: where the job's collection record is taken (research's stage 2 on the fix batch).** v23 had the plugin record the items in a first-run `pytest_collection_modifyitems`. A conftest's own first-run implementation registers later and runs before it, so it could drop a failing test that neither the record nor the JUnit then held: pytest exited 0 and no node differed (measured on a fixture; the suite's own conftest hook is last-run and only reorders). The plugin now records each item as pytest collects it, before any `pytest_collection_modifyitems` implementation of any priority, and writes the list when collection finishes. §4d, its cells and INV-SA6 say so; the one residual is stated. Nothing else changes. Prior: v23 — **v23 — 2026-10-28: the round-3 implementation verdict's I4 and I5 findings, as rules (verdict banked at coordination `c1ea30b`: SA-R3-02, SA-R3-03 and SA-R3-04; research's stage-1 read of their classes).** The verdict withheld implementation acceptance; the round-2 design acceptance stands, and no outcome of the design changes. Three statements were narrower than the guarantees they serve, and the code implemented them as written. (1) §4d's node set was compared as a set of modules. It is now bound as a multiset of node ids, collected in the job's own invocation before any deselection, and the job refuses an inherited environment that can shape collection or load plugins. (2) The suite's exit status was not consumed; it now is, beside the JUnit, and so is `HEAD`'s git exit. (3) The fresh write's “keeps every other step” listed only some steps. It now refuses a future or malformed record of any key, and runs the ordinary merge over the ORIGINAL artifact, before it drops anything. INV-SA6 and §4d's cells gain the matching rows. The closed outcome set is unchanged, and 0013 v38 carries SA-R3-01. Prior: v22 — **v22 — 2026-10-27: what the first branch run found (run 1 wrote no record), and two corrections to v21's bootstrap.** §4d gains three things. (1) The suite selection is closed under the joint test groups: the seam model's store driver was selected without its companion, and that group's gate failed every job. (2) A build that verifies with an unreadable key field ends `unattestable` (exit 0) after its re-derivation, which does not need the key. (3) `PT_INTERP` is read wherever it lies: the reader's fixed window read none of python-build-standalone's aarch64 and musl builds, and research's measurement answers v0.12's open question about uv on musl. From research's stage 2 of the bootstrap (§4d, the bootstrap): the bootstrap mark is the exemption's own test, not a second wording, and the fresh write refuses a new record that is itself a bootstrap record, whatever the input's form. INV-SA6, INV-SA12 and §4g.7 gain the matching rows. The path evidence's build-naming label (also run 1) was a code defect under 0013 §5f.3's existing text, so 0013 is unchanged. Prior: v21 — **v21 — 2026-10-27: the attestation bootstrap (the owner's ruling, “Two runs, bootstrap”), and two items queued from I5.** A10's committed-evidence node runs inside every attestation job and fails while no current record exists, so no job could pass and no first record could be written (dev's find while implementing I1–I7). §4d gains the bootstrap: at a zero-current state, which recurs at every manifest-algorithm or schema-version bump, the job exempts exactly that node, as the new outcome `bootstrap-pending`. Run 1's records seed the path-evidence regeneration and never ship. Run 2, at the next commit, runs with the exemption void, and its records are written as a fresh artifact. That write is the one bounded exception to “merge, never replace”, and release refuses a bootstrap record, which is derived from history, not stored. INV-SA6 and §4g.7 gain the matching rows. Queued from I5: provenance names a job by its matrix index, and §4g.9 states that a record does not carry its dependency set. 0013 is unchanged: §5f.3 already covers both runs. Prior: v20 — **v20 — 2026-10-26: the retired legacy record class's citations are mapped to their replacements, and a record's commit is defined.** I4 (A) (dev's `3ae54aa`) deleted the legacy runtime record class and its readers, and with them 27 tests cited by 19 S-rows (S36, S47, S55, S56, S58, S63–S69, S72–S78), 16 of them on rows that state their tests run. Each of those rows now cites the tests that check its rule over attestation records, the attestation writer or the manifestation validator, with a (v20) note; S47, S56 and S66 keep their v17 withdrawals. §4g.6 4f lists every retired test once, with its rows. §4g.6 4d gains one rule from I4's writer side (W1): every provenance entry's commit is equal, and that one commit is the record's commit, which the writer requires to be the checkout's `HEAD`. No outcome changes. Prior: v19 — **v19 — 2026-10-26: across runs, a re-record of one attestation key is ordered by commit ancestry (§4g.6, 4d), on the owner's word (2026-10-26, “Approve; fold now”).** The finding is from research's stage-1 read of I1–I7, item 10(e), accepted by dev. v18 applies “merge, never replace” over the full key but states no order between runs, and I4's “a later suite revision” has no definition of “later”. Read that way (item 10(e)), the frozen rule ADMITS a run of an OLDER commit replacing a newer commit's record of the same key, with rc 0: S75's class, on the result-digest field. That is a reading of the rule, never observed in a run. The writer now decides in a fixed order: (1) S75's monotone check. (2) Whether ancestry is answerable. It refuses “unanswerable” when there is no `git`, when it is not inside a repository, in a shallow clone, or when either id is not a full hex id in the repository's object format. (3) The same commit: idempotent with equal evidence; a refusal with different evidence. (4) `git merge-base --is-ancestor`: exit 0 replaces; exit 1 refuses “not an ancestor”, naming the direction; any other exit refuses “unanswerable”. INV-SA6 gains the rule and its mutants. §4g.4's row 4 gains a dated annotation: from `d427822`, which deleted `schema_version.py`'s dead first copies, the module defines `artifact_problems` once, so the row's own grep prints one line. No other rule, invariant or outcome changes. Prior: v18 — **v18 — 2026-10-25: §4g.3 gains its adversarial column (0022 Q10; the owner's ruling of 2026-10-25, "Fix 0007 first, gate later").** Each of §4g.3's four rows now names its hostile input and at least one vector: a test node in `tests/test_store_versioning.py`, either existing or one the implementation writes under its frozen obligations (every INV-SA mutant is exercised), each forward one declared `owed_at_implementation` in the citation-debt ratchet in this adoption. No rule, invariant or outcome changes. Prior: v17 — **v17 — 2026-10-25: the SQLite attestation fold (amendment `0013/0007-sqlite-attestation`, v0.12.1, sha16 `134243c63b05845a`).** Its design was accepted at its external round 2 (2026-10-25; verdict banked at coordination `2b84ab5`) and by the owner (2026-10-25T19:10Z). The new §4g carries the amendment; §4's state table, §4a-viii, §4b, §6 (S36, S47, S56, S58, S64, S66, S69), §7, §8, §10 (S-Q7) and `## Review closure` are edited in place and point to it. Prior: v16. |
| **Status** | *see `Spec-Status:` — canonical.* Deliberately small and separable: it is a **prerequisite** of `0013` and of every schema-changing spec, not a part of any of them. |
| **Internal reviewers** | research — pending |
| **External review** | required — `store/sqlite.py` is guarded and a wrong adoption makes stores unopenable |
| **Review history** | *see `specs/STATUS.md`, generated from `specs/reviews.py`. No counts are stated here; a hand-maintained count drifted in `0008` and was found by the reviewer.* |
| **Decision + date** | **ACCEPTED** — external round 14, 2026-08-03; status set by dev under §4a · **v17: the amendment's DESIGN ACCEPTED** — its external round 2, 2026-10-25, and the owner's word; implementation acceptance is outstanding (I1–I7, `## Review closure`) |
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
| ~~no version check exists~~ | `grep -rn "user_version" src/veracium/` | **implemented 2026-08-03**, post-acceptance: `store/schema_version.py` carries the kernel and `SqliteStore` opens through the §4 table. The row is struck, not deleted — it was true for the entire review |
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
| **unsupported runtime** | ~~this runtime is not qualified by `sqlite_runtimes.json` (§4a-viii)~~ **v17: `runtime_status()` is `refused` (§4g.6, 4a)** | **REFUSE** `reason="unsupported-sqlite"` — checked **before** any of the rows below; an `attested` or `verified` build proceeds, a `verified` open with the unattested-build warning (§4g.6, 4e) |
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

> **v17 — amended by §4g (amendment `0013/0007-sqlite-attestation`).** A build is `attested`, `verified` or `refused` by measurement when a store opens (§4g.6, 4a and 4b), and CI writes one attestation record per measured build (§4g.6, 4d). `runtime_supported()` is replaced by `runtime_status()` (§4g.2). The paragraphs marked **WITHDRAWN (v17)** below are withdrawn by §4g.6, 4f; the rest of this subsection stands. **Kept:** the fail-closed totality of the predicate (round 13), the complete-manifestation rule (S69), conflict and duplicate refusal (S64, S65), and “merge, never replace” for records.

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
| constructor digests **and complete manifestations** | **the qualification rule, in one place:** build identity matches · the record is structurally valid · the constructor digest matches · **the complete constructor manifestation matches byte-for-byte, rebuildable objects included** (the acceptance digest excludes them by design, so digests alone attest nothing about them) |
| ~~migration-path digests~~ | **`0013`'s**, not `0007`'s. DDL rewriting is why a version can have several accepted manifests, so a runtime agreeing on constructors could still disagree on an `ALTER` path — but at `SCHEMA_VERSION = 1` there are no paths and this build records none |
| manifest algorithm, schema version | a record generated under a different algorithm or schema version qualifies nothing |

**AMENDED (v17; §4g.2, §4g.6 4b):** `runtime_supported()` matches version **and** source id **and** probes, then
**re-derives the constructor digests here** and compares. Anything else is
refused with `reason="unsupported-sqlite"`, **before** any version or shape
decision.

**The constructor key set must equal what the registry declares** — not merely
contain no extras. *(Historical, and `0013`'s to carry: v8 keyed migration
digests by destination version and returned after the first viable base, so only
one path per destination could be recorded, while different bases can produce
different exact output at the same destination. `0007` records no migration
paths, so it makes no claim about their coverage.)*

**WITHDRAWN (v17; §4g.6, 4f):** **`0007` supports exactly one active runtime** (round 10, finding 2). v9
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

**WITHDRAWN (v17; §4g.6, 4f — an unrecorded build is `verified` or `refused` by measurement):** **An unqualified runtime is a skip, not a suite failure.** v7 asserted
`runtime_supported()` unconditionally, so the entire adversarial schema suite
failed on an unrecorded SQLite. Those are two different questions and they are
now two different tests: *is the recorded evidence complete and self-consistent*
(always runs), and *is this runner one of the recorded runtimes* (skips, with
the command to fix it in the message). **S56**.

**WITHDRAWN (v17; §4g.6, 4f — the CI matrix of §4g.6, 4d discharges S-Q7):** **This remains deliberately narrow**, and narrow in the direction that fails
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
`"locked"`, `"unsupported-sqlite"` (v17: kept; raised only for a `refused` build, its message names the first point of disagreement and only remedies that ship, §4g.6, 4e). **The three `migration-*` reasons are
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

### 4g. The SQLite attestation (v17, amendment `0013/0007-sqlite-attestation`)

> **What this section adds:** the accepted amendment `0013/0007-sqlite-attestation` (v0.12.1, sha256 `134243c63b05845a…`; design accepted at its external round 2, 2026-10-25, verdict banked at coordination `2b84ab5`; the owner's acceptance 2026-10-25T19:10Z): a SQLite build is `attested`, `verified` or `refused` by measurement when a store opens, and attested by CI. 0007's guarantee is unchanged. The clauses it amends are edited in place and point here: §4's state table, §4a-viii, §4b, §6 (S36, S47, S56, S58, S64, S66, S69), §7, §8, §10 and `## Review closure` (which carries the implementation obligations I1–I7). **Within this section, a reference to “§1”–“§8” or “§4a”–“§4f” means the subsection labelled with that number here** (the amendment's own numbering, kept so its references resolve). **“§4c”, “§4c-ii” and “§4c-iii” mean the subsections labelled so in 0013 §5f**, which carries the migration side, with INV-SA10 and INV-SA11. The amendment's §9 (the reviewer's brief) and §10 (its open questions, all answered) are not folded; they stay in the reviewed bytes. A reference to 0007's own sections says “0007”.

**Amends:** 0013's `migration_attempted` event (one additive key, INV-SA11), §4f (two annotations, §4c-ii) and its 0013-PA1 closure evidence (v0.11: INV-SA10's commit-time gate, which asserts that every ladder write maps to a checked step), **(v0.12) 0013 §5c's runtime seam (the schema-runtime and migration-runtime qualification, and the path-evidence key and its cardinality: §4c-iii), M11, M12, M15 and M18 (as §4c-iii lists them) and §8a item 2's "runtime qualification"; and `specs/skip_inventory.py` (an attestation column, §4d)**, and 0018's sidecar writer (it copies the key); 0007 §4a-viii (the SQLite runtime), §4b's `unsupported-sqlite` remedy text, §6 rows S36, S47, S56, S58, S64, S66
and S69, §7, §8's SQLite limit, and §10's S-Q7 row. **Leaves 0007's guarantee unchanged:** a version-aware build never
opens a store whose shape it does not recognise. *Who* may run that check is what changes.

**The owner's ruling, verbatim (relayed first-hand by dev):** a NEW store is creatable on any SQLite build, with a
warning; refusal is kept only where the schema evidence cannot be verified; and as many common builds as possible are
qualified, each MEASURED, never inferred from its version. Marketing's census
(its outbox, sqlite-builds-census-2026-10-13) is the target list. The owner, 2026-10-13: *"We need to
support as many of the most common versions of SQLite as possible."*

#### 4g.1 Why (the amendment's §1)

##### 1a. The gate refuses builds that reproduce the schema exactly — measured

0007 §4a-viii qualifies a SQLite build only if `src/veracium/store/evidence/sqlite_runtimes.json` records its exact
identity (version, `sqlite_source_id()`, the feature probes). One build is recorded: Ubuntu 24.04's patched 3.45.1. Every
other build is refused with `unsupported-sqlite`. Released since 0.5.0 (2026-08-07), the requirement went undisclosed
until `f98a3a0`.

Research measured the gate on uv's CPython 3.14.7 (SQLite 3.53.1, python-build-standalone) at `af1e564`, with the
qualified build as control (research `99ced3ec`, specs/evidence/0007-sqlite-attestation/probe_build_reproduces.py and its output). At
`58dd7f6` (schema 16) dev re-ran the probe unchanged, and research re-ran it from its own archive, with the same result
(v0.11; specs/evidence/0007-sqlite-attestation/at-58dd7f6):

| on SQLite 3.53.1, at `58dd7f6` | result |
|---|---|
| the four feature probes | **equal** to the qualified record's |
| the constructor digest, rebuilt on the fly, for each of the 16 schema versions | **in the accepted set, 16 of 16** (15 of 15 at `af1e564`) |
| the complete manifestation (rebuildable objects included) for each version | **byte-equal to the qualified record's, 16 of 16** |
| `runtime_supported()` | **False**: the record's build identity is not this build's |
| opening a store the qualified build created | **refused**, `unsupported-sqlite` |
| creating a new store | **refused**, `unsupported-sqlite` |

So the refusal is decided by **identity alone**. The check that would show the build reads and writes the accepted
schema correctly already exists in `runtime_supported()`, but it runs only after an exact identity match.

##### 1b. It refuses existing stores, not only new ones

The gate runs at every open, before any version decision (§2c-ii row 1), so an unrecorded build opens no store at all.
The disclosure shipped at `f98a3a0` says other builds are "refused at store creation" (README, docs/index.md, docs/mcp.md;
row 9), which **understates** it: a user whose Python upgrade brings a different SQLite loses access to their existing
store. The disclosure correction is outside this amendment and is noted for the owner.

##### 1c. The remedy names a tool the wheel does not ship, and the diagnostic cannot run

The refusal's remedy is "regenerate the evidence there (schema_evidence.py --runtime --write)" (row 2). That script lives
under `specs/`, not in the wheel. `veracium doctor` has a runtime check (row 7), but it is unreachable on an unrecorded
build: doctor opens the store first, the open gate refuses, and doctor returns before the check runs.

##### 1d. The census by route: what Python 3.14 users actually load (v0.6)

Marketing re-measured the census by install route (its outbox, sqlite-builds-by-route-2026-10-13, marketing `d76df0a`;
the probe logs beside it). Most rows were MEASURED: each route's own Python 3.14 run in a container, x86_64 Linux,
recording `sqlite_version` and `sqlite_source_id()`. macOS and Windows rows were read from build sources. Findings that
bear on this amendment:
- **Twelve distinct SQLite versions** across 3.14 routes: 3.34.1 (RHEL 9 AppStream), 3.37.2, 3.40.0 (Amazon Linux
  2023), 3.40.1, 3.45.1, 3.46.1, 3.50.2 (Fedora 43), 3.50.4 (python.org, every 3.14 patch), 3.51.2 (Fedora 44), 3.53.1
  (python-build-standalone: uv, mise by default), 3.53.4 (Alpine 3.24, Debian testing, Ubuntu 26.10) and 3.54.0
  (Homebrew, conda-forge).
- **Ubuntu 26.04 LTS's DEFAULT `python3` is 3.14** (3.14.4, SQLite 3.46.1). A distro's default Python is a route
  wherever it meets the floor.
- **`sqlite_source_id()` does not separate distro builds:** Debian 13, Ubuntu 26.04 and RHEL 10 report one identical
  3.46.1 id (research checked the three raw probe lines: three library paths, one id). §4d's identity adds compile
  options.
- **Two routes load today's attested build exactly** (`setup-python` on ubuntu-24.04, deadsnakes on Ubuntu 24.04), so
  today's CI job cannot see the refusal, or the `verified` path (§6).
- **Most routes link SQLite dynamically** (apt, Homebrew, conda), so an operating-system package update can change the
  build under an existing store. Today that refuses the user's store on the next open. Under this amendment the next
  open re-verifies the new build (§5). Not measured: whether a distro security update changes the source id.
- Not covered: arm64, the Windows Store Python, Nix, openSUSE, Arch, usage shares.

#### 4g.2 Field contracts (the amendment's §2)

| site | today (0007 v16) | after |
|---|---|---|
| `runtime_supported()` | True iff a recorded build identity equals this build's AND its digests and manifestations reproduce | **replaced by `runtime_status()`**, returning one of `attested`, `verified`, `refused` (§4a), with a reason |
| the open gate in `open_versioned` | refuses unless `runtime_supported()` | proceeds on `attested` or `verified`; refuses only on `refused`. A `verified` open emits the unattested-build warning (§4e) |
| `sqlite_runtimes.json` | at most ONE active identity (S66) | **any number** of attestation records, each for one attestation key (§4d: the build identity and, v0.12, the measured `machine`, `system` and `libc`); still refused: a malformed current record, two records with one key and different evidence, and a duplicate |
| accepted manifests (`schema_versions.json`) | derived from the records this process reproduces (S58) | **unchanged, and no longer widened by any runtime record**: every build is held to the ONE accepted evidence set (§4d) |
| `StoreVersionError(reason="unsupported-sqlite")` | remedy names `schema_evidence.py` | the reason is kept; the text names the first point of disagreement and only remedies that ship (§4e) |
| `veracium doctor` | its runtime check is unreachable on an unrecorded build | the SQLite check runs **before** any store is opened, at `info` level for `verified`, `error` for `refused` (§4e) |
| 0018 `run_release_migration` preflight | outcome `unsupported-sqlite` unless qualified | outcome `unsupported-sqlite` only on `refused` |
| CI | one job family, Python 3.14 on `ubuntu-latest` | plus a build matrix (§4d) |

#### 4g.3 Untrusted inputs (the amendment's §2c)

| input | supplied by | treated as | adversarial |
|---|---|---|---|
| the SQLite build the interpreter loads | the user's environment | **untrusted**: its behaviour is measured on every open (§4b), never inferred from its version string | a build that reports an attested build's `sqlite_version` and `source_id` (a patched or forked SQLite) but fails a feature probe, or reads a near-miss as the accepted schema (INV-SA1, INV-SA2, INV-SA4). vector: `tests/test_store_versioning.py::test_inv_sa1_an_attested_identity_does_not_skip_verification`; vector: `tests/test_store_versioning.py::test_inv_sa4_a_build_that_cannot_tell_a_near_miss_apart_is_refused` |
| a store file on disk | anyone with write access | unchanged from 0007: matched against the accepted evidence, refused if it does not match. 0007 §8's limit stands (not integrity) | a stamped store with the wrong shape, opened on the attested build and on a `verified` build, the route the attested runner never takes (INV-SA3). vector: `tests/test_store_versioning.py::test_s16_a_stamped_store_with_the_wrong_shape_is_refused`; vector: `tests/test_store_versioning.py::test_inv_sa3_a_wrong_shape_store_is_refused_on_a_verified_build` |
| `sqlite_runtimes.json` | the package (written by the CI matrix) | **package data, not a capability**: a record can only remove the warning. It cannot widen what is accepted (§4d), so a forged record buys an unrecorded build nothing it would not already get by verifying | a forged record that matches the running build and adds a manifestation to the accepted set; two records with one key and different evidence (INV-SA5, INV-SA6). vector: `tests/test_store_versioning.py::test_inv_sa5_a_forged_record_cannot_widen_the_accepted_evidence`; vector: `tests/test_store_versioning.py::test_inv_sa6_one_key_with_two_evidences_poisons_the_artifact` |
| **(v0.12)** the attestation key's platform fields (`machine`, `system`, `libc`) | the running interpreter, measured (§4d) | **measured, never taken from a runner's label.** An unreadable field makes the build unattestable (at most `verified`), never a match | a record field not in canonical form (`AMD64`, `x86-64`, a `libc` taken from `platform.libc_ver()`); a Linux interpreter whose `PT_INTERP` matches neither loader (INV-SA12). vector: `tests/test_store_versioning.py::test_inv_sa12_a_non_canonical_record_field_poisons_the_artifact`; vector: `tests/test_store_versioning.py::test_inv_sa12_an_unreadable_platform_field_is_at_most_verified` |

#### 4g.4 Assertions about reach (the amendment's §2c-ii)

Commands run from the repository root, re-derived at `58dd7f6` (v0.11: dev's read, and research from its own archive,
equal line for line; earlier at `d273f19` and `af1e564`). **EXECUTED** = run and read; **READ** = the cited lines.

| # | assertion | command | result |
|---|---|---|---|
| 1 | the runtime gate runs at every open, before any version decision | `grep -n "if not runtime_supported():" src/veracium/store/schema_version.py` | READ: L1939 (in `open_versioned`) |
| 2 | the refusal's remedy names a script under specs/ | `grep -n "regenerate the evidence there" src/veracium/store/schema_version.py` | READ: L1944 |
| 3 | reproduction is checked only after an exact identity match | `grep -n -e "if build_identity(r) != build_identity" -e "if any(_constructor_digest(int(v)) != d" src/veracium/store/schema_version.py` | READ: L1597, L1601 |
| 4 | a second active build identity is an artifact problem | `grep -n "supports exactly one" src/veracium/store/schema_version.py` | READ: L1132, L1446 (the module defines `artifact_problems` twice, at L1081 and L1395; the later definition is the live one). **(v19, 2026-10-26):** from `d427822` the module defines `artifact_problems` once (L1210), and this grep prints one line, L1261; the row stays as read at `58dd7f6` |
| 5 | 0013's ALTER steps byte-match reviewed expectations and refuse otherwise | `grep -n -e "the expectation never moves" -e "the expectations never move" src/veracium/store/migration.py` | READ: L352, L380, L406 |
| 6 | doctor exits 1 on any warning-level finding | `grep -n "return 1 if any(f.level in" src/veracium/doctor.py` | READ: L149 |
| 7 | doctor's runtime check runs only after a store opens | `grep -n -e "def _check_runtime" -e "_check_runtime(rep)" src/veracium/doctor.py` | READ: L661, L710 (the snapshot refusal returns at L683, before the check) |
| 8 | CI runs one Python, on one runner image | `grep -n -e "python-version" -e "runs-on" .github/workflows/test.yml` | READ: L14 (the job name), L19, L34, L62, L85 (all 3.14); all four jobs `runs-on: ubuntu-latest` (L15, L55, L80, L95) |
| 9 | the shipped disclosure says "refused at store creation" | `grep -n "refused at store creation" README.md docs/index.md docs/mcp.md` | READ: no match at `58dd7f6` (nor at `d273f19`), because the disclosure was corrected (Q3). At `af1e564`: README L61, docs/index.md L13, docs/mcp.md L15 |
| 10 | an unrecorded build that reproduces the schema is refused, at open and at creation | research's build-reproduction probe (research `99ced3ec`) | EXECUTED at `58dd7f6`: on 3.53.1, 16 of 16 digests accepted and manifestations equal; both opens refused. Control on the qualified build: both open |

#### 4g.5 Trust classes, authorization and scope (the amendment's §3 and §3b)

| trust class | touched? | how |
|---|---|---|
| user | no | no fact, edge or record changes class; the amendment decides only whether a store opens |
| third_party | no | untouched |
| system | no | untouched |
| assistant | no | untouched |
| the store file's shape | **yes, unchanged in rule** | it is matched against the same accepted evidence. Only the set of builds allowed to run the match grows |

##### 3b. Authorization and scope

No new capability is granted to any caller. A build gains the ability to open a store only by reproducing, on that open,
the evidence a recorded build would be held to. The amendment touches `src/veracium/store/schema_version.py`,
`src/veracium/store/release_migration.py`, `src/veracium/doctor.py`, the evidence generator and CI. **(v0.12)** Specs-side, it also touches the 0013 model (`specs/migrations_0013.py`, §4c-iii), the census instrument behind INV-SA10's commit-time gate (§4c), `specs/skip_inventory.py` (an attestation column) and the two test skips the record rule strands (§4d). It does not touch
`store/sqlite.py`.

#### 4g.6 Behaviour (the amendment's §4)

##### 4a. Three outcomes, decided by measurement

On every open, before any version or shape decision (where today's gate runs), the store computes `runtime_status()`:

| status | when | the open |
|---|---|---|
| **`attested`** | this build's identity has a current attestation record (§4d) **and** verification (§4b) passes | proceeds, silently |
| **`verified`** | no attestation record matches, **and** verification passes | proceeds, with the unattested-build warning (§4e) |
| **`refused`** | verification fails at any step | refused, `unsupported-sqlite`, naming the first failing step |

**Verification runs for every build, attested or not.** A record never replaces the measurement; it adds provenance.
That is today's behaviour for the recorded build (`runtime_supported()` re-derives its digests on every call), extended
to every build. A record whose identity matches but whose evidence does not reproduce is `refused`, as today (S69).

##### 4b. Verification: the build must read and write the accepted schema, and must still tell a near-miss apart

Three steps, in order, each total and fail-closed (any exception is `refused`):

1. **Feature probes.** The two 0007 requires today: `preserves_ddl_body` and `xinfo_exposes_generated` must be True.
   (`strict_tables` and `generated_columns` stay recorded, not required, as today.)
2. **Reproduction.** For every declared schema version, the constructor rebuilt in memory must produce a digest in that
   version's ACCEPTED set, and a complete manifestation, rebuildable objects included, byte-equal to the accepted one.
   This is the check `runtime_supported()` already runs, now compared against the accepted evidence, not against one
   build's record.
3. **Discrimination.** Reproduction proves the build gives the right answer on the right schema. It does not prove the
   build still gives a DIFFERENT answer on a wrong one, and that is the failure 0007 §7 exists to prevent ("opening and
   silently misreading"). A small packaged set of near-misses is built in memory, each the head constructor with ONE
   change, and each must produce a digest or manifestation different from the accepted one. Required members: an added
   column; a changed declared type; a dropped rebuildable index; a changed index column; a changed `DEFAULT`; a column
   reordered within a table. They live in `src/` (package data), not `tests/`, so the check runs on users' machines.

**Cost:** the reproduction step already runs on every open today, on the recorded build. The near-miss set adds a fixed
number of in-memory builds. The result may be cached per process, keyed by the build identity, because a process cannot
change its SQLite build.

##### 4d. Attestation: one record per build, written by CI, widening nothing

**One accepted evidence set for every build.** 0007 v9 tried a union of manifests across runtimes and withdrew it:
nothing persisted which runtime contributed what (§4a-viii, S66). This amendment does not revive the union. **A build is
supported if and only if it reproduces the ONE accepted evidence set.** A build that writes or reads the schema
differently (for example, by normalising stored DDL) is `refused`, and supporting it is a separate design, not a record.

**An attestation record** (in `sqlite_runtimes.json`) states that the build passed the FULL schema suite in this
repository's CI, not only the open-time check. It carries:
- the build identity: version, `sqlite_source_id()`, the four probes and **(v0.6) a digest of `PRAGMA compile_options`** (v0.7: of its canonical form, sorted and newline-joined, read through the library the store's connections use), because one source id is shared by builds of several distros (§1d), so a record keyed without the options would attest builds CI never ran. **(v0.12, SA-R1-03) With the measured architecture, operating system and C library of the process that loaded the library, this is the ATTESTATION KEY:**
  - `machine`: `platform.machine()`, lower-cased, then mapped through a CLOSED alias map of exactly two entries, `amd64` → `x86_64` and `arm64` → `aarch64`. Every other value stays as lower-cased, so `i686`, `ppc64le` and `s390x` are each their own key. The result must match `^[a-z0-9_]+$`. The aliases exist because, once lower-cased, Windows reports `amd64` and `arm64`, and macOS reports `arm64`, for the instruction sets Linux reports as `x86_64` and `aarch64`.
  - `system`: `platform.system()`, exactly as returned, non-empty, matching `^[A-Za-z0-9_]+$`.
  - `libc`: on Linux, `glibc` or `musl`, read from the running interpreter's ELF `PT_INTERP` (`ld-linux-*` → `glibc`, `ld-musl-*` → `musl`), the method packaging uses for musllinux tags; never from `platform.libc_ver()`, which returns `('', '')` on musl CPython. On every other `system` it is the fixed token `none`. A Linux interpreter with no `PT_INTERP` (a statically linked executable), or with one matching neither pattern, has an unreadable `libc`. Each §4d row whose route can install a static interpreter states that its builds are at most `verified`. Which python-build-standalone build uv resolves on musl is measured before the matrix is written. **(v22, measured by research, parse-only, on uv's 3.14.9 downloads):** python-build-standalone's `aarch64-gnu`, `aarch64-musl` and `x86_64-musl` builds are dynamically linked, against `/lib/ld-linux-aarch64.so.1`, `/lib/ld-musl-aarch64.so.1` and `/lib/ld-musl-x86_64.so.1`, so each has a readable `libc`. Their `PT_INTERP` segments lie about 19 to 20 MiB into the file. A reader that reads a fixed window from the start of the file read none of the three, and gave each build an unreadable `libc` (the first branch run's arm64 row). `PT_INTERP` is read wherever its program header says it lies, and its bytes must be exactly the declared size and end in one NUL. A short, empty or unterminated segment is unreadable, never an empty name.

  A build with any of the three fields unreadable matches no record, and no job can record it. It is at most `verified`, and `veracium doctor` names the unreadable field. A record's field must be an exact `str` already in canonical form; any other value is malformed and poisons the artifact. **One definition:** the build side (what `runtime_identity()` reports, on a user's machine and in a CI job) and the record side (what `artifact_problems()` accepts) call ONE canonicalisation function, in `store/schema_version.py` beside `runtime_identity()`, which the CI writer imports. A second implementation is a defect.

  *Why `system` and `libc`, beyond the reviewer's `machine`.* Both are constructed counterexamples, not measurements. python-build-standalone bundles one SQLite pin for every platform (the table below), and ships gnu and musl Linux builds of it. Version, source id, probes and options may then be equal between Linux aarch64 and macOS arm64, or between glibc and musl. The key must not rest on their being different;
- the commit and the CI run and job that produced it. **(v21)** A job is named by its run id and its MATRIX INDEX within that run (`strategy.job-index`), never by GitHub's numeric job id; the index is unique within one run, which is all the provenance ordering needs;
- the runner image;
- the digest of the attestation suite's result (v0.12: defined below), and **(v0.12)** the sixteen confinement probe results, each True (§4c-iii), as provenance.
`artifact_problems()` drops the single-identity rule (S66) and keeps the rest, **over the full attestation key (v0.12)**: a malformed current
record poisons the artifact; two current records with one key and different EVIDENCE conflict; and two with one key and equal evidence are a duplicate and are refused. A record's evidence is its result digest and its sixteen confinement results. Its provenance (commit, run, job, runner image) is never compared.

**The CI matrix: one job per ROUTE TO A 3.14, on each OS it serves, each MEASURED (v0.4).** A Veracium user loads the
SQLite of whatever gave them Python 3.14, so the matrix's axis is the INSTALLER, not the OS (dev's restructuring). A
distro's SQLite reaches a Veracium user through a route that builds or packages 3.14 against it, so distros appear as
the images those routes run on. The owner's "as many of the most common versions as possible" is delivered here, read
as the common ROUTES to a 3.14: **the owner's ruling (Q5, 2026-10-13)**, and the matrix grows by adding a row.

**What the first implementation runs: the owner's ruling (Q4, 2026-10-15, v0.10).** The aim is to cover the SQLite versions most commonly in use.
- **Every row below that CI can obtain now.** Hosted runners and public container images reach all twelve census versions (§1d), so the first matrix runs each of them.
- **arm64 Linux for the python-build-standalone and official Docker rows.** The census was measured on x86_64 Linux. A Docker image on an Apple-silicon Mac, and an arm64 cloud host, run arm64 Linux. An arm64 build of one SQLite version is a different build, and an attestation keys on the build (INV-SA12).
- **The Windows Store Python stays LATER.** The reason is in its row.

**(v0.12)** Each job measures `machine`, `system` and `libc` as part of the attestation key (above), so a row's architecture is measured, not assumed from the runner's label.

**The Python floor comes first.** Veracium requires Python `>=3.14` (pyproject.toml). Each job first records its
interpreter's version. A row whose route does not reach 3.14 records "not a Veracium route", never a SQLite result,
because no Veracium user loads that SQLite through that interpreter. Each job then records the build identity it
measured, and the record attests that identity. The third column is the census's figure where one exists: a version
to compare against, never the result.

| route to a Python 3.14 | OS images | SQLite it loads (census figure, where known; the job measures it) |
|---|---|---|
| `actions/setup-python` (what most users' CI runs) | `ubuntu-24.04`, `ubuntu-22.04`, `macos-latest`, `windows-latest` | ubuntu-24.04: 3.45.1, today's attested build (M); ubuntu-22.04: 3.37.2 (M); macOS and Windows repackage python.org: 3.50.4 (S) |
| python-build-standalone: uv, mise by default, and Rye, PDM and hatch through it | Linux, macOS, Windows | its own bundled SQLite: 3.53.1, one pin for every platform (S; M on Linux x86_64, research `99ced3ec`) |
| python.org installers | macOS, Windows | bundled: 3.50.4, every 3.14 patch (S) |
| Homebrew `python@3.14` | macOS | Homebrew's `sqlite`, linked dynamically: 3.54.0 (S) |
| conda-forge `python` 3.14 | Linux, macOS, Windows | conda's `libsqlite`, floating: 3.54.0 (M) |
| pyenv and asdf source builds (and mise with `python.compile=true`) | the distro images below | each image's system `libsqlite3` (S); macOS not measured |
| the deadsnakes PPA | Ubuntu 22.04, 24.04 | the system library: 3.37.2 and 3.45.1, the latter today's attested build (M) |
| a distro's own Python 3.14: its DEFAULT `python3` where it reaches 3.14, or its `python3.14` package | Ubuntu 26.04 LTS (default), Fedora 43 and 44 (default), Alpine 3.24 (default), RHEL 9 and 10 (AppStream package), Amazon Linux 2023 (package) | 3.46.1, 3.50.2, 3.51.2, 3.53.4, 3.34.1, 3.46.1, 3.40.0 (M) |
| official Docker `python:3.14` images | `-bookworm`, `-trixie`, `-alpine` | built against the image's system library: 3.40.1, 3.46.1, 3.53.4 (M) |
| **arm64 Linux (v0.10, Q4):** python-build-standalone, and the official Docker `python:3.14` images | GitHub's arm64 Ubuntu runner; the `-bookworm`, `-trixie` and `-alpine` images on `linux/arm64` | not in the census, which was measured on x86_64 (the job measures it) |
| the Windows Store Python | Windows | LATER: not installable non-interactively on a hosted runner (dev to confirm by trying). It probably bundles the same SQLite as python.org's Windows installer, but nobody has checked |

A distro's DEFAULT `python3`, and macOS's `/usr/bin/python3`, are rows only if the floor check shows they reach 3.14.

Each job runs the attestation suite (below), the generator in attestation mode, and `--check-evidence` (§4c-iii),
then uploads its record. **A job whose build fails verification records that result, it does not fail the matrix**:
the census row becomes a documented `refused`, with the failing step. **(v22)** A build that verifies but has an unreadable key field is `unattestable`: no job can record it (above). Its job still runs `--check-evidence`, because the re-derivation is owed on every build that verifies (0013 §5f.3), and it does not need the build's key: the comparison leaves `generated_on` aside, and only GENERATING path evidence needs the key. A failed re-derivation is still a failed job. When the re-derivation passes, the job ends `unattestable`, naming the unreadable field, with exit 0 and a census row. It does not run the suite, which could buy no record. The set of attested builds is what CI measured,
never a version range.

**Aggregation within one CI run is deterministic (v0.12, SA-R1-03).** Several jobs can measure one key: `setup-python`
and deadsnakes on `ubuntu-24.04` both load the system 3.45.1. The aggregation step:
1. groups the run's attestation inputs (below) by full attestation key;
2. emits ONE record per key only if every job in the group has equal evidence. The record's provenance lists the
   contributing jobs (route, runner image, run id, job id), sorted by route, then image, then job id;
3. on any disagreement within a group (different result digests, or one job verifying while another of the same key
   is refused), emits NO record for that key and fails the aggregation step, naming every job in the group.
   Disagreement means the key does not identify the build: that is a finding, not a record.

Across runs, "merge, never replace" applies over the full key (§4f, kept).

**Across runs, a re-record is ordered by commit ancestry (v19).** Each attestation record carries the full commit id that wrote it, which is already provenance. **(v20):** every provenance entry's `commit` is equal, and that one commit is the record's commit; a record whose provenance names two commits is malformed (`test_a_record_whose_provenance_names_two_commits_is_malformed`). The writer refuses a record whose commit is not the checkout's `HEAD` (`test_real_the_records_commit_must_be_head`). When a current-revision record of the same full key exists, the writer decides IN THIS ORDER, and stops at the first step that decides:
1. **S75's monotone check** (manifest algorithm, schema version), unchanged.
2. **Is ancestry answerable?** `git` must be present, and the writer must be inside a repository. `git rev-parse --is-shallow-repository` must print `false`. Both commit ids must be full hex ids in the repository's object format (`git rev-parse --show-object-format`). If any of these fails, the writer refuses “unanswerable”, and `--is-ancestor` never runs. In a shallow clone, exit 1 from `--is-ancestor` is ambiguous: it is also what a TRUE ancestor gives when the path between them is cut.
3. **The same commit.** With equal evidence, the re-record is idempotent: the bytes are unchanged, rc 0. With different evidence it refuses, as §4d's in-run disagreement does: two runs of one commit that disagree mean the key does not identify the build. This step comes before step 4 because a commit is its own ancestor (`--is-ancestor C C` exits 0), so step 4 would silently replace.
4. **`git merge-base --is-ancestor <record's commit> <writing commit>`, in the full repository:**
   - exit 0: replace.
   - exit 1: refuse “not an ancestor”. The message names the direction by running the reverse call. If the reverse exits 0, the writing commit is OLDER. If it exits 1, the two are on sibling branches or the history was rewritten.
   - any other exit, from either call: refuse “unanswerable”.

No step is skipped, and a nonzero exit is never read as one class. Measured with git 2.43.0 (research's stage-1 read, item 10):
- In a shallow clone that holds a true ancestor's commit object but not the path between, `--is-ancestor` exits 1.
- An absent object, an unknown commit and a malformed id each exit 128.
- `--is-ancestor C C` exits 0.

Ancestry orders WRITES only: the conflict and duplicate rules above still never compare provenance. This is what I4's “a later suite revision” means (`## Review closure`). The attestation job checks out full history, as `test.yml`'s pytest job does today (`fetch-depth: 0`).

**Cells** are product tests at implementation, under §4g.8's Gate. There is one cell for each refusal: an older commit; a sibling branch; no `git`; a writer outside any repository; a shallow clone; an unknown commit; a malformed id; and the same commit with different evidence. Each cell asserts the MESSAGE, not only the refusal. The shallow cell asserts “unanswerable”, never “not an ancestor”. One more cell covers the same commit with equal evidence, which is idempotent (bytes unchanged, rc 0). Each cell is demonstrated red against the mutant that removes or reorders its arm. The shallow cell's mutant moves the shallow check after `--is-ancestor`. The same-commit cell's mutant moves step 3 after step 4.

**The attestation suite, by a rule a script computes (v0.12).** It is every `test_*` module under `tests/` whose AST either
imports one of `sqlite3`, `veracium.store.schema_version`, `veracium.store.migration`,
`veracium.store.release_migration`, `schema_evidence` or `migrations_0013` (at any depth, `import` or `from … import`),
or passes `schema_evidence.py` or `migrations_0013.py` as a string inside a call's arguments (loading the file by
path). A literal anywhere else admits nothing. The node set is pytest's collection of those modules. **(v22) The selection is closed under the joint test groups** (`specs/evidence/offline/JOINT-TEST-GROUPS.md`): a selected module brings every other member of its group. A group's gate reads state its other members record in the same process. With a member missing, the gate fails on every job, whatever the build, so a selection that splits a group can never pass. The first branch run measured this. Its store driver was selected, because it imports `sqlite3`, but its companion driver was not, so the seam model's runtime execution gate failed every job that reached the suite. Research measured the same at `ae98d42`: the selection run alone fails that gate, and the two drivers together pass it, 286 of 286. The groups document is the one carrier of the groups, and the rule reads it, or a cell asserts that the rule's list equals it. G2, a module collected whole, needs nothing more, because the job runs whole modules. The rule lives in
one committed script, and a gate asserts that the suite each CI job runs equals the rule's output at that commit.
- **At `58dd7f6` it selects 54 of the 250 test modules** (research's suite rule, specs/evidence/0007-sqlite-attestation/r1-repro-at-58dd7f6).
- **Why `sqlite3` is a root:** without it the rule selects 37 and misses direct SQLite users such as
  `test_0044_v1_readonly_db.py`.
- **Why string literals count only inside call arguments:** admitting any literal also took in
  `tests/test_spec_gate.py`, whose only reference is a skip-reason fixture string, which is repository governance
  and not a run of the model.

**(v23) What the job binds, beside the rule's modules** (the round-3 verdict, SA-R3-02 and SA-R3-03; research's
stage-1 read of their classes). The module comparison above is kept and runs first. Three bindings follow it:
- **The environment, at step 0, after the non-root check.** An inherited `PYTHONPATH`, `PYTHONHOME`, or any variable
  whose name starts with `PYTEST_`, refuses the job as `wrong-job-state`, naming the variables, before anything runs.
  Nothing is stripped, so the operator sees the refusal; every other variable is inherited. A refusal, not a node
  check alone: an inherited `PYTEST_ADDOPTS="-o python_functions=…"` shrinks pytest's own collection. A failing test
  is then never collected, pytest exits 0 with every selected module present, and that invocation's collection
  reports no deselection (research's stage-1 read). The verdict's `--deselect` is the same class. The suite's process
  gets exactly two additions to the environment: `PYTHONPATH`, naming a directory that holds only the collection
  plugin, and `VERACIUM_ATTESTATION_COLLECTED`, naming the file the plugin writes.
- **The nodes, as a multiset.** The collection plugin (`-p attestation_collect`) records each item's node id as
  pytest collects it (`pytest_itemcollected`), in the same invocation, before any `pytest_collection_modifyitems`
  implementation of any priority (a conftest's included) and so before any deselection, and writes the list when
  collection finishes. **(v23.1)** v23 recorded in a first-run `pytest_collection_modifyitems`; a conftest's own
  first-run implementation ran before it and could drop a failing test unseen (research's stage 2). The residual,
  stated: an item a conftest never creates (`pytest_pycollect_makeitem`) is invisible to any collection record;
  the committed rule's module check still sees a module that yields nothing. The JUnit's cases must equal that list as a multiset. A difference is `suite-mismatch`, naming how many
  were collected and not reported, reported and not collected, and reported more than once; a missing collection
  record is `suite-mismatch` too. Both lists come from one process, so no second collection is compared, and none
  replaces the run (the verdict: “a separate collect-only run must not replace execution of the full suite”).
- **The exit status, beside the JUnit, after the node check.** Exit 1 with no failing JUnit case is `failed-tests`,
  as a session-level failure (the verdict's witness: a session-finish error after the JUnit was written, exit 1, every
  case passed). Exit 0 beside a failing case is `suite-mismatch`. Any other status is `suite-mismatch`, naming it:
  2 interrupted, 3 internal error, 4 usage error, 5 no tests collected.
- **(v23.2) The completion record, after the exit status.** The exit status and the JUnit cannot tell a suite process
  that completed from one that ALSO failed after the JUnit was written (the round-4 verdict, SA-R4-01: A10's failure
  plus a session-finish error gave the same record and digest as A10's failure alone). So every outcome that produces
  a record (`evidence`, `bootstrap-pending`) also requires a **completion record** from the suite process, written only
  after `pytest.main` RETURNED, carrying the job's per-run nonce and the exit status, which must equal the process's
  own. A missing, stale or unequal completion record is `failed-tests`, naming it, and nothing is recorded. Only then
  does exit 1 with failing cases go on to the failure rules, so A10's node failing alone at a zero-current state is
  `bootstrap-pending` only for a suite process that completed (the bootstrap, below). **The limit, stated:** the
  record proves that `pytest.main` returned in that process; code inside the suite runs in the same process and could
  forge it, which is outside this spec's adversary (an honest failure, not a hostile suite).
  *v23.1's sentence, kept for the record:* "Exit 1 with failing cases goes on to the failure rules, so A10's node
  failing alone at a zero-current state stays `bootstrap-pending`."
- **`HEAD`.** The record's commit is read with `git rev-parse HEAD`. A nonzero exit is `wrong-job-state`, naming it.
  Before v23 it was read as the empty string, which the record validator refused as a confinement failure: red, but
  under the wrong outcome.

**Conditional skips inside the suite carry an attestation class.** A digest over raw `(node id, outcome)` would split
one build by environment. The reviewer's run measured this: on one identity (3.45.1), 46 pass→skip and 2 skip→pass
changes against the author capture, from git absence, root, the missing MCP extra and timezone. 8 of those 48 fall
inside the 54 modules, all of the `job` class below (`mcp` 2, git checkout 4, root 2), and the two timezone swaps fall
outside. At `58dd7f6`, 14 of `skip_inventory`'s 54 entries fall inside the suite. Each carries one class in a new
`skip_inventory` column, and a gate requires the column on every entry whose file is in the suite:
- **`key` (3):** the condition is a function of the attestation key or of the Python floor, so it fires identically
  for every job of one key. These are `no fcntl on this platform` (`system`), and two Python-version conditions that
  never fire at the floor.
- **`job:runs` (9):** the attestation job fixes the condition so the test RUNS:
  - both `geteuid` entries: the job runs non-root, and in a container as a created user;
  - the four git-checkout entries: a full-history checkout;
  - `mcp`: the job installs the extra;
  - both selection-conditional entries: the job runs the whole suite.

  The job asserts from its own JUnit, through `skip_inventory.reconcile`, that none of these fired. A job where one
  fired is **not an attestation input**: it is named and excluded, and it is not a disagreement. (A root job did not
  run the read-only-database tests, so "must agree" would attest a suite it did not run.) Dev's fresh-clone capture at
  the pin (full history, non-root, `[dev,mcp]`) shows none of the nine firing.
- **`rewrite` (2):** the condition presupposes the single-record rule this amendment withdraws (below).

**The result digest** is sha256 over the suite's sorted `(node id, outcome)` pairs from the JUnit, without timings.
Within one key it is deterministic: `key` skips are equal by construction, and `job` conditions are fixed, or the job
is excluded.

**Stranded rows.** Two schema-suite skips are conditioned on the record rule itself:
- `tests/test_migrations_0013.py` L677: "artifact records a different runtime identity" (in M11's
  reproduces-on-the-recording-runtime test);
- `tests/test_schema_model.py` L321–L323: `if not ev.sv.runtime_supported(): pytest.skip(… "is not a qualified
  runtime" …)`.

On every unrecorded build these skip exactly the tests an attestation job exists to run, so no new build could ever
pass the suite. Under this amendment each skips only when `runtime_status()` is `refused`, and the first re-derives
on any other build (§4c-iii, M11). A wider `git grep` census at `58dd7f6` finds 26 lines in 4 test files that call
`runtime_supported(`, `build_identity(`, `runtime_identity(` or `migration_runtime_supported(`:
`test_schema_model.py` 17, `test_migrations_0013.py` 6, `test_store_versioning.py` 2, `test_0042_sites.py` 1. It
finds readers, not forgetters. Each is read against the new predicate in the implementing commit.

**The bootstrap: two runs at a zero-current state (v21; the owner's ruling, 2026-10-27, “Two runs, bootstrap”).** A10's committed-evidence node, `tests/test_migrations_0013.py::test_the_committed_path_evidence_was_generated_on_an_attested_build`, is in the attestation suite. It fails whenever no current attestation record exists, because no path record's `generated_on` can then resolve (0013 §5f.3). Only a job whose suite passes writes a record, so without this clause no run could ever write the first one. **The state recurs:** every manifest-algorithm or schema-version bump makes every committed record superseded. This clause is the procedure for every such state, not a one-time step. Below, C0 is the commit run 1 tests, C1 the commit that adds run 1's records, and C2 the commit that adds run 2's.
1. **The exemption.** The job declares a BOOTSTRAP set of exactly one node, A10's above. That node's JUnit failure is exempt, and the job's outcome is `bootstrap-pending`, only when every record in the committed artifact at the job's checkout is superseded (an empty list included). A current, malformed or future record voids the exemption, and the failure is `failed-tests`: a poisoned artifact attests nothing, and poisoning it must not re-open the exemption. Only a `<failure>` of that node is exempt. An `<error>` on it, or any other failing node, is `failed-tests`.
2. **Run 1, at C0.** A `bootstrap-pending` job builds its record as an `evidence` job does, and its result digest is honest: the declared node is in it as failed. A run-1 record states that the suite passed except the declared node, at a zero-current state. In aggregation, a key whose jobs mix `bootstrap-pending` and `evidence` is a disagreement. The run's records are committed at C1 through the writer's ordinary merge, together with the path evidence regenerated on a build they attest (0013 §5f.3, Generation: the record is committed in the commit that adds the path records). **Run 1's records are never shipped**; they seed that regeneration only.
3. **Run 2, at C1.** The full suite runs, and the exemption is void because current records exist. The shipped artifact is run 2's records only, written at C2 as a FRESH artifact, never merged over run 1's. The fresh write is the one exception to “merge, never replace”, and it is bounded:
   - it refuses an aggregate that contains any `bootstrap-pending` job; **(v22)** and it refuses any NEW record that is itself a bootstrap record by the same derivation, whatever form the input takes. The aggregate's job names are one form; a bare list of records is another, and v21's form-keyed refusal took it;
   - it refuses unless every current record in the existing artifact is a **bootstrap record**: one whose own commit's committed artifact held no record current at that record's revision. **(v22)** “Held no current record” is the exemption's own test, run on that commit's artifact: every record superseded, with an empty list included. One function answers both, so an artifact holding only a future or malformed record is not a bootstrap state for either. In v21 the two were worded apart and implemented apart, and they disagreed on exactly those two artifacts. Every run at a zero-current state is a bootstrap run, so the mark is derived from history, not stored. A git failure, a shallow clone or an unreadable artifact at that commit is “unanswerable”, never “not a bootstrap record”. Without this bound, a fresh write at any later run would drop attested keys whose routes were unavailable that day;
   - it keeps every other step: production's record and artifact validators, answerability, the record's commit equal to `HEAD`, and the read-back as `attested`. **(v23)** That list was short, and the implementation applied it as written. The round-3 verdict (SA-R3-04) measured a fresh write over a same-key record of a NEWER revision writing, where the ordinary write refuses (S75); research's stage-1 read measured the same for another key's newer record, and for a malformed record, over which the ordinary write refuses as poisoned. Before it drops anything, the fresh write now: (1) refuses, bytes unchanged, when the existing artifact holds a future or malformed record of ANY key, naming it (S75 for a future one). **(v23.2)** "Malformed" means rejected by this revision's ARTIFACT validator run over the ORIGINAL artifact: a bad revision field, and equally a current record with a bad result digest, a missing or false confinement field, or an unexpected field, and a conflicting duplicate (the round-4 verdict, SA-R4-02; 0013 §5f.3 A12 already calls a false probe malformed). v23's sentence was wider than the check that implemented it (the revision classifier alone). A superseded record is outside "malformed" by S74's scoping: no validator of this revision judges an older format, and the fresh write drops it by design; (2) runs the ordinary merge over the ORIGINAL artifact as a dry run, so S75 on the same key, v19's order and the poison check apply; and only then (3) applies the two refusals above. It drops superseded records and bootstrap current records, and nothing else.
4. **Main fast-forwards to C2 only when C2's full suite is green.** At C2 the path evidence resolves by key against run 2's records, so a generating key that run 1 attested and run 2 did not fails A10 there, as 0013 §5f.3's rule for withdrawing a generating record already requires. Main then does not move.
5. **Release refuses a bootstrap record**, by the same derivation, beside S77's stale-record report. This check runs at release and is never a node of the attestation suite: as a node it would fail run 2 at C1, which still holds run 1's records, and re-create the deadlock.

**Cells** (§4g.8's Gate), each demonstrated red against its INV-SA6 mutant:
- zero current records exempts the node; a superseded-only artifact exempts it too;
- each of a current, a malformed and a future record voids the exemption;
- an `<error>` on the node is `failed-tests`; a second failing node is `failed-tests`;
- the BOOTSTRAP constant has one entry, and pytest collects it;
- a key mixing `bootstrap-pending` and `evidence` is a disagreement;
- the fresh write refuses a `bootstrap-pending` input; it refuses over a record that is not a bootstrap record; and on a shallow clone it refuses “unanswerable”;
- the release check refuses a planted bootstrap record.
- **(v23)** the fresh write refuses, bytes unchanged, over a future record of the same key (S75) and of another key,
  over a malformed record of another key, and when v19's order fails against the original artifact; a two-run
  bootstrap replacement still writes;
- **(v23.2)** the fresh write refuses, bytes unchanged, over a CURRENT record of the same key that the artifact
  validator rejects (a bad result digest, a missing confinement field, a false probe, an unexpected field) and over a
  conflicting duplicate; a superseded record with a bad digest is dropped, not refused (S74); the ordinary write's
  behaviour on all of them is unchanged. The job: A10's failure plus a session-finish error is `failed-tests` with no
  record, and so is a suite process that never returned (`os._exit` after an all-pass JUnit), a stale nonce, or an
  exit status unequal to the process's; the outcomes that produce a record are exactly `evidence` and
  `bootstrap-pending`, both after the completion check;
- **(v23)** an inherited `PYTEST_ADDOPTS` (`--deselect`, and `-o python_functions`), `PYTEST_PLUGINS` or `PYTHONPATH`
  is `wrong-job-state`, and nothing runs; a node missing inside a still-present module, an unexpected node and a
  node reported twice are each `suite-mismatch`, named; **(v23.1)** a conftest that drops a collected test, at any
  hook priority, is `suite-mismatch`;
- **(v23)** a real session-finish error (exit 1, every JUnit case passed) is `failed-tests`; exits 2, 3 and 5 are
  `suite-mismatch`, named; the bootstrap case stays `bootstrap-pending`; a failing `git rev-parse HEAD` is
  `wrong-job-state`.

##### 4e. What the user sees

**The warning (`verified`):** emitted once per process, through Python's `warnings` and the `veracium` logger:

> SQLite {version} ({source id, last 12}, {machine}, {system}, {libc}) is not one of Veracium's attested builds. Veracium verified this build when
> opening the store: it reproduces all {N} schema versions and tells apart all {M} near-miss checks. Its CI has not run
> the full schema suite on this build. `veracium doctor` lists the attested builds.

**The refusal (`refused`):** reason `unsupported-sqlite`, unchanged for hosts that branch on it. The text names the
failing step and only remedies that ship:

> SQLite {version} ({source id}) cannot be verified for Veracium's store: {the first failure — "feature probe
> preserves_ddl_body is False" | "schema v{N}: {type}:{name} differs from the accepted manifest" | "near-miss
> {name} was not told apart"}. The store was not opened. Use a Python whose SQLite is an attested build (`veracium
> doctor` lists them), or report this build to the project.

**`veracium doctor`:** reports the SQLite status **before** opening any store, so it works exactly when a user needs it. **(v0.12)** It lists each attested build with its `machine`, `system` and `libc`, and names any field of the running build's key that was unreadable.
It reports `attested` and `verified` at `info` level: doctor exits 1 on any warning (row 6), and an unattested but
verified build is not a store problem. It reports `refused` at `error` level, with the failing step and the list of
attested builds.

##### 4f. What this withdraws from 0007

- §4a-viii's "`0007` supports exactly one active runtime" and S66's single-identity refusal.
- S47's and S56's "an unrecorded runtime is not qualified": an unrecorded build is `verified` or `refused` by measurement.
- §8's limit "SQLite support is the recorded set, and it currently has one member", replaced by §8 below.
- S-Q7's release gate, which this amendment discharges: release requires the CI matrix to have run, not every census
  build to pass.

**What this withdraws from 0013 (v0.12, §4c-iii):** the migration-runtime record class, and with it the single-active-runtime policy in `migration_runtime_artifact_problems`; the runtime-identity component of the path-evidence key and of its expected set; and the requirement that a path record's runtime resolve to a schema-runtime record and a migration-runtime record. M15's `test_recorded_confinement_behaviours_must_reproduce_live` and M18's `test_a_malformed_current_migration_runtime_record_poisons` are retired, and M18's `test_a_foreign_identity_path_record_fails_the_artifact` is replaced (§4c-iii lists their replacements).

**Kept:** the fail-closed totality of the predicate (round 13), the complete-manifestation rule (S69), conflict and
duplicate refusal (S64, S65), and "merge, never replace" for records.

**(v20) Retired with the legacy record class** (I4 (A), dev's `3ae54aa`: `runtimes`, the interim predicate and every function that read the class are deleted). Each test below is retired, and its row now cites its replacement, or is withdrawn above: `test_this_runtime_is_qualified_or_explicitly_is_not` (S36, S56); `test_an_unrecorded_runtime_is_not_qualified` (S47); `test_a_matching_version_with_different_features_is_not_qualified` (S47); `test_writing_runtime_evidence_actually_writes` (S55); `test_the_recorded_runtimes_are_internally_valid` (S56); `test_an_empty_digest_map_does_not_qualify_vacuously` (S56); `test_an_unattested_foreign_runtime_contributes_nothing` (S58); `test_a_self_consistent_fabrication_is_rejected` (S63); `test_conflicting_runtime_identities_reject_the_artifact` (S64); `test_a_duplicate_runtime_record_is_rejected` (S64); `test_a_conflicting_artifact_disqualifies_the_runtime` (S65); `test_the_recorded_artifact_has_no_conflicts` (S65); `test_two_active_runtime_identities_are_refused` (S66); `test_one_canonical_identity_is_used_everywhere` (S66); `test_replacement_is_by_build_identity` (S66); `test_a_superseded_revision_of_the_same_build_is_replaceable` (S66); `test_a_staging_failure_publishes_nothing` (S67); `test_a_failed_publish_rolls_the_first_file_back` (S67); `test_staged_temporaries_are_not_left_behind` (S68); `test_a_modified_rebuildable_ddl_disqualifies_the_runtime` (S69); `test_a_missing_rebuildable_index_disqualifies_the_runtime` (S69); `test_a_mistyped_feature_is_rejected` (S72); `test_a_malformed_current_algorithm_record_poisons_the_artifact` (S74); `test_future_evidence_is_not_overwritten` (S75); `test_the_record_validator_is_total` (S76); `test_the_predicate_is_total_over_garbage` (S76); `test_superseded_duplicates_do_not_disqualify` (S77). The two tests that kept their names, `test_a_missing_declared_object_fails_the_record` (S73) and `test_an_extra_manifestation_field_is_rejected` (S78), now exercise `manifestation_problems` directly.

#### 4g.7 Regimes (the amendment's §5)

| regime | behaviour |
|---|---|
| the recorded 3.45.1 build | `attested`; unchanged |
| a build that reproduces the accepted evidence, with no record (measured: uv's 3.53.1) | `verified`: opens, creates, adopts and migrates, with the warning |
| the same build after CI attests it | `attested`; no warning |
| a build that stores DDL differently, or fails a required probe | `refused`, naming the step; today's outcome, with a true message |
| a build that reproduces the schema but fails a near-miss | `refused`: its matcher cannot be trusted to tell stores apart |
| an operating-system update changes a dynamically linked SQLite under an existing store (apt, Homebrew, conda) | today: refused on the next open. Here: the next open re-verifies the new build; it opens `verified` or `attested`, or is refused naming the step |
| a forged attestation record for some build | buys nothing: verification still runs, and a record widens no accepted evidence |
| a store migrated on a build whose ALTER output differs | the step refuses, `unsupported-migration`; the transaction leaves the store unchanged |
| **(v0.11)** a store migrated on a build where a data step's output differs | that step's postcondition refuses, `unsupported-migration`, naming the step; the transaction leaves the store unchanged. The same on `attested` and `verified` builds |
| **(v0.12)** a commit adds DDL outside the frozen class-(b) list, or a write SQLite's authorizer reports that no step claims, whatever its first word | the commit-time gate (INV-SA10) fails the suite |
| **(v0.12)** a `verified` build migrates in production | as an attested build: the same ladder, postconditions and `_validated_current`; neither installs a runtime authorizer (§4c-iii, carrier (ii)) |
| **(v0.12)** the 0013 model, on a build whose schema verifies but whose authorizer is weak | ordinary open proceeds; migration refuses `unsupported-sqlite`, naming the first failing probe (A3) |
| **(v0.12)** an x86_64 record, and an aarch64 build otherwise identical | no match: the build is `verified`, with the warning (INV-SA12) |
| **(v0.12)** two CI jobs measure one key and disagree | no record for that key; the aggregation step fails, naming both jobs (INV-SA6) |
| **(v22)** a build that verifies, with an unreadable key field (a loader launch, a statically linked interpreter) | `--check-evidence` re-derives as on any verifying build; the job ends `unattestable`, naming the field, with exit 0 and no record. A failed re-derivation is still a failed job (§4d) |
| **(v21)** the first CI run at a zero-current state: the first run, or the first after a manifest-algorithm or schema-version bump | A10's node is `bootstrap-pending`, and any other failure is `failed-tests`. Its records seed the path-evidence regeneration and never ship. A second run at the next commit, with the exemption void, writes the shipped artifact fresh (§4d, the bootstrap) |
| **(v0.11)** a commit adds a ladder write that maps to no checked step | the commit-time gate (INV-SA10) fails the suite; the write never ships to any build |

#### 4g.8 Invariants (the amendment's §6)

| | invariant | mutant that must fail |
|---|---|---|
| **INV-SA1** | every open computes `runtime_status()` before any version or shape decision, for every build | skip verification when an attestation record matches; decide shape first |
| **INV-SA2** | `verified` requires all three steps (§4b); any failure or exception is `refused` | accept on reproduction alone (drop discrimination); accept on probes alone; let an exception return `verified` |
| **INV-SA3** | reproduction compares against the ACCEPTED evidence, digest AND complete manifestation | compare digests only (S69's rebuildable-index hole returns); compare against the build's own record |
| **INV-SA4** | each required near-miss changes the digest or manifestation on the running build, and a near-miss that does not change it refuses the build | drop a near-miss from the set; treat an equal near-miss as a pass |
| **INV-SA5** | no attestation record widens the accepted evidence | let a record's manifestations join the accepted set (the withdrawn union) |
| **INV-SA6** | any number of attestation records with distinct attestation keys is valid; two with one key and different evidence, or a duplicate, poison the artifact; **(v0.12)** within one CI run, aggregation emits one record per key only when every attestation input measuring that key agrees, and a job whose `job`-class skip fired is excluded, not counted as a disagreement; **(v19)** across runs, a re-record of one key replaces the current record only when that record's commit is an ancestor of the writing commit and not the same commit. The same commit with equal evidence is idempotent. Every other case refuses, naming why: an older commit, a sibling branch, a same-commit disagreement, or ancestry unanswerable (§4d); **(v21)** at a zero-current state the attestation job exempts exactly A10's node, as `bootstrap-pending`, and nothing else; the fresh write that replaces the bootstrap records refuses unless every current record it drops is a bootstrap record and no input job is `bootstrap-pending`; and release refuses a bootstrap record (§4d, the bootstrap); **(v23)** the job's outcome is bound to the JUnit's node ids as a multiset equal to its own invocation's collection, to the suite's exit status, and to an environment that cannot shape collection; and the fresh write refuses a future or malformed record of any key and applies the ordinary writer's checks to the original artifact before it drops anything (§4d); **(v23.2)** "malformed" is rejection by this revision's artifact validator over the original artifact, superseded records excepted (S74); and every record-producing outcome requires a completion record from a suite process whose `pytest.main` returned, with this run's nonce and an equal exit status (§4d) | refuse a second key (S66, withdrawn); accept a conflicting pair; **(v0.12)** aggregate by majority or by the first job; compare provenance as evidence (two agreeing jobs become a false conflict); digest the suite result with timings (one build splits); drop the `job`-state assertion (one root job and one non-root job of one key disagree, and aggregation reports a false "key does not identify the build"); run a suite other than the rule's output; leave a `rewrite`-class skip in place (a new build's job skips its schema tests and attests on the rest); **(v19)** replace whatever the commit order (an older commit's run replaces a newer record: v18's behaviour); read any nonzero `--is-ancestor` exit as “not an ancestor” (a shallow clone then refuses a true ancestor and gives “older commit” as the reason); run `--is-ancestor` before the shallow check; take the same-commit step after the ancestry step (a commit is its own ancestor, so a same-commit disagreement replaces); compare provenance as evidence (ordering writes must not make provenance a conflict field); **(v21)** exempt a second node; exempt the declared node while the artifact holds a current, malformed or future record; exempt it only when the artifact is empty (the next bump's superseded records re-create the deadlock); exempt an `<error>` on the declared node; let the fresh write drop a record that is not a bootstrap record; let the fresh write accept a `bootstrap-pending` job; read an unanswerable bootstrap derivation as “not a bootstrap record”; ship a bootstrap record (the release check passes it); **(v22)** select a module without the other members of its joint test group (the group's gate fails every job); decide `unattestable` before `--check-evidence` (a verifying build's re-derivation is skipped); end the job red on an unreadable key field; derive the bootstrap mark by a test other than the exemption's; let the fresh write accept a new record that is itself a bootstrap record; **(v23)** compare the rule's modules only (a node removed inside a present module still gives `evidence`); inherit `PYTEST_ADDOPTS` or `PYTEST_PLUGINS` (an ini override shrinks the collection itself); discard the suite's exit status (a session-finish error after the JUnit is written gives `evidence`); read a failed `git rev-parse HEAD` as an empty commit; fresh refuses no future or malformed record (another key's is erased; the same key's reads as S75); fresh skips the dry run over the original artifact (v19's order is not applied); the superseded implementation: fresh checks only current records, then clears the list; **(v23.1)** record the collection in a first-run `pytest_collection_modifyitems` (a conftest's own first-run hook drops a failing test before the record sees it); **(v23.2)** fresh validates only the original's revision fields (a same-key current record the artifact validator rejects is erased); fresh validates the merged output, not the original artifact; fresh validates only other keys' records; fresh validates each record without the artifact-level check (a conflicting duplicate passes); a record-producing outcome without a completion record (a session-finish error after the JUnit reads `bootstrap-pending`); the completion record written from a sessionfinish hookwrapper (a conftest's tryfirst wrapper raises after it); a stale completion record (no nonce check); the completion record's exit status not compared with the process's |
| **INV-SA7** | a `verified` open emits the warning exactly once per process; an `attested` open emits none | warn on every open; warn on an attested build; never warn |
| **INV-SA8** | the refusal text names the first failing step and names no file outside the wheel | keep `schema_evidence.py` in the text; omit the step |
| **INV-SA9** | `veracium doctor` reports the SQLite status without opening a store, `info` for `attested`/`verified` and `error` for `refused` | report after opening (unreachable on a refused build); report `verified` at `warn` (doctor exits 1 for every uv user) |
| **INV-SA12** | **(v0.6)** an attestation record matches a build only if version, source id, the four probes AND the compile-options digest are all equal, **and (v0.12) canonical `machine`, `system` and `libc`, each from ONE canonicalisation function** | match on version and source id alone (one 3.46.1 record would cover Debian 13, Ubuntu 26.04 and RHEL 10); omit the compile options from the record; **(v0.7)** digest the options in the order the build returns them (one build becomes two); read them from a SQLite library other than the one the store's connections use; **(v0.12)** drop `machine` while every other field is equal (an x86_64 record attests an aarch64 build: the reviewer's constructed pair); drop `system` (a Linux aarch64 record attests a macOS arm64 build); drop `libc` (a glibc record attests a musl build of one pin); read `libc` from `platform.libc_ver()`; take `machine` from the runner's label; canonicalise one side only (a Windows build never matches its own record); widen the alias map (`i686` → `x86_64` makes a 32-bit build match a 64-bit record); let an unreadable field match a record with the same value; **(v22)** read `PT_INTERP` from a fixed window at the start of the file (python-build-standalone's aarch64 and musl builds read an unreadable `libc`); read a short or unterminated segment as a name |

**Gate:** each row is a PRODUCT test at implementation, demonstrated red against its mutant. **(v0.6) The `verified` and `refused` paths must be exercised on a route other than the attested one:** `setup-python` on ubuntu-24.04 loads the attested build exactly (§1d), so a suite run only there can reach neither path, except by forcing the predicate. The CI matrix (§4d) is its
own evidence: one attestation record per measured build, and a documented `refused` for each build that fails, with its
failing step.

INV-SA10 and INV-SA11 check 0013's code and are in 0013 §5f.4; the **Gate** above applies to them as well.

#### 4g.9 Failure modes, claims and limits (the amendment's §7 and §8)

##### 7. Failure modes and reversibility

**The failure 0007 exists to prevent is unchanged:** a build that cannot show it reads the schema correctly does not
open the store. What changes is that showing it no longer requires being on a list.

**The new residual, stated rather than minimised:** a `verified` build has passed the open-time checks, which are a
subset of the full schema suite. A defect in that build that the suite would catch, and the open-time near-misses do
not, would go unseen until CI attests the build or refuses it. The warning names this, and §4b's near-miss set is the
mitigation. Attestation closes it, per build.

**Reversible:** the amendment changes no stored byte. A store created on a `verified` build is the same accepted shape
an attested build creates (that is what verification checked), so it opens on every build that verifies.

##### 8. Claims and limits

**Claim:** every version-aware build refuses to open a store it does not recognise (0007 §8, unchanged), and **opens a
store only on a SQLite build that, on that open, reproduces the accepted schema evidence and tells apart the packaged
near-misses.**

**Limits:**
- **Not the full suite at open.** A `verified` build has passed a subset; only attestation runs the whole suite (§7).
- **INV-SA10 sees the writes the campaign's fixtures reach (v0.11.1).** Its site check finds an `execute` never
  observed. It does not find a write inside a helper whose only call sits on a branch no fixture reaches; that needs
  line coverage. Research measured line coverage of the functions the ladder enters, over the 48 paths and all 1,480
  campaign cells at `58dd7f6` (specs/evidence/0007-sqlite-attestation/at-58dd7f6, §4). In `store/migration.py` 81 lines never execute.
  31 sit in a block that ends in `raise`. Of the other 50, 40 are problem-report lines in the postcondition functions
  and 10 are paths: a non-outcome episode on a base-1/2 store (`_migrate_outcome_chains`), an episode json that does
  not parse, the `migration_committed` audit path (the campaign runs with no `audit_sink`), and one line in `_older`.
  A line-coverage gate would therefore refuse the correct tree until fixtures reach those paths and a second exemption
  covers the problem reports. It is not part of INV-SA10, and the class stays in §9's attack points. The 50 is this
  campaign's scope; the wider suite may run some of those lines, which this document does not measure.
- **One accepted evidence set.** A build that stores the schema differently is refused, not adapted to.
- **The census is by install route, mostly measured on x86_64 Linux** (§1d), and it is a list of versions with their
  source ids. Which builds VERIFY is what the CI matrix measures; this document predicts none of them beyond the one
  measured `verified` build (3.53.1). The census does not cover arm64, the Windows Store Python, Nix, openSUSE, Arch or
  usage shares. From v0.10 the matrix runs arm64 Linux (§4d, Q4). The Windows Store Python is LATER. Nix, openSUSE,
  Arch and usage shares remain uncovered.
- **(v0.12) Class (b) is a closed list of statement texts** (§4c); a statement outside it owes a step, a
  postcondition and cells. **0013-PA1's census has been re-measured with SQLite's classification** (C1: equal figures,
  0 disagreements). **The step table's 432 / 1,685 has not; it is still a count of statements a leading-keyword label
  called DDL or DML.**
- **(v0.12) Production runs no confinement at runtime**, on attested and `verified` builds alike (§4c-iii, carrier
  (ii)): accepted 0013's deferral to 0008, unchanged.
- **(v0.12) `attested` claims** that CI ran the attestation suite (§4d: a computed set of 54 test modules at
  `58dd7f6`, not the whole test suite) against a SQLite library with this attestation key, on this architecture,
  operating system and C library. It does not claim the user's CPython is the binary CI ran. A statically linked
  interpreter's C library cannot be read, so such a build is at most `verified`.
- **(v21) A record does not carry the dependency set its suite ran with.** Provenance's fields are closed. Every job installs against `specs/evidence/attestation/constraints.txt`, so the set is the one committed at the record's commit: it is recoverable from that commit, not from the record.
- **Not integrity** (0007 §8, unchanged).

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

**Implemented 2026-08-03, after acceptance.** The kernel is
`src/veracium/store/schema_version.py` — production owns it, and
`specs/schema_model.py` / `specs/schema_evidence.py` import it, which closes the
shared-boundary requirement of rounds 6 and 8. The store-level invariants run in
`tests/test_store_versioning.py`; the kernel counterexamples in
`tests/test_schema_model.py`. Rows whose checks exist are real names the
"measured today" gate verifies; the migration-borne rows the scope cut
retired stay with `specs/0013`.

| invariant | executable check |
|---|---|
| **S1** a fresh store is stamped | `test_new_store_is_stamped` |
| **S2** a newer store is refused | `test_a_newer_store_is_refused` — write `SCHEMA_VERSION + 1` directly |
| **S3** adoption verifies signature, not counter | `test_s3_a_foreign_store_at_version_zero_is_refused` |
| **S5** the decision is made under the write lock | `test_first_open_locks_before_reading` — assert `BEGIN IMMEDIATE` precedes the version read |
| **S6** an existing store keeps working, no data change | `test_legacy_store_is_adopted_losslessly` — every edge/episode byte-identical after adoption |
| **S7** `FORMAT_VERSION` is untouched | `test_s7_export_format_version_is_independent` |
| **S8** exact set equality (falls out of the digest) | `test_s8_a_store_with_extra_tables_is_refused` |
| **S9** adoption is recorded, and a failing sink aborts it | `test_adoption_audit_sink_failure_aborts` — sink raises, assert **not** stamped |
| **S10** the **production** internal-exclusion query excludes `sqlite_stat1` | `test_analyze_does_not_change_the_digest` — `ANALYZE`, reopen, assert adopted. **Must call the shipped query** |
| **S11** no code depends on column order | `test_every_statement_names_its_columns` — no `SELECT *` (except aggregates), **every `INSERT` names its destination columns**. *(Round 4: this is now a **general quality lint**, not a justification. v5 still described it as licensing an "unordered column comparison"; the manifest stores ordered `table_xinfo` rows and byte-for-byte DDL, so nothing about acceptance rests on it.)* |
| **S12** index drift is repaired on **every** path | `test_drifted_acceleration_index_is_rebuilt` — replace with a UNIQUE index on an already-**stamped** store, reopen, assert the canonical definition |
| **S13** the stamp is transactional in the installed sqlite | `test_s13_user_version_rolls_back` |
| **S14** a negative version refuses; `SCHEMA_VERSION` is in range | `test_s14_a_negative_user_version_is_refused` |
| **S16** a stamped store validates its manifest | `test_s16_a_stamped_store_with_the_wrong_shape_is_refused` |
| **S17** an unstamped file with any foreign object is not "new" | `test_s17_a_database_with_only_an_unrelated_table_is_refused` |
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
| **S36** the runtime is qualified by recorded evidence | `test_no_matching_record_is_verified_and_a_matching_one_is_attested` · `test_each_verification_step_refuses_and_names_itself` · `test_inv_sa1_an_attested_identity_does_not_skip_verification` — **the full §4a-viii rule**: build identity · structural validity · constructor digest · **complete manifestation byte-for-byte** · **v17:** the rule now governs an `attested` build's record; a build without one is `verified` or `refused` by measurement (§4g.6, 4a and 4b; INV-SA1–INV-SA3) · **(v20):** the legacy record class is retired (I4), and its test with it (§4g.6, 4f, v20 list) |
| **S37** conformance covers rebuildable **DDL** | `test_a_wrong_rebuildable_ddl_fails_conformance` — v5's digest-based S23 passed it |
| **S39** legacy resolution is candidate-based | `test_resolution_does_not_use_a_default_version_digest` — **measured today** |
| **S40** only unstamped releases feed the legacy set | `test_resolution_is_restricted_to_legacy_base_versions` |
| **S41** the gate re-derives every **authoritative** field | `schema_evidence.py --check` in CI. *(Manual probe, not a suite test: it rebuilds 23 worktrees. The fabricated-artifact result is recorded in §15, not claimed as an automated check.)* |
| **S42** historical manifests are immutable | `test_deleting_a_historical_version_is_an_error` — **measured today** |
| **S44** flipping only a **policy** fails conformance | `test_flipping_only_a_policy_fails_conformance` — **v6's check was tautological** |
| **S45** version-zero tries only `LEGACY_BASE_VERSIONS` | `test_resolution_is_restricted_to_legacy_base_versions` |
| **S46** deleting a historical version is an error | `test_deleting_a_historical_version_is_an_error` |
| **S47** a runtime is qualified by **evidence** | `test_no_matching_record_is_verified_and_a_matching_one_is_attested` · `test_each_key_field_separates_two_records_that_agree_on_every_other` · `test_a_build_whose_probe_reads_as_an_int_matches_no_record` · **v17: WITHDRAWN in part (§4g.6, 4f):** “an unrecorded runtime is not qualified” no longer holds; an unrecorded build is `verified` or `refused` by measurement · **(v20):** the kept half is cited: a record matches only on the full attestation key, its features compared as exact bools; an unmatched build is `verified`. The two legacy tests are retired (§4g.6, 4f, v20 list) |
| **S49** the audit event payload is the frozen type | `test_adoption_event_payload_is_typed` — §4e, both events, paired `adoption_id`. **Not yet written**; needs the store |
| **S54** missing legacy evidence authorises nothing | `test_missing_legacy_evidence_authorizes_nothing` — **measured today** |
| **S55** runtime evidence can actually be written | `test_a_written_record_reads_back_attested` · `test_a_record_the_reader_would_poison_is_never_written` — **measured today**; v7's flag was ignored · **(v20):** the attestation writer (`specs/attestation_writer.py`) replaces the legacy writer; what it writes reads back `attested`, and it never writes what the reader would poison |
| **S56** recorded runtimes are internally valid | `test_the_packaged_attestation_artifact_is_valid` · `test_the_record_and_artifact_key_sets_are_closed` — **measured today** · **v17: WITHDRAWN in part (§4g.6, 4f):** the skipping test's premise, “an unrecorded runtime is not qualified”, is withdrawn; an unrecorded build is `verified` or `refused` by measurement · **(v20):** the shipped attestation artifact is the recorded evidence and is asserted valid; the skipping test and the empty-digest-map test are retired with the class (§4g.6, 4f, v20 list) |
| **S58** an **unattested** runtime contributes nothing | `test_inv_sa5_a_forged_record_cannot_widen_the_accepted_evidence` · `test_every_accepted_manifestation_comes_from_a_closed_set_of_sources` — **measured today**. Internal consistency is not provenance · **v17:** accepted manifests are no longer widened by any runtime record: every build is held to the ONE accepted evidence set (§4g.2; §4g.6, 4d) · **(v20):** the accepted-set generator's union over runtime records is removed (I4); every accepted manifestation comes from a constructor, a reviewed migration or a reviewed legacy ALTER chain |
| **S65** the **production predicate** rejects a conflicting artifact | `test_a_poisoned_artifact_blocks_attestation_never_verification` · `test_the_packaged_attestation_artifact_is_valid` — **measured today**; v12 checked this only in the generator · **(v20):** “rejects” now means the artifact attests nothing: a conflicting attestation artifact blocks attestation and the build is `verified` (§4g.3, a record can only remove the warning) |
| **S66** exactly one active runtime **build identity** | `test_any_number_of_keys_is_valid_and_another_keys_record_attests_nothing` · `test_a_superseded_revision_is_replaced_only_on_the_full_key` — **measured today**. **Build identity** (version · source id · canonical typed probes) governs one-active, matching, replacement, attestation, reporting; **evidence revision** (algorithm · schema version) only versions the record. A superseded revision of the *same* build is replaceable — that carve-out is what clears an algorithm bump without deadlock · **v17: WITHDRAWN (§4g.6, 4f):** any number of attestation records, each for one attestation key (§4g.2; §4g.6, 4d) · **(v20):** the carve-out is kept on the FULL attestation key: a superseded revision is replaced only by a record of the same key |
| **S72** feature results are a closed, typed vocabulary | `test_a_build_whose_probe_reads_as_an_int_matches_no_record` · `test_the_record_and_artifact_key_sets_are_closed` — **measured today**; `1 == True` in Python · **(v20):** the attestation key's features are a fixed tuple of exact bools |
| **S73** a manifestation's key set **equals** the declaration | `test_a_missing_declared_object_fails_the_record` — **measured today**; "no extras" was only half of "exact" · **(v20):** the same name, now exercised on the manifestation through `manifestation_problems`; the record class is retired |
| **S74** a malformed current-algorithm record poisons the artifact | `test_a_revision_field_that_is_not_an_exact_int_is_malformed_and_poisons` · `test_every_record_field_as_a_container_leaves_the_build_verified_naming_it` — **measured today**; superseded records are ignored, malformed current ones are evidence of breakage · **(v20):** over attestation records; a malformed current record poisons the artifact and the build stays `verified` |
| **S75** evidence revisions are **monotone** | `test_a_future_revision_of_this_key_is_never_overwritten_and_another_keys_does_not_block` — **measured today**; an older checkout silently downgraded a future algorithm and a future schema version, rc 0 both times · **(v20):** the attestation writer's first step (§4g.6, 4d, v19's order) |
| **S76** the validators are **total** | `test_every_record_field_as_a_container_leaves_the_build_verified_naming_it` · `test_a_validator_escape_poisons_that_record_and_the_build_stays_verified` · `test_a_failing_identity_read_refuses_at_the_gate_and_never_raises_through_it` — **measured today**; `features=[]` raised `AttributeError` out of the predicate, and `13.0`/`True` revision fields qualified via Python equality · **(v20):** the attestation validators and `runtime_status()` are total |
| **S77** superseded records cannot disqualify | `test_a_superseded_or_future_record_contributes_nothing_and_poisons_nothing` · `test_the_release_check_reports_every_stale_attestation_record` — **measured today**; two stale leftovers beside a valid record caused a needless startup failure. `--check` reports them for cleanup instead · **(v20):** over attestation records; `--check` reports each superseded record for cleanup |
| **S78** manifestation structure is genuinely closed | `test_an_extra_manifestation_field_is_rejected` — exact field sets, typed fields, exact column-row width · **(v20):** the same name, now exercised on the manifestation through `manifestation_problems`; the record class is retired |
| **S69** the predicate attests the **complete** manifestation | `test_reproduction_compares_the_complete_manifestation_not_the_digest_alone` · `test_inv_sa3_a_wrong_shape_store_is_refused_on_a_verified_build` — **measured today**; the acceptance digest excludes rebuildable objects, so digests alone attest nothing about them · **v17: kept** (§4g.6, 4f): every verification compares against the ACCEPTED evidence, digest AND complete manifestation (INV-SA3) · **(v20):** verification compares the complete manifestation for every build |
| **S70** `SCHEMA_VERSION` is bound to the registry | `test_schema_version_must_match_the_registry` · `test_the_registry_versions_are_contiguous` — **measured today**. *(This invariant existed before the scope cut, regressed when the module holding it was deleted, and the round-6 disposition went on claiming it. The citation gate now catches that class.)* |
| **S71** a missing versions artifact fails the gate | `test_a_missing_versions_artifact_fails_the_gate` — **measured today** |
| **S67** a failed publish leaves nothing published | `test_a_failed_publish_leaves_the_artifact_unchanged_and_no_temporary` — **measured today**; v12 claimed rollback with no test · **(v20):** the attestation writer publishes ONE file (a temporary file and `os.replace` in the same directory), so there is no first file to roll back |
| **S68** staged temporaries are cleaned up | `test_a_failed_publish_leaves_the_artifact_unchanged_and_no_temporary` · `test_the_repository_has_no_stray_staged_artifacts` — **measured today**; v12 shipped a `.tmp` in the review package · **(v20):** the writer's failed publish leaves no temporary file |
| **S63** a self-consistent fabrication is rejected | `test_a_fabricated_manifestation_is_rejected` — **measured today**; a manifestation may hold only declared objects · **(v20):** exercised on the manifestation itself, through `manifestation_problems`; the record class is retired |
| **S64** conflicting runtime identities reject the artifact | `test_inv_sa6_one_key_with_two_evidences_poisons_the_artifact` · `test_equal_evidence_with_different_provenance_is_a_duplicate_not_a_conflict` — **measured today** · **v17: kept** (§4g.6, 4f), over the full attestation key (§4g.6, 4d) · **(v20):** over attestation records: one full key with different evidence conflicts, equal evidence is a duplicate, and provenance is never compared |
| **S59** the policy vocabulary is closed | `test_a_policy_typo_is_a_build_error` · `test_a_rebuildable_non_index_is_a_build_error` — **measured today**; a typo disabled validation entirely |
| **S61** the release `result` is re-derived | `test_the_release_result_is_rederived` — **measured today**; v8 read the stored value |
| **S62** feature probes assert their behaviour | `test_the_strict_table_probe_reports_a_real_bool` · `test_the_ddl_probe_asserts_body_preservation` — **measured today**. *(Round 12: STRICT support is identity, not a requirement, so the probe reports rather than demands — and the report must be a real bool, because `1 == True` in Python split the canonical identity from dict equality.)* |
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
created under a different SQLite runtime may not match, and would be refused. **v17:** the RUNTIME refusal narrows to builds that cannot verify (§4g.6, 4a and 4b); the amendment's failure modes are §4g.9.
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
- **WITHDRAWN (v17; §4g.6, 4f — replaced by §4g.9):** **SQLite support is the recorded set, and it currently has one member**
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

**Round 13: the store design stands approved; three findings in the evidence
file, all reproduced, all fixed. This v16 touches nothing else.**

**Finding 1 — my "older" was actually "any other".** The replacement carve-out
was written `!= current algorithm` while the comments said *older*, so an old
checkout silently overwrote evidence generated by newer code — a record at
algorithm 14 became 13, a schema-version-2 record became 1, rc 0 both times.
**The evidence revision is now monotone**: a future component on the same build
refuses with the message naming the direction ("this checkout is older than the
artifact"), and the carve-out replaces **strictly older** revisions only. Both
of your regression cases are tests, asserting nonzero rc and byte-identical
artifacts. **S75.**

**Finding 2 — the validator was not total, and the revision fields were
untyped.** `features = []` raised `AttributeError` out of
`runtime_supported()`, so the caller got an implementation exception instead of
the closed `unsupported-sqlite` outcome. And `manifest_algorithm = 13.0` with
`schema_version = True` qualified — the same Python-equality class as round 12,
one field over. Now: **structural typing before any field is used**
(`type(v) is int`, never `isinstance` — bool is an int subclass), the artifact
boundary validated (non-list, non-dict members, unreadable JSON), and the
predicate wrapped so **any escape is False**. Diagnostics live in `--check`;
the predicate only answers the question. **S76.**

**Finding 3 — superseded records now actually contribute nothing.** The
duplicate loop examined all records, so two identical stale leftovers beside a
valid current record caused a needless startup failure. Every production check
is scoped to current-algorithm records; `--check` reports stale and duplicate
leftovers for repository cleanup, which is where you said the diagnostics
belong. **S77.**

**Corrections:** the runtime table now states the qualification rule in one
place — build identity · structural validity · digest · complete manifestation
byte-for-byte; and "closed field structure" is now true — exact field sets,
typed fields, exact column-row width, with the extra-field case tested.
**S78.**

**Where I am least confident:**

1. **The `!=` vs `<` bug is the one that should worry us both**, because it was
   introduced *while implementing your previous finding* and survived my own
   re-probes — I tested the deadlock direction and not the downgrade direction.
   The regression tests now cover both directions of that comparison; I do not
   have a general defence against testing only the direction I was thinking
   about.
2. **Nothing else.** The evidence file has now had five consecutive rounds of
   findings; every predicate in it is total, typed, monotone and scoped, and
   the remaining surface is small.

## Review closure

**Set `accepted` 2026-08-03 15:57 UTC by dev, under `PROCESS.md` §4a: external review is
required and dev sets the status once the review's comments are satisfied.
Round 14's verdict was itself "Accepted… approved for acceptance"; its three
non-blocking corrections are applied in the acceptance commit** — the generator
made total over malformed members, manifestation entries checked for internal
consistency (type/key agreement, owning table, non-null SQL, unique column
names, flag domains), and the last digest-only summary replaced by the full
§4a-viii rule.

**Fourteen external rounds.** Every finding of every round is closed in that
round's disposition — **§11 through §24, one section per round, each finding
against openable evidence**: a section, an invariant, a test name that the
"measured today" gate verifies exists, or a measurement quoted with its output.
The dispositions are the closure record; nothing is re-argued here.

| rounds | what they settled |
|---|---|
| 1–3 | the shape comparison: names+types → semantic signature → **known-constructor manifests** (S-Q4 answered by the reviewer) |
| 4–5 | a truthful generator; the instrument split into kernel / evidence / pytest |
| 6–7 | migration containment and destination contracts — later **cut** |
| 8 (scope cut) | **stamp · refuse-newer · adopt-v1**; migrations to a dedicated spec |
| 9–13 | runtime evidence: attestation, atomicity, one build identity, monotone revisions, total validators |
| 14 | **accepted**, three non-blocking corrections |

**What `accepted` authorises, exactly.** Implementation of **this spec's
versioning layer** — S1–S78's unimplemented contract. `0007` has no
`Spec-Requires:`, so the gate passes a commit citing it.

**What it does not authorise, and the gate enforces:** any schema-changing
spec. `0006`, `0008`, `0009` and `0010` each require `0013`, which is `draft`
and, by the round-9 M-Q1 ruling, **must be reviewed against `0008`'s
`confirmations` table before it can be accepted.**

**What remains open, and is not claimed:**

- ~~Nothing is implemented~~ — **no longer true**: the versioning layer landed
  2026-08-03 after acceptance, in the commit citing this spec. Kept struck
  because it was true when acceptance was recorded, minutes earlier.
- **WITHDRAWN (v17; §4g.6, 4f):** **One qualified runtime** (SQLite 3.45.1 by build identity). Release on any
  other identity must refuse with `unsupported-sqlite` until evidence is
  regenerated there — **S-Q7 is a release gate**, per the round-12 and round-14
  rulings.
- **S-Q3** (non-SQLite backends) remains deferred.

**v17 — the SQLite attestation amendment's implementation obligations** (amendment `0013/0007-sqlite-attestation`; its round-2 verdict and this checklist banked verbatim at coordination `2b84ab5`, body sha16 `b6cf6a9d9f0a3ca6`). The design is accepted; implementation acceptance requires every row:

This checklist accompanies design acceptance. It does not assert that the amendment is implemented at `58dd7f6` and does not request another design round for the same invariant surface.

| Obligation | Required implementation evidence |
|---|---|
| **I1 — Complete INV-SA10** | Implement the closed 33-action table, unknown-code refusal, simultaneous schema/row effects, per-call attribution, cache disabling, trace/authorizer completeness, script refusal, direct catalog-write refusal, REINDEX pairing and connection-configuration guards. Freeze the read pragma vocabulary by name and argument shape. Validate every table constructor as plain CREATE without CTAS or IF NOT EXISTS. Keep exact text classification separate from site declarations. |
| **I2 — Negative cells and controls** | Demonstrate N1–N12 red against their named mutants and C1–C3 green. Keep DROP/CTE/comment/script cases and both real and no-op index repair. The control must not fail on nested table-valued pragma traces. Retain exact-one write ownership, missing-site coverage and postcondition mutation checks. The supplied census alone is not the final gate. |
| **I3 — Carrier-specific runtime seam** | Implement A1–A15 for the model and P1–P3 for production now; carry A1–A15 into 0008 when its artifact lands. Run all 16 confinement probes live where required, preserve the unchanged-store refusal cases, exact current-key cardinality, malformed-record poisoning, declaration identity, complete output comparison, provenance resolution and monotone writes. Exercise both production gate call sites. |
| **I4 — Full-key identity and record lifecycle** | Use one canonicalizer for process identity, record validation and the writer. Match and group on the full key. Test malformed/unreadable fields, the exact alias map, architecture/OS/libc separation, equal-evidence aggregation despite different provenance, disagreement refusal and deterministic contributor ordering. Preserve same-build re-recording and monotone evidence revisions while retaining other build keys. Test a later suite revision with changed result digest: do not append two current records for one key or silently lose other keys. This is the integration of §4c-iii's permitted regeneration with the existing replacement rules, not a new build-key dimension. |
| **I5 — Actual attestation jobs** | Bind collection to the one committed suite-selection rule. Enforce every `job:runs` condition from the same job's JUnit, rewrite the two stranded skips and exclude ineligible jobs as specified. Run `--check-evidence` on each verifying build. Distinguish verification refusal, failed tests, excluded jobs and agreeing successful evidence. Execute the required route matrix and arm64 rows; the reviewer's offline suite is not that matrix. |
| **I6 — Product experience and provenance** | Exercise all INV-SA1–INV-SA12 mutants, including universal verification before shape decisions, near-miss discrimination, once-per-process warning behavior, doctor status before store access, migration audit identity and unchanged accepted evidence. Demonstrate real `verified` and `refused` routes beyond the attested runner, as §6 requires. |
| **I7 — C2 tooling follow-up** | Land the separately supplied emitted-reason patch with implementation, or preserve its tested behavior in an equivalent change. Keep its whole-inventory consumer check and leave-one-out tests. Reconcile named environment skips; do not remove tests or modify the reviewed pin to manufacture the author's pass/skip total. |

The package's accepted limits remain limits: the reached-function census does not promise full line coverage, production's current ladder has no runtime confinement, and constructed key checks do not count as execution on other architectures.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~S-Q1~~ | **RULED 2026-08-01, revised 2026-08-02:** names+types **withdrawn** after round 1; the comparison is the semantic signature in §4a. | resolved | research → external | — |
| ~~S-Q2~~ | **RULED 2026-08-02: `allow_adopt: bool = True`**, §4b — and the default is now justified by §4a-iv rather than by convenience. | resolved | dev | — |
| ~~S-Q4~~ | **ANSWERED by round 2, 2026-08-02: known-constructor equality, not semantic equivalence.** It was a list that grew — v3's signature admitted four more counterexamples. §4a. | resolved | external | — |
| ~~S-Q5~~ | **RESOLVED by round 3, 2026-08-02: a structured schema registry.** `SchemaObject(kind, name, ddl, policy)` generates creation, expectation, typed rebuildable identities, repair and drift from one declaration. §4a-vi. **It was blocking, and it was the cause of the `(type, name)` bypass.** | resolved | external | — |
| ~~S-Q6~~ | **RESOLVED by round 4, refined by round 5:** gate the runtime, and **derive qualification from evidence** rather than a hand-edited list. §4a-viii. | resolved | external | — |
| ~~S-Q7~~ | **RULED by round 12, 2026-08-03: one qualified runtime is sufficient to authorise implementation.** The limitation is operational, not architectural: implementation proceeds against the evidenced runtime; **release stays blocked where the packaged SQLite identity is not qualified**; widening needs durable per-runtime attestation and aggregation. Remains a **release gate**, no longer an acceptance question. **v17: DISCHARGED** (§4g.6, 4f): release requires the CI matrix to have run (§4g.6, 4d), not every census build to pass. | resolved | external | — |
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

---

## 23. Round 12 review disposition

**Verdict: core design approved — and S-Q7 ruled: one qualified runtime
authorises implementation.** v14 deferred on 3 runtime-evidence findings and 2
corrections. **All taken.**

| # | finding | closed by |
|---|---|---|
| 1 | the canonical identity was still not used for replacement or matching | **`RuntimeBuildIdentity` / `EvidenceRevision` split adopted.** Replacement by build identity, with the superseded-revision carve-out; matching by canonical identity, never dict equality — `1 == True` in Python split the two. Features are a closed typed vocabulary. **S66 restated, S72** |
| 2 | the record validator accepted missing objects | **exact key set** — missing declared objects and malformed field shapes fail the record itself; the operative table freezes complete-manifestation comparison. **S73** |
| 3 | a malformed current-algorithm record was skipped, not fatal | **it poisons the artifact** — every current-algorithm record must pass validation before any qualification. Superseded records stay ignored. **S74** |

**Corrections:** the STRICT probe test reports rather than demands; the union
wording in the generator is historical.

**Rulings:** S-Q7 resolved — implementation may proceed against the one
evidenced runtime; release remains blocked on unqualified SQLite identities;
widening requires durable per-runtime attestation. **The store-shape design has
no remaining blocker.**

---

## 24. Round 13 review disposition

**Verdict: store architecture approved (standing); v15 deferred on 3
runtime-evidence findings.** All taken, plus both corrections.

| # | finding | closed by |
|---|---|---|
| 1 | evidence revisions can be silently downgraded | **monotone revisions** — a future algorithm or schema version on the same build refuses; the carve-out replaces strictly older only. The bug: `!=` where the comments said *older*. **S75** |
| 2 | the validator is not total; revision fields untyped | **structural typing before use**, `type(v) is int` (bool is an int subclass), artifact-boundary validation, and a predicate that returns False on any escape. **S76** |
| 3 | superseded records still disqualify | **production checks scoped to current-algorithm records**; `--check` carries the stale-record diagnostics. **S77** |

**Corrections:** the qualification rule stated in one place; manifestation
structure genuinely closed (**S78**).
