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
BEGIN = "<!-- GENERATED:lessons-summary -->"
END = "<!-- /GENERATED:lessons-summary -->"

# EXTERNAL ROUND 18, R18-2. The summary above the table used to be hand-written
# prose guarded by a pytest heuristic that hunted for cardinal words and digits.
# Two things were wrong with that. It lived only in the test file, so
# `--check` — the thing the ARCHIVE VERIFIER runs, and the only check a
# reviewer's extraction exercises — never saw it. And detecting quantities in
# natural language is a proxy for the property that matters: the scrubber
# dropped every four-digit number as though all of them were spec ids, so
# "has not moved in 9999 rounds" read as clean.
#
# A proxy for "this prose is what the generator says" is not needed when the
# generator can simply say it. The WHOLE summary — title, prologue, table and
# derived paragraphs — is generated from here and byte-verified, so any edit to
# any of it fails `--check`, in the tree and in the extraction alike.
PROLOGUE = """# What the external review of 0022 and 0023 actually found

Spec-Status: n/a — this is a process record, not a spec

**The design stopped moving early; the packaging did not.** Since the last
change to either specification, every finding has been in the EVIDENCE
MACHINERY — the checks, the carriers, and the way the package is built. That
is worth stating plainly, because the natural reading of a long series of
returned rounds is that the design is troubled. The generated table below
says when the last specification change was, and how many rounds have passed
since; this prose is no longer permitted to say it.

The findings are not a pile of unrelated defects. Classified by FAILURE
MECHANISM rather than by symptom, they collapse into a small number of classes
— and most of those classes were RE-FOUND after their first instance was
fixed. That is the actual problem: not that the reviewer keeps finding things,
but that I kept fixing the named cell and shipping.

**This document has been the defect it describes, repeatedly.** Its first
version was hand-written, with class counts that did not match the findings
they counted and a restated duration no carrier agreed with. Its replacement
generated the table and then left a free-text round count in this opening
summary — outside the block, ungated, and wrong; the reviewer flipped it to an
absurd value and every check still passed.

So: no quantity appears above the table, and a gate enforces that rather than
trusting me. Everything countable is generated from
`specs/review_lessons.py`, where every finding carries its own classification
and the whole set is checked TOTAL against the closure ledger — an
unclassified finding fails the build, so does a classification naming a
finding that does not exist, and so does a class with nothing in it.

---

## The classes"""
SPECS = ("0022", "0023", "0024", "0025")


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

# R17-2. `spec` means the finding required a change to a specification's
# NORMATIVE BODY — a § section, one of its generated blocks, or the
# reference implementation such a block is generated from. `packaging` is
# everything else: the checks, the carriers, the evidence machinery. The
# document's standing claim about the design not having moved is derived
# from this field and from nothing else.
SCOPES = ("spec", "packaging")

# (spec, round, finding) -> (class, why THIS mechanism and not a neighbouring
# one). A finding often exhibits two; the class recorded is the PRIMARY one —
# the mechanism that, if it had been absent, would have prevented the finding.
MECHANISM = {
    # ---- external ----------------------------------------------------------
    ("0022", 1, "F2"): ("proxy", "spec",
        "the host-supplied wall clock stood in for the order decisions were made in"),
    ("0022", 1, "F3"): ("self-assertion", "spec",
        "'supersession, never edit' was normative text true of no carrier that shipped"),
    ("0022", 1, "F4"): ("proxy", "spec",
        "`system_authored` stood in for the author-blindness the class claimed"),
    ("0023", 1, "F1"): ("domain", "spec",
        "quarantine reached one consumer of five — the rule's reach was not its domain"),
    ("0022", 3, "R3-1"): ("proxy", "spec",
        "`with conn:` was LABELLED BEGIN IMMEDIATE, and the harness was green on a "
        "different construction"),
    ("0022", 3, "R3-2"): ("domain", "spec",
        "the lint pattern matched one phrasing of the withdrawn rule, so the other "
        "phrasing stayed normative"),
    ("0022", 3, "R3-4"): ("second-copy", "packaging",
        "a round count beside the rows it counts, disagreeing with them"),
    ("0022", 3, "R3-5"): ("domain", "packaging",
        "the completeness gate's regex could not see four unconditional skips; the "
        "14-vs-6 mismatch was the symptom"),
    ("0023", 3, "F4"): ("domain", "spec",
        "N15 swept for the OLD CONDITION, so a consumer that never had one was "
        "outside the sweep's reach — form, not fact"),
    ("0023", 3, "R3-3"): ("domain", "spec",
        "the mirror case: the lifecycle predicate was applied too WIDELY and dropped "
        "episodes in a store with zero revocations"),
    ("0022", 4, "R4-1"): ("self-assertion", "spec",
        "the construction was NAMED atomic-and-shared while appending the row and "
        "never applying the effects — the name was the only evidence"),
    ("0022", 4, "R4-3"): ("second-copy", "packaging",
        "the hand-maintained ledger drifted from its own rows for a third round"),
    ("0022", 4, "R4-4"): ("domain", "packaging",
        "`render()`'s hard-coded category list silently dropped a whole category"),
    ("0023", 4, "R4-2"): ("second-copy", "spec",
        "the section header contradicted a row of the table beneath it"),
    ("0022", 5, "R5-1"): ("domain", "spec",
        "the failure outcomes were not total: a failing rollback and every "
        "IntegrityError fell outside the enumerated cases"),
    ("0022", 5, "R5-2"): ("proxy", "packaging",
        "the BUSY test measured SQLite's internal wait — a stand-in for the branch "
        "it was named after"),
    ("0022", 5, "R5-3"): ("proxy", "packaging",
        "a per-ROUND row stood in for the per-FINDING row PROCESS §4a requires"),
    ("0022", 5, "R5-4"): ("proxy", "packaging",
        "pytest's emitted reason was matched against source-site tokens — two "
        "representations compared as if one were the other"),
    ("0022", 6, "R6-1"): ("domain", "spec",
        "the rollback boundary caught Exception while the operation caught "
        "BaseException, leaving part of its own domain uncovered"),
    ("0022", 6, "R6-2"): ("second-copy", "spec",
        "a withdrawn sentence survived beside the generated block that replaced it"),
    ("0022", 6, "R6-3"): ("second-copy", "packaging",
        "the closure ledger was a hand-maintained twin of the generated one"),
    ("0023", 6, "R6-3"): ("second-copy", "packaging",
        "the same twin, on 0023's ledger"),
    ("0022", 6, "R6-4"): ("self-assertion", "packaging",
        "the launcher invented its own qualification rule and certified against it, "
        "while runtime_supported() said False"),
    ("0022", 7, "R7-1"): ("proxy", "packaging",
        "set-equality of ids stood in for per-finding validation, so a wrong round, "
        "an erased evidence string and a duplicate all passed"),
    ("0022", 7, "R7-2"): ("second-copy", "packaging",
        "the reproduction carrier restated the previous round's launcher result"),
    ("0022", 8, "R8-1"): ("coercion", "packaging",
        "`.get(..., [])` made an OMITTED field indistinguishable from a declared "
        "absence — a default that fabricated the fact"),
    ("0022", 8, "R8-2"): ("self-assertion", "packaging",
        "four package claims were hand-maintained beside the executables that "
        "contradicted them"),
    ("0022", 9, "R9-1"): ("self-assertion", "packaging",
        "both carriers claimed an extracted-archive rerun that did not happen"),
    ("0022", 10, "R10-1"): ("second-copy", "packaging",
        "the reviewer guide's workflow contradicted COLLECTED for ten rounds"),
    ("0022", 10, "R10-2"): ("proxy", "packaging",
        "the extraction registry bound LABELS, so swapping a command for "
        "`python -c pass` was invisible"),
    ("0022", 10, "R10-3"): ("env-leak", "packaging",
        "the sealing user's uid/gid rode into the archive, so a plain `tar -xzf` "
        "exited 2 for the recipient"),
    ("0022", 11, "R11-1"): ("proxy", "packaging",
        "the binding was textual containment of two names, satisfiable by a "
        "program that does nothing"),
    ("0022", 11, "R11-2"): ("env-leak", "packaging",
        "sealing inherited the whole environment, so a recursion marker turned the "
        "evidence runner into a skip"),
    ("0022", 12, "R12-1"): ("self-assertion", "packaging",
        "the evidence claim had no source read: deleting the transcript entirely "
        "still produced a passing archive"),
    ("0022", 12, "R12-2"): ("self-assertion", "packaging",
        "`ran` was trusted rather than derived, so a zero-record transcript "
        "claiming 40 satisfied every check"),
    ("0022", 13, "R13-1"): ("coercion", "packaging",
        "`exit: false` passed `!= 0` because bool subclasses int; a 64-character "
        "non-hex string passed a length check"),
    ("0022", 13, "R13-2"): ("second-copy", "packaging",
        "'the SAME six checks' over seven, in the sentence explaining that the list "
        "must not be maintained twice"),
    ("0022", 13, "R13-3"): ("second-copy", "packaging",
        "a selector naming a test that had been replaced — a stale copy of a name "
        "that lives in the test file"),
    ("0022", 14, "R14-1"): ("coercion", "packaging",
        "`ran: 45.0` == 45, a 64-digit integer digest through `str()`, a duplicate "
        "vanishing into a set"),
    ("0022", 15, "R15-1"): ("domain", "packaging",
        "closedness was established for command objects and not for the object "
        "holding them — the property's own domain is every level with keys"),
    ("0022", 15, "R15-2"): ("second-copy", "packaging",
        "hand-written class counts beside the findings they count, and a restated "
        "duration beside three carriers that measure it"),

    # ---- internal / self-found --------------------------------------------
    ("0022", 1, "M1"): ("domain", "spec",
        "'the sweep is pure and can be re-run' quantified over one moment; its "
        "domain is every moment, and the inputs mutate"),
    ("0022", 1, "M4"): ("disclosure", "spec",
        "complete=False is the expected steady state on a consolidation-bearing "
        "store and operators had not been told"),
    ("0022", 1, "S1"): ("domain", "spec",
        "the sweep's record domain was unenumerated — 'records' silently meant "
        "edges, and episode text renders into recall"),
    ("0023", 1, "M2"): ("domain", "spec",
        "the one §4 seam with no executed command turned out to have no verb at "
        "all — an unexercised cell of the domain"),
    ("0023", 1, "M3"): ("domain", "spec",
        "the supersession-refusal path was covered by neither rule of the split"),
    ("0023", 1, "S1"): ("domain", "spec",
        "0022's unenumerated record domain, inherited through the mutual "
        "Spec-Requires"),
    ("0023", 1, "S2"): ("self-assertion", "spec",
        "the lift asymmetry's justification asserted the inputs were not decidable "
        "from the record; they are all ON the record"),
    ("0023", 2, "S3"): ("domain", "spec",
        "quarantine-at-birth wrote a field no reader consulted — enforcement that "
        "reached none of its domain"),
    ("0022", 20, "R20-1"): ("proxy", "packaging",
        "occurrence ANYWHERE in the carrier stood in for the field's value, so "
        "`specs: none` on the line a reviewer reads passed while the correct "
        "block sat lower down"),
    ("0022", 19, "R19-1"): ("proxy", "packaging",
        "the fields I chose to extract — spec id and revision — stood in for the "
        "carrier, so a renamed PATH passed every identity check"),
    ("0022", 19, "R19-2"): ("domain", "packaging",
        "the check's domain was the region BETWEEN the markers; the document is "
        "larger than that, and a prepended title retitled it"),
    ("0022", 18, "R18-1"): ("domain", "packaging",
        "a record called structured was untotal three ways at once — an "
        "unchecked second copy in prose, duplicate carriers collapsing through "
        "dict() (R14-1's mechanism, in a check written after it), and a lower "
        "bound mistaken for a domain"),
    ("0022", 18, "R18-2"): ("proxy", "packaging",
        "hunting cardinal words stood in for `this prose is what the generator "
        "says` — and the check lived only in the test file, never in the "
        "command the archive verifier runs"),
    ("0022", 17, "R17-1"): ("domain", "packaging",
        "the round-16 fix enumerated the three identity carriers the reviewer "
        "NAMED; the carrier domain had five, and the two it missed were the "
        "per-spec candidate revisions"),
    ("0022", 17, "R17-2"): ("second-copy", "packaging",
        "a derivable count restated in prose OUTSIDE the generated block — the "
        "table was guarded and the sentence above it was not"),
    ("0022", 16, "R16-1"): ("self-assertion", "packaging",
        "the package's identity was typed into a template instead of produced "
        "from the version the seal was asked for — R8-2's shape, in the first "
        "line a reviewer reads"),
    ("0022", 16, "R16-2"): ("second-copy", "packaging",
        "a second, weaker implementation of a marker-block verifier that already "
        "existed here — and the copy carried the bug the original was written to "
        "fix. An implementation is a second copy of a RULE"),
    ("0022", 21, "R21-1"): ("self-reference", "packaging",
        "a test MUTATED the shipped document that another check reads, which "
        "only concurrency could expose — the mirror of R15-3, where a test read "
        "what another test wrote"),
    ("0022", 15, "R15-3"): ("self-reference", "packaging",
        "a test read the live transcript another test writes, and pytest-randomly "
        "shuffles order — so CI failed on some seeds from round 12 onward"),
    ("0022", 14, "R14-2"): ("self-reference", "packaging",
        "R7-1's evidence selected the evidence RUNNER, whose nested child skips on "
        "the recursion marker, so half the command exercised nothing and exited 0"),
    # ---- the L-pair, external round 1 --------------------------------------
    ("0024", 1, "F1"): ("domain", "spec",
        "the independence declaration was never checked against the rewrite's "
        "actual dependency domain — the fallback member lives in 0025's registry"),
    ("0024", 1, "F2"): ("proxy", "spec",
        "'denotes the user themself' stood in for a computation, over a domain "
        "the shipped str() conversion actually defines"),
    ("0024", 1, "F3"): ("second-copy", "spec",
        "the invariant list existed in three carriers and two drifted — "
        "including a hand-typed count in the package header"),
    ("0024", 1, "F4"): ("self-assertion", "spec",
        "§8 asserted provenance accuracy in general while the rule corrects "
        "one measured cell, prospectively"),
    ("0025", 1, "F1"): ("domain", "spec",
        "'orthogonal to trust' was not checked against the registry cell that "
        "breaks it — a host dict omitting the quarantine relation"),
    ("0025", 1, "F2"): ("self-assertion", "spec",
        "'the shipped retry path' named a construction that existed nowhere — "
        "no call count, matching, episode or malformed rule"),
    ("0025", 1, "F3"): ("domain", "spec",
        "three boundary properties were stated with no order over the "
        "construction domain, and two of them contradict when injection runs first"),
    ("0025", 1, "F4"): ("second-copy", "spec",
        "the §3 matrix retyped DEFAULT_RELATIONS from memory and drifted from "
        "the shipped functional flag"),
    ("0025", 1, "F5"): ("second-copy", "spec",
        "two in-spec carriers of the count contract disagreed (one key vs "
        "three) and the caller surfaces were nowhere"),
    ("0025", 1, "F6"): ("proxy", "spec",
        "note prose stood in for a typed carrier of the original relation — "
        "spoofable and mechanically unrecoverable"),
    # ---- the L-pair, external round 2 --------------------------------------
    ("0024", 2, "R2-1"): ("domain", "spec",
        "two round-1 fixes each proven in isolation were never composed over "
        "the shared pipeline — the contradiction lived between the specs"),
    ("0024", 2, "R2-2"): ("self-assertion", "spec",
        "§8 restated an aspiration the construction does not prove — the "
        "recurrence of round 1's F4, one door over"),
    ("0024", 2, "R2-3"): ("second-copy", "spec",
        "§3b's 'no new surface' and U5's test name both drifted from what "
        "round 1's own fixes had made true"),
    ("0025", 2, "R2-1"): ("domain", "spec",
        "the shadow rule was never run against the shipped default registry — "
        "the motivating adversary was checked, the ordinary input was not"),
    ("0025", 2, "R2-2"): ("domain", "spec",
        "the matching rule was total over the demo vectors, not over "
        "duplicates, reserved answers, no-provider and exception cells"),
    ("0025", 2, "R2-3"): ("domain", "spec",
        "the typed-field fix enumerated spec carriers but not SERIALIZATION "
        "carriers — bytes, digests, exports were all consumers"),
    ("0025", 2, "R2-4"): ("second-copy", "spec",
        "the same matrix cell was corrected in one spec and left in the twin"),
    ("0025", 2, "R2-5"): ("second-copy", "spec",
        "§3b contradicted §4c inside one spec, and counter ownership was "
        "stated twice across the pair"),
    # ---- the L-pair, external round 3 --------------------------------------
    ("0024", 3, "R3-1"): ("domain", "spec",
        "the pipeline was composed over the pair but not over the ACCEPTED "
        "stack — 0023's floor was not in the composition domain"),
    ("0024", 3, "R3-2"): ("second-copy", "spec",
        "the shared field acquired a definition per spec, and two carriers "
        "still described shapes earlier rounds had replaced"),
    ("0025", 3, "R3-1"): ("domain", "spec",
        "the snapshot froze the fields the FIX read, not the fields its "
        "consumers read — the prompt renderer was a consumer"),
    ("0025", 3, "R3-2"): ("second-copy", "spec",
        "counter inventories again — the third round running; the authority "
        "table itself omitted a counter another spec deferred to it"),
    ("0025", 3, "R3-3"): ("domain", "spec",
        "the fix's own injection made the catch-all prompt-visible — the "
        "new state opened the evasion it was measuring"),
    ("0025", 3, "R3-4"): ("domain", "spec",
        "the digest bump was verified against the writer, never against the "
        "stored-receipt reader on the failure path it exists for"),
    # ---- the L-pair, external round 4 --------------------------------------
    ("0024", 4, "R4-1"): ("second-copy", "spec",
        "the matrix restated the pipeline minus its newest dimension — a "
        "copy that did not move when the pipeline did"),
    ("0024", 4, "PAIR-R4-1"): ("second-copy", "spec",
        "published numbers and regenerable numbers were two copies of one "
        "measurement, and only one could be executed"),
    ("0025", 4, "R4-1"): ("self-assertion", "spec",
        "the canonical gloss was AUTHORED from memory instead of read from "
        "the product, and the vector was lossy in exactly the field that "
        "would have caught it"),
    ("0025", 4, "R4-2"): ("domain", "spec",
        "'rendered as today' was never executed against today — sorted() "
        "was an unexamined default over an order-bearing surface"),
    ("0025", 4, "R4-3"): ("second-copy", "spec",
        "the count appeared in prose twice more than in its inventory — "
        "fourth round of the same class"),
    ("0025", 4, "R4-4"): ("domain", "spec",
        "the rule was stated over the happy rows only — no cell for "
        "malformed, unknown, migration, or the durable field itself"),
    ("0025", 4, "PAIR-R4-1"): ("second-copy", "spec",
        "a number whose construction never shipped was carried as if "
        "regenerable — the claim outlived its evidence"),
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
        if not (type(v) is tuple and len(v) == 3
                and all(type(x) is str for x in v)):
            problems.append(f"{k!r} is classified as {v!r}, which is not "
                            f"(class: str, scope: str, why: str)")
        elif v[1] not in SCOPES:
            # R17-2: the document claimed the design "has not moved in eight
            # rounds" as free text, and it was wrong (nine) and ungated. The
            # claim is now DERIVED from this field, so the field must be
            # declared per finding and never defaulted — a default would
            # silently file an unclassified finding as packaging and make the
            # claim stronger than the evidence.
            problems.append(f"{k!r} declares scope {v[1]!r}; expected one of "
                            f"{sorted(SCOPES)}")
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

    for k, (cls, _scope, why) in sorted(MECHANISM.items()):
        if cls not in CLASS_KEYS:
            problems.append(f"{k}: undeclared class {cls!r}")
        if not (why or "").strip():
            problems.append(f"{k}: classified with no reason")

    used = {v[0] for v in MECHANISM.values()}
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
        ext = sorted(k for k, v in MECHANISM.items()
                     if v[0] == key and ledger.get(k) == "external")
        internal = sorted(k for k, v in MECHANISM.items()
                          if v[0] == key and ledger.get(k) == "internal")
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
        PROLOGUE,
        "",
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

    # R17-2: THE CLAIM THE PROSE USED TO MAKE BY HAND. "the design has not
    # moved in eight rounds" was free text, ungated and wrong — it was nine,
    # and the reviewer edited it to "999 rounds" with every check still
    # passing. It is derived here, from the per-finding scope, and the prose
    # above the table now carries no quantity at all.
    spec_rounds = sorted({k[1] for k, v in MECHANISM.items()
                          if v[1] == "spec" and ledger.get(k) == "external"})
    if spec_rounds:
        last_spec = max(spec_rounds)
        since = sorted(r for r in verdicted if r > last_spec)
        lines += [
            "",
            f"**The last finding that required a change to either "
            f"specification was raised in round {last_spec}.** The "
            f"{len(since)} rounds that returned a verdict since "
            f"({since[0]}–{since[-1]}) raised packaging and process findings "
            f"only — {sum(1 for k, v in MECHANISM.items() if v[1] == 'spec')} "
            f"of the {len(MECHANISM)} findings here are spec-scoped, and every "
            f"one of them is at or before round {last_spec}. Derived from the "
            f"`scope` field on each classification; nothing in this paragraph "
            f"is typed."
            if since else
            f"**The last finding that required a change to either "
            f"specification was raised in round {last_spec}**, which is the "
            f"most recent round to return a verdict.",
        ]

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

    # R16-2: this used to be `text.split(BEGIN, 1)` — the FIRST marker pair,
    # with nothing requiring there be only one. The reviewer appended a second
    # block claiming 999 findings and `--check`, the pytest gate and the whole
    # archive verifier all passed. The strict rule already existed in this repo
    # (skip_inventory.verify_collected, written for 0014's identical finding);
    # this was a second, weaker copy of it. Now there is ONE implementation and
    # both carriers call it — including on the WRITE path, so a duplicated
    # block cannot be papered over by regenerating.
    sys.path.insert(0, str(HERE))
    import generated_block as gb
    expected = f"\n{render()}\n"
    text = DOC.read_text()

    if "--write" in argv:
        try:
            DOC.write_text(gb.replace(text, BEGIN, END, expected,
                                      at_start=True))
        except gb.BlockError as e:
            print(f"{DOC}: {e}", file=sys.stderr)
            return 1
        print(f"wrote {DOC}")
        return 0
    try:
        gb.verify(text, BEGIN, END, expected, at_start=True)
    except gb.BlockError as e:
        print(f"{DOC} has DRIFTED from specs/review_lessons.py ({e}) — "
              f"regenerate with `python3 specs/review_lessons.py --write`",
              file=sys.stderr)
        return 1
    print(f"review lessons: VALID ({len(MECHANISM)} findings classified, "
          f"{len(CLASSES)} classes, block in sync)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
