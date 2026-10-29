"""0003/within-episode §6's mutation table, specs/evidence/0003/within_episode_mutants.py: current, every row good,
a no-op control per mutated file, and the table check refuses each tampered table."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load(name="veracium_within_episode_mutants"):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / "specs" / "evidence" / "0003" / "within_episode_mutants.py")
        m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return sys.modules[name]


wm = _load()


def test_the_mutation_table_is_current_and_every_row_good():
    assert wm.problems() == []


def test_every_mutated_file_has_a_no_op_control_naming_its_mutants_cells():
    """Research's condition (2026-10-29): an unmutated-in-behaviour copy of each file passes the same cells, so a kill
    can never be a cell that fails on ANY change to the file."""
    noops = {k[1]: k for k in wm.CONTROLS if k[5] == "SURVIVED"}
    for rel in sorted({m[2] for m in wm.MUTANTS}):
        assert rel in noops, f"{rel} has mutants and no no-op control"
        assert set(noops[rel][3]) == {c for m in wm.MUTANTS if m[2] == rel for c in m[4]}, rel


def test_a_no_op_control_whose_cells_never_ran_is_not_good(tmp_path):
    """Research's guard on the protocol's no-op form: 'none failed' is vacuous when nothing was collected. A NO-OP
    control naming a cell that does not exist reads NOT good, run for real on a copy of the tree."""
    import shutil
    bogus = ("NOOP-bogus", wm.G, [("def _within_episode_drafts(", "# no-op\ndef _within_episode_drafts(")],
             [f"{wm.T}::test_no_such_cell_exists"], "a no-op naming a cell that does not exist", "SURVIVED")
    root = tmp_path / "tree"
    wm.SUBJECT_P.snapshot(root)
    row = wm.SUBJECT_P.run_control(root, bogus)
    assert row["outcome"] == "SURVIVED" and row["cells_passed"] == [] and row["good"] is False, row
    real = next(k for k in wm.CONTROLS if k[0] == "NOOP-graph")
    row = wm.SUBJECT_P.run_control(root, (real[0], real[1], real[2], real[3][:1], real[4], real[5]))
    assert row["good"] is True and row["cells_passed"] == real[3][:1], row
    shutil.rmtree(root)


def _base():
    t = json.loads(wm.TABLE.read_text(encoding="utf-8"))
    t["header"]["digests"] = wm._digests(ROOT)
    return t


def _write(tmp_path, t, redigest=True):
    if redigest:
        t["body_sha256"] = hashlib.sha256(wm.canonical({k: v for k, v in t.items() if k != "body_sha256"})).hexdigest()
    p = tmp_path / "mutation-table.json"
    p.write_text(wm.render(t), encoding="utf-8")
    return p


TAMPERS = {
    "edited after writing": (lambda t: t["rows"][0].__setitem__("what", "edited"), False,
                             "does not match its own body digest"),
    "a row not killed": (lambda t: t["rows"][0].update(outcome="SURVIVED"), True, "not a good row"),
    "a named cell that passed": (lambda t: t["rows"][0].update(cells_failed=[]), True, "not a good row"),
    "an honest probe that failed": (lambda t: t["rows"][0].update(honest="fail: 1 failed, 0 errored of 1"), True,
                                    "not a good row"),
    "a missing row": (lambda t: t["rows"].pop(), True, "the rows are not one per mutant"),
    "a stale digest": (lambda t: t["header"]["digests"].__setitem__(wm.G, "0" * 64), True, "stale: "),
    "a changed definition": (lambda t: t["header"]["definitions"].__setitem__(wm.MUTANTS[0][0], "0" * 64), True,
                             "the mutant definitions differ"),
    "a red clean run": (lambda t: t["header"]["clean"]["first"].__setitem__("ok", False), True,
                        "the clean runs are not both green"),
    "a no-op control that killed": (lambda t: t["controls"][0].update(outcome="KILLED"), True,
                                    "negative control is not good"),
    "a no-op control whose cells never ran": (lambda t: t["controls"][0].update(cells_passed=[]), True,
                                              "negative control is not good"),
    "a classifier control that killed": (lambda t: t["controls"][-1].update(outcome="KILLED"), True,
                                         "negative control is not good"),
    "another spec": (lambda t: t["header"].__setitem__("spec", "0007"), True, "not 0003/within-episode"),
}


def test_the_table_check_refuses_each_tampered_table(tmp_path):
    check = _load().problems                     # the artifact this matrix binds (P1): within_episode_mutants.py
    (tmp_path / "control").mkdir()
    assert check(_write(tmp_path / "control", _base())) == []           # the untampered copy passes
    for name, (tamper, redigest, want) in TAMPERS.items():
        t = copy.deepcopy(_base())
        tamper(t)
        d = tmp_path / name.replace(" ", "-")
        d.mkdir()
        probs = check(_write(d, t, redigest))
        assert any(want in p for p in probs), (name, probs)
