# Feature spec: the user's own words are not third-party testimony (L1)

Spec-Status: draft
Spec-Requires: 0005

*Found by dev during the L1 mechanism audit research commissioned
(`veracium-research/longmemeval/L1-mechanism-audit-dev.md`, 2026-08-17),
measured at $0 over the 2026-08-01 extraction cache. Scheduled by Quentin
2026-08-17. Deliberately SEPARATE from `0025` (L2 — relation-vocabulary
enforcement); see §7b for why sharing a freeze would destroy the
measurement.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v1** — first draft; no review rounds yet |
| **Status** | *see `Spec-Status:` — canonical.* Draft authorises nothing. |
| **Internal reviewers** | pending — research |
| **External review** | required — changes a disclosure decision on the ingest write path |
| **Decision + date** | — |
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

**Measured, not inferred.** Over 183,416 cached triples from the 2026-08-01
LongMemEval run:

| measure | count | share of `third_party_claim` |
|---|---|---|
| triples on `third_party_claim` | 3,945 | — |
| … whose own `note` names the USER as the source | **1,637** | **41.5%** |
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
| `Edge.relation` | written at ingest | the extractor's classification | supersession, absorption, `0025` | a triple that fails §4's coherence test is re-dispositioned, which means its RELATION changes too. Recorded in the note, never silently discarded |
| `Provenance.author_of_evidence` / `derived_from` | READ | who authored the evidence, and whether its content embeds lower-trust material | the cap (`0005`), the gate | **read EARLIER than today** — that is the entire change |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| the extractor's `relation` — **PRODUCER: the LLM, whose output is not constrained today (`0025`)** | absent → the triple is already dropped by the shipped `subject/relation/object` completeness check (`ingest.py:178`) | non-str → same drop | a relation outside the registry → **out of scope here; `0025` owns it.** This spec changes only the `third_party_claim` cell | an extractor steered into labelling everything `third_party_claim` (a denial-of-assertion attack) | **W1** — the coherence test is structural, so mislabelling in EITHER direction is caught by the same rule |
| the extractor's `subject` on a `third_party_claim` triple | empty → drop (shipped) | non-str → drop | a claimant name this store has never seen → **QUARANTINES, unchanged.** An unknown claimant is the ordinary case | **the attack that matters: text engineered to make the extractor emit `subject="user"` in order to ESCAPE quarantine** | **W2** — the escape is bounded by the author floor, which is evaluated FIRST after this change. A THIRD_PARTY-authored event cannot reach `MENTIONABLE` by any relation, so the attack buys `USE_ONLY` at best — which is what it would have got with no quarantine relation at all |
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
| **the mislabelling is real and its size is known** | a $0 pass over the 2026-08-01 extraction cache | 3,945 `third_party_claim` triples; **41.5%** carry a note naming the user as source; **40.7%** have `subject == "user"` |

*(The third row is the one that changed the design: this looked like a
one-line reordering until `Edge.quarantined` turned out to OR on the
relation, which means a re-dispositioned triple has to lose the relation
too. A fix that only reordered `_disclosure_for` would have passed review
and changed nothing observable.)*

## 3. Trust-class matrix — REQUIRED, blocking

| author | `derived_from` | relation | subject | disclosure TODAY | disclosure AFTER | why |
|---|---|---|---|---|---|---|
| USER | — | ordinary | anything | MENTIONABLE | MENTIONABLE | unchanged |
| USER | — | `third_party_claim` | **a claimant** | QUARANTINED | **QUARANTINED** | the user is the courier; the claim is still hearsay. **Unchanged, and this is the case the fix must not break** |
| USER | — | `third_party_claim` | **the user** | QUARANTINED | **MENTIONABLE**, relation re-dispositioned | **the contradiction.** A third-party claim whose claimant is the user is not a third-party claim |
| USER | THIRD_PARTY | `third_party_claim` | the user | QUARANTINED | **USE_ONLY** | the author floor still applies — the content embeds lower-trust material, so it never reaches MENTIONABLE |
| THIRD_PARTY | any | `third_party_claim` | the user | QUARANTINED | **USE_ONLY** | **the attack cell.** Steering `subject` buys `USE_ONLY`, never MENTIONABLE — exactly what an ordinary third-party inference gets |
| SYSTEM | THIRD_PARTY | `third_party_claim` | the user | QUARANTINED | **USE_ONLY** | `0005`'s three-lever cap logic, unchanged |
| any | any | ordinary | the user | per author | per author | unchanged |

**Nothing in this table raises a disclosure for content whose author or
`derived_from` is THIRD_PARTY.** The only cell that rises is the one where
BOTH the author and the declared content source are the user, and the
extractor's own classification contradicts itself.

## 3b. Authorization and scope

- **No new caller-facing surface.** No API, no flag, no config. The rule is
  inside `_disclosure_for`, which no host can reach.
- **Per record, at write time.** Nothing existing is rewritten (§7).
- **Does anything become visible to a principal who could not see it
  before?** **Yes, and this is the one place in the pair where the answer is
  not "no" — it is stated plainly rather than buried.** A record that was
  quarantined becomes assertable. That is the POINT: it is the user's own
  statement, and it should have been assertable when it was written. The
  bound is the matrix above — the rise happens only when author and
  `derived_from` are both non-third-party. Under `0020`, scoped principals
  see no more than the policy already allows.
- **Existing records are NOT re-dispositioned** (§7). This is a write-time
  rule; a retroactive sweep is `Q1`.

## 4. Behaviour

### 4a. The coherence test

A triple is **incoherent** when `relation == QUARANTINE_RELATION` and the
`subject` denotes the user themself. The extraction prompt states the
claimant convention explicitly — *"Emit those ONLY as `{"relation":
"third_party_claim", "subject": "<claimant>", ...}"`* (`prompts.py:38`) — so
the subject slot of a third-party claim IS the claimant, and a claim whose
claimant is the user is a contradiction in the extractor's own terms.

**The test is on the SUBJECT, not on the note.** The note is free text and
was the strongest measured signal (41.5%), but it is prose an LLM wrote and
nothing constrains it. The subject is a structural slot with a stated
meaning. **We test the thing with a contract, not the thing with the
higher hit rate** — and we accept a smaller catch as the price.

### 4b. What an incoherent triple becomes

The triple is **re-dispositioned, not dropped**:

1. its `relation` becomes the extractor's own fallback for an unclassified
   user statement (§7a names the exact value; it is an ORDINARY relation,
   never `third_party_claim`, because `Edge.quarantined` ORs on the
   relation — §2c-ii row 3);
2. its disclosure is decided by the author rules ALONE — the second and
   third branches of `_disclosure_for`, unchanged;
3. **the original relation is preserved in the `note`**, so the
   re-disposition is visible in the record and reversible by inspection.
   Nothing is silently rewritten.

**Order matters and is the whole fix:** the author floor is evaluated
BEFORE the structural quarantine can be skipped, so no path reaches
`MENTIONABLE` for THIRD_PARTY-authored or THIRD_PARTY-derived content.

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
| a store with no `third_party_claim` triples | **byte-identical.** The new branch is unreachable; **W4** pins it |
| ordinary assistant/user chat ingest | changes only for triples the extractor labels `third_party_claim` with `subject == user` |
| a THIRD_PARTY-authored event (mail, documents) | **unchanged in every cell.** The author floor decides, as it does today |
| import (`0005`) | **unchanged.** The cap runs on already-written records; this is a write-time rule at ingest |
| a store under `0023` revocation | unchanged — revocation quarantine is a separate floor and is not relation-derived |
| a host supplying its own `relations` registry | unchanged: `QUARANTINE_RELATION` is a module constant, not a registry entry |

## 6. Invariants and executable checks — REQUIRED, blocking

| # | invariant | check |
|---|---|---|
| **W1** | a `third_party_claim` whose subject is a CLAIMANT still quarantines, whatever the author | `test_relayed_third_party_claim_still_quarantines` |
| **W2** | no THIRD_PARTY-authored or THIRD_PARTY-derived record reaches `MENTIONABLE` by any relation/subject combination | `test_author_floor_survives_the_coherence_test` — enumerates the §3 matrix and asserts every cell, so the attack cell is exercised rather than argued |
| **W3** | a re-dispositioned triple does not keep `QUARANTINE_RELATION`, so `Edge.quarantined` reports false | `test_redispositioned_triple_is_not_quarantined_by_relation` — the check that would have failed on a fix that only reordered `_disclosure_for` |
| **W4** | a store whose extractor never emits `third_party_claim` is byte-identical before and after | `test_no_quarantine_relation_is_byte_identical` |
| **W5** | the original relation survives in the record | `test_redisposition_is_visible_in_the_note` |
| **W6** | disclosure still has exactly ONE write site | `test_single_disclosure_write_site` — the AST sweep `0023` **N2** already specifies, extended to cover this change rather than duplicated |

## 7. Failure modes and reversibility

- **If the coherence test is too narrow** (subject-based, ~40.7% of the
  mislabelled population): the residual stays quarantined, which is
  today's behaviour. **Failing narrow costs recall, never assertion.**
- **If it were too broad** — the case to fear — a genuine relayed claim
  would become assertable. **W1** is the test that fails first, and the
  matrix in §3 is enumerated rather than sampled.
- **Reversibility:** the rule is write-time, so reverting the code reverts
  the behaviour for all future writes. Records written under it keep the
  disclosure they were written with, which is the same asymmetry `0023`
  §4i declares — stated here rather than discovered.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `src/veracium/ingest.py` | `_disclosure_for` gains the coherence test; the call site and the write site do not move |
| `src/veracium/schema.py` | the fallback relation for a re-dispositioned triple, if the registry has no suitable ordinary member — a registry addition, not a new mechanism |
| `src/veracium/prompts.py` | **optional and non-normative**: tightening the claimant convention. Explicitly NOT the fix (§4c) |
| tests | W1–W6 |
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

> **Provenance accuracy.** A statement you made in your own voice is
> recorded as yours. Content a third party asserted — including something
> you relayed — remains an unverified claim and is never asserted as fact.

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

**What we are least sure of:**

1. **The subject test's coverage.** We chose the structural slot (40.7%)
   over the note text (41.5%) because the note has no contract. If you
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
| **Q2** | should the note signal be used as a SECOND, weaker test — flagging rather than re-dispositioning? | `pre-release` — it would surface the residual without acting on prose. Leaning: no for v1; a flag nobody consumes is a field, not a mechanism |
| **Q3** | should a `third_party_claim` with an EMPTY subject be treated as incoherent too? | `pre-release` — currently dropped by the shipped completeness check before this code sees it, so the cell may be unreachable. Verify before deciding |
