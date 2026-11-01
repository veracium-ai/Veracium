#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0007_closure_mutants.py::test_the_table_check_refuses_each_tampered_table
"""The SQLite attestation amendment's CODE closures (0007 §4g; its external rounds 1-5): each finding killed by its cells.

tests/test_closure_mutants.py's rule, at the acceptance fold: a code finding raised on or after its date closes only
with a mutant that the closure row's cited cells kill, in a table declaring spec 0007 and that finding. One table per
finding (the protocol binds one finding per table), at specs/evidence/0007/closure/<id>/mutation-table.json, each run
by the shared protocol (specs/evidence/mutation_protocol.py) on a copy of the tracked tree.

Each finding's first mutant is ITS SUPERSEDED IMPLEMENTATION, re-expressed as the smallest edit that restores the
defect on today's code; the rest are the siblings its closure named. The definitions are the in-test matrices' own
(tests/test_0007_attestation_jobs.py's job matrix, tests/test_0007_attestation_writer.py's MUTANTS, INV-SA10's rows in
specs/evidence/0013/sa10_mutants.py, imported by id), so a closure is proven by the edit its matrix already kills,
now run as a separate process against the named cells. Per mutated file, a NO-OP control whose cells must all pass.

SA-R3-C1's fix was a FIXTURE (the synthetic job cases pass a non-root euid explicitly), so its mutant edits the test
helper and its cell simulates the reviewer's root host (os.geteuid patched to 0): the restored default reads the host.

    $PY specs/evidence/0007/closure_mutants.py --check [ID ...]     # fast: every table current, every row good
    TMPDIR=/dev/shm $PY specs/evidence/0007/closure_mutants.py --write [ID ...]
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import mutation_protocol as _protocol  # noqa: E402

SELF = "specs/evidence/0007/closure_mutants.py"
TABLES = HERE / "closure"
JOB = "specs/attestation_job.py"
WRITER = "specs/attestation_writer.py"
SKIP = "specs/skip_inventory.py"
GATE = "specs/evidence/0013/sa10_gate.py"
SA10 = "specs/evidence/0013/sa10_mutants.py"
AMATRIX = "specs/evidence/0013/a_matrix_mutants.py"
SA = "specs/evidence/0007/sa_mutants.py"
SPEC13 = "specs/0013-store-migrations.md"
C1_CELL = "tests/test_0007_sa_r1_c1_census_scopes.py::test_sa_r1_c1_the_two_censuses_keep_their_own_scope_and_counts"
_C1_LEAD = "  are two censuses, each with its own fixture scope (v0.12, C1):\n"
_STEP_SCOPE = ("  - **The step table's census** covers its 49 native ladder entries, HEAD drift repair included (its 49 orchestrator\n"
               "    entries carry no write arrays).")
_PA1_CENSUS = ("  - **0013-PA1's census** covers the 48 fixtures the gate runs over, which add qualifying arity and notice rows. 513\n"
               "    non-DDL writes each match exactly one step, and none is unmapped or ambiguous. There are 1,645 DDL writes, all from\n"
               "    `_apply_forward`, none from `_repair_drift`.\n")
JT = "tests/test_0007_attestation_jobs.py"
WT = "tests/test_0007_attestation_writer.py"
ST = "tests/test_spec_gate.py"
GT = "tests/test_0013_sa10_gate.py"
COMMON = ("specs/evidence/mutation_protocol.py", _protocol.KINDS, SELF)


SOURCES = {}


def _source(rel):
    """Another table's runner, loaded once; its mutants are reused BY ID, so their definition digests are its own."""
    if rel not in SOURCES:
        spec = importlib.util.spec_from_file_location("veracium_closure_src_" + pathlib.Path(rel).stem, ROOT / rel)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        SOURCES[rel] = m
    return SOURCES[rel]


def _rows(rel, ids):
    by_id = {r[0]: r for r in _source(rel).MUTANTS}
    missing = [i for i in ids if i not in by_id]
    assert not missing, f"{rel} has no mutant {missing}"
    return [by_id[i] for i in ids]


J = lambda name: f"{JT}::{name}"                                                       # noqa: E731
W = lambda name: f"{WT}::{name}"                                                       # noqa: E731
S = lambda name: f"{ST}::{name}"                                                       # noqa: E731
JUNIT = lambda f: J(f"test_r5_f3_an_unreadable_junit_is_suite_mismatch[{f}]")          # noqa: E731
ROWS5 = lambda r: J(f"test_r4_01_the_reviewers_five_rows[{r}]")                        # noqa: E731
COMPL = lambda k: J(f"test_r4_01_the_completion_record_must_be_this_runs_and_agree[{k}]")   # noqa: E731
LIVE = lambda m: J(f"test_the_real_suite_process_is_bound_by_its_collection_and_its_exit_status[{m}]")  # noqa: E731
R402 = lambda c: W(f"test_r4_02_the_reviewers_rows_in_both_modes[{c}]")               # noqa: E731
FRESH = lambda c: W(f"test_real_a_fresh_write_erases_no_future_or_malformed_record_of_any_key[{c}]")  # noqa: E731
EXIT1 = J("test_pytests_exit_status_must_agree_with_its_junit[1-False-failed-tests-session-level failure]")
MULTI = J("test_the_junit_must_equal_the_invocations_own_collection_as_a_multiset[missing]")
ENV_O = J("test_an_environment_that_shapes_pytest_refuses_the_job_before_anything_runs[PYTEST_ADDOPTS--o python_functions=test_first]")
ENV_P = J("test_an_environment_that_shapes_pytest_refuses_the_job_before_anything_runs[PYTHONPATH-/elsewhere]")
DUP = W("test_r4_02_a_conflicting_duplicate_in_the_original_refuses_a_fresh_write")
V19 = W("test_real_a_fresh_write_keeps_v19s_order")
ROOT_JOB = J("test_a_root_job_is_a_named_failure_before_anything_runs")
ROOT_HOST = J("test_r3_c1_a_synthetic_case_reaches_its_outcome_on_a_root_host")
EMITS = S("test_every_skip_site_reconciles_as_pytest_emits_it")
LOGS = S("test_reconcile_accepts_the_reviewers_git_less_and_root_logs")
BITES = S("test_the_emitted_reason_gate_bites_on_each_missing_alias")
UNRENDERED = S("test_the_emitted_reason_gate_refuses_a_reason_it_cannot_render")
DIFFERS = S("test_reconcile_handles_an_emitted_reason_that_differs_from_its_source_token")

_READ = "CHILD_READ_ERRORS = (OSError, ValueError, RecursionError, ET.ParseError, LookupError)"
_ORIGINALS = "        bad = sv.attestation_artifact_problems(records)\n"
_FRESH_REV = '            if rev in ("future", "malformed"):\n'
_DRY_RUN = "        probe = list(records)\n        for new in news:\n            probe, _ = merged(probe, new, repo=repo, git=git)\n"
_C2_ALIASES = [(f'    ("{f}", "{tok}"):\n        ("{why}",),\n', "") for f, tok, why in (
    ("tests/test_0044_v1_readonly_db.py", "geteuid", "root writes a read-only file"),
    ("tests/test_0013_pa1_campaign.py", "not _is_checkout()", "a git-less copy has none"),
    ("tests/test_0041_mutation_campaign.py", "not _is_checkout()", "a git-less copy has none"),
    ("tests/test_0043_mutation_campaign.py", "not _is_checkout()", "a git-less copy has none"),
    ("tests/test_0042_scope_resolution.py", "sys.version_info < (3, 11)", "which 3.10 does not record"))]

# finding: (the commit that fixed it, [mutants], [(file, no-op anchor)], the runner whose import probe it takes).
# A mutant is the protocol's 8-tuple. Round 1's three design findings are proven by the implementation mutants the
# finding itself asked for, reused by id: SA-R1-01 "a negative cell for the supplied drop/recreate case" (INV-SA10's
# N1-N3); SA-R1-02 "a finite acceptance matrix" (0013's A-matrix); SA-R1-03 "a mutant that drops architecture while
# all other fields remain equal" (INV-SA12's).
FINDINGS = {
    "SA-R1-01": ("81c6512", _rows(SA10, ["N1-site-admits-schema-writes", "N2-b1-by-prefix", "N3-b2-every-index",
                                          "N2-row-count-postcondition"]),
                 [(GATE, "def constructor_problems(")], SA10),
    "SA-R1-02": ("81c6512", _rows(AMATRIX, ["a1-require-a-record", "a3-runtime-status-alone", "a5-confinement-first",
                                             "p1-runtime-supported-as-the-gate"]),
                 [("specs/migrations_0013.py", "def _draft("), ("src/veracium/store/schema_version.py", "def runtime_status(")],
                 AMATRIX),
    "SA-R1-03": ("81c6512", _rows(SA, ["sa12-drop-machine", "sa12-canonicalise-one-side"]),
                 [("src/veracium/store/schema_version.py", "def canonical_machine(")], SA),
    "SA-R1-C1": ("81c6512", [
        ("c1-the-two-censuses-folded-into-one", "text", SPEC13,
         [(_C1_LEAD, "  is one census:\n"), (_STEP_SCOPE, "  - **The census** covers the ladder."), (_PA1_CENSUS, "")],
         [C1_CELL], [], None,
         "the conflation round 1 named: one census carrying the step table's 432/1,685, its scope unstated, and the "
         "48 PA1 fixtures' own scope and figures gone"),
    ], [(SPEC13, _C1_LEAD)], None),
    "SA-R1-C2": ("870aed0", [
        ("c2-the-five-aliases-removed", "product", SKIP, _C2_ALIASES, [EMITS, LOGS], [DIFFERS], None,
         "the superseded inventory: EMITTED without the five aliases, so a git-less tree and a root host each report a "
         "listed skip as unlisted"),
        ("c2-the-emitted-reason-gate-disabled", "product", SKIP,
         [('    return problems + reconcile("\\n".join(lines))\n', "    return []\n")], [BITES, UNRENDERED], [DIFFERS],
         None, "the class check removed: every alias is again one host's hand fix, and an unrenderable reason passes"),
    ], [(SKIP, "def emitted_reason_problems(root) -> list:")], None),
    "SA-R3-01": ("95c207c", _rows(SA10, ["sa-r3-01-connect-forwards-the-callers-arguments",
                                          "sa-r3-01-the-seam-forwards-the-module", "sa-r3-01-set-values-unchecked",
                                          "sa-r3-01-replay-runs-recorded-behaviour"]),
                 [(GATE, "def connect_args_problem(")], SA10),
    "SA-R3-02": ("95c207c", [
        ("r3-02-modules-compared-nodes-not", "product", JOB,
         [("            mismatch = node_problems(cases, collected)\n", "            mismatch = []\n")],
         [MULTI, LIVE("deselect")], [LIVE("control")], None,
         "the superseded rule: the JUnit's modules compared with the rule's, its nodes never compared with the "
         "invocation's own collection"),
        ("r3-02-the-environment-not-checked", "product", JOB, [(" or environment_problem(environ)\n", "\n")],
         [ENV_O, ENV_P], [LIVE("control")], None,
         "an inherited PYTEST_ADDOPTS or PYTHONPATH reaches the suite (the reviewer's deselect route)"),
    ], [(JOB, "def node_problems(")], None),
    "SA-R3-03": ("95c207c", [
        ("r3-03-pytests-exit-status-discarded", "product", JOB,
         [("            bad = exit_problem(rc, cases)\n", "            bad = None\n")],
         [EXIT1, LIVE("session-finish-raise")], [LIVE("control")], None,
         "the superseded decide: run_suite's return discarded, so a pytest that exited 1 after an all-pass JUnit is "
         "evidence"),
    ], [(JOB, "def exit_problem(")], None),
    "SA-R3-04": ("95c207c", [
        ("r3-04-fresh-checks-only-current-then-clears", "product", WRITER,
         [(_FRESH_REV, "            if False:\n"), (_DRY_RUN, "")],
         [FRESH("same-key-future"), V19], [R402("valid-bootstrap-fresh")], None,
         "the superseded fresh write: no future or malformed record refuses, and v19's order is never applied"),
    ], [(WRITER, "def write_records(")], None),
    "SA-R3-C1": ("95c207c", [
        ("r3-c1-the-synthetic-euid-read-from-the-host", "fixture", JT,
         [("            suite_rc=None, collected=None, euid=1000, environ=None,",
           "            suite_rc=None, collected=None, euid=None, environ=None,")],
         [ROOT_HOST], [ROOT_JOB], None,
         "the superseded fixture: a synthetic job case takes the host's euid, so on the reviewer's root host it is "
         "wrong-job-state instead of the behaviour it tests"),
    ], [(JT, "def _decide(")], None),
    "SA-R4-01": ("c0a1ace", [
        ("r4-01-the-completion-record-ignored", "product", JOB,
         [("            bad = completion_problem(completion_path(junit), rc, nonce)\n", "            bad = None\n")],
         [ROWS5("bootstrap+session-raise"), COMPL("absent")], [ROWS5("passing-control")], None,
         "the superseded decide: the exempt bootstrap failure explains exit 1 whether or not pytest.main returned"),
        ("r4-01-pytest-main-status-not-compared", "product", JOB,
         [('    if type(rec["exit_status"]) is not int or rec["exit_status"] != rc:\n',
           '    if type(rec["exit_status"]) is not int:\n')],
         [COMPL("status")], [ROWS5("passing-control")], None, "a completion record whose status disagrees stands"),
        ("r4-01-the-nonce-not-checked", "product", JOB,
         [('    if rec["nonce"] != nonce:\n', "    if False:\n")],
         [COMPL("stale")], [ROWS5("passing-control")], None, "a stale run's completion record stands"),
    ], [(JOB, "def completion_problem(")], None),
    "SA-R4-02": ("c0a1ace", [
        ("r4-02-the-original-records-unvalidated", "product", WRITER, [(_ORIGINALS, "        bad = []\n")],
         [R402(f"same-key-{c}-fresh") for c in ("bad-digest", "missing-confinement", "false-probe", "extra-field")]
         + [DUP], [R402("valid-bootstrap-fresh")], None,
         "the superseded fresh write: a same-key current record the production validator rejects is replaced, "
         "never refused"),
        ("r4-02-per-record-validation-only", "product", WRITER,
         [(_ORIGINALS, "        bad = [q for x in records if sv.attestation_revision(x) == 'current' "
                       "for q in sv.attestation_record_problems(x)]\n")],
         [DUP], [R402("valid-bootstrap-fresh")], None,
         "per-record validation without the artifact-level check: a conflicting duplicate passes"),
    ], [(WRITER, "def write_records(")], None),
    "SA-R5-C1": ("b718f43", [
        ("r5-c1-lookup-error-escapes-the-junit-read", "product", JOB,
         [(_READ, "CHILD_READ_ERRORS = (OSError, ValueError, RecursionError, ET.ParseError)")],
         [JUNIT("unknown-encoding"), JUNIT("bytes-codec")], [JUNIT("truncated")], None,
         "the superseded read boundary: an XML declaration naming no text codec raises LookupError out of decide"),
    ], [(JOB, "CHILD_READ_ERRORS = (")], None),
}


def _noop(fid, rel, anchor, mutants):
    note = "<!-- no-op control: a comment, no behaviour -->\n" if rel.endswith(".md") else "# no-op control: a comment, no behaviour\n"
    return (f"NOOP-{fid}-{pathlib.Path(rel).stem}", rel, [(anchor, note + anchor)],
            sorted({c for m in mutants if m[2] == rel for c in m[4]}),
            f"a comment before {anchor.strip()!r}: the bytes change, the behaviour does not", "SURVIVED")


def subject(fid: str) -> "_protocol.Subject":
    _fix, mutants, noops, src = FINDINGS[fid]
    files = sorted({m[2] for m in mutants})
    cells = sorted({n.split("::")[0] for m in mutants for n in (*m[4], *m[5])})
    source = _source(src).SUBJECT_P if src else None
    return _protocol.Subject(
        spec="0007", finding=fid, table=TABLES / fid / "mutation-table.json",
        digested=tuple(dict.fromkeys((*files, *cells, *((src,) if src else ()), *COMMON))), mutants=mutants,
        controls=[_noop(fid, rel, anchor, mutants) for rel, anchor in noops],
        import_modules=source.import_modules if source else (),
        import_specs=source.import_specs if source else tuple(f for f in files if f.endswith(".py") and not f.startswith("tests/")),
        cells_files=tuple(cells), kinds=tuple(sorted({m[1] for m in mutants})))


SUBJECTS = {fid: subject(fid) for fid in FINDINGS}
canonical = _protocol.canonical
render = _protocol.render


def problems(root: pathlib.Path = ROOT) -> list:
    out = []
    for fid, s in SUBJECTS.items():
        out += [f"{fid}: {p}" for p in s.problems(root=root)]
    found = sorted(p.parent.name for p in TABLES.glob("*/mutation-table.json"))
    if found != sorted(SUBJECTS):
        out.append(f"the tables on disk {found} are not one per finding {sorted(SUBJECTS)}")
    return out


def main(argv=None) -> int:
    argv = sys.argv if argv is None else argv
    ids = [a for a in argv[1:] if not a.startswith("--")] or list(SUBJECTS)
    unknown = sorted(set(ids) - set(SUBJECTS))
    if unknown:
        print(f"unknown finding(s): {unknown}")
        return 2
    if "--write" in argv or "--try" in argv:
        TABLES.mkdir(exist_ok=True)
        rc = 0
        for fid in ids:
            (TABLES / fid).mkdir(exist_ok=True)
            print(f"== {fid}", flush=True)
            mode = "--write" if "--write" in argv else "--try"
            rest = [] if mode == "--write" else [m[0] for m in SUBJECTS[fid].mutants] + [k[0] for k in SUBJECTS[fid].controls]
            rc |= SUBJECTS[fid].main([argv[0], mode, *rest])
        return rc
    bad = problems()
    for b in bad:
        print(f"STALE: {b}")
    if not bad:
        print(f"{len(SUBJECTS)} closure tables current, every row good")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
