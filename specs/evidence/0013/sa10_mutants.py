#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0013_sa10_mutants.py::test_the_table_check_refuses_each_tampered_table
"""INV-SA10 — the gate's mutation table (0013 §5f.1; 0007 I2): each negative cell red against the gate mutant §5f.1
names beside it, and the gate's own checks each red against the mutant that removes them.

Three kinds of mutant, one protocol:
  GATE     an edit to the gate (sa10_gate.py) or its comparator (sa10_digest.py) that reintroduces the weaker design
           §5f.1's table names in its "gate mutant it kills" column (N1–N15), or removes one of the gate's own
           checks (I1's campaign, kept here so it is reproducible);
  TREE     an edit to the ladder (src/veracium/store/migration.py, release_migration.py) that INV-SA10's mutation row
           names: a write that maps to no step, the same write behind a condition no fixture satisfies, DDL from a
           site not declared to issue it, and a write added to a release_migration function (stage-1 decision 5);
  CONTROL  an unrelated TypeError, which the shared classifier must read UNCLASSIFIED, never KILLED.

The protocol is pa1_campaign.py's part (B), on a copy of the tracked tree (TMPDIR=/dev/shm recommended):
  CLEAN    every named cell and every honest probe passes on the unmutated copy, FIRST and again LAST (a campaign whose
           controls fail at either end measured nothing);
  per mutant: every anchor occurs EXACTLY ONCE in its file and the bytes change; the gate and the ladder still import
           from the copy; its HONEST probes pass (a kill only because the clean path broke is vacuous); its NAMED cells
           run under pytest with a JUnit record, each failing cell classified by specs/evidence/mutation_kinds.py;
           KILLED iff the classifier says so AND every named cell failed AND, where the row declares a REASON, that
           text is in a named cell's failure (a clean-ladder cell fails on ANY problem, so its kill is pinned to the
           problem the mutant must cause); the file is restored byte-identically.
THE PHRASE COMPLEMENT (`CARRIERS`, `carrier_problems()`; 0007's sa_mutants.py is the model): §5f.1's "gate mutant it
kills" column is read from the spec at run time and split by mutant; every phrase has exactly one carrier (a row of this
table, or ABSENT with a reason and a cell) and every carrier's phrase exists, so a named mutant with no row fails by
NAME in `--check`, `--write` and the table test, never by review.
`--check` is FAST and re-runs nothing: the phrase complement, definitions, anchors, digests, the named cells'
existence, every row good.
    $PY specs/evidence/0013/sa10_mutants.py --check
    $PY specs/evidence/0013/sa10_mutants.py --phrases      # each §5f.1 phrase and its carrier
    TMPDIR=/dev/shm $PY specs/evidence/0013/sa10_mutants.py --write
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import pathlib
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TABLE = HERE / "sa10" / "mutation-table.json"     # the name tests/test_closure_mutants.py finds
SELF = "specs/evidence/0013/sa10_mutants.py"
GATE = "specs/evidence/0013/sa10_gate.py"
DIGEST = "specs/evidence/0013/sa10_digest.py"
MIGRATION = "src/veracium/store/migration.py"
RELEASE = "src/veracium/store/release_migration.py"
CELLS_FILE = "tests/test_0013_sa10_gate.py"
KINDS = "specs/evidence/mutation_kinds.py"
DIGESTED = (GATE, DIGEST, MIGRATION, RELEASE, "src/veracium/store/schema_version.py", "specs/evidence/mutation_protocol.py",
            "specs/evidence/0013/pa1_campaign.py", "specs/evidence/0013/steptable.py", CELLS_FILE, KINDS, SELF)
SUBJECT = "INV-SA10"


sys.path.insert(0, str(HERE.parent))
import mutation_protocol as _protocol  # noqa: E402  (THE protocol; 0007 I6 factored it out of this file)

MK = _protocol.MK
_strict_pairs = _protocol._strict_pairs


C = lambda name: f"{CELLS_FILE}::{name}"                                     # noqa: E731
HARNESS = C("test_the_control_harness_is_green_without_a_channel[allowlist]")
ROUTE = lambda r: C(f"test_the_proxy_refuses_each_route_and_records_the_refusal[{r}]")           # noqa: E731
RULE = lambda i: C(f"test_each_classification_rule_refuses_its_case_and_admits_its_legitimate_one[{i}]")  # noqa: E731
FWD = lambda n: C(f"test_replay_equivalence_catches_each_unrecorded_route_with_the_allowlist_removed[{n}]")  # noqa: E731
ALW = lambda n: C(f"test_the_allowlist_refuses_each_connection_route_and_replay_still_sees_the_file_routes[{n}]")  # noqa: E731
N1315 = lambda n: C(f"test_n13_n15_a_zero_callback_channel_at_a_declared_site_is_refused[{n}]")  # noqa: E731
COMPARATOR = C("test_the_comparator_refuses_another_build_and_names_each_section")
PARAMS = C("test_parameters_are_recorded_by_value_and_replay_compares_every_outcome")
CLEAN_GATE = C("test_the_gate_passes_the_clean_ladder_on_every_path_and_entry")
RELEASE_SEAM = C("test_release_migration_opens_its_connections_through_the_seam")

_STAMP_REFUSE = ('        _refuse_unless(base, STEP_STAMP, [f"user_version reads {stamped}, not {SCHEMA_VERSION}"]\n'
                 '                       if stamped != SCHEMA_VERSION else [])\n')
_NO_OP_WRITE = '        conn.execute("UPDATE episodes SET json = json")\n'

# (id, kind, file, [(anchor, replacement)], named cells (EVERY one must fail), honest probes, reason or None, what)
MUTANTS = [
    # ---- the N-table's gate mutants (§5f.1; N13–N15 from stage-1 item 4) ------------------------------------------
    ("N1-site-admits-schema-writes", "gate", GATE,
     [("        if tc is None:\n            problems.append(f\"{where}: a schema write that is not class (a) or (b) by "
       "its text\")\n            cls = \"OUTSIDE\"\n        else:\n            cls = tc\n",
       "        if tc is None and not (rec.site is not None and (rec.site[0], rec.site[1]) in DDL_SITES):\n"
       "            problems.append(f\"{where}: a schema write that is not class (a) or (b) by its text\")\n"
       "            cls = \"OUTSIDE\"\n        else:\n            cls = tc or \"b1\"\n")],
     [C("test_n1_the_reviewers_drop_and_recreate_at_a_declared_site_is_refused"),
      C("test_n3_dropping_and_recreating_the_op_key_unique_index_is_refused_on_the_drop")], [HARNESS], None,
     "N1: class (b) decided by the site: every schema write at a declared site is admitted"),
    ("N2-b1-by-prefix", "gate", GATE,
     [('    return "a" if sql in alters else "b1" if sql in b1 else "b2" if sql in b2 else None',
       '    return "a" if sql in alters else "b1" if sql in b1 or (sql or "").startswith(("CREATE TABLE ", '
       '"CREATE INDEX ", "CREATE UNIQUE INDEX ")) else "b2" if sql in b2 else None')],
     [C("test_n2_a_count_preserving_rebuild_is_refused_statement_by_statement")], [HARNESS], None,
     "N2: (b1) matched by its prefix, not byte-equality to a head constructor"),
    ("N3-b2-every-index", "gate", GATE,
     [('    b2 = {f"DROP INDEX IF EXISTS {o.key[1]}" for o in head if o.key[0] == "index" and o.policy == '
       'sv.REBUILDABLE}', '    b2 = {f"DROP INDEX IF EXISTS {o.key[1]}" for o in head if o.key[0] == "index"}')],
     [C("test_n3_dropping_and_recreating_the_op_key_unique_index_is_refused_on_the_drop")], [HARNESS], None,
     "N3: (b2) widened from the rebuildable indexes to every index"),
    ("N4-N8-executescript-by-first-statement", "gate", GATE,
     [('               "close": lambda: census.call(cid, "close", None, None, real.close)}',
       '               "close": lambda: census.call(cid, "close", None, None, real.close),\n'
       '               "executescript": lambda script: census.call(cid, "execute", script.split(";")[0].strip(), (),\n'
       '                                                            lambda: real.executescript(script))}')],
     [C("test_n4_n8_a_script_on_the_ladders_connection_is_refused_outright[N4]"),
      C("test_n4_n8_a_script_on_the_ladders_connection_is_refused_outright[N8]"),
      ROUTE("connection.executescript")], [HARNESS], None,
     "N4/N8: executescript allowed, the script classified by its first statement"),
    ("N5-N10-constructor-assertion-dropped", "gate", GATE,
     [('    problems += [f"head constructor: {p}" for p in constructor_problems()]\n', "")],
     [C("test_n5_n10_a_head_constructor_that_is_not_a_plain_create_fails_the_gate[N5]"),
      C("test_n5_n10_a_head_constructor_that_is_not_a_plain_create_fails_the_gate[N10]")], [HARNESS], None,
     "N5/N10: the gate no longer asserts its head constructors are plain creates"),
    ("N6-N7-leading-keyword", "gate", GATE,
     [("    by_class = collections.defaultdict(list)\n",
       '    if label(rec.sql) == "READ":\n        return "read", problems\n'
       "    by_class = collections.defaultdict(list)\n")],
     [C("test_n6_a_comment_prefixed_drop_is_classified_by_its_actions"),
      C("test_n7_a_cte_prefixed_delete_at_no_step_is_refused")], [HARNESS], None,
     "N6/N7: a statement the prefix label calls a read is classified as a read"),
    ("N7-complement-over-labelled-DML", "gate", GATE,
     [("    if rows:\n", '    if rows and lab == "DML":\n')],
     [C("test_n7_a_cte_prefixed_delete_at_no_step_is_refused")], [HARNESS], None,
     "N7: the write complement runs over labelled DML only"),
    ("N9-every-pragma-reads", "gate", GATE,
     [("        if PRAGMA_READS.get(name) != shape or shape is None:\n", "        if False:\n")],
     [C("test_n9_writable_schema_at_a_declared_site_is_off_the_pragma_vocabulary"), RULE(8)], [HARNESS], None,
     "N9: every pragma other than the stamp is a read"),
    ("N11-orphans-skipped", "gate", GATE,
     [('    problems += [f"orphan {k} on connection {cid}: {str(x)[:100]}" for k, cid, x in census.orphans]\n', "")],
     [C("test_n11_a_statement_around_the_proxy_is_an_orphan")], [HARNESS], None,
     "N11: the orphan check skipped"),
    ("N12-schema-table-write-reads", "gate", GATE,
     [("    if book and not schema:\n", "    if False:\n")],
     [C("test_n12_setconfig_writable_schema_then_a_schema_table_delete_is_refused_twice_over"), RULE(6)], [HARNESS],
     None, "N12: a write to sqlite_master alone is classified as a read"),
    ("N12-getconfig-dropped", "gate", GATE,
     [("        if ws:\n", "        if False:\n")],
     [C("test_n12_setconfig_writable_schema_then_a_schema_table_delete_is_refused_twice_over"),
      C("test_the_configuration_guard_sees_setconfig_which_no_statement_shows")], [HARNESS], None,
     "N12: the getconfig assertion after every call dropped"),
    ("N13-N15-forward-unknown-attributes", "gate", GATE,
     [('            raise census.refuse(f"connection.{n}")', "            return getattr(real, n)")],
     [N1315("N13 blobopen"), N1315("N14 backup into the connection"),
      N1315("N15 set_authorizer(None), then DELETE"), ROUTE("connection.blobopen"), ROUTE("connection.backup"),
      ROUTE("connection.set_authorizer")], [HARNESS], None,
     "N13–N15: the connection proxy forwards every name it does not list to the real connection"),
    ("W3-allowlist-in-getattr", "gate", GATE,
     [("        __slots__ = ()\n\n        def __getattribute__(self, n):\n            f = methods.get(n)",
       "        def __getattr__(self, n):\n            f = methods.get(n)"),
      ("    return ConnectionProxy()\n",
       "    proxy = ConnectionProxy()\n    object.__setattr__(proxy, \"_real\", real)\n    return proxy\n")],
     [ROUTE("connection._real"), ROUTE("connection.__dict__")], [HARNESS], None,
     "stage-1 4(g): the superseded shape, the allowlist in __getattr__ with the real connection an instance "
     "attribute, so a name the object HAS (`_real`, `__dict__`) never reaches the allowlist"),
    ("W3-setattr-forwards", "gate", GATE,
     [("            if n not in CONN_SET_ATTRS:\n                raise census.refuse(f\"setting connection.{n}\")",
       "            if False:\n                raise census.refuse(f\"setting connection.{n}\")")],
     [ROUTE("setting connection._real"), ROUTE("setting connection.autocommit")], [HARNESS], None,
     "the proxy's __setattr__ forwards every name to the real connection: setting `_real` or `autocommit` is admitted"),
    ("enter-returns-real", "gate", GATE,
     [("        def __enter__(self):\n            return self", "        def __enter__(self):\n            return real")],
     [ROUTE("connection.blobopen (through with)")], [HARNESS], None,
     "stage-1 4(f): `with conn as c` binds the real connection"),
    ("execute-returns-real-cursor", "gate", GATE,
     [("        return cursor_proxy(cur, census, census.events[-1])\n\n    def executemany",
       "        return cur\n\n    def executemany")],
     [ROUTE("cursor.connection"), C("test_execute_hands_back_the_cursor_wrapper_never_the_real_cursor")], [HARNESS],
     None, "stage-1 4(f): execute returns the real cursor, whose .connection is the real connection"),
    ("cursor-iter-returns-real", "gate", GATE,
     [("        def __iter__(self):\n            return self", "        def __iter__(self):\n            return iter(cur)")],
     [ROUTE("cursor.connection (through iter)")], [HARNESS], None,
     "stage-1 4(f) note: iter() of the cursor wrapper is the real cursor"),
    # ---- the gate's own checks (I1's campaign) -------------------------------------------------------------------
    ("digest-rowid-only", "gate", DIGEST,
     [('            cols = [r[0] for r in con.execute("SELECT name FROM pragma_table_xinfo(?)", (name,))]\n'
       "            if not cols:",
       '            cols = [r[1] for r in con.execute(f"SELECT * FROM pragma_table_xinfo({_q(name)!r})")]\n'
       "            if False:")],
     [COMPARATOR], [HARNESS], None, "the comparator's column lookup misses every table: rows digest as rowids"),
    ("digest-no-typeof", "gate", DIGEST,
     [('sel = ", ".join(f"typeof({_q(c)}), {_q(c)}" for c in cols)', 'sel = ", ".join(f"{_q(c)}" for c in cols)')],
     [COMPARATOR], [HARNESS], None, "the comparator digests values without their storage class"),
    ("digest-rootpage", "gate", DIGEST,
     [('        sections = {"schema": _h(schema)}',
       '        sections = {"schema": _h(schema + con.execute("SELECT rootpage FROM sqlite_schema ORDER BY type, name, '
       'tbl_name, sql").fetchall())}')],
     [COMPARATOR], [HARNESS], None, "the comparator digests physical placement (rootpage) with the schema rows"),
    ("digest-build-unasserted", "gate", DIGEST,
     [("        if (version, source) != (want_version, want_source):", "        if False:")],
     [COMPARATOR], [HARNESS], None, "the comparator does not assert the census's SQLite build"),
    ("integrity-unasserted", "gate", GATE,
     [('    if real["integrity"] != ["ok"]:', "    if False:")],
     [FWD("raw file I/O corrupting only an index page"), ALW("raw file I/O corrupting only an index page")],
     [HARNESS], None, "integrity_check on the census file is not asserted"),
    ("replay-replays-nothing", "gate", GATE,
     [('    for ev in events:\n        if ev.kind == "connect-failed":',
       '    for ev in []:\n        if ev.kind == "connect-failed":')],
     [PARAMS], [ROUTE("connection.blobopen")], None, "replay re-runs nothing"),
    ("replay-ignores-outcomes", "gate", GATE,
     [("        if out != ev.outcome:", "        if False:")],
     [PARAMS], [HARNESS], None, "replay does not compare each call's outcome"),
    ("params-by-reference", "gate", GATE,
     [("        out = tuple(params)", "        out = params")],
     [PARAMS], [HARNESS], None, "parameters recorded by reference: a later mutation reaches the replay"),
    ("heartbeat-off", "gate", GATE,
     [('    if rec.outcome == ("ok",):\n        if not rec.traces:', '    if False:\n        if not rec.traces:')],
     [C("test_the_heartbeat_refuses_a_call_that_ran_with_the_instrument_removed"),
      FWD("set_authorizer(None), then a DELETE through execute")], [HARNESS], None,
     "a call that ran untraced and unauthorized is not refused"),
    ("type-check-off", "gate", GATE,
     [("        if isinstance(value, _FORBIDDEN_RETURN):\n            raise", "        if False:\n            raise")],
     [C("test_no_allowed_name_hands_back_a_real_connection_cursor_or_blob")], [HARNESS], None,
     "an allowed name may hand back a real Connection, Cursor or Blob"),
    ("site-coverage-blind", "gate", GATE,
     [("            if not any(lo <= ln <= hi for ln in lines):", "            if False:")],
     [C("test_site_coverage_reports_an_unobserved_site_in_a_function_the_census_entered")], [HARNESS], None,
     "site coverage reports no unobserved site"),
    ("cross-connection-callbacks-admitted", "gate", GATE,
     [('            if cur is None or cur.cid != cid:\n                self.orphans.append(("auth"',
       '            if cur is None:\n                self.orphans.append(("auth"')],
     [C("test_an_orphan_callback_and_a_cross_connection_callback_are_refusals")], [HARNESS], None,
     "an authorizer callback from another connection is attributed to the current call"),
    ("unknown-code-reads", "gate", GATE,
     [('cls = CODE_CLASS.get(a[0], "unknown")', 'cls = CODE_CLASS.get(a[0], "read")')],
     [C("test_the_action_table_is_a_closed_partition_of_the_33_codes_and_any_other_code_refuses")], [HARNESS], None,
     "an action code outside the closed table reads as a read"),
    ("c2-c3-not-required", "gate", GATE,
     [('        if c2 is None or c2["b2_with_drop_index"] < 1:', "        if False:")],
     [C("test_a_narrowed_path_set_refuses_loudly")], [HARNESS], None,
     "a gate run with no real (b2) observed passes"),
    ("stamp-value-unchecked", "gate", GATE,
     [("            if arg != str(head):", "            if False:")],
     [RULE(13)], [HARNESS], None, "a stamp below the head is admitted"),
    ("ddl-site-ignored", "gate", GATE,
     [("        if rec.site is None or (rec.site[0], rec.site[1]) not in DDL_SITES:", "        if False:")],
     [RULE(2)], [HARNESS], None, "a schema write from an undeclared site is admitted"),
    ("seam-skips-release-migration", "gate", GATE,
     [("    mig.sqlite3 = rm.sqlite3 = seam", "    mig.sqlite3 = seam")],
     [RELEASE_SEAM], [HARNESS], None, "release_migration's own connections bypass the seam"),
    ("exact-one-relaxed", "gate", GATE,
     [("        if len(hits) != 1:", "        if not hits:")],
     [C("test_a_row_write_two_steps_both_claim_is_refused")], [HARNESS], None,
     "a row write two steps' matchers both claim is admitted (exact-one ownership)"),
    ("per-call-trace-count", "gate", GATE,
     [("        if not rec.traces:\n",
       "        if len(rec.traces) > 1:\n            problems.append(f\"{where}: the call traced more than once\")\n"
       "        if not rec.traces:\n")],
     [C("test_the_clean_control_admits_a_call_whose_nested_pragma_traces_twice")], [ROUTE("connection.blobopen")],
     "the call traced more than once", "§5f.1 rule 3: a per-call trace count refuses the nested table-valued pragma"),
    # ---- tree mutants: the ladder (INV-SA10's mutation row; stage-1 decision 5) ----------------------------------
    ("tree-unmapped-write", "tree", MIGRATION,
     [(_STAMP_REFUSE, _STAMP_REFUSE + _NO_OP_WRITE)],
     [HARNESS], [ROUTE("connection.blobopen")], "a row write on ['episodes'] maps to 0 steps",
     "a ladder write that maps to no step, after the stamp postcondition"),
    ("tree-unreached-write", "tree", MIGRATION,
     [(_STAMP_REFUSE, _STAMP_REFUSE + "        if base == -1:\n    " + _NO_OP_WRITE)],
     [CLEAN_GATE], [HARNESS], "site never observed on any path: veracium/store/migration.py:_apply_forward:",
     "the same write behind a condition no fixture satisfies (dev's mutant2-conditional): the site check alone"),
    ("tree-undeclared-ddl", "tree", MIGRATION,
     [('    conn.execute("DELETE FROM wiki")\n',
       '    conn.execute("DROP INDEX IF EXISTS ix_episodes_user")\n'
       '    conn.execute("CREATE INDEX ix_episodes_user ON episodes(user_id, date)")\n'
       '    conn.execute("DELETE FROM wiki")\n')],
     [HARNESS], [ROUTE("connection.blobopen")], "a schema write from a site not declared to issue DDL",
     "(b2) and (b1) texts issued from _drop_wiki_cache, a site not declared to issue DDL"),
    ("tree-release-migration-write", "tree", RELEASE,
     [('            found = conn.execute("PRAGMA user_version").fetchone()[0]\n',
       '            found = conn.execute("PRAGMA user_version").fetchone()[0]\n'
       '            conn.execute("UPDATE episodes SET json = json")\n')],
     [RELEASE_SEAM], [HARNESS], "veracium/store/release_migration.py:_observe:",
     "a write added to release_migration's _observe, inside its BEGIN IMMEDIATE ... ROLLBACK"),
]

_CONNECT = "    conn = sqlite3.connect(path)\n"
_FACTORY = ("class _ReviewerFactory(sqlite3.Connection):\n    def __init__(self, *a, **k):\n        super().__init__(*a, **k)\n"
            "        self.execute(\"UPDATE episodes SET json = json_set(json, '$.summary', 'factory mutation')\")\n"
            "        self.commit()\n\n\n")
_CF = lambda f: C(f"test_connect_refuses_a_factory_or_any_extra_argument_before_anything_runs[{f}]")      # noqa: E731
_SETV = lambda i: C(f"test_a_settable_attribute_takes_only_its_closed_values[{i}]")                         # noqa: E731
_RPL = lambda f: C(f"test_replay_never_runs_recorded_caller_behaviour[{f}]")                                # noqa: E731
_SEAM = C("test_the_module_seam_exposes_connect_and_what_the_ladder_reads_and_nothing_else")
MUTANTS += [
    # ---- 0007 round 3, SA-R3-01 and research's stage-1 read: caller-supplied connection behaviour -------------------
    # TREE: the reviewer's product mutation and its siblings, each refused across the COMPLETE gate (the closure's words)
    ("tree-connect-factory-keyword", "tree", MIGRATION,
     [("def migrate_store(path: str, *,", _FACTORY + "def migrate_store(path: str, *,"),
      (_CONNECT, "    conn = sqlite3.connect(path, factory=_ReviewerFactory)\n")],
     [CLEAN_GATE], [ROUTE("connection.blobopen")], "refused connect with the keyword argument(s) ['factory']",
     "SA-R3-01, the reviewer's mutation: migrate_store's connection is a Connection subclass whose constructor "
     "updates an episode summary and commits, before the authorizer and trace exist"),
    ("tree-connect-factory-positional", "tree", MIGRATION,
     [("def migrate_store(path: str, *,", _FACTORY + "def migrate_store(path: str, *,"),
      (_CONNECT, "    conn = sqlite3.connect(path, 5.0, 0, None, True, _ReviewerFactory)\n")],
     [CLEAN_GATE], [ROUTE("connection.blobopen")], "refused connect with 5 positional argument(s)",
     "SA-R3-01: the same factory passed positionally"),
    ("tree-direct-connection", "tree", MIGRATION,
     [(_CONNECT, "    _w = sqlite3.Connection(path)\n"
                 "    _w.execute(\"UPDATE episodes SET json = json_set(json, '$.summary', 'direct')\")\n"
                 "    _w.commit()\n    _w.close()\n" + _CONNECT)],
     [CLEAN_GATE], [ROUTE("connection.blobopen")], "refused sqlite3.Connection through the module seam",
     "research's stage-1 read: a connection constructed directly through the seam, with no connect at all"),
    ("tree-row-factory-function", "tree", MIGRATION,
     [(_CONNECT, _CONNECT + "    conn.row_factory = lambda cur, row: row\n")],
     [CLEAN_GATE], [ROUTE("connection.blobopen")], "refused setting connection.row_factory to",
     "research's stage-1 read: a Python row factory, caller code that replay would re-run"),
    ("tree-text-factory-function", "tree", MIGRATION,
     [(_CONNECT, _CONNECT + "    conn.text_factory = lambda b: b.decode()\n")],
     [CLEAN_GATE], [ROUTE("connection.blobopen")], "refused setting connection.text_factory to",
     "research's stage-1 read: a Python text factory, likewise"),
    # GATE: each new check removed, each killed by its own cells
    ("sa-r3-01-connect-forwards-the-callers-arguments", "gate", GATE,
     [('        bad = connect_args_problem(args, kw)\n        if bad:                                   # SA-R3-01: '
       'before sqlite3.connect, so no factory ever runs\n            raise self.refuse(f"connect with {bad}", site)\n', "")],
     [_CF("factory-keyword"), _CF("factory-positional")], [_SETV("row_factory-Row")], None,
     "the shipped connect: the caller's arguments, factory included, reach sqlite3.connect"),
    ("sa-r3-01-the-seam-forwards-the-module", "gate", GATE,
     [('        if n in SEAM_ATTRS:\n            return getattr(sqlite3, n)\n'
       '        raise self._census.refuse(f"sqlite3.{n} through the module seam")\n', "        return getattr(sqlite3, n)\n")],
     [_SEAM], [_CF("factory-keyword")], None, "the shipped seam: every sqlite3 attribute but connect forwarded"),
    ("sa-r3-01-set-values-unchecked", "gate", GATE,
     [("            if not set_value_ok(n, v):\n", "            if False:\n")],
     [_SETV("row_factory-function"), _SETV("text_factory-function")], [_SETV("row_factory-Row")], None,
     "a settable attribute takes any value, a Python factory included"),
    ("sa-r3-01-replay-runs-recorded-behaviour", "gate", GATE,
     [("            bad = connect_args_problem(ev.args, kw)\n            if bad:                               # SA-R3-01: "
       "replay never runs recorded caller behaviour\n", "            bad = None\n            if bad:\n"),
      ("            if ev.name not in CONN_SET_ATTRS or not set_value_ok(ev.name, ev.value):\n", "            if False:\n")],
     [_RPL("connect-factory"), _RPL("set-function")], [PARAMS], None,
     "replay re-runs a recorded connect's arguments and a recorded set's value"),
]

MUTANTS += [
    # ---- 0013 v37 §5f.1: the pre-3.41 declare_vtab sequence (Quentin, 2026-10-27: "Yes, build v37") -----------------
    ("v37-filter-without-the-probe", "gate", GATE,
     [("        if not first or not declare_vtab_probe():\n", "        if not first:\n")],
     [C("test_the_declare_vtab_sequence_is_a_write_on_a_build_whose_probe_does_not_reproduce")], [], None,
     "v37: the sequence attributed on a build whose own probe does not reproduce it"),
    # one mutant, all four variants: the window's callback CODES drawn from the sequence's (UPDATE, READ), arguments
    # and order unchecked. The superseded definition compared the codes as a tuple, which a sixth UPDATE column
    # still fails (six UPDATEs are not five and a READ), so it could not fail the [sixth-column] cell.
    ("v37-a-loose-sequence", "gate", GATE,
     [("                if (a[0] == sqlite3.SQLITE_SELECT and tuple(rec.acts[i + 1:i + 1 + n]) == DECLARE_VTAB_SEQ\n",
       "                if (a[0] == sqlite3.SQLITE_SELECT and {x[0] for x in rec.acts[i + 1:i + 1 + n]}\n"
       "                        <= {x[0] for x in DECLARE_VTAB_SEQ}\n")],
     [C("test_a_variant_of_the_declare_vtab_sequence_stays_a_write[sixth-column]"),
      C("test_a_variant_of_the_declare_vtab_sequence_stays_a_write[another-table]"),
      C("test_a_variant_of_the_declare_vtab_sequence_stays_a_write[another-database]"),
      C("test_a_variant_of_the_declare_vtab_sequence_stays_a_write[trigger-argument]")], [], None,
     "v37: a loose sequence (callback codes only, from UPDATE/READ) accepts a sixth column, another table, another "
     "database or a trigger argument"),
    ("v37-a-second-use", "gate", GATE,
     [("        first = mods - self.vtab_used[cid]\n", "        first = mods\n")],
     [C("test_the_declare_vtab_sequence_is_bookkeeping_only_on_a_connections_first_use")], [], None,
     "v37: the sequence accepted on a second use on one connection"),
    ("v37-outside-a-prepare", "gate", GATE,
     [("\n                        and all(p == 0 for p in rec.act_phase[i + 1:i + 1 + n])):", "):")],
     [C("test_the_declare_vtab_sequence_outside_a_prepare_stays_a_write")], [], None,
     "v37: the sequence accepted outside a prepare"),
    ("v37-no-change-dropped", "gate", GATE,
     [("    return reproduces and before == after\n", "    return reproduces\n")],
     [C("test_the_declare_vtab_probe_needs_the_exact_sequence_and_no_change")], [], None,
     "v37: the probe's no-change check dropped"),
]

MUTANTS += [
    # ---- §5f.1's named mutants no row carried until the phrase complement below (CARRIERS) found them ---------------
    ("N2-row-count-postcondition", "gate", GATE,
     [('    problems += [f"orphan {k} on connection {cid}: {str(x)[:100]}" for k, cid, x in census.orphans]\n',
       "    def _counts(p):\n"
       "        with contextlib.closing(sqlite3.connect(p)) as c:\n"
       "            return {t: c.execute(f'SELECT count(*) FROM \"{t}\"').fetchone()[0] for (t,) in c.execute(\n"
       "                \"SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'\").fetchall()}\n"
       "    named = {a[2] if a[0] == sqlite3.SQLITE_ALTER_TABLE else a[1] for rec in calls if rec.cls == \"OUTSIDE\"\n"
       "             for a in rec.acts if CODE_CLASS.get(a[0]) == \"schema\"}\n"
       "    before, after = _counts(pre), _counts(store)\n"
       "    if all(before[t] == after[t] for t in named if t in before and t in after):\n"
       "        problems = [p for p in problems if not p.endswith(\"a schema write that is not class (a) or (b) by its "
       "text\")]\n"
       '    problems += [f"orphan {k} on connection {cid}: {str(x)[:100]}" for k, cid, x in census.orphans]\n')],
     [C("test_n2_a_count_preserving_rebuild_is_refused_statement_by_statement")], [HARNESS], None,
     "N2: a row-count postcondition in place of the list: a schema write outside the text classes is admitted when "
     "every table the outside writes name keeps, over the path, the row count it had before"),
    ("N11-attribute-by-trace-sequence", "gate", GATE,
     [("        def auth(code, a1, a2, db, trig):\n            cur = self.cur\n",
       "        def auth(code, a1, a2, db, trig):\n            cur = self.cur or getattr(self, \"last_traced\", None)\n"),
      ("        def trace(text):\n            cur = self.cur\n",
       "        def trace(text):\n            cur = self.cur or getattr(self, \"last_traced\", None)\n"),
      ("                cur.traces.append(text)\n",
       "                cur.traces.append(text)\n                self.last_traced = cur\n")],
     [C("test_n11_a_statement_around_the_proxy_is_an_orphan")], [HARNESS], None,
     "N11: actions attributed by trace sequence: a callback that arrives while no proxied call runs joins the call "
     "that traced last (on its connection), instead of being an orphan"),
    ("C2-fixture-out-of-scope", "gate", GATE,
     [('    out = [(lab, "migrate_store", lambda p, lab=lab: (_clear(p), pa1.fresh_fixture(p, lab))) for lab in labels]\n'
       '    for mode, c in (("wrong", "C2"), ("missing", "C3")):\n',
       '    out = [(lab, "migrate_store", lambda p, lab=lab: (_clear(p), pa1.fresh_fixture(p, lab))) for lab in labels]\n'
       '    for mode, c in (("missing", "C3"),):\n'),
      ('            out.append((lab, "release", lambda p, lab=lab: (_clear(p), pa1.fresh_fixture(p, lab))))\n'
       '    for mode, c in (("wrong", "C2"), ("missing", "C3")):\n',
       '            out.append((lab, "release", lambda p, lab=lab: (_clear(p), pa1.fresh_fixture(p, lab))))\n'
       '    for mode, c in (("missing", "C3"),):\n')],
     [CLEAN_GATE], [HARNESS], "C2: no (b2) statement carrying a DROP_INDEX action was observed",
     "C2: a gate with no C2 fixture (`wrong`) in scope, on either entry: the clean ladder then fails as no (b2) "
     "observed"),
    ("C3-refuse-every-disagreement", "gate", GATE,
     [('        if lab == "DDL" and cls == "read" and not rec.acts and tc == "b2":\n', "        if False:\n")],
     [CLEAN_GATE, RULE(22)], [HARNESS], "C3-missing: execute 'DROP INDEX IF EXISTS ",
     "C3: every label/SQLite disagreement refused in both directions (rule 6's one exception, the (b2) no-op of an "
     "index already absent, dropped): the clean ladder's C3 path refuses"),
    # ---- I1: the pragma vocabulary is frozen by name AND argument shape (rule 5); N9's row admits every pragma ----
    ("I1-pragma-unlisted-name-reads", "gate", GATE,
     [("        if PRAGMA_READS.get(name) != shape or shape is None:\n",
       "        if PRAGMA_READS.get(name, shape) != shape or shape is None:\n")],
     [C("test_n9_writable_schema_at_a_declared_site_is_off_the_pragma_vocabulary"), RULE(8), RULE(11)], [HARNESS],
     None, "I1: a pragma name off the list is a read when its argument has a well-formed shape (the shape still "
           "checked for a listed name)"),
    ("I1-pragma-another-shape-reads", "gate", GATE,
     [("        if PRAGMA_READS.get(name) != shape or shape is None:\n",
       "        if name not in PRAGMA_READS or shape is None:\n")],
     [RULE(25)], [HARNESS], None,
     "I1: a listed pragma is a read with any well-formed argument shape (the vocabulary frozen by name only)"),
]

# ---- I1's clauses with a cell and no NAMED mutant (research's stage-1 read of the round-3 drafts): each is
# demonstrated red anyway, so "implement X" never rests on a cell nobody has shown failing ------------------------------
MUTANTS += [
    ("I1-a-listed-code-reclassed", "gate", GATE,
     [('    "SQLITE_ATTACH": "refused", "SQLITE_DETACH": "refused",', '    "SQLITE_ATTACH": "read", "SQLITE_DETACH": "refused",')],
     [C("test_the_action_table_is_a_closed_partition_of_the_33_codes_and_any_other_code_refuses"), RULE(15)], [HARNESS],
     None, "I1: a listed code (ATTACH) re-classed from refused to read in the closed table"),
    ("I1-schema-branch-only", "gate", GATE,
     [('    rows = [a for a in by_class["row"] if a[1] not in SCHEMA_TABLE_NAMES]\n',
       '    rows = [] if by_class["schema"] else [a for a in by_class["row"] if a[1] not in SCHEMA_TABLE_NAMES]\n')],
     [RULE(5)], [HARNESS], None,
     "I1: a call with both effects evaluated by its schema branch only (its row writes dropped)"),
    # NO honest probe, by necessity: with the cache on, a repeated statement's PREPARE gives no authorizer callback, so
    # the heartbeat (rule 7) refuses the CLEAN ladder too (measured: the harness probe fails under this mutant). The
    # named cell carries its own control (Python's default cache, no second callback), so the kill is not vacuous.
    ("I1-statement-cache-left-on", "gate", GATE,
     [('        kw2["cached_statements"] = 0\n', "")],
     [C("test_the_census_disables_the_statement_cache")], [], None,
     "I1: the census leaves the statement cache at its default (a cached PREPARE gives no authorizer callback)"),
    ("I1-reindex-paired-by-any-create-index", "gate", GATE,
     [("        if a[1] not in made:\n", "        if not made:\n")],
     [RULE(26)], [HARNESS], None,
     "I1: REINDEX paired with ANY CREATE_INDEX in the call, not the one of its name"),
]

# (id, file, [(anchor, replacement)], named cells, what, the outcome the classifier must give)
CONTROLS = [
    ("CTRL-unrelated-TypeError", GATE,
     [("def text_classes():\n", "def text_classes():\n"
       '    raise TypeError("an unrelated execution failure (classifier negative control)")\n')],
     [C("test_n1_the_reviewers_drop_and_recreate_at_a_declared_site_is_refused"), HARNESS],
     "an UNRELATED TypeError in the gate's text classes: every path raises for no reason a cell names",
     "UNCLASSIFIED"),
]


SUBJECT_P = _protocol.Subject(
    spec="0013", finding=SUBJECT, table=TABLE, digested=DIGESTED, mutants=MUTANTS, controls=CONTROLS,
    import_modules=("veracium.store.migration", "veracium.store.release_migration"),
    import_specs=("specs/evidence/0013/sa10_gate.py",), cells_files=(CELLS_FILE,), kinds=("gate", "tree"))
"""INV-SA10's subject: its data, run by the shared protocol (specs/evidence/mutation_protocol.py)."""

definition_sha = _protocol.definition_sha
canonical = _protocol.canonical
render = _protocol.render
named_cells = SUBJECT_P.named_cells
honest_nodes = SUBJECT_P.honest_nodes
_digests = SUBJECT_P.digests
campaign = SUBJECT_P.campaign


def defined_tests(root: pathlib.Path = ROOT) -> set:
    """The bare test names in CELLS_FILE (this module's callers read names, not `file::name`)."""
    return {n.split("::")[1] for n in SUBJECT_P.defined_tests(root)}


# ---- the phrase complement: §5f.1's "gate mutant it kills" column, read from the spec at run time -----------------------
# 0007's sa_mutants.py `phrases()` / `CARRIERS` / `carrier_problems()` is the model. A phrase is ONE named mutant: the
# column's cell, cut at its first sentence end (C2's cell goes on to explain the step table's fixture), version markers
# stripped, split at parenthesis depth 0 on "; ", ", or " and " or " (never on " and ": N4's "allow `executescript` and
# classify the script by its first statement" is one edit). Keyed by (row, phrase TEXT), so a reworded, added, removed
# or reordered phrase fails by name in both directions; an index key would let a reorder pass silently.
#   "—"         no mutant (C1, the control the census itself is): the row yields no phrase, and any other empty cell
#               is a problem;
#   "the same"  N7's first half, N14 and N15: the PREVIOUS row's mutant. It stays its own phrase (the row's cell must
#               still be demonstrated against it), its text names the referent, and its carrier MUST equal the
#               referent's carrier (it is the same edit). A "the same" whose previous row has more than one phrase is
#               ambiguous and refuses.
SPEC = "specs/0013-store-migrations.md"
TABLE_HEADER = "| # | cell | expected | gate mutant it kills |"
NO_MUTANT = "—"
SAME = "the same"
_SEPS = ("; ", ", or ", " or ")                      # ", or " before " or ": the comma is consumed with its separator
_MARKER = re.compile(r"\*\*\((?:v[0-9.]+)\)\*\*\s*")


def _split_depth0(text: str) -> list:
    """`text` split on _SEPS at parenthesis depth 0. Unbalanced parentheses raise (a phrase would be cut wrongly)."""
    out, cur, depth, i = [], [], 0, 0
    while i < len(text):
        if depth == 0:
            sep = next((s for s in _SEPS if text.startswith(s, i)), None)
            if sep is not None:
                out.append("".join(cur))
                cur, i = [], i + len(sep)
                continue
        ch = text[i]
        depth += (ch == "(") - (ch == ")")
        if depth < 0:
            raise ValueError(f"unbalanced ')' at {i} in {text!r}")
        cur.append(ch)
        i += 1
    if depth != 0:
        raise ValueError(f"unbalanced '(' in {text!r}")
    out.append("".join(cur))
    return out


def _first_sentence(text: str) -> str:
    depth = 0
    for i, ch in enumerate(text):
        depth += (ch == "(") - (ch == ")")
        if ch == "." and depth == 0 and text[i + 1:i + 2] == " " and text[i + 2:i + 3].isupper():
            return text[:i]
    return text


def section_rows(root: pathlib.Path = ROOT) -> list:
    """[(row id, the "gate mutant it kills" cell)] of §5f.1's negative-cell table, in order. Refuses (ValueError) a
    missing or repeated header, a row that is not exactly four cells, or a table with no rows."""
    lines = (root / SPEC).read_text(encoding="utf-8").splitlines()
    at = [i for i, ln in enumerate(lines) if ln.strip() == TABLE_HEADER]
    if len(at) != 1:
        raise ValueError(f"{SPEC}: the §5f.1 header {TABLE_HEADER!r} occurs {len(at)} time(s), not once")
    body = lines[at[0] + 1:]
    if not body or not re.fullmatch(r"\|(-+\|){4}", body[0].strip()):
        raise ValueError(f"{SPEC}: the §5f.1 header is not followed by its |---| separator")
    rows = []
    for ln in body[1:]:
        if not ln.strip().startswith("|"):
            break
        cells = [c.strip() for c in ln.strip().split("|")]
        if len(cells) != 6 or cells[0] or cells[-1] or not re.fullmatch(r"[A-Z]\d+", cells[1]):
            raise ValueError(f"{SPEC}: a §5f.1 table row is not `| id | cell | expected | mutant |`: {ln[:100]!r}")
        rows.append((cells[1], cells[4]))
    if not rows:
        raise ValueError(f"{SPEC}: the §5f.1 table has no rows")
    return rows


def phrases(root: pathlib.Path = ROOT) -> dict:
    """{(row, phrase): referent}: every named mutant of §5f.1's table. `referent` is None for a phrase of its own row,
    else (the previous row, its phrase) for a "the same", resolved through a chain (N15 -> N14 -> N13)."""
    out, prev, seen = {}, None, set()
    for row, cell in section_rows(root):
        if row in seen:
            raise ValueError(f"§5f.1 row {row} occurs twice")
        seen.add(row)
        text = _MARKER.sub("", _first_sentence(cell)).strip()
        mine = []
        if text != NO_MUTANT:
            for p in (q.strip() for q in _split_depth0(text)):
                if not p:
                    raise ValueError(f"§5f.1 row {row}: an empty phrase in {text!r}")
                if p == SAME:
                    if prev is None or len(prev[1]) != 1:
                        raise ValueError(f"§5f.1 row {row}: 'the same' needs a previous row with exactly one phrase")
                    (pk, pref), = prev[1]
                    ref = pref or pk
                    out[(row, p)] = ref
                else:
                    out[(row, p)] = None
                mine.append(((row, p), out[(row, p)]))
        prev = (row, mine)
    return out


CARRIERS = {
    # (row, phrase) -> ("mutant", id) | ("absent", reason, cell). Several phrases share ONE row only where one edit
    # genuinely realises each of them; each share is justified beside it.
    ("N1", "admit every statement at a declared class-(b) site"): ("mutant", "N1-site-admits-schema-writes"),
    ("N2", "match (b1) by prefix rather than byte-equality"): ("mutant", "N2-b1-by-prefix"),
    ("N2", "a row-count postcondition in place of the list"): ("mutant", "N2-row-count-postcondition"),
    ("N3", "widen (b2) to every index"): ("mutant", "N3-b2-every-index"),
    # SHARED (N4, N8): the one edit is "executescript allowed, the script classified by its first statement"; N8's
    # phrase is the second half of N4's, and no gate can classify a script it does not allow
    ("N4", "allow `executescript` and classify the script by its first statement"):
        ("mutant", "N4-N8-executescript-by-first-statement"),
    ("N8", "classify a script by its first statement"): ("mutant", "N4-N8-executescript-by-first-statement"),
    # SHARED (N5, N10): both are "drop the assertion", the same constructor assertion; N10's parenthesis says what its
    # absence costs, not a second edit
    ("N5", "drop the assertion"): ("mutant", "N5-N10-constructor-assertion-dropped"),
    ("N10", "drop the assertion (a recreate of an existing name becomes a silent no-op, a second legitimate-looking "
            "no-op beside (b2)'s)"): ("mutant", "N5-N10-constructor-assertion-dropped"),
    # SHARED (N6, N7 "the same"): the spec says it is the same mutant; the row names both cells
    ("N6", "classify by the leading keyword"): ("mutant", "N6-N7-leading-keyword"),
    ("N7", "the same"): ("mutant", "N6-N7-leading-keyword"),
    ("N7", "a write complement over labelled DML only"): ("mutant", "N7-complement-over-labelled-DML"),
    ("N9", "treat every pragma other than the stamp as a read"): ("mutant", "N9-every-pragma-reads"),
    ("N11", "attribute actions by trace sequence"): ("mutant", "N11-attribute-by-trace-sequence"),
    ("N11", "skip the orphan check"): ("mutant", "N11-orphans-skipped"),
    ("N12", "classify a `sqlite_master`-only write as a read"): ("mutant", "N12-schema-table-write-reads"),
    ("N12", "drop the `getconfig` assertion"): ("mutant", "N12-getconfig-dropped"),
    # SHARED (N13, N14 and N15 "the same"): the spec says it is the same mutant; the row names all three cases
    ("N13", "forward every name the proxy does not list to the real connection"):
        ("mutant", "N13-N15-forward-unknown-attributes"),
    ("N14", "the same"): ("mutant", "N13-N15-forward-unknown-attributes"),
    ("N15", "the same"): ("mutant", "N13-N15-forward-unknown-attributes"),
    ("W1", "`__enter__` returns the real connection's `__enter__()`"): ("mutant", "enter-returns-real"),
    ("W2", "`execute` returns the real cursor"): ("mutant", "execute-returns-real-cursor"),
    ("W2", "the wrapper's `__iter__` returns the real cursor"): ("mutant", "cursor-iter-returns-real"),
    ("W3", "the allowlist written in `__getattr__`, with the real connection stored as an instance attribute (Python "
           "consults `__getattr__` only for a name the object lacks)"): ("mutant", "W3-allowlist-in-getattr"),
    ("W3", "a `__setattr__` that forwards every name to the real connection"): ("mutant", "W3-setattr-forwards"),
    ("C2", "a gate with no such fixture in scope (C2 then fails as \"no (b2) observed\")"):
        ("mutant", "C2-fixture-out-of-scope"),
    ("C3", "refuse every label/SQLite disagreement in both directions"): ("mutant", "C3-refuse-every-disagreement"),
}
"""Every §5f.1 phrase's ONE carrier: a row of THIS table, or ABSENT with its reason and a cell (none today)."""

_N_CELL = re.compile(r"(?:_n|\[N)(\d+)")


def carrier_problems(root: pathlib.Path = ROOT) -> list:
    """The complement check: §5f.1's phrase set EQUALS CARRIERS' key set, each carrier resolves (a mutant of this table,
    or an ABSENT cell that exists), a "the same" phrase has its referent's carrier, and an N-row's carrier names a cell
    of that N (the `_n<k>` / `[N<k>` the cells file uses)."""
    try:
        ph = phrases(root)
    except (OSError, ValueError) as e:
        return [f"the §5f.1 phrases cannot be read: {e}"]
    out = []
    out += [f"{k[0]} phrase {k[1]!r} has no carrier" for k in sorted(set(ph) - set(CARRIERS))]
    out += [f"{k[0]} carrier {k[1]!r} has no phrase in the spec" for k in sorted(set(CARRIERS) - set(ph))]
    by_id = {m[0]: m for m in MUTANTS}
    tests = SUBJECT_P.defined_tests(root)
    for k, c in sorted(CARRIERS.items()):
        if k not in ph:
            continue
        if c[0] == "mutant" and len(c) == 2:
            m = by_id.get(c[1])
            if m is None:
                out.append(f"{k[0]} phrase {k[1]!r}: no mutant {c[1]!r} in this table")
            elif k[0].startswith("N") and not any(
                    int(x) == int(k[0][1:]) for n in m[4] for x in _N_CELL.findall(n.split("::")[-1])):
                out.append(f"{k[0]} phrase {k[1]!r}: its carrier {c[1]!r} names no {k[0]} cell")
        elif c[0] == "absent" and len(c) == 3:
            f, name = c[2].split("::")[0], c[2].split("::")[-1].split("[")[0]
            if f"{f}::{name}" not in tests:
                out.append(f"{k[0]} phrase {k[1]!r}: the ABSENT cell {c[2]} is not a test in {f}")
        else:
            out.append(f"{k[0]} phrase {k[1]!r}: carrier {c!r} is not ('mutant', id) or ('absent', reason, cell)")
        ref = ph[k]
        if ref is not None and CARRIERS.get(ref) != c:
            out.append(f"{k[0]} phrase {k[1]!r} is the same mutant as {ref[0]}'s {ref[1]!r} but has another carrier")
    return out


def problems(path=None, root: pathlib.Path = ROOT) -> list:
    """The table check (`--check`): the phrase complement, then the protocol's checks of the committed table."""
    return carrier_problems(root) + SUBJECT_P.problems(path, root)


def main(argv=None) -> int:
    argv = sys.argv if argv is None else argv
    if "--phrases" in argv:
        ph = phrases()
        for k in sorted(ph, key=lambda k: list(ph).index(k)):
            c = CARRIERS.get(k, ("MISSING",))
            same = f"  [= {ph[k][0]}: {ph[k][1]}]" if ph[k] else ""
            print(f"{k[0]:4s} {c[0]:7s} {c[1] if len(c) > 1 else '':40s} {k[1]}{same}")
        bad = carrier_problems()
        for b in bad:
            print(f"CARRIER: {b}")
        return 1 if bad else 0
    bad = carrier_problems()
    if bad and ("--write" in argv or "--try" in argv):
        for b in bad:
            print(f"CARRIER: {b}")
        return 1
    if "--write" in argv or "--try" in argv:
        return SUBJECT_P.main(argv)
    probs = problems()
    for b in probs:
        print(f"STALE: {b}")
    if probs:
        return 1
    t = json.loads(TABLE.read_text(encoding="utf-8"), object_pairs_hook=_strict_pairs)
    print(f"{TABLE.relative_to(ROOT)} current: {json.dumps(t['summary'])} (body_sha256 {t['body_sha256']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
