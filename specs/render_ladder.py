#!/usr/bin/env python3
"""Generate specs/0003's authority tables from specs/ladder.py.

v1 wrote the ASSISTANT row out by hand and inverted two of four. The rule is one
line of arithmetic; its consequences are computed here and rendered between
markers. `--check` fails on drift and runs in CI.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = ROOT / "specs" / "0003-supersession-authority.md"
sys.path.insert(0, str(ROOT / "specs"))


def _regions() -> dict[str, str]:
    from ladder import AUTH, CLASSES, author_matrix, divergent, effective_matrix

    order = " > ".join(f"{c.upper()} {AUTH[c]}" for c in CLASSES)
    rows = []
    for p, i, ok in author_matrix():
        note = "same class" if p == i else ""
        rows.append(f"| `{p}` | `{i}` | {'allow' if ok else '**BLOCK**'} | {note} |")
    matrix = (f"`{order}`\n\n"
              "| prior | incoming | result | |\n|---|---|---|---|\n" + "\n".join(rows))

    full, div = effective_matrix(), divergent()
    ex = []
    for pa, pf, ia, if_, ok in div[:6]:
        ex.append(f"| `{pa}`/`{pf or '—'}` | `{ia}`/`{if_ or '—'}` | "
                  f"{'allow' if ok else '**BLOCK**'} | differs from the author-only answer |")
    coverage = (
        f"**The rule reads `min(author, derived_from)`, so the matrix is over "
        f"the full product: {len(full)} rows, not {len(author_matrix())}.** "
        f"**{len(div)} of them give a different answer than authorship alone.** "
        f"Those are the decisions that *depend on* the derivation cap: omitting "
        f"`derived_from` collapses them toward the author-only result — verified, "
        f"**zero** of the {len(div)} have the cap absent on both sides.\n\n"
        "| prior author/derived | incoming author/derived | result | |\n"
        "|---|---|---|---|\n" + "\n".join(ex) +
        f"\n\n*(first {len(ex)} of {len(div)}; the test enumerates all "
        f"{len(full)})*")
    from ladder import blocked_states, same_block_contention, disclosure
    import collections
    sb = same_block_contention()
    shapes = collections.Counter((b[0], b[2]) for b in sb)
    srows = "\n".join(
        f"| `{p}` → `{i}` | {n} | both `mentionable` |"
        for (p, i), n in sorted(shapes.items(), key=lambda x: -x[1]))
    contention = (
        f"**{len(blocked_states())} of the 400 states are refused. "
        f"{len(sb)} of those put both edges in the SAME read partition** — the "
        f"cases a reader sees as two competing values. The rest are already "
        f"separated by the existing gate.\n\n"
        f"| author shape | states | partition |\n|---|---|---|\n{srows}\n\n"
        f"**v4 said \"exactly one pair\" and reasoned from the six author-only "
        f"blocked pairs.** Over the real product it is {len(sb)} states across "
        f"{len(shapes)} shapes: **a derivation cap by `assistant` or `system` "
        f"lowers effective authority without changing disclosure**, so the "
        f"author-only projection cannot see those contentions at all.")
    return {"matrix": matrix, "coverage": coverage, "contention": contention}


def _apply(text: str, regions: dict[str, str]) -> str:
    for name, body in regions.items():
        pat = re.compile(rf"(<!-- GENERATED:{name} -->\n)(.*?)(<!-- /GENERATED:{name} -->)", re.S)
        if not pat.search(text):
            raise SystemExit(f"no <!-- GENERATED:{name} --> region in {SPEC.name}")
        text = pat.sub(lambda m: m.group(1) + body + "\n" + m.group(3), text)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = SPEC.read_text()
    want = _apply(text, _regions())
    if a.write:
        SPEC.write_text(want); print(f"regenerated {len(_regions())} region(s)"); return 0
    if a.check:
        if want != text:
            print(f"{SPEC.name}: a generated authority table is stale. Edit "
                  f"specs/ladder.py and run --write. v1 hand-wrote this table "
                  f"and inverted two of four ASSISTANT cases.", file=sys.stderr)
            return 1
        print("authority tables are in sync with specs/ladder.py"); return 0
    print(_regions()["matrix"]); return 0


if __name__ == "__main__":
    raise SystemExit(main())
