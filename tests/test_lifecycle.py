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
        assert active[0].valid_from.date().isoformat() == "2026-01-05"  # refreshed
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
    test_consolidation_preserves_and_compresses()
    print("lifecycle OK")
