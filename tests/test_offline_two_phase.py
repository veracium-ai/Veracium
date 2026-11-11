"""specs/evidence/offline/two_phase.py, the offline launcher's two-phase split (the owner, 2026-11-08): which files run in one
process, and the check that refuses unless the two phases ran exactly the collected suite. P1's matrix for two_phase.py."""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
OFF = ROOT / "specs" / "evidence" / "offline"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


TP = _load(OFF / "two_phase.py", "offline_two_phase")

IDS = ["tests/test_a.py::test_one", "tests/test_a.py::test_p[x::y]", "tests/test_a.py::TestK::test_m",
       "tests/sub/test_b.py::test_two", "tests/test_seam_model_z.py::test_s"]
P2 = ["tests/test_seam_model_z.py"]


def _collect(ids=IDS, count=None):
    return "\n".join(ids) + f"\n\n{len(ids) if count is None else count} tests collected in 0.01s\n"


def _junit(ids, failed=(), skipped=()):
    s = ET.Element("testsuite", name="pytest")
    for n in ids:
        c, name = TP.junit_key(n)
        tc = ET.SubElement(s, "testcase", classname=c, name=name)
        if n in failed:
            ET.SubElement(tc, "failure", message="assert 0")
        if n in skipped:
            ET.SubElement(tc, "skipped", message="why")
    s.set("tests", str(len(ids)))
    s.set("failures", str(len([n for n in ids if n in failed])))
    s.set("errors", "0")
    s.set("skipped", str(len([n for n in ids if n in skipped])))
    root = ET.Element("testsuites")
    root.append(s)
    return ET.tostring(root)


P1_IDS, P2_IDS = IDS[:4], IDS[4:]


def _lines(n1, n2):
    return [f"{n1} passed in 1.00s", f"{n2} passed in 1.00s"]


def test_the_phase2_files_are_the_rule_ci_shard_uses():
    """Two carriers of one rule (ci_shard's _is_seam and this module's), compared over the real tests/ directory."""
    shard = _load(ROOT / ".github" / "ci_shard.py", "ci_shard_for_two_phase")
    theirs = sorted(f"tests/{p.name}" for p in (ROOT / "tests").glob("*.py") if shard._is_seam(p))
    assert TP.phase2_files(ROOT / "tests") == theirs
    assert theirs, "no phase-2 file: the seam gate moved, and the split no longer matches the suite"


def test_a_clean_two_phase_run_passes_and_counts_from_the_junits():
    problems, t = TP.check(_collect(), _junit(P1_IDS, skipped={IDS[1]}), _junit(P2_IDS), ["3 passed, 1 skipped in 1s",
                                                                                         "1 passed in 1s"], P2)
    assert problems == []
    assert (t["passed"], t["skipped"], t["failed"]) == (4, 1, 0)


def _refused(want, collect=None, p1=None, p2=None, lines="default", phase2=P2, rcs=(0, 0)):
    lines = _lines(len(P1_IDS), len(P2_IDS)) if lines == "default" else lines
    problems, _ = TP.check(collect or _collect(), p1 or _junit(P1_IDS), p2 or _junit(P2_IDS), lines, phase2, rcs)
    assert any(want in p for p in problems), (want, problems)


def test_the_check_refuses_each_broken_run():
    """Each the reviewer's next mutant of a split run, in turn: the artifact this matrix binds is two_phase.py."""
    _refused("ran in neither phase", p1=_junit(P1_IDS[:-1]), lines=_lines(3, 1))
    _refused("ran more than once", p2=_junit(P2_IDS + [IDS[0]]), lines=_lines(4, 2), phase2=None)
    _refused("phase 1 ran a phase-2 file", p1=_junit(P1_IDS + P2_IDS), p2=_junit([]), lines=_lines(5, 0))
    _refused("phase 2 ran file(s) outside", p1=_junit(P1_IDS[1:]), p2=_junit(P2_IDS + P1_IDS[:1]), lines=_lines(3, 2))
    _refused("were not collected", p1=_junit(P1_IDS + ["tests/test_a.py::test_ghost"]), lines=_lines(5, 1))
    _refused("disagrees with its junit", lines=["99 passed in 1s", "1 passed in 1s"])
    _refused("phase 1: 1 failed", p1=_junit(P1_IDS, failed={IDS[0]}), lines=["1 failed, 3 passed in 1s", "1 passed in 1s"])
    _refused("does not count its", collect=_collect(count=4))
    _refused("is not a node-id list", collect="not an id\n\n1 test collected\n")
    _refused("phase 2 exited 5 (no tests ran) while the collection gives it 1", p1=_junit(P1_IDS), p2=_junit([]),
             lines=_lines(4, 0), rcs=(0, 5))
    _refused("phase 1 exited 2", rcs=(2, 0))


def test_an_empty_phase_under_a_narrowed_selection_is_empty_not_red():
    """Research's E1: with -k the collection itself narrows; a phase whose share of it is empty exits 5, and that is not red."""
    ids = IDS[:2]
    problems, t = TP.check(_collect(ids), _junit(ids), _junit([]), ["2 passed in 1s", "no tests ran in 0.01s"], P2, (0, 5))
    assert problems == [] and t["passed"] == 2


def test_a_marked_file_outside_the_seam_glob_joins_phase_2(tmp_path):
    """The rule is the gate's own mark first: a file refusing an xdist worker joins phase 2 whatever its name."""
    t = tmp_path / "tests"
    t.mkdir()
    (t / "test_plain.py").write_text("def test_x():\n    pass\n")
    # the mark built from TP.SEAM_MARK, never written out here: a literal would make THIS file a phase-2 file (and ci_shard's)
    (t / "test_gate.py").write_text('import os\nassert os.environ.get("' + TP.SEAM_MARK + '\n')
    (t / "test_seam_model_q.py").write_text("def test_y():\n    pass\n")
    assert TP.phase2_files(t) == ["tests/test_gate.py", "tests/test_seam_model_q.py"]


def test_the_phase2_rule_equals_g1_as_the_joint_groups_document_names_it():
    doc = (OFF / "JOINT-TEST-GROUPS.md").read_text(encoding="utf-8")
    assert TP.g1_members(doc) == TP.phase2_files(ROOT / "tests") != []


def test_the_suite_line_is_pytests_grammar_and_never_says_zero_failed():
    import collections
    t = collections.Counter(passed=8827, skipped=60)
    line = TP.suite_line(t, 1234.5)
    assert line == "8827 passed, 60 skipped in 1234.50s"
    assert "failed" not in line and "error" not in line
    assert TP.suite_line(collections.Counter(failed=1, passed=2, error=1)) == "1 failed, 2 passed, 1 error"
    assert TP.suite_line(collections.Counter()) == "no tests ran"


def test_two_collected_ids_with_one_junit_key_refuse_rather_than_merge():
    ids = ["tests/test_a.py::K::test_one", "tests/test_a/K.py::test_one"]    # both are (tests.test_a.K, test_one)
    problems, _ = TP.check(_collect(ids), _junit(ids[:1]), _junit([]), None, None)
    assert any("share a junit key" in p for p in problems), problems


def test_the_junit_key_keeps_the_brackets_whole_and_joins_a_class():
    assert TP.junit_key("tests/test_a.py::test_p[x::y]") == ("tests.test_a", "test_p[x::y]")
    assert TP.junit_key("tests/test_a.py::TestK::test_m") == ("tests.test_a.TestK", "test_m")
    assert TP._module("tests.test_a.TestK") == "tests/test_a.py"
    assert TP._module("tests.sub.test_b") == "tests/sub/test_b.py"


def test_the_merged_junit_holds_both_phases_and_the_manifest_reads_it(tmp_path):
    merged = TP.merge(_junit(P1_IDS, skipped={IDS[1]}), _junit(P2_IDS))
    root = ET.fromstring(merged)
    suites = list(root.iter("testsuite"))
    assert len(suites) == 2 and [len(list(x.iter("testcase"))) for x in suites] == [len(P1_IDS), len(P2_IDS)]
    assert ET.tostring(suites[1]) == ET.tostring(ET.fromstring(_junit(P2_IDS))[0])      # copied verbatim
    one = ET.fromstring(TP.merge(_junit(P1_IDS), _junit([])))
    assert len(list(one.iter("testcase"))) == len(P1_IDS) != len(IDS)               # a merge missing a phase is short
    tm = _load(OFF / "testcase_manifest.py", "offline_manifest_for_two_phase")
    f = tmp_path / "merged.xml"
    f.write_bytes(merged)
    _rows, counts = tm.manifest(str(f))
    assert counts["passed"] == 4 and counts["skipped"] == 1


def test_the_launcher_asks_two_phase_for_the_split_and_checks_it_with_the_files():
    """The launcher's own text: the split's files come from two_phase.py, and the check is given --tests so the split is
    checked, not only the totals. A launcher that dropped either would still print a green line."""
    sh = (OFF / "run_offline.sh").read_text(encoding="utf-8")
    assert '"$HERE/two_phase.py" files tests' in sh
    assert "--tests tests" in sh and '--merge "$JUNIT"' in sh and '--rc "$RC1" "$RC2"' in sh
    assert 'VERACIUM_OFFLINE_MODE:-two-phase' in sh
    assert '--collect-only -q tests -p no:randomly \\\n    "${ARGS[@]}"' in sh       # the collection takes the phases' selection
    assert sh.rstrip().splitlines()[-1].lstrip().startswith("--merge"), "the check's line must be the transcript's last"
    assert sys.version_info >= (3, 10)


def test_a_non_strict_xpass_reconciles_as_the_passed_testcase_junit_records():
    """pytest's line says "1 xpassed" where its junit records a plain passed testcase; the summary check must add them."""
    problems, _ = TP.check(_collect(), _junit(P1_IDS), _junit(P2_IDS), ["3 passed, 1 xpassed in 1s", "1 passed in 1s"], P2,
                           (0, 0))
    assert problems == [], problems


def test_a_narrowed_collection_is_read_and_must_add_up():
    """Research's L1: under -k or -m pytest prints "N/M tests collected (K deselected)"; N must be the listed ids and M - N must
    be K. Before this, every narrowed run refused."""
    ids = IDS[:2]
    text = "\n".join(ids) + "\n\n2/9 tests collected (7 deselected) in 0.01s\n"
    try:
        got = TP.collected(text)
    except ValueError as e:
        raise AssertionError(f"a narrowed collection refused: {e}") from e
    assert got == ids
    for bad in ("3/9 tests collected (6 deselected)", "2/9 tests collected (6 deselected)", "2/9 tests collected"):
        try:
            TP.collected("\n".join(ids) + f"\n\n{bad} in 0.01s\n")
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad!r}")


def test_a_refused_collection_still_counts_what_ran():
    """Research's L2: the suite line is counted from the junits even when the collection refuses, so it never says "no tests
    ran" over a run that ran."""
    problems, t = TP.check("garbage\n", _junit(P1_IDS), _junit(P2_IDS), None, P2, (0, 0))
    assert problems and t["passed"] == len(IDS)


def test_a_marked_test_module_in_a_subdirectory_joins_phase_2(tmp_path):
    """Research's L5: ci_shard applies the mark to every test module, subdirectories included; so does this rule."""
    t = tmp_path / "tests"
    (t / "sub").mkdir(parents=True)
    (t / "sub" / "test_deep.py").write_text('import os\nassert os.environ.get("' + TP.SEAM_MARK + '\n')
    (t / "sub" / "helper.py").write_text('import os\nassert os.environ.get("' + TP.SEAM_MARK + '\n')   # not a test module
    (t / "sub" / "deep_test.py").write_text('import os\nassert os.environ.get("' + TP.SEAM_MARK + '\n')  # pytest's other form
    assert TP.phase2_files(t) == ["tests/sub/deep_test.py", "tests/sub/test_deep.py"]


def test_only_a_real_positional_is_refused_never_an_options_value():
    """Research's L4: `-k specs` and `--deselect tests/x.py::t` carry values, not paths; a bare path or node id is refused."""
    assert TP.positionals(["-k", "specs"]) == []
    assert TP.positionals(["--deselect", "tests/x.py::t", "-m", "slow", "-x"]) == []
    assert TP.positionals(["-k=specs", "--deselect=tests/x.py::t"]) == []
    assert TP.positionals(["tests/x.py"]) == ["tests/x.py"]
    assert TP.positionals(["-x", "tests/x.py::t"]) == ["tests/x.py::t"]


def test_the_launcher_reads_a_failed_collection_instead_of_dying_on_it():
    """Research's L3: under set -e a bare collection command that exits non-zero ends the script before its own branch runs."""
    sh = (OFF / "run_offline.sh").read_text(encoding="utf-8")
    assert '2>&1 || CRC=$?' in sh and 'CRC=0\n' in sh
    assert '"$HERE/two_phase.py" positionals "${ARGS[@]}" || exit 2' in sh


def test_an_empty_selection_is_refused_by_name_never_passed():
    """A selection that collects nothing ran nothing: refused with that reason, and the suite line says "no tests ran"."""
    problems, t = TP.check("\nno tests collected (8899 deselected) in 0.5s\n", _junit([]), _junit([]), None, P2, (5, 5))
    assert problems and "collected no tests" in problems[0]
    assert TP.suite_line(t) == "no tests ran"
    assert TP._last_line("286 deselected in 0.40s") == "286 deselected in 0.40s"


def _with_module_skip(junit_bytes, name, child="skipped"):
    """A junit as pytest writes a module skipped at collection: ONE testcase, an empty classname, the dotted module path as
    its name, and a single child (<skipped> for a skip; another tag forges a nameless entry that is not one)."""
    root = ET.fromstring(junit_bytes)
    s = root.find("testsuite")
    tc = ET.SubElement(s, "testcase", classname="", name=name)
    ET.SubElement(tc, child, message="could not import 'mcp': No module named 'mcp'")
    s.set("tests", str(int(s.get("tests")) + 1))
    if child == "skipped":
        s.set("skipped", str(int(s.get("skipped")) + 1))
    return ET.tostring(root)


MODS = ["tests/test_a.py", "tests/sub/test_b.py", "tests/test_seam_model_z.py", "tests/test_c.py"]


def test_a_module_skipped_at_collection_is_accounted_for_not_uncollected():
    """Found at the shipped-changes round-2 pin: on a host without `mcp`, 0053's adapter suite skips whole at import; its one
    junit entry (empty classname, the module as its name) was refused as a node that ran uncollected, failing a green run."""
    p1 = _with_module_skip(_junit(P1_IDS), "tests.test_c")
    problems, n = TP.check(_collect(), p1, _junit(P2_IDS), phase2=P2, modules=MODS)
    assert problems == [] and n["skipped"] == 1, (problems, n)


def test_a_module_skip_naming_no_test_module_of_the_run_stays_uncollected():
    """Research's cross-check (a): the entry must name one of the run's own test modules. One naming a module the tree does
    not hold stays a node that ran uncollected."""
    p1 = _with_module_skip(_junit(P1_IDS), "tests.test_absent")
    problems, _n = TP.check(_collect(), p1, _junit(P2_IDS), phase2=P2, modules=MODS)
    assert any("ran that were not collected" in p for p in problems), problems


def test_with_no_module_set_a_module_skip_is_not_accounted_for():
    """Fail closed: a caller that gives no module set accounts for no module skip."""
    p1 = _with_module_skip(_junit(P1_IDS), "tests.test_c")
    problems, _n = TP.check(_collect(), p1, _junit(P2_IDS), phase2=P2)
    assert any("ran that were not collected" in p for p in problems), problems


def test_a_skipped_module_whose_nodes_were_collected_is_refused():
    """The accounting holds only when NONE of the module's nodes was collected: a module both collected and reported as
    skipped whole is a contradiction, refused by name."""
    p1 = _with_module_skip(_junit(P1_IDS), "tests.test_a")
    problems, _n = TP.check(_collect(), p1, _junit(P2_IDS), phase2=P2, modules=MODS)
    assert any("tests/test_a.py is reported skipped at collection" in p for p in problems), problems


def test_a_nameless_entry_that_is_not_a_skip_is_still_uncollected():
    """Only pytest's skip form is accounted for: a nameless entry carrying an <error> (a collection error) stays a node
    that ran uncollected, and its error is counted."""
    p1 = _with_module_skip(_junit(P1_IDS), "tests.test_c", child="error")
    problems, _n = TP.check(_collect(), p1, _junit(P2_IDS), phase2=P2, modules=MODS)
    assert any("ran that were not collected" in p for p in problems), problems
