"""specs/0020 — the VERIFIER QUALIFICATION FAULT MATRIX (external round
10's artifact ask). Runs `verify_package._runtime_qualified` under every
fault class the reviewer injected (plus ours) and asserts each lands in
the REQUIRED classification — never a successful skip:

  exception fault        -> error   (R9-5: a raise is a package defect)
  non-boolean (None)     -> error   (R10-5: truthiness made it a skip)
  non-boolean (1)        -> error   (1 == True must NOT qualify)
  sibling-prefix shadow  -> error   (R10-5: startswith accepted
                                     '<ROOT>-shadow/...'; is_relative_to
                                     refuses it)
  preloaded module       -> error   (a cached foreign veracium fails
                                     containment)
  evaluated False        -> unqualified (the ONLY skip)
  evaluated True         -> qualified

Run FROM THE PACKAGE ROOT: `<venv>/python
specs/evidence/0020/verify_package_selftest.py`. The seal runs it and
records the result in `verifier_selftest_result.txt`.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path.cwd()
HERE = pathlib.Path(__file__).resolve().parent


def _load_verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_package", HERE / "verify_package.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    vp = _load_verifier()
    sys.path.insert(0, str(ROOT / "src"))
    import veracium.store.schema_version as sv
    checks = []

    real_supported = sv.runtime_supported
    real_file = sv.__file__

    def expect(state, label):
        got_state, detail = vp._runtime_qualified()
        assert got_state == state, (
            f"{label}: expected {state!r}, got {got_state!r} ({detail})")
        checks.append(f"{label} -> {state}")

    try:
        # baseline (whatever this host is — must be a REAL state)
        base_state, _ = vp._runtime_qualified()
        assert base_state in ("qualified", "unqualified"), base_state
        checks.append(f"baseline evaluates cleanly -> {base_state}")

        def boom():
            raise RuntimeError("injected qualification defect")
        sv.runtime_supported = boom
        expect("error", "exception fault")

        sv.runtime_supported = lambda: None
        expect("error", "non-boolean result (None)")

        sv.runtime_supported = lambda: 1
        expect("error", "non-boolean result (1 == True)")

        sv.runtime_supported = lambda: False
        expect("unqualified", "evaluated False (the ONLY skip)")

        sv.runtime_supported = lambda: True
        expect("qualified", "evaluated True")

        # sibling-prefix shadow: '<ROOT>-shadow/...' passed the old
        # string-startswith containment; Path.is_relative_to refuses it
        sv.runtime_supported = real_supported
        sv.__file__ = str(ROOT.resolve()) + "-shadow/src/veracium/x.py"
        expect("error", "sibling-prefix shadow path")

        # preloaded foreign module: __file__ outside the tree entirely
        sv.__file__ = "/usr/lib/python3/dist-packages/veracium/x.py"
        expect("error", "preloaded foreign module")
    finally:
        sv.runtime_supported = real_supported
        sv.__file__ = real_file

    # ---- R12-3: MUTATION CELLS against the shipped consistency gates —
    # fixture trees derived from the REAL carriers; each mutation must
    # FAIL the gate (the reviewer's negative control, as a regression)
    import re as _re
    import shutil
    import tempfile
    ev = "specs/evidence/0020"
    carriers = ("specs/0021-scope-under-maintenance.md",
                "specs/0020-scoped-recall.md",
                f"{ev}/linkage_carriers.md")
    with tempfile.TemporaryDirectory() as td:
        fx = pathlib.Path(td)
        (fx / ev).mkdir(parents=True)
        for c in carriers:
            (fx / c).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / c, fx / c)
        shutil.copyfile(ROOT / ev / "reference_scope.py",
                        fx / ev / "reference_scope.py")
        def req(spec_path):
            mm = _re.search(r"^Spec-Requires: (.+)$",
                            (ROOT / spec_path).read_text(), _re.M)
            return [x.strip() for x in mm.group(1).split(",")]
        manifest = {"candidates": {
            "0020": {"requires": req("specs/0020-scoped-recall.md")},
            "0021": {"requires":
                     req("specs/0021-scope-under-maintenance.md")}}}
        def gates():
            # a fresh module namespace per call so the fixture's
            # reference_scope re-imports cleanly
            for k in [k for k in sys.modules if k == "reference_scope"]:
                del sys.modules[k]
            return vp._consistency_gates(manifest, root=fx)
        base = gates()
        assert base == [], f"fixture baseline not clean: {base}"
        checks.append("mutation baseline: gates clean on the real carriers")

        # (i) corrupt a matrix block in ONE carrier
        p20 = fx / "specs/0020-scoped-recall.md"
        orig = p20.read_text()
        p20.write_text(orig.replace(
            "| `absorption` |", "| `absorption-CORRUPTED` |", 1))
        assert any("SITE-MATRIX drift" in f for f in gates()), \
            "matrix mutation NOT caught"
        p20.write_text(orig)
        checks.append("mutation: corrupted matrix row -> gate FAILS")

        # (ii) remove a dependency from a header
        p21 = fx / "specs/0021-scope-under-maintenance.md"
        orig21 = p21.read_text()
        p21.write_text(orig21.replace(
            "Spec-Requires: 0009, 0014, 0016, 0018, 0019, 0020",
            "Spec-Requires: 0009, 0014, 0016, 0018, 0020"))
        assert any("dependency drift" in f for f in gates()), \
            "header mutation NOT caught"
        p21.write_text(orig21)
        checks.append("mutation: deleted header dependency -> gate FAILS")

        # (iii) reintroduce the retired formulation
        p20.write_text(orig + "\nthe row whose contributor_ref "
                              "names this record → its survivor\n")
        assert any("retired formulation" in f for f in gates()), \
            "forbidden-phrase mutation NOT caught"
        p20.write_text(orig)
        checks.append("mutation: retired formulation reintroduced -> "
                      "gate FAILS")

    for line in checks:
        print("PASS", line)
    print(f"verifier fault matrix: {len(checks)} classifications hold — "
          f"no fault becomes a successful skip; gate mutations FAIL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
