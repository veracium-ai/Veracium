"""Spec-Status accepted ⇒ a real `Review closure` section, not the template's
placeholder.

PROCESS.md §4a: "A spec at `accepted` carries a `## Review closure` section
with one row per review finding." `check_spec_reference.py` enforces the
HEADER's presence, but only on a guarded-src commit that cites the spec — so
an accepted spec whose closure section is still the template's draft text
("*n/a — draft; ... land here before `accepted`*") can sit unnoticed until
the next implementation commit trips over it. That is exactly how 0031
reached `accepted` (round 16, 2026-09-04) with the placeholder and turned
CI red at `d83775d`; 0030 reached `accepted` at joint round 18 the day
before with the same placeholder and is still carrying it.

Property, checked over EVERY accepted spec (the domain, not the motivating
case): at least one heading contains "Review closure" (0009/0010 use
per-round headings plus a "Review closure ledger" subsection; 0026/0031
carry the generated block; 0029/0032 are hand-written), and the text under
the LAST such heading is not the placeholder.

0030 is a STRICT xfail, not a name exemption: the row FAILS the suite the
moment its ledger lands, forcing this file to forget it. A debt that expires
by itself is a property; a name in an allow-list is not.
"""
from __future__ import annotations

import pathlib
import re

import pytest

SPECS = pathlib.Path(__file__).resolve().parent.parent / "specs"

# Accepted specs whose closure section is KNOWN to be the placeholder, with
# the reason and date. Strict: passing here is a failure — remove the row.
PLACEHOLDER_DEBT = {
    "0030": "accepted at joint round 18 (2026-09-03) with the template placeholder; "
    "its 18-round ledger is queued (research's ruling: one ledger, target "
    "artifact named per row) — remove this row when it lands",
}

PLACEHOLDER = re.compile(r"^\*n/a\s+[—-]\s+draft", re.I)
HEADING = re.compile(r"^#{2,3}\s.*review closure", re.I | re.M)


def _accepted_specs() -> list[pathlib.Path]:
    out = []
    for f in sorted(SPECS.glob("[0-9][0-9][0-9][0-9]-*.md")):
        m = re.search(r"^Spec-Status:\s*(\S+)", f.read_text(), re.M)
        if m and m.group(1) == "accepted":
            out.append(f)
    return out


def _closure_body(text: str) -> str | None:
    heads = list(HEADING.finditer(text))
    if not heads:
        return None
    start = heads[-1].end()
    # up to the next heading of the same-or-higher level, or EOF
    nxt = re.search(r"^#{1,3}\s", text[start:], re.M)
    return text[start : start + nxt.start()] if nxt else text[start:]


def _params():
    for f in _accepted_specs():
        num = f.name[:4]
        marks = ()
        if num in PLACEHOLDER_DEBT:
            marks = (pytest.mark.xfail(strict=True, reason=PLACEHOLDER_DEBT[num]),)
        yield pytest.param(f, id=num, marks=marks)


@pytest.mark.parametrize("spec", list(_params()))
def test_accepted_spec_carries_a_real_review_closure(spec: pathlib.Path) -> None:
    body = _closure_body(spec.read_text())
    assert body is not None, f"{spec.name}: accepted with no 'Review closure' heading"
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    assert lines, f"{spec.name}: accepted with an EMPTY Review closure section"
    assert not PLACEHOLDER.match(lines[0]), (
        f"{spec.name}: accepted but its Review closure is the template placeholder: "
        f"{lines[0][:80]!r}"
    )


def test_the_debt_register_names_only_accepted_specs() -> None:
    """A row for a spec that is no longer accepted (or no longer exists) is
    dead weight; a row for a spec that has its ledger fails strictly above."""
    accepted = {f.name[:4] for f in _accepted_specs()}
    stale = set(PLACEHOLDER_DEBT) - accepted
    assert not stale, f"debt rows for non-accepted specs: {sorted(stale)}"


def test_the_placeholder_pattern_matches_the_template_text() -> None:
    """The regex is a checker; this is its mutant: the exact 0030 text (and
    the two dash forms) must match, and a real closure opener must not."""
    assert PLACEHOLDER.match("*n/a — draft; the frozen §6a manifest digest")
    assert PLACEHOLDER.match("*n/a - draft")
    assert not PLACEHOLDER.match("**Owner-accepted — Quentin's word")
    assert not PLACEHOLDER.match("*(PROCESS §4a — one row per finding.)*")
