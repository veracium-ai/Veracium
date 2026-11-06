# Feature spec: the release-migration orchestrator

Spec-Status: accepted
Spec-Requires: 0007[0013/0007-sqlite-attestation], 0013[0013/0007-sqlite-attestation], 0016
Folds: 0044/0018-data-migration, 0013/0007-sqlite-attestation, 0018-adjacent-rungs

| | |
|---|---|
| **Author / session** | dev |
| **Version** | **v9 — 2026-11-04: the adjacent-rungs fold (amendment `0018-adjacent-rungs`, v0.5.1, sha16 `bebe330d18206458`).** Design accepted at round 3 (accepted-with-amendments, closed internally under PROCESS.md §4a on the owner's ruling); implementation acceptance outstanding — I33's populated fixtures, I36's declared plan descriptors and digest vectors, I39's SA10 campaign, the original-preservation checks; the owner schedules it. The new §4j carries the amendment; the 0019 rider's (B1), the 2026-09-18 diagnostic amendment, §4a, §4b, §4c, §4e, §4f, §4g, §4h and I13, I15 and I19 are edited in place and point to it; its marked 0007 and 0013 amendments are 0007 §4h and 0013 §5g; `## Review closure` carries its three rounds. Prior: **v8.1 — 2026-11-01: the amendment's implementation acceptance, recorded (0007 v24's acceptance fold).** The SQLite attestation amendment `0013/0007-sqlite-attestation` was IMPLEMENTATION ACCEPTED at its external round 5, 2026-10-31. Its record is in 0007 v24 and 0007 `## Review closure`, and the Decision cell now says so. Nothing else changes; `Spec-Status` stays `accepted`. Prior: **v8 — 2026-10-25: the SQLite attestation fold (amendment `0013/0007-sqlite-attestation`, v0.12.1, sha16 `134243c63b05845a`): the preflight's runtime case and the migration audit's sidecar writer (§4a), edited in place; the amendment itself is 0007 §4g and 0013 §5f.** Prior: **v7 — THE DATA-MIGRATION FOLD (amendment `0044/0018-data-migration`, v4, sha16 `c09a4aed2db848a9`).** Its design was accepted with 0044 at round 4 of the 0044 package (verdict 2026-10-13: I24–I32, with I13–I23 kept), and the owner ruled “Accept now, fold next” (2026-10-14). It adds a per-user data-migration operation BESIDE the release orchestrator, which it leaves untouched. Folded as §4i, labelled by the amendment's own section numbers so its internal references resolve; pointers added at §2, §6 and §8. Its reach rows are re-derived at `af1e564`. Not folded: its review brief, open questions and version history. Prior: **v6 (ACCEPTED)** — EXTERNAL ROUND 4: **APPROVED FOR ACCEPTANCE under the finite-acceptance rule; the frozen surface is I13–I23** (total preflight · the exact retry sequence · the result truth table · exact attestation · loud audit failures · reason-only resolution evidence · the CLI contract · the terminal-domain split · total routing · the fingerprint encoding · the closed readback carrier). v6 = v5 + the four same-commit CLOSURE OBLIGATIONS, each demonstrated in this revision: (1) the R3-2 sweep COMPLETED — the §2c cell's test clause now carries I18's two-condition expectation (the description half was fixed in v5, the test half still said "no authority"); (2) exactness made RECURSIVE — `ReadbackResult` requires `type(facts) is TerminalFacts` and invokes `TerminalFacts.problems(facts)` UNBOUND (the reviewer's dynamic-validator subclass probe is the named regression), and `PreflightResolution` exact-types every scalar before any comparison (`resolved_base=True` refuses; hostile `str` subclasses refuse) — I18/I23 extended; (3) read-level failure TOTALITY — `malformed(problems)` is the total read-failure arm (`read-failed: <class>` bounded entries; forced-read-failure regression), and the `ReadbackResult` row is IN §7a (v5 had put it in §2 while claiming §7a complete); (4) the R3-5 output sweep FINISHED — the false "store not accessed" clause removed (the preflight reads the manifest), and §4g/I19 enumerate the five package routes. The reviewer's verification: the corrected fingerprint EXECUTED and matched an independent encoder; the suite delta reconciled exactly; B3-1 closed. **Acceptance is ATOMIC with 0016 v18 (this commit flips both).** *(v5 history: external round 3 — 5+1 folded: the executable fingerprint via `identity(manifest())`, the swept §2c/I14 carriers, the constructed `ReadbackResult`, the pre-mint package route, the MCP gate-scope correction.)* |
| **Status** | *narrative only — canonical is the `Spec-Status:` line* |
| **Internal reviewers** | research — round 1 RETURNED + folded (v2); re-review CLEARED 2026-08-13. *(v2 history: F1 readback reconciliation — refined by external R1-4; F2 sections inlined; F3 the `PreflightResolution` §2c row + reason-labeling pin.)* |
| **External review** | **ROUND 4: APPROVED FOR ACCEPTANCE** (2026-08-13, package `0018-v5-20260813T2202Z.tar.gz` sha `107e7720…`) — findings 3(int)/7/9+1/5+1/0; the four closure obligations folded same-commit with the flip |
| **Decision + date** | **ACCEPTED 2026-08-13** — external round 4, under the finite-acceptance rule; the frozen surface is I13–I23; ATOMIC with `0016` v18 (commit `32faaa8`). *(Row filled 2026-08-22 — the audit also found this round's VERDICT was never recorded in `specs/reviews.py`; recorded now.)* **v7, 2026-10-14:** the amendment `0044/0018-data-migration`, accepted with 0044 at round 4, folded on the owner's ruling “Accept now, fold next”. · **v8: the amendment's design accepted** (its round 2, 2026-10-25, and the owner's word); implementation acceptance was outstanding until 0007 v24 (its obligations are in 0007 `## Review closure`; 0018's invariant ids are its own, so they are not repeated here) · **the amendment's IMPLEMENTATION ACCEPTED** at its external round 5, 2026-10-31 (recorded in 0007 v24) · **v9: amendment `0018-adjacent-rungs`'s DESIGN ACCEPTED** (its external round 3, 2026-11-04, accepted with amendments, closed internally under PROCESS.md §4a on the owner's ruling; both seats ran every closure row, `## Review closure`); implementation acceptance outstanding (I33, I36, I39, the original-preservation checks) |
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
>
> **v9 (amendment `0018-adjacent-rungs`, §4j):** no cell produces `unsupported-base` at this head, and the derived diagnostic loses its only caller and is removed (§4j.6.4a; §4j.3). The outcome and its row stay for a future floor.

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
>
> **v9 (amendment `0018-adjacent-rungs`, §4j):** (B1)'s “resolved base **7** ALONE proceeds to minting” (HEAD−1 in the code) is superseded: every resolved base `b`, `FIRST_MIGRATABLE ≤ b ≤ HEAD−1`, stamped or unstamped-legacy, proceeds to minting `b → b+1` (§4j.6.4a), and no cell produces `unsupported-base` at this head.

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

**v9 (amendment `0018-adjacent-rungs`; §4j.6.4a):** the mint cell moves. Every resolved base `b` with `FIRST_MIGRATABLE ≤ b ≤ HEAD−1`, stamped or unstamped-legacy, proceeds to minting `b → b+1`; the CLI walks the rungs (§4j.6.4g); no cell produces `unsupported-base` at this head. Every other cell above is unchanged.

Every preflight interception creates ZERO authorities and ZERO 0013 audit
rows. **Byte-identity holds for every preflight cell EXCEPT
current-with-repair** (external R1-7): that one cell commits the
rebuildable-drift repair through the shared opening path and honestly reports
`(True, True, destination, 7)`; every other interception leaves the store
byte-unchanged. Ordinary OPENING of a below-v6 store is UNCHANGED by this
spec — 0013's existing below-head refusal governs it; only the orchestrator's
preflight returns `unsupported-base`.

### 4b. `PreflightResolution` — the construction (external R1-2)

> **v9 (amendment `0018-adjacent-rungs`; §4j.6.4b):** `resolved_base ∈ {FIRST_MIGRATABLE … HEAD−1}`; its exact-type admission, the fingerprint and I18's reason-labeling-only pin are unchanged.

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

> **v9 (amendment `0018-adjacent-rungs`; §4j.6.4c):** the mint re-observes the store and mints `b → b+1` for a store stamped `b` and accepted there, or unstamped and resolving to `b` through `legacy_base_versions()`; the retry sequence is unchanged and per rung.

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

> **v9 (amendment `0018-adjacent-rungs`; §4j.6.4e):** the result domain is the preflight rows, the no-record rows, and every delegated carrier lawful at SOME rung `(b, b+1)`; the exact binding lives in `RungReport` (§4j.6.4e-iii). No cell produces the `unsupported-base` row at this head; the row stays for a future floor. A third, glossed `migration-source-missing` row is added (§4j.6.4e-ii).

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

> **v9 (amendment `0018-adjacent-rungs`; §4j.6.4e-i and §4j.6.4f):** the rules are unchanged, applied per rung at the minted endpoints `(b, t)` wherever this section says `(HEAD−1, HEAD)`.

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

> **v9 (amendment `0018-adjacent-rungs`; §4j.6.4g):** `veracium migrate` walks the rungs with a bound that holds by construction, per-rung reporting and one total recovery classifier (§4j.9); the flags, the usage exits and the attestation grammar are unchanged.

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

> **v9 (amendment `0018-adjacent-rungs`):** its own marked amendments are 0007 §4h (`open_versioned`'s migration target) and 0013 §5g (the forward step with a target; §5f.1 bound to the operation's target).

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

*Annotation (research, 2026-11-06; the row above is kept as written): I31 is the data-migration amendment's, and it holds of that amendment, which changed none of I13–I23. The adjacent-rungs amendment then amended I13, I15 and I19 by its own authority (§4j.1), restated as I13′, I15′ and I19′ (§4j.8), and their tests moved with it, so "pass unmodified" does not describe those three rows after v9. In `tests/test_0018_orchestrator.py`, `tests/test_0013_presend_gates.py` and `tests/test_migrate_cli.py`, the cells of `unsupported-base` and the ladder are replaced, the result oracle is widened and the CLI cells move to the walk. I14, I16–I18 and I20–I23 are unchanged, and the tests they cite assert what they asserted. Two tests followed a private seam and no assertion moved: `test_mint_race_reclassifies`'s stub takes `_preflight_classify`'s new argument, and `test_package_escape_propagates_on_both_routes` patches `_run_rung`.*

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

## 4j. Adjacent rungs (v9, amendment `0018-adjacent-rungs`)

> **What this section adds:** the accepted amendment `0018-adjacent-rungs` (v0.5.1, sha256 `bebe330d18206458…`; design accepted at its external round 3, accepted with amendments, closed internally under PROCESS.md §4a on the owner's ruling, with both seats' closure runs in `## Review closure`): `veracium migrate` walks a released store to head one schema version per audited operation, each rung its own operation id, terminal record and clock read, under one operator attestation; recovery from a stopped walk is one total classifier (§4j.9). The clauses it amends are edited in place and point here: the 0019 rider's (B1), the 2026-09-18 diagnostic amendment, §4a, §4b, §4c, §4e, §4f, §4g, §4h and I13, I15 and I19 in §6. **Within this section, a reference to “§1”–“§8”, “§2a”, “§2c-ii”, “§3b”, “§4a”–“§4h” (and their “-i”, “-ii”, “-iii” parts) or “§7a”–“§7c” means the subsection here whose label ends in that number** (the amendment's own numbering, kept so its references resolve, behind the prefix of the 4j.N subsection that holds it: “§4a” is §4j.6.4a, “§2c-ii” is §4j.4.2c-ii, “§7b” is §4j.9.7b), **except that “§4d-i” means 0007 §4h and “§4d-ii” and “§4d-iii” mean 0013 §5g**, which carry the amendment's marked 0007 and 0013 amendments. The amendment's §9 (the reviewer's brief), §10 (its open questions, answered) and its reviewer checklist are not folded. A reference to 0018's own sections says “0018”.

### 4j.1 What it amends (the amendment's header)

| | |
|---|---|
| **Amends** | 0018 (accepted; frozen surface I13–I23): §4a's mint cell, §4b's accepted-base set, §4c's mint, §4e's result domain and its `unsupported-base` row, §4f's endpoints, §4g's CLI contract, I13, I15, I19. The 0019 rider's (B1) clause "resolved base 7 ALONE proceeds to minting" (HEAD−1 in the code). **Marked 0007 amendment:** `open_versioned` gains a migration target (§4d-i). **Marked 0013 amendments:** the forward step takes a target, and its steps become one declaration consumed by execution and the digest (§4d-ii); §5f.1's (b1), (b2) and stamp rules bind to the operation's target (§4d-iii). |
| **Leaves unchanged** | accepted 0013's adjacency law (round 15, correction B: a migration is `n → n+1`); `TerminalFacts` and its `problems()`; `MigrationAuthority`'s shape; 0018 §4e's deference law, its no-record rows and the retry-unsafe `migration-audit-state-unknown`; I14, I16–I18 and I20–I23; the public `migrate_store`, which still goes base→head in one call; ordinary opening; the runtime gate. **Each "unchanged" is checked in §2a against the values this amendment moves, not asserted.** |
| **Ruling** | Round-3 closure (the owner, first-hand, relayed by dev, 2026-11-04): **"Close internally (Recommended)"**: fix, both seats verify each closure row by running it, then dev sets the amendment accepted with a `## Review closure` section, with no round-4 dispatch. Round 3 (the owner, first-hand, 2026-11-03, ledger `72f7b19`): **"Amend for round 3, after 0048 r4 (Recommended)"**. R1-07 (the owner, first-hand, ledger `02d5787`): **"Migrating build only (Recommended)"**. The option the owner chose reads, verbatim (relayed by dev): *"Promise only that rerunning `migrate` with the same (or newer) build resumes and finishes. Don't promise an older release can read a half-walked store; the backup taken before the walk is the way back."* |

### 4j.2 Why (the amendment's §1)

`veracium migrate` (0018's orchestrator) mints an authority only for a store at **HEAD−1**. Today that is v15, and no
release ever shipped v15. So the CLI refuses **every store a release wrote below head**:

| releases | schema |
|---|---|
| 0.26.x | v14 |
| 0.20–0.25 | v13 |
| 0.18–0.19 | v12 |
| 0.16–0.17 | v11 |
| 0.14–0.15 | v10 |
| 0.13 | v9 |
| 0.11–0.12 | v8 |
| 0.10 | v7 |
| 0.7–0.9 | v6 |
| 0.6 | v4 |
| 0.5 | v3 |
| 0.1–0.4.8 | v1, unstamped (`user_version` 0) |

*Source:* `src/veracium/store/evidence/legacy_stores.json` for every row it records. For the eight releases whose
entry is null there (v0.7–v0.9, v0.10, v0.14–v0.15, v0.16–v0.17; §4h), the version is each tag's own `SCHEMA_VERSION`,
re-derived by dev from the tags.

At the pin, the open refusal names the offline library call `migrate_store(path)` and names `veracium migrate` for a
v{HEAD−1} store only; `doctor` relays that refusal verbatim (the 0.30.0 interim, dev `9e6c134`). So the operator is
told a route that works, and the CLI still cannot serve these stores.

Minting one authority from a released base straight to head produces a terminal record that accepted 0013's adjacency
law refuses ("Round 15, correction B: the migration contract is ADJACENT single-step (n → n+1)", ported into
`TerminalFacts.problems()`). **This amendment keeps the law and walks the rungs**: one audited operation per schema
version, each with its own operation id, terminal record and clock read, under one operator attestation.

**Round 2 (external, 2026-11-03) kept the approach and closed five of round 1's findings** (R1-01..R1-04, R1-07; R1-05 and R1-06 partly). It returned three: a committed error the walk did not count (R2-01), I36's trace units and the direct route's construction (R2-02), and three head-bound refusals §2a missed (R2-03). §9 maps each to its answer.

**Round 1 (external, 2026-11-03) endorsed the approach and returned the contract.** Its seven findings, R1-01..R1-07,
are answered in §9's table. Five of them ran an accepted rule that is bound to the value this amendment changes (the
mint's fixed endpoints, or the head as destination) against the new contract. v0.3 therefore lists every such rule in
§2a and states, for each, how it moves and which cell runs it.

**Two pre-existing defects this amendment closes** (both found while building the round-1 model, both RUN by dev at
the pin, both shipped since `1cab3a7d`, 2026-08-16, which 23 release tags from v0.11.0 contain). Each needs a false
quiescence attestation or a racing writer, which accepted 0018's Limits already say the orchestrator cannot detect. So
they are audit-honesty gaps under a violated precondition, not data defects:
- **M1.** A v15 store swapped for an accepted, stamped v13 between the mint and the transaction is walked 13→16 and
  ends `migrated`. **Its attempted event says `13 → 16`; its terminal record, result and readback say `15 → 16`.** The
  delegated kernel is called without the authority, so nothing binds the transaction's source to the minted one.
  Closed by §4d-i's source binding.
- **M3.** A store deleted in the same window is re-created by `sqlite3.connect`, then built as a fresh v16 store (77
  objects) and recorded `internal-error (True, True, destination, 16)` with no attempted event. Closed by §4e row 11a
  (the rung opens without creating). Its sibling M2, an empty replacement created at head, is 0018's documented
  narrowing (no `new=` seam in `migrate_store`) and is closed by §4e row 10.

**Alternatives rejected:**
- **One multi-version authority (option A).** It reopens a law 0013 closed on purpose, at round 15.
- **The CLI calls `migrate_store` directly** (the pre-0018 contract). It drops the preflight, the attestation, the
  authority and the terminal readback that 0016/0018 made the CLI's contract.
- **Mint only from bases a shipped release names.** The release record carries no schema head for eight releases, and a
  store interrupted mid-walk sits at an unreleased version (v15) that must still be resumable.

### 4j.3 Field contracts (the amendment's §2)

| carrier | today | after |
|---|---|---|
| the preflight's mint cell (§4a; the 0019 rider's (B1)) | resolved base HEAD−1 ALONE mints | **every resolved base `b`, `FIRST_MIGRATABLE ≤ b ≤ HEAD−1`, stamped or unstamped-legacy,** proceeds to mint `b → b+1` |
| `mint_release_authority` (§4c) | mints only a store STAMPED `HEAD−1` | mints `b → b+1` for a store stamped `b` and accepted there, **or unstamped and resolving to `b` through `legacy_base_versions()`**, by its own observation (§4c) |
| `PreflightResolution.resolved_base` (§4b) | ∈ {1 … HEAD−1} (the code; "{1…6}" in the frozen text) | unchanged set, exact-typed as before |
| `MigrationAuthority` (§4c) | `(HEAD−1, HEAD)` | `(b, b+1)`. **The shape is unchanged; adjacency holds by construction** |
| `MigrationAuthority.migration_digest` | hashes `[HEAD−1, HEAD, ALTERS_V7_TO_V8]` at every head | SHA-256 over the rung's **declared steps** in the frozen preimage grammar (§4d-ii) |
| `MigrationResult` (§4e) | delegated rows validated at the fixed `(HEAD−1, HEAD)` | the domain is the preflight rows, the no-record rows, and every delegated carrier lawful at SOME rung `(b, b+1)`; the exact binding lives in `RungReport` |
| **`RungReport`** (new, §4e-iii) | — | one rung's report: its kind, result, observed base and stamp, operation id and minted endpoints |
| `run_release_migration` | one operation, HEAD−1 → HEAD | **one rung per call**, `b → b+1`; signature and public result unchanged; returns `run_release_rung(…).result` |
| **`run_release_rung`** (new, package-private) | — | `run_release_rung(path, *, host_attestation, expect_base=None) -> RungReport` (§4e-iii) |
| the `unsupported-base` outcome (§4e) | bases 1..HEAD−2 | **no cell produces it at this head**; the member, its row and its I20 exclusion stay for a future floor |
| CLI `veracium migrate` (§4g) | one operation | **a walk** with a bound that holds by construction, per-rung reporting, and a recovery table; flags and exit classes unchanged |
| `open_versioned` (0007, marked) | migrates an older store to HEAD | an optional `migrate_to` (§4d-i) |
| the forward step and its steps (0013, marked) | diff to `SCHEMAS[HEAD]`; guards and stamp at HEAD; steps written inline | the same with target `t`; the steps become ONE guarded entry table, from which `plan(b, t)` is derived for every operation, direct or rung (§4d-ii) |
| 0013 §5f.1 (b1), (b2), the stamp (marked) | bound to `SCHEMAS[SCHEMA_VERSION]` and the head stamp | bound to the target `t` established for the operation (§4d-iii) |

**Consumers enumerated:** `grep -rn "run_release_migration\|_MINT_BASE\|_ladder_diagnostic\|_release_heads" src tests`
(dev at implementation). `_ladder_diagnostic` and `_release_heads` lose their only caller and are removed; the release
record keeps its other consumer, `legacy_base_versions()`.

##### 4j.3.2a. The accepted rules bound to the values this amendment moves

This amendment turns two constants into per-operation values: the mint's endpoints `(HEAD−1, HEAD)` become `(b, b+1)`,
and the kernel's destination HEAD becomes the target `t`. Every accepted rule bound to either is listed here, from a
census at the pin (`grep -n "_MINT_BASE\|_HEAD"` over `src/veracium/store/release_migration.py`; `grep -n
SCHEMA_VERSION` over `specs/evidence/0013/sa10_gate.py`; the 0013 text's head-bound phrases). A row is "moves" or
"stays", with its reason and the cell that runs it.

**The kernel's rows are a DERIVED set, not a list** (R2-03). Round 2 found three head-bound refusals that v0.3's
hand-made rows omitted. The set is defined as **every reference to `SCHEMA_VERSION` in the forward step's REACH, by
AST**: `_apply_forward`, the module functions it calls, and the constructors of the errors it raises, transitively,
within `src/veracium/store/` (the Name and attribute forms, and any module-level alias of it). Every member moves
to `t`. The reach matters: `MigrationPostconditionError` passes `SCHEMA_VERSION` itself (L63), and every refusing
check reaches it through `_refuse_unless`, on every rung; a set scoped to `_apply_forward`'s own body would miss it
(dev's stage-1 read of v0.4). Dev's generated census computes the set and refuses any difference from its committed
expectation (cited below, with its digests). At the pin the members are: the base
check and its raise (L321–324); the additive diff (L331); the eight step guards; the five ALTER-output byte-check
raises (v6 L386–387, v8 L414–415, v10 L440–441, v16 L496–497 and L529–530); the stamp and its check (L587–590);
and the postcondition error's L63. The other functions and classes in the reach carry none: 34 are reached across four store modules (`migration` 24,
`schema_version` 4, `edge_events` 5, `lifetime` 1). **The census:** dev, head_bound_census.py (`4d9d4d22…`), its
expectation head_bound_census.expected.json (`f2ab0596…`) and its plant matrix head_bound_census_matrix.py
(`438eac8a…`), shipped in specs/evidence/0018-adjacent-rungs/dev-model/ and run against `tree/` at the pin: **21 references, equal to the
expectation**, the 20 above in `_apply_forward` and L63; the matrix gives 12 of 12 cases as expected (nine plants
refused, among them an import-as alias, a module alias's attribute, a reference in a reached helper of another store
module and one in a raised error's base `__init__`; the honest tree and two controls pass). Research re-ran the
census and its matrix on its own `git archive` export of the pin, with the same result. Its residual is named in its
README: a string-built lookup is out of reach of an AST census. Its repository copy, with its matrix, is an
implementation obligation under I33 (iii).

**The rung's events are outside the set by construction.** The rung entry builds its attempted and committed events
in its OWN `older` hook, with `(b, t)` (§4d-i); it does not reuse `migrate_store`'s hook. So `migrate_store`'s
L822/L828/L838 are the direct route's and stay at head (the row below).

| rule (at the pin) | where | disposition | run by |
|---|---|---|---|
| mint predicate `found == _MINT_BASE` | `release_migration.py` L915–916 | **moves**: any accepted base, stamped or legacy (§4c; R1-01) | model, A2 row 2 and A3 |
| authority endpoints and `source_digest` at `_MINT_BASE` | L923–924 | **moves** to `(b, b+1)`, `digest(objs, b)` | model, C2 |
| `_declared_migration_digest` `[_MINT_BASE, _HEAD, ALTERS_V7_TO_V8]` | L874–880 | **moves** to the declaration (§4d-ii; R1-06) | I36 vectors |
| `MigrationResult` delegated check at `(_MINT_BASE, _HEAD)` | L761 | **moves** to "lawful at some rung" plus `RungReport`'s exact binding (§4e-iii; R1-03) | model, C1; facts check |
| every `TerminalFacts(…, _MINT_BASE, _HEAD, …)` in `_kernel_call`, and `r.resulting_version == _HEAD` | L1151–1218 | **moves** to the minted `(b, t)` and `== t` | model, A2 |
| the post-mint package escape's facts | L1283 | **moves** to `(b, t)` | I23 cell at a lower rung |
| preflight `found == _HEAD` / `> _HEAD` cells | L1020–1034 | **stays**: the preflight judges the store against the BUILD's head; only a delegated rung is target-relative (§4e-ii) | model, C2 at HEAD |
| `unsupported-base` and the ladder diagnostic | L976–991, L1056–1059 | **moves**: no cell produces it; the diagnostic is removed | I13′ |
| `_MAX_UNSUPPORTED = _HEAD - 2`, the range `unsupported-base` carries | L71, used at L744–746 | **moves**: the range becomes the bases below `FIRST_MIGRATABLE`, empty at this head | I13′; I15′ |
| `PreflightResolution`'s set `1 <= resolved_base <= _MINT_BASE` | L684–686 | **stays** by value (HEAD−1); bound to `_MINT_BASE` by name, so it is restated as `FIRST_MIGRATABLE … HEAD−1` | I22 cells unchanged |
| the mint's refusal diagnostic "is not an accepted v{_MINT_BASE} migration source" | L938 | **moves** to the mint's own observed `b` | model, A3 |
| kernel base check `base >= SCHEMA_VERSION`, and its raise (`SCHEMA_VERSION` as its expected-version argument, passed positionally, and "no migration path from base {base} to head {SCHEMA_VERSION}") | `migration.py` L321–324 | **moves** to `base >= t`, the raise's expected version and text to `t` | I33 |
| additive diff against `SCHEMAS[SCHEMA_VERSION]` | L331 | **moves** to `SCHEMAS[t]` | I33 (shape probe) |
| eight step guards `… <= SCHEMA_VERSION`, at L337, 348, 358, 378, 406, 429, 452 and 487 (three with a lower bound on `base`, e.g. L378 `4 <= base < 6 <= SCHEMA_VERSION`), and the step blocks they open | the blocks, L337–586 | **moves**: `SCHEMA_VERSION` is replaced by `t` in each guard, lower bounds kept | I33; §2c-ii row 1 |
| the v6, v8 and v10 ALTER-output byte-check raises (`supersession_operations` against `ALTER_PATH_V6_SQL`; the v8 and v10 tables against `ALTER_PATH_V8_SQL` and the two accepted v10 forms), each passing `SCHEMA_VERSION` as its expected-version argument (**missed by v0.3; round 2, R2-03**) | `migration.py` L386–387, L414–415, L440–441 | **moves**: the expected version to `t`. Each fires only on a rung whose plan includes its ALTER (`t` = 6, 8, 10 on a walk); on a direct route to head it still says 16, as today | I33 (iii): a lower-target mismatch at 5→6, 7→8 and 9→10 reports expected 6, 8 and 10 |
| the v16 block's two byte-check raises (the v15→v16 ALTER output of `confirmations` and `redactions` against the frozen `ALTER_PATH_V16_*_SQL`), each passing `SCHEMA_VERSION` as its expected-version argument | L496–497, L529–530 | **moves**: the expected version to `t`. They fire only at `t = 16` | I33 at the last rung |
| the stamp and `STEP_STAMP` check | L587–590 | **moves** to `t` | E2 sequence 2 (the stamp is a `_refuse_unless` call) |
| the attempted/committed events' `to_version` in `migrate_store`'s own hook | L822, L828, L838 | **stays** at head: they are `migrate_store`'s, which passes `SCHEMA_VERSION`. A rung's events are built by the rung entry's OWN `older` hook (§4d-i) with `(b, t)` | model, A2 row 2 (the attempted record says from 1) |
| `MigrationPostconditionError`'s expected version (its constructor passes `SCHEMA_VERSION` itself; reached through `_refuse_unless` by every refusing check, on every rung) | L56–65, the reference at L63 | **moves** to `t` | I35; the census (in the reach) |
| `open_versioned`'s expected version, accepted digests and `_validated_current` | `schema_version.py` L1924– | **moves** for the version and shape decisions only, when `migrate_to` is given (§4d-i) | model, A1 |
| the runtime gate: `runtime_status()`, `attestation_revision()`, `verify_build()` | `schema_version.py` L1371, L1483, L1572 | **stays at the build's revision.** The target must not reach it (§4d-i; dev's model F1: patched, every below-head rung refused `unsupported-sqlite`) | I37 cell |
| (b1) "byte-equal to the head constructor DDL `SCHEMAS[SCHEMA_VERSION][k].ddl`" | 0013 §5f.1; `sa10_gate.py` L562, L732 | **moves** to `SCHEMAS[t]` (§4d-iii; R1-02) | I39 |
| (b2) rebuildable-index repair over the head's indexes | `sa10_gate.py` L864 | **moves** to `SCHEMAS[t]` | I39 |
| PRAGMA row "the stamp is exactly (`user_version`, the head version)" | 0013 §5f.1; `sa10_gate.py` L949 | **moves** to `t` | I39 |
| `gate_paths()` release entries `b == SCHEMA_VERSION − 1` only | `sa10_gate.py` L894 | **moves**: every release base, unstamped legacy fixtures, drift repair at an intermediate `t` | I39 |
| 0018 I35's expected label `migration-failed` | v0.2.2 §6 | **moves** to `unsupported-migration` (accepted 0013 §4f, M123) | model, A2 row 12 |
| §5's "an older build can open an interrupted store" | v0.2.2 §5 | **withdrawn** (R1-07; 0016's required `source_type`) | §8 claim |
| `TerminalFacts.problems()` | L215–293 | **stays**: every §4e row's facts pass it at four rungs | facts check (56/56) |
| 0018 §4e no-record rows, retry-unsafe text | §4e; `_NO_RECORD_DIAGNOSTICS`, L1119–1131 | **stays**, per rung | model, B rows 5–6 |
| 0018 §4e's two `migration-source-missing` rows (nothing at the path → `missing`; an empty `user_version=0` file → `unaccepted`) | §4e | **stays**, and a THIRD glossed row is added: an accepted store at the wrong version, `unaccepted` meaning rejected as this operation's source (§4e-ii) | model, rows 7a, 8a, 10, 11a |

### 4j.4 Untrusted inputs and reach (the amendment's §2c)

Every row of 0018 §2c stands. The changed and new rows:

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant that pins it |
|---|---|---|---|---|---|
| a stored database at any base `1 ≤ b ≤ HEAD−1`, stamped and accepted at `b`, **or unstamped and resolving to a `legacy_base_versions()` base** | — | shape not accepted at its stamp → `stamped-shape-mismatch`, unchanged | unstamped, matching no legacy base → `foreign-shape`, unchanged | a store stamped at a version no release shipped (v2, v5, v15) mints like any other: the authority is the accepted-shape evidence for `b`, never the release record | **I13′**, **I33** |
| the store **between the mint and the rung's transaction** (another process, despite the attestation) | deleted → §4e row 11a: refused, nothing created (M3) | replaced by an empty database → row 10 (M2) | another accepted version below the source → row 7a; past the target → 7b; at the target → `current` at `t` (row 4) | swapped at the SAME version and shape: not visible. The transaction binds the base and shape, not the content (0018 Limits, unchanged) | **I38** |
| an interrupted walk | — | — | — | the store sits at an intermediate version, stamped and accepted there; the next `migrate` resolves it as an ordinary base and resumes **with the migrating build or a newer one**. No partial rung exists: each rung is one transaction | **I35** |
| the attestation, across rungs | — | as 0018 | — | **one** `MigrationAttestation` for the walk, re-admitted exact-type at every mint, never re-prompted or fabricated. It cannot expire: it carries exactly `quiesced` and `backup_ref`; the 15-minute window belongs to each rung's freshly minted authority | I16, **I34** |
| `PreflightResolution` passed to the mint | — | refused exact-type, as 0018 | — | forged (any base) changes no mint decision either way: it labels a failure only (I18). Run by the model with forged bases 7, 15 and 2 against an eligible v13 and a refusing foreign store | I18 |
| the path the rung entry opens without creating (§4d-i), as a SQLite URI | — | a path containing `?`, `#`, `%` or a space; a non-UTF-8 filename the platform supports | — | **a sibling whose name is the path's prefix up to `?` or `#`** (the reviewer's E2-01: an unencoded URI migrated the sibling and reported success). The URI carries the canonical path's filesystem bytes percent-encoded, so it names exactly that file; an open that fails is reported by §4e-ii's existing rows, never as `missing` unless nothing is at the path | **I38** |
| `migrate_to` on `open_versioned` | `None` → today's behaviour | non-int, `bool`, `int` subclass → `TypeError`; out of `FIRST_MIGRATABLE+1 … HEAD` → `ValueError`; both before any store access | — | `t < HEAD` without the migration hook → `ValueError`, so no ordinary open reaches a below-head target | **I37** |

`expect_base` is supplied only by the package's own CLI, never by a caller of the public API, so it is not an
untrusted input; `run_release_rung` is package-private.

##### 4j.4.2c-ii. Assertions about reach — REQUIRED

All at the pin, dev `67bbba69`, on `git archive` exports with CPython 3.14.7. **Rows 6–9 are model results, kept
apart from product results:** the model runs the pin's real opening path, kernel, audit writers and validator, with a
rung's target set by a process-local patch; it is not the implementation.

| # | assertion | how established | result |
|---|---|---|---|
| 1 | every rung `b → b+1` from every base `1 ≤ b ≤ 15`, walked to v16, lands on a shape accepted at `b+1` | research, specs/evidence/0018-adjacent-rungs/research-67bbba6 (probe_rungs.py), empty stores built by `sv.create(conn, b)` | 120 of 120 rungs; 15 of 15 direct jumps; four controls as expected (three say no, one says yes). The reviewer reproduced it byte-for-byte |
| 2 | accepted 0013 forbids a non-adjacent terminal record | `specs/migrations_0013.py` L915–918; `src/veracium/store/release_migration.py` L242–245 | "endpoints must be adjacent" in both |
| 3 | every historical table/index constructor has the shape (b1) asserts of the head's | research, specs/evidence/0018-adjacent-rungs/research-v0.3 (probe_constructors.py) | 338 constructors over v1–v16, none with `IF NOT EXISTS`, `AS SELECT` or a non-plain `CREATE`; 23 `(version, table)` constructors differ from head's, the reviewer's four among them; a planted control is reported |
| 4 | every §4e-ii row's facts are lawful | research, the same directory (check_a2_facts.py), the pin's `TerminalFacts.problems()` | 56 of 56 at rungs 1→2, 13→14, 14→15, 15→16; five controls refuse; the pin's `MigrationResult` refuses a lawful `(migrated, v14)` (R1-03 reproduced) |
| 5 | `legacy_base_versions()` | research, at the pin | `{1}`, so §4e row 8b is unreachable at this head |
| 6 | the reviewer's witnesses reproduce | dev, reviewer_probes.py from the inbox archive | round 1: 14 of 14 records equal theirs apart from the generated operation id. **Round 2** (dev, from the round-2 inbox archive, at the pin): 14 of 15 records of the reviewer's probe script equal after normalising, the fifteenth being the environment record; the reviewer's census-error probe 6 of 6 |
| 7 | M1, M2, M3 at the pin | dev, probe_m1_m2.py; **round 2's E2-02:** its observer opened the path with SQLite after `os.remove`, recreating an empty file, so its M3 run repeated the empty-replacement case. The reviewer's corrected observer (`os.path.exists`, no open) independently confirms M3: the path is absent before delegation, and the pin creates a v16 store and returns committed `internal-error`. Dev's corrected probe replaces the round-2 pair, which is superseded with no digest | M1 and M2 as §1 states; M3: the path is absent immediately before delegation, then the pin creates a v16 store and returns committed `internal-error`, read back as a record. Dev's corrected probe probe_m1_m2.py (`5e035bae…`), output m1-m2-m3-67bbba6-r3.jsonl (`a19bcdd1…`; operation ids inside, compared after normalising them); its counter-control, round 2's observer kept byte-identical as probe_m1_m2.round2-observer.py (`2fae3653…`), re-run at the pin as m1-m2-m3-67bbba6-round2-observer.jsonl (`3d3d0daf…`), still reproduces the empty-replacement case: it sees the empty file it creates. Shipped in specs/evidence/0018-adjacent-rungs/dev-model/ |
| 8 | the kernel routes an unstamped legacy store with objects to the hook | dev, cell5.py (`b395e57a…`), output cell5-67bbba6.jsonl (`408ffd5b…`), shipped in specs/evidence/0018-adjacent-rungs/dev-model/ | `older(…, found=0, base=1)`; a raising hook leaves stamp 0. Only the mint excludes the legacy store |
| 9a | **this version's text, modelled (round 3)** | dev, model_v04.py (`1e97046e…`), output model-v04-run-67bbba6.jsonl (`6fe72245…`), against v0.4.1 with research's corrected absence rule; its records 2–77 (75 cells and the E2 check-sequence record) are round 2's model-v03 run, byte for byte. An earlier model_v04 pair, taken before that correction, is superseded with no digest; shipped in specs/evidence/0018-adjacent-rungs/dev-model/; deterministic (byte-identical from another work directory after its first line's source path) | **119 ok, 0 not ok, 2 inexpressible** (round 2's two E2 records). E2-01: five named-file cells, a non-UTF-8 name among them, each migrating exactly the named file; the three unencoded counter-controls fail as they should; a directory at the path is unopenable. Absence (§4d-i): a dangling symlink at preflight time is `missing` and nothing is minted; one swapped in after the mint is `store-unopenable` `(False, False, unknown, None)`; 0013 round 16 f5: a source vanishing between the `lstat` and the open, re-checked fresh, reads `missing`, and its mutant (no re-check) reads `store-unopenable` and is killed. P5: totality at 1→2, 13→14 and 15→16, printing the carriers `problems()` admits and refuses, each admitted one mapped to exactly one §7 row. R2-01: seven walk cells, five mutants killed, round 2's counting algorithm among them. R2-02: the guard table read from the pin's AST; the trace equals `plan(b, t)` with kind attribution (SQLite's authorizer, statement cache off) on all 29 routes the model walks; 0, 1 and 2 legacy rows give 0, 1 and 2 writes; the reviewer's direct-versus-adjacent witness (direct: the v16 constructor, 0 ALTERs, 1 clock read, stamp 16; adjacent: the v2 constructor, 14, 15, stamps 2..16); eight closure mutants, all detected. The model states its own bound: kinds are read from the declaration, and only populated fixtures exercise a data write |
| 9 | round 2's tables, modelled (**superseded**) | dev, model_v03.py and its run model-v03-run-67bbba6.jsonl, against the tables' revision 3, shipped in round 2's package. **Not shipped in round 3: superseded by model_v04, whose records 2–77 (75 cells and the E2 check-sequence record) are v0.3's run, byte for byte** (row 9a); cited with no digest. **Deterministic:** the work directory and operation ids are normalised before any note is truncated, so a run from a different work directory reproduces it byte for byte. Three earlier runs are superseded and cited with no digest: one against revision 2 (67 ok, 6 not ok, F1–F3, 2 inexpressible), whose script was overwritten in place; and two against revision 3 with the same cell results as this, the first carrying local paths and live operation ids, the second truncating notes before normalising, so that its bytes depended on the work directory's length | **73 ok, 0 not ok, 2 inexpressible** (now implementation obligations, §6); the deleted-store cells give `(False, False, missing, None)` with no file on disk afterwards. Confirmed: §4d-i's argument rows; §4e-ii rows 1–5, 7a, 7b, 8a, 9, 10, 12 at three rungs; row 2 on a populated unstamped v1, a forced failure restoring stamp 0 and the data; I18 against forged resolutions; `RungReport` binding; walks from v13 (3 rungs), populated v1 (15), unstamped v1 (15), HEAD (0); a store moved down after rung 1 stopping with one mint; recovery rows 5–8; a pre-mint escape after two rungs carrying no id |

**What these do not establish:**
- **The implementation.** Rows 6–9 run the pin's code under a patched head. The target parameter, the rung entry and
  the declaration do not exist yet.
- **Release-authored populated stores.** Rows 1 and 3–4 read definitions or empty stores; row 9 used synthetic
  populated stores. I33 owes fixtures written by each release's own code.
- **The SA10 gate at an intermediate target.** It is head-bound at the pin; I39 is its implementation cell.

### 4j.5 Trust classes, authorization and scope (the amendment's §3 and §3b)

No new trust class: every caller is the operator who owns the file (0018 §3, unchanged). The walk adds no input that
another principal supplies.

##### 4j.5.3b. Authorization and scope

Unchanged from 0018 §3b, with one carrier fewer: `unsupported-base`'s diagnostic, which cited release tags, is no
longer produced. Per-rung reporting carries versions, outcomes and operation ids, never store content.

### 4j.6 Behaviour (the amendment's §4)

##### 4j.6.4a. The preflight (amends 0018 §4a and the 0019 rider's (B1))

The preflight's matrix is unchanged except for one cell:
- **every resolved base `b` with `FIRST_MIGRATABLE ≤ b ≤ HEAD−1`, stamped or unstamped-legacy, proceeds to minting
  `b → b+1`.** `FIRST_MIGRATABLE` is 1 at this head (every version 1..16 has accepted-shape evidence in
  `src/veracium/store/evidence/schema_versions.json`, and the kernel defines a step from each). A future head that drops
  an old base raises it; bases below it then return `unsupported-base`, the only cell that can produce the outcome.
- `current` (clean, and with repair), and every refusal cell, are as today. The preflight stays read-only: it never
  stamps an unstamped store. It judges the store against the BUILD's head; only a delegated rung is target-relative.
- The release record is not consulted.

##### 4j.6.4b. `PreflightResolution` (amends 0018 §4b)

`resolved_base ∈ {FIRST_MIGRATABLE … HEAD−1}`. Its exact-type admission, the fingerprint and I18's reason-labeling-only
pin are unchanged.

##### 4j.6.4c. The mint (amends 0018 §4c; R1-01)

`mint_release_authority` re-observes the store itself and mints `from_version = b`, `to_version = b+1` when, **by its
own observation**:
- the store is stamped `b`, `1 ≤ b ≤ HEAD−1`, and `digest(objs, b) ∈ accepted_digests(b)`; or
- it is unstamped, has objects, and `resolve(objs, version_records(), candidates=legacy_base_versions())` returns `b`,
  `1 ≤ b ≤ HEAD−1`.

`source_digest = digest(objs, b)`. **The resolved base, the raw stamp and the source facts:** the authority's
`from_version`, the terminal record's `from_version` and the attempted event's source are all the RESOLVED base `b`
(the pin's kernel already records the hook's `base`: `src/veracium/store/migration.py` L817–822); the raw stamp (0 for
a legacy store) is reported only in `RungReport.source_stamp`.

I18 is unchanged: `resolved` labels a failure and decides nothing. A forged `PreflightResolution` cannot make a refusing
store mint, and cannot stop an eligible one. The retry sequence (three mints, re-resolution after the first two only)
is unchanged and is per rung.

The amendment's §4d (its marked 0007 and 0013 amendments) is 0007 §4h (§4d-i) and 0013 §5g (§4d-ii, §4d-iii).

##### 4j.6.4e. Results and routing (amends 0018 §4e and §4f)

###### 4j.6.4e-i. The laws, per rung

0018 §4e's deference law is unchanged: a delegated carrier carries its terminal record's facts verbatim, and is valid
iff those facts pass 0013's `problems()` **at the minted endpoints `(b, t)`**. Wherever 0018 §4f and the code use
`(_MINT_BASE, _HEAD)`, a rung uses its minted `(b, t)` (§2a). The no-record rows, the retry-unsafe
`migration-audit-state-unknown`, the readback routing and the loud escapes are unchanged, per rung.

**The v0.2.2 sentence "`current` carries HEAD" is withdrawn.** A PREFLIGHT `current` carries HEAD. A DELEGATED `current`
carries its record's `t`. They are told apart by `RungReport.kind`, never by the label (R1-04).

###### 4j.6.4e-ii. Inside one rung's transaction (`BEGIN IMMEDIATE`, authority `b → t`, `t = b+1 ≤ HEAD`)

Facts are `TerminalFacts(outcome, b, t, changed, committed, state, version)`; every row's facts pass the pin's
`problems()` at four rungs (§2c-ii row 4). "Existing" means 0013's own cell with endpoints `(b, t)`.

| # | observed in the transaction | outcome | facts `(changed, committed, state, version)` |
|---|---|---|---|
| 1 | stamped `t−1`, accepted at `t−1` | the hook brings it to `t`; stamp, accepted digest and drift checked against `t` → `migrated` | `(True, True, destination, t)` |
| 2 | **unstamped, with objects, resolving through `legacy_base_versions()` to `t−1`** (R1-01) | as row 1; the stamp written is `t` | `(True, True, destination, t)` |
| 3 | stamped `t−1`, shape not accepted | `stamped-shape-mismatch` (existing) | `(False, False, unaccepted, None)` |
| 4 | **stamped `t`, accepted, no drift** (another operation reached the target) | `current` | `(False, False, destination, t)` |
| 5 | stamped `t`, accepted, rebuildable drift | repaired against `t` → `current` | `(True, True, destination, t)` |
| 6 | stamped `t`, shape not accepted | `stamped-shape-mismatch` | `(False, False, unaccepted, None)` |
| 7a | stamped `0 < found < t−1` | the hook refuses → `migration-source-missing` ("no accepted v{t−1} source where the authority attests one; observed v{found}"); nothing written | `(False, False, unaccepted, None)` |
| 7b | stamped `t < found ≤ HEAD` (only when `t < HEAD`) | `newer`, diagnostic "v{found} is newer than this rung's target v{t}", scoped to the rung's target and never with an "install a newer build" remedy (round 2's answer); nothing written, never a backward step. The rerun's preflight reports `current` at HEAD when the store is there | `(False, False, unaccepted, None)` |
| 8a | unstamped, resolving to a base other than `t−1` and `t` | the hook refuses → `migration-source-missing` | `(False, False, unaccepted, None)` |
| 8b | unstamped, resolving to exactly `t` | **unreachable at this head**: resolution uses `legacy_base_versions()` = `{1}` and every `t ≥ 2`, so the store takes row 9. `allow_adopt=False` stays as a defence (it would be `adoption-refused`) | — (I15 and I37 assert unreachability) |
| 9 | unstamped, resolving to nothing | `foreign-shape` (existing) | `(False, False, unaccepted, None)` |
| 10 | unstamped with no objects (an empty replacement) | the `new=` hook refuses → `migration-source-missing` (closes M2) | `(False, False, unaccepted, None)` |
| 11a | **nothing at the path** | opened without creating (`mode=rw`): refused at the open, nothing appears on disk → `migration-source-missing`, state `missing` as in the preflight's own row for nothing at the path (closes M3) | `(False, False, missing, None)` |
| 11b | `found > HEAD`, `found < 0`, unopenable, locked, a refused runtime | existing | existing |
| 12 | a step's postcondition fails inside the hook | `unsupported-migration` (0013 §4f, M123); rollback; the store keeps its original raw stamp (`t−1`, or 0 for an unstamped first rung) | `(False, False, unknown, None)` |

*Annotation (research, 2026-11-06; the table above is kept as written): Row 3 is decided by the check after the hook: no check of the source's shape precedes the step. So the step has run and its attempted event stands in the sidecar beside the terminal record, though the transaction rolled back, and I38's "no attempted event" does not reach this row. A difference the step itself meets ends before that check, with no attempted event: row 12 when a postcondition fails, `migration-failed` with `(None, None, unknown, None)` when its SQL fails. Measured over 958 forms at every rung, the store is left as it was in each, and no source unaccepted at `b` is migrated.*

**A third, glossed `migration-source-missing` row (marked amendment to 0018 §4e).** Accepted §4e has two rows under
that label: nothing at the path (`missing`), and an existing, valid, empty `user_version=0` database (`unaccepted`,
R2-3). Rows 11a and 10 are those two, verbatim. Rows 7a and 8a add a third:

> | `migration-source-missing` (a store EXISTS at an accepted version other than the authority's source, observed
> inside the rung's transaction) | False | False | `unaccepted` — **rejected as THIS operation's source**: the store
> was read and may be valid at its own version, but it is not the `b` the authority attests | None |

The diagnostic names the observed version ("observed v{found}"). The label stays 0013's returnable vocabulary, so
`TerminalFacts`, the terminal domain and I15's oracle need no new member. `unaccepted` here means rejected as this
operation's source, not rejected as a store; §4e's gloss on `source` (read-and-accepted) and `unaccepted`
(read-and-rejected) is read relative to the operation.

**What the transaction binds: the base and the shape, not the content.** A swap at the same version and shape (different
rows) is not visible; `source_digest` digests the shape. That is accepted 0018's Limit under quiescence, unchanged. Row
1 is not an identity binding.

**Why rows 7 and 8 refuse rather than follow the store:** a store anywhere but `t−1` or `t` is outside what this
authority attests; following it needs a different authority, and moving it backward is not a migration. The walk's next
call re-observes the store, and the base expectation (§4e-iii) decides whether that is progress.

###### 4j.6.4e-iii. The operation context: `RungReport` and `run_release_rung` (R1-03)

`run_release_rung(path, *, host_attestation, expect_base=None) -> RungReport` is package-private.
`run_release_migration(path, *, host_attestation)` keeps its signature and public `MigrationResult`, and returns
`run_release_rung(path, host_attestation=…).result`.

`RungReport` is a `NamedTuple`, admitted by exact type, with a validating constructor:

| field | type | `kind == "preflight"` | `kind == "delegated"` | `kind == "unexpected-base"` |
|---|---|---|---|---|
| `kind` | exact `str` | | | |
| `result` | exactly `MigrationResult`, or `None` | a §4e preflight row (incl. `mint-contention`, `invalid-request`) | a delegated row | `None` |
| `preflight_base` | `int` or `None` | the resolved base, or `None` when nothing resolved | the base this call's LAST resolution gave | the base it resolved |
| `source_stamp` | `int` or `None` | the raw `user_version` read, or `None` | the same | the same |
| `operation_id` | `str` (0013's token grammar) or `None` | `None` | the minted id | `None` |
| `from_version`, `to_version` | `int` or `None` | `None` | the minted endpoints: adjacent, `FIRST_MIGRATABLE ≤ from < HEAD` | `None` |
| `expected_base` | `int` or `None` | the argument | the argument | the argument; differs from `preflight_base` |

**Binding.** A delegated `RungReport` is valid only if its result is a 0018 no-record row, or
`TerminalFacts(result.outcome, from_version, to_version, …facts).problems()` is empty. The record binds to the MINTED
endpoints, never to endpoints rebuilt from `resulting_version`: a lawful `(13, 14, migrated)` validates under `13 → 14`
and fails under `14 → 15`.

**`MigrationResult`'s domain** becomes: the preflight rows; the no-record rows; every delegated carrier lawful at SOME
rung `(b, b+1)`, `FIRST_MIGRATABLE ≤ b ≤ HEAD−1`. It is enumerable, so I15's oracle still enumerates it, and the pin's
refusal of a lawful `(migrated, v14)` ("a committed change is at version 16") disappears.

**`expect_base` is checked inside the rung entry, before any authority is used:** after the first resolution, after
each retry re-resolution, and against the minted authority's `from_version` before delegation. A mismatch returns
`unexpected-base`. An authority minted and not delegated is discarded: minting writes nothing, and the attempted insert
is the consumption.

**Escapes carry the context.** Every escape raised after a mint (`MigrationAuditWriteError`, `MigrationAuditReadError`,
post-mint `PackageConsistencyError`) carries a validated `rung_context = (operation_id, from_version, to_version)`; a
pre-mint `PackageConsistencyError` carries `rung_context = None`. No id is ever parsed out of a diagnostic.

##### 4j.6.4f. Routing (0018 §4f): unchanged in its rules, per rung, at the minted endpoints (§4e-i).

##### 4j.6.4g. The CLI contract (amends 0018 §4g)

`veracium migrate --db X --i-have-quiesced --backup REF`. The flags, the usage exits and the attestation grammar are
unchanged. The walk:

```
expect = None; committed = []
loop:
  rep = run_release_rung(path, host_attestation=A, expect_base=expect)   # the ONE attestation object, every call
  preflight current (at HEAD, with or without repair)  -> print; exit 0      # the head-level check: the ONLY exit 0
  preflight refusal, mint-contention included          -> §7 P1, P2, P4; exit 1
  unexpected-base                                      -> §7 P3; exit 1
  delegated:
      if the record's facts are (True, True): committed.append(rep.operation_id)   # FIRST, whatever the outcome
      if outcome in (migrated, current) and resulting_version == rep.to_version:
          print "rung v{from} -> v{to}: {outcome} (operation {id})"
          expect = rep.to_version; continue          # §7 U0: an unchanged current at t continues, uncounted
      else                                         -> §7's classifier (N, C2, K, U); exit per 0018 §4g
  escape:
      if its validated facts are (True, True): committed.append(rung_context.operation_id)
          # the facts it carries (E1), or a readback BOUND to the escape (E4), validated before counting
                                                   -> §7 E1-E4; exit 3, with rung_context, or "pre-mint"
```

**The bound holds by construction, before any mutation.** `b₀` is the first report's `from_version` (that call's own
resolution, not a second CLI observation). `expect` rises by exactly one per continued rung from `b₀+1`. When it
reaches HEAD the next call can never mint: HEAD is not a mint base, and a mint cell at any other base is
`unexpected-base`. So a walk makes at most `HEAD − b₀` rungs and no counter is needed. A rung that reports `migrated`
without the next resolution reaching its `to_version` is the `unexpected-base` stop.

**Counting comes before the continuation decision** (R2-01). An operation id enters `committed` when its validated
facts are `(True, True)`, whatever its outcome, so a committed `internal-error` (accepted 0018 §4e retains
`internal-error/True/True/destination/t`) is counted once and still STOPS the walk; counting never makes it a
success. Each id is appended at most once: a report is either continued or stopped, never both.

**One counting rule for every way a rung ends:** an operation id enters `committed` if and only if its validated facts
are `(True, True)`. For a delegated report the facts are its record's; for an escape they are the facts it carries
(`MigrationAuditWriteError`, §7 E1) or a readback bound to the escape (a post-mint `PackageConsistencyError`, §7 E4:
a valid `package-inconsistent` record at the minted endpoints, per 0018 §4f(7), checked before counting). A store that advanced is counted however the walk ended. A `MigrationAuditReadError` (§7 E2) has no validated
facts, so its id is not counted, and the last lines say that the store may be at `t` regardless.

**The last lines** state how many rungs THIS walk committed, with their ids, counted by facts `(True, True)` and never by
printed lines; the stopping row's action id and its prose (§7); whether a rerun is safe, from that row; and the
store's version, or `unknown`, or (E2) a labelled derived state.

The documented exits stay: **0** = the store is `current` at HEAD at the end · **1** = a refusal, or an
`unexpected-base` stop · **2** = usage · **3** = a loud escape.

**The carriers ruled to ride this amendment.** At the pin they are ONE carrier and its relay: the open refusal's text
(`src/veracium/store/schema_version.py`, the "opening does not migrate" refusal) and `doctor`'s finding, which relays it
verbatim. In the same commit as the CLI change, the refusal names `veracium migrate --db … --i-have-quiesced --backup
REF` for every base `≥ FIRST_MIGRATABLE`, replacing the 0.30.0 interim text. `doctor` follows through the relay.

##### 4j.6.4h. Beside the amendment (not normative here)

The release record's eight null `store_schema_version`/`digest` entries are filled by re-running the record's generator
against those tags, never by hand. No mint rule reads the record; completing it is evidence hygiene, dev's to schedule.

### 4j.7 Regimes (the amendment's §5)

- **A released store below HEAD−1.** Before: `unsupported-base`, exit 1. After: a walk of `HEAD − b` rungs, exit 0.
  0.26.x (v14) takes two rungs; 0.1–0.4.8 (v1, unstamped) takes fifteen.
- **A HEAD−1 store:** one rung, the same operation as today, with the same facts. Its authority digest now names its own
  steps.
- **An interrupted walk:** the store is stamped and accepted at the last committed rung's version. **Where the
  stopping rung's §7 row permits a rerun, rerunning `migrate` with the migrating build or a newer one resumes it**
  (R1-07, as ruled). A known version alone does not permit it: §7's N2, N4, U1, U5, E3 and E4 prohibit a rerun until the record
  is queried, the build repaired or the store restored, and C2, K, U3, U4, U7 and E2 ask for an inspection first
  (R2-01, R3-01). **No claim is made that an older
  release can read it:** the rung kernel uses the current record models, and the 2→3 conversion drops
  `provenance.source_type`, which accepted 0016 records that pre-D2 readers require. The pre-walk backup is the way back.
- **Clock reads across a walk.** A walk reads the clock once per rung, so the v2→v3 `observed_at` fill, the v13 store
  epoch's `started_at` and the v16 registry's `written_at` carry their own rungs' values, where a one-call
  `migrate_store` gives them one. 0013 §4f B1 holds per operation. **Each value equals its own operation's injected
  clock read; no order or inequality across operations is required, since separate reads may be equal or move
  backward** (the reviewer's precision note). The reader census (two readers of `started_at`, both per-operation,
  `doctor.py` L238 and the `migration.py` postcondition at L458–460, checked at L764) is unchanged, and the reviewer
  found the same two.
- **Ordinary opening** is unchanged, including its two distinct refusals: a stamped below-head store raises
  `PackageConsistencyError`; an unstamped resolved legacy store raises `StoreVersionError(reason='migration-required')`.
- **Scale:** a walk of `n` rungs does `n` transactions where the library jump does one. Not measured, and stated.

### 4j.8 Invariants (the amendment's §6)

I14, I16–I18 and I20–I23 are unchanged. I13, I15 and I19 are restated; I33–I39 are new (0018 uses up to I32, §4i).

| invariant | executable check | mutant that must fail |
|---|---|---|
| **I13′** the preflight matrix is total. Every resolved base `FIRST_MIGRATABLE ≤ b ≤ HEAD−1`, stamped or unstamped-legacy, mints `b → b+1`; every other cell is as frozen I13; no cell produces `unsupported-base` at this head | `test_preflight_matrix_total`, re-parametrised over every base and the legacy unstamped v1 (each mints, endpoints asserted), plus every frozen non-mint cell | mint only from HEAD−1; mint `b → HEAD`; mint only a stamped store; consult the release record |
| **I15′** the result domain | the independent oracle enumerates the widened `MigrationResult` domain (§4e-iii) and `RungReport`'s binding: a lawful record validates at its minted rung and fails at any other; row 8b's unreachability is asserted. **Admission is separate from validity** (round 3): the oracle admits by route, the ordinary delegated route admitting `TERMINAL_OUTCOMES` less the audit-only `package-inconsistent`, which only §7 E4 admits; a lawful septuple alone admits no label | validate at `(HEAD−1, HEAD)`; bind to endpoints rebuilt from `resulting_version`; admit `package-inconsistent` on the ordinary route |
| **I33** every rung from every base lands on a shape accepted at `b+1`, passes its postconditions, and keeps its rows | `test_every_rung_from_every_base`. (i) The empty-store walk of §2c-ii row 1 through the implemented rung kernel. (ii) **Populated:** for each released base, fixtures written by that release's own code (a `git archive` of its tag; raw unstamped stores included; transformed tables populated; ALTER-derived starting shapes as well as fresh constructors), with the generator, source tag/commit, dependencies and hashes recorded; walked to head; rows compared with the direct jump of the same fixture, every column except the declared clock values, which each equal their own rung's clock read. (iii) **Every head-bound reference moves** (R2-03): the generated census of `SCHEMA_VERSION` references in the forward step's reach (§2a: `_apply_forward`, the functions it calls and the constructors of the errors it raises) equals its committed expectation; and with each frozen ALTER-output expectation deliberately mismatched at 5→6, 7→8 and 9→10, the refusal reports expected 6, 8 and 10 (and 16 at both v16 raises on the last rung) | the target ignored by the additive diff; a guard bound to HEAD; the stamp written as HEAD; **any one of the v6, v8 or v10 refusals left head-bound** (each its own mutant: the lower-target control reports 16) |
| **I34** the CLI walk is bounded, bound to its expectation, and reported per rung | `tests/test_migrate_cli.py`: a v13 store walks three rungs, three distinct ids, three records, exit 0; a populated and an unstamped v1 walk fifteen; a store at HEAD makes none, exit 0; a store moved down between rungs stops with `unexpected-base` before a second mint; a row-4 `current` continues and is not counted; a pre-mint escape after two rungs prints no earlier id; one attestation object is admitted at every mint. **R2-01:** a lawful committed `internal-error` (`TerminalFacts("internal-error", 14, 15, True, True, "destination", 15)`) injected at rung 2 of a v13 walk STOPS the walk with §7 C2, and the final count lists rung 1's and rung 2's ids, each exactly once; the same for a committed `package-inconsistent` carrier; a `MigrationAuditWriteError` with committed facts is counted once; **R3-03:** a post-mint `PackageConsistencyError` whose readback is a valid `package-inconsistent` record at the minted rung with committed facts is counted once and prints its version as recorded; one whose readback has another outcome (e.g. `migrated`) or another lawful rung's endpoints adds no id and prints `unavailable (readback: …)`; an unchanged bound `package-inconsistent` adds no id; binding is checked before counting. **Row 7b:** a lower rung whose store a racing operation took to HEAD reports `newer` with the target-scoped diagnostic, and the rerun reports `current` | loop without the expectation; check it after the mint is delegated; count printed rungs; re-create the attestation per rung; **count only in the migrated/current branch** (the committed error drops out); count a committed error twice; continue past a committed error; **count a package escape's readback before checking that it is bound** (round 2's model accepted any readback of kind `record`) |
| **I35** an interrupted walk resumes, and its recovery is ONE total classifier | (i) **The final classifier is one executable function** returning §7's action ids. The exhaustive oracle enumerates every carrier `problems()` admits at rungs 1→2, 13→14 and 15→16, restricted to the outcomes each route admits, plus the four no-record outcomes and every preflight outcome, and requires **exactly one action id** for each; it prints the count per row. (ii) **The reviewer's equal-input pairs** get one conservative action each: `migration-source-missing`/`unaccepted` from an accepted v12 replacement and from an empty replacement → U3 for both; `newer` from a v15 store and from a v17 store under 13→14 → U4 for both. (iii) **R3-02's pairs**: the same carried facts as an ordinary record and inside a `MigrationAuditWriteError` (committed `migrated`, committed `internal-error`, unchanged `unsupported-migration`) receive the same store-side action id, plus `audit-record-not-published` for the escape; exit 1 vs 3 as §7 says; committed facts counted once in both. (iv) A postcondition failure at rung 2 of a v13 walk (an injected fault) leaves stamp v14, accepted, rung 1's record intact, rung 2 `unsupported-migration` with no store change, action `no-rerun-this-build`; **with the fault removed** (the build repaired), the rerun walks v14 → v16. (v) An unknown-facts rung prints `unknown`, never the previous rung's version; `migration-audit-state-unknown` says "do not rerun before querying the operation id"; a `MigrationAuditReadError` prints its derived state as a state and the version as `unknown` | leave a partial rung; print the previous rung's version on unknown facts; promise that rerun repairs a missing record; print `derived_resulting_state` in the version column; offer a rerun because a version is known; **the superseded blanket-unchanged retry** (every unchanged carrier → rerun); **the same-build postcondition retry**; an audit-write escape receiving a weaker action than its carried facts' (round 2's row 8); a cause chosen for U3 or U4 from diagnostic prose; any admitted input with zero or two action ids |
| **I36** a rung's `migration_digest` names its plan, and every operation executes exactly its plan | (i) per rung, the digest equals SHA-256 over the frozen preimage of `plan(t−1, t)`, checked against the vector file's preimages and entry lists. (ii) **The step-invocation trace** equals `plan(b, t)` for every completed operation, rung and direct, and is a prefix ending at the refusing entry for a refused one. (iii) **SQL attribution**: every write is attributed to its active entry and admitted by its declared kind, on populated v2 fixtures with 0, 1 and 2 legacy outcome rows (0, 1 and 2 writes under one `data` entry) and on I33's release-authored populated fixtures; an empty store alone cannot exercise a data write. (iv) **The direct route keeps its contract**: base 1 → 16 and v13 → 16 through `migrate_store` use the destination constructors, one clock read and one stamp, as at the pin (the reviewer's direct-versus-adjacent witness) | a helper-carried check dropped; one repeated v16 check dropped; two data steps swapped; the stamp check removed; a field encoded with a separator instead of its own segment; **an undeclared SQL write (no active entry); an undeclared dispatch; a nested check deleted; a direct route rebuilt as the concatenation of adjacent plans; a `data` entry issuing DDL or a PRAGMA; an ALTER moved under a neighbouring `data` entry (a mis-split); a direct byte check deleted; one statement of a frozen `ALTERS_*` tuple dropped; the clock read moved after the additive diff** |
| **I37** ordinary opening, `migrate_store` and the runtime gate are unchanged | a v15 store opened with no target raises `PackageConsistencyError` and an unstamped legacy one `StoreVersionError(migration-required)`; `migrate_store` on a v13 store reaches v16 in ONE operation with one clock read (`tests/test_0013_pa1_postconditions.py` unchanged and green); `migrate_to=HEAD` equals `None` byte for byte, with and without the hook; every non-int, `bool` and out-of-range target, and `t < HEAD` without the hook, refuse before the store is touched; a below-head rung on an attested build has the same runtime status as at HEAD | default `migrate_to` to `found+1`; let an ordinary open migrate to a target; let the target reach `runtime_status()` |
| **I38** a rung binds its source and never creates | at rungs 1→2, 13→14 and 15→16, the store changed between mint and transaction: to `t` (row 4), above `t` and to HEAD (7b), below the source (7a), unstamped elsewhere (8a), emptied (10), deleted (11a). Each gives its row's outcome and facts, the stamp unchanged, no attempted event, and nothing created on disk. M1 and M3 at the implementation give rows 7a and 11a. **E2-01:** for a store named with `?`, `#`, `%`, a space, and a supported non-UTF-8 name, each beside an accepted sibling whose name is its prefix, the rung migrates exactly the named file and leaves the sibling's bytes unchanged; an existing directory at the path is unopenable (row 11b), never `missing` | the binding put on `migrate_to` (the last rung unbound); `sqlite3.connect` without `mode=rw`; no `new=` hook; **the path interpolated into the URI unencoded; an `OperationalError` mapped to `missing`** |
| **I39** the closed write rules bind to the operation's target | the SA10 gate (`specs/evidence/0013/sa10_gate.py`) over the extended path inventory: every release base, the legacy fixtures, drift repair at an intermediate `t`. A correct lower target passes | writing HEAD instead of `t`; another historical constructor; a stamp of any valid version but `t`; a release base dropped from the inventory; the direct route losing its head-bound checks |
| **I19′** the CLI contract | as frozen I19 (flags, exits, the five exit-3 package routes), plus I34's walk cells | — |

*Annotation (research, 2026-11-06; the table above is kept as written): I13′'s re-parametrised cells landed beside `test_preflight_matrix_total`, not in it. `test_every_base_mints_its_own_rung_and_only_that_rung` takes every base, `test_unstamped_legacy_v1_resolves_without_stamping_and_takes_the_first_rung` takes the legacy v1, and `test_preflight_matrix_total` keeps the frozen non-mint cells. All three are in `tests/test_0018_orchestrator.py`.*

### 4j.9 Failure modes, recovery and reversibility (the amendment's §7)

Each rung's failure modes are 0013's, inside one transaction; its loud escapes are 0018's, per rung. A walk is not one
transaction: a walk that stops after `k` committed rungs has committed `k`.

**Recovery is ONE total function, the final classifier** (R2-01, R3-01). Its inputs are structured and nothing else:
the report's `kind` (`preflight`, `unexpected-base`, `delegated`) or the escape's type; the result's outcome; the
validated record facts, if the route has any; for an escape, the facts it carries or a readback bound to it (E1, E4).
**It never reads diagnostic prose.** It returns exactly one **action id** per input. The id is stable, and it is what
the implementation and the model return and what the check-to-row map compares; the prose beside it explains the id.
Where one structured input admits more than one cause (U3, U4), the action is a **conservative conditional**: stop,
inspect, and correct the condition before a rerun. The classifier never claims which cause happened.

**The fact classes** are keyed by `(store_changed, transaction_committed)` alone, never by a full septuple:
*committed* = `(True, True)`, *unchanged* = `(False, False)`, *unknown* = `(None, None)`. `TerminalFacts.problems()`
admits only these three (the two must be the same tri-state value), so every lawful carrier is in exactly one class;
the state and version are data the row prints. **Admission is separate from validity:** the ordinary delegated route
admits `TERMINAL_OUTCOMES` less the audit-only `package-inconsistent` (`_AUDIT_ONLY_OUTCOMES` at the pin), which only
the post-mint package escape (E4) admits. A lawful septuple alone admits no label to any route.

**Totality.** Every input reaches exactly one row: by kind first (P, N for the no-record outcomes, E for escapes), then
by fact class (C, K, U), then, within *unchanged*, by outcome, ending in the U7 fallback, which takes every unchanged
outcome no earlier row names, including any a later head adds. The exhaustive oracle enumerates every carrier
`problems()` admits at the oracle's rungs, restricted to the outcomes each route admits, plus the four no-record
outcomes (`_NO_RECORD_OUTCOMES` at the pin: `migration-audit-unavailable`, `migration-audit-state-unknown`,
`migration-quiescence-required`, `migration-evidence-missing`) and every preflight outcome, and requires exactly one
action id for each (I35).

**Exits** stay as 0018 §4g: 0 for P0 only; 1 for every other P, N, C2, K and U stop; 3 for every E row.

##### 4j.9.7a. Before delegation, and the no-record outcomes (no facts; nothing counted)

| row | input | action id | the CLI prints | rerun? | what the operator does |
|---|---|---|---|---|---|
| P0 | preflight `current` at HEAD (with or without repair) | `done` | the store's version, HEAD | — | nothing; exit 0 |
| P1 | preflight refusal, outcome `mint-contention` | `rerun-after-contention` | `unknown` | yes | rerun once the race settles |
| P2 | preflight refusal, outcome `invalid-request` | `fix-invocation` | — | yes, once corrected | correct the command line |
| P3 | `unexpected-base` (the store changed between rungs) | `rerun-when-quiescent` | "observed v{preflight_base} where v{expected_base} was expected" | yes, once quiescence holds | stop the other writer, rerun |
| P4 | any other preflight refusal | **the U row its outcome and state select** (U1, U2, U4, U5, U6 or U7), read as an observation made just now | as that row | as that row | as that row. **At preflight the cause is not ambiguous**, because the preflight's report is the observation itself, with no transaction between: `newer` means the store is beyond this build's head (U4's second branch, `no-rerun-this-build`); `migration-source-missing` with state `unaccepted` is an empty `user_version = 0` file at the path (U1, `no-rerun-not-a-source`) |
| N1 | `migration-audit-unavailable` | `rerun` | `unknown` | yes | rerun: the attempted record is proven not written and nothing was consumed |
| N2 | **`migration-audit-state-unknown`** | `query-id-first` | `unknown` | **NO** (0018 §4e, verbatim) | query the durable `operation_id` (`read_terminal`) before any rerun |
| N3 | `migration-quiescence-required` (refused before observation: an invalid, expired, consumed, retargeted or cross-build authority) | `rerun-when-quiescent` | `unknown` | yes, once quiescence holds; the rerun mints a fresh authority | stop the other writer, rerun |
| N4 | `migration-evidence-missing` (refused before observation: no current path record evidences this rung's migration, an artifact property) | `no-rerun-this-build` | `unknown` | **not with the same build** | repair or upgrade the build, then rerun; or restore the backup |

##### 4j.9.7b. A delegated report with a record, by fact class

| row | input | action id | the CLI prints | rerun? | what the operator does |
|---|---|---|---|---|---|
| C1 | committed, outcome `migrated` or `current`, at `to_version` | `continue` | "rung v{from} -> v{to}: {outcome} (operation {id})" | the walk continues | — (counted) |
| C2 | committed, **any other outcome** (at the pin: `internal-error`; `package-inconsistent` only through E4) | `stop-inspect-committed` | `v{version}`, labelled "recorded: committed with {outcome}" | **not automatically**: a committed error's facts can describe a store the operation itself created (the pin's M3 shape: a deleted store re-created empty at v16, recorded committed `internal-error`, whose facts read "at `t`" exactly as a real advance would), so a direct rerun could resume from an empty store and lose data silently. The no-create open closes M3 itself (§4e-ii row 11a); this row covers every committed error | counted once; the walk STOPS. Inspect the store; then rerun, which resumes from its actual version, or restore the backup |
| K | unknown | `stop-inspect-unknown` | `unknown`; **the previous rung's version is never reported as the store's** | not automatically | inspect the store; then rerun, or restore the backup |
| U0 | unchanged, outcome `current`, state `destination` at `t` (another operation reached the target) | `continue-uncounted` | as C1 | the walk continues | — (not counted) |
| U1 | unchanged, outcome `stamped-shape-mismatch`, `foreign-shape`, `invalid-version` or `invalid-store` | `no-rerun-not-a-source` | the record's version, or `unknown` | **not as it stands**: a rerun meets the same store and refuses the same way | inspect; restore the backup or repair the store, then rerun |
| U2 | unchanged, outcome `migration-source-missing`, state `missing` (nothing at the path, by 0013's `lstat` ENOENT) | `fix-path-then-rerun` | `unknown` | yes, once the path holds the store | correct the path or restore the backup, then rerun |
| U3 | unchanged, outcome `migration-source-missing`, state `unaccepted` | `conditional-other-writer-or-path` | `unknown`, with "the source changed or is empty; this report does not say which" | **not until inspected**: this one input arises from an accepted store at another version (§4e-ii rows 7a, 8a) and from an empty replacement (row 10), and the report carries nothing that tells them apart | stop; inspect the path's version. If it is an accepted store at another version, stop the other writer and rerun; otherwise restore the backup or correct the path |
| U4 | unchanged, outcome `newer` | `conditional-other-writer-or-newer-build` | `unknown`, with "the store is newer than this rung's target; this report does not say by how much" | **not until inspected**: this one input arises from a store another operation moved above the target but within this build's head (§4e-ii row 7b) and from one beyond the build's head | stop; inspect the store's version. At or below this build's head, stop the other writer and rerun (the preflight resumes it or reports `current`); above it, use a build whose head reaches it |
| U5 | unchanged, outcome `unsupported-migration` (§4e-ii row 12: a step's postcondition failed), `unsupported-sqlite` (a refused runtime) or `unsupported-base` (a store below this build's lowest migratable base; after this amendment no cell produces it at this head, §4a) | `no-rerun-this-build` | the record's version, or `unknown` | **not with the same build or runtime**: the cause is deterministic, so a rerun fails the same way | repair or upgrade the build or the runtime, then rerun; for `unsupported-base`, first migrate with a release whose floor reaches the store; or restore the backup |
| U6 | unchanged, outcome `store-unopenable` or `locked` | `fix-access-then-rerun` | `unknown` | yes, once the cause is fixed | fix the permission, the path's type or the lock, then rerun |
| U7 | unchanged, **any other outcome** (at the pin, among others: `internal-error`, `migration-failed` and `migration-result-mismatch` with state `source` at the base, the reviewer's three; `adoption-refused`; `migration-required`; and any outcome a later head adds) | `inspect-first-fallback` | `v{version}` when the state is `source` or `destination`, else `unknown` | **not until the cause is identified**: the store is unchanged by this rung, but the report does not establish why it refused | inspect the diagnostic and the build; correct the cause, then rerun |

##### 4j.9.7c. Escapes (exit 3): the escape adds restrictions and disclosure, never removes one

| row | input | action id | the CLI prints | rerun? | what the operator does |
|---|---|---|---|---|---|
| E1 | `MigrationAuditWriteError` (the terminal record not published) | **the 7b action of the facts it carries**, classified exactly as if they were the record, except that an escape never continues: C1 and U0 facts give `rerun-resumes-store`; C2, K and U1–U7 give their own 7b ids; **plus** the disclosure `audit-record-not-published` | as that row, plus the operation id and "its terminal record was not published; this tool does not repair it" | as that row: the audit loss never makes it less restrictive | as that row; also record the operation id. Counted once when its carried facts are committed |
| E2 | `MigrationAuditReadError` | `inspect-audit-trail` | version `unknown`; the error's `derived_resulting_state` printed separately, labelled derived-from-outcome (a state, never a version) | not until the record is inspected | inspect the audit trail for the id. **Not counted** (no validated facts), and the store may nonetheless be at `t`: the last lines say both |
| E3 | `PackageConsistencyError` before the mint | `repair-build` | `unavailable (pre-mint: no operation minted)`; no earlier id reused | no: the build is inconsistent | repair or reinstall the build |
| E4 | `PackageConsistencyError` after the mint | `repair-build`; and, when the bound readback's facts are committed, also `stop-inspect-committed` | a readback is used **only** when it is a valid record bound to this escape (0018 §4f(7)): outcome `package-inconsistent` at the minted endpoints, **checked before any counting**. Then its version, labelled recorded; otherwise `unavailable (readback: …)` | no, until the build is repaired | repair or reinstall the build; when the bound record is committed, inspect the store as C2 says. Counted once only for a bound, committed record; a record with another outcome or another rung's endpoints adds no id and no recorded version |

**What a rerun is promised for:** P1, P2 (corrected), P3, N1, N3, U2 and U6 once their condition holds, and E1's
`rerun-resumes-store` (C1 or U0 facts). Every other row asks for an inspection first (C2, K, U3, U4, U7, E2) or prohibits a rerun until its
condition is met (N2, N4, U1, U5, E3, E4), whether or not a version is known.

**Reversibility** is 0013's: the one backup the operator took before rung 1 (`--backup REF`) returns the store to its
pre-walk version, for every row. The amendment adds no reverse step and does not claim that no inspection step is ever
needed.

### 4j.10 Claims and limits (the amendment's §8)

**Claim (for the CHANGELOG):** *"`veracium migrate` now upgrades a store written by any earlier release, one schema
version at a time, each step its own audited operation. If a walk stops part-way, its last lines say why and whether
running `migrate` again is safe; where they say so, running it with this release or a newer one resumes the walk, and
otherwise they say what to inspect first. A part-walked store is usable only by migrating it with this release or a
newer one, or by restoring the backup you took before the walk."*

**Limits:**
- the attestation is the host's assertion, unchanged; a racing writer is detected only where §4e-ii's rows see it, and
  a same-version, same-shape swap is not seen;
- a walk does `n` transactions, where the library call does one;
- each per-rung clock value comes from its own rung's clock read, so values may be equal, increase or move backward
  across rungs (§5);
- an audit record missing after a committed rung (§7 E1) is reported, not repaired;
- no older release is claimed to read an intermediate store;
- the populated-data guarantee is I33's, at implementation; the design evidence is shape-only plus a model.

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
| **I13** the preflight matrix is TOTAL: bases 1–5 → `unsupported-base` + the ladder; clean-current → `current` (False, False, destination, 7) byte-identical; current-with-repair → `current` (True, True, destination, 7) via the one shared opening path; missing/foreign/malformed/unstamped/newer/locked → the corresponding refusal without minting; every short-circuit zero-authority/zero-audit; resolved base 6 ALONE mints and delegates | `test_preflight_matrix_total` (every cell incl. both current cells and locked) + `test_below_v6_base_refuses_with_the_ladder_message` (all five bases) + `test_below_v6_open_unchanged` + `test_base_6_proceeds_through_the_audited_operation` | CI · **v9:** restated as I13′ (amendment `0018-adjacent-rungs`, §4j.8) |
| **I14** the mint race closes by the EXACT §4c sequence (pinned by external R3-3 after R2-8's fix missed this carrier) | `test_mint_race_reclassifies` — EXACTLY three resolves and three mint calls, interleaved resolve→mint, with re-resolution after failures one and two ONLY and NO resolve after the third failure; each of the first two `MintError` reasons re-resolves to the now-true outcome; the third → `mint-contention`, facts `(False, False, unknown, None)`, three attempts named in the diagnostic — never proceed-to-mint, never a fourth resolve (call-count asserted, not inferred) | CI |
| **I15** `MigrationResult` carriers are table-only | `test_migration_result_truth_table` — the LITERAL §4e table: every preflight row (all FIFTEEN, incl. both `migration-source-missing` forms — R2-3), the delegated DEFERENCE law (a record-bearing carrier is valid iff its seven-field `TerminalFacts` passes accepted 0013's `problems()` verbatim, tri-state effects included — R2-2), and the four fixed `(False, False, unknown, None)` no-record rows (R2-9); the validating constructor rejects every out-of-table carrier incl. every non-vocabulary state word. **Gate-extension obligation: the validator joins `tests/test_0013_presend_gates.py`'s independent-oracle pattern — a separately-written oracle enumerates the §4e domain and the exhaustive diff must be empty** | CI · **v9:** restated as I15′ (amendment `0018-adjacent-rungs`, §4j.8) |
| **I20** the two new outcomes are returnable, never terminal (external R1-5) | `test_new_outcomes_are_excluded_from_terminal_facts` — the reviewer's probe as the regression: constructing `TerminalFacts` (and attempting terminal publication) with `unsupported-base` or `mint-contention` REFUSES; the extended independent oracle enumerates all FOUR exclusion cells (the two new members + the two never-terminal audit outcomes — R2-4's latent-0013-gap closure) AND the `package-inconsistent` inclusion cell; the explicit `TERMINAL_OUTCOMES` definition is asserted | CI |
| **I22** the fingerprint has an independent oracle (external R3-1) | `test_preflight_fingerprint_oracle` — a separately-written encoder (its own `identity`-equivalent and framing) reproduces the §4b fingerprint byte-for-byte on fixture stores incl. a generated-column store and a quoted-literal DDL store; the raw-`manifest()` serialization failure (tuple keys) is the named negative case | CI |
| **I23** `ReadbackResult` is a closed constructed carrier (external R3-4) | `test_readback_result_contract` — every cross-field-law violation, a hostile subclass of `ReadbackResult`, a hostile SUBCLASS OF `TerminalFacts` as `facts` (exact-type + the UNBOUND `problems()` call — the reviewer's dynamic-validator probe as the named regression), a list-typed `problems`, a mutable member inside `problems`, and an uncapped problem flood all REFUSE at construction; the malformed row's total construction yields ≥1 capped problem entry; a FORCED read failure (failed SELECT/open) maps to `malformed(read-failed: …)`, never a raise | CI |
| **I21** the delegated routing is total (external R1-4) | `test_delegated_routing_total` — for EVERY member of 0013's returnable vocabulary as a delegated return: record-present → facts verbatim; record-absent × the four no-record outcomes → the fixed rows, NO error; record-absent × every other outcome → `MigrationAuditReadError(missing)`; malformed × any outcome → `MigrationAuditReadError(malformed)`; a VALID record whose outcome differs from the kernel return → `MigrationAuditReadError(mismatched)` (R2-5); `PackageConsistencyError` propagates on BOTH routes (R3-5): pre-mint → no readback, `unavailable (pre-mint)`; post-mint → readback with the record accepted ONLY when valid AND bound to `package-inconsistent` (any other outcome → `unavailable (readback: mismatched)`); absent/malformed → unavailable — stderr facts labeled recorded or unavailable, never invented | CI |
| **I16** the attestation contract is exact | `test_attestation_contract` — absent, coerced (`quiesced=1`/truthy object), grammar-violating (incl. embedded space), duck-typed, and HOSTILE-SUBCLASS cells (R14-4; `type(x) is` admission, the 0013 authority-regression pattern) | CI |
| **I17** audit failures are loud end-to-end | `test_audit_read_error_is_loud` — a missing record under a record-guaranteed outcome, and a malformed record under ANY outcome, raise `MigrationAuditReadError` whose validated carrier reaches CLI exit 3 with `derived_resulting_state` labeled derived-from-outcome on stderr; the existing `MigrationAuditWriteError` path and the newly-dispositioned `PackageConsistencyError` share the exit-3 loud-escape class, never exit 0. **Gate-extension obligation: the readback boundary, the no-record routing branch, and the mint-retry loop are NEW failure seams — they join `test_every_fault_seam_preserves_the_invariants`'s injection list** | CI |
| **I18** the resolution evidence is reason-labeling only (internal F3; test form corrected by external R2-7 — the v3 regression demanded unconditional refusal, which would itself have made the evidence authority-relevant) | `test_resolution_is_reason_labeling_only` — forged vs genuine `resolved` compared under BOTH real-store conditions: with a VALID store + attestation, mint SUCCEEDS identically under forged evidence (an authority IS granted — forgery must not deny either); with a FAILING store, mint fails identically, and at most the `MintError` reason label differs; PLUS the recursive-exactness cells (closure obligation 2): `resolved_base=True` and hostile `str`-subclass scalars REFUSE at the `PreflightResolution` boundary before any comparison runs | CI |
| **I19** the CLI contract | `tests/test_migrate_cli.py`, amended under this spec's authority (§7a): flags required on the migration path (missing → exit 2), invalid `--backup` → exit 2 with the grammar, exits 0/1/2/3 as §4, reporting from structured fields only — **and the exit-3 package routes enumerated as five named cases (closure obligation 4): pre-mint · bound `package-inconsistent` (recorded facts) · mismatched · missing · malformed, each with its exact stderr form** | CI · **v9:** restated as I19′ (amendment `0018-adjacent-rungs`, §4j.8) |

**v7: I24–I32, the data-migration operation's invariants, are §4i.8**; I13–I23 above are unchanged. **v9: I33–I39, the adjacent rungs' invariants, and the restated I13′, I15′ and I19′ are §4j.8** (amendment `0018-adjacent-rungs`).

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
| 0018-adjacent-rungs ext 1 (v0.2.2) | R1-01..R1-07 (round 1 returned the contract for amendment; banked verdict sha16 `65425b2b1eb6b4e5`) | v0.3 (research `91a04864`..`28de0a4f`, v0.3.4); round 2's verdict closed R1-01..R1-04 and R1-07 and partly R1-05, R1-06 (banked verdict sha16 `b5723ec25e5fc57a`) |
| 0018-adjacent-rungs ext 2 (v0.3.4) | R2-01 committed-error accounting · R2-02 I36's trace units and the direct route · R2-03 three head-bound refusals · E2-01, E2-02 · two text repairs (banked verdict sha16 `b5723ec25e5fc57a`) | v0.4..v0.4.4 (research `b5a78c1b`..`b657699d`); round 3's verdict closed R2-01's counting, R2-02, R2-03, E2-01, E2-02 (banked verdict sha16 `0235b70c17012766`) |
| 0018-adjacent-rungs ext 3 (v0.4.4) | **ACCEPTED WITH AMENDMENTS** (banked verdict sha16 `0235b70c17012766`), closed internally under PROCESS.md §4a on the owner's ruling: **R3-01** the final recovery split · **R3-02** an audit-write failure weakening recovery · **R3-03** the package-escape control counting an unbound record · the three reconciliations (the census's reach in I33 (iii); I35's resume clearing its fault; admission separate from validity) | v0.5, v0.5.1 (research `ac7f7d3f`, `7a2e150f`): §4j.9's total classifier with action ids, E1, E4, I15′, I33 (iii), I35 (iv). **Executable, run by both seats** from a `git archive` of 67bbba6 with `PYTHONPATH=src`: `python3 specs/evidence/0018-adjacent-rungs/closure/model_v05.py <new dir>` (143 ok, 0 not ok, 3 inexpressible; R3-01: the exhaustive oracle, the reviewer's four carriers, both equal-input pairs; R3-02: four transport pairs; R3-03: the bound positive, two unbound negatives, the zero-count; I35 (iv); twelve mutants killed) and `python3 specs/evidence/0018-adjacent-rungs/closure/check_row_map.py specs/evidence/0018-adjacent-rungs/closure/model-v05-run-67bbba6.jsonl specs/evidence/0018-adjacent-rungs/closure/recovery-table-v051.json` (57 checks, 0 disagree, 24 of 24 rows; `--control` exits 1), with `specs/evidence/0018-adjacent-rungs/closure/recovery_v05.py` and `specs/evidence/0018-adjacent-rungs/closure/extract_table.py` beside them and `specs/evidence/0018-adjacent-rungs/closure/check-row-map.md` their output; research's runs on its own export (veracium-research commits 617a17a3, 4bfedbdd and 657d4bc4, cited without backticks so that no check reads them as a digest of the paths above), including an independent classifier read from the text (341 inputs, 0 differences); the reconciliations by the text diff v0.4.4 → v0.5.1; and this fold |
