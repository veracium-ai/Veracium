"""SA-R1-C1 (the SQLite attestation amendment's round 1): 0013 §5f states the two write censuses separately, each with
its own fixture scope and its own counts, so neither instrument's figures read as the other's.

A TEXT PIN, stated as one. The correction was to the amendment's text ("Give each its own fixture scope and counts so
the gate's expected evidence is reproducible without conflating the two instruments"), and both censuses are
measurements at 58dd7f6, which no cell can recompute at HEAD. What this binds is that the text keeps the two scopes
apart: the closure table's mutant (specs/evidence/0007/closure_mutants.py, SA-R1-C1) folds them back into one.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = ROOT / "specs" / "0013-store-migrations.md"
LEAD = "are two censuses, each with its own fixture scope (v0.12, C1):"
STEP = "**The step table's census**"
PA1 = "**0013-PA1's census**"


def _bullets():
    text = SPEC.read_text(encoding="utf-8")
    assert text.count(LEAD) == 1, "0013 no longer introduces two censuses, each with its own fixture scope"
    block = text.split(LEAD, 1)[1]
    items = re.split(r"\n  - ", "\n" + block.split("\n\n", 1)[0])[1:]
    return {i.split(" covers", 1)[0]: " ".join(i.split()) for i in items if " covers " in i}


def test_sa_r1_c1_the_two_censuses_keep_their_own_scope_and_counts():
    b = _bullets()
    assert set(b) == {STEP, PA1}, f"the censuses stated are {sorted(b)}, not the step table's and 0013-PA1's"
    step, pa1 = b[STEP], b[PA1]
    assert "49 native ladder entries" in step and "432 writes" in step and "1,685 writes" in step, step
    assert "48 fixtures" in pa1 and "513 non-DDL writes" in pa1 and "1,645 DDL writes" in pa1, pa1
    for own, other in (("432", pa1), ("1,685", pa1), ("49 native", pa1), ("513", step), ("48 fixtures", step)):
        assert own not in other, f"{own!r} appears under the other census's scope"
