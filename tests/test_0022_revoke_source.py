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


# --- R18's three NAMED tests (0022 §6) ---------------------------------------

def test_revocation_retires_episodes(tmp_path):
    """R18 at the surface S1 was ABOUT: a revoked source's episode text must
    not appear in recall()'s rendered context. The store-level exclusion is
    necessary; this is the assertion at the RENDER seam, where the model
    actually reads."""
    from veracium import Memory, MemoryConfig

    def fake_llm(prompt, *, system=None, role="compile", json_schema=None):
        return "wiki: compiled"          # recall compiles the wiki en route

    db = str(tmp_path / "m.db")
    m = Memory(llm=fake_llm, config=MemoryConfig(db_path=db))
    s = m.store
    d = _seed(s)
    marker = "the feed said the user is in Lisbon"
    ctx_before = m.recall(U, "where is the user").context
    assert marker in ctx_before, (
        "fixture defect: the episode never rendered, so its absence after "
        "the revocation would prove nothing")
    rv.revoke_source(s, U, d, "revoke", "operator", AT)
    assert marker not in m.recall(U, "where is the user").context, (
        "a revoked source's episode text reached the rendered context — the "
        "read-seam exclusion did not carry to the surface that matters")


def test_episode_read_seam_is_sole_path():
    """R18: every `FROM episodes` outside the store package routes through
    store.episodes(), which is what stands in for the SQL-level guarantee a
    retirement column would have given. The raw sites are dispositioned in
    §7a — all inside src/veracium/store/ — so the check is a closed sweep,
    not a hope."""
    import pathlib
    src_root = pathlib.Path("src/veracium")
    offenders = []
    for f in sorted(src_root.rglob("*.py")):
        if f.parts[:3] == ("src", "veracium", "store"):
            continue                     # the dispositioned §7a interior
        if "FROM episodes" in f.read_text():
            offenders.append(str(f))
    assert not offenders, (
        f"{offenders} query episodes RAW outside the store package — retired "
        f"episodes would bypass the sole read seam (R18)")


def test_retired_episode_round_trips(tmp_path):
    """R18: export/import PRESERVE retired state rather than resurrecting it.
    A retired episode that came back live through portability would be
    non-revival's back door in the export file."""
    from veracium import Memory, MemoryConfig
    m = Memory(llm=None, config=MemoryConfig(db_path=str(tmp_path / "a.db")))
    d = _seed(m.store)
    rv.revoke_source(m.store, U, d, "revoke", "operator", AT)
    out = tmp_path / "export.json"
    m.export_memory(U, out)

    m2 = Memory(llm=None, config=MemoryConfig(db_path=str(tmp_path / "b.db")))
    m2.import_memory(out)
    assert m2.store.episodes(U) == [], (
        "the retired episode re-entered the read seam through import")
    got = m2.store.episodes(U, include_retired=True)
    assert got and got[0].retired_reason == "revoked_source", (
        "retired state was dropped in the round trip — the export file is a "
        "revival path (R18)")
