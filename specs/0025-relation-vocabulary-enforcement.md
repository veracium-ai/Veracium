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
| **Version** | **v5** — external round 3 folded (2026-08-21): **R3-1** the snapshot freezes ALL prompt- and classification-bearing fields `(name, functional, desc)` and is the ONE registry for prompt, retry, membership and supersession; canonical reserved comparison covers the complete shipped form (desc drift refused, `DEFAULT_RELATIONS` still passes); **R3-2** §4c is THE counter inventory — five public keys incl. `0024`'s `redispositioned`, `retry_calls` reference-only, reconciliation statable publicly; **R3-3** `unclassified` is not extractor-selectable (§4b-iv) — the prompt renders the selectable set, a direct emission enters residual accounting; **R3-4** the receipt digest-domain bump gets a cross-era construction (durable domain version on new receipts, dual-domain comparison for legacy, no migration) and is BLOCKED on the accepted-`0014` co-owner interface-freeze amendment (§7b). `original_relation` defined once for the pair (0024 R3-2). *Prior:* **v4** — external round 2 folded (2026-08-21): **R2-1** conflicting-shadow-only refusal (the shipped `DEFAULT_RELATIONS` passes — v3's rule rejected it) and the snapshot concretized as frozen `(name, functional)` extraction; **R2-2** retry totality — one-to-one multiset matching in occurrence order, ONE stated normalization (strip+casefold), recovered defined by the final stored relation, `invalid`/`retried` split so no-provider counts honestly, provider exceptions degrade recorded-never-raised, §9's per-triple sentence fixed; **R2-3** `Edge.original_relation` None-omission across every serialization, receipts partition + digest domain versioned, portability FORMAT_VERSION gated (X6 restated); **R2-4** the §2c relation cell corrected like `0024`'s; **R2-5** §3b surface complete, §4c the pair's single counter authority, telemetry under the consent contract. X10 narrowed to the vocabulary fallback (§4b-iii). *Prior:* **v3** — external round 1 folded (2026-08-21): **F1** disclosure ordered before the rewrite (X10) and `third_party_claim` made a protected resident beside `unclassified` (X8/X9 widened); **F2** the retry constructed — one call per event, content-pair matching, discard rule, malformed no-op, reconciling counts; **F3** the effective-registry construction ordered (§4b-ii) with X5 pinned to the as-supplied dict and X11's immutable snapshot; **F4** the `prefers` matrix row corrected to shipped code; **F5** the three counts dispositioned on every caller surface; **F6** `Edge.original_relation` typed field replaces note prose (X3). *Prior:* **v2** — internal round 1 folded (research, 2026-08-17). **M2: the reserved member's RESIDENCY was unpinned, and that left the spec's own mechanism able to violate its own X1** — a host registry omitting `unclassified` would make the fallback write a non-member, and a host defining it as FUNCTIONAL would let every unclassified triple supersede. It is now a module constant on the `QUARANTINE_RELATION` pattern, injected into every effective registry and refused if shadowed (**X8**, **X9**). Also folded: **X4** splits into `retried`/`recovered`/`residual` so the re-run can attribute movement, and §7b states the pair composition. Ratified unchanged: the non-superseding ruling, polarity-first with X7, refuse-vs-remap, Q2's separation. |
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
| the ingest result dict | written | per-event counts the host logs | hosts, telemetry | gains the §4c public counters (THE inventory — round 3, R3-2 stopped this row restating it), present on every path. **New keys, so §7a states the compatibility question rather than assuming it** |
| `Edge.original_relation` | **NEW** — THE single definition for the pair (external round 3, R3-2: v4 defined it here as off-vocabulary-only while `0024` also wrote it): the original relation for ANY structural re-disposition, with exactly TWO writers — `0024`'s coherence rewrite and this spec's vocabulary fallback | the pre-rewrite relation; `None` everywhere else | render (inspection), a future `Q1` migration | additive, default `None`; no existing consumer reads it (round 1, F6). **SERIALIZATION, dispositioned (external round 2, R2-3, blocking — an optional field still serializes its None and broke every byte contract): the field is OMITTED from every serialization when `None`** (a field-level serializer, not a call-site `exclude_none`), so an unaffected `Edge` is byte-identical across store JSON, receipts, exports and MCP render — proven by vector, not asserted. **Receipts — the CROSS-ERA construction (external round 3, R3-4, blocking: a bare domain bump broke lost-response retries — existing receipts store only `request_digest`, phase two compares digests directly, and identical bytes hashed under v1 and v2 domains differ, so a legitimate retry classified as a DIFFERENT request):** the accepted request-receipt field partition gains the field in the SAME commit; NEW receipts durably store the digest-domain version beside `request_digest`; for LEGACY receipts (no stored version) phase two compares under BOTH domains and a match under either is the same request; stored receipts are never migrated; true mismatches refuse exactly as today; the era rule ships with frozen vectors. **This amends accepted `0014`'s frozen interface, so it requires the co-owner interface-freeze amendment process — implementation is BLOCKED on that authorization (§7b names it)** **Portability:** the export FORMAT_VERSION increments; the import gate accepts the prior version (absent → `None`) and the new one — old readers see bytes they already accept because the None-omission keeps unaffected edges identical |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| the extractor's `relation` — **PRODUCER: the LLM, unconstrained today** | absent/empty → already dropped by the shipped completeness check (`ingest.py:178`) | truthy non-str → NOT dropped: str()-converted by the shipped path (`ingest.py:203`), and the converted string is validated like any other — the same correction round 1 made to `0024`'s copy of this cell and round 2 found missing here (R2-4); the retry's normalization (§4b(1)) is the same stated rule | **THE CASE THIS SPEC EXISTS FOR** — a relation outside the registry | an extractor steered to emit a registry name whose semantics do not fit the content (mislabelling INTO the vocabulary) | **X1**: unknown relations take a NAMED, explicit branch; **X4**: the branch cannot be silent |
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
| **the size of the population** | `$PY specs/evidence/0025/corpus_counts.py --cache <extractions.jsonl>` — the aggregation is now a SHIPPED script whose docstring pins the cache manifest (sha `654e336a…`) and states its two ±0.01% deltas from this row honestly (round 3 package feedback; the corpus itself stays local-only) | 12,575 distinct relations; **64,029 / 183,416 = 34.9%** off-vocabulary; `prefers` 33.9%; stranded near-synonym mass **4,772 = 2.60%** |

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

- **Caller-facing surface, complete (external round 2, R2-5: v3 said
  "none except registry validation" while adding counters and changing
  CLI/telemetry output).** The registry validation at the existing
  `ingest_event(relations=…)` boundary (**X5**); the §4c public counters
  (§4c — the AUTHORITATIVE disposition of every counter carrier for BOTH
  specs, which `0024` U7 references rather than restates); CLI output
  gains the counts; telemetry gains the three fields under the accepted
  telemetry contract — whitelisted with a per-field minimum schema
  version, named in the consent text (version bumped), consent AND
  no-consent tests, nothing emitted absent consent.
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
   - **Matching is ONE-TO-ONE over occurrences (external round 2, R2-2,
     blocking: v3 keyed on the pair alone, so two failing triples sharing
     a normalized pair were both "recovered" by one replacement).** The
     match key is `str(x).strip().casefold()` applied to subject and
     object — stated here as THE normalization, the same rule §2c and the
     coherence predicate use (v3's prose said `strip()` while the
     reference also casefolded; one rule now, written down). Failing
     triples and retry output are consumed as MULTISETS in occurrence
     order: each retry triple repairs at most one failing triple and each
     failing triple accepts at most one repair.
   - **`recovered` is defined by the FINAL stored relation:** a repair
     counts only when the stored relation is an ORDINARY registry member —
     a retry that answers with a reserved member (`unclassified`,
     `third_party_claim`) is not a recovery; the triple goes to (2) and
     counts residual (round 2, R2-2: the reserved answer previously
     counted as recovered while §4c called it residual).
   - **Discards:** retry output that matches no failing occurrence is
     DISCARDED — the retry may repair relations, never add facts.
   - **Malformed retry output** (unparseable JSON, wrong shape) **and
     provider exceptions**: the whole retry is a no-op — every failing
     triple goes to (2), the failure is RECORDED (log + the retry counts
     make it visible: `retried > 0, recovered = 0`), never re-raised, and
     never retried again. Any exception from the single call degrades this
     way; none propagates to the ingest caller.
   - **The episode is written once**, from the original extraction; the
     retry cannot touch it.
   - **Counts, total over the no-provider cell (round 2, R2-2: v3 counted
     `retried` even when no retry ran):** `invalid` = triples failing
     membership; `retried` = triples that entered an ACTUAL retry call
     (0 when no provider is configured — a count named "retried" may not
     count things that were never retried); `recovered` = repairs per the
     final-stored-relation rule; `residual` = triples landing in
     `unclassified` = `invalid − recovered`. Reconciliation is by
     construction and X4 asserts it.
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

#### 4b-iii. The combined pipeline with `0024` — stated ONCE (external round 2, R2-1, blocking)

v3 held two locally-proven rules that contradict when composed: X10 said
disclosure comes from the ORIGINAL relation, while `0024` §4b re-dispositions
an incoherent triple and assigns disclosure by the author rules — for a USER
author, MENTIONABLE, where the original relation said QUARANTINED. The
reference implemented `0024` and violated literal X10. The normative order,
which both specs now cite and neither restates:

1. **Coherence (`0024` §4a/§4b).** An incoherent `third_party_claim` is
   re-dispositioned; this DELIBERATELY changes the semantic state — the
   record stops being hearsay and becomes the user's own statement.
2. **Disclosure is established** for the post-coherence semantic state —
   the author rules for a re-dispositioned triple, the relation-then-author
   rules otherwise. It is computed once and RETAINED.
3. **Every ACCEPTED disclosure floor applies — the standing-revocation
   floor named explicitly (external round 3, R3-1, blocking: the v4
   pipeline composed the PAIR and forgot the stack it lands on — a
   standing-revoked source's incoherent triple came out MENTIONABLE while
   accepted `0023` N1 requires QUARANTINED independently of author and
   relation).** The floors run on the established disclosure and may only
   LOWER it; the coherence rewrite cannot lift a record over a floor that
   ignores relation and author by construction.
4. **Vocabulary fallback (this spec, §4b).** An off-vocabulary relation is
   retried/rewritten WITHOUT changing the resulting disclosure — X10's
   whole scope. The coherence rewrite in step 1 targets a registry-resident
   relation, so it never re-enters this step.


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
3. **Shadowing — CONFLICTING shadows only (external round 2, R2-1,
   blocking: v3 refused ANY entry bearing a reserved name, and the shipped
   `DEFAULT_RELATIONS` itself contains `third_party_claim` — the rule
   rejected the default registry and ordinary ingestion could not start).**
   A host entry bearing a reserved name is ACCEPTED when it exactly matches
   the canonical definition (same name, `functional=False`) and REFUSED
   when it conflicts — a functional reserved member, or any semantic drift
   from the canonical form, **where the canonical form is the COMPLETE
   shipped definition — `(name, functional, desc)` — so a reserved entry
   with the right name and flag but a rewritten `desc` is refused
   (external round 3, R3-1: `desc` is rendered into the extraction prompt;
   a drifted gloss steers the extractor while passing a name-and-flag
   check).** The canonical forms are the module-constant `Relation` objects
   `DEFAULT_RELATIONS` itself references, so the shipped registry still
   passes unchanged, as §2 promises — the R2-1 correction is preserved,
   not recursed.
4. **Injection.** Any reserved member not already present (canonically) is
   added (X8).
5. **Snapshot.** The effective registry is EXTRACTED into an immutable
   per-event snapshot whose members are frozen internal records of
   `(name, functional, desc)` — ALL prompt- and classification-bearing
   fields (round 3, R3-1: v4 froze only `(name, functional)` while the
   prompt renders `desc`, so the prompt and classification could observe
   DIFFERENT registries after host mutation). NOT the host's `Relation`
   objects, which are mutable pydantic models a deep copy would merely
   duplicate, not freeze (round 2, R2-1). **This ONE snapshot feeds prompt
   rendering, retry validation, membership, and supersession** — there is
   no second registry read anywhere in the event. Mutating the host's
   dict, the host's `Relation` objects, or anything reachable THROUGH the
   snapshot after construction cannot change the event's prompt or
   classification (X11's test mutates through the snapshot), and two
   concurrent events cannot see each other's registries.

#### 4b-iv. The extractor-selectable set — `unclassified` is not a choice (external round 3, R3-3)

The effective registry exists before extraction and v4 would have rendered
ALL of it into the prompt — including `unclassified`, so an extractor could
SELECT the catch-all directly: stored, in-vocabulary, `invalid=0`,
`residual=0`, `original_relation=None`. The exact instrument §4c builds —
residual counts exposing registry pressure — silently bypassed by naming
its bucket.

- **The prompt renders the SELECTABLE set: the effective registry minus
  `unclassified`.** `third_party_claim` REMAINS selectable — the trust
  convention requires the extractor to emit it for hearsay.
- **An extractor-originated `unclassified` is OFF-vocabulary by
  definition** — it fails membership of the selectable set, enters the
  ordinary retry path, and lands in the residual accounting with
  `original_relation="unclassified"`. The catch-all is reachable only
  through the system's own fallback (this spec's §4b and `0024`'s
  re-disposition), which stays registry-resident under X1.

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

**THE COUNTER INVENTORY — the pair's ONE authoritative list (external
round 3, R3-2: v4's carriers said "three" while §4b defined `invalid`, the
reference emitted five keys, and `redispositioned` — which `0024` U7
declares governed HERE — was absent).**

| counter | public? | meaning |
|---|---|---|
| `invalid` | **yes** | triples failing selectable-set membership (§4b-iv) — needed publicly: with no provider the honest line is `invalid=1, retried=0, residual=1`, unstatable in three keys |
| `retried` | **yes** | triples that entered an ACTUAL retry call |
| `recovered` | **yes** | repairs per the final-stored-ordinary-member rule |
| `residual` | **yes** | triples landing in `unclassified`; `invalid = recovered + residual` reconciles in PUBLIC keys |
| `redispositioned` | **yes** | `0024`'s coherence rewrites (its U7 defers here) |
| `retry_calls` | **no — reference-only** | the harness's one-call-per-event probe; never in any public carrier |

All five public keys are present on EVERY path — `0` on an event with
nothing off-vocabulary and on the unparseable-extraction path, because an
absent key is not a zero. `Memory.remember` passes the dict through
unchanged; the MCP surface STRIPS all five, consistent with its existing
removal of the supersession/reinforcement counts; the CLI prints them with
the existing counts; telemetry gains the five fields under the §3b consent
contract. Every other mention of the counts in EITHER spec references this
table.

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
| **X4** | the off-vocabulary population is reported through the §4c PUBLIC counters — one authoritative inventory, no lump sum (the development re-run needs to attribute movement between "the retry worked" and "the registry was too small") | `test_offvocab_counts_are_reported_separately` — asserts every §4c public key on every path and that `invalid = recovered + residual` reconciles |
| **X8** | BOTH reserved members — `unclassified` AND `third_party_claim` — are present in EVERY effective registry, injected structurally rather than expected; a host cannot remove either (external round 1, F1 extended the rule to the quarantine relation) | `test_reserved_members_are_always_resident` (including registries omitting each, and both) |
| **X9** | a host entry CONFLICTING with either reserved name's canonical definition is REFUSED at the boundary, before injection; an exactly-matching entry is accepted — the shipped `DEFAULT_RELATIONS` must pass (external round 2, R2-1) | `test_conflicting_reserved_shadow_is_refused` — both names, functional shadows refused, canonical matches accepted, AND the shipped default registry accepted verbatim |
| **X10** | disclosure on a VOCABULARY-rewritten triple equals disclosure established BEFORE the vocabulary fallback ran — the fallback never changes an established disclosure (external round 2, R2-1: v3's "from the ORIGINAL relation" contradicted `0024` §4b, whose COHERENCE rewrite legitimately changes the semantic state disclosure is computed FOR; X10 is now scoped to the vocabulary fallback alone, and §4b-iii states the one combined pipeline) | `test_vocabulary_fallback_never_changes_disclosure` — includes the laundering cell AND the cross-spec ordering vector (an incoherent triple whose coherence rewrite yields MENTIONABLE is CORRECT; an off-vocabulary hearsay-shaped relation keeps its pre-fallback disclosure) |
| **X11** | the effective registry is an immutable per-event snapshot of frozen internal `(name, functional)` records; mutation of the host's dict, the host's `Relation` objects, OR anything reachable through the snapshot changes nothing for that event (round 2, R2-1: a read-only mapping around mutable values is not deeply immutable) | `test_registry_snapshot_is_immutable` — mutates THROUGH the snapshot, not only the caller's copy |
| **X5** | the host registry AS SUPPLIED is validated at the API boundary — shape, key == `Relation.name` for every entry, and non-empty — BEFORE reserved-member injection, so injection can never mask an empty or malformed registry (§4b-ii order; external round 1, F3) | `test_empty_registry_is_refused` — plus `test_mismatched_key_is_refused` |
| **X6** | a store whose extractions are all in-vocabulary is byte-identical before and after — TRUE ONLY VIA the `original_relation` None-omission rule (§2; round 2, R2-3: without it the new field falsified this row) | `test_in_vocabulary_corpus_is_byte_identical` — compares serialized bytes of old-shape and new-shape unaffected edges, plus a receipt-digest and portability round trip |
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
| the ingest result dict | the §4c public counters, present on every path. **Compatibility: hosts read this dict — the keys are ADDITIVE and no existing key changes meaning**, the same discipline `0023` applied to its `quarantined` count |
| `Memory.remember` / MCP / CLI / telemetry | pass-through / STRIPS the §4c public counters (consistent with its existing count removal) / prints them / gains the fields (§4c, consent-gated) |
| tests | the §6 table's named tests — §6 is the ONE authoritative invariant list (the v2 range here had already drifted from it; same F3-class defect `0024` fixed in its §7a) |
| docs / CHANGELOG | a behaviour-change entry: extracted relations are now constrained to the registry |

### 7b. Cross-spec carriers

| spec | touchpoint | disposition |
|---|---|---|
| **`0024`** | the mislabelling of `third_party_claim`, **and its re-disposition target** | **COMPOSITION, STATED (internal M3): `0024`'s coherence test runs FIRST — `third_party_claim` is in the registry, so enforcement would pass it through untouched — and its fallback IS this spec's `unclassified`, so the rewrite is registry-resident under X1. A corrected user statement therefore becomes assertable but NON-SUPERSEDING, which `0024` §4b-i adopts as a chosen cell rather than inheriting as an accident. ORTHOGONAL, AND MUST NOT SHARE A FREEZE.** `third_party_claim` is IN the registry, so nothing here touches that defect, and `0024` does not reduce the off-vocabulary population. **The operative reason is measurement: a shared freeze makes the movement unattributable between two levers of very different size** (~35% vs one contradiction class) |
| **`0014`** | the frozen raw-request receipt contract | **AMENDED, with authorization pending (round 3, R3-4).** The `Edge.original_relation` None-omission changes the complete-dump bytes the receipt digest covers; the cross-era rule (§2: durable domain-version on new receipts, dual-domain comparison for legacy, no migration) is the construction. **AUTHORIZED 2026-08-21 by Quentin (co-owner); the amendment is recorded in `0014`'s header blockquote** — the implementation block on this front is lifted |
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

**The constructions are executable (round-1 package feedback):**
`specs/evidence/0025/reference_enforcement.py` is a dependency-free
reference of the v3 constructions — the §4b-ii registry order, the §4b(1)
retry with its matching and no-op rules, X10's disclosure ordering (the
laundering cell runs the WRONG order on purpose and shows the bite),
X11's snapshot, and `0024`'s §4a predicate with its fail-closed odd-type
cells, and (round 2) the shipped-default-registry, duplicate-pair,
snapshot-through-mutation, byte-identity and combined-pipeline vectors.
The vector list is the file itself — no count here to drift; the
implementation will be differentially tested
against it, the `0022` vector-harness discipline.

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
3. **The retry.** One re-extraction per EVENT (§4b(1) — round 2 corrected
   this sentence, which still said per failing triple) is a provider call
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
