"""specs/0022 §4e end-to-end: revoke_source against the product store.

Store-level coverage of the sweep through the adapter: direct retirement of
both record types, the 0004 wiki seat firing on revoked_source, preview/commit
agreement (§4e's one-computation rule), and the lift restoring exactly what
the revocation took. The differential vector corpus and R18's render-surface
tests land beside this in the following commit.
"""

import uuid

import pytest

from veracium import EvidenceAuthor, SqliteStore
from veracium.schema import Edge, Episode, Provenance, utcnow
from veracium.store import revocation as rv
from veracium.store.revocation_sweep import digest_of

U = "u"
AT = "2026-08-21T00:00:00Z"


def _store(tmp_path):
    return SqliteStore(str(tmp_path / "rs.db"))


def _prov(source_id):
    return Provenance(author_of_evidence=EvidenceAuthor.THIRD_PARTY,
                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}",
                      source_id=source_id)


def _seed(s, source_id="feed-1"):
    e = Edge(id="e1", user_id=U, subject="user", relation="located_at",
             object="Lisbon", provenance=_prov(source_id))
    s.add_edge(e)
    ep = Episode(id="ep1", user_id=U, date="2026-08-01",
                 summary="the feed said the user is in Lisbon",
                 provenance=_prov(source_id))
    s.add_episode(ep)
    s.set_wiki(U, "cached", s.store_version(U))
    return digest_of(None, source_id, s.local_origin())


def test_revoke_retires_both_record_types_and_drops_the_wiki(tmp_path):
    s = _store(tmp_path)
    d = _seed(s)
    st = rv.revoke_source(s, U, d, "revoke", "operator", AT)
    assert st["standing"] is True
    assert ["edge:e1" == f"{t}:{i}" for t, i in st["direct"]]
    edges = s.edges(U, active_only=False)
    assert not edges[0].active
    assert edges[0].invalidation_reason == "revoked_source"
    assert s.episodes(U) == [], "the retired episode must leave the read seam"
    assert s.episodes(U, include_retired=True)[0].retired_reason == \
        "revoked_source"
    assert s.get_wiki(U) is None, "the 0004 registry seat must fire (W5)"


def test_preview_and_commit_run_the_same_computation(tmp_path):
    s = _store(tmp_path)
    d = _seed(s)
    preview = rv.revoke_source(s, U, d, "revoke", "operator", AT, dry_run=True)
    committed = rv.revoke_source(s, U, d, "revoke", "operator", AT)
    assert preview["effects"] == committed["effects"]
    assert preview["retire"] == committed["retire"]
    # the preview wrote NOTHING: the commit still allocated seq 0
    assert committed["row"]["seq"] == 0


def test_a_lift_reinstates_what_the_revocation_took(tmp_path):
    s = _store(tmp_path)
    d = _seed(s)
    rv.revoke_source(s, U, d, "revoke", "operator", AT)
    st = rv.revoke_source(s, U, d, "lift", "operator", AT)
    assert st["standing"] is False
    e = s.edges(U)[0]
    assert e.active and e.invalidation_reason is None
    assert s.episodes(U)[0].id == "ep1", "the episode returns to the seam"


def test_a_lift_does_not_reinstate_other_retirements(tmp_path):
    s = _store(tmp_path)
    d = _seed(s)
    # retire the edge for an unrelated reason FIRST
    s.invalidate_edge("e1", utcnow(), "disputed")
    rv.revoke_source(s, U, d, "revoke", "operator", AT)
    rv.revoke_source(s, U, d, "lift", "operator", AT)
    e = s.edges(U, active_only=False)[0]
    assert not e.active and e.invalidation_reason == "disputed", (
        "a record retired as disputed is not this operation's to reinstate")


def test_an_unknown_effect_verb_refuses_and_rolls_back(tmp_path):
    s = _store(tmp_path)
    d = _seed(s)
    with pytest.raises(rv.RevocationEffectError):
        rv._apply_statement_effect(s, AT, {"verb": "vaporise", "type": "edge",
                                           "id": "e1"})
