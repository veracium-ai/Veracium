"""0018's closure tables for the adjacent-rungs arc, specs/evidence/0018/closure_mutants.py: one per code finding, current, every row
good, a no-op control per mutated file, each reused row its source table's own, and the table check refuses each tampered table.

THE MAPPING'S CRITERION (research, 2026-11-08): a reused row closes a finding only if reverting it reproduces that finding's failure.
For the design-round findings (rounds 1 to 3: R1-01..R1-06, R2-01..R2-03, E2-01, E2-02, R3-01..R3-03) the row stands in for the code
that implements the fix the design adopted; it is NOT a test of the spec text, which the reviewer accepted at round 3."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load(name="veracium_0018_closure_mutants"):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / "specs" / "evidence" / "0018" / "closure_mutants.py")
        m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return sys.modules[name]


cm = _load()


def _reviews():
    spec = importlib.util.spec_from_file_location("veracium_reviews_for_0018_closure", ROOT / "specs" / "reviews.py")
    rv = importlib.util.module_from_spec(spec); spec.loader.exec_module(rv)
    return rv.REVIEWS


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
    """Every finding reuses the implementation table's mutants BY ID: each must be the very tuple that table defines and the very
    definition its committed table ran (research: two rows were re-anchored at round 6, so the digest is compared, not the id)."""
    src = cm._source()
    theirs = {m[0]: cm._protocol.definition_sha(m) for m in src.MUTANTS}
    ran = {r["id"]: r["definition_sha256"] for r in json.loads(src.TABLE.read_text(encoding="utf-8"))["rows"]}
    for fid, s in cm.SUBJECTS.items():
        for m in s.mutants:
            assert theirs.get(m[0]) == cm._protocol.definition_sha(m) == ran.get(m[0]), (fid, m[0])


def test_every_raised_adjacent_code_finding_has_a_table_and_only_the_three_exempt_ones_do_not():
    """R1-07 closed by narrowing the spec's claim, C5-01 by the v9.1 text, C5-02 in the round-6 package's stage: none touched a
    non-test .py, so the closure-mutant rule exempts them by property, and they have no table."""
    raised = {f for r in _reviews() if r["spec"] == "0018" for f in r.get("raised", []) if f.startswith(cm.P)}
    assert raised - set(cm.FINDINGS) == {cm.P + "R1-07", cm.P + "C5-01", cm.P + "C5-02"}, sorted(raised - set(cm.FINDINGS))
    assert set(cm.FINDINGS) <= raised


def test_each_adjacent_row_names_its_own_ordinal_and_raises_only_its_own_round_s_ids():
    """The arc is recorded as 0018 rounds 5-10 while its verdicts, the spec's table and its ids count 1-6 (research): row k+4 says
    "0018-adjacent-rungs round k" and raises only AR-R<k>, AR-E<k> or AR-C<k> ids."""
    rows = [r for r in _reviews() if r["spec"] == "0018" and r["round"] >= 5]
    assert sorted({r["round"] for r in rows}) == list(range(5, 11))
    for r in rows:
        k = r["round"] - 4
        assert f"0018-adjacent-rungs round {k}" in r["verdict"], (r["round"], r["verdict"][:80])
        for f in r.get("raised", []):
            assert re.fullmatch(rf"0018-AR-[REC]{k}-0\d", f), (r["round"], f)


SUBJ = cm.P + "R4-02"


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


RM = "src/veracium/store/release_migration.py"
TAMPERS = {
    "edited after writing": (lambda t: t["rows"][0].__setitem__("what", "edited"), False, "does not match its own body digest"),
    "a row not killed": (lambda t: t["rows"][0].update(outcome="SURVIVED"), True, "not a good row"),
    "a named cell that passed": (lambda t: t["rows"][0].update(cells_failed=[]), True, "not a good row"),
    "an honest probe that failed": (lambda t: t["rows"][0].update(honest="fail: 1 failed, 0 errored of 1"), True, "not a good row"),
    "a missing row": (lambda t: t["rows"].pop(), True, "the rows are not one per mutant"),
    "a stale digest": (lambda t: t["header"]["digests"].__setitem__(RM, "0" * 64), True, "stale: "),
    "a changed definition": (lambda t: t["header"]["definitions"].__setitem__(cm.SUBJECTS[SUBJ].mutants[0][0], "0" * 64), True,
                             "the mutant definitions differ"),
    "a red clean run": (lambda t: t["header"]["clean"]["first"].__setitem__("ok", False), True, "the clean runs are not both green"),
    "a no-op control that killed": (lambda t: t["controls"][0].update(outcome="KILLED"), True, "negative control is not good"),
    "a no-op control whose cells never ran": (lambda t: t["controls"][0].update(cells_passed=[]), True, "negative control is not good"),
    "another finding": (lambda t: t["header"].__setitem__("finding", cm.P + "R4-03"), True, f"not 0018/{SUBJ}"),
    "another spec": (lambda t: t["header"].__setitem__("spec", "0048"), True, f"not 0018/{SUBJ}"),
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
