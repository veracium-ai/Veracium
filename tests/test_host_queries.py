"""Host/admin query conveniences: list_entities() and edges_since()."""

import json
import tempfile
from datetime import datetime, timezone

import pytest

from veracium import EvidenceAuthor, Memory, MemoryConfig
from veracium.store.sqlite import SqliteStore


class Fake:
    def __init__(self):
        self._i = 0
        self.scripts = [
            {"triples": [{"subject": "user", "relation": "uses_tool", "object": "invoices portal",
                          "volatility": "durable"}],
             "episode": "Vendor sent an invoice via the portal."},
            {"triples": [{"subject": "user", "relation": "uses_tool", "object": "wire transfer",
                          "volatility": "durable"}],
             "episode": "Vendor asked to switch to wire transfer."},
            {"triples": [], "episode": "Newsletter received."},
        ]

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            out = self.scripts[self._i]; self._i += 1
            return json.dumps(out)
        return ""


def test_list_entities_counts_per_user():
    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=Fake(), config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db",  # 0006 v8: opted out — measures records that exist (rule 8 / I3 / I13), not the ingest requirement
                                                     wiki_recompile_after_writes=0))
        mem.remember("vendor:acme", "invoice", date="2026-07-01",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        mem.remember("vendor:acme", "wire", date="2026-07-10",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        mem.remember("vendor:globex", "newsletter", date="2026-07-05",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        ents = mem.list_entities()
        assert [e["user_id"] for e in ents] == ["vendor:acme", "vendor:globex"]
        acme = ents[0]
        assert acme["edges"] == 2 and acme["episodes"] == 2
        assert ents[1]["edges"] == 0 and ents[1]["episodes"] == 1  # empty triples
        mem.close()


def test_edges_since_filters_on_observed_at():
    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=Fake(), config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db",  # 0006 v8: opted out — measures records that exist (rule 8 / I3 / I13), not the ingest requirement
                                                     wiki_recompile_after_writes=0))
        mem.remember("vendor:acme", "invoice", date="2026-07-01",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        mem.remember("vendor:acme", "wire", date="2026-07-10",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")

        recent = mem.edges_since("vendor:acme", "2026-07-05")
        assert len(recent) == 1 and "wire" in recent[0].object
        assert mem.edges_since("vendor:acme", "2026-07-11") == []
        both = mem.edges_since("vendor:acme", "2026-06-01")
        assert len(both) == 2
        # includes non-assertable material: these third-party edges are use_only
        assert all(not e.assertable for e in both)
        mem.close()


@pytest.mark.xfail(strict=True, reason=(
    "specs 0049 (research's candidate): edges_since filters on provenance.observed_at, which ingest sets from the "
    "EVENT's date, so a fact learned today about an older event is missed. Remove this marker with the fix: "
    "strict, so the fix turns this test red until the marker goes."))
def test_edges_since_means_learned_not_occurred():
    """`edges_since` returns the edges Veracium LEARNED after `since` (its docstring, docs/api.md, docs/recipes.md), not
    the ones whose event happened after it. Event time and learned time are pulled apart: two events dated in 2025 and
    2024 are remembered on a controlled store clock on 2026-07-01 and 2026-07-10. The superseded test above cannot tell
    the two meanings apart, because its event dates and remember dates coincide (0049 §1)."""
    with tempfile.TemporaryDirectory() as d:
        now = {"t": datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)}
        store = SqliteStore(f"{d}/t.db", clock=lambda: now["t"])
        mem = Memory(llm=Fake(), store=store,
                     config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db",  # 0006 v8: opted out, as above
                                         wiki_recompile_after_writes=0))
        mem.remember("vendor:acme", "invoice", date="2025-03-01",            # learned 2026-07-01, happened 2025
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        now["t"] = datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)
        mem.remember("vendor:acme", "wire", date="2024-11-15",               # learned 2026-07-10, happened 2024
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")

        recent = mem.edges_since("vendor:acme", "2026-07-05")
        assert [e.object for e in recent] == ["wire transfer"], [e.object for e in recent]
        assert mem.edges_since("vendor:acme", "2026-07-11") == []
        assert len(mem.edges_since("vendor:acme", "2026-06-01")) == 2
        assert mem.edges_since("vendor:acme", "2026-01-01") != []    # an event-time filter would also return both here
        mem.close()
