#!/usr/bin/env python3
"""Apply a1-reference.patch to a TEMPORARY COMPLETE tree and run the
patched file's OWN vector runner — one command, no manual steps.

Round-14 standing feedback, hardened at round 15 (PACKAGE-R15-1): the
first version copied ONLY the reference file, so the reference's
computed `<root>/src` path was empty — and in dev's environment the
installed `veracium` package masked that (env-leak: the verifier passed
locally while accepting `1 named skip(s)` in a clean extraction). This
version constructs the tree the reference actually needs (`src/` is
copied in), requires the EXACT zero-skip tail, and exposes the
omitted-tree case as a testable refusal.

Runs from the repo AND from an extracted review package (no `.git`
required — `git apply` operates on plain files; `patch -p1` is the
fallback). Exits 0 only when the patch applies cleanly AND the patched
file reports `... vectors run, 0 named skip(s)` under its own runner.
If the patch file is absent (a future package after A1 folds in), it
says so and exits 0 — an absent candidate is not a failure, and the
message makes the skip visible rather than silent.
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
SRC = ROOT / "src"


def run_verification(*, copy_src: bool = True) -> int:
    """The whole procedure. `copy_src=False` exists ONLY for the
    regression that proves an incomplete tree is REFUSED (PACKAGE-R15-1:
    the skip must fail the verifier, not ride a fuzzy tail match)."""
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
        if copy_src:
            # the reference inserts `<root>/src` into sys.path; a tree
            # without it makes the shipped-default-registry vector SKIP,
            # and an installed veracium in the RUNNER'S environment can
            # mask that (the round-15 env-leak) — so the tree is made
            # complete rather than the environment trusted
            shutil.copytree(SRC, work / "src",
                            ignore=shutil.ignore_patterns("__pycache__"))
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
        # -I isolates the child from the runner's environment: no user
        # site-packages, no PYTHONPATH — the reference sees ONLY the
        # constructed tree, so an installed veracium cannot mask a hole
        r = subprocess.run([sys.executable, "-I",
                            str(target / REFERENCE.name)],
                           capture_output=True, text=True)
        tail = (r.stdout.strip().splitlines() or ["<no output>"])[-1]
        if r.returncode != 0:
            print(f"verify_a1_patch: the PATCHED reference suite FAILED "
                  f"under its own runner:\n{r.stdout}{r.stderr}",
                  file=sys.stderr)
            return 1
        if not tail.endswith("vectors run, 0 named skip(s)"):
            print(f"verify_a1_patch: runner tail is {tail!r} — the EXACT "
                  f"zero-skip result is required (PACKAGE-R15-1: a skipped "
                  f"vector is an unverified vector, not a pass)",
                  file=sys.stderr)
            return 1
        # PACKAGE-R15-1, the env-leak half: zero skips is necessary but a
        # runner environment with veracium INSTALLED could supply the
        # import from site-packages and mask a missing shipped tree. So
        # the import's PROVENANCE is witnessed: under the same path
        # insertion the reference performs, `veracium` must resolve from
        # INSIDE the constructed tree — an installed copy refuses.
        probe = subprocess.run(
            [sys.executable, "-I", "-c",
             "import sys, pathlib; "
             f"sys.path.insert(0, {str(work / 'src')!r}); "
             "import veracium; "
             "print(pathlib.Path(veracium.__file__).resolve())"],
            capture_output=True, text=True)
        resolved = probe.stdout.strip()
        if (probe.returncode != 0
                or not resolved.startswith(str(work.resolve()))):
            print(f"verify_a1_patch: veracium resolved from "
                  f"{resolved or probe.stderr.strip()!r}, not from the "
                  f"constructed tree — the vectors did not exercise the "
                  f"SHIPPED code (PACKAGE-R15-1 env-leak refusal)",
                  file=sys.stderr)
            return 1
        print(f"verify_a1_patch: patch applies; patched suite green "
              f"({tail}); veracium exercised from the constructed tree")
    return 0


def main() -> int:
    return run_verification(copy_src=True)


if __name__ == "__main__":
    raise SystemExit(main())
