#!/usr/bin/env python3
"""Fail if a withdrawn rule reappears as live specification text.

Four external reviews in a row found withdrawn rules still stated normatively,
each time after the document said they had been removed. The failure was always
the same shape: I searched for *my own edits* -- annotation markers, the
sections I remembered touching -- rather than for every place a rule is stated.
A search for one's own corrections cannot find text one never annotated.

A withdrawn phrase may still appear as HISTORY, which specs need in order to
explain what shipped. That requires an explicit marker in the same block:
`WITHDRAWN` or `OBSOLETE`, in capitals. Explicit, greppable, and impossible to
apply by accident -- unlike a heuristic, which is how the stale text survived.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
MARKERS = ("WITHDRAWN", "OBSOLETE")


def _normalise(text: str) -> str:
    """Markdown is presentation. `**same author**` and `same author` are the
    same claim, and a lint that misses one because of emphasis is theatre."""
    return re.sub(r"\s+", " ", re.sub(r"[*`_~]", "", text))


def _targets() -> list:
    out = sorted(SPECS.glob("*.md"))
    tests = ROOT / "tests"
    if tests.is_dir():
        out += sorted(tests.rglob("test_*.py"))
    return out


def _n_targets() -> int:
    return len(_targets())


def violations() -> list[tuple[str, str, str, str]]:
    from withdrawn_phrases import WITHDRAWN
    out = []
    # Specs AND the test tree. The seventh review found a GREEN test asserting
    # the M3 behaviour R3 forbids: a suite that asserts withdrawn behaviour
    # cannot verify the new invariant, and scanning only specs/ could not see it.
    for f in _targets():
        # 0010 was outside the review package's lint run because the recipe
        # never copied it in, so its stale X-Q1 and partition text survived a
        # pass that reported "no withdrawn phrases". The lint scans every spec
        # in the directory; the packaging must ship every spec it scans.
        # Review dispositions quote the text they retract. 0002 calls that
        # section "Review history" and 0003 calls it "First external review";
        # splitting on one spec's heading left the other's quotations live, so
        # the boundary is any "## <n>. ...review..." heading.
        body = re.split(r"^##+ \d+\w*\..*review",
                        f.read_text(), flags=re.M | re.I)[0]
        # paragraph granularity: a marker exempts the block it appears in
        for para in re.split(r"\n\s*\n", body):
            flat = _normalise(para)
            if any(m in para for m in MARKERS):
                continue
            for pat, why, where in WITHDRAWN:
                m = re.search(pat, flat, re.I)
                if m:
                    out.append((f.name, m.group(0)[:70], why, where))
    return out


def main() -> int:
    bad = violations()
    for name, phrase, why, where in bad:
        print(f"{name}: withdrawn phrase still stated as live text\n"
              f"    found:     {phrase!r}\n"
              f"    withdrawn: {why}\n"
              f"    current:   {where}", file=sys.stderr)
    if bad:
        print(f"\n{len(bad)} withdrawn phrase(s). Replace with the current rule, "
              f"or -- if it is deliberately quoted as history -- mark the block "
              f"WITHDRAWN or OBSOLETE.", file=sys.stderr)
        return 1
    print(f"no withdrawn phrases in {_n_targets()} spec/test file(s)")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(SPECS))
    raise SystemExit(main())
