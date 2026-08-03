# Feature spec: on-disk store migrations

Spec-Status: in review
Spec-Requires: 0007

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v6)** — round 4: *architecture standing (planner, evidence
> consumption, qualification design, DDL all approved); v5 deferred on five
> falsifiable gaps*. All taken, with the reviewer's constraint honoured — the
> migration and the shared planner are unchanged: **the failure boundary is
> actually total** (malformed nested evidence fields, non-database bytes and
> unopenable paths were escaping as raw exceptions; validators type-check
> before use, context entry is inside the boundary, and two store-failure
> outcomes — `invalid-store`, `store-unopenable` — join the vocabulary);
> **malformed current migration-runtime records POISON the qualification**
> (v5 silently filtered them); **path cardinality is exact artifact-wide**
> (expected = every active identity × step × accepted source; a
> foreign-identity record now fails both validators); **confinement probes
> require `SQLITE_AUTH` specifically** (the `RELEASE` probe held no savepoint,
> so `no such savepoint` was recorded as a denial — a permissive authorizer
> now flips all twelve denial probes False); and **the authority has a
> lifecycle** — canonical realpath binding, source and step binding, an
> issuance/expiry window, and single-use consumption, so the round-4 replay
> and symlink-retarget probes both refuse with no store touched.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v6 |
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

**The destination requirement is independent of the migration.** What
authorises an output today is stated in §5 and §5c: **exact constructor
identity plus recorded path evidence** — nothing a migration produces enters
the accepted set on its own sayso.

### 4c-deferred. The structural-capability model — first `ALTER`, own review

*(Round 3: this subsection is **explicitly deferred design**, not present
contract — v4 still said capability "authorises", which contradicted §5/§5c's
correct statement that it is context only.)* An `ALTER`-class migration will
legitimately produce DDL text that differs from the constructor's, which is
the case a byte-for-byte rule wrongly rejects. When the first real `ALTER`
arrives, the deferred model — every declared object present and of the right
kind, columns compared via `table_xinfo` rather than DDL text, no unapproved
objects, rebuildable absence as repairable drift — gets its own external
review round before anything relies on it. Until then
`destination_problems()` is non-authorizing scaffolding, exact DDL text
remains what `0007`'s digest records, and **only exact identity and recorded
evidence authorise**.

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
(72 tests: every round-2, round-3 and round-4 probe as a regression, the full inherited
planner across empty/unstamped/foreign/malformed/newer stores, the evidence
gate's adversarial records, confinement qualification, the closed failure
model, and the stale-connection hazard below).

**And there is exactly one planner** (round 3, finding 1). The instrument owns
no version-state machine: `open_or_migrate` / `migrate_store` install the
draft registry and the draft evidence artifact into the production `0007`
kernel — the state a v2 build would ship as package data — and call
`open_versioned()`, whose **older-row hook** is the seam `0007` §4 delegates
to this spec. Ordinary opening installs a refusing hook (classify the source,
then `migration-required`); the dedicated offline operation installs the
migrating hook (§5b–§5c). Every other row — new, legacy, foreign, current
with drift repair, stamped-wrong, newer, locked, unsupported — is the
kernel's own code, which is why a stamped v1 store with an unauthorized extra
table now answers `stamped-shape-mismatch` (round 3 measured it being
promised a migration), and a table squatting a rebuildable index name is a
closed refusal via the typed digest rather than an `OperationalError` from a
repair statement.

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

**The boundary is a mechanism, and its claim is exactly this** (round 3
narrowed the wording): **ordinary opening cannot initiate migration; the
trusted deployment authority owns quiescence, old-binary fencing, and backup
validity.** The stale-process race is not "gone" — the library cannot see
other processes — it is *owned*, explicitly, by the party that can.

Migration is a **dedicated operation** (`migrate_store`), never a parameter on
tenant-facing opening — `open_or_migrate` has no authority argument at all
(round 3). The `MigrationAuthority` is an **attestation the library validates
but cannot verify** — and round 4 showed that binding it to a path *string*
is not binding it to an *operation*: an authority was replayed after the
store at its path was replaced (the replacement migrated under an attestation
belonging to the earlier file), and a retargeted symlink carried an authority
minted for a different store. **The authority contract is therefore frozen
here, not left as an implementation note** (round 4's acceptance-boundary
ruling):

| field | binds | validation at consumption |
|---|---|---|
| `quiesced` | the host's quiescence assertion | exactly `True` — a truthy `1` refuses (round 3's probe) |
| `store_path` | canonical store identity | `os.path.realpath` at mint AND at consumption; a retargeted symlink is a different store and refuses |
| `from_version` · `to_version` | the step's endpoints | exact ints, equal to the selected step's |
| `source_digest` | the source manifestation being migrated | equals the acceptance digest measured under the write lock, pre-repair (rebuildable-blind, so incidental index drift does not unbind) |
| `migration_digest` | the reviewed statements | equals the declaration digest of the registered step |
| `backup_ref` | the backup this operation made | nonempty string |
| `release_ref` | the minting release/deployment | nonempty string; **real release identity at implementation** |
| `operation_id` | this one migration operation | **single-use** — consumed on acceptance, before execution; a replay refuses |
| `issued_at` · `expires_at` | the validity window | RFC 3339, timezone-aware, parseable; `issued ≤ expires`, `now < expires` |

An expired, previously consumed, retargeted, source-mismatched, mistyped or
unbound authority refuses `migration-quiescence-required`. **Consumption is
in-process in the draft and durable in production — the migration audit
(§5e) is the durable consumer.** What remains host-trust, stated rather than
hidden: a host that atomically swaps in an identical-shape store at the same
canonical path inside the validity window defeats path binding. The host is
explicitly trusted; the lifecycle exists so its assertion cannot silently
**drift** to a different operation — which is the failure round 4 measured.
`allow_adopt` never doubles as migration permission.

*(v2's §8 said "not multi-process" while §5b demonstrated five concurrent
openers — the contradiction is resolved as above: concurrent **cooperating**
openers are serialised by the lock; **stale** openers are the operational
contract's problem.)*

## 5c. Path evidence: recorded, validated, consumed — never re-derived

**Round 3's central finding: v4 generated its "expected" record from the
currently loaded migration code, so an altered migration authorised itself.**
Measured — `DELETE FROM edges` appended to the declared statements produced
the exact v2 schema, stamped `migrated`, and left zero edge rows; exact schema
identity cannot detect data destruction. **The correction is architectural:
evidence is a shipped, committed artifact that the planner LOADS; the live
code contributes only a digest to match against.** *Committed, not
immutable* — round 4's distinction, adopted: the artifact is version-controlled
package data, consumed rather than re-derived, but it is **not** independently
authenticated or integrity-protected at runtime; package signing or filesystem
integrity would be a separate boundary and is not claimed here.

The artifact — `specs/generated/migration_0013_evidence.json`, the M11/M12
draft forms — is generated by `migrations_0013.py --write-evidence` on a
runtime being qualified, verified by `--check-evidence` (structural validation
plus exact re-derivation on the recording runtime), and consumed by
`migrate_store`. One path record carries:

```
migration_evidence_algorithm · manifest_algorithm · runtime build identity
from_version  · source acceptance digest · source FULL-manifest hash
to_version    · output acceptance digest · output FULL-manifest hash
              · complete output manifestation
migration declaration digest · provenance
```

**Record-level consistency rules, enforced by the validator** (round 3):

```
hash(complete output manifestation) == output full-manifest hash
digest(complete output manifestation) == output acceptance digest
source identifiers resolve to exactly ONE accepted source manifestation
output identifiers resolve to exactly ONE accepted destination manifestation
```

**Selection at migration time is over the full frozen key**: runtime build
identity × source version × source acceptance digest × source full-manifest
hash × destination version × **migration declaration digest** (sha256 over
domain-separated canonical JSON of `[from, to, [statements…]]` —
`canonical_migration_bytes()`). Exactly one record or the migration does not
run: an altered migration — even one producing the identical schema — digests
differently, matches nothing, and refuses `migration-evidence-missing` with
data and stamp untouched. **Cardinality is exact ARTIFACT-WIDE** (round 4:
v5 computed expectations only for the running process's identity, so a
foreign-identity record accumulated silently): the expected set is **every
active build identity × every declared step × every accepted source
manifestation**, actual current-record keys must equal it exactly, and every
current record's runtime must **resolve** — to exactly one active
schema-runtime record and exactly one valid migration-runtime record in the
same artifact. Missing, extra, foreign, unattested, duplicate,
stale-algorithm or contradictory records each fail closed, and each has an
adversarial test. **A missing or mistyped algorithm field is malformed, not
superseded** — only explicitly superseded algorithms are ignored (`0007`
round 12's rule, applied to every record class in this artifact).
After execution the complete output is repaired, recomputed and compared
against the record's manifestation, acceptance digest AND full-manifest hash
before any stamp — full-manifest hashes because the acceptance digest is
blind to rebuildables by design (round 2, measured).

**Migration confinement is itself runtime-qualified** (round 3, finding 3).
`0007`'s runtime identity deliberately carries no authorizer probe — migration
left its scope in v10 — so its qualification cannot attest the behaviours
§4b's confinement leans on. The artifact therefore records a
**migration-runtime qualification** per build identity: authorizer API
available; `BEGIN`/`COMMIT`/`END`/`ROLLBACK`, savepoints and `RELEASE`,
`PRAGMA`, `ATTACH`/`DETACH`, and TEMP-schema effects each **observed and
denied**; restoration after rejection verified. All twelve probes are
required, and **a denial counts only when the failure is specifically
authorization** — `sqlite_errorcode == SQLITE_AUTH` (message-text fallback on
Python 3.10, which lacks the attribute). Round 4 measured why: the `RELEASE`
probe held no savepoint, so `no such savepoint` — raised under a fully
permissive authorizer — was recorded as a denial; every probe's setup is now
a valid statement sequence (the savepoint exists before the authorizer is
installed), and the permissive-authorizer falsifier flips all twelve denial
results to False. Consumption does not trust the record: the probes are
re-run live and compared — mirroring how `0007`'s `runtime_supported()`
re-derives constructor manifestations — and **artifact-level validation
poisons the qualification** on any malformed current-algorithm record,
duplicate identity, identity without an active schema-runtime record, or
violation of the single-active-runtime policy (round 4: v5 silently filtered
a malformed record and stayed qualified on the valid one beside it).
`migrate_store` requires **both** the schema-runtime and the
migration-runtime qualification before touching the store; ordinary opening
requires only `0007`'s, because it executes no confined statement.

## 5d. The closed outcome contract

**Total over expected store, SQLite, evidence, authority and protocol
failures** — and the boundary covers **evidence loading, context entry, and
the database connection itself** (round 4, finding 1: v5's boundary started
after context entry, so a malformed nested evidence field raised `TypeError`
out of the validators, non-database bytes raised `DatabaseError`, and an
unopenable path raised `OperationalError` — three raw escapes from a model
that claimed totality; round 3 had already closed the invalid-SQL and
free-form-string escapes):

| failure class | closed outcome |
|---|---|
| the path cannot be opened at all | `store-unopenable` |
| the bytes are not readable as a SQLite database | `invalid-store` |
| lock acquisition exhausted | `locked` |
| unqualified schema- or migration-runtime; malformed or poisoned schema/runtime evidence — **at any nesting depth** | `unsupported-sqlite` |
| source not an accepted manifestation | `stamped-shape-mismatch` / `foreign-shape` |
| invalid, unbound, expired, consumed or retargeted authority | `migration-quiescence-required` |
| absent, ambiguous, malformed, foreign or non-matching path evidence | `migration-evidence-missing` |
| SQL execution or protocol failure during the migration | `migration-failed` |
| executed output differs from the recorded output | `migration-result-mismatch` |

**Every validator type-checks a field before iterating, hashing, sorting, or
using it as a key** — the round-4 totality rule; a validator escape at
context entry is itself treated as a malformed artifact and fails closed.

Successes are equally closed: `created` · `adopted` · `current` · `migrated`.
The entry points return an `Outcome` — a value that string-compares as its
closed member and carries diagnostics separately, and that **refuses to exist
outside the vocabulary**. Detailed exception text rides the diagnostic, never
the branch value. One deliberate exception, inherited from `0007`'s reviewed
behaviour: package-consistency impossibilities (the constructor disagreeing
with the build's own shipped evidence) raise, because they are properties of a
broken package, not of the store on disk.

## 5e. The migration audit — implementation obligation

*(Round 4's additional correction, recorded as load-bearing spec text.)*
Migration is irreversible, so the production migration operation appends
audit records the way `0007` §4e's adoption path does: an **attempted**
record before execution and a **completed or failed** record after, each
carrying the closed outcome, the authority's identity (`operation_id`,
`release_ref`, issuance window), source and output versions with their
manifestation digests, the migration declaration digest, and the opaque
`backup_ref`. **The audit is also the authority's durable consumer**: the
draft's in-process single-use set (§5b) becomes a lookup against previously
recorded operations, which is what makes single-use survive a process
restart. Lands with the `0008` implementation; the draft demonstrates the
lifecycle in-process.

## 6. Invariants and executable checks — REQUIRED, blocking

**The store contains no migration code — `0013` authorises nothing.** The
rows below marked with test names now run against the **draft instrument**
(`specs/migrations_0013.py`) and the concrete migration; they become store
tests at implementation.

| invariant | executable check |
|---|---|
| **M1** a declared step runs inside the caller's transaction | `test_the_executor_requires_an_existing_transaction` — **measured today**; and exercised by every instrument test via the shared `0007` planner |
| **M2** transaction control in a declared statement is denied | `test_transaction_control_and_pragmas_are_denied` — **measured today**, six forms |
| **M3** temp objects are refused | `test_a_temp_object_is_refused` — **measured today** |
| **M4** pragmas are refused | `test_transaction_control_and_pragmas_are_denied` — **measured today** |
| **M5** the authorizer is restored after failure | `test_the_authorizer_is_restored_after_failure` — **measured today** |
| **M6** an empty migration cannot authorise its output | `test_an_empty_migration_cannot_authorize_its_output` — **measured today**, against the real `confirmations` requirement |
| **M7** a correct migration reaches its declared destination | `test_the_concrete_migration_reaches_the_v2_constructor_output` — **measured today**; output byte-identical to the constructor |
| **M8** a partial or wrong-shape result is rejected | `test_a_partial_migration_is_rejected` — **measured today** |
| **M9** the registry is well-formed | `test_m9_the_draft_registry_is_well_formed` · `test_a_gap_refuses` — **measured today** |
| **M10** a skipped release still upgrades | **NOT demonstrated, and not claimed** (round 2, finding 7). `0013` today authorises the concrete adjacent v1→v2 only; the multi-step planner is reviewed at the first spec needing two real steps |
| **M11** every migration path is keyed individually | **draft form measured today**: the committed artifact keys records by runtime × source digest+hash × destination × declaration digest — `test_the_committed_evidence_artifact_is_valid_and_reproduces`. Production artifact lands with `0008` |
| **M12** runtime evidence covers every declared path | **draft form measured today**: exact cardinality against the live registry — `test_an_absent_path_record_refuses` · `test_a_duplicate_path_record_refuses` · `test_a_stale_algorithm_record_is_superseded_not_consumed`. Production with `0008` |
| **M13** migration runs exactly once among cooperating openers | `test_mq2_concurrent_migration_runs_exactly_once`, and the reviewer's independent five-**process** run. **The stale-opener hazard is measured, not solved** — §5b's quiescence contract. |
| **M14** an altered migration cannot authorise itself | `test_a_data_destructive_alteration_cannot_authorize_itself` · `test_a_side_effect_free_alteration_is_still_not_evidenced` — **measured today**: refusal before execution, data and stamp untouched |
| **M15** migration confinement is runtime-qualified, independently of `0007`'s gate | `test_the_migration_runtime_gate_is_independent_of_0007s` · `test_recorded_confinement_behaviours_must_reproduce_live` · `test_the_authorizer_probes_all_hold_on_this_runner` — **measured today** |
| **M16** every outcome is a member of the closed vocabulary | `test_invalid_sql_returns_migration_failed_not_an_exception` · `test_a_wrong_unique_constraint_is_a_result_mismatch` · `test_the_outcome_vocabulary_is_closed` — **measured today** |
| **M17** the failure boundary covers evidence loading, context entry and the connection | `test_a_malformed_accepted_manifestation_fails_closed` · `test_a_malformed_path_field_fails_closed` · `test_a_non_database_file_is_a_closed_refusal` · `test_an_unopenable_path_is_a_closed_refusal` — **measured today** |
| **M18** malformed current-algorithm records poison their artifact class; foreign records fail cardinality | `test_a_malformed_current_migration_runtime_record_poisons` · `test_a_foreign_identity_path_record_fails_the_artifact` · `test_a_missing_algorithm_field_is_malformed_not_superseded` — **measured today** |
| **M19** confinement denial means `SQLITE_AUTH`, nothing else | `test_a_permissive_authorizer_fails_every_denial_probe` · `test_the_release_probe_holds_a_real_savepoint` — **measured today** |
| **M20** an authority authorises exactly one operation, inside its window, on its canonical store | `test_an_authority_is_single_use_and_cannot_migrate_a_replacement` · `test_a_retargeted_symlink_unbinds_the_authority` · `test_an_unparseable_or_expired_authority_is_refused` — **measured today** |

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

**Claim, bounded (round 2):** a version-1 store can be brought to version 2 by
the declared migration under an explicit offline authority, or is refused with
a closed reason. **Skipped-release upgrading is not claimed** — it is the
mandatory requirement the first two-step spec must demonstrate.

**Limits:**

- **Cooperating concurrent openers are serialised** by the write lock (§5b);
  **stale old-version processes are unsupported unless quiesced** — the
  distinction round 2 required in place of v3's contradictory "not
  multi-process" line.
- **The `MigrationAuthority` is an attestation, not a verification** — ruled
  acceptable at the library boundary in round 3: a library cannot prove every
  process on the host has stopped, so it refuses without the attestation,
  validates its types and bindings exactly, and never auto-migrates. What the
  host attests, the host owns.
- **Not a sandbox.** §4b's authorizer defends against an accidental declared
  statement. **Migration statements are trusted code.**
- **Not equivalence.** A third-party database that is equivalent but differently
  written is refused, per `0007` §4a.
- **Bounded by the qualified runtimes.** `0007`'s runtime gate applies; a
  migration path's output must be recorded per qualified runtime.

---

## 9. Brief for the external reviewer

**Round 5 of this spec. All five round-4 blockers and both additional
corrections taken; every probe reproduced first** — the `objects: 1`
TypeError at context entry, the list-valued hash crash, the raw
`file is not a database`, the silently filtered malformed migration-runtime
record, the foreign-identity path record, the savepoint-less `RELEASE` probe
reporting denial under a fully permissive authorizer, the replayed authority
migrating a replacement store, and the retargeted symlink. Per your v6
guidance, **the migration and the shared planner are unchanged** — every
edit is in the evidence validators, the probes, the authority, and the entry
points' failure boundary.

1. **Totality, actually** (finding 1): every validator type-checks before
   iterating, hashing or keying; context entry is inside the boundary; the
   connection is inside the boundary. Your probes are regressions:
   malformed nested evidence at any depth → `unsupported-sqlite` (schema
   class) or `migration-evidence-missing` (path class); non-database bytes →
   `invalid-store`; missing parent directory → `store-unopenable` — two new
   frozen members, §5d. Registry validation reports mixed, string and
   bool-typed keys instead of raising.
2. **Malformed current records poison** (finding 2):
   `migration_runtime_artifact_problems` — complete validity for every
   current-algorithm record, identity uniqueness, contradiction rejection,
   resolution to an active schema-runtime record, single-active-runtime
   policy. Your `{"migration_evidence_algorithm": 1}` record now disqualifies
   the runtime; a missing algorithm field is malformed, not superseded.
3. **Cardinality is artifact-wide** (finding 3): expected = every active
   build identity × declared step × accepted source; actual keys must equal
   it exactly; every current path record must resolve to both
   qualifications. Your foreign-identity duplicate now fails both validators
   and the operation refuses; a features-as-list foreign record is reported,
   not skipped.
4. **Denial means `SQLITE_AUTH`** (finding 4): every probe setup is a valid
   statement sequence — the `RELEASE` probe holds a real savepoint created
   before the authorizer is installed — and only an authorization error
   counts (error code on 3.11+, message fallback on 3.10, stated in code).
   Your falsifier is the regression test: a fully permissive authorizer
   flips all twelve denial probes False. `denies_rollback` added; the
   artifact is regenerated under the twelve-probe vocabulary.
5. **The authority has a lifecycle** (finding 5): the contract is **frozen
   in §5b as a table, not an implementation note** — canonical realpath
   binding (symlinks resolve at mint and consumption), source-manifestation
   and step binding, backup and release references, RFC 3339
   issuance/expiry window, and **single-use consumption spent on
   acceptance**. Your replay probe now refuses with the replacement store
   untouched; your symlink probe refuses with neither store touched; §5e
   names the migration audit as the durable consumer at implementation.

**Also per your rulings**: the artifact is described as *committed, not
immutable* (§5c states exactly what is and is not claimed); the migration
audit is load-bearing spec text (§5e).

**Where I am least confident:** the draft/production consumption split for
single-use authorities — in-process consumption demonstrates the semantics
but only the audit-backed durable form survives a restart, and that lands
with `0008`'s implementation. The residual host-trust statement in §5b (an
atomic identical-shape swap inside the validity window) is stated as
narrowly as I can make it; if it is still too wide, that is the judgement
left.

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~M-Q1~~ | **RULED by round 9, 2026-08-03: wait.** `0013` must not reach `accepted` before it is reviewed **against an actual migration** — that is the principle that justified the `0007` scope cut, and it applies equally to the replacement. **The first case is `0008`'s `confirmations` table**: accepted, simple, additive, already blocked on `0013`, and independent of `0006`'s unresolved source-identity design. **`0013` may generalise only what that real migration demonstrates.** | resolved | external | — |
| ~~M-Q2~~ | **RULED (round 1) adopt-with-conditions; condition RESOLVED (round 2) by the offline boundary; boundary APPROVED (round 3) at the library level** with the narrowed claim (§5b: ordinary opening cannot initiate migration; the trusted deployment authority owns quiescence, fencing and backup validity) and the authority binding conditions (exact types, bound to store/migration/operation; release-identity binding at implementation). | resolved | external | — |
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

---

## 12. Round 2 review disposition

**Verdict: concrete migration and direction approved; v3 deferred.** 4
blockers, 4 inconsistencies, all taken.

| # | finding | closed by |
|---|---|---|
| 1 | the instrument bypassed `0007`'s gates | **integrated planner** — runtime gate first; *current* validates + repairs; malformed stamped v2 refuses. Regression tests for both probes |
| 2 | path evidence attested less than it authorised | **full-manifest hashes** (acceptance digest is rebuildable-blind, measured); defined canonical bytes; exact cardinality; complete output reproduced |
| 3 | quiescence was prose over auto-migration | **offline boundary**: `migration-required` on ordinary open; `MigrationAuthority`; closed failure model. M-Q2's condition resolved |
| 4 | one-transaction was a calling convention | **executable precondition**, re-checked per statement; the autocommit partial-migration case is a regression |

---

## 13. Round 3 review disposition

**Verdict: concrete v1→v2 approved directionally; v4 deferred for a focused
v5.** Four load-bearing guarantees were false in the executable instrument;
all four taken, plus the M-Q2 ruling and every additional correction.

| # | finding | closed by |
|---|---|---|
| 1 | the "integrated planner" was a second hand-written state machine — empty and unstamped stores answered `unexpected version 0`; a malformed stamped source was promised `migration-required`; a squatting table raised `OperationalError` | **the second machine is deleted.** The instrument installs the draft registry + evidence into the production kernel and calls `open_versioned()`; `0007` gains the older-row hook its §4 always delegated to `0013`. Adversarial tests across empty / unstamped / foreign / malformed±authority / squatting-name stores |
| 2 | path evidence was generated from the live migration code — an appended `DELETE FROM edges` authorised itself; the recorded source hash was never consulted; the record omitted the frozen contract's fields | **evidence is a committed artifact** (`migration_0013_evidence.json`): generator, validator (record-level consistency rules incl. output resolution), and consuming planner all exist in the draft; selection over the full frozen key; both alteration probes refuse `migration-evidence-missing`, data and stamp untouched |
| 3 | `0007`'s runtime qualification cannot attest authorizer behaviour | **migration-runtime qualification**: eleven required confinement probes per build identity, recorded and re-verified live at consumption; `migrate_store` requires both gates |
| 4 | the closed failure model leaked raw exceptions and free-form strings | **total mapping** to the closed vocabulary; `Outcome` refuses non-members; `migration-failed` and `migration-result-mismatch` demonstrably reachable via crafted-evidence tests; §5d states the package-consistency exception |
| M-Q2 | attestation model | **approved at the library boundary** with narrowed wording (§5b verbatim) and binding conditions: exact-typed authority bound to store, migration digest and operation; release-identity binding and freshness at implementation; no authority parameter on tenant-facing opening |
| a | §4c still said capability "authorises" | moved to §4c-deferred, present-tense claim removed |
| b | simulator crashed past its own refusal | gates first; clean `rc 2` on an unqualified runtime — regression test |
| c | README claimed five failing tests on 3.46.1 | package README states the measured behaviour and the artifact-regeneration path |
| d | §5c lacked record-level consistency rules | the four rules (plus output resolution) are spec text with adversarial tests for missing / extra / stale-algorithm / duplicate / contradictory records |

---

## 14. Round 4 review disposition

**Verdict: architecture standing — planner, evidence consumption,
qualification design and the concrete migration all approved; v5 deferred on
five falsifiable gaps.** All five taken, plus both additional corrections and
the acceptance-boundary ruling; the migration and the shared planner are
unchanged per the reviewer's v6 guidance.

| # | finding | closed by |
|---|---|---|
| 1 | the closed contract was not total — malformed nested evidence raised `TypeError` at context entry, a list-valued hash crashed selection-key construction, non-database bytes and unopenable paths escaped as raw SQLite errors | **type-checks before every iterate/hash/key**; context entry and the connection inside the boundary; two new frozen outcomes `invalid-store` / `store-unopenable` (§5d); registry key-type totality (`True == 1` measured); adversarial tests per nested field class |
| 2 | a malformed current-algorithm migration-runtime record was silently filtered while qualification held | **`migration_runtime_artifact_problems` poisons**: complete validity per current record, identity uniqueness, contradiction rejection, resolution to an active schema-runtime record, single-active-runtime policy; missing/mistyped algorithm = malformed, not superseded |
| 3 | path cardinality ignored foreign runtime identities — an unattested prospective record accumulated | **artifact-wide exact cardinality**: expected = every active identity × step × accepted source, actual keys equal it exactly; every current path record resolves to both qualifications |
| 4 | the `RELEASE` probe was a false positive (no savepoint; any `DatabaseError` counted as denial) — the qualification agreed with itself about a behaviour never established | **denial means `SQLITE_AUTH`** (error code on 3.11+, message fallback on 3.10); every setup is a valid statement sequence; `denies_rollback` added (twelve probes); the permissive-authorizer falsifier is the regression test |
| 5 | the authority was indefinitely replayable and bound to a path string — a replacement store migrated under an attestation belonging to the earlier file; a retargeted symlink migrated the wrong store | **the lifecycle contract is frozen in §5b**: canonical realpath at mint and consumption, source + step + migration binding, backup and release references, RFC 3339 issuance/expiry window, single-use consumption spent on acceptance; §5e names the audit as the durable consumer |
| a | registry validation raised on malformed keys | exact-int key typing before `max()`/`sorted()`/arithmetic, reported not raised |
| b | "immutable" overclaimed the artifact | *committed, not immutable* — §5c states exactly what is and is not claimed |
| c | `operation_id` had no durable consumer | §5e: the migration audit is load-bearing spec text and the authority's durable consumer at implementation |
