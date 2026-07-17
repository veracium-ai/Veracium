"""MCP server — exposes veracium to any MCP-compatible agent (Claude Desktop/Code,
others) with no Python on the host side.

    pip install veracium[mcp,anthropic]
    ANTHROPIC_API_KEY=... VERACIUM_DB_PATH=~/.veracium.db veracium-mcp

Config via env: VERACIUM_DB_PATH (default veracium.db), VERACIUM_USER (default user id
when a tool call omits one). The server owns its own model access (Anthropic
reference provider by default); a host that would rather veracium use its own model
can wrap this module's tool implementations around a custom `Complete` callable.

The tool *implementations* below are plain functions taking a `Memory`, so they're
unit-testable without a running server or an installed MCP SDK.
"""

from __future__ import annotations

import os
from typing import Optional

from . import Memory, MemoryConfig
from .schema import EvidenceAuthor

_AUTHOR = {"user": EvidenceAuthor.USER,
           "third_party": EvidenceAuthor.THIRD_PARTY,
           "system": EvidenceAuthor.SYSTEM}


# -- tool implementations (testable; no MCP/LLM dependency of their own) ------

def remember_impl(mem: Memory, user_id: str, text: str, author: str = "user",
                  event_type: str = "chat", date: Optional[str] = None,
                  derived_from: Optional[str] = None) -> dict:
    return mem.remember(user_id, text, author=_AUTHOR.get(author, EvidenceAuthor.USER),
                        event_type=event_type, date=date,
                        derived_from=_AUTHOR.get(derived_from) if derived_from else None)


def recall_impl(mem: Memory, user_id: str, query: str,
                token_budget: Optional[int] = None) -> str:
    out = mem.recall(user_id, query, token_budget=token_budget).context
    mem.flush_telemetry()  # in-process weekly push; no-ops until due, never raises
    return out


def answer_impl(mem: Memory, user_id: str, query: str) -> str:
    return mem.answer(user_id, query)


def maintain_impl(mem: Memory, user_id: str) -> dict:
    return mem.maintain(user_id)


# -- server wiring ------------------------------------------------------------

def build_memory() -> Memory:
    from .llm.anthropic import AnthropicComplete
    from . import telemetry, diagnostics
    # Respect the user's recorded telemetry choice (default off). Consent is set
    # out-of-band via `veracium telemetry` (the MCP stdio transport isn't a TTY, so
    # we never prompt here); prompt_consent just ensures a disabled config exists.
    telemetry.prompt_consent()
    diagnostics.prompt_consent()  # advance-permission choice for auto-sending logs
    # A Reporter logs genuine errors to a local, user-owned file. It only SENDS a
    # log if the operator granted advance permission via `veracium diagnostics enable`
    # (stdio isn't a TTY, so it never prompts); otherwise the log stays local and can
    # be sent later with `veracium diagnostics report`.
    return Memory(llm=AnthropicComplete(),
                  config=MemoryConfig(db_path=os.environ.get("VERACIUM_DB_PATH", "veracium.db")),
                  telemetry=telemetry.load_collector_if_enabled(),
                  diagnostics=diagnostics.load_reporter())


def build_server(mem: Memory, *, default_user: str = "default"):
    """Construct the FastMCP server with veracium's tools registered. Separated from
    main() so the wiring is testable without starting the stdio loop."""
    from mcp.server.fastmcp import FastMCP
    server = FastMCP("veracium",
                     instructions="Provenance-aware memory for AI agents.")

    @server.tool()
    def remember(text: str, user_id: str = default_user, author: str = "user",
                 event_type: str = "chat", date: Optional[str] = None,
                 derived_from: Optional[str] = None) -> dict:
        """Store an interaction event in the user's long-term memory.

        Set author="third_party" for content the user did NOT author (received
        email, external documents, tool output about the user) — this quarantines
        any claims it makes so they are never asserted as fact. Use author="user"
        for the user's own messages and sent mail. If the event is yours but its
        TEXT embeds lower-trust content (a summary quoting a received email's
        subject or body), set derived_from="third_party" — trust is capped at the
        minimum of the two, so quoted material can never become an asserted fact.
        `date` is the ISO date the event occurred (defaults to today)."""
        return remember_impl(mem, user_id, text, author=author, event_type=event_type,
                             date=date, derived_from=derived_from)

    @server.tool()
    def recall(query: str, user_id: str = default_user,
               token_budget: Optional[int] = None) -> str:
        """Retrieve grounded memory relevant to a query, as a context block to
        drop into your prompt. Verified facts and history are stated plainly;
        unverified third-party claims appear under an explicit never-assert marker.
        `token_budget` (approximate) caps the block's size — query-matched facts
        and claim flags are kept in preference to the wiki and old episodes."""
        return recall_impl(mem, user_id, query, token_budget=token_budget)

    @server.tool()
    def answer(query: str, user_id: str = default_user) -> str:
        """Answer a question directly from the user's memory, with grounding
        discipline: answers only from verified memory, never asserts unverified
        third-party claims as fact, and says it doesn't know rather than guessing."""
        return answer_impl(mem, user_id, query)

    @server.tool()
    def maintain(user_id: str = default_user) -> dict:
        """Run memory maintenance: expire stale transient facts, flag possibly-
        stale durable ones, and consolidate old history. Call periodically (e.g.
        once a day)."""
        return maintain_impl(mem, user_id)

    return server


_USAGE = """\
veracium-mcp — Provenance-aware memory for AI agents, as an MCP stdio server.

This command is not interactive: it speaks MCP over stdin/stdout and is meant
to be launched BY an MCP client (Claude Desktop, Claude Code, ...). Point your
client's config at this executable — config JSON and tool reference:
https://docs.veracium.ai/mcp/

Environment:
  ANTHROPIC_API_KEY   key for the reference LLM provider (required)
  VERACIUM_DB_PATH    SQLite store path        (default: veracium.db)
  VERACIUM_USER       default user id for tools (default: "default")

Options:
  -h, --help     show this help and exit
  --version      print the installed veracium version and exit
"""


def main(argv=None) -> None:
    import sys
    args = sys.argv[1:] if argv is None else argv
    if "-h" in args or "--help" in args:
        print(_USAGE)
        return
    if "--version" in args:
        from importlib.metadata import version
        print(version("veracium"))
        return
    if args:
        raise SystemExit(f"veracium-mcp: unknown argument {args[0]!r} (see --help). "
                         "This server takes no positional arguments; it is "
                         "configured via environment variables.")
    try:
        import mcp.server.fastmcp  # noqa: F401
    except ImportError as e:  # pragma: no cover
        raise SystemExit("The MCP server needs the SDK: pip install veracium[mcp]") from e
    try:
        mem = build_memory()
    except Exception as e:
        raise SystemExit(f"veracium-mcp: failed to start: {e}\n"
                         "(Is ANTHROPIC_API_KEY set? Run veracium-mcp --help.)") from e
    build_server(mem, default_user=os.environ.get("VERACIUM_USER", "default")).run()


if __name__ == "__main__":
    main()
