#!/usr/bin/env python3
"""Generate specs/STATUS.md — every spec at a glance, for Quentin and coordination.

GENERATED, deliberately. A hand-maintained status table is the thing this
project has spent a week removing: 0002 was deferred seven times, and every
round found a status claim contradicting another status claim.

Every column is derived:

  status        the `Spec-Status:` line in the file
  updated       `git log -1` on the file, or today if it is uncommitted --
                never a date anyone types
  internal /    specs/reviews.py
  external
  open Qs       question-table rows not struck through or marked resolved
  blocking      those marked blocking
  findings      specs/findings.py, by owner
  code          whether any finding this spec owns is shipped or committed

`--check` fails when STATUS.md is stale, so it cannot silently rot.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
OUT = SPECS / "STATUS.md"
sys.path.insert(0, str(SPECS))

STATUS = re.compile(r"^Spec-Status:\s*(\S[^\n]*)$", re.M)
TITLE = re.compile(r"^#\s+(.+)$", re.M)
QROW = re.compile(r"^\|\s*(~{0,2})\*\*([A-Z]{0,2}-?Q\d+[a-z]?)\*\*~{0,2}\s*\|(.*)$", re.M)


def _updated(path: pathlib.Path) -> str:
    """The last commit date of `path` -- or **today**, if the working tree's copy
    differs from what is committed.

    The fallback is the whole point. Reading `git log -1` alone makes this
    renderer's output depend on a commit that does not exist yet: edit a spec on
    a later day than its previous commit, regenerate (still yesterday's date),
    commit -- and the commit itself makes STATUS.md stale, because now
    `git log -1` says today. `--check` then fails in CI on **every** spec commit
    that crosses a day boundary, and the only escape is to regenerate and amend.

    Anticipating the date the pending commit will carry converges instead: the
    rendered value already says today, so committing does not change it. Found
    by running `--check` after committing `0007` v2 rather than only before."""
    dirty = subprocess.run(["git", "status", "--porcelain", "--", str(path)],
                           capture_output=True, text=True, cwd=ROOT).stdout.strip()
    if dirty:
        return datetime.date.today().isoformat()
    r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", str(path)],
                       capture_output=True, text=True, cwd=ROOT)
    # An archive is not a checkout: say so rather than printing a bare dash that
    # reads like "never updated".
    return r.stdout.strip() or "(no git)"


def _questions(body: str):
    """(open, blocking) — a row is open unless struck or marked resolved/moved."""
    # Matches ONLY a review-disposition section, not any heading containing
    # "review". The looser pattern also matched "Brief for the external
    # reviewer" and "Scope inherited from 0003's reviews", silently
    # truncating 27-61% of four specs -- a coverage loss inside a check that
    # exists to prevent coverage loss.
    body = re.split(
        r"^##+ \d+\w*\.\s*(?:Review history\b|[^\n]*review[^\n]*disposition\b)", body, flags=re.M | re.I)[0]
    open_q = blocking = 0
    for struck, _qid, rest in QROW.findall(body):
        low = rest.lower()
        # A `watch` row is a recorded trigger for a FUTURE condition, not an open
        # question blocking acceptance (round-6 contract D: 0003 Q2a was counted as
        # the sole open Q though the spec calls it "not an open question").
        if (struck or "resolved" in low or "moved" in low or "ruled" in low
                or "watch" in low):
            continue
        open_q += 1
        if "blocking" in low:
            blocking += 1
    return open_q, blocking


def render() -> str:
    from findings import FINDINGS
    from reviews import REVIEWS

    rows, totals = [], dict(internal=0, external=0, open_q=0, blocking=0)
    for f in sorted(SPECS.glob("[0-9][0-9][0-9][0-9]-*.md")):
        num = f.name[:4]
        body = f.read_text()
        st = (STATUS.search(body).group(1).strip() if STATUS.search(body) else "**MISSING**")
        title = TITLE.search(body).group(1) if TITLE.search(body) else f.name
        title = re.sub(r"^Feature spec:\s*", "", title)
        internal = sum(1 for r in REVIEWS if r["spec"] == num and r["kind"] == "internal")
        external = sum(1 for r in REVIEWS if r["spec"] == num and r["kind"] == "external")
        open_q, blocking = _questions(body)
        owned = [x for x in FINDINGS if x["owner"] == num]
        live = [x for x in owned if x["implementation"] in ("shipped", "committed")]
        code = (f"{len(live)}/{len(owned)}" if owned else "—")
        totals["internal"] += internal
        totals["external"] += external
        totals["open_q"] += open_q
        totals["blocking"] += blocking
        flag = "🔴 " if st in ("draft", "deferred") and blocking else ""
        rows.append(f"| **{num}** | {title} | `{st}` | {_updated(f)} | {internal} | "
                    f"{external} | {open_q} | {flag}{blocking} | {len(owned)} | {code} |")

    accepted = sum(1 for f in SPECS.glob("[0-9][0-9][0-9][0-9]-*.md")
                   if (m := STATUS.search(f.read_text())) and m.group(1).strip() == "accepted")
    return f"""<!-- GENERATED by specs/render_index.py — do not hand-edit.
     Regenerate: python3 specs/render_index.py --write
     Verify:     python3 specs/render_index.py --check -->

# Spec status

**{len(rows)} specs · {accepted} accepted · {totals['external']} external review
rounds · {totals['blocking']} blocking questions open.**

**Only `accepted` authorises implementation** (`PROCESS.md` §4a), and external
review is required to reach it. **{accepted} of {len(rows)} are accepted**, which
is the number that decides what can be built.

| # | spec | status | updated | int | ext | open Q | blocking | findings | code |
|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

**Review archives** — the exact package sent for each round, with a sha256 per
archive — are indexed in `specs/archives/INDEX.md`.

**Columns.** *updated* is `git log -1` on the file — or today, when the file has
uncommitted changes, since the commit that would carry that date does not exist
while this runs. Never a typed date. *int*/*ext*
are review rounds from `specs/reviews.py`. *open Q* counts question-table rows
not struck, resolved, moved, ruled or watch-only. *findings* is how many entries in
`specs/findings.py` this spec owns; *code* is how many of those are shipped or
committed.

**This table is generated.** Every fact in it is derived from the spec files,
`git`, `specs/findings.py` and `specs/reviews.py`. Nothing here is typed by
hand, because every status claim this project has hand-maintained has drifted —
0002 was deferred seven times and each round found one status statement
contradicting another.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    want = render()
    if a.write:
        OUT.write_text(want)
        print(f"wrote {OUT.relative_to(ROOT)}")
        return 0
    if a.check:
        if not OUT.exists() or OUT.read_text() != want:
            print(f"{OUT.name} is stale — run render_index.py --write", file=sys.stderr)
            return 1
        print("spec status index is current")
        return 0
    print(want)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
