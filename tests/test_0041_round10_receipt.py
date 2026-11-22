"""specs/0041 round 10 — §11.5(3) as widened by the owner (2026-10-02, given in the dev session): the receipt NAMES the
records that may still carry the content, found by an identifier join in EITHER direction — derived from the target
(outcome episodes by `edge_id`, consolidation outputs by lineage, ledger survivors) or its SOURCE (the episode an edge
was extracted from, the edges extracted from an episode, by a shared `provenance.evidence_ref`). Dispute/correct
summaries, which have no structural link this round, are a NAMED DOMAIN flagged when the record was disputed or
corrected, or replaced a corrected prior (the owner's ruling (ii)). From 0041 v16.5 (§11.7; the owner's §10 Q4
ruling, 2026-11-22) dispute and confirmation episodes are named exactly by their reference, and the domain covers
correct alone; tests/test_0041_v16_5_confirm_quoting.py carries that amendment's cells.

Every join has a control that shares nothing with the target and is NOT named.
"""
import importlib.util
import json
import pathlib
import sys

import pytest

from veracium import Memory
from veracium.config import MemoryConfig
from veracium.schema import Disclosure, Edge, EvidenceAuthor, Provenance
from veracium.store.sqlite import SqliteStore

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("tt41_r10rc", ROOT / "tests" / "test_0041_transition_table.py")
tt = importlib.util.module_from_spec(_spec)
sys.modules["tt41_r10rc"] = tt
_spec.loader.exec_module(tt)

U = "u"


def _extracting(obj):
    """A stub extractor: one triple with `obj`, and an episode that quotes it — the shape `remember` stores."""
    def llm(prompt, system=None, role=None, **kw):
        return json.dumps({"triples": [{"subject": "user", "relation": "lives_at", "object": obj, "quote": obj}],
                           "episode": f"The user said they live at {obj}.", "instructions": []})
    return llm


def _mem(tmp_path, obj, name="rc.db"):
    return Memory(llm=_extracting(obj), config=MemoryConfig(db_path=str(tmp_path / name), wiki_recompile_after_writes=0,
                                                         scope_groups={}, require_source_id=False))


def _remembered(m, text):
    before = {e.id for e in m.store.edges(U, active_only=False)} | {e.id for e in m.store.episodes(U)}
    m.remember(U, text)
    (edge,) = [e for e in m.store.edges(U, active_only=False) if e.id not in before]
    (ep,) = [e for e in m.store.episodes(U) if e.id not in before]
    assert edge.provenance.evidence_ref == ep.provenance.evidence_ref     # the structural link the join reads
    return edge, ep


def _named(receipt):
    return {(d["kind"], d["id"]): d["via"] for d in receipt.surviving_derived}


def _prov():
    return Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev", disclosure=Disclosure.MENTIONABLE)


# ------------------------------------------------------------------------------------------------ the source direction
def test_redacting_a_remembered_fact_names_its_source_episode_and_not_another_events(tmp_path):
    m = _mem(tmp_path, "Flat 4B Zebrafinch Lane")
    edge, ep = _remembered(m, "I live at Flat 4B Zebrafinch Lane.")
    m.llm = _extracting("Tram stop 9")                            # a second, unrelated event — the control
    _e2, ep2 = _remembered(m, "My stop is Tram stop 9.")
    named = _named(m.redact(U, edge_id=edge.id, reason="subject_request"))
    assert named.get(("episode", ep.id)) == "evidence_ref"
    assert ("episode", ep2.id) not in named


def test_redacting_a_source_episode_names_the_facts_extracted_from_it(tmp_path):
    m = _mem(tmp_path, "Flat 4B Zebrafinch Lane")
    edge, ep = _remembered(m, "I live at Flat 4B Zebrafinch Lane.")
    m.llm = _extracting("Tram stop 9")
    e2, _ep2 = _remembered(m, "My stop is Tram stop 9.")
    named = _named(m.redact(U, episode_id=ep.id, reason="subject_request"))
    assert named.get(("edge", edge.id)) == "evidence_ref" and ("edge", e2.id) not in named


def test_a_record_already_redacted_is_not_named_it_no_longer_carries_the_content(tmp_path):
    m = _mem(tmp_path, "Flat 4B Zebrafinch Lane")
    edge, ep = _remembered(m, "I live at Flat 4B Zebrafinch Lane.")
    m.redact(U, episode_id=ep.id, reason="subject_request")
    assert ("episode", ep.id) not in _named(m.redact(U, edge_id=edge.id, reason="subject_request"))


def test_the_join_is_the_same_users_only(tmp_path):
    m = _mem(tmp_path, "Flat 4B Zebrafinch Lane")
    edge, ep = _remembered(m, "I live at Flat 4B Zebrafinch Lane.")
    m.store.add_episode(ep.model_copy(update={"id": "ep-other-user", "user_id": "someone-else"}))
    named = _named(m.redact(U, edge_id=edge.id, reason="subject_request"))
    assert ("episode", "ep-other-user") not in named and ("episode", ep.id) in named


def test_a_repeat_receipt_names_the_same_records_the_join_survives_the_treatment(tmp_path):
    m = _mem(tmp_path, "Flat 4B Zebrafinch Lane")
    edge, ep = _remembered(m, "I live at Flat 4B Zebrafinch Lane.")
    first = m.redact(U, edge_id=edge.id, reason="subject_request")
    again = m.redact(U, edge_id=edge.id, reason="subject_request")
    assert again.repeated and _named(again) == _named(first) and ("episode", ep.id) in _named(again)


# ------------------------------------------------------------------------------------------------ outcome episodes
def test_outcome_episodes_are_named_exactly_by_edge_id_and_another_edges_are_not(tmp_path):
    m = tt._mem(tmp_path)
    for eid in ("e-1", "e-2"):
        m.store.add_edge(Edge(id=eid, user_id=U, subject="user", relation="lives_at", object=f"place {eid}",
                              provenance=_prov()))
        m.record_outcome(U, eid, outcome="challenged", evidence_ref=f"ctx-{eid}", actor="system")
    outcome_of = {e.edge_id: e.id for e in m.store.episodes(U) if e.kind == "outcome"}
    named = _named(m.redact(U, edge_id="e-1", reason="subject_request"))
    assert named.get(("episode", outcome_of["e-1"])) == "edge_id"
    assert ("episode", outcome_of["e-2"]) not in named


# ------------------------------------------------------------------------------------------------ the named domain
def _domain(receipt):
    return SqliteStore.QUOTING_DOMAIN in receipt.receipt_domains


def test_a_disputed_record_names_its_dispute_episode_exactly_and_no_quoting_domain(tmp_path):
    """Was `test_the_quoting_domain_is_named_for_a_disputed_record`. From 0041 v16.5 the owner's §10 Q4 ruling
    (2026-11-22, "Yes, name them exactly (Recommended)") moves dispute episodes to the exact tier by their
    `dispute:<edge id>` reference (§11.7.3), and the domain covers correct alone."""
    m = tt._mem(tmp_path)
    m.store.add_edge(Edge(id="e-1", user_id=U, subject="user", relation="lives_at", object="x", provenance=_prov()))
    m.dispute(U, "e-1")
    (dep,) = [e.id for e in m.store.episodes(U) if e.provenance.evidence_ref == "dispute:e-1"]
    receipt = m.redact(U, edge_id="e-1", reason="subject_request")
    assert _named(receipt).get(("episode", dep)) == "evidence_ref:dispute"
    assert not _domain(receipt)


def test_the_quoting_domain_is_named_for_a_corrected_prior_and_for_its_replacement(tmp_path):
    m = tt._mem(tmp_path)
    m.store.add_edge(Edge(id="e-1", user_id=U, subject="user", relation="lives_at", object="x", provenance=_prov()))
    replacement = m.correct(U, "e-1", "y")["replacement"]
    assert _domain(m.redact(U, edge_id="e-1", reason="subject_request"))
    assert _domain(m.redact(U, edge_id=replacement, reason="subject_request"))   # quoted as "… to 'y'"


def test_control_the_quoting_domain_is_absent_for_a_record_never_disputed_or_corrected(tmp_path):
    m = tt._mem(tmp_path)
    m.store.add_edge(Edge(id="e-1", user_id=U, subject="user", relation="lives_at", object="x", provenance=_prov()))
    receipt = m.redact(U, edge_id="e-1", reason="subject_request")
    assert not _domain(receipt) and receipt.receipts_complete is False
