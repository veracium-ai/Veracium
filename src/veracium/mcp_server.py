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

# `"system"` is deliberately ABSENT. `remember` is an @server.tool(), so the
# MODEL calls it and `author` is a free parameter — mapping "system" here let a
# model declare its own evidence class as SYSTEM. Under the supersession
# authority ladder (USER 3 > SYSTEM 2 > ASSISTANT 1 > THIRD_PARTY 0) that is
# self-elevation from rung 1 to rung 2, across the boundary the generated-content
# class exists to establish.
#
# The general rule, which is the same one that keeps `derived_from` capping-only:
# **a trust-bearing field must not be settable by the party whose trust it
# describes.** SYSTEM means veracium's own maintenance output; nothing arriving
# through a model-facing tool is that, by definition.
#
# An unrecognised value raises rather than defaulting — failing closed, because a
# silent fallback to USER would be the worst possible default here.
_AUTHOR = {"user": EvidenceAuthor.USER,
           "third_party": EvidenceAuthor.THIRD_PARTY}


# -- tool implementations (testable; no MCP/LLM dependency of their own) ------

def remember_impl(mem: Memory, user_id: str, text: str, author: str = "user",
                  event_type: str = "chat", date: Optional[str] = None,
                  derived_from: Optional[str] = None) -> dict:
    # Fail CLOSED on an unrecognised author. This used to be
    # `_AUTHOR.get(author, EvidenceAuthor.USER)` — a silent fallback to the
    # HIGHEST-authority class, so a typo, a stale caller, or a model asking for
    # a class it is not entitled to would all land on USER. Removing "system"
    # from the map without this would have made the self-elevation worse, not
    # better: "system" would have resolved to USER.
    if author not in _AUTHOR:
        raise ValueError(
            f"author={author!r} is not accepted here. Use "
            f"{sorted(_AUTHOR)}. 'system' is deliberately unavailable through "
            f"the MCP surface: it denotes veracium's own maintenance output, "
            f"and a trust-bearing field must not be settable by the party whose "
            f"trust it describes.")
    if derived_from is not None and derived_from not in _AUTHOR:
        raise ValueError(
            f"derived_from={derived_from!r} is not accepted. Use "
            f"{sorted(_AUTHOR)} or omit it.")
    r = dict(mem.remember(user_id, text, author=_AUTHOR[author],
                          event_type=event_type, date=date,
                          derived_from=_AUTHOR[derived_from] if derived_from else None))
    # specs/0015 §3b/I11: the per-write supersession/reinforcement counts are a
    # SUPERSESSION ORACLE over prior store state; the model caller is the one
    # principal that cannot otherwise derive them. Never in the tool result.
    r.pop("supersessions", None)
    r.pop("reinforcements", None)
    # specs/0025 §4c: the five public counters are a LIBRARY surface, not a
    # tool-call surface — stripped here consistent with the two above.
    for k in ("invalid", "retried", "recovered", "residual",
              "redispositioned",
              # specs/0023 Q4: trust-state audit facts — never in the
              # tool result the model caller reads
              "quarantined_at_birth", "birth_revocation_digest"):
        r.pop(k, None)
    return r


def recall_impl(mem: Memory, user_id: str, query: Optional[str] = None,
                token_budget: Optional[int] = None, principal=None) -> str:
    # specs/0020 §4f: MCP passes the HOST's declared principal THROUGH — it
    # never invents one, and no new MCP tool FIELD is added. The registered
    # tool below therefore calls this with `principal=None`, which is the
    # §5 adoption-path honesty row: the default MCP stream supplies no
    # identities, so NO isolation exists on it. A host embedding these
    # `*_impl` functions in its own server passes its principal here.
    out = mem.recall(user_id, query, token_budget=token_budget,
                     principal=principal).context
    mem.flush_telemetry()  # in-process weekly push; no-ops until due, never raises
    return out


def answer_impl(mem: Memory, user_id: str, query: str, principal=None) -> str:
    return mem.answer(user_id, query, principal=principal)


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


def _server_cls():
    """SDK 2.0 renamed FastMCP to MCPServer (same decorator API); support both."""
    try:
        from mcp.server.mcpserver import MCPServer  # mcp >= 2.0
        return MCPServer
    except ImportError:
        from mcp.server.fastmcp import FastMCP  # mcp 1.x
        return FastMCP


def build_server(mem: Memory, *, default_user: str = "default"):
    """Construct the MCP server with veracium's tools registered. Separated from
    main() so the wiring is testable without starting the stdio loop."""
    server = _server_cls()("veracium",
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
    def recall(query: Optional[str] = None, user_id: str = default_user,
               token_budget: Optional[int] = None) -> str:
        """Retrieve grounded memory relevant to a query, as a context block to
        drop into your prompt. Verified facts and history are stated plainly;
        unverified third-party claims appear under an explicit never-assert marker.
        `token_budget` (approximate) caps the block's size — query-matched facts
        and claim flags are kept in preference to the wiki and old episodes.
        Omit `query` for a session-start briefing: commitments coming due,
        facts to confirm, current context, recent history (verified facts
        only — nothing unverified is ever volunteered unprompted)."""
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
        # Distribution metadata is absent from a bare source tree -- a checkout,
        # or the review archive, where `--version` raised PackageNotFoundError
        # and took the whole suite down. A version report should degrade, not
        # fail: the code is present either way and its version is knowable.
        from importlib.metadata import PackageNotFoundError, version
        try:
            print(version("veracium"))
        except PackageNotFoundError:
            # Deliberately NOT a `__version__` constant. pyproject.toml is the
            # single source of the version, and adding a second copy in code is
            # the drift this project has spent a week removing. An uninstalled
            # tree honestly has no version -- say so.
            print("veracium (source tree — no distribution metadata; "
                  "install the package for a version)")
        return
    if args:
        raise SystemExit(f"veracium-mcp: unknown argument {args[0]!r} (see --help). "
                         "This server takes no positional arguments; it is "
                         "configured via environment variables.")
    try:
        _server_cls()
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
