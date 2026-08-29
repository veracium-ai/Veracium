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


# ---- S5: trusted ingress is a capability (E4, §4d) -------------------------
# The complete §4d grammar, every cell reachable and named. RAISES cells are
# driven through the REAL entry point and assert NOTHING WAS WRITTEN.

import json as _json

from veracium import ingest as _ingest_mod
from veracium.ingest import ingest_event
from veracium.schema import EvidenceContext


def _llm_for(triples):
    payload = _json.dumps({"triples": triples, "episode": "ep"})

    def llm(prompt, *, system=None, role="distill", json_schema=None):
        if role == "distill-retry":
            return _json.dumps({"triples": []})
        return payload
    return llm


_TRIPLE = [{"subject": "user", "relation": "works_as", "object": "engineer"}]


def _run_ingest(store, **kw):
    return ingest_event(store, _llm_for(_TRIPLE), U, event_text="t",
                        author=A.USER, date="2026-08-29",
                        relations=DEFAULT_RELATIONS, **kw)


def test_absent_context_floors_conservative():
    """S5: no context and no legacy derived_from is the FLOOR cell —
    derived(THIRD_PARTY) on every record the event produces. Absence is
    never the trusted cell."""
    store = SqliteStore(":memory:")
    _run_ingest(store)
    edges = store.edges(U, active_only=False)
    assert edges, "the floor cell must still write — it floors, not refuses"
    for e in edges:
        assert e.provenance.derived_from == A.THIRD_PARTY
        assert e.provenance.third_party_influenced
    (ep,) = store.episodes(U)
    assert ep.provenance.derived_from == A.THIRD_PARTY


def test_direct_context_preserves_first_party_capture():
    """§4d: `direct` is the host's POSITIVE attestation of first-party
    capture — the one way to the trusted cell that used to be the default."""
    store = SqliteStore(":memory:")
    _run_ingest(store, context=EvidenceContext.direct())
    for e in store.edges(U, active_only=False):
        assert e.provenance.derived_from is None
        assert not e.provenance.third_party_influenced


def test_legacy_derived_from_is_a_positive_declaration():
    """§4d: `derived_from=X` was already a positive declaration and stays
    honoured as derived(X) — the floor applies only to declaring NOTHING."""
    store = SqliteStore(":memory:")
    _run_ingest(store, derived_from=A.SYSTEM)
    for e in store.edges(U, active_only=False):
        assert e.provenance.derived_from == A.SYSTEM


def test_derived_grammar_is_total_and_pinned():
    """§4d adversarial matrix: the derived() domain is pinned to the enum
    CELL BY CELL — an EvidenceAuthor member added later with no cell here
    fails this equality rather than inheriting a default."""
    pinned = {A.USER: A.USER, A.SYSTEM: A.SYSTEM,
              A.ASSISTANT: A.ASSISTANT, A.THIRD_PARTY: A.THIRD_PARTY}
    assert set(pinned) == set(A), (
        "a new EvidenceAuthor member needs its §4d cell decided explicitly")
    for member, want in pinned.items():
        ctx = EvidenceContext.derived(member)
        assert _ingest_mod._resolve_context(ctx, None) is want


def test_absence_is_distinct_from_explicit_third_party(monkeypatch):
    """§4d adversarial matrix: the absence path and the explicit
    derived(THIRD_PARTY) path must be DISTINCT paths a refactor cannot
    collapse. Witness: move the floor constant and ONLY absence moves."""
    monkeypatch.setattr(_ingest_mod, "_ABSENT_CONTEXT_FLOOR", A.USER)
    assert _ingest_mod._resolve_context(None, None) is A.USER
    assert _ingest_mod._resolve_context(
        EvidenceContext.derived(A.THIRD_PARTY), None) is A.THIRD_PARTY
    # and the entry points default to ABSENCE, not to a minted context
    import inspect
    from veracium import Memory
    assert inspect.signature(ingest_event).parameters["context"].default is None
    assert inspect.signature(Memory.remember).parameters["context"].default is None


@pytest.mark.parametrize("mint", [
    lambda: EvidenceContext.derived(None),        # derived(None) ≠ absence
    lambda: EvidenceContext.derived("user"),      # bare string: no coercion
    lambda: EvidenceContext.derived("direct"),
    lambda: EvidenceContext.derived(3),
    lambda: EvidenceContext.derived(True),
    lambda: EvidenceContext.derived({}),
    lambda: EvidenceContext.derived([A.USER]),
    lambda: EvidenceContext("weird", None),       # closed kind domain
    lambda: EvidenceContext("direct", A.USER),    # direct derives from nothing
])
def test_malformed_context_raises_at_construction(mint):
    """§4d: the from_class domain is CLOSED and validated at construction —
    an unknown or malformed value RAISES; no coercion, no str()."""
    with pytest.raises((TypeError, ValueError)):
        mint()


class _ForgedContext(EvidenceContext):
    """A subclass that bypasses construction validation entirely."""

    def __init__(self):
        object.__setattr__(self, "kind", "derived")
        object.__setattr__(self, "derived_from", "user")


@pytest.mark.parametrize("kw", [
    {"context": "direct"},                        # bare string where a context goes
    {"context": EvidenceContext},                 # the class, not an instance
    {"context": _ForgedContext()},                # subclass laundering
    {"context": EvidenceContext.direct(),
     "derived_from": A.SYSTEM},                   # two declaration carriers
])
def test_invalid_context_raises_with_nothing_written(kw):
    """§4d: every RAISES cell fires at the REAL entry point BEFORE the LLM
    runs or anything is written — refusal is loud and has no write."""
    store = SqliteStore(":memory:")

    def llm_must_not_run(prompt, **_):
        raise AssertionError("the LLM ran before the context was validated")

    with pytest.raises((TypeError, ValueError)):
        ingest_event(store, llm_must_not_run, U, event_text="t",
                     author=A.USER, date="2026-08-29",
                     relations=DEFAULT_RELATIONS, **kw)
    assert store.edges(U, active_only=False) == []
    assert store.episodes(U) == []


def test_context_is_immutable_and_value_semantic():
    """§4d: a value object — no mutation after mint, equality by value."""
    c = EvidenceContext.direct()
    with pytest.raises(AttributeError):
        c.kind = "derived"
    with pytest.raises(AttributeError):
        c.derived_from = A.USER
    assert EvidenceContext.direct() == EvidenceContext.direct()
    assert (EvidenceContext.derived(A.USER)
            == EvidenceContext.derived(A.USER))
    assert EvidenceContext.direct() != EvidenceContext.derived(A.USER)
    assert len({EvidenceContext.direct(), EvidenceContext.direct()}) == 1
