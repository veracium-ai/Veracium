#!/usr/bin/env python3
"""The structured identity of every dispatched review package. One source.

EXTERNAL ROUND 17, R17-1. Round 16 made the package version PRODUCED rather
than typed — and enumerated three carriers of it: the archive basename, the
manifest's PACKAGE line, and COLLECTED's first line. There were FIVE. Lines 6
and 7 of COLLECTED name each specification's own candidate revision, and those
were still template literals: the v17 package shipped saying `draft v16` for
both specs while its SENT rows described them as v18. `identity_problems()`
read the three carriers it had been told about, found no disagreement, and the
whole archive verifier accepted it.

The fix that closes a finding is where the next one hides. Enumerating the
carriers a reviewer NAMED is not enumerating the carrier domain — this is the
carrier-completeness rule, and the round-16 fix broke it while obeying it.

So identity stops being prose. A package is:

    version    the package revision, `vN`, which also fixes the round number
    round      N, derived — never typed twice
    candidates {spec id: the revision of THAT spec inside this package}

and every carrier that states any of it is filled from here and verified
against here. The reviewer asked for exactly this record; it also answers the
guide's standing request, since it replaces the remaining free-text identity
claims with something a machine can check.

DECLARED DOMAIN: packages from v17 onward, the ones sealed under this
mechanism. Earlier archives are already sealed and immutable, so there is
nothing to keep true about them; a version with no row here CANNOT be sealed
(`seal_package` refuses), which is what makes the record total over everything
that can still be produced.
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

# line -> version -> (round, {spec: candidate revision in this package}).
# GENERALIZED for the second package line (0024/0025, first send 2026-08-21):
# a flat version->record map was AMBIGUOUS the moment two lines existed — v1
# of the L-pair would collide with a v1 of any future line, and the contiguity
# rule would weld unrelated lines into one run. Each line carries its own
# governed range.
PACKAGES = {
    "0022-0023": {
        "v17": (17, {"0022": "v18", "0023": "v18"}),
        "v18": (18, {"0022": "v19", "0023": "v19"}),
        "v19": (19, {"0022": "v20", "0023": "v20"}),
        "v20": (20, {"0022": "v21", "0023": "v21"}),
        "v21": (21, {"0022": "v22", "0023": "v22"}),
    },
    # L1 (author-blind quarantine) + L2 (relation-vocabulary enforcement):
    # independent Spec-Requires, coupled as ONE review package for the same
    # economy the 0004 triple used; per-spec verdicts requested.
    "0024-0025": {
        "v1": (1, {"0024": "v2", "0025": "v2"}),
        "v2": (2, {"0024": "v3", "0025": "v3"}),
        "v3": (3, {"0024": "v4", "0025": "v4"}),
        "v4": (4, {"0024": "v5", "0025": "v5"}),
        "v5": (5, {"0024": "v6", "0025": "v6"}),
        "v6": (6, {"0024": "v7", "0025": "v7"}),
    },
}

# per-line: the version each line's mechanism first governed
FIRST_GOVERNED = {"0022-0023": 17, "0024-0025": 1}


def _reviews():
    sys.path.insert(0, str(HERE))
    import importlib
    import reviews
    importlib.reload(reviews)
    return reviews.REVIEWS


def candidates(line: str, version: str) -> dict:
    """The per-spec candidate revisions for `line`/`version`, or raise KeyError."""
    return PACKAGES[line][version][1]


# EXTERNAL ROUND 20, R20-1. The label lived in the template and the lines were
# rendered here, so verification could only ask whether the LINES occurred
# somewhere in COLLECTED — and a package that answered `specs: none — this
# package has no external candidates` while carrying the correct block further
# down passed every check. The FIELD is the carrier, so the field is what is
# rendered: label and lines together, from here, verified as one artifact at
# one position.
LABEL = "specs:" + " " * 11
INDENT = " " * len(LABEL)


def render_candidate_field(line: str, version: str) -> str:
    """The COLLECTED `specs:` field, whole — the unit that gets verified."""
    return LABEL + render_candidate_lines(line, version)


def render_candidate_lines(line: str, version: str, indent: str = INDENT) -> str:
    """The COLLECTED `specs:` block, generated from the record.

    R17-1: these two lines were template literals reading `draft v16` while the
    package was v17. A carrier that states a fact must be filled from the fact.
    """
    cands = candidates(line, version)
    names = {"0022": "specs/0022-source-revocation.md",
             "0023": "specs/0023-non-revival-under-maintenance.md",
             "0024": "specs/0024-authorship-before-structural-quarantine.md",
             "0025": "specs/0025-relation-vocabulary-enforcement.md"}
    out = []
    for i, spec in enumerate(sorted(cands)):
        if spec not in names:
            raise KeyError(f"no filename known for spec {spec!r}")
        out.append(f"{'' if i == 0 else indent}{names[spec]} — "
                   f"draft {cands[spec]} (external candidate)")
    return "\n".join(out)


def validate() -> list:
    """Return a list of problems; empty means every row agrees with reviews.py."""
    problems = []
    for line, versions in sorted(PACKAGES.items()):
        if line not in FIRST_GOVERNED:
            problems.append(f"line {line!r} has no FIRST_GOVERNED entry")
            continue
        problems += _validate_line(line, versions, FIRST_GOVERNED[line])
    for line in FIRST_GOVERNED:
        if line not in PACKAGES:
            problems.append(f"FIRST_GOVERNED names line {line!r} with no packages")
    return problems


def _validate_line(line: str, versions: dict, first: int) -> list:
    """One package line's record, held to the round-18 rules WITHIN the line.

    R18-1(c) generalized: contiguity is a PER-LINE property — welding two
    lines into one run would demand a v2..v16 the L-pair never had, which is
    the same category error as no contiguity at all."""
    problems = []
    nums = sorted(int(v[1:]) for v in versions if re.fullmatch(r"v\d+", v))
    if nums:
        want = list(range(first, max(nums) + 1))
        if nums != want:
            missing = sorted(set(want) - set(nums))
            problems.append(
                f"{line}: governed versions {['v%d' % n for n in nums]} are "
                f"not the contiguous run v{first}..v{max(nums)} — missing "
                f"{['v%d' % n for n in missing]} (R18-1)")
    elif versions:
        problems.append(f"{line}: no row carries a `vN` version")

    for version, row in sorted(versions.items()):
        if not re.fullmatch(r"v\d+", version):
            problems.append(f"{line} {version!r} is not a `vN` package version")
            continue
        if not (isinstance(row, tuple) and len(row) == 2
                and type(row[0]) is int and type(row[1]) is dict
                and row[1] and all(type(k) is str and type(v) is str
                                   for k, v in row[1].items())):
            problems.append(f"{line} {version}: the row is not (round: int, "
                            f"{{spec: revision}}) with at least one spec")
            continue
        rnd, cands = row
        if rnd != int(version[1:]):
            problems.append(f"{line} {version} declares round {rnd} — the "
                            f"round is DERIVED from the version and must be "
                            f"{int(version[1:])}")
        if sorted(cands) != line.split("-"):
            problems.append(f"{line} {version}: candidates {sorted(cands)} do "
                            f"not match the line's own specs")
        for spec, rev in sorted(cands.items()):
            if not re.fullmatch(r"v\d+(\.\d+)?", rev):
                problems.append(f"{line} {version} {spec}: {rev!r} is not a "
                                f"`vN` candidate revision")

        pkg = f"{line}-{version}"
        bounded = re.compile(re.escape(pkg) + r"(?![0-9])")
        for spec in sorted(cands):
            sent = [r for r in _reviews()
                    if r["kind"] == "external" and r["spec"] == spec
                    and r["verdict"].startswith("SENT")
                    and bounded.search(r["verdict"])]
            if len(sent) != 1:
                problems.append(
                    f"{pkg} {spec}: found {len(sent)} SENT rows naming "
                    f"`{pkg}` in reviews.py, expected exactly one — a dispatch "
                    f"recorded twice or not at all (R17-1)")
                continue
            if sent[0]["round"] != rnd:
                problems.append(
                    f"{pkg} {spec}: the SENT row is at round "
                    f"{sent[0]['round']}, the package declares round {rnd}")

        # R18-1(a): SENT prose restating candidate revisions must AGREE
        for r in _reviews():
            if not (r["kind"] == "external" and r["spec"] in cands
                    and r["verdict"].startswith("SENT")
                    and bounded.search(r["verdict"])):
                continue
            for claimed_spec, claimed_rev in re.findall(
                    r"\b(\d{4}) at (v\d+(?:\.\d+)?)", r["verdict"]):
                if claimed_spec not in cands:
                    problems.append(
                        f"{pkg}: the {r['spec']} SENT row claims a revision "
                        f"for {claimed_spec}, which this package does not carry")
                elif cands[claimed_spec] != claimed_rev:
                    problems.append(
                        f"{pkg}: the {r['spec']} SENT row says "
                        f"`{claimed_spec} at {claimed_rev}` and the record "
                        f"declares {cands[claimed_spec]} — the prose is a "
                        f"second copy and it disagrees (R18-1)")
    return problems


def main(argv) -> int:
    problems = validate()
    if problems:
        print("package identity INVALID:\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    n = sum(len(v) for v in PACKAGES.values())
    print(f"package identity: VALID ({n} package(s) across {len(PACKAGES)} "
          f"line(s), each with exactly one SENT row per packaged spec)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
