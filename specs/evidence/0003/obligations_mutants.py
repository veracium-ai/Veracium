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
- N1-K-counts-members (K counted over the members, not the distinct values) is a ROW (SR2-03, shipped-changes round
  2). The round-2 package declared it equivalent by construction, on the premise that the commitment tier holds one
  member per object; that premise is FALSE. A repeated value whose edges carry DISTINCT NOTES survives
  `collapse_for_render` (it keeps carrier distinctions), and the tier admits every dated member: the reviewer's case
  (A 'initial', then B 'new' and A 'restated') reaches the tier as three members over two values. The forged inputs
  behind the declaration (a prior A and one episode naming [B, A]; research's five stage-2 forms) never varied the note.
  Both distinct-note cells kill it by assertion, the one-slot path ("or 2 more") and the ordinary path ("…, … or 1
  more"). test_n1_k_counts_values_when_one_episode_repeats_a_value stays, as a regression that does not reach it.
  Two neighbours were stated equivalent beside it; the reason given ("follow from it") is WITHDRAWN, and each was
  re-measured with a reach check (research's stage 1 for round 3, research 1d543e05):
  - the clamped-item signal without `first != values[0]` (A5) is a ROW: the distinct-note pattern with B beyond the
    window puts one value over two members in the tier (K 0), and the one-slot fallback cuts that value, under the
    object width, so only `first != values[0]` reports the clamp (SR2-03-A5-clamp-signal-drops-first);
  - the n-slot `first` taken unclamped (A7) is EQUIVALENT by an identity: on that path `first` is clamped at
    max(16, _cap - 48), `_obj`'s own width, so `first != values[0]` holds exactly when `_obj(m) != m.object` fires for
    that member. The mutant that breaks the identity, R2S-2-display-width (A6), is a killed row: its control.
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
SB = "src/veracium/speaker_backstop.py"
S = "src/veracium/schema.py"
I = "src/veracium/ingest.py"   # noqa: E741
T = "tests/test_0003_obligations.py"
SUBJECT = "obligations"
DIGESTED = (G, M, X, D, P, SB, S, I, T, "specs/evidence/mutation_protocol.py", _protocol.KINDS, SELF)

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
B1_OBJ = C("test_b1_a_contested_line_keeps_each_members_object")
B1_DEADLINE = C("test_b1_a_contested_deadline_keeps_its_time_and_place")
N1_FLOOR = C("test_n1_a_long_group_at_the_floor_budget_keeps_its_nearest_dates_and_its_framing")
N1_OVERSIZED = C("test_n1_a_group_of_oversized_objects_is_held_to_the_item_cap")
N1_K = C("test_n1_k_counts_the_distinct_values_not_shown_not_the_members")
SR1_FOLD = C("test_sr1_01_two_distinct_values_that_clamp_alike_are_one_shown_and_one_more")
SR1_MIX = C("test_sr1_01_a_collision_beside_a_plain_value_keeps_the_plain_value_and_counts_the_collision")
SR1_REVIEWER = C("test_sr1_01_the_reviewers_regression")
R2S2_NEAREST = C("test_r2s_2_the_one_slot_path_shows_the_nearest_value_and_counts_the_other")
R2S2_SR1 = C("test_r2s_2_sr1_01_on_the_one_slot_path")
SR2_03_SLOT = C("test_sr2_03_a_repeated_value_with_a_distinct_note_is_one_value_on_the_one_slot_path")
SR2_03_ORD = C("test_sr2_03_a_repeated_value_with_a_distinct_note_is_one_value_on_the_ordinary_path")
SR2_03_A5 = C("test_sr2_03_a_one_value_unit_clamped_on_the_one_slot_path_is_reported_clamped")
NEW1 = C("test_new1_a_plain_commitment_line_is_held_to_the_item_cap")
NEW1_MARK = C("test_new1_a_marked_lone_member_is_held_to_the_item_cap_with_its_mark")
N2 = C("test_n2_a_clamped_group_is_one_clamped_item")
N2_CONTROL = C("test_n2_a_group_beside_a_clamped_plain_commitment_is_two_clamped_items")
N3_ORDER = C("test_n3_a_group_sorts_at_its_nearest_due_date")
N3_TIE = C("test_n3_groups_tied_on_their_nearest_date_sort_newest_observation_first")
B1_ROW = lambda row, form: C(                                                         # noqa: E731
    f"test_b1_the_backstop_judges_an_obligations_date_by_grounding_per_side[{row}-{form}]")
B1_E2E = lambda row: C(f"test_b1_an_assistant_only_date_under_a_named_obligation_is_not_volunteered[{row}]")  # noqa: E731
B1_USER = C("test_b1_a_user_stated_date_under_a_named_obligation_is_volunteered")
B1_OTHER_PARTY = C("test_b1_another_partys_deadline_keeps_the_every_side_rule")
B1_ENTITY = C("test_b1_a_non_obligation_triple_keeps_both_its_sides_judged")
B2_GENERIC = lambda form: C(f"test_b2_a_generic_query_reaches_a_commitment_in_either_form[{form}]")    # noqa: E731
B2_ASOF = lambda form: C(f"test_b2_an_as_of_recall_reaches_a_commitment_in_either_form[{form}]")      # noqa: E731
B2_ENTITY = lambda i: C(f"test_b2_an_entity_edge_still_needs_a_token_match[{i}]")                    # noqa: E731
B2_RANK = C("test_b2_an_obligation_ranks_as_a_subject_user_fact_does")
IS_OB = lambda i: C(f"test_is_obligation_over_its_domain[{i}]")                      # noqa: E731
XCHK = lambda i: C(f"test_is_obligation_and_subject_class_name_one_user[{i}]")       # noqa: E731
UN, NA = "subject-user", "subject-named"

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
    ("B1-slots-are-dates-only", "product", X,
     [("        values = list(dict.fromkeys(m.object for m in order))\n",
       "        values = list(dict.fromkeys(str(min(_dates_in(m.object + \" \" + m.note))) for m in order))\n")],
     [B1_OBJ, B1_DEADLINE], [OB3], None, "a contested line names only each member's date, dropping its object "
                                        "(research's stage-2 B1)"),
    ("S1-4-subject-dropped", "product", X,
     [('    return "" if e.subject == "user" else f"{e.subject} — "\n', '    return ""\n')],
     [NAMES], [USER_SAME], None, "the plain line drops a non-user subject (the obligation's name)"),
    ("S1-4a-subject-clamp-uncounted", "product", X,
     [("                if s_out != s or o != e.object:\n", "                if o != e.object:\n")],
     [CLAMP], [NAMES], None, "an oversized subject clamped without the I10a signal"),
    ("S1-4b-withheld-subject-rendered", "product", X,
     [("    _edges = [e for e in _edges if not snap.withheld(e)]\n", "")],
     [WITHHELD_NAME, OB9], [NAMES], None, "a withheld commitment's subject rendered (0047 withholding skipped)"),
    # ---- the N1–N4 batch (research's stage 2 on 6d10dc6, 4910a8b9; stage 1 on ea88c72, d3d22dd5) ----------------
    ("N1-first-item-tail-clamp", "product", X,
     [("                            line = (_contested_line if isinstance(unit, _ContestedCommitment) else _commit_line)(\n",
       "                            line = ((lambda u, c: _ci(line, c)) if isinstance(unit, _ContestedCommitment) else _commit_line)(\n")],
     [N1_FLOOR], [N1_OVERSIZED], None, "the superseded first-item path: a group line tail-clamped at the remaining "
                                       "budget, cutting a date and its framing (N1)"),
    ("N1-farthest-slots-kept", "product", X,
     [("            for v in values[:n]:\n",
       "            for v in values[len(values) - n:]:\n")],
     [N1_FLOOR], [OB3], None, "the elided form keeps the FARTHEST dates, not the nearest (research's stage 1)"),
    # ---- shipped-changes round 1, SR1-01 (the superseded implementation is the mutant; research's stage 1, Q1) -------
    ("SR1-01-dedup-after-clamp", "product", X,
     [("        values = list(dict.fromkeys(m.object for m in order))\n",
       "        values = list(dict.fromkeys(_obj(m) for m in order))\n")],
     [SR1_FOLD, SR1_MIX, SR1_REVIEWER, N1_K], [OB3], None, "distinct values decided AFTER the clamp, so two different "
                                                            "values that shorten alike are one and K loses one (SR1-01)"),
    ("SR1-01-collision-shown-twice", "product", X,
     [("                if s not in out:\n                    out.append(s)\n", "                out.append(s)\n")],
     [SR1_FOLD, SR1_MIX], [OB3], None, "a value whose clamped display repeats a shown one is shown again (\"X or X\"), "
                                      "not folded into K (research's stage 1, Q1)"),
    # ---- research's stage 2 on 974a6122 (R2S-2): the one-slot fallback, and two siblings of the n-slot form ----------
    ("R2S-2-one-slot-k-counts-displays", "product", X,
     [("            k = len(values) - 1\n", "            k = len(_shown(len(values))) - 1\n")],
     [R2S2_SR1], [OB3], None, "the one-slot fallback counts K over clamped displays: SR1-01 on the other path (A4)"),
    ("R2S-2-one-slot-shows-farthest", "product", X,
     [("                first = _clamp(values[0], content)\n", "                first = _clamp(values[-1], content)\n")],
     [R2S2_NEAREST], [OB3], None, "the one-slot fallback shows the FARTHEST value, not the nearest (A8)"),
    ("R2S-2-one-slot-k-zero", "product", X,
     [("            k = len(values) - 1\n", "            k = 0\n")],
     [R2S2_NEAREST, R2S2_SR1], [OB3], None, "the one-slot fallback names no other value (A10)"),
    ("R2S-2-k-counts-slots", "product", X,
     [("            cand = head + _body(shown, len(values) - len(shown)) + tail\n",
       "            cand = head + _body(shown, len(values) - n) + tail\n"),
      ("                line, k, first = cand, len(values) - len(shown), shown[0]\n",
       "                line, k, first = cand, len(values) - n, shown[0]\n")],
     [SR1_FOLD, SR1_MIX], [OB3], None, "K counts the values not reached, not those not shown: a folded collision is "
                                      "counted nowhere (A3)"),
    ("R2S-2-display-width", "product", X,
     [("                s = _clamp(v, max(16, _cap - 48))\n", "                s = _clamp(v, max(16, _cap - 40))\n")],
     [SR1_FOLD, SR1_MIX], [OB3], None, "the display clamped wider than an object's composition width (A6)"),
    # ---- shipped-changes round 2, SR2-03: the member count, declared equivalent in round 2, reached by distinct notes --
    ("N1-K-counts-members", "product", X,
     [("            cand = head + _body(shown, len(values) - len(shown)) + tail\n",
       "            cand = head + _body(shown, len(ms) - len(shown)) + tail\n"),
      ("                line, k, first = cand, len(values) - len(shown), shown[0]\n",
       "                line, k, first = cand, len(ms) - len(shown), shown[0]\n"),
      ("            k = len(values) - 1\n", "            k = len(ms) - 1\n")],
     [SR2_03_SLOT, SR2_03_ORD], [OB3], None, "K counted over the MEMBERS, not the distinct values: a repeated value "
                                            "with a distinct note is counted twice, on both paths (SR2-03, the "
                                            "reviewer's three-site mutant)"),
    ("SR2-03-A5-clamp-signal-drops-first", "product", X,
     [("        if label != subject or k or first != values[0] or any(_obj(m) != m.object for m in ms):\n",
       "        if label != subject or k or any(_obj(m) != m.object for m in ms):\n")],
     [SR2_03_A5], [OB3], None, "a one-value unit cut on the one-slot path is not counted clamped: the value is under "
                               "the object width, so only first != values[0] signals the cut (A5, research's reach "
                               "measurement for round 3)"),
    ("NEW1-object-cap-ignores-the-line", "product", X,
     [("        content = min(max(16, _cap - 48), line_cap - _est0(head) - _est0(tail))\n",
       "        content = max(16, _cap - 48)\n"),
      ("            if _est0(line) <= line_cap:\n                if s_out != s or o != e.object:\n",
       "            if True:\n                if s_out != s or o != e.object:\n")],
     [NEW1, NEW1_MARK], [CLAMP], None, "the superseded plain line: the object capped at item_cap−48 on top of the "
                                       "subject's own cap, the line unchecked (research's stage-1 NEW 1)"),
    ("NEW1-mark-outside-the-cap", "product", X,
     [("        head, tail = f\"{e.relation}: {s_out}\", _flag_of[e.id] + _marked.get(e.id, \"\")\n",
       "        head, tail = f\"{e.relation}: {s_out}\", _flag_of[e.id]\n"),
      ("                    _clamped_ids.add((\"edge\", e.id))\n                return line\n",
       "                    _clamped_ids.add((\"edge\", e.id))\n                return line + _marked.get(e.id, \"\")\n")],
     [NEW1_MARK], [OUTSIDE], None, "the lone member's mark appended after the line is held to the cap (NEW 1)"),
    ("N2-grouped-members-composed", "product", X,
     [("            _unit = _ContestedCommitment(_ms)\n",
       "            for _m in _ms:\n                _commit_line(_m, _cap)\n            _unit = _ContestedCommitment(_ms)\n")],
     [N2, N2_CONTROL], [OB3], None, "the superseded count: each grouped member's discarded line still registers "
                                    "its clamps (N2, R-impl4-4)"),
    ("R3-group-order-latest", "product", X,
     [("            return (min(ds) if ds else today,\n                    -max(m.provenance",
       "            return (max(ds) if ds else today,\n                    -max(m.provenance")],
     [N3_ORDER], [OB3], None, "a group sorts at its LATEST due date (research's stage-2 R3)"),
    ("R4-group-tie-reversed", "product", X,
     [("                    -max(m.provenance.observed_at.timestamp() for m in e.edges)",
       "                    max(m.provenance.observed_at.timestamp() for m in e.edges)")],
     [N3_TIE], [OB3], None, "groups tied on their nearest date sort OLDEST observation first (research's stage-2 R4)"),
    ("R5-group-clamp-uncounted", "product", X,
     [("        if label != subject or k or first != values[0] or any(_obj(m) != m.object for m in ms):\n"
       "            _clamped_ids.add((\"contested\", unit.id))",
       "        if False:\n            pass")],
     [N2, N1_OVERSIZED], [OB3], None, "a clamped or elided group line without the I10a signal (research's stage-2 R5)"),
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
    # the 0.29.0 release blockers B1+B2 (research's notes read on fc9cc15, 1eb722a9; the owner: "Hold; fix B1+B2
    # first (Recommended)"): the obligation form keeps the speaker backstop and the lexical eligibility 0.28.0's
    # subject-`user` form had
    ("B1-token-rule-kept", "product", SB,
     [("    if (relation == OBLIGATION_RELATION and session_date is not None\n",
       "    if (False and relation == OBLIGATION_RELATION and session_date is not None\n")],
     [B1_ROW("user-words-assistant-echoes-iso", UN), B1_ROW("assistant-only-iso", NA),
      B1_ROW("assistant-only-words", UN), B1_ROW("assistant-only-words", NA),
      B1_E2E("assistant-only-iso"), B1_E2E("assistant-only-words")],
     [B1_ROW("user-words-assistant-words", UN), B1_ROW("user-words-assistant-words", NA), B1_USER], None,
     "an obligation is judged by 0051's every-side token rule (the pre-fix backstop: B1)"),
    ("B1-whole-event-grounding", "product", SB,
     [("    return (grounding.ungrounded(obj, user_text, session_date)\n",
       "    return (grounding.ungrounded(obj, user_text + \"\\n\" + other_text, session_date)\n")],
     [B1_ROW("assistant-only-iso", UN), B1_ROW("assistant-only-iso", NA),
      B1_ROW("assistant-only-words", UN), B1_ROW("assistant-only-words", NA)],
     [B1_ROW("user-words-assistant-echoes-iso", UN), B1_USER], None,
     "the user side is grounded over the WHOLE event, so the assistant's words ground it"),
    ("B1-user-condition-alone", "product", SB,
     [("            and not grounding.ungrounded(obj, other_text, session_date))\n", ")\n")],
     [B1_ROW("in-no-turn", UN), B1_ROW("in-no-turn", NA)],
     [B1_ROW("assistant-only-words", NA), B1_USER], None,
     "a date no side grounds is restricted (the non-user condition dropped)"),
    ("B1-subject-user-form-excluded", "product", SB,
     [("            and (str(subject).strip().casefold() == \"user\" or is_obligation(subject, relation))):\n",
       "            and is_obligation(subject, relation)):\n")],
     [B1_ROW("user-words-assistant-echoes-iso", UN), B1_ROW("assistant-only-words", UN)],
     [B1_ROW("assistant-only-words", NA)], None, "only the named form is judged by its date; subject `user` keeps tokens"),
    ("B1-caller-drops-the-relation", "product", I,
     [("relation=relation, session_date=date))", "session_date=date))")],
     [B1_ROW("assistant-only-iso", NA), B1_ROW("assistant-only-words", NA), B1_ROW("assistant-only-words", UN)],
     [B1_ROW("user-words-assistant-words", NA)], None, "ingest calls the backstop without the relation"),
    ("B1-caller-drops-the-date", "product", I,
     [("relation=relation, session_date=date))", "relation=relation))")],
     [B1_ROW("assistant-only-iso", NA), B1_ROW("assistant-only-words", NA), B1_ROW("assistant-only-words", UN)],
     [B1_ROW("user-words-assistant-words", NA)], None, "ingest calls the backstop without the session date"),
    ("B2-scorer-drops-the-obligation", "product", G,
     [("        if e.subject == \"user\" or is_obligation(e.subject, e.relation):\n",
       "        if e.subject == \"user\":\n")],
     [B2_GENERIC(NA), B2_ASOF(NA), B2_RANK], [B2_GENERIC(UN), B2_ENTITY("entity")], None,
     "an obligation must match a query word to enter (B2, the pre-fix rule)"),
    ("B2-obligation-takes-the-entity-base", "product", G,
     [("        if e.subject == \"user\" or is_obligation(e.subject, e.relation):\n"
       "            base = 1 + 2 * overlap      # eligible always; ranked by relevance\n",
       "        if e.subject == \"user\":\n"
       "            base = 1 + 2 * overlap      # eligible always; ranked by relevance\n"
       "        elif is_obligation(e.subject, e.relation):\n"
       "            base = 3 * overlap\n")],
     [B2_GENERIC(NA), B2_ASOF(NA), B2_RANK], [B2_GENERIC(UN)], None, "an obligation is scored as an entity edge"),
    ("PRED-every-relation", "product", S,
     [("    return relation == OBLIGATION_RELATION and s != \"user\" and not _KIND_PREFIX.match(s)\n",
       "    return s != \"user\" and not _KIND_PREFIX.match(s)\n")],
     [IS_OB("located_at"), IS_OB("scope"), IS_OB("Deadline")], [B2_GENERIC(NA)], None,
     "any relation with a named subject is an obligation"),
    ("PRED-entity-ref-included", "product", S,
     [("    return relation == OBLIGATION_RELATION and s != \"user\" and not _KIND_PREFIX.match(s)\n",
       "    return relation == OBLIGATION_RELATION and s != \"user\"\n")],
     [IS_OB("person-ref"), IS_OB("org-ref"), IS_OB("Person-ref"), XCHK("person-ref"),
      B2_ENTITY("another-partys-deadline"), B1_OTHER_PARTY], [B2_GENERIC(NA), B1_ENTITY], None,
     "another party's deadline (person:alice) is read as the user's obligation (research 8b0de7d2)"),
    ("PRED-case-sensitive", "product", S,
     [("    s = str(subject).strip().casefold()\n", "    s = str(subject)\n")],
     [IS_OB("User"), IS_OB("padded-user"), IS_OB("Person-ref"), XCHK("User"), XCHK("padded-USER")],
     [IS_OB("named")], None, "\"User\" is read as an obligation, not as the user (0011 E1 disagrees)"),
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
    _noop(SB, "def speaker_restricts(", _cells_of(SB)),
    _noop(S, "def is_obligation(", _cells_of(S)),
    _noop(I, "        speaker_restricted = (user_effective", _cells_of(I)),
    ("CTRL-unrelated-TypeError", X,
     [("    if contested:\n        _tier =",
       '    raise TypeError("an unrelated execution failure (classifier negative control)")\n'
       "    if contested:\n        _tier =")],
     [OB3], "an UNRELATED TypeError in assemble: every cell fails for no reason a row names", "UNCLASSIFIED"),
]

SUBJECT_P = _protocol.Subject(
    spec="0003", finding=SUBJECT, table=TABLE, digested=DIGESTED, mutants=MUTANTS, controls=CONTROLS,
    import_modules=("veracium.graph", "veracium", "veracium.proactive", "veracium.doctor", "veracium.prompts",
                    "veracium.speaker_backstop", "veracium.schema", "veracium.ingest"),
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
