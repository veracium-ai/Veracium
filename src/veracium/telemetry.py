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
# NOTE — six fields were removed from this whitelist because they were listed
# here and populated NOWHERE. A whitelist describes what we send; an entry no
# call site writes is a promise, not a payload. CONSENT_TEXT was built on this
# list and promised users "token/latency totals" — we collected less than we
# said, which is the safe direction for privacy but is still a claim the code
# did not honour.
#
#   distill_in_tok, distill_out_tok, gate_in_tok, gate_out_tok
#       Cannot be populated today BY DESIGN: `Complete` returns a bare string
#       and veracium never owns credentials or model choice, so usage is not
#       visible to us. Re-add only with the planned `veracium.llm.metered`
#       opt-in wrapper that makes it visible.
#
#   supersessions, reinforcements
#       RESTORED by accepted specs/0015 (the spec 2767a35 asked for): counted at
#       the planner (fresh commits only), consent-gated at record time
#       (FIELD_MIN_VERSION 2), stripped from the MCP tool result (the oracle).
#
# `tests/test_telemetry_claims.py` fails if any field is whitelisted but never
# populated, which is how all six were found.
EVENT_FIELDS: dict[str, set[str]] = {
    "ingest": {"facts", "quarantined", "episodes", "unparseable", "ms",
               # specs/0015 (accepted): populated by Memory.remember via the
               # planner's SupersessionCounts; consent-gated (min version 2).
               "supersessions", "reinforcements"},
    "recall": {"wiki_used", "subgraph_edges", "grounded_items", "unverified_items", "proactive",
               "trimmed", "ms"},  # "trimmed" not "truncated": the content-free
                                  # guard rejects payloads containing "cat"
    "answer": {"abstained", "ms"},
    "maintain": {"lapsed", "decayed", "flagged", "consolidated_in", "consolidated_out"},
    "forget": {"edges", "episodes"},
    "introspect": {"facts", "claims", "episodes"},
    "feedback": {"disputed", "confirmed", "corrected"},
    "outcome": {"new", "upgraded"},
    "selfcheck": {"total_ok", "total_n", "injection_asserts", "supersession_ok",
                  "supersession_n", "abstention_ok", "abstention_n"},
}

SCHEMA_VERSION = 2  # v2 (specs/0015): the supersession/reinforcement counters

# specs/0015 §4: fields gated on the CONSENTED schema version — a field is sent
# only if it was RECORDED under a consent that admitted it (record-time gating).
FIELD_MIN_VERSION: dict[tuple, int] = {("ingest", "supersessions"): 2,
                                       ("ingest", "reinforcements"): 2}

# The tombstone sentinel (specs/0015 R10-1): equals NO valid persisted epoch
# (epochs are positive ints); a tombstoned collector drops every record until a
# successful valid-config adoption.
TOMBSTONE = "tombstoned"


class TelemetryLockError(RuntimeError):
    """An EXPLICIT consent transition could not acquire the consent lock — the
    user's choice must never silently fail to persist (specs/0015 §4 rule 2)."""


def _acquire_lock(deadline_s: float = 2.0):
    """The OS-exclusive advisory lock (specs/0015 §4 rule 2, pinned by call):
    POSIX `flock(fd, LOCK_EX | LOCK_NB)`; Windows `msvcrt.locking(LK_NBLCK, 1)`.
    Nonblocking, 50 ms retries against a monotonic deadline. Returns the held
    fd or None (callers split by operation class). The descriptor is held for
    the lock's lifetime — that is what makes process-death release work."""
    lock_path = _config_dir() / "telemetry.json.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
    end = time.monotonic() + deadline_s
    while True:
        try:
            if os.name == "posix":
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:  # pragma: no cover — exercised by the platform-gated tests
                import msvcrt
                if os.fstat(fd).st_size == 0:
                    os.write(fd, b"\0")
                os.lseek(fd, 0, 0)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return fd
        except (BlockingIOError, InterruptedError, OSError):
            if time.monotonic() >= end:
                os.close(fd)
                return None
            time.sleep(0.05)


def _release_lock(fd) -> None:
    try:
        if os.name == "posix":
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN)
        else:  # pragma: no cover
            import msvcrt
            os.lseek(fd, 0, 0)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(fd)


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
    # specs/0015: the DISPLAYED-AND-ACCEPTED consent version. Default 1 — the
    # default is a stamping carrier (R1-F2); only affirmative display flows
    # write the current version.
    schema_version: int = 1
    # specs/0015: the monotonic consent-transition counter; positive int; a
    # persisted invalid/absent value is normalized under the lock (I16).
    consent_epoch: int = 1

    @classmethod
    def path(cls) -> Path:
        return _config_dir() / "telemetry.json"

    @classmethod
    def load(cls) -> "TelemetryConfig":
        p = cls.path()
        if p.exists():
            try:
                cfg = cls(**{**asdict(cls()), **json.loads(p.read_text())})
            except Exception:
                return cls()  # unknown key / unreadable: whole-config fail-closed
            # specs/0015 I16 — closed validity predicates, floors never current:
            sv = cfg.schema_version
            if not (isinstance(sv, int) and not isinstance(sv, bool)
                    and 1 <= sv <= SCHEMA_VERSION):
                cfg.schema_version = 1
            ce = cfg.consent_epoch
            if not (isinstance(ce, int) and not isinstance(ce, bool) and ce >= 1):
                cfg.consent_epoch = 0  # invalid marker: normalized under lock
            return cfg
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

    def __init__(self, consent_epoch: int = 1, schema_version: int = 1):
        # specs/0015: the consent this collector was constructed/adopted under.
        # The record gate binds AT RECORD TIME to these; TOMBSTONE drops all.
        self.consent_epoch = consent_epoch
        self.schema_version = schema_version
        self._clear()

    def _clear(self):
        self._agg: dict[str, dict[str, float]] = {e: {} for e in EVENT_FIELDS}
        self._counts: dict[str, int] = {e: 0 for e in EVENT_FIELDS}

    def tombstone(self) -> None:
        """specs/0015 R10-1: an observed absent/malformed config. Drops every
        subsequent record; equals no valid epoch; resumes only via a
        successful valid-config adoption."""
        self._clear()
        self.consent_epoch = TOMBSTONE

    def adopt_consent(self, config: "TelemetryConfig") -> None:
        """specs/0015 §4 rule 4: ANY epoch difference — including ABA and the
        tombstone — discards pending aggregates before adopting."""
        if self.consent_epoch != config.consent_epoch:
            self._clear()
        self.consent_epoch = config.consent_epoch
        self.schema_version = config.schema_version

    def record(self, event: str, fields: dict) -> None:
        if self.consent_epoch == TOMBSTONE:
            return  # tombstoned: every record dropped (I17b)
        allowed = EVENT_FIELDS.get(event)
        if allowed is None:
            return
        self._counts[event] += 1
        bucket = self._agg[event]
        for k, v in fields.items():
            if k not in allowed:
                continue  # drop anything off-whitelist (defense against content leaks)
            if FIELD_MIN_VERSION.get((event, k), 1) > self.schema_version:
                continue  # specs/0015 I8: never ACCUMULATES under a consent
                          # that does not admit it (record-time gating)
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
        """Clears aggregates ONLY; the adopted consent state is preserved
        (specs/0015 I15 — a defaulted re-__init__ would downgrade a v2
        collector or raise after the POST)."""
        self._clear()


def _read_config_status():
    """specs/0015 R7-2: the under-lock read WITH status — (status, config),
    status ∈ {"valid", "absent", "malformed"}. Absent/malformed are decided by
    the read, never inferred from default-valued objects."""
    p = TelemetryConfig.path()
    if not p.exists():
        return "absent", TelemetryConfig()
    try:
        cfg = TelemetryConfig(**{**asdict(TelemetryConfig()),
                                 **json.loads(p.read_text())})
    except Exception:
        return "malformed", TelemetryConfig()
    return "valid", TelemetryConfig.load()


def _normalize_epoch_locked(cfg: TelemetryConfig) -> TelemetryConfig:
    """A parse-valid config with an invalid/absent epoch (load() marked it 0)
    is normalized UNDER THE LOCK to a fresh persisted positive epoch BEFORE
    any collector adopts it (specs/0015 R5-2/R6-2)."""
    if cfg.consent_epoch == 0:
        cfg.consent_epoch = 1
        cfg.save()
    return cfg


def _payload(config: TelemetryConfig, collector: Collector) -> dict:
    body = {"schema_version": SCHEMA_VERSION, "install_id": config.install_id,
            "period_start": config.last_sent, "period_end": time.time(),
            **collector.snapshot()}
    # defense-in-depth re-strip (the binding gate is record-time — I8)
    for (ev, field), minv in FIELD_MIN_VERSION.items():
        if minv > config.schema_version:
            ev_body = body.get("events", {}).get(ev)
            if ev_body:
                ev_body.get("sums", {}).pop(field, None)
    return body


def preview(config: TelemetryConfig, collector: Collector):
    """specs/0015 R9-3, the TOTAL preview matrix: lock failure / absent /
    malformed / disabled → None; valid + enabled → the adopted would-be
    payload REGARDLESS of due time or endpoint. Preview NEVER POSTs."""
    fd = _acquire_lock()
    if fd is None:
        return None
    try:
        status, cfg = _read_config_status()
        if status != "valid":
            collector.tombstone()
            return None
        cfg = _normalize_epoch_locked(cfg)
        collector.adopt_consent(cfg)
        if not cfg.enabled:
            return None
        return _payload(cfg, collector)
    finally:
        _release_lock(fd)


def flush_if_due(config: TelemetryConfig, collector: Collector, *,
                 now: Optional[float] = None, poster=None) -> bool:
    """POST the aggregate if opted in, an endpoint is set, and the interval has
    elapsed. Never raises — telemetry must never break the host. Returns True if a
    send happened."""
    now = now or time.time()
    # (a) lock first — failure: False, nothing sent, NO adoption (specs/0015 §4.5)
    fd = _acquire_lock()
    if fd is None:
        return False
    try:
        # (b) status read; (c) branch by status FIRST — absent/malformed:
        # tombstone, NO write, NO normalization (a deleted config is never
        # recreated; malformed never rewritten)
        status, cfg = _read_config_status()
        if status != "valid":
            collector.tombstone()
            return False
        cfg = _normalize_epoch_locked(cfg)
        collector.adopt_consent(cfg)   # adoption precedes eligibility (R8-2)
        # (d) eligibility — adoption has already happened
        if not (cfg.enabled and cfg.endpoint):
            return False
        if cfg.last_sent and (now - cfg.last_sent) < cfg.interval_days * 86400:
            return False
        payload = _payload(cfg, collector)
        authorized_epoch = cfg.consent_epoch
        endpoint = cfg.endpoint
    finally:
        _release_lock(fd)
    # (e) the POST is AUTHORIZED by the recheck above; it may complete after a
    # later revocation (the narrow claim: no data recorded after a revocation
    # is ever sent — record-time gating + the epoch discard guarantee it)
    try:
        (poster or _post)(endpoint, payload)
    except Exception:
        return False  # nothing was sent
    # (f) post-POST, TOTAL (the terminal matrix): True always — a send happened
    collector.reset()
    fd = _acquire_lock()
    if fd is None:
        return True  # lock failure post-send: last_sent unwritten (interval drift)
    try:
        status, cur = _read_config_status()
        if status != "valid":
            collector.tombstone()   # deleted → NEVER recreated; malformed → untouched
            return True
        cur = _normalize_epoch_locked(cur)
        if cur.consent_epoch != authorized_epoch:
            collector.adopt_consent(cur)  # consent changed mid-POST: discard+adopt
        cur.last_sent = now
        cur.save()                   # updates ONLY on the CURRENT file (R5-1)
        return True
    except Exception:
        return True                  # write failure: last_sent unwritten
    finally:
        try:
            _release_lock(fd)
        except Exception:
            pass


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
extracted, claims quarantined, values superseded or reinforced, and answers
abstained; latency totals; and
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
    fd = _acquire_lock()
    if fd is None:
        raise TelemetryLockError("consent prompt could not acquire the consent lock")
    try:
        cfg = TelemetryConfig(enabled=enabled, install_id=uuid.uuid4().hex,
                              endpoint=endpoint,
                              # only AFFIRMATIVE consent stamps current (I13);
                              # every non-acceptance path ends at 1
                              schema_version=SCHEMA_VERSION if enabled else 1)
        cfg.save()
        return cfg
    finally:
        _release_lock(fd)


def set_enabled(enabled: bool, *, endpoint: Optional[str] = None) -> TelemetryConfig:
    """Toggles `enabled` under the lock. NEVER stamps `schema_version` (I12 —
    the consent version belongs to the DISPLAY event); bumps `consent_epoch`
    iff the persisted (enabled, schema_version) pair actually changed (§4.3).
    Raises TelemetryLockError on lock deadline — an explicit consent choice
    must never silently fail to persist."""
    fd = _acquire_lock()
    if fd is None:
        raise TelemetryLockError("set_enabled could not acquire the consent lock")
    try:
        cfg = TelemetryConfig.load()
        if cfg.consent_epoch == 0:
            cfg = _normalize_epoch_locked(cfg)
        if not cfg.install_id:
            cfg.install_id = uuid.uuid4().hex
        changed = cfg.enabled != enabled
        cfg.enabled = enabled
        if endpoint is not None:
            cfg.endpoint = endpoint
        if changed:
            cfg.consent_epoch += 1
        cfg.save()
        return cfg
    finally:
        _release_lock(fd)


def accept_current_consent(*, endpoint: Optional[str] = None) -> TelemetryConfig:
    """The DISPLAY-flow acceptance (specs/0015 I13): the caller has shown
    CONSENT_TEXT and the user affirmed — enables AND stamps the current
    consent version; the epoch bumps iff the persisted (enabled,
    schema_version) pair actually changed. `set_enabled` deliberately cannot
    do this (I12)."""
    fd = _acquire_lock()
    if fd is None:
        raise TelemetryLockError("consent acceptance could not acquire the consent lock")
    try:
        cfg = TelemetryConfig.load()
        if cfg.consent_epoch == 0:
            cfg = _normalize_epoch_locked(cfg)
        if not cfg.install_id:
            cfg.install_id = uuid.uuid4().hex
        changed = (cfg.enabled, cfg.schema_version) != (True, SCHEMA_VERSION)
        cfg.enabled = True
        cfg.schema_version = SCHEMA_VERSION
        if endpoint is not None:
            cfg.endpoint = endpoint
        if changed:
            cfg.consent_epoch += 1
        cfg.save()
        return cfg
    finally:
        _release_lock(fd)


def load_collector_if_enabled() -> Optional[Collector]:
    """A Collector iff the user config opts in — used by the CLI/MCP entry points
    to wire consented telemetry into a Memory. The library core never calls this
    implicitly."""
    fd = _acquire_lock()
    if fd is None:
        return None  # specs/0015 R8-3: no collector at all beats an unnormalized one
    try:
        status, cfg = _read_config_status()
        if status != "valid" or not cfg.enabled:
            return None
        cfg = _normalize_epoch_locked(cfg)
        return Collector(consent_epoch=cfg.consent_epoch,
                         schema_version=cfg.schema_version)
    finally:
        _release_lock(fd)
