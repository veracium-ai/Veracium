#!/usr/bin/env python3
# Mutation-Matrix: tests/test_sr2_01_wiki_cache_mutants.py::test_the_table_check_refuses_each_tampered_table
"""SR2-01 (shipped-changes round 2, a patch-release blocker): every mutant of the fix demonstrated red.

The fix: compile._CONTENTION_POLICY_VERSION bumped to 0012-v2, so a wiki cached by released code under the old digest
(round 1's "(no verified facts yet)"; v0.27.x's model-written empty body) is re-keyed; a pairing gate that refuses a
change to the code-owned empty body or the branch that selects it without a bump; and, found in the fix, a cached
code-owned empty body is stale on ANY store_version advance (a model summary keeps the write threshold). Each mutant is
a code edit run by the shared protocol (specs/evidence/mutation_protocol.py) on a copy of the tracked tree, killed by
assertion in ITS named cells, with an HONEST probe that still passes under it (a model-written body below the threshold
is served from the cache). Beside them, a NO-OP control for compile.py and one classifier negative control.

    $PY specs/evidence/sr2-01/wiki_cache_mutants.py --check     # fast: definitions, anchors, digests, every row good
    TMPDIR=/dev/shm $PY specs/evidence/sr2-01/wiki_cache_mutants.py --write
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import mutation_protocol as _protocol  # noqa: E402

TABLE = HERE / "mutation-table.json"     # the name tests/test_closure_mutants.py finds
SELF = "specs/evidence/sr2-01/wiki_cache_mutants.py"
K = "src/veracium/compile.py"
T = "tests/test_sr2_01_wiki_upgrade.py"
SUBJECT = "sr2-01-wiki-cache"
B = "src/veracium/budgets.py"
FIXTURES = ("specs/evidence/sr2-01/legacy-empty-wiki-v0.31.0.sqlite", "specs/evidence/sr2-01/legacy-empty-wiki-v0.27.1.sqlite",
            "specs/evidence/sr2-01/legacy-empty-wiki.json")
DIGESTED = (K, B, T, *FIXTURES, "specs/evidence/mutation_protocol.py", _protocol.KINDS, SELF)

C = lambda name: f"{T}::{name}"                                                       # noqa: E731
P = lambda name: [C(f"{name}[v0.31.0]"), C(f"{name}[v0.27.1]")]                        # noqa: E731
REVIEWER = P("test_sr2_01_the_reviewers_sequence_does_not_serve_the_legacy_body")
BETWEEN = P("test_sr2_01_a_read_between_the_upgrade_and_the_grounded_write")
NO_LLM = P("test_sr2_01_a_provider_free_reader_of_a_legacy_row_gets_the_stale_notice")
FRESH = C("test_sr2_01_a_fresh_cached_empty_body_is_stale_after_any_write")
GATE = C("test_sr2_01_the_policy_version_is_paired_with_the_empty_body_and_its_branch")
HONEST = C("test_sr2_01_a_model_written_body_below_the_threshold_is_still_served")
N2_THIRD = C("test_n2_a_cached_empty_body_after_a_third_party_write_gets_the_notice_without_the_model_claim")
N2_GROUNDED = C("test_n2_a_cached_empty_body_after_a_grounded_write_gets_the_same_notice")
N2_IDENTITY = C("test_n2_an_identity_stale_empty_body_keeps_0012s_notice")
N2_CLI = C("test_n2_the_store_only_cli_recall_prints_the_notice_after_a_write")

# (id, kind, file, [(anchor, replacement)], named cells, honest nodes, reason or None, what)
MUTANTS = [
    ("SR2-01-no-bump", "product", K,
     [('_CONTENTION_POLICY_VERSION = "0012-v2"\n', '_CONTENTION_POLICY_VERSION = "0012-v1"\n')],
     [*REVIEWER, *BETWEEN, *NO_LLM, GATE], [HONEST], None,
     "the policy version not bumped: a wiki cached by released code keeps its old digest and its old body (SR2-01)"),
    ("SR2-01-body-changed-without-a-bump", "product", K,
     [('EMPTY_GROUNDED_BODY = "(no verified facts in this view)"\n', 'EMPTY_GROUNDED_BODY = "(no verified facts here)"\n')],
     [GATE], [HONEST], None,
     "the code-owned empty body re-worded under the same policy version (round 1's SR1-03 change, repeated)"),
    ("SR2-01-branch-changed-without-a-bump", "product", K,
     [("    raw = (EMPTY_GROUNDED_BODY if not edges and not episodes\n", "    raw = (EMPTY_GROUNDED_BODY if not edges\n")],
     [GATE], [HONEST], None,
     "the empty-input selection changed under the same policy version (2f3899be's shape: the branch, not the words)"),
    ("SR2-01-empty-body-keeps-the-threshold", "product", K,
     [("    if behind > 0 and _is_code_owned_empty(body):\n", "    if False and _is_code_owned_empty(body):\n")],
     [*BETWEEN, FRESH], [HONEST], None,
     "a cached code-owned empty body waits for the write threshold, so it is served above a verified fact (found in "
     "the fix)"),
    # ---- research's stage 2 on the round-3 fix, N2: the provider-free notice for a cached empty body ---------------
    ("N2-the-empty-row-gets-0012s-notice", "product", K,
     [("            return _budgets.STALE_EMPTY_WIKI_NOTICE\n", "            return _budgets.STALE_WIKI_NOTICE\n")],
     [N2_THIRD, N2_GROUNDED, N2_CLI], [HONEST], None,
     "a cached empty body stale by a write alone is served the notice that says a model is needed, where its "
     "recompile may call none (N2)"),
    ("N2-every-stale-row-gets-the-empty-notice", "product", K,
     [("    return _budgets.STALE_WIKI_NOTICE\n\n\ndef ", "    return _budgets.STALE_EMPTY_WIKI_NOTICE\n\n\ndef ")],
     [*NO_LLM, N2_IDENTITY], [HONEST], None,
     "the selection widened to every stale row: a legacy or identity-stale row loses 0012's notice (N2)"),
    ("N2-identity-stale-empty-row-gets-the-empty-notice", "product", K,
     [("        if digest == _policy_digest(relations, **kw) and _is_code_owned_empty(body):\n",
       "        if _is_code_owned_empty(body):\n")],
     [N2_IDENTITY], [HONEST], None,
     "the row's digest not checked: a code-owned empty body stale by IDENTITY gets the write-stale notice (N2, "
     "0003 v18.5's 'an identity-stale row keeps 0012's notice')"),
]


def _noop(rel, anchor, cells):
    return (f"NOOP-{pathlib.Path(rel).stem}", rel, [(anchor, "# no-op control: a comment, no behaviour\n" + anchor)],
            sorted(set(cells)), f"a comment edit in {rel}: its mutants' cells must all pass", "SURVIVED")


def _cells_of(rel):
    return [c for m in MUTANTS if m[2] == rel for c in m[4]]


# (id, file, [(anchor, replacement)], named cells, what, the outcome the classifier must give)
CONTROLS = [
    _noop(K, "def _is_code_owned_empty(", _cells_of(K)),
    ("CTRL-unrelated-TypeError", K,
     [("    behind = store.store_version(user_id) - version_at_compile\n",
       '    raise TypeError("an unrelated execution failure (classifier negative control)")\n'
       "    behind = store.store_version(user_id) - version_at_compile\n")],
     [FRESH], "an UNRELATED TypeError in needs_recompile: every cell fails for no reason a row names", "UNCLASSIFIED"),
]

SUBJECT_P = _protocol.Subject(
    spec="0003", finding=SUBJECT, table=TABLE, digested=DIGESTED, mutants=MUTANTS, controls=CONTROLS,
    import_modules=("veracium.compile", "veracium"), import_specs=(), cells_files=(T,), kinds=("product",))

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
