#!/usr/bin/env python3
"""ONE strict implementation of a marker-delimited generated block.

EXTERNAL ROUND 16, R16-2. `review_lessons.py` located its generated block with
`text.split(BEGIN, 1)` and `rest.split(END, 1)` — the FIRST marker pair, with
no requirement that there be exactly one. The reviewer appended a second,
conflicting block claiming "999 external findings" and it passed `--check`, the
dedicated pytest gate, and full archive verification after repacking.

THE DEFECT IS NOT THAT THE PARSING WAS WEAK. It is that this project had
already solved this exact problem, for this exact reviewer, in
`skip_inventory.verify_collected` — written for 0014's round-15 finding, where
`split(begin, 1)` accepted an appended duplicate block and a boundary newline.
I wrote a second, weaker copy of a verifier that already existed, twelve
metres away, and the second copy had the same bug the first one was written to
fix. A count is a second copy of a list; an implementation is a second copy of
a rule, and it decays the same way.

So there is one implementation now and both carriers call it:

  * markers count ONLY as complete standalone lines (a marker mentioned
    mid-line, in prose or inside a code fence, is not a marker)
  * EXACTLY one opening and one closing marker — a duplicated complete block
    fails on the count, before any content is compared
  * the enclosed text is compared with NO normalization, so a boundary newline
    is a difference
  * the WRITE path is strict too: regenerating a carrier whose markers are
    already duplicated or damaged raises instead of silently rewriting the
    first block and leaving the second one lying, which is how the reviewer's
    mutation would have survived a `--write`.
"""
from __future__ import annotations


class BlockError(ValueError):
    """A carrier's generated block is missing, duplicated or damaged."""


def locate(text: str, begin: str, end: str, *, at_start: bool) -> tuple:
    """Return (begin_index, end_index, enclosed_text) or raise BlockError.

    `at_start` is REQUIRED and keyword-only, because it is a per-carrier policy
    and getting it silently wrong is EXTERNAL ROUND 19, R19-2: everything
    BETWEEN the markers was verified byte for byte, and the text BEFORE the
    opening marker was unconstrained, so prepending

        # What 9999 rounds actually found

    to the lessons document gave it a new title — the first thing a reader
    sees, and a markdown document's identity — while `--check`, the pytest gate
    and full archive verification all passed. Verifying the block is not
    verifying the document.

    COLLECTED legitimately carries a header above its block, so this cannot be
    unconditional; it is passed explicitly at both call sites instead of
    defaulted, so neither can acquire the wrong answer by omission.
    """
    if at_start and not text.startswith(begin + "\n"):
        raise BlockError(
            f"`{begin}` is not the first line of the carrier — text before a "
            f"generated block is text nobody checks (R19-2: a prepended "
            f"markdown title replaced the document's title and every check "
            f"still passed)")
    lines = text.split("\n")
    begins = [i for i, l in enumerate(lines) if l == begin]
    ends = [i for i, l in enumerate(lines) if l == end]
    if len(begins) != 1 or len(ends) != 1:
        raise BlockError(
            f"expected exactly one standalone `{begin}` and one `{end}`, found "
            f"{len(begins)} begin / {len(ends)} end — a duplicated block, a "
            f"missing marker, or a marker that is not on a line of its own "
            f"(R16-2: a second appended block claiming different numbers "
            f"passed every check)")
    b, e = begins[0], ends[0]
    if e <= b:
        raise BlockError("the end marker precedes the begin marker")
    return b, e, "\n".join(lines[b + 1:e])


def verify(text: str, begin: str, end: str, expected: str, *,
           at_start: bool) -> None:
    """Raise BlockError unless the carrier holds exactly one block == expected."""
    _b, _e, block = locate(text, begin, end, at_start=at_start)
    if block != expected:
        raise BlockError(
            "the enclosed block is not byte-identical to the generator's "
            "output (stale, hand-edited, or boundary-padded)")


def replace(text: str, begin: str, end: str, block: str, *,
            at_start: bool) -> str:
    """Return `text` with its ONE generated block replaced by `block`.

    Strict on the way in: a carrier that already carries two blocks cannot be
    repaired by rewriting the first one, so this raises and the operator is
    told which mutation to undo.
    """
    lines = text.split("\n")
    b, e, _ = locate(text, begin, end, at_start=at_start)
    return "\n".join(lines[:b + 1] + block.split("\n") + lines[e:])
