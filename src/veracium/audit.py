"""Opt-in operation audit log — who called what, when, over which user.

Attach via `Memory(audit=AuditLog("audit.jsonl"))`. Every Memory operation
(remember/recall/answer/maintain/dispute/confirm/forget/export/import) appends
one JSON line: UTC timestamp, operation, user_id, and the operation's
content-free counters. No memory text ever appears — the log records *that*
operations happened, not what memory says (pair with `export_memory` when an
inspection needs content).

The log is append-only and owned by the host: rotate, ship, or retain it under
your own policy. Like the other sinks, auditing must never break memory —
failures are swallowed."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


class AuditLog:
    def __init__(self, path):
        self.path = Path(path)
        self._lock = Lock()

    def record(self, op: str, user_id: str, fields: dict) -> None:
        """Append one audit line. Never raises."""
        try:
            line = json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                               "op": op, "user_id": user_id, **fields})
            with self._lock, self.path.open("a") as f:
                f.write(line + "\n")
        except Exception:
            pass  # auditing must never break memory

    def entries(self, *, user_id: str | None = None, op: str | None = None) -> list[dict]:
        """Read the log back, optionally filtered. Convenience for hosts/tests."""
        if not self.path.exists():
            return []
        out = []
        with self.path.open() as f:
            for ln in f:
                if not ln.strip():
                    continue
                rec = json.loads(ln)
                if user_id is not None and rec.get("user_id") != user_id:
                    continue
                if op is not None and rec.get("op") != op:
                    continue
                out.append(rec)
        return out
