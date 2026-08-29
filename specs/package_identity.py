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
    # 0011 subject-scoped entitlement — first external round. Both internal
    # rounds are recorded in reviews.py, which is what this record is
    # validated against.
    "0011": {
        "v1": (1, {"0011": "v4"}),
        "v2": (2, {"0011": "v5"}),
        "v3": (3, {"0011": "v6"}),
        "v4": (4, {"0011": "v7"}),
        "v5": (5, {"0011": "v8"}),
        "v6": (6, {"0011": "v9"}),
        "v7": (7, {"0011": "v10"}),
        "v8": (8, {"0011": "v11"}),
        "v9": (9, {"0011": "v12"}),
        "v10": (10, {"0011": "v13"}),
        "v11": (11, {"0011": "v14"}),
        "v12": (12, {"0011": "v15"}),
        "v13": (13, {"0011": "v16"}),
        "v14": (14, {"0011": "v17"}),
        "v15": (15, {"0011": "v18"}),
    },
    # 0026 label/value agreement — first external round, same shape as 0011:
    # both internal rounds recorded, governed from v1.
    "0026": {
        "v1": (1, {"0026": "v4"}),
    },
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
    # 0001's rounds 1-2 (v2 reviewed 2026-07-31, v3 reviewed 2026-08-01) were
    # document-only sends that predate this record and the sealer; the line
    # enters the record at its first SEALED package, round 3.
    "0001": {
        "v3": (3, {"0001": "v4"}),
        "v4": (4, {"0001": "v5"}),
        "v5": (5, {"0001": "v6"}),
        "v6": (6, {"0001": "v7"}),
        "v7": (7, {"0001": "v8"}),
        "v8": (8, {"0001": "v9"}),
        "v9": (9, {"0001": "v10"}),
        "v10": (10, {"0001": "v11"}),
        "v11": (11, {"0001": "v12"}),
        "v12": (12, {"0001": "v13"}),
        "v13": (13, {"0001": "v14"}),
        "v14": (14, {"0001": "v15"}),
        "v15": (15, {"0001": "v16"}),
        "v16": (16, {"0001": "v17"}),
        "v17": (17, {"0001": "v18"}),
        "v18": (18, {"0001": "v20"}),
    },
    "0024-0025": {
        "v1": (1, {"0024": "v2", "0025": "v2"}),
        "v2": (2, {"0024": "v3", "0025": "v3"}),
        "v3": (3, {"0024": "v4", "0025": "v4"}),
        "v4": (4, {"0024": "v5", "0025": "v5"}),
        "v5": (5, {"0024": "v6", "0025": "v6"}),
        "v6": (6, {"0024": "v7", "0025": "v7"}),
        "v7": (7, {"0024": "v7", "0025": "v8"}),
        "v8": (8, {"0024": "v7", "0025": "v9"}),
        "v9": (9, {"0024": "v7", "0025": "v10"}),
        "v10": (10, {"0024": "v7", "0025": "v11"}),
        "v11": (11, {"0024": "v7", "0025": "v12"}),
        "v12": (12, {"0024": "v7", "0025": "v13"}),
        "v13": (13, {"0024": "v8", "0025": "v13"}),
        "v14": (14, {"0024": "v9", "0025": "v13"}),
        "v15": (15, {"0024": "v10", "0025": "v13"}),
        "v16": (16, {"0024": "v11", "0025": "v13"}),
        "v17": (17, {"0024": "v12", "0025": "v13"}),
        "v18": (18, {"0024": "v13", "0025": "v13"}),
        "v19": (19, {"0024": "v14", "0025": "v13"}),
        "v20": (20, {"0024": "v15", "0025": "v13"}),
        "v21": (21, {"0024": "v16", "0025": "v13"}),
        "v22": (22, {"0024": "v17", "0025": "v13"}),
        "v23": (23, {"0024": "v18", "0025": "v13"}),
        "v24": (24, {"0024": "v19", "0025": "v13"}),
    },
}

# C7-1: superseded/discarded seals, DISCLOSED — a governed row's canonical
# archive is the one its round's verdict quotes, witnessed by the ONE
# committed sidecar; earlier seals of the same version are named here so
# their absence from the sidecar set is a disclosure, never a gap.
# C8-1: the ONE row permitted a missing sidecar — the seal in flight,
# DECLARED here (explicit, diffable) rather than inferred from being the
# newest (the frontier exemption let the newest witness be deleted
# silently). The sealer refuses to seal any version not named here, and
# the sidecar commit that lands the witness also clears this.
IN_FLIGHT: tuple = ()              # C8-1/C9-1: no seal in flight
                                   # (0011-v15 sealed 20260829T0023Z,
                                   # sidecar committed)

DISCARDED_PRE_ROUND = (
    "0001-v3-20260822T2144Z (sealed, discarded unsent)",
    "0001-v3-20260822T2159Z (C-plus round-1 specimen; superseded)",
    "0001-v3-20260822T2236Z (C-plus round-2 specimen; superseded)",
    "0001-v7-20260823T1217Z (sealed pre-candidate-patch, discarded unsent)",
    "0024-0025-v13-20260823T2131Z (sealed, discarded unsent — research's "
    "§11 fidelity pass added the marker-witness note and the cell-A "
    "denominator fix before dispatch)",
    "0024-0025-v16-20260824T0102Z (sealed, discarded unsent — research's "
    "validator co-check found the canary file unchecked; the validator "
    "grew unknown-member refusal + the canary check before dispatch)",
    "0011-v6-20260828T0137Z (sealed, discarded unsent — the campaign "
    "EXTENSION to the census and contention checkers found six more "
    "mutants all missed and both checkers outside P1's domain; the "
    "reseal carries those fixes too)",
    "0011-v6-20260827T2333Z (sealed, discarded unsent — the dispatch was "
    "HELD for dev's own mutant campaign against the evidence artifacts, "
    "which found six of nine mutants MISSED; the reseal carries the "
    "hardened artifacts and the campaign record, since a package whose "
    "checks are known-bypassable should not ask for a review round)",
    "0026-v1-20260826T1130Z (sealed, discarded unsent — §6a's acceptance "
    "gate was MEASURED an hour later, and the measurement amended §3a; a "
    "package whose dispatch row said the gate was unmeasured would have "
    "understated what it carries)",
    "0001-v18-20260825T2101Z (sealed, discarded unsent — the terminus "
    "note was added in-archive so it ships WITH the package that asks "
    "its question, rather than following it by a side channel)",
)


def strict_archive_re(line: str, version: str):
    """C9-2: THE archive filename grammar, defined once. Predecessor
    selection already required `{line}-{version}-{YYYYMMDD}T{HHMM}Z.tar.gz`
    while lineage validation accepted any `\\S+.tar.gz`, so a
    self-consistent sidecar with a malformed name passed one gate and was
    invisible to the other. Every consumer parses archive names through
    this one pattern."""
    import re as _re
    return _re.compile(_re.escape(line) + "-" + _re.escape(version)
                       + r"-\d{8}T\d{4}Z\.tar\.gz")


def strict_any_version_re(line: str):
    """C9-2: the same grammar with the version and timestamp captured —
    for consumers that enumerate a line's archives (prior selection)."""
    import re as _re
    return _re.compile(_re.escape(line)
                       + r"-v(\d+)-(\d{8}T\d{4}Z)\.tar\.gz")


def lineage_problems(archives_dir) -> list:
    """C7-1: EXACT correspondence between the governed domain and the
    hash witnesses — every PACKAGES row must have exactly ONE committed
    sidecar. The history field points here; a pointer at witnesses that
    do not exist is a false carrier claim (the round-7 finding: v3/v4
    sidecars of DISPATCHED packages had been deleted during reseal
    cycles). A lost package must be disclosed in DISCARDED_PRE_ROUND or
    a LOST entry, never silently absent."""
    import pathlib as _pl
    import re as _re
    problems = []
    d = _pl.Path(archives_dir)
    # C9-1: the exemption channel is CONSTRAINED before it is honored —
    # a singleton, naming a governed row of a known line, whose sidecar
    # is genuinely absent. Round 9's attack widened IN_FLIGHT to cover a
    # deleted committed witness beside the real seal; an unconstrained
    # declaration was an exemption anyone could stretch.
    if len(IN_FLIGHT) > 1:
        problems.append(
            f"IN_FLIGHT declares {len(IN_FLIGHT)} seals — the declaration "
            f"is a singleton: one seal in flight, or none (C9-1)")
    for entry in IN_FLIGHT:
        parts = entry.rsplit("-v", 1)
        if (len(parts) != 2 or parts[0] not in PACKAGES
                or not _re.fullmatch(r"\d+", parts[1])):
            problems.append(
                f"IN_FLIGHT entry {entry!r} does not name a known governed "
                f"line as `<line>-v<round>` (C9-1)")
        elif f"v{parts[1]}" not in PACKAGES[parts[0]]:
            problems.append(
                f"IN_FLIGHT entry {entry!r} names no governed PACKAGES row "
                f"— a declaration with no row is a dead exemption (C9-1)")
        elif sorted(d.glob(f"{entry}-*.tar.gz.sha256")):
            problems.append(
                f"IN_FLIGHT entry {entry!r} already has a committed sidecar "
                f"— the sidecar commit must clear the declaration; a stale "
                f"declaration is a standing exemption (C9-1)")
    claimed = set()
    for line, versions in PACKAGES.items():
        for v in sorted(versions, key=lambda x: int(x[1:])):
            side = sorted(d.glob(f"{line}-{v}-*.tar.gz.sha256"))
            claimed.update(s.name for s in side)
            if not side and f"{line}-{v}" in IN_FLIGHT:
                continue    # C8-1: the EXPLICITLY declared in-flight seal
            if len(side) != 1:
                problems.append(
                    f"governed row {line}-{v} has {len(side)} committed "
                    f"sidecars, expected exactly one — the lineage the "
                    f"history field points at is incomplete (C7-1/C8-1)")
                continue
            # C8-1: the RECORD is validated, not just the filename — a
            # sidecar reading `not-a-digest  wrong-target` passed the
            # count check
            body = side[0].read_text().strip()
            m = _re.fullmatch(r"([0-9a-f]{64})\s+(\S+\.tar\.gz)", body)
            expected_target = side[0].name[: -len(".sha256")]
            if not m:
                problems.append(
                    f"{side[0].name}: sidecar body is not "
                    f"`<64-hex>  <name>.tar.gz` (C8-1)")
            elif m.group(2) != expected_target:
                problems.append(
                    f"{side[0].name}: declares target {m.group(2)!r}, its "
                    f"own name says {expected_target!r} (C8-1)")
            elif not strict_archive_re(line, v).fullmatch(expected_target):
                problems.append(
                    f"{side[0].name}: archive name does not match the ONE "
                    f"strict grammar `{line}-{v}-YYYYMMDDTHHMMZ.tar.gz` — "
                    f"a name the predecessor selector cannot parse must not "
                    f"stand as a lineage witness (C9-2)")
    # C9-2 (completeness half): a sidecar that names a round INSIDE the
    # governed domain — a known line at or past FIRST_GOVERNED — must be
    # claimed by a PACKAGES row. Pre-governed seals and other lines are
    # OUTSIDE the domain and draw no claim (C6-1: the record never infers
    # beyond what it governs — the first draft of this sweep flagged the
    # legitimate pre-governed 0022-0023 witnesses).
    for s in sorted(d.glob("*.tar.gz.sha256")):
        if s.name in claimed:
            continue
        for line in PACKAGES:
            m = _re.match(_re.escape(line) + r"-v(\d+)-", s.name)
            if m and int(m.group(1)) >= FIRST_GOVERNED.get(line, 10**9):
                problems.append(
                    f"{s.name}: sidecar names governed round "
                    f"{line}-v{m.group(1)} but NO PACKAGES row claims it — "
                    f"an unclaimed witness inside the governed domain "
                    f"(C9-2)")
                break
    return problems


def render_lineage(archives_dir) -> str:
    """The machine-checkable LINEAGE table for INDEX.md — generated from
    PACKAGES x the committed sidecars, discarded seals disclosed."""
    import pathlib as _pl
    d = _pl.Path(archives_dir)
    rows = ["## Lineage (generated: PACKAGES x committed sidecars — C7-1)",
            "", "| line | version | round | dispatched archive | sha256 |",
            "|---|---|---|---|---|"]
    for line in sorted(PACKAGES):
        for v in sorted(PACKAGES[line], key=lambda x: int(x[1:])):
            side = sorted(d.glob(f"{line}-{v}-*.tar.gz.sha256"))
            if len(side) == 1:
                sha, name = side[0].read_text().split()
                rows.append(f"| {line} | {v} | {PACKAGES[line][v][0]} | "
                            f"`{name}` | `{sha[:16]}…` |")
            else:
                rows.append(f"| {line} | {v} | {PACKAGES[line][v][0]} | "
                            f"**{len(side)} sidecars — LINEAGE GAP** | — |")
    rows += ["", "Superseded/discarded seals (disclosed, deliberately "
             "un-witnessed):", ""]
    rows += [f"- {x}" for x in DISCARDED_PRE_ROUND]
    return "\n".join(rows) + "\n"


# per-line: the version each line's mechanism first governed
FIRST_GOVERNED = {"0022-0023": 17, "0024-0025": 1, "0001": 3,
                  # governed from their first seal — these lines have
                  # no pre-governance history to exempt
                  "0011": 1, "0026": 1}


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


# ONE authority for what a candidate claim LOOKS like (R2-1: the sweep that
# refuses candidate-shaped claims outside the verified field must be shared
# by every carrier — COLLECTED.txt and PACKAGE_MANIFEST.txt — not copied).
CANDIDATE_LINE_RE = (r"specs/\S+\.md — [a-z][a-z -]{2,30} v\d+(?:\.\d+)?"
                     r" \(external candidate\)")


def candidate_field_problems(text: str, field: str, carrier: str) -> list:
    """POSITION-AND-LABEL binding of the candidate field, shared by every
    carrier (C3-1: the manifest check was presence-bound — `specs: none`
    on the real label with the correct field rendered behind a `backup:`
    prefix passed everything. R20-1's lesson, verbatim, on the other
    carrier): exactly one line begins `specs:`, the record-rendered field
    begins EXACTLY at that label's offset, and nothing candidate-shaped
    exists outside the field."""
    import re as _re
    problems = []
    labels = [m.start() for m in _re.finditer(r"(?m)^specs:", text)]
    if len(labels) != 1:
        problems.append(
            f"{carrier} carries {len(labels)} `specs:` fields, expected "
            f"exactly one — a second one can contradict the first (R20-1)")
        return problems
    if not text.startswith(field, labels[0]):
        got = text[labels[0]:labels[0] + len(field)].split("\n")[0]
        problems.append(
            f"{carrier}'s `specs:` field is not the rendered candidate "
            f"field. Found: {got!r}. The field must BEGIN at the label's "
            f"offset (C3-1: presence elsewhere is not the field stating it)")
        return problems
    # C4-1: END-bound too — start-bound alone accepted the canonical field
    # with a same-line contradiction appended ("… — withdrawn; no external
    # candidate is under review"). The byte after the field must be a
    # newline or EOF.
    end = labels[0] + len(field)
    if end < len(text) and text[end] != "\n":
        problems.append(
            f"{carrier}'s candidate field carries trailing bytes on its "
            f"final line ({text[end:end + 60]!r}) — the field must END at a "
            f"line boundary (C4-1: a start-bound field can still be "
            f"contradicted on its own line)")
    outside = _re.findall(CANDIDATE_LINE_RE, text.replace(field, "", 1))
    if outside:
        problems.append(
            f"{carrier} carries candidate-shaped claim(s) OUTSIDE its "
            f"verified field: {outside} (R18-1/R19-1)")
    return problems


def render_candidate_field(line: str, version: str) -> str:
    """The COLLECTED `specs:` field, whole — the unit that gets verified."""
    return LABEL + render_candidate_lines(line, version)


def _spec_status(name: str) -> str:
    """PACKAGE-R13-1: the candidate line's status word is DERIVED from the
    spec's ONE canonical `Spec-Status:` line, never typed here — the v13
    package described accepted 0025 and in-review 0024 both as `draft`
    because the word was a literal in the renderer. Fails closed: a spec
    file without a readable status line refuses the render."""
    import re as _re
    path = HERE.parent / name
    m = _re.search(r"^Spec-Status:\s*(\S[^\n]*?)\s*$",
                   path.read_text(), _re.M)
    if not m:
        raise ValueError(f"{name}: no Spec-Status line — the candidate "
                         f"carrier cannot state a status it cannot read")
    return m.group(1)


def render_candidate_lines(line: str, version: str, indent: str = INDENT) -> str:
    """The COLLECTED `specs:` block, generated from the record.

    R17-1: these two lines were template literals reading `draft v16` while the
    package was v17. A carrier that states a fact must be filled from the fact.
    PACKAGE-R13-1: the STATUS word is a fact too — derived per spec.
    """
    cands = candidates(line, version)
    out = []
    for i, spec in enumerate(sorted(cands)):
        name = _spec_filename(spec)
        out.append(f"{'' if i == 0 else indent}{name} — "
                   f"{_spec_status(name)} {cands[spec]} "
                   f"(external candidate)")
    return "\n".join(out)


def _spec_filename(spec: str) -> str:
    """The spec's path, DERIVED from the tree rather than recalled.

    This was a hand-maintained dict of five entries, and it refused the
    first seal of a sixth line with `no filename known` — after the suite
    was measured and the archive built, because nothing before that point
    consults it. A list of filenames maintained beside the files it names
    drifts the moment a file is added; the tree already knows.

    Strict on purpose: exactly one `specs/NNNN-*.md` must match. Zero means
    the packaged spec does not exist; more than one means the id is
    ambiguous and a carrier would have to guess, which is the failure this
    function exists to avoid.
    """
    hits = sorted(HERE.glob(f"{spec}-*.md"))
    if len(hits) != 1:
        raise KeyError(
            f"spec {spec!r} matches {len(hits)} files in specs/ "
            f"({[h.name for h in hits]}) — exactly one is required")
    return f"specs/{hits[0].name}"


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
