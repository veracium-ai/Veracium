#!/usr/bin/env python3
"""Generate each spec's `## Review closure` ledger FROM `specs/reviews.py`.

External round 4, R4-3. The closure sections had been hand-maintained beside
reviews.py and drifted three rounds running: "THREE ROUNDS" over four,
"FOUR ROUNDS" over five, a placeholder row that said it had been removed
sitting under the rows it denied, 0023 carrying no rows at all, and two
tables with incompatible column counts in one document.

Every one of those is the same defect the repo already knows by name — a
summary maintained independently of the thing it summarises — and
`findings.py`'s docstring says so in the first paragraph it ever had. The
reviewer's prescription is the one this repo reached years of rounds ago for
STATUS.md: derive it.

So the ledger is now DERIVED. `--check` fails when a spec's rendered block
differs from what reviews.py implies, which is the same contract
`render_index.py` has for STATUS.md.

The block is delimited by markers so the surrounding narrative — the counting
convention, the PROCESS §4a pointer — stays hand-written where it belongs.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
BEGIN = "<!-- GENERATED:review-closure -->"
END = "<!-- /GENERATED:review-closure -->"


def _rounds_for(spec: str):
    sys.path.insert(0, str(SPECS))
    from reviews import REVIEWS
    rows = [r for r in REVIEWS if r["spec"] == spec]
    return sorted(rows, key=lambda r: (r["kind"] != "internal", r["round"]))


def render(spec: str) -> str:
    rows = _rounds_for(spec)
    if not rows:
        return (f"{BEGIN}\n\n*No review round has been recorded for {spec} in "
                f"`specs/reviews.py`.*\n\n{END}")
    # A round has TWO rows in reviews.py: the pre-seal SENT dispatch and the
    # returning VERDICT. Counting rows would report six external rounds where
    # three happened — the same over-counting the "two bases" convention warns
    # about, arriving through a generator instead of a hand.
    def _is_sent(r):
        return r["verdict"].lstrip().upper().startswith("SENT")
    internal = len({r["round"] for r in rows
                    if r["kind"] == "internal" and not _is_sent(r)})
    external = len({r["round"] for r in rows
                    if r["kind"] == "external" and not _is_sent(r)})
    dispatched = len({r["round"] for r in rows if _is_sent(r)})
    out = [BEGIN, ""]
    out.append(f"**{internal} internal round(s) and {external} external "
               f"round(s) with a returned VERDICT are recorded for `{spec}`; "
               f"{dispatched} package(s) were dispatched** — counted from "
               f"`specs/reviews.py`, which is the source this block is "
               f"generated from. A round appearing here and not there, or the "
               f"reverse, is impossible by construction. **SENT rows are "
               f"dispatch records, not outcomes**, and are labelled below so "
               f"the two are never summed.")
    out.append("")
    # PER-ROUND dispatch/verdict index (R4-3) …
    out.append("| round | date | findings raised | verdict (compressed) |")
    out.append("|---|---|---|---|")
    for r in rows:
        v = r["verdict"].replace("|", "\\|")
        v = (v[:300] + "…") if len(v) > 300 else v
        label = "SENT" if _is_sent(r) else "verdict"
        out.append(f"| {r['kind']} {r['round']} ({label}) | {r['date']} | "
                   f"{r.get('findings', '—') if label == 'verdict' else '—'} | {v} |")
    # … and the PER-FINDING closure ledger PROCESS §4a actually requires
    # (R5-3: the round index above is a shorter verdict, not a closure).
    from closure_findings import CLOSURES
    mine = [c for c in CLOSURES if c[0] == spec]
    out.append("")
    out.append(f"**Per-finding closure ledger — PROCESS §4a.** {len(mine)} "
               f"finding(s) recorded for `{spec}`, each with a command you can "
               f"RUN. Generated from `specs/closure_findings.py`; a finding "
               f"without runnable evidence cannot be added, which is the point.")
    out.append("")
    out.append("| finding | round | what it was | closed in | evidence (runnable) |")
    out.append("|---|---|---|---|---|")
    for _spec, kind, rno, fid, summary, closed_in, evidence in mine:
        e = evidence.replace("|", "\\|")
        out.append(f"| **{fid}** | {kind} {rno} | {summary} | {closed_in} | "
                   f"`{e}` |")
    out.append("")
    out.append(END)
    return "\n".join(out)


def _apply(path: pathlib.Path, spec: str, write: bool) -> bool:
    text = path.read_text()
    block = render(spec)
    if BEGIN not in text or END not in text:
        return False           # spec has no generated block yet
    new = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), block,
                 text, flags=re.S)
    if new == text:
        return True
    if write:
        path.write_text(new)
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    stale = []
    for p in sorted(SPECS.glob("[0-9][0-9][0-9][0-9]-*.md")):
        spec = p.name[:4]
        text = p.read_text()
        if BEGIN not in text:
            continue
        if not _apply(p, spec, a.write):
            stale.append(p.name)
    if a.check and stale:
        print("review-closure blocks are stale — run "
              "`python3 specs/render_closure.py --write`:\n  "
              + "\n  ".join(stale), file=sys.stderr)
        return 1
    if a.write:
        print("review-closure blocks written")
    elif not stale:
        print("review-closure blocks are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
