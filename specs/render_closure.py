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
    counts = ledger_counts()
    out.append(f"**Per-finding closure ledger — PROCESS §4a.** "
               f"**{counts['per_spec'].get(spec, 0)} finding(s) for `{spec}`; "
               f"{counts['total']} across the pair** — every number here is "
               f"DERIVED from the rows below (external round 7, R7-1: the "
               f"manifest claimed 26 while the ledgers held 31, and 0023 said "
               f"9/9 above a 10-row table). Generated from "
               f"`specs/closure_findings.py` and validated against "
               f"`specs/reviews.py` on `(spec, kind, round, id)` EXACTLY — "
               f"extras, duplicates, wrong rounds and empty evidence all fail "
               f"the build.")
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


# ---------------------------------------------------------------------------
# COMPLETENESS AGAINST THE REVIEWS — external round 6, R6-3.
#
# `--check` proved the rendered block matched `closure_findings.py`. It could
# not prove `closure_findings.py` matched REALITY, so the ledger sat 12-of-15
# and 3-of-5 complete while the gate stayed green. That is the same defect as
# `verify_collected` comparing a block to an incomplete generator (R4-4) and
# `render_closure` replacing one hand-maintained twin with another (R5-3).
#
# So the finding ids are EXTRACTED from `reviews.py`'s own verdict text and
# every one must appear in the ledger. The reviews are written first and
# independently; a ledger validated against them cannot quietly fall behind.
FINDING_ID = None


def review_findings() -> dict:
    """The AUTHORITATIVE map {(spec, id): (kind, round)} — read from each review
    row's STRUCTURED `raised` list, never regex-extracted from prose.

    External round 7, R7-1: the previous version pulled ids out of verdict TEXT
    and compared SETS. Set equality cannot see a wrong round, an erased
    evidence string, a duplicate row, or a count that disagrees with the rows
    it counts — and the cross-spec regex ate `0022 R99-1` because it could not
    tell a reference to another spec from this spec's own finding. Structure
    replaces inference: the reviews declare their ids, and the ledger must
    match on `(spec, kind, round, id)` EXACTLY.
    """
    sys.path.insert(0, str(SPECS))
    from reviews import REVIEWS
    out = {}
    for r in REVIEWS:
        for fid in r.get("raised", []):
            key = (r["spec"], fid)
            if key in out and out[key] != (r["kind"], r["round"]):
                raise ValueError(
                    f"{key} is raised by two different rounds: {out[key]} and "
                    f"{(r['kind'], r['round'])} — a finding id must be unique "
                    f"within its spec")
            out[key] = (r["kind"], r["round"])
    return out


def completeness_problems() -> list:
    """EXACT equality, not containment. Every clause here is a defect R7-1
    demonstrated by mutating the ledger and watching the old check stay green."""
    sys.path.insert(0, str(SPECS))
    from closure_findings import CLOSURES
    import collections

    want = review_findings()
    problems = []

    seen = collections.Counter((c[0], c[3]) for c in CLOSURES)
    for key, n in sorted(seen.items()):
        if n > 1:
            problems.append(f"{key[0]} {key[1]}: {n} ledger rows for one finding")

    have = {(c[0], c[3]): (c[1], c[2]) for c in CLOSURES}
    for key in sorted(set(want) - set(have)):
        problems.append(f"{key[0]} {key[1]}: raised in reviews.py, NO ledger row")
    for key in sorted(set(have) - set(want)):
        problems.append(f"{key[0]} {key[1]}: in the ledger, raised by NO review "
                        f"row — every closure must close something")
    for key in sorted(set(want) & set(have)):
        if want[key] != have[key]:
            problems.append(
                f"{key[0]} {key[1]}: ledger says {have[key][0]} {have[key][1]}, "
                f"reviews.py says {want[key][0]} {want[key][1]}")

    for spec, kind, rno, fid, summary, closed_in, evidence in CLOSURES:
        if not (evidence or "").strip():
            problems.append(f"{spec} {fid}: EMPTY evidence — a closure with no "
                            f"runnable command closes nothing")
        if not (summary or "").strip():
            problems.append(f"{spec} {fid}: empty summary")
        if not (closed_in or "").strip():
            problems.append(f"{spec} {fid}: no carrier named")
    return problems


def ledger_counts() -> dict:
    """Counts DERIVED from the rows, so no prose can claim a different total —
    the manifest said 26 while the ledgers held 31 (R7-1)."""
    sys.path.insert(0, str(SPECS))
    from closure_findings import CLOSURES
    import collections
    per = collections.Counter(c[0] for c in CLOSURES)
    return {"total": len(CLOSURES), "per_spec": dict(sorted(per.items()))}


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
    if a.check:
        gaps = completeness_problems()
        if gaps:
            print("the closure ledger is INCOMPLETE against specs/reviews.py:\n  "
                  + "\n  ".join(gaps), file=sys.stderr)
            return 1
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


