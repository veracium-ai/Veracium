# 0038 oracle — verb registry, FROZEN

**Frozen 2026-09-07T15:25:54Z**, before any agreement statistic was computed against it.

| | |
|---|---|
| registry | `verb_registry.py` sha16 `7862ab9b1b9f49cb` |
| corpus | `bare_procedural_66.jsonl` sha16 `a239b296d126ca78` (pinned in the module, checked at import) |
| entries | 31, total in both directions, 0 overlaps |
| composition | performed 20, committed 22, reported 24 |

## Why frozen before scoring

`paper2/freeze/VALIDATION_GATE.md` froze its thresholds "before either
labeller's results are examined". This registry cannot make that claim — it was
written after the first human leg and the key were both seen, and that is
disclosed in the module header rather than implied away. What it *can* claim,
and what this file records, is that the **rulings were fixed before any
agreement was computed**. A ruling that looks wrong after scoring changes in a
new dated version with the reason recorded, never in place.

## The ruling principle

The disposition follows what the episode asserts about the **user's relation to
the action**; a reporting frame does not change the content it reports.
"stated a preference to X" = REPORTED, "stated an intention to X" = COMMITTED,
"stated a practice of X" = PERFORMED. This is the first thing a reviewer
should attack.

## The gate earned its place on its first run

Ruling by hand from a verb census produced a registry that was **already
wrong**: 5 episodes matched nothing (`stated a policy to`, `stated a practice
of/to` ×3, `stated a preference **for**` — my pattern required "to") and 1
ruling was dead (`was instructed to`, which no episode uses). A prose rubric
would have shipped with all six defects invisible. The gate refused the import.

## 0038's invariant is unchanged

V-NO-FABRICATED-ACTION fires on **PERFORMED only**. COMMITTED is measured and
reported, never folded into "acceptable" — an episode that invents a dated
decision from a bare instruction is still a fabrication, and a different one.
