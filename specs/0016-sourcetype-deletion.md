# Feature spec: SourceType deletion + the evidence_basis contract freeze

Spec-Status: draft

| | |
|---|---|
| **Author / session** | dev |
| **Version** | v3 — *re-read before editing; quote the version you approve*. v2→v3: research's forward-lens addition folded pre-review — **the migration-boundary transition**: the two-way stamp partition (`<7` benign / `=7` integrity) is sound only if `committed_schema` is TOTAL over ops — every op fully-6 or fully-7, never straddling the v6→v7 ALTER. Designed in: the migration is ATOMIC w.r.t. receipt writes (the 0013 offline contract quiesces callers; additionally the ALTER and the stamp backfill commit in ONE transaction, and a receipt write observing a mid-migration schema is impossible by construction — asserted by a boundary test). This is 0015's transitions-vs-states lens applied before the external round could find it. v1→v2: the tenth write site (`model_copy(update=)`) | |
| **Status** | *narrative only — canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research — stage-1 scope adjudicated 2026-08-11; full-spec internal review pending |
| **External review** | required (full spec — touches `schema.py`, `ingest.py`, `__init__.py`, `store/sqlite.py`, `portability.py`, `lifecycle.py`); not yet sent |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation

`SourceType` (`STATED`/`OBSERVED`/`INFERRED`) gates nothing, cannot be honestly
attested, and is published to hosts in exports while carrying no information —
it is a forgery-free function of `author_of_evidence` (`ingest.py:104-109`),
and a forgery-free function of an existing field carries none. `OBSERVED` is
unreachable: a dead value on a public enum. The vocabulary collides invertedly
with the deferred `evidence_basis` (`SourceType.OBSERVED` = weak/inferred;
basis `observed` = strongest/first-hand — same `Provenance` object), which
blocks the axis this project actually wants. **Do nothing:** the only
structural spec debt stays; a host builds logic on a meaningless exported
field; our published representation-without-enforcement critique remains
turned on us (A1 point 4). Research's adjudication adds the closing argument:
even in the one machinery that *compares* the field (0014 receipts), it is
**redundant** — derived from `author_of_evidence`, which is in the same
comparison set, so it contributes zero discriminating power there too.

**Alternatives rejected** (A1 §3, adopted): **demote** to advisory metadata —
a provenance product shipping a provenance field it tells you not to rely on;
**re-found as a lexical measurement** — genuinely defensible but must be
pulled by a decision that needs it, and none does; **ship `evidence_basis` in
this spec** — a consumer-less provenance field is the exact defect Ruling 2
split it out of 0006 for; the freeze below is the honest alternative.

---

## 1b. The evidence_basis contract — FROZEN here, field NOT shipped

The successor contract, recorded so it cannot drift before its first consumer:

1. **Enum semantics per Ruling 1** (`proposals/0006-rulings-round2.md`): the
   attested values are **NOT a total order** (`observed`/`restated` =
   directness; `derived` = mechanism); **unknown is a fourth state, stored
   absent (I8), and is the FLOOR** — no trust-bearing decision may treat
   unknown more favourably than *any* attested basis; per-decision constraints
   are defined by **the spec that ships the first consumer**, never by a
   global ranking.
2. **Unforgeability (evidence-basis-design §4.1), research's sharpening:**
   the extraction schema must not contain a basis field at all — not
   validated, not ignored-if-suspicious, **absent**, so a model emitting a
   basis key has it dropped by the parser with no code path that reads it.
   The field is attested at a host-controlled boundary or not at all. This is
   the constraint that makes the axis buildable; freezing only the enum would
   lose it.
3. **Optional, host-supplied only; never required when `source_id` is
   present** — a guessed `observed` (visibly the strongest value) is worse
   than an absent one.
4. **Trigger:** a first consumer, in its own spec. This spec's deletion is
   that spec's prerequisite (A1 §6): the colliding vocabulary is gone.

---

## 2. Field contracts touched

| field | read / written | its **documented** contract | every other consumer | preserved? |
|---|---|---|---|---|
| `Provenance.source_type` | **deleted at D2** | "epistemic distance" — in fact derived from `author` (`ingest.py:104-109`) | **10 write sites**: 9 `Provenance(...)` constructions + the `model_copy(update={"source_type": ...})` write at `sqlite.py:1143-1147` (grep BOTH forms, §2c-ii); `contribution.py:143/:201` (partition + comparison); `store/base.py:223` docstring; exports (whole-edge serialisation); 62 non-0014 test refs; 0 docs refs | the contract was never honoured (nothing reads it to decide); deletion makes the surface honest |
| `SourceType` (public enum) | **deprecated at D1, removed at D2** | exported at top level | host imports (uncountable — public API, hence the cycle) | D1 warns without behaviour change; D2 is the API break, in an API-breaking release |
| `EXACT_EQUAL_PROV_FIELDS` | written: drops `source_type` at D2 | the TOTAL partition over `Provenance.model_fields`; totality is test-pinned | `verify_snapshot_against_plan` (`contribution.py:201`), `test_0014_receipt_split.py:80,:125` | yes — the totality test forces the constant and the model to move together; idempotency strength unchanged (the field was redundant with `author_of_evidence`, same set) |
| `FORMAT_VERSION` | 5 → **6 at D2** | import gates by version | `portability.py`, S7/0006 pins | an OLD build's `Provenance` REQUIRES `source_type` (`schema.py:111`), so without the bump a new export dies there as a pydantic error; the bump makes it an honest version refusal |
| supersession receipts | gain `committed_schema` stamp at D2 (`ALTER`, SCHEMA v6→v7) | receipts carry request/outcome digests; phase 1 compares | `apply_supersession_plan` phase 1/2 | the stamp is what keeps schema-shift and tampering different findings (§4) |

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| old exports (FORMAT ≤5, carry `source_type`) | — | existing gates | key present after D2 | a file claiming any `source_type` value | **silently dropped on import** — pydantic default `extra=None` → ignore (verified §2c-ii: unknown keys tolerated); `test_old_export_source_type_is_dropped` |
| new exports read by OLD builds | — | — | missing required `source_type` | — | **FORMAT 6 refusal precedes the pydantic error** — old builds gate on version before validation; `test_format_6_refused_by_version_gate` (pinned against the v5 gate code path) |
| extractor output | — | — | a model-emitted `source_type` (or basis) key | model asserts provenance | **parser drops unknown keys with no reading code path** — the §4.1 rule, now also the deletion's own regression: `test_extractor_cannot_emit_provenance_fields` |
| pre-D2 receipts (stored digests computed over the old field set) | — | — | digest mismatch on resubmission | indistinguishable-by-digest from tamper | **the `committed_schema` stamp partitions the two** (§4): `< 7` → `ReceiptSchemaBoundaryError` (named, benign, expected); `= 7` mismatch → `SupersessionIntegrityError` (genuine, loud); `test_receipt_boundary_error_names_the_schema` + `test_post_removal_mismatch_still_integrity_error` |
| host code importing `SourceType` | — | — | import after D2 → `AttributeError` | — | D1's `DeprecationWarning` (module `__getattr__`) is the cycle's notice; `test_sourcetype_import_warns_at_d1` |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | result |
|---|---|---|
| no trust decision reads it | `grep -n "source_type" src/veracium/gate.py src/veracium/compile.py src/veracium/graph.py` | no hits (exit 1) |
| not rendered to the model | `grep -n "source_type" src/veracium/prompts.py src/veracium/proactive.py` | no hits (exit 1) |
| not exposed via MCP/CLI/introspect/audit | `grep -n "source_type" src/veracium/mcp_server.py src/veracium/cli.py src/veracium/introspect.py src/veracium/audit.py` | no hits |
| 9 `Provenance(` construction sites | `grep -rn "Provenance(" src/veracium/ \| grep -v "class Provenance\|#" \| wc -l` | 9 |
| **+1 `model_copy(update=)` write — the form a constructor grep misses** (research's 0016 sign-off catch, 0015-F3 generalized: a write site is ANY write, so the sweep runs BOTH greps) | `grep -rn '"source_type":' src/veracium/ \| grep -v "#"` | `store/sqlite.py:1144` — total write sites: **10** |
| the 0014 consumer A1 predates | `grep -n "source_type" src/veracium/contribution.py` | line 143 (partition); consumed at 201 |
| outcome digest wraps the plan projection | `grep -n "_outcome_digest_v2" -A 12 src/veracium/store/sqlite.py` | `pre_split` wraps `_logical_request_digest(plan)` (sqlite.py:315-327) |
| `source_type` is required today (why old builds break on new files) | `grep -n "source_type: SourceType" src/veracium/schema.py` | line 111, no default |
| unknown keys are dropped on load (why old files import fine) | `python -c "from veracium.schema import Provenance; Provenance.model_validate({...,'unknown_key':'x'})"` | validates; attribute absent |
| test / docs reach | `grep -rn "source_type" tests/ \| grep -v test_0014 \| wc -l` · `grep -rn "source_type" docs/ README.md \| wc -l` | 62 · 0 |

---

## 3. Trust-class matrix — REQUIRED, blocking

The operation is a **field deletion whose field no trust decision reads**
(§2c-ii row 1) — the state-transition form applies. Enumerated from today's
enums (`EvidenceAuthor` USER/THIRD_PARTY/SYSTEM × `Disclosure`
MENTIONABLE/USE_ONLY/QUARANTINED, `schema.py:37-48`): for **every** class
pair, D1 changes nothing (a warning on enum access), and D2 removes a field
that `gate.py`/`compile.py`/`graph.py`/`lifecycle` decisions never consult —
disclosure routing, supersession, absorption, reinforcement, quarantine, and
staleness behave byte-identically (I1, §6). Directionality: n/a — no merge or
ordering touches the field.

- **User-asserted fact becomes non-assertable?** No — assertability derives
  from `author_of_evidence`/`disclosure`/flags, none touched (I1).
- **Non-user content gains user-grade authority/confidence/currency?** No —
  same mechanism.
- **Clears `needs_confirmation`?** No — untouched; 0008's suite keeps
  running.
- **Merges/drops/overwrites provenance?** It **deletes one provenance field
  everywhere at once** — uniformly, for every class, at a version boundary,
  with the export format versioned (FORMAT 6). No selective or
  class-dependent drop exists.

**Write-time or maintain-time?** Neither — a schema change at a release
boundary. No currency, confidence, or flag movement anywhere.

---

## 3b. Authorization and scope — *full specs only*

Analyzed at the **information level** (the 0015 lesson): deletion only ever
*removes* information from surfaces (exports, receipts’ digest basis). No
recipient — host, model caller, importer, telemetry — can derive anything
after D2 that it could not before; the model caller never saw the field at
all (§2c-ii rows 2-3). No user/tenant/scope boundary is crossed; nothing
becomes visible to any principal. The one *new* signal is the
`ReceiptSchemaBoundaryError` name, visible to the host-API caller on a
cross-boundary retry — it reveals "this op committed before the upgrade,"
which the host (who ran the migration) already knows.

---

## 4. Behaviour

**D1 — deprecation (next minor, 0.8.0):** `SourceType` access via the package
namespace emits `DeprecationWarning` (module-level `__getattr__`); the field
is still constructed, stored, exported, compared — byte-identical behaviour.
CHANGELOG names D2's release.

**D2 — removal (the next API-breaking release):**

- `Provenance.source_type` and `SourceType` removed; **all 10 write sites**
  — the 9 `Provenance(` constructions AND the `model_copy(update=)` write at
  `sqlite.py:1143-1147`, whose `"source_type"` update key is dropped (left in
  place it would raise or silently no-op depending on model config, neither
  acceptable) — plus `store/base.py:223` docstring and
  `EXACT_EQUAL_PROV_FIELDS`, updated in the same commit (the partition
  totality test forces the constant; I1's byte-identity forces the rest).
- **`FORMAT_VERSION` 5→6.** New builds import ≤5 files by dropping the key
  (verified `extra` behaviour); old builds refuse 6 by version gate — an
  honest refusal instead of a pydantic crash on a missing required field.
- **SCHEMA v6→v7:** `ALTER TABLE supersession_operations ADD COLUMN
  committed_schema INTEGER NOT NULL DEFAULT 6` — existing receipts stamp 6
  (pre-removal), new receipts write 7. The ALTER-path DDL literal is authored
  empirically and sha-pinned per the 0013/0014 convention, with the stored-DDL
  byte check in the migration.
- **The migration boundary is an ATOMIC TRANSITION (the 0015
  transitions-vs-states lens, applied in advance):** `committed_schema` is
  TOTAL over operations — every receipt is fully-6 (written before the
  migration, stamped by the ALTER's DEFAULT) or fully-7 (written after),
  never straddling. Mechanism: 0013 migrations are offline with quiesced
  callers, AND the ALTER + backfill commit in one transaction, so no receipt
  write can observe a mid-migration schema; `test_no_receipt_straddles_the_
  v7_boundary` asserts it. Without this, a boundary op with an ambiguous
  stamp would be mis-classified by the partition below.
- **Phase-1/2 receipt behaviour at the boundary:** stamp `< 7` + any digest
  mismatch → **`ReceiptSchemaBoundaryError`** — named, fail-closed, message
  states the op committed under a prior schema and is not replay-verifiable
  across the removal; stamp `= 7` + mismatch → the existing
  **`SupersessionIntegrityError`** (genuine violation, distinct and louder).
  Schema-shift and tampering stay different findings (research's required
  refinement). Stamp `< 7` + digest MATCH is impossible by construction
  (old digests were computed over a shape that no longer serialises) and is
  treated as integrity violation if ever observed.
- `test_lifecycle.py:324` reshaped to its real intent: a summary does not
  inherit its first input's `evidence_ref` (A1 §5 / 0002 M1); the 62
  non-0014 test references swept in the same change.

**Interfaces:** D2 removes a top-level export — the API break the cycle
exists for. **Migration:** offline per 0013; one ALTER; nothing else changes
on disk (edge JSON keeps historical `source_type` keys, which readers drop —
no rewrite of stored edges, so nothing is unrecoverable and old data remains
byte-stable).

---

## 5. Regime analysis

- No decision path touches the field, so no scale/density/threshold regime
  exists for behaviour. The regimes that matter are **boundary regimes**, and
  each gets a test (§6): old-export import; new-export-to-old-build refusal
  (exercised against the pinned v5 gate); pre-D2 receipt resubmitted post-D2
  (both the benign and the genuine-mismatch cells); D1 warning; a full
  v1→v7 migration chain (extending the 0013 suite).
- Cold vs warm: no difference. Release class: **stable** — every named
  regime is reachable in CI.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where it runs |
|---|---|---|
| I1 — decision byte-identity: identical ingest/recall/maintain sequences produce identical edges, gates, and renders before/after D2 | `test_deletion_is_decision_invisible` (fixture-sequence dump compare) + the standing 0003/0008/0012/0014 suites green | CI |
| I2 — D1 warns, D1 changes nothing else | `test_sourcetype_import_warns_at_d1` + suite green under `-W error::DeprecationWarning` allowlist | CI |
| I3 — old exports import with the key dropped; every other field preserved | `test_old_export_source_type_is_dropped` | CI |
| I4 — FORMAT 6 refused by the v5 version gate before validation | `test_format_6_refused_by_version_gate` | CI |
| I5 — the receipt boundary partitions: stamp<7 mismatch → `ReceiptSchemaBoundaryError`; stamp=7 mismatch → `SupersessionIntegrityError`; stamp<7 match → integrity error | `test_receipt_boundary_error_names_the_schema` · `test_post_removal_mismatch_still_integrity_error` · `test_impossible_old_match_is_integrity_error` | CI |
| I6 — partition totality survives: `EXACT_EQUAL_PROV_FIELDS` minus the field + the model minus the field still partition exactly | `test_raw_request_field_partition_is_total` (existing, breaks then passes) | CI |
| I7 — idempotency strength unchanged: two same-op submissions differing ONLY in author-class still conflict (the redundancy argument, tested from the surviving side) | `test_idempotency_discrimination_unweakened` | CI |
| I8 — the extractor cannot emit provenance fields (the §4.1 rule as a regression) | `test_extractor_cannot_emit_provenance_fields` | CI |
| I9 — the D2 ALTER's stored DDL byte-equals the sha-pinned literal | migration self-check + `test_v7_alter_path_matches_pinned_literal` | CI |
| I10 — the frozen evidence_basis contract is text-pinned: §1b's four clauses present verbatim until a first-consumer spec supersedes them | `test_evidence_basis_contract_frozen` (text pin, breaks on drift) | CI |

**Reproducer retention:** review defects become regressions beside these.

---

## 7. Failure modes and reversibility

- **Silent failure:** a missed consumer of `source_type` discovered post-D2 —
  pinned by §2's grep-enumerated consumer table and I1's byte-identity, both
  mechanical rather than remembered.
- **Reversibility:** D1 is trivially reversible. D2 is an API break by
  design; stored data is untouched (historical keys remain in edge JSON,
  dropped on read), so a rollback build reads old stores unchanged — only
  post-D2 exports (FORMAT 6) and v7 receipts are forward-shaped, both
  version-gated.
- **Partial failure:** the D2 migration is one 0013-governed offline ALTER —
  atomic, audited, refusing unknown shapes as ordinary opening would.
- **Attack surface:** none added; one surface (a meaningless exported field a
  host could build on) removed. The boundary error is host-API visible only
  (§3b).

---

## 8. Claims and limits

- **Changelog (D1):** "`SourceType` is deprecated and will be removed in
  <the named API-breaking release>. It has never influenced any decision;
  hosts reading it from exports should stop — the field is a restatement of
  `author_of_evidence`."
- **Changelog (D2):** "`SourceType`/`Provenance.source_type` removed
  (deprecated since 0.8.0). Behaviour is unchanged (the field gated nothing —
  the suite proves byte-identity). Export format is now 6; older builds
  refuse new exports rather than misreading them. A supersession retry whose
  original committed before this upgrade is refused with a named error rather
  than guessed at."
- **What this does NOT establish:** it does not ship `evidence_basis` (frozen
  contract only, §1b); it does not improve any trust decision (nothing read
  the field); it does not make pre-D2 receipts replay-verifiable across the
  boundary (explicitly the opposite, fail-closed); the D2 rollback story
  covers stores, not FORMAT-6 exports or v7 receipts.
- **Measurements:** consumer counts and reach claims carry their commands
  (§2c-ii); no other numbers appear.

---

## 9. Brief for the external reviewer

- **Least sure of, one:** the **receipt-boundary cell we called impossible**
  (stamp `< 7` with a digest MATCH). We reason old digests cannot match
  new-shape dumps byte-wise; if you can construct a collision path (e.g. an
  edge whose old and new serialisations coincide), the cell's routing needs
  re-deciding.
- **Least sure of, two:** whether **D1's warning surface is complete** — a
  module `__getattr__` catches `veracium.SourceType`, but
  `from veracium.schema import SourceType` bypasses the package namespace.
  Options and their costs are in §10 Q2.
- **Where we may have overstated:** "nothing is unrecoverable" (§4) — true
  for stores, but a host that *depended* on reading `source_type` from
  exports loses that read at D2 with no replacement by design; we believe no
  such host exists and cannot prove it.
- **What would change our minds:** a demonstrated consumer of epistemic
  distance (A1 option 3 becomes live), or a receipt-boundary flaw that makes
  fail-closed refusal unsound rather than merely strict.
- **Reviewer-safe copy:** not needed.

---

## 10. Open questions

1. **Which release is D2?** Needs a named API-breaking release (the 0009
   deprecation rides the same train). **Decides: Quentin. Class:
   pre-release** (D1 can ship without the answer; D2 cannot).
2. **D1 warning mechanism for `from veracium.schema import SourceType`** —
   module `__getattr__` on `schema` too, or accept the package-namespace-only
   warning? **Decides: dev at implementation, recorded in the spec at
   acceptance. Class: blocking** (it defines what D1 promises).
3. **Should the 0009 `last_outcome`/`last_outcome_at` deprecation formally
   name the same D2 release in this spec?** They share the cycle. **Decides:
   Quentin. Class: pre-release.**

---

## Reviewer checklist

- [ ] §3 has no unanswered cells, and is **directional** where the operation is
- [ ] §3's classes were read from the enums, not copied from the template
- [ ] Prohibitions AND the corresponding **permissions** are both tested
- [ ] Every default fails **closed**
- [ ] §2c has a row per uncontrolled input, and **no empty invariant cell**
- [ ] §2c-ii: every reach claim carries **the command**
- [ ] §2 consumers were enumerated by grep, not recall
- [ ] Every §6 invariant has a check that actually runs
- [ ] §5 regimes are reachable by tests, or the change is experimental
- [ ] §3b: no principal can see anything they could not see before
- [ ] §6 and §8 are filled in
- [ ] §10 questions each carry a class
- [ ] §8 states what this does *not* establish
- [ ] I have said where I think the **author's conclusion is wrong**
- [ ] I re-read the current version before reviewing
- [ ] §9 brief is written, and external review has been sent
