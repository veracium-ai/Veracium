#!/usr/bin/env python3
"""0011 — the round-1 fold, checked STRUCTURALLY rather than by substring.

P4 refuses closure evidence that greps for a diagnostic string, because a
no-op artifact containing that string satisfies it. These four findings are
folds into spec TEXT (the spec is a draft; there is no behaviour yet), so
the evidence checks the SHAPE the fold had to take — a table's row count, a
branch's totality, the ABSENCE of the contradictory phrasing that was the
defect — not that a sentence appears somewhere.

Run:  $PY specs/evidence/0011/check_round1_fold.py
"""
from __future__ import annotations

import pathlib
import re
import sys

SPEC = (pathlib.Path(__file__).resolve().parents[3]
        / "specs" / "0011-subject-scoped-entitlement.md")


def check_r1_1(t: str) -> list:
    """The policy function must be TOTAL and must include the sourced term
    v4 omitted — the omission was the finding, not the wording."""
    bad = []
    # the fenced block opens at the predicate definitions, not at `policy`
    block = next((b for b in re.findall(r"```\n(.*?)```", t, re.S)
                  if "policy(incoming, prior)" in b), None)
    if block is None:
        return ["R1-1: no policy function block"]
    for term in ("REFUSE", "ALLOW", "sourced(prior)",
                 "self_assertion(incoming)", "subject_class(prior) == OTHER"):
        if term not in block:
            bad.append(f"R1-1: the policy block omits {term!r}")
    if "otherwise" not in block:
        bad.append("R1-1: the policy block has no catch-all — a policy "
                   "function that is not total is v4's defect again")
    # the predicates must be DEFINED, not merely used
    for pred in (r"sourced\(e\)\s*:=", r"self_assertion\(e\)\s*:="):
        if not re.search(pred, t):
            bad.append(f"R1-1: {pred} is used but never defined")
    # and the rider must have the counter that makes it measurable
    if "would_refuse_broad" not in t:
        bad.append("R1-1: the rider has no allowed-cell counter, so the "
                   "broad rule's constituency is still unmeasurable")
    return bad


def check_r1_2(t: str) -> list:
    """The authentication claim must be GONE from every carrier that made
    it — the finding was a claim in three places, not one sentence."""
    bad = []
    if re.search(r"needs an unforgeable authorisation", t):
        bad.append("R1-2: the E5 requirement row still asserts an "
                   "unforgeable authorisation")
    if not re.search(r"INTEGRITY BINDING", t):
        bad.append("R1-2: the binding is not restated as integrity")
    if not re.search(r"PROTECTED HOST API", t):
        bad.append("R1-2: correct() is not stated as a protected host API")
    # the host's obligations must be a TABLE, not a sentence
    if not re.search(r"\| the host must \|", t):
        bad.append("R1-2: no host-obligation table")
    return bad


def check_r1_4(t: str) -> list:
    """ONE outcome for malformed input, and absence kept distinct."""
    bad = []
    if re.search(r"fails CLOSED to the `derived\(THIRD_PARTY\)`\s*\n?floor",
                 t):
        bad.append("R1-4: the contradictory flooring sentence is back")
    if "RAISES and NOTHING IS WRITTEN" not in t:
        bad.append("R1-4: the single outcome is not stated")
    if "ABSENCE IS A DIFFERENT INPUT" not in t:
        bad.append("R1-4: absence is not distinguished from malformed")
    raises = len(re.findall(r"\|\s*\*\*RAISES\*\*", t))
    if raises < 4:
        bad.append(f"R1-4: the grammar table names {raises} RAISES cells; "
                   f"the enumerated invalid inputs were 4")
    return bad


def check_r1_5(t: str) -> list:
    """Total AND exclusive: a numbered first-match table ending in a
    catch-all, carrying the two labels v4 had no cell for."""
    bad = []
    m = re.search(r"\| # \| condition \| label \|\n\|[-| ]+\|\n((?:\|.*\n)+)", t)
    if not m:
        return ["R1-5: no precedence table"]
    rows = [r for r in m.group(1).strip().splitlines() if r.startswith("|")]
    if len(rows) != 5:
        bad.append(f"R1-5: the precedence table has {len(rows)} rows, not 5")
    if "otherwise" not in rows[-1]:
        bad.append("R1-5: the last row is not a catch-all, so the labels "
                   "are not total — which was the finding")
    for label in ("QUARANTINED_CLAIM", "CONTESTED_CURRENT"):
        if not any(label in r for r in rows):
            bad.append(f"R1-5: {label} is missing — v4 had no cell for it, "
                       f"which is why an edge could match zero labels")
    if "FIRST MATCH WINS" not in t:
        bad.append("R1-5: first-match is not stated, so exclusivity is "
                   "not established")
    return bad


def main() -> int:
    t = SPEC.read_text()
    bad = (check_r1_1(t) + check_r1_2(t) + check_r1_4(t) + check_r1_5(t))
    if bad:
        print("0011 round-1 fold INCOMPLETE:\n  " + "\n  ".join(bad),
              file=sys.stderr)
        return 1
    print("0011 round-1 fold: R1-1, R1-2, R1-4 and R1-5 hold structurally "
          "(policy totality, claim withdrawal in every carrier, one outcome "
          "for malformed input, a 5-row first-match precedence table)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
