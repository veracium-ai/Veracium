"""0011 — standing tests for every campaign mutant that had none.

PROCESS-R6-1: MUTANT-CAMPAIGN.md claimed every fix carried a standing test.
It did not — F1–F4, C1–C4 and the row-unbound withdrawal were verified by
ad-hoc shell plants during the session and never became tests, so neutering
an entire new check left everything green. Every mutant here plants its
attack IN MEMORY (attacked text, fabricated aggregate, patched constant) and
requires the bite; `specs/evidence/0011/mutant_registry.py` binds each
campaign id to its node and derives the totals by executing them.
"""
from __future__ import annotations

import copy
import importlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVID = ROOT / "specs" / "evidence" / "0011"
sys.path.insert(0, str(EVID))

import check_round1_fold as CF                                # noqa: E402
import policy_matrix as PM                                    # noqa: E402
import subject_census as SC                                   # noqa: E402

SPEC = (ROOT / "specs" / "0011-subject-scoped-entitlement.md").read_text()
AGG = json.loads((EVID / "subject_aggregate.json").read_text())


def _attacked(policy_extra, fence):
    t = SPEC.replace(
        "             and self_assertion(incoming)\n    ALLOW    otherwise",
        f"             and {policy_extra}\n"
        "             and self_assertion(incoming)\n    ALLOW    otherwise",
        1)
    return t.replace("## 13. Changes in v7",
                     fence + "\n\n## 13. Changes in v7", 1)


# ---- F1–F4: the fold checker's grammar holes -------------------------------

def test_indented_helper_definition_is_followed():
    t = _attacked("sourced(prior)",
                  "```\n    sourced(e) := e.provenance.source_id is not None\n```")
    assert any("source_id" in b for b in CF.check_r1_1(t)), "F1 regressed"


def test_parenless_binding_is_followed():
    t = _attacked("srcflag",
                  "```\nsrcflag := prior.provenance.source_id is not None\n```")
    assert any("source_id" in b for b in CF.check_r1_1(t)), "F2 regressed"


def test_info_string_fence_is_scanned():
    t = _attacked("sourced(prior)",
                  "```text\nsourced(e) := e.provenance.source_id is not None\n```")
    assert any("source_id" in b for b in CF.check_r1_1(t)), "F3 regressed"


def test_extra_table_row_is_refused():
    t = SPEC.replace("| `user` | `user` | 3 | **REFUSE** | ALLOW |",
                     "| `user` | `user` | 3 | **REFUSE** | ALLOW |\n"
                     "| `user` | `user` | 3 | **ALLOW** | ALLOW |", 1)
    assert CF.check_decision_table(t), "F4 regressed"
    assert not CF.check_decision_table(SPEC), "pristine control"


# ---- the reviewer's round-5 carrier attack ---------------------------------

def test_rider_promise_in_the_row_is_refused():
    # rebuild the row carrying the old promise
    i = SPEC.index("| USER (sole authority: self-assertion) |")
    j = SPEC.index("\n", i)
    t = SPEC[:i] + SPEC[i:j].split("|")[0] + \
        "| USER (sole authority: self-assertion) | **OTHER** | any | " \
        "retires | **REFUSED** | narrow by ruling, with the measurement " \
        "rider |" + SPEC[j:]
    assert any("measurement rider" in b for b in CF.check_carriers(t)), (
        "the row-bound rider check regressed (CARRIER-R5-1)")


# ---- C1–C4: the census figure bindings -------------------------------------

def test_inflated_aggregate_figure_is_refused():
    m = copy.deepcopy(AGG)
    m["predicate_passes"] = 99_999
    assert any("drifted from its artifact" in b
               for b in CF.check_census_figures(SPEC, agg=m)), "C1 regressed"


def test_gutted_candidate_table_is_refused():
    m = copy.deepcopy(AGG)
    m["candidate_table"] = {"me": 31}
    assert CF.check_census_figures(SPEC, agg=m), "C2 regressed"


def test_unmasked_name_in_aggregate_is_refused():
    # the artifact under attack, named in the body (P1's binding):
    assert (EVID / "subject_census.py").exists()
    m = copy.deepcopy(AGG)
    m["candidate_table"] = dict(AGG["candidate_table"])
    m["candidate_table"]["user's friend David"] = 3
    assert any("unmasked" in b for b in SC.validate_aggregate(m)), (
        "C3 regressed — subject_census accepts an unmasked name")
    assert not SC.validate_aggregate(AGG), "pristine control"


def test_spec_figure_drift_is_refused():
    t = SPEC.replace("| predicate passes | **72,253 = 39.4%**",
                     "| predicate passes | **72,254 = 39.4%**", 1)
    assert t != SPEC, "the drift failed to apply"
    assert CF.check_census_figures(t, agg=AGG), "C4 regressed"
    assert not CF.check_census_figures(SPEC, agg=AGG), "pristine control"


# ---- R6-1 and the neutered-check hole --------------------------------------

def test_narrowed_enum_dimension_is_refused(monkeypatch):
    """EVIDENCE-R6-1: removing THIRD_PARTY from DERIVED shrank the claimed
    domain 1,440 → 1,152 with exit 0 — both sides read the constants. The
    enum axes are pinned to the enum itself now."""
    monkeypatch.setattr(PM, "DERIVED",
                        [None] + [a for a in PM.A
                                  if a is not PM.A.THIRD_PARTY])
    assert any("DERIVED" in b for b in PM.problems()), "R6-1 regressed"
    monkeypatch.undo()
    monkeypatch.setattr(PM, "AUTHORS",
                        [a for a in PM.A if a is not PM.A.SYSTEM])
    assert any("AUTHORS" in b for b in PM.problems()), (
        "the AUTHORS axis can still self-narrow")


def test_every_fold_check_is_reached(monkeypatch):
    """PROCESS-R6-1: deleting `check_census_figures` from main()'s sum left
    every test green — nothing proved the aggregation REACHES each check.
    The R14-1 sentinel, per check function."""
    checks = [n for n in dir(CF)
              if n.startswith("check_") and callable(getattr(CF, n))]
    assert len(checks) >= 6, checks
    for name in checks:
        class _Reached(Exception):
            pass

        def _sentinel(*a, _r=_Reached, **k):
            raise _r()

        monkeypatch.setattr(CF, name, _sentinel)
        try:
            CF.main()
        except _Reached:
            pass
        except SystemExit:
            raise AssertionError(
                f"main() finished without invoking {name} — a neutered "
                f"check is invisible (PROCESS-R6-1)")
        else:
            raise AssertionError(
                f"main() returned without invoking {name}")
        monkeypatch.undo()
