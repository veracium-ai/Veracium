# Feature spec: the release-migration orchestrator

Spec-Status: draft
Spec-Requires: 0007, 0013, 0016

| | |
|---|---|
| **Author / session** | dev |
| **Version** | v1 — born from the 0016 round-14 split (Quentin's ruling, research's meaning/execution line): 0016 states what D2 MEANS; THIS spec owns how a release EXECUTES it. The construction below is the 0016 v10–v17 material — already through five external rounds of hardening — **with the four round-14 findings folded from birth (§4b)** |
| **Status** | *narrative only — canonical is the `Spec-Status:` line* |
| **Internal reviewers** | research — internal review REQUESTED 2026-08-13 (queued behind 0017 per their queue order) |
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

## 2–3b. Contracts, untrusted inputs, trust matrix

The §2/§2c/§3/§3b analysis for this machinery lives in 0016 v17 §§2–3b
(reviewed rounds 10–14) and TRANSFERS here verbatim at the next revision;
the load-bearing rows: the `MigrationAttestation` §2c row (absent/coerced/
grammar-violating/hostile-subclass cells), the below-v6 store row, and §3b's
no-new-visibility analysis. This spec performs no stored-state operation —
it orchestrates operations 0013 already specifies.

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
  **The readback interface, defined (R13-3, in the 0013 amendment):**
  `read_terminal(operation_id) -> TerminalFacts` on the audit store —
  own-operation binding (the orchestrator may read ONLY the operation id it
  minted), consistent snapshot (read on the same connection after
  `record_terminal` returns), and a malformed or missing record yields the
  audit-unknown facts, never an error. **`MigrationAuditWriteError` REMAINS
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

## 5–8. Regimes, invariants, failure modes, claims

The I-table transfers from 0016 v17's I13 family at the next revision:
`test_preflight_matrix_total` (every cell incl. both current cells and
locked) · `test_mint_race_reclassifies` (+ the exhaustion cell) ·
`test_migration_result_truth_table` (the §4b table, exhaustive) ·
`test_attestation_contract` (+ the hostile-subclass cell) ·
`test_audit_read_error_is_loud` · the amended `test_migrate_cli.py`.
Claims: this spec establishes HOW D2 executes; it does not alter what D2
means (0016's), and nothing here runs until both specs are accepted.

## 9. Brief for the external reviewer

This construction is yours as much as ours: rounds 10–14 of 0016 built it
finding by finding, and §4b folds your round-14 findings. Least sure of:
whether `mint-contention`'s facts row and `MigrationAuditReadError`'s
placement survive the same 0013-instrument scrutiny the rest did.

## 10. Open questions

1. Does the `PreflightResolution` evidence parameter need its own §2c row
   (it is orchestrator-internal, never caller-supplied)? **Decides: research
   at internal review. Class: blocking.**
