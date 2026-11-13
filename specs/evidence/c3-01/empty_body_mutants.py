#!/usr/bin/env python3
# Mutation-Matrix: tests/test_c3_01_empty_body_mutants.py::test_the_table_check_refuses_each_tampered_table
"""C3-01 (shipped-changes round 3's follow-up; specs/0003 §4c-ii v18.7/v18.8, I6d) and 0031 §4a-ii (v22.1, N1/N4):
every mutant of the fix demonstrated red.

The fix: the code-owned empty body carries its basis version (the cached row's, or the compile's version_at_begin), and
recall's bind read (`compile.empty_body_unbound`), after its last store read whose result can reach a response carrying
the body, leaves the body out when the user's store_version moved. Found in the fix by I6d's census: revocation's bump
followed its COMMIT, and the live data migration's restoration did not bump. With them, 0031 v22.1: serverInfo.version
is veracium's, and a start failure names no provider key. Each mutant is a code edit run by the shared protocol
(specs/evidence/mutation_protocol.py) on a copy of the tracked tree, killed by assertion in ITS named cells, with an
HONEST probe that still passes under it. Beside them, a NO-OP control per mutated file and one classifier control.

    $PY specs/evidence/c3-01/empty_body_mutants.py --check     # fast: definitions, anchors, digests, every row good
    TMPDIR=/dev/shm $PY specs/evidence/c3-01/empty_body_mutants.py --write
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import mutation_protocol as _protocol  # noqa: E402

TABLE = HERE / "mutation-table.json"     # the name tests/test_closure_mutants.py finds
SELF = "specs/evidence/c3-01/empty_body_mutants.py"
K = "src/veracium/compile.py"
I = "src/veracium/__init__.py"
V = "src/veracium/store/revocation.py"
D = "src/veracium/store/data_migration.py"
M = "src/veracium/mcp_server.py"
T = "tests/test_c3_01_empty_body_bind.py"
W = "tests/test_c3_01_writers_census.py"
S = "tests/test_0031_server_reports_itself.py"
SUBJECT = "c3-01-empty-body-bind"
DIGESTED = (K, I, V, D, M, "src/veracium/store/sqlite.py", T, W, S, "specs/evidence/c3-01/census_trace_plugin.py",
            "specs/evidence/mutation_protocol.py", _protocol.KINDS, SELF)

C = lambda name: f"{T}::{name}"                                                       # noqa: E731
R = lambda p: C(f"test_a_write_during_the_recall_leaves_the_empty_body_out_of_that_response[{p}]")   # noqa: E731
CACHED, COMPILE, AFTER_BOUND, EPISODES = (R("cached-body-before-snapshot"), R("compile-inputs-before-publication"),
                                          R("after-bound-wiki-before-detail"), R("after-selection-before-episodes"))
BOUNDARY = C("test_the_boundary_a_write_after_the_bind_read_is_not_in_that_response")
NO_WRITE = C("test_with_no_write_the_response_is_byte_identical_to_v18_6")
SUMMARY = C("test_a_model_summary_is_served_across_a_concurrent_write")
PROVIDER_FREE = C("test_a_provider_free_reader_leaves_the_body_out_and_calls_no_model")
OTHER_USER = C("test_another_users_write_leaves_the_body_served")
PRINCIPAL = C("test_a_principal_bearing_recall_is_unchanged")
STATIC = f"{W}::test_every_writer_of_a_table_a_recall_reads_advances_the_counter_or_is_named"
DYNAMIC = f"{W}::test_every_committed_transaction_that_changes_a_record_advances_the_counter_in_it"
SERVERINFO = f"{S}::test_serverinfo_is_veracium_and_its_version_by_the_handshake"
START_FAILURE = f"{S}::test_a_start_failure_states_its_own_cause_and_names_no_provider_key"
HELP = f"{S}::test_help_still_lists_the_provider_key"

_BIND_CALL = ('''        if _compile.empty_body_unbound(self.store, user_id, wiki, wiki_basis.get("basis")):
            wiki = None
''')
_BIND_BLOCK = ('''        # specs/0003 §4c-ii v18.7 (C3-01): the bind read, after the last store read whose result can reach a response
        # that carries the body (the selection, the redaction sets, the episodes, the contested build) and before
        # rendering. A write for the user since the empty body's basis leaves it out of this one response.
''' + _BIND_CALL)

# (id, kind, file, [(anchor, replacement)], named cells, honest nodes, reason or None, what)
MUTANTS = [
    ("C3-01-no-bind-read", "product", K,
     [('        return _SITE_EMPTY_BODY_BIND.fire(basis is None or store.store_version(user_id) != basis, "omit-body")\n',
       '        return _SITE_EMPTY_BODY_BIND.fire(False, "omit-body")\n')],
     [CACHED, COMPILE, AFTER_BOUND, EPISODES, PROVIDER_FREE], [PRINCIPAL], None,
     "no bind read: the empty body is served whatever was written during the call (v18.6, the round-3 limit)"),
    ("C3-01-bind-at-bound-wikis-return", "product", I,
     [(_BIND_BLOCK, ""),
      ("                item_cap=self.config.item_cap_tokens)\n",
       "                item_cap=self.config.item_cap_tokens)\n" + _BIND_CALL)],
     [AFTER_BOUND, EPISODES], [PRINCIPAL], None,
     "the bind read at bound_wiki's return: a write after it, before detail selection, is missed (the third placement)"),
    ("C3-01-bind-on-every-body", "product", K,
     [("    if body is None or not _is_code_owned_empty(body):\n        return False\n    with _SITE_EMPTY_BODY_BIND",
       "    if body is None:\n        return False\n    with _SITE_EMPTY_BODY_BIND")],
     [SUMMARY], [PRINCIPAL], None,
     "the bind applied to every body: a model summary is dropped by a concurrent write (broadening 0012's lag)"),
    ("C3-01-basis-after-the-inputs", "product", K,
     [('        _bind["drew"], _bind["drew_episodes"] = edges, episodes\n',
       '        _bind["drew"], _bind["drew_episodes"] = edges, episodes\n        _bind["basis"] = store.store_version(user_id)\n')],
     [COMPILE], [PRINCIPAL], None,
     "the compile's basis read after its inputs: a write between the inputs and that read is missed (the second placement)"),
    ("C3-01-always-omit", "product", K,
     [('        return _SITE_EMPTY_BODY_BIND.fire(basis is None or store.store_version(user_id) != basis, "omit-body")\n',
       '        return _SITE_EMPTY_BODY_BIND.fire(True, "omit-body")\n')],
     [NO_WRITE, OTHER_USER, BOUNDARY], [PRINCIPAL], None,
     "the empty body always omitted: the no-write response is no longer v18.6's"),
    ("C3-01-bind-before-the-episode-read", "product", I,
     [(_BIND_BLOCK, ""),
      ("        episodes = [e for e in self.store.episodes(user_id)\n",
       _BIND_CALL + "        episodes = [e for e in self.store.episodes(user_id)\n")],
     [EPISODES], [PRINCIPAL], None,
     "the bind read before the episode read: a write between the selection and the episodes is missed (the fourth)"),
    ("C3-01-revocation-bump-after-its-commit", "product", V,
     [("            store._bump(user_id)\n            return st[\"effects\"]\n", "            return st[\"effects\"]\n"),
      ("                apply_effect=lambda _conn, e: _apply_statement_effect(store, at, e))\n        store._conn.commit()\n",
       "                apply_effect=lambda _conn, e: _apply_statement_effect(store, at, e))\n        store._bump(user_id)\n"
       "        store._conn.commit()\n")],
     [DYNAMIC], [NO_WRITE], None,
     "revocation's bump after revocation_operation's COMMIT (as before the census): a reader sees revoked rows under the "
     "old counter"),
    ("C3-01-delete-episode-bump-after-its-commit", "product", "src/veracium/store/sqlite.py",
     [("                self._drop_contributions_for_survivor(row[0], \"episode\", episode_id)\n"
       "                self._bump(row[0])\n            self._conn.commit()\n",
       "                self._drop_contributions_for_survivor(row[0], \"episode\", episode_id)\n"
       "            self._conn.commit()\n            if row:\n                self._bump(row[0])\n"
       "                self._conn.commit()\n")],
     [DYNAMIC], [NO_WRITE], None,
     "delete_episode's bump after its COMMIT (research's stage-2 survivor on 35610a8a): the census must SEE every bump "
     "site, so a bump moved out of its transaction anywhere fails"),
    ("C3-01-restoration-without-a-bump", "product", D,
     [("    if restored:\n        store._bump(user)\n", "")],
     [STATIC], [NO_WRITE], None,
     "the live data migration's restoration without a bump (as before the census): reinstated edges under the old counter"),
    ("N1-the-version-left-unset", "product", M,
     [("    _set_server_version(server)            # specs/0031 §4a-ii (v22.1, N1)\n", "")],
     [SERVERINFO], [HELP], None,
     "serverInfo.version left to the SDK, which reports its own package version (0031 v22.1's V-SERVERINFO RED)"),
    ("N4-the-key-hint-restored", "product", M,
     [('raise SystemExit(f"veracium-mcp: failed to start: {e}\\n(see veracium-mcp --help)") from e',
       'raise SystemExit(f"veracium-mcp: failed to start: {e}\\n(Is ANTHROPIC_API_KEY set? Run veracium-mcp --help.)") from e')],
     [START_FAILURE], [HELP], None,
     "the key hint appended to every start failure, the schema refusal included (0031 v22.1's V-START-FAILURE RED)"),
]


def _noop(rel, anchor, cells):
    return (f"NOOP-{pathlib.Path(rel).stem}", rel, [(anchor, "# no-op control: a comment, no behaviour\n" + anchor)],
            sorted(set(cells)), f"a comment edit in {rel}: its mutants' cells must all pass", "SURVIVED")


def _cells_of(rel):
    return [c for m in MUTANTS if m[2] == rel for c in m[4]]


# (id, file, [(anchor, replacement)], named cells, what, the outcome the classifier must give)
CONTROLS = [
    _noop(K, "def _is_code_owned_empty(", _cells_of(K)),
    _noop(I, "    def _build_contested(", _cells_of(I)),
    _noop(V, "def _apply_statement_effect(", _cells_of(V)),
    _noop(D, "def convert_rows(", _cells_of(D)),
    _noop(M, "def _server_cls():", _cells_of(M)),
    _noop("src/veracium/store/sqlite.py", "    def delete_episode(", _cells_of("src/veracium/store/sqlite.py")),
    ("CTRL-unrelated-TypeError", K,
     [("    behind = store.store_version(user_id) - version_at_compile\n",
       '    raise TypeError("an unrelated execution failure (classifier negative control)")\n'
       "    behind = store.store_version(user_id) - version_at_compile\n")],
     [AFTER_BOUND], "an UNRELATED TypeError in needs_recompile: every cell fails for no reason a row names", "UNCLASSIFIED"),
]

SUBJECT_P = _protocol.Subject(
    spec="0003", finding=SUBJECT, table=TABLE, digested=DIGESTED, mutants=MUTANTS, controls=CONTROLS,
    import_modules=("veracium.compile", "veracium", "veracium.store.revocation", "veracium.store.data_migration",
                    "veracium.mcp_server"), import_specs=(), cells_files=(T, W, S), kinds=("product",))

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
