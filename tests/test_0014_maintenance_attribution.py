"""specs/0014 + 0012 — the maintenance-attribution regressions.

Site ownership (research ruling 2026-08-08): the two REINFORCEMENT tests below pin finding M9,
now owned by `specs/0012` (Design 1 persists the reinforcing edge — the edge is the attribution).
The two reinforcement tests FLIPPED to passing when accepted `0012` landed (2026-08-10); the
consolidation/absorption pair stays xfail until `0014` lands.
The CONSOLIDATION and ABSORPTION tests pin `specs/0014` (the contribution ledger) and stay
xfail(strict) until `0014` lands; kept in one file because they share the reproduction
harness. (The pre-0012 header text describing reinforcement's transfer-and-discard defect is
superseded — that defect is CLOSED; see the two passing tests below and `0012` §12.)
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


def _edge(eid, author, evidence_ref, confidence, observed_at, source_id=None):
    # same subject/relation/value on every edge → a reinforcement, not a supersession;
    # MENTIONABLE on both → same disclosure class, so the identity merge is permitted
    # (USER and SYSTEM share MENTIONABLE, so a SYSTEM feed reinforces a USER fact).
    return Edge(id=eid, user_id=U, subject="user", relation="works_as", object="CFO at Acme",
                provenance=Provenance(source_type=SourceType.STATED, author_of_evidence=author,
                                      evidence_ref=evidence_ref, disclosure=Disclosure.MENTIONABLE,
                                      confidence=confidence, observed_at=observed_at,
                                      source_id=source_id))


def _evidence_ref_digest(origin: str, evidence_ref: str):
    """The FROZEN §4a construction (R2-5), implemented inline so these tests bite the
    moment the ledger lands — byte-exact: UTF-8, u32be length prefixes, domain-separated,
    origin-scoped; NULL (None) iff evidence_ref == "" (empty is DEFINED as absent)."""
    import hashlib, struct
    if evidence_ref == "":
        return None
    o, e = origin.encode("utf-8"), evidence_ref.encode("utf-8")
    return hashlib.sha256(b"veracium.evidence-ref.v1"
                          + struct.pack(">I", len(o)) + o
                          + struct.pack(">I", len(e)) + e).hexdigest()


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


def test_reinforcement_attributes_the_contributing_source(tmp_path):
    """0012 Design 1, LANDED (I7): the persisted incoming edge IS the M9 attribution.
    Inverted from the strict xfail that documented the pre-0012 defect: the transfer no
    longer happens (the prior is byte-untouched), BOTH edges survive, and the contributing
    source is recoverable through the edge it persisted."""
    s = SqliteStore(str(tmp_path / "s.db"))
    s.add_edge(_edge("e1", EvidenceAuthor.USER, "user-chat-jan", 0.5, JAN))
    apply_supersession(s, _edge("e2", EvidenceAuthor.SYSTEM, "badfeed-aug", 0.95, AUG),
                       DEFAULT_RELATIONS)

    survivors = {e.id: e for e in s.edges(U, active_only=True)}
    assert set(survivors) == {"e1", "e2"}              # Design 1: both persist
    prior = survivors["e1"]
    assert prior.provenance.observed_at == JAN         # the transfer NO LONGER happens
    assert prior.provenance.confidence == 0.5          # (currency + trust doors closed)

    # ...and the contributing source IS recoverable: the persisted edge is the attribution.
    assert _contributor_is_recoverable(s, U, prior.id, "badfeed-aug")


def test_reinforcement_records_the_contributor_even_when_no_value_moves(tmp_path):
    """0012 Design 1, LANDED: the empty-payload case. An older AND weaker contributor
    (DEC < JAN, 0.3 < 0.5 — under the old max() transfer nothing would have moved) is
    still PERSISTED with its own provenance, so the consumption is recorded regardless of
    whether any value moved — the record is owed to the act, not the payload."""
    s = SqliteStore(str(tmp_path / "s.db"))
    s.add_edge(_edge("e1", EvidenceAuthor.USER, "user-chat-jan", 0.5, JAN))
    apply_supersession(s, _edge("e2", EvidenceAuthor.SYSTEM, "badfeed-dec", 0.3, DEC),
                       DEFAULT_RELATIONS)

    survivors = {e.id: e for e in s.edges(U, active_only=True)}
    assert set(survivors) == {"e1", "e2"}              # Design 1: the contributor persists
    prior = survivors["e1"]
    assert prior.provenance.observed_at == JAN         # byte-unchanged, as before
    assert prior.provenance.confidence == 0.5

    # the older/weaker contributor no longer vanishes: its edge IS the record.
    assert _contributor_is_recoverable(s, U, prior.id, "badfeed-dec")


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
    # TWO outputs (R2-7): the N×M input×output relation must be exercised, not the
    # degenerate one-output case
    mem = Memory(llm=_Compactor([{"date": "2020-01-01", "summary": "compacted A"},
                                 {"date": "2020-06-01", "summary": "compacted B"}]),
                 config=cfg)
    return mem, cfg


def _add_cold(mem, i, author, evidence_ref, source_id=None):
    old = (datetime.now(timezone.utc) - timedelta(days=400)).date().isoformat()
    mem.store.add_episode(Episode(
        id=f"ep{i}", user_id="u", date=old, summary=f"cold episode {i}",
        provenance=Provenance(source_type=SourceType.STATED, author_of_evidence=author,
                              evidence_ref=evidence_ref, disclosure=Disclosure.MENTIONABLE,
                              source_id=source_id,
                              observed_at=datetime.now(timezone.utc))))


def _summary_contributor_sources(store, user_id, summary) -> set:
    """The contributor identities that fed a consolidation summary — the set `0014` A2
    makes recoverable, as CONTENT-FREE digests (the v5 contract, R1-7): the ledger read is
    `contributions(user_id, survivor_type, survivor_id)` and rows carry `identity_digest` /
    `evidence_ref_digest`, never raw refs. Today falls back to resolving `lineage` ids to a
    surviving episode (which fails — the inputs were deleted)."""
    contributions = getattr(store, "contributions", None)
    if contributions is not None:
        try:
            return {getattr(c, "evidence_ref_digest", None)
                    for c in contributions(user_id, "episode", summary.id)}
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
    _add_cold(mem, 0, EvidenceAuthor.USER, "user-onboarding", source_id="mailbox:me")
    for i in range(1, 9):                    # >= consolidate_min_batch (8) cold inputs
        _add_cold(mem, i, EvidenceAuthor.THIRD_PARTY, "badfeed-ep",
                  source_id="feed:bad")     # source_id SUPPLIED (R2-7)
    # the TWO-output compactor comes from _cold_mem's mem.llm (R3-4 — the previous
    # revision passed a separate ONE-output compactor here, failing len(outputs)==2
    # before ever reaching the ledger assertion)
    n_inputs = 9
    result = consolidate(mem.store, mem.llm, "u", cfg)
    assert result["consolidated"] == n_inputs, f"consolidation did not run: {result}"

    outputs = [e for e in mem.store.episodes("u") if e.lineage]
    assert len(outputs) == 2, "the N×M case needs BOTH outputs"

    # N×M CARDINALITY is asserted on ROWS, not a collapsed set (R3-4): every output
    # carries one row PER CLAIMED INPUT; identity is compared ONLY by the frozen
    # digest construction computed inline — no raw-reference escape.
    origin = mem.store.local_origin()
    expected_bad = _evidence_ref_digest(origin, "badfeed-ep")
    expected_user = _evidence_ref_digest(origin, "user-onboarding")
    for summary in outputs:
        rows = mem.store.contributions("u", "episode", summary.id)
        assert len(rows) == n_inputs, (
            f"output {summary.id}: expected N={n_inputs} contributor rows (the input×output "
            f"relation), got {len(rows)} — the sources behind the deleted inputs are not "
            f"recoverable (finding, 0014 §3.2/A2)")
        digests = [getattr(r, "evidence_ref_digest", None) for r in rows]
        assert digests.count(expected_bad) == 8 and digests.count(expected_user) == 1, (
            "the recovered rows do not carry the frozen evidence-ref digests of the "
            "consumed inputs (content-free identity, R2-7/R3-4)")
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
            rows = contributions("u", "edge", winner_id)      # the typed read (R1-7)
            expected = _evidence_ref_digest(store.local_origin(), contributor_ref)
            # prove THE contributor: site + the frozen-construction digest match (R2-7)
            return any(getattr(c, "site", None) == "absorption"
                       and getattr(c, "evidence_ref_digest", None) == expected
                       for c in rows)
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
