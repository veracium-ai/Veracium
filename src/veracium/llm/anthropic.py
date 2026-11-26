"""Reference `Complete`/`Embed` implementations backed by the Anthropic SDK.

Optional — install with `pip install veracium-memory[anthropic]`. This is a convenience so
hosts without an existing LLM client can get started; the model-per-role defaults
are cost-tuned (cheap tier for high-volume extraction, stronger tier for the
correctness-critical gate) and fully overridable. Any host that already has an
LLM client should prefer wrapping it as a `Complete` callable instead.
"""

from __future__ import annotations

import json
from typing import Optional

from .base import Role

# Cost-tuned defaults. Distillation is high-volume and structured (cheap tier);
# compilation needs curation judgment; the abstention gate is correctness-
# critical. Override any of these via AnthropicComplete(models={...}).
DEFAULT_MODELS: dict[Role, str] = {
    "distill": "claude-haiku-4-5",
    "compile": "claude-sonnet-5",
    "gate": "claude-sonnet-5",
}


class EmptyCompletion(RuntimeError):
    """The model returned NO text block — an empty completion is never a result.

    Found 2026-09-19 (research, reproduced against the SDK): with the default
    `max_tokens` a hard prompt can spend the whole budget inside a `thinking` block,
    the call succeeds with `stop_reason == "max_tokens"` and no text, and the caller
    got "" with no signal. Every role reads emptiness as a finding — an empty distill
    is "no triples", an empty compile is "an empty wiki", an empty GATE answer is what
    an abstention looks like. So the provider REFUSES: the message names the stop
    reason, the output tokens and the block types seen, and the fields carry them.
    """

    def __init__(self, *, stop_reason, output_tokens, block_types, max_tokens, model):
        self.stop_reason, self.output_tokens = stop_reason, output_tokens
        self.block_types, self.max_tokens, self.model = list(block_types), max_tokens, model
        hint = (" — the budget was spent before any text (raise max_tokens)"
                if stop_reason == "max_tokens" else "")
        super().__init__(
            f"{model} returned no text block (stop_reason={stop_reason!r}, output "
            f"tokens={output_tokens}, blocks={self.block_types}, max_tokens={max_tokens}){hint}; "
            f"an empty completion is never a result")


def text_of(msg, *, max_tokens: int, model: str) -> str:
    """The ONE assembly of a completion's text: the text blocks joined, or
    `EmptyCompletion` when there are none — whatever the stop reason (`max_tokens`
    inside thinking, `refusal`, an `end_turn` with nothing said). Pure over the
    message shape so it is testable without the SDK; `AnthropicComplete.__call__`
    renders through it."""
    # plain attribute reads: the SDK message always carries content, stop_reason and
    # usage (0031's getattr inventory stays at its one allowed site below)
    content = list(msg.content or [])
    text = "".join(b.text for b in content if getattr(b, "type", None) == "text")
    if text:
        return text
    raise EmptyCompletion(
        stop_reason=msg.stop_reason,
        output_tokens=msg.usage.output_tokens if msg.usage is not None else None,
        block_types=[b.type for b in content],
        max_tokens=max_tokens, model=model)


class AnthropicComplete:
    """A `Complete` implementation. Uses structured outputs when a json_schema is
    provided so extraction/curation return valid JSON without fragile parsing.
    Raises `EmptyCompletion` rather than returning "" when the model produced no
    text block (see `text_of`)."""

    def __init__(self, *, client=None, models: Optional[dict[Role, str]] = None,
                 max_tokens: int = 4096):
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "The Anthropic reference provider needs the SDK: pip install veracium-memory[anthropic]. "
                "Or pass your own Complete callable instead."
            ) from e
        self._client = client or anthropic.Anthropic()
        self._models = {**DEFAULT_MODELS, **(models or {})}
        self._max_tokens = max_tokens

    def __call__(self, prompt: str, *, system: Optional[str] = None,
                 role: Role = "compile", json_schema: Optional[dict] = None) -> str:
        model = self._models.get(role, self._models["compile"])
        kwargs: dict = {"model": model, "max_tokens": self._max_tokens,
                        "messages": [{"role": "user", "content": prompt}]}
        if system:
            kwargs["system"] = system
        if json_schema is not None:
            kwargs["output_config"] = {"format": {"type": "json_schema", "schema": json_schema}}
        msg = self._client.messages.create(**kwargs)
        return text_of(msg, max_tokens=self._max_tokens, model=model)


class AnthropicEmbed:
    """Optional `Embed` via a Bedrock/Voyage/etc. embedding endpoint of the host's
    choice. Left minimal on purpose — veracium's primary retrieval is graph-based;
    embeddings are only a fallback over episodes. Supply your own if you want it."""

    def __init__(self, embed_fn):
        self._embed = embed_fn

    def __call__(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)
