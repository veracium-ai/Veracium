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

**ONE COMMIT, NOT TWO. The package's `PACKAGE_MANIFEST.txt` and its
`COLLECTED.txt` must name the SAME commit.** Round 2's package named
`1d896041` (the archive commit) in one and `90c418c` (the tested commit) in
the other, because the suite was measured, then the pre-seal SENT rows were
committed, then the archive was built from the newer HEAD. The reviewer
could not tell whether an untested diff had entered the package — and could
not rule it out, which is the same thing. **Measure AFTER the last commit
that will be in the archive**, or state the two commits with the intervening
diff as an explicit allowlist. Identical is better; it needs no allowlist to
audit.

**MEASURE TO A SCRATCH PATH, THEN SEAL THE ARTIFACT.** `COLLECTED_pytest_rs.txt`
is a SEALED record of a completed run, and the packaged-state test READS it.
Redirect pytest straight into that filename and the test reads the file the
run is still writing — it saw an empty file, rendered the "no measured run"
block, and failed the byte-exact check while the same comparison passed
outside the run. Round 5 spent two full suite runs on it. Write to a scratch
path, copy it in AFTER the run completes, then regenerate COLLECTED's block
from the copy.

**Sealing is not sending. A sealed package is STAGED to
`~/Documents/veracium/outbox/`, BOTH files -- the `.tar.gz` and its `.sha256`
sidecar -- beside every prior package.** Building the archive here leaves it on
the dev machine and nowhere else; the outbox is the step that puts it where the
external reviewer's copy is taken from. Verify after copying (`sha256sum -c`
run INSIDE the outbox, against the sidecar that travelled with it), so the
check exercises the copy that will be sent rather than the one that was built.

This paragraph exists because the step was real, load-bearing, and written
down nowhere: on 2026-08-17 the `0004-0022-0023-v1` package was sealed here,
indexed, verified by extraction, and never staged -- while `reviews.py` already
carried its `SENT` rows. Every documented rule was followed and the package
still had not gone anywhere. **A ledger row saying SENT is only true once both
files are in the outbox**; write the row at seal time as the convention has it,
then stage, or the record outruns reality in the window between.

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
# COUPLED packages (two OR MORE specs reviewed as one round — REVIEWER_GUIDE
# Part 7; the external 0020/0021 reviewer asked for both candidates in the
# name): NNNN-NNNN[-NNNN...]-v<version>-<ts>.tar.gz — the FIRST number is the
# lead spec (grouping/sorting key); the rest name the coupled candidates.
#
# GENERALISED from exactly-two to N on 2026-08-17, for the 0004+0022+0023
# triple: 0022/0023 accept atomically (mutual `Spec-Requires`) and 0004 is
# 0022's critical-path dependency, so all three are reviewed as ONE round.
# The two-spec form was not a design decision — it was the arity the first
# coupled round happened to need.
#
# `<version>` MEANS TWO DIFFERENT THINGS AND THE DISTINCTION IS LOAD-BEARING.
# For a single-spec or lockstep-versioned package it is the SPEC version (the
# 0020/0021 pair moved v3..v15 together, so one number was honest). When the
# components carry DIFFERENT versions it cannot be a spec version without
# lying about two of them, so it is the EXTERNAL ROUND number for that
# package, and the component versions are carried in the package's own
# PACKAGE_MANIFEST.txt. The triple ships at v1 = its first external round,
# with 0004 at v3.1, 0022 at v2 and 0023 at v3 named in the manifest.
NAME = re.compile(r"^(\d{4}(?:-\d{4})*)-(impl-)?v(\d+)-(\d{8}T\d{4}Z)\.tar\.gz$")


def _entries():
    out, bad = [], []
    for f in sorted(ARCHIVES.glob("*.tar.gz")):
        m = NAME.match(f.name)
        if not m:
            bad.append(f.name)
            continue
        specs_field, impl, ver, ts = m.groups()
        # "0004-0022-0023" -> "0004+0022+0023"; the gate below splits on "+"
        # to cross-check EVERY component against reviews.py, so the join has
        # to stay lossless for any arity.
        spec = specs_field.replace("-", "+")
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        n = len(subprocess.run(["tar", "tzf", str(f)], capture_output=True,
                               text=True).stdout.split())
        out.append(dict(name=f.name, spec=spec, ver=int(ver), ts=ts,
                        impl=bool(impl),
                        kb=round(f.stat().st_size / 1024), sha=digest, files=n))
    return out, bad


# ---------------------------------------------------------------------------
# POST-ACCEPTANCE DELTAS — the disclosure form research ruled on (2026-08-16).
# An accepted package is a snapshot; when the repo later diverges from one, the
# divergence must be IMPOSSIBLE TO MISS at the next external contact rather than
# something a reviewer discovers. Each entry names the accepted seal, the
# artifacts that moved, why, and where the fix is. Rendered into the index, so
# any future round opens on the disclosed diff.
DELTAS = [
    {
        "package": "0020-0021-v15-20260816T1159Z.tar.gz",
        "seal": "449a0624c999d7c3…",
        "what": (
            "TWO defects in the ACCEPTED normative reference "
            "(`specs/evidence/0020/reference_scope.py`), both in "
            "`prune_absorbed_record`, both self-found AFTER acceptance and "
            "fixed in the reference AND the production port together."),
        "detail": [
            "(1) NON-TERMINATION on a record that is its own canonical "
            "absorber: the reparented rows it appended were themselves "
            "canonical and were appended to the list being iterated. Found by "
            "differentially fuzzing the new production implementation against "
            "the reference — 89 of 800 random prune ledgers hit it.",
            "(2) BOUNDED-WRONG at cycle length n>=2, found when research asked "
            "the domain question about fix (1): a 2-cycle TERMINATED but "
            "MANUFACTURED a self-absorbing row on the absorber, silently "
            "degrading to a closure-incomplete marker instead of refusing — "
            "the corrupt state fix (1) had just been written to reject.",
            "Both are failures to implement 0020 §4a-iii's OWN clause (corrupt "
            "linkage REFUSES), not gaps in the contract, so the fixes RESTORE "
            "accepted semantics rather than moving them. Adjudicated as "
            "defect-fix-not-amendment by research (the acceptance-record "
            "owner); the frozen surfaces V1–V19 / W1–W18 are untouched.",
            "The guard is now length-agnostic: the whole canonical-absorber "
            "chain is walked and ANY revisit refuses. No claim is made that "
            "n>2 reduces to n=2, and no impossibility argument is relied on — "
            "the one-absorber rule lives read-side only, so nothing prevents a "
            "corrupt ledger carrying mutual rows, and the defense is refusal.",
        ],
        "fix_commits": ["cd5285b", "2596f4f"],
        "vectors": "129 (self-absorption) · 130 (2-cycle) · 131 (3-cycle); "
                   "the regression covers n=1..5",
        "artifacts_moved": [
            ("specs/evidence/0020/reference_scope.py",
             "2a6ab277a04cdb1c…", "e71c0237e32c55ce…"),
            ("specs/evidence/0020/vectors.json",
             "9da681c9e6505a21…", "ace258d8c44e79d5…"),
        ],
        "found_by": ("a SECOND IMPLEMENTATION disagreeing with the first "
                     "(defect 1) and a SECOND REVIEWER closing its domain "
                     "(defect 2) — neither alone was sufficient, and fourteen "
                     "external rounds had not tried either input."),
    },
]

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
    # a COUPLED archive ("0020+0021") is evidence of a round for EACH
    # component spec — the cross-check requires rows per component, since
    # reviews.py records per-spec verdicts even for a shared package
    archived = {part for e in entries for part in e["spec"].split("+")}
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
    if DELTAS:
        blocks = []
        for d in DELTAS:
            moved = "\n".join(
                f"  * `{path}` — accepted `{was}` → now `{now}`"
                for path, was, now in d["artifacts_moved"])
            detail = "\n".join(f"  {line}" for line in d["detail"])
            blocks.append(
                f"### `{d['package']}` (accepted, seal `{d['seal']}`)\n\n"
                f"**{d['what']}**\n\n{detail}\n\n"
                f"* Fix commits: {', '.join('`' + c + '`' for c in d['fix_commits'])}\n"
                f"* Vectors: {d['vectors']}\n"
                f"* Found by: {d['found_by']}\n"
                f"* Artifacts that moved:\n{moved}")
        deltas = "\n\n".join(blocks)
    else:
        deltas = "*None — every accepted package matches the repo.*"
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

## Post-acceptance deltas — READ THIS FIRST at any next external contact

*Where the repo has moved away from a package that was already ACCEPTED. Listed
so a reviewer opens on the disclosed diff instead of discovering it.*

{deltas}
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
