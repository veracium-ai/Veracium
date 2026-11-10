"""veracium's served tools as Pydantic AI tools (specs/0053; `pip install "veracium[pydantic_ai]"`).

    from pydantic_ai import Agent
    from veracium.adapters.pydantic_ai import as_tools
    agent = Agent(model, tools=as_tools(mem, user_id="alice", capability="direct", source_id="chat-app"))

Every tool is the served MCP tool: the same name, the same parameters (the JSON schema FastMCP reflects, handed to
`Tool.from_schema`) and the same description, byte for byte. The descriptions are model-facing safety text; a provider
path that caps one below its length is a different surface, and the conformance suite fails it by name.

The user, the capability (0031 §4a), the source (0006 I1) and the principal (0020) are the HOST's, bound here and never
a tool argument. A refusal comes back as the library's data (`{"ok": false, "refusal": …}`). Any error raised while
answering comes back through Pydantic AI's tool-error channel, `ModelRetry`, carrying its message verbatim: the model
reads it through its provider's tool-error channel (`{"error": <message>}` where the provider has none, as FastMCP
reports a tool error on MCP), and the error does not crash the agent loop (within the retry budget below). The adapter
retries nothing, rewords nothing and answers nothing with another model; the framework then offers the model another
turn, which is Pydantic AI's behaviour for every tool error, outside this adapter.

The retry budget is the HOST's (measured on pydantic-ai-slim 2.66.0): Pydantic AI ends a run with
`UnexpectedModelBehavior` when one tool errors more times than its `max_retries` without a success of its own in
between (the agent's `retries`, default 1); a call to another tool, raising or not, resets nothing, and at
`max_retries=0` the first error ends the run before the model sees it. Pass `max_retries=` here to set every tool's
budget, or set the agent's `retries`. A serialized refusal is a plain return value, never a retry, and spends no budget.
"""
from __future__ import annotations

from typing import Optional

from ._surface import Binding

__all__ = ["as_tools"]


def _framework():
    """pydantic-ai, imported when the tools are built (as mcp_server imports the MCP library): this module imports
    without the extra, and building tools without it names the extra."""
    try:
        from pydantic_ai import ModelRetry, Tool
    except ImportError as exc:
        raise ImportError('veracium.adapters.pydantic_ai needs pydantic-ai: pip install "veracium[pydantic_ai]"') from exc
    return Tool, ModelRetry


def _tool(binding: Binding, spec, Tool, ModelRetry):
    name = spec.name

    def run(**kwargs):
        try:
            return binding.call(name, kwargs)
        except Exception as exc:             # Pydantic AI's tool-error channel, as FastMCP reports any tool error
            raise ModelRetry(str(exc)) from exc

    return Tool.from_schema(run, name=name, description=spec.description, json_schema=spec.parameters)


def as_tools(mem, *, user_id: str = "default", capability=None, source_id: Optional[str] = None,
             principal=None, max_retries: Optional[int] = None) -> list:
    """The served tools over `mem` as Pydantic AI `Tool`s, in the server's registration order. `max_retries`, when
    given, is every tool's error budget (None: the agent's own `retries`)."""
    if max_retries is not None and (isinstance(max_retries, bool) or not isinstance(max_retries, int)
                                    or max_retries < 0):
        raise ValueError(f"max_retries must be a non-negative int or None, not {max_retries!r}")
    Tool, ModelRetry = _framework()
    binding = Binding(mem, user_id=user_id, capability=capability, source_id=source_id, principal=principal)
    tools = [_tool(binding, spec, Tool, ModelRetry) for spec in binding.tools()]
    if max_retries is not None:
        for t in tools:
            t.max_retries = max_retries
    return tools
