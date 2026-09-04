"""The joint arc's ONE ledger (0029 + 0030 + the seam, housed in 0030) —
the properties its two structured side-tables promise.

Research's ruling (2026-09-04): one ledger, each finding row naming the
artifact it targeted; full uniform treatment (verdict rows with structured
`raised`, SENT rows, a closure row per finding). The render and the
completeness gate already bind rows ↔ raised ids; this file binds the two
tables that ruling added:

  closure_findings.TARGETS      finding id → target artifact
  test_spec_gate TEXT_ONLY      finding id → why the closure is text, not a test

Each is checked as a PROPERTY over the whole 0030 row set — totality both
ways, values in the declared enum, and the exempt rows still citing an
openable fold — plus the mutant each check exists to catch.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "specs"))

import closure_findings  # noqa: E402
import reviews  # noqa: E402


def _rows():
    return [c for c in closure_findings.CLOSURES if c[0] == "0030"]


def test_the_target_table_is_total_over_the_0030_rows_and_nothing_else():
    ids = {c[3] for c in _rows()}
    assert ids, "no 0030 closure rows"
    assert set(closure_findings.TARGETS) == ids, (
        f"TARGETS ≠ 0030 rows: missing {sorted(ids - set(closure_findings.TARGETS))}, "
        f"extra {sorted(set(closure_findings.TARGETS) - ids)}")
    bad = {k: v for k, v in closure_findings.TARGETS.items()
           if v not in closure_findings.TARGET_VALUES}
    assert not bad, f"targets outside the enum: {bad}"


def test_every_target_value_is_used_and_the_shipped_rows_name_their_carrier():
    """The enum is not decorative: each value labels at least one row, and a
    `shipped` row's closure text names the shipped file it changed (the seam
    surfaced fixes to revocation_sweep.py / the 0022 oracle — the enum has
    the value so the row can be honest about the carrier)."""
    used = set(closure_findings.TARGETS.values())
    assert used == set(closure_findings.TARGET_VALUES), (
        f"unused target values: {set(closure_findings.TARGET_VALUES) - used}")
    for c in _rows():
        if closure_findings.TARGETS[c[3]] == "shipped":
            assert re.search(r"revocation_sweep\.py|reference_revocation\.py|vectors\.json", c[5]), (
                f"{c[3]} is `shipped` but its closure names no shipped carrier: {c[5][:100]!r}")


def test_the_text_only_exemptions_are_exactly_the_git_show_rows():
    """The P4 gate's TEXT_ONLY table (per-finding, not a round cutoff) must
    name EXACTLY the 0030 rows whose evidence is `git show` — a row that
    gained a test must leave the table (a stale exemption hides a mechanism
    behind text), and a `git show` row missing from it fails P4 loudly."""
    src = (ROOT / "tests/test_spec_gate.py").read_text()
    block = re.search(r"TEXT_ONLY = \{(.*?)\n    \}", src, re.S).group(1)
    exempt = set(re.findall(r"'(0030-R\d+-\d+)':", block))
    git_show = {c[3] for c in _rows() if c[6].startswith("git show ")}
    assert exempt == git_show, (
        f"exempt but tested: {sorted(exempt - git_show)}; "
        f"git-show without exemption: {sorted(git_show - exempt)}")
    for c in _rows():
        if c[3] in exempt:
            m = re.match(r"git show ((?:[0-9a-f]{7} )+)-- (.+)$", c[6])
            assert m, f"{c[3]}: text-only evidence must cite fold sha(s) and a spec path: {c[6]!r}"
            for path in m.group(2).split():
                assert (ROOT / path).exists(), f"{c[3]} cites a spec path that does not exist: {path}"


def test_every_round_has_one_sent_and_one_verdict_row_and_raised_matches():
    rows = [r for r in reviews.REVIEWS if r["spec"] == "0030"]
    sent = {r["round"] for r in rows if r["verdict"].lstrip().upper().startswith("SENT")}
    verd = {r["round"] for r in rows if not r["verdict"].lstrip().upper().startswith("SENT")}
    assert sent == verd == set(range(1, 19)), (sent, verd)
    raised = {fid for r in rows if "raised" in r for fid in r["raised"]}
    assert raised == {c[3] for c in _rows()}
    # round 18 is the acceptance: it raised nothing, and says so structurally
    r18 = [r for r in rows if r["round"] == 18 and "raised" in r][0]
    assert r18["raised"] == [] and "ACCEPTED" in r18["verdict"]


def test_the_r7_f2_row_does_not_credit_the_fold_it_names_as_unchanged():
    """Both seats verified (2026-09-04) that the round-7 F2 spec half — the
    boolean `restricted` at §4a-i against the three-valued carrier — is
    unchanged from v15 through v30 ACCEPTED and was never re-raised. The
    ledger must say so and must NOT cite 0226dd1 as its closure: this is the
    ledger doing its job on ourselves, and a tidying pass must not undo it."""
    row = [c for c in _rows() if c[3] == "0030-R7-2"][0]
    assert "UNCHANGED" in row[5] and "0226dd1" in row[5]
    assert "does NOT cite 0226dd1" in row[5]
    assert "0226dd1" not in row[6], "the evidence column must not cite 0226dd1"


def test_mutants():
    """The checks above are checkers; these are their mutants."""
    t = dict(closure_findings.TARGETS)
    t.pop(next(iter(t)))
    assert set(t) != {c[3] for c in _rows()}          # a dropped row is seen
    assert "process" not in closure_findings.TARGET_VALUES  # the enum is the five ruled values
    assert not re.match(r"git show ((?:[0-9a-f]{7} )+)-- (.+)$", "git show -- specs/x.md")  # sha-less git show refused
