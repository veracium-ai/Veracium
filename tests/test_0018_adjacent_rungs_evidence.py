"""specs/0018 v9 §4j (the adjacent-rungs fold): the mutation matrices of the three checkers its evidence directory
carries. Their bytes are the reviewed (or both-seat-run) evidence and are never edited, so each one's P1 pointer is
declared in its directory's MUTATION-MATRIX.txt, admitted by tests/test_spec_gate.py only while the directory's
SHA256SUMS hashes to its pinned value (REVIEWED_EVIDENCE) and the file equals its SUMS line."""
import shutil
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EV = ROOT / "specs" / "evidence" / "0018-adjacent-rungs"


def _run(*args, cwd=ROOT):
    return subprocess.run([sys.executable, "-B", *map(str, args)], cwd=cwd, capture_output=True, text=True,
                          env={"PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})


def test_check_a2_facts_reproduces_its_recorded_output_and_controls():
    """research-v0.3/check_a2_facts.py: every §4e-ii row's facts pass the tree's own TerminalFacts, and its five
    controls (unlawful facts) are refused. Re-run here, its output must equal the recorded one byte for byte, the
    controls line included: a checker that stopped refusing a control would change it."""
    r = _run(EV / "research-v0.3" / "check_a2_facts.py")
    assert r.returncode == 0, r.stderr[-400:]
    recorded = (EV / "research-v0.3" / "check-a2-facts-67bbba6.out").read_text()
    assert r.stdout == recorded, "check_a2_facts.py no longer prints its recorded output"
    assert "controls refused: [True, True, True, True, True]" in r.stdout


def test_head_bound_census_refuses_each_planted_reference(tmp_path):
    """dev-model/head_bound_census.py (R2-03) is the design's census, and it follows calls by name, so it is blind to a table
    (research's stage-1 read). Its claim is about the kernel it was written against, so it runs there: this tree with the
    frozen body in place. `--check` equals its expectation, and its matrix plants nine changes, each refused by name, and runs
    three controls. The live kernel is the repository census's, below."""
    census = EV / "dev-model" / "head_bound_census.py"
    expected = EV / "dev-model" / "head_bound_census.expected.json"
    tree = tmp_path / "at-the-branch"
    shutil.copytree(ROOT / "src", tree / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(ROOT / "specs/evidence/0018/rungs/superseded/migration_at_branch.py", tree / "src/veracium/store/migration.py")
    r = _run(census, tree, "--check", expected)
    assert r.returncode == 0 and r.stdout.startswith("CENSUS EQUAL: 21 references"), r.stdout + r.stderr[-300:]
    m = _run(EV / "dev-model" / "head_bound_census_matrix.py", tree, expected, tmp_path / "matrix")
    assert m.returncode == 0, m.stdout[-600:] + m.stderr[-300:]
    assert m.stdout.rstrip().endswith("CENSUS MATRIX: 12 cases, 0 not as expected")
    assert m.stdout.count("OK  PLANT") == 9 and sum(m.stdout.count(f"OK  {k}") for k in ("honest", "CONTROL")) == 3


def test_the_repository_census_sees_a_table_and_refuses_each_plant(tmp_path):
    """specs/evidence/0018/head_bound_census.py, the repository copy I33 (iii) owes. A census that follows calls by name
    goes blind on a table (research's stage-1 read: a one-entry table read 21 references as 0, and a blind census and a
    clean one print the same), so this one follows a function merely referenced and reads module-level values like
    function bodies, through imports, class attributes included. Its matrix plants each form, research's fourteen other
    table shapes among them, and runs its controls. The kernel takes a target now: 1 reference, the default of `target`, as T2-EXPECTATION.md stated before the code; the rest having
    moved to `target`. The comparison with the RUNTIME table is tests/test_0018_rungs_t1.py's."""
    census = ROOT / "specs/evidence/0018/head_bound_census.py"
    expected = ROOT / "specs/evidence/0018/head_bound_census.expected.json"
    r = _run(census, ROOT, "--check", expected)
    assert r.returncode == 0 and r.stdout.startswith("CENSUS EQUAL: 1 references"), r.stdout + r.stderr[-300:]
    m = _run(ROOT / "specs/evidence/0018/head_bound_census_matrix.py", ROOT, expected, tmp_path / "matrix")
    assert m.returncode == 0, m.stdout[-600:] + m.stderr[-300:]
    assert m.stdout.rstrip().endswith("CENSUS MATRIX: 31 cases, 0 not as expected")
    assert m.stdout.count("OK  PLANT") == 27 and sum(m.stdout.count(f"OK  {k}") for k in ("honest", "CONTROL")) == 4
    assert "PLANT a step named only in FORWARD_ENTRIES" in m.stdout and "table assembled from a named sub-tuple" in m.stdout


def test_check_row_map_refuses_a_stale_row():
    """closure/check_row_map.py (the round-3 closure's check-to-row map): every model check's asserted §7 row and
    ids agree with the table extracted from v0.5.1, every row asserted at least once; with --control (v0.4.1's stale
    U5 `rerun`) it must refuse."""
    tool = EV / "closure" / "check_row_map.py"
    run, table = EV / "closure" / "model-v05-run-67bbba6.jsonl", EV / "closure" / "recovery-table-v051.json"
    ok = _run(tool, run, table)
    assert ok.returncode == 0, ok.stdout[-400:]
    assert ok.stdout.rstrip().endswith("ROWMAP checks=57 disagree=0 rows=24 unexercised=0")
    assert ok.stdout == (EV / "closure" / "check-row-map.md").read_text()
    bad = _run(tool, run, table, "--control")
    assert bad.returncode == 1 and "disagree=1" in bad.stdout
