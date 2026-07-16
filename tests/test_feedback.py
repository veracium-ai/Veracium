"""dispute()/confirm(): explicit user-feedback verbs over the evidence model."""

import json
import tempfile

import pytest

from veracium import EvidenceAuthor, Memory, MemoryConfig
from veracium.gate import partition


class Fake:
    SCRIPTS = [
        {"triples": [{"subject": "user", "relation": "works_as",
                      "object": "designer at Acme", "volatility": "durable"}],
         "episode": "User said they work as a designer at Acme."},
        {"triples": [{"subject": "org:quickclaim", "relation": "third_party_claim",
                      "object": "user owes $2,400"}],
         "episode": "Received a billing notice claiming the user owes $2,400."},
    ]

    def __init__(self):
        self._i = 0

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            out = self.SCRIPTS[self._i]; self._i += 1
            return json.dumps(out)
        return ""


def _mem(d):
    mem = Memory(llm=Fake(), config=MemoryConfig(db_path=f"{d}/t.db",
                                                 wiki_recompile_after_writes=0))
    mem.remember("u", "USER: I'm a designer at Acme.", date="2026-06-01")
    mem.remember("u", "From QuickClaim: you owe $2,400.", date="2026-06-04",
                 author=EvidenceAuthor.THIRD_PARTY, event_type="email")
    return mem


def test_dispute_removes_from_assertable_but_keeps_history():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d)
        fact = next(e for e in mem.store.edges("u") if e.relation == "works_as")
        r = mem.dispute("u", fact.id, reason="I never said that", actor="user:u")
        assert r["disputed"] == fact.id

        # out of every assertable surface, retained as history
        assert all(e.id != fact.id for e in mem.store.edges("u"))          # not active
        hist = {e.id: e for e in mem.store.edges("u", active_only=False)}
        assert hist[fact.id].invalidation_reason == "disputed"
        grounded, _ = partition(mem.store.edges("u", active_only=False),
                                mem.store.episodes("u"))
        # the disputed EDGE is no longer an assertable fact line (the historical
        # episode recording that the user once said it legitimately remains)
        assert "works_as: designer at Acme (since" not in grounded

        # the dispute itself is remembered, with actor and reason
        eps = mem.store.episodes("u")
        assert any("disputed" in ep.summary and "user:u" in ep.summary
                   and "never said that" in ep.summary for ep in eps)

        # disputing twice fails loudly
        with pytest.raises(ValueError, match="not active"):
            mem.dispute("u", fact.id)
        mem.close()


def test_confirm_refreshes_validity_and_blocks_claim_elevation():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d)
        fact = next(e for e in mem.store.edges("u") if e.relation == "works_as")
        fact.needs_confirmation = True                    # simulate a stale flag
        mem.store.add_edge(fact)

        r = mem.confirm("u", fact.id, date="2026-07-16", actor="user:u")
        assert r["confirmed"] == fact.id
        refreshed = next(e for e in mem.store.edges("u") if e.id == fact.id)
        assert not refreshed.needs_confirmation
        assert refreshed.valid_from.date().isoformat() == "2026-07-16"
        assert refreshed.provenance.confidence >= 0.9
        assert any("confirmed" in ep.summary for ep in mem.store.episodes("u"))

        # confirming a quarantined claim must NOT elevate it (laundering vector)
        claim = next(e for e in mem.store.edges("u", active_only=False)
                     if e.quarantined)
        with pytest.raises(ValueError, match="remember"):
            mem.confirm("u", claim.id)

        with pytest.raises(ValueError, match="no edge"):
            mem.confirm("u", "e-nonexistent")
        mem.close()
