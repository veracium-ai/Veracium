"""MCP server — exposes veracium to any MCP-compatible agent (Claude Desktop/Code,
others) with no Python on the host side.

    pip install veracium[mcp,anthropic]
    ANTHROPIC_API_KEY=... VERACIUM_DB_PATH=~/.veracium.db veracium-mcp

Config via env: VERACIUM_DB_PATH (default veracium.db), VERACIUM_USER (default user id
when a tool call omits one), VERACIUM_MCP_CAPABILITY (the host attestation,
specs/0031 §4a — see `HostCapability`; unset means `none`, the untrusted cell).
The server owns its own model access (Anthropic reference provider by default);
a host that would rather veracium use its own model can wrap this module's tool
implementations around a custom `Complete` callable.

The tool *implementations* below are plain functions taking a `Memory`, so they're
unit-testable without a running server or an installed MCP SDK.
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Optional

from . import Memory, MemoryConfig
from .schema import EvidenceAuthor, EvidenceContext

_log = logging.getLogger("veracium.mcp")

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
           "third_party": EvidenceAuthor.THIRD_PARTY,
           # specs/0001 §2d.6 (candidate): self-DEMOTION, not elevation —
           # rung 1, use_only; "system" stays deliberately unavailable
           "assistant": EvidenceAuthor.ASSISTANT}


class HostCapability(str, Enum):
    """What the DEPLOYMENT attests about every call on this server
    (specs/0031 §3a/§4a, Phase A). Declared once at server construction;
    not per-call and not model-reachable — it is a parameter of
    `build_server`, never of a tool, so no tool schema can carry it.

    `direct` is defined at deployment grain: every call originates in a turn
    with the authenticated principal, AND the deployment accepts the model's
    authorship labelling as its own — liability, not clairvoyance (§3a). A
    host declaring it may be lying; that is the trust boundary (§8). A host
    unwilling to stand behind its agent's labelling leaves the default.

    `none` is the untrusted cell and the ABSENCE default. Only absence
    resolves here: every SUPPLIED value outside the closed set — including
    the empty string, which is a typo, not an absence — raises at
    construction, so a mistyped attestation fails loudly instead of running
    un-attested while believing it is attesting (§4a, F3).
    """
    NONE = "none"
    DIRECT = "direct"


def _resolve_capability(value) -> HostCapability:
    """`None` → NONE (absence). Anything else → `HostCapability(value)`, which
    raises outside the closed set. The enum call IS the validator — there is
    no second one to drift out of step (the `validate_semantic` lesson)."""
    if value is None:
        return HostCapability.NONE
    return HostCapability(value)


# The author BASELINE each capability establishes (§4a "author loses its
# default"): both trust legs draw from this ONE carrier. Under `none` the
# baseline is `third_party`, not `assistant` — `assistant` scores authority 1
# and would be safe only because the derived_from floor's `min` masks it,
# which is precisely the structure round-2 F2 found. A baseline must be
# jointly minimal on its own.
_BASELINE_AUTHOR = {HostCapability.NONE: "third_party",
                    HostCapability.DIRECT: "user"}


# -- tool implementations (testable; no MCP/LLM dependency of their own) ------

def _closed_set(field: str, value) -> None:
    """Step 2 of the pipeline: a SUPPLIED value is validated against its closed
    domain and a malformed one RAISES regardless of capability (§2c-i: the
    closed-set check "still RAISES rather than defaulting"). Wrong types are
    malformed too — `123 in _AUTHOR` is False, an unhashable value would raise
    TypeError from the lookup; both are refusals, made explicit here."""
    if not isinstance(value, str) or value not in _AUTHOR:
        if field == "author":
            raise ValueError(
                f"author={value!r} is not accepted here. Use "
                f"{sorted(_AUTHOR)}. 'system' is deliberately unavailable through "
                f"the MCP surface: it denotes veracium's own maintenance output, "
                f"and a trust-bearing field must not be settable by the party whose "
                f"trust it describes.")
        raise ValueError(
            f"derived_from={value!r} is not accepted. Use "
            f"{sorted(_AUTHOR)} or omit it.")


def remember_report(mem: Memory, user_id: str, text: str,
                    author: Optional[str] = None, event_type: str = "chat",
                    date: Optional[str] = None,
                    derived_from: Optional[str] = None, *,
                    capability=None) -> dict:
    """The FULL write report — the library-level surface a host embedding these
    functions reads — including the operator counter
    `provenance_raises_discarded`. `remember_impl` is this with the operator
    counters stripped for the tool result.

    specs/0031 §4a (Phase A), the pipeline in order:
      1. absence vs presence — `author=None` / `derived_from=None` is ABSENT;
      2. a SUPPLIED value is validated against its closed set; malformed
         RAISES regardless of capability;
      3. valid values are compared with the capability's baseline;
      4. only a prohibited ELEVATION is discarded — under `none` every
         non-identity value is one (the baseline is the bottom element, §2c-i);
         under `direct` the baseline is the top, so every closed-set value is
         a RESTRICTION and is honoured;
      5. each discard is counted: `provenance_raises_discarded` increments
         once per valid supplied field discarded as an attempted elevation.
         Invalid values raised and were never classified — not counted. An
         equal restatement of the baseline is inert but not an attempted
         raise — not counted. A restriction under `direct` is honoured — not
         counted;
      6. only the effective values are persisted, through the §3a PINNED
         bridge: `direct` + nothing → `EvidenceContext.direct()`; `direct` +
         `derived_from=X` → `EvidenceContext.derived(X)` (the restriction
         honoured THROUGH the declaration, one carrier); `none` → the
         absent-context floor, no context and no derived_from. Never both
         carriers (`_resolve_context` raises on two declarations of one fact).
    """
    cap = _resolve_capability(capability)
    baseline = _BASELINE_AUTHOR[cap]
    discarded = 0
    # -- author leg --------------------------------------------------------
    if author is None:
        effective_author = baseline                       # V-AUTHOR-BASELINE
    else:
        _closed_set("author", author)
        if cap is HostCapability.NONE:
            effective_author = baseline                   # inert (V-INERT-UNDER-NONE)
            if author != baseline:
                discarded += 1                            # attempted elevation
        else:
            effective_author = author                     # restrict-only, honoured
    # -- derived leg + the bridge ----------------------------------------------
    if derived_from is not None:
        _closed_set("derived_from", derived_from)
    if cap is HostCapability.NONE:
        context = None                                    # the absent-context floor
        if derived_from is not None and derived_from != "third_party":
            discarded += 1                                # attempted elevation
    elif derived_from is None:
        context = EvidenceContext.direct()                # bridge row 1
    else:
        context = EvidenceContext.derived(_AUTHOR[derived_from])   # bridge row 2
    r = dict(mem.remember(user_id, text, author=_AUTHOR[effective_author],
                          event_type=event_type, date=date, context=context))
    # present on EVERY returned path, zero included — an absent key is not a
    # zero (the shipped `agreement_floored` shape; specs/0031 §4d)
    r["provenance_raises_discarded"] = discarded
    return r


# The operator counters stripped from the TOOL result. specs/0015 §3b/I11: the
# per-write supersession/reinforcement counts are a SUPERSESSION ORACLE over
# prior store state; specs/0025 §4c: the five public counters are a LIBRARY
# surface; specs/0023 Q4: trust-state audit facts; specs/0026 §3d: operator
# counters; specs/0031 §4d: the discarded-raise counter — a model that learns
# how often its elevation attempts are refused learns to probe.
_OPERATOR_ONLY = ("supersessions", "reinforcements",
                  "invalid", "retried", "recovered", "residual",
                  "redispositioned",
                  "quarantined_at_birth", "birth_revocation_digest",
                  "agreement_floored", "agreement_recorded",
                  "provenance_raises_discarded")


def remember_impl(mem: Memory, user_id: str, text: str,
                  author: Optional[str] = None, event_type: str = "chat",
                  date: Optional[str] = None,
                  derived_from: Optional[str] = None, *,
                  capability=None) -> dict:
    """The tool result: `remember_report` minus every operator counter."""
    r = remember_report(mem, user_id, text, author=author, event_type=event_type,
                        date=date, derived_from=derived_from,
                        capability=capability)
    for k in _OPERATOR_ONLY:
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


def build_server(mem: Memory, *, default_user: str = "default", capability=None):
    """Construct the MCP server with veracium's tools registered. Separated from
    main() so the wiring is testable without starting the stdio loop.

    `capability` (specs/0031 §4a, keyword-only): the host attestation, `None`
    meaning ABSENT → `HostCapability.NONE`. Resolved ONCE here and retained by
    the tool closures — never re-read per request, so one server lifetime
    cannot span two baselines. This function never reads the environment;
    `main()` reads it once and passes the value, so each deployment path has
    exactly one configuration carrier. It is excluded from every tool schema
    BY CONSTRUCTION: the framework reflects the `@server.tool()` signatures,
    and this is not one of them (`test_capability_is_host_only` makes the
    construction claim falsifiable against the reflected schema).
    """
    cap = _resolve_capability(capability)
    server = _server_cls()("veracium",
                           instructions="Provenance-aware memory for AI agents.")
    # The effective capability, to OPERATORS only (specs/0031 punch-list I3):
    # stderr-bound logging, never a tool surface.
    _log.info("veracium-mcp: host capability %r (declared once at construction; "
              "not model-reachable)", cap.value)

    # specs/0031 §4b-iii, pinned: `user_id` comes OFF the served tool schemas.
    # The host process is the identity boundary (§4e); a model-supplied
    # user_id bound nothing, so it is absent BY SCHEMA — no value to validate,
    # nothing to refuse. The deployment-scoped user is `default_user`,
    # captured at construction (all four tools; see recall below).
    @server.tool()
    def remember(text: str, author: Optional[str] = None,
                 event_type: str = "chat", date: Optional[str] = None,
                 derived_from: Optional[str] = None) -> dict:
        """Store an interaction event in the user's long-term memory.

        Provenance is set by the DEPLOYMENT's attestation, not by this call:
        when `author` is omitted the event takes the deployment's baseline
        class, and a supplied `author` or `derived_from` can only RESTRICT
        trust below that baseline, never raise it (an attempted raise is
        discarded). Set author="third_party" for content the user did NOT
        author (received email, external documents, tool output about the
        user) — this quarantines any claims it makes so they are never
        asserted as fact. Set author="assistant" for your own output. If the
        event's TEXT embeds lower-trust content (a summary quoting a received
        email's subject or body), set derived_from="third_party" — trust is
        capped at the minimum, so quoted material can never become an
        asserted fact. `date` is the ISO date the event occurred (defaults to
        today)."""
        return remember_impl(mem, default_user, text, author=author,
                             event_type=event_type, date=date,
                             derived_from=derived_from, capability=cap)

    # specs/0031 §4b-iii applies to EVERY served tool (research's adjudication,
    # 2026-09-04): a model-suppliable user_id on RECALL is a cross-principal
    # READ — the identity boundary defeated worse than on a write.
    @server.tool()
    def recall(query: Optional[str] = None,
               token_budget: Optional[int] = None) -> str:
        """Retrieve grounded memory relevant to a query, as a context block to
        drop into your prompt. Verified facts and history are stated plainly;
        unverified third-party claims appear under an explicit never-assert marker.
        `token_budget` (approximate) caps the block's size — query-matched facts
        and claim flags are kept in preference to the wiki and old episodes.
        Omit `query` for a session-start briefing: commitments coming due,
        facts to confirm, current context, recent history (verified facts
        only — nothing unverified is ever volunteered unprompted)."""
        return recall_impl(mem, default_user, query, token_budget=token_budget)

    @server.tool()
    def answer(query: str) -> str:
        """Answer a question directly from the user's memory, with grounding
        discipline: answers only from verified memory, never asserts unverified
        third-party claims as fact, and says it doesn't know rather than guessing."""
        return answer_impl(mem, default_user, query)

    @server.tool()
    def maintain() -> dict:
        """Run memory maintenance: expire stale transient facts, flag possibly-
        stale durable ones, and consolidate old history. Call periodically (e.g.
        once a day)."""
        return maintain_impl(mem, default_user)

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
  VERACIUM_MCP_CAPABILITY
                      the HOST's attestation about every call on this server
                      (specs/0031 §4a). Unset = "none": model-supplied
                      provenance can only restrict, and events default to the
                      third-party class. "direct" = every call originates in a
                      turn with the authenticated principal AND this deployment
                      stands behind the model's authorship labelling as its
                      own; events then default to the user's class. Read ONCE
                      at startup. Any other value — the empty string included —
                      refuses to start. This is attested by the host, NOT
                      verified by veracium: a server reachable by a public or
                      untrusted agent must leave it unset.

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
    # The environment is read ONCE, here, and passed in (specs/0031 §4a; the
    # punch-list's A6 precedence rule). `os.environ.get` yields None when the
    # variable is UNSET (absence → none) and "" when it is set empty (supplied
    # and invalid → build_server raises) — the two are deliberately distinct.
    try:
        server = build_server(
            mem, default_user=os.environ.get("VERACIUM_USER", "default"),
            capability=os.environ.get("VERACIUM_MCP_CAPABILITY"))
    except ValueError as e:
        raise SystemExit(
            f"veracium-mcp: refusing to start: VERACIUM_MCP_CAPABILITY="
            f"{os.environ.get('VERACIUM_MCP_CAPABILITY')!r} is not one of "
            f"{[c.value for c in HostCapability]} (unset it for 'none'). "
            f"A mistyped attestation must fail here, not run un-attested.") from e
    server.run()


if __name__ == "__main__":
    main()
