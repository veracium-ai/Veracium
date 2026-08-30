#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0011_mutant_registry.py::test_r18_transcript_checker_matrix
"""0011 — the digest-bound focused R18 transcript (the round-19 optional ask).

External round 19 ACCEPTED the spec and recorded one optional ask: a
digest-bound focused R18 transcript — the pristine pass plus the
replacement-mutant identity failure — so future reviewers need not replant
the mutant themselves to confirm PROCESS-R18-1's closure.

This harness is runner-observed end to end (the arc's own standard — no
claim channel exists):

  1. snapshot the tree (mutant_registry's `_snapshot`: the live tree is
     never touched, concurrent readers are safe by construction);
  2. run the R18 regression node in the PRISTINE snapshot — it must pass;
  3. apply the reviewer's replacement mutant (`raise type(_e)(*_e.args)`
     — same type, same message, fresh object) to the snapshot's copy of
     mutant_registry.py, byte-exactly the hunk the standing mutant test
     drives;
  4. run the same node again — it must FAIL, and fail AT the identity
     probe: the failure's own `E` line must carry the probe's message,
     proving type-and-message assertions were satisfied and object
     identity is what bit (a failure anywhere else is refused — a
     collection error, a skip, or a different assert is not a kill;
     PROCESS-R11-1's fail-open lesson).

The record binds by digest: the artifact's whole-file sha, the probe test
function's source-segment sha (the function, not the file, so unrelated
test-file edits do not stale the transcript while any probe change does),
and the mutated artifact's sha. `--check` (the default) is grammar-first —
strict duplicate-refusing parse, closed exactly-typed schema, raw bytes
equal to the canonical writer, digests current against the live tree — all
BEFORE any run is spent; then it re-executes both runs and requires the
recomputed record to equal the shipped one byte-for-byte. `--write` is
seal-time only and refuses to write a record whose runs misbehave.

    $PY specs/evidence/0011/check_r18_transcript.py            # check
    $PY specs/evidence/0011/check_r18_transcript.py --write    # regenerate
"""
from __future__ import annotations

import ast
import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mutant_registry as MR                                    # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
RECORD = pathlib.Path(__file__).resolve().parent / "r18_transcript.json"

NODE = ("tests/test_0011_mutant_registry.py::"
        "test_copy_exception_cleanup_is_regression_bound")
ARTIFACT = "specs/evidence/0011/mutant_registry.py"

# The reviewer's exact replacement mutant, byte-identical to the hunk the
# standing mutant test (test_the_exception_replacement_mutant_is_caught)
# drives: cleanup kept, type kept, message kept, exception OBJECT swapped.
HUNK_OLD = ('    except BaseException:\n'
            '        shutil.rmtree(snap, ignore_errors=True)\n'
            '        raise')
HUNK_NEW = ('    except BaseException as _e:\n'
            '        shutil.rmtree(snap, ignore_errors=True)\n'
            '        raise type(_e)(*_e.args)')

# The identity probe's own assertion message. It appears on a pytest `E`
# line only when THAT assert fires — matching it anywhere else in stdout
# (e.g. traceback source context) would bless a kill at a different site,
# so extraction requires the `E ` prefix and judge() requires the tag too.
PROBE_MARK = "is not the SAME OBJECT the copy raised"
PROBE_TAG = "(PROCESS-R18-1)"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def probe_source_sha(root) -> str:
    """Sha of the probe test FUNCTION's source segment. Binding the whole
    test file would stale the transcript on every unrelated edit; binding
    nothing would let the probe drift under a green transcript. The
    function is exactly the bytes the transcript's claim is about."""
    tfile, tname = NODE.split("::")
    text = (pathlib.Path(root) / tfile).read_text()
    tree = ast.parse(text)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == tname), None)
    if fn is None:
        raise ValueError(f"probe test {tname} not found in {tfile}")
    return _sha(ast.get_source_segment(text, fn) or "")


def hunk_problems(artifact_text: str) -> list:
    """The mutant must apply UNAMBIGUOUSLY: the old text exactly once."""
    n = artifact_text.count(HUNK_OLD)
    if n != 1:
        return [f"the mutant's old text occurs {n} times in {ARTIFACT} "
                f"(need exactly 1) — the transcript cannot say which "
                f"block it mutated"]
    return []


def _run(node: str, root) -> dict:
    """One isolated pytest run, mirroring mutant_registry._run_node (env
    scrub, private bytecode namespace, rootdir/confcutdir pinned) plus two
    transcript needs: stdout is captured for the probe-line extraction,
    and `--tb=short` bounds the failure context to the failing frame — a
    long traceback prints the WHOLE test body, so the probe's message
    would appear in source context whatever assert fired, and the
    discriminator would observe nothing."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    cache = tempfile.mkdtemp(prefix="veracium-r18-pyc-")
    env["PYTHONPYCACHEPREFIX"] = cache
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", node, "-q", "--tb=short",
             "-p", "no:randomly", f"--rootdir={root}",
             f"--confcutdir={root}"],
            cwd=root, capture_output=True, text=True, env=env)
    finally:
        shutil.rmtree(cache, ignore_errors=True)
    passed = failed = skipped = 0
    tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    for count, word in re.findall(r"(\d+) (passed|failed|skipped|xfailed|"
                                  r"xpassed|deselected)", tail):
        if word == "passed":
            passed = int(count)
        elif word == "failed":
            failed = int(count)
        else:
            skipped += int(count)
    return {"exit": r.returncode, "passed": passed, "failed": failed,
            "skipped": skipped, "stdout": r.stdout}


def probe_line(stdout: str):
    """The first pytest `E` line carrying the probe's message, whitespace
    normalized (alignment padding varies with source indent). None when
    the identity probe never fired."""
    for line in stdout.splitlines():
        s = line.strip()
        if s.startswith("E ") and PROBE_MARK in s:
            return " ".join(s.split())
    return None


def judge(pristine: dict, mutated: dict) -> list:
    """PURE verdict over the two observed runs — exact pins, not
    inequalities, so a widened node, a skip, or a collection error is
    named rather than absorbed. The mutation matrix drives this function
    directly with forged runs."""
    problems = []
    for name, want, run in (("pristine", (0, 1, 0, 0), pristine),):
        e, p, f, s = want
        if (run["exit"], run["passed"], run["failed"],
                run["skipped"]) != (e, p, f, s):
            problems.append(
                f"{name} run: exit {run['exit']}, {run['passed']} passed, "
                f"{run['failed']} failed, {run['skipped']} skipped — "
                f"expected exit {e}, {p} passed, {f} failed, {s} skipped")
    if mutated["exit"] == 0:
        problems.append("the replacement mutant SURVIVED — the mutated "
                        "run passed; the identity probe observes nothing")
        return problems
    if (mutated["passed"], mutated["failed"],
            mutated["skipped"]) != (0, 1, 0):
        problems.append(
            f"mutated run: {mutated['passed']} passed, "
            f"{mutated['failed']} failed, {mutated['skipped']} skipped — "
            f"expected exactly 1 failure and nothing else (a collection "
            f"error or a skip is not a kill; PROCESS-R11-1)")
    line = probe_line(mutated["stdout"])
    if line is None:
        problems.append(
            "the mutated run failed somewhere OTHER than the identity "
            "probe — no `E` line carries the probe's message; a kill at "
            "a different assert does not witness PROCESS-R18-1")
    elif PROBE_TAG not in line:
        problems.append(
            f"the probe line lost its {PROBE_TAG} tag — the message no "
            f"longer names the finding it witnesses")
    return problems


def compute(root) -> tuple:
    """Both runs, in a PRIVATE snapshot (the live tree is never touched;
    the snapshot is discarded whole, so no restore step exists to trust).
    Returns (record, problems); the record is None when the transcript
    cannot honestly be written."""
    root = pathlib.Path(root)
    artifact_text = (root / ARTIFACT).read_text()
    problems = hunk_problems(artifact_text)
    if problems:
        return None, problems
    art_sha = _sha(artifact_text)
    prb_sha = probe_source_sha(root)
    mut_sha = _sha(artifact_text.replace(HUNK_OLD, HUNK_NEW))
    snap = MR._snapshot(root)
    try:
        pristine = _run(NODE, snap)
        rest = MR._Restorer(pathlib.Path(snap))
        problems += rest.apply([(ARTIFACT, HUNK_OLD, HUNK_NEW)])
        if problems:
            return None, problems
        mutated = _run(NODE, snap)
    finally:
        shutil.rmtree(snap, ignore_errors=True)
    problems += judge(pristine, mutated)
    if problems:
        return None, problems
    record = {
        "schema": 1,
        "node": NODE,
        "artifact": ARTIFACT,
        "artifact_sha256": art_sha,
        "probe_sha256": prb_sha,
        "mutant": {"old": HUNK_OLD, "new": HUNK_NEW,
                   "mutated_sha256": mut_sha},
        "runs": {
            "pristine": {k: pristine[k]
                         for k in ("exit", "passed", "failed", "skipped")},
            "mutated": dict(
                {k: mutated[k]
                 for k in ("exit", "passed", "failed", "skipped")},
                identity_probe_line=probe_line(mutated["stdout"])),
        },
    }
    return record, []


def _is_int(x):
    return type(x) is int


def validate_record(rec) -> list:
    """Closed, exactly typed, and PINNED: the transcript's fixed shape —
    node, artifact, the mutant's hunks, both runs' outcomes — is part of
    the claim, so a shipped record asserting any other values is invalid
    on its face; only the three digests and the observed probe line are
    variable content."""
    if type(rec) is not dict:
        return ["record is not an object"]
    if sorted(rec) != ["artifact", "artifact_sha256", "mutant", "node",
                       "probe_sha256", "runs", "schema"]:
        return [f"top-level keys {sorted(rec)} != the closed set"]
    bad = []
    if rec["schema"] != 1 or not _is_int(rec["schema"]):
        bad.append(f"schema is {rec['schema']!r}, not 1")
    if rec["node"] != NODE:
        bad.append(f"node is {rec['node']!r}, not the R18 regression")
    if rec["artifact"] != ARTIFACT:
        bad.append(f"artifact is {rec['artifact']!r}, not {ARTIFACT}")
    for key in ("artifact_sha256", "probe_sha256"):
        v = rec[key]
        if type(v) is not str or not _HEX64.match(v):
            bad.append(f"{key} is not a 64-hex digest")
    m = rec["mutant"]
    if (type(m) is not dict
            or sorted(m) != ["mutated_sha256", "new", "old"]):
        bad.append("mutant is not the closed {old,new,mutated_sha256}")
    else:
        if m["old"] != HUNK_OLD or m["new"] != HUNK_NEW:
            bad.append("mutant hunks differ from the reviewer's "
                       "replacement mutant — the record describes a "
                       "different mutation")
        if type(m["mutated_sha256"]) is not str \
                or not _HEX64.match(m["mutated_sha256"]):
            bad.append("mutant.mutated_sha256 is not a 64-hex digest")
    runs = rec["runs"]
    if type(runs) is not dict or sorted(runs) != ["mutated", "pristine"]:
        bad.append("runs is not the closed {pristine,mutated}")
        return bad
    pin = {"pristine": {"exit": 0, "passed": 1, "failed": 0, "skipped": 0},
           "mutated": {"exit": 1, "passed": 0, "failed": 1, "skipped": 0}}
    for name, want in pin.items():
        run = runs[name]
        keys = sorted(want) + (["identity_probe_line"]
                               if name == "mutated" else [])
        if type(run) is not dict or sorted(run) != sorted(keys):
            bad.append(f"runs.{name} keys are not the closed set")
            continue
        for k, v in want.items():
            if not _is_int(run[k]) or run[k] != v:
                bad.append(f"runs.{name}.{k} is {run[k]!r}, must be "
                           f"exactly {v} (bool never passes as int)")
        if name == "mutated":
            line = run["identity_probe_line"]
            if type(line) is not str or PROBE_MARK not in line \
                    or PROBE_TAG not in line:
                bad.append("runs.mutated.identity_probe_line does not "
                           "carry the probe's message and its "
                           "PROCESS-R18-1 tag")
    return bad


def static_problems(raw: str, root) -> list:
    """Everything checkable WITHOUT spending a run, in the R10 order:
    parse, closed schema, canonical bytes, then digest currency against
    the live tree — a transcript describing stale bytes refuses before
    any subprocess starts."""
    try:
        rec = MR.strict_parse(raw)
    except ValueError as e:
        return [f"record does not strict-parse: {e}"]
    problems = validate_record(rec)
    if problems:
        return problems
    if raw != MR.canonical_bytes(rec):
        problems.append("shipped bytes are not the canonical writer's "
                        "output — nothing survives a parse-normalise "
                        "round trip (EVIDENCE-R9-1)")
    root = pathlib.Path(root)
    artifact_text = (root / ARTIFACT).read_text()
    problems += hunk_problems(artifact_text)
    live = {
        "artifact_sha256": _sha(artifact_text),
        "probe_sha256": probe_source_sha(root),
    }
    for key, want in live.items():
        if rec[key] != want:
            problems.append(
                f"{key} is stale: record {rec[key][:12]}…, live tree "
                f"{want[:12]}… — the transcript describes bytes this "
                f"tree no longer ships; regenerate with --write")
    if not problems and rec["mutant"]["mutated_sha256"] != \
            _sha(artifact_text.replace(HUNK_OLD, HUNK_NEW)):
        problems.append("mutant.mutated_sha256 does not equal the hunk "
                        "applied to the live artifact")
    return problems


def check_problems(record_path, root) -> list:
    """The full check: static first (grammar, pins, digest currency),
    then both runs re-executed and the recomputed record required to
    equal the shipped bytes exactly."""
    p = pathlib.Path(record_path)
    if not p.exists():
        return [f"{p} does not exist — run --write at seal time"]
    raw = p.read_text()
    problems = static_problems(raw, root)
    if problems:
        return problems
    computed, problems = compute(root)
    if problems:
        return problems
    if MR.canonical_bytes(computed) != raw:
        problems.append("recomputed transcript differs from the shipped "
                        "record — the runs no longer reproduce it")
    return problems


def main() -> int:
    write = "--write" in sys.argv
    if write:
        record, problems = compute(ROOT)
        if problems:
            for b in problems:
                print(f"REFUSED: {b}")
            return 1
        RECORD.write_text(MR.canonical_bytes(record))
        print(f"wrote {RECORD.relative_to(ROOT)} — pristine pass + "
              f"replacement-mutant identity kill, runner-observed")
        return 0
    problems = check_problems(RECORD, ROOT)
    if problems:
        for b in problems:
            print(f"PROBLEM: {b}")
        return 1
    print("r18 transcript: OK — pristine pass and replacement-mutant "
          "identity failure both reproduce; digests current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
