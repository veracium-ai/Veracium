"""Host/admin query conveniences: list_entities() and edges_since()."""

import json
import tempfile

from veracium import EvidenceAuthor, Memory, MemoryConfig


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
        mem = Memory(llm=Fake(), config=MemoryConfig(db_path=f"{d}/t.db",
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
        mem = Memory(llm=Fake(), config=MemoryConfig(db_path=f"{d}/t.db",
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
