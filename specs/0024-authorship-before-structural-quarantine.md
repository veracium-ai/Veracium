# Feature spec: the user's own words are not third-party testimony (L1)

Spec-Status: accepted
Spec-Requires: 0005, 0025

> **external round 1, F1 (blocking):** v2 declared independence while its
> §4b rewrite target — `unclassified` — is DEFINED AND PROTECTED by 0025:
> without 0025 the member is not registry-resident, and a host supplying a
> FUNCTIONAL `unclassified` would let the rewritten fact supersede, against
> §4b-i's own never-supersedes outcome. The dependency was real and the
> declaration was wrong, so the declaration moves. One-way: 0024's
> acceptance now waits on 0025's; the IMPLEMENTATION freezes remain
> separate (0024's is a measurement constraint), which the reviewer
> explicitly allows.

*Found by dev during the L1 mechanism audit research commissioned
(`veracium-research/longmemeval/L1-mechanism-audit-dev.md`, 2026-08-17),
measured at $0 over the 2026-08-01 extraction cache. Scheduled by Quentin
2026-08-17. Deliberately SEPARATE from `0025` (L2 — relation-vocabulary
enforcement); see §7b for why sharing a freeze would destroy the
measurement.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v7** — external round 5 folded (2026-08-21): **R5-1** the THIRD_PARTY-authored incoherent cell's QUARANTINED → USE_ONLY transition RULED INTENDED and stated in §5 (was "unchanged in every cell" — false), U2 upgraded to EXACT OUTPUT over the full product (a floor-only check let two implementations disagree while green), the §3 scope wording fixed (the revoked row is the stated exception). *Prior:* **v6** — external round 4 folded (2026-08-21): **R4-1** the §3 matrix scoped to non-revoked sources with the revocation dimension as its own row (N1 wins over every column) and "author rules ALONE" retired for base-vs-final disclosure language; **PAIR-R4-1** every measured figure is the shipped script's exact output (183,417; note rule 1,644 = 41.7%). *Prior:* **v5** — external round 3 folded (2026-08-21): **R3-1** the combined pipeline gains the standing-revocation floor as an explicit step (`0025` §4b-iii step 3) and §5's "unchanged under 0023" claim corrected — accepted N1 wins over the coherence rewrite, with revoked-source vectors; **R3-2** `Edge.original_relation` defined ONCE at `0025` §2 with both writers enumerated, §5's registry claim and §7a's schema row de-staled. *Prior:* **v4** — external round 2 folded (2026-08-21): **R2-1** the combined pipeline with `0025` stated once (`0025` §4b-iii) — coherence first, disclosure established for the post-coherence state, vocabulary fallback never changes it; **R2-2** §8 narrowed to the recorded-claimant property and §7 states the two doors honestly (a mis-emitted relay with subject="user" is outside every invariant here, bounded by §3b's vacuity argument); **R2-3** §3b/§7a carry the observation surface (result key, MCP strip, CLI, telemetry under the consent contract) and U5's test renamed off the withdrawn note carrier. *Prior:* **v3** — external round 1 folded (2026-08-21): **F1** `Spec-Requires: 0005, 0025` (the independence declaration was the defect); **F2** the coherence predicate made mechanical (§4a: canonical subject shared with the write site, whole-string casefold equality, odd types fail closed; §2c corrected to shipped str() behaviour; U1 restated over the complementary domain); **F3** §6 made the ONE invariant list with U7's count carriers dispositioned; **F4** §8 narrowed to the literal-user-subject cell, prospective only. Original-relation carrier moved to the typed field with `0025` F6. *Prior:* **v2** — internal round 1 folded (research, 2026-08-17). **The ruling this spec asked for is ADJUDICATED: the door OPENS, and the argument is stronger than v1's** — the steered-extractor attack is VACUOUS, not bounded (an ordinary relation already reaches MENTIONABLE), so `third_party_claim` was never a boundary against the extractor; what the fix removes is the model's power to unilaterally DEMOTE user testimony. Also folded: M1 (the §3 matrix sampled the author domain and missed the LIVE `SYSTEM`/no-`derived_from` cell), M3's pair composition, and the symmetric re-disposition count. Invariants renamed **W→U** so the prefix does not collide with `0004`'s. |
| **Status** | *see `Spec-Status:` — canonical.* Draft authorises nothing. |
| **Internal reviewers** | research — round 1 RETURN 2026-08-17 (1 adjudication + 2 moderates + minors), folded here |
| **External review** | required — changes a disclosure decision on the ingest write path |
| **Decision + date** | **ACCEPTED 2026-08-22** — external round 12, on the frozen **U1–U7** invariant surface (package `0024-0025-v12`, sha `5a91e736…`, commit `68555fe`); simultaneous with its pair partner per the round-12 verdict. The `0014` interface-freeze confirmation stands separately |
| **Path** | full |

---

## 1. Problem and motivation

**`_disclosure_for` tests the RELATION before it tests the AUTHOR, so a
record the USER wrote can be quarantined as third-party testimony.**

```python
# src/veracium/ingest.py:96
if relation == QUARANTINE_RELATION:          # "third_party_claim"
    return Disclosure.QUARANTINED            # <-- the author is never consulted
if (author == EvidenceAuthor.THIRD_PARTY
        or derived_from == EvidenceAuthor.THIRD_PARTY):
    return Disclosure.USE_ONLY
return Disclosure.MENTIONABLE
```

The relation is chosen by the LLM extractor. When it mislabels a user's own
statement, the store quarantines content the user said in their own voice,
and every assertable surface then refuses it — *"there are some unverified
third-party claims … but these were never confirmed by you."*

**Measured, not inferred — figures are the SHIPPED script's exact output
(round 4, PAIR-R4-1; `specs/evidence/0025/corpus_counts.py`, cache sha
`654e336a…`).** Over 183,417 cached triples from the 2026-08-01
LongMemEval run:

| measure | count | share of `third_party_claim` |
|---|---|---|
| triples on `third_party_claim` | 3,945 | — |
| … whose own `note` names the USER as the source | **1,644** | **41.7%** — the script's substring rule; the earlier 1,637/41.5% used an unshipped phrase set and is retired |
| … whose `subject` is literally `"user"` | **1,606** | **40.7%** |

The extractor testifies against itself in the note field it wrote:

```
{"relation":"third_party_claim","object":"the original price of Luna's pet bed was $40",
 "note":"price stated by user"}
{"relation":"third_party_claim","object":"The opening act was Whiskey Wanderers",
 "note":"user's observation of the event lineup"}
```

**Why this is a defect and not a design position.** The position this
product holds is *never assert unconfirmed THIRD-PARTY testimony*. It has
never said *treat the user's own words as third-party*. Correcting this is
**provenance accuracy** — it makes the stored trust label match what
actually happened — and it STRENGTHENS the position rather than trading it
away for recall.

**What we do NOT claim, and the bound on the whole spec.** A user can relay
a genuine third-party claim: *"my landlord says I owe $500."* That IS
third-party testimony, the user is merely the courier, and quarantining it
is correct. **The defect is the CONFLATION of "user relays someone else's
assertion" with "user states their own observation", and any fix that
cannot tell them apart is not a fix.** §4 turns that distinction into a
structural test rather than a matter of extractor judgement.

**What happens if we do nothing.** The store keeps mislabelling a fraction
of first-person memory as hearsay. The cost is invisible in normal use —
the content is retained, so nothing looks lost — and surfaces only as the
model declining to use things the user plainly told it.

## 2. Field contracts touched

| field | read / written | its documented contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `Provenance.disclosure` | written at ONE site (`ingest.py:181`) | `_disclosure_for(author, relation, derived_from)` decides it at ingest and nothing lowers or raises it afterwards | the gate, render, `proactive`, export, `0004`'s wiki rule, `0023`'s quarantine-at-birth | the FUNCTION's decision changes for one contradictory input class; **the single write site does not move and no second writer appears.** `0023` **N2** and `0004` W-series depend on that and are preserved |
| `Edge.quarantined` | derived | `relation == QUARANTINE_RELATION or disclosure == QUARANTINED` (`schema.py:274`) | gate, render partitioning | **UNCHANGED as a formula.** Because it ORs on the relation, a re-dispositioned triple must not keep the relation — see §4's carrier note, which is the whole reason this is not a one-line change |
| `Edge.relation` | written at ingest | the extractor's classification | supersession, absorption, `0025` | a triple that fails §4's coherence test is re-dispositioned, which means its RELATION changes too. Recorded in the typed `Edge.original_relation` field (`0025` F6; one carrier for both specs), never silently discarded |
| `Provenance.author_of_evidence` / `derived_from` | READ | who authored the evidence, and whether its content embeds lower-trust material | the cap (`0005`), the gate | **read EARLIER than today** — that is the entire change |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| the extractor's `relation` — **PRODUCER: the LLM, whose output is not constrained today (`0025`)** | absent → the triple is already dropped by the shipped `subject/relation/object` completeness check (`ingest.py:178`) | truthy non-str → NOT dropped: str()-converted by the shipped path (`ingest.py:203`), and the converted oddity is a string outside the registry, which `0025` refuses (same F2 correction as the subject cell: the previous "drop" claim was not what shipped code does) | a relation outside the registry → **out of scope here; `0025` owns it.** This spec changes only the `third_party_claim` cell | an extractor steered into labelling everything `third_party_claim` (a denial-of-assertion attack) | **U1** — the coherence test is structural, so mislabelling in EITHER direction is caught by the same rule |
| the extractor's `subject` on a `third_party_claim` triple | falsy → drop (shipped truthiness check, `ingest.py:201`) | truthy non-str → NOT dropped: str()-converted by the shipped write path (`ingest.py:225`), then misses the §4a predicate → stays QUARANTINED (external round 1, F2: this cell previously claimed a drop the shipped code does not perform) | a claimant name this store has never seen → **QUARANTINES, unchanged.** An unknown claimant is the ordinary case | **the apparent attack: text engineered to make the extractor emit `subject="user"` to ESCAPE quarantine** | **THE ATTACK IS VACUOUS, not merely bounded — see §3b.** A steered extractor never needed the subject: it could emit an ORDINARY relation and reach `MENTIONABLE` directly, today, with no coherence test in sight. **U2** additionally pins the author floor |
| `author_of_evidence` | absent → the model rejects it (required field) | invalid enum → rejected by validation before this code | — | a host declaring THIRD_PARTY content as USER | **out of scope, and stated so:** a host that lies about authorship is outside this spec's threat model and outside the product's (0006 C2 — identity is namespacing, not authentication) |

### 2c-ii. Assertions about reach — REQUIRED

**Every command was RUN in this repository on 2026-08-17 and the result
column records its real output.**

| assertion | command | result (RUN 2026-08-17) |
|---|---|---|
| **`_disclosure_for` tests the relation BEFORE the author** — the defect, in the source | `grep -n "def _disclosure_for" -A 14 src/veracium/ingest.py` | `ingest.py:96` `if relation == QUARANTINE_RELATION: return Disclosure.QUARANTINED`, at line 96, ahead of the author test at `:98` |
| **there is exactly ONE disclosure write site**, so the fix has one home | `grep -rn "_disclosure_for" src/veracium/ --include=*.py` | three hits: the definition (`:88`), a docstring reference (`:113`), and the single call (`:181`) |
| **`quarantined` ORs on the RELATION as well as the disclosure** — so changing the disclosure alone would not change the behaviour | `sed -n '273,280p' src/veracium/schema.py` | `return (self.relation == QUARANTINE_RELATION or self.provenance.disclosure == Disclosure.QUARANTINED)` |
| **the adapter is NOT the defect** — user turns are ingested as USER with no `derived_from` | `sed -n '88,96p'` of `longmemeval/run_longmemeval.py` (the harness in `~/Documents/veracium/proposals/`) | `if role == "user": return EvidenceAuthor.USER, None, "chat"` |
| **the steered-extractor attack is VACUOUS — an ordinary relation already reaches MENTIONABLE** (the executed basis for §3b) | `python -c "from veracium.ingest import _disclosure_for; ..."` over the whole `EvidenceAuthor` domain | `author=user relation=prefers -> mentionable` · `author=system -> mentionable` · `author=third_party -> use_only`. **The extractor could always grant; it never needed the subject slot** |
| **`EvidenceAuthor` has exactly THREE members — there is no `assistant`** (the domain **U2** must span; internal M1 named the row "ASSISTANT", which is a HOST MAPPING onto `SYSTEM`, not an enum member) | `python -c "from veracium.schema import EvidenceAuthor; print([e.value for e in EvidenceAuthor])"` | `['user', 'third_party', 'system']` |
| **the mislabelling is real and its size is known** | a $0 pass over the 2026-08-01 extraction cache | 3,945 `third_party_claim` triples; **41.7%** carry a note naming the user as source (script rule, round 4); **40.7%** have `subject == "user"` — the load-bearing cell, exact |

*(The third row is the one that changed the design: this looked like a
one-line reordering until `Edge.quarantined` turned out to OR on the
relation, which means a re-dispositioned triple has to lose the relation
too. A fix that only reordered `_disclosure_for` would have passed review
and changed nothing observable.)*

## 3. Trust-class matrix — REQUIRED, blocking

**Scope (round 4 R4-1; wording fixed round 5 R5-1): the FIRST row below
is the revoked-source result; every OTHER row states the result for a
NON-REVOKED standing source.** The rows are BASE authorship
disclosure — step 2 of `0025` §4b-iii — and the accepted floors then run on
the result; v5's rows read as unconditional finals, which was false the
moment `0023` N1 applied. The revocation dimension collapses to one row
because the floor ignores every column:

| author | `derived_from` | relation | subject | disclosure TODAY | disclosure AFTER | why |
|---|---|---|---|---|---|---|
| **any** | **any** | **any** | **any** — source standing-REVOKED | QUARANTINED | **QUARANTINED** | accepted `0023` **N1**: the standing-revocation floor is evaluated independently of relation, subject and author, and it WINS over the coherence re-disposition — `reference_enforcement.vector_revoked_source_floor_wins_over_coherence` pins the revoked USER-authored `third_party_claim` cell the reviewer named |
| USER | — | ordinary | anything | MENTIONABLE | MENTIONABLE | unchanged |
| USER | — | `third_party_claim` | **a claimant** | QUARANTINED | **QUARANTINED** | the user is the courier; the claim is still hearsay. **Unchanged, and this is the case the fix must not break** |
| USER | — | `third_party_claim` | **the user** | QUARANTINED | **MENTIONABLE**, relation re-dispositioned | **the contradiction.** A third-party claim whose claimant is the user is not a third-party claim |
| USER | THIRD_PARTY | `third_party_claim` | the user | QUARANTINED | **USE_ONLY** | the author floor still applies — the content embeds lower-trust material, so it never reaches MENTIONABLE |
| THIRD_PARTY | any | `third_party_claim` | the user | QUARANTINED | **USE_ONLY** | **the attack cell.** Steering `subject` buys `USE_ONLY`, never MENTIONABLE — exactly what an ordinary third-party inference gets |
| SYSTEM | THIRD_PARTY | `third_party_claim` | the user | QUARANTINED | **USE_ONLY** | `0005`'s three-lever cap logic, unchanged |
| **SYSTEM** | **none** | `third_party_claim` | the user | QUARANTINED | **MENTIONABLE** | **the cell v1 omitted (internal M1) — and it is LIVE.** See the enumeration below |
| any | any | ordinary | the user | per author | per author | unchanged |

**The full author domain, enumerated rather than sampled (internal M1).**
`EvidenceAuthor` has exactly THREE members — `user`, `third_party`,
`system` (executed, §2c-ii). **There is no `assistant` author**: an
assistant turn is a HOST MAPPING onto `SYSTEM`, with `derived_from` set or
not according to the host's trust arm. So the domain of the incoherent cell
is `author × derived_from` = 3 × 4 (three members plus absent), and every
cell is decided by the author rules after re-disposition:

| author | `derived_from` | result after re-disposition | live in the re-run? |
|---|---|---|---|
| USER | none | MENTIONABLE | yes |
| USER | THIRD_PARTY | USE_ONLY | yes |
| USER | USER / SYSTEM | MENTIONABLE | rare, legal |
| **SYSTEM** | **none** | **MENTIONABLE** | **YES — this is an assistant turn under a trusting host arm** |
| SYSTEM | THIRD_PARTY | USE_ONLY | yes — the capped assistant arm |
| SYSTEM | USER / SYSTEM | MENTIONABLE | rare, legal |
| THIRD_PARTY | any | USE_ONLY | yes |

**The SYSTEM/none cell is not an oversight to be closed; it is the host's
declared trust arm doing what it says.** A host that declares assistant
content SYSTEM-authored with no third-party derivation has said that
content is trusted, and re-disposition returns it to exactly the
disclosure an ordinary relation from the same event would have received.
**What v1 got wrong was not the outcome, it was enumerating a domain by
example.** **U2** now spans the whole product.

**Nothing in this table raises a disclosure for content whose author or
`derived_from` is THIRD_PARTY.** The cells that rise are those where the
trusted inputs — author AND declared content source — already licensed
MENTIONABLE, and only the extractor's self-contradictory label said
otherwise.

## 3b. Authorization and scope

- **Caller-facing surface, complete (external round 2, R2-3: v3 said "no
  new surface" while U7 added three).** No new API, flag or config; the
  rule is inside `_disclosure_for`, which no host can reach. But the
  OBSERVATION surface grows: the ingest result dict gains
  `redispositioned` (through `Memory.remember`, unchanged), the CLI prints
  it, telemetry gains the field, and the MCP surface STRIPS it. The
  telemetry field is governed by the accepted telemetry contract — added
  to the event-field whitelist with a minimum schema version, named in the
  consent text (version bumped), and covered by consent AND no-consent
  tests; absent consent the field is never emitted.
- **Per record, at write time.** Nothing existing is rewritten (§7).
- **Does anything become visible to a principal who could not see it
  before?** **Yes — a quarantined record becomes assertable — and v1
  described that as a BOUNDED DOOR. It is not a door at all, and the
  stronger argument is now stated here rather than left for the external
  reviewer to find (internal round 1).**

  **The attack cell is VACUOUS.** v1 worried about an extractor steered into
  emitting `subject="user"` to escape quarantine. But the extractor chooses
  the RELATION too, and it always could: a steered extractor emits an
  ORDINARY relation — `prefers`, `works_as`, anything — and reaches
  `MENTIONABLE` directly, **today, with no coherence test involved**.
  Executed (§2c-ii): `_disclosure_for(USER, "prefers", None) → mentionable`.

  **`third_party_claim` was never a security boundary against the extractor.
  It IS the extractor's output.** A defence cannot be built out of the thing
  it is defending against.

  So compare the two powers honestly. After this change the extractor's
  power to GRANT is **exactly what it was** — total over its own labels,
  floored by the author. What changes is its power to unilaterally **DEMOTE**
  the user's own testimony, which this spec takes away.

  **That is why this is not an un-cap.** An un-cap raises a record above what
  the TRUSTED inputs license. Here the trusted inputs — `author_of_evidence`
  and `derived_from`, both supplied by the host, neither chosen by the model —
  already license `MENTIONABLE`, and the UNTRUSTED input demoted it. **The
  rule restores the trusted inputs' decision after an untrusted one
  contradicted it.** `0005`'s C1 forbids granting past a floor; no floor is
  crossed here, and **U2** pins that over the full author domain.
- Under `0020`, scoped principals see no more than the policy already allows.
- **Existing records are NOT re-dispositioned** (§7). This is a write-time
  rule; a retroactive sweep is `Q1`.

## 4. Behaviour

### 4a. The coherence test

A triple is **incoherent** when `relation == QUARANTINE_RELATION` and the
**canonical subject** is exactly the user. Both halves are mechanical
(external round 1, F2 — "denotes the user themself" named an intent, not a
computation):

- **Canonical subject** = `str(t["subject"]).strip()` — the SAME conversion
  the shipped write path applies (`ingest.py:225`), computed ONCE and used
  for both the test and the stored field, so the test can never disagree
  with the subject the Edge actually carries.
- **The predicate** = `canonical_subject.casefold() == "user"`. Whole-string
  equality after casefold; nothing else — no substring match, no synonym
  list, no note inspection.
- **Odd types fail closed.** The shipped completeness check (`ingest.py:201`)
  drops only FALSY subjects; a truthy non-string — `["user"]`,
  `{"name": "user"}`, `1` — survives it and is str()-converted.
  `str(["user"])` is `"['user']"`, which is not `"user"`, so every such
  triple misses the predicate and stays QUARANTINED. A subject must arrive
  as the literal string to be recognized; type games buy nothing.

The extraction prompt states the
claimant convention explicitly — *"Emit those ONLY as `{"relation":
"third_party_claim", "subject": "<claimant>", ...}"`* (`prompts.py:38`) — so
the subject slot of a third-party claim IS the claimant, and a claim whose
claimant is the user is a contradiction in the extractor's own terms.

**The test is on the SUBJECT, not on the note.** The note is free text and
was the strongest measured signal (41.7%), but it is prose an LLM wrote and
nothing constrains it. The subject is a structural slot with a stated
meaning. **We test the thing with a contract, not the thing with the
higher hit rate** — and we accept a smaller catch as the price.

### 4b. What an incoherent triple becomes

The triple is **re-dispositioned, not dropped**:

1. its `relation` becomes **`unclassified`** — the reserved, registry-resident,
   NON-FUNCTIONAL member `0025` §4b defines and injects into every effective
   registry. It is an ORDINARY relation (never `third_party_claim`, because
   `Edge.quarantined` ORs on the relation — §2c-ii row 3), and naming it here
   rather than "some fallback" is what makes the pair compose (§7b);
2. its disclosure is decided by the author rules — the second and
   third branches of `_disclosure_for`, unchanged — **as the BASE
   authorship disclosure: step 2 of the combined pipeline `0025` §4b-iii,
   after which the accepted floors (step 3 — standing revocation among
   them) produce the FINAL result** (round 4, R4-1 retired the "author
   rules ALONE" phrasing: authorship determines the base, never the
   final; round 2's R2-1 note stands — `0025` X10 is scoped to the
   vocabulary fallback and does not constrain this step);
3. **the original relation is preserved in the TYPED field
   `Edge.original_relation`** — defined ONCE at `0025` §2 as the original
   relation for ANY structural re-disposition, this rewrite being one of
   its two enumerated writers (round 3, R3-2: the two specs had drifted
   into two definitions) — so the re-disposition is visible in the record
   and reversible by inspection. Nothing is silently rewritten.

**Order matters and is the whole fix:** the author floor is evaluated
BEFORE the structural quarantine can be skipped, so no path reaches
`MENTIONABLE` for THIRD_PARTY-authored or THIRD_PARTY-derived content.

**The count is symmetric.** v1 required the original relation to survive in
the note but did not require the re-dispositions to be COUNTED — while
`0025` **X4** insists an invisible residual is how 34.9% went unnoticed.
The same principle applies to this spec's own rewrites: the ingest result
carries a re-disposition count (**U7**). A rule that silently rewrites
extractor output is the shape this project keeps finding.

#### 4b-i. What happens when BOTH specs land — the composition, chosen not inherited (internal M3)

| question | answer |
|---|---|
| is the fallback relation registry-resident? | **yes** — `unclassified` is `0025`'s reserved member, injected structurally into every registry, so this spec's rewrite cannot violate `0025` **X1** |
| which rule runs first? | **the coherence test (this spec), then vocabulary enforcement (`0025`).** `third_party_claim` is IN the registry, so enforcement would pass it through untouched; the coherence test is the only rule that can see the contradiction |
| **is a corrected user statement then able to SUPERSEDE?** | **NO — and this is a CHOSEN cell, not an accident.** `unclassified` is non-functional, so a re-dispositioned triple becomes assertable but never supersedes a prior. **Half-restoration is the honest outcome**: the coherence test establishes that the extractor's TRUST label was self-contradictory; it establishes nothing about which RELATION the fact belonged under. Guessing a functional relation in order to complete the restoration would file a fact under semantics nobody derived, and a wrong guess retires an unrelated record — `0025` §4b refuses exactly that trade for the same reason |
| could a future spec complete it? | yes, and it would need evidence about the relation, not about the author. Recorded as **Q4** |

### 4c. What is deliberately NOT done

- **No retroactive sweep.** Existing quarantined records keep their
  disclosure. Re-dispositioning stored records means a SECOND disclosure
  writer, which breaks the single-write-site property `0004` and `0023`
  both reason from. `Q1` holds the question.
- **No prompt-only fix.** Tightening the extraction prompt is worth doing
  and is not a spec: a prompt is not enforcement, and this defect survived
  a prompt that already states the claimant convention.
- **No note-based heuristics.** See §4a.

## 5. Regime analysis — where does this behave differently?

| regime | behaviour |
|---|---|
| a store with no `third_party_claim` triples | **byte-identical.** The new branch is unreachable; **U4** pins it |
| ordinary assistant/user chat ingest | changes only for triples the extractor labels `third_party_claim` with `subject == user` |
| a THIRD_PARTY-authored event (mail, documents) | **CHANGED for exactly the incoherent subset, and INTENDED (external round 5, R5-1, blocking: v6 said "unchanged in every cell" while the §3 matrix and the reference both move the incoherent cell QUARANTINED → USE_ONLY — structural isolation to may-inform-never-assert).** The ruling: a third-party-authored triple whose self-contradictory label collapses gets exactly what an ordinary third-party statement gets — USE_ONLY, the author floor — no more, and §3b's vacuity bound shows the extractor could already reach that via an ordinary relation. Every COHERENT third-party cell is untouched |
| import (`0005`) | **unchanged.** The cap runs on already-written records; this is a write-time rule at ingest |
| a store under `0023` revocation | **the standing-revocation floor applies AFTER the coherence rewrite and wins (external round 3, R3-1, blocking: v4 said "unchanged" while the §4b pipeline as written let a revoked source's incoherent triple out at MENTIONABLE, against accepted N1).** A revoked source's records land QUARANTINED whatever the coherence test decides — step 3 of `0025` §4b-iii, and the revoked-source vectors pin it |
| a host supplying its own `relations` registry | unchanged in effect — and stated correctly now (round 3, R3-2): `QUARANTINE_RELATION` is a module constant AND a protected effective-registry resident under `0025` §4b-ii; a host cannot remove or conflictingly redefine it |

## 6. Invariants and executable checks — REQUIRED, blocking

| # | invariant | check |
|---|---|---|
| **U1** | a `third_party_claim` whose canonical subject (§4a: str → strip → casefold) is anything OTHER than the exact string `user` — a named claimant, a str()-converted list or dict, an empty-after-strip string — quarantines, whatever the author. The complementary domain, so no cell is left to interpretation (external round 1, F2) | `test_relayed_third_party_claim_still_quarantines` |
| **U2** | the §3 matrix is EXACT OUTPUT over the FULL `author × derived_from` product (3 × 4, internal M1) — every cell's disclosure equals the matrix's stated value, revoked and non-revoked; not merely the not-MENTIONABLE floor (round 5, R5-1: two implementations could disagree on the QUARANTINED-vs-USE_ONLY cell while a floor-only check stayed green) | `test_author_floor_spans_the_author_domain` — enumerates the entire product against a separately-written EXACT oracle, so a cell can neither be overlooked nor satisfied by the wrong member of the floor |
| **U3** | a re-dispositioned triple does not keep `QUARANTINE_RELATION`, so `Edge.quarantined` reports false | `test_redispositioned_triple_is_not_quarantined_by_relation` — the check that would have failed on a fix that only reordered `_disclosure_for` |
| **U4** | a store whose extractor never emits `third_party_claim` is byte-identical before and after | `test_no_quarantine_relation_is_byte_identical` |
| **U5** | the original relation survives in the record, in the typed `Edge.original_relation` field | `test_redisposition_carries_the_original_relation` — renamed round 2 (R2-3): the old name promised the note, a carrier round 1 withdrew |
| **U6** | disclosure still has exactly ONE write site | `test_single_disclosure_write_site` — the AST sweep `0023` **N2** already specifies, extended to cover this change rather than duplicated |
| **U7** | re-dispositions are COUNTED and returned, never silent — the symmetric form of `0025` **X4** applied to this spec's own rewrites. **The COUNT'S CARRIERS, enumerated (round 1, F3):** the ingest result dict gains `redispositioned` (present on EVERY path, 0 on the unparseable and no-hit paths — an absent key is not a zero); `Memory.remember` passes the dict through unchanged; the MCP surface STRIPS it (consistent with its existing removal of the supersession/reinforcement counts — operator counts are a library surface, not a tool-call surface); telemetry gains the field beside the existing ingest counts. **Carrier ownership: `0025` §4c is the single authoritative disposition for the pair's counters; this row applies it to `redispositioned`, not restates it (round 2, R2-5)** | `test_redisposition_count_is_reported` — asserts the key on all three paths, including both zeros |

## 7. Failure modes and reversibility

- **If the coherence test is too narrow** (subject-based, ~40.7% of the
  mislabelled population): the residual stays quarantined, which is
  today's behaviour. **Failing narrow costs recall, never assertion.**
- **If it were too broad** — the case to fear — a genuine relayed claim
  would become assertable. Two distinct doors, stated honestly (external
  round 2, R2-2): a RULE that widened (a non-user claimant slipping the
  predicate) is what **U1** catches, and the §3 matrix is enumerated rather
  than sampled. But an EXTRACTOR that mis-emits a genuine relay with
  `subject="user"` lands inside the first-person exception and NO invariant
  here catches it — the rule reads what is recorded, not what was said.
  That residual is bounded by the same fact §3b establishes: the extractor
  could already grant assertability through an ordinary relation, so the
  exception adds no power it lacked.
- **Reversibility:** the rule is write-time, so reverting the code reverts
  the behaviour for all future writes. Records written under it keep the
  disclosure they were written with, which is the same asymmetry `0023`
  §4i declares — stated here rather than discovered.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `src/veracium/ingest.py` | `_disclosure_for` gains the coherence test; the call site and the write site do not move |
| `src/veracium/schema.py` | the FIXED re-disposition target `unclassified` (`0025`'s reserved member — never conditional, round 3 R3-2 removed the stale "if the registry has no suitable member" phrasing) and the shared `Edge.original_relation` typed field, defined once at `0025` §2 with its two writers enumerated |
| `src/veracium/prompts.py` | **optional and non-normative**: tightening the claimant convention. Explicitly NOT the fix (§4c) |
| the ingest result dict / `Memory.remember` / MCP / CLI / telemetry | `redispositioned` on every path / passthrough / STRIPPED / printed / whitelisted field under the telemetry contract with consent gating (round 2, R2-3 — these carriers were governed by U7 but absent from this inventory) |
| tests | the §6 table's named tests, U1–U7 — §6 is the ONE authoritative invariant list (external round 1, F3: this row said W1–W6, §6 listed U1–U7 out of order, and the package header hand-typed a range ending one past the real list — three versions of one surface; every other carrier now REFERENCES §6 rather than restating it) |
| docs / CHANGELOG | a behaviour-change entry: some records that were quarantined are now assertable, with the matrix |

### 7b. Cross-spec carriers

| spec | touchpoint | disposition |
|---|---|---|
| **`0025`** | the relation vocabulary | **ORTHOGONAL, AND MUST NOT SHARE A FREEZE.** `third_party_claim` is IN the 19-relation registry, so `0025`'s enforcement does not touch this mislabelling, and this spec does not reduce the off-vocabulary population. They are independent mechanisms, and — the operative reason — **a shared freeze makes the measured movement unattributable between them** |
| **`0005`** | the import cap | CONSUMED unchanged. The cap floors imported records to `USE_ONLY`/`QUARANTINED` after this rule has already run at their origin store |
| **`0004`** | the wiki drop | **nothing to add.** This spec does not invalidate; it changes what a new record may assert |
| **`0023`** | quarantine-at-birth and **N2**'s single-writer AST pin | this spec keeps the single write site, which **N2** requires. If both land, **N2**'s sweep covers this change too — one pin, not two |
| **`0020`** | scoped read | unchanged; policy decides visibility, this decides assertability |

## 8. Claims and limits

**What we will say:**

> **Provenance accuracy, in the cell the rule recognizes.** A statement you
> made in your own voice — recorded with YOU as the literal claimant — is no
> longer demoted to hearsay by an extractor mislabel. A claim recorded with
> a NON-USER claimant remains an unverified third-party claim and is never
> asserted as fact.

*(External round 2, R2-2: the earlier sentence promised relayed content "is
never asserted as fact" — but a genuine relay the extractor mis-emits with
`subject="user"` falls INSIDE the deliberate first-person exception and may
become MENTIONABLE. U1 protects non-user claimants only and cannot catch
that error. The guarantee is structural, about what is RECORDED, not about
what was originally said; §7 states the residual risk honestly.)*
>
> *(External round 1, F4: the earlier absolute form — "a statement in your
> own voice is recorded as yours" — exceeded the rule. The mechanism
> corrects the literal-user-subject cell, ~40.7% of the measured mislabel
> population, PROSPECTIVELY; a user observation the extractor emits under
> another claimant string stays quarantined, and this section may not imply
> otherwise.)*

**What this does NOT establish.**

- **It is not a recall improvement, and must not be sold as one.** Any
  benchmark movement is a byproduct of storing the right trust label. If
  the labels were already right, the score would be unchanged.
- **It does not catch every mislabelling.** The subject test addresses the
  40.7% with `subject == "user"`. The remainder — mislabelled with a
  plausible claimant, or the note-only signal — stays quarantined. **The
  residual is the honest cost of testing a structural slot instead of
  prose.**
- **It is not extractor correctness.** The extractor still mislabels; this
  refuses to act on one class of self-contradictory output. `0025` and the
  prompt are different levers.
- **It does not authenticate authorship.** A host that declares
  third-party content USER-authored is outside the threat model (`0006` C2).

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

1. **The subject test's coverage.** We chose the structural slot (40.7%)
   over the note text (41.7%) because the note has no contract. If you
   think prose with a measurably higher hit rate is the better instrument,
   argue it — we think a signal nothing constrains is not enforcement, but
   we are trading measured coverage for that principle.
2. **The one cell that RAISES a disclosure.** Everything else in this
   codebase is restrict-only, and `0005` C1 forbids grants. We argue this
   is not a grant but a CORRECTION of a mislabel, and we bound it with the
   author floor. **If you think "correction" is a door that should not be
   opened at all, that is the finding we want** — it is the same shape as
   an un-cap, and we have been suspicious of un-caps everywhere else.
3. **Where the boundary between relay and observation actually sits.**
   "My landlord says I owe $500" is a relay. "The opening act was Whiskey
   Wanderers" is an observation. Both are things the user typed about the
   external world. We claim the claimant slot separates them; attack that.

**Where we suspect we have overstated:** "provenance accuracy" is a
generous framing for a rule that catches one contradiction shape. It is
accurate for the cell it covers and silent about the rest.

## 10. Open questions

| # | question | state |
|---|---|---|
| **Q1** | should existing quarantined records be re-dispositioned retroactively? | `deferred` — it needs a SECOND disclosure writer, which breaks the single-write-site property `0004` and `0023` reason from. The same asymmetry `0023` §4i declares, for the same reason |
| **Q2** | should the note signal be used as a SECOND, weaker test — flagging rather than re-dispositioning? | **RESOLVED 2026-08-22 (Quentin): NO for v1** — a flag nobody consumes is a field, not a mechanism. The note-as-agreement-evidence idea lives on in the queued label/value agreement check (dev task #107), which is its proper generalisation |
| **Q4** | should a re-dispositioned triple ever recover a FUNCTIONAL relation, completing the restoration? | `post-v1` — it would need evidence about the RELATION, which this spec does not have and does not claim. Half-restoration (assertable, never superseding) is §4b-i's chosen cell |
| **Q3** | should a `third_party_claim` with an EMPTY subject be treated as incoherent too? | **RESOLVED 2026-08-22 (Quentin, on the reachability check this row asked for): NO.** Measured on the live ingest: a LITERAL empty subject is dropped by the shipped completeness check (unreachable); a WHITESPACE subject survives, strips to an empty claimant, and stays QUARANTINED. An absent claimant is no evidence the user is the claimant — the conservative floor holds. Both cells pinned executable: `test_q3_empty_subject_cells_ruled_and_pinned` |

## Review closure

*(PROCESS §4a — one row per review finding, with evidence that is openable
or executable. The round-by-round ledger below is GENERATED from
`specs/reviews.py`. Regenerate with `python3 specs/render_closure.py
--write`; `--check` fails the build when it drifts.)*

<!-- GENERATED:review-closure -->

**2 internal round(s) and 12 external round(s) with a returned VERDICT are recorded for `0024`; 12 package(s) were dispatched** — counted from `specs/reviews.py`, which is the source this block is generated from. A round appearing here and not there, or the reverse, is impossible by construction. **SENT rows are dispatch records, not outcomes**, and are labelled below so the two are never summed.

| round | date | findings raised (from `raised=`) | verdict (compressed) |
|---|---|---|---|
| internal 1 (verdict) | 2026-08-17 | 0 | RETURN — light: one adjudication (the ruling the spec ASKED for), two moderates, four minors, all text-level. THE ADJUDICATION: the one disclosure-RAISING cell was put to the reviewer as 'if you think this door should not open at all, that is the finding we want'. IT OPENS — and the reviewer's argum… |
| internal 2 (verdict) | 2026-08-17 | 0 | PASS — the L1/L2 pair's internal review is COMPLETE. Verified against the diff: the vacuous-attack row EXECUTED in §2c-ii (the one-liner is the whole argument); the full 3x4 author x derived_from product with U2 against a separate oracle; the composition chosen with the half-restoration cell carryin… |
| external 1 (SENT) | 2026-08-21 | — | SENT (the coupled round-1 package `0024-0025-v1` — ONE archive, two INDEPENDENT specs (Spec-Requires 0005 and 0012 respectively, no mutual coupling), per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports n/a — first external round). 0024 at v2: L1, authorship-before… |
| external 1 (verdict) | 2026-08-21 | 4 | RETURN FOR AMENDMENT (2 blocking + 2 moderate; package sha 16024eeba284ac24 pinned). F1 BLOCKING — the spec declared independence from 0025 while its §4b rewrite target `unclassified` is DEFINED AND PROTECTED by 0025; without it the member is not registry-resident and a host supplying a FUNCTIONAL `… |
| external 2 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v2`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 at v3: all four round-1 findings folded — Spec-Requires names 0005 AND 0025 with the one-way acceptance coupling stated (F1); the coherence pr… |
| external 2 (verdict) | 2026-08-21 | 3 | RETURN FOR AMENDMENT (1 blocking + 2 moderate; sha 09f48f99 pinned). R2-1 BLOCKING — MY OWN two round-1 fixes contradict when composed: 0025 X10 said disclosure comes from the ORIGINAL relation while 0024 §4b assigns a re-dispositioned triple author-rules disclosure (USER → MENTIONABLE where the ori… |
| external 3 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v3`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 at v4: all three round-2 findings folded — the combined pipeline stated once at 0025 §4b-iii with X10 narrowed to the vocabulary fallback and … |
| external 3 (verdict) | 2026-08-21 | 2 | RETURN FOR AMENDMENT (1 blocking + 1 moderate; sha 588c761e pinned). R3-1 BLOCKING — the combined pipeline composed the PAIR and forgot the ACCEPTED STACK: a standing-revoked source's incoherent triple came out MENTIONABLE while accepted 0023 N1 requires QUARANTINED independently of author and relat… |
| external 4 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v4`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 at v5: both round-3 findings folded — the pipeline composes the ACCEPTED stack (every disclosure floor an explicit step, 0023 N1 named, revoke… |
| external 4 (verdict) | 2026-08-21 | 2 | RETURN FOR AMENDMENT (1 blocking + the shared evidence finding; sha c10b7341 pinned). R4-1 BLOCKING — §3's matrix still stated unconditional finals from author and relation alone: its USER/none/third_party_claim row said MENTIONABLE, false the moment the source is standing-revoked (accepted 0023 N1 … |
| external 5 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v5`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 at v6: both round-4 findings folded — the §3 matrix scoped to non-revoked sources with the revocation dimension its own row and base-vs-final … |
| external 5 (verdict) | 2026-08-21 | 1 | RETURN FOR AMENDMENT (1 blocking; sha b557698b pinned). R5-1 BLOCKING — the THIRD_PARTY-authored incoherent cell is simultaneously CHANGED (the matrix and reference move it QUARANTINED → USE_ONLY: relation re-dispositioned, quarantined property true → false, structural isolation → may-inform-never-a… |
| external 6 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v6`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 at v7: the round-5 finding folded — the THIRD_PARTY incoherent cell's transition RULED INTENDED and stated in §5, U2 exact-output over the ful… |
| external 6 (verdict) | 2026-08-21 | 0 | RETURN FOR AMENDMENT — DEPENDENCY-ONLY (sha ac0434d9 pinned): NO new 0024-scoped defect; R5-1 is CLOSED. 0024 cannot be accepted while its Spec-Requires 0025 remains unresolved. No amendment; the spec stays at v7 |
| external 7 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v7`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 UNCHANGED at v7 — the round-6 return was dependency-only (no 0024-scoped defect; R5-1 closed); it rides for the coupled verdict while 0025 res… |
| external 7 (verdict) | 2026-08-21 | 0 | RETURN FOR AMENDMENT — DEPENDENCY-ONLY (sha 5275d119 pinned): no new 0024-scoped defect; U1-U7 coherent; acceptance blocked by required 0025. No amendment; stays v7 |
| external 8 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v8`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 UNCHANGED at v7 — second consecutive dependency-only return; rides for the coupled verdict while 0025 resolves |
| external 8 (verdict) | 2026-08-21 | 0 | RETURN FOR AMENDMENT — DEPENDENCY-ONLY (sha 3f6ed6f0 pinned): no new 0024-scoped defect, third consecutive round; acceptance blocked by required 0025. No amendment; stays v7 |
| external 9 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v9`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 UNCHANGED at v7 — third consecutive dependency-only return; rides for the coupled verdict |
| external 9 (verdict) | 2026-08-21 | 0 | RETURN FOR AMENDMENT — DEPENDENCY-ONLY (sha a3970517 pinned): no new 0024-scoped defect, fourth consecutive round; blocked on required 0025. Stays v7 |
| external 10 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v10`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 UNCHANGED at v7 — fourth consecutive dependency-only return |
| external 10 (verdict) | 2026-08-21 | 0 | RETURN FOR AMENDMENT — DEPENDENCY-ONLY (sha 1e0c5104 pinned): byte-identical to the v9 copy, no new direct defect, fifth consecutive round; blocked on required 0025. Stays v7 |
| external 11 (SENT) | 2026-08-21 | — | SENT (package `0024-0025-v11`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 UNCHANGED at v7 — fifth consecutive dependency-only return |
| external 11 (verdict) | 2026-08-22 | 0 | RETURN FOR AMENDMENT — DEPENDENCY-ONLY (sha 9e5fd437 pinned): unchanged from v10, sixth consecutive round; 0005 noted ACCEPTED by the reviewer, so the wait is on 0025 alone. Stays v7 |
| external 12 (SENT) | 2026-08-22 | — | SENT (package `0024-0025-v12`; per-spec verdicts requested; sealed AFTER this row, sha pinned on return; prior reports omitted per standing instruction). 0024 UNCHANGED at v7 — sixth consecutive dependency-only return; the reviewer states both specs are final-disposition candidates after round 11's … |
| external 12 (verdict) | 2026-08-22 | 0 | 🏁 ACCEPTED on the frozen U1-U7 invariant surface (sha 5a91e7363bd5c310 verified by the reviewer; byte-identical to v11), following the SIMULTANEOUS acceptance of required 0025; prerequisite 0005 already accepted; the 0014 interface-freeze confirmation remains in force. Six final rounds dependency-on… |

**Per-finding closure ledger — PROCESS §4a.** **12 finding(s) for `0024`; 152 across the 5 tracked specs** — every number here is DERIVED from the rows below (external round 7, R7-1: the manifest claimed 26 while the ledgers held 31, and 0023 said 9/9 above a 10-row table). Generated from `specs/closure_findings.py` and validated against `specs/reviews.py` on `(spec, kind, round, id)` EXACTLY — extras, duplicates, wrong rounds and empty evidence all fail the build.

| finding | round | what it was | closed in | evidence (runnable) |
|---|---|---|---|---|
| **F1** | external 1 | the spec declared independence from 0025 while its rewrite target `unclassified` is defined and protected there — without 0025 the member is not registry-resident and a functional host shadow lets the rewrite supersede | Spec-Requires header, the F1 blockquote | `grep -n 'Spec-Requires' specs/0024-authorship-before-structural-quarantine.md  # names 0005 AND 0025, with the coupling stated in the blockquote below it` |
| **F2** | external 1 | the coherence predicate was an intent, not a computation — the shipped ingest str()-converts truthy non-strings, so subject=["user"] survives the completeness check and the predicate's domain was undefined over it | §4a, §2c (subject AND relation cells), U1 | `grep -n 'casefold' specs/0024-authorship-before-structural-quarantine.md  # the canonical predicate, shared with the write site; odd types fail closed` |
| **F3** | external 1 | the invariant inventory existed in three drifted copies — §6 out of order, §7a citing a W-range, the package header hand-typing a range one past the real list | §6 (the ONE list), §7a tests row, collected_header_0024_0025.txt | `grep -n 'ONE authoritative' specs/0024-authorship-before-structural-quarantine.md  # and the header template now points at §6 instead of restating a count` |
| **F4** | external 1 | §8 claimed provenance accuracy in general; the rule corrects the literal-user-subject cell (~40.7% of the measured mislabels), prospectively, and the claim must not exceed it | §8 | `grep -n 'cell the rule recognizes' specs/0024-authorship-before-structural-quarantine.md` |
| **R2-1** | external 2 | two round-1 fixes contradicted when composed: X10 (disclosure from the original relation) vs §4b (author-rules disclosure after the coherence rewrite) — the reference implemented one and violated the other | 0025 §4b-iii (the one pipeline), 0024 §4b(2), X10 narrowed | `$PY specs/evidence/0025/reference_enforcement.py  # vector_combined_pipeline_ordering — the cross-spec cell, both branches` |
| **R2-2** | external 2 | §8 promised relayed content is never asserted; a relay mis-emitted with subject='user' lands inside the first-person exception and U1 cannot catch it | §8 (recorded-claimant property), §7 (the two doors) | `grep -n 'NON-USER claimant' specs/0024-authorship-before-structural-quarantine.md` |
| **R2-3** | external 2 | §3b claimed no new caller surface while U7 added three; U5's test name promised the withdrawn note carrier; telemetry had no consent disposition | §3b, §7a carriers row, U5, U7 ownership pointer | `grep -n 'test_redisposition_carries_the_original_relation' specs/0024-authorship-before-structural-quarantine.md` |
| **R3-1** | external 3 | the combined pipeline composed the pair and forgot the accepted stack — a standing-revoked source's incoherent triple came out MENTIONABLE against 0023 N1, and §5 claimed 0023 behaviour unchanged | 0025 §4b-iii step 3, 0024 §5 regime row | `$PY specs/evidence/0025/reference_enforcement.py  # vector_revoked_source_floor_wins_over_coherence — shows the without-the-floor bite on purpose` |
| **R3-2** | external 3 | Edge.original_relation carried two definitions across the pair, and §5/§7a still described the pre-round-1 registry and schema shapes | 0025 §2 (the one definition, two writers), 0024 §4b(3), §5, §7a | `grep -n 'TWO writers' specs/0025-relation-vocabulary-enforcement.md` |
| **R4-1** | external 4 | the §3 matrix stated unconditional finals from author and relation — false for a standing-revoked source (0023 N1) — and §4b said 'author rules ALONE' | §3 (scope + the revocation row), §4b(2) base-vs-final language | `$PY specs/evidence/0025/reference_enforcement.py  # vector_revoked_source_floor_wins_over_coherence — the revoked USER-authored third_party_claim cell the reviewer named` |
| **PAIR-R4-1** | external 4 | the published measurements did not reproduce from the shipped script | §1 (script-exact figures, rule stated), §2c-ii | `grep -n '41.7%' specs/evidence/0025/corpus_counts.py specs/0024-authorship-before-structural-quarantine.md  # the recorded run and the spec cite ONE figure; the corpus is local-only, the script runs where it lives` |
| **R5-1** | external 5 | the THIRD_PARTY incoherent cell was changed by the matrix and declared unchanged by §5, with U2 flooring where the matrix specified — two green implementations could disagree | §5 (the ruled transition), U2 (exact output), §3 scope sentence | `grep -n 'CHANGED for exactly the incoherent subset' specs/0024-authorship-before-structural-quarantine.md  # and the reference asserts USE_ONLY exactly: vector_author_floor_holds_through_redisposition` |

<!-- /GENERATED:review-closure -->
