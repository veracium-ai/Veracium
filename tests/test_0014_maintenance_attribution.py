"""specs/0014 (draft) — the maintenance-attribution regression, pinning finding M9.

This test documents an OPEN defect executably. Reinforcement transfers a contributor's
liveness (`observed_at`) and confidence into the survivor and then discards the incoming
edge, so the contributing source leaves no trace — it cannot be audited ("why is this fact
live?") or reversed (source revocation). See `specs/findings.py` M9 and
`specs/0014-maintenance-attribution.md` §3.1 / invariant A1.

It is marked `xfail(strict=True)` because `0014` is `draft` and unimplemented: the
attribution record does not exist yet, so the property fails today. When `0014` lands the
contribution ledger, this test XPASSes, the strict marker turns the suite red, and whoever
implemented it updates the assertion to the real `contributions()` API and removes the
marker — the same xfail→prohibition path `tests/test_maintenance_invariant.py` used. The
"the transfer DID happen" assertions below are true TODAY, so the only thing that fails is
the attribution — the finding, and nothing else.
"""
from datetime import datetime, timezone

import pytest

from veracium.graph import apply_supersession
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge, EvidenceAuthor,
                             Provenance, SourceType)
from veracium.store.sqlite import SqliteStore

U = "u1"
JAN = datetime(2026, 1, 1, tzinfo=timezone.utc)
AUG = datetime(2026, 8, 1, tzinfo=timezone.utc)


def _edge(eid, author, evidence_ref, confidence, observed_at):
    # same subject/relation/value on every edge → a reinforcement, not a supersession;
    # MENTIONABLE on both → same disclosure class, so the identity merge is permitted
    # (USER and SYSTEM share MENTIONABLE, so a SYSTEM feed reinforces a USER fact).
    return Edge(id=eid, user_id=U, subject="user", relation="works_as", object="CFO at Acme",
                provenance=Provenance(source_type=SourceType.STATED, author_of_evidence=author,
                                      evidence_ref=evidence_ref, disclosure=Disclosure.MENTIONABLE,
                                      confidence=confidence, observed_at=observed_at))


def _contributor_is_recoverable(store, user_id, survivor_id, contributor_ref) -> bool:
    """Can the source that reinforced `survivor_id` be found after the fact? The property
    `0014` will establish. Prefers the future contribution ledger; falls back to the only
    place attribution could live today (a persisted edge carrying that evidence_ref)."""
    contributions = getattr(store, "contributions", None)
    if contributions is not None:
        try:
            return any(getattr(c, "contributor_ref", None) == contributor_ref
                       for c in contributions(survivor_id))
        except NotImplementedError:
            pass
    return any(e.provenance.evidence_ref == contributor_ref
               for e in store.edges(user_id, active_only=False))


@pytest.mark.xfail(strict=True, reason=(
    "specs/0014 / finding M9: reinforcement does not yet attribute the contributing source. "
    "The incoming edge is never persisted (insert_incoming=False) and no contribution record "
    "is written, so the source that moved the survivor's liveness and confidence leaves no "
    "trace. Remove this marker when 0014's contribution ledger lands."))
def test_reinforcement_attributes_the_contributing_source(tmp_path):
    s = SqliteStore(str(tmp_path / "s.db"))
    # the user states the fact in January, at low confidence
    s.add_edge(_edge("e1", EvidenceAuthor.USER, "user-chat-jan", 0.5, JAN))
    # a DIFFERENT source (the one we might later want to revoke) restates the SAME value in
    # August at high confidence — a same-class reinforcement of the user's fact
    apply_supersession(s, _edge("e2", EvidenceAuthor.SYSTEM, "badfeed-aug", 0.95, AUG),
                       DEFAULT_RELATIONS)

    survivors = s.edges(U, active_only=True)
    assert len(survivors) == 1
    survivor = survivors[0]

    # the transfer DID happen (measured, true today): the contributor moved the survivor's
    # liveness forward seven months and raised its confidence — lifecycle ages against
    # observed_at, so a compromised feed can keep a stale fact alive invisibly.
    assert survivor.provenance.observed_at == AUG      # was JAN
    assert survivor.provenance.confidence == 0.95      # was 0.5

    # ...but the contributing source left NO recoverable record (M9 / 0014 A1). This is the
    # defect: state was transferred, the evidence it happened was not. Fails today.
    assert _contributor_is_recoverable(s, U, survivor.id, "badfeed-aug"), (
        "the source 'badfeed-aug' moved the survivor's observed_at and confidence but left "
        "no attribution — its contribution cannot be audited or reversed (finding M9)")
