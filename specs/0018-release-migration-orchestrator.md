# Feature spec: the release-migration orchestrator

Spec-Status: draft
Spec-Requires: 0007, 0013, 0016

| | |
|---|---|
| **Author / session** | dev |
| **Version** | v2 — INTERNAL ROUND 1 (research, 2026-08-13, `veracium-research/proposals/0018-internal-review.md`): RETURN FOR AMENDMENT, 3 findings, none rejecting the design; all folded here. **F1 (class D, cross-carrier contradiction — found-in-fix of the split itself):** R13-3's readback rule ("audit-unknown facts, never an error") and R14-3's loud-readback rule contradicted over the same input; the R13-3 branch was DEAD (every `read_terminal` call site is post-`record_terminal`-success) → research's option (a) taken: the integrity check lives at the read boundary, R13-3's "never an error" DELETED (§4), the dead phrase added to `withdrawn_phrases.py`. *Pre-send miss diagnosed: R14-3 was folded into §4b at the split without sweeping §4 for the carrier it contradicted — checklist item 5 skipped under split-night pressure; the registry entry is the mechanized check.* **F2 (class C, completeness):** §2/§2c/§3/§3b/§5–8 were forward-references ("transfers at the next revision") — a spec that isn't self-contained can't be adversarially reviewed; ALL sections now INLINED (from the reviewed 0016 v17 material, adapted to this spec's boundary). **F3 (§10 Q1 RULED by research):** `PreflightResolution` IS caller-suppliable (it enters the production mint API) → its §2c row added with the bounded-damage analysis AND the load-bearing pin: mint treats it as reason-labeling evidence ONLY, never authority-relevant (§4b, I-table) — else it is a TOCTOU. Research confirmed none of F1–F3 moves the frozen 0016-facing policy: **the atomic 0016+0018 acceptance path stands.** |
| **Status** | *narrative only — canonical is the `Spec-Status:` line* |
| **Internal reviewers** | research — round 1 RETURNED 2026-08-13 (3 findings, folded in v2); re-review requested on this revision |
| **External review** | required (full spec — the executable surface: `store/migration.py`, `cli.py`, the 0013 amendments); not yet sent |
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
| `MigrationResult` | frozen: `Outcome`-label string-compare + `store_changed: Optional[bool]`, `transaction_committed: Optional[bool]`, `resulting_state` (0013 vocabulary verbatim), `resulting_version: Optional[int]`, `diagnostic: str`; a validating constructor REJECTS every out-of-table carrier (§4b table is the domain) | CLI reporting; hosts — facts never inferred from the label (0013 r8-f3) |
| `mint_release_authority(path, attestation, *, resolved) -> MigrationAuthority`, raising `MintError(reason)` | the production mint API; closed reason enum {`source-missing`, `source-unaccepted`, `source-changed`}; `resolved` is reason-labeling evidence ONLY (§2c row, §4b pin) | the orchestrator; host-reachable (which is why §2c carries its rows) |
| 0013 `Outcome` vocabulary | +2 members by marked amendment: `unsupported-base`, `mint-contention` — both preflight-side, zero audit rows, no terminal-facts mapping | 0013's exhaustive outcome tests, extended |
| `read_terminal(operation_id) -> TerminalFacts` | 0013-amendment readback: own-operation, same-connection post-`record_terminal`; **missing/malformed there raises `MigrationAuditReadError`** (§4 — the F1 fold) | the orchestrator's delegated-outcome facts |
| CLI `migrate` | gains `--i-have-quiesced` + `--backup REF`; exits 0/1/2/3 | operators; `tests/test_migrate_cli.py` re-dispositioned §7a |

## 2c. Untrusted inputs — REQUIRED, blocking

*(The below-v6 and attestation rows are the 0016 v17 rows, reviewed in its
rounds 10–14, transferred; the `PreflightResolution` row is NEW — the F3
ruling.)*

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant that pins it |
|---|---|---|---|---|---|
| `path` (caller-supplied) | missing file → the missing refusal outcome, no minting | foreign/malformed/unstamped → the corresponding 0007/0013 refusal outcome, no minting | newer-than-head → the newer refusal, no minting | a path racing with concurrent writes | the preflight matrix is TOTAL (I13); the preflight→mint race closes by reclassification (§4b), never by trusting the first resolution |
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

## 4. Behaviour — the construction (from 0016 v17, five rounds hardened)

  release first — the two-release ladder"). **The exact public contract
  (R8-1, construction per R9-1 — v12's form was IMPOSSIBLE under 0013's
  authority/audit machinery):** the release migration
  **ORCHESTRATOR/PREFLIGHT**, before ANY authority minting, resolves the
  base; for bases 1–5 it RETURNS — never raises — the outcome
  **`unsupported-base`** with the ladder diagnostic verbatim. **It does NOT
  invoke `migrate_store`, mints NO `MigrationAuthority`, and creates NO
  0013 audit lifecycle** (no operation row, no attempted event, no terminal
  record — a terminal event is foreign-keyed to an authority-bound
  operation that never exists here). The store's bytes and stamp are
  byte-unchanged. **Base 6 alone proceeds through authority minting and the
  ordinary audited 0013 operation.** **The executable owner (R10-1, re-ruled by
  R11-1/R11-2):** **`run_release_migration(path: str, *, host_attestation:
  MigrationAttestation) -> MigrationResult`** in
  `src/veracium/store/migration.py`. `MigrationAttestation` is the
  HOST-OWNED interface — the quiescence attestation and backup reference
  0013 requires, passed VERBATIM into authority minting; the orchestrator
  never fabricates or defaults them (a path-only signature could not be
  honest). **The total matrix — the preflight intercepts EVERYTHING except
  resolved base 6:** bases 1–5 → `unsupported-base` with the ladder;
  already-current v7 → the `current` outcome WITHOUT minting (minting
  against a current destination is "not an accepted source" in the 0013
  instrument); missing path / foreign / malformed / unstamped / newer → the
  corresponding 0007/0013 refusal outcome WITHOUT minting; **resolved base
  6 ALONE mints an authority (host attestation passed through) and
  delegates to `migrate_store(path, authority)`** — 0013's revalidation
  inside the operation closes the preflight→mint race. Every preflight
  short-circuit creates ZERO authorities and ZERO audit rows.
  **`MigrationResult` (R11-2, the `OpenResult` precedent — 0013 r8-f3:
  facts are never inferred from the label):** string-compares as the closed
  `Outcome` label while carrying `store_changed`, `transaction_committed`,
  `resulting_version`, and `diagnostic`; preflight short-circuits carry
  `(False, False, resolved-version-or-None)`; delegated operations carry
  `migrate_store`'s own facts. **The preflight→mint race, closed by RECLASSIFICATION over a DEFINED mint
  interface (R12-1/R13-1):** the production mint API is
  **`mint_release_authority(path, attestation) -> MigrationAuthority`**,
  raising **`MintError(reason)`** with the closed reason enum
  **{`source-missing`, `source-unaccepted`, `source-changed`}** (the
  test-only `make_authority` and its undifferentiated `ValueError` are not
  the production surface). **Every preflight→mint transition, classified:**
  ANY `MintError` — a competing migration (`source-changed`), a store
  deleted between preflight and mint (`source-missing`), or an unaccepted
  shape appearing (`source-unaccepted`) — RESTARTS the preflight, bounded
  at 3 attempts; the re-run resolves whatever is now true (a vanished store
  → the missing refusal; a migrated store → `current`; nothing ever
  "surfaces directly" past classification). **Exhaustion:** after the third
  failed attempt the orchestrator returns the FINAL preflight's
  classification outcome with a contention diagnostic appended — the result
  is total by construction because every preflight outcome already is. **The current cell SPLITS (R12-2):** clean-current →
  `current` with facts (False, False, 7) and byte-identity;
  current-with-rebuildable-drift → `current` carrying the repair facts
  (True, True, 7) — the repair rides the ONE shared opening/planner path
  (0007's own repair-during-opening), never a second repairer; `locked` is
  restored to the matrix (→ the open-failure refusal outcome, no minting).
  **`MigrationResult`, frozen (R12-3/R13-2):** `store_changed:
  Optional[bool]`, `transaction_committed: Optional[bool]` (tri-state —
  `None` means audit-unknown, never a fabricated bool),
  **`resulting_state`: the 0013 vocabulary VERBATIM (including `missing`,
  `unaccepted`, `unknown`)** — the field whose omission collapsed three
  distinct terminal cells; `resulting_version: Optional[int]`; `diagnostic:
  str`. The stale resolved-version-or-None short-circuit rule is RETIRED:
  the exhaustive outcome→facts table covers BOTH preflight and delegated
  outcomes over the full quadruple, mirroring 0013's seven terminal cells
  verbatim; a validating constructor REJECTS every out-of-table carrier.
  **The readback interface, defined (R13-3, reconciled with R14-3 by
  internal F1 — the integrity check lives AT the read boundary):**
  `read_terminal(operation_id) -> TerminalFacts` on the audit store —
  own-operation binding (the orchestrator may read ONLY the operation id it
  minted), consistent snapshot (read on the same connection after
  `record_terminal` returns). **A missing or malformed record at that
  boundary raises `MigrationAuditReadError`** — every call site is
  post-`record_terminal`-success by construction (preflight short-circuits
  take their facts from the §4b table and never call readback), so an
  absent/corrupt record there is ALWAYS an audit-integrity failure and is
  ALWAYS loud; there is no caller that legitimately accepts an
  audit-unknown fallback from this interface, and the v1 rule that offered
  one described a dead branch (deleted, registered in
  `withdrawn_phrases.py`). Audit-unknown facts exist ONLY where 0013
  permits them — carried IN a well-formed terminal record — never as a
  readback substitute for a record that should exist. **`MigrationAuditWriteError` REMAINS
  the deliberately loud ESCAPING exception exactly as 0013 requires** — the
  orchestrator never converts it to a `MigrationResult` (that would hide an
  audit failure behind exit 0); it propagates, and the CLI maps it to
  **exit 3** with the exception's own `resulting_state` on stderr. **`MigrationAttestation`, frozen
  (R12-4/R13-4):** an immutable carrier of exactly {`quiesced` — must be
  the bool literal `True`, checked `is True`, so `1` and truthy objects
  refuse; `backup_ref` — validated by **0013's OWN frozen token-grammar
  validator (1–128 ASCII, the accepted grammar)** — no separate predicate,
  NO normalization: the exact token or a `ValueError` (so `"backup ref"`
  refuses here rather than failing later inside minting)}. **The ONLY
  accepted representation is the `MigrationAttestation` type itself —
  `isinstance` checked; duck-typed carriers are REFUSED, never copied**
  (v16's re-validated-copy rule is retired as contradictory: exactness wins
  over tolerance). The CLI rejects an invalid `--backup` value with exit 2
  and the grammar stated in the message. **The CLI acquisition flow, frozen as
  FLAGS (never prompts — prompting is coercion-prone and non-interactive
  hostile):** `veracium migrate --db X --i-have-quiesced --backup REF`;
  both flags required for the migration path, missing → exit 2 with usage;
  exit codes: 0 = migrated/current · 1 = every refusal incl.
  `unsupported-base` · 2 = usage/invalid attestation · 3 =
  `MigrationAuditWriteError` escaped (the loud audit failure, with its
  `resulting_state` on stderr). Reporting stays on the structured fields;
  `cli.py` and `tests/test_migrate_cli.py` are dispositioned in §7a under
  this spec's authority. **Ordinary OPENING of a below-v6 store is
  UNCHANGED by this spec** — 0013's existing below-head refusal governs it;
  only `run_release_migration`'s PREFLIGHT returns the new outcome (§2c
  carries both cells). **The 0013 M10 amendment is WITHDRAWN**: with older
  bases refused, this spec needs exactly ONE declared step (6→7), and
  M10's planner stays deferred to the first spec that truly needs a chain.
  I13 (§6) pins the contract over every legal resolved base 1–5.

> **0013 Outcome-vocabulary amendment (0016 D2, R9-1 form):** the closed
> vocabulary gains ONE member, `unsupported-base` — produced by the release
> migration ORCHESTRATOR'S PREFLIGHT, before authority minting, when the
> resolved base is an accepted version below the lowest declared step
> source (bases 1–5 against 6→7). The preflight does not invoke
> `migrate_store` and creates no audit lifecycle, so the member needs NO
> permitted-resulting-state rule and NO terminal-facts mapping — it never
> reaches them; the store is byte-unchanged. `Outcome` continues to refuse
> non-members; the exhaustive outcome tests extend over the new member and
> assert the zero-audit-rows property. **Terminal-record readback (R12-3):**
> the orchestrator that initiated an operation may READ that operation's
> terminal facts to populate its structured result — a read-only,
> own-operation interface; the facts are never inferred from the label.

### 4b. The round-14 findings, folded from birth

- **R14-1 (the retry state machine, completed):** the mint call receives the
  preflight's resolution evidence (`mint_release_authority(path,
  attestation, *, resolved: PreflightResolution)`) so `source-changed` is
  distinguishable from `source-unaccepted` against what preflight saw.
  **The internal-F3 pin, load-bearing:** mint treats `resolved` as
  reason-labeling evidence ONLY — it never skips, weakens, or substitutes
  any validation because of it; path and attestation are validated against
  the REAL store independently on every attempt. (If mint ever trusted
  `resolved` to elide a check, the parameter would become a TOCTOU — the
  §2c row and `test_resolution_is_reason_labeling_only` pin the boundary.)
  **Exhaustion is a returnable outcome:** after the third `MintError`, the
  orchestrator returns the NEW outcome **`mint-contention`** (added to the
  0013 vocabulary amendment beside `unsupported-base`) with facts
  `(False, False, unknown, None)` and a diagnostic naming the three
  attempts — never "proceed to mint" as a result. The complete state
  machine: resolve → {short-circuit outcome | mint} → mint → {authority |
  MintError → re-resolve (≤3) | exhaustion → `mint-contention`} →
  delegate → result.
- **R14-2 (the table, enumerated):** the exact outcome × `(changed,
  committed, state, version)` table is IN this spec: `unsupported-base` →
  (False, False, unchanged, resolved-base) · `current`/clean → (False,
  False, destination, 7) · `current`/with-repair → (True, True,
  destination, 7) · each refusal (missing/foreign/malformed/unstamped/
  newer/locked) → (False, False, <the 0013 state word for that cell>,
  None) · `mint-contention` → (False, False, unknown, None) · delegated
  outcomes → the readback facts verbatim (0013's seven cells). **The stale
  `(False, False, resolved-version-or-None)` carrier is REMOVED** — the
  table above is the only rule.
- **R14-3 (readback failure, ruled loud):** a terminal record missing or
  malformed AFTER `record_terminal` succeeded is an AUDIT-INTEGRITY
  failure — the orchestrator raises **`MigrationAuditReadError`** (a
  sibling of `MigrationAuditWriteError`, equally loud, CLI exit 3), never
  returns audit-unknown success facts (0013 rejects
  `migrated/None/None/unknown` — the reviewer's cells). Audit-unknown
  facts exist ONLY for outcomes 0013 permits them on. I13 here and §7a
  carry exits 0/1/2/3 consistently.
- **R14-4 (exact-type admission):** `type(attestation) is
  MigrationAttestation` — per accepted 0013's own adversarial regression
  for authorities; the hostile-subclass cell joins the §2c tests.

---

## 5. Regime analysis

The §4b outcome × facts table IS the regime enumeration — every input class
lands in exactly one row, each row names its facts quadruple, and the
validating constructor makes off-table carriers unrepresentable. The three
regimes worth naming in prose: **preflight short-circuits** (facts from the
table, zero authorities, zero audit rows, store byte-unchanged);
**delegated base-6 operations** (facts from the terminal readback verbatim —
0013's seven cells); **audit-trail failures** (`MigrationAuditWriteError` /
`MigrationAuditReadError` ESCAPE — never a `MigrationResult`, never exit 0).

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **I13** the preflight matrix is TOTAL: bases 1–5 → `unsupported-base` + the ladder; clean-current → `current` (False, False, destination, 7) byte-identical; current-with-repair → `current` (True, True, destination, 7) via the one shared opening path; missing/foreign/malformed/unstamped/newer/locked → the corresponding refusal without minting; every short-circuit zero-authority/zero-audit; resolved base 6 ALONE mints and delegates | `test_preflight_matrix_total` (every cell incl. both current cells and locked) + `test_below_v6_base_refuses_with_the_ladder_message` (all five bases) + `test_below_v6_open_unchanged` + `test_base_6_proceeds_through_the_audited_operation` | CI |
| **I14** the mint race closes by reclassification, bounded, total | `test_mint_race_reclassifies` (each `MintError` reason → re-resolve → the now-true outcome) + the exhaustion cell (third failure → `mint-contention`, facts `(False, False, unknown, None)`, three attempts named in the diagnostic — never proceed-to-mint) | CI |
| **I15** `MigrationResult` carriers are table-only | `test_migration_result_truth_table` — the EXHAUSTIVE §4b table (preflight + delegated + `mint-contention` rows against 0013's seven terminal cells); the validating constructor rejects every out-of-table quadruple. **Gate-extension obligation (CLAUDE-gate rule): this validator's domain is small and closed — it joins `tests/test_0013_presend_gates.py`'s independent-oracle pattern (`test_terminal_facts_matches_the_independent_oracle`), enumerated against a separately-written oracle, not example-tested** | CI |
| **I16** the attestation contract is exact | `test_attestation_contract` — absent, coerced (`quiesced=1`/truthy object), grammar-violating (incl. embedded space), duck-typed, and HOSTILE-SUBCLASS cells (R14-4; `type(x) is` admission, the 0013 authority-regression pattern) | CI |
| **I17** audit failures are loud end-to-end | `test_audit_read_error_is_loud` (missing/malformed record post-`record_terminal` → `MigrationAuditReadError` escapes → CLI exit 3 with `resulting_state` on stderr) + the existing `MigrationAuditWriteError` path (exit 3, never behind exit 0). **Gate-extension obligation: the readback boundary and the mint-retry loop are NEW failure seams — they join `test_every_fault_seam_preserves_the_invariants`'s injection list, not just these example tests** | CI |
| **I18** the resolution evidence is reason-labeling only (internal F3) | `test_resolution_is_reason_labeling_only` — a forged/mismatched `PreflightResolution` changes NO validation outcome, grants NO authority, alters NO facts; at most the `MintError` reason label differs, and the re-resolve then re-establishes truth | CI |
| **I19** the CLI contract | `tests/test_migrate_cli.py`, amended under this spec's authority (§7a): flags required on the migration path (missing → exit 2), invalid `--backup` → exit 2 with the grammar, exits 0/1/2/3 as §4, reporting from structured fields only | CI |

## 7. Failure modes and reversibility

Every preflight short-circuit and every refusal leaves the store
byte-unchanged (zero authorities, zero audit rows). The delegated operation's
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
| 0013 amendments (marked, land same-commit with implementation per the 0014 §7b rule) | `Outcome` +`unsupported-base` +`mint-contention`; `read_terminal` + `MigrationAuditReadError`; the exhaustive outcome tests extended |
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
