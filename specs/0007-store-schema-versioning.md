# Feature spec: on-disk store schema versioning

Spec-Status: in review

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v2)** — opened 2026-08-01, revised for external review
> 2026-08-02. **Carried from `0001` Q3 since July and unactioned;** `0006` Q1 is
> what forces it, because `0006` is the first change that would alter the
> on-disk shape. **It is now also the `Spec-Requires:` prerequisite of `0006`,
> `0008`, `0009` and `0010`** — including `0008`, which is `accepted` and cannot
> be implemented until this one is. **This spec is the critical path.**

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v2 |
| **Status** | *see `Spec-Status:` — canonical.* Deliberately small and separable: it is a **prerequisite** of `0006`, not a part of it. |
| **Internal reviewers** | research — pending |
| **External review** | required — `store/sqlite.py` is guarded and a bad migration makes stores unopenable |
| **Review history** | *see `specs/STATUS.md`, generated from `specs/reviews.py`. No counts are stated here; a hand-maintained count drifted in `0008` and was found by the reviewer.* |
| **Decision + date** | — |
| **Path** | full |

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
schema has never changed. This is a latent defect, not a live one — **and the
next schema change is `0006`, which is why it is being fixed now rather than
alongside.** Landing versioning *with* the change that needs it means the
migration mechanism gets its first exercise on the same commit that first needs
to be correct.

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
| `_SCHEMA` | unchanged | `CREATE TABLE IF NOT EXISTS …` | unchanged; **stops being the sole definition of shape** |
| `FORMAT_VERSION` | unchanged | export/import wire format | **explicitly independent** — see §8 |

**No trust-bearing field changes.** This spec adds no capability and touches no
provenance; it constrains *when a store may be opened at all*.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant |
|---|---|---|---|---|---|
| **`user_version` in the file** | `0` → adopt-or-create, see §4 | not possible (sqlite integer) | **higher than ours → REFUSE** | **set to `0` to force adoption of a foreign-shaped store** | **S3** — adoption requires the shape to *match*, not merely the counter to read zero |
| **the db file** | new store | sqlite rejects | — | **anyone who can write this file already owns the process** — stated, not defended | out of scope, and named so it is not mistaken for covered |
| **a lower `user_version`** | — | — | — | downgrade to re-open an unmigrated path | **S4** — migrations are forward-only and a gap refuses |
| **concurrent first open** | — | — | — | two processes stamp at once | **S5** — stamp and DDL commit together, see §4c |
| **extra objects in the file** | — | — | sqlite's own `sqlite_stat1`, `sqlite_autoindex_*` | a foreign table added beside ours | **S8** with **S10** — extra *veracium-visible* tables refuse; sqlite-internal objects are excluded **and that exclusion is measured, not assumed** |

## 2c-ii. Assertions about reach

**Every row below was executed on this working tree on 2026-08-02 and states
the output, not the expectation.** The v1 version of this table contained a
claim that was wrong in exactly the way this table exists to prevent — it is
kept as the last row so the correction is visible rather than quietly dropped.

| assertion | command | result |
|---|---|---|
| no version check exists | `grep -rn "user_version" src/veracium/` | no matches |
| the schema is applied unconditionally | `sed -n '45,47p' src/veracium/store/sqlite.py` | `executescript(_SCHEMA)` on every open, line 46 |
| exports *are* version-checked | `portability.py:69` | newer-than-ours rejected; `FORMAT_VERSION = 2` |
| **`_SCHEMA` defines 4 tables and 3 indices** | `grep -nE "CREATE (TABLE\|INDEX)" src/veracium/store/sqlite.py` | `edges`, `episodes`, `wiki`, `write_counter`; `ix_edges_user_active`, `ix_edges_subj_rel`, `ix_episodes_user` |
| **a fresh store today reads `user_version = 0`** | open a store, `PRAGMA user_version` | `0` — so every existing store takes the adoption path exactly once |
| **sqlite adds objects we did not declare** | `SELECT type,name FROM sqlite_master` on a fresh store | 4 `sqlite_autoindex_*` entries we never wrote; after `ANALYZE`, also `sqlite_stat1` |
| **every read names its columns** | `grep -nE "SELECT" src/veracium/store/sqlite.py` | 11 statements, **no `SELECT *`**; positional access is only ever into a named projection |
| ~~"`_SCHEMA` is `IF NOT EXISTS` — every table"~~ | `grep -c "IF NOT EXISTS"` → `7` | **v1 stated this as `every table`. It is 7 = 4 tables + 3 indices.** A count that spans two kinds of object was reported as if it counted one. |

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
inputs — the integer in the file and the shape of the file — and neither is
attributable to a principal.

**This is stated rather than omitted because the omission would be readable as
an oversight**, given that every neighbouring spec (`0003`, `0011`, `0012`) is
about exactly who may do what. Here the answer is: **the check is not
overridable at runtime by anyone.** A host that wants a different policy gets
one construction-time choice, `allow_adopt` (§4b), and even that can only make
the check **stricter** — never weaker. That direction is deliberate and matches
the standing rule that **configuration may narrow, never widen**.

---

## 4. Behaviour

`SCHEMA_VERSION = 1`. On open, exactly one of:

| state on disk | condition | action |
|---|---|---|
| **new** | `user_version = 0` **and no veracium tables** | create schema, stamp `SCHEMA_VERSION` |
| **legacy** | `user_version = 0` **and the shape matches** (§4a) | **adopt**: re-apply `_SCHEMA` (idempotent), stamp `1`, **no data change** |
| **foreign** | `user_version = 0` **and tables exist but the shape does not match** | **REFUSE** |
| **current** | `user_version = SCHEMA_VERSION` | open |
| **older** | `0 < user_version < SCHEMA_VERSION` | run each registered migration in order; stamp; refuse on a gap |
| **newer** | `user_version > SCHEMA_VERSION` | **REFUSE** — this build cannot know what it does not know |

### 4a. Shape matching — ruled, with the comparison defined exactly

**S-Q1 ruled: compare table names + column names, as an *exact set*.** v1 stated
the ruling but left three things undefined that decide whether an implementation
is correct. They are defined here.

**The correction worth carrying, because I had the axis wrong.** I called this
the "moderate" option between names-only and a `sqlite_master.sql` hash. **The
hash is not stricter — it is strict about the wrong thing.** It fires on DDL
reformatting and SQLite version differences: **differences that are not
differences.** A check that refuses stores which are genuinely fine gets
bypassed, and a bypassed check is weaker than a narrower one that holds.
**Strictness should key on semantics, not representation** — which makes
names+columns the **strictest** option once non-difference checks are excluded,
not a midpoint.

**The shape of a store is defined as:**

```
{ table_name : { (column_name, declared_type) } }
```

drawn from `sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite\_%'`
and `PRAGMA table_info(<table>)`. Compared with **`==`** against the same
structure derived from `_SCHEMA`.

**Four decisions, each with its reason and its cost:**

1. **Exact set equality, not containment.** A database holding our tables **plus
   others** must be **refused** (**S8**). Containment would adopt a foreign store
   that happens to embed our schema — precisely the case adoption exists to
   catch.
2. **sqlite-internal objects are excluded, and this is not cosmetic.** A fresh
   store already contains four `sqlite_autoindex_*` entries nobody declared, and
   running `ANALYZE` adds `sqlite_stat1` — **both measured, §2c-ii.** Without the
   exclusion, S8 refuses a store that a user optimised, which is the
   "refuses stores which are genuinely fine" failure this section opens by
   warning against. **The exclusion is therefore load-bearing and gets its own
   invariant (S10)** rather than living in an implementer's judgement.
3. **Columns compare as an unordered set, and that is justified rather than
   assumed.** All 11 `SELECT` statements name their columns and none is
   `SELECT *` (§2c-ii), so no read depends on ordinal position. **If a future
   read introduces `SELECT *`, this justification lapses** — S11 fails the build
   if one appears.
4. **Declared type is part of the comparison; indices are not.** Type is in
   because `json TEXT` and `json BLOB` are a real difference that a
   names-only check cannot see. Indices are out because they are a performance
   property, not a shape property — and because **adoption re-applies `_SCHEMA`,
   whose `CREATE INDEX IF NOT EXISTS` restores any that are missing** (S12).
   *Limit, stated:* SQLite is dynamically typed, so this compares the
   **declaration**, not the stored values. It catches a differing build; it does
   not catch a writer that put an integer in a `TEXT` column.

**Every adoption is logged** — path, matched shape, timestamp, resulting
version (**S9**). **A one-time trust decision that is not recorded is
unauditable forever after**, and adoption happens once per store, silently, on
upgrade.

**Adoption is the only subtle case.** Every store in existence today reads
`user_version = 0` (measured, §2c-ii) and is shape-identical to v1, so adoption
is correct *now* and would be wrong later. **It is safe only because it verifies
the shape rather than trusting the counter** (S3) — the counter is the thing an
adversary or a truncated copy would leave at zero.

**Migrations are forward-only, registered explicitly, and run inside a
transaction with the stamp.** The registry is **empty** in this change: the
mechanism lands with zero migrations, so its first real use in `0006` is not
also its first execution.

### 4b. The public contract, frozen

```python
SCHEMA_VERSION: int = 1

class StoreVersionError(RuntimeError):
    """The store on disk is not a shape this build can open."""
    path: str            # the file we refused
    found: int           # user_version read from the file (0 = unstamped)
    expected: int        # SCHEMA_VERSION of this build
    reason: str          # one of the closed set below

class SqliteStore(Store):
    def __init__(self, path: str | Path = "veracium.db", *,
                 allow_adopt: bool = True) -> None: ...
```

**`reason` is a closed set** — `"newer"`, `"foreign-shape"`, `"migration-gap"`,
`"adoption-refused"`. Closed because hosts will branch on it; free-form strings
are the thing `0008` round 3 was deferred over.

**`allow_adopt=False`** resolves **S-Q2**: a host that would rather refuse an
unstamped store than adopt it sets it, and gets `reason="adoption-refused"`.
Default `True`, because the default must not break every store that exists
today. **It can only narrow** (§3b).

**The exception message carries all three of `path`, `found`, `expected`,**
because the only useful remedy is a build change and the message must say so.

**`StoreVersionError` derives from `RuntimeError`, not from a veracium base
class.** No such base exists today; introducing one is a wider change than this
spec, and inventing it here would be scope creep of the kind `0008` was told
off for twice.

### 4c. The open transaction — and why `executescript` cannot carry it

**S5 says the stamp and the DDL commit together. `executescript` cannot do
that, and this was measured rather than reasoned about:**

```
BEGIN; PRAGMA user_version=7; executescript("CREATE TABLE …")
  -> reopen without committing: user_version reads 7
```

**`sqlite3.Cursor.executescript` issues an implicit COMMIT before it runs.** An
implementation that keeps the current `executescript(_SCHEMA)` call and adds a
stamp around it therefore has **no transaction at all** — the two halves commit
separately, and a crash between them leaves a stamped store with no tables, or
tables with no stamp.

**Required:** the create and adopt paths execute the schema statements
**individually** on a connection inside an explicit transaction, with the
`PRAGMA user_version` write in the same transaction, and one commit. **This is
an implementation constraint that the spec has to state**, because the obvious
implementation is wrong in a way that only shows up on a crash.

**Named limit:** `PRAGMA user_version` is transactional in SQLite — it lives in
the database header and rolls back — but this is a property of SQLite that the
invariant depends on. **S13 asserts it against the installed SQLite** rather
than trusting the documentation, because a false assumption here silently
removes the atomicity S5 claims.

---

## 5. Regime analysis — where does this behave differently?

**The regime that matters is the one no test naturally reaches:** an *older*
build opening a *newer* store. Fixtures create fresh stores at the current
version, so this path is invisible to ordinary tests — the same reason the
maintenance regimes in `0002` needed simulated clocks.

**S2 reaches it by writing `user_version` directly**, rather than by
constructing a build that does not exist yet.

**The second unreachable regime is the migration gap.** With `SCHEMA_VERSION =
1` and an empty registry, **S4 cannot be exercised by any real store** — there
is no version to migrate from. S4 therefore injects a registry with a
deliberately missing step. **Stated because the alternative is an invariant that
silently tests nothing**, which is how `0002` shipped four rows whose checks
never ran.

---

## 6. Invariants and executable checks — REQUIRED, blocking

**None of these tests exist. Nothing in this spec is implemented.** The names
below are the contract for what must be written, not a description of what is
there — `grep -rn "user_version" src/veracium/ tests/` returns nothing today.
**Stated in this form because a previous manifest listed 17 rows of which 11
cited tests that did not exist.**

| invariant | executable check | where |
|---|---|---|
| **S1** a fresh store is stamped | `test_new_store_is_stamped` | CI |
| **S2** a newer store is **refused**, not opened | `test_a_newer_store_is_refused` — set `user_version = SCHEMA_VERSION + 1` directly | CI |
| **S3** adoption verifies **shape**, not the counter | `test_a_foreign_store_at_version_zero_is_refused` — a db with a `veracium`-ish table of the wrong shape | CI |
| **S4** migrations are forward-only; a gap refuses | `test_a_missing_migration_refuses` — **injects a registry**, see §5 | CI |
| **S5** first open is atomic under concurrency | `test_concurrent_first_open_stamps_once` — N threads on one path | CI |
| **S6** an existing store keeps working with no data change | `test_legacy_store_is_adopted_losslessly` — build a store on the current code, clear `user_version`, reopen, assert every edge/episode is byte-identical | CI |
| **S7** `FORMAT_VERSION` is untouched | `test_export_format_version_is_independent` | CI |
| **S8** shape matching is **exact set equality** | `test_a_store_with_extra_tables_is_refused` — our schema plus one foreign table | CI |
| **S9** every adoption is logged | `test_adoption_is_logged` — asserts path, shape, version in the record | CI |
| **S10** sqlite-internal objects do **not** defeat S8 | `test_analyze_does_not_make_a_store_foreign` — run `ANALYZE`, reopen, assert adopted | CI |
| **S11** no read may depend on column order | `test_no_select_star_in_the_sqlite_store` — greps the module; **fails the build if `SELECT *` appears**, because §4a decision 3 rests on its absence | CI |
| **S12** adoption restores a missing index | `test_adoption_recreates_a_dropped_index` — drop `ix_edges_subj_rel`, reopen, assert present | CI |
| **S13** the stamp is transactional in the installed SQLite | `test_user_version_rolls_back` — stamp inside a transaction, roll back, assert the old value | CI |

**S6 is the one that protects users** and is the reason adoption is specified
before it is convenient: everyone who has a store today goes through that path
exactly once, silently, on upgrade.

**S11 is unusual and worth flagging to the reviewer:** it is a lint, not a
behavioural test. It exists because §4a decision 3 is a *justified* choice
rather than a safe one, and the justification is a property of the source that
a future commit can remove without noticing.

---

## 7. Failure modes and reversibility

**Failure mode is refusal to open, which is loud, safe and reversible** by
installing the matching build. **The unacceptable failure is the current one:
opening and silently misreading.**

**The cost is stated rather than minimised:** this change can make a store that
opens today refuse to open tomorrow. The population that hits it is a store
whose shape does not match — which under `SCHEMA_VERSION = 1` should be empty,
since the schema has never changed. **If that reasoning is wrong, the blast
radius is "the application will not start."** S6 is the invariant that has to
carry it.

**Reversibility.** Adoption writes one integer and no data, so downgrading to a
pre-0007 build works — that build ignores `user_version` entirely. **A real
migration will not be reversible**, which is exactly why the registry is empty
here and why `0006` must specify its own down-path or declare it one-way.

---

## 8. Claims and limits

**Claim:** a veracium build refuses to open a store it does not understand.

**Limits:**

- **Not integrity, not authentication.** Nothing detects tampering or
  corruption; `user_version` is advisory metadata that a writer can set to
  anything. Against an adversary with write access to the file this proves
  nothing — **and that adversary already owns everything.**
- **Not multi-process coordination.** S5 covers concurrent *first open*, not
  concurrent migration across processes. A migration should be run once, by one
  process, and `0006` must say so.
- **Not a data-format guarantee.** The JSON blobs inside the rows are validated
  by pydantic on read, unchanged by this spec.
- **Not a type guarantee.** §4a compares *declared* types. SQLite does not
  enforce them, so a store whose `TEXT` column holds integers matches.
- **Not applicable to other backends.** `base.py` is an interface; a Postgres
  store would need its own mechanism (**S-Q3**).

---

## 9. Brief for the external reviewer

**What is being asked:** whether the open-time decision table in §4 and the
shape comparison in §4a are correct and implementable — **not** whether
versioning is worth having.

**This spec is the critical path.** It is the `Spec-Requires:` prerequisite of
`0006`, `0008`, `0009` and `0010`. `0008` is **`accepted`** and still cannot be
implemented, because the CI gate refuses a commit citing an accepted spec whose
prerequisite is `draft`. **Four specs are waiting on this one.** That is context
for priority, and explicitly **not** an argument for a lighter review — a
prerequisite that four specs stand on is the worst possible place to be lenient.

**The three places I would look first, because they are where I am least
confident:**

1. **§4a decision 2 — the sqlite-internal exclusion.** I am excluding a set
   defined by a name prefix (`sqlite_%`). If that prefix does not in fact cover
   everything SQLite may add, S8 refuses legitimate stores in the field. I
   measured two cases; I have not enumerated the space.
2. **§4c — the transaction.** I found that `executescript` implicitly commits,
   which breaks the obvious implementation of S5. **I would like this checked
   independently**, because the whole atomicity claim rests on one measurement
   I made myself.
3. **Adoption, §4 row 2.** It is a one-time, silent, irreversible-in-practice
   trust decision applied to every store that exists. The argument that it is
   safe rests entirely on "the schema has never changed." **If that premise is
   false anywhere, adoption is the mechanism that will hide it.**

**What I deliberately did not do:**

- No `veracium` exception base class (§4b) — wider than this spec.
- No index or trigger comparison (§4a decision 4) — argued, not overlooked.
- No cross-process migration locking (§8) — pushed to `0006`.

**What v2 changed from v1**, so the round is reviewable rather than re-read
from scratch: §2c-ii's incorrect "every table" claim corrected and kept visible;
§3b added (absent, and required for the `full` path); §4a's ruling made
executable — internal objects, column order, declared types, indices each
decided with a reason; §4b public contract frozen, resolving S-Q2; §4c added
after measuring `executescript`; S10–S13 added; §6 now states plainly that
nothing is implemented; §9 added.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~S-Q1~~ | **RULED 2026-08-01: names + columns, with exact set equality.** Made executable in §4a v2 — internal objects, ordering, types and indices each decided. Note the framing correction: it is not a midpoint. | resolved | research | — |
| ~~S-Q2~~ | **RULED 2026-08-02: yes — `allow_adopt: bool = True`, §4b.** Default `True` because the default must not break every existing store; it can only narrow, never widen. | resolved | dev | — |
| **S-Q3** | Does anything other than `SqliteStore` need this? `base.py` is an interface; a future Postgres store would need its own mechanism. **Not in scope, recorded so it is not assumed covered.** | `deferred` | dev | — |
