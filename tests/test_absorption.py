"""T1 subset-absorption (value-equivalence tier 1, proposals/value-equivalence.md).

A more specific restatement of a held value ("cat Miso" after "Miso") absorbs
the shorter form; a less specific restatement reinforces the fuller one. Both
are write-time identity events — never supersession, never destructive.
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from veracium.graph import _subsumes, _value_key, apply_supersession, render_edges
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge, EvidenceAuthor,
                             Provenance, SourceType)
from veracium.store.sqlite import SqliteStore


def _dt(day: int) -> datetime:
    return datetime(2026, 7, day, tzinfo=timezone.utc)


def _edge(eid, obj, *, day=1, relation="has_pet", subject="user",
          confidence=0.9, note="", needs_confirmation=False,
          author=EvidenceAuthor.USER,
          disclosure=Disclosure.MENTIONABLE) -> Edge:
    return Edge(id=eid, user_id="u1", subject=subject, relation=relation,
                object=obj, note=note, needs_confirmation=needs_confirmation,
                valid_from=_dt(day),
                provenance=Provenance(source_type=SourceType.STATED,
                                      author_of_evidence=author,
                                      evidence_ref=f"ev-{eid}", observed_at=_dt(day),
                                      disclosure=disclosure,
                                      confidence=confidence))


def _tp_edge(eid, obj, **kw) -> Edge:
    """A third-party inference edge as ingest would build it: use_only."""
    return _edge(eid, obj, author=EvidenceAuthor.THIRD_PARTY,
                 disclosure=Disclosure.USE_ONLY, **kw)


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
    assert winner.valid_from == _dt(1)          # inherits EARLIEST first-known
    assert winner.provenance.observed_at == _dt(5)   # latest recording
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

    # specs/0012 Design 1 (accepted 2026-08-10): the less-specific restatement is the same
    # evidentiary event and takes the reinforcement branch — which now PERSISTS it with its
    # own provenance and touches nothing else. Both rows survive; nothing transfers.
    edges = {e.id: e for e in store.edges("u1", active_only=False)}
    assert set(edges) == {"e1", "e2"}
    e1 = edges["e1"]
    assert e1.object == "cat Miso"                 # fuller surface kept, byte-untouched
    assert e1.valid_from == _dt(1)                 # first-known is immutable
    assert e1.provenance.observed_at == _dt(1)     # 0012: liveness NO LONGER transfers
    assert e1.provenance.confidence != 0.95        # 0012: confidence NO LONGER transfers
    assert e1.needs_confirmation is True           # specs/0008: only confirm() clears
    assert e1.invalidated_at is None               # and no absorption fired (0012 I6)


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
    # specs/0012 Design 1: the subset restatement persists as its own edge; the NO-CHURN
    # intent this test protects is preserved — no supersession, no invalidation (0012 I6).
    edges = {e.id: e for e in store.edges("u1", active_only=False)}
    assert set(edges) == {"e1", "e2"}
    assert edges["e1"].invalidation_reason is None
    assert edges["e2"].supersedes is None
    # a genuinely different value still supersedes — BOTH same-value actives retire
    apply_supersession(store, _edge("e3", "detailed answers",
                                    relation="prefers", day=8), DEFAULT_RELATIONS)
    active = store.edges("u1")
    assert [e.id for e in active] == ["e3"]
    assert active[0].supersedes in {"e1", "e2"}
    all_edges = {e.id: e for e in store.edges("u1", active_only=False)}
    assert all_edges["e1"].invalidated_at is not None
    assert all_edges["e2"].invalidated_at is not None


def test_absorbed_edges_never_render_as_history():
    store = _store()
    apply_supersession(store, _edge("e1", "Miso"), DEFAULT_RELATIONS)
    apply_supersession(store, _edge("e2", "cat Miso", day=5), DEFAULT_RELATIONS)
    out = render_edges(store.edges("u1", active_only=False))
    assert "cat Miso" in out
    assert "SUPERSEDED" not in out
    assert out.count("Miso") == 1  # the absorbed surface form is not shown


# -- identity merges never cross trust classes (t1-review Findings 1 & 2) ----

def test_third_party_restatement_never_absorbs_user_fact():
    """Finding 1: a use_only subset restatement must not retire the user's
    assertable fact or inherit its confidence."""
    store = _store()
    apply_supersession(store, _edge("e-user", "Miso", day=1, confidence=0.95),
                       DEFAULT_RELATIONS)
    apply_supersession(store, _tp_edge("e-3p", "cat Miso", day=5, confidence=0.6),
                       DEFAULT_RELATIONS)
    edges = {e.id: e for e in store.edges("u1", active_only=False)}
    assert len(edges) == 2  # accumulated, not merged
    assert edges["e-user"].active and edges["e-user"].assertable
    assert edges["e-user"].invalidation_reason is None
    assert edges["e-3p"].active and edges["e-3p"].use_only
    assert edges["e-3p"].provenance.confidence == 0.6  # no confidence inheritance


def test_third_party_restatement_never_reinforces_user_edge():
    """Finding 2: a third-party exact restatement must not refresh liveness,
    clear the staleness flag, or raise confidence on a USER edge."""
    store = _store()
    apply_supersession(store, _edge("e-user", "cat Miso", day=1, confidence=0.7,
                                    needs_confirmation=True), DEFAULT_RELATIONS)
    apply_supersession(store, _tp_edge("e-3p", "cat Miso", day=9, confidence=0.99),
                       DEFAULT_RELATIONS)
    user = [e for e in store.edges("u1", active_only=False) if e.id == "e-user"][0]
    assert user.valid_from == _dt(1)          # liveness not refreshed
    assert user.needs_confirmation is True    # flag means: the USER should reconfirm
    assert user.provenance.confidence == 0.7  # no confidence injection
    assert len(store.edges("u1", active_only=False)) == 2  # 3p version accumulates


def test_user_restatement_does_not_upgrade_third_party_edge():
    """The upgrade path for corroborated third-party material is confirm(),
    never a silent merge: the user's own statement becomes a NEW assertable
    edge; the use_only edge is untouched."""
    store = _store()
    apply_supersession(store, _tp_edge("e-3p", "cat Miso", day=1, confidence=0.6),
                       DEFAULT_RELATIONS)
    apply_supersession(store, _edge("e-user", "cat Miso", day=3, confidence=0.9),
                       DEFAULT_RELATIONS)
    edges = {e.id: e for e in store.edges("u1", active_only=False)}
    assert len(edges) == 2
    assert edges["e-user"].active and edges["e-user"].assertable
    assert edges["e-3p"].active and edges["e-3p"].use_only
    assert edges["e-3p"].provenance.confidence == 0.6


def test_same_class_merges_still_work_within_use_only():
    """Same-class identity merges are unchanged: two use_only restatements of
    one fact absorb within their own trust class."""
    store = _store()
    apply_supersession(store, _tp_edge("e1", "Miso", day=1), DEFAULT_RELATIONS)
    apply_supersession(store, _tp_edge("e2", "cat Miso", day=4), DEFAULT_RELATIONS)
    active = store.edges("u1")
    assert [e.id for e in active] == ["e2"]
    loser = [e for e in store.edges("u1", active_only=False) if e.id == "e1"][0]
    assert loser.invalidation_reason == "absorbed_duplicate"


# -- retrieval ranking at scale (LongMemEval pilot finding) -------------------

def test_ranking_is_not_query_blind_in_a_large_store():
    """The pilot's real bug, and the one my first two fixes did NOT catch:
    every user-subject edge scored the same, so past max_subgraph_edges the
    truncation ignored the query entirely — recall returned the same 40 facts
    whatever you asked. Widening the cap only returned more of the same, which
    is exactly what the 40->200 ablation measured.

    The discriminating assertion is that DIFFERENT queries return DIFFERENT
    sets. Asserting only "the target is retrieved" passes on the broken code
    whenever the target happens to sit early in store order — which is how the
    first version of this test fooled me."""
    from veracium.graph import subgraph_for_query
    store = _store()
    for i in range(150):
        apply_supersession(store, _edge(f"noise{i}", f"unrelated detail {i}",
                                        relation="mentioned"), DEFAULT_RELATIONS)
    apply_supersession(store, _edge("pet", "cat named Miso", relation="has_pet"),
                       DEFAULT_RELATIONS)
    apply_supersession(store, _edge("job", "Brellin Optics", relation="works_for"),
                       DEFAULT_RELATIONS)
    for i in range(150):
        apply_supersession(store, _edge(f"more{i}", f"other detail {i}",
                                        relation="mentioned"), DEFAULT_RELATIONS)

    pet = [e.id for e in subgraph_for_query(store, "u1",
                                            "what pet does the user have?", max_edges=40)]
    job = [e.id for e in subgraph_for_query(store, "u1",
                                            "where does the user work?", max_edges=40)]
    assert pet != job, "retrieval must depend on the query, not store order"
    assert pet[0] == "pet" and job[0] == "job"


def test_owner_token_does_not_make_every_fact_look_relevant():
    """'user' appears in most questions AND is the subject of most edges, so
    counting it as a match re-collapses ranking — the failure mode that defeated
    my first fix."""
    from veracium.graph import _tokens
    assert "user" not in _tokens("what does the user prefer?")


def test_query_wording_reaches_relation_names():
    """'work' must reach works_for and 'pets' must reach has_pet: exact-token
    matching failed silently on ordinary morphology."""
    from veracium.graph import _tokens
    assert _tokens("work") & _tokens("works_for")
    assert _tokens("pets") & _tokens("has_pet")


def test_small_store_still_returns_everything_off_the_user_node():
    """Eligibility is unchanged: when the store fits under the cap, every
    user-subject edge is still returned regardless of query overlap."""
    from veracium.graph import subgraph_for_query
    store = _store()
    for i in range(5):
        apply_supersession(store, _edge(f"e{i}", f"fact {i}", day=1 + i,
                                        relation="mentioned"), DEFAULT_RELATIONS)
    got = subgraph_for_query(store, "u1", "something entirely unrelated",
                             max_edges=40)
    assert len(got) == 5


def test_relation_tokens_are_matchable():
    """'pet' should reach has_pet: the relation was never part of the matched
    text before, so a query naming the relation scored zero on it."""
    from veracium.graph import subgraph_for_query
    store = _store()
    apply_supersession(store, _edge("pet", "Miso", relation="has_pet"),
                       DEFAULT_RELATIONS)
    apply_supersession(store, _edge("job", "Brellin Optics", day=2,
                                    relation="works_for"), DEFAULT_RELATIONS)
    got = subgraph_for_query(store, "u1", "pet", max_edges=40)
    assert got[0].id == "pet"


def test_stemming_is_symmetric_and_conservative():
    """A stemmer that breaks matches is worse than none: a single pass mapped
    'addresses'->'address' but 'address'->'addres', so the forms stopped
    matching. Folding converges instead. 'es' is excluded because stripping it
    maps 'deadlines'->'deadlin' and loses the `deadline` relation."""
    from veracium.graph import _stem, _tokens
    assert _tokens("deadlines") & _tokens("deadline")
    assert _tokens("pets") & _tokens("has_pet")
    assert _tokens("prefers") & _tokens("prefer")
    # never strips below a 3-char stem, so short words are left alone
    for w in ("has", "bed", "used", "miso"):
        assert _stem(w) == w


# -- E1: time-coverage in subgraph selection ---------------------------------

def _dated(eid, obj, day, relation="mentioned"):
    return _edge(eid, obj, day=day, relation=relation)


def test_selection_spans_time_instead_of_collapsing_on_one_day():
    """Reproduces the LongMemEval failure: an interval question got 37 date
    mentions of which ONE was distinct.

    The fixture must make the same-period records score HIGHER, because that is
    what actually happens — a cluster of facts from one conversation shares the
    question's vocabulary, so relevance alone keeps them and the recency
    tiebreak never gets a say. (An earlier version of this test gave every
    record the same score, which the recency tiebreak alone already spreads
    across days — it passed without exercising coverage at all.)"""
    from veracium.graph import subgraph_for_query
    store = _store()
    for i in range(60):        # 2 query terms -> outrank everything below
        apply_supersession(store, _dated(f"d1-{i}", f"project alpha note {i}", 1),
                           DEFAULT_RELATIONS)
    for k, day in enumerate((5, 9, 14, 20)):   # 1 query term, later days
        apply_supersession(store, _dated(f"other-{k}", f"alpha update {k}", day),
                           DEFAULT_RELATIONS)

    off = subgraph_for_query(store, "u1", "project alpha", max_edges=40,
                             coverage_share=0.0)
    assert len({e.valid_from.date() for e in off}) == 1, \
        "pure top-k should collapse onto the dominant period"

    on = subgraph_for_query(store, "u1", "project alpha", max_edges=40)
    assert len(on) == 40
    assert len({e.valid_from.date() for e in on}) >= 3, "coverage did not reach other periods"
    # head stays pure relevance: the strongest matches are never displaced
    assert sum(1 for e in on if e.id.startswith("d1-")) >= 30


def test_coverage_never_shrinks_the_budget():
    """Coverage spends the reserved tail; it must not cost volume. With no other
    period to reach, the tail backfills by relevance."""
    from veracium.graph import subgraph_for_query
    store = _store()
    for i in range(100):
        apply_supersession(store, _dated(f"same-{i}", f"alpha note {i}", 3),
                           DEFAULT_RELATIONS)
    assert len(subgraph_for_query(store, "u1", "alpha", max_edges=40)) == 40


def test_small_store_selection_is_unchanged_by_coverage():
    """Below the budget nothing is chosen between, so behaviour is identical to
    pure ranking — this can only affect stores large enough to truncate."""
    from veracium.graph import subgraph_for_query
    store = _store()
    for i in range(5):
        apply_supersession(store, _dated(f"e{i}", f"note {i}", 1 + i), DEFAULT_RELATIONS)
    a = [e.id for e in subgraph_for_query(store, "u1", "note", max_edges=40)]
    b = [e.id for e in subgraph_for_query(store, "u1", "note", max_edges=40,
                                          coverage_share=0.0)]
    assert a == b


# -- first-known vs liveness (C′) --------------------------------------------

def test_reinforcement_preserves_when_a_fact_first_became_true():
    """The defect LongMemEval exposed: a fact restated over time kept only its
    LATEST restatement date, so `render_edges` stated "(since <latest>)" to the
    answering model — a false statement in the answer context, not merely lost
    history. valid_from is first-known and immutable; liveness rides on
    observed_at."""
    store = _store()
    for i, day in enumerate((1, 9, 20), start=1):
        apply_supersession(store, _edge(f"e{i}", "morning runs", day=day,
                                        relation="prefers"), DEFAULT_RELATIONS)
    # specs/0012 Design 1: each restatement persists per-edge; the defect this test
    # protects — the FIRST-known date surviving restatement and rendering truthfully —
    # holds through e1, which is byte-untouched.
    edges = store.edges("u1", active_only=False)
    assert len(edges) == 3
    first = next(e for e in edges if e.id == "e1")
    assert first.valid_from == _dt(1), "first-known must survive restatement"
    assert first.provenance.observed_at == _dt(1)   # 0012: liveness no longer transfers
    assert "since 2026-07-01" in render_edges(edges)


def test_absorption_winner_inherits_earliest_first_known():
    """A fuller restatement is the same fact, so the winner carries the earliest
    point the fact was known — min, not max."""
    store = _store()
    apply_supersession(store, _edge("old", "Miso", day=2), DEFAULT_RELATIONS)
    apply_supersession(store, _edge("new", "cat Miso", day=11), DEFAULT_RELATIONS)
    winner = store.edges("u1")[0]
    assert winner.id == "new"
    assert winner.valid_from == _dt(2)
    assert winner.provenance.observed_at == _dt(11)


def test_valid_from_never_exceeds_observed_at_on_any_write_path():
    """Research's cheap invariant: a fact cannot become true after we recorded
    it. Holds at creation and after reinforcement, absorption and supersession —
    the check that catches a regression here."""
    store = _store()
    apply_supersession(store, _edge("a", "runs", day=1, relation="prefers"), DEFAULT_RELATIONS)
    apply_supersession(store, _edge("b", "runs", day=9, relation="prefers"), DEFAULT_RELATIONS)
    apply_supersession(store, _edge("c", "morning runs", day=14, relation="prefers"),
                       DEFAULT_RELATIONS)
    apply_supersession(store, _edge("d", "tea", day=3, relation="prefers"), DEFAULT_RELATIONS)
    for e in store.edges("u1", active_only=False, include_quarantined=True):
        assert e.valid_from <= e.provenance.observed_at, \
            f"{e.id}: became true {e.valid_from} after being recorded {e.provenance.observed_at}"


def test_lifecycle_ages_against_last_recording_not_first_known():
    """A fact stated long ago and restated yesterday is live; one recorded once
    and never again is what should lapse. Ageing against valid_from lapsed the
    former — the bug reinforcement exists to prevent, re-created by making
    valid_from immutable without moving liveness."""
    from datetime import timedelta
    from veracium import lifecycle
    from veracium.config import MemoryConfig
    from veracium.schema import Volatility
    store = _store()
    e = _edge("old-but-live", "morning runs", day=1, relation="prefers")
    e.volatility = Volatility.SLOW
    apply_supersession(store, e, DEFAULT_RELATIONS)
    apply_supersession(store, _edge("restated", "morning runs", day=27,
                                    relation="prefers"), DEFAULT_RELATIONS)
    cfg = MemoryConfig()
    report = lifecycle.expire(store, "u1", cfg, now=_dt(28))
    assert store.edges("u1"), "a recently restated fact must not lapse"
    assert report["lapsed"] == 0
