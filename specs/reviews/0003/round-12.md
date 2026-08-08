# specs/0003 — external review round 12 (2026-08-08)

**Verdict: APPROVED FOR ACCEPTANCE. Broad pre-implementation external architecture review is
closed. No v15 design-review round is warranted.**

The architecture was approved at round 11, and v14 correctly made the two contract/process
corrections requested there. Both round-11 requirements are closed:

- **C1 (structured/rendered contention agreement) — CLOSED.** §4c-ii now defines three classes of
  fully-exposed member (the I6a-preserved prior; every grounded same-partition member I6 renders
  deterministically, even if unselected; any relevance-selected member); only an unseen fenced
  CROSS-partition challenger gets content-free linkage. A same-partition refused case
  (`USER works_as=CFO` vs refused `SYSTEM works_as=unemployed`) now has ONE consistent
  representation across `Recall.context`/`contested`/`edges` even on an unrelated query; the
  cross-partition unselected challenger still gets only content-free linkage. I6c names separate
  prospective tests for both.
- **L (acceptance ledger) — CLOSED under the evidence-loss ruling.** Rounds 1/2/5 carry individual
  findings + commit evidence (round 5 expanded to seven rows). Rounds 3/4 are recorded as
  verdict-only with an explicit evidence-loss ruling rather than fabricated findings — the correct
  response to irrecoverable historical evidence. `8c876da` is cited for the `0011` narrowing. The
  round-11 rows' "this revision" self-reference resolves via the package README to `40fa9de`.

## One required same-commit deletion (deletion-pass, no behaviour change)

v14 still contains a stale round-9-scope sentence:

> the plan drops the wiki cache in the same commit, and no `import`/`correct()`/lifecycle path
> needs to, because those do not create refusals.

That contradicts the approved round-10 rule that every transition INTO **or OUT OF** a
`live_refusal_contention` invalidates in the same mutation — `correct()`/lifecycle MUST invalidate
when they resolve an existing live refusal contention. Replace the sentence so it says: the plan
drops the cache when it FORMS a live refusal contention; non-refusal formation does not enter the
derived view; any path (incl. `correct()`/lifecycle) that transitions an existing
`live_refusal_contention` OUT of the live state invalidates under the symmetric rule below. This
changes no approved behaviour.

## Disposition

Remove/rewrite that one sentence in the SAME change that sets `Spec-Status: accepted`. Then:
end pre-implementation external architecture review; implement against I1–I9; treat future
counterexamples as implementation defects unless they reveal an actual contradiction in a frozen
invariant.

## Found-in-fix

The v13→v14 diff had no production-source or ordinary-test changes; the two corrections widened
nothing. The compiler-policy-digest carrier remains an implementation watch: if implementation
cannot satisfy the frozen cache invariant without a wiki column or third schema object, it must
return for a schema amendment rather than silently violating §7a.
