"""specs/0017 — token-usage telemetry over the Metered wrapper (I1–I12).

The frozen acceptance surface: affirmative capability opt-in, the six-step
listener with step 6 as the only authority, the five-field registry under
one instance lock with the eight atomic transitions, call-exact
compare-consume, the four-column carrier matrix, and successful-operation
scoping. Review-round reproductions are regression cells here (R3-1 shared
wrapper, R6-1/R7-2 stale-context, R8-1 close cross-product, R9-1 barrier
seams)."""
import ast
import contextvars
import json
import pathlib
import threading

import pytest

from veracium import Memory, MemoryConfig
from veracium import telemetry as T
from veracium.audit import AuditLog
from veracium.llm.metered import METERING_CAPABILITY, Metered, count_valid
from veracium.usage import (ATTRIBUTED_PAIRS, CONTEXT_ENTERING_OPERATIONS,
                            PRODUCER_REGISTRY, ROLE_FIELDS, active_call,
                            routing_frame)

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "veracium"
U = "alice"


class _Fake:
    """Deterministic scripted extraction — same shape as the other suites."""
    SCRIPT = {"triples": [{"subject": "user", "relation": "works_as",
                           "object": "chef"}],
              "episode": "User is a chef."}

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            return json.dumps(self.SCRIPT)
        if role == "gate":
            return "You are a chef."
        return "## wiki\n- works as chef"


def _counter(text):
    return len(text) // 4 + 1


def _mem(tmp_path, llm, name="t.db", **kw):
    return Memory(llm=llm,
                  config=MemoryConfig(db_path=str(tmp_path / name),
                                      wiki_recompile_after_writes=0), **kw)


def _metered_mem(tmp_path, name="t.db", counter=_counter, **kw):
    m = Metered(_Fake(), counter=counter)
    return _mem(tmp_path, m, name, **kw), m


# -- I11: opt-in is affirmative -------------------------------------------------------
def test_coincidental_totals_shape_is_never_invoked(tmp_path):
    calls = []

    class Coincidental:
        def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
            return _Fake()(prompt, system=system, role=role, json_schema=json_schema)

        def totals(self, *, reset=False):
            calls.append("totals")
            return {}

        def add_usage_listener(self, fn):
            calls.append("add")
            return object()

    mem = _mem(tmp_path, Coincidental())
    assert mem._metered_handle is None          # no capability constant → no registration
    mem.remember(U, "USER: I'm a chef.", date="2026-06-01")
    assert calls == []                          # never probed, never invoked
    assert "llm_usage" not in mem.introspect(U)
    mem.close()


def test_capability_must_match_exactly(tmp_path):
    class Wrong(Metered):
        metering_capability = "veracium-metered-v2-DIFFERENT"

    mem = _mem(tmp_path, Wrong(_Fake(), counter=_counter))
    assert mem._metered_handle is None
    mem.close()


# -- I12: the registration/removal/close matrix is TOTAL ------------------------------
def test_registration_control_plane_matrix(tmp_path):
    # capability WITHOUT add_usage_listener → treated unmetered
    class NoAdd:
        metering_capability = METERING_CAPABILITY

        def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
            return _Fake()(prompt, system=system, role=role, json_schema=json_schema)

    m1 = _mem(tmp_path, NoAdd(), "m1.db")
    assert m1._metered_handle is None and "missing" in m1._metering_note
    m1.close()

    # add_usage_listener RAISES → registration failed, Memory unregistered
    class AddRaises(NoAdd):
        def add_usage_listener(self, fn):
            raise RuntimeError("no")

    m2 = _mem(tmp_path, AddRaises(), "m2.db")
    assert m2._metered_handle is None and "raised" in m2._metering_note
    m2.close()

    # add returns None → the ONLY invalid handle value → unregistered
    class AddNone(NoAdd):
        def add_usage_listener(self, fn):
            return None

    m3 = _mem(tmp_path, AddNone(), "m3.db")
    assert m3._metered_handle is None and "None" in m3._metering_note
    m3.close()

    # ANY non-None return is a VALID handle — 0 included (R6-3)
    class AddZero(NoAdd):
        def add_usage_listener(self, fn):
            self.fn = fn
            return 0

        def remove_usage_listener(self, handle):
            assert handle == 0
            self.removed = True

    z = AddZero()
    m4 = _mem(tmp_path, z, "m4.db")
    assert m4._metered_handle == 0
    m4.close()
    assert getattr(z, "removed", False)

    # unknown + duplicate handle removal on the real wrapper: isolated no-ops
    w = Metered(_Fake(), counter=_counter)
    h = w.add_usage_listener(lambda ev: None)
    w.remove_usage_listener("never-issued")
    w.remove_usage_listener(h)
    w.remove_usage_listener(h)                  # duplicate → idempotent

    # remove ABSENT/RAISING during close → the store STILL closes, and the
    # listener is proven INERT first (the R8-1 cross-product with an armed
    # in-flight operation is in test_close_cross_product below)
    class RemoveRaises(Metered):
        def remove_usage_listener(self, handle):
            raise RuntimeError("broken removal")

    rw = RemoveRaises(_Fake(), counter=_counter)
    m5 = _mem(tmp_path, rw, "m5.db")
    assert m5._metered_handle is not None
    m5.close()                                  # no raise; store closed
    with pytest.raises(Exception):
        m5.store.edges(U)                       # proven closed
    m5.close()                                  # duplicate close: harmless


# -- I3: atomic accounting; the deadlock cell ----------------------------------------
def test_counter_failure_is_atomic_and_never_breaks_the_operation(tmp_path):
    for failing_position in (1, 2):
        state = {"n": 0}

        def counter(text, _pos=failing_position):
            state["n"] += 1
            if state["n"] == _pos:
                raise RuntimeError("counter broke")
            return 7

        mem, w = _metered_mem(tmp_path, f"cf{failing_position}.db", counter=counter)
        r = mem.remember(U, "USER: I'm a chef.", date="2026-06-01")
        assert r["facts"] >= 0                   # the operation is unbroken
        tot = w.totals()
        assert "in_tok" not in tot.get("distill", {}), \
            "a failing counter must discard the WHOLE pair"
        assert tot["distill"]["calls"] == 1      # calls ride the always-valid block
        assert mem.introspect(U).get("llm_usage", {}).get("roles", {}) == {}, \
            "no partial token state may survive"
        mem.close()


def test_listener_reentry_does_not_deadlock(tmp_path):
    w = Metered(_Fake(), counter=_counter)
    seen = []

    def reentrant(ev):
        w.totals()                               # re-enter the wrapper lock
        h2 = w.add_usage_listener(lambda e: None)
        w.remove_usage_listener(h2)
        seen.append(ev)

    w.add_usage_listener(reentrant)

    def raising(ev):
        raise RuntimeError("bad listener")

    w.add_usage_listener(raising)
    out = w("prompt", role="distill")            # completes, no deadlock
    assert out and len(seen) == 1
    assert seen[0] == {"role": "distill",
                       "in_tok": _counter("prompt"),
                       "out_tok": _counter(out)}


# -- I2: no counter → no token telemetry anywhere ------------------------------------
def test_no_counter_sends_no_token_fields(tmp_path):
    coll = T.Collector(consent_epoch=1, schema_version=3)
    log = AuditLog(str(tmp_path / "audit.jsonl"))
    m = Metered(_Fake())                         # NO counter
    mem = Memory(llm=m, telemetry=coll, audit=log,
                 config=MemoryConfig(db_path=str(tmp_path / "nc.db"),
                                     wiki_recompile_after_writes=0))
    mem.remember(U, "USER: I'm a chef.", date="2026-06-01")
    mem.answer(U, "job?")
    snap = coll.snapshot()
    for ev, payload in snap.get("events", {}).items():
        sums = payload.get("sums", {})
        assert not any("tok" in f for f in sums), (ev, sums)
    for entry in log.entries():
        assert not any("tok" in k for k in entry), entry
    assert mem.introspect(U).get("llm_usage", {}).get("roles", {}) in ({},), \
        "no token events exist without a counter"
    assert "in_chars" in m.totals()["distill"]   # chars stay host-side
    mem.close()


# -- I2b: the producer registry vs the AST, and explicit role= ------------------------
def _in_tree_complete_invocations():
    """Every `llm(...)`-shaped invocation in src/veracium (outside llm/)."""
    sites = []
    for p in sorted(SRC.rglob("*.py")):
        if "llm" in p.parts[-2:] or p.name == "usage.py":
            continue
        tree = ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id in ("llm", "op_llm"):
                kw = {k.arg: k for k in node.keywords}
                sites.append((str(p.relative_to(SRC.parents[1])), node.lineno, kw))
    return sites


def test_token_payload_covers_every_role_event_pair():
    sites = _in_tree_complete_invocations()
    assert sites, "the scan must find the producer call sites"
    roles_seen = set()
    for path, lineno, kw in sites:
        assert "role" in kw, (f"{path}:{lineno} invokes the provider without an "
                              f"explicit role= — the I2b scan rejects omissions")
        role_node = kw["role"].value
        assert isinstance(role_node, ast.Constant) and isinstance(role_node.value, str), \
            f"{path}:{lineno} role= must be a string literal"
        roles_seen.add(role_node.value)
    registry_roles = {r for r, _, _ in PRODUCER_REGISTRY}
    assert roles_seen == registry_roles, (roles_seen, registry_roles)
    # the registry's events and the context-entering set are the same set
    assert CONTEXT_ENTERING_OPERATIONS == {e for _, e, _ in PRODUCER_REGISTRY}
    # every registry callsite file really invokes with that role
    for role, _event, callsite in PRODUCER_REGISTRY:
        body = (SRC.parents[1] / callsite).read_text()
        assert f'role="{role}"' in body, (role, callsite)
    # every attributed pair maps to whitelisted fields at min version 3
    for role, event in ATTRIBUTED_PAIRS:
        in_f, out_f = ROLE_FIELDS[role]
        assert in_f in T.EVENT_FIELDS[event] and out_f in T.EVENT_FIELDS[event]
        assert T.FIELD_MIN_VERSION[(event, in_f)] == 3
        assert T.FIELD_MIN_VERSION[(event, out_f)] == 3


def test_no_unpropagated_thread_fanout_in_operation_paths():
    """The I2b thread-fanout gate: no thread/executor dispatch inside a
    context-entering operation path unless it propagates context."""
    for name in ("ingest.py", "compile.py", "gate.py", "lifecycle.py"):
        body = (SRC / name).read_text()
        for needle in ("Thread(", "ThreadPoolExecutor", ".submit("):
            if needle in body:
                assert "copy_context" in body, (
                    f"{name} dispatches to a thread without copy_context() — "
                    f"attribution context would be lost (I2b)")


# -- I1: metering is decision-invisible ----------------------------------------------
def test_metering_is_decision_invisible(tmp_path):
    def run(llm, db):
        mem = _mem(tmp_path, llm, db)
        mem.remember(U, "USER: I'm a chef.", date="2026-06-01")
        ans = mem.answer(U, "what is my job?")
        edges = sorted(e.model_dump_json() for e in
                       mem.store.edges(U, active_only=False, include_quarantined=True))
        eps = sorted(ep.model_dump_json() for ep in mem.store.episodes(U))
        mem.close()
        return ans, edges, eps

    plain = run(_Fake(), "plain.db")
    metered = run(Metered(_Fake(), counter=_counter), "metered.db")
    # identical answers; stores identical modulo minted ids/timestamps —
    # compare the content-bearing projection
    assert plain[0] == metered[0]

    def strip(rows):
        out = []
        for r in rows:
            d = json.loads(r)
            for k in ("id", "user_id"):
                d.pop(k, None)
            d.get("provenance", {}).pop("evidence_ref", None)
            d.pop("valid_from", None)
            prov = d.get("provenance", {})
            prov.pop("observed_at", None)
            d.pop("edge_id", None)
            d.pop("when", None)
            out.append(json.dumps(d, sort_keys=True))
        return sorted(out)

    assert strip(plain[1]) == strip(metered[1])
    assert len(plain[2]) == len(metered[2])


# -- I4: the twelve-cell carrier matrix ----------------------------------------------
def test_carrier_consent_matrix(tmp_path):
    def cells(llm, consent_version, db):
        coll = T.Collector(consent_epoch=1, schema_version=consent_version)
        log = AuditLog(str(tmp_path / f"{db}.audit.jsonl"))
        mem = Memory(llm=llm, telemetry=coll, audit=log,
                     config=MemoryConfig(db_path=str(tmp_path / db),
                                         wiki_recompile_after_writes=0))
        mem.remember(U, "USER: I'm a chef.", date="2026-06-01")
        tel_fields = set()
        for ev, payload in coll.snapshot().get("events", {}).items():
            tel_fields |= {f for f in payload.get("sums", {}) if "tok" in f}
        audit_fields = {k for e in log.entries() for k in e if "tok" in k}
        intro = mem.introspect(U).get("llm_usage")
        mem.close()
        return tel_fields, audit_fields, intro

    # column 1: unmetered
    tel, aud, intro = cells(_Fake(), 3, "c1.db")
    assert tel == set() and aud == set() and intro is None
    # column 2: metered, NO counter
    tel, aud, intro = cells(Metered(_Fake()), 3, "c2.db")
    assert tel == set() and aud == set()
    assert intro is not None and intro["roles"] == {}      # metered but no events
    # column 3: metered + counter, consent < 3 → telemetry stripped; local carriers live
    tel, aud, intro = cells(Metered(_Fake(), counter=_counter), 2, "c3.db")
    assert tel == set()
    assert aud == {"distill_in_tok", "distill_out_tok"}
    assert intro["roles"]["distill"]["calls"] == 1
    # column 4: consent v3 → the fields flow
    tel, aud, intro = cells(Metered(_Fake(), counter=_counter), 3, "c4.db")
    assert tel == {"distill_in_tok", "distill_out_tok"}
    assert aud == {"distill_in_tok", "distill_out_tok"}
    assert intro["roles"]["distill"]["in_tok"] > 0
    assert intro["scope"] == "instance-lifetime"


# -- I7: no MCP surface carries usage ------------------------------------------------
def test_mcp_results_carry_no_usage_fields():
    body = (SRC / "mcp_server.py").read_text()
    assert "_tok" not in body
    assert "llm_usage" not in body
    assert "introspect" not in body.lower() or "@server.tool" not in body, \
        "introspect must not be an MCP tool"


# -- the listener validates fail-closed (§4a/§2c) ------------------------------------
def test_listener_validates_fail_closed(tmp_path):
    mem, w = _metered_mem(tmp_path, "fc.db")
    mem.remember(U, "USER: I'm a chef.", date="2026-06-01")   # a real, clean op
    baseline = mem.introspect(U)["llm_usage"]["roles"]["distill"]["in_tok"]

    # inject garbage DURING a live armed operation: craft the op context
    listener = mem._usage_listener
    op_token = object()
    with mem._usage_lock:
        mem._usage_registry[op_token] = {"user_id": U, "event": "ingest",
                                         "buffer": {}, "cancelled": False,
                                         "armed_call": None}
    frame_tok = routing_frame.set((mem, op_token))
    call_id = object()
    with mem._usage_lock:
        mem._usage_registry[op_token]["armed_call"] = (call_id, False)
    call_tok = active_call.set(call_id)
    try:
        for bad in (None, "x", [], {"role": "distill"},                 # shape
                    {"role": "distill", "in_tok": 1, "out_tok": 1, "extra": 1},
                    {"role": "gate", "in_tok": 1, "out_tok": 1},        # wrong pair for ingest
                    {"role": "distill", "in_tok": True, "out_tok": 1},  # bool
                    {"role": "distill", "in_tok": -1, "out_tok": 1},
                    {"role": "distill", "in_tok": 2**53 + 1, "out_tok": 1},
                    {"role": "distill", "in_tok": 1.0, "out_tok": 1},
                    {"role": 7, "in_tok": 1, "out_tok": 1}):
            listener(bad)                       # never raises, never attributes
        assert mem._usage_registry[op_token]["buffer"] == {}
        # a VALID event in the same armed call is accepted exactly once —
        # the poison ruling: prior garbage never erased valid attribution
        listener({"role": "distill", "in_tok": 5, "out_tok": 6})
        listener({"role": "distill", "in_tok": 5, "out_tok": 6})   # consumed → drop
        assert mem._usage_registry[op_token]["buffer"]["distill"] == [5, 6, 1]
    finally:
        active_call.reset(call_tok)
        routing_frame.reset(frame_tok)
        with mem._usage_lock:
            mem._usage_registry.pop(op_token, None)
    assert mem.introspect(U)["llm_usage"]["roles"]["distill"]["in_tok"] == baseline
    mem.close()


# -- I9: attribution is exact within the stated boundary -----------------------------
def test_attribution_is_exact_under_concurrency(tmp_path):
    """Two users' operations with OVERLAPPING armed windows: both providers
    are in flight simultaneously (frames + armed calls live together — the
    cross-attribution hazard), while the store writes stay serialized (the
    store's documented contract is single-writer; attribution, not store
    concurrency, is what I9 pins)."""
    barrier = threading.Barrier(2)
    a_done = threading.Event()

    class OverlappingFake(_Fake):
        def __call__(self, prompt, *, system=None, role="compile",
                     json_schema=None):
            if role == "distill":
                who = threading.current_thread().name
                barrier.wait()               # both armed windows now overlap
                if who == "thread-b":        # B stays in-provider until A's
                    a_done.wait(timeout=30)  # whole operation (incl. writes,
                                             # emission, merge) completes
            return super().__call__(prompt, system=system, role=role,
                                    json_schema=json_schema)

    w = Metered(OverlappingFake(), counter=_counter)
    mem = _mem(tmp_path, w, "conc.db")
    errors = []

    def work(uid, name):
        try:
            ctx = contextvars.copy_context()
            ctx.run(mem.remember, uid, "USER: I'm a chef.", date="2026-06-01")
            if name == "thread-a":
                a_done.set()
        except Exception as e:                   # pragma: no cover
            errors.append(e)
            a_done.set()

    ta = threading.Thread(target=work, args=("ua", "thread-a"), name="thread-a")
    tb = threading.Thread(target=work, args=("ub", "thread-b"), name="thread-b")
    ta.start(); tb.start(); ta.join(); tb.join()
    assert not errors
    for uid in ("ua", "ub"):
        roles = mem.introspect(uid)["llm_usage"]["roles"]
        assert roles["distill"]["calls"] == 1, \
            f"{uid}: exactly one distill call must attribute (no cross-user smear)"
        assert roles["distill"]["in_tok"] > 0
    mem.close()


def test_nested_answer_recall_attributes_to_inner_context(tmp_path):
    mem, w = _metered_mem(tmp_path, "nested.db")
    mem.config.wiki_recompile_after_writes = 1   # force a compile during recall
    mem.remember(U, "USER: I'm a chef.", date="2026-06-01")
    mem.answer(U, "what is my job?")
    roles = mem.introspect(U)["llm_usage"]["roles"]
    assert roles["gate"]["calls"] == 1           # answer's own producer
    assert roles.get("compile", {}).get("calls", 0) >= 1   # recall's, not answer's
    mem.close()


def test_shared_wrapper_two_memories_never_cross(tmp_path):
    w = Metered(_Fake(), counter=_counter)
    m1 = _mem(tmp_path, w, "s1.db")
    m2 = _mem(tmp_path, w, "s2.db")
    m1.remember("alice", "USER: I'm a chef.", date="2026-06-01")
    m2.remember("bob", "USER: I'm a baker.", date="2026-06-01")
    assert m1.introspect("alice")["llm_usage"]["roles"]["distill"]["calls"] == 1
    assert m1.introspect("bob").get("llm_usage", {"roles": {}})["roles"] == {}
    assert m2.introspect("bob")["llm_usage"]["roles"]["distill"]["calls"] == 1
    m1.close(); m2.close()


def test_replay_and_stale_context_cells(tmp_path):
    mem, w = _metered_mem(tmp_path, "replay.db")

    # replay OUTSIDE any armed call → wrapper totals only, nothing attributes
    mem._usage_listener({"role": "distill", "in_tok": 999, "out_tok": 999})
    assert mem.introspect(U).get("llm_usage", {"roles": {}})["roles"] == {}

    # the R7-2 prescription: owner and op_token CONSTANT throughout
    op_token = object()
    with mem._usage_lock:
        mem._usage_registry[op_token] = {"user_id": U, "event": "ingest",
                                         "buffer": {}, "cancelled": False,
                                         "armed_call": None}
    frame_tok = routing_frame.set((mem, op_token))
    try:
        # arm call A and capture its context
        call_a = object()
        with mem._usage_lock:
            mem._usage_registry[op_token]["armed_call"] = (call_a, False)
        tok_a = active_call.set(call_a)
        ctx_a = contextvars.copy_context()       # A's copied context
        active_call.reset(tok_a)
        with mem._usage_lock:                    # clear A
            mem._usage_registry[op_token]["armed_call"] = None
        # arm call B
        call_b = object()
        with mem._usage_lock:
            mem._usage_registry[op_token]["armed_call"] = (call_b, False)
        # emit from A's STALE copied context → drops AT THE CALL-ID COMPARISON,
        # and B's expectation is NOT consumed
        ctx_a.run(mem._usage_listener,
                  {"role": "distill", "in_tok": 7, "out_tok": 7})
        entry = mem._usage_registry[op_token]
        assert entry["buffer"] == {}
        assert entry["armed_call"] == (call_b, False), \
            "the stale-context drop must not consume B's expectation"
        # B's genuine event → accepted exactly once
        tok_b = active_call.set(call_b)
        try:
            mem._usage_listener({"role": "distill", "in_tok": 3, "out_tok": 4})
            mem._usage_listener({"role": "distill", "in_tok": 3, "out_tok": 4})
        finally:
            active_call.reset(tok_b)
        assert entry["buffer"]["distill"] == [3, 4, 1]
    finally:
        routing_frame.reset(frame_tok)
        with mem._usage_lock:
            mem._usage_registry.pop(op_token, None)
    mem.close()


# -- I8: erasure and lifecycle over the actual state machine -------------------------
def test_usage_accumulator_lifecycle(tmp_path):
    mem, w = _metered_mem(tmp_path, "life.db")

    # success path: entry registered during, removed after; accumulator fed
    mem.remember(U, "USER: I'm a chef.", date="2026-06-01")
    assert mem._usage_registry == {}             # transition 7 ran
    assert mem._llm_usage[U]["distill"]["calls"] == 1

    # failure path: the raise discards — nothing merges, entry removed
    class Boom(Metered):
        pass

    def raising_complete(prompt, *, system=None, role="compile", json_schema=None):
        raise RuntimeError("provider down")

    bw = Metered(raising_complete, counter=_counter)
    bmem = _mem(tmp_path, bw, "boom.db")
    with pytest.raises(RuntimeError):
        bmem.remember(U, "USER: hi.", date="2026-06-01")
    assert bmem._usage_registry == {}
    assert bmem._llm_usage == {}                 # a failed operation records NOTHING
    bmem.close()

    # forget: transition 5 — accumulator gone; introspect shows no usage record
    mem.forget(U)
    assert U not in mem._llm_usage
    assert mem.introspect(U)["llm_usage"]["roles"] == {}

    # copied contexts hold only opaque tokens — no user string anywhere
    with mem._usage_operation(U, "ingest") as (op_llm, fin):
        ctx = contextvars.copy_context()
        frame = ctx[routing_frame]
        assert frame[0] is mem and isinstance(frame[1], object)
        assert U not in repr(frame[1])
    # after exit + forget, the copied context resolves to nothing
    assert ctx[routing_frame][1] not in mem._usage_registry

    # two instances independent; restart empty
    m2, _ = _metered_mem(tmp_path, "other.db")
    assert m2._llm_usage == {}
    m2.close()

    # self_check pushes no frame and attributes nothing
    mem.self_check(record=False)
    assert mem._llm_usage.get(U, {}) == {}       # still empty post-forget
    assert routing_frame.get() is None
    mem.close()


def test_merge_vs_forget_barrier_race(tmp_path):
    mem, w = _metered_mem(tmp_path, "race.db")
    # forget acquiring the lock BEFORE the merge wins: cancelled → discard
    with mem._usage_operation(U, "ingest") as (op_llm, fin):
        op_llm("p", role="distill")              # buffer something real
        with mem._usage_lock:
            for e in mem._usage_registry.values():
                if e["user_id"] == U:
                    e["cancelled"] = True        # forget's cancel, interleaved
        assert fin() == {}                       # the merge observes cancelled
    assert mem._llm_usage.get(U) is None
    # merge first, then forget deletes what it merged
    with mem._usage_operation(U, "ingest") as (op_llm, fin):
        op_llm("p", role="distill")
        fields = fin()
        assert fields["distill_in_tok"] > 0
    mem.forget(U)
    assert U not in mem._llm_usage
    mem.close()


def test_close_cross_product(tmp_path):
    """R8-1 × R9-1: successful registration × raising removal × an armed
    in-flight operation × a post-close emission — the store closes AND the
    retained callback cannot consume, buffer, merge, audit, or emit."""
    class RemoveRaises(Metered):
        def remove_usage_listener(self, handle):
            raise RuntimeError("removal broken")

    w = RemoveRaises(_Fake(), counter=_counter)
    mem = _mem(tmp_path, w, "cx.db")
    assert mem._metered_handle is not None

    # an armed in-flight operation at close time
    op_token = object()
    with mem._usage_lock:
        mem._usage_registry[op_token] = {"user_id": U, "event": "ingest",
                                         "buffer": {}, "cancelled": False,
                                         "armed_call": (object(), False)}
    frame_tok = routing_frame.set((mem, op_token))
    call_id = mem._usage_registry[op_token]["armed_call"][0]
    call_tok = active_call.set(call_id)
    try:
        mem.close()                              # raising removal; still closes
        with pytest.raises(Exception):
            mem.store.edges(U)
        # the retained callback is INVOKED post-close (a dead call) — R9-1's
        # first barrier seam: it dies at step 6's lock-guarded re-check
        mem._usage_listener({"role": "distill", "in_tok": 5, "out_tok": 5})
        assert mem._usage_registry[op_token]["buffer"] == {}
        assert mem._llm_usage == {}
    finally:
        active_call.reset(call_tok)
        routing_frame.reset(frame_tok)


def test_event_buffered_before_close_dies_at_the_merge(tmp_path):
    """R9-1's second barrier seam: buffered before close, merged after —
    the merge's cancellation check discards."""
    mem, w = _metered_mem(tmp_path, "seam2.db")
    with mem._usage_operation(U, "ingest") as (op_llm, fin):
        op_llm("p", role="distill")              # buffered, real event
        with mem._usage_lock:                    # transition 8, mid-operation
            mem._listener_active = False
            for e in mem._usage_registry.values():
                e["cancelled"] = True
        assert fin() == {}                       # cancelled → nothing merges
    assert mem._llm_usage == {}
    mem.close()


# -- successful-operation scoping at the record boundary -----------------------------
def test_token_fields_reach_the_terminal_record_once(tmp_path):
    coll = T.Collector(consent_epoch=1, schema_version=3)
    log = AuditLog(str(tmp_path / "rec.audit.jsonl"))
    mem = Memory(llm=Metered(_Fake(), counter=_counter), telemetry=coll, audit=log,
                 config=MemoryConfig(db_path=str(tmp_path / "rec.db"),
                                     wiki_recompile_after_writes=0))
    mem.remember(U, "USER: I'm a chef.", date="2026-06-01")
    ingest_entries = log.entries(op="ingest")
    assert len(ingest_entries) == 1              # ONE audit line per operation
    assert ingest_entries[0]["distill_in_tok"] > 0
    assert coll.snapshot()["events"]["ingest"]["n"] == 1
    mem.close()
