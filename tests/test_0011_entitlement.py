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


# ---- S4: correct() through the ladder, authorised (E5, §4e) ----------------
# The M7-correct regression plus the forge/replay/rebind/cross-principal
# cells, each driven through the REAL machinery.

import tempfile as _tempfile

from veracium import Memory, MemoryConfig, graph as _graph
from veracium.graph import CorrectionRefused, plan_correction
from veracium.schema import CorrectionAuthorisation, correction_digest
from veracium.store.base import CorrectionAuthorisationError


def _quiet_llm(prompt, **kw):
    raise AssertionError("correct() must not call the LLM")


def _mem_with(tmp, *edges, llm=None):
    db = f"{tmp}/t.db"
    mem = Memory(llm=llm or _quiet_llm, config=MemoryConfig(db_path=db))
    for e in edges:
        mem.store.add_edge(e)
    return mem


def _auth_for(store, prior_id, value, principal="user"):
    return CorrectionAuthorisation(
        origin=store.local_origin(), prior_edge_id=prior_id,
        replacement_digest=correction_digest(value),
        kind="corrected", principal=principal)


def test_correct_requires_bound_authorisation(tmp_path):
    """S4 happy path + the M7 regression: the correction commits atomically
    through the plan machinery ONLY — the direct invalidate_edge/add_edge
    path the defect used is proven unreachable by making it explode."""
    mem = _mem_with(tmp_path, _edge("p1", "user", "engineer", A.USER))
    mem.store.invalidate_edge = _explode  # the M7 path, armed
    mem.store.add_edge = _explode
    r = mem.correct(U, "p1", "staff engineer")
    prior = [e for e in mem.store.edges(U, active_only=False)
             if e.id == "p1"][0]
    assert not prior.active and prior.invalidation_reason == "corrected"
    repl = [e for e in mem.store.edges(U) if e.id == r["replacement"]][0]
    assert repl.object == "staff engineer" and repl.supersedes == "p1"
    assert mem.store.refusals(U) == []
    (ep,) = mem.store.episodes(U)     # the post-commit narration episode
    assert "corrected" in ep.summary
    mem.close()


def _explode(*a, **k):
    raise AssertionError(
        "correct() reached storage outside the plan machinery (M7)")


def test_forged_unbound_and_rebound_authorisations_abort(tmp_path):
    """S4: a 'corrected' retirement with NO authorisation, a rebound
    replacement value, a replay against a different prior, a foreign-origin
    mint, and a dangling authorisation all abort INSIDE the transaction —
    nothing written, the prior stays active."""
    mem = _mem_with(tmp_path,
                    _edge("p1", "user", "engineer", A.USER),
                    _edge("p2", "user", "welder", A.USER,
                          relation="hobby"))
    store = mem.store

    def fresh_plan():
        prior = [e for e in store.edges(U) if e.id == "p1"][0]
        repl = _edge("r-new", "user", "staff engineer", A.USER)
        return plan_correction(store, prior, repl, op_id=f"op-{repl.id}")[0]

    good = _auth_for(store, "p1", "staff engineer")
    bad_cells = [
        (None, "user"),                                          # forged: none
        (_auth_for(store, "p1", "principal engineer"), "user"),  # rebound value
        (_auth_for(store, "p2", "staff engineer"), "user"),      # other prior
        (CorrectionAuthorisation(
            origin="not-this-store", prior_edge_id="p1",
            replacement_digest=correction_digest("staff engineer"),
            kind="corrected", principal="user"), "user"),        # foreign mint
        (CorrectionAuthorisation(
            origin=store.local_origin(), prior_edge_id="p1",
            replacement_digest=correction_digest("staff engineer"),
            kind="absorbed_duplicate", principal="user"), "user"),  # wrong kind
        (good, "operator"),                       # cross-principal replay
    ]
    for auth, principal in bad_cells:
        plan = fresh_plan()
        with pytest.raises(CorrectionAuthorisationError):
            store.apply_supersession_plan(plan, authorisation=auth,
                                          acting_principal=principal)
        prior = [e for e in store.edges(U, active_only=False)
                 if e.id == "p1"][0]
        assert prior.active, "an aborted correction must write NOTHING"
        assert not any(e.id.startswith("r-new")
                       for e in store.edges(U, active_only=False))
    # the dangling cell: an authorisation with no corrected retirement to bind
    plan = fresh_plan()
    plan.prior_invalidations = []
    with pytest.raises(CorrectionAuthorisationError):
        store.apply_supersession_plan(plan, authorisation=good,
                                      acting_principal="user")
    # the one-auth-many-retirements cell: an authorisation binds exactly ONE
    plan = fresh_plan()
    plan.prior_invalidations = plan.prior_invalidations + [
        ("p2", plan.incoming_edge.valid_from, "corrected")]
    with pytest.raises(CorrectionAuthorisationError):
        store.apply_supersession_plan(plan, authorisation=good,
                                      acting_principal="user")
    assert [e.id for e in store.edges(U) if e.id == "p2"] == ["p2"]
    # and the legitimate binding still commits — the gates bite attacks only
    r = store.apply_supersession_plan(fresh_plan(), authorisation=good,
                                      acting_principal="user")
    assert r.invalidated == 1
    mem.close()


def test_correcting_an_other_subject_prior_refuses(tmp_path):
    """S4 × §4b: corrections are subject to the SAME entitlement rule as
    extractor supersession — a bare self-assertion cannot retire an
    OTHER-subject prior. The refusal row is durable, the raise is loud,
    and nothing else is written."""
    mem = _mem_with(tmp_path,
                    _edge("p9", "user's sister", "nurse", A.SYSTEM,
                          derived=A.THIRD_PARTY))
    with pytest.raises(CorrectionRefused) as exc:
        mem.correct(U, "p9", "surgeon")
    assert exc.value.prior_edge_id == "p9"
    prior = [e for e in mem.store.edges(U, active_only=False)
             if e.id == "p9"][0]
    assert prior.active, "the refused correction must not retire the prior"
    refusals = mem.store.refusals(U)
    assert [r.prior_edge_id for r in refusals] == ["p9"]
    assert all(e.id == "p9" for e in mem.store.edges(U, active_only=False)), (
        "the refused replacement must not be inserted")
    mem.close()


def test_inactive_prior_still_refused_loudly(tmp_path):
    """correct() on an already-retired edge keeps its named ValueError —
    the escape path gets the same loud treatment after the rewrite."""
    from datetime import datetime as _dt, timezone as _tz
    mem = _mem_with(tmp_path, _edge("p1", "user", "engineer", A.USER))
    mem.store.invalidate_edge("p1", _dt(2026, 5, 2, tzinfo=_tz.utc),
                              "superseded")
    with pytest.raises(ValueError, match="not active"):
        mem.correct(U, "p1", "x")
    mem.close()


def test_correction_plan_refuses_a_prior_the_cas_cannot_pin(tmp_path):
    """The diff-scan race: a prior retired between the caller's read and
    planning must refuse AT PLANNING — otherwise the plan would commit a
    double-retirement (the CAS token, computed after the retirement, would
    not protect it) and overwrite the recorded reason."""
    from datetime import datetime as _dt, timezone as _tz
    mem = _mem_with(tmp_path, _edge("p1", "user", "engineer", A.USER))
    store = mem.store
    prior = [e for e in store.edges(U) if e.id == "p1"][0]
    store.invalidate_edge("p1", _dt(2026, 5, 2, tzinfo=_tz.utc), "superseded")
    repl = _edge("r-x", "user", "staff engineer", A.USER)
    with pytest.raises(ValueError, match="cannot retire"):
        plan_correction(store, prior, repl, op_id="op-race")
    stale = [e for e in store.edges(U, active_only=False) if e.id == "p1"][0]
    assert stale.invalidation_reason == "superseded", (
        "the recorded reason must survive the refused race")
    mem.close()


# ---- S6: the history partition is total and exclusive (E6, §4f) ------------

from veracium.graph import HISTORY_LABELS, history_label
from veracium.schema import Disclosure


def test_history_partition_is_total():
    """S6: exactly one of the five labels for EVERY cell of the
    (active × disclosure × ungrounded × contested) cross-product, checked
    against an independently-written precedence oracle — including the two
    cells R1-5 executed against v4 (quarantined-grounded-uncontested and
    mentionable-grounded-contested)."""
    def oracle(active, disclosure, ungrounded, contested):
        # the §4f table, restated independently: first match wins
        if not active:
            return "RETIRED_HISTORY"
        if disclosure == Disclosure.QUARANTINED:
            return "QUARANTINED_CLAIM"
        if contested:
            return "CONTESTED_CURRENT"
        if ungrounded or disclosure == Disclosure.USE_ONLY:
            return "UNVERIFIED_CURRENT"
        return "GROUNDED_CURRENT"

    seen = set()
    n = 0
    for active in (True, False):
        for disclosure in Disclosure:
            for ungrounded in (True, False):
                for contested in (True, False):
                    e = _edge(f"x{n}", "user", f"v{n}", A.USER)
                    if not active:      # active is DERIVED from invalidated_at
                        e.invalidated_at = NOW
                        e.invalidation_reason = "superseded"
                    e.provenance.disclosure = disclosure
                    e.ungrounded = ungrounded
                    got = history_label(e, contested=contested)
                    assert got in HISTORY_LABELS
                    assert got == oracle(active, disclosure, ungrounded,
                                         contested), (
                        f"cell (active={active}, {disclosure}, "
                        f"ungrounded={ungrounded}, contested={contested})")
                    seen.add(got)
                    n += 1
    assert seen == set(HISTORY_LABELS), (
        "every label must be REACHABLE from the cross-product")
    # R1-5's two executed cells, by name
    q = _edge("q", "user", "v", A.USER)
    q.provenance.disclosure = Disclosure.QUARANTINED
    assert history_label(q, contested=False) == "QUARANTINED_CLAIM"
    m = _edge("m", "user", "v", A.USER)
    assert history_label(m, contested=True) == "CONTESTED_CURRENT"


def test_no_disclosure_interaction():
    """S7: the partition READS disclosure to place a label and never writes
    it — the 0023 N2 single-writer sweep EXTENDED to the E6 surfaces: the
    labelling leaves the edge byte-identical, and neither graph.py nor
    introspect.py joins the N2 writer set."""
    import re
    from pathlib import Path
    e = _edge("s7", "user", "v", A.USER)
    before = e.model_dump()
    for contested in (True, False):
        history_label(e, contested=contested)
    assert e.model_dump() == before, "labelling must not mutate the edge"
    src = Path(graph.__file__).resolve().parent
    for fname in ("graph.py", "introspect.py"):
        text = (src / fname).read_text()
        assert not re.search(
            r"[\"']?disclosure[\"']?\s*(?:(?<![=!])=(?!=)|:)\s*"
            r"[\(\"']*(Disclosure\.|_disclosure_for)", text), (
            f"{fname} must not join the N2 disclosure-writer set (S7)")


# ---- S3: CONTESTED is derived and every reader handles the cell (E3) -------

def _stub_llm_quiet(prompt, **kw):
    if "distill" in str(kw.get("role", "")):
        return '{"triples": []}'
    return "ok"


def _live_contention(tmp, obj_a="engineer", obj_b="teacher"):
    """A REAL live refusal contention via the shipped machinery: a USER
    self-assertion meets an OTHER-subject SYSTEM prior on a functional
    relation — the §4b cell refuses the retirement, both edges stay active,
    the refusal row is durable."""
    mem = _mem_with(tmp, llm=_stub_llm_quiet)
    mem.store.add_edge(_edge("pri", "user's sister", obj_a, A.SYSTEM,
                             derived=A.THIRD_PARTY))
    incoming = _edge("inc", "user's sister", obj_b, A.USER)
    from veracium.graph import apply_supersession
    apply_supersession(mem.store, incoming, DEFAULT_RELATIONS)
    assert [r.prior_edge_id for r in mem.store.refusals(U)] == ["pri"]
    return mem


def test_contested_is_derived_and_total_over_readers(tmp_path):
    """S3: no stored carrier exists — the store schema has no contested
    column and no src writer assigns one to an Edge — and every reader
    handles the cell: recall asserts the CONTENTION (never one side as a
    plain current fact), maintain suppresses resolution but NOT 0012 expiry,
    an exported/imported pair arrives uncontested, and a directly-inserted
    pair is not contested (the reviewer's executed cell)."""
    import re
    from pathlib import Path

    # (0) no persisted carrier: schema DDL and Edge never carry `contested`
    import veracium.store.sqlite as _sq, veracium.schema as _sc
    assert "contested" not in Path(_sq.__file__).read_text().lower()
    assert not re.search(r"^\s*contested\s*[:=]", Path(_sc.__file__).read_text(),
                         re.M), "Edge must not grow a stored contested field"

    # (1) recall: the contention is asserted, never one side
    mem = _live_contention(tmp_path)
    rec = mem.recall(U, "sister")
    assert rec.contested, "the live refusal contention must reach the carrier"
    assert "engineer" in rec.context and "teacher" in rec.context, (
        "the CONTENTION renders — both values visible as contested")
    plain = [ln for ln in rec.context.splitlines()
             if "engineer" in ln and "teacher" not in ln
             and "contest" not in ln.lower() and "disputed" not in ln.lower()]
    assert not plain, f"one side rendered as a plain current fact: {plain!r}"

    # (2) maintain: no resolution — both stay active; 0012 expiry NOT
    # suspended (a lapsed-lifetime contested member still expires)
    mem.maintain(U, consolidate=False)
    active_ids = {e.id for e in mem.store.edges(U)}
    assert {"pri", "inc"} <= active_ids, "maintain must not resolve the pair"
    from veracium import lifecycle as _lc
    from datetime import datetime as _dt, timezone as _tz
    old = _edge("exp", "user's sister", "berlin", A.SYSTEM,
                derived=A.THIRD_PARTY, relation="located_at")
    old.volatility = "transient"
    old.provenance.observed_at = _dt(2026, 1, 1, tzinfo=_tz.utc)
    mem.store.add_edge(old)
    challenger = _edge("exp2", "user's sister", "lisbon", A.USER,
                       relation="located_at")
    from veracium.graph import apply_supersession as _aps
    _aps(mem.store, challenger, DEFAULT_RELATIONS)
    assert len(mem.store.refusals(U)) == 2      # a second live contention
    _lc.expire(mem.store, U, mem.config, now=_dt(2026, 8, 29, tzinfo=_tz.utc))
    exp = [e for e in mem.store.edges(U, active_only=False)
           if e.id == "exp"][0]
    assert not exp.active and exp.invalidation_reason == "lapsed", (
        "contention must NOT suspend 0012 per-edge expiry (§4c/§7a)")

    # (3) portability: a refusal record is store-local — the imported pair
    # is NOT contested on arrival
    out = tmp_path / "exp.jsonl"
    mem.export_memory(U, out)
    mem2 = Memory(llm=_stub_llm_quiet,
                  config=MemoryConfig(db_path=f"{tmp_path}/t2.db"))
    mem2.import_memory(out, restore=True)
    assert mem2.store.refusals(U) == []
    assert mem2.recall(U, "sister").contested == []
    mem2.close()

    # (4) direct insertion: two active same-class distinct values, no
    # refusal — NOT contested (the reviewer's executed cell)
    mem3 = Memory(llm=_stub_llm_quiet,
                  config=MemoryConfig(db_path=f"{tmp_path}/t3.db"))
    mem3.store.add_edge(_edge("d1", "user's sister", "engineer", A.SYSTEM,
                              derived=A.THIRD_PARTY))
    mem3.store.add_edge(_edge("d2", "user's sister", "teacher", A.SYSTEM,
                              derived=A.THIRD_PARTY))
    assert mem3.recall(U, "sister").contested == []
    mem3.close()
    mem.close()
