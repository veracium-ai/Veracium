"""specs/0004 W1–W8 (+W6): derived views must not outlive a revoked trust decision.

The invariant surface frozen at 0004's round-2 approval and implemented at
acceptance (external round 21, atomic with 0022/0023). The drop lives in the
sole `active=0` writer (`_invalidate_edge_row`), keyed on a RETAIN-set — so an
unrecognised reason drops (fail-closed, internal R1), and every invalidation
path present or future inherits the drop by construction (internal R2).
"""

import ast
import pathlib
import uuid

import pytest

from veracium import EvidenceAuthor, SqliteStore
from veracium.graph import _build_supersession_plan, apply_supersession
from veracium.schema import (DEFAULT_RELATIONS, DISPOSITIONED_REASONS, Edge,
                             Provenance, WIKI_RETAINING_REASONS, utcnow)

U = "u"


def _edge(obj, rel="located_at"):
    return Edge(id=f"e-{uuid.uuid4().hex[:8]}", user_id=U, subject="user",
                relation=rel, object=obj,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}"))


def _store_with_wiki(tmp_path):
    s = SqliteStore(str(tmp_path / "w.db"))
    e = _edge("Lisbon")
    s.add_edge(e)
    s.set_wiki(U, "cached wiki body", s.store_version(U))
    assert s.get_wiki(U) is not None
    return s, e


# --- W1: a revoking invalidation empties the wiki ---------------------------

def test_dispute_drops_the_wiki(tmp_path):
    s, e = _store_with_wiki(tmp_path)
    s.invalidate_edge(e.id, utcnow(), "disputed")
    assert s.get_wiki(U) is None


# --- W2: the SUPERSESSION path drops it — apply_supersession_plan's
#         prior_invalidations, through the sole writer ------------------------

def test_third_party_supersession_drops_the_wiki(tmp_path):
    s = SqliteStore(str(tmp_path / "w.db"))
    apply_supersession(s, _edge("Lisbon"), DEFAULT_RELATIONS)
    s.set_wiki(U, "cached", s.store_version(U))
    incoming = _edge("Porto")          # located_at is functional → supersedes
    plan, _ = _build_supersession_plan(s, incoming, DEFAULT_RELATIONS,
                                       f"sup-{incoming.id}")
    assert any(r == "superseded" for _, _, r in plan.prior_invalidations), (
        "fixture defect: the plan supersedes nothing, so this test would pass "
        "without exercising W2")
    s.apply_supersession_plan(plan)
    assert s.get_wiki(U) is None


# --- W3: staleness does NOT drop it — a pinned deliberate exclusion ----------

@pytest.mark.parametrize("reason", ["lapsed", "decayed"])
def test_decay_does_not_drop_the_wiki(tmp_path, reason):
    s, e = _store_with_wiki(tmp_path)
    s.invalidate_edge(e.id, utcnow(), reason)
    assert s.get_wiki(U) is not None, (
        f"{reason} is a staleness event, not a trust event — W3 pins the "
        f"exclusion so the drop cannot erode into 'drop on everything'")


# --- W4: no LLM call on the drop path ----------------------------------------

def test_wiki_drop_makes_no_llm_call(tmp_path):
    # The store layer holds no LLM handle, so the property is structural: the
    # drop is a DELETE inside the invalidation transaction. Assert it at the
    # source — the sole writer's function body performs no attribute access on
    # any completion/llm object and no import of a provider.
    src = pathlib.Path("src/veracium/store/sqlite.py").read_text()
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_invalidate_edge_row")
    body = ast.get_source_segment(src, fn)
    assert "llm" not in body.lower() and "complete" not in body.lower(), (
        "the drop path must never invoke a model — recompilation happens "
        "lazily at the next read, not eagerly at the drop")


# --- W5: the registries — total, and consulted with the right polarity -------

def test_invalidation_reason_registry_is_total():
    """Every reason any PRODUCER can pass is dispositioned. The producer set is
    enumerated from the §2c row: dispute/correct (host verbs), lifecycle
    (lapsed/decayed), the supersession plan builder (superseded /
    absorbed_duplicate), and 0022's sweep (revoked_source). A new producer
    reason fails here until its spec dispositions it."""
    producer_reachable = {
        "disputed", "corrected",              # __init__.py host verbs
        "lapsed", "decayed",                  # lifecycle.py
        "superseded", "absorbed_duplicate",   # graph.py plan builder
        "revoked_source",                     # 0022's sweep (reserved seat)
    }
    undispositioned = producer_reachable - set(DISPOSITIONED_REASONS)
    assert not undispositioned, (
        f"producer-reachable reasons with no disposition: {undispositioned}")
    # the retain-set is the 'retain' projection of the record — one source
    assert WIKI_RETAINING_REASONS == {
        r for r, d in DISPOSITIONED_REASONS.items() if d == "retain"}
    # and the producer literals above are honest: each appears at a call site
    src_root = pathlib.Path("src/veracium")
    corpus = "".join(p.read_text() for p in
                     [src_root / "__init__.py", src_root / "lifecycle.py",
                      src_root / "graph.py"])
    for reason in producer_reachable - {"revoked_source"}:
        assert f'"{reason}"' in corpus, (
            f"{reason!r} is enumerated as producer-reachable but no producer "
            f"passes it — the enumeration has drifted from the code")


def test_runtime_consults_only_the_retain_set(tmp_path):
    """The runtime branches on retain-set membership, never on a drop-list
    (internal R1's polarity): EVERY registered reason outside the retain set
    drops. An INVENTED reason string no longer reaches this branch at all —
    specs/0029 V-KIND (accepted 2026-09-01) refuses the WRITE for a reason
    outside DISPOSITIONED_REASONS, which is fail-closed one layer earlier:
    the edge stays live and the wiki stays as it was, because nothing
    happened. Before 0029 this test drove the invented string through and
    asserted the drop; the polarity claim is the same, exercised over the
    registered domain (the only one the writer can now see)."""
    from veracium.schema import DISPOSITIONED_REASONS, WIKI_RETAINING_REASONS
    s, e = _store_with_wiki(tmp_path)
    with pytest.raises(ValueError):
        s.invalidate_edge(e.id, utcnow(), "some_reason_no_spec_has_named")
    assert s.get_wiki(U) is not None, "a refused write must touch nothing"
    non_retaining = sorted(set(DISPOSITIONED_REASONS) - WIKI_RETAINING_REASONS)
    assert non_retaining, "the polarity needs at least one registered non-retaining reason"
    for reason in non_retaining:
        d = tmp_path / reason; d.mkdir()
        s2, e2 = _store_with_wiki(d)
        s2.invalidate_edge(e2.id, utcnow(), reason)
        assert s2.get_wiki(U) is None, f"registered non-retaining reason {reason!r} did not drop"


# --- W6: 0003's refusal-contention drop still fires, independently -----------

def test_refusal_contention_still_drops_the_wiki(tmp_path):
    """The reason-blind 0003 condition survives the 0004 generalisation: a
    RETAINING reason still drops the wiki when the edge participates in a
    refusal contention, because contention resolution is a derived-view event
    regardless of why the edge retired."""
    s, e = _store_with_wiki(tmp_path)
    s._conn.execute(
        "INSERT INTO supersession_refusals(refusal_id, user_id, prior_edge_id, "
        "incoming_edge_id, relation, prior_effective, incoming_effective, "
        "rule_version, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (f"rf-{e.id}", U, e.id, "e-other", "located_at",
         utcnow().isoformat(), utcnow().isoformat(), 1, utcnow().isoformat()))
    s._conn.commit()
    s.invalidate_edge(e.id, utcnow(), "lapsed")    # retaining reason
    assert s.get_wiki(U) is None


# --- W7: the transition invariant is STRUCTURAL — one active=0 writer --------

def test_sole_active_zero_writer():
    src_root = pathlib.Path("src/veracium")
    writers = []
    for f in sorted(src_root.rglob("*.py")):
        text = f.read_text()
        if "active=0" not in text and "active = 0" not in text:
            continue
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, ast.FunctionDef):
                continue
            body = ast.get_source_segment(text, node) or ""
            if "SET active=0" in body:
                writers.append((f.name, node.name))
    assert writers == [("sqlite.py", "_invalidate_edge_row")], (
        f"active=0 writers: {writers} — 0004 W7 requires exactly ONE, so every "
        f"active→inactive transition inherits the wiki drop; a second writer "
        f"must route through _invalidate_edge_row instead")


# --- W8: the absorption exclusion is PINNED (W-Q1 ruling) --------------------

def test_absorption_does_not_drop_the_wiki(tmp_path):
    s = SqliteStore(str(tmp_path / "w.db"))
    apply_supersession(s, _edge("Miso", rel="has_pet"), DEFAULT_RELATIONS)
    s.set_wiki(U, "cached", s.store_version(U))
    winner = _edge("cat Miso", rel="has_pet")      # more specific → absorbs
    plan, _ = _build_supersession_plan(s, winner, DEFAULT_RELATIONS,
                                       f"sup-{winner.id}")
    assert any(r == "absorbed_duplicate" for _, _, r in plan.prior_invalidations), (
        "fixture defect: nothing absorbed, so this test would pass vacuously")
    assert not any(r == "superseded" for _, _, r in plan.prior_invalidations), (
        "fixture defect: a superseded row would drop the wiki and mask W8")
    s.apply_supersession_plan(plan)
    assert s.get_wiki(U) is not None, (
        "absorption is trust-preserving by construction (W-Q1, ruled): the "
        "content stays backed by a live same-trust record, so the exclusion "
        "shelters nothing revoked")
