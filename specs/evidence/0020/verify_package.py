"""specs/0020 — ONE COMMAND that verifies the whole package (external
round 4's archive ask): every hash in review_manifest.json checked against
the tree, then every declared harness executed. Run from the extracted package
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
    """Round-8 archive ask, HARDENED per round 9 (R9-5 — the reviewer
    injected an internal defect and watched it become a success-with-skip:
    a broken qualification implementation is NOT evidence that SQLite is
    merely unsupported). ONLY a successfully evaluated
    `runtime_supported() == False` is a skip; import errors, malformed
    evidence, or predicate exceptions return ("error", detail) and FAIL
    package verification. Returns (state, detail) with state in
    {"qualified", "unqualified", "error"}."""
    sys.path.insert(0, str(ROOT / "src"))
    try:
        import veracium.store.schema_version as _sv
        # the qualification must be THIS package's code — an editable
        # install or stray module resolving elsewhere would qualify a
        # DIFFERENT veracium (found by our own fault-injection retest of
        # R9-5: the injected defect was masked by an installed copy).
        # REAL path containment (R10-5: string startswith accepted a
        # sibling '<ROOT>-shadow/...' path), and preloaded modules are
        # caught the same way — sys.modules caching returns them and
        # their __file__ fails containment.
        modpath = pathlib.Path(_sv.__file__).resolve()
        if not modpath.is_relative_to(ROOT.resolve()):
            return ("error",
                    f"the qualification module resolved OUTSIDE the "
                    f"package tree ({_sv.__file__}) — wrong cwd, missing "
                    f"src, a shadowing install, or a preloaded module "
                    f"(R9-5/R10-5)")
        from veracium.store.schema_version import (runtime_identity,
                                                   runtime_supported,
                                                   qualified_runtimes)
        me = runtime_identity()
        supported = runtime_supported()
        # R10-5: the reviewer injected `lambda: None` and truthiness made
        # it a successful skip. STRICT: only a real bool is a result;
        # only the literal False is a skip; True is qualified; anything
        # else is a package defect.
        if type(supported) is not bool:
            return ("error",
                    f"runtime_supported() returned {supported!r} "
                    f"({type(supported).__name__}) — its contract is a "
                    f"total bool; a non-boolean is a package defect, "
                    f"never an environment skip (R10-5)")
        if supported is True:
            return ("qualified",
                    f"SQLite {me.get('sqlite_version')} (qualified)")
        recs = sorted({r.get("sqlite_version") for r in qualified_runtimes()
                       if isinstance(r, dict)} - {None})
        return ("unqualified",
                f"SQLite {me.get('sqlite_version')} is NOT a qualified "
                f"runtime (package qualifies: "
                f"{', '.join(recs) or 'none recorded'}) — run under the "
                f"qualified runtime to execute the store-backed harnesses")
    except Exception as e:
        return ("error",
                f"runtime qualification COULD NOT BE EVALUATED ({e!r}) — "
                f"this is a package defect, never an environment skip "
                f"(R9-5)")


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

    state, detail = _runtime_qualified()
    qualified = state == "qualified"
    if state == "error":
        print("FAIL runtime:", detail)
        failures.append(f"runtime qualification evaluation: {detail}")
    else:
        print(("ok  runtime: " if qualified else "SKIP runtime: ") + detail)

    ev = m["normative_evidence"]
    for name, script, recorded, needs_store in (
            ("vector harness", ev["harness"], ev.get("harness_result"),
             False),
            ("store adapter harness", ev.get("store_adapter"),
             ev.get("store_adapter_result"), True),
            ("ledger plan harness", ev.get("ledger_plan"),
             ev.get("ledger_plan_result"), True),
            ("schema v8 evidence", ev.get("schema_v8"),
             ev.get("schema_v8_result"), False),
            ("verifier fault matrix", ev.get("selftest"),
             ev.get("selftest_result"), False)):
        if script is None:
            continue
        if needs_store and state == "error":
            print(f"NOT RUN {name}: runtime qualification errored (already "
                  f"a FAILURE above — R9-5: never converted to a skip)")
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
            # R11-4: compare the FULL normalized output, never just the
            # final line (the reviewer changed the recorded runtime line
            # and the old tail-only check still reported a match — the
            # same logic would miss changed constructor text or hashes).
            # Environment-dependent lines are DECLARED per entry in the
            # manifest (`normalize` regex list) and stripped from BOTH
            # sides; everything that remains must be byte-identical.
            import re as _re
            pats = [_re.compile(p, _re.M)
                    for p in m.get("evidence_normalize", {}).get(
                        name.replace(" ", "_"), [])]
            def _norm(text):
                for p in pats:
                    text = p.sub("<ENV>", text)
                return text.strip()
            fresh_n = _norm(r.stdout)
            rec_n = _norm((ROOT / recorded).read_text())
            if fresh_n != rec_n:
                import difflib
                delta = list(difflib.unified_diff(
                    rec_n.splitlines(), fresh_n.splitlines(),
                    "recorded", "fresh", lineterm=""))[:12]
                failures.append(
                    f"{name}: fresh output differs from recorded "
                    f"{recorded} after declared normalization (R11-4: "
                    f"full-output comparison): " + " | ".join(delta))
            else:
                print(f"ok  {name}: full normalized output matches the "
                      f"recorded file")

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
