"""Reference `Complete`/`Embed` implementations backed by the Anthropic SDK.

Optional — install with `pip install engram[anthropic]`. This is a convenience so
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


class AnthropicComplete:
    """A `Complete` implementation. Uses structured outputs when a json_schema is
    provided so extraction/curation return valid JSON without fragile parsing."""

    def __init__(self, *, client=None, models: Optional[dict[Role, str]] = None,
                 max_tokens: int = 4096):
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "The Anthropic reference provider needs the SDK: pip install engram[anthropic]. "
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
        return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")


class AnthropicEmbed:
    """Optional `Embed` via a Bedrock/Voyage/etc. embedding endpoint of the host's
    choice. Left minimal on purpose — engram's primary retrieval is graph-based;
    embeddings are only a fallback over episodes. Supply your own if you want it."""

    def __init__(self, embed_fn):
        self._embed = embed_fn

    def __call__(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)
