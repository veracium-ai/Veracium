#!/usr/bin/env python3
"""The ONE checker for the A1 consequence-carrier closures — shared by
the A1-R14-1 and A1-R15-1 ledger rows (round 16, A1-R16-1: the R15-1
row's inline grep printed `1` and exited happily, establishing none of
the three properties its prose claimed; a closure command maintained
per-row is a second copy of the check, and this file replaces both with
one named script per the R11-1 named-scripts rule).

Checks, all hard failures — each SCOPED to the section that carries
the property (round 17, A1-R17-1: the first version searched the whole
file for the §4b-i header, and the generated closure ledger QUOTES that
phrase — restoring the obsolete header while leaving the ledger passed;
presence-somewhere stood in for presence-at-the-site, the proxy class):
  1. §9 names ALL THREE co-owned `0025` replacement targets
     (§4b-iii step 1, §4b-iii step 2, §7b's row);
  2. §9 does NOT carry the obsolete singular summary (the literal
     'one-sentence' — §9's note deliberately describes rather than
     quotes it so this grep stays honest);
  3. §4b-i ITSELF opens its supersession question with the
     re-dispositioned-record row — asserted inside the isolated §4b-i
     section AND anchored to the start of an actual Markdown table row
     (round 18, A1-R18-1: a substring match within the section accepted
     the live fragment inside an HTML COMMENT while the obsolete row
     stood — mention is not use, the sealer's own placeholder lesson).

Takes an optional path argument so the adversarial mutation matrix can
run it against mutated COPIES (the reviewer's requested artifact).
"""
from __future__ import annotations

import pathlib
import re
import sys

SPEC = (pathlib.Path(__file__).resolve().parent
        / "0024-authorship-before-structural-quarantine.md")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    spec = pathlib.Path(argv[0]) if argv else SPEC
    text = spec.read_text()
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
    mb = re.search(r"^#### 4b-i\..*?(?=^#{2,4} )", text, re.M | re.S)
    if not mb:
        problems.append("§4b-i not found")
        section_b = ""
    else:
        # comments are stripped BEFORE matching: the round-18 fix anchored
        # to a line-start table row, and a multi-line HTML comment can put
        # the fragment at a line start — recursing the property rather
        # than waiting for that round
        section_b = re.sub(r"<!--.*?-->", "", mb.group(0), flags=re.S)
    if mb and not re.search(
            r"^\| \*\*is a re-dispositioned record then able to "
            r"SUPERSEDE\?\*\*",
            section_b, re.M):
        problems.append(
            "§4b-i does not open an ACTUAL table row (line-anchored "
            "`| **…`) with the re-dispositioned question — a quotation "
            "elsewhere (A1-R17-1's ledger shadow) or the fragment inside "
            "a comment in the section (A1-R18-1's comment shadow) does "
            "not count; mention is not use")
    if problems:
        print("check_a1_carriers: FAILED\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    print("check_a1_carriers: §9 names all three replacement targets, "
          "the singular form is absent, the §4b-i header is live")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
