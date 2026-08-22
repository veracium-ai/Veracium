"""specs/0017 — the attribution context, producer registry, and arming proxy.

The TWO module-global `contextvars.ContextVar`s (§4b, external R7-1): the
ROUTING frame — a fully-immutable `(owner, op_token)` tuple carrying NO
user-bearing state (external R4-3: `copy_context()` copies frames, and a
copied `user_id` would survive `forget()`; everything user-bearing lives in
the Memory-owned registry, keyed by the opaque token) — and `_active_call`,
the opaque per-provider-call id (external R6-1: consumption is call-EXACT by
comparison, never call-current).

Shared by every `Memory` in the process (external R3-1 — reviewer-executed:
per-instance variables re-broke the shared-wrapper double-attribution; one
shared routing variable lets each listener's owner check accept the event in
exactly the correct Memory).
"""

from __future__ import annotations

from contextvars import ContextVar

#: the routing frame: None, or the immutable (owner: Memory, op_token: object)
routing_frame: ContextVar = ContextVar("veracium_usage_frame", default=None)

#: the active provider-call id: None, or an opaque per-call object (§4b)
active_call: ContextVar = ContextVar("veracium_active_call", default=None)


# specs/0017 §4e — the declarative producer registry: the four attributed
# (role, event) pairs with their call sites, plus the named exclusion. The
# I2b test asserts this against an AST scan of every in-tree `Complete`
# invocation; the PAIR is the unit of validity (external R3-3: role-set
# membership let role="gate" pass during an ingest frame).
PRODUCER_REGISTRY = (
    ("distill", "ingest", "src/veracium/ingest.py"),
    # specs/0025 §4b(1): the ONE re-extraction retry per event — a second
    # producer inside the same ingest frame, its own role so usage
    # attribution can split extraction cost from retry cost (Q3's budget
    # question is answered by exactly this attribution).
    ("distill-retry", "ingest", "src/veracium/ingest.py"),
    ("gate", "answer", "src/veracium/gate.py"),
    ("compile", "recall", "src/veracium/compile.py"),
    ("compile", "maintain", "src/veracium/lifecycle.py"),
)
ATTRIBUTED_PAIRS = frozenset((r, e) for r, e, _ in PRODUCER_REGISTRY)

#: the §4b context-entering operation set — mechanically compared to the
#: registry's events by I2b. `self_check` deliberately absent (external
#: R4-6: it has no user_id; its events arrive context-free).
CONTEXT_ENTERING_OPERATIONS = frozenset(e for _, e, _ in PRODUCER_REGISTRY)

#: the telemetry field names each attributed role populates — LITERAL
#: strings (the whitelisted⇒populated gate greps sources for them):
#: "distill_in_tok", "distill_out_tok" (ingest); "gate_in_tok",
#: "gate_out_tok" (answer); "compile_in_tok", "compile_out_tok" (recall AND
#: maintain — internal F1: the consolidation compile is a producer too).
ROLE_FIELDS = {
    "distill": ("distill_in_tok", "distill_out_tok"),
    "distill-retry": ("distill_retry_in_tok", "distill_retry_out_tok"),
    "gate": ("gate_in_tok", "gate_out_tok"),
    "compile": ("compile_in_tok", "compile_out_tok"),
}


class ArmingComplete:
    """The per-operation provider proxy: §4d transitions 2 (arm) and 4
    (clear) around every provider invocation. The emit happens inside
    `Metered.__call__` at return, in this calling context — so the armed
    window and `active_call` are live exactly when the listener's step 6
    compares call ids."""

    def __init__(self, mem, op_token, inner):
        self._mem = mem
        self._op_token = op_token
        self._inner = inner

    def __call__(self, prompt, *, system=None, role="compile",
                 json_schema=None):
        mem, tok = self._mem, self._op_token
        call_id = object()                       # opaque, per-call
        with mem._usage_lock:                    # transition 2: arm
            entry = mem._usage_registry.get(tok)
            if entry is not None and not entry["cancelled"]:
                entry["armed_call"] = (call_id, False)
        ctx_token = active_call.set(call_id)
        try:
            return self._inner(prompt, system=system, role=role,
                               json_schema=json_schema)
        finally:                                 # transition 4: clear
            active_call.reset(ctx_token)
            with mem._usage_lock:
                entry = mem._usage_registry.get(tok)
                if entry is not None:
                    entry["armed_call"] = None
