#!/usr/bin/env python3
"""Index the review archives in specs/archives/, and enforce their naming.

Naming convention:

    NNNN-[impl-]v<version>-<YYYYMMDDTHHMMZ>.tar.gz   (impl- = implementation-review package)
    NNNN-NNNN-v<version>-<YYYYMMDDTHHMMZ>.tar.gz     (a COUPLED two-spec round; lead spec first)
    0002-v7-20260802T0410Z.tar.gz
    0020-0021-v3-20260815T1600Z.tar.gz

Spec number first so archives sort and group by spec; version so the archive is
tied to the document it carried; UTC timestamp so two archives of one version
are distinguishable and the ordering is unambiguous across sessions.

**The index is committed; the tarballs are not** -- Quentin's decision,
2026-08-02, on the size argument: each archive snapshots a tree already in git,
so committing it stores the repo inside itself, ~400KB per review round against
a 93KiB packed history.

The sha256 recorded here is what carries the provenance: it is tamper-evident,
and anyone holding a copy can verify it is the one that was sent.

**The known limit of that trade, stated because it is real:** a hash of a file
nobody kept proves nothing. The archives live on the dev machine only, so if
they are lost the index becomes a record that something existed rather than a
way to check it. Reversing this is one deleted line in `.gitignore`.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARCHIVES = ROOT / "specs" / "archives"
INDEX = ARCHIVES / "INDEX.md"
# `impl-v` marks a POST-IMPLEMENTATION review package (the accepted protocol
# preserves reviewer standing against the implementation — 0012 §12); its
# version numbers count implementation-review rounds, not spec versions.
# COUPLED packages (two specs reviewed as one round — REVIEWER_GUIDE Part 7;
# the external 0020/0021 reviewer asked for both candidates in the name):
# NNNN-NNNN-v<version>-<ts>.tar.gz — the FIRST number is the lead spec
# (grouping/sorting key); the second names the coupled candidate.
NAME = re.compile(r"^(\d{4})(?:-(\d{4}))?-(impl-)?v(\d+)-(\d{8}T\d{4}Z)\.tar\.gz$")


def _entries():
    out, bad = [], []
    for f in sorted(ARCHIVES.glob("*.tar.gz")):
        m = NAME.match(f.name)
        if not m:
            bad.append(f.name)
            continue
        spec, coupled, impl, ver, ts = m.groups()
        if coupled:
            spec = f"{spec}+{coupled}"
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        n = len(subprocess.run(["tar", "tzf", str(f)], capture_output=True,
                               text=True).stdout.split())
        out.append(dict(name=f.name, spec=spec, ver=int(ver), ts=ts,
                        impl=bool(impl),
                        kb=round(f.stat().st_size / 1024), sha=digest, files=n))
    return out, bad


def _archived_specs_missing_external_reviews(entries):
    """The invariant this file's own docstring asserts — "each archive is the
    exact package sent for one external review round" — but never enforced: an
    archived spec MUST have at least one external round recorded in reviews.py.

    Its absence is exactly how `0009`/`0010` silently reported `ext=0` in
    STATUS.md while 7 and 9 archives sat on disk (caught by a reader, 2026-08-08,
    who nearly filed a process violation on two shipped specs). The naming was
    machine-checked; the evidence was simply never compared to the ledger. This
    closes that gap: the evidence on disk and the count in reviews.py can no
    longer disagree by omission.

    Deliberately a floor (>=1), not equality: several specs have more archives
    than recorded rounds (a version re-packaged or re-sent within one round is
    normal), so `archives == rounds` would false-positive. Zero rounds under >=1
    archive is the only unambiguous defect, and it is the one that bit."""
    from reviews import REVIEWS  # specs/ is sys.path[0] when run as a script
    archived = {e["spec"] for e in entries}
    reviewed = {r["spec"] for r in REVIEWS if r["kind"] == "external"}
    return sorted(archived - reviewed)


def render() -> str:
    entries, bad = _entries()
    if bad:
        raise SystemExit(
            "archive names do not match the convention "
            "`NNNN-[impl-]v<version>-<YYYYMMDDTHHMMZ>.tar.gz`:\n  " + "\n  ".join(bad))
    missing = _archived_specs_missing_external_reviews(entries)
    if missing:
        raise SystemExit(
            "these specs have review archives on disk but NO external review "
            "round recorded in specs/reviews.py, so STATUS.md would report "
            f"ext=0 for them: {missing}. Add the rounds to reviews.py — the "
            "archives are the evidence they happened.")
    rows = "\n".join(
        f"| `{e['name']}` | {e['spec']} | {'impl-' if e.get('impl') else ''}v{e['ver']} | "
        f"{e['ts'][:4]}-{e['ts'][4:6]}-{e['ts'][6:8]} {e['ts'][9:11]}:{e['ts'][11:13]}Z | "
        f"{e['files']} | {e['kb']} KB | `{e['sha'][:16]}…` |"
        for e in sorted(entries, key=lambda e: (e["spec"], e.get("impl", False), e["ver"])))
    total = sum(e["kb"] for e in entries)
    return f"""<!-- GENERATED by specs/render_archives.py — do not hand-edit.
     Regenerate: python3 specs/render_archives.py --write
     Verify:     python3 specs/render_archives.py --check -->

# Review archives

**{len(entries)} archives, {total} KB.** Each is the exact package sent for one
external review round.

**Naming:** `NNNN-v<version>-<YYYYMMDDTHHMMZ>.tar.gz` — spec number first so
archives group by spec, version so the archive is tied to the document it
carried, UTC timestamp so two archives of one version are distinguishable and
the ordering is unambiguous across sessions. **The name is machine-checked.**

**The tarballs are not committed; this index is** — *decided 2026-08-02*. Each
archive snapshots a tree already in git, so committing it stores the repo inside
itself: undiffable, unprunable, ~400 KB per review round against a 93 KiB packed
history.

**The `sha256` is what carries the provenance** — tamper-evident, and anyone
holding a copy can prove it is the one that was sent. **The limit, stated
because it is real: a hash of a file nobody kept proves nothing.** These live on
the dev machine only; if they are lost this becomes a record that something
existed rather than a way to check it.

| archive | spec | version | sent (UTC) | files | size | sha256 |
|---|---|---|---|---|---|---|
{rows}

**To verify a copy you were sent:**

```sh
sha256sum 0002-v7-20260802T0410Z.tar.gz
```

**These are snapshots, not sources.** The repo is the source of truth; where an
archive and the repo disagree, the repo wins — and the disagreement is itself
the finding.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    want = render()
    if a.write:
        INDEX.write_text(want)
        print(f"wrote {INDEX.relative_to(ROOT)}")
        return 0
    if a.check:
        if not INDEX.exists() or INDEX.read_text() != want:
            print(f"{INDEX.name} is stale — run render_archives.py --write",
                  file=sys.stderr)
            return 1
        print("archive index is current and every name matches the convention")
        return 0
    print(want)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
