# Feature spec: the release-migration orchestrator

Spec-Status: draft
Spec-Requires: 0007, 0013, 0016

| | |
|---|---|
| **Author / session** | dev |
| **Version** | v5 — EXTERNAL ROUND 3 (5 bin-(a) + 1 bin-(b), narrowing 7→9→5; R2-2/3/4/9 confirmed closed; every finding confined to v4's own folds): ALL FOLDED. **R3-1 (A, found-in-fix of R2-1):** the reviewer EXECUTED the fingerprint and raw `manifest()` is not JSON-serializable (tuple keys) → the encoding defers to the instrument's own: `identity(manifest())` (0007's tuple-key-safe canonicalisation, `schema_version.py:374`) with `digest()`'s exact `json.dumps` parameters; a NEW independent digest oracle (I22) incl. the tuple-key negative case. **R3-2 (D, sweep-miss of R2-7):** the §2c forged-resolution cell still said "cannot grant an authority", contradicting corrected I18 → rewritten to I18's two-condition comparison verbatim. **R3-3 (D, sweep-miss of R2-8):** I14 still said each-error-re-resolves → pinned to exactly three resolves + three mints, call-counts asserted. **R3-4 (A+F, found-in-fix of R2-5):** `ReadbackResult` was a name → the exact NamedTuple sum carrier with total cross-field laws, immutable capped `problems`, exact-type admission, and the adversarial cells (I23); §7a row added. **R3-5 (G+C, found-in-fix of R2-6):** accepted 0013 permits the package escape PRE-MINT (no operation id exists) → two routes (pre-mint: no readback, labeled unavailable; post-mint: the record is a fact source ONLY when valid AND bound to `package-inconsistent`); §7's every-exit-3-reports-commit claim narrowed. **B3-1 (found-in-fix of B2-1):** the MCP reconciliation was wrong AGAIN — the importorskip gates ONE test (`test_mcp_server_wiring`), not the file's five; the reviewer's mcp-absent run sees 4 PASS + 1 SKIP → the inventory entry now states the gate's SCOPE, and the decomposition follows. *Misses diagnosed: R3-2/R3-3 are carrier-sweep failures of my own round-2 fixes (the 0015 sweep class — fixed the primary site, never grepped the invariant table and §2c); R3-1/R3-4 are constructions I stated but did not EXECUTE (the reviewer ran the probe; the I22 oracle and I23 cells make execution the acceptance condition); B3-1 is verify-against-the-domain at test-file granularity — I counted `def test`, not the gate's scope.* |
| **Status** | *narrative only — canonical is the `Spec-Status:` line* |
| **Internal reviewers** | research — round 1 RETURNED + folded (v2); re-review CLEARED 2026-08-13. *(v2 history: F1 readback reconciliation — refined by external R1-4; F2 sections inlined; F3 the `PreflightResolution` §2c row + reason-labeling pin.)* |
| **External review** | ROUND 3 RETURNED 2026-08-13 (package `0018-v4-20260813T2140Z.tar.gz`): 5 bin-(a) + 1 bin-(b), folded as v5; round-4 package next |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation

Accepted 0016 defines what deleting `source_type` means and rules the D2
policy (base-6-only; the two-release ladder) — but four consecutive external
rounds (11–14) showed the EXECUTION machinery generates a construction
contract of its own: a preflight with a total state matrix, a host-owned
attestation, a typed mint API, a structured result carrier, a terminal
readback, and a CLI acquisition flow. Folding a fifth layer inside 0016
would hold its endorsed core hostage (the Ruling-2 lesson). **Do nothing:**
0016's D2 cannot be implemented at all — I13 gates it on this spec.

**Alternatives rejected:** keep it in 0016 (four rounds of evidence against);
implement without a spec (the machinery touches guarded `cli.py`-adjacent and
0013-amendment surfaces).

---

## 2. Field contracts touched

This spec performs no stored-state operation of its own — it orchestrates
operations 0013 already specifies. Its contracts are the NEW public carriers
and the marked 0013 amendments:

| carrier | contract | consumers |
|---|---|---|
| `run_release_migration(path, *, host_attestation) -> MigrationResult` | the orchestrator (`store/migration.py`, future surface): total over every input per the §4 matrix; every short-circuit zero-authority/zero-audit | CLI `migrate`; hosts running release migrations |
| `MigrationAttestation` | immutable, exact-type-admitted carrier of {`quiesced is True`, `backup_ref` in 0013's token grammar} — the host-owned facts, passed VERBATIM into minting, never fabricated | `run_release_migration`, `mint_release_authority` |
| `MigrationResult` | frozen: `Outcome`-label string-compare + `store_changed: Optional[bool]`, `transaction_committed: Optional[bool]`, `resulting_state` (0013's five words verbatim), `resulting_version: Optional[int]`, `diagnostic: str`; a validating constructor REJECTS every carrier outside **the literal §4e table** | CLI reporting; hosts — facts never inferred from the label (0013 r8-f3) |
| `PreflightResolution` | frozen evidence carrier {`canonical_path`, `resolved_base`, `source_fingerprint`}, validating constructor, exact-type admission; produced ONLY by the shared opening-path interface the §4h amendment defines; consumed as reason-labeling evidence ONLY (I18) | the preflight; `mint_release_authority` |
| `mint_release_authority(path, attestation, *, resolved: PreflightResolution) -> MigrationAuthority`, raising `MintError(reason)` | the production mint API; closed reason enum {`source-missing`, `source-unaccepted`, `source-changed`}; three mint calls max, re-resolution after the first two failures only, the third error → `mint-contention` (R2-8) | the orchestrator; host-reachable (which is why §2c carries its rows) |
| 0013 `Outcome` vocabulary | +2 RETURNABLE members by marked amendment (`unsupported-base`, `mint-contention`) — **and `TERMINAL_OUTCOMES` is defined EXPLICITLY: (OUTCOMES ∪ audit-only) − {the two new members, the two never-terminal audit outcomes} (R2-4, closing a latent 0013 gap); `TerminalFacts`/terminal publication validate against it; the oracle extends with four exclusion cells + the package-inconsistent inclusion cell** | 0013's exhaustive outcome tests + the presend-gate oracle, extended |
| `read_terminal(operation_id)` | 0013-amendment readback: own-operation; returns the closed **`ReadbackResult`** (record \| absent \| malformed) and RAISES NOTHING (R2-5) — every raise decision is the orchestrator's, routed by §4f; consistency from append-once immutability | the orchestrator's delegated-outcome facts |
| `MigrationAuditReadError` | frozen, validated carrier {`operation_id`, `failure` ∈ {missing, malformed, mismatched}, `outcome`, `derived_resulting_state` — from the frozen outcome→states map, labeled derived} — constructed by the ORCHESTRATOR, which holds the kernel outcome (§4f, R2-5) | the CLI's exit-3 stderr; hosts |
| `ReadbackResult` | the closed readback sum carrier (§4f, external R3-4): NamedTuple {`kind` ∈ {record, absent, malformed}, `facts: Optional[TerminalFacts]`, `problems: tuple[str, ...]`} — cross-field laws constructor-enforced, problems immutable/capped, exact-type admitted | `read_terminal` → the orchestrator's §4f routing |
| CLI `migrate` | gains `--i-have-quiesced` + `--backup REF`; exits 0/1/2 and **3 = the loud-escape class (`MigrationAuditWriteError` / `MigrationAuditReadError` / `PackageConsistencyError`)** | operators; `tests/test_migrate_cli.py` re-dispositioned §7a |

## 2c. Untrusted inputs — REQUIRED, blocking

*(The below-v6 and attestation rows are the 0016 v17 rows, reviewed in its
rounds 10–14, transferred; the `PreflightResolution` row is NEW — the F3
ruling.)*

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant that pins it |
|---|---|---|---|---|---|
| `path` (caller-supplied) | missing file → the missing refusal outcome, no minting | foreign/malformed/unstamped → the corresponding 0007/0013 refusal outcome, no minting | newer-than-head → the newer refusal, no minting | a path racing with concurrent writes | the preflight matrix is TOTAL (I13); the preflight→mint race closes by reclassification (§4c), never by trusting the first resolution |
| a stored below-v6 database (bases 1–5) presented post-D2 | — | — | ordinary OPEN → 0013's existing below-head refusal, unchanged by this spec | the migration ORCHESTRATOR'S PREFLIGHT → the `unsupported-base` outcome (returned, never raised), the ladder diagnostic, NO authority, ZERO 0013 audit rows, bytes+stamp unchanged | I13; `test_below_v6_base_refuses_with_the_ladder_message` (all five bases) + `test_below_v6_open_unchanged` |
| `MigrationAttestation` (caller-supplied — the host-owned facts) | absent → `TypeError` (required keyword) | `quiesced=1`/truthy-object → refused (`is True` check); empty/whitespace `backup_ref` → `ValueError` | unknown extra fields → refused (immutable, exact) | a hostile SUBCLASS (attribute-interception) or duck-typed carrier | **exact-type admission `type(x) is MigrationAttestation` (R14-4 — 0013's own authority regression); duck-types and subclasses REFUSED, never copied; `backup_ref` validates with 0013's own token grammar**; `test_attestation_contract` (absent, coerced, grammar-violating incl. embedded-space, duck-type, hostile-subclass cells) |
| **`PreflightResolution`** (the mint API's `resolved=` evidence — **caller-suppliable**: `mint_release_authority` is the production surface, so its parameters are host-reachable; "orchestrator-internal" is not assumed — the F3 ruling) | absent → `TypeError` (required keyword) | wrong type → refused at the boundary | — | **a FORGED resolution — analyzed in I18's two-condition form VERBATIM (external R3-2; the prior cell's "cannot grant an authority" contradicted I18):** with a VALID store + attestation, mint SUCCEEDS identically under forged evidence (an authority IS granted — forgery must not deny either); with a FAILING store, mint fails identically and at most the `MintError` reason label differs, and the re-resolve then re-establishes truth. Forgery cannot corrupt a terminal outcome or skip a validation; worst case is a misleading reason label on an already-failing call | **the load-bearing pin: mint treats `resolved` as reason-labeling evidence ONLY, never authority-relevant — it never skips or weakens any check because of it** (else this row becomes a TOCTOU and security-critical); `test_resolution_is_reason_labeling_only` (forged resolution → identical validation behaviour, no authority, outcome facts unchanged) |
| CLI flags | `--i-have-quiesced`/`--backup` missing on the migration path → exit 2 with usage | invalid `--backup` token → exit 2 with the grammar stated | — | flags are the operator's explicit assertions — never prompted for (prompting is coercion-prone and non-interactive-hostile) | the frozen flag acquisition (§4); `test_migrate_cli.py` amended |

### 2c-ii. Assertions about reach — run 2026-08-13

| assertion | command | result |
|---|---|---|
| the orchestrator surfaces do not exist yet (this spec defines them) | `grep -rn "run_release_migration\|mint_release_authority\|PreflightResolution" src/` | no hits — future surface, nothing to collide with |
| the 0013 instrument's names this spec builds on exist and are the reviewed ones | `grep -n "class MigrationAuthority\|class TerminalFacts\|class MigrationAuditWriteError" specs/migrations_0013.py` | `:642`, `:860`, `:375` |
| `make_authority` is test-only, not the production mint API | `grep -rln "make_authority" src/` vs `tests/` | zero `src/` hits; consumed by `tests/test_migrations_0013.py` and the instrument only |
| the CLI migrate verb currently delegates DIRECTLY to `migrate_store` (the contract this spec re-dispositions) | `grep -n "migrate_store" src/veracium/cli.py` | `:267`, `:270` — the ce896fc contract, moved under this spec's authority in §7a |
| the hostile-subclass regression pattern exists in accepted 0013 | `grep -n "class Hostile" tests/test_0013_presend_gates.py` | `:1541`, `:1557` — the pattern R14-4 imports for the attestation |

## 3. Trust-class matrix — REQUIRED, blocking

**No new trust class.** Every caller of this surface is the OPERATOR/HOST — the
principal that already owns the database file and could edit it with sqlite3.
The machinery exists to make an *authorized* operation safe, auditable, and
honest about its outcome — not to defend the store from its owner. The
adversarial §2c cells guard against *mistakes wearing valid shapes* (a truthy
non-True `quiesced`, a duck-typed attestation, a forged resolution) and against
this spec's own code trusting inputs it shouldn't — not against a hostile
principal gaining anything (there is nothing here to gain that file ownership
does not already grant).

## 3b. Authorization and scope — the information level (the 0015 lens)

- **Reachability:** `run_release_migration` and the CLI verb are operator/host
  surfaces. Not exposed over MCP (no tool registers it); not reachable by the
  model; not reachable through `Memory` recall/ingest paths. Offline by
  contract (0013's quiescence requirement, attested by the caller).
- **What `MigrationResult` newly reveals, per recipient:** the caller learns
  the outcome label, the 0013 `resulting_state` vocabulary verbatim
  (`missing`/`unaccepted`/`unknown` included), the facts quadruple, and a
  diagnostic. Every one of these is derivable by the SAME principal from
  surfaces it already owns: the path's existence and bytes (it supplied the
  path), 0007's shape resolution on a file it can open, and 0013's existing
  `migrate_store`/audit records. `unsupported-base`'s diagnostic is static
  ladder text; `mint-contention` reveals that a concurrent process raced —
  concurrency visibility over the caller's own store, same principal.
  **No recipient learns anything a principal of that class could not already
  derive; no cross-user, cross-tenant, or content data is carried** (the
  result carries versions, states, and fixed vocabulary — never store
  content).
- **The audit errors** (`MigrationAuditWriteError`, `MigrationAuditReadError`)
  reveal "the audit trail failed" to the operator whose audit trail it is —
  loud by design (§4); hiding them is the hazard, not surfacing them.

---

## 4. Behaviour — the CONSOLIDATED contract (v3, external R1-1)

*One integrated statement. v1/v2 layered the round-14 and internal-round
corrections beneath an unconsolidated v17 §4 — the exact layering failure
0015's round 7 taught (and whose fix there was consolidation); external round
1 found four §4↔§4b contradictions the layering produced. This section now
states the final contract once; nothing below it amends it. The construction's
provenance (0016 rounds 10–14 + the four R14 findings + internal F1/F3) is in
the header and the closure ledger, not in a corrections layer.*

### 4a. The preflight and the total matrix

**`run_release_migration(path: str, *, host_attestation: MigrationAttestation)
-> MigrationResult`** in `src/veracium/store/migration.py`. The preflight
resolves the store through **the one shared opening/planner path** (0007's own
resolution, including its repair-during-opening probe) and **intercepts
EVERYTHING except resolved base 6**:

- **bases 1–5** → the `unsupported-base` outcome (returned, never raised) with
  the two-release ladder diagnostic verbatim;
- **already-current v7, clean** → `current` with no effect;
- **already-current v7 with rebuildable drift** → `current` WITH the repair
  facts — the repair rides the one shared opening path, never a second
  repairer;
- **missing / unopenable / malformed / locked / unqualified-runtime / foreign
  / newer / bad-version / stamped-shape-mismatch** → the corresponding closed
  refusal outcome (the §4e table enumerates every cell);
- **resolved base 6 ALONE** proceeds to authority minting (§4c) and delegates
  to `migrate_store(path, authority)` — 0013's ordinary audited operation.

Every preflight interception creates ZERO authorities and ZERO 0013 audit
rows. **Byte-identity holds for every preflight cell EXCEPT
current-with-repair** (external R1-7): that one cell commits the
rebuildable-drift repair through the shared opening path and honestly reports
`(True, True, destination, 7)`; every other interception leaves the store
byte-unchanged. Ordinary OPENING of a below-v6 store is UNCHANGED by this
spec — 0013's existing below-head refusal governs it; only the orchestrator's
preflight returns `unsupported-base`.

### 4b. `PreflightResolution` — the construction (external R1-2)

The preflight's observation, as an immutable evidence carrier — and it exists
**only where a store RESOLVED** (external R2-1: missing, unopenable, and
rejected stores have no base or fingerprint to carry, and no cell that
consumes one — mint is reached only from resolved base 6, and the only other
consumer is `unsupported-base`'s `resulting_version`, which needs a resolved
base 1–5). Every non-resolving cell short-circuits with NO
`PreflightResolution` constructed.

- **Fields, exactly:** `canonical_path: str` (non-empty; the absolute
  resolved path as the shared opening path canonicalises it),
  `resolved_base: int` (∈ the accepted-base set {1…6}),
  `source_fingerprint: str` (exactly 64 lowercase hex characters).
- **The fingerprint, executable (external R3-1 — the reviewer's probe proved
  raw `manifest()` is not JSON-serializable: its keys are `(type, name)`
  TUPLES; the fix defers to the instrument's own encodings rather than
  inventing one):** SHA-256 over the UTF-8 concatenation of length-framed
  segments, each segment its byte length as an 8-byte big-endian prefix
  followed by the bytes, in this order: (1) the domain tag
  `0018-preflight-fingerprint-v1`; (2) `str(user_version)` (the stamped
  value as decimal); (3) `json.dumps(identity(manifest(conn)),
  sort_keys=True, separators=(",", ":"))` — **`identity()` is accepted
  0007's OWN tuple-key-safe canonicalisation** (`schema_version.py:374`:
  sorted `"type:name"` string keys over every object, nothing excluded —
  the version-independent record), and the `json.dumps` parameters are
  byte-identical to the ones 0007's own `digest()` uses
  (`schema_version.py:391`; `ensure_ascii` default True). The complete
  byte-exact DDL and `table_xinfo` evidence ride inside `identity()`'s
  values unchanged. **An independent digest oracle is an acceptance check
  (I22):** a separately-written encoder reproduces the fingerprint
  byte-for-byte on fixture stores, incl. a generated-column store (the
  `table_xinfo` cell) and a quoted-literal DDL store (0007's own
  round-3 byte-exactness case).
- **Representation, pinned:** a `NamedTuple` (the same representation
  accepted 0013 uses for its own carriers); the validating constructor
  refuses an empty path, a base outside the accepted set, or a malformed
  fingerprint. Exact-type admission at every consumer (`type(x) is
  PreflightResolution` — the same rule as the attestation).
- **Producer:** ONLY the shared opening/planner path, which this spec AMENDS
  (§4h) to RETURN its resolution evidence for every store it RESOLVES —
  external R1-2 established that the existing 0007 APIs do not return it;
  the amendment is the defined interface, and the preflight consumes it
  rather than re-deriving. (The interface also defines the read-only
  resolution mode — §4h, external R2-3.)
- **Consumption (the internal-F3 pin, unchanged):** mint receives `resolved`
  as **reason-labeling evidence ONLY** — it re-resolves the path itself,
  validates path and attestation against the REAL store on every attempt, and
  never skips or weakens a check because of `resolved` (I18). The evidence
  exists so mint can HONESTLY LABEL a failure: current observation matches
  `source_fingerprint` but the shape is no longer accepted → `source-
  unaccepted`; observation differs from `source_fingerprint` → `source-
  changed`; nothing at `canonical_path` → `source-missing`.
- Its §2c row carries the forged-resolution analysis (bounded: worst case a
  mislabeled reason on an already-failing call).

### 4c. The mint API and the bounded retry

**`mint_release_authority(path, attestation, *, resolved: PreflightResolution)
-> MigrationAuthority`**, raising **`MintError(reason)`** with the closed
reason enum **{`source-missing`, `source-unaccepted`, `source-changed`}** (the
test-only `make_authority` and its undifferentiated `ValueError` are not the
production surface). **The retry sequence, EXACT (external R2-8 — "every
MintError reclassifies" was incompatible with the no-fourth-resolve bound and
is superseded):** at most THREE mint calls; **re-resolution follows only the
first two failures**:

    resolve0 -> mint1 --err--> resolve1 -> mint2 --err--> resolve2 -> mint3
    --err--> return `mint-contention`

A re-resolution that lands on a non-base-6 cell exits with that cell's
interception outcome (a vanished store -> the missing refusal; a migrated
store -> `current`) — that is what the first two errors' reclassification
means. **The THIRD `MintError` terminates as `mint-contention`** — facts
`(False, False, unknown, None)`, diagnostic naming the three attempts — never
a fourth resolve, never "proceed to mint", and never a bare final
classification (contention that persists three rounds is its own honest
outcome, not whichever refusal the last race happened to leave behind).

### 4d. `MigrationAttestation` — the host-owned facts, exact

An immutable carrier of exactly **{`quiesced` — must be the bool literal
`True`, checked `is True`, so `1` and truthy objects refuse; `backup_ref` —
validated by 0013's OWN frozen token grammar (1–128 ASCII), no separate
predicate, no normalization}**. **Admission is EXACT-TYPE: `type(attestation)
is MigrationAttestation`** — subclasses (which can intercept attribute access)
and duck-typed carriers are REFUSED, never copied (accepted 0013's own
authority-regression rule; the v16 re-validated-copy rule stays retired). The
attestation passes VERBATIM into minting; the orchestrator never fabricates or
defaults it.

### 4e. `MigrationResult` — the carrier and THE LITERAL TABLE (external R1-3)

Frozen fields: the `Outcome`-string label + `store_changed: Optional[bool]`,
`transaction_committed: Optional[bool]`, `resulting_state: str` (0013's
five-word vocabulary VERBATIM: `destination` · `source` · `missing` ·
`unaccepted` · `unknown`), `resulting_version: Optional[int]`, `diagnostic:
str`. Facts are never inferred from the label (0013 r8-f3). **A validating
constructor rejects every carrier not in the table below — the table IS the
domain, and the independent oracle enumerates it (I15).**

**Preflight rows** (zero-authority, zero-audit; facts fixed per cell):

| outcome | changed | committed | resulting_state | resulting_version |
|---|---|---|---|---|
| `unsupported-base` | False | False | `source` — the store was opened, read, and resolved as an ACCEPTED older-base source, untouched (the read-and-accepted case; `unaccepted` is for read-and-rejected) | the resolved base (1–5) |
| `current` (clean) | False | False | `destination` | 7 |
| `current` (with repair) | True | True | `destination` | 7 |
| `migration-source-missing` (nothing at the path) | False | False | `missing` | None |
| `migration-source-missing` (a file EXISTS but is a valid, empty, `user_version=0` SQLite database with no objects — accepted 0013's own classification for an empty replacement, external R2-3) | False | False | `unaccepted` | None |
| `store-unopenable` | False | False | `unknown` | None |
| `invalid-store` | False | False | `unknown` | None |
| `locked` | False | False | `unknown` | None |
| `unsupported-sqlite` | False | False | `unknown` | None |
| `foreign-shape` | False | False | `unaccepted` | None |
| `newer` | False | False | `unaccepted` | None |
| `invalid-version` | False | False | `unaccepted` | None |
| `stamped-shape-mismatch` | False | False | `unaccepted` | None |
| `invalid-request` (malformed call) | False | False | `unknown` | None |
| `mint-contention` | False | False | `unknown` | None |

**Delegated rows** (base 6; the facts come VERBATIM from the §4f routing —
the terminal record where one exists, the fixed no-record rows where 0013
defines none). **The delegated law is DEFERENCE, not restatement (external
R2-2 — v3's re-derived laws contradicted accepted 0013, whose TerminalFacts
carries SEVEN fields with TRI-STATE effects: `internal-error/None/None/
unknown/None`, `migration-failed/None/None/unknown/None`, and
`internal-error/True/True/destination/7` are all reviewer-verified VALID):**
a record-bearing delegated carrier is valid **iff the record's own
`TerminalFacts` passes accepted 0013's `problems()` verbatim** — this spec
adds no effect/state/version law of its own on that path, and the result
carries the record's facts unmodified (`store_changed`/`transaction_
committed` are `Optional[bool]` precisely so the tri-state survives). The
ONLY 0018-added checks: the outcome is a member of 0013's returnable
vocabulary, and the record binds to this operation (§4f's mismatch rule).

**No-record rows (fixed — external R2-9 revises v3's `source`/6 claim, which
was STALE under the race model this spec itself specifies):** after minting,
a concurrent process can migrate the store before an audit-activation
refusal, so the preflight's moments-old observation does NOT prove the
store's current state. The only contract-proven facts are THIS operation's:
it accessed nothing and changed nothing. All four no-record outcomes —
`migration-audit-unavailable`, `migration-audit-state-unknown` (with the
mandatory retry-unsafe diagnostic: the authority MAY be consumed, query the
durable `operation_id` before retrying), and the pre-observation
`migration-quiescence-required` / `migration-evidence-missing` (when §4f
finds no record) — carry **(False, False, `unknown`, None)**, where
False/False are this-operation facts and `unknown`/None honestly decline to
assert the store's present state.

### 4f. Delegated-outcome routing, the readback, and the loud escapes (external R1-4/R1-6, revised R2-5/R2-6)

**`read_terminal(operation_id)`** (defined in the marked 0013 amendment,
§4h) **RAISES NOTHING (external R2-5 — v3 required it to raise an exception
whose mandatory `outcome` field it does not possess):** one SELECT by the
operation id, in its own read transaction, returning a closed
**`ReadbackResult`** — **the exact carrier (external R3-4; a name is not a
construction):** a `NamedTuple` (the instrument's carrier convention) of
`kind: str` ∈ {`"record"`, `"absent"`, `"malformed"`},
`facts: Optional[TerminalFacts]`, and `problems: tuple[str, ...]`, with the
cross-field laws TOTAL and constructor-enforced: `kind=="record"` ⇔ `facts`
is a `TerminalFacts` whose own `problems()` is empty ∧ `problems == ()`;
`kind=="absent"` ⇔ `facts is None` ∧ `problems == ()`; `kind=="malformed"`
⇔ `facts is None` ∧ `problems` non-empty. `problems` is an IMMUTABLE tuple
of `str` (a list or any mutable/nested collection REFUSES — `type(x) is
tuple`, each element `type(e) is str`), capped at 32 entries of ≤500
characters each with an explicit `…truncated` final entry when the cap
bites, and the malformed row's construction is TOTAL: any durable row
failing validation yields at least one problem entry (the validator's own
problem list, capped). Exact-type admission at every consumer
(`type(x) is ReadbackResult`); adversarial cells: a hostile subclass, a
list-typed `problems`, a mutable object inside `problems`, and every
cross-field-law violation REFUSE at construction (I23). Consistency comes
from 0013's append-once-per-`operation_id` immutability, NOT from connection
identity; own-operation binding unchanged. **Every raise decision belongs to
the ORCHESTRATOR**, which holds the kernel outcome the exception needs.

**The routing, total over every delegated return:**

1. Kernel returns an outcome → `read_terminal(operation_id)`.
2. **`record` + the record's outcome EQUALS the kernel return** → the
   result's facts come from the record verbatim (§4e's deference law).
3. **`record` + the record's outcome DIFFERS from the kernel return**
   (external R2-5's silent-disagreement case — e.g. a returned
   `migration-failed` beside a valid `migration-quiescence-required` record)
   → **`MigrationAuditReadError(failure="mismatched")`** — a valid record
   that does not bind to the return is an audit-integrity failure, never a
   fact source.
4. **`absent` + outcome ∈ the no-record set** — exactly
   {`migration-audit-unavailable`, `migration-audit-state-unknown`,
   `migration-quiescence-required`, `migration-evidence-missing`} — → the
   §4e fixed no-record row.
5. **`absent` + any other outcome** (consumption implies a record or a
   `MigrationAuditWriteError`) → `MigrationAuditReadError(failure="missing")`.
6. **`malformed` + any outcome** → `MigrationAuditReadError(failure="malformed")`.
7. **Named escapes propagate, never converted to a `MigrationResult`:**
   `MigrationAuditWriteError` (0013's, unchanged — it carries its own
   facts); `MigrationAuditReadError`; and **`PackageConsistencyError`**,
   with TWO routes (external R3-5 — accepted 0013 permits this escape
   BEFORE mint, during release-identity acquisition, where no operation id
   exists; v4's single retained-id route assumed one always does):
   **pre-mint** (the escape fires before any authority was minted) — no
   readback is possible or attempted; the CLI prints `resulting_state:
   unavailable (pre-mint: no operation minted; store not accessed)`;
   **post-mint** (the orchestrator retains the minted `operation_id`) — the
   escape-path readback runs, and the record is accepted as a fact source
   ONLY when it is valid AND its outcome is `package-inconsistent` (the one
   outcome 0013 terminal-records for this escape — a valid record carrying
   any OTHER outcome is a binding failure, printed as `resulting_state:
   unavailable (readback: mismatched)`); `absent`/`malformed` → `resulting_
   state: unavailable (readback: missing|malformed)`. The exception then
   propagates unchanged on every route. §4g's and §7's claims are narrowed
   to match: recorded facts where a valid BOUND record exists,
   explicitly-labeled unavailability otherwise.

**`MigrationAuditReadError` — the executable carrier:** frozen fields, all
validated at construction: `operation_id` (0013's token grammar),
`failure: "missing" | "malformed" | "mismatched"`, `outcome` (the
kernel-returned `Outcome`, ∈ the closed vocabulary), and
`derived_resulting_state` — the sole member of accepted 0013's
`_OUTCOME_TERMINAL_STATES[outcome]` when that set is a singleton (e.g.
`migrated` → `destination`), else `"unknown"`. The state is DERIVED from the
frozen outcome→states map and the kernel return the orchestrator holds —
never read from the failed record, never fabricated — and both the exception
message and the CLI's stderr line label it `derived-from-outcome`.

### 4g. The CLI contract

`veracium migrate --db X --i-have-quiesced --backup REF` — flags, never
prompts; both required for the migration path (missing → exit 2 with usage);
an invalid `--backup` token → exit 2 with the grammar stated. Exit codes:
**0** = `migrated`/`current` · **1** = every refusal outcome (incl.
`unsupported-base` and `mint-contention`) · **2** = usage / invalid
attestation · **3** = a named loud escape (`MigrationAuditWriteError`,
`MigrationAuditReadError`, `PackageConsistencyError`), with the exception
class on stderr plus: the write error's own carried facts; the read error's
`derived_resulting_state`, labeled derived-from-outcome; and for the package
escape, the RECORDED facts where the §4f escape-path readback found a valid
record, else `resulting_state: unavailable (readback: missing|malformed)` —
every printed state labeled recorded, derived, or unavailable (external
R2-6: the accepted package exception itself carries no facts, and the CLI
never invents them).
Reporting stays on the structured fields; `cli.py` and
`tests/test_migrate_cli.py` are dispositioned in §7a under this spec's
authority.

### 4h. The marked 0013/0007 amendments (land same-commit with the implementation)

> **Outcome vocabulary (revised by external R1-5 AND R2-4):** the returnable
> vocabulary gains `unsupported-base` and `mint-contention`, produced ONLY by
> the release orchestrator's preflight/retry machinery before authority
> minting. **The terminal domain is defined EXPLICITLY, never by subtraction
> over `OUTCOMES` alone (R2-4 — the v3 subtraction both omitted the
> audit-only `package-inconsistent`, which is a valid terminal outcome
> outside `OUTCOMES`, and still admitted the two never-terminal audit
> outcomes through the default-`{unknown}` mapping):**
>
>     TERMINAL_OUTCOMES = (OUTCOMES ∪ _AUDIT_ONLY_OUTCOMES)
>                         − { unsupported-base, mint-contention,
>                             migration-audit-unavailable,
>                             migration-audit-state-unknown }
>
> `TerminalFacts` and terminal publication validate against
> `TERMINAL_OUTCOMES`; the independent terminal-facts oracle is EXTENDED
> with all FOUR exclusion cells and the `package-inconsistent` inclusion
> cell. **This amendment also CLOSES a latent gap in accepted 0013 itself**
> (reviewer-probed both rounds): today `migration-audit-unavailable` and
> `migration-audit-state-unknown` pass `TerminalFacts.problems()` through
> the default mapping although 0013's own text says they never terminalize —
> a strengthening the exhaustive oracle diff will show as exactly those
> cells. Neither new member creates an audit row, a permitted-state entry,
> or a terminal-facts mapping. `Outcome` continues to refuse non-members.
>
> **Resolution evidence + the read-only resolution mode (R2-3):** the shared
> opening/planner path gains a READ-ONLY resolution mode — it never creates,
> never adopts, never stamps — that RETURNS, for every store it RESOLVES,
> the evidence `PreflightResolution` is built from (`canonical_path`, the
> resolved base, the stamped `user_version`, and the complete `manifest()`
> manifestation §4b's fingerprint is computed over). In this mode: a valid
> but EMPTY `user_version=0` database (no objects) is classified
> source-missing/unaccepted — never created-into, never adopted; a
> legitimate unstamped store whose shape matches a `legacy_base_versions()`
> entry resolves to that base WITHOUT being stamped; an unstamped
> non-matching store refuses as foreign. (Ordinary `migrate_store`/open
> behaviour is untouched — the mode exists for the preflight only.)
>
> **Terminal-record readback:** `read_terminal(operation_id)` per §4f —
> own-operation; returns the closed `ReadbackResult`
> (record | absent | malformed); raises nothing; the initiating orchestrator
> owns every raise decision, and facts are never inferred from the label.


## 5. Regime analysis

The §4e outcome × facts table IS the regime enumeration — every input class
lands in exactly one row, and the validating constructor makes off-table
carriers unrepresentable. The four regimes in prose: **preflight
interceptions** (facts from the table, zero authorities, zero audit rows,
store byte-unchanged — **with exactly one exception, external R1-7:
current-with-repair commits the rebuildable-drift repair and reports (True,
True, destination, 7)**); **delegated base-6 operations with a terminal
record** (facts from the readback verbatim, constructor-checked against
0013's frozen outcome→states map); **delegated no-record outcomes** (the
four 0013-defined pre-consumption/pre-observation returns → the fixed §4e
rows, no readback error); **the loud escapes** (`MigrationAuditWriteError` /
`MigrationAuditReadError` / `PackageConsistencyError` ESCAPE — never a
`MigrationResult`, never exit 0).

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **I13** the preflight matrix is TOTAL: bases 1–5 → `unsupported-base` + the ladder; clean-current → `current` (False, False, destination, 7) byte-identical; current-with-repair → `current` (True, True, destination, 7) via the one shared opening path; missing/foreign/malformed/unstamped/newer/locked → the corresponding refusal without minting; every short-circuit zero-authority/zero-audit; resolved base 6 ALONE mints and delegates | `test_preflight_matrix_total` (every cell incl. both current cells and locked) + `test_below_v6_base_refuses_with_the_ladder_message` (all five bases) + `test_below_v6_open_unchanged` + `test_base_6_proceeds_through_the_audited_operation` | CI |
| **I14** the mint race closes by the EXACT §4c sequence (pinned by external R3-3 after R2-8's fix missed this carrier) | `test_mint_race_reclassifies` — EXACTLY three resolves and three mint calls, interleaved resolve→mint, with re-resolution after failures one and two ONLY and NO resolve after the third failure; each of the first two `MintError` reasons re-resolves to the now-true outcome; the third → `mint-contention`, facts `(False, False, unknown, None)`, three attempts named in the diagnostic — never proceed-to-mint, never a fourth resolve (call-count asserted, not inferred) | CI |
| **I15** `MigrationResult` carriers are table-only | `test_migration_result_truth_table` — the LITERAL §4e table: every preflight row (all FIFTEEN, incl. both `migration-source-missing` forms — R2-3), the delegated DEFERENCE law (a record-bearing carrier is valid iff its seven-field `TerminalFacts` passes accepted 0013's `problems()` verbatim, tri-state effects included — R2-2), and the four fixed `(False, False, unknown, None)` no-record rows (R2-9); the validating constructor rejects every out-of-table carrier incl. every non-vocabulary state word. **Gate-extension obligation: the validator joins `tests/test_0013_presend_gates.py`'s independent-oracle pattern — a separately-written oracle enumerates the §4e domain and the exhaustive diff must be empty** | CI |
| **I20** the two new outcomes are returnable, never terminal (external R1-5) | `test_new_outcomes_are_excluded_from_terminal_facts` — the reviewer's probe as the regression: constructing `TerminalFacts` (and attempting terminal publication) with `unsupported-base` or `mint-contention` REFUSES; the extended independent oracle enumerates all FOUR exclusion cells (the two new members + the two never-terminal audit outcomes — R2-4's latent-0013-gap closure) AND the `package-inconsistent` inclusion cell; the explicit `TERMINAL_OUTCOMES` definition is asserted | CI |
| **I22** the fingerprint has an independent oracle (external R3-1) | `test_preflight_fingerprint_oracle` — a separately-written encoder (its own `identity`-equivalent and framing) reproduces the §4b fingerprint byte-for-byte on fixture stores incl. a generated-column store and a quoted-literal DDL store; the raw-`manifest()` serialization failure (tuple keys) is the named negative case | CI |
| **I23** `ReadbackResult` is a closed constructed carrier (external R3-4) | `test_readback_result_contract` — every cross-field-law violation, a hostile subclass, a list-typed `problems`, a mutable member inside `problems`, and an uncapped problem flood all REFUSE at construction; the malformed row's total construction yields ≥1 capped problem entry | CI |
| **I21** the delegated routing is total (external R1-4) | `test_delegated_routing_total` — for EVERY member of 0013's returnable vocabulary as a delegated return: record-present → facts verbatim; record-absent × the four no-record outcomes → the fixed rows, NO error; record-absent × every other outcome → `MigrationAuditReadError(missing)`; malformed × any outcome → `MigrationAuditReadError(malformed)`; a VALID record whose outcome differs from the kernel return → `MigrationAuditReadError(mismatched)` (R2-5); `PackageConsistencyError` propagates on BOTH routes (R3-5): pre-mint → no readback, `unavailable (pre-mint)`; post-mint → readback with the record accepted ONLY when valid AND bound to `package-inconsistent` (any other outcome → `unavailable (readback: mismatched)`); absent/malformed → unavailable — stderr facts labeled recorded or unavailable, never invented | CI |
| **I16** the attestation contract is exact | `test_attestation_contract` — absent, coerced (`quiesced=1`/truthy object), grammar-violating (incl. embedded space), duck-typed, and HOSTILE-SUBCLASS cells (R14-4; `type(x) is` admission, the 0013 authority-regression pattern) | CI |
| **I17** audit failures are loud end-to-end | `test_audit_read_error_is_loud` — a missing record under a record-guaranteed outcome, and a malformed record under ANY outcome, raise `MigrationAuditReadError` whose validated carrier reaches CLI exit 3 with `derived_resulting_state` labeled derived-from-outcome on stderr; the existing `MigrationAuditWriteError` path and the newly-dispositioned `PackageConsistencyError` share the exit-3 loud-escape class, never exit 0. **Gate-extension obligation: the readback boundary, the no-record routing branch, and the mint-retry loop are NEW failure seams — they join `test_every_fault_seam_preserves_the_invariants`'s injection list** | CI |
| **I18** the resolution evidence is reason-labeling only (internal F3; test form corrected by external R2-7 — the v3 regression demanded unconditional refusal, which would itself have made the evidence authority-relevant) | `test_resolution_is_reason_labeling_only` — forged vs genuine `resolved` compared under BOTH real-store conditions: with a VALID store + attestation, mint SUCCEEDS identically under forged evidence (an authority IS granted — forgery must not deny either); with a FAILING store, mint fails identically, and at most the `MintError` reason label differs | CI |
| **I19** the CLI contract | `tests/test_migrate_cli.py`, amended under this spec's authority (§7a): flags required on the migration path (missing → exit 2), invalid `--backup` → exit 2 with the grammar, exits 0/1/2/3 as §4, reporting from structured fields only | CI |

## 7. Failure modes and reversibility

Every preflight interception and every refusal leaves the store
byte-unchanged (zero authorities, zero audit rows) — **except
current-with-repair, the one interception that commits (external R1-7): its
repair rides 0007's own repair-during-opening path and is reported honestly
as (True, True, destination, 7), so reversibility there is 0007's own
contract, not this spec's**. The delegated operation's
failure modes are 0013's own — this spec adds none inside the transaction; it
adds the loud escapes OUTSIDE it, and their loudness is the safety property:
an operator who sees exit 3 has an audit trail needing attention and NEVER a
silent success; the stderr `resulting_state` reports whether the migration
committed WHERE a valid bound record (or the write error's own carried
facts) exists, and prints an explicitly-labeled `unavailable` otherwise
(external R3-5 — a pre-mint package escape and a failed readback have no
commit fact to report, and the CLI never invents one). `mint-contention` is retryable
by construction: nothing was minted, nothing written.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `src/veracium/store/migration.py` | gains `run_release_migration`, `mint_release_authority`, `MintError`, `MigrationAttestation`, `MigrationResult`, `PreflightResolution` (guarded; this spec's authority) |
| `src/veracium/cli.py` migrate verb | re-dispositioned FROM the ce896fc direct-`migrate_store` contract TO the orchestrator: `--i-have-quiesced --backup REF`, exits 0/1/2/3 (this spec's authority — the carriers dev itself froze are re-frozen here) |
| `tests/test_migrate_cli.py` | amended to the new contract, same commit as the CLI change |
| 0013/0007 amendments (marked, §4h — land same-commit with implementation per the 0014 §7b rule) | the RETURNABLE vocabulary +`unsupported-base` +`mint-contention` with the **`TERMINAL_OUTCOMES` split** (both excluded from `TerminalFacts`/terminal publication; the independent oracle extended with the exclusion cells); the shared opening-path **resolution-evidence interface** (the `PreflightResolution` producer); `read_terminal` (record-or-ABSENT) + `MigrationAuditReadError`; the exhaustive outcome tests extended |
| `tests/test_0013_presend_gates.py` | EXTENDED per I15/I17 (oracle enumeration for the result table; fault injections at the readback + mint seams) |
| docs (`docs/api.md` migration section, CLI help) | the flag contract + exit codes |
| MCP / telemetry | **no change** — not exposed, nothing recorded (§3b) |

## 8. Claims and limits

**Claim:** this spec establishes HOW D2 executes — a total, audited,
loud-on-audit-failure orchestration whose every outcome carries
never-inferred facts. It does not alter what D2 *means* (0016's), and nothing
here runs until both specs are accepted (the mutual gate).

**Limits:** the attestation attests what the HOST asserts — `quiesced=True`
from a host that didn't quiesce is a false statement the orchestrator cannot
detect (0013's own boundary, unchanged); `backup_ref` is a token, not a
verified backup. The `resolved` evidence bounds (§2c) hold only while the
I18 pin holds — the pin is the contract, not a hope.

## 9. Brief for the external reviewer

This construction is yours as much as ours: rounds 10–14 of 0016 built it
finding by finding, and §4b folds your round-14 findings. Least sure of:
whether `mint-contention`'s facts row and `MigrationAuditReadError`'s
placement survive the same 0013-instrument scrutiny the rest did.

## 10. Open questions

1. ~~Does the `PreflightResolution` evidence parameter need its own §2c row
   (it is orchestrator-internal, never caller-supplied)?~~ **RULED (research,
   internal round 1, 2026-08-13): YES — "orchestrator-internal" was an
   assumption, not a verified property; the parameter enters the production
   mint API and is therefore caller-suppliable. The row exists (§2c) with
   the bounded-damage analysis and the reason-labeling-only pin (I18).**
   *(The alternative — making `mint_release_authority` non-host-reachable —
   was not taken: §4 expressly defines it as the production surface.)* | resolved |

**No open questions remain.**
