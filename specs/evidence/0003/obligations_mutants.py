#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0003_obligations_mutants.py::test_the_table_check_refuses_each_tampered_table
"""0003/obligations §6 (INV-OB2–OB6, OB8–OB10) and research's stage-1 conditions: every mutant demonstrated red.

The amendment (research's candidate v0.2, adopted 2026-11-01; the owner: "Ship, then review") is folded into 0003 and
0012 in the same batch; each row's id carries the invariant it demonstrates. Every mutant is a code edit run by the
shared protocol (specs/evidence/mutation_protocol.py) on a copy of the tracked tree, killed by assertion in ITS named
cells, with an HONEST probe that still passes under it. Beside them, per mutated file, a NO-OP control whose named
cells must all pass, and one classifier negative control.

Two of §6's named mutants are not code edits here, stated rather than dropped:
- INV-OB1's is "the subject-`user` extraction": the extractor's choice, not the product's; the defect's own cell
  (test_ob1_the_subject_user_form_is_the_defect_it_answers) is kept beside its inversion, and INV-OB7 measures the
  extractor's rate.
- INV-OB5's "a check that writes" is equivalent BY CONSTRUCTION: `doctor.diagnose` opens a snapshot copy in a
  temporary directory (`_open_snapshot`), so a write in any check lands in the copy; the cell's byte-identical
  assertion holds for that reason, and the counting mutants below are its killable half.
- INV-OB8 holds at TWO layers: the carrier passes only `_build_contested`'s EXPOSED ids (no query selection, so a
  fenced challenger is linkage), and `assemble` admits only assertable members. A one-file mutant of either layer
  survives by construction, and the protocol edits one file per mutant, so its kill is the DOUBLE mutant, run by
  hand at adoption (recorded in the commit), and the cell stays in the suite.

    $PY specs/evidence/0003/obligations_mutants.py --check     # fast: definitions, anchors, digests, every row good
    TMPDIR=/dev/shm $PY specs/evidence/0003/obligations_mutants.py --write
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import mutation_protocol as _protocol  # noqa: E402

TABLE = HERE / "obligations" / "mutation-table.json"     # the name tests/test_closure_mutants.py finds
SELF = "specs/evidence/0003/obligations_mutants.py"
G = "src/veracium/graph.py"
M = "src/veracium/__init__.py"
X = "src/veracium/proactive.py"
D = "src/veracium/doctor.py"
P = "src/veracium/prompts.py"
T = "tests/test_0003_obligations.py"
SUBJECT = "obligations"
DIGESTED = (G, M, X, D, P, T, "specs/evidence/mutation_protocol.py", _protocol.KINDS, SELF)

C = lambda name: f"{T}::{name}"                                                       # noqa: E731
OB2 = C("test_ob2_a_reschedule_is_contested_with_one_refusal_row")
OB3 = C("test_ob3_the_briefing_renders_a_contested_commitment_once")
OB10 = C("test_ob10_one_episode_naming_two_dates_renders_once_contested")
OUTSIDE = C("test_a_member_outside_the_window_never_appears_and_marks_its_partner")
UNMARKED = C("test_an_uncontested_commitment_carries_no_mark")
NAMES = C("test_a_plain_commitment_names_a_subject_other_than_user")
USER_SAME = C("test_a_subject_user_commitment_renders_byte_identical_to_before")
CLAMP = C("test_an_oversized_subject_is_clamped_and_counted")
OB4 = C("test_ob4_two_dated_values_with_no_refusal_row_render_as_two_plain_commitments")
OB8 = C("test_ob8_a_fenced_third_party_challenger_leaves_one_plain_line")
OB9 = C("test_ob9_a_challenged_member_is_withheld_before_the_group_is_counted")
WITHHELD_NAME = C("test_a_withheld_commitments_subject_is_never_rendered")
FLAGGED = C("test_a_lone_member_whose_partner_is_flagged_is_marked_contested")
OB5 = C("test_ob5_the_doctor_counts_the_subject_user_chain_exactly_and_writes_nothing")
OB6 = C("test_ob6_the_obligation_rule_reaches_the_extractor")
DIRECT = C("test_a_direct_assemble_with_no_contested_argument_renders_per_edge")

_SUBJECT_AXIS = '            elif (subject_class(edge.user_id, prior.subject) == "OTHER"\n'
_CARRIER = "            contested=[(g.subject, g.relation, [e.id for e in g.exposed]) for g in groups])"
_TIER = "            _ms = [_tier[i] for i in _ids if i in _tier and i not in _grouped]\n"
_REPLACE = "            commitments = [p for p in commitments if p[1].id not in _grouped] + _units\n"
_RULE = '- A dated obligation the user states (an appointment, a deadline, a due date,\n  a renewal, a scheduled event) is ONE triple whose SUBJECT is the obligation\n  itself ("dentist appointment", "Q3 report", "lease renewal"), relation\n  `deadline`, and whose object is the date as an ISO date (YYYY-MM-DD): a\n  weekday or "tomorrow" copied from the DATE CONTEXT calendar; a stated date\n  with no year ("November 12") is the next such date on or after the day the\n  event occurred, unless the event says which year. A date with no\n  stated day ("sometime in November", "next month"), or a relative date the\n  calendar does not hold ("in three weeks"), keeps the text\'s words: never\n  give it a day. Never use the subject `user` for an obligation: the user has\n  many. A third party\'s claim about the user\'s obligations is still a CLAIM\n  under the rule above.\n'

# (id, kind, file, [(anchor, replacement)], named cells, honest nodes, reason or None, what)
MUTANTS = [
    ("OB2-subject-axis-bypassed-for-deadline", "product", G,
     [(_SUBJECT_AXIS, '            elif (subject_class(edge.user_id, prior.subject) == "OTHER" '
                      'and edge.relation != "deadline"\n')],
     [OB2, OB3], [NAMES], None, "the subject axis skipped for `deadline`: a reschedule retires the old date (OB10's "
                               "one-episode case is still caught by 0003 §4c-iv's within-episode net, so it is not named)"),
    ("OB3-no-briefing-carrier", "product", M,
     [(_CARRIER, "            contested=None)")],
     [OB3, OB10, OUTSIDE, FLAGGED], [NAMES], None, "today's per-edge rendering: the briefing path builds no contested groups"),
    ("OB3-member-also-rendered-plain", "product", X,
     [(_REPLACE, "            commitments = commitments + _units\n")],
     [OB3, OB10], [NAMES], None, "a contested member rendered plain as well as in the group line"),
    ("OB4-any-two-distinct-values", "product", X,
     [("    if contested:\n        _tier =",
       "    contested = [(_k[0], _k[1], [e.id for e in _v]) for _k, _v in __import__('itertools').groupby(sorted("
       "[e for e in surfaced if e.assertable], key=lambda e: (e.subject, e.relation)), "
       "key=lambda e: (e.subject, e.relation))]\n    if contested:\n        _tier =")],
     [OB4], [OB3], None, "a second predicate: any two active values of one key are a contest"),
    ("OB9-group-built-before-withholding", "product", X,
     [(_TIER, "            _ms = [e for e in store.edges(user_id) if e.id in _ids and e.assertable and e.id not in _grouped]\n")],
     [OB9], [OB3], None, "the contested line built over the store's edges, before 0047's withholding"),
    ("I10d-out-of-window-member-named", "product", X,
     [(_TIER, "            _ms = [e for e in surfaced if e.id in _ids and e.assertable and not e.needs_confirmation "
              "and e.id not in _grouped and _dates_in(e.object + \" \" + e.note)]\n")],
     [OUTSIDE], [OB3], None, "an out-of-window member named in the contested line: new reach (0012 I10d)"),
    ("I10d-lone-member-unmarked", "product", X,
     [("            if len(_ms) == 1 and _outside:\n", "            if False:\n")],
     [OUTSIDE, FLAGGED], [OB3], None, "a lone tier member whose partner sits outside the tier renders as settled"),
    ("I10d-every-commitment-marked", "product", X,
     [("            if len(_ms) == 1 and _outside:\n", "            if len(_ms) == 1:\n")],
     [OB9, OB8], [OB3], None, "the mark on a lone member whose partner is withheld or fenced (content of a "
                               "challenged or fenced member's existence volunteered)"),
    ("S1-4-subject-dropped", "product", X,
     [('    return "" if e.subject == "user" else f"{e.subject} — "\n', '    return ""\n')],
     [NAMES], [USER_SAME], None, "the plain line drops a non-user subject (the obligation's name)"),
    ("S1-4a-subject-clamp-uncounted", "product", X,
     [("        if out != s:\n            _clamped_ids.add((\"edge\", e.id))\n        return out\n",
       "        return out\n")],
     [CLAMP], [NAMES], None, "an oversized subject clamped without the I10a signal"),
    ("S1-4b-withheld-subject-rendered", "product", X,
     [("    _edges = [e for e in _edges if not snap.withheld(e)]\n", "")],
     [WITHHELD_NAME, OB9], [NAMES], None, "a withheld commitment's subject rendered (0047 withholding skipped)"),
    ("OB5-non-user-subjects-counted", "product", D,
     [('        if (prior is not None and prior.get("subject") == "user" and d.get("subject") == "user"\n',
       "        if (prior is not None\n")],
     [OB5], [OB6], None, "the doctor count includes a non-user subject's chain"),
    ("OB5-every-relation-counted", "product", D,
     [('                and prior.get("relation") in OBLIGATION_RELATIONS and d.get("relation") == prior.get("relation")\n',
       '                and d.get("relation") == prior.get("relation")\n')],
     [OB5], [OB6], None, "the doctor count includes another relation's chain (located_at)"),
    ("OB6-rule-not-sent", "product", P,
     [(_RULE, ""), ("\ndef date_context(", '\nOBLIGATION_RULE = """- A dated obligation the user states ..."""\n\n\n'
                                          'def date_context(')],
     [OB6], [NAMES], None, "the extraction rule in a constant the extractor is never sent"),
]


def _noop(rel, anchor, cells):
    return (f"NOOP-{pathlib.Path(rel).stem}", rel, [(anchor, "# no-op control: a comment, no behaviour\n" + anchor)],
            sorted(set(cells)), f"a comment edit in {rel}: its mutants' cells must all pass", "SURVIVED")


def _cells_of(rel):
    return [c for m in MUTANTS if m[2] == rel for c in m[4]]


# (id, file, [(anchor, replacement)], named cells, what, the outcome the classifier must give)
CONTROLS = [
    _noop(G, "def subject_class(", _cells_of(G)),
    _noop(M, "    def _build_contested(", _cells_of(M)),
    _noop(X, "def _commitment_subject(", _cells_of(X)),
    _noop(D, "def _check_obligation_chains(", _cells_of(D)),
    _noop(P, "def date_context(", _cells_of(P)),
    ("CTRL-unrelated-TypeError", X,
     [("    if contested:\n        _tier =",
       '    raise TypeError("an unrelated execution failure (classifier negative control)")\n'
       "    if contested:\n        _tier =")],
     [OB3], "an UNRELATED TypeError in assemble: every cell fails for no reason a row names", "UNCLASSIFIED"),
]

SUBJECT_P = _protocol.Subject(
    spec="0003", finding=SUBJECT, table=TABLE, digested=DIGESTED, mutants=MUTANTS, controls=CONTROLS,
    import_modules=("veracium.graph", "veracium", "veracium.proactive", "veracium.doctor", "veracium.prompts"),
    import_specs=(), cells_files=(T,), kinds=("product",))

definition_sha = _protocol.definition_sha
canonical = _protocol.canonical
render = _protocol.render
_digests = SUBJECT_P.digests


def problems(path: pathlib.Path = TABLE, root: pathlib.Path = ROOT) -> list:
    return SUBJECT_P.problems(path, root)


def main() -> int:
    if "--check" in sys.argv or len(sys.argv) == 1:
        probs = problems()
        for b in probs:
            print(f"STALE: {b}")
        return 1 if probs else 0
    return SUBJECT_P.main(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
