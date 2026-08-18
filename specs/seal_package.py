#!/usr/bin/env python3
"""Seal an external-review package. ONE procedure, not five rounds of shell.

Every seal-time defect this review found was a hand-run step going wrong in a
way the sha256 could not show:

  round 2  a duplicate archive member, from `tar --append` of a missing file
  round 4  PACKAGE_MANIFEST written through an unquoted heredoc, so command
           substitution ATE the two backticked regex names in the paragraph
           explaining the finding
  round 4  COLLECTED and the manifest naming DIFFERENT commits
  round 5  `PLACEHOLDER_TS` shipped, because the round-5 substitution replaced
           the commit and the measured line and nobody replaced the timestamp
  round 5  pytest redirected straight into COLLECTED_pytest_rs.txt, so the
           packaged-state test read the file the run was still writing

None of those is subtle. All of them survived because the procedure lived in
my head and a shell history. This script is the procedure, and it REFUSES
rather than warns: a surviving placeholder, a member appearing twice, two
commits, an unverified extraction — each aborts the seal.

Usage:
    python3 specs/seal_package.py --specs 0022,0023 --version v6 \\
        --manifest path/to/manifest.txt [--outbox ~/Documents/veracium/outbox]

It does NOT commit, push, or send. It produces the artifact and stages it.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
ARCHIVES = SPECS / "archives"
OUTBOX_DEFAULT = pathlib.Path.home() / "Documents" / "veracium" / "outbox"


def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def _fail(msg):
    print(f"SEAL REFUSED: {msg}", file=sys.stderr)
    raise SystemExit(1)


def measure(scratch: pathlib.Path) -> pathlib.Path:
    """Run the suite to a SCRATCH path, never to the artifact's own name.

    Round 5 redirected pytest into COLLECTED_pytest_rs.txt directly, so the
    packaged-state test read a half-written file and failed a check that
    passed outside the run.
    """
    out = scratch / "pytest_rs.txt"
    env = dict(os.environ, VERACIUM_FORBID_NETWORK="1", PYTHONPATH="src")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests", "-p", "no:randomly", "-rs"],
        cwd=ROOT, env=env, capture_output=True, text=True)
    out.write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        _fail(f"the suite did not pass (exit {r.returncode}); see {out}")
    return out


def build_collected(rs_path: pathlib.Path, specs: list[str], version: str,
                    header: str) -> str:
    sys.path.insert(0, str(SPECS))
    import skip_inventory as S
    rs = rs_path.read_text()
    body = header + S.BEGIN_MARKER + "\n" + S.render(rs) + "\n" + S.END_MARKER + "\n"
    S.verify_collected(body, rs)
    problems = S.reconcile(rs)
    if problems:
        _fail("the sealed run does not reconcile:\n  " + "\n  ".join(problems))
    return body


def refuse_placeholders(*texts_and_names):
    """A placeholder that reaches the archive is a lie with a valid sha256.

    MENTION IS NOT USE. The first version of this guard matched any occurrence
    of "PLACEHOLDER", and refused the seal because the COLLECTED header
    EXPLAINS the round-5 PLACEHOLDER_TS defect in prose. That is the third
    mention-vs-use error in one day (a `pytest.skip(...)` in a docstring
    counted as a skip site; the invariant gate read finding ids as citations),
    and it is the same shape as the findings this package is answering: a
    checker whose definition of its own domain is wrong in one direction or
    the other.

    So the check is on VALUE POSITIONS: an unsubstituted `__TOKEN__` anywhere,
    or a legacy `PLACEHOLDER_*` immediately after a field's colon. Prose about
    placeholders is prose.
    """
    for text, name in texts_and_names:
        for m in re.finditer(r"__[A-Z][A-Z_]*__", text):
            _fail(f"{name} still carries the unsubstituted token {m.group(0)!r}")
        for m in re.finditer(r"^[A-Za-z][\w /()-]*:\s*(PLACEHOLDER[_A-Z]*|<TODO>)",
                             text, re.M):
            _fail(f"{name} has a placeholder in a FIELD VALUE: {m.group(0)!r} "
                  f"— round 5 shipped PLACEHOLDER_TS exactly this way")


def build_archive(name: str, extra: dict[str, str]) -> pathlib.Path:
    """`git archive` of HEAD plus the loose files, with NO duplicate members."""
    dest = ARCHIVES / f"{name}.tar.gz"
    with tempfile.TemporaryDirectory() as td:
        tar_path = pathlib.Path(td) / "p.tar"
        r = _run(["git", "archive", "--format=tar", "--prefix=./", "HEAD",
                  "-o", str(tar_path)], cwd=ROOT)
        if r.returncode != 0:
            _fail(f"git archive failed: {r.stderr}")
        with tarfile.open(tar_path, "a") as tf:
            existing = set(tf.getnames())
            for fname, content in extra.items():
                member = f"./{fname}"
                if member in existing:
                    _fail(f"{member} is already in the archive — appending it "
                          f"again is round 2's duplicate-member defect")
                p = pathlib.Path(td) / fname
                p.write_text(content)
                tf.add(p, arcname=member)
        data = tar_path.read_bytes()
    import gzip
    dest.write_bytes(gzip.compress(data, 9))
    return dest


def verify_archive(path: pathlib.Path, specs: list[str]) -> str:
    """Extract and RUN, because the build tree is not the artifact."""
    with tarfile.open(path) as tf:
        names = tf.getnames()
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        _fail(f"duplicate members: {sorted(dupes)}")
    with tempfile.TemporaryDirectory() as td:
        with tarfile.open(path) as tf:
            tf.extractall(td)
        d = pathlib.Path(td)
        col = (d / "COLLECTED.txt").read_text()
        man = (d / "PACKAGE_MANIFEST.txt").read_text()
        refuse_placeholders((col, "extracted COLLECTED.txt"),
                            (man, "extracted PACKAGE_MANIFEST.txt"))
        c1 = re.search(r"source commit:\s*([0-9a-f]{7,40})", col)
        c2 = re.search(r"^COMMIT:\s*([0-9a-f]{7,40})", man, re.M)
        if not c1 or not c2:
            _fail("one of the carriers does not name a commit")
        if not (c1.group(1).startswith(c2.group(1)[:7])
                or c2.group(1).startswith(c1.group(1)[:7])):
            _fail(f"COLLECTED names {c1.group(1)} and the manifest names "
                  f"{c2.group(1)} — round 4's two-commit defect")
        for harness in ("vector_harness.py", "store_concurrency_harness.py"):
            hp = d / "specs" / "evidence" / "0022" / harness
            if not hp.exists():
                continue
            r = _run([sys.executable, str(hp)], cwd=d)
            if r.returncode != 0:
                _fail(f"{harness} FAILS from the extracted archive:\n{r.stdout}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--specs", required=True, help="e.g. 0022,0023")
    ap.add_argument("--version", required=True, help="e.g. v6 (the ROUND)")
    ap.add_argument("--manifest", required=True, type=pathlib.Path)
    ap.add_argument("--header", required=True, type=pathlib.Path,
                    help="COLLECTED.txt header, everything above the inventory")
    ap.add_argument("--outbox", type=pathlib.Path, default=OUTBOX_DEFAULT)
    a = ap.parse_args()

    specs = a.specs.split(",")
    dirty = _run(["git", "status", "--porcelain"], cwd=ROOT).stdout.strip()
    if dirty:
        _fail("the tree is dirty — everything in the archive must be COMMITTED "
              "before the measurement, or the two carriers name different "
              "states:\n  " + dirty.replace("\n", "\n  "))
    commit = _run(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout.strip()
    ts = time.strftime("%Y%m%dT%H%MZ", time.gmtime())

    with tempfile.TemporaryDirectory() as td:
        scratch = pathlib.Path(td)
        rs_path = measure(scratch)
        rs = rs_path.read_text()
        measured = re.search(r"\d+ passed[^\n]*", rs).group(0)

        header = a.header.read_text()
        # EXTERNAL ROUND 7, R7-2: the launcher result was PROSE, carried over
        # from the previous round against a different test set. If the header
        # asks for it, the sealer RUNS the launcher on the final tree and
        # substitutes what it actually printed. A number nobody measured in
        # this state cannot reach the carrier.
        launcher = "not requested"
        if "__LAUNCHER__" in header:
            lv = scratch / "launcher-venv"
            lr = subprocess.run(
                ["bash", "specs/evidence/offline/run_offline.sh"],
                cwd=ROOT, capture_output=True, text=True,
                env=dict(os.environ, VERACIUM_OFFLINE_VENV=str(lv)))
            tail = (lr.stdout + lr.stderr).strip().splitlines()
            line = next((l for l in reversed(tail) if "passed" in l or "REFUS" in l), "")
            if lr.returncode != 0:
                _fail(f"the offline launcher did not succeed on the final tree "
                      f"(exit {lr.returncode}): {line}")
            launcher = line.strip()
        subs = {"__COMMIT__": commit[:7], "__COMMIT_FULL__": commit,
                "__TS__": ts, "__MEASURED__": measured, "__LAUNCHER__": launcher}
        manifest = a.manifest.read_text()
        for k, v in subs.items():
            header = header.replace(k, v)
            manifest = manifest.replace(k, v)

        collected = build_collected(rs_path, specs, a.version, header)
        refuse_placeholders((collected, "COLLECTED.txt"),
                            (manifest, "PACKAGE_MANIFEST.txt"))

        name = f"{'-'.join(specs)}-{a.version}-{ts}"
        archive = build_archive(name, {
            "COLLECTED.txt": collected,
            "COLLECTED_pytest_rs.txt": rs,
            "PACKAGE_MANIFEST.txt": manifest,
        })

    digest = verify_archive(archive, specs)
    (ARCHIVES / f"{name}.tar.gz.sha256").write_text(
        f"{digest}  {name}.tar.gz\n")

    a.outbox.mkdir(parents=True, exist_ok=True)
    for suffix in (".tar.gz", ".tar.gz.sha256"):
        shutil.copy2(ARCHIVES / f"{name}{suffix}", a.outbox / f"{name}{suffix}")
    staged = a.outbox / f"{name}.tar.gz"
    if hashlib.sha256(staged.read_bytes()).hexdigest() != digest:
        _fail("the staged copy does not match the sealed digest")

    print(f"sealed  {name}.tar.gz")
    print(f"sha256  {digest}")
    print(f"commit  {commit[:7]}  (both carriers)")
    print(f"measured {measured}")
    print(f"staged  {staged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
