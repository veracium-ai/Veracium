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
COMMAND_FOCUSED = f"python -m pytest {FOCUSED} -q -p no:randomly"
COMMAND_FULL = "python -m pytest tests/ -q"

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


def measure(base: str | None = None) -> dict:
    """Measure at `base` (any committish) or at HEAD. R12-1: the base is
    a PARAMETER so the record can be REPLAYED against the base it
    declares — comparing two typed copies of a hash proves nothing."""
    if not PATCH.exists():
        raise SystemExit("measure_candidate: no candidate.patch to measure")
    base = subprocess.run(["git", "rev-parse", base or "HEAD"], cwd=ROOT,
                          capture_output=True, text=True, check=True
                          ).stdout.strip()
    with tempfile.TemporaryDirectory() as td:
        work = pathlib.Path(td) / "tree"
        work.mkdir()
        tar = subprocess.run(["git", "archive", "--format=tar", base],
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
                "command_focused": COMMAND_FOCUSED,
                "command_full": COMMAND_FULL,
            },
        }


def replay_matches_record() -> list:
    """R12-1's requested artifact: regenerate the COMPLETE record from
    the base the record DECLARES and diff every field. Run by the
    sealer (it needs git); the extraction-safe half is
    check_candidate_results.py. Environment fields are compared too —
    a replay on a different interpreter is a REAL difference and says
    so rather than being excused."""
    if not RECORD.exists():
        return []
    shipped = json.loads(RECORD.read_text())
    base = shipped.get("base_commit")
    if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40}", base):
        return [f"the record's base_commit {base!r} is not a commit id — "
                f"nothing to replay against"]
    return record_differences(shipped, measure(base), base)


def record_differences(shipped: dict, fresh: dict, base: str = "") -> list:
    """The comparison, PURE and separately testable (R13-1: the
    replay's discrimination must be provable without paying for two
    suite runs, so the expensive measurement and the decision about it
    are separate functions). Every key on either side is compared — a
    field the record grew is a difference, not an omission."""
    problems = []
    for key in sorted(set(shipped) | set(fresh)):
        if shipped.get(key) != fresh.get(key):
            problems.append(
                f"REPLAY DIFFERS at {key!r}: record has "
                f"{json.dumps(shipped.get(key))[:120]}, replaying the "
                f"declared base {base[:8]}… produced "
                f"{json.dumps(fresh.get(key))[:120]}")
    return problems


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--verify" in argv:
        problems = replay_matches_record()
        if problems:
            print("measure_candidate --verify: FAILED\n  "
                  + "\n  ".join(problems), file=sys.stderr)
            return 1
        print("measure_candidate --verify: the shipped record REPLAYS "
              "exactly from its declared base — every field identical")
        return 0
    base = None
    if "--base" in argv:
        base = argv[argv.index("--base") + 1]
    rec = measure(base)
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
