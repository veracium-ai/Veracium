# CURRENT DISPOSITION of this evidence set — read before any file in it

*Research, 2026-09-07, answering external round-3 R3-1. **This file is the
evidence set's current disposition. Where any other file in this directory
disagrees with it, THIS FILE IS CURRENT AND THAT FILE IS A HISTORICAL RECORD OF
A RUN, not a live conclusion.***

---

## THE WITHDRAWN CONCLUSION

**`paper2/freeze/VALIDATION_GATE.md`'s §8 gate is NOT SATISFIED for 0038.** Its
§1 requires a **blind human labeller**. No blind human leg exists in this
oracle's classes:

- **Run 1 was blind and is UNCOMPUTABLE against these classes.** Its answer
  space was *performed / reported / neither*; `COMMITTED` did not exist until
  the registry did.
- **Run 2 was RUBRIC-APPLIED and NOT BLIND**, and its agreement with the
  registry is **partially circular** — the rater applied the registry's own
  principle to score the registry.

**What IS met is §6b-A**, an explicitly weaker rule defined in
`specs/0038-extraction-speech-act.md`, which borrows the gate's *statistic* and
**none of its authority**. §6b-A is not a substitute for the gate and the spec
says so.

**Withdrawn phrases, registered in `specs/withdrawn_phrases.py`:** *"the §8
gate PASSED"* and *"a named deviation, not waived"*.

## WHERE THE WITHDRAWN CONCLUSION STILL APPEARS, AND WHY EACH FILE IS TREATED AS IT IS

**Four files, not the two the reviewer named** — found by sweeping the whole
set rather than the files quoted in the finding.

| file | what it still asserts | treatment |
|---|---|---|
| `0038-oracle-§8-MODEL-LEG-AND-VERDICT.md` | "THE §8 GATE — PASSES"; "two independent raters"; "§8 PASSES"; "Nothing to pass" | **SUPERSESSION HEADER added.** Research's own write-up; a header marks it without altering the run it records |
| `0038-oracle-§8-human-leg-v2-RESULT.md` | "applied independently"; "Every class passes" | **SUPERSESSION HEADER added**, same reason |
| `RUBRIC.md` | tells the rater the pass establishes whether the principle "applied **independently**" reproduces the rulings | **NOT AMENDED, DELIBERATELY — see below** |
| `verb_registry.py` | its v2 CHANGELOG says *"after the §8 gate PASSED against v1"* | **owner is the dev seat** (its digest is pinned); flagged for the same treatment in the same commit |

### Why `RUBRIC.md` is NOT amended

**It is the instrument the rater was actually shown.** Amending it would make
the record of the run false — a reader could no longer tell what the rater was
told, which is the one thing that artifact exists to establish. **The claim it
contains is withdrawn; the fact that the rater was shown that claim is not.**

**That is precisely why the run's agreement is not independent:** the rubric
told the rater the registry's own principle, and then the run was scored against
the registry. **`RUBRIC.md` is evidence FOR the circularity, not against it**,
and leaving it unaltered is what makes that checkable.

## THE MECHANICAL CHECK — its data, so it is not a prose promise

**Rule:** every file in this set that contains a withdrawn phrase must EITHER
carry a supersession marker OR appear in `declared_exempt` below **with its
reason**. Nothing may carry a withdrawn phrase silently.

```json
{
  "withdrawn_phrases": [
    "§8 GATE — PASSES", "§8 gate PASSED", "§8 PASSES",
    "two independent raters", "applied independently",
    "Nothing to pass", "named deviation, not waived"
  ],
  "marker": "SUPERSEDED CONCLUSION",
  "declared_exempt": {
    "RUBRIC.md": "the instrument the rater was SHOWN; amending it would make the record of the run false, and its claim is evidence FOR the circularity",
    "SUPERSEDED-CONCLUSIONS.md": "this file — it quotes the withdrawn phrases in order to withdraw them"
  },
  "owned_elsewhere": {
    "verb_registry.py": "dev seat: its digest is pinned by the oracle manifest; the v2 CHANGELOG's 'after the §8 gate PASSED against v1' needs the same treatment in the pinning commit"
  }
}
```

**Why `declared_exempt` is data and not a sentence:** an exemption in prose is
an exemption nobody can check. **This is the shape `known_foreign_digests`
already uses in the oracle manifest**, and it is the same argument — a rule
that names its exceptions in a file a test can read cannot drift from the rule
a test enforces.

**And the marker convention is the house one, not a new one:** it is the same
use-versus-mention distinction `lint_withdrawn.py` already solves for specs
(a paragraph containing the marker is exempt), applied to a directory of
evidence rather than to a document.

## WHAT THIS SET DOES AND DOES NOT SUPPORT

**Supports:** a **blind** cross-family model leg (74/74, 0 unparsed, blindness
AST-tested with three leak mutants); a **rubric-applied** human leg with
intra-rater consistency measured directly (8 hidden repeats, 8/8); per-class
one-vs-rest κ between them of 0.857 / 0.804 / 0.728; registry v1 ↔ model κ
0.909 against a human↔model ceiling of 0.795.

**Does NOT support:** that the §8 gate passed; that the two raters are
independent of each other; that a human, unaided and blind, reproduces the
oracle. **The strongest honest claim rests on the BLIND MODEL leg alone.**

## WHAT WOULD CLOSE THE GAP

A blind human labelling by a rater who has **not seen this corpus**. The
project's one human rater has now labelled it twice and knows which class was
disputed, so blindness is unavailable from that seat — **form without
substance, which is the error the withdrawn claim already made once.**
