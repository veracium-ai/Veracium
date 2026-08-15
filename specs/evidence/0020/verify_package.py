"""specs/0020 — ONE COMMAND that verifies the whole package (external
round 4's archive ask): every hash in review_manifest.json checked against
the tree, then both harnesses executed. Run from the extracted package
root:

    <venv>/python specs/evidence/0020/verify_package.py

Exit 0 = every manifest hash matches and every harness passes.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path.cwd()


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    m = json.loads((ROOT / "review_manifest.json").read_text())
    failures = []

    def check(path, want, label):
        got = sha(path)
        (failures.append(f"{label}: {path} sha mismatch")
         if got != want else print(f"ok  {label}: {path}"))

    for num, c in m["candidates"].items():
        check(c["path"], c["sha256"], f"candidate {num}")
    ev = m["normative_evidence"]
    check(ev["reference"], ev["reference_sha256"], "reference")
    check(ev["vectors"], ev["vectors_sha256"], "vectors")
    check(ev["harness"], ev["harness_sha256"], "harness")
    if "harness_result_sha256" in ev:
        check(ev["harness_result"], ev["harness_result_sha256"],
              "harness result")
    if "store_adapter" in ev:
        check(ev["store_adapter"], ev["store_adapter_sha256"],
              "store adapter harness")

    for name, script in (("vector harness", ev["harness"]),
                         ("store adapter harness",
                          ev.get("store_adapter"))):
        if script is None:
            continue
        r = subprocess.run([sys.executable, str(ROOT / script)],
                           capture_output=True, text=True, cwd=ROOT)
        tail = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
        if r.returncode != 0:
            failures.append(f"{name} FAILED: {tail}")
        else:
            print(f"ok  {name}: {tail}")

    if failures:
        for f in failures:
            print("FAIL", f)
        return 1
    print("package verification: EVERYTHING MATCHES AND PASSES")
    return 0


if __name__ == "__main__":
    sys.exit(main())
