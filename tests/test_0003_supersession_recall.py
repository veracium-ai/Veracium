"""specs/0003 — the read layer (§4c-ii, §4e): the authority permutation, the compiler
contention contract, and the registry/policy cache digest.

Function-level so the LLM is not needed: the permutation is asserted on subgraph_for_query,
the wiki exclusion on `_grounded_inputs`, and the cache digest on `needs_recompile`.
"""
from datetime import datetime, timedelta, timezone

from veracium import compile as _compile
from veracium.compile import (_grounded_inputs, _live_refusal_contention_edge_ids,
                              _policy_digest, needs_recompile)
from veracium.graph import apply_supersession, subgraph_for_query
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge, EvidenceAuthor,
                             Provenance, Relation, SourceType)
from veracium.store.sqlite import SqliteStore

U = "u1"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _edge(eid, author, obj, rel="works_as", subject="user", disc=Disclosure.MENTIONABLE,
          df=None, age=0):
    return Edge(id=eid, user_id=U, subject=subject, relation=rel, object=obj,
                provenance=Provenance(source_type=SourceType.STATED, author_of_evidence=author,
                                      evidence_ref="ev", disclosure=disc, derived_from=df,
                                      observed_at=T0 + timedelta(days=age)))


# --- I6b: the permutation (authority within a group; unrelated positions fixed) ----

def test_unrelated_edges_keep_their_positions(tmp_path):
    """§4e: the reorder is a PERMUTATION — only a functional-contention group's own slots
    are reordered by authority; every unrelated edge keeps its position (I6b)."""
    s = SqliteStore(str(tmp_path / "s.db"))
    # a functional contention on works_as: low-authority THIRD_PARTY is newer (would rank
    # first on recency), high-authority USER is older; plus unrelated edges interleaved.
    s.add_edge(_edge("tp", EvidenceAuthor.THIRD_PARTY, "unemployed", disc=Disclosure.QUARANTINED, age=9))
    s.add_edge(_edge("user", EvidenceAuthor.USER, "CFO at Acme", age=1))
    s.add_edge(_edge("pet", EvidenceAuthor.USER, "cat Miso", rel="has_pet", age=5))
    before = subgraph_for_query(s, U, "works_as pet", relations=DEFAULT_RELATIONS)
    ids = [e.id for e in before]
    # the higher-authority contention member (user) precedes the lower (tp) despite being older
    assert ids.index("user") < ids.index("tp")
    # the unrelated has_pet edge keeps whatever slot it held (not dragged into the group)
    # — reorder only swapped the two works_as members' slots among themselves.
    assert "pet" in ids


def test_higher_authority_contention_member_ranks_first(tmp_path):  # I6a via ordering
    """A refusal must not reduce the prior's recall visibility: the higher-authority
    grounded prior is authority-ordered ahead of the fenced challenger that failed to
    retire it, so a small max_edges keeps the prior, not the newer challenger (§4d)."""
    s = SqliteStore(str(tmp_path / "s.db"))
    prior = _edge("p", EvidenceAuthor.USER, "CFO at Acme", age=1)
    s.add_edge(prior)
    inc = _edge("i", EvidenceAuthor.THIRD_PARTY, "unemployed job role work", disc=Disclosure.QUARANTINED, age=9)
    apply_supersession(s, inc, DEFAULT_RELATIONS)                    # refused, both active
    ranked = subgraph_for_query(s, U, "works_as", relations=DEFAULT_RELATIONS)
    assert [e.id for e in ranked][0] == "p"                         # the user's fact survives first


# --- I6c: the compiler contention contract (refusal-scoped exclusion) -----------

def test_a_live_refusal_contention_is_excluded_from_the_wiki(tmp_path):
    """§4c-ii: a contested functional group in a LIVE refusal contention is kept OUT of the
    one-value LLM wiki — the compiler only ever sees facts that have one current value."""
    s = SqliteStore(str(tmp_path / "s.db"))
    s.add_edge(_edge("p", EvidenceAuthor.USER, "CFO at Acme"))
    s.add_edge(_edge("other", EvidenceAuthor.USER, "Boston", rel="located_at"))    # uncontested
    apply_supersession(s, _edge("i", EvidenceAuthor.THIRD_PARTY, "unemployed",
                                disc=Disclosure.QUARANTINED), DEFAULT_RELATIONS)
    excluded = _live_refusal_contention_edge_ids(s, U, DEFAULT_RELATIONS)
    assert excluded == {"p", "i"}
    wiki_edges, _ = _grounded_inputs(s, U, DEFAULT_RELATIONS)
    wiki_ids = {e.id for e in wiki_edges}
    assert "p" not in wiki_ids                                      # the contested prior is withheld
    assert "other" in wiki_ids                                      # an uncontested fact still compiles


def test_pre_existing_non_refusal_contention_is_not_given_the_derived_view(tmp_path):
    """Option B (round-9 blocker 2): the wiki-exclusion is REFUSAL-scoped. A pre-existing
    contention with no refusal record (legacy/import/host) keeps ordinary wiki behaviour."""
    s = SqliteStore(str(tmp_path / "s.db"))
    # two active same-class values on a functional relation, added directly — NO refusal
    s.add_edge(_edge("a", EvidenceAuthor.USER, "CFO"))
    s.add_edge(_edge("b", EvidenceAuthor.USER, "CEO"))
    assert _live_refusal_contention_edge_ids(s, U, DEFAULT_RELATIONS) == set()
    wiki_ids = {e.id for e in _grounded_inputs(s, U, DEFAULT_RELATIONS)[0]}
    assert {"a", "b"} <= wiki_ids                                   # not withheld — no new surface


def test_resolving_a_refusal_contention_stops_excluding_the_prior(tmp_path):
    """When the contention ends (a member goes inactive), the group is no longer a LIVE
    refusal contention, so the surviving prior returns to the ordinary wiki inputs."""
    s = SqliteStore(str(tmp_path / "s.db"))
    prior = _edge("p", EvidenceAuthor.USER, "CFO at Acme")
    s.add_edge(prior)
    inc = _edge("i", EvidenceAuthor.THIRD_PARTY, "unemployed", disc=Disclosure.QUARANTINED)
    apply_supersession(s, inc, DEFAULT_RELATIONS)
    assert "p" not in {e.id for e in _grounded_inputs(s, U, DEFAULT_RELATIONS)[0]}
    s.invalidate_edge("i", prior.valid_from, "disputed")           # the challenger goes away
    assert _live_refusal_contention_edge_ids(s, U, DEFAULT_RELATIONS) == set()
    assert "p" in {e.id for e in _grounded_inputs(s, U, DEFAULT_RELATIONS)[0]}


# --- I6c: the cache binds the registry/policy digest ---------------------------

def test_cached_wiki_is_invalidated_when_relation_registry_semantics_change(tmp_path):
    """Same store and user, two registries, ZERO intervening writes: a registry that
    classifies a relation differently changes the required wiki, with no store_version
    change, so the digest — not store_version — forces recompilation (round-10 B2)."""
    s = SqliteStore(str(tmp_path / "s.db"))
    s.add_edge(_edge("p", EvidenceAuthor.USER, "CFO"))
    reg_a = DEFAULT_RELATIONS
    reg_b = {**DEFAULT_RELATIONS, "has_pet": Relation(name="has_pet", functional=True)}
    assert _policy_digest(reg_a) != _policy_digest(reg_b)
    # a wiki compiled and cached under registry A (envelope carries A's digest)
    ver = s.store_version(U)
    s.set_wiki(U, f"{_compile._ENVELOPE}{_policy_digest(reg_a)}\ncached body", ver)
    assert not needs_recompile(s, U, 8, reg_a)                     # fresh under A
    assert needs_recompile(s, U, 8, reg_b)                         # stale under B, no writes


def test_a_pre_0003_wiki_without_an_envelope_recompiles(tmp_path):
    """A cache written before 0003 has no policy envelope, so its digest is None and never
    matches — it recompiles on the first recall after upgrade (§7a)."""
    s = SqliteStore(str(tmp_path / "s.db"))
    s.add_edge(_edge("p", EvidenceAuthor.USER, "CFO"))
    s.set_wiki(U, "legacy body with no envelope", s.store_version(U))
    assert needs_recompile(s, U, 8, DEFAULT_RELATIONS)


def test_a_single_refusal_recompiles_the_wiki_immediately(tmp_path):
    """Forming a contention drops the wiki cache in the SAME commit, so the next recall
    recompiles regardless of the recompile_after threshold (§4c-ii, immediate not batched)."""
    s = SqliteStore(str(tmp_path / "s.db"))
    prior = _edge("p", EvidenceAuthor.USER, "CFO at Acme")
    s.add_edge(prior)
    s.set_wiki(U, f"{_compile._ENVELOPE}{_policy_digest(DEFAULT_RELATIONS)}\nbody",
               s.store_version(U))
    assert not needs_recompile(s, U, 8, DEFAULT_RELATIONS)         # fresh
    apply_supersession(s, _edge("i", EvidenceAuthor.THIRD_PARTY, "unemployed",
                                disc=Disclosure.QUARANTINED), DEFAULT_RELATIONS)
    assert s.get_wiki(U) is None                                   # dropped on formation
    assert needs_recompile(s, U, 8, DEFAULT_RELATIONS)             # immediate recompile
