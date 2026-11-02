"""specs/0048 §6: maintenance never raises confidence — the decay bounds, and expiry decided from the current row.

One cell per §6 invariant, named as §6 names it: N4 (property), N4b, N4b′, N4b-assign, N4c (i–iii; iv is
tests/test_0048_evidence.py::test_every_tripwire_hit_on_this_tree_is_classified), N4d, N4d-prefix, N4e, N4f (both
halves), N4g, N4h, N4i. The §6 mutant table runs against these cells through the shared mutation protocol
(specs/evidence/0048/closure/…); the reproductions of the shipped defects these cells invert stay in
tests/test_0048_evidence.py, rewritten to assert the fixed behaviour.
"""
from __future__ import annotations

import ast
import datetime as dt
import json
import math
import pathlib
import random
import re
import sqlite3
import threading

import pytest

from veracium import Disclosure, Edge, EvidenceAuthor, Memory, MemoryConfig, Provenance
from veracium import schema as S
from veracium.config import validate_decay_bound
from veracium.lifecycle import expire
from veracium.store import sqlite as SQ
from veracium.store.sqlite import SqliteStore

ROOT = pathlib.Path(__file__).resolve().parent.parent
U = "u1"
OLD = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)
NOW = dt.datetime(2026, 11, 2, tzinfo=dt.timezone.utc)
FIELDS = ("decay_factor", "confidence_floor")
REJECTED = [1.5, -0.1, float("nan"), float("inf"), float("-inf"), True, False, "0.5", None,
            math.nextafter(1.0, 2.0), math.nextafter(0.0, -1.0)]
BOUNDARY = [0.0, 1.0, 0, 1]


def _quiet(prompt, *, system=None, role="compile", json_schema=None):
    return json.dumps({"triples": [], "episode": "we talked", "instructions": []})


def _mem(db, **cfg):
    try:
        config = MemoryConfig(db_path=str(db), wiki_recompile_after_writes=0, scope_groups={}, require_source_id=False,
                              **cfg)
    except ValueError as ex:          # every policy a cell builds here is valid: a refusal is the defect under test
        raise AssertionError(f"a valid config was refused: {ex}")
    return Memory(llm=_quiet, config=config)


def _edge(eid, vol, conf, observed=OLD, flagged=False):
    return Edge(id=eid, user_id=U, subject="user", relation="works_on", object=f"Atlas {eid}", volatility=vol,
                needs_confirmation=flagged,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=f"ev-{eid}",
                                      disclosure=Disclosure.MENTIONABLE, confidence=conf, observed_at=observed))


class Duck:
    """A duck-typed policy object: `expire()` reads three attributes from whatever it is handed (§2c row 3)."""

    def __init__(self, decay_factor=0.5, confidence_floor=0.3):
        self.decay_factor, self.confidence_floor = decay_factor, confidence_floor
        self.volatility_lifetime_days = MemoryConfig().volatility_lifetime_days


@pytest.fixture
def decay_mapped(monkeypatch):
    """SLOW -> DECAY for the test only (the shipped table maps no class to DECAY, §2c-ii row 3)."""
    monkeypatch.setitem(S.DEFAULT_EXPIRY, S.Volatility.SLOW, S.ExpiryBehavior.DECAY)


def _snapshot(path):
    """Every table's rows, ordered: the store's complete state (counters and 0029's journal included)."""
    conn = sqlite3.connect(str(path))
    try:
        names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {n: conn.execute(f'SELECT * FROM "{n}" ORDER BY 1').fetchall() for n in names}
    finally:
        conn.close()


def _refuses(exc_type, fn, match=None):
    """`fn()` must raise `exc_type` (optionally matching `match`); a different exception, or none, fails BY ASSERTION
    (so a mutant that breaks the refusal reads as a kill the classifier can vouch for, not an escaping error)."""
    try:
        fn()
    except BaseException as ex:  # noqa: BLE001 — the point is to classify it
        assert isinstance(ex, exc_type), f"expected {exc_type.__name__}, got {type(ex).__name__}: {ex}"
        assert match is None or re.search(match, str(ex)), (match, str(ex))
        return ex
    raise AssertionError(f"expected {exc_type.__name__}: nothing raised")


def _expire_valid(store, config, **kw):
    """expire() under a policy the cell holds VALID: a refusal is the defect under test, so it fails BY ASSERTION."""
    try:
        return expire(store, U, config, **kw)
    except ValueError as ex:
        raise AssertionError(f"a valid policy was refused: {ex}")


def _row(store, eid):
    (e,) = [x for x in store.edges(U, active_only=False, include_quarantined=True) if x.id == eid]
    return e


# ---- N4b, N4b′, N4b-assign: one validator, at construction and on assignment -----------------------------------------

@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", REJECTED, ids=repr)
def test_config_bounds_are_validated(field, value):
    """N4b: both fields refuse >1, <0, NaN, ±inf, a bool, a string, None and the nearest floats beyond each bound,
    with ValueError naming the field."""
    with pytest.raises(ValueError, match=field):
        MemoryConfig(**{field: value})


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", BOUNDARY, ids=repr)
def test_boundary_configs_are_still_valid(field, value):
    """N4b′: 0.0, 1.0, 0 and 1 stay accepted on both fields, at construction and on assignment (the cheapest wrong fix
    is an exclusive bound)."""
    try:
        built = MemoryConfig(**{field: value})
        c = MemoryConfig()
        setattr(c, field, value)
    except ValueError as ex:
        raise AssertionError(f"the boundary {value!r} on {field} was refused: {ex}")
    assert getattr(built, field) == value and getattr(c, field) == value


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", REJECTED, ids=repr)
def test_config_bounds_hold_on_assignment(field, value):
    """N4b-assign: every value N4b refuses, assigned after construction, refuses, and the field keeps its old value."""
    c = MemoryConfig(decay_factor=0.25, confidence_floor=0.75)
    old = getattr(c, field)
    with pytest.raises(ValueError, match=field):
        setattr(c, field, value)
    assert getattr(c, field) == old


def test_other_fields_still_assign():
    """The __setattr__ is on the two bounds only (§10 Q4): every other field assigns as before."""
    c = MemoryConfig()
    c.db_path = "elsewhere.db"
    c.consolidate_min_batch = 3
    assert (c.db_path, c.consolidate_min_batch) == ("elsewhere.db", 3)


# ---- N4d, N4g: the policy is validated once, at expire()'s entry, for any config -------------------------------------

def _mixed(tmp_path):
    """An expired TRANSIENT edge listed BEFORE an expired SLOW edge (SLOW mapped to DECAY by the caller): a validation
    moved back inside the DECAY branch would lapse the TRANSIENT edge first."""
    s = SqliteStore(str(tmp_path / "n4d.db"))
    s.add_edge(_edge("a-transient", S.Volatility.TRANSIENT, 0.9))
    s.add_edge(_edge("b-slow", S.Volatility.SLOW, 0.9))
    assert [e.id for e in s.edges(U)] == ["a-transient", "b-slow"]
    return s


@pytest.mark.parametrize("factor,floor", [(2.0, 0.3), (-1.0, 0.3), (float("nan"), 0.3), (True, 0.3), ("0.5", 0.3),
                                          (0.5, 2.0), (0.5, -0.5), (0.5, float("nan"))], ids=repr)
def test_decay_config_refusal_writes_nothing(tmp_path, decay_mapped, factor, floor):
    """N4d: a malformed duck-typed policy refuses at entry with ValueError, and the complete store snapshot is
    byte-identical (every table; the counters and 0029's journal included). Then the same on an EMPTY store."""
    s = _mixed(tmp_path)
    before = _snapshot(tmp_path / "n4d.db")
    _refuses(ValueError, lambda: expire(s, U, Duck(factor, floor), now=NOW))
    assert _snapshot(tmp_path / "n4d.db") == before
    empty = SqliteStore(str(tmp_path / "empty.db"))
    _refuses(ValueError, lambda: expire(empty, U, Duck(factor, floor), now=NOW))


@pytest.mark.parametrize("conf", [0.0, 0.3, 0.9])
@pytest.mark.parametrize("factor", [2.0, math.nextafter(1.0, 2.0), -1.0, float("nan"), True], ids=repr)
def test_factor_is_validated_whatever_the_confidence(tmp_path, decay_mapped, conf, factor):
    """N4g: the factor refuses at entry whatever the edge's confidence. 0.3 × 2.0 → 0.6 is IN range: it is the
    retained regression a range-only implementation passes (0.9 × 2.0 alone cannot tell them apart)."""
    s = SqliteStore(str(tmp_path / "n4g.db"))
    s.add_edge(_edge("e", S.Volatility.SLOW, conf))
    before = _snapshot(tmp_path / "n4g.db")
    _refuses(ValueError, lambda: expire(s, U, Duck(factor, 0.0), now=NOW), match="decay_factor")
    assert _snapshot(tmp_path / "n4g.db") == before
    assert _row(s, "e").provenance.confidence == conf


def test_the_policy_is_read_once_at_entry(tmp_path, decay_mapped):
    """§4B / N3: the three attributes are read ONCE; a policy object that changes under the run (or a lifetimes dict
    mutated mid-run) does not change what the run applies."""
    s = SqliteStore(str(tmp_path / "once.db"))
    for i in range(3):
        s.add_edge(_edge(f"e{i}", S.Volatility.SLOW, 0.8))

    class Shifting(Duck):
        reads = 0

        @property
        def decay_factor(self):
            Shifting.reads += 1
            return 0.5 if Shifting.reads == 1 else 2.0

        @decay_factor.setter
        def decay_factor(self, v):
            pass

    expire(s, U, Shifting(), now=NOW)
    assert Shifting.reads == 1
    assert [round(e.provenance.confidence, 6) for e in s.edges(U)] == [0.4, 0.4, 0.4]


def test_the_lifetimes_are_copied_at_entry(tmp_path):
    """research's N3: `volatility_lifetime_days` is a mutable dict; a host mutating it while a run is in flight (here,
    during the listing) does not change what that run decides — the transitions use the copy taken at entry."""
    s = SqliteStore(str(tmp_path / "copy.db"))
    for i in range(3):
        s.add_edge(_edge(f"e{i}", S.Volatility.SLOW, 0.6))
    cfg = MemoryConfig()
    real = s.edges

    def mutate_while_listing(*a, **k):
        r = list(real(*a, **k))
        cfg.volatility_lifetime_days[S.Volatility.SLOW] = None    # "never expires", set mid-run
        return r
    s.edges = mutate_while_listing
    out = expire(s, U, cfg, now=NOW)
    s.edges = real
    assert out["flagged_for_confirmation"] == 3, out


def test_a_host_that_rebinds_lifecycles_table_is_honoured(tmp_path, monkeypatch):
    """research's F2: the shipped expire() read `lifecycle.DEFAULT_EXPIRY`, so a host that REBINDS that name to its own
    table (rather than editing schema.DEFAULT_EXPIRY in place) was honoured. expire() reads its own name at entry and
    hands the copy to the transition, so the rebound table decides, not the store module's import."""
    import veracium.lifecycle as LC
    table = dict(S.DEFAULT_EXPIRY)
    table[S.Volatility.SLOW] = S.ExpiryBehavior.DECAY
    monkeypatch.setattr(LC, "DEFAULT_EXPIRY", table)
    assert S.DEFAULT_EXPIRY[S.Volatility.SLOW] == S.ExpiryBehavior.CONFIRM, "the schema's own table is untouched"
    s = SqliteStore(str(tmp_path / "rebound.db"))
    s.add_edge(_edge("e", S.Volatility.SLOW, 0.9))
    out = _expire_valid(s, Duck(0.5, 0.3), now=NOW)
    e = _row(s, "e")
    assert out["flagged_for_confirmation"] == 0 and round(e.provenance.confidence, 9) == 0.45, (out, e)


# ---- N4d-prefix: a later ordinary failure keeps the per-edge prefix -------------------------------------------------

def test_a_later_failure_keeps_the_processed_prefix(tmp_path, monkeypatch):
    """N4d-prefix: a valid policy, a store failure injected INSIDE the second due edge's transition (at its write):
    the first edge's transition is committed, the second's is rolled back, and the error propagates."""
    s = SqliteStore(str(tmp_path / "prefix.db"))
    s.add_edge(_edge("e1", S.Volatility.SLOW, 0.6))      # SLOW -> CONFIRM (the shipped table)
    s.add_edge(_edge("e2", S.Volatility.SLOW, 0.6))
    real, calls = s._upsert_edge_row, []

    def failing(edge):
        calls.append(edge.id)
        if len(calls) == 2:
            raise RuntimeError("injected store failure")
        return real(edge)
    monkeypatch.setattr(s, "_upsert_edge_row", failing)
    with pytest.raises(RuntimeError, match="injected"):
        expire(s, U, MemoryConfig(), now=NOW)
    monkeypatch.undo()
    assert _row(s, "e1").needs_confirmation is True
    assert _row(s, "e2").needs_confirmation is False


def test_an_unrelated_write_refusal_inside_the_transition_still_raises(tmp_path, monkeypatch):
    """research's N4 note: with the 0041 skip inside the transaction, nothing swallows a ValueError from the write
    path (the shipped `except ValueError: if _attested_now: continue` is gone)."""
    s = SqliteStore(str(tmp_path / "refuse.db"))
    s.add_edge(_edge("e1", S.Volatility.SLOW, 0.6))

    def refuse(_edge):
        raise ValueError("refused for an unrelated reason")
    monkeypatch.setattr(s, "_upsert_edge_row", refuse)
    with pytest.raises(ValueError, match="unrelated"):
        expire(s, U, MemoryConfig(), now=NOW)


# ---- N4e: a valid policy never makes B raise ---------------------------------------------------------------------------

@pytest.mark.parametrize("factor", [0.0, 0.25, 0.5, 1.0, 0, 1])
@pytest.mark.parametrize("floor", [0.0, 0.3, 1.0, 0, 1])
def test_valid_decay_never_raises(tmp_path, decay_mapped, factor, floor):
    """N4e: every factor/floor pair on the grid (both boundaries, int forms included) over confidences {0, 0.3, 0.9,
    1.0}: expire() completes and every stored row reads back, in range."""
    s = SqliteStore(str(tmp_path / "n4e.db"))
    for i, c in enumerate((0.0, 0.3, 0.9, 1.0)):
        s.add_edge(_edge(f"e{i}", S.Volatility.SLOW, c))
    _expire_valid(s, Duck(factor, floor), now=NOW)
    rows = s.edges(U, active_only=False)
    assert len(rows) == 4 and all(0.0 <= e.provenance.confidence <= 1.0 for e in rows)


# ---- N4: no maintenance operation raises confidence (property) --------------------------------------------------------

@pytest.mark.parametrize("seed", range(12))
def test_no_maintenance_op_raises_confidence(tmp_path, decay_mapped, seed):
    """N4 (confidence half): a random sequence of expire() runs over edges of every volatility, DECAY mapped, under
    random VALID policies: every edge's confidence after each run is <= before, and in [0, 1]. (Consolidation, the
    other maintenance writer of confidence, is held by tests/test_lifecycle.py::
    test_consolidation_output_is_no_stronger_than_its_weakest_input.)"""
    rnd = random.Random(seed)
    s = SqliteStore(str(tmp_path / "n4.db"))
    vols = list(S.Volatility)
    for i in range(10):
        s.add_edge(_edge(f"e{i}", rnd.choice(vols), rnd.choice([0.0, 1.0, rnd.random()]),
                         observed=NOW - dt.timedelta(days=rnd.choice([0, 3, 30, 200, 1000]))))
    for _ in range(rnd.randint(1, 6)):
        before = {e.id: e.provenance.confidence for e in s.edges(U, active_only=False)}
        factor = rnd.choice([0.0, 1.0, rnd.random()])
        floor = rnd.choice([0.0, 1.0, rnd.random()])
        _expire_valid(s, Duck(factor, floor), now=NOW + dt.timedelta(days=rnd.randint(0, 400)))
        for e in s.edges(U, active_only=False):
            assert 0.0 <= e.provenance.confidence <= before[e.id], (e.id, before[e.id], e.provenance.confidence)


# ---- N4i: DECAY keeps the shipped result (R2-02) ----------------------------------------------------------------------

# (factor, floor, confidence, already flagged) -> (decayed count, active, stored confidence, flagged); the table read
# from the shipped expire() at c1c9ecf (§6 N4i)
N4I = {
    "retained":            ((0.5, 0.3, 0.9, False), (0, True, 0.45, False)),
    "below the floor":     ((0.5, 0.5, 0.9, False), (1, False, 0.9, False)),
    "exactly at the floor": ((0.5, 0.3, 0.6, False), (0, True, 0.3, False)),
    "factor 1.0":          ((1.0, 0.3, 0.9, False), (0, True, 0.9, False)),
    "factor 0, floor 0":   ((0.0, 0.0, 0.9, False), (0, True, 0.0, False)),
    "factor 0, floor 0.3": ((0.0, 0.3, 0.9, False), (1, False, 0.9, False)),
    "already flagged":     ((0.5, 0.3, 0.9, True), (0, True, 0.45, True)),
}


@pytest.mark.parametrize("case", list(N4I))
def test_decay_keeps_the_shipped_result(tmp_path, decay_mapped, case):
    """N4i: the returned counts and the stored edge equal the shipped table, case by case; a retiring case also writes
    its journal row (kind `invalidated`, reason `decayed`) and, as the shipped code does, KEEPS the compiled wiki:
    0004 W3 retains it on `decayed` (schema.WIKI_RETAINING_REASONS), the shipped meaning R2-02 binds. (§6 N4i's text
    says "the wiki drop"; sent to research as a spec-text finding, 2026-11-02.)"""
    (factor, floor, conf, flagged), (n_decayed, active, stored, still_flagged) = N4I[case]
    s = SqliteStore(str(tmp_path / "n4i.db"))
    s.add_edge(_edge("e", S.Volatility.SLOW, conf, flagged=flagged))
    s.set_wiki(U, "cached", s.store_version(U))
    r = _expire_valid(s, Duck(factor, floor), now=NOW)
    e = _row(s, "e")
    assert r == {"lapsed": 0, "decayed": n_decayed, "flagged_for_confirmation": 0}, r
    assert (e.active, round(e.provenance.confidence, 9), e.needs_confirmation) == (active, stored, still_flagged)
    if not active:
        kinds = [(ev.kind, ev.reason) for ev in s.edge_events(U) if ev.edge_id == "e"]
        assert ("invalidated", "decayed") in kinds, kinds
        assert e.invalidation_reason == "decayed"
        assert s.get_wiki(U) is not None, "0004 W3: a decayed retirement retains the wiki (the shipped meaning)"


def test_lapse_and_confirm_keep_their_shipped_counts(tmp_path):
    """The two shipped behaviours, counted as before (§2's `expire()` return row): a LAPSE invalidation counts in
    `lapsed`; a newly set flag in `flagged_for_confirmation`; an edge already flagged is not re-counted."""
    s = SqliteStore(str(tmp_path / "shipped.db"))
    s.add_edge(_edge("t", S.Volatility.TRANSIENT, 0.9))
    s.add_edge(_edge("d", S.Volatility.SLOW, 0.9))
    s.add_edge(_edge("f", S.Volatility.SLOW, 0.9, flagged=True))
    s.add_edge(_edge("p", S.Volatility.PERMANENT, 0.9))
    assert expire(s, U, MemoryConfig(), now=NOW) == {"lapsed": 1, "decayed": 0, "flagged_for_confirmation": 1}
    assert (_row(s, "t").active, _row(s, "d").needs_confirmation, _row(s, "p").active) == (False, True, True)


# ---- N4h: decided from the row committed when the transition runs ---------------------------------------------------

def _overlap(tmp_path, name, vol, conf, b_ops, cfg=None, serial=False):
    """A runs expire() and pauses after its LISTING, before any transition; B (a second real connection) commits;
    A resumes. Deterministic (events), not a timing race. `serial` runs B, then A, with no overlap."""
    db = tmp_path / f"{name}.db"
    A, B = _mem(db, **(cfg or {})), _mem(db, **(cfg or {}))
    A.store.add_edge(_edge("e-1", vol, conf))
    if serial:
        for op in b_ops:
            op(B)
        out = expire(A.store, U, A.config)
        return out, _row(B.store, "e-1")
    read, go, out = threading.Event(), threading.Event(), {}
    real = A.store.edges

    def paused(*a, **k):
        r = list(real(*a, **k))
        read.set()
        assert go.wait(10)
        return r
    A.store.edges = paused
    t = threading.Thread(target=lambda: out.setdefault("A", expire(A.store, U, A.config)))
    t.start()
    assert read.wait(10)
    for op in b_ops:
        op(B)
    go.set()
    t.join(10)
    assert not t.is_alive()
    A.store.edges = real
    return out.get("A"), _row(B.store, "e-1")


def _state(e):
    return (e.active, round(e.provenance.confidence, 9), e.needs_confirmation, e.provenance.observed_at.date())


CASES = {
    # name: (volatility, confidence, B's operations, policy, decay mapped)
    "confirm": (S.Volatility.SLOW, 0.6, lambda B: [B.confirm(U, "e-1")], None, False),
    "confirm95": (S.Volatility.SLOW, 0.95, lambda B: [B.confirm(U, "e-1")], None, False),
    "lapse": (S.Volatility.TRANSIENT, 0.6, lambda B: [B.confirm(U, "e-1")], None, False),
    "decay": (S.Volatility.SLOW, 0.9, lambda B: [expire(B.store, U, B.config), expire(B.store, U, B.config)],
              {"decay_factor": 0.5, "confidence_floor": 0.0}, True),
}


@pytest.mark.parametrize("name", list(CASES))
def test_expiry_is_decided_from_the_current_row(tmp_path, monkeypatch, name):
    """N4h: for §2c-ii row 11's four cases, B's committed state is KEPT and A applies only what is due on it, which is
    exactly the serial control's state (B, then A): `confirm`/`confirm95`/`lapse` keep the confirmation (nothing is
    due after it), and `decay` lands on 0.1125 (A decays B's 0.225), never A's stale 0.45 (H-01)."""
    vol, conf, ops, cfg, mapped = CASES[name]
    if mapped:
        monkeypatch.setitem(S.DEFAULT_EXPIRY, S.Volatility.SLOW, S.ExpiryBehavior.DECAY)
    (tmp_path / "o").mkdir()
    (tmp_path / "s").mkdir()
    _, overlapped = _overlap(tmp_path / "o", name, vol, conf, [ops], cfg)
    _, serial = _overlap(tmp_path / "s", name, vol, conf, [ops], cfg, serial=True)
    assert _state(overlapped) == _state(serial), (_state(overlapped), _state(serial))
    if name == "decay":
        assert _state(overlapped)[1] == 0.1125
    else:
        assert overlapped.active and not overlapped.needs_confirmation and overlapped.provenance.confidence >= 0.9


def test_a_legacy_serialisation_is_processed_not_skipped(tmp_path):
    """N4h's legacy-bytes control: a row stored with valid but NON-CANONICAL json (keys reordered, as an earlier
    release's serialiser might have written it) is decided and written like any other."""
    s = SqliteStore(str(tmp_path / "legacy.db"))
    s.add_edge(_edge("e", S.Volatility.SLOW, 0.6))
    raw = json.loads(s._conn.execute("SELECT json FROM edges WHERE id='e'").fetchone()[0])
    reordered = json.dumps(dict(reversed(list(raw.items()))))
    assert reordered != json.dumps(raw)
    s._conn.execute("UPDATE edges SET json=? WHERE id='e'", (reordered,))
    s._conn.commit()
    assert expire(s, U, MemoryConfig(), now=NOW)["flagged_for_confirmation"] == 1
    assert _row(s, "e").needs_confirmation is True


def test_a_redaction_after_the_listing_is_seen_inside_the_transition(tmp_path):
    """§4D step 1: the 0041 skip moved INSIDE the transaction — a redaction attested after expire()'s listing (here:
    before the transition runs) makes the transition write nothing and count nothing, and the run completes."""
    m = _mem(tmp_path / "redact.db")
    m.store.add_edge(_edge("e-1", S.Volatility.SLOW, 0.6))
    real = m.store.edges

    def list_then_redact(*a, **k):
        r = list(real(*a, **k))
        m.redact(U, edge_id="e-1", reason="subject_request")
        return r
    m.store.edges = list_then_redact
    try:
        out = expire(m.store, U, m.config, now=NOW)
    except ValueError as ex:
        raise AssertionError(f"a redaction after the listing made expire() raise: {ex}")
    finally:
        m.store.edges = real
    assert out == {"lapsed": 0, "decayed": 0, "flagged_for_confirmation": 0}


def test_a_delegating_wrapper_store_is_not_refused(tmp_path):
    """A host's wrapper that DELEGATES to a real store through `__getattr__` (tests/test_0021_maintain_scope.py's fault
    wrappers have this shape) reaches the inner store's transition, so expire() runs through it; the refusal is for a
    store whose class resolves to the Store base's default, or that has no transition at all."""
    inner = SqliteStore(str(tmp_path / "wrapped.db"))
    inner.add_edge(_edge("e", S.Volatility.TRANSIENT, 0.9))

    class Wrapper:
        def __init__(self, s):
            self._s = s

        def __getattr__(self, name):
            return getattr(self._s, name)
    try:
        out = expire(Wrapper(inner), U, MemoryConfig(), now=NOW)
    except NotImplementedError as ex:
        raise AssertionError(f"a delegating wrapper was refused: {ex}")
    assert out["lapsed"] == 1 and not _row(inner, "e").active


def test_a_wrapper_around_a_store_without_the_transition_refuses_at_entry(tmp_path):
    """research's case (2026-11-02): a delegating wrapper around a Store subclass that does NOT override the
    transition refuses at ENTRY, on an empty store, before any listing — the capability is asked of the method the
    wrapper resolves, not of the wrapper's class (which a class lookup finds nothing on, and lets through)."""
    from veracium.store.base import Store
    reads = []

    class Custom(SqliteStore):
        expiry_transition = Store.expiry_transition

        def edges(self, *a, **k):
            reads.append(1)
            return super().edges(*a, **k)

    class Wrapper:
        def __init__(self, s):
            self._s = s

        def __getattr__(self, name):
            return getattr(self._s, name)
    _refuses(NotImplementedError, lambda: expire(Wrapper(Custom(str(tmp_path / "w.db"))), U, MemoryConfig(), now=NOW),
             match="expiry_transition")
    assert reads == [], "the listing was read before the refusal"


def test_a_store_without_the_transition_refuses_at_entry(tmp_path):
    """The owner's ruling (2026-11-02, "Refuse, name it"): a Store subclass without `expiry_transition` refuses
    before any edge is read, naming the method; it never falls back to the listing-then-write path."""
    from veracium.store.base import Store
    read = []

    class Custom(SqliteStore):
        expiry_transition = Store.expiry_transition

        def edges(self, *a, **k):
            read.append(1)
            return super().edges(*a, **k)
    s = Custom(str(tmp_path / "custom.db"))
    s.add_edge(_edge("e", S.Volatility.TRANSIENT, 0.9))
    with pytest.raises(NotImplementedError, match="expiry_transition"):
        expire(s, U, MemoryConfig(), now=NOW)
    assert read == [] and _row(s, "e").active
    with pytest.raises(NotImplementedError, match="expiry_transition"):
        Store.expiry_transition(s, U, "e", now=NOW, lifetimes={}, behaviors={}, decay_factor=0.5, confidence_floor=0.3)


# ---- N4f: no edge write bypasses the validating serialiser; the serialiser refuses -----------------------------------

def test_the_store_refuses_an_out_of_bound_edge(tmp_path):
    """N4f (b): an edge whose NESTED Provenance was built with `model_construct` (no validation, as a buggy path
    would) carrying confidence 1.8 is refused by add_edge, and the table is unchanged; NaN likewise."""
    s = SqliteStore(str(tmp_path / "n4f.db"))
    s.add_edge(_edge("ok", S.Volatility.SLOW, 0.5))
    before = _snapshot(tmp_path / "n4f.db")
    for bad in (1.8, float("nan"), -0.2):
        good = _edge("bad", S.Volatility.SLOW, 0.5)
        good.provenance = Provenance.model_construct(**{**dict(good.provenance), "confidence": bad})
        _refuses(ValueError, lambda: s.add_edge(good))
        assert _snapshot(tmp_path / "n4f.db") == before
    one = _edge("ok2", S.Volatility.SLOW, 0.5)
    assert SQ._validated_edge_json(one) == one.model_dump_json(), "N1: the helper returns the edge's own bytes"


SQLITE = ROOT / "src" / "veracium" / "store" / "sqlite.py"
HELPER = "_validated_edge_json"
# every edges write form in sqlite.py, normalised, -> the position of its json parameter (None: no json column)
RECOGNISED = {
    "insert or replace into edges(id,user_id,subject,relation,object,active,quarantined,json) values(?,?,?,?,?,?,?,?)": 7,
    "update edges set json=? where id=?": 0,
    "update edges set active=0, json=? where id=?": 0,
    "update edges set active=1, json=? where id=?": 0,
    "update edges set json=?, subject=?, relation=?, object=?, quarantined=? where id=?": 0,
}
NON_WRITE_ATTRS = {"commit", "rollback", "close", "in_transaction"}   # resolved: none of them runs SQL text
# THE BINDING INVENTORY: every reference to the connection the gate cannot resolve from the statement itself, with
# its reason. Keyed (function, form). Its scope is store/sqlite.py ONLY: five other modules reach `store._conn`
# (doctor, current_state, data_migration, migration, revocation), and the rglob token tripwire (N4c iv,
# test_every_tripwire_hit_on_this_tree_is_classified) is what covers them — the receiver rule is not package-wide.
INVENTORY = {
    ("__init__", "arg:open_versioned"): "the 0007/0013 versioned open (DDL, the stamp, migrations); any edges write it "
                                        "makes is outside this AST (sqlite.py only) and is the tripwire's",
    ("_journal_edge_write", "arg:next_txn"): "store.edge_events: the 0029 journal's allocation read",
    ("_journal_edge_write", "arg:mint_recorded_at"): "store.edge_events: the journal's clock mint",
    ("_journal_edge_write", "arg:next_seq"): "store.edge_events: the journal's sequence read",
    ("_journal_edge_write", "arg:append_event"): "store.edge_events: appends to edge_event, never to edges",
    ("standing_revocations", "arg:_standing"): "store.revocation.standing_revocations: a SELECT on source_revocations",
    ("_redact_in_txn", "arg:_redact_revocation_reasons"): "store.revocation: UPDATE source_revocations' reason column",
    ("_redact_in_txn", "arg:_revocation_reason_marked"): "store.revocation: a SELECT on source_revocations",
    ("forget_user", "sql:delete from {table}"): "the erasure loop over _ERASE_TABLES: a DELETE stores no value",
    ("commit_outcome_import_plan", "sql:insert into {act table}"): "an act row into one of _ACT_COLUMNS' tables, "
                                                                   "which are not edges (asserted below)",
}
# the modules the inventory's callees live in, and the edges-write text none of them may hold
CALLEE_MODULES = {"next_txn": "store/edge_events.py", "mint_recorded_at": "store/edge_events.py",
                  "next_seq": "store/edge_events.py", "append_event": "store/edge_events.py",
                  "_standing": "store/revocation.py", "_redact_revocation_reasons": "store/revocation.py",
                  "_revocation_reason_marked": "store/revocation.py"}


def _literal(node, assigns):
    """The SQL text of a statement node, or None: a str constant; a + of resolvable parts; a JoinedStr's static text
    with `{…}` for each formatted value; a `.format(…)` on a literal; a Name every assignment of which in the function
    is resolvable (all the same leading verb). Anything else is unresolved."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a = _literal(node.left, assigns)
        return None if a is None else a + "{…}"
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else "{…}" for v in node.values)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format":
        return _literal(node.func.value, assigns)
    if isinstance(node, ast.Name) and assigns.get(node.id):
        heads = [v for kind, v in assigns[node.id] if kind == "set"]
        tails = [v for kind, v in assigns[node.id] if kind == "aug"]
        texts = [_literal(v, {}) for v in heads] + [_literal(v, {}) for v in tails]
        if not heads or any(x is None for x in texts):
            return None
        tail = " {…}" if tails else ""
        return ";".join(_literal(v, {}) + tail for v in heads)
    return None


def _gate(source: str) -> list:
    """N4f (a) over sqlite.py's source: the problems, or []."""
    tree = ast.parse(source)
    parent = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}

    def enclosing_fn(n):
        while n in parent:
            n = parent[n]
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return n
        return None
    assigns_by_fn = {}
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = {}
            for n in ast.walk(fn):
                if isinstance(n, ast.Assign):
                    for t in n.targets:
                        if isinstance(t, ast.Name):
                            a.setdefault(t.id, []).append(("set", n.value))
                elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
                    a.setdefault(n.target.id, []).append(("aug", n.value))
            assigns_by_fn[fn] = a
    bad, used = [], set()
    is_conn = lambda n: (isinstance(n, ast.Attribute) and n.attr == "_conn" and isinstance(n.value, ast.Name)
                         and n.value.id == "self")
    for n in ast.walk(tree):
        line = getattr(n, "lineno", "?")
        if isinstance(n, ast.Name) and n.id in ("getattr", "setattr", "delattr", "vars", "eval", "exec"):
            bad.append(f"L{line}: dynamic access `{n.id}` in the store module")
        if isinstance(n, ast.Attribute) and n.attr in ("__dict__", "__getattribute__", "__setattr__"):
            bad.append(f"L{line}: dynamic access `{n.attr}` in the store module")
        if (isinstance(n, ast.Attribute) and n.attr == "connect" and isinstance(n.value, ast.Name)
                and n.value.id == "sqlite3"):
            fn = enclosing_fn(n)
            asg = parent.get(parent.get(n))
            if not (fn is not None and fn.name == "__init__" and isinstance(asg, ast.Assign)
                    and any(is_conn(t) for t in asg.targets)):
                bad.append(f"L{line}: a second sqlite3 connection")
        if isinstance(n, ast.Attribute) and n.attr == "_conn" and not is_conn(n):
            bad.append(f"L{line}: the connection reached through something other than `self`")
        if not is_conn(n):
            continue
        fn = enclosing_fn(n)
        fname = fn.name if fn else "<module>"
        p = parent[n]
        if isinstance(p, ast.Assign) and n in p.targets:
            if fname != "__init__":
                bad.append(f"L{line}: the connection rebound in {fname}")
            continue
        if isinstance(p, ast.Attribute) and p.value is n:
            call = parent.get(p)
            called = isinstance(call, ast.Call) and call.func is p
            if p.attr in NON_WRITE_ATTRS and (called or p.attr == "in_transaction"):
                continue
            if p.attr != "execute" or not called:
                bad.append(f"L{line}: `self._conn.{p.attr}` in a form the gate does not resolve ({fname})")
                continue
            sql = _literal(call.args[0], assigns_by_fn.get(fn, {})) if call.args else None
            if sql is None:
                bad.append(f"L{line}: an execute whose SQL the gate cannot read ({fname})")
                continue
            for stmt in sql.split(";"):
                norm = " ".join(stmt.lower().split())
                verb = norm.split(" ", 1)[0] if norm else ""
                READS = ("select", "pragma", "with", "begin", "commit", "rollback", "savepoint", "release", "end", "")
                if verb in READS or not re.match(r"(insert|update|replace|delete)\b", norm):
                    if verb not in READS:
                        bad.append(f"L{line}: a statement of unknown verb ({fname}): {norm[:60]}")
                    continue
                m = re.match(r"(?:insert(?: or replace)? into|replace into|update|delete from)\s+([\w{}…]+)", norm)
                table = m.group(1) if m else None
                if table == "{…}":
                    key = {"forget_user": "sql:delete from {table}",
                           "commit_outcome_import_plan": "sql:insert into {act table}"}.get(fname)
                    if key is None or (fname, key) not in INVENTORY:
                        bad.append(f"L{line}: a write to a formatted table not in the inventory ({fname})")
                    used.add((fname, key))
                    continue
                if table is None:
                    bad.append(f"L{line}: a write whose table the gate cannot read ({fname}): {norm[:60]}")
                    continue
                if table != "edges":
                    continue
                if norm not in RECOGNISED:
                    bad.append(f"L{line}: an edges write of an unrecognised form ({fname}): {norm[:70]}")
                    continue
                params = call.args[1] if len(call.args) > 1 else None
                k = RECOGNISED[norm]
                v = params.elts[k] if isinstance(params, ast.Tuple) and len(params.elts) > k else None
                ok = isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == HELPER
                if isinstance(v, ast.Name):
                    vals = assigns_by_fn.get(fn, {}).get(v.id, [])
                    ok = bool(vals) and all(kind == "set" and isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                                            and x.func.id == HELPER for kind, x in vals)
                if not ok:
                    bad.append(f"L{line}: the edges json is not bound to {HELPER}(...)'s return value ({fname})")
            continue
        if isinstance(p, ast.Call) and n in p.args:
            callee = ast.unparse(p.func)
            if (fname, f"arg:{callee}") in INVENTORY:
                used.add((fname, f"arg:{callee}"))
                continue
            bad.append(f"L{line}: the connection passed to `{callee}`, not in the inventory ({fname})")
            continue
        bad.append(f"L{line}: the connection reached in a form the gate does not resolve ({fname})")
    stale = set(INVENTORY) - used
    if stale:
        bad.append(f"inventory entries no longer reached (stale): {sorted(stale)}")
    return bad


def test_every_edge_write_goes_through_the_validating_serialiser():
    """N4f (a), R2-01's receiver rule over store/sqlite.py: every reference to `self._conn` is a direct `execute`
    whose SQL the gate reads (a literal, a literal's static text, or a name bound only to literals), one of the
    non-write connection attributes, the one assignment in `__init__`, or a binding-inventory entry with its reason;
    every write of the edges table's `json` binds `_validated_edge_json(...)`'s return value (directly, or a name bound
    ONLY to it in that function); any other form fails, whatever the method is called (an alias, `executemany`, a
    cursor, `getattr`, the unbound method, the connection passed on, `__dict__`, a second connection). The inventory
    is checked both ways: an entry nothing reaches is stale."""
    assert _gate(SQLITE.read_text()) == []
    # the gate SAW the seven writers (a gate that recognises nothing passes everything): the definition plus 7 calls
    src = SQLITE.read_text()
    norms = [" ".join(m.lower().split()) for m in re.findall(r'"((?:INSERT OR REPLACE INTO|UPDATE) edges[^"]*)"', src)]
    assert src.count(f"{HELPER}(") == 8 and len(norms) == 7, (src.count(f"{HELPER}("), norms)


def test_the_inventorys_reasons_hold():
    """The inventory's reasons are claims about other code, checked: the act tables are not edges, and no callee
    module the inventory names holds an edges write."""
    assert "edges" not in SqliteStore._ACT_COLUMNS
    for mod in sorted(set(CALLEE_MODULES.values())):
        text = (ROOT / "src" / "veracium" / mod).read_text()
        assert not re.search(r"(?i)\b(insert(\s+or\s+replace)?\s+into|update)\s+edges\b", text), mod


# the R2-01 forms (and the per-writer bypass and ignored-return rows) the gate must refuse: each an edit of sqlite.py's
# text whose anchor must occur exactly once
_W = '            new_json = _validated_edge_json(edge)\n            self._conn.execute(\n                "INSERT OR REPLACE INTO edges'
GATE_MUTANTS = {
    "executemany": ('self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?",',
                    'self._conn.executemany("UPDATE edges SET active=0, json=? WHERE id=?",'),
    "an alias of execute": ('        self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?",',
                            '        ex = self._conn.execute\n        ex("UPDATE edges SET active=0, json=? WHERE id=?",'),
    "getattr": ('self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?",',
                'getattr(self._conn, "execute")("UPDATE edges SET active=0, json=? WHERE id=?",'),
    "a cursor": ('self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?",',
                 'self._conn.cursor().execute("UPDATE edges SET active=0, json=? WHERE id=?",'),
    "SQL held in a variable": ('        self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?",',
                               '        q = edge.relation and "UPDATE edges SET active=0, json=? WHERE id=?"\n'
                               '        self._conn.execute(q,'),
    "parameters held in a variable": ('        self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?",\n'
                                      '                           (new_json, edge_id))',
                                      '        args = (new_json, edge_id)\n'
                                      '        self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?", args)'),
    "the unbound Connection.execute": ('self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?",',
                                       'sqlite3.Connection.execute(self._conn, "UPDATE edges SET active=0, json=? WHERE id=?",'),
    "a second connection": ('self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?",',
                            'sqlite3.connect(self._path).execute("UPDATE edges SET active=0, json=? WHERE id=?",'),
    "the instance __dict__": ('self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?",',
                              'self.__dict__["_conn"].execute("UPDATE edges SET active=0, json=? WHERE id=?",'),
    "a writer bypasses the helper": ('        edge.invalidation_reason = reason\n        new_json = _validated_edge_json(edge)\n',
                                     '        edge.invalidation_reason = reason\n        new_json = edge.model_dump_json()\n'),
    "the helper called, its return ignored": (
        '        edge.invalidation_reason = reason\n        new_json = _validated_edge_json(edge)\n',
        '        edge.invalidation_reason = reason\n        _validated_edge_json(edge)\n        new_json = edge.model_dump_json()\n'),
    "an inventory entry gone stale": ('        append_event(self._conn, user_id=user_id,',
                                      '        append_event(None, user_id=user_id,'),
}


@pytest.mark.parametrize("name", list(GATE_MUTANTS))
def test_the_gate_refuses_each_unresolved_form(name):
    """The gate's own matrix: each form, planted on a copy of sqlite.py's text, is refused (the honest text passes,
    above). The per-writer bypass row runs once per writer in the next test."""
    old, new = GATE_MUTANTS[name]
    src = SQLITE.read_text()
    assert src.count(old) == 1, f"{name}: the anchor occurs {src.count(old)} times — re-anchor it"
    assert _gate(src.replace(old, new)), f"{name}: the gate passed it"


def test_each_writer_bypassing_the_helper_is_refused():
    """§6's 'for each of the declared edge writers: that writer bypasses the helper' row, one planted copy per writer."""
    src = SQLITE.read_text()
    sites = [m.start() for m in re.finditer(re.escape(f"{HELPER}(edge)") + "|" + re.escape(f"{HELPER}(model_after)"),
                                            src)]
    assert len(sites) == 7, len(sites)
    for at in sites:
        call_end = src.index(")", at) + 1
        arg = src[at + len(HELPER) + 1:call_end - 1]
        mutated = src[:at] + f"{arg}.model_dump_json()" + src[call_end:]
        assert _gate(mutated), f"the bypass at offset {at} passed"


# ---- N4c (i–iii): declared bounds hold on construction, assignment, and every census-visible writer ------------------

def _bounded_fields():
    import annotated_types as at
    out = []
    for name in dir(S):
        cls = getattr(S, name)
        if isinstance(cls, type) and hasattr(cls, "model_fields") and cls.__module__ == S.__name__:
            for f, info in cls.model_fields.items():
                ms = [m for m in info.metadata if isinstance(m, (at.Ge, at.Le, at.Gt, at.Lt))]
                if ms:
                    out.append((cls, f, ms))
    return out


# the census's confidence writers on this tree (file, the key's expression) -> the reason each stays in range
DECLARED = {
    ("src/veracium/graph.py", "max(incoming.provenance.confidence, prior.provenance.confidence)"):
        "in range by its inputs: the maximum of two stored, validated confidences",
    ("src/veracium/store/sqlite.py", "float(values['confidence'])"):
        "0022's recompute: a value the sweep folded from stored confidences; and C revalidates the edge it writes",
    ("src/veracium/store/sqlite.py", "min((e.provenance.confidence for e in inputs)) if inputs else base.confidence"):
        "in range by its inputs: the minimum of validated episodes' confidences (an EPISODE, outside C, §4C)",
    ("src/veracium/store/sqlite.py", "max(edge.provenance.confidence, 0.9)"):
        "confirm: the maximum of a stored confidence and 0.9",
}


def test_declared_bounds_hold_on_every_write_path(tmp_path):
    """N4c (i)–(iii), enumerated from the models: every pydantic field in `veracium.schema` carrying Ge/Le/Gt/Lt
    (i) refuses construction past its bound; (ii) refuses assignment (frozen model or validate_assignment); and (iii)
    the AST census of specs/evidence/0048/census_0048.py — every `model_copy(update=…)` writing a bounded field, every
    whole-provenance replacement, nothing UNRESOLVED — equals the declared table, each site with its reason. The
    decayed stamp is no longer a `model_copy`: it is built validated in the store's transition (§4B), so the census
    has four confidence writers, not the five §2c-ii row 8 measured before the change."""
    import subprocess, sys, os
    fields = _bounded_fields()
    assert [(c.__name__, f) for c, f, _ in fields] == [("Provenance", "confidence")], fields
    for cls, f, ms in fields:
        base = Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="x")
        for past in (1.0000001, -0.0000001, float("nan")):
            with pytest.raises(ValueError):
                cls(**{**base.model_dump(), f: past})
        with pytest.raises((ValueError, TypeError, AttributeError)):
            setattr(base, f, 2.0)
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "TMPDIR": str(tmp_path)}
    r = subprocess.run([sys.executable, str(ROOT / "specs/evidence/0048/census_0048.py"), str(ROOT)], cwd=ROOT, env=env,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    sites = re.findall(r"^  (src/veracium/\S+):\d+\s+key at L\d+: (.+)$", r.stdout, re.M)
    assert sorted(sites) == sorted(DECLARED), {"undeclared": sorted(set(sites) - set(DECLARED)),
                                               "declared but gone": sorted(set(DECLARED) - set(sites))}
    assert "UNRESOLVED: 0" in r.stdout and "edge json writers in store/sqlite.py: 7" in r.stdout, r.stdout
    assert "lifecycle.py" not in r.stdout.split("edge json writers")[0], "no unvalidated decay copy remains"


# ---- the round-2 verdict's implementation controls, against the actual store ------------------------------------------

def _shipped_expire(store, user_id, config, now):
    """THE SHIPPED expire() body (91219d0, before §4), kept here as the REFERENCE the implementation must equal when
    nothing overlaps: same counts, same stored state, same journal kinds, same store version, same wiki. (The round-2
    verdict: "Include a small old/new behavior table" and "assert the side effects as well as the edge JSON".)"""
    lapsed = decayed = flagged = 0
    redacted = store.redacted_targets(user_id, "edge")
    for e in store.edges(user_id, active_only=True):
        if e.id in redacted:
            continue
        lifetime = config.volatility_lifetime_days.get(e.volatility)
        if lifetime is None or (now - e.provenance.observed_at).days <= lifetime:
            continue
        behavior = S.DEFAULT_EXPIRY[e.volatility]
        if behavior == S.ExpiryBehavior.LAPSE:
            store.invalidate_edge(e.id, now, "lapsed"); lapsed += 1
        elif behavior == S.ExpiryBehavior.DECAY:
            e.provenance = e.provenance.model_copy(update={"confidence": e.provenance.confidence * config.decay_factor})
            if e.provenance.confidence < config.confidence_floor:
                store.invalidate_edge(e.id, now, "decayed"); decayed += 1
            else:
                store.add_edge(e)
        elif not e.needs_confirmation:
            e.needs_confirmation = True
            store.add_edge(e); flagged += 1
    return {"lapsed": lapsed, "decayed": decayed, "flagged_for_confirmation": flagged}


def _effects(store):
    """Everything a transition can touch, as data: each edge's state, the journal's (edge, kind, reason) rows in order,
    the user's store version, and whether a compiled wiki is cached."""
    edges = {e.id: (e.active, e.invalidation_reason, round(e.provenance.confidence, 9), e.needs_confirmation)
             for e in store.edges(U, active_only=False, include_quarantined=True)}
    journal = [(ev.edge_id, ev.kind, ev.reason) for ev in store.edge_events(U)]
    return edges, journal, store.store_version(U), store.get_wiki(U) is not None


SIDE_CASES = {
    # name: (volatility, confidence, DECAY mapped, policy)
    "lapse": (S.Volatility.TRANSIENT, 0.9, False, (0.5, 0.3)),
    "flag": (S.Volatility.SLOW, 0.9, False, (0.5, 0.3)),
    "decay retained": (S.Volatility.SLOW, 0.9, True, (0.5, 0.3)),
    "decay below the floor": (S.Volatility.SLOW, 0.9, True, (0.5, 0.5)),
    "not due": (S.Volatility.PERMANENT, 0.9, False, (0.5, 0.3)),
}


@pytest.mark.parametrize("case", list(SIDE_CASES))
def test_a_transitions_side_effects_equal_the_shipped_paths(tmp_path, monkeypatch, case):
    """With nothing overlapping, every outcome's side effects equal the shipped path's, measured on twin stores: the
    returned counts, each edge's stored state, the journal rows (kind and reason), the user's store version (one bump
    per write) and the compiled wiki (kept on lapsed/decayed, 0004 W3). The old/new table for R2-02's two cases is
    the `decay retained` and `decay below the floor` rows."""
    vol, conf, mapped, (factor, floor) = SIDE_CASES[case]
    if mapped:
        monkeypatch.setitem(S.DEFAULT_EXPIRY, S.Volatility.SLOW, S.ExpiryBehavior.DECAY)
    results = []
    for arm, run in (("shipped", _shipped_expire), ("0048", lambda s, u, c, now: expire(s, u, c, now=now))):
        s = SqliteStore(str(tmp_path / f"{arm}.db"))
        s.add_edge(_edge("e", vol, conf))
        s.set_wiki(U, "cached", s.store_version(U))
        before = s.store_version(U)
        out = run(s, U, Duck(factor, floor), NOW)
        edges, journal, version, wiki = _effects(s)
        results.append((out, edges, journal, version - before, wiki))
    assert results[0] == results[1], {"shipped": results[0], "0048": results[1]}


def _between(store, change, seen):
    """Wrap the store's listing so `change(store)` runs after it, before any transition; `seen["version"]` is the
    user's store version once the change has committed (so a transition's own bump can be told from the change's)."""
    real = store.edges

    def listing(*a, **k):
        r = list(real(*a, **k))
        change(store)
        seen["version"] = store.store_version(U)
        return r
    store.edges = listing
    return real


BETWEEN = {
    # name: (the change made between listing and transition, expected counts, expected (active, reason, flagged))
    "deleted": (lambda s: s.forget_user(U), {"lapsed": 0, "decayed": 0, "flagged_for_confirmation": 0}, None),
    "invalidated": (lambda s: s.invalidate_edge("e", NOW, "disputed"),
                    {"lapsed": 0, "decayed": 0, "flagged_for_confirmation": 0}, (False, "disputed", False)),
    "made permanent": ("permanent", {"lapsed": 0, "decayed": 0, "flagged_for_confirmation": 0}, (True, None, False)),
    "made transient": ("transient", {"lapsed": 1, "decayed": 0, "flagged_for_confirmation": 0}, (False, "lapsed", False)),
}


@pytest.mark.parametrize("name", list(BETWEEN))
def test_a_change_between_listing_and_transition_is_decided_on_the_current_row(tmp_path, name):
    """The round-2 verdict's no-op and current-volatility controls, on the actual store: a SLOW (CONFIRM) edge, listed
    as due, is DELETED, INVALIDATED or made PERMANENT before its transition runs → no write, no count; made TRANSIENT →
    LAPSE applies from the current row (never the listed CONFIRM)."""
    s = SqliteStore(str(tmp_path / "between.db"))
    s.add_edge(_edge("e", S.Volatility.SLOW, 0.9))
    change, counts, state = BETWEEN[name]
    real = s.edges
    if isinstance(change, str):
        vol = S.Volatility.PERMANENT if change == "permanent" else S.Volatility.TRANSIENT

        def change(st, vol=vol):
            (e,) = [x for x in real(U, active_only=False) if x.id == "e"]
            st.add_edge(e.model_copy(update={"volatility": vol}))
    seen = {}
    _between(s, change, seen)
    out = expire(s, U, MemoryConfig(), now=NOW)
    s.edges = real
    assert out == counts, out
    rows = [e for e in s.edges(U, active_only=False, include_quarantined=True) if e.id == "e"]
    if state is None:
        assert rows == []
    else:
        (e,) = rows
        assert (e.active, e.invalidation_reason, e.needs_confirmation) == state
    if counts == {"lapsed": 0, "decayed": 0, "flagged_for_confirmation": 0}:
        journal_after_change = [ev for ev in s.edge_events(U) if ev.reason in ("lapsed", "decayed")]
        assert journal_after_change == [], "a no-op transition journalled a retirement"
        assert s.store_version(U) == seen["version"], "a transition that wrote nothing moved the store version"
    else:
        assert s.store_version(U) == seen["version"] + 1, "a writing transition bumps exactly once"


def test_a_policy_changed_during_the_first_transition_does_not_reach_the_second(tmp_path, decay_mapped):
    """The verdict's configuration control: all three policy values are changed while the FIRST transition runs; the
    second edge still decays under the policy captured at entry."""
    s = SqliteStore(str(tmp_path / "policy.db"))
    s.add_edge(_edge("a", S.Volatility.SLOW, 0.8))
    s.add_edge(_edge("b", S.Volatility.SLOW, 0.8))
    cfg = MemoryConfig()
    real = s.expiry_transition
    calls = []

    def first_changes_the_policy(*a, **k):
        out = real(*a, **k)
        if not calls:
            cfg.decay_factor, cfg.confidence_floor = 1.0, 0.9
            cfg.volatility_lifetime_days[S.Volatility.SLOW] = None
        calls.append(out)
        return out
    s.expiry_transition = first_changes_the_policy
    out = _expire_valid(s, cfg, now=NOW)
    assert calls == ["decay-retained", "decay-retained"] and out["decayed"] == 0, (calls, out)
    assert [round(e.provenance.confidence, 9) for e in s.edges(U)] == [0.4, 0.4]


def test_a_failing_transition_rolls_back_its_journal_and_its_bump(tmp_path, monkeypatch):
    """N4d-prefix's side effects: the failing edge leaves no journal row and no store-version bump; the committed one
    keeps both."""
    s = SqliteStore(str(tmp_path / "rollback.db"))
    s.add_edge(_edge("e1", S.Volatility.SLOW, 0.6))
    s.add_edge(_edge("e2", S.Volatility.SLOW, 0.6))
    before_v, before_j = s.store_version(U), len(s.edge_events(U))
    real, calls = s._upsert_edge_row, []

    def failing(edge):
        calls.append(edge.id)
        real(edge)                                   # the write happens, then the transaction is made to fail
        if len(calls) == 2:
            raise RuntimeError("injected store failure after the write")
    monkeypatch.setattr(s, "_upsert_edge_row", failing)
    _refuses(RuntimeError, lambda: expire(s, U, MemoryConfig(), now=NOW))
    monkeypatch.undo()
    assert s.store_version(U) == before_v + 1, "only the committed transition bumps"
    events = s.edge_events(U)[before_j:]
    assert [ev.edge_id for ev in events] == ["e1"], [(ev.edge_id, ev.kind) for ev in events]
    assert _row(s, "e2").needs_confirmation is False


# ---- research's stage-2 mark on 574f130: the transition's own 0003 §4c-ii wiki drop, held by a cell -------------------

def _in_refusal(store, eid, role):
    """A durable refusal record naming `eid` as its PRIOR or its INCOMING edge (0003 §4c-ii: either makes the edge a
    possible member of a live refusal contention); `role` None writes none."""
    if role is None:
        return
    prior, incoming = (eid, "e-other") if role == "prior" else ("e-other", eid)
    at = NOW.isoformat()
    store._conn.execute(
        "INSERT INTO supersession_refusals(refusal_id, user_id, prior_edge_id, incoming_edge_id, relation, "
        "prior_effective, incoming_effective, rule_version, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (f"rf-{eid}-{role}", U, prior, incoming, "works_on", at, at, 1, at))
    store._conn.commit()


RETIRING = {"lapse", "decay below the floor"}


@pytest.mark.parametrize("role", ["prior", "incoming"])
@pytest.mark.parametrize("case", list(SIDE_CASES))
def test_a_transition_of_an_edge_in_a_refusal_has_the_shipped_side_effects(tmp_path, monkeypatch, case, role):
    """The transition repeats invalidate_edge's 0003 §4c-ii rule (research's stage-2 mark: no cell held it): an outcome
    that RETIRES an edge in a refusal (`lapsed`, and `decayed` below the floor) ends a contention and drops the wiki;
    an outcome that keeps the edge (a flag, a retained decay) and an edge not due keep it. Measured on twin stores
    against the shipped path, every effect `_effects` reads, and the wiki also asserted by name, for the edge as the
    refusal's prior and as its incoming side."""
    vol, conf, mapped, (factor, floor) = SIDE_CASES[case]
    if mapped:
        monkeypatch.setitem(S.DEFAULT_EXPIRY, S.Volatility.SLOW, S.ExpiryBehavior.DECAY)
    results = []
    for arm, run in (("shipped", _shipped_expire), ("0048", lambda s, u, c, now: expire(s, u, c, now=now))):
        s = SqliteStore(str(tmp_path / f"{arm}.db"))
        s.add_edge(_edge("e", vol, conf))
        _in_refusal(s, "e", role)
        s.set_wiki(U, "cached", s.store_version(U))
        before = s.store_version(U)
        out = run(s, U, Duck(factor, floor), NOW)
        edges, journal, version, wiki = _effects(s)
        results.append((out, edges, journal, version - before, wiki))
    assert results[1][4] is (case not in RETIRING), (case, role, "wiki cached" if results[1][4] else "wiki dropped")
    assert results[0] == results[1], {"shipped": results[0], "0048": results[1]}


@pytest.mark.parametrize("age", ["exactly the lifetime", "one day past it"])
def test_the_transition_itself_decides_due_ness_at_the_lifetime_boundary(tmp_path, age):
    """A DIRECT call (research's stage-2 survivor: through expire() the listing applies the same skip, so an
    exclusive `<` in the transition is invisible there): an edge exactly `lifetime` days old on its current row is not
    due (None, nothing written, the store version unmoved); one day past it is."""
    lifetimes = dict(MemoryConfig().volatility_lifetime_days)
    days = lifetimes[S.Volatility.TRANSIENT] + (0 if age == "exactly the lifetime" else 1)
    s = SqliteStore(str(tmp_path / "boundary.db"))
    s.add_edge(_edge("e", S.Volatility.TRANSIENT, 0.9, observed=NOW - dt.timedelta(days=days)))
    before = s.store_version(U)
    out = s.expiry_transition(U, "e", now=NOW, lifetimes=lifetimes, behaviors=dict(S.DEFAULT_EXPIRY),
                              decay_factor=0.5, confidence_floor=0.3)
    if age == "exactly the lifetime":
        assert (out, _row(s, "e").active, s.store_version(U)) == (None, True, before), out
    else:
        assert (out, _row(s, "e").active, s.store_version(U)) == ("lapsed", False, before + 1), out
