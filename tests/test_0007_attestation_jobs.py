"""0007 §4d (I5): the actual attestation jobs — the committed suite rule, one job's closed outcome, aggregation within
one CI run, the matrix's one carrier (rows.json) and the workflow that reads it, and the pinned dependency set.
Research's stage-1 read of I5 (BLOCKING 1–4, Q2/Q4/Q5a/Q6a) is asserted cell by cell, and each artifact carries a
mutation matrix (P1) in the writer's form: each mutant killed BY ASSERTION in a named cell, control first and last.
"""
from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import pathlib
import subprocess
import sys
import types
from types import SimpleNamespace

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
ATT = SPECS / "evidence" / "attestation"
sys.path.insert(0, str(SPECS))


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


suite_rule = _load(SPECS / "attestation_suite.py", "veracium_attestation_suite")
job = _load(SPECS / "attestation_job.py", "veracium_attestation_job")
agg = _load(SPECS / "attestation_aggregate.py", "veracium_attestation_aggregate")
cons = _load(SPECS / "attestation_constraints.py", "veracium_attestation_constraints")
import skip_inventory  # noqa: E402

sv = agg.sv

OTHER_MACHINE = "ppc64le" if sv.canonical_platform()["machine"] == "riscv64" else "riscv64"
"""A canonical machine that is NOT this build's (0007 CI run 1, 2026-10-27): "another key" made with a fixed
`aarch64` was this build's own key on arm64 runners, and `libc="musl"` was non-canonical beside Darwin, so cells meant
to hold two keys held one, or a malformed record, off x86_64 Linux."""



# ---- Q1: the suite rule ----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("source", [
    "import sqlite3",
    "import sqlite3 as db",
    "import sqlite3.dbapi2",
    "from sqlite3 import connect",
    "from veracium.store import schema_version",
    "from veracium.store.migration import migrate",
    "from veracium.store import release_migration as rm",
    "def f():\n    import schema_evidence",
    "try:\n    import migrations_0013\nexcept ImportError:\n    pass",
    "class T:\n    def m(self):\n        from veracium.store.schema_version import SCHEMA_VERSION",
    "spec_from_file_location('m', ROOT / 'specs' / 'migrations_0013.py')",
    "runpy.run_path(path='specs/schema_evidence.py')",
    "subprocess.run([sys.executable, f'{SPECS}/schema_evidence.py', '--check'])",
])
def test_the_rule_admits_each_root_by_import_at_any_depth_or_by_file_inside_a_call(source):
    assert suite_rule.reasons(source), source


@pytest.mark.parametrize("source", [
    "import veracium.store",                         # the package, not a root
    "from veracium import store",                    # imports veracium.store, not a root
    "from . import schema_version",                  # relative: not this rule's module name
    "from .sqlite3 import connect",                  # relative, even when its tail names a root
    "import sqlite3x",                               # a prefix of a NAME is not a submodule
    "X = 'specs/schema_evidence.py'",                # a literal outside any call's arguments
    "def f():\n    '''loads migrations_0013.py by path'''",
    "pytest.skip",                                   # an attribute, no call
])
def test_the_rule_admits_nothing_else(source):
    assert suite_rule.reasons(source) == [], source


def test_the_rule_agrees_with_researchs_frozen_implementation_at_this_tree():
    """Two implementations of ONE rule (research's suite_rule_v2.py, frozen at its pin, and the product script); a
    divergence is a finding in one of them. Research's reads `from p import x` only as `p` or `p.x` against the roots
    exactly, the product's as a root or its submodule; no module of this tree tells them apart, which this cell
    asserts."""
    frozen = SPECS / "evidence" / "0007-sqlite-attestation" / "r1-repro-at-58dd7f6" / "suite_rule_v2.py"
    p = subprocess.run([sys.executable, "-I", str(frozen), str(ROOT)], capture_output=True, text=True, check=True)
    theirs = [line.split(" ", 1)[0] for line in p.stdout.splitlines() if line.strip()]
    selected = sorted(str(f.relative_to(ROOT)) for f in (ROOT / "tests").rglob("test_*.py")
                      if suite_rule.reasons(f.read_text(encoding="utf-8")))
    assert theirs == selected                        # the rule itself, before v22's joint-group closure
    assert len(theirs) == int(p.stderr.split("TOTAL")[-1].strip())


def _groups_tree(tmp_path, rows):
    """A planted tree: the groups document with `rows`, and the modules they and the rule name."""
    (tmp_path / "specs" / "evidence" / "offline").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "specs" / "evidence" / "offline" / "JOINT-TEST-GROUPS.md").write_text("\n".join(rows) + "\n")
    (tmp_path / "tests" / "test_root.py").write_text("import sqlite3\n")
    (tmp_path / "tests" / "test_partner.py").write_text("x = 1\n")
    (tmp_path / "tests" / "test_alone.py").write_text("y = 1\n")
    return tmp_path


def test_the_joint_group_parser_refuses_a_missing_member_and_moves_with_the_document(tmp_path):
    """Research's stage-2 (b), on planted trees: a member this tree lacks refuses (it would close over nothing); a group
    of one changes nothing; a group added to the DOCUMENT grows the suite with no code change."""
    t = _groups_tree(tmp_path / "a", ["| members | `tests/test_root.py` AND `tests/test_gone.py` |"])
    with pytest.raises(ValueError, match="does not have"):
        suite_rule.suite(t)
    t = _groups_tree(tmp_path / "b", ["| members | `tests/test_alone.py` |"])
    assert suite_rule.suite(t) == ["tests/test_root.py"]
    t = _groups_tree(tmp_path / "c", ["| members | `tests/test_alone.py` |",
                                      "| members | `tests/test_root.py` AND `tests/test_partner.py` |"])
    assert suite_rule.suite(t) == ["tests/test_partner.py", "tests/test_root.py"]
    t = _groups_tree(tmp_path / "d", ["no groups here"])
    with pytest.raises(ValueError, match="declares no joint test group"):
        suite_rule.suite(t)


def test_the_suite_is_closed_under_the_joint_test_groups():
    """0007 v22 §4d (run 1: the store driver alone failed its gate in every job): a selected member of a joint test
    group brings the others, read from the ONE carrier, specs/evidence/offline/JOINT-TEST-GROUPS.md. Today that adds
    exactly G1's base driver, and nothing outside a group."""
    selected = {str(f.relative_to(ROOT)) for f in (ROOT / "tests").rglob("test_*.py")
                if suite_rule.reasons(f.read_text(encoding="utf-8"))}
    groups = suite_rule.joint_groups()
    added = set(suite_rule.suite(ROOT)) - selected
    assert added == {m for g in groups if selected & set(g) for m in g} - selected
    assert "tests/test_seam_model_0029_0030.py" in added
    assert any(len(g) > 1 for g in groups)


def _junit(tmp_path, cases, modules=None):
    """A planted JUnit: every rule module once (passed), unless `modules` says otherwise, plus `cases`:
    [(module path, test name, kind, message)], kind one of passed/failed/error/skip/xfail."""
    modules = suite_rule.suite(ROOT) if modules is None else modules
    rows = [(m, "test_planted_ok", "passed", None) for m in modules] + list(cases)
    body = []
    for mod, name, kind, msg in rows:
        cls = mod[:-3].replace("/", ".")
        inner = {"passed": "", "failed": '<failure message="boom">x</failure>', "error": '<error message="e">x</error>',
                 "skip": f'<skipped type="pytest.skip" message="{msg}">{mod}:1: {msg}</skipped>',
                 "xfail": f'<skipped type="pytest.xfail" message="{msg}" />'}[kind]
        body.append(f'<testcase classname="{cls}" name="{name}" time="0.{len(body)}">{inner}</testcase>')
    path = tmp_path / "junit.xml"
    path.write_text('<?xml version="1.0"?><testsuites><testsuite name="pytest">' + "".join(body)
                    + "</testsuite></testsuites>")
    return path


def test_the_job_must_have_run_exactly_the_rules_modules(tmp_path):
    mods = suite_rule.suite(ROOT)
    assert suite_rule.nodes_problems(_junit(tmp_path, []), ROOT) == []
    extra = suite_rule.nodes_problems(_junit(tmp_path, [("tests/test_not_in_suite.py", "t", "passed", None)]), ROOT)
    assert extra == ["the job ran tests/test_not_in_suite.py, which the rule does not select"]
    missing = suite_rule.nodes_problems(_junit(tmp_path, [], modules=mods[1:]), ROOT)
    assert missing == [f"the rule selects {mods[0]}, which the job did not run"]


# ---- Q2: the attestation-class column ----------------------------------------------------------------------------------
def test_every_inventory_entry_in_the_suite_carries_its_attestation_class_and_none_outside():
    """§4d: "a gate requires the column on every entry whose file is in the suite"; outside it, the column is None."""
    in_suite = set(suite_rule.suite(ROOT))
    bad = []
    for e in skip_inventory.INVENTORY:
        cls = skip_inventory.attestation_class(e)
        if e[0] in in_suite and cls not in skip_inventory.ATTESTATION_CLASSES:
            bad.append(f"{e[0]} [{e[2]}]: in the suite, class {cls!r}")
        if e[0] not in in_suite and cls is not None:
            bad.append(f"{e[0]} [{e[2]}]: outside the suite, class {cls!r}")
    assert not bad, bad


def test_no_inventory_entry_carries_the_rewrite_class():
    """Research's Q2a: `rewrite` stays in the vocabulary, and is EMPTY by rule (§4d's mutant: a rewrite-class skip
    left in place)."""
    assert "rewrite" in skip_inventory.ATTESTATION_CLASSES
    assert [e for e in skip_inventory.INVENTORY if skip_inventory.attestation_class(e) == "rewrite"] == []


_STRANDED = ("records a different runtime identity", "is not a qualified runtime", "runtime_" + "supported",
             "_runtime_" + "supported_interim", "qualified_runtimes")
"""(Both predicate names are split: test_0007_runtime_status's census refuses any live file whose code names either,
a string constant included.)"""


def _skip_sites(text):
    """The source of every skip DECISION in a module: pytest.skip/skipif/importorskip calls and skipif markers."""
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            if name in ("skip", "skipif", "importorskip"):
                yield ast.get_source_segment(text, node) or ""
        elif isinstance(node, ast.If) and any(
                isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "skip" for s in node.body
                for c in ast.walk(s)):
            yield ast.get_source_segment(text, node.test) or ""


def test_both_stranded_skips_are_gone_from_the_suite():
    """§4d's stranded rows: no skip decision in a suite module (its call, marker or guarding condition) still rests on
    the withdrawn single-record rule. Control: the two stranded forms as they were, planted, are found."""
    hits = [f"{mod}: {site[:100]}" for mod in suite_rule.suite(ROOT)
            for site in _skip_sites((ROOT / mod).read_text()) if any(m in site for m in _STRANDED)]
    assert not hits, hits
    skip = "pytest." + "skip"                     # split, so the completeness gate does not read a skip site here
    planted = (f"def test_x():\n    if not ev.sv.runtime_supported():\n        {skip}('x is not a qualified runtime')\n"
               f"def test_y():\n    {skip}('artifact records a different runtime identity')\n")
    assert len([s for s in _skip_sites(planted) if any(m in s for m in _STRANDED)]) == 3


# ---- Q3: one job, its closed outcome -------------------------------------------------------------------------------------
def _args(**over):
    base = dict(route="setup-python", runner_image="ubuntu-24.04", expect_prefix=sys.base_prefix, run_id="7",
                job_id=3)
    base.update(over)
    return SimpleNamespace(**base)


def _status(status="verified"):
    return lambda: sv.runtime_status()._replace(status=status, reason="" if status != "refused" else "probe x is False")


def _decide(tmp_path, cases=(), modules=None, status="verified", evidence_rc=0, probes=None, records=None,
            suite_rc=None, collected=None, euid=1000, environ=None, head=None, completion=True, **over):
    """A synthetic job. Its suite stands in for a real one in all three carriers: the JUnit, the invocation's own
    collection record (the JUnit's nodes unless `collected` says otherwise, SA-R3-02) and an exit status that agrees
    with the JUnit unless `suite_rc` says otherwise (SA-R3-03). C1 (round 3): `euid` is EXPLICIT and non-root, so a
    synthetic case reaches the behaviour it tests on a root host too; only the root-job cell passes 0."""
    junit = _junit(tmp_path, cases, modules)
    nodes = [n for n, _, _ in job.junit_cases(junit)]
    failing = any(o in ("failed", "error") for _, o, _ in job.junit_cases(junit))

    def run_suite(target):
        pathlib.Path(target).write_bytes(junit.read_bytes())
        job.collected_path(target).write_text(json.dumps(nodes if collected is None else collected))
        rc = (1 if failing else 0) if suite_rc is None else suite_rc
        if completion is not None:     # SA-R4-01: an honest suite's record (pytest.main returned rc), unless overridden
            job.completion_path(target).write_text(json.dumps(
                completion(rc, job.nonce_path(target).read_text()) if callable(completion) else
                {"returned": True, "exit_status": rc, "nonce": job.nonce_path(target).read_text()}))
        return rc
    return job.decide(_args(**over), runtime_status=_status(status), check_evidence=lambda: (evidence_rc, "tail"),
                      run_suite=run_suite, head=head or (lambda: "a" * 40), records=records, euid=euid,
                      environ={} if environ is None else environ,
                      probes=probes or (lambda: {k: True for k in sv.CONFINEMENT_PROBE_KEYS}))


def test_agreeing_evidence_builds_this_builds_record_here(tmp_path):
    r = _decide(tmp_path)
    assert r["outcome"] == "evidence" and job.OUTCOME_EXIT["evidence"] == 0
    rec = r["record"]
    assert sv.attestation_record_problems(rec) == []
    assert sv.attestation_key(rec) == sv.attestation_key(sv.attestation_identity())
    assert rec["provenance"] == [{"route": "setup-python", "runner_image": "ubuntu-24.04", "run_id": "7", "job_id": 3,
                                  "commit": "a" * 40}]


def test_a_wrong_interpreter_is_a_named_failure_naming_both_locations(tmp_path):
    """BLOCKING 3: the row must be the route it claims."""
    r = _decide(tmp_path, expect_prefix="/no/such/route")
    assert r["outcome"] == "wrong-interpreter" and job.OUTCOME_EXIT["wrong-interpreter"] == 1
    assert "/no/such/route" in r["reason"] and str(pathlib.Path(sys.base_prefix).resolve()) in r["reason"]
    assert (job.interpreter_problem(sys.base_prefix, version_info=(3, 13, 0)) or "").startswith("Python 3.13 is below")
    assert job.interpreter_problem(str(pathlib.Path(sys.base_prefix).parent)) is None      # under a declared prefix


def test_a_root_job_is_a_named_failure_before_anything_runs(tmp_path):
    """INV-SA6's job-state assertion: a root job is red, named, and runs nothing; a non-root uid passes it."""
    ran = []
    r = job.decide(_args(), runtime_status=_status(), check_evidence=lambda: ran.append("ce") or (0, ""),
                   run_suite=lambda t: ran.append("suite"), head=lambda: "a" * 40, euid=0)
    assert (r["outcome"], ran) == ("wrong-job-state", []) and job.OUTCOME_EXIT["wrong-job-state"] == 1
    assert "root" in r["reason"] and job.job_state_problem(1000) is None


@pytest.mark.parametrize("var,value", [
    ("PYTEST_ADDOPTS", "--deselect=tests/test_a.py::test_second"),        # the reviewer's SA-R3-02 route
    ("PYTEST_ADDOPTS", "-o python_functions=test_first"),                 # research's: collection itself shrinks
    ("PYTEST_PLUGINS", "some_plugin"), ("PYTHONPATH", "/elsewhere"), ("PYTHONHOME", "/elsewhere"),
])
def test_an_environment_that_shapes_pytest_refuses_the_job_before_anything_runs(tmp_path, var, value):
    """SA-R3-02 (round 3) and research's stage-1 read: an inherited PYTEST_* (or PYTHONPATH/PYTHONHOME) can deselect
    a node, shrink collection so that the invocation's own collection agrees, or load code that rewrites outcomes. The
    job refuses it, named, at step 0 and runs nothing. Control: an ordinary CI environment is no problem."""
    ran = []
    r = job.decide(_args(), runtime_status=_status(), check_evidence=lambda: ran.append("ce") or (0, ""),
                   run_suite=lambda t: ran.append("suite"), head=lambda: "a" * 40, euid=1000, environ={var: value})
    assert (r["outcome"], ran) == ("wrong-job-state", []) and var in r["reason"]
    assert job.environment_problem({"PATH": "/usr/bin", "HOME": "/h", "CI": "true", "GITHUB_RUN_ID": "1"}) is None


@pytest.mark.parametrize("change", ["missing", "unexpected", "duplicate"])
def test_the_junit_must_equal_the_invocations_own_collection_as_a_multiset(tmp_path, change):
    """SA-R3-02's closure: executed node identities AND multiplicities equal the same invocation's collection. The
    reviewer's witness is `missing`: a node deselected inside a module that still reports, so the rule's module check
    passes. The module check itself is kept (control: `test_the_job_must_have_run_exactly_the_rules_modules`)."""
    mod = suite_rule.suite(ROOT)[0]
    cases = [(mod, "test_first", "passed", None), (mod, "test_second", "passed", None)]
    nodes = [n for n, _, _ in job.junit_cases(_junit(tmp_path, cases))]
    collected = {"missing": nodes + [f"{mod}::test_deselected"], "unexpected": nodes[:-1],
                 "duplicate": nodes}[change]
    if change == "duplicate":
        cases = cases + [cases[-1]]
    r = _decide(tmp_path, cases=cases, collected=collected)
    word = {"missing": "1 missing", "unexpected": "1 unexpected", "duplicate": "reported more than once"}[change]
    assert r["outcome"] == "suite-mismatch" and word in r["reason"], r["reason"]
    if change == "missing":
        assert _decide(tmp_path, cases=cases)["outcome"] == "evidence"                     # control: equal multisets


@pytest.mark.parametrize("rc,failing,outcome,word", [
    (1, False, "failed-tests", "session-level failure"),       # SA-R3-03: the reviewer's real witness, in the JUnit form
    (0, True, "suite-mismatch", "exited 0 while its JUnit has a failing case"),
    (2, False, "suite-mismatch", "interrupted"), (3, False, "suite-mismatch", "internal error"),
    (4, False, "suite-mismatch", "usage error"), (5, False, "suite-mismatch", "no tests collected"),
])
def test_pytests_exit_status_must_agree_with_its_junit(tmp_path, rc, failing, outcome, word):
    """SA-R3-03 (round 3): `decide` discarded run_suite's status, so a pytest that exited 1 after writing an all-pass
    JUnit attested. Now 0 means no failing case and 1 at least one; any other status is named. The bootstrap control
    (exit 1, the A10 node alone failing, at a zero-current state) stays `bootstrap-pending`:
    `test_the_bootstrap_node_failing_at_a_zero_current_state_is_bootstrap_pending`."""
    mod = suite_rule.suite(ROOT)[0]
    cases = [(mod, "test_x", "failed" if failing else "passed", None)]
    r = _decide(tmp_path, cases=cases, suite_rc=rc)
    assert r["outcome"] == outcome and word in r["reason"], r


def test_a_failed_git_head_is_the_jobs_state_not_a_confinement_failure(tmp_path, monkeypatch):
    """Research's stage-1 read of SA-R3-03: `_head()` dropped git's exit code, and its "" reached the record validator
    as `confinement-failed`. Now it is `wrong-job-state`, naming the exit; a readable HEAD still passes."""
    import attestation_writer as aw_mod
    monkeypatch.setattr(aw_mod, "run_git", lambda args, repo: (128, ""))
    r = _decide(tmp_path, head=job._head)
    assert r["outcome"] == "wrong-job-state" and "exited 128" in r["reason"], r
    monkeypatch.setattr(aw_mod, "run_git", lambda args, repo: (0, "b" * 40))
    assert _decide(tmp_path, head=job._head)["outcome"] == "evidence"


_LIVE_A = "def test_first():\n    assert True\n\n\ndef test_second():\n    assert True\n"
_LIVE_B = "def test_first():\n    assert True\n\n\ndef test_other():\n    assert True\n"
_LIVE_RAISE = ("import pytest\n\n\n@pytest.hookimpl(wrapper=True)\ndef pytest_sessionfinish(session):\n"
               "    yield\n    raise RuntimeError('a session-finish failure after the JUnit was written')\n")


_DROP_HOOK = {   # research's stage 2 on 95c207c: a conftest drops a failing test from `items`, no deselect report
    "unmarked": "", "tryfirst": "@pytest.hookimpl(tryfirst=True)\n", "trylast": "@pytest.hookimpl(trylast=True)\n",
    "wrapper": "@pytest.hookimpl(wrapper=True)\n",
}
_SUPERSEDED_PLUGIN = (   # the first form (95c207c): a tryfirst modifyitems hook, which a conftest's tryfirst one precedes
    "import json, os\nimport pytest\n\n\n@pytest.hookimpl(tryfirst=True)\n"
    "def pytest_collection_modifyitems(session, config, items):\n    path = os.environ.get('VERACIUM_ATTESTATION_COLLECTED')\n"
    "    if path:\n        with open(path, 'w') as f:\n            json.dump([i.nodeid for i in items], f)\n")


@pytest.mark.parametrize("hook", sorted(_DROP_HOOK))
def test_a_conftest_that_drops_a_collected_test_is_caught_whatever_its_hook_priority(tmp_path, monkeypatch, hook):
    """SA-R3-02, research's stage 2: the collection record must precede EVERY collection_modifyitems implementation, a
    conftest's tryfirst one and a wrapper included. A real pytest process through `_run_suite`; the conftest drops a
    FAILING test. The committed plugin (pytest_itemcollected) names it missing for every priority. Its superseded form
    is run against the same fixture as the cell's own control, and must miss the tryfirst and wrapper forms: a cell
    that cannot tell the two plugins apart would prove nothing."""
    root = tmp_path / "tree"
    (root / "tests").mkdir(parents=True)
    (root / "tests" / "test_a.py").write_text("def test_first():\n    assert True\n\n\ndef test_second():\n    assert False\n")
    body = ("    items[:] = [i for i in items if i.name != 'test_second']\n" if hook != "wrapper" else
            "    items[:] = [i for i in items if i.name != 'test_second']\n    yield\n")   # before every inner hook
    (root / "tests" / "conftest.py").write_text(f"import pytest\n\n\n{_DROP_HOOK[hook]}def pytest_collection_modifyitems(items):\n{body}")
    for k in [k for k in __import__("os").environ if k.startswith("PYTEST_")]:
        monkeypatch.delenv(k)
    monkeypatch.setattr(job, "ROOT", root)
    monkeypatch.setattr(job.attestation_suite, "suite", lambda r: ["tests/test_a.py"])

    def outcome():
        return job.decide(_args(), runtime_status=_status(), check_evidence=lambda: (0, ""), run_suite=job._run_suite,
                          head=lambda: "a" * 40, euid=1000, environ={}, records=[],
                          probes=lambda: {k: True for k in sv.CONFINEMENT_PROBE_KEYS})
    r = outcome()
    assert r["outcome"] == "suite-mismatch" and "1 missing (collected, not reported): tests/test_a.py::test_second" in r["reason"], r
    old = tmp_path / "superseded"
    old.mkdir()
    (old / "attestation_collect.py").write_text(_SUPERSEDED_PLUGIN)
    monkeypatch.setattr(job, "COLLECT_PLUGIN_DIR", old)
    caught = outcome()["outcome"] == "suite-mismatch"
    assert caught is (hook not in ("tryfirst", "wrapper")), (hook, caught)


@pytest.mark.parametrize("mode", ["control", "deselect", "session-finish-raise"])
def test_the_real_suite_process_is_bound_by_its_collection_and_its_exit_status(tmp_path, monkeypatch, mode):
    """SA-R3-02 and SA-R3-03 with a REAL pytest process through the unchanged `_run_suite` (the reviewer's minimal
    fixture: two modules, four tests; ROOT and the rule's module list are the only seams). `deselect` reaches pytest
    because decide's own environment check is handed a clean environment, so the collection binding alone must catch
    it; `session-finish-raise` writes an all-pass JUnit and exits 1."""
    root = tmp_path / "tree"
    (root / "tests").mkdir(parents=True)
    (root / "tests" / "test_a.py").write_text(_LIVE_A)
    (root / "tests" / "test_b.py").write_text(_LIVE_B)
    if mode == "session-finish-raise":
        (root / "conftest.py").write_text(_LIVE_RAISE)
    for k in [k for k in __import__("os").environ if k.startswith("PYTEST_")]:
        monkeypatch.delenv(k)
    if mode == "deselect":
        monkeypatch.setenv("PYTEST_ADDOPTS", "--deselect=tests/test_a.py::test_second")
    mods = ["tests/test_a.py", "tests/test_b.py"]
    monkeypatch.setattr(job, "ROOT", root)
    monkeypatch.setattr(job.attestation_suite, "suite", lambda r: mods)
    r = job.decide(_args(), runtime_status=_status(), check_evidence=lambda: (0, ""), run_suite=job._run_suite,
                   head=lambda: "a" * 40, euid=1000, environ={}, records=[],
                   probes=lambda: {k: True for k in sv.CONFINEMENT_PROBE_KEYS})
    want = {"control": ("evidence", ""), "deselect": ("suite-mismatch", "1 missing (collected, not reported): "
                                                      "tests/test_a.py::test_second"),
            "session-finish-raise": ("failed-tests", "session-level failure")}[mode]
    assert r["outcome"] == want[0] and want[1] in r["reason"], r



# ---- 0007 round 4, SA-R4-01: the exempt bootstrap failure explains exit 1 only if the process COMPLETED --------------------
_BOOT_MOD, _BOOT_NAME = job.BOOTSTRAP[0].split("::")
_LATE_FAILURE = {   # failures pytest itself does not catch, each AFTER the JUnit was written
    "session-finish-raise": _LIVE_RAISE,                          # the reviewer's: an unmarked sessionfinish wrapper
    "tryfirst-wrapper-raise": ("import pytest\n\n\n@pytest.hookimpl(wrapper=True, tryfirst=True)\n"
                               "def pytest_sessionfinish(session):\n    yield\n"
                               "    raise RuntimeError('a tryfirst session-finish failure after the JUnit was written')\n"),
    "unconfigure-raise": ("def pytest_unconfigure(config):\n    raise RuntimeError('an unconfigure failure')\n"),
    "exit-after-junit": ("import os\nimport pytest\n\n\n@pytest.hookimpl(trylast=True)\n"
                         "def pytest_unconfigure(config):\n    os._exit(0)\n"),
}


def _boot_tree(tmp_path, monkeypatch, *, boot_fails, other_fails, late=None):
    root = tmp_path / "tree"
    (root / "tests").mkdir(parents=True)
    (root / _BOOT_MOD).write_text(f"def {_BOOT_NAME}():\n    assert {not boot_fails}\n\n\ndef test_two():\n    assert True\n")
    (root / "tests" / "test_b.py").write_text(f"def test_first():\n    assert True\n\n\ndef test_other():\n    assert {not other_fails}\n")
    if late:
        (root / "conftest.py").write_text(_LATE_FAILURE[late])
    for k in [k for k in __import__("os").environ if k.startswith("PYTEST_")]:
        monkeypatch.delenv(k)
    monkeypatch.setattr(job, "ROOT", root)
    monkeypatch.setattr(job.attestation_suite, "suite", lambda r: [_BOOT_MOD, "tests/test_b.py"])
    return job.decide(_args(), runtime_status=_status(), check_evidence=lambda: (0, ""), run_suite=job._run_suite,
                      head=lambda: "a" * 40, euid=1000, environ={}, records=[],
                      probes=lambda: {k: True for k in sv.CONFINEMENT_PROBE_KEYS})


@pytest.mark.parametrize("row", ["passing-control", "passing+session-raise", "bootstrap-alone", "bootstrap+session-raise",
                                 "bootstrap+other-failure"])
def test_r4_01_the_reviewers_five_rows(tmp_path, monkeypatch, row):
    """0007 round 4, SA-R4-01 (the reviewer's table, a REAL pytest process through `_run_suite`, the declared A10 node at
    a zero-current state): the exact bootstrap failure plus a session-finish exception after the JUnit was written read
    `bootstrap-pending`, identical to the bootstrap failure alone. Now it is refused, no record; the other rows stand."""
    boot, other, late = {"passing-control": (False, False, None), "passing+session-raise": (False, False, "session-finish-raise"),
                         "bootstrap-alone": (True, False, None), "bootstrap+session-raise": (True, False, "session-finish-raise"),
                         "bootstrap+other-failure": (True, True, None)}[row]
    r = _boot_tree(tmp_path, monkeypatch, boot_fails=boot, other_fails=other, late=late)
    want = {"passing-control": ("evidence", ""), "passing+session-raise": ("failed-tests", "session-level failure"),
            "bootstrap-alone": ("bootstrap-pending", "bootstrap run"),
            "bootstrap+session-raise": ("failed-tests", "did not complete normally"),
            "bootstrap+other-failure": ("failed-tests", "failing")}[row]
    assert r["outcome"] == want[0] and want[1] in r["reason"], r
    assert (r["record"] is None) is (want[0] == "failed-tests"), r


@pytest.mark.parametrize("late", ["tryfirst-wrapper-raise", "unconfigure-raise", "exit-after-junit"])
def test_r4_01_a_failure_pytest_does_not_catch_is_refused_whatever_its_priority(tmp_path, monkeypatch, late):
    """The completion record is written after pytest.main RETURNS, so no hook of any priority runs after it: a conftest's
    TRYFIRST sessionfinish wrapper (which runs outside a -p plugin's own wrapper: the hookwrapper design, kept as a
    mutant), a raising pytest_unconfigure, and a process that exits 0 from inside pytest after writing its JUnit. The
    last runs with every test PASSING: exit 0 beside a failing case is already exit_problem's suite-mismatch, so only an
    all-pass JUnit isolates the completion check (before it, that process attested though it never finished)."""
    r = _boot_tree(tmp_path, monkeypatch, boot_fails=(late != "exit-after-junit"), other_fails=False, late=late)
    assert r["outcome"] == "failed-tests" and "did not complete normally" in r["reason"] and r["record"] is None, r


@pytest.mark.parametrize("kind", ["stale", "status", "absent", "keys"])
def test_r4_01_the_completion_record_must_be_this_runs_and_agree(tmp_path, kind):
    """Research's stage-1 (e) freshness, and the record's own fields: another run's record (its nonce), a pytest.main
    status other than the process's, no record, and a record with other keys each refuse, at the bootstrap state where
    the record matters most."""
    mod = suite_rule.suite(ROOT)[0]
    cases = [(job.BOOTSTRAP[0].split("::")[0], job.BOOTSTRAP[0].split("::")[1], "failed", None), (mod, "test_x", "passed", None)]
    completion = {"stale": lambda rc, n: {"returned": True, "exit_status": rc, "nonce": "0" * 32},
                  "status": lambda rc, n: {"returned": True, "exit_status": 0, "nonce": n},
                  "absent": None,
                  "keys": lambda rc, n: {"returned": True, "exit_status": rc, "nonce": n, "extra": 1}}[kind]
    r = _decide(tmp_path, cases=cases, records=[], completion=completion)
    word = {"stale": "nonce differs", "status": "returned 0 but the process exited 1", "absent": "no completion record",
            "keys": "keys are not"}[kind]
    assert r["outcome"] == "failed-tests" and word in r["reason"] and r["record"] is None, r
    (tmp_path / "control").mkdir()
    assert _decide(tmp_path / "control", cases=cases, records=[])["outcome"] == "bootstrap-pending"   # an honest record


def test_r4_01_every_record_producing_outcome_requires_the_completion_record():
    """Research's stage-1 (d), as a CHECKED predicate over decide's own source: the outcomes decide pairs with a record
    are exactly {evidence, bootstrap-pending}, and the completion check precedes every one of them in the same body.
    A future outcome that yields a record after the check is placed fails here by name."""
    import ast
    tree = ast.parse(inspect.getsource(job.decide))
    calls = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "completion_problem"]
    assert len(calls) == 1, calls
    yields = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "update":
            kw = {k.arg: k.value for k in n.keywords}
            if "record" in kw and "outcome" in kw and isinstance(kw["outcome"], ast.Constant):
                yields[kw["outcome"].value] = n.lineno
    assert set(yields) == {"evidence", "bootstrap-pending"}, yields
    assert all(line > calls[0] for line in yields.values()), (calls, yields)

def test_an_unreadable_key_is_unattestable_after_the_rederivation_and_runs_no_suite(tmp_path, monkeypatch):
    """0007 v22 §4d: the re-derivation runs FIRST (owed on every verifying build), then a build whose key has an
    unreadable field ends `unattestable`, exit 0, naming the field; no suite runs. A failing re-derivation stays red."""
    agg_input = dict(_result(), outcome="unattestable", record=None)      # built while the key still reads
    real = sv.attestation_identity
    monkeypatch.setattr(sv, "attestation_identity", lambda: {**real(), "libc": None})
    ran = []
    r = job.decide(_args(), runtime_status=_status(), check_evidence=lambda: ran.append("ce") or (0, ""),
                   run_suite=lambda t: ran.append("suite"), head=lambda: "a" * 40, euid=1000, environ={})
    assert (r["outcome"], ran) == ("unattestable", ["ce"]) and job.OUTCOME_EXIT["unattestable"] == 0
    assert "libc" in r["reason"] and r["record"] is None
    red = job.decide(_args(), runtime_status=_status(), check_evidence=lambda: (1, "differs"),
                     run_suite=lambda t: None, head=lambda: "a" * 40, euid=1000, environ={})
    assert red["outcome"] == "evidence-mismatch"
    out = agg.aggregate([dict(agg_input, reason=r["reason"])])
    assert not agg.failed(out) and out["unattestable"] and not out["records"]


def test_a_refused_build_is_a_census_row_and_runs_nothing(tmp_path):
    ran = []
    r = job.decide(_args(), runtime_status=_status("refused"), check_evidence=lambda: ran.append("ce") or (0, ""),
                   run_suite=lambda t: ran.append("suite"), head=lambda: "a" * 40, euid=1000, environ={})
    assert (r["outcome"], r["record"], ran) == ("refused", None, []) and job.OUTCOME_EXIT["refused"] == 0
    assert "probe x is False" in r["reason"]


def test_a_check_evidence_failure_is_evidence_mismatch_not_refused(tmp_path):
    """BLOCKING 2: §5f.3, a build that re-derives differently is a FAILED job, never a record and never a census
    `refused`."""
    r = _decide(tmp_path, evidence_rc=1)
    assert r["outcome"] == "evidence-mismatch" and job.OUTCOME_EXIT["evidence-mismatch"] == 1 and r["record"] is None


def test_a_suite_other_than_the_rules_is_suite_mismatch(tmp_path):
    r = _decide(tmp_path, cases=[("tests/test_not_in_suite.py", "t", "passed", None)])
    assert r["outcome"] == "suite-mismatch" and "test_not_in_suite.py" in r["reason"]


def test_an_xfail_is_not_a_skip_and_an_unmapped_skip_fails(tmp_path):
    """BLOCKING 4: one xfail and one ordinary unmapped skip; ONLY the skip fails the job."""
    mod = suite_rule.suite(ROOT)[0]
    r = _decide(tmp_path, cases=[(mod, "test_x", "xfail", "known"), (mod, "test_s", "skip", "an invented reason")])
    assert r["outcome"] == "unmapped-skip" and "test_s" in r["reason"] and "test_x" not in r["reason"]
    alone = _decide(tmp_path, cases=[(mod, "test_x", "xfail", "known")])
    assert alone["outcome"] == "evidence"


def _job_runs_entry():
    in_suite = set(suite_rule.suite(ROOT))
    return next(e for e in skip_inventory.INVENTORY
                if e[0] in in_suite and skip_inventory.attestation_class(e) == "job:runs")


def test_a_fired_job_runs_condition_excludes_the_job_naming_its_entry(tmp_path):
    e = _job_runs_entry()
    r = _decide(tmp_path, cases=[(e[0], "test_s", "skip", e[2])])
    assert r["outcome"] == "excluded" and job.OUTCOME_EXIT["excluded"] == 0 and r["record"] is None
    assert r["excluded_entries"] and e[0] in r["excluded_entries"][0] and e[2] in r["excluded_entries"][0]


def test_a_fired_condition_never_hides_a_failure(tmp_path):
    """Research's stage 2 on 84c512b: a fired job:runs skip AND a failure give failed-tests, exit 1, still naming the
    fired entry (exclusion means "not an input", never "not a failure")."""
    e = _job_runs_entry()
    r = _decide(tmp_path, cases=[(e[0], "test_s", "skip", e[2]), (e[0], "test_f", "failed", None)])
    assert r["outcome"] == "failed-tests" and job.OUTCOME_EXIT[r["outcome"]] == 1
    assert r["excluded_entries"] and e[2] in r["excluded_entries"][0] and "job:runs condition" in r["reason"]


def test_a_key_class_skip_is_evidence_not_exclusion(tmp_path, monkeypatch):
    """A `key` skip fires identically for every job of one key, so it is part of the evidence. The entry is PLANTED, so
    the cell never depends on which key-class entries this tree happens to carry."""
    mod = suite_rule.suite(ROOT)[0]
    planted = (mod, "skip", "a planted key-class token", "system", "planted by the cell", "key")
    monkeypatch.setattr(skip_inventory, "INVENTORY", [*skip_inventory.INVENTORY, planted])
    r = _decide(tmp_path, cases=[(mod, "test_s", "skip", planted[2])])
    assert r["outcome"] == "evidence", r["reason"]


A10_MOD, A10_NAME = "tests/test_migrations_0013.py", "test_the_committed_path_evidence_was_generated_on_an_attested_build"


def test_the_bootstrap_node_failing_at_a_zero_current_state_is_bootstrap_pending(tmp_path):
    """v21 (1): iff every record is superseded (none counts), the declared node's FAILURE alone gives bootstrap-pending
    (exit 0), and the record is built. Both zero-current states: the first run's empty artifact, and a bump's artifact
    of superseded records (phrase 15: "only when empty" would re-create the deadlock at the next bump)."""
    assert job.BOOTSTRAP == (f"{A10_MOD}::{A10_NAME}",)
    superseded = dict(_result()["record"], manifest_algorithm=sv.MANIFEST_ALGORITHM - 1)
    for records in ([], [superseded]):
        r = _decide(tmp_path, cases=[(A10_MOD, A10_NAME, "failed", None)], records=records)
        assert r["outcome"] == "bootstrap-pending" and job.OUTCOME_EXIT["bootstrap-pending"] == 0, (records, r["reason"])
        assert r["record"] is not None and A10_NAME in r["reason"]


@pytest.mark.parametrize("kind", ["current", "malformed", "future"])
def test_the_bootstrap_exemption_is_void_at_a_non_zero_current_state(tmp_path, kind):
    """v21 (1): a current, malformed or future record voids it (poisoning the artifact cannot re-open it)."""
    base = _result()["record"]
    rec = {"current": base, "malformed": {"manifest_algorithm": True},
           "future": dict(base, schema_version=sv.SCHEMA_VERSION + 1)}[kind]
    r = _decide(tmp_path, cases=[(A10_MOD, A10_NAME, "failed", None)], records=[rec])
    assert r["outcome"] == "failed-tests" and r["record"] is None and "exemption is void" in r["reason"]
    assert job.bootstrap_open([rec]) is False


def test_an_error_on_the_bootstrap_node_is_failed_tests(tmp_path):
    """v21 (1): only a JUnit <failure> of the node is exempt; an <error> (a broken fixture, an import) is red."""
    r = _decide(tmp_path, cases=[(A10_MOD, A10_NAME, "error", None)], records=[])
    assert r["outcome"] == "failed-tests" and r["record"] is None


def test_the_bootstrap_node_is_one_pytest_collects():
    """v21 (1): a renamed node would leave the exemption covering nothing, silently."""
    import os
    p = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:randomly", "-p",
                        "no:cacheprovider", *job.BOOTSTRAP], cwd=str(ROOT), capture_output=True, text=True,
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert p.returncode == 0 and [l for l in p.stdout.splitlines() if "::" in l] == list(job.BOOTSTRAP), p.stdout[-800:]


def test_the_bootstrap_exemption_never_covers_a_second_node(tmp_path):
    other = suite_rule.suite(ROOT)[0]
    r = _decide(tmp_path, cases=[(A10_MOD, A10_NAME, "failed", None), (other, "test_f", "failed", None)], records=[])
    assert r["outcome"] == "failed-tests" and r["record"] is None


def test_failing_tests_are_red_and_still_carry_their_digest(tmp_path):
    mod = suite_rule.suite(ROOT)[0]
    r = _decide(tmp_path, cases=[(mod, "test_f", "failed", None)])
    assert r["outcome"] == "failed-tests" and job.OUTCOME_EXIT["failed-tests"] == 1
    assert r["result_digest"] and r["record"] is None and r["key"]


def test_a_failing_confinement_probe_is_never_a_record(tmp_path):
    first = sorted(sv.CONFINEMENT_PROBE_KEYS)[0]
    r = _decide(tmp_path, probes=lambda: {k: k != first for k in sv.CONFINEMENT_PROBE_KEYS})
    assert r["outcome"] == "confinement-failed" and job.OUTCOME_EXIT["confinement-failed"] == 1 and r["record"] is None


def test_the_suite_runs_once_in_pytests_own_order(monkeypatch, tmp_path):
    """BLOCKING 1: pytest-randomly disabled, no cache, the rule's modules, one process. SA-R4-01: that process is the
    completion child around pytest.main, handed the completion path and decide's nonce before pytest's own arguments."""
    seen = []
    monkeypatch.setattr(job.subprocess, "run", lambda argv, **k: seen.append(argv) or SimpleNamespace(returncode=0))
    junit = tmp_path / "j.xml"
    job.nonce_path(junit).write_text("n" * 32)
    job._run_suite(junit)
    (argv,) = seen
    assert argv[1:5] == ["-c", job._CHILD, str(job.completion_path(junit)), "n" * 32], argv[:5]
    assert "no:randomly" in argv and argv[argv.index("no:randomly") - 1] == "-p"
    assert "-n" not in argv and argv[-len(suite_rule.suite(ROOT)):] == suite_rule.suite(ROOT)


def test_the_result_digest_ignores_timing_and_order_and_sees_one_outcome(tmp_path):
    mod = suite_rule.suite(ROOT)[0]
    a = job.junit_cases(_junit(tmp_path, [(mod, "test_a", "passed", None), (mod, "test_b", "failed", None)]))
    b = list(reversed(a))
    assert job.result_digest(a) == job.result_digest(b)
    flipped = [(n, "passed" if n.endswith("test_b") else o, m) for n, o, m in a]
    assert job.result_digest(flipped) != job.result_digest(a)


def test_the_suites_node_ids_do_not_depend_on_the_hash_seed():
    """Research's determinism ask, at the cost a suite cell can carry: the suite's COLLECTED node ids under two
    PYTHONHASHSEED values are identical (a node id built from set order fails here, not as a silent CI disagreement).
    The full twice-run of outcomes is evidence, run once (scratch transcript), not a suite cell."""
    import os
    ids = []
    for seed in ("0", "12345"):
        p = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:randomly",
                            "-p", "no:cacheprovider", *suite_rule.suite(ROOT)], cwd=str(ROOT), capture_output=True,
                           text=True, env={**os.environ, "PYTHONHASHSEED": seed})
        assert p.returncode == 0, p.stdout[-2000:] + p.stderr[-2000:]
        ids.append([line for line in p.stdout.splitlines() if "::" in line])
    assert ids[0] and ids[0] == ids[1]


# ---- Q4/Q5: aggregation --------------------------------------------------------------------------------------------------
def _result(outcome="evidence", route="setup-python", image="ubuntu-24.04", job_id=1, digest="e" * 64, **rec_over):
    key = list(sv.attestation_key(sv.attestation_identity()))
    r = {"outcome": outcome, "route": route, "runner_image": image, "job_id": job_id, "reason": "", "key": key,
         "excluded_entries": [], "record": None}
    if outcome == "evidence":
        rec = {**{k: sv.attestation_identity()[k] for k in sv.KEY_FIELDS}, "manifest_algorithm": sv.MANIFEST_ALGORITHM,
               "schema_version": sv.SCHEMA_VERSION, "result_digest": digest,
               "confinement": {k: True for k in sv.CONFINEMENT_PROBE_KEYS},
               "provenance": [{"route": route, "runner_image": image, "run_id": "9", "job_id": job_id,
                               "commit": "a" * 40}]}
        rec.update(rec_over)
        r["record"] = rec
        r["key"] = list(sv.attestation_key(rec))
    return r


def test_equal_evidence_aggregates_to_one_record_with_sorted_union_provenance():
    out = agg.aggregate([_result(route="setup-python", job_id=4), _result(route="deadsnakes", job_id=2)])
    assert not agg.failed(out) and len(out["records"]) == 1
    prov = out["records"][0]["provenance"]
    assert [j["route"] for j in prov] == ["deadsnakes", "setup-python"]
    assert sv.attestation_record_problems(out["records"][0]) == []


def test_different_evidence_is_a_disagreement_naming_every_job_and_other_keys_still_emit():
    """Other keys still emit whether they sort BEFORE or AFTER the disagreeing key (0007 CI run 1: with one other key,
    the kill of "one disagreement stops every key" depended on which machine name the runner had)."""
    before = _result(route="docker", image="python:3.14-alpine", job_id=8, machine="aa_sorts_first")
    after = _result(route="docker", image="python:3.14-trixie", job_id=9, machine="zz_sorts_last")
    out = agg.aggregate([_result(job_id=1), _result(route="deadsnakes", job_id=2, digest="d" * 64), before, after])
    assert agg.failed(out) and out["disagreements"][0]["why"] == "different evidence"
    assert len(out["disagreements"][0]["jobs"]) == 2
    assert sorted(sv.attestation_key(r) for r in out["records"]) == sorted(
        sv.attestation_key(x["record"]) for x in (before, after))


def test_bootstrap_jobs_aggregate_to_records_named_as_bootstrap_and_a_mixed_key_disagrees():
    """v21 (2): a bootstrap run's agreeing jobs emit records through the NORMAL path, and are named in bootstrap_jobs
    (the writer's --fresh refuses such an aggregate); a key mixing bootstrap-pending and evidence jobs disagrees."""
    a = _result(job_id=1)
    a["outcome"] = "bootstrap-pending"
    b = _result(route="deadsnakes", job_id=2)
    b["outcome"] = "bootstrap-pending"
    out = agg.aggregate([a, b])
    assert not agg.failed(out) and len(out["records"]) == 1 and len(out["bootstrap_jobs"]) == 2
    mixed = agg.aggregate([a, _result(route="deadsnakes", job_id=2)])
    assert agg.failed(mixed) and "bootstrap" in mixed["disagreements"][0]["why"]


def test_a_refused_job_beside_a_verifying_one_of_the_same_key_is_a_disagreement():
    out = agg.aggregate([_result(job_id=1), _result("refused", route="deadsnakes", job_id=2)])
    assert agg.failed(out) and not out["records"] and "refused" in out["disagreements"][0]["why"]


@pytest.mark.parametrize("red", ["failed-tests", "evidence-mismatch", "confinement-failed"])
def test_a_key_with_only_failing_jobs_fails_aggregation(red):
    """Research's Q5a: "attested" is never one red job away from silently empty."""
    out = agg.aggregate([_result(red, job_id=1)])
    assert agg.failed(out) and out["failed_keys"] and not out["records"]


def test_excluded_and_refused_only_keys_are_listed_not_failures_and_a_missing_row_is_unavailable():
    rows = [{"route": "setup-python", "runner_image": "ubuntu-24.04"}, {"route": "distro", "runner_image": "rhel-10"}]
    out = agg.aggregate([_result("excluded", job_id=1), _result("refused", route="conda-forge", job_id=2)], rows)
    assert not agg.failed(out) and out["excluded"] and out["refused"]
    assert out["unavailable"] == ["distro on rhel-10"]


def test_the_aggregator_takes_each_key_from_its_record_never_from_its_own_runner(monkeypatch):
    """Research's Q4 addition: an aggregator on another platform still emits the job's key."""
    mine = _result(job_id=1)
    monkeypatch.setattr(sv, "attestation_identity", lambda: {**mine["record"], "machine": "riscv64", "libc": "musl"})
    out = agg.aggregate([mine])
    assert [sv.attestation_key(r) for r in out["records"]] == [sv.attestation_key(mine["record"])]


# ---- Q6: the matrix's one carrier, and the workflow that reads it --------------------------------------------------------
def _spec_route_rows():
    text = (SPECS / "0007-store-schema-versioning.md").read_text()
    start = text.index("| route to a Python 3.14 | OS images |")
    rows = []
    for line in text[start:].splitlines()[2:]:
        if not line.startswith("|"):
            break
        rows.append(line.split("|")[1].strip())
    return rows


def test_rows_json_is_its_generators_output():
    p = subprocess.run([sys.executable, "-I", str(ATT / "gen_rows.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_every_route_row_of_the_spec_is_a_matrix_row_or_named_later():
    data = json.loads((ATT / "rows.json").read_text())
    covered = {r["spec_row"] for r in data["rows"]} | {r["spec_row"] for r in data["later"]}
    spec_rows = _spec_route_rows()
    assert spec_rows and set(spec_rows) == covered, (sorted(set(spec_rows) - covered), sorted(covered - set(spec_rows)))


def test_every_row_declares_its_route_location_install_and_interpreter():
    """BLOCKING 3's carrier: a row cannot run without the location its interpreter must lie under."""
    data = json.loads((ATT / "rows.json").read_text())
    bad = []
    for r in data["rows"]:
        for f in ("route", "runner_image", "runs_on", "install", "python", "expect_prefix"):
            if not isinstance(r.get(f), str) or not r[f]:
                bad.append(f"{r.get('route')}/{r.get('runner_image')}: no {f}")
        if "image" in r and not r.get("user_add"):
            bad.append(f"{r['route']}/{r['runner_image']}: a container row with no non-root user")
    pairs = [(r["route"], r["runner_image"]) for r in data["rows"]]
    assert not bad and len(pairs) == len(set(pairs)), (bad, pairs)


def test_the_workflow_reads_the_rows_runs_each_row_non_root_with_full_history_and_never_runs_on_main():
    wf = (ROOT / ".github" / "workflows" / "attestation.yml").read_text()
    assert 'branches: ["attest/**"]' in wf and "workflow_dispatch:" in wf
    assert "main" not in wf.split("jobs:")[0]                         # the trigger block names no main branch
    assert "include: ${{ fromJSON(needs.rows.outputs.rows) }}" in wf
    assert "rows.json" in wf and wf.count("fetch-depth: 0") == 2
    assert wf.count("specs/evidence/attestation/run_row.sh") == 2 and "docker exec -u attest" in wf
    assert "--rows specs/evidence/attestation/rows.json" in wf
    sh = (ATT / "run_row.sh").read_text()
    assert 'refusing to run as root' in sh and "-c specs/evidence/attestation/constraints.txt" in sh
    assert '-e ".[dev,mcp]"' in sh


# ---- the pinned dependency set (research's do-now; the network half is a command, never a cell) ---------------------------
def test_the_constraints_pin_every_direct_requirement_within_its_bound():
    assert cons.offline_problems() == []


def test_the_constraints_check_refuses_an_unpinned_or_out_of_bound_or_unparseable_set():
    text = cons.CONSTRAINTS.read_text()
    name = cons._canon(__import__("packaging.requirements", fromlist=["Requirement"]).Requirement(
        cons.direct_requirements()[0]).name)
    lines = [l for l in text.splitlines() if not cons._canon(l.split("==")[0].strip()) == name]
    assert any("is not pinned" in p for p in cons.offline_problems("\n".join(lines)))
    assert any("does not satisfy" in p for p in cons.offline_problems(text + "\npytest==1.0\n"))
    assert any("does not parse" in p for p in cons.offline_problems(text + "\nzzz==1.0 ; python_version >>> '3'\n"))
    assert any("not an exact pin" in p for p in cons.offline_problems(text + "\nzzz>=1.0\n"))


# ---- the mutation matrices (P1) -------------------------------------------------------------------------------------------
def _run_cell(cell, params, tmp_path_factory, patch):
    """'pass', 'kill' (an assertion or DID NOT RAISE) or 'crash: …'. `patch` swaps this module's global for the
    mutant module."""
    this = sys.modules[__name__]
    fn = getattr(this, cell)
    with pytest.MonkeyPatch.context() as mp:
        name, mod = patch
        mp.setattr(this, name, mod)
        args = {}
        for p in inspect.signature(fn).parameters:
            if p in params:
                args[p] = params[p]
            elif p == "tmp_path":
                args[p] = tmp_path_factory.mktemp("cell")
            elif p == "monkeypatch":
                args[p] = mp
            else:
                raise AssertionError(f"{cell}: no argument for {p}")
        try:
            fn(**args)
        except (AssertionError, pytest.fail.Exception):
            return "kill"
        except Exception as exc:  # noqa: BLE001 - a crash is reported, never counted as a kill
            return f"crash: {type(exc).__name__}: {exc}"
    return "pass"


def _matrix(path, global_name, mutants, tmp_path_factory):
    text = path.read_text()

    def load(t, n):
        mod = types.ModuleType(n)
        mod.__file__ = str(path)
        exec(compile(t, str(path), "exec"), mod.__dict__)
        return mod
    cells = sorted({(c, tuple(sorted(p.items()))) for _, kills in mutants.values() for c, p in kills})

    def control(label):
        mod = load(text, "control")
        bad = {c: r for c, p in cells if (r := _run_cell(c, dict(p), tmp_path_factory, (global_name, mod))) != "pass"}
        assert not bad, (label, bad)
    control("control, first")
    survivors = {}
    for name, (edits, kills) in mutants.items():
        mutated = text
        for anchor, repl in edits:
            assert mutated.count(anchor) == 1, (name, anchor)
            mutated = mutated.replace(anchor, repl)
        assert mutated != text, name
        mod = load(mutated, "mutant")
        results = {c: _run_cell(c, p, tmp_path_factory, (global_name, mod)) for c, p in kills}
        if "kill" not in results.values():
            survivors[name] = results
    control("control, last")
    assert not survivors, survivors


def test_the_attestation_suite_rule_mutation_matrix(tmp_path_factory):
    """P1 for specs/attestation_suite.py."""
    A, N = "test_the_rule_admits_each_root_by_import_at_any_depth_or_by_file_inside_a_call", "test_the_rule_admits_nothing_else"
    _matrix(SPECS / "attestation_suite.py", "suite_rule", {
        "submodules not admitted": ([('name == r or name.startswith(r + ".")', "name == r")],
                                    [(A, {"source": "import sqlite3.dbapi2"})]),
        "a name prefix admitted": ([('name.startswith(r + ".")', "name.startswith(r)")], [(N, {"source": "import sqlite3x"})]),
        "from p import x not read as p.x": ([('why |= {f"{node.module}.{a.name}" for a in node.names if _is_root(f"{node.module}.{a.name}")}', "pass")],
                                            [(A, {"source": "from veracium.store import schema_version"})]),
        "relative imports admitted": ([("node.level == 0 and node.module", "node.module")],
                                      [(N, {"source": "from .sqlite3 import connect"})]),
        "keywords ignored": ([("[*node.args, *(k.value for k in node.keywords)]", "list(node.args)")],
                             [(A, {"source": "runpy.run_path(path='specs/schema_evidence.py')"})]),
        "any literal admits": ([("        elif isinstance(node, ast.Call):\n            for arg in [*node.args, *(k.value for k in node.keywords)]:\n                for c in ast.walk(arg):",
                                 "        elif isinstance(node, ast.Module):\n            for arg in [node]:\n                for c in ast.walk(arg):")],
                               [(N, {"source": "X = 'specs/schema_evidence.py'"})]),
        "depth 0 only": ([("    for node in ast.walk(ast.parse(source)):", "    for node in ast.parse(source).body:")],
                         [(A, {"source": "def f():\n    import schema_evidence"})]),
        "the joint-group closure dropped (v22)": ([("        if picked & set(members):\n            picked |= set(members)\n", "        pass\n")],
                                                  [("test_the_suite_is_closed_under_the_joint_test_groups", {})]),
        "a joint group's missing member accepted (v22)": ([("            if missing:\n", "            if False:\n")],
                                                          [("test_the_joint_group_parser_refuses_a_missing_member_and_moves_with_the_document", {})]),
        "an extra module is not reported": ([('    out = [f"the job ran {m}, which the rule does not select" for m in sorted(ran - want)]', "    out = []")],
                                            [("test_the_job_must_have_run_exactly_the_rules_modules", {})]),
        "a missing module is not reported": ([('    out += [f"the rule selects {m}, which the job did not run" for m in sorted(want - ran)]', "")],
                                             [("test_the_job_must_have_run_exactly_the_rules_modules", {})]),
    }, tmp_path_factory)


def test_the_attestation_job_mutation_matrix(tmp_path_factory):
    """P1 for specs/attestation_job.py: each closed outcome's arm, and BLOCKING 1–4."""
    ENVC = "test_an_environment_that_shapes_pytest_refuses_the_job_before_anything_runs"
    MULTI = "test_the_junit_must_equal_the_invocations_own_collection_as_a_multiset"
    EXITC = "test_pytests_exit_status_must_agree_with_its_junit"
    LIVE = "test_the_real_suite_process_is_bound_by_its_collection_and_its_exit_status"
    _matrix(SPECS / "attestation_job.py", "job", {
        "the interpreter check dropped": ([("        if bad:\n            raise Decided(\"wrong-interpreter\", bad)", "        if False:\n            raise Decided(\"wrong-interpreter\", bad)")],
                                          [("test_a_wrong_interpreter_is_a_named_failure_naming_both_locations", {})]),
        "the floor dropped": ([("    if tuple(version_info[:2]) < (3, 14):", "    if False:")],
                              [("test_a_wrong_interpreter_is_a_named_failure_naming_both_locations", {})]),
        "refused runs the suite": ([('        if st.status == "refused":\n            raise Decided("refused", st.reason or "refused")\n', "")],
                                   [("test_a_refused_build_is_a_census_row_and_runs_nothing", {})]),
        "check-evidence read as refused (BLOCKING 2)": ([('raise Decided("evidence-mismatch",', 'raise Decided("refused",')],
                                                        [("test_a_check_evidence_failure_is_evidence_mismatch_not_refused", {})]),
        "the suite's module set unchecked": ([("      # the committed rule's modules, kept\n            if mismatch:\n",
                                               "      # the committed rule's modules, kept\n            if False:\n")],
                                             [("test_a_suite_other_than_the_rules_is_suite_mismatch", {})]),
        "an xfail read as a skip (BLOCKING 4)": ([('            if sk.get("type") == "pytest.xfail":', "            if False:")],
                                                 [("test_an_xfail_is_not_a_skip_and_an_unmapped_skip_fails", {})]),
        "an unmapped skip tolerated": ([("        if unmapped:\n", "        if False:\n")],
                                       [("test_an_xfail_is_not_a_skip_and_an_unmapped_skip_fails", {})]),
        "a fired job:runs condition tolerated": ([("        if fired:\n", "        if False:\n")],
                                                 [("test_a_fired_job_runs_condition_excludes_the_job_naming_its_entry", {})]),
        "every inventoried skip excludes": ([('        elif skip_inventory.attestation_class(entry) == "job:runs":', "        else:")],
                                            [("test_a_key_class_skip_is_evidence_not_exclusion", {})]),
        "exclusion before failures (stage 2)": ([('        if fired:\n            raise Decided("excluded"', '        if False:\n            raise Decided("excluded"'),
                                                  ("        failing = [n for n, o, _ in cases if o in (\"failed\", \"error\")]\n",
                                                   "        failing = [n for n, o, _ in cases if o in (\"failed\", \"error\")]\n        if fired:\n            raise Decided(\"excluded\", \"fired\")\n")],
                                                 [("test_a_fired_condition_never_hides_a_failure", {})]),
        "failures tolerated": ([("        if failing and (set(failing) - set(pending) or not open_):\n", "        if False:\n")],
                               [("test_failing_tests_are_red_and_still_carry_their_digest", {})]),
        "a failing probe recorded": ([("        if problems:                                       # a failing", "        if False:                                       # a failing")],
                                     [("test_a_failing_confinement_probe_is_never_a_record", {})]),
        "randomly left on (BLOCKING 1)": ([('PYTEST_ARGS = ("-p", "no:randomly", "-p", "no:cacheprovider", "-q")', 'PYTEST_ARGS = ("-p", "no:cacheprovider", "-q")')],
                                          [("test_the_suite_runs_once_in_pytests_own_order", {})]),
        "timings in the digest": ([("    pairs = sorted((n, o) for n, o, _ in cases)", "    pairs = [(n, o) for n, o, _ in cases]")],
                                  [("test_the_result_digest_ignores_timing_and_order_and_sees_one_outcome", {})]),
        "drop the job-state assertion (INV-SA6)": ([("        bad = job_state_problem(euid) or environment_problem(environ)\n        if bad:\n            raise Decided(\"wrong-job-state\", bad)", "        pass")],
                                                   [("test_a_root_job_is_a_named_failure_before_anything_runs", {})]),
        # ---- round 3: SA-R3-02, SA-R3-03 and research's stage-1 siblings -------------------------------------------
        "the environment is not checked (SA-R3-02: an inherited PYTEST_ADDOPTS or PYTHONPATH reaches the suite)": (
            [(" or environment_problem(environ)\n", "\n")],
            [(ENVC, {"var": "PYTEST_ADDOPTS", "value": "-o python_functions=test_first"}), (ENVC, {"var": "PYTHONPATH", "value": "/elsewhere"})]),
        "PYTEST_* not refused (only PYTHONPATH/PYTHONHOME are)": ([('ENV_REFUSED_PREFIXES = ("PYTEST_",)', "ENV_REFUSED_PREFIXES = ()")],
                                                                  [(ENVC, {"var": "PYTEST_PLUGINS", "value": "some_plugin"})]),
        "the shipped rule: modules compared, nodes not (SA-R3-02)": (
            [("            mismatch = node_problems(cases, json.loads(cp.read_text()) if cp.exists() else None)\n", "            mismatch = []\n")],
            [(MULTI, {"change": "missing"}), (LIVE, {"mode": "deselect"})]),
        "nodes compared as a set (multiplicity dropped)": ([("    dup = sorted(n for n, c in got.items() if c > 1)\n", "    dup = []\n")],
                                                           [(MULTI, {"change": "duplicate"})]),
        # re-anchored for SA-R4-01's launch (research's stage-1 (f): the round-3 guard re-run on the new child)
        "the collection plugin not loaded": ([('*PYTEST_ARGS, "-p", "attestation_collect", f"--junitxml={junit}"', '*PYTEST_ARGS, f"--junitxml={junit}"')],
                                             [(LIVE, {"mode": "control"})]),
        "the shipped rule: pytest's exit status discarded (SA-R3-03)": ([("            bad = exit_problem(rc, cases)\n", "            bad = None\n")],
                                                                        [(EXITC, {"rc": 1, "failing": False, "outcome": "failed-tests", "word": "session-level failure"}),
                                                                         (LIVE, {"mode": "session-finish-raise"})]),
        "an exit 1 with no failing case admitted": ([("    if rc == 1 and not failing:\n", "    if False:\n")],
                                                    [(EXITC, {"rc": 1, "failing": False, "outcome": "failed-tests", "word": "session-level failure"})]),
        "an exit 0 beside a failing case admitted": ([("    if rc == 0 and failing:\n", "    if False:\n")],
                                                     [(EXITC, {"rc": 0, "failing": True, "outcome": "suite-mismatch", "word": "exited 0 while its JUnit has a failing case"})]),
        "SA-R4-01: the completion record ignored": ([("            bad = completion_problem(completion_path(junit), rc, nonce)\n", "            bad = None\n")],
                                                     [("test_r4_01_the_reviewers_five_rows", {"row": "bootstrap+session-raise"}),
                                                      ("test_r4_01_the_completion_record_must_be_this_runs_and_agree", {"kind": "absent"})]),
        "SA-R4-01: the completion record required only for evidence": ([('            if bad:\n                raise Decided("failed-tests", bad)\n',
                                                                         '            if bad and not any(o == "failed" and n in BOOTSTRAP for n, o, _ in cases):\n                raise Decided("failed-tests", bad)\n')],
                                                                       [("test_r4_01_the_reviewers_five_rows", {"row": "bootstrap+session-raise"})]),
        "SA-R4-01: the record written from a sessionfinish hookwrapper (research's first idea)": ([('_CHILD = ("import json, sys\\n"\n          "import pytest\\n"\n          "path, nonce, args = sys.argv[1], sys.argv[2], sys.argv[3:]\\n"\n          "rc = int(pytest.main(args))\\n"\n          "with open(path, \'w\', encoding=\'utf-8\') as f:\\n"\n          "    json.dump({\'returned\': True, \'exit_status\': rc, \'nonce\': nonce}, f)\\n"\n          "sys.exit(rc)\\n")', '_CHILD = ("import json, sys\\n"\n          "import pytest\\n"\n          "path, nonce, args = sys.argv[1], sys.argv[2], sys.argv[3:]\\n"\n          "class W:\\n"\n          "    @pytest.hookimpl(wrapper=True)\\n"\n          "    def pytest_sessionfinish(self, session):\\n"\n          "        r = yield\\n"\n          "        json.dump({\'returned\': True, \'exit_status\': int(session.exitstatus), \'nonce\': nonce}, open(path, \'w\'))\\n"\n          "        return r\\n"\n          "sys.exit(int(pytest.main(args, plugins=[W()])))\\n")')],
            [("test_r4_01_a_failure_pytest_does_not_catch_is_refused_whatever_its_priority", {"late": "tryfirst-wrapper-raise"})]),
        "SA-R4-01: pytest.main's status not compared with the process's": ([('    if type(rec["exit_status"]) is not int or rec["exit_status"] != rc:\n', '    if type(rec["exit_status"]) is not int:\n')],
                                                                            [("test_r4_01_the_completion_record_must_be_this_runs_and_agree", {"kind": "status"})]),
        "SA-R4-01: the nonce not checked (a stale record stands)": ([('    if rec["nonce"] != nonce:\n', "    if False:\n")],
                                                                    [("test_r4_01_the_completion_record_must_be_this_runs_and_agree", {"kind": "stale"})]),
        "an unnamed exit status admitted": ([("    if rc not in (0, 1):\n", "    if False:\n")],
                                            [(EXITC, {"rc": 5, "failing": False, "outcome": "suite-mismatch", "word": "no tests collected"})]),
        "git's exit code dropped (_head)": ([('    if rc != 0:\n        raise Decided("wrong-job-state", f"git rev-parse HEAD', '    if False:\n        raise Decided("wrong-job-state", f"git rev-parse HEAD')],
                                            [("test_a_failed_git_head_is_the_jobs_state_not_a_confinement_failure", {})]),
        "the bootstrap exemption covers a second node (v21)": ([('        pending = sorted(n for n, o, _ in cases if o == "failed" and n in BOOTSTRAP)', '        pending = sorted(n for n, o, _ in cases if o == "failed")')],
                                                               [("test_the_bootstrap_exemption_never_covers_a_second_node", {})]),
        "the bootstrap exemption at a non-zero-current state (v21)": ([("        open_ = bootstrap_open(records)", "        open_ = True")],
                                                                      [("test_the_bootstrap_exemption_is_void_at_a_non_zero_current_state", {"kind": "current"})]),
        "the bootstrap exemption only when the artifact is empty (v21)": ([("    return aw.zero_current(records)", "    return records == []")],
                                                                          [("test_the_bootstrap_node_failing_at_a_zero_current_state_is_bootstrap_pending", {})]),
        "the bootstrap exemption covers an <error> (v21)": ([('o == "failed" and n in BOOTSTRAP', 'o in ("failed", "error") and n in BOOTSTRAP')],
                                                            [("test_an_error_on_the_bootstrap_node_is_failed_tests", {})]),
        "a bootstrap record reported as evidence": ([('            result.update(outcome="bootstrap-pending", record=record,', '            result.update(outcome="evidence", record=record,')],
                                                    [("test_the_bootstrap_node_failing_at_a_zero_current_state_is_bootstrap_pending", {})]),
        "unattestable decided before --check-evidence (v22)": (
            [("        rc, tail = check_evidence()\n        if rc != 0:\n",
              "        if sv.attestation_key(sv.attestation_identity()) is None:\n            raise Decided(\"unattestable\", \"early\")\n        rc, tail = check_evidence()\n        if rc != 0:\n")],
            [("test_an_unreadable_key_is_unattestable_after_the_rederivation_and_runs_no_suite", {})]),
        "an unreadable key ends the job red (v22)": ([('"bootstrap-pending": 0, "refused": 0, "unattestable": 0,', '"bootstrap-pending": 0, "refused": 0, "unattestable": 1,')],
                                                     [("test_an_unreadable_key_is_unattestable_after_the_rederivation_and_runs_no_suite", {})]),
        "refused fails the matrix": ([('"bootstrap-pending": 0, "refused": 0, "unattestable": 0,', '"bootstrap-pending": 0, "refused": 1, "unattestable": 0,')],
                                     [("test_a_refused_build_is_a_census_row_and_runs_nothing", {})]),
    }, tmp_path_factory)


def test_the_attestation_aggregate_mutation_matrix(tmp_path_factory):
    """P1 for specs/attestation_aggregate.py: §4d's three steps, Q4, Q5a and Q6a."""
    _matrix(SPECS / "attestation_aggregate.py", "agg", {
        "different evidence emitted": ([("        if any({k: v for k, v in rec.items() if k != \"provenance\"} != base for rec in recs[1:]):", "        if False:")],
                                       [("test_different_evidence_is_a_disagreement_naming_every_job_and_other_keys_still_emit", {})]),
        "refused beside evidence emitted": ([('        elif outcome in FAILING or outcome == "refused":', "        elif outcome in FAILING:")],
                                            [("test_a_refused_job_beside_a_verifying_one_of_the_same_key_is_a_disagreement", {})]),
        "a failing-only key silent (Q5a)": ([('            out["failed_keys"].append({"key": repr(key), "jobs": names})', "            pass")],
                                            [("test_a_key_with_only_failing_jobs_fails_aggregation", {"red": "failed-tests"})]),
        "confinement-failed not failing": ([('"evidence-mismatch", "confinement-failed", "wrong-job-state")', '"evidence-mismatch", "wrong-job-state")')],
                                           [("test_a_key_with_only_failing_jobs_fails_aggregation", {"red": "confinement-failed"})]),
        "provenance unsorted": ([('        prov = sorted((j for rec in recs for j in rec["provenance"]),\n                      key=lambda j: (j["route"], j["runner_image"], j["job_id"]))', '        prov = [j for rec in recs for j in rec["provenance"]]')],
                                [("test_equal_evidence_aggregates_to_one_record_with_sorted_union_provenance", {})]),
        "one disagreement stops every key": ([("            out[\"disagreements\"].append({\"key\": repr(key), \"why\": why, \"jobs\": names})\n            continue", "            out[\"disagreements\"].append({\"key\": repr(key), \"why\": why, \"jobs\": names})\n            break")],
                                             [("test_different_evidence_is_a_disagreement_naming_every_job_and_other_keys_still_emit", {})]),
        "unavailable rows unnamed (Q6a)": ([("            out[\"unavailable\"].append(f\"{row['route']} on {row['runner_image']}\")", "            pass")],
                                           [("test_excluded_and_refused_only_keys_are_listed_not_failures_and_a_missing_row_is_unavailable", {})]),
        "compare provenance as evidence (INV-SA6: two agreeing jobs become a false conflict)": (
            [('        base = {k: v for k, v in recs[0].items() if k != "provenance"}\n        if any({k: v for k, v in rec.items() if k != "provenance"} != base for rec in recs[1:]):',
              '        base = dict(recs[0])\n        if any(dict(rec) != base for rec in recs[1:]):')],
            [("test_equal_evidence_aggregates_to_one_record_with_sorted_union_provenance", {})]),
        "bootstrap jobs unnamed (v21)": ([('            out["bootstrap_jobs"] += names', "            pass")],
                                         [("test_bootstrap_jobs_aggregate_to_records_named_as_bootstrap_and_a_mixed_key_disagrees", {})]),
        "a mixed bootstrap key aggregates (v21)": ([('        if "bootstrap-pending" in kinds and kinds != {"bootstrap-pending"}:', "        if False:")],
                                                   [("test_bootstrap_jobs_aggregate_to_records_named_as_bootstrap_and_a_mixed_key_disagrees", {})]),
        "excluded counted as a failure": ([('    return bool(summary["disagreements"] or summary["failed_keys"])', '    return bool(summary["disagreements"] or summary["failed_keys"] or summary["excluded"])')],
                                          [("test_excluded_and_refused_only_keys_are_listed_not_failures_and_a_missing_row_is_unavailable", {})]),
        "the key from this runner (Q4)": ([("            key = sv.attestation_key(rec) if isinstance(rec, dict) else None", "            key = sv.attestation_key(sv.attestation_identity()) if isinstance(rec, dict) else None"),
                                           ('        out["records"].append({**base, "provenance": prov})', '        out["records"].append({**base, **{k: sv.attestation_identity()[k] for k in sv.KEY_FIELDS}, "provenance": prov})')],
                                          [("test_the_aggregator_takes_each_key_from_its_record_never_from_its_own_runner", {})]),
    }, tmp_path_factory)


def test_the_attestation_constraints_mutation_matrix(tmp_path_factory):
    """P1 for specs/attestation_constraints.py's offline rule."""
    C = "test_the_constraints_check_refuses_an_unpinned_or_out_of_bound_or_unparseable_set"
    _matrix(SPECS / "attestation_constraints.py", "cons", {
        "an unpinned requirement tolerated": ([('            problems.append(f"{req.name} (a direct requirement: {spec!r}) is not pinned")', "            pass")], [(C, {})]),
        "bounds unchecked": ([("            if not req.specifier.contains(Version(v), prereleases=True):", "            if False:")], [(C, {})]),
        "markers unparsed": ([("                Marker(marker)\n", "                pass\n")], [(C, {})]),
        "a range read as a pin": ([('_PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\\s;]+)\\s*(?:;\\s*(.+))?$")', '_PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:==|>=)([^\\s;]+)\\s*(?:;\\s*(.+))?$")')], [(C, {})]),
    }, tmp_path_factory)
