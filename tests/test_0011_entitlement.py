"""specs/0011 §6 — the S-invariants of the subject-scoped entitlement
implementation (E1/E2 in this file; E3–E6 join in their commits).

0011 was ACCEPTED at external round 19; §6 is the ONE authoritative test
list and these are its named tests."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from veracium import authority, graph
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge,
                             EvidenceAuthor as A, Provenance)
from veracium.store.sqlite import SqliteStore

NOW = datetime(2026, 5, 1, tzinfo=timezone.utc)
U = "u"


def _edge(eid, subject, obj, author, derived=None, relation="works_as"):
    return Edge(id=eid, user_id=U, subject=subject, relation=relation,
                object=obj, valid_from=NOW, active=True,
                provenance=Provenance(author_of_evidence=author,
                                      derived_from=derived,
                                      evidence_ref=f"r-{eid}",
                                      observed_at=NOW))


# ---- S1: subject_class is TOTAL with OTHER as default ----------------------

@pytest.mark.parametrize("subject,want", [
    ("user", "SELF"), (" USER ", "SELF"), ("User", "SELF"),
    ("user's sister", "OTHER"), ("users", "OTHER"), ("", "OTHER"),
    ("   ", "OTHER"), (None, "OTHER"), (42, "OTHER"),
    ("u​ser", "OTHER"),            # zero-width smuggling stays OTHER
    ("user\n", "SELF"),                 # strip() is the 0024 predicate
    ("me", "OTHER"), ("I", "OTHER"),    # only the canonical slot is SELF
    (object(), "OTHER"),
])
def test_subject_class_is_total(subject, want):
    """S1: every subject string classifies; only the 0024 canonical cell
    is SELF, and OTHER is the DEFAULT — the conservative class — so an
    unknown entity ref refuses more, never less."""
    assert graph.subject_class(U, subject) == want


# ---- S2: a self-assertion never retires an OTHER-subject prior -------------

def _plan_for(store, incoming):
    plan, _reinf = graph._build_supersession_plan(
        store, incoming, DEFAULT_RELATIONS, op_id="op-t")
    return plan


def _seed(store, subject, obj, author, derived=None, source_id=None):
    e = _edge(f"p-{obj[:6]}", subject, obj, author, derived)
    if source_id is not None:
        e.provenance.source_id = source_id
    store.add_edge(e)
    return e


@pytest.mark.parametrize("source_id", [None, "feed-a"])
@pytest.mark.parametrize("derived", [None, A.USER])
def test_self_assertion_cannot_retire_other_subject(tmp_path, source_id,
                                                    derived):
    """S2: the E2 cell over BOTH source states (R2-1: sourced was the
    motivating case, not the rule) and both qualifying chains (R3-1:
    (USER, None) and (USER, USER) are the same authority). The prior
    stays active, the incoming is stored, and the refusal row is
    durable."""
    store = SqliteStore(f"{tmp_path}/s2.db")
    prior = _seed(store, "user's sister", "CFO at Acme", A.THIRD_PARTY,
                  source_id=source_id)
    incoming = _edge("i1", "user's sister", "unemployed", A.USER, derived)
    plan = _plan_for(store, incoming)
    retired = [pid for pid, *_ in plan.prior_invalidations]
    assert prior.id not in retired, (
        "a USER self-assertion retired an OTHER-subject prior")
    assert any(r.prior_edge_id == prior.id for r in plan.refusals), (
        "no refusal row for the blocked retirement")
    assert plan.insert_incoming, "the incoming must still be stored"
    store.close()


def test_self_assertion_still_retires_self_subject(tmp_path):
    """The conservation half: SELF-on-SELF entitlement is today's ladder
    — a user correcting their OWN fact is untouched by the subject axis."""
    store = SqliteStore(f"{tmp_path}/s2b.db")
    prior = _seed(store, "user", "CFO at Acme", A.THIRD_PARTY)
    incoming = _edge("i1", "user", "CTO at Globex", A.USER)
    plan = _plan_for(store, incoming)
    assert any(pid == prior.id for pid, *_ in plan.prior_invalidations), (
        "the SELF-subject retirement regressed")
    store.close()


def test_derived_caps_never_launder_through_the_subject_rule(tmp_path):
    """The laundering cells, §4b's generated table: SYSTEM/ASSISTANT
    evidence marked derived_from=USER keeps its own class — NOT a
    self-assertion — and the ladder decides (here: effective 2 vs the
    prior's 0, so it retires; the subject rule stays out of it)."""
    store = SqliteStore(f"{tmp_path}/s2c.db")
    prior = _seed(store, "user's sister", "CFO at Acme", A.THIRD_PARTY)
    incoming = _edge("i1", "user's sister", "CTO at Globex", A.SYSTEM,
                     A.USER)
    plan = _plan_for(store, incoming)
    assert any(pid == prior.id for pid, *_ in plan.prior_invalidations), (
        "a non-self-assertion was refused by the subject rule")
    store.close()


def test_user_derived_third_party_is_not_a_self_assertion(tmp_path):
    """USER derived_from=THIRD_PARTY has effective 0: not a
    self-assertion (the subject rule stays out) AND the ladder refuses
    it against a rung-0 prior only when authority says so — here 0 >= 0
    permits, which is the generated table's ALLOW cell."""
    store = SqliteStore(f"{tmp_path}/s2d.db")
    prior = _seed(store, "user's sister", "CFO at Acme", A.THIRD_PARTY)
    incoming = _edge("i1", "user's sister", "CTO at Globex", A.USER,
                     A.THIRD_PARTY)
    plan = _plan_for(store, incoming)
    assert any(pid == prior.id for pid, *_ in plan.prior_invalidations)
    store.close()


def test_rule_version_bumped_for_the_subject_axis():
    """§4b: a refusal-widening flips allowed pairs to refused — the
    change class RULE_VERSION exists to version."""
    assert authority.RULE_VERSION == "supersession-authority-v2"
