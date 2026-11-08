"""Run one CI pytest job and leave the evidence a review stage reads from CI instead of a local fresh-clone capture.

    python .github/ci_run.py <out-dir> -- <pytest args...>

The owner approved replacing the local capture with CI's per-test results (2026-11-07). Research set five
requirements for its leg; this writes four of them, and the collect job writes the fifth's full list:

  (1) manifest.json, the binding: GITHUB_SHA, GITHUB_RUN_ID, GITHUB_RUN_ATTEMPT, the job's display name, the shard
      k/n, the workflow ref and the workflow file's git blob sha, sys.version, the exact pytest argv, pytest's exit
      code, and each file's sha256;
  (2) junit.xml, and selected.txt, the node ids this shard was given (from ci_shard's report, which this job also
      copies whole as shard-report.json);
  (3) pytest-output.txt, the raw output, and summary-tail.txt, its last 40 lines, for a committed script to derive
      the suite line from the junits rather than this text;
  (4) pip-freeze.txt (`pip freeze --all`) and the Python version, inside the manifest.

The output is streamed as well as kept, so the job log reads as before. The exit code is pytest's own, so the job
goes red exactly when pytest does. Nothing here changes what runs or how it is judged.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys

TAIL = 40


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _git(*a) -> str:
    r = subprocess.run(["git", *a], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else f"ERROR: {r.stderr.strip()}"


def main(argv) -> int:
    assert len(argv) >= 3 and argv[1] == "--", __doc__
    out = pathlib.Path(argv[0])
    out.mkdir(parents=True, exist_ok=True)
    args = list(argv[2:])
    junit = out / "junit.xml"
    # the `pytest` console script, as the job ran it before: `python -m pytest` would put the cwd on sys.path
    beside = pathlib.Path(sys.executable).parent / "pytest"
    cmd = [str(beside) if beside.exists() else (shutil.which("pytest") or "pytest"), *args, f"--junitxml={junit}"]
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze", "--all"], capture_output=True, text=True)
    (out / "pip-freeze.txt").write_text(freeze.stdout)
    env = dict(os.environ)
    report = pathlib.Path(env["VERACIUM_CI_SHARD_REPORT"]) if env.get("VERACIUM_CI_SHARD_REPORT") else None
    output = out / "pytest-output.txt"
    with output.open("w", encoding="utf-8") as f:
        p = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             encoding="utf-8", errors="replace")
        for line in p.stdout:
            sys.stdout.write(line)
            f.write(line)
        rc = p.wait()
    lines = output.read_text(encoding="utf-8").splitlines(keepends=True)
    (out / "summary-tail.txt").write_text("".join(lines[-TAIL:]), encoding="utf-8")
    if report is not None and report.exists():
        shutil.copyfile(report, out / "shard-report.json")
        sel = json.loads(report.read_text(encoding="utf-8"))["selected"]
        (out / "selected.txt").write_text("".join(f"{n}\n" for n in sel), encoding="utf-8")
    wf = os.environ.get("GITHUB_WORKFLOW_REF", "")
    wf_path = wf.split("@", 1)[0].split("/", 2)[-1] if wf else ".github/workflows/test.yml"
    manifest = {
        "github_sha": os.environ.get("GITHUB_SHA"), "head": _git("rev-parse", "HEAD"),
        "run_id": os.environ.get("GITHUB_RUN_ID"), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "job": os.environ.get("GITHUB_JOB"), "job_name": os.environ.get("VERACIUM_CI_JOB_NAME"),
        "shard": os.environ.get("VERACIUM_CI_SHARD"),
        "workflow_ref": wf or None, "workflow_sha": os.environ.get("GITHUB_WORKFLOW_SHA"),
        "workflow_path": wf_path, "workflow_blob": _git("rev-parse", f"HEAD:{wf_path}"),
        "python": sys.version, "implementation": platform.python_implementation(), "platform": platform.platform(),
        "argv": ["pytest", *cmd[1:]], "exit": rc,
        "files": {q.name: _sha(q) for q in sorted(out.iterdir()) if q.is_file() and q.name != "manifest.json"},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
