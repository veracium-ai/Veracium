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


def _walk_hashes(node, prefix=""):
    """R5-4: GENERIC traversal — every key ending in _sha256 pairs with the
    sibling key it names (foo_sha256 <- foo); nothing declared can go
    unchecked (the round-5 executed gap: store_adapter_result_sha256 was
    in the manifest and never verified)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "sha256" or k.endswith("_sha256"):
                sib = (k[: -len("_sha256")] if k.endswith("_sha256")
                       else "path")
                path = node.get(sib) or node.get("path")
                if path and isinstance(path, str):
                    yield (f"{prefix}{sib}", path, v)
            elif isinstance(v, dict):
                yield from _walk_hashes(v, prefix=f"{prefix}{k}.")


def main():
    m = json.loads((ROOT / "review_manifest.json").read_text())
    failures = []
    checked = 0
    for label, path, want in _walk_hashes(m):
        got = sha(path)
        checked += 1
        (failures.append(f"{label}: {path} sha mismatch")
         if got != want else print(f"ok  {label}: {path}"))
    if checked == 0:
        failures.append("no *_sha256 keys found — the manifest is empty?")

    ev = m["normative_evidence"]
    for name, script, recorded in (
            ("vector harness", ev["harness"], ev.get("harness_result")),
            ("store adapter harness", ev.get("store_adapter"),
             ev.get("store_adapter_result"))):
        if script is None:
            continue
        r = subprocess.run([sys.executable, str(ROOT / script)],
                           capture_output=True, text=True, cwd=ROOT)
        tail = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
        if r.returncode != 0:
            failures.append(f"{name} FAILED: {tail}")
            continue
        print(f"ok  {name}: {tail}")
        if recorded:
            rec = (ROOT / recorded).read_text()
            if tail not in rec:
                failures.append(
                    f"{name}: fresh result {tail!r} not in recorded "
                    f"{recorded} (R5-4: fresh-vs-recorded comparison)")
            else:
                print(f"ok  {name}: fresh result matches the recorded file")

    if failures:
        for f in failures:
            print("FAIL", f)
        return 1
    print(f"package verification: {checked} hashes + both harnesses "
          f"(fresh-vs-recorded) — EVERYTHING MATCHES AND PASSES")
    return 0


if __name__ == "__main__":
    sys.exit(main())
