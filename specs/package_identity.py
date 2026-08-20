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
    "v19": (19, {"0022": "v20", "0023": "v20"}),
    "v20": (20, {"0022": "v21", "0023": "v21"}),
    "v21": (21, {"0022": "v22", "0023": "v22"}),
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


# EXTERNAL ROUND 20, R20-1. The label lived in the template and the lines were
# rendered here, so verification could only ask whether the LINES occurred
# somewhere in COLLECTED — and a package that answered `specs: none — this
# package has no external candidates` while carrying the correct block further
# down passed every check. The FIELD is the carrier, so the field is what is
# rendered: label and lines together, from here, verified as one artifact at
# one position.
LABEL = "specs:" + " " * 11
INDENT = " " * len(LABEL)


def render_candidate_field(version: str) -> str:
    """The COLLECTED `specs:` field, whole — the unit that gets verified."""
    return LABEL + render_candidate_lines(version)


def render_candidate_lines(version: str, indent: str = INDENT) -> str:
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

    # R18-1(c): the lower bound was enforced and CONTINUITY FROM IT WAS NOT, so
    # deleting the v17 row left the record valid while a governed package went
    # undeclared. A bound is not a domain: the governed versions must be the
    # exact contiguous run from FIRST_GOVERNED to the newest.
    nums = sorted(int(v[1:]) for v in PACKAGES if re.fullmatch(r"v\d+", v))
    if nums:
        want = list(range(FIRST_GOVERNED, max(nums) + 1))
        if nums != want:
            missing = sorted(set(want) - set(nums))
            problems.append(
                f"the governed versions are {['v%d' % n for n in nums]}, which "
                f"is not the contiguous run v{FIRST_GOVERNED}..v{max(nums)} — "
                f"missing {['v%d' % n for n in missing]} (R18-1: the lower "
                f"bound was checked and continuity from it was not)")
    elif PACKAGES:
        problems.append("no row carries a `vN` version")

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

        # R18-1(a): THE SENT PROSE IS A SECOND COPY OF THE CANDIDATE REVISIONS
        # and it was unchecked — the row could say `0022 at v999` beside a
        # record saying v19 and validate() returned clean, because it only
        # asked whether the row NAMED the package and the round. A dispatch row
        # may still describe what it carried; it may not disagree with the
        # record. Rows that make no such claim are fine — there is nothing to
        # contradict — so the rule is: every claim of this shape must match.
        for r in _reviews():
            if not (r["kind"] == "external" and r["spec"] in cands
                    and r["verdict"].startswith("SENT")
                    and bounded.search(r["verdict"])):
                continue
            for claimed_spec, claimed_rev in re.findall(
                    r"\b(\d{4}) at (v\d+(?:\.\d+)?)", r["verdict"]):
                if claimed_spec not in cands:
                    problems.append(
                        f"{version}: the {r['spec']} SENT row claims a revision "
                        f"for {claimed_spec}, which this package does not carry")
                elif cands[claimed_spec] != claimed_rev:
                    problems.append(
                        f"{version}: the {r['spec']} SENT row says "
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
    print(f"package identity: VALID ({len(PACKAGES)} package(s), each with "
          f"exactly one SENT row per packaged spec)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
