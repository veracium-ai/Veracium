# Feature spec: relation arity — a functional relation is ONE SLOT PER SUBJECT, and three of ours should not be

Spec-Status: draft

| | |
|---|---|
| **Author / session** | research (veracium-research-48), the candidate's author → dev (veracium-2b), adopted at rest and re-read from the file: v1.1 2026-09-20 from `0044-relation-arity-CANDIDATE.md` (sha16 3f9f9db8ea92cc0a); v1.2 2026-10-10 from `0044-relation-arity-CANDIDATE.md` (sha16 72cd614748837a31); v1.3 2026-10-11 from `0044-relation-arity-CANDIDATE.md` (sha16 3741b0c83f8bde59) |
| **Version** | **v1.3 — 2026-10-11: round 1 returned for amendment (R1-01..R1-10); this version is STAGE 1, the accumulation stage, on the owner's ruling (A), “defer keys”** (2026-10-11, first-hand in the dev session, relayed by dev). `single` and `multi` are operational; `keyed` is a reserved word that a registry may not yet declare; `measures`, `prefers` and `health_state` become `multi`; operational keys are a later round, carrying the reviewer's warning that a deterministic rule over a model-chosen object is not a trusted key source. **The restoration of values already retired is rebuilt** to answer R1-01 (standing revocation), R1-03 (completion, restart and receipt — through a companion AMENDMENT TO 0018, a separate host operation), R1-04 (truthful successor evidence), R1-05 (durable operation identity, not “the latest event”), and R1-06 (a persisted plan from the host's effective registry). **The owner made the restoration OPTIONAL, with a warning** (2026-10-11): §4h states the cost. **The authors' P-1..P-8** (the round's addendum, credited by the reviewer as author-disclosed) are folded where each belongs. **Q6 is answered: KEEP the successor's pointer** (the reviewer's recommendation, conditional on R1-04/R1-05, both now met). Every rule in §4 was model-checked before this text: dev's reference model (pure Python, `specs/evidence/0044/` when landed) — 12 invariants hold on research's rule set, 16 mechanism mutants each killed by the invariant that names it. Prior: v1.2 · v1.1 · v1. |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line at the top* |
| **Internal reviewers** | research (author) · dev |
| **External review** | **required** — round 2. Round 1: `0044-round1-review-package` (sha256 262e8037…), RETURN FOR AMENDMENT, ten findings. |
| **Decision + date** | (A) defer keys: the owner, 2026-10-11. Restoration of the superset with a receipt: the owner, 2026-10-10. Restoration optional with a warning: the owner, 2026-10-11. Acceptance: pending round 2. |
| **Path** | **full** |
| **Number** | 0044 — from `allocation.py --next` at adoption, 2026-09-20. |
| **Predecessor** | none. Occasioned by `TRACK-B-RENDER-PATH-RESULT.md` §5–6 (fix **B**, *“stop treating multi-valued attributes as functional”*, recorded there as *“the real modelling question and the owner's”*). **Travels with** the 0003 contested-order amendment in one review package (the owner's grouping, 2026-09-19: the two share the contested-render surface a reviewer needs whole) |
| **Requires** *(version-bound; the machine-checked form is dev's gate, R1-10)* | the 0018 amendment (a per-user data-migration operation); a 0029 amendment (a closed reason for `reinstated`, §4j). The 0003 amendment requires THIS version. |

---

## 1. Problem and motivation

### 1a. The defect, reproduced — with a control that separates

**The supersession scope is `(user, subject, relation)`** (`graph._build_supersession_plan`'s scope read), and for a
relation flagged `functional` **any differing object retires the prior**. So `functional` means **one slot per
subject**, not one slot per quantity, per topic or per condition.

Driving the supersession path the ingest path applies (`graph.apply_supersession`) with two differing values under
one `(subject, relation)`, then reading the active set (§2c-ii row 1):

| relation | `functional` | active after the second value |
|---|---|---|
| **`prefers`** | `True` | only the second — *“oat milk”* retired by *“window seats”* |
| **`health_state`** | `True` | only the second — *“asthma”* retired by *“iron deficiency”* |
| **`measures`** | `True` | only the second — *“weight 78 kg”* retired by *“savings 4200”* |
| 🔴 **`uses_tool`** *(the control)* | **`False`** | **both** |

🔴 **`measures`' own gloss names three different quantities — “weight, reading progress, savings balance” — and then
files them in ONE slot.**

**“Retired” means:** the prior row is KEPT — `invalidated_at` set, `invalidation_reason = 'superseded'` — and leaves
every active read. *The agent stops “knowing” a person's asthma the moment a second condition is mentioned, and nothing
tells anyone.*

> **Method note.** A probe through the raw `Store.add_edge` writer shows both rows ACTIVE — the raw writer applies no
> supersession. The table above drives the supersession path itself.

**A figure removed rather than caveated (v1.1, A7):** v1 carried a share figure from a store that no longer exists;
it is not restated. The owner's 2026-10-10 answer that store statistics may travel does not make it re-derivable.

### 1b. What the boolean carries, and why stage 1 accepts accumulation

`functional` answers two questions with one bit: *does a new value REPLACE an old one?* and *what is the slot?* For
`prefers`, `measures`, `health_state` the slot is the topic, the quantity, the condition — not the subject.

**v1.1 and v1.2 called “flip the flag to non-functional” the narrow dodge** and proposed `keyed` arity. Round 1 found
that `keyed` had no key carrier and that slot identity stopped at the supersession branch (R1-02); the reviewer judged
that *“a clearly described accumulation stage is defensible”* rather than *“preserv[ing] known cross-quantity
retirement simply to keep some update behavior.”* **The owner chose (A): this version ships the accumulation stage,
and keys are a later round.** The cost is stated where it lands (§4c): no latest-value semantics for `measures`.

### 1c. Alternatives rejected

- **Keep the three relations `single`** — retains the reproduced defect (§1a) to keep update behaviour; the reviewer
  and the owner rejected it.
- **Specify the key carrier now** ((B)) — the owner chose (A); no host supplies keys today.
- **Split `measures` into per-quantity relations** — workable for a small closed set; does not solve open-ended
  preferences or conditions. Remains a stage-2 alternative.
- **Leave already-retired values retired** — not chosen: the owner chose restoration with a receipt (2026-10-10).
- **Reinstate silently** — rejected: it changes what the agent says about a person with no record of why.
- **Clear the successor's `supersedes` pointer at restoration** — rejected (Q6, the reviewer's recommendation): for
  every correctly replaced pair the pointer is a true record of a storage transition.
- **Select restorable rows by relation name** — rejected (R1-06): a host's custom `single` declaration of the same name
  would be restored against its intent; §4e's plan replaces it.

---

## 2. Field contracts touched

**Consumers enumerated FROM THE SITES, not only by a grep for `functional`** (round 1: a grep finds readers, never a
consumer that forgot the field). The `functional` textual census (§2c-ii row 6, nine lines) is the compatibility
census; the slot census adds the sites that group or combine by `(subject, relation)` without reading the flag.

| field / site | read / written | contract | stage-1 change |
|---|---|---|---|
| `Relation.arity` *(new)* | read by every consumer below | `single` · `multi` (operational) · `keyed` (reserved) | new; **a registry declaring `keyed` is REFUSED at validation** |
| `Relation.functional` (`schema.py`) | compatibility | *“one current value per subject”* | **derived** (`single ⇒ True`); a registry declaring both and disagreeing is refused |
| `registry.FrozenRel` construction (`registry.py` L74 host relations, L78 reserved relations) | snapshot | carries `functional` | **both sites carry `arity`** |
| supersession planner (`graph.py` L548) | reads | a differing value under a functional relation retires the prior | unchanged for `single`; `multi` never supersedes (as today) |
| reinforcement and absorption (`graph.py` L436–L460, before the functional branch) | write | same-or-subsuming values reinforce or absorb within `(user, subject, relation)` | **unchanged** — as for every `multi` relation today (§4b, INV-A2 narrowed) |
| contention ordering (`graph.py` L658), recall contested groups (`__init__.py` L1413), wiki compile's refusal exclusion (`compile.py` L116) | read | group or exclude refusal pairs of a functional relation | **`multi` forms no new groups; refusals recorded while the relation was `single` KEEP their protection (§4d)** |
| recall variants tier (`__init__.py` L1507) | reads | groups by `(subject, relation)` | unchanged under stage 1 (no keys); **stage 2 must group by slot** (P-2) |
| wiki value groups (`compile.py`, the `_value_groups` construction) | reads | one survivor per incomparable value | unchanged; the render consequence is §4c |
| `compile._policy_digest` (`compile.py` L79–80) | reads | binds the functional names | binds arity; **one recompilation per affected cached user view, generally on a later read** (not once per store) |
| `Edge.invalidated_at`, `invalidation_reason` | written by restoration and undo (§4f, §4i) | `superseded` = retired by a later value in the slot | cleared on restoration; restored per field on undo |
| journal `reinstated` event (`_journal_edge_write`) | written | reason non-NULL iff `invalidated`/`redacted` (0029) | **0029 amendment (§4j):** `reinstated` gains a closed reason |
| `doctor`'s `refs` rule (`doctor.py` L294–L310) | reads | an active predecessor of an active successor warns (exit 1) | **downgraded to `info` for a restoration recorded in `migration_outcome`** (§4k) |
| `migration_run`, `migration_outcome`, `reclassification_plan` *(new tables)* | written by the 0018 amendment's operation | — | §4e–§4i |
| portability (`portability.py`) | export / import | reproduces superseded history exactly | **exports `migration_outcome` rows for exported edges; import-time conversion for pre-arity files** (§4l) |

**Documentation that states the old meaning and changes with it:** the `functional` comment in `schema.py` (L457),
`graph.py`'s module docstring, and `_policy_digest`'s docstring.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant** |
|---|---|---|---|---|---|
| **extractor output** — relation and object from `remember`'s text | no edge | the extractor's refusal | unclassified route | a model-chosen object cannot retire a stored value under a `multi` relation; under `single`, 0003's authority gate is unchanged | **INV-A1**, **INV-A2** |
| **host registry** (`arity`, `functional`) | absent `arity` → derived from `functional` | an `arity` outside the set → refused | **`keyed` → refused** | `functional=True` with `arity=multi` → refused | **INV-A4**, **INV-A10** |
| **the registry passed to the restoration** (0018 amendment) | refused | refused by 0025's validator | — | a later call with different declarations for the three relations → `registry-changed`, nothing changed | **INV-A15** |
| **data written by an older version** — rows retired as `superseded` | the plan selects none | an unparseable row aborts that user's transaction | a redacted row (its `relation` is the marker) is never considered | **a row whose source is under standing revocation is never restored** | **INV-A7**, **INV-A11** |
| **an import file** | — | the existing import refusals | — | a pre-arity file's retired rows are converted; an id already held locally is SKIPPED; a newer file's unexplained retirement is never reinstated by guess; default-import testimony gives no `doctor` exemption | **INV-A16** |
| **the undo request** (`edge_id`, `correlation_id`) | refused | refused | an edge the restoration did not restore → refused | the same id for a different edge or verb → refused (0008's rule) | **INV-A12**, **INV-A13** |
| CLI / environment / network | n/a | | | | |

### 2c-ii. Assertions about reach — REQUIRED

Commands run from the repository root at `1054cc4`, with a Python carrying the package's dependencies (research,
CPython 3.14.7, 2026-10-11). The three probe scripts are research's, to be landed beside dev's model under
`specs/evidence/0044/probes/`. **EXECUTED** = run and read; **READ** = the cited lines.

| # | assertion | command | result |
|---|---|---|---|
| 1 | a second value under `prefers` / `health_state` / `measures` retires the first; `uses_tool` keeps both | `PYTHONPATH=src python -c "from veracium.graph import apply_supersession as ap; from veracium.schema import DEFAULT_RELATIONS as R, Edge, Provenance, EvidenceAuthor as A, Disclosure as D; from veracium.store.sqlite import SqliteStore as S; E=lambda i,r,o: Edge(id=i,user_id=\"u\",subject=\"user\",relation=r,object=o,provenance=Provenance(author_of_evidence=A.USER,evidence_ref=\"ev\",disclosure=D.MENTIONABLE)); run=lambda r,a,b:(s:=S(\":memory:\"),s.add_edge(E(\"p\",r,a)),ap(s,E(\"i\",r,b),R),s.add_edge(E(\"i\",r,b)),sorted(x.object for x in s.edges(\"u\")))[-1]; [print(r, run(r,a,b)) for r,a,b in ((\"prefers\",\"oat milk\",\"window seats\"),(\"health_state\",\"asthma\",\"iron deficiency\"),(\"measures\",\"weight 78 kg\",\"savings 4200\"),(\"uses_tool\",\"Notion\",\"Figma\"))]"` | EXECUTED: `prefers ['window seats']` · `health_state ['iron deficiency']` · `measures ['savings 4200']` · `uses_tool ['Figma', 'Notion']` |
| 2 | `Relation` has no key field and `remember` takes none | `PYTHONPATH=src python -c "import inspect; from veracium.schema import Relation; from veracium import Memory; print(list(Relation.model_fields)); print(list(inspect.signature(Memory.remember).parameters))"` | EXECUTED: `['name', 'functional', 'desc', 'relation_kind']` · no key parameter |
| 3 | revoking a source leaves an ALREADY-retired row's reason `superseded` (R1-01) | `PYTHONPATH=src python specs/evidence/0044/probes/revocation_keeps_superseded.py` | EXECUTED: `after revoking feed-A, the retired prior's reason: superseded` |
| 4 | a non-functional `measures` still absorbs `80` into `weight 80` (R1-02) | `PYTHONPATH=src python specs/evidence/0044/probes/multi_still_absorbs.py` | EXECUTED: `{'80': 'absorbed_duplicate', 'weight 80': None}` |
| 5 | reinstatement widens the past valid-time window (P-6) | `PYTHONPATH=src python specs/evidence/0044/probes/asof_past_window.py` | EXECUTED: control — the retired window shows only `window seats`; reinstated — the same window shows both |
| 6 | nine lines in `src/` read `.functional` | `grep -rn --include="*.py" -e "\.functional\b" src/` | READ: 9 lines; `registry.py` L74 and L78 are the two `FrozenRel` construction sites |
| 7 | `supersedes` is a single field (R1-04) | `PYTHONPATH=src python -c "from veracium.schema import Edge; print(Edge.model_fields['supersedes'].annotation)"` | EXECUTED: `str` or `None` |
| 8 | the journal is not exported (P-5) | `grep -ci -e edge_events -e journal src/veracium/portability.py` | EXECUTED: `0` |
| 9 | `doctor` exits 1 on a warning | `grep -n "return 1 if any(f.level in (\"error\", \"warn\")" src/veracium/doctor.py` | READ: L142 |
| 10 | the variants tier groups by subject and relation (P-2) | `grep -n "g = (e.subject, e.relation)" src/veracium/__init__.py` | READ: L1507 |

---

## 3. Trust-class matrix — REQUIRED, blocking

Classes from the enums at `1054cc4`: `EvidenceAuthor` = user, third_party, system, assistant; `Disclosure` =
mentionable, use_only, quarantined.

### 3a. Supersession — directional, stage 1

**Stage 1 changes which relations supersede, never the authority rule.** For a `single` relation every cell is 0003's
matrix, unchanged. For a `multi` relation:

| | prior=A, incoming=B | prior=B, incoming=A | same class | involving quarantined | involving `use_only` |
|---|---|---|---|---|---|
| **differing value** | no candidate — both stand | no candidate | no candidate | no candidate | no candidate |
| **same-or-subsuming value** | reinforcement / absorption as today (0012, 0014) | as today | as today | as today | as today |

### 3b-i. The restoration — a state transition over a planned set

| row's author | mentionable | use_only | quarantined |
|---|---|---|---|
| any, source NOT under standing revocation | restored; provenance, disclosure, confidence unchanged | same | **restored and still quarantined** |
| any, source under standing revocation (direct or contribution-derived) | **withheld (`withheld_revoked`)** | same | same |
| any, redacted | **never considered** (its `relation` is the marker) | same | same |

- *User-asserted fact made non-assertable?* No — supersession can only retire LESS; restoration only reinstates.
- *Non-user content gains user-grade authority?* No — each row keeps its own stamp.
- 🔴 *A correctly replaced value made current again?* **Yes, by the owner's decision** — the receipt names it; §4i
  re-retires it.
- *`needs_confirmation`, provenance merge?* Untouched.

## 3b. Authorization and scope — *full specs only*

- No user, tenant or scope boundary is crossed; every operation acts on one user's rows.
- **The restoration** is the 0018 amendment's host operation: a store path, 0018's quiescence attestation (for its
  backup reference — the only whole-store undo for a superset restoration), and the host's registry. Not MCP.
- **The undo verb** is host-only, per row. Not MCP (as `dispute()` is not).
- **The receipt read** returns one user's outcomes.
- **Nothing becomes visible to a principal who could not see it before:** a restored row returns to the same user's
  surfaces, under its own disclosure.

---

## 4. Behaviour

### 4a. Arity in stage 1

| arity | stage-1 status |
|---|---|
| `single` | one value per `(user, subject, relation)`; a differing value supersedes, under 0003's authority gate |
| `multi` | a differing value never supersedes |
| `keyed` | **reserved word; a registry declaring it is refused.** Defined by a later round |

`functional=True ≡ single`, `functional=False ≡ multi`: every host registry valid today keeps its meaning.

### 4b. The reclassification, and what `multi` does and does not do

`measures`, `prefers`, `health_state` → `multi`. Every other default unchanged (`works_as`, `located_at`, `deadline`,
`scope` stay `single`).

**A differing value never supersedes. Reinforcement and absorption are unchanged** (R1-02, INV-A2 narrowed): a
same-or-subsuming value reinforces or absorbs within the `(user, subject, relation)` scope, exactly as for every
`multi` relation today (`80` then `weight 80` → `absorbed_duplicate`, §2c-ii row 4). *Absorption requires one value
key to subsume the other, so unrelated quantities (`weight 78 kg`, `savings 4200`) never merge. Residual, stated: a bare
less-specific reading can be absorbed by a more specific one of a different quantity whose text contains it — today's
`multi` behaviour, not new.*

### 4c. 🔴 The render consequence (P-1, in the reviewer's terms)

Incomparable readings remain eligible as **simultaneous current facts** in compiler input and recall; ordinary
visibility, trust and budget limits still apply; a generative wiki is not guaranteed to print every survivor. **There
are no latest-value semantics for `measures`** until a later round defines keys: “I weigh 78 kg” and “I weigh 80 kg”
are both current. *That is the cost of stage 1, and the reviewer and the owner accepted it over cross-quantity
retirement. It is not “strictly better” in every respect.*

### 4d. Historical refusal protection is RETAINED

A `supersession_refusals` row recorded under one of the three relations **before the plan's `effective_at`** (while the
relation was `single`) keeps its contested rendering and compiler exclusion. New refusals are not created under
`multi`. *Stage 1 has no slot evidence to resolve such a pair; it stays contested until an existing verb (correct,
dispute, redaction) retires a member — no expiry* (INV-A14). *Without this, existing disagreements such as USER
`weight 78` / SYSTEM `weight 80` would lose their deterministic read-side protection (the reviewer's non-blocking
note).*

### 4e. The reclassification plan (R1-06)

A persisted store-level record, written by the 0018 amendment's operation **from the effective registry the host
passes to it**: `plan(plan_id, relation, from='single', to='multi', effective_at, registry_digest)`. `effective_at` is
the v16 schema step's commit time. **A relation enters the plan only if its effective declaration is canonically the
default** — a host that keeps its own `single` declaration for one of these names gets no plan row for it, and its
supersessions stay. *Unknown history, stated:* the registry is host configuration and is not stored, so a host that
used a custom `single` declaration in the past and the default today is indistinguishable from one that always used
the default. The plan is fixed at its first write; later different declarations are refused (`registry-changed`).

### 4f. Eligibility (R1-01, R1-03)

A row `r` is **considered** iff its `relation` has a plan row, `invalidation_reason = 'superseded'`, and — **for a
LOCAL row** — `invalidated_at < effective_at`. A considered row is evaluated **inside the user's write transaction**:

1. **Redacted** (its carriers hold the marker, or a redaction attestation names it): never considered. *Today a
   redacted row already fails the first test, because 0041 replaces `relation`; this guard is defence in depth.*
2. **Standing revocation:** if the revocation sweep's OWN predicate — the standing set and its contribution-derived
   basis, evaluated for `r` as if active — yields a `revoked_source` effect, the outcome is **`withheld_revoked`**.
   *One implementation: the sweep's.*
3. **Once per plan, ever:** if a `migration_outcome` row exists for (plan, `r`), `r` is not considered again. *This is
   the only guard for a row that returns by re-import after a local undo* (INV-A9).
4. Otherwise **`restored`**: clear `invalidated_at` and `invalidation_reason` (0022's reinstate write), journal
   `reinstated` with reason `arity_reclassified` (§4j), and record the outcome.

### 4g. Outcomes and the receipt (R1-04)

`migration_outcome(plan_id, user_id, edge_id, outcome, pre_invalidated_at, pre_reason, successor_evidence, undone_at,
undo_request_digest, undo_op_id)`, written in the same transaction as the restorations.

- **Successor evidence:** `pointer:[ids]` = every row whose `supersedes` names `r` — zero, one or many — and `none`
  when there is none. *`supersedes` is a single field (§2c-ii row 7), so two retired restatements can have one
  successor between them; the evidence is never filled by matching quantity or time.* The receipt says “replaced by:
  unknown” for `none`.
- **The receipt is a view** over these rows (the 0018 amendment's `data_migration_receipt`): ids, outcomes,
  timestamps, successor ids; object text is read from the LIVE edge at read time (a redacted edge shows the marker; a
  forgotten edge shows `no longer held`). *No copy of memory content is stored in the receipt.*

### 4h. The operation — the 0018 amendment (R1-03), OPTIONAL

The schema step v15 → v16 creates the three tables and stamps `effective_at`, changing no row. The restoration is a
separate host operation, `run_data_migration(path, *, host_attestation, registry)`: the plan once, then one
transaction per user, continuing past a failing user, idempotent on re-call, with the receipt recoverable at any time
after each user's commit. Its full contract, result table and failure boundaries are the 0018 amendment's.

🔴 **The owner made it optional (2026-10-11).** A v16 store opens normally. **Until the operation runs, the values
retired under the old rule stay hidden and no receipt exists; `doctor` warns and names the operation.** The owner
accepted that cost explicitly.

### 4i. Undo (R1-05, P-7)

`undo_restoration(user_id, edge_id, *, correlation_id=None)` — host-only.

1. **Replay first.** `correlation_id` is unique per USER and shared with 0008's `confirm()`. Same id + same request
   digest (operation, user, edge, plan) → the recorded result; same id + different digest — another edge or another
   verb — → refused. **Without an id**, a call on an already-undone row returns the recorded `already undone at T`.
2. **Eligibility:** the outcome is `restored`, not undone, and the edge is still active. Ordinary mutations — outcome
   counters, confirmation, reinforcement — do not affect eligibility; a later retirement by any other operation does,
   and the refusal names it. *Not “the latest journal event”: an ordinary `record_outcome` changes that (R1-05).*
3. **Per-field restore:** `invalidated_at := pre_invalidated_at`, `invalidation_reason := pre_reason`; every other
   field untouched. One transaction; a concurrent duplicate commits once and replays.

### 4j. The journal — an amendment to 0029

`reinstated` gains a reason from a CLOSED vocabulary — `source_restored` (0022's verb, updated to write it) and
`arity_reclassified` — refused outside it at the emission choke point. Events written before the amendment keep NULL,
read as `source_restored`. *The journal stays store-local (0029 V-INERT); it is diagnostic history, not the
restoration's evidence — `migration_outcome` is.*

### 4k. `doctor`

The `refs` warning for an active predecessor is **`info`** iff a `migration_outcome` row records it `restored` and not
undone, under a LOCAL plan or a TRUSTED restore's evidence. Under a default import the warning stays and its text names
the imported testimony. Every other `doctor` check is unchanged; the revocation check has nothing to report because
of §4f.2.

### 4l. Portability (P-4, P-5)

| | default import | trusted restore |
|---|---|---|
| edges | capped (today) | as recorded |
| `migration_outcome` rows for edges IN the file | imported as testimony; no `doctor` exemption | as recorded; exemption and undo apply |
| outcome rows for edges NOT in the file | refused | refused |
| a file from a format BEFORE the arity version | **import-time conversion**: its retired rows under plan relations are run through §4f (no time test) under a new operation id, in the import's transaction, with a receipt | same |
| a file at or after the arity version, with a `superseded` row under a plan relation and no outcome row | kept retired; reported `unknown-linkage`; never reinstated by guess | same |
| an incoming id already held locally | **SKIPPED** — never converted or overwritten; reported `collision: kept local` | same |

*Conversion touches only incoming rows: it never rescans local rows and never reverses a local undo.*

### 4m. Valid time (P-6)

Restoration clears `invalidated_at`, so the restored row's valid-time interval widens, **including past dates**: an
as-of query for a moment inside the old retirement window now returns it (§2c-ii row 5). Local operational history
remains in the store's journal; ordinary export does not carry it. *Because the owner chose a superset restoration,
some widened intervals belong to values that were correctly replaced.*

---

## 5. Regime analysis — where does this behave differently?

| regime | behaviour |
|---|---|
| default extractor path | the three relations accumulate; all incomparable readings current (§4c) |
| host registry with no `multi` change | byte-identical to today, except `keyed` is refused |
| host keeping a custom `single` declaration for one of the names | no plan row; its supersessions stay |
| store upgraded, restoration never run | values stay hidden; `doctor` warns (§4h) |
| store upgraded, restoration run | restored per user; receipts recoverable |
| restoration, then undo, then re-run | the undone row is not re-restored (§4f.3) |
| a source revoked before the restoration | its rows are withheld (§4f.2) |
| import of a pre-arity export after the restoration | converted on import; local undo untouched (§4l) |
| multi-user store | one recompilation per affected cached user view, on a later read |

---

## 6. Invariants and executable checks — REQUIRED, blocking

Each is a **MODEL check** now — dev's reference model encodes the rules of §4 and kills the named mutant — and a
named **PRODUCT test** at the implementation gate (R1-10's split). *The model: 12 invariants hold, 16 mutants killed,
on research's rule set (2026-10-11).*

| | invariant | mechanism mutant that must fail |
|---|---|---|
| **INV-A1** | a `multi` relation never supersedes on a differing value | supersede under `multi` |
| **INV-A2** | under `multi`, reinforcement and absorption behave exactly as today, and only for same-or-subsuming values | absorb non-subsuming values |
| **INV-A3** | a registry declaring `keyed` is refused | accept it |
| **INV-A4** | every registry valid today keeps its meaning (`functional=True ≡ single`) | map `True` to `multi` |
| **INV-A5** | the plan admits only canonically default declarations | a name-only selector |
| **INV-A6** | historical refusals keep their protection after reclassification | declassify them |
| **INV-A7** | a redacted row is never restored (both arms) | select by reason alone |
| **INV-A8** | the receipt names every considered row with honest successor evidence | a guessed successor; a single-pointer-only lookup |
| **INV-A9** | a row is considered once per plan, ever (re-import after undo) | selector-only completion |
| **INV-A10** | `functional` and `arity` cannot disagree | accept the disagreement |
| **INV-A11** | a row under standing revocation is never restored | omit the standing-set check |
| **INV-A12** | undo eligibility is the outcome row plus “still active” | latest-event eligibility |
| **INV-A13** | undo restores per field, replays by user-scoped id, and is idempotent without an id | whole-snapshot undo; per-edge id scope |
| **INV-A14** | retained refusals have no expiry | expire them |
| **INV-A15** | the plan is fixed at its first write | re-plan on each call |
| **INV-A16** | import converts only incoming pre-arity rows, skips collisions, never reverses a local undo | rescan local rows; overwrite on collision |
| **INV-A17** | `doctor`'s exemption follows `migration_outcome`, local or trusted only | journal-keyed exemption; default-import exemption |
| **INV-A18** | `reinstated`'s reason is closed (0029 amendment) | accept any reason |

---

## 7. Failure modes and reversibility

- **Silent failure:** a host that never runs the restoration (§4h) — warned, not silent to the operator; silent to the
  user. The superset restoration's correctly replaced values — named in the receipt; re-retirable by §4i.
- **Reversible?** Per row by §4i; whole-store by the backup the 0018 amendment's attestation requires.
- **Partial failure:** per-user transactions; the 0018 amendment's `partial` names each failed user; a re-call
  retries exactly those.
- **Attack surface:** the undo verb is narrow by construction and host-only. Stage 1 removes a surface: text the model
  extracts can no longer retire a stored value under these three relations.

---

## 8. Claims and limits

**Claimed:** under `prefers`, `health_state` and `measures`, a later statement no longer retires an earlier,
different one; values retired that way can be restored — once per user, never against a standing revocation, with a
receipt that names each one and with a per-row undo — when the host runs the restoration.

**NOT claimed:**
- **latest-value semantics for `measures`** — every incomparable reading is current (§4c);
- **that the restoration restores only wrongly retired values** — it restores a superset, by the owner's decision;
- **that the restoration runs** — it is optional (§4h);
- **keyed behaviour** — reserved, refused, a later round;
- **that `works_as` is right** — retained as a separate question.

**Release text (the owner's costs, in substance):** *“`prefers`, `health_state` and `measures` now keep every value:
a second preference, condition or measurement no longer retires the first. One consequence: every measurement you
have recorded is treated as current. This upgrade does not restore values the old rule already retired; run
`run_data_migration` to restore them and get a receipt listing each one — some were correctly replaced, and the
receipt lets you re-retire those. Until you run it, those values stay hidden and `doctor` warns.”*

---

## 9. Brief for the external reviewer — ROUND 2

**The question this round asks: is the accumulation stage, with this restoration protocol, acceptable as specified?**

- **Least sure of:** (1) §4d's retained refusals with no expiry — a pair that can never resolve in stage 1;
  (2) §4e's “canonically default” test as the only evidence of host intent; (3) §4b's residual: absorption of a bare
  reading into a more specific one of a different quantity.
- **Where we may have overstated:** §4f.2's reuse of the sweep's predicate as complete over contribution-derived
  effects — tell us if a derived case escapes it.
- **What would change our minds:** a host relying on cross-quantity retirement for one of the three relations.
- **What we are NOT asking:** keys (deferred, the owner); the superset (the owner); optional vs mandatory (the owner);
  the pointer (Q6, answered as the reviewer recommended).
- **Round 1, finding by finding:** R1-01 → §4f.2, INV-A11 · R1-02 → (A), §4a–§4b, INV-A1–A3 · R1-03 → §4h and the 0018
  amendment, INV-A9 · R1-04 → §4g, INV-A8 · R1-05 → §4i, §4k, INV-A12/A17 · R1-06 → §4e, INV-A5/A15 · R1-10 → §6's
  split and the Requires cell. P-1 → §4c · P-2 → §2 (stage 2) · P-3 → §4b · P-4/P-5 → §4l · P-6 → §4m · P-7 → §4i ·
  P-8 → §6.
- **Reviewer-safe copy:** nothing generalised.

---

## 10. Open questions

| # | question | who decides | by when | class |
|---|---|---|---|---|
| Q6 | keep or clear the successor's pointer — **RESOLVED: keep** (round 1's recommendation; R1-04/R1-05 met) | — | — | resolved |
| Q5 | operational keys (stage 2) | owner + dev | a later round | deferred |
| Q7 | `works_as` | owner | — | deferred |
| Q8 | §9 (1): an expiry or resolution path for retained refusals | dev + external reviewer | before acceptance | blocking |

---

## Reviewer checklist

- [ ] §3 has no unanswered cells, and is directional where the operation is
- [ ] §3's classes were read from the enums
- [ ] Prohibitions AND permissions are both tested
- [ ] Every default fails closed
- [ ] §2c has a row per uncontrolled input and no empty invariant cell
- [ ] §2c-ii: every reach claim carries its command
- [ ] §2 consumers were enumerated from the sites, not only by grep
- [ ] Every §6 invariant names its mutant, and the model kills it
- [ ] §10 questions each carry a class
- [ ] §8 states what this does not establish
- [ ] I have said where I think the author's conclusion is wrong, not only where the text is wrong
- [ ] I re-read the current version before reviewing, and I am quoting the version I approve
