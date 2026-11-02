#!/usr/bin/env python3
# Mutation-Matrix: tests/test_spec_gate.py::test_render_index_question_rows_mutation_matrix
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
from typing import NamedTuple, Optional

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
OUT = SPECS / "STATUS.md"
sys.path.insert(0, str(SPECS))

STATUS = re.compile(r"^Spec-Status:\s*(\S[^\n]*)$", re.M)
TITLE = re.compile(r"^#\s+(.+)$", re.M)
# A question row: a table row whose FIRST CELL begins with a question id. Groups: (strike, id, the rest of the row).
# The id may be bold or not, struck or not, back-ticked, and prefixed (`S-Q1`), and the cell may carry text after it
# (`~~**Q6** `actor`~~`). The first form needed the id in bold and so read 54 question rows in 16 specs as no rows at all,
# 0044's open, blocking Q8 among them (found by research, 2026-10-11). The strike group is the cell's own `~~`, never
# the bold, so an unstruck bold id cannot read as struck.
QROW = re.compile(r"^\|\s*[*`]*(~{1,2})?[*`\s]*([A-Z]{0,2}-?Q\d+[a-z]?)\b[^|\n]*\|(.*)$", re.M)
# A table's header row is its first row when a separator row (`|---|`) follows it.
SEP = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+\s*$")
# Disposition sections are history, not open questions. Matches ONLY a review-disposition section, not any heading
# containing "review": the looser pattern also matched "Brief for the external reviewer" and "Scope inherited from
# 0003's reviews", silently truncating 27-61% of four specs -- a coverage loss inside a check that exists to prevent
# coverage loss.
DISPOSITIONS = re.compile(r"^##+ \d+\w*\.\s*(?:Review history\b|[^\n]*review[^\n]*disposition\b)", re.M | re.I)


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


class QuestionRow(NamedTuple):
    """One question row. `index` is the row's line number in the spec's text (0-based), `header` its OWN table's header
    cells, lower-cased and stripped, or None when the row's block has no header row. A consumer that reads a column by
    name (the who-decides cell) reads it from `header`, so the header that made the row a question is the header it
    reads."""
    index: int
    line: str
    strike: str
    qid: str
    rest: str
    header: Optional[list]


def question_rows(text: str) -> list:
    """Every question row before the first disposition section, as QuestionRow.

    A row whose table has a header row with no `question` column is not a question, whatever its first cell says:
    0031's threat table numbers its vectors Q1-Q6, and 0048's closure table names Q4 as a finding it closed. A row in
    a block with no header row (0006's Q4 sits one blank line below its question table) is still counted."""
    lines = DISPOSITIONS.split(text)[0].splitlines()   # a prefix of text.splitlines(), so indices are the text's
    out = []
    for i, ln in enumerate(lines):
        m = QROW.match(ln)
        if not m:
            continue
        j = i
        while j > 0 and lines[j - 1].startswith("|"):
            j -= 1
        head = None
        if j + 1 < len(lines) and SEP.match(lines[j + 1]):
            head = [c.strip().lower() for c in lines[j].strip().strip("|").split("|")]
            if not any("question" in h for h in head):
                continue
        out.append(QuestionRow(i, ln, *m.groups(), head))
    return out


def row_state(row: QuestionRow) -> tuple:
    """(open, blocking) for ONE question row — a row is open unless struck or marked closed by a closure word. The
    table rule is question_rows' job: call this only on rows it returned."""
    low = row.rest.lower()
    # A `watch` row is a recorded trigger for a FUTURE condition, not an open
    # question blocking acceptance (round-6 contract D: 0003 Q2a was counted as
    # the sole open Q though the spec calls it "not an open question").
    # "ratified" (2026-10-10, the owner's accuracy check of this table): 0023 Q2 —
    # "v2 says NO … and the ruling is RATIFIED", pinned by N13 — was counted open
    # because only "ruled" was recognised. Swept first: it is the only question row
    # in any spec that mentions ratification, so this moves exactly that count.
    # WHOLE WORDS (2026-10-11): as substrings, "moved" matched "removed", so 0048's Q3 ("…or be removed?",
    # deferred and open) was skipped, and "unresolved" would read as "resolved". A sweep of every spec found
    # exactly one row moved by the change, 0048 Q3.
    # "scoped elsewhere" (2026-10-12, when the unbolded rows became visible): 0037 Q6 was answered by the owner
    # ("Scope Q6 as option b", a sibling spec) and its class cell says so; it is the only question row in any
    # spec carrying the phrase.
    if row.strike or re.search(r"\b(?:resolved|moved|ruled|ratified|watch|scoped elsewhere)\b", low):
        return False, False
    # "closed" (2026-11-02, adopting research's 0021 Q4 / 0023 Q3 closures, written `**CLOSED 2026-11-02: …` and
    # `` **`closed` 2026-11-02: … `` in the state/class cell; 0037 Q5's class cell already read `closed`): it counts
    # ONLY where the row's LAST cell — its disposition — BEGINS with it. As a word anywhere it would close 0022 Q8 and
    # 0037 Q4, two open rows whose prose says "fail-closed"; and "closed-form" is not a disposition.
    last = row.line.rstrip().rstrip("|").rsplit("|", 1)[-1].lower()
    if re.match(r"^[\s*`_]*closed(?![\w-])", last):
        return False, False
    return True, "blocking" in low


def _header_cell(body: str, name: str) -> str:
    """The text of the header row `| **<name>** | … |`, or '' when the spec has no such row."""
    m = re.search(r"^\| \*\*" + re.escape(name) + r"\*\* \|(.*)\|", body, re.M)
    return m.group(1) if m else ""


# "accepted at external round N" is a claim, so the round must be the one the ACCEPTANCE names: ACCEPTED, then
# "external"/"externally", then "round N", in one clause (no `;`, `(` or `)` between). The first form took the first
# "round N" anywhere in the Decision cell, and so stated 0051 "accepted at external round 2" from "R-II round 2 carries
# it to the external reviewer" in a cell recording an owner's-word acceptance (found auditing STATUS.md, 2026-11-02).
EXTERNAL_ACCEPTANCE = re.compile(r"\bACCEPTED\b[^;()|]*?\bexternal(?:ly)?\b[^;()|]*?\bround (\d+)", re.I)


def outside_ledger_note(num: str, body: str) -> str:
    """The note for an accepted spec with no external round in specs/reviews.py, read from its OWN header cells:
    an external acceptance round, else an external review the header records as owed, else an owner acceptance the
    header says had no external round, else the unresolved form."""
    dec = _header_cell(body, "Decision + date")
    m = EXTERNAL_ACCEPTANCE.search(dec)
    if m:
        return (f"**{num}** — accepted at external round {m.group(1)} per its own header; those rounds predate "
                f"`specs/reviews.py` and are recorded in the spec")
    if re.search(r"\bowed\b", _header_cell(body, "External review"), re.I):
        return (f"**{num}** — accepted, and its own header records its external review as owed (no round of it is "
                f"in `specs/reviews.py`)")
    if any(re.search(r"\bno external round\b", _header_cell(body, c), re.I)
           for c in ("Acceptance", "Decision + date", "External review")):
        return (f"**{num}** — owner-accepted with no external round, per its own header (PROCESS §4a's second "
                f"path)")
    return (f"**{num}** — no rounds in `specs/reviews.py` and no round named in its header (owner-accepted under "
            f"PROCESS §4a's second path, or a gap)")


def _questions(body: str):
    """(open, blocking) — counts of row_state over question_rows."""
    open_q = blocking = 0
    for row in question_rows(body):
        o, b = row_state(row)
        open_q += o
        blocking += b
    return open_q, blocking


def render() -> str:
    from findings import FINDINGS
    from reviews import REVIEWS

    rows, totals = [], dict(internal=0, external=0, open_q=0, blocking=0)
    # Rounds the ledger does not carry under a spec's own number are STATED,
    # so a `0` in the ext column cannot read as "never reviewed" (found when
    # the table was audited, 2026-09-05). 0029's joint rounds are HOUSED IN
    # 0030's ledger by research's ruling of 2026-09-04 (one ledger for the
    # joint review stream, each row naming its target) — a structural fact
    # like TRACKED, not a typed count. A spec accepted before the ledger
    # existed names its acceptance round only in its own header; the note
    # reads it back from that cell (outside_ledger_note) rather than typing
    # a number, and only a round the ACCEPTANCE names counts.
    LEDGER_HOUSED_IN = {"0029": "0030"}
    outside_ledger = []
    for f in sorted(SPECS.glob("[0-9][0-9][0-9][0-9]-*.md")):
        num = f.name[:4]
        body = f.read_text()
        st = (STATUS.search(body).group(1).strip() if STATUS.search(body) else "**MISSING**")
        title = TITLE.search(body).group(1) if TITLE.search(body) else f.name
        title = re.sub(r"^Feature spec:\s*", "", title)
        # Count DISTINCT round numbers, not rows: since the pre-seal ritual
        # (0005 era) a round can be recorded as a SENT row + a verdict row,
        # both kind="external" with the same round number — row-counting
        # inflated those specs (0019 showed 8 rounds for 4; the header total
        # claimed 179 for 165). Distinct-round counting is correct under
        # every recording convention in reviews.py (one-row-per-round,
        # SENT-edited-in-place, and SENT+verdict pairs).
        internal = len({r["round"] for r in REVIEWS
                        if r["spec"] == num and r["kind"] == "internal"})
        external = len({r["round"] for r in REVIEWS
                        if r["spec"] == num and r["kind"] == "external"})
        open_q, blocking = _questions(body)
        owned = [x for x in FINDINGS if x["owner"] == num]
        live = [x for x in owned if x["implementation"] in ("shipped", "committed")]
        code = (f"{len(live)}/{len(owned)}" if owned else "—")
        totals["internal"] += internal
        totals["external"] += external
        totals["open_q"] += open_q
        totals["blocking"] += blocking
        flag = "🔴 " if st in ("draft", "deferred") and blocking else ""
        if external == 0 and st == "accepted":
            if num in LEDGER_HOUSED_IN:
                outside_ledger.append(
                    f"**{num}** — its rounds are housed in **{LEDGER_HOUSED_IN[num]}**'s "
                    f"ledger (one ledger for the joint review stream; each row names its target)")
            else:
                outside_ledger.append(outside_ledger_note(num, body))
        rows.append(f"| **{num}** | {title} | `{st}` | {_updated(f)} | {internal} | "
                    f"{external} | {open_q} | {flag}{blocking} | {len(owned)} | {code} |")

    accepted = sum(1 for f in SPECS.glob("[0-9][0-9][0-9][0-9]-*.md")
                   if (m := STATUS.search(f.read_text())) and m.group(1).strip() == "accepted")
    from render_closure import TRACKED as closure_tracked, ledger_counts
    closure = ledger_counts()
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

**Per-finding closure ledger — {closure['total']} findings across the
{len(closure_tracked)} tracked specs** ({", ".join(closure_tracked)}), derived from
`specs/closure_findings.py` and validated against `specs/reviews.py` by
`specs/render_closure.py --check`. This total is rendered HERE ONLY (owner's
ruling, 2026-09-08): each tracked spec's `## Review closure` block carries its
own count and rows, never the cross-spec total, so a spec joining the set or
closing a finding rewrites no other spec's text.

**Rounds recorded outside the ledger** — so a `0` in *ext* is not read as
"never reviewed": {"; ".join(outside_ledger) if outside_ledger else "none"}.
A `draft` spec under the hand-assembled seal shows `0` here until acceptance:
that protocol writes its `specs/reviews.py` rows and one closure row per
finding AT the acceptance fold (0037, 0038, 0039), and until then the spec's
own Version cell and Prior chain, and its packages' `prior-rounds/`, are the
round record — so a returned draft is not "never reviewed" either.
The header total counts ledger rounds only.

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
