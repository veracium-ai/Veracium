"""Opt-in error reporting — capture genuine engram errors to a local log file and,
only with consent, send that log to the maintainers for diagnosis.

Unlike telemetry (`engram.telemetry`), a log file is NOT content-free: a traceback
or an exception message can incidentally include memory content. So error reporting
is a SEPARATE, more careful channel:

  1. LOCAL FIRST. Errors are written to a local, user-owned rotating log file.
     That always happens when a reporter is attached; nothing leaves the machine.
  2. SENDING IS CONSENTED. A log is transmitted only with either advance permission
     (opt-in auto-send) or an explicit per-incident "yes". Default: neither.
  3. TRANSPARENT + REDACTED. `preview()` shows exactly what would be sent; a
     redaction pass (on by default) scrubs common content patterns from the tail.
  4. ANONYMOUS + BOUNDED. A random install id (shared with telemetry if present),
     minimal environment (engram / python / os), and only the log TAIL up to a cap.
  5. NEVER MAKES THINGS WORSE. The reporter never raises; a genuine error is logged
     and RE-RAISED to the host unchanged — reporting is strictly additive.

engram ships NO endpoint, so even "enabled" sends nothing until one is configured.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import re
import sys
import time
import traceback
import urllib.request
import uuid
from dataclasses import asdict, dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

SCHEMA_VERSION = 1
_LOGGER_NAME = "engram.diagnostics"


def _config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "engram"


def _state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "engram"


def _engram_version() -> str:
    try:
        from importlib.metadata import version
        return version("engram")
    except Exception:
        return "0+unknown"


def _install_id_from_telemetry() -> str:
    """Reuse the telemetry install id for anonymous correlation if the user already
    has one; otherwise mint a fresh random id here. Never derived from user/host."""
    try:
        from . import telemetry
        tid = telemetry.TelemetryConfig.load().install_id
        if tid:
            return tid
    except Exception:
        pass
    return uuid.uuid4().hex


@dataclass
class DiagnosticsConfig:
    log_enabled: bool = True            # write the local, user-owned error log
    report_enabled: bool = False        # advance permission to SEND a log on error
    prompt_on_error: bool = True        # if not pre-authorized: ask (interactive only)
    redact: bool = True                 # scrub common content patterns before sending
    endpoint: Optional[str] = None      # engram ships none; no endpoint → never sends
    log_path: Optional[str] = None
    install_id: str = ""
    max_report_bytes: int = 64 * 1024   # only ever send the log tail, capped
    report_min_interval_s: int = 300    # throttle auto-send so an error loop can't flood
    last_report: Optional[float] = None
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def path(cls) -> Path:
        return _config_dir() / "diagnostics.json"

    @classmethod
    def load(cls) -> "DiagnosticsConfig":
        p = cls.path()
        if p.exists():
            try:
                return cls(**{**asdict(cls()), **json.loads(p.read_text())})
            except Exception:
                pass
        return cls()

    def resolved_log_path(self) -> Path:
        return Path(self.log_path) if self.log_path else _state_dir() / "engram.log"

    def save(self) -> None:
        p = self.path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asdict(self), indent=2))

    def exists(self) -> bool:
        return self.path().exists()


# --- redaction (best-effort; the real safeguard is consent + preview) --------

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
# Target content-ish number shapes (phones, accounts, card/SSN-like runs, grouped
# amounts) while leaving ISO dates / log timestamps like 2026-07-11 22:39:33 alone.
_NUMBERS = [
    re.compile(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b"),          # 415-555-1234
    re.compile(r"\b\d{7,}\b"),                            # long unbroken digit runs
    re.compile(r"\$\s?\d{1,3}(?:,\d{3})+(?:\.\d+)?"),     # $4,200 / $1,234.50
]


def redact(text: str) -> str:
    text = _EMAIL.sub("<redacted-email>", text)
    for pat in _NUMBERS:
        text = pat.sub("<redacted-number>", text)
    return text


# --- the reporter ------------------------------------------------------------

class Reporter:
    """Owns the local error log and the consented send flow. Attach one to a Memory
    (or use directly). All methods are failure-tolerant: nothing here re-raises."""

    def __init__(self, config: Optional[DiagnosticsConfig] = None):
        self.config = config or DiagnosticsConfig.load()
        if not self.config.install_id:
            self.config.install_id = _install_id_from_telemetry()
        self._logger: Optional[logging.Logger] = None
        self._pending = 0

    # -- local logging --
    def _get_logger(self) -> Optional[logging.Logger]:
        if not self.config.log_enabled:
            return None
        if self._logger is not None:
            return self._logger
        try:
            path = self.config.resolved_log_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            logger = logging.getLogger(f"{_LOGGER_NAME}.{id(self)}")
            logger.setLevel(logging.INFO)
            logger.propagate = False
            if not logger.handlers:
                h = RotatingFileHandler(str(path), maxBytes=1_000_000, backupCount=2)
                h.setFormatter(logging.Formatter(
                    "%(asctime)s %(levelname)s %(message)s"))
                logger.addHandler(h)
            self._logger = logger
        except Exception:
            self._logger = None
        return self._logger

    def record_error(self, where: str, exc: BaseException,
                     context: Optional[dict] = None) -> None:
        """Log a genuine engram error locally (with traceback) and, if the user gave
        advance permission and set an endpoint, attempt to send it. Never raises."""
        try:
            logger = self._get_logger()
            if logger is not None:
                ctx = " ".join(f"{k}={v}" for k, v in (context or {}).items())
                tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                logger.error("op=%s %s\n%s", where, ctx, tb)
            self._pending += 1
        except Exception:
            pass
        # advance-permission auto-send (throttled). Prompted sending is driven by
        # the host/CLI via send(); a library op can't reliably prompt.
        try:
            cfg = self.config
            if cfg.report_enabled and cfg.endpoint and self._auto_send_due():
                self.send(reason=f"auto:{where}", interactive=False)
        except Exception:
            pass

    def _auto_send_due(self) -> bool:
        last = self.config.last_report
        return last is None or (time.time() - last) >= self.config.report_min_interval_s

    # -- payload + preview --
    def log_tail(self, max_bytes: Optional[int] = None) -> str:
        cap = max_bytes or self.config.max_report_bytes
        try:
            path = self.config.resolved_log_path()
            if not path.exists():
                return ""
            data = path.read_bytes()[-cap:]
            text = data.decode("utf-8", "replace")
            return redact(text) if self.config.redact else text
        except Exception:
            return ""

    def build_payload(self, reason: Optional[str] = None) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "install_id": self.config.install_id,
            "reason": reason,
            "engram_version": _engram_version(),
            "python": platform.python_version(),
            "os": platform.system(),
            "redacted": self.config.redact,
            "log_tail": self.log_tail(),
        }

    def preview(self, reason: Optional[str] = None) -> dict:
        """Exactly what a send would POST (redacted if enabled) — for review before
        consenting. This is the log content that would leave the machine."""
        return self.build_payload(reason)

    def has_pending(self) -> bool:
        return self._pending > 0

    # -- consented send --
    def _confirm(self, interactive: Optional[bool]) -> bool:
        is_tty = sys.stdin.isatty() if interactive is None else interactive
        if not is_tty:
            return False
        p = self.preview()
        print(CONSENT_TEXT)
        print(f"\n  install id: {p['install_id']}\n  log path:   "
              f"{self.config.resolved_log_path()}\n  size:       "
              f"{len(p['log_tail'])} bytes (redacted={p['redacted']})")
        try:
            return input("\nSend this diagnostic log now? [y/N] ").strip().lower() in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    def send(self, *, reason: Optional[str] = None, interactive: Optional[bool] = None,
             poster=None) -> bool:
        """Send the current log tail if consented. Consent = advance permission
        (report_enabled) OR an interactive yes. No endpoint → never sends. Never
        raises. Returns True iff a send happened."""
        cfg = self.config
        if not cfg.endpoint:
            return False
        if not cfg.report_enabled and not self._confirm(interactive):
            return False
        payload = self.build_payload(reason)
        if not payload["log_tail"]:
            return False
        try:
            (poster or _post)(cfg.endpoint, payload)
        except Exception:
            return False
        cfg.last_report = time.time()
        try:
            cfg.save()
        except Exception:
            pass
        self._pending = 0
        return True


def _post(endpoint: str, payload: dict) -> None:
    req = urllib.request.Request(
        endpoint, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "engram-diagnostics"},
        method="POST")
    urllib.request.urlopen(req, timeout=15).close()


# --- consent -----------------------------------------------------------------

CONSENT_TEXT = """\
engram can send its LOCAL error log to the maintainers to help diagnose a genuine
bug. Unlike anonymous usage statistics, a log CAN contain fragments of your memory
data (e.g. inside an error message). engram redacts obvious patterns (emails,
number runs) and shows you exactly what would be sent first. It is anonymous (a
random install id) and off by default; enable per-incident here, or grant advance
permission with `engram diagnostics enable`."""


def prompt_consent(*, endpoint: Optional[str] = None,
                   interactive: Optional[bool] = None) -> DiagnosticsConfig:
    """First-run advance-permission question for AUTO-sending logs on error. Prompts
    only on a TTY; otherwise records report disabled (never assume yes). Idempotent."""
    cfg = DiagnosticsConfig.load()
    if cfg.exists():
        return cfg
    is_tty = sys.stdin.isatty() if interactive is None else interactive
    enabled = False
    if is_tty:
        try:
            print(CONSENT_TEXT)
            ans = input("\nAutomatically send error logs when engram hits a genuine "
                        "bug? [y/N] ").strip().lower()
            enabled = ans in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            enabled = False
    if not cfg.install_id:
        cfg.install_id = _install_id_from_telemetry()
    cfg.report_enabled = enabled
    if endpoint is not None:
        cfg.endpoint = endpoint
    cfg.save()
    return cfg


def set_report_enabled(enabled: bool, *, endpoint: Optional[str] = None) -> DiagnosticsConfig:
    cfg = DiagnosticsConfig.load()
    if not cfg.install_id:
        cfg.install_id = _install_id_from_telemetry()
    cfg.report_enabled = enabled
    if endpoint is not None:
        cfg.endpoint = endpoint
    cfg.save()
    return cfg


def load_reporter() -> Optional[Reporter]:
    """A Reporter iff local logging is enabled (the default) — used by the CLI/MCP
    entry points to give engram a log to capture errors into. The library core never
    creates one implicitly; embedding hosts pass their own (or None)."""
    cfg = DiagnosticsConfig.load()
    return Reporter(cfg) if cfg.log_enabled else None
