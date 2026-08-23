#!/usr/bin/env python3
"""C4-2: EXACT wheelset verification for the no-pip bootstrap.

The first bootstrap required only (a) every wheel digest to appear
somewhere in the lock and (b) wheel count >= requirement count — so a
locked wheel could be REPLACED by a renamed duplicate of another locked
wheel and the set still "verified". This module binds each requirement
(name, version) to ITS OWN permitted digest set and requires exact set
equality, reading each wheel's identity from its METADATA inside the zip
(the filename is advisory; METADATA is the wheel's own claim).

Pure stdlib; importable (verify(wheels_dir, lock_path) -> list[str] of
problems) and runnable (exits 1 with the problems printed).
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import sys
import zipfile


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_lock(lock_text: str) -> tuple:
    """({(normalised name, version): set(sha256)}, [problems]) — STRICT
    (C5-2: the first parser silently ignored unsupported lines, so a
    direct-reference requirement APPENDED to the lock sat outside the
    computed set and the verifier accepted the lock anyway). Every
    non-blank, non-comment LOGICAL line must be exactly
    `name==version` followed by one or more `--hash=sha256:<64hex>`
    options; anything else — direct references, markers, other options,
    duplicates, orphan continuations — REFUSES."""
    problems: list = []
    reqs: dict = {}
    # join continuation lines into logical lines first
    logical: list = []
    buf = ""
    for raw in lock_text.splitlines():
        s = raw.rstrip()
        if s.endswith("\\"):
            buf += s[:-1] + " "
            continue
        logical.append(buf + s)
        buf = ""
    if buf.strip():
        problems.append(f"orphan continuation at EOF: {buf.strip()[:60]!r}")
    line_re = re.compile(
        r"^([A-Za-z0-9][A-Za-z0-9_.\-]*)==([A-Za-z0-9_.!+\-]+)"
        r"((?:\s+--hash=sha256:[0-9a-f]{64})+)\s*$")
    for ln in logical:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        m = line_re.match(s)
        if not m:
            problems.append(f"unsupported lock grammar (C5-2): {s[:80]!r}")
            continue
        key = (_norm(m.group(1)), m.group(2))
        if key in reqs:
            problems.append(f"duplicate declaration: {key[0]}=={key[1]}")
            continue
        reqs[key] = set(re.findall(r"--hash=sha256:([0-9a-f]{64})",
                                   m.group(3)))
    return reqs, problems


def wheel_identity(wheel: pathlib.Path) -> tuple:
    """(normalised name, version) from the wheel's OWN METADATA."""
    with zipfile.ZipFile(wheel) as z:
        meta_names = [n for n in z.namelist()
                      if n.endswith(".dist-info/METADATA")]
        if len(meta_names) != 1:
            raise ValueError(f"{wheel.name}: {len(meta_names)} METADATA "
                             f"members, expected exactly one")
        meta = z.read(meta_names[0]).decode(errors="replace")
    name = re.search(r"^Name:\s*(\S+)", meta, re.M)
    ver = re.search(r"^Version:\s*(\S+)", meta, re.M)
    if not name or not ver:
        raise ValueError(f"{wheel.name}: METADATA lacks Name/Version")
    return _norm(name.group(1)), ver.group(1)


def verify(wheels_dir: pathlib.Path, lock_path: pathlib.Path) -> list:
    """Every problem that makes this wheelset NOT the locked set."""
    reqs, problems = parse_lock(lock_path.read_text())
    if problems:
        return [f"{lock_path.name}: {p}" for p in problems]
    if not reqs:
        return [f"{lock_path.name}: no requirements parsed"]
    seen: dict = {}
    for w in sorted(wheels_dir.glob("*.whl")):
        try:
            ident = wheel_identity(w)
        except ValueError as e:
            problems.append(str(e))
            continue
        if ident in seen:
            problems.append(f"{w.name}: duplicate of {seen[ident]} — two "
                            f"wheels claim {ident[0]}=={ident[1]} (C4-2)")
            continue
        seen[ident] = w.name
        if ident not in reqs:
            problems.append(f"{w.name}: {ident[0]}=={ident[1]} is not in "
                            f"the lock")
            continue
        digest = hashlib.sha256(w.read_bytes()).hexdigest()
        if digest not in reqs[ident]:
            problems.append(f"{w.name}: sha256 {digest[:16]}… is not among "
                            f"{ident[0]}=={ident[1]}'s permitted hashes — "
                            f"a digest elsewhere in the lock does not count "
                            f"(C4-2)")
    missing = sorted(set(reqs) - set(seen))
    for name, ver in missing:
        problems.append(f"locked requirement {name}=={ver} has NO wheel on "
                        f"disk (C4-2: count parity is not set equality)")
    return problems


def main(argv) -> int:
    if len(argv) != 3:
        print("usage: verify_wheelset.py <wheels_dir> <lock_file>",
              file=sys.stderr)
        return 2
    problems = verify(pathlib.Path(argv[1]), pathlib.Path(argv[2]))
    if problems:
        print("REFUSED:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    print("wheelset: exact match against the lock (name==version per-"
          "requirement digests, no duplicates, no absences)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
