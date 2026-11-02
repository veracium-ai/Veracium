"""specs/0022 §4g / §7a: the host API — `Memory.revoke_source`, `unrevoke_source`, `source_revocations`.

Promised by the accepted spec's public-surface inventory and never shipped until 0.30.0 (found 2026-10-28 answering
marketing's Scan #16 questions): the store-level machinery (`store.revocation.revoke_source`) has shipped since
v0.13.0, and these cells hold the host methods to it. Each cell attacks one property the methods' names and
docstrings claim: the digest is the store's resolved identity (origin None = this store's own records), a preview is
the commit's own statement and writes nothing, a lift reverses by recomputation, the audit view is in append order,
the audit event is content-free and one per committed operation, refusals write nothing, and a revocation is per
user.
"""

import hashlib
import json
import sqlite3
import uuid

import pytest

from veracium import EvidenceAuthor, Memory, MemoryConfig
from veracium.audit import AuditLog
from veracium.schema import Edge, Episode, Provenance
from veracium.store import revocation as rv
from veracium.store.revocation_sweep import digest_of

U, V = "u", "v"
AUDIT_FIELDS = {"identity_digest", "action", "complete", "class_a_linked", "class_b_linkless",
                "class_c_unattributed", "retired", "retired_synthesized", "recomputed", "reinstated"}


def _mem(tmp_path, audit=True):
    m = Memory(config=MemoryConfig(db_path=str(tmp_path / "m.db")), llm=None)
    if audit:
        m.audit = AuditLog(tmp_path / "audit.jsonl")
    return m


def _prov(source_id, origin=None):
    return Provenance(author_of_evidence=EvidenceAuthor.THIRD_PARTY, evidence_ref=f"ev-{uuid.uuid4().hex[:6]}",
                      source_id=source_id, origin=origin)


def _seed(m, user=U, source_id="feed-1", origin=None, tag="1"):
    m.store.add_edge(Edge(id=f"e{tag}-{user}", user_id=user, subject="user", relation="located_at",
                          object="Lisbon", provenance=_prov(source_id, origin)))
    m.store.add_episode(Episode(id=f"ep{tag}-{user}", user_id=user, date="2026-08-01",
                                summary="the feed said the user is in Lisbon",
                                provenance=_prov(source_id, origin)))


def _db_bytes(m):
    """Every table's rows, ordered — the store's state, independent of page layout."""
    conn = sqlite3.connect(m.config.db_path)
    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {t: conn.execute(f'SELECT * FROM "{t}" ORDER BY 1').fetchall() for t in tables}
    finally:
        conn.close()


def _events(m, op=None):
    return m.audit.entries(op=op) if op else [e for e in m.audit.entries()
                                              if e["op"] in ("revoke_source", "unrevoke_source")]


def test_revoke_retires_both_record_types_and_lift_restores_them(tmp_path):
    m = _mem(tmp_path)
    _seed(m)
    st = m.revoke_source(U, None, "feed-1", "policy")
    assert st["standing"] is True and st["complete"] is True
    (edge,) = m.store.edges(U, active_only=False)
    assert not edge.active and edge.invalidation_reason == "revoked_source"
    assert m.store.episodes(U) == []
    lifted = m.unrevoke_source(U, None, "feed-1", "subject_request")
    assert lifted["standing"] is False
    (edge,) = m.store.edges(U, active_only=False)
    assert edge.active, "a lift with no other standing revocation reinstates the record"
    assert [ep.id for ep in m.store.episodes(U)] == ["ep1-u"]


def test_the_digest_is_the_stores_resolved_identity(tmp_path):
    """origin=None is THIS store's origin (0006 §4 rule 6): the statement targets digest_of(None, …, local_origin),
    and passing the local origin explicitly is the same identity, not a second one."""
    m = _mem(tmp_path)
    _seed(m)
    local = m.store.local_origin()
    want = digest_of(None, "feed-1", local)
    assert m.revoke_source(U, None, "feed-1", "policy", dry_run=True)["target"] == want
    assert m.revoke_source(U, local, "feed-1", "policy", dry_run=True)["target"] == want
    # a foreign origin is a different identity: it does not reach the local record
    st = m.revoke_source(U, "origin-elsewhere", "feed-1", "policy")
    assert st["target"] != want and st["affected"] == []
    assert all(e.active for e in m.store.edges(U, active_only=False))


def test_a_foreign_record_is_revoked_by_its_own_origin(tmp_path):
    m = _mem(tmp_path)
    _seed(m, origin="origin-elsewhere", tag="f")
    _seed(m, tag="l")
    m.revoke_source(U, "origin-elsewhere", "feed-1", "policy")
    by_id = {e.id: e.active for e in m.store.edges(U, active_only=False)}
    assert by_id == {"ef-u": False, "el-u": True}


def test_preview_is_the_commits_statement_and_writes_nothing(tmp_path):
    m = _mem(tmp_path)
    _seed(m)
    before = _db_bytes(m)
    preview = m.revoke_source(U, None, "feed-1", "policy", dry_run=True)
    assert _db_bytes(m) == before, "a preview must write nothing"
    assert _events(m) == [], "a preview is not a revocation: no audit event"
    committed = m.revoke_source(U, None, "feed-1", "policy")
    strip = lambda s: {k: v for k, v in s.items() if k != "row"}
    assert strip(committed) == strip(preview), "§4e: preview and commit run ONE computation"
    assert committed["row"]["action"] == preview["row"]["action"] == "revoke"
    assert committed["row"]["identity_digest"] == preview["row"]["identity_digest"]


@pytest.mark.parametrize("dry_run", [1, "yes", None])
def test_dry_run_must_be_a_bool(tmp_path, dry_run):
    """A truthy non-bool must not silently commit (or preview): it is refused, and nothing is written."""
    m = _mem(tmp_path)
    _seed(m)
    before = _db_bytes(m)
    with pytest.raises(TypeError):
        m.revoke_source(U, None, "feed-1", "policy", dry_run=dry_run)
    assert _db_bytes(m) == before


def test_source_revocations_is_the_standing_set_and_the_history_in_append_order(tmp_path):
    m = _mem(tmp_path)
    _seed(m)
    _seed(m, source_id="feed-2", tag="2")
    d1, d2 = (digest_of(None, s, m.store.local_origin()) for s in ("feed-1", "feed-2"))
    assert m.source_revocations(U) == {"standing": [], "history": []}
    _seed(m, source_id="feed-3", tag="3")
    d3 = digest_of(None, "feed-3", m.store.local_origin())
    m.revoke_source(U, None, "feed-2", "policy")
    m.revoke_source(U, None, "feed-3", "legal_obligation")
    m.revoke_source(U, None, "feed-1", "subject_request")
    assert m.source_revocations(U)["standing"] == sorted([d1, d2, d3]), "standing is the sorted digest list"
    m.unrevoke_source(U, None, "feed-2", "policy")
    view = m.source_revocations(U)
    assert view["standing"] == sorted([d1, d3])
    assert [(h["seq"], h["identity_digest"], h["action"], h["reason"]) for h in view["history"]] == [
        (0, d2, "revoke", "policy"), (1, d3, "revoke", "legal_obligation"), (2, d1, "revoke", "subject_request"),
        (3, d2, "lift", "policy")]
    assert all(set(h) == {"seq", "identity_digest", "action", "at", "reason"} for h in view["history"])
    assert m.source_revocations(V) == {"standing": [], "history": []}, "the view is per user"


def test_standing_is_sorted_whatever_the_set_order(tmp_path):
    """`standing` is a sorted list, not a set's iteration order: eight digests, so an unsorted list passing by chance is
    ~1 in 40,000 (three could pass 1 in 6, by string-hash order)."""
    m = _mem(tmp_path)
    srcs = [f"feed-{i}" for i in range(8)]
    for i, s in enumerate(srcs):
        _seed(m, source_id=s, tag=f"s{i}")
        m.revoke_source(U, None, s, "policy")
    want = sorted(digest_of(None, s, m.store.local_origin()) for s in srcs)
    assert m.source_revocations(U)["standing"] == want


def test_a_revocation_is_per_user(tmp_path):
    m = _mem(tmp_path)
    _seed(m, user=U)
    _seed(m, user=V)
    m.revoke_source(U, None, "feed-1", "policy")
    assert not m.store.edges(U, active_only=False)[0].active
    assert m.store.edges(V, active_only=False)[0].active, "another user's record from the same source is untouched"
    assert m.source_revocations(V)["standing"] == []


@pytest.mark.parametrize("call,kwargs,exc", [
    ("revoke_source", dict(source_id="feed-1", reason="revoked_in_error"), ValueError),  # a lift reason on a revoke
    ("revoke_source", dict(source_id="feed-1", reason=""), ValueError),
    ("revoke_source", dict(source_id="feed-1", reason="because I said so"), ValueError),
    ("unrevoke_source", dict(source_id="feed-1", reason="erroneous_capture"), ValueError),  # a revoke-only reason
    ("revoke_source", dict(source_id="x" * 10_000, reason="policy"), Exception),  # past the shipped bound
])
def test_a_refusal_writes_nothing_and_audits_nothing(tmp_path, call, kwargs, exc):
    m = _mem(tmp_path)
    _seed(m)
    before = _db_bytes(m)
    with pytest.raises(exc):
        getattr(m, call)(U, None, **kwargs)
    assert _db_bytes(m) == before
    assert _events(m) == []


@pytest.mark.parametrize("call", ["revoke_source", "unrevoke_source"])
def test_a_source_with_no_identity_is_refused_by_name(tmp_path, call):
    """source_id=None has no digest (0006's absence rule): refused at the host method, naming why, and nothing
    is written — not left to whatever the store does with a None target."""
    m = _mem(tmp_path)
    _seed(m)
    before = _db_bytes(m)
    with pytest.raises(ValueError, match="no source identity"):
        getattr(m, call)(U, None, None, "policy")
    assert _db_bytes(m) == before
    assert _events(m) == []


def test_one_content_free_audit_event_per_committed_operation(tmp_path):
    m = _mem(tmp_path)
    _seed(m)
    d = digest_of(None, "feed-1", m.store.local_origin())
    m.revoke_source(U, None, "feed-1", "subject_request")
    m.unrevoke_source(U, None, "feed-1", "subject_request")
    rev, lift = _events(m)
    assert (rev["op"], lift["op"]) == ("revoke_source", "unrevoke_source")
    for ev, action in ((rev, "revoke"), (lift, "lift")):
        assert set(ev) - {"ts", "op", "user_id"} == AUDIT_FIELDS, sorted(ev)
        assert ev["identity_digest"] == d and ev["action"] == action and ev["user_id"] == U
        assert all(isinstance(ev[k], int) and not isinstance(ev[k], bool)
                   for k in AUDIT_FIELDS - {"identity_digest", "action", "complete"})
        assert isinstance(ev["complete"], bool)
    assert (rev["retired"], rev["reinstated"]) == (2, 0)
    assert (lift["retired"], lift["reinstated"]) == (0, 2)
    text = json.dumps(_events(m))
    for content in ("Lisbon", "feed-1", "subject_request", "e1-u", "ep1-u"):
        assert content not in text, f"{content!r} reached the audit event"


def test_telemetry_never_carries_the_revocation_event(tmp_path):
    """The event is audit-only: telemetry's whitelist has no entry for it, so a consented aggregate never counts it
    (0017's schema is unchanged)."""
    from veracium.telemetry import EVENT_FIELDS
    assert "revoke_source" not in EVENT_FIELDS and "unrevoke_source" not in EVENT_FIELDS


def test_no_audit_sink_is_not_an_error(tmp_path):
    m = _mem(tmp_path, audit=False)
    _seed(m)
    assert m.revoke_source(U, None, "feed-1", "policy")["standing"] is True


def test_a_store_without_revocation_support_refuses_loudly(tmp_path):
    m = _mem(tmp_path)

    class Other:  # stands in for a non-SqliteStore backend
        pass

    m.store = Other()
    for call in (lambda: m.revoke_source(U, None, "feed-1", "policy"),
                 lambda: m.unrevoke_source(U, None, "feed-1", "policy"),
                 lambda: m.source_revocations(U)):
        with pytest.raises(NotImplementedError):
            call()


def test_a_retired_consolidation_summary_is_counted_as_synthesized(tmp_path):
    """§4c's split, in the audit event as in the statement: a consolidation summary is SYNTHESIZED (its text was
    written over its contributor set). Consolidation pools by source identity (0021 §4b), so each source gets its own
    summary; revoking feed-1 retires feed-1's summary and leaves feed-2's, and the event's `retired_synthesized`
    counts it (a sole-basis retirement would count in `retired` alone)."""
    from datetime import datetime, timedelta, timezone
    from veracium.lifecycle import consolidate
    from veracium.store.revocation_sweep import KIND_SYNTHESIZED
    m = _mem(tmp_path)
    old = datetime.now(timezone.utc) - timedelta(days=90)
    for i in range(8):
        m.store.add_episode(Episode(
            id=f"c{i}", user_id=U, date=old.date().isoformat(), summary=f"s{i}",
            provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=f"event-{i}",
                                  observed_at=old, source_id="feed-1" if i < 4 else "feed-2")))
    consolidate(m.store, lambda *a, **k: json.dumps({"records": [{"date": old.date().isoformat(), "summary": "S"}]}),
                U, MemoryConfig(consolidate_after_days=30, consolidate_min_batch=4))
    summaries = [e for e in m.store.episodes(U) if e.id.startswith("epc")]
    assert len(summaries) == 2, [e.id for e in m.store.episodes(U)]
    _seed(m, tag="sole")  # an edge and an episode resting on feed-1 alone: sole-basis, not synthesized
    st = m.revoke_source(U, None, "feed-1", "policy")
    # a summary carries no source_id of its own (the system wrote it): the sweep's ledger walk names which one rests
    # on feed-1, and exactly one of the two does
    hit = [e for e in summaries if f"episode:{e.id}" in st["kinds"]]
    assert len(hit) == 1, (st["kinds"], [e.id for e in summaries])
    assert st["kinds"][f"episode:{hit[0].id}"] == KIND_SYNTHESIZED, st["kinds"]
    retired_synth = [e for e in st["effects"] if e["verb"] == "retire"
                     and st["kinds"].get(f"{e['type']}:{e['id']}") == KIND_SYNTHESIZED]
    assert [f"{e['type']}:{e['id']}" for e in retired_synth] == [f"episode:{hit[0].id}"]
    (ev,) = _events(m)
    assert ev["retired_synthesized"] == 1
    # consolidation already retired the summary's four inputs; the retired set is the summary plus the sole-basis
    # edge and episode, and only the summary counts as synthesized
    retired_all = sorted(f"{e['type']}:{e['id']}" for e in st["effects"] if e["verb"] == "retire")
    assert retired_all == sorted([f"episode:{hit[0].id}", "edge:esole-u", "episode:epsole-u"]), retired_all
    assert (ev["retired"], ev["retired_synthesized"]) == (3, 1)
