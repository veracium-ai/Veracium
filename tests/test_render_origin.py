"""Unverified material must never carry a confidently wrong origin.

`render_edges` used to hardcode `[third-party-reported; unconfirmed]` for every
`use_only` edge, keyed on the disclosure tier rather than on who actually
authored it. That is correct for every author reachable today, and it was a
landmine for the next one: spec 0001 proposes `EvidenceAuthor.ASSISTANT` held at
`use_only`, and the hardcoded string would have told the model
"third-party-reported" about assistant-generated text — an affirmatively false
origin, in the release whose whole purpose is stopping hosts from mislabelling
assistant content.

**A confidently wrong provenance label is worse than a missing one**, because
the model has no way to discount it.

These tests are the tripwire. `test_every_author_reaching_use_only_has_a_label`
fails the moment a new `EvidenceAuthor` member exists without a deliberate
origin string — so the gate is enforced by CI rather than remembered from a
deferred spec.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from veracium.graph import _ORIGIN_LABELS, _origin_label, render_edges
from veracium.schema import (Disclosure, Edge, EvidenceAuthor, Provenance,
                             SourceType)

NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def _edge(author, derived=None, disclosure=Disclosure.USE_ONLY):
    return Edge(id="e1", user_id="u", subject="user", relation="owes",
                object="500 to Acme", valid_from=NOW, active=True,
                provenance=Provenance(source_type=SourceType.INFERRED,
                                      author_of_evidence=author,
                                      evidence_ref="r", derived_from=derived,
                                      disclosure=disclosure, observed_at=NOW))


def test_every_author_reaching_use_only_has_a_label():
    """The tripwire. Adding an EvidenceAuthor member without an origin string
    must fail here, not surface as a false label in model context."""
    missing = [a for a in EvidenceAuthor if a not in _ORIGIN_LABELS]
    assert not missing, (
        f"{[a.value for a in missing]} has no entry in _ORIGIN_LABELS. Any "
        f"author that can reach use_only needs a deliberate origin string — "
        f"see spec 0001 §12 (the v3 render gate). Do not let it inherit "
        f"another class's label.")


def test_an_unlabelled_author_fails_safe_rather_than_confidently():
    """Belt and braces: if the tripwire is ever bypassed, the fallback must not
    borrow a wrong-but-plausible origin."""
    class _Fake(str):
        pass
    e = _edge(EvidenceAuthor.THIRD_PARTY)
    object.__setattr__(e.provenance, "author_of_evidence", _Fake("brand_new"))
    assert _origin_label(e) == "unverified-origin"
    assert "third-party" not in _origin_label(e)


@pytest.mark.parametrize("author,derived", [
    (EvidenceAuthor.THIRD_PARTY, None),
    (EvidenceAuthor.USER, EvidenceAuthor.THIRD_PARTY),
    (EvidenceAuthor.SYSTEM, EvidenceAuthor.THIRD_PARTY),
])
def test_output_is_unchanged_for_every_author_reachable_today(author, derived):
    """This refactor is behaviour-preserving. Rendered text IS model context, so
    'byte-identical' is the requirement, not 'equivalent'."""
    out = render_edges([_edge(author, derived)])
    assert out == ("owes: 500 to Acme (since 2026-08-01) "
                   "[third-party-reported; unconfirmed]")


def test_mentionable_edges_carry_no_origin_marker():
    out = render_edges([_edge(EvidenceAuthor.USER, disclosure=Disclosure.MENTIONABLE)])
    assert "unconfirmed" not in out and "third-party" not in out
