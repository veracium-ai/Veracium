"""0011 §4b — the policy oracle's own mutation matrix.

EVIDENCE-R4-1 (external round 4): the previous oracle enumerated source and
origin but never passed them to the decision, and its invariance check
re-called `policy()` instead of comparing the EMITTED cells — so a planted
source-conditional ALLOW in the emission exited 0 while the oracle printed
that source identity was invariant. Both of the reviewer's attacks from that
round are planted here as standing tests, so the oracle cannot quietly
regress to certifying its inputs instead of its subject.

0011 is a DRAFT; this exercises evidence artifacts only (the
test_0026_relay_lexicon.py precedent).
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVID = ROOT / "specs" / "evidence" / "0011"

sys.path.insert(0, str(EVID))
import policy_matrix as PM                                   # noqa: E402


def test_the_oracle_is_clean_on_the_shipped_predicate():
    r = subprocess.run([sys.executable, str(EVID / "policy_matrix.py")],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def test_a_variance_planted_in_the_emission_is_caught():
    """The round-4 attack, standing: one USER/None/OTHER cell flipped to
    ALLOW only when the incoming source is caller-chosen. The oracle judges
    the STREAM, so an injected stream with the variance must fail — if this
    ever passes, the oracle has gone back to recomputing instead of
    consuming its own output."""
    mutated = []
    flipped = 0
    for row in PM.cells():
        a, d, sc, src_in, *rest, out = row
        if (a is PM.A.USER and d is None and sc == "OTHER"
                and src_in == "caller-chosen-anything" and flipped == 0):
            row = (a, d, sc, src_in, *rest, "ALLOW")
            flipped += 1
        mutated.append(row)
    assert flipped == 1, "the attack cell was never emitted"
    bad = PM.problems(stream=mutated)
    assert bad, ("a source-conditional ALLOW planted in the emitted stream "
                 "was NOT caught — the oracle is certifying its inputs "
                 "again (EVIDENCE-R4-1)")
    assert any("equal authority" in b or "uniformly REFUSE" in b
               for b in bad), bad


def test_a_duplicate_hiding_a_missing_cell_is_caught():
    """The round-5 attack, standing: replace one emitted cell with a
    duplicate of another. The COUNT stays 1,440 while a source/origin
    combination silently vanishes — cardinality-preserving omission. The
    oracle compares the emitted key set to the exact expected Cartesian
    set and rejects duplicates separately, so both halves of the swap are
    named."""
    rows = list(PM.cells())
    mutated = rows[:]
    mutated[7] = mutated[3]
    assert len(mutated) == len(rows), "the attack must preserve cardinality"
    bad = PM.problems(stream=mutated)
    assert any("MORE THAN ONCE" in b for b in bad), (
        "a duplicated cell key was not reported (EVIDENCE-R5-1)")
    assert any("NEVER EMITTED" in b for b in bad), (
        "the cell the duplicate displaced was not reported missing "
        "(EVIDENCE-R5-1)")


def test_an_alien_cell_key_is_caught():
    """A key outside the declared domain is neither missing nor duplicate —
    it is an emission the domain never promised, and it must be named."""
    rows = list(PM.cells())
    a, d, sc, si, sp, oi, op, out = rows[0]
    rows[0] = (a, d, sc, "a-source-no-domain-declares", sp, oi, op, out)
    bad = PM.problems(stream=rows)
    assert any("outside the declared domain" in b for b in bad)


def test_a_truncated_stream_is_caught():
    """Dropping cells silently narrows the domain — the count is checked."""
    partial = list(PM.cells())[:100]
    assert PM.problems(stream=partial), (
        "a 100-cell stream passed a 1440-cell domain")


def test_the_fold_checker_refuses_a_shadowed_helper(tmp_path):
    """The round-4 shadowing attack, standing: a dangerous `sourced()`
    reading source_id followed by a benign redefinition. The dependency
    closure carries EVERY definition of a name, so the read in the first
    body is still a read."""
    sys.path.insert(0, str(EVID))
    import check_round1_fold as CF
    spec = (ROOT / "specs" / "0011-subject-scoped-entitlement.md").read_text()
    attacked = spec.replace(
        "             and self_assertion(incoming)\n    ALLOW    otherwise",
        "             and sourced(prior)\n"
        "             and self_assertion(incoming)\n    ALLOW    otherwise",
        1).replace(
        "## 13. Changes in v7",
        "```\nsourced(e) := e.provenance.source_id is not None\n```\n\n"
        "```\nsourced(e) := False\n```\n\n## 13. Changes in v7", 1)
    assert attacked != spec, "the attack failed to apply"
    bad = CF.check_r1_1(attacked)
    assert any("source_id" in b for b in bad), (
        "a source read shadowed by a benign redefinition passed the "
        "dependency closure (EVIDENCE-R4-1)")
    # the pristine control
    assert not any("source_id" in b for b in CF.check_r1_1(spec))


def test_the_import_cell_runs_the_production_adapter():
    """The import-flattened cell is measured, not asserted: the default
    path flattens the author (0005) and the decision follows it; restore
    preserves the author and the refusal returns."""
    rows = PM.import_flattened_cells()
    by_mode = {m: (auth, dec) for m, auth, dec in rows}
    assert by_mode["default"][0] is not PM.A.USER
    assert by_mode["default"][1] == "ALLOW"
    assert by_mode["restore"][0] is PM.A.USER
    assert by_mode["restore"][1] == "REFUSE"
