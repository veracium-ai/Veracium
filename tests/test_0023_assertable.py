"""specs/0023 §4a-iv — Episode's derived properties (Slice C1).

The shared predicate exists before its consumers rewire (the next slice), the
same order Slice A/B landed in: the property's own contract is pinned here;
N14/N15 pin the consumption."""

import uuid

from veracium import EvidenceAuthor
from veracium.schema import Disclosure, Episode, Provenance, utcnow


def _ep(disclosure=Disclosure.MENTIONABLE, retired=None):
    return Episode(
        id=f"ep-{uuid.uuid4().hex[:6]}", user_id="u", date="2026-08-01",
        summary="s", retired_reason=retired,
        retired_at=(utcnow() if retired else None),
        provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                              evidence_ref="ev", disclosure=disclosure))


def test_the_derived_matrix_is_total():
    """Every (disclosure, retired) cell, against the §4a-iv rule — derived,
    never stored, so there is no second copy to drift."""
    for disclosure in Disclosure:
        for retired in (None, "revoked_source"):
            ep = _ep(disclosure, retired)
            assert ep.active is (retired is None)
            assert ep.quarantined is (disclosure == Disclosure.QUARANTINED)
            assert ep.use_only is (disclosure == Disclosure.USE_ONLY)
            assert ep.assertable is (
                retired is None
                and disclosure not in (Disclosure.QUARANTINED,
                                       Disclosure.USE_ONLY)), (
                f"assertable wrong at ({disclosure}, retired={retired!r})")


def test_nothing_stores_the_derived_values():
    """The properties are DERIVED: they must not appear in the serialized
    record, or a second source of truth exists (§4a point 1)."""
    import json
    blob = json.loads(_ep().model_dump_json())
    for field in ("quarantined", "assertable", "use_only", "active"):
        assert field not in blob, (
            f"{field} is serialized — a stored copy of a derived value")
