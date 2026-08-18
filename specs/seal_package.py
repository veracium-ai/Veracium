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
import sqlite3
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


# EXTERNAL ROUND 11, R11-2. `measure()` copied ALL of os.environ and overrode
# two keys. With VERACIUM_EVIDENCE_CHILD=1 inherited from the shell, the
# evidence-runner test SKIPS — and the sealer went on generating "all N
# evidence commands ran" from the closure ledger, unconditionally, because the
# claim was counted rather than observed. The skip is inventoried, so
# reconciliation would not reject it either. A sealed package could therefore
# assert an execution that had been silently switched off.
#
# So the measurement environment is an ALLOWLIST, and the claim is OBSERVED.
_ENV_ALLOW = ("PATH", "HOME", "LANG", "LC_ALL", "TZ", "TMPDIR", "SHELL",
              "SSL_CERT_FILE", "SSL_CERT_DIR", "SOURCE_DATE_EPOCH")


def sealed_env(**extra) -> dict:
    """The ONLY environment sealing runs anything in.

    Anything not on the allowlist is dropped — most pointedly
    VERACIUM_EVIDENCE_CHILD, whose presence turns the evidence runner into a
    skip, and VERACIUM_* flags generally, which gate live tiers."""
    env = {k: v for k, v in os.environ.items() if k in _ENV_ALLOW}
    leaked = sorted(k for k in os.environ
                    if k.startswith("VERACIUM_") and k in env)
    if leaked:                      # belt and braces: the allowlist has no
        _fail(f"the allowlist leaks {leaked}")   # VERACIUM_* keys by design
    env.update(extra)
    return env


def measure(scratch: pathlib.Path) -> pathlib.Path:
    """Run the suite to a SCRATCH path, never to the artifact's own name.

    Round 5 redirected pytest into COLLECTED_pytest_rs.txt directly, so the
    packaged-state test read a half-written file and failed a check that
    passed outside the run.
    """
    out = scratch / "pytest_rs.txt"
    env = sealed_env(VERACIUM_FORBID_NETWORK="1", PYTHONPATH="src")
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


# Claims this project has WITHDRAWN. A withdrawn claim reaching the archive is
# the round-8 defect (four carriers) and its round-9 sequel (a fifth, inside
# the GENERATED inventory, contradicting the -rs output shipped beside it).
# Four carriers were swept by hand and a fifth survived, so the sweep is
# mechanical now: the sealer greps the BUILT artifact, not the sources.
#
# COROLLARY, learned the hard way and worth obeying: prose EXPLAINING a
# withdrawn claim must not QUOTE it. A check searching for a string cannot tell
# a live assertion from a description of one, and every carrier that quoted its
# own needle broke either the check or the claim. Describe; do not quote.
WITHDRAWN_CLAIMS = (
    (r"PACKAGED-STATE", "sealing measures BEFORE building COLLECTED, so no "
                        "carrier may claim the suite ran with COLLECTED present"),
    (r"measuring copy has no \.git", "sealing measures the git checkout"),
    (r"meets the 3\.35 floor", "the launcher asks runtime_supported(), not a "
                               "version floor"),
    (r"That copy has no `\.git`", "sealing measures the author's git checkout; "
                                  "the separate-extracted-copy workflow is "
                                  "withdrawn (R10-1)"),
    (r'"QUOTED VERBATIM" IS WITHDRAWN', "§4e-i is generated from the "
                                        "executable; the withdrawal is stale"),
)


def refuse_withdrawn_claims(*texts_and_names):
    for text, name in texts_and_names:
        for pat, why in WITHDRAWN_CLAIMS:
            m = re.search(pat, text)
            if m:
                _fail(f"{name} carries the WITHDRAWN claim {m.group(0)!r} — "
                      f"{why}")


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
                # EXTERNAL ROUND 10, R10-3: `git archive` writes root/root, and
                # tarfile.add() stamped the SEALING USER's uid/gid on the three
                # appended carriers. A plain `tar -xzf` then exits 2 on any host
                # that cannot restore uid 1000 — the reviewer needed
                # --no-same-owner to open the package at all. Normalise so the
                # archive extracts with the ordinary command.
                info = tf.gettarinfo(str(p), arcname=member)
                info.uid = info.gid = 0
                info.uname = info.gname = "root"
                info.mode = 0o644
                info.mtime = int(info.mtime)
                with open(p, "rb") as fh:
                    tf.addfile(info, fh)
        data = tar_path.read_bytes()
    import gzip
    dest.write_bytes(gzip.compress(data, 9))
    return dest


# EXTERNAL ROUND 9, R9-1. The carriers claimed the sealer reran "both
# harnesses and both verifiers from the EXTRACTED archive". It ran the two
# harnesses and nothing else — the verifiers ran BEFORE the archive existed,
# against the build tree. An execution trace of verify_archive() showed it.
#
# The claim was the better one, so the code moved to meet it rather than the
# claim shrinking to meet the code: everything below RUNS FROM THE EXTRACTION,
# which is the only place a reviewer's copy is actually represented. The
# registry is the single source for both the execution and the carrier's
# description, so they cannot drift apart again.
EXTRACTION_CHECKS = (
    ("vector_harness.py",
     [sys.executable, "specs/evidence/0022/vector_harness.py"]),
    ("store_concurrency_harness.py",
     [sys.executable, "specs/evidence/0022/store_concurrency_harness.py"]),
    # R11-1: NAMED SCRIPTS, not inline `-c`. A registry entry whose command is
    # a source string can only be checked by inspecting that string, and
    # `python -c "pass # verify_collected COLLECTED"` satisfied every such
    # inspection while doing nothing.
    ("verify_extracted.py collected",
     [sys.executable, "specs/verify_extracted.py", "collected"]),
    ("verify_extracted.py reconcile",
     [sys.executable, "specs/verify_extracted.py", "reconcile"]),
    ("render_closure.py --check",
     [sys.executable, "specs/render_closure.py", "--check"]),
    ("render_operation.py --check",
     [sys.executable, "specs/render_operation.py", "--check"]),
)


def verify_archive(path: pathlib.Path, specs: list[str]) -> str:
    """Extract and RUN, because the build tree is not the artifact."""
    # R10-3: ownership must be uniform, and the archive must open with the
    # ORDINARY command — not one carrying --no-same-owner.
    with tarfile.open(path) as tf:
        owners = {(m.uname or str(m.uid), m.gname or str(m.gid))
                  for m in tf.getmembers()}
    if len(owners) > 1:
        _fail(f"the archive carries mixed ownership {sorted(owners)} — a plain "
              f"`tar -xzf` fails on hosts that cannot restore those ids (R10-3)")
    with tempfile.TemporaryDirectory() as probe:
        pr = subprocess.run(["tar", "-xzf", str(path)], cwd=probe,
                            capture_output=True, text=True)
        if pr.returncode != 0:
            _fail(f"plain `tar -xzf` FAILS on this archive (exit "
                  f"{pr.returncode}): {pr.stderr.strip()[:200]}")
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
        ran = []
        for name, cmd in EXTRACTION_CHECKS:
            target = cmd[-1]
            if target.endswith(".py") and not (d / target).exists():
                _fail(f"{name}: {target} is not in the archive")
            r = _run(cmd, cwd=d)
            if r.returncode != 0:
                _fail(f"{name} FAILS from the EXTRACTED archive "
                      f"(exit {r.returncode}):\n{r.stdout}\n{r.stderr}")
            ran.append(name)
        if [n for n, _ in EXTRACTION_CHECKS] != ran:
            _fail(f"the extraction ran {ran}, not the registry")
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
        # EXTERNAL ROUND 8, R8-2: every one of these was TYPED into the header
        # and went stale — the harness line said 17/17 against an 18/18
        # executable, and "All 31" evidence commands described a 33-row ledger
        # of which the test runs 32. Numbers a human maintains beside numbers a
        # machine produces will disagree; these are produced.
        harnesses = []
        for h in ("vector_harness.py", "store_concurrency_harness.py"):
            hp = ROOT / "specs" / "evidence" / "0022" / h
            if not hp.exists():
                continue
            hr = _run([sys.executable, str(hp)], cwd=ROOT)
            if hr.returncode != 0:
                _fail(f"{h} fails on the tree being sealed:\n{hr.stdout}")
            harnesses.append(f"{h:<32} — {hr.stdout.strip().splitlines()[-1]}")
        harness_block = "\n                 ".join(harnesses)

        # R10-1: the reviewer guide promises the exact command, environment,
        # pytest version and node count. They were absent from COLLECTED, so
        # the promise was carried by a document that could not keep it. They
        # are MEASURED here and substituted.
        probe_env = sealed_env(VERACIUM_FORBID_NETWORK="1", PYTHONPATH="src")
        pv = subprocess.run([sys.executable, "-m", "pytest", "--version"],
                            cwd=ROOT, capture_output=True, text=True,
                            env=probe_env)
        if pv.returncode != 0:
            _fail(f"the pytest-version probe failed: {pv.stderr.strip()[:200]}")
        collected_n = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "tests", "--collect-only",
             "-p", "no:randomly"], cwd=ROOT, capture_output=True, text=True,
            env=probe_env)
        if collected_n.returncode != 0:
            _fail(f"the collection probe failed: "
                  f"{collected_n.stderr.strip()[:200]}")
        n_nodes = ""
        for ln in reversed((collected_n.stdout or "").strip().splitlines()):
            if "test" in ln and ("collected" in ln or "tests" in ln):
                n_nodes = ln.strip()
                break
        if not n_nodes:
            # R11-2: "collection unavailable" was a carrier shipping a shrug
            _fail("the collection probe produced no count line")
        import platform as _plat
        context = (
            f"command        VERACIUM_FORBID_NETWORK=1 PYTHONPATH=src "
            f"{sys.executable} -m pytest -q tests -p no:randomly -rs\n"
            f"                 cwd            {ROOT}  (the author's committed git "
            f"checkout — R10-1: the ONE canonical measurement site)\n"
            f"                 interpreter    {sys.executable}\n"
            f"                 python         {sys.version.split()[0]} "
            f"({_plat.machine()}, {_plat.system()} {_plat.release()})\n"
            f"                 pytest         {(pv.stdout or pv.stderr).strip()}\n"
            f"                 sqlite         {sqlite3.sqlite_version}\n"
            f"                 collection     {n_nodes or 'unavailable'}")

        sys.path.insert(0, str(SPECS))
        import closure_findings
        total_ev = len(closure_findings.CLOSURES)
        launcher_ev = sum(1 for c in closure_findings.CLOSURES
                          if "run_offline.sh" in c[6])
        # R11-2: OBSERVED, from the transcript the evidence runner wrote
        # during measure(). Reading an artifact costs nothing; the first
        # version spawned another pytest to watch the runner print a number,
        # and that duplication took the suite to 23 minutes.
        tpath = ROOT / "specs" / "generated" / "evidence_run.json"
        if not tpath.exists():
            _fail("no evidence transcript after the measured run — the runner "
                  "was skipped (a stray VERACIUM_EVIDENCE_CHILD, or a -k that "
                  "deselected it), so the all-commands-ran claim has no source")
        import json as _json
        tdata = _json.loads(tpath.read_text())
        observed = tdata["ran"]
        bad = [c for c in tdata["commands"] if c["exit"] != 0]
        if bad:
            _fail(f"the transcript records failing evidence commands: "
                  f"{[c['finding'] for c in bad]}")
        if observed != total_ev - launcher_ev:
            _fail(f"the evidence runner ran {observed} commands; the ledger "
                  f"holds {total_ev} with {launcher_ev} launcher entry(ies)")
        evidence_claim = (
            f"{total_ev} closure-evidence commands: {observed} OBSERVED "
            f"executing during this seal's measured run, each with its argv, "
            f"cwd, exit status and output digest recorded in "
            f"specs/generated/evidence_run.json (shipped), and {launcher_ev} "
            f"(the launcher) run separately — the runner skips that one "
            f"because it builds a venv and runs the whole suite")

        launcher = "not requested"
        if "__LAUNCHER__" in header:
            lv = scratch / "launcher-venv"
            lr = subprocess.run(
                ["bash", "specs/evidence/offline/run_offline.sh"],
                cwd=ROOT, capture_output=True, text=True,
                env=sealed_env(VERACIUM_OFFLINE_VENV=str(lv)))
            tail = (lr.stdout + lr.stderr).strip().splitlines()
            line = next((l for l in reversed(tail) if "passed" in l or "REFUS" in l), "")
            if lr.returncode != 0:
                _fail(f"the offline launcher did not succeed on the final tree "
                      f"(exit {lr.returncode}): {line}")
            launcher = line.strip()
        subs = {"__COMMIT__": commit[:7], "__COMMIT_FULL__": commit,
                "__TS__": ts, "__MEASURED__": measured, "__LAUNCHER__": launcher,
                "__HARNESSES__": harness_block, "__EVIDENCE__": evidence_claim,
                "__CONTEXT__": context,
                "__EXTRACTED__": "\n                 ".join(
                    f"{i+1}. {n}" for i, (n, _) in enumerate(EXTRACTION_CHECKS))}
        manifest = a.manifest.read_text()
        for k, v in subs.items():
            header = header.replace(k, v)
            manifest = manifest.replace(k, v)

        collected = build_collected(rs_path, specs, a.version, header)
        refuse_placeholders((collected, "COLLECTED.txt"),
                            (manifest, "PACKAGE_MANIFEST.txt"))
        guide = (ROOT / "specs" / "REVIEWER_GUIDE.md").read_text()
        refuse_withdrawn_claims((collected, "COLLECTED.txt"),
                                (manifest, "PACKAGE_MANIFEST.txt"),
                                # R10-1: the guide SHIPS in the archive and
                                # carried the withdrawn workflow claim for ten
                                # rounds while the guard read only two files
                                (guide, "specs/REVIEWER_GUIDE.md"))

        name = f"{'-'.join(specs)}-{a.version}-{ts}"
        archive = build_archive(name, {
            "COLLECTED.txt": collected,
            "COLLECTED_pytest_rs.txt": rs,
            "PACKAGE_MANIFEST.txt": manifest,
            "evidence_run.json": tpath.read_text(),
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
