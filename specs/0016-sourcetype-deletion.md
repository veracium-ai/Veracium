# Feature spec: SourceType deletion + the evidence_basis contract freeze

Spec-Status: draft
Spec-Requires: 0003, 0013, 0014

| | |
|---|---|
| **Author / session** | dev |
| **Version** | v10 — *re-read before editing; quote the version you approve*. v9→v10: EXTERNAL ROUND 6 (4 bin-(a), bin (b) EMPTY; every endorsement holds): R6-1 A+C+D+F found-in-fix of R5-2 — the [b→6] "aggregate evidenced step" does NOT EXIST under accepted 0013 (adjacency is enforced by the registry, TerminalFacts, the single-use authority, and the hook; the evidence holds only the concrete 1→2 path) → the planner is the ACTUAL ADJACENT ROUTE [b→b+1, …, 6→7]: the D2 commit DECLARES every missing adjacent edge (2→3, 3→4, 4→5, 5→6) with per-step evidence so the registry is total over 1..7; each step mints and consumes its OWN single-use MigrationAuthority (mint → run in its own transaction → terminal record + durable stamp → the next step mints fresh); fault injection at EVERY inter-step seam joins the 0013 presend gates; the aggregate production path is RETIRED at D2; R6-2 A+C+D+G — `SCHEMA_V7 = SCHEMA_V6` breaks 0007 shape resolution (reviewer-probed: identical digests, resolve → None, HEAD evidence UNKNOWN) → the explicit 0007 same-shape rule by verbatim amendment: THE STAMP discriminates same-shape versions; an UNSTAMPED store matching a multi-version shape resolves to the OLDEST match (fail-conservative — adoption then migrates forward through the no-op); the resolver + `schema_evidence` HEAD probe updated; 0007/`schema_evidence.py`/`schema_model.py`/tests join §7a; R6-3 D found-in-fix of R5-1 — five carriers still described compare-then-branch → ALL swept to UNCONDITIONAL RECEIPT-HIT refusal (a pre-v3 receipt refuses on sight at both phases; NO digest is computed; the regression replaces digest functions with EXPLODING SENTINELS over all three legal pre-v3 states at both phases); R6-4 A+C+D+G found-in-fix of R5-3 — a floor test cannot force 2.7.0 in an unconstrained install → a REAL minimum-dependency CI job (`pydantic==2.7.0`) beside the latest job, `.github/workflows/test.yml` joins §7a, the test ASSERTS the installed version; the notice contradiction fixed (field access removed from the unwarned list). | |
| **Status** | *narrative only — canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research — stage-1 scope adjudicated 2026-08-11; **full-spec internal review PASSED 2026-08-11** (`proposals/0016-internal-review.md`; Q2 ruled, folded in v4) |
| **Spec-Requires** | `0003` (accepted — §4f gains the schema-conditioned third outcome by same-commit amendment), `0013` (accepted — the offline migration contract D2 rides), `0014` (accepted — `EXACT_EQUAL_PROV_FIELDS` loses the field at D2 by same-commit amendment) (F3) |
| **External review** | required (full spec). **The complete carrier surface (F3):** `schema.py` · `ingest.py` · `__init__.py` · `store/sqlite.py` · `store/base.py` (the new exception) · `store/schema_version.py` (v7 + the declared no-op step) · `store/migration.py` (the D2 step) · `graph.py` + `contribution.py` (the partition + snapshot carriers) · `portability.py` (FORMAT 6) · `lifecycle.py` · the migration evidence artifacts (`schema_evidence` two-directory sweep) · same-commit amendments to accepted `0003` §4f and `0014`. Round 1 (v4): 3 bin-(a) + 2 bin-(b) → v5 = the round-2 resubmission |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation

`SourceType` (`STATED`/`OBSERVED`/`INFERRED`) gates nothing and cannot be
honestly attested. **On the INGEST path** it is a forgery-free function of
`author_of_evidence` (`ingest.py:104-109`) and `OBSERVED` is unreachable
there; **on the PUBLIC model contract** (direct construction, imports) it is
free-standing state — any enum value including `OBSERVED` is settable, no
validator couples it to `author`, and it discriminates 0014 request digests
(the round-1 F1 demonstration). Both halves argue deletion: the derived half
carries no information; the free-standing half carries UNATTESTED
information published as provenance. The vocabulary collides invertedly
with the deferred `evidence_basis` (`SourceType.OBSERVED` = weak/inferred;
basis `observed` = strongest/first-hand — same `Provenance` object), which
blocks the axis this project actually wants. **Do nothing:** the only
structural spec debt stays; a host builds logic on a meaningless exported
field; our published representation-without-enforcement critique remains
turned on us (A1 point 4). *(v5 correction, round-1 F1: the earlier "redundant in the receipt
machinery" claim was FALSE over the public model contract — it held only for
ingest-derived edges. Hosts construct `Edge`s directly; no validator couples
`source_type` to `author_of_evidence`; the reviewer demonstrated two valid
edges identical except STATED-vs-INFERRED yielding DIFFERENT frozen request
digests, and `OBSERVED` is publicly reachable the same way. The deletion
therefore COLLAPSES that discrimination — defined in §4 as part of the D2
API break, with I1/I7 narrowed accordingly.)*

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
| `EXACT_EQUAL_PROV_FIELDS` | written: drops `source_type` at D2 | the TOTAL partition over `Provenance.model_fields`; totality is test-pinned | `verify_snapshot_against_plan` (`contribution.py:201`), `test_0014_receipt_split.py:80,:125` | the totality test forces the constant and the model to move together; **idempotency discrimination NARROWS by the defined collapse (R2-1/F1)** — requests differing only in the deleted field become identical, per the 0014 amendment block (§7a) |
| `FORMAT_VERSION` | 5 → **6 at D2** | import gates by version | `portability.py`, S7/0006 pins | an OLD build's `Provenance` REQUIRES `source_type` (`schema.py:111`), so without the bump a new export dies there as a pydantic error; the bump makes it an honest version refusal |
| supersession receipts | post-D2 writers stamp `outcome_digest_version = 3` (no new column — the R3-3 redesign); SCHEMA v6→v7 is a no-DDL refusal bump | 0014: the validated closed receipt state; the version is the durable projection discriminator | `apply_supersession_plan` phase 1/2; `validate_receipt_state` + its exhaustive oracle (extended to {1,2,3}) | **the version separates ERAS; a pre-v3 receipt refuses UNCONDITIONALLY on ANY resubmission — no digest is computed (R6-3)** — never "different findings", never benign |

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| old exports (FORMAT ≤5, carry `source_type`) | — | existing gates | key present after D2 | a file claiming any `source_type` value | **silently dropped on import** — pydantic default `extra=None` → ignore (verified §2c-ii: unknown keys tolerated); `test_old_export_source_type_is_dropped` |
| new exports read by OLD builds | — | — | missing required `source_type` | — | **FORMAT 6 refusal precedes the pydantic error** — old builds gate on version before validation; `test_format_6_refused_by_version_gate` (pinned against the v5 gate code path) |
| extractor output | — | — | a model-emitted `source_type` (or basis) key | model asserts provenance | **parser drops unknown keys with no reading code path** — the §4.1 rule, now also the deletion's own regression: `test_extractor_cannot_emit_provenance_fields` |
| pre-D2 receipts (stored digests computed over the old field set) | — | — | ANY resubmission hitting a pre-v3 receipt | **classification is impossible — and that impossibility IS the ruling (R2-3/R5-1/R6-3)** | **a version<3 receipt refuses UNCONDITIONALLY ON SIGHT at both phases — no digest is computed, no comparison branch exists**: `ReceiptSchemaBoundaryError(SupersessionIntegrityError)`, never benign; a version-3 receipt follows the ordinary 0014 contract; `test_pre_v3_receipt_refuses_on_sight` (all three legal pre-v3 states × both phases, digest functions replaced by EXPLODING SENTINELS) + `test_v3_receipts_follow_the_ordinary_contract` |
| stored `source_type` values (direct constructors/imports: any VALID enum value incl. `OBSERVED` — an unrecognised string raises `ValidationError` at construction today; arbitrary strings reach storage only via validation-bypassing writes or hand-edited JSON) (F1, precision per round-2 bin-(b)) | — | — | unknown value in stored JSON (bypass/hand-edit only) | a crafted value aimed at post-D2 readers | **dropped on read post-D2 exactly like the historical key** (`extra` ignore); pre-D2 they are inert to decisions (§2c-ii row 1) and discriminate digests only until the boundary; `test_arbitrary_stored_source_type_dropped_post_d2` |
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
staleness behave identically in their DECISION projections (I1's narrowed sense, §6) — receipt identity and replay/conflict classification change by the defined collapse (I7). Directionality: n/a — no merge or
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
cross-boundary retry — it reveals "this op committed before the upgrade."
*Stated assumption (internal review): this reads most naturally when the
migration-runner and the API-caller are the same host; the conclusion holds
even when they differ, because the error carries only a temporal fact about
an operation's commit era — no user, tenant, or content data.*

---

## 4. Behaviour

**D1 — deprecation (next minor, 0.8.0): the SEVEN-row access/introspection
matrix (R2-2/R4-3/R5-3) — every supported path warns or is enumerated; I2
tests every row:**

| access path | D1 behaviour | warns |
|---|---|---|
| `veracium.SourceType` attribute access | enum via package `__getattr__` | yes |
| `from veracium import SourceType` | same | yes |
| `veracium.schema.SourceType` attribute access | enum via schema `__getattr__` (not a normal binding during D1; internal code binds `_SourceType`) | yes |
| `from veracium.schema import SourceType` | same | yes |
| `from veracium.schema import *` | **`schema.__all__` is DEFINED (none exists today) and lists `SourceType` during D1**, so PEP-562 star-import triggers the `__getattr__` — probe-verified; without `__all__` this cell silently BREAKS | yes |
| `provenance.source_type` field access | **WARNS (R4-3):** `Field(deprecated=...)` emits exactly ONE `DeprecationWarning` on attribute access, none during construction or dump, and marks the JSON schema deprecated — **requires `pydantic>=2.7` (R5-3): 2.0 treats the keyword as an extra and cannot warn; `pyproject.toml` pins ≥2.7 at D1 and a lowest-supported-version regression runs the warning under the pinned floor** | yes |
| `typing.get_type_hints(Provenance)["source_type"]` | **the D1 annotation binds the private name** (`source_type: _SourceType`, the SAME enum object), so hints resolve to the identical class — no `NameError`; module `__getattr__` cannot intercept annotation resolution through module globals, so this cell CANNOT warn | **no — enumerated in the deprecation notice** |

**The rest of the surface, ruled (R3-1):**
- **Field access WARNS (R4-3, `pydantic>=2.7` — R5-3):** `Field(deprecated=...)` on
  `Provenance.source_type` — one warning per access, none on
  construction/dump, JSON schema marked. Only MODEL METADATA
  (`model_fields`, `get_type_hints`) remains un-warned, enumerated in the
  notice text (§8).
- **Namespace preservation, exact**: `schema.__all__` is the full current
  public namespace (42 names — the 41 existing plus `SourceType` via the
  `__getattr__`); `test_star_import_namespace_is_byte_identical` compares
  the pre-D1 and D1 star-import namespaces exactly.
- **Both `dir()` surfaces**: package `__dir__` and `schema.__dir__` include
  `SourceType` during D1.
- **Internal imports**: `__init__.py`, `ingest.py`, `lifecycle.py`, and
  `store/sqlite.py` all bind `_SourceType` — no internal use touches the
  warning path, so **ordinary library import and operation are
  WARNING-FREE** (`test_ordinary_operation_emits_no_deprecation_warning`),
  and `__init__.py` creates NO normal package binding that would defeat the
  package `__getattr__`.
- **Pickling, exact**: members pickle by module+name; serialization and
  deserialization EACH invoke the lazy lookup — **one round-trip emits
  exactly TWO warnings**, stated as such in I2, not a singular warning.

Any later-discovered path joins the notice, never silence. The field is
still constructed, stored, exported, compared — decision behaviour
unchanged (I1's narrowed sense). CHANGELOG names D2's release.

**D2 — removal (the next API-breaking release):**

- **The digest collapse, defined as part of the API break (F1):** post-D2,
  two submissions that differed only in `source_type` produce IDENTICAL
  snapshots and digests — they ARE the same request. This is an accepted
  consequence of deleting free-standing public state, not an oversight:
  pre-D2 receipts whose digests were discriminated by the field fall under
  the version-era boundary rule like every other pre-D2 receipt.
  Stored values (any VALID enum value a constructor or importer persisted —
  `OBSERVED` included; arbitrary strings only via validation-bypassing
  writes or hand-edits, per §2c) are dropped on read post-D2.
- `Provenance.source_type` and `SourceType` removed; **all 10 write sites**
  — the 9 `Provenance(` constructions AND the `model_copy(update=)` write at
  `sqlite.py:1143-1147`, whose `"source_type"` update key is dropped (left in
  place it would raise or silently no-op depending on model config, neither
  acceptable) — plus `store/base.py:223` docstring and
  `EXACT_EQUAL_PROV_FIELDS`, updated in the same commit (the partition
  totality test forces the constant; I1's decision-projection identity forces the rest).
- **`FORMAT_VERSION` 5→6.** New builds import ≤5 files by dropping the key
  (verified `extra` behaviour); old builds refuse 6 by version gate — an
  honest refusal instead of a pydantic crash on a missing required field.
- **The era discriminator (R3-3 redesign): `outcome_digest_version = 3` —
  the `committed_schema` column is WITHDRAWN.** Accepted 0014 already
  defines the durable digest-projection discriminator and validates the
  closed receipt state on every read and write. D2 changes the projection
  (the snapshot loses the field), so post-D2 receipts stamp **version 3**;
  the 0014 amendment (§7a) extends the closed set to {1, 2, 3} and extends
  `validate_receipt_state` + its exhaustive oracle test. Everything the
  parallel column got wrong vanishes with it: no SQLite type freedom (the
  validated state machinery rejects non-members exactly as 0014 already
  does for versions), no missed-writer DEFAULT (writers stamp the version
  they compute — the existing 0014 pattern), no composite-discriminator
  ambiguity. **SCHEMA v6→v7 is a no-DDL refusal bump** (the 0006 v4→v5
  precedent — CORRECTED by R4-2: v4→v5 was minimal-DDL, adding the
  `store_identity` singleton; the no-DDL form is NEW here and reviewed as
  such): it exists so an older build refuses rather than misreads a store
  whose receipts it cannot classify. **The 0007 same-shape rule (R6-2 —
  reviewer-probed: v6 and v7 share one shape digest, so the resolver
  returned None and HEAD evidence went UNKNOWN):** by verbatim 0007
  amendment (§7a), when two accepted versions share a shape digest, **the
  STAMP (`user_version`) discriminates**; an UNSTAMPED store matching a
  multi-version shape resolves to the OLDEST matching version
  (fail-conservative — adoption then migrates forward through the declared
  no-op). The resolver and `schema_evidence`'s HEAD release probe are
  updated to this rule; tests cover stamped v6, stamped v7, HEAD release
  evidence, migration-output evidence, and unstamped adoption.
- **Receipt v3, mechanically defined (R4-1):** the legal v3 triples are
  **{(request_digest, 3, response_json), (NULL, 3, response_json)}** — the
  same two shapes as v2 (a post-D2 public submission carries its snapshot;
  a store-level snapshotless submission stores NULL request identity). The
  **v3 digest projection is the v2 construction computed over the POST-D2
  field set** (pre_split + contributions + absorption_pre_image, with the
  collapsed model — same wrapper, new basis). **Phase-1/2 selection (re-ruled by
  R5-1 — historical reconstruction was a FALSE promise):** post-D2 neither
  the v1 nor the v2 projection can be computed faithfully — both included
  the deleted field; the reduced-model wrapper computes v3. So: stored 3 →
  the v3 projection and the ordinary contract; **stored 1 or 2 →
  UNCONDITIONAL boundary refusal on any resubmission
  (`ReceiptSchemaBoundaryError`) — no digest comparison is attempted,
  because none is possible**; any other value is rejected by
  `validate_receipt_state`. The exhaustive read/write oracle extends over
  EVERY {1,2,3} triple, and the verbatim 0014 amendment (§7a) carries the
  exact legal v3 triples and these comparison rules — a bare {1,2}→{1,2,3}
  set extension leaves the accepted closed-state contract incomplete.
- **The migration step's executable declaration (R4-2, per accepted 0013):**
  the v6→v7 step declares the reviewed no-op statement tuple
  **`("SELECT 1",)`**, pinned by the reviewer-computed authorization
  artifact (C1, the 0014 R13-1 precedent — the literal is IN this reviewed
  candidate): canonical bytes `veracium-migration-v1:[6,7,["SELECT 1"]]`,
  SHA-256
  `2deae0327584cb0ed265b79f101843eba9e3b5e81b9092d08bf35326aa83ffe9`;
  0013 path evidence binds to that exact SQL; the version stamp update is
  the step's effect. An empty tuple is rejected by 0013 and is not used.
- **The multi-step planner (R5-2, made REPRESENTABLE by R6-1):** accepted
  0013 enforces adjacency everywhere (registry, `TerminalFacts`, the
  single-use `MigrationAuthority`, the executable hook), so the chain is the
  **actual adjacent route [b→b+1, …, 5→6, 6→7]**. The D2 commit **declares
  every missing adjacent edge (2→3, 3→4, 4→5, 5→6) with its own declaration
  and per-step path evidence** — the registry becomes TOTAL over 1..7
  (today's evidence holds only the concrete 1→2 path; the aggregate
  production path is RETIRED at D2). **Authority lifecycle, explicit:** each
  step MINTS its own single-use `MigrationAuthority` bound to its adjacent
  pair and evidence snapshot, runs in its OWN transaction, writes its
  terminal record and stamps its destination durably, and only then does the
  next step mint — no authority spans two steps, no handoff object exists;
  the seam between steps IS the durable stamp. A mid-chain failure leaves
  the store at the last completed stamp (a legal accepted version); a re-run
  resumes from it. **Fault injection at every inter-step seam joins the 0013
  presend gates** (a seam added = an injection added, the standing rule).
  The verbatim 0013 amendment (§7a) carries exactly this.
- **The migration boundary is an ATOMIC TRANSITION (the 0015
  transitions-vs-states lens):** the era stamp is TOTAL over operations —
  every receipt carries the `outcome_digest_version` its writer computed
  (pre-D2 writers: 1 or 2; post-D2 writers: 3), and the 0013 offline
  contract (quiesced callers; the version bump commits atomically) means no
  receipt write can straddle the migration;
  `test_no_receipt_straddles_the_v7_boundary` asserts it.
- **`ReceiptSchemaBoundaryError` — the operative API (R2-3, re-ruled):**
  defined in `store/base.py`, **SUBCLASSING `SupersessionIntegrityError`**
  (the earlier sibling ruling REVERSED): for a stamp-6 receipt post-D2, a
  legitimate retry whose only removed input was `source_type` and a
  genuinely different request reusing the operation id produce THE SAME
  resubmission — classification is impossible, so the outcome is
  handled at least as conservatively as an integrity violation, and existing
  `except SupersessionIntegrityError` handlers (which caught the
  different-request case pre-D2) keep catching it. The subclass adds the era
  context — its message states that the receipt committed under schema 6 and
  the digest basis changed at v7, so legitimate-retry cannot be
  distinguished from a different request — and NEVER the word benign.
  Exported from `veracium.store.base` beside its parent; raised in BOTH
  receipt phases (the phase-1 public lookup in `graph.py` and the store's
  phase-2 check in `sqlite.py`).
- **Phase-1/2 receipt behaviour at the boundary:** version `< 3` + any digest
  receipt-hit → **`ReceiptSchemaBoundaryError`** — unconditional, no digest
  computed (R6-3), fail-closed, message
  states the op committed under a prior schema and is not replay-verifiable
  across the removal; version `= 3` receipts follow the ordinary contract —
  a version-3 mismatch → the existing
  **`SupersessionIntegrityError`** (genuine violation, distinct and louder).
  A pre-v3 receipt refuses on sight — no comparison, so no match/mismatch
  cells exist for it (R6-3; the one contract).
- **Same-commit amendments to the accepted corpus (F3):** `0003` §4f gains
  the schema-conditioned third outcome (boundary refusal, distinct from
  integrity conflict) by verbatim amendment block in the D2 commit; `0014`'s
  `EXACT_EQUAL_PROV_FIELDS` freeze is amended to the post-D2 field set in
  the same commit (the partition totality test forces the constant; the
  amendment records WHY). Implementation may not land while either accepted
  spec still states the superseded contract.
- `test_lifecycle.py:324` reshaped to its real intent: a summary does not
  inherit its first input's `evidence_ref` (A1 §5 / 0002 M1); the 62
  non-0014 test references swept in the same change.

**Interfaces:** D2 removes a top-level export — the API break the cycle
exists for. **Migration:** offline per 0013; the declared no-op step
(`("SELECT 1",)`) plus the version stamp; nothing else changes
on disk (edge JSON keeps historical `source_type` keys, which readers drop —
no rewrite of stored edges, so nothing is unrecoverable and old data remains
byte-stable).

---

## 5. Regime analysis

- No decision path touches the field, so no scale/density/threshold regime
  exists for behaviour. The regimes that matter are **boundary regimes**, and
  each gets a test (§6): old-export import; new-export-to-old-build refusal
  (exercised against the pinned v5 gate); pre-D2 receipt resubmitted post-D2
  (the unclassifiable pre-v3 cell and the ordinary v3 cell); D1 warning; a full
  v1→v7 migration chain (extending the 0013 suite).
- Cold vs warm: no difference. Release class: **stable** — every named
  regime is reachable in CI.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where it runs |
|---|---|---|
| I1 — **trust/recall-decision identity (narrowed by R2-1)**: identical sequences produce identical gates, disclosure routing, and renders before/after D2 — **EXCLUDING receipt identity and replay/conflict classification, which the defined collapse changes** (I7 owns those); the dumps differ exactly by the deleted key | `test_deletion_is_decision_invisible` (projection compare, receipt outcomes excluded) + the standing 0003/0008/0012 suites green | CI |
| I2 — the COMPLETE D1 surface (R3-1/R4-3/R5-3): the SIX warnable rows each warn (five access paths + field access via `Field(deprecated=...)` under the `pydantic>=2.7` floor); `get_type_hints` resolves to the identical class without `NameError`; only model metadata is un-warned and notice-enumerated; the star-import namespace is byte-identical to pre-D1 (all 42 names); both `dir()` surfaces include the enum; a pickle round-trip emits exactly TWO warnings; **ordinary library import and operation emit ZERO deprecation warnings** (internal comparisons use model dumps — warning-free, reviewer-confirmed — and all internal imports bind the private name) | `test_sourcetype_import_warns_at_d1` (all seven rows) · `test_field_access_warns_at_pinned_floor` (runs in the DEDICATED minimum-dependency CI job — `pydantic==2.7.0` exact — and ASSERTS the installed version so it cannot silently run elsewhere; R6-4) · `test_star_import_namespace_is_byte_identical` · `test_dir_surfaces_include_sourcetype` · `test_pickle_roundtrip_emits_exactly_two_warnings` · `test_ordinary_operation_emits_no_deprecation_warning` | CI |
| I3 — old exports import with the key dropped; every other field preserved | `test_old_export_source_type_is_dropped` | CI |
| I4 — FORMAT 6 refused by the v5 version gate before validation | `test_format_6_refused_by_version_gate` | CI |
| I5 — the receipt era rule, ONE contract (R5-1/R6-3): a version<3 receipt refuses UNCONDITIONALLY ON SIGHT at both phases — no digest computed, no comparison branch (the adversarial regression replaces the digest functions with exploding sentinels over all three legal pre-v3 states, {(NULL,1,NULL), (NULL,2,json), (digest,2,json)}, at BOTH phases); a version-3 receipt follows the ordinary 0014 contract; the closed set {1,2,3} is validated on every read and write | `test_pre_v3_receipt_refuses_on_sight` · `test_v3_receipts_follow_the_ordinary_contract` · the extended 0014 oracle test | CI |
| I6 — partition totality survives: `EXACT_EQUAL_PROV_FIELDS` minus the field + the model minus the field still partition exactly | `test_raw_request_field_partition_is_total` (existing, breaks then passes) | CI |
| I7 — idempotency discrimination, stated honestly (narrowed by F1): author-class differences still conflict; **`source_type`-only differences STOP conflicting at D2 — the defined collapse — and the test asserts BOTH directions** (pre-D2 receipts hitting the boundary rule; post-D2 same-request identity) | `test_idempotency_discrimination_post_collapse` (replaces the unweakened-claim test) | CI |
| I8 — the extractor cannot emit provenance fields (the §4.1 rule as a regression) | `test_extractor_cannot_emit_provenance_fields` | CI |
| I9 — the v6→v7 step's declared statement tuple `("SELECT 1",)` is sha-pinned and its 0013 path evidence binds to that exact SQL; the step changes no object (asserted: sqlite_master byte-identical before/after) | migration self-check + `test_v7_step_declaration_matches_pin` + `test_v7_step_changes_no_objects` | CI |
| I10 — the frozen evidence_basis contract is text-pinned: §1b's four clauses present verbatim until a first-consumer spec supersedes them | `test_evidence_basis_contract_frozen` (text pin, breaks on drift) | CI |

**Reproducer retention:** review defects become regressions beside these.

---

## 7. Failure modes and reversibility

- **Silent failure:** a missed consumer of `source_type` discovered post-D2 —
  pinned by §2's grep-enumerated consumer table and I1's decision-projection
  identity, both
  mechanical rather than remembered.
- **Reversibility (corrected by round-1 bin-(b), reviewer-probed):** D1 is
  trivially reversible. **D2 is not runtime-reversible: a v7-stamped store
  REFUSES on a v6 build** (`StoreVersionError(reason="newer")` — the version
  gate doing its job, probed). Rollback requires a pre-migration backup or
  v7-capable code; the 0013 offline-migration guidance already tells
  operators to back up first, and the D2 changelog repeats it. Historical
  JSON retention protects DATA, not downgrade-readability.
- **Partial failure:** the D2 migration is one 0013-governed offline step
  (the declared no-op + version stamp) — atomic, audited, refusing unknown
  shapes as ordinary opening would.
- **Attack surface:** none added; one surface (a meaningless exported field a
  host could build on) removed. The boundary error is host-API visible only
  (§3b).

---

## 7a. Surface inventory — every carrier, dispositioned (R2-4)

| carrier | phase | change |
|---|---|---|
| `src/veracium/schema.py` | D1+D2 | `_SourceType` alias + `__getattr__` + `__all__` + `__dir__` (D1); enum + field removed (D2) |
| `src/veracium/__init__.py` | D1+D2 | package `__getattr__` warning (D1); export removed (D2) |
| `src/veracium/ingest.py` | **D1** (`_SourceType` binding — required for warning-free operation) + D2 (deriver + construction site removed) |
| `src/veracium/graph.py` | D2 | phase-1 receipt lookup refuses UNCONDITIONALLY on any pre-v3 receipt hit (no digest computed) |
| `src/veracium/contribution.py` | D2 | `EXACT_EQUAL_PROV_FIELDS` loses the field (totality test forces it); snapshot shape changes → the defined digest collapse |
| `src/veracium/store/base.py` | D2 | `ReceiptSchemaBoundaryError(SupersessionIntegrityError)` defined + exported |
| `src/veracium/store/sqlite.py` | **D1** (`_SourceType` binding) + D2 (construction sites incl. the `model_copy(update=)` write; phase-2 era check; version-3 stamping; the by-stored-version projection selection with no fall-through) |
| `src/veracium/store/schema_version.py` | D2 | `SCHEMA_V7`, `SCHEMA_VERSION=7`, the sha-pinned declared no-op step |
| `src/veracium/store/migration.py` | D2 | the v6→v7 step (the declared no-op + version stamp, one transaction) |
| `src/veracium/portability.py` | D2 | `FORMAT_VERSION` 6; import drop rule |
| `src/veracium/lifecycle.py` | **D1** (`_SourceType` binding) + D2 (construction site removed; `test_lifecycle.py:324` reshaped) |
| `pyproject.toml` | **D1** | `pydantic>=2.7` (the `Field(deprecated=…)` floor — R5-3) |
| `.github/workflows/test.yml` | **D1** | a REAL minimum-dependency job (`pydantic==2.7.0`) beside the latest job (R6-4) |
| `specs/0007-store-schema-versioning.md` (accepted) | D2, same commit | the same-shape rule amendment block below (R6-2) |
| `specs/schema_evidence.py` + `specs/schema_model.py` + their tests | D2 | the same-shape resolver/HEAD-probe update (R6-2) |
| evidence artifacts (`schema_evidence` — BOTH directories) | D2 | the v7 row |
| `specs/0003-supersession-authority.md` (accepted) | D2, same commit | the §4f amendment block below |
| `specs/0014-maintenance-attribution.md` (accepted) | D2, same commit | the partition amendment block below |

**The verbatim amendment blocks (applied to the accepted specs in the D2
commit — implementation may not land while either still states the
superseded contract):**

> **0003 §4f amendment (0016 D2):** the receipt path gains an
> era-conditioned outcome that fires BEFORE any comparison. §4f's digest
> comparison happens ONLY for receipts whose `outcome_digest_version` is the
> current projection version (3). A receipt stamped below it refuses
> UNCONDITIONALLY on sight — no digest is computed, no comparison branch
> exists — raising `ReceiptSchemaBoundaryError` (a subclass of the integrity
> error); it is never treated as benign and never replayed.

> **0014 partition + version amendment (0016 D2):** `EXACT_EQUAL_PROV_FIELDS`
> loses `source_type` (the field is deleted from `Provenance`); the partition
> remains TOTAL over the post-D2 model (the totality test enforces the
> constant). **The digest-projection version increments to 3. The legal v3
> triples are exactly {(request_digest, 3, response_json),
> (NULL, 3, response_json)}; the v3 projection is the v2 construction
> computed over the post-D2 field set. Comparison rules: a version-3 receipt
> follows the ordinary contract; a version-1 or version-2 receipt refuses
> UNCONDITIONALLY on resubmission (`ReceiptSchemaBoundaryError`) — neither
> historical projection is computable post-D2, so no comparison is
> attempted. `validate_receipt_state` and its exhaustive oracle extend over
> every {1, 2, 3} triple in the same commit.** Consequence, accepted as part
> of the API break: requests differing only in the deleted field become
> identical.

> **0013 M10 amendment (0016 D2) — the multi-step planner, specified by the
> first spec to need two real steps:** a migration is a CHAIN of ADJACENT
> declared steps [b→b+1, …, n−1→n] — adjacency is unchanged; what M10 adds
> is the chain semantics. Every edge in the chain is individually declared
> and evidenced in the registry (0016's D2 commit declares the missing
> 2→3, 3→4, 4→5, 5→6 edges; 6→7 is the declared no-op, pin
> `2deae0327584cb0ed265b79f101843eba9e3b5e81b9092d08bf35326aa83ffe9`).
> Each step mints and consumes its OWN single-use `MigrationAuthority`
> bound to its adjacent pair and evidence snapshot; runs in its own
> transaction; writes its own terminal record; and stamps its destination
> durably before the next step mints — no authority spans steps; the
> durable stamp IS the seam. A mid-chain failure leaves the store at the
> last completed stamp (a legal accepted version) from which a re-run
> resumes idempotently. Fault is injected at every inter-step seam in the
> standing gates. The aggregate base→head production path is retired.

> **0007 §4-i amendment (0016 D2) — the same-shape rule:** two accepted
> versions may share a persistent shape (v6/v7 are the first pair). Where
> shapes collide, resolution is BY STAMP: a stamped store resolves to its
> `user_version`; an unstamped store matching a multi-version shape
> resolves to the OLDEST matching version, and adoption migrates it forward
> through the declared steps. The resolver and the HEAD release evidence
> probe implement this rule; `resolve` never returns None for a shape that
> matches at least one accepted version.

## 8. Claims and limits

- **Changelog (D1), the SUPPLIED notice text (R3-1):** "`SourceType` is
  deprecated and will be removed in <the named API-breaking release>. It has
  never influenced any decision. On ingest-derived records it restates
  `author_of_evidence`; directly-constructed records may carry any value,
  which nothing reads. Accessing the enum through the package or
  `veracium.schema` (including `import *` and pickling) now warns. NOT
  warned, by design: reading `provenance.source_type` on an edge, and model
  metadata (`model_fields`, `get_type_hints`) — those and only those.
  Reading `provenance.source_type` warns once per access. Hosts reading it
  from exports should stop."
- **Changelog (D2):** "**Back up your store before migrating — a v7 store
  does not open on older builds.** `SourceType`/`Provenance.source_type` removed
  (deprecated since 0.8.0). Behaviour is unchanged (the field gated nothing —
  the suite proves decision-projection identity; receipt identity changes by
  the defined collapse). Export format is now 6; older builds
  refuse new exports rather than misreading them. A supersession retry whose
  original committed before this upgrade is refused with a named error rather
  than guessed at."
- **What this does NOT establish:** it does not ship `evidence_basis` (frozen
  contract only, §1b); it does not improve any trust decision (nothing read
  the field); it does not make pre-D2 receipts replay-verifiable across the
  boundary (explicitly the opposite, fail-closed); D2 has NO runtime rollback: a v6 build refuses a
  v7 store (probed); recovery is the pre-migration backup.
- **Measurements:** consumer counts and reach claims carry their commands
  (§2c-ii); no other numbers appear.

---

## 9. Brief for the external reviewer

- **Least sure of, one:** the **on-sight refusal's completeness** — a
  pre-v3 receipt refuses before any digest work at both phases, proven by
  exploding-sentinel regressions. Is there a path to a pre-v3 receipt we
  have not enumerated (an import? an audit read?) where a digest could
  still be computed?
- **Least sure of, two:** whether the **seven-row matrix + the notice's
  un-warned remainder** is now exhaustive — field access, model
  metadata, both `dir()` surfaces, star-import namespace preservation, and
  the two-warning pickle round-trip are all ruled; is there a supported
  consumption path still unenumerated?
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
2. ~~D1 warning mechanism~~ — **RULED (research internal review,
   2026-08-11): EVERY public access path warns**, including
   `from veracium.schema import SourceType`, via a `schema`-module
   `__getattr__` that provides the enum lazily (not a normal binding during
   D1; internal code binds the private name). Package-namespace-only
   rejected — an unwarned common import path blindsides its users at D2.
   Any path that genuinely cannot warn is enumerated in the notice.
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
