#!/usr/bin/env python3
# Mutation-Matrix: tests/test_collected_header.py::test_candidate_results_record_binds_the_measurement
"""Validate the candidate results RECORD against a CLOSED, exactly typed
schema, and bind every field it claims to the artifacts that carry the
same fact.

0001 external round 12 (2026-08-24), R12-1: the first version bound a
PROJECTION — patch hash, README focused count, README triple, failure
count — while the record CLAIMS base commit, environment, commands,
focused outcome and a sorted failure set. The reviewer changed
`base_commit` to forty zeroes and Python to `0.0.0` while the README
still said `59cd1cf`/`3.12.3`, and separately replaced one failure with
a duplicate (16 entries, 15 unique): both exited 0. A checker whose
domain is the fields its author happened to think of is the
verify-against-the-domain defect, one layer up.

So the domain is now the SCHEMA, and the schema is closed:
  * every key at every level is REQUIRED and no extra key is tolerated
    (a record that grows a field without a check is a red run);
  * every value is exactly typed and range-checked;
  * `failure_set` must be sorted, UNIQUE, node-id shaped, and
    cardinality-equal to `full_suite.failed`;
  * the commands are compared to what `measure_candidate` actually
    runs — imported, never retyped;
  * `patch_sha256` must equal the shipped patch's bytes, and the README
    inside that patch must state the same focused count, full triple,
    base commit and Python version the record does.

Seal-time replay (the reviewer's requested artifact) is a separate,
git-requiring step: `measure_candidate.py --verify`, run by the sealer
in the repo, regenerates the COMPLETE record from the declared base and
refuses on any difference. This checker is the extraction-safe half and
needs no git.
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
NODE_ID = re.compile(r"tests/[\w/.-]+\.py::[\w\[\]/.:-]+$")
SUITE_KEYS = {"passed", "failed", "skipped"}


def _typed(problems, path, value, kind, extra=None):
    if not isinstance(value, kind) or isinstance(value, bool) != (kind is bool):
        problems.append(f"{path}: expected {kind.__name__}, got "
                        f"{type(value).__name__}")
        return False
    if extra and not extra(value):
        problems.append(f"{path}: value {value!r} fails its constraint")
        return False
    return True


def _closed(problems, path, mapping, required):
    if not isinstance(mapping, dict):
        problems.append(f"{path}: expected object")
        return False
    missing = sorted(required - set(mapping))
    extra = sorted(set(mapping) - required)
    if missing:
        problems.append(f"{path}: MISSING {missing} — every claimed field "
                        f"is validated (R12-1)")
    if extra:
        problems.append(f"{path}: UNKNOWN {extra} — the schema is closed; a "
                        f"field without a check is a red run, not a pass")
    return not (missing or extra)


def validate(rec: dict, patch_text: str, patch_sha: str,
             commands: dict) -> list:
    p = []
    _closed(p, "record", rec, {
        "generated_by", "base_commit", "patch_sha256", "focused_suite",
        "full_suite", "failure_set", "environment"})

    _typed(p, "generated_by", rec.get("generated_by"), str,
           lambda v: v == "specs/evidence/0001/measure_candidate.py")
    _typed(p, "base_commit", rec.get("base_commit"), str,
           lambda v: bool(re.fullmatch(r"[0-9a-f]{40}", v)))
    _typed(p, "patch_sha256", rec.get("patch_sha256"), str,
           lambda v: bool(re.fullmatch(r"[0-9a-f]{64}", v)))

    fs = rec.get("focused_suite")
    if _closed(p, "focused_suite", fs, SUITE_KEYS | {"path"}):
        _typed(p, "focused_suite.path", fs["path"], str,
               lambda v: v == "tests/test_0001_candidate.py")
        for k in sorted(SUITE_KEYS):
            _typed(p, f"focused_suite.{k}", fs[k], int, lambda v: v >= 0)
        if isinstance(fs.get("failed"), int) and fs["failed"] != 0:
            p.append(f"focused_suite.failed is {fs['failed']} — the "
                     f"candidate's own suite must PASS")
        if isinstance(fs.get("passed"), int) and fs["passed"] <= 0:
            p.append("focused_suite.passed must be positive")

    full = rec.get("full_suite")
    if _closed(p, "full_suite", full, SUITE_KEYS):
        for k in sorted(SUITE_KEYS):
            _typed(p, f"full_suite.{k}", full[k], int, lambda v: v >= 0)

    env = rec.get("environment")
    if _closed(p, "environment", env, {"python", "platform",
                                       "command_focused", "command_full"}):
        _typed(p, "environment.python", env["python"], str,
               lambda v: bool(re.fullmatch(r"\d+\.\d+\.\d+", v)))
        _typed(p, "environment.platform", env["platform"], str,
               lambda v: bool(v.strip()))
        for k, want in (("command_focused", commands["focused"]),
                        ("command_full", commands["full"])):
            if env.get(k) != want:
                p.append(f"environment.{k} is {env.get(k)!r} but "
                         f"measure_candidate runs {want!r} — the record may "
                         f"not describe a command it did not run")

    fset = rec.get("failure_set")
    if not isinstance(fset, list) or not all(isinstance(x, str) for x in fset):
        p.append("failure_set: expected a list of strings")
    else:
        if fset != sorted(fset):
            p.append("failure_set is not SORTED — the set is the claim, and "
                     "an unordered claim cannot be diffed")
        if len(set(fset)) != len(fset):
            dupes = sorted({x for x in fset if fset.count(x) > 1})
            p.append(f"failure_set has DUPLICATES {dupes} — {len(fset)} "
                     f"entries, {len(set(fset))} unique (R12-1's second "
                     f"counterexample)")
        bad = [x for x in fset if not NODE_ID.fullmatch(x)]
        if bad:
            p.append(f"failure_set entries are not pytest node ids: {bad[:3]}")
        if isinstance(full, dict) and isinstance(full.get("failed"), int) \
                and len(fset) != full["failed"]:
            p.append(f"failure_set names {len(fset)} failures but "
                     f"full_suite.failed is {full['failed']}")

    if rec.get("patch_sha256") != patch_sha:
        p.append(f"the record binds patch {str(rec.get('patch_sha256'))[:16]}… "
                 f"but the shipped patch is {patch_sha[:16]}… — regenerate "
                 f"with measure_candidate.py --write")

    # ...and the README INSIDE that patch must state the same facts
    m = re.search(r"`tests/test_0001_candidate\.py`:\s*\*\*(\d+) passed\*\*",
                  patch_text)
    if not m:
        p.append("the patch's README states no focused count")
    elif isinstance(fs, dict) and int(m.group(1)) != fs.get("passed"):
        p.append(f"README focused count {m.group(1)} != record "
                 f"{fs.get('passed')}")
    m2 = re.search(r"measured \d{4}-\d\d-\d\d: (\d+) failed, (\d+) passed, "
                   r"(\d+) skipped", patch_text)
    if not m2:
        p.append("the patch's README states no full-suite triple")
    elif isinstance(full, dict):
        got = tuple(int(x) for x in m2.groups())
        want = (full.get("failed"), full.get("passed"), full.get("skipped"))
        if got != want:
            p.append(f"README triple {got} != record {want}")
    m3 = re.search(r"base: main @ ([0-9a-f]{7,40}) \+ this branch", patch_text)
    if not m3:
        p.append("the patch's README states no base commit")
    elif not str(rec.get("base_commit", "")).startswith(m3.group(1)):
        p.append(f"README base {m3.group(1)} is not a prefix of the record's "
                 f"{str(rec.get('base_commit'))[:12]}… (R12-1's first "
                 f"counterexample)")
    m4 = re.search(r"environment: CPython (\d+\.\d+\.\d+)", patch_text)
    if not m4:
        p.append("the patch's README states no Python version")
    elif isinstance(env, dict) and m4.group(1) != env.get("python"):
        p.append(f"README Python {m4.group(1)} != record "
                 f"{env.get('python')!r} (R12-1's first counterexample)")
    return p


def main() -> int:
    if not PATCH.exists() and not RECORD.exists():
        print("check_candidate_results: no candidate patch or record in "
              "this tree — nothing to bind (absent, not broken)")
        return 0
    if PATCH.exists() != RECORD.exists():
        print(f"check_candidate_results: patch exists={PATCH.exists()} but "
              f"record exists={RECORD.exists()} — a measurement without its "
              f"artifact, or an artifact without its measurement",
              file=sys.stderr)
        return 1
    sys.path.insert(0, str(HERE / "evidence" / "0001"))
    import measure_candidate as mc
    commands = {"focused": mc.COMMAND_FOCUSED, "full": mc.COMMAND_FULL}
    problems = validate(json.loads(RECORD.read_text()), PATCH.read_text(),
                        hashlib.sha256(PATCH.read_bytes()).hexdigest(),
                        commands)
    if problems:
        print("check_candidate_results: FAILED\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    rec = json.loads(RECORD.read_text())
    print(f"check_candidate_results: schema closed and total; every claimed "
          f"field bound (base {rec['base_commit'][:8]}…, python "
          f"{rec['environment']['python']}, focused "
          f"{rec['focused_suite']['passed']}, full "
          f"{rec['full_suite']['failed']}F/{rec['full_suite']['passed']}P/"
          f"{rec['full_suite']['skipped']}S, {len(rec['failure_set'])} "
          f"sorted unique failures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
