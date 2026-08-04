# Feature spec: on-disk store migrations

Spec-Status: in review
Spec-Requires: 0007

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v10)** — round 8: *architecture standing; v9 deferred on five
> load-bearing gaps*. All taken; concrete migration, evidence selection key
> and ordinary planner states untouched: **TEMP confinement is probed per
> object class** (v9's one probe created a TEMP *table*; SQLite gives tables,
> indexes, views and triggers different action codes, and a weak authorizer
> allowing TEMP triggers passed all twelve — each class now has its own
> `SQLITE_AUTH` probe, fifteen total); **the audit machine enforces its
> schema and state** (v9 accepted both terminal events for one operation,
> arbitrary event names and payloads — activation is now one transaction,
> `migration_operations`/`migration_audit_events` with the event enum, exact
> terminal payload schema, and **at most one terminal event per operation**);
> **terminal facts come from the kernel** (v9 inferred `resulting_version`
> from the outcome string and reported v1 for a v2 store — `open_versioned`
> now returns an `OpenResult` carrying `store_changed`,
> `transaction_committed`, `resulting_version`); **release identity fails
> closed** (v9 substituted a shared `+unknown` sentinel on an unreadable
> input, re-opening the cross-build hole — acquisition now raises
> `PackageConsistencyError`); and **timestamps are canonical and capped**
> (v9 accepted a 100 kB fractional-second string — a 32-char
> `YYYY-MM-DDTHH:MM:SS.ffffff+00:00` grammar, checked before parse, with a
> canonical round-trip). The resolution/refusal split was APPROVED.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v10 |
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
(135 tests: every round-2 through round-8 probe as a regression, the full inherited
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
(round 3). **And the dedicated operation is a MODE of the shared planner,
not a second state machine** (round 6, finding 1: v7's operation reached the
planner's new-row and CREATED a fresh v2 store after its attested v1 source
was deleted — likewise over an empty replacement database). In migrate mode:
an accepted older source runs the migration hook; a current destination is a
permitted no-op (`current`, the race case); **a new or empty store refuses
`migration-source-missing` and never creates** (the connection itself is
`mode=rw` and cannot materialise a file; a nonexistent path refuses with the
path left uncreated); an unstamped shape is never adopted (`allow_adopt` off
— the candidate restriction already refuses it as `foreign-shape`); foreign,
malformed and newer keep their normal closed refusals. The creation seam is
the kernel's `new=` hook, the exact mirror of the older-row hook. The `MigrationAuthority` is an **attestation the library validates
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
| `backup_ref` | the backup this operation made | the frozen token grammar: ASCII `[A-Za-z0-9._+:/-]`, ≤ 128 chars, no whitespace — a grammar closes the prose channel a byte cap only bounded (round 6); normalization is moot because the charset admits one representation |
| `release_ref` | the minting release/deployment | must equal the RUNNING release identity — **frozen: `veracium-<version>+<source-digest>`**, the digest being the FULL sha256 (round 7: 12 hex chars were 48 bits against an adversary who constructs builds) over a **framed, domain-separated** encoding: `"veracium-release-identity-v1"` then, per file in the frozen ordered list (this instrument, the `0007` kernel), length-framed name and length-framed content — round 7 measured a docstring moved across the raw-concatenation boundary keeping the identity byte-identical, no hash collision required. Representation: the token grammar (128 chars holds it); source of truth: the running tree's own bytes, identical in editable and archive builds; comparison: exact equality; rotation: any covered-file change. Production may substitute a signed release-artifact digest |
| `operation_id` | this one migration operation | **single-use over the COMPLETE operation** (round 5) — consumed at acceptance, before any store access; an opaque UUID-shaped token (the grammar checks shape, not version/variant bits — round 7's wording ruling) |
| `issued_at` · `expires_at` | the validity window | timezone-aware ISO 8601 as accepted by the parser (round 6 narrowed the wording); `issued ≤ now < expires`; `expires − issued ≤` the frozen `MAX_AUTHORITY_LIFETIME` (1 h); **no clock-skew allowance** — skew handling, if production ever permits it, must be explicit and bounded |
| `evidence_digest` | the exact evidence artifact consumed | sha256 of the operation's SNAPSHOT bytes (round 7: one read feeds digest, comparison, parse and planner — v8's two reads were a TOCTOU, measured); a regenerated artifact unbinds the authority |
| *(all three digests)* | — | exactly 64 lowercase hex, statically; and the authority's (from, to, source, migration) key must resolve to **exactly one current path record in the snapshot** before consumption — so even a no-op `current` operation was valid for one exact evidenced source (round 7: v8's current branch accepted a garbage source digest) |

An expired, future-issued, over-long-lived, previously consumed,
retargeted, source-mismatched, wrong-release, mistyped or unbound authority
refuses `migration-quiescence-required`; a resolution failure — bindings no
current path record evidences — is an ARTIFACT property and refuses
`migration-evidence-missing`. **Minting never creates**: `make_authority`
opens the source `mode=rw` and refuses when there is no store or the store
is not an accepted source — round 7 measured plain `connect()`
materialising a zero-byte database at a missing path and returning an
authority over the empty manifestation. A nested draft context pinned to a
different artifact digest than the installed one refuses rather than
silently sharing (round 7's second TOCTOU variant). **Consumption covers the complete
dedicated operation** (round 5): once static validation accepts an operation
id — before the store is even opened — it is spent, and EVERY subsequent
outcome spends it: `migrated`, a no-op `current`, an evidence refusal, a
lost race, even `locked`. Round 5 measured why the narrower hook-only rule
fails: an authority whose operation found the store already current was
never consumed and later migrated a replacement store at the same canonical
path; the five-opener race leaves four such authorities. The cost is stated
plainly: an operation that ends in `locked` or `store-unopenable` has spent
its authority and the host mints a fresh one — operationally correct, since
the world changed while it waited. **Consumption is in-process in the draft
and durable in production — the migration audit (§5e) is the durable
consumer.** What remains host-trust, stated rather than
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
`migrate_store`.

**Writes are monotone over the `MigrationEvidenceRevision`** — the triple
`(migration_evidence_algorithm, manifest_algorithm, draft_schema_version)`
(round 5: the writer replaced artifacts seeded with future revisions of
every component — the downgrade class `0007`'s runtime-evidence writer
already refuses) — **and the complete write operation is serialized by an
interprocess lock** (round 6: a pre-generation inspection was a
check-then-replace race — a future artifact published while an older writer
generated was downgraded, measured with a forced interleaving). The
sequence: acquire the writer lock · re-read and validate the existing
revision UNDER it · generate · validate the complete prospective artifact ·
stage to a writer-unique temporary · publish · release. *(The draft's lock
is `fcntl` — evidence GENERATION is POSIX-only in the draft, stated as a
platform bound per round 7; production may adopt cross-platform locking.
Consumption has no platform bound.)*

**Readers take ONE byte snapshot per operation** (round 7, finding 1): the
artifact bytes are read once; the digest is computed over those bytes; the
authority's `evidence_digest` is compared against that digest; those same
bytes are parsed; and that exact object enters the planner context — nothing
re-reads the path mid-operation. Concurrent nested contexts must agree on
the installed digest or refuse. The inspection
**refuses without changing a byte** when any existing component exceeds the
tool's own, or when the existing revision is unreadable (overwriting what
cannot be identified is data loss; an explicit delete is the only way past
it). Same-revision replacement is the explicit
active-runtime policy: regenerating on a new runner replaces the whole
artifact at equal revision — the reviewer's disposable-copy workflow. The
complete prospective artifact validates before the file is replaced. Every
revision scalar is **exact-typed** (`type(v) is int` — round 5 measured
`True`, `13.0` and `2.0` passing coercive equality at the top level and in
path records; a numerically equal wrong-typed value is malformed and
poisons). The artifact also records its **generator** (tool and repository
commit, `unavailable` outside a checkout) — diagnostic provenance, never a
substitute for the declaration digest.

One path record carries:

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
failures** — and the boundary is **genuinely outermost**: parameter
validation, path conversion, canonicalization, draft-context entry, evidence
loading, the database connection, and planner execution all sit inside it.
Round 5 measured the v6 boundary starting too late — an embedded-NUL path
escaped as `ValueError` from `lstat` and a mistyped `busy_timeout_ms` as
`TypeError` from division, both BEFORE any mapping ran; a public entry point
claiming totality cannot require its callers to know which preprocessing
precedes the boundary. (Round 4, finding 1: v5's boundary started
after context entry, so a malformed nested evidence field raised `TypeError`
out of the validators, non-database bytes raised `DatabaseError`, and an
unopenable path raised `OperationalError`; round 3 had closed the
invalid-SQL and free-form-string escapes.)

| failure class | closed outcome |
|---|---|
| a malformed CALL — mistyped/out-of-range `busy_timeout_ms` (exact int, 1..600000), a non-pathlike path argument | `invalid-request` |
| the path cannot be opened, canonicalized or represented at all — missing parent, embedded NUL, over 4096 bytes | `store-unopenable` |
| the bytes are not readable as a SQLite database | `invalid-store` |
| lock acquisition exhausted | `locked` |
| unqualified schema- or migration-runtime; malformed or poisoned schema/runtime evidence — **at any nesting depth** | `unsupported-sqlite` |
| source not an accepted manifestation | `stamped-shape-mismatch` / `foreign-shape` |
| invalid, unbound, expired, consumed, retargeted, cross-build or evidence-unbound authority | `migration-quiescence-required` |
| the dedicated operation finds no source where its authority attests one — vanished file, empty or truncated replacement, nonexistent path | `migration-source-missing` (the path stays uncreated) |
| the attempted audit record cannot be written (production) | `migration-audit-unavailable` — nothing consumed, no store access |
| absent, ambiguous, malformed, foreign or non-matching path evidence | `migration-evidence-missing` |
| SQL execution or protocol failure during the migration | `migration-failed` |
| executed output differs from the recorded output | `migration-result-mismatch` |
| an unforeseen failure in THIS library — never a store or migration semantic | `internal-error`, phase named in the diagnostic, commit state unknown unless the phase proves otherwise (round 7: labelling a library defect `invalid-store` invited hosts to restore a healthy database) |

**Every validator type-checks a field before iterating, hashing, sorting, or
using it as a key** — the round-4 totality rule; a validator escape at
context entry is itself treated as a malformed artifact and fails closed.

Successes are equally closed: `created` · `adopted` · `current` · `migrated`.
The entry points return an `Outcome` — a value that string-compares as its
closed member and carries diagnostics separately, and that **refuses to exist
outside the vocabulary**. Detailed exception text rides the diagnostic, never
the branch value. Exactly TWO deliberate, NAMED exceptions escape the
boundary (round 6 made both classes explicit): `PackageConsistencyError` —
the build's own pieces disagree, a property of a broken package, not of the
store — and `MigrationAuditWriteError` (§5e) — the audit of an irreversible
operation failed after the operation touched the store, and its `committed`
flag is the caller's decision input. Everything else, including whatever a
`PathLike.__fspath__` or a diagnostic `__repr__` raises, maps to the closed
vocabulary.

## 5e. The migration audit and the durable authority state machine

*(Round 4 made the audit load-bearing; round 5 requires the durable
consumption rules frozen as spec text, because they are single-use
semantics, not audit formatting.)* Migration is irreversible, so the
production migration operation appends audit records the way `0007` §4e's
adoption path does: an **attempted** record before execution and a
**completed or failed** record after, each carrying the closed outcome, the
authority's identity (`operation_id`, `release_ref`, issuance window),
source and output versions with their manifestation digests, the migration
declaration digest, and the opaque `backup_ref` — all under the frozen
opaque-token caps (§5b), so audit fields cannot become prose channels.

**The frozen durable model is TWO tables, not one** (round 7, finding 3: a
single append-only table whose `operation_id` is globally unique cannot hold
an attempted AND a terminal event for one operation — the previous freeze
was internally inconsistent):

```
migration_operations                    migration_audit_events
    operation_id  PRIMARY KEY               event_id       PRIMARY KEY
    authority bindings                      operation_id   FOREIGN KEY
    activation state                        event · occurred_at · payload
    attempted_at                            UNIQUE(operation_id, event)
```

**The operation-row insert IS the compare-and-set consumption.** The rules:

| rule | contract |
|---|---|
| duplicate operation id on activation | the authority IS consumed — `migration-quiescence-required` (round 7 split this from the outage case v8 conflated) |
| audit storage unavailable before activation | **`migration-audit-unavailable`** — no store access, nothing consumed (a failed insert consumed nothing); a retry may re-present the authority |
| migrated and committed, terminal write fails | **`MigrationAuditWriteError(committed=True, resulting_version)`** — the facts come from the kernel's `OpenResult` (`store_changed`, `transaction_committed`, `resulting_version`), NEVER inferred from the outcome string (round 8, finding 3: v9 read `resulting_version` from the label and reported v1 for a lost-race `current` whose store was already v2); a retry opens `current`. Mirrors `0007` §4e |
| rolled back, terminal write fails | store unchanged, authority spent; **`MigrationAuditWriteError(committed=False)`** |
| `current` with no repair | terminal record written (outcome `current`); a terminal-write failure is `committed=False` — nothing changed |
| `current` with a committed rebuildable repair | the repair transaction committed: a terminal-write failure is `committed=True`, resulting version unchanged — requires the production planner to report repairs (a precise implementation obligation; the draft cannot observe the kernel's repair) |
| every consumed outcome | writes its terminal event — a spent authority with no record is indistinguishable from a crash. Executable in the draft: `DraftAuditStore` implements both tables in-process, `UNIQUE(operation_id, event)` enforced, terminal records measured for `migrated` and the no-op `current` |

**The frozen record schema** — every field typed and capped, so a record is
data, not prose:

```
schema_version        int, 1
event                 "migration_attempted" | "migration_completed" | "migration_failed"
operation_id          the op-<uuid4> grammar
store_path            canonical, ≤ 4096 fs-encoded bytes
from_version          int          to_version   int
source_acceptance_digest · output_acceptance_digest      64 lowercase hex
migration_declaration_digest · evidence_digest           64 lowercase hex
outcome               a member of §5d's closed vocabulary (completed/failed only)
release_ref · backup_ref                                 the token grammar
issued_at · expires_at · occurred_at                     timezone-aware ISO 8601
```

Lands with the `0008` implementation; the draft demonstrates the complete
lifecycle in-process — atomic consumption under concurrency, the typed
`MigrationAuditWriteError` contract (declared, with `committed`,
`operation_id`, store identity and resulting version), and the
`migration-audit-unavailable` outcome — so the production sink implements a
frozen contract rather than designing one.

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
| **M21** evidence writes are monotone over the `MigrationEvidenceRevision` | `test_a_future_evidence_revision_is_never_overwritten` (three components, byte-unchanged) · `test_an_unreadable_existing_revision_refuses_regeneration` — **measured today** |
| **M22** consumption covers the complete operation, atomically | `test_an_authority_finding_the_store_current_is_still_consumed` · `test_authorities_losing_the_concurrent_race_are_consumed` · `test_operation_consumption_is_atomic_under_concurrency` — **measured today** |
| **M23** the validity window is real: `issued ≤ now < expires`, lifetime-capped, release-bound | `test_a_future_issued_authority_is_refused` · `test_an_authority_lifetime_above_the_frozen_maximum_refuses` · `test_an_authority_from_a_different_release_refuses` · `test_an_oversized_token_field_refuses` — **measured today** |
| **M24** scalar typing is exact and the boundary is outermost | `test_coerced_top_level_scalars_poison_the_artifact` · `test_a_coerced_path_algorithm_poisons_the_paths` · `test_an_embedded_nul_path_is_a_closed_outcome` · `test_a_mistyped_timeout_is_a_closed_outcome` · `test_a_non_pathlike_argument_is_a_closed_outcome` · `test_an_oversized_path_is_a_closed_outcome` — **measured today** |
| **M25** a migration never creates or adopts | `test_a_deleted_source_cannot_become_a_new_store` · `test_a_truncated_source_cannot_become_a_new_store` · `test_an_empty_database_replacement_cannot_be_migrated` · `test_an_unstamped_current_shape_replacement_is_refused_not_adopted` · `test_ordinary_open_still_creates` — **measured today**; every case leaves the path uncreated or byte-unchanged |
| **M26** evidence publication is serialized and monotone under concurrency | `test_a_concurrent_future_publication_is_not_downgraded` (two-process barrier) — **measured today**; the round-5 static seeds remain |
| **M27** the boundary is Unicode- and PathLike-safe | `test_a_non_utf8_bytes_path_works_end_to_end` · `test_a_pathlike_that_raises_is_a_closed_outcome` · `test_a_surrogate_token_field_is_a_closed_refusal` — **measured today** |
| **M28** the audit contract's two named escapes exist | `test_the_audit_contract_is_frozen` — **measured today**; the enforced state machine and record schema are M36/M37 and §5e (round 8: M28/M32 no longer claim the complete lifecycle is measured — schema validation, atomic activation, terminal exclusivity and the four terminal cells are the M36/M37 evidence) |
| **M29** the release identity is immutable per build and the evidence artifact is bound | `test_the_release_identity_is_content_derived` · `test_a_version_only_release_ref_is_refused` · `test_a_cross_build_authority_is_refused` · `test_an_authority_binds_the_evidence_artifact` — **measured today** |
| **M30** one evidence snapshot per operation; nested contexts agree or refuse | `test_the_operation_consumes_the_bytes_the_authority_bound` · `test_a_nested_context_never_silently_swaps_artifacts` — **measured today** |
| **M31** the release identity binds the file boundary at full digest length | `test_moving_bytes_across_the_file_boundary_changes_the_identity` — **measured today** |
| **M32** consumption is split from audit outage; both are executable | `test_audit_unavailability_consumes_nothing_and_is_retryable` · `test_a_duplicate_operation_is_consumed_not_an_audit_outage` · `test_terminal_records_are_written_for_migrated_and_noop_current` · `test_a_failed_terminal_write_raises_the_typed_error` — **measured today**. Schema/atomicity/exclusivity/terminal-cells are M36/M37 |
| **M33** source binding is static, and minting never creates | `test_an_authority_binds_the_source_manifestation` · `test_minting_never_creates_a_store` · `test_minting_refuses_a_non_accepted_source` — **measured today** |
| **M34** internal failures are `internal-error`, never store semantics | `test_an_internal_defect_is_not_a_store_outcome` · `test_check_evidence_is_total_over_non_mapping_runtime_members` — **measured today** |
| **M35** each TEMP object class is qualified independently, `SQLITE_AUTH`-specific | `test_the_temp_probes_cover_every_object_class` · `test_an_authorizer_allowing_temp_triggers_fails_qualification` — **measured today** |
| **M36** the audit store enforces schema, event enum and one-terminal-per-operation, atomically | `test_the_audit_store_rejects_two_terminal_events` · `test_the_audit_store_rejects_unknown_events_and_payloads` · `test_the_operation_row_carries_the_full_frozen_schema` · `test_activation_is_atomic` — **measured today** |
| **M37** terminal audit facts come from the kernel, correct on every branch | `test_the_current_branch_reports_the_actual_resulting_version` · `test_the_current_with_repair_branch_reports_committed_true` · `test_the_migrated_branch_reports_committed_true` — **measured today** |
| **M38** release identity acquisition fails closed | `test_an_unreadable_covered_file_fails_closed` · `test_a_missing_version_declaration_fails_closed` · `test_no_unknown_sentinel_authority_migrates` — **measured today** |
| **M39** every persisted timestamp is canonical and length-capped | `test_a_hundred_kilobyte_timestamp_is_refused` · `test_a_noncanonical_but_valid_instant_is_refused` · `test_minted_timestamps_are_canonical` — **measured today** |

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

**Round 9 of this spec. All five round-8 blockers and the four additional
corrections taken; every probe reproduced first** — the weak authorizer
allowing TEMP triggers past all twelve v9 probes, both terminal events
accepted for one operation, the lost-race `current` reporting
`resulting_version=1` for a v2 store, the `+unknown` sentinel identity, and
the 100 kB timestamp. Per your v10 bar the concrete migration, evidence
selection key and ordinary planner states are untouched, and the
resolution/refusal split you approved is unchanged.

1. **Per-class TEMP qualification** (finding 1): table, index, view and
   trigger each get their own `SQLITE_AUTH`-specific probe (fifteen total).
   Your falsifier is the regression — a full-replacement authorizer denying
   temp tables while allowing temp triggers flips `denies_temp_trigger`
   False and fails runtime qualification.
2. **Enforced audit schema and state machine** (finding 2): two tables,
   activation as one transaction (operation row + attempted event together),
   the event enum, the exact terminal payload field set and types, and
   **one terminal event per operation** via a compare-and-set `state`.
   Unknown events, arbitrary payloads and a second terminal all reject.
3. **Kernel terminal facts** (finding 3): `open_versioned` returns an
   `OpenResult` carrying `store_changed`, `transaction_committed`,
   `resulting_version`; the wrapper uses them, never the label. All four
   cells are exercised with a forced terminal-write failure — lost-race
   `current` now reports version 2 and `committed=False`; `current` with a
   committed rebuildable repair reports `committed=True`; `migrated` reports
   `committed=True`, version 2.
4. **Fail-closed release identity** (finding 4): an unreadable covered file,
   an unreadable or version-less `pyproject.toml`, or a
   non-grammar-safe version each raise `PackageConsistencyError` before any
   authority is minted or accepted — no sentinel is ever a valid component.
5. **Canonical, bounded timestamps** (finding 5): a 32-char
   `YYYY-MM-DDTHH:MM:SS.ffffff+00:00` grammar checked before parse, UTC,
   with a canonical round-trip; minting emits it; every persisted timestamp
   uses it. The 100 kB string and a valid-but-noncanonical instant both
   refuse.

**Additional corrections**: the record schema names and types `event_id`,
`state` and every field (no undefined names); `DraftAuditStore` stores the
full frozen operation-row schema; M28/M32 no longer claim the complete
lifecycle is "measured" (M36/M37 carry the schema, atomicity, exclusivity
and four-cell evidence); and `make_authority`'s defaulted `quiesced`/backup
are documented as test-only draft convenience, outside any production host
API.

**Where I am least confident:** the `current`-with-repair `committed` flag
depends on the kernel's `OpenResult.transaction_committed`, which the draft
reports as "drift was repaired". A production planner that repairs in a
separate transaction, or batches repair with the stamp differently, must
report the same fact — I have written that as an implementation obligation
in §5e, but it is the one terminal cell whose correctness rests on a
kernel contract the draft can only demonstrate, not freeze for production.

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

---

## 15. Round 5 review disposition

**Verdict: architecture standing — planner, evidence-selection, artifact
cardinality, qualification and DDL all approved; v6 deferred on four
falsifiable gaps.** All taken; migration, planner and evidence-selection
unchanged per the reviewer's constraint.

| # | finding | closed by |
|---|---|---|
| 1 | `write_evidence` overwrote artifacts seeded with future migration/manifest/schema revisions — the downgrade class `0007`'s writer refuses | **monotone writes over `MigrationEvidenceRevision`**: inspect before generating, refuse byte-unchanged on any newer component or an unreadable revision; same-revision active-runtime replacement stated as explicit policy; three parametrized byte-identity regressions |
| 2 | consumption lived only in the older-row hook — an authority whose operation found the store current stayed spendable and migrated a replacement; future-dated authorities validated; no lifetime cap; `release_ref` unchecked | **acceptance = consumption, before any store access** — every outcome spends; `issued ≤ now < expires` with no skew allowance; frozen 1-hour `MAX_AUTHORITY_LIFETIME`; release-identity binding (draft: in-tree `pyproject.toml`); 256-byte token caps; atomic CAS measured under concurrency |
| 3 | `True`/`13.0`/`2.0` passed coercive equality at top level and in path records; `artifact`/`generated_at` accepted integers | **exact scalar typing before equality** everywhere; `artifact` exact string; `generated_at` parsed timezone-aware; numerically-equal wrong types poison; parametrized regressions |
| 4 | the boundary began after path canonicalization and timeout arithmetic — NUL path and mistyped timeout escaped raw | **genuinely outermost boundary**: parameter validation, fspath/realpath, the 4096-byte cap, context entry, connection, planner; `invalid-request` joins the vocabulary for malformed calls |
| — | durable authority semantics under-specified | **§5e frozen**: unique durable key, atomic compare-and-set insertion as consumption, refuse-before-store-access on attempted-record failure, crash-between = spent + re-mint with fresh attestation, post-commit audit failure mirrors `0007` §4e |
| a | generator provenance | `generator: {tool, repository_commit}` recorded and validated — diagnostic, never a substitute for the declaration digest |
| b | token fields as prose channels | 256-byte caps in the draft; frozen opaque-token formats at implementation (§5b/§5e) |

---

## 16. Round 6 review disposition

**Verdict: approved architecture restated in full; v7 deferred on five
load-bearing problems.** All taken; the concrete migration, path evidence,
authorizer probes and ordinary planner states untouched per the reviewer's
constraint. The pre-lock consumption point was **ruled an acceptable
conservative policy** — the defect was what a consumed operation could still
do.

| # | finding | closed by |
|---|---|---|
| 1 | the dedicated operation CREATED a v2 store where its attested v1 source had vanished (deleted file, empty replacement) | **migrate mode of the shared planner**: `mode=rw` connection (cannot materialise files), nonexistent path refuses uncreated, the kernel `new=` creation seam raises `migration-source-missing`, adoption off; five regression cases, each path uncreated or byte-unchanged |
| 2 | evidence monotonicity was a check-then-replace race — a future artifact published mid-generation was downgraded (measured, forced interleaving); the shared `.tmp` path collided | **serialized publication**: interprocess lock around inspect-generate-validate-stage-publish; inspection under the SAME lock; writer-unique staging; two-process barrier regression |
| 3 | the boundary leaked `UnicodeEncodeError` (surrogate paths, surrogate tokens) and whatever `__fspath__` raised | **fs-aware conversions end to end** (kernel caps fs-encoded; a non-UTF-8-named store works), guarded `fspath` mapping any exception to `invalid-request`, `_safe_repr` diagnostics, token grammars matching on the str; exactly two NAMED escapes (`PackageConsistencyError`, `MigrationAuditWriteError`) |
| 4 | no representable post-commit audit-failure outcome; four state-machine cells undefined | **§5e completed**: `migration-audit-unavailable` (attempted record; nothing consumed), `MigrationAuditWriteError(committed=False/True)` for the rolled-back and committed cases, no-op `current` writes its record, frozen typed-and-capped record schema |
| 5 | `release_ref` was a mutable package version — an authority crossed builds sharing `0.4.8` | **content-derived identity** `veracium-<version>+<source-digest>` with representation/charset/size/source/comparison/rotation frozen; `evidence_digest` binds the exact artifact consumed |
| a | `--check-evidence` said "structural checks pass" for a foreign artifact with stripped paths | cardinality validation before the identity early-return — regression test |
| b | byte caps bound, not close, a prose channel | frozen token grammars (ASCII charset, `op-<uuid4>` shape); normalization moot by construction |
| c | "RFC 3339" overclaimed the parser | wording narrowed to what the parser accepts |

---

## 17. Round 7 review disposition

**Verdict: migrate-only mode, serialized writer publication and the Unicode
boundary held; v8 deferred on five issues.** All taken; the concrete
migration, path evidence, authorizer probes and ordinary planner states
untouched.

| # | finding | closed by |
|---|---|---|
| 1 | evidence-digest binding was a reader-side TOCTOU — digest from one file read, planner context from another; a nested context silently reused the outer artifact while a B-bound authority was accepted | **one byte snapshot per operation** feeding digest, comparison, parse and planner; `_draft(loaded=…)` takes the object; nested contexts pinned to a different digest refuse. Both variants are regressions |
| 2 | the release identity concatenated raw bytes — a docstring moved across the file boundary kept the identity (measured, no collision); 12 hex chars = 48 bits | **framed, domain-separated, full-length**: per-file length-framed name and content under `veracium-release-identity-v1`, frozen ordered list, full sha256; boundary-move regression |
| 3 | the audit freeze was internally inconsistent (globally unique `operation_id` vs attempted+terminal events); duplicate-vs-outage conflated; the `current`-with-repair cell undefined | **two tables** — operations (insert = CAS consumption) and events with `UNIQUE(operation_id, event)`; duplicate = consumed (`quiescence-required`), outage = `audit-unavailable` with nothing consumed (retry measured); all four terminal cells frozen; **executable `DraftAuditStore`** with terminal records measured for `migrated` and no-op `current` |
| 4 | `source_digest` was checked only in the older hook — a garbage digest passed the `current` branch; `make_authority` materialised a zero-byte database at a missing path | **static hex64 + resolution to exactly one current path record before consumption**; minting opens `mode=rw` and refuses missing paths (nothing created) and non-accepted sources |
| 5 | the residual catch-all labelled internal defects `invalid-store` / `migration-failed` — false semantics hosts act on | **`internal-error`** with phase named and commit state (`false`/`unknown`); the two named escapes remain the only escapes |
| a | `check_evidence` raised `AttributeError` on `runtimes: [42]` | the `0007` `active_records` accessor is total (both copies); regression at the `check_evidence` level |
| b | `fcntl` is POSIX-only | stated platform bound for draft evidence GENERATION; consumption unaffected |
| c | the grammar accepts any UUID-shaped value | wording: an opaque UUID-shaped operation token |

---

## 18. Round 8 review disposition

**Verdict (reviewer's, recorded verbatim in substance): architecture
standing — the concrete migration, shared planner, evidence snapshot,
static source binding and closed-outcome direction remain approved; v9
deferred on five load-bearing gaps.** The resolution-versus-refusal split
was **approved as written**. All five taken; migration, evidence selection
key and ordinary planner states untouched.

| # | finding | closed by |
|---|---|---|
| 1 | runtime qualification attested TEMP-table denial but not the TEMP-trigger behaviour the contract depends on — a weak authorizer allowing temp triggers passed all twelve probes | **per-class probes** (table, index, view, trigger), each requiring `SQLITE_AUTH`; fifteen total; weak-authorizer falsifier as regression |
| 2 | the two-table model still admitted both terminal events for one operation, arbitrary event names and payloads, and did not freeze activation as one transaction | **enforced schema + state machine**: activation is one transaction; event enum; exact terminal payload field set/types; one terminal per operation via CAS `state`; full operation-row schema |
| 3 | terminal-write failure misreported `resulting_version` for `current` (v1 for a v2 store) and could not represent a committed repair | **kernel `OpenResult`** carries `store_changed` / `transaction_committed` / `resulting_version`; the wrapper uses them; all four terminal cells tested under forced terminal-write failure |
| 4 | release identity fell open to a shared `+unknown` sentinel on unreadable inputs, re-opening the cross-build hole | **fail-closed acquisition** — unreadable covered file, unreadable/version-less pyproject, or non-grammar-safe version each raise `PackageConsistencyError` before mint or acceptance |
| 5 | `issued_at`/`expires_at` were unbounded, noncanonical audit channels (a 100 kB string validated) | **canonical 32-char grammar** capped before parse, UTC, canonical round-trip; applied to every persisted timestamp |
| a | `event_id`/`state` named but untyped in the diagram | the record schema now types every field including `event_id` and the `state` transition |
| b | `DraftAuditStore` stored a subset of the operation-row schema | the full frozen schema is asserted on insert |
| c | M28/M32 overclaimed "measured today" | reworded; M36/M37 carry the schema/atomicity/exclusivity/four-cell evidence |
| d | `make_authority` silently defaults `quiesced` and backup | documented as test-only draft convenience, outside any production host API |
