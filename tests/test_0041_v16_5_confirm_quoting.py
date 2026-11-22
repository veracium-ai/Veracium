"""specs/0041 v16.5 §11.7 (amendment `0041/confirm-quoting`, cross-spec line `0041/0009-quoting-ref-remap`).

`confirm()` writes an episode that quotes the edge it confirms. Redacting that edge named the episode in neither tier
of §8. From v16.5:
- the receipt names it by `provenance.evidence_ref` = `confirm:` + the target's id (§11.7.3, INV-Q1/Q2);
- a cross-user import rewrites `confirm:<k>` / `dispute:<k>` through its id map, on edges, episodes AND the linkage
  snapshot (§11.7.4, INV-Q3/Q4);
- a store that took a cross-user import BEFORE v16.5 reports a domain when an orphan reference exists (§11.7.5,
  INV-Q5).

Each invariant's mutant (§11.7.6) is named on the test that kills it.
"""
import json

import pytest

from veracium import EvidenceContext, Memory, portability
from veracium.config import MemoryConfig
from veracium.graph import DEFAULT_RELATIONS, apply_supersession
from veracium.schema import Edge, Episode, EvidenceAuthor, Provenance
from veracium.scope_linkage import evidence_digest_of
from veracium.store.sqlite import SqliteStore

U, U2 = "u", "u2"


def _extracting(obj):
    def llm(prompt, system=None, role=None, **kw):
        return json.dumps({"triples": [{"subject": "user", "relation": "lives_at", "object": obj, "quote": obj}],
                           "episode": "The user said where they live.", "instructions": []})
    return llm


def _mem(tmp_path, obj="ZQ-OBJECT", name="m.db"):
    return Memory(llm=_extracting(obj), config=MemoryConfig(db_path=str(tmp_path / name), wiki_recompile_after_writes=0,
                                                         scope_groups={}, require_source_id=False))


def _remembered_edge(m, user=U, obj="ZQ-OBJECT"):
    """`obj` is the text's; the stored object is the extractor's (`_mem`'s `obj`)."""
    before = {e.id for e in m.store.edges(user, active_only=False)}
    m.remember(user, f"I live at {obj}", author=EvidenceAuthor.USER, context=EvidenceContext.direct())
    (edge,) = [e for e in m.store.edges(user, active_only=False) if e.id not in before]
    return edge.id


def _named(receipt):
    return {(d["kind"], d["id"]): d["via"] for d in receipt.surviving_derived}


def _confirmation_episodes(m, user, edge_id):
    return sorted(e.id for e in m.store.episodes(user) if e.provenance.evidence_ref == f"confirm:{edge_id}")


def _holders(m, user, token):
    return sorted(e.id for e in m.store.episodes(user) if token in e.summary)


# ------------------------------------------------------------------------------------------------------------ INV-Q1
# mutants killed: the reference arm removed; an id-only join (`ep-` + the act's id)

def test_q1_a_local_confirmation_episode_is_named(tmp_path):
    m = _mem(tmp_path)
    eid = _remembered_edge(m)
    m.confirm(U, eid)
    (cep,) = _confirmation_episodes(m, U, eid)
    assert cep in _holders(m, U, "ZQ-OBJECT")                     # the episode quotes the object
    named = _named(m.redact(U, edge_id=eid, reason="subject_request"))
    assert named.get(("episode", cep)) == "evidence_ref:confirm"


@pytest.mark.parametrize("mode", ["same-user", "restore"])
def test_q1_an_imported_confirmation_episode_is_named_though_the_act_id_was_reminted(tmp_path, mode):
    src = _mem(tmp_path, name="src.db")
    eid = _remembered_edge(src)
    src.confirm(U, eid)
    exp = tmp_path / "x.jsonl"
    src.export_memory(U, exp)
    dst = _mem(tmp_path, name="dst.db")
    dst.import_memory(exp, restore=(mode == "restore"))
    (cep,) = _confirmation_episodes(dst, U, eid)
    act_ids = [c.id for c in dst.store.confirmations_for(U, eid)]
    if mode == "same-user":
        assert cep not in {f"ep-{a}" for a in act_ids}           # the id join would miss it (dev's arm 1)
    named = _named(dst.redact(U, edge_id=eid, reason="subject_request"))
    assert named.get(("episode", cep)) == "evidence_ref:confirm"


def test_q1_a_pre_80673163_confirmation_episode_with_an_independent_id_is_named(tmp_path):
    m = _mem(tmp_path)
    eid = _remembered_edge(m)
    m.store.add_episode(Episode(id="ep-legacy-confirm", user_id=U, date="2026-09-01",
                                summary="(user) confirmed 'lives_at: ZQ-OBJECT' still holds",
                                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                      evidence_ref=f"confirm:{eid}")))
    named = _named(m.redact(U, edge_id=eid, reason="subject_request"))
    assert named.get(("episode", "ep-legacy-confirm")) == "evidence_ref:confirm"


def test_q1_a_cross_user_imported_confirmation_episode_is_named(tmp_path):
    src = _mem(tmp_path, name="src.db")
    eid = _remembered_edge(src)
    src.confirm(U, eid)
    exp = tmp_path / "x.jsonl"
    src.export_memory(U, exp)
    dst = _mem(tmp_path, name="dst.db")
    dst.import_memory(exp, user_id=U2)
    (new_eid,) = [e.id for e in dst.store.edges(U2, active_only=False)]
    assert new_eid != eid
    ceps = _confirmation_episodes(dst, U2, new_eid)
    assert len(ceps) == 1, f"the reference names the destination edge: {ceps}"
    (cep,) = ceps
    named = _named(dst.redact(U2, edge_id=new_eid, reason="subject_request"))
    assert named.get(("episode", cep)) == "evidence_ref:confirm"


def test_q1_control_another_edges_confirmation_is_not_named(tmp_path):
    m = _mem(tmp_path, obj="ZQ-ONE")
    e1 = _remembered_edge(m, obj="ZQ-ONE")
    m2 = Memory(llm=_extracting("ZQ-TWO"), config=m.config)
    e2 = _remembered_edge(m2, obj="ZQ-TWO")
    m.confirm(U, e2)
    (cep2,) = _confirmation_episodes(m, U, e2)
    named = _named(m.redact(U, edge_id=e1, reason="subject_request"))
    assert ("episode", cep2) not in named


# ------------------------------------------------------------------------------------------------------------ INV-Q2
# mutant killed: the naming rule's redacted exclusion removed

def test_q2_a_redacted_confirmation_episode_is_not_named_and_a_repeat_receipt_names_the_same_set(tmp_path):
    m = _mem(tmp_path)
    eid = _remembered_edge(m)
    m.confirm(U, eid)
    (cep,) = _confirmation_episodes(m, U, eid)
    m.redact(U, episode_id=cep, reason="subject_request")
    first = m.redact(U, edge_id=eid, reason="subject_request")
    assert ("episode", cep) not in _named(first)
    again = m.redact(U, edge_id=eid, reason="subject_request")
    assert again.repeated and _named(again) == _named(first)


# ------------------------------------------------------------------------------------------------------------ INV-Q3
# mutants killed: R applied to episodes only; R not applied

def test_q3_a_cross_user_import_rewrites_confirm_and_dispute_references_to_the_destination_ids(tmp_path):
    src = _mem(tmp_path, obj="ZQ-C", name="src.db")
    ec = _remembered_edge(src, obj="ZQ-C")
    src.confirm(U, ec)
    src2 = Memory(llm=_extracting("ZQ-D"), config=src.config)
    ed = _remembered_edge(src2, obj="ZQ-D")
    src.dispute(U, ed, reason="wrong")
    exp = tmp_path / "x.jsonl"
    src.export_memory(U, exp)
    dst = _mem(tmp_path, name="dst.db")
    dst.import_memory(exp, user_id=U2)
    new = {e.object: e.id for e in dst.store.edges(U2, active_only=False)}
    refs = {e.provenance.evidence_ref for e in dst.store.episodes(U2)}
    assert f"confirm:{new['ZQ-C']}" in refs and f"dispute:{new['ZQ-D']}" in refs
    assert f"confirm:{ec}" not in refs and f"dispute:{ed}" not in refs


def test_q3_a_caller_written_confirm_reference_still_joins_an_edge_to_its_source_episode(tmp_path):
    src = SqliteStore(tmp_path / "src.db")
    prov = Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="confirm:e-other")
    src.add_edge(Edge(id="e-other", user_id=U, subject="user", relation="likes", object="tea",
                      provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-other")))
    src.add_edge(Edge(id="e-pair", user_id=U, subject="user", relation="lives_at", object="ZQ-PAIR", provenance=prov))
    src.add_episode(Episode(id="ep-pair", user_id=U, date="2026-11-01", summary="said ZQ-PAIR", provenance=prov))
    exp = tmp_path / "x.jsonl"
    portability.export_memory(src, U, exp)
    src.close()
    m = _mem(tmp_path, name="dst.db")
    m.import_memory(exp, user_id=U2)
    new_edge = {e.object: e for e in m.store.edges(U2, active_only=False)}
    (new_ep,) = [e for e in m.store.episodes(U2) if e.summary == "said ZQ-PAIR"]
    assert new_edge["ZQ-PAIR"].provenance.evidence_ref == new_ep.provenance.evidence_ref \
        == f"confirm:{new_edge['tea'].id}"
    named = _named(m.redact(U2, edge_id=new_edge["ZQ-PAIR"].id, reason="subject_request"))
    assert named.get(("episode", new_ep.id)) == "evidence_ref"


def test_q3_control_correct_and_procedure_references_are_not_rewritten(tmp_path):
    src = SqliteStore(tmp_path / "src.db")
    src.add_edge(Edge(id="e-k", user_id=U, subject="user", relation="likes", object="tea",
                      provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-k")))
    for i, ref in enumerate(("correct:e-k", "procedure:e-k")):
        src.add_episode(Episode(id=f"ep-{i}", user_id=U, date="2026-11-01", summary="s",
                                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=ref)))
    exp = tmp_path / "x.jsonl"
    portability.export_memory(src, U, exp)
    src.close()
    dst = SqliteStore(tmp_path / "dst.db")
    portability.import_memory(dst, exp, user_id=U2)
    assert {e.provenance.evidence_ref for e in dst.episodes(U2)} == {"correct:e-k", "procedure:e-k"}
    dst.close()


# ------------------------------------------------------------------------------------------------------------ INV-Q4
# mutant killed: R applied after the snapshot only (records rewritten, the linkage snapshot not)

def test_q4_the_ledger_digest_of_an_absorbed_caller_written_reference_agrees_with_the_stored_value(tmp_path):
    now = "2026-08-01T00:00:00+00:00"

    def edge(obj, eid, conf, ref):
        return Edge(id=eid, user_id=U, subject="user", relation="pet", object=obj, valid_from=now,
                    provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=ref, source_id="agent-a",
                                          observed_at=now, confidence=conf))
    s = SqliteStore(tmp_path / "s.db")
    apply_supersession(s, edge("Miso", "A", 0.2, "confirm:B"), DEFAULT_RELATIONS)
    apply_supersession(s, edge("cat Miso", "B", 0.9, "ev-B"), DEFAULT_RELATIONS)
    exp = tmp_path / "x.jsonl"
    portability.export_memory(s, U, exp)
    s.close()
    dst = SqliteStore(tmp_path / "dst.db")
    portability.import_memory(dst, exp, user_id=U2)
    by_obj = {e.object: e for e in dst.edges(U2, active_only=False)}
    absorbed, survivor = by_obj["Miso"], by_obj["cat Miso"]
    assert absorbed.invalidation_reason == "absorbed_duplicate"
    assert absorbed.provenance.evidence_ref == f"confirm:{survivor.id}"       # R reached the record
    rows = [c for c in dst.contributions(U2, "edge", survivor.id) if c.contributor_ref == absorbed.id]
    assert rows, "the absorption's ledger row was reconstructed"
    want = evidence_digest_of(absorbed.provenance.origin, absorbed.provenance.evidence_ref, dst.local_origin())
    assert {c.evidence_ref_digest for c in rows} == {want}
    dst.close()


# ------------------------------------------------------------------------------------------------------------ INV-Q5
# mutants killed: the domain removed; the domain fired on the prefix alone

def _cross_user_imported(tmp_path, monkeypatch, *, pre_v16_5):
    src = _mem(tmp_path, name="src.db")
    eid = _remembered_edge(src)
    src.confirm(U, eid)
    exp = tmp_path / "x.jsonl"
    src.export_memory(U, exp)
    if pre_v16_5:          # the old path, run: a cross-user import with R disabled
        monkeypatch.setattr(portability, "_rewrite_quoting_refs", lambda *a, **k: None)
    dst = _mem(tmp_path, name="dst.db")
    dst.import_memory(exp, user_id=U2)
    monkeypatch.undo()
    (new_eid,) = [e.id for e in dst.store.edges(U2, active_only=False)]
    return dst, eid, new_eid


def test_q5_a_pre_v16_5_remapped_store_reports_the_domain(tmp_path, monkeypatch):
    dst, old_eid, new_eid = _cross_user_imported(tmp_path, monkeypatch, pre_v16_5=True)
    assert new_eid.startswith("imp-e-")
    assert _confirmation_episodes(dst, U2, old_eid)                    # the orphan: names no edge of U2
    receipt = dst.redact(U2, edge_id=new_eid, reason="subject_request")
    assert SqliteStore.REMAPPED_QUOTING_DOMAIN in receipt.receipt_domains
    assert not any(v == "evidence_ref:confirm" for v in _named(receipt).values())   # the exact arm cannot reach it


def test_q5_control_a_v16_5_remapped_store_has_no_orphan_and_no_domain(tmp_path, monkeypatch):
    dst, _old, new_eid = _cross_user_imported(tmp_path, monkeypatch, pre_v16_5=False)
    assert new_eid.startswith("imp-e-")
    receipt = dst.redact(U2, edge_id=new_eid, reason="subject_request")
    assert SqliteStore.REMAPPED_QUOTING_DOMAIN not in receipt.receipt_domains


def test_q5_control_a_local_target_never_reports_the_domain(tmp_path):
    m = _mem(tmp_path)
    eid = _remembered_edge(m)
    m.store.add_episode(Episode(id="ep-orphan", user_id=U, date="2026-09-01", summary="s",
                                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                      evidence_ref="confirm:e-gone")))
    receipt = m.redact(U, edge_id=eid, reason="subject_request")
    assert SqliteStore.REMAPPED_QUOTING_DOMAIN not in receipt.receipt_domains


# ------------------------------------------------------------------------------- dispute joins the exact tier (§10 Q4)
# The owner's ruling, 2026-11-22: "Yes, name them exactly (Recommended)". Mutant killed: the dispute arm removed.

def _dispute_episodes(m, user, edge_id):
    return sorted(e.id for e in m.store.episodes(user) if e.provenance.evidence_ref == f"dispute:{edge_id}")


@pytest.mark.parametrize("path", ["local", "same-user", "restore", "cross-user"])
def test_q1_a_dispute_episode_is_named_on_every_arrival_path(tmp_path, path):
    src = _mem(tmp_path, name="src.db")
    eid = _remembered_edge(src)
    src.dispute(U, eid, reason="not true")
    if path == "local":
        m, user, target = src, U, eid
    else:
        exp = tmp_path / "x.jsonl"
        src.export_memory(U, exp)
        m = _mem(tmp_path, name="dst.db")
        user = U2 if path == "cross-user" else U
        m.import_memory(exp, restore=(path == "restore"), user_id=(U2 if path == "cross-user" else None))
        (target,) = [e.id for e in m.store.edges(user, active_only=False)]
    deps = _dispute_episodes(m, user, target)
    assert len(deps) == 1, f"the reference names the edge as it arrived: {deps}"
    assert deps[0] in _holders(m, user, "ZQ-OBJECT")
    receipt = m.redact(user, edge_id=target, reason="subject_request")
    assert _named(receipt).get(("episode", deps[0])) == "evidence_ref:dispute"


# ----------------------------------------------------------------- the quoting domain covers correct alone (§10 Q4)
# Mutant killed: `disputed` left in the domain's trigger.

def _quoting(receipt):
    return SqliteStore.QUOTING_DOMAIN in receipt.receipt_domains


def test_q6_the_quoting_domain_is_absent_for_a_disputed_only_edge(tmp_path):
    m = _mem(tmp_path)
    eid = _remembered_edge(m)
    m.dispute(U, eid, reason="not true")
    assert not _quoting(m.redact(U, edge_id=eid, reason="subject_request"))


def test_q6_the_quoting_domain_still_fires_for_a_corrected_prior_and_its_replacement(tmp_path):
    m = _mem(tmp_path)
    eid = _remembered_edge(m)
    replacement = m.correct(U, eid, "ZQ-NEW")["replacement"]
    assert _quoting(m.redact(U, edge_id=eid, reason="subject_request"))
    assert _quoting(m.redact(U, edge_id=replacement, reason="subject_request"))


def test_q6_the_quoting_domain_reads_the_v16_5_text_verbatim():
    # §11.7.3 gives the string verbatim so two seats render one; mutant killed: the old (dispute/correct) string
    assert SqliteStore.QUOTING_DOMAIN == ("episodes quoting the record (correct summaries) — no exact list this round: "
                                          "the record was corrected, and the episode that says so quotes it")
