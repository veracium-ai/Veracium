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
import json
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from veracium import Memory
from veracium.config import MemoryConfig
from veracium.graph import apply_supersession
from veracium.lifecycle import consolidate
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge, Episode, EvidenceAuthor,
                             Provenance, SourceType)
from veracium.store.sqlite import SqliteStore

U = "u1"
DEC = datetime(2025, 12, 1, tzinfo=timezone.utc)   # OLDER than the prior
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


@pytest.mark.xfail(strict=True, reason=(
    "specs/0014 A1a (research's consult-and-discard sharpening): a contributor that moves no "
    "max() — older AND weaker — leaves the survivor unchanged, but is STILL consumed and STILL "
    "vanishes. A transfer-keyed rule would miss it; the invariant is owed to the consumption. "
    "This is the attack path: an adversary contributes invisibly by ensuring no value moves. "
    "Remove this marker when 0014's contribution ledger records empty-payload consumptions."))
def test_reinforcement_records_the_contributor_even_when_no_value_moves(tmp_path):
    s = SqliteStore(str(tmp_path / "s.db"))
    # the prior is newer AND stronger than the contributor, so max() keeps it on both fields
    s.add_edge(_edge("e1", EvidenceAuthor.USER, "user-chat-jan", 0.5, JAN))
    apply_supersession(s, _edge("e2", EvidenceAuthor.SYSTEM, "badfeed-dec", 0.3, DEC),
                       DEFAULT_RELATIONS)

    survivors = s.edges(U, active_only=True)
    assert len(survivors) == 1
    survivor = survivors[0]

    # the payload is EMPTY — nothing transferred, the survivor is byte-for-byte unchanged
    # (true today): DEC < JAN and 0.3 < 0.5, so both max() keep the prior.
    assert survivor.provenance.observed_at == JAN      # unchanged
    assert survivor.provenance.confidence == 0.5       # unchanged

    # ...yet the contributor was consulted and discarded, and left no trace — so
    # "which sources support this fact?" omits it and a blast radius under-reports (0014 A1a).
    assert _contributor_is_recoverable(s, U, survivor.id, "badfeed-dec"), (
        "an older/weaker contributor moved no value but was still consumed and still vanished "
        "— a transfer-keyed invariant misses it; the record is owed to the consumption (0014 A1a)")


# =============================================================================
# §3.2 — consolidation: a summary's contributor SOURCES are not recoverable.
# 0010's `lineage` records which input IDs went into a summary, but the inputs are
# hard-deleted, so lineage-id → source cannot be resolved (0014 §3.2, A2).
# =============================================================================

class _Compactor:
    """A faithful compactor (mirrors test_consolidation_provenance): returns the summary
    records it was constructed with, regardless of prompt."""

    def __init__(self, records):
        self.records = records

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        return json.dumps({"records": self.records})


def _cold_mem(tmp_path):
    cfg = MemoryConfig(db_path=str(tmp_path / "c.db"), wiki_recompile_after_writes=0)
    mem = Memory(llm=_Compactor([{"date": "2020-01-01", "summary": "compacted"}]), config=cfg)
    return mem, cfg


def _add_cold(mem, i, author, evidence_ref):
    old = (datetime.now(timezone.utc) - timedelta(days=400)).date().isoformat()
    mem.store.add_episode(Episode(
        id=f"ep{i}", user_id="u", date=old, summary=f"cold episode {i}",
        provenance=Provenance(source_type=SourceType.STATED, author_of_evidence=author,
                              evidence_ref=evidence_ref, disclosure=Disclosure.MENTIONABLE,
                              observed_at=datetime.now(timezone.utc))))


def _summary_contributor_sources(store, user_id, summary) -> set:
    """The sources that fed a consolidation summary — the set `0014` A2 makes recoverable.
    Prefers the future contribution ledger; today falls back to resolving `lineage` ids to a
    surviving episode's source (which fails, because the inputs were deleted)."""
    contributions = getattr(store, "contributions", None)
    if contributions is not None:
        try:
            return {getattr(c, "contributor_ref", None) for c in contributions(summary.id)}
        except NotImplementedError:
            pass
    by_id = {e.id: e for e in store.episodes(user_id)}
    return {by_id[lid].provenance.evidence_ref
            for lid in (summary.lineage or []) if lid in by_id}


@pytest.mark.xfail(strict=True, reason=(
    "specs/0014 §3.2 / A2: a consolidation summary's contributor SOURCES are not recoverable. "
    "0010's lineage records the input IDs, but the inputs are hard-deleted, so lineage-id → "
    "source cannot be resolved. Remove this marker when 0014 records input attribution before "
    "deletion."))
def test_consolidation_contributors_survive_input_deletion(tmp_path):
    mem, cfg = _cold_mem(tmp_path)
    _add_cold(mem, 0, EvidenceAuthor.USER, "user-onboarding")
    for i in range(1, 6):                                     # several cold episodes to consolidate
        _add_cold(mem, i, EvidenceAuthor.THIRD_PARTY, "badfeed-ep")
    result = consolidate(mem.store, _Compactor([{"date": "2020-01-01", "summary": "compacted"}]),
                         "u", cfg)
    assert result["consolidated"] > 0, f"consolidation did not run: {result}"

    outputs = [e for e in mem.store.episodes("u") if e.lineage]
    assert outputs, "no consolidation output was written"
    summary = outputs[0]
    assert summary.lineage                                    # the input IDs ARE recorded (0010)

    # ...but the SOURCE behind those inputs is gone — a summary carrying badfeed's material
    # cannot be identified as carrying it (0014 §3.2). Fails today.
    sources = _summary_contributor_sources(mem.store, "u", summary)
    assert "badfeed-ep" in sources, (
        "a consolidation summary cannot name the sources that fed it — its inputs were "
        "deleted and lineage ids resolve to nothing (finding, 0014 §3.2/A2)")
    mem.close()


# =============================================================================
# §3.3 — absorption: the contributor link is a free-text `note` string, not a
# queryable contribution record (0014 §3.3, A3).
# =============================================================================

def _pet_edge(eid, obj, evidence_ref):
    return Edge(id=eid, user_id="u", subject="user", relation="has_pet", object=obj,
                provenance=Provenance(source_type=SourceType.STATED,
                                      author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=evidence_ref, disclosure=Disclosure.MENTIONABLE))


def _absorption_contributor_queryable(store, winner_id, contributor_ref) -> bool:
    """Is the absorbed contributor recoverable via a QUERYABLE record (not by parsing a
    free-text note)? The property `0014` A3 establishes. No note-string fallback here —
    that the note exists is asserted separately as the (partial) state today."""
    contributions = getattr(store, "contributions", None)
    if contributions is not None:
        try:
            return any(getattr(c, "contributor_ref", None) == contributor_ref
                       for c in contributions(winner_id))
        except NotImplementedError:
            pass
    return False


@pytest.mark.xfail(strict=True, reason=(
    "specs/0014 §3.3 / A3: absorption's contributor link survives only as a free-text "
    "`note = 'absorbed_by:<id>'` string, not a queryable relation, and the inherited "
    "valid_from/observed_at/confidence cannot be un-inherited. Remove this marker when 0014 "
    "promotes the link to a queryable contribution record."))
def test_absorption_link_is_a_queryable_contribution(tmp_path):
    s = SqliteStore(str(tmp_path / "a.db"))
    # a shorter prior from one source, then a MORE SPECIFIC restatement from another absorbs it
    s.add_edge(_pet_edge("e1", "Miso", "badfeed-pet"))
    apply_supersession(s, _pet_edge("e2", "cat Miso", "user-pet"), DEFAULT_RELATIONS)

    winner = next(e for e in s.edges("u", active_only=True))
    loser = next(e for e in s.edges("u", active_only=False) if not e.active)
    # the link DOES survive, but only as a free-text note back-pointer (true today — the
    # partial state 0014 §3.3 names): recoverable by string-parsing, not by query.
    assert loser.invalidation_reason == "absorbed_duplicate"
    assert f"absorbed_by:{winner.id}" in loser.note

    # ...the queryable contribution record does not exist, so the contributor cannot be
    # enumerated as a relation (0014 §3.3/A3). Fails today.
    assert _absorption_contributor_queryable(s, winner.id, "badfeed-pet"), (
        "absorption's contributor link is only a note string, not a queryable contribution "
        "record — it cannot be enumerated or reversed (finding, 0014 §3.3/A3)")
