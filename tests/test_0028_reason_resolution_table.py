"""Mutation matrix for specs/evidence/0028/reason_resolution_table.py (P1 / CLAUDE.md
item 9): the generator asserts three properties at generation — TOTALITY,
REGISTRY ORDER, CLOSURE — and `--check <spec>` compares the spec's §4b table to
the enum AS DATA (V-CROSS). Each property gets the mutant a reviewer would plant,
executed against the real functions, plus the positive run against the spec.

# Mutation-Matrix: this file references reason_resolution_table.py by name so the
# evidence gate's pointer convention holds whether or not its glob sweeps the
# filename.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "specs" / "evidence" / "0028" / "reason_resolution_table.py"
SPEC = ROOT / "specs" / "0028-as-of-query.md"


def _load():
    spec = importlib.util.spec_from_file_location("reason_resolution_table", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_check_passes_against_the_spec_table_as_data():
    r = subprocess.run([sys.executable, str(GEN), "--check", str(SPEC)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "V-CROSS OK" in r.stdout + r.stderr


def test_mutant_eighth_reason_fails_totality():
    mod = _load()
    disp, reasons = mod.load()
    disp = dict(disp); disp["invented_reason"] = next(iter(disp.values()))
    with pytest.raises(SystemExit) as e:
        mod.assert_totality(disp, reasons)
    assert "TOTALITY FAILED" in str(e.value)


def test_mutant_shuffled_rows_diverge_from_the_spec_table():
    mod = _load()
    disp, reasons = mod.load()
    rs = mod.rows(disp, reasons)
    shuffled = mod.rows(disp, list(reversed(list(reasons))))
    assert shuffled != rs, "reversing the registry order must change the emitted rows"
    got = mod.parse_spec_table(SPEC.read_text(encoding="utf-8"))
    assert got == rs and got != shuffled


def test_mutant_unmapped_disposition_fails_closure():
    mod = _load()
    disp, reasons = mod.load()
    disp = dict(disp); first = list(reasons)[0]
    disp[first] = "quarantined_as_of_nowhere"
    with pytest.raises(SystemExit) as e:
        mod.rows(disp, reasons)
    assert "UNMAPPED" in str(e.value)


def test_parse_is_fail_closed_on_a_missing_table():
    mod = _load()
    assert mod.parse_spec_table("no table here\n| a | b |\n") == []
