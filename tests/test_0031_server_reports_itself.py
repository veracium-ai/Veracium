"""specs/0031 §4a-ii (v22.1): what the MCP server reports about itself.

V-SERVERINFO: the `initialize` result's serverInfo is veracium's own, read from the handshake itself (never from an SDK
attribute), so it fails if the way the version is set stops working. V-START-FAILURE: a start failure states its own
cause, with its remedy, and names no provider key.
"""
import sqlite3
from importlib.metadata import version

import anyio
import pytest

from veracium import Memory, MemoryConfig
from veracium import mcp_server


@pytest.fixture(autouse=True)
def _needs_the_mcp_sdk():
    """Each cell needs the optional MCP SDK; skipped per cell, never the module at collection."""
    pytest.importorskip("mcp")


def _handshake_server_info(server):
    from mcp.shared.memory import create_connected_server_and_client_session

    async def go():
        low = getattr(server, "_mcp_server", None) or server
        async with create_connected_server_and_client_session(low) as client:
            result = await client.initialize()
            return result.serverInfo
    return anyio.run(go)


def test_serverinfo_is_veracium_and_its_version_by_the_handshake(tmp_path):
    m = Memory(llm=lambda *a, **k: "", config=MemoryConfig(db_path=str(tmp_path / "v.db")))
    info = _handshake_server_info(mcp_server.build_server(m))
    assert info.name == "veracium"
    assert info.version == version("veracium") and info.version != version("mcp"), (info.version, version("mcp"))
    m.close()


def test_with_the_version_left_unset_the_handshake_reports_the_sdks_own(tmp_path, monkeypatch):
    """V-SERVERINFO's RED, as a control the check must tell apart: the SDK's fallback is its own package version."""
    monkeypatch.setattr(mcp_server, "_set_server_version", lambda server: None)
    m = Memory(llm=lambda *a, **k: "", config=MemoryConfig(db_path=str(tmp_path / "v.db")))
    info = _handshake_server_info(mcp_server.build_server(m))
    assert info.version == version("mcp") != version("veracium")
    m.close()


def test_a_tree_without_metadata_reports_a_marker_that_names_no_release(monkeypatch):
    import importlib.metadata as md

    def missing(name):
        raise md.PackageNotFoundError(name)
    monkeypatch.setattr(md, "version", missing)
    assert mcp_server._veracium_version() == mcp_server.SOURCE_TREE_VERSION
    assert not any(c.isdigit() for c in mcp_server.SOURCE_TREE_VERSION)


def test_a_start_failure_states_its_own_cause_and_names_no_provider_key(tmp_path, monkeypatch):
    """The newer-stamped store (0054 I7's case): the refusal and its remedy, and no ANTHROPIC_API_KEY hint."""
    db = tmp_path / "newer.db"
    Memory(llm=lambda *a, **k: "", config=MemoryConfig(db_path=str(db))).close()
    c = sqlite3.connect(db)
    n = c.execute("PRAGMA user_version").fetchone()[0]
    c.execute(f"PRAGMA user_version = {n + 1}")
    c.commit()
    c.close()
    monkeypatch.setenv("VERACIUM_DB_PATH", str(db))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # the provider's SDK is an optional extra (absent in CI's lanes): stub its class so the failure is the store's
    import veracium.llm.anthropic as provider
    monkeypatch.setattr(provider, "AnthropicComplete", lambda *a, **k: (lambda *x, **y: ""))
    with pytest.raises(SystemExit) as exc:
        mcp_server.main([])
    msg = str(exc.value)
    assert msg.startswith("veracium-mcp: failed to start:"), msg
    assert "newer" in msg and "SCHEMA_VERSION" in msg, msg
    assert "ANTHROPIC_API_KEY" not in msg, msg


def test_help_still_lists_the_provider_key(capsys):
    """Control: tool calls that reach the model still need the key, so --help keeps naming it."""
    mcp_server.main(["--help"])
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().out
