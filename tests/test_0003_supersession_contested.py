"""specs/0003 §4c-ii — the structured `Recall.contested` carrier and the reach contract.

The reach-sensitive corrections (rounds 9–11): a value the deterministic surface renders is
a FULL structured member; the unseen fenced CROSS-partition challenger is content-free
linkage only, on every public surface. Tested precisely on `_build_contested` (so selection
is controlled) plus one end-to-end recall.
"""
from veracium import Memory
from veracium.config import MemoryConfig
from veracium.budgets import floor_for as _ff
_floor_recall = _ff("recall")
from veracium.graph import apply_supersession
from veracium.schema import Disclosure, Edge, EvidenceAuthor, Provenance

U = "u1"


class _Fake:
    def __call__(self, *a, **k):
        return ""


def _mem(tmp_path):
    # wiki disabled (recompile_after=0) → no LLM call in recall
    return Memory(llm=_Fake(), config=MemoryConfig(
        db_path=str(tmp_path / "m.db"), wiki_recompile_after_writes=0))


def _edge(eid, author, obj, disc=Disclosure.MENTIONABLE, df=None):
    return Edge(id=eid, user_id=U, subject="user", relation="works_as", object=obj,
                provenance=Provenance(author_of_evidence=author,
                                      evidence_ref="ev", disclosure=disc, derived_from=df))


def _make_cross_partition_refusal(mem):
    """USER grounded prior vs a refused THIRD_PARTY fenced (quarantined) challenger."""
    mem.store.add_edge(_edge("p", EvidenceAuthor.USER, "CFO at Acme"))
    apply_supersession(mem.store, _edge("i", EvidenceAuthor.THIRD_PARTY, "unemployed",
                                        disc=Disclosure.QUARANTINED), mem.config.relations)


def test_recall_contested_carries_full_edge_only_for_exposed_members(tmp_path):
    mem = _mem(tmp_path)
    _make_cross_partition_refusal(mem)
    contested, exposed = mem._build_contested(U, query_edges=[])   # nothing query-selected
    assert len(contested) == 1
    g = contested[0]
    assert g.subject == "user" and g.relation == "works_as"
    # the grounded prior is a FULL exposed Edge even though the query selected nothing
    assert [e.id for e in g.exposed] == ["p"]
    assert g.exposed[0].object == "CFO at Acme"
    # the unseen fenced cross-partition challenger is content-free linkage only
    assert [lk.edge_id for lk in g.linkage] == ["i"]
    assert g.linkage[0].partition == "unverified" and g.linkage[0].authority == 0
    # content-free: the challenger's value/provenance never travels in the linkage
    assert "unemployed" not in g.model_dump_json()


def test_only_the_unseen_fenced_cross_partition_challenger_is_content_free_linkage(tmp_path):
    """If ordinary retrieval DID select the fenced challenger, it becomes a full exposed
    member (case 3) — content-free linkage is only for the UNSEEN one."""
    mem = _mem(tmp_path)
    _make_cross_partition_refusal(mem)
    inc = next(e for e in mem.store.edges(U, active_only=True) if e.id == "i")
    contested, _ = mem._build_contested(U, query_edges=[inc])      # challenger IS selected
    g = contested[0]
    assert "i" in [e.id for e in g.exposed]                        # now a full member
    assert g.linkage == []                                         # no content-free entry


def test_a_same_partition_grounded_member_i6_renders_is_a_full_exposed_member_even_if_unselected(tmp_path):
    """round-11: a same-partition GROUNDED challenger (here a refused SYSTEM value, still
    MENTIONABLE/grounded) is a full exposed member even when the query did not select it —
    I6's deterministic rendering and the structured carrier agree."""
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("p", EvidenceAuthor.USER, "CFO at Acme"))
    # SYSTEM eff 2 < USER 3 → refused; SYSTEM MENTIONABLE → grounded (same partition)
    apply_supersession(mem.store, _edge("i", EvidenceAuthor.SYSTEM, "unemployed"),
                       mem.config.relations)
    contested, _ = mem._build_contested(U, query_edges=[])         # nothing selected
    g = contested[0]
    ids = {e.id for e in g.exposed}
    assert ids == {"p", "i"}                                       # BOTH grounded → both exposed
    assert g.linkage == []                                         # nothing content-free


def test_recall_edges_is_the_dedup_union_with_the_exposed_prior(tmp_path):
    """Recall.edges is the de-duplicated union of query-selected edges and the exposed
    preservation members — the higher-authority grounded prior is present regardless."""
    mem = _mem(tmp_path)
    _make_cross_partition_refusal(mem)
    r = mem.recall(U, "unrelated query about pizza")
    ids = [e.id for e in r.edges]
    assert ids.count("p") == 1                                     # present exactly once
    assert "p" in ids                                              # the prior survives recall
    assert len(r.contested) == 1


def test_proactive_recall_never_volunteers_a_fenced_contested_value(tmp_path):
    mem = _mem(tmp_path)
    _make_cross_partition_refusal(mem)
    r = mem.recall(U)                                              # proactive (query=None)
    assert "unemployed" not in r.context
    assert r.contested == []                                       # proactive surfaces no contention


def test_refusal_does_not_evict_the_prior_at_a_finite_budget(tmp_path):
    """I6a (finite-budget form): holding query/config/store fixed and adding ONLY the
    refused edge, the higher-authority prior never drops below where it stood before the
    refusal. The CONTESTED block is rendered first (HIGH priority), so the prior survives a
    tight budget both before and after the refusal."""
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("p", EvidenceAuthor.USER, "CFO at Acme"))
    # specs/0012 I10e: budgets below the envelope-derived floor (256) now raise; the
    # finite-budget intent survives at a just-above-floor value.
    before = mem.recall(U, "works_as", token_budget=_floor_recall + 4)
    assert "CFO at Acme" in before.context                          # prior visible pre-refusal
    apply_supersession(mem.store, _edge("i", EvidenceAuthor.THIRD_PARTY, "unemployed",
                                        disc=Disclosure.QUARANTINED), mem.config.relations)
    after = mem.recall(U, "works_as", token_budget=_floor_recall + 4)
    assert "CFO at Acme" in after.context                           # NOT evicted by the refusal
    assert "unemployed" not in after.grounded                       # challenger stays out of grounded


def test_contested_surface_is_budgeted_not_unbounded(tmp_path):
    """round-8 blocker 2: the contested surface participates in token_budget — it is not an
    unbounded prompt surface across accumulating contentions. Many contentions + a tiny
    budget → deterministic truncation, flagged in Recall.truncated, and a bounded context."""
    mem = _mem(tmp_path)
    functional = ["works_as", "located_at", "prefers", "health_state", "deadline"]
    for n, rel in enumerate(functional):
        long_tail = " with an intentionally verbose qualifier occupying budget" * 3
        mem.store.add_edge(_edge(f"p{n}", EvidenceAuthor.USER,
                                 f"grounded value {n}{long_tail}").model_copy(
            update={"relation": rel}))
        inc = _edge(f"i{n}", EvidenceAuthor.THIRD_PARTY, f"challenge {n}{long_tail}",
                    disc=Disclosure.QUARANTINED).model_copy(update={"relation": rel})
        apply_supersession(mem.store, inc, mem.config.relations)
    full = mem.recall(U, "value")                                   # unbudgeted: all groups render
    assert full.context.count("CONTESTED") >= 1
    assert len(full.contested) == 5
    tight = mem.recall(U, "value", token_budget=_floor_recall + 4)                # just above the floor
    assert tight.truncated                                          # the surface was gated
    assert len(tight.context) < len(full.context)                  # bounded, not unbounded
    # the structured carrier still reports every contention (raw material is full; the
    # RENDERED surface is what the budget bounds, cf. Recall.edges)
    assert len(tight.contested) == 5


def test_the_carrier_renders_every_distinct_grounded_value_not_a_pair(tmp_path):
    """The carrier is n-ary, not pair-assuming (round-8 corr B): it exposes every distinct
    active member of the group. (A guard-produced refusal contention collapses to a pair —
    equal-authority challengers supersede each other — so n>2 arises from mixed histories;
    the carrier's generic membership is what this pins.)"""
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("p", EvidenceAuthor.USER, "CFO at Acme"))
    apply_supersession(mem.store, _edge("i", EvidenceAuthor.SYSTEM, "unemployed"),
                       mem.config.relations)
    contested, _ = mem._build_contested(U, query_edges=[])
    g = contested[0]
    # every DISTINCT active value in the group is exposed (here the grounded pair), ordered
    # by effective authority — never assuming a fixed count
    assert [e.object for e in g.exposed] == ["CFO at Acme", "unemployed"]
    assert [e.id for e in g.exposed] == ["p", "i"]                 # USER (3) before SYSTEM (2)
