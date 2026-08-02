#!/usr/bin/env python3
"""Generate every status summary in specs/0002 from specs/findings.py.

Five reviews, five deferrals, and each one found a status claim contradicting
another status claim in the same document. Every fix was a better hand-check;
the last was a phrase lint, which passed while "M1-M5, all closed" sat in the
header. A summary maintained beside the thing it summarises will drift, and
checking it harder does not change that.

So the summaries are generated between markers:

    <!-- GENERATED:name -->  ...  <!-- /GENERATED:name -->

`--write` rewrites them; `--check` fails on drift. Text inside a region is not
edited by hand -- edit `findings.py` instead.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = ROOT / "specs" / "0002-maintenance-provenance-invariant.md"
sys.path.insert(0, str(ROOT / "specs"))


def _regions() -> dict[str, str]:
    from findings import FINDINGS, REVIEWS

    open_f = [f for f in FINDINGS if f["disposition"] == "open"]
    unimpl = [f for f in FINDINGS if f["implementation"] == "none"]
    shipped = [f for f in FINDINGS if f["implementation"] == "shipped"]
    releases = sorted({f["release"] for f in shipped if f["release"]})

    ids = lambda fs: ', '.join(f"`{f['id']}`" for f in fs)

    rows = []
    for f in FINDINGS:
        owner = "this spec" if f["owner"] == "0002" else f"**`specs/{f['owner']}`**"
        impl = {"shipped": f"**yes** — {f['release']}",
                "none": "**no**", "n/a": "n/a"}[f["implementation"]]
        cur = f["current_defect"] or "—"
        if f["disposition"] == "open":
            cur = f"🔴 {cur}"
        adv = f" + {f['advisory']}" if f.get("advisory") else ""
        rows.append(f"| **{f['id']}** {f['title']} | {f['released_defect'] or '—'} | "
                    f"{cur} | {owner} | {impl}{adv} | `{f['test']}` |")

    ledger = ("| finding | released behaviour | current defect | owner | "
              "implemented? | test |\n|---|---|---|---|---|---|\n" + "\n".join(rows))

    summary = (
        f"**{len(FINDINGS)} findings · {len(shipped)} shipped "
        f"({', '.join(releases)}) · {len(unimpl)} unimplemented · "
        f"{len(open_f)} still open.**\n\n"
        f"**Unimplemented:** {ids(unimpl)}. **Open:** {ids(open_f)}.\n\n"
        f"*Two of the unimplemented — `M3` and `M4` — shipped in 0.4.5 as fixes "
        f"that do not hold.*")

    rv = " · ".join(f"{r['version']} ({r['findings']})" for r in REVIEWS)
    reviews = (f"**{len(REVIEWS)} external reviews, {sum(r['findings'] for r in REVIEWS)} "
               f"findings: {rv}.** The invariant was approved in every one; the "
               f"retrospective was deferred in every one.")

    return {"ledger": ledger, "summary": summary, "reviews": reviews}


def _apply(text: str, regions: dict[str, str]) -> str:
    for name, body in regions.items():
        pat = re.compile(rf"(<!-- GENERATED:{name} -->\n)(.*?)(<!-- /GENERATED:{name} -->)",
                         re.S)
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
        SPEC.write_text(want)
        print(f"regenerated {len(_regions())} region(s) in {SPEC.name}")
        return 0
    if a.check:
        if want != text:
            print(f"{SPEC.name}: a generated region is stale. Edit "
                  f"specs/findings.py, then run render_status.py --write. "
                  f"Status prose is derived; five reviews were deferred for "
                  f"maintaining it by hand.", file=sys.stderr)
            return 1
        print("status regions are in sync with specs/findings.py")
        return 0
    print(_regions()["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
