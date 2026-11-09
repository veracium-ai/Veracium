"""The framework-free half of every adapter: the served tool surface and the host's bindings (specs/0053).

`served_tools` reads the tools from `build_server`'s registration: name, description and the JSON schema FastMCP
reflects. An adapter presents those, so it has no copy of a schema or a description that could drift.

`Binding` answers a call. It validates the arguments with the served tool's own argument model, exactly as an MCP call
is validated, extra arguments ignored as FastMCP ignores them. Then it calls the `*_impl` function the served tool
calls, with the host's user, capability, source and principal, all fixed at construction. No tool argument reaches a
binding.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from .. import mcp_server as _mcp

#: The served tools this module knows how to answer. `served_tools` refuses a registration that differs, either way:
#: a new served tool with no binding here would otherwise be dropped or answered by nothing.
TOOLS = ("remember", "recall", "answer", "maintain", "record_procedure", "describe_procedures")


@dataclass(frozen=True)
class ToolSpec:
    """One served tool as a framework presents it. `parameters` is a private copy of the reflected schema (a JSON
    round-trip: the schema is JSON by construction)."""
    name: str
    description: str
    parameters: dict


def _registered(mem):
    """The served tools as FastMCP registered them, in registration order. The schema does not depend on the
    bindings, so the server is built with its defaults; it is never run."""
    server = _mcp.build_server(mem)
    try:
        tools = list(server._tool_manager.list_tools())
    except AttributeError as exc:
        raise RuntimeError("the MCP server exposes no tool manager; this adapter reads the served surface from it "
                           "(mcp>=1.0,<2)") from exc
    names = tuple(t.name for t in tools)
    if sorted(names) != sorted(TOOLS) or len(set(names)) != len(names):
        raise RuntimeError(f"the served tools are {names}, and this adapter binds {TOOLS}: an adapter that presents a "
                           f"tool it cannot answer, or drops one it serves, is refused")
    return tools


def served_tools(mem) -> tuple[ToolSpec, ...]:
    return tuple(ToolSpec(t.name, t.description, json.loads(json.dumps(t.parameters))) for t in _registered(mem))


class Binding:
    """The host's bindings, fixed at construction, and the one way a call reaches the library."""

    def __init__(self, mem, *, user_id: str = "default", capability=None, source_id: Optional[str] = None,
                 principal=None):
        if not isinstance(user_id, str) or not user_id:
            raise ValueError(f"user_id must be a non-empty string, not {user_id!r}")
        self._mem = mem
        self._user = user_id
        # resolved ONCE, here: a supplied value outside the closed set raises now, as build_server does (0031 §4a)
        self._capability = _mcp._resolve_capability(capability)
        self._source_id = source_id
        self._principal = principal
        self._models = {t.name: t.fn_metadata for t in _registered(mem)}

    def validate(self, name: str, args: dict) -> dict:
        """The served tool's own validation: FastMCP's JSON pre-parse, then its argument model. A malformed value
        raises pydantic's ValidationError, a ValueError; an extra argument is ignored, as on MCP."""
        meta = self._models[name]
        return meta.arg_model.model_validate(meta.pre_parse_json(dict(args))).model_dump_one_level()

    def call(self, name: str, args: dict) -> Any:
        if name not in self._models:
            raise ValueError(f"unknown tool {name!r}")
        a = self.validate(name, args)
        mem, user = self._mem, self._user
        if name == "remember":
            return _mcp.remember_impl(mem, user, a["text"], author=a["author"], event_type=a["event_type"],
                                      date=a["date"], derived_from=a["derived_from"], source_id=self._source_id,
                                      capability=self._capability)
        if name == "recall":
            return _mcp.recall_impl(mem, user, a["query"], token_budget=a["token_budget"],
                                    principal=self._principal)
        if name == "answer":
            return _mcp.answer_impl(mem, user, a["query"], principal=self._principal)
        if name == "maintain":
            return _mcp.maintain_impl(mem, user)
        if name == "record_procedure":
            return _mcp.record_procedure_impl(mem, user, a["summary"], a["basis"], author=a["author"],
                                              derived_from=a["derived_from"], relation=a["relation"],
                                              note=a["note"], date=a["date"], source_id=self._source_id,
                                              capability=self._capability)
        if name == "describe_procedures":
            return _mcp.describe_procedures_impl(mem, user, a["query"], principal=self._principal)
        raise ValueError(f"unknown tool {name!r}")   # unreachable while TOOLS and the branches agree
