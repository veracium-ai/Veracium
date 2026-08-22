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
    # R12-2: a STALE transcript from an earlier run would satisfy every check
    # while describing a different tree. Remove it, so the measured run is the
    # only thing that can produce one.
    stale = ROOT / "specs" / "generated" / "evidence_run.json"
    if stale.exists():
        stale.unlink()
    out = scratch / "pytest_rs.txt"
    # C-plus: the argv and env are IMPORTED from the probe module, so the
    # command the probe RECORDS and the command sealing RUNS are one
    # authority (COLLECTED_HEADER_DESIGN §5.1.4).
    sys.path.insert(0, str(SPECS))
    import runtime_probe
    env = sealed_env(**runtime_probe.MEASUREMENT_ENV)
    r = subprocess.run(
        [sys.executable, *runtime_probe.MEASUREMENT_ARGV],
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


# ONE authority for the loose-carrier names (round 11, PACKAGE-R11-2: the
# diff-exclusion set and the manifest/extra tuple were two copies): drives
# diff exclusion, manifest generation, and the extra dict.
LOOSE_CARRIERS = ("COLLECTED.txt", "COLLECTED_pytest_rs.txt",
                  "PACKAGE_MANIFEST.txt",
                  "specs/generated/evidence_run.json",  # evidence_transcript.REL_PATH — asserted at seal time
                  "CHANGED_FROM_PREVIOUS.txt",
                  # C-plus (COLLECTED_HEADER_DESIGN §5.1): the structured
                  # record and the two captured raw artifacts it derives
                  # from — names asserted against collected_record at seal.
                  "collected_header.json",
                  "RUNTIME_PROBE.json",
                  "LAUNCHER_TRANSCRIPT.txt")


def _select_prior_archive(line: str, version: str, outbox: pathlib.Path):
    """PURE numeric prior-selection (round 11, PACKAGE-R11-1: the regression
    must run in an EXTRACTED review package, where there is no .git — so the
    selection logic owns no git call). Returns the newest archive of the
    line with a numeric version strictly below `version`, or None."""
    def _key(p: pathlib.Path):
        m = re.match(rf"{re.escape(line)}-v(\d+)-(\d+T\d+Z)\.tar\.gz$",
                     p.name)
        return (int(m.group(1)), m.group(2)) if m else None
    cur = int(version.lstrip("v"))
    priors = sorted((p for p in outbox.glob(f"{line}-v*.tar.gz")
                     if _key(p) and _key(p)[0] < cur), key=_key)
    return priors[-1] if priors else None


def _changed_from_previous(line: str, version: str,
                           outbox: pathlib.Path) -> str:
    """Member-level diff against the newest prior same-line archive found on
    the sealing host (outbox). Emits prior name+sha and added/removed/changed
    paths; the always-regenerated loose carriers (the LOOSE set below — one
    authority, no typed count) are listed under their own heading so real
    tree changes stand out."""
    import gzip as _gzip
    import hashlib as _hashlib
    import io as _io
    prior = _select_prior_archive(line, version, outbox)
    if prior is None:
        return ("No prior archive of this line was present on the sealing "
                "host — diff SKIPPED, named here rather than omitted.\n")
    prior_sha = _hashlib.sha256(prior.read_bytes()).hexdigest()

    def member_hashes(tgz: pathlib.Path) -> dict:
        out = {}
        with tarfile.open(fileobj=_io.BytesIO(
                _gzip.decompress(tgz.read_bytes()))) as tf:
            for m in tf.getmembers():
                if m.isfile():
                    out[m.name.removeprefix("./")] = _hashlib.sha256(
                        tf.extractfile(m).read()).hexdigest()
        return out

    old = member_hashes(prior)
    # the CURRENT tree at HEAD + the loose carriers are hashed after build by
    # the caller's verify step; here we hash the same inputs pre-build via
    # git archive of HEAD
    with tempfile.TemporaryDirectory() as td:
        tp = pathlib.Path(td) / "h.tar"
        _run(["git", "archive", "--format=tar", "--prefix=./", "HEAD",
              "-o", str(tp)], cwd=ROOT)
        new = {}
        with tarfile.open(tp) as tf:
            for m in tf.getmembers():
                if m.isfile():
                    new[m.name.removeprefix("./")] = _hashlib.sha256(
                        tf.extractfile(m).read()).hexdigest()
    LOOSE = set(LOOSE_CARRIERS)
    added = sorted(k for k in new.keys() - old.keys() if k not in LOOSE)
    removed = sorted(k for k in old.keys() - new.keys() if k not in LOOSE)
    changed = sorted(k for k in new.keys() & old.keys()
                     if new[k] != old[k] and k not in LOOSE)
    lines = [f"PREVIOUS: {prior.name}", f"SHA256:   {prior_sha}", "",
             f"CHANGED ({len(changed)}):"] + [f"  {k}" for k in changed]
    lines += ["", f"ADDED ({len(added)}):"] + [f"  {k}" for k in added]
    lines += ["", f"REMOVED ({len(removed)}):"] + [f"  {k}" for k in removed]
    lines += ["", "Always-regenerated loose carriers (not diffed): "
              + ", ".join(sorted(LOOSE)), ""]
    return "\n".join(lines)


def build_archive(name: str, extra: dict[str, str],
                  seal_epoch: int | None = None) -> pathlib.Path:
    """`git archive` of HEAD plus the loose files, with NO duplicate members.

    `seal_epoch` (impl-review round 1, F3): appended members are stamped with
    the DECLARED seal time, not the write time — C-plus §5.4 promises member
    mtimes ≤ the declared seal time, and the loose carriers were landing ~13s
    after it. Normalising at the source keeps the promise exact; verify
    enforces it with NO tolerance (the 900s tolerance belongs to the
    verifier's-own-clock check, a different contract)."""
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
                p.parent.mkdir(parents=True, exist_ok=True)   # nested member
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
                info.mtime = (int(seal_epoch) if seal_epoch is not None
                              else int(info.mtime))
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
    ("evidence_transcript.py (validate the shipped transcript)",
     [sys.executable, "specs/evidence_transcript.py"]),
    ("render_closure.py --check",
     [sys.executable, "specs/render_closure.py", "--check"]),
    ("render_operation.py --check",
     [sys.executable, "specs/render_operation.py", "--check"]),
    # R16-2: the lessons carrier was checked in the build tree and NOWHERE in
    # the archive, so a block appended after the build was invisible to the
    # only verification a reviewer actually receives. Every generated carrier
    # that ships must be re-checked from the extraction.
    ("review_lessons.py --check",
     [sys.executable, "specs/review_lessons.py", "--check"]),
    # R17-1: the identity record is the source every identity carrier is filled
    # from, so it is re-checked against reviews.py FROM THE EXTRACTION — where
    # a reviewer can run it — rather than only in the tree that built it.
    ("package_identity.py (the record agrees with reviews.py)",
     [sys.executable, "specs/package_identity.py"]),
    # C-plus: the header record conforms to the code-owned policy registry,
    # COLLECTED.txt recomputes byte-for-byte as one whole file, and every
    # field's required witness holds — all from the extraction.
    ("verify_extracted.py header",
     [sys.executable, "specs/verify_extracted.py", "header"]),
)


def identity_problems(archive_name: str, col: str, man: str,
                      members: set) -> list:
    """R16-1. Return the ways the package's THREE identity carriers disagree.

    The commit has been checked across both carriers since round 4. The
    VERSION was checked nowhere, so `--version v16` produced an archive named
    v16 whose manifest said `0022-0023-v15 — external ROUND 15` and whose
    COLLECTED header said `round-15 ... (v15)`: the version reached
    build_collected and controlled the FILENAME alone, while the identity a
    reviewer reads first came from a hand-edited template.

    Identity lives in several carriers, so all of them are read and compared
    here — a pure function over the extracted text, which is why it can be
    exercised per-carrier by a regression instead of only by building an
    archive.

    `members` is the archive's member set. It is REQUIRED, not optional with a
    default: R19-1 showed the carrier can name a path that does not exist, and
    a default of `None` meaning "skip the check" would be exactly the kind of
    silent absence this review keeps finding. A caller with no member list must
    say so by passing one.
    """
    problems = []
    stem = re.match(r"(.+)-(v\d+)-\d{8}T\d{4}Z\.tar\.gz$", archive_name)
    if not stem:
        return [f"the archive name {archive_name!r} does not carry a "
                f"`<specs>-v<N>-<timestamp>` identity (R16-1)"]
    mp = re.search(r"^PACKAGE:\s*(\S+)\s+—\s+external ROUND\s+(\d+)", man, re.M)
    if not mp:
        problems.append("PACKAGE_MANIFEST.txt has no `PACKAGE: <name> — "
                        "external ROUND <n>` identity line (R16-1)")
    # `COUPLED` is optional: multi-spec lines say it, a single-spec line
    # (0001 is the first) says nothing — the identity is the round+version.
    ch = re.search(r"round-(\d+) external-review package \((v\d+)\)", col)
    if not ch:
        problems.append("COLLECTED.txt has no `round-<n> "
                        "external-review package (<version>)` line (R16-1)")
    if problems:
        return problems

    claims = {
        "archive basename": (f"{stem.group(1)}-{stem.group(2)}",
                             int(stem.group(2)[1:])),
        "PACKAGE_MANIFEST.txt": (mp.group(1), int(mp.group(2))),
        "COLLECTED.txt": (f"{stem.group(1)}-{ch.group(2)}", int(ch.group(1))),
    }
    if len(set(claims.values())) != 1:
        problems.append(
            "the package's identity carriers disagree — "
            + "; ".join(f"{k} says {v[0]} round {v[1]}"
                        for k, v in claims.items())
            + " (R16-1: v16 shipped with both carriers saying v15)")

    # R17-1: AND THE PER-SPEC CANDIDATE REVISIONS, which round 16's fix did not
    # count as identity carriers — so v17 shipped `draft v16` on both spec
    # lines while the three carriers above agreed perfectly. The expected
    # values come from the structured record, so this cannot be satisfied by a
    # template and a matching typo.
    version = stem.group(2)
    line = stem.group(1)
    sys.path.insert(0, str(SPECS))
    import package_identity as pid
    if version not in pid.PACKAGES.get(line, {}):
        problems.append(f"specs/package_identity.py has no row for line "
                        f"{line} version {version} — the packaged candidate "
                        f"revisions are undeclared (R17-1)")
        return problems
    expected = pid.candidates(line, version)
    # NOT anchored to the start of a line: the first candidate shares its line
    # with the `specs:` label, so `^\s*specs/` silently found only the SECOND
    # one — and a check that sees one of two carriers is how R17-1 happened.
    # Caught by the clean control, which is the argument for keeping one.
    # R19-1 / R20-1: THE FIELD IS THE CARRIER, AND WHERE IT SITS IS PART OF IT.
    #
    # R19-1 stopped this from comparing extracted fields and made it compare
    # the rendered lines. R20-1 showed that was still not the carrier: the
    # check asked whether the block occurred ANYWHERE in COLLECTED, so a
    # package could answer
    #
    #     specs: none — this package has no external candidates
    #
    # on the reviewer-facing line and carry the correct block further down, and
    # every check passed on the contradiction. Presence somewhere stood in for
    # the field's value — the proxy class again, one level up from where it was
    # last closed.
    #
    # So the unit verified is the WHOLE FIELD, label included, rendered from
    # the identity record, required to be the file's ONLY `specs:` field, and
    # required to sit exactly where that field sits.
    field = pid.render_candidate_field(line, version)
    labels = [m.start() for m in re.finditer(r"(?m)^specs:", col)]
    if len(labels) != 1:
        problems.append(
            f"COLLECTED.txt carries {len(labels)} `specs:` fields, expected "
            f"exactly one — a second one can contradict the first (R20-1)")
        return problems
    # ...and in the HEADER, where a reviewer reads it. "Unique expected header
    # position" is enforced against the inventory marker rather than a line
    # number, so the template can grow without the rule going stale.
    sys.path.insert(0, str(SPECS))
    import skip_inventory as _si
    body_at = col.find(_si.BEGIN_MARKER)
    if body_at != -1 and labels[0] > body_at:
        problems.append(
            f"COLLECTED.txt's `specs:` field sits BELOW the generated "
            f"inventory block — the identity a reviewer reads is in the "
            f"header, and a field relocated out of it is not that field "
            f"(R20-1)")
        return problems
    if not col.startswith(field, labels[0]):
        got = col[labels[0]:labels[0] + len(field)].split("\n")[0]
        problems.append(
            f"COLLECTED.txt's `specs:` field is not the rendered candidate "
            f"field for {version}. Found: {got!r}. Expected the field to BEGIN "
            f"at that position with:\n{field}\n(R20-1: the block appearing "
            f"somewhere in the file is not the field stating it)")
        return problems

    # nothing of that shape anywhere else — an exact field says nothing about
    # what the rest of the carrier claims
    CAND_RE = r"specs/\S+\.md — draft v\d+(?:\.\d+)? \(external candidate\)"
    outside = re.findall(CAND_RE, col.replace(field, "", 1))
    if outside:
        problems.append(
            f"COLLECTED.txt carries candidate line(s) OUTSIDE its verified "
            f"field: {outside} — a carrier that states the same fact twice can "
            f"disagree with itself (R18-1/R19-1)")

    # AND EVERY DECLARED PATH MUST BE IN THE ARCHIVE. A field that matches the
    # generator perfectly still misdirects if the generator names a file the
    # package does not carry.
    normalised = {m[2:] if m.startswith("./") else m for m in members}
    for path in re.findall(r"(specs/\S+\.md) — draft", field):
        if path not in normalised:
            problems.append(
                f"COLLECTED.txt directs the reviewer to {path}, which is NOT a "
                f"member of the archive (R19-1)")
    return problems


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

        for p in identity_problems(path.name, col, man, set(names)):
            _fail(p)

        # C-plus §5.4: the archive basename and the record's ts field are
        # copies of ONE variable — required equal and labelled consistency,
        # not truth — and no member's mtime may postdate the declared seal
        # time beyond the declared tolerance.
        sys.path.insert(0, str(SPECS))
        import calendar as _cal
        import json as _json
        import time as _time
        import collected_record as _CR
        rec_path = d / _CR.RECORD_CARRIER
        if not rec_path.exists():
            _fail(f"{_CR.RECORD_CARRIER} is not in the archive — a package "
                  f"without its record cannot be verified")
        rec = _json.loads(rec_path.read_text())
        rec_ts = rec["fields"]["ts"]["value"]
        base_ts = re.search(r"-(\d{8}T\d{4}Z)\.tar\.gz$", path.name)
        if not base_ts or base_ts.group(1) != rec_ts:
            _fail(f"the basename timestamp "
                  f"{base_ts.group(1) if base_ts else 'absent'} and the "
                  f"record's ts {rec_ts} are not one canonical value (§5.4)")
        seal_epoch = _cal.timegm(_time.strptime(rec_ts, "%Y%m%dT%H%MZ"))
        # F3: EXACT — §5.4 promises mtime ≤ the declared seal time, and the
        # sealer now stamps appended members with the seal epoch, so there is
        # nothing for a tolerance to forgive. The 900s tolerance is the
        # verifier's-own-clock contract and does not apply here.
        with tarfile.open(path) as tf:
            late = [m.name for m in tf.getmembers()
                    if m.mtime > seal_epoch]
        if late:
            _fail(f"archive members postdate the declared seal time "
                  f"(§5.4, exact — F3): {late[:5]}")
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

    with tempfile.TemporaryDirectory() as td:
        scratch = pathlib.Path(td)
        # C-plus §5.3 STEP 1: run the measurement and harness commands.
        rs_path = measure(scratch)
        rs = rs_path.read_text()

        sys.path.insert(0, str(SPECS))
        import collected_record as CR
        import collected_render as CX
        import evidence_transcript
        import runtime_probe

        # §5.3 STEP 2: capture immutable raw outputs — files, digested into
        # the record at step 3, shipped in the archive. The record derives
        # FROM these files, never from the in-memory values that produced
        # them (blocking 3): agreement between record and render means
        # something only because both descend from the captures.
        probe_path = scratch / CR.PROBE_CARRIER
        pr = _run([sys.executable, "specs/runtime_probe.py"], cwd=ROOT,
                  env=sealed_env(**runtime_probe.MEASUREMENT_ENV))
        if pr.returncode != 0:
            _fail(f"the runtime probe failed (exit {pr.returncode}): "
                  f"{pr.stderr.strip()[:300]}")
        probe_path.write_text(pr.stdout)

        # R8-2 carried forward: harness results are PRODUCED, never typed —
        # now via capture files rather than in-memory strings.
        harness_captures = []
        for h in ("vector_harness.py", "store_concurrency_harness.py"):
            hp = ROOT / "specs" / "evidence" / "0022" / h
            if not hp.exists():
                continue
            hr = _run([sys.executable, str(hp)], cwd=ROOT)
            if hr.returncode != 0:
                _fail(f"{h} fails on the tree being sealed:\n{hr.stdout}")
            cap = scratch / f"harness_{h}.txt"
            cap.write_text(hr.stdout)
            harness_captures.append((str(hp.relative_to(ROOT)), cap))

        # R7-2 carried forward: the launcher runs on the FINAL tree, and its
        # complete stdout/stderr + exit status now ship as a digested
        # artifact (moderate 5) — the header line derives from the file.
        launcher_path = scratch / CR.LAUNCHER_CARRIER
        lv = scratch / "launcher-venv"
        lr = subprocess.run(
            ["bash", "specs/evidence/offline/run_offline.sh"],
            cwd=ROOT, capture_output=True, text=True,
            env=sealed_env(VERACIUM_OFFLINE_VENV=str(lv)))
        launcher_path.write_text(lr.stdout + lr.stderr
                                 + f"\n--- LAUNCHER EXIT: {lr.returncode} ---\n")
        if lr.returncode != 0:
            _fail(f"the offline launcher did not succeed on the final tree "
                  f"(exit {lr.returncode}); transcript kept at {launcher_path}")

        # R11-2: the evidence transcript the runner wrote during measure(),
        # validated before anything derives from it.
        tpath = ROOT / evidence_transcript.REL_PATH
        tproblems = evidence_transcript.validate(tpath, SPECS)
        if tproblems:
            _fail("the evidence transcript does not validate:\n  "
                  + "\n  ".join(tproblems))
        import json as _json
        # R16-1: PACKAGE IDENTITY IS DERIVED AND CROSS-CHECKED, not typed into
        # a template. `--version v16` produced an archive named v16 whose two
        # shipped carriers both still said v15/ROUND 15, because `version`
        # reached build_collected and was never used — it controlled the
        # FILENAME alone. Round 8's finding was four hand-maintained package
        # claims that had gone false; this was a fifth and a sixth, in the
        # identity line a reviewer reads first.
        #
        # The round number is not a second hand-kept fact either: it comes from
        # the version, and both are checked against the SENT row recorded in
        # specs/reviews.py before sealing. Sealing a version nobody dispatched,
        # or one whose recorded round disagrees, now fails here rather than
        # arriving as next round's finding.
        pkg = f"{'-'.join(specs)}-{a.version}"
        m = re.fullmatch(r"v(\d+)", a.version)
        if not m:
            _fail(f"--version {a.version!r} is not `v<N>`, so the round number "
                  f"cannot be derived from it (R16-1)")
        round_no = int(m.group(1))
        sys.path.insert(0, str(SPECS))
        import reviews as _reviews
        import package_identity as _pid

        # R17-1: the STRUCTURED identity record governs everything a carrier
        # may claim about this package. Round 16 fixed the three carriers the
        # reviewer named and left two — each spec's own candidate revision, in
        # COLLECTED lines 6-7 — as template literals, so v17 shipped saying
        # `draft v16`. A version with no row here cannot be sealed at all.
        for p in _pid.validate():
            _fail(f"the package identity record is invalid: {p}")
        _line = "-".join(specs)
        if a.version not in _pid.PACKAGES.get(_line, {}):
            _fail(f"specs/package_identity.py has no row for line {_line} "
                  f"version {a.version} — the package's round and each spec's "
                  f"candidate revision must be declared before sealing (R17-1)")
        rec_round, rec_cands = _pid.PACKAGES[_line][a.version]
        if rec_round != round_no:
            _fail(f"the identity record puts {a.version} at round {rec_round}, "
                  f"its version says {round_no}")
        if sorted(rec_cands) != sorted(specs):
            _fail(f"the identity record packages {sorted(rec_cands)} for "
                  f"{a.version}, --specs says {sorted(specs)}")
        # `pkg in verdict` would be a SUBSTRING match, and `0022-0023-v1`
        # occurs inside `0022-0023-v16` — a check that silently accepts the
        # wrong dispatch row for every single-digit version. Bounded on the
        # right so v1 stops matching v16, v17, v18...
        _pkg_re = re.compile(re.escape(pkg) + r"(?![0-9])")
        sent = [r for r in _reviews.REVIEWS
                if r["kind"] == "external" and r["spec"] in specs
                and r["verdict"].startswith("SENT") and _pkg_re.search(r["verdict"])]
        if not sent:
            _fail(f"no SENT row in specs/reviews.py names `{pkg}` — the "
                  f"dispatch must be recorded BEFORE sealing, so the archive "
                  f"carries the row that describes it (R16-1)")
        bad = sorted({r["round"] for r in sent} - {round_no})
        if bad:
            _fail(f"`{pkg}` is dispatched at round(s) {bad} in "
                  f"specs/reviews.py but its version says round {round_no} "
                  f"(R16-1)")

        # R10-2/R11-2: the module-level LOOSE_CARRIERS is the one authority;
        # its hardcoded carrier names are asserted against the live modules.
        if evidence_transcript.REL_PATH not in LOOSE_CARRIERS:
            _fail("LOOSE_CARRIERS does not carry evidence_transcript.REL_PATH "
                  "— the one authority drifted from the module it names")
        for carrier in (CR.RECORD_CARRIER, CR.PROBE_CARRIER,
                        CR.LAUNCHER_CARRIER):
            if carrier not in LOOSE_CARRIERS:
                _fail(f"LOOSE_CARRIERS does not carry {carrier} — the one "
                      f"authority drifted from collected_record")

        # §5.4: the DECLARED seal time is stamped after measurement and
        # captures complete, so the ordering checks (ts after the probe's
        # capture; archive-member mtimes not later than ts) can hold. One
        # canonical value reaches the basename and the header from the
        # record — consistency between copies of one variable, labelled as
        # exactly that (design §4).
        ts = time.strftime("%Y%m%dT%H%MZ", time.gmtime())

        # §5.3 STEP 3: derive the structured record FROM THE CAPTURES.
        record = CR.build_record(
            ROOT, line=_line, version=a.version, round_no=round_no,
            commit_full=commit, ts=ts, rs_path=rs_path,
            probe_path=probe_path, launcher_path=launcher_path,
            harness_captures=harness_captures, template_path=a.header,
            manifest_template_path=a.manifest)
        for p in CR.validate_record(record):
            _fail(f"the derived record does not conform to the code-owned "
                  f"registry: {p}")

        # §5.3 STEP 4: cross-check every witnessed field. The manifest is
        # rendered from the same record first so the cross-carrier witnesses
        # can read it; the captures are passed as overrides because the
        # archive does not exist yet.
        manifest = CX.render_manifest(record, a.manifest.read_text())
        for p in CX.manifest_problems(manifest, record,
                                      a.manifest.read_text()):
            _fail(f"the built manifest fails its own whole-file equation: "
                  f"{p}")
        wp = CR.witness_problems(
            record, ROOT, manifest_text=manifest,
            overrides={"COLLECTED_pytest_rs.txt": rs_path,
                       CR.PROBE_CARRIER: probe_path,
                       CR.LAUNCHER_CARRIER: launcher_path})
        if wp:
            _fail("seal-time witness cross-check failed:\n  "
                  + "\n  ".join(wp))

        # §5.3 STEP 5: render COLLECTED.txt from the record, then require
        # the whole-file equation of the BUILT text (blocking 2) before it
        # may become a carrier.
        template_text = a.header.read_text()
        header = CX.render_header(record, template_text)
        collected = build_collected(rs_path, specs, a.version, header)
        for p in CX.whole_file_problems(collected, record, template_text, rs):
            _fail(f"the built COLLECTED.txt fails its own whole-file "
                  f"equation: {p}")
        record_json = _json.dumps(record, indent=2, sort_keys=True) + "\n"
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
        extra = {
            "COLLECTED.txt": collected,
            "COLLECTED_pytest_rs.txt": rs,
            "PACKAGE_MANIFEST.txt": manifest,
            evidence_transcript.REL_PATH: tpath.read_text(),
            # Round 8 (L-line) package feedback: the machine-generated diff
            # against the previous same-line archive; a missing prior is a
            # NAMED skip, never silent.
            "CHANGED_FROM_PREVIOUS.txt": _changed_from_previous(
                _line, a.version, a.outbox),
            # C-plus: the record and the two captures it derives from ship
            # beside the carriers they witness (§5.1.4).
            CR.RECORD_CARRIER: record_json,
            CR.PROBE_CARRIER: probe_path.read_text(),
            CR.LAUNCHER_CARRIER: launcher_path.read_text(),
        }
        if set(extra) != set(LOOSE_CARRIERS):
            _fail("the extra dict and LOOSE_CARRIERS diverged — the one "
                  "authority split (R10-2)")
        import calendar as _cal2
        archive = build_archive(
            name, extra,
            seal_epoch=_cal2.timegm(time.strptime(ts, "%Y%m%dT%H%MZ")))

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
    print(f"measured {record['fields']['measured']['value']}")
    print(f"staged  {staged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
