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
    """Optional. Batch-embed texts to vectors (specs/0027 semantic recall;
    also the episode semantic fallback).

    `__call__` is the embedding call — batch in, batch out, same length and
    order; the one-input query path is `embedder([query])[0]`.

    `id()` and `dim()` (0027 §4d) make the embedder's identity explicit:
    one `id()` PERMANENTLY denotes one embedding behaviour — one model, one
    revision, one preprocessing, one output space. ANY semantic change (new
    model, retrained revision, changed tokenisation/normalisation, different
    dim) MUST yield a new `id()`, because the persisted index mixes vectors
    across operations and process restarts — reusing an id for changed
    behaviour silently mixes incompatible vectors. Shape: a non-empty string
    matching `^[A-Za-z0-9._@:+-]{1,128}$` (`name@revision` is conventional),
    compared by byte-equality. `dim()` is the declared dimension — a strict
    positive `int` (`bool` rejected); it is the source against which "wrong
    dimension" is judged. An embedder missing either method still works for
    everything EXCEPT semantic recall, which reports
    `semantic_status="no_embedder"` and degrades to lexical (0027 V6).
    """

    def __call__(self, texts: list[str]) -> list[list[float]]: ...

    def id(self) -> str: ...

    def dim(self) -> int: ...
