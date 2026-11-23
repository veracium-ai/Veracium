"""The framework-free half of every adapter: the served tool surface and the host's bindings (specs/0053).

`served_tools` reads the tools from `build_server`'s registration: name, description and the JSON schema FastMCP
reflects. An adapter presents those, so it has no copy of a schema or a description that could drift.

`Binding` answers a call. It validates the arguments with the served tool's own argument model, exactly as an MCP call
is validated, extra arguments ignored as FastMCP ignores them. Then it calls the `*_impl` function the served tool
calls, with the host's user, capability, source and principal, all fixed at construction. No tool argument reaches a
binding.

The trust tools (specs/0031 §4f) take, besides those, the binding's ERASURE setting (§4i, decided here once) and its
own PREVIEW-TOKEN ISSUER (§4e: each binding owns one, shared with no other surface, so a token one binding issued is
`preview_unknown` to every other).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from .. import credentials as _cred
from .. import mcp_server as _mcp

#: The served tools this module knows how to answer. `served_tools` refuses a registration that differs, either way:
#: a new served tool with no binding here would otherwise be dropped or answered by nothing.
TOOLS = ("remember", "recall", "answer", "maintain", "record_procedure", "describe_procedures",
         # specs/0031 §4f (the owner's Q10 ruling, "Integrations too"): the seven trust tools, answered through their
         # `*_impl` with the host's bindings and `call_path=adapter_direct`
         "find_facts", "correct_fact", "dispute_fact", "confirm_fact", "forget_fact",
         "forget_everything_preview", "forget_everything_confirm")


@dataclass(frozen=True)
class ToolSpec:
    """One served tool as a framework presents it. `parameters` is a private copy of the reflected schema (a JSON
    round-trip: the schema is JSON by construction)."""
    name: str
    description: str
    parameters: dict


def _registered(mem, capability=None):
    """The served tools as FastMCP registered them, in registration order. The server is built with the host's
    capability, so its one operator log line (0031 I3) names the capability this adapter serves under; it is never
    run, and the schema does not depend on the capability."""
    server = _mcp.build_server(mem, capability=capability)
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


def _specs(tools) -> tuple[ToolSpec, ...]:
    return tuple(ToolSpec(t.name, t.description, json.loads(json.dumps(t.parameters))) for t in tools)


def served_tools(mem, capability=None) -> tuple[ToolSpec, ...]:
    return _specs(_registered(mem, capability))


class Binding:
    """The host's bindings, fixed at construction, and the one way a call reaches the library."""

    def __init__(self, mem, *, user_id: str = "default", capability=None, source_id: Optional[str] = None,
                 principal=None, erasure=None, audit_log=None):
        if not isinstance(user_id, str) or not user_id:
            raise ValueError(f"user_id must be a non-empty string, not {user_id!r}")
        # specs/0055 §4g: the adapter's AuditLog (an `audit.AuditLog`, or a path for one), attached to the bound Memory
        # so the credential counts and 0031 §10 Q4's discarded raises reach the operator, as VERACIUM_AUDIT_LOG does for
        # the stock server. A Memory that already has a different log is refused: one operation, one log.
        if audit_log is not None:
            from ..audit import AuditLog
            log = audit_log if isinstance(audit_log, AuditLog) else AuditLog(audit_log)
            if mem.audit is None:
                mem.audit = log
            elif mem.audit is not audit_log:
                raise ValueError("audit_log: this Memory already has an audit log attached; pass that one, or none")
        self._mem = mem
        self._user = user_id
        # resolved ONCE, here: a supplied value outside the closed set raises now, as build_server does (0031 §4a)
        self._capability = _mcp._resolve_capability(capability)
        self._source_id = source_id
        self._principal = principal
        self._erasure = _mcp._resolve_erasure(erasure)     # specs/0031 §4i: an invalid value raises now
        from ..schema import ConfirmationCallPath
        from ..trust_tools import PreviewTokenIssuer
        self._call_path = ConfirmationCallPath.ADAPTER_DIRECT
        self._issuer = PreviewTokenIssuer(mem.store.local_origin(), user_id)   # this binding's own (§4e)
        self._tools = _registered(mem, self._capability)
        self._models = {t.name: t.fn_metadata for t in self._tools}

    def tools(self) -> tuple[ToolSpec, ...]:
        """The served tools this binding answers, read once at construction."""
        return _specs(self._tools)

    def validate(self, name: str, args: dict) -> dict:
        """The served tool's own validation: FastMCP's JSON pre-parse, then its argument model. A malformed value
        raises pydantic's ValidationError, a ValueError; an extra argument is ignored, as on MCP."""
        meta = self._models[name]
        return meta.arg_model.model_validate(meta.pre_parse_json(dict(args))).model_dump_one_level()

    def call(self, name: str, args: dict) -> Any:
        """Answer one call as the served tool answers it (specs/0055 §4g): through the `adapter` surface, a credential
        refusal returned as its refusal dict, and any other error raised as a ValueError carrying the outward
        formatter's text (field and reason, never the caller's value), chained to the original."""
        if name not in self._models:
            raise ValueError("unknown tool: this binding serves " + ", ".join(sorted(self._models)))
        # the served tool's own argument validation, as FastMCP runs it BEFORE the tool body: its text is pydantic's
        # message from the served argument model, which hides the input (E2), exactly as an MCP call reports it
        a = self.validate(name, args)
        with _cred.on_surface("adapter"):
            try:
                return self._call(name, args, a)
            except _cred.CredentialRefused as exc:
                return exc.as_refusal()
            except Exception as exc:                     # noqa: BLE001 - re-raised, formatted, chained
                raise ValueError(_cred.outward_text(exc)) from exc

    def _call(self, name: str, args: dict, a: dict) -> Any:
        """Answer one call with its VALIDATED arguments `a` (`args` is the call as given, which nothing here reads:
        a binding takes no tool argument outside the served schema)."""
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
        # specs/0031 §4f: the trust tools, with the host's principal, source, erasure setting and issuer
        cap, pr, src, cp = self._capability, self._principal, self._source_id, self._call_path
        if name == "find_facts":
            return _mcp.find_facts_impl(mem, user, a["query"], capability=cap, principal=pr)
        if name == "correct_fact":
            return _mcp.correct_fact_impl(mem, user, a["edge_id"], a["corrected_value"], capability=cap,
                                          principal=pr, source_id=src, call_path=cp)
        if name == "dispute_fact":
            return _mcp.dispute_fact_impl(mem, user, a["edge_id"], a["reason"], capability=cap, principal=pr,
                                          source_id=src, call_path=cp)
        if name == "confirm_fact":
            return _mcp.confirm_fact_impl(mem, user, a["edge_id"], capability=cap, principal=pr, source_id=src,
                                          call_path=cp)
        if name == "forget_fact":
            return _mcp.forget_fact_impl(mem, user, a["edge_id"], a["episode_id"], capability=cap,
                                         erasure=self._erasure, principal=pr)
        if name == "forget_everything_preview":
            return _mcp.forget_everything_preview_impl(mem, user, capability=cap, erasure=self._erasure,
                                                       principal=pr, issuer=self._issuer)
        if name == "forget_everything_confirm":
            return _mcp.forget_everything_confirm_impl(mem, user, a["preview_token"], capability=cap,
                                                       erasure=self._erasure, principal=pr, issuer=self._issuer)
        raise ValueError(f"unknown tool {name!r}")   # unreachable while TOOLS and the branches agree
