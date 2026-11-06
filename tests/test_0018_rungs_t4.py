"""0018 §4j.9 (T4): the product's recovery classifier against the table extracted from the spec, input by input. The reference is
specs/evidence/0018-adjacent-rungs/closure/recovery_v05.py over recovery-table-v051.json: it reads its rows from the spec's own
text, so a row retyped wrongly in `classify_recovery` differs here. I35 (i) to (iii)."""
from __future__ import annotations

import importlib.util
import inspect
import itertools
import pathlib
import re
import sys

import pytest

import veracium.store.release_migration as rm

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLOSURE = ROOT / "specs" / "evidence" / "0018-adjacent-rungs" / "closure"
RUNGS = ((1, 2), (13, 14), (15, 16))
TRI = (True, False, None)
STATES = sorted(rm._RESULTING_STATES)


def _reference():
    name = "veracium_recovery_v05"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, CLOSURE / "recovery_v05.py")
        m = importlib.util.module_from_spec(spec)
        sys.modules[name] = m
        spec.loader.exec_module(m)
        m.load(CLOSURE / "recovery-table-v051.json")
    return sys.modules[name]


REF = _reference()
OUTCOMES = sorted(rm.TERMINAL_OUTCOMES) + ["a-future-outcome"]
PREFLIGHT = sorted(set(OUTCOMES) | {"current", "mint-contention", "invalid-request", "newer", "migration-source-missing", "locked"})


def _versions(b, t):
    return (None, b, t, t + 1)


def _facts(b, t):
    """Every class of facts `problems()` admits, and every state and version beside them."""
    for tri in TRI:
        for state, version in itertools.product(STATES, _versions(b, t)):
            yield (tri, tri, state, version)


def _lawful(o, b, t, f):
    return not rm.TerminalFacts(o, b, t, *f).problems() if o in rm.TERMINAL_OUTCOMES else True


def _same(p, r):
    return (p.row, tuple(p.actions), p.counted) == (r.row, tuple(r.actions), r.counted)


@pytest.mark.parametrize("b, t", RUNGS, ids=lambda v: str(v))
def test_the_classifier_equals_the_extracted_table_input_by_input(b, t):
    """Every outcome (a later head's included), every fact class, every state and version, on the delegated route and carried by a
    write error. Wider than what `problems()` admits, so a row that differs anywhere differs here."""
    n = 0
    for o, f in itertools.product(OUTCOMES, _facts(b, t)):
        for route in ("delegated", "write-error"):
            got, want = rm.classify_recovery(route, o, f, t), REF.classify(route, o, f, t)
            assert _same(got, want), (route, o, f, got, want)
            n += 1
    for o in REF.NO_RECORD:
        got, want = rm.classify_recovery("delegated", o, None, t), REF.classify("delegated", o, None, t)
        assert _same(got, want), (o, got, want)
    assert n > 1000, n


def test_the_preflight_rows_equal_the_extracted_table():
    for o, state in itertools.product(PREFLIGHT, STATES + [None]):
        facts = (False, False, state, None)
        got, want = rm.classify_recovery("preflight", o, facts), REF.classify("preflight", o, facts)
        assert _same(got, want), (o, state, got, want)


def test_the_routes_without_facts_equal_the_extracted_table():
    for route in ("unexpected-base", "read-error", "package-pre-mint"):
        assert _same(rm.classify_recovery(route), REF.classify(route)), route


class _Readback:
    kind = "record"

    def __init__(self, facts):
        self.facts = facts


@pytest.mark.parametrize("o, frm, to, tri", [
    ("package-inconsistent", 13, 14, True), ("package-inconsistent", 13, 14, False), ("package-inconsistent", 13, 14, None),
    ("migrated", 13, 14, True), ("package-inconsistent", 14, 15, True)],
    ids=["bound committed", "bound unchanged", "bound unknown", "another outcome", "another rung"])
def test_a_package_escape_counts_only_a_bound_readback(o, frm, to, tri):
    f = rm.TerminalFacts(o, frm, to, tri, tri, "destination" if tri else ("source" if tri is False else "unknown"),
                         to if tri else (frm if tri is False else None))
    got = rm.classify_recovery("package-post-mint", minted=(13, 14), readback_facts=f)
    want = REF.classify("package-post-mint", ctx=(13, 14), readback=_Readback(f))
    assert _same(got, want), (got, want)
    assert got.counted == (o == "package-inconsistent" and (frm, to) == (13, 14) and tri is True)


def test_no_readback_counts_nothing():
    assert rm.classify_recovery("package-post-mint", minted=(13, 14)) == rm.RecoveryDecision("E4", ("repair-build",), False)


@pytest.mark.parametrize("b, t", RUNGS, ids=lambda v: str(v))
def test_every_admitted_input_has_exactly_one_store_action(b, t):
    """I35 (i): the classifier is total on what `problems()` admits, and every route gives exactly one store-side id."""
    rows = {}
    for o, f in itertools.product(sorted(rm.TERMINAL_OUTCOMES), _facts(b, t)):
        if not _lawful(o, b, t, f):
            continue
        d = rm.classify_recovery("delegated", o, f, t)
        assert len(d.actions) == 1, (o, f, d)
        rows[d.row] = rows.get(d.row, 0) + 1
    print(f"{b}->{t}: {dict(sorted(rows.items()))}")
    assert {"C1", "C2", "K", "U0"} <= set(rows), rows


def test_the_reviewers_equal_input_pairs_get_one_conservative_action():
    """I35 (ii): one input, two causes, so one conditional, and the classifier never claims which."""
    unaccepted = (False, False, "unaccepted", None)
    assert rm.classify_recovery("delegated", "migration-source-missing", unaccepted, 14).actions == ("conditional-other-writer-or-path",)
    newer = (False, False, "unaccepted", None)
    assert rm.classify_recovery("delegated", "newer", newer, 14).actions == ("conditional-other-writer-or-newer-build",)


@pytest.mark.parametrize("o, f", [("migrated", (True, True, "destination", 14)), ("internal-error", (True, True, "destination", 14)),
                                  ("unsupported-migration", (False, False, "source", 13))], ids=["migrated", "internal-error", "unsupported"])
def test_the_same_facts_as_a_record_and_as_a_write_error_get_the_same_store_action(o, f):
    """I35 (iii), R3-02: an escape never continues, and it adds the disclosure; the count is the record's."""
    rec, esc = rm.classify_recovery("delegated", o, f, 14), rm.classify_recovery("write-error", o, f, 14)
    want = "rerun-resumes-store" if rec.actions == ("continue",) else rec.actions[0]
    assert esc.actions == (want, "audit-record-not-published") and esc.counted == rec.counted


def test_every_action_the_table_names_has_prose_and_a_rerun_answer():
    named = {a for r in REF.TABLE.values() for a in r["actions"]} - {"continue", "continue-uncounted", "audit-record-not-published"}
    assert named == set(rm.RECOVERY_PROSE), named ^ set(rm.RECOVERY_PROSE)
    for action, (rerun, prose) in rm.RECOVERY_PROSE.items():
        assert rerun and prose, action


def test_no_action_promises_a_rerun_repairs_the_missing_record():
    """§4j.10's limit: an audit record missing after a committed rung is reported, not repaired, so no prose may say otherwise."""
    for action, (rerun, prose) in rm.RECOVERY_PROSE.items():
        assert not re.search(r"repair\w*\b.*\brecord", prose), (action, prose)


def test_the_classifier_takes_no_diagnostic():
    """§4j.9: it never reads diagnostic prose, so it is not given any."""
    assert not {"diagnostic", "message", "text"} & set(inspect.signature(rm.classify_recovery).parameters)
