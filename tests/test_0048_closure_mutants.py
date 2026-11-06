"""0048's closure tables, specs/evidence/0048/closure_mutants.py: one per code finding, current, every row good, a no-op control per
mutated file, and the table check refuses each tampered table."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load(name="veracium_0048_closure_mutants"):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / "specs" / "evidence" / "0048" / "closure_mutants.py")
        m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return sys.modules[name]


cm = _load()


def test_every_closure_table_is_current_and_every_row_good():
    assert cm.problems() == []


def test_every_mutated_file_has_a_no_op_control_naming_its_mutants_cells():
    """An unmutated-in-behaviour copy of each file passes the same cells, so a kill can never be a cell that fails on ANY change."""
    for fid, s in cm.SUBJECTS.items():
        noops = {k[1]: k for k in s.controls if k[5] == "SURVIVED"}
        for rel in sorted({m[2] for m in s.mutants}):
            assert rel in noops, f"{fid}: {rel} has mutants and no no-op control"
            assert set(noops[rel][3]) == {c for m in s.mutants if m[2] == rel for c in m[4]}, (fid, rel)


def test_a_reused_row_is_its_source_tables_own_definition():
    """The product findings reuse the implementation table's mutants BY ID: each must be the very tuple it runs."""
    for fid, (_fix, mutants, _files, src) in cm.FINDINGS.items():
        if src is None:
            continue
        theirs = {m[0]: cm._protocol.definition_sha(m) for m in cm._source(src).MUTANTS}
        for m in mutants:
            assert theirs.get(m[0]) == cm._protocol.definition_sha(m), (fid, m[0], src)


def test_every_raised_code_finding_has_a_table_and_only_the_two_exempt_ones_do_not():
    spec = importlib.util.spec_from_file_location("veracium_reviews_for_0048_closure", ROOT / "specs" / "reviews.py")
    rv = importlib.util.module_from_spec(spec); spec.loader.exec_module(rv)
    raised = {f for r in rv.REVIEWS if r["spec"] == "0048" for f in r.get("raised", [])}
    assert raised - set(cm.FINDINGS) == {"0048-R1-04", "0048-R1-05"}, sorted(raised - set(cm.FINDINGS))
    assert set(cm.FINDINGS) <= raised


SUBJ = "0048-R3-03"


def _base():
    s = cm.SUBJECTS[SUBJ]
    t = json.loads(s.table.read_text(encoding="utf-8"))
    t["header"]["digests"] = s.digests(ROOT)
    return t


def _write(tmp_path, t, redigest=True):
    if redigest:
        t["body_sha256"] = hashlib.sha256(cm.canonical({k: v for k, v in t.items() if k != "body_sha256"})).hexdigest()
    p = tmp_path / "mutation-table.json"
    p.write_text(cm.render(t), encoding="utf-8")
    return p


TAMPERS = {
    "edited after writing": (lambda t: t["rows"][0].__setitem__("what", "edited"), False, "does not match its own body digest"),
    "a row not killed": (lambda t: t["rows"][0].update(outcome="SURVIVED"), True, "not a good row"),
    "a named cell that passed": (lambda t: t["rows"][0].update(cells_failed=[]), True, "not a good row"),
    "an honest probe that failed": (lambda t: t["rows"][0].update(honest="fail: 1 failed, 0 errored of 1"), True, "not a good row"),
    "a missing row": (lambda t: t["rows"].pop(), True, "the rows are not one per mutant"),
    "a stale digest": (lambda t: t["header"]["digests"].__setitem__(cm.CFG, "0" * 64), True, "stale: "),
    "a changed definition": (lambda t: t["header"]["definitions"].__setitem__(cm.FINDINGS[SUBJ][1][0][0], "0" * 64), True,
                             "the mutant definitions differ"),
    "a red clean run": (lambda t: t["header"]["clean"]["first"].__setitem__("ok", False), True, "the clean runs are not both green"),
    "a no-op control that killed": (lambda t: t["controls"][0].update(outcome="KILLED"), True, "negative control is not good"),
    "a no-op control whose cells never ran": (lambda t: t["controls"][0].update(cells_passed=[]), True, "negative control is not good"),
    "another finding": (lambda t: t["header"].__setitem__("finding", "0048-R4-02"), True, "not 0048/0048-R3-03"),
    "another spec": (lambda t: t["header"].__setitem__("spec", "0007"), True, "not 0048/0048-R3-03"),
}


def test_the_table_check_refuses_each_tampered_table(tmp_path):
    check = _load().SUBJECTS[SUBJ].problems          # the artifact this matrix binds (P1): closure_mutants.py
    (tmp_path / "control").mkdir()
    assert check(_write(tmp_path / "control", _base())) == []           # the untampered copy passes
    for name, (tamper, redigest, want) in TAMPERS.items():
        t = copy.deepcopy(_base())
        tamper(t)
        d = tmp_path / name.replace(" ", "-")
        d.mkdir()
        probs = check(_write(d, t, redigest))
        assert any(want in p for p in probs), (name, probs)


def test_a_missing_table_is_named_by_the_whole_check(tmp_path, monkeypatch):
    """The set check: a finding whose table was never written (or one left on disk for no finding) is a problem."""
    monkeypatch.setattr(cm, "TABLES", tmp_path)
    assert any("not one per finding" in p for p in cm.problems())
