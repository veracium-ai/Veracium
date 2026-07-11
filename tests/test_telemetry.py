"""Telemetry: content-free guarantee, off-by-default, consent gating, flush."""

import json
import os
import tempfile

import pytest

from engram import Memory, MemoryConfig, EvidenceAuthor
from engram import telemetry as T


@pytest.fixture(autouse=True)
def _isolated_config(tmp_path, monkeypatch):
    # never touch the real ~/.config/engram
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))


def test_content_free_record_drops_everything_off_whitelist():
    c = T.Collector()
    # legitimate scalar fields accumulate...
    c.record("ingest", {"facts": 2, "quarantined": 1, "episodes": 1})
    # ...string values and unknown keys (potential content) are dropped entirely
    c.record("ingest", {"facts": 1, "object": "vegetarian", "user_id": "alice",
                        "note": "$2,400 owed", "episode_text": "secret"})
    snap = c.snapshot()
    flat = json.dumps(snap)
    for leak in ("vegetarian", "alice", "2,400", "secret", "object", "user_id"):
        assert leak not in flat
    assert snap["events"]["ingest"]["sums"]["facts"] == 3.0   # 2 + 1
    assert snap["events"]["ingest"]["n"] == 2


def test_disabled_by_default_never_sends():
    cfg = T.TelemetryConfig.load()
    assert cfg.enabled is False and not cfg.exists()
    sent = []
    c = T.Collector(); c.record("recall", {"subgraph_edges": 3})
    # disabled → no send even with an endpoint
    cfg.endpoint = "https://example/collect"
    assert T.flush_if_due(cfg, c, poster=lambda u, p: sent.append(p)) is False
    assert sent == []


def test_enabled_but_no_endpoint_never_sends():
    cfg = T.set_enabled(True)                      # opted in, but no endpoint
    sent = []
    c = T.Collector(); c.record("recall", {"subgraph_edges": 3})
    assert T.flush_if_due(cfg, c, poster=lambda u, p: sent.append(p)) is False
    assert sent == []


def test_flush_when_due_sends_content_free_payload():
    cfg = T.set_enabled(True, endpoint="https://example/collect")
    captured = {}
    c = T.Collector()
    c.record("answer", {"abstained": True, "ms": 120})
    ok = T.flush_if_due(cfg, c, poster=lambda url, payload: captured.update(payload=payload, url=url))
    assert ok
    p = captured["payload"]
    assert p["install_id"] == cfg.install_id and p["schema_version"] == T.SCHEMA_VERSION
    assert p["events"]["answer"]["sums"]["abstained"] == 1.0
    # anonymity: no user data anywhere
    assert "user" not in json.dumps(p).lower()
    # not sent again immediately (interval gate)
    assert T.flush_if_due(cfg, c, poster=lambda u, x: None) is False


def test_consent_prompt_noninteractive_defaults_disabled():
    cfg = T.prompt_consent(interactive=False)      # e.g. CI / stdio transport
    assert cfg.enabled is False and cfg.install_id and cfg.exists()


def test_memory_emits_when_telemetry_wired():
    scripts = [
        {"triples": [{"subject": "user", "relation": "has_pet", "object": "cat", "volatility": "durable"}],
         "episode": "has a cat"},
        "I don't know.",
    ]
    class Fake:
        def __init__(s): s.i = 0
        def __call__(s, prompt, *, system=None, role="compile", json_schema=None):
            o = scripts[s.i]; s.i += 1
            return o if isinstance(o, str) else json.dumps(o)
    with tempfile.TemporaryDirectory() as d:
        coll = T.Collector()
        mem = Memory(llm=Fake(), telemetry=coll,
                     config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=0))
        mem.remember("u", "USER: I have a cat.", date="2026-06-01")
        mem.answer("u", "what car do I drive?")
        snap = coll.snapshot()
        assert snap["events"]["ingest"]["sums"]["facts"] == 1.0
        assert snap["events"]["answer"]["sums"]["abstained"] == 1.0  # detected locally
        # preview is content-free
        assert "cat" not in json.dumps(mem.telemetry_preview())
        mem.close()


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
