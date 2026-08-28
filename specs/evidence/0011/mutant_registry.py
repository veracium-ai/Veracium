#!/usr/bin/env python3
"""0011 — the mutant campaign as an executable, INDEPENDENTLY CHECKABLE ledger.

PROCESS-R7-1: the first registry derived success from the distinct pytest
nodes, not from the mutants — a fictitious entry riding an already-listed
passing node made 22 entries over the same 18 nodes with exit 0, artifact
paths were never validated, and the result record was WRITE-ONLY: the runner
overwrote it and nothing ever read it back.

The binding now comes from the EXECUTED side. Each standing test, after its
assertions succeed, reports the mutant id(s) it just killed via
`record_kill()` into a kill log the runner owns. The runner requires the
reported kills to equal the registry's ids EXACTLY — one-to-one, duplicates
rejected, unknowns rejected — so an entry nothing kills, and a kill nothing
declares, are both loud. Artifact paths must exist. And the record has two
modes:

    $PY specs/evidence/0011/mutant_registry.py            # CHECK (default):
        re-runs the campaign, rebuilds the record, and REQUIRES it to equal
        the shipped mutant_results.json byte-for-byte. Non-mutating.
    $PY specs/evidence/0011/mutant_registry.py --write    # seal-time only:
        writes the record.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
RECORD = HERE / "mutant_results.json"
KILL_ENV = "VERACIUM_MUTANT_KILL_LOG"
T1 = "tests/test_0011_policy_matrix.py"
T2 = "tests/test_0011_mutant_registry.py"

# (id, found_by, artifact RELPATH — validated to exist, mutation, node)
ENTRIES = (
    ("R4A", "reviewer", "specs/evidence/0011/policy_matrix.py",
     "source-conditional ALLOW planted in the emitted stream",
     f"{T1}::test_a_variance_planted_in_the_emission_is_caught"),
    ("R4B", "reviewer", "specs/evidence/0011/check_round1_fold.py",
     "dangerous helper shadowed by a benign redefinition",
     f"{T1}::test_the_fold_checker_refuses_a_shadowed_helper"),
    ("R5A", "reviewer", "specs/evidence/0011/policy_matrix.py",
     "one cell replaced by a duplicate — cardinality-preserving omission",
     f"{T1}::test_a_duplicate_hiding_a_missing_cell_is_caught"),
    ("R5B", "reviewer", "specs/evidence/0011/check_round1_fold.py",
     "the withdrawn rider re-promised in §3c's live row",
     f"{T2}::test_rider_promise_in_the_row_is_refused"),
    ("R6A", "reviewer", "specs/evidence/0011/policy_matrix.py",
     "THIRD_PARTY removed from DERIVED — enum axis self-narrows",
     f"{T2}::test_narrowed_enum_dimension_is_refused"),
    ("R6B", "reviewer", "specs/evidence/0011/check_round1_fold.py",
     "check_census_figures dropped from main()'s aggregation",
     f"{T2}::test_every_fold_check_is_reached"),
    ("M1", "dev", "specs/evidence/0011/policy_matrix.py",
     "SOURCES narrowed", f"{T1}::test_narrowed_dimensions_are_refused"),
    ("M2", "dev", "specs/evidence/0011/policy_matrix.py",
     "ORIGINS narrowed", f"{T1}::test_narrowed_dimensions_are_refused"),
    ("M3", "dev", "specs/evidence/0011/policy_matrix.py",
     "the OTHER subject dropped",
     f"{T1}::test_narrowed_dimensions_are_refused"),
    ("M4", "dev", "specs/evidence/0011/policy_matrix.py",
     "stream truncated / judged elsewhere",
     f"{T1}::test_a_truncated_stream_is_caught"),
    ("M5", "dev", "specs/evidence/0011/policy_matrix.py",
     "import cells fabricated in problems()",
     f"{T1}::test_problems_actually_reaches_the_import_adapter"),
    ("F1", "dev", "specs/evidence/0011/check_round1_fold.py",
     "helper definition indented",
     f"{T2}::test_indented_helper_definition_is_followed"),
    ("F2", "dev", "specs/evidence/0011/check_round1_fold.py",
     "parenless binding, bare-name read",
     f"{T2}::test_parenless_binding_is_followed"),
    ("F3", "dev", "specs/evidence/0011/check_round1_fold.py",
     "helper in an info-string fence",
     f"{T2}::test_info_string_fence_is_scanned"),
    ("F4", "dev", "specs/evidence/0011/check_round1_fold.py",
     "extra contradicting table row",
     f"{T2}::test_extra_table_row_is_refused"),
    ("C1", "dev", "specs/evidence/0011/check_round1_fold.py",
     "recorded-only census figure inflated in the aggregate",
     f"{T2}::test_inflated_aggregate_figure_is_refused"),
    ("C2", "dev", "specs/evidence/0011/check_round1_fold.py",
     "candidate table gutted, SELF total kept",
     f"{T2}::test_gutted_candidate_table_is_refused"),
    ("C3", "dev", "specs/evidence/0011/subject_census.py",
     "unmasked name-shaped key in the aggregate",
     f"{T2}::test_unmasked_name_in_aggregate_is_refused"),
    ("C4", "dev", "specs/evidence/0011/check_round1_fold.py",
     "spec §3b figure drifted by one",
     f"{T2}::test_spec_figure_drift_is_refused"),
    ("K1", "dev", "specs/evidence/0011/check_contention_rule.py",
     "positive-control cell deleted",
     f"{T1}::test_contention_checker_cells_cannot_vanish"),
    ("K2", "dev", "specs/evidence/0011/check_contention_rule.py",
     "cell assertion neutered while the cell still runs",
     f"{T1}::test_contention_checker_cells_cannot_vanish"),
)


def record_kill(*ids) -> None:
    """Called by a standing test AFTER its assertions succeed. A no-op in
    an ordinary suite run; under the runner, the kill log is the executed
    side of the one-to-one binding."""
    path = os.environ.get(KILL_ENV)
    if not path:
        return
    with open(path, "a") as fh:
        for i in ids:
            fh.write(i + "\n")


def validate_entries(entries=None) -> list:
    """Structural validity, independent of any run: unique ids, real
    artifact paths, non-empty mutations, plausibly-formed nodes."""
    entries = ENTRIES if entries is None else entries
    bad = []
    ids = [e[0] for e in entries]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        bad.append(f"duplicate registry id(s): {sorted(dupes)}")
    for i, _by, art, mut, node in entries:
        if not (ROOT / art).exists():
            bad.append(f"{i}: artifact {art!r} does not exist")
        if not mut.strip():
            bad.append(f"{i}: empty mutation description")
        if "::" not in node or not node.startswith("tests/"):
            bad.append(f"{i}: {node!r} is not a pytest node id")
    return bad


def execute(entries=None) -> tuple:
    """One pytest run over the registry's nodes, kills read from the log.
    Returns (killed_ids_sorted, exit_code, passed_count)."""
    entries = ENTRIES if entries is None else entries
    nodes = sorted({e[4] for e in entries})
    with tempfile.NamedTemporaryFile("r", suffix=".kills",
                                     delete=False) as fh:
        log = fh.name
    env = dict(os.environ, **{KILL_ENV: log})
    r = subprocess.run(
        [sys.executable, "-m", "pytest", *nodes, "-q", "-p", "no:randomly"],
        cwd=ROOT, capture_output=True, text=True, env=env)
    killed = sorted(pathlib.Path(log).read_text().split())
    pathlib.Path(log).unlink(missing_ok=True)
    tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    passed = 0
    for tok in tail.split():
        if tok.isdigit():
            passed = int(tok)
            break
    return killed, r.returncode, passed


def binding_problems(entries, killed) -> list:
    """PROCESS-R7-1's core: declared ids and reported kills must be the
    SAME MULTISET. An entry nothing kills, a kill nothing declares, and a
    double-report are all named."""
    declared = sorted(e[0] for e in entries)
    bad = []
    unkilled = sorted(set(declared) - set(killed))
    unknown = sorted(set(killed) - set(declared))
    if unkilled:
        bad.append(f"registry id(s) NO EXECUTED TEST REPORTS KILLING: "
                   f"{unkilled} — an entry that nothing kills is prose "
                   f"wearing a ledger")
    if unknown:
        bad.append(f"kill(s) reported for id(s) the registry does not "
                   f"declare: {unknown}")
    over = sorted({k for k in killed if killed.count(k) > 1})
    if over:
        bad.append(f"id(s) reported killed more than once in one run: "
                   f"{over}")
    return bad


def build_record(entries, killed, exit_code, passed) -> dict:
    by_finder: dict = {}
    for e in entries:
        by_finder[e[1]] = by_finder.get(e[1], 0) + 1
    return dict(
        schema=2,
        entries=[dict(id=i, found_by=f, artifact=a, mutation=m, node=n)
                 for i, f, a, m, n in entries],
        killed=killed,
        totals=dict(**by_finder, all=len(entries),
                    distinct_nodes=len({e[4] for e in entries})),
        executed=dict(exit=exit_code, passed=passed),
    )


def main() -> int:
    write = "--write" in sys.argv
    bad = validate_entries()
    if bad:
        print("mutant registry INVALID:\n  " + "\n  ".join(bad),
              file=sys.stderr)
        return 1
    killed, exit_code, passed = execute()
    bad = binding_problems(ENTRIES, killed)
    if exit_code != 0:
        bad.append(f"the campaign's pytest run FAILED (exit {exit_code})")
    if bad:
        print("mutant registry FAILED:\n  " + "\n  ".join(bad),
              file=sys.stderr)
        return 1
    record = build_record(ENTRIES, killed, exit_code, passed)
    if write:
        RECORD.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
        print(f"mutant registry: {record['totals']['all']} entries, every "
              f"one REPORTED KILLED by its executed test; record WRITTEN")
        return 0
    # CHECK mode (default): the shipped record must equal the recomputation
    if not RECORD.exists():
        print("mutant_results.json is MISSING — nothing to check",
              file=sys.stderr)
        return 1
    shipped = json.loads(RECORD.read_text())
    if shipped != record:
        for k in sorted(set(shipped) | set(record)):
            if shipped.get(k) != record.get(k):
                print(f"shipped record DIVERGES at {k!r}", file=sys.stderr)
        return 1
    print(f"mutant registry: {record['totals']['all']} entries "
          f"({record['totals'].get('reviewer', 0)} reviewer + "
          f"{record['totals'].get('dev', 0)} dev), one-to-one kill binding "
          f"holds, shipped record matches the recomputation exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
