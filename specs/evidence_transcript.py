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

    commands = data.get("commands")
    if not isinstance(commands, list):
        return ["the transcript has no `commands` list"]

    # R12-2: the count is DERIVED. A `ran` that disagrees is a claim about the
    # records rather than a summary of them.
    if data.get("ran") != len(commands):
        problems.append(f"`ran` is {data.get('ran')} but the transcript holds "
                        f"{len(commands)} command records")

    ledger = _ledger(specs_dir)
    expected = {(c[0], c[3], c[6]) for c in ledger if "run_offline.sh" not in c[6]}
    launcher = {f"{c[0]} {c[3]} (launcher — run separately at seal)"
                for c in ledger if "run_offline.sh" in c[6]}

    seen = []
    for i, c in enumerate(commands):
        for field in ("spec", "finding", "argv", "cwd", "exit", "output_sha256"):
            if field not in c:
                problems.append(f"command {i} is missing `{field}`")
                break
        else:
            where = f"{c['spec']} {c['finding']}"
            # EXTERNAL ROUND 13, R13-1: PRESENCE AND LENGTH ARE NOT VALUES.
            # `exit != 0` accepted `false`, because in Python `False == 0`;
            # `len(str(digest)) == 64` accepted 64 letter-x's; and `cwd` was
            # only required to EXIST, so `null` passed. A transcript of 42
            # rows with null cwds, boolean exits and non-hex digests satisfied
            # this function and the whole archive verifier.
            if type(c["exit"]) is not int or isinstance(c["exit"], bool):
                problems.append(f"{where}: `exit` is {c['exit']!r} "
                                f"({type(c['exit']).__name__}), not an int — "
                                f"note that a bool IS an int in Python and "
                                f"False == 0, which is how `false` passed")
            elif c["exit"] != 0:
                problems.append(f"{where} exited {c['exit']}")
            if not _HEX64.fullmatch(str(c["output_sha256"])):
                problems.append(f"{where}: `output_sha256` is not 64 hex "
                                f"digits: {str(c['output_sha256'])[:16]}…")
            cwd = c["cwd"]
            if not isinstance(cwd, str) or not cwd.strip():
                problems.append(f"{where}: `cwd` is {cwd!r}, not a non-empty "
                                f"string")
            elif not pathlib.PurePosixPath(cwd).is_absolute():
                problems.append(f"{where}: `cwd` {cwd!r} is not absolute — a "
                                f"relative path does not identify where the "
                                f"command ran")
            for field in ("spec", "finding", "argv"):
                if not isinstance(c[field], str) or not c[field].strip():
                    problems.append(f"{where}: `{field}` is {c[field]!r}, not "
                                    f"a non-empty string")
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
