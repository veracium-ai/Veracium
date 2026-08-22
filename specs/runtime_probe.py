#!/usr/bin/env python3
"""The measurement-context CAPTURE — C-plus (COLLECTED_HEADER_DESIGN §5.1.4).

The context block used to be prose assembled from in-memory values at seal
time. C-plus (blocking 3) requires an immutable raw output captured BEFORE
the record exists, with the record derived FROM the capture — never from
the variables that produced it. This probe IS that capture: run as a named
script it prints ONE JSON object to stdout; the sealer redirects that to
RUNTIME_PROBE.json, ships it in the archive, and `collected_record`
derives the header's context field from the FILE.

It also owns MEASUREMENT_ARGV and MEASUREMENT_ENV: the sealer imports the
argv/env it measures with from here, so the command the probe RECORDS and
the command the sealer RUNS are one authority and cannot drift.

Run:  python specs/runtime_probe.py        (prints the JSON object)
"""
from __future__ import annotations

import json
import pathlib
import platform
import sqlite3
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The ONE canonical measurement command (R10-1). seal_package.measure() runs
# [sys.executable, *MEASUREMENT_ARGV] under MEASUREMENT_ENV; the probe records
# the identical rendering below.
MEASUREMENT_ARGV = ("-m", "pytest", "-q", "tests", "-p", "no:randomly", "-rs")
MEASUREMENT_ENV = {"VERACIUM_FORBID_NETWORK": "1", "PYTHONPATH": "src"}

# The artifact's closed key set — `collected_record` refuses a probe artifact
# carrying more, fewer, or different keys (closed at every level, R15-1).
PROBE_KEYS = ("captured_at", "command", "cwd", "interpreter", "python",
              "machine", "system", "release", "pytest", "sqlite", "collection")


def rendered_command() -> str:
    env = " ".join(f"{k}={v}" for k, v in MEASUREMENT_ENV.items())
    return f"{env} {sys.executable} " + " ".join(MEASUREMENT_ARGV)


def probe() -> dict:
    pv = subprocess.run([sys.executable, "-m", "pytest", "--version"],
                        cwd=ROOT, capture_output=True, text=True)
    if pv.returncode != 0:
        print(f"pytest-version probe failed: {pv.stderr.strip()[:200]}",
              file=sys.stderr)
        raise SystemExit(2)
    co = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests", "--collect-only",
         "-p", "no:randomly"], cwd=ROOT, capture_output=True, text=True)
    if co.returncode != 0:
        print(f"collection probe failed: {co.stderr.strip()[:200]}",
              file=sys.stderr)
        raise SystemExit(2)
    collection = ""
    for ln in reversed((co.stdout or "").strip().splitlines()):
        if "test" in ln and ("collected" in ln or "tests" in ln):
            collection = ln.strip()
            break
    if not collection:
        # R11-2: a carrier shipping a shrug ("collection unavailable") is a
        # refusal here, not a value.
        print("the collection probe produced no count line", file=sys.stderr)
        raise SystemExit(2)
    return {
        "captured_at": time.strftime("%Y%m%dT%H%MZ", time.gmtime()),
        "command": rendered_command(),
        "cwd": str(ROOT),
        "interpreter": sys.executable,
        "python": sys.version.split()[0],
        "machine": platform.machine(),
        "system": platform.system(),
        "release": platform.release(),
        "pytest": (pv.stdout or pv.stderr).strip(),
        "sqlite": sqlite3.sqlite_version,
        "collection": collection,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
