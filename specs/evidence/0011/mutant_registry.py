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
    side of the binding.

    PROCESS-R8-1(1): the log records (node, id) PAIRS, with the node taken
    from pytest's own PYTEST_CURRENT_TEST — a global bag of ids proved only
    that every id appeared SOMEWHERE, so swapping two entries' nodes changed
    nothing. The caller cannot misdeclare its node, because it does not
    supply it."""
    path = os.environ.get(KILL_ENV)
    if not path:
        return
    node = os.environ.get("PYTEST_CURRENT_TEST", "?").split(" ")[0]
    with open(path, "a") as fh:
        for i in ids:
            fh.write(f"{node}\t{i}\n")


FOUND_BY = ("reviewer", "dev")           # closed: EVIDENCE-R9-1 planted
                                          # "banana" and the totals grew a
                                          # partition the round never governed


def _no_dup_pairs(pairs):
    """EVIDENCE-R9-1(1): `json.loads` keeps the LAST of duplicate keys, so a
    prepended `"schema": false` vanished in parsing and canonicalisation
    then blessed the file. Duplicates refuse at PARSE."""
    seen = set()
    for k, _v in pairs:
        if k in seen:
            raise ValueError(f"duplicate JSON key {k!r}")
        seen.add(k)
    return dict(pairs)


def strict_parse(raw: str) -> dict:
    return json.loads(raw, object_pairs_hook=_no_dup_pairs)


def canonical_bytes(record: dict) -> str:
    """THE writer. Check mode compares the shipped file's RAW BYTES to this
    exact serialisation, so nothing survives a parse-normalise round trip."""
    return json.dumps(record, indent=1, sort_keys=True) + "\n"


def validate_record(rec) -> list:
    """Recursive, exactly typed, CLOSED — unknown and missing keys refuse at
    every level, bool never passes as int (bool is an int subclass), and
    found_by is the governed two-value partition."""
    bad = []

    def is_int(x):
        return type(x) is int

    if type(rec) is not dict:
        return ["record is not an object"]
    if sorted(rec) != ["entries", "executed", "killed", "schema", "totals"]:
        return [f"top-level keys {sorted(rec)} != the closed set"]
    if rec["schema"] != 3 or not is_int(rec["schema"]):
        bad.append(f"schema {rec['schema']!r} is not 3 (the killed field "
                   f"became (node, id) pairs — that shape change is a "
                   f"version, EVIDENCE-R9-1)")
    if type(rec["entries"]) is not list or not rec["entries"]:
        bad.append("entries is not a non-empty list")
    else:
        for e in rec["entries"]:
            if type(e) is not dict or sorted(e) != [
                    "artifact", "found_by", "id", "mutation", "node"]:
                bad.append(f"entry keys {sorted(e) if type(e) is dict else e}"
                           f" != the closed set")
                break
            if any(type(e[k]) is not str for k in e):
                bad.append(f"entry {e.get('id')!r} carries a non-string")
                break
            if e["found_by"] not in FOUND_BY:
                bad.append(f"entry {e['id']!r} found_by {e['found_by']!r} is "
                           f"outside the governed partition {FOUND_BY}")
                break
    if (type(rec["killed"]) is not list
            or any(type(k) is not list or len(k) != 2
                   or any(type(x) is not str for x in k)
                   for k in rec["killed"])):
        bad.append("killed is not a list of [node, id] string pairs")
    t_ = rec["totals"]
    if type(t_) is not dict or sorted(t_) != ["all", "dev", "distinct_nodes",
                                              "reviewer"]:
        bad.append(f"totals keys != the closed set (got "
                   f"{sorted(t_) if type(t_) is dict else t_})")
    elif not all(is_int(v) for v in t_.values()):
        bad.append("a totals value is not an exact int")
    ex = rec["executed"]
    if type(ex) is not dict or sorted(ex) != ["exit", "passed"] or \
            not all(is_int(v) for v in ex.values()):
        bad.append("executed is not {exit: int, passed: int}")
    return bad


def validate_entries(entries=None) -> list:
    """Structural validity, independent of any run: unique ids, real
    artifact paths, non-empty mutations, plausibly-formed nodes."""
    entries = ENTRIES if entries is None else entries
    bad = []
    ids = [e[0] for e in entries]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        bad.append(f"duplicate registry id(s): {sorted(dupes)}")
    for i, by, art, mut, node in entries:
        if by not in FOUND_BY:
            bad.append(f"{i}: found_by {by!r} outside the governed "
                       f"partition {FOUND_BY}")
        # PROCESS-R8-1(3): `ROOT / "/etc/passwd"` IS "/etc/passwd" —
        # pathlib discards the left side when the right is absolute, so an
        # artifact anywhere on the host validated. Paths must be relative,
        # resolve INSIDE the tree, and be regular files.
        ap = pathlib.PurePosixPath(art)
        if ap.is_absolute() or ".." in ap.parts:
            bad.append(f"{i}: artifact {art!r} is not a plain relative "
                       f"path inside the package")
            continue
        full = (ROOT / art)
        try:
            full.resolve().relative_to(ROOT.resolve())
        except ValueError:
            bad.append(f"{i}: artifact {art!r} escapes the package root")
            continue
        if not full.is_file():
            bad.append(f"{i}: artifact {art!r} is not a regular file in "
                       f"the package")
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
    killed = sorted(tuple(l.split("\t")) for l in
                    pathlib.Path(log).read_text().splitlines() if l)
    pathlib.Path(log).unlink(missing_ok=True)
    # PROCESS-R9-1: attribution must come from the RUN, not the registry —
    # any reported node the runner did not invoke is a fabricated join
    alien = sorted({n for n, _i in killed} - set(nodes))
    if alien:
        killed.append(("<runner>", f"ALIEN-NODE:{alien[0]}"))
    tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    passed = 0
    for tok in tail.split():
        if tok.isdigit():
            passed = int(tok)
            break
    return killed, r.returncode, passed


def binding_problems(entries, killed) -> list:
    """PROCESS-R7-1 + R8-1(1): declared (node, id) PAIRS and reported
    (node, id) pairs must be the SAME MULTISET. A global id-bag proved only
    that every id appeared somewhere — swapping two entries' nodes changed
    nothing — so the binding is per-pair: an entry whose OWN node never
    reports its id is named, whichever other node happens to."""
    declared = sorted((e[4], e[0]) for e in entries)
    bad = []
    unkilled = sorted(set(declared) - set(killed))
    unknown = sorted(set(killed) - set(declared))
    if unkilled:
        bad.append(f"registry pair(s) whose OWN node never reports the "
                   f"kill: {unkilled} — an id reported by a different node "
                   f"is a misbound entry, not a kill")
    if unknown:
        bad.append(f"kill pair(s) the registry does not declare: {unknown}")
    over = sorted({k for k in killed if killed.count(k) > 1})
    if over:
        bad.append(f"pair(s) reported more than once in one run: {over}")
    return bad


def build_record(entries, killed, exit_code, passed) -> dict:
    by_finder: dict = {}
    for e in entries:
        by_finder[e[1]] = by_finder.get(e[1], 0) + 1
    return dict(
        schema=3,
        entries=[dict(id=i, found_by=f, artifact=a, mutation=m, node=n)
                 for i, f, a, m, n in entries],
        killed=[list(k) for k in killed],
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
    # CHECK mode (default): grammar FIRST — a corrupt file refuses before
    # any recomputation runs — then the shipped RAW BYTES must equal the
    # canonical writer's output for the recomputed record exactly.
    record_path = pathlib.Path(os.environ.get("VERACIUM_MUTANT_RECORD",
                                              str(RECORD)))
    if not record_path.exists():
        print("mutant_results.json is MISSING — nothing to check",
              file=sys.stderr)
        return 1
    raw = record_path.read_text()
    try:
        shipped = strict_parse(raw)
    except ValueError as exc:
        print(f"shipped record REFUSED at parse: {exc}", file=sys.stderr)
        return 1
    gram = validate_record(shipped)
    if gram:
        print("shipped record REFUSED by the grammar:\n  "
              + "\n  ".join(gram), file=sys.stderr)
        return 1
    # PROCESS-R8-1(2): dict equality COERCES — False == 0, True == 1 — so a
    # boolean smuggled into an int field claimed an exact match. Canonical
    # SERIALIZED BYTES are compared instead ("false" is not "0"), after a
    # typed sanity pass on the fields coercion can reach.
    if raw != canonical_bytes(record):
        for k in sorted(set(shipped) | set(record)):
            if (json.dumps(shipped.get(k), sort_keys=True)
                    != json.dumps(record.get(k), sort_keys=True)):
                print(f"shipped record DIVERGES at {k!r}", file=sys.stderr)
        print("shipped bytes are not the canonical writer's bytes for the "
              "recomputed record", file=sys.stderr)
        return 1
    print(f"mutant registry: {record['totals']['all']} entries "
          f"({record['totals'].get('reviewer', 0)} reviewer + "
          f"{record['totals'].get('dev', 0)} dev), one-to-one kill binding "
          f"holds, shipped record matches the recomputation exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
