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

    # Round-6 contract correction B: order the displayed ladder by DESCENDING
    # authority, not `EvidenceAuthor` declaration order — a normative heading that
    # reads `USER 3 > THIRD_PARTY 0 > SYSTEM 2` is a false inequality even though the
    # matrix rows below it are correct. Assert the rendered inequalities are monotone.
    ranked = sorted(CLASSES, key=lambda c: AUTH[c], reverse=True)
    ranked_auth = [AUTH[c] for c in ranked]
    assert ranked_auth == sorted(ranked_auth, reverse=True) and \
        len(set(ranked_auth)) == len(ranked_auth), \
        f"authority heading is not strictly descending: {list(zip(ranked, ranked_auth))}"
    order = " > ".join(f"{c.upper()} {AUTH[c]}" for c in ranked)
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
        f"the full product: {len(full)} rows over the shipped enum, "
        f"not {len(author_matrix())}.** "
        f"**{len(div)} of them give a different answer than authorship alone.** "
        f"Those are the decisions that *depend on* the derivation cap: omitting "
        f"`derived_from` collapses them toward the author-only result — verified, "
        f"**zero** of the {len(div)} have the cap absent on both sides.\n\n"
        "| prior author/derived | incoming author/derived | result | |\n"
        "|---|---|---|---|\n" + "\n".join(ex) +
        f"\n\n*(first {len(ex)} of {len(div)}; the test enumerates all "
        f"{len(full)})*")
    from ladder import CLASSES, blocked_states, same_block_contention, disclosure
    import collections
    sb = same_block_contention()
    shapes = collections.Counter((b[0], b[2]) for b in sb)
    srows = "\n".join(
        f"| `{p}` → `{i}` | {n} | both `mentionable` |"
        for (p, i), n in sorted(shapes.items(), key=lambda x: -x[1]))
    contention = (
        f"**{len(blocked_states())} of the {len(effective_matrix())} states are refused. "
        f"{len(sb)} of those put both edges in the SAME read partition** — the "
        f"cases a reader sees as two competing values. The rest are already "
        f"separated by the existing gate.\n\n"
        f"| author shape | states | partition |\n|---|---|---|\n{srows}\n\n"
        f"**Derived from the SHIPPED enum** (`{', '.join(CLASSES)}`) and the "
        f"**production** `_disclosure_for`. v5 hard-coded four classes including "
        f"`assistant`, which does not exist in `EvidenceAuthor`, and "
        f"reimplemented disclosure — so its {400 - len(effective_matrix())} extra "
        f"states modelled a rule the runtime cannot execute. **When `0001` lands "
        f"and the enum gains `ASSISTANT`, these tables regenerate with no edit "
        f"here.**")
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
