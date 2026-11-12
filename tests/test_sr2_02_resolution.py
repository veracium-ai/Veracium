"""SR2-02 (shipped-changes round 2): how a contested commitment is resolved, run on the review's own case.

0003 v18.4 §4c-v.6a, README, docs/api.md and the CHANGELOG state that `correct()` applies no reschedule to a named
obligation, `confirm()` retires neither date, and the user's resolution is `dispute()` of each stale date. Round 2
found the previous wording ("no public call settles") was a claim no cell ran; this cell runs every call the text names,
so the next change that moves one of them fails here instead of leaving the text silently false.

The case is the reviewer's (repro/probe_round2.py, public_dispute): a dentist appointment stated as 2026-11-12, then as
2026-11-14, by two direct user events.
"""
import json

import pytest

from veracium import EvidenceAuthor, EvidenceContext, Memory, MemoryConfig, redaction
from veracium.graph import CorrectionRefused

OLD, NEW = "2026-11-12", "2026-11-14"


class _Scripted:
    def __init__(self, dates):
        self.dates = list(dates)

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role != "distill":
            return ""
        return json.dumps({"triples": [{"subject": "dentist appointment", "relation": "deadline",
                                        "object": self.dates.pop(0), "volatility": "durable"}],
                           "episode": "The user stated a dated commitment.", "instructions": []})


def _contest(tmp_path, name="s.db", sources=False):
    m = Memory(llm=_Scripted([OLD, NEW]), config=MemoryConfig(db_path=str(tmp_path / name), require_source_id=False,
                                                               wiki_recompile_after_writes=0))
    for i, d in enumerate((OLD, NEW)):
        kw = {"source_id": f"src-{i}"} if sources else {}
        m.remember("u", f"My dentist appointment is {d}.", date=f"2026-11-0{i + 1}", context=EvidenceContext.direct(),
                   **kw)
    edges = {e.object: e for e in m.store.edges("u") if e.relation == "deadline"}
    assert set(edges) == {OLD, NEW} and all(e.active for e in edges.values()), edges
    groups, _ = m._build_contested("u", [], None)
    assert len(groups) == 1, "the case must start as one contested commitment"
    return m, edges


def _active(m):
    return {e.object for e in m.store.edges("u") if e.relation == "deadline" and e.active}


def test_sr2_02_correct_applies_no_reschedule_to_either_date(tmp_path):
    m, edges = _contest(tmp_path)
    for stale, other in ((OLD, NEW), (NEW, OLD)):
        with pytest.raises(CorrectionRefused):
            m.correct("u", edges[stale].id, other)
    assert _active(m) == {OLD, NEW} and len(m._build_contested("u", [], None)[0]) == 1
    m.close()


def test_sr2_02_confirm_retires_neither_date(tmp_path):
    """0003 v18.4: `confirm()` of either member retires neither date."""
    m, edges = _contest(tmp_path)
    for d in (OLD, NEW):
        m.confirm("u", edges[d].id)
        assert _active(m) == {OLD, NEW} and len(m._build_contested("u", [], None)[0]) == 1, d
    m.close()


def test_sr2_02_dispute_of_the_stale_date_is_the_users_resolution(tmp_path):
    m, edges = _contest(tmp_path)
    assert m.recall("u", "dentist appointment", semantic=False).contested, "the query must report the contest before"
    before = {e.id for e in m.store.episodes("u")}
    m.dispute("u", edges[OLD].id, reason="The earlier date is no longer current.")
    assert _active(m) == {NEW}
    assert m._build_contested("u", [], None)[0] == []
    assert not m.recall("u", "dentist appointment", semantic=False).contested
    kept = next(e for e in m.store.edges("u", active_only=False) if e.id == edges[OLD].id)
    assert not kept.active and kept.invalidation_reason == "disputed"          # kept as history, out of the views
    new = [e for e in m.store.episodes("u") if e.id not in before]
    assert len(new) == 1, new                                                   # the dispute's own episode, by id
    assert new[0].kind == "interaction" and new[0].provenance.author_of_evidence == EvidenceAuthor.USER, new[0]
    m.close()


def test_sr2_02_redact_and_revoke_source_remove_a_date_without_being_a_resolution(tmp_path):
    """The text names them as content removal and source distrust: each takes the date out of the current views."""
    m, edges = _contest(tmp_path, "redact.db")
    m.redact("u", edge_id=edges[OLD].id, reason=sorted(redaction.ORIGINATING_REASONS)[0])
    assert OLD not in _active(m) and NEW in _active(m)
    m.close()
    m, edges = _contest(tmp_path, "revoke.db", sources=True)
    m.revoke_source("u", None, "src-0", sorted(redaction.SOURCE_REVOCATION_REASONS)[0])
    assert OLD not in _active(m) and NEW in _active(m)
    m.close()
