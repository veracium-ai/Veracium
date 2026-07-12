"""Opt-in, anonymous, content-free product telemetry.

Guarantees, in order of importance:
  1. DEFAULT OFF. Nothing is collected-for-sending or sent without an explicit
     opt-in recorded in the user config.
  2. CONTENT-FREE BY CONSTRUCTION. Only the whitelisted scalar fields below are
     ever recorded; `record()` drops everything else. No facts, names, entity
     ids, queries, answers, or free text can enter the payload — enforced in code,
     not by convention.
  3. ANONYMOUS. A random install id (no user ids, no hostnames) identifies a
     deployment across weeks; that's all.
  4. REVOCABLE + TRANSPARENT. `preview()` returns exactly what would be sent;
     opt-out is one call. The endpoint is explicit — veracium ships none, so even
     "enabled" sends nothing until an endpoint is configured.

Where veracium is embedded in a host application, the HOST obtains end-user consent
and configures this; veracium defaults to off and never phones home on its own.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# --- the content-free event schema (whitelist of scalar fields per event) ---
# Anything not listed here is silently dropped by record(). Values are coerced to
# int / float / bool. No string values are ever accepted (strings could be content),
# except the event name itself, which is one of these fixed keys.
EVENT_FIELDS: dict[str, set[str]] = {
    "ingest": {"facts", "quarantined", "episodes", "supersessions", "reinforcements",
               "unparseable", "distill_in_tok", "distill_out_tok", "ms"},
    "recall": {"wiki_used", "subgraph_edges", "grounded_items", "unverified_items", "ms"},
    "answer": {"abstained", "gate_in_tok", "gate_out_tok", "ms"},
    "maintain": {"lapsed", "decayed", "flagged", "consolidated_in", "consolidated_out"},
    "selfcheck": {"total_ok", "total_n", "injection_asserts", "supersession_ok",
                  "supersession_n", "abstention_ok", "abstention_n"},
}

SCHEMA_VERSION = 1


def _config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "veracium"


@dataclass
class TelemetryConfig:
    enabled: bool = False
    install_id: str = ""
    endpoint: Optional[str] = None   # veracium ships none; no endpoint → never sends
    interval_days: int = 7
    last_sent: Optional[float] = None  # epoch seconds
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def path(cls) -> Path:
        return _config_dir() / "telemetry.json"

    @classmethod
    def load(cls) -> "TelemetryConfig":
        p = cls.path()
        if p.exists():
            try:
                return cls(**{**asdict(cls()), **json.loads(p.read_text())})
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        p = self.path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asdict(self), indent=2))

    def exists(self) -> bool:
        return self.path().exists()


class Collector:
    """Accumulates content-free counters. Recording is always local and cheap;
    sending only happens via flush_if_due() when opted in."""

    def __init__(self):
        self._agg: dict[str, dict[str, float]] = {e: {} for e in EVENT_FIELDS}
        self._counts: dict[str, int] = {e: 0 for e in EVENT_FIELDS}

    def record(self, event: str, fields: dict) -> None:
        allowed = EVENT_FIELDS.get(event)
        if allowed is None:
            return
        self._counts[event] += 1
        bucket = self._agg[event]
        for k, v in fields.items():
            if k not in allowed:
                continue  # drop anything off-whitelist (defense against content leaks)
            if isinstance(v, bool):
                num = 1.0 if v else 0.0
            elif isinstance(v, (int, float)):
                num = float(v)
            else:
                continue  # never accept strings/objects
            bucket[k] = bucket.get(k, 0.0) + num

    def snapshot(self) -> dict:
        """Aggregated payload body (sums + operation counts). Content-free."""
        return {"events": {e: {"n": self._counts[e], "sums": dict(self._agg[e])}
                           for e in EVENT_FIELDS if self._counts[e]}}

    def reset(self) -> None:
        self.__init__()


def preview(config: TelemetryConfig, collector: Collector) -> dict:
    """Exactly what a flush would POST — for `veracium telemetry preview`."""
    return {"schema_version": SCHEMA_VERSION, "install_id": config.install_id,
            "period_start": config.last_sent, "period_end": time.time(),
            **collector.snapshot()}


def flush_if_due(config: TelemetryConfig, collector: Collector, *,
                 now: Optional[float] = None, poster=None) -> bool:
    """POST the aggregate if opted in, an endpoint is set, and the interval has
    elapsed. Never raises — telemetry must never break the host. Returns True if a
    send happened."""
    now = now or time.time()
    if not (config.enabled and config.endpoint):
        return False
    if config.last_sent and (now - config.last_sent) < config.interval_days * 86400:
        return False
    payload = preview(config, collector)
    try:
        (poster or _post)(config.endpoint, payload)
    except Exception:
        return False  # silent: a telemetry failure is never the app's problem
    config.last_sent = now
    config.save()
    collector.reset()
    return True


def _post(endpoint: str, payload: dict) -> None:
    req = urllib.request.Request(
        endpoint, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "veracium-telemetry"},
        method="POST")
    urllib.request.urlopen(req, timeout=10).close()


# --- consent ---------------------------------------------------------------

CONSENT_TEXT = """\
veracium can send anonymous, content-free usage statistics once a week to help
improve the library. It would share ONLY aggregate counters — how often facts are
extracted, claims quarantined, and answers abstained; token/latency totals; and
self-check scores. It NEVER sends your memory: no facts, names, messages, queries,
or answers. It is anonymous (a random install id) and you can turn it off any time
with `veracium telemetry disable`. Preview exactly what would be sent with
`veracium telemetry preview`.

Enable anonymous usage statistics?"""


def prompt_consent(*, endpoint: Optional[str] = None,
                   interactive: Optional[bool] = None) -> TelemetryConfig:
    """First-run consent. Prompts only on an interactive TTY; otherwise records a
    disabled config (never assume yes). Idempotent: returns the existing config if
    already chosen."""
    cfg = TelemetryConfig.load()
    if cfg.exists():
        return cfg
    import sys
    is_tty = sys.stdin.isatty() if interactive is None else interactive
    enabled = False
    if is_tty:
        try:
            ans = input(CONSENT_TEXT + " [y/N] ").strip().lower()
            enabled = ans in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            enabled = False
    cfg = TelemetryConfig(enabled=enabled, install_id=uuid.uuid4().hex,
                          endpoint=endpoint)
    cfg.save()
    return cfg


def set_enabled(enabled: bool, *, endpoint: Optional[str] = None) -> TelemetryConfig:
    cfg = TelemetryConfig.load()
    if not cfg.install_id:
        cfg.install_id = uuid.uuid4().hex
    cfg.enabled = enabled
    if endpoint is not None:
        cfg.endpoint = endpoint
    cfg.save()
    return cfg


def load_collector_if_enabled() -> Optional[Collector]:
    """A Collector iff the user config opts in — used by the CLI/MCP entry points
    to wire consented telemetry into a Memory. The library core never calls this
    implicitly."""
    return Collector() if TelemetryConfig.load().enabled else None
