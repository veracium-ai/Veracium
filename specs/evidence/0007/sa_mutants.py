#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0007_sa_mutants.py::test_the_table_check_refuses_each_tampered_table
"""INV-SA1–INV-SA12's mutation table (0007 §4g.8 and 0013 §5f.4; 0007 I6): every mutant the spec names, demonstrated.

§4g.8's Gate: "each row is a PRODUCT test at implementation, demonstrated red against its mutant". The mutants are the
spec's own PHRASES: each invariant's "mutant that must fail" cell, cut at its first sentence end and split on ";" at
parenthesis depth 0, version markers stripped (research's stage-1 read of I6, Q2: derived from the text, so a missing
mutant fails by NAME). Every phrase has exactly one carrier:
  MUTANT  a row of THIS table: a production edit, run by the shared protocol (specs/evidence/mutation_protocol.py,
          INV-SA10's, factored out), killed by assertion in its named cells;
  CITE    a row of another matrix that already kills it (`file::matrix::row`), checked to exist;
  ABSENT  no mutant is writable on today's code, with the reason and a cell that fails the day one becomes writable.
INV-SA10's phrases are 0013 §5f.4's; most are rows of INV-SA10's own table (specs/evidence/0013/sa10_mutants.py) or of
0013-PA1's (specs/evidence/0013/mutation-table.json), cited.

    $PY specs/evidence/0007/sa_mutants.py --check          # fast: definitions, anchors, digests, phrases, every row good
    TMPDIR=/dev/shm $PY specs/evidence/0007/sa_mutants.py --write
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import mutation_protocol as _protocol  # noqa: E402

_strict_pairs = _protocol._strict_pairs

TABLE = HERE / "sa" / "mutation-table.json"     # the name tests/test_closure_mutants.py finds
SELF = "specs/evidence/0007/sa_mutants.py"
SV = "src/veracium/store/schema_version.py"
NM = "src/veracium/store/near_misses.py"
DOC = "src/veracium/doctor.py"
REL = "src/veracium/store/release_migration.py"
MIG = "src/veracium/store/migration.py"
SE = "specs/schema_evidence.py"
SI = "specs/skip_inventory.py"
RS = "tests/test_0007_runtime_status.py"
SVT = "tests/test_store_versioning.py"
SM = "tests/test_schema_model.py"
JOBS = "tests/test_0007_attestation_jobs.py"
WRITER = "tests/test_0007_attestation_writer.py"
SPEC_0007 = "specs/0007-store-schema-versioning.md"
SPEC_0013 = "specs/0013-store-migrations.md"
SUBJECT = "INV-SA1-SA12"
DIGESTED = (SV, NM, DOC, REL, MIG, SE, SI, RS, SVT, SM, JOBS, WRITER, SPEC_0007, SPEC_0013,
            "specs/evidence/0013/sa10_gate.py", "specs/evidence/0013/pa1_campaign.py", "tests/test_0013_sa10_gate.py",
            "tests/test_0013_pa1_campaign_cells.py",
            "specs/evidence/mutation_protocol.py", _protocol.KINDS, SELF)

R = lambda name: f"{RS}::{name}"                                                    # noqa: E731
GATE = lambda site: R(f"test_a_refused_build_is_refused_before_any_version_decision[{site}]")   # noqa: E731

_OPEN_GATE = ('''    with _SITE_OPEN_RUNTIME_UNSUPPORTED.consult():
        status = runtime_status()
        if runtime_refused(status):
            raise _SITE_OPEN_RUNTIME_UNSUPPORTED.fire(StoreVersionError(
                spath, found=None, expected=SCHEMA_VERSION,
                reason="unsupported-sqlite", diff=refusal_text(status)))
    warn_unattested(status)
''')
_PRE_GATE = ('''    status = sv.runtime_status()                 # measured once, here (0007 §4g.6 4a; 0013 §5f.3)
    if sv.runtime_refused(status):
        return _intercept("unsupported-sqlite", False, False, "unknown", None,
                          sv.refusal_text(status))
    sv.warn_unattested(status)                   # a verified build reading a store warns here too (once per process)
''')
_KEY_TUPLE = ('''    return (r["sqlite_version"], r["source_id"], tuple(f[k] for k in sorted(FEATURE_KEYS)),
            r["compile_options_digest"], r["machine"], r["system"], r["libc"])''')
_PLATFORM = '''    return {"machine": canonical_machine(platform.machine()), "system": system,'''
_EACH_KEY = R("test_each_key_field_separates_two_records_that_agree_on_every_other")
GATE_FILE = "specs/evidence/0013/sa10_gate.py"
PA1_CELLS = "tests/test_0013_pa1_campaign_cells.py"
SA10_CELLS = "tests/test_0013_sa10_gate.py"
_OLDER = ("                    older(conn, spath, found, objs, found, runtime=status)\n"
          "                    _validated_current(conn, spath, found, require_stamp=True)\n")
P1 = lambda s: R(f"test_p1_a_verified_build_migrates_a_base_store_as_the_attested_build_does[{s}]")   # noqa: E731
P3 = lambda s: R(f"test_p3_a_stamp_below_head_is_refused_by_revalidation_and_rolls_back[{s}]")        # noqa: E731

# (id, kind, file, [(anchor, replacement)], named cells (EVERY one must fail), honest probes, reason or None, what)
MUTANTS = [
    # ---- INV-SA1 ----------------------------------------------------------------------------------------------------
    ("sa1-skip-verification-when-attested", "product", SV,
     [("        try:\n            verify_build()\n",
       "        if attested_key(key, attestations()):\n            return RuntimeStatus(\"attested\", None, key, "
       "unreadable, *build)\n        try:\n            verify_build()\n")],
     [f"{SVT}::test_inv_sa1_an_attested_identity_does_not_skip_verification"], [], None,
     "a matching attestation record short-circuits verification"),
    ("sa1-open-decides-shape-first", "product", SV,
     [(_OPEN_GATE, ""),
      ("                if found == SCHEMA_VERSION:\n                    repaired = _validated_current(conn, spath, found)",
       "                " + _OPEN_GATE.replace("\n    ", "\n                    ").replace("    with ", "with ", 1)
       .replace("\n                    warn_unattested", "\n                warn_unattested")
       + "                if found == SCHEMA_VERSION:\n                    repaired = _validated_current(conn, spath, found)")],
     [GATE("store/sqlite.py:__init__")], [], None,
     "open_versioned decides the version (invalid, newer) before measuring the build"),
    ("sa1-preflight-decides-shape-first", "product", REL,
     [(_PRE_GATE, ""),
      ("    if found == _HEAD:\n        if sv.digest(objs, _HEAD) not in sv.accepted_digests(_HEAD):",
       _PRE_GATE + "    if found == _HEAD:\n        if sv.digest(objs, _HEAD) not in sv.accepted_digests(_HEAD):")],
     [GATE("store/release_migration.py:_classify_or_intercept")], [], None,
     "the release preflight decides the version before measuring the build"),
    # ---- INV-SA2 ----------------------------------------------------------------------------------------------------
    ("sa2-reproduction-alone", "product", SV,
     [("    kinds = {nm.kind for nm in near_misses.NEAR_MISSES}\n",
       "    return\n    kinds = {nm.kind for nm in near_misses.NEAR_MISSES}\n")],
     [R("test_each_verification_step_refuses_and_names_itself[discrimination]"),
      R("test_a_near_miss_that_coincides_with_an_accepted_head_shape_refuses_the_build")], [], None,
     "accept on reproduction alone: discrimination dropped"),
    ("sa2-probes-alone", "product", SV,
     [("    verify_reproduction(records, SCHEMAS, _constructor_objects)\n",
       "    return\n    verify_reproduction(records, SCHEMAS, _constructor_objects)\n")],
     [R("test_each_verification_step_refuses_and_names_itself[reproduction]")], [], None,
     "accept on probes alone: reproduction and discrimination dropped"),
    ("sa2-exception-verified", "product", SV,
     [('        return RuntimeStatus("refused", f"verification raised {type(exc).__name__}", None, (),',
       '        return RuntimeStatus("verified", f"verification raised {type(exc).__name__}", None, (),')],
     [R("test_each_verification_step_refuses_and_names_itself[an exception]")], [], None,
     "an exception inside verification returns verified"),
    # ---- INV-SA3 ----------------------------------------------------------------------------------------------------
    ("sa3-digests-only", "product", SV,
     [('        if objs != entry["objects"]:\n', "        if False:\n")],
     [R("test_reproduction_compares_the_complete_manifestation_not_the_digest_alone")], [], None,
     "reproduction compares digests only (S69's rebuildable-index hole)"),
    ("sa3-against-own-manifestation", "product", SV,
     [('        if objs != entry["objects"]:\n', "        if objs != dict(objs):\n"),
      ("        if _digest_of_identity(objs, v, schemas) not in accepted:\n", "        if False:\n")],
     [R("test_each_verification_step_refuses_and_names_itself[reproduction]"),
      R("test_reproduction_compares_the_complete_manifestation_not_the_digest_alone")], [], None,
     "reproduction compares the build against its own manifestation, not the accepted evidence"),
    # ---- INV-SA4 ----------------------------------------------------------------------------------------------------
    ("sa4-drop-a-near-miss", "product", NM,
     [('    NearMiss("episodes-date-integer", "changed-type", ("table", "episodes"), "date TEXT,", "date INTEGER,"),\n',
       "")],
     [R("test_the_near_miss_set_covers_every_required_kind_and_each_is_the_head_with_one_change")], [], None,
     "one required near-miss dropped from the set"),
    ("sa4-equal-near-miss-passes", "product", SV,
     [("        if objs in accepted_head:", "        if False:")],
     [R("test_a_near_miss_that_coincides_with_an_accepted_head_shape_refuses_the_build"),
      f"{SVT}::test_inv_sa4_a_build_that_cannot_tell_a_near_miss_apart_is_refused"], [], None,
     "a near-miss equal to an accepted head shape passes"),
    # ---- INV-SA5 ----------------------------------------------------------------------------------------------------
    ("sa5-the-withdrawn-union", "product", SE,
     [('        accepted.append({"provenance": f"constructor v{version}",\n'
       '                         "digest": digest(manifest(c), version),\n'
       '                         "objects": identity(manifest(c))})\n',
       '        accepted.append({"provenance": f"constructor v{version}",\n'
       '                         "digest": digest(manifest(c), version),\n'
       '                         "objects": identity(manifest(c))})\n'
       '        accepted.append({"provenance": f"constructor v{version} @ sqlite {sqlite3.sqlite_version}",\n'
       '                         "digest": digest(manifest(c), version), "objects": identity(manifest(c))})\n')],
     [f"{SM}::test_every_accepted_manifestation_comes_from_a_closed_set_of_sources"], [], None,
     "a runtime record's manifestation joins the accepted set (the withdrawn union's entry form)"),
    # ---- INV-SA6 (production) ---------------------------------------------------------------------------------------
    ("sa6-refuse-a-second-key", "product", SV,
     [("        else:\n            seen[key] = (i, evidence)\n    return problems\n",
       "        else:\n            seen[key] = (i, evidence)\n    if len(seen) > 1:\n"
       "        problems.append(\"more than one active runtime\")\n    return problems\n")],
     [R("test_any_number_of_keys_is_valid_and_another_keys_record_attests_nothing")], [], None,
     "S66's single-active rule resurrected: a second key poisons the artifact"),
    ("sa6-accept-a-conflicting-pair", "product", SV,
     [("        if key in seen:\n            problems.append(",
       "        if key in seen and seen[key][1] == evidence:\n            problems.append(")],
     [f"{SVT}::test_inv_sa6_one_key_with_two_evidences_poisons_the_artifact"], [], None,
     "one key with different evidence is accepted"),
    ("sa6-a-rewrite-class-skip-left", "product", SI,
     [('claims nothing", "key")', 'claims nothing", "rewrite")')],
     [f"{JOBS}::test_no_inventory_entry_carries_the_rewrite_class"], [], None,
     "an in-suite skip left in the rewrite class"),
    ("sa6-ship-a-bootstrap-record", "product", SE,
     [("        if boot:\n", "        if False:\n")],
     [f"{WRITER}::test_real_the_release_check_refuses_a_bootstrap_record_by_derivation"], [], None,
     "the release check passes a bootstrap record (v21)"),
    # ---- INV-SA7 ----------------------------------------------------------------------------------------------------
    ("sa7-warn-on-every-open", "product", SV,
     [('    if st.status != "verified" or _WARNED:', '    if st.status != "verified":')],
     [R("test_a_verified_open_warns_once_per_process_and_an_attested_open_never")], [], None, "warn on every open"),
    ("sa7-warn-on-an-attested-build", "product", SV,
     [('    if st.status != "verified" or _WARNED:', '    if st.status == "refused" or _WARNED:')],
     [R("test_a_verified_open_warns_once_per_process_and_an_attested_open_never")], [], None,
     "warn on an attested build"),
    ("sa7-never-warn", "product", SV,
     [('    if st.status != "verified" or _WARNED:', "    if True:")],
     [R("test_a_verified_open_warns_once_per_process_and_an_attested_open_never")], [], None, "never warn"),
    # ---- INV-SA8 ----------------------------------------------------------------------------------------------------
    ("sa8-a-file-outside-the-wheel", "product", SV,
     [('f"them), or report this build to the project.")',
       'f"them), run `specs/schema_evidence.py --check`, or report this build to the project.")')],
     [R("test_the_refusal_names_the_first_failing_step_and_no_file_outside_the_wheel")], [], None,
     "the refusal text names schema_evidence.py"),
    ("sa8-omit-the-step", "product", SV,
     [("cannot be verified for Veracium's store: {st.reason}. \"", "cannot be verified for Veracium's store. \"")],
     [R("test_the_refusal_names_the_first_failing_step_and_no_file_outside_the_wheel")], [], None,
     "the refusal text omits the failing step"),
    # ---- INV-SA9 ----------------------------------------------------------------------------------------------------
    ("sa9-report-after-opening", "product", DOC,
     [("    _check_runtime(rep)                                       # before any store is opened (INV-SA9)\n", ""),
      ("        store = _open_snapshot(rep, path, tmpdir)\n",
       "        store = _open_snapshot(rep, path, tmpdir)\n        _check_runtime(rep)\n")],
     [R("test_doctor_checks_the_sqlite_build_before_opening_any_store")], [], None,
     "doctor reports the SQLite status after opening a store"),
    ("sa9-verified-at-warn", "product", DOC,
     [('        rep.add("runtime", "info", "this interpreter\'s SQLite is not an attested build;',
       '        rep.add("runtime", "warn", "this interpreter\'s SQLite is not an attested build;')],
     [R("test_doctor_reports_verified_at_info_and_refused_at_error[verified-info]")], [], None,
     "doctor reports a verified build at warn (doctor then exits 1 for every uv user)"),
    # ---- INV-SA11 (0013 §5f.4) ------------------------------------------------------------------------------------
    ("sa11-omit-the-key", "product", MIG,
     [("    occurred_at: str           # RFC 3339, UTC\n    runtime: MigrationRuntime\n",
       "    occurred_at: str           # RFC 3339, UTC\n"),
      ("occurred_at=datetime.now(timezone.utc).isoformat(), runtime=runtime)",
       "occurred_at=datetime.now(timezone.utc).isoformat())")],
     [R("test_both_kernel_events_carry_the_gates_measurement_as_their_last_field[verified]")], [], None,
     "the attempted and committed events carry no runtime"),
    ("sa11-attested-on-a-verified-build", "product", MIG,
     [("    rt = MigrationRuntime(status.sqlite_version, status.source_id, status.status)",
       '    rt = MigrationRuntime(status.sqlite_version, status.source_id, "attested")')],
     [R("test_both_kernel_events_carry_the_gates_measurement_as_their_last_field[verified]")], [], None,
     "a verified build's migration records attested"),
    # ---- INV-SA12 ---------------------------------------------------------------------------------------------------
    ("sa12-version-and-source-id-alone", "product", SV,
     [(_KEY_TUPLE, '    return (r["sqlite_version"], r["source_id"])')], [_EACH_KEY], [], None,
     "match on version and source id alone"),
    ("sa12-omit-compile-options", "product", SV,
     [(_KEY_TUPLE, _KEY_TUPLE.replace('            r["compile_options_digest"], ', "            "))], [_EACH_KEY], [],
     None, "the compile-options digest left out of the key"),
    ("sa12-options-in-returned-order", "product", SV,
     [('"\\n".join(sorted(str(o) for o in options))', '"\\n".join(str(o) for o in options)')],
     [R("test_the_compile_options_digest_ignores_the_order_the_build_returns_them_in")], [], None,
     "the options digested in the order the build returns them"),
    ("sa12-options-from-another-read", "product", SV,
     [("    return options_digest(_probe_build()[1])",
       "    with contextlib.closing(sqlite3.connect(\":memory:\")) as c:\n"
       "        return options_digest(r[0] for r in c.execute(\"PRAGMA compile_options\"))")],
     [R("test_the_compile_options_come_from_the_probe_connection")], [], None,
     "the options read somewhere other than the one probe of the store's own library"),
    ("sa12-drop-machine", "product", SV, [(_KEY_TUPLE, _KEY_TUPLE.replace('r["machine"], ', ""))], [_EACH_KEY], [], None,
     "machine dropped from the key"),
    ("sa12-drop-system", "product", SV, [(_KEY_TUPLE, _KEY_TUPLE.replace('r["system"], ', ""))], [_EACH_KEY], [], None,
     "system dropped from the key"),
    ("sa12-drop-libc", "product", SV, [(_KEY_TUPLE, _KEY_TUPLE.replace(', r["libc"]', ""))], [_EACH_KEY], [], None,
     "libc dropped from the key"),
    ("sa12-libc-from-libc-ver", "product", SV,
     [('            "libc": canonical_libc(system, interp)}', '            "libc": (platform.libc_ver()[0] or None)}')],
     [R("test_libc_comes_from_pt_interp_never_from_libc_ver")], [], None, "libc read from platform.libc_ver()"),
    ("sa12-machine-from-the-runner-label", "product", SV,
     [(_PLATFORM, '    return {"machine": canonical_machine(os.environ.get("RUNNER_ARCH") or platform.machine()), '
                  '"system": system,')],
     [R("test_machine_is_read_from_the_process_never_a_runner_label")], [], None,
     "machine taken from the CI runner's label"),
    ("sa12-canonicalise-one-side", "product", SV,
     [(_PLATFORM, '    return {"machine": platform.machine(), "system": system,')],
     [R("test_a_record_canonicalised_on_one_side_only_matches_nothing")], [], None,
     "the running build's machine is not canonicalised (a record's is)"),
    ("sa12-widen-the-alias-map", "product", SV,
     [('MACHINE_ALIASES = {"amd64": "x86_64", "arm64": "aarch64"}',
       'MACHINE_ALIASES = {"amd64": "x86_64", "arm64": "aarch64", "i686": "x86_64"}')],
     [R("test_the_machine_canonicaliser_is_a_closed_two_entry_alias_map[i686-i686]")], [], None,
     "i686 aliased to x86_64"),
    ("sa12-pt-interp-from-a-fixed-window", "product", SV,
     [("                f.seek(off)\n                raw = f.read(size)\n",
       "                if off + size > (1 << 20):\n                    return ''\n                f.seek(off)\n"
       "                raw = f.read(size)\n")],
     [R("test_pt_interp_is_read_wherever_the_segment_lies")], [], None,
     "PT_INTERP read from a 1 MiB window at the start of the file (v22; run 1's aarch64 and musl builds)"),
    ("sa12-a-short-segment-read-as-a-name", "product", SV,
     [('                if len(raw) != size or raw[-1:] != b"\\0" or b"\\0" in raw[:-1]:\n                    return None\n'
       '                return raw[:-1].decode("ascii")',
       '                return raw.rstrip(b"\\0").decode("ascii")')],
     [R("test_a_short_empty_or_unterminated_pt_interp_is_none_never_empty[truncated]"),
      R("test_a_short_empty_or_unterminated_pt_interp_is_none_never_empty[unterminated]")], [], None,
     "a short or unterminated PT_INTERP read as a name (v22)"),
    ("sa12-unreadable-matches", "product", SV,
     [("    if not isinstance(r, dict) or any(r.get(k) is None for k in KEY_FIELDS):", "    if not isinstance(r, dict):"),
      ('    if not all(isinstance(r[k], str) for k in KEY_FIELDS if k != "features"):',
       '    if not all(isinstance(r[k], (str, type(None))) for k in KEY_FIELDS if k != "features"):')],
     [f"{SVT}::test_inv_sa12_an_unreadable_platform_field_is_at_most_verified"], [], None,
     "an unreadable key field matches a record carrying the same None"),
]

MUTANTS += [
    # ---- INV-SA10's phrases outside INV-SA10's own table (research's scope ruling, 2026-10-27) --------------------
    ("sa10-narrow-the-site-scope", "product", GATE_FILE,
     [("        if fn.startswith(prefix):", '        if fn.startswith(prefix) and fn.endswith(os.sep + "migration.py"):')],
     [f"{SA10_CELLS}::test_the_gate_passes_the_clean_ladder_on_every_path_and_entry"], [], None,
     "the gate attributes sites in migration.py only: it then refuses a correct tree"),
    ("sa10-a-vacuous-postcondition", "product", MIG,
     [('        _refuse_unless(base, STEP_STAMP, [f"user_version reads {stamped}, not {SCHEMA_VERSION}"]\n'
       '                       if stamped != SCHEMA_VERSION else [])',
       "        _refuse_unless(base, STEP_STAMP, [])")],
     [f"{PA1_CELLS}::test_cell_a_perturbed_stamp_refuses_at_the_stamp"], [], None,
     "the stamp's postcondition made vacuous: its problems are always empty"),
    ("sa10-a-step-with-no-matcher", "product", MIG,
     [('STEP_STAMP, STEP_IDENTITY, STEP_EPOCH = "stamp", "store-identity", "store-epoch"',
       'STEP_STAMP, STEP_IDENTITY, STEP_EPOCH = "stamp", "store-identity", "store-epoch"\nSTEP_ORPHAN = "orphan-step"')],
     [R("test_every_migration_step_has_a_campaign_matcher_or_a_named_reason")], [], None,
     "a STEP_* name the campaign has no matcher for"),
    ("sa10-skip-the-byte-match-unattested", "product", SV,
     [(_OLDER, _OLDER.replace("                    _validated_current(",
                              "                    if status.status == \"attested\":\n"
                              "                        _validated_current("))],
     [P1("verified"), P3("verified")], [], None, "a verified build's migration skips the revalidation byte-match"),
    ("sa10-commit-before-revalidating", "product", SV,
     [(_OLDER, _OLDER.replace("                    _validated_current(",
                              "                    conn.execute(\"COMMIT\")\n                    conn.execute(\"BEGIN IMMEDIATE\")\n"
                              "                    _validated_current("))],
     [P3("verified"), P3("attested")], [], None, "the migration commits before it revalidates"),
    ("sa10-verified-takes-fewer-checks", "product", SV,
     [(_OLDER, _OLDER.replace("require_stamp=True)", "require_stamp=status.status == \"attested\")"))],
     [P1("verified")], [], None, "a verified build revalidates without the stamp requirement"),
]

# (id, file, [(anchor, replacement)], named cells, what, the outcome the classifier must give)
CONTROLS = [
    ("CTRL-unrelated-TypeError", SV,
     [("def refusal_text(st: RuntimeStatus) -> str:\n",
       "def refusal_text(st: RuntimeStatus) -> str:\n"
       '    raise TypeError("an unrelated execution failure (classifier negative control)")\n')],
     [R("test_the_refusal_names_the_first_failing_step_and_no_file_outside_the_wheel")],
     "an UNRELATED TypeError in the refusal text: a cell fails for no reason the row names", "UNCLASSIFIED"),
]

WRITER_MATRIX = f"{WRITER}::MUTANTS"
JOB_MATRIX = f"{JOBS}::test_the_attestation_job_mutation_matrix"
SUITE_MATRIX = f"{JOBS}::test_the_attestation_suite_rule_mutation_matrix"
AGG_MATRIX = f"{JOBS}::test_the_attestation_aggregate_mutation_matrix"
SA10_TABLE = "specs/evidence/0013/sa10_mutants.py::MUTANTS"
PA1_TABLE = "specs/evidence/0013/mutation-table.json::rows"

CARRIERS = {
    # (invariant, phrase index) -> ("mutant", id) | ("cite", "<file>::<matrix>::<row>") | ("absent", reason, cell)
    ("INV-SA1", 0): ("mutant", "sa1-skip-verification-when-attested"),
    ("INV-SA1", 1): ("mutant", "sa1-open-decides-shape-first", "sa1-preflight-decides-shape-first"),
    ("INV-SA2", 0): ("mutant", "sa2-reproduction-alone"),
    ("INV-SA2", 1): ("mutant", "sa2-probes-alone"),
    ("INV-SA2", 2): ("mutant", "sa2-exception-verified"),
    ("INV-SA3", 0): ("mutant", "sa3-digests-only"),
    ("INV-SA3", 1): ("mutant", "sa3-against-own-manifestation"),
    ("INV-SA4", 0): ("mutant", "sa4-drop-a-near-miss"),
    ("INV-SA4", 1): ("mutant", "sa4-equal-near-miss-passes"),
    ("INV-SA5", 0): ("mutant", "sa5-the-withdrawn-union"),
    ("INV-SA6", 0): ("mutant", "sa6-refuse-a-second-key"),
    ("INV-SA6", 1): ("mutant", "sa6-accept-a-conflicting-pair"),
    ("INV-SA6", 2): ("cite", f"{AGG_MATRIX}::different evidence emitted"),
    ("INV-SA6", 3): ("cite", f"{AGG_MATRIX}::compare provenance as evidence (INV-SA6: two agreeing jobs become a false "
                             f"conflict)"),
    ("INV-SA6", 4): ("cite", f"{JOB_MATRIX}::timings in the digest"),
    ("INV-SA6", 5): ("cite", f"{JOB_MATRIX}::drop the job-state assertion (INV-SA6)"),
    ("INV-SA6", 6): ("cite", f"{JOB_MATRIX}::the suite's module set unchecked"),
    ("INV-SA6", 7): ("mutant", "sa6-a-rewrite-class-skip-left"),
    ("INV-SA6", 8): ("cite", f"{WRITER_MATRIX}::replace whatever the commit order (v18's behaviour, INV-SA6)"),
    ("INV-SA6", 9): ("cite", f"{WRITER_MATRIX}::any nonzero --is-ancestor read as 'not an ancestor'"),
    ("INV-SA6", 10): ("cite", f"{WRITER_MATRIX}::shallow check after the ancestry"),
    ("INV-SA6", 11): ("cite", f"{WRITER_MATRIX}::same-commit step after --is-ancestor"),
    ("INV-SA6", 12): ("cite", f"{WRITER_MATRIX}::compare provenance as evidence when ordering writes (INV-SA6)"),
    # ---- v21, the attestation bootstrap (Quentin, 2026-10-27: "Two runs, bootstrap") --------------------------------
    ("INV-SA6", 13): ("cite", f"{JOB_MATRIX}::the bootstrap exemption covers a second node (v21)"),
    ("INV-SA6", 14): ("cite", f"{JOB_MATRIX}::the bootstrap exemption at a non-zero-current state (v21)"),
    ("INV-SA6", 15): ("cite", f"{JOB_MATRIX}::the bootstrap exemption only when the artifact is empty (v21)"),
    ("INV-SA6", 16): ("cite", f"{JOB_MATRIX}::the bootstrap exemption covers an <error> (v21)"),
    ("INV-SA6", 17): ("cite", f"{WRITER_MATRIX}::a fresh write drops a non-bootstrap record (v21)"),
    ("INV-SA6", 18): ("cite", f"{WRITER_MATRIX}::a fresh write accepts a bootstrap-pending job (v21)"),
    ("INV-SA6", 19): ("cite", f"{WRITER_MATRIX}::an unanswerable bootstrap derivation read as not bootstrap (v21)"),
    ("INV-SA6", 20): ("mutant", "sa6-ship-a-bootstrap-record"),
    # ---- v22, what CI run 1 found (Quentin, 2026-10-27: "Adopt v22 now (Recommended)") -------------------------
    ("INV-SA6", 21): ("cite", f"{SUITE_MATRIX}::the joint-group closure dropped (v22)"),
    ("INV-SA6", 22): ("cite", f"{JOB_MATRIX}::unattestable decided before --check-evidence (v22)"),
    ("INV-SA6", 23): ("cite", f"{JOB_MATRIX}::an unreadable key ends the job red (v22)"),
    ("INV-SA6", 24): ("cite", f"{WRITER_MATRIX}::the bootstrap mark derived by a test other than the exemption's (v22)"),
    ("INV-SA6", 25): ("cite", f"{WRITER_MATRIX}::a fresh write accepts a new bootstrap record (v22)"),
    # (v23) the round-3 verdict: SA-R3-02, SA-R3-03 (and research's _head sibling), SA-R3-04
    ("INV-SA6", 26): ("cite", f"{JOB_MATRIX}::the shipped rule: modules compared, nodes not (SA-R3-02)"),
    ("INV-SA6", 27): ("cite", f"{JOB_MATRIX}::the environment is not checked (SA-R3-02: an inherited PYTEST_ADDOPTS or PYTHONPATH reaches the suite)"),
    ("INV-SA6", 28): ("cite", f"{JOB_MATRIX}::the shipped rule: pytest's exit status discarded (SA-R3-03)"),
    ("INV-SA6", 29): ("cite", f"{JOB_MATRIX}::git's exit code dropped (_head)"),
    ("INV-SA6", 30): ("cite", f"{WRITER_MATRIX}::fresh refuses no future or malformed record (another key's is erased; the same key's reads as S75)"),
    ("INV-SA6", 31): ("cite", f"{WRITER_MATRIX}::fresh skips the dry run over the original artifact (v19's order is not applied)"),
    ("INV-SA6", 32): ("cite", f"{WRITER_MATRIX}::the superseded implementation: fresh checks only current records, then clears the list"),
    ("INV-SA12", 12): ("mutant", "sa12-pt-interp-from-a-fixed-window"),
    ("INV-SA12", 13): ("mutant", "sa12-a-short-segment-read-as-a-name"),
    ("INV-SA7", 0): ("mutant", "sa7-warn-on-every-open"),
    ("INV-SA7", 1): ("mutant", "sa7-warn-on-an-attested-build"),
    ("INV-SA7", 2): ("mutant", "sa7-never-warn"),
    ("INV-SA8", 0): ("mutant", "sa8-a-file-outside-the-wheel"),
    ("INV-SA8", 1): ("mutant", "sa8-omit-the-step"),
    ("INV-SA9", 0): ("mutant", "sa9-report-after-opening"),
    ("INV-SA9", 1): ("mutant", "sa9-verified-at-warn"),
    ("INV-SA11", 0): ("mutant", "sa11-omit-the-key"),
    ("INV-SA11", 1): ("mutant", "sa11-attested-on-a-verified-build"),
    ("INV-SA11", 2): ("absent", "no schema version stores a SQLite build identity, so there is no store-side value the "
                                "audit could read in place of its measurement", R(
                                    "test_the_store_records_no_sqlite_build_so_the_audit_can_only_measure")),
    ("INV-SA12", 0): ("mutant", "sa12-version-and-source-id-alone"),
    ("INV-SA12", 1): ("mutant", "sa12-omit-compile-options"),
    ("INV-SA12", 2): ("mutant", "sa12-options-in-returned-order"),
    ("INV-SA12", 3): ("mutant", "sa12-options-from-another-read"),
    ("INV-SA12", 4): ("mutant", "sa12-drop-machine"),
    ("INV-SA12", 5): ("mutant", "sa12-drop-system"),
    ("INV-SA12", 6): ("mutant", "sa12-drop-libc"),
    ("INV-SA12", 7): ("mutant", "sa12-libc-from-libc-ver"),
    ("INV-SA12", 8): ("mutant", "sa12-machine-from-the-runner-label"),
    ("INV-SA12", 9): ("mutant", "sa12-canonicalise-one-side"),
    ("INV-SA12", 10): ("mutant", "sa12-widen-the-alias-map"),
    ("INV-SA12", 11): ("mutant", "sa12-unreadable-matches"),
    # ---- INV-SA10 (0013 §5f.4), research's scope ruling: one carrier per phrase -------------------------------------
    ("INV-SA10", 0): ("cite", f"{SA10_TABLE}::tree-unmapped-write"),
    ("INV-SA10", 1): ("cite", f"{SA10_TABLE}::tree-unreached-write"),
    ("INV-SA10", 2): ("mutant", "sa10-narrow-the-site-scope"),
    ("INV-SA10", 3): ("cite", f"{SA10_TABLE}::exact-one-relaxed"),
    ("INV-SA10", 4): ("cite", f"{PA1_TABLE}::del-stamp"),
    ("INV-SA10", 5): ("mutant", "sa10-a-vacuous-postcondition"),
    ("INV-SA10", 6): ("mutant", "sa10-a-step-with-no-matcher"),
    ("INV-SA10", 7): ("cite", f"{SA10_TABLE}::tree-undeclared-ddl"),
    ("INV-SA10", 8): ("mutant", "sa10-skip-the-byte-match-unattested"),
    ("INV-SA10", 9): ("mutant", "sa10-commit-before-revalidating"),
    ("INV-SA10", 10): ("mutant", "sa10-verified-takes-fewer-checks"),
    ("INV-SA10", 11): ("cite", f"{SA10_TABLE}::N13-N15-forward-unknown-attributes"),
    # ---- 0013 v37 §5f.1: the pre-3.41 declare_vtab sequence -----------------------------------------------------------
    ("INV-SA10", 12): ("cite", f"{SA10_TABLE}::v37-filter-without-the-probe"),
    ("INV-SA10", 13): ("cite", f"{SA10_TABLE}::v37-a-loose-sequence"),
    ("INV-SA10", 14): ("cite", f"{SA10_TABLE}::v37-a-second-use"),
    ("INV-SA10", 15): ("cite", f"{SA10_TABLE}::v37-outside-a-prepare"),
    ("INV-SA10", 16): ("cite", f"{SA10_TABLE}::v37-no-change-dropped"),
    # (v38) the round-3 verdict, SA-R3-01, and research's stage-1 siblings: the census's input surface
    ("INV-SA10", 17): ("cite", f"{SA10_TABLE}::sa-r3-01-connect-forwards-the-callers-arguments"),
    ("INV-SA10", 18): ("cite", f"{SA10_TABLE}::sa-r3-01-the-seam-forwards-the-module"),
    ("INV-SA10", 19): ("cite", f"{SA10_TABLE}::sa-r3-01-set-values-unchecked"),
    ("INV-SA10", 20): ("cite", f"{SA10_TABLE}::sa-r3-01-replay-runs-recorded-behaviour"),
}
"""Every phrase's ONE carrier (an INV-SA1 phrase spans both gate sites, so it names two mutants)."""


# ---- the phrases, from the spec text ----------------------------------------------------------------------------------
_MARKER = re.compile(r"\*\*\((?:v[0-9.]+)\)\*\*\s*")


def _split_depth0(text, sep):
    out, depth, cur = [], 0, []
    for ch in text:
        depth += ch == "("
        depth -= ch == ")"
        if ch == sep and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def _first_sentence(text):
    depth = 0
    for i, ch in enumerate(text):
        depth += ch == "("
        depth -= ch == ")"
        if ch == "." and depth == 0 and text[i + 1:i + 2] == " " and text[i + 2:i + 3].isupper():
            return text[:i]
    return text


def phrases(root: pathlib.Path = ROOT) -> dict:
    """{(invariant, index): phrase}: §4g.8's and 0013 §5f.4's "mutant that must fail" cells."""
    out = {}
    for spec in (SPEC_0007, SPEC_0013):
        for line in (root / spec).read_text(encoding="utf-8").splitlines():
            m = re.match(r"\| \*\*(INV-SA\d+)\*\* \|", line)
            if not m:
                continue
            cells = [c.strip() for c in line.split("|")]
            if len(cells) < 4 or (m.group(1), 0) in out:
                continue
            cell = _MARKER.sub("", _first_sentence(cells[3]))
            for i, p in enumerate(q.strip() for q in _split_depth0(cell, ";")):
                out[(m.group(1), i)] = p
    return out


def cited_rows(root: pathlib.Path = ROOT, ref: str = "") -> set:
    """The row names a citation's matrix carries, read from the matrix itself (AST or JSON), never grepped."""
    path, matrix = ref.split("::")[0], ref.split("::")[1]
    text = (root / path).read_text(encoding="utf-8")
    if path.endswith(".json"):
        return {r["id"] for r in json.loads(text, object_pairs_hook=_strict_pairs)[matrix]}
    tree = ast.parse(text)
    if matrix == "MUTANTS":
        # EVERY `MUTANTS = …` and `MUTANTS += […]` at module level (sa10_mutants extends its list for v37): a reader that
        # saw only the first assignment would read later rows as missing, or worse, miss a removed one
        names = set()
        for n in tree.body:
            target = n.targets[0] if isinstance(n, ast.Assign) else n.target if isinstance(n, ast.AugAssign) else None
            if getattr(target, "id", "") != "MUTANTS":
                continue
            if isinstance(n.value, ast.Dict):
                names |= {k.value for k in n.value.keys}
            else:
                names |= {e.elts[0].value for e in n.value.elts}
        return names
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == matrix:
            for c in ast.walk(n):
                if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "_matrix":
                    return {k.value for k in c.args[2].keys}
    return set()


def carrier_problems(root: pathlib.Path = ROOT) -> list:
    """The complement check (research's I6 Q2): the spec's phrase set EQUALS the carriers' key set, and each carrier
    resolves (a mutant of this table, a row of the cited matrix, or an ABSENT cell that exists)."""
    ph, out = phrases(root), []
    ids = {m[0] for m in MUTANTS}
    out += [f"{k[0]} phrase {k[1]} has no carrier: {ph[k]!r}" for k in sorted(set(ph) - set(CARRIERS))]
    out += [f"{k[0]} carrier {k[1]} has no phrase in the spec" for k in sorted(set(CARRIERS) - set(ph))]
    used = set()
    for k, c in sorted(CARRIERS.items()):
        if c[0] == "mutant":
            for mid in c[1:]:
                used.add(mid)
                if mid not in ids:
                    out.append(f"{k[0]} phrase {k[1]}: no mutant {mid!r} in this table")
        elif c[0] == "cite":
            ref, row = c[1].rsplit("::", 1)
            if row not in cited_rows(root, ref):
                out.append(f"{k[0]} phrase {k[1]}: {ref} has no row {row!r}")
        elif c[0] == "absent":
            f, name = c[2].split("::")[0], c[2].split("::")[-1].split("[")[0]
            if f"{f}::{name}" not in SUBJECT_P.defined_tests(root) and name not in (root / f).read_text():
                out.append(f"{k[0]} phrase {k[1]}: the ABSENT cell {c[2]} does not exist")
        else:
            out.append(f"{k[0]} phrase {k[1]}: carrier kind {c[0]!r} is not mutant/cite/absent")
    out += [f"mutant {m} carries no phrase" for m in sorted(ids - used)]
    return out


SUBJECT_P = _protocol.Subject(
    spec="0007", finding=SUBJECT, table=TABLE, digested=DIGESTED, mutants=MUTANTS, controls=CONTROLS,
    import_modules=("veracium.store.schema_version", "veracium.store.migration", "veracium.store.release_migration",
                    "veracium.doctor", "veracium.store.near_misses"),
    import_specs=(SE, GATE_FILE), cells_files=(RS, SVT, SM, JOBS, WRITER, PA1_CELLS, SA10_CELLS),
    kinds=("product",))


def problems(path: pathlib.Path = TABLE, root: pathlib.Path = ROOT) -> list:
    return carrier_problems(root) + SUBJECT_P.problems(path, root)


definition_sha = _protocol.definition_sha
canonical = _protocol.canonical
render = _protocol.render
_digests = SUBJECT_P.digests


def main() -> int:
    if "--phrases" in sys.argv:
        for k, p in sorted(phrases().items()):
            print(f"{k[0]:9s} {k[1]:2d}  {CARRIERS.get(k, ('MISSING',))[0]:7s}  {p}")
        return 0
    bad = carrier_problems()
    if bad and "--write" in sys.argv:
        for b in bad:
            print(f"CARRIER: {b}")
        return 1
    if "--check" in sys.argv or len(sys.argv) == 1:
        probs = problems()
        for b in probs:
            print(f"STALE: {b}")
        return 1 if probs else 0
    return SUBJECT_P.main(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
