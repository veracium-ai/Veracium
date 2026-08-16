"""specs/0012 (accepted v17) — Design 1, the core invariants I1–I6.

Reinforcement transfers NOTHING: the incoming same-value restatement is persisted with its
own provenance and the prior is left byte-identical. I7 (the persisted edge IS the M9
attribution) lives in tests/test_0014_maintenance_attribution.py, whose two 0012-attributed
xfail markers come off in the same commit as this file. The I8/I9/I10 families land in their
own slices and gate release per §12.
"""
from datetime import datetime, timedelta, timezone

import pytest

from veracium.config import MemoryConfig
from veracium.graph import apply_supersession
from veracium.lifecycle import expire
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge, EvidenceAuthor, Provenance, Volatility)
from veracium.store.sqlite import SqliteStore

U = "u1"
NOW = datetime.now(timezone.utc)


def _edge(eid, author, disc, days_ago, *, obj="chef", rel="works_as", conf=0.7,
          vol=Volatility.SLOW, source_id=None, flag=False):
    t = NOW - timedelta(days=days_ago)
    return Edge(id=eid, user_id=U, subject="user", relation=rel, object=obj,
                volatility=vol, valid_from=t, needs_confirmation=flag,
                provenance=Provenance(author_of_evidence=author, evidence_ref=f"ev-{eid}",
                                      disclosure=disc, confidence=conf, observed_at=t,
                                      source_id=source_id))


def _store_with_prior(**kw):
    s = SqliteStore(":memory:")
    prior = _edge("e-prior", EvidenceAuthor.USER, Disclosure.MENTIONABLE, 200, **kw)
    s.add_edge(prior)
    return s, prior


def _by_id(store, eid):
    return [e for e in store.edges(U, active_only=True, include_quarantined=True)
            if e.id == eid][0]


# --- I1: the incoming edge is persisted byte-unchanged --------------------------------
def test_reinforcement_persists_the_incoming_edge_unmodified():
    s, _ = _store_with_prior()
    inc = _edge("e-inc", EvidenceAuthor.SYSTEM, Disclosure.MENTIONABLE, 1,
                conf=0.4, source_id="pipeline:daily")
    submitted = inc.model_dump()
    apply_supersession(s, inc, DEFAULT_RELATIONS)
    stored = _by_id(s, "e-inc")
    assert stored.model_dump() == submitted        # its own author, dates, confidence,
    assert stored.provenance.source_id == "pipeline:daily"   # source_id — all its own (I1)


# --- I2: the prior is byte-identical after a reinforcement ----------------------------
def test_reinforcement_leaves_the_prior_byte_identical():
    s, prior = _store_with_prior()
    before = _by_id(s, "e-prior").model_dump()
    apply_supersession(s, _edge("e-inc", EvidenceAuthor.SYSTEM, Disclosure.MENTIONABLE, 1,
                                conf=0.99), DEFAULT_RELATIONS)
    after = _by_id(s, "e-prior").model_dump()
    assert after == before                          # no observed_at/confidence/valid_from/
    assert after["provenance"]["confidence"] == 0.7  # note/flag movement whatsoever (I2)


# --- I3 (frozen): per-edge ageing — the fresh duplicate does not shield the stale one -
def test_a_stale_user_edge_flags_despite_a_fresher_same_value_edge():
    s, _ = _store_with_prior()                      # 200d SLOW user edge (lifetime 120)
    apply_supersession(s, _edge("e-inc", EvidenceAuthor.SYSTEM, Disclosure.MENTIONABLE, 1),
                       DEFAULT_RELATIONS)
    r = expire(s, U, MemoryConfig(db_path=":memory:"), now=NOW)
    assert r["flagged_for_confirmation"] == 1
    assert _by_id(s, "e-prior").needs_confirmation is True   # the stale edge flags (I3)
    assert _by_id(s, "e-inc").needs_confirmation is False    # the fresh one, on its own age


# --- I4: reinforcement never clears needs_confirmation (0008 preserved) ---------------
def test_reinforcement_never_clears_the_flag():
    s, _ = _store_with_prior(flag=True)             # already flagged
    apply_supersession(s, _edge("e-inc", EvidenceAuthor.USER, Disclosure.MENTIONABLE, 0),
                       DEFAULT_RELATIONS)
    assert _by_id(s, "e-prior").needs_confirmation is True   # only confirm() clears (I4)


# --- I5: the measured §1 bypass is closed at its reachable doors ----------------------
def test_restatements_no_longer_defeat_staleness():
    # door (a): SYSTEM/mentionable — the §1 sequence, four restatements over 200 days
    s, _ = _store_with_prior()
    for i, days in enumerate((150, 100, 50, 1)):
        apply_supersession(s, _edge(f"e-sys{i}", EvidenceAuthor.SYSTEM,
                                    Disclosure.MENTIONABLE, days, conf=0.95),
                           DEFAULT_RELATIONS)
    prior = _by_id(s, "e-prior")
    assert prior.provenance.confidence == 0.7       # the confidence door is closed
    expire(s, U, MemoryConfig(db_path=":memory:"), now=NOW)
    assert _by_id(s, "e-prior").needs_confirmation is True   # the flag fires (was False)

    # door (b): third_party -> third_party within use_only
    s2 = SqliteStore(":memory:")
    tp = _edge("e-tp", EvidenceAuthor.THIRD_PARTY, Disclosure.USE_ONLY, 200, conf=0.5)
    s2.add_edge(tp)
    apply_supersession(s2, _edge("e-tp2", EvidenceAuthor.THIRD_PARTY,
                                 Disclosure.USE_ONLY, 1, conf=0.9), DEFAULT_RELATIONS)
    old = _by_id(s2, "e-tp")
    assert old.provenance.confidence == 0.5 and \
        (NOW - old.provenance.observed_at).days == 200       # keeps ITSELF fresh no longer


def test_cross_class_restatement_still_touches_nothing():
    # the 0.4.1 cross-class guard held BEFORE Design 1 and must hold after (I5 pin)
    s, _ = _store_with_prior()
    before = _by_id(s, "e-prior").model_dump()
    for i in range(4):
        apply_supersession(s, _edge(f"e-tp{i}", EvidenceAuthor.THIRD_PARTY,
                                    Disclosure.USE_ONLY, 1, conf=0.99), DEFAULT_RELATIONS)
    assert _by_id(s, "e-prior").model_dump() == before


# --- I6: a same-or-subsumed value never contends, absorbs, or supersedes --------------
def test_a_same_value_restatement_produces_no_contention_artifacts():
    # exact value on a FUNCTIONAL relation: no refusal, no invalidation, no supersedes
    s, _ = _store_with_prior()
    inc = _edge("e-inc", EvidenceAuthor.SYSTEM, Disclosure.MENTIONABLE, 1)
    apply_supersession(s, inc, DEFAULT_RELATIONS)
    assert s.supersessions_refused(U) == 0
    stored = _by_id(s, "e-inc")
    assert stored.supersedes is None
    prior = _by_id(s, "e-prior")
    assert prior.active and prior.invalidated_at is None and "absorbed" not in prior.note

    # the SUBSUMED form — the mis-routing seam §4a names: "Miso" after "cat Miso"
    s2 = SqliteStore(":memory:")
    full = _edge("e-full", EvidenceAuthor.USER, Disclosure.MENTIONABLE, 10,
                 obj="cat Miso", rel="has_pet", vol=Volatility.DURABLE)
    s2.add_edge(full)
    short = _edge("e-short", EvidenceAuthor.USER, Disclosure.MENTIONABLE, 1,
                  obj="Miso", rel="has_pet", vol=Volatility.DURABLE)
    apply_supersession(s2, short, DEFAULT_RELATIONS)
    act = {e.id for e in s2.edges(U, active_only=True)}
    assert act == {"e-full", "e-short"}             # both active — no absorption fired
    assert _by_id(s2, "e-full").invalidated_at is None
    assert _by_id(s2, "e-short").supersedes is None
    assert s2.supersessions_refused(U) == 0
