"""`veracium mcp`: the MCP stdio server under the distribution's own name, for the MCP registry.

The registry launches a PyPI package by its identifier, which must be `veracium`; `veracium-mcp` is a second console
script it cannot name. So `veracium mcp` must BE `veracium-mcp`: the same help, version and refusals, and the same
server over real stdio, launched the way the registry's entry launches it (a fresh interpreter, the `mcp` argument,
configuration only by environment variables).
"""
import json
import os
import sys
from pathlib import Path

import pytest

import veracium
from veracium import mcp_server
from veracium.cli import main as cli_main


def _out(capsys, fn, *args):
    fn(*args)
    return capsys.readouterr().out


def test_help_and_version_are_the_servers_own(capsys):
    assert _out(capsys, cli_main, ["mcp", "--help"]) == _out(capsys, mcp_server.main, ["--help"])
    assert "MCP stdio server" in _out(capsys, cli_main, ["mcp", "--help"])
    version = _out(capsys, cli_main, ["mcp", "--version"])
    assert version.strip() and version == _out(capsys, mcp_server.main, ["--version"])


@pytest.mark.parametrize("args", [["serve"], ["--db", "x.db"], ["--help-me"]])
def test_an_argument_the_server_does_not_take_refuses_as_it_does(args):
    with pytest.raises(SystemExit) as via_cli:
        cli_main(["mcp", *args])
    with pytest.raises(SystemExit) as direct:
        mcp_server.main(args)
    assert str(via_cli.value) == str(direct.value) and "unknown argument" in str(via_cli.value)


def test_the_cli_lists_the_subcommand(capsys):
    with pytest.raises(SystemExit) as done:
        cli_main(["--help"])
    assert done.value.code == 0
    assert "mcp" in capsys.readouterr().out.split("positional arguments:", 1)[1].split("options:", 1)[0]


def test_the_registry_launch_serves_the_same_tools_over_real_stdio(tmp_path):
    """A fresh interpreter runs `veracium.cli mcp` with only environment configuration, as the registry's entry does;
    an MCP client completes the handshake over its stdin/stdout and lists the tools. The listing equals the in-process
    server's, so the subcommand reaches the same server, and nothing preceded the protocol on stdout."""
    pytest.importorskip("mcp")
    import anyio  # arrives with the MCP SDK, an optional extra: imported here, never at module level
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    db = tmp_path / "registry.db"
    src = str(Path(veracium.__file__).resolve().parents[1])
    # The server builds the reference provider at start (the registry entry installs `veracium[mcp,anthropic]`); the
    # Anthropic SDK is not a test dependency, so the child gets a stand-in whose client is never called: listing tools
    # makes no model call. HOME and the XDG dirs point into tmp_path, so the start's consent defaults are written there.
    stub = tmp_path / "stub"
    (stub / "anthropic").mkdir(parents=True)
    (stub / "anthropic" / "__init__.py").write_text("class Anthropic:\n    def __init__(self, *a, **k):\n        pass\n")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("VERACIUM_", "XDG_"))}
    env.update(VERACIUM_DB_PATH=str(db), HOME=str(tmp_path), XDG_CONFIG_HOME=str(tmp_path / "config"),
               XDG_STATE_HOME=str(tmp_path / "state"), PYTHONPATH=os.pathsep.join(
                   [str(stub), src] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])))
    params = StdioServerParameters(command=sys.executable, args=["-m", "veracium.cli", "mcp"], env=env)

    # stdout is the protocol channel, and the SDK's client skips a line it cannot parse, so its handshake alone would
    # pass a banner printed before the server: read the FIRST raw stdout line, which must be the reply to initialize
    import subprocess
    import threading
    proc = subprocess.Popen([sys.executable, "-m", "veracium.cli", "mcp"], env=env, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    watchdog = threading.Timer(60, proc.kill)
    watchdog.start()
    try:
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}}) + "\n")
        proc.stdin.flush()
        first = proc.stdout.readline()
        proc.stdin.close()                  # end of input: the server returns, and anything buffered is written
        rest = proc.stdout.read()
        code = proc.wait()
    finally:
        watchdog.cancel()
        proc.kill()
        proc.wait()
    reply = json.loads(first)
    assert reply.get("id") == 1 and reply["result"]["serverInfo"]["name"] == "veracium", first
    for line in rest.splitlines():          # nothing but protocol on stdout, through exit
        json.loads(line)
    assert code == 0, (code, rest)

    async def go():
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                tools = await session.list_tools()
                return init.serverInfo.name, sorted(t.name for t in tools.tools)
    name, served = anyio.run(go)
    assert name == "veracium"

    from veracium import Memory, MemoryConfig
    m = Memory(llm=lambda *a, **k: "", config=MemoryConfig(db_path=str(tmp_path / "inproc.db")))
    try:
        server = mcp_server.build_server(m)

        async def listed():
            return sorted(t.name for t in await server.list_tools())
        expected = anyio.run(listed)
    finally:
        m.close()
    assert served == expected, json.dumps({"served": served, "in_process": expected})
    assert {"remember", "recall", "find_facts"} <= set(served)
