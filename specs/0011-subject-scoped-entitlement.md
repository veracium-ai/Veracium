# Feature spec: subject-scoped entitlement

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — split out of `0003` on 2026-08-02, **after two external reviews
> showed the entitlement model is a larger design than the defect that motivated
> it.** `0003` narrows to the reported attack and ships; this owns the breadth.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v3** — internal round 1 folded (research, 2026-08-23, PASS WITH AMENDMENTS): **M-2/E-Q4 RULED YES** — the acting principal (`0020`) joins the E5 tuple as the fifth element, verified in-transaction (E5 authenticates CORRECTORS, not just corrections; S4 gains the replay-across-principals cell); **M-3** §4b keeps the NARROW refusal cell for v1 with a measurement RIDER (count refusal rows by cell post-ship; broad revisits on an operator's numbers — the E-Q1 pattern); **M-1** currency + references (0024 cited at its SPEC surface with the predicate-not-disposition statement for the A1 divergence; the S7 pointer fixed; sections renumbered §3a/§3b); minors m-4 (historical motivation marked), m-5 (symbol not line), m-6 (`derived(from_class)` closed domain, unknown fails to the THIRD_PARTY floor). Ratified untouched: E-Q2, E-Q3, the conservation argument, absence-as-positive-capability, S1–S7's shape, and research's purpose-scoping non-foreclosure lens (passes by construction). *Prior:* **v2** — the design (2026-08-22, authorized by Quentin's "Proceed with 0011"): E-Q2 and E-Q3 RULED (both dev-owned; derived-at-read and explicit threading — the accepted stack's own disciplines), E-Q1 dispatched to research with a decision frame and a provisional floor, the six inherited findings turned into §4's constructions and §6's invariants, and the open `M7-correct` finding adopted as this spec's motivating live defect. *Prior:* v1, the scope-holder from the `0003` split |
| **Status** | *see `Spec-Status:` — canonical.* Holds `0003`'s deferred scope. **Nothing here blocks `0003`.** |
| **Internal reviewers** | research — round 1 PASS WITH AMENDMENTS 2026-08-23 (3 moderates + 3 minors, both §9 questions answered, E-Q4 ruled), folded in v3; round 2 same-day |
| **External review** | required |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Why this is separate

**`0003` proposed a global author ladder. Two reviews established that the
ladder is right for user-self facts and overbroad for the graph** — a user
assertion should not erase sourced third-party evidence about another person or
an organisation.

**The fix `0003` v2 proposed does not work.** It derived subject class from the
relation registry, and **a relation cannot tell you whose fact it is**:
`Quentin works_as Acme` and `Alice works_as Acme` share a relation and belong to
different classes. Making it work needs subject identity, alias canonicalisation
and a total classifier — **a design, not an amendment.**

**At the time of the split (2026-08-02) the reported defect was unfixed
after two review rounds** — third-party content could still retire a user
fact (then `graph.py:139`). **So `0003` narrowed to that, and the breadth
landed here** rather than holding a guard hostage to an entitlement model.
(`0003` has since shipped, v0.6.0 — the sentence above is the historical
motivation, not a live defect; internal round 1, m-4.)

---

## 2. Scope inherited from `0003`'s reviews

| # | inherited finding | why it needs this spec |
|---|---|---|
| **E1** | subject class cannot come from the relation | needs `subject_class(user_id, subject, relation)`, canonical identity, alias handling, and an explicit default |
| **E2** | the authority matrix must be subject-aware | once subject class is load-bearing, the 400-row product stops being the decision procedure; the generated policy must take a subject dimension |
| **E3** | external-world contention has no current-value semantics | *"both stay active"* leaves a functional relation with no unique value; needs a **`CONTESTED`** relation state every reader handles |
| **E4** | trusted ingress must be a capability | `derived_from=None` is safe only if absence was **positively established**; a persistence-site manifest cannot authenticate origin |
| **E5** | `correct()` and absorption under one authorised replacement | needs an unforgeable authorisation bound to *(store, prior, replacement, kind)* and checked inside the atomic operation |
| **E6** | a distinct history partition | `GROUNDED_CURRENT` / `UNVERIFIED_CURRENT` / `RETIRED_HISTORY`, so an inactive edge is never in a block whose meaning is *present grounded fact* |

**`0003` explicitly does not claim any of these.** Its §8 says so.

---

## 3. Why the narrow version does not make this harder

**Blocking is strictly conservative.** `0003` only ever **refuses** a retirement
it currently permits; it grants nothing and hides nothing. So every rule here
can be added later as a **further restriction or a widening of an existing
refusal**, without unwinding `0003`.

**The one thing `0003` fixes that this spec would otherwise inherit** is the
attack: after `0003`, no lower-authority edge retires a higher-authority one
through functional supersession. **This spec then decides who is entitled to
retire *what about whom*** — a different question, and one that is safe to leave
open while the deletion primitive is closed.

---

## 3a. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| the extractor's `subject` string | falsy → dropped by the shipped completeness check (`ingest.py`); whitespace → survives, strips to an empty claimant (the cell `0024` Q3 RULED conservative — its pinned tests return at 0024's landing; internal round 1, M-1: post-revert they are not on main) | truthy non-str → str()-converted by the shipped path | an entity ref this store has never seen → class **OTHER** (the default IS the conservative class) | text engineered to make the extractor emit `subject="user"` so a third-party fact rides the SELF class | **E1**: the classifier is TOTAL with OTHER as default; and SELF grants nothing to the *content* — it gates only which ENTITLEMENT rules apply to retirement, never disclosure (`0024` owns disclosure; **S7** states the non-interaction). **This spec consumes `0024`'s PREDICATE (§4a canonical subject), never its DISPOSITION** — amendment A1 (0024 v8) moves the disposition to uniform USE_ONLY and nothing here moves with it (M-1: stated so the divergence cannot read as drift) |
| the caller's `actor` on `correct()` | absent → the shipped default `"user"` — **the M7 defect's second face: a string DEFAULT is not an authorisation** | any string passes today | — | a tool-driven caller invoking `correct()` with `actor="user"` | **E5**: the authorisation capability is UNFORGEABLE and bound to *(store origin, prior id, replacement value, kind, **acting principal** — the `0020` element, internal round 1 M-2/E-Q4)* — a string names nobody, and without the principal ANY caller reaching `correct()` minted a valid capability: the binding closed forge/replay of a DIFFERENT correction, not an unauthorised caller minting a fresh one |
| the host's ingress declaration (`derived_from=None`) | absence is the TRUSTED claim today — safe only if positively established | — | — | a persistence-site caller replaying content with `derived_from` omitted | **E4**: absence must be a POSITIVE capability, not a missing argument |
| a second active value on a functional relation | — | — | — | an attacker holding one side of a contention to keep a stale value live | **E3**: `CONTESTED` is DERIVED at read (E-Q2 ruling) — no writer can pin it, no reader can miss it |

## 3b. The rulings (E-Q2, E-Q3) and the provisional floor (E-Q1)

- **E-Q2 — RULED (dev, 2026-08-22): `CONTESTED` is DERIVED at read, never
  stored.** A functional relation with two or more ACTIVE same-disclosure-
  class edges on one `(user_id, subject, relation)` IS contested; the state
  is a read-time property in the same family as `Edge.active`,
  `quarantined` and `assertable` — every one of which is derived precisely
  so no second writer can drift from the fact it restates (`0023` N2's
  single-writer sweep exists because stored duplicates of derivable facts
  rot). A stored member would need a writer at every mutation site that
  can create or resolve contention — an enumeration this repo has watched
  drift through twelve external rounds elsewhere.
- **E-Q3 — RULED (dev, 2026-08-22): `EvidenceContext` is an EXPLICIT
  constructor argument threaded through ingest.** Invasive and checkable
  beats ambient and neither: an explicit parameter is enumerable by the
  X7-style AST sweep (`0025`'s "no unvalidated path" form), while ambient
  context is invisible to exactly the structural checks this repo's gates
  are built from.
- **E-Q1 — RESOLVED for v1 (research's ruling + the measured count,
  2026-08-22): (c), the predicate floor — and the count says the floor may
  be the ceiling.** v1 SELF is the `0024` canonical-subject predicate —
  `str(subject).strip().casefold() == "user"` — one predicate, shared
  verbatim with an accepted consumer. **An identity RELATION is REJECTED
  blocking-grade** (research): it would make the entitlement gate's input
  writable by the machinery the gate governs — supersession could rewrite
  who "the user" is, and a poisoned extraction could assert identity to
  acquire entitlement. Identity that gates anything must be
  HOST-ATTESTED; content-derived identity is the injection surface the
  ingest ladder closed. The named extension point, if a real operator
  ever needs it, is (a)-shaped: a host-declared alias set,
  boundary-validated, frozen per event — the registry pattern — arriving
  through its own review round, never a config flag. **The deciding
  count, run over the 183,417-triple corpus (2026-08-22):** predicate
  passes 72,253 (39.4%); predicate-failing subjects plausibly denoting
  the user: 305 = **0.166%** — and the hand-classified distinct-string
  table shows most are correctly OTHER (possessives: "user's mom",
  "user's sister"; work topics: "User interviews", "end user"); the
  genuinely self-denoting rows (`me`, `I`, `[User]`) total ≈30 triples ≈
  **0.016%** — HAND-CLASSIFIED from the recorded distinct-string table,
  not a regex verdict: the raw regex family said 305, a 10× overstatement
  ("user's mom" denotes the mom), so a future reader re-derives the
  figure from the table rather than trusting it (the
  classify-from-artifacts rule, earning its keep on a live design
  decision). The floor costs nothing real, and the alias set has no
  measured constituency yet.

## 4. Behaviour — the constructions

### 4a. The classifier (E1)

`subject_class(user_id, subject) -> SELF | OTHER` — TOTAL, with **OTHER
the default**: SELF iff the canonical subject equals the user under the
`0024` predicate (§3b's floor; research's E-Q1 answer widens it behind the
same interface). The classifier consumes the STORED subject — the
str()-converted, stripped slot with a stated contract — never the note,
never the relation (§1: a relation cannot tell you whose fact it is).

### 4b. The subject-aware entitlement rule (E2)

The `0003` ladder (`authority.py`, `supersession-authority-v1`) remains
the AUTHOR axis; this spec adds the SUBJECT axis as a REFUSAL widening
only (§3's conservation argument): a retirement permitted by the author
ladder is additionally refused when `subject_class(prior) == OTHER` and
the incoming edge's sole authority is the user's self-assertion — a user
statement about themselves cannot retire sourced evidence about someone
else. The generated policy gains the subject dimension; the 400-row
author product stops being the whole decision procedure, and the refusal
lands as a `supersession_refusals` row exactly like the ladder's own
(same carrier, `rule_version` bumped — no new table).

**The narrowness is v1's, held with a MEASUREMENT RIDER (internal round
1, M-3 ruling):** "sole authority is self-assertion" closes the reviewed
attack without pushing routine user corrections of their own third-party
entries into authorisation friction — and the broad form ("ANY
user-authored retirement of an OTHER-subject sourced fact refuses
pending confirmation") has no measured constituency. The rider is a
design obligation, not a hope: the §4b refusal rows are COUNTED BY CELL
post-release, and the broad form is revisited on an operator's numbers,
never by taste — the E-Q1 pattern applied to this spec's own knob.

### 4c. `CONTESTED` at every reader (E3, per the E-Q2 ruling)

Derived: `contested(user_id, subject, relation)` is true while a
functional relation holds ≥2 active same-class edges. Readers handle it
the way they handle `needs_confirmation` — recall labels the value set
as contested rather than choosing one; the gate treats a contested
functional value as non-assertable-as-current (assert the CONTENTION,
never one side); `maintain` neither resolves nor consolidates across a
contested pair. Resolution happens only through the entitled paths:
supersession by an entitled author, `correct()` under E5, or `confirm()`.

### 4d. Trusted ingress as a capability (E4)

`derived_from=None` stops being trusted-by-omission: `ingest_event`
gains an explicit `EvidenceContext` (E-Q3: a constructor argument)
carrying the host's POSITIVE declaration — `direct` (the host attests
first-party capture) or `derived(from_class)`. **`from_class` is a
CLOSED domain, validated at construction (internal round 1, m-6 — the
week's validator lesson): an enum the constructor refuses unknowns of;
an unknown or malformed value fails CLOSED to the `derived(THIRD_PARTY)`
floor, never open.** Absence of the context is
the conservative cell: treated as `derived(THIRD_PARTY)`, never as
direct. The context is a value object the persistence site cannot mint
implicitly; hosts that never construct one get exactly today's
worst-case flooring, so the change is refusal-conservative.

### 4e. `correct()` through the ladder, authorised (E5 — closes `M7-correct`)

The live defect (`findings.py M7-correct`, at the symbol `Memory.correct` — cited by name, not line; internal round 1, m-5):
`correct()` calls `invalidate_edge` + `add_edge` directly — no ladder, no
receipt, no refusal record, and `actor` is an unauthenticated string
defaulting to `"user"`. The construction: `correct()` builds a
replacement edge and submits it through `apply_supersession`'s atomic
plan machinery with a **`CorrectionAuthorisation`** bound to
*(store origin, prior edge id, replacement value digest, kind, **acting
principal**)* — the fifth element is `0020`'s principal (internal round
1, M-2/E-Q4 RULED YES): E5 as a four-tuple authenticated CORRECTIONS but
not CORRECTORS — `Memory.correct` mints the authorisation itself on the
interactive path, so any caller who reached it obtained a valid
capability, and the §3a adversarial cell was closed only against
forge/replay of a different correction. With the principal bound and
verified INSIDE the transaction like the rest (the `0014`
snapshot-verification shape): hosts can scope `correct()` per-principal
with the STORE enforcing consistency, the receipt row records WHO, a
forged, replayed, rebound, or cross-principal-replayed authorisation
aborts, and the subject-entitlement rule of §4b applies to corrections
exactly as to extractor-driven supersession. `record_outcome` stays
fact-untouching.

### 4f. The history partition (E6)

Derived labels over existing fields — no new storage:
`GROUNDED_CURRENT` (active, not ungrounded, assertable),
`UNVERIFIED_CURRENT` (active but ungrounded / use-only / contested),
`RETIRED_HISTORY` (inactive, any reason). Readers that today interleave
history with present fact (`compile`, `introspect`) partition their
output by these labels so an inactive edge is never rendered inside a
block whose meaning is *present grounded fact*.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| a store with only user-self facts | byte-identical decisions — SELF-on-SELF entitlement is today's ladder |
| third-party/org facts, no contention | unchanged until a USER self-assertion attempts to retire an OTHER-subject sourced fact — then a NEW refusal row |
| a functional relation in genuine contention | today: silent both-active; after: derived `CONTESTED` at every reader, gate asserts the contention |
| existing `correct()` callers | same signature; the authorisation is minted by `Memory.correct` itself for the interactive path — the CHANGE is that tool-driven and replayed invocations can no longer forge it |
| hosts that never construct `EvidenceContext` | floored at `derived(THIRD_PARTY)` — strictly more conservative than today |

## 6. Invariants and executable checks — REQUIRED, blocking

| # | invariant | check |
|---|---|---|
| **S1** | `subject_class` is TOTAL with OTHER as default — every subject string classifies, and only the canonical-predicate cell is SELF | `test_subject_class_is_total` — property test over adversarial strings, the `0024` predicate cells included |
| **S2** | a USER self-assertion never retires an OTHER-subject sourced fact; the refusal lands as a `supersession_refusals` row | `test_self_assertion_cannot_retire_other_subject` — the E2 cell, plus the refusal-row assertion |
| **S3** | `CONTESTED` is derived — NO stored carrier exists, and every reader (recall, gate, maintain) handles the contested cell | `test_contested_is_derived_and_total_over_readers` — an AST sweep for stored writes plus per-reader behaviour cells |
| **S4** | `correct()` reaches storage ONLY through the atomic plan machinery with a verified `CorrectionAuthorisation`; a forged, replayed, unbound, or **cross-principal** authorisation aborts inside the transaction (M-2: a capability minted under one principal replayed under another is the named new cell) | `test_correct_requires_bound_authorisation` — the M7 regression, forge/replay/rebind cells **+ the replay-across-principals cell** |
| **S5** | absent `EvidenceContext` floors at `derived(THIRD_PARTY)` — absence is never the trusted cell — **and so does an unknown or malformed `from_class` (m-6): the domain is closed; validators refuse the unknown, not just cover the known** | `test_absent_context_floors_conservative` — plus the unknown-value cell |
| **S6** | the partition labels are derived and total — every edge lands in exactly one of the three | `test_history_partition_is_total` — enumeration over the field product |
| **S7** | disclosure is UNTOUCHED — no rule here reads or writes `Provenance.disclosure` (the `0024`/`0025` pipeline owns it) | `test_no_disclosure_interaction` — the N2-style single-writer sweep extended, not duplicated |

## 7. Failure modes and reversibility

- **Too-narrow SELF** (the literal predicate misses aliased self-facts):
  the OTHER default refuses more retirements than intended — costs
  convenience, never integrity. Research's E-Q1 widening recovers it.
- **Too-broad SELF** would be the dangerous direction; S1's property test
  and the single-predicate discipline (shared with `0024`) bound it.
- **Reversibility:** every rule is a refusal-widening or a derived read
  label; reverting restores today's behaviour with no stored state to
  unwind. The `CorrectionAuthorisation` and receipt rows are additive.

## 7a. Surfaces touched

| carrier | change |
|---|---|
| `src/veracium/authority.py` | the subject dimension in the generated policy; `rule_version` bump |
| `src/veracium/graph.py` | the §4b refusal cell in plan building; contested derivation |
| `src/veracium/__init__.py` (`correct`) | routed through the plan machinery with the bound authorisation |
| `src/veracium/ingest.py` | the explicit `EvidenceContext` parameter (E-Q3) |
| `src/veracium/compile.py` / `gate.py` / `introspect.py` | contested handling + the §4f partition labels |
| tests | the §6 table's named tests — §6 is the ONE authoritative list |

## 8. Claims and limits

This spec decides who may retire what about whom, and nothing else. It
does not touch disclosure (`0024`/`0025` own the trust pipeline), does
not resolve contention (it makes contention VISIBLE and gates its
resolution paths), and grants no new authority to anyone — every rule is
a refusal that does not exist today or a label over facts already
stored.

## 9. Brief for the internal reviewer

1. **The E-Q2 ruling** — derived-at-read rests on the single-writer
   discipline; if you think a stored member with enumerated writers is
   safer, that reverses three accepted precedents and we should argue it
   before design review.
2. **The E5 binding** — RULED at internal round 1 (M-2/E-Q4): the
   acting principal IS the fifth element. Kept here for the external
   reviewer: attack the in-transaction verification and the
   cross-principal replay cell.
3. **The §4b refusal cell** — RULED at internal round 1 (M-3): narrow
   for v1, with the measurement rider in §4b. For the external reviewer:
   attack the rider's cell taxonomy — are refusal rows countable by the
   cells an operator would actually decide from?

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| **E-Q1** | How is the user's own subject identity canonicalised? | **RESOLVED for v1 (2026-08-22)** — the predicate floor ships; the identity-relation option rejected blocking-grade; the alias-set extension point named and priced at ≈0.016% measured constituency (§3b) | research + dev, jointly | — |
| **E-Q4** | should the E5 authorisation tuple carry the acting principal (`0020`) as a fifth element? | **RESOLVED (internal round 1, 2026-08-23): YES** — E5 as drafted bound the arguments, not the actor; under `0020` the principal IS what distinguishes callers. Fifth element, verified in-transaction, receipt records WHO, S4 gains the cross-principal replay cell (§4e) | dev + internal review | — |
