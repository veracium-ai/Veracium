# Feature spec: the relation vocabulary is closed, or it is not a vocabulary (L2)

Spec-Status: draft
Spec-Requires: 0012

*Found by dev while checking research's `prefers`-catch-all observation
during the L1 audit (`veracium-research/longmemeval/L1-mechanism-audit-dev.md`
§ addendum, 2026-08-17), measured at $0 over the 2026-08-01 extraction
cache. Scheduled by Quentin 2026-08-17. Deliberately SEPARATE from `0024`
(L1); see §7b.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v3** — external round 1 folded (2026-08-21): **F1** disclosure ordered before the rewrite (X10) and `third_party_claim` made a protected resident beside `unclassified` (X8/X9 widened); **F2** the retry constructed — one call per event, content-pair matching, discard rule, malformed no-op, reconciling counts; **F3** the effective-registry construction ordered (§4b-ii) with X5 pinned to the as-supplied dict and X11's immutable snapshot; **F4** the `prefers` matrix row corrected to shipped code; **F5** the three counts dispositioned on every caller surface; **F6** `Edge.original_relation` typed field replaces note prose (X3). *Prior:* **v2** — internal round 1 folded (research, 2026-08-17). **M2: the reserved member's RESIDENCY was unpinned, and that left the spec's own mechanism able to violate its own X1** — a host registry omitting `unclassified` would make the fallback write a non-member, and a host defining it as FUNCTIONAL would let every unclassified triple supersede. It is now a module constant on the `QUARANTINE_RELATION` pattern, injected into every effective registry and refused if shadowed (**X8**, **X9**). Also folded: **X4** splits into `retried`/`recovered`/`residual` so the re-run can attribute movement, and §7b states the pair composition. Ratified unchanged: the non-superseding ruling, polarity-first with X7, refuse-vs-remap, Q2's separation. |
| **Status** | *see `Spec-Status:` — canonical.* Draft authorises nothing. |
| **Internal reviewers** | research — round 1 RETURN 2026-08-17 (1 moderate + minors), folded here |
| **External review** | required — changes what reaches the supersession machinery |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation

**The product ships a 19-relation registry, the extractor emitted 12,575
distinct relation strings, and nothing checks.** The prompt says
`"relation": "<one of the relations below>"` (`prompts.py`), the registry is
passed in to build that list (`ingest.py:109`, `:125`), and the returned
value is stored verbatim (`ingest.py:180`).

| measure | value |
|---|---|
| `DEFAULT_RELATIONS` | **19** |
| distinct relation strings emitted | **12,575** |
| triples on an OFF-VOCABULARY relation | **64,029 — 34.9% of 183,416** |
| `prefers` alone | 62,143 — 33.9% |
| `prefers` + `uses_tool` | **48.1% of every triple in the corpus** |

Invented relations stored as-is: `includes` (2,718) · `has_feature`
(1,920) · `has_property` (1,141) · `is_a` (509) · `is` (480) …

**This is a BEHAVIOUR defect, not untidiness, and that is the whole case
for spending a spec on it.** `graph.py:341` reads
`rel = relations.get(edge.relation)` and gates on `if rel and rel.functional:`.
An off-vocabulary relation resolves to `None`, so it:

- can never be functional and therefore **never supersedes**, and
- never enters the contention grouping at `graph.py:423`.

**About 35% of extracted knowledge is filed where the supersession
machinery cannot reach it.** Restatements accumulate as parallel edges
instead of updating a current value — which is precisely the
current-value-versus-occurrence confusion that multi-session recall
punishes.

**The codebase already predicted this.** `schema.py:187`:

> *"Glosses matter: the extractor sees only these names + glosses, and
> confusable pairs (`works_as` vs `works_on`) otherwise drift between runs
> — which silently defeats supersession for facts filed under the wrong
> relation."*

The comment is correct. **The enforcement it implies was never written** —
a documented intention nothing enforces. And the drift is not between two
confusable names; it is across 12,556 of them.

**Sizing, stated up front because one of these numbers is a trap.**

| lever | worth |
|---|---|
| enforcing the vocabulary at all | **≈ 35%** of triples |
| canonicalising near-synonyms (`has_benefit`/`benefits`/`benefit`) | **≈ 2.6%** — 4,772 triples under a non-dominant spelling |
| the bare-quantity tail (`prefers "25 hours"`) | **11 triples corpus-wide** |

*(A first pass measured near-synonym fragmentation at 63.6%. That counted
whole GROUPS and was dominated by `prefers`(62,143) versus `prefer`(37) —
37 strays making 62,180 triples "fragmented". It overstates by ~40× and is
recorded here as DISCARDED so nobody re-derives it and reads agreement.
The honest measure is stranded minority mass: 2.60%.)*

**What happens if we do nothing.** The knowledge graph keeps a third of its
edges in a region where the update machinery does not run. Nothing errors.
The store simply accumulates, and every downstream claim about superseding
stale facts is true only of the 65% that landed in the registry.

## 2. Field contracts touched

| field | read / written | its documented contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `Edge.relation` | written at ingest | the extractor's classification, drawn from the registry | supersession (`graph.py:341`), contention (`:423`), absorption, render, `0024` | the value is now VALIDATED against the registry before storage. The field's type and meaning are unchanged; what changes is that the documented constraint becomes real |
| `DEFAULT_RELATIONS` | read | *"a small, extensible default registry. Hosts can add their own via config"* (`schema.py:185`) | `ingest_event(relations=…)`, `apply_supersession` | **UNCHANGED and load-bearing: host extensibility is why enforcement cannot mean a hardcoded list.** The registry stays the authority; enforcement means the registry is CONSULTED, not that it is frozen |
| `Relation.functional` | read | one current value per subject → supersede on change | supersession, contention | unchanged. More triples reach it; none behave differently once there |
| the ingest result dict | written | per-event counts the host logs | hosts, telemetry | gains THREE counts — `retried`/`recovered`/`residual` (§4c), present on every path. **New keys, so §7a states the compatibility question rather than assuming it** |
| `Edge.original_relation` | **NEW** — written ONLY by the §4b rewrite | the extractor's original off-vocabulary relation; `None` everywhere else | render (inspection), a future `Q1` migration | additive, default `None`; no existing consumer reads it (external round 1, F6) |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| the extractor's `relation` — **PRODUCER: the LLM, unconstrained today** | absent/empty → already dropped by the shipped completeness check (`ingest.py:178`) | non-str → same | **THE CASE THIS SPEC EXISTS FOR** — a relation outside the registry | an extractor steered to emit a registry name whose semantics do not fit the content (mislabelling INTO the vocabulary) | **X1**: unknown relations take a NAMED, explicit branch; **X4**: the branch cannot be silent |
| the HOST's registry (`ingest_event(relations=…)`) | an empty dict → **every** relation is off-vocabulary. Not hypothetical: a host can pass `{}` | a dict whose values are not `Relation` → today, `rel.functional` would raise at supersession time | a registry omitting `third_party_claim` | a host shrinking the registry to force everything into the unknown branch | **X5**: the registry is validated at the API boundary, and an empty registry is REFUSED rather than silently disabling classification |
| the relation's SEMANTICS | — | — | a name in the registry used for the wrong content | the mislabelling `0024` addresses, in the other direction | **out of scope, and stated:** this spec enforces MEMBERSHIP, not correctness. A relation can be in the registry and wrong, and no check here catches that |

### 2c-ii. Assertions about reach — REQUIRED

**Every command was RUN in this repository on 2026-08-17.**

| assertion | command | result (RUN 2026-08-17) |
|---|---|---|
| **the registry is 19 relations** | `python -c "from veracium.schema import DEFAULT_RELATIONS; print(len(DEFAULT_RELATIONS))"` | `19` |
| **nothing validates the extractor's relation against it** | `grep -n "relations" src/veracium/ingest.py` | the registry is used to BUILD the prompt (`:125`) and passed to `apply_supersession` (`:202`). **No membership test anywhere between extraction and storage** |
| **an unknown relation cannot supersede** | `sed -n '341,342p' src/veracium/graph.py` | `rel = relations.get(edge.relation)` / `if rel and rel.functional:` — `None` fails the gate, so no supersession branch runs |
| **…and never enters contention grouping either** | `sed -n '422,425p' src/veracium/graph.py` | `rel = relations.get(e.relation)` / `if e.active and rel and rel.functional:` |
| **the failure mode is already written down in the code** | `sed -n '186,190p' src/veracium/schema.py` | *"confusable pairs … silently defeats supersession for facts filed under the wrong relation"* |
| **the size of the population** | a $0 pass over the 2026-08-01 extraction cache | 12,575 distinct relations; **64,029 / 183,416 = 34.9%** off-vocabulary; `prefers` 33.9%; stranded near-synonym mass **4,772 = 2.60%** |

*(The third and fourth rows are why this is a behaviour spec. Before running
them the finding read as "the extractor is untidy"; after them it reads as
"a third of the graph is outside the update mechanism", which is a
different severity and a different fix.)*

## 3. Trust-class matrix — REQUIRED, blocking

Relation membership is **orthogonal to trust**, and the fold makes the
orthogonality an ORDERING rather than an assertion (external round 1, F1,
blocking): **disclosure is computed from the ORIGINAL extracted relation,
BEFORE any vocabulary rewrite, and the computed value is retained.** The
rewrite never feeds `_disclosure_for`. Without that order the mechanism
launders hearsay: a registry from which `third_party_claim` is missing
sends the extractor's `third_party_claim` down the off-vocabulary path,
the rewrite lands it on `unclassified`, and a disclosure computed from the
REWRITTEN relation no longer trips the quarantine test. **X10** pins the
order; §4b-ii closes the registry hole itself by making
`third_party_claim` a protected resident like `unclassified`. Nothing in
this spec WRITES `disclosure`, `author_of_evidence` or `derived_from`. The
matrix is therefore about what the UPDATE machinery does, which is the
axis this spec moves.

| relation | in registry? | functional? | supersedes today | supersedes after | contention grouping |
|---|---|---|---|---|---|
| `works_as` | yes | yes | yes | yes | yes |
| `prefers` | yes | **yes** (`schema.py:203`) | yes | yes | yes |
| `works_on` | yes | no (accumulates) | no | no | no |
| `has_feature` | **no** | — | **no — unreachable** | **decided by §4b, explicitly** | **no → per §4b** |
| `is_a` | **no** | — | **no — unreachable** | as above | as above |
| a host's custom relation | yes (host registry) | host's choice | per host | per host, unchanged | per host |
| `third_party_claim` | yes | no | no | no | no |

> **external round 1, F4:** v2's `prefers` row typed "no (by design —
> preferences accumulate)" — shipped `schema.py:203` marks `prefers`
> `functional=True`, so the matrix contradicted the code it claims to
> describe. The row now restates the code, and the accumulating example is
> `works_on`, which actually is non-functional. A matrix cell is a second
> copy of the code; it is regenerated against `DEFAULT_RELATIONS`, not
> remembered.

**The cell that matters is the `has_feature` row.** Today it is unreachable by accident.
After this spec it is unreachable, or reachable, **by decision** — and the
decision is written down.

## 3b. Authorization and scope

- **No new caller-facing surface**, except the registry validation at the
  existing `ingest_event(relations=…)` boundary (**X5**).
- **Host extensibility is preserved exactly.** A host that wants
  `has_feature` adds it to its registry. Enforcement makes the registry
  authoritative; it does not make it ours.
- **Does anything become visible to a principal who could not see it
  before?** **No.** No disclosure, no filter, no scope decision is touched.
  A record's visibility is identical before and after; only whether a LATER
  record can supersede it changes.
- **Per store, at write time.** Existing edges keep their relations (§7).

## 4. Behaviour

### 4a. The polarity is the design, and it is stated first

**The enforced side is the DEFAULT. An off-vocabulary relation takes an
explicit, named branch; there is no pass-through.**

This is stated first because the natural shape of this fix — "validate
against the registry, and if it is not there, store it anyway" — is a
DENY-LIST, and a deny-list is exactly the inversion `0004`'s internal round
1 caught in a spec whose entire thesis was failing closed. The rule is
therefore written as: *every relation is handled by a named rule; the
registry decides which one.*

### 4b. What an off-vocabulary relation gets — the decision, not the default

**The unknown branch is NON-FUNCTIONAL, and that is a deliberate ruling
rather than an inherited accident.** An unknown relation must not
supersede, because superseding means retiring a prior record, and doing
that on a relation whose semantics the system does not know would destroy
data on a guess. Today's behaviour is accidentally right and this spec
makes it intentional.

**So the fix is NOT to make unknown relations supersede. It is to stop 35%
of triples from arriving there.** Two mechanisms, in this order:

1. **Constrain extraction — the retry, constructed (external round 1, F2,
   blocking; v2 described a retry without defining one).**
   - **Budget: exactly ONE provider call per EVENT**, issued only when at
     least one triple fails membership. Never one call per triple; never a
     second call, whatever the first returns.
   - **Prompt:** the same extraction prompt, the registry rendered as
     today, plus ONLY the failing triples as `(subject, relation, object)`
     with the instruction to re-emit exactly those triples using relations
     drawn from the registry. The passing triples and the episode are NOT
     re-extracted.
   - **Matching:** a retry triple replaces a failing triple only when it
     matches on the `(subject, object)` pair after the shipped
     `str().strip()` canonicalisation — the content pair is the identity;
     the relation is the thing under repair. The replacement relation must
     itself be a registry member, or the match is ignored.
   - **Discards:** retry output that matches no failing triple is
     DISCARDED — the retry may repair relations, never add facts. A
     failing triple with no match remains failing and is handled by (2).
   - **Malformed retry output** (unparseable JSON, wrong shape): the whole
     retry is a no-op — every failing triple goes to (2). No second
     attempt.
   - **The episode is written once**, from the original extraction; the
     retry cannot touch it.
   - **Counts reconcile by construction:** `retried` = triples that
     entered the retry, `recovered` = triples replaced by a registry
     member, `residual` = `retried − recovered` = triples landing in
     `unclassified` (X4).
   This is where the 35% is actually recovered.
2. **Name the residual.** A triple that still carries an off-vocabulary
   relation is stored under the RESERVED member **`unclassified`**,
   non-functional, **with the original relation preserved in a TYPED field —
   `Edge.original_relation: str | None`, default `None`, written only by the
   rewrite** (external round 1, F6: v2 said "preserved in the note", but the
   note is free prose the extractor also writes into, so recovery would mean
   parsing LLM text back out of LLM text; a typed field is mechanically
   reversible and cannot be spoofed by note content) — no data loss, no
   silent pass-through, and the residual is countable rather than
   invisible.

**The reserved member's RESIDENCY is structural, and v1 left it unpinned
(internal M2).** Saying "a reserved registry member" without saying where it
lives leaves the mechanism dependent on the very thing it is enforcing
against — the host's registry — and creates two live adversarial cells:

| cell | what v1 permitted | the rule |
|---|---|---|
| a host registry that OMITS `unclassified` | the fallback writes a relation that is not in the effective registry — **the spec's own mechanism violating X1** | `unclassified` is a MODULE CONSTANT on the `QUARANTINE_RELATION` pattern, **injected into every effective registry** at the boundary. Not optional, not removable |
| a host defining `unclassified` as FUNCTIONAL | every unclassified triple becomes able to supersede — the exact data-loss outcome §4b refuses | a conflicting definition is **REFUSED at the boundary**, beside **X5**. The name is reserved; shadowing it is an error, not an override |

This is the same shape as `QUARANTINE_RELATION` — **and the fold applies
the rule TO `QUARANTINE_RELATION` itself** (external round 1, F1): a host
registry omitting `third_party_claim` would send genuine hearsay down the
off-vocabulary path. Both names are reserved members now.

#### 4b-ii. The effective registry — construction order (external round 1, F3, blocking)

v2 stated three properties (X5 refuses empty, X8 injects, X9 refuses
shadowing) without an order, and two of them contradict: injection first
makes an empty registry non-empty, so X5 could never fire. The
construction, in order, all at the `ingest_event` boundary before any
extraction:

1. **Shape.** Every value must be a `Relation`, and every KEY must equal
   its value's `.name` — a mismatched pair is REFUSED (the registry is
   keyed by name everywhere it is read; a key/name split would make
   membership and lookup disagree).
2. **Empty.** The host registry AS SUPPLIED is tested; empty is REFUSED.
   X5 is a statement about the host's dict BEFORE injection — that
   resolves the X5/X8 contradiction.
3. **Shadowing.** A host entry named `unclassified` or
   `third_party_claim` is REFUSED (X9) — reserved names are errors, not
   overrides, and refusal happens BEFORE injection so a shadow can never
   transiently exist.
4. **Injection.** Both reserved members are added (X8).
5. **Snapshot.** The effective registry is DEEP-COPIED into an immutable
   per-event snapshot (X11). A host mutating the dict it passed — or a
   `Relation` object inside it — after the call cannot change the event's
   classification mid-flight, and two concurrent events cannot see each
   other's registries.

**Why not refuse the triple.** Refusal destroys extracted content because
the extractor picked a synonym. The cost lands on the user's memory, not
on the extractor.

**Why not auto-remap to the nearest registry member.** That is a semantic
guess made by string similarity, and a wrong remap files a fact under a
FUNCTIONAL relation, where it can then supersede an unrelated record. The
failure mode of a bad remap is data loss; the failure mode of the reserved
member is a fact that does not supersede — which is where it already is
today. **Canonicalisation is a separate lever worth ~2.6%, and `Q2` holds
it rather than smuggling it in here.**

### 4c. Visibility of the residual

The ingest result gains **three** counts — `retried` (validation failed and
re-extraction ran), `recovered` (the retry produced a registry member) and
`residual` (landed in `unclassified`). **One lump sum would be enough to
prove the mechanism runs and useless for the question that follows it:**
whether the residual is the extractor formatting badly (retry recovers it)
or the registry being too small for real corpora (retry cannot). §9's third
uncertainty and **Q4** both turn on that split, and the development re-run
needs it to attribute movement.

**Every carrier of the counts, dispositioned (external round 1, F5 — v2
named the keys and no surface):** the ingest result dict carries ALL THREE
keys on EVERY path — `0` on an event with no off-vocabulary triples and on
the unparseable-extraction path, because an absent key is not a zero;
`Memory.remember` passes the dict through unchanged; the MCP surface
STRIPS all three, consistent with its existing removal of the
supersession/reinforcement counts; the CLI prints them with the existing
counts; telemetry gains the three fields. The same carrier discipline as
`0024` U7.

A residual nobody can see is how 34.9% went unnoticed through every review
this codebase has had.

## 5. Regime analysis — where does this behave differently?

| regime | behaviour |
|---|---|
| a store whose extractor only ever emits registry relations | **byte-identical**; **X6** pins it |
| the LongMemEval corpus as measured | ~35% of triples change relation, from ad-hoc strings to registry members or the reserved member |
| a host with a large custom registry | strictly less residual — its relations are IN its registry |
| a host passing `relations={}` | **REFUSED** at the boundary (**X5**). Today it silently classifies nothing |
| an existing store, not re-ingested | unchanged. Old edges keep their relations and their non-superseding behaviour (§7) |
| a store where the re-extraction retry is unavailable (no provider) | falls to the reserved member — degraded, never refused |

## 6. Invariants and executable checks — REQUIRED, blocking

| # | invariant | check |
|---|---|---|
| **X1** | every stored `Edge.relation` is a member of the registry in force at write time (the reserved member included) | `test_every_stored_relation_is_in_the_registry` — a property test over generated extractor output, including adversarial strings |
| **X2** | the reserved member is NON-FUNCTIONAL, so an unclassified fact can never supersede | `test_reserved_relation_never_supersedes` |
| **X3** | the original relation survives on any re-dispositioned triple, in the TYPED `Edge.original_relation` field — never only in note prose (external round 1, F6) | `test_offvocab_original_relation_survives_typed` |
| **X4** | the off-vocabulary population is reported as **THREE counts, not one — `retried`, `recovered`, `residual`** (internal minor: the development re-run needs to attribute movement between "the retry worked" and "the registry was too small", and a lump sum cannot) | `test_offvocab_counts_are_reported_separately` — asserts all three keys and that they reconcile |
| **X8** | BOTH reserved members — `unclassified` AND `third_party_claim` — are present in EVERY effective registry, injected structurally rather than expected; a host cannot remove either (external round 1, F1 extended the rule to the quarantine relation) | `test_reserved_members_are_always_resident` (including registries omitting each, and both) |
| **X9** | a host shadowing EITHER reserved name — `unclassified` or `third_party_claim` — is REFUSED at the boundary, before injection | `test_shadowing_a_reserved_member_is_refused` — both names, functional and non-functional shadows; the adversarial cell, not the happy path |
| **X10** | disclosure on a rewritten triple equals disclosure computed from the ORIGINAL relation — the rewrite runs strictly after `_disclosure_for` and its output never feeds it (external round 1, F1) | `test_rewrite_never_changes_disclosure` — includes the laundering cell: a hostile registry plus an off-vocabulary quarantine-shaped relation |
| **X11** | the effective registry is an immutable per-event DEEP-COPY snapshot; mutating the host's dict or its `Relation` objects after the call changes nothing for that event | `test_registry_snapshot_is_immutable` |
| **X5** | the host registry AS SUPPLIED is validated at the API boundary — shape, key == `Relation.name` for every entry, and non-empty — BEFORE reserved-member injection, so injection can never mask an empty or malformed registry (§4b-ii order; external round 1, F3) | `test_empty_registry_is_refused` — plus `test_mismatched_key_is_refused` |
| **X6** | a store whose extractions are all in-vocabulary is byte-identical before and after | `test_in_vocabulary_corpus_is_byte_identical` |
| **X7** | the polarity holds: adding a relation to the registry is what changes behaviour; NO code path stores an unvalidated relation | `test_no_unvalidated_relation_path` — an AST/call-graph sweep asserting the write site is reached only through the validator, the structural form `0004` W7 and `0023` N2 use |

## 7. Failure modes and reversibility

- **The re-extraction retry costs a provider call** on triples that fail
  validation. Bounded at one retry per event, and `Q3` holds whether that
  is the right budget.
- **If the retry makes things worse** (the model repeats itself), the
  triple lands in the reserved member — the current behaviour, no loss.
- **Existing stores are not migrated.** Old edges keep ad-hoc relations and
  keep not superseding. A migration is `Q1`; it is a rewrite of stored
  records and needs its own argument.
- **Reversibility:** write-time. Reverting restores pass-through for future
  writes; records written under the rule keep their relations.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `src/veracium/ingest.py` | the membership validation, the single retry, and the reserved-member fallback |
| `src/veracium/schema.py` | both reserved registry members (non-functional), and the `Edge.original_relation` field |
| `src/veracium/prompts.py` | non-normative tightening; the prompt already lists the registry |
| the ingest result dict | three new count keys, present on every path. **Compatibility: hosts read this dict — the keys are ADDITIVE and no existing key changes meaning**, the same discipline `0023` applied to its `quarantined` count |
| `Memory.remember` / MCP / CLI / telemetry | pass-through / STRIPS the three counts (consistent with its existing count removal) / prints them / gains the three fields (§4c) |
| tests | the §6 table's named tests — §6 is the ONE authoritative invariant list (the v2 range here had already drifted from it; same F3-class defect `0024` fixed in its §7a) |
| docs / CHANGELOG | a behaviour-change entry: extracted relations are now constrained to the registry |

### 7b. Cross-spec carriers

| spec | touchpoint | disposition |
|---|---|---|
| **`0024`** | the mislabelling of `third_party_claim`, **and its re-disposition target** | **COMPOSITION, STATED (internal M3): `0024`'s coherence test runs FIRST — `third_party_claim` is in the registry, so enforcement would pass it through untouched — and its fallback IS this spec's `unclassified`, so the rewrite is registry-resident under X1. A corrected user statement therefore becomes assertable but NON-SUPERSEDING, which `0024` §4b-i adopts as a chosen cell rather than inheriting as an accident. ORTHOGONAL, AND MUST NOT SHARE A FREEZE.** `third_party_claim` is IN the registry, so nothing here touches that defect, and `0024` does not reduce the off-vocabulary population. **The operative reason is measurement: a shared freeze makes the movement unattributable between two levers of very different size** (~35% vs one contradiction class) |
| **`0012`** | reinforcement and the independence condition | **`Spec-Requires`, because this spec changes WHICH edges reach the supersession path at all.** 0012's rule that a restatement transfers nothing is unchanged; what changes is that ~35% more triples are eligible to be considered in the first place |
| **`0003`** | the supersession ladder and refusal records | CONSUMED unchanged. More edges reach the ladder; the ladder decides as it always has |
| **`0019`** | the `ungrounded` flag | untouched — flagged at extraction, independent of relation |
| **`0021`** | the combining-site matrix | no new combining site; this changes an input to existing ones |

## 8. Claims and limits

**What we will say:**

> **A closed relation vocabulary.** Extracted facts are filed under the
> relations your registry defines. Anything the extractor invents is
> recorded, counted and kept — but it is never filed as if the system
> understood it.

**What this does NOT establish.**

- **It is not extraction correctness.** Membership is not meaning. A
  relation can be in the registry and applied to the wrong content, and
  nothing here catches that. `0024` is one instance of that class; there
  are others.
- **It does not make unknown relations supersede**, and that is the
  intended behaviour, not a limitation we regret (§4b).
- **It does not migrate existing stores.** A store ingested before this
  keeps ~35% of its edges outside the update machinery. **Anyone reasoning
  about an existing store must not assume this fixed it.**
- **The 19-relation registry may simply be too small for real corpora.**
  48.1% of triples landing on two relations is a signal about the
  registry's fit, not only about enforcement. This spec makes the pressure
  VISIBLE via the residual count; it does not resolve it.

## 9. Brief for the external reviewer

**What we are least sure of:**

1. **Whether the reserved member is a bucket or a bug factory.** It keeps
   data and it keeps facts out of the update machinery — the same place
   they are today. If you think a large `unclassified` population is worse
   than refusing the triple outright, argue it; we chose to protect the
   user's content over the graph's tidiness, and that is a real trade.
2. **The registry's size.** Two relations carry half the corpus. We
   deliberately did NOT grow the registry in this spec, because "add more
   relations" is unfalsifiable without a measurement, and enforcement is
   what makes the measurement possible. You may think that ordering is
   backwards.
3. **The retry.** One re-extraction per failing triple is a provider call
   spent on a formatting failure. If you think a spec should not build in
   a paid retry to compensate for an unconstrained model, say so — an
   alternative is to fall straight to the reserved member and let the
   residual count drive a prompt fix instead.

**Where we suspect we have overstated:** "35%" is the share of triples on
off-vocabulary relations. It is NOT a claim that 35% of facts would have
superseded had they been in the registry — most relations are
non-functional, so many would accumulate anyway. **The honest claim is
that 35% never got the chance to be considered.**

## 10. Open questions

| # | question | state |
|---|---|---|
| **Q1** | should existing stores be migrated — ad-hoc relations remapped into the registry? | `deferred` — a rewrite of stored records, with the same second-writer concern `0024` Q1 has. Needs its own argument, and probably its own spec |
| **Q2** | should near-synonym canonicalisation (`has_benefit`/`benefits`/`benefit`) ship with this? | `pre-release` — worth ~2.6% (4,772 stranded triples) against enforcement's ~35%. **Leaning: NO, separately** — it is a different mechanism (normalisation, not membership) and bundling it repeats the attributability mistake §7b refuses |
| **Q3** | is one re-extraction retry the right budget? | `pre-release` — one is a guess. The residual count (**X4**) is the instrument that would answer it, which is an argument for shipping the count first |
| **Q4** | should the registry grow, and on what evidence? | `post-v1` — 48.1% of triples on two relations suggests it should. The residual count makes it measurable rather than a matter of taste |
