#!/usr/bin/env python3
"""Apply a1-reference.patch to a TEMPORARY copy and run the patched file's
OWN vector runner — one command, no manual steps.

Round-14 standing feedback, and the mechanical closure of the round-13
wrapper-versus-own-runner mismatch (A1-R13-2): dev verified the patched
vectors through the pytest wrapper, which reaches 20 of the 22 vectors,
while the reviewer runs `python reference_enforcement.py` itself. This
script IS the reviewer's procedure, so the two verifications cannot
diverge again.

Runs from the repo AND from an extracted review package (no `.git`
required — `git apply` operates on plain files; `patch -p1` is the
fallback). Exits 0 only when the patch applies cleanly AND every
`vector_*` in the patched file passes under its own runner. If the patch
file is absent (a future package after A1 folds in), it says so and
exits 0 — an absent candidate is not a failure, and the message makes
the skip visible rather than silent.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PATCH = ROOT / "specs" / "evidence" / "0024" / "a1-reference.patch"
REFERENCE = ROOT / "specs" / "evidence" / "0025" / "reference_enforcement.py"


def main() -> int:
    if not PATCH.exists():
        print("verify_a1_patch: no a1-reference.patch in this tree — "
              "nothing to verify (the candidate is absent, not broken)")
        return 0
    if not REFERENCE.exists():
        print("verify_a1_patch: reference_enforcement.py is MISSING while "
              "the patch exists", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as td:
        work = pathlib.Path(td)
        target = work / "specs" / "evidence" / "0025"
        target.mkdir(parents=True)
        shutil.copy2(REFERENCE, target / REFERENCE.name)
        patch_copy = work / "a1-reference.patch"
        shutil.copy2(PATCH, patch_copy)
        applied = False
        for cmd in (["git", "apply", str(patch_copy)],
                    ["patch", "-p1", "-i", str(patch_copy)]):
            try:
                r = subprocess.run(cmd, cwd=work, capture_output=True,
                                   text=True)
            except FileNotFoundError:
                continue
            if r.returncode == 0:
                applied = True
                break
        if not applied:
            print("verify_a1_patch: the patch did not apply (tried git "
                  "apply, then patch -p1)", file=sys.stderr)
            return 1
        r = subprocess.run([sys.executable, str(target / REFERENCE.name)],
                           capture_output=True, text=True)
        tail = (r.stdout.strip().splitlines() or ["<no output>"])[-1]
        if r.returncode != 0:
            print(f"verify_a1_patch: the PATCHED reference suite FAILED "
                  f"under its own runner:\n{r.stdout}{r.stderr}",
                  file=sys.stderr)
            return 1
        if "vectors run" not in tail:
            print(f"verify_a1_patch: unexpected runner tail {tail!r} — "
                  f"refusing to call an unrecognised output a pass",
                  file=sys.stderr)
            return 1
        print(f"verify_a1_patch: patch applies; patched suite green "
              f"({tail})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
