# Feature spec: on-disk store schema versioning

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — opened 2026-08-01. **Carried from `0001` Q3 since July and
> unactioned;** `0006` Q1 is what forces it, because `0006` is the first change
> that would alter the on-disk shape.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 |
| **Status** | *see `Spec-Status:` — canonical.* Deliberately small and separable: it is a **prerequisite** of `0006`, not a part of it. |
| **Internal reviewers** | research — pending |
| **External review** | required — `store/sqlite.py` is guarded and a bad migration makes stores unopenable |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation

**Nothing identifies the shape of an on-disk store.**

```
$ grep -rn "user_version" src/veracium/     -> (nothing)
```

`SqliteStore.__init__` connects and unconditionally runs
`executescript(_SCHEMA)` (`sqlite.py:45-47`), which is `CREATE TABLE IF NOT
EXISTS`. **Any build opens any store.** A build whose `_SCHEMA` has diverged
adds its missing tables to a foreign store and proceeds, reading the rest under
assumptions that no longer hold.

`FORMAT_VERSION` (`portability.py:35`) guards **exports** and is version-checked
on import. **The store itself has no equivalent**, so the file people actually
keep is the one thing with no version on it.

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
| **concurrent first open** | — | — | — | two processes stamp at once | **S5** — stamp inside the same transaction as the DDL |

## 2c-ii. Assertions about reach

| assertion | command | result |
|---|---|---|
| no version check exists | `grep -rn "user_version" src/veracium/` | none |
| the schema is applied unconditionally | `sed -n '45,47p' src/veracium/store/sqlite.py` | `executescript(_SCHEMA)` on every open |
| `_SCHEMA` is `IF NOT EXISTS` | `grep -c "IF NOT EXISTS" src/veracium/store/sqlite.py` | every table |
| exports *are* version-checked | `portability.py:69` | newer-than-ours rejected |

---

## 3. Trust-class matrix

**Not applicable — no trust class is read or written.** Recorded explicitly
rather than omitted, because the template requires it and *"not applicable"*
should be a stated finding rather than a missing section.

**The trust-relevant property is different and worth naming:** this spec
protects the *integrity of the substrate* the trust model is stored in. Every
invariant in `0002`–`0006` assumes the bytes on disk mean what this build thinks
they mean. **That assumption is currently unchecked**, which makes this a
precondition of all of them rather than a peer.

---

## 4. Behaviour

`SCHEMA_VERSION = 1`. On open, exactly one of:

| state on disk | condition | action |
|---|---|---|
| **new** | `user_version = 0` **and no veracium tables** | create schema, stamp `SCHEMA_VERSION` |
| **legacy** | `user_version = 0` **and the tables match today's shape** | **adopt**: stamp `1`, no data change |
| **foreign** | `user_version = 0` **and tables exist but do not match** | **REFUSE** |
| **current** | `user_version = SCHEMA_VERSION` | open |
| **older** | `0 < user_version < SCHEMA_VERSION` | run each registered migration in order; stamp; refuse on a gap |
| **newer** | `user_version > SCHEMA_VERSION` | **REFUSE** — this build cannot know what it does not know |

**Adoption is the only subtle case.** Every store in existence today reads
`user_version = 0` and is shape-identical to v1, so adoption is correct *now*
and would be wrong later. **It is safe only because it verifies the shape rather
than trusting the counter** (S3) — the counter is the thing an adversary or a
truncated copy would leave at zero.

**Migrations are forward-only, registered explicitly, and run inside a
transaction with the stamp.** The registry is **empty** in this change: the
mechanism lands with zero migrations, so its first real use in `0006` is not
also its first execution.

**Refusal raises with the two version numbers and the file path**, because the
only useful remedy is a build change and the message must say so.

---

## 5. Regime analysis

**The regime that matters is the one no test naturally reaches:** an *older*
build opening a *newer* store. Fixtures create fresh stores at the current
version, so this path is invisible to ordinary tests — the same reason the
maintenance regimes in `0002` needed simulated clocks.

**S2 reaches it by writing `user_version` directly**, rather than by
constructing a build that does not exist yet.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **S1** a fresh store is stamped | `test_new_store_is_stamped` | CI |
| **S2** a newer store is **refused**, not opened | `test_a_newer_store_is_refused` — set `user_version = SCHEMA_VERSION + 1` directly | CI |
| **S3** adoption verifies **shape**, not the counter | `test_a_foreign_store_at_version_zero_is_refused` — a db with a `veracium`-ish table of the wrong shape | CI |
| **S4** migrations are forward-only; a gap refuses | `test_a_missing_migration_refuses` | CI |
| **S5** first open is atomic under concurrency | `test_concurrent_first_open_stamps_once` — N threads on one path | CI |
| **S6** an existing store keeps working with no data change | `test_legacy_store_is_adopted_losslessly` — build a store on the current code, clear `user_version`, reopen, assert every edge/episode is byte-identical | CI |
| **S7** `FORMAT_VERSION` is untouched | `test_export_format_version_is_independent` | CI |

**S6 is the one that protects users** and is the reason adoption is specified
before it is convenient: everyone who has a store today goes through that path
exactly once, silently, on upgrade.

---

## 7. Failure modes and reversibility

**Failure mode is refusal to open, which is loud, safe and reversible** by
installing the matching build. **The unacceptable failure is the current one:
opening and silently misreading.**

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

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| **S-Q1** | **How is "the tables match today's shape" defined?** Options: table names only (cheap, weak) · names + column names (moderate) · a hash of `sqlite_master.sql` (exact, but brittle against harmless formatting changes). **Dev leans names + columns** — a hash would refuse stores that are genuinely fine. | **blocking** | research | before implementation |
| **S-Q2** | Should `SqliteStore` accept `allow_adopt=False` for hosts that would rather refuse an unstamped store than adopt it? | `pre-release` | dev | before release |
| **S-Q3** | Does anything other than `SqliteStore` need this? `base.py` is an interface; a future Postgres store would need its own mechanism. **Not in scope, recorded so it is not assumed covered.** | `deferred` | dev | — |
