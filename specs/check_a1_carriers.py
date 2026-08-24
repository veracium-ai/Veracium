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
  3. §4b-i's question TABLE is PARSED (round 19, A1-R19-1: anchoring
     a phrase to a pipe-prefixed line proved neither table membership
     nor exclusivity — an isolated pipe line outside the table, or a
     second contradictory row, both passed). The parsed properties:
     exactly ONE question/answer table in the section; exactly ONE
     supersession-question row in its body; that row uses the
     re-dispositioned wording; NO row carries the obsolete
     corrected-user-statement question. Comments AND fenced code
     regions are stripped first (rounds 18 and 20: a comment can carry
     the phrase, and a fenced block renders as code, not a table), and
     a candidate block is a table only with a valid two-column
     Markdown DELIMITER row (round 20, A1-R20-1: consecutive pipe
     lines with an ordinary row where the delimiter belongs are not a
     Markdown table). Fence removal is a STATE PARSER over the full
     fence grammar — backtick OR tilde markers of length >= 3, closed
     by a compatible marker of the same character at least as long
     (round 21, A1-R21-1: the regex removed exactly triple-backtick
     fences, and a tilde or four-backtick fence still rendered the
     table as code while passing).

Takes an optional path argument so the adversarial mutation matrix can
run it against mutated COPIES (the reviewer's requested artifact).
"""
from __future__ import annotations

import pathlib
import re
import sys

SPEC = (pathlib.Path(__file__).resolve().parent
        / "0024-authorship-before-structural-quarantine.md")


def _strip_fenced(text: str) -> str:
    """A1-R21-1: fence-state parsing over the FULL fence grammar —
    an opener is three-or-more backticks OR tildes at line start
    (leading whitespace allowed); the region closes only at a marker of
    the SAME character, at least as long, alone on its line. A regex
    for one literal fence form is a proxy for the grammar."""
    import re as _re
    out = []
    fence_char, fence_len = None, 0
    for line in text.splitlines():
        m = _re.match(r"\s*(`{3,}|~{3,})\s*\S*\s*$", line)
        if fence_char is None:
            if m:
                fence_char = m.group(1)[0]
                fence_len = len(m.group(1))
                continue
            out.append(line)
        else:
            if (m and m.group(1)[0] == fence_char
                    and len(m.group(1)) >= fence_len
                    and _re.fullmatch(r"\s*(`{3,}|~{3,})\s*", line)):
                fence_char = None
            # every line inside the fence is dropped
    return "\n".join(out)


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
    else:
        # comments stripped first (A1-R18-1's shadow class), then
        # FENCED CODE regions (A1-R20-1: a fenced table renders as
        # code), then the question table is PARSED — membership and
        # exclusivity, not phrase anchoring (A1-R19-1)
        section_b = re.sub(r"<!--.*?-->", "", mb.group(0), flags=re.S)
        section_b = _strip_fenced(section_b)
        blocks, cur = [], []
        for line in section_b.splitlines():
            if line.lstrip().startswith("|"):
                cur.append(line.strip())
            else:
                if cur:
                    blocks.append(cur)
                cur = []
        if cur:
            blocks.append(cur)
        delim = re.compile(r"\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|")
        tables = [b for b in blocks
                  if len(b) >= 2
                  and re.fullmatch(r"\|\s*question\s*\|\s*answer"
                                   r"\s*\|", b[0])
                  and delim.fullmatch(b[1])]
        if len(tables) != 1:
            problems.append(
                f"§4b-i holds {len(tables)} question/answer table(s), "
                f"expected exactly one — an isolated pipe-prefixed line "
                f"is not the table (A1-R19-1)")
        else:
            body = [row for row in tables[0][2:]]     # header + separator
            firsts = [row.split("|")[1].strip() if row.count("|") >= 2
                      else "" for row in body]
            sup = [f for f in firsts if "able to SUPERSEDE" in f]
            if len(sup) != 1:
                problems.append(
                    f"the question table holds {len(sup)} supersession-"
                    f"question row(s), expected exactly one — "
                    f"contradictory carriers are not a live header "
                    f"(A1-R19-1)")
            elif "re-dispositioned record" not in sup[0]:
                problems.append(
                    "the ONE supersession-question row does not use the "
                    "re-dispositioned wording")
            if any("corrected user statement" in f for f in firsts):
                problems.append(
                    "an obsolete corrected-user-statement question row "
                    "exists in the table — exclusivity violated "
                    "(A1-R19-1)")
    if problems:
        print("check_a1_carriers: FAILED\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    print("check_a1_carriers: §9 names all three replacement targets, "
          "the singular form is absent, the §4b-i header is live")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
