"""veracium's served tools as LangChain tools (specs/0053; `pip install "veracium[langchain]"`).

    from veracium.adapters.langchain import as_tools
    tools = as_tools(mem, user_id="alice", capability="direct", source_id="chat-app")
    agent = create_agent(model, tools)          # or llm.bind_tools(tools), a LangGraph ToolNode, ...

Every tool is the served MCP tool: the same name, the same parameters (the JSON schema FastMCP reflects) and the same
description, byte for byte. The descriptions are model-facing safety text ("Set author=\"third_party\" … this
quarantines …"); a provider path that caps a description below its length is a different surface, and the
conformance suite fails it by name.

The user, the capability (0031 §4a), the source (0006 I1) and the principal (0020) are the HOST's, bound here and never
a tool argument. A refusal comes back as the library's data (`{"ok": false, "refusal": …}`). A library raise (a value
outside a closed set, a malformed argument) comes back as a tool-error result carrying the library's message verbatim
(`handle_tool_error=True`), so the model reads the reason and the agent loop does not crash. Nothing is retried,
reworded or answered by another model.
"""
from __future__ import annotations

from typing import Optional

from ._surface import Binding, served_tools

__all__ = ["as_tools"]


def _framework():
    """langchain-core, imported when the tools are built (as mcp_server imports the MCP library): this module imports
    without the extra, and building tools without it names the extra."""
    try:
        from langchain_core.tools import StructuredTool, ToolException
    except ImportError as exc:
        raise ImportError('veracium.adapters.langchain needs langchain-core: pip install "veracium[langchain]"') from exc
    return StructuredTool, ToolException


def _tool(binding: Binding, spec, StructuredTool, ToolException):
    name = spec.name

    def run(**kwargs):
        try:
            return binding.call(name, kwargs)
        except ValueError as exc:            # the library's caller errors, pydantic's ValidationError included
            raise ToolException(str(exc)) from exc

    return StructuredTool(name=name, description=spec.description, args_schema=spec.parameters, func=run,
                          handle_tool_error=True)


def as_tools(mem, *, user_id: str = "default", capability=None, source_id: Optional[str] = None,
             principal=None) -> list:
    """The served tools over `mem` as LangChain `StructuredTool`s, in the server's registration order."""
    StructuredTool, ToolException = _framework()
    binding = Binding(mem, user_id=user_id, capability=capability, source_id=source_id, principal=principal)
    return [_tool(binding, spec, StructuredTool, ToolException) for spec in served_tools(mem)]
