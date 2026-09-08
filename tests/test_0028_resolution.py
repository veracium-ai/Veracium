"""specs/0028 §6 — the invariants marked OWED at acceptance, delivered with the
implementation (2026-09-08). One node per row, named for the row; every
check is deterministic over constructed store state (§6a). The successor
accessor is run against the FROZEN observation table of the accepted model
(`specs/evidence/0028/check_successor_lookup.py`, EXPECTED — pinned by
research at 1f1cf53: file sha16 aa3c5c33af0a1ad9, EXPECTED block sha16
7c49dfe9a9504ec4 by ast.unparse of the parsed node), so the oracle preceded
the code.
"""
from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
import pathlib
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from veracium import FutureAsOfRefused, Memory, MemoryConfig
from veracium.asof import (FENCED_SELF, GROUNDED_OUTCOMES, HOP_BOUND, INDETERMINATE,
                           NOT_RETURNABLE, POINTER_TO, RESOLUTION, RETURN_SELF,
                           RETURN_SELF_FLAGGED, resolve_as_of)
from veracium.asof import recall as recall_mod
from veracium.asof import resolve as resolve_mod
from veracium.asof.classify import FENCED_AS_OF, GROUNDED_AS_OF, NOT_VALID_AT_T
from veracium.asof.resolve import (CAUSE_CYCLE, CAUSE_HOP_BOUND, TAG_CURRENT,
                                   TAG_UNKNOWN_REASON_EXCLUDED, _resolve_edge)
from veracium.schema import (DISPOSITIONED_REASONS, NAMES_A_SUCCESSOR, Disclosure,
                             Edge, EvidenceAuthor, Provenance, SuccessorDisposition,
                             SuccessorLookup)
from veracium.scope import Identity, ScopeError, validate_policy
from veracium.store.sqlite import SqliteStore

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL = ROOT / "specs" / "evidence" / "0028" / "check_successor_lookup.py"
U = "u"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
D = timedelta(days=1)
NOW = T0 + 150 * D
US = timedelta(microseconds=1)


class RecordingClock:
    """The store's INJECTED clock, recording every read (V-ONE-CLOCK)."""

    def __init__(self, *values):
        self.values = list(values) or [NOW]
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.values[min(self.calls - 1, len(self.values) - 1)]


def _edge(obj="Porto", *, relation="located_at", source="mb-a", valid_from=T0,
          supersedes=None, subject="user", disclosure=Disclosure.MENTIONABLE):
    return Edge(id=f"e-{uuid.uuid4().hex[:10]}", user_id=U, subject=subject,
                relation=relation, object=obj, valid_from=valid_from,
                supersedes=supersedes,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}",
                                      source_id=source, disclosure=disclosure,
                                      observed_at=valid_from))


def _store(tmp_path, clock=None, name="asof.db"):
    return SqliteStore(str(tmp_path / name), clock=clock or RecordingClock())


def _mem(tmp_path, store):
    return Memory(llm=lambda *a, **k: "ok", store=store,
                  config=MemoryConfig(db_path=str(tmp_path / "unused.db"),
                                      wiki_recompile_after_writes=0))


def _model():
    spec = importlib.util.spec_from_file_location("check_successor_lookup", MODEL)
    mod = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _correct(store, prior, replacement):
    return _model().correct(store, prior, replacement)


def _tamper(store, eid, **changes):
    """DB-level row edit — the stated fixture origin for states no shipped
    writer produces (§4b-iii's corrupted-state cells)."""
    row = json.loads(store._conn.execute(
        "SELECT json FROM edges WHERE id=?", (eid,)).fetchone()[0])
    row.update({k: (v.isoformat() if isinstance(v, datetime) else v)
                for k, v in changes.items()})
    active = 0 if row.get("invalidated_at") else 1
    store._conn.execute("UPDATE edges SET json=?, active=? WHERE id=?",
                        (json.dumps(row), active, eid))
    store._conn.commit()


def _facts(store, T, **kw):
    return {f.edge.id: f.resolution for f in resolve_as_of(store, U, T, **kw).facts}


def _resolution_of(store, eid, T, now=NOW):
    """The per-edge outcome INCLUDING NOT_RETURNABLE, which the answer omits."""
    with store.read_window(U):
        rows = store.edges(U, active_only=False)
        e = next(x for x in rows if x.id == eid)
        return _resolve_edge(store, U, e, rows, T, now, None, None, None, lambda _e: True)


# ------------------------------------------------------------------ the oracle
def test_the_accessor_matches_the_frozen_model_on_every_state(tmp_path):
    """`edges_superseding` run against EXPECTED — the 13 states the accepted
    model names, both principals, disposition AND visible count — and the
    two halves of V-NO-EXISTENCE-SIGNAL on the SHIPPED accessor: the
    excluded principal's hidden and nonexistent results equal as WHOLE
    OBJECTS, and the holder is never told HEAD about a retired-hidden state."""
    m = _model()
    store, ids = m.build(tmp_path / "model.db")
    A, B = m.principals(store)
    MU = m.U                                   # the model's user, not this file's
    assert len(m.EXPECTED) == 13
    for name, ((da, na), (db, nb)) in m.EXPECTED.items():
        la = store.edges_superseding(MU, ids[name], principal=A[0], policy=A[1])
        lb = store.edges_superseding(MU, ids[name], principal=B[0], policy=B[1])
        assert isinstance(la, SuccessorLookup) and isinstance(lb, SuccessorLookup)
        assert (la.disposition.value, len(la.successors)) == (da, na), name
        assert (lb.disposition.value, len(lb.successors)) == (db, nb), name
    nonexistent = store.edges_superseding(MU, ids["nonexistent"], principal=B[0], policy=B[1])
    for name in m.HIDDEN_RETIRED + ("hidden_queried",):
        lb = store.edges_superseding(MU, ids[name], principal=B[0], policy=B[1])
        la = store.edges_superseding(MU, ids[name], principal=A[0], policy=A[1])
        if name == "hidden_queried":
            assert lb == nonexistent          # the hidden QUERIED id reads as nonexistent
        else:
            assert lb == store.edges_superseding(MU, ids["forward_missing"],
                                                 principal=B[0], policy=B[1])
        assert la.disposition is not SuccessorDisposition.HEAD
    # ordering: valid_from asc then id asc, never store order
    multi = store.edges_superseding(MU, ids["multiple"], principal=A[0], policy=A[1])
    keys = [(e.valid_from, e.id) for e in multi.successors]
    assert keys == sorted(keys) and len(keys) == 2
    store.close()


def test_the_lookup_is_immutable_and_two_fielded():
    lk = SuccessorLookup(SuccessorDisposition.HEAD, ())
    with pytest.raises(AttributeError):
        lk.disposition = SuccessorDisposition.SUPERSEDED
    with pytest.raises(AttributeError):
        lk.extra = 1
    assert SuccessorLookup.__slots__ == ("disposition", "successors")
    with pytest.raises(TypeError):
        SuccessorLookup("head", ())


def test_the_registry_is_the_shipped_one(tmp_path):
    """V-SUCCESSOR-REGISTRY-TOTAL on the SHIPPED registry (the model carries
    its own copy): keys equal DISPOSITIONED_REASONS, values booleans, and the
    derived set is exactly the three the spec's table marks."""
    assert set(NAMES_A_SUCCESSOR) == set(DISPOSITIONED_REASONS)
    assert all(type(v) is bool for v in NAMES_A_SUCCESSOR.values())
    assert {r for r, v in NAMES_A_SUCCESSOR.items() if v} == {
        "corrected", "superseded", "absorbed_duplicate"}


# ------------------------------------------------------------------- V-COMPAT
def test_v_compat_as_of_none_takes_the_pre_existing_path_unchanged(tmp_path, monkeypatch):
    """Structural (§6a): the parameter is keyword-only, default None, and the
    resolution is NEVER invoked when it is None — the existing recall suite
    is the differential."""
    p = inspect.signature(Memory.recall).parameters["as_of"]
    assert p.kind is inspect.Parameter.KEYWORD_ONLY and p.default is None
    store = _store(tmp_path)
    store.add_edge(_edge())
    mem = _mem(tmp_path, store)

    def boom(*a, **k):
        raise AssertionError("the as-of resolution ran with as_of=None")
    monkeypatch.setattr(resolve_mod, "resolve_as_of", boom)
    monkeypatch.setattr(recall_mod, "resolve_as_of", boom)
    monkeypatch.setattr(recall_mod, "recall_at", boom)
    r = mem.recall(U, "porto")
    assert "Porto" in r.context and r.as_of is None
    # the proactive path refuses the axis rather than ignoring it
    with pytest.raises(ValueError):
        mem.recall(U, None, as_of=NOW)


# --------------------------------------------------------- V-TOTAL / V-CROSS
def test_v_total_the_resolution_table_equals_the_registry():
    """`set(RESOLUTION) == set(DISPOSITIONED_REASONS)` — and the mutant: an
    eighth reason fails the resolution module's import gate (in a
    SUBPROCESS: reloading the module in-process would re-mint its classes
    and break exception identity for every later test)."""
    import subprocess
    import sys
    assert set(RESOLUTION) == set(DISPOSITIONED_REASONS)
    code = ("import importlib, veracium.schema as s, veracium.asof.resolve as r\n"
            "s.DISPOSITIONED_REASONS['eighth'] = 'drop'\n"
            "try:\n    importlib.reload(r)\nexcept ImportError as e:\n"
            "    print('REFUSED', 'V-TOTAL' in str(e)); raise SystemExit(0)\n"
            "print('ADMITTED'); raise SystemExit(1)\n")
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert p.returncode == 0 and "REFUSED True" in p.stdout, p.stdout + p.stderr


# -------------------------------------------------------- V-MUTANT / V-NONE
def test_v_mutant_a_reason_outside_the_registry_is_not_returnable(tmp_path):
    store = _store(tmp_path)
    e = _edge(); store.add_edge(e)
    _tamper(store, e.id, invalidated_at=T0 + 10 * D, invalidation_reason="mystery")
    r = _resolution_of(store, e.id, T0 + 5 * D)
    assert r.outcome == NOT_RETURNABLE and r.tag == TAG_UNKNOWN_REASON_EXCLUDED
    assert e.id not in _facts(store, T0 + 5 * D)
    assert mem_facts_ids(tmp_path, store, T0 + 5 * D) == []


def test_v_none_a_none_reason_on_an_invalidated_edge_is_not_returnable(tmp_path):
    store = _store(tmp_path)
    e = _edge(); store.add_edge(e)
    _tamper(store, e.id, invalidated_at=T0 + 10 * D, invalidation_reason=None)
    r = _resolution_of(store, e.id, T0 + 5 * D)
    assert r.outcome == NOT_RETURNABLE and r.tag == TAG_UNKNOWN_REASON_EXCLUDED
    assert e.id not in _facts(store, T0 + 5 * D)


def mem_facts_ids(tmp_path, store, T):
    return [f.edge.id for f in _mem(tmp_path, store).facts_valid_at(U, "user", "located_at", T)]


# ----------------------------------------------- V-NO-UPGRADE / V-NEVER-BYPASS
@pytest.mark.parametrize("reason", sorted(DISPOSITIONED_REASONS))
def test_v_no_upgrade_no_row_outranks_the_0030_verdict(tmp_path, reason):
    """Per row: the outcome is a grounded one IFF 0030 said GROUNDED_AS_OF,
    and the carried status IS 0030's status for the same inputs."""
    from veracium.asof import Envelope, classify_as_of
    from veracium.store.base import RawEdgeState
    store = _store(tmp_path)
    e = _edge(); store.add_edge(e)
    store.invalidate_edge(e.id, T0 + 10 * D, reason)
    T = T0 + 5 * D
    r = _resolution_of(store, e.id, T)
    cs = store.current_state(U, e.id)
    verdict = classify_as_of(Envelope(U, e.id),
                             RawEdgeState(e.id, U, cs.current_raw, 0, 0, "live", ""),
                             cs, T, NOW)
    assert r.status == verdict.status
    # never STRONGER than the verdict (weaker is permitted: the absorbed row
    # is INDETERMINATE under a GROUNDED verdict by §4b-iii's legacy cell)
    if r.outcome in GROUNDED_OUTCOMES:
        assert verdict.status == GROUNDED_AS_OF
    expected = {"superseded": RETURN_SELF, "lapsed": RETURN_SELF_FLAGGED,
                "decayed": RETURN_SELF_FLAGGED, "absorbed_duplicate": INDETERMINATE,
                "corrected": FENCED_SELF, "disputed": FENCED_SELF,
                "revoked_source": NOT_RETURNABLE}
    assert r.outcome == expected[reason], reason
    assert (verdict.status == GROUNDED_AS_OF) == (reason in
                                                  ("superseded", "lapsed", "decayed",
                                                   "absorbed_duplicate"))


@pytest.mark.parametrize("reason", ["corrected", "disputed", "revoked_source"])
def test_v_never_bypass_fenced_reasons_yield_no_assertable_value_at_any_t(tmp_path, reason):
    """Sampled inside the interval and at BOTH boundaries (0030's V-NEVER met
    on this axis): never a grounded outcome; revoked_source never returns."""
    store = _store(tmp_path)
    e = _edge(); store.add_edge(e)
    vf, ia = T0, T0 + 10 * D
    store.invalidate_edge(e.id, ia, reason)
    for T in (vf, vf + US, vf + 5 * D, ia - US, ia, ia + D):
        facts = _facts(store, T)
        r = facts.get(e.id)
        if reason == "revoked_source":
            assert r is None
        elif vf <= T < ia:
            assert r is not None and r.outcome == FENCED_SELF and r.status == FENCED_AS_OF
        else:
            assert r is None


# --------------------------------------------------------- V-HEAD / V-BOUND
def test_v_head_the_pointer_resolves_to_the_head_classified_at_now(tmp_path):
    """A chain terminating on a DISPUTED head: the pointer names the head
    with its 0030 status at T=now — fenced, never truth; an intact head
    reads GROUNDED_AS_OF."""
    store = _store(tmp_path)
    a = _edge("Porto"); store.add_edge(a)
    b = _correct(store, a, _edge("Braga", supersedes=a.id, valid_from=T0 + D))
    r = _facts(store, T0 + 12 * timedelta(hours=1))[a.id]
    assert r.outcome == FENCED_SELF and r.pointer.outcome == POINTER_TO
    assert (r.pointer.head_id, r.pointer.head_status, r.pointer.hops) == (b.id, GROUNDED_AS_OF, 1)
    store.invalidate_edge(b.id, T0 + 20 * D, "disputed")
    r = _facts(store, T0 + 12 * timedelta(hours=1))[a.id]
    # a disputed head is RETIRED, so at T=now 0030 says it is not held at
    # all (NOT_VALID_AT_T) — a pointer to a record that is not truth now
    assert r.pointer.head_id == b.id and r.pointer.head_status == NOT_VALID_AT_T
    assert r.pointer.head_status != GROUNDED_AS_OF and r.outcome not in GROUNDED_OUTCOMES
    # a head fenced while CURRENT: a source-restricted or quarantined head
    s2 = _store(tmp_path, name="fenced-head.db")
    a2 = _edge("Porto"); s2.add_edge(a2)
    b2 = _correct(s2, a2, _edge("Braga", supersedes=a2.id, valid_from=T0 + D))
    _tamper(s2, b2.id, provenance={**json.loads(b2.model_dump_json())["provenance"],
                                   "disclosure": Disclosure.QUARANTINED.value})
    r2 = _facts(s2, T0 + timedelta(hours=1))[a2.id]
    assert r2.pointer.head_id == b2.id and r2.pointer.head_status == FENCED_AS_OF


def test_v_bound_a_chain_longer_than_n_and_a_cycle_are_indeterminate(tmp_path):
    store = _store(tmp_path)
    chain = [_edge("v0")]; store.add_edge(chain[0])
    for i in range(1, HOP_BOUND + 2):                      # v0 → v1 → … → v(N+1)
        chain.append(_correct(store, chain[-1],
                              _edge(f"v{i}", supersedes=chain[-1].id, valid_from=T0 + i * D)))
    T = T0 + timedelta(hours=1)
    r = _facts(store, T)[chain[0].id]
    assert r.pointer.outcome == INDETERMINATE and r.pointer.cause == CAUSE_HOP_BOUND
    # exactly N hops is a head
    r1 = _facts(store, T0 + D + timedelta(hours=1))[chain[1].id]
    assert r1.pointer.outcome == POINTER_TO and r1.pointer.hops == HOP_BOUND
    # a cycle: the first edge's own `supersedes` names its corrector (raw edit)
    s2 = _store(tmp_path, name="cycle.db")
    a = _edge("a"); s2.add_edge(a)
    b = _correct(s2, a, _edge("b", supersedes=a.id, valid_from=T0 + D))
    _tamper(s2, a.id, supersedes=b.id)
    r = _facts(s2, T)[a.id]
    assert r.pointer.outcome == INDETERMINATE and r.pointer.cause == CAUSE_CYCLE


def test_v_never_head_successor_unavailable_is_indeterminate_without_a_cause(tmp_path):
    """The forward-missing state: the corrected row asserts a successor and
    none is present — INDETERMINATE, no cause, never a head."""
    store = _store(tmp_path)
    a = _edge("a"); store.add_edge(a)
    b = _correct(store, a, _edge("b", supersedes=a.id, valid_from=T0 + D))
    store._conn.execute("DELETE FROM edges WHERE id=?", (b.id,)); store._conn.commit()
    r = _facts(store, T0 + timedelta(hours=1))[a.id]
    assert r.pointer.outcome == INDETERMINATE and r.pointer.cause is None
    assert r.pointer.head_id is None


# ------------------------------------------------------ V-EMPTY / V-BOUNDARY
def test_v_empty_an_empty_interval_is_returned_at_no_t(tmp_path):
    store = _store(tmp_path)
    e = _edge(valid_from=T0 + 5 * D); store.add_edge(e)
    _tamper(store, e.id, invalidated_at=T0 + 5 * D, invalidation_reason="superseded")
    for T in (T0 + 5 * D, T0 + 5 * D + US, T0 + 4 * D, T0 + 6 * D):
        assert e.id not in _facts(store, T)
    _tamper(store, e.id, invalidated_at=T0 + 3 * D, invalidation_reason="superseded")
    for T in (T0 + 3 * D, T0 + 4 * D, T0 + 5 * D):
        assert e.id not in _facts(store, T)


def test_v_boundary_at_the_adjacency_exactly_one_edge_returns_the_corrector(tmp_path):
    """T = c: the corrector only (the prior's interval is [v, c), open at c);
    T = c - 1µs: the prior (fenced, pointing forward). The null upper bound
    is INSIDE at any T ≥ valid_from."""
    store = _store(tmp_path)
    a = _edge("Porto"); store.add_edge(a)
    c = T0 + 7 * D
    b = _correct(store, a, _edge("Braga", supersedes=a.id, valid_from=c))
    at_c = _facts(store, c)
    assert set(at_c) == {b.id} and at_c[b.id].outcome == RETURN_SELF and at_c[b.id].tag == TAG_CURRENT
    before = _facts(store, c - US)
    assert set(before) == {a.id} and before[a.id].outcome == FENCED_SELF
    assert before[a.id].pointer.head_id == b.id
    assert set(_facts(store, T0)) == {a.id}                 # T = valid_from: INSIDE
    assert set(_facts(store, NOW)) == {b.id}                # open upper bound, T = now
    assert _facts(store, T0 - US) == {}                     # before any record: empty, no error


# ------------------------------------------------- V-NO-FUTURE / V-ONE-CLOCK
def test_v_no_future_a_sleeper_is_returned_at_no_permitted_t_and_the_future_refuses(tmp_path):
    clock = RecordingClock(NOW)
    store = _store(tmp_path, clock)
    s = _edge("sleeper", valid_from=NOW + timedelta(seconds=1)); store.add_edge(s)
    held = _edge("held"); store.add_edge(held)
    with pytest.raises(FutureAsOfRefused) as ei:
        resolve_as_of(store, U, s.valid_from)                # T = its own valid_from
    assert ei.value.T == s.valid_from and ei.value.now == NOW
    assert s.id not in _facts(store, NOW)                    # T = the clock snapshot
    assert held.id in _facts(store, NOW)


def test_v_one_clock_a_straddling_clock_does_not_admit_the_sleeper(tmp_path):
    """The seam is microseconds wide: successive clock reads straddle the
    sleeper's `valid_from`. A ONE-READ resolution at T = the first reading
    never sees it; the recording clock counts EXACTLY ONE invocation per
    resolution, on both surfaces."""
    now1 = NOW
    sleeper_vf = now1 + US
    now2 = now1 + 2 * US
    clock = RecordingClock(now1, now2, now2, now2)
    store = _store(tmp_path, clock)
    s = _edge("sleeper", valid_from=sleeper_vf); store.add_edge(s)
    held = _edge("held"); store.add_edge(held)
    clock.calls, clock.values = 0, [now1, now2, now2, now2, now2, now2]
    answer = resolve_as_of(store, U, now1)
    assert clock.calls == 1
    assert {f.edge.id for f in answer.facts} == {held.id} and answer.now == now1
    mem = _mem(tmp_path, store)
    clock.calls = 0
    facts = mem.facts_valid_at(U, "user", "located_at", now1)
    assert clock.calls == 1 and {f.edge.id for f in facts} == {held.id}
    clock.calls = 0
    r = mem.recall(U, "held sleeper", as_of=now1)
    assert clock.calls == 1
    assert {e.id for e in r.edges} == {held.id} and r.as_of.now == now1


def test_v_one_clock_the_as_of_branch_never_consults_the_wall_clock_predicates(tmp_path, monkeypatch):
    """Mutant 2, behavioural and direct: `Edge.valid_now`/`Edge.assertable`
    are replaced by raising properties for the duration of an as-of recall
    and a direct lookup — both must complete. (The evidence script's
    recording clock proves the same across the whole exercised surface.)"""
    from veracium import schema
    store = _store(tmp_path)
    a = _edge("Porto"); store.add_edge(a)
    b = _correct(store, a, _edge("Braga", supersedes=a.id, valid_from=T0 + D))
    claim = _edge("claim", source="other", disclosure=Disclosure.QUARANTINED)
    store.add_edge(claim)
    mem = _mem(tmp_path, store)

    def trip(self):
        raise AssertionError("wall-clock predicate consulted on the as-of branch")
    monkeypatch.setattr(schema.Edge, "valid_now", property(trip))
    monkeypatch.setattr(schema.Edge, "assertable", property(trip))
    facts = {f.edge.id: f.resolution for f in
             mem.facts_valid_at(U, "user", "located_at", T0 + timedelta(hours=1))}
    assert set(facts) == {a.id, claim.id}
    assert facts[a.id].outcome == FENCED_SELF and facts[claim.id].outcome == FENCED_SELF
    r = mem.recall(U, "porto braga", as_of=T0 + 2 * D)
    assert {e.id for e in r.edges} == {b.id, claim.id}     # the claim is held, fenced
    assert r.as_of.resolution_of(b.id).outcome == RETURN_SELF
    assert r.as_of.resolution_of(claim.id).outcome == FENCED_SELF
    assert "Braga" in r.grounded and "claim" not in r.grounded and "claim" in r.unverified
    assert r.episodes == [] and r.contested == []
    assert "as of 2026-01-03: current; held 2026-01-02→open" in r.context


# -------------------------------------------------------------- V-NORM-FIRST
def test_v_norm_first_a_naive_future_t_is_a_value_error_not_a_refusal(tmp_path):
    store = _store(tmp_path)
    store.add_edge(_edge())
    with pytest.raises(ValueError) as ei:
        resolve_as_of(store, U, (NOW + D).replace(tzinfo=None))
    assert not isinstance(ei.value, FutureAsOfRefused)
    with pytest.raises(ValueError) as ei:
        resolve_as_of(store, U, "2026-01-01T00:00:00+00:00")
    assert not isinstance(ei.value, FutureAsOfRefused)
    assert resolve_as_of(store, U, NOW).T == NOW               # T == now is PERMITTED
    with pytest.raises(FutureAsOfRefused):
        resolve_as_of(store, U, NOW + US)
    with pytest.raises(TypeError):
        _mem(tmp_path, store).facts_valid_at(U, "user", "located_at", None)


# ------------------------------------------------------ V-SCOPE-DIFFERENTIAL
def test_two_principals_one_store_one_record(tmp_path):
    """Research's design (proposals, round 4, R3-3): one store, one record
    with a known half-open interval, principal A in its scope and B not.
    (1) A sees it exactly inside the interval; (2) B at no T; (3)
    ORTHOGONALITY — B's answer is empty at EVERY T, inside, at both
    boundaries and outside: no choice of T grants B a record its scope
    excludes. Mutant: a non-Identity principal is refused by the view."""
    store = _store(tmp_path)
    vf, ia = T0, T0 + 10 * D
    e = _edge("Porto", source="other-mailbox", valid_from=vf); store.add_edge(e)
    store.invalidate_edge(e.id, ia, "superseded")
    mem = _mem(tmp_path, store)
    A = (Identity(origin=None, source_id="mb-a"),
         validate_policy({}, cross_scope_visible=True, local_origin=store.local_origin()))
    B = (Identity(origin=None, source_id="mb-a"),
         validate_policy({}, cross_scope_visible=False, local_origin=store.local_origin()))
    samples = (vf - D, vf, vf + US, vf + 5 * D, ia - US, ia, ia + D)
    for T in samples:
        fa = mem.facts_valid_at(U, "user", "located_at", T, principal=A[0], policy=A[1])
        fb = mem.facts_valid_at(U, "user", "located_at", T, principal=B[0], policy=B[1])
        assert fb == []                                        # (2) and (3)
        assert ([f.edge.id for f in fa] == [e.id]) == (vf <= T < ia)   # (1)
    with pytest.raises(ScopeError):
        mem.facts_valid_at(U, "user", "located_at", vf, principal="mb-a", policy=A[1])


# ----------------------------------------------------------- V-ONE-SNAPSHOT
def test_v_one_snapshot_the_resolution_reads_one_snapshot_under_wal(tmp_path):
    """A correction COMMITTED by another connection during the resolution
    (after its candidate scan, before its per-edge reads) is INVISIBLE to
    the later reads: the prior resolves as `current`, not fenced. The write
    lands (the second store sees it afterwards)."""
    path = tmp_path / "wal.db"
    store = SqliteStore(str(path), clock=RecordingClock())
    store._conn.execute("PRAGMA journal_mode=WAL"); store._conn.commit()
    a = _edge("Porto"); store.add_edge(a)
    writer = SqliteStore(str(path), busy_timeout_ms=2000)
    fired = []
    original = store.current_state

    def current_state_with_a_concurrent_correction(*args, **kw):
        if not fired:
            fired.append(1)
            t = threading.Thread(target=lambda: _correct(
                writer, a, _edge("Braga", supersedes=a.id, valid_from=T0 + D)))
            t.start(); t.join(10)
            assert not t.is_alive()
        return original(*args, **kw)
    store.current_state = current_state_with_a_concurrent_correction
    answer = resolve_as_of(store, U, T0 + 2 * D)
    r = answer.resolution_of(a.id)
    assert r is not None and r.outcome == RETURN_SELF and r.tag == TAG_CURRENT
    assert fired
    live = {e.object: e.active for e in writer.edges(U, active_only=False)}
    assert live == {"Porto": False, "Braga": True}
    store.close(); writer.close()


def test_read_window_joins_on_the_owning_thread_and_serialises_others(tmp_path):
    store = _store(tmp_path)
    store.add_edge(_edge())
    with store.read_window(U):
        assert store._conn.in_transaction
        with store.read_window(U):                         # nested: joins, no deadlock
            assert store.current_state(U, "nope").current_raw is None
        assert store._conn.in_transaction                   # the inner did not commit
        entered = threading.Event()

        def other():
            with store.read_window(U):
                entered.set()
        t = threading.Thread(target=other); t.start()
        assert not entered.wait(0.3)                        # blocked on the instance lock
    t.join(5)
    assert entered.is_set() and not store._conn.in_transaction


# ---------------------------------------------------------------- rendering
def test_the_as_of_answer_renders_the_tag_and_interval_and_omits_now_sections(tmp_path):
    store = _store(tmp_path)
    a = _edge("Porto"); store.add_edge(a)
    b = _correct(store, a, _edge("Braga", supersedes=a.id, valid_from=T0 + 3 * D))
    lapsed = _edge("Lisbon", relation="visited"); store.add_edge(lapsed)
    store.invalidate_edge(lapsed.id, T0 + 5 * D, "lapsed")
    mem = _mem(tmp_path, store)
    mem.remember(U, "we talked about porto")               # an episode: OMITTED under as_of
    r = mem.recall(U, "porto braga lisbon", as_of=T0 + D)
    assert r.episodes == [] and "SUPERSEDED" not in r.context
    assert "corrected-fenced; held 2026-01-01→2026-01-04" in r.context
    assert f"[truth became: {b.id} ({GROUNDED_AS_OF})]" in r.context
    assert "in-interval-stale; held 2026-01-01→2026-01-06" in r.context
    assert "never assert as fact" in r.unverified
    assert {f.edge.id for f in r.as_of.facts} == {a.id, lapsed.id}
    assert r.as_of.resolution_of(lapsed.id).outcome == RETURN_SELF_FLAGGED
