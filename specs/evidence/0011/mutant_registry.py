#!/usr/bin/env python3
"""0011 — the mutant campaign as an EXECUTABLE REGISTRY (PROCESS-R6-1).

The prose record claimed every fix carried a standing test, and it did not:
F1–F4, C1–C4 and the row-unbound withdrawal had been verified by ad-hoc
shell plants that died with the session, and its totals were hand
arithmetic that did not add up (4 + 9 + 6 is 19, the record said 15). This
registry binds every campaign id to its artifact, its mutation, and the
pytest node that plants it; the runner EXECUTES the registry in one pytest
invocation and writes `mutant_results.json` with the totals DERIVED from
what ran — no hand counting anywhere.

Run:  $PY specs/evidence/0011/mutant_registry.py
      (writes mutant_results.json beside this file; nonzero if any entry's
       node is missing or fails to bite)
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
T1 = "tests/test_0011_policy_matrix.py"
T2 = "tests/test_0011_mutant_registry.py"

# (id, found_by, artifact, mutation, pytest node that plants it)
ENTRIES = (
    ("R4A", "reviewer", "policy_matrix.py",
     "source-conditional ALLOW planted in the emitted stream",
     f"{T1}::test_a_variance_planted_in_the_emission_is_caught"),
    ("R4B", "reviewer", "check_round1_fold.py",
     "dangerous helper shadowed by a benign redefinition",
     f"{T1}::test_the_fold_checker_refuses_a_shadowed_helper"),
    ("R5A", "reviewer", "policy_matrix.py",
     "one cell replaced by a duplicate — cardinality-preserving omission",
     f"{T1}::test_a_duplicate_hiding_a_missing_cell_is_caught"),
    ("R5B", "reviewer", "check_round1_fold.py",
     "the withdrawn rider re-promised in §3c's live row",
     f"{T2}::test_rider_promise_in_the_row_is_refused"),
    ("R6A", "reviewer", "policy_matrix.py",
     "THIRD_PARTY removed from DERIVED — enum axis self-narrows",
     f"{T2}::test_narrowed_enum_dimension_is_refused"),
    ("R6B", "reviewer", "check_round1_fold.py",
     "check_census_figures dropped from main()'s aggregation",
     f"{T2}::test_every_fold_check_is_reached"),
    ("M1", "dev", "policy_matrix.py", "SOURCES narrowed",
     f"{T1}::test_narrowed_dimensions_are_refused"),
    ("M2", "dev", "policy_matrix.py", "ORIGINS narrowed",
     f"{T1}::test_narrowed_dimensions_are_refused"),
    ("M3", "dev", "policy_matrix.py", "the OTHER subject dropped",
     f"{T1}::test_narrowed_dimensions_are_refused"),
    ("M4", "dev", "policy_matrix.py", "stream truncated / judged elsewhere",
     f"{T1}::test_a_truncated_stream_is_caught"),
    ("M5", "dev", "policy_matrix.py", "import cells fabricated in problems()",
     f"{T1}::test_problems_actually_reaches_the_import_adapter"),
    ("F1", "dev", "check_round1_fold.py", "helper definition indented",
     f"{T2}::test_indented_helper_definition_is_followed"),
    ("F2", "dev", "check_round1_fold.py", "parenless binding, bare-name read",
     f"{T2}::test_parenless_binding_is_followed"),
    ("F3", "dev", "check_round1_fold.py", "helper in an info-string fence",
     f"{T2}::test_info_string_fence_is_scanned"),
    ("F4", "dev", "check_round1_fold.py", "extra contradicting table row",
     f"{T2}::test_extra_table_row_is_refused"),
    ("C1", "dev", "subject_census.py / fold binding",
     "recorded-only figure inflated in the aggregate",
     f"{T2}::test_inflated_aggregate_figure_is_refused"),
    ("C2", "dev", "subject_census.py / fold binding",
     "candidate table gutted, SELF total kept",
     f"{T2}::test_gutted_candidate_table_is_refused"),
    ("C3", "dev", "subject_census.py",
     "unmasked name-shaped key in the aggregate",
     f"{T2}::test_unmasked_name_in_aggregate_is_refused"),
    ("C4", "dev", "spec §3b / fold binding", "spec figure drifted by one",
     f"{T2}::test_spec_figure_drift_is_refused"),
    ("K1", "dev", "check_contention_rule.py", "positive-control cell deleted",
     f"{T1}::test_contention_checker_cells_cannot_vanish"),
    ("K2", "dev", "check_contention_rule.py",
     "cell assertion neutered while the cell still runs",
     f"{T1}::test_contention_checker_cells_cannot_vanish"),
)


def main() -> int:
    nodes = sorted({e[4] for e in ENTRIES})
    r = subprocess.run(
        [sys.executable, "-m", "pytest", *nodes, "-q", "-p", "no:randomly"],
        cwd=ROOT, capture_output=True, text=True)
    ok = r.returncode == 0
    by_finder: dict = {}
    for e in ENTRIES:
        by_finder[e[1]] = by_finder.get(e[1], 0) + 1
    record = dict(
        schema=1,
        entries=[dict(id=i, found_by=f, artifact=a, mutation=m, node=n)
                 for i, f, a, m, n in ENTRIES],
        totals=dict(**by_finder, all=len(ENTRIES),
                    distinct_nodes=len(nodes)),
        executed=dict(exit=r.returncode,
                      tail=r.stdout.strip().splitlines()[-1]
                      if r.stdout.strip() else ""),
    )
    out = pathlib.Path(__file__).resolve().parent / "mutant_results.json"
    out.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    print(f"mutant registry: {len(ENTRIES)} entries "
          f"({by_finder.get('reviewer', 0)} reviewer-found + "
          f"{by_finder.get('dev', 0)} dev-found) over {len(nodes)} nodes — "
          f"{'ALL BITE' if ok else 'FAILURES'}; record -> {out.name}")
    if not ok:
        print(r.stdout[-800:], file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
