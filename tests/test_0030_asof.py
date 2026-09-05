"""specs/0030 — time-relative classification: the §6 invariants as executable
checks, each under the test NAME the spec's §6 table binds it to (twenty-one
rows, twenty-five names). Fixtures go through the REAL store: snapshots come
from 0029's `edge_state_at` (or the live row when no K is given), the current
carrier from `Store.current_state`, principals through the real `ScopeView`.
Malformed persisted state is planted the ONE honest way the spec allows
(§6a-3b F5: DB-level tamper, stated) — the store cannot emit an invalid edge.

RULE ZERO (the seam model's): every assertion ships with a negative control
in this file that makes it fail.
"""
from __future__ import annotations

import inspect
import json
import pathlib
import re
import sqlite3
import threading
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from veracium import EvidenceAuthor, SqliteStore
from veracium.asof import (EXCLUDED, FENCED_AS_OF, GROUNDED_AS_OF, IDENTITY_UNBOUND,
                           MALFORMED, NOT_VALID_AT_T, SCOPE_HIDDEN, STALE_AT_RECALL,
                           STATUSES, CurrentState, Envelope, RestrictionVerdict,
                           ScopeCell, assertable_as_of, classify_as_of)
from veracium.schema import (AS_OF_DISPOSITION, DISPOSITIONED_REASONS, FENCED,
                             GROUNDABLE, Disclosure, Edge, Provenance, as_utc_optional,
                             as_utc_required)
from veracium.scope import Identity, validate_policy
from veracium.scope_read import ScopeView
from veracium.source_identity import source_identity_digest
from veracium.store.base import RawEdgeState
from veracium.store.revocation import revoke_source

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "veracium"
U = "u"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
D = timedelta(days=1)
NOW = T0 + 150 * D


def _edge(obj="Porto", *, relation="located_at", eid=None, source="mb-a",
          disclosure=Disclosure.MENTIONABLE, valid_from=T0, note=""):
    return Edge(id=eid or f"e-{uuid.uuid4().hex[:10]}", user_id=U, subject="user",
                relation=relation, object=obj, note=note, valid_from=valid_from,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}",
                                      source_id=source, disclosure=disclosure,
                                      observed_at=valid_from))


@pytest.fixture()
def store(tmp_path):
    s = SqliteStore(str(tmp_path / "asof.db"))
    yield s
    s.close()


def _row(store, eid) -> str:
    return store._conn.execute("SELECT json FROM edges WHERE id=?", (eid,)).fetchone()[0]


def _set_row(store, eid, text):
    """DB-level tamper — the stated fixture origin (§6a-3b F5 (b))."""
    store._conn.execute("UPDATE edges SET json=? WHERE id=?", (text, eid)); store._conn.commit()


def _set_snapshot(store, eid, text, k=None):
    """Tamper the JOURNAL payload at (or after) txn k — the other honest origin,
    a journal outliving the model that wrote it (§6a-3b F5 (a))."""
    k = k if k is not None else store.edge_events(U, edge_id=eid)[-1].txn
    store._conn.execute("UPDATE edge_event SET state=? WHERE user_id=? AND edge_id=? AND txn=?",
                        (text, U, eid, k)); store._conn.commit()


def _snap(store, eid, k=None) -> RawEdgeState:
    if k is None:                                    # "the live edge when no K is given"
        return RawEdgeState(edge_id=eid, user_id=U, state=_row(store, eid), txn=0, seq=0,
                            kind="live", recorded_at="")
    return store.edge_state_at(U, eid, k)


def _k(store, eid) -> int:
    return store.edge_events(U, edge_id=eid)[-1].txn


def _cls(store, eid, T, *, now=NOW, k=None, principal=None, policy=None, cs=None, snap=None):
    cs = cs or store.current_state(U, eid, principal=principal, policy=policy)
    view = ScopeView(store, U, principal, policy) if principal is not None else None
    return classify_as_of(Envelope(U, eid), snap or _snap(store, eid, k), cs, T, now, view)


def _payload(store, eid, **changes) -> str:
    d = json.loads(_row(store, eid))
    for key, val in changes.items():
        if "." in key:
            a, b = key.split(".", 1); d[a][b] = val
        else:
            d[key] = val
    return json.dumps(d)


def _iso(dt) -> str:
    return dt.isoformat()


# --------------------------------------------------------------------------- #
# V-NEVER
# --------------------------------------------------------------------------- #

def test_never_grounds_excluded_at_any_t(store):
    """V-NEVER: reason ∈ {corrected, disputed, revoked_source} or class ∈
    {quarantined, use_only} never returns GROUNDED_AS_OF for any sampled T,
    boundaries included. Control: a superseded edge (GROUNDABLE) grounds
    inside its interval, so the sampler discriminates."""
    ia = T0 + 10 * D
    samples = [T0 - D, T0, T0 + 5 * D, ia, ia + 10 * D]
    excluded = []
    for reason in ("corrected", "disputed", "revoked_source"):
        e = _edge(reason); store.add_edge(e); store.invalidate_edge(e.id, ia, reason)
        excluded.append(e.id)
    q = _edge("claim", relation="third_party_claim", disclosure=Disclosure.QUARANTINED); store.add_edge(q)
    uo = _edge("inference", disclosure=Disclosure.USE_ONLY); store.add_edge(uo)
    excluded += [q.id, uo.id]
    for eid in excluded:
        for T in samples:
            r = _cls(store, eid, T)
            assert r.status != GROUNDED_AS_OF, (eid, T, r)
            assert r.status in STATUSES
    # control
    s = _edge("Lisbon"); store.add_edge(s); store.invalidate_edge(s.id, ia, "superseded")
    assert _cls(store, s.id, T0 + 5 * D).status == GROUNDED_AS_OF


# --------------------------------------------------------------------------- #
# V-MALFORMED / V-NORMALIZE / V-NORM-TOTAL
# --------------------------------------------------------------------------- #

def test_incoherent_states_are_malformed_never_grounded(store):
    """V-MALFORMED: active+reason, inactive+no-reason, non-string reason,
    inverted interval → MALFORMED, on EITHER leg, never a raise. An
    unknown-but-STRING reason is coherent → FENCED_AS_OF; an EMPTY interval
    is coherent → NOT_VALID_AT_T. Built via add_edge (which does not couple
    the fields) and DB-level tamper for the non-string case."""
    ia = T0 + 10 * D
    # active + reason / inactive + no reason / inverted — all reachable via add_edge
    a = _edge("a"); a.invalidation_reason = "disputed"; store.add_edge(a)
    b = _edge("b"); b.invalidated_at = ia; store.add_edge(b)
    c = _edge("c", valid_from=ia); c.invalidated_at = T0; c.invalidation_reason = "lapsed"; store.add_edge(c)
    for e in (a, b, c):
        assert _cls(store, e.id, T0 + 5 * D).status == MALFORMED, e.object
        assert _cls(store, e.id, T0 + 5 * D).held_at_K is None
    # non-string reason: snapshot leg, then current leg
    d = _edge("d"); store.add_edge(d); store.invalidate_edge(d.id, ia, "lapsed"); k = _k(store, d.id)
    _set_snapshot(store, d.id, _payload(store, d.id, invalidation_reason=17), k)
    assert _cls(store, d.id, T0 + 5 * D, k=k).status == MALFORMED
    good = _edge("g"); store.add_edge(good); store.invalidate_edge(good.id, ia, "lapsed"); kg = _k(store, good.id)
    _set_row(store, good.id, _payload(store, good.id, invalidation_reason=["unhashable"]))
    assert _cls(store, good.id, T0 + 5 * D, k=kg).status == MALFORMED     # current leg
    # unknown-but-string reason → coherent, FENCED (F8b); empty interval → NOT_VALID_AT_T
    u = _edge("u"); store.add_edge(u); store.invalidate_edge(u.id, ia, "lapsed"); ku = _k(store, u.id)
    _set_snapshot(store, u.id, _payload(store, u.id, invalidation_reason="eighth_reason"), ku)
    assert _cls(store, u.id, T0 + 5 * D, k=ku).status == FENCED_AS_OF
    em = _edge("em"); store.add_edge(em); store.invalidate_edge(em.id, T0, "lapsed")
    for T in (T0 - D, T0, T0 + D):
        assert _cls(store, em.id, T).status == NOT_VALID_AT_T
    # control: the coherent inactive edge grounds
    ok = _edge("ok"); store.add_edge(ok); store.invalidate_edge(ok.id, ia, "lapsed")
    assert _cls(store, ok.id, T0 + 5 * D).status == GROUNDED_AS_OF


def test_normalization_covers_both_states(store):
    """V-NORMALIZE: a non-string (incl. unhashable) reason or a garbage
    timestamp on EITHER leg → MALFORMED without reaching `in`/`dict.get` and
    without a raise; a naive T is coerced (UTC) and classifies like the aware one."""
    ia = T0 + 10 * D
    e = _edge(); store.add_edge(e); store.invalidate_edge(e.id, ia, "lapsed"); k = _k(store, e.id)
    for leg in ("snapshot", "current"):
        for change in ({"invalidation_reason": {"a": 1}}, {"invalidated_at": "not-a-date"},
                       {"invalidated_at": 17}, {"valid_from": "2026-13-45"}):
            f = _edge("f"); store.add_edge(f); store.invalidate_edge(f.id, ia, "lapsed"); kf = _k(store, f.id)
            text = _payload(store, f.id, **change)
            (_set_snapshot if leg == "snapshot" else _set_row)(store, f.id, text, *( [kf] if leg == "snapshot" else []))
            r = _cls(store, f.id, T0 + 5 * D, k=kf)
            assert r.status == MALFORMED, (leg, change, r)
    aware = _cls(store, e.id, T0 + 5 * D, k=k); naive = _cls(store, e.id, (T0 + 5 * D).replace(tzinfo=None), k=k)
    assert aware == naive and aware.status == GROUNDED_AS_OF


def test_required_and_optional_normalizers_are_separate(store):
    """V-NORM-TOTAL: T, now and both valid_from go through as_utc_required
    (None/garbage → refused); only invalidated_at goes through as_utc_optional
    (None stays None). Through the classifier: T=None / now=None → MALFORMED,
    not a raise; a None valid_from on either leg → MALFORMED."""
    with pytest.raises(TypeError):
        as_utc_required(None)
    with pytest.raises(TypeError):
        as_utc_required(True)
    assert as_utc_optional(None) is None
    assert as_utc_required("2026-01-01T00:00:00Z") == T0
    e = _edge(); store.add_edge(e); k = _k(store, e.id)
    assert _cls(store, e.id, None, k=k).status == MALFORMED
    assert _cls(store, e.id, T0 + D, now=None, k=k).status == MALFORMED
    _set_snapshot(store, e.id, _payload(store, e.id, valid_from=None), k)
    assert _cls(store, e.id, T0 + D, k=k).status == MALFORMED
    g = _edge("g"); store.add_edge(g); kg = _k(store, g.id)
    _set_row(store, g.id, _payload(store, g.id, valid_from=None))
    assert _cls(store, g.id, T0 + D, k=kg).status == MALFORMED
    # control: the ordinary edge grounds under the same call shape
    h = _edge("h"); store.add_edge(h)
    assert _cls(store, h.id, T0 + D).status == GROUNDED_AS_OF


# --------------------------------------------------------------------------- #
# V-TWO-STATE / V-FAILCLOSED / V-STALE / V-INTERVAL
# --------------------------------------------------------------------------- #

def test_two_state_current_caps_subtract_only(store):
    """V-TWO-STATE: held_at_K from the snapshot ALONE; status applies current
    caps that only SUBTRACT. Headline: corrected/disputed AFTER K →
    held_at_K=True, FENCED_AS_OF; a standing revocation → EXCLUDED at every
    K; no cap ever RAISES a verdict (held False ⇒ status never GROUNDED)."""
    ia = T0 + 10 * D; T = T0 + 5 * D
    for reason in ("corrected", "disputed"):
        e = _edge(reason); store.add_edge(e); k = _k(store, e.id)
        store.invalidate_edge(e.id, ia, reason)
        r = _cls(store, e.id, T, k=k)
        assert (r.held_at_K, r.status) == (True, FENCED_AS_OF), (reason, r)
    rv = _edge("rv", source="src:R"); store.add_edge(rv); k0 = _k(store, rv.id)
    revoke_source(store, U, source_identity_digest(store.local_origin(), "src:R"), "revoke",
                  "op", _iso(ia).replace("+00:00", "Z"))
    k1 = _k(store, rv.id)
    # EXCLUDED at EVERY K; held_at_K is the snapshot's own fact — True at k0 (the
    # belief was held), False at k1 (the snapshot IS the revoked state)
    for k, held in ((k0, True), (k1, False)):
        r = _cls(store, rv.id, T, k=k)
        assert (r.status, r.held_at_K) == (EXCLUDED, held), (k, r)
    # subtract-only: a snapshot the store did NOT hold as groundable never grounds
    q = _edge("claim", relation="third_party_claim", disclosure=Disclosure.QUARANTINED); store.add_edge(q)
    r = _cls(store, q.id, T)
    assert r.held_at_K is False and r.status != GROUNDED_AS_OF
    # control: with no cap the belief grounds
    ok = _edge("ok"); store.add_edge(ok)
    assert _cls(store, ok.id, T).status == GROUNDED_AS_OF


def test_as_of_disposition_is_total_and_failclosed(store):
    """V-FAILCLOSED: exact key equality with DISPOSITIONED_REASONS; closed
    values; unknown key defaults to FENCED at lookup AND through the
    classifier (the default is reachable)."""
    assert set(AS_OF_DISPOSITION) == set(DISPOSITIONED_REASONS)
    assert set(AS_OF_DISPOSITION.values()) <= {GROUNDABLE, FENCED, "excluded"}
    assert AS_OF_DISPOSITION.get("eighth_reason", FENCED) == FENCED
    assert AS_OF_DISPOSITION["superseded"] == GROUNDABLE       # the asymmetry with WIKI_RETAINING
    ia = T0 + 10 * D
    e = _edge(); store.add_edge(e); store.invalidate_edge(e.id, ia, "lapsed"); k = _k(store, e.id)
    _set_snapshot(store, e.id, _payload(store, e.id, invalidation_reason="eighth_reason"), k)
    r = _cls(store, e.id, T0 + 5 * D, k=k)
    assert r.status == FENCED_AS_OF and r.held_at_K is False
    # control: the source text carries the equality gate, so a drift fails the IMPORT
    src = (SRC / "schema.py").read_text()
    assert "set(AS_OF_DISPOSITION) != set(DISPOSITIONED_REASONS)" in src


def test_result_carries_stale_flag(store):
    """V-STALE: on a GROUNDED_AS_OF result, stale-at-recall iff reason ∈
    {lapsed, decayed} and invalidated_at <= now; a future-lapsing edge grounds
    WITHOUT the flag (now is load-bearing); non-grounded results never carry it."""
    ia = T0 + 10 * D; T = T0 + 5 * D
    for reason in ("lapsed", "decayed"):
        e = _edge(reason); store.add_edge(e); store.invalidate_edge(e.id, ia, reason)
        stale = _cls(store, e.id, T, now=ia + D); fresh = _cls(store, e.id, T, now=ia - D)
        assert stale.status == GROUNDED_AS_OF and STALE_AT_RECALL in stale.flags
        assert fresh.status == GROUNDED_AS_OF and not fresh.flags
    s = _edge("s"); store.add_edge(s); store.invalidate_edge(s.id, ia, "superseded")
    assert not _cls(store, s.id, T, now=ia + D).flags                 # not a staleness reason
    c = _edge("c"); store.add_edge(c); store.invalidate_edge(c.id, ia, "corrected")
    r = _cls(store, c.id, T, now=ia + D)
    assert r.status != GROUNDED_AS_OF and not r.flags


def test_half_open_interval_boundaries(store):
    """V-INTERVAL: [valid_from, invalidated_at) — T == valid_from grounds,
    T == invalidated_at is the successor's (NOT_VALID_AT_T); UTC-aware only."""
    ia = T0 + 10 * D
    e = _edge(); store.add_edge(e); store.invalidate_edge(e.id, ia, "superseded")
    assert _cls(store, e.id, T0).status == GROUNDED_AS_OF
    assert _cls(store, e.id, ia - timedelta(microseconds=1)).status == GROUNDED_AS_OF
    assert _cls(store, e.id, ia).status == NOT_VALID_AT_T
    assert _cls(store, e.id, T0 - timedelta(microseconds=1)).status == NOT_VALID_AT_T
    # an aware T in another zone compares correctly
    other_zone = ia.astimezone(timezone(timedelta(hours=5)))
    assert _cls(store, e.id, other_zone).status == NOT_VALID_AT_T


# --------------------------------------------------------------------------- #
# V-CURRENT-UNCHANGED / V-ADDITIVE
# --------------------------------------------------------------------------- #

def test_current_path_oracle_identical_post0027(tmp_path):
    """V-CURRENT-UNCHANGED (half 1): `Edge.assertable` is unmodified (its
    shipped body), the current recall path calls no as-of code (caller-grep
    over src outside the asof package and the store's derivation), and the
    post-0027 frozen classification oracle replays identically."""
    body = inspect.getsource(Edge.assertable.fget)
    assert "self.active and not self.quarantined and not self.use_only" in body and "valid_now" in body
    callers = []
    for py in SRC.rglob("*.py"):
        rel = str(py.relative_to(SRC))
        if rel.startswith("asof") or rel == "store/current_state.py":
            continue
        if re.search(r"\b(classify_as_of|assertable_as_of)\b", py.read_text()):
            callers.append(rel)
    assert callers == [], f"the current path reaches the as-of classifier: {callers}"
    import importlib.util
    p = ROOT / "specs" / "evidence" / "0027" / "v10_oracle" / "generate_oracle.py"
    spec = importlib.util.spec_from_file_location("v10_oracle", p)
    orc = importlib.util.module_from_spec(spec); spec.loader.exec_module(orc)
    s = orc.build_store(tmp_path / "oracle.db")
    try:
        frozen = json.loads((p.parent / "legacy_projections.json").read_text())
        assert orc.capture(s) == frozen
    finally:
        s.close()


def test_as_of_now_diverges_only_on_two_cells(store):
    """V-CURRENT-UNCHANGED (half 2): `classify_as_of(..., T=now).status ==
    GROUNDED_AS_OF` agrees with `edge.assertable` on the ordinary edge and
    diverges on EXACTLY the §4e state cells AS THEY STAND: 0032 (accepted
    2026-09-04) closed the future-`valid_from` cell — `assertable` now reads
    `valid_now` — so this test asserts that cell AGREES and that the ONE
    remaining divergence (future `invalidated_at`: inactive today, yet validly
    held at T=now) is open. A silently vanished divergence must be
    indistinguishable from nothing, so the set is asserted exactly."""
    now = datetime.now(timezone.utc)          # `valid_now` reads the wall clock: one clock for both predicates
    cells = {}
    ordinary = _edge("ordinary", valid_from=now - 10 * D); store.add_edge(ordinary); cells["ordinary"] = ordinary
    fut_vf = _edge("future-valid-from", valid_from=now + 10 * D); store.add_edge(fut_vf); cells["future_valid_from"] = fut_vf
    fut_ia = _edge("future-invalidated-at", valid_from=now - 10 * D); fut_ia.invalidated_at = now + 10 * D
    fut_ia.invalidation_reason = "lapsed"; store.add_edge(fut_ia); cells["future_invalidated_at"] = fut_ia
    sup = _edge("superseded", valid_from=now - 20 * D); store.add_edge(sup); store.invalidate_edge(sup.id, now - 10 * D, "superseded"); cells["superseded_past"] = sup
    q = _edge("claim", relation="third_party_claim", disclosure=Disclosure.QUARANTINED, valid_from=now - 10 * D); store.add_edge(q); cells["quarantined"] = q
    divergent = set()
    for name, e in cells.items():
        live = Edge.model_validate_json(_row(store, e.id))
        as_of_now = _cls(store, e.id, now, now=now).status == GROUNDED_AS_OF
        if live.assertable != as_of_now:
            divergent.add(name)
    assert divergent == {"future_invalidated_at"}, divergent
    assert Edge.model_validate_json(_row(store, fut_vf.id)).assertable is False   # 0032 closed this cell


def test_no_edge_field_added(store):
    """V-ADDITIVE: no field added to `Edge`; the classifier is a pure function
    of its carrier inputs + the registry + (T, now, view) — no clock read, no
    store write, same inputs → same output."""
    assert set(Edge.model_fields) == {
        "id", "user_id", "subject", "relation", "object", "note", "volatility", "provenance",
        "valid_from", "invalidated_at", "invalidation_reason", "supersedes", "original_relation",
        "needs_confirmation", "agreement", "ungrounded", "times_used", "outcome_counts",
        "last_outcome", "last_outcome_at"}
    src = (SRC / "asof" / "classify.py").read_text()
    assert "datetime.now" not in src and "utcnow" not in src and "_conn" not in src
    e = _edge(); store.add_edge(e)
    cs = store.current_state(U, e.id); snap = _snap(store, e.id)
    a = classify_as_of(Envelope(U, e.id), snap, cs, T0 + D, NOW)
    b = classify_as_of(Envelope(U, e.id), snap, cs, T0 + D, NOW)
    assert a == b


# --------------------------------------------------------------------------- #
# V-SCOPE / V-FAILHIDDEN
# --------------------------------------------------------------------------- #

def _policy(store, cross_visible):
    return validate_policy({}, cross_scope_visible=cross_visible, local_origin=store.local_origin())


def test_scope_outermost_hidden_never_leaks(store):
    """V-SCOPE (a): a cross-scope HIDDEN record returns ONLY SCOPE_HIDDEN —
    never MALFORMED, never a held_at_K — even when its payload is malformed
    (joint scenario 8). Control: the same record unscoped is MALFORMED."""
    me = Identity(origin=None, source_id="mb-a"); pol = _policy(store, cross_visible=False)
    foreign = _edge("Paris", source="other-mailbox"); store.add_edge(foreign); k = _k(store, foreign.id)
    r = _cls(store, foreign.id, T0 + D, k=k, principal=me, policy=pol)
    assert (r.status, r.held_at_K) == (SCOPE_HIDDEN, None)
    _set_row(store, foreign.id, _payload(store, foreign.id, invalidation_reason=17))     # malformed too
    r = _cls(store, foreign.id, T0 + D, k=k, principal=me, policy=pol)
    assert (r.status, r.held_at_K, r.flags) == (SCOPE_HIDDEN, None, frozenset())
    assert _cls(store, foreign.id, T0 + D, k=k).status == MALFORMED             # control: unscoped reveals the condition


def test_scope_composes_via_time_relative_verdict_not_shape(store, monkeypatch):
    """V-SCOPE (b): a cross-scope-VISIBLE superseded record grounds unscoped
    and is FENCED_AS_OF for the restricted principal — composed through
    gate.scoped_assertable on the time-relative verdict; `ScopeView.shape()`
    is never called (it short-circuits on today's assertability, which is
    False for every historical edge)."""
    me = Identity(origin=None, source_id="mb-a"); pol = _policy(store, cross_visible=True)
    foreign = _edge("Paris", source="other-mailbox"); store.add_edge(foreign); k = _k(store, foreign.id)
    store.invalidate_edge(foreign.id, T0 + 10 * D, "superseded")
    def boom(self, *a, **kw):
        raise AssertionError("view.shape() was called")
    monkeypatch.setattr(ScopeView, "shape", boom, raising=False)
    assert _cls(store, foreign.id, T0 + 5 * D, k=k).status == GROUNDED_AS_OF
    r = _cls(store, foreign.id, T0 + 5 * D, k=k, principal=me, policy=pol)
    assert (r.status, r.held_at_K) == (FENCED_AS_OF, True)
    # control: the principal's OWN superseded record grounds under the same policy
    own = _edge("Porto", source="mb-a"); store.add_edge(own); ko = _k(store, own.id)
    store.invalidate_edge(own.id, T0 + 10 * D, "superseded")
    assert _cls(store, own.id, T0 + 5 * D, k=ko, principal=me, policy=pol).status == GROUNDED_AS_OF


def test_unreadable_scope_fails_closed_to_hidden(store):
    """V-FAILHIDDEN: an unreadable CURRENT payload with a view → SCOPE_HIDDEN
    (the cell is fail-closed); with no view → MALFORMED. The foreign/garbage
    payload's scope fields never reach a visibility decision."""
    me = Identity(origin=None, source_id="mb-a"); pol = _policy(store, cross_visible=True)
    e = _edge("Porto", source="mb-a"); store.add_edge(e); k = _k(store, e.id)
    _set_row(store, e.id, "{not json")
    cs = store.current_state(U, e.id, principal=me, policy=pol)
    assert cs.scope_cell is not None and cs.scope_cell.fail_closed and not cs.scope_cell.visible
    assert _cls(store, e.id, T0 + D, k=k, principal=me, policy=pol, cs=cs).status == SCOPE_HIDDEN
    assert _cls(store, e.id, T0 + D, k=k).status == MALFORMED
    # control: the readable row is visible to its own principal and grounds
    g = _edge("Braga", source="mb-a"); store.add_edge(g)
    assert _cls(store, g.id, T0 + D, principal=me, policy=pol).status == GROUNDED_AS_OF


# --------------------------------------------------------------------------- #
# V-BIND
# --------------------------------------------------------------------------- #

def test_six_leg_binding__with_its_control(store):
    """V-BIND: snapshot, current_state, envelope, view, and the cell's
    principal on both branches must cohere — checked BEFORE visibility, the
    guard before the dereference. Each broken leg → IDENTITY_UNBOUND; the
    honest assembly binds (control)."""
    me = Identity(origin=None, source_id="mb-a"); pol = _policy(store, cross_visible=True)
    a = _edge("A"); b = _edge("B"); store.add_edge(a); store.add_edge(b)
    cs_a = store.current_state(U, a.id, principal=me, policy=pol); snap_a = _snap(store, a.id)
    view = ScopeView(store, U, me, pol)
    assert classify_as_of(Envelope(U, a.id), snap_a, cs_a, T0 + D, NOW, view).status == GROUNDED_AS_OF  # control
    assert classify_as_of(Envelope(U, b.id), snap_a, cs_a, T0 + D, NOW, view).status == IDENTITY_UNBOUND  # envelope
    assert classify_as_of(Envelope(U, a.id), _snap(store, b.id), cs_a, T0 + D, NOW, view).status == IDENTITY_UNBOUND  # snapshot
    assert classify_as_of(Envelope("mallory", a.id), snap_a, cs_a, T0 + D, NOW, view).status == IDENTITY_UNBOUND  # user
    other_view = ScopeView(store, "v", me, pol)
    assert classify_as_of(Envelope(U, a.id), snap_a, cs_a, T0 + D, NOW, other_view).status == IDENTITY_UNBOUND  # view leg
    # the cell's principal: computed for someone else
    cs_other = replace(cs_a, scope_cell=replace(cs_a.scope_cell, principal=(None, "mb-z")))
    assert classify_as_of(Envelope(U, a.id), snap_a, cs_other, T0 + D, NOW, view).status == IDENTITY_UNBOUND
    cs_nameless = replace(cs_a, scope_cell=replace(cs_a.scope_cell, principal=None))
    assert classify_as_of(Envelope(U, a.id), snap_a, cs_nameless, T0 + D, NOW, view).status == IDENTITY_UNBOUND
    cs_cellless = replace(cs_a, scope_cell=None)
    assert classify_as_of(Envelope(U, a.id), snap_a, cs_cellless, T0 + D, NOW, view).status == IDENTITY_UNBOUND
    # binding is PARSE-INDEPENDENT: a corrupt payload still binds, then is MALFORMED
    corrupt = snap_a._replace(state="{garbage")
    assert classify_as_of(Envelope(U, a.id), corrupt, cs_a, T0 + D, NOW, view).status == MALFORMED


def test_viewless_cell_is_refused__with_its_control(store):
    """V-BIND (round-8 F1): ANY cell without a view is refused — the pair is
    present together or absent together. Control: no cell + no view binds."""
    me = Identity(origin=None, source_id="mb-a"); pol = _policy(store, cross_visible=True)
    a = _edge("A"); store.add_edge(a); snap = _snap(store, a.id)
    with_cell = store.current_state(U, a.id, principal=me, policy=pol)
    assert with_cell.scope_cell is not None
    assert classify_as_of(Envelope(U, a.id), snap, with_cell, T0 + D, NOW, None).status == IDENTITY_UNBOUND
    principal_less = replace(with_cell, scope_cell=ScopeCell(visible=True, shape="own", principal=None))
    assert classify_as_of(Envelope(U, a.id), snap, principal_less, T0 + D, NOW, None).status == IDENTITY_UNBOUND
    no_cell = store.current_state(U, a.id)
    assert no_cell.scope_cell is None
    assert classify_as_of(Envelope(U, a.id), snap, no_cell, T0 + D, NOW, None).status == GROUNDED_AS_OF


# --------------------------------------------------------------------------- #
# V-WINDOW
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("mode", ["delete", "wal"])
def test_transactional_read_is_one_world__both_journal_modes(tmp_path, monkeypatch, mode):
    """V-WINDOW: one read window, one world, in BOTH journal modes. A second
    store instance commits a mutation INSIDE the reader's window (a
    connection-level fixture in tests/, guarded — no product hook): the
    mutation moves the edge to a REVOKED source, so a non-one-world read
    would carry current_raw from before the write and a RESTRICTED verdict
    computed after it. Property: the carrier describes ONE state (CLEAR, and
    the pre-write row). Mechanism per mode: rollback-journal REFUSES the
    writer for the window's duration; WAL lets it proceed and the reader keeps
    its snapshot."""
    p = str(tmp_path / f"{mode}.db")
    reader = SqliteStore(p); writer = SqliteStore(p, busy_timeout_ms=200)
    try:
        reader._conn.execute(f"PRAGMA journal_mode={'WAL' if mode == 'wal' else 'DELETE'}")
        assert reader._conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == mode
        e = _edge("Porto", source="src:clean"); reader.add_edge(e)
        other = _edge("Faro", source="src:bad", relation="visits"); reader.add_edge(other)
        revoke_source(reader, U, source_identity_digest(reader.local_origin(), "src:bad"), "revoke",
                      "op", "2026-01-05T00:00:00Z")
        before = _row(reader, e.id)
        import veracium.store.current_state as cs_mod
        real = cs_mod.standing_revocations
        outcome = {}
        moved = Edge.model_validate_json(before); moved.provenance.source_id = "src:bad"
        def interleave(conn, user_id):
            # INSIDE the reader's window: the writer commits on its own connection
            def w():
                try:
                    writer.add_edge(moved); outcome["writer"] = "committed"
                except sqlite3.OperationalError as ex:
                    outcome["writer"] = f"refused: {ex}"
            t = threading.Thread(target=w); t.start(); t.join(5)
            return real(conn, user_id)
        monkeypatch.setattr(cs_mod, "standing_revocations", interleave)
        cs = reader.current_state(U, e.id)
        monkeypatch.setattr(cs_mod, "standing_revocations", real)
        assert cs.current_raw == before
        assert cs.source_restricted is RestrictionVerdict.CLEAR, "the verdict saw a different world than the row"
        if mode == "delete":
            assert outcome["writer"].startswith("refused"), outcome
        else:
            assert outcome["writer"] == "committed", outcome
        # control: AFTER the window the moved row is restricted
        if mode == "delete":
            writer.add_edge(moved)
        after = reader.current_state(U, e.id)
        assert after.source_restricted is RestrictionVerdict.RESTRICTED and after.current_raw != before
    finally:
        reader.close(); writer.close()


# --------------------------------------------------------------------------- #
# V-CARRIER-AGREES / V-PARSE / V-COLUMN-NOT-INPUT / V-EXTRACT / V-RAW
# --------------------------------------------------------------------------- #

def test_payload_identity_must_match_the_row(store, monkeypatch):
    """V-CARRIER-AGREES: a payload carrying another edge's id/user under this
    row: snapshot leg → MALFORMED; current leg → V-FAILHIDDEN's branch
    (SCOPE_HIDDEN with a view, MALFORMED without), and the FOREIGN payload's
    scope fields never reach the visibility decision (decision() not called)."""
    me = Identity(origin=None, source_id="mb-a"); pol = _policy(store, cross_visible=True)
    a = _edge("A", source="mb-a"); b = _edge("B", source="other-mailbox"); store.add_edge(a); store.add_edge(b)
    ka = _k(store, a.id)
    _set_snapshot(store, a.id, _row(store, b.id), ka)                  # B's content under A's row
    assert _cls(store, a.id, T0 + D, k=ka).status == MALFORMED
    c = _edge("C", source="mb-a"); store.add_edge(c); kc = _k(store, c.id)
    _set_row(store, c.id, _row(store, b.id))
    calls = []
    real = ScopeView.decision
    monkeypatch.setattr(ScopeView, "decision", lambda self, rec: calls.append(rec.id) or real(self, rec))
    r = _cls(store, c.id, T0 + D, k=kc, principal=me, policy=pol)
    assert r.status == SCOPE_HIDDEN and calls == [], "the foreign payload reached the visibility decision"
    assert _cls(store, c.id, T0 + D, k=kc).status == MALFORMED
    # control: the honest payload's identity agrees and grounds
    assert _cls(store, b.id, T0 + D).status == GROUNDED_AS_OF


def test_unparseable_payloads_are_classified_not_raised(store):
    """V-PARSE: unparseable CURRENT text with a view → SCOPE_HIDDEN, without →
    MALFORMED; unparseable SNAPSHOT → MALFORMED. All three BIND first (row-
    sourced identity) — a parse failure is classified, never mistaken for an
    identity fault, and never raised."""
    me = Identity(origin=None, source_id="mb-a"); pol = _policy(store, cross_visible=True)
    e = _edge("Porto", source="mb-a"); store.add_edge(e); k = _k(store, e.id)
    for text in ("{not json", "[1, 2]", '{"id": "x", "id": "y"}', "﻿{}", "null"):
        s = _snap(store, e.id, k)._replace(state=text)
        r = classify_as_of(Envelope(U, e.id), s, store.current_state(U, e.id), T0 + D, NOW)
        assert r.status == MALFORMED, (text, r)
    _set_row(store, e.id, "{not json")
    assert _cls(store, e.id, T0 + D, k=k, principal=me, policy=pol).status == SCOPE_HIDDEN
    assert _cls(store, e.id, T0 + D, k=k).status == MALFORMED


def test_classifier_never_reads_the_event_reason_column(store, tmp_path):
    """V-COLUMN-NOT-INPUT: the event `reason` COLUMN is never a classifier
    input — the state's own invalidation_reason lives INSIDE the payload. A
    migrated inactive edge's baseline event carries reason NULL with a
    `superseded` payload and classifies from the PAYLOAD; a RawEdgeState with
    a garbage reason/kind classifies identically to the honest one."""
    from veracium.store import schema_version as sv
    from veracium.store.migration import migrate_store
    p = str(tmp_path / "v12.db"); c = sqlite3.connect(p)
    for o in sv.SCHEMAS[12]:
        c.execute(o.ddl)
    c.execute("INSERT INTO store_identity(id, origin) VALUES(1, ?)", (str(uuid.uuid4()),))
    old = _edge("Lisbon"); old.invalidated_at = T0 + 10 * D; old.invalidation_reason = "superseded"
    c.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,quarantined,json) VALUES(?,?,?,?,?,?,?,?)",
              (old.id, U, "user", "located_at", "Lisbon", 0, 0, old.model_dump_json()))
    c.execute("PRAGMA user_version = 12"); c.commit(); c.close()
    migrate_store(p); s = SqliteStore(p)
    try:
        ev = s.edge_events(U)[0]
        assert ev.kind == "baseline" and ev.reason is None
        r = _cls(s, old.id, T0 + 5 * D, k=ev.txn)
        assert (r.status, r.held_at_K) == (GROUNDED_AS_OF, True)      # from the payload's `superseded`
        garbage = _snap(s, old.id, ev.txn)._replace(kind="corrupt", recorded_at="")
        assert classify_as_of(Envelope(U, old.id), garbage, s.current_state(U, old.id), T0 + 5 * D, NOW) == r
    finally:
        s.close()
    src = (SRC / "asof" / "classify.py").read_text()
    assert "snapshot_raw.reason" not in src and "snapshot_raw.kind" not in src


def test_missing_raw_fields_never_default(store):
    """V-EXTRACT: every field the rules read is extracted defensively — a
    missing content field or flag-bearing provenance key ⇒ MALFORMED /
    SCOPE_HIDDEN, NEVER a default (a defaulted-False flag would GRANT; a
    missing subject would raise at the digest)."""
    from veracium.asof.adapter import REQUIRED_KEYS, SCOPE_PROVENANCE_KEYS
    me = Identity(origin=None, source_id="mb-a"); pol = _policy(store, cross_visible=True)
    e = _edge("Porto", source="mb-a"); store.add_edge(e); k = _k(store, e.id)
    honest = json.loads(_row(store, e.id))
    for key in sorted(REQUIRED_KEYS):
        d = dict(honest); d.pop(key)
        s = _snap(store, e.id, k)._replace(state=json.dumps(d))
        assert classify_as_of(Envelope(U, e.id), s, store.current_state(U, e.id), T0 + D, NOW).status == MALFORMED, key
    for key in sorted(SCOPE_PROVENANCE_KEYS):
        d = json.loads(_row(store, e.id)); d["provenance"].pop(key)
        f = _edge("F", source="mb-a"); store.add_edge(f); kf = _k(store, f.id)
        d["id"] = f.id
        _set_row(store, f.id, json.dumps(d))
        assert _cls(store, f.id, T0 + D, k=kf, principal=me, policy=pol).status == SCOPE_HIDDEN, key
        assert _cls(store, f.id, T0 + D, k=kf).status == MALFORMED, key
    # the flags are DERIVED, never read: a payload claiming quarantined=False is ignored
    d = json.loads(_row(store, e.id)); d["quarantined"] = False; d["use_only"] = False
    d["provenance"]["disclosure"] = "quarantined"
    s = _snap(store, e.id, k)._replace(state=json.dumps(d))
    r = classify_as_of(Envelope(U, e.id), s, store.current_state(U, e.id), T0 + D, NOW)
    assert r.status != GROUNDED_AS_OF and r.held_at_K is False


def test_malformed_state_traverses_the_raw_carrier(store):
    """V-RAW: malformed persisted state, through the REAL load path, both
    hidden and visible — origin (b), DB-level tamper of a then-valid payload
    (stated). The carrier hands the text through verbatim; the classifier
    classifies: visible → MALFORMED, hidden → SCOPE_HIDDEN only; no raise."""
    me = Identity(origin=None, source_id="mb-a"); pol = _policy(store, cross_visible=False)
    vis = _edge("Porto", source="mb-a"); hid = _edge("Paris", source="other-mailbox")
    store.add_edge(vis); store.add_edge(hid)
    future_shape = '{"id": "%s", "user_id": "%s", "schema": 99, "valid_from": {"epoch": 0}}'
    for e in (vis, hid):
        k = _k(store, e.id); _set_snapshot(store, e.id, future_shape % (e.id, U), k)
        assert store.edge_state_at(U, e.id, k).state == future_shape % (e.id, U)   # verbatim
    assert _cls(store, vis.id, T0 + D, k=_k(store, vis.id), principal=me, policy=pol).status == MALFORMED
    assert _cls(store, hid.id, T0 + D, k=_k(store, hid.id), principal=me, policy=pol).status == SCOPE_HIDDEN


# --------------------------------------------------------------------------- #
# V-TRUST-INPUT / V-SUBTRACT
# --------------------------------------------------------------------------- #

def test_restricted_source_excludes_via_standing_state_not_row(store):
    """V-TRUST-INPUT: a superseded (inactive) edge whose source is later
    revoked → EXCLUDED, driven by the STANDING source state — the row still
    says `superseded` (the sweep skips inactive rows) and is byte-unchanged."""
    e = _edge("Porto", source="src:S"); store.add_edge(e); k = _k(store, e.id)
    store.invalidate_edge(e.id, T0 + 10 * D, "superseded")
    row_before = _row(store, e.id)
    assert _cls(store, e.id, T0 + 5 * D, k=k).status == GROUNDED_AS_OF
    revoke_source(store, U, source_identity_digest(store.local_origin(), "src:S"), "revoke", "op",
                  "2026-02-01T00:00:00Z")
    cs = store.current_state(U, e.id)
    assert cs.source_restricted is RestrictionVerdict.RESTRICTED
    assert json.loads(cs.current_raw)["invalidation_reason"] == "superseded"
    assert _row(store, e.id) == row_before, "the row was rewritten — the input must be the standing state"
    r = _cls(store, e.id, T0 + 5 * D, k=k, cs=cs)
    assert (r.status, r.held_at_K) == (EXCLUDED, True)
    # negative control: a classifier reading the ROW's reason would say GROUNDABLE here
    assert AS_OF_DISPOSITION[json.loads(cs.current_raw)["invalidation_reason"]] == GROUNDABLE


def test_lift_flips_the_trust_input_without_touching_the_row(store):
    """V-TRUST-INPUT (free cell): LIFT flips the verdict with no row ever
    rewritten; the snapshot at K is unchanged — held_at_K stable, status moves."""
    e = _edge("Porto", source="src:S"); store.add_edge(e); k = _k(store, e.id)
    store.invalidate_edge(e.id, T0 + 10 * D, "superseded"); row = _row(store, e.id)
    digest = source_identity_digest(store.local_origin(), "src:S")
    revoke_source(store, U, digest, "revoke", "op", "2026-02-01T00:00:00Z")
    a = _cls(store, e.id, T0 + 5 * D, k=k)
    revoke_source(store, U, digest, "lift", "op", "2026-02-02T00:00:00Z")
    b = _cls(store, e.id, T0 + 5 * D, k=k)
    assert (a.status, b.status) == (EXCLUDED, GROUNDED_AS_OF) and a.held_at_K is b.held_at_K is True
    assert _row(store, e.id) == row


def test_current_projection_subtracts_on_time_and_identity(store):
    """V-SUBTRACT: the current leg subtracts on VALID-TIME and SEMANTIC
    IDENTITY too. (a) snapshot open at K, superseded effective Feb, T in Mar →
    FENCED_AS_OF, held True; (b) same-id semantic replacement after K →
    FENCED_AS_OF, held True, current still active. Neither is EXCLUDED."""
    e = _edge("Porto"); store.add_edge(e); k = _k(store, e.id)
    store.invalidate_edge(e.id, datetime(2026, 2, 1, tzinfo=timezone.utc), "superseded")
    r = _cls(store, e.id, datetime(2026, 3, 1, tzinfo=timezone.utc), k=k)
    assert (r.status, r.held_at_K) == (FENCED_AS_OF, True)
    assert _cls(store, e.id, datetime(2026, 1, 15, tzinfo=timezone.utc), k=k).status == GROUNDED_AS_OF  # control
    f = _edge("Lisbon"); store.add_edge(f); kf = _k(store, f.id)
    store.add_edge(_edge("Madrid", eid=f.id))                          # same id, new content, still active
    r = _cls(store, f.id, T0 + D, k=kf)
    assert (r.status, r.held_at_K) == (FENCED_AS_OF, True)
    assert json.loads(_row(store, f.id))["invalidated_at"] is None
