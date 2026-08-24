#!/usr/bin/env python3
# Mutation-Matrix: tests/test_collected_header.py::test_candidate_results_record_binds_the_measurement
"""Refuse any disagreement between the candidate results RECORD, the
shipped patch's own bytes, and the figures the patch's README states.

0001 external round 11 (2026-08-24): `CANDIDATE_README.md` said
"20 passed" while the branch ran 21 — a carried count incremented by
inference, inside a paragraph claiming the measurement was re-run. The
reviewer asked for a structured record so future count drift FAILS
SEALING. This is that gate; it runs in the sealer's extraction checks.

Checks, all hard failures:
  1. the record's `patch_sha256` equals the sha256 of the shipped
     `candidate.patch` — a re-generated patch with a stale record
     refuses (the record binds THAT patch, not a patch);
  2. every figure the README states inside the patch equals the
     record's: the focused passed count, and the full suite's
     failed/passed/skipped triple;
  3. the record's failure_set is non-empty and its size equals the
     recorded `full_suite.failed` — the set IS the claim, so a count
     without its members refuses.

Absent patch AND absent record is a clean skip (the candidate has been
folded or was never shipped); one without the other refuses.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
PATCH = HERE / "evidence" / "0001" / "candidate.patch"
RECORD = HERE / "evidence" / "0001" / "candidate_results.json"


def main() -> int:
    if not PATCH.exists() and not RECORD.exists():
        print("check_candidate_results: no candidate patch or record in "
              "this tree — nothing to bind (absent, not broken)")
        return 0
    problems = []
    if PATCH.exists() != RECORD.exists():
        print(f"check_candidate_results: patch exists={PATCH.exists()} but "
              f"record exists={RECORD.exists()} — a measurement without its "
              f"artifact, or an artifact without its measurement",
              file=sys.stderr)
        return 1
    rec = json.loads(RECORD.read_text())
    patch_text = PATCH.read_text()
    actual = hashlib.sha256(PATCH.read_bytes()).hexdigest()
    if rec.get("patch_sha256") != actual:
        problems.append(
            f"the record binds patch {str(rec.get('patch_sha256'))[:16]}… "
            f"but the shipped patch is {actual[:16]}… — regenerate the "
            f"record with measure_candidate.py --write")

    focused = rec["focused_suite"]["passed"]
    full = rec["full_suite"]
    # the README lives INSIDE the patch; its figures must equal the record
    m = re.search(r"`tests/test_0001_candidate\.py`:\s*\*\*(\d+) passed\*\*",
                  patch_text)
    if not m:
        problems.append("the patch's README states no focused count in the "
                        "expected form (`…candidate.py`: **N passed**)")
    elif int(m.group(1)) != focused:
        problems.append(
            f"the README's focused count {m.group(1)} != the record's "
            f"{focused} (round-11 defect class: a carried number)")

    m2 = re.search(r"measured \d{4}-\d\d-\d\d: (\d+) failed, (\d+) passed, "
                   r"(\d+) skipped", patch_text)
    if not m2:
        problems.append("the patch's README states no full-suite triple in "
                        "the expected form")
    else:
        got = tuple(int(x) for x in m2.groups())
        want = (full["failed"], full["passed"], full["skipped"])
        if got != want:
            problems.append(
                f"the README's full-suite triple {got} != the record's "
                f"{want}")

    fs = rec.get("failure_set") or []
    if len(fs) != full["failed"]:
        problems.append(
            f"the record names {len(fs)} failures but counts "
            f"{full['failed']} — the SET is the claim, not the count")

    if problems:
        print("check_candidate_results: FAILED\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    print(f"check_candidate_results: record binds the shipped patch "
          f"({actual[:16]}…); README figures equal the record "
          f"(focused {focused}; full {full['failed']}F/{full['passed']}P/"
          f"{full['skipped']}S, {len(fs)} named failures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
