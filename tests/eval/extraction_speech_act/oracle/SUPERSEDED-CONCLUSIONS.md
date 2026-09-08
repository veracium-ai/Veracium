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
| `verb_registry.py` | its v2 CHANGELOG *did* say *"after the §8 gate PASSED against v1"* | **MARKED — `WITHDRAWN` at lines 68 and 78**, in the round-4 pinning commit. It is **in this set and covered by the rule below**, not deferred to another seat |

### This table's registry row was itself stale for one assembly — the finding, one level down

**Round 4's first assembly (`18ad6b69…`, discarded before dispatch) shipped this
row saying the registry *"needs the same treatment"* — after the treatment had
been applied, in the same package.** The registry was marked before the pin; the
disposition file that exists to say what is current went on describing it as
outstanding. **A reviewer following this table would have found a registry
already marked and a disposition file saying it was not.**

**Both seal-check legs were green**, because nothing reads this file against the
files it describes. That is R3-1 exactly, one level down: round 3 found the
**spec** current and the **evidence** stale; round 4 found the **evidence**
current and the **disposition of the evidence** stale.

**The cause is a sentence shape, and it is the rule worth carrying: an entry
phrased as a TO-DO (*"needs the same treatment"*) goes stale the moment it is
done, and nothing can tell. An entry phrased as a STATE (*"carries `WITHDRAWN`
at lines 68 and 78"*) can be compared against the file.** Every entry below is
now phrased as a state.

**The `owned_elsewhere` key is deleted, not corrected.** It meant *"true, but
checked somewhere else"* — and *somewhere else* was no one. A category whose
members are exempt from the local rule and named in no other rule is where
staleness lives. The registry is in `must_carry_a_marker` with every other file.

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
  "markers_from": "specs/lint_withdrawn.py :: MARKERS — IMPORTED, never retyped here",
  "markers_extra": ["SUPERSEDED CONCLUSION"],
  "must_carry_a_marker": {
    "0038-oracle-§8-MODEL-LEG-AND-VERDICT.md": "carries a SUPERSEDED CONCLUSION header",
    "0038-oracle-§8-human-leg-v2-RESULT.md": "carries a SUPERSEDED CONCLUSION header",
    "verb_registry.py": "carries WITHDRAWN in the v2 CHANGELOG, at the two lines that stated the gate result"
  },
  "header_marker_governs_record": {
    "0038-oracle-§8-MODEL-LEG-AND-VERDICT.md": "a historical record of a run: its supersession header governs the whole document, because a record's body is not amended",
    "0038-oracle-§8-human-leg-v2-RESULT.md": "same — a record of a run, marked at its head and unaltered below"
  },
  "declared_exempt": {
    "RUBRIC.md": "the instrument the rater was SHOWN; amending it would make the record of the run false, and its claim is evidence FOR the circularity",
    "SUPERSEDED-CONCLUSIONS.md": "this file — it quotes the withdrawn phrases in order to withdraw them"
  }
}
```

**`header_marker_governs_record` is declared data for the same reason
`declared_exempt` is.** The marker rule is otherwise paragraph-granular, matching
`lint_withdrawn`'s exemption: a paragraph carrying a withdrawn phrase must carry
a marker itself. **These two files legitimately break that rule** — they are
records of runs, marked at the head and deliberately unaltered below, so a strict
same-paragraph rule would demand the amendment the round forbids.

**But "any file whose first paragraph happens to contain a marker is exempt
everywhere" is an exemption nobody declared**, and it would silently swallow the
next file that gains a header. **So the widening is listed, per file, with its
reason** — which is the argument this file already makes about exemptions in
prose, applied to itself.

**Measured, so the widening's cost is on the record rather than assumed:** the
two records carry withdrawn phrases in **7 and 2 paragraphs** respectively, of
which **1 each** carries a marker of its own. The blanket covers 7 paragraphs
that the strict rule would flag.

**No digests are repeated here.** The manifest already records a sha256 for every
file in this set and is the authority for them; a second carrier of the same
digest is a second thing to keep in step, which is the defect this round is
about. **What this file records is marker STATE, which a check establishes by
reading the file — a claim that cannot go stale behind your back, because
verifying it means opening the artifact.**

**`markers_from` is a pointer, not a copy,** for the same reason: `WITHDRAWN` and
`OBSOLETE` live in `lint_withdrawn.MARKERS`, and a JSON file that retyped them
would be a second definition free to drift from the enforced one.

**Why `declared_exempt` is data and not a sentence:** an exemption in prose is
an exemption nobody can check. **This is the shape `known_foreign_digests`
already uses in the oracle manifest**, and it is the same argument — a rule
that names its exceptions in a file a test can read cannot drift from the rule
a test enforces.

**And the marker convention is the house one, not a new one:** it is the same
use-versus-mention distinction `lint_withdrawn.py` already solves for specs
(a paragraph containing the marker is exempt), applied to a directory of
evidence rather than to a document.

## WHAT THE CHECK OVER THIS FILE DOES AND DOES NOT REACH

**`tests/test_oracle_set_disposition.py` reads the JSON above and holds the
marker-or-exemption rule over every file in this set.** It lives under
`tests/test_*.py` so the house gate reads *it*.

**Two limits, measured and stated rather than left to be discovered:**

**The rule has no live input in the present set.** Every file here that carries a
withdrawn phrase is either in `declared_exempt` (`RUBRIC.md`) or in
`header_marker_governs_record` (both run records). **Nothing currently reaches
the paragraph rule**, so the check's central property is exercised by its
negative controls and not by the real set. That is a check standing guard over a
future edit, which is a legitimate thing for a check to be — but *"it holds over
the set"* and *"it fired on the set"* are different claims and only the first is
true.

**And `verb_registry.py` contains no withdrawn phrase at all.** Its two gate
sentences were **rewritten and marked**, not left standing under a marker, so the
coverage rule finds nothing in it to cover; it is listed in
`must_carry_a_marker` by hand, as belt-and-braces, not because the rule derives
it.

## `lint_withdrawn` ITSELF STILL READS NONE OF THIS SET

**`lint_withdrawn.py` selects `specs/*.md` and `tests/test_*.py`. This set lives
at `tests/eval/extraction_speech_act/oracle/`. The overlap is ZERO of 18 files
— measured, not assumed.** So the house withdrawn-phrase gate does not read one
byte of this evidence set, and nothing else reads the JSON above.

**That gap is exactly what let the registry row above stand stale through a full
two-seat green**, and it is why the fix is a test rather than a better sentence.

**What changed is reach, not coverage.** `test_oracle_set_disposition.py` sits
inside the house gate's selection and reaches these 18 files **by reading the
JSON**; the gate's own file list is unchanged and still contains none of them.
Saying the gate now covers the evidence set would replace a stale claim with a
flattering one.

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
