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

# version -> (round, {spec: candidate revision of that spec in this package})
PACKAGES = {
    "v17": (17, {"0022": "v18", "0023": "v18"}),
    "v18": (18, {"0022": "v19", "0023": "v19"}),
}

FIRST_GOVERNED = 17          # the domain declared in the docstring, mechanized


def _reviews():
    sys.path.insert(0, str(HERE))
    import importlib
    import reviews
    importlib.reload(reviews)
    return reviews.REVIEWS


def candidates(version: str) -> dict:
    """The per-spec candidate revisions for `version`, or raise KeyError."""
    return PACKAGES[version][1]


def render_candidate_lines(version: str, indent: str = "                 ") -> str:
    """The COLLECTED `specs:` block, generated from the record.

    R17-1: these two lines were template literals reading `draft v16` while the
    package was v17. A carrier that states a fact must be filled from the fact.
    """
    cands = candidates(version)
    names = {"0022": "specs/0022-source-revocation.md",
             "0023": "specs/0023-non-revival-under-maintenance.md"}
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
    for version, row in sorted(PACKAGES.items()):
        if not re.fullmatch(r"v\d+", version):
            problems.append(f"{version!r} is not a `vN` package version")
            continue
        if not (isinstance(row, tuple) and len(row) == 2
                and type(row[0]) is int and type(row[1]) is dict
                and row[1] and all(type(k) is str and type(v) is str
                                   for k, v in row[1].items())):
            problems.append(f"{version}: the row is not (round: int, "
                            f"{{spec: revision}}) with at least one spec")
            continue
        rnd, cands = row
        if rnd != int(version[1:]):
            problems.append(f"{version} declares round {rnd} — the round is "
                            f"DERIVED from the version and must be "
                            f"{int(version[1:])}")
        if rnd < FIRST_GOVERNED:
            problems.append(f"{version} is below the declared domain "
                            f"(v{FIRST_GOVERNED} onward)")
        for spec, rev in sorted(cands.items()):
            if not re.fullmatch(r"v\d+(\.\d+)?", rev):
                problems.append(f"{version} {spec}: {rev!r} is not a `vN` "
                                f"candidate revision")

        # EXACTLY ONE SENT ROW PER PACKAGED SPEC — the reviewer's requirement.
        # `no row` was already refused at the seal; two rows for one spec is
        # the other half of the same question, and it was unasked.
        pkg = f"{'-'.join(sorted(cands))}-{version}"
        bounded = re.compile(re.escape(pkg) + r"(?![0-9])")
        for spec in sorted(cands):
            sent = [r for r in _reviews()
                    if r["kind"] == "external" and r["spec"] == spec
                    and r["verdict"].startswith("SENT")
                    and bounded.search(r["verdict"])]
            if len(sent) != 1:
                problems.append(
                    f"{version} {spec}: found {len(sent)} SENT rows naming "
                    f"`{pkg}` in reviews.py, expected exactly one — a dispatch "
                    f"recorded twice or not at all (R17-1)")
                continue
            if sent[0]["round"] != rnd:
                problems.append(
                    f"{version} {spec}: the SENT row is at round "
                    f"{sent[0]['round']}, the package declares round {rnd}")
    return problems


def main(argv) -> int:
    problems = validate()
    if problems:
        print("package identity INVALID:\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    print(f"package identity: VALID ({len(PACKAGES)} package(s), each with "
          f"exactly one SENT row per packaged spec)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
