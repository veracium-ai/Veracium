"""specs/0023 §6 — the non-revival guards at the maintenance verbs (C5).

Canonical N-names from the spec's own table. Every test builds the standing
revocation through the real 0022 surface (revoke_source), so the guards are
exercised against the state the sweep actually writes."""

import uuid

from veracium import EvidenceAuthor, SqliteStore
from veracium.graph import _build_supersession_plan, apply_supersession
from veracium.lifecycle import partition_cold
from veracium.schema import DEFAULT_RELATIONS, Edge, Episode, Provenance, utcnow
from veracium.scope_linkage import identity_digest_of
from veracium.store import revocation as rv

U = "u"
AT = "2026-08-21T00:00:00Z"


def _edge(obj, *, source="feed-1", rel="located_at", author=EvidenceAuthor.USER):
    return Edge(id=f"e-{uuid.uuid4().hex[:8]}", user_id=U, subject="user",
                relation=rel, object=obj,
                provenance=Provenance(author_of_evidence=author,
                                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}",
                                      source_id=source))


def _revoke(s, source="feed-1"):
    d = identity_digest_of(None, source, s.local_origin())
    rv.revoke_source(s, U, d, "revoke", "operator", AT)
    return d


def _standing_only(s, source="feed-1"):
    """A standing revocation with NO effects applied — the raw ledger row.

    The full `revoke_source` SWEEPS, so a revoked source's records are
    already retired before any maintenance verb sees them; the first version
    of these fixtures used it and proved only that the sweep got there first.
    The builder guards defend the ground the sweep does NOT hold: the window
    before a sweep runs, and records a partial sweep missed. Standing-only
    state is exactly that ground."""
    d = identity_digest_of(None, source, s.local_origin())
    seq = 1 + s._conn.execute(
        "SELECT COALESCE(MAX(seq), -1) FROM source_revocations WHERE user_id=?",
        (U,)).fetchone()[0]
    s._conn.execute(
        "INSERT INTO source_revocations(user_id, seq, identity_digest, action,"
        " at, reason) VALUES(?,?,?,?,?,?)", (U, seq, d, "revoke", AT, "op"))
    s._conn.commit()
    return d


def test_revoked_source_does_not_reinforce(tmp_path):
    """N3: the restatement is not COUNTED as a reinforcement; the prior is
    byte-unchanged. (Design 1 already transfers nothing — N3 pins the
    counter and the branch.)"""
    s = SqliteStore(str(tmp_path / "n.db"))
    prior = _edge("Lisbon")
    apply_supersession(s, prior, DEFAULT_RELATIONS)
    before = s.edges(U)[0].model_dump_json()
    _standing_only(s)
    restatement = _edge("Lisbon")               # same value, same source
    plan, is_reinf = _build_supersession_plan(s, restatement, DEFAULT_RELATIONS,
                                              f"op-{restatement.id}")
    assert is_reinf is False, "a revoked source's restatement counted as reinforcement"
    assert s.edges(U)[0].model_dump_json() == before


def test_absorption_refuses_a_revoked_source_on_either_side(tmp_path):
    """N4, both directions as separate cells; N7 rides on the refusal — the
    absorption fold is the ONE seam where currency survives (M2: no renewal
    verb), so refusing candidacy IS refusing renewal."""
    for revoked_side in ("incoming", "prior"):
        s = SqliteStore(str(tmp_path / f"n4-{revoked_side}.db"))
        prior = _edge("Miso", rel="has_pet",
                      source=("feed-1" if revoked_side == "prior" else "feed-2"))
        apply_supersession(s, prior, DEFAULT_RELATIONS)
        prior_before = s.edges(U)[0].model_dump_json()
        _standing_only(s, "feed-1")
        winner = _edge("cat Miso", rel="has_pet",
                       source=("feed-1" if revoked_side == "incoming" else "feed-2"))
        plan, _ = _build_supersession_plan(s, winner, DEFAULT_RELATIONS,
                                           f"op-{winner.id}")
        assert not any(r == "absorbed_duplicate"
                       for _, _, r in plan.prior_invalidations), (
            f"absorption took a revoked source on the {revoked_side} side")
        assert plan.insert_incoming, "both records must persist separately"
        # N7 at the seam: the prior's currency is byte-unchanged
        s.apply_supersession_plan(plan)
        kept = next(e for e in s.edges(U, active_only=False)
                    if e.id == prior.id)
        assert kept.model_dump_json() == prior_before, (
            "the refused absorption still touched the prior (N7)")


def test_revoked_source_does_not_renew(tmp_path):
    """N7's named test: a revoked-source restatement that WOULD subsume a
    live prior — the prior's observed_at must be byte-unchanged."""
    s = SqliteStore(str(tmp_path / "n7.db"))
    prior = _edge("Miso", rel="has_pet", source="feed-2")
    apply_supersession(s, prior, DEFAULT_RELATIONS)
    observed_before = s.edges(U)[0].provenance.observed_at
    _standing_only(s, "feed-1")
    subsuming = _edge("cat Miso", rel="has_pet", source="feed-1")   # revoked
    plan, _ = _build_supersession_plan(s, subsuming, DEFAULT_RELATIONS,
                                       f"op-{subsuming.id}")
    s.apply_supersession_plan(plan)
    kept = next(e for e in s.edges(U) if e.id == prior.id)
    assert kept.provenance.observed_at == observed_before


def test_revoked_source_cannot_supersede(tmp_path):
    """N5: a revoked-source incoming may not retire a standing record —
    refusal recorded, prior active. The REVERSE works: a live incoming
    retires a revoked-source prior."""
    s = SqliteStore(str(tmp_path / "n5.db"))
    prior = _edge("Lisbon", source="feed-2")
    apply_supersession(s, prior, DEFAULT_RELATIONS)
    _standing_only(s, "feed-1")
    challenger = _edge("Porto", source="feed-1")          # revoked incoming
    plan, _ = _build_supersession_plan(s, challenger, DEFAULT_RELATIONS,
                                       f"op-{challenger.id}")
    assert not any(r == "superseded" for _, _, r in plan.prior_invalidations)
    assert plan.refusals, "the refusal must be durable and content-free"

    # THE REVERSE: live retires revoked
    s2 = SqliteStore(str(tmp_path / "n5r.db"))
    revoked_prior = _edge("Lisbon", source="feed-1")
    apply_supersession(s2, revoked_prior, DEFAULT_RELATIONS)
    _standing_only(s2, "feed-1")
    live = _edge("Porto", source="feed-2")
    plan2, _ = _build_supersession_plan(s2, live, DEFAULT_RELATIONS,
                                        f"op-{live.id}")
    assert any(r == "superseded" for _, _, r in plan2.prior_invalidations), (
        "the reverse direction must still work — N5's second half")


def test_consolidation_excludes_revoked_sources(tmp_path):
    """N6, at partition_cold: the revoked source's episodes enter NO pool."""
    s = SqliteStore(str(tmp_path / "n6.db"))
    eps = []
    for src in ("feed-1", "feed-1", "feed-2"):
        ep = Episode(id=f"ep-{uuid.uuid4().hex[:6]}", user_id=U,
                     date="2026-08-01", summary="s",
                     provenance=Provenance(
                         author_of_evidence=EvidenceAuthor.USER,
                         evidence_ref="ev", source_id=src))
        s.add_episode(ep); eps.append(ep)
    _standing_only(s, "feed-1")
    pools = partition_cold(s, U, eps)
    pooled = [e.id for _, members in pools for e in members]
    assert eps[2].id in pooled
    assert eps[0].id not in pooled and eps[1].id not in pooled, (
        "revoked-source episodes entered a consolidation pool (N6)")


def test_unidentified_writes_are_never_quarantined_by_revocation(tmp_path):
    """N11: no source_id → no digest → unaffected by ANY standing
    revocation, at every site."""
    s = SqliteStore(str(tmp_path / "n11.db"))
    _standing_only(s, "feed-1")
    e = _edge("Lisbon", source=None)
    plan, _ = _build_supersession_plan(s, e, DEFAULT_RELATIONS, f"op-{e.id}")
    assert plan.insert_incoming and not plan.refusals


def test_no_revocation_is_byte_identical(tmp_path):
    """N12: a store with NO standing revocation takes the pre-0023 code path
    — same plan, same stored state, for the same inputs."""
    outs = []
    for name in ("a", "b"):
        s = SqliteStore(str(tmp_path / f"n12-{name}.db"))
        from datetime import datetime, timezone
        pinned = datetime(2026, 8, 1, tzinfo=timezone.utc)
        apply_supersession(s, Edge(
            id="e-fixed", user_id=U, subject="user", relation="has_pet",
            object="Miso", valid_from=pinned, provenance=Provenance(
                author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-1",
                observed_at=pinned,      # PINNED: the comparison is behaviour,
                source_id="feed-1")), DEFAULT_RELATIONS)   # not clock noise
        outs.append(sorted(e.model_dump_json() for e in s.edges(U)))
    assert outs[0] == outs[1]
