"""specs/0027 — semantic hybrid recall: the §6 invariant surface.

Every test name below is the executable check a §6 row names. The fused
construction is exercised at two altitudes on purpose (the 0020 precedent):
end-to-end through `Memory.recall` — where a bypass would live — and directly
on `fused_subgraph` for the collapse/reserve cells whose fixtures need exact
control of which lane holds which edge.

The embedder here is a SYNONYM-AXIS vocab embedder: words in one axis class
embed identically, so "yacht" is semantically close to "boat" while sharing
zero shipped `_tokens` with it — a real zero-overlap paraphrase, which is the
one shape the lexical lane cannot find (§1).
"""
from __future__ import annotations

import pathlib
import sys
import time
from datetime import datetime, timedelta, timezone

import pytest

from veracium import Memory, Recall, RecalledEdge, SEMANTIC_STATUSES
from veracium import semantic as sm_mod
from veracium.config import MemoryConfig
from veracium.graph import (_lexical_scored, _tokens, collapse_for_render,
                            fused_subgraph, semantic_duplicate_of,
                            subgraph_for_query)
from veracium.schema import (Disclosure, Edge, EvidenceAuthor, Provenance)
from veracium.scope import Identity

ROOT = pathlib.Path(__file__).resolve().parents[1]
U = "u-0027"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

A1 = Identity(None, "agent-1")


class _Fake:
    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        return ""


# synonym axes: words in one class embed to the same dimension, so semantic
# closeness NEVER implies token overlap
_AXES = [{"boat", "yacht", "sail", "dinghy"},
         {"cat", "feline", "tabby"},
         {"temple", "shrine", "pagoda"},
         {"car", "sedan", "vehicle"},
         {"bread", "sourdough", "loaf"}]


class VocabEmbed:
    def id(self):
        return "vocab-syn@1"

    def dim(self):
        return len(_AXES) + 1

    def __call__(self, texts):
        out = []
        for t in texts:
            words = set(t.lower().split())
            v = [float(len(words & ax)) for ax in _AXES]
            v.append(0.05)                    # bias: never the zero vector
            out.append(v)
        return out


def _cfg(tmp_path, name="m.db", **kw):
    return MemoryConfig(db_path=str(tmp_path / name),
                        wiki_recompile_after_writes=0, **kw)


def _mem(tmp_path, name="m.db", *, embed=VocabEmbed(), **kw):
    return Memory(llm=_Fake(), embed=embed, config=_cfg(tmp_path, name, **kw))


_SEQ = [0]


def _edge(eid, subject, relation, obj, *, note="", days=0, author=EvidenceAuthor.USER,
          disc=Disclosure.MENTIONABLE, derived=None, source_id=None,
          active=True, needs_confirmation=False):
    t = T0 + timedelta(days=days)
    e = Edge(id=eid, user_id=U, subject=subject, relation=relation, object=obj,
             note=note, needs_confirmation=needs_confirmation,
             provenance=Provenance(author_of_evidence=author,
                                   evidence_ref=f"ev-{eid}", observed_at=t,
                                   disclosure=disc, derived_from=derived,
                                   source_id=source_id),
             valid_from=t)
    if not active:
        e = e.model_copy(update={"invalidated_at": t + timedelta(days=1),
                                 "invalidation_reason": "superseded"})
    return e


def _emb_count(store, user_id=U):
    return store._conn.execute(
        "SELECT COUNT(*) FROM edge_embedding WHERE user_id=?",
        (user_id,)).fetchone()[0]


# ---------------------------------------------------------------------------
# V10 / V3 — the frozen legacy projection and every degrade path
# ---------------------------------------------------------------------------

def _oracle_module():
    import importlib.util
    p = ROOT / "specs" / "evidence" / "0027" / "v10_oracle" / "generate_oracle.py"
    spec = importlib.util.spec_from_file_location("v10_oracle", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_legacy_projection_identical_when_semantic_off_unscoped(tmp_path):
    """V10: with principal=None and semantic_status != ok, the ordered
    edge-id list is byte-identical to the FROZEN pre-feature oracle —
    captured at commit bd5fdc0, before `subgraph_for_query` was refactored,
    so no refactor drift can redefine "today's behaviour" from inside."""
    import json
    orc = _oracle_module()
    store = orc.build_store(tmp_path / "oracle.db")
    frozen = json.loads((ROOT / "specs" / "evidence" / "0027" / "v10_oracle" /
                         "legacy_projections.json").read_text())
    got = orc.capture(store)
    assert got == frozen, "the live pipeline drifted from the frozen oracle"
    store.close()


def test_lexical_fallback_is_pre_feature_identical_unscoped(tmp_path):
    """V3: semantic=False / no-embedder / raising-embedder / invalid-output /
    absent-storage all reproduce the SAME legacy projection, and each names
    its status. The baseline is the semantic=False path, which V10 above
    pins to the pre-feature oracle."""
    edges = [_edge("f1", "user", "enjoys", "boat trips", days=1),
             _edge("f2", "harbor:1", "hosts", "boat races", days=2),
             _edge("f3", "user", "drinks", "coffee", days=3)]

    def build(embed):
        m = _mem(tmp_path, f"f-{id(embed)}.db", embed=embed)
        for e in edges:
            m.store.add_edge(e)
        return m

    base = build(None)
    r0 = base.recall(U, "boat", semantic=False)
    assert r0.semantic_status == "disabled"
    baseline = [e.id for e in r0.edges]
    assert r0.recalled_edges == {}

    r1 = base.recall(U, "boat")                      # auto, no embedder
    assert r1.semantic_status == "no_embedder"
    assert [e.id for e in r1.edges] == baseline

    class RaisingId(VocabEmbed):
        def id(self):
            raise RuntimeError("boom")
    r2 = build(RaisingId()).recall(U, "boat")
    assert r2.semantic_status == "unavailable"
    assert [e.id for e in r2.edges] == baseline

    class RaisingCall(VocabEmbed):
        def __call__(self, texts):
            raise RuntimeError("embedder down")
    r3 = build(RaisingCall()).recall(U, "boat", semantic=True)
    assert r3.semantic_status == "unavailable"
    assert [e.id for e in r3.edges] == baseline

    class BadOutput(VocabEmbed):
        def __call__(self, texts):
            return [[float("nan")] * self.dim() for _ in texts]
    r4 = build(BadOutput()).recall(U, "boat")
    assert r4.semantic_status == "degraded"          # query vector refused (V5)
    assert [e.id for e in r4.edges] == baseline

    class NoSemanticStore(type(base.store)):
        def semantic_candidates(self, *a, **k):
            raise NotImplementedError("no semantic storage")
    m5 = build(VocabEmbed())
    m5.store.__class__ = NoSemanticStore
    r5 = m5.recall(U, "boat")
    assert r5.semantic_status == "unavailable"
    assert [e.id for e in r5.edges] == baseline


def test_semantic_status_closed_vocabulary(tmp_path):
    """V-STATUS: the vocabulary is CLOSED at exactly the six §4b values, and
    the ok path reports ok."""
    assert SEMANTIC_STATUSES == {"ok", "disabled", "no_embedder",
                                 "unavailable", "timeout", "degraded"}
    m = _mem(tmp_path)
    m.store.add_edge(_edge("s1", "user", "enjoys", "boat trips"))
    m.embed_backfill(U)
    r = m.recall(U, "boat")
    assert r.semantic_status == "ok"
    assert r.semantic_status in SEMANTIC_STATUSES


def test_embedder_timeout_degrades(tmp_path):
    """V6: an embedder exceeding semantic_timeout_ms degrades to the lexical
    result with status "timeout", no exception, within the bound (plus
    scheduling slack) — recall never blocks on the embedder."""
    class Slow(VocabEmbed):
        def __call__(self, texts):
            time.sleep(10)
            return super().__call__(texts)

    m = _mem(tmp_path, embed=Slow(), semantic_timeout_ms=150)
    m.store.add_edge(_edge("t1", "user", "enjoys", "boat trips"))
    t = time.perf_counter()
    r = m.recall(U, "boat")
    elapsed = time.perf_counter() - t
    assert r.semantic_status == "timeout"
    assert [e.id for e in r.edges] == ["t1"]
    assert elapsed < 2.0, f"recall blocked {elapsed:.2f}s past the deadline"


# ---------------------------------------------------------------------------
# V2 / V9 — classification preservation
# ---------------------------------------------------------------------------

def test_semantic_preserves_classification(tmp_path):
    """V2: a poison-shaped edge reachable ONLY through the semantic lane
    surfaces FENCED — same class the lexical lane would give it; it never
    enters the grounded context."""
    m = _mem(tmp_path)
    m.store.add_edge(_edge("p1", "user", "enjoys", "boat trips", days=1))
    # third-party claim, quarantined, ZERO token overlap with the query —
    # only the synonym axis reaches it
    m.store.add_edge(_edge("p2", "stranger:x", "claims", "free yacht offer",
                           days=2, author=EvidenceAuthor.THIRD_PARTY,
                           disc=Disclosure.QUARANTINED))
    m.embed_backfill(U)
    r = m.recall(U, "boat")
    got = {e.id: e for e in r.edges}
    assert "p2" in got, "the semantic lane did not surface the paraphrase"
    assert r.recalled_edges["p2"].route == "semantic"
    assert got["p2"].quarantined and not got["p2"].assertable, \
        "classification moved — the fence is off"
    assert "yacht" not in r.grounded, "poison reached the grounded context"
    assert "yacht" in r.unverified, "the fenced surface lost the claim"


def test_retired_edge_class_parity_across_routes(tmp_path):
    """V9: a retired edge keeps its vector; surfaced via the semantic lane it
    carries the IDENTICAL non-assertable class the lexical lane gives it —
    no route makes a non-assertable edge assertable."""
    m = _mem(tmp_path)
    live = _edge("r1", "marina:1", "sells", "yacht berths", days=1)
    m.store.add_edge(live)
    m.embed_backfill(U)
    m.store.invalidate_edge("r1", T0 + timedelta(days=2), "superseded")
    assert _emb_count(m.store) == 1, "retirement must RETAIN the vector"
    r = m.recall(U, "boat")
    got = {e.id: e for e in r.edges}
    if "r1" in got:                                   # surfaced as history
        assert not got["r1"].active and not got["r1"].assertable
        lex = {e.id: e for e in subgraph_for_query(m.store, U, "yacht berths")}
        assert "r1" in lex and lex["r1"].assertable == got["r1"].assertable


# ---------------------------------------------------------------------------
# V4 / V5 / V-FRESH / V-ERASE — the index lifecycle
# ---------------------------------------------------------------------------

def test_embedding_is_a_derived_index(tmp_path):
    """V4: a full rebuild changes no disposition, and embeddings are absent
    from the export (0005: a derived index is not exported)."""
    m = _mem(tmp_path)
    m.store.add_edge(_edge("d1", "user", "enjoys", "boat trips"))
    m.store.add_edge(_edge("d2", "temple:k", "houses", "gold shrine",
                           author=EvidenceAuthor.THIRD_PARTY,
                           disc=Disclosure.QUARANTINED))
    m.embed_backfill(U)
    r_before = m.recall(U, "boat")
    classes_before = {e.id: (e.assertable, e.quarantined) for e in r_before.edges}
    # full rebuild
    m.store._conn.execute("DELETE FROM edge_embedding")
    m.store._conn.commit()
    assert _emb_count(m.store) == 0
    m.embed_backfill(U)
    r_after = m.recall(U, "boat")
    classes_after = {e.id: (e.assertable, e.quarantined) for e in r_after.edges}
    assert classes_before == classes_after, "a rebuild changed a disposition"
    out = tmp_path / "export.jsonl"
    m.export_memory(U, str(out))
    exported = out.read_text()
    assert "edge_embedding" not in exported and '"vec"' not in exported, \
        "the derived index leaked into the export"


def test_vector_binding_and_no_cross_embedder(tmp_path):
    """V5: vectors never co-search across embedder_id or dim; malformed
    vectors and blobs are refused at every boundary."""
    m = _mem(tmp_path)
    m.store.add_edge(_edge("b1", "harbor:2", "moors", "yacht fleet"))
    m.embed_backfill(U)

    class OtherEmbed(VocabEmbed):
        def id(self):
            return "vocab-syn@2"           # a NEW identity — never co-searches
    m2 = Memory(llm=_Fake(), embed=OtherEmbed(),
                config=MemoryConfig(db_path=str(tmp_path / "m.db"),
                                    wiki_recompile_after_writes=0))
    r = m2.recall(U, "boat")
    assert r.semantic_status == "ok"
    assert all(v.route == "lexical" for v in r.recalled_edges.values()), \
        "a cross-embedder_id vector co-searched"

    # store-level: wrong-length blob is refused, never served
    m.store._conn.execute(
        "UPDATE edge_embedding SET vec = ?", (b"\x00" * 7,))
    m.store._conn.commit()
    qv = VocabEmbed()([" boat "])[0]
    assert m.store.semantic_candidates(
        U, qv, embedder_id="vocab-syn@1", dim=VocabEmbed().dim(),
        k=10, min_cosine=0.0) == []

    # component hygiene at the validation boundary
    d = 3
    assert sm_mod.validate_vector([True, 0.1, 0.2], d) is None       # bool
    assert sm_mod.validate_vector([float("inf"), 0.1, 0.2], d) is None
    assert sm_mod.validate_vector([0.0, 0.0, 0.0], d) is None        # zero
    assert sm_mod.validate_vector([0.1, 0.2], d) is None             # length
    assert sm_mod.validate_vector("abc", d) is None
    assert sm_mod.cosine([0.0, 0.0], [1.0, 0.0]) is None             # zero norm


def test_stale_vector_excluded_after_text_mutation(tmp_path):
    """V-FRESH: after an in-place text mutation (same id), the stored vector's
    digest no longer matches the live edge and it is EXCLUDED at read; the
    digest-conditional write refuses a stale worker's upsert."""
    m = _mem(tmp_path)
    e = _edge("fr1", "marina:3", "rents", "yacht slips")
    m.store.add_edge(e)
    m.embed_backfill(U)
    old_digest = sm_mod.content_digest(e)
    mutated = e.model_copy(update={"note": "renewed for the season"})
    m.store.add_edge(mutated)                        # same-id replace
    qv = VocabEmbed()(["boat"])[0]
    assert m.store.semantic_candidates(
        U, qv, embedder_id="vocab-syn@1", dim=VocabEmbed().dim(),
        k=10, min_cosine=0.0) == [], "a stale vector was served"
    # a delayed worker holding the OLD digest writes nothing
    assert m.store.upsert_embedding(
        edge_id="fr1", user_id=U, embedder_id="vocab-syn@1",
        content_digest=old_digest, dim=VocabEmbed().dim(),
        vec=sm_mod.pack_vec(qv), built_at=T0.isoformat()) is False
    # re-embed under the NEW digest restores the lane
    m.embed_backfill(U)
    got = m.store.semantic_candidates(
        U, qv, embedder_id="vocab-syn@1", dim=VocabEmbed().dim(),
        k=10, min_cosine=0.0)
    assert [eid for eid, _ in got] == ["fr1"]


def test_forget_user_erases_embeddings(tmp_path):
    """V-ERASE: forget_user removes every edge_embedding row in the same
    transaction; an in-flight worker inserts nothing afterwards."""
    m = _mem(tmp_path)
    e = _edge("er1", "user", "enjoys", "boat trips")
    m.store.add_edge(e)
    m.embed_backfill(U)
    assert _emb_count(m.store) == 1
    d = sm_mod.content_digest(e)
    m.store.forget_user(U)
    assert _emb_count(m.store) == 0, "erasure left embedding bytes behind"
    # the in-flight worker: no live edge → digest-conditional write refuses
    assert m.store.upsert_embedding(
        edge_id="er1", user_id=U, embedder_id="vocab-syn@1",
        content_digest=d, dim=VocabEmbed().dim(),
        vec=sm_mod.pack_vec([0.1] * VocabEmbed().dim()),
        built_at=T0.isoformat()) is False
    assert _emb_count(m.store) == 0


# ---------------------------------------------------------------------------
# V-COLLAPSE / V1 — the Stage 3/4 construction, driven directly
# ---------------------------------------------------------------------------

def _prep(edges, query, sm):
    """Build fused_subgraph inputs from real edges via the real extraction."""
    class _ListStore:
        def __init__(self, es):
            self._es = es

        def edges(self, user_id, active_only=True, **kw):
            return [e for e in self._es if e.active] if active_only else list(self._es)

    scored, relevant, by_id = _lexical_scored(_ListStore(edges), U, query)
    return scored, relevant, by_id


def test_lexical_first_collapse_unchanged_by_semantic(tmp_path):
    """V-COLLAPSE (R5-1 + R6-1): collapse decides MEMBERSHIP on Lx alone —
    the kept lexical set equals collapse_for_render(Lx)'s, a semantic-only
    arrival can neither resurface a suppressed member nor change a survivor —
    while the output ORDER is the FUSED order, not collapse's lexical order.
    Drives the reviewer's 1-anchor→2-anchor fixture and the duplicate/
    subsuming/warning conjuncts of semantic_duplicate_of."""
    # the Miso fixture: A anchors B (unique subsumption) so B is suppressed;
    # C is the 2nd anchor whose arrival USED to resurface B
    A = _edge("cA", "pet:m", "called", "cat miso", days=3)
    B = _edge("cB", "pet:m", "called", "miso", days=2)
    C = _edge("cC", "pet:m", "called", "dog miso", days=1)
    edges = [A, B, C]
    scored, relevant, by_id = _prep(edges, "cat miso called", None)
    lx_ids = {e.id for _s, _o, e in scored}
    assert lx_ids == {"cA", "cB", "cC"}, "fixture drift: all three are lexical here"
    # make C semantic-only by REMOVING it from the lexical lane (the unit
    # seam: the construction is defined over its inputs)
    scored_lx = [t for t in scored if t[2].id != "cC"]
    lex_baseline = [e.id for e in collapse_for_render(
        [e for _s, _o, e in scored_lx])[0]]
    assert lex_baseline == ["cA"], "fixture drift: B must be suppressed by A alone"
    out, meta = fused_subgraph(scored_lx, relevant, by_id, [("cC", 0.9)],
                               max_edges=40)
    got = [e.id for e in out]
    assert "cB" not in got, \
        "the semantic arrival RESURFACED a lexically-suppressed member (R5-1)"
    assert "cC" in got and meta["cC"]["route"] == "semantic"
    assert set(got) & {"cA", "cB"} == {"cA"}, "a lexical survivor changed"

    # ORDER is fused, not lexical (R6-1): a semantic-only edge with the top
    # fused rank leads the output even though collapse never ranked it
    D = _edge("oD", "user", "enjoys", "harbor walks", days=5)
    E = _edge("oE", "user", "enjoys", "hill walks", days=4)
    F = _edge("oF", "marina:9", "offers", "yacht cruises", days=1)
    scored2, rel2, by2 = _prep([D, E, F], "walks", None)
    assert [e.id for _s, _o, e in scored2] == ["oD", "oE"]
    out2, meta2 = fused_subgraph(scored2, rel2, by2,
                                 [("oF", 0.95), ("oD", 0.5)], max_edges=40)
    assert meta2["oD"]["route"] == "both"
    # oD: lex rank 1 + sem rank 2 → 1/61 + 1/62 ; oF: sem rank 1 → 1/61 ;
    # oE: lex rank 2 → 1/62. Fused order: oD, oF, oE — NOT the lexical order.
    assert [e.id for e in out2] == ["oD", "oF", "oE"], \
        "the output lost the fused order (R6-1: v6 emitted collapse's order)"

    # the suppression predicate's conjuncts, one mutant each
    surv = _edge("sv", "pet:m", "called", "miso cat", days=1)
    dup = _edge("dp", "pet:m", "called", "miso cat", days=0)
    assert semantic_duplicate_of(dup, surv), "the baseline duplicate must hold"
    sub = _edge("sb", "pet:m", "called", "big miso cat", days=0)
    assert not semantic_duplicate_of(sub, surv), \
        "a SUBSUMING value is DISTINCT — added, not suppressed (conjunct 3)"
    warn = _edge("wn", "pet:m", "called", "miso cat", days=0,
                 needs_confirmation=True)
    assert not semantic_duplicate_of(warn, surv), \
        "suppressing the flagged member would drop a warning (conjunct 5)"
    dead = _edge("dd", "pet:m", "called", "miso cat", days=0, active=False)
    assert not semantic_duplicate_of(dead, surv), \
        "inactive history is never suppressed (conjunct 1)"
    dead_surv = _edge("ds", "pet:m", "called", "miso cat", days=2,
                      active=False)
    assert not semantic_duplicate_of(dup, dead_surv), \
        "suppressed AGAINST inactive history — conjunct 1 requires BOTH " \
        "records active (R7-2: the reviewer's other-carrier mutant)"
    other = _edge("ot", "pet:m", "called", "miso cat", days=0,
                  disc=Disclosure.USE_ONLY)
    assert not semantic_duplicate_of(other, surv), \
        "a different authority envelope is never a duplicate (conjunct 2)"


def test_single_reserve_no_belt_and_exact_fallback(tmp_path):
    """V1: ONE reserve, capped at ⌈max_edges/4⌉, taken in FUSED order; with
    semantic off, exact matches are placed exactly as today (⊆ V10)."""
    edges = [_edge(f"x{i:02d}", "user", "likes", f"boat topic{i}", days=i)
             for i in range(12)]
    scored, relevant, by_id = _prep(edges, "boat", None)
    out, meta = fused_subgraph(scored, relevant, by_id, [], max_edges=8)
    assert len(out) == 8
    # every edge is relevant+assertable, so the reserve holds exactly the cap
    # (⌈8/4⌉ = 2) and leads the output in fused order
    top2 = [e.id for e in out[:2]]
    fused_top2 = sorted(meta, key=lambda i: meta[i]["fused_rank"])[:2]
    assert top2 == fused_top2, "the reserve is not taken in fused order"
    # semantic off ⇒ exactly today's placement
    class _S:
        def __init__(self, es): self._es = es
        def edges(self, user_id, active_only=True, **kw):
            return list(self._es)
    legacy = [e.id for e in subgraph_for_query(_S(edges), U, "boat",
                                               max_edges=8)]
    assert [e.id for e in out] == legacy, \
        "with Sm empty the construction must equal today's placement"


def test_recalled_edges_covers_only_ranked_selections(tmp_path, monkeypatch):
    """V7: recalled_edges holds an entry for EXACTLY the ranked selection
    that survived narrowing; a contention/I6a-preserved append (never
    scored) gets NO invented entry."""
    m = _mem(tmp_path)
    m.store.add_edge(_edge("v1", "user", "enjoys", "boat trips"))
    # ENTITY subject + zero overlap + no synonym axis: outside BOTH lanes —
    # genuinely unscored, present only via the preservation append
    preserved = _edge("v9", "archive:9", "holds", "quiet records")
    m.store.add_edge(preserved)
    m.embed_backfill(U)
    real = Memory._build_contested

    def fake_contested(self, user_id, edges, view):
        groups, extra = real(self, user_id, edges, view)
        return groups, list(extra) + [preserved]     # the I6a append seam
    monkeypatch.setattr(Memory, "_build_contested", fake_contested)
    r = m.recall(U, "boat")
    ids = [e.id for e in r.edges]
    assert "v9" in ids, "the preserved append must reach Recall.edges"
    assert "v9" not in r.recalled_edges, \
        "an unscored preserved edge got an INVENTED provenance entry (V7)"
    assert r.recalled_edges.get("v1") is not None
    assert set(r.recalled_edges) <= set(ids)
    for k, v in r.recalled_edges.items():
        assert isinstance(v, RecalledEdge) and v.edge_id == k
        assert v.route in ("lexical", "semantic", "both")


def test_semantic_only_survives_grounded_budget_fixture(tmp_path):
    """V-SEM: in a pinned store with NO higher-precedence classes, a
    semantic-only assertable edge survives collapse→reserve→cover under
    max_edges=2 and its route reads "semantic" from recalled_edges."""
    m = _mem(tmp_path, max_subgraph_edges=2)
    m.store.add_edge(_edge("gA", "user", "enjoys", "boat trips", days=3))
    m.store.add_edge(_edge("gB", "marina:7", "offers", "yacht cruises",
                           days=2))                   # zero overlap with "boat"
    m.store.add_edge(_edge("gC", "user", "dislikes", "loud chewing", days=1))
    m.embed_backfill(U)
    r = m.recall(U, "boat")
    assert r.semantic_status == "ok"
    ids = [e.id for e in r.edges]
    assert "gB" in ids, "the semantic-only match was crowded out of the budget"
    assert r.recalled_edges["gB"].route == "semantic"
    assert r.recalled_edges["gB"].semantic_cosine is not None
    assert isinstance(next(e for e in r.edges if e.id == "gB"), Edge)


def test_lexical_tokenizer_is_pinned(tmp_path):
    """V-TOK: the lexical overlap on BOTH sides is the shipped `_tokens`
    (graph.py `_stem`/`_STOP`): the recorded lexical_overlap must equal the
    shipped tokenizer's intersection, case/stem behaviour included."""
    m = _mem(tmp_path)
    e = _edge("tk1", "user", "enjoys", "Sailing BOATS daily")
    m.store.add_edge(e)
    m.embed_backfill(U)
    q = "boats sailing"
    r = m.recall(U, q)
    expected = len(_tokens(f"{e.subject} {e.relation} {e.object} {e.note}")
                   & _tokens(q))
    assert expected > 0, "fixture drift: the query must overlap"
    assert r.recalled_edges["tk1"].lexical_overlap == expected, \
        "overlap is not the shipped _tokens on both sides"


# ---------------------------------------------------------------------------
# V8 / scoped V10 — the lens on both lanes
# ---------------------------------------------------------------------------

def test_scope_lens_shapes_before_reserve(tmp_path):
    """V8(a): a cross-visible edge that shaping demotes cannot occupy an
    assertable reserve slot — both lanes are shaped BEFORE ranking/collapse/
    I6, so the reserve reads the principal-facing assertability."""
    m = _mem(tmp_path, max_subgraph_edges=2,
             scope_groups={"g": [A1]}, cross_scope_visible=True)
    # cross-scope, raw-MENTIONABLE (assertable raw; shaped → USE_ONLY,
    # non-assertable to this principal), high lexical score
    m.store.add_edge(_edge("s-cross", "user", "boat", "boat boat boat",
                           source_id="agent-2", days=3))
    # the principal's own relevant assertable record
    m.store.add_edge(_edge("s-own", "user", "sails", "boat weekends",
                           source_id="agent-1", days=2))
    m.store.add_edge(_edge("s-noise", "user", "likes", "boat snacks",
                           source_id="agent-1", days=1))
    m.embed_backfill(U)
    r = m.recall(U, "boat", principal=A1, semantic=False)
    got = {e.id: e for e in r.edges}
    assert "s-own" in got, \
        "a shaped-non-assertable cross edge displaced the principal's own " \
        "assertable record from the reserve (the R3-1 bug)"
    if "s-cross" in got:
        assert got["s-cross"].provenance.disclosure == Disclosure.USE_ONLY, \
            "a RAW cross-scope record reached the structured carrier"
        assert not got["s-cross"].assertable


def test_scoped_shape_merge_intended(tmp_path):
    """V8(b), R5-3/R6-4: a cross-scope duplicate that shapes to the same
    principal-facing envelope MERGES (intended); the suppressed member's
    identity is GONE from the result — count-only-and-discarded, not
    "counted somewhere the caller can read"."""
    m = _mem(tmp_path, scope_groups={"g": [A1]}, cross_scope_visible=True)
    # A: cross-scope MENTIONABLE, shaped → (USE_ONLY, THIRD_PARTY)
    m.store.add_edge(_edge("mgA", "person:kit", "runs", "harbor cafe",
                           source_id="agent-2", days=1))
    # B: own-scope, ALREADY (USE_ONLY, THIRD_PARTY) — post-shaping identical
    # envelope AND identical value
    m.store.add_edge(_edge("mgB", "person:kit", "runs", "harbor cafe",
                           source_id="agent-1", days=2,
                           disc=Disclosure.USE_ONLY,
                           derived=EvidenceAuthor.THIRD_PARTY))
    m.embed_backfill(U)
    r = m.recall(U, "harbor cafe", principal=A1, semantic=False)
    ids = [e.id for e in r.edges]
    assert len([i for i in ids if i in ("mgA", "mgB")]) == 1, \
        "the shaped duplicates did not merge (or both vanished)"
    survivor = next(e for e in r.edges if e.id in ("mgA", "mgB"))
    # R7-5: the survivor is PINNED, not either-accepted — by
    # _collapse_survivor_order (note-bearing → most-specific → freshest →
    # id), equal notes and values leave freshest observed_at deciding:
    # mgB (days=2) beats mgA (days=1)
    assert survivor.id == "mgB", (
        f"the survivor is {survivor.id}, not the ordering's pick — either "
        f"_collapse_survivor_order changed or the fixture drifted (R7-5)")
    assert survivor.provenance.disclosure == Disclosure.USE_ONLY
    assert "mgA" not in ids
    assert "mgA" not in r.recalled_edges, \
        "the suppressed member's provenance survived — §4a says DISCARDED"


def test_scoped_semantic_off_order_amended(tmp_path):
    """V10 (scoped half): principal-bearing semantic-off recall runs the NEW
    construction — the lens precedes selection, so every structured carrier
    holds SHAPED records even with the semantic lane off. (Byte-identity to
    the legacy scoped path is NOT claimed — the deliberate amendment.)"""
    m = _mem(tmp_path, scope_groups={"g": [A1]}, cross_scope_visible=True)
    m.store.add_edge(_edge("o-cross", "person:ann", "runs", "boat rentals",
                           source_id="agent-2"))
    m.store.add_edge(_edge("o-own", "user", "enjoys", "boat trips",
                           source_id="agent-1"))
    r = m.recall(U, "boat", principal=A1, semantic=False)
    got = {e.id: e for e in r.edges}
    assert "o-cross" in got
    assert got["o-cross"].provenance.disclosure == Disclosure.USE_ONLY, \
        "the selection handed a RAW cross-scope edge downstream — Stage 0 " \
        "did not precede selection"
    assert got["o-cross"].provenance.derived_from == EvidenceAuthor.THIRD_PARTY


# ---------------------------------------------------------------------------
# config resolution (R6-3)
# ---------------------------------------------------------------------------

def test_semantic_fetch_k_sentinel_tracks_live_config(tmp_path):
    """R6-3: the None sentinel SURVIVES construction and resolves at recall
    from the LIVE max_subgraph_edges; an explicit value is re-validated
    against the live range and refuses after a bad mutation."""
    cfg = _cfg(tmp_path)
    assert cfg.semantic_fetch_k is None, "__post_init__ overwrote the sentinel"
    seen = {}

    class KSpy(VocabEmbed):
        pass
    m = _mem(tmp_path, embed=KSpy())
    m.store.add_edge(_edge("k1", "user", "enjoys", "boat trips"))
    m.embed_backfill(U)
    real = type(m.store).semantic_candidates

    def spy(self, user_id, qv, *, k, **kw):
        seen["k"] = k
        return real(self, user_id, qv, k=k, **kw)
    type(m.store).semantic_candidates = spy
    try:
        m.recall(U, "boat")
        assert seen["k"] == max(200, m.config.max_subgraph_edges)
        m.config.max_subgraph_edges = 500              # post-construction mutation
        m.recall(U, "boat")
        assert seen["k"] == 500, \
            "auto did not track the LIVE max_subgraph_edges (the stale-resolve bug)"
        m.config.semantic_fetch_k = 220
        m.config.max_subgraph_edges = 400              # 220 now out of range
        with pytest.raises(ValueError):
            m.recall(U, "boat")
        # R7-4: the live check is THE SAME validator as construction —
        # strict types included; a post-construction mutation to a bool
        # timeout or a float fetch size refuses at recall, not silently
        # passes the range test (bool <= int and float-in-range both did)
        m.config.semantic_fetch_k = 200.5
        m.config.max_subgraph_edges = 40
        with pytest.raises(ValueError):
            m.recall(U, "boat")
        m.config.semantic_fetch_k = None
        m.config.semantic_timeout_ms = True
        with pytest.raises(ValueError):
            m.recall(U, "boat")
        m.config.semantic_timeout_ms = 250
        m.config.semantic_min_cosine = 1.5
        with pytest.raises(ValueError):
            m.recall(U, "boat")
        m.config.semantic_min_cosine = 0.25
    finally:
        type(m.store).semantic_candidates = real

    with pytest.raises(ValueError):
        _cfg(tmp_path, "z1.db", semantic_min_cosine=1.5)
    with pytest.raises(ValueError):
        _cfg(tmp_path, "z2.db", semantic_timeout_ms=0)
    with pytest.raises(ValueError):
        _cfg(tmp_path, "z3.db", semantic_fetch_k=5)    # below max_subgraph_edges
