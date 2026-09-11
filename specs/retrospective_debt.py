"""The RETROSPECTIVE DEBT of the security-hotfix carve-out — the half of the
deadline PROCESS says is machine-checked and is not.

WHY THIS EXISTS. PROCESS §"Carve-out — security hotfixes may ship first" says:

    "`Spec-Retrospective-Due` below is mandatory and machine-checked, because a
     deadline is what keeps this a carve-out rather than a door."

Half of that is true. `specs/check_spec_reference.py` verifies, at COMMIT TIME,
that a `security-hotfix` commit carries a `Spec-Retrospective-Due` trailer and
that it parses as `YYYY-MM-DD`. It runs before the deadline can possibly have
passed, and NOTHING EVER READS THE DATE AGAIN. So the mechanism named as what
keeps the carve-out from being a door enforces only that a door has a sign on
it. 0038's own retrospective proposed this check rather than building it
(§Retrospective, observation 1); this is that check.

MEASURED AT WRITING (2026-09-08), which is the argument for it:
    9 commits carry a `Spec-Retrospective-Due`
    1 spec carries a `## Retrospective` section discharging one
    7 dates are PAST with no discharge recorded anywhere in the tree
The oldest is `ea2e1ab` (0002, due 2026-08-07) — a month over, and the
generated status page says of 0002 "the retrospective was deferred in every
one". Whether those seven were discharged in SUBSTANCE elsewhere is exactly the
question a check forces into the open; today nothing asks it.

THE TWO CARRIERS AND WHY THE SHA IS THE KEY. The obligation lives in a COMMIT
TRAILER; the discharge lives in a SPEC. Binding them by DATE would let two
hotfixes sharing a date be discharged by one retrospective — four of the nine
share 2026-08-09. So a discharge must NAME THE SHA it discharges. 0038's
section names `d59592d` and its date; that is the shape.

DEFERRAL IS A DECISION, NOT A BYPASS. An owner may re-date an obligation —
`DEFERRED` carries the new date, the reason, and who authorised it. What an
owner may NOT do is let a date pass in silence, which is the state the tree is
in today. A deferral without a future date is refused: that is a door.

SUPERSESSION IS THE THIRD KIND, AND IT IS VERIFIED. An obligation whose code has
since been externally reviewed under a later ACCEPTED spec may be closed as
`SUPERSEDED` without a written retrospective — with the covering specs named,
the limit of the claim stated, a reason, and an authoriser. `problems()` checks
each named spec against the tree: absent or not `accepted`, the closure is
refused. Neither of the other two kinds was honest for the six: a `Discharges:`
line would claim a retrospective that was never written; a deferral would claim
one is still coming.

Run: `python3 specs/retrospective_debt.py [--json]` from anywhere — the repository
root is derived from this file's location, never from the current directory
(an ocr review of the v0.21.0 range, 2026-09-11, found `main()` defaulting to
`Path.cwd()`: run from `specs/` as this docstring then said, `specs/specs/` was
empty, every obligation was reported outstanding and every SUPERSEDED closure
refused — real-looking debt from a wrong root). Exit 1 if anything is
outstanding. Home: `specs/`, with a node in `tests/test_spec_gate.py`
so it runs on every CI run rather than once at commit time — a deadline checked
only at commit time is checked before it can be missed.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]          # the repository root: this file lives in specs/
SPECS_DIRNAME = "specs"

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

#: spec-or-sha -> the re-dated obligation. An owner decision, recorded.
#: Every entry needs a NEW date in the future of the original and a reason;
#: a deferral without one is a door, and `problems()` refuses it.
DEFERRED: dict[str, dict] = {
    "ea2e1ab": {
        "new_due": "2026-12-01",
        "reason": "0002 is Spec-Status: deferred; the invariant was approved in "
                  "every external round and the retrospective deferred in every "
                  "one. The obligation stands with the spec and is re-dated "
                  "with it, not closed — this is the one of the seven that is "
                  "genuinely still owed. The date is the one number in the "
                  "disposition that nothing derives: far enough out not to be "
                  "theatre, near enough to be real.",
        "authorized_by": "Quentin, 2026-09-08 (\"Let's land the gate in the way "
                         "you recommend\", relayed by research; ledger "
                         "[Quentin, research session])",
    },
}

#: Obligations closed WITHOUT a written retrospective, because the code they
#: touched was covered by the external review of a later ACCEPTED spec. Not a
#: bypass: `covered_by` must name specs that are actually `Spec-Status:
#: accepted` in this tree, and `problems()` VERIFIES that — a superseded
#: closure whose justification names a draft, a deferred spec, or a spec that
#: does not exist is refused, as is one missing its `reason`, `covered_by`,
#: `limit` or `authorized_by`. `limit` is REQUIRED because the claim has one and
#: it belongs in the record rather than in a message: `covered_by` shows the
#: AREA was externally reviewed, not that this specific defect was examined in
#: that round. The escape hatch is checked against the tree, like everything
#: else here. (Research's disposition, 2026-09-08, on Quentin's word "Let's
#: land the gate in the way you recommend"; his frame: "I'm not really
#: concerned with revising history unless you think not doing it would hurt us
#: now or moving forward" — the history does not hurt; the blockage does, because
#: the gate protects the NEXT hotfix.)
_SUPERSEDED_REASON = (
    "Shipped under the security-hotfix carve-out before the deadline was "
    "enforceable. The code it touched has since been through external review "
    "under the accepted specs named in `covered_by`; a written retrospective "
    "now would produce a document nobody reads for review that already "
    "happened.")
_SUPERSEDED_LIMIT = (
    "`covered_by` shows the AREA was externally reviewed under an accepted "
    "spec. It does NOT show that this specific defect was individually "
    "examined in that round. The closure is 'superseded in substance', not "
    "'reviewed line by line', and anyone relying on it should read it that "
    "way.")
_SUPERSEDED_AUTH = ("Quentin, 2026-09-08 (\"Let's land the gate in the way you "
                    "recommend\", relayed by research; ledger [Quentin, "
                    "research session])")
SUPERSEDED: dict[str, dict] = {
    # model-reachable self-elevation into SYSTEM (mcp_server.py)
    "362f474": {"covered_by": ["0031"], "reason": _SUPERSEDED_REASON,
                "limit": _SUPERSEDED_LIMIT, "authorized_by": _SUPERSEDED_AUTH},
    # two live 0.4.5 defects incl. the unrecoverable future-date case
    "533092c": {"covered_by": ["0003", "0014"], "reason": _SUPERSEDED_REASON,
                "limit": _SUPERSEDED_LIMIT, "authorized_by": _SUPERSEDED_AUTH},
    # malformed-date fallback writing an invented observation time
    "33b19fe": {"covered_by": ["0014"], "reason": _SUPERSEDED_REASON,
                "limit": _SUPERSEDED_LIMIT, "authorized_by": _SUPERSEDED_AUTH},
    # offset-bearing date bypassing the skew limit; consolidation
    "f7f1bff": {"covered_by": ["0010", "0014"], "reason": _SUPERSEDED_REASON,
                "limit": _SUPERSEDED_LIMIT, "authorized_by": _SUPERSEDED_AUTH},
    # consolidation writing internally false source_type
    "c83b31b": {"covered_by": ["0010", "0014"], "reason": _SUPERSEDED_REASON,
                "limit": _SUPERSEDED_LIMIT, "authorized_by": _SUPERSEDED_AUTH},
    # unparseable-extraction branch recording an unsupplied time
    "88d909c": {"covered_by": ["0014", "0031"], "reason": _SUPERSEDED_REASON,
                "limit": _SUPERSEDED_LIMIT, "authorized_by": _SUPERSEDED_AUTH},
}
# `b8a4489` (0.18.1, the designated compat release for 0031 Phase A rollback,
# on release/0.18 — never in main's history) was the one of nine left
# deliberately UNDISPOSED when this gate landed: due 2026-09-11, it shipped the
# day 0031 was accepted, so 0031's round could not have covered it. Its
# retrospective was WRITTEN into specs/0031 on 2026-09-08, three days early
# (`Discharges: b8a4489`) — the first obligation this mechanism named before
# its date rather than a month after. The section records the split judgement:
# the rule (punch-list I4) externally reviewed, the branch implementation not.

_SPEC_STATUS = re.compile(r"^Spec-Status:\s*(\S+)", re.M)


def spec_statuses(repo: Path) -> dict[str, str]:
    """DERIVED from the tree: spec number -> its `Spec-Status:` value."""
    out: dict[str, str] = {}
    for p in sorted((repo / SPECS_DIRNAME).glob("[0-9][0-9][0-9][0-9]-*.md")):
        m = _SPEC_STATUS.search(p.read_text(errors="ignore"))
        out[p.name[:4]] = m.group(1) if m else "(no Spec-Status line)"
    return out


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(("git", "-C", str(repo), *args),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def obligations(repo: Path) -> list[dict]:
    """DERIVED from history: every commit whose trailers declare the carve-out
    and a deadline. Not a list anyone maintains — the commits are the record."""
    # REFUSE a shallow repository before deriving anything. Measured by
    # research (2026-09-08): at depth 5 the derivation saw 0 of 9 obligations
    # and the vacuity guard fired — correct by luck; at depth 150 and 400 it
    # saw 1 of 9 and reported 1 problem, and once that one was disposed the
    # gate would go GREEN because the history was not there, not because the
    # debt was paid. A partial answer from a completeness check is worse than
    # none, because it looks like the whole one. CI's pytest jobs check out
    # with fetch-depth 0 today; this asserts it rather than relying on a
    # setting in another file that nobody editing it would connect to here.
    if _git(repo, "rev-parse", "--is-shallow-repository").strip() == "true":
        raise RuntimeError(
            "shallow repository: the obligation set is DERIVED from full "
            "history, and a shallow clone reports fewer obligations without "
            "reporting fewer problems. Refuse rather than under-report "
            "(CI must check out with fetch-depth 0).")
    out = []
    # `--all` IS LOAD-BEARING, not completeness for its own sake: a hotfix on
    # a RELEASE BRANCH never reaches main's history — b8a4489 (0.18.1, the
    # designated Phase A rollback target on release/0.18) is invisible to
    # every gate that runs on main, and this derivation named its obligation
    # ONLY because it walks every ref. Narrowing this to `git log` (HEAD) would
    # silently blind the gate to exactly the class of release that most needs
    # it; the rule-zero battery asserts an unreachable-branch hotfix is derived.
    # (Research, 2026-09-08, on the 0.18.1 retrospective.)
    # ONE git call over the whole history (the per-commit form took 5.5 s
    # over 1,266 commits; this runs in well under a second). A literal NUL
    # cannot travel in an argv string, so the field separator is a token git
    # will never emit inside these four fields, and the record separator is
    # a second one; both are asserted absent from every record they frame.
    SEP, REC = "@@|@@", "@@REC@@"
    fmt = (f"%H{SEP}%(trailers:key=Spec-Exception,valueonly){SEP}"
           f"%(trailers:key=Spec-Retrospective-Due,valueonly){SEP}%s{REC}")
    for record in _git(repo, "log", "--all", f"--format={fmt}").split(REC):
        if not record.strip():
            continue
        sha, exc, due, subject = record.split(SEP, 3)
        sha = sha.strip()
        if exc.strip() != "security-hotfix":
            continue
        due = due.strip()
        if not due:
            continue            # commit-time gate's job, not this one's
        out.append({"sha": sha[:7], "full_sha": sha, "due": due,
                    "subject": subject.strip().splitlines()[0][:100]})
    return sorted(out, key=lambda o: o["due"])


#: A discharge is DECLARED, not inferred from a mention.
_DISCHARGES = re.compile(r"^Discharges:\s*([0-9a-f]{7,40}(?:\s*,\s*[0-9a-f]{7,40})*)\s*$",
                         re.M)


def discharges(repo: Path) -> dict[str, list[str]]:
    """DERIVED from the specs: for each spec carrying a `## Retrospective`
    section, the shas that section EXPLICITLY DISCHARGES via a
    `Discharges: <sha>[, <sha>]` line inside it.

    THE SHA IS THE KEY because four of the nine obligations share a date, and a
    date-keyed discharge would let one retrospective close four hotfixes it
    never mentioned.

    THE DECLARATION IS REQUIRED because the first draft of this function took
    ANY sha the section mentioned, and 0038's section mentions three — its own
    hotfix plus two acceptance commits. Under that rule a retrospective that
    happened to cite `ea2e1ab` in passing would silently discharge 0002's
    obligation. An obligation must be closed on purpose, by a line that says
    so, and never by an incidental citation.
    """
    found: dict[str, list[str]] = {}
    for p in sorted((repo / SPECS_DIRNAME).glob("*.md")):
        text = p.read_text(errors="ignore")
        m = re.search(r"^## Retrospective.*?(?=^## |\Z)", text, re.M | re.S)
        if not m:
            continue
        named: set[str] = set()
        for line in _DISCHARGES.findall(m.group(0)):
            named |= {s.strip()[:7] for s in line.split(",")}
        if named:
            found[p.name] = sorted(named)
    return found


def problems(repo: Path, today: str | None = None) -> list[str]:
    """Outstanding obligations, refused deferrals, and the vacuity guard."""
    today = today or _dt.date.today().isoformat()
    obs = obligations(repo)
    out: list[str] = []

    # A check that finds nothing to check has not passed — it has not run.
    if not obs:
        return ["no `Spec-Retrospective-Due` obligation found in history at "
                "all: either the trailer changed name or this check is "
                "pointed at the wrong tree. A zero here is not a pass."]

    discharged: set[str] = set()
    for spec, shas in discharges(repo).items():
        discharged |= set(shas)

    for key, d in DEFERRED.items():
        if not _DATE.match(str(d.get("new_due", ""))):
            out.append(f"deferral for {key}: `new_due` must be YYYY-MM-DD — a "
                       f"deferral without a date is the door the deadline "
                       f"exists to prevent")
        if not str(d.get("reason", "")).strip():
            out.append(f"deferral for {key}: needs a reason")
        if not str(d.get("authorized_by", "")).strip():
            out.append(f"deferral for {key}: needs who authorised it")

    statuses = spec_statuses(repo)
    for key, s in SUPERSEDED.items():
        for field in ("reason", "covered_by", "limit", "authorized_by"):
            if not s.get(field):
                out.append(f"superseded closure for {key}: needs `{field}` — a "
                           f"closure without its {field} is a sweep, not a "
                           f"disposition")
        for spec in s.get("covered_by") or []:
            status = statuses.get(str(spec))
            if status is None:
                out.append(f"superseded closure for {key}: `covered_by` names "
                           f"spec {spec}, which does not exist in {SPECS_DIRNAME}/")
            elif status != "accepted":
                out.append(f"superseded closure for {key}: `covered_by` names "
                           f"spec {spec}, whose Spec-Status is {status!r}, not "
                           f"accepted — only an accepted spec's external review "
                           f"can stand in for a retrospective")

    for o in obs:
        if o["sha"] in discharged:
            continue
        if o["sha"] in SUPERSEDED:
            continue          # closed above, with its justification verified
        deferred = DEFERRED.get(o["sha"])
        effective_due = (deferred or {}).get("new_due", o["due"])
        if effective_due > today:
            continue                      # not yet due; nothing owed today
        via = (f" (deferred to {effective_due})" if deferred else "")
        out.append(
            f"{o['sha']} due {o['due']}{via} — no `## Retrospective` section "
            f"in any spec names it. {o['subject']!r}")
    return out


def main(argv: list[str]) -> int:
    repo = Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("-") \
        else REPO
    probs = problems(repo)
    if "--json" in argv:
        print(json.dumps({"obligations": obligations(repo),
                          "discharges": discharges(repo),
                          "problems": probs}, indent=1))
    else:
        for p in probs:
            print(f"  OUTSTANDING  {p}")
        obs = obligations(repo)
        print(f"  {len(probs)} problem(s); {len(obs)} obligation(s) in "
              f"history, {len(discharges(repo))} spec(s) recording a "
              f"discharge")
    return 1 if probs else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
