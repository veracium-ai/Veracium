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
import importlib
import importlib.util
import inspect
import json
import math
import pathlib
import random
import re
import sqlite3
import symtable
import sys
import threading
import types

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
VAST = 10 ** 5000                      # round 4, R4-02: beyond the 4,300-digit rendering limit — `{value!r}` raised
REJECTED = [1.5, -0.1, float("nan"), float("inf"), float("-inf"), True, False, "0.5", None,
            math.nextafter(1.0, 2.0), math.nextafter(0.0, -1.0), HUGE, -HUGE, VAST, -VAST]


def _vid(v):
    """A cell id: `repr(v)` — every existing id unchanged — except the integers too long to print."""
    big = {HUGE: "+10**400", -HUGE: "-10**400", VAST: "+10**5000", -VAST: "-10**5000"}
    return big[v] if isinstance(v, int) and not isinstance(v, bool) and v in big else repr(v)
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
@pytest.mark.parametrize("value", [VAST, -VAST], ids=_vid)
def test_a_refusal_beyond_the_rendering_limit_names_the_field_and_the_value(field, value):
    """R4-02: beyond the interpreter's decimal-rendering limit the refusal is still §4A's ValueError, its message
    LEADING with the field and naming the value boundedly (sign and bit length); the process-wide limit is untouched."""
    limit = sys.get_int_max_str_digits()
    with pytest.raises(ValueError) as ex:
        MemoryConfig(**{field: value})
    msg = str(ex.value)
    assert msg.startswith(f"{field} must be") and f"an integer of {'+' if value > 0 else '-'}{value.bit_length()} bits" in msg
    assert len(msg) < 400 and sys.get_int_max_str_digits() == limit


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
                                          (HUGE, 0.3), (-HUGE, 0.3), (0.5, HUGE), (0.5, -HUGE),
                                          (VAST, 0.3), (-VAST, 0.3), (0.5, VAST), (0.5, -VAST)], ids=_vid)
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
# round 5 (R4-01 (a)): the write method's binding layout, frozen like the bodies and never rebound from anywhere
LAYOUT = "_JSON_LAYOUT"
PROTECTED = GUARDED + (LAYOUT,)
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
FROZEN = {METHOD: "b593ddefa27983b2b441be8cd9b98282ef4904a6fe7184d222c979c0ac7ae67a", DEFERRED: "f34451a125834bb07a97daad6febc2b328674410162d77f18867ad95c1b7f2d8",
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
# the migration ladder (0013's audited path): the same rules, except that a value fed by a parameter is listed for its
# reason and not held to the SELECT/PRAGMA head rule — its statements are the ladder's own tables of DDL and steps
MIGRATION_MODULES = {"veracium/store/migration.py", "veracium/store/schema_version.py"}
# round 5 (R4-01 (d)): each entry's BINDING — the containing function and the module/class binders of every name its
# value reads, followed into every function or method it reaches (`_sql_binding`; `_binding_digest`, sha256/16) —
# regenerated from the tree and re-reviewed when it moves
NONLITERAL_BINDING = {
    ('SqliteStore.__init__', 'bc3471530373188da9c30e0ba7e78b2d090076e469d28882db5b0d4698a09d11'): 'a007dac83ad5a192',
    ('SqliteStore._act_rows_where', 'cc00ad315a59e9575d3a838a0b388ca3610a764627bbbcab38e6e2cd49762c68'): 'db9f67ef1d767cb0',
    ('SqliteStore._attested_by_another_owner', 'eb2ba4c3290426945f64f55e532238461d5d9d44a5ee085a4f52645c927eeb3a'): 'd4fc7f5ee142b3a5',
    ('SqliteStore._attested_fields', 'b4446c6ae88d8497d190f8f13a92911f81cf0e25a5c0df840c605cad4633adbf'): '471eb25f14d333e4',
    ('SqliteStore._completed_attestation', 'ac4cc2426e52d922b8ed28e84effe37c30011850f64dd4452e744ad48eb150ab'): '4d491a150e8caa2a',
    ('SqliteStore._confirm_replay', '0fbc4fa0d37e8071b0b5d73055918b6efd7b50a9f1fe40d6c3d3b079ac40816c'): '45981a477261c709',
    ('SqliteStore._id_reserved', '39865061523d15e9bada3bba4afb270b89f19e430857060a14b8a6ae6efac59d'): 'd44dc55816e85de6',
    ('SqliteStore._load_op', '27d008897c48b8c107eb9520ec542b393921f9e25847f9c51fedc2edfb07af6d'): 'e8a2b28487621067',
    ('SqliteStore._ops_for_user', '2f505a5bb0ddb655bf46fa2ba3b0e786f2db13e1241afb349d9eb3adba2c4902'): '5201b8a46b469ae7',
    ('SqliteStore._redact_in_txn', '5647332e7211148b9ad5b71a487ab19b4c15e73a38f06d91cb309d3070fb9335'): 'c092f64467014f77',
    ('SqliteStore._redaction_record', 'c2aa0c6f503ee77f2f03c4cd951b3745a4d865b0e283306c915c53d5fbb16e05'): 'cd48256676379af6',
    ('SqliteStore._reply_replay', 'ebab35174f4bd03a186cdddb45260a877bf8623edb94965487f0a205325d2eac'): 'da23ba8b0553970b',
    ('SqliteStore._source_redacted', '29a9ff461c9d9dce95085ee23caaf9cf3005b1caa65b04eaaa213d5db57baa50'): '2799124cf5fa5c48',
    ('SqliteStore._surviving_derived', '3d9f2c553d81b34f9e0c3dae13bdce09ed08cd1a45de42c73e1c810fdaef9421'): '00fc3fe13f6cd5b6',
    ('SqliteStore._write_edge_row', '33f41f90a9a4e29967595c068ca002673821bcb52a03d702ab8f50612eae4c23'): '837cbf13ae6f3251',
    ('SqliteStore._write_op', 'b0447a31f610348c07a0930af4ffe437a4178a7e2f7cdc52d11e2e5d8753060b'): 'f33708a9b03795b5',
    ('SqliteStore.acted_edge_ids', 'b4820e17f1261cb74f4605d69f700b538e78998cf1b5c347ff27fcff8c8b43e3'): 'c6a8d350c8576df4',
    ('SqliteStore.active_challenges', '7aae11eef304bd121d26fa2bfe8557573f7bad633b1f0ac29ea9852f41560577'): '51ab4f0c4419ffc6',
    ('SqliteStore.add_reply', 'a2022f06b808b3a462a935471067cafc7535c753122add6c146aa954827fa400'): '16ce222052f71771',
    ('SqliteStore.commit_outcome_import_plan', '03827958ec7b7072aefe89448678674c9fc02886e4c4edb1311a054d9d8f4a2d'): '9c2d3144a3f87cbb',
    ('SqliteStore.commit_outcome_import_plan', '25a68e8dfc53a69efba960f40b99fc74fd55430b7a5d678e75be6ac3347e56eb'): '8b9ba230c6669e58',
    ('SqliteStore.commit_outcome_import_plan', '70905b22342c93513fc74ea1d16e4f11233b00789a3dd9f73bc874dac57eebc9'): '6d5a5fff8f0d0aec',
    ('SqliteStore.commit_outcome_import_plan', 'add6a203baf74ebdf25588d537da098d28d3d62b1dd80390be8daa6599b1fb04'): '6f9398b295171a36',
    ('SqliteStore.commit_outcome_import_plan', 'bce31bcedb2ea1608534e21b890939d2de16cd7611d1339fd4212f223c9af28d'): '6d5a5fff8f0d0aec',
    ('SqliteStore.commit_outcome_import_plan', 'e09d8261753337dde680071ab5bdc7e6175a5754f49b43053debc68f25e57da4'): '58ce5c12abef5978',
    ('SqliteStore.confirm_edge', '97ab04e41e08ed70ecdb71fc3252db4d341b4bda2cb224f3499c6142ae9ae628'): 'ed117a2c64ccf155',
    ('SqliteStore.confirm_notice', '5647332e7211148b9ad5b71a487ab19b4c15e73a38f06d91cb309d3070fb9335'): '9f164edab461b1c5',
    ('SqliteStore.confirm_notice', 'e47d7977d4c6808ad45f95d96520dcdbbba44b01614abab0dd7ce34fd79796d6'): '05623ef1b5666877',
    ('SqliteStore.confirmations_for', '6de03e078785d11fe4b34b9c39000a308103c9a26815b350347938403fc4eea6'): '17ed76defda31afb',
    ('SqliteStore.contributions', 'c1a33b453a06fc1a588f12603f9d30098c211b2f378a5aa76edf0dfc0c49e6ef'): 'f98d99163f1cec8b',
    ('SqliteStore.contributors_of_source', 'ff79d44b37b3604e5d6ef605c9bec3381dec33cb8f91d45a207c030863ae2a27'): '4c3df298fc8b4db1',
    ('SqliteStore.edge_events', 'ea84967ae8e3eeaac6eca15de3557d2ce972249021e2339bd2f233b1737a612e'): 'f952d758c62e895e',
    ('SqliteStore.edges', 'ea84967ae8e3eeaac6eca15de3557d2ce972249021e2339bd2f233b1737a612e'): '0c543259081195a0',
    ('SqliteStore.forget_user', '99b754925b96f9575742044fee438d82476f53a86a23cd0dd138a323fc044add'): 'a3396a908001aa71',
    ('SqliteStore.migration_outcomes', 'e8e50718b302ae192e9d7ec4f38f340869dceab25ea51999b09d66a1041cf291'): 'f759f8fe493a46ea',
    ('SqliteStore.migration_outcomes_by_uid', '0af9489795fdbff7246fc9b15f70bf20e45f07abc5cdb64638b5a4e429a4e3a4'): '72f22f204b4df4af',
    ('SqliteStore.policy_receipts', '33f41f90a9a4e29967595c068ca002673821bcb52a03d702ab8f50612eae4c23'): '93162dbd3567d5ad',
    ('SqliteStore.redact', 'e47d7977d4c6808ad45f95d96520dcdbbba44b01614abab0dd7ce34fd79796d6'): '0fa9218fe3cded6b',
    ('SqliteStore.redacted_targets', '6f6166079c03b2f9ad0b61e4d8ba0e1882ed1b32d1d221f124d45d4b67c39af6'): '3308dde1ffb62e56',
    ('SqliteStore.replies_for', '0e50f0c8b250ce20c7dcb393bdcbfc6c910b7099e5eb19b7c5a02ef0c64833d6'): 'c76c555fda255a01',
    ('SqliteStore.transition_consolidation_if_current', '5126e0419cd211f8dc948a7d1276927164e8eab4a076c2c872d1addc70fe9f09'): '1eee398d92ea435c',
}
# round 5, research's stage 2 (S2-01): the same rule for every OTHER src module's non-literal SQL argument, keyed
# ("<module>:<function>", sha256 of the expression) -> (times, its text, its binding). Wherever the connection travels
# — passed, or read off a passed store — SQL runs at a call, so the check sits at the call, on any receiver.
SRC_NONLITERAL = {
    ('veracium/doctor.py:_check_data_migration', '8e17d043b1b6ae8134b00ee61345e868571c8eb8e3d3d66bea3f97d7c92d4541'):
        (1, "q + (' AND i.user_id=?' if user else '') + ' ORDER BY i.edge_id'", 'dec94e9cf72b4fb8'),
    ('veracium/doctor.py:_check_data_migration', 'cf6e6f7f0a4468d3d52baba1a1eee4e2633ae33b3d6290b9a728377c0a3a5d34'):
        (1, "q + (' AND i.user_id=?' if user else '') + ' ORDER BY i.user_id'", 'dec94e9cf72b4fb8'),
    ('veracium/doctor.py:_check_data_migration', 'f06c89976436a13dfe55e75ea294ce4250614f108663f7864f0d457918086d97'):
        (1, "q + (' WHERE user_id=?' if user else '')", 'dec94e9cf72b4fb8'),
    ('veracium/doctor.py:_check_journal', 'bfdca166f562f1f95f4ac1877ac78f637f10b6ec44767e09996ed5fdc24f6df7'):
        (1, "f'SELECT DISTINCT user_id, edge_id FROM edge_event {where}'", '28b48aa6525f0e22'),
    ('veracium/doctor.py:_check_refs', '31e30ee2297326561188480017bac2db4a18bd117108e1211bc20d0774312c31'):
        (1, 'f"SELECT r.id FROM replies r LEFT JOIN replies c ON c.user_id = r.user_id AND c.id = r.tar', '2c310b21299c1260'),
    ('veracium/doctor.py:_check_refs', '37140b66979feb2e79aac0550b6e37bf99c6f8d62d6fdf5d338016bd4de23b04'):
        (1, "f'SELECT DISTINCT edge_id, user_id FROM edge_event {where}'", '2c310b21299c1260'),
    ('veracium/doctor.py:_check_refs', '4257d179728b8b0c3e099820ee15d75cc47e2998a6c7054e90ff6a5a6036f1d5'):
        (1, "f'SELECT id, user_id, edge_id FROM confirmations {where}'", '2c310b21299c1260'),
    ('veracium/doctor.py:_check_refs', '79df04d0ef1a255ae68f48ed8b84c2dea0201fac82739ea677fb240a907ded86'):
        (1, "f'SELECT DISTINCT episode_id, user_id FROM episode_event {where}'", '2c310b21299c1260'),
    ('veracium/doctor.py:_check_refs', '83b8971e0a2e6b27d567c87e361c6c0562ff426c1adb2710b33333bb907150f2'):
        (1, "f'SELECT id, user_id, target_kind, target_id, reason, event_ref, source_origin, source_use", '2c310b21299c1260'),
    ('veracium/doctor.py:_check_refs', '92549afc2b9edb51ecb80fc79841aa6bbb7dacadf65ac9a9652e738c9696cd2e'):
        (1, "f'SELECT id, user_id, survivor_type, survivor_id, contributor_type, contributor_ref FROM c", '2c310b21299c1260'),
    ('veracium/doctor.py:_check_refs', 'b7527025020dc60459241af8611d6fb771e2f7c7eaad6ad1106468314fa4085b'):
        (1, "f'SELECT id, user_id, edge_id FROM replies {where}'", '2c310b21299c1260'),
    ('veracium/doctor.py:_check_refs', 'ca4b102eebad13600163a82f70f966c3acb11866165e482c93917e3b72f282bd'):
        (1, "f'SELECT DISTINCT edge_id, user_id FROM edge_embedding {where}'", '2c310b21299c1260'),
    ('veracium/doctor.py:_live_restoration_origins', '2457f8481d7c284a56809efa46249a5191b2c0859200fc23ae29b609e7f508e5'):
        (1, '"SELECT user_id, edge_id, origin FROM migration_outcome WHERE outcome=\'restored\' AND undon', '527788fcf853149d'),
    ('veracium/doctor.py:_load_rows', '7fb37f163f2b7c4e05db81e28c7cebb33226627379e5998dff82000e46827890'):
        (1, "f'SELECT id, user_id, active, quarantined, json FROM edges {where}'", '9cc67749d8953e08'),
    ('veracium/doctor.py:_load_rows', 'dce6a89322ea2f08410b10bde9a08c6978544c2e4a5f2fc1dd815c1c25c7f036'):
        (1, "f'SELECT id, user_id, json FROM episodes {where}'", '9cc67749d8953e08'),
    ('veracium/store/edge_events.py:append_event', '3e25ffaa62d0012a435668ae6fb4c8bfa6b2122a6b3a1a824e1c1b850d45b70f'):
        (1, 'EVENT_INSERT_SQL', '00f9eeb97905ba10'),
    ('veracium/store/migration.py:_apply_forward', '7796f4f66361ff1cc7cafc731c207bb2ee15b9f7e1f47d8e4c79e9b8fb939d67'):
        (1, "f'PRAGMA user_version = {entry.step}'", 'bbda67fc10f5ecab'),
    ('veracium/store/migration.py:_apply_forward', '827d5abbca003d06e59d3546e7bf9189eb9b743f863a72df04b49929409ab8f7'):
        (1, 'entry.step', 'bbda67fc10f5ecab'),
    ('veracium/store/migration.py:_apply_forward', 'dc29d9ccfdb98bf9b34a25a44b096e4978cb32a6fb0a53246857c755bdd6f288'):
        (1, 'entry.step.ddl', 'bbda67fc10f5ecab'),
    ('veracium/store/migration.py:_data_arity_inventory', '52ae70d7758a2043598287bcf7e3c91641da51f67278f73fa05155c369ddc28c'):
        (1, "f'SELECT id, user_id, json FROM edges WHERE {named} ORDER BY id'", '3d63e4f075e13aea'),
    ('veracium/store/migration.py:_read_conf_after', '3f01b166ad2f4380f59e89aecde8502431db2a9604f8b46a5017aad3f9c4b070'):
        (1, "f'SELECT {_CONF_V15_COLS}, {_CONF_ACT_COLS} FROM confirmations'", '5c4ec00660075665'),
    ('veracium/store/migration.py:_read_conf_before', '5fd0dd2e27462e8513c5103e98f8f36c436273f2b6d777d11a31300cbe7911fd'):
        (1, "f'SELECT {_CONF_V15_COLS} FROM confirmations'", '3b5a397c92fd8f1d'),
    ('veracium/store/migration.py:_read_named_edges', '4a4fe4cc6f7dc95668bab05b8c6fa993bae999d2b47ab277793e1a320354b5de'):
        (1, "f'SELECT id, user_id, relation, active, json FROM edges WHERE {named}'", '1d0f2e4698ae9aba'),
    ('veracium/store/migration.py:_read_red_after', '2d110200e5595808793e3b6846c7c617b412b1e9c318c5f07fb3ee78ced6497c'):
        (1, "f'SELECT {_RED_V15_COLS}, state, pending_reason FROM redactions'", 'a3fbf8035cd1a883'),
    ('veracium/store/migration.py:_read_red_before', 'c0634dd354e5053a7fcf81a408092222722dba6046af6435842e1a58d3f8dff0'):
        (1, "f'SELECT {_RED_V15_COLS} FROM redactions'", '529d01c8ebc78cc9'),
    ('veracium/store/migration.py:_read_registry', 'b11a754c51fdd2817d36701eed6469279476290cf9e96146ab5f65acfd782496'):
        (1, "f'SELECT {_REGISTRY_COLS} FROM request_registry'", '6d05565b7c151322'),
    ('veracium/store/migration.py:_read_registry_before', 'b11a754c51fdd2817d36701eed6469279476290cf9e96146ab5f65acfd782496'):
        (1, "f'SELECT {_REGISTRY_COLS} FROM request_registry'", 'da614baa291f79c3'),
    ('veracium/store/migration.py:_rows', '33f41f90a9a4e29967595c068ca002673821bcb52a03d702ab8f50612eae4c23'):
        (1, 'sql', '15c100bc856f50f2'),
    ('veracium/store/migration.py:unattested_marker_report', '7bfafeef2fbae7cb3167a698387e39cba03e7e5160aa7ff3b3dccdb94a499062'):
        (1, "f'SELECT id, json FROM {table}'", '94e6c52ec53fa058'),
    ('veracium/store/revocation.py:redact_revocation_reasons', '9c8a2192ebccb54f1ae616fa397623c61b6828a14b3266616306f6bc8e09a6f8'):
        (1, 'f"UPDATE source_revocations SET reason=? WHERE user_id=? AND identity_digest=? AND reason<', 'c56a8f10500707bd'),
    ('veracium/store/schema_version.py:_feature_probes', '1b129df51e10002df77d69dd7c431df1fbe259667748e32c35d6aa0f65bc604e'):
        (1, 'marker', '3578532e379f2e4d'),
    ('veracium/store/schema_version.py:_near_miss_objects', '4b4c725a93da55a020217305a0fa4d593fba67b51151d9a97c3d5b1f4067c9f8'):
        (1, 'ddl', 'af61a1275a5189db'),
    ('veracium/store/schema_version.py:_repair_drift', '2118418edeb0136dc156a0bd7e2548e49c513c53059609b5d2cd13de6d1a0cc3'):
        (1, "f'DROP INDEX IF EXISTS {key[1]}'", '7936da4b7265b0f2'),
    ('veracium/store/schema_version.py:_repair_drift', '2af12ae0eb2811145ee94aa7ec6ad079f10a5f2d988af2cced31550ce41d1a1b'):
        (1, 'declared[key].ddl', '7936da4b7265b0f2'),
    ('veracium/store/schema_version.py:create', '36db0a761d117d0b8642c1deb33a0a415cde37727c9d97d42d35d253cfe5ef0a'):
        (1, 'o.ddl', '97ef93adf55329e6'),
    ('veracium/store/schema_version.py:manifest', 'e570e7c925fadb4580eb2e4ebaf2fe8b625768b9db63f9944145c77fef3f90b8'):
        (1, '_OBJECTS', '605a66d54de65139'),
    ('veracium/store/schema_version.py:open_versioned', 'bb4024dac0c6ee3c63c8899509bbacab1a9dc1dfc5c4b5d4f8f9caa0f999ebf9'):
        (2, "f'PRAGMA user_version = {target}'", '97fe282024360f8a'),
    ('veracium/store/schema_version.py:verify_reproduction', 'f1faaebed47e985137dd526dd1df36ee06707c126d20e91259e9583d40926338'):
        (1, 'd', '9b13912394de2129'),
}
# round 5 (W1): the names of sqlite3.Connection and sqlite3.Cursor, as 3.14 has them; the gate takes this UNION dir() so
# a name an older runtime lacks (3.10 has no blobopen) still refuses, and a name a newer one adds refuses unreviewed.
# ADMITTED is what src/ may touch: reads of a result, transaction control, and the exception classes. Everything else —
# blobopen above all, which writes a column with NO statement, so no authorizer callback sees it — refuses on any
# receiver in any src module.
DB_NAMES = {"DataError", "DatabaseError", "Error", "IntegrityError", "InterfaceError", "InternalError",
            "NotSupportedError", "OperationalError", "ProgrammingError", "Warning", "arraysize", "autocommit", "backup",
            "blobopen", "close", "commit", "connection", "create_aggregate", "create_collation", "create_function",
            "create_window_function", "cursor", "description", "deserialize", "enable_load_extension", "execute",
            "executemany", "executescript", "fetchall", "fetchmany", "fetchone", "getconfig", "getlimit",
            "in_transaction", "interrupt", "isolation_level", "iterdump", "lastrowid", "load_extension", "rollback",
            "row_factory", "rowcount", "serialize", "set_authorizer", "set_progress_handler", "set_trace_callback",
            "setconfig", "setinputsizes", "setlimit", "setoutputsize", "text_factory", "total_changes"}
DB_ADMITTED = {"DataError", "DatabaseError", "Error", "IntegrityError", "InterfaceError", "InternalError",
               "NotSupportedError", "OperationalError", "ProgrammingError", "Warning", "close", "commit",
               "fetchall", "fetchmany", "fetchone", "in_transaction", "isolation_level", "lastrowid", "rollback",
               "row_factory", "rowcount", "description", "execute", "executemany", "executescript"}
# the one same-named non-database read in src/: (module, containing function, receiver, attribute) -> that function's
# whole digest. Round 6: a receiver's spelling proves nothing (`import shutil as args`), so the function is reviewed
# and frozen, and the attribute may be read or passed but is never the function of a call
DB_NAME_EXCEPTIONS = {("veracium/cli.py", "_migrate", "args", "backup"): "a3449f0b50faa60c99970f93f188694ccbcde1ed853dcaa6d38992dff087b2a4"}
# round 5 (W2): callable accessors reach an attribute with no attribute node. src/ uses none, so all refuse, by
# attribute, by name and by import
ACCESSORS = {"attrgetter", "methodcaller", "getattr_static"}
# round 6, research's stage 2 (1a493ea3; the owner: "Close members too (Recommended)"). Every module src/ names and every
# member it reads of each, frozen: a list of import statements alone leaves an unlisted module one attribute away, since a
# listed module holds others (`urllib.request.string`, `enum.bltns`, `dataclasses.inspect`). A new use adds a row here.
SRC_IMPORTS = {
    "__future__": {"annotations"},
    "abc": {"ABC", "abstractmethod"},
    "anthropic": {"Anthropic"},
    "argparse": {"ArgumentParser"},
    "calendar": {"monthrange"},
    "collections": {"defaultdict"},
    "collections.abc": {"Mapping"},
    "contextlib": {"closing", "contextmanager", "nullcontext"},
    "contextvars": {"ContextVar"},
    "dataclasses": {"asdict", "dataclass", "field", "fields"},
    "datetime": {"date", "datetime", "timedelta", "timezone"},
    "enum": {"Enum"},
    "fcntl": {"LOCK_EX", "LOCK_NB", "LOCK_UN", "flock"},
    "hashlib": {"sha256"},
    "importlib.metadata": {"PackageNotFoundError", "version"},
    "json": {"JSONDecodeError", "JSONDecoder", "dump", "dumps", "load", "loads"},
    "logging": {"Formatter", "INFO", "Logger", "getLogger"},
    "logging.handlers": {"RotatingFileHandler"},
    "math": {"inf", "isfinite", "sqrt"},
    "mcp.server.fastmcp": {"FastMCP"},
    "mcp.server.mcpserver": {"MCPServer"},
    "msvcrt": {"LK_NBLCK", "LK_UNLCK", "locking"},
    "os": {"O_CREAT", "O_RDWR", "close", "environ", "fsencode", "fstat", "fsync", "getpid", "lseek", "lstat", "name", "open",
        "path", "replace", "write"},
    "os.path": {"basename", "exists", "isabs", "join", "realpath"},
    "pathlib": {"Path"},
    "platform": {"machine", "python_version", "system"},
    "pydantic": {"BaseModel", "Field", "StrictBool", "TypeAdapter", "ValidationError", "field_validator",
        "model_serializer", "model_validator"},
    "re": {"I", "compile", "escape", "findall", "finditer", "fullmatch", "match", "search", "split", "sub"},
    "secrets": {"token_bytes"},
    "shutil": {"copy2", "rmtree"},
    "sqlite3": {"Connection", "DatabaseError", "Error", "IntegrityError", "OperationalError", "Row", "connect",
        "sqlite_version"},
    "struct": {"error", "pack", "unpack", "unpack_from"},
    "sys": {"argv", "stderr", "stdin"},
    "tempfile": {"TemporaryDirectory", "mkdtemp"},
    "threading": {"Lock", "RLock", "Thread", "get_ident"},
    "time": {"monotonic", "perf_counter", "sleep", "time"},
    "traceback": {"format_exception"},
    "types": {"MappingProxyType"},
    "typing": {"Any", "Callable", "Literal", "Mapping", "NamedTuple", "Optional", "Protocol", "TYPE_CHECKING",
        "get_args", "runtime_checkable"},
    "urllib": {"parse", "request"},
    "urllib.parse": {"quote_from_bytes"},
    "urllib.request": {"Request", "urlopen"},
    "uuid": {"UUID", "uuid4"},
    "warnings": {"warn"},
    "weakref": {"WeakKeyDictionary"},
}
# every dunder src/ reads: `__globals__`, `__builtins__`, `__match_args__`, `__annotations__` and the rest fall outside it
SRC_DUNDERS = {"__all__", "__cause__", "__file__", "__func__", "__getitem__", "__init__", "__name__",
               "__new__", "__setattr__", "__slots__", "__store_mutator__", "__str__", "__traceback__"}
# names src/ does not use, each reaching a namespace, a module or an evaluator whatever holds it
REACH_NAMES = {"globals", "import_module", "locals", "model_rebuild"}
# an attribute name src/ does not read: `pathlib.Path.parser` is `posixpath`, a module the member walk cannot see through a
# class (research, 9e5daf2f). A plain name is not refused: src/'s `parser` variables are argparse's
REACH_ATTRIBUTES = {"parser"}
# round 6 (research's read): the two `__import__` calls, each frozen with the attribute read on it. (module, function) -> digest
IMPORT_SITES = {("veracium/portability.py", "import_memory"):
                    "bc26b86e08e26b357106adbe7551a63ea74a1c4f035a83779a68c3ae05b15ce4",
                ("veracium/schema.py", None):
                    "d5956fdb940525256bc1066ba504b6dcd866ccf1159e70741dba3017f501e027"}
# a class's attribute that holds a module: the walk stops at a class, so each is named here and refused by name above
CLASS_HELD_MODULES = {("pathlib", "Path", "parser")}
# rows the runtime audit cannot import on every lane: a platform's module or an optional extra. The tables stay AST-only
UNAUDITED_MODULES = {"anthropic", "fcntl", "mcp.server.fastmcp", "mcp.server.mcpserver", "msvcrt"}
# the one own module src/ passes as a value: (module, function, name) -> that function's whole digest
OWN_MODULE_VALUES = {("veracium/store/sqlite.py", "SqliteStore.upsert_embedding", "_semantic"):
                     "d0b51a22f785ffdcd824b47053465f2c18ba99850f7ec8eee235ea605a50ebe1"}
# pydantic evaluates a string it is handed as a type, so its one call here is frozen: (module, function) -> the call's digest
TYPE_ADAPTER_SITE = {("veracium/store/migration.py", "_typed"):
                     "85b8cdbe11b38e63e227521d86d087a4432bb0075ae20d6f9d9ee19b350581fe"}
# round 5 (R4-01 (a)): the frozen statement binding _JSON_LAYOUT in sqlite.py
FROZEN_LAYOUT = "1656bcdef030866f5bec4be139413ac460b0b77bcbba747356d3f25ecd1e8472"
# round 5 (R4-01 (b), research's B2): the connection's closed non-SQL uses — exactly the pin's. `create_function`,
# `set_authorizer`, `total_changes`, `cursor`, `backup`, `iterdump` and the rest are absent, so they refuse: a user
# function is how an unread statement can write ((c)'s witness), and `set_authorizer(None)` would remove the test
# fixture's runtime authorizer
CONN_CALLS = {"commit", "rollback", "close"}
CONN_READS = {"in_transaction"}
# THE BINDING INVENTORY (round 3's, restored and counted): every pass of the connection to a function, keyed
# (calling function, "arg:<callee name>") -> (times, the import the name must be bound by, the reason). Whether each
# callee can write edges.json: `test_the_connection_inventorys_callees_hold` reads each one's body.
INVENTORY = {
    ("SqliteStore.__init__", "arg:open_versioned"): (1, ".schema_version:open_versioned",
        "the 0007/0013 versioned open (DDL, the stamp, the migration ladder): MIGRATION SCOPE — an edges rewrite there "
        "is 0013's audited migration, outside 0048's maintenance writers; N4c's tripwire covers the package"),
    ("SqliteStore._journal_edge_write", "arg:next_txn"): (1, ".edge_events:next_txn",
        "store.edge_events: the 0029 journal's allocation read; no edges write"),
    ("SqliteStore._journal_edge_write", "arg:mint_recorded_at"): (1, ".edge_events:mint_recorded_at",
        "store.edge_events: the journal's clock mint; no edges write"),
    ("SqliteStore._journal_edge_write", "arg:next_seq"): (1, ".edge_events:next_seq",
        "store.edge_events: the journal's sequence read; no edges write"),
    ("SqliteStore._journal_edge_write", "arg:append_event"): (1, ".edge_events:append_event",
        "store.edge_events: appends to edge_event, never to edges"),
    ("SqliteStore.standing_revocations", "arg:_standing"): (1, ".revocation:standing_revocations",
        "store.revocation: a SELECT on source_revocations; no edges write"),
    ("SqliteStore._redact_in_txn", "arg:_redact_revocation_reasons"): (1, ".revocation:redact_revocation_reasons",
        "store.revocation: UPDATE of source_revocations' reason column; no edges write"),
    ("SqliteStore._redact_in_txn", "arg:_revocation_reason_marked"): (1, ".revocation:revocation_reason_marked",
        "store.revocation: a SELECT on source_revocations; no edges write"),
}


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


def _bound_names(n):
    """The names node `n` BINDS, in every statement form Python has (the one rule `_binders` and `_Binders` share)."""
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        yield n.name
    elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
        yield n.id                     # Assign/AnnAssign/AugAssign/For/With/NamedExpr/comprehension/Delete targets
    elif isinstance(n, ast.alias):
        yield n.asname or n.name.split(".")[0]
    elif isinstance(n, ast.arg):
        yield n.arg
    elif isinstance(n, ast.ExceptHandler) and n.name:
        yield n.name
    elif isinstance(n, (ast.Global, ast.Nonlocal)):
        yield from n.names
    elif isinstance(n, (ast.MatchAs, ast.MatchStar)) and n.name:
        yield n.name
    elif isinstance(n, ast.MatchMapping) and n.rest:
        yield n.rest
    elif hasattr(ast, "TypeVar") and isinstance(n, (ast.TypeVar, ast.ParamSpec, ast.TypeVarTuple)):
        yield n.name


def _binders(tree, name):
    """Every node that BINDS `name` anywhere in the tree, in every statement form Python has."""
    return [n for n in ast.walk(tree) if name in _bound_names(n)]


_CLASSIFIER = []
_CLASSIFIED = {}
# round 5, research's recheck (R-01): routes around the store's own schema. A TEMP table named `edges` shadows main.edges
# for the connection, so reads and unqualified writes go to a table no journal, trigger rule or teardown invariant
# sees; ATTACH, ALTER outside main and writable_schema are the class's neighbours. A direct write to a schema table needs
# no rule: with writable_schema off SQLite refuses to prepare it ("may not be modified"), so it is UNRESOLVED.
PIN_PRAGMAS = {"quick_check", "user_version", "compile_options"}     # the literal PRAGMAs src/ uses


def _schema_route(action, a1, a2, db) -> bool:
    """One authorizer callback that leaves the store's schema: any database but main, ATTACH or DETACH, ALTER outside
    main (ALTER reports its database in a1, not db), or writable_schema. Used at prepare by the classifier and at run
    time by the tripwire."""
    return (db not in (None, "main") or action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH)
            or (action == sqlite3.SQLITE_ALTER_TABLE and a1 != "main")
            or (action == sqlite3.SQLITE_PRAGMA and str(a1).lower() == "writable_schema"))
# research's stage-1b catch (2026-11-03): a trigger's body writes are reported only when a statement that FIRES it is
# prepared, never at CREATE TRIGGER, so a trigger or a view is refused as such, wherever it is created
_TRIGGER_OR_VIEW = {sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_CREATE_TEMP_TRIGGER, sqlite3.SQLITE_CREATE_VIEW,
                    sqlite3.SQLITE_CREATE_TEMP_VIEW}


# 0048 round 5 (R4-01 (c)), round 6 (R5-02): the statement is COMPILED under `EXPLAIN QUERY PLAN` and never run, so the
# authorizer sees every action and nothing steps, whatever the runtime's variable limit is (the qualified runtime
# allows 250000, so a count alone could not promise a refusal, and a statement with exactly that many parameters ran).
# Not plain `EXPLAIN`: `EXPLAIN QUERY PLAN` is a production of its own, so `QUERY PLAN x` would prepare under it, where
# SQLite refuses it bare. This production cannot repeat. Over-binding remains how the parameter count is read: CPython
# checks it before the first step, with exactly this message. Any other failure (a missing function, table or
# collation, a syntax error, two statements) is a statement SQLite did not read: UNRESOLVED, never "no write".
_PREPARE = "EXPLAIN QUERY PLAN "
_OVERBIND = 32767
_BIND_COUNT = re.compile(r"Incorrect number of bindings supplied\. The current statement uses (\d+), and there are "
                         + str(_OVERBIND) + r" supplied\.")
UNRESOLVED = "unresolved"
_PARAMS = {}


def _classifier_conn():
    if not _CLASSIFIER:
        from veracium.store import schema_version as _sv
        # NO statement cache: a cached statement is not re-prepared, so the authorizer would not be asked again
        c0 = sqlite3.connect(":memory:", isolation_level=None, cached_statements=0)
        c0.execute("BEGIN")
        _sv.create(c0, _sv.SCHEMA_VERSION)
        c0.execute("COMMIT")
        _CLASSIFIER.append(c0)
    return _CLASSIFIER[0]


def _sqlite_classify(sql: str) -> set:
    """SQLite's own reading of a statement, not a keyword: COMPILE it under an authorizer against an in-memory store at
    the head schema and record each (action, table, column) — the prepare asks once per updated column. Returns the
    subset of {"edges-insert", "edges-json-update", "trigger-or-view", UNRESOLVED} the reading gives; UNRESOLVED when
    the statement did not prepare (round 5, R4-01 (c): an unknown function is not an empty write set)."""
    if sql in _CLASSIFIED:
        return set(_CLASSIFIED[sql])
    c = _classifier_conn()
    seen = []

    def auth(action, a1, a2, db, trigger):
        seen.append((action, a1, a2, db))     # SQLite asks once per updated COLUMN: every one must be seen
        return sqlite3.SQLITE_OK
    c.set_authorizer(auth)
    prepared = False
    try:
        c.execute(_PREPARE + sql, (None,) * _OVERBIND).close()
        prepared, _PARAMS[sql] = True, _OVERBIND      # it binds exactly that many: only the plan listing ran
    except Exception as ex:                  # every outcome is read, not only the database's own errors
        m = _BIND_COUNT.fullmatch(str(ex)) if type(ex) is sqlite3.ProgrammingError else None
        if m:
            prepared, _PARAMS[sql] = True, int(m.group(1))
    finally:
        c.set_authorizer(None)
        if c.in_transaction:                 # never reached by a statement that only prepared: kept as a backstop
            c.execute("ROLLBACK")
    tags = set() if prepared else {UNRESOLVED}
    for action, a1, a2, db in seen:
        if action in _TRIGGER_OR_VIEW:
            tags.add("trigger-or-view")
        if action in (sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_DROP_TABLE) and "edges" in (a1, a2):
            tags.add("trigger-or-view")      # research's stage 2, S2-01: renaming edges routes a write around it
        if action == sqlite3.SQLITE_INSERT and a1 == "edges":
            tags.add("edges-insert")
        elif action == sqlite3.SQLITE_UPDATE and a1 == "edges" and a2 == "json":
            tags.add("edges-json-update")
        if _schema_route(action, a1, a2, db) or (action == sqlite3.SQLITE_PRAGMA and str(a1).lower() not in PIN_PRAGMAS):
            tags.add("schema-route")
    # a flag PRAGMA takes effect AT PREPARE (`PRAGMA writable_schema=ON` sets the flag with nothing run), so one outside
    # the pin's set would change how every later statement reads: the scratch connection is thrown away after it
    if any(a == sqlite3.SQLITE_PRAGMA and str(x).lower() not in PIN_PRAGMAS for a, x, _y, _d in seen):
        c.close()
        _CLASSIFIER.clear()
    _CLASSIFIED[sql] = frozenset(tags)
    return tags


def _param_count(sql: str) -> int:
    """The statement's parameter count, as SQLite reports it after the prepare (the binding-count refusal)."""
    assert UNRESOLVED not in _sqlite_classify(sql), sql
    return _PARAMS[sql]


_LAYOUT_DERIVED = []


def _derive_one(sql: str) -> tuple:
    """(parameters, json index) of ONE statement, by execution (research's B4 recipe; see `_derived_layout`)."""
    from veracium.store import schema_version as _sv
    n = _param_count(sql)
    c = sqlite3.connect(":memory:", isolation_level=None)
    c.execute("BEGIN")
    _sv.create(c, _sv.SCHEMA_VERSION)
    c.execute("COMMIT")
    c.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,quarantined,json) "
              "VALUES('S0','u','s','r','o',1,0,'{}')")
    hits = []
    for k in range(n):
        vals = ["S0"] * n
        vals[k] = '{"probe": %d}' % k
        c.execute("SAVEPOINT p")
        try:
            c.execute(sql, vals)
            if vals[k] in {r[0] for r in c.execute("SELECT json FROM edges")}:
                hits.append(k)
        except sqlite3.DatabaseError:
            pass
        c.execute("ROLLBACK TO p")
        c.execute("RELEASE p")
    c.close()
    assert len(hits) == 1, (sql, hits)
    return n, hits[0]


def _derived_layout() -> frozenset:
    """R4-01 (a), research's B4 recipe: each closed statement's json position BY EXECUTION — a scratch store at the head
    schema, one seeded row; for each position k, a distinct JSON sentinel at k and the seed id everywhere else; the k
    whose sentinel lands in edges.json is the json position. Exactly one k per statement, or this refuses."""
    if _LAYOUT_DERIVED:
        return _LAYOUT_DERIVED[0]
    out = set()
    for sql in sorted(CLOSED_SQL):
        n, k = _derive_one(sql)
        out.add((sql, n, k))
    _LAYOUT_DERIVED.append(frozenset(out))
    return _LAYOUT_DERIVED[0]


_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


class _Binders:
    """`_binders(sub, name)` for many names over one tree, from ONE walk with the same rule (`_bound_names`), restricted
    to the subtree `sub` by node identity."""

    def __init__(self, tree):
        self.by_name, self._ids, self._digests, self.self_stores = {}, {}, {}, {}
        for n in ast.walk(tree):
            for name in _bound_names(n):
                self.by_name.setdefault(name, []).append(n)
            if (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self"
                    and isinstance(n.ctx, (ast.Store, ast.Del))):
                self.self_stores.setdefault(n.attr, []).append(n)    # `self.X = …` / `del self.X`

    def digest(self, node):
        d = self._digests.get(id(node))
        if d is None:
            d = self._digests[id(node)] = _digest(node)
        return d

    def ids(self, sub):
        ids = self._ids.get(id(sub))
        if ids is None:
            ids = self._ids[id(sub)] = {id(x) for x in ast.walk(sub)}
        return ids

    def of(self, sub, name):
        ids = self.ids(sub)
        return [b for b in self.by_name.get(name, []) if id(b) in ids]


def _scope_of(node, parent):
    """The innermost def, class or lambda enclosing `node` (None: the module)."""
    while node in parent:
        node = parent[node]
        if isinstance(node, _SCOPES):
            return node
    return None


def _stmt_of(node, parent, holder):
    """The statement directly in `holder`'s body that contains `node`."""
    while parent.get(node) is not holder:
        node = parent[node]
    return node


def _value_of_binder(b, parent):
    """The expression a local binder takes its value from; None for a parameter (round 5, R4-01 (d))."""
    if isinstance(b, ast.arg):
        return None
    x = b
    while x in parent:
        pnode = parent[x]
        if isinstance(pnode, (ast.Assign, ast.AnnAssign, ast.NamedExpr)) and x is not pnode.value:
            return pnode.value
        if isinstance(pnode, ast.AugAssign):
            return pnode
        if isinstance(pnode, (ast.For, ast.AsyncFor, ast.comprehension)) and x is pnode.target:
            return pnode.iter
        if isinstance(pnode, ast.withitem) and x is pnode.optional_vars:
            return pnode.context_expr
        if isinstance(pnode, ast.stmt):
            return pnode
        x = pnode
    return b


def _sql_binding(tree, parent, fnode, expr, idx=None):
    """R4-01 (d), research's B3: what determines a non-literal SQL value — the names it reads, followed through their
    local definitions in the containing function: (parameters reached, {module name: binder digests},
    {self attribute: binder digests}). Module and class binders are the statements that bind the name at that scope;
    a name with no module binder is a builtin and records []. RECURSIVE: when a binder is a function or method (the
    value calls it), the module names and self attributes ITS body reads are followed the same way, to closure — a
    changed helper two calls down moves the binding like a changed constant."""
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SqliteStore"), None)
    idx = idx or _Binders(tree)
    params, mod, attrs = set(), {}, {}

    def local_reads(func, start):
        """(module names, self attributes, parameters) `start` reads, through `func`'s local definitions."""
        g, a, ps, todo, seen, done = set(), set(), set(), [start], set(), set()
        while todo:
            node = todo.pop()
            for x in ast.walk(node):
                if (isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == "self"
                        and isinstance(x.ctx, ast.Load)):
                    a.add(x.attr)
                if not (isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)) or x.id == "self" or x.id in done:
                    continue
                done.add(x.id)
                local = [b for b in idx.of(func, x.id) if b is not func] if func is not None else []
                if not local:
                    g.add(x.id)
                for b in local:
                    v = _value_of_binder(b, parent)
                    if v is None:
                        ps.add(x.id)
                    elif id(v) not in seen:
                        seen.add(id(v))
                        todo.append(v)
        return g, a, ps

    g, a, params = local_reads(fnode, expr)
    work = [("mod", n) for n in g] + [("self", n) for n in a]
    while work:
        kind, name = work.pop()
        if (mod if kind == "mod" else attrs).get(name) is not None:
            continue
        if kind == "mod":
            stmts = [_stmt_of(b, parent, tree) for b in idx.of(tree, name) if _scope_of(b, parent) is None]
        elif cls is None:
            stmts = []
        else:
            stmts = [_stmt_of(b, parent, cls) for b in idx.of(cls, name) if _scope_of(b, parent) is cls and b is not cls]
            cls_ids = idx.ids(cls)
            for x in idx.self_stores.get(name, []):     # `self.X = …` in a method: the statement that stores it
                if id(x) in cls_ids:
                    while not isinstance(x, ast.stmt):
                        x = parent[x]
                    stmts.append(x)
        (mod if kind == "mod" else attrs)[name] = sorted(idx.digest(s) for s in stmts)
        for s in stmts:                                 # a function the value reaches: follow what IT reads
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
                g2, a2, _p = local_reads(s, s)
                work += [("mod", n) for n in g2 if n not in mod] + [("self", n) for n in a2 if n not in attrs]
    return sorted(params), mod, attrs


def _binding_digest(tree, parent, fnode, expr, binding=None, idx=None) -> str:
    params, mod, attrs = binding or _sql_binding(tree, parent, fnode, expr, idx)
    blob = json.dumps([(idx.digest if idx else _digest)(fnode), params, mod, attrs], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _leading_constant(expr, local=None):
    """The SQL text an expression begins with, when a constant fixes it (else None). `local(name)` gives a local name's
    assigned values: a name counts when EVERY binder of it opens with the same statement kind."""
    if isinstance(expr, ast.Name) and local is not None:
        heads = [_leading_constant(v) for v in local(expr.id)]
        return heads[0] if heads and all(h and _PARAM_HEAD.match(h) for h in heads) else None
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    if isinstance(expr, ast.JoinedStr) and expr.values and isinstance(expr.values[0], ast.Constant):
        return expr.values[0].value
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        return _leading_constant(expr.left, local)
    if (isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute) and expr.func.attr == "format"
            and not expr.keywords):
        return _leading_constant(expr.func.value, local)
    return None


# R4-01 (d), the head rule for a non-literal whose value a PARAMETER reaches (research's B3): its leading constant fixes
# the statement as a SELECT, or as a PRAGMA whose name is fixed — neither writes a table (one statement per execute;
# no user function can be registered, (b))
_PARAM_HEAD = re.compile(r"\s*(SELECT\s|PRAGMA\s+\w+\s*=)", re.I)


def _act_table_insert(fnode, expr) -> bool:
    """The one other form a parameter may reach: `INSERT INTO {T}(…)` whose table T is, in the same function, preceded by
    a `self._ACT_COLUMNS[T]` lookup — which raises unless T is one of the frozen ACT_TABLES (5c), none of them
    edges. Matched by the expression's own shape, not by the function's name. "Preceded" is by line, in the same
    function: the gate does not prove the lookup dominates the execute (the frozen function digest binds the order)."""
    if not (isinstance(expr, ast.JoinedStr) and len(expr.values) >= 2 and isinstance(expr.values[0], ast.Constant)
            and re.fullmatch(r"\s*INSERT\s+INTO\s*", expr.values[0].value, re.I)
            and isinstance(expr.values[1], ast.FormattedValue)):
        return False
    want = ast.dump(expr.values[1].value)
    return any(isinstance(x, ast.Subscript) and isinstance(x.value, ast.Attribute) and x.value.attr == "_ACT_COLUMNS"
               and isinstance(x.value.value, ast.Name) and x.value.value.id == "self" and ast.dump(x.slice) == want
               and x.lineno <= expr.lineno for x in ast.walk(fnode))


def _import_target(tree, parent, fnode, name, idx=None):
    """The `module:attr` a callee name is bound to by an import, in the calling function or at module level; None
    when any binder of the name is not such an import."""
    idx = idx or _Binders(tree)
    bs = [b for b in idx.of(fnode, name) if b is not fnode] or [
        b for b in idx.of(tree, name) if _scope_of(b, parent) is None]
    out = set()
    for b in bs:
        imp = parent.get(b)
        if not (isinstance(b, ast.alias) and isinstance(imp, ast.ImportFrom)):
            return None
        out.add(f"{'.' * imp.level}{imp.module}:{b.name}")
    return out.pop() if len(out) == 1 else None


def _derived_layout_by_digest() -> frozenset:
    """The derived layout as sqlite.py keys it: (sha256 of the statement, parameters, json index)."""
    return frozenset((hashlib.sha256(s.encode()).hexdigest(), n, j) for s, n, j in _derived_layout())


def _gate(source: str, others: dict | None = None) -> list:
    """N4f (a), round 4 (R3-02, (a′)), over sqlite.py's source: the problems, or []. `others` maps the OTHER src/
    modules' relative paths to their source (for the attribute and class rules); None reads them from disk."""
    tree = ast.parse(source)
    q = _qualnames(tree)
    parent = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
    idx = _Binders(tree)
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
        b = idx.of(tree, name)
        if len(b) != 1 or not isinstance(b[0], (ast.FunctionDef, ast.ClassDef)) or b[0] not in tree.body:
            bad.append(f"{name}: bound {len(b)} time(s) in sqlite.py ({[at(x) for x in b]}) — exactly its one "
                       f"module-level definition may bind it")
    for name in (METHOD, JOURNAL):
        b = idx.of(tree, name)
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
        for name in (HELPER, DEFERRED, LAYOUT):
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
    # 2b. the binding layout (round 5, R4-01 (a)): ONE module-level binder, its statement frozen, its value the layout
    # SQLite gives BY EXECUTION, and read only by the write method
    lb = idx.of(tree, LAYOUT)
    asg = parent.get(lb[0]) if len(lb) == 1 else None
    if not (isinstance(asg, ast.Assign) and asg in tree.body and len(asg.targets) == 1 and asg.targets[0] is lb[0]):
        bad.append(f"{LAYOUT}: bound {len(lb)} time(s) ({[at(x) for x in lb]}) — exactly one module-level assignment "
                   f"may bind it")
    else:
        if _digest(asg) != FROZEN_LAYOUT:
            bad.append(f"{LAYOUT}: its statement is not the frozen one (digest {_digest(asg)[:16]}…) — re-review it")
        try:
            val = ast.literal_eval(asg.value)
        except (ValueError, SyntaxError, TypeError):
            val = None
        if not (isinstance(val, tuple) and len(set(val)) == len(val) and set(val) == _derived_layout_by_digest()):
            bad.append(f"{LAYOUT}: its value is not the layout SQLite gives by execution")
    refs = [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == LAYOUT and isinstance(n.ctx, ast.Load)]
    if [q.get(id(r)) for r in refs] != [f"SqliteStore.{METHOD}"]:
        bad.append(f"{LAYOUT}: read at {[at(r) for r in refs]} — exactly once, by the write method")
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
                    if isinstance(x, ast.Attribute) and x.attr in PROTECTED:
                        bad.append(f"{rel} {at(n)}: `{x.attr}` assigned or deleted as an attribute")
            # research's stage 2, S2-02: `setattr(SqliteStore, "_write_edge_row", …)` from another module
            if (isinstance(n, ast.Call) and (getattr(n.func, "id", None) in ("setattr", "delattr")
                                             or getattr(n.func, "attr", None) in ("setattr", "delattr"))
                    and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and n.args[1].value in PROTECTED):
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
            elif UNRESOLVED in _sqlite_classify(sql.value):
                bad.append(f"{at(n)}: `{METHOD}`'s sql did not prepare: SQLite has not read it ({where})")
            elif not (_sqlite_classify(sql.value) & {"edges-insert", "edges-json-update"}):
                bad.append(f"{at(n)}: `{METHOD}`'s sql is not, by SQLite's reading, an edges json write ({where})")
            # round 5 (R4-01 (a)): the captured bytes reach the statement's json parameter and no other — before and
            # after are tuple displays whose lengths are the layout SQLite gives by execution
            if len(call.args) == 4:
                b4, af = call.args[1], call.args[3]
                if not all(isinstance(x, ast.Tuple) and not any(isinstance(e, ast.Starred) for e in x.elts)
                           for x in (b4, af)):
                    bad.append(f"{at(n)}: `{METHOD}`'s before/after are not tuple displays of fixed length ({where})")
                elif (isinstance(sql, ast.Constant) and (sql.value, len(b4.elts) + 1 + len(af.elts), len(b4.elts))
                      not in _derived_layout()):
                    bad.append(f"{at(n)}: `{METHOD}`'s binding layout puts the captured json at parameter "
                               f"{len(b4.elts)} of {len(b4.elts) + 1 + len(af.elts)}, not at the statement's json "
                               f"position ({where})")
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
    # 5a'. every connection reference resolves (round 5, R4-01 (b); research's B1/B2): no cursor and no `.connection`
    # anywhere in the module; an execute-family attribute on ANY receiver is the function of a direct call — never
    # held, passed or returned; and every `self._conn` is a direct execute-family call (its SQL read below), one of the
    # closed non-SQL uses, the one binder in __init__, or a counted, reasoned pass in the inventory
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and n.attr in ("connection", "cursor"):
            bad.append(f"{at(n)}: `.{n.attr}` in the store module — a cursor or its connection is not resolved "
                       f"({q.get(id(n), '<module>')})")
        if (isinstance(n, ast.Attribute) and n.attr in SQL_CALLS
                and not (isinstance(parent.get(n), ast.Call) and parent[n].func is n)):
            bad.append(f"{at(n)}: `.{n.attr}` held, passed or returned, not called ({q.get(id(n), '<module>')})")
    passes = {}
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Attribute) and n.attr == "_conn" and isinstance(n.value, ast.Name)
                and n.value.id == "self"):
            continue
        where, pn = q.get(id(n), "<module>"), parent.get(n)
        if isinstance(n.ctx, (ast.Store, ast.Del)):
            if not (where == "SqliteStore.__init__" and isinstance(pn, ast.Assign) and pn.targets == [n]):
                bad.append(f"{at(n)}: the connection bound outside its one assignment in __init__ ({where})")
            passes["<binder>"] = passes.get("<binder>", 0) + 1
            continue
        if isinstance(pn, ast.Attribute) and pn.value is n:
            called = isinstance(parent.get(pn), ast.Call) and parent[pn].func is pn
            if called and pn.attr in SQL_CALLS:
                continue
            if called and pn.attr in CONN_CALLS and not parent[pn].args and not parent[pn].keywords:
                continue
            if not called and pn.attr in CONN_READS and isinstance(pn.ctx, ast.Load):
                continue
            bad.append(f"{at(n)}: `self._conn.{pn.attr}` in a form the gate does not resolve ({where})")
            continue
        if isinstance(pn, ast.Call) and n in pn.args and isinstance(pn.func, ast.Name):
            key = (where, f"arg:{pn.func.id}")
            fnode = _scope_of(n, parent)
            if key not in INVENTORY:
                bad.append(f"{at(n)}: the connection passed to `{pn.func.id}`, not in the inventory ({where})")
            elif _import_target(tree, parent, fnode, pn.func.id, idx) != INVENTORY[key][1]:
                bad.append(f"{at(n)}: `{pn.func.id}` is not bound to the inventory's "
                           f"{INVENTORY[key][1]} ({where})")
            passes[key] = passes.get(key, 0) + 1
            continue
        bad.append(f"{at(n)}: the connection reached in a form the gate does not resolve ({where})")
    if passes.get("<binder>") != 1:
        bad.append(f"the connection is bound {passes.get('<binder>', 0)} time(s), not once")
    for key, (count, _target, _reason) in INVENTORY.items():
        if passes.get(key, 0) != count:
            bad.append(f"inventory entry {key} is reached {passes.get(key, 0)} time(s), the inventory says {count}")
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
            if UNRESOLVED in tags:
                bad.append(f"{at(n)}: a statement SQLite did not prepare ({where}): {' '.join(a0.value.split())[:70]}")
            if "schema-route" in tags:
                bad.append(f"{at(n)}: a route around the store's schema ({where}): {' '.join(a0.value.split())[:70]}")
            if tags & {"edges-insert", "edges-json-update"}:
                bad.append(f"{at(n)}: an edges json write executed directly, not through `{METHOD}` ({where}): "
                           f"{' '.join(a0.value.split())[:70]}")
            if n.func.attr == "executescript":
                bad.append(f"{at(n)}: executescript in the store module ({where})")
            continue
        key = (where, _digest(a0))
        if key not in NONLITERAL:
            bad.append(f"{at(n)}: a non-literal SQL site not in the reviewed list ({where}): {ast.unparse(a0)[:80]}")
        else:
            # round 5 (R4-01 (d)): the entry binds what determines the value — the containing function and the module
            # and class binders of every name the value reads — and a value a parameter reaches is a SELECT or a
            # fixed PRAGMA by its leading constant (the write method's own `sql`: its callers' literals, above)
            fnode = _scope_of(n, parent)
            binding = _sql_binding(tree, parent, fnode, a0, idx)
            got = _binding_digest(tree, parent, fnode, a0, binding, idx)
            if got != NONLITERAL_BINDING.get(key):
                bad.append(f"{at(n)}: what determines the non-literal SQL at {key[0]} changed (binding {got}) — "
                           f"re-review it ({ast.unparse(a0)[:60]})")
            params = binding[0]
            if (params and where != f"SqliteStore.{METHOD}" and not _PARAM_HEAD.match(_leading_constant(a0) or "")
                    and not _act_table_insert(fnode, a0)):
                bad.append(f"{at(n)}: a parameter ({', '.join(params)}) reaches SQL whose leading constant does not "
                           f"fix a SELECT or a named PRAGMA ({where}): {ast.unparse(a0)[:60]}")
        seen_nonlit[key] = seen_nonlit.get(key, 0) + 1
    # COUNTED (research's stage 2): a second site with an identical expression in the same function is not admitted
    # by the first one's entry
    if set(NONLITERAL_BINDING) != set(NONLITERAL):
        bad.append(f"the non-literal list and its bindings disagree: {sorted(set(NONLITERAL) ^ set(NONLITERAL_BINDING))}")
    for key, (count, _text) in NONLITERAL.items():
        if seen_nonlit.get(key, 0) != count:
            bad.append(f"non-literal site {key} occurs {seen_nonlit.get(key, 0)} time(s), the reviewed list says {count}")
    bad += _package_problems(source, tree, parent, idx, others)
    return bad


_PARSED = {}


def _parsed(text: str):
    """(tree, parent map, qualnames, binder index) of one module's text. Read-only by every caller, so cached by text."""
    got = _PARSED.get(text)
    if got is None:
        tree = ast.parse(text)
        got = _PARSED[text] = (tree, {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}, _qualnames(tree),
                               _Binders(tree))
    return got


def _exec_callee(call, names):
    """The derived execute-family name a call reaches, on ANY receiver, or None. Round 6 (R5-01): no receiver is exempt
    by its spelling. The one method that shared the name was renamed, so no resolving or reviewing is left to do."""
    f = call.func
    name = getattr(f, "id", None) or getattr(f, "attr", None)
    return name if name in names else None


def _sql_argument_of(call, positions):
    """The SQL-carrying argument of a call of a derived execute-family name, or None (a keyword form reads the same)."""
    pos, name = positions
    if len(call.args) > pos:
        return call.args[pos]
    return next((k.value for k in call.keywords if k.arg == name), None)


def _sites_of(rel, tree, parent, q):
    """Every direct execute-family call in a module: (call, its SQL argument, "<module>:<function>")."""
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in SQL_CALLS and n.args:
            yield n, n.args[0], f"{rel}:{q.get(id(n), '<module>')}"


def _bare_parameter_sites(mods):
    """W3: {function name: (position, parameter)} for every function whose SQL argument IS one of its parameters — that
    function is an execute-family name by another spelling, so every call of it meets the same rules. Derived, to
    closure: a call passing its own caller's parameter through makes the caller one too."""
    names = {}
    changed = True
    while changed:
        changed = False
        for rel, _text, tree, parent, q, _idx in mods:
            sites = list(_sites_of(rel, tree, parent, q))
            for n in ast.walk(tree):
                if isinstance(n, ast.Call):
                    callee = _exec_callee(n, names)
                    if callee and _sql_argument_of(n, names[callee]) is not None:
                        sites.append((n, _sql_argument_of(n, names[callee]), None))
            for call, arg, _where in sites:
                f = _scope_of(call, parent)
                if not (isinstance(arg, ast.Name) and isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))):
                    continue
                params = [a.arg for a in f.args.posonlyargs + f.args.args]
                if arg.id in params and f.name != METHOD and f.name not in names:
                    names[f.name] = (params.index(arg.id), arg.id)
                    changed = True
    return names


_MODULE_RESULTS = {}
# the decorators src/'s methods carry today: anything else, staticmethod and classmethod first, is not a plain method
SELF_DECORATORS = {"abstractmethod", "contextlib.contextmanager", "contextmanager", "model_serializer", "model_validator",
                   "property", "store_mutator"}


def _plain_method(f, par):
    """`f` is a def directly in a class, its first parameter `self`, carrying only decorators known to leave it one."""
    if not (isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and isinstance(par.get(f), ast.ClassDef)):
        return False
    first = (f.args.posonlyargs + f.args.args)[:1]
    deco = {ast.unparse(d.func if isinstance(d, ast.Call) else d) for d in f.decorator_list}
    return bool(first) and first[0].arg == "self" and deco <= SELF_DECORATORS


def _self_problems(rel, t, par, ix):
    """Round 6 (R5-01): the gate reads `self.X` as an instance's X in many places, so the name's meaning is established
    once, for all of src/: its only binder is a plain method's first parameter, and every read reaches one through the
    enclosing scopes (a closure counts; a default or a decorator is evaluated outside the method, so it does not). The
    read half catches what binds nothing the binder walk sees, such as `globals()["self"] = …`."""
    bad = []
    for b in ix.by_name.get("self", ()):
        owner = par.get(par.get(b)) if isinstance(b, ast.arg) else None
        if not (owner is not None and _plain_method(owner, par)):      # a parameter name cannot repeat: this is the first
            bad.append(f"{rel} L{getattr(b, 'lineno', '?')}: `self` bound other than as a plain method's first parameter")
    for n in ast.walk(t):
        if isinstance(n, ast.Name) and n.id == "self" and isinstance(n.ctx, ast.Load):
            child, node = n, par.get(n)
            while node is not None and not (_plain_method(node, par) and any(child is x for x in node.body)):
                child, node = node, par.get(node)
            if node is None:
                bad.append(f"{rel} L{n.lineno}: `self` read where no plain method's first parameter reaches it")
    return bad


def _db_name_exception(rel, n, par, q):
    """`n`, a denied name's attribute node, is the reviewed exception: its function and receiver are listed, the whole
    function is the reviewed one, and the attribute is not the function of a call."""
    recv = n.value.id if isinstance(n.value, ast.Name) else None
    want = DB_NAME_EXCEPTIONS.get((rel, q.get(id(n)), recv, n.attr))
    called = isinstance(par.get(n), ast.Call) and par[n].func is n
    return want is not None and not called and _digest(_scope_of(n, par)) == want


def _module_bindings(t):
    """{name: dotted module} for every name an absolute import binds to a module."""
    out = {}
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            for a in n.names:
                out[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
        elif isinstance(n, ast.ImportFrom) and n.level == 0:
            for a in n.names:
                if f"{n.module}.{a.name}" in SRC_IMPORTS:      # `from os import path as p`: the name holds a module
                    out[a.asname or a.name] = f"{n.module}.{a.name}"
    return out


def _is_base(n, par):
    """`n` is read only as the base of an attribute."""
    q = par.get(n)
    return isinstance(q, ast.Attribute) and q.value is n


def _is_dunder(name):
    return isinstance(name, str) and len(name) > 4 and name.startswith("__") and name.endswith("__")


def _import_uses(t, par):
    """Everything in one module the closed tables judge: (kind, name, member, node), kind one of module, member, held,
    dunder, dynamic (a name read for its site). The gate and the table's currency cell both read this, so they cannot drift."""
    bound = _module_bindings(t)
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            for a in n.names:
                yield "module", a.name, None, n
        elif isinstance(n, ast.ImportFrom) and n.level == 0:
            yield "module", n.module, None, n
            for a in n.names:
                yield "member", n.module, a.name, n
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in bound:
            if not _is_base(n, par):
                yield "held", n.id, None, n
                continue
            mod, q = bound[n.id], par[n]
            while True:
                yield "member", mod, q.attr, q
                full = f"{mod}.{q.attr}"
                if full not in SRC_IMPORTS:
                    break
                if not _is_base(q, par):
                    yield "held", full, None, q
                    break
                mod, q = full, par[q]
        name = n.attr if isinstance(n, ast.Attribute) else n.id if isinstance(n, ast.Name) else None
        if _is_dunder(name) and not (isinstance(n, ast.Name) and name == "__import__"):
            yield "dunder", name, None, n
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "getattr" and len(n.args) >= 2:
            if isinstance(n.args[1], ast.Constant) and _is_dunder(n.args[1].value):
                yield "dunder", n.args[1].value, None, n
        if isinstance(n, ast.Name) and n.id == "__import__":
            yield "dynamic", "__import__", None, n


def _absolute_names(t):
    """Every name an absolute import binds in this module, module or member."""
    out = set()
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            out |= {a.asname or a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.level == 0:
            out |= {a.asname or a.name for a in n.names}
    return out


def _own_module_at(path, modules):
    """The own module at dotted-path `path`: its file, its `__init__.py`, or `path/` for a directory of modules with no
    `__init__.py`. `veracium/store` is one, and `from .. import store` binds it all the same."""
    for m in (f"{path}.py", f"{path}/__init__.py"):
        if m in modules:
            return m
    return f"{path}/" if any(m.startswith(f"{path}/") for m in modules) else None


def _own_targets(rel, t, modules):
    """{name: module of src/} for every relative import of a module, and [(node, target, name, bound as)] for every
    relative import of a name out of a module. `modules` is the set of src/'s module paths."""
    bound, names = {}, []
    pkg = rel.split("/")[:-1]
    for n in ast.walk(t):
        if isinstance(n, ast.ImportFrom) and n.level:
            base = "/".join(pkg[:len(pkg) - n.level + 1] + (n.module.split(".") if n.module else []))
            for a in n.names:
                sub = _own_module_at(f"{base}/{a.name}", modules)
                if sub:
                    bound[a.asname or a.name] = sub
                else:
                    tgt = _own_module_at(base, modules)
                    if tgt and not tgt.endswith("/"):
                        names.append((n, tgt, a.name, a.asname or a.name))
    return bound, names


def _own_index(mods):
    """{module: (its absolute names, ((name, own module it holds), ...))}, every input `_own_problems` reads of OTHER
    modules, so the memo's key can carry it whole."""
    modules = {m[0] for m in mods}
    return {rel: (tuple(sorted(_absolute_names(tree))), tuple(sorted(_own_targets(rel, tree, modules)[0].items())))
            for rel, _text, tree, _p, _q, _i in mods}


def _own_problems(rel, t, par, q, own_index):
    """A name reached through another module of src/ (N6): `d.X` or `from .m import X`, X anything `d` took by an absolute
    import, through own modules to any depth."""
    bad = []
    bound, names = _own_targets(rel, t, set(own_index))
    at = lambda n: f"{rel} L{getattr(n, 'lineno', '?')}"
    why = "a name another module of src/ imported, reached through it"
    for n, tgt, name, as_name in names:
        if name in own_index[tgt][0]:
            bad.append(f"{at(n)}: `{name}`, {why}")
        held = dict(own_index[tgt][1]).get(name)
        if held:
            bound[as_name] = held
    for n in ast.walk(t):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in bound:
            if not _is_base(n, par):
                want = OWN_MODULE_VALUES.get((rel, q.get(id(n)), n.id))
                if want is None or _digest(_scope_of(n, par)) != want:
                    bad.append(f"{at(n)}: `{n.id}`, a module of src/ held as a value")
                continue
            tgt, a = bound[n.id], par[n]
            while True:
                names_of, held_of = own_index.get(tgt, ((), ()))       # a directory has no text, so it holds nothing itself
                if a.attr in names_of:
                    bad.append(f"{at(a)}: `{a.attr}`, {why}")
                    break
                sub = dict(held_of).get(a.attr)
                if sub is None and tgt.endswith(("/", "/__init__.py")):
                    sub = _own_module_at(f"{tgt.rsplit('/', 1)[0]}/{a.attr}", own_index)
                if sub is None:
                    break
                if not _is_base(a, par):
                    bad.append(f"{at(a)}: `{a.attr}`, a module of src/ held as a value")
                    break
                tgt, a = sub, par[a]
    return bad


def _annotation_slots(n):
    """The annotation expressions node `n` carries."""
    if isinstance(n, ast.AnnAssign):
        yield n.annotation
    elif isinstance(n, ast.arg) and n.annotation is not None:
        yield n.annotation
    elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.returns is not None:
        yield n.returns


def _annotation_problem(slot):
    """Why a library evaluating this annotation would run code, or None. A string is parsed and read as an expression;
    a computed string has no text to read, so a computed form refuses. `-` stays: it cannot build a string, and a Literal's
    honest value (`"within-episode-v1"`) parses as subtraction."""
    for c in ast.walk(slot):
        if isinstance(c, (ast.Call, ast.JoinedStr)) or (isinstance(c, ast.BinOp) and not isinstance(c.op, (ast.BitOr, ast.Sub))):
            return ast.unparse(c)[:50]
        if isinstance(c, ast.Constant) and isinstance(c.value, str):
            try:
                inner = ast.parse(c.value, mode="eval")
            except SyntaxError:
                return c.value[:50]
            found = _annotation_problem(inner.body)       # a string inside the string is read the same way
            if found is not None:
                return found
    return None


_LADDER_HEAD = re.compile(r"ALTER TABLE [a-z_]+ ADD COLUMN ")
_MIGRATION = "veracium/store/migration.py"


# `_alters` and `plan` make every entry the table does not spell out: each frozen whole, function digest
LADDER_FUNCTIONS = {"_alters": "307f6485a18cbd6e7dad340f3216ed896a6e1a34933e52dac31e11e69606dc99",
                    "plan": "82fc1b7502c2bc7567410d9fba5ec8bc3760436ec58c5abf9959e33395438f18"}
TABLE_KINDS = {"read", "data", "check"}


def _ladder_problems(rel, t, par):
    """Research's B4, written once with 0018's table, closed over the grammar (its read of cad9e795). `conn.execute(entry.step)`
    reads a table entry, so no binding reaches a statement in it, and the statements are read where they stand:
    - an `ALTERS_*` name is bound once, by a plain assignment at module level, to a tuple of literal `ADD COLUMN` statements;
    - each element of `FORWARD_ENTRIES` is `*_alters(lo, v, ALTERS_*)` or a five-positional `ForwardEntry` of a table kind
      naming a function, its fifth a tuple of names and literal strings (0013 §5g.1's `fields`, data the step reads and no
      code it runs); a `ForwardEntry` made anywhere else is made in `_alters` or `plan`, each frozen whole."""
    bad = []
    at = lambda n: f"{rel} L{getattr(n, 'lineno', '?')}"
    alters = lambda n: isinstance(n, ast.Name) and n.id.startswith("ALTERS_")
    bound = {}
    for n in ast.walk(t):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)) and n.id.startswith("ALTERS_"):
            bound[n.id] = bound.get(n.id, 0) + 1
            holder = par.get(n)
            if not (isinstance(holder, ast.Assign) and len(holder.targets) == 1 and holder.targets[0] is n
                    and isinstance(par.get(holder), ast.Module) and isinstance(holder.value, ast.Tuple)):
                bad.append(f"{at(n)}: `{n.id}` bound other than as a plain module-level tuple")
                continue
            for e in holder.value.elts:
                if not (isinstance(e, ast.Constant) and isinstance(e.value, str) and _LADDER_HEAD.match(e.value)):
                    bad.append(f"{at(e)}: a ladder statement that is not a literal ADD COLUMN: {ast.unparse(e)[:60]}")
        if isinstance(n, ast.alias) and (n.asname or "").startswith("ALTERS_") and n.asname != n.name:
            bad.append(f"{at(n)}: `{n.asname}` bound by an import of `{n.name}`")
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in LADDER_FUNCTIONS and rel == _MIGRATION:
            if _digest(n) != LADDER_FUNCTIONS[n.name]:
                bad.append(f"{at(n)}: `{n.name}` changed: it makes the table's entries, so it is re-reviewed")
    bad += [f"{rel}: `{k}` bound {c} times" for k, c in bound.items() if c > 1]
    table = next((n.value for n in t.body if isinstance(n, ast.Assign) and any(getattr(x, "id", "") == "FORWARD_ENTRIES" for x in n.targets)), None)
    listed = set()
    if table is not None:
        for e in table.elts if isinstance(table, ast.Tuple) else [table]:
            if isinstance(e, ast.Starred) and isinstance(e.value, ast.Call) and getattr(e.value.func, "id", None) == "_alters":
                listed.add(id(e.value))
                if not (len(e.value.args) == 3 and not e.value.keywords and alters(e.value.args[2])):
                    bad.append(f"{at(e)}: `_alters` of something other than a frozen `ALTERS_*` tuple")
                continue
            ok = (isinstance(e, ast.Call) and getattr(e.func, "id", None) == "ForwardEntry" and len(e.args) == 5 and not e.keywords
                  and isinstance(e.args[2], ast.Constant) and e.args[2].value in TABLE_KINDS and isinstance(e.args[3], ast.Name)
                  and isinstance(e.args[4], ast.Tuple)
                  and all(isinstance(x, ast.Name) or (isinstance(x, ast.Constant) and isinstance(x.value, str)) for x in e.args[4].elts))
            if ok:
                listed.add(id(e))
            else:
                bad.append(f"{at(e)}: a table element that is neither `_alters` nor a named read, data or check: {ast.unparse(e)[:60]}")
    for n in ast.walk(t):
        if isinstance(n, ast.Call) and id(n) not in listed and getattr(n.func, "id", None) in ("ForwardEntry", "_alters"):
            if getattr(_scope_of(n, par), "name", "") not in LADDER_FUNCTIONS and not (table is not None and n in ast.walk(table)):
                bad.append(f"{at(n)}: `{n.func.id}` outside the table and the functions frozen beside it")
    return bad


def _import_problems(rel, t, par, q):
    """N1-N5, N7, N8: what src/ may reach by name, over one module. Pure in its arguments and the tables."""
    bad = []
    at = lambda n: f"{rel} L{getattr(n, 'lineno', '?')}"
    for kind, name, member, n in _import_uses(t, par):
        if kind == "module" and name not in SRC_IMPORTS:
            bad.append(f"{at(n)}: `{name}`, a module src/ does not import")
        elif kind == "member" and member not in SRC_IMPORTS.get(name, ()):
            bad.append(f"{at(n)}: `{name}.{member}`, a member src/ does not use")
        elif kind == "held":
            bad.append(f"{at(n)}: `{name}`, a module held as a value")
        elif kind == "dunder" and name not in SRC_DUNDERS:
            bad.append(f"{at(n)}: `{name}`, a dunder src/ does not read")
        elif kind == "dynamic":
            call = par.get(n)
            read = par.get(call)
            if not (isinstance(call, ast.Call) and call.func is n and isinstance(read, ast.Attribute)
                    and IMPORT_SITES.get((rel, q.get(id(n)))) == _digest(read)):
                bad.append(f"{at(n)}: `__import__` outside its two reviewed calls")
    for n in ast.walk(t):
        if isinstance(n, ast.Match):
            bad.append(f"{at(n)}: `match`, whose patterns read an attribute with no attribute node")
        if isinstance(n, ast.alias) and n.name == "*":
            bad.append(f"{at(n)}: a star import, whose names no rule here can see")
        word = n.attr if isinstance(n, ast.Attribute) else n.id if isinstance(n, ast.Name) else None
        if isinstance(n, ast.alias):
            word = n.name.split(".")[-1]
        if word in REACH_NAMES:
            bad.append(f"{at(n)}: `{word}`, which reaches a namespace, a module or an evaluator")
        if isinstance(n, ast.Attribute) and n.attr in REACH_ATTRIBUTES:
            bad.append(f"{at(n)}: `.{n.attr}`, an attribute of a class that holds a module")
        if isinstance(n, ast.ClassDef) and _scope_of(n, par) is not None and not isinstance(_scope_of(n, par), ast.ClassDef):
            bad.append(f"{at(n)}: a class inside a function, where a library can evaluate its annotations against locals")
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "type" and len(n.args) + len(n.keywords) > 1:
            bad.append(f"{at(n)}: `type` building a class, whose annotations a library can evaluate")
        for slot in _annotation_slots(n):
            why = _annotation_problem(slot)
            if why is not None:
                bad.append(f"{at(n)}: an annotation a library would evaluate as code: {why}")
        spelled = n.attr if isinstance(n, ast.Attribute) else n.id if isinstance(n, ast.Name) else None
        if spelled == "TypeAdapter":
            call = par.get(n)
            site = (rel, q.get(id(n)))
            if not (isinstance(call, ast.Call) and call.func is n and TYPE_ADAPTER_SITE.get(site) == _digest(call)):
                bad.append(f"{at(n)}: `TypeAdapter` outside its one reviewed call")
        if isinstance(n, ast.alias) and n.name == "TypeAdapter" and n.asname:
            bad.append(f"{at(n)}: `TypeAdapter` imported under another name, `{n.asname}`")
    return bad


def _module_problems(rel, t, par, q, ix, denied, exec_names, guarded_literals, sq, own_index):
    """One module's share of `_package_problems`: (problems, {site key: times seen}). Pure in its arguments, so a matrix
    of mutants of one module re-reads only that module."""
    bad, seen = (_self_problems(rel, t, par, ix) + _import_problems(rel, t, par, q) + _own_problems(rel, t, par, q, own_index)
                 + _ladder_problems(rel, t, par)), {}
    at = lambda n: f"{rel} L{getattr(n, 'lineno', '?')}"
    for n in ast.walk(t):
        if isinstance(n, ast.Attribute):
            if n.attr in denied and not _db_name_exception(rel, n, par, q):
                bad.append(f"{at(n)}: `.{n.attr}` of the database API, which src/ does not use")
            if n.attr in ACCESSORS:
                bad.append(f"{at(n)}: `.{n.attr}`, an accessor that reaches an attribute with no attribute node")
            if n.attr in SQL_CALLS and not (isinstance(par.get(n), ast.Call) and par[n].func is n):
                bad.append(f"{at(n)}: `.{n.attr}` held, passed or returned, not called")
        if isinstance(n, ast.Name) and n.id in ACCESSORS:
            bad.append(f"{at(n)}: `{n.id}`, an accessor that reaches an attribute with no attribute node")
        if isinstance(n, ast.alias) and n.name.split(".")[-1] in ACCESSORS:
            bad.append(f"{at(n)}: `{n.name}` imported, an accessor that reaches an attribute with no attribute node")
        # W3: a derived name stays spelled as itself, or a call of it would read as some other function's
        if isinstance(n, ast.alias) and n.name in exec_names and n.asname not in (None, n.name):
            bad.append(f"{at(n)}: `{n.name}` runs its SQL argument: imported under another name, `{n.asname}`")
        if (isinstance(n, ast.Call) and getattr(n.func, "id", None) == "getattr" and len(n.args) >= 2
                and isinstance(n.args[1], ast.Constant) and n.args[1].value in guarded_literals):
            bad.append(f"{at(n)}: getattr of `{n.args[1].value}`")
        # W3: a derived execute-family name is called, never held
        if (isinstance(n, (ast.Name, ast.Attribute)) and (getattr(n, "id", None) or getattr(n, "attr", None)) in exec_names
                and isinstance(n.ctx, ast.Load) and not (isinstance(par.get(n), ast.Call) and par[n].func is n)):
            bad.append(f"{at(n)}: `{getattr(n, 'id', None) or n.attr}` runs its SQL argument: held, not called")
    sites = [] if rel == sq else list(_sites_of(rel, t, par, q))
    for n in ast.walk(t):
        if isinstance(n, ast.Call):
            callee = _exec_callee(n, exec_names)
            if callee:
                arg = _sql_argument_of(n, exec_names[callee])
                if arg is None:
                    bad.append(f"{at(n)}: `{callee}` called with no SQL argument the gate can read")
                else:
                    sites.append((n, arg, f"{rel}:{q.get(id(n), '<module>')}"))
    for call, arg, where in sites:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            tags = _sqlite_classify(arg.value)
            if UNRESOLVED in tags:
                bad.append(f"{at(call)}: a statement SQLite did not prepare ({where}): {' '.join(arg.value.split())[:70]}")
            if "schema-route" in tags:
                bad.append(f"{at(call)}: a route around the store's schema ({where}): {' '.join(arg.value.split())[:70]}")
            if tags & {"edges-insert", "edges-json-update"}:
                bad.append(f"{at(call)}: an edges json write outside the write method ({where}): "
                           f"{' '.join(arg.value.split())[:70]}")
            continue
        key = (where, _digest(arg))
        seen[key] = seen.get(key, 0) + 1
        f = _scope_of(call, par)
        if key not in SRC_NONLITERAL:
            bad.append(f"{at(call)}: a non-literal SQL site not in the reviewed list ({where}): {ast.unparse(arg)[:80]}")
            continue
        binding = _sql_binding(t, par, f, arg, ix)
        got = _binding_digest(t, par, f, arg, binding, ix)
        if got != SRC_NONLITERAL[key][2]:
            bad.append(f"{at(call)}: what determines the non-literal SQL at {where} changed (binding {got}) — "
                       f"re-review it ({ast.unparse(arg)[:60]})")
        if binding[0] and rel not in MIGRATION_MODULES:
            def values(name):
                out = []
                for b in ix.of(f, name):
                    v = _value_of_binder(b, par)
                    out.append(v if v is not None else ast.Constant(value=""))
                return out
            if not _PARAM_HEAD.match(_leading_constant(arg, values) or ""):
                bad.append(f"{at(call)}: a parameter ({', '.join(binding[0])}) reaches SQL whose leading constant "
                           f"does not fix a SELECT or a named PRAGMA ({where}): {ast.unparse(arg)[:60]}")
    return bad, seen


def _package_problems(source, tree, parent, idx, others) -> list:
    """Round 5, research's stage 2 (S2-01, W1–W3, S2-02): N4f's rules over ALL of src/, on any receiver. The connection
    leaves sqlite.py in more ways than the inventory counts (a passed `self` is read as `store._conn`), so the check
    sits where SQL runs and where the connection can be used without SQL. A NON-LITERAL `getattr` is 0031's census's to
    refuse (connect_census); that dependence is stated, not re-implemented here."""
    bad = []
    sq = "veracium/store/sqlite.py"
    mods = [(sq, source, tree, parent, _qualnames(tree), idx)] + [
        (rel, text, *_parsed(text)) for rel, text in sorted(others.items())]
    denied = (DB_NAMES | {n for c in (sqlite3.Connection, sqlite3.Cursor) for n in dir(c) if not n.startswith("__")})
    denied -= DB_ADMITTED
    exec_names = _bare_parameter_sites(mods)
    guarded_literals = denied | set(SQL_CALLS) | {"_conn"} | ACCESSORS | set(exec_names)
    bound_names, seen = set(), {}
    own_index = _own_index(mods)
    # every input `_module_problems` reads, every table a cell may patch included: a key that omits one serves a stale
    # result, which only a fixed test order shows (round 6: offline red, the suite and CI green)
    shared = (tuple(sorted(exec_names.items())), tuple(sorted(denied)), tuple(sorted(DB_NAME_EXCEPTIONS.items())),
              tuple(sorted(SRC_NONLITERAL.items())), tuple(sorted((k, tuple(sorted(v))) for k, v in SRC_IMPORTS.items())),
              tuple(sorted(SRC_DUNDERS)), tuple(sorted(REACH_NAMES)), tuple(sorted(OWN_MODULE_VALUES.items())),
              tuple(sorted(TYPE_ADAPTER_SITE.items())), tuple(sorted(IMPORT_SITES.items())), tuple(sorted(REACH_ATTRIBUTES)), tuple(sorted(LADDER_FUNCTIONS.items())),
              tuple(sorted(own_index.items())))
    for rel, text, tree_m, par_m, q_m, ix_m in mods:
        key = (rel, text, shared)
        if key not in _MODULE_RESULTS:
            _MODULE_RESULTS[key] = _module_problems(rel, tree_m, par_m, q_m, ix_m, denied, exec_names, guarded_literals, sq,
                                                    own_index)
        got_bad, got_seen = _MODULE_RESULTS[key]
        bad += got_bad
        for k, v in got_seen.items():
            seen[k] = seen.get(k, 0) + v
    for key, (count, _text, _b) in SRC_NONLITERAL.items():
        if seen.get(key, 0) != count:
            bad.append(f"non-literal site {key} occurs {seen.get(key, 0)} time(s), the reviewed list says {count}")
    # S2-02: no attribute store reaches a value a listed binding reads, in any module. `self.X` inside the store class
    # is the binding's own subject and is held by it
    t0 = mods[0][2]
    cls = next(n for n in t0.body if isinstance(n, ast.ClassDef) and n.name == "SqliteStore")
    for n in ast.walk(t0):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in SQL_CALLS and n.args:
            a0 = n.args[0]
            if not (isinstance(a0, ast.Constant) and isinstance(a0.value, str)):
                _p, m_names, a_names = _sql_binding(t0, parent, _scope_of(n, parent), a0, idx)
                bound_names |= {k for k, v in m_names.items() if v} | {k for k, v in a_names.items() if v}
    cls_ids = idx.ids(cls)
    for rel, _text, t, par, q, ix in mods:
        for n in ast.walk(t):
            if isinstance(n, ast.Attribute) and isinstance(n.ctx, (ast.Store, ast.Del)) and n.attr in bound_names:
                own = rel == sq and id(n) in cls_ids and isinstance(n.value, ast.Name) and n.value.id == "self"
                if not own:
                    bad.append(f"{rel} L{n.lineno}: `{n.attr}`, a name a listed SQL binding reads, stored as an attribute")
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
        writes = [n.value for n in ast.walk(ast.parse(p.read_text())) if isinstance(n, ast.Constant)
                  and isinstance(n.value, str) and "edges" in n.value.lower()
                  and _sqlite_classify(n.value) & {"edges-insert", "edges-json-update"}]
        assert writes == [], (p, writes)


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


# ---- round 5 (R4-01): the four unresolved forms, their siblings and the harmless controls -----------------------------
# Each mutant edits ONLY a call site or a definition the gate reads — the write method is never changed (the reviewer:
# "the positional witness must use the unchanged frozen method") — and each is refused by the STATIC gate for its own
# named reason (research's N3), asserted below. (old, new, the reason's text); old None appends to the end.
_UPSERT = ("                (edge.id, edge.user_id, edge.subject, edge.relation, edge.object,\n"
           "                 int(edge.active), int(edge.quarantined)), edge, (),\n"
           "                user_id=edge.user_id, edge_id=edge.id,")
_RECOMPUTE = ('        self._write_edge_row("UPDATE edges SET json=? WHERE id=?", (), edge, (edge_id,),\n'
              '                             user_id=row[1], edge_id=edge_id, prior=row[0])\n'
              '        self._conn.execute("DELETE FROM wiki WHERE user_id=?", (row[1],))')
_LIFT = '(edge.model_dump_json().replace("0.8", "1.8"), edge_id)'
R5_MUTANTS = {
    # (a) the binding layout
    "(a) the reviewer's re-layout: the captured json in `quarantined`, an unchecked dump in `json`": (
        _UPSERT, "                (edge.id, edge.user_id, edge.subject, edge.relation, edge.object,\n"
                 "                 int(edge.active)), edge, (edge.model_dump_json().replace(\"0.8\", \"1.8\"),),\n"
                 "                user_id=edge.user_id, edge_id=edge.id,", "binding layout puts the captured json at parameter 6 of 8"),
    "(a) a starred `before`": (
        _UPSERT, _UPSERT.replace("(edge.id, edge.user_id,", "(*(edge.id,), edge.user_id,"), "not tuple displays"),
    "(a) a `before` held in a name": (
        _INV, "        before = ()\n" + _INV.replace('WHERE id=?", (), edge,', 'WHERE id=?", before, edge,'),
        "not tuple displays"),
    # (b) every connection reference
    "(b) the reviewer's alias of execute, with constructed SQL": (
        _RECOMPUTE, _RECOMPUTE + '\n        run_sql = self._conn.execute\n        run_sql("UP" + "DATE ed" + "ges SET js"'
                    ' + "on=? WHERE id=?", ' + _LIFT + ')', "held, passed or returned, not called"),
    "(b) a cursor's `.connection` held in a name (research's B1)": (
        _RECOMPUTE, _RECOMPUTE + '\n        run_sql = self._conn.execute("SELECT 1").connection.execute\n'
                    '        run_sql("UP" + "DATE edges SET json=? WHERE id=?", ' + _LIFT + ')', "`.connection` in the store module"),
    "(b) a cursor's own execute held in a name (research's B1)": (
        _RECOMPUTE, _RECOMPUTE + '\n        run_sql = self._conn.execute("SELECT 1").execute\n'
                    '        run_sql("UP" + "DATE edges SET json=? WHERE id=?", ' + _LIFT + ')', "held, passed or returned, not called"),
    "(b) create_function on the store's connection": (
        _RECOMPUTE, _RECOMPUTE + '\n        self._conn.create_function("lift", 1, lambda j: j)', "`self._conn.create_function`"),
    "(b) set_authorizer(None) on the store's connection": (
        _RECOMPUTE, _RECOMPUTE + '\n        self._conn.set_authorizer(None)', "`self._conn.set_authorizer`"),
    "(b) total_changes read": (
        _RECOMPUTE, _RECOMPUTE + '\n        assert self._conn.total_changes >= 0', "`self._conn.total_changes`"),
    "(b) `with self._conn:`": (
        _RECOMPUTE, _RECOMPUTE + '\n        with self._conn:\n            pass', "the connection reached in a form"),
    "(b) the connection passed to a function the inventory lacks": (
        _RECOMPUTE, _RECOMPUTE + '\n        _lift(self._conn)', "not in the inventory"),
    "(b) an inventory callee rebound at module scope": (None, "\nappend_event = print\n", "is not bound to the inventory's"),
    "(b) the connection held in a name": (
        _RECOMPUTE, _RECOMPUTE + '\n        c = self._conn\n        c.execute("SELECT 1")', "the connection reached in a form"),
    # (c) a statement SQLite did not prepare
    "(c) the reviewer's unregistered function": (
        _RECOMPUTE, _RECOMPUTE + '\n        self._conn.execute("UPDATE edges SET json=reviewer_json(json) WHERE id=?", (edge_id,))',
        "a statement SQLite did not prepare"),
    "(c) a missing collation": (
        _RECOMPUTE, _RECOMPUTE + '\n        self._conn.execute("UPDATE edges SET json=? WHERE id=? AND json < \'x\' COLLATE lift", '
                    + _LIFT + ')', "a statement SQLite did not prepare"),
    "(c) a missing table": (
        _RECOMPUTE, _RECOMPUTE + '\n        self._conn.execute("UPDATE edges SET json=(SELECT j FROM scratch) WHERE id=?", (edge_id,))',
        "a statement SQLite did not prepare"),
    "(c) a syntax error": (
        _RECOMPUTE, _RECOMPUTE + '\n        self._conn.execute("UPDATE edges SET json=? WHERE", (edge_id,))',
        "a statement SQLite did not prepare"),
    # (d) what determines a listed non-literal
    "(d) the reviewer's changed assignment reaching `q` in edges": (
        '            q = "SELECT json FROM edges WHERE user_id=?"\n',
        '            q = ("UP" + "DATE ed" + "ges SET js" + "on=re" + "place(js"\n'
        '                 + "on, \'0.8\', \'1.8\') WHERE user_id=?")\n', "what determines the non-literal SQL at SqliteStore.edges"),
    "(d) a changed _APPLIED_SQL (research's B3)": (
        '_APPLIED_SQL = "(state = \'applied\')"', '_APPLIED_SQL = "(state = \'applied\' OR 1)"',
        "what determines the non-literal SQL at SqliteStore._attested_by_another_owner"),
    "(d) a changed _OP_COLS (research's B3)": (
        '    _OP_COLS = ("operation_id", "user_id", "fence", "state", "owner",',
        '    _OP_COLS = ("operation_id", "user_id", "fence", "state", "owner", "json",',
        "what determines the non-literal SQL at SqliteStore._load_op"),
    "(d) a method two calls down changed (the binding is followed to closure)": (
        "            lease_expires_at=row[6], claimed_ids=json.loads(row[7]))\n",
        "            lease_expires_at=row[6], claimed_ids=json.loads(row[7]) or [])\n",
        "what determines the non-literal SQL at SqliteStore.transition_consolidation_if_current"),
    "(d) an edit elsewhere in a listed function": (
        '            rows = self._conn.execute(q, args).fetchall()\n',
        '            args = list(args)\n            rows = self._conn.execute(q, args).fetchall()\n',
        "what determines the non-literal SQL at SqliteStore.edges"),
}
R5_MUTANTS.update({
    # W1, W2 and W3 in sqlite.py itself (research's stage 2)
    "(W1) blobopen writes the column with no statement": (
        _RECOMPUTE, _RECOMPUTE + '\n        self._conn.blobopen("edges", "json", 1)', "`.blobopen` of the database API"),
    "(W2) attrgetter reaches execute with no attribute node": (
        _RECOMPUTE, _RECOMPUTE + '\n        import operator\n        operator.attrgetter("_conn.execute")(self)("UP" + "DATE edges '
                    'SET json=? WHERE id=?", ' + _LIFT + ')', "`.attrgetter`, an accessor"),
    "(W2) methodcaller reaches execute with no attribute node": (
        _RECOMPUTE, _RECOMPUTE + '\n        import operator\n        operator.methodcaller("execute", "SELECT 1")(self._conn)',
        "`.methodcaller`, an accessor"),
    "(W2) `from operator import attrgetter`": (
        _RECOMPUTE, _RECOMPUTE + '\n        from operator import attrgetter as ag\n        ag("_conn")(self)',
        "`attrgetter` imported"),
    "(W3) the bare-parameter helper from the store": (
        _RECOMPUTE, _RECOMPUTE + '\n        from .migration import _rows\n        _rows(self._conn, "UP" + "DATE edges SET json=? '
                    'WHERE id=?", ' + _LIFT + ')', "a non-literal SQL site not in the reviewed list"),
    # S2-02: a listed binding's value reached by an attribute store
    "(S2-02) a class attribute a binding reads, stored at module level": (
        None, '\nSqliteStore._OP_COLS = ("json",)\n', "`_OP_COLS`, a name a listed SQL binding reads"),
})
_SHADOW = {
    "CREATE TEMP TABLE edges": "CREATE TEMP TABLE IF NOT EXISTS edges AS SELECT id, json FROM main.edges",
    "CREATE TEMPORARY TABLE edges": "CREATE TEMPORARY TABLE edges(id, json)",
    "CREATE TABLE temp.edges": "CREATE TABLE temp.edges(id, json)",
    "a TEMP table shadowing the journal": "CREATE TEMP TABLE edge_event(user_id, seq)",
    "a TEMP virtual table": "CREATE VIRTUAL TABLE temp.edges USING fts5(json)",
    "ATTACH": "ATTACH DATABASE ':memory:' AS side",
    "writable_schema": "PRAGMA writable_schema=ON",
    "a pragma the pin does not use": "PRAGMA trusted_schema=ON",
}
for _k, _sql in _SHADOW.items():
    R5_MUTANTS[f"(R-01) {_k}"] = (_RECOMPUTE, _RECOMPUTE + f'\n        self._conn.execute("{_sql}")',
                                  "a route around the store's schema")
R5_MUTANTS["(R-01) a direct write to the schema table"] = (
    _RECOMPUTE, _RECOMPUTE + '\n        self._conn.execute("UPDATE sqlite_schema SET sql=sql WHERE name=\'edges\'")',
    "a statement SQLite did not prepare")
# research's stage 2 (S2-01): plants in OTHER src modules, read through the package rule. (module, old, new, reason)
_NS = ('    serialized (the PK is a backstop only, §4a)."""\n    return 1 + conn.execute(\n'
       '        "SELECT COALESCE(MAX(seq), 0) FROM edge_event WHERE user_id=?",')
_EE = "veracium/store/edge_events.py"
_SPLIT = ('"".join(("UP", "DA", "TE ed", "ges SE", "T js", "on=rep", "lace(js", "on, \'0.8\', \'1.8\') WH", "ERE us", "er_id=?"))')


def _in_next_seq(lines):
    return _NS.replace('"""\n    return', '"""\n' + lines + '\n    return')


_DR = "veracium/doctor.py"
_DR_AT = "    conn = store._conn                                 # the package's own convention (revocation.project_store)\n"
_DM = "veracium/store/data_migration.py"
_DM_AT = '    converting import\'s (0044 §4l, T11a). Returns (restored ids, withheld ids)."""\n    conn = store._conn\n'
R5_SRC_MUTANTS = {
    "a direct split-SQL write in next_seq": (_EE, _NS, _in_next_seq(f'    conn.execute({_SPLIT}, (user_id,))'),
                                             "a non-literal SQL site not in the reviewed list"),
    "UPDATE edges in next_seq": (_EE, _NS, _in_next_seq('    conn.execute("UPDATE edges SET json=json WHERE user_id=?", (user_id,))'),
                                 "an edges json write outside the write method"),
    "UPDATE OR IGNORE edges in next_seq": (_EE, _NS, _in_next_seq('    conn.execute("UPDATE OR IGNORE edges SET json=json WHERE '
                                                                  'user_id=?", (user_id,))'),
                                           "an edges json write outside the write method"),
    'UPDATE "edges" in next_seq': (_EE, _NS, _in_next_seq("    conn.execute('UPDATE \"edges\" SET json=json WHERE user_id=?', (user_id,))"),
                                   "an edges json write outside the write method"),
    "REPLACE INTO edges in next_seq": (_EE, _NS, _in_next_seq('    conn.execute("REPLACE INTO edges(id, user_id, subject, relation, '
                                                              'object, json) SELECT id, user_id, subject, relation, object, json '
                                                              'FROM edges WHERE user_id=?", (user_id,))'),
                                       "an edges json write outside the write method"),
    "execute held in next_seq, SQL by +": (_EE, _NS, _in_next_seq('    run_sql = conn.execute\n    run_sql("UP" + "DATE edges SET '
                                                                  'json=json WHERE user_id=?", (user_id,))'),
                                           "`.execute` held, passed or returned"),
    "execute held in next_seq, SQL by join (research's full escape)": (
        _EE, _NS, _in_next_seq(f'    run_sql = conn.execute\n    run_sql({_SPLIT}, (user_id,))'), "`.execute` held, passed or returned"),
    "blobopen in next_seq": (_EE, _NS, _in_next_seq('    conn.blobopen("edges", "json", 1)'), "`.blobopen` of the database API"),
    "attrgetter in next_seq": (_EE, _NS, _in_next_seq('    import operator\n    operator.attrgetter("execute")(conn)("SELECT 1")'),
                               "`.attrgetter`, an accessor"),
    "methodcaller in next_seq": (_EE, _NS, _in_next_seq('    import operator\n    operator.methodcaller("execute", "SELECT 1")(conn)'),
                                 "`.methodcaller`, an accessor"),
    "`from operator import attrgetter` in next_seq": (
        _EE, _NS, _in_next_seq('    from operator import attrgetter\n    attrgetter("execute")(conn)("SELECT 1")'), "`attrgetter` imported"),
    "migration._rows from next_seq (W3)": (
        _EE, _NS, _in_next_seq(f'    from . import migration\n    migration._rows(conn, {_SPLIT}, (user_id,))'),
        "a non-literal SQL site not in the reviewed list"),
    "the derived name imported under another name (research's recheck)": (
        _EE, _NS, _in_next_seq(f'    from .migration import _rows as r\n    r(conn, {_SPLIT}, (user_id,))'),
        "imported under another name"),
    "the derived name held in a local (research's recheck)": (
        _EE, _NS, _in_next_seq(f'    from . import migration\n    run = migration._rows\n    run(conn, {_SPLIT}, (user_id,))'),
        "runs its SQL argument: held, not called"),
    "the derived name through functools.partial (research's recheck)": (
        _EE, _NS, _in_next_seq(f'    import functools\n    from .migration import _rows\n    functools.partial(_rows, conn)({_SPLIT})'),
        "runs its SQL argument: held, not called"),
    "a wrapper passing its parameter to the derived name (the closure)": (
        _EE, _NS, _in_next_seq(f'    from .migration import _rows\n\n    def relay(c, text):\n        return _rows(c, text)\n'
                               f'    relay(conn, {_SPLIT})'), "a non-literal SQL site not in the reviewed list"),
    "a literal getattr of execute": (_EE, _NS, _in_next_seq('    getattr(conn, "execute")("SELECT 1")'), "getattr of `execute`"),
    "a split-SQL write in the doctor": (_DR, _DR_AT, _DR_AT + f'    conn.execute({_SPLIT}, ("u",))\n',
                                        "a non-literal SQL site not in the reviewed list"),
    "blobopen in the doctor": (_DR, _DR_AT, _DR_AT + '    conn.blobopen("edges", "json", 1)\n', "`.blobopen` of the database API"),
    "a passed store read as store._conn in convert_rows": (
        _DM, _DM_AT, _DM_AT + f'    store._conn.execute({_SPLIT}, (user,))\n', "a non-literal SQL site not in the reviewed list"),
    "a listed binding's constant stored from another module (S2-02)": (
        "veracium/_planted.py", None, 'import veracium.store.sqlite as s\ns._APPLIED_SQL = "1"\n', "`_APPLIED_SQL`, a name a listed SQL binding reads"),
    "a store class attribute stored from another module (S2-02)": (
        "veracium/_planted.py", None, 'from veracium.store.sqlite import SqliteStore\nSqliteStore._OP_COLS = ()\n',
        "`_OP_COLS`, a name a listed SQL binding reads"),
}
for _k, _sql in _SHADOW.items():
    R5_SRC_MUTANTS[f"(R-01) {_k} in next_seq"] = (_EE, _NS, _in_next_seq(f'    conn.execute("{_sql}")'),
                                                  "a route around the store's schema")
# Round 6 (R5-01, research's stage-1 B1-B3): the receiver matrix. Each form names its STATIC outcome (the gate's reason, or
# None where the gate has nothing to say) and its RUNTIME one, recorded apart, because a runtime refusal does not establish
# the static claim: "denied" is the authorizer refusing the write; an exception class is a route that dies before any
# SQL now that `MembershipResolver._rows` is `_membership_rows` (the cell asserts that class AND that nothing reached the
# store, since "it raised" would pass a plant that raised for another reason); "ran" is a read that completes.
_NOWHERE = '"".join(("UP", "DA", "TE ed", "ges SE", "T js", "on=rep", "lace(js", "on, \'0.8\', \'1.8\')"))'
_CALL = f"self._rows(conn, {_SPLIT}, (user_id,))"
_MOD = "    from . import migration as m_\n"
_RES = "    from ..scope_read import MembershipResolver as R_\n"
_SELF_BOUND = "`self` bound other than as a plain method's first parameter"
_OWN_HELD = "a module of src/ held as a value"
_LOCAL_CLASS = "a class inside a function"
_SELF_READ = "`self` read where no plain method's first parameter reaches it"
_UNLISTED = "a non-literal SQL site not in the reviewed list"
_HELD = "runs its SQL argument: held, not called"
_SUBCLASS = "        from .migration import _rows\n        def g(self, conn, s):\n            return self._projection(self, conn, s)\n"
R6_RECEIVER = {
    # the reviewer's plant, and the binders of the name
    "P0 a module imported as self (the reviewer's)": ("    from . import migration as self\n    " + _CALL, _SELF_BOUND, "denied"),
    "P2 assignment": (_MOD + "    self = m_\n    " + _CALL, _SELF_BOUND, "denied"),
    "P3 a for target": (_MOD + "    for self in (m_,):\n        " + _CALL, _SELF_BOUND, "denied"),
    "P4 a walrus in a condition": (_MOD + "    if (self := m_):\n        " + _CALL, _SELF_BOUND, "denied"),
    "P5 a nested def's parameter": (_MOD + f"    def g(self):\n        return {_CALL}\n    g(m_)", _SELF_BOUND, "denied"),
    "P6 a lambda's parameter": (_MOD + f"    (lambda self: {_CALL})(m_)", _SELF_BOUND, "denied"),
    "P7 import … as self": ("    import veracium.store.migration as self\n    " + _CALL, _SELF_BOUND, "denied"),
    "P8 a match capture": (_MOD + "    match m_:\n        case self:\n            " + _CALL, _SELF_BOUND, "denied"),
    "P9 a class named self": ("    class self:\n        from .migration import _rows\n    " + _CALL, _SELF_BOUND, "denied"),
    "P10 global self": ("    global self\n    from . import migration as self\n    " + _CALL, _SELF_BOUND, "denied"),
    "P11 with … as self": (_MOD + "    import contextlib\n    with contextlib.nullcontext(m_) as self:\n        " + _CALL,
                           _SELF_BOUND, "denied"),
    "G1 globals()['self'] binds nothing the walk sees": (_MOD + '    globals()["self"] = m_\n    ' + _CALL, _SELF_READ, "denied"),
    # the name is a real method's first parameter: the rule that refuses is the call's
    "P12 method-shaped, no such member": (
        _MOD + f"    class K:\n        def f(self, conn, user_id):\n            {_CALL}\n    K.f(m_, conn, user_id)", _UNLISTED, "denied"),
    "P13 method-shaped, its own _rows member": (
        _MOD + f"    class K:\n        def _rows(self, *a):\n            return []\n        def f(self, conn, user_id):\n"
        f"            {_CALL}\n    K.f(m_, conn, user_id)", _UNLISTED, "denied"),
    # held references (the verdict's sibling)
    "P1 held: run = self._rows": (f"    from . import migration as self\n    run = self._rows\n    run(conn, {_SPLIT}, (user_id,))",
                                  _HELD, "denied"),
    "P14 held, passed as an argument": (
        f"    from . import migration as self\n    (lambda f: f(conn, {_SPLIT}, (user_id,)))(self._rows)", _HELD, "denied"),
    "X1 a literal getattr of the derived name (B3)": (_MOD + f'    getattr(m_, "_rows")(conn, {_SPLIT}, (user_id,))',
                                                      "getattr of `_rows`", "denied"),
    # B1: a method reached unbound. The rename leaves it nothing to reach, so each raises before any SQL; stage 2's
    # closures refuse the forms statically too, for the module held as a value or the class inside a function
    "U1 R_._projection(module, conn, sql)": (_MOD + _RES + f"    R_._projection(m_, conn, {_NOWHERE})", _OWN_HELD, AttributeError),
    "U2 held f = R_._projection": (_MOD + _RES + f"    f_ = R_._projection\n    f_(m_, conn, {_NOWHERE})", _OWN_HELD, AttributeError),
    "U3 a subclass importing _rows": (_RES + "    class K_(R_):\n" + _SUBCLASS + f"    K_.g(K_, conn, {_NOWHERE})", _LOCAL_CLASS, TypeError),
    "U4 types.MethodType": (_MOD + _RES + f"    import types\n    types.MethodType(R_._projection, m_)(conn, {_NOWHERE})",
                            _OWN_HELD, AttributeError),
    "U5 a subclass through an alias base": (_RES + "    B_ = R_\n    class K_(B_):\n" + _SUBCLASS + f"    K_.g(K_, conn, {_NOWHERE})",
                                            _LOCAL_CLASS, TypeError),
    "U6 a super() route": (_RES + "    class K_(R_):\n        from .migration import _rows\n        @classmethod\n"
                           f"        def g(cls, conn, s):\n            return super()._projection(cls, conn, s)\n    K_.g(conn, {_NOWHERE})",
                           _LOCAL_CLASS, TypeError),
    "X5 a literal getattr of the method": (_MOD + _RES + f'    getattr(R_, "_projection")(m_, conn, {_NOWHERE})', _OWN_HELD, AttributeError),
    # the three ways round the rename research tried, with the new name
    "U7 _rows imported under the method's name": (
        _RES + f"    class K_(R_):\n        from .migration import _rows as _membership_rows\n    K_._projection(K_, conn, {_NOWHERE})",
        "imported under another name", "denied"),
    "U8 a class attribute from the imported _rows": (
        _RES + "    class K_(R_):\n        from .migration import _rows\n        _membership_rows = _rows\n"
        f"    K_._projection(K_, conn, {_NOWHERE})", _HELD, "denied"),
    "U9 a subclass method calling _rows": (
        _MOD + _RES + "    class K_(R_):\n        def _membership_rows(self, k, i):\n            return m_._rows(k, i)\n"
        f"    K_._projection(object.__new__(K_), conn, {_NOWHERE})", "called with no SQL argument the gate can read", "denied"),
    # controls. C3 is the reviewer's own read control, and its static outcome CHANGED this round (the verdict allows
    # refusing an unresolved receiver); its runtime did not. The "legitimate method" control has no subject after the
    # rename: `self._membership_rows` is no derived name, and the honest tree is what covers its two calls
    "C1 control: the same write through a named module": (
        f"    from . import migration as reader\n    reader._rows(conn, {_SPLIT}, (user_id,))", _UNLISTED, "denied"),
    "C2 control: a literal read through a named module": (
        '    from . import migration as reader\n    reader._rows(conn, "SELECT json FROM edges WHERE user_id=?", (user_id,))', None, "ran"),
    "C3 control: the read through a module spelled self": (
        '    from . import migration as self\n    self._rows(conn, "SELECT json FROM edges WHERE user_id=?", (user_id,))', _SELF_BOUND, "ran"),
}
_Q = f"({_SPLIT}, (user_id,))"
_P = f"(conn, {_SPLIT}, (user_id,))"
_GF = 'Formatter().get_field("0.execute", (conn,), {})[0]'
_FAKE = ("    class Mt_(type):\n        def __instancecheck__(c, o):\n            return True\n"
         "    class P_(metaclass=Mt_):\n        __match_args__ = (%r,)\n")
_TEXT = f'"c.exe" + "cute(s, p)", globals={{"c": conn, "s": {_SPLIT}, "p": (user_id,)}}'
_EVAL = '"conn.exe" "cute(\'UP\' \'DATE edges SET json=json\')"'
_MEMBER = "a member src/ does not use"
_MODULE = "a module src/ does not import"
_HELD_MOD = "a module held as a value"
_DUNDER = "a dunder src/ does not read"
_REACH = "which reaches a namespace, a module or an evaluator"
_OWN = "a name another module of src/ imported, reached through it"
_SITE = "`__import__` outside its two reviewed calls"
_MATCH = "`match`, whose patterns read an attribute with no attribute node"
_ANN = "an annotation a library would evaluate as code"
_BMOD = "    from pydantic import BaseModel\n"
_BRACKETS = '    o_, c_, s_ = "(", ")", "UP" + "DATE edges SET json=json"\n'
# stage 2 (research 1a493ea3; the owner: "Close members too (Recommended)"). Each form wrote, or was accepted by gate and
# census, at e25eb0a7. A form's name says which rule it answers; the line each rule stops short of is the README's
R6_IMPORT = {
    # N1: a pattern reads an attribute with no attribute node, and positionally with no keyword either
    "M1 a class pattern on a module": (_MOD + f"    match m_:\n        case object(_rows=run):\n            run{_P}", _MATCH, "denied"),
    "M2 a class pattern on the connection": (f"    match conn:\n        case object(execute=run):\n            run{_Q}", _MATCH, "denied"),
    "M3 positional, __match_args__, the connection": (_FAKE % "execute" + f"    match conn:\n        case P_(run):\n            run{_Q}", _MATCH, "denied"),
    "M4 positional, __match_args__, a module": (_MOD + _FAKE % "_rows" + f"    match m_:\n        case P_(run):\n            run{_P}", _MATCH, "denied"),
    # N2: a module src/ does not name
    "L1 import string": (f"    import string as g_\n    run = g_.{_GF}\n    run{_Q}", _MODULE, "denied"),
    "L2 from string import": (f"    from string import Formatter\n    run = {_GF}\n    run{_Q}", _MODULE, "denied"),
    "L6 logging.config": (f'    import logging.config\n    run = logging.config.BaseConfigurator({{}}).resolve("veracium.store.migration._rows")\n    run{_P}',
                          _MODULE, "denied"),
    "T1 timeit": (f"    import timeit\n    timeit.timeit({_TEXT}, number=1)", _MODULE, "denied"),
    "T2 cProfile": (f'    import cProfile\n    cProfile.runctx("c.exe" + "cute(s, p)", {{"c": conn, "s": {_SPLIT}, "p": (user_id,)}}, {{}})', _MODULE, "denied"),
    "T3 xmlrpc": (f'    from xmlrpc.server import resolve_dotted_attribute as r_\n    r_(conn, "execute"){_Q}', _MODULE, "denied"),
    "S1 subprocess": ('    import subprocess\n    subprocess.run(["true"])', _MODULE, None),
    "H5 __import__ of an unlisted module": (f'    run = __import__("string").{_GF}\n    run{_Q}', _SITE, "denied"),
    # N3: a member src/ does not use, one attribute past a listed module
    "L6b from logging import config": ('    from logging import config as c_\n    c_.BaseConfigurator({})', _MEMBER, "ran"),
    "R1 urllib.request.string": (f"    import urllib.request as u_\n    run = u_.string.{_GF}\n    run{_Q}", _MEMBER, "denied"),
    "R3 enum.bltns": (f'    import enum as e_\n    run = e_.bltns.getattr(conn, "exe" + "cute")\n    run{_Q}', _MEMBER, "denied"),
    "R4 dataclasses.inspect": (f'    import dataclasses as d_\n    run = dict(d_.inspect.getmembers(conn))["exe" + "cute"]\n    run{_Q}', _MEMBER, "denied"),
    "R5 logging.handlers.pickle": ("    import logging.handlers as h_\n    h_.pickle", _MEMBER, "ran"),
    "R9 os.path.sys": ("    import os as o_\n    o_.path.sys", _MEMBER, "ran"),
    "H4 from urllib.request import string": (f"    from urllib.request import string as g_\n    run = g_.{_GF}\n    run{_Q}", _MEMBER, "denied"),
    "H6 __import__ of a listed dotted name": (f'    run = __import__("urllib.request").request.string.{_GF}\n    run{_Q}', _SITE, "denied"),
    "H10 a listed submodule by from-import": ("    from os import path as p_\n    p_.sys", _MEMBER, "ran"),
    "H11 from logging import handlers": ("    from logging import handlers as h_\n    h_.pickle", _MEMBER, "ran"),
    "H17 from urllib import request": (f"    from urllib import request as r_\n    run = r_.string.{_GF}\n    run{_Q}", _MEMBER, "denied"),
    "H18 a from-imported submodule held": (f"    from urllib import request as r_\n    x_ = r_\n    run = x_.string.{_GF}\n    run{_Q}", _HELD_MOD, "denied"),
    "R10 pathlib.Path.parser": ("    from pathlib import Path\n    Path.parser.sys", "an attribute of a class that holds a module", "ran"),
    "G1 typing.get_type_hints": (f'    import typing as y_\n    def g_(): pass\n    g_.__annotations__ = {{"x": "c.exe" + "cute(s, p)"}}\n'
                                 f'    y_.get_type_hints(g_, {{"c": conn, "s": {_SPLIT}, "p": (user_id,)}})', _MEMBER, "denied"),
    "E1 EntryPoint.load": (f'    from importlib.metadata import EntryPoint\n    EntryPoint("x", "veracium.store.migration:_rows", "g").load(){_P}', _MEMBER, "denied"),
    "S2 os.system": ('    import os as o_\n    o_.system("true")', _MEMBER, None),
    "S3 os.popen": ('    import os as o_\n    o_.popen("true").close()', _MEMBER, None),
    # N4: a module read as a value, which no member rule then sees
    "H1 a module held": (f"    import urllib.request as u_\n    x_ = u_\n    run = x_.string.{_GF}\n    run{_Q}", _HELD_MOD, "denied"),
    "H2 a dotted module held": (f"    import urllib.request\n    x_ = urllib.request\n    run = x_.string.{_GF}\n    run{_Q}", _HELD_MOD, "denied"),
    "H3 a module passed": (f"    import urllib.request as u_\n    run = (lambda m: m.string.{_GF})(u_)\n    run{_Q}", _HELD_MOD, "denied"),
    # N5: the named import route, and `__import__` the gate cannot read
    "I1 import_module through importlib.metadata": (f'    import importlib.metadata as m_\n    run = m_.import_module("string").{_GF}\n    run{_Q}', _REACH, "denied"),
    "I2 from importlib import import_module": (f'    from importlib import import_module\n    run = import_module("string").{_GF}\n    run{_Q}', _REACH, "denied"),
    "H7 __import__ of a computed name": (f'    run = __import__("str" + "ing").{_GF}\n    run{_Q}', _SITE, "denied"),
    "H15 __import__ held": (f'    i_ = __import__\n    run = i_("string").{_GF}\n    run{_Q}', _SITE, "denied"),
    "H16 __import__ of a listed module, a listed member": ('    __import__("json").dumps({})', _SITE, "ran"),
    "H12 globals()": ('    b_ = globals()["__buil" + "tins__"]\n    run = b_["getattr"](conn, "exe" + "cute")\n' + f"    run{_Q}", _REACH, "denied"),
    "H13 locals()": (f'    import urllib.request as u_\n    run = locals()["u_"].string.{_GF}\n    run{_Q}', _REACH, "denied"),
    # N6: a module reached through another module of src/
    "H8 an own module's import": ("    from . import migration as m_\n    m_.sqlite3", _OWN, "ran"),
    "H9 from an own module, its import": ("    from .migration import sqlite3 as q_\n    q_.connect", _OWN, "ran"),
    "H14 an own module held": ("    from . import migration as m_\n    x_ = m_\n    x_.sqlite3", _OWN_HELD, "ran"),
    "H19 an own module's from-import": ("    from . import migration as m_\n    m_.BaseModel", _OWN, "ran"),
    "H20 from an own module, its from-import": ("    from .migration import BaseModel as B_\n    B_", _OWN, "ran"),
    "H21 a second own module deep": ("    from .. import store as s_\n    s_.migration.sqlite3", _OWN, "ran"),
    "H22 an own module held by another, from-imported": ("    from .sqlite import _semantic as z_\n    z_.hashlib", _OWN, None),
    # not a route: the gate has always refused this, and the record says so
    "T4 a held execute as a Thread target": (f'    import threading as h_\n    h_.Thread(target=conn.execute, args=({_SPLIT}, (user_id,))).run()',
                                             "held, passed or returned, not called", "denied"),
    # N7: a dunder src/ does not read
    "D1 a function's __globals__": ('    import json as j_\n    b_ = j_.dumps.__globals__["__builtins__"]\n    run = b_["getattr"](conn, "exe" + "cute")\n' + f"    run{_Q}", _DUNDER, "denied"),
    "D2 a lambda's __globals__": ('    b_ = (lambda: 0).__globals__["__builtins__"]\n    run = b_["getattr"](conn, "exe" + "cute")\n' + f"    run{_Q}", _DUNDER, "denied"),
    "D3 __builtins__": ('    run = __builtins__["getattr"](conn, "exe" + "cute")\n' + f"    run{_Q}", _DUNDER, "denied"),
    "D4 __loader__": ("    __loader__", _DUNDER, None),
    "D5 a subclass walk": ("    ().__class__.__base__.__subclasses__()", _DUNDER, "ran"),
    "D6 a literal getattr of a dunder": ('    import json as j_\n    b_ = getattr(j_.dumps, "__globals__")["__builtins__"]\n    run = b_["getattr"](conn, "exe" + "cute")\n' + f"    run{_Q}", _DUNDER, "denied"),
    # N8: text a library evaluates. A class inside a function is how an annotation sees a local
    "P1 a quoted annotation": (_BMOD + f"    class K_(BaseModel):\n        a: {_EVAL}", _ANN, "denied"),
    "P2 TypeAdapter on a string": (f"    from pydantic import TypeAdapter\n    TypeAdapter({_EVAL})", "`TypeAdapter` outside its one reviewed call", "denied"),
    "P3 an annotation held in a name": (_BMOD + '    s_ = "conn.exe" + "cute(\'UP\' \'DATE edges SET json=json\')"\n    class K_(BaseModel):\n        a: s_', _LOCAL_CLASS, "denied"),
    # every constant of P4 and P5 parses, to a name: the string rule alone would pass both, at any depth
    "P4 an annotation of joined strings": (_BMOD + _BRACKETS + "    class K_(BaseModel):\n        a: \"conn.execute\" + o_ + \"s_\" + c_", _ANN, "denied"),
    "P5 an f-string annotation": (_BMOD + _BRACKETS + "    class K_(BaseModel):\n        a: f\"conn.execute{o_}s_{c_}\"", _ANN, "denied"),
    "P6 a quoted annotation inside Optional": (_BMOD + f"    from typing import Optional\n    class K_(BaseModel):\n        a: Optional[{_EVAL}]", _ANN, "denied"),
    "P10 a string inside a quoted annotation": (_BMOD + "    class K_(BaseModel):\n        a: \"\\\"conn.exe\\\" \\\"cute('UP' 'DATE edges SET json=json')\\\"\"", _ANN, "denied"),
    "P7 type() building a model": (_BMOD + f'    type("K_", (BaseModel,), {{"__annot" + "ations__": {{"a": {_EVAL}}}}})', "`type` building a class", "denied"),
    "P8 TypeAdapter under another name": (f"    from pydantic import TypeAdapter as T_\n    T_({_EVAL})", "imported under another name", "denied"),
    "P9 model_rebuild": (_BMOD + "    BaseModel.model_rebuild", _REACH, "ran"),
    # controls: what a listed member, a read and a type annotation still may do
    "C1 control: a literal read on the connection": ('    conn.execute("SELECT 1")', None, "ran"),
    "C2 control: a listed member": ("    import json as j_\n    j_.dumps({})", None, "ran"),
    "C3 control: a listed from-import": ("    from typing import Any\n    x_: Any = 1", None, "ran"),
    "C4 control: a quoted type": ('    x_: "dict | None" = None', None, "ran"),
}
_CLI = "veracium/cli.py"
_CLI_AT = "    if not args.i_have_quiesced or args.backup is None:\n"
_MG = "veracium/store/migration.py"
R5_SRC_MUTANTS.update({
    "(Q1) cli: args rebound and .backup called": (_CLI, _CLI_AT, '    import shutil as args\n    args.backup("x")\n' + _CLI_AT,
                                                  "`.backup` of the database API"),
    "(Q2) cli: args.backup called, unrebound": (_CLI, _CLI_AT, '    args.backup("x")\n' + _CLI_AT, "`.backup` of the database API"),
    "(Q4) cli: args rebound, the reads unchanged": (_CLI, _CLI_AT, "    import shutil as args\n" + _CLI_AT,
                                                    "`.backup` of the database API"),
    "(Q3) the named attribute read in another function": ("veracium/_planted.py", None, "def f(args):\n    return args.backup\n",
                                                          "`.backup` of the database API"),
    "(R1) a function spelled _write_edge_row": (
        _EE, _NS, _in_next_seq(f"    def _write_edge_row(conn, sql, p):\n        return conn.execute(sql, p)\n"
                               f"    _write_edge_row(conn, {_SPLIT}, (user_id,))"), _UNLISTED),
    "(R3) migration.py: a literal json write": (
        _MG, "def _rows(", "def _plant(conn, user_id):\n    conn.execute(\"UPDATE edges SET json=json WHERE user_id=?\", (user_id,))\n\n\n"
        "def _rows(", "an edges json write outside the write method"),
    "(R3b) migration.py: assembled SQL through _rows": (
        _MG, "def _rows(", f"def _plant(conn, user_id):\n    _rows(conn, {_SPLIT}, (user_id,))\n\n\ndef _rows(", _UNLISTED),
    "(S1) a static method's self": ("veracium/_planted.py", None, "class K:\n    @staticmethod\n    def f(self):\n        return self\n",
                                    _SELF_BOUND),
    "(S2) a class method's self": ("veracium/_planted.py", None, "class K:\n    @classmethod\n    def f(self):\n        return self\n",
                                   _SELF_BOUND),
    "(S3) a decorator the rule does not know": ("veracium/_planted.py", None, "class K:\n    @wrap\n    def f(self):\n        return self\n",
                                                _SELF_BOUND),
    "(S4) a default is evaluated outside the method": ("veracium/_planted.py", None, "class K:\n    def f(self, x=self):\n        return x\n",
                                                       _SELF_READ),
    "(S5) self as a later parameter": ("veracium/_planted.py", None, "class K:\n    def f(this, self):\n        return self\n", _SELF_BOUND),
    "(S6) a module-level def's self": ("veracium/_planted.py", None, "def f(self):\n    return self\n", _SELF_BOUND),
})
R5_MUTANTS.update({
    "(R2) sqlite.py: a named module, the store's connection": (
        _RECOMPUTE, _RECOMPUTE + f'\n        from . import migration\n        migration._rows(self._conn, {_SPLIT}, ("u",))',
        "the connection reached in a form the gate does not resolve"),
    "(R2b) sqlite.py: self rebound inside a store method": (
        _RECOMPUTE, _RECOMPUTE + f'\n        store = self\n        from . import migration as self\n        self._rows(store._conn, {_SPLIT}, ("u",))',
        _SELF_BOUND),
})
R5_SRC_CONTROLS = {
    "a new literal read in next_txn": (
        _EE, '    transaction (V-TXN-ALLOC) — two connections cannot read the same maximum."""\n',
        '    transaction (V-TXN-ALLOC) — two connections cannot read the same maximum."""\n    conn.execute("SELECT 1")\n'),
    "an unrelated .backup-named read stays the named exception's": (
        "veracium/_planted.py", None, "def f(args):\n    return args.description\n"),
}
# the harmless controls: each edit is one the gate must PASS
R5_CONTROLS = {
    "a new literal read": (_RECOMPUTE, _RECOMPUTE + '\n        self._conn.execute("SELECT 1 FROM edges WHERE id=?", (edge_id,))'),
    "a new literal write to another table": (
        _RECOMPUTE, _RECOMPUTE + '\n        self._conn.execute("UPDATE confirmations SET request_digest=? WHERE edge_id=?", '
                    '("x", edge_id))'),
    "an edit in a function no listed site reads": (
        "    def _edge_in_refusal(self, user_id: str, edge_id: str) -> bool:\n",
        "    def _edge_in_refusal(self, user_id: str, edge_id: str) -> bool:\n        pass\n"),
    "a commit and a rollback": (_RECOMPUTE, _RECOMPUTE + '\n        if not self._conn.in_transaction:\n'
                                '            self._conn.commit()\n            self._conn.rollback()'),
}


def _r5_planted(old, new):
    src = SQLITE.read_text()
    if old is None:
        return src + new
    assert src.count(old) == 1, f"the anchor occurs {src.count(old)} times — re-anchor it: {old[:60]!r}"
    out = src.replace(old, new)
    assert out != src
    return out


@pytest.mark.parametrize("name", list(R5_MUTANTS))
def test_the_gate_refuses_each_round_5_form_for_its_reason(name):
    """R4-01 (a)–(d): each form planted on a copy of sqlite.py — the write method unchanged — is refused by the static
    gate, and one of the problems is the form's own named reason (not a neighbour rule catching it by accident)."""
    old, new, reason = R5_MUTANTS[name]
    bad = _gate(_r5_planted(old, new))
    assert any(reason in b for b in bad), f"{name}: not refused for its reason {reason!r}: {bad}"


def _r5_others(rel, old, new):
    others = {str(p.relative_to(SRC)): p.read_text() for p in sorted(SRC.rglob("*.py")) if p.resolve() != SQLITE.resolve()}
    if old is None:
        return {**others, rel: new}
    assert others[rel].count(old) == 1, f"the anchor occurs {others[rel].count(old)} times — re-anchor it: {old[:60]!r}"
    return {**others, rel: others[rel].replace(old, new)}


@pytest.mark.parametrize("name", list(R5_SRC_MUTANTS))
def test_the_gate_refuses_each_form_outside_the_store_for_its_reason(name):
    """Research's stage 2 (S2-01): wherever the connection travels, the rule meets it at the call. Each plant goes into
    an honest OTHER src module, sqlite.py unchanged, and is refused for its own reason. The escape was the full one:
    a split-SQL write inside inventoried next_seq passed this gate and the runtime authorizer and stored 1.8."""
    rel, old, new, reason = R5_SRC_MUTANTS[name]
    bad = _gate(SQLITE.read_text(), _r5_others(rel, old, new))
    assert any(reason in b for b in bad), f"{name}: not refused for its reason {reason!r}: {bad}"


@pytest.mark.parametrize("name", list(R5_SRC_CONTROLS))
def test_the_gate_passes_each_harmless_edit_outside_the_store(name):
    assert _gate(SQLITE.read_text(), _r5_others(*R5_SRC_CONTROLS[name])) == []


@pytest.mark.parametrize("name", list(R6_RECEIVER))
def test_each_receiver_form_has_its_stated_static_and_runtime_outcome(name, tmp_path, monkeypatch, _edges_write_tripwire):
    """R5-01's matrix, static and runtime apart. Static: the plant in next_seq, the gate's own reason or, where the
    rename leaves nothing to refuse, no problem. Runtime: the same lines run inside the journal's next_seq on a real store
    under the authorizer, with the exact outcome the table states and, for every route, the store unchanged."""
    _plant_outcome(name, *R6_RECEIVER[name], tmp_path, monkeypatch, _edges_write_tripwire)


@pytest.mark.parametrize("name", list(R6_IMPORT))
def test_each_import_form_has_its_stated_static_and_runtime_outcome(name, tmp_path, monkeypatch, _edges_write_tripwire):
    """Stage 2's matrix (1a493ea3), read the same way. A runtime of None is static only: those forms start a second
    process or read a name and do nothing, and none was run."""
    _plant_outcome(name, *R6_IMPORT[name], tmp_path, monkeypatch, _edges_write_tripwire)


def _plant_outcome(name, lines, reason, runtime, tmp_path, monkeypatch, _edges_write_tripwire):
    bad = _gate(SQLITE.read_text(), _r5_others(_EE, _NS, _in_next_seq(lines)))
    if reason is None:
        assert bad == [], bad
    else:
        assert any(reason in b for b in bad), f"{name}: not refused for its reason {reason!r}: {bad}"
    if runtime is None:
        return
    path = tmp_path / "plant.db"
    s = SqliteStore(str(path))
    s.add_edge(_edge("e", S.Volatility.SLOW, 0.9))
    before = _snapshot(path)
    scope = {"__name__": "veracium.store.edge_events", "__package__": "veracium.store"}
    exec(compile("def planted(conn, user_id):\n" + lines + "\n", "<plant>", "exec"), scope)
    real = SQ.next_seq

    def next_seq(conn, user_id):
        scope["planted"](conn, user_id)
        return real(conn, user_id)
    monkeypatch.setattr(SQ, "next_seq", next_seq)

    def drive():
        with s._lock, s._write_txn():
            s._recompute_edge_row("e", {"valid_from": OLD, "observed_at": OLD, "confidence": 0.8})
    if runtime == "ran":
        drive()
        assert _edges_write_tripwire == [] and _row(s, "e").provenance.confidence == 0.8
        return
    with pytest.raises(sqlite3.DatabaseError if runtime == "denied" else runtime) as ex:
        drive()
    if runtime == "denied":
        assert "not authorized" in str(ex.value) and len(_edges_write_tripwire) == 1, (ex.value, _edges_write_tripwire)
    else:
        assert type(ex.value) is runtime and _edges_write_tripwire == [], (ex.value, _edges_write_tripwire)
    assert _snapshot(path) == before, "something reached the store"
    _edges_write_tripwire.clear()


_SQ_AT = "    def upsert_embedding(self"


def _in_sqlite(body):
    text = SQLITE.read_text()
    assert text.count(_SQ_AT) == 1, f"the anchor occurs {text.count(_SQ_AT)} times — re-anchor it"
    return text.replace(_SQ_AT, "    def planted(self):\n" + body + "\n\n" + _SQ_AT)


@pytest.mark.parametrize("body", [
    "        match self:\n            case object(_conn=object(execute=run)):\n                run('SELECT 1')",
    "        match self._conn:\n            case object(execute=run):\n                run('SELECT 1')"], ids=["Q2 nested, _conn unspelled", "Q1 the subject spelled"])
def test_a_class_pattern_inside_the_store_is_refused(body):
    others = _r5_others(_EE, _NS, _NS)
    assert not any(_MATCH in b for b in _gate(SQLITE.read_text(), others))
    assert any(_MATCH in b for b in _gate(_in_sqlite(body), others))


def test_a_class_pattern_from_a_new_module_is_refused():
    """O1: the same reach from a module the inventory has not met, holding a store."""
    plant = "def f(store):\n    match store:\n        case object(_conn=object(execute=run)):\n            run('SELECT 1')\n"
    bad = _gate(SQLITE.read_text(), _r5_others("veracium/_planted.py", None, plant))
    assert any(_MATCH in b for b in bad), bad


@pytest.mark.parametrize("plant", ["from .store.migration import *\n", "from os import *\n"], ids=["relative", "absolute"])
def test_a_star_import_is_refused(plant):
    """S1 (research 4e8529bd). It binds names no binder walk sees, so the relative form reached neither N3, N4 nor N6. A
    star is legal only at module level, so this plant is a new module's and not a row of next_seq."""
    bad = _gate(SQLITE.read_text(), _r5_others("veracium/_planted.py", None, plant))
    assert any("a star import, whose names no rule here can see" in b for b in bad), bad


@pytest.mark.parametrize("slot, refused", [
    ('Literal["within-episode-v1"]', False), ("int | None", False), ('"dict | None"', False),
    ('"\'a\' + \'b\'"', True), ('"\'\\\'a\\\' + \\\'b\\\'\'"', True), ('"\'a\' % \'b\'"', True), ('"\'a\' * 2"', True), ('"f()"', True)],
    ids=["a Literal's value", "a union", "a quoted union", "joined in a string", "joined two strings deep", "formatted", "repeated", "a call"])
def test_an_annotation_slot_reads_as_its_rule_says(slot, refused):
    """The rule alone, on the shapes the honest tree holds and the shapes that build text."""
    assert (_annotation_problem(ast.parse(slot, mode="eval").body) is not None) is refused


def _src_uses():
    modules, members, dunders, other = set(), {}, set(), []      # `other`: only `__import__`, which is judged by site
    for p in sorted(SRC.rglob("*.py")):
        tree = ast.parse(p.read_text())
        par = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
        for kind, name, member, n in _import_uses(tree, par):
            if kind == "module":
                modules.add(name)
            elif kind == "member":
                members.setdefault(name, set()).add(member)
            elif kind == "dunder":
                dunders.add(name)
            else:
                other.append((str(p), kind, name))
    return modules, members, dunders, other


def test_the_closed_tables_are_exactly_what_src_uses():
    """Both ways: a use the tables lack is the gate's to refuse, and a row nothing uses is a route left open for nothing.
    The tables are frozen data; this compares them with a fresh read of src/, and never derives them."""
    modules, members, dunders, other = _src_uses()
    assert [k for _p, k, _n in other] == ["dynamic"] * len(IMPORT_SITES) == ["dynamic"] * 2, other
    assert {m: set(v) for m, v in SRC_IMPORTS.items() if v} == members
    assert modules <= set(SRC_IMPORTS) and set(SRC_IMPORTS) - modules <= set(members)
    assert SRC_DUNDERS == dunders


def _gate_r1():
    return _gate(SQLITE.read_text(), _r5_others(_EE, _NS, _in_next_seq(R6_IMPORT["R1 urllib.request.string"][0])))


def _audited_rows():
    """Each table row whose module imports here, with what it holds. The tables stay AST-only: this reads the interpreter
    the suite runs on, so a new Python's route is caught by this cell and not by a reviewer."""
    for module, members in sorted(SRC_IMPORTS.items()):
        try:
            mod = importlib.import_module(module)
        except ImportError:
            assert module.split(".")[0] in {m.split(".")[0] for m in UNAUDITED_MODULES}, module
            continue
        for member in sorted(members):
            yield module, member, getattr(mod, member, None)


def test_no_listed_member_holds_a_route_to_an_unlisted_module():
    """Research's read (9e5daf2f, B2), one attribute level, classes and modules: the walk reads through a listed module
    and stops at anything else, so a class holding a module is a route it cannot see. Each is named, and refused by name."""
    seen = set()
    for module, member, value in _audited_rows():
        if isinstance(value, types.ModuleType):
            assert f"{module}.{member}" in SRC_IMPORTS, (module, member, value)
        elif isinstance(value, type):
            for k in dir(value):
                try:
                    held = inspect.getattr_static(value, k)
                except AttributeError:
                    continue
                if isinstance(held, types.ModuleType):
                    seen.add((module, member, k))
    assert seen <= CLASS_HELD_MODULES, seen - CLASS_HELD_MODULES      # by the interpreter: `Path.parser` is 3.13's
    assert {k for _m, _c, k in CLASS_HELD_MODULES} <= REACH_ATTRIBUTES


def test_a_reach_attribute_moves_the_gate_when_it_moves(monkeypatch):
    others = _r5_others(_EE, _NS, _in_next_seq(R6_IMPORT["R10 pathlib.Path.parser"][0]))
    why = R6_IMPORT["R10 pathlib.Path.parser"][1]
    assert any(why in b for b in _gate(SQLITE.read_text(), others))
    monkeypatch.setattr(sys.modules[__name__], "REACH_ATTRIBUTES", set())
    assert not any(why in b for b in _gate(SQLITE.read_text(), others))


def test_the_two_import_calls_are_frozen(monkeypatch):
    others = _r5_others(_EE, _NS, _NS)
    assert not any(_SITE in b for b in _gate(SQLITE.read_text(), others))
    monkeypatch.setattr(sys.modules[__name__], "IMPORT_SITES", {k: "0" * 64 for k in IMPORT_SITES})
    assert sum(_SITE in b for b in _gate(SQLITE.read_text(), others)) == 2


def test_a_closed_table_moves_the_gate_when_it_moves(monkeypatch):
    """The unpatched call runs first, in the same test: a memo that omits a table then fails here and not by order."""
    assert any(_MEMBER in b for b in _gate_r1())
    monkeypatch.setitem(SRC_IMPORTS, "urllib.request", SRC_IMPORTS["urllib.request"] | {"string"})
    assert not any(_MEMBER in b for b in _gate_r1())


def test_a_dunder_row_moves_the_gate_when_it_moves(monkeypatch):
    plant = _in_next_seq(R6_IMPORT["D4 __loader__"][0])
    others = _r5_others(_EE, _NS, plant)
    assert any(_DUNDER in b for b in _gate(SQLITE.read_text(), others))
    monkeypatch.setattr(sys.modules[__name__], "SRC_DUNDERS", SRC_DUNDERS | {"__loader__"})
    assert not any(_DUNDER in b for b in _gate(SQLITE.read_text(), others))


def test_a_reach_name_moves_the_gate_when_it_moves(monkeypatch):
    others = _r5_others(_EE, _NS, _in_next_seq(R6_IMPORT["H13 locals()"][0]))
    assert any(_REACH in b for b in _gate(SQLITE.read_text(), others))
    monkeypatch.setattr(sys.modules[__name__], "REACH_NAMES", REACH_NAMES - {"locals"})
    assert not any(_REACH in b for b in _gate(SQLITE.read_text(), others))


def test_the_reviewed_own_module_value_is_frozen_with_its_function(monkeypatch):
    """`upsert_embedding` passes `_semantic` on as a value: the one entry. Any edit of the function refuses until it is
    re-reviewed, and the table is read, not the spelling."""
    others = _r5_others(_EE, _NS, _NS)
    assert not any(_OWN_HELD in b for b in _gate(SQLITE.read_text(), others))
    monkeypatch.setattr(sys.modules[__name__], "OWN_MODULE_VALUES", {k: "0" * 64 for k in OWN_MODULE_VALUES})
    assert any(_OWN_HELD in b for b in _gate(SQLITE.read_text(), others))


def test_an_own_module_read_follows_what_that_module_imports():
    """N6 reads another module's text. The plant's own module does not change between the two calls, so a memo that omits
    the bindings serves the first answer to the second."""
    plant = "    from . import migration as m_\n    m_.zz_"
    others = _r5_others(_EE, _NS, _in_next_seq(plant))
    assert not any(_OWN in b for b in _gate(SQLITE.read_text(), others))
    moved = {**others, _MG: "import json as zz_\n" + others[_MG]}
    assert any(_OWN in b for b in _gate(SQLITE.read_text(), moved))


def test_the_one_type_adapter_call_is_frozen(monkeypatch):
    others = _r5_others(_EE, _NS, _NS)
    assert not any("`TypeAdapter` outside" in b for b in _gate(SQLITE.read_text(), others))
    monkeypatch.setattr(sys.modules[__name__], "TYPE_ADAPTER_SITE", {k: "0" * 64 for k in TYPE_ADAPTER_SITE})
    assert any("`TypeAdapter` outside" in b for b in _gate(SQLITE.read_text(), others))


def test_a_closure_over_a_methods_self_is_the_method_s():
    """Rule 4's other half: a nested def or lambda inside a plain method, and a comment edit inside the reviewed
    `_migrate`, change nothing. (Four closures in src/ read `self`; the honest pass holds them, this states the shape.)"""
    plant = "class K:\n    def f(self):\n        def g():\n            return self\n        return (g, lambda: self)\n"
    assert _gate(SQLITE.read_text(), _r5_others("veracium/_planted.py", None, plant)) == []
    assert _gate(SQLITE.read_text(), _r5_others(_CLI, _CLI_AT, "    # a comment edit\n" + _CLI_AT)) == []


def test_a_reviewed_function_may_still_not_call_the_named_attribute(monkeypatch):
    """The exception's two conditions are separate: the digest alone would let a re-review admit a call. With the planted
    `_migrate`'s own digest admitted, its four reads pass and the call alone is refused."""
    rel, key = _CLI, next(iter(DB_NAME_EXCEPTIONS))
    others = _r5_others(_CLI, _CLI_AT, '    args.backup("x")\n' + _CLI_AT)
    fn = next(n for n in ast.parse(others[rel]).body if isinstance(n, ast.FunctionDef) and n.name == "_migrate")
    assert len(_gate(SQLITE.read_text(), others)) == 5, "the four reads and the call, before the digest is admitted"
    monkeypatch.setitem(DB_NAME_EXCEPTIONS, key, _digest(fn))
    bad = _gate(SQLITE.read_text(), others)       # the same text again: the patched table must reach the memo
    assert len(bad) == 1 and "`.backup` of the database API" in bad[0], bad


def test_a_name_parameter_reaching_sql_meets_the_head_rule(monkeypatch):
    """The head rule no longer exempts a bare name: a reviewed, listed site whose SQL is a NAME a parameter reaches is
    refused like any other expression. The entry and binding are admitted, as a re-review would, so the head rule is the
    only problem left."""
    rel, text = "veracium/_planted.py", "def f(conn, stmt):\n    q = stmt\n    return conn.execute(q)\n"
    tree, par, _q, ix = _parsed(text)
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call))
    arg, fn = call.args[0], _scope_of(call, par)
    binding = _sql_binding(tree, par, fn, arg, ix)
    assert binding[0] == ["stmt"], binding
    key = (f"{rel}:f", _digest(arg))
    assert any("not in the reviewed list" in b for b in _gate(SQLITE.read_text(), _r5_others(rel, None, text)))
    monkeypatch.setitem(SRC_NONLITERAL, key, (1, "q", _binding_digest(tree, par, fn, arg, binding, ix)))
    bad = _gate(SQLITE.read_text(), _r5_others(rel, None, text))     # the same text again, the entry admitted
    assert len(bad) == 1 and "reaches SQL whose leading constant does not fix a SELECT" in bad[0], bad


_ALTERS_AT = "ALTERS_V15_TO_V16 = (\n"
_SV = "veracium/store/schema_version.py"
_MIG = "veracium/store/migration.py"
_NOT_ADD = "a ladder statement that is not a literal ADD COLUMN"


@pytest.mark.parametrize("line", ['"UP" + "DATE ed" + "ges SET js" + "on=re" + "place(js" + "on, \'0.8\', \'1.8\')"',
                                  '"UPDATE edges SET json=replace(json, \'0.8\', \'1.8\')"', '"ALTER TABLE edges DROP COLUMN json"', "_NAME"],
                         ids=["split", "literal", "another ALTER", "a name"])
def test_a_ladder_table_statement_is_refused_statically(line):
    """Research's B4, as the round-6 cell promised: when 0018's table landed its first assertion turned over. A statement added
    to a ladder table is refused where it stands, split or not, and the table's reach is closed by `_alters`."""
    assert not any(_NOT_ADD in b for b in _gate(SQLITE.read_text(), _r5_others(_SV, _ALTERS_AT, _ALTERS_AT)))
    bad = _gate(SQLITE.read_text(), _r5_others(_SV, _ALTERS_AT, _ALTERS_AT + f"    {line},\n"))
    assert any(_NOT_ADD in b for b in bad), bad


_ROW = "    ForwardEntry(0, 3, \"read\", _read_episodes_before, (_check_chains,)),\n"
_ELEMENT = "a table element that is neither"
_U = '"UPDATE edges SET json=json"'


@pytest.mark.parametrize("old, new, why", [
    ("*_alters(2, 16, ALTERS_V15_TO_V16),", f"*_alters(2, 16, ({_U},)),", "`_alters` of something other than"),
    ("*_alters(2, 16, ALTERS_V15_TO_V16),", f'ForwardEntry(2, 16, "alter", {_U}, ()),', _ELEMENT),
    (_ROW, _ROW + f'    ForwardEntry(lo=0, v=3, kind="read", step=_read_episodes_before, fields=(_check_chains,)),\n', _ELEMENT),
    (_ROW, _ROW + f'    ForwardEntry(0, 3, "add", _read_episodes_before, ()),\n', _ELEMENT),
    (_ROW, _ROW + f'    ForwardEntry(0, 3, "stamp", 16, ()),\n', _ELEMENT),
    (_ROW, _ROW + f'    ForwardEntry(0, 3, "sideways", _read_episodes_before, ()),\n', _ELEMENT),
    (_ROW, _ROW + f'    ForwardEntry(0, 3, "data", lambda conn, run: conn.execute({_U}), ()),\n', _ELEMENT),
    (_ROW, _ROW + f'    ForwardEntry(0, 3, "read", _read_episodes_before),\n', _ELEMENT),
    (_ROW, _ROW + f'    ForwardEntry(0, 3, "read", _read_episodes_before, [_check_chains]),\n', _ELEMENT),
    (_ROW, _ROW + f'    ForwardEntry(0, 3, "read", _read_episodes_before, (lambda: {_U},)),\n', _ELEMENT),
    (_ROW, _ROW + f'    ForwardEntry(0, 3, "read", _read_episodes_before, (_check_chains(),)),\n', _ELEMENT),
    (_ROW, _ROW + f'    *[ForwardEntry(0, 3, "alter", {_U}, ())],\n', _ELEMENT),
    ('    return [ForwardEntry(lo, v, "alter", s) for s in statements]\n',
     f'    return [ForwardEntry(lo, v, "alter", {_U}) for s in statements]\n', "it makes the table's entries"),
    ('            + [ForwardEntry(0, target, "stamp", target),', f'            + [ForwardEntry(0, target, "alter", {_U}), ForwardEntry(0, target, "stamp", target),',
     "it makes the table's entries"),
    ("def _alters(lo, v, statements):\n", f'_MORE = ForwardEntry(0, 3, "alter", {_U})\n\n\ndef _alters(lo, v, statements):\n', "outside the table and the functions"),
], ids=["a literal through _alters", "an alter by hand", "keywords", "add in the table", "stamp in the table", "an unknown kind", "a lambda", "four fields",
        "a list of fields", "a lambda in the fields", "a call in the fields",
        "a starred list", "_alters's body", "plan's body", "an entry made beside the table"])
def test_an_entry_comes_only_from_the_table_s_grammar(old, new, why):
    assert not any(why in b for b in _gate(SQLITE.read_text(), _r5_others(_MIG, old, old)))
    bad = _gate(SQLITE.read_text(), _r5_others(_MIG, old, new))
    assert any(why in b for b in bad), bad


@pytest.mark.parametrize("new", [f"ALTERS_X: tuple = ({_U},)\n", f"ALTERS_V5_TO_V6 += ({_U},)\n", f"ALTERS_X = [{_U}]\n",
                                 f"def f():\n    ALTERS_X = ({_U},)\n", f"for ALTERS_X in (({_U},),):\n    pass\n", "ALTERS_V5_TO_V6 = ()\n",
                                 "from .schema import Episode as ALTERS_X\n"],
                         ids=["annotated", "augmented", "a list", "in a function", "a for target", "bound twice", "an import"])
def test_an_alters_name_is_bound_only_as_a_plain_tuple(new):
    """Research's read of cad9e795: `ALTERS_X: tuple = (…)` and `ALTERS_X += (…)` passed a rule that read `ast.Assign`."""
    text = (SRC / _SV).read_text()
    assert not any("ALTERS_" in b for b in _gate(SQLITE.read_text(), _r5_others(_SV, _ALTERS_AT, _ALTERS_AT)))
    bad = _gate(SQLITE.read_text(), {**_r5_others(_SV, _ALTERS_AT, _ALTERS_AT), _SV: text + "\n" + new})
    assert any("ALTERS_" in b for b in bad), bad


def test_sa10_still_refuses_a_ladder_statement_by_execution(tmp_path, monkeypatch):
    """The second layer, kept: an `alter` entry that reached the table anyway is refused by SA10 on every base that runs it, and
    v1, which never runs it, is clean. The table is frozen at import, so the plant goes into the table."""
    name = "veracium_sa10_gate"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / "specs/evidence/0013/sa10_gate.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    g = sys.modules[name]
    import veracium.store.migration as mig
    at = next(i for i, e in enumerate(mig.FORWARD_ENTRIES) if e.kind == "alter" and e.lo == 2)
    plant = mig.ForwardEntry(2, 16, "alter", "UPDATE edges SET json=replace(json, '0.8', '1.8')")
    monkeypatch.setattr(mig, "FORWARD_ENTRIES", mig.FORWARD_ENTRIES[:at] + (plant,) + mig.FORWARD_ENTRIES[at:])
    builders = {lab: b for lab, e, b in g.gate_paths() if e == "migrate_store"}
    for label in ("v2#0", "v15#0"):        # the table's two ends: the ladder runs it from every base from v2
        r = g.run_path(label, "migrate_store", builders[label], str(tmp_path / label))
        assert any("a row write on ['edges'] maps to 0 steps" in p for p in r["problems"]), (label, r["problems"])
    assert g.run_path("v1#0", "migrate_store", builders["v1#0"], str(tmp_path / "v1"))["problems"] == []   # never runs it


def _scratch_state():
    """The classifier's whole scratch database: its schema, every table's rows, and SQLite's change counter."""
    c = _classifier_conn()
    schema = c.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name").fetchall()
    rows = {t: c.execute(f'SELECT * FROM "{t}"').fetchall() for k, t, _n, _s in schema if k == "table"}
    return schema, rows, c.total_changes


def test_a_statement_that_binds_exactly_is_compiled_and_not_run():
    """R5-02's case: exactly `_OVERBIND` numbered parameters, which bind on any runtime whose limit allows them (the
    qualified one's is 250000). Where they bind the statement counts as prepared, with that count; where they cannot it is
    UNRESOLVED. Either way nothing ran: no table, no row, no change."""
    limit = _classifier_conn().getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER)
    sql = f"CREATE TABLE reviewer_classifier_probe AS SELECT ?{_OVERBIND} AS value"
    _CLASSIFIED.pop(sql, None)
    before = _scratch_state()
    tags = _sqlite_classify(sql)
    assert _scratch_state() == before
    if limit >= _OVERBIND:
        assert tags == set() and _param_count(sql) == _OVERBIND, tags
    else:
        assert tags == {UNRESOLVED}, tags
    assert UNRESOLVED in _sqlite_classify("SELECT value FROM reviewer_classifier_probe")


def test_classifying_every_sql_literal_in_src_leaves_the_scratch_unchanged():
    """The same invariance over the pin: every literal at an execute-family call in src/, read fresh."""
    lits = {n.args[0].value for p in sorted(SRC.rglob("*.py")) for n in ast.walk(ast.parse(p.read_text()))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in SQL_CALLS and n.args
            and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)} | set(CLOSED_SQL)
    assert len(lits) > 100, len(lits)
    before = _scratch_state()
    for sql in sorted(lits):
        _CLASSIFIED.pop(sql, None)
        _sqlite_classify(sql)
        assert _scratch_state() == before, sql


@pytest.mark.parametrize("sql", ["QUERY PLAN SELECT 1", "QUERY PLAN DELETE FROM edges", "-- c\nQUERY PLAN DELETE FROM edges"])
def test_a_string_sqlite_refuses_bare_stays_unresolved(sql):
    """Research's B2: the prefix must not make a new statement grammatical (R4-01 (c))."""
    _CLASSIFIED.pop(sql, None)
    assert _sqlite_classify(sql) == {UNRESOLVED}


def test_the_superseded_preparations_are_what_these_cells_catch(monkeypatch):
    """The two superseded forms, run: with no prefix the exact-count statement EXECUTES in the scratch (R5-02), and with
    plain `EXPLAIN ` a `QUERY PLAN` string prepares (B2). So the cells above can fail, and the prefix is what passes them."""
    env = _sqlite_classify.__globals__
    limit = sqlite3.connect(":memory:").getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER)
    assert limit >= _OVERBIND, limit       # the demonstration needs a runtime that binds them; the qualified one does
    for prefix, sql, check in (
            ("", f"CREATE TABLE reviewer_classifier_probe AS SELECT ?{_OVERBIND} AS value",
             lambda: _classifier_conn().execute("SELECT count(*) FROM reviewer_classifier_probe").fetchone() == (1,)),
            ("EXPLAIN ", "QUERY PLAN SELECT 1", lambda: _sqlite_classify("QUERY PLAN SELECT 1") == set())):
        with monkeypatch.context() as m:
            m.setitem(env, "_PREPARE", prefix)
            m.setitem(env, "_CLASSIFIER", [])
            m.setitem(env, "_CLASSIFIED", {})
            _sqlite_classify(sql)
            assert check(), prefix
            _classifier_conn().close()


def test_the_database_names_cover_this_runtime_and_the_named_exception_is_needed():
    """W1: the frozen names are a superset of this runtime's minus nothing it lacks by age; every refused name is
    absent from src/ but for the one named exception, which is live; and the bare-parameter derivation finds `_rows`
    alone (W3)."""
    here = {n for c in (sqlite3.Connection, sqlite3.Cursor) for n in dir(c) if not n.startswith("__")}
    assert here <= DB_NAMES | here and "blobopen" in DB_NAMES - DB_ADMITTED and DB_ADMITTED <= DB_NAMES
    uses = [(str(p.relative_to(SRC)), n.value.id if isinstance(n.value, ast.Name) else None, n.attr)
            for p in sorted(SRC.rglob("*.py")) for n in ast.walk(ast.parse(p.read_text()))
            if isinstance(n, ast.Attribute) and n.attr in (DB_NAMES | here) - DB_ADMITTED]
    assert set(uses) == {(rel, recv, attr) for rel, _f, recv, attr in DB_NAME_EXCEPTIONS}, uses
    src = SQLITE.read_text()
    others = {str(p.relative_to(SRC)): p.read_text() for p in sorted(SRC.rglob("*.py")) if p.resolve() != SQLITE.resolve()}
    mods = [(r, x, *_parsed(x)) for r, x in [("veracium/store/sqlite.py", src)] + sorted(others.items())]
    assert _bare_parameter_sites(mods) == {"_rows": (1, "sql")}


def test_the_tripwire_holds_a_write_to_the_frame_that_ran_it(tmp_path, monkeypatch, _edges_write_tripwire):
    """Research's fix 3: a callee the write method reaches runs UNDER it. A write from next_seq, inside the journal
    writer inside `_write_edge_row`, is denied: the frame that called execute is not the write method. Before, any
    frame on the stack sufficed, the write passed, and 1.8 persisted."""
    s = SqliteStore(str(tmp_path / "frame.db"))
    real = SQ.next_seq

    def planted(conn, user_id):
        conn.execute("UPDATE edges SET json=json WHERE user_id=?", (user_id,))
        return real(conn, user_id)
    monkeypatch.setattr(SQ, "next_seq", planted)
    with pytest.raises(sqlite3.DatabaseError):
        s.add_edge(_edge("f", S.Volatility.SLOW, 0.8))
    assert len(_edges_write_tripwire) == 1 and s.edges(U, active_only=False) == []
    _edges_write_tripwire.clear()


def test_the_schema_route_reading_of_honest_and_shadow_statements():
    """R-01's tag, by SQLite's reading: an honest CREATE (which itself writes sqlite_master), a read of main and a pin
    PRAGMA are not routes; ALTER outside main reports its database in a1, not db, and is one. Every literal SQL argument
    in src/ reads clean (the gate's honest pass, above)."""
    for ok_sql in ("CREATE TABLE side(x)", "SELECT id FROM main.edges", "PRAGMA user_version"):
        assert "schema-route" not in _sqlite_classify(ok_sql), ok_sql
    for sql in _SHADOW.values():
        assert "schema-route" in _sqlite_classify(sql), sql
    assert _schema_route(sqlite3.SQLITE_ALTER_TABLE, "temp", "x", None)
    assert not _schema_route(sqlite3.SQLITE_ALTER_TABLE, "main", "x", None)


def test_a_pragma_read_at_prepare_does_not_change_the_next_reading():
    """A flag PRAGMA takes effect at prepare, though nothing runs. Classifying one must not change how a later
    statement reads, so this holds in either order: unlike the rest of the classifier's inputs, each statement here is
    read fresh, and a direct schema-table write stays unreadable after writable_schema was classified. The scratch
    connection keeps no flag."""
    direct = "UPDATE sqlite_schema SET sql=sql WHERE name='e'"
    for sql in (direct, "PRAGMA writable_schema=ON", "PRAGMA writable_schema=1"):
        _CLASSIFIED.pop(sql, None)
    assert UNRESOLVED in _sqlite_classify(direct)
    _CLASSIFIED.pop(direct)
    assert "schema-route" in _sqlite_classify("PRAGMA writable_schema=ON")
    assert UNRESOLVED in _sqlite_classify(direct)
    assert _classifier_conn().execute("PRAGMA writable_schema").fetchone() == (0,)
    assert "schema-route" in _sqlite_classify("PRAGMA WRITABLE_SCHEMA=1") and "schema-route" not in _sqlite_classify("PRAGMA USER_VERSION")


def test_the_tripwire_denies_a_table_shadowing_the_store(tmp_path, _edges_write_tripwire):
    """R-01 at run time: the shadow was invisible to the authorizer and to the teardown invariant, which opens the file
    while a TEMP table is the connection's own; it read 0.9 over a stored 0.8. Now the CREATE is denied, and the store
    reads what it holds."""
    s = SqliteStore(str(tmp_path / "shadow.db"))
    s.add_edge(_edge("h", S.Volatility.SLOW, 0.8))
    with pytest.raises(sqlite3.DatabaseError):
        s._conn.execute("CREATE TEMP TABLE IF NOT EXISTS edges AS SELECT id, user_id, subject, relation, object, active, "
                        "quarantined, replace(json, '0.8', '0.9') AS json FROM main.edges")
    assert len(_edges_write_tripwire) >= 1 and _row(s, "h").provenance.confidence == 0.8
    _edges_write_tripwire.clear()


def test_the_census_n4f_depends_on_holds_over_src():
    """Research's recheck: N4f leaves a NON-literal getattr, vars(), eval, exec and the dunder routes to 0031's
    connect_census, so that dependence is asserted here too, not only in 0031's own cell: no module of src/ carries a
    refused form, and a planted one is refused."""
    spec = importlib.util.spec_from_file_location("connection_census_48", ROOT / "specs/evidence/0031/connection_census.py")
    census = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(census)
    refused = [(str(p), k) for p in sorted(SRC.rglob("*.py")) for k in census.connect_census(p.read_text(), str(p.relative_to(SRC)))
               if "[REFUSED" in k]
    assert refused == [], refused
    for plant in ("def f(c, n):\n    return getattr(c, n)\n", "def f(c):\n    return vars(type(c))\n",
                  "def f(c):\n    return c.__getattribute__('execute')\n", "eval('1')\n",
                  # stage 2: the frames need no rule of N4f's, because this holds them
                  "def f():\n    return (x for x in ()).gi_frame.f_builtins\n",
                  "def f(e):\n    return e.__traceback__.tb_frame.f_builtins\n",
                  "import sys\ndef f():\n    return sys.exc_info()[2].tb_frame.f_builtins\n",
                  "import sys\ndef f():\n    return sys._getframe().f_builtins\n"):
        assert any("[REFUSED" in k for k in census.connect_census(plant, "x.py")), plant


def test_the_round_5_mutants_leave_the_write_method_unchanged():
    """The reviewer's condition on the witnesses: every R5 mutant leaves the write method's frozen body as it is."""
    for name, (old, new, _r) in R5_MUTANTS.items():
        tree = ast.parse(_r5_planted(old, new))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SqliteStore")
        m = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == METHOD)
        assert _digest(m) == FROZEN[METHOD], name


@pytest.mark.parametrize("name", list(R5_CONTROLS))
def test_the_gate_passes_each_harmless_round_5_control(name):
    """The other half of each rule: a harmless edit of the same kinds passes (a gate refusing everything is no gate)."""
    old, new = R5_CONTROLS[name]
    assert _gate(_r5_planted(old, new)) == []


def test_a_parameter_reaching_a_write_refuses_by_the_head_rule(monkeypatch):
    """R4-01 (d)'s head rule ALONE: a listed site whose value a parameter reaches becomes a DELETE; its new entry and
    binding are admitted (as a re-review would), so the only remaining problem is the head rule's."""
    old = 'f"SELECT json FROM {table} WHERE id=? AND user_id=?"'
    new = 'f"DELETE FROM {table} WHERE id=? AND user_id=?"'
    planted = _r5_planted(old, new)
    tree = ast.parse(planted)
    parent = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
    expr = next(n for n in ast.walk(tree) if isinstance(n, ast.JoinedStr) and ast.unparse(n).startswith("f'DELETE FROM {table}"))
    call = parent[expr]
    fnode = _scope_of(call, parent)
    key = (f"SqliteStore.{fnode.name}", _digest(expr))
    oldkey = next(k for k, v in NONLITERAL.items() if k[0] == key[0] and "SELECT json FROM {table}" in v[1])
    monkeypatch.delitem(NONLITERAL, oldkey)
    monkeypatch.delitem(NONLITERAL_BINDING, oldkey)
    monkeypatch.setitem(NONLITERAL, key, (1, new))
    monkeypatch.setitem(NONLITERAL_BINDING, key, _binding_digest(tree, parent, fnode, expr))
    bad = _gate(planted)
    assert len(bad) == 1 and "reaches SQL whose leading constant does not fix a SELECT" in bad[0], bad
    assert _sql_binding(tree, parent, fnode, expr)[0] == ["kind"]


def test_the_classifier_prepares_and_never_runs():
    """R4-01 (c): the classifier's one expected outcome is CPython's binding-count refusal, raised after the prepare and
    before any step; its text is pinned here, with N a number. A missing function, collation or table, a syntax error
    and two statements are UNRESOLVED; a 0-parameter COMMIT or BEGIN prepares and does nothing; and every literal SQL
    argument in the pin's sqlite.py prepares (0 UNRESOLVED)."""
    c = sqlite3.connect(":memory:", isolation_level=None)
    with pytest.raises(sqlite3.ProgrammingError) as ex:
        c.execute("SELECT ?, ?", (None,) * _OVERBIND)
    assert str(ex.value) == ("Incorrect number of bindings supplied. The current statement uses 2, and there are "
                             "32767 supplied.")
    for bad_sql in ("UPDATE edges SET json=reviewer_json(json) WHERE id=?", "SELECT json FROM edges ORDER BY json "
                    "COLLATE nope", "SELECT j FROM scratch", "UPDATE edges SET json=? WHERE", "SELECT 1; SELECT 2"):
        assert UNRESOLVED in _sqlite_classify(bad_sql), bad_sql
    conn = _classifier_conn()
    for ok_sql in ("COMMIT", "BEGIN IMMEDIATE", "ROLLBACK", "SELECT 1"):
        assert _sqlite_classify(ok_sql) == set() and _param_count(ok_sql) == 0, ok_sql
    assert not conn.in_transaction and conn.execute("SELECT COUNT(*) FROM edges").fetchone() == (0,)
    tree = ast.parse(SQLITE.read_text())
    lits = [n.args[0].value for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr in SQL_CALLS and n.args and isinstance(n.args[0], ast.Constant)
            and isinstance(n.args[0].value, str)]
    assert len(lits) > 100 and [s for s in lits if UNRESOLVED in _sqlite_classify(s)] == [], len(lits)


def test_the_layout_is_derived_by_execution_and_frozen_in_the_store():
    """R4-01 (a), research's B4: each closed statement's json position comes from EXECUTING it (INSERT 8/7, each UPDATE
    at 0 — the call sites' before-lengths), the moved-json control derives 1, and sqlite.py's _JSON_LAYOUT is exactly
    that, by digest, as an immutable tuple."""
    got = {(s, n, j) for s, n, j in _derived_layout()}
    assert {(n, j) for _s, n, j in got} == {(8, 7), (2, 0), (6, 0)} and len(got) == len(CLOSED_SQL) == 5
    assert _derive_one("UPDATE edges SET subject=?, json=? WHERE id=?") == (3, 1)
    assert isinstance(SQ._JSON_LAYOUT, tuple) and all(isinstance(r, tuple) for r in SQ._JSON_LAYOUT)
    assert set(SQ._JSON_LAYOUT) == _derived_layout_by_digest() and len(SQ._JSON_LAYOUT) == 5


def test_the_write_method_refuses_a_wrong_layout_before_any_sql(tmp_path):
    """R4-01 (a)'s second layer, at run time: the reviewer's re-layout reaching the UNCHANGED method's caller shape —
    the captured json bound one slot early — refuses with ValueError before any statement runs; the store is
    byte-identical. The honest layout writes."""
    db = tmp_path / "layout.db"
    s = SqliteStore(str(db))
    e = _edge("e", S.Volatility.SLOW, 0.8)
    s.add_edge(e)
    before = _snapshot(db)
    ins = next(x for x in CLOSED_SQL if x.startswith("INSERT"))
    with pytest.raises(ValueError, match="binding layout"):
        with s._write_txn():
            s._write_edge_row(ins, (e.id, e.user_id, e.subject, e.relation, e.object, int(e.active)), e,
                              (e.model_dump_json().replace("0.8", "1.8"),), user_id=e.user_id, edge_id=e.id, prior=None)
    assert _snapshot(db) == before
    with pytest.raises(ValueError, match="binding layout"):
        with s._write_txn():
            s._write_edge_row("UPDATE edges SET json=? WHERE id=?", (), e, (), user_id=e.user_id, edge_id=e.id, prior=None)
    assert _snapshot(db) == before and _row(s, "e").provenance.confidence == 0.8


def test_the_connection_inventorys_callees_hold():
    """R4-01 (b), research's B2: the inventory's reasons are claims about other code, checked — each callee resolves to
    the function its entry names, and that function's body holds no statement SQLite reads as an edges json write;
    open_versioned is the one stated MIGRATION SCOPE entry (its ladder is 0013's audited path). The pin passes the
    connection eight times."""
    assert sum(c for c, _t, _r in INVENTORY.values()) == 8
    for (where, form), (_count, target, reason) in INVENTORY.items():
        mod, fname = target.split(":")
        path = SRC / "veracium" / "store" / (mod.lstrip(".") + ".py")
        fn = next(n for n in ast.walk(ast.parse(path.read_text()))
                  if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == fname)
        writes = [n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                  and _sqlite_classify(n.value) & {"edges-insert", "edges-json-update"}]
        if fname == "open_versioned":
            assert "MIGRATION SCOPE" in reason and writes == [], (target, writes)
        else:
            assert writes == [] and ("no edges write" in reason or "never to edges" in reason), (target, writes, reason)


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


def _sql_caller():
    """The code object of the frame that CALLED execute (research's stage 2, S2-01): the first frame outside this file.
    The authorizer runs at prepare, inside the C call, so that frame is the statement's author. A write method on the
    stack proves nothing: a callee it reaches (next_seq, under the journal writer) runs under it."""
    f = sys._getframe(1)
    while f is not None and f.f_code.co_filename == __file__:
        f = f.f_back
    return f.f_code if f is not None else None


_TAKEN = {}                                                 # the guarded code objects, taken ONCE (research's S2-02)


def _outside_the_write_method(action, a1, a2):
    if not ((action == sqlite3.SQLITE_INSERT and a1 == "edges")
            or (action == sqlite3.SQLITE_UPDATE and a1 == "edges" and a2 == "json")):
        return False
    return _sql_caller() is not _TAKEN["write"]            # BY CODE IDENTITY, taken at setup, never by name


def _journal_forged(action, a1):
    """An edge_event INSERT prepared from neither the journal writer nor the v13 baseline journal (the only two
    callers of append_event in src/): a forged journal would let a write pass the row-equals-journal invariant."""
    return action == sqlite3.SQLITE_INSERT and a1 == "edge_event" and not (
        _sql_caller() is _TAKEN["append"] and _in_frames({_TAKEN["journal"], _TAKEN["baselines"]}))


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
    # BY CONTENT (research's stage 2, S2-04): a filename and a first line are metadata a replacement can copy onto its
    # own code (`f.__code__ = _w.__code__.replace(co_filename=…, co_firstlineno=…)`). Each live code object must EQUAL
    # the one a fresh compile of the store module's source gives under the same qualname — CPython's code equality
    # compares the bytecode, the constants, the names and the line table.
    fresh = {}
    stack = [compile(SQLITE.read_text(), SQ.__file__, "exec")]
    while stack:
        c = stack.pop()
        fresh.setdefault(c.co_qualname, c)
        stack.extend(k for k in c.co_consts if hasattr(k, "co_qualname"))
    for name in sorted(want):
        code = getattr(have.get(name), "__code__", None)
        if code is not None and code != fresh.get(code.co_qualname):
            probs.append(f"{name}: its code is not the store module's source, compiled ({code.co_qualname})")
    # WHAT THIS BINDS, AND THE RESIDUAL (research): the guarded objects' code equals their source. It does not bind
    # what that code references at run time — the module's `json` or `Edge`, the connection object — which in-process
    # code can still rebind; identity inside one interpreter is not a closable domain (the 0007 lesson). The row
    # invariants are the route-independent layer; in-bound, journaled, wrong bytes would need a behavioural oracle.
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
                  append=SQ.append_event.__code__,
                  baselines=_ee.journal_baselines.__code__)
    hits, paths = [], []
    real_init = SqliteStore.__init__

    def init(self, *a, **k):
        real_init(self, *a, **k)
        paths.append(self._path)

        def auth(action, a1, a2, db, trigger):
            edges_write = ((action == sqlite3.SQLITE_INSERT and a1 == "edges")
                           or (action == sqlite3.SQLITE_UPDATE and a1 == "edges" and a2 == "json"))
            if (action in _TRIGGER_OR_VIEW or _schema_route(action, a1, a2, db) or (trigger is not None and edges_write)
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


def test_the_identity_check_compares_code_by_content():
    """Research's stage 2, S2-04: a replacement that keeps the real function object and swaps its __code__ for one
    carrying the original's filename, first line, name and qualname passes a metadata check; the content check — each
    live code object equal to a fresh compile of the store module's source — names it."""
    real = SqliteStore.__dict__[METHOD]

    def _w(self, sql, before, edge, after, *, user_id, edge_id, prior, kind=None, reason=None, defer=False):
        return None
    forged = _w.__code__.replace(co_filename=real.__code__.co_filename, co_firstlineno=real.__code__.co_firstlineno,
                                 co_name=real.__code__.co_name, co_qualname=real.__code__.co_qualname)
    assert _guarded_identity_problems() == []
    saved = real.__code__
    try:
        real.__code__ = forged
        probs = _guarded_identity_problems()
    finally:
        real.__code__ = saved
    assert probs and all("compiled" in x for x in probs) and any(METHOD in x for x in probs), probs
    assert _guarded_identity_problems() == []
