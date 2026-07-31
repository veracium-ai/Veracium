# Feature spec: <name>

*Fill this in **before** implementing. See `PROCESS.md`.*

> Copy this file. Process: `PROCESS.md`. **Every section below exists
> because we shipped or nearly shipped a defect it would have caught** —
> the provenance of each is noted in italics. Delete nothing; write
> **"n/a — <reason>"** rather than leaving a heading blank, because a blank
> heading is indistinguishable from an unasked question.

| | |
|---|---|
| **Author / session** | |
| **Version** | v1 — *re-read before editing; quote the version you approve* |
| **Status** | draft · in review · accepted · accepted-with-amendments · deferred · rejected |
| **Internal reviewers** | dev · research · workflow-platform *(name who actually reviewed; note any unavailable)* |
| **External review** | required for **full** specs (= touches a guarded file); not required for lightweight · date sent / returned · reviewer-safe copy? · **retrospective** if security hotfix |
| **Decision + date** | |
| **Path** | full · `lightweight` (§§1, 2c, 4, 6, 7, 8; §§2, 3, 3b, 5 omitted) |

---

## 1. Problem and motivation

What is wrong today, for whom, and **what happens if we do nothing**. One
paragraph. If the honest answer to the last question is "nothing much", the
correct outcome is **rejection at proposal stage** — that is what the stage is
for.

**Alternatives rejected**, with the reason. *(A spec that never considered
an alternative usually has not considered the problem.)*

---

## 2. Field contracts touched

*Provenance: reinforcement silently overwrote `valid_from`, whose documented
meaning at three code sites is "when the fact became true". The renderer
then emitted `(since <that value>)` into the answer context — a false
statement injected into recall. Nobody had enumerated who reads the field.*

| field | read / written | its **documented** contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| | | | | |

**Enumerate consumers mechanically, do not recall them** —
`grep -rn "<field>" src/`. List every hit.

If the change alters a field's meaning: **which documentation, docstrings,
renderers, and exports state the old meaning, and are they all updated in
this change?**

---

## 2c. Untrusted inputs — REQUIRED, blocking

*Provenance: three fail-open defaults shipped or nearly shipped in three days —
a checker that exited 0 when it could not resolve its commit range, a disclosure
rule that made any unrecognised subject assertable, and a render that stripped
origin. **All three were inputs the library does not control.** The first
proposed remedy was a prose section asking "which way does this fail on garbage
input"; it was rejected, correctly, because a prose answer is a **judgement**
made from the same mental model that produced the defect — the author who wrote
the fail-open rule believed it failed closed, and so did the reviewer who
amended it. **So this is an enumeration, not an evaluation.** A table makes a
missing mechanism visible; a paragraph lets it be described away.*

One row per input this change consumes but does not control.

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| *(extractor output)* | | | | | |
| *(host configuration)* | | | | | |
| *(CLI / environment / git)* | | | | | |
| *(data written by an older version)* | | | | | |
| *(network / provider response)* | | | | | |

**An empty cell in the invariant column blocks the change.** That column is the
whole point: a behaviour with no mechanism to enforce it is a hope. The rule was
tested against a real case before adoption — an amendment that made a rule
*fail closed* on a predicate the codebase **cannot evaluate** (there was no
entity resolution, and no user display name to compare against) passes a prose
version of this section and **fails this one**, because the row has no invariant
to name.

---

## 3. Trust-class matrix — REQUIRED, blocking

*Provenance: T1 subset-absorption merged edges without checking authorship
or disclosure, so a third-party restatement could retire a user-asserted
fact out of the assertable set and inherit its confidence. Advisory
GHSA-r7j7-5jq9-3f5q. The design review and both sessions missed it because
everyone was reasoning about identity semantics.*

For every operation this change performs on stored state, state the outcome
for each combination. **An unanswered cell blocks the change.**

**Enumerate the classes from code, not from this table** — `EvidenceAuthor` and
`Disclosure` are enums and gain members. A matrix hardcoded here goes stale
silently; one built from today's members cannot.

**Be directional where the operation is.** Supersession, absorption and
reinforcement all distinguish the **prior/surviving** edge from the
**incoming/candidate** one, and **the 0.4.1 defect lived precisely in that
asymmetry** — `prior=user, incoming=third-party` and its reverse are different
operations with different correct answers, so a single `user × third-party` cell
cannot express the bug the section exists to prevent. Use two rows.

| operation | prior=A, incoming=B | prior=B, incoming=A | same-class | involving quarantined | involving `use_only` |
|---|---|---|---|---|---|
| | | | | | |

*(For unary operations use a state-transition table instead; for batch
operations state the rule over the set — and say explicitly whether the result's
provenance is derived from the **whole set** or from one member. Deriving it
from one member is what produced GHSA-hcj3-8jqc-wqrp.)*

Then answer explicitly:

- Can this operation cause a **user-asserted fact to become
  non-assertable**? Under what input?
- Can it cause **non-user content to gain user-grade authority,
  confidence, or currency**?
- Can it **clear `needs_confirmation`**, and is the triggering event
  genuinely new evidence?
- Does it **merge, drop, or overwrite provenance** of any input?

**Write-time or maintain-time?** *(This distinction resolved the T2
disagreement: reinforcement may refresh currency at write time because
fresh evidence just arrived; maintenance-time bookkeeping over existing
statements may not, because that manufactures freshness from recognition.)*
State which this is, and justify any currency, confidence, or flag change
against it.

---

## 3b. Authorization and scope — *full specs only*

*Trust class answers **whose claim this is and what authority it has**. It does
not answer **which user is permitted to see it**. Those are separate invariants,
and a claim can be fully user-authoritative and still private to another
tenant.*

- Does this cross a **user, tenant, or scope** boundary? Which?
- Who may **see** the affected state, and does this change that set?
- What happens on **scope change** — sharing, un-sharing, group join or leave,
  revocation?
- Does anything become **visible to a principal who could not see it before**?

---

## 4. Behaviour

What the change does, in observable terms — what a caller sees, not how it
is implemented. Include the **exact rendering change**, if any, since
rendered text becomes model context.

**Interfaces:** new or changed public API, CLI, MCP surface, export format.
**Migration:** what happens to existing stores. What is **unrecoverable**?

---

## 5. Regime analysis — where does this behave differently?

*Provenance: recall was query-blind on any store past `max_subgraph_edges` —
every user-subject edge scored a constant, so truncation returned store
order and different questions returned identical facts. **No fixture ever
caught it because small stores never truncate.** It took a ~1,700-fact
store to expose, and only a real corpus builds one.*

- At what **scale, density, or duration** does this behave differently?
  (store size, edge count, history length, relation cardinality, tenancy)
- Which **thresholds or caps** does it interact with?
- **Do the tests reach those regimes?** If not, which release class is this?
  **Stable (on by default):** an unreachable regime **blocks** — add a test
  that reaches it. **Experimental (off by default):** may ship with the regime
  stated as untested in §8, provided the default is off and §8 says so.
  **Flipping that default to on is itself a change requiring a spec whose §5
  reaches the regime**, or the split becomes a two-step route to shipping
  untested behaviour.
- What behaves differently on a **cold vs warm** store, or first vs
  thousandth call?

---

## 6. Invariants and executable checks — REQUIRED, blocking

*Provenance: the T1 fix shipped with a hard bench canary. That is why the
same class of regression cannot recur silently.*

| invariant | executable check | where it runs |
|---|---|---|
| | | |

**Every invariant needs a check that runs in CI or the bench `--compare`
gate. An invariant with no check does not count** and blocks the change.

Standing checks that must not regress: injection asserts 0 · cross-user
leaks 0 · trust canaries 0 · supersession probes pass · malformed edges 0 ·
declared read-cost and latency ceilings.

**Reproducer retention:** any defect found during review becomes a
regression test, preserved with the spec.

---

## 7. Failure modes and reversibility

- How could this fail **silently**? What would the first visible symptom
  be, and how long after the cause?
- Is the effect **reversible**? From what record — and does that record
  contain enough to restore the *complete* prior state, not just reactivate
  one row?
- What does it do under **partial failure** (crash mid-operation, provider
  timeout, quota exhaustion)? *(Permanent errors must not be retried into a
  silent empty success.)*
- Does it create a new **attack surface** — anything that lets non-user
  content influence stored state, recall selection, or rendered context?

---

## 8. Claims and limits

*Provenance: this week a claim was retracted after measurement, and had
already propagated into two downstream documents before the retraction
reached them.*

- **What we will say** about this in the changelog, docs, or marketing —
  the exact wording.
- **What this does NOT establish.** List it. A change that "improves
  recall" on one corpus has not improved recall generally; a passing
  security suite is *"no failures observed on the frozen suite"*, never
  "secure".
- Any **measurement** cited here carries its run or commit.

---

---

## 9. Brief for the external reviewer

*Every full spec goes to the trusted third-party reviewer after internal
review. A brief produces a sharper review than "please review this" —
and past reviews found a distinct class of problem: not code errors and not
semantics errors, but **the frame we could not see because we were inside
it**.*

- **What we are least sure of** — name two or three things.
- **Where we suspect we have overstated** a claim, a measurement, or an
  assurance.
- **What would change our minds** about the approach.
- **Anything generalised for a reviewer-safe copy**, and why.

---

## 10. Open questions

Things genuinely undecided, each with **who decides**, **by when**, and a
class: `blocking` (before acceptance) · `pre-release` · `deferred`.
**Unclassified defaults to `blocking`**, so the cheap path is to think about it
rather than leave it blank. Better here than resolved by whoever implements
first.

---

## Reviewer checklist

- [ ] §3 has no unanswered cells, and is **directional** where the operation is
- [ ] §3's classes were read from the enums, not copied from the template
- [ ] Prohibitions AND the corresponding **permissions** are both tested — a
      guard drawn too broadly passes every prohibition test
- [ ] Every default fails **closed**: an unresolvable input costs assertability
      rather than granting it
- [ ] §2c has a row per uncontrolled input, and **no empty invariant cell** —
      "fails closed" on a predicate the code cannot evaluate is not a control
- [ ] §2 consumers were enumerated by grep, not recall
- [ ] Every §6 invariant has a check that actually runs
- [ ] §5 regimes are reachable by tests, or the change is experimental,
      off by default, and §8 says so
- [ ] §3b: no principal can see anything they could not see before (full specs)
- [ ] §6 and §8 are filled in — `n/a — <reason>` counts, blank does not
- [ ] §10 questions each carry a class; unclassified means blocking
- [ ] §8 states what this does *not* establish
- [ ] I have said where I think the **author's conclusion is wrong**, not
      only where the text is wrong
- [ ] I re-read the current version before reviewing, and I am quoting the
      version I approve
- [ ] §9 brief is written, and external review has been sent (or the
      security-hotfix carve-out is recorded)
