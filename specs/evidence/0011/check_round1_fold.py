#!/usr/bin/env python3
"""0011 — the round-1 fold, checked STRUCTURALLY rather than by substring.

P4 refuses closure evidence that greps for a diagnostic string, because a
no-op artifact containing that string satisfies it. These four findings are
folds into spec TEXT (the spec is a draft; there is no behaviour yet), so
the evidence checks the SHAPE the fold had to take — a table's row count, a
branch's totality, the ABSENCE of the contradictory phrasing that was the
defect — not that a sentence appears somewhere.

Run:  $PY specs/evidence/0011/check_round1_fold.py
"""
from __future__ import annotations

import pathlib
import re
import sys

SPEC = (pathlib.Path(__file__).resolve().parents[3]
        / "specs" / "0011-subject-scoped-entitlement.md")


def _strip_comments(code: str) -> str:
    return "\n".join(l for l in code.splitlines()
                      if not l.lstrip().startswith("#"))


def _dependency_closure(spec: str, block: str) -> str:
    """Every fenced definition the policy block reaches, transitively.

    CARRIER-R3-1: a check on the policy block's own text is satisfied by
    moving the read one indirection away — `sourced(e)` defined in another
    fence, called from the policy. So the closure follows the calls: collect
    every `name(...) :=` definition in every fence, then expand from the
    policy block until nothing new is pulled in. Comments are stripped, so
    prose ABOUT a read is not mistaken for one.
    """
    fences = re.findall(r"```\n(.*?)```", spec, re.S)
    defs = {}
    for f in fences:
        for m in re.finditer(r"^(\w+)\s*\([^)]*\)\s*:?=", f, re.M):
            start = m.start()
            nxt = re.search(r"^\w+\s*\([^)]*\)\s*:?=", f[m.end():], re.M)
            end = m.end() + (nxt.start() if nxt else len(f) - m.end())
            defs[m.group(1)] = f[start:end]
    seen, frontier, out = set(), [_strip_comments(block)], []
    while frontier:
        body = frontier.pop()
        out.append(body)
        for name in set(re.findall(r"\b(\w+)\s*\(", body)):
            if name in defs and name not in seen:
                seen.add(name)
                frontier.append(_strip_comments(defs[name]))
    return "\n".join(out)


def check_r1_1(t: str) -> list:
    """The policy function must be TOTAL and must include the sourced term
    v4 omitted — the omission was the finding, not the wording."""
    bad = []
    # the fenced block opens at the predicate definitions, not at `policy`
    block = next((b for b in re.findall(r"```\n(.*?)```", t, re.S)
                  if "policy(incoming, prior)" in b), None)
    if block is None:
        return ["R1-1: no policy function block"]
    # NOTE: `sourced(prior)` was round 1's answer and round 2 REMOVED it —
    # 0006 forbids source_id from granting, so the rule must not read it.
    # A checker that still demanded the term would pin the defect in place,
    # which is what this line did until R2-1 was folded.
    for term in ("REFUSE", "ALLOW",
                 "self_assertion(incoming)", "subject_class(prior) == OTHER"):
        if term not in block:
            bad.append(f"R1-1: the policy block omits {term!r}")
    if "otherwise" not in block:
        bad.append("R1-1: the policy block has no catch-all — a policy "
                   "function that is not total is v4's defect again")
    # the predicates must be DEFINED, not merely used
    if not re.search(r"self_assertion\(e\)\s*:=", t):
        bad.append("R1-1: self_assertion is used but never defined")
    # R2-1: the decision must READ NO source_id. Checked on the block, not
    # on the prose about it — prose can claim anything.
    # R3-1/CARRIER-R3-1: check the predicate's TRANSITIVE DEPENDENCIES, not
    # the policy block's literal text. The reviewer defeated the syntactic
    # version by moving the source read behind a helper defined in a
    # SEPARATE FENCE — every check still passed. A rule is what it calls.
    if "source_id" in _dependency_closure(t, block):
        bad.append("R2-1: the decision READS `source_id`, directly or "
                   "through a helper it calls. 0006 says it may GROUP, "
                   "never GRANT — omission would strip protection and a "
                   "caller-supplied value would buy it")
    # whitespace-tolerant: the quotation is line-wrapped in the spec, and a
    # literal match would fail on a reflow that changes nothing
    if not re.search(r"may GROUP,\s+never\s+GRANT", t):
        bad.append("R2-1: 0006's constraint is not quoted as the reason")
    if "decision unchanged" not in t:
        bad.append("R2-1: no source-identity invariance matrix — the claim "
                   "that the rule ignores source_id is untested")
    # the rider must have the counter that makes it measurable. NOT
    # `would_refuse_broad`, which R2-2 deleted as constant-true — this
    # check required it, so the checker was pinning a vacuous field in
    # place. The load-bearing artifact is the allowed-but-broad-refusing
    # counter, which is the only one that can vary.
    # R3-2: the rider is DEFERRED. 0015 defers refusal counters to a consent
    # discussion this spec cannot hold, so v1 ships with the constituency
    # unmeasured and says so. This check previously REQUIRED the counter —
    # the third time a guard here pinned in place the very thing the next
    # round removed, which is why it now asserts the deferral and its reason
    # rather than a mechanism.
    if "THE RIDER IS DEFERRED" not in t:
        bad.append("R3-2: the rider is neither deferred nor built — it may "
                   "not assume 0015's deferred consent surface")
    if "UNMEASURED, and says so" not in t:
        bad.append("R3-2: the deferral does not state that v1 ships with "
                   "the broad rule's constituency unmeasured")
    return bad


def check_r1_2(t: str) -> list:
    """The authentication claim must be GONE from every carrier that made
    it — the finding was a claim in three places, not one sentence."""
    bad = []
    if re.search(r"needs an unforgeable authorisation", t):
        bad.append("R1-2: the E5 requirement row still asserts an "
                   "unforgeable authorisation")
    if not re.search(r"INTEGRITY BINDING", t):
        bad.append("R1-2: the binding is not restated as integrity")
    if not re.search(r"PROTECTED HOST API", t):
        bad.append("R1-2: correct() is not stated as a protected host API")
    # the host's obligations must be a TABLE, not a sentence
    if not re.search(r"\| the host must \|", t):
        bad.append("R1-2: no host-obligation table")
    return bad


def check_r1_4(t: str) -> list:
    """ONE outcome for malformed input, and absence kept distinct."""
    bad = []
    if re.search(r"fails CLOSED to the `derived\(THIRD_PARTY\)`\s*\n?floor",
                 t):
        bad.append("R1-4: the contradictory flooring sentence is back")
    if "RAISES and NOTHING IS WRITTEN" not in t:
        bad.append("R1-4: the single outcome is not stated")
    if "ABSENCE IS A DIFFERENT INPUT" not in t:
        bad.append("R1-4: absence is not distinguished from malformed")
    raises = len(re.findall(r"\|\s*\*\*RAISES\*\*", t))
    if raises < 4:
        bad.append(f"R1-4: the grammar table names {raises} RAISES cells; "
                   f"the enumerated invalid inputs were 4")
    return bad


def check_r1_5(t: str) -> list:
    """Total AND exclusive: a numbered first-match table ending in a
    catch-all, carrying the two labels v4 had no cell for."""
    bad = []
    m = re.search(r"\| # \| condition \| label \|\n\|[-| ]+\|\n((?:\|.*\n)+)", t)
    if not m:
        return ["R1-5: no precedence table"]
    rows = [r for r in m.group(1).strip().splitlines() if r.startswith("|")]
    if len(rows) != 5:
        bad.append(f"R1-5: the precedence table has {len(rows)} rows, not 5")
    if "otherwise" not in rows[-1]:
        bad.append("R1-5: the last row is not a catch-all, so the labels "
                   "are not total — which was the finding")
    for label in ("QUARANTINED_CLAIM", "CONTESTED_CURRENT"):
        if not any(label in r for r in rows):
            bad.append(f"R1-5: {label} is missing — v4 had no cell for it, "
                       f"which is why an edge could match zero labels")
    if "FIRST MATCH WINS" not in t:
        bad.append("R1-5: first-match is not stated, so exclusivity is "
                   "not established")
    return bad


# CARRIER-R2-1: each assertion is bound to its NAMED ROW. v5's checker
# searched narrow phrases across the whole file, so withdrawing a claim in
# §4e while §3a still asserted it PASSED — seven contradictory authoritative
# statements survived a green check. A row-scoped check cannot be satisfied
# by a withdrawal written somewhere else.
#
# (anchor that locates the row, substring that must NOT appear in it, why)
ROW_CONTRADICTIONS = (
    ("| the caller's `actor` on `correct()` |", "UNFORGEABLE",
     "§3a's adversarial row claims an unforgeable authorisation; §4e "
     "withdrew that claim (R1-2)"),
    # S6 is checked DATA-TO-DATA below, not by phrase — see check_s6_count.
    # A forbidden-substring check missed it entirely: the row says "one of
    # the three", never "three labels", so the guard looked for wording the
    # spec had never used. That is CARRIER-R2-1's own failure repeated
    # inside the fix for CARRIER-R2-1.
    ("| **S7**", "no rule here reads",
     "S7 denies reading disclosure; §4f's partition reads `quarantined` "
     "and `use_only` to place a label"),
    ("| **E-Q1** |", "0.016%",
     "E-Q1 still states the RETIRED figure as authoritative "
     "(PACKAGE-R1-1)"),
    ("| USER (with other authority", "confirmation, a higher rung",
     "§3c grants confirmation a rung; 0008 grants it none (R1-1)"),
    ("| existing `correct()` callers |", "can no longer forge",
     "§5 claims callers can no longer forge; they can still name a "
     "principal they are not (R1-2)"),
)


_NUMBER = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
           "six": 6, "seven": 7}


def check_s6_count(t: str) -> list:
    """S6 states HOW MANY labels the partition has; §4f IS the partition.
    Compare the two rather than searching for a phrase — the count is data
    on both sides, so no wording can hide a disagreement."""
    m = re.search(r"\| # \| condition \| label \|\n\|[-| ]+\|\n((?:\|.*\n)+)", t)
    if not m:
        return ["S6: no precedence table to count"]
    actual = len([r for r in m.group(1).strip().splitlines()
                  if r.startswith("|")])
    i = t.find("| **S6**")
    if i < 0:
        return ["S6: the invariant row is gone"]
    row = t[i:t.index("\n", i)]
    # the row carries the count as a TOKEN. Parsing an English number out of
    # prose read "exactly ONE of the five" as a claim of one — the number
    # that matters has to be unambiguous, so the carrier states it as data.
    m2 = re.search(r"`labels=(\d+)`", row)
    if not m2:
        return ["S6: the row carries no `labels=N` token, so its claim "
                "cannot be compared with §4f's table"]
    claimed = int(m2.group(1))
    if claimed != actual:
        return [f"S6 claims {claimed} labels; §4f's precedence table has "
                f"{actual}"]
    return []


def check_carriers(t: str) -> list:
    bad = []
    for anchor, forbidden, why in ROW_CONTRADICTIONS:
        i = t.find(anchor)
        if i < 0:
            bad.append(f"CARRIER: the row anchored at {anchor!r} is GONE — "
                       f"a renamed row silently drops its own check")
            continue
        row = t[i:t.index("\n", i)]
        if forbidden in row:
            bad.append(f"CARRIER: {why} — the row still says "
                       f"{forbidden!r}")
    return bad


def check_decision_table(t: str) -> list:
    """§4b's decision table must BE the matrix's output.

    A table transcribed by hand drifts from the function it describes, and
    the drift is invisible for exactly as long as nobody re-runs the
    generator. So the rows are compared to `policy_matrix.render()` —
    data against data, no phrase to miss.
    """
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    try:
        import policy_matrix
    except Exception as exc:                       # noqa: BLE001
        return [f"policy_matrix is not importable ({exc}) — §4b's table "
                f"has no generator to be checked against"]
    rows = [l for l in policy_matrix.render().splitlines()
            if l.startswith("| `")]
    missing = [r for r in rows if r not in t]
    if missing:
        return [f"§4b's decision table is STALE against policy_matrix: "
                f"{len(missing)} of {len(rows)} generated rows absent, "
                f"first is {missing[0]!r}"]
    if policy_matrix.problems():
        return ["policy_matrix itself FAILS — the table the spec carries is "
                "generated from a matrix that does not hold"]
    return []


def main() -> int:
    t = SPEC.read_text()
    bad = (check_r1_1(t) + check_r1_2(t) + check_r1_4(t) + check_r1_5(t)
           + check_carriers(t) + check_s6_count(t)
           + check_decision_table(t))
    if bad:
        print("0011 round-1 fold INCOMPLETE:\n  " + "\n  ".join(bad),
              file=sys.stderr)
        return 1
    print("0011 round-1 fold: R1-1, R1-2, R1-4 and R1-5 hold structurally "
          "(policy totality, claim withdrawal in every carrier, one outcome "
          "for malformed input, a 5-row first-match precedence table)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
