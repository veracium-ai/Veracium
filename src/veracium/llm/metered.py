"""Opt-in metering for any `Complete` callable — the specs/0017 producer side.

Veracium deliberately never owns credentials or model choice — `Complete`
returns a bare string, so the library cannot see token usage (the trade
`2767a35` recorded). `Metered` is the host-side answer: wrap YOUR callable,
and the wrapper counts what the library cannot.

    from veracium.llm.metered import Metered
    llm = Metered(your_complete, counter=your_count_tokens)  # counter optional
    mem = Memory(llm=llm, ...)
    ...
    llm.totals()          # the host's own per-process view
    llm.totals(reset=True)

specs/0017 (accepted): metering detection is an AFFIRMATIVE capability. The
wrapper carries `metering_capability = "veracium-metered-v1"` and a listener
interface — `add_usage_listener(fn) -> handle` /
`remove_usage_listener(handle)` (idempotent). After each call whose BOTH
token counts validate, the wrapper emits exactly one event
`{"role": str, "in_tok": int, "out_tok": int}` synchronously, in the context
that entered `__call__` (at return, on the caller's side — a `Complete` that
internally fans out still attributes to the calling operation), to a
SNAPSHOT of the listener list taken under the lock and invoked OUTSIDE it
with per-listener exception isolation. A listener added during an emission
sees the next event; one removed during an emission may still receive the
in-flight event, never a later one.

The accounting is ATOMIC (specs/0017 §4c): the provider is called first and
its output is ALWAYS returned; both counts are computed and validated into
locals outside the lock against the ONE shared validity predicate
(`count_valid`); any failure — exception, non-int, bool, negative, over
2**53 — from either invocation discards the WHOLE token pair before any
token-state mutation or emission. `calls` and the character counts ride the
always-valid block. Without a `counter`, the wrapper records calls and
CHARACTER counts (`in_chars`/`out_chars`) and never fabricates token
numbers — and emits NO events (characters are not tokens).

`totals()` remains the host's own view; `Memory` no longer reads it — the
consent-bearing surfaces (telemetry, audit, introspect) are fed only through
the registered listener per specs/0017 §4b/§4f.
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

#: specs/0017 §4a — the affirmative capability constant. Registration happens
#: iff this matches exactly; a coincidental `totals()` shape is never probed.
METERING_CAPABILITY = "veracium-metered-v1"

#: specs/0017 §4c — the ONE shared count-validity predicate, used identically
#: at the wrapper and at the Memory listener (external R3-6: a split rule was
#: a split brain). bool is excluded deliberately (it IS an int subtype).
_COUNT_LIMIT = 2 ** 53


def count_valid(x) -> bool:
    return type(x) is int and 0 <= x <= _COUNT_LIMIT


class Metered:
    """Wraps any `Complete`-shaped callable with per-role usage accounting
    and the specs/0017 listener protocol."""

    metering_capability = METERING_CAPABILITY

    def __init__(self, complete: Callable, *,
                 counter: Optional[Callable[[str], int]] = None):
        self._complete = complete
        self._counter = counter
        self._lock = threading.Lock()
        self._usage: dict[str, dict[str, int]] = {}
        self._listeners: dict[object, Callable] = {}

    # -- the specs/0017 §4a listener control plane ---------------------------
    def add_usage_listener(self, fn: Callable) -> object:
        """Register a usage listener; returns an opaque handle (never None)."""
        handle = object()
        with self._lock:
            self._listeners[handle] = fn
        return handle

    def remove_usage_listener(self, handle) -> None:
        """Idempotent removal: an unknown or already-removed handle is a no-op."""
        with self._lock:
            self._listeners.pop(handle, None)

    # -- the call path -------------------------------------------------------
    def __call__(self, prompt: str, *, system: Optional[str] = None,
                 role: str = "compile", json_schema: Optional[dict] = None) -> str:
        out = self._complete(prompt, system=system, role=role,
                             json_schema=json_schema)
        text_in = (system or "") + prompt

        # §4c: compute + validate BOTH counts into locals OUTSIDE the lock.
        # Any failure discards the whole pair — no token-state mutation, no
        # emission; the provider output is returned regardless.
        in_tok = out_tok = None
        if self._counter is not None:
            try:
                a = self._counter(text_in)
                b = self._counter(out or "")
                if count_valid(a) and count_valid(b):
                    in_tok, out_tok = a, b
            except Exception:
                pass

        listeners = ()
        with self._lock:
            u = self._usage.setdefault(role, {"calls": 0})
            u["calls"] += 1
            if self._counter is not None:
                if in_tok is not None:
                    u["in_tok"] = u.get("in_tok", 0) + in_tok
                    u["out_tok"] = u.get("out_tok", 0) + out_tok
            else:
                u["in_chars"] = u.get("in_chars", 0) + len(text_in)
                u["out_chars"] = u.get("out_chars", 0) + len(out or "")
            if in_tok is not None and self._listeners:
                listeners = tuple(self._listeners.values())   # snapshot

        # §4a: emit OUTSIDE the lock, synchronously, in the caller's context,
        # with per-listener exception isolation. One event per wrapper call.
        for fn in listeners:
            try:
                fn({"role": role, "in_tok": in_tok, "out_tok": out_tok})
            except Exception:
                pass

        return out

    def totals(self, *, reset: bool = False) -> dict[str, dict[str, int]]:
        with self._lock:
            snap = {r: dict(u) for r, u in self._usage.items()}
            if reset:
                self._usage.clear()
        return snap
