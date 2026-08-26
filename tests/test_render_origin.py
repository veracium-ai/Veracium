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
from veracium.schema import Disclosure, Edge, EvidenceAuthor, Provenance

NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def _edge(author, derived=None, disclosure=Disclosure.USE_ONLY):
    return Edge(id="e1", user_id="u", subject="user", relation="owes",
                object="500 to Acme", valid_from=NOW, active=True,
                provenance=Provenance(author_of_evidence=author,
                                      evidence_ref="r", derived_from=derived,
                                      disclosure=disclosure, observed_at=NOW))


def _expected_label(author, derived):
    """0001 §4b's decision order, written INDEPENDENTLY of the implementation
    it checks — the capping axis first, then the author class.

    This is an oracle, not a mirror: it is derived from the spec's prose and
    is deliberately a different shape from `_origin_label`, so agreement
    between them is evidence rather than tautology.
    """
    if derived is EvidenceAuthor.THIRD_PARTY:
        return "third-party-derived"        # relayed claim — the cap wins
    if author is EvidenceAuthor.THIRD_PARTY:
        return "third-party-reported"
    if author is EvidenceAuthor.ASSISTANT:
        return "assistant-generated"
    return "unverified-origin"              # deliberately unlabelled


def test_every_author_reaching_use_only_has_a_deliberate_label():
    """The tripwire, over the WHOLE domain rather than one axis of it.

    0001 I12 made the label PAIR-keyed (author × derived_from), so asking
    whether each author appears in `_ORIGIN_LABELS` no longer answers the
    question — `USER` and `SYSTEM` deliberately have no entry now, because
    inheriting another class's string is exactly the failure this file
    exists to prevent, and their label comes from the fail-safe instead.
    Membership in a dict was a PROXY for "has a deliberate label"; under
    pair-keying the proxy reads false for cells that are correct.

    So the matrix is enumerated: every author against every derivation,
    compared to an independently written oracle. Enumeration has no cell
    to overlook, and a new `EvidenceAuthor` member enters the
    cross-product automatically — which is the tripwire the old test was
    for, now armed on both axes.
    """
    derivations = [None] + list(EvidenceAuthor)
    wrong = []
    for author in EvidenceAuthor:
        for derived in derivations:
            got = _origin_label(_edge(author, derived))
            want = _expected_label(author, derived)
            if got != want:
                wrong.append(f"({author.value}, "
                             f"{derived.value if derived else None}): "
                             f"got {got!r}, §4b says {want!r}")
    assert not wrong, (
        "the rendered origin disagrees with 0001 §4b's decision order at "
        + str(len(wrong)) + " cell(s):\n  " + "\n  ".join(wrong))

    # ...and no cell may be CONFIDENTLY WRONG, which is the property the
    # labels exist for: material that is neither a third party's nor the
    # assistant's must not be described as either.
    for author in (EvidenceAuthor.USER, EvidenceAuthor.SYSTEM):
        for derived in (None, EvidenceAuthor.USER, EvidenceAuthor.SYSTEM,
                        EvidenceAuthor.ASSISTANT):
            label = _origin_label(_edge(author, derived))
            assert "third-party" not in label and "assistant" not in label, (
                f"({author.value}, {derived}) renders {label!r} — an "
                f"affirmatively false origin, which is worse than none")


def test_an_unlabelled_author_fails_safe_rather_than_confidently():
    """Belt and braces: if the tripwire is ever bypassed, the fallback must not
    borrow a wrong-but-plausible origin."""
    class _Fake(str):
        pass
    e = _edge(EvidenceAuthor.THIRD_PARTY)
    object.__setattr__(e.provenance, "author_of_evidence", _Fake("brand_new"))
    assert _origin_label(e) == "unverified-origin"
    assert "third-party" not in _origin_label(e)


@pytest.mark.parametrize("author,derived,label", [
    (EvidenceAuthor.THIRD_PARTY, None, "third-party-reported"),
    # 0001 I12 — CHANGED AT IMPLEMENTATION, deliberately. Under the §4b
    # decision order the capping axis is read first, so a user's or the
    # system's record DERIVED FROM a third party is a relayed claim and
    # says so. Before pair-keying both rendered "third-party-reported",
    # which named the relay as the reporter.
    (EvidenceAuthor.USER, EvidenceAuthor.THIRD_PARTY,
     "third-party-derived"),
    (EvidenceAuthor.SYSTEM, EvidenceAuthor.THIRD_PARTY,
     "third-party-derived"),
    (EvidenceAuthor.ASSISTANT, None, "assistant-generated"),
    (EvidenceAuthor.ASSISTANT, EvidenceAuthor.THIRD_PARTY,
     "third-party-derived"),
])
def test_the_rendered_origin_is_exact_for_every_reachable_author(
        author, derived, label):
    """Rendered text IS model context, so 'byte-identical' is the
    requirement, not 'equivalent' — the whole line is pinned, not just
    the label, because that is what reaches the model."""
    out = render_edges([_edge(author, derived)])
    assert out == (f"owes: 500 to Acme (since 2026-08-01) "
                   f"[{label}; unconfirmed]")


def test_mentionable_edges_carry_no_origin_marker():
    out = render_edges([_edge(EvidenceAuthor.USER, disclosure=Disclosure.MENTIONABLE)])
    assert "unconfirmed" not in out and "third-party" not in out
