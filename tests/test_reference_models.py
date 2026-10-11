"""The two package reference models, run as part of the suite (R1-10's MODEL checks, before design acceptance).

`specs/evidence/0044/run_model.py` encodes research's arity stage-1 rules (0044 v1.3, the 0003 and 0018 amendments);
`specs/evidence/0045/run_model.py` encodes the grounding x reply x confirmation rules (0045, 0047, the 0019
amendment). Each exits 0 only when every invariant holds AND every declared mutant is killed by EXACTLY the
invariant that names it. They are models, not product code (no `veracium` import): the product tests that bind the
same properties to shipped code belong to the implementation gate.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODELS = {"0044": ROOT / "specs" / "evidence" / "0044" / "run_model.py",
          "0045": ROOT / "specs" / "evidence" / "0045" / "run_model.py"}


@pytest.mark.parametrize("spec", sorted(MODELS))
def test_the_reference_model_passes_and_every_mutant_dies_by_its_own_invariant(spec, tmp_path):
    out = tmp_path / "results.json"
    r = subprocess.run([sys.executable, "-B", str(MODELS[spec]), "--out", str(out)],
                       capture_output=True, text=True, cwd=MODELS[spec].parent)
    assert r.returncode == 0, r.stdout + r.stderr
    res = json.loads(out.read_text())
    assert res["verdict"] == "PASS"
    assert res["invariants"] and all(v is True for v in res["invariants"].values()), res["invariants"]
    # rule zero: the model can fail — there is at least one mutant, each killed, each by its OWN invariant, and every
    # invariant owns at least one mutant (an invariant no mutant has ever failed is not shown to be able to fail)
    muts = res["mutants"]
    assert muts and all(m["killed_by_owner"] for m in muts.values()), muts
    assert set(res["invariants"]) <= {m["owner"] for m in muts.values()}, \
        sorted(set(res["invariants"]) - {m["owner"] for m in muts.values()})


@pytest.mark.parametrize("spec", sorted(MODELS))
def test_the_model_leaves_its_directory_untouched(spec, tmp_path):
    """The runner writes only where --out says, so a test run cannot dirty the tracked tree."""
    d = MODELS[spec].parent
    before = sorted(p.name for p in d.iterdir() if p.name != "__pycache__")
    subprocess.run([sys.executable, "-B", str(MODELS[spec]), "--out", str(tmp_path / "r.json")],
                   capture_output=True, text=True, cwd=d)
    assert sorted(p.name for p in d.iterdir() if p.name != "__pycache__") == before
