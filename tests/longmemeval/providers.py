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

import atexit
import collections
import json
import os
import random
import threading
import time
from pathlib import Path
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

# Spend ledger. Cost used to be reported only in a run record, which is written
# when a run COMPLETES — so every killed run (rate-limit restarts, the quota
# abort, my own cache-identity restarts) spent real money that appeared in no
# report at all. Under-reporting spend by 2x is not a rounding error, so usage
# is now flushed to an append-only ledger during the run and at exit.
LEDGER = Path.home() / "Datasets" / "longmemeval" / "spend.jsonl"
LEDGER_EVERY = 200         # calls between flushes

# Rate limits are PER MODEL and set by the account tier, not by us. Measured on
# this org (2026-07-30): gpt-4.1-mini 200k TPM, gpt-4.1 30k TPM, gpt-4o 30k TPM
# — the answer model is 6.7x tighter than the extractor, so one shared budget
# would starve nothing and 429 everything. Budgets are keyed by model and
# self-tune from the provider's own `x-ratelimit-limit-tokens` header, so a tier
# change is picked up automatically with no code edit.
DEFAULT_TPM = 200_000          # fallback for an unseen model
SEED_TPM = {                   # starting guesses, corrected by live headers
    "gpt-4.1-mini-2025-04-14": 200_000,
    "gpt-4.1-2025-04-14": 30_000,
    "gpt-4o": 30_000,
}
TPM_SAFETY = 0.85          # headroom for estimate error and in-flight requests
OUTPUT_TOKEN_ALLOWANCE = 300   # extraction replies are small; counted anyway


class QuotaExhausted(RuntimeError):
    """Billing quota is gone: no retry can fix it, and no further call in this
    run can succeed. Raised so the runner aborts instead of writing a full set
    of empty hypotheses that would look like a completed run."""


class MeteredOpenAI:
    """`Complete` callable over OpenAI chat-completions with per-role metering.

    Retries transient failures with backoff; a retry is counted so the record
    shows how much of the wall clock was rate-limit waiting.
    """

    def __init__(self, *, distill_model: str = DISTILL_MODEL,
                 answer_model: str = ANSWER_MODEL, max_retries: int = 8,
                 max_tokens: int = 4096, temperature: float = 0.0,
                 tpm: int = DEFAULT_TPM, label: str = "",
                 ledger: Optional[Path] = LEDGER):
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
        self.rate_limited = 0
        # sliding-window token budget, PER MODEL (limits differ ~7x between the
        # extraction and answer models on this tier)
        self.tpm = tpm                      # explicit override for the extractor
        self._limits: dict[str, float] = {}
        self._windows: dict[str, collections.deque] = {}
        self._in_window: dict[str, float] = {}
        self._pace_lock = threading.Lock()
        self._pace_waits = 0
        self._ledger = Path(ledger) if ledger else None
        self._label = label
        self._calls_since_flush = 0
        if self._ledger is not None:
            atexit.register(self.flush_spend, "atexit")
        for name in set(self.models.values()):
            self._limits[name] = float(
                tpm if name == self.models["distill"] and tpm != DEFAULT_TPM
                else SEED_TPM.get(name, DEFAULT_TPM))

    # what the run record needs to identify this provider
    @property
    def model(self) -> str:
        return self.models["distill"]

    @property
    def decoding(self) -> dict:
        """SAMPLING parameters only — this feeds the extraction cache identity,
        so it must contain exactly the things that change a model's output and
        nothing operational. Putting throughput state here (rate limits, worker
        counts) silently invalidates every cached extraction whenever tuning
        changes: it cost a full re-extraction once. Operational state belongs in
        `throughput` below, which the run record reports and the key ignores."""
        return {"temperature": self.temperature, "max_tokens": self.max_tokens}

    @property
    def throughput(self) -> dict:
        """Operational, NEVER part of the cache identity."""
        return {"tpm_limits": {m: int(v) for m, v in sorted(self._limits.items())},
                "tpm_safety": TPM_SAFETY, "pace_waits": self._pace_waits,
                "rate_limit_hits": self.rate_limited}

    def _pace(self, model: str, est_tokens: int) -> None:
        """Admit a request only when its estimated tokens fit that MODEL's
        trailing-60s budget. Blocks the calling worker instead of letting the
        provider reject it — a 429 costs a retry and can still fail an item,
        whereas waiting costs only latency."""
        while True:
            with self._pace_lock:
                now = time.monotonic()
                w = self._windows.setdefault(model, collections.deque())
                used = self._in_window.get(model, 0.0)
                while w and w[0][0] <= now - 60.0:
                    _, n = w.popleft()
                    used -= n
                budget = self._limits.get(model, DEFAULT_TPM) * TPM_SAFETY
                if used + est_tokens <= budget or not w:
                    w.append((now, est_tokens))
                    self._in_window[model] = used + est_tokens
                    return
                self._in_window[model] = used
                wait = max(0.05, w[0][0] + 60.0 - now)
                self._pace_waits += 1
            time.sleep(min(wait, 2.0))

    def _penalize(self, model: str, est_tokens: int) -> None:
        """A 429 means the provider's accounting is ahead of ours; charge that
        model's window for the rejected request so the whole pool slows, not
        just this thread (the limit is org-wide)."""
        with self._pace_lock:
            self._windows.setdefault(model, collections.deque()).append(
                (time.monotonic(), est_tokens))
            self._in_window[model] = self._in_window.get(model, 0.0) + est_tokens

    def _learn_limit(self, model: str, headers) -> None:
        """Adopt the provider's own reported limit. A tier change then needs no
        code edit — the pacer widens (or narrows) on the next response."""
        raw = None
        try:
            raw = headers.get("x-ratelimit-limit-tokens")
        except Exception:
            return
        if not raw:
            return
        try:
            limit = float(str(raw).strip())
        except ValueError:
            return
        with self._pace_lock:
            if limit > 0 and self._limits.get(model) != limit:
                self._limits[model] = limit

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
            self._calls_since_flush += 1
            due = self._calls_since_flush >= LEDGER_EVERY
            if due:
                self._calls_since_flush = 0
        if due:
            self.flush_spend("periodic")

    def flush_spend(self, reason: str = "periodic") -> None:
        """Append current usage to the ledger. Best-effort and never raises —
        accounting must not be able to break a run."""
        if self._ledger is None:
            return
        try:
            with self._lock:
                if not self.usage:
                    return
                snapshot = {r: dict(b) for r, b in self.usage.items()}
            row = {"at": int(time.time()), "reason": reason, "label": self._label,
                   "pid": os.getpid(), "usage": snapshot,
                   "usd": self._cost_of(snapshot)["total_usd"]}
            self._ledger.parent.mkdir(parents=True, exist_ok=True)
            with self._ledger.open("a") as f:
                f.write(json.dumps(row) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            pass

    @staticmethod
    def _cost_of(usage: dict) -> dict:
        out, total = {}, 0.0
        for role, b in usage.items():
            pr = PRICES.get(b["model"])
            if not pr:
                out[role] = {**b, "usd": None}
                continue
            usd = b["in_tokens"] / 1e6 * pr["in"] + b["out_tokens"] / 1e6 * pr["out"]
            out[role] = {**b, "usd": round(usd, 4)}
            total += usd
        out["total_usd"] = round(total, 4)
        return out

    def cost_usd(self) -> dict:
        """Actual incurred cost from provider-reported usage, per role."""
        with self._lock:
            snapshot = {r: dict(b) for r, b in self.usage.items()}
        out = self._cost_of(snapshot)
        out["rate_limit_hits"] = self.rate_limited
        out["pace_waits"] = self._pace_waits
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
        # cheap token estimate: chars/4 for the prompt + a small output allowance
        est_tokens = (len(prompt) + len(system or "")) // 4 + OUTPUT_TOKEN_ALLOWANCE
        delay = 2.0
        for attempt in range(self.max_retries):
            try:
                self._pace(model, est_tokens)
                raw = self._client.chat.completions.with_raw_response.create(**kwargs)
                self._learn_limit(model, raw.headers)
                resp = raw.parse()
                self._meter(role, model, resp)
                return resp.choices[0].message.content or ""
            except Exception as e:
                name = type(e).__name__
                text = str(e)
                # Quota exhaustion arrives dressed as a 429 but is terminal —
                # the SDK reuses RateLimitError for insufficient_quota. Never
                # retry it; abort the run so the failure is unmistakable.
                if "insufficient_quota" in text or "exceeded your current quota" in text:
                    with self._lock:
                        self.failures += 1
                    raise QuotaExhausted(
                        "OpenAI billing quota exhausted — add credit or raise the "
                        "plan limit, then re-run: cached extractions are reused, "
                        "so only the unfinished remainder is re-paid.") from e
                # structured output unsupported / schema rejected: drop it once
                if "BadRequest" in name and "response_format" in kwargs:
                    kwargs.pop("response_format")
                    continue
                is_429 = "RateLimit" in name or "429" in text[:120]
                if attempt == self.max_retries - 1:
                    with self._lock:
                        self.failures += 1
                    raise
                with self._lock:
                    self.retries += 1
                    if is_429:
                        self.rate_limited += 1
                if is_429:
                    self._penalize(model, est_tokens)
                time.sleep(delay * (0.5 + random.random()))   # jitter, no lockstep
                delay = min(delay * 2, 30)
        raise RuntimeError("unreachable")
