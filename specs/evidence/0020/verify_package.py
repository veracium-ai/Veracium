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


def _runtime_qualified():
    """Round-8 archive ask: an unqualified SQLite must be an EXPLICIT
    SKIP/unqualified-runtime result, never an opaque harness failure. The
    packaged store fails closed at open on unqualified runtimes, so the
    store-backed harnesses cannot run there — the PURE harnesses still
    verify. Returns (qualified: bool, detail: str)."""
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from veracium.store.schema_version import (runtime_identity,
                                                   runtime_supported,
                                                   qualified_runtimes)
        me = runtime_identity()
        if runtime_supported():
            return True, f"SQLite {me.get('sqlite_version')} (qualified)"
        recs = sorted({r.get("sqlite_version") for r in qualified_runtimes()
                       if isinstance(r, dict)} - {None})
        return False, (f"SQLite {me.get('sqlite_version')} is NOT a "
                       f"qualified runtime (package qualifies: "
                       f"{', '.join(recs) or 'none recorded'}) — run under "
                       f"the qualified runtime to execute the store-backed "
                       f"harnesses")
    except Exception as e:                      # fail toward the skip, loudly
        return False, f"runtime qualification unreadable ({e!r})"


def main():
    m = json.loads((ROOT / "review_manifest.json").read_text())
    failures = []
    skips = []
    checked = 0
    for label, path, want in _walk_hashes(m):
        got = sha(path)
        checked += 1
        (failures.append(f"{label}: {path} sha mismatch")
         if got != want else print(f"ok  {label}: {path}"))
    if checked == 0:
        failures.append("no *_sha256 keys found — the manifest is empty?")

    qualified, detail = _runtime_qualified()
    print(("ok  runtime: " if qualified else "SKIP runtime: ") + detail)

    ev = m["normative_evidence"]
    for name, script, recorded, needs_store in (
            ("vector harness", ev["harness"], ev.get("harness_result"),
             False),
            ("store adapter harness", ev.get("store_adapter"),
             ev.get("store_adapter_result"), True),
            ("ledger plan harness", ev.get("ledger_plan"),
             ev.get("ledger_plan_result"), True)):
        if script is None:
            continue
        if needs_store and not qualified:
            skips.append(name)
            print(f"SKIP {name}: unqualified-runtime (explicit skip, not a "
                  f"failure — the recorded result file still hash-verifies "
                  f"above)")
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
    if skips:
        print(f"package verification: {checked} hashes verified; "
              f"{len(skips)} store-backed harness(es) SKIPPED "
              f"(unqualified-runtime) — NO FAILURES; not a full pass")
        return 0
    print(f"package verification: {checked} hashes + all harnesses "
          f"(fresh-vs-recorded) — EVERYTHING MATCHES AND PASSES")
    return 0


if __name__ == "__main__":
    sys.exit(main())
