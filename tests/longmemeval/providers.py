"""Benchmark providers with pinned models and token accounting.

The adapter needs two things the shipped example (`examples/openai_provider.py`)
deliberately doesn't do:

  * **dated model pins** — a canonical run must name the exact snapshot, not a
    floating alias that silently changes under it;
  * **provider-reported token counts per role** — the run record reports actual
    incurred cost from the API's own usage numbers, not an estimate.

Model choice for the pilot, recorded in the run record:
  distill (extraction, ~250k calls at full scale) → gpt-4.1-mini snapshot
  compile / gate (curation + the answer path)     → gpt-4.1 snapshot

Note the answerer is deliberately NOT gpt-4o: the official judge is gpt-4o, and
having the same model answer and grade invites self-preference bias. Keeping
them in different families is a small, free methodological improvement.

Credentials come from the environment (`OPENAI_API_KEY`); nothing here reads or
writes a key file, and no key is ever placed in a run record.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Optional

DISTILL_MODEL = "gpt-4.1-mini-2025-04-14"
ANSWER_MODEL = "gpt-4.1-2025-04-14"
JUDGE_MODEL = "gpt-4o"          # official pin, for reference in the record

# USD per 1M tokens, as of the pilot date — recorded so a cost figure can be
# recomputed if prices move. Not authoritative pricing, just bookkeeping.
PRICES = {
    "gpt-4.1-mini-2025-04-14": {"in": 0.40, "out": 1.60},
    "gpt-4.1-2025-04-14": {"in": 2.00, "out": 8.00},
}

DECODING = {"temperature": 0.0, "max_tokens": 4096}


class MeteredOpenAI:
    """`Complete` callable over OpenAI chat-completions with per-role metering.

    Retries transient failures with backoff; a retry is counted so the record
    shows how much of the wall clock was rate-limit waiting.
    """

    def __init__(self, *, distill_model: str = DISTILL_MODEL,
                 answer_model: str = ANSWER_MODEL, max_retries: int = 5,
                 max_tokens: int = 4096, temperature: float = 0.0):
        from openai import OpenAI  # local import: not a veracium dependency
        if not os.environ.get("OPENAI_API_KEY"):
            raise SystemExit("MeteredOpenAI needs OPENAI_API_KEY in the environment")
        self._client = OpenAI()
        self.models = {"distill": distill_model, "compile": answer_model,
                       "gate": answer_model}
        self.max_retries = max_retries
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._lock = threading.Lock()
        self.usage: dict[str, dict[str, float]] = {}
        self.retries = 0
        self.failures = 0

    # what the run record needs to identify this provider
    @property
    def model(self) -> str:
        return self.models["distill"]

    @property
    def decoding(self) -> dict:
        return {"temperature": self.temperature, "max_tokens": self.max_tokens}

    def _meter(self, role: str, model: str, resp) -> None:
        u = getattr(resp, "usage", None)
        if u is None:
            return
        with self._lock:
            b = self.usage.setdefault(role, {"model": model, "calls": 0,
                                             "in_tokens": 0, "out_tokens": 0})
            b["calls"] += 1
            b["in_tokens"] += getattr(u, "prompt_tokens", 0) or 0
            b["out_tokens"] += getattr(u, "completion_tokens", 0) or 0

    def cost_usd(self) -> dict:
        """Actual incurred cost from provider-reported usage, per role."""
        out, total = {}, 0.0
        for role, b in self.usage.items():
            p = PRICES.get(b["model"])
            if not p:
                out[role] = {**b, "usd": None}
                continue
            usd = b["in_tokens"] / 1e6 * p["in"] + b["out_tokens"] / 1e6 * p["out"]
            out[role] = {**b, "usd": round(usd, 4)}
            total += usd
        out["total_usd"] = round(total, 4)
        return out

    def __call__(self, prompt: str, *, system: Optional[str] = None,
                 role: str = "compile", json_schema: Optional[dict] = None) -> str:
        model = self.models.get(role, self.models["compile"])
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        kwargs: dict = {"model": model, "messages": messages,
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature}
        if json_schema is not None:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "veracium_output", "schema": json_schema,
                                "strict": False},
            }
        delay = 2.0
        for attempt in range(self.max_retries):
            try:
                resp = self._client.chat.completions.create(**kwargs)
                self._meter(role, model, resp)
                return resp.choices[0].message.content or ""
            except Exception as e:
                name = type(e).__name__
                # structured output unsupported / schema rejected: drop it once
                if "BadRequest" in name and "response_format" in kwargs:
                    kwargs.pop("response_format")
                    continue
                if attempt == self.max_retries - 1:
                    with self._lock:
                        self.failures += 1
                    raise
                with self._lock:
                    self.retries += 1
                time.sleep(delay)
                delay = min(delay * 2, 30)
        raise RuntimeError("unreachable")
