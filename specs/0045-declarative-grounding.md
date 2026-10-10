# Feature spec: the declarative grounding axis — was a fact STATED, or did we work it out?

Spec-Status: draft

| | |
|---|---|
| **Author / session** | research (veracium-research-48), the candidate's author → dev (veracium-2b), adopted at rest and re-read from the file: v1.3 2026-09-20 from `0045-declarative-grounding-CANDIDATE.md` (sha16 bca55cc31018d5de); v1.4 2026-10-10 from `0045-declarative-grounding-CANDIDATE.md` (sha16 7e306b4bcd327921) |
| **Version** | **v1.4 — 2026-10-10: the owner's answers folded, a conflict with accepted 0019 named and resolved, and the document restructured into the template's sections.** Base: the tree's adopted copy at `4ea1ce5` (v1.3); the Author and Number cells are dev's and are carried verbatim. 🔴 **v1.3 said this spec “extends 0019” and never named that 0019 §4c (accepted) is *flag-never-refuse*** — *“demotion would silently bury real memories, which is refusal wearing a different hat”* — **while §2d's persistence line refuses at the flag, on a predicate this spec WIDENS.** The reconciliation is a companion **amendment to 0019 §4c**, carried in this package (cited by description, not by a research-tree filename, which would dangle from `specs/` — v1.3's own correction): a refused inference returns to the host as a PROPOSAL and is stored only on the user's confirmation. **The owner chose that mechanism on 2026-10-10 (“yes, go with (A)”)**, and it answers the open question v1.3 left in §2d: **a confirmation path for an inferred attribute IS intended (the owner, 2026-10-10, Q2 = yes)**, and a confirmed inference is a **third grounding value, `confirmed`**, derived rather than stored (§4d), which keeps 0019's flag immutable. **Part B's residue is removed**: v1.3 still argued in §1 that grounding and reply were ONE document, and its claims, alternatives and second brief question were Part B's — they now live in 0047. **Template sections §2, §2c, §2c-ii, §3 added.** Prior: v1.3 · v1.2 · v1.1 · v1. |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line at the top* |
| **Internal reviewers** | research (author) · dev |
| **External review** | **required** — it changes what the agent may ASSERT about a person, and what ingest is permitted to write. |
| **Decision + date** | **Q2 (a confirmation path is intended): yes, the owner, 2026-10-10. The mechanism (A): the owner, 2026-10-10.** Acceptance: pending the external round. |
| **Path** | **full** |
| **Number** | 0045 — from `allocation.py --next` at adoption, 2026-09-20. |
| **Predecessor** | none. Occasioned by `A9` (Solove's aggregation; Lee et al., CHI 2024, from 321 documented AI privacy incidents). **Travels with** 0047 (the subject's reply) and the 0019 §4c amendment in one package. |

---

## 1. Problem and motivation

### 1a. The demand, and why it is not a preference

The harm literature names **correct-but-uninvited inference** as a harm in its own
right — *“don't derive the thing I deliberately never told you”* — and benchmarks
reward precisely that, since it is what multi-hop items score. **The scoring rule and
the demand have opposite signs.** Our extractor infers.

**A9's ruling:** *“ingest never writes an attribute the user did not state UNLESS CONFIRMED.”* This spec is the axis
that ruling needs — **was a fact STATED, or did we work it out?** — and the line it draws.

### 1b. 🔴 `basis` cannot be borrowed, and this is load-bearing

0037 established the concept exactly — *“an inferred procedure is not less TRUSTED than
a stated one; it is differently GROUNDED”* — and then scoped its carrier to procedural
records: **`basis` is “never applicable to a declarative record”**, and the stored rule
is

    procedural  iff  record_kind == "procedural"  OR  basis is not None

**So stamping `basis` on a fact would make that fact PROCEDURAL BY FLOOR**, which is
0037's anti-laundering invariant working exactly as designed. 0037 also already rejected
a fourth `Disclosure` tier (*“the tier was never the problem; the author was”*),
`derived_from` (trust-capping only), and `needs_confirmation` (a ranking input inside
the assertable set, not a gate).

### 1c. The carrier v1 missed: 0019's `Edge.ungrounded`, on the same model

**Dev's internal review, C1, blocking.** `Edge.ungrounded` is shipped and externally accepted under **0019**, and it
is a **product-derived, ingest-time, never model-declared grounding check**: `grounding.ungrounded(obj_raw,
event_text, session_date)` is True iff any **specifics** token of the object — digit tokens, alphanumeric
identifiers, proper-noun runs, ISO dates through the resolution set — is not grounded in the event text. It carries a
render marker, proactive suppression, export carriage with a pre-v6 strip rule, and it is **monotone**.

> 🔴 **So v1's open question — *bind the fact's TERMS to the event text while allowing the object to be normalised* —
> IS 0019 §4b's predicate, widened from SPECIFICS to TERMS.** *v1 posed as an open design question something the
> product already answers in a narrower form, and concluded “every plausible existing carrier is spoken for” about a
> carrier on the same model.*

**Two booleans on one edge with overlapping meaning is the carrier split this project keeps paying for.** So **this
spec EXTENDS 0019 and adds no field**: grounding is READ from the existing carrier, and the change is the
PREDICATE'S WIDTH, from specifics to terms.

### 1d. 🔴 And extending 0019 runs into its §4c — named in v1.4, not in v1.3

0019 §4c (accepted) is **flag-never-refuse**: a flagged fact is STORED with a marker, because *“at any precision
materially below 1, a flag may be a false positive; demotion would silently bury real memories, which is refusal
wearing a different hat.”* **A9's line refuses at the flag.** And this spec widens the predicate, which raises the
false-positive rate the rationale is about.

**Resolution: the 0019 §4c amendment in this package (the owner's (A), 2026-10-10).** Ingest still writes nothing
unattested; a refused triple from the user's own event returns **to the host** — never to the model — as a
proposal; a host-only verb stores it on the user's confirmation. *A false positive becomes a question instead of a
burial.* The mechanism, its invariants and its costs (a host that ignores proposals; MCP-only deployments) are the
amendment's; this spec states the axis and the line.

### 1e. Alternatives rejected

- **Reuse `basis` for declarative facts** — §1b: the procedural floor rule makes a stamped fact procedural.
- **Add a new grounding field** — §1c: a second carrier of 0019's meaning.
- **Make the model declare a fact's grounding** — §4a: it would be marking its own homework.
- **Confirmation by re-statement through `remember()`** ((B)) — rejected by the owner, 2026-10-10: it buries every
  false positive silently.
- **Keep 0019's flag-never-refuse and only mark** — contradicts A9's ruling: it persists the derivation A9 names.

---

## 2. Field contracts touched

| field / site | read / written | its documented contract | preserved? |
|---|---|---|---|
| `grounding.ungrounded` (0019 §4b's predicate) | read at ingest | True iff any **specifics** token of the object is not in the event text | **Widened** from specifics to TERMS — **the width is this round's question (§9)**; the function's contract (deterministic, product-computed, never model-declared) is preserved |
| `Edge.ungrounded` | written at ingest, immutable (0019 §4d) | the extraction event did not contain these terms | **Preserved** (the amendment writes it fresh; nothing flips it) |
| the derived grounding value *(new, derived — not stored)* | read by render, `why`, `introspect`, and 0047's §5 gate | — | `stated` · `confirmed` · `inferred` (§4d; the amendment's §4d) |
| ingest's flagged branch | writes | 0019: store with the flag | **Reversed — by the companion amendment**, not by this spec |

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| **extractor output**, including any field claiming the triple's grounding | no triple | the extractor's refusal | outside the vocabulary → unclassified route | **a model-supplied grounding claim is IGNORED and the predicate recomputed** | **INV-G1** |
| **event text** (host-supplied) | nothing attested; every triple flagged | n/a | n/a | whoever authors the event text authors the grounding corpus (0019 §8 limit 1, inherited) | 0019 §8 |
| **the query** (recall) | — | — | — | the persistence line does not reach query time: a question may still be answered by derivation | **INV-G6** |
| **data written by an older version** — edges flagged under 0019's specifics-only predicate | — | — | — | grounding derived as `inferred` (or `confirmed`, if confirmed); **no re-derivation under the wider predicate** | **INV-G7** |

### 2c-ii. Assertions about reach — REQUIRED

Commands run from the repository root at `4ea1ce5` (research, CPython 3.14.7, 2026-10-10).

| # | assertion | command | result |
|---|---|---|---|
| 1 | 0019's predicate is specifics-only today | `grep -n "True iff any specifics token of the" src/veracium/grounding.py` | READ: L201 |
| 2 | `basis` makes a record procedural by floor | `grep -rn --include="*.py" -e "basis is not None" src/veracium/` | READ: `schema.py` L237 — `return self.record_kind == "procedural" or self.basis is not None` |
| 3 | ingest stores a flagged edge today | `grep -n "A failing edge is STORED with the flag" src/veracium/ingest.py` | READ: L729 |
| 4 | 0019 §4c is flag-never-refuse | `grep -n "^### 4c. Consumers" specs/0019-*.md` | READ: L277 |

---

## 3. Trust-class matrix — REQUIRED, blocking

Classes from the enums at `4ea1ce5`: `EvidenceAuthor` = user, third_party, system, assistant; `Disclosure` =
mentionable, use_only, quarantined.

**The axis is orthogonal to trust class:** *“an inferred fact is not less TRUSTED than a stated one; it is
differently GROUNDED”* (0037's sentence, carried). So grounding never changes authority, disclosure or confidence,
and every class gets the same axis. **What differs by class is the confirmation path**, which is the amendment's:

| source event (effective) | a flagged triple, under this spec + the amendment |
|---|---|
| **user** | not written; proposed to the host; stored only on the user's confirmation → `confirmed` |
| **system** · **assistant** · **third_party** (any disclosure) | not written; not proposed; counted |

- Can it make a **user-asserted fact non-assertable**? Yes — a user's statement the predicate wrongly flags is not
  written at ingest (A9, ruled); it returns as a proposal (the amendment).
- Can **non-user content gain user-grade authority**? No.
- Can it **clear `needs_confirmation`**, or **merge, drop or overwrite provenance**? No.

**Write-time or maintain-time?** Write-time.

## 3b. Authorization and scope — *full specs only*

n/a beyond the amendment's §3b (its verb is host-only; proposals never reach the model). This spec adds no surface
and no principal sees anything new.

---

## 4. Behaviour

### 4a. Grounding is DERIVED — structurally, never asked of the model

**0037's procedural path already does this and its rule is the precedent:**
`V-EXTRACTOR-QUOTE-GATED` admits a procedural triple only when its `quote` is a verbatim
span of the event and the author is the user — *“basis is DERIVED `stated` below, never
read from the model.”*

> **The same discipline binds here: the model never declares a fact's grounding.**
> *A model asked “did they state this or did you work it out?” is being asked to mark
> its own homework, on the one axis where its incentive runs the wrong way.*

🔴 **But the procedural gate cannot be reused verbatim, and pretending otherwise would
sink the feature.** A declarative object is normally a NORMALISED value — `works_as:
night auditor at the Grand` — not a verbatim span, so a strict substring gate would
refuse most legitimate extraction. **The attestation test for declarative facts is the
open design question this spec takes to review (§9).**

### 4b. The persistence line — the policy half of `A9`

| | |
|---|---|
| **at query time** | 🔴 **derivation is unrestricted.** A question invites its own derivation; answering it is not the harm the literature names |
| **at ingest** | **an unattested attribute is NOT WRITTEN.** The default is refusal, counted, never silently filed; a user's own refused triple returns to the host as a proposal (the amendment) |
| **edges, not episodes** | **This spec claims EDGES.** 0019 put `ungrounded` on `Edge` only, and `Episode` is a separate model (C3). *Episode-level derivation is OUT OF SCOPE and said so — an episode is a narrative summary whose whole nature is derivation, and marking it inferred tells a reader nothing they did not know.* |

### 4c. “Unless confirmed” — the path (Q2, the owner, 2026-10-10: yes)

v1.3 found the clause had no carrier and left open *what grounding a confirmed inference gets*. **Decided:** the
confirmation path is the amendment's `confirm_inference` — host-only, on a proposal the library minted from the
user's own event — and **a confirmed inference is a THIRD value, `confirmed`**, not `stated`. *Collapsing it into
`stated` would erase that the system proposed it, which is the asymmetry the reply (0047) exists to answer.*

### 4d. The three values

| grounding | meaning | stored as | rendered |
|---|---|---|---|
| **`stated`** | the predicate found the triple attested in the user's event | `ungrounded = False` | no marker |
| **`confirmed`** | the system proposed it, and the person affirmed it | `ungrounded = True` + a `confirmations` row | `[inferred; confirmed by the user]` |
| **`inferred`** | flagged, never confirmed — **only edges written before the amendment** | `ungrounded = True`, no confirmation | `[possible extraction error]` (0019's marker) |

*v1.3 feared that a third value would widen 0019's monotone boolean into an enum. Deriving it from the boolean and
0008's `confirmations` table avoids that: no stored field changes, and no flag flips.*

> **The axis exists because the line has exceptions.** *A rule with an unmarked
> exception becomes a lie the first time the exception runs; the exceptions are marked,
> so the claim in §8 stays true.*

---

## 5. Regime analysis — where does this behave differently?

| regime | behaviour |
|---|---|
| **predicate at its pinned width** (specifics) | today's flagged triples are refused instead of stored-with-marker (the amendment) |
| **predicate widened** (terms — this round's question) | more triples flagged; more proposals; more refusals for non-USER events |
| **legacy store** | flagged edges stay; derived `inferred` / `confirmed` (INV-G7) |
| **query time** | unchanged: derivation unrestricted (INV-G6) |

---

## 6. Invariants and executable checks — REQUIRED, blocking

| | invariant | check, and the MUTANT it must fail on |
|---|---|---|
| **INV-G1** | **Grounding is DERIVED, never model-declared** | an extractor output claiming its own grounding is IGNORED, and the derivation is recomputed. **Mutant: honour the model's field → refuse** |
| **INV-G2** | **An unattested attribute is not written at ingest** | the refusal is counted and named. **Mutant: file it as `stated` → the count must move and the check FAIL** *(the mechanism and its proposal are the amendment's INV-P1–P3)* |
| **INV-G6** | **The persistence line does not reach query time** | a multi-hop question is still answered from the store. **Mutant: apply the ingest rule at recall → the answer disappears and the check FAILS** |
| **INV-G7** | **Legacy flagged edges are never re-derived under the wider predicate** | an edge stored before the change keeps its flag and derives `inferred`. **Mutant: re-run the widened predicate over stored edges → FAILS (and 0019's U4 refuses the write)** |
| **INV-G8** | **Grounding is three-valued and derived** | `stated` / `confirmed` / `inferred` fixtures derive correctly from the flag and the `confirmations` table. **Mutant: derive `confirmed` from the flag alone → FAILS** |

**Each check must be demonstrated RED against its mutant before acceptance.**

---

## 7. Failure modes and reversibility

- **Silent failure:** a predicate too wide refuses real statements. **Not silent in the store** (counted), and a
  user's own refused triple returns to the host — but a host that ignores proposals loses it (the amendment's §7).
  **The first visible symptom:** the agent not knowing something the user said.
- **Reversible?** Refusal stores nothing, so nothing is recoverable from the store; the evidence is the episode and
  the count. A confirmed inference is an ordinary edge, retirable by the existing verbs.
- **Attack surface:** reduced — model-derived attributes no longer reach the store unless a person affirms them.

---

## 8. Claims and limits

**Claimed:** that an attribute the user never stated is not written as though they had; that where the product
stores a derivation, it is one the person confirmed, and it is marked so; and that grounding is never declared by the
model.

**NOT claimed:**
- **that we can always tell.** §4a's attestation test is unresolved for declarative objects; a weak test will mark
  some stated facts inferred. *That direction is the safe one, and it is still a cost — paid in proposals, or in
  loss where no host surfaces them.*
- **that query-time derivation is restricted.** It is not, by design (§4b).
- **anything about episodes** (§4b).

---

## 9. Brief for the external reviewer — ROUND 1

**The question this round asks: what is the attestation test for a DECLARATIVE fact?**
The procedural gate demands a verbatim span; a declarative object is normally a
normalised value, so the same gate would refuse most legitimate extraction. *Our reading
is that attestation must bind the fact's TERMS to the event text — subject and object
tokens present, relation from the declared vocabulary — while allowing the object to be
normalised; but that test admits an inference whose terms happen to appear, and we would
rather have the weakness named than argue it away.*

- **Least sure of:** (1) the test above; (2) whether `confirmed` should render differently from `stated` at all once
  a person has affirmed it (we say yes: the system's proposal is part of the record's history); (3) whether the
  widened predicate should apply to non-USER events at all, where it only refuses.
- **Where we may have overstated:** §1c's claim that the widening is “0019's predicate, wider” — a terms test may be
  a different predicate in kind, not in width.
- **What would change our minds:** a measured false-positive rate for a terms test high enough that refusal costs
  more than the uninvited inference it prevents.
- **What we are NOT asking:** whether to build the axis (ruled), or whether a confirmation path exists (ruled, Q2).
- **Reviewer-safe copy:** nothing generalised.

> 🔴 **A SENTENCE A SEALER CHECKS, not only an author — carried VERBATIM into this package's README and PIN:**
>
> **“The declarative grounding axis and the subject's right of reply CANNOT BE ACCEPTED INDEPENDENTLY. The
> composition rule — the cells where a fact is `inferred` or `confirmed` AND `disputed` — needs both documents. They
> may be REVIEWED in either order; accepting one without the other accepts half of a rule.”**

---

## 10. Open questions

| # | question | who decides | by when | class |
|---|---|---|---|---|
| Q2 | Is a confirmation path for an inferred attribute intended? **RESOLVED 2026-10-10: yes** (the owner); mechanism (A), the amendment | owner | — | resolved |
| G1 | The attestation test for declarative facts (§9) | external reviewer + dev | before acceptance | blocking |
| G2 | Whether the widened predicate applies to non-USER events (§9 (3)) | dev + external reviewer | before acceptance | blocking |

---

## Reviewer checklist

- [ ] §3 has no unanswered cells
- [ ] §3's classes were read from the enums, not copied from the template
- [ ] Prohibitions AND the corresponding **permissions** are both tested
- [ ] Every default fails **closed**
- [ ] §2c has a row per uncontrolled input, and **no empty invariant cell**
- [ ] §2c-ii: every claim about what is reachable carries **the command**
- [ ] Every §6 invariant has a check that actually runs, demonstrated RED against its mutant
- [ ] §10 questions each carry a class
- [ ] §8 states what this does *not* establish
- [ ] I have said where I think the **author's conclusion is wrong**, not only where the text is wrong
- [ ] I re-read the current version before reviewing, and I am quoting the version I approve
