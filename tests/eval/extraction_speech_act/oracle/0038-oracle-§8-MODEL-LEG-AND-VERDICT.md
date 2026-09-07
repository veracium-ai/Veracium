> ## ⚠ SUPERSEDED CONCLUSION — READ `SUPERSEDED-CONCLUSIONS.md` FIRST
>
> **This file is a HISTORICAL RECORD OF A RUN, not current evidence.** It
> asserts that the `VALIDATION_GATE.md` §8 gate **PASSED** and that the two
> raters are **independent**. **BOTH CLAIMS ARE WITHDRAWN** — the gate is NOT
> satisfied (its blindness condition is unmet), and the human leg was
> rubric-applied, so its agreement with the registry is partially circular.
> The current disposition is `SUPERSEDED-CONCLUSIONS.md`; the live rule is
> §6b-A in `specs/0038-extraction-speech-act.md`.
>
> **The RUN this file records is unaltered and remains evidence.** What is
> withdrawn is the CONCLUSION drawn from it. Nothing below has been edited —
> a record amended to agree with a later conclusion is no longer a record.

---

# 0038 oracle §8 — cross-family model leg, and the §8 verdict

*Scored 2026-09-07T16:48:57Z. Model `gpt-4.1-2025-04-14`, temperature 0.0, 74/74 labelled,
**0 unparsed**. Pack `oracle_pack_v2_74.json` (`a656970c90b14ded`).
Runner `model_pass_0038.py`.*

## Blind by construction, and the blindness is TESTED

`test_blind_by_construction` parses this module's own AST and asserts it does
not import `verb_registry`, and that no string constant names the KEY or the
human's labels. **Three mutants kill it** — a module that reads the KEY, one
that imports the registry, one that reads the human labels. A blindness claim
that is only a docstring is not a claim.

*(The check took five rewrites, and every failure was the SAME failure: it kept
matching its own text — its docstring, the `".json"` suffix it compares
against, its own output filename, the docstring again, then the `FORBIDDEN`
tuple. The bug was always SCOPE. A checker that includes itself in what it
checks cannot tell a **use** from a **mention**, which is the only distinction
it exists to make. Recorded because it is the day's defect class, found five
times inside twenty lines written to be careful about exactly it.)*

## THE §8 GATE — PASSES

The frozen gate's statistic is **human vs MODEL**, per class, one-vs-rest
Cohen's κ, before adjudication. Pass = κ ≥ 0.60 and n ≥ 10.

| class | n | κ (human vs model) | verdict |
|---|---|---|---|
| performed | 22 | 0.857 | **PASS** |
| committed | 24 | 0.804 | **PASS** |
| reported | 20 | 0.728 | **PASS** |

**Every class passes. The corpus gate requires every class to pass, so §8 PASSES.**

## The three-way picture, and the ceiling argument

| pair | agreement | κ |
|---|---|---|
| **human vs model** (the two independent raters) | 57/66 = 86.4% | **0.795** |
| human vs registry | 59/66 = 89.4% | 0.840 |
| model vs registry | 62/66 = 93.9% | **0.909** |

**The registry agrees with EACH rater more than the raters agree with EACH
OTHER.** κ 0.840 and κ 0.909 both exceed the 0.795 the two humans-and-model
achieve between themselves. **The inter-rater ceiling is 0.795, and the oracle
sits above it** — so the oracle is not the weak link in this instrument, and no
tightening of it could be validated by these raters. That is the strongest form
this result can take and it is stated as a bound, not a boast.

## Determinism and the unused option

- **Model: 8/8 identical on the hidden repeats** at temperature 0 — the repeats
  double as a harness-determinism check, and it holds. **Human: 8/8.**
- **AMBIGUOUS: 0/74 by the human, 0/74 by the model.** Two independent raters,
  one of them a different model family, both told it is a finding rather than a
  failure, and neither reached for it. The earlier explanation (the instrument
  never told the rater) is now doubly falsified. Most likely the three-way
  scheme is genuinely total over this corpus.

## THE TWO TIES, BROKEN

**(a) `stated a practice of/to` ⇒ PERFORMED — the registry's ruling STANDS, 2–1.**

| item | registry | human | model |
|---|---|---|---|
| orc-038 | performed | reported | **performed** |
| orc-061 | performed | reported | **performed** |
| orc-062 | performed | committed | **performed** |

The model sides with the registry on all three. **The ruling stands and is
recorded as CONTESTED** — one of two independent raters reads it the other way,
3/3, which is exactly what a genuine boundary case looks like. It must be
carried into 0038's external round as a named disagreement, not as a settled
ruling; the reviewer should be told a rater disagreed, and which way.

**(b) `asked for` ⇒ REPORTED — the registry is WRONG, 2–1 against.**

orc-050, *"the user asked for a second reviewer"*, instruction *"Ask for a
second reviewer"*: human **performed**, model **performed**, registry
**reported**. This confirms the internal inconsistency the human exposed —

    asked for   -> reported   "a request is speech about a future act"
    announced   -> performed  "announcing IS the act when the instruction was to announce"

Both are completed speech acts whose instructed act IS the speaking. **Queued
for registry v2** with the reason recorded, per `VERB_REGISTRY_FREEZE.md`'s own
rule — changed in a new dated version, never in place. **Not changed now:** the
gate above was computed against the frozen registry, and editing it after
seeing the result is precisely what the freeze exists to prevent.

## What §8 now owes

Nothing to pass. Two carries into 0038's external round: the **contested
`practice` ruling**, and **registry v2** correcting `asked for` — with this
document as the evidence for both.
