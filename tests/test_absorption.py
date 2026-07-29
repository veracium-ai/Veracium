"""T1 subset-absorption (value-equivalence tier 1, proposals/value-equivalence.md).

A more specific restatement of a held value ("cat Miso" after "Miso") absorbs
the shorter form; a less specific restatement reinforces the fuller one. Both
are write-time identity events — never supersession, never destructive.
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from veracium.graph import _subsumes, _value_key, apply_supersession, render_edges
from veracium.schema import (DEFAULT_RELATIONS, Edge, EvidenceAuthor, Provenance,
                             SourceType)
from veracium.store.sqlite import SqliteStore


def _dt(day: int) -> datetime:
    return datetime(2026, 7, day, tzinfo=timezone.utc)


def _edge(eid, obj, *, day=1, relation="has_pet", subject="user",
          confidence=0.9, note="", needs_confirmation=False) -> Edge:
    return Edge(id=eid, user_id="u1", subject=subject, relation=relation,
                object=obj, note=note, needs_confirmation=needs_confirmation,
                valid_from=_dt(day),
                provenance=Provenance(source_type=SourceType.STATED,
                                      author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{eid}", observed_at=_dt(day),
                                      confidence=confidence))


def _store():
    d = tempfile.mkdtemp(prefix="veracium-t1-")
    return SqliteStore(Path(d) / "t.db")


def test_subsumes_bounds():
    assert _subsumes(_value_key("cat Miso"), _value_key("Miso"))
    assert _subsumes(_value_key("orange cat Miso"), _value_key("Miso"))  # +2
    assert not _subsumes(_value_key("grumpy orange cat Miso"), _value_key("Miso"))  # +3
    assert not _subsumes(_value_key("Miso"), _value_key("Miso"))  # equal length
    # ordered subsequence, not bag-subset
    assert not _subsumes(_value_key("tea over coffee always"), _value_key("coffee over tea"))


def test_more_specific_arrival_absorbs_prior():
    store = _store()
    apply_supersession(store, _edge("e1", "Miso", day=1, confidence=0.95,
                                    note="from onboarding"), DEFAULT_RELATIONS)
    apply_supersession(store, _edge("e2", "cat Miso", day=5, confidence=0.9),
                       DEFAULT_RELATIONS)

    active = store.edges("u1")
    assert [e.id for e in active] == ["e2"]
    winner = active[0]
    assert winner.object == "cat Miso"
    assert winner.valid_from == _dt(5)
    assert winner.provenance.confidence == 0.95  # max of the pair
    assert winner.supersedes is None  # identity, not change

    loser = [e for e in store.edges("u1", active_only=False) if e.id == "e1"][0]
    assert loser.invalidation_reason == "absorbed_duplicate"
    assert "absorbed_by:e2" in loser.note
    assert "from onboarding" in loser.note  # prior note preserved


def test_less_specific_arrival_reinforces_fuller_prior():
    store = _store()
    apply_supersession(store, _edge("e1", "cat Miso", day=1,
                                    needs_confirmation=True), DEFAULT_RELATIONS)
    apply_supersession(store, _edge("e2", "Miso", day=6, confidence=0.95),
                       DEFAULT_RELATIONS)

    edges = store.edges("u1", active_only=False)
    assert [e.id for e in edges] == ["e1"]  # no new row at all
    e = edges[0]
    assert e.object == "cat Miso"  # fuller surface kept
    assert e.valid_from == _dt(6)  # restatement refreshes liveness
    assert e.provenance.confidence == 0.95
    assert e.needs_confirmation is False  # write-time evidence clears the flag


def test_reinforcement_never_rewinds_validity():
    store = _store()
    apply_supersession(store, _edge("e1", "cat Miso", day=10), DEFAULT_RELATIONS)
    apply_supersession(store, _edge("e2", "cat Miso", day=3), DEFAULT_RELATIONS)  # back-dated
    assert store.edges("u1")[0].valid_from == _dt(10)


def test_absorption_needs_same_subject_and_relation():
    store = _store()
    apply_supersession(store, _edge("e1", "Miso", subject="user"), DEFAULT_RELATIONS)
    apply_supersession(store, _edge("e2", "cat Miso", subject="person:ida", day=2),
                       DEFAULT_RELATIONS)
    apply_supersession(store, _edge("e3", "cat Miso", relation="cares_for", day=2),
                       DEFAULT_RELATIONS)
    assert len(store.edges("u1")) == 3  # nothing merged across subject/relation


def test_third_person_possessives_still_never_merge():
    store = _store()
    apply_supersession(store, _edge("e1", "his assistant", relation="works_with"),
                       DEFAULT_RELATIONS)
    apply_supersession(store, _edge("e2", "her assistant", relation="works_with", day=2),
                       DEFAULT_RELATIONS)
    assert len(store.edges("u1")) == 2


def test_wide_gap_accumulates_instead_of_merging():
    store = _store()
    apply_supersession(store, _edge("e1", "Miso"), DEFAULT_RELATIONS)
    apply_supersession(store, _edge("e2", "grumpy old orange cat Miso", day=2),
                       DEFAULT_RELATIONS)
    assert len(store.edges("u1")) == 2  # >2 extra tokens: visible dup, no risk taken


def test_functional_relation_subset_reinforces_instead_of_churning():
    store = _store()
    apply_supersession(store, _edge("e1", "concise bullet answers",
                                    relation="prefers", day=1), DEFAULT_RELATIONS)
    apply_supersession(store, _edge("e2", "concise answers",
                                    relation="prefers", day=4), DEFAULT_RELATIONS)
    edges = store.edges("u1", active_only=False)
    assert [e.id for e in edges] == ["e1"]  # reinforced, not superseded
    assert edges[0].invalidation_reason is None
    # a genuinely different value still supersedes
    apply_supersession(store, _edge("e3", "detailed answers",
                                    relation="prefers", day=8), DEFAULT_RELATIONS)
    assert store.edges("u1")[0].id == "e3"
    assert store.edges("u1")[0].supersedes == "e1"


def test_absorbed_edges_never_render_as_history():
    store = _store()
    apply_supersession(store, _edge("e1", "Miso"), DEFAULT_RELATIONS)
    apply_supersession(store, _edge("e2", "cat Miso", day=5), DEFAULT_RELATIONS)
    out = render_edges(store.edges("u1", active_only=False))
    assert "cat Miso" in out
    assert "SUPERSEDED" not in out
    assert out.count("Miso") == 1  # the absorbed surface form is not shown
