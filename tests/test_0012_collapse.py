"""specs/0012 (accepted v17) — the I8 read-path collapse family + I9.

The store keeps every edge (Design 1); these tests pin what SURFACES: strict-redundancy-only
suppression over the full authority envelope, unique-anchor value grouping with all three
anchored-by cells, deterministic survivors, the one-warning-carrier pin, and coverage of all
three model-facing read paths. I10's budget family lands in the next slice.
"""
import itertools
from datetime import datetime, timedelta, timezone

from veracium.compile import _grounded_inputs
from veracium.config import MemoryConfig
from veracium.graph import apply_supersession, collapse_for_render, render_edges, subgraph_for_query
from veracium.lifecycle import expire
from veracium.proactive import assemble
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge, EvidenceAuthor, Provenance, Volatility)
from veracium.schema import _SourceType as SourceType  # specs/0016 D1: internal tests bind the private name
from veracium.store.sqlite import SqliteStore

U = "u1"
NOW = datetime.now(timezone.utc)


def _edge(eid, obj, *, author=EvidenceAuthor.USER, disc=Disclosure.MENTIONABLE,
          derived=None, days=1, rel="works_as", note="", vol=Volatility.SLOW,
          flag=False, conf=0.7):
    t = NOW - timedelta(days=days)
    return Edge(id=eid, user_id=U, subject="user", relation=rel, object=obj, note=note,
                volatility=vol, valid_from=t, needs_confirmation=flag,
                provenance=Provenance(source_type=SourceType.STATED, author_of_evidence=author,
                                      evidence_ref=f"ev-{eid}", disclosure=disc,
                                      derived_from=derived, confidence=conf, observed_at=t))


def _ids(edges):
    return {e.id for e in edges}


# --- I8: every read path suppresses only strictly-redundant ACTIVE duplicates ---------
def test_read_paths_collapse_same_class_duplicates():
    s = SqliteStore(":memory:")
    for i in range(5):                                   # 5 strictly-redundant restatements
        s.add_edge(_edge(f"e{i}", "chef", days=50 - 10 * i))
    s.add_edge(_edge("e-sys", "chef", author=EvidenceAuthor.SYSTEM, days=2))  # cross-author

    # query recall: one USER representative + the SYSTEM edge (envelope differs)
    got = subgraph_for_query(s, U, "chef job")
    assert len([e for e in got if e.provenance.author_of_evidence == EvidenceAuthor.USER]) == 1
    assert len([e for e in got if e.provenance.author_of_evidence == EvidenceAuthor.SYSTEM]) == 1
    # wiki input
    edges, _ = _grounded_inputs(s, U, DEFAULT_RELATIONS)
    assert len(edges) == 2
    # the store keeps every edge
    assert len(s.edges(U, active_only=True)) == 6


# --- I8a: no trust distinction or staleness signal hidden -----------------------------
def test_collapse_preserves_author_and_confirmation():
    s = SqliteStore(":memory:")
    s.add_edge(_edge("e-user", "chef", days=200, flag=True))              # stale, flagged
    s.add_edge(_edge("e-sys", "chef", author=EvidenceAuthor.SYSTEM, days=1))
    got = subgraph_for_query(s, U, "chef")
    assert _ids(got) >= {"e-user", "e-sys"}
    text = render_edges(got)
    assert "possibly stale" in text                       # the flag renders


# --- I8b: history survives the collapse ------------------------------------------------
def test_history_survives_the_collapse():
    s = SqliteStore(":memory:")
    apply_supersession(s, _edge("e1", "Acme", days=2000), DEFAULT_RELATIONS)
    apply_supersession(s, _edge("e2", "Beta", days=1000), DEFAULT_RELATIONS)   # supersedes
    apply_supersession(s, _edge("e3", "Acme", days=10), DEFAULT_RELATIONS)     # back again
    got = subgraph_for_query(s, U, "Acme employer works")
    assert {"e1", "e3"} <= _ids(got)                      # BOTH Acme edges
    text = render_edges(got)
    assert "SUPERSEDED" in text                           # the old interval renders


# --- I8c: proactive is inside the contract ---------------------------------------------
def test_proactive_collapses_duplicates_within_budget():
    s = SqliteStore(":memory:")
    for i in range(4):                                    # 4 duplicate transients
        s.add_edge(_edge(f"t{i}", "traveling", rel="health_state",
                         vol=Volatility.TRANSIENT, days=3 - i % 3))
    due = (NOW + timedelta(days=3)).date().isoformat()
    s.add_edge(_edge("e-commit", f"report due {due}", rel="works_on",
                     vol=Volatility.SLOW, days=5))
    s.add_edge(_edge("e-flag", "chef", days=300, flag=True))
    ctx, edges, _eps, _tr = assemble(s, U, MemoryConfig(db_path=":memory:"),
                                     now=NOW, token_budget=1200)
    assert ctx.count("traveling") == 1                    # one line, not four
    assert f"due {due}" in ctx                        # the commitment surfaces
    assert "confirm when natural" in ctx                  # the stale prompt surfaces


# --- I8d: subsumed variants share one group --------------------------------------------
def test_subsumed_variants_share_one_group():
    s = SqliteStore(":memory:")
    full = "senior backend engineer acme portland"
    s.add_edge(_edge("e-full", full, days=1))
    s.add_edge(_edge("e-v1", "senior backend engineer acme", days=2))   # -1 token
    s.add_edge(_edge("e-v2", "backend engineer acme", days=3))          # -2 from full? via v1
    surfaced, _ = collapse_for_render(list(s.edges(U, active_only=True)))
    assert _ids(surfaced) == {"e-full"}                   # one representative, the full form


# --- I8e: incomparable anchors never merge ---------------------------------------------
def test_incomparable_anchors_are_never_merged():
    s = SqliteStore(":memory:")
    s.add_edge(_edge("e-cat", "cat Miso", rel="has_pet", vol=Volatility.DURABLE, days=3))
    s.add_edge(_edge("e-dog", "dog Miso", rel="has_pet", vol=Volatility.DURABLE, days=2))
    s.add_edge(_edge("e-bare", "Miso", rel="has_pet", vol=Volatility.DURABLE, days=1))
    surfaced, _ = collapse_for_render(list(s.edges(U, active_only=True)))
    assert _ids(surfaced) == {"e-cat", "e-dog", "e-bare"}  # ambiguous surfaces alone


# --- I8f: the COMPLETE effective-authority envelope, table-driven ----------------------
def test_collapse_respects_the_authority_envelope():
    combos = [(EvidenceAuthor.USER, None), (EvidenceAuthor.USER, EvidenceAuthor.SYSTEM),
              (EvidenceAuthor.SYSTEM, None), (EvidenceAuthor.SYSTEM, EvidenceAuthor.THIRD_PARTY)]
    for (a1, d1), (a2, d2) in itertools.combinations(combos, 2):
        s = SqliteStore(":memory:")
        s.add_edge(_edge("x1", "chef", author=a1, derived=d1, days=2))
        s.add_edge(_edge("x2", "chef", author=a2, derived=d2, days=1))
        surfaced, _ = collapse_for_render(list(s.edges(U, active_only=True,
                                                       include_quarantined=True)))
        assert _ids(surfaced) == {"x1", "x2"}, f"{(a1, d1)} vs {(a2, d2)} must not collapse"
    # equal envelope DOES collapse
    s = SqliteStore(":memory:")
    s.add_edge(_edge("y1", "chef", derived=EvidenceAuthor.SYSTEM, days=2))
    s.add_edge(_edge("y2", "chef", derived=EvidenceAuthor.SYSTEM, days=1))
    surfaced, _ = collapse_for_render(list(s.edges(U, active_only=True)))
    assert len(surfaced) == 1


# --- I8g: no carrier-visible information lost ------------------------------------------
def test_collapse_never_drops_carrier_fields():
    s = SqliteStore(":memory:")
    s.add_edge(_edge("e-note", "finish the report", rel="works_on", days=30,
                     note=f"due {(NOW + timedelta(days=4)).date().isoformat()}", vol=Volatility.DURABLE))
    s.add_edge(_edge("e-fresh", "finish the report", rel="works_on", days=1,
                     vol=Volatility.TRANSIENT))
    surfaced, _ = collapse_for_render(list(s.edges(U, active_only=True)))
    assert _ids(surfaced) == {"e-note", "e-fresh"}        # note AND volatility distinct
    got = subgraph_for_query(s, U, "report due")
    assert "e-note" in _ids(got)                          # query scoring still finds the note
    ctx, *_ = assemble(s, U, MemoryConfig(db_path=":memory:"), now=NOW)
    assert f"due {(NOW + timedelta(days=4)).date().isoformat()}" in ctx   # the commitment renders


# --- I8h: one confirmable owner at a time ----------------------------------------------
def _flagged_mem(tmp_path, n):
    import veracium
    cfg = MemoryConfig(db_path=str(tmp_path / "m.db"))
    mem = veracium.Memory(llm=lambda p, **k: "{}", config=cfg)
    for i in range(n):
        mem.store.add_edge(_edge(f"f{i}", "chef", days=300 + i, flag=True))
    return mem, cfg


def test_confirming_the_surfaced_warning_clears_it(tmp_path):
    mem, cfg = _flagged_mem(tmp_path, 2)
    ctx, edges, _eps, _tr = assemble(mem.store, U, cfg, now=NOW)
    shown = [e for e in edges if e.needs_confirmation]
    assert len(shown) == 1                                # one owner
    mem.confirm(U, shown[0].id)
    kept = next(e for e in mem.store.edges(U, active_only=True) if e.id == shown[0].id)
    assert kept.needs_confirmation is False               # 0008 per-edge clearing intact
    mem.close()


def test_n_flagged_duplicates_surface_one_owner_at_a_time(tmp_path):
    mem, cfg = _flagged_mem(tmp_path, 25)
    confirmed = 0
    for _ in range(25):
        ctx, edges, _eps, _tr = assemble(mem.store, U, cfg, now=NOW)
        shown = [e for e in edges if e.needs_confirmation]
        assert len(shown) == 1, f"round {confirmed}: expected ONE owner, got {len(shown)}"
        if confirmed == 0:
            assert "×25 restatements" in ctx              # the truthful count, round one
        mem.confirm(U, shown[0].id)
        confirmed += 1
    ctx, edges, _eps, _tr = assemble(mem.store, U, cfg, now=NOW)
    assert not [e for e in edges if e.needs_confirmation]  # all 25 confirmed, none left
    mem.close()


# --- I8i: all three anchored-by cells --------------------------------------------------
def test_a_token_dropping_chain_surfaces_its_unanchored_members():
    # _subsumes' bound is 2 extra tokens: a 6→5→3 chain makes the interior 3-token
    # member ZERO-anchored (6 is the only anchor; 6 vs 3 exceeds the bound; 5 is not
    # an anchor). It must surface alone — never silently suppressed, never merged up.
    s = SqliteStore(":memory:")
    s.add_edge(_edge("c6", "alpha beta gamma delta epsilon zeta", days=1))
    s.add_edge(_edge("c5", "alpha beta gamma delta epsilon", days=2))       # anchored by c6
    s.add_edge(_edge("c3", "alpha beta gamma", days=3))                     # anchored by NONE
    surfaced, _ = collapse_for_render(list(s.edges(U, active_only=True)))
    assert _ids(surfaced) == {"c6", "c3"}                 # c5 collapses; c3 surfaces alone


# --- I8j: deterministic, store-order invariant -----------------------------------------
def test_surfaced_set_is_permutation_invariant():
    members = [
        _edge("p1", "chef", note="", days=1),             # fresh, empty note
        _edge("p2", "chef", note="head chef at Aria", days=9),
        _edge("p3", "chef", days=5),
        _edge("p4", "chef", days=3, flag=True),
    ]
    baseline = None
    for perm in itertools.permutations(members):
        surfaced, _ = collapse_for_render(list(perm))
        got = _ids(surfaced)
        baseline = baseline or got
        assert got == baseline                            # identical set, every order
    assert "p2" in baseline                               # the note-bearer always survives


# --- I9: the high-restatement regime, adversarial mix ----------------------------------
def test_the_high_restatement_regime_stays_correct_and_bounded():
    s = SqliteStore(":memory:")
    prior = _edge("e-prior", "senior engineer acme", days=200)
    s.add_edge(prior)
    before = next(e for e in s.edges(U, active_only=True)).model_dump()
    forms = ["senior engineer acme", "engineer acme"]   # exact + token-DROPPED only
    # (a token-ADDED form would hit ABSORPTION, which 0012 leaves unchanged)
    for i in range(25):
        e = _edge(f"r{i}", forms[i % 2], days=max(1, 190 - 7 * i),
                  note="restated in standup" if i % 5 == 0 else "",
                  vol=Volatility.TRANSIENT if i % 7 == 0 else Volatility.SLOW)
        apply_supersession(s, e, DEFAULT_RELATIONS)       # every ingest applies cleanly
    assert s.supersessions_refused(U) == 0                # no contention artifacts
    after = next(e for e in s.edges(U, active_only=True)
                 if e.id == "e-prior").model_dump()
    assert after == before                                # the prior untouched throughout
    r = expire(s, U, MemoryConfig(db_path=":memory:"), now=NOW)
    assert next(e for e in s.edges(U, active_only=True, include_quarantined=True)
                if e.id == "e-prior").needs_confirmation  # expire still flags it
    surfaced, _ = collapse_for_render(list(s.edges(U, active_only=True,
                                                   include_quarantined=True)))
    assert len(surfaced) < 15                             # bounded: 26 rows, far fewer surface
