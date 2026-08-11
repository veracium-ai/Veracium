"""Opt-in metering for any `Complete` callable.

Veracium deliberately never owns credentials or model choice — `Complete`
returns a bare string, so the library cannot see token usage (that is the
trade `2767a35` recorded when it removed the never-populated token fields
from the telemetry whitelist). `Metered` is the planned host-side answer:
wrap YOUR callable, and the wrapper counts what the library cannot.

    from veracium.llm.metered import Metered
    llm = Metered(your_complete, counter=your_count_tokens)  # counter optional
    mem = Memory(llm=llm, ...)
    ...
    llm.totals()          # {"distill": {"calls": 3, "in_tok": ..., ...}, ...}
    llm.totals(reset=True)

The wrapper is HOST-SIDE ACCOUNTING ONLY: totals stay in this object, owned by
the host, per-process. Nothing here writes to telemetry, audit, or
introspect — those surfaces are guarded and consent-bearing, and routing
usage into them is a spec of its own (see the `2767a35` whitelist comment and
spec 0015's consent-versioning mechanism; token fields may not be whitelisted
until they are both written AND consented).

Token counting: pass `counter=fn(text) -> int` for real counts (e.g. your
tokenizer). Without one, the wrapper records calls and CHARACTER counts under
`in_chars`/`out_chars` and never fabricates token numbers — an estimate
labelled as tokens is the kind of claim-vs-code mismatch this codebase has
had to retract before.
"""

from __future__ import annotations

import threading
from typing import Callable, Optional


class Metered:
    """Wraps any `Complete`-shaped callable with per-role usage accounting."""

    def __init__(self, complete: Callable, *,
                 counter: Optional[Callable[[str], int]] = None):
        self._complete = complete
        self._counter = counter
        self._lock = threading.Lock()
        self._usage: dict[str, dict[str, int]] = {}

    def __call__(self, prompt: str, *, system: Optional[str] = None,
                 role: str = "compile", json_schema: Optional[dict] = None) -> str:
        out = self._complete(prompt, system=system, role=role,
                             json_schema=json_schema)
        text_in = (system or "") + prompt
        with self._lock:
            u = self._usage.setdefault(role, {"calls": 0})
            u["calls"] += 1
            if self._counter is not None:
                u["in_tok"] = u.get("in_tok", 0) + self._counter(text_in)
                u["out_tok"] = u.get("out_tok", 0) + self._counter(out or "")
            else:
                u["in_chars"] = u.get("in_chars", 0) + len(text_in)
                u["out_chars"] = u.get("out_chars", 0) + len(out or "")
        return out

    def totals(self, *, reset: bool = False) -> dict[str, dict[str, int]]:
        with self._lock:
            snap = {r: dict(u) for r, u in self._usage.items()}
            if reset:
                self._usage.clear()
        return snap
