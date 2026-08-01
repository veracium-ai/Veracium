# Feature specification process

*Adopted 2026-07-31. Lives here rather than in a design folder because a
process that governs code belongs beside it and is versioned with it.*

*Every rule below exists because we shipped, or nearly shipped, a defect it
would have caught. The provenance is kept deliberately: a rule whose reason has
been forgotten is a rule that gets dropped in the first hurry.*

---

## Why this exists, stated concretely

In the last three days we designed a feature (T1 subset-absorption), wrote a
design document for it, had it reviewed by both sessions, resolved a
substantive disagreement about its semantics, approved it, merged it, and
**released a trust-boundary regression to PyPI that required a published
security advisory** (GHSA-r7j7-5jq9-3f5q).

Nothing in that sequence was careless. The design doc was good; the review
was real; the disagreement it resolved was the right one. **The defect
survived because every participant was reasoning about identity semantics,
and nobody's checklist asked what happens when the two merged edges have
different trust classes.**

That is what a specification process is for: not to make people think
harder, but to **make certain questions get asked whether or not anyone
thinks of them.**

**Admission rule for this document and the template: every required
question exists because we shipped, or nearly shipped, a defect it would
have caught.** New questions may be added preventively, but the rationale
is recorded.

**Removing a question requires all three:** in force for **≥10 full specs** ·
caught nothing in that time · **and the failure mode it targets is now
prevented by an executable check.** Remove prose only when a mechanism has
replaced it — *a question that catches nothing may be why nothing has gone
wrong.* Record removals with the evidence.

---

## Scope

**Applies to:** any change to stored state, its semantics, its trust or
disclosure classes, its lifecycle, or how it is selected for recall.

**Does not apply to:** documentation, tests, CI, packaging, dependency
bumps, or pure refactors that provably preserve behaviour. *If unsure,
write the spec — it is an hour, and the advisory cost more.*

**Lightweight path.** A change is **full** if it touches any file on the
guarded list (`specs/check_spec_reference.py`); otherwise it is
**lightweight**. The trigger is the list, never a prose judgement, so the
process and the checker cannot disagree.

**Lightweight specs still require §1, §2c (including §2c-ii), §4, §6, §7 and
§8.** Only §§2, 3,
3b and 5 — field contracts, trust-class matrix, authorization, regime analysis —
are conditional on being a full spec, because those are the guarded-surface
questions. **§2c is not**, because untrusted input does not care whether a file
is on a list.

**§6 and §8 are never skippable.** An invariant with no executable check and a
claim we cannot support are failure modes that do not care whether a file is on
a list. Where they are genuinely inapplicable, write `n/a — <reason>`; that
costs a line and catches the case where the author assumed inapplicability and
was wrong.

---

## The stages

**1. Proposal** — one page: the problem, why now, and what happens if we do
nothing. Routed to reviewers. May be rejected here cheaply; that
is the point of having the stage.

**2. Specification** — the template (`TEMPLATE.md`) is filled in.
**The spec is written before implementation**, and the sections that most
often catch defects — field contracts, trust-class matrix, regime analysis —
are written *before* the author has an implementation they are attached to.

**3a. Internal review** — at minimum one reviewer who did not write it.
**The author may not silently self-approve.** If no other session is available,
name the waiver and its holder in the spec; an unnamed waiver is
indistinguishable from nobody having looked. Reviewers have distinct standing:
- **dev** owns execution facts, code reality, and implementability;
- **research** owns semantics, trust-model consequences, and any public
  claim;
- **workflow-platform** owns consumer impact when the change is
  user-visible.

A reviewer's job is not only to find errors. It is to say **where they
think the author has drawn the wrong conclusion** — which found more real
defects this week than error-spotting did.

**3b. External review — REQUIRED for every full spec.** *(Quentin,
2026-07-31.)* Lightweight specs do not require it. "Full" means "touches a
guarded file", so the trigger is mechanical rather than a judgement call. Every
full spec goes to the trusted third-party reviewer before the decision in
stage 4.

**Why, specifically.** The two internal sessions catch different things and
both miss a third class. Over the past week the external reviewer caught,
among others: an instability band presented as a confidence interval; a
benchmark that would have rewarded systems for reproducing our own
ontology; a scored field supplied by the system being scored; and a defect
matrix that contradicted defence-in-depth. **None of those was a
code-reality error (dev's domain) or a semantics error (research's
domain).** They were failures to see our own frame — and insiders share the
frame, which is exactly why we cannot see it. Assume the external review
finds a *different class* of problem, not more of the same.

**Order matters: internal first, then external.** Sending an unreviewed
draft spends the scarcest resource on defects the fleet could have caught
itself. Every round this week that worked went internal → external.

**What to send.** The spec, plus a short brief naming **what we are least
sure of** — briefs produced sharper reviews than "please review this". If
the spec contains competitive-audit detail or unpublished findings, send a
**reviewer-safe copy** with those generalised, and say that you did.

**Carve-out — security hotfixes may ship first.** A fix for a live
user-affecting defect is not held for review; it ships, and the spec goes
for **retrospective** external review, with that fact recorded in the spec.
The 0.4.1 advisory fix went out ~35 minutes after escalation, and delaying
it would have been the wrong call. **The carve-out carries a deadline** —
`Spec-Retrospective-Due` below is mandatory and machine-checked, because a
deadline is what keeps this a carve-out rather than a door.

**If the reviewer is unavailable:** for a *lightweight* change, record the
unavailability and proceed. For a full spec touching stored state, trust
classes, or lifecycle, **wait** — that is the whole class of change this
process exists for, and it is the class where our internal review has
already been shown to be insufficient.

**4. Decision** — accepted, accepted-with-amendments, deferred, or
rejected, recorded in the spec itself with the date. **Amendments are
applied by search, not by memory:** when a claim is retracted, grep for it
and fix it at source. Citing a retraction list is not applying it — we did
exactly that this week and a retracted claim shipped into two downstream
documents.

**4b. Record the decision where a machine can read it.** Every spec carries a
`Spec-Status:` line directly under its title — one of `draft · in review ·
accepted · accepted-with-amendments · deferred · rejected`. It is the
**canonical** state; the header table carries narrative only, because two
sources drift.

> **Only `accepted` authorises implementation.** The CI gate refuses a commit
> that touches a guarded file and cites a spec in any other state, and fails
> closed on a spec with no status line or an unrecognised one.

`accepted-with-amendments` deliberately does **not** qualify. The amendments
must be resolved and the amended version approved, at which point the line
becomes `accepted`. Writing the spec, its tests, and its documentation while
it is still in draft is expected — that is what `Spec-Exception: docs-only`
and `test-only` are for.

*Why this exists:* the gate previously proved only that the cited file
**existed**. 0.4.5 shipped citing `0002-maintenance-provenance-invariant.md`
while that spec's own header read *"draft — internal review not yet
requested"*, and nothing objected. A process whose central control is a
citation must check what is being cited.

**5. Implementation** — the spec's invariants become executable checks
*in the same change*, not afterwards. The T1 fix shipped with
`engine.trust_canary_failures == 0` as a hard bench key; that is the
standard, not an exception.

**6. Verification before release** — every invariant in §6 of the spec has
a passing check; the regime analysis (§5) has a test that actually reaches
the regime; and the reproducer for any defect found in review is retained
as a regression test.

**7. Release note discipline** — the spec's §8 claim language is what goes
in the changelog. If the spec says a claim is unsupported, the changelog
does not make it.

---

## How a commit references its spec

`specs/check_spec_reference.py` runs in CI and requires every commit touching a
**guarded** file to carry one of the forms below. It is a **tripwire**: it
establishes that a reference is present and well-formed, **not** that the
process was followed. Read a green result accordingly.

```
Spec: specs/0007-generated-content-trust-class.md
```

```
Spec-Exception: docs-only
Spec-Exception-Reason: corrected a stale comment in graph.py
```

```
Spec-Exception: security-hotfix
Spec-Exception-Reason: GHSA-r7j7-5jq9-3f5q, cross-trust identity merges
Spec-Retrospective-Due: 2026-08-04
```

Exception categories: `docs-only` · `test-only` ·
`behavior-preserving-refactor` · `security-hotfix`. A reason is required, and
`security-hotfix` additionally requires the retrospective deadline.

**These must be real Git trailers**, which means the trailer block is the last
paragraph of the message and any wrapped value is **indented** on its
continuation lines. This is not pedantry: when the checker was hardened, *all
three* of our existing `Spec:` lines turned out not to be trailers at all — an
unindented continuation had broken every one, and the old regex accepted text
Git itself does not recognise.

**Changes to the process controls** — the checker, `PROCESS.md`, `TEMPLATE.md`,
and the CI workflow — require a `Process-Change: <reason>` trailer. That does
not *prevent* a change from weakening the gate and having the weakened gate
approve itself, since CI runs the checker from the branch's own tree; it removes
"nobody noticed" as an explanation. Closing it properly needs CODEOWNERS or a
base-branch-sourced workflow, which is repo settings rather than code.

---

## Rules that exist because we broke them

**R1 — One owner per document, and re-read before you edit.** We had a
three-way collision on the T2 design: one reviewer approved v1 while the author was
rewriting to v2, and the approval referred to a document that no longer
existed. If you are editing a shared spec, re-read it first; if you are
approving one, quote the version you approved.

**R2 — Before releasing, re-read open asks addressed to you since your last
entry.** The T1 review was posted at 02:45 and the release went out at
10:52 without it being seen. This is a two-minute check that would have
prevented an advisory.

**R3 — Consolidate rather than layer.** A document that has accumulated
five rounds of inline corrections becomes internally contradictory even
when every individual correction is right. Past three rounds, rewrite.

**R4 — Name the run beside every number.** Any measurement in a spec
carries the run or commit that produced it. We mixed figures from different
runs inside one table three separate times in three days.

**R5 — State what the change does *not* establish.** Specs claim more than
they support by default. §8 of the template exists to force the opposite.

**R6 — Verify postconditions.** A tool or migration that prints success
without checking its effect is not evidence of anything; assert the state
you claim to have created.

---

## What this process deliberately does not do

- It does not require sign-off from a particular *internal* session. If no
  second session is available, that is recorded and the change proceeds.
  **This does not extend to the external review (3b)**, which is required
  for full specs — with the security-hotfix carve-out above. The
  distinction is deliberate: internal reviewers are substitutable for one
  another, and the external reviewer is not substitutable for either.
- It does not gate refactors, docs, or tests.
- It does not ask for estimates, story points, or status meetings.

**Hard gates — these block regardless of schedule pressure:** an unanswered
question in the trust-class matrix (§3); **an empty invariant cell in the
untrusted-input table (§2c)** — "fails closed" on a predicate the code cannot
evaluate is not a control; a field whose documented contract the change
violates (§2); an invariant with no executable check (§6);
**or a full spec that has not had external review (3b), outside the
security-hotfix carve-out.**

**Regimes the tests cannot reach — two release classes, not one rule.**
*Stable (on by default):* an unreachable regime **blocks**. *Experimental (off
by default):* may ship with the regime stated as untested in §8, provided the
default is off and §8 says so. **Flipping an experimental default to on is
itself a change requiring a spec, and that spec's §5 must reach the regime** —
otherwise the split becomes a two-step route to shipping untested behaviour.
