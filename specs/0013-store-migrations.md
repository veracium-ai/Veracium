# Feature spec: on-disk store migrations

Spec-Status: in review
Spec-Requires: 0007

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v26)** — round 23: *M-Q4 boundary respected; architecture
> standing; v26 deferred on three load-bearing semantic gaps plus two
> corrections* — all closed. This round tightened the **`on_committed` PROTOCOL
> contract** and the **exact authority carrier type**. **A successful migrate
> result requires its mandatory `on_committed` publication** (equal
> field-for-field) — a kernel returning `migrated` without the callback and
> without touching the store is `internal-error`, never retroactively
> establishing commit/position (finding 1). **`on_committed` validates the
> mode-aware SEMANTIC cell before freezing** — a structurally valid but
> impossible `migrated`/(F,F) publication is a defect, not a destination position
> (finding 2), via one shared validator used by both the callback and the
> returned result. **The authority carrier must be the EXACT `MigrationAuthority`
> type before any field access** — a subclass (which can intercept attribute
> reads to pass validation then raise after the real commit) is a closed refusal,
> never a raw escape that strands the operation attempted-only (finding 3 +
> correction A). The initial terminal fallback is moved inside the total
> post-consumption boundary; the independent gate covers the new cases
> (correction B). No finding relied on arbitrary private-state corruption or
> reopened a `0008` obligation; the M-Q4 boundary (§8a) held. Concrete migration,
> evidence key, release identity, source binding, one-snapshot reader, TEMP
> confinement and ordinary planner states untouched; the evidence artifact
> reproduces byte-for-byte.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v26 |
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
(every review probe carried as a regression — the count is whatever pytest
collects that round, not a number embedded here to go stale, per round 12's
correction C: the full inherited planner across empty/unstamped/foreign/
malformed/newer stores, the evidence gate's adversarial records, confinement
qualification, the closed failure model, and the stale-connection hazard
below).

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
| `operation_id` | this one migration operation | **single-use over the COMPLETE operation** (round 5) — consumed at acceptance, before any store access; an opaque `op-<uuid4>` token whose grammar enforces the version-4 and RFC-variant bits (round 16, correction C; round 18, correction D reconciles this row with the enforced grammar — the earlier "shape, not version/variant" wording predated M77 and is withdrawn) |
| `issued_at` · `expires_at` | the validity window | **the one canonical timestamp contract** (round 9, finding 5, applied uniformly): exact `str`, 32 ASCII chars, `YYYY-MM-DDTHH:MM:SS.ffffff+00:00`, UTC only, length-capped before parse, byte-equal to the reserialization of the parsed instant; `issued ≤ now < expires`; `expires − issued ≤` the frozen `MAX_AUTHORITY_LIFETIME` (1 h); **no clock-skew allowance**. EVERY persisted timestamp — `attempted_at`, `occurred_at`, and the evidence artifact's `generated_at` — uses this exact contract |
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
`PRAGMA`, `ATTACH`/`DETACH`, and **each TEMP object class — table, index,
view, trigger and virtual table — separately** each **observed and denied**;
restoration after rejection verified. **All SIXTEEN probes are required**
(round 8 split the single TEMP probe into per-class probes because SQLite
gives each class a distinct action code, and a weak authorizer allowing TEMP
triggers passed the one probe; round 9, finding 4 added
`denies_temp_virtual_table` after a weak authorizer allowing TEMP virtual
tables — whose constructor runs before the post-step leak assertion —
passed all fifteen). **A denial counts only when the failure is specifically
authorization** — `sqlite_errorcode == SQLITE_AUTH` (message-text fallback on
Python 3.10, which lacks the attribute). Round 4 measured why: the `RELEASE`
probe held no savepoint, so `no such savepoint` — raised under a fully
permissive authorizer — was recorded as a denial; every probe's setup is now
a valid statement sequence (the savepoint exists before the authorizer is
installed), and the permissive-authorizer falsifier flips every denial
result to False. Consumption does not trust the record: the probes are
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
loading, the database connection, planner execution, **the kernel-result
validation, and terminal-fact derivation** all sit inside it. **The kernel
result is a validated contract** (round 15, finding 2: v16 trusted the
`OpenResult`, so a kernel returning the bare string `"migrated"` made terminal
derivation raise `AttributeError` outside the boundary and stranded a consumed
operation) — a malformed result terminalizes as `internal-error` using the best
known facts, never escapes as `AttributeError`/`TypeError`/`ValueError`. **The
validation is COMPLETE and MODE-AWARE** (round 16, finding 3: v17 checked SHAPE
only, so `migrated`/¬changed, a `created`/`adopted` in migrate mode and
`migrated` at the wrong version passed and were misreported as audit outages) —
in migrate mode `migrated` must be changed+committed at `to_version`, `current`
must be `(¬changed,¬committed)` or `(changed,committed)` at `to_version`,
`created`/`adopted` are forbidden, and the result must agree with the
`on_committed` facts INCLUDING THE BRANCH LABEL (round 17, finding 3: v18
compared only the change/commit/version tuple, so a committed `migrated`
returned as `current` passed — the branches are not interchangeable). **The
`on_committed` sink itself VALIDATES and freezes, and distinguishes a proven
commit from a no-commit position** (round 17, finding 4; round 18, finding 3:
the kernel fires `on_committed` after its COMMIT even for a no-op `current` that
changed nothing, so (T,T) is a genuine commit that must survive a later
post-commit read error while a single (F,F) is only the store's resolved
position — the kernel fires the sink at most once, so a second, DIFFERENT
publication is a defect and a false `current`/(F,F) must never suppress a real
`migrated`/(T,T); v19 kept whichever fired first). **Terminal-fact derivation,
receipt validation and the ENTIRE post-consumption sequence are a TOTAL
boundary** (round 17, finding 5; round 18, finding 4: v19 left timestamp
generation, a hostile receipt equality, and `MigrationAuditWriteError`
construction itself outside the protected region — a receipt whose `status.__ne__`
raised, or an `audit_committed=1` the constructor rejects, leaked a raw third
exception after commit) — every step, including audit-commit sanitization and
the exception constructor, is inside the boundary; a defect terminalizes
`internal-error` from previously-FROZEN facts, a write failure is
`MigrationAuditWriteError`, no other class escapes, and a proven commit
survives. **A derivation fallback changes the PUBLIC outcome, not only the
durable record** (round 18, finding 5: v19 recorded `internal-error` durably yet
returned `migrated`) — the terminal write returns the effective outcome, so the
caller and the audit agree for every non-named return. **The connection's
cleanup scope begins the INSTANT it is opened** (round 15, finding 5) — every
opened connection is closed exactly once.
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
| the bytes are not readable as a SQLite database **WHILE `open_versioned` reads/interprets them** | `invalid-store` — classified by the READ SITE (round 13 f2, round 14 f4, round 15 f3). A `sqlite3.DatabaseError` from the runtime gate, `PRAGMA` setup, connection cleanup, or after a committed publish is `internal-error`; a `DatabaseError` from WITHIN the migration hook is `migration-failed` (round 15, finding 3: v16 still caught the whole `open_versioned` call, so a hook-raised error was mislabeled `invalid-store` on a healthy store). Only the kernel's own read of the bytes is `invalid-store` |
| lock acquisition exhausted | `locked` |
| unqualified schema- or migration-runtime; malformed or poisoned schema/runtime evidence — **at any nesting depth** | `unsupported-sqlite` |
| source not an accepted manifestation | `stamped-shape-mismatch` / `foreign-shape` |
| invalid, unbound, expired, consumed, retargeted, cross-build or evidence-unbound authority | `migration-quiescence-required` |
| the dedicated operation finds no source where its authority attests one — vanished file, empty or truncated replacement | `migration-source-missing` (the path stays uncreated). Absence is proven by an `lstat` ENOENT, NEVER by `os.path.lexists` (round 13 f3). The check is re-run FRESH on a mode=rw open failure (round 16, finding 5: the source can vanish BETWEEN the pre-open `lstat` and the open — a check-to-open race — and a confirmed post-failure ENOENT is `migration-source-missing`/`missing`, not `store-unopenable`/`unknown`) |
| the attempted audit record is PROVEN not written (production) | `migration-audit-unavailable` — nothing consumed, no store access, safe to retry |
| the attempted audit record write is UNKNOWN — neither confirmed nor disproved (production) | `migration-audit-state-unknown` — the authority MAY be consumed; the host queries the durable `operation_id` before retrying (round 12, finding 3) |
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
    release_ref · backup_ref                operation_id   FOREIGN KEY
    store_path · from_version · to_version  event  (the closed enum)
    source_digest · output_digest           occurred_at
    migration_digest · evidence_digest      payload (terminal only)
    issued_at · expires_at · attempted_at   UNIQUE(operation_id, event)
    state  attempted | terminal            ≤ one TERMINAL event per operation
```

**The COMPLETE operation-row schema** (round 9, finding 2) — every authority
binding plus the resolved destination identity; the `event_id` is an
opaque `ev-<uuid4>` token (round 10, restart-safe, no counter to resume);
the schema guard is a real check that survives `python -O`, not an
`assert`. **The audit store validates every field's TYPE and grammar, not
merely the field-name set, and freezes each value DEEPLY** (round 12,
correction A: v13 accepted `backup_ref=[]` on the strength of the name set
alone, and its `_readonly` proxied dict values but passed list values through
by reference, so mutating the caller's original list mutated the published,
supposedly-immutable row). Token grammars, 64-hex digests, canonical
timestamps, int versions and the path cap are all enforced at the store
boundary, and the published copy severs every alias to caller-held mutable
state. **The `event_id` GRAMMAR is enforced, not only its uniqueness** (round
12, correction B: v13 checked the primary-key collision but never
`ev-<uuid4>`, so a faulty generator's `ev-not-a-uuid` was accepted). **The
operation-row insert IS the compare-and-set consumption, and
the entire audit state is ONE immutable value published in ONE mutation**
(round 10, finding 1: v11's `self._ops, self._events, self._event_seq = …`
was three attribute stores, so a failure on the second left the first
applied and consumed an operation with no attempted event). The draft holds
the whole state as one `AuditState(ops, events, event_ids, seq)` behind one
attribute and publishes a new one with a single assignment; production uses
one DB transaction. A failure anywhere — construction, validation, or injected
on the publish — leaves the previous state intact.

**The published state is DEEPLY immutable, and `event_id` is enforced as a
primary key** (round 11, findings 4 and correction B): v12's `AuditState`
was a NamedTuple of LIVE dicts exposed through `_ops`, so a held reference
could flip an operation to `terminal` and drop its attempted event WITHOUT
the single publish, its lock, or validation — the atomicity the whole design
exists for. `ops` and `events` are now read-only proxies over read-only rows;
the single publish is the ONLY path that changes state. And v12 keyed events
by `(operation_id, event)` and never checked `event_id`, so a repeated
generator produced two events sharing one id; the draft carries the
`event_ids` frozenset and refuses a collision exactly as the production
table's `event_id` PRIMARY KEY would. The rules:

| rule | contract |
|---|---|
| duplicate operation id on activation | the authority IS consumed — `migration-quiescence-required` (round 7 split this from the outage case v8 conflated) |
| audit storage unavailable before activation (the typed `AuditStorageUnavailable` ONLY) | its `committed` flag maps to THREE structurally distinct outcomes (round 11, correction A + round 12, finding 3: v13 collapsed `False` and `None` into one retryable outcome, and DEFAULTED `committed` to `False` so an omitted fact was fabricated as proven-not-written). `committed=False` (PROVEN not written) → **`migration-audit-unavailable`**, nothing consumed, a retry may safely re-present the authority. `committed=None` (UNKNOWN — the default; an omitted fact is never a fabricated `False`) → **`migration-audit-state-unknown`**, the authority MAY be consumed, so the host must query the durable `operation_id` before retrying. `committed=True` (the row WAS written, response lost) → the authority IS consumed → **`migration-quiescence-required`**, mint a fresh one, **AND the wrapper still writes a terminal event** (round 14, finding 2: v15 marked the operation consumed only on the normal return path, leaving a durably-consumed authority with just an attempted record). **A library/validation defect during activation is NONE of these** — it is `internal-error` (round 10, finding 4: v11 mislabelled an `AssertionError` as retryable) |
| the activation result is not a valid receipt BOUND to the COMPLETE activation | **`internal-error` BEFORE any store access**. Activation returns a typed **`ActivationReceipt`** whose `problems()` validates every scalar (round 17 corr B: an `activated`+`audit_committed=False` is impossible), and the wrapper VERIFIES BOTH atomic records: the durable operation row BINDS the exact authority — `store_path`, release/backup refs, endpoints, ALL digests, the window, `state=attempted` — AND the durable attempted EVENT is complete and bound: the exact field set, a valid unique `event_id`, `operation_id` and `event` matching, and `occurred_at == row.attempted_at` (round 17, finding 1 bound only the row; round 18, finding 1: v19 verified the attempted event only by key existence, so a malformed attempted event under the right key let the irreversible operation proceed). `duplicate` is verified to BIND THE AUTHORITY too — a row for a different store is a collision, not a replay — and its `terminal_present` must AGREE with durable state (round 17, correction A + round 18, correction B: v19 bound the duplicate row to nothing and left `terminal_present` unvalidated) |
| the terminal write is not a COMPLETE `attempted → terminal` transition | **`MigrationAuditWriteError`**. Terminal publication returns a typed **`TerminalReceipt`** (`problems()` total, and a `recorded` receipt MUST be `audit_committed=True` — round 18, correction A: `False` is contradictory, `None` belongs to the failure path), and the wrapper VERIFIES the durable state is a complete transition: the operation row is now `terminal`, exactly ONE terminal event exists (no conflicting kind), its `event_id` is valid, unique and DISTINCT from the attempted event's, it carries the exact field set, and its payload EQUALS the request field-for-field (round 17, finding 2 verified the payload only; round 18, finding 2: v19 accepted a valid payload whose operation was still `attempted`, or whose terminal event reused the attempted `event_id`). A missing, malformed, contradictory, content-mismatched, or transition-incomplete receipt raises, never returns success |
| terminal write fails (any consumed ending) | **`MigrationAuditWriteError(operation_id, store_path, facts, audit_committed)`** carrying the SAME validated `TerminalFacts` the record would have held (round 13, finding 5). `facts.transaction_committed` (tri-state) is the STORE's commit; **`audit_committed` is the AUDIT WRITE's own commit** — `True`/`False`/`None` (round 14, finding 3). When a RECOGNIZED typed terminal-sink exception carries its own `.committed`, the wrapper PRESERVES it (round 15, correction A) — but the metadata is an UNTRUSTED seam, read under protection, so an accessor that itself raises yields `None` and NEVER leaks a third exception (round 16, finding 4: v17's bare `getattr` let a hostile `committed` property escape a raw `RuntimeError` after the store committed). `facts.resulting_state` says which of `destination`/`source`/`missing`/`unaccepted`/`unknown` the store is — `False`/`None` do NOT prove it unchanged. The exception validates its OWN context — an absolute NUL-free capped `store_path` and ADJACENT endpoints (`to == from + 1`), and `audit_committed` is exact-`bool`-or-`None`, never `1` (round 14 corr B + round 15 corr B). A terminal-write failure is ALWAYS this exception, never a raw `ValueError` (round 14, finding 5); a non-mapping payload is a controlled schema error, never a raw `TypeError` (round 15, correction C) |
| `current` with no repair | terminal record written (outcome `current`); a terminal-write failure is `committed=False` — nothing changed |
| `current` with a committed rebuildable repair | the repair transaction committed: a terminal-write failure is `committed=True`, resulting version unchanged. The kernel's `OpenResult.transaction_committed` carries this fact (round 8) — the draft demonstrates it; **the production planner must report the same fact if it repairs in a separate transaction** (§5e implementation obligation) |
| every consumed outcome, INCLUDING a named escape | writes its terminal event — a spent authority with no record is indistinguishable from a crash. Round 11, finding 3: a `PackageConsistencyError` raised after consumption escaped the wrapper WITHOUT a terminal event; it is now terminalized as the audit-only outcome `package-inconsistent` and re-raised (§5d). The one escape NOT terminalized is `MigrationAuditWriteError` — it IS the terminal-write failure. Executable in the draft: `DraftAuditStore` implements both tables, atomic activation, and terminal records measured for `migrated`, the no-op `current`, `current`-with-repair, the rolled-back cell and the terminalized named escape |

**The terminal record is the EXACT per-cell contract, validated through ONE
`TerminalFacts` value shared with `MigrationAuditWriteError`** (round 13,
finding 5: v14's exception validated only the null-version rule — a strict
subset of the record's contract — so it accepted a committed `source` and a
`destination` at the wrong version; the two carriers now share
`TerminalFacts.problems()`, so the exception is exactly as strong as the
record it replaces). A terminal payload is `outcome` · `store_changed` ·
`transaction_committed` · `resulting_version` · `resulting_state` ·
`occurred_at`, over the endpoints (`from_version`, `to_version`) the operation
row carries.

**`store_changed` and `transaction_committed` are TRI-STATE** — `True`,
`False`, or `None` (unknown) (round 13, finding 1). **They are one fact
observed twice and must be the SAME tri-state value** (round 14, finding 1:
v15 rejected only a disagreement between two KNOWN values, so it accepted a
partial `None` pair like `(None, True)` and an `(None, None)` cell paired with
a known state). A disk change is exactly a commit, and neither is known without
the other. They are `None` only when genuinely unknown — a rollback ATTEMPTED
and FAILED; a confirmed rollback or a never-entered transaction is a known
`False`.

**The complete permitted `(store_changed, transaction_committed,
resulting_state, resulting_version)` tuple is validated in ONE place** —
`TerminalFacts.problems()`, shared verbatim by the record and the exception
(round 14, finding 1: v15 kept the `migrated → changed+committed` rule OUTSIDE
it, so the exception carrier was still weaker):

```
(True,  True,  destination, to_version)      migrated · current-with-repair · post-commit failure
(False, False, destination, to_version)      current, no repair
(False, False, source,      from_version)    confirmed rollback of an observed source
(False, False, missing,     NULL)            path proven absent
(False, False, unaccepted,  NULL)            store exists, not an accepted source
(False, False, unknown,     NULL)            known unchanged, state unclassified (locked, activation loss)
(None,  None,  unknown,     NULL)            rollback attempted and FAILED — genuinely uncertain
```

`(None, None)` is the ONLY `None` cell, and it requires `resulting_state
unknown`; `(True, True)` requires `destination`. `migrated` is the one outcome
whose effect is fixed — it MUST have changed and committed.

**`resulting_state` is one of `destination`, `source`, `missing`,
`unaccepted`, `unknown`, and it FIXES the version**: `destination` →
`to_version`, `source` → `from_version`, the three null-version states → NULL.
Those three are DISTINCT physical realities (round 12, finding 2): `missing`
(a path PROVEN absent), `unaccepted` (a store EXISTS and opened but is not an
accepted source), `unknown` (never observed, or a rollback not confirmed to
have restored the source).

**Each outcome permits only the states it can PHYSICALLY reach** (round 13,
finding 4: v14 froze effect/state relationships but not the outcome/state
relationship, so it accepted `locked`+source, `invalid-store`+missing,
`unsupported-sqlite`+unaccepted). The states are the union over every site the
outcome can be raised from — an in-hook refusal fires after the source is
observed and rolled back (→ `source`) or with an unconfirmed rollback (→
`unknown`):

```
migrated / current              → destination
migration-source-missing        → missing | unaccepted
migration-failed / -result-mismatch / -evidence-missing / -quiescence-required
                                → source | unknown
internal-error                  → destination | source | unknown
package-inconsistent            → destination | source | unknown   (round 14, finding 5)
foreign-shape / newer / invalid-version   → unaccepted | unknown   (round 15, finding 4)
stamped-shape-mismatch          → source | unaccepted | unknown
never-read outcomes             → unknown   (locked, store-unopenable,
  (the default)                              unsupported-sqlite, invalid-store bytes)
```

**A store that OPENED and was READ but is not an accepted source is
`unaccepted`, not `unknown`** (round 15, finding 4: v16 recorded `unknown` for a
readable existing store rejected as `foreign-shape`/`stamped-shape-mismatch`,
collapsing it with a never-observed store). `unaccepted` is reserved for a store
whose existence and non-acceptance are both PROVEN; `unknown` is a store never
read (a lock, an unopenable path, unreadable bytes).

A `package-inconsistent` escape can be discovered before a transaction
(`unknown`), after a confirmed rollback (`source`), or AFTER a commit
(`destination`) — the terminal record preserves whichever facts are already
proven (round 14, finding 5: v15 permitted only `unknown`, so a post-commit
package escape's `destination` facts were rejected, producing a raw
`ValueError` that lost the named escape and left the operation unterminated).

The unifying invariants: `store_changed` and `transaction_committed` are the
same tri-state value; `(True, True)` leaves the store at the `destination` at
`to_version`; a `migrated` operation must have changed and committed; a
`migration_failed` leaves the `source` ONLY after a CONFIRMED rollback on an
observed store, the `destination` if it committed before a post-commit defect,
and `missing`/`unaccepted`/`unknown` with a NULL version otherwise. Every
`outcome` is a closed member. `event_id` is the `ev-<uuid4>` grammar; the
`state` transitions `attempted → terminal` by
compare-and-set.

Every timestamp — `issued_at`, `expires_at`, `attempted_at`, `occurred_at` —
is the canonical 32-char form (§5b); every digest 64 lowercase hex; the
token fields the frozen grammars.

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
| **M36** the audit store enforces schema, event enum and one-terminal-per-operation | `test_the_audit_store_rejects_two_terminal_events` · `test_the_audit_store_rejects_unknown_events_and_payloads` · `test_the_operation_row_carries_the_full_frozen_schema` — **measured today**; single-mutation atomicity is M40 |
| **M37** terminal audit facts come from the kernel, correct on every branch | `test_the_current_branch_reports_the_actual_resulting_version` · `test_the_current_with_repair_branch_reports_committed_true` · `test_the_migrated_branch_reports_committed_true` — **measured today** |
| **M38** release identity acquisition fails closed | `test_an_unreadable_covered_file_fails_closed` · `test_a_missing_version_declaration_fails_closed` · `test_no_unknown_sentinel_authority_migrates` — **measured today** |
| **M39** every persisted timestamp is canonical and length-capped, INCLUDING the evidence artifact | `test_a_hundred_kilobyte_timestamp_is_refused` · `test_a_noncanonical_but_valid_instant_is_refused` · `test_minted_timestamps_are_canonical` · `test_a_noncanonical_generated_at_poisons_the_artifact` · `test_the_committed_generated_at_is_canonical` — **measured today** |
| **M40** audit state is one immutable value published in one mutation | `test_activation_publishes_one_state_or_none` · `test_terminal_publication_publishes_one_state_or_none` — **measured today**; a failure injected on the publish leaves the previous state intact (round 10: v11's three-attribute store could half-publish) |
| **M41** the operation row carries every frozen field; terminal records are semantically consistent | `test_the_operation_row_carries_every_frozen_field` · `test_the_terminal_validator_rejects_contradictions` — **measured today** |
| **M42** a post-commit internal defect never misreports the version | `test_a_post_commit_internal_defect_never_reports_the_wrong_version` — **measured today**; the kernel builds `OpenResult` before COMMIT |
| **M43** TEMP virtual tables are qualified; the four terminal cells including rolled-back are exercised | `test_temp_virtual_tables_are_probed` · `test_an_authorizer_allowing_temp_vtables_fails_qualification` · `test_the_rolled_back_cell_reports_the_source_version` — **measured today** |
| **M44** the audit state is one immutable value; a failure on the publish leaves the previous state | `test_activation_publishes_one_state_or_none` · `test_terminal_publication_publishes_one_state_or_none` — **measured today** |
| **M45** the terminal validator freezes the exact per-cell contract, including the post-commit failure | `test_the_terminal_validator_rejects_impossible_success_records` · `test_the_terminal_validator_accepts_every_valid_success_cell` · `test_a_post_commit_failure_records_the_destination_version` · `test_the_terminal_validator_permits_a_committed_failure` — **measured today** |
| **M46** only a typed storage outage is retryable; a library defect is `internal-error` | `test_an_internal_activation_defect_is_not_a_storage_outage` · `test_a_typed_storage_outage_is_retryable` — **measured today** |
| **M47** every evidence validator and `--check-evidence` is total over malformed JSON containers | `test_check_evidence_is_total_over_malformed_list_fields` (15 combinations) · `test_the_artifact_validators_are_total_over_non_lists` — **measured today** |
| **M48** the terminal record carries `resulting_state`, and missing/unaccepted/unknown stores are recorded without a fabricated version | `test_terminal_facts_never_fabricate_a_version_for_missing_or_unknown` · `test_a_missing_and_an_unknown_failure_cell_are_legal_terminal_records` · `test_a_missing_or_unknown_state_rejects_a_non_null_version` — **measured today**; `resulting_state` ∈ {destination, source, missing, unaccepted, unknown} fixes the version, and v12's `from_version` fabrication is refused |
| **M49** every committing branch delivers its `OpenResult` to `on_committed` BEFORE the post-commit cleanup | `test_on_committed_delivers_the_committed_result_before_cleanup` (kernel) — **measured today**; a forced `isolation_level`-restore failure cannot erase a proven commit, closing v12's discard-on-cleanup path |
| **M50** a named escape after consumption is terminalized and re-raised | `test_a_package_consistency_error_is_terminalized_and_reraised` — **measured today**; a `PackageConsistencyError` records `package-inconsistent` and re-raises, so no consumed operation lacks a terminal event |
| **M51** the published audit state is deeply read-only and `event_id` is unique | `test_the_published_audit_state_is_deeply_read_only` · `test_a_repeated_event_id_is_rejected` — **measured today**; containers and rows are read-only proxies and a repeated `event_id` is refused as the PK it stands in for |
| **M52** a lost activation response is mapped by its `committed` flag, and every validator is total over NESTED malformed JSON | `test_a_lost_activation_response_is_mapped_by_its_commit_flag` (True/False/None) · `test_every_validator_is_total_over_nested_malformed_json` · `test_check_evidence_is_total_over_nested_malformed_json` (7 nested mutations each) · `test_artifact_problems_is_total_over_an_unhashable_identity_field` (kernel) — **measured today** |
| **M53** the kernel publishes the rollback outcome, and `source` requires a CONFIRMED rollback | `test_on_rolled_back_reports_the_rollback_outcome` (kernel: rolled-back / rollback-failed) · `test_terminal_facts_never_fabricate_a_version_for_missing_or_unknown` — **measured today**; a rollback that itself fails is `unknown`, never `source` (round 12, finding 1) |
| **M54** absent, unaccepted, and unobserved stores get distinct truthful classifications | `test_an_existing_empty_store_is_unaccepted_not_missing` · `test_a_proven_absent_path_is_missing` · `test_terminal_facts_never_fabricate_a_version_for_missing_or_unknown` — **measured today**; `missing` is a path proven absent, `unaccepted` an existing non-source store (round 12, finding 2) |
| **M55** the unknown activation state is structurally distinct and `committed` defaults to unknown | `test_a_lost_activation_response_is_mapped_by_its_commit_flag` (None → `migration-audit-state-unknown`) · `test_the_committed_flag_defaults_to_unknown_and_is_typed` — **measured today** (round 12, finding 3) |
| **M56** `MigrationAuditWriteError` preserves `resulting_state`/`resulting_version` | `test_the_audit_write_error_carries_and_distinguishes_the_state` · `test_a_forced_terminal_write_failure_preserves_the_state` — **measured today**; a missing and an unknown ending are distinguishable, message names the state (round 12, finding 4) |
| **M57** every validator is total under RECURSIVE nested mutation; the operation row validates types and freezes deeply; the `event_id` grammar is enforced | `test_every_validator_is_total_under_recursive_nested_mutation` (>5000 combinations) · `test_the_specific_nested_key_escapes_are_closed` · `test_the_operation_row_validates_field_types` · `test_a_published_row_does_not_alias_caller_mutable_state` · `test_a_malformed_event_id_grammar_is_rejected` — **measured today** (round 12, finding 5 + corrections A, B) |
| **M58** an unconfirmed rollback never fabricates Boolean change/commit facts | `test_an_unconfirmed_rollback_never_fabricates_boolean_facts` · `test_a_tri_state_unknown_terminal_record_is_accepted` — **measured today**; the unknown cell's `store_changed`/`transaction_committed` are `None`, not a fabricated `False` (round 13, finding 1) |
| **M59** a post-commit SQLite cleanup failure is `internal-error`, not `invalid-store`, and keeps the committed facts | `test_a_post_commit_cleanup_failure_is_internal_error_not_invalid_store` — **measured today**; SQLite errors are classified by PHASE, not exception superclass (round 13, finding 2) |
| **M60** only a proven absence (`lstat` ENOENT) is `missing`; an unsearchable path is `store-unopenable` | `test_an_unsearchable_existing_store_is_not_proven_missing` — **measured today**; `os.path.lexists` is not proof of absence (round 13, finding 3) |
| **M61** each terminal outcome permits only the resulting_states it can physically reach | `test_each_outcome_permits_only_its_physical_states` (10 combinations) — **measured today**; `locked`+source, `invalid-store`+missing and the like reject (round 13, finding 4) |
| **M62** the terminal record and `MigrationAuditWriteError` share ONE validated `TerminalFacts`; operation-row paths reject embedded NULs | `test_the_write_error_enforces_the_full_terminal_relationship` · `test_the_record_and_the_exception_share_one_validator` · `test_the_operation_row_rejects_embedded_nul_paths` — **measured today** (round 13, finding 5 + correction A) |
| **M63** `TerminalFacts.problems()` encodes the COMPLETE permitted tuple (both carriers) and is total | `test_terminal_facts_encodes_the_complete_tuple` (13 cells) · `test_the_migrated_rule_lives_inside_terminal_facts` · `test_terminal_facts_problems_is_total` — **measured today**; a partial `None` pair, an `(None,None)` non-unknown cell and a no-change `migrated` all reject, and `outcome=[]`/`state={}` report rather than raise (round 14, finding 1 + correction A) |
| **M64** a committed activation-response loss still writes a terminal event | `test_a_committed_activation_loss_still_writes_a_terminal` — **measured today**; a durably-consumed authority is never left with only an attempted record (round 14, finding 2) |
| **M65** a terminal write's own commit status is representable | `test_a_lost_terminal_response_reports_audit_committed` — **measured today**; `MigrationAuditWriteError.audit_committed` distinguishes durable-but-response-lost from never-written (round 14, finding 3) |
| **M66** SQLite errors are classified by READ SITE, not commit-fact existence | `test_a_runtime_probe_defect_is_internal_error_not_invalid_store` · `test_invalid_store_is_only_the_planner_reading_bad_bytes` — **measured today**; a runtime-gate defect is `internal-error`, only the planner's read is `invalid-store` (round 14, finding 4) |
| **M67** a package-inconsistency terminalizes at every phase and re-raises; the write error validates its context | `test_a_package_inconsistency_terminalizes_at_every_phase` (before/after-rollback/after-commit — the after-rollback case genuinely rolls back) · `test_the_write_error_validates_its_context` — **measured today** (round 14, finding 5 + correction B; round 15, correction D) |
| **M68** only a closed activation-result member proceeds; a malformed result never touches the store | `test_a_malformed_activation_result_never_touches_the_store` (None/string/bool/object) — **measured today** (round 15, finding 1) |
| **M69** a malformed kernel result terminalizes as `internal-error`, never escapes as `AttributeError`; the connection's cleanup begins the instant it opens | `test_a_malformed_kernel_result_is_internal_error_not_attribute_error` · `test_an_isolation_level_setup_failure_closes_the_connection` — **measured today** (round 15, findings 2 & 5) |
| **M70** a migration-hook SQLite error is `migration-failed`, not `invalid-store`; a read-rejected store is `unaccepted`, not `unknown` | `test_a_migration_hook_database_error_is_migration_failed` · `test_a_readable_rejected_store_is_unaccepted_not_unknown` — **measured today** (round 15, findings 3 & 4) |
| **M71** the write error preserves a supplied commit status; endpoints are adjacent and `audit_committed` is exact-bool; a non-mapping payload is controlled | `test_the_write_error_preserves_a_supplied_commit_status` · `test_non_adjacent_endpoints_and_integer_commit_flags_reject` · `test_a_non_mapping_terminal_payload_is_a_controlled_error` — **measured today** (round 15, corrections A, B, C) |
| **M72** MECHANICAL pre-send gates: the whole `TerminalFacts` truth table vs a GENUINELY independent (hand-written, not implementation-read) oracle, and a fault at every audit/planner seam asserting universal invariants INCLUDING record completeness | `tests/test_0013_presend_gates.py` — **measured today**; proven to catch round-14 f1/f4, round-15 f1, and round-16 f1/f2 (round 16, correction B: the oracle no longer shares the implementation map, and the sweep asserts a success outcome leaves a row and exactly one terminal event) |
| **M73** activation returns a typed `ActivationReceipt` verified against the durable row; a lying or spoofing result never touches the store | `test_an_activation_receipt_without_a_published_row_is_rejected` · `test_an_equality_spoofing_activation_result_is_rejected` — **measured today** (round 16, finding 1) |
| **M74** terminal publication returns a verified `TerminalReceipt`; a silent no-op raises, never reports success | `test_a_silent_terminal_noop_raises_never_reports_success` — **measured today** (round 16, finding 2) |
| **M75** the kernel result is validated COMPLETELY and mode-aware | `test_a_semantically_contradictory_kernel_result_is_internal_error` (5 cells) — **measured today**; `migrated`/¬changed, `created`/`adopted` in migrate mode, `migrated`/wrong-version reject (round 16, finding 3) |
| **M76** hostile terminal-sink metadata never leaks a third exception; a check-to-open race is a vanished source | `test_a_hostile_committed_accessor_never_escapes` · `test_a_source_deleted_between_check_and_open_is_missing` — **measured today** (round 16, findings 4 & 5) |
| **M77** the `event_id`/`operation_id` grammar enforces UUID-4 bits; `MigrationRefused` raises under `python -O` | `test_the_event_id_grammar_enforces_uuid4_bits` · `test_migration_refused_raises_under_dash_o` — **measured today** (round 16, corrections C & D) |
| **M78** the activation receipt is BOUND to the exact authority row; a false duplicate leaves the authority usable | `test_activation_binds_the_exact_authority_row` · `test_a_false_duplicate_receipt_leaves_the_authority_usable` — **measured today** (round 17, finding 1 + correction A) |
| **M79** the terminal receipt is BOUND to the requested payload; the returned branch must equal the committed branch | `test_the_terminal_receipt_binds_the_requested_payload` · `test_the_returned_branch_must_equal_the_committed_branch` — **measured today** (round 17, findings 2 & 3) |
| **M80** a malformed `on_committed` never asserts no-change and never erases a proven commit; a terminal-derivation defect never escapes raw | `test_a_malformed_on_committed_publication_never_asserts_no_change` · `test_a_terminal_derivation_defect_never_escapes_raw` — **measured today** (round 17, findings 4 & 5) |
| **M81** both receipts have TOTAL scalar `problems()` validators; the pre-send gates assert request-to-record CONTENT binding | `test_receipt_problems_validate_every_scalar` · `tests/test_0013_presend_gates.py` (the oracle is hand-written; the sweep asserts the row binds the authority store and the terminal event carries the requested outcome) — **measured today** (round 17, corrections B & C) |
| **M82** activation binds the COMPLETE attempted event, not just the row; a duplicate binds the authority and its `terminal_present` agrees with durable state | `test_activation_binds_the_complete_attempted_event` · `test_a_duplicate_row_must_bind_the_authority` — **measured today** (round 18, finding 1 + correction B) |
| **M83** the terminal write verifies the full `attempted → terminal` transition — operation `terminal`, one terminal event, a unique non-reused `event_id` — not only the payload | `test_terminal_write_requires_the_state_transition` · `test_terminal_write_rejects_a_reused_event_id` — **measured today** (round 18, finding 2) |
| **M84** a false `current`/(F,F) never suppresses a real `migrated`/(T,T); the durable record retains the strongest proven state | `test_a_false_uncommitted_publication_never_suppresses_a_real_commit` — **measured today** (round 18, finding 3) |
| **M85** the whole post-consumption sequence is total (hostile receipt equality, a non-bool audit flag) and a derivation fallback changes the PUBLIC outcome; a `recorded` receipt must be `audit_committed=True` | `test_a_hostile_receipt_equality_never_escapes` · `test_an_uncommittable_audit_flag_never_leaks_a_type_error` · `test_a_derivation_fallback_agrees_public_and_durable_outcome` · `test_a_recorded_receipt_must_be_audit_committed` — **measured today** (round 18, findings 4 & 5 + correction A) |
| **M86** `MigrationAuditWriteError.audit_committed` follows the STRONGEST durable evidence — an observed complete transition proves `True`, never a contradictory `False` receipt; a validated no-op-`current` destination position survives a later internal defect | `test_the_write_error_audit_committed_follows_durable_proof` · `test_a_noop_current_position_survives_a_post_callback_defect` — **measured today** (round 19, findings 1 & 2) |
| **M87** terminalisation verifies the operation row and attempted event were PRESERVED (only the state changed `attempted → terminal`), not just the terminal delta | `test_terminalization_requires_the_prior_records_preserved` (delete-attempted, mutate-row) — **measured today** (round 19, correction A) |
| **M88** a malformed duplicate lifecycle is audit-integrity `internal-error`, not a replay; activation readback checks the reference `event_ids` index and exact row field set | `test_a_malformed_duplicate_lifecycle_is_audit_integrity` · `test_activation_readback_requires_the_event_id_in_the_index` — **measured today** (round 19, corrections B & C) |
| **M89** receipt validators are TOTAL over hostile `str` subclasses (`type(x) is str` before comparison) | `test_receipt_validators_are_total_over_str_subclasses` — **measured today** (round 19, correction D) |
| **M90** strongest-durable-evidence governs CONSUMPTION: a complete durable activation is consumed despite a lying carrier — an invalid `activated` receipt or a contradictory `committed=False` exception is `internal-error` WITH a terminal event, never left attempted-only, never advertised as a safe retry | `test_a_durable_activation_is_consumed_despite_a_lying_carrier` (invalid-receipt, committed-false) — **measured today** (round 20, finding 1) |
| **M91** a terminal-sink EXCEPTION cannot override a durably-observed commit — `MigrationAuditWriteError.audit_committed` follows the transition on the raise path too | `test_a_terminal_sink_exception_cannot_override_durable_commit` — **measured today** (round 20, finding 2) |
| **M92** the terminal-derivation fallback preserves EVERY established physical state (proven no-op destination, proven-missing source), not only a committed destination | `test_terminal_fallback_preserves_every_established_state` (noop-destination, missing-source) — **measured today** (round 20, finding 3) |
| **M93** the shared `TerminalFacts.problems()` is TOTAL over hostile `str` subclasses (`type(x) is str` before hashing) | `test_terminal_facts_problems_total_over_hostile_str_subclass` — **measured today** (round 20, correction A) |
| **M94** a `duplicate` activation receipt must be `audit_committed=True` (the row exists durably) | `test_a_duplicate_receipt_must_be_audit_committed` — **measured today** (round 20, correction B) |
| **M95** durable readback precedes classifying EVERY activation carrier — a wrong-type return or an unrecognized post-publication exception after a durable activation is `internal-error` WITH a terminal event, never left attempted-only | `test_durable_activation_consumed_for_every_carrier_class` (wrong-type-return, unrecognized-exception) — **measured today** (round 21, finding 1) |
| **M96** an adapter-supplied `MigrationAuditWriteError` is an UNTRUSTED carrier — the wrapper re-derives `audit_committed` and owns the identity (operation id, store path), keeping the adapter's exception only as the cause | `test_a_sink_supplied_write_error_is_an_untrusted_carrier` — **measured today** (round 21, finding 2) |
| **M97** a typed `committed=True` with no observable terminal transition is contradictory — `audit_committed` degrades to `None`, never proven `True` | `test_committed_true_without_a_transition_is_not_proven_durable` — **measured today** (round 21, finding 3) |
| **M98** timestamp/token/digest/path validators are TOTAL over hostile `str` subclasses (`type(x) is str` before length/regex/parse) — an invalid authority stays a closed refusal, never a library defect | `test_timestamp_validation_is_total_over_hostile_str_subclasses` — **measured today** (round 21, correction A) |
| **M99** the COMPLETE durable lifecycle is classified before every activation carrier — an already-`terminal` operation + `committed=False` is a consumed replay (`migration-quiescence-required`), never a false `migration-audit-unavailable` | `test_a_completed_lifecycle_is_quiescence_not_retryable` · gate `test_gate_completed_lifecycle_committed_false_is_quiescence` — **measured today** (round 22, finding 1) |
| **M100** `on_committed` FREEZES a wrapper-owned immutable copy and reads the branch from the exact underlying value — a live mutation after publication cannot change the facts, and an `OpenResult` subclass cannot spoof its branch | `test_on_committed_facts_are_frozen_against_mutation` · `test_an_open_result_subclass_cannot_spoof_the_branch` · gate `open_versioned-subclass-spoofs-branch` — **measured today** (round 22, finding 2) |
| **M101** `MigrationAuditWriteError` requires `type(facts) is TerminalFacts` and calls the BASE validator, and `type(operation_id) is str` — a subclass cannot replace the shared truth-table validator | `test_the_write_error_requires_exact_carrier_types` (facts-subclass, operation-id-subclass) — **measured today** (round 22, finding 3) |
| **M102** the TOP-LEVEL authority validator exact-types every token/digest/path/timestamp field before `.strip()`/regex — a hostile `str` subclass stays a closed refusal | `test_authority_validation_is_total_over_hostile_str_subclasses` · gate `test_gate_authority_str_subclass_is_a_closed_refusal` — **measured today** (round 22, correction A) |
| **M103** a successful migrate result REQUIRES its mandatory `on_committed` publication (equal field-for-field) — a kernel returning `migrated` without the callback is `internal-error`, store untouched, never retroactively establishing commit/position | `test_a_success_requires_an_on_committed_publication` · gate `open_versioned-success-without-callback` — **measured today** (round 23, finding 1) |
| **M104** `on_committed` validates the mode-aware SEMANTIC cell (one shared `_cell_problems`, used by the callback and the returned-result check) BEFORE freezing — a `migrated`/(F,F) publication is a defect, not a destination position | `test_on_committed_validates_the_semantic_cell_before_freezing` · gate `open_versioned-impossible-callback-cell` — **measured today** (round 23, finding 2) |
| **M105** the authority carrier must be the EXACT `MigrationAuthority` type before any field access (a subclass can intercept it) — a subclass is a closed refusal, never `internal-error` or a raw escape after commit; the initial terminal fallback is inside the total boundary | `test_a_migration_authority_subclass_is_a_closed_refusal` · `test_a_late_authority_getter_never_strands_a_committed_operation` · gates — **measured today** (round 23, finding 3 + correction A) |

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

## 8a. Acceptance boundary — M-Q4 RULED (round 19)

Round 19 ruled M-Q4 and **froze a finite acceptance boundary**: `0013` reviews
the *abstract migration design and audit protocol*; the *production audit sink*
is reviewed with `0008`. Arbitrary mutation of the in-process reference's private
immutable state can always expose one more defensive readback, so proving every
possible backend correct is **not** a finite acceptance criterion for `0013`.

**`0013` is acceptable when these finite properties are frozen in normative text
and mechanically demonstrated** (they are — see the invariants table and the two
pre-send gates):

1. **Concrete migration correctness** — the reviewed v1→v2 declaration preserves
   source data, reaches the exact v2 constructor manifestation, and stamps only
   after evidence-authorised validation (§5, M1–M12).
2. **Planner and evidence architecture** — one shared planner, one evidence
   snapshot, exact path-record selection, runtime qualification, source/release/
   declaration binding, no migration through ordinary opening (§5b–§5c).
3. **Closed public semantics** — every expected failure maps to the frozen
   outcome vocabulary; the two named exceptions and the `TerminalFacts` truth
   table are internally consistent (§5d, gate 1).
4. **Abstract audit protocol** — activation is one atomic compare-and-set
   creating the operation + attempted event; terminal publication is one atomic
   `attempted → terminal` transition; the duplicate, unavailable, unknown-commit,
   committed-response-loss and terminal-write-failure states are distinguished
   (§5e).
5. **Adapter conformance surface** — typed receipts and typed failures have total
   validators; public outcomes, terminal facts, and known store/audit commit
   facts cannot contradict one another (§5e, M81–M89).
6. **Independent mechanical gates** — the normative outcome/fact table and each
   named adapter return/failure class are covered without importing the
   implementation's own expected-answer tables (`tests/test_0013_presend_gates.py`).

Acceptance does **not** require the wrapper to stay correct after arbitrary direct
replacement of the reference's private immutable state, nor after an adapter
violates the frozen atomicity contract while returning a success receipt. Those
are **backend-conformance tests for `0008`'s adapter.**

**These land with `0008`'s production audit sink as explicit blocking
implementation obligations** (not residual risks silently accepted here):

- real two-table DDL with primary, foreign, uniqueness, enum and field
  constraints;
- one DB transaction for activation and one compare-and-set transaction for
  terminalisation;
- multiprocess operation-ID consumption;
- commit-status handling when the DB commits but the response is lost;
- readback from a transactionally consistent snapshot;
- preservation and immutability of the attempted record during terminalisation;
- restart-safe attempted-only reconciliation and durable lookup by operation id;
- detection of malformed or contradictory existing audit rows;
- **the actual `current`-with-repair `transaction_committed=True` contract** (the
  one item the draft can demonstrate but not freeze — carried since round 8);
- crash injection before commit, after commit, and during response delivery.

The draft `DraftAuditStore` remains an **executable protocol model**, not proof
that any future database adapter implements the protocol.

---

## 9. Brief for the external reviewer

**Round 24 of this spec. All three round-23 blockers and both corrections are
closed; every probe reproduced first. The M-Q4 boundary (§8a) held.** The theme
was the **`on_committed` protocol contract** and the **exact authority carrier
type**. Concrete migration, evidence-selection key, release identity, source
binding, one-snapshot reader, TEMP confinement and ordinary planner states are
untouched; the evidence artifact reproduces byte-for-byte.

1. **A successful migrate result requires its mandatory `on_committed`
   publication** (finding 1): the callback is the protocol proof a branch
   resolved, and v25 compared against it only when it existed. A fake kernel that
   returned a valid `migrated` WITHOUT publishing the callback (and without
   touching the store) was accepted. Now every successful migrate result requires
   exactly one valid publication equal to it field-for-field; its absence is
   `internal-error` from independently-established facts, and the returned result
   does not retroactively establish commit or position.
2. **`on_committed` validates the mode-aware semantic cell BEFORE freezing**
   (finding 2): `_frozen_from_open_result` exact-typed and copied but validated
   only structure, so a `migrated`/(F,F) publication established a destination
   position for a store still at v1 (the returned-result validator would reject
   it, but the kernel raised before returning). One shared `_cell_problems` now
   validates the migrate-mode cell (`migrated`→T/T, `current`→(F,F)|(T,T),
   `created`/`adopted` forbidden) at BOTH the callback and the returned result, so
   a value can never be accepted at one and rejected at the other.
3. **The authority carrier must be the EXACT `MigrationAuthority` type** (finding
   3 + correction A): `authority_static_problems` used `isinstance`, so a
   `MigrationAuthority` subclass could intercept attribute access — pass
   validation, then raise from a field getter AFTER the real commit, escaping the
   initial `_fallback_terminal_facts` call (which was outside the terminal `try`)
   and stranding the operation attempted-only; a simpler subclass was
   misclassified `internal-error`. It now requires `type(a) is MigrationAuthority`
   before any field access (a subclass is a closed `migration-quiescence-required`
   refusal), and the initial fallback is moved inside the total post-consumption
   boundary so the structure reflects the normative totality claim.

**Correction B**: the independent gate covers the three new cases
(success-without-callback, impossible-callback-cell, authority subclass).

**On the boundary.** Every finding was *inside* the six §8a properties — the
protocol contract that the callback establishes facts, and the exact carrier type
— and I treated each as a `0013` blocker. None required defending the reference's
private state against arbitrary corruption; that remains a `0008` obligation.

**Where I am least confident:** unchanged — the `current`-with-repair
`committed=True` cell (§8a `0008` obligation, carried since round 8): the draft
demonstrates the kernel's `transaction_committed` contract but cannot freeze it
for a production planner that repairs in a separate transaction.

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~M-Q1~~ | **RULED by round 9, 2026-08-03: wait.** `0013` must not reach `accepted` before it is reviewed **against an actual migration** — that is the principle that justified the `0007` scope cut, and it applies equally to the replacement. **The first case is `0008`'s `confirmations` table**: accepted, simple, additive, already blocked on `0013`, and independent of `0006`'s unresolved source-identity design. **`0013` may generalise only what that real migration demonstrates.** | resolved | external | — |
| ~~M-Q2~~ | **RULED (round 1) adopt-with-conditions; condition RESOLVED (round 2) by the offline boundary; boundary APPROVED (round 3) at the library level** with the narrowed claim (§5b: ordinary opening cannot initiate migration; the trusted deployment authority owns quiescence, fencing and backup validity) and the authority binding conditions (exact types, bound to store/migration/operation; release-identity binding at implementation). | resolved | external | — |
| ~~M-Q3~~ | **RULED by round 9: yes, it belongs here.** The capability comparison exists to decide whether a *migration result* satisfies its destination despite differing DDL, so it is `0013`'s. `0007` retains exact manifestation identity, digest comparison, rebuildable drift and candidate resolution — and `capability_problems()` has been removed from its kernel. | resolved | external | — |
| ~~M-Q4~~ | **RULED by round 19: the acceptance boundary is frozen (§8a).** `0013` reviews the abstract migration design and audit *protocol* against six finite, mechanically-gated properties (concrete migration correctness; planner/evidence architecture; closed public semantics; abstract atomic audit protocol; adapter conformance surface; independent gates). It does **not** require the in-process reference to defend against arbitrary direct corruption of its private immutable state, nor an adapter that violates atomicity while returning a success receipt — those are **`0008` adapter-conformance tests**. Ten production obligations (real DDL/constraints, one activation + one compare-and-set transaction, multiprocess consumption, response-loss handling, consistent-snapshot readback, attempted-record immutability, restart-safe reconciliation, malformed-row detection, the `current`-with-repair `committed=True` contract, crash injection) become explicit blocking `0008` gates. The draft is an executable protocol model, not proof that a backend implements the protocol. | resolved | external | — |

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

---

## 19. Round 9 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, one-snapshot evidence handling,
release-identity direction and ordinary planner states remain approved; v11
deferred on five load-bearing gaps plus the rolled-back cell and stale
wording.** The resolution/refusal split remains approved. All taken;
migration, path-evidence key, release framing, one-snapshot reader and
ordinary planner states untouched.

| # | finding | closed by |
|---|---|---|
| 1 | audit activation was two independent writes, not one rollback-capable transaction — a failure between them left the operation consumed with no attempted record | **atomic swap** of the whole `_ops`/`_events` state (production: one DB transaction); forced-failure regressions for activation and terminal publication prove nothing persists |
| 2 | the operation row omitted `backup_ref`/`issued_at`/`expires_at`/output digest, and terminal records accepted contradictory outcomes | **complete operation-row schema** plus **semantic terminal validation** — closed-vocabulary outcome consistent with the event, version ∈ {source, destination}, `store_changed`⇒commit, `migrated`⇒destination |
| 3 | an internal defect after commit recorded `committed=False` and v1 for a v2 store | **kernel builds `OpenResult` before `COMMIT`**, so a raise rolls back and every fact is truthful; regression injects a post-result-build failure and checks the store stays v1 |
| 4 | the fifteen-probe vocabulary allowed TEMP virtual tables to execute before the leak assertion | **sixteenth `SQLITE_CREATE_VTABLE` probe** (fires before module resolution → `SQLITE_AUTH` on any runtime); vtable-allowing falsifier fails qualification |
| 5 | the evidence `generated_at` — inside the `evidence_digest` — was uncapped and noncanonical | **canonical `generated_at`** at generation and validation, the same 32-char contract as every persisted timestamp |
| gap | the rolled-back terminal cell was unexercised | regression: a migration failing after a statement, forced terminal-write failure → `committed=False`, source version, store rolled back, authority consumed |
| a | §5c said "twelve probes"; timestamps described as generic ISO 8601 | corrected to the sixteen-probe vocabulary and the one canonical timestamp contract |

---

## 20. Round 10 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release framing, one-snapshot reader,
source binding, TEMP virtual-table qualification and canonical evidence
timestamp remain approved; v12 deferred on five load-bearing gaps in the
audit reference.** The resolution/refusal split remains approved. All taken;
concrete migration, evidence-selection key, release identity, source
binding, one-snapshot reader and ordinary planner states untouched.

| # | finding | closed by |
|---|---|---|
| 1 | the "atomic swap" was three attribute assignments — a failure on the second half-published the state (operation consumed, no attempted event) | **one immutable `AuditState` behind one attribute**, published in a single assignment; injection on the publish leaves the previous state; regressions for activation and terminal publication |
| 2 | the terminal validator accepted impossible success records (`current`/v1, `migrated`/no-change) | **the exact per-cell contract** — `store_changed == transaction_committed`, completed leaves the destination, each of the five valid cells frozen |
| 3 | a post-commit internal defect could not be recorded — `migration_failed` was forced to the source version | **a failure that committed leaves the destination**; a post-commit `internal-error` records `committed=True`, version = destination |
| 4 | every activation exception was mapped to the retryable `migration-audit-unavailable` | **only the typed `AuditStorageUnavailable`** is retryable; a library defect propagates to `internal-error`, nothing consumed |
| 5 | `check_evidence` raised a raw `TypeError` on `runtimes: false` and other malformed containers | **`_artifact_list` + total `active_records`**; `check_evidence` wraps each validator — clean nonzero, never a traceback; 15 field×value regressions |
| a | the schema guard was an `assert` (vanishes under `-O`) | replaced with a raise; regression runs under `python -O` |
| b | `event_id` grammar unspecified | frozen `ev-<uuid4>` |
| c | authority timestamp comments said generic ISO 8601 | corrected to the canonical 32-char form |
| d | M36/M40 overclaimed atomicity | reworded to the single-mutation design; M44 carries the atomicity evidence |

---

## 21. Round 11 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release framing, one-snapshot reader, source
binding, TEMP virtual-table qualification and canonical evidence timestamp
remain approved; v13 deferred on five load-bearing gaps in the audit
reference plus two corrections.** The resolution/refusal split remains
approved. All taken; concrete migration, evidence-selection key, release
identity, source binding, one-snapshot reader and ordinary planner states
untouched; the evidence artifact reproduces byte-for-byte (no probe
vocabulary changed).

| # | finding | closed by |
|---|---|---|
| 1 | the terminal record fabricated `resulting_version = from_version` for every non-kernel ending, so a missing or unobserved store was recorded at the source version | **`resulting_state` ∈ {destination, source, missing, unknown}** fixes the version (destination→to, source→from, missing/unknown→NULL); the validator refuses a null-version state carrying a version and a versioned state carrying the wrong one (M48) |
| 2 | the function-level `finally` restoring `isolation_level` runs on the return path and can raise, discarding the committed `OpenResult` — the caller's audit then reported v1 for a v2 store | **every committing kernel branch delivers the `OpenResult` to an infallible `on_committed` sink BEFORE the cleanup**; a forced restore-failure still delivers committed facts (kernel regression, M49) |
| 3 | a `PackageConsistencyError` raised after consumption escaped the wrapper with no terminal event | **terminalized as the audit-only outcome `package-inconsistent` and re-raised**; `MigrationAuditWriteError` remains the one non-terminalized escape (M50) |
| 4 | `AuditState` held LIVE dicts exposed through `_ops`, so a held reference could flip an operation to `terminal` and drop its attempted event outside the single publish | **read-only proxies over read-only rows**; the single publish is the only mutation path (M51) |
| 5 | validators were total over a malformed top-level container but NOT over nested malformed JSON — `schema_version={}` put a dict in a dedup key (kernel `TypeError`), a null version-record `.get`-crashed the path resolver, `accepted: false` was iterated as a bool | **a keyability guard in the kernel** (round-4 rule) and **nested-container guards in the path resolver and expected-set builder**; seven nested mutations × four validators return problem lists, `--check-evidence` a clean nonzero each (M52) |
| A | every lost `AuditStorageUnavailable` response was mapped to "not consumed", so a response lost after a durable activation invited a retry that then saw `duplicate` | **the `committed` flag decides**: proven-written → `migration-quiescence-required`; not-proven/unknown → the retryable `migration-audit-unavailable` (M52) |
| B | events were keyed by `(operation_id, event)` with `event_id` never checked, so a repeated generator produced two events with one id | **`AuditState.event_ids` enforces the `event_id` PRIMARY KEY**; a collision is refused (M51) |

---

## 22. Round 12 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP confinement qualification, named-escape direction and canonical
evidence timestamp remain approved; v14 deferred on five load-bearing gaps plus
three corrections.** The resolution/refusal split and the bounded
adjacent-migration claim remain approved. All taken; concrete migration,
evidence-selection key, release identity, source binding, one-snapshot reader
and ordinary planner states untouched; the evidence artifact reproduces
byte-for-byte.

| # | finding | closed by |
|---|---|---|
| 1 | the kernel discarded the `ROLLBACK` result, so the wrapper recorded a confirmed `source` for a store a failed rollback left partially migrated | **the kernel PUBLISHES the rollback outcome** through an infallible `on_rolled_back` sink (`rolled-back`/`rollback-failed`); `source` requires a CONFIRMED rollback, an unconfirmed one is `unknown` (M53) |
| 2 | `resulting_state=missing` conflated a vanished file with an existing, valid, empty database | **`missing` reserved for a path PROVEN absent**; an existing non-source store is `unaccepted` — distinct null-version states for distinct physical realities (M54) |
| 3 | `committed=None` was collapsed into the retryable `migration-audit-unavailable`, and `committed` defaulted to a fabricated `False` | **new closed outcome `migration-audit-state-unknown`** for the unknown case (query the durable operation first); `committed` defaults to `None` and is typed `bool | None` (M55) |
| 4 | `MigrationAuditWriteError` dropped the new `resulting_state`, so a missing and an unknown ending were indistinguishable `vNone` errors | **the exception carries `resulting_state`/`resulting_version`**, validated against the terminal schema's relationship; the message names the state (M56) |
| 5 | validators were total over seven KNOWN nested locations, not recursively — `runtime.source_id={}` and an accepted-manifest `digest={}` still put a dict in a key | **key construction guarded by the CONSTRUCTED KEY's hashability** — total over any malformed component at any depth; a recursive walk of every node × wrong-typed values raises nothing (M57) |
| A | `_operation_row` validated only the field-NAME set (`backup_ref=[]` accepted) and `_readonly` aliased caller-held lists | **every field validated to type and grammar** at the store boundary, and the published copy is frozen DEEPLY (M57) |
| B | the `event_id` grammar was declared but only uniqueness was checked | **`ev-<uuid4>` grammar enforced before publication**, alongside uniqueness (M57) |
| C | the spec embedded a `170 tests` count that went stale (the archive ran 193) | the count is no longer embedded — it is whatever pytest collects that round |

---

## 23. Round 13 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP confinement qualification, named-escape direction and canonical
evidence timestamp remain approved; v15 deferred on five load-bearing gaps plus
three corrections.** The resolution/refusal split and the bounded
adjacent-migration claim remain approved. All taken; concrete migration,
evidence-selection key, release identity, source binding, one-snapshot reader
and ordinary planner states untouched; the evidence artifact reproduces
byte-for-byte.

| # | finding | closed by |
|---|---|---|
| 1 | the unknown cell still asserted `store_changed=False`/`transaction_committed=False` even when a failed rollback may have committed partial changes | **tri-state facts**: `store_changed`/`transaction_committed` are `True`/`False`/`None`; a rollback attempted-and-failed leaves both `None`, a confirmed rollback or never-entered transaction a known `False` (M58) |
| 2 | a post-commit `conn.close()` `DatabaseError` was mislabelled `invalid-store`, telling the host to remediate a valid v2 database | **classify by PHASE**: a cleanup-phase or post-committed-facts `DatabaseError` is `internal-error` carrying the committed facts; `invalid-store` is only for bytes failing WHILE read (M59) |
| 3 | `os.path.lexists` (False on `EACCES`) was treated as proof a path was absent | **`os.lstat`**: only an explicit `FileNotFoundError` is `missing`; an unsearchable path is `store-unopenable` (M60) |
| 4 | the terminal validator accepted outcome/state pairs the outcome cannot produce (`locked`+source, `invalid-store`+missing, …) | **a per-outcome allowed-state map**, the union over every raise site; records outside it reject (M61) |
| 5 | `MigrationAuditWriteError` enforced only the null-version rule — a subset of the record's contract | **one validated `TerminalFacts`** shared by the record and the exception, carrying outcome/endpoints/tri-state facts/state/version; the exception's contract is now identical to the record's (M62) |
| A | the operation-row store path accepted embedded NULs | rejected, along with explicit filesystem-encoding failures (M62) |
| B | M48, the §5d table and the lifecycle rows omitted newly-frozen states | reconciled — `unaccepted`, `migration-audit-state-unknown` and `resulting_state` now appear where they belong |
| C | "confirmed rollback re-established the source" overclaimed | narrowed to "`ROLLBACK` returned successfully"; the draft does not re-hash the source manifestation |

---

## 24. Round 14 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP confinement qualification and canonical timestamp contract remain
approved; v16 deferred on five load-bearing gaps plus three corrections.** The
resolution/refusal split and the bounded adjacent-migration claim remain
approved. All taken; concrete migration, evidence-selection key, release
identity, source binding, one-snapshot reader and ordinary planner states
untouched; the evidence artifact reproduces byte-for-byte.

| # | finding | closed by |
|---|---|---|
| 1 | `TerminalFacts` was weaker than the record — it accepted partial `None` pairs, `(None,None)` non-unknown cells, and a no-change `migrated` (that rule lived only in the record validator) | **the COMPLETE tuple validated in `TerminalFacts.problems()`**: change and commit are the same tri-state value; `(None,None)`→unknown, `(True,True)`→destination; `migrated`→changed+committed — shared verbatim by both carriers (M63) |
| 2 | a `committed=True` activation-response loss left a durably-consumed operation with only an attempted event | **`_consume_authority` marks the operation consumed the instant consumption is PROVEN**, so the wrapper writes its terminal event (M64) |
| 3 | a terminal write that committed then lost its response was indistinguishable from one that never landed | **`MigrationAuditWriteError.audit_committed`** (`True`/`False`/`None`) carries the AUDIT write's own commit status, distinct from the store's (M65) |
| 4 | SQLite errors were classified by "commit facts exist", so a runtime-gate `DatabaseError` before any read became `invalid-store` | **classified by READ SITE**: only a `DatabaseError` inside `open_versioned`'s read is `invalid-store`; everything else is `internal-error` (M66) |
| 5 | a post-commit `package-inconsistent` carried `destination` facts the permits-only-unknown map rejected, escaping as a raw `ValueError` and losing the named escape | **`package-inconsistent` permits `destination`/`source`/`unknown`**; it terminalizes with the proven facts at any phase and re-raises the original escape; a terminal-write failure is always `MigrationAuditWriteError` (M67) |
| A | `TerminalFacts.problems()` raised `TypeError` on `outcome=[]`/`resulting_state={}` | type-checked before set membership — total (M63) |
| B | the write-error carrier accepted a relative/NUL/oversized path and reversed endpoints | validates its own context: absolute NUL-free capped path, adjacent ordered endpoints (M67) |
| C | the permission-denial regression failed under root (which traverses `chmod 0`) | skipped when effective UID is zero |

---

## 25. Round 15 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP-confinement qualification and canonical timestamp contract remain
approved; v17 deferred on five load-bearing gaps plus four corrections.** The
resolution/refusal split and the bounded adjacent-migration claim remain
approved. All taken; concrete migration and approved elements untouched; the
evidence artifact reproduces byte-for-byte.

| # | finding | closed by |
|---|---|---|
| 1 | an invalid audit-activation return value (`None`, wrong type, unknown string) was treated as success, permitting a migration with no operation row or attempted event | **only `activated` proceeds**; any other value is `internal-error` BEFORE the store is opened (M68) |
| 2 | a malformed kernel result escaped the terminal wrapper as `AttributeError`, stranding a consumed operation | **the kernel result is validated**; a malformed return terminalizes as `internal-error`, and terminal derivation is inside the outermost boundary (M69) |
| 3 | a `sqlite3.DatabaseError` from migration-hook code was mislabelled `invalid-store` | **converted at the hook to `migration-failed`**; only the kernel's own read is `invalid-store` (M70) |
| 4 | a readable existing store rejected as foreign/malformed was audited `unknown`, not `unaccepted` | **`unaccepted`** for a store that opened and was read but is not an accepted source; outcome-state map updated (M70) |
| 5 | an `isolation_level` setup failure leaked the opened connection | **the cleanup scope begins the instant the connection opens** — closed exactly once (M69) |
| A | the write error inferred audit-commit status from local state, ignoring the sink exception's own `.committed` | **preserves a supplied `.committed`**; only a carrier-less exception is inferred (M71) |
| B | non-adjacent endpoints and an integer `audit_committed` were accepted | **adjacency (`to == from + 1`)** at the row, `TerminalFacts` and the write error; `audit_committed` is exact-`bool`-or-`None` (M71) |
| C | `record_terminal(op, event, None)` raised a raw `TypeError` | a non-mapping payload is a controlled schema error (M71) |
| D | the `after-rollback` package regression actually ran to commit | rewritten to inject inside the hook so the kernel genuinely rolls back (M67) |

---

## 26. Round 16 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP-confinement qualification and canonical timestamp contract remain
approved; v18 deferred on five load-bearing gaps plus four corrections.** The
resolution/refusal split and the bounded adjacent-migration claim remain
approved. All taken; concrete migration and approved elements untouched; the
evidence artifact reproduces byte-for-byte.

| # | finding | closed by |
|---|---|---|
| 1 | an activation success TOKEN was not proof — an `__eq__` spoof and a no-op returning the token both migrated with no operation row | **a typed `ActivationReceipt`** required by exact type + identity, AND the durable row/attempted event verified before proceeding (M73) |
| 2 | terminal publication had no success receipt, so a no-op sink reported `migrated` with no terminal event | **a typed `TerminalReceipt`** required and the landed event verified; a silent no-op raises `MigrationAuditWriteError` (M74) |
| 3 | the kernel-result validator checked SHAPE, not semantics — `migrated`/¬changed, `created`/`adopted` in migrate mode, `migrated`/v999 passed | **one mode-aware `OpenResult` contract**, compared with `on_committed`; a contradiction is `internal-error`, never an audit-store call reported as an outage (M75) |
| 4 | inspecting a sink exception's `committed` could leak a third raw exception | **guarded metadata read for a recognized type only** → `None` on any failure; the documented exception always escapes (M76) |
| 5 | the source could vanish between the pre-open `lstat` and the mode=rw open, misclassified `store-unopenable`/`unknown` | **a FRESH post-failure presence check** — a confirmed ENOENT is `migration-source-missing`/`missing` (M76) |
| A | attempted-only duplicate reconciliation was unspecified | the receipt's `terminal_present` distinguishes an already-complete operation from an attempted-only one to reconcile via the durable id (M73) |
| B | the "independent" gate oracle read the implementation map, and the seam sweep did not assert record completeness | the oracle is hand-written (a wrong map disagrees); the sweep asserts a success outcome leaves a row and exactly one terminal event — now catches f1/f2 (M72) |
| C | the UUID4 grammar accepted non-v4 values | version-4 and RFC-variant bits enforced on `event_id` and `operation_id` (M77) |
| D | `MigrationRefused` relied on an `assert` that vanishes under `-O` | replaced with an explicit raise (M77) |

---

## 27. Round 17 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP-confinement qualification and canonical timestamp contract remain
approved; v19 deferred on five load-bearing gaps plus three corrections.** The
resolution/refusal split and the bounded adjacent-migration claim remain
approved. All taken; concrete migration and approved elements untouched; the
evidence artifact reproduces byte-for-byte. The unifying theme — verify CONTENT,
not existence — is adopted throughout.

| # | finding | closed by |
|---|---|---|
| 1 | the activation receipt proved only that some row existed under the id — a sink could bind a DIFFERENT store | **the durable row is verified to BIND the exact authority** field-for-field before store access (M78) |
| 2 | the terminal receipt proved only that some event existed under the key — a different valid payload passed | **the durable event is verified to EQUAL the requested payload** field-for-field (M79) |
| 3 | the returned `OpenResult` could change the committed branch (`migrated`→`current`) when the fact tuple was equal | **the branch LABEL is part of the `on_committed` agreement** (M79) |
| 4 | a malformed `on_committed` value erased a proven commit and was still treated as non-null commit evidence | **the sink validates and freezes**; a defect leaves the commit state UNKNOWN, never a fabricated `False`, and never erases a valid receipt (M80) |
| 5 | terminal-fact derivation was outside the total boundary — a defect stranded a committed operation with a raw exception | **derivation/validation/publication after consumption is a total boundary** — `internal-error` from frozen facts or `MigrationAuditWriteError`, nothing else (M80) |
| A | a false `duplicate` receipt was trusted without durable proof, leaving the authority usable | duplicates are verified against the durable row; `terminal_present` is derived from durable state (M78) |
| B | receipt scalar fields were not fully validated and could leak a raw `TypeError` | both receipts have total `problems()` validators with exact typing and cross-field consistency (M81) |
| C | the mechanical gates asserted counts/local validity, not request-to-record binding | the seam sweep asserts the row binds the authority store and the terminal event carries the requested outcome; two content-mismatch seams added (M81) |

---

## 28. Round 18 review disposition

**Verdict: architecture standing — the concrete v1→v2 migration, shared
planner, evidence-selection key, release identity, source binding, one-snapshot
reader, TEMP-confinement qualification and canonical timestamp contract remain
approved; v20 deferred on five load-bearing gaps plus four corrections.** The
resolution/refusal split and the bounded adjacent-migration claim remain
approved. All taken; concrete migration and approved elements untouched; the
evidence artifact reproduces byte-for-byte. The unifying theme — verify the
COMPLETE record, both atomic parts and the whole resulting state — is adopted
throughout.

| # | finding | closed by |
|---|---|---|
| 1 | activation bound the operation ROW but verified the attempted EVENT only by key existence — a malformed attempted event under the right key let the operation proceed | **both atomic records are verified** — the attempted event's exact field set, unique `event_id`, binding and `occurred_at == row.attempted_at` (M82) |
| 2 | the terminal write verified the payload but not the `attempted → terminal` transition — a valid payload with the operation still `attempted`, or a reused `event_id`, passed | **the full transition is verified** — operation `terminal`, one terminal event, a valid unique non-reused `event_id`, the exact field set (M83) |
| 3 | `on_committed` accepted a `current`/(F,F) that says no commit, so a false one suppressed a real `migrated`/(T,T) and the audit claimed no change | **the sink distinguishes a proven commit (T,T) from a no-commit position**; a conflicting second publication is a defect and the strongest proven state is retained (M84) |
| 4 | timestamp generation, receipt equality and the exception constructor sat outside the total boundary — a hostile `__ne__` or an `audit_committed=1` leaked a raw exception after commit | **the whole post-consumption sequence is total** — exact-typed receipt validators, audit-flag sanitization, guarded construction (M85) |
| 5 | a derivation fallback recorded `internal-error` durably but the public call still returned `migrated` | **the terminal write returns the effective outcome** — public and durable agree for every non-named return (M85) |
| A | a `recorded` terminal receipt could claim `audit_committed=False` | a durably-verified `recorded` receipt must be `audit_committed=True`; `False` is contradictory, `None` is the failure path (M85) |
| B | a duplicate receipt was not bound to the authority, and `terminal_present` was unvalidated | duplicates bind the authority (a different-store row is a collision); `terminal_present` must agree with durable state (M82) |
| C | the content gate verified a subset of the durable state | the gate now asserts the COMPLETE state for a success — all authority-row fields, attempted-event contents, the transition, `event_id` integrity — with seven new content-mismatch seams; reverting any round-18 fix fails a gate (M82–M85) |
| D | the operation-id prose contradicted the enforced UUID4 grammar | the row is reconciled — `op-<uuid4>` with version-4/variant bits; the earlier "shape, not version/variant" wording is withdrawn (M77) |

---

## 29. Round 19 review disposition

**Verdict: M-Q4 RULED — the acceptance boundary is frozen (§8a). `0013` is
acceptable on six finite, mechanically-gated properties of the abstract migration
design and audit protocol; ten production obligations move to `0008` as explicit
blocking gates. Architecture standing; v22 deferred on two load-bearing semantic
gaps plus four reference-scope corrections — all closed.** The reviewer ruled
that arbitrary corruption of the reference's private immutable state is not a
finite acceptance criterion, and that production transactionality, multiprocess
durability, response-loss reconciliation, historical-row integrity and the
`current`-with-repair commit fact are `0008` adapter obligations. The two
semantic gaps were both a *verified fact overridden by a weaker one*. The bounded
adjacent-migration claim and resolution/refusal split remain approved.

| # | finding | closed by |
|---|---|---|
| M-Q4 | where does review of the abstract design end and `0008` implementation review begin? | **RULED — §8a**: six finite acceptance properties are gated in the draft; ten production obligations are explicit `0008` blocking gates; the draft is an executable protocol model, not proof a backend implements it |
| 1 | a rejected terminal receipt could still set `MigrationAuditWriteError.audit_committed=False` after the wrapper's own readback proved the write committed | **the audit fact follows the STRONGEST durable evidence** — an observed complete transition is `True`; `False` arises only from a typed sink that says definitely-not-written with no durable transition; all else `None` (M86) |
| 2 | a valid no-op `current`/(F,F) callback followed by an internal `sqlite3` defect lost its proven destination position and recorded `unknown` | **`position_established` is tracked separately from `write_commit_established`** — a proven destination survives a later defect: `internal-error`/`False`/`False`/`destination`/v2 (M86) |
| A | terminalisation verified the terminal delta but not that the operation row and attempted event were preserved | **the row and attempted event are snapshotted at activation and verified immutable** (only the state changes); the premise is frozen in §5e text and enforced in `0008` (M87) |
| B | a malformed duplicate lifecycle was treated as an ordinary consumed replay | **a malformed/contradictory lifecycle is audit-integrity `internal-error`**, distinct from a valid completed or attempted-only replay (M88) |
| C | activation readback omitted the reference `event_ids` index and exact row field-set checks | **both are checked** in the readback and the pre-send gate; §8a names the production PK/schema constraints as the `0008` equivalent (M88) |
| D | receipt validators used `isinstance(x, str)`, not total over a hostile `str` subclass | **`type(x) is str` before comparison** — a subclass whose equality raises is classified, not executed (M89) |

---

## 30. Round 20 review disposition

**Verdict: M-Q4 boundary respected and applied as ruled; architecture standing;
v23 deferred on three load-bearing semantic gaps plus two corrections — all
closed.** No finding relied on arbitrary private-state corruption or reopened a
`0008` obligation. Every gap was the same class: the STRONGEST durable evidence
was not applied on *every* path, so a weaker carrier could override a verified
fact. The bounded adjacent-migration claim, resolution/refusal split, and finite
M-Q4 acceptance framework remain approved.

| # | finding | closed by |
|---|---|---|
| 1 | a complete durable activation could be treated as unconsumed when the sink returned an invalid receipt or raised `AuditStorageUnavailable(committed=False)` — leaving an attempted-only operation and (in the latter case) falsely advertising a safe retry | **strongest-evidence precedence on activation** — a durable row means consumed regardless of the carrier: `internal-error` WITH a terminal event; only a genuinely absent row trusts the typed flag (M90) |
| 2 | a terminal sink that published the complete transition and then raised a contradictory typed exception still produced `MigrationAuditWriteError.audit_committed=False` | **one `_audit_commit_fact` helper governs BOTH the return and raise paths** — an observed complete transition is `True` (M91) |
| 3 | terminal-derivation fallback discarded established non-commit states, recording `unknown` for a proven current-v2 destination or a proven-missing source | **the fallback reconstructs via the canonical `_store_facts_from_state`** (no divergent copy) and preserves every established physical state; `internal-error` permits the full state set (M92) |
| A | the shared `TerminalFacts.problems()` was non-total over a hostile `str` subclass (`__hash__` raises) | **`type(x) is str` before hashing/membership** (M93) |
| B | a `duplicate` activation receipt could claim `audit_committed=False`, contradicting the durable row | **a `duplicate` must be `audit_committed=True`** — `False` rejects as `internal-error` (M94) |

---

## 31. Round 21 review disposition

**Verdict: M-Q4 boundary respected and applied as ruled; architecture standing;
v24 deferred on three load-bearing semantic gaps plus two corrections — all
closed.** No finding relied on private-state corruption or reopened a `0008`
obligation. Each gap was the round-20 principle not yet applied to *every*
carrier: strongest durable evidence, and validator totality, held for the
recognized carriers but not the unrecognized ones. The bounded adjacent-migration
claim, resolution/refusal split, and finite M-Q4 acceptance framework remain
approved.

| # | finding | closed by |
|---|---|---|
| 1 | a complete durable activation was left attempted-only when the adapter returned a non-receipt or raised an unrecognized post-publication exception (consumption was established only inside selected carrier branches) | **durable readback precedes classifying EVERY carrier** — a `duplicate` alone means "someone else consumed it"; every other carrier over a durable row is `internal-error` WITH a terminal event (M95) |
| 2 | an adapter-supplied `MigrationAuditWriteError` was re-raised unchanged, letting it override durable proof and substitute a foreign operation id / store path | **it is an untrusted carrier** — the wrapper re-derives `audit_committed`, owns the identity, and keeps the adapter's exception only as the cause (M96) |
| 3 | a typed terminal `committed=True` with no observable transition was reported as proven audit durability | **`_audit_commit_fact` implements its exact three-way precedence** — `committed=True` with no transition degrades to `None` (M97) |
| A | timestamp validation was non-total over a hostile `str` subclass (`__len__` raises), misclassifying an invalid authority as `internal-error` | **`type(x) is str` before length/regex/parse** across the timestamp/token/digest/path validators; an invalid authority stays a closed refusal (M98) |
| B | the pre-send seam gate omitted the new carrier combinations | **added** — wrong-type return, unrecognized exception, sink-supplied write error, `committed=True`-no-transition (M95–M97) |

---

## 32. Round 22 review disposition

**Verdict: M-Q4 boundary respected and applied as ruled; architecture standing;
v25 deferred on three load-bearing semantic gaps plus two corrections — all
closed.** No finding relied on private-state corruption or reopened a `0008`
obligation. Each gap was a value or carrier trusted by SHAPE (`isinstance`, an
overridable `str()`/`problems()`, a live mutable object, a partial lifecycle
predicate) rather than by EXACT identity. The bounded adjacent-migration claim,
resolution/refusal split, and finite M-Q4 acceptance framework remain approved.

| # | finding | closed by |
|---|---|---|
| 1 | a completed (`terminal`) operation + `AuditStorageUnavailable(committed=False)` was falsely reported `migration-audit-unavailable` (safe retry) because readback recognised only a fresh `attempted` activation | **`_durable_lifecycle` classifies the complete lifecycle before every carrier** — terminal/attempted → consumed replay (`quiescence`); malformed → `internal-error`; only a genuinely absent row → `unavailable` (M99) |
| 2 | `on_committed` stored a live mutable `OpenResult` and read the branch from overridable `str()`, so a post-publication mutation or a branch-spoofing subclass made an untouched v1 store appear committed at v2 | **`_FrozenResult`** — exact `type(r) is OpenResult`, branch from the underlying value, fields copied; returned result exact-typed and compared field-for-field with no identity shortcut (M100) |
| 3 | `MigrationAuditWriteError` accepted a `TerminalFacts` subclass and invoked its overridable `problems()`, admitting impossible caller-decision facts | **`type(facts) is TerminalFacts` + `TerminalFacts.problems(facts)` (base) + `type(operation_id) is str`** (M101) |
| A | the top-level authority validator called `.strip()`/regex before exact-type rejection, so a hostile `str` subclass was `internal-error` | **exact-type every token/digest/path/timestamp field first** — a closed refusal, never a library defect (M102) |
| B | the independent gate omitted the five new cases | **added** — completed-lifecycle retry, on_committed mutation, OpenResult-subclass spoof, TerminalFacts subclass, authority `str` subclass (M99–M102) |

---

## 33. Round 23 review disposition

**Verdict: M-Q4 boundary respected and applied as ruled; architecture standing;
v26 deferred on three load-bearing semantic gaps plus two corrections — all
closed.** No finding relied on private-state corruption or reopened a `0008`
obligation. The gaps concerned the `on_committed` protocol contract (a success
trusted without its mandatory publication; a publication frozen before its cell
was validated) and the exact authority carrier type (a subclass that could
intercept attribute access). The bounded adjacent-migration claim, resolution/
refusal split, and finite M-Q4 acceptance framework remain approved.

| # | finding | closed by |
|---|---|---|
| 1 | a semantically valid `OpenResult` was accepted without any `on_committed` publication, letting an untouched v1 store be reported migrated at v2 | **a successful migrate result requires exactly one valid publication equal to it**; its absence is `internal-error` from independently-established facts (M103) |
| 2 | the callback freezer exact-typed and copied but did not apply the migrate-mode semantic table before establishing position — a `migrated`/(F,F) callback followed by a kernel error recorded a false destination-v2 state | **one shared `_cell_problems` validates the mode-aware cell at BOTH the callback and the returned result, before any fact is established** (M104) |
| 3 | the top-level authority gate accepted `MigrationAuthority` subclasses; one could begin raising after the real commit and escape from the initial fallback outside the terminal `try`, stranding the operation attempted-only | **`type(a) is MigrationAuthority` before any field access** (a subclass is a closed refusal); **the initial fallback moved inside the total boundary** (M105) |
| A | a simpler hostile authority subclass was misclassified `internal-error` before consumption | closed by the same exact-carrier-type check — a malformed authority is `migration-quiescence-required` (M105) |
| B | the independent gate omitted the three fresh cases | **added** — success-without-callback, impossible-callback-cell, authority subclass (M103–M105) |
