"""Bring-your-own LLM interface.

Veracium never owns credentials or model choice. The host supplies a `Complete`
callable; the plug-in calls it for the three internal roles below. An embedding
function is optional (only used for episode semantic fallback retrieval).

A reference Anthropic implementation ships in `veracium.llm.anthropic`, but any
callable with the right signature works — including the host agent's existing
client.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

# Internal roles, so a host can route each to an appropriate model/effort tier.
# distill/extract: structured, high-volume, cheap-tier friendly.
# compile: curation and judgment — mid tier.
# gate: correctness-critical abstention decision — strongest tier.
Role = str  # "distill" | "compile" | "gate"


@runtime_checkable
class Complete(Protocol):
    """A single completion call. Implementations SHOULD honor `json_schema` when
    given (returning parseable JSON), but veracium's callers also tolerate fenced/
    noisy JSON, so a plain string-in/string-out callable is a valid implementation."""

    def __call__(self, prompt: str, *, system: Optional[str] = None,
                 role: Role = "compile", json_schema: Optional[dict] = None) -> str: ...


@runtime_checkable
class Embed(Protocol):
    """Optional. Batch-embed texts to vectors for episode semantic fallback."""

    def __call__(self, texts: list[str]) -> list[list[float]]: ...
