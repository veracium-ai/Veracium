"""Extraction cache: replayable, keyed on the full extraction identity.

A `CachedComplete` wraps the real provider. On a hit it returns the stored
extraction for that (turn, extraction-config); on a miss it calls through and
stores. The veracium write path — supersession, T1 absorption + the
same-disclosure-class guard, quarantine routing, episodes — always runs live
on top, so a replay exercises today's engine over frozen extractions.

Not "reproducible" in the statistical sense: the first miss freezes one
stochastic draw per key and every later question reusing that turn replays it.
That is the point (cost, comparability) and its limit — the variance protocol
(`--variance`) measures what it hides.

The key hashes actual CONTENT, not hand-maintained version labels, so a
forgotten bump cannot poison replay. Labels still go in the run record for
humans.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path

CACHE_DIR = Path.home() / "Datasets" / "longmemeval" / "cache"

# Bump when the serialization of the cached VALUE changes (not the key inputs).
SCHEMA_VERSION = 1


def _sha(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode())
        h.update(b"\x1f")
    return h.hexdigest()


class CacheLock:
    """Single-process discipline (spec §11): concurrent writers are excluded
    rather than made safe — one lock file, removed on exit."""

    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            # A killed run (SIGTERM/SIGKILL) never runs __exit__, so distinguish
            # a live holder from a corpse instead of making the operator delete
            # the file by hand and guess which it was.
            holder = self._holder_pid()
            if holder is not None and self._alive(holder):
                raise RuntimeError(
                    f"cache is locked by a LIVE run (pid {holder}, {self.path}). "
                    f"LongMemEval runs are single-process.")
            print(f"[cache] clearing stale lock from dead pid {holder} ({self.path})")
            self.path.unlink(missing_ok=True)
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return self

    def _holder_pid(self):
        try:
            return int(self.path.read_text().strip())
        except (OSError, ValueError):
            return None

    @staticmethod
    def _alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True     # exists, owned by someone else
        return True

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)
        return False


class CachedComplete:
    """Provider wrapper. Only `role="distill"` calls are cached — compile/gate
    calls are per-question and not replayable across questions."""

    def __init__(self, inner, *, path: Path, identity: dict, enabled: bool = True):
        """`identity` = every non-text input that can change an extraction:
        model id, decoding params, prompt content hash, output-schema content
        hash, parser version, truncation policy, context-window policy. Hashed
        once into the key prefix."""
        self.inner = inner
        self.path = Path(path)
        self.enabled = enabled
        self.identity = dict(identity)
        self._id_hash = _sha(json.dumps(self.identity, sort_keys=True))
        self._mem: dict[str, str] = {}
        self.stats = {"hits": 0, "misses": 0, "writes": 0, "incompatible": 0}
        # Runs parallelize across ITEMS, so one cache instance is shared by
        # worker threads: the dict/stats/file need a lock, and the bound key
        # must be per-thread (it identifies the turn a given worker is on).
        self._lock = threading.Lock()
        self._local = threading.local()
        if self.enabled:
            self._load()

    # -- key ----------------------------------------------------------------
    def key_for(self, event_text: str, *, author: str, event_type: str,
                date: str) -> str:
        return _sha(self._id_hash, event_text, author, event_type, date)

    def parts_for(self, event_text: str, *, author: str, event_type: str,
                  date: str) -> dict:
        """The key's components, stored beside the value. If an identity field
        changes in a way that cannot affect extraction output, entries can be
        re-keyed from these instead of re-extracted (which is what the
        identity-leak incident cost)."""
        return {"text_sha": _sha(event_text)[:32], "author": author,
                "event_type": event_type, "date": date,
                "identity": self._id_hash[:16]}

    def bind(self, key: str, parts: dict | None = None) -> None:
        """The runner binds the key for the turn it is about to ingest; the
        provider call itself carries no turn identity. Thread-local: parallel
        workers are each mid-turn on a different item."""
        self._local.key = key
        self._local.parts = parts

    # -- storage ------------------------------------------------------------
    def _load(self) -> None:
        if not self.path.exists():
            return
        for line in self.path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue  # partially written tail: ignore, it will be re-extracted
            if rec.get("schema") != SCHEMA_VERSION:
                self.stats["incompatible"] += 1
                continue  # entry written under an older value format
            if "key" in rec and "value" in rec:
                self._mem[rec["key"]] = rec["value"]

    def _append(self, key: str, value: str, parts: dict | None = None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        rec = {"schema": SCHEMA_VERSION, "key": key, "value": value,
               "stored_at": int(time.time())}
        if parts:
            rec["parts"] = parts
        # append + flush + fsync: a killed run leaves whole lines, never a
        # half-line that silently truncates a later parse
        with self.path.open("a") as f:
            f.write(json.dumps(rec) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self.stats["writes"] += 1

    # -- provider interface --------------------------------------------------
    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        key = getattr(self._local, "key", None)
        if not (self.enabled and role == "distill" and key):
            return self.inner(prompt, system=system, role=role, json_schema=json_schema)
        with self._lock:
            if key in self._mem:
                self.stats["hits"] += 1
                return self._mem[key]
            self.stats["misses"] += 1
        # provider call OUTSIDE the lock: parallel workers must not serialize on
        # each other's network time. A duplicate concurrent miss on the same key
        # costs one extra call and resolves to one stored value — acceptable.
        out = self.inner(prompt, system=system, role=role, json_schema=json_schema)
        with self._lock:
            self._mem[key] = out
            self._append(key, out, getattr(self._local, "parts", None))
        return out

    @property
    def unique_keys(self) -> int:
        return len(self._mem)
