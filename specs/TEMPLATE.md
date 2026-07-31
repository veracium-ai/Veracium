# Feature spec: <name>

*Fill this in **before** implementing. See `PROCESS.md`.*

> Copy this file. Process: `spec-process.md`. **Every section below exists
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
| **External review** | required for full specs · date sent / returned · reviewer-safe copy? · **retrospective** if security hotfix |
| **Decision + date** | |
| **Path** | full · `lightweight` (§1, §4, §7 only) |

---

## 1. Problem and motivation

What is wrong today, for whom, and **what happens if we do nothing**. One
paragraph. If the answer to the last question is "nothing much", stop here.

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

## 3. Trust-class matrix — REQUIRED, blocking

*Provenance: T1 subset-absorption merged edges without checking authorship
or disclosure, so a third-party restatement could retire a user-asserted
fact out of the assertable set and inherit its confidence. Advisory
GHSA-r7j7-5jq9-3f5q. The design review and both sessions missed it because
everyone was reasoning about identity semantics.*

For every operation this change performs on stored state, state the outcome
for each combination. **An unanswered cell blocks the change.**

| operation | user × user | user × third-party | third-party × third-party | involving quarantined | involving `use_only` |
|---|---|---|---|---|---|
| | | | | | |

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
- **Do the tests reach those regimes?** If not, this is a hard gate: either
  add a test that does, or state the regime as knowingly untested in §8.
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

Things genuinely undecided, each with **who decides** and **by when**.
Better here than resolved by whoever implements first.

---

## Reviewer checklist

- [ ] §3 has no unanswered cells
- [ ] §2 consumers were enumerated by grep, not recall
- [ ] Every §6 invariant has a check that actually runs
- [ ] §5 regimes are reachable by tests, or declared untested in §8
- [ ] §8 states what this does *not* establish
- [ ] I have said where I think the **author's conclusion is wrong**, not
      only where the text is wrong
- [ ] I re-read the current version before reviewing, and I am quoting the
      version I approve
- [ ] §9 brief is written, and external review has been sent (or the
      security-hotfix carve-out is recorded)
