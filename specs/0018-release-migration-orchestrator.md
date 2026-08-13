# Feature spec: the release-migration orchestrator

Spec-Status: draft
Spec-Requires: 0007, 0013, 0016

| | |
|---|---|
| **Author / session** | dev |
| **Version** | v3 — EXTERNAL ROUND 1 (7 bin-(a), bin (b) empty; the split and 0016's frozen surface remain endorsed): ALL SEVEN FOLDED. **R1-1 (class D — the 0015-round-7 layering failure, repeated):** §4 still stated four pieces of superseded v17 machinery beneath the §4b corrections layer (mint without `resolved`; exhaustion returning the final classification; `isinstance` admission; the retired result carrier) → **§4 is CONSOLIDATED into one integrated contract; the corrections layer is gone.** *Miss diagnosed: the split imported v17 §4 verbatim and layered every later fold beneath it; internal F1 fixed one §4↔§4b contradiction — the INSTANCE — and I never diff-scanned the two sections claim-by-claim for the CLASS (checklist item 7). The consolidation is the structural fix; seal ship-checks now assert the superseded forms are absent from this file.* **R1-2 (class A):** `PreflightResolution` was a name → §4b defines fields/immutability/validation/producer, and the marked amendment defines the shared opening-path interface that RETURNS resolution evidence (external round 1 is right that existing 0007 APIs do not). **R1-3 (class F+D):** the table was invalid (`unchanged` is not a 0013 state word) and non-literal → §4e carries the LITERAL complete table over the five-word vocabulary; the surviving retired rule died with the consolidation. **R1-4 (class G+C):** the readback premise contradicted accepted 0013 — four outcomes legitimately return with NO terminal record → §4f's total routing (absent is OUTCOME-CONDITIONAL; internal F1's blanket refined, its dead-branch deletion preserved); `PackageConsistencyError` dispositioned as the third loud escape. **R1-5 (class E+D):** the amendment leaked the two new names into `TerminalFacts` via the default `{unknown}` mapping (reviewer-probed) and still said "one member" → the amendment SPLITS the domain (`TERMINAL_OUTCOMES` excludes both; the oracle extends with the exclusion cells; the probe is the named regression). **R1-6 (class A+F):** `MigrationAuditReadError` gains its executable carrier (fields validated; `derived_resulting_state` from the frozen outcome→states map, labeled derived-from-outcome; the same-connection snapshot claim RETIRED for the real guarantee — append-once immutability). **R1-7 (class D):** §5/§7 now name the one preflight cell that commits (current-with-repair) as the byte-identity exception. |
| **Status** | *narrative only — canonical is the `Spec-Status:` line* |
| **Internal reviewers** | research — round 1 RETURNED + folded (v2); re-review CLEARED 2026-08-13. *(v2 history: F1 readback reconciliation — refined by external R1-4; F2 sections inlined; F3 the `PreflightResolution` §2c row + reason-labeling pin.)* |
| **External review** | ROUND 1 RETURNED 2026-08-13 (package `0018-v2-20260813T1155Z.tar.gz`): 7 bin-(a), folded as v3; round-2 package next |
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
| `mint_release_authority(path, attestation, *, resolved: PreflightResolution) -> MigrationAuthority`, raising `MintError(reason)` | the production mint API; closed reason enum {`source-missing`, `source-unaccepted`, `source-changed`}; every `MintError` reclassifies (≤3), exhaustion → `mint-contention` | the orchestrator; host-reachable (which is why §2c carries its rows) |
| 0013 `Outcome` vocabulary | +2 RETURNABLE members by marked amendment (`unsupported-base`, `mint-contention`) — **and the domain SPLITS: `TERMINAL_OUTCOMES` excludes both; `TerminalFacts`/terminal publication REFUSE them; the independent oracle extends with the exclusion cells** (external R1-5) | 0013's exhaustive outcome tests + the presend-gate oracle, extended |
| `read_terminal(operation_id)` | 0013-amendment readback: own-operation; returns **the record or ABSENT**; a malformed record raises `MigrationAuditReadError`; ABSENT is routed by §4f's outcome-conditional rule; consistency from append-once immutability | the orchestrator's delegated-outcome facts |
| `MigrationAuditReadError` | frozen, validated carrier {`operation_id`, `failure`, `outcome`, `derived_resulting_state` — from the frozen outcome→states map, labeled derived} (§4f) | the CLI's exit-3 stderr; hosts |
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
| **`PreflightResolution`** (the mint API's `resolved=` evidence — **caller-suppliable**: `mint_release_authority` is the production surface, so its parameters are host-reachable; "orchestrator-internal" is not assumed — the F3 ruling) | absent → `TypeError` (required keyword) | wrong type → refused at the boundary | — | **a FORGED resolution.** Bounded damage, stated: forgery can only mislabel a `MintError` *reason* (`source-changed` vs `source-unaccepted`) — the reason triggers a re-resolve (≤3) that authoritatively re-establishes truth, and mint validates path+attestation against the REAL store independently. Forgery cannot corrupt a terminal outcome, skip a validation, or grant an authority; worst case is a misleading diagnostic on an already-failing call | **the load-bearing pin: mint treats `resolved` as reason-labeling evidence ONLY, never authority-relevant — it never skips or weakens any check because of it** (else this row becomes a TOCTOU and security-critical); `test_resolution_is_reason_labeling_only` (forged resolution → identical validation behaviour, no authority, outcome facts unchanged) |
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

The preflight's observation, as an immutable evidence carrier:

- **Fields, exactly:** `canonical_path: str` (the resolved absolute path, as
  the shared opening path canonicalises it), `resolved_base: int` (the
  accepted base the shape resolution established), `source_fingerprint: str`
  (64 lowercase hex — SHA-256 over the resolution's own evidence: the
  stamped `user_version` and the ordered `(type, name, normalized column
  list)` shape set 0007's names+columns resolution already computes; the
  digest is length-framed and domain-separated per accepted 0006's shared
  canonical-digest-primitive rule, §4 rule 7 there).
- **Representation:** a frozen dataclass/NamedTuple; a validating constructor
  refuses an empty path, a base outside the accepted set, or a malformed
  fingerprint. Exact-type admission at every consumer (`type(x) is
  PreflightResolution` — the same rule as the attestation).
- **Producer:** ONLY the shared opening/planner path, which this spec AMENDS
  (in the marked 0013/0007 amendment, §4h) to RETURN its resolution evidence
  to the orchestrator across the total matrix — external R1-2 is right that
  the existing 0007 APIs do not return it; the amendment is the defined
  interface, and the preflight consumes it rather than re-deriving.
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
production surface). **Every `MintError` reclassifies:** the orchestrator
re-runs the preflight (which resolves whatever is now true — a vanished store
→ the missing refusal, a migrated store → `current`), bounded at **3
attempts**. **Exhaustion returns the `mint-contention` outcome** — facts
`(False, False, unknown, None)`, diagnostic naming the three attempts — never
a fourth resolve, never "proceed to mint", and never a bare final
classification (the v17 exhaustion rule is superseded: contention that
persists three rounds is its own honest outcome, not whichever refusal the
last race happened to leave behind). The complete state machine:
resolve → {interception outcome | mint} → mint → {authority | MintError →
re-resolve (≤3) | exhaustion → `mint-contention`} → delegate → §4f routing →
result.

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

**Delegated rows** (base 6; the quadruple comes VERBATIM from the §4f
routing — the terminal record where one exists, the fixed no-record rows
where 0013 defines none). The constructor enforces, for every delegated
carrier: `resulting_state ∈` accepted 0013's frozen
`_OUTCOME_TERMINAL_STATES[outcome]` (absent → `{unknown}`);
`resulting_version` = 7 iff state `destination` and the outcome is
`migrated`/`current`, 6 iff state `source`, else None; `(changed, committed)`
= (True, True) only where state is `destination` under
`migrated`/`internal-error`/`package-inconsistent` (a post-commit discovery),
(False, False) otherwise — no half-commit is representable, mirroring 0013's
own validator. The two literal success rows: `migrated` → (True, True,
`destination`, 7); delegated `current` → (False, False, `destination`, 7).
**No-record rows (fixed):** `migration-audit-unavailable` → (False, False,
`source`, 6) — 0013 defines it as a refusal BEFORE any store access with the
authority NOT consumed, so untouched is contract-proven; `migration-audit-
state-unknown` → (False, False, `source`, 6) with the mandatory retry-unsafe
diagnostic (the authority MAY be consumed — query the durable `operation_id`
before retrying); pre-observation `migration-quiescence-required` /
`migration-evidence-missing` (when §4f finds no record) → (False, False,
`source`, 6). The `source`/6 in these rows is the preflight's own moments-old
observation, carried honestly in the orchestrator's result — the OPERATION
proved only "untouched," and the diagnostic says which facts are whose.
**The v17 `(False, False, resolved-version-or-None)` short-circuit rule is
DELETED — this table is the only rule.**

### 4f. Delegated-outcome routing, the readback, and the loud escapes (external R1-4/R1-6)

**`read_terminal(operation_id)`** (defined in the marked 0013 amendment,
§4h): one SELECT by the operation id, in its own read transaction, returning
**the terminal record, or ABSENT** — consistency comes from 0013's
append-once-per-`operation_id` immutability, NOT from connection identity
(the v2 "same connection after `record_terminal` returns" phrasing is
RETIRED as neither necessary nor sufficient); own-operation binding
unchanged (the orchestrator may read only the id it minted). A **present but
MALFORMED** record (failing the durable-field/`TerminalFacts` validation)
raises `MigrationAuditReadError` unconditionally — a written-but-corrupt
record is never ordinary.

**The routing, total over every delegated return** (this refines internal
F1's option (a): the blanket "absent always raises" was too strong — accepted
0013 defines outcomes that legitimately return with NO terminal record, and
the reviewer ran them; absent is now OUTCOME-CONDITIONAL, while the dead
"audit-unknown fallback" branch of R13-3 stays dead):

1. Kernel returns an outcome → call `read_terminal(operation_id)`.
2. **Record present + valid** → the result's facts come from it verbatim
   (§4e's delegated constraints enforced by the constructor).
3. **Record ABSENT + outcome ∈ the no-record set** — exactly
   {`migration-audit-unavailable`, `migration-audit-state-unknown`,
   `migration-quiescence-required`, `migration-evidence-missing`}, the
   outcomes accepted 0013's own text says "never reach a terminal record"
   in their pre-consumption/pre-observation sites — → the §4e fixed
   no-record row.
4. **Record ABSENT + any other outcome** (consumption implies a record or a
   `MigrationAuditWriteError` — so absence here is audit-integrity loss) →
   **`MigrationAuditReadError`**.
5. **Named escapes propagate, never converted to a `MigrationResult`:**
   `MigrationAuditWriteError` (0013's, unchanged — carrying its own
   `resulting_state`); `MigrationAuditReadError` (below); and
   **`PackageConsistencyError`** (0013's other named escape, previously
   undispositioned): it ESCAPES the orchestrator exactly as it escapes
   `migrate_store` — 0013 already terminal-records it as
   `package-inconsistent` where consumption occurred, and a broken-package
   state must never present as a structured result.

**`MigrationAuditReadError` — the executable carrier (external R1-6):**
frozen fields, all validated at construction: `operation_id` (0013's token
grammar), `failure: "missing" | "malformed"`, `outcome` (the kernel-returned
`Outcome`, ∈ the closed vocabulary), and `derived_resulting_state` — the sole
member of accepted 0013's `_OUTCOME_TERMINAL_STATES[outcome]` when that set
is a singleton (e.g. `migrated` → `destination`), else `"unknown"`. The state
is DERIVED from the frozen outcome→states map and the kernel return the
orchestrator holds — never read from the failed record, never fabricated —
and both the exception's message and the CLI's stderr line label it
`derived-from-outcome` so it is never mistaken for a recorded fact.

### 4g. The CLI contract

`veracium migrate --db X --i-have-quiesced --backup REF` — flags, never
prompts; both required for the migration path (missing → exit 2 with usage);
an invalid `--backup` token → exit 2 with the grammar stated. Exit codes:
**0** = `migrated`/`current` · **1** = every refusal outcome (incl.
`unsupported-base` and `mint-contention`) · **2** = usage / invalid
attestation · **3** = a named loud escape (`MigrationAuditWriteError`,
`MigrationAuditReadError`, `PackageConsistencyError`), with the exception
class and its facts — each state labeled recorded vs derived — on stderr.
Reporting stays on the structured fields; `cli.py` and
`tests/test_migrate_cli.py` are dispositioned in §7a under this spec's
authority.

### 4h. The marked 0013/0007 amendments (land same-commit with the implementation)

> **Outcome vocabulary (revised by external R1-5 — TWO members, and they are
> RETURNABLE, never TERMINAL):** the returnable vocabulary gains
> `unsupported-base` and `mint-contention`, produced ONLY by the release
> orchestrator's preflight/retry machinery before authority minting. **The
> amendment SPLITS the domain:** `TERMINAL_OUTCOMES = OUTCOMES −
> {unsupported-base, mint-contention}`; `TerminalFacts` and terminal
> publication validate against `TERMINAL_OUTCOMES` and REFUSE the two new
> members (the reviewer's probe — `TerminalFacts.problems()` silently
> accepting both via the default `{unknown}` mapping — becomes the named
> regression), and the independent terminal-facts oracle is EXTENDED with the
> two exclusion cells so the exhaustive enumeration proves the refusal.
> Neither member creates an audit row, a permitted-state entry, or a
> terminal-facts mapping. `Outcome` continues to refuse non-members.
> **Resolution evidence:** the shared opening/planner path RETURNS its
> resolution evidence (`canonical_path`, `resolved_base`, the names+columns
> shape set and stamped version it already computes) to the release
> orchestrator across the total matrix — the `PreflightResolution` producer
> interface (§4b). **Terminal-record readback:** `read_terminal
> (operation_id)` per §4f — own-operation, record-or-ABSENT, malformed
> raises; the initiating orchestrator may read only its own operation's
> facts, which are never inferred from the label.

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
| **I14** the mint race closes by reclassification, bounded, total | `test_mint_race_reclassifies` (each `MintError` reason → re-resolve → the now-true outcome) + the exhaustion cell (third failure → `mint-contention`, facts `(False, False, unknown, None)`, three attempts named in the diagnostic — never proceed-to-mint) | CI |
| **I15** `MigrationResult` carriers are table-only | `test_migration_result_truth_table` — the LITERAL §4e table: every preflight row (all fourteen), the delegated constructor laws (state ∈ the frozen map; the version and effect-pair derivations), and the four fixed no-record rows; the validating constructor rejects every out-of-table quadruple incl. every `unchanged`-style non-vocabulary state word. **Gate-extension obligation: the validator joins `tests/test_0013_presend_gates.py`'s independent-oracle pattern — a separately-written oracle enumerates the §4e domain and the exhaustive diff must be empty** | CI |
| **I20** the two new outcomes are returnable, never terminal (external R1-5) | `test_new_outcomes_are_excluded_from_terminal_facts` — the reviewer's probe as the regression: constructing `TerminalFacts` (and attempting terminal publication) with `unsupported-base` or `mint-contention` REFUSES; the extended independent oracle enumerates both exclusion cells; the amendment's `TERMINAL_OUTCOMES` split is asserted | CI |
| **I21** the delegated routing is total (external R1-4) | `test_delegated_routing_total` — for EVERY member of 0013's returnable vocabulary as a delegated return: record-present → facts verbatim; record-absent × the four no-record outcomes → the fixed rows, NO error; record-absent × every other outcome → `MigrationAuditReadError`; malformed record × any outcome → `MigrationAuditReadError`; `PackageConsistencyError` propagates uncaught | CI |
| **I16** the attestation contract is exact | `test_attestation_contract` — absent, coerced (`quiesced=1`/truthy object), grammar-violating (incl. embedded space), duck-typed, and HOSTILE-SUBCLASS cells (R14-4; `type(x) is` admission, the 0013 authority-regression pattern) | CI |
| **I17** audit failures are loud end-to-end | `test_audit_read_error_is_loud` — a missing record under a record-guaranteed outcome, and a malformed record under ANY outcome, raise `MigrationAuditReadError` whose validated carrier reaches CLI exit 3 with `derived_resulting_state` labeled derived-from-outcome on stderr; the existing `MigrationAuditWriteError` path and the newly-dispositioned `PackageConsistencyError` share the exit-3 loud-escape class, never exit 0. **Gate-extension obligation: the readback boundary, the no-record routing branch, and the mint-retry loop are NEW failure seams — they join `test_every_fault_seam_preserves_the_invariants`'s injection list** | CI |
| **I18** the resolution evidence is reason-labeling only (internal F3) | `test_resolution_is_reason_labeling_only` — a forged/mismatched `PreflightResolution` changes NO validation outcome, grants NO authority, alters NO facts; at most the `MintError` reason label differs, and the re-resolve then re-establishes truth | CI |
| **I19** the CLI contract | `tests/test_migrate_cli.py`, amended under this spec's authority (§7a): flags required on the migration path (missing → exit 2), invalid `--backup` → exit 2 with the grammar, exits 0/1/2/3 as §4, reporting from structured fields only | CI |

## 7. Failure modes and reversibility

Every preflight interception and every refusal leaves the store
byte-unchanged (zero authorities, zero audit rows) — **except
current-with-repair, the one interception that commits (external R1-7): its
repair rides 0007's own repair-during-opening path and is reported honestly
as (True, True, destination, 7), so reversibility there is 0007's own
contract, not this spec's**. The delegated operation's
failure modes are 0013's own — this spec adds none inside the transaction; it
adds the two loud audit-trail escapes OUTSIDE it, and their loudness is the
safety property (an operator who sees exit 3 has a store whose migration
committed or didn't per the stderr `resulting_state`, and an audit trail
needing attention — never a silent success). `mint-contention` is retryable
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
