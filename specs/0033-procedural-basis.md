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
| **Version** | **v6** — Q6 RESHAPED on research's semantics (2026-09-06, before the commit): an episode is not a procedure but the record that one was mentioned (`Episode`'s own contract), so v1's answer stands — no procedural episode type; refusing or deleting the episode would destroy true history to hide text. But the exposure is not where Q6 put it: it is FREE TEXT RENDERED VERBATIM INTO MODEL CONTEXT, and there are at least two carriers — an assertable episode's `summary` (`gate.py:137`, the probe) and an assertable declarative edge's `note` (`graph.py:1116`, straight into `render_edges` and the grounded block) — so an episode-side kind would close one door and leave the sibling open, F2's partial-fix shape. Research's recommendation, carried into Q6 for Quentin: apply the imperative-shape refusal to free text AT THE RENDER CHOKE POINT V-RENDER-SITES already enumerates, for any record type — no new host field, completeness checkable by the existing sweep, claimed as a FLOOR (reduces, never closes: the text was never authored as a procedure). The trusted path this sits on is already measured (research: `user_attested_inference_framing` 0.42 [0.30, 0.55]; `controls` 0.667), so Quentin scopes it with the shape on the table. *Prior:* **v5** — the §6/§6a internal-review fold (research, 2026-09-06). **F4 (BLOCKING)** — EPISODES were not mentioned once: they reach model context on their own path (`gate.py:106` `partition_parts` returns `ep_lines` and `tp_ep_lines`), ordinary ingest writes one beside the edges, and an episode has NO relation — so "excluded by kind" could not see it (F2 through a door the kind check cannot see). PROBED, not argued: procedural text through ordinary `remember` with a scripted extractor produced ZERO edges and ONE episode, and recall's context carried the executable steps verbatim (§8, the measured residual). v5 settles all three cases: `record_procedure` writes NO episode (V-NO-EPISODE); ordinary ingest's episode path is TODAY's behaviour, unchanged, stated as the residual with the probe; whether v1 must ALSO govern procedural text arriving through ordinary ingest — which needs a host-declared EPISODE kind, a larger change — is §10 Q6, blocking, for Quentin. The edge-side concept is renamed `relation_kind` because `Episode.kind` already exists (`interaction | outcome`). **F5** — the `stated`/`observed` ORDER was never declared while two invariants leaned on "whole-set minimum": declared now beside the field — the lattice is `observed ≤ stated`, `observed` is the minimum, so absorption can only ever yield `observed` from a mixed set (the only order consistent with V-BASIS-CAP-ONLY). **V-CARRIERS** made derivable: the sweep basis is every `Provenance(` constructor and `model_copy(update=` site (both forms — 0016's tenth-site lesson) and every `provenance.` reader, never the hand list v4 carried. *Prior:* **v4** — research's correction of its OWN F3 recommendation (2026-09-06, before the first commit): "refuse on both paths" was too broad. `portability.py:21-30` defines `restore=True` as the operator's explicit assertion that the file is THIS store's own history — precisely the attestation `basis` requires — so refusing there costs backup fidelity for no trust gain and loses every procedural record of a store's own backup, silently to anyone not reading the refusal count. v4: the DEFAULT path refuses (the relay reading holds exactly); `restore=True` ACCEPTS the record with its declared basis; the invariant becomes V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE with the restore leg as a POSITIVE case (a refusal-only test would pass while backup/restore was broken). §8 names the precedent extended: the house has two moves for a field an import will not honour — CAP it (author/derived_from → THIRD_PARTY) and DROP the key (`source_type`, ≤v6 files); refusing the whole record is a third, stronger move, taken on the default path only. *Prior:* **v3** — the second internal-review fold (research, 2026-09-06, before the first commit): **F3** — `record_procedure` was NOT the sole producer at the store layer: `commit_outcome_import_plan` writes edges directly (one of the seven sites in 0029's own `EDGE_WRITE_SITE_RULINGS`, checked against the registry rather than the API surface), so an import could introduce a procedural record carrying a basis DECLARED BY A DIFFERENT HOST — 0026's relay shape, and a collision with §4b's "basis is a positive capability THIS host declares"; harmless while both bases are merely describable, a laundering route to recommendation the moment §4d's composition exists. v3 takes the first of three ways out: **import REFUSES procedural records** with a named outcome (`procedural_import_refused`), §8 states the limitation, and V-ONE-PRODUCER becomes true rather than reworded. V-ONE-PRODUCER's sweep basis is now 0029's registry × the raw-SQL sweep, never a fresh inventory (a second list of edge writers is the hand-list 0029 already paid for). *Prior:* **v2** — the §3a internal-review fold (research, 2026-09-06; two BLOCKING findings at the conclusion, both verified in code, both taken; Q1 ruled). **F1** — the extractor DECIDES KIND TRANSITIVELY by choosing the relation (`ingest.py:169` passes the registry's names into the extraction prompt), and with basis REQUIRED that made every extractor-emitted procedural edge a silent refusal fleet-wide through the DEFAULT registry — the declarative fail-closed hazard arriving by another door. v2: procedural relations are FILTERED OUT of the extractor's vocabulary at the extraction boundary, so the extractor can never emit one; procedural capture is an EXPLICIT host surface that carries basis (`Memory.record_procedure`). Kind is host-declared end to end, not only in principle. **F2** — `assertable=False` is a ROUTING signal today, not suppression (`gate.py:139`: not-assertable renders as a fenced third-party claim, Q5), so overloading it with "is procedural" would render a procedure as a fenced claim at every site v1 missed — the Tier 8 failure mode. v2: `Edge.assertable` is UNTOUCHED and type-correct; procedural records are excluded ONCE, BY RELATION KIND, at the recall/partition choke point, with a named outcome, and a V-TOTAL-style sweep derives every model-context render site and proves each reaches that choke point. **Q1 ruled (research, from the Tier 8 competitor arms, 0.25–0.90 guidance rates for procedural content that reached the answerer's context):** procedures are excluded from the UNVERIFIED block too, and §4a carries the sentence that keeps a later reader from "fixing" it by symmetry with Q5. **§8** now claims `executable_detail` as a FLOOR, not a guarantee: a paraphrase defeats it. *Prior:* **v1** — the candidate, 2026-09-06. |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research (requested 2026-09-06) · dev (author; may not self-approve) · workflow-platform unavailable (no such session exists this arc; recorded as the waiver, holder Quentin) |
| **External review** | required (full spec) — not yet sent; internal first |
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
| `Memory.record_procedure(user_id, summary, *, basis, context, note=None, relation="follows_procedure")` — NEW | the ONLY producer of procedural records (F1, F3); constructs the edge directly, never through the extractor, and the import commit refuses them | — | new | n/a — additive; neither the extractor path nor the import path can produce a procedural record |
| `portability.import_memory` / `commit_outcome_import_plan` (an edge writer in 0029's `EDGE_WRITE_SITE_RULINGS`) | DEFAULT path REFUSES procedural records (named outcome; declarative records unchanged); `restore=True` ACCEPTS them with their declared basis (F3, corrected v4) | 0005: "an importing store's knowledge of an edge begins at ITS import"; the default path caps trust; `restore` is the operator vouching that the file is this store's own history | export/import round-trip tests, the 0005 boundary registry | YES — on the default path an imported basis is another host's declaration; under `restore` it is this host's own, re-asserted by the operator |
| `Memory.describe_procedures(user_id, ...)` — NEW | the stage-3 surface | — | new | n/a — additive |

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
| the extractor's relation choice | drops out-of-vocabulary relations as `invalid` (unchanged) | — | the extractor filing a procedure under a DECLARATIVE relation (today's behaviour, unchanged: the text is treated as whatever it was filed under — stated in §8 as the residual) | the extractor emitting `follows_procedure` (from a prompt-injected name, or a model that has seen the docs) to reach the describe surface | the extractor NEVER SEES a procedural relation (its `rel_names` are filtered by relation kind at the extraction boundary) and an emitted procedural relation is dropped as `invalid` like any out-of-vocabulary name — **V-EXTRACTOR-BLIND** (`test_extractor_vocabulary_carries_no_procedural_relation`); kind is a property of the REGISTRY and total over the vocabulary — **V-KIND-REGISTRY** |
| the procedure's description text (rendered by `describe_procedures`) | — | — | — | text crafted to read as instructions ("step 1: run …") — the render REFUSES executable detail (§4a-ii): the description is the record's gloss-level summary with its basis and provenance, never the steps | **V-NO-IMPLICIT-RECOMMEND** (`test_describe_never_reproduces_executable_detail`) |
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
| `describe_procedures` | describable iff active ∧ valid_now ∧ ¬quarantined ∧ ¬use_only ∧ basis ∈ {stated, observed}; the render carries basis and provenance and refuses executable detail | never (use_only) | describable | never (use_only) | never | never |

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
hidden from a principal is not described to them (the visibility gate is
outermost, as in 0030 V-SCOPE); a cross-scope-visible procedural record is
described in the third-party shape. No principal can see anything they could
not see before: procedural records are a NEW class that recall never
rendered, and `describe_procedures` shows less than recall would have.

---

## 4. Behaviour

### 4a. What makes a record procedural — the registry, never the text

An EDGE is procedural iff its relation is registered with
`relation_kind="procedural"`. Relation kind is a property of the RELATION
REGISTRY (named `relation_kind` deliberately: `Episode.kind` already exists
and means `interaction | outcome`, nothing to do with this axis — F4's
adjacent-name collision), declared by
the host (the default registry ships one procedural relation,
`follows_procedure`), and is therefore TOTAL over the vocabulary: every
stored record has exactly one kind, and there is no "unclassified or mixed"
record for the round's conservative ambiguous-type rule to bite on — that
rule is satisfied by construction, and stated so rather than left to be
rediscovered.

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

**4a-ii. The describe predicate.** `Memory.describe_procedures(user_id, *,
query=None, principal=None) -> list[ProcedureDescription]` returns, for
each procedural record that is visible to the principal and satisfies
`active ∧ valid_now ∧ ¬quarantined ∧ ¬use_only ∧ basis ∈ {stated, observed}`,
a description consisting of: the relation's gloss, the record's object
(the procedure's NAME/summary as stored), its basis rendered as
attribution — `stated`: "you said you follow …"; `observed`: "a pattern you
reported observing: …" — its provenance (author, observed_at), and its
disclosure. **The description never reproduces executable detail:** the
render emits the summary field only, never the `note` (where step-level
detail lives if the extractor captured it), and refuses (returns the record
as `not_describable: executable_detail`) when the summary itself matches the
imperative-step shape (§6 V-NO-IMPLICIT-RECOMMEND names the check; the
shape is DERIVED from the corpus's procedure texts at test time, not a hand
list — the derivable-set rule). A description that reproduces a procedure
in executable detail IS a recommendation whatever its framing (round 5).
**The refusal is a FLOOR, not a guarantee** (§8): a paraphrase in
non-imperative mood ("you could disable the audit log first") carries the
same executable content and passes the shape check. The structural
defences are the ones that hold — the `note` is never rendered, and the
summary is the host's own gloss-level text.

Every non-describable outcome is NAMED: `not_procedural`, `hidden`,
`inactive`, `not_yet_valid`, `quarantined`, `use_only`, `basis_unknown`,
`executable_detail`. There is no default allow and no untyped refusal.

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
outcome into a refusal: the extractor's vocabulary is unchanged. Through MCP, `remember` gains a
`basis` argument that is honoured only under `capability=direct` (the host
attests; 0031's rule) and refused otherwise with the same named outcome as
an attempted elevation.

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

- Library: `Relation(kind=...)`, `EvidenceContext.direct(basis=)` /
  `derived(X, basis=)`, `Provenance.basis`, `Memory.describe_procedures`,
  `ProcedureDescription`.
- MCP: `remember(..., basis: Optional[str] = None)` — honoured under
  `direct` only; a new `describe_procedures` tool.
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
  procedural records on both paths.
- Migration: NONE. The relation registry is code, not schema; `basis` is a
  JSON field inside the existing payload. The pre-feature oracle replays
  byte-identically (V-DECLARATIVE-UNCHANGED).
- Unrecoverable: nothing; the change is additive and reversible (§7).

---

## 5. Regime analysis — where does this behave differently?

- **Scale:** the describe surface is a filtered read over the user's
  procedural records; it shares recall's caps (`max_subgraph_edges`) and is
  tested at the truncation regime (a store with more procedural records than
  the cap must describe by relevance, not store order — the 0.x regime
  defect's shape).
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
| **V-DESCRIBE-CONJUNCTION** `describe_procedures` returns a description iff every conjunct holds, and otherwise a NAMED outcome from the closed set; the set is enumerated exhaustively (a 0013-style oracle over the cell product) | `test_describe_outcomes_are_named_and_total` | CI |
| **V-NO-IMPLICIT-RECOMMEND** a description never reproduces executable detail: the `note` is never rendered; a summary matching the imperative-step shape yields `executable_detail`; the shape is DERIVED from the corpus's procedure texts at test time, with must-match AND must-not-match cases | `test_describe_never_reproduces_executable_detail` | CI |
| **V-SCOPE-OUTERMOST** a hidden procedural record yields `hidden` only — never its basis, never `executable_detail` | `test_hidden_procedure_yields_hidden_only` | CI |
| **V-HOST-DECLARED** through MCP, `basis` is honoured under `capability=direct` only; under `none` it is the same named outcome as an attempted elevation, counted like one | `test_mcp_basis_is_host_attested` | CI |
| **V-NO-EPISODE** (F4) `record_procedure` writes NO episode: the user's episode count is unchanged by a procedural write, and no episode text contains the procedure's summary or note; control: ordinary `remember` of the same text writes one | `test_record_procedure_writes_no_episode` | CI |
| **V-CARRIERS** every carrier of `basis` accounts for it in one commit — the sweep basis is DERIVED: every `Provenance(` constructor site and every `model_copy(update=` site (both forms, 0016's tenth-site lesson) plus every `provenance.` reader in src, each classified as carrying, passing through, or not applicable; a site absent from the classification fails | `test_basis_reaches_every_carrier` | CI |

Standing checks that must not regress: injection asserts 0 · cross-user leaks
0 · trust canaries 0 · the 0029 corpus 19/19 · the 0030 module 29/29.

### 6a. Acceptance measurement — REQUIRED, FINITE

A correctness gate over a frozen scripted corpus (research freezes the
expectations from this spec's text; dev owns the runner — the 0029 pattern):
every cell of author × disclosure × basis × {active, inactive, future,
hidden, visible} × {stated summary, imperative summary} with its expected
named outcome from `describe_procedures` and its expected ABSENCE from
recall's blocks. Pass = 100%.

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
they are describable through a dedicated surface that names their basis and
never reproduces executable detail. Recommendation of procedures is not
provided — it awaits a harness contract."

**What this does NOT establish.** That a described procedure is not acted
on: a host that reads a description into an action has made that choice
(the shipped disclosure). That `executable_detail` catches every actionable
description: it is a FLOOR — a paraphrase in non-imperative mood defeats the
shape check; the structural defences (the `note` never rendered; the summary
the host's gloss-level text) are what hold. That procedural text the
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

- **Least sure of:** (1) whether "kind is a property of the registry" is
  the right place for procedural-ness — it is the only place that is not
  the model deciding, but it puts the classification burden on the host's
  extractor prompt (the gloss); (2) whether the imperative-shape refusal
  can be made a derived, testable check rather than a hand list, and
  whether it can fail open on a paraphrased procedure; (3) whether
  excluding procedural records from BOTH gate blocks is the right reading
  of "recommend unavailable by default", or whether the UNVERIFIED block
  (which already says "never assert these as fact") should carry them.
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
| Q3 | The imperative-shape check: derived from research's corpus at test time (the derivable-set rule) — who freezes the derivation, and is a paraphrase attack in scope for v1? | research | before acceptance | blocking |
| Q4 | Declarative basis (a stated non-goal of v1): if ever, which of §4c's three absence options — and is (2) fail-closed with host re-attestation acceptable as a product call? | Quentin | not in v1 | deferred |
| Q5 | Should `describe_procedures` be exposed through MCP in v1, or library-only until a host asks? | workflow-platform (unavailable) → Quentin | pre-release | pre-release |
| Q6 | Must v1 ALSO reduce the exposure of FREE TEXT rendered verbatim into model context — the assertable episode `summary` (probed, §8) AND the assertable declarative edge `note` (`graph.py:1116`), at least — which carry executable steps today regardless of record type? Research's semantics (2026-09-06): episodes are interaction history, NOT procedures — no procedural episode type, and never delete history to hide text; the exposure is at the RENDER, so the fix that covers both carriers and any third is the imperative-shape refusal applied to free text at the render choke point V-RENDER-SITES already enumerates, for any record type, claimed as a FLOOR (a paraphrase defeats it; the text was never authored as a procedure), with no new host-declared field. Scope options for Quentin: (a) in v1, at the choke point, as a floor; (b) a sibling spec; (c) not now — in which case the inferred cell moves only by the harness routing procedural probes through `record_procedure`, and the trusted-path figures (0.42 inference-framing; 0.667 controls) stand as measured. | Quentin (scope), research's semantics given | before acceptance | blocking |
