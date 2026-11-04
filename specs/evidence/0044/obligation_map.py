"""The PRODUCT obligation map, GENERATED (the round-4 verdicts: V44 L20 and L58–L62, the frozen rows; T12, build note
b2870871 D10 as replaced by addendum 1's M1, with P7 and P8).

Every frozen row of the seven documents is joined to the product test nodes bound to it AND to the classified kill,
by one of those nodes, of a mutant that ANSWERS the row — from ONE consolidated campaign re-run at T12's pin over the
union of every tranche's definitions (`campaign/defs.py`; its result `campaign/result.json`). A docstring citation
alone closes nothing. `specs/evidence/0044/obligations.py` stays the MODEL map; this is the implementation gate's.

  rows       parsed from each document's own table (the bold-id rows of its §6, the 0018 amendment's §4i.8, 0041's
             §11.6.8): 0044 INV-A1–A23; 0018 I13–I32 (its original §6 and the amendment's); the 0003 amendment
             INV-O1–O10; the 0008 amendment INV-Q1–Q10 with Q4′ and INV-I1–I7 and the two C-rows it amended, C8 and
             C11 (its gate names both: research's T12 P9); 0045 INV-G*; 0047 INV-R*; the 0041
             amendment INV-RR*. A row whose invariant cell begins "Withdrawn" is listed and owes nothing; its
             withdrawal text is quoted (WITHDRAWN, checked). The COMPLEMENT is checked too: every bold id row in the
             seven tables (the id grammar `INV-<X>n` / `<X>n`) is a row or a declared NON_ROW family, with its reason.
  binding    a test node is bound to a row when its docstring, or the SECTION BANNER it sits under (the nearest
             preceding `# ====`/`# ----` comment line, the tranche files' convention), cites the row's EXPLICIT id
             (`INV-A21`; for 0018, `I29` or `INV-I29` — 0008's INV-I rows stop at I7), or the row names the node
             (`test_…` in backticks) — through `specs/citation_debt.py`'s declared rename when the named node moved —
             or, naming no test, names its test FILE (`tests/test_….py`: every node in it — 0018's I19). A row whose subject is other rows (0018's
             I31, "0018's I13–I23 are unchanged") takes their nodes and their answering mutants (DERIVED, its quote
             checked). A bare native id binds outside its document's own modules only when qualified by the
             document ("0008 C11"). Bare ids (`R3`, `Q10`) and test names are not read: they are also research's finding labels
             and the build notes' question numbers.
  answering  a mutant answers a row when its NAME cites the row's id, or `campaign/defs.py`'s
             ANSWERS annotation says so. A GROUP label never answers: it names a tranche's theme or lists several
             rows (the rehearsal measured 82 findings with labels answering, 35 without) — a JUDGEMENT, so each entry carries the row's clause (quoted from the row,
             checked), and one line on why the mutation falsifies it; the mutant's site is GENERATED as file::symbol
             from its anchor. T12's own mutants cite the explicit id in their names instead. NOT_ANSWERS records the
             pairs judged NOT to answer (with the reason); they are excluded and listed.
  findings   an answering pair whose mutant is KILLED only by nodes NOT bound to the row is a FINDING (the map missed
             a binding, or the row's tests miss its mutant) and refuses until resolved: a reviewed BINDING_EDIT, a new
             bound cell, or a NOT_ANSWERS entry (research's T12 P10).
  retired    each retired mutant names its superseding commit and its INVERSE (the mutant that now carries the rule),
             which must read KILLED in the campaign — a retirement never silently loses coverage.
  the gate   a row is CLOSED iff some answering mutant is KILLED (mutation_kinds' rule) with a bound node among its
             failing cells. Each document's gate is quoted from its own text (GATES; a quote that no longer occurs
             refuses); for 0008 and the 0041 amendment, which state no split, every row is PRODUCT (research's P7).
  edits      BINDING_EDITS lists the citations T12 added to existing tests so that the binding reads them, each with
             the row it binds, that row's clause and the test line that asserts it — the citation must occur in its
             node's text, the clause in the row's, the line in that test function's own source, and the node must be
             bound to the row (all checked); the line's file:line is rendered, computed, and so is the CELL of the row
             the clause quotes (invariant, mutant, or check), for every binding edit and ANSWERS entry. A pair both
             in ANSWERS and NOT_ANSWERS refuses (research's T12 S2-P2). It is the reviewer's list of
             what T12 changed to bind, read as "does this line assert this clause".
  the defs   every result row carries the digest of the DEFINITION it ran (group, name, file, anchor, replacement);
             a row whose digest is absent or differs from campaign/defs.py refuses — a result is cited only for the
             mutant that produced it (a definition swapped after the run, as R-A round 2's recovery was, re-runs).
  the pin    the campaign's result records the digest of every file its cells and mutants read (src/veracium, tests/,
             each mutated file); a tree whose digest differs refuses — a kill is cited only at the pin it was made at.

    python obligation_map.py --write   regenerate obligation_map.json / .md
    python obligation_map.py --check   exit 1 if a fresh derivation differs, or any problem stands
"""
# Mutation-Matrix: tests/test_0044_t12_obligation_map.py::test_the_map_refuses_each_planted_defect
from __future__ import annotations

import ast
import functools
import hashlib
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
CAMPAIGN = HERE / "campaign"
OUT_JSON = HERE / "obligation_map.json"
OUT_MD = HERE / "obligation_map.md"

# (document, spec file, the explicit-id pattern of its frozen rows)
SPECS = (
    ("0044", "0044-relation-arity", r"INV-A\d+"),
    ("0018", "0018-release-migration-orchestrator", r"I(?:1[3-9]|2\d|3[0-2])"),
    ("0003", "0003-supersession-authority", r"INV-O\d+"),
    ("0008", "0008-staleness-clearing", r"INV-(?:Q\d+′?|I\d+)|C(?:8|11)"),
    ("0045", "0045-declarative-grounding", r"INV-G\d+"),
    ("0047", "0047-subject-reply", r"INV-R\d+"),
    ("0041", "0041-targeted-redaction", r"INV-RR\d+"),
)
# each document's gate, QUOTED from its own text (the quote must occur verbatim in the named file)
GATES = {
    "0044": ("0044-relation-arity", "At the implementation gate, every row is in addition a named PRODUCT test, "
                                    "demonstrated red against its mutant."),
    "0003": ("0044-relation-arity", "**The gate, stated the same way in 0044, the 0003 amendment and the 0018 "
                                    "amendment (R2-08):**"),
    "0018": ("0044-relation-arity", "**The gate, stated the same way in 0044, the 0003 amendment and the 0018 "
                                    "amendment (R2-08):**"),
    "0045": ("0045-declarative-grounding", "**PRODUCT tests** are named here and land at the implementation gate."),
    "0047": ("0047-subject-reply", "**PRODUCT tests** are named here and land at the implementation gate."),
    "0008": ("0008-staleness-clearing", "tests at the implementation gate, including C8's cross-verb concurrency and "
                                        "C11's new export test."),
    "0041": (None, "no MODEL/PRODUCT split is stated: every row is PRODUCT (research's T12 stage-1 P7)"),
}
# the bold-id rows the seven tables define that are NOT programme rows, by family: (document, id regex) -> (reason,
# and where the reason needs the document's own words, (spec file, the quote that must occur in it))
NON_ROWS = {
    ("0003", r"I\d+[a-z]?"): ("0003's own §6 (accepted before the programme); its programme rows are the amendment's "
                              "INV-O", None),
    ("0003", r"Q2a"): ("0003's recorded-trigger row (a watch item, not an invariant)", None),
    ("0008", r"C(?:[1-79]|10|12|2a)"): (
        "0008's own checks (the original confirm contract): the amendment folded into C8 and C11 only, and those two "
        "are rows", ("0008-staleness-clearing", "§6d's SQLite line and two retention rows, C8 and C11, the v6 invariants")),
    ("0041", r"INV-\d+"): ("0041's own INV-1–INV-12 (implementation accepted at round 14); its programme rows are the "
                           "amendment's INV-RR", None),
    ("0018", r"I(?:1[359]′|3[3-9])"): (
        "0018 v9's adjacent-rungs rows (§4j, amendment 0018-adjacent-rungs, design accepted at its round 3): not "
        "programme rows; their implementation acceptance is outstanding and the owner schedules it",
        ("0018-release-migration-orchestrator", "implementation acceptance outstanding — I33's populated fixtures")),
}
_ID = re.compile(r"(?:INV-[A-Z]*|[A-Z])\d+[a-z]?′?")
# a withdrawn row's withdrawal, quoted from its row
WITHDRAWN = {"0041 INV-RR13": "**Withdrawn; not a current invariant.**"}
# the citations T12 added to existing tests so that the binding reads them, each with the row it binds, that row's
# CLAUSE (quoted from the row, checked) and the line of the test that ASSERTS it (checked to occur in that test
# function's own source; its file:line is rendered, computed): research's T12 D10 ask — a binding edit is chosen
# after its test killed the mutant, so the reviewer reads 'does this line assert this clause'. The first 8 bind
# rows T12's cells exercise; the rest are the rehearsal's findings (B3, B5). (node, cited text, row, clause, line)
BINDING_EDITS = (
    ('tests/test_0044_t6_operation.py::test_only_the_three_declarations_count',
     'I25 / INV-A15', '0044 INV-A15',
     'the plan is fixed at its first write',
     'assert _run(p, registry=_reg(works_as="multi"), op_id="op-2", plan_only=True).outcome == "already-planned"'),
    ('tests/test_0044_t6_operation.py::test_three_header_states_and_an_empty_plan_is_recorded',
     "INV-A21's store clauses", '0044 INV-A21',
     'a later call is admitted or refused by digest',
     'assert _run(p, op_id="op-2").outcome == "registry-changed"'),
    ('tests/test_0044_t6_operation.py::test_two_concurrent_first_callers_produce_one_header',
     'INV-A21 / §4e admission', '0044 INV-A21',
     'two headers from concurrent first calls',
     'assert _q(p, "SELECT COUNT(*) FROM plan_header") == [(1,)]'),
    ('tests/test_0029_reinstatement_reason.py::test_reinstated_reason_is_closed_and_an_invalid_one_unwinds_the_write',
     "0044's INV-A18", '0044 INV-A18',
     "`reinstated`'s reason is closed (0029 v12)",
     'assert not e.active and e.invalidation_reason == "revoked_source", f"{name}: the row\'s reinstatement persisted"'),
    ('tests/test_0008_request_registry.py::test_a_backfilled_redacted_confirmation_is_terminal_not_a_replay',
     "0041's INV-RR7", '0041 INV-RR7',
     "the registry step backfills an already-redacted confirmation's registry row with the marker",
     'assert _rows(p, "SELECT request_digest FROM request_registry") == [(_redaction.MARKER,)]'),
    ('tests/test_0047_t10b_read.py::test_g8_the_marker_follows_the_flag_unchallenged_and_a_challenged_flagged_fact_is_withheld',
     "INV-G8: 0019's marker follows the FLAG on every grounding value", '0045 INV-G8',
     "0019's marker follows the FLAG on every grounding value",
     'assert ("[possible extraction error]" in r.context) == ungrounded'),
    ('tests/test_0047_t11b_portability.py::test_rr6_rr9_an_old_or_partial_notice_refuses_an_arriving_act',
     "INV-I5's coverage clause", '0008 INV-I5',
     'coverage is all or nothing per row',
     '_refused(_mem(tmp_path, "c.db"), part, "coverage is all or nothing|fabricated|untreated|shows", restore=True)'),
    ('tests/test_0044_t11a_portability.py::test_d3_an_undecided_sources_candidate_is_refused_into_an_uninitialized_store',
     "INV-A21's third clause", '0044 INV-A21',
     'a pre-arity import into an uninitialized store is refused, naming the plan-only mode',
     '_refuses(dst, f, match=r"plan_only=True")'),
    ('tests/test_0044_t7_undo.py::test_undo_restores_the_retirement_per_field_and_nothing_else',
     "INV-A13's per-field restore", '0044 INV-A13',
     'undo restores per field',
     'assert {k for k in before if before[k] != after[k]} == {"invalidated_at", "invalidation_reason"}'),
    ('tests/test_0044_t7_undo.py::test_one_id_space_with_confirm_in_both_directions',
     '0008am INV-Q1: one id space across confirm and undo', '0008 INV-Q1',
     'an id held by one verb or request is an integrity conflict for any other, in both orders',
     'assert "held by a \'confirm\' request" in str(_refuses(ValueError, _undo_raw, p, cid="held-by-confirm"))'),
    ('tests/test_0044_t12_registry_scenario.py::test_a_user_holding_all_three_verbs_is_erased_at_once_and_every_id_is_free_again',
     '0044 INV-A20', '0044 INV-A20',
     "user erasure removes the user's outcomes, runs, inventory and registry rows atomically",
     'assert T6._q(p, f"SELECT COUNT(*) FROM {table} WHERE user_id=?", (U,))[0][0] == 0, table'),
    ('tests/test_0044_t5_era.py::test_forget_user_erases_the_users_inventory_outcome_and_run_rows_and_no_one_elses',
     '(0044 INV-A20)', '0044 INV-A20',
     "user erasure removes the user's outcomes, runs, inventory and registry rows atomically",
     'assert {r[0] for r in s._conn.execute(f"SELECT user_id FROM {table}")} == {V}, table'),
    ('tests/test_0029_carrier.py::test_every_edge_writing_site_carries_an_event_ruling',
     "0044 INV-A22's product half", '0044 INV-A22',
     'by every writer',
     'assert rulings[name].get("lifetime") in ("choke-point", "erasure"), ('),
    ('tests/test_0044_t6_operation.py::test_a_users_transaction_is_atomic',
     "I32's cumulative status", '0018 I32',
     'the status read returns cumulative commits for the operation',
     'assert DM.data_migration_status(p, "op-2") == DM.DataMigrationStatus("known", False, tuple(sorted((U, V))))'),
    ('tests/test_0044_t5_era.py::test_a_re_retired_member_stays_a_member_but_its_retirement_no_longer_matches',
     "I30's pre-plan doctor phase", '0018 I30',
     'states the name-only predicate before a plan exists',
     'assert [sorted(f.ids) for f in found] == [["m-other", "p-old"]], found'),
    ('tests/test_0044_t6_operation.py::test_three_header_states_and_an_empty_plan_is_recorded',
     "I30's initialized-empty doctor phase", '0018 I30',
     '`doctor` warns in both phases (§4e)',
     'assert _dm_findings(p)[0][0] == "warn"'),
    ('tests/test_0008_request_registry.py::test_erasure_frees_the_ids_but_never_resets_the_counter',
     'INV-Q6, INV-Q9', '0008 INV-Q9',
     'positions come from a store-wide counter that is never reset',
     'assert _rows(p, "SELECT act_seq FROM confirmations") == [(2,)]'),
    ('tests/test_0047_t11b_portability.py::test_rr8_rule4_writes_a_covered_act_treated_even_where_its_notice_stays_pending',
     "INV-RR8 and 0008's INV-I4", '0041 INV-RR8',
     'written with BOTH `text` and `request_digest` treated',
     'assert x["request_digest"] == R.MARKER and (x["table"] == "confirmations" or x["text"] == R.MARKER)'),
    ('tests/test_0047_t11b_portability.py::test_rr8_rule4_writes_a_covered_act_treated_even_where_its_notice_stays_pending',
     "INV-RR8 and 0008's INV-I4", '0008 INV-I4',
     'written with BOTH content carriers treated',
     'assert x["request_digest"] == R.MARKER and (x["table"] == "confirmations" or x["text"] == R.MARKER)'),
    ('tests/test_0047_t10a_reply.py::test_io_ii_3_a_reply_under_a_pending_notice_is_admitted_and_its_confirmation_treats_it',
     "0008's INV-I5, its fourth mutant, and INV-I7's confirm_notice clause", '0008 INV-I5',
     "treat only the arriving notice's attested carriers on HELD rows",
     'assert v.store._conn.execute("SELECT text, request_digest FROM replies").fetchall() == [(R.MARKER, R.MARKER)]'),
    ('tests/test_0047_t10a_reply.py::test_io_ii_3_a_reply_under_a_pending_notice_is_admitted_and_its_confirmation_treats_it',
     "0008's INV-I5, its fourth mutant, and INV-I7's confirm_notice clause", '0008 INV-I7',
     '`confirm_notice` then treats the held row and every other held carrier of the target',
     'assert v.store._conn.execute("SELECT text, request_digest FROM replies").fetchall() == [(R.MARKER, R.MARKER)]'),
    ('tests/test_0047_t11b_portability.py::test_q10_ties_a_second_resolve_and_a_resolve_before_its_challenge_each_refuse',
     'INV-Q10 at §6f', '0008 INV-Q10',
     'two acts at one position refuse the unit',
     '_refused(_mem(tmp_path, "b.db"), _edit(f, "tie.jsonl", lambda rs: rs + [tie]), "one position", restore=True)'),
    ('tests/test_0047_t11b_portability.py::test_s2_research_rm_q_a_new_act_at_a_held_acts_position_ties',
     'RM-Q (INV-Q10)', '0008 INV-Q10',
     'two acts at one position refuse the unit',
     '_refused(b, g, "one position", restore=True)'),
    ('tests/test_0047_t11b_portability.py::test_q10_incomparable_or_unknown_positions_refuse_unless_the_challenge_is_resolved',
     '(INV-Q10, INV-R23;', '0008 INV-Q10',
     'an order that cannot be established',
     '_refused(_mem(tmp_path, "b.db"), unresolved, "cannot be ordered")'),
    ('tests/test_0047_t11b_portability.py::test_rm1_a_legacy_position_restores_first_among_proof_acts_and_refuses_whole_in_default',
     'R-M1 (INV-Q10, INV-R23)', '0008 INV-Q10',
     'an order that cannot be established',
     '_refused(_mem(tmp_path, "c.db"), testimony, "cannot be ordered", restore=True)'),
    ('tests/test_0047_t11b_portability.py::test_rm1_a_legacy_position_restores_first_among_proof_acts_and_refuses_whole_in_default',
     'R-M1 (INV-Q10, INV-R23)', '0047 INV-R23',
     'or when an order it needs cannot be established',
     '_refused(_mem(tmp_path, "c.db"), testimony, "cannot be ordered", restore=True)'),
    ('tests/test_0047_t11b_portability.py::test_s2_research_rm_i_r_m1_needs_both_labels_proof_a_testimony_challenge_stays_incomparable',
     'RM-I (INV-Q10, INV-R23)', '0008 INV-Q10',
     'an order that cannot be established',
     '_refused(_mem(tmp_path, "b.db"), f, "cannot be ordered", restore=True)'),
    ('tests/test_0047_t11b_portability.py::test_s2_research_rm_i_r_m1_needs_both_labels_proof_a_testimony_challenge_stays_incomparable',
     'RM-I (INV-Q10, INV-R23)', '0047 INV-R23',
     'or when an order it needs cannot be established',
     '_refused(_mem(tmp_path, "b.db"), f, "cannot be ordered", restore=True)'),
    ('tests/test_0047_t11b_portability.py::test_q10_a_confirmation_before_the_challenge_is_consistent_and_an_incoming_challenge_meets_a_held_one',
     "INV-Q10 at §6f's first row", '0008 INV-Q10',
     'judge only incoming confirmations',
     '_refused(c, later, "made under challenge", restore=True)'),
    ('tests/test_0047_t11b_portability.py::test_q10_a_resolved_history_is_admitted_with_the_challenge_held_and_the_rest_arriving',
     'INV-R23 and INV-Q10', '0008 INV-Q10',
     'a legitimate challenge → resolve → confirm history is admitted',
     'assert (r["confirmations"], r["replies"], r["acts_existing"]) == (2, 1, 1)'),
    ('tests/test_0047_t11b_portability.py::test_s2_research_rm_y_a_resolve_after_the_confirmation_does_not_clear_it',
     'RM-Y (INV-Q10, INV-R23)', '0008 INV-Q10',
     'a confirmation made under a challenge that is unresolved in H is refused',
     '_refused(_mem(tmp_path, "b.db"), g, "made under challenge", restore=True)'),
    ('tests/test_0047_t11b_portability.py::test_s2_research_rm_y_a_resolve_after_the_confirmation_does_not_clear_it',
     'RM-Y (INV-Q10, INV-R23)', '0047 INV-R23',
     'an incoming confirmation is refused when a challenge of its edge is unresolved in destination ∪ file and ordered before it',
     '_refused(_mem(tmp_path, "b.db"), g, "made under challenge", restore=True)'),
    ('tests/test_0047_t10b_read.py::test_r18_the_compiler_input_never_holds_a_challenged_fact',
     "INV-R3 at the wiki compiler's input", '0047 INV-R3',
     'An edge with an active challenge reaches NO assertion surface',
     'assert llm.prompts["compile"] and all("CFO at Acme" not in p for p in llm.prompts["compile"])'),
    ('tests/test_0047_t11b_portability.py::test_d14_the_commit_primitive_refuses_an_act_labelled_local_or_keyed_in_the_callers_grammar',
     '(INV-Q5, 0047 INV-R21)', '0047 INV-R21',
     "An act's origin never upgrades",
     'with pytest.raises(ValueError, match="an import writes only"):'),
    ('tests/test_0045_t9_write.py::test_f2_an_imported_confirmation_is_testimony_and_does_not_lift_the_guard',
     '0047 INV-R21: only `local` and `restored` confirmations count', '0047 INV-R21',
     'only `local` and `restored` confirmations count toward `g(e)`',
     '_refuses(mem.confirm, U, "e1", correlation_id="k2", match="source episode was redacted")'),
    ('tests/test_0044_t11a_portability.py::test_inv_a23_an_ended_held_row_and_a_live_arrival_is_older_evidence_a_no_op',
     'INV-A23: an ended local episode is never revived', '0044 INV-A23',
     'an ended local episode is never revived',
     'assert (rows, existing) == ([], 1)'),
    # research's T12 stage-2 S2-M1: this cell's second half is INV-I3 (the held challenge replays in the unit)
    ('tests/test_0047_t11b_portability.py::test_q10_a_confirmation_under_an_open_challenge_refuses_in_one_file_and_across_two',
     "0008's INV-I3: the held challenge REPLAYS", '0008 INV-I3',
     'never exempts another new act in the unit from validation',
     '_refused(c, no_resolve, "made under challenge", restore=True)'),
)
# a row whose subject is other rows: (the quote that must occur in its row, the rows it stands for)
DERIVED = {"0018 I31": ("0018's I13–I23 are unchanged", [f"0018 I{n}" for n in range(13, 24)])}
_RENAME = re.compile(r"live node(?: is)? (test_\w+)")


# 0018's ids are bare in their own document (I13), so a BARE citation binds only in that document's own test modules:
# its own files and the 0044 tranches that implement its amendment (T5-2 the step, T6 the operation, T7 undo); other
# specs carry their own I13–I17. The INV-I form (`INV-I24`, T5's spelling) binds anywhere — 0008's INV-I rows stop at I7.
_BARE_SCOPE = {"0018": re.compile(r"tests/test_(?:0018_\w+|migrate_cli|0044_t[5-7]_\w+)\.py::"),
               "0008": re.compile(r"tests/test_(?:0008_\w+|confirm_contract_0008)\.py::")}   # its C8, C11
# the map's own test cites row ids as DATA, never as a claim to test them
_SELF = "tests/test_0044_t12_obligation_map.py::"


@functools.lru_cache(maxsize=None)
def _tok(rid: str) -> re.Pattern:
    pre = "(?:INV-)?" if rid.startswith("I") and not rid.startswith("INV-") else ""     # 0018's I24 written INV-I24
    return re.compile(r"(?<![\w-])" + pre + re.escape(rid) + r"(?![\w′])")


def clause_cell(row: dict, clause: str):
    """Which cell of the row a quoted clause comes from, DERIVED from the row's own columns (research's T12 S2-P1): the
    invariant, or the second column (`mutant`; `check` where the row's id shares its cell with the invariant, as in
    0018's I13–I23 and 0008's C-rows, whose second column is the executable check). None: the clause is in no cell."""
    cells = row["text"].split("|")
    named = [c for c in cells if c.strip()]
    second = "check" if cells and cells[0].strip() else "mutant"
    for k, c in enumerate(named):
        if clause in c:
            return "invariant" if k == 0 else second if k == 1 else f"column {k + 1}"
    return None


def complement() -> list:
    """Every bold-id table row of the seven documents that is neither a programme row nor a declared NON_ROW."""
    R, out = rows(), []
    for doc, f, _pat in SPECS:
        text = (ROOT / "specs" / f"{f}.md").read_text(encoding="utf-8")
        for m in re.finditer(r"^\| \*\*([^*|]+?)\*\*", text, re.M):
            tok = m.group(1).split()[0]
            if not _ID.fullmatch(tok) or f"{doc} {tok}" in R:
                continue
            if not any(d == doc and re.fullmatch(rx, tok) for d, rx in NON_ROWS):
                out.append(f"{doc} {tok}")
    return sorted(set(out))


def symbol(rel: str, anchor: str) -> str:
    """file::symbol of an anchor: the innermost class/def whose span holds the anchor's first line."""
    src = (ROOT / rel).read_text(encoding="utf-8")
    k = src.find(anchor)
    if k < 0 or not rel.endswith(".py"):
        return rel
    line = src.count("\n", 0, k) + 1
    holding = [path for lo, hi, path in _def_spans(str(ROOT), rel) if lo <= line <= hi]
    return f"{rel}::{'.'.join(max(holding, key=len)) if holding else '<module>'}"


@functools.lru_cache(maxsize=64)
def _def_spans(_root: str, rel: str) -> tuple:
    """Every class/def of a file as (first line, last line, its qualified path), parsed once per tree and file."""
    out = []

    def walk(node, path):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.append((ch.lineno, ch.end_lineno, tuple(path + [ch.name])))
                walk(ch, path + [ch.name])
            else:
                walk(ch, path)
    walk(ast.parse((pathlib.Path(_root) / rel).read_text(encoding="utf-8")), [])
    return tuple(out)


def rows() -> dict:
    return _rows_at(str(ROOT))


@functools.lru_cache(maxsize=4)
def _rows_at(_root: str) -> dict:
    """The parse, memoised per tree (the planted cells derive many times over one tree)."""
    out = {}
    for doc, f, pat in SPECS:
        text = (ROOT / "specs" / f"{f}.md").read_text(encoding="utf-8")
        for m in re.finditer(r"^\| \*\*(" + pat + r")\*\*(.*)$", text, re.M):
            body = m.group(2)
            first = body.split("|")[1].strip() if body.startswith(" |") else body.split("|")[0].strip()
            out[f"{doc} {m.group(1)}"] = {"doc": doc, "id": m.group(1), "text": body,
                                          "names": sorted(set(re.findall(r"`(test_\w+)`", body))),
                                          "files": sorted(set(re.findall(r"`(tests/test_\w+\.py)`", body))),
                                          "withdrawn": first.startswith("**Withdrawn")}
    return out


_BANNER = re.compile(r"^\s*# ?[=\-]{4,}")


def nodes() -> dict:
    """Every test function under tests/, {node: its docstring + its section banner}, by AST (a parametrised node is its
    function). The banner is the nearest comment line above the def that opens with a rule of `=` or `-`."""
    return _nodes_at(str(ROOT))[0]


@functools.lru_cache(maxsize=4)
def _nodes_at(_root: str) -> tuple:
    """({node: docstring + banner}, {node: (its source segment, its first line)}), memoised per tree."""
    out, srcs = {}, {}
    for p in sorted((ROOT / "tests").glob("test_*.py")):
        src = p.read_text(encoding="utf-8")
        lines = src.split("\n")
        banners = [i for i, l in enumerate(lines) if _BANNER.match(l)]
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_"):
                above = [i for i in banners if i < n.lineno - 1]
                banner = lines[above[-1]] if above else ""
                out[f"tests/{p.name}::{n.name}"] = (ast.get_docstring(n) or "") + "\n" + banner
                srcs[f"tests/{p.name}::{n.name}"] = (ast.get_source_segment(src, n) or "", n.lineno)
    return out, srcs


def assert_line(node: str, text: str):
    """file:line of `text` in the test function's own source (its first line that holds it), or None."""
    seg, first = _nodes_at(str(ROOT))[1].get(node, ("", 0))
    for i, line in enumerate(seg.split("\n")):
        if text in line:
            return f"{node.split('::')[0]}:{first + i}"
    return None


def renames() -> dict:
    """{old node name: live node name} from citation_debt.py's declared stale citations."""
    tree = ast.parse((ROOT / "specs" / "citation_debt.py").read_text(encoding="utf-8"))
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant) and isinstance(k.value, str) \
                        and k.value.startswith("test_") and isinstance(v.value, str):
                    m = _RENAME.search(v.value)
                    if m:
                        out[k.value] = m.group(1)
    return out


def _strict_pairs(pairs):
    """0026's evidence-boundary rule: a duplicate key is a REFUSAL, never last-wins."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r}")
        out[k] = v
    return out


def def_digest(group: str, mutant: tuple) -> str:
    """The digest of one definition as it ran: its group label and the (name, file, anchor, replacement) tuple."""
    return hashlib.sha256(json.dumps([group, *mutant], ensure_ascii=False).encode()).hexdigest()


def tree_digest(files) -> str:
    h = hashlib.sha256()
    for rel in sorted(set(files)):
        h.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    return h.hexdigest()


def pin_files(groups) -> list:
    src = [str(p.relative_to(ROOT)) for p in (ROOT / "src" / "veracium").rglob("*.py")]
    tests = [str(p.relative_to(ROOT)) for p in (ROOT / "tests").glob("*.py")]
    return sorted(set(src + tests + [m[1] for _g, _c, ms in groups for m in ms]))


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _with_cell(entry, row):
    return None if entry is None else {**entry, "cell": clause_cell(row, entry.get("clause", ""))}


def derive(defs=None, result=None) -> dict:
    defs = defs or _load(CAMPAIGN / "defs.py", "obligation_campaign_defs")
    result = result or json.loads((CAMPAIGN / "result.json").read_text(), object_pairs_hook=_strict_pairs)
    R, N, RN = rows(), nodes(), renames()
    by_name = {}
    for node in N:
        by_name.setdefault(node.split("::")[1], []).append(node)
    bound = {k: {} for k in R}
    for k, r in R.items():
        tok, scope = _tok(r["id"]), _BARE_SCOPE.get(r["doc"])
        for node, doc in N.items():
            if node.startswith(_SELF) or r["id"] not in doc:   # the literal id is a necessary condition of every match
                continue
            hit = tok.search(doc)
            if (hit and scope is not None and not hit.group(0).startswith("INV-") and not scope.match(node)
                    and f"{r['doc']} {r['id']}" not in doc):          # "0008 C11", qualified by its document, anywhere
                hit = None
            if hit or (r["id"].endswith("′") and r["id"] in doc):
                bound[k][node] = "cites the row"
        for name in r["names"]:
            live = name if name in by_name else RN.get(name)
            for node in by_name.get(live, []):
                bound[k].setdefault(node, "named by the row" + ("" if live == name else f" (declared rename of {name})"))
        for f in (r["files"] if not r["names"] else ()):        # a FILE binds only a row that names no test
            for node in N:
                if node.startswith(f + "::"):
                    bound[k].setdefault(node, "in the file the row names")
    for k, (_q, of) in DERIVED.items():
        for o in of:
            for node, how in bound.get(o, {}).items():
                bound[k].setdefault(node, f"bound to {o.split()[1]}, which this row stands for")
    answers, sites = {}, {}
    for g, _cells, ms in defs.GROUPS:
        for m in ms:
            key = f"{g} :: {m[0]}"
            sites[key] = symbol(m[1], m[2])
            a = ({k for k, r in R.items() if _tok(r["id"]).search(m[0])}
                 | {e["row"] for e in defs.ANSWERS.get(key, ())})
            a -= {row for (kk, row) in getattr(defs, "NOT_ANSWERS", {}) if kk == key}
            answers[key] = sorted(a | {k for k, (_q, of) in DERIVED.items() if a & set(of)})
    outcome = {f"{x['group']} :: {x['mutant']}": x for x in result["rows"]}
    digests = {f"{g} :: {mu[0]}": def_digest(g, mu) for g, _c, ms in defs.GROUPS for mu in ms}
    stale_defs = sorted(k for k, x in outcome.items() if x.get("def_digest") != digests.get(k))
    out_rows, unbound_kills = {}, []
    for k, r in R.items():
        kills = []
        for key, ans in answers.items():
            x = outcome.get(key)
            if k in ans and x is not None and x.get("outcome") == "KILLED":
                for cell, kind in sorted(x["cell_kinds"].items()):
                    base = cell.split("[")[0]
                    if base in bound[k]:
                        kills.append({"mutant": key, "node": base, "kind": kind})
        for key, ans in answers.items():
            x = outcome.get(key)
            if k in ans and x is not None and x.get("outcome") == "KILLED" and not r["withdrawn"]:
                killers = sorted({c.split("[")[0] for c in x["cell_kinds"]})
                if not set(killers) & set(bound[k]):
                    unbound_kills.append({"row": k, "mutant": key, "killing_nodes": killers})
        state = ("withdrawn" if r["withdrawn"] else "closed" if kills
                 else "open: no bound node" if not bound[k]
                 else "open: no answering mutant" if not any(k in a for a in answers.values())
                 else "open: no answering mutant killed by a bound node")
        out_rows[k] = {"state": state, "bound": dict(sorted(bound[k].items())), "kills": kills,
                       "answering": [{"mutant": key, "site": sites[key],
                                      "annotation": _with_cell(next((e for e in defs.ANSWERS.get(key, ()) if e["row"] == k),
                                                                    None), r)}
                                     for key in sorted(key for key, a in answers.items() if k in a)]}
    retired = [{**x, "inverse_outcome": outcome.get(x.get("inverse"), {}).get("outcome")} for x in defs.RETIRED]
    return {"rows": out_rows, "gates": {d: {"source": g[0], "quote": g[1]} for d, g in GATES.items()},
            "campaign": {"summary": result["summary"], "pin_digest": result.get("pin_digest"),
                         "tree_digest": tree_digest(pin_files(defs.GROUPS)),
                         "defined": len(answers), "results": len(outcome), "retired": retired},
            "binding_edits": [{"node": n, "text": t, "row": row, "clause": cl,
                               "cell": clause_cell(R[row], cl) if row in R else None,
                               "asserts": ln, "line": assert_line(n, ln), "bound": n in bound.get(row, {})}
                              for n, t, row, cl, ln in BINDING_EDITS],
            "_answer_overlap": sorted(f"{kk} -> {row}" for (kk, row) in getattr(defs, "NOT_ANSWERS", {})
                                      if any(e.get("row") == row for e in defs.ANSWERS.get(kk, ()))),
            "findings_unbound_kills": unbound_kills,
            "_stale_defs": stale_defs,
            "not_answers": [{"mutant": kk, "row": row, "reason": why}
                            for (kk, row), why in sorted(getattr(defs, "NOT_ANSWERS", {}).items())],
            "_unknown_not_answers": sorted(f"{kk} -> {row}" for (kk, row) in getattr(defs, "NOT_ANSWERS", {})
                                           if kk not in answers or row not in R),
            "_unknown_answers": sorted((key, e.get("row")) for key, ans in defs.ANSWERS.items() for e in ans
                                       if key not in answers or e.get("row") not in R),
            "_bad_annotations": sorted((key, e.get("row")) for key, ans in defs.ANSWERS.items() for e in ans
                                       if e.get("row") in R and (not e.get("why") or not e.get("clause")
                                                                 or e["clause"] not in R[e["row"]]["text"])),
            "_complement": complement()}


def problems(m: dict) -> list:
    out = []
    for d, g in m["gates"].items():
        if g["source"] and g["quote"] not in (ROOT / "specs" / f"{g['source']}.md").read_text(encoding="utf-8"):
            out.append(f"the {d} gate's quote no longer occurs in specs/{g['source']}.md")
    for k, (q, _of) in DERIVED.items():
        if q not in rows().get(k, {}).get("text", ""):
            out.append(f"{k} no longer reads {q!r}: its DERIVED binding is stale")
    c = m["campaign"]
    if c["pin_digest"] != c["tree_digest"]:
        out.append(f"the campaign ran at pin digest {str(c['pin_digest'])[:16]}, the tree is {c['tree_digest'][:16]} — "
                   f"re-run the consolidated campaign")
    if c["defined"] != c["results"]:
        out.append(f"the campaign holds {c['results']} result(s) for {c['defined']} defined mutant(s)")
    if not c["summary"].get("controls_green"):
        out.append("a campaign control was not green")
    for key, a in m["_unknown_answers"]:
        out.append(f"ANSWERS names an unknown mutant or row: {key!r} -> {a!r}")
    for f in m["findings_unbound_kills"]:
        out.append(f"FINDING {f['row']}: answering mutant {f['mutant']!r} is killed only by nodes not bound to it "
                   f"({', '.join(n.split('::')[1] for n in f['killing_nodes'])}) — a BINDING_EDIT, a bound cell, or "
                   f"NOT_ANSWERS")
    for k in m["_stale_defs"]:
        out.append(f"result row {k!r} ran a definition other than campaign/defs.py's (or carries no def_digest) — "
                   f"re-run it")
    for x in m["_answer_overlap"]:
        out.append(f"ANSWERS and NOT_ANSWERS both hold {x}: one judgement contradicts the other (research's S2-P2)")
    for x in m["_unknown_not_answers"]:
        out.append(f"NOT_ANSWERS names an unknown mutant or row: {x}")
    for key, a in m["_bad_annotations"]:
        out.append(f"ANSWERS entry {key!r} -> {a!r} lacks a why, or its clause is not quoted from the row")
    for (d, rx), (_why, src) in NON_ROWS.items():
        if src and src[1] not in (ROOT / "specs" / f"{src[0]}.md").read_text(encoding="utf-8"):
            out.append(f"the {d} NON_ROW family {rx!r} cites words its spec no longer holds: {src[1]!r}")
    for t in m["_complement"]:
        out.append(f"{t}: a bold id row that is neither a programme row nor a declared NON_ROW family")
    R = rows()
    for k, q in WITHDRAWN.items():
        if not R.get(k, {}).get("withdrawn") or q not in R[k]["text"]:
            out.append(f"{k}: its withdrawal no longer reads {q!r}")
    for k, r in R.items():
        if r["withdrawn"] and k not in WITHDRAWN:
            out.append(f"{k} reads withdrawn but WITHDRAWN does not quote it")
    N = nodes()
    names = {n.split("::")[1] for n in N}
    for old, live in renames().items():
        if live not in names and any(old in r["names"] for r in R.values()):
            out.append(f"citation_debt declares {old} renamed to {live}, which is not a test node")
    for e in m["binding_edits"]:
        if e["text"] not in N.get(e["node"], ""):
            out.append(f"binding edit gone: {e['node']} no longer carries {e['text']!r}")
        if e["row"] not in R or e["clause"] not in R[e["row"]]["text"]:
            out.append(f"binding edit {e['node']} -> {e['row']}: its clause {e['clause']!r} is not the row's text")
        if e["line"] is None:
            out.append(f"binding edit {e['node']} -> {e['row']}: its asserting line {e['asserts']!r} is not in the test")
        if not e["bound"]:
            out.append(f"binding edit {e['node']} -> {e['row']}: the node is not bound to the row")
    for x in m["campaign"]["retired"]:
        if not x.get("commit") or x.get("inverse_outcome") != "KILLED":
            out.append(f"retired {x['mutant']!r}: its superseding commit is unnamed or its inverse "
                       f"{x.get('inverse')!r} reads {x.get('inverse_outcome')!r}, not KILLED")
    for k, r in m["rows"].items():
        if r["state"].startswith("open"):
            out.append(f"{k}: {r['state']}")
    return out


def render(m: dict) -> str:
    c = m["campaign"]
    L = ["# The PRODUCT obligation map (GENERATED: `specs/evidence/0044/obligation_map.py`; do not edit)", "",
         f"The consolidated campaign: {c['summary']['killed']} of {c['summary']['mutants']} mutants KILLED, "
         f"{len(c['retired'])} retired with reasons (`campaign/defs.py`); pin digest `{str(c['pin_digest'])[:16]}`.", "",
         "## The gate, per document (quoted)", ""]
    for d, g in m["gates"].items():
        L.append(f"- **{d}**: {g['quote']}" + (f" — `specs/{g['source']}.md`" if g["source"] else ""))
    L += ["", "## Retired mutants (each with its superseding commit and its inverse's outcome)", ""]
    for x in c["retired"]:
        L.append(f"- {x['mutant']} — {x['reason']} (commit {x.get('commit')}; inverse {x.get('inverse')}: "
                 f"{x.get('inverse_outcome')})")
    L += ["", "## Pairs judged NOT to answer (NOT_ANSWERS)", ""]
    L += [f"- {x['row']} ← {x['mutant']}: {x['reason']}" for x in m["not_answers"]] or ["- none"]
    L += ["", "## Open findings: answering mutants killed only by unbound nodes", ""]
    L += [f"- {f['row']} ← {f['mutant']}" for f in m["findings_unbound_kills"]] or ["- none"]
    L += ["", "## Binding edits (citations T12 added to existing tests)", ""]
    L += ["| node | now cites | row | the row's clause (its cell) | the line that asserts it |", "|---|---|---|---|---|"]
    L += [f"| `{e['node'].split('::')[1]}` | “{e['text']}” | {e['row']} | “{e['clause']}” ({e['cell']}) | "
          f"`{e['line']}`: `{e['asserts']}` |" for e in m["binding_edits"]]
    L += ["", "## Rows", "", "| row | state | bound nodes (by how) | killing (mutant → node, kind) |", "|---|---|---|---|"]
    for k, r in m["rows"].items():
        from collections import Counter
        how = ", ".join(f"{n} {h}" for h, n in sorted(Counter(v.split(" (")[0] for v in r["bound"].values()).items()))
        kills = "; ".join(f"{x['mutant'].split(' :: ', 1)[1]} → `{x['node'].split('::')[1]}` ({x['kind']})"
                          for x in r["kills"][:3]) + (f"; +{len(r['kills']) - 3}" if len(r["kills"]) > 3 else "")
        L.append(f"| {k} | {r['state']} | {how or '—'} | {kills or '—'} |")
    return "\n".join(L) + "\n"


def _public(m: dict) -> dict:
    return {k: v for k, v in m.items() if not k.startswith("_")}


def main(argv) -> int:
    m = derive()
    bad = problems(m)
    for b in bad:
        print("REFUSED:", b)
    js, md = json.dumps(_public(m), indent=1, sort_keys=True, ensure_ascii=False) + "\n", render(m)
    if "--write" in argv:
        OUT_JSON.write_text(js)
        OUT_MD.write_text(md)
        n = sum(r["state"] == "closed" for r in m["rows"].values())
        print(f"wrote {OUT_JSON.name}, {OUT_MD.name}: {n} of {len(m['rows'])} rows closed")
        return 1 if bad else 0
    if "--check" in argv:
        if not OUT_JSON.exists() or OUT_JSON.read_text() != js or OUT_MD.read_text() != md:
            print("STALE: regenerate with --write")
            return 1
        return 1 if bad else 0
    sys.stdout.write(md)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
