# Feature spec: the subject's right of reply — the record stands, and the reply travels with it

Spec-Status: draft

| | |
|---|---|
| **Author / session** | research (veracium-research-48), the candidate's author → dev (veracium-2b), adopted at rest and re-read from the file: v1.2 2026-09-20 from `0047-subject-reply-CANDIDATE.md` (sha16 e8daf82c70cb4031); v1.3 2026-10-10 from `0047-subject-reply-CANDIDATE.md` (sha16 c5f61f2972e97a58) |
| **Version** | **v1.3 — 2026-10-10: the owner's answer folded, the carrier settled, the §5 grid aligned with 0045's third value, and the document restructured into the template's sections.** Base: the tree's adopted copy at `4ea1ce5` (v1.2); the Author and Number cells are dev's and are carried verbatim. 🔴 **The owner, 2026-10-10 (first-hand in the dev session, relayed by dev):** *“I agree that the person a fact is about should be able to attach a reply to it. If implementing this requires amending accepted spec 0041 then let's do it but if there's a better way to implement it let me know.”* **Research's answer, recorded in §1c: there is no better way — the amendment is intrinsic, not a cost of choosing a table:** a reply holds the person's own words ABOUT a fact, those words routinely restate it, and so ANY carrier of a reply must be treated by 0041 when its edge is redacted; a reply-as-edge would need a cross-edge cascade 0041 does not have. **The carrier is the table, with §0's amendment.** 🔴 **0045 now has a third grounding value, `confirmed`** (the owner's Q2 = yes, and mechanism (A)), **so §4c's grid gains a row**, and the cell a v1.2 reviewer could not evaluate is written. 🔴 **v1.2 contradicted itself on §0a:** its §0a said research leans *refuse*, its brief said research's reading was the conditional third; **§0a now states one position (§9).** **Two dependencies are stated rather than discovered:** *“subject-authored”* is enforceable only on the caller's label until authenticated principals (research's 0050) exist; and 0047's reply kind `disputed` is NOT `Memory.dispute()` (§1d). **And a mechanism corrected on dev's carrier read:** §4c's *“the latest subject act decides … by construction”* relied on `confirm()` refusing a disputed edge, and `confirm()` checks only the edge's own `assertable` property, which reads no reply; **a named refusal now carries it (INV-R13).** **Corrected citation:** the 0041 sentence §0 answers sits at 0041 L220, in the preamble's record of dev's sweep, not in a section numbered §3. Prior: v1.2 · v1.1 (the joint candidate's Part B). |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line at the top* |
| **Internal reviewers** | research (author) · dev |
| **External review** | **required** — it adds a CONTENT-CARRYING table and amends an accepted spec's enumeration. |
| **Decision + date** | **The reply is wanted, and amending 0041 is accepted if required: the owner, 2026-10-10.** Acceptance: pending the external round. |
| **Path** | **full** |
| **Number** | 0047 — from `allocation.py --next` at adoption, 2026-09-20. |
| **Predecessor** | the joint candidate's v1.1 Part B — that half is now the declarative grounding axis, adopted as **0045**. *(Cited by NUMBER rather than by filename: v1.1 named the sibling's file, the file was renamed to its allocated stem, and the reference dangled.)* **Travels with** 0045 and the 0019 §4c amendment in one package. |

---

## 0. 🔴 THE FIRST SECTION IS AN AMENDMENT TO ACCEPTED 0041, BECAUSE A NEW COLUMN MUST ANSWER IT

**0041 (accepted) states, at L220: “No other TEXT/BLOB column carries content.”** *A reply table is exactly such a
column, so this spec cannot be shipped beside that sentence — it lands WITH an amendment of it, or it does not land.*
The sentence is enforced by a census, not by prose: `test_the_carrier_enumeration_reproduces_its_committed_output_byte_for_byte`
goes red the moment a new content column exists (§2c-ii row 2).

> **That sentence was written as an ENUMERATION CLAIM precisely so a new column would have
> to answer it.** *It is the census-that-refuses-on-change working as designed. The obligation is the feature, not an
> obstacle to it.*

**What the amendment carries, in the shape 0041 already uses for side rows** *(the shape of
`confirmations.request_digest` and the refusal rows' copied `relation` in `SIDE_TABLE_TREATMENTS`)*:

| | |
|---|---|
| **the treatment map** | gains a row: **`replies.text` → REPLACE with the marker**, the ROW KEPT so append-only survives, the closed `kind` PRESERVED. 🔴 *It is the first side-table column in the map that holds FREE TEXT — every existing side row holds a digest, a closed value or an id — and the review should see that said plainly.* |
| **when** | in the SAME transaction as the edge's redaction, with the attestation record naming it |
| **the carriers** | one line in the store's `SIDE_TABLE_TREATMENTS`, one in the receipt, and the enumeration's committed output moves by this model's carriers |
| **export / import** | the redaction-era precedent exactly: a `reply` record line under a conditional stamp, older readers refuse. 🔴 **On import, a reply for an edge the destination does not hold REFUSES THE WHOLE FILE BEFORE ANY WRITE** — not a flag, an atomic refusal |
| **`doctor`** | one more `refs` row for the orphan check |
| 🔴 **the `kind` is closed only if something REFUSES** | 0041 §2d-iv: a closed set is closed **at the WRITE path or not at all**. **The reply writer refuses a `kind` outside the set** |
| 🔴 **INV-11's MIRROR binds the reply writer** | a NON-redaction write may not introduce the marker, **so a marker-carrying reply is refused at write AND at import** |
| 🔴 **the map must be TOTAL over the table** | the reply's other columns — ids, the actor field, timestamps — are **PRESERVE** rows and are listed as such |
| **0012** | the reserve rule every rendered class has — an unbounded reply cannot crowd the block it is attached to |

**Landing:** the amendment's text lives in this spec and becomes part of 0041 only on this spec's acceptance (the
rule agreed for Package I: an accepted spec is IMPLEMENTABLE, so unreviewed text does not enter it at the pin).

## 0a. 🔴 THE DECISION THIS ROUND MUST MAKE: a reply written AFTER its edge is redacted

| | |
|---|---|
| **refuse it** | the edge is a tombstone, and words attached to a tombstone would make the reply table the content channel INV-6 fences |
| **admit it, and make the reply itself a redaction target** | `redact(reply_id=…)` as a third target kind |

> **A third reading the binary hides:** 0041 lets a redaction DISCLOSE THAT A RECORD EXISTED. Where existence remains
> disclosable, there IS something to reply to — *“you are telling people a record about my medication existed; I never
> said that”* — and a flat refusal silences the subject where the system is still speaking about them.
>
> **And the consequence, which is the argument against it:** the row exists structurally after redaction and `why`
> renders `redacted`, so a reply COULD be attached to the id — **but no surface that speaks to the MODEL renders a
> tombstone.** Recall, the wiki and the contested groups all exclude it by the attestation record. *So a post-redaction
> reply would be rendered nowhere but the biography: the subject answers, durably, to an audience of the operator.*

**Research's position (one position — v1.2 stated two):** **refuse**, with the third reading named as the case
against. The conditional form collapses, on inspection, to *“admit a reply that lives only in `why`”*, and an answer
only the operator can read is not the right of reply this spec gives. **The round may choose otherwise; §9 asks.**

---

## 1. Problem and motivation

### 1a. What it answers

LINDDUN lists *“let me be able to deny I said that”* as a first-class requirement. **Veracium is built to defeat that
sentence** — durable attribution is the product, and an enterprise buyer is paying for exactly what a data subject may
not want. The owner's ruling (`A8`) names the tension publicly **and** builds the counterweight.

> 🔴 **THE SHAPE OF THE COUNTERWEIGHT: the record stands, and the reply travels with it.** *We do not resolve the
> tension by weakening attribution — that would sell the product's premise to answer a critique of it. We resolve it
> by making the subject's answer as durable as the claim, and by refusing to let the claim be rendered without it.*

### 1b. What it deliberately does NOT give

- **not deletion** — that is 0041's targeted redaction, a different right with a different ruling
- **not supersession** — a dispute is not a correction; *a subject saying “that's wrong” and the record being wrong
  are different facts, and merging them would let a reply silently rewrite history*
- **not removal from an audit trail** — the enterprise premise survives this feature or the feature is dishonest

### 1c. Why a table, and why the 0041 amendment is intrinsic (the owner's “better way” question)

**A reply holds the subject's own words about a fact, and those words routinely RESTATE it** — *“I never took
sertraline.”* Redact the edge, and a surviving reply re-publishes what was redacted. **So whatever carries the reply,
redacting the target must treat the reply in the same transaction — which is 0041's job, so 0041 must say so.**

| carrier | does it avoid amending 0041? | what else it costs |
|---|---|---|
| 🔴 **a table + one treatment row** *(chosen)* | no — one REPLACE row in the shape 0041 already uses | the first free-text side column (§0) |
| **a reply as an EDGE** pointing at its target | **no — worse:** redacting an edge treats its own carriers and its side rows, and there is **no edge→edge cascade** (§2c-ii row 1). A reply-edge would outlive its redacted target as an independent fact carrying the redacted content; preventing that is a cascade amendment, larger than one row | a reply becomes a FACT: recalled as one, superseded (0044's defect), decayed, consolidated |
| **text inside the edge** (an annotation field) | — | edits the record: breaks append-only and §4a's *“effect on the edge: NONE”* |
| **host-side replies, a digest in the store** | yes | the store can no longer render the reply beside the claim, so §4c's gate becomes the host's promise, and export loses the reply |
| **a reply as an EPISODE** | no — still needs a link and the cascade | episodes feed ingest and consolidation: the reply would be extracted into facts |

**So, to the owner's question: there is no better way.** The amendment follows from “the person a fact is about can
attach their words to it”, and the table makes it one treatment-map row.

### 1d. 🔴 Two names this spec must not be confused with

- **`Memory.dispute()`** (shipped) **RETIRES** an edge — reason `disputed`, *“the host revoked its trust”*
  (`DISPOSITIONED_REASONS`, §2c-ii row 5). **A reply of kind `disputed` retires NOTHING** (INV-R1). *Same word,
  opposite effect on the record; §9 asks whether the kind should be renamed.*
- **0003's “contested” facts** are functional facts with refused challengers. A replied-to fact is not contested in
  that sense.

---

## 2. Field contracts touched

| field / site | read / written | its documented contract | preserved? |
|---|---|---|---|
| `replies` *(new table)*: `id`, `user_id`, `edge_id`, `kind` ∈ {`disputed`, `context`, `withdrawn-consent`}, `text`, `actor`, `written_at` | written by the reply verb; read by render, `why`, `doctor`, export | — | new; append-only (INV-R2) |
| 0041's enumeration claim (L220) and `SIDE_TABLE_TREATMENTS` (`redaction.py` L99) | read by the census test | no other TEXT/BLOB column carries content | **Amended (§0)** |
| the render of an edge (0012's classes) | reads | an edge renders in its partition | **Qualified (§4c):** a `disputed` reply renders beside its edge, or the edge does not render as assertable |
| 0045's derived grounding | read | `stated` · `confirmed` · `inferred` | read only |
| `doctor`'s `refs` check | reads | dangling references are reported | **Gains** the orphan-reply row (INV-R5) |
| portability (export / import) | writes / reads | the record lines and their stamps | **Gains** a `reply` line under a conditional stamp (§0) |
| `store.confirm_edge` (0008's confirmation path, `store/sqlite.py` L670–L690) | reads | *“Only assertable facts can be confirmed”* (0008), enforced as `if not edge.assertable` (L684) | **Gains one refusal:** an edge carrying a `disputed` reply is refused at a new named site (§4c, INV-R13). 0008's sentence is preserved in meaning: under this spec such an edge is not assertable at the gate, and the store's check now says so |

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| **the reply text** — the subject's own words, open domain | refused (a reply says something) | n/a — text | n/a | **a marker-carrying text** → refused at write and at import (INV-11's mirror); **unbounded text** → bounded by the render reserve | **INV-R7**, **INV-R6** |
| **the reply `kind`** | refused | refused | **a value outside the closed set → refused at the write path** | — | **INV-R8** |
| **the target `edge_id`** | refused | refused | an edge that does not exist for that user → refused | **a redacted edge** → refused (§0a's position) | **INV-R9** |
| 🔴 **who wrote it** — the `actor` the caller supplies | refused | refused | outside the closed set → refused | **an assistant-authored reply LABELLED as the subject's is NOT detected**: the store enforces the label, not the person, until authenticated principals exist (research's 0050). *Enforced today: a reply labelled assistant or extractor is refused, and the verb is not reachable by the model (§3b)* | **INV-R2**, **INV-R10** |
| **an import file** | — | the existing import refusals | — | a reply for an edge the destination does not hold → the whole file refused before any write | **INV-R11** |

### 2c-ii. Assertions about reach — REQUIRED

Commands run from the repository root at `4ea1ce5` (research, CPython 3.14.7, 2026-10-10).

| # | assertion | command | result |
|---|---|---|---|
| 1 | redacting an edge treats its own side rows, and no other edge | `grep -n "^SIDE_TABLE_TREATMENTS" -A4 src/veracium/redaction.py` | READ: L99–L102 — `confirmations.request_digest`, `contribution_ledger` ×2, `supersession_refusals.relation`, `edge_embedding`, `source_revocations.reason`; no edge→edge row |
| 2 | 0041's content-column claim, and the census that enforces it | `grep -n "No other TEXT/BLOB column carries content" specs/0041-targeted-redaction.md; grep -n "def test_the_carrier_enumeration_reproduces_its_committed_output_byte_for_byte" tests/test_0041_evidence.py` | READ: L220 · L75 |
| 3 | no reply table exists today | `grep -rn --include="*.py" -e "CREATE TABLE replies" src/; echo "exit $?"` | EXECUTED: `exit 1` (no match) |
| 4 | `confirmations` holds no free text | `grep -n '_COLS = ("id, user_id, edge_id, confirmed_at, actor, call_path, "' -A1 src/veracium/store/sqlite.py` | READ: L672–L673, and the same columns at L768–L769 (the second writer) — ids, timestamps, closed enums, a correlation id, a digest |
| 5 | `dispute()` retires, and is not an MCP tool | `grep -n '"disputed": "drop"' src/veracium/schema.py; grep -n "Not exposed over MCP (an agent-callable suppress verb" src/veracium/__init__.py` | READ: L578 · L1843 |
| 6 | `confirm()` checks only the edge's own `assertable` property, which reads no reply | `grep -n "if not edge.assertable:" src/veracium/store/sqlite.py; grep -n "def assertable(self) -> bool:" src/veracium/schema.py` | READ: L684 · L828 (`Edge.assertable`; the second hit, L927, is `Episode`'s) — the edge property tests `active`, `quarantined`, `use_only`, `valid_now` only |

---

## 3. Trust-class matrix — REQUIRED, blocking

Classes from the enums at `4ea1ce5`: `EvidenceAuthor` = user, third_party, system, assistant; `Disclosure` =
mentionable, use_only, quarantined.

**The reply's AUTHOR:** the subject (or the user acting on their behalf) only. A reply labelled **assistant**,
**system** or **third_party** is refused (INV-R2) — enforced on the label until 0050 (§2c).

**The EDGE replied to, by its author and disclosure — what the reply changes:**

| edge's author | mentionable | use_only | quarantined |
|---|---|---|---|
| user · third_party · system · assistant | the edge is unchanged (INV-R1); a `disputed` reply qualifies its render per §4c | same | the edge is not assertable today; the reply is stored and shown in `why`; nothing becomes assertable |

- Can it make a **user-asserted fact non-assertable**? **Yes, in one cell:** a `confirmed` or `inferred` fact with a
  `disputed` reply (§4c). A `stated` fact stays assertable with its reply beside it.
- Can **non-user content gain user-grade authority**? **No.** A reply is not evidence for the fact; it never raises
  confidence, authority or disclosure.
- Can it **clear `needs_confirmation`**, or **merge, drop or overwrite provenance**? No (INV-R1).

**Write-time or maintain-time?** A write — of the reply, never of the edge.

## 3b. Authorization and scope — *full specs only*

- **The reply verb is HOST API ONLY**, not an MCP tool: *“never the extractor, never the assistant”* (§4a) is
  enforced first by reachability. *The posture of `confirm()` and `dispute()`.*
- **Scope:** per user. A reply attaches to an edge of the same `user_id`.
- **Who sees it:** every surface that renders its edge, under the edge's own disclosure. **Nothing becomes visible to
  a principal who could not see it before** — a reply rides with its edge and never renders without it.
- **Redaction:** the reply's text is treated with its edge's redaction (§0), in the same transaction.

---

## 4. Behaviour

### 4a. The carrier

| | |
|---|---|
| **what** | a **reply record** bound to an edge: the subject's own words, with a closed `kind` (**`disputed`** \| **`context`** \| **`withdrawn-consent`**) |
| **who** | the SUBJECT of the edge, or the user acting on their behalf — **never the extractor, never the assistant** |
| **effect on the edge** | 🔴 **NONE.** It does not retire, supersede, edit or delete. *0022's rule already governs this shape: “revocation retains every record”* |
| **shape** | **append-only.** A second reply does not replace the first; a reply is never edited, only added to |
| **effect on the AGENT** | §4c: a replied-to edge cannot be rendered without its reply |

### 4b. The carrier list a new content table owes (v1.1's C4)

| carrier | what it owes |
|---|---|
| **export / import** (0021, portability) | §0's `reply` line; the whole-file refusal for an orphan |
| 🔴 **0041** | §0's amendment |
| **0012** | a cap or reserve, like every rendered class (INV-R6) |
| **`veracium why` / `doctor`** | an orphan reply must be reachable and reportable (INV-R5) |

### 4c. 🔴 THE ONE SURFACE RULE — with 0045's three values

> **This rule reads 0045's grounding axis, and that dependency is stated rather than hidden:** neither document may be
> ACCEPTED without the other having been read; they may be reviewed in either order.

**Grounding and reply are separate carriers and ONE decision at the gate.** *(Only a `disputed` reply changes
assertability; `context` and `withdrawn-consent` render beside the edge and change nothing else.)*

| | **no `disputed` reply** | **a `disputed` reply** |
|---|---|---|
| **`stated`** | assertable — today's behaviour, unchanged | 🔴 **assertable ONLY WITH THE REPLY RENDERED BESIDE IT.** *The claim stands; the subject's answer travels with it. This is the whole of A8's counterweight* |
| **`confirmed`** *(0045 v1.4)* | **assertable as a CONFIRMED INFERENCE** — with its marker, never as a thing the person said | 🔴 **NOT ASSERTABLE.** *The person affirmed it and then disputed it; their latest word is the dispute, and what remains is the system's derivation. The reply and the earlier confirmation both render in `why`* |
| **`inferred`** *(legacy only, after 0045)* | **assertable ONLY AS AN INFERENCE**, with its marker | 🔴 **NOT ASSERTABLE.** *An unattested derivation that its own subject disputes has nothing left holding it up* |

**“The latest subject act decides” — made true by a REFUSAL, not by construction.** v1.3's first draft said it held
by construction because *“0008's `confirm()` refuses a non-assertable edge”*. **It does not do what that sentence
needed** (dev's carrier read): `confirm()`'s only assertability refusal is `if not edge.assertable` (§2c-ii row 6),
and `Edge.assertable` is a property of the EDGE alone — it reads no other table — while this grid's “NOT ASSERTABLE”
includes a reply in another table. *Two predicates shared one word.* So after confirm → `disputed` reply, a second
`confirm()` would be ACCEPTED, write a newer confirmation, and report success, while the grid still rendered the fact
not assertable: the subject's latest act would not decide, and the API would have said it did.

**The rule, with its mechanism:** 🔴 **`confirm()` REFUSES an edge that carries a `disputed` reply** — a new named
refusal site in the store's confirmation path (`store.confirm.disputed-by-subject`), in every grounding row, so a
confirmation can never post-date a dispute on the same edge (INV-R13). **The subject's way back is a NEW statement**
— `remember()`, which writes `stated` — or a `context` reply saying the dispute no longer stands. *No timestamp
comparison is needed, because the refusal keeps the order from ever arising.* `confirm_inference` (the 0019
amendment) writes a NEW edge, so it is unaffected.

**C5 — where the qualification sits.** *“Assertable only with the reply rendered beside it”* is **a render
qualification INSIDE the assertable partition, not a new class.** In 0012 §4c(iv)'s class order a reply rides with its
edge — it is not a class competing for budget. **Neither qualification may mask the other:** a rendering that shows
the reply and drops the grounding marker, or the reverse, **fails INV-R3 / INV-R12.**

---

## 5. Regime analysis — where does this behave differently?

| regime | behaviour |
|---|---|
| **no replies** | byte-identical to today |
| **`context` / `withdrawn-consent` replies** | rendered beside the edge; assertability unchanged |
| **`disputed` on `stated`** | assertable, with the reply |
| **`disputed` on `confirmed` / `inferred`** | not assertable; visible in `why` |
| **edge redacted after a reply** | the reply's text is REPLACED in the same transaction; the row and kind survive (INV-R4) |
| **reply attempted after redaction** | refused (§0a's position; the round decides) |
| **`confirm()` on an edge with a `disputed` reply** | refused at `store.confirm.disputed-by-subject` (INV-R13); the way back is `remember()` or a `context` reply |
| **import into an older reader** | refused by the conditional stamp |
| **MCP-only deployment** | no reply path (host API only) — §9 |

---

## 6. Invariants and executable checks — REQUIRED, blocking

| | invariant | check, and the MUTANT it must fail on |
|---|---|---|
| **INV-R1** | **A reply mutates nothing** | edge bytes identical before and after; the edge is neither retired nor superseded. **Mutant: let a reply set `invalidated_at` → FAILS** |
| **INV-R2** | **Append-only, subject-labelled** | a second reply adds; a reply labelled assistant, system or third_party is refused. **Mutant: allow an edit in place → FAILS** |
| **INV-R3** | 🔴 **A replied-to edge cannot be rendered without its reply** | render a `disputed` `stated` edge: the reply is beside it. **Mutant: drop the reply while keeping the edge → FAILS** |
| **INV-R4** | 🔴 **The reply survives its edge's redaction as a ROW and not as CONTENT** | redact the edge: `replies.text` carries the marker, the row is kept, `kind` preserved, the attestation names it. **Mutants: delete the row → append-only broken; keep the text → 0041's claim broken** |
| **INV-R5** | **An orphan reply is reachable and reportable** | `doctor`'s refs check lists it. **Mutant: silence it → FAILS** |
| **INV-R6** | **A reply is bounded in the render** | the reserve rule. **Mutant: unbounded text crowds the block → FAILS** |
| **INV-R7** | **INV-11's mirror binds the reply writer** | a marker-carrying reply is refused at write and at import. **Mutant: accept it → FAILS** |
| **INV-R8** | **`kind` is closed at the write path** | an out-of-set kind is refused. **Mutant: accept it → FAILS** |
| **INV-R9** | **A reply to a redacted or absent edge is refused** *(§0a's position)* | **Mutant: accept it → FAILS** |
| **INV-R10** | **The reply verb is not reachable over MCP** | the served tool list has no reply tool. **Mutant: register it → FAILS** |
| **INV-R11** | **An import with an orphan reply is refused whole, before any write** | **Mutant: import the rest and drop the orphan → FAILS** |
| **INV-R12** | **§4c's grid, all six cells** | a fixture per cell asserts assertability and the rendered reply/marker. **Mutant: treat `confirmed` + `disputed` as assertable → FAILS** |
| **INV-R13** | **A confirmation never post-dates a dispute on the same edge** | confirm → `disputed` reply → `confirm()` is REFUSED at `store.confirm.disputed-by-subject`, for a `stated`, a `confirmed` and an `inferred` edge; no confirmations row is written. **Mutant: drop the refusal → the second `confirm()` succeeds → FAILS** |

**Each check must be demonstrated RED against its mutant before acceptance.**

---

## 7. Failure modes and reversibility

- **Silent failure:** a render path that forgets the reply (INV-R3 is the guard), or a reply labelled as the subject's
  that the subject did not write (undetectable until 0050; §2c).
- **Reversible?** A reply is append-only and cannot be withdrawn by editing; the subject adds another. The edge is
  never touched, so there is nothing of the record to restore.
- **Partial failure:** the reply write and a redaction's treatment of it are single transactions.
- **Attack surface:** a new free-text table. Bounded by: host-only reachability (INV-R10), the marker mirror
  (INV-R7), the closed kind (INV-R8), the render reserve (INV-R6), and redaction's treatment (INV-R4).

---

## 8. Claims and limits

**Claimed:** that a subject's answer to a record about them is as durable as the record, travels wherever the record
is rendered, and survives the record's redaction as an attested row rather than as content.

**NOT claimed:**
- **not deniability.** *It does not let a person unsay something; it lets them answer, durably.*
- **not deletion, not supersession, not removal from an audit trail** (§1b).
- **not that the subject wrote it.** Until authenticated principals exist, the store enforces who the reply is
  LABELLED as, not who wrote it (§2c).
- **that the tension is resolved.** It is NAMED and answered. An enterprise buyer and a data subject still want
  opposite things, and the materials say so.

---

## 9. Brief for the external reviewer — ROUND 1

**The question this round asks: is the post-redaction reply refused, admitted as its own redaction target, or decided
CONDITIONALLY on whether that redaction still discloses the record's existence?** *Research's position is REFUSE
(§0a): the conditional form collapses to a reply only the operator can read. But a refusal silences the subject where
existence is still disclosed, and we would rather have that attacked than assume it.*

- **Least sure of:** (1) §0a; (2) whether `stated` + `disputed` should stay assertable-with-reply or become
  non-assertable until a human resolves it — *we chose assertable because non-assertable hands any subject a veto
  over any record about them, which an enterprise buyer cannot accept — we have not surveyed statute, and a reviewer who knows one that requires such a veto should say so*;
  (3) whether the reply kind `disputed` should be renamed, since `Memory.dispute()` retires an edge under the same
  word (§1d); (4) MCP-only deployments have no reply path.
- **Where we may have overstated:** §1c's table — tell us if a carrier we rejected avoids the 0041 amendment after
  all.
- **What would change our minds:** a reviewer-supplied carrier that keeps the reply beside the claim without a
  free-text side column.
- **What we are NOT asking:** whether the table needs 0041's amendment (§0, §1c), or whether to build the reply (the
  owner, 2026-10-10).
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
| R1 | §0a: the post-redaction reply | external reviewer + dev | before acceptance | blocking |
| R2 | rename the `disputed` kind (§1d) | dev + external reviewer | before acceptance | blocking |
| R3 | verified subject authorship | owner + dev | with 0050 | deferred |
| R4 | an MCP-surface reply path | owner + dev | after acceptance | deferred |

---

## Reviewer checklist

- [ ] §3 has no unanswered cells
- [ ] §3's classes were read from the enums, not copied from the template
- [ ] Prohibitions AND the corresponding **permissions** are both tested
- [ ] Every default fails **closed**
- [ ] §2c has a row per uncontrolled input, and **no empty invariant cell**
- [ ] §2c-ii: every claim about what is reachable carries **the command**
- [ ] Every §6 invariant has a check that actually runs, demonstrated RED against its mutant
- [ ] §3b: no principal can see anything they could not see before
- [ ] §10 questions each carry a class
- [ ] §8 states what this does *not* establish
- [ ] I have said where I think the **author's conclusion is wrong**, not only where the text is wrong
- [ ] I re-read the current version before reviewing, and I am quoting the version I approve
