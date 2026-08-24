#!/usr/bin/env python3
# Mutation-Matrix: tests/test_collected_header.py::test_candidate_results_record_binds_the_measurement
"""Generate `candidate_results.json` by RUNNING the shipped candidate
patch — never by editing a number.

Round-11 finding (0001 external, 2026-08-24): `CANDIDATE_README.md`
said "20 passed" while the branch ran 21, because the count was
carried forward and incremented by inference — inside a README whose
own text claims its measurement is "re-run, never carried". The
reviewer's instruction: derive the values from a structured result
record so future count drift fails sealing.

So the numbers have exactly one producer. This script:
  1. materialises the CURRENT tree at HEAD into a temp directory,
  2. applies `candidate.patch` (the shipped artifact, by its own bytes),
  3. runs the focused candidate suite and the full suite in that tree,
  4. writes `candidate_results.json` binding patch sha256, base commit,
     both measurements, the sorted FAILURE SET, and the environment.

`specs/check_candidate_results.py` then refuses any disagreement
between the record, the shipped patch, and the README's stated
figures — in the sealer's extraction checks, so a stale count cannot
reach a package.

Usage:  python specs/evidence/0001/measure_candidate.py [--write]
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
PATCH = HERE / "candidate.patch"
RECORD = HERE / "candidate_results.json"
FOCUSED = "tests/test_0001_candidate.py"

_TAIL = re.compile(
    r"(?:(?P<failed>\d+) failed, )?(?P<passed>\d+) passed"
    r"(?:, (?P<skipped>\d+) skipped)?")


def _tail(output: str) -> dict:
    """The LAST pytest summary line, parsed — never a typed count."""
    lines = [l for l in output.strip().splitlines() if " passed" in l
             or " failed" in l]
    if not lines:
        raise SystemExit("measure_candidate: no pytest summary line found")
    m = _TAIL.search(lines[-1])
    if not m:
        raise SystemExit(f"measure_candidate: unparsed tail {lines[-1]!r}")
    return {"passed": int(m.group("passed")),
            "failed": int(m.group("failed") or 0),
            "skipped": int(m.group("skipped") or 0)}


def measure() -> dict:
    if not PATCH.exists():
        raise SystemExit("measure_candidate: no candidate.patch to measure")
    base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True, check=True
                          ).stdout.strip()
    with tempfile.TemporaryDirectory() as td:
        work = pathlib.Path(td) / "tree"
        work.mkdir()
        tar = subprocess.run(["git", "archive", "--format=tar", "HEAD"],
                             cwd=ROOT, capture_output=True, check=True)
        subprocess.run(["tar", "-x"], cwd=work, input=tar.stdout, check=True)
        patch_copy = work / "candidate.patch"
        shutil.copy2(PATCH, patch_copy)
        applied = subprocess.run(["git", "apply", str(patch_copy)], cwd=work,
                                 capture_output=True, text=True)
        if applied.returncode != 0:
            raise SystemExit(f"measure_candidate: the shipped patch does "
                             f"not apply to HEAD:\n{applied.stderr}")
        env = {"PYTHONPATH": str(work / "src"), "PATH": "/usr/bin:/bin",
               "HOME": str(work)}
        focused = subprocess.run(
            [sys.executable, "-m", "pytest", FOCUSED, "-q", "-p",
             "no:randomly"], cwd=work, capture_output=True, text=True,
            env=env)
        full = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q"],
            cwd=work, capture_output=True, text=True, env=env)
        failures = sorted(
            l.split(" - ")[0].removeprefix("FAILED ").strip()
            for l in full.stdout.splitlines() if l.startswith("FAILED "))
        return {
            "generated_by": "specs/evidence/0001/measure_candidate.py",
            "base_commit": base,
            "patch_sha256": hashlib.sha256(PATCH.read_bytes()).hexdigest(),
            "focused_suite": {"path": FOCUSED, **_tail(focused.stdout)},
            "full_suite": _tail(full.stdout),
            "failure_set": failures,
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "command_focused": f"python -m pytest {FOCUSED} -q "
                                   f"-p no:randomly",
                "command_full": "python -m pytest tests/ -q",
            },
        }


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    rec = measure()
    text = json.dumps(rec, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        RECORD.write_text(text)
        print(f"measure_candidate: wrote {RECORD.name} — focused "
              f"{rec['focused_suite']['passed']} passed, full "
              f"{rec['full_suite']['failed']} failed/"
              f"{rec['full_suite']['passed']} passed/"
              f"{rec['full_suite']['skipped']} skipped")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
