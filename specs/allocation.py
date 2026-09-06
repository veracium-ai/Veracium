#!/usr/bin/env python3
"""The spec-number ALLOCATION registry — one authoritative table of every
number: what holds it, its status, and which claims are RESERVATIONS rather
than drafts. Renders `specs/ALLOCATION.md`; `--check` refuses a stale render;
`tests/test_spec_allocation.py` refuses any NEW collision.

Why this exists (2026-09-06, external round 9 of the procedural design
round): the numbers 0033–0036 had been reserved for another arc two days
earlier, and the only record of that reservation was a sentence inside a
paragraph of a coordination-file row for a third spec. Two seats then
drafted, reviewed seven versions of, and merged `specs/0033-…` under the
reserved number without either checking, because there was nothing to check
against — the same defect class as a phantom citation: a claim with no
registry. The HOLDERS below are DERIVED from the tree (never hand-listed);
the RESERVATIONS are the one hand-maintained part, which is why each carries
its source and date and why the gate reads them as data.

Contested cells are RECORDED, not hidden: a collision that exists today is
named with its date and the ruling it awaits, and the gate refuses only a
collision that is not so recorded — the registry names the known state and
blocks the next one.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
OUT = SPECS / "ALLOCATION.md"
STATUS = re.compile(r"^Spec-Status:\s*(\S[^\n]*)$", re.M)
NUMBER = re.compile(r"^(\d{4})-")

#: RESERVATIONS — numbers claimed by an arc that has not drafted them. Each
#: carries WHO banked it, WHEN, WHERE (the carrier a reader can open), the
#: gate that must open before drafting, and — because a reservation is a
#: claim about the FUTURE that nothing in the tree can falsify — a REVIEW
#: TRIGGER: the date by which, or the condition under which, the claim is
#: reviewable. A reservation past its review is NAMED for the owner by
#: `allocation_problems()`, never auto-released (releasing is an allocation
#: decision, the owner's). Without the trigger a reservation whose arc dies
#: blocks its numbers forever with no pressure but memory (research,
#: 2026-09-06). Released only by an owner ruling recorded here.
RESERVATIONS: list[dict] = [
    {
        "range": ("0033", "0036"),
        "holder": "the self-learning concept review's decomposition "
                  "(0033 receipts / 0034 origin / 0035 admission / 0036) — LIVE, not "
                  "dormant: the concept note reached a second external review "
                  "2026-09-04 ('ready for owner adjudication, not yet for normative "
                  "drafting'); the owner approved its modifications and workflow, "
                  "fixing the sequence procedural memory → harness → self-learning; "
                  "and `0035 Requires: 0033 AND 0034` is an externally reviewed "
                  "dependency stated BY NUMBER — the numbers are load-bearing",
        "banked_by": "research",
        "banked_on": "2026-09-04",
        "carrier": "COORDINATION.md — a note inside the 0031 dev-queue row "
                   "(the reason this registry exists)",
        "gate": "ten owner decisions gate any drafting there (one partly taken: "
                "procedure-shaped records categorically outside 0035 v1's effect "
                "vocabulary)",
        "review_by": "2027-01-04",   # set by research, the banker, 2026-09-06 —
                                     # replacing dev's provisional 30-day date, which
                                     # would have fired mid-stage-one and trained
                                     # readers to ignore it
        "review_when": "self-learning is THIRD in the owner-approved sequence "
                       "procedural → harness → self-learning; review when the HARNESS "
                       "stage begins (the arc becomes next and its numbers are wanted), "
                       "or if the owner abandons or reorders the sequence, or by "
                       "review_by — whichever is first",
        "released": None,
    },
]

#: CONTESTED — a number both held by a file in the tree and inside a live
#: reservation, recorded with its date and the decision it awaits. The gate
#: refuses a collision NOT listed here; listing one is a disclosure, not a
#: permission.
CONTESTED: dict[str, dict] = {}   # 0033's collision CLEARED by the owner's renumber ruling (2026-09-06 → 0037);
                                  # the history lives in the commit that moved the file and in COORDINATION


def holders() -> list[dict]:
    """Every number the TREE holds — derived, never hand-listed."""
    rows = []
    for f in sorted(SPECS.glob("[0-9][0-9][0-9][0-9]-*.md")):
        m = NUMBER.match(f.name)
        if not m:
            continue
        text = f.read_text(encoding="utf-8")
        st = STATUS.search(text)
        title = text.splitlines()[0].lstrip("# ").replace("Feature spec: ", "", 1).strip() if text else ""
        rows.append({"number": m.group(1), "file": f.name,
                     "status": st.group(1).strip() if st else "MISSING",
                     "title": title})
    return rows


def _in_range(n: str, rng: tuple[str, str]) -> bool:
    return rng[0] <= n <= rng[1]


def _today() -> str:
    """ISO date, UTC; a module-level indirection so the gate's test can move
    the clock without patching the standard library."""
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).date().isoformat()


def allocation_problems() -> list[str]:
    """Every defect the registry can see. Empty means: no duplicate number in
    the tree, no UNRECORDED collision with a live reservation, no CONTESTED
    entry that is stale (its file gone or its reservation released), and
    every reservation carries its provenance."""
    problems: list[str] = []
    rows = holders()
    seen: dict[str, str] = {}
    for r in rows:
        if r["number"] in seen:
            problems.append(f"duplicate number {r['number']}: {seen[r['number']]} and {r['file']}")
        seen[r["number"]] = r["file"]
        if r["status"] == "MISSING":
            problems.append(f"{r['file']}: no Spec-Status line")
    live = [x for x in RESERVATIONS if x.get("released") is None]
    today = _today()
    for x in RESERVATIONS:
        for key in ("range", "holder", "banked_by", "banked_on", "carrier", "gate", "review_by", "review_when"):
            if not x.get(key):
                problems.append(f"reservation {x.get('range')}: missing {key} — a reservation must carry what would end it")
        if x.get("released") is None and x.get("review_by") and x["review_by"] < today:
            problems.append(
                f"reservation {x['range'][0]}–{x['range'][1]} is PAST REVIEW ({x['review_by']}; {x['review_when']}) — "
                f"named for the owner: release, renew with a new review_by, or draft")
    for r in rows:
        for x in live:
            if _in_range(r["number"], x["range"]) and r["number"] not in CONTESTED:
                problems.append(
                    f"{r['file']} takes number {r['number']} inside the live reservation "
                    f"{x['range'][0]}–{x['range'][1]} ({x['holder']}) and is NOT recorded as "
                    f"contested — record it or renumber")
    for n, c in CONTESTED.items():
        if n not in seen:
            problems.append(f"CONTESTED {n} names no file in the tree ({c['file']}) — stale entry")
        elif seen[n] != pathlib.Path(c["file"]).name:
            problems.append(f"CONTESTED {n} names {c['file']} but the tree holds {seen[n]}")
        if not any(_in_range(n, x["range"]) for x in live):
            problems.append(f"CONTESTED {n} is inside no live reservation — stale entry; remove it")
    return problems


def next_uncontested(after: str | None = None) -> str:
    """The first number above the tree's highest (or `after`) that no live
    reservation covers — the answer to "what number may a new spec take?"."""
    rows = holders(); top = max([r["number"] for r in rows] + [after or "0000"])
    n = int(top) + 1
    live = [x for x in RESERVATIONS if x.get("released") is None]
    while any(_in_range(f"{n:04d}", x["range"]) for x in live):
        n += 1
    return f"{n:04d}"


def render() -> str:
    rows = holders()
    out = ["# Spec allocation — every number, its holder, its status, and the reservations",
           "",
           "*Generated by `specs/allocation.py --write`; `--check` refuses a stale copy; "
           "`tests/test_spec_allocation.py` refuses any NEW collision. Holders are DERIVED "
           "from the tree; reservations are the hand-maintained part and carry their "
           "provenance. A new spec takes `allocation.py`'s next uncontested number.*",
           "",
           "## Held in the tree", "",
           "| number | file | status | title | note |", "|---|---|---|---|---|"]
    for r in rows:
        note = ""
        if r["number"] in CONTESTED:
            c = CONTESTED[r["number"]]
            note = f"**CONTESTED since {c['since']}** — inside a live reservation; awaits {c['awaits']}"
        out.append(f"| {r['number']} | `{r['file']}` | `{r['status']}` | {r['title']} | {note} |")
    out += ["", "## Reservations (claimed, not drafted)", "",
            "| range | holder | banked by | on | carrier | gate before drafting | review by / when | released |",
            "|---|---|---|---|---|---|---|---|"]
    for x in RESERVATIONS:
        out.append(f"| {x['range'][0]}–{x['range'][1]} | {x['holder']} | {x['banked_by']} | {x['banked_on']} | "
                   f"{x['carrier']} | {x['gate']} | {x.get('review_by', '—')} / {x.get('review_when', '—')} | {x['released'] or '—'} |")
    out += ["", f"**Next uncontested number for a new spec:** `{next_uncontested()}`", ""]
    problems = allocation_problems()
    out += ["## Registry state", "", "no problems" if not problems else "\n".join(f"- {p}" for p in problems), ""]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    text = render()
    if "--write" in argv:
        OUT.write_text(text, encoding="utf-8"); print(f"wrote {OUT.relative_to(ROOT)}")
    if "--check" in argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("ALLOCATION.md is stale — run allocation.py --write"); return 1
        print("ALLOCATION.md is current")
    problems = allocation_problems()
    for p in problems:
        print("PROBLEM:", p)
    if "--next" in argv:
        print(next_uncontested())
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
