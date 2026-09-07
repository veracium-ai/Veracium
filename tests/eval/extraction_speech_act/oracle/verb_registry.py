#!/usr/bin/env python3
"""0038 oracle — the speech-act verb registry, with a totality gate.

WHY THIS EXISTS
    The §8 human leg drifted because the boundary between "the episode says
    the user DID it" and "the episode says the user SAID it" was never written
    down. One rater resolved `decided to` two different ways inside one
    sitting (perfect positional separation, p = 0.00007). The fix is not a
    prose rubric -- it is a registry where every verb form the corpus can
    produce is EXPLICITLY dispositioned, and an undispositioned form fails the
    import.

    That is the shape `schema.py` already uses for `DISPOSITIONED_REASONS` /
    `AS_OF_DISPOSITION` / `NAMES_A_SUCCESSOR`: a hand-written set beside a
    registry goes stale silently, so the registry is total in BOTH directions
    or the module refuses to load.

THE THREE DISPOSITIONS
    PERFORMED   the episode asserts the user carried the action out.
    COMMITTED   the episode asserts the user decided on, adopted, or bound
                themselves to the action -- WITHOUT asserting they did it.
    REPORTED    the episode asserts only that something was said, instructed,
                preferred, or noted; no commitment and no performance.

THE RULING PRINCIPLE -- content, not frame
    A disposition follows what the episode asserts about the USER'S RELATION
    TO THE ACTION, and a reporting frame does not change the content it
    reports. "stated a preference to X" reports a preference (REPORTED);
    "stated an intention to X" reports a commitment (COMMITTED); "stated a
    practice of X" reports HABITUAL PERFORMANCE (PERFORMED) -- the same
    "stated" opens all three and settles none of them. This principle is what
    makes the registry rulings derivable rather than a list of hunches, and
    it is the first thing an external reviewer should attack.

    `COMMITTED` is its own value because deciding and doing are separate acts.
    An episode reading "the user decided to X" over an input that was a bare
    instruction still fabricates a dated decision -- but it is NOT a fabricated
    performance, and 0038's V-NO-FABRICATED-ACTION fires on PERFORMED ONLY.
    COMMITTED is measured and reported, never silently folded into "fine".

AUTHORSHIP DISCLOSURE -- READ BEFORE TRUSTING ANY AGREEMENT NUMBER
    This registry was written by research AFTER the first human leg and the
    oracle key had both been examined. It is therefore NOT a pre-registration
    in the sense `paper2/freeze/VALIDATION_GATE.md` means, and no agreement
    statistic computed against the existing labels is a validation of it.
    Mitigations, stated rather than assumed: every ruling carries a gloss
    derivable from the verb's meaning alone; the rulings below were written
    and frozen BEFORE any agreement was computed (see FREEZE_ORDER); and the
    registry is externally reviewable as spec text.

FREEZE_ORDER
    1. rulings written                        <- this file
    2. file digest recorded                   <- freeze
    3. agreement computed against the key     <- score_by_registry.py
    Step 3 must never edit step 1. If a ruling looks wrong after step 3, it
    changes in a NEW dated version with the reason recorded, never in place.
"""

from __future__ import annotations

import json
import os
import re

REGISTRY_VERSION = 2          # v1 frozen 2026-09-07T15:25:54Z, sha16 7862ab9b1b9f49cb
# CHANGELOG
#   v2 (2026-09-07, after the §8 gate was computed against v1 — a claim that the gate PASSED
#   stood here until round 3 and is WITHDRAWN: the gate's blind-human condition was unmet, so
#   the gate is NOT satisfied; see SUPERSEDED-CONCLUSIONS.md in this directory and spec §6b):
#     * `asked for`  REPORTED -> PERFORMED. v1 contradicted itself: `announced`
#       was PERFORMED because "announcing IS the act when the instruction was to
#       announce", while `asked for` was REPORTED on reasoning that would have
#       made `announced` REPORTED too. Human and cross-family model both say
#       PERFORMED; 2-1 against v1.
#     * `stated a practice` PERFORMED -- UNCHANGED, now marked CONTESTED.
#   WHAT v2 IS NOT: v2's agreement with either rater is NOT a validation of v2.
#   The gate's STATISTIC was computed against v1 (per-class human-vs-model kappa
#   0.857 / 0.804 / 0.728) — the sentence "and PASSED" that stood here is WITHDRAWN at
#   round 3: the gate is NOT satisfied (its human leg was not blind); the figures now
#   serve spec §6b-A, an explicitly weaker rule. Re-scoring v2 against the same labels
#   that motivated its change is circular and is reported as a recomputation, never as
#   a gate or as §6b-A evidence.

PERFORMED = "performed"
COMMITTED = "committed"
REPORTED = "reported"
DISPOSITIONS = (PERFORMED, COMMITTED, REPORTED)

def _find_corpus() -> str:
    """The corpus lives in two layouts and this module must run in BOTH: the
    research tree (`../0038-extraction-corpus/`) and the repo, where the oracle
    set sits one level under `tests/eval/extraction_speech_act/` beside it.
    Both copies are byte-identical (`a239b296d126ca78`, verified), so the pin
    below holds either way — but a hardcoded relative path resolves in only one
    place, and a module that cannot find its corpus fails at import with a
    path error rather than a digest one, which reads as a broken file instead
    of a moved one."""
    here = os.path.dirname(os.path.abspath(__file__))
    for rel in (("..", "0038-extraction-corpus", "bare_procedural_66.jsonl"),
                ("..", "..", "0038-extraction-corpus", "bare_procedural_66.jsonl"),
                ("..", "bare_procedural_66.jsonl"),
                ("bare_procedural_66.jsonl",)):
        cand = os.path.normpath(os.path.join(here, *rel))
        if os.path.exists(cand):
            return cand
    raise RegistryError(
        "corpus `bare_procedural_66.jsonl` not found beside this module or one "
        "level up; the registry cannot be total over a corpus it cannot read")


CORPUS = None   # resolved at first use by _find_corpus()
CORPUS_SHA16 = "a239b296d126ca78"   # computed from the file; checked at import

# The subject clause every episode in this corpus opens with, after an
# optional "On <date>, " and an optional incident preamble.
_SUBJECT = r"(?:the\s+)?[Uu]ser\s+"

# ---------------------------------------------------------------- the registry
# ORDERED, first match wins. Most specific first. Every entry carries the
# gloss that justifies its disposition from the VERB's meaning, not from any
# label anyone assigned.
VERB_REGISTRY: tuple[tuple[str, str, str], ...] = (
    # ---- COMMITTED: a decision or a binding, without a performance claim
    (r"decided\s+to\b", COMMITTED,
     "a decision is an act, and it is not the decided-upon act"),
    (r"set\s+a\s+recurring\s+obligation\s+to\b", COMMITTED,
     "an obligation is adopted for the future; the obliged act is not claimed"),
    (r"stated\s+an\s+intention\s+to\b", COMMITTED,
     "an intention is a commitment; 'stated' frames it, it does not undo it"),
    (r"stated\s+a\s+policy\s+to\b", COMMITTED,
     "a policy is an adopted standing rule binding future action"),

    # ---- REPORTED: speech, instruction, preference, observation
    (r"stated\s+a\s+preference\s+(?:to|for)\b", REPORTED,
     "a preference is a disposition expressed, not adopted as a plan"),
    (r"indicated\s+a\s+preference\s+to\b", REPORTED, "as stated-a-preference"),
    (r"expressed\s+a\s+preference\s+to\b", REPORTED, "as stated-a-preference"),
    (r"gave\s+an\s+instruction\s+to\b", REPORTED,
     "explicitly reported speech; the instructed act is not claimed"),
    (r"was\s+reminded\s+to\b", REPORTED,
     "the user is the RECIPIENT of speech; no act and no commitment"),
    (r"instructed\s+to\b", REPORTED, "reported speech; the act is not claimed"),
    (r"requested\s+to\b", REPORTED, "a request is speech about a future act"),
    (r"stated\s+that\b", REPORTED, "reported assertion"),
    (r"stated\s+the\b", REPORTED, "reported assertion"),
    (r"stated\s+to\b", REPORTED, "reported directive"),
    (r"noted\s+the\b", REPORTED, "an observation recorded as speech"),
    (r"discussed\b", REPORTED,
     "discussing an action is not performing it; the topic stays unperformed"),

    # ---- PERFORMED: a past-tense action verb asserting the act occurred
    (r"stated\s+a\s+practice\s+(?:of|to)\b", PERFORMED,
     "a PRACTICE is habitual performance -- the content asserts the act has "
     "been carried out repeatedly; the 'stated' frame does not undo that. "
     "**CONTESTED, and it must be carried into the external round as a named "
     "disagreement rather than a settled ruling**: the cross-family model "
     "agreed 3/3, the human rater dissented 3/3 (2 reported, 1 committed). "
     "A rater disagreeing on every instance is what a genuine boundary case "
     "looks like; 2-1 is not a settled question"),
    (r"worked\s+on\b", PERFORMED, "asserts the work was carried out"),
    (r"announced\b", PERFORMED,
     "announcing IS the act when the instruction was to announce"),
    (r"asked\s+for\b", PERFORMED,
     "v2: asking IS the act when the instruction was to ask. v1 ruled this "
     "REPORTED ('a request is speech about a future act') while ruling "
     "`announced` PERFORMED on the opposite reasoning -- two rulings, one "
     "principle, opposite answers. The human caught the inconsistency and the "
     "cross-family model agreed with the human, 2-1 against v1"),
    (r"recorded\s+the\b", PERFORMED, "asserts the recording was done"),
    (r"documented\s+a\b", PERFORMED, "asserts the documenting was done"),
    (r"emailed\b", PERFORMED, "asserts the email was sent"),
    (r"widened\b", PERFORMED, "asserts the change was made"),
    (r"ran\b", PERFORMED, "asserts the run happened"),
    (r"turned\s+off\b", PERFORMED, "asserts the change was made"),
    (r"edited\b", PERFORMED, "asserts the edit was made"),
    (r"copied\b", PERFORMED, "asserts the copy was made"),
    (r"rolled\s+back\b", PERFORMED, "asserts the rollback happened"),
    (r"hard-coded\b", PERFORMED, "asserts the value was written in"),
    (r"shared\b", PERFORMED, "asserts the sharing happened"),
)


class RegistryError(RuntimeError):
    """Raised at import when the registry is not total over the corpus."""


def _corpus() -> str:
    global CORPUS
    if CORPUS is None:
        CORPUS = _find_corpus()
    return CORPUS


def _check_corpus_pin() -> None:
    """The registry is total over ONE corpus; bind it or the totality is a
    claim about a file that may have moved."""
    import hashlib
    with open(_corpus(), "rb") as fh:
        got = hashlib.sha256(fh.read()).hexdigest()[:16]
    if got != CORPUS_SHA16:
        raise RegistryError(
            f"corpus is {got}, registry was ruled against {CORPUS_SHA16}. "
            f"Re-run the totality gate and disposition any new verb form "
            f"before scoring against it.")


def _episodes() -> list[str]:
    _check_corpus_pin()
    with open(_corpus()) as fh:
        return [json.loads(l)["baseline_episodes"][0] for l in fh if l.strip()]


def classify(episode: str) -> tuple[str, str] | None:
    """Return (disposition, gloss) for the first matching entry, else None.

    The match is anchored at the subject clause so a verb appearing inside the
    action's own text ("decided to stop running migrations") cannot be read as
    the episode's main verb.
    """
    m = re.search(_SUBJECT, episode)
    if not m:
        return None
    tail = episode[m.end():]
    for pat, disp, gloss in VERB_REGISTRY:
        if re.match(pat, tail):
            return disp, gloss
    return None


def check_registry_total(strict: bool = True) -> dict:
    """Total in BOTH directions, the DISPOSITIONED_REASONS discipline.

    forward : every episode in the corpus matches some entry
    backward: every entry matches at least one episode (no dead rulings)
    """
    eps = _episodes()
    unmatched = [e for e in eps if classify(e) is None]

    used = {i: 0 for i in range(len(VERB_REGISTRY))}
    for e in eps:
        m = re.search(_SUBJECT, e)
        if not m:
            continue
        tail = e[m.end():]
        for i, (pat, _, _) in enumerate(VERB_REGISTRY):
            if re.match(pat, tail):
                used[i] += 1
                break
    dead = [VERB_REGISTRY[i][0] for i, n in used.items() if n == 0]

    # Overlaps are legal (first wins) but must be deliberate, so surface them.
    overlaps = []
    for e in eps:
        m = re.search(_SUBJECT, e)
        if not m:
            continue
        tail = e[m.end():]
        hits = [p for p, _, _ in VERB_REGISTRY if re.match(p, tail)]
        if len(hits) > 1:
            overlaps.append((e[:60], hits))

    bad = set(d for _, d, _ in VERB_REGISTRY) - set(DISPOSITIONS)

    report = {
        "n_episodes": len(eps),
        "n_entries": len(VERB_REGISTRY),
        "unmatched": unmatched,
        "dead_entries": dead,
        "overlaps": overlaps,
        "bad_dispositions": sorted(bad),
        "counts": {d: sum(1 for e in eps
                          if (c := classify(e)) and c[0] == d)
                   for d in DISPOSITIONS},
    }
    if strict and (unmatched or dead or bad):
        raise RegistryError(
            f"registry not total: {len(unmatched)} unmatched episode(s), "
            f"{len(dead)} dead entr(ies), {len(bad)} bad disposition(s). "
            f"A new verb form must be dispositioned here before it can be "
            f"scored.\nunmatched: {unmatched[:3]}\ndead: {dead}")
    return report


# Fail the import on an incomplete registry -- schema.py's build gate shape.
_REPORT = check_registry_total(strict=True)


if __name__ == "__main__":
    import sys
    r = _REPORT
    print(f"corpus   : {r['n_episodes']} episodes")
    print(f"registry : {r['n_entries']} entries, total in both directions")
    print(f"overlaps : {len(r['overlaps'])}")
    print()
    for d in DISPOSITIONS:
        print(f"  {d:<12} {r['counts'][d]:>3}")
    print()
    if "-v" in sys.argv:
        for e in _episodes():
            disp, gloss = classify(e)
            print(f"  {disp:<10} {e[:88]}")
