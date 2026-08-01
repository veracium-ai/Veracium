"""Lifecycle: expiry, reinforcement, consolidation (offline, time-controlled)."""

import json
import tempfile
from datetime import datetime, timezone

from veracium import Memory, MemoryConfig, EvidenceAuthor
from veracium import lifecycle


class Fake:
    def __init__(self, scripts):
        self._s = list(scripts); self.i = 0
    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        out = self._s[self.i]; self.i += 1
        return out if isinstance(out, str) else json.dumps(out)


def _mem(d, scripts):
    return Memory(llm=Fake(scripts),
                  config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=0))


def test_expiry_lapse_confirm_and_reinforcement():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d, [
            # transient illness + durable employer
            {"triples": [{"subject": "user", "relation": "health_state", "object": "flu", "volatility": "transient"},
                         {"subject": "user", "relation": "works_as", "object": "designer at Acme", "volatility": "durable"}],
             "episode": "User is sick with flu; works as a designer at Acme."},
        ])
        mem.remember("u", "USER: I've got the flu. I'm a designer at Acme.", date="2026-01-01")

        # 60 days later: transient flu should LAPSE, durable employer stays active
        now = datetime(2026, 3, 2, tzinfo=timezone.utc)
        rep = lifecycle.expire(mem.store, "u", mem.config, now=now)
        assert rep["lapsed"] == 1
        assert not any(e.object == "flu" for e in mem.store.edges("u"))          # gone (active)
        assert any(e.object == "flu" for e in mem.store.edges("u", active_only=False))  # retained
        assert any("designer at Acme" in e.object for e in mem.store.edges("u"))  # durable survives

        # 800 days later: durable employer past lifetime → flagged, not dropped
        now2 = datetime(2028, 3, 15, tzinfo=timezone.utc)
        rep2 = lifecycle.expire(mem.store, "u", mem.config, now=now2)
        assert rep2["flagged_for_confirmation"] == 1
        emp = [e for e in mem.store.edges("u") if "Acme" in e.object][0]
        assert emp.needs_confirmation and emp.active  # surfaced as stale, still present
        mem.close()


def test_reinforcement_refreshes_not_duplicates():
    with tempfile.TemporaryDirectory() as d:
        script = {"triples": [{"subject": "user", "relation": "health_state", "object": "flu", "volatility": "transient"}],
                  "episode": "still sick"}
        mem = _mem(d, [script, script])
        mem.remember("u", "sick", date="2026-01-01")
        mem.remember("u", "still sick", date="2026-01-05")  # re-stated → refresh
        active = mem.store.edges("u", relation="health_state")
        assert len(active) == 1                              # not duplicated
        # valid_from is FIRST-KNOWN and immutable; the restatement refreshes
        # liveness on observed_at, which is the field lifecycle now ages against
        assert active[0].valid_from.date().isoformat() == "2026-01-01"
        assert active[0].provenance.observed_at.date().isoformat() == "2026-01-05"
        mem.close()


def test_reinforcement_matches_paraphrased_values():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d, [
            {"triples": [{"subject": "user", "relation": "has_pet", "object": "dog named Ollie", "volatility": "durable"}],
             "episode": "has a dog named Ollie"},
            {"triples": [{"subject": "user", "relation": "has_pet", "object": "dog Ollie", "volatility": "durable"}],
             "episode": "mentioned the dog again"},
        ])
        mem.remember("u", "I have a dog named Ollie.", date="2026-01-01")
        mem.remember("u", "My dog Ollie is great.", date="2026-01-05")  # paraphrase → refresh
        active = mem.store.edges("u", relation="has_pet")
        assert len(active) == 1                              # reinforced, not duplicated
        assert active[0].valid_from.date().isoformat() == "2026-01-01"   # first-known
        assert active[0].provenance.observed_at.date().isoformat() == "2026-01-05"
        mem.close()


def test_paraphrase_match_stays_order_sensitive():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d, [
            {"triples": [{"subject": "user", "relation": "prefers", "object": "tea over coffee", "volatility": "durable"}],
             "episode": "prefers tea"},
            {"triples": [{"subject": "user", "relation": "prefers", "object": "coffee over tea", "volatility": "durable"}],
             "episode": "prefers coffee now"},
        ])
        mem.remember("u", "I prefer tea over coffee.", date="2026-01-01")
        mem.remember("u", "Actually I prefer coffee over tea.", date="2026-01-05")
        active = mem.store.edges("u", relation="prefers")
        assert len(active) == 1                              # functional → superseded
        assert active[0].object == "coffee over tea"         # NOT merged with the old value
        hist = mem.store.edges("u", relation="prefers", active_only=False)
        assert any(not e.active and e.object == "tea over coffee" for e in hist)
        mem.close()


def test_consolidation_preserves_and_compresses():
    with tempfile.TemporaryDirectory() as d:
        # 10 cold episodes; consolidation returns 3 (a failure, its fix, a routine merge)
        extract = [{"triples": [], "episode": f"Routine work day {i}."} for i in range(10)]
        consolidated = {"records": [
            {"date": "2026-01-02", "summary": "Build failed on the export step (first occurrence)."},
            {"date": "2026-01-05", "summary": "Fixed the export by switching tools."},
            {"date": "2026-01-06", "summary": "Several routine work days."}]}
        mem = _mem(d, extract + [consolidated])
        for i in range(10):
            mem.remember("u", f"day {i}", date=f"2026-01-{i+1:02d}")
        assert len(mem.store.episodes("u")) == 10

        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        rep = lifecycle.consolidate(mem.store, mem.llm, "u", mem.config, now=now)
        assert rep == {"consolidated": 10, "into": 3}
        eps = mem.store.episodes("u")
        assert len(eps) == 3
        assert any("first occurrence" in e.summary for e in eps)  # guard held
        mem.close()


if __name__ == "__main__":
    test_expiry_lapse_confirm_and_reinforcement()
    test_reinforcement_refreshes_not_duplicates()
    test_reinforcement_matches_paraphrased_values()
    test_paraphrase_match_stays_order_sensitive()
    test_consolidation_preserves_and_compresses()
    print("lifecycle OK")


# --- 0.4.6: the two defects found verifying 0002's external review ----------

def _one_edge(m, valid_from):
    from veracium.schema import Edge, Provenance, SourceType
    e = Edge(id="e-t", user_id="u", subject="user", relation="likes", object="tea",
             valid_from=valid_from,
             provenance=Provenance(source_type=SourceType.STATED,
                                   author_of_evidence=EvidenceAuthor.USER,
                                   evidence_ref="x", observed_at=valid_from))
    m.store.add_edge(e)
    return e


def test_confirm_returns_the_real_valid_from_not_the_confirmation_date():
    """M2 removed the false date from the model's context and left it in the
    return contract a host UI reads."""
    with tempfile.TemporaryDirectory() as d:
        m = _mem(d, [])
        _one_edge(m, datetime(2026, 1, 1, tzinfo=timezone.utc))
        r = m.confirm("u", "e-t", date="2026-03-15")
        assert r["valid_from"] == "2026-01-01", "returned the confirmation date again"
        assert r["confirmed_at"] == "2026-03-15"
        stored = [x for x in m.store.edges("u") if x.id == "e-t"][0]
        assert r["valid_from"] == stored.valid_from.date().isoformat()


def test_a_future_event_date_is_rejected():
    import pytest
    from veracium.ingest import _event_dt
    with pytest.raises(ValueError, match="in the future"):
        _event_dt("2099-01-01")


def test_clock_skew_is_tolerated_but_a_typo_is_not():
    import pytest
    from veracium.ingest import _event_dt, MAX_FUTURE_SKEW
    from veracium.schema import utcnow
    _event_dt((utcnow() + MAX_FUTURE_SKEW / 2).date().isoformat())   # must not raise
    with pytest.raises(ValueError):
        _event_dt((utcnow() + MAX_FUTURE_SKEW * 10).date().isoformat())


def test_a_future_confirmation_cannot_freeze_an_edge_out_of_the_lifecycle():
    """observed_at only ever advances, so before the clamp a single future date
    was unrecoverable: no later confirmation could lower it."""
    import pytest
    with tempfile.TemporaryDirectory() as d:
        m = _mem(d, [])
        _one_edge(m, datetime(2026, 1, 1, tzinfo=timezone.utc))
        with pytest.raises(ValueError):
            m.confirm("u", "e-t", date="2099-01-01")
        stored = [x for x in m.store.edges("u") if x.id == "e-t"][0]
        assert stored.provenance.observed_at.year < 2099, "the write must not land"


def test_a_future_date_cannot_enter_through_ingest_either():
    """The clamp is at _event_dt, not in confirm(): remember() reaches
    valid_from AND observed_at, so it was the wider of the two doors."""
    import pytest
    with tempfile.TemporaryDirectory() as d:
        m = _mem(d, [{"triples": [{"subject": "user", "relation": "works_as",
                                   "object": "CFO"}], "episode": "said"}])
        with pytest.raises(ValueError, match="in the future"):
            m.remember("u", "I am CFO at Acme", date="2099-01-01")


def test_past_and_today_still_work():
    with tempfile.TemporaryDirectory() as d:
        m = _mem(d, [])
        _one_edge(m, datetime(2026, 1, 1, tzinfo=timezone.utc))
        assert m.confirm("u", "e-t", date="2026-02-01")["confirmed"] == "e-t"
