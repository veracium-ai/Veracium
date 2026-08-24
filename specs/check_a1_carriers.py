#!/usr/bin/env python3
"""The ONE checker for the A1 consequence-carrier closures — shared by
the A1-R14-1 and A1-R15-1 ledger rows (round 16, A1-R16-1: the R15-1
row's inline grep printed `1` and exited happily, establishing none of
the three properties its prose claimed; a closure command maintained
per-row is a second copy of the check, and this file replaces both with
one named script per the R11-1 named-scripts rule).

Checks, all hard failures:
  1. §9 names ALL THREE co-owned `0025` replacement targets
     (§4b-iii step 1, §4b-iii step 2, §7b's row);
  2. §9 does NOT carry the obsolete singular summary (the literal
     'one-sentence' — §9's note deliberately describes rather than
     quotes it so this grep stays honest);
  3. the §4b-i question header is the re-dispositioned form.
"""
from __future__ import annotations

import pathlib
import re
import sys

SPEC = (pathlib.Path(__file__).resolve().parent
        / "0024-authorship-before-structural-quarantine.md")


def main() -> int:
    text = SPEC.read_text()
    m = re.search(r"^## 9\..*?(?=^## 10\.)", text, re.M | re.S)
    problems = []
    if not m:
        problems.append("§9 not found between '## 9.' and '## 10.'")
        section = ""
    else:
        section = m.group(0)
    for target in ("§4b-iii step 1", "§4b-iii step 2", "§7b's"):
        if target not in section:
            problems.append(f"§9 does not name the co-owned replacement "
                            f"target {target!r}")
    if "one-sentence" in section:
        problems.append("§9 carries the obsolete singular summary "
                        "('one-sentence') — the round-14 defect restored")
    if "is a re-dispositioned record then able to SUPERSEDE" not in text:
        problems.append("the §4b-i question header is not the "
                        "re-dispositioned form")
    if problems:
        print("check_a1_carriers: FAILED\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    print("check_a1_carriers: §9 names all three replacement targets, "
          "the singular form is absent, the §4b-i header is live")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
