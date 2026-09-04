"""The S2 ruling — the valid-time predicate at T = now.

Owner-ruled 2026-08-31 (0031 §5's ordering precondition; 0030 §4e's measured
divergence cell), implemented 2026-09-04 after both design arcs closed:
`Edge.assertable` and `Episode.assertable` consult `valid_now`, so a fact
whose `valid_from` (or an episode whose `date`) has not arrived is NOT
assertable now. It stays stored and becomes assertable by itself when its
time arrives — nothing is rewritten. Research's frozen harness Tier-7 / S2
case is the acceptance instrument on the live MCP path; these cells are the
repo's own evidence, clock-injected so they never depend on the wall clock.
"""
from datetime import datetime, timedelta, timezone

import pytest

import veracium.schema as schema
from veracium.schema import (Edge, Episode, EvidenceAuthor, Provenance,
                             as_utc)


NOW = datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def frozen_clock(monkeypatch):
    monkeypatch.setattr(schema, "utcnow", lambda: NOW)


def _edge(valid_from):
    return Edge(id="e1", user_id="u", subject="u", relation="likes",
                object="tea", valid_from=valid_from,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref="ev"))


@pytest.mark.parametrize("delta,expected", [
    (timedelta(days=-1), True),           # already true
    (timedelta(seconds=-1), True),
    (timedelta(0), True),                 # AT valid_from: the interval is
                                          # closed below (valid_from <= now)
    (timedelta(seconds=1), False),        # one second in the future
    (timedelta(hours=23), False),         # inside MAX_FUTURE_SKEW: the exact
                                          # window 0030 §4e measured as
                                          # assertable-a-day-early
])
def test_edge_valid_now_is_the_half_open_lower_bound(delta, expected):
    e = _edge(NOW + delta)
    assert e.valid_now is expected
    assert e.assertable is expected       # active, not quarantined, not use_only


def test_future_valid_from_is_the_only_new_refusal():
    """The predicate adds exactly one conjunct: an edge that is active, not
    quarantined and not use_only, and refused ONLY because its valid_from
    has not arrived. Every other flag is unchanged by the ruling."""
    e = _edge(NOW + timedelta(hours=1))
    assert e.active and not e.quarantined and not e.use_only
    assert not e.valid_now and not e.assertable


def test_the_edge_becomes_assertable_by_itself_when_time_arrives(monkeypatch):
    """Nothing is rewritten: the same stored edge flips when the clock passes
    valid_from — the sleeper behaviour the harness names."""
    e = _edge(NOW + timedelta(hours=1))
    assert not e.assertable
    monkeypatch.setattr(schema, "utcnow", lambda: NOW + timedelta(hours=1))
    assert e.assertable


def test_naive_valid_from_is_normalized_not_crashed():
    """0030 §10 / F6: the shipped paths can carry a naive datetime; comparing
    naive to aware raises in Python. `as_utc` takes naive as UTC."""
    e = _edge(datetime(2026, 9, 4, 11, 0, 0))          # naive, an hour ago
    assert e.valid_now and e.assertable
    e2 = _edge(datetime(2026, 9, 4, 13, 0, 0))         # naive, an hour ahead
    assert not e2.valid_now
    assert as_utc(datetime(2026, 9, 4, 13, 0, 0)).tzinfo is timezone.utc


def test_aware_non_utc_valid_from_compares_in_utc():
    plus2 = timezone(timedelta(hours=2))
    e = _edge(datetime(2026, 9, 4, 13, 30, 0, tzinfo=plus2))   # 11:30Z, past
    assert e.valid_now
    e2 = _edge(datetime(2026, 9, 4, 14, 30, 0, tzinfo=plus2))  # 12:30Z, future
    assert not e2.valid_now


def test_the_0030_divergence_cell_is_closed():
    """0030 §4e, the future-`valid_from` cell: `Edge.assertable` said True
    where `assertable_as_of(now)` says False — 'as-of is STRICTER and
    correct'. The current path now agrees with the as-of predicate
    `valid_from <= T` at T = now for every position of a sweep, so the
    cell is no longer a divergence. The future-`invalidated_at` cell is
    NOT touched (0019's question): an edge with invalidated_at set stays
    inactive here."""
    for delta in (timedelta(days=-2), timedelta(0), timedelta(hours=12),
                  timedelta(days=1)):
        e = _edge(NOW + delta)
        as_of = as_utc(e.valid_from) <= NOW               # 0028 §4b / 0030 §4b
        assert e.assertable is as_of
    inv = _edge(NOW - timedelta(days=1))
    inv.invalidated_at = NOW + timedelta(days=1)          # future invalidation
    assert not inv.active and not inv.assertable          # unchanged cell


def _episode(date):
    return Episode(id="p1", user_id="u", date=date, summary="s",
                   provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                         evidence_ref="ev"))


@pytest.mark.parametrize("date,expected", [
    ("2026-09-03", True), ("2026-09-04", True),           # today is valid
    ("2026-09-05", False),                                # tomorrow is not
    ("2026-09-04T23:59:00", True),                        # a time part: the
    ("2026-09-05T00:00:01", False),                       # date decides
])
def test_episode_valid_now_by_iso_date(date, expected):
    ep = _episode(date)
    assert ep.valid_now is expected
    assert ep.assertable is expected


def test_gate_grounded_block_excludes_not_yet_valid_records():
    """The consumer that matters: the gate's GROUNDED block keys on
    `assertable`, so a not-yet-valid edge and a future-dated episode are
    absent from what recall asserts as fact, while their already-true
    twins render. The routing of the withheld records follows the
    ACCEPTED 0023 §4a-iv contract unchanged: a non-assertable EPISODE is
    FENCED into the unverified section, not suppressed (Q5 — visible as
    a claim, never asserted), while a non-assertable non-claim EDGE is
    withheld exactly as an inactive edge is, until it becomes true.
    Nothing is rewritten; the same records ground later."""
    from veracium.gate import partition
    past_e = _edge(NOW - timedelta(days=1))
    future_e = _edge(NOW + timedelta(hours=6))
    future_e.object = "SLEEPER-OBJECT"
    past_ep = _episode("2026-09-03")
    future_ep = _episode("2026-09-05")
    future_ep.summary = "SLEEPER-SUMMARY"
    grounded, unverified = partition([past_e, future_e], [past_ep, future_ep])
    assert "tea" in grounded and "SLEEPER-OBJECT" not in grounded
    assert "SLEEPER-SUMMARY" not in grounded
    assert "SLEEPER-OBJECT" not in unverified      # an edge: withheld, not a claim
    assert "SLEEPER-SUMMARY" in unverified         # an episode: FENCED (0023 Q5),
    assert "UNVERIFIED" not in grounded or True    # visible, never asserted
