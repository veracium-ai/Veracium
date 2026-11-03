"""specs/0048 §6: maintenance never raises confidence — the decay bounds, and expiry decided from the current row.

One cell per §6 invariant, named as §6 names it: N4 (property), N4b, N4b′, N4b-assign, N4c (i–iii; iv is
tests/test_0048_evidence.py::test_every_tripwire_hit_on_this_tree_is_classified), N4d, N4d-prefix, N4e, N4f (both
halves), N4g, N4h, N4i. The §6 mutant table runs against these cells through the shared mutation protocol
(specs/evidence/0048/closure/…); the reproductions of the shipped defects these cells invert stay in
tests/test_0048_evidence.py, rewritten to assert the fixed behaviour.
"""
from __future__ import annotations

import ast
import contextlib
import datetime as dt
import hashlib
import json
import math
import pathlib
import random
import re
import sqlite3
import symtable
import sys
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
HUGE = 10 ** 400                       # 0048 round 3, R3-03: beyond float — `math.isfinite` raised OverflowError on it
REJECTED = [1.5, -0.1, float("nan"), float("inf"), float("-inf"), True, False, "0.5", None,
            math.nextafter(1.0, 2.0), math.nextafter(0.0, -1.0), HUGE, -HUGE]


def _vid(v):
    """A cell id: `repr(v)` — every existing id unchanged — except the two integers too long to print."""
    return "+10**400" if v == HUGE else "-10**400" if v == -HUGE else repr(v)
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
@pytest.mark.parametrize("value", REJECTED, ids=_vid)
def test_config_bounds_are_validated(field, value):
    """N4b: both fields refuse >1, <0, NaN, ±inf, a bool, a string, None and the nearest floats beyond each bound,
    with ValueError naming the field. Asserted through `_refuses`, so another exception — round 3's OverflowError on
    ±10**400 (R3-03) — fails by assertion, not as an escaping error."""
    _refuses(ValueError, lambda: MemoryConfig(**{field: value}), match=field)


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
@pytest.mark.parametrize("value", REJECTED, ids=_vid)
def test_config_bounds_hold_on_assignment(field, value):
    """N4b-assign: every value N4b refuses, assigned after construction, refuses, and the field keeps its old value."""
    c = MemoryConfig(decay_factor=0.25, confidence_floor=0.75)
    old = getattr(c, field)
    _refuses(ValueError, lambda: setattr(c, field, value), match=field)
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
                                          (0.5, 2.0), (0.5, -0.5), (0.5, float("nan")),
                                          (HUGE, 0.3), (-HUGE, 0.3), (0.5, HUGE), (0.5, -HUGE)], ids=_vid)
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
    # planted through a SEPARATE connection, as an earlier release's own writer would have stored it — not through this
    # store's connection, which the edges-write tripwire holds to the write method
    with contextlib.closing(sqlite3.connect(str(tmp_path / "legacy.db"))) as other:
        other.execute("UPDATE edges SET json=? WHERE id='e'", (reordered,))
        other.commit()
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
SRC = ROOT / "src"
HELPER = "_validated_edge_json"
METHOD = "_write_edge_row"
DEFERRED = "_DeferredJournal"
JOURNAL = "_journal_edge_write"
GUARDED = (HELPER, METHOD, DEFERRED, JOURNAL)
# 0048 round 4 (R3-02, (a′)): THE edges-json writers — exactly these seven call the write method, and an eighth is a
# reviewed addition (research's stage-1 read, item 5)
WRITERS = {"SqliteStore._upsert_edge_row", "SqliteStore.confirm_edge", "SqliteStore._invalidate_edge_row",
           "SqliteStore._reinstate_edge_row", "SqliteStore._recompute_edge_row",
           "SqliteStore.commit_outcome_import_plan", "SqliteStore._redact_in_txn"}
DEFER_SITE = "SqliteStore._redact_in_txn"
# the CLOSED set of json-writing statements: each is classified by SQLite (below) as an edges INSERT or an UPDATE of
# edges.json, and appears ONLY as the `sql` argument of a write-method call
CLOSED_SQL = {
    "INSERT OR REPLACE INTO edges(id,user_id,subject,relation,object,active,quarantined,json) VALUES(?,?,?,?,?,?,?,?)",
    "UPDATE edges SET json=? WHERE id=?",
    "UPDATE edges SET active=0, json=? WHERE id=?",
    "UPDATE edges SET active=1, json=? WHERE id=?",
    "UPDATE edges SET json=?, subject=?, relation=?, object=?, quarantined=? WHERE id=?",
}
# the frozen bodies (ast.dump without positions, sha256). An edit of either refuses until the digest is re-reviewed.
FROZEN = {METHOD: "a188aa4c5166525dd305b32f88182168968e05ee76276927642cd3bf20482db0", DEFERRED: "f34451a125834bb07a97daad6febc2b328674410162d77f18867ad95c1b7f2d8",
          HELPER: "135b1ee93136505fff98d067a0513316f795866f5d8c6353caade25cb7e2e86a"}   # research's stage 2 (S2-03): the helper's single capture is frozen with the rest
# the dynamic-rebinding routes refused anywhere in sqlite.py (the existing receiver rule's list, plus the module routes)
DYNAMIC_NAMES = {"getattr", "setattr", "delattr", "vars", "eval", "exec", "globals", "locals", "compile", "__import__",
                 "reload"}
DYNAMIC_ATTRS = {"__dict__", "__getattribute__", "__setattr__", "__delattr__", "__class__", "__code__", "reload"}
SQL_CALLS = ("execute", "executemany", "executescript")
# every NON-literal SQL argument of an execute/executemany/executescript in sqlite.py, keyed (qualname, sha256 of the
# expression's ast.dump) -> its static text, the reviewed reading: none writes edges.json except the write method's own
# `sql`, whose callers' literals are the closed set above. A new or changed non-literal site refuses until listed.
NONLITERAL = {
    ('SqliteStore.__init__', 'bc3471530373188da9c30e0ba7e78b2d090076e469d28882db5b0d4698a09d11'):
        (1, "f'PRAGMA busy_timeout = {int(busy_timeout_ms)}'"),
    ('SqliteStore._act_rows_where', 'cc00ad315a59e9575d3a838a0b388ca3610a764627bbbcab38e6e2cd49762c68'):
        (1, 'f"SELECT {\', \'.join(cols)} FROM {table} WHERE {where} ORDER BY id"'),
    ('SqliteStore._attested_by_another_owner', 'eb2ba4c3290426945f64f55e532238461d5d9d44a5ee085a4f52645c927eeb3a'):
        (1, "f'SELECT 1 FROM redactions WHERE target_kind=? AND target_id=? AND user_id<>? AND {_APPLIE"),
    ('SqliteStore._attested_fields', 'b4446c6ae88d8497d190f8f13a92911f81cf0e25a5c0df840c605cad4633adbf'):
        (1, "'SELECT fields FROM redactions WHERE target_kind=? AND target_id=?' + owner_sql + ('' if c"),
    ('SqliteStore._completed_attestation', 'ac4cc2426e52d922b8ed28e84effe37c30011850f64dd4452e744ad48eb150ab'):
        (1, "f'SELECT 1 FROM redactions WHERE user_id=? AND target_kind=? AND target_id=? AND {_APPLIED"),
    ('SqliteStore._confirm_replay', '0fbc4fa0d37e8071b0b5d73055918b6efd7b50a9f1fe40d6c3d3b079ac40816c'):
        (1, "f'SELECT {_COLS} FROM confirmations WHERE id=? AND user_id=?'"),
    ('SqliteStore._id_reserved', '39865061523d15e9bada3bba4afb270b89f19e430857060a14b8a6ae6efac59d'):
        (1, 'f"SELECT {\', \'.join(self._OP_COLS)} FROM consolidation_ops"'),
    ('SqliteStore._load_op', '27d008897c48b8c107eb9520ec542b393921f9e25847f9c51fedc2edfb07af6d'):
        (1, 'f"SELECT {\', \'.join(self._OP_COLS)} FROM consolidation_ops WHERE operation_id=?"'),
    ('SqliteStore._ops_for_user', '2f505a5bb0ddb655bf46fa2ba3b0e786f2db13e1241afb349d9eb3adba2c4902'):
        (1, 'f"SELECT {\', \'.join(self._OP_COLS)} FROM consolidation_ops WHERE user_id=?"'),
    ('SqliteStore._redact_in_txn', '5647332e7211148b9ad5b71a487ab19b4c15e73a38f06d91cb309d3070fb9335'):
        (1, "f'SELECT {self.RECORD_COLS} FROM redactions WHERE id=?'"),
    ('SqliteStore._redaction_record', 'c2aa0c6f503ee77f2f03c4cd951b3745a4d865b0e283306c915c53d5fbb16e05'):
        (1, "f'SELECT {self.RECORD_COLS} FROM redactions WHERE user_id=? AND target_kind=? AND target_i"),
    ('SqliteStore._reply_replay', 'ebab35174f4bd03a186cdddb45260a877bf8623edb94965487f0a205325d2eac'):
        (1, "f'SELECT {self._REPLY_COLS} FROM replies WHERE id=? AND user_id=?'"),
    ('SqliteStore._source_redacted', '29a9ff461c9d9dce95085ee23caaf9cf3005b1caa65b04eaaa213d5db57baa50'):
        (1, 'f"SELECT json FROM episodes WHERE user_id=? AND id IN ({\',\'.join(\'?\' * len(redacted))})"'),
    ('SqliteStore._surviving_derived', '3d9f2c553d81b34f9e0c3dae13bdce09ed08cd1a45de42c73e1c810fdaef9421'):
        (1, "f'SELECT json FROM {table} WHERE id=? AND user_id=?'"),
    ('SqliteStore._write_edge_row', '33f41f90a9a4e29967595c068ca002673821bcb52a03d702ab8f50612eae4c23'):
        (1, 'sql'),
    ('SqliteStore._write_op', 'b0447a31f610348c07a0930af4ffe437a4178a7e2f7cdc52d11e2e5d8753060b'):
        (1, 'f"INSERT OR REPLACE INTO consolidation_ops({\', \'.join(self._OP_COLS)}) VALUES(?,?,?,?,?,?,'),
    ('SqliteStore.acted_edge_ids', 'b4820e17f1261cb74f4605d69f700b538e78998cf1b5c347ff27fcff8c8b43e3'):
        (1, "f'SELECT edge_id FROM confirmations WHERE user_id=? AND edge_id IN ({q}) UNION SELECT edge"),
    ('SqliteStore.active_challenges', '7aae11eef304bd121d26fa2bfe8557573f7bad633b1f0ac29ea9852f41560577'):
        (1, 'f"SELECT {self._REPLY_COLS} FROM replies WHERE user_id=? AND edge_id=? AND kind=\'challenge'),
    ('SqliteStore.add_reply', 'a2022f06b808b3a462a935471067cafc7535c753122add6c146aa954827fa400'):
        (1, 'f"INSERT INTO replies({self._REPLY_COLS}, origin, act_seq) VALUES(?,?,?,?,?,?,?,?,?,?,\'loc'),
    ('SqliteStore.commit_outcome_import_plan', '03827958ec7b7072aefe89448678674c9fc02886e4c4edb1311a054d9d8f4a2d'):
        (1, "f'SELECT user_id, target_kind, target_id, {self.RECORD_COLS} FROM redactions WHERE source_"),
    ('SqliteStore.commit_outcome_import_plan', '25a68e8dfc53a69efba960f40b99fc74fd55430b7a5d678e75be6ac3347e56eb'):
        (1, 'f"INSERT INTO migration_outcome({\', \'.join(self._OUTCOME_COLUMNS)}) VALUES({\',\'.join(\'?\' *'),
    ('SqliteStore.commit_outcome_import_plan', '70905b22342c93513fc74ea1d16e4f11233b00789a3dd9f73bc874dac57eebc9'):
        (2, "f'SELECT user_id, json FROM {tbl} WHERE id=?'"),
    ('SqliteStore.commit_outcome_import_plan', 'add6a203baf74ebdf25588d537da098d28d3d62b1dd80390be8daa6599b1fb04'):
        (1, 'f"SELECT {\', \'.join(self._OUTCOME_COLUMNS)} FROM migration_outcome WHERE outcome_uid=?"'),
    ('SqliteStore.commit_outcome_import_plan', 'bce31bcedb2ea1608534e21b890939d2de16cd7611d1339fd4212f223c9af28d'):
        (1, 'f"SELECT user_id, json FROM {(\'edges\' if k == \'edge\' else \'episodes\')} WHERE id=?"'),
    ('SqliteStore.commit_outcome_import_plan', 'e09d8261753337dde680071ab5bdc7e6175a5754f49b43053debc68f25e57da4'):
        (1, 'f"INSERT INTO {a[\'table\']}({\', \'.join(cols)}) VALUES({\',\'.join(\'?\' * len(cols))})"'),
    ('SqliteStore.confirm_edge', '97ab04e41e08ed70ecdb71fc3252db4d341b4bda2cb224f3499c6142ae9ae628'):
        (1, 'f"INSERT INTO confirmations({_COLS}, origin, act_seq) VALUES(?,?,?,?,?,?,?,?,\'local\',?)"'),
    ('SqliteStore.confirm_notice', '5647332e7211148b9ad5b71a487ab19b4c15e73a38f06d91cb309d3070fb9335'):
        (1, "f'SELECT {self.RECORD_COLS} FROM redactions WHERE id=?'"),
    ('SqliteStore.confirm_notice', 'e47d7977d4c6808ad45f95d96520dcdbbba44b01614abab0dd7ce34fd79796d6'):
        (1, "f'SELECT user_id, json FROM {table} WHERE id=?'"),
    ('SqliteStore.confirmations_for', '6de03e078785d11fe4b34b9c39000a308103c9a26815b350347938403fc4eea6'):
        (1, "f'SELECT {_COLS} FROM confirmations WHERE user_id=? AND edge_id=? ORDER BY confirmed_at DE"),
    ('SqliteStore.contributions', 'c1a33b453a06fc1a588f12603f9d30098c211b2f378a5aa76edf0dfc0c49e6ef'):
        (1, "f'SELECT {self._CONTRIB_COLS} FROM contribution_ledger WHERE user_id=? AND survivor_type=?"),
    ('SqliteStore.contributors_of_source', 'ff79d44b37b3604e5d6ef605c9bec3381dec33cb8f91d45a207c030863ae2a27'):
        (1, "f'SELECT {self._CONTRIB_COLS} FROM contribution_ledger WHERE user_id=? AND identity_digest"),
    ('SqliteStore.edge_events', 'ea84967ae8e3eeaac6eca15de3557d2ce972249021e2339bd2f233b1737a612e'):
        (1, 'q'),
    ('SqliteStore.edges', 'ea84967ae8e3eeaac6eca15de3557d2ce972249021e2339bd2f233b1737a612e'):
        (1, 'q'),
    ('SqliteStore.forget_user', '99b754925b96f9575742044fee438d82476f53a86a23cd0dd138a323fc044add'):
        (1, "f'DELETE FROM {table} WHERE user_id=?'"),
    ('SqliteStore.migration_outcomes', 'e8e50718b302ae192e9d7ec4f38f340869dceab25ea51999b09d66a1041cf291'):
        (1, "f'SELECT {cols} FROM migration_outcome WHERE user_id=? ORDER BY edge_id, plan_id'"),
    ('SqliteStore.migration_outcomes_by_uid', '0af9489795fdbff7246fc9b15f70bf20e45f07abc5cdb64638b5a4e429a4e3a4'):
        (1, 'f"SELECT {cols} FROM migration_outcome WHERE outcome_uid IN ({\',\'.join(\'?\' * len(ids))})"'),
    ('SqliteStore.policy_receipts', '33f41f90a9a4e29967595c068ca002673821bcb52a03d702ab8f50612eae4c23'):
        (1, 'sql'),
    ('SqliteStore.redact', 'e47d7977d4c6808ad45f95d96520dcdbbba44b01614abab0dd7ce34fd79796d6'):
        (1, "f'SELECT user_id, json FROM {table} WHERE id=?'"),
    ('SqliteStore.redacted_targets', '6f6166079c03b2f9ad0b61e4d8ba0e1882ed1b32d1d221f124d45d4b67c39af6'):
        (1, "f'SELECT DISTINCT target_id FROM redactions WHERE user_id=? AND target_kind=? AND {_APPLIE"),
    ('SqliteStore.replies_for', '0e50f0c8b250ce20c7dcb393bdcbfc6c910b7099e5eb19b7c5a02ef0c64833d6'):
        (1, "f'SELECT {self._REPLY_COLS} FROM replies WHERE user_id=? AND edge_id=? ORDER BY written_at"),
    ('SqliteStore.transition_consolidation_if_current', '5126e0419cd211f8dc948a7d1276927164e8eab4a076c2c872d1addc70fe9f09'):
        (1, "'SELECT COUNT(*) FROM episodes WHERE user_id=? AND id IN ({})'.format(','.join('?' * len(o"),
}
# the one dynamic-table INSERT among them reaches only these tables (the domain is frozen with the entry)
ACT_TABLES = {"confirmations", "replies"}


def _qualnames(tree):
    out = {}

    def walk(node, prefix):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = f"{prefix}.{ch.name}" if prefix else ch.name
                for n in ast.walk(ch):
                    out[id(n)] = q
                walk(ch, q)
            else:
                walk(ch, prefix)
    walk(tree, "")
    return out


def _digest(node) -> str:
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


def _binders(tree, name):
    """Every node that BINDS `name` anywhere in the tree, in every statement form Python has."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name:
            out.append(n)
        elif isinstance(n, ast.Name) and n.id == name and isinstance(n.ctx, (ast.Store, ast.Del)):
            out.append(n)                  # Assign/AnnAssign/AugAssign/For/With/NamedExpr/comprehension/Delete targets
        elif isinstance(n, ast.alias) and (n.asname or n.name.split(".")[0]) == name:
            out.append(n)
        elif isinstance(n, ast.arg) and n.arg == name:
            out.append(n)
        elif isinstance(n, ast.ExceptHandler) and n.name == name:
            out.append(n)
        elif isinstance(n, (ast.Global, ast.Nonlocal)) and name in n.names:
            out.append(n)
        elif isinstance(n, (ast.MatchAs, ast.MatchStar)) and n.name == name:
            out.append(n)
        elif isinstance(n, ast.MatchMapping) and n.rest == name:
            out.append(n)
        elif hasattr(ast, "TypeVar") and isinstance(n, (ast.TypeVar, ast.ParamSpec, ast.TypeVarTuple)) and n.name == name:
            out.append(n)
    return out


_CLASSIFIER = []
_CLASSIFIED = {}
# research's stage-1b catch (2026-11-03): a trigger's body writes are reported only when a statement that FIRES it is
# prepared, never at CREATE TRIGGER, so a trigger or a view is refused as such, wherever it is created
_TRIGGER_OR_VIEW = {sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_CREATE_TEMP_TRIGGER, sqlite3.SQLITE_CREATE_VIEW,
                    sqlite3.SQLITE_CREATE_TEMP_VIEW}


def _sqlite_classify(sql: str) -> set:
    """SQLite's own reading of a statement, not a keyword: prepare it under an authorizer against an in-memory store at
    the head schema and record each (action, table, column) — the prepare asks once per updated column, so every
    callback is allowed and the statement runs inside a savepoint that is always rolled back. Returns the subset of
    {"edges-insert", "edges-json-update"} the statement performs."""
    if sql in _CLASSIFIED:
        return set(_CLASSIFIED[sql])
    if not _CLASSIFIER:
        from veracium.store import schema_version as _sv
        # NO statement cache: a cached statement is not re-prepared, so the authorizer would not be asked again
        c0 = sqlite3.connect(":memory:", isolation_level=None, cached_statements=0)
        c0.execute("BEGIN")
        _sv.create(c0, _sv.SCHEMA_VERSION)
        c0.execute("COMMIT")
        _CLASSIFIER.append(c0)
    c = _CLASSIFIER[0]
    if True:
        seen = []

        def auth(action, a1, a2, db, trigger):
            seen.append((action, a1, a2, db))     # SQLite asks once per updated COLUMN: every one must be seen
            return sqlite3.SQLITE_OK
        c.set_authorizer(auth)
        c.execute("BEGIN")                       # an in-memory scratch store, and whatever ran is rolled back
        try:
            c.execute(sql)
        except (sqlite3.DatabaseError, sqlite3.ProgrammingError):
            pass                                  # unbound parameters stop it after the prepare the authorizer saw
        finally:
            c.set_authorizer(None)
            if c.in_transaction:
                c.execute("ROLLBACK")
        tags = set()
        for action, a1, a2, db in seen:
            if action in _TRIGGER_OR_VIEW:
                tags.add("trigger-or-view")
            if action in (sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_DROP_TABLE) and "edges" in (a1, a2):
                tags.add("trigger-or-view")      # research's stage 2, S2-01: renaming edges routes a write around it
            if action == sqlite3.SQLITE_INSERT and a1 == "edges":
                tags.add("edges-insert")
            elif action == sqlite3.SQLITE_UPDATE and a1 == "edges" and a2 == "json":
                tags.add("edges-json-update")
        _CLASSIFIED[sql] = frozenset(tags)
        return tags


def _gate(source: str, others: dict | None = None) -> list:
    """N4f (a), round 4 (R3-02, (a′)), over sqlite.py's source: the problems, or []. `others` maps the OTHER src/
    modules' relative paths to their source (for the attribute and class rules); None reads them from disk."""
    tree = ast.parse(source)
    q = _qualnames(tree)
    parent = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
    bad = []
    at = lambda n: f"L{getattr(n, 'lineno', '?')}"
    cls = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SqliteStore"]
    defs = {n.name: n for n in (cls[0].body if cls else []) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    mod = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    # 1. the frozen bodies
    for name, want in FROZEN.items():
        node = defs.get(name) if name == METHOD else mod.get(name)   # the helper and the deferred journal: module level
        if node is None:
            bad.append(f"{name}: not defined where the gate expects it")
        elif _digest(node) != want:
            bad.append(f"{name}: its body is not the frozen one (digest {_digest(node)[:16]}…) — re-review it")
    # 2. the names: one binder each, never shadowed, never reached dynamically
    for name in (HELPER, DEFERRED):
        b = _binders(tree, name)
        if len(b) != 1 or not isinstance(b[0], (ast.FunctionDef, ast.ClassDef)) or b[0] not in tree.body:
            bad.append(f"{name}: bound {len(b)} time(s) in sqlite.py ({[at(x) for x in b]}) — exactly its one "
                       f"module-level definition may bind it")
    for name in (METHOD, JOURNAL):
        b = _binders(tree, name)
        if len(b) != 1 or b[0] is not defs.get(name):
            bad.append(f"{name}: bound {len(b)} time(s) in sqlite.py ({[at(x) for x in b]}) — exactly its one def "
                       f"in SqliteStore's class body may bind it")
    table = symtable.symtable(source, "sqlite.py", "exec")

    def scopes(t):
        yield t
        for ch in t.get_children():
            yield from scopes(ch)
    for t in scopes(table):
        if t.get_type() == "module":
            continue
        for name in (HELPER, DEFERRED):
            try:
                s = t.lookup(name)
            except KeyError:
                continue
            if s.is_assigned() or s.is_local() or s.is_parameter() or s.is_imported():
                bad.append(f"{name}: bound in the scope {t.get_name()!r} (symtable) — a shadow of the module's own")
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id in DYNAMIC_NAMES:
            bad.append(f"{at(n)}: dynamic access `{n.id}` in the store module")
        if isinstance(n, ast.Attribute) and n.attr in DYNAMIC_NAMES:      # `builtins.setattr` (research's stage 2)
            bad.append(f"{at(n)}: dynamic access `.{n.attr}` in the store module")
        if isinstance(n, ast.Attribute) and n.attr in DYNAMIC_ATTRS:
            bad.append(f"{at(n)}: dynamic access `{n.attr}` in the store module")
    # 3. method names are what they say, across src/ (research's read, item 1): no attribute assignment or deletion of
    # a guarded name on any receiver, and no class but SqliteStore defines the two methods
    if others is None:
        others = {str(p.relative_to(SRC)): p.read_text() for p in sorted(SRC.rglob("*.py"))
                  if p.resolve() != SQLITE.resolve()}
    for rel, text in [("veracium/store/sqlite.py", source)] + sorted(others.items()):
        t2 = tree if text is source else ast.parse(text)
        for n in ast.walk(t2):
            targets = (n.targets if isinstance(n, (ast.Assign, ast.Delete)) else
                       [n.target] if isinstance(n, (ast.AnnAssign, ast.AugAssign)) else [])
            for tg in targets:
                for x in ast.walk(tg):
                    if isinstance(x, ast.Attribute) and x.attr in GUARDED:
                        bad.append(f"{rel} {at(n)}: `{x.attr}` assigned or deleted as an attribute")
            # research's stage 2, S2-02: `setattr(SqliteStore, "_write_edge_row", …)` from another module
            if (isinstance(n, ast.Call) and (getattr(n.func, "id", None) in ("setattr", "delattr")
                                             or getattr(n.func, "attr", None) in ("setattr", "delattr"))
                    and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and n.args[1].value in GUARDED):
                bad.append(f"{rel} {at(n)}: `{n.args[1].value}` rebound by setattr/delattr")
            if isinstance(n, ast.ClassDef) and not (rel.endswith("store/sqlite.py") and n.name == "SqliteStore"):
                for m in n.body:
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name in (METHOD, JOURNAL):
                        bad.append(f"{rel} {at(m)}: class {n.name} defines {m.name} (only SqliteStore may)")
    # 4. the call sites: who calls what
    for n in ast.walk(tree):
        if not isinstance(n, (ast.Name, ast.Attribute)):
            continue
        name = n.id if isinstance(n, ast.Name) else n.attr
        if name not in GUARDED or (isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)):
            continue
        call = parent.get(n)
        where = q.get(id(n), "<module>")
        if not (isinstance(call, ast.Call) and call.func is n):
            bad.append(f"{at(n)}: `{name}` referenced, not called ({where})")
            continue
        if name == HELPER and where != f"SqliteStore.{METHOD}":
            bad.append(f"{at(n)}: the helper called outside the write method ({where})")
        if name == JOURNAL and where not in (f"SqliteStore.{METHOD}", f"{DEFERRED}.emit"):
            bad.append(f"{at(n)}: the journal writer called outside the write method ({where})")
        if name == DEFERRED and where != f"SqliteStore.{METHOD}":
            bad.append(f"{at(n)}: the deferred journal built outside the write method ({where})")
        if name == METHOD:
            if where not in WRITERS:
                bad.append(f"{at(n)}: `{METHOD}` called from {where}, not one of the seven writers")
            if not (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self"):
                bad.append(f"{at(n)}: `{METHOD}` reached through something other than `self` ({where})")
            if len(call.args) != 4 or any(isinstance(a, ast.Starred) for a in call.args):
                bad.append(f"{at(n)}: `{METHOD}` called with {len(call.args)} positional arguments, not 4 ({where})")
            sql = call.args[0] if call.args else None
            if not (isinstance(sql, ast.Constant) and isinstance(sql.value, str) and sql.value in CLOSED_SQL):
                bad.append(f"{at(n)}: `{METHOD}`'s sql is not a literal of the closed set ({where})")
            elif not (_sqlite_classify(sql.value) & {"edges-insert", "edges-json-update"}):
                bad.append(f"{at(n)}: `{METHOD}`'s sql is not, by SQLite's reading, an edges json write ({where})")
            kws = {k.arg: k.value for k in call.keywords}
            if None in kws:
                bad.append(f"{at(n)}: `{METHOD}` called with **kwargs ({where})")
            d = kws.get("defer")
            if d is not None:
                w = parent.get(call)
                ok = (where == DEFER_SITE and isinstance(d, ast.Constant) and d.value is True
                      and isinstance(w, ast.withitem) and w.context_expr is call and isinstance(w.optional_vars, ast.Name))
                if not ok:
                    bad.append(f"{at(n)}: `defer=` other than the constant True at the one `with` site ({where})")
    defer_sites = [n for n in ast.walk(tree) if isinstance(n, ast.keyword) and n.arg == "defer"]
    if len(defer_sites) != 1:
        bad.append(f"`defer=` appears {len(defer_sites)} times — exactly the redaction's one site may pass it")
    called = {q.get(id(n)) for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == METHOD}
    if called != WRITERS:
        bad.append(f"the writers calling `{METHOD}` are {sorted(c for c in called if c)}, not the seven")
    # 5a. the connection itself (round 3's receiver rules, kept): one connection, reached only through `self`
    for n in ast.walk(tree):
        if (isinstance(n, ast.Attribute) and n.attr == "connect" and isinstance(n.value, ast.Name)
                and n.value.id == "sqlite3" and q.get(id(n)) != "SqliteStore.__init__"):
            bad.append(f"{at(n)}: a second sqlite3 connection ({q.get(id(n), '<module>')})")
        if (isinstance(n, ast.Attribute) and n.attr == "_conn"
                and not (isinstance(n.value, ast.Name) and n.value.id == "self")):
            bad.append(f"{at(n)}: the connection reached through something other than `self`")
    # 5b. every string constant that SQLite reads as an edges json write is the `sql` of a write-method call — so an
    # alias of execute, the unbound Connection.execute, a cursor, a second connection or SQL held in a name cannot
    # carry one (the R2-01 forms)
    sql_args = {id(c.args[0]) for c in ast.walk(tree) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                and c.func.attr == METHOD and c.args}
    for n in ast.walk(tree):
        if (isinstance(n, ast.Constant) and isinstance(n.value, str) and "edges" in n.value.lower()
                and id(n) not in sql_args and _sqlite_classify(n.value) & {"edges-insert", "edges-json-update"}):
            bad.append(f"{at(n)}: an edges json write outside a write-method call ({q.get(id(n), '<module>')}): "
                       f"{' '.join(n.value.split())[:70]}")
    # 5b'. no trigger or view is created by any literal in src/ — SQLite reads a trigger's body writes only when a
    # statement fires it, so a trigger rewriting edges.json after a correct write is invisible to 5b (research)
    for rel, text in [("veracium/store/sqlite.py", source)] + sorted(others.items()):
        t3 = tree if text is source else ast.parse(text)
        for n in ast.walk(t3):
            low = n.value.lower() if isinstance(n, ast.Constant) and isinstance(n.value, str) else ""
            if (any(w in low for w in ("trigger", "view", "alter", "drop"))
                    and "trigger-or-view" in _sqlite_classify(n.value)):
                bad.append(f"{rel} {at(n)}: a trigger or view created, or edges altered or dropped: "
                           f"{' '.join(n.value.split())[:70]}")
    # 5c. the dynamic-table domain, frozen with its listed entry
    if _act_tables_in(source) != ACT_TABLES:
        bad.append(f"_ACT_COLUMNS reaches {sorted(_act_tables_in(source))}, not the frozen {sorted(ACT_TABLES)}")
    # 5. SQL: every execute/executemany/executescript on ANY receiver
    seen_nonlit = {}
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in SQL_CALLS):
            continue
        where = q.get(id(n), "<module>")
        if not n.args:
            bad.append(f"{at(n)}: `{n.func.attr}` with no SQL argument ({where})")
            continue
        a0 = n.args[0]
        if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
            tags = _sqlite_classify(a0.value)
            if tags & {"edges-insert", "edges-json-update"}:
                bad.append(f"{at(n)}: an edges json write executed directly, not through `{METHOD}` ({where}): "
                           f"{' '.join(a0.value.split())[:70]}")
            if n.func.attr == "executescript":
                bad.append(f"{at(n)}: executescript in the store module ({where})")
            continue
        key = (where, _digest(a0))
        if key not in NONLITERAL:
            bad.append(f"{at(n)}: a non-literal SQL site not in the reviewed list ({where}): {ast.unparse(a0)[:80]}")
        seen_nonlit[key] = seen_nonlit.get(key, 0) + 1
    # COUNTED (research's stage 2): a second site with an identical expression in the same function is not admitted
    # by the first one's entry
    for key, (count, _text) in NONLITERAL.items():
        if seen_nonlit.get(key, 0) != count:
            bad.append(f"non-literal site {key} occurs {seen_nonlit.get(key, 0)} time(s), the reviewed list says {count}")
    return bad


def _act_tables_in(source: str) -> set:
    tree = ast.parse(source)
    for n in ast.walk(tree):
        if (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_ACT_COLUMNS" for t in n.targets)
                and isinstance(n.value, ast.Dict)):
            return {k.value for k in n.value.keys if isinstance(k, ast.Constant)}
    return set()


def test_every_edge_write_goes_through_the_validating_serialiser():
    """N4f (a), round 4 (R3-02, (a′)): every write of the edges table's json goes through the ONE frozen write method,
    which binds the helper's captured bytes and journals the same bytes; exactly the seven writers call it, each with
    a literal of the closed set that SQLite reads as an edges json write; the guarded names are bound once and never
    shadowed (every binding form; symtable; attribute assignment anywhere in src/; no subclass override); no other
    statement — literal or not, through any receiver — writes edges.json; every non-literal SQL site is reviewed."""
    assert _gate(SQLITE.read_text()) == []
    assert SqliteStore._ACT_COLUMNS.keys() == ACT_TABLES == _act_tables_in(SQLITE.read_text())
    # the gate SAW them (a gate that recognises nothing passes everything)
    src = SQLITE.read_text()
    assert src.count(f"self.{METHOD}(") == 7 and src.count(f"{HELPER}(") == 2, (src.count(f"self.{METHOD}("),
                                                                               src.count(f"{HELPER}("))
    assert len(NONLITERAL) >= 40, len(NONLITERAL)
    for sql in CLOSED_SQL:
        assert _sqlite_classify(sql) & {"edges-insert", "edges-json-update"}, sql


def test_sqlite_reads_the_reviewers_two_sql_forms_as_edges_writes():
    """R3-02's SQL half: a leading keyword is not the reading. SQLite classifies a WITH-led UPDATE and a
    schema-qualified one as the edges json writes they are; a plain SELECT on edges and a write to another table are
    not; an UPDATE of another edges column is not a json write."""
    assert _sqlite_classify("WITH unused AS (SELECT 1) UPDATE edges SET json=? WHERE id=?") == {"edges-json-update"}
    assert _sqlite_classify("UPDATE main.edges SET json=? WHERE id=?") == {"edges-json-update"}
    assert _sqlite_classify("INSERT INTO main.edges(id,user_id,subject,relation,object,active,quarantined,json) "
                            "VALUES(?,?,?,?,?,?,?,?)") == {"edges-insert"}
    assert _sqlite_classify("SELECT json FROM edges WHERE id=?") == set()
    assert _sqlite_classify("UPDATE edges SET quarantined=? WHERE id=?") == set()
    assert _sqlite_classify("UPDATE confirmations SET request_digest=? WHERE edge_id=?") == set()


def test_the_inventorys_reasons_hold():
    """The reviewed lists' reasons are claims about other code, checked: the act tables are exactly the frozen domain,
    and no OTHER src module holds an edges write (the write method is the package's one)."""
    assert set(SqliteStore._ACT_COLUMNS) == ACT_TABLES
    for p in sorted(SRC.rglob("*.py")):
        if p.resolve() == SQLITE.resolve():
            continue
        assert not re.search(r"(?i)\b(insert(\s+or\s+replace)?\s+into|update)\s+(main\.)?edges\b", p.read_text()), p


# The mutants: each an edit of sqlite.py's text (anchors asserted to occur exactly once), refused by the gate. The
# reviewer's seven forms are writers that BYPASS the write method; (a′)'s own attack the method, its names and its lists.
_INV = ('        self._write_edge_row("UPDATE edges SET active=0, json=? WHERE id=?", (), edge, (edge_id,),\n'
        '                             user_id=row[1], edge_id=edge_id, prior=row[0], kind="invalidated", reason=reason)')
_BYPASS = ('        new_json = _validated_edge_json(edge)\n{rebind}'
           '        self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?", (new_json, edge_id))\n'
           '        self._journal_edge_write(row[1], edge_id, new_json, row[0], kind="invalidated", reason=reason)')
GATE_MUTANTS = {
    # the reviewer's seven (R3-02)
    "annotated rebinding": (_INV, _BYPASS.format(rebind='        new_json: str = new_json.replace("0.8", "1.8")\n')),
    "a loop target": (_INV, _BYPASS.format(rebind='        for new_json in (new_json.replace("0.8", "1.8"),):\n            pass\n')),
    "unpacking": (_INV, _BYPASS.format(rebind='        new_json, _ = new_json.replace("0.8", "1.8"), None\n')),
    "a named expression": (_INV, _BYPASS.format(rebind='        if (new_json := new_json.replace("0.8", "1.8")):\n            pass\n')),
    "the helper shadowed by a lambda": (_INV, '        _validated_edge_json = lambda obj: obj.model_dump_json()\n' +
                                        _BYPASS.format(rebind="")),
    "a WITH-led write": (_INV, '        self._conn.execute("WITH unused AS (SELECT 1) UPDATE edges SET active=0, json=? '
                               'WHERE id=?", (edge.model_dump_json(), edge_id))'),
    "a schema-qualified write": (_INV, '        self._conn.execute("UPDATE main.edges SET active=0, json=? WHERE id=?", '
                                       '(edge.model_dump_json(), edge_id))'),
    # (a′)'s own
    "an edit inside the write method": ('        captured = _validated_edge_json(edge)\n',
                                        '        captured = _validated_edge_json(edge)\n        captured = captured\n'),
    "a second helper call inside it": ('        if defer:\n            return _DeferredJournal(',
                                       '        _validated_edge_json(edge)\n        if defer:\n            return _DeferredJournal('),
    "journaling different bytes": ('        self._journal_edge_write(user_id, edge_id, captured, prior, kind=kind, reason=reason)',
                                   '        self._journal_edge_write(user_id, edge_id, edge.model_dump_json(), prior, kind=kind, reason=reason)'),
    "a writer journals for itself": (_INV, _INV + '\n        self._journal_edge_write(row[1], edge_id, "{}", row[0])'),
    "the redaction journals its own dump": ('                pending.emit(kind="redacted", reason=reason)',
                                            '                self._journal_edge_write(user_id, target_id, new_json, before_json, '
                                            'kind="redacted", reason=reason)'),
    "defer non-constant": ('prior=before_json, defer=True) as pending:', 'prior=before_json, defer=bool(kind)) as pending:'),
    "defer through **kwargs": ('prior=before_json, defer=True) as pending:', 'prior=before_json, **{"defer": True}) as pending:'),
    "a second defer site": (_INV, _INV.replace('reason=reason)', 'reason=reason, defer=True)')),
    "an f-string edges write": (_INV, '        self._conn.execute(f"UPDATE {\'edges\'} SET active=0, json=? WHERE id=?", '
                                      '(edge.model_dump_json(), edge_id))'),
    "executescript": (_INV, _INV + '\n        self._conn.executescript("UPDATE edges SET json=\'{}\' WHERE 0")'),
    "a non-literal site added unlisted": (_INV, _INV + '\n        self._conn.execute(" ".join(["SELECT", "1"]))'),
    "an eighth writer": ('    def _edge_in_refusal(self, user_id: str, edge_id: str) -> bool:',
                         '    def _eighth(self, edge):\n'
                         '        self._write_edge_row("UPDATE edges SET json=? WHERE id=?", (), edge, (edge.id,),\n'
                         '                             user_id=edge.user_id, edge_id=edge.id, prior=None)\n\n'
                         '    def _edge_in_refusal(self, user_id: str, edge_id: str) -> bool:'),
    "the write method reached unbound": (_INV, _INV.replace("self._write_edge_row(", "SqliteStore._write_edge_row(self, ")),
    "an instance-attribute shadow": ('        self._path = str(path)\n',
                                     '        self._path = str(path)\n        self._write_edge_row = lambda *a, **k: None\n'),
    "the helper shadowed at module scope": ('class _DeferredJournal:\n',
                                            '_validated_edge_json = _validated_edge_json\n\n\nclass _DeferredJournal:\n'),
    "the act tables gain edges": ('    _ACT_COLUMNS = {\n', '    _ACT_COLUMNS = {\n        "edges": ("id",),\n'),
    # round 3's R2-01 forms, kept (each now a bypass writer)
    "executemany": (_INV, '        self._conn.executemany("UPDATE edges SET active=0, json=? WHERE id=?", '
                          '[(edge.model_dump_json(), edge_id)])'),
    "an alias of execute": (_INV, '        ex = self._conn.execute\n'
                                  '        ex("UPDATE edges SET active=0, json=? WHERE id=?", (edge.model_dump_json(), edge_id))'),
    "a cursor": (_INV, '        self._conn.cursor().execute("UPDATE edges SET active=0, json=? WHERE id=?", '
                       '(edge.model_dump_json(), edge_id))'),
    "SQL held in a name": (_INV, '        q = "UPDATE edges SET active=0, json=? WHERE id=?"\n'
                                 '        self._conn.execute(q, (edge.model_dump_json(), edge_id))'),
    "the unbound Connection.execute": (_INV, '        sqlite3.Connection.execute(self._conn, "UPDATE edges SET active=0, '
                                             'json=? WHERE id=?", (edge.model_dump_json(), edge_id))'),
    "a second connection": (_INV, '        sqlite3.connect(self._path).execute("UPDATE edges SET active=0, json=? '
                                  'WHERE id=?", (edge.model_dump_json(), edge_id))'),
}
GATE_MUTANTS["a trigger rewriting edges.json after a correct write"] = (
    _INV, _INV + '\n        self._conn.execute("CREATE TRIGGER IF NOT EXISTS lift AFTER INSERT ON edge_event BEGIN '
                 "UPDATE edges SET json = json_set(json, '$.provenance.confidence', 1.8) WHERE id = NEW.edge_id; END\")")
GATE_MUTANTS["a rename route around the edges table (research's S2-01)"] = (
    _INV, _INV + '\n        self._conn.execute("ALTER TABLE edges RENAME TO edges_x")\n'
                 '        self._conn.execute("UPDATE edges_x SET json=? WHERE id=?", (edge.model_dump_json(), edge_id))\n'
                 '        self._conn.execute("ALTER TABLE edges_x RENAME TO edges")')
GATE_MUTANTS["builtins.setattr in the store module"] = (
    _INV, _INV + '\n        import builtins\n        builtins.setattr(edge, "id", edge_id)')
GATE_MUTANTS["a second identical non-literal site"] = (
    '                self._conn.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))\n',
    '                self._conn.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))\n'
    '                self._conn.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))\n')
GATE_MUTANTS["an edit inside the helper (research's S2-03)"] = (
    '    Edge.model_validate_json(captured)\n    return captured\n',
    '    Edge.model_validate_json(captured)\n    captured = captured\n    return captured\n')
GATE_MUTANTS["a temporary view"] = (_INV, _INV + '\n        self._conn.execute("CREATE TEMP VIEW v AS SELECT json FROM edges")')
# appended to the END of sqlite.py's text (class-level attacks)
EOF_MUTANTS = {
    "a class-attribute reassignment": "\nSqliteStore._write_edge_row = SqliteStore._journal_edge_write\n",
    "a subclass override": "\n\nclass _Shadow(SqliteStore):\n    def _write_edge_row(self, *a, **k):\n        return None\n",
    "the deferred journal rebound": "\n_DeferredJournal = object\n",
}
# the mutants the gate reads OUTSIDE sqlite.py's text: a same-named method on a class in another src module
OTHER_MUTANTS = {
    "setattr of the write method from another module (research's S2-02)": {
        "veracium/_planted.py": "from veracium.store.sqlite import SqliteStore\n"
                                "setattr(SqliteStore, '_write_edge_row', lambda *a, **k: None)\n"},
    "a trigger created in another module": {"veracium/_planted.py": 'def plant(c):\n    c.execute("CREATE TRIGGER t AFTER '
                                            'INSERT ON edge_event BEGIN UPDATE edges SET json = json WHERE id = '
                                            'NEW.edge_id; END")\n'},
    "a class elsewhere defines the write method": {"veracium/_planted.py": "class X:\n    def _write_edge_row(self):\n        pass\n"},
    "an attribute assignment elsewhere": {"veracium/_planted.py": "import veracium.store.sqlite as s\n"
                                                                  "s.SqliteStore._journal_edge_write = None\n"},
}


@pytest.mark.parametrize("name", list(GATE_MUTANTS))
def test_the_gate_refuses_each_unresolved_form(name):
    """The gate's own matrix (R2-01's forms kept; R3-02's seven; (a′)'s own): each planted on a copy of sqlite.py's
    text is refused; the honest text passes (above)."""
    old, new = GATE_MUTANTS[name]
    src = SQLITE.read_text()
    assert src.count(old) == 1, f"{name}: the anchor occurs {src.count(old)} times — re-anchor it"
    assert _gate(src.replace(old, new)), f"{name}: the gate passed it"


@pytest.mark.parametrize("name", list(EOF_MUTANTS))
def test_the_gate_refuses_each_class_level_attack(name):
    assert _gate(SQLITE.read_text() + EOF_MUTANTS[name]), f"{name}: the gate passed it"


@pytest.mark.parametrize("name", list(OTHER_MUTANTS))
def test_the_gate_reads_the_rest_of_src(name):
    others = {str(p.relative_to(SRC)): p.read_text() for p in sorted(SRC.rglob("*.py")) if p.resolve() != SQLITE.resolve()}
    assert _gate(SQLITE.read_text(), others) == []
    assert _gate(SQLITE.read_text(), {**others, **OTHER_MUTANTS[name]}), f"{name}: the gate passed it"


def test_each_writer_bypassing_the_write_method_is_refused():
    """§6's 'for each of the declared edge writers: that writer bypasses the write method' row, one planted copy per
    writer: its call becomes a direct execute of the same literal with an unvalidated dump."""
    src = SQLITE.read_text()
    tree = ast.parse(src)
    calls = [c for c in ast.walk(tree) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
             and c.func.attr == METHOD]
    assert len(calls) == 7, len(calls)
    lines = src.split("\n")
    for c in calls:
        sql = c.args[0].value
        start, end = c.lineno - 1, c.end_lineno - 1
        ind = lines[start][:len(lines[start]) - len(lines[start].lstrip())]
        stmt = f'{ind}self._conn.execute({sql!r}, ())'
        if lines[start].lstrip().startswith("with "):
            stmt = f"{ind}with contextlib.nullcontext() as pending:\n{ind}    self._conn.execute({sql!r}, ())"
        mutated = "\n".join(lines[:start] + [stmt] + lines[end + 1:])
        assert _gate(mutated), f"the bypass at L{c.lineno} passed"


# ---- R3-01: the store binds the bytes it validated ------------------------------------------------------------------

def _swap_after_validation(edge, bad_conf):
    """A hook on the validators that, AFTER a validation succeeds, lets a second thread replace the caller's mutable
    Edge's provenance (the unvalidated `model_copy` route C protects against), once — the reviewer's schedule."""
    fired = []
    real_json, real_obj = Edge.model_validate_json, Edge.model_validate

    def mutate():
        edge.provenance = edge.provenance.model_copy(update={"confidence": bad_conf})

    def after(result):
        if not fired:
            fired.append(1)
            t = threading.Thread(target=mutate)
            t.start()
            t.join()
        return result
    return (classmethod(lambda cls, *a, **k: after(real_json.__func__(cls, *a, **k))),
            classmethod(lambda cls, *a, **k: after(real_obj.__func__(cls, *a, **k))), fired)


def _two_observations(edge):                    # round 3's body: validate one dump, serialise another
    Edge.model_validate(edge.model_dump())
    return edge.model_dump_json()


def _validate_then_redump(edge):                # validate the capture, return a FRESH dump
    captured = edge.model_dump_json()
    Edge.model_validate_json(captured)
    return edge.model_dump_json()


def _capture_unvalidated(edge):                 # one observation, never validated
    return edge.model_dump_json()


def _capture_validate_the_object(edge):         # research's stage-2 M4: capture, but validate the OBJECT's dump
    captured = edge.model_dump_json()
    Edge.model_validate(edge.model_dump())
    return captured


def _capture_validate_a_copy(edge):             # research's stage-2 M6: capture, validate a deep copy's dump
    captured = edge.model_dump_json()
    Edge.model_validate(edge.model_copy(deep=True).model_dump())
    return captured


R3_01_MUTANTS = {"two observations (round 3's body)": _two_observations,
                 "validate the capture, return a fresh dump": _validate_then_redump,
                 "capture without validating": _capture_unvalidated,
                 "capture, validate the object's dump (research's M4)": _capture_validate_the_object,
                 "capture, validate a deep copy's dump (research's M6)": _capture_validate_a_copy}


def _r3_01_cell(tmp_path, monkeypatch, helper=None):
    """Returns (refused_before, stored_confidence, read_ok, fired) for one run of the reviewer's schedule through
    add_edge. Its hooks live in their OWN MonkeyPatch context, so undoing them never undoes the tripwire's patches."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    with pytest.MonkeyPatch.context() as mp:
        return _r3_01_run(tmp_path, mp, helper)


def _r3_01_run(tmp_path, monkeypatch, helper):
    if helper is not None:
        monkeypatch.setattr(SQ, HELPER, helper)
    s = SqliteStore(str(tmp_path / "r301.db"))
    pre = _edge("pre", S.Volatility.SLOW, 0.5)
    pre.provenance = Provenance.model_construct(**{**dict(pre.provenance), "confidence": 1.8})
    try:
        s.add_edge(pre)
        refused = False
    except ValueError:
        refused = True
    e = _edge("race", S.Volatility.SLOW, 0.8)
    vj, vo, fired = _swap_after_validation(e, 1.8)
    with pytest.MonkeyPatch.context() as hooks:
        hooks.setattr(Edge, "model_validate_json", vj)
        hooks.setattr(Edge, "model_validate", vo)
        s.add_edge(e)
    stored = json.loads(sqlite3.connect(str(tmp_path / "r301.db")).execute(
        "SELECT json FROM edges WHERE id='race'").fetchone()[0])["provenance"]["confidence"]
    try:
        s.edges(U, active_only=False, include_quarantined=True)
        read_ok = True
    except ValueError:
        read_ok = False
    return refused, stored, read_ok, bool(fired)


def _mirror_cell(tmp_path, monkeypatch, helper=None):
    """Research's stage-2 MIRROR schedule: the edge carries an unvalidated 1.8 when the helper serialises it, and a
    second thread repairs it to 0.8 right after that serialisation. Returns (refused, stored confidence or None,
    fired). The hook fires only for a dump made by whatever is CURRENTLY bound as the helper."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    with pytest.MonkeyPatch.context() as mp:
        if helper is not None:
            mp.setattr(SQ, HELPER, helper)
        s = SqliteStore(str(tmp_path / "mirror.db"))
        e = _edge("mir", S.Volatility.SLOW, 0.8)
        e.provenance = Provenance.model_construct(**{**dict(e.provenance), "confidence": 1.8})
        real, fired = Edge.model_dump_json, []

        def dump(self, *a, **k):
            out = real(self, *a, **k)
            if self is e and not fired and sys._getframe(1).f_code is SQ.__dict__[HELPER].__code__:
                fired.append(1)
                th = threading.Thread(target=lambda: setattr(e, "provenance",
                                                             e.provenance.model_copy(update={"confidence": 0.8})))
                th.start()
                th.join()
            return out
        with pytest.MonkeyPatch.context() as hooks:
            hooks.setattr(Edge, "model_dump_json", dump)
            try:
                s.add_edge(e)
                refused = False
            except ValueError:
                refused = True
    row = sqlite3.connect(str(tmp_path / "mirror.db")).execute("SELECT json FROM edges WHERE id='mir'").fetchone()
    return refused, (json.loads(row[0])["provenance"]["confidence"] if row else None), bool(fired)


def test_the_store_binds_the_bytes_it_validated(tmp_path, monkeypatch):
    """N4f (b), round 3's R3-01: the helper serialises ONCE and validates and returns those bytes. Under the reviewer's
    schedule — validation succeeds, then another thread replaces the caller's Edge provenance with an unvalidated 1.8
    — the store commits the 0.8 it validated and reads back; an already-invalid input is still refused. Under the
    MIRROR schedule (research's stage 2) — an unvalidated 1.8 at the serialisation, repaired to 0.8 right after — the
    store refuses and writes nothing: the bytes validated are the bytes captured."""
    assert _r3_01_cell(tmp_path / "a", monkeypatch) == (True, 0.8, True, True)
    assert _mirror_cell(tmp_path / "b", monkeypatch) == (True, None, True)


@pytest.mark.parametrize("name", list(R3_01_MUTANTS))
def test_the_store_binds_the_bytes_it_validated_kills_each_mutant(tmp_path, monkeypatch, name):
    """Each superseded or weakened helper body fails the regression above under at least one of its two schedules
    (the superseded implementation is the mutant): two observations and a fresh re-dump commit 1.8 under the
    reviewer's; a capture never validated admits the invalid input; validating the OBJECT's dump, or a copy's, stores
    1.8 under the mirror (research's M4 and M6)."""
    a = _r3_01_cell(tmp_path / "a", monkeypatch, R3_01_MUTANTS[name])
    b = _mirror_cell(tmp_path / "b", monkeypatch, R3_01_MUTANTS[name])
    assert (a, b) != ((True, 0.8, True, True), (True, None, True)), f"{name}: both schedules passed it ({a}, {b})"


test_the_store_binds_the_bytes_it_validated_kills_each_mutant.plants_defects = True   # its mutants store 1.8


def test_the_redaction_journals_the_bytes_it_stored(tmp_path):
    """(a′)'s single capture in the one writer whose journal is DEFERRED past its tombstone: after a redaction, the
    `redacted` event's state is byte-identical to the stored row's json (before round 4 the row bound the helper's
    bytes and the journal a second dump of the same model — equal strings by measurement, now one value)."""
    s = SqliteStore(str(tmp_path / "red.db"))
    s.add_edge(_edge("r", S.Volatility.SLOW, 0.5))
    s.redact(U, edge_id="r", reason="subject_request")
    c = sqlite3.connect(str(tmp_path / "red.db"))
    row = c.execute("SELECT json FROM edges WHERE id='r'").fetchone()[0]
    ev = c.execute("SELECT state FROM edge_event WHERE edge_id='r' AND kind='redacted'").fetchall()
    assert ev == [(row,)], (ev, row)


# ---- (a′)'s deferred journal, by behaviour ---------------------------------------------------------------------------

def _deferred(tmp_path):
    """A store holding edge "d" at 0.5, and a CHANGED copy of it (0.6) to write — so a rolled-back write and a committed
    one differ on disk."""
    s = SqliteStore(str(tmp_path / "dj.db"))
    s.add_edge(_edge("d", S.Volatility.SLOW, 0.5))
    e = _row(s, "d")
    return s, e.model_copy(update={"provenance": e.provenance.model_copy(update={"confidence": 0.6})})


def _rows_and_events(where):
    c = sqlite3.connect(str(where / "dj.db"))
    return (c.execute("SELECT json FROM edges").fetchall(), c.execute("SELECT seq, kind, state FROM edge_event").fetchall())


def test_a_deferred_journal_left_unemitted_rolls_the_write_back(tmp_path):
    """Leaving the block without emit — fall-through or an early return — raises inside the transaction: the row write
    is rolled back with it, so no row commits without its journal."""
    s, e = _deferred(tmp_path)
    before = _rows_and_events(tmp_path)

    def early_return():
        with s._write_txn():
            with s._write_edge_row("UPDATE edges SET json=? WHERE id=?", (), e, ("d",), user_id=U, edge_id="d",
                                   prior=None, defer=True):
                return "left early"
    _refuses(RuntimeError, early_return)
    assert _rows_and_events(tmp_path) == before


def test_a_deferred_journal_emits_once_and_only_inside_its_block(tmp_path):
    s, e = _deferred(tmp_path)
    with s._write_txn():
        with s._write_edge_row("UPDATE edges SET json=? WHERE id=?", (), e, ("d",), user_id=U, edge_id="d",
                               prior=_row_json(tmp_path, "d"), defer=True) as pending:
            pending.emit()
            _refuses(RuntimeError, lambda: pending.emit())
    _refuses(RuntimeError, lambda: pending.emit())
    _refuses(TypeError, lambda: s._write_edge_row("UPDATE edges SET json=? WHERE id=?", (), e, ("d",), user_id=U,
                                                  edge_id="d", prior=None, defer=True, kind="mutated"))


def _a_failing_side_write(where):
    """(the exception propagated, the store unchanged) for a deferred write whose block raises before emit."""
    where.mkdir()
    s, e = _deferred(where)
    before = _rows_and_events(where)
    try:
        with s._write_txn():
            with s._write_edge_row("UPDATE edges SET json=? WHERE id=?", (), e, ("d",), user_id=U, edge_id="d",
                                   prior=None, defer=True):
                raise sqlite3.OperationalError("a side-table write failed")
        raised = False
    except sqlite3.OperationalError:
        raised = True
    return raised, _rows_and_events(where) == before


def test_a_deferred_journal_never_swallows_an_exception(tmp_path, monkeypatch):
    """An exception leaving the block is neither emitted for nor suppressed, so the transaction rolls the row back.
    Mutant: `__exit__` returning True swallows a failed side-table write and commits a row with no journal."""
    assert _a_failing_side_write(tmp_path / "honest") == (True, True)
    monkeypatch.setattr(SQ._DeferredJournal, "__exit__", lambda self, *a: True)
    assert _a_failing_side_write(tmp_path / "mutant") != (True, True), "the swallowing mutant passed"


test_a_deferred_journal_never_swallows_an_exception.plants_defects = True   # its mutant commits a row with no journal


def _row_json(tmp_path, eid):
    return sqlite3.connect(str(tmp_path / "dj.db")).execute("SELECT json FROM edges WHERE id=?", (eid,)).fetchone()[0]


# ---- the runtime tripwire (tests only): an edges json write prepared outside the write method's frame ----------------

def _in_frames(codes) -> bool:
    f = sys._getframe(2)
    while f is not None:
        if f.f_code in codes:
            return True
        f = f.f_back
    return False


_TAKEN = {}                                                 # the guarded code objects, taken ONCE (research's S2-02)


def _outside_the_write_method(action, a1, a2):
    if not ((action == sqlite3.SQLITE_INSERT and a1 == "edges")
            or (action == sqlite3.SQLITE_UPDATE and a1 == "edges" and a2 == "json")):
        return False
    return not _in_frames({_TAKEN["write"]})               # BY CODE IDENTITY, taken at setup, never by name


def _journal_forged(action, a1):
    """An edge_event INSERT prepared from neither the journal writer nor the v13 baseline journal (the only two
    callers of append_event in src/): a forged journal would let a write pass the row-equals-journal invariant."""
    return action == sqlite3.SQLITE_INSERT and a1 == "edge_event" and not _in_frames({_TAKEN["journal"],
                                                                                      _TAKEN["baselines"]})


def _guarded_identity_problems():
    """Research's stage 2, S2-02: the four guarded objects are THE SOURCE'S OWN — each code object's file is the store
    module and its first line is its `def` in that file's AST — so a replacement installed by setattr from elsewhere
    (or any rebinding the static gate cannot see) is named before the cell runs."""
    tree = ast.parse(SQLITE.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SqliteStore")
    dj = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == DEFERRED)
    want = {(f"SqliteStore.{n.name}"): n.lineno for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in (METHOD, JOURNAL)}
    want[HELPER] = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == HELPER).lineno
    want.update({f"{DEFERRED}.{n.name}": n.lineno for n in dj.body if isinstance(n, ast.FunctionDef)})
    have = {f"SqliteStore.{m}": SqliteStore.__dict__.get(m) for m in (METHOD, JOURNAL)}
    have[HELPER] = SQ.__dict__.get(HELPER)
    djc = SQ.__dict__.get(DEFERRED)
    if not (isinstance(djc, type) and djc.__module__ == SQ.__name__):
        return [f"{DEFERRED} is not the store module's own class: {djc!r}"]
    have.update({f"{DEFERRED}.{m}": djc.__dict__.get(m) for m in ("__init__", "__enter__", "emit", "__exit__")})
    probs = []
    for name, line in sorted(want.items()):
        code = getattr(have.get(name), "__code__", None)
        if code is None or pathlib.Path(code.co_filename).resolve() != pathlib.Path(SQ.__file__).resolve() \
                or code.co_firstlineno != line:
            probs.append(f"{name}: not the store module's own definition at L{line} ({have.get(name)!r})")
    return probs


def _store_invariant_problems(path):
    """Research's stage 2: route-independent comparisons over a store a cell left, whatever route wrote it —
    (1) every edges row validates as an Edge; (2) every edges row equals the state of its last edge_event (an
    unjournaled write, in bound or not, shows here)."""
    if not pathlib.Path(path).exists():
        return []
    c = sqlite3.connect(path)
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='edge_event'").fetchone():
            return []
        out = []
        for eid, uid, js in c.execute("SELECT id, user_id, json FROM edges"):
            try:
                Edge.model_validate_json(js)
            except ValueError as ex:
                out.append(f"{path}: edge {eid!r} does not validate ({str(ex).splitlines()[0][:80]})")
            last = c.execute("SELECT state FROM edge_event WHERE user_id=? AND edge_id=? ORDER BY seq DESC LIMIT 1",
                             (uid, eid)).fetchone()
            if last is None or last[0] != js:
                out.append(f"{path}: edge {eid!r}'s row is not its last journaled state")
        return out
    finally:
        c.close()


@pytest.fixture(autouse=True)
def _edges_write_tripwire(monkeypatch, request):
    """Every store this module opens carries an authorizer that DENIES (and records) an edges INSERT or edges.json
    UPDATE prepared from a stack without the write method's code object, ANY such write a trigger makes, and the
    creation of any trigger or view; its connection keeps no statement cache, so every execution is re-prepared and
    seen. Every executed path in these cells and the N4c fixtures is checked at runtime, beside the static gate."""
    assert _guarded_identity_problems() == [], _guarded_identity_problems()
    from veracium.store import edge_events as _ee
    _TAKEN.update(write=SqliteStore.__dict__[METHOD].__code__, journal=SqliteStore.__dict__[JOURNAL].__code__,
                  baselines=_ee.journal_baselines.__code__)
    hits, paths = [], []
    real_init = SqliteStore.__init__

    def init(self, *a, **k):
        real_init(self, *a, **k)
        paths.append(self._path)

        def auth(action, a1, a2, db, trigger):
            edges_write = ((action == sqlite3.SQLITE_INSERT and a1 == "edges")
                           or (action == sqlite3.SQLITE_UPDATE and a1 == "edges" and a2 == "json"))
            if (action in _TRIGGER_OR_VIEW or (trigger is not None and edges_write)
                    or (action in (sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_DROP_TABLE) and "edges" in (a1, a2))
                    or (trigger is None and _outside_the_write_method(action, a1, a2))
                    or (trigger is None and _journal_forged(action, a1))):
                hits.append((action, a1, a2, trigger))
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        self._conn.set_authorizer(auth)
    monkeypatch.setattr(SqliteStore, "__init__", init)
    # NO statement cache on the store's connection: the authorizer runs at PREPARE, and a cached statement is not
    # re-prepared, so a same-text bypass after a legitimate write would run unseen (research's stage-1b catch)
    real_connect = sqlite3.connect
    monkeypatch.setattr(sqlite3, "connect", lambda *a, **k: real_connect(*a, **{"cached_statements": 0, **k}))
    yield hits
    assert hits == [], f"an edges json write outside the write method: {hits}"
    if not (getattr(request.function, "plants_defects", False)      # a cell that stores a defect ON PURPOSE says so
            or getattr(request.node, "_0048_call_failed", False)):    # a failed cell has already detected its defect
        probs = [x for path in dict.fromkeys(paths) for x in _store_invariant_problems(path)]
        assert probs == [], probs


def test_the_tripwire_refuses_a_write_outside_the_method_and_a_same_named_function(tmp_path, _edges_write_tripwire):
    """The tripwire's own controls: a direct edges.json UPDATE on the store's connection is DENIED; so is one made
    from a function that is merely NAMED `_write_edge_row`; the real method passes."""
    s = SqliteStore(str(tmp_path / "tw.db"))
    s.add_edge(_edge("t", S.Volatility.SLOW, 0.5))
    with pytest.raises(sqlite3.DatabaseError):
        s._conn.execute("UPDATE edges SET json=json WHERE id='t'")
    ns = {}
    exec("def _write_edge_row(c):\n    c.execute(\"UPDATE edges SET json=json WHERE id='t'\")\n", ns)
    with pytest.raises(sqlite3.DatabaseError):
        ns["_write_edge_row"](s._conn)
    assert len(_edges_write_tripwire) == 2
    _edges_write_tripwire.clear()


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


def test_the_head_schema_creates_no_trigger_and_no_view():
    """The pin the trigger rule rests on: the head schema has no trigger and no view (so a trigger's writes could only
    come from code the gate refuses), and no src/ module holds trigger or view DDL."""
    from veracium.store import schema_version as _sv
    c = sqlite3.connect(":memory:")
    c.execute("BEGIN")
    _sv.create(c, _sv.SCHEMA_VERSION)
    c.execute("COMMIT")
    assert c.execute("SELECT type, name FROM sqlite_master WHERE type IN ('trigger', 'view')").fetchall() == []
    for p in sorted(SRC.rglob("*.py")):
        assert not re.search(r"(?i)\bcreate\s+(temp(orary)?\s+)?(trigger|view)\b", p.read_text()), p


def test_the_tripwire_sees_a_trigger_and_a_cached_same_text_bypass(tmp_path, _edges_write_tripwire):
    """The tripwire's controls for research's two catches: creating a trigger on the store's connection is DENIED; and
    after a legitimate write has prepared a statement text, a DIRECT execute of that same text is still denied — the
    connection keeps no cache, so it is re-prepared and seen."""
    s = SqliteStore(str(tmp_path / "tw2.db"))
    s.add_edge(_edge("c", S.Volatility.SLOW, 0.5))
    with pytest.raises(sqlite3.DatabaseError):
        s._conn.execute("CREATE TRIGGER lift AFTER INSERT ON edge_event BEGIN UPDATE edges SET json = json "
                        "WHERE id = NEW.edge_id; END")
    e = _row(s, "c")
    prior = sqlite3.connect(str(tmp_path / "tw2.db")).execute("SELECT json FROM edges WHERE id='c'").fetchone()[0]
    with s._write_txn():                    # the legitimate write prepares the statement text first
        s._write_edge_row("UPDATE edges SET json=? WHERE id=?", (), e, ("c",), user_id=U, edge_id="c", prior=prior)
    with pytest.raises(sqlite3.DatabaseError):
        s._conn.execute("UPDATE edges SET json=? WHERE id=?", ("{}", "c"))
    assert len(_edges_write_tripwire) == 2, _edges_write_tripwire
    _edges_write_tripwire.clear()


def test_the_identity_check_names_a_replaced_write_method():
    """Research's stage 2, S2-02, at runtime: a write method (or helper, or journal writer) replaced by setattr is
    named by the setup-time identity check; the source's own objects pass it."""
    assert _guarded_identity_problems() == []
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(SqliteStore, METHOD, lambda *a, **k: None)
        assert any(METHOD in x for x in _guarded_identity_problems())
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(SQ, HELPER, lambda e: e.model_dump_json())
        assert any(HELPER in x for x in _guarded_identity_problems())


def test_the_row_invariants_name_an_out_of_bound_and_an_unjournaled_write(tmp_path):
    """The route-independent comparisons (research's stage 2) on rows planted through a SEPARATE connection, so no
    route the authorizer knows is involved: an out-of-bound confidence fails (1); an IN-bound unjournaled rewrite
    fails (2); the honest store passes both."""
    s = SqliteStore(str(tmp_path / "inv.db"))
    s.add_edge(_edge("i", S.Volatility.SLOW, 0.5))
    s.add_edge(_edge("j", S.Volatility.SLOW, 0.5))
    assert _store_invariant_problems(str(tmp_path / "inv.db")) == []
    with contextlib.closing(sqlite3.connect(str(tmp_path / "inv.db"))) as raw:
        for eid, conf in (("i", 1.8), ("j", 0.25)):
            js = json.loads(raw.execute("SELECT json FROM edges WHERE id=?", (eid,)).fetchone()[0])
            js["provenance"]["confidence"] = conf
            raw.execute("UPDATE edges SET json=? WHERE id=?", (json.dumps(js), eid))
        raw.commit()
    probs = _store_invariant_problems(str(tmp_path / "inv.db"))
    assert any("'i' does not validate" in x for x in probs) and any("'j'" in x and "journaled" in x for x in probs), probs


test_the_row_invariants_name_an_out_of_bound_and_an_unjournaled_write.plants_defects = True


def test_the_tripwire_denies_a_forged_journal_and_a_rename(tmp_path, _edges_write_tripwire):
    """An edge_event INSERT from outside the journal writer (a forged journal would satisfy the row invariant) and an
    ALTER TABLE renaming edges (research's S2-01 route) are DENIED on the store's connection."""
    from veracium.store import edge_events as _ee
    s = SqliteStore(str(tmp_path / "fj.db"))
    s.add_edge(_edge("f", S.Volatility.SLOW, 0.5))
    with pytest.raises(sqlite3.DatabaseError):
        with s._write_txn():
            _ee.append_event(s._conn, user_id=U, seq=99, txn=99, edge_id="f", kind="mutated", reason=None,
                             state="{}", recorded_at=NOW.isoformat())
    with pytest.raises(sqlite3.DatabaseError):
        s._conn.execute("ALTER TABLE edges RENAME TO edges_x")
    assert len(_edges_write_tripwire) == 2, _edges_write_tripwire
    _edges_write_tripwire.clear()
