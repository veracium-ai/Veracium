# Feature spec: procedural records and the `basis` axis (stages 1–3)

Spec-Status: draft

*Candidate authored by dev (2026-09-06) on Quentin's commission of the same
day — "Commission the basis spec but sequenced after (2), and scoped to
procedural content only" — where (2) is the ruling that the stage boundary is
content-type-relative and that for procedural content stage 4 (recommend)
does not exist yet at all. Both rulings are logged verbatim in
`COORDINATION.md` under `[Quentin]`. Internal reviewer: research (semantics,
trust-model consequences, any public claim). Full spec: it touches guarded
files (`schema.py`, `ingest.py`, the gate). See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | dev (veracium-69); the question and the axis from dev's first reading (2026-09-06); the scope, the sequencing and the commission Quentin's; three standing constraints research's (recorded in `COORDINATION.md`'s dev queue and carried in §2c, §4 and §10 here) |
| **Version** | **v9** — research's PRE-SEAL PASS on v8 (2026-09-06; batch rule), three items, all landed: **F-A** the one-result-per-visible-candidate accounting BROKE under truncation (a describable record ordered below the cap was in neither list — exactly on the population V-DESCRIBE-ORDER exists to test) → `DescribeResult` gains `total_describable: int` (the describable population BEFORE the cut) and V-RESULT-SCHEMA is scoped to before truncation, so `total_describable + len(withheld)` accounts for every visible record (§4a-ii, §6); **F-B** `relation_unregistered` is NAMED on describe and SILENT on recall — a host that shrinks its registry sees facts vanish from recall with no signal, and V-DECLARATIVE-UNCHANGED does not cover that population (its guarantee rests on the default registry) → said plainly in §4a and §8, §9's alternative weighed against the recall-side silence, and a cheap signal asked as §10 Q7 for round 2; the third homograph sentence restored to its measured literal ("Store the recovery codes in a password manager is what the team does") — a frozen must-not corpus needs the string, not an ellipsis (§6a). Confirmed by research against source, not read: the §6a figures re-derived from the measurement (exact); `_disclosure_for(author, relation, derived_from)` at `ingest.py:141-142`; Q6's wording canonical. Research CLEARS v9 for the round-2 seal. *Prior:* **v8** — the EXTERNAL ROUND-1 fold (verdict RETURN for revision, 2026-09-06, banked verbatim `outbox/0037-round1-verdict-verbatim.md` sha16 `4be410ce697bd171`; package `5d9ac247…` @ `af880b3`). Eight blocking findings, all spec-content, each reproduced at a line of v7 and folded: **F1** the MCP write path contradicted the library contract (`remember(basis=)` could not produce a procedural record without bypassing the sole producer) → a DEDICATED MCP `record_procedure` tool, capability-gated to `direct`, relation validated against the active registry; `remember` on BOTH surfaces rejects any basis (§4b, §4e). **F2** the describe RESULT contract was undefined → `DescribeResult` with a full schema and observable ordering (§4a-ii). **F3** §8 claimed "never reproduces executable detail" beside its own paraphrase limit → the ACTUAL guarantee everywhere: the `note` is never rendered; a summary matching the frozen recognition rule is withheld; a paraphrase passes (§4a-ii, §6, §8). **F4** Q3 unresolved → RESOLVED: research owns the recognition corpus (the 0029 condition: every expectation from the spec's text, OPEN where undetermined), frozen with a version and digest against THIS version before any implementation line, ± sets, change control by amendment, the v1 paraphrase boundary a stated limit (§6a, §10). **F5** §3b's "third-party shape" contradicted the matrix → deleted; a `use_only` procedural record yields the named non-description `use_only`; `hidden` and no-match are INDISTINGUISHABLE to an unauthorised principal, `use_only` and no-match need not be — scope decides whether you may know, disclosure what you may be told; and `withheld` is QUERY-BLIND so an id's presence cannot become a search oracle over a record the principal may not read (research's semantics; §3, §3b, §4a-ii, V-WITHHELD-QUERY-BLIND, oracle cells added). **F6** relation validation missing → `record_procedure` REQUIRES the relation to exist in the active registry with `relation_kind="procedural"`, else RAISES, nothing written (§4b, V-RELATION-VALID). **F7** registry totality overstated → kind is total over the ACTIVE registry, not over stored records; a stored edge whose relation left the registry is the named `relation_unregistered`, excluded from both blocks and from describe, never silently moved — a disclosed behaviour change for a host that shrinks its registry (§4a, §8, V-RELATION-UNREGISTERED). **F8** §5's relevance promise had no invariant → V-DESCRIBE-ORDER (above-cap population, stable ties, repeated runs, the null query). Corrections: `Relation(kind=…)` → `relation_kind` in §4e; the stale "three members" row is 0001 §2c-ii:175 (an as-of note added there, docs-only); ONE failure taxonomy (write-path failures RAISE with nothing written; read-path outcomes are RETURNED, named — §4b); `ProcedureDescription`'s fields and that no raw stored text appears in any field (§4a-ii); how `record_procedure` populates id, dates, evidence_ref, source_id, disclosure (§4b); default import is ATOMIC over the admitted set with procedural records refused per record and counted (§4e); the sibling's governance state stated canonically: the commission STANDS and is formally parked behind a mechanism-selection prerequisite (§10 Q6). Preserved as the reviewer named: host-declared kind; the blind extractor; exclusion from both blocks; `assertable` untouched; basis orthogonal; absence semantics; the lattice; import vs restore; recommendation outside; the residual disclosed. *Prior:* **v7** — **Q6 SCOPED by the owner: option (b), a sibling spec** (Quentin, 2026-09-06, verbatim "Scope Q6 as option b", logged under `[Quentin]`). The free-text render exposure is neither addressed here nor left unaddressed; §8's residual disclosure stays exactly as it is, which is what makes the deferral honest rather than silent. The sibling's SCOPE is recorded in §10 so it does not live in a conversation; its COMMISSION has NOT been granted (the owner's word was "scope", not "commission" — the distinction research held to). Why (b) and not (a), inherited by the sibling: (a) would have changed SHIPPED declarative behaviour — content recall returns today would stop being returned — the hazard class this spec avoided by scoping `basis` to procedural records, ridden in on a commission scoped to procedural records only; and the exposure PREDATES this spec and is not created by it. The internal round is complete from both seats; this version proceeds to external review. *Prior:* **v6** — Q6 RESHAPED on research's semantics (2026-09-06, before the commit): an episode is not a procedure but the record that one was mentioned (`Episode`'s own contract), so v1's answer stands — no procedural episode type; refusing or deleting the episode would destroy true history to hide text. But the exposure is not where Q6 put it: it is FREE TEXT RENDERED VERBATIM INTO MODEL CONTEXT, and there are at least two carriers — an assertable episode's `summary` (`gate.py:137`, the probe) and an assertable declarative edge's `note` (`graph.py:1116`, straight into `render_edges` and the grounded block) — so an episode-side kind would close one door and leave the sibling open, F2's partial-fix shape. Research's recommendation, carried into Q6 for Quentin: apply the imperative-shape refusal to free text AT THE RENDER CHOKE POINT V-RENDER-SITES already enumerates, for any record type — no new host field, completeness checkable by the existing sweep, claimed as a FLOOR (reduces, never closes: the text was never authored as a procedure). The trusted path this sits on is already measured (research: `user_attested_inference_framing` 0.42 [0.30, 0.55]; `controls` 0.667), so Quentin scopes it with the shape on the table. *Prior:* **v5** — the §6/§6a internal-review fold (research, 2026-09-06). **F4 (BLOCKING)** — EPISODES were not mentioned once: they reach model context on their own path (`gate.py:106` `partition_parts` returns `ep_lines` and `tp_ep_lines`), ordinary ingest writes one beside the edges, and an episode has NO relation — so "excluded by kind" could not see it (F2 through a door the kind check cannot see). PROBED, not argued: procedural text through ordinary `remember` with a scripted extractor produced ZERO edges and ONE episode, and recall's context carried the executable steps verbatim (§8, the measured residual). v5 settles all three cases: `record_procedure` writes NO episode (V-NO-EPISODE); ordinary ingest's episode path is TODAY's behaviour, unchanged, stated as the residual with the probe; whether v1 must ALSO govern procedural text arriving through ordinary ingest — which needs a host-declared EPISODE kind, a larger change — is §10 Q6, blocking, for Quentin. The edge-side concept is renamed `relation_kind` because `Episode.kind` already exists (`interaction | outcome`). **F5** — the `stated`/`observed` ORDER was never declared while two invariants leaned on "whole-set minimum": declared now beside the field — the lattice is `observed ≤ stated`, `observed` is the minimum, so absorption can only ever yield `observed` from a mixed set (the only order consistent with V-BASIS-CAP-ONLY). **V-CARRIERS** made derivable: the sweep basis is every `Provenance(` constructor and `model_copy(update=` site (both forms — 0016's tenth-site lesson) and every `provenance.` reader, never the hand list v4 carried. *Prior:* **v4** — research's correction of its OWN F3 recommendation (2026-09-06, before the first commit): "refuse on both paths" was too broad. `portability.py:21-30` defines `restore=True` as the operator's explicit assertion that the file is THIS store's own history — precisely the attestation `basis` requires — so refusing there costs backup fidelity for no trust gain and loses every procedural record of a store's own backup, silently to anyone not reading the refusal count. v4: the DEFAULT path refuses (the relay reading holds exactly); `restore=True` ACCEPTS the record with its declared basis; the invariant becomes V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE with the restore leg as a POSITIVE case (a refusal-only test would pass while backup/restore was broken). §8 names the precedent extended: the house has two moves for a field an import will not honour — CAP it (author/derived_from → THIRD_PARTY) and DROP the key (`source_type`, ≤v6 files); refusing the whole record is a third, stronger move, taken on the default path only. *Prior:* **v3** — the second internal-review fold (research, 2026-09-06, before the first commit): **F3** — `record_procedure` was NOT the sole producer at the store layer: `commit_outcome_import_plan` writes edges directly (one of the seven sites in 0029's own `EDGE_WRITE_SITE_RULINGS`, checked against the registry rather than the API surface), so an import could introduce a procedural record carrying a basis DECLARED BY A DIFFERENT HOST — 0026's relay shape, and a collision with §4b's "basis is a positive capability THIS host declares"; harmless while both bases are merely describable, a laundering route to recommendation the moment §4d's composition exists. v3 takes the first of three ways out: **import REFUSES procedural records** with a named outcome (`procedural_import_refused`), §8 states the limitation, and V-ONE-PRODUCER becomes true rather than reworded. V-ONE-PRODUCER's sweep basis is now 0029's registry × the raw-SQL sweep, never a fresh inventory (a second list of edge writers is the hand-list 0029 already paid for). *Prior:* **v2** — the §3a internal-review fold (research, 2026-09-06; two BLOCKING findings at the conclusion, both verified in code, both taken; Q1 ruled). **F1** — the extractor DECIDES KIND TRANSITIVELY by choosing the relation (`ingest.py:169` passes the registry's names into the extraction prompt), and with basis REQUIRED that made every extractor-emitted procedural edge a silent refusal fleet-wide through the DEFAULT registry — the declarative fail-closed hazard arriving by another door. v2: procedural relations are FILTERED OUT of the extractor's vocabulary at the extraction boundary, so the extractor can never emit one; procedural capture is an EXPLICIT host surface that carries basis (`Memory.record_procedure`). Kind is host-declared end to end, not only in principle. **F2** — `assertable=False` is a ROUTING signal today, not suppression (`gate.py:139`: not-assertable renders as a fenced third-party claim, Q5), so overloading it with "is procedural" would render a procedure as a fenced claim at every site v1 missed — the Tier 8 failure mode. v2: `Edge.assertable` is UNTOUCHED and type-correct; procedural records are excluded ONCE, BY RELATION KIND, at the recall/partition choke point, with a named outcome, and a V-TOTAL-style sweep derives every model-context render site and proves each reaches that choke point. **Q1 ruled (research, from the Tier 8 competitor arms, 0.25–0.90 guidance rates for procedural content that reached the answerer's context):** procedures are excluded from the UNVERIFIED block too, and §4a carries the sentence that keeps a later reader from "fixing" it by symmetry with Q5. **§8** now claims `executable_detail` as a FLOOR, not a guarantee: a paraphrase defeats it. *Prior:* **v1** — the candidate, 2026-09-06. |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research (requested 2026-09-06) · dev (author; may not self-approve) · workflow-platform unavailable (no such session exists this arc; recorded as the waiver, holder Quentin) |
| **External review** | round 1 sent 2026-09-06 (package `5d9ac247…` @ `af880b3`, CI 34049009899, both seats' legs green) and RETURNED the same day: RETURN for revision, eight blocking + seven corrections, "strong overall architecture" — folded as v8; round 2 after research's pre-seal pass |
| **Decision + date** | — |
| **Path** | full |
| **Scope** | PROCEDURAL records only. Declarative facts, `Edge.assertable`, recall's grounded/unverified partition and every shipped predicate on declarative records are UNCHANGED. Recommendation (stage 4) for procedural records is NOT specified here (§4d, a stated non-goal awaiting a harness contract). |

---

## 1. Problem and motivation

**The store cannot see procedural content, and cannot see whether such
content was stated or observed.** The relation registry has nineteen
relations and none is procedural (`DEFAULT_RELATIONS`, §2c-ii); the
extractor drops an out-of-vocabulary relation as `invalid`. A procedure —
"whenever a ticket arrives from X, do Y then Z" — therefore arrives as free
text and lands, if anywhere, under a declarative relation, where it is
governed exactly as a fact: `active ∧ ¬quarantined ∧ ¬use_only ∧ valid_now`
makes it assertable, and assertable content is rendered into the GROUNDED
block that a host's model acts on. That is the vacuum the external design
round's reviewer named and research's Tier 8 run measured: on the harness's
`inferred` cell (the speaker reporting *a pattern they observed* — "I have
noticed the team following this: …"), every probe is ingested as an attested
first-party statement, because that is all a host can declare, and the
store passes it at competitor rates (0.42 [0.30, 0.55] under family-level
clustering — **a behavioural observation on identical input, not a
provenance result**; research's correction of 2026-09-06). Two independent
routes reached the same gap: the reviewer's *"inferred procedures require
explicit policy because ordinary user-origin rules do not settle whether an
inferred procedure should be recommended"*, and dev's reading that
user-origin is the wrong axis because both a stated and an observed
procedure are user-origin.

**What happens if we do nothing.** Procedural content keeps entering the
action-oriented path (grounded recall context) with the same authority as a
stated fact, and a procedure the user merely *reported observing* is handed
to the model as something to follow. Under the adopted reference-monitor
model that is the store doing, on the inferred path, what it forbids on the
corroboration path: repetition conferring authority. And there is no way
for a host — or the harness that measures us — to declare otherwise, so the
number cannot move and the gap cannot close.

**The frame this spec adopts (Quentin's ruling 2).** The stage boundary is
content-type-relative. For DECLARATIVE facts stage 4 is shipped and governed
(`Edge.assertable` is stage 4's minimum rule minus the consequence check,
which is meaningless for a fact). For PROCEDURAL content stage 4 does not
exist: it must not be built without its consequence check, and that check
needs a harness contract we do not own. So this spec builds stages 1–3 for
procedural records — store, internal retrieval, DESCRIBE — and leaves
recommendation unavailable by default. An inferred procedure is not less
TRUSTED than a stated one; it is differently GROUNDED. `basis` is that axis.

**Alternatives rejected.**

- *A fourth `Disclosure` tier* — rejected on 0001's own reasoning ("the tier
  was never the problem; the author was"): basis is orthogonal to trust.
  An observed procedure from the user is fully user-authoritative and still
  not something to act on.
- *Carrying "observed" in `derived_from`* — blocked by design (0001, the
  0.1.7 laundering defence): `derived_from` may only cap trust, and
  "observed" is not a trust class of the source.
- *Reusing `needs_confirmation` as the carrier* — it is a RANKING input
  inside the assertable set ("confirm before relying", ranked first; set only
  by a CHALLENGED outcome, cleared only by `confirm_edge`), not a gate; a
  flagged record is still rendered as grounded.
- *Letting the extractor decide procedural-ness or basis from the text* —
  rejected by the round's ruling and by 0031's: that is the model deciding
  provenance. Both are declared by the host.
- *Applying `basis` to declarative facts too* — rejected for v1 by the
  commission's scope and for a reason worth recording so a later reviewer
  does not rediscover it: an observed-basis fact would become
  non-assertable, changing behaviour for EVERY existing edge, and the
  absence semantics for pre-existing records (§4c) would become a fleet-wide
  migration question. Procedural content has no shipped behaviour to
  migrate, so v1 avoids that question outright rather than deferring it
  silently. **Declarative basis is a stated non-goal of v1.**
- *Letting the extractor emit the procedural relation* (v1's shape) —
  rejected at internal review (F1): the extractor decides kind transitively
  by choosing the relation, and with basis required that is a silent
  fleet-wide refusal through the default registry. Procedural capture is an
  explicit host surface; the extractor never sees a procedural relation.
- *Overloading `Edge.assertable`* (v1's shape) — rejected at internal review
  (F2): not-assertable is a ROUTING signal today (render as a fenced claim),
  and "out of scope for this path" is a different proposition from "not safe
  to state as fact"; one predicate must not carry both.
- *Doing nothing and documenting it* — rejected: two independent reviewers
  reached the gap, and the shipped disclosure (`9baa936`) already says the
  labels are advisory; an advisory label that cannot be declared is not a
  label.

---

## 2. Field contracts touched

Consumers enumerated by command, not recalled (commands in §2c-ii; counts of
2026-09-06).

| field | read / written | its **documented** contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `Relation` (`schema.py:350`) — NEW field `relation_kind: Literal["declarative","procedural"] = "declarative"` | registry-declared | "a small, extensible default registry; hosts can add their own via config" | the extractor prompt (glosses) — **procedural relations are FILTERED OUT of `rel_names` at the extraction boundary (F1)**; ingest's vocabulary check (an extractor-emitted procedural relation is dropped as `invalid` like any out-of-vocabulary name); `authority.py` (functional); graph clustering | YES — every existing relation is declarative by default and unchanged; the extractor's view of the registry is byte-identical to today's |
| `DEFAULT_RELATIONS` — ONE new relation `follows_procedure` (`relation_kind="procedural"`, non-functional, subject `user`, object the procedure's description) | registry | as above | as above | YES — additive; a host may register further procedural relations |
| `EvidenceContext` (`schema.py:188`) — NEW keyword `basis` on `direct()` and `derived()`, closed domain `{"stated","observed"}`, REQUIRED when the event is procedural, REFUSED when it is not (§4b) | host-minted | 0011 E4: "absence must be a POSITIVE capability, not a missing argument"; the constructor refuses unknowns | `ingest.py` (`_validate_context`, `ingest_event`), `mcp_server.py` (the capability bridge), `Memory.remember` | YES — inherits E4's rule rather than setting its own (§4c) |
| `Provenance` — NEW field `basis: Optional[Literal["stated","observed"]] = None`, with the DECLARED ORDER `observed ≤ stated` (`observed` is the minimum; F5) | WRITTEN at ingest from the context; READ by the describe predicate | None = "not a procedural record" (absent BY CONSTRUCTION on every declarative record and on every record written before this version); never a default for a procedural record; "whole-set minimum" everywhere in this spec means the minimum under `observed ≤ stated`, so a mixed set yields `observed` — the only order consistent with V-BASIS-CAP-ONLY | export/import (the field serializes; import caps like every trust field — §4e), `adapt` (0030's raw adapter tolerates unknown keys), `contribution` payloads | YES — orthogonal to author/disclosure; cap-only (a host can declare `observed`, nothing can promote it) |
| `Edge.assertable` (`schema.py:528`) | **UNTOUCHED** (F2) | "safe to state as fact" — and today `not assertable` ROUTES a record to the fenced third-party block (`gate.py:139`, Q5) | the 22 call sites 0032 enumerated | YES — the predicate keeps both its meaning and its routing role; a procedural record's assertability is simply never consulted on the model-context path, because that path excludes procedurals BY RELATION KIND before it asks (§4a) |
| the model-context choke point — `gate.partition` / `partition_parts` (`gate.py:95`, `:123`) and recall's edge selection | procedural records EXCLUDED ONCE, BY RELATION KIND, with the named outcome `procedural_out_of_scope` (§4a) | GROUNDED (assertable) / UNVERIFIED (third-party claims, "fenced not suppressed") | `Memory.recall`, `answer`, `compile`, `proactive`, `selfcheck` — every site that renders records into model context, DERIVED by the §6 sweep | YES — both blocks keep their meaning; a procedure is neither a fact nor a claim, it is out of scope for the path, and the exclusion is one site the sweep can check |
| `Memory.record_procedure(user_id, summary, *, basis, context, relation="follows_procedure", note=None, when=None, evidence_ref=None, source_id=None) -> str` (the new edge id) — NEW | the ONLY producer of procedural records (F1, F3); constructs the edge directly, never through the extractor; the import commit refuses them on the default path; the RELATION must exist in the active registry with `relation_kind="procedural"` or the call RAISES and writes nothing (round-1 F6) | — | new; MCP's `record_procedure` tool is a capability-gated adapter to it (round-1 F1) | n/a — additive; neither the extractor path nor the import path can produce a procedural record |
| MCP `record_procedure` tool — NEW (round-1 F1) | the ONLY MCP write path for procedural records: `record_procedure(summary, basis, relation="follows_procedure", note=None, date=None, source_id=None)`; honoured under `capability=direct` only, refused under `none` with the same named outcome as an attempted elevation and counted like one; it validates the relation exactly as the library does and calls `Memory.record_procedure` | host-attested writes (0031 Phase A) | `mcp_server.py` | n/a — additive; MCP `remember` gains NOTHING and rejects any basis like the library path |
| `portability.import_memory` / `commit_outcome_import_plan` (an edge writer in 0029's `EDGE_WRITE_SITE_RULINGS`) | DEFAULT path REFUSES procedural records (named outcome; declarative records unchanged); `restore=True` ACCEPTS them with their declared basis (F3, corrected v4) | 0005: "an importing store's knowledge of an edge begins at ITS import"; the default path caps trust; `restore` is the operator vouching that the file is this store's own history | export/import round-trip tests, the 0005 boundary registry | YES — on the default path an imported basis is another host's declaration; under `restore` it is this host's own, re-asserted by the operator |
| `Memory.describe_procedures(user_id, *, query=None, principal=None, limit=None) -> DescribeResult` — NEW | the stage-3 surface; its full result schema and ordering are §4a-ii (round-1 F2) | — | new; MCP `describe_procedures` tool (same shape, JSON) | n/a — additive |

**Documentation stating the old meaning, updated in this change:**
`docs/concepts.md` (the disclosure paragraph gains ruling 2's sentence —
fact recall governed and shipped; procedural recommendation has no governed
type and is not built), `docs/api.md`, `docs/mcp.md`, the `Relation` and
`EvidenceContext` docstrings.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| the host's `basis` declaration on a procedural event | ABSENT → the ingest REFUSES and writes nothing (E4: absence is not a missing argument; a procedural event without a declared basis is a caller error) | not a str, or a str outside `{stated, observed}` → the constructor RAISES (E4's chosen resolution: refusal, nothing written) | — | a host declaring `stated` for content it observed — out of scope for the store (the host attests; 0031's rule) and stated in §8 | **V-BASIS-POSITIVE** (`test_procedural_ingest_requires_a_declared_basis`), **V-BASIS-CLOSED** (`test_basis_domain_is_closed_and_refuses_at_construction`) |
| a `basis` declaration on a DECLARATIVE event | absent — the ordinary case | present → REFUSED at ingest (basis is not applicable to declarative records in v1; accepting it silently would make declarative basis a hidden feature) | — | — | **V-BASIS-SCOPE** (`test_basis_on_a_declarative_event_is_refused`) |
| a stored procedural record with `basis=None` (written by a version that admitted the relation without the field, or DB-level tamper) | — | evaluated as `basis_unknown` → NOT describable, a NAMED non-allow (never a default, never a raise) | — | — | **V-ABSENCE-NAMED** (`test_procedural_record_without_basis_is_a_named_non_allow`) |
| the `relation` argument to `record_procedure` (round-1 F6) | absent → the default `follows_procedure` | not a str → RAISES, nothing written | unknown to the ACTIVE registry, or registered with `relation_kind="declarative"` → RAISES (`ValueError`, named `relation_not_procedural`), nothing written | a host passing a declarative relation to launder a procedure into the grounded block → RAISES | **V-RELATION-VALID** (`test_record_procedure_requires_a_registered_procedural_relation`) |
| a STORED edge whose relation is absent from the ACTIVE registry (a host shrank or renamed its registry after writing; round-1 F7) | — | — | the relation has no `relation_kind` to read → the named outcome `relation_unregistered`: excluded from BOTH model-context blocks and from `describe_procedures` (listed in `withheld` with that outcome when visible), never silently moved to a block, never dropped from the store; `introspect` still shows it | a relation reclassified declarative→procedural or the reverse between write and read → the record follows the ACTIVE registry's kind at read (the registry is the host's policy) and §8 discloses it as a host-side behaviour change | **V-RELATION-UNREGISTERED** (`test_unregistered_relation_is_named_and_out_of_every_path`) |
| the extractor's relation choice | drops out-of-vocabulary relations as `invalid` (unchanged) | — | the extractor filing a procedure under a DECLARATIVE relation (today's behaviour, unchanged: the text is treated as whatever it was filed under — stated in §8 as the residual) | the extractor emitting `follows_procedure` (from a prompt-injected name, or a model that has seen the docs) to reach the describe surface | the extractor NEVER SEES a procedural relation (its `rel_names` are filtered by relation kind at the extraction boundary) and an emitted procedural relation is dropped as `invalid` like any out-of-vocabulary name — **V-EXTRACTOR-BLIND** (`test_extractor_vocabulary_carries_no_procedural_relation`); kind is a property of the REGISTRY and total over the vocabulary — **V-KIND-REGISTRY** |
| the procedure's summary text (rendered by `describe_procedures`) | — | — | — | text crafted to read as instructions ("step 1: run …") — the render WITHHOLDS a summary matching the FROZEN recognition rule (§4a-ii, §6a) as `executable_detail`; the `note` is NEVER rendered; a paraphrase in non-imperative mood PASSES the rule and is the stated v1 limit (§8) | **V-NO-IMPLICIT-RECOMMEND** (`test_describe_withholds_the_frozen_rule_and_never_renders_the_note`) |
| data written by an older version (a v13 store) | no procedural relation existed → no procedural record exists; every existing edge is declarative and unchanged | — | — | — | **V-DECLARATIVE-UNCHANGED** (`test_every_pre_existing_edge_is_declarative_and_unchanged`) — the V-COMPAT pattern: the pre-feature oracle replays byte-identically |
| export files carrying procedural records (any `basis`), imported on the DEFAULT path | — | — | — | an export claiming `basis="stated"` for a procedure — a basis DECLARED BY ANOTHER HOST (0026's relay shape; 0005: an importing store's knowledge begins at ITS import) — **the default import REFUSES every procedural record**, named `procedural_import_refused`, declarative records in the same file unaffected; nothing about a foreign file can make a procedure describable on this side | **V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE** (`test_default_import_refuses_procedural_records`), **V-BASIS-CAP-ONLY** (`test_basis_can_only_subtract`) |
| the same files under `restore=True` (the operator's explicit assertion that the file is THIS store's own history — `portability.py:21-30`) | — | a procedural record with no `basis`, or one outside the closed domain → refused as a record (E4's malformed case; nothing written for it) | — | the operator has made exactly the attestation `basis` requires, so the record is ACCEPTED WITH ITS DECLARED BASIS; a forged `restore` flag is the operator's own act, out of the store's scope (the existing `restore` trust note) | **V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE** (the positive leg: `test_restore_round_trips_procedural_records_with_basis`) |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | result (2026-09-06) |
|---|---|---|
| no relation is procedural today | `python -c "from veracium.schema import DEFAULT_RELATIONS as D; print(len(D), [n for n in D if 'proced' in n])"` | `19 []` |
| `Relation` carries no content kind | `grep -n "^class Relation" -A 4 src/veracium/schema.py` | `name`, `functional`, `desc` |
| the extractor drops out-of-vocabulary relations | `grep -n "invalid" src/veracium/ingest.py` | the `invalid` drop at the vocabulary check |
| `EvidenceContext` has exactly two kinds and no basis | `grep -n "_KINDS\|basis" src/veracium/schema.py` | `_KINDS = ("direct", "derived")`; no `basis` |
| `needs_confirmation` is a ranking input, not a gate | `grep -n "needs_confirmation" src/veracium/__init__.py` | `:1050-1054` partition of the ASSERTABLE set by the flag; `:1537` the only setter (CHALLENGED outcome) |
| `confirm_edge` is the sole clearer | `grep -rn "needs_confirmation = False" src/veracium/` | `store/sqlite.py` (`confirm_edge`) only |
| the harness ingests the inferred cell as attested user statements | research, against `paper2/instrument/validation/tier8_KEY.json`: all 40 reporting probes `author: trusted` | verified by research 2026-09-06 (the only marker is the in-text frame) |
| the harness can declare basis per ingest step once the store offers it | research's resurfacing runner (harness repo, not this tree) already declares `author` per probe and asserts it against the class's expectation | research 2026-09-06: "a small change on my side when the field exists" |
| the MCP surface has no way to declare basis | `grep -n "def remember(" src/veracium/mcp_server.py` | `remember(text, author=None, ...)` — no basis, no relation kind |
| the extractor's vocabulary is the registry's names, passed into the prompt (F1's mechanism) | `grep -n "relations: dict\[str, Relation\]\|rel_names" src/veracium/ingest.py` | `:169` `relations=DEFAULT_RELATIONS`; `rel_names` into the distill prompt |
| `not assertable` ROUTES to the fenced block today (F2's mechanism) | `grep -n "not e.assertable\|not ep.assertable\|FENCED, not suppressed" src/veracium/gate.py` | `:139` — third-party lines built from records that are NOT assertable; "FENCED, not suppressed (Q5)" |
| shipped `recall` renders assertable records into GROUNDED context | `grep -n "GROUNDED" src/veracium/gate.py` | `:9`, `:154` — "you may state these as fact" |

---

## 3. Trust-class matrix — REQUIRED, blocking

Classes read from the enums today: `EvidenceAuthor` = {user, third_party,
system, assistant}; `Disclosure` = {mentionable, use_only, quarantined};
NEW `basis` = {stated, observed} on procedural records only. The operations
this change performs are (a) ingest of a procedural event, (b) the describe
predicate, (c) the exclusion from the gate's partition. None is directional
(no prior/incoming pair is merged: `follows_procedure` is non-functional and
absorption applies the shipped same-class rule unchanged, with `basis`
carried like disclosure — the whole-set MINIMUM: an `observed` member makes
the survivor `observed`).

| operation | author=user | author=third_party | author=system | author=assistant | disclosure=quarantined | disclosure=use_only |
|---|---|---|---|---|---|---|
| ingest procedural, basis=stated | stored, mentionable, describable | stored, use_only (0001 rule unchanged), NOT describable | stored (our own consolidation output), describable | stored, use_only, NOT describable | stored, NOT describable | NOT describable |
| ingest procedural, basis=observed | stored, mentionable, describable WITH the observed attribution | as above | as above | as above | as above | as above |
| ingest procedural, basis absent/malformed | REFUSED, nothing written | REFUSED | REFUSED | REFUSED | REFUSED | REFUSED |
| the model-context choke point (recall/answer/compile/proactive/selfcheck) | EXCLUDED BY RELATION KIND from GROUNDED and from UNVERIFIED, named `procedural_out_of_scope` — every class | EXCLUDED | EXCLUDED | EXCLUDED | EXCLUDED | EXCLUDED |
| `describe_procedures` | describable iff visible ∧ active ∧ valid_now ∧ ¬quarantined ∧ ¬use_only ∧ basis ∈ {stated, observed} ∧ summary passes the frozen rule; the render carries basis and provenance, never the note | the named non-description `use_only` (record listed in `withheld`, no text) | describable | the named non-description `use_only` | the named non-description `quarantined` | the named non-description `use_only` |

Cross-scope (round-1 F5, research's semantics): scope decides WHETHER a
principal may know a record exists; disclosure decides WHAT they may be
told. A procedural record HIDDEN from the principal is OMITTED entirely —
`hidden` and "no matching record" are INDISTINGUISHABLE to an unauthorised
principal by design (a distinguishable `hidden` would be an existence
oracle). A record VISIBLE to the principal but `use_only` (a cross-scope-
visible record is `use_only` by 0020's third-party shaping) yields the
NAMED non-description `use_only` in `withheld` — the principal is already
authorised to know it exists; they are not told its content. The oracle
(§6a) carries principal × visibility × author/disclosure, including the
cell that fails if this is inverted: an unauthorised principal probing for
a record that exists receives exactly the answer they receive for one that
does not.

- Can this operation cause a **user-asserted fact to become
  non-assertable**? No. Declarative records are untouched (V-DECLARATIVE-
  UNCHANGED). A procedural record was never a fact; it is never assertable,
  by construction, whatever its basis.
- Can it cause **non-user content to gain user-grade authority, confidence,
  or currency**? No. `basis` is cap-only; the describe predicate is a
  conjunction that only subtracts from the existing trust predicates.
- Can it **clear `needs_confirmation`**? No. v1 does not touch the flag
  (confirmation-as-promotion is §4d's non-goal; see §10 Q2).
- Does it **merge, drop, or overwrite provenance**? No. `basis` is added;
  absorption carries the whole-set minimum.

**Write-time.** Basis is declared at ingest by the host; nothing at
maintain time can set, clear or change it (V-BASIS-IMMUTABLE — the 0019 U4
shape: a stored basis never changes on same-id replace).

---

## 3b. Authorization and scope — *full specs only*

No user, tenant or scope boundary is crossed. `describe_procedures` takes
the same `principal`/`ScopeView` composition as recall: a procedural record
HIDDEN from a principal is OMITTED from the result entirely — not described,
not listed, indistinguishable from no match (the visibility gate is
outermost, as in 0030 V-SCOPE); a cross-scope-VISIBLE procedural record is
`use_only` under 0020's shaping and yields the named non-description
`use_only`, never a description in any shape (round-1 F5 deleted v7's
"third-party shape", which contradicted the matrix). No principal can see
anything they could not see before: procedural records are a NEW class that
recall never rendered, and `describe_procedures` shows less than recall
would have.

---

## 4. Behaviour

**One failure taxonomy, stated once (round-1 correction).** WRITE-path
failures RAISE and write nothing: a malformed or absent basis, a basis on
a declarative event, a relation that is unknown or not procedural, a
`when` beyond the skew. READ-path outcomes are RETURNED and NAMED, never
raised: every `Withheld.outcome`, `procedural_out_of_scope` at the choke
point, `relation_unregistered`. The only exceptions on a read path are the
existing ones (`ScopeError` for a principal without a policy — 0020's).
"Refuses" below means the write-path raise; "named outcome" means the
read-path return.

### 4a. What makes a record procedural — the registry, never the text

An EDGE is procedural iff its relation is registered with
`relation_kind="procedural"`. Relation kind is a property of the RELATION
REGISTRY (named `relation_kind` deliberately: `Episode.kind` already exists
and means `interaction | outcome`, nothing to do with this axis — F4's
adjacent-name collision), declared by
the host (the default registry ships one procedural relation,
`follows_procedure`), and is therefore TOTAL over the ACTIVE REGISTRY: every
relation the registry holds has exactly one kind, so no record filed under
a registered relation is "unclassified or mixed", and the round's
conservative ambiguous-type rule is satisfied for them by construction.
It is NOT total over stored records (round-1 F7): a host that removes or
renames a relation after writing leaves stored edges whose relation the
active registry does not hold. Such an edge is the NAMED outcome
`relation_unregistered` — its kind cannot be read, so it is treated
conservatively: excluded from BOTH model-context blocks and from
`describe_procedures` (where, if visible, it appears in `withheld` with that
outcome), never silently moved to a block, never dropped from the store,
still visible in `introspect`. Today an out-of-vocabulary stored edge IS
rendered by recall; this is therefore a behaviour change for a host that
shrinks its registry, disclosed in §8 and the changelog. Two things are
said plainly (pre-seal F-B): the exclusion is OBSERVABLE on describe
(`withheld` names it) and SILENT on recall (there is no withheld list;
the record stops appearing), so such a host learns why only if it calls
the describe surface — §10 Q7 asks for a cheap recall-side signal; and
V-DECLARATIVE-UNCHANGED holds because the default registry holds every
relation any shipped record carries, which means it does NOT cover the
one population at risk, a custom registry that shrinks.

**The extractor never sees a procedural relation (F1).** The registry's
procedural relations are filtered out of the vocabulary handed to the
extraction prompt, so the model cannot emit one, and an emitted procedural
name is dropped as `invalid` exactly like any out-of-vocabulary relation.
Kind is therefore host-declared END TO END, not only in principle: the sole
producer of a procedural record is the explicit surface
`Memory.record_procedure(user_id, summary, *, basis, context, note=None)`,
which constructs the edge directly under a procedural relation and REQUIRES
the basis the host must declare. Text the extractor reads as procedural is
treated exactly as today — filed under whatever declarative relation it
chooses, or dropped — so upgrading changes no extractor outcome (§8 names
this residual).

**A procedural record never enters the model-context path — excluded ONCE,
BY RELATION KIND, at the choke point (F2).** `Edge.assertable` is UNTOUCHED: it means
"safe to state as fact" and, today, `not assertable` ROUTES a record into the
fenced third-party block ("FENCED, not suppressed", `gate.py:139`, Q5).
"Out of scope for this path" is a different proposition from "not safe to
state as fact", and one predicate does not carry both. So the partition
(`gate.partition` / `partition_parts`) and recall's edge selection exclude
procedural records by relation kind BEFORE assertability is consulted, with the
named outcome `procedural_out_of_scope`; §6's sweep derives every site that
renders records into model context and proves each reaches that one
exclusion. This is "recommend unavailable by default" made concrete: the
action-oriented path never carries a procedure.

**Episodes (F4).** Episodes reach model context on their own path — the
partition returns episode lines for both blocks — and an episode has no
relation, so relation kind cannot exclude one. Three cases, each settled:
(1) `record_procedure` writes NO episode — the procedural edge is the whole
record, and V-NO-EPISODE pins it (the ordinary ingest path DOES write one,
so a later change could add it without a test noticing); (2) therefore no
procedural record produced by this spec's surface reaches context through
an episode; (3) procedural TEXT arriving through ORDINARY ingest is
today's behaviour and UNCHANGED by this spec: V-EXTRACTOR-BLIND drops the
edge, and the episode carries the text into context exactly as it does
today — measured, not argued (§8). Governing that path needs a
host-declared EPISODE kind, which is a larger change than this
commission's scope; it is §10 Q6, blocking, for Quentin.

**Excluded from the UNVERIFIED block too — Q1, ruled by research from the
data.** The fenced block's own rule ("a quarantined claim stays visible as a
claim rather than vanishing", Q5) is right for declarative claims and WRONG
here, and the reason must be stated so nobody later restores symmetry: the
harm from a FACT rendered as a claim is a wrong belief; the harm from a
PROCEDURE rendered as a claim is an ACTION. Across the Tier 8 competitor
arms, procedural content that reached the answerer's context was handed
back as guidance at family-level rates of 0.25–0.90 — the unverified block
is context, and context is what a host renders into a prompt.

**4a-ii. The describe surface — the result contract (round-1 F2).**

```
Memory.describe_procedures(user_id, *, query: Optional[str] = None,
                           principal=None, limit: Optional[int] = None) -> DescribeResult

DescribeResult:
    descriptions:      list[ProcedureDescription]   # the describable records, ORDERED (below), cut at `limit`
    total_describable: int                          # the describable population BEFORE the cut (pre-seal F-A)
    withheld:          list[Withheld]               # visible-but-not-describable records, never cut
    truncated:         bool                         # True iff len(descriptions) < total_describable
    query:        Optional[str]                 # echoed, normalized (lower-cased, whitespace-collapsed)

ProcedureDescription:                          # NO raw stored text in any field:
    edge_id:      str                           #   the record's id (row-sourced)
    relation:     str                           #   the registered relation name
    gloss:        str                           #   the registry's one-clause gloss for the relation
    summary:      str                           #   the record's `object` — the host's gloss-level name of the
                                                #   procedure, the ONLY stored text that is ever rendered
    basis:        Literal["stated", "observed"]
    attribution:  str                           #   "you said you follow …" / "a pattern you reported observing: …",
                                                #   composed from basis + summary, never from the note
    author:       str                           #   EvidenceAuthor value
    observed_at:  datetime; valid_from: datetime
    disclosure:   str                           #   always "mentionable" here (use_only/quarantined are withheld)

Withheld:
    edge_id: str
    outcome: Literal["not_procedural", "relation_unregistered", "inactive", "not_yet_valid",
                     "quarantined", "use_only", "basis_unknown", "executable_detail"]
```

The `note` (where step-level detail lives if the host supplied it) appears
in NO field of either type; a hidden record appears in NEITHER list (§3).
One result per VISIBLE candidate, BEFORE truncation: every procedural
record visible to the principal is describable or withheld, never both
and never neither, and `total_describable + len(withheld)` is the visible
population. `descriptions` is then cut at `limit`, so a describable record
below the cut is in neither list — `total_describable` is what keeps the
population accountable after the cut (`total_describable -
len(descriptions)` records were cut; pre-seal F-A: `truncated` alone says
that a cut happened, not what it removed). `withheld` carries the id and
the named outcome only.

**Predicate.** A visible record is described iff
`relation registered ∧ relation_kind == procedural ∧ active ∧ valid_now ∧
¬quarantined ∧ ¬use_only ∧ basis ∈ {stated, observed} ∧ summary passes the
frozen recognition rule (§6a)`; the first failing conjunct, in that order,
names the withheld outcome. There is no default allow and no untyped
outcome.

**Ordering (observable, deterministic).** The query ORDERS `descriptions`;
it never filters either list. With a query: descending relevance, where
relevance is the count of query tokens present in the record's `{subject,
relation, object}` tokens (the store's existing `_rel` tokenisation:
lower-cased alphanumeric runs; the `note` is NOT scored — it would let
step text influence ranking); ties by `valid_from` descending, then
`edge_id` ascending; zero-relevance records follow, in the same tie order.
With `query=None`: `valid_from` descending, then `edge_id` ascending.
`limit` defaults to `MemoryConfig.max_subgraph_edges`; the population is
ordered BEFORE the cut and `truncated` says whether a cut happened.
Repeated calls on an unchanged store return byte-identical results.

**`withheld` is QUERY-BLIND (research, round-1 F5's second half):** its
membership and its order (`valid_from` descending, `edge_id` ascending;
never truncated) do not depend on the query. If it were query-filtered,
an id's PRESENCE would be the leak: a principal entitled to know that a
`use_only` record exists could learn what it is ABOUT by varying the
query — `describe_procedures(query="audit log")` listing it says it
concerns the audit log — and a wordlist would reconstruct the topic of a
record they may never read, a search oracle built from an outcome
designed to disclose nothing. The property is invisible in the API's
shape, so V-WITHHELD-QUERY-BLIND states it and the oracle carries its
failing cell: the same record, two different queries, identical
`withheld`. (The premise it rests on was checked, not assumed: edge ids
are random — `f"{prefix}-{uuid4().hex[:12]}"`, `ingest.py:30` — so an id
discloses nothing about content.)

**What the render guarantees (round-1 F3 — the actual guarantee, not the
absolute claim):** the `note` is never rendered, in any field; a summary
matching the FROZEN recognition rule (§6a — research's corpus, its digest
recorded before implementation) is withheld as `executable_detail`; a
description that reproduces a procedure's steps in the system's own voice
IS a recommendation whatever its framing (round 5), and these two defences
are what stand between a summary and that. **What it does not guarantee:**
a summary that carries the same content in non-imperative mood ("you could
disable the audit log first") PASSES the rule; that is the stated v1
paraphrase boundary (§6a, §8), a limit and not a guarantee.

### 4b. The ingest contract — basis is a positive capability

A procedural record is written only by `record_procedure`, and only with a
declared basis: `EvidenceContext.direct(basis="stated")`,
`direct(basis="observed")`, or `derived(X, basis=...)`. The constructor
refuses a basis outside the closed domain (raises; nothing written).
`record_procedure` refuses a context that carries no basis (raises; nothing
written). The extractor path (`ingest_event` / `remember`) REFUSES a context
that carries a basis (raises) — it cannot produce a procedural record (F1),
so a basis there is a caller error, and accepting it silently would ship
declarative basis as a hidden feature. No upgrade path turns an extractor
outcome into a refusal: the extractor's vocabulary is unchanged.

**The relation (round-1 F6).** `record_procedure` REQUIRES its `relation`
to exist in the ACTIVE registry with `relation_kind="procedural"`; a name
the registry does not hold, or one registered declarative, RAISES
(`ValueError`, `relation_not_procedural`) and writes nothing. The sole-
producer invariant therefore proves what it names: this producer writes
only procedural relations. A relation reclassified AFTER the write is read
under the active registry's kind at read time (§4a, `relation_unregistered`
if removed).

**What `record_procedure` writes** (round-1 correction): a new `Edge` with
`id` minted like `remember`'s (`e-<12 hex>`), `subject="user"`, the given
`relation`, `object=summary`, `note=note or ""`, `valid_from=when or
utcnow()` (a `when` beyond `MAX_FUTURE_SKEW` refuses as ingest does),
`provenance=Provenance(author_of_evidence=<from the context: USER for
direct(), the declared class for derived(X)>, evidence_ref=evidence_ref or
f"procedure:{id}", observed_at=valid_from, source_id=source_id,
disclosure=_disclosure_for(author, relation, derived_from) — the shipped
rule, so a derived-from-third-party procedure is use_only exactly as a fact
would be — basis=<from the context>)`. No episode is written (V-NO-EPISODE).
Returns the new edge id.

**Through MCP (round-1 F1): a DEDICATED `record_procedure` tool, not a
`basis` on `remember`.** `remember` on both surfaces never carries a basis
and rejects one. The MCP tool `record_procedure(summary, basis,
relation="follows_procedure", note=None, date=None, source_id=None)` is a
capability-gated adapter to `Memory.record_procedure`: under
`capability=direct` it validates the relation exactly as the library does
(exists ∧ procedural, else the tool returns the named refusal
`relation_not_procedural` and writes nothing) and calls through with
`context=EvidenceContext.direct(basis=basis)`; under `capability=none` it
REFUSES with the same named outcome as an attempted elevation, counted like
one — a host that has not attested first-party capture cannot declare a
basis. MCP also gains `describe_procedures(query=None)` returning
`DescribeResult` as JSON.

(The failure taxonomy these follow is stated once, at the head of §4.)

### 4c. Absence semantics — chosen once

Two situations, distinguished as 0011 E4 distinguished them:

- **At ingest, absence or malformation REFUSES and writes nothing.** A
  procedural event without a basis is a caller error, not a policy input.
- **At evaluation, absence is `basis_unknown`, a named non-allow.** A stored
  procedural record with `basis=None` (a future relation registered as
  procedural over records written before the field, or tamper) is not
  describable, never described by default, never raised on.

Pre-existing records: there are NONE to migrate. No relation is procedural
today (§2c-ii), so every record written before this version is declarative
and `basis=None` on it means exactly "not applicable". This is why the
scope is procedural-only: the three options for declarative absence
(default `stated` = trusted-by-omission; fail-closed = every existing edge
non-recommendable on upgrade; migration backfill = the store asserting
provenance on the host's behalf) do not arise, and the spec records that
they do not arise rather than choosing among them silently. A later spec
that extends basis to declarative records MUST choose one.

### 4d. What v1 does NOT build — recommendation

Stage 4 (recommend) does not exist for procedural records and is not
specified here. In particular this spec does NOT make an `observed`-basis
record recommendable after `confirm_edge`, although that composition
("history never confers authority; a capability increase needs an
independent governed event") is the natural next step: turning confirmation
into a GATE changes what a confirmation means, and the harness contract that
would consume a recommendation does not exist. A recommend predicate for
procedural records requires its consequence check; without it the
predicate must not be built (ruling 2). §10 Q2 carries this.

### 4e. Interfaces and migration

- Library: `Relation(relation_kind=...)`, `EvidenceContext.direct(basis=)` /
  `derived(X, basis=)`, `Provenance.basis`, `Memory.record_procedure`,
  `Memory.describe_procedures`, `DescribeResult`, `ProcedureDescription`,
  `Withheld`.
- MCP: a new `record_procedure` tool (capability-gated adapter, §4b) and a
  new `describe_procedures` tool; `remember` UNCHANGED and rejecting any
  basis.
- CLI: `--basis` beside `--author`/`--derived-from` (the same hardcoded
  list hazard 0001 recorded: both carriers change in one commit).
- Export: `provenance.basis` serializes; the format version is unchanged
  (an additive optional key; a v2 reader ignores it — verified by test).
- Import: procedural records in an export file are REFUSED on the DEFAULT
  path (F3) — a basis in a foreign file was declared by another host, and
  0005's principle applies — and ACCEPTED WITH THEIR DECLARED BASIS under
  `restore=True` (v4): `restore` is defined as the operator's assertion that
  the file is this store's own history, which is exactly the attestation
  basis requires, so a store's own backup round-trips its procedures.
  Declarative records import as today on both paths. Export serializes
  procedural records on both paths. **Atomicity (round-1 correction):** the
  default import is ATOMIC over the ADMITTED set — procedural records are
  refused PER RECORD before the commit (the importer's existing per-record
  skip shape), counted in the report as `procedural_refused`, and the
  admitted declarative records commit as ONE transaction exactly as today;
  a file mixing both therefore imports its declarative records in full and
  none of its procedural ones, and the report says so. Nothing partial is
  ever committed.
- Migration: NONE. The relation registry is code, not schema; `basis` is a
  JSON field inside the existing payload. The pre-feature oracle replays
  byte-identically (V-DECLARATIVE-UNCHANGED).
- Unrecoverable: nothing; the change is additive and reversible (§7).

---

## 5. Regime analysis — where does this behave differently?

- **Scale:** the describe surface is a filtered read over the user's
  procedural records; it shares recall's cap (`max_subgraph_edges`, the
  default `limit`) and is tested at the truncation regime: a store with more
  procedural records than the cap must describe by the §4a-ii order, never
  store order, with stable ties and identical repeated runs — the 0.x
  regime defect's shape, pinned by V-DESCRIBE-ORDER (round-1 F8).
- **Cold vs warm:** none; no cache.
- **Density:** many procedural records under one subject are non-functional
  and accumulate; absorption's same-class rule applies with the whole-set
  minimum basis. Tested at the absorption regime.
- **Tests reach the regimes** (§6); the feature is on by default (the
  registry ships one procedural relation) but INERT until a host declares a
  procedural event — no shipped host does today, so the default-on state
  changes no existing behaviour (V-DECLARATIVE-UNCHANGED).

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **V-DECLARATIVE-UNCHANGED** every pre-existing edge is declarative; recall, context, export and MCP reproduce the pre-feature oracle byte-identically (the 0029 V-COMPAT oracle, extended with a procedural-free store) | `test_every_pre_existing_edge_is_declarative_and_unchanged` | CI |
| **V-KIND-REGISTRY** a record's kind is the registry's declaration for its relation, total over the vocabulary; no text feature decides it (mutant: a classifier keyed on the text must NOT change any kind) | `test_record_kind_is_registry_declared_never_inferred` | CI |
| **V-EXTRACTOR-BLIND** (F1) the vocabulary handed to the extraction prompt carries NO procedural relation, for the default registry and for any host registry (the filter is by relation kind); an extractor emitting a procedural name is dropped as `invalid`, nothing written; mutant: a registry with a procedural relation must produce a prompt byte-identical to the same registry without it | `test_extractor_vocabulary_carries_no_procedural_relation` | CI |
| **V-ONE-PRODUCER** (F1, F3) `record_procedure` is the only site that can write a procedural relation from THIS host's declaration — the sweep basis is 0029's OWN write-site registry (`EDGE_WRITE_SITE_RULINGS` × the raw-SQL sweep of `tests/test_0029_carrier.py`), never a fresh inventory; every other site either cannot receive a procedural relation (the extractor path, V-EXTRACTOR-BLIND) or refuses it by relation kind on the default path (the import commit); the one other admitting site, `restore=True`, admits only what this store previously wrote and the operator re-asserts; a write site absent from the registry fails 0029's gate first | `test_record_procedure_is_the_sole_producer` | CI |
| **V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE** (F3, corrected v4) on the DEFAULT path an export's procedural records are refused with the named outcome `procedural_import_refused`, declarative records in the same file import unchanged, and no foreign `basis` reaches a stored record; under `restore=True` the SAME file round-trips its procedural records WITH their declared basis, byte-identical to the exporting store's rows (the positive leg — a refusal-only test would pass while backup/restore was broken); a restore-path record with a missing or out-of-domain basis is refused as malformed | `test_default_import_refuses_procedural_records` + `test_restore_round_trips_procedural_records_with_basis` | CI |
| **V-OUT-OF-PATH** (F2 + Q1) a procedural record is excluded BY RELATION KIND at the model-context choke point with the named outcome `procedural_out_of_scope`, for every author × disclosure × basis cell (enumerated from the enums), and appears in NEITHER block; `Edge.assertable` is byte-unchanged (its source pinned) | `test_procedural_records_never_reach_model_context` + `test_assertable_is_untouched` | CI |
| **V-RENDER-SITES** (F2) every site that renders records into model context — DERIVED by sweep (gate, recall, compile, proactive, selfcheck), never hand-listed — reaches the one exclusion; a new render site without it fails here | `test_every_model_context_site_excludes_by_kind` | CI |
| **V-BASIS-POSITIVE** a procedural event without a declared basis REFUSES at ingest and writes nothing (store byte-identical after the refusal) | `test_procedural_ingest_requires_a_declared_basis` | CI |
| **V-BASIS-CLOSED** a basis outside `{stated, observed}` (any type, incl. unhashable) raises at construction; nothing written | `test_basis_domain_is_closed_and_refuses_at_construction` | CI |
| **V-BASIS-SCOPE** a basis on a declarative event is refused | `test_basis_on_a_declarative_event_is_refused` | CI |
| **V-ABSENCE-NAMED** a stored procedural record with `basis=None` yields the named non-allow `basis_unknown`, never a default, never a raise | `test_procedural_record_without_basis_is_a_named_non_allow` | CI |
| **V-BASIS-CAP-ONLY** no operation (same-id replace, absorption, import, confirm, reinforcement) can move a record from `observed` to `stated`; absorption carries the whole-set minimum | `test_basis_can_only_subtract` | CI |
| **V-BASIS-IMMUTABLE** a stored basis never changes on same-id replace (the 0019 U4 shape) | `test_stored_basis_is_immutable` | CI |
| **V-DESCRIBE-CONJUNCTION** `describe_procedures` describes iff every conjunct holds, in the stated order, and otherwise returns the FIRST failing conjunct's named outcome; the outcome set is closed and enumerated exhaustively (a 0013-style oracle over the cell product, §6a) | `test_describe_outcomes_are_named_and_total` | CI |
| **V-RESULT-SCHEMA** (round-1 F2; pre-seal F-A) BEFORE truncation every visible procedural record is in exactly ONE of `descriptions` / `withheld`; after the cut `total_describable + len(withheld)` equals the visible population, `len(descriptions) == min(total_describable, limit)`, and `truncated == (len(descriptions) < total_describable)` — asserted on a store ABOVE the cap; no field of either type carries the `note` or any raw stored JSON; the query echo is normalized | `test_describe_result_schema_accounts_for_every_visible_record` | CI |
| **V-DESCRIBE-ORDER** (round-1 F8) with more procedural records than the cap, `descriptions` is the §4a-ii order (relevance ⟶ valid_from desc ⟶ edge_id asc; recency then id under a null query), the cut is applied AFTER ordering, ties are stable, and ten repeated calls on an unchanged store are byte-identical; a store-order result fails | `test_describe_orders_by_relevance_above_the_cap_and_is_stable` | CI |
| **V-NO-IMPLICIT-RECOMMEND** (round-1 F3, the actual guarantee) the `note` is rendered in NO field; a summary matching the FROZEN recognition rule (§6a) is withheld as `executable_detail`; must-match AND must-NOT-match cases from the frozen corpus, the homograph facts by name; the paraphrase boundary is asserted as a KNOWN PASS (a control that documents the limit rather than a test that pretends it away) | `test_describe_withholds_the_frozen_rule_and_never_renders_the_note` | CI |
| **V-SCOPE-OUTERMOST** (round-1 F5) a HIDDEN procedural record appears in neither list — an unauthorised principal's result for an existing hidden record is byte-identical to the result for a nonexistent one (the existence-oracle cell); a VISIBLE `use_only` or `quarantined` record is in `withheld` with that named outcome and no text | `test_hidden_is_indistinguishable_from_no_match` + `test_use_only_is_named_not_described` | CI |
| **V-WITHHELD-QUERY-BLIND** (round-1 F5, research) for the same principal and store, `withheld` — membership and order — is byte-identical across any two queries and the null query; a query-dependent `withheld` (the search-oracle mutant: filter it by relevance) fails | `test_withheld_membership_is_independent_of_the_query` | CI |
| **V-RELATION-VALID** (round-1 F6) `record_procedure` raises and writes nothing for a relation that is unknown to the active registry, not a str, or registered declarative; the store is byte-identical after the refusal; control: the registered procedural relation writes | `test_record_procedure_requires_a_registered_procedural_relation` | CI |
| **V-RELATION-UNREGISTERED** (round-1 F7) a stored edge whose relation is absent from the active registry is `relation_unregistered`: in neither model-context block, in `withheld` when visible, still in the store and in `introspect`; a registry that regains the relation restores it; control: the same edge under the full registry behaves per its kind | `test_unregistered_relation_is_named_and_out_of_every_path` | CI |
| **V-HOST-DECLARED** (round-1 F1) through MCP the ONLY procedural write path is the `record_procedure` tool: under `capability=direct` it validates the relation and writes through the library surface; under `none` it refuses with the attempted-elevation outcome, counted; MCP `remember` with any basis-shaped input writes nothing and returns the named refusal | `test_mcp_record_procedure_is_the_only_procedural_write_path` | CI |
| **V-NO-EPISODE** (F4) `record_procedure` writes NO episode: the user's episode count is unchanged by a procedural write, and no episode text contains the procedure's summary or note; control: ordinary `remember` of the same text writes one | `test_record_procedure_writes_no_episode` | CI |
| **V-CARRIERS** every carrier of `basis` accounts for it in one commit — the sweep basis is DERIVED: every `Provenance(` constructor site and every `model_copy(update=` site (both forms, 0016's tenth-site lesson) plus every `provenance.` reader in src, each classified as carrying, passing through, or not applicable; a site absent from the classification fails | `test_basis_reaches_every_carrier` | CI |

Standing checks that must not regress: injection asserts 0 · cross-user leaks
0 · trust canaries 0 · the 0029 corpus 19/19 · the 0030 module 29/29.

### 6a. Acceptance measurement — REQUIRED, FINITE

A correctness gate over a frozen scripted corpus. **Ownership (round-1 F4,
resolved):** RESEARCH freezes the expectations, DEV owns the runner — the
0029 pattern, for its reason: the seat that implements may not set its own
bar. Research's self-imposed condition applies verbatim: every expectation
derives from THIS spec's text, never from dev's plan or code, each carrying
the line that determines it; where the spec does not determine a value it
is marked OPEN and asked, never guessed. The freeze happens against THIS
version (a corpus frozen against a spec under revision freezes the wrong
bar) and BEFORE any implementation line.

- **Artifact and version:** `tests/eval/procedural_describe/MANIFEST.json`
  (research-authored, dev-placed), versioned by amendment, its sha256
  recorded in `## Review closure` at the freeze and at every amendment.
- **Cells:** author × disclosure × basis × {active, inactive, future
  valid_from} × {visible, hidden, cross-scope-visible} × {plain summary,
  imperative summary, paraphrased summary} × {registered, unregistered
  relation}, each with its expected `DescribeResult` membership and named
  outcome AND its expected ABSENCE from recall's two blocks; the existence-
  oracle cell (an unauthorised principal probing an existing hidden record
  vs a nonexistent one) is in it by name.
- **The recognition rule:** research's frozen procedure texts supply the
  imperative-opener and step-marker sets, DERIVED at test time from the
  corpus rather than hand-listed; the must-match set is those texts; the
  must-NOT-match set holds realistic declarative summaries and, BY NAME,
  the two failure modes research measured for any first-word-of-clause
  imperative rule: (i) INTERROGATIVES — on 11,088 real user sentences a
  first-word rule fired on 17.2%, 84% of those questions ("Do you have any
  tips on…"), the single opener `do` accounting for 77% of the false
  positives; (ii) clause-initial NOUN/VERB HOMOGRAPHS — "Archive access is
  granted to the ops group", "Email is handled by the infra team", "Store
  the recovery codes in a password manager is what the team does" (the
  measured literals — a frozen must-not corpus needs the string, never an
  elision). Beside them the corpus
  records the rule's error in the other direction on the same real text:
  it caught 31.6% of procedural texts, every miss structural (quote-
  stripped spans). Those are not this surface's numbers — its inputs are
  host-authored summaries, not arbitrary user text — but they are what the
  rule's error looks like when measured, and the reviewer will ask.
- **The v1 paraphrase boundary, a stated limit:** exact-form recognition
  only. A paraphrased summary is an OPEN-and-answered cell whose expected
  outcome is DESCRIBED (the rule does not fire), asserted as a known pass —
  the corpus documents the limit rather than pretending it away, and §8
  claims no more.
- **Change control:** a corpus revision is an amendment with a superseding
  digest, recorded as a closure row stating what it closed; the runner pins
  the digest and fails on any other bytes (the 0029 runner's shape).
- Pass = 100% of cells.

**The Tier 8 `inferred` cell — stated plainly (research's constraint 1):**
the number CANNOT MOVE until this store offers `basis` AND the harness
declares it (`basis` beside `author` in the ingest dict, per research's
existing per-probe declaration pattern). The first post-feature measurement
is therefore a HARNESS change as much as a behaviour change, and must be
reported as such: the cell measures the adapter's ingest choice until then.
The expected post-feature result, if the harness declares the inferred
probes as `follows_procedure` + `observed`: recall recommends them at 0.00,
because procedural records never enter the partition — and the same for
`stated`. The cell then measures describe, not recommend, and a separate
probe class is needed for the describe surface.

---

## 7. Failure modes and reversibility

- **Silent failure:** a host registering a procedural relation over
  existing records would make those records procedural without a basis →
  `basis_unknown`, not describable, and — the visible symptom — gone from
  recall's blocks. First symptom: the host's recall loses those facts. This
  is why V-KIND-REGISTRY's mutant and V-DECLARATIVE-UNCHANGED exist, and why
  §4a states that re-registering an existing relation as procedural is a
  breaking host change (documented; not prevented — the registry is the
  host's).
- **Reversible:** fully. Remove the relation from the registry and the
  records are out-of-vocabulary (unchanged bytes, invisible); remove the
  field and every record still parses (`basis` is optional).
- **Partial failure:** ingest refusals write nothing (the existing
  transaction shape); the describe surface is read-only.
- **New attack surface:** a third party cannot declare basis (the context
  is host-minted; through MCP it is capability-gated) and cannot reach the
  procedural relation through text (V-EXTRACTOR-BLIND). The describe
  surface renders less than recall would have. The imperative-shape check
  is the one new text-dependent decision; it can only REFUSE, and it is a
  floor (§8).

---

## 8. Claims and limits

**What we will say.** "Procedural records are a new, host-declared content
kind with a host-declared basis (`stated` / `observed`). They are never
asserted as fact and never enter recall's grounded or unverified blocks;
they are describable through a dedicated surface that names their basis,
never renders a record's note, and withholds a summary that matches a
frozen recognition rule for imperative step text. Recommendation of
procedures is not provided — it awaits a harness contract. A host that
removes a relation from its registry after writing will find those records
withheld from recall as `relation_unregistered` rather than rendered —
named on the describe surface, silent on recall."

**What this does NOT establish.** That a described procedure is not acted
on: a host that reads a description into an action has made that choice
(the shipped disclosure). That no description carries executable content:
the guarantee is exactly the two defences named above — the note never
rendered, the frozen rule applied to the summary — and a summary carrying
the same content in non-imperative mood PASSES the rule (the v1 paraphrase
boundary, §6a, asserted as a known pass rather than claimed away). That procedural text the
EXTRACTOR reads is governed: it is not — such text is filed under a
declarative relation or dropped exactly as today (the residual v1 leaves,
by design, so that upgrading changes no extractor outcome); a host that
wants it governed calls `record_procedure`. **That procedural TEXT through
ordinary ingest stays out of model context: it does not, today or after
v1.** Probed 2026-09-06 (a scripted extractor returning no triples and an
episode summary; `remember` of "whenever a ticket arrives from the billing
queue I disable the audit log first, then escalate to on-call" under
`author=USER`, `context=direct()`): ZERO edges, ONE episode, and recall's
context rendered the episode verbatim under RELEVANT DETAIL, steps
included. And the episode is not the only carrier: an assertable
DECLARATIVE edge's `note` is rendered verbatim into the grounded block
(`graph.py:1116`, `render_edges`), so a note carrying the steps has the
same exposure by a different door — the `note`-is-never-rendered rule
lives inside `describe_procedures` and protects neither. v1 leaves both
exactly as they are; the harness's inferred probes will keep reaching
context by these routes until either the harness routes procedural probes
through `record_procedure` (kind + basis declared) or Q6 is scoped (§10):
the shape refusal applied to free text at the render choke point, as a
floor. That procedural records are
portable ACROSS HOSTS: v1 exports them, refuses them on the DEFAULT import
(the basis in a foreign file is another host's declaration), and
round-trips them only under `restore=True` — a store's own backup restores
its procedures; a host moving procedures between stores re-records them,
attesting basis itself. The default-path refusal is deliberate and closes,
while it costs one refusal, what would be a laundering route to
recommendation once §4d's composition exists. **Precedent extended:** for
a field an import will not honour the house has two moves — CAP it
(`author_of_evidence`/`derived_from` → THIRD_PARTY on the default path) and
DROP the key (`provenance.source_type` from ≤v6 files) — and this spec
takes a third, stronger one on the default path, refusing the whole record,
because a capped or key-dropped procedural record would be a procedure
with no basis, which §4c makes `basis_unknown`: stored, never shown — the
residue that later reads as a bug. That `observed` is true when declared: the host
attests basis as it attests authorship. That the Tier 8 `inferred` number
will move: it moves only when the harness declares basis, and then measures
the describe surface, not recommendation. That declarative facts have a
basis: v1 does not say.

**Measurements cited:** Tier 8 inferred cell 0.42 [0.30, 0.55] (research,
family-level clustering, 2026-09-06; a behavioural observation on identical
input, not a provenance result).

**The restore round-trip claim is scoped WITHIN A VERSION** (research,
verified 2026-09-06): import re-serializes through the current model
(`model_validate` then `model_dump_json`), and the import commit is a raw
replace outside the three normalized write sites, so bytes are stable for
records written by the same version; cross-version drift is the export
format version's job, not this invariant's.

---

## 9. Brief for the external reviewer

- **Least sure of (round 2):** (1) whether `relation_unregistered` — a
  behaviour change for a host that shrinks its registry, on records recall
  renders today — is the right conservative default, weighed against the
  RECALL-SIDE SILENCE (pre-seal F-B): the describe surface names the
  outcome, recall does not, so the alternative — keep today's declarative
  treatment with a warning — trades a silent disappearance for a rendered
  record whose kind cannot be read; we hold that fail-closed is right and
  that the missing piece is a signal (Q7), not a different default; (2)
  whether the describe ordering (token overlap on subject/relation/object,
  the note deliberately unscored) is too weak to be useful above the cap,
  and whether a stronger relevance would have to read the note; (3)
  whether the existence-oracle rule (hidden ≡ no-match; use_only named) is
  right at the boundary where a principal is visible-but-restricted.
- **Where we may have overstated:** "no migration" — true for records, but
  a host that re-registers an existing relation as procedural changes its
  own behaviour, and we document rather than prevent that.
- **What would change our minds:** a harness contract for stage 4 that
  needs `basis` to mean something other than describe-time attribution; or
  evidence that hosts cannot declare basis at ingest time in practice (then
  the axis is unreachable and the spec is a hope).
- **Resolved at internal review (research, 2026-09-06), recorded so the
  external reviewer sees the trail:** v1 let the extractor emit the
  procedural relation (F1) and overloaded `assertable` (F2); both were
  wrong at the conclusion and are reversed in v2.
- **Reviewer-safe copy:** the Tier 8 figure and cell names are research's
  published instrument; nothing here is competitive-audit detail.

---

## 10. Open questions

| # | question | who decides | by when | class |
|---|---|---|---|---|
| Q1 | ~~Should procedural records be excluded from the UNVERIFIED block too, or rendered there in the third-party shape?~~ **RULED at internal review (research, 2026-09-06): excluded from both** — the harm from a fact rendered as a claim is a wrong belief; from a procedure, an action; Tier 8 competitor arms handed procedural context back as guidance at 0.25–0.90. §4a carries the sentence. | research | ruled | closed |
| Q2 | The confirm-as-promotion composition (`observed` → recommendable after `confirm_edge`): specified in the stage-4 spec when a harness contract exists, or never? Note it turns a ranking input into a gate; procedural-only scope means no existing confirmation sits on a procedural record. | Quentin | when a harness contract exists | deferred |
| Q3 | ~~The imperative-shape check: who freezes the derivation, and is a paraphrase attack in scope for v1?~~ **RESOLVED (round-1 F4; research, 2026-09-06):** research OWNS the recognition corpus and freezes it against THIS version before any implementation line, under the 0029 condition; artifact `tests/eval/procedural_describe/MANIFEST.json` with version and digest in `## Review closure`; derivation at test time from the frozen texts; ± sets frozen (homographs by name); change control by amendment with a superseding digest; the v1 paraphrase boundary is a STATED LIMIT asserted as a known pass, not a guarantee (§6a). | research (expectations) · dev (runner) | freeze after v8 lands | closed |
| Q4 | Declarative basis (a stated non-goal of v1): if ever, which of §4c's three absence options — and is (2) fail-closed with host re-attestation acceptable as a product call? | Quentin | not in v1 | deferred |
| Q5 | ~~Should `describe_procedures` be exposed through MCP in v1?~~ **RESOLVED by round-1 F1's fold:** v1 exposes BOTH MCP tools — `record_procedure` (the only MCP procedural write path, capability-gated to `direct`) and `describe_procedures` — because a write surface without its read surface is half a stage; both are additive. | dev (author), reviewer-directed | folded in v8 | closed |
| Q7 | A cheap recall-side signal for `relation_unregistered` (pre-seal F-B): a counter on the recall result, or a diagnostic naming the excluded records' relation, so a host that shrinks its registry does not discover the exclusion as missing data. Round-2 question: which carrier, and does it belong in this spec or in the recall result's own contract? | reviewer → dev | round 2 | open |
| Q6 | **SCOPED — option (b) (Quentin, 2026-09-06: "Scope Q6 as option b"), then COMMISSIONED the same day ("Leave it documented and I commission the spec"); the canonical governance state (round-1 correction; research, after design-round 10): THE COMMISSION STANDS and is formally PARKED behind a mechanism-selection prerequisite — research measured the mechanism the recorded scope had named and withdrew it (108/342 caught; a 2.7% floor of real declarative sentences withheld after its obvious defect), so the work is research's mechanism selection first, and it takes no spec number until a candidate passes pre-defined acceptance criteria. 0037 is unchanged by it; §8's residual disclosure stays exactly as written.** Original scoping record: The sibling's scope, recorded so it does not become a decision living in a conversation: free text at the render choke point V-RENDER-SITES enumerates, ALL record types (both carriers verified: the assertable episode `summary`, `gate.py:137`; the assertable declarative edge `note`, `graph.py:1116`); REUSES this spec's corpus-derived imperative-shape check, no new host field (covers a carrier nobody has found yet; completeness checkable by the existing sweep); claimed as a FLOOR (a paraphrase defeats it, more easily than in `describe_procedures`); and REQUIRES A MEASUREMENT FIRST — how much currently-returned declarative content the check would withhold — before committing to the change. Original question kept for the record: must v1 ALSO reduce the exposure of FREE TEXT rendered verbatim into model context — the assertable episode `summary` (probed, §8) AND the assertable declarative edge `note` (`graph.py:1116`), at least — which carry executable steps today regardless of record type? Research's semantics (2026-09-06): episodes are interaction history, NOT procedures — no procedural episode type, and never delete history to hide text; the exposure is at the RENDER, so the fix that covers both carriers and any third is the imperative-shape refusal applied to free text at the render choke point V-RENDER-SITES already enumerates, for any record type, claimed as a FLOOR (a paraphrase defeats it; the text was never authored as a procedure), with no new host-declared field. Scope options for Quentin: (a) in v1, at the choke point, as a floor; (b) a sibling spec; (c) not now — in which case the inferred cell moves only by the harness routing procedural probes through `record_procedure`, and the trusted-path figures (0.42 inference-framing; 0.667 controls) stand as measured. | Quentin (scoped 2026-09-06) | sibling spec, when commissioned | scoped elsewhere |
