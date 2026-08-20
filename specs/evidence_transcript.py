#!/usr/bin/env python3
"""Validate the closure-evidence transcript. ONE implementation, three callers.

External round 12. The transcript shipped at `./evidence_run.json` while
`COLLECTED.txt` named `specs/generated/evidence_run.json`; `verify_archive()`
never looked at it, so DELETING IT ENTIRELY still produced a passing archive
(R12-1). And the count was self-asserted: the sealer and the regression both
read `data["ran"]` without requiring records to exist, so

    {"ran": 40, "skipped": [], "commands": []}

satisfied both (R12-2). A transcript is evidence of execution; a number in a
file is a claim, and the previous checks could not tell them apart.

`validate()` derives everything from the RECORDS and matches them against the
closure ledger by exact `(spec, finding, argv)`. The seal, the extraction
verifier and the pytest regression all call THIS — the shape this review has
repeatedly shown is the only one that does not drift.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REL_PATH = "specs/generated/evidence_run.json"     # the path COLLECTED names
_HEX64 = re.compile(r"[0-9a-f]{64}")


# EXTERNAL ROUND 13 typed three fields; ROUND 14 found three MORE coercions in
# the cells I had not typed — `ran: 45.0` (45.0 == 45), a 64-digit JSON INTEGER
# digest surviving `str()` before the hex regex, and a duplicated `skipped`
# entry vanishing into a set. Patching cells one round at a time is how a
# validator acquires a long tail of holes, so the shape changes: every field is
# DECLARED with its exact JSON type, and anything not declared is rejected.
#
# `type(x) is T`, never isinstance, because in Python `bool` is a subclass of
# `int` and every one of these findings has turned on a coercion the language
# performs silently.
def _exact(t):
    def check(v):
        return type(v) is t
    check.__name__ = f"exactly {t.__name__}"
    return check


def _hex64(v):
    return type(v) is str and _HEX64.fullmatch(v) is not None


def _abs_str(v):
    return type(v) is str and bool(v.strip()) and pathlib.PurePosixPath(v).is_absolute()


def _nonempty_str(v):
    return type(v) is str and bool(v.strip())


COMMAND_SCHEMA = {
    "spec": (_nonempty_str, "a non-empty string"),
    "finding": (_nonempty_str, "a non-empty string"),
    "argv": (_nonempty_str, "a non-empty string"),
    "cwd": (_abs_str, "a non-empty ABSOLUTE path string"),
    "exit": (_exact(int), "exactly int (a bool is an int in Python)"),
    "output_sha256": (_hex64, "a STRING of 64 hex digits (an int of 64 "
                              "digits survived str() before)"),
    # ROUND 21 (self-found, cost work): how long this command took. Declared
    # rather than smuggled — the schema is closed, so an undeclared field is
    # refused, and the mutation matrix in tests/test_spec_gate.py derives a
    # mutation for every declared field automatically. Adding a field to a
    # closed schema is the cheap case BECAUSE it was closed.
    "duration_ms": (_exact(int), "exactly int (milliseconds; a float would "
                                 "pass == comparisons, which is R14-1)"),
}

TOP_SCHEMA = {
    "ran": (_exact(int), "exactly int (45.0 == 45 passed before)"),
    # what the evidence machinery COSTS, recorded where the next round will
    # read it. The suite went from 39s to 8 minutes over fifteen rounds because
    # every round added a check and none measured one.
    "wall_ms": (_exact(int), "exactly int (milliseconds of wall clock)"),
    "workers": (_exact(int), "exactly int (concurrent runners)"),
    "skipped": (lambda v: type(v) is list and all(type(x) is str for x in v),
                "a list of strings"),
    "commands": (lambda v: type(v) is list, "a list"),
}


def _ledger(specs_dir: pathlib.Path):
    sys.path.insert(0, str(specs_dir))
    import importlib
    import closure_findings
    importlib.reload(closure_findings)
    return closure_findings.CLOSURES


def validate(transcript_path: pathlib.Path, specs_dir: pathlib.Path) -> list:
    """Return a list of problems; empty means the transcript IS the execution."""
    problems = []
    if not transcript_path.exists():
        return [f"no transcript at {transcript_path} — the evidence claim has "
                f"no source (R12-1: deleting it used to pass every check)"]
    try:
        data = json.loads(transcript_path.read_text())
    except Exception as e:                                    # noqa: BLE001
        return [f"{transcript_path} is not readable JSON: {e}"]

    if type(data) is not dict:
        return ["the transcript is not a JSON object"]
    # EXTERNAL ROUND 15 (R15-1): closedness was established one layer down and
    # not at the layer above it. Commands rejected undeclared fields; the
    # OBJECT HOLDING THEM did not, so `{"undeclared_top_level": "accepted"}`
    # rode through validate() and the whole archive verifier. A property named
    # "closed" is recursive or it is decoration — every level that has keys
    # rejects keys it does not declare.
    extra = [f for f in data if f not in TOP_SCHEMA]
    if extra:
        problems.append(f"the transcript carries undeclared top-level field(s) "
                        f"{sorted(extra)} — the schema is closed at EVERY level")
    for field, (check, why) in TOP_SCHEMA.items():
        if field not in data:
            problems.append(f"the transcript has no `{field}`")
        elif not check(data[field]):
            problems.append(f"`{field}` is {data[field]!r} "
                            f"({type(data[field]).__name__}); required: {why}")
    if problems:
        return problems
    commands = data["commands"]

    # R14-1: `skipped` was compared as a SET, so a duplicated launcher record
    # vanished. Multiplicity is part of the claim.
    if len(data["skipped"]) != len(set(data["skipped"])):
        dupes = sorted({x for x in data["skipped"]
                        if data["skipped"].count(x) > 1})
        problems.append(f"`skipped` contains duplicates: {dupes}")

    # R12-2: the count is DERIVED. A `ran` that disagrees is a claim about the
    # records rather than a summary of them.
    if data["ran"] != len(commands):
        problems.append(f"`ran` is {data['ran']} but the transcript holds "
                        f"{len(commands)} command records")

    ledger = _ledger(specs_dir)
    expected = {(c[0], c[3], c[6]) for c in ledger if "run_offline.sh" not in c[6]}
    launcher = {f"{c[0]} {c[3]} (launcher — run separately at seal)"
                for c in ledger if "run_offline.sh" in c[6]}

    seen = []
    for i, c in enumerate(commands):
        if type(c) is not dict:
            problems.append(f"command {i} is not a JSON object")
            continue
        missing = [f for f in COMMAND_SCHEMA if f not in c]
        if missing:
            problems.append(f"command {i} is missing {missing}")
            continue
        extra = [f for f in c if f not in COMMAND_SCHEMA]
        if extra:
            problems.append(f"command {i} carries undeclared field(s) {extra} "
                            f"— the schema is closed")
        where = f"{c['spec']} {c['finding']}" if _nonempty_str(c.get("spec")) \
            and _nonempty_str(c.get("finding")) else f"command {i}"
        ok = True
        for field, (check, why) in COMMAND_SCHEMA.items():
            if not check(c[field]):
                problems.append(f"{where}: `{field}` is {c[field]!r} "
                                f"({type(c[field]).__name__}); required: {why}")
                ok = False
        if ok and c["exit"] != 0:
            problems.append(f"{where} exited {c['exit']}")
        if ok:
            seen.append((c["spec"], c["finding"], c["argv"]))

    dupes = {k for k in seen if seen.count(k) > 1}
    if dupes:
        problems.append(f"duplicate command records: {sorted(dupes)}")

    missing = expected - set(seen)
    extra = set(seen) - expected
    for spec, fid, argv in sorted(missing):
        problems.append(f"{spec} {fid}: in the closure ledger, NOT executed "
                        f"in the transcript")
    for spec, fid, argv in sorted(extra):
        problems.append(f"{spec} {fid}: executed but matches no closure row "
                        f"(argv differs, or the row was removed)")

    if set(data.get("skipped") or []) != launcher:
        problems.append(f"the skipped set is {sorted(data.get('skipped') or [])}, "
                        f"expected exactly the launcher row(s) {sorted(launcher)}")
    return problems


def main(argv) -> int:
    root = pathlib.Path(argv[1]) if len(argv) > 1 else HERE.parent
    problems = validate(root / REL_PATH, root / "specs")
    if problems:
        print("evidence transcript INVALID:\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    print(f"evidence transcript: VALID ({REL_PATH})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
