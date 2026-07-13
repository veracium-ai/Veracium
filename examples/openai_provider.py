"""Example BYO provider: wrap an OpenAI-compatible chat-completions API as a
veracium `Complete` callable.

"OpenAI-compatible" covers the OpenAI API itself as well as self-hosted
endpoints that mimic it — vLLM's `--api-key`-optional server and Ollama's
`/v1` endpoint both speak this dialect, so one client covers the largest
group of self-hosters. Needs the `openai` SDK (`pip install openai`); it is
not a veracium dependency, only an example one.

`json_schema` handling is honest, not decorative: if given, this first tries
OpenAI's structured-output `response_format` so distill/compile calls come
back as valid JSON directly. If the endpoint rejects that param — most local
servers don't implement it yet — it falls back to a plain completion and lets
veracium's tolerant JSON parser (`veracium._json.extract_json`) do the work.
Nothing here raises just because structured output isn't supported.
"""

from __future__ import annotations

import os
from typing import Optional

# Two-tier split mirroring the AnthropicComplete reference: a cheap/fast model
# for high-volume distill/extract calls, a stronger one for curation and the
# correctness-critical gate. These are OpenAI model names — if you're pointing
# at vLLM or Ollama, override every entry with the model name your server
# actually serves (e.g. "llama3.1", "qwen2.5:14b"); those servers ignore
# names they don't recognize rather than mapping them.
ROLE_MODEL = {
    "distill": "gpt-4o-mini",
    "compile": "gpt-4o",
    "gate": "gpt-4o",
}


class OpenAIComplete:
    """A `Complete` implementation for any OpenAI-compatible chat-completions API.

    Examples:
        OpenAIComplete()                                            # OpenAI, uses OPENAI_API_KEY
        OpenAIComplete(base_url="http://localhost:11434/v1")         # Ollama
        OpenAIComplete(base_url="http://localhost:8000/v1",          # vLLM
                        models={"distill": "llama3.1", "compile": "llama3.1", "gate": "llama3.1"})
    """

    def __init__(self, *, client=None, base_url: Optional[str] = None,
                 api_key: Optional[str] = None,
                 models: Optional[dict[str, str]] = None,
                 max_tokens: int = 4096):
        try:
            from openai import BadRequestError, OpenAI
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "OpenAIComplete needs the SDK: pip install openai"
            ) from e
        if client is not None:
            self._client = client
        else:
            # Local servers (vLLM/Ollama) usually don't check the key, but the
            # SDK still requires a non-empty string when no OPENAI_API_KEY is set.
            key = api_key or os.environ.get("OPENAI_API_KEY")
            if key is None and base_url is not None:
                key = "not-needed"
            self._client = OpenAI(base_url=base_url, api_key=key)
        self._bad_request = BadRequestError
        self._models = {**ROLE_MODEL, **(models or {})}
        self._max_tokens = max_tokens
        self._structured: Optional[bool] = None  # None = untried; False = endpoint rejected it

    def __call__(self, prompt: str, *, system: Optional[str] = None,
                 role: str = "compile", json_schema: Optional[dict] = None) -> str:
        model = self._models.get(role, self._models["compile"])
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        kwargs: dict = {"model": model, "messages": messages, "max_tokens": self._max_tokens}

        if json_schema is not None and self._structured is not False:
            try:
                resp = self._client.chat.completions.create(
                    **kwargs,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {"name": "veracium_output", "schema": json_schema, "strict": True},
                    },
                )
                self._structured = True
                return resp.choices[0].message.content or ""
            except self._bad_request:
                # Endpoint doesn't support structured output — remember that and
                # fall through; veracium parses plain completions tolerantly.
                self._structured = False

        resp = self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""
