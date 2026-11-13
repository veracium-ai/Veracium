"""specs/0031 §4a-ii (v22.1): what the MCP server reports about itself.

V-SERVERINFO: the `initialize` result's serverInfo is veracium's own, read from the handshake itself (never from an SDK
attribute), so it fails if the way the version is set stops working. V-START-FAILURE: a start failure states its own
cause, with its remedy, and names no provider key.
"""
import importlib.metadata as md
import sqlite3

import pytest

from veracium import Memory, MemoryConfig
from veracium import mcp_server


@pytest.fixture(autouse=True)
def _needs_the_mcp_sdk():
    """Each cell needs the optional MCP SDK; skipped per cell, never the module at collection."""
    pytest.importorskip("mcp")


def _own():
    """What serverInfo.version must be, derived here from §4a-ii's rule and not from the product's helper: the
    installed veracium's version, or the source-tree marker where there is no distribution metadata. Looked up at call
    time, so the metadata="absent" cells' patch applies. (Shipped-changes round 4, research's dry-run-3 leg: the cells
    called version("veracium") unconditionally and raised in a source tree run with PYTHONPATH=src.)"""
    try:
        return md.version("veracium")
    except md.PackageNotFoundError:
        return mcp_server.SOURCE_TREE_VERSION


@pytest.fixture(params=["installed", "absent"])
def metadata(request, monkeypatch):
    """Each handshake cell runs with veracium's distribution metadata as the run has it, and again with it absent (a
    source tree on PYTHONPATH), so neither configuration depends on how the suite was installed."""
    if request.param == "absent":
        real = md.version

        def version(name):
            if name == "veracium":
                raise md.PackageNotFoundError(name)
            return real(name)
        monkeypatch.setattr(md, "version", version)
    return request.param


def _handshake_server_info(server):
    # anyio arrives with the MCP SDK, an optional extra: imported here, never at module level (the pydantic-floor lane
    # installs neither, and a module-level import fails its collection before the per-cell skip can run)
    import anyio
    from mcp.shared.memory import create_connected_server_and_client_session

    async def go():
        low = getattr(server, "_mcp_server", None) or server
        async with create_connected_server_and_client_session(low) as client:
            result = await client.initialize()
            return result.serverInfo
    return anyio.run(go)


def test_serverinfo_is_veracium_and_its_version_by_the_handshake(tmp_path, metadata):
    m = Memory(llm=lambda *a, **k: "", config=MemoryConfig(db_path=str(tmp_path / "v.db")))
    info = _handshake_server_info(mcp_server.build_server(m))
    assert info.name == "veracium"
    assert info.version == _own() and info.version != md.version("mcp"), (metadata, info.version, md.version("mcp"))
    if metadata == "absent":
        assert info.version == mcp_server.SOURCE_TREE_VERSION, info.version
    m.close()


def test_with_the_version_left_unset_the_handshake_reports_the_sdks_own(tmp_path, monkeypatch, metadata):
    """V-SERVERINFO's RED, as a control the check must tell apart: the SDK's fallback is its own package version."""
    monkeypatch.setattr(mcp_server, "_set_server_version", lambda server: None)
    m = Memory(llm=lambda *a, **k: "", config=MemoryConfig(db_path=str(tmp_path / "v.db")))
    info = _handshake_server_info(mcp_server.build_server(m))
    assert info.version == md.version("mcp") != _own(), (metadata, info.version)
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
