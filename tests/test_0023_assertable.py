"""specs/0023 §4a-iv — Episode's derived properties (Slice C1).

The shared predicate exists before its consumers rewire (the next slice), the
same order Slice A/B landed in: the property's own contract is pinned here;
N14/N15 pin the consumption."""

import uuid

from veracium import EvidenceAuthor
from veracium.schema import Disclosure, Episode, Provenance, utcnow


def _ep(disclosure=Disclosure.MENTIONABLE, retired=None,
        author=EvidenceAuthor.USER, derived=None):
    return Episode(
        id=f"ep-{uuid.uuid4().hex[:6]}", user_id="u", date="2026-08-01",
        summary="s", retired_reason=retired,
        retired_at=(utcnow() if retired else None),
        provenance=Provenance(author_of_evidence=author, derived_from=derived,
                              evidence_ref="ev", disclosure=disclosure))


def test_the_derived_matrix_is_total():
    """Every (disclosure, retired) cell, against the §4a-iv rule — derived,
    never stored, so there is no second copy to drift."""
    for disclosure in Disclosure:
        for retired in (None, "revoked_source"):
            for author, derived in [
                    (EvidenceAuthor.USER, None),
                    (EvidenceAuthor.THIRD_PARTY, None),          # legacy tp
                    (EvidenceAuthor.SYSTEM, EvidenceAuthor.THIRD_PARTY)]:
                ep = _ep(disclosure, retired, author, derived)
                tp = ep.provenance.third_party_influenced
                assert ep.active is (retired is None)
                assert ep.quarantined is (disclosure == Disclosure.QUARANTINED)
                # use_only SUBSUMES the legacy signal: pre-0023 rows carry the
                # default disclosure, and the floor of both carriers is what
                # keeps them fenced (S3)
                assert ep.use_only is (
                    disclosure == Disclosure.USE_ONLY or tp)
                assert ep.assertable is (
                    retired is None
                    and disclosure not in (Disclosure.QUARANTINED,
                                           Disclosure.USE_ONLY)
                    and not tp), (
                    f"assertable wrong at ({disclosure}, {retired!r}, "
                    f"{author}, derived={derived})")


def test_nothing_stores_the_derived_values():
    """The properties are DERIVED: they must not appear in the serialized
    record, or a second source of truth exists (§4a point 1)."""
    import json
    blob = json.loads(_ep().model_dump_json())
    for field in ("quarantined", "assertable", "use_only", "active"):
        assert field not in blob, (
            f"{field} is serialized — a stored copy of a derived value")


def test_render_split_runs_on_the_shared_predicate():
    """N14, at the surface F1 was about. The assertable episode renders in
    ordinary detail; the quarantined one is FENCED, NOT SUPPRESSED (Q5 —
    suppression would make episodes stricter than shipped edge behaviour
    under one rule), and the fenced section follows ordinary detail."""
    import tempfile
    from veracium import Memory, MemoryConfig

    def fake_llm(prompt, *, system=None, role="compile", json_schema=None):
        return "wiki: compiled"

    d = tempfile.mkdtemp()
    m = Memory(llm=fake_llm, config=MemoryConfig(db_path=f"{d}/m.db"))
    q = _ep(Disclosure.QUARANTINED); q.summary = "CLAIMED-BY-FEED"
    g = _ep(); g.summary = "USER-SAID-SO"
    m.store.add_episode(q); m.store.add_episode(g)
    ctx = m.recall("u", "what happened").context
    assert "USER-SAID-SO" in ctx
    assert "CLAIMED-BY-FEED" in ctx, (
        "the quarantined episode VANISHED — Q5 requires fencing, not "
        "suppression")
    # and the fenced text sits under the unverified/reported section, after
    # the ordinary detail that carries the grounded episode
    assert ctx.index("USER-SAID-SO") < ctx.index("CLAIMED-BY-FEED"), (
        "the fenced episode rendered before ordinary detail — the sections "
        "are inverted or the split did not run on the predicate")
