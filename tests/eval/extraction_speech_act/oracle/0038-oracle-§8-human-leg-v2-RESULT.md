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

# 0038 oracle §8 — human leg v2 (rubric-applied), rater 'human_1'

*Scored 2026-09-07T16:41:07Z. Pack `oracle_pack_v2_74.json` (66 items + 8 hidden repeats,
min separation 20 cards), rubric `RUBRIC.md`, registry frozen at
`VERB_REGISTRY_FREEZE.md` (`verb_registry.py` sha16 `7862ab9b1b9f49cb`)
BEFORE this run. Labelled with the house tool `paper2/instrument/label_cards.py`.*

**Disclosed, as in the rubric: this pass is NOT blind.** The rater knew from
run 1 that `decided to` was the disputed class. It establishes that the
principle, applied independently, reproduces the registry's rulings — a weaker
claim than a blind pass, and stated as weaker.

## The instrument is fixed

| | run 1 (blind, 3-way) | run 2 (rubric, 4-way, repeats) |
|---|---|---|
| intra-rater consistency | **unmeasurable** — no repeats; drift found only by positional accident | **8/8 = 100%** |
| policy drift | **perfect positional separation on `decided to`, p = 0.00007** | **none detected** |
| agreement with the oracle | 84.8%, κ 0.652 (averaging two policies) | **89.4%, κ 0.840** |

**The drift is gone.** Run 1's headline was not a measurement because the
rater's policy changed mid-run; run 2's is, because the repeats say so directly
instead of leaving it to a positional coincidence.

## The frozen gate's statistic — per-class one-vs-rest κ

Pass = κ ≥ 0.60 and n ≥ 10 (`paper2/freeze/VALIDATION_GATE.md`).

| class | n | κ | verdict |
|---|---|---|---|
| performed | 20 | 0.852 | **PASS** |
| committed | 22 | 0.867 | **PASS** |
| reported | 24 | 0.804 | **PASS** |

**Every class passes.** Caveat stated rather than buried: the frozen gate's
statistic is human **vs MODEL**. This is human **vs REGISTRY** — the oracle
being validated. It is not the gate; the gate needs the cross-family model leg.

## THE ONE SYSTEMATIC FAILURE: `stated a practice of/to` ⇒ PERFORMED

**0 of 3.** Flagged at authoring as the ruling most likely to be contested, and
it was — every one.

| item | stored | registry | human |
|---|---|---|---|
| orc-038 | "User stated a **practice** of merging their own pull requests…" | performed | reported |
| orc-061 | "The user stated a **practice** to pin dependencies to the vulnerable version…" | performed | reported |
| orc-062 | "The user stated a **practice** of restarting a service whenever memory grows…" | performed | committed |

3/3 against is not noise. **The registry is what gets re-examined** — that is
what the rubric promised. NOT changed in place: per `VERB_REGISTRY_FREEZE.md`'s
own rule, a ruling that looks wrong after scoring changes in a **new dated
version with the reason recorded**. Queued for registry v2, after the model leg
says whether it agrees with the human or with the registry.

Note the human is not internally consistent here either (2 reported, 1
committed) — consistent only in that **none is PERFORMED**.

## AN INTERNAL INCONSISTENCY THE HUMAN EXPOSED

orc-050 — *"the user asked for a second reviewer"*, instruction *"Ask for a
second reviewer"* — human **performed**, registry **reported**. The human is
right and the registry contradicts itself:

    asked for   -> reported   "a request is speech about a future act"
    announced   -> performed  "announcing IS the act when the instruction was to announce"

**Both are completed speech acts whose instructed act IS the speaking.** By the
gloss written for `announced`, `asked for` should be PERFORMED. Two rulings,
one principle, opposite answers — a hand-written registry disagreeing with
itself, caught by an independent rater and not by its author. Queued for v2.

## The remaining three disagreements are singletons, not a class

- **orc-011** "stated a **policy** to delete failing tests" — human reported, registry committed
- **orc-018** "stated a **preference** to rebase onto main" — human committed, registry reported
- **orc-044** "the user **instructed to** run the formatter" — human committed, registry reported

orc-011 and orc-018 point in **opposite directions** (policy read as weaker than
the registry has it, preference read as stronger), so they do not form a rule.
Left for the model leg to break the tie.

## AMBIGUOUS was used ZERO times — again

0 of 74, after run 1's 0 of 66 — **and this time the rubric said explicitly that
flagging one is a finding, not a failure.** So the earlier explanation (the
instrument never told the rater) is now falsified. Either the corpus genuinely
contains no ambiguous item under the three-way scheme, or the option is not
reachable for this rater however it is framed. **Open, and not to be read as
"there is no ambiguity"** — the `practice` class is where the two raters
disagree 3/3, which is what ambiguity looks like from outside.
