# Running the suite offline

This directory holds a self-contained, hash-locked test environment for the qualified runtime (CPython 3.14,
SQLite 3.45.1): thirteen wheels, `requirements-test.lock`, the launcher `run_offline.sh`, `two_phase.py`, which splits
the run and checks the split, and `verify_wheelset.py`, which checks the wheels against the lock exactly. No network is used.

## The invocation

```
VERACIUM_PYTHON=<a CPython 3.14 interpreter> bash specs/evidence/offline/run_offline.sh \
    --basetemp=<a directory OUTSIDE the package tree, on the SAME filesystem as it> \
    --junitxml=<results.xml>
```

- **`VERACIUM_PYTHON`** chooses the interpreter. The launcher builds a fresh venv (it refuses to reuse one), installs
  the locked wheels with no network, then asks the repository's own predicate (`runtime_supported()`, specs/0007)
  whether that runtime is qualified, and **refuses** if it is not.
- **The import preflight comes first.** Before building anything, the launcher has that interpreter import every
  compiled standard-library module in `stdlib_extensions.txt`: the set the launcher's own run loaded, measured by
  tracing every process it started (`stdlib_extensions_from_trace.py` says how). A build missing one (a CPython built
  without libffi has no `_ctypes`) is refused by name in seconds, not found partway through the suite.
  `VERACIUM_PREFLIGHT=warn` reports the same list and runs anyway, for a module only an accelerated path uses.
- **Two phases, by default** (the owner's ruling, 2026-11-08; a one-process run took 110m52s at 0.31.0). The launcher
  collects the suite once, then runs it in two pytest sessions, each with `-q -p no:randomly -rs`, so every skip prints
  with its reason. **Phase 1** runs every file but the phase-2 files under pytest-xdist, with `VERACIUM_OFFLINE_WORKERS`
  workers (default 8, capped at the host's cores). **Phase 2** runs the phase-2 files in ONE process: each file that
  refuses an xdist worker by the gate's own mark, plus the seam-model drivers. That is `JOINT-TEST-GROUPS.md`'s G1, and
  `two_phase.py files` refuses unless the two are equal. Then `two_phase.py check` refuses unless the two phases' junits
  ran exactly the collected node ids, each once, with phase 2 holding exactly the phase-2 files. Its line, the
  transcript's LAST, is the suite line in pytest's own grammar, counted from the two junits, with the launcher's wall
  time and each phase's own pytest line in parentheses. The exit is non-zero if a phase or the check is red.
  `VERACIUM_OFFLINE_MODE=single` runs the suite as ONE process instead, `-q tests -p no:randomly -rs`, as releases through
  0.31.0 did.
- **Further arguments** are pytest options, given to the collection and to both phases (`-k`, `-m`, `-x`, …). A phase
  whose share of a narrowed selection is empty exits 5, which counts as empty, not as red. Two-phase mode refuses a
  path or node id (pytest would run it in both phases); use `-k`, or the single mode.
- **`--basetemp` on the package's filesystem.** One test,
  `tests/test_0026_relay_lexicon.py::test_bootstrap_paths_cannot_alias_and_worklists_stay_local`, hard-links a file of
  the tree into its `tmp_path`. A hard link cannot cross filesystems, so with a `tmp_path` elsewhere (a tmpfs `/tmp`,
  for instance) it fails, and it says so: `… on another filesystem (EXDEV): run pytest with --basetemp=…`. That is a
  property of the run's environment, not of the product; the 0041 round-10 reviewer met it, and passing `--basetemp`
  beside the package fixed it. Do not put the base directory INSIDE the package tree: the tree under review is not
  written to. In two-phase mode each phase gets its own subdirectory, `<basetemp>/phase1` and `<basetemp>/phase2`,
  since pytest empties its base directory when a session starts.
- **`--junitxml`** records the same run machine-readably. In two-phase mode each phase writes `<results.xml>.phase1.xml`
  and `<results.xml>.phase2.xml`, and `<results.xml>` itself is the two merged: each phase's `<testsuite>` copied verbatim,
  phase 1's first, under one `<testsuites>`. `testcase_manifest.py` reads it as it reads any junit.

## The testcase manifest

```
python specs/evidence/offline/testcase_manifest.py <results.xml> [<out.tsv>]
```

One line per testcase: its identity, its outcome, and for a skip its reason, sorted, with a count footer. It refuses
(exit 1) if the cases do not reconcile with the testsuite's own totals. Two runs reconcile by `diff` of their
manifests.

## What this profile does not install

The launcher installs exactly the locked wheels (the test requirements: pytest, pytest-randomly, pydantic and their dependencies) and runs with `PYTHONPATH=src`; it does not install `mcp`, so the MCP tests skip, by name. In a git-archive export
(no `.git`), the tests that check pins against git history skip too, by name. Every skip prints its cause under `-rs`.

There is no offline MCP profile; the round-10 verdict called one optional. The MCP tests run in the full profile, `pip install -e ".[dev,mcp]"` from a fresh clone, which is how every review package's capture is made (network required).

## Running the suite in pieces

The suite is meant to run as ONE pytest process. If you split it, keep the two groups named in
[JOINT-TEST-GROUPS.md](JOINT-TEST-GROUPS.md) whole.
