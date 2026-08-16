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

    for line in checks:
        print("PASS", line)
    print(f"verifier fault matrix: {len(checks)} classifications hold — "
          f"no fault becomes a successful skip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
