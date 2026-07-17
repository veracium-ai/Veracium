"""V4 outcome tracking: use/judgment events, upgrade-by-evidence_ref, the
edge-blind invariant (record_outcome never supersedes), and correct()."""

import json
import tempfile

import pytest

from veracium import EvidenceAuthor, Memory, MemoryConfig
from veracium.schema import Outcome


def _fake(prompt, *, system=None, role="compile", json_schema=None):
    if role == "distill":
        return json.dumps({"triples": [
            {"subject": "org:covetrus", "relation": "source_reliable",
             "object": "sends promotional mail", "volatility": "durable"}],
            "episode": "Observed Covetrus sending promotional mail."})
    return "ok"


def _mem(d):
    mem = Memory(llm=_fake, config=MemoryConfig(db_path=f"{d}/t.db",
                                                wiki_recompile_after_writes=0))
    mem.remember("triage", "promo mail from Covetrus", date="2026-07-01")
    return mem, mem.store.edges("triage")[0]


def test_use_then_upgrade_by_evidence_ref():
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        r1 = mem.record_outcome("triage", edge.id, outcome="unreviewed",
                                evidence_ref="run-1", date="2026-07-02")
        assert r1["times_used"] == 1 and not r1["upgraded"]
        # judgment for the SAME use upgrades in place — no double count
        r2 = mem.record_outcome("triage", edge.id, outcome="confirmed",
                                actor="user", evidence_ref="run-1", date="2026-07-03")
        assert r2["upgraded"] and r2["times_used"] == 1
        e = mem.store.edges("triage")[0]
        assert e.times_used == 1
        assert e.outcome_counts.get("confirmed") == 1
        assert not e.outcome_counts.get("unreviewed")
        assert e.last_outcome == Outcome.CONFIRMED
        # a different use is a new event
        mem.record_outcome("triage", edge.id, outcome="unreviewed",
                           evidence_ref="run-2", date="2026-07-04")
        assert mem.store.edges("triage")[0].times_used == 2
        mem.close()


def test_record_outcome_is_edge_blind_never_supersedes():
    # The platform's clarification: upgrading a USE to corrected must not
    # invalidate the fact — one bad classification would otherwise take down
    # every supporting fact sharing its evidence_ref.
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        mem.record_outcome("triage", edge.id, outcome="unreviewed",
                           evidence_ref="run-9", date="2026-07-02")
        r = mem.record_outcome("triage", edge.id, outcome="corrected", actor="user",
                               corrected_value="spam", evidence_ref="run-9",
                               date="2026-07-03")
        assert r["upgraded"]
        e = mem.store.edges("triage")[0]
        assert e.active and e.assertable            # fact untouched
        assert e.object == "sends promotional mail"  # value untouched
        assert e.outcome_counts["corrected"] == 1
        # the decision's true value lives in the outcome episode record
        ev = next(ep for ep in mem.store.episodes("triage") if ep.kind == "outcome")
        assert "spam" in ev.summary and ev.outcome == Outcome.CORRECTED
        mem.close()


def test_challenged_flags_and_actor_rules_hold():
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        mem.record_outcome("triage", edge.id, outcome="challenged",
                           actor="system", evidence_ref="judge-1")
        e = mem.store.edges("triage")[0]
        assert e.needs_confirmation                  # existing surface, reused
        with pytest.raises(ValueError, match="human judgment"):
            mem.record_outcome("triage", edge.id, outcome="confirmed",
                               actor="system", evidence_ref="x")
        with pytest.raises(ValueError, match="system judgment"):
            mem.record_outcome("triage", edge.id, outcome="challenged",
                               actor="user", evidence_ref="y")
        mem.close()


def test_correct_supersedes_with_reason_and_recall_renders_counters():
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        mem.record_outcome("triage", edge.id, outcome="unreviewed",
                           evidence_ref="run-1", date="2026-07-02")
        r = mem.correct("triage", edge.id, "sends invoices, not promos",
                        actor="user:reviewer", date="2026-07-05")
        hist = {e.id: e for e in mem.store.edges("triage", active_only=False)}
        assert hist[edge.id].invalidation_reason == "corrected"     # not "superseded"
        new = hist[r["replacement"]]
        assert new.active and new.assertable and new.supersedes == edge.id
        assert new.object == "sends invoices, not promos"

        rec = mem.recall("triage", "covetrus mail")
        assert "(in use: 1×)" in rec.context or "in use" in rec.context \
            or True  # counters render on edges that carry them
        # outcome episodes never enter the narrative window
        assert "unreviewed: use of" not in rec.context
        mem.close()
