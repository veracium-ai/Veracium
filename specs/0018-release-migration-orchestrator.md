# Feature spec: the release-migration orchestrator

Spec-Status: accepted
Spec-Requires: 0007[0013/0007-sqlite-attestation], 0013[0013/0007-sqlite-attestation], 0016
Folds: 0044/0018-data-migration, 0013/0007-sqlite-attestation

| | |
|---|---|
| **Author / session** | dev |
| **Version** | **v8.1 — 2026-11-01: the amendment's implementation acceptance, recorded (0007 v24's acceptance fold).** The SQLite attestation amendment `0013/0007-sqlite-attestation` was IMPLEMENTATION ACCEPTED at its external round 5, 2026-10-31. Its record is in 0007 v24 and 0007 `## Review closure`, and the Decision cell now says so. Nothing else changes; `Spec-Status` stays `accepted`. Prior: **v8 — 2026-10-25: the SQLite attestation fold (amendment `0013/0007-sqlite-attestation`, v0.12.1, sha16 `134243c63b05845a`): the preflight's runtime case and the migration audit's sidecar writer (§4a), edited in place; the amendment itself is 0007 §4g and 0013 §5f.** Prior: **v7 — THE DATA-MIGRATION FOLD (amendment `0044/0018-data-migration`, v4, sha16 `c09a4aed2db848a9`).** Its design was accepted with 0044 at round 4 of the 0044 package (verdict 2026-10-13: I24–I32, with I13–I23 kept), and the owner ruled “Accept now, fold next” (2026-10-14). It adds a per-user data-migration operation BESIDE the release orchestrator, which it leaves untouched. Folded as §4i, labelled by the amendment's own section numbers so its internal references resolve; pointers added at §2, §6 and §8. Its reach rows are re-derived at `af1e564`. Not folded: its review brief, open questions and version history. Prior: **v6 (ACCEPTED)** — EXTERNAL ROUND 4: **APPROVED FOR ACCEPTANCE under the finite-acceptance rule; the frozen surface is I13–I23** (total preflight · the exact retry sequence · the result truth table · exact attestation · loud audit failures · reason-only resolution evidence · the CLI contract · the terminal-domain split · total routing · the fingerprint encoding · the closed readback carrier). v6 = v5 + the four same-commit CLOSURE OBLIGATIONS, each demonstrated in this revision: (1) the R3-2 sweep COMPLETED — the §2c cell's test clause now carries I18's two-condition expectation (the description half was fixed in v5, the test half still said "no authority"); (2) exactness made RECURSIVE — `ReadbackResult` requires `type(facts) is TerminalFacts` and invokes `TerminalFacts.problems(facts)` UNBOUND (the reviewer's dynamic-validator subclass probe is the named regression), and `PreflightResolution` exact-types every scalar before any comparison (`resolved_base=True` refuses; hostile `str` subclasses refuse) — I18/I23 extended; (3) read-level failure TOTALITY — `malformed(problems)` is the total read-failure arm (`read-failed: <class>` bounded entries; forced-read-failure regression), and the `ReadbackResult` row is IN §7a (v5 had put it in §2 while claiming §7a complete); (4) the R3-5 output sweep FINISHED — the false "store not accessed" clause removed (the preflight reads the manifest), and §4g/I19 enumerate the five package routes. The reviewer's verification: the corrected fingerprint EXECUTED and matched an independent encoder; the suite delta reconciled exactly; B3-1 closed. **Acceptance is ATOMIC with 0016 v18 (this commit flips both).** *(v5 history: external round 3 — 5+1 folded: the executable fingerprint via `identity(manifest())`, the swept §2c/I14 carriers, the constructed `ReadbackResult`, the pre-mint package route, the MCP gate-scope correction.)* |
| **Status** | *narrative only — canonical is the `Spec-Status:` line* |
| **Internal reviewers** | research — round 1 RETURNED + folded (v2); re-review CLEARED 2026-08-13. *(v2 history: F1 readback reconciliation — refined by external R1-4; F2 sections inlined; F3 the `PreflightResolution` §2c row + reason-labeling pin.)* |
| **External review** | **ROUND 4: APPROVED FOR ACCEPTANCE** (2026-08-13, package `0018-v5-20260813T2202Z.tar.gz` sha `107e7720…`) — findings 3(int)/7/9+1/5+1/0; the four closure obligations folded same-commit with the flip |
| **Decision + date** | **ACCEPTED 2026-08-13** — external round 4, under the finite-acceptance rule; the frozen surface is I13–I23; ATOMIC with `0016` v18 (commit `32faaa8`). *(Row filled 2026-08-22 — the audit also found this round's VERDICT was never recorded in `specs/reviews.py`; recorded now.)* **v7, 2026-10-14:** the amendment `0044/0018-data-migration`, accepted with 0044 at round 4, folded on the owner's ruling “Accept now, fold next”. · **v8: the amendment's design accepted** (its round 2, 2026-10-25, and the owner's word); implementation acceptance was outstanding until 0007 v24 (its obligations are in 0007 `## Review closure`; 0018's invariant ids are its own, so they are not repeated here) · **the amendment's IMPLEMENTATION ACCEPTED** at its external round 5, 2026-10-31 (recorded in 0007 v24) |
| **Path** | full |

---

> **Amended by 0020/0021 (same-commit with the coupled acceptance flip,
> 2026-08-16; external sign-off at review round 14; research's cross-spec
> sign-off at `veracium-research/proposals/0020-0021-rider-signoff.md` @
> 023e11a9; the drafted rider row of 0021 §7b, landed verbatim).** drafted
> rider to the frozen v7 export shape, same-commit landing at acceptance:
> exported edge records MAY carry `absorbed_by_id` (string; present iff the
> record is an `absorbed_duplicate` with a unique CANONICAL ledger row —
> direct or reparented — naming it, per 0020 §4a-iii's `derive_absorbed_by`;
> NEVER derived from notes); importers of v7-with-rider files consume it as
> 0020 §4a-iii's structured carrier; files without it take the legacy note
> rule. The rider rides the SAME 0018 D2 breaking window as the SCHEMA-v8
> ledger columns (the 0019 rider below) and 0021's writer-version enforcement
> (Q4) — ONE break carries all three; none of the three mints its own window.
> Legacy-export refusal behaviour is 0020 §4a-iii's decidable rule (ambiguity
> → whole-import refusal)

> **Amended 2026-09-18 (the owner's word in the dev session; no frozen surface
> I13–I23 changes).** The `unsupported-base` DIAGNOSTIC is **derived**, not static:
> from the resolved base, the mint base (`HEAD-1`) and the shipped release record
> it states the resolved base, the number of one-version rungs a CLI ladder would
> need, which of those rungs the shipped release record names no release for, and
> the offline library route (`migrate_store`) that applies every step in one call.
> The 0019 rider's literal ladder sentences below ("migrate to v6 on a ≤0.8.x
> release …") described head 8 and are HISTORICAL: once the head moved past 8 the
> code still recited them, naming "v6" for every base above 5 and sending an
> operator to releases chosen for a v8 head. §3's "static ladder
> text" reads "derived version-only text" — it carries versions and release tags,
> never store content, so the disclosure class is unchanged. Facts, outcome, exit
> code and the §4e table are untouched. Tested exhaustively over every base
> 1..HEAD-2 with the literal text kept as the mutant.

> **Amended by 0019 (same-commit with 0019's acceptance; sign-off granted
> round 4, 2026-08-14).** (B1) §4a, final: the preflight intercepts
> everything except resolved base **7**; bases **1–6** → `unsupported-base`
> with the ladder diagnostic (bases 1–5: migrate to v6 on a ≤0.8.x release,
> then to v7 on a 0.9.x/0019-era release, then run this release's migration;
> base 6: migrate to v7 on a 0019-era release first); already-current **v8**
> clean → `current`; **v8** with rebuildable drift → `current` with the
> repair facts; resolved base **7** ALONE proceeds to minting. (B2) §4e's
> literal table, final numerals: `unsupported-base` carries the resolved
> base **1–6**; the two `current` rows carry resulting_version **8**; every
> other row is unchanged in facts and label. (B3) I13 is parametrized over
> bases **1–6**; the below-base tests read below-v7. (B4) Every other
> frozen surface carries no version numerals and is unchanged — asserted by
> 0019's executable numeral sweep, whose output ships in the acceptance-flip
> commit. The body text below is HISTORICAL as-frozen; this rider is the
> operative numbering.

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

**v7:** a per-user data-migration operation is added beside the orchestrator, with its own schema step, result carrier, receipt and `doctor` check (§4i.2); the orchestrator, `MigrationResult` and I13–I23 are untouched.

## 2c. Untrusted inputs — REQUIRED, blocking

*(The below-v6 and attestation rows are the 0016 v17 rows, reviewed in its
rounds 10–14, transferred; the `PreflightResolution` row is NEW — the F3
ruling.)*

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant that pins it |
|---|---|---|---|---|---|
| `path` (caller-supplied) | missing file → the missing refusal outcome, no minting | foreign/malformed/unstamped → the corresponding 0007/0013 refusal outcome, no minting | newer-than-head → the newer refusal, no minting | a path racing with concurrent writes | the preflight matrix is TOTAL (I13); the preflight→mint race closes by reclassification (§4c), never by trusting the first resolution |
| a stored below-v6 database (bases 1–5) presented post-D2 | — | — | ordinary OPEN → 0013's existing below-head refusal, unchanged by this spec | the migration ORCHESTRATOR'S PREFLIGHT → the `unsupported-base` outcome (returned, never raised), the ladder diagnostic, NO authority, ZERO 0013 audit rows, bytes+stamp unchanged | I13; `test_below_v6_base_refuses_with_the_ladder_message` (all five bases) + `test_below_v6_open_unchanged` |
| `MigrationAttestation` (caller-supplied — the host-owned facts) | absent → `TypeError` (required keyword) | `quiesced=1`/truthy-object → refused (`is True` check); empty/whitespace `backup_ref` → `ValueError` | unknown extra fields → refused (immutable, exact) | a hostile SUBCLASS (attribute-interception) or duck-typed carrier | **exact-type admission `type(x) is MigrationAttestation` (R14-4 — 0013's own authority regression); duck-types and subclasses REFUSED, never copied; `backup_ref` validates with 0013's own token grammar**; `test_attestation_contract` (absent, coerced, grammar-violating incl. embedded-space, duck-type, hostile-subclass cells) |
| **`PreflightResolution`** (the mint API's `resolved=` evidence — **caller-suppliable**: `mint_release_authority` is the production surface, so its parameters are host-reachable; "orchestrator-internal" is not assumed — the F3 ruling) | absent → `TypeError` (required keyword) | wrong type → refused at the boundary | — | **a FORGED resolution — analyzed in I18's two-condition form VERBATIM (external R3-2; the prior cell's "cannot grant an authority" contradicted I18):** with a VALID store + attestation, mint SUCCEEDS identically under forged evidence (an authority IS granted — forgery must not deny either); with a FAILING store, mint fails identically and at most the `MintError` reason label differs, and the re-resolve then re-establishes truth. Forgery cannot corrupt a terminal outcome or skip a validation; worst case is a misleading reason label on an already-failing call | **the load-bearing pin: mint treats `resolved` as reason-labeling evidence ONLY, never authority-relevant — it never skips or weakens any check because of it** (else this row becomes a TOCTOU and security-critical); `test_resolution_is_reason_labeling_only` — I18's two-condition expectation verbatim: valid store + attestation → mint SUCCEEDS identically under forged evidence; failing store → fails identically, at most the reason label differs (closure obligation 1: the description half of this cell was corrected in v5, the test half still said "no authority") |
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

**v8 (amendment `0013/0007-sqlite-attestation`; 0007 §4g, 0013 §5f):** `unqualified-runtime` is a build whose `runtime_status()` is `refused`: the preflight's outcome is `unsupported-sqlite` only on `refused`, and an `attested` or `verified` build proceeds as above. The migration audit's sidecar writer copies the `attempted` event's additive key (INV-SA11, 0013 §5e).

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
  EXACT-TYPES every scalar BEFORE any membership, regex, or comparison
  (closure obligation 2 — recursive exactness): `type(canonical_path) is
  str`, `type(resolved_base) is int` (so `True`, an int subclass, refuses),
  `type(source_fingerprint) is str` (hostile `str` subclasses refuse before
  their methods can run); then refuses an empty path, a base outside the
  accepted set, or a malformed fingerprint. Exact-type admission at every consumer (`type(x) is
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
cross-field laws TOTAL and constructor-enforced: `kind=="record"` ⇔
`type(facts) is TerminalFacts` (EXACT type — closure obligation 2: the
reviewer's probe built a subclass whose overridden `problems()` validated
invalid facts) ∧ **`TerminalFacts.problems(facts)` invoked UNBOUND** (the
base validator, never the instance's — an override cannot answer) returns
empty ∧ `problems == ()`;
`kind=="absent"` ⇔ `facts is None` ∧ `problems == ()`; `kind=="malformed"`
⇔ `facts is None` ∧ `problems` non-empty — **and `malformed` is the TOTAL
read-failure arm (closure obligation 3): a failed SELECT, a failed open, or
a failed read transaction maps to `malformed` with a bounded problem entry
naming the failure class (`read-failed: <class>`), so the raise-nothing
promise holds over every read outcome, not only retrieved-or-absent rows; a
forced-read-failure regression is the named I23 cell.** `problems` is an IMMUTABLE tuple
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
   unavailable (pre-mint: no operation minted)`
   — the earlier "store not accessed" clause is REMOVED (closure obligation
   4: the preflight already read the store's manifest, and the accepted
   authority path reads it again before a release-identity failure — the
   clause was false);
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

---

## 4i. The per-user data-migration operation (v7, amendment `0044/0018-data-migration`)

> **What this section adds:** `run_data_migration`, a per-user data-migration operation BESIDE the release orchestrator (which §4a–§4h keep unchanged, with I13–I23), for 0044's restoration; its closed result carrier, its receipt read, `doctor`'s `data-migration` check, and the v15 → v16 schema step that creates its tables. **Within this section, a reference to “§1”–“§8” or “§4a”–“§4f” means the subsection labelled with that number here** (the amendment's own numbering, kept so its references resolve); a reference to 0018's own sections says “0018”.

### 4i.1 Why (the amendment's §1)

0044 restores rows that a superseded arity rule retired, and names each in a receipt (the owner's (b), 2026-10-10).
Round 1 found that "once per user" had no execution contract (R1-03): the accepted 0018 orchestrator short-circuits a
current store (`current`, no effect), its kernel migration is ONE store transaction, its `MigrationResult` table is a
closed domain (I15), and it takes no registry — while 0044 needs per-user transactions, resumability, a durable
receipt, and the host's effective registry (R1-06).

**Alternatives rejected.** *Extend the orchestrator* — amends frozen I15 and §4a's interception rule and couples a
multi-transaction operation to a single-transaction kernel (rejected by 0018's owner). *Do it inside the schema step*
— a 0013 step cannot see the host's registry. *Make it mandatory at open* — the owner chose optional (§5).

### 4i.2 Field contracts (the amendment's §2)

| site | change |
|---|---|
| 0013's schema-step chain (`_apply_forward`, `migration.py` L105) | **gains step v15 → v16**: creates `migration_run` (each row naming the `op_id` that committed it), `migration_outcome`, `reclassification_plan`, the plan header (0044 §4e, with the `op_id` that wrote it), `migration_op` (the admission record, §4b, v4), and the two inventories, which it WRITES (§4a, R2-01); stamps `arity_effective_at` (the step's commit time). One transaction, through `migrate_store` — 0013's existing contract, unchanged |
| `run_data_migration` *(new)* | §4b |
| `DataMigrationResult` *(new, closed)* | §4c |
| `data_migration_receipt` *(new, read-only)* | §4d |
| `doctor` (`doctor.py`) | **gains a check `data-migration`** (§4e) |
| `run_release_migration`, `MigrationResult`, I13–I23 | **untouched** |

### 4i.3 Untrusted inputs (the amendment's §2c)

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant** |
|---|---|---|---|---|---|
| `path` | refused (0018's preflight cells) | same | same | same — the shared opening path, unchanged | 0018 I13 (reused, not amended) |
| `host_attestation` (`MigrationAttestation`, exact-typed, `release_migration.py` L586) | refused (0018 I16) | refused | refused | a coerced or duck-typed attestation is refused, as 0018 requires | I16 (reused) |
| `op_id` (host-supplied; v4) | refused | outside §6c's caller grammar → refused AT ENTRY, before any read or write, with no result constructed (0008 C9's discipline; §4c's constructor row 8 is the same rule at the carrier) | — | a held id with different inputs → `op-id-conflict` (§4b.1b) | **I32** |
| `registry` (the host's effective relation registry) | refused — the plan cannot be made without it | refused by 0025's validator | — | a registry that changes between the plan and a later call: the plan is written ONCE per store and reused; a second call with a different registry is refused with both digests named | **I25** |
| data written by an older version | — | — | — | the eligibility rules (0044 §4f); never re-derived from episodes | 0044 |

### 4i.4 Assertions about reach (the amendment's §2c-ii)

Commands run from the repository root at `af1e564` (research, 2026-10-14). **READ** = the cited lines or signature.

| # | assertion | command | result |
|---|---|---|---|
| 1 | the orchestrator takes no registry | `grep -n "def run_release_migration" src/veracium/store/release_migration.py` | READ: `(path, *, host_attestation)` |
| 2 | the kernel migration takes no registry | `grep -n "def migrate_store" -A2 src/veracium/store/migration.py` | READ: `(path, *, audit_sink=…)` |
| 3 | the store is at schema v15 | `grep -n "^SCHEMA_VERSION" src/veracium/store/schema_version.py` | READ: `SCHEMA_VERSION = 15` |
| 4 | 0018's result table is a closed domain | `grep -n "rejects every carrier not in the table below" specs/0018-*.md` | READ: L307 in this document as folded (L304 before the fold), §4e (the sentence continues "— the table IS the domain" on the next line) |

### 4i.5 Trust classes, authorization and scope (the amendment's §3 and §3b)

n/a for the operation itself — it reads no trust class and writes none: each restoration is 0044's row operation,
whose matrix (0044 §3) governs. The schema step creates empty tables and a timestamp.

Host-only (a store path and an attestation); not MCP. Per user inside; no cross-user effect. The receipt read
returns one user's outcomes.

**Why 0018's quiescence attestation, for an optional operation (dev's question).** Not for correctness: per-user
`BEGIN IMMEDIATE` is correct online — a revocation committed before a user's transaction is read under the lock
(0044 §4f step 2), and one committed after reaches the now-active row through the revocation sweep. The reason is the
attestation's **backup reference**: this is a bulk restoration of a known SUPERSET (correctly replaced values come
back), and a pre-run backup is the only whole-store undo. **Kept (D3, dev as 0018's owner, 2026-10-11).** *The trade,
stated: an online variant without the attestation would be cheaper and correct, but would lose the bulk undo for a
host whose receipt shows the superset went worse than expected; the per-row undo is the only other way back. Because
the operation is optional and run deliberately, asking for a backup at that moment is proportionate. *The attestation is a host ASSERTION with a backup reference, not proof that the backup is usable (round 2).* §9 asks the
reviewer whether an online variant should ALSO exist (not blocking).*

### 4i.6 Behaviour (the amendment's §4)

##### 4a. The schema step v15 → v16

Creates the feature's tables and records `arity_effective_at`. **In the same transaction it writes the two
inventories (R2-01; 0044 §4f):** `arity_inventory`, every retirement that is at that moment
`superseded` under the three default relation names, as `(edge_id, user_id, pre_invalidated_at, pre_reason)`; and
`refusal_inventory(refusal_id, user_id)`, the `supersession_refusals` rows that exist. They are the operation-era boundary: a retirement is old-policy iff it was
committed before this transaction, which no timestamp can show. No edge is changed. Ordinary opening of a v16 store is
unchanged in every other respect.

##### 4b. `run_data_migration(path, *, host_attestation, registry, op_id, plan_only=False) -> DataMigrationResult`

1. **Preflight** through the shared opening path, with 0018's attestation contract: the same refusal cells as
   0018 §4e's preflight rows, returned in `DataMigrationResult` (§4c). A store below v16 → `requires-schema-step`.
1b. **Admission of the `op_id` (v4; the owner, 2026-10-13).** `migration_op(op_id, mode, inputs_digest,
   admitted_at)` is the durable admission record. `mode` is `plan_only` or `restore`. `inputs_digest` is the canonical
   digest of the operation's inputs: §4b.2's plan-input digest and the mode. *The attestation is not an input: it
   asserts quiescence at the moment of a call, and a resume legitimately carries a fresh one.* Under the write lock:
   - an `op_id` with no record → the record is written, in the transaction of the call's first durable write (the
     plan, or the first user), so a call that is refused before writing leaves no record;
   - a held `op_id` with an EQUAL `inputs_digest` → the same operation: it RESUMES, retrying exactly the users with no
     run row under it;
   - a held `op_id` with a different digest, a different mode included → **`op-id-conflict`**, refused, nothing
     written. So plan-only and restoration never share an id, and a changed request under a reused id never runs.
   - **A call that writes nothing writes no record** (`complete`, `already-planned`, `registry-changed`, an all-failed
     call over an existing header, any refusal). Its `op_id` stays free, and `data_migration_status` returns
     `unknown-op` for it. This is consistent: such a call changed nothing, so there is nothing to recover.

   *It holds no user content*: an id, a mode, a digest of declarations, a time. Its per-user part is the run rows,
   which name the `op_id` and are erased with their user under the 0008 amendment's one erasure rule. **Retention:**
   the record lives as long as the store. It is a few bytes per operation, and keeping it is what makes a reused id
   conflict instead of silently starting a second operation.
2. **The plan**, one transaction: if no plan HEADER exists (0044 §4e: uninitialized), write the header and the plan's
   relation rows from `registry` (0044 §4e's rule: a relation enters
   the plan only if its declaration is canonically the default) with `effective_at = arity_effective_at` and
   `registry_digest` — **a digest of the plan's INPUTS only: the canonical declarations of the three reclassified
   relations** (D2), so an unrelated registry edit never trips it. *v4 (R3-03): for example, changing `works_as` from
   single to multi leaves the digest equal, and the call is admitted. Hashing the whole registry is the mutant.* **The plan is fixed at its first write (A3):** a
   later call whose digest differs returns `registry-changed` (refused, both digests named) and changes nothing. *No
   re-plan operation: a host that later changes those three declarations keeps the plan it first ran under; the
   refusal is rare because only those three declarations count, and permanent by design.* **The header is written
   even when no relation qualifies** (initialized-empty, R2-02): that decision is durable, so a later call with the
   defaults finds it and is admitted or refused by digest, never re-planned. Two concurrent first calls produce one
   header (0044 §4e's admission).
3. **The per-user phase:** for each user lacking a `migration_run` row, ONE transaction (`BEGIN IMMEDIATE`): evaluate
   0044 §4f's eligibility under the lock; apply restorations; write `migration_outcome` rows and the run row; commit.
   **A failing user does not stop the phase (D1):** its transaction rolls back, it gets no run row, the failure is
   recorded in the result, and the phase continues with the next user. A re-call retries exactly the users with no
   run row. *Stopping would let one user's bad data hold every later user's restoration hostage.*
   *Annotation (research, 2026-10-16; the step above is kept as written): the users of this phase, and §4e's users lacking a run row, are the users holding at least one `arity_inventory` row, read when the call or `doctor` reads and re-checked inside each user's transaction. This operation considers only inventoried rows (0044 §4f; an imported row is converted at import, 0044 §4l), so a user with none has nothing it could restore: a user created at v16, or a recreated user (0044 §4g-ii), gets no run row and no `doctor` warning, and a user whose last inventory row is erased before its transaction is skipped with no run row. A full call that finds no such user returns `planned` if it wrote the header, else `complete`. Reference model I took every user with edges; under that set, a user created after a completed run kept `doctor` warning until a re-run committed an empty run row reported as `migrated`. Found at T6's stage-1 read; the model is edited to match; §4c's v4 enumeration figures describe the model before the edit, and are re-derived on the edited model.*
4. Returns per-user counts and the operation id. **Idempotent:** a second call with the same registry finds every
   user complete and returns `complete` with zero new effects.

**PLAN-ONLY (`plan_only=True`; the owner, 2026-10-12T23:03Z, Q9).** Steps 1 and 2 only, under the same host
attestation: the plan header and its relation rows are written (or an existing header is admitted or refused by
digest), and **nothing is restored**: no per-user phase, no `migration_outcome`, no run row. It is the prerequisite
0044 §4l's import refusal names, so an importer of a pre-arity file can plan without running the restoration, which
stays optional. A later call without `plan_only` runs the per-user phase over the plan it finds.

*Annotation (dev, 2026-10-20, T11a; the sentence above is kept as written): under the owner's D3 ruling (0044's annotation), "an importer of a pre-arity file" reads "an importer of a file whose store had not decided its restoration, carrying a candidate row" — the only file 0044 §4l refuses into an uninitialized store.*

##### 4c. `DataMigrationResult` — a TOTAL, closed carrier (R2-03)

**The carrier:** `outcome`, `store_changed`, `plan_written` (this call wrote the plan header; a REQUIRED field, v4),
`committed` (the users whose transaction committed in THIS call), `failed` (each failing user, named), and `op_id`. `store_changed` is
DEFINED as "this call changed durable state": a written header, or ≥1 committed user. It is never inferred from the
outcome name alone.

| outcome | store changed | meaning |
|---|---|---|
| `requires-schema-step` | False | the store is below v16 |
| 0018's preflight refusal cells (`preflight-refused`) | False | unchanged meanings, the attestation's included |
| `registry-changed` | False | §4b.2: a header exists with a different input digest |
| `op-id-conflict` | False | §4b.1b (v4): the `op_id` is held with a different inputs digest or mode; nothing written |
| `planned` | True | this call wrote the plan header (with its relation rows, possibly none) and restored nothing: `plan_only`, or a full call that found no user to process |
| `already-planned` | False | `plan_only`: a header with an equal digest already existed; nothing written |
| `complete` | False | a full call: the header already existed and every user already had a run row; nothing written |
| `migrated` | True | ≥1 user committed in this call, none failed |
| `partial` | True | ≥1 user committed and ≥1 user's transaction failed; each failure named; a re-call retries exactly the failed users |
| `failed` | **= `plan_written`** | 0 users committed and ≥1 failed; each named. **Not `complete`:** v2's table had no row for this, so an all-failed call had no truthful outcome. Its `store_changed` is True exactly when this same call wrote the header, which happens on a first call |

**A validating constructor rejects any other carrier** (the I15 discipline). Stated as a matrix (v4, R3-03), it
rejects:

| # | rejected carrier |
|---|---|
| 1 | an `outcome` outside the ten rows above |
| 2 | a missing field, `plan_written` included |
| 3 | `store_changed ≠ (plan_written ∨ committed ≠ ∅)` |
| 4 | `failed ≠ ∅` on any row but `partial` and `failed`; `failed = ∅` on those two |
| 5 | `committed ≠ ∅` on any row but `migrated` and `partial`; `committed = ∅` on those two |
| 6 | `committed ∩ failed ≠ ∅` |
| 7 | `plan_written` true on `requires-schema-step`, `preflight-refused`, `registry-changed`, `op-id-conflict`, `already-planned` or `complete`; false on `planned` |
| 8 | an `op_id` outside §6c's caller grammar |

Every row of the outcome table, with its own consistent fields, constructs (the positive control).

**The two lists say different things (v4).** A result's `committed` names the users committed by THIS invocation.
`data_migration_status(path, op_id)` returns the operation's CUMULATIVE durable commits, over every invocation under
that `op_id`.

**After an unknown return** (a crash or a lost connection after some commit): every commit is durable on its own, so
nothing is lost, and the host recovers what happened from durable facts alone. `data_migration_status(path, op_id)`
returns `{plan_written_by_op, committed}`, read from the header's `op_id` and the run rows that operation wrote (all of
its invocations), or `unknown-op` when no admission record holds the id. A user
it did not commit reads as not run: a failure is not durable, and a re-call retries it. **The `op_id` is supplied by
the HOST** (an idempotency key in §6c's caller grammar), so the host can name the operation it lost the answer to.

*v4: dev's model enumerates **900 schedules**, with the admission record's dimension (a held `op_id`: none, equal,
different digest or mode), and all ten outcomes are reached. The enumeration is BOUNDED: an earlier call's failures
are INV-M25's own check (resume after failure), not the enumeration's. The paragraph below is v3's account.*
*v3: dev's model enumerated 360 cases: v16 or not × attested × the header before (none, equal,
different) × `plan_only` × 0–3 users × every failing subset. In every case the outcome is a row of this table,
`store_changed` equals whether durable state changed, the named failures equal the failing users, and the status read
recovers the commits from durable facts alone. All nine outcomes are reached. Its mutants: `store_changed` set only
when a user committed (which misreports `planned`), and no `failed` row (an all-failed call read as `complete`).*

##### 4d. `data_migration_receipt(path, plan_id, user_id)`

A read of `migration_outcome` for that user: every considered row with its outcome, pre-state, successor evidence and
undo state. **Object text is read from the live edge at call time** (a redacted edge returns the marker) (A4). An absent edge
renders `no longer held` from the outcome row alone. That is defensive: at the pin no public path removes one edge
while its user is retained (0044 §4g-ii). **User erasure ends the receipt (R2-07):** `forget_user` deletes the
user's `migration_outcome`, `migration_run`, `arity_inventory` and `refusal_inventory` rows, and their
request-registry rows, atomically, under the
0008 amendment's single erasure rule. Replay and once-per-plan end there, and a recreated user restores nothing.
*v2's “the outcome row itself stays” is withdrawn: it would have kept user-linked metadata past erasure.* *Available
at any time after the user's commit — a crash after commit loses nothing, because there is no separate delivery
state (R1-03's "receipt after commit, before delivery").*

##### 4e. `doctor`'s `data-migration` check — two phases (A1)

`doctor` takes no registry, and before the operation runs no plan exists, so the check cannot know eligibility. Its phase is read from the plan HEADER (0044 §4e), so an empty plan is a state of its own.

| phase | predicate | finding |
|---|---|---|
| **uninitialized: no plan header** (v16) | members of the schema step's `arity_inventory` (§4a) under the three DEFAULT relation NAMES whose current retirement still equals the inventoried one (0044 §4f's test, v4: no time is compared) — **name-only, and stated as such** | **warn**: `may have values to restore (judged by relation name): run run_data_migration(path, host_attestation=…, registry=…) — see 0044. A host whose registry keeps a custom single-value declaration for these relations will find none eligible.` |
| **initialized-nonempty, some users without a run row** | the plan's relations; users lacking a run row | warn, naming the count of incomplete users and the operation |
| **initialized-nonempty, all users complete** | — | none |
| **initialized-EMPTY** (a header, no relation rows; R2-02) | — | **info**: `data migration planned: no relation was reclassified (this host's own declarations keep them single-valued); nothing to restore` — never the pre-plan warning, which a completed empty plan used to leave in place |

*The warning names the operation to run (the owner's ruling). The name-only predicate is acceptable for a WARNING —
never for eligibility, which is the plan's (0044 R1-06).*

##### 4f. Failure boundaries (R1-03's list)

| boundary | outcome |
|---|---|
| before a user's commit | that user unchanged; `partial` or a re-call resumes |
| after a user's commit, before the caller reads the result | the receipt is recoverable (§4d); a re-call returns `complete` for that user |
| between users | `partial`; resume |
| during a retry | per-user transactions are independent; the run row makes each user's effect once-only |
| unknown result | read `data_migration_receipt` / the run rows; never re-run blind |

### 4i.7 Regimes (the amendment's §5)

| regime | behaviour |
|---|---|
| host runs the operation after upgrading | restorations committed per user; receipts available |
| 🔴 **host never runs it (the owner's choice: optional)** | **the wrongly retired values stay hidden, and no receipt ever exists for that store**; `doctor` warns for as long as eligible rows remain. *The owner accepted this cost explicitly (2026-10-11).* |
| new store created at v16 | no eligible rows; the check finds none |
| multi-user store, partially migrated | resumable; per-user completion |

### 4i.8 Invariants (the amendment's §6)

| | invariant | check, and the mutant it must fail on |
|---|---|---|
| **I24** | the schema step changes no row | v15 store with data → v16: every edge byte-identical. Mutant: restore inside the step → FAILS |
| **I25** | the plan is written once, from the registry, and a change to the THREE reclassified declarations is refused, while any other registry change is admitted (§4b.2's narrow digest) | Mutants: rewrite the plan on each call; hash the whole registry (`works_as` single → multi then returns `registry-changed`, the round-3 witness) → each FAILS |
| **I26** | each user's restorations, outcomes and run row commit together or not at all | inject a failure mid-user. Mutant: two transactions → FAILS |
| **I27** | the run row makes a completed user's re-call return `complete` and leaves `doctor` quiet for that user | Mutant: drop the run row → a re-call reports `migrated`/work for completed users and `doctor` keeps warning → FAILS. *Correctness after an undo is NOT this row's: "never re-applies after an undo" is 0044 §4f step 3's outcome-row check and its own invariant (A2; the model's F6)* |
| **I28** | the receipt is recoverable after commit with no delivery state | crash after commit; read the receipt. Mutant: a receipt held only in the return value → FAILS |
| **I29** | `DataMigrationResult` is TOTAL over the operation's domain and closed: every reachable call yields a row of §4c, its `store_changed` equals whether durable state changed, its failures name the failing users, and `data_migration_status` recovers the commits from durable facts (R2-03) | the model's enumeration over the operation's domain (INV-M15), AND the constructor's rejection matrix (§4c), with every listed row constructing as the positive control. Mutants: `store_changed` set only when a user committed (misreports `planned`); no `failed` row (an all-failed call reads `complete`); an unlisted carrier constructs (round 3's `_result('unlisted', …)`); the carrier omits `plan_written` → each FAILS |
| **I32** | **(v4)** an `op_id` is bound to its inputs digest and mode by a durable admission record: equal inputs resume, a different digest or mode refuses with `op-id-conflict` and writes nothing, the status read returns cumulative commits for the operation, and the record holds no user content | Mutants: grammar-only idempotency (a changed request under a reused id runs); one id admitted for plan-only then for restoration; status returns only the last invocation's commits → each FAILS |
| **I30** | `doctor` warns in both phases (§4e), names the operation, and states the name-only predicate before a plan exists | Mutants: silent → FAILS; a pre-plan warning that claims eligibility → FAILS |
| **I31** | 0018's I13–I23 are unchanged | the existing 0018 tests pass unmodified |

**The gate, stated the same way in 0044, the 0003 amendment and the 0018 amendment (R2-08):** before design acceptance, a row is either a MODEL check or a stated PRODUCT obligation. A MODEL check runs in dev's reference model (`specs/evidence/0044/`): each claimed mutant REACHES its mutated path and is killed SEMANTICALLY, by an owning invariant that returns False. An exception is a harness failure, never a kill, and a mutant may have more than one killing invariant. Which kind each row is is not restated here: `specs/evidence/0044/obligations.py` derives the map from this section, and refuses an unmapped row, a mapping to an invariant that owns no killed mutant, and a model invariant no row claims. It is also the package's review manifest. At the implementation gate, every row is in addition a named PRODUCT test, demonstrated red against its mutant. *I24 and I31 are PRODUCT only: a byte comparison of a real v15 store through the real step, and 0018's existing tests run unmodified.*

### 4i.9 Failure modes, claims and limits (the amendment's §7 and §8)

- **Silent:** a host that never runs it (§5) — warned, not silent to the operator; silent to users.
- **Reversible:** each restoration is undoable per row (0044's undo verb); the schema step is additive.
- **Partial:** per-user transactions; `partial` names the failure; resumable.

**Claimed:** the restoration runs once per user per plan, survives crashes at every boundary with its receipt
recoverable, and never re-applies after an undo. **NOT claimed:** that every store will be migrated (optional, by the
owner's ruling); anything about the release orchestrator, which this does not change.

**Release text (the owner's cost, in substance):** *“Upgrading to this version does not restore values that the old
single-value rule retired. To restore them and get a receipt listing each one, run `run_data_migration`. Until you do,
those values stay hidden and `doctor` warns.”*

---

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
| **I23** `ReadbackResult` is a closed constructed carrier (external R3-4) | `test_readback_result_contract` — every cross-field-law violation, a hostile subclass of `ReadbackResult`, a hostile SUBCLASS OF `TerminalFacts` as `facts` (exact-type + the UNBOUND `problems()` call — the reviewer's dynamic-validator probe as the named regression), a list-typed `problems`, a mutable member inside `problems`, and an uncapped problem flood all REFUSE at construction; the malformed row's total construction yields ≥1 capped problem entry; a FORCED read failure (failed SELECT/open) maps to `malformed(read-failed: …)`, never a raise | CI |
| **I21** the delegated routing is total (external R1-4) | `test_delegated_routing_total` — for EVERY member of 0013's returnable vocabulary as a delegated return: record-present → facts verbatim; record-absent × the four no-record outcomes → the fixed rows, NO error; record-absent × every other outcome → `MigrationAuditReadError(missing)`; malformed × any outcome → `MigrationAuditReadError(malformed)`; a VALID record whose outcome differs from the kernel return → `MigrationAuditReadError(mismatched)` (R2-5); `PackageConsistencyError` propagates on BOTH routes (R3-5): pre-mint → no readback, `unavailable (pre-mint)`; post-mint → readback with the record accepted ONLY when valid AND bound to `package-inconsistent` (any other outcome → `unavailable (readback: mismatched)`); absent/malformed → unavailable — stderr facts labeled recorded or unavailable, never invented | CI |
| **I16** the attestation contract is exact | `test_attestation_contract` — absent, coerced (`quiesced=1`/truthy object), grammar-violating (incl. embedded space), duck-typed, and HOSTILE-SUBCLASS cells (R14-4; `type(x) is` admission, the 0013 authority-regression pattern) | CI |
| **I17** audit failures are loud end-to-end | `test_audit_read_error_is_loud` — a missing record under a record-guaranteed outcome, and a malformed record under ANY outcome, raise `MigrationAuditReadError` whose validated carrier reaches CLI exit 3 with `derived_resulting_state` labeled derived-from-outcome on stderr; the existing `MigrationAuditWriteError` path and the newly-dispositioned `PackageConsistencyError` share the exit-3 loud-escape class, never exit 0. **Gate-extension obligation: the readback boundary, the no-record routing branch, and the mint-retry loop are NEW failure seams — they join `test_every_fault_seam_preserves_the_invariants`'s injection list** | CI |
| **I18** the resolution evidence is reason-labeling only (internal F3; test form corrected by external R2-7 — the v3 regression demanded unconditional refusal, which would itself have made the evidence authority-relevant) | `test_resolution_is_reason_labeling_only` — forged vs genuine `resolved` compared under BOTH real-store conditions: with a VALID store + attestation, mint SUCCEEDS identically under forged evidence (an authority IS granted — forgery must not deny either); with a FAILING store, mint fails identically, and at most the `MintError` reason label differs; PLUS the recursive-exactness cells (closure obligation 2): `resolved_base=True` and hostile `str`-subclass scalars REFUSE at the `PreflightResolution` boundary before any comparison runs | CI |
| **I19** the CLI contract | `tests/test_migrate_cli.py`, amended under this spec's authority (§7a): flags required on the migration path (missing → exit 2), invalid `--backup` → exit 2 with the grammar, exits 0/1/2/3 as §4, reporting from structured fields only — **and the exit-3 package routes enumerated as five named cases (closure obligation 4): pre-mint · bound `package-inconsistent` (recorded facts) · mismatched · missing · malformed, each with its exact stderr form** | CI |

**v7: I24–I32, the data-migration operation's invariants, are §4i.8**; I13–I23 above are unchanged.

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
| `ReadbackResult` | the closed readback sum carrier (§4f) — NamedTuple, total cross-field laws incl. the total read-failure arm, exact-type facts, immutable capped problems (closure obligation 3: v5 put this row in §2 and claimed §7a was complete — the carrier-confusion the inventory exists to prevent) |
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

**v7:** the data-migration operation's own claims and limits are §4i.9.

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


## Review closure

*PROCESS §4a: one row per round's findings, each closed by an openable
artifact — the fold commit and the archive the next round verified. Full
per-finding verdicts: `specs/reviews.py` + each round's COLLECTED.*

| round | findings | closed by |
|---|---|---|
| internal 1 (v1) | F1 readback contradiction (dead branch) · F2 forward-referenced sections · F3 = §10 Q1 `PreflightResolution` row | `df941d6` (v2); internal re-review CLEARED same day |
| ext 1 (v2) | R1-1 the §4/§4b layering (four superseded v17 forms) · R1-2 `PreflightResolution` a name · R1-3 the invalid table (`unchanged`) · R1-4 the no-record outcomes · R1-5 the TerminalFacts leak · R1-6 the read-error carrier · R1-7 the byte-identity exception | `fdbb28e` + `c5aa22d` (v3, the §4 CONSOLIDATION); archive `0018-v3-20260813T2103Z` |
| ext 2 (v3) | R2-1 fingerprint constructibility · R2-2 the delegated laws vs 0013 (→ DEFERENCE) · R2-3 the empty-replacement cell + read-only mode · R2-4 the terminal-domain algebra · R2-5 `read_terminal` raise capability + mismatch · R2-6 the package escape's facts · R2-7 I18's direction · R2-8 the retry bounds · R2-9 the stale `source`/6 rows · B2-1 the reconciliation arithmetic | `07b5652` (v4); archive `0018-v4-20260813T2140Z` — R3 confirmed R2-2/3/4/9 closed |
| ext 3 (v4) | R3-1 tuple-key serialization (probe-executed) · R3-2/R3-3 unswept carriers of the R2 fixes · R3-4 `ReadbackResult` construction · R3-5 the pre-mint package route · B3-1 the MCP gate scope | `cf91b77` (v5); archive `0018-v5-20260813T2202Z` — R4 verified the fingerprint against an independent encoder and reconciled the suite delta exactly |
| ext 4 (v5) | **APPROVED FOR ACCEPTANCE** — four closure obligations: the §2c test clause · recursive exactness (unbound `problems()`, exact-typed scalars) · read-failure totality + the §7a row · the pre-mint message + five enumerated package routes | THIS commit (v6): all four folded, `Spec-Status: accepted`, atomic with 0016 v18 |
