# 0038 oracle — verb registry v2, FROZEN

**Frozen 2026-09-07T17:44:33Z.** `verb_registry.py` sha16 `197e0976272eed3d`
(v1 was `7862ab9b1b9f49cb`, frozen 2026-09-07T15:25:54Z). Corpus unchanged at
`a239b296d126ca78`; 31 entries, total in both directions, 0 overlaps.

## TWO COPIES, TWO DIGESTS, ONE SET OF RULINGS (added at publication)

**The published copy of `verb_registry.py` is `54acc45ad818fa94`; the
research-tree copy is `197e0976272eed3d`.** They differ in **corpus-path
resolution only** — the published copy resolves the corpus in the repo layout
(`tests/eval/extraction_speech_act/`) as well as the research layout, because a
module that cannot find its corpus fails at import with a *path* error, which
reads as a broken file rather than a moved one.

**The RULINGS are byte-identical, and that is checkable rather than asserted:**
the `VERB_REGISTRY` tuple parsed from each copy digests to
**`af7823c7ac15152f`** in both. **The freeze is a freeze of the rulings**, and
they have not moved; the file digests differ because a digest names a **copy**,
not a set of rulings.

**Cite `54acc45a` for the published artifact and `af7823c7` for the rulings.**
A carrier that pins only a file digest cannot say whether a change touched a
ruling or a path.

## What changed, and why — both settled by measurement, not by re-reading

**1. `asked for`: REPORTED → PERFORMED.** v1 contradicted itself. It ruled
`announced` PERFORMED because *"announcing IS the act when the instruction was
to announce"*, and `asked for` REPORTED on reasoning that would have made
`announced` REPORTED too. **Both are completed speech acts whose instructed
act IS the speaking.** The human rater caught it; the cross-family model
independently agreed with the human. **2–1 against v1.**

**2. `stated a practice of/to`: PERFORMED, UNCHANGED — now marked CONTESTED.**
The model agreed with v1 on all three instances; the human dissented on all
three (2 reported, 1 committed). **2–1 for the ruling, so it stands — but a
rater disagreeing on every instance is what a genuine boundary case looks
like**, and it is carried into 0038's external round as a **named
disagreement**, not as a settled ruling.

## WHAT THIS FREEZE IS NOT

**v2's agreement with either rater is not a validation of v2, and no number
below should be quoted as one.** The §8 gate was computed against **v1** and
**PASSED** (per-class human-vs-model κ 0.857 / 0.804 / 0.728, every class over
the 0.60 threshold, n ≥ 20). Re-scoring v2 against the very labels that
motivated its change is **circular**; it is reported as a recomputation so the
effect of the edit is visible, and for no other purpose.

**The gate's statistic is human vs MODEL and is unaffected by this edit** — it
does not involve the registry at all. That is why the gate still stands after
the registry moved: the two raters' agreement with each other is what was
measured, and v2 changed neither rater's labels.

## The standing obligation

If `stated a practice` is ever re-adjudicated, it changes in a **v3** with the
reason recorded — never in place. The rule that produced v2 is the rule that
governs v2.
