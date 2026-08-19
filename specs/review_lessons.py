#!/usr/bin/env python3
"""Classify every 0022/0023 review finding by FAILURE MECHANISM. One source.

EXTERNAL ROUND 15, R15-2. `specs/REVIEW_LESSONS.md` was written by hand: it
said "39 external findings collapse into six classes" while its six headings
summed to THIRTY, and it restated a suite duration ("~5min") that three
carriers in the same package measured at 16:45, 15:06 and 1:33. A document
about the second-copy class was itself two second copies — a count beside the
list it summarises, and a constant beside the thing it measures.

Nine findings were unclassified, and the prose could not show it. The counts
now come from `MECHANISM` below, which is checked TOTAL against the closure
ledger: every finding classified exactly once, no classification naming a
finding that does not exist, no class declared without an instance. Add a
finding to `closure_findings.py` and this module fails until it is classified.

`kind` is carried through from the ledger rather than flattened, because the
distinction turned out to matter: the ONE class I found myself (self-reference)
was never raised externally, and the old hand-written document hid that by
attributing external ids to it.

    python3 specs/review_lessons.py --check    # fails if the doc has drifted
    python3 specs/review_lessons.py --write    # regenerate the block
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
DOC = HERE / "REVIEW_LESSONS.md"
BEGIN = "<!-- GENERATED:mechanism-table -->"
END = "<!-- /GENERATED:mechanism-table -->"
SPECS = ("0022", "0023")


# key, title, the rule that follows from it, what mechanizes it now
CLASSES = (
    ("self-assertion",
     "A claim not produced by the thing it describes",
     "a number, status or property in a carrier must be PRODUCED by the thing "
     "it describes, in the same run that ships it",
     "the sealer substitutes measured values and refuses unsubstituted tokens; "
     "the transcript is read, not counted"),
    ("proxy",
     "The check binds a stand-in, not the property",
     "ask what the check would accept that is wrong — if a rename, a comment, "
     "a label or a cast defeats it, it binds a proxy",
     "argv pinned exactly with `-c` forbidden; every `-k` atom must select a "
     "test; the extraction registry binds behaviour"),
    ("second-copy",
     "The same fact stated twice",
     "if a fact appears twice, one copy is already wrong or will be — delete "
     "or generate, never sync. A COUNT IS A SECOND COPY OF A LIST",
     "generated blocks with `--check` gates, including THIS table; the "
     "withdrawn-claim sweep reads the BUILT artifact"),
    ("domain",
     "The rule's reach is not its domain",
     "enumerate the domain and prove the enumeration, or make the checker "
     "RAISE on anything it does not recognise — and check the reach is not "
     "too WIDE either, which is the same defect mirrored",
     "`render()` raises on an unknown category; the transcript schema is "
     "closed at every level with a mutation per declared field"),
    ("self-reference",
     "The check reads what its own run produces",
     "an evidence command must never read an artifact whose production it is "
     "part of — validate finished artifacts in the extraction",
     "the closure-evidence gate rejects any command reading an artifact the "
     "runner writes"),
    ("coercion",
     "A silent cast or default admits what the check meant to reject",
     "`type(x) is T`, never isinstance, in any integrity check — and never a "
     "default that fabricates the fact being checked",
     "the closed, exactly-typed transcript schema; `raised` is required "
     "explicitly rather than defaulted"),
    ("env-leak",
     "The producing environment leaked into the artifact",
     "an artifact must be built and verified as the RECIPIENT will open it, "
     "not as its producer happens to hold it",
     "normalized ownership on every member, a plain `tar -xzf` gate, and an "
     "allowlisted sealing environment"),
    ("disclosure",
     "Behaviour that is correct but never stated to whoever must act on it",
     "if the steady state surprises an operator, the surprise is the defect",
     "not mechanized — prose review only"),
)

CLASS_KEYS = tuple(k for k, *_ in CLASSES)

# (spec, round, finding) -> (class, why THIS mechanism and not a neighbouring
# one). A finding often exhibits two; the class recorded is the PRIMARY one —
# the mechanism that, if it had been absent, would have prevented the finding.
MECHANISM = {
    # ---- external ----------------------------------------------------------
    ("0022", 1, "F2"): ("proxy",
        "the host-supplied wall clock stood in for the order decisions were made in"),
    ("0022", 1, "F3"): ("self-assertion",
        "'supersession, never edit' was normative text true of no carrier that shipped"),
    ("0022", 1, "F4"): ("proxy",
        "`system_authored` stood in for the author-blindness the class claimed"),
    ("0023", 1, "F1"): ("domain",
        "quarantine reached one consumer of five — the rule's reach was not its domain"),
    ("0022", 3, "R3-1"): ("proxy",
        "`with conn:` was LABELLED BEGIN IMMEDIATE, and the harness was green on a "
        "different construction"),
    ("0022", 3, "R3-2"): ("domain",
        "the lint pattern matched one phrasing of the withdrawn rule, so the other "
        "phrasing stayed normative"),
    ("0022", 3, "R3-4"): ("second-copy",
        "a round count beside the rows it counts, disagreeing with them"),
    ("0022", 3, "R3-5"): ("domain",
        "the completeness gate's regex could not see four unconditional skips; the "
        "14-vs-6 mismatch was the symptom"),
    ("0023", 3, "F4"): ("domain",
        "N15 swept for the OLD CONDITION, so a consumer that never had one was "
        "outside the sweep's reach — form, not fact"),
    ("0023", 3, "R3-3"): ("domain",
        "the mirror case: the lifecycle predicate was applied too WIDELY and dropped "
        "episodes in a store with zero revocations"),
    ("0022", 4, "R4-1"): ("self-assertion",
        "the construction was NAMED atomic-and-shared while appending the row and "
        "never applying the effects — the name was the only evidence"),
    ("0022", 4, "R4-3"): ("second-copy",
        "the hand-maintained ledger drifted from its own rows for a third round"),
    ("0022", 4, "R4-4"): ("domain",
        "`render()`'s hard-coded category list silently dropped a whole category"),
    ("0023", 4, "R4-2"): ("second-copy",
        "the section header contradicted a row of the table beneath it"),
    ("0022", 5, "R5-1"): ("domain",
        "the failure outcomes were not total: a failing rollback and every "
        "IntegrityError fell outside the enumerated cases"),
    ("0022", 5, "R5-2"): ("proxy",
        "the BUSY test measured SQLite's internal wait — a stand-in for the branch "
        "it was named after"),
    ("0022", 5, "R5-3"): ("proxy",
        "a per-ROUND row stood in for the per-FINDING row PROCESS §4a requires"),
    ("0022", 5, "R5-4"): ("proxy",
        "pytest's emitted reason was matched against source-site tokens — two "
        "representations compared as if one were the other"),
    ("0022", 6, "R6-1"): ("domain",
        "the rollback boundary caught Exception while the operation caught "
        "BaseException, leaving part of its own domain uncovered"),
    ("0022", 6, "R6-2"): ("second-copy",
        "a withdrawn sentence survived beside the generated block that replaced it"),
    ("0022", 6, "R6-3"): ("second-copy",
        "the closure ledger was a hand-maintained twin of the generated one"),
    ("0023", 6, "R6-3"): ("second-copy",
        "the same twin, on 0023's ledger"),
    ("0022", 6, "R6-4"): ("self-assertion",
        "the launcher invented its own qualification rule and certified against it, "
        "while runtime_supported() said False"),
    ("0022", 7, "R7-1"): ("proxy",
        "set-equality of ids stood in for per-finding validation, so a wrong round, "
        "an erased evidence string and a duplicate all passed"),
    ("0022", 7, "R7-2"): ("second-copy",
        "the reproduction carrier restated the previous round's launcher result"),
    ("0022", 8, "R8-1"): ("coercion",
        "`.get(..., [])` made an OMITTED field indistinguishable from a declared "
        "absence — a default that fabricated the fact"),
    ("0022", 8, "R8-2"): ("self-assertion",
        "four package claims were hand-maintained beside the executables that "
        "contradicted them"),
    ("0022", 9, "R9-1"): ("self-assertion",
        "both carriers claimed an extracted-archive rerun that did not happen"),
    ("0022", 10, "R10-1"): ("second-copy",
        "the reviewer guide's workflow contradicted COLLECTED for ten rounds"),
    ("0022", 10, "R10-2"): ("proxy",
        "the extraction registry bound LABELS, so swapping a command for "
        "`python -c pass` was invisible"),
    ("0022", 10, "R10-3"): ("env-leak",
        "the sealing user's uid/gid rode into the archive, so a plain `tar -xzf` "
        "exited 2 for the recipient"),
    ("0022", 11, "R11-1"): ("proxy",
        "the binding was textual containment of two names, satisfiable by a "
        "program that does nothing"),
    ("0022", 11, "R11-2"): ("env-leak",
        "sealing inherited the whole environment, so a recursion marker turned the "
        "evidence runner into a skip"),
    ("0022", 12, "R12-1"): ("self-assertion",
        "the evidence claim had no source read: deleting the transcript entirely "
        "still produced a passing archive"),
    ("0022", 12, "R12-2"): ("self-assertion",
        "`ran` was trusted rather than derived, so a zero-record transcript "
        "claiming 40 satisfied every check"),
    ("0022", 13, "R13-1"): ("coercion",
        "`exit: false` passed `!= 0` because bool subclasses int; a 64-character "
        "non-hex string passed a length check"),
    ("0022", 13, "R13-2"): ("second-copy",
        "'the SAME six checks' over seven, in the sentence explaining that the list "
        "must not be maintained twice"),
    ("0022", 13, "R13-3"): ("second-copy",
        "a selector naming a test that had been replaced — a stale copy of a name "
        "that lives in the test file"),
    ("0022", 14, "R14-1"): ("coercion",
        "`ran: 45.0` == 45, a 64-digit integer digest through `str()`, a duplicate "
        "vanishing into a set"),
    ("0022", 15, "R15-1"): ("domain",
        "closedness was established for command objects and not for the object "
        "holding them — the property's own domain is every level with keys"),
    ("0022", 15, "R15-2"): ("second-copy",
        "hand-written class counts beside the findings they count, and a restated "
        "duration beside three carriers that measure it"),

    # ---- internal / self-found --------------------------------------------
    ("0022", 1, "M1"): ("domain",
        "'the sweep is pure and can be re-run' quantified over one moment; its "
        "domain is every moment, and the inputs mutate"),
    ("0022", 1, "M4"): ("disclosure",
        "complete=False is the expected steady state on a consolidation-bearing "
        "store and operators had not been told"),
    ("0022", 1, "S1"): ("domain",
        "the sweep's record domain was unenumerated — 'records' silently meant "
        "edges, and episode text renders into recall"),
    ("0023", 1, "M2"): ("domain",
        "the one §4 seam with no executed command turned out to have no verb at "
        "all — an unexercised cell of the domain"),
    ("0023", 1, "M3"): ("domain",
        "the supersession-refusal path was covered by neither rule of the split"),
    ("0023", 1, "S1"): ("domain",
        "0022's unenumerated record domain, inherited through the mutual "
        "Spec-Requires"),
    ("0023", 1, "S2"): ("self-assertion",
        "the lift asymmetry's justification asserted the inputs were not decidable "
        "from the record; they are all ON the record"),
    ("0023", 2, "S3"): ("domain",
        "quarantine-at-birth wrote a field no reader consulted — enforcement that "
        "reached none of its domain"),
    ("0022", 15, "R15-3"): ("self-reference",
        "a test read the live transcript another test writes, and pytest-randomly "
        "shuffles order — so CI failed on some seeds from round 12 onward"),
    ("0022", 14, "R14-2"): ("self-reference",
        "R7-1's evidence selected the evidence RUNNER, whose nested child skips on "
        "the recursion marker, so half the command exercised nothing and exited 0"),
}


def _ledger():
    sys.path.insert(0, str(HERE))
    import importlib
    import closure_findings
    importlib.reload(closure_findings)
    return [c for c in closure_findings.CLOSURES if c[0] in SPECS]


def validate() -> list:
    """Return a list of problems; empty means the classification is TOTAL."""
    problems = []
    if len(CLASS_KEYS) != len(set(CLASS_KEYS)):
        problems.append("duplicate class keys")

    # R15-1's OWN LESSON, applied here: "total" is recursive. A key set that
    # matches the ledger proves nothing if an entry is malformed, so the SHAPE
    # of every class row and every classification is checked before anything
    # unpacks one. Without this the loop below raises a ValueError instead of
    # reporting a problem, and a crash in a `--check` gate is not a verdict.
    for i, row in enumerate(CLASSES):
        if type(row) is not tuple or len(row) != 4 or not all(
                type(x) is str and x.strip() for x in row):
            problems.append(f"class row {i} is not (key, title, rule, "
                            f"mechanized) of non-empty strings: {row!r}")
    for k, v in MECHANISM.items():
        if not (type(k) is tuple and len(k) == 3 and type(k[0]) is str
                and type(k[1]) is int and type(k[2]) is str):
            problems.append(f"classification key {k!r} is not "
                            f"(spec: str, round: int, finding: str)")
        if not (type(v) is tuple and len(v) == 2
                and all(type(x) is str for x in v)):
            problems.append(f"{k!r} is classified as {v!r}, which is not "
                            f"(class: str, why: str)")
    if problems:
        return problems

    ledger = {(c[0], c[2], c[3]): c[1] for c in _ledger()}
    unclassified = sorted(set(ledger) - set(MECHANISM))
    phantom = sorted(set(MECHANISM) - set(ledger))
    for k in unclassified:
        problems.append(f"{k[0]} r{k[1]} {k[2]}: in the closure ledger, NOT "
                        f"classified — the count would silently under-report it")
    for k in phantom:
        problems.append(f"{k[0]} r{k[1]} {k[2]}: classified but matches no "
                        f"closure row (renamed, or the row was removed)")

    for k, (cls, why) in sorted(MECHANISM.items()):
        if cls not in CLASS_KEYS:
            problems.append(f"{k}: undeclared class {cls!r}")
        if not (why or "").strip():
            problems.append(f"{k}: classified with no reason")

    used = {cls for cls, _ in MECHANISM.values()}
    for k in CLASS_KEYS:
        if k not in used:
            problems.append(f"class {k!r} is declared with NO finding — a class "
                            f"nothing lands in is a claim, not an observation")
    return problems


def rows():
    """Per class: (key, title, external count, internal count, rounds)."""
    ledger = {(c[0], c[2], c[3]): c[1] for c in _ledger()}
    out = []
    for key, title, _rule, _mech in CLASSES:
        ext = sorted(k for k, (c, _) in MECHANISM.items()
                     if c == key and ledger.get(k) == "external")
        internal = sorted(k for k, (c, _) in MECHANISM.items()
                          if c == key and ledger.get(k) == "internal")
        out.append((key, title, ext, internal))
    return out


def render() -> str:
    ledger = {(c[0], c[2], c[3]): c[1] for c in _ledger()}
    n_ext = sum(1 for v in ledger.values() if v == "external")
    n_int = sum(1 for v in ledger.values() if v == "internal")
    ext_rounds = sorted({k[1] for k in ledger if ledger[k] == "external"})

    # No denominator is asserted here. Writing one surfaced a gap in the source
    # itself: round 2 was DISPATCHED and returned, and no verdict row for these
    # two specs was ever recorded — a clean round and an unrecorded round look
    # identical in `reviews.py`, which is R8-1's admission hole one level up.
    # The gap is DERIVED below rather than described, so it disappears from the
    # document if it is ever filled, and reappears if it happens again.
    sys.path.insert(0, str(HERE))
    import reviews
    ours = [r for r in reviews.REVIEWS
            if r["kind"] == "external" and r["spec"] in SPECS]
    verdicted = {r["round"] for r in ours if "raised" in r}
    dispatched = {r["round"] for r in ours if r["verdict"].startswith("SENT")}
    # the newest dispatch is legitimately awaiting its verdict, not a gap
    in_flight = {max(dispatched)} if dispatched and (
        not verdicted or max(dispatched) > max(verdicted)) else set()
    unrecorded = sorted(dispatched - verdicted - in_flight)

    lines = [
        f"**{n_ext} external findings, raised across {len(ext_rounds)} rounds, "
        f"and {n_int} found internally — every one classified below, exactly "
        f"once.** Counts are DERIVED from `MECHANISM` in "
        f"`specs/review_lessons.py`, which is checked total against the closure "
        f"ledger: a finding that is not classified fails the build, and so does "
        f"a class with nothing in it. Nothing in this section is a hand-kept "
        f"number — R15-2 was exactly that.",
        "",
        "| # | class | external | self-found | rounds it was raised in | recurred |",
        "|---|---|---|---|---|---|",
    ]
    for i, (key, title, ext, internal) in enumerate(rows(), 1):
        rnds = sorted({k[1] for k in ext})
        recurred = "**yes**" if len(rnds) > 1 else ("—" if not rnds else "no")
        rlist = ", ".join(str(r) for r in rnds) if rnds else "—"
        lines.append(f"| {i} | **{key}** — {title} | {len(ext)} | "
                     f"{len(internal)} | {rlist} | {recurred} |")

    recurring = [k for k, _t, e, _i in rows() if len({x[1] for x in e}) > 1]
    lines += [
        "",
        f"**{len(recurring)} of {len(CLASSES)} classes recurred** — they were "
        f"raised in more than one round, which means the first instance was "
        f"fixed and the mechanism shipped again in another costume: "
        f"{', '.join('`%s`' % r for r in recurring)}. That is the finding this "
        f"document exists for. It is derived from the rounds column, not "
        f"asserted.",
    ]
    lonely = [k for k, _t, e, i in rows() if not e and i]
    if lonely:
        names = ", ".join("`%s`" % k for k in lonely)
        one = len(lonely) == 1
        lines += [
            "",
            f"**{names} {'was' if one else 'were'} never raised by the "
            f"reviewer** — {'it is the class' if one else 'they are the classes'} "
            f"I found myself, while fixing something else. The previous "
            f"hand-written version of this table attributed external finding "
            f"ids to `self-reference`, which is how a document about second "
            f"copies acquired one.",
        ]
    if unrecorded:
        lines += [
            "",
            f"**Gap in the source, derived not described:** round"
            f"{'' if len(unrecorded) == 1 else 's'} "
            f"{', '.join(str(r) for r in unrecorded)} "
            f"{'was' if len(unrecorded) == 1 else 'were'} DISPATCHED and "
            f"returned, and `specs/reviews.py` holds no verdict row for these "
            f"specs — so a round that came back clean is indistinguishable "
            f"from a round nobody recorded. The report is not in the repo (the "
            f"reviewer asked that prior reports stay out of the package), so "
            f"the row is not reconstructed here rather than guessed at. This "
            f"sentence disappears when the gap is filled.",
        ]
    return "\n".join(lines)


def main(argv) -> int:
    problems = validate()
    if problems:
        print("review-lessons classification INVALID:\n  "
              + "\n  ".join(problems), file=sys.stderr)
        return 1

    block = f"{BEGIN}\n\n{render()}\n\n{END}"
    text = DOC.read_text()
    if BEGIN not in text or END not in text:
        print(f"{DOC} carries no generated block", file=sys.stderr)
        return 1
    head, rest = text.split(BEGIN, 1)
    _old, tail = rest.split(END, 1)
    new = head + block + tail

    if "--write" in argv:
        DOC.write_text(new)
        print(f"wrote {DOC}")
        return 0
    if new != text:
        print(f"{DOC} has DRIFTED from specs/review_lessons.py — regenerate "
              f"with `python3 specs/review_lessons.py --write`", file=sys.stderr)
        return 1
    print(f"review lessons: VALID ({len(MECHANISM)} findings classified, "
          f"{len(CLASSES)} classes, block in sync)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
