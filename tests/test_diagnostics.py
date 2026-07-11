"""Diagnostics / error reporting: local-first logging, consent-gated send,
redaction, and Memory capturing-then-re-raising genuine errors."""

import json

import pytest

from engram import Memory, MemoryConfig
from engram import diagnostics as D


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))


def _boom(msg="kaboom"):
    try:
        raise ValueError(msg)
    except ValueError as e:
        return e


def test_error_is_logged_locally_by_default():
    r = D.Reporter()
    assert r.config.log_enabled and not r.config.report_enabled  # local on, send off
    r.record_error("remember", _boom("boom-token"), {"user_hash": "abc123"})
    tail = r.log_tail()
    assert "op=remember" in tail and "user_hash=abc123" in tail
    assert "ValueError" in tail and "boom-token" in tail


def test_redaction_scrubs_email_and_numbers():
    r = D.Reporter()
    r.record_error("recall", _boom("failed for user alice@example.com id 4155551234"))
    tail = r.log_tail()
    assert "alice@example.com" not in tail and "<redacted-email>" in tail
    assert "4155551234" not in tail and "<redacted-number>" in tail


def test_no_endpoint_never_sends():
    r = D.Reporter()
    r.record_error("answer", _boom())
    assert r.send(interactive=False) is False           # no endpoint


def test_disabled_and_noninteractive_never_sends():
    cfg = D.DiagnosticsConfig.load()
    cfg.endpoint = "https://example/report"             # endpoint but no consent
    r = D.Reporter(cfg)
    r.record_error("answer", _boom())
    # report_enabled False + non-interactive → no consent → no send
    sent = []
    assert r.send(interactive=False, poster=lambda u, p: sent.append(p)) is False
    assert sent == []


def test_advance_permission_sends_redacted_payload():
    cfg = D.set_report_enabled(True, endpoint="https://example/report")
    r = D.Reporter(cfg)
    r.record_error("remember", _boom("secret bob@corp.com"))
    captured = {}
    ok = r.send(interactive=False, poster=lambda url, p: captured.update(url=url, p=p))
    assert ok
    p = captured["p"]
    assert p["install_id"] == cfg.install_id and p["schema_version"] == D.SCHEMA_VERSION
    assert p["engram_version"] and p["python"] and p["os"]
    assert "bob@corp.com" not in json.dumps(p) and "<redacted-email>" in p["log_tail"]


def test_auto_send_on_error_when_pre_authorized(monkeypatch):
    D.set_report_enabled(True, endpoint="https://example/report")
    sent = []
    monkeypatch.setattr(D, "_post", lambda url, payload: sent.append(payload))
    r = D.Reporter()                     # picks up the enabled config
    r.record_error("maintain", _boom("auto"))
    assert len(sent) == 1 and sent[0]["reason"] == "auto:maintain"


def test_memory_captures_then_reraises_genuine_error(tmp_path):
    class Exploding:
        def __call__(self, prompt, *, system=None, role="", json_schema=None):
            raise RuntimeError("model exploded on extract")
    reporter = D.Reporter()
    mem = Memory(llm=Exploding(), diagnostics=reporter,
                 config=MemoryConfig(db_path=str(tmp_path / "m.db")))
    with pytest.raises(RuntimeError, match="model exploded"):   # real error still surfaces
        mem.remember("u", "USER: hello")
    mem.close()
    assert reporter.has_pending()
    tail = reporter.log_tail()
    assert "op=remember" in tail and "RuntimeError" in tail
    # user id is hashed, never logged raw
    assert "\nu\n" not in tail and "user_hash=" in tail


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
