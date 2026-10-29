#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0003_within_episode_mutants.py::test_the_table_check_refuses_each_tampered_table
"""0003/within-episode §6 (INV-WE1–WE5, WE8, WE9): every mutant the amendment names, demonstrated red.

The amendment (research's candidate; the owner, 2026-10-29: "Contest, retire nothing") is outside the tree until its
fold, so its phrases are not read from spec bytes here: each row's id carries the invariant it demonstrates. Every
mutant is a code edit run by the shared protocol (specs/evidence/mutation_protocol.py) on a copy of the tracked tree,
killed by assertion in ITS named cells, with an HONEST probe that still passes under it. Beside them, per mutated
file, a NO-OP control (a comment edit outside any string: the bytes change, the behaviour does not) whose named cells
must all pass, so no kill is merely "this file changed"; and one classifier negative control.

    $PY specs/evidence/0003/within_episode_mutants.py --check     # fast: definitions, anchors, digests, every row good
    TMPDIR=/dev/shm $PY specs/evidence/0003/within_episode_mutants.py --write
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import mutation_protocol as _protocol  # noqa: E402

TABLE = HERE / "within_episode" / "mutation-table.json"     # the name tests/test_closure_mutants.py finds
SELF = "specs/evidence/0003/within_episode_mutants.py"
G = "src/veracium/graph.py"
I = "src/veracium/ingest.py"
P = "src/veracium/prompts.py"
S = "src/veracium/schema.py"
Q = "src/veracium/store/sqlite.py"
T = "tests/test_0003_within_episode.py"
SUBJECT = "within-episode"
DIGESTED = (G, I, P, S, Q, T, "specs/evidence/mutation_protocol.py", _protocol.KINDS, SELF)

C = lambda name: f"{T}::{name}"                                                       # noqa: E731
ORDER = [C(f"test_every_emission_order_leaves_the_same_active_set_and_row_set[{v}-{p}]")
         for v in ("two", "three") for p in ("no-prior", "prior-boston")]
REFINE = [C("test_a_refinement_of_one_city_is_not_a_contest[values0]"),
          C("test_a_refinement_of_one_city_is_not_a_contest[values1]")]
RETIRES = [C("test_a_contested_key_retires_no_prior_and_no_own_edge[values0]"),
           C("test_a_contested_key_retires_no_prior_and_no_own_edge[values1]")]
SINGLE = C("test_a_single_value_episode_supersedes_as_today")
REINFORCE = C("test_a_key_already_holding_both_values_still_records_its_contest")
LADDER = C("test_a_ladder_refusal_in_a_contested_key_keeps_its_own_row_and_gets_no_second")
ONE_GROUPING = C("test_one_grouping_decides_the_contest_with_the_priors")
GUARD = C("test_a_shorter_value_of_its_own_group_is_not_absorbed_in_a_contested_key")
COUNTER = C("test_the_counter_is_present_and_zero_on_every_uncontested_path")
RULE_SENT = C("test_the_extraction_rule_reaches_the_extractor")
SERIALIZED = C("test_a_ladder_refusal_serializes_exactly_as_before_the_field")
CLOSED = C("test_the_store_refuses_a_rule_version_outside_the_closed_set")

_RETIRE_GUARD = ("                if within_episode is not None:\n"
                 "                    continue      # specs/0003/within-episode §4b: a contested key retires NOTHING\n")
_FAST_PATH = ("        if len({_value_key(e.object) for e in es}) < 2:\n"
              "            continue                     # one value key: one group whatever the priors (the common case "
              "reads nothing)\n")
_GROUPING = "        g = {m.id: gk for gk, members in value_groups(priors + es).items() for m in members}\n"
_ABSORB_GUARD = ("        if within_episode is not None and prior.id in {p.id for p in within_episode}:\n"
                 "            continue          # specs/0003/within-episode §4b: only a SAME-group prior is absorbed in a "
                 "contested key\n")
_RULE = ('- A value the event says is NO LONGER true ("previously", "used to",\n'
         '  "formerly", "no longer", "moved from", "before that") is history, not a\n'
         '  current fact: do NOT emit it as a triple; say it in the episode ("moved\n'
         '  from Boston to Denver"). A value that is STILL true is current even when it\n'
         '  began in the past ("since 2019", "for ten years"): emit it as usual.\n')

# (id, kind, file, [(anchor, replacement)], named cells, honest nodes, reason or None, what)
MUTANTS = [
    ("WE1-emission-order", "product", G,
     [("    return ordered, len(contested)\n", "    return [(e, None) for e in edges], 0\n")],
     ORDER, [RULE_SENT], None, "per-edge supersession in emission order (the code before the amendment)"),
    ("WE1-grouping-by-value-key", "product", G,
     [(_GROUPING, "        g = {m.id: _value_key(m.object) for m in priors + es}\n")],
     REFINE, [RULE_SENT], None, "the contest grouped by _value_key, not value_groups: a refinement reads as two values"),
    ("WE2-priors-retired-first", "product", G, [(_RETIRE_GUARD, "")],
     RETIRES, [RULE_SENT], None, "the functional retire not withheld in a contested key"),
    ("WE3-group-check-on-every-key", "product", G,
     [(_FAST_PATH, ""), ("        if len({g[e.id] for e in es}) >= 2:\n", "        if len({g[e.id] for e in es}) >= 1:\n")],
     [SINGLE], [RULE_SENT], None, "every functional key treated as contested (no supersession at all)"),
    ("WE4-no-refusal-row", "product", G,
     [("    if not within_episode:\n        return []\n", "    if True:\n        return []\n")],
     ORDER + [REINFORCE], [RULE_SENT], None, "no within-episode refusal row is drafted"),
    ("WE4-counter-absent-unparseable", "product", I,
     [('                "within_episode_contested": 0,  # specs/0003/within-episode: present, zero on the unparseable '
       'path\n', "")],
     [COUNTER], [SINGLE], None, "the counter absent, not 0, on the unparseable path"),
    ("WE4-all-reinforce-rows-omitted", "product", G,
     [("refusals=_within_episode_drafts(edge, within_episode, set())), True", "refusals=[]), True")],
     [REINFORCE], [RULE_SENT], None, "a contested key whose edges all reinforce records no row"),
    ("WE4-ladder-row-relabelled", "product", G,
     [("    refusals += _within_episode_drafts(incoming, within_episode, {r.prior_edge_id for r in refusals})\n",
       "    refusals += _within_episode_drafts(incoming, within_episode, set())\n")],
     [LADDER], [RULE_SENT], None, "a pair the ladder refused also drafted within-episode (two rows)"),
    ("WE5-rule-not-sent", "product", P,
     [(_RULE, ""), ("\ndef date_context(", '\nPAST_VALUE_RULE = """- A value the event says is NO LONGER true ..."""\n\n\n'
                                          'def date_context(')],
     [RULE_SENT], [SINGLE], None, "the extraction rule in a constant the extractor is never sent"),
    ("WE8-absent-rule-version-serialized", "product", S,
     [('        if d.get("rule_version") is None:\n            d.pop("rule_version", None)\n', "")],
     [SERIALIZED], [SINGLE], None, "the absent rule_version dumped as null (every ladder refusal's digest moves)"),
    ("WE8-closed-set-unchecked", "product", Q,
     [("if d.rule_version is not None and d.rule_version not in DRAFTED_RULE_VERSIONS:", "if False:")],
     [CLOSED], [SINGLE], None, "the store accepts a rule_version outside the closed set"),
    ("WE9-absorption-guard-removed", "product", G, [(_ABSORB_GUARD, "")],
     [GUARD], [RULE_SENT], None, "absorption retires a differing-group edge in a contested key"),
    ("WE9-episode-only-grouping", "product", G,
     [(_GROUPING, "        g = {**{m.id: gk for gk, ms in value_groups(priors).items() for m in ms}, "
                  "**{m.id: gk for gk, ms in value_groups(es).items() for m in ms}}\n")],
     [ONE_GROUPING], [RULE_SENT], None, "the contest decided over the episode's edges alone, not with the priors"),
]


def _noop(rel, anchor, cells):
    return (f"NOOP-{pathlib.Path(rel).stem}", rel, [(anchor, "# no-op control: a comment, no behaviour\n" + anchor)],
            sorted(set(cells)), f"a comment edit in {rel}: its mutants' cells must all pass", "SURVIVED")


def _cells_of(rel):
    return [c for m in MUTANTS if m[2] == rel for c in m[4]]


# (id, file, [(anchor, replacement)], named cells, what, the outcome the classifier must give)
CONTROLS = [
    _noop(G, "def _within_episode_drafts(", _cells_of(G)),
    _noop(I, "def ingest_event(", _cells_of(I)),
    _noop(P, "def date_context(", _cells_of(P)),
    _noop(S, "class SupersessionPlan(BaseModel):", _cells_of(S)),
    _noop(Q, "    def forget_user(self, user_id) -> dict:", _cells_of(Q)),
    ("CTRL-unrelated-TypeError", G,
     [("    keys: dict = {}\n", '    raise TypeError("an unrelated execution failure (classifier negative control)")\n'
                             "    keys: dict = {}\n")],
     ORDER, "an UNRELATED TypeError in within_episode_order: every cell fails for no reason a row names",
     "UNCLASSIFIED"),
]

SUBJECT_P = _protocol.Subject(
    spec="0003", finding=SUBJECT, table=TABLE, digested=DIGESTED, mutants=MUTANTS, controls=CONTROLS,
    import_modules=("veracium.graph", "veracium.ingest", "veracium.prompts", "veracium.schema", "veracium.store.sqlite"),
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
