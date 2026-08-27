# Feature spec: subject-scoped entitlement

Spec-Status: draft
Spec-Requires: 0003, 0005, 0006, 0008, 0012, 0014, 0015, 0016, 0020, 0023, 0024, 0025

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — split out of `0003` on 2026-08-02, **after two external reviews
> showed the entitlement model is a larger design than the defect that motivated
> it.** `0003` narrows to the reported attack and ships; this owns the breadth.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v7** — the ROUND-3 FOLD (2026-08-27; §13 maps every finding). R3-1: the predicate is defined over the AUTHORITY CHAIN via production `effective()`, so a marker carrying no authority cannot move the decision — the executable 240-cell policy matrix asserts the CLASS (equal authority decides equally), not the two named instances. R3-2: the measurement rider is WITHDRAWN — 0015 defers refusal counters to a consent discussion this spec cannot hold, so v1 ships with the constituency unmeasured and says so. CARRIER-R3-1: five more contradictions swept and the checker bound to the predicate's TRANSITIVE DEPENDENCIES, closing the helper-in-another-fence bypass. EVIDENCE-R3-1: `schema == 1` required, the predicate cross-checked against 0025 on the shared subset, and every figure labelled by what backs it — including the two that are RECORDED ONLY. *Prior:* **v6** — the ROUND-2 FOLD (2026-08-27; §12 maps every finding). R2-1: **`source_id` is no longer read by the entitlement decision at all** — `0006` says it may GROUP, never GRANT, and v5 made it a capability in both directions (omission stripped protection, a caller-supplied value bought retirement). The `sourced` term is GONE, the rule refuses on subject class + self-assertion alone, the narrowing is deferred to `0016`'s frozen carrier, and a source-identity INVARIANCE matrix is owed. R2-2: `would_refuse_broad` DELETED as constant-true; the rider adds no stored state, so §7's claim holds again. R2-3: contention is `0003`'s REFUSAL-scoped notion — the shipped one — not a second contract. CARRIER-R2-1: seven contradictory authoritative statements swept, and the checker rebuilt to bind each assertion to its NAMED ROW, with S6 compared count-to-count. EVIDENCE-R2-1: the census aggregate has a closed typed schema and is cross-checked against 0025's independently-derived artifact. *Prior:* **v5** — the ROUND-1 FOLD (2026-08-26; §11 maps every finding). R1-1: the entitlement rule is REPRESENTABLE — `sourced` and `self_assertion` defined as closed predicates over state that exists today, a TOTAL policy function replacing v4's condition (which omitted the sourced term and contradicted §3c), the over-inclusion named in the refusing direction, the withdrawn 'confirmation is a higher rung' phrase retired against 0008, the basis-aware form deferred to 0016 rather than unfreezing it, and the measurement rider made MEASURABLE (it could not have measured anything: the deciding population produces no refusal row). R1-2: E5 is an INTEGRITY BINDING, not authentication — the claim is withdrawn, `correct()` is a protected host API with the host's obligations stated. R1-3: contention requires ≥2 DISTINCT `_value_key` values (v4's rule was false against accepted 0012, executed). R1-4: one outcome for a malformed `from_class` — RAISES, no write — with the complete grammar. R1-5: a first-match precedence table, total and exclusive, and E6 re-motivated after its premise was measured false. PACKAGE-R1-1: the census is GENERATED and digest-bound; two unreproducible figures retired. *Prior:* **v4** — the pre-send audit (2026-08-24, dev; nothing from a reviewer — these are the findings this spec would otherwise have paid a round for): **`Spec-Requires` declared for the first time** (0003, 0014, 0020, 0023, 0024, 0025 — the F1 class 0024 paid a round-1 finding for: a spec that consumes another's mechanism must say so); §3a-ii **Assertions about reach** and §3c **Trust-class matrix** written, both REQUIRED by TEMPLATE and both absent; the §3a `0024` Q3 currency line corrected (it said the pinned tests were absent post-revert — true when research wrote it, stale within the day when 0024 landed as amended); the §9 brief addressed to the EXTERNAL reviewer with the internal rounds recorded; section order fixed to 3a → 3a-ii → 3b → 3c (internal M-1b). Every command in §3a-ii was RUN and its real output recorded. *Prior:* **v3** — internal round 1 folded (research, 2026-08-23, PASS WITH AMENDMENTS): **M-2/E-Q4 RULED YES** — the acting principal (`0020`) joins the E5 tuple as the fifth element, verified in-transaction (E5 authenticates CORRECTORS, not just corrections; S4 gains the replay-across-principals cell); **M-3** §4b keeps the NARROW refusal cell for v1 with a measurement RIDER (count refusal rows by cell post-ship; broad revisits on an operator's numbers — the E-Q1 pattern); **M-1** currency + references (0024 cited at its SPEC surface with the predicate-not-disposition statement for the A1 divergence; the S7 pointer fixed; sections renumbered §3a/§3b); minors m-4 (historical motivation marked), m-5 (symbol not line), m-6 (`derived(from_class)` closed domain, unknown fails to the THIRD_PARTY floor). Ratified untouched: E-Q2, E-Q3, the conservation argument, absence-as-positive-capability, S1–S7's shape, and research's purpose-scoping non-foreclosure lens (passes by construction). *Prior:* **v2** — the design (2026-08-22, authorized by Quentin's "Proceed with 0011"): E-Q2 and E-Q3 RULED (both dev-owned; derived-at-read and explicit threading — the accepted stack's own disciplines), E-Q1 dispatched to research with a decision frame and a provisional floor, the six inherited findings turned into §4's constructions and §6's invariants, and the open `M7-correct` finding adopted as this spec's motivating live defect. *Prior:* v1, the scope-holder from the `0003` split |
| **Status** | *see `Spec-Status:` — canonical.* Holds `0003`'s deferred scope. **Nothing here blocks `0003`.** |
| **Internal reviewers** | research — round 1 PASS WITH AMENDMENTS 2026-08-23 (3 moderates + 3 minors, both §9 questions answered, E-Q4 ruled), folded in v3; **round 2 PASS 2026-08-23 (diff-verified 83d84c9..36eb177, zero stale refs, no new findings) — READY FOR EXTERNAL, send at Quentin's discretion** |
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
| **E5** | `correct()` and absorption under one authorised replacement | needs a TAMPER-EVIDENT authorisation bound to *(store, prior, replacement, kind, principal)* and checked inside the atomic operation. NOT unforgeable and NOT authentication — see §4e: the principal is host-supplied and `correct()` mints the authorisation, so this binds INTEGRITY and ATTRIBUTION, and authenticating the corrector is the host's obligation (R1-2) |
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
| the extractor's `subject` string | falsy → dropped by the shipped completeness check (`ingest.py`); whitespace → survives, strips to an empty claimant (the cell `0024` Q3 RULED conservative, and its pinned tests are ON MAIN as of 2026-08-24, when 0024's mechanism landed as amended by A1 — the internal-round-1 note said they were absent post-revert, true when written and stale within the day; re-derived at packaging) | truthy non-str → str()-converted by the shipped path | an entity ref this store has never seen → class **OTHER** (the default IS the conservative class) | text engineered to make the extractor emit `subject="user"` so a third-party fact rides the SELF class | **E1**: the classifier is TOTAL with OTHER as default; and SELF grants nothing to the *content* — it gates only which ENTITLEMENT rules apply to retirement, never disclosure (`0024` owns disclosure; **S7** states the non-interaction). **This spec consumes `0024`'s PREDICATE (§4a canonical subject), never its DISPOSITION** — amendment A1 (ACCEPTED 2026-08-24, round 24) sets the disposition to uniform USE_ONLY and nothing here moves with it (M-1: stated so the divergence cannot read as drift; currency updated at A1's acceptance) |
| the caller's `actor` on `correct()` | absent → the shipped default `"user"` — **the M7 defect's second face: a string DEFAULT is not an authorisation** | any string passes today | — | a tool-driven caller invoking `correct()` with `actor="user"` | **E5**: the authorisation capability is TAMPER-EVIDENT (NOT unforgeable — R1-2/§4e: `correct()` mints it from caller-controlled values, so the host authenticates the principal) and bound to *(store origin, prior id, replacement value, kind, **acting principal** — the `0020` element, internal round 1 M-2/E-Q4)* — a string names nobody, and without the principal ANY caller reaching `correct()` minted a valid capability: the binding closed forge/replay of a DIFFERENT correction, not an unauthorised caller minting a fresh one |
| the host's ingress declaration (`derived_from=None`) | absence is the TRUSTED claim today — safe only if positively established | — | — | a persistence-site caller replaying content with `derived_from` omitted | **E4**: absence must be a POSITIVE capability, not a missing argument |
| a second active value on a functional relation | — | — | — | an attacker holding one side of a contention to keep a stale value live | **E3**: `CONTESTED` is DERIVED at read (E-Q2 ruling) — no writer can pin it, no reader can miss it |

### 3a-ii. Assertions about reach — REQUIRED

**Every command was RUN in this repository on 2026-08-24 and the result
column records its real output.**

| assertion | command | result (RUN 2026-08-24) |
|---|---|---|
| **`Memory.correct` bypasses the ladder entirely and its `actor` is an unauthenticated string** — the motivating defect (`findings.py M7-correct`), in the source | `python -c "import inspect, veracium; print(inspect.getsource(veracium.Memory.correct))"` | signature carries `actor: str = "user"`; the body's store calls are exactly `['add_edge', 'invalidate_edge']` — **no `apply_supersession`, no receipt** |
| **the `0003` ladder this spec extends is a GENERATED policy with a version id** (so §4b's subject dimension is a regeneration + bump, not a new table) | `python -c "from veracium import authority; print(authority.RULE_VERSION)"` | `supersession-authority-v1` |
| **the refusal carrier §4b lands rows in already exists** — no new table | `select name from sqlite_master where type='table'` on a fresh store | `supersession_refusals` PRESENT |
| **`subject_class` does not exist today** — E1 is a construction, not a rename | `python -c "import veracium.graph as g; print(hasattr(g,'subject_class'))"` | `False` |
| **`CONTESTED` has no stored carrier today** — E-Q2's derived-at-read ruling is not undoing an existing field | `python -c "from veracium.schema import Edge; print([f for f in Edge.model_fields if 'contest' in f])"` | `[]` |
| **the `0024` canonical-subject predicate this spec's SELF floor consumes is SHIPPED** (as amended by A1, landed 2026-08-24) | `grep 'casefold() == "user"' src/veracium/ingest.py` | present at the coherence test; the same `str → strip` canonical subject the write path stores |
| **`0020`'s principal — E5's fifth element — is a real binding target** on the read path this spec must compose with | `grep -rln principal src/veracium/*.py` | eight modules, `scope_read.py` being "the ONE place a read path asks 'may this principal…'" |

*(The first row is why this spec exists and why E5 is not a rename: a
correction today reaches storage through two direct store calls, so
there is no plan, no receipt, no refusal record and no authorisation to
verify — the subject-entitlement rule of §4b would have nothing to
attach to.)*

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
  through its own review round, never a config flag. **The deciding count, GENERATED (PACKAGE-R1-1):**
  `specs/evidence/0011/subject_census.py` over the cache pinned by
  sha256 `654e336a…`, with the counts-only aggregate and the
  distinct-string candidate table shipped beside it, so every figure
  below re-derives WITHOUT the corpus (`--aggregate` reproduces the run
  exactly).

  | | |
  |---|---|
  | triples | 183,417 — the same corpus and sha as 0025's census |
  | predicate passes | **72,253 = 39.4%** (`subject.strip().casefold() == "user"`) |
  | candidate rows | **337 = 0.184%**, over **94 distinct strings** |
  | classified SELF | **31 = 0.017%**, over 4 distinct strings (`me`, `I`, `[User]`, `the user`) |
  | classified OTHER | 306 — possessives ("user's mom", "user's sister"), work topics ("User interviews", "end user"), roles |

  **Round 1 retired two figures that could not be reproduced.** v4 said
  305 candidates = 0.166% and ≈30 self-denoting ≈0.016%. The
  load-bearing one — 72,253 / 39.4% — reproduces EXACTLY. The other two
  came from a regex family that was never recorded, so its exact set
  cannot be reconstructed; the script's candidate regex IS recorded and
  deliberately over-inclusive (its job is to bound what a human must
  read, not to decide anything), and it finds 337 rows over 94 strings.
  The conclusion is unchanged and marginally stronger: 0.017% rather
  than 0.016%.

  **WHAT THE ARCHIVE CAN CHECK, AND WHAT IT CANNOT (external round 3,
  EVIDENCE-R3-1).** Round 2 added a closed schema and manifest
  cross-checks, and the reviewer showed the DECIDING figures were still
  self-asserted: keeping the peer manifest and triple total but setting
  `schema = 999`, `predicate_passes = 0` and a one-row candidate table
  produced no findings. `schema` was typed and never valued. The
  validator now requires `schema == 1`, and each figure is labelled by
  what actually backs it:

  | figure | backing |
  |---|---|
  | cache manifest, entries, unparseable, 183,417 triples | **cross-checked** against 0025's aggregate — same cache, different script |
  | the PREDICATE itself, on the `third_party_claim` subset: 1,606 of 3,945 | **cross-checked** against 0025's independently-derived `subject_user`. It does not bind the whole-corpus count, but it proves this predicate IS 0025's, on 1,600+ real rows |
  | candidate rows (337), classified SELF (31) | **derived** from the shipped table — recomputable from the archive alone |
  | `predicate_passes` over the whole corpus (**72,253**), and the candidate table's COMPLETENESS | **RECORDED ONLY.** 0025 carries no whole-corpus subject data, so these reproduce with `--cache` on the measuring host and NOT from the archive alone |

  That last row is a limitation of this package, stated rather than
  papered over: a reader without the corpus is trusting dev for 72,253
  and for the claim that no candidate was omitted. The narrowing is the
  honest option the round offered, and the alternative — shipping a
  whole-corpus subject-frequency table — would put 12,000+ corpus
  strings in a public archive to bind one number.

  The classification stays a HUMAN judgement and is now auditable as
  one: `SELF_DENOTING` in the script lists the strings judged
  self-denoting, the candidate table ships every row that judgement was
  made over, and a reader who disagrees edits the set and watches the
  number move. A regex cannot make this call — it finds subjects
  MENTIONING the user, and most of those ("user's mom") correctly denote
  somebody else. Given names in the table are masked (`user's friend
  <name>`); the classification never depends on them.

  The floor costs nothing real, and the alias set has no measured
  constituency yet.

## 3c. Trust-class matrix — REQUIRED, blocking

**Scope:** the rows state what a RETIREMENT attempt is entitled to do;
disclosure is untouched throughout (**S7**), so no cell here moves a
trust class. `SELF`/`OTHER` are §4a's classifier output for the PRIOR
edge's subject; "sole authority is self-assertion" is §4b's narrow cell
as ruled at internal round 1.

| incoming author | prior subject class | prior evidence | today | after | why |
|---|---|---|---|---|---|
| USER (self-assertion) | **SELF** | any | retires by the ladder | **unchanged** | a user's own facts about themselves are exactly what the `0003` ladder is for |
| USER (sole authority: self-assertion) | **OTHER** | sourced third-party evidence | retires by the ladder | **REFUSED**, `supersession_refusals` row | the reviewed attack: a user statement erasing sourced evidence about someone else. §4b's cell, narrow by ruling, with the measurement rider |
| USER (with other authority — **NOT confirmation: `0008` grants it none, R1-1**) | OTHER | any | retires | **unchanged** | the refusal is scoped to SOLE self-assertion authority; other authority is the ladder's business |
| THIRD_PARTY / SYSTEM | any | any | per the ladder | **unchanged** | this spec adds no authority to anyone; it only refuses |
| any | OTHER | **no** sourced evidence (an unsourced OTHER-subject edge) | per the ladder | **REFUSED when the incoming edge is a bare user self-assertion — CHANGED at R2-1** | v5 keyed the refusal on displacing SOURCED evidence; `0006` forbids `source_id` from granting anything, so the distinction has no trustworthy carrier and the rule refuses on subject class + self-assertion alone. Deferred to `0016`'s frozen `evidence_basis` |
| any | any (functional relation, ≥2 active same-class **with ≥2 distinct `_value_key` values**) | silent both-active | **`CONTESTED` at every reader** (derived) | E3/E-Q2: visible, never resolved by this spec. Same-VALUE restatements are agreement, not contention — `0012` persists them deliberately (R1-3) |
| `correct()` caller | any | any | direct invalidate+add, unauthenticated | **through the plan machinery with a bound `CorrectionAuthorisation`** — the correction becomes TAMPER-EVIDENT and ATTRIBUTED, and a caller who names a principal they are not is STILL NOT STOPPED here (R1-2: `correct()` mints from caller-controlled values; authenticating the corrector is the host's obligation, §4e) | E5; the subject rule above applies to corrections exactly as to extractor-driven supersession |

**Nothing in this table grants a retirement that is refused today.**
Every changed cell is a refusal that does not exist yet, a derived label
over facts already stored, or a route through machinery that already
records what it does — which is the conservation argument §3 makes and
the reason this composes with `0003` without unwinding it.

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
ladder is additionally refused when the POLICY FUNCTION below returns
`REFUSE` — a user statement on their own authority cannot retire sourced
evidence about someone else.

**v4's condition was `subject_class(prior) == OTHER` AND "sole
authority", and it OMITTED the sourced predicate — contradicting §3c's
own unchanged row, which says the refusal keys on displacing SOURCED
evidence and not on subject class alone (external round 1, R1-1). Worse,
neither "sourced" nor "self-assertion" had a runtime predicate at all.
`self_assertion` is defined here over the AUTHORITY CHAIN; `sourced` was REMOVED at R2-1 and is not a term of this decision.**

```
self_assertion(e) := effective(author_of_evidence, derived_from)
                    == effective(USER, None)
                    # "the chain carries nothing but the user's own
                    #  authority", computed by 0003's own effective()

policy(incoming, prior) :=
    REFUSE   if  subject_class(prior) == OTHER
             and self_assertion(incoming)
    ALLOW    otherwise            # total by construction

# THE RULE READS NO source_id. That is the point, not an omission.
```

**THE PREDICATE IS DEFINED OVER THE AUTHORITY CHAIN, NOT OVER A MARKER'S
PRESENCE (external round 3, R3-1).** v6 said `derived_from is None`, and
`EvidenceContext.derived(USER)` is valid and reachable, so:

| incoming provenance | effective authority | v6 |
|---|---|---|
| `USER`, `derived_from=None` | 3 | REFUSE |
| `USER`, `derived_from=USER` | **3 — identical** | **ALLOW** |

A marker supplying no independent authority bought permission to retire an
OTHER-subject fact. That is the SAME DEFECT as R2-1 one field over, and
both were mine: each round replaced one unauthenticated marker with
another and inherited the class. **The common defect is keying on the
presence or absence of a marker instead of on authority**, so the
predicate now asks production `effective()` — 0003's own function —
whether the chain carries anything but the user. Enumerated against it,
exactly two chains qualify, and R3-1's cell is inside the refusal set BY
CONSTRUCTION rather than by patch.

**§6 acceptance surface — `specs/evidence/0011/policy_matrix.py`, 240
cells, executable.** It enumerates author × derived_from × subject class ×
source presence × origin and asserts: totality; the named R3-1 cell; the
GENERAL property that equal effective authority decides equally (which is
the class, not the instance); invariance under source identity and origin
(0006's GROUP-never-GRANT, proved rather than asserted); that
`derived_from` never RAISES authority; and that a SELF-subject prior is
never refused. Both defects that actually shipped were planted against it
and both are caught.

**The decision table, GENERATED from that matrix:**

| author | derived_from | effective | subject OTHER | subject SELF |
|---|---|---|---|---|
| `user` | `None` | 3 | **REFUSE** | ALLOW |
| `user` | `user` | 3 | **REFUSE** | ALLOW |
| `user` | `third_party` | 0 | **ALLOW** | ALLOW |
| `user` | `system` | 2 | **ALLOW** | ALLOW |
| `user` | `assistant` | 1 | **ALLOW** | ALLOW |
| `third_party` | `None` | 0 | **ALLOW** | ALLOW |
| `third_party` | `user` | 0 | **ALLOW** | ALLOW |
| `third_party` | `third_party` | 0 | **ALLOW** | ALLOW |
| `third_party` | `system` | 0 | **ALLOW** | ALLOW |
| `third_party` | `assistant` | 0 | **ALLOW** | ALLOW |
| `system` | `None` | 2 | **ALLOW** | ALLOW |
| `system` | `user` | 2 | **ALLOW** | ALLOW |
| `system` | `third_party` | 0 | **ALLOW** | ALLOW |
| `system` | `system` | 2 | **ALLOW** | ALLOW |
| `system` | `assistant` | 1 | **ALLOW** | ALLOW |
| `assistant` | `None` | 1 | **ALLOW** | ALLOW |
| `assistant` | `user` | 1 | **ALLOW** | ALLOW |
| `assistant` | `third_party` | 0 | **ALLOW** | ALLOW |
| `assistant` | `system` | 1 | **ALLOW** | ALLOW |
| `assistant` | `assistant` | 1 | **ALLOW** | ALLOW |

**The laundering cells, decided rather than defaulted (R3-1 asked).**
`derived_from` CAPS authority — it is a `min`, never a raise — so
`SYSTEM`/`ASSISTANT` evidence marked `derived_from=USER` keeps its own
class and is not the user's self-assertion. The matrix asserts both
halves: those cells are not self-assertions, and the marker does not
raise their authority. A lower class cannot launder upward through a
derivation marker, which is why they ALLOW here and the ladder decides.

**`sourced` IS GONE, AND `source_id` IS NOT READ ANYWHERE IN THIS
DECISION (external round 2, R2-1).** v5 defined both predicates from
`source_id` presence, and the reviewer executed what that bought:

| mutation | v5 outcome |
|---|---|
| sourced OTHER prior + plain USER assertion | REFUSE |
| omit the prior's `source_id` | **ALLOW** — omission removed the protection |
| add any `source_id` to the USER assertion | **ALLOW** — caller-supplied metadata granted permission |

Accepted `0006` says in four places that **`source_id` may GROUP, never
GRANT**: it is optional, host-supplied and DIAGNOSTIC, and its absence
must not relax a decision. v5 made it an entitlement capability in both
directions — omission stripped protection, and supplying a value bought
retirement permission. `0006` was not even declared as a prerequisite
while its carrier was being consumed to decide authority. That is the
whole finding, and the fix is not to read the field more carefully; it
is to STOP READING IT.

**What this costs, stated plainly.** The `sourced` qualifier was v5's
narrowness — the refusal keyed on displacing SOURCED evidence, so a
user correcting their own unsourced entries about another subject was
untouched. Without a trustworthy carrier for that distinction the
narrowing cannot be expressed, so the rule REFUSES MORE: any bare user
self-assertion retiring an OTHER-subject prior is refused, sourced or
not. A refusal is a recorded row and a confirmable path, never data
loss — but it is friction on a real workflow, and the rider below now
has to measure exactly that.

**When the distinction returns.** `0016`'s `evidence_basis` is the
authenticated carrier this rule wants and it is FROZEN; v1 does not
unfreeze it. The narrowing is deferred to that carrier's own round, and
the deferral is the reason the rule is broad rather than an oversight.

**The invariance this spec now owes `0006`, as a matrix:** the decision
must be UNCHANGED under every manipulation of source identity, which is
a stronger claim than "we don't use it" and is testable —

| mutation of the incoming or prior edge | required |
|---|---|
| `source_id` present → absent, either side | decision unchanged |
| `source_id` absent → present, either side | decision unchanged |
| `source_id` set to an arbitrary caller-chosen value | decision unchanged |
| `origin` local → foreign, either side | decision unchanged |
| the prior arrives by IMPORT (0005 cap applied, author flattened) | decision follows the FLATTENED author, and still reads no `source_id` |

**Every term, including absence:**

| term | absent case | why this reading |
|---|---|---|
| ~~`source_id`~~ | **NOT A TERM (R2-1)** | removed from the decision entirely: `0006` says it may GROUP, never GRANT. Kept in this table as a struck row so a reader who remembers it finds its removal rather than its absence |
| `derived_from` | `None` → not relayed | **and this is the known soft spot, named rather than hidden.** Today `None` means both "genuinely first-party" and "the host said nothing" — which is precisely the ambiguity §4d's `EvidenceContext` exists to remove. Until a host supplies one, `self_assertion` is over-inclusive: it will be TRUE for user edges whose provenance was merely unstated. |
| `author_of_evidence` | never absent | a required field on `Provenance` |

**The over-inclusion is in the REFUSING direction, and that is the
choice.** A user edge whose derivation was never declared is treated as
self-assertion, so the rule refuses more often than a perfectly-informed
rule would. A refusal is a recorded row and a confirmable path, not data
loss; the opposite error silently erases sourced evidence about a third
party. Once `EvidenceContext` ships, `self_assertion` tightens to
`context.direct`, and it tightens WITHOUT changing this rule's shape.

**What is NOT expressible today, and is therefore not claimed.** v4 also
spoke of "confirmation, a higher rung". `0008` grants confirmation NO
authority, so there is no rung to read, and the phrase is withdrawn
rather than reinterpreted. A basis-aware rule — one that distinguishes
first-hand from relayed evidence properly — needs `0016`'s frozen
`evidence_basis`, and 0016 is a FROZEN surface. **v1 does not unfreeze
it.** The basis-aware form is recorded as the successor and named as
blocked on 0016's own round. The generated policy gains the subject dimension; the 400-row
author product stops being the whole decision procedure, and the refusal
lands as a `supersession_refusals` row exactly like the ladder's own
(same carrier, `rule_version` bumped — no new table).

**The narrowness is v1's, held with a MEASUREMENT RIDER (internal round
1, M-3 ruling):** "sole authority is self-assertion" closes the reviewed
attack without pushing routine user corrections of their own third-party
entries into authorisation friction — and the broad form ("ANY
user-authored retirement of an OTHER-subject sourced fact refuses
pending confirmation") has no measured constituency. **The rider as v4 wrote it could not have measured anything, and the
reviewer showed why (R1-1).** Refusal rows carry edge ids, relation,
effective authorities and `rule_version` — no cell code, so refusals
could not be attributed to a cell. And the decisive population is the
one that produces NO ROW AT ALL: an event the narrow rule ALLOWS and the
broad rule would refuse never reaches the refusal carrier, so counting
refusals could never find the broad form's constituency. It would have
returned zero for the wrong reason, and zero is what "no measured
constituency" already claims — the rider would have confirmed itself.

**THE RIDER IS DEFERRED. IT CANNOT BE BUILT ON ANOTHER SPEC'S DEFERRED
CONSENT SURFACE (external round 3, R3-2).**

Round 2 rewrote the rider as counters on `0015`'s existing carrier,
incremented at decision time under the existing consent posture. Accepted
`0015` says the opposite of every clause of that:

| `0015` says | v6 assumed |
|---|---|
| refusal counters are **explicitly deferred to a new consent discussion** | they can be added now |
| new payload fields require **consent-version gating and updated consent text** | the existing posture covers them |
| counters derive **only from a fresh commit** | increment at decision time |
| replays, stale attempts and refusal-only outcomes **do not count** | every decision counts |

Decision-time increments would also overcount aborted and `PLAN_STALE`
attempts, and the rider named no field names, cell taxonomy, consent
version, visibility rules or multi-prior cardinality. **This is the third
round in which I asserted a rule over another spec's contract without
checking that contract's domain** — after `0006` at R2-1 and `0012` at
R1-3 — and it is the same error each time.

So the rider is WITHDRAWN from v1 rather than specified around:

* **v1 ships with the broad rule's constituency UNMEASURED, and says so.**
  The narrow/broad question is not resolved by this spec and cannot be
  resolved by it, because the only honest way to count the deciding
  population is a telemetry surface whose consent question `0015` has
  deferred.
* Revisiting the broad form therefore waits on **`0015`'s consent
  discussion**, and on a complete telemetry construction — field names, a
  closed cell taxonomy, consent version and text, host/MCP visibility, and
  fresh-commit semantics that exclude replays and stale attempts. That is
  `0015`'s round to hold, not this spec's to pre-empt.
* What v1 keeps is the NARROWNESS ITSELF as a stated, deliberate choice
  with its cost named (§4b: the rule refuses more than a
  perfectly-informed rule would), rather than a promise to measure that it
  has no mechanism to keep.

`0015` remains in `Spec-Requires` — this spec still depends on its
supersession counters existing — but nothing here adds to its payload.

### 4c. `CONTESTED` at every reader (E3, per the E-Q2 ruling)

**CONTENTION IS `0003`'s REFUSAL-SCOPED NOTION. This spec does not
define a second one (external round 2, R2-3).**

`contested` is what the shipped surface already means: a LIVE REFUSAL
CONTENTION — a refusal record exists, both referenced edges are still
active and distinct, and the relation is functional. `compile.py` says
so in terms ("the derived-view treatment is REFUSAL-scoped (Option B),
not every contention") and `Recall.contested` carries one entry per live
refusal.

v5 defined it instead from ANY active same-class pair with ≥2 distinct
values, and the reviewer executed the divergence: two active, same-class,
distinct-value edges inserted directly into a real store are **contested
under v5's predicate and NOT contested under the shipped
`Recall.contested`** — 0 groups, 0 exposed members. The draft was
carrying two contracts at once and calling both `contested`, which is
how a reader gets a label that no reader produces.

So E3 governs the RENDERING of the refusal-scoped set — what a reader
does when it meets one — and derives nothing new:

| surface | E3's obligation |
|---|---|
| `Recall.contested` | already the carrier; E3 adds no members and removes none |
| gate | a contested functional value is non-assertable-as-current — assert the CONTENTION, never one side |
| maintain | resolution verbs (consolidate, absorb across the pair) are suppressed; **`0012`'s per-edge expiry is NOT** |
| import | a refusal record is store-local state; an imported pair carries no refusal and is therefore not contested on arrival |
| direct-store insertion | **not contested** — no refusal, no contention. This is the reviewer's executed cell, and the shipped answer is the right one |

The distinct-value requirement folded at R1-3 is not lost: it is part of
the shipped predicate already ("still distinct"), which is why adopting
that predicate keeps R1-3 closed rather than reopening it.

**The distinct-value clause is not a refinement; without it the rule was
FALSE against accepted `0012` (external round 1, R1-3, executed).** v4
defined contention as two active same-class edges and stopped there.
`0012` deliberately PERSISTS a same-value restatement as a separate
active edge and says in terms that such a pair is not contested — the
reviewer ran
`tests/test_0012_currency_renewal.py::test_a_same_value_restatement_produces_no_contention_artifacts`
(**1 passed**) on a MENTIONABLE USER/SYSTEM pair that is active,
same-class, and produces no contention artifact. v4's rule would have
labelled every renewal in the store as a contradiction. Two records of
the same value are agreement; contention needs disagreement, and
disagreement means distinct values.

**Composition with the specs this rule reaches into**, which v4 left
unstated:

* **`0003`** already scopes contention to REFUSAL — a refused
  supersession leaves both sides active and records why. This rule is
  derived and additive: it names the resulting state at read time and
  changes no refusal semantics. Where `0003` has already recorded a
  refusal, `contested` is the read-side view of that same fact, not a
  second one.
* **`0012`** owns same-value persistence, the render-time collapse of
  strict redundancy, and **per-edge expiry**. The clause above adopts
  `0012`'s own `_value_key` normalisation rather than inventing a
  second notion of "same value", so the two cannot drift apart.
* **`maintain` neither resolves nor consolidates across a contested
  pair** — and that is a NARROWER claim than v4 made. It does NOT
  suspend `0012`'s per-edge expiry: a contested edge still expires on
  its own schedule, because holding a stale value alive because it is
  disputed is the opposite of the guarantee. Contention suppresses
  RESOLUTION verbs (consolidate, absorb across the pair), never
  lifecycle.
* Structured reach, budgeting, scoping, proactive no-new-reach and
  cache semantics are UNCHANGED by this rule. It adds a label at read
  time; a reader that never asks for the label sees exactly today's
  behaviour.

Readers handle it the way they handle `needs_confirmation` — recall
labels the value set as contested rather than choosing one; the gate
treats a contested functional value as non-assertable-as-current
(assert the CONTENTION, never one side). Resolution happens only
through the entitled paths: supersession by an entitled author,
`correct()` under E5, or `confirm()`.

**Prerequisite consequence:** `0012` joins `Spec-Requires` as a direct
dependency, and `src/veracium/lifecycle.py` joins §7a's consumer list —
the expiry interaction above is a claim about that module and v4 did
not name it.

### 4d. Trusted ingress as a capability (E4)

`derived_from=None` stops being trusted-by-omission: `ingest_event`
gains an explicit `EvidenceContext` (E-Q3: a constructor argument)
carrying the host's POSITIVE declaration — `direct` (the host attests
first-party capture) or `derived(from_class)`. **`from_class` is a CLOSED domain,
validated at construction (internal round 1, m-6): an unknown or
malformed value RAISES and NOTHING IS WRITTEN.**

*(External round 1, R1-4: v4 said both "the constructor refuses
unknowns" AND "fails closed to the `derived(THIRD_PARTY)` floor". Those
are different observable outcomes for one input, and a spec that names
two cannot be conformed to. REFUSAL is chosen: flooring a malformed
value silently accepts a host bug and writes a record whose declared
provenance nobody meant, which is the failure this capability exists to
prevent. Refusing is loud, has no write, and leaves the host's bug
where the host can see it.)*

**ABSENCE IS A DIFFERENT INPUT AND KEEPS THE FLOOR.** No context at all
is the conservative cell: treated as `derived(THIRD_PARTY)`, never as
direct. That is not a contradiction of the refusal above — a host that
supplies nothing has declared nothing and gets today's worst case; a
host that supplies GARBAGE has declared something untrue, and the
difference is worth an exception.

**The complete grammar, with every cell reachable and named:**

| input | outcome |
|---|---|
| context absent (`None`) | `derived(THIRD_PARTY)` — the floor |
| `direct` | host attests first-party capture |
| `derived(USER)` / `derived(SYSTEM)` / `derived(ASSISTANT)` / `derived(THIRD_PARTY)` | as declared |
| `derived(<unknown member>)` | **RAISES**, no write |
| `derived(None)` | **RAISES**, no write — `derived` with nothing derived from is not the same as absence |
| `derived(<non-enum type>)` — str, int, dict, list | **RAISES**, no write; no coercion, no `str()` |
| a bare string `"direct"` where a context is expected | **RAISES** — the value object cannot be minted from a caller string |

**Adversarial matrix (V-names to be assigned at implementation):** each
RAISES row above is a test, plus the two that make the closed domain
mean something — an enum member added later with no cell must fail the
totality test rather than inherit a default, and the absence row must
be proven distinct from `derived(THIRD_PARTY)` supplied explicitly, so
the two paths cannot be collapsed by a future refactor. The context is a value object the persistence site cannot mint
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
1, M-2/E-Q4).

**WHAT THIS IS: AN INTEGRITY BINDING. IT IS NOT AUTHENTICATION, AND v4
CLAIMED OTHERWISE (external round 1, R1-2).** v4 said binding the
principal made the authorisation "unforgeable" and that it
"authenticates CORRECTORS". It does neither, and the reviewer executed
the reason: `0020` states plainly that `principal` is HOST-SUPPLIED,
FORGEABLE and NOT AUTHENTICATED, while `Memory.correct()` MINTS the
authorisation itself from caller-controlled values. A caller may name
any principal, request a fresh authorisation for it, and pass the
in-transaction equality check. The cross-principal replay test blocks
REUSE under a different name; it never blocked fresh impersonation, and
a five-tuple cannot authenticate a value its own caller chose.

So the claim is withdrawn and replaced by the one the mechanism
supports:

* **What the binding DOES establish.** A correction, once authorised,
  cannot be altered, replayed against a different prior, rebound to a
  different replacement value, or reused under a different principal —
  every element is verified INSIDE the transaction (the `0014`
  snapshot-verification shape). The receipt records WHICH principal the
  caller declared, so an operator can attribute and scope after the
  fact. That is integrity and attribution, and it is worth having.
* **What it does NOT establish.** That the declared principal is who
  they say they are. Nothing in this spec authenticates a corrector.

**`correct()` is therefore a PROTECTED HOST API, on 0008's model, and
the obligations are the host's** — stated here rather than assumed:

| the host must | because |
|---|---|
| authenticate the principal before calling | the store cannot; `principal` arrives as a caller-supplied string |
| establish the user's INTENT to correct | a correction retires a prior fact; an unintended one is a silent loss |
| not expose `correct()` on a surface a model can reach with a caller-chosen principal | that is self-elevation with extra steps — the same rule that keeps `system` off the MCP surface |

A future spec may specify an externally issued opaque capability that
`Memory.correct()` cannot mint from caller-controlled values, which
WOULD authenticate. That is a real API-surface change, it is out of
scope for v1, and it is named here so the gap is a known one rather
than a silent one.

With the binding so scoped: the subject-entitlement rule of §4b applies
to corrections exactly as to extractor-driven supersession. `record_outcome` stays
fact-untouching.

### 4f. The history partition (E6)

**v4's three labels were neither TOTAL nor EXCLUSIVE, and their stated
motivation was FALSE. External round 1, R1-5, executed all three.**

Applying v4's definitions literally: an active, quarantined, grounded,
uncontested edge matched **zero** labels; an active, mentionable,
grounded, contested edge matched **both** `GROUNDED_CURRENT` and
`UNVERIFIED_CURRENT`. And the premise — that `compile` and `introspect`
interleave history with present fact — does not hold: `compile.py`
reads `active_only=True`, `introspect.py` already separates retired
counts and renders categories from the active set, and `gate.partition_parts`
drops inactive edges from both blocks. **No shipped reader interleaves
history with present fact.** The defect E6 was written to fix is not
there.

**So E6 is re-motivated to what it actually earns, and it is smaller.**
Two states this spec introduces — `CONTESTED` (§4c) and the quarantined
cell — have no defined rendering, and every reader that meets them will
otherwise invent one. E6 supplies ONE vocabulary so they cannot diverge,
and states the precedence exactly. It is a naming and totality
guarantee, not a repair of a live interleaving bug, and v4 claimed the
latter.

**The precedence table — FIRST MATCH WINS, which is what makes it both
total and exclusive:**

| # | condition | label |
|---|---|---|
| 1 | `not e.active` | `RETIRED_HISTORY` |
| 2 | `e.quarantined` | `QUARANTINED_CLAIM` |
| 3 | `contested(user_id, subject, relation)` (§4c) | `CONTESTED_CURRENT` |
| 4 | `e.ungrounded or e.use_only` | `UNVERIFIED_CURRENT` |
| 5 | otherwise | `GROUNDED_CURRENT` |

Row 5 is a catch-all, so TOTALITY holds by construction rather than by
enumeration; first-match makes EXCLUSIVITY hold for the same reason.
`QUARANTINED_CLAIM` and `CONTESTED_CURRENT` are new since v4 — v4 had no
cell for either, which is exactly why an edge could match none or two.
Precedence order is a claim in itself: quarantine outranks contention
because a quarantined edge's dispute is moot until it leaves quarantine,
and contention outranks ungroundedness because a contested value must
not be rendered as merely unverified-but-current.

**The invariant, and its adversarial matrix:** for every edge, exactly
one label — asserted over the CROSS-PRODUCT of (active × quarantined ×
ungrounded × use_only × contested), not over sampled cells. The two
cells R1-5 executed (quarantined-grounded-uncontested → row 2;
mentionable-grounded-contested → row 3) are named cells in it, since
they are the ones v4 got wrong.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| a store with only user-self facts | byte-identical decisions — SELF-on-SELF entitlement is today's ladder |
| third-party/org facts, no contention | unchanged until a USER self-assertion attempts to retire ANY OTHER-subject fact — sourced or not (R2-1 removed the sourced qualifier, so this widened) — then a NEW refusal row |
| a functional relation in genuine contention | today: silent both-active; after: derived `CONTESTED` at every reader, gate asserts the contention |
| existing `correct()` callers | same signature; the authorisation is minted by `Memory.correct` itself for the interactive path — the CHANGE is that tool-driven and replayed invocations can no longer TAMPER WITH or REPLAY (they can still name a principal they are not — R1-2) it |
| hosts that never construct `EvidenceContext` | floored at `derived(THIRD_PARTY)` — strictly more conservative than today |

## 6. Invariants and executable checks — REQUIRED, blocking

| # | invariant | check |
|---|---|---|
| **S1** | `subject_class` is TOTAL with OTHER as default — every subject string classifies, and only the canonical-predicate cell is SELF | `test_subject_class_is_total` — property test over adversarial strings, the `0024` predicate cells included |
| **S2** | a USER self-assertion never retires an OTHER-subject sourced fact; the refusal lands as a `supersession_refusals` row | `test_self_assertion_cannot_retire_other_subject` — the E2 cell, plus the refusal-row assertion |
| **S3** | `CONTESTED` is derived — NO stored carrier exists, and every reader (recall, gate, maintain) handles the contested cell | `test_contested_is_derived_and_total_over_readers` — an AST sweep for stored writes plus per-reader behaviour cells |
| **S4** | `correct()` reaches storage ONLY through the atomic plan machinery with a verified `CorrectionAuthorisation`; a forged, replayed, unbound, or **cross-principal** authorisation aborts inside the transaction (M-2: a capability minted under one principal replayed under another is the named new cell) | `test_correct_requires_bound_authorisation` — the M7 regression, forge/replay/rebind cells **+ the replay-across-principals cell** |
| **S5** | absent `EvidenceContext` floors at `derived(THIRD_PARTY)` — absence is never the trusted cell — **and an unknown or malformed `from_class` RAISES with no write — a DIFFERENT outcome, settled at R1-4 (absence declares nothing; garbage declares something untrue)** (was: floored too (m-6): the domain is closed; validators refuse the unknown, not just cover the known** | `test_absent_context_floors_conservative` — plus the unknown-value cell |
| **S6** | the partition labels are derived and total — every edge lands in exactly one of `labels=5` — the labels of §4f's first-match precedence table (R1-5/CARRIER-R2-1: v5 said three, which was neither total nor exclusive, and said it in a row a phrase-search did not reach) | `test_history_partition_is_total` — enumeration over the field product |
| **S7** | disclosure is never WRITTEN here — the `0024`/`0025` pipeline owns it. **§4f's partition READS it** (`quarantined`, `use_only`) to place a label, which v5 denied (R2-1/CARRIER-R2-1); reading to render is not writing to decide, and the distinction is the invariant | `test_no_disclosure_interaction` — the N2-style single-writer sweep extended, not duplicated |

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
| `src/veracium/lifecycle.py` | **added at R1-3.** §4c claims contention does NOT suspend `0012`'s per-edge expiry; that is a claim about this module and v4 named neither |
| `src/veracium/portability.py` | **retained, on NARROWER grounds (R3-1).** R1-1 listed this because source identity participated in the predicate; it no longer does. What remains is real: the `0005` import cap FLATTENS an imported record's author, and the decision is a function of author and derivation — so the import boundary decides which authority chain the predicate sees. The matrix asserts the import-flattened cell |
| tests | the §6 table's named tests — §6 is the ONE authoritative list |

## 8. Claims and limits

This spec decides who may retire what about whom, and nothing else. It
does not touch disclosure (`0024`/`0025` own the trust pipeline), does
not resolve contention (it makes contention VISIBLE and gates its
resolution paths), and grants no new authority to anyone — every rule is
a refusal that does not exist today or a label over facts already
stored.

## 9. Brief for the external reviewer

*(Internal review is complete: research ran two rounds — round 1 PASS
WITH AMENDMENTS with all three questions ruled, round 2 PASS with no new
findings, both folded. The questions below are what we most want you to
attack.)*

1. **The E-Q2 ruling** — derived-at-read rests on the single-writer
   discipline; if you think a stored member with enumerated writers is
   safer, that reverses three accepted precedents and is the finding we
   would rather have now than after implementation.
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
| **E-Q1** | How is the user's own subject identity canonicalised? | **RESOLVED for v1 (2026-08-22)** — the predicate floor ships; the identity-relation option rejected blocking-grade; the alias-set extension point named and priced at ≈0.017% — the GENERATED census (31 rows over 94 distinct candidate strings). The figure v4 carried here is superseded and is not restated in this row; PACKAGE-R1-1 and §3b record what it was and why it went measured constituency (§3b) | research + dev, jointly | — |
| **E-Q4** | should the E5 authorisation tuple carry the acting principal (`0020`) as a fifth element? | **RESOLVED (internal round 1, 2026-08-23): YES** — E5 as drafted bound the arguments, not the actor; under `0020` the principal IS what distinguishes callers. Fifth element, verified in-transaction, receipt records WHO, S4 gains the cross-principal replay cell (§4e) | dev + internal review | — |

## 11. Changes in v5 — the round-1 fold (2026-08-26)

Round 1 returned draft v4 for major amendment: five spec findings and one
package finding. All six are folded here. Two of them found claims that
were not merely incomplete but **false against shipped, accepted
behaviour**, and the reviewer executed both.

**0011-R1-1 — the central cell was not representable.** v4's rule spoke
of `sourced`, `self-assertion` and "confirmation, a higher rung", and
none had a runtime predicate; §4b's formal condition tested subject class
and sole authority while OMITTING the sourced term, contradicting §3c's
own unchanged row. Folded: `sourced` and `self_assertion` are closed
predicates over state that exists today, the policy function is TOTAL and
replaces the condition, and every term's absence case is stated. The
`derived_from is None` ambiguity is named as the known soft spot rather
than hidden, with the over-inclusion pointed in the REFUSING direction
and the reason given. "Confirmation is a higher rung" is WITHDRAWN —
`0008` grants confirmation no authority, so there was no rung to read.
The basis-aware successor needs `0016`'s frozen `evidence_basis`; **v1
does not unfreeze it**, and the successor is recorded as blocked on
0016's own round. `0008`, `0012` and `0016` join `Spec-Requires`.

**The rider could not have measured anything.** Refusal rows carry no
cell code, and the deciding population — allowed by the narrow rule,
refused by the broad one — produces NO REFUSAL ROW AT ALL. Counting
refusals would have returned zero for the wrong reason and confirmed the
claim it was meant to test. Folded at round 1 as a cell code and a flag
on the existing carrier plus a counts-only counter — and
ROUND 2 deleted the flag as constant-true and the columns with it; see
§12.

**0011-R1-2 — E5 binds an asserted identity; it does not authenticate.**
v4 called the authorisation "unforgeable" and said it "authenticates
CORRECTORS". `0020` states that `principal` is host-supplied, forgeable
and unauthenticated, and `Memory.correct()` mints the authorisation from
caller-controlled values — so a caller may name any principal, obtain a
fresh authorisation and pass the in-transaction check. The
cross-principal replay test blocks REUSE, never fresh impersonation.
Folded: the claim is withdrawn; the binding is INTEGRITY and
ATTRIBUTION, stated as such in all three carriers that made the claim;
`correct()` is a protected host API on 0008's model with the host's
authentication and intent obligations written down; the externally
issued capability that WOULD authenticate is named as out of scope for
v1 rather than implied.

**0011-R1-3 — E3 misclassified same-value restatements.** v4 defined
contention as ≥2 active same-class edges. Accepted `0012` deliberately
persists a same-value restatement as a separate active edge and says
such a pair is not contested; the reviewer ran
`test_a_same_value_restatement_produces_no_contention_artifacts`
(1 passed) on exactly that shape. v4's rule would have labelled every
renewal in the store a contradiction. Folded: ≥2 DISTINCT normalised
`_value_key` values, using `0012`'s own normalisation so the two cannot
drift; composition with `0003`, `0012`, budgeting, scoping, proactive
reach and cache semantics stated; **"maintain neither resolves" narrowed
so it does not suspend `0012`'s per-edge expiry** — contention suppresses
resolution verbs, never lifecycle; `lifecycle.py` added to §7a.

**0011-R1-4 — the invalid-input contract contradicted itself.** §4d said
a malformed `from_class` is both refused by the constructor and floored
to `derived(THIRD_PARTY)`. Those are different observable outcomes and a
spec naming two cannot be conformed to. Folded: it RAISES and nothing is
written. ABSENCE is a different input and keeps the floor — a host that
supplies nothing has declared nothing; one that supplies garbage has
declared something untrue. The complete `direct`/`derived` grammar is
enumerated with every cell reachable, and the adversarial matrix named.

**0011-R1-5 — S6's labels were neither total nor exclusive, and their
premise was false.** Executed: an active, quarantined, grounded,
uncontested edge matched ZERO labels; an active, mentionable, grounded,
contested edge matched TWO. And `compile.py` reads `active_only=True`,
`introspect.py` already separates retired, `gate.partition_parts` drops
inactive — **no shipped reader interleaves history with present fact**,
so the defect E6 claimed to fix was not there. Folded: a five-row
first-match precedence table, total by catch-all and exclusive by
ordering, with `QUARANTINED_CLAIM` and `CONTESTED_CURRENT` added
(v4 had no cell for either, which is why an edge could match none or
two); the invariant asserted over the cross-product rather than sampled
cells; and E6 re-motivated to what it earns — one vocabulary for states
this spec introduces — with the false premise retracted in place.

**PACKAGE-R1-1 — the deciding measurement was not reproducible.** No
`specs/evidence/0011/` existed; the archive could not re-derive any
reported figure. Folded: `subject_census.py`, a counts-only aggregate
digest-bound to the same cache sha as 0025's census, and the
distinct-string candidate table the hand classification was made over,
with given names masked. `--aggregate` reproduces every figure without
the corpus. **The load-bearing figure reproduces exactly — 183,417
triples, 72,253 predicate passes, 39.4%. Two prose figures did not and
are RETIRED**: v4's 305 candidates = 0.166% and ≈30 self-denoting
≈0.016% came from a regex family that was never recorded; the recorded
one finds 337 over 94 distinct strings, of which 31 = 0.017%. The
conclusion is unchanged and marginally stronger. This is the 0001 R11-1
lesson — packaged figures are GENERATED and BOUND — reaching a second
line, which it should have done before this package was sealed.

## 12. Changes in v6 — the round-2 fold (2026-08-27)

Round 2 returned v5 for major amendment. **Four of the five findings were
defects in round 1's own fixes**, which is what the found-in-fix checklist
exists to prevent and I did not run on that fold.

**0011-R2-1 — `source_id` had become an entitlement capability.** Round 1
defined both `sourced` and `self_assertion` from `source_id` presence,
because it was state that existed. The reviewer executed what that bought:
omitting the prior's `source_id` ALLOWED the retirement, and adding any
`source_id` to the incoming assertion ALLOWED it too. Accepted `0006` says
in four places that `source_id` **may GROUP, never GRANT** — optional,
host-supplied, diagnostic, and its absence must not relax a decision — and
`0006` was not even a declared prerequisite while its carrier decided
authority. The fix is not to read the field more carefully but to STOP
READING IT: `sourced` is gone, and the rule refuses on subject class plus
self-assertion alone. That refuses MORE — the narrowness is lost with the
distinction — and the cost is stated rather than absorbed. `0016`'s frozen
`evidence_basis` is the carrier that would restore it; v1 does not unfreeze
it. A source-identity invariance matrix is now owed: the decision must be
unchanged under presence, absence, forgery, foreign origin and import.

**0011-R2-2 — a field that could not vary.** `would_refuse_broad` was
CONSTANT TRUE, because the broad predicate is a strict superset of the
narrow one. It is deleted. Round 1 also proposed two new columns while §7a
named no schema, migration, erasure or telemetry surface and §7 claimed
there was no stored state to unwind — three statements, two false if the
columns shipped. The rider now adds NO stored state: counters on `0015`'s
existing carrier, no column, no migration, nothing to erase. §7 is true
again, and `0013` is not a prerequisite because there is no schema change.

**0011-R2-3 — two contracts called `contested`.** The checker validated a
standalone value-list function — a reimplementation, not the rule any
reader sees. The reviewer inserted two active, same-class, distinct-value
edges into a real store: v5's predicate said contested, the shipped
`Recall.contested` said 0 groups and 0 exposed members. `compile.py`
states the shipped contract outright — REFUSAL-scoped, not every
contention — so this spec adopts it and defines nothing new; E3 governs
the RENDERING of that set across `Recall.contested`, gate, maintain,
import and direct-store insertion. The checker now drives a real store and
asserts both the reviewer's cell (direct pair → NOT contested) and a
positive control (a live refusal → contested), so it cannot pass by never
firing.

**CARRIER-R2-1 — contradictory text passed a green checker.** Seven
authoritative statements survived round 1: §3a's UNFORGEABLE, §3c's
"confirmation, a higher rung", §5's "can no longer forge", S5's doubled
malformed-input outcome, S6's three labels, S7's denial that any rule
reads disclosure, and E-Q1's retired figure. The checker searched narrow
phrases across the whole file, so a withdrawal written in §4e satisfied it
while §3a still asserted the opposite. All seven are swept, and each
assertion is now bound to its NAMED ROW — a withdrawal written elsewhere
cannot satisfy it. **S6 is checked count-to-count**: the row carries
`labels=5` as a token and the checker compares it to the actual number of
rows in §4f's table. That last change came from this fix's own failure —
the first attempt searched for "three labels", and the row says "one of
the three", so the guard looked for wording the spec never used and the
contradiction survived a second time.

**EVIDENCE-R2-1 — the census verified nothing in aggregate mode.** A
one-entry aggregate with an all-zero digest printed the claimed
measurement and exited 0. The aggregate now passes a CLOSED typed schema
(missing and unknown keys both refused) and every figure it asserts about
the cache is cross-checked against `0025`'s aggregate — derived from the
same cache by a different script, shipped in the same archive — including
a triple total independently derived by summing 0025's relation counts. A
fabricated manifest must now agree with an artifact its author does not
control. Seven fabrications tested, all refused; the real aggregate still
verifies. This is `0001`'s R12-1 arriving in a second place, again after
the fact rather than before.

## 13. Changes in v7 — the round-3 fold (2026-08-27)

Round 3 returned v6 for major amendment. Three of the four findings were
again defects in the previous round's fixes, and the shape had become a
pattern worth naming rather than folding past.

**0011-R3-1 — `derived(USER)` bypassed the rule, exactly as `source_id`
had.** `EvidenceContext.derived(USER)` is valid and reachable, and
`USER/derived_from=USER` carries effective authority **3 — identical to
`USER/None`** — yet v6 refused one and allowed the other. A marker
supplying no independent authority bought permission to retire an
OTHER-subject fact.

That is R2-1 one field over. R1 defined the rule over `source_id`; R2
found `source_id` grants and it moved to `derived_from is None`; R3 found
`derived_from` grants. **Each round replaced one unauthenticated marker
with another and inherited the class**: the defect was never the field,
it was keying on a marker's PRESENCE rather than on AUTHORITY.

The predicate is now `effective(author, derived_from) == effective(USER,
None)` — the chain carries nothing but the user's own authority, computed
by `0003`'s own function. Enumerated against production authority exactly
two chains qualify, so R3-1's cell sits in the refusal set BY
CONSTRUCTION. `specs/evidence/0011/policy_matrix.py` is the §6 acceptance
surface: 240 cells over author × derived_from × subject class × source
presence × origin, asserting totality, the named cell, **the general
property that equal effective authority decides equally**, invariance
under source identity and origin, that `derived_from` never raises
authority, and that a SELF-subject prior is never refused. Both defects
that actually shipped were planted against it and both are caught — the
absence-based one by the generalised check, which is the property that
would have ended this at round 2. §4b's decision table is GENERATED from
the matrix and bound to it.

**0011-R3-2 — the rider assumed another spec's deferred consent
surface.** `0015` defers refusal counters to a new consent discussion,
requires consent-version gating for new payload fields, and counts only
from a fresh commit — excluding replays and stale attempts. v6's rider
contradicted all of it and would have overcounted aborted and
`PLAN_STALE` attempts. **This was the third round in which I asserted a
rule over another spec's contract without checking that contract's
domain**, after `0006` and `0012`. The rider is WITHDRAWN: v1 ships with
the broad rule's constituency unmeasured, states that plainly, and leaves
both the consent question and the telemetry construction to `0015`'s own
round.

**CARRIER-R3-1 — the sweep was still incomplete and the check was
syntactic.** Five more contradictions survived: S5's doubled
malformed-input outcome, §4b claiming `sourced` is defined here after its
removal, the term table still listing `source_id`, the regime row scoped
to sourced priors when unsourced ones now refuse too, and §7a justifying
portability on a participation that no longer exists. All five swept. And
the reviewer defeated the no-`source_id` check by moving the read behind a
helper defined in a SEPARATE FENCE — every check still passed. The check
now follows the predicate's TRANSITIVE DEPENDENCIES across fences: both
the reviewer's bypass and a deeper two-hop version are closed.

**EVIDENCE-R3-1 — the deciding figures were still self-asserted.**
`schema` was typed and never valued, so `schema = 999` with
`predicate_passes = 0` produced no findings. `schema == 1` is required
now. More usefully, `0025` turns out to carry subject data for one
subpopulation — `subject_user` over `third_party_claim` — so **the
predicate itself is cross-checked: 1,606 of 3,945, two scripts, same
answer**. That does not bind the whole-corpus count, and the package no
longer implies it does: every figure is labelled by what backs it, and
`predicate_passes` (72,253) plus the candidate table's completeness are
marked **RECORDED ONLY**, reproducible with `--cache` on the measuring
host and not from the archive alone. A reader without the corpus is
trusting dev for those two, which is stated rather than papered over.
