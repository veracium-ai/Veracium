#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0018_implementation_mutants.py::test_the_table_check_refuses_each_tampered_table
"""0018 §4j.8's named mutants, against the implementation: every row demonstrated red by its invariant's cells.

Every mutant §4j.8 names has a row here, or its row is in the place stated: I39's are in specs/evidence/0013/sa10_mutants.py, beside the gate
they edit, but for one whose cell is in T2, and the head-bound mutants of the two v16 raises are equivalent on the last rung, so they have cells and no row.

Each row is a code edit run by the shared protocol (specs/evidence/mutation_protocol.py) on a copy of the tracked tree, killed by
assertion (or DID NOT RAISE) in ITS named cells, with an HONEST probe that still passes under it. Beside them, per mutated file, a NO-OP
control whose named cells must all pass, and one classifier negative control. I39's rows live in specs/evidence/0013/sa10_mutants.py,
beside the gate they edit.

    $PY specs/evidence/0018/rungs/implementation_mutants.py --check
    TMPDIR=/dev/shm $PY specs/evidence/0018/rungs/implementation_mutants.py --write
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parents[1]))
import mutation_protocol as _protocol  # noqa: E402

TABLE = HERE / "implementation" / "mutation-table.json"
SELF = "specs/evidence/0018/rungs/implementation_mutants.py"
MIG = "src/veracium/store/migration.py"
RM = "src/veracium/store/release_migration.py"
SV = "src/veracium/store/schema_version.py"
CLI = "src/veracium/cli.py"
GATE = "specs/evidence/0013/sa10_gate.py"
T3 = "tests/test_0018_rungs_t3.py"
T4 = "tests/test_0018_rungs_t4.py"
T5 = "tests/test_0018_rungs_t5.py"
TC = "tests/test_migrate_cli.py"
T2 = "tests/test_0018_rungs_t2.py"
PA1 = "tests/test_0013_pa1_campaign_cells.py"
DIGESTED = (MIG, RM, SV, CLI, GATE, T2, T3, T4, T5, TC, PA1, "specs/evidence/0018/rungs/digest_vectors.json",
            "specs/evidence/0018/rungs/manifest.json", "specs/evidence/0018/rungs/fixtures.tar.xz",
            "specs/evidence/0018-adjacent-rungs/closure/recovery_v05.py",
            "specs/evidence/0018-adjacent-rungs/closure/recovery-table-v051.json",
            "specs/evidence/mutation_protocol.py", _protocol.KINDS, SELF)

FIRST = "v01-910e49325716-from-v0.4.8.db"
WALK = f"{T5}::test_every_rung_from_every_base[{FIRST}]"
PLANNED = f"{T5}::test_a_rung_executes_exactly_its_plan_and_every_write_is_its_entry_s[{FIRST}]"
VECTOR = f"{T5}::test_each_rung_s_digest_is_its_vector"
ORDER = f"{T5}::test_the_direct_plans_keep_their_order"
DIRECT = f"{T5}::test_the_direct_route_executes_its_own_plan_with_one_clock_and_one_stamp[1]"
ALTERED = lambda n, t: f"{T5}::test_a_mismatched_alter_output_reports_the_rung_s_target[{n}-{t}]"     # noqa: E731
ROW = lambda n: f"{T3}::{n}"                                                                         # noqa: E731
CELL = lambda n: f"{TC}::{n}"                                                                        # noqa: E731
EQUAL = lambda r: f"{T4}::test_the_classifier_equals_the_extracted_table_input_by_input[{r}]"        # noqa: E731
HONEST = [CELL("test_a_store_at_head_makes_no_rung")]
HONEST_T4 = [f"{T4}::test_the_classifier_takes_no_diagnostic"]

_PLAN_ADD = "[ForwardEntry(0, target, \"add\", o) for o in SCHEMAS[target] if o.key not in have]"
_GUARD = "[e for e in FORWARD_ENTRIES if e.lo <= base < e.v <= target]"
_STAMP = 'ForwardEntry(0, target, "stamp", target)'
_CHECK = ', ForwardEntry(0, target, "read", _read_stamped, (_check_stamp,)),\n               ForwardEntry(0, target, "check", _check_stamp, (STEP_STAMP,))])'
_FAULT = '                "", base, target, "unsupported-migration", diff=fault.diff), fault.why) from None\n'
_LOOP = "            for entry in plan(base, target):\n"
_WIKI = "def _data_wiki(conn, run):\n"
_REPEAT = ('    ForwardEntry(0, 16, "read", _read_counter, (_check_act_counter,)),\n    ForwardEntry(0, 16, "check", _check_act_counter, (STEP_ACT_COUNTER,)),\n'
           '    ForwardEntry(15, 16, "read", _read_red_before, (_check_notice_state,)),\n')
_SWAP_A = '    ForwardEntry(0, 3, "data", _data_outcome_chains, (STEP_CHAINS,)),\n    ForwardEntry(0, 3, "check", _check_chains, (STEP_CHAINS,)),\n    ForwardEntry(0, 4, "data", _data_wiki, (STEP_WIKI,)),\n'
_SWAP_B = '    ForwardEntry(0, 4, "data", _data_wiki, (STEP_WIKI,)),\n    ForwardEntry(0, 3, "data", _data_outcome_chains, (STEP_CHAINS,)),\n    ForwardEntry(0, 3, "check", _check_chains, (STEP_CHAINS,)),\n'
_MIDDLE = ('    ForwardEntry(0, 16, "read", _read_counter, (_check_act_counter,)),\n    ForwardEntry(0, 16, "check", _check_act_counter, (STEP_ACT_COUNTER,)),\n'
           '    ForwardEntry(0, 16, "read", _read_registry_before, (_check_registry,)),\n')
_COUNTER = '    ForwardEntry(0, 16, "data", _data_act_counter, (STEP_ACT_COUNTER,)),\n'
_REGISTRY = '    ForwardEntry(0, 16, "data", _data_registry, (STEP_REGISTRY,)),\n'
_SAME_RUNG, _SAME_RUNG_SWAPPED = _COUNTER + _MIDDLE + _REGISTRY, _REGISTRY + _MIDDLE + _COUNTER
_SEG = "        out += [_segment(e.kind), _segment(len(fields))] + [_segment(f) for f in fields]\n"
_CLOCK_FIRST = ('    return ([ForwardEntry(0, target, "clock", None)]\n            + [ForwardEntry(0, target, "add", o) for o in SCHEMAS[target] if o.key not in have]\n')
_CLOCK_AFTER = ('    return ([ForwardEntry(0, target, "add", o) for o in SCHEMAS[target] if o.key not in have]\n            + [ForwardEntry(0, target, "clock", None)]\n')

MUTANTS = [
    # ---- I33: every rung lands at its target ----------------------------------------------------------------------------
    ("I33-the-additive-diff-ignores-the-target", "product", MIG, [(_PLAN_ADD, _PLAN_ADD.replace("SCHEMAS[target]", "SCHEMAS[SCHEMA_VERSION]"))],
     [WALK], HONEST, None, "a rung adds head's objects, not its target's"),
    ("I33-a-guard-bound-to-head", "product", MIG, [(_GUARD, "[e for e in FORWARD_ENTRIES if e.lo <= base < e.v]")],
     [WALK], HONEST, None, "a rung runs every later step, because the guard forgot the target"),
    ("I33-the-stamp-written-as-head", "product", MIG, [(_STAMP, 'ForwardEntry(0, target, "stamp", SCHEMA_VERSION)')],
     [WALK], HONEST, None, "a rung stamps head"),
    # D4: one raise since T1, so each row conditions on its step. At v16 a head-bound mutant is EQUIVALENT: the last rung's target is head, so
    # the two v16 raises report 16 either way. Their cells stand; no row can kill what cannot differ.
    ("I33-the-v6-refusal-reports-head", "product", MIG, [(_FAULT, _FAULT.replace('"", base, target,', '"", base, SCHEMA_VERSION if fault.why == "v6-alter-path" else target,'))],
     [ALTERED("ALTER_PATH_V6_SQL", 6)], HONEST, None, "the v6 refusal reports head"),
    ("I33-the-v8-refusal-reports-head", "product", MIG, [(_FAULT, _FAULT.replace('"", base, target,', '"", base, SCHEMA_VERSION if fault.why == "v8-alter-path" else target,'))],
     [ALTERED("ALTER_PATH_V8_SQL", 8)], HONEST, None, "the v8 refusal reports head"),
    ("I33-the-v10-refusal-reports-head", "product", MIG, [(_FAULT, _FAULT.replace('"", base, target,', '"", base, SCHEMA_VERSION if fault.why == "v10-alter-path" else target,'))],
     [ALTERED("ALTER_PATH_V10_FROM_CONSTRUCTOR_SQL", 10)], HONEST, None, "the v10 refusal reports head"),
    # ---- I36: the plan, and what runs -----------------------------------------------------------------------------------
    ("I36-the-stamp-check-removed", "product", MIG, [(_CHECK, "])")], [VECTOR], HONEST, None, "the stamp is written and never read back"),
    ("I36-one-repeated-v16-check-dropped", "product", MIG,
     [(_REPEAT, '    ForwardEntry(15, 16, "read", _read_red_before, (_check_notice_state,)),\n')], [VECTOR], HONEST, None,
     "a check the v16 block repeats runs once fewer"),
    ("I36-two-data-steps-swapped", "product", MIG, [(_SAME_RUNG, _SAME_RUNG_SWAPPED)], [VECTOR], HONEST, None, "two data steps of one rung run in the other order"),
    ("I36-two-rungs-data-steps-swapped", "product", MIG, [(_SWAP_A, _SWAP_B)], [ORDER], HONEST, None,
     "two data steps of different rungs swap: the same direct route, a different order, and no rung's digest moves"),
    ("I36-a-field-joined-by-a-separator", "product", MIG,
     [(_SEG, '        out += [_segment(e.kind), _segment(len(fields)), _segment("|".join(str(f) for f in fields))]\n')],
     [VECTOR], HONEST, None, "a field is encoded with a separator, not as its own segment"),
    ("I36-the-clock-read-after-the-diff", "product", MIG, [(_CLOCK_FIRST, _CLOCK_AFTER)], [VECTOR], HONEST, None,
     "the one clock read moves after the additive diff"),
    ("I36-an-undeclared-write", "product", MIG, [(_LOOP, '            conn.execute("UPDATE episodes SET json=json")\n' + _LOOP)],
     [PLANNED], HONEST, None, "a write with no active entry"),
    ("I36-an-undeclared-dispatch", "product", MIG,
     [(_LOOP, '            for entry in [*plan(base, target), ForwardEntry(0, target, "clock", None)]:\n')], [DIRECT], HONEST, None,
     "an entry the plan does not hold is dispatched"),
    ("I36-a-data-entry-issues-ddl", "product", MIG,
     [(_WIKI, _WIKI + '    conn.execute("CREATE TABLE IF NOT EXISTS mis_split (a)")\n    conn.execute("DROP TABLE mis_split")\n')],
     [PLANNED], HONEST, None, "a `data` entry issues DDL: what the kind rule stops and SA10 alone would admit elsewhere"),
    ("I36-a-direct-byte-check-deleted", "product", MIG, [("    if run.stored_v6 != ALTER_PATH_V6_SQL:\n", "    if False:\n")],
     [ALTERED("ALTER_PATH_V6_SQL", 6)], HONEST, None, "the v6 byte check never fires"),
    ("I36-a-frozen-alter-dropped", "product", SV, [('    "ALTER TABLE confirmations ADD COLUMN origin_store TEXT",\n', "")],
     [VECTOR], HONEST, None, "one statement of a frozen ALTERS tuple is dropped"),
    # ---- research's read of e1734fe3 (d5d78fab): the rest of §4j.8's named mutants, each with the cell that kills it -----------------
    ('I34-checked-after-the-mint', "product", RM, [('    resolved = payload\n    if expect_base is not None and resolved.resolved_base != expect_base:\n        return unexpected(seen, resolved.resolved_base)\n    canonical = resolved.canonical_path\n', '    resolved = payload\n    canonical = resolved.canonical_path\n'), ('        resolved = payload\n        if expect_base is not None and resolved.resolved_base != expect_base:\n            return unexpected(seen, resolved.resolved_base)\n    if expect_base is not None and authority.from_version != expect_base:\n        return unexpected(seen, authority.from_version)\n    result = _delegate(canonical, authority)\n', '        resolved = payload\n    result = _delegate(canonical, authority)\n    if expect_base is not None and authority.from_version != expect_base:\n        return unexpected(seen, authority.from_version)\n')],
     [ROW("test_a_mismatched_expectation_stops_before_any_authority_is_used")], HONEST, None, 'the expectation is checked after the mint is delegated'),
    ('I35-same-build-retry', "product", RM, [('("U5", ("unsupported-migration", "unsupported-sqlite", "unsupported-base"), None, "no-rerun-this-build")', '("U5", ("unsupported-migration", "unsupported-sqlite", "unsupported-base"), None, "rerun")')],
     [EQUAL("1-2")], HONEST_T4, None, 'U5 offers a retry with the same build'),
    ('I35-rerun-because-a-version-is-known', "product", RM, [('        return "K", "stop-inspect-unknown"\n', '        return ("K", "rerun") if version is not None else ("K", "stop-inspect-unknown")\n')],
     [EQUAL("1-2")], HONEST_T4, None, 'unknown facts with a version offer a rerun'),
    ('I35-audit-write-weaker', "product", RM, [('store = "rerun-resumes-store" if row in ("C1", "U0") else action', 'store = "rerun-resumes-store"')],
     [EQUAL("1-2")], HONEST_T4, None, 'every write-error resumes, its facts unread'),
    ('I35-rerun-repairs-a-missing-record', "product", RM, [('"rerun-resumes-store": ("yes", "rerun resumes from the store as it stands"),', '"rerun-resumes-store": ("yes", "rerun repairs the missing record"),')],
     [f"{T4}::test_no_action_promises_a_rerun_repairs_the_missing_record"], HONEST_T4, None, 'the prose promises that a rerun repairs a missing record'),
    ('I36-helper-carried-check-dropped', "product", MIG, [('def _check_chains(conn, run):\n', 'def _check_chains(conn, run):\n    return\n')],
     [ROW("test_row_12_a_postcondition_failure_rolls_back_to_the_original_stamp")], HONEST, None, 'a check that lives in a helper never runs'),
    ('I36-nested-check-deleted', "product", MIG, [('def _check_wiki(conn, run):\n', 'def _check_wiki(conn, run):\n    return\n')],
     ["tests/test_0013_pa1_campaign_cells.py::test_cell_a_skipped_wiki_drop_refuses_at_its_step"], HONEST, None, "a check's body is emptied"),
    ('I36-direct-as-adjacent-plans', "product", MIG, [('    have = {o.key for o in SCHEMAS[base]}\n    return ([ForwardEntry(0, target, "clock", None)]\n', '    if target - base > 1:\n        return [e for b in range(base, target) for e in plan(b, b + 1)]\n    have = {o.key for o in SCHEMAS[base]}\n    return ([ForwardEntry(0, target, "clock", None)]\n')],
     [WALK], HONEST, None, 'the direct route is rebuilt as the concatenation of adjacent plans'),
    ('I37-default-found-plus-one', "product", SV, [('                    if found > target:\n', '                    if migrate_to is None and 0 < found < target:\n                        target = found + 1\n                    if found > target:\n')],
     [f"{T5}::test_every_rung_from_every_base[v03-ed6ae6221423-from-v0.4.8.db]"], HONEST, None, '`migrate_to` defaults to found+1'),
    ('I38-binding-on-migrate_to', "product", RM, [('            if base != t - 1:\n', '            if t < sv.SCHEMA_VERSION and base != t - 1:\n')],
     [ROW("test_row_7a_a_store_below_the_source_refuses_and_nothing_is_written[last one behind]")], HONEST, None, 'the binding is put on `migrate_to`, so the last rung is unbound'),
    ('I38-no-new-hook', "product", RM, [('older=older, new=new, migrate_to=t, allow_adopt=False', 'older=older, migrate_to=t, allow_adopt=False')],
     [ROW("test_row_1_a_rung_moves_one_version_and_binds_to_its_minted_endpoints[1]")], HONEST, None, 'no `new=` hook'),
    ('I38-path-unencoded', "product", RM, [('uri = "file:" + urllib.parse.quote_from_bytes(os.fsencode(canonical)) + "?mode=rw"', 'uri = "file:" + canonical + "?mode=rw"')],
     [ROW("test_the_rung_addresses_exactly_the_file_the_mint_observed[question]")], HONEST, None, 'the path interpolated into the URI unencoded'),
    ('I38-operational-error-is-missing', "product", RM, [('    except sqlite3.OperationalError as exc:\n        try:\n            os.lstat(canonical)\n', '    except sqlite3.OperationalError as exc:\n        raise _RungRefused("missing", "gone") from exc\n        try:\n            os.lstat(canonical)\n')],
     [ROW("test_row_11b_an_existing_path_that_will_not_open_is_unopenable")], HONEST, None, 'an OperationalError mapped to `missing`'),
    ("I37-an-ordinary-open-migrates-to-a-target", "product", SV, [('        if migrate_to < SCHEMA_VERSION and older is None:\n            raise ValueError("a migration target below head requires the migration hook")\n', "")],
     ["tests/test_0018_rungs_t2.py::test_a_target_below_head_needs_the_hook"], HONEST, None, "an ordinary open, with no migration hook, reaches a below-head target"),
    ("I37-the-target-reaches-the-gate", "product", SV, [("        status = runtime_status()\n", "        attestation_revision(target)\n        status = runtime_status()\n")],
     ["tests/test_0018_rungs_t2.py::test_the_runtime_gate_never_sees_the_target"], HONEST, None, "the target reaches the runtime gate"),
    ("I35-zero-action-ids", "product", RM, [("        return RecoveryDecision(row, (action,), row in (\"C1\", \"C2\"))\n", "        return RecoveryDecision(row, (), row in (\"C1\", \"C2\"))\n")],
     [f"{T4}::test_every_admitted_input_has_exactly_one_store_action[1-2]"], HONEST_T4, None, "an admitted input gets no action id"),
    ("I35-two-action-ids", "product", RM, [("        return RecoveryDecision(row, (action,), row in (\"C1\", \"C2\"))\n", "        return RecoveryDecision(row, (action, \"rerun\"), row in (\"C1\", \"C2\"))\n")],
     [f"{T4}::test_every_admitted_input_has_exactly_one_store_action[1-2]"], HONEST_T4, None, "an admitted input gets two action ids"),
    ("I35-a-partial-rung", "product", MIG, [('                    conn.execute(f"PRAGMA user_version = {entry.step}")\n', '                    conn.execute(f"PRAGMA user_version = {entry.step}")\n                    conn.execute("COMMIT")\n                    conn.execute("BEGIN IMMEDIATE")\n')],
     [CELL("test_a_postcondition_failure_at_rung_two_leaves_rung_one_whole_and_a_repaired_build_resumes"), ROW("test_a_first_rung_that_fails_restores_the_original_stamp_and_data")], HONEST, None, "a rung commits before its last check, so a failure leaves it partial"),
    ("I38-drift-repaired-against-head", "product", SV, [("        if drift(objs, target):\n            _repair_drift(conn, target)\n", "        if drift(objs, target):\n            _repair_drift(conn, SCHEMA_VERSION)\n")],
     [ROW("test_row_5_a_target_store_with_drift_is_repaired_against_the_target[13]")], HONEST, None, "row 5: a rung's drift is repaired against head, not `t`"),
    ("I38-a-target-store-judged-at-head", "product", SV, [('        accepted = accepted_digests(target)\n        objs = manifest(conn)\n', '        accepted = accepted_digests(SCHEMA_VERSION)\n        objs = manifest(conn)\n')],
     [ROW("test_row_4_another_operation_reached_the_target_first[13]")], HONEST, None, "a store at the rung's target is judged against head's accepted shapes: row 4 reads the difference, and row 6 refuses either way"),
    ("I38-a-shape-accepted-at-any-version-passes", "product", SV, [("        if digest(objs, target) not in accepted:\n            raise _SITE_OPEN_UNACCEPTED_SHAPE", "        if digest(objs, target) not in accepted and not any(digest(objs, v) in accepted_digests(v) for v in range(1, SCHEMA_VERSION + 1)):\n            raise _SITE_OPEN_UNACCEPTED_SHAPE")],
     [ROW("test_row_6_a_neighbour_s_whole_shape_under_the_target_s_stamp_refuses")], HONEST, None, "a shape accepted at another version passes: what an intruder table cannot show"),
    ("I38-the-target-branch-not-validated", "product", SV, [("                    repaired = _validated_current(conn, spath, found, target=target)\n", "                    repaired = False\n")],
     [ROW("test_row_6_a_target_store_of_another_shape_refuses_as_stamped_shape_mismatch[13]"), ROW("test_row_5_a_target_store_with_drift_is_repaired_against_the_target[13]")], HONEST, None, "a store already at the target is not validated at all"),
    ("I38-the-post-hook-check-removed", "product", SV, [("                    older(conn, spath, found, objs, found, runtime=status)\n                    _validated_current(conn, spath, found, require_stamp=True, target=target)\n", "                    older(conn, spath, found, objs, found, runtime=status)\n")],
     [ROW("test_row_3_a_source_of_another_shape_refuses_as_stamped_shape_mismatch[13]")], HONEST, None, "nothing validates the migrated store, so row 3 has no refusal"),
    ("I38-a-repair-not-counted", "product", SV, [("                    repaired = _validated_current(conn, spath, found, target=target)\n", "                    repaired = _validated_current(conn, spath, found, target=target) and False\n")],
     [CELL("test_rows_3_to_6_through_the_real_walk[row 5-13]")], HONEST, None, "a committed repair reads as nothing, so the walk does not count it"),
    ("I39-every-historical-constructor-admitted", "gate", GATE, [('    b1 = {o.ddl for o in head if o.key[0] in ("table", "index")}\n', '    b1 = {o.ddl for v in sv.SCHEMAS.values() for o in v if o.key[0] in ("table", "index")}\n')],
     ["tests/test_0018_rungs_t2.py::test_sa10_s_text_classes_bind_the_target_and_not_the_head"], HONEST, None,
     "head equality is widened to every historical constructor, which round 1 ruled out. Here and not in SA10's table because its cell is in T2"),
    ("I13-the-preflight-writes-the-store", "product", RM, [("    status = sv.runtime_status()                 # measured once, here (0007 §4g.6 4a; 0013 §5f.3)\n", '    with sqlite3.connect(path) as written:\n        if written.execute("PRAGMA user_version").fetchone()[0] == 0:\n            written.execute("PRAGMA user_version = 1")\n    status = sv.runtime_status()                 # measured once, here (0007 §4g.6 4a; 0013 §5f.3)\n')],
     [ROW("test_before_delegation_an_unstamped_store_keeps_its_bytes_and_stamp")], HONEST, None, "resolving a legacy store stamps it, so a stopped rung has changed it"),
    ("I13-forged-evidence-carried-into-the-authority", "product", RM, [("            source_digest=sv.digest(objs, base),\n", "            source_digest=tuple.__getitem__(resolved, 2),\n")],
     [ROW("test_forged_resolution_evidence_cannot_alter_a_rung[unstamped first rung]"), ROW("test_forged_resolution_evidence_cannot_alter_a_rung[stamped middle rung]")], HONEST, None, "the authority carries the resolution's digest, not the store's own observation"),
    ("I36-a-mis-split", "product", MIG, [("    *_alters(2, 16, ALTERS_V15_TO_V16),\n", ""), ("def _read_v16_conf_stored(conn, run):\n", "def _read_v16_conf_stored(conn, run):\n    for statement in ALTERS_V15_TO_V16:\n        conn.execute(statement)\n")],
     [PLANNED], HONEST, None, "an ALTER moved under a neighbouring entry: a write lands where its kind does not admit it"),
    ("I33-one-clock-for-every-rung", "product", MIG, [("                    run.now = _clock()\n", '                    run.now = globals().setdefault("_ONE_READ", _clock())\n')],
     [f"{T5}::test_each_declared_clock_value_is_its_own_rung_s_read[written_at]"], HONEST, None, "every rung reuses the first clock read"),
    # ---- I38: a rung binds its source and never creates -----------------------------------------------------------------
    ("I38-the-source-unbound", "product", RM, [("            if base != t - 1:\n", "            if False:\n")],
     [ROW("test_row_7a_a_store_below_the_source_refuses_and_nothing_is_written[middle two behind]")], HONEST, None,
     "M1: the transaction walks from a base the authority did not attest"),
    ("I38-a-rung-opens-to-create", "product", RM, [('"?mode=rw"', '"?mode=rwc"')],
     [ROW("test_row_11a_nothing_at_the_path_is_refused_and_nothing_appears[13]")], HONEST, None, "M3: a store deleted in the window is re-created"),
    ("I38-an-empty-store-read-as-nothing-there", "product", RM,
     [('raise _RungRefused("unaccepted", "an empty database where', 'raise _RungRefused("missing", "an empty database where')],
     [ROW("test_row_10_an_empty_replacement_is_never_created_into[1]")], HONEST, None,
     "M2 reported as a store that is not there. Building into the empty store is refused twice: a mutant that builds meets a second, loud "
     "refusal in `open_versioned`, a crash and no assertion, so this row kills what the refusal SAYS"),
    # ---- I34: the walk --------------------------------------------------------------------------------------------------
    ("I34-a-loop-without-the-expectation", "product", CLI, [("host_attestation=attestation, expect_base=expect)", "host_attestation=attestation, expect_base=None)")],
     [CELL("test_a_store_moved_down_between_rungs_stops_before_a_second_mint")], HONEST, None, "the walk does not bind each rung to the last"),
    ("I34-count-printed-rungs", "product", CLI, [("        if d.counted:\n            committed.append(rep.operation_id)\n", '        if d.row in ("C1", "U0"):\n            committed.append(rep.operation_id)\n')],
     [CELL("test_an_unchanged_current_at_the_target_continues_and_is_not_counted")], HONEST, None, "a printed rung is counted, so an unchanged current is"),
    ("I34-count-only-the-migrated-branch", "product", CLI, [("        if d.counted:\n            committed.append(rep.operation_id)\n", '        if d.row == "C1":\n            committed.append(rep.operation_id)\n')],
     [CELL("test_a_committed_error_is_counted_once_and_stops_the_walk")], HONEST, None, "a committed error drops out of the count"),
    ("I34-count-a-committed-error-twice", "product", CLI, [("        if d.counted:\n            committed.append(rep.operation_id)\n", "        if d.counted:\n            committed.append(rep.operation_id)\n            committed.append(rep.operation_id)\n")],
     [CELL("test_a_committed_error_is_counted_once_and_stops_the_walk")], HONEST, None, "an id enters the count twice"),
    ("I34-continue-past-a-committed-error", "product", CLI, [('        if d.row in ("C1", "U0"):\n', '        if d.row in ("C1", "C2", "U0"):\n')],
     [CELL("test_a_committed_error_is_counted_once_and_stops_the_walk")], HONEST, None, "a committed error is treated as a success"),
    ("I34-re-create-the-attestation", "product", CLI, [("rm.run_release_rung(path, host_attestation=attestation, expect_base=expect)", 'rm.run_release_rung(path, host_attestation=rm.MigrationAttestation(quiesced=True, backup_ref=attestation.backup_ref), expect_base=expect)')],
     [CELL("test_one_attestation_object_is_admitted_at_every_call")], HONEST, None, "each rung gets a fresh attestation"),
    ("I34-count-a-readback-before-it-is-bound", "product", RM, [('    return (readback_facts is not None and readback_facts.outcome == "package-inconsistent"\n            and (readback_facts.from_version, readback_facts.to_version) == tuple(minted))\n', "    return readback_facts is not None\n")],
     [f"{T4}::test_a_package_escape_counts_only_a_bound_readback[another rung]", f"{T4}::test_a_package_escape_counts_only_a_bound_readback[another outcome]"], HONEST_T4, None,
     "any record counts, as round 2's model accepted any readback of kind `record`"),
    # ---- I35: recovery is one classifier --------------------------------------------------------------------------------
    ("I35-unknown-prints-the-previous-version", "product", CLI, [('        elif d.row in ("K", "U2", "U3", "U4", "U6") or d.row.startswith("N"):\n            version = "unknown"\n', '        elif d.row in ("K", "U2", "U3", "U4", "U6") or d.row.startswith("N"):\n            version = f"v{expect}"\n')],
     [CELL("test_unknown_facts_print_unknown_never_the_previous_rungs_version")], HONEST, None, "unknown facts print the last known version"),
    ("I35-the-derived-state-as-a-version", "product", CLI, [('            _migrate_last_lines(committed, d, "unknown", err=True)\n            return 3\n', '            _migrate_last_lines(committed, d, e.derived_resulting_state, err=True)\n            return 3\n')],
     [CELL("test_a_read_error_prints_its_state_as_a_state_and_the_version_as_unknown")], HONEST, None, "`derived_resulting_state` lands in the version column"),
    ("I35-the-superseded-blanket-retry", "product", RM, [('    return "U7", "inspect-first-fallback"\n', '    return "U7", "rerun"\n')],
     [EQUAL("1-2"), EQUAL("13-14"), EQUAL("15-16")], HONEST_T4, None, "every unchanged carrier the rows do not name retries blindly"),
    ("I35-a-conditional-claims-a-cause", "product", RM, [('    ("U3", ("migration-source-missing",), "unaccepted", "conditional-other-writer-or-path"),\n', '    ("U3", ("migration-source-missing",), "unaccepted", "fix-path-then-rerun"),\n')],
     [EQUAL("13-14")], HONEST_T4, None, "U3 claims it knows which cause happened"),
]

_NOOP = {MIG: "def _alters(lo, v, statements):\n", RM: "class RecoveryDecision(NamedTuple):\n", SV: "def legacy_base_versions(", CLI: "def _facts_of(r):\n", GATE: "def text_classes(target=None):\n"}
CONTROLS = [(f"NOOP-{pathlib.Path(rel).stem}", rel, [(a, "# no-op control: a comment, no behaviour\n" + a)],
             sorted({c for m in MUTANTS if m[2] == rel for c in m[4]}), f"a comment before {a.strip()!r}: bytes change, behaviour does not", "SURVIVED")
            for rel, a in _NOOP.items()]
CONTROLS.append(("CTRL-unrelated-TypeError", CLI, [("def _facts_of(r):\n", 'def _facts_of(r):\n    raise TypeError("an unrelated execution failure (classifier negative control)")\n')],
                 [CELL("test_a_v13_store_walks_three_rungs_with_three_ids_and_three_records"), CELL("test_a_store_at_head_makes_no_rung")],
                 "an UNRELATED TypeError in the CLI: every walk fails for no reason a row names", "UNCLASSIFIED"))

SUBJECT_P = _protocol.Subject(
    spec="0018", finding="adjacent-rungs-implementation", table=TABLE, digested=DIGESTED, mutants=MUTANTS, controls=CONTROLS,
    import_modules=("veracium.store.migration", "veracium.store.release_migration", "veracium.store.schema_version", "veracium.cli"),
    import_specs=(), cells_files=(T2, T3, T4, T5, TC, PA1), kinds=("product", "gate"))

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
