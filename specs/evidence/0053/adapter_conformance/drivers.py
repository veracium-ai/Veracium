"""specs/0053 §5: the driver interface, and the two drivers this tree carries.

A driver wraps one adapter over one `Memory` with one set of host bindings:

- `tools()`  : [{"name", "description", "parameters"}] as the framework will present them;
- `call(name, args)` : the value as the adapter hands it to its framework (for LangChain, the `ToolMessage` the
  framework's own tool-call path produces, which is the text the model reads);
- `decode(value)` : the declared decoder, to the reference form `("ok", value)` or `("error", message)`. It must be
  total and lossless; `check_decoder` round-trips every fixture value through it.

`CoreDriver` is the green control: the framework-free core (`veracium.adapters._surface`), the `*_impl` functions
wrapped in the adapter interface. `LangChainDriver` is `veracium.adapters.langchain`. Both take the adapter MODULES as
arguments, so the mutant row can hand them a mutated copy of the package.
"""
from __future__ import annotations

import json

from .canon import _strict_pairs


class CoreDriver:
    name = "core"

    def __init__(self, surface, mem, binding: dict):
        self._binding = surface.Binding(mem, **binding)
        self._specs = self._binding.tools()

    def tools(self):
        return [{"name": s.name, "description": s.description, "parameters": s.parameters} for s in self._specs]

    def converted(self):
        return None                                   # no framework conversion

    def call(self, name, args):
        try:
            return ("ok", self._binding.call(name, args))
        except Exception as exc:                      # the reference form of a raise: FastMCP reports any tool error
            return ("error", str(exc))

    def decode(self, value):
        return value


class LangChainDriver:
    name = "langchain"

    def __init__(self, langchain_module, mem, binding: dict):
        self._tools = {t.name: t for t in langchain_module.as_tools(mem, **binding)}
        self._order = list(self._tools)

    def tools(self):
        return [{"name": n, "description": self._tools[n].description, "parameters": self._tools[n].args_schema}
                for n in self._order]

    def converted(self):
        """The framework's own offline conversion to a provider's tool schema (OpenAI's function form)."""
        from langchain_core.utils.function_calling import convert_to_openai_tool
        out = []
        for n in self._order:
            f = convert_to_openai_tool(self._tools[n])["function"]
            out.append({"name": f["name"], "description": f.get("description", ""), "parameters": f["parameters"]})
        return out

    def call(self, name, args):
        if name not in self._tools:
            return ("missing-tool", name)
        return self._tools[name].invoke({"type": "tool_call", "name": name, "args": dict(args), "id": "call-0053"})

    def decode(self, value):
        """ToolMessage -> the reference form. An error status is the framework's tool-error result; a success's
        content is the tool's string as is, or a dict the framework serialised to JSON text."""
        from langchain_core.messages import ToolMessage
        if isinstance(value, tuple):
            return value
        if not isinstance(value, ToolMessage):
            return ("not-a-tool-message", repr(value)[:200])
        if value.status == "error":
            return ("error", value.content)
        content = value.content
        if isinstance(content, str) and content[:1] == "{":
            try:
                parsed = json.loads(content, object_pairs_hook=_strict_pairs)
            except ValueError:
                return ("ok", content)
            if isinstance(parsed, dict):
                return ("ok", parsed)
        return ("ok", content)

    @staticmethod
    def encode(outcome):
        """What the framework would hand the model for a reference outcome: its own `ToolMessage` path, used by the
        decoder's round-trip check. Built through the framework's own conversion, never re-implemented."""
        from langchain_core.tools import StructuredTool, ToolException
        kind, v = outcome

        def f():
            if kind == "error":
                raise ToolException(v)
            return v
        t = StructuredTool(name="probe", description="probe", args_schema={"type": "object", "properties": {}},
                           func=f, handle_tool_error=True)
        return t.invoke({"type": "tool_call", "name": "probe", "args": {}, "id": "call-0053"})


class PydanticAIDriver:
    """`veracium.adapters.pydantic_ai`, driven through a real `Agent` with Pydantic AI's offline `FunctionModel`: the
    scripted model makes one tool call and the driver keeps the tool-return part the framework then hands the model."""
    name = "pydantic_ai"
    CALL_ID = "call-0053"

    def __init__(self, pydantic_ai_module, mem, binding: dict):
        self._tools = {t.name: t for t in pydantic_ai_module.as_tools(mem, **binding)}
        self._order = list(self._tools)

    def tools(self):
        return [{"name": n, "description": self._tools[n].description,
                 "parameters": self._tools[n].function_schema.json_schema} for n in self._order]

    def _run(self, script, tools=None):
        from pydantic_ai import Agent
        from pydantic_ai.models.function import FunctionModel
        Agent(FunctionModel(script), tools=list((tools or self._tools).values())).run_sync("conformance")

    def converted(self):
        """The tool definitions the agent hands a model (FunctionModel's AgentInfo), the framework's own conversion."""
        from pydantic_ai.messages import ModelResponse, TextPart
        seen = {}

        def script(messages, info):
            seen["defs"] = list(info.function_tools)
            return ModelResponse(parts=[TextPart("done")])
        self._run(script)
        return [{"name": d.name, "description": d.description or "", "parameters": d.parameters_json_schema}
                for d in seen["defs"]]

    def call(self, name, args):
        if name not in self._tools:
            return ("missing-tool", name)
        from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
        seen = {}

        def script(messages, info):
            if len(messages) == 1:
                return ModelResponse(parts=[ToolCallPart(name, dict(args), tool_call_id=self.CALL_ID)])
            seen["part"] = next(p for p in messages[-1].parts if getattr(p, "tool_call_id", None) == self.CALL_ID)
            return ModelResponse(parts=[TextPart("done")])
        self._run(script)
        return seen["part"]

    def decode(self, value):
        """The tool-return part -> the reference form, read from the TEXT the model is handed: an `outcome` of
        "retried" (ModelRetry, Pydantic AI's tool-error channel) is `{"error": <message>}`; otherwise the tool's string,
        or the dict the framework serialised to JSON text."""
        from pydantic_ai.messages import ToolReturnPart
        if isinstance(value, tuple):
            return value
        if not isinstance(value, ToolReturnPart):
            return ("not-a-tool-return", repr(value)[:200])
        text = value.model_response_str()
        if value.outcome == "retried":
            try:
                parsed = json.loads(text, object_pairs_hook=_strict_pairs)
            except ValueError:
                return ("error-unparsed", text)
            if isinstance(parsed, dict) and set(parsed) == {"error"}:
                return ("error", parsed["error"])
            return ("error-unparsed", text)
        if text[:1] == "{":
            try:
                parsed = json.loads(text, object_pairs_hook=_strict_pairs)
            except ValueError:
                return ("ok", text)
            if isinstance(parsed, dict):
                return ("ok", parsed)
        return ("ok", text)

    @classmethod
    def encode(cls, outcome):
        """The part the framework hands the model for a reference outcome, through its own tool path."""
        from pydantic_ai import ModelRetry, Tool
        from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
        kind, v = outcome

        def f():
            if kind == "error":
                raise ModelRetry(v)
            return v
        tool = Tool.from_schema(f, name="probe", description="probe", json_schema={"type": "object", "properties": {}})
        seen = {}

        def script(messages, info):
            if len(messages) == 1:
                return ModelResponse(parts=[ToolCallPart("probe", {}, tool_call_id=cls.CALL_ID)])
            seen["part"] = next(p for p in messages[-1].parts if getattr(p, "tool_call_id", None) == cls.CALL_ID)
            return ModelResponse(parts=[TextPart("done")])
        from pydantic_ai import Agent
        from pydantic_ai.models.function import FunctionModel
        Agent(FunctionModel(script), tools=[tool]).run_sync("conformance")
        return seen["part"]
