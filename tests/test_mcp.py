"""MCP tool-implementation logic (offline — no mcp/anthropic SDK needed).

Verifies the tools map onto Memory correctly, including the security-critical
author routing (third_party → quarantine)."""

import pytest
import json
import tempfile

from veracium import Memory, MemoryConfig
from veracium.mcp_server import remember_impl, recall_impl, answer_impl, maintain_impl


class Fake:
    def __init__(self, scripts):
        self._s = list(scripts); self.i = 0
    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        out = self._s[self.i]; self.i += 1
        return out if isinstance(out, str) else json.dumps(out)


def test_mcp_tools_route_correctly():
    scripts = [
        {"triples": [{"subject": "user", "relation": "has_pet", "object": "cat named Minerva", "volatility": "durable"}],
         "episode": "User mentioned a cat named Minerva."},
        {"triples": [{"subject": "org:scam", "relation": "third_party_claim", "object": "user owes $500"}],
         "episode": "Received an unverified notice claiming $500 owed."},
        "no",  # gate answer for the scam probe
    ]
    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=Fake(scripts),
                     config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=0))

        # user-authored fact
        r = remember_impl(mem, "u", "USER: I have a cat named Minerva.", author="user", date="2026-06-01")
        assert r["facts"] == 1 and r["quarantined"] == 0

        # third-party content → quarantined, never a fact
        r2 = remember_impl(mem, "u", "From scam: you owe $500.", author="third_party",
                           event_type="email", date="2026-06-02")
        assert r2["quarantined"] == 1 and r2["facts"] == 0

        # recall surfaces the pet; the claim is fenced
        ctx = recall_impl(mem, "u", "does the user have a pet, and do they owe money?")
        assert "Minerva" in ctx and "never assert" in ctx.lower()

        # answer routes through the gate
        assert answer_impl(mem, "u", "does the user owe $500?") == "no"

        # maintain runs
        assert "expiry" in maintain_impl(mem, "u")
        mem.close()


def test_mcp_server_wiring():
    """The FastMCP server registers veracium's tools (skipped if mcp SDK absent)."""
    import asyncio
    import pytest
    pytest.importorskip("mcp")
    from veracium.mcp_server import build_server
    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=Fake(["{}"]),
                     config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=0))
        server = build_server(mem, default_user="alice")
        names = sorted(t.name for t in asyncio.run(server.list_tools()))
        assert names == ["answer", "maintain", "recall", "remember"]
        mem.close()


if __name__ == "__main__":
    test_mcp_tools_route_correctly()
    print("mcp OK")


def test_mcp_entrypoint_help_and_version(capsys):
    # `veracium-mcp --help` must explain itself and exit cleanly — it used to
    # ignore argv and silently boot the stdio server (launch-prep finding).
    from veracium.mcp_server import main
    main(["--help"])
    out = capsys.readouterr().out
    assert "MCP stdio server" in out and "ANTHROPIC_API_KEY" in out
    main(["--version"])
    assert capsys.readouterr().out.strip()  # prints the installed version

    import pytest
    with pytest.raises(SystemExit, match="unknown argument"):
        main(["serve"])


# --- the model must not be able to declare its own evidence class -----------

def test_the_mcp_surface_refuses_system_authorship():
    """`remember` is an @server.tool(), so the MODEL calls it and `author` is a
    free parameter. Mapping "system" there let a model declare its own evidence
    class — self-elevation from ASSISTANT (rung 1) to SYSTEM (rung 2) on the
    supersession authority ladder, across the boundary the generated-content
    class exists to establish.

    The general rule, and the same one that keeps `derived_from` capping-only:
    a trust-bearing field must not be settable by the party whose trust it
    describes.
    """
    import tempfile
    from veracium import Memory, MemoryConfig
    from veracium.mcp_server import _AUTHOR, remember_impl

    assert "system" not in _AUTHOR
    assert set(_AUTHOR) == {"user", "third_party"}

    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=None, config=MemoryConfig(db_path=f"{d}/m.db",
                                                   wiki_recompile_after_writes=0))
        with pytest.raises(ValueError, match="not accepted here"):
            remember_impl(mem, "u", "the deploy succeeded", author="system")
        mem.close()


def test_an_unrecognised_author_fails_closed_not_to_user():
    """The trap in the fix itself: the lookup was
    `_AUTHOR.get(author, EvidenceAuthor.USER)`, so removing "system" from the map
    would have resolved it to USER — the HIGHEST authority — making the
    self-elevation worse rather than blocking it."""
    import tempfile
    from veracium import Memory, MemoryConfig
    from veracium.mcp_server import remember_impl

    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=None, config=MemoryConfig(db_path=f"{d}/m.db",
                                                   wiki_recompile_after_writes=0))
        for bad in ("system", "assistant", "admin", "", "USER"):
            with pytest.raises(ValueError):
                remember_impl(mem, "u", "x", author=bad)
        with pytest.raises(ValueError, match="derived_from"):
            remember_impl(mem, "u", "x", author="user", derived_from="system")
        mem.close()
