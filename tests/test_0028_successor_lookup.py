"""specs/0028 round 5 — the mutation matrix for `specs/evidence/0028/check_successor_lookup.py`
(the executable successor-lookup model). The positive run first; then each mutant the
design exists to refuse, planted through the model's injectable lookup / head predicate
against the SAME six store states.
"""
from __future__ import annotations

import importlib.util
import pathlib
from dataclasses import dataclass

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARTIFACT = ROOT / "specs" / "evidence" / "0028" / "check_successor_lookup.py"


def _load():
    import sys
    spec = importlib.util.spec_from_file_location("check_successor_lookup", ARTIFACT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod            # the model's frozen dataclass resolves its module by name
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- positive
def test_the_model_holds_the_observation_table_and_both_invariants(tmp_path):
    """Six states, two principals: the table v11 §5.1 states; B's hidden result
    equals B's missing result whole-object; UNAVAILABLE is never head; the
    result type carries exactly its two fields."""
    m = _load()
    ok, rep = m.run(workdir=tmp_path)
    assert ok, rep
    assert rep["table"]["hidden"] == {"A": ("superseded", 1), "B": ("successor_unavailable", 0)}
    assert rep["table"]["missing"]["B"] == rep["table"]["hidden"]["B"]


# ------------------------------------------------------------------ mutants
def test_v9_typed_result_reintroduces_the_existence_signal(tmp_path):
    """MUTANT 1 — v9's own shape (R4-1 as shipped in the spec): the result gains
    `omitted`/`causes`. B's hidden result then differs from B's missing one by
    a field, and V-NO-EXISTENCE-SIGNAL fails on WHOLE-OBJECT equality — the
    reason the invariant is equality of the object, not of a flag. The artifact
    under test is specs/evidence/0028/check_successor_lookup.py."""
    m = _load()

    @dataclass(frozen=True)
    class Leaky:
        disposition: object
        successors: tuple
        omitted: int
        causes: frozenset

    def leaky(store, user_id, edge_id, principal, policy):
        base = m.successor_lookup(store, user_id, edge_id, principal, policy)
        rows = store.edges(user_id, active_only=False, include_quarantined=True)
        total = sum(1 for e in rows if e.supersedes == edge_id)
        omitted = total - len(base.successors)
        return Leaky(base.disposition, base.successors, omitted,
                     frozenset({"cross_user"}) if omitted else frozenset())

    ok, rep = m.run(lookup=leaky, workdir=tmp_path)
    assert not ok
    assert rep["V-NO-EXISTENCE-SIGNAL (B: hidden == missing, whole object)"] is False
    assert rep["vocabulary closed and result has exactly two fields"] is False


def test_a_head_predicate_that_ignores_the_integrity_signal_is_refused(tmp_path):
    """MUTANT 2 — R4-5's old rule: "no visible successors ⇒ head". It calls the
    MISSING and the HIDDEN cases heads, and V-UNAVAILABLE-NEVER-HEAD fails."""
    m = _load()
    ok, rep = m.run(head_pred=lambda l: len(l.successors) == 0, workdir=tmp_path)
    assert not ok and rep["V-UNAVAILABLE-NEVER-HEAD"] is False


def test_collapsing_the_hidden_case_into_head_trades_a_leak_for_a_lie(tmp_path):
    """MUTANT 3 — the tempting fix: hide the hidden successor by reporting HEAD.
    No existence signal — but B is told a superseded edge is current. The
    table fails (B/hidden must be UNAVAILABLE) and so does NEVER-HEAD."""
    m = _load()

    def collapse(store, user_id, edge_id, principal, policy):
        base = m.successor_lookup(store, user_id, edge_id, principal, policy)
        if base.disposition is m.SuccessorDisposition.SUCCESSOR_UNAVAILABLE:
            return m.SuccessorLookup(m.SuccessorDisposition.HEAD, ())
        return base

    ok, rep = m.run(lookup=collapse, workdir=tmp_path)
    assert not ok and rep["table_matches_spec"] is False and rep["V-UNAVAILABLE-NEVER-HEAD"] is False


def test_the_hand_set_corrected_alone_lies_to_the_principal_on_two_reachable_states(tmp_path):
    """MUTANT 5 — the model's own first cut (research's finding, 2026-09-07):
    `{"corrected"}` alone. A prior retired `superseded` or `absorbed_duplicate`
    with a hidden successor then falls through to HEAD — a lie B can catch on
    the edge's own row — and V-NO-EXISTENCE-SIGNAL and NEVER-HEAD both fail on
    exactly those two states, which are reachable through the public write
    surface (unlike "missing")."""
    m = _load()

    def hand_set(store, user_id, edge_id, principal, policy):
        return m.successor_lookup(store, user_id, edge_id, principal, policy, names_successor={"corrected"})

    ok, rep = m.run(lookup=hand_set, workdir=tmp_path)
    assert not ok
    assert rep["table"]["hidden_superseded"]["B"] == ("head", 0)
    assert rep["table"]["hidden_absorbed"]["B"] == ("head", 0)
    assert rep["table"]["hidden"]["B"] == ("successor_unavailable", 0), "the corrected case alone still reads right — that is why the hand set survived a review"
    assert rep["V-NO-EXISTENCE-SIGNAL (B: hidden == missing, whole object)"] is False
    assert rep["V-UNAVAILABLE-NEVER-HEAD"] is False


def test_the_registry_must_be_total_over_the_dispositioned_reasons():
    """MUTANT 6 — the gate the third registry shares with AS_OF_DISPOSITION: a
    reason missing from it, or one it names that the schema does not, refuses
    at build time; the positive gate holds on the shipped registry."""
    m = _load()
    m.check_registry_total()
    with pytest.raises(AssertionError):
        m.check_registry_total({k: v for k, v in m.NAMES_A_SUCCESSOR.items() if k != "absorbed_duplicate"})
    with pytest.raises(AssertionError):
        m.check_registry_total({**m.NAMES_A_SUCCESSOR, "a_new_reason": True})


def test_the_vocabulary_refuses_a_string():
    """MUTANT 4 — `frozenset[str]` admitted anything (R4-1's last sentence). The
    enum refuses a value outside its three members."""
    m = _load()
    with pytest.raises(ValueError):
        m.SuccessorDisposition("cross_user")
    assert {d.value for d in m.SuccessorDisposition} == {"head", "superseded", "successor_unavailable"}
