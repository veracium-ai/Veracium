"""specs/0031 §4f, implementation round 3: the trust tools' round-3 cells, through EVERY surface a tool is served on.

Surfaces: `mcp` (the FastMCP server, no principal), `core` (the framework-free adapter core, `veracium.adapters._surface`),
and the two framework rows, `langchain` and `pydantic_ai`, driven through 0053's drivers (a real LangChain tool call;
a real Pydantic AI agent with the offline FunctionModel). A framework row skips by name without its extra, and FAILS
instead in the CI job whose VERACIUM_ADAPTER_ROWS names it (0053's rule), so a skip cannot read as a pass there.

- TT-R3-01 (INV-TT3): the proactive receipt admits exactly the contested members whose value the line SHOWS; members
  named only by "or K more" are not units. `Recall.edges` (host-only, §4b's "never does" list) keeps them all.
- TT-R3-02 (INV-TT3, round 2's answer 5): a unit's `subject` is the subject as its admitted line rendered it, clamped
  where the line clamped it; a line that names no subject carries none. Never the record's raw field.
- TT-R3-04 C (INV-TT16, INV-TT17, INV-TT19): the frozen principal matrices through the core and both framework adapters
  (each class, principals in a group, another group and no group, cross-group visibility off and on; both whole-user
  tools under a principal; the absorption-descendant comparison), and round 2's four source witnesses on the actual
  tools, MCP included where no principal applies. Refusals compare whole against literal payloads; no-write is a
  digest of every row of every table.
- TT-R3-03 (INV-TT11, §4a step 8): a refusal is serialized only while no write has committed in the call; after a
  writing commit a refusal-class failure raises through the surface's error channel. The phase is recorded at the
  commit, on the call's own connection, per call.

Every expected value below is an independent fixture (planted ids and strings), never read back from the product's
receipt construction. The proactive clock is held, so the dated fixtures stay inside the briefing window.
"""
import asyncio
import importlib
import json
import os
import pathlib
import sys
import threading
from datetime import datetime, timezone

import pytest

pytest.importorskip("mcp", reason="specs/0031 §4f: the MCP surface needs the mcp extra")

from veracium import Memory, MemoryConfig, graph  # noqa: E402
from veracium import mcp_server as M  # noqa: E402
from veracium.adapters import _surface  # noqa: E402
from veracium.budgets import ELISION_MARKER  # noqa: E402
from veracium.schema import Disclosure, Edge, EvidenceAuthor, Provenance, Volatility  # noqa: E402
from veracium.scope import Identity  # noqa: E402
from veracium.trust_tools import TrustInternalError  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "specs" / "evidence" / "0053"))
from adapter_conformance import drivers as D  # noqa: E402
from adapter_conformance import rows as R  # noqa: E402

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
U = "u"
SURFACES = ("mcp", "core", "langchain", "pydantic_ai")
PRINCIPAL_SURFACES = ("core", "langchain", "pydantic_ai")      # MCP stdio binds no principal (§4f.6)


# ------------------------------------------------------------------ the surfaces
def _row(row):
    """0053's rule for a framework row: skip by name without its extra; FAIL when VERACIUM_ADAPTER_ROWS names it; the
    installed framework must be the version the row pins."""
    import importlib.metadata
    required = row in os.environ.get("VERACIUM_ADAPTER_ROWS", "").split(",")
    mod = {"langchain": "langchain_core", "pydantic_ai": "pydantic_ai"}[row]
    if required:
        importlib.import_module(mod)
    if row == "langchain":
        pytest.importorskip("langchain_core", reason="specs/0053: the langchain row needs the langchain extra")
    else:
        pytest.importorskip("pydantic_ai", reason="specs/0053: the pydantic_ai row needs the pydantic_ai extra")
    name, pinned = R.ROWS[row]["framework"]
    assert importlib.metadata.version(name) == pinned, f"the {row} row is pinned to {name} {pinned}"
    return importlib.import_module(f"veracium.adapters.{row}")


def surface(m, name, **binding):
    """`call(tool, args) -> (channel, value)`: ("ok", the tool's result dict) or ("error", the surface's error text)."""
    if name == "mcp":
        assert "principal" not in binding, "MCP stdio binds no principal"
        server = M.build_server(m, default_user=U, capability="direct", **binding)

        def call(tool, args):
            try:
                out = asyncio.run(server.call_tool(tool, args))
            except Exception as exc:                  # FastMCP's tool error, raised in-process
                return "error", str(exc)
            return "ok", json.loads(out[0].text)
        return call
    b = {"user_id": U, "capability": "direct", **binding}
    if name == "core":
        d = D.CoreDriver(_surface, m, b)
    else:
        d = {"langchain": D.LangChainDriver, "pydantic_ai": D.PydanticAIDriver}[name](_row(name), m, b)
    return lambda tool, args: d.decode(d.call(tool, args))


# ------------------------------------------------------------------ reading a result: shape asserted first
def _unit(out, eid):
    """The one unit with id `eid`; a missing or doubled unit is a failed assertion, never an unpacking error."""
    units = [u for u in (out.get("units") or []) if isinstance(u, dict) and u.get("id") == eid]
    assert len(units) == 1, (eid, out)
    return units[0]


def _field(got, key):
    """`key` of a surface's ok result, asserted present before it is read (a refusal in its place fails the
    assertion with the payload shown, never a KeyError)."""
    assert got[0] == "ok" and isinstance(got[1], dict) and key in got[1], (key, got)
    return got[1][key]


# ------------------------------------------------------------------ fixtures
HELD = datetime(2026, 11, 16, 8, 30, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def held_clock(monkeypatch):
    import veracium.proactive as proactive

    class Held(datetime):
        @classmethod
        def now(cls, tz=None):
            v = cls(2026, 11, 16, 8, 30, tzinfo=timezone.utc)
            return v if tz is None else v.astimezone(tz)
    monkeypatch.setattr(proactive, "datetime", Held)


def _mem(tmp_path, cap=96, **cfg):
    cfg.setdefault("wiki_recompile_after_writes", 0)
    return Memory(llm=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no model call")),
                  config=MemoryConfig(db_path=str(tmp_path / "v.db"), require_source_id=False, item_cap_tokens=cap,
                                      **cfg))


def _edge(eid, obj, subject="person:x", rel="works_as", author=EvidenceAuthor.USER, disc=Disclosure.MENTIONABLE,
          vol=Volatility.SLOW):
    t = datetime(2026, 11, 15, tzinfo=timezone.utc)
    return Edge(id=eid, user_id=U, subject=subject, relation=rel, object=obj, volatility=vol, valid_from=t,
                provenance=Provenance(author_of_evidence=author, evidence_ref="ev-" + eid, observed_at=t,
                                      disclosure=disc))


def _contend(m, subject, values, ids=None):
    ids = ids or [f"e-{i}" for i in range(len(values))]
    for i, obj in zip(ids, values):
        m.store.add_edge(_edge(i, obj, subject))
    graph.apply_supersession(m.store, _edge("e-ch", "challenge", subject, author=EvidenceAuthor.THIRD_PARTY,
                                            disc=Disclosure.QUARANTINED), m.config.relations)


# ====================================================================== TT-R3-01
@pytest.mark.parametrize("transport", SURFACES)
def test_withheld_contested_values_are_not_units(tmp_path, transport):
    """Three distinct long dated values: the line shows the nearest and "or 2 more"; only that member is a unit."""
    m = _mem(tmp_path)
    _contend(m, "person:x", ["alpha 2026-11-16 " + "A" * 400, "beta 2026-11-17 " + "B" * 400,
                             "gamma 2026-11-18 " + "C" * 400])
    r = m.recall(U)
    assert "or 2 more" in r.context and "beta" not in r.context and "gamma" not in r.context   # the trigger
    assert {"e-0", "e-1", "e-2"} <= {e.id for e in r.edges}     # Recall.edges keeps every member (host-only, §4b)
    ch, out = surface(m, transport)("find_facts", {})
    assert ch == "ok" and out["ok"] is True
    assert [u["id"] for u in out["units"] if u["partition"] == "contested"] == ["e-0"], out["units"]


@pytest.mark.parametrize("transport", SURFACES)
def test_a_restated_duplicate_of_the_shown_value_is_collapsed_before_composition(tmp_path, transport):
    """Two members carrying one value: the briefing collapses the restatement upstream (0012 I8), so the composer sees
    one member per value and the duplicate is in neither `Recall.edges` nor the receipt. Measured 2026-11-16: the
    shared-value branch of the admission rule (`m.object in shown`) is unreachable on the proactive path."""
    m = _mem(tmp_path)
    alpha = "alpha 2026-11-16 " + "A" * 400
    _contend(m, "person:x", [alpha, alpha, "beta 2026-11-17 " + "B" * 400, "gamma 2026-11-18 " + "C" * 400])
    r = m.recall(U)
    assert "or 2 more" in r.context and "beta" not in r.context
    assert "e-1" not in {e.id for e in r.edges}
    ch, out = surface(m, transport)("find_facts", {})
    assert ch == "ok"
    assert [u["id"] for u in out["units"] if u["partition"] == "contested"] == ["e-0"], out["units"]


@pytest.mark.parametrize("transport", SURFACES)
def test_a_value_whose_clamped_display_repeats_a_shown_one_is_not_a_unit(tmp_path, transport):
    """Two values that differ only past the clamp render as one slot; the second is counted in K, not shown."""
    m = _mem(tmp_path)
    stem = "alpha 2026-11-16 " + "A" * 600
    _contend(m, "person:x", [stem + "-ONE", stem + "-TWO"])
    r = m.recall(U)
    assert "or 1 more" in r.context and "-ONE" not in r.context and "-TWO" not in r.context
    ch, out = surface(m, transport)("find_facts", {})
    assert ch == "ok"
    assert [u["id"] for u in out["units"] if u["partition"] == "contested"] == ["e-0"], out["units"]


def test_the_first_item_recomposition_carries_its_own_shown_set(tmp_path):
    """The first item recomposed at the remaining budget (a smaller cap) shows fewer values; its units follow it."""
    m = _mem(tmp_path, cap=512)
    _contend(m, "person:x", ["alpha 2026-11-16", "beta 2026-11-17", "gamma 2026-11-18 " + "C" * 1600])
    whole = m.recall(U, render_receipt=True)
    assert "gamma" in whole.context and "more" not in whole.context            # at the item cap every value fits
    tight = m.recall(U, token_budget=256, render_receipt=True)                 # the proactive floor
    assert "gamma" not in tight.context and "more" in tight.context           # the trigger: recomposed, K > 0
    shown = [u["id"] for u in tight.render_receipt if u["partition"] == "contested"]
    assert shown and "e-2" not in shown, tight.render_receipt


def test_the_one_slot_fallback_admits_only_its_one_shown_value(tmp_path):
    """Research's stage-2 S09: when even one clamped value with "or K more" overflows the remaining budget, the line
    falls back to ONE slot, the nearest value alone; only that member is a unit. Mutant: the fallback's kept set
    left as every value (the member behind "or 1 more" admitted)."""
    m = _mem(tmp_path, cap=512)
    _contend(m, "person:x", ["alpha 2026-11-16 " + "A" * 1600, "beta 2026-11-17 " + "B" * 1600])
    tight = m.recall(U, token_budget=256, render_receipt=True)                 # the proactive floor
    assert "alpha" in tight.context and "beta" not in tight.context and "1 more" in tight.context   # the trigger
    shown = [u["id"] for u in tight.render_receipt if u["partition"] == "contested"]
    assert shown == ["e-0"], tight.render_receipt


# ====================================================================== TT-R3-02
LONG = "person:" + "X" * 500 + "SUBJECT_TAIL_SENTINEL"


def _subject_units(out):
    return [u for u in out["units"] if "subject" in u]


@pytest.mark.parametrize("transport", SURFACES)
@pytest.mark.parametrize("query", ["engineer", None])
def test_a_clamped_contested_subject_is_not_restored(tmp_path, transport, query):
    m = _mem(tmp_path)
    _contend(m, LONG, ["engineer alpha", "engineer beta"] if query else ["alpha 2026-11-16", "beta 2026-11-17"])
    assert "SUBJECT_TAIL_SENTINEL" not in m.recall(U, query).context
    ch, out = surface(m, transport)("find_facts", {"query": query})
    assert ch == "ok" and _subject_units(out)
    assert "SUBJECT_TAIL_SENTINEL" not in json.dumps(out)
    for u in _subject_units(out):
        assert u["subject"].endswith(ELISION_MARKER) and LONG.startswith(u["subject"][:-len(ELISION_MARKER)])


@pytest.mark.parametrize("transport", SURFACES)
def test_a_dated_commitment_subject_is_carried_as_clamped(tmp_path, transport):
    """A DATED COMMITMENTS line names a non-user subject clamped at item_cap//8; its unit carries that clamp."""
    m = _mem(tmp_path)
    m.store.add_edge(_edge("e-d", "2026-11-17", LONG, rel="due"))
    r = m.recall(U)
    assert "SUBJECT_TAIL_SENTINEL" not in r.context and "2026-11-17" in r.context
    ch, out = surface(m, transport)("find_facts", {})
    assert ch == "ok"
    u = _unit(out, "e-d")
    s = u.get("subject")
    assert isinstance(s, str) and s.endswith(ELISION_MARKER) and LONG.startswith(s[:-len(ELISION_MARKER)]), u
    assert s in u["text"] and "SUBJECT_TAIL_SENTINEL" not in json.dumps(out)


@pytest.mark.parametrize("transport", SURFACES)
def test_a_query_line_renders_its_subject_whole_and_carries_it_whole(tmp_path, transport):
    """The query path's ordinary line names the subject whole (its clamp shrinks the object and note only)."""
    m = _mem(tmp_path, cap=512)
    subject = "person:" + "Y" * 120
    m.store.add_edge(_edge("e-q", "engineer", subject))
    ch, out = surface(m, transport)("find_facts", {"query": "engineer"})
    assert ch == "ok"
    u = _unit(out, "e-q")
    assert u.get("subject") == subject and u["text"].startswith(subject + " "), u


@pytest.mark.parametrize("transport", SURFACES)
def test_a_proactive_current_line_names_its_subject_and_the_unit_carries_it(tmp_path, transport):
    """0012 v18.2 (research's stage-2 N3, pre-existing since 0.4.0): CURRENT CONTEXT rendered `relation: object
    (since …)` for a `person:x` fact, which read as the user's own; until v18.2 this cell pinned that line and a unit
    carrying no subject. The line now names its subject as a DATED COMMITMENTS line does, and under TT-R3-02 the
    receipt follows the line: the unit carries the subject as rendered, on every surface."""
    m = _mem(tmp_path)
    m.store.add_edge(_edge("e-c", "visiting Lisbon", "person:x", rel="currently", vol=Volatility.TRANSIENT))
    r = m.recall(U)
    [line] = [ln for ln in r.context.splitlines() if "visiting Lisbon" in ln]
    assert line.startswith("currently: person:x — visiting Lisbon (since "), line
    ch, out = surface(m, transport)("find_facts", {})
    assert ch == "ok"
    u = _unit(out, "e-c")
    assert u["subject"] == "person:x", u


def test_the_claim_line_prefix_is_the_marker_render_edges_writes():
    """`graph.CLAIM_LINE_PREFIX` (the offset a claim line's subject sits at, TT-R3-02) and the literal `render_edges`
    writes (kept literal for specs/0043's derived-marker census) are one string: a claim line starts with the prefix
    and its subject sits right after it. Mutant: either carrier edited alone."""
    e = _edge("e-q", "engineer", "person:x", disc=Disclosure.QUARANTINED)
    assert e.quarantined
    [line] = [ln for ln in graph.render_edges([e]).splitlines() if "person:x" in ln]
    assert line.startswith(graph.CLAIM_LINE_PREFIX + "person:x claims: "), line
    seg, off = graph.edge_subject_span(e)
    assert line[off:off + len(seg)] == seg == "person:x"


# ====================================================================== TT-R3-03
def _committed_dispute(m, transport, monkeypatch, error_type):
    m.store.add_edge(_edge("e-1", "tea", "user"))
    call = surface(m, transport)
    monkeypatch.setattr(m, "_record", lambda *a, **k: (_ for _ in ()).throw(error_type("after commit")))
    ch, out = call("dispute_fact", {"edge_id": "e-1"})
    held = m.store.edges(U, active_only=False, include_quarantined=True)[0]
    assert held.invalidation_reason == "disputed" and not held.active and len(m.store.episodes(U)) == 1
    return ch, out


@pytest.mark.parametrize("transport", SURFACES)
@pytest.mark.parametrize("error_type", [ValueError, TypeError])
def test_a_refusal_class_failure_after_a_commit_uses_the_error_channel(tmp_path, monkeypatch, transport, error_type):
    ch, out = _committed_dispute(_mem(tmp_path), transport, monkeypatch, error_type)
    assert ch == "error", (ch, out)


@pytest.mark.parametrize("transport", SURFACES)
@pytest.mark.parametrize("verb", ["forget_everything_confirm", "find_facts"])
def test_a_failure_after_the_erase_or_the_wiki_write_commits_uses_the_error_channel(tmp_path, monkeypatch, transport,
                                                                                    verb):
    """Research's stage-2 S23 and S24: the two verbs whose only write is not an act (the whole-user erase; find_facts'
    conditional wiki publication on an empty user, the default configuration) are phase-recorded too. A ValueError
    raised once after that write committed goes through the surface's error channel, never as a refusal; the write
    itself happened. Mutant: the verb's call made with no memory, so no cell records its commit."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    m = Memory(llm=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no model call")),
               config=MemoryConfig(db_path=str(tmp_path / "v.db"), require_source_id=False))
    call = surface(m, transport)
    args = {"query": "empty"}
    if verb == "forget_everything_confirm":
        m.store.add_edge(_edge("e-1", "tea", "user"))
        args = {"preview_token": _field(call("forget_everything_preview", {}), "preview_token")}
    real, fired = M._ok, []

    def once(result):
        if not fired:
            fired.append(1)
            raise ValueError("after the commit")
        return real(result)
    monkeypatch.setattr(M, "_ok", once)
    channel, out = call(verb, args)
    assert fired and channel == "error", (channel, out)
    if verb == "forget_everything_confirm":
        assert m.store.edges(U, active_only=False) == []                       # the erase committed
    else:
        assert m.store._conn.execute("SELECT COUNT(*) FROM wiki").fetchone()[0] == 1   # the wiki row committed


@pytest.mark.parametrize("transport", SURFACES)
def test_confirm_then_a_concurrent_erase_is_an_internal_failure(tmp_path, monkeypatch, transport):
    """The reviewer's interleaving: confirm commits, a SECOND connection erases the user, the readback raises."""
    m = _mem(tmp_path)
    m.store.add_edge(_edge("e-1", "tea", "user"))
    other = Memory(llm=lambda *a, **k: "unused", config=MemoryConfig(
        db_path=str(tmp_path / "v.db"), require_source_id=False, wiki_recompile_after_writes=0))
    call = surface(m, transport)
    real, seen = m.store.confirm_edge, []

    def interleave(*a, **k):
        conf = real(*a, **k)
        seen.append(len(other.store.confirmations_for(U, "e-1")))   # the commit is visible to another connection
        other.forget(U)
        return conf
    monkeypatch.setattr(m.store, "confirm_edge", interleave)
    ch, out = call("confirm_fact", {"edge_id": "e-1"})
    other.close()
    assert seen == [1] and m.store.edges(U) == []
    assert ch == "error", (ch, out)


@pytest.mark.parametrize("transport", SURFACES)
def test_a_pre_commit_library_refusal_is_still_a_refusal(tmp_path, transport):
    """The control: the measured library origin (confirm on a non-assertable record) refuses before any commit."""
    m = _mem(tmp_path)
    m.store.add_edge(_edge("e-q", "claim", "user", author=EvidenceAuthor.THIRD_PARTY, disc=Disclosure.QUARANTINED))
    before = m.store.confirmations_for(U, "e-q")
    ch, out = surface(m, transport)("confirm_fact", {"edge_id": "e-q"})
    assert ch == "ok" and out["ok"] is False and out["refusal"] == "refused", out
    assert m.store.confirmations_for(U, "e-q") == before


def test_the_internal_failure_is_chained_and_not_a_refusal_class(tmp_path, monkeypatch):
    m = _mem(tmp_path)
    m.store.add_edge(_edge("e-1", "tea", "user"))
    monkeypatch.setattr(m, "_record", lambda *a, **k: (_ for _ in ()).throw(ValueError("after commit")))
    with pytest.raises(TrustInternalError) as ei:
        M.dispute_fact_impl(m, U, "e-1", "", capability="direct")
    assert isinstance(ei.value.__cause__, ValueError) and not isinstance(ei.value, (ValueError, TypeError))


# ------------------------------------------------------------------ the phase record, measured independently
class _Trace:
    """The connection's own statement trace (sqlite3's trace callback): each COMMIT that closed a transaction holding
    a write. Independent of `_PhaseConnection`, which it checks."""
    WRITES = ("INSERT", "UPDATE", "DELETE", "REPLACE")

    def __init__(self, conn):
        self.writing_commits, self._wrote = 0, False
        conn.set_trace_callback(self._on)

    def _on(self, sql):
        word = sql.split(None, 1)[0].upper() if sql.strip() else ""
        if word in self.WRITES:
            self._wrote = True
        elif word in ("COMMIT", "END"):
            self.writing_commits += self._wrote
            self._wrote = False
        elif word == "ROLLBACK":
            self._wrote = False


def _record_cells(monkeypatch):
    import veracium.store.sqlite as S
    cells, real = [], S.trust_commit_phase

    def recording(conn):
        cm = real(conn)

        class _Wrap:
            def __enter__(self):
                c = cm.__enter__()
                cells.append(c)
                return c

            def __exit__(self, *exc):
                return cm.__exit__(*exc)
        return _Wrap()
    monkeypatch.setattr(S, "trust_commit_phase", recording)
    return cells


@pytest.mark.parametrize("verb", ["correct_fact", "dispute_fact", "confirm_fact", "forget_fact"])
def test_each_calls_writing_commits_equal_its_flag_sets(tmp_path, monkeypatch, verb):
    m = _mem(tmp_path)
    m.store.add_edge(_edge("e-1", "tea", "user"))
    cells = _record_cells(monkeypatch)
    trace = _Trace(m.store._conn)
    args = {"edge_id": "e-1", **({"corrected_value": "coffee"} if verb == "correct_fact" else {})}
    ch, out = surface(m, "core")(verb, args)
    assert ch == "ok" and out["ok"] is True, out
    assert len(cells) == 1 and trace.writing_commits >= 1
    assert len(cells[0]) == trace.writing_commits


def _refusing_confirm(m):
    """A confirm that the STORE refuses before writing (the measured library origin: a non-assertable record), so the
    call enters `_trust_call`, opens its cell, and refuses from inside the library."""
    m.store.add_edge(_edge("e-q", "claim", "user", author=EvidenceAuthor.THIRD_PARTY, disc=Disclosure.QUARANTINED))


def test_another_connections_commit_never_sets_this_calls_flag(tmp_path, monkeypatch):
    """A second Memory on the same file commits INSIDE this call (same thread, same context): not this call's."""
    m = _mem(tmp_path)
    _refusing_confirm(m)
    other = Memory(llm=lambda *a, **k: "unused", config=MemoryConfig(
        db_path=str(tmp_path / "v.db"), require_source_id=False, wiki_recompile_after_writes=0))
    cells = _record_cells(monkeypatch)
    real = m.store.confirm_edge

    def with_other_commit(*a, **k):
        other.store.add_edge(_edge("e-9", "juice", "user"))      # a writing commit on the OTHER connection
        return real(*a, **k)
    monkeypatch.setattr(m.store, "confirm_edge", with_other_commit)
    ch, out = surface(m, "core")("confirm_fact", {"edge_id": "e-q"})
    other.close()
    assert ch == "ok" and out["ok"] is False and out["refusal"] == "refused", out
    assert len(cells) == 1 and cells[0] == []
    assert any(e.id == "e-9" for e in m.store.edges(U))           # the other connection's commit did land


def test_a_refusal_in_one_thread_while_another_thread_commits_stays_a_refusal(tmp_path, monkeypatch):
    """The cell is per call and per context: thread B's writing commit on the SAME connection, made while thread A's
    call is inside the library before its refusal, never reaches A's cell."""
    m = _mem(tmp_path)
    _refusing_confirm(m)
    m.store.add_edge(_edge("e-1", "tea", "user"))
    a_inside, b_done = threading.Event(), threading.Event()
    real = m.store.confirm_edge
    cells = _record_cells(monkeypatch)

    def slow(*a, **k):
        if threading.current_thread().name == "A":
            a_inside.set()
            assert b_done.wait(10)
        return real(*a, **k)
    monkeypatch.setattr(m.store, "confirm_edge", slow)
    result = {}
    ta = threading.Thread(name="A", target=lambda: result.setdefault(
        "a", surface(m, "core")("confirm_fact", {"edge_id": "e-q"})))
    ta.start()
    assert a_inside.wait(10)
    ch_b, out_b = surface(m, "core")("dispute_fact", {"edge_id": "e-1"})    # B: this thread, a writing commit
    b_done.set()
    ta.join(10)
    assert ch_b == "ok" and out_b["ok"] is True, out_b
    ch_a, out_a = result["a"]
    assert ch_a == "ok" and out_a["ok"] is False and out_a["refusal"] == "refused", out_a
    a_cell = [c for c in cells if c == []]
    assert a_cell, cells                                         # A's cell stayed empty; B's recorded its commit
    assert any(len(c) >= 1 for c in cells)


def test_a_read_only_commit_is_not_a_commit_of_the_call(tmp_path):
    """A transaction that wrote nothing never sets the flag, whether it ends by the read window's COMMIT statement or
    by `commit()` (the route the connection itself records). Mutant: a read-only COMMIT counted as a write."""
    from veracium.store.sqlite import trust_commit_phase
    m = _mem(tmp_path)
    m.store.add_edge(_edge("e-1", "tea", "user"))
    conn = m.store._conn
    with trust_commit_phase(conn) as cell:
        conn.execute("BEGIN")
        conn.execute("SELECT count(*) FROM edges").fetchall()
        conn.execute("COMMIT")
        assert cell == []
        conn.execute("BEGIN")
        conn.execute("SELECT count(*) FROM edges").fetchall()
        assert conn.in_transaction
        conn.commit()                                          # the recorded route, a read-only transaction
        assert cell == []
        conn.execute("INSERT INTO write_counter(user_id, n) VALUES ('zz', 1) "
                     "ON CONFLICT(user_id) DO UPDATE SET n = n + 1")
        conn.commit()
        assert len(cell) == 1


@pytest.mark.parametrize("route", ["created", "reopened"])
def test_an_opened_stores_first_empty_commit_is_not_a_commit_of_the_call(tmp_path, route):
    """Round 4 N1: creation ends by `open_versioned`'s raw COMMIT, which never passes the phase class, so the
    constructor's mark trailed the counter (0 against 4) and a fresh store's first empty `commit()` inside a phase
    cell was recorded as a write. The store re-reads the mark after opening. Both routes an open completes by
    (an older or unstamped store refuses at open: migration is offline) start with the mark AT the counter, a first
    empty commit records nothing, and a real write still records. Mutant: the re-read after `open_versioned` removed."""
    from veracium.store.sqlite import trust_commit_phase
    if route == "reopened":
        _mem(tmp_path).close()
    m = _mem(tmp_path)
    conn = m.store._conn
    assert conn._changes_mark == conn.execute("SELECT total_changes()").fetchone()[0]
    with trust_commit_phase(conn) as cell:
        conn.execute("BEGIN")
        conn.execute("SELECT 1").fetchall()
        conn.commit()
        assert cell == []
        conn.execute("INSERT INTO write_counter(user_id, n) VALUES ('zz', 1)")
        conn.commit()
        assert len(cell) == 1
    m.close()


def test_a_rolled_back_write_is_no_commit_of_the_call_and_the_mark_follows_it(tmp_path):
    """Research's stage 2 on f25ff044, S04-S06 (NEXT-ROUND, disclosed at rounds 4 and 5): no cell held a rolled-back
    write inside a phase cell. SQLite's total_changes() keeps counting a rolled-back write, so the mark must follow a
    rollback: the rollback itself records nothing (S04: a rollback recorded as a commit), and an empty commit after it
    records nothing either (S05: a rollback not refreshing the mark); a real write after both still records. The
    class's own constructor starts the mark AT the counter (S06: the mark starting unknown; through the store the
    round-4 re-read after opening masks it, so it is held here on the class itself). Each mutant can only turn a
    refusal into an internal error (fail-safe), and each now fails one of these assertions."""
    import sqlite3
    from veracium.store.sqlite import trust_commit_phase
    m = _mem(tmp_path)
    conn = m.store._conn
    assert hasattr(type(conn), "_changes"), f"the store's connection is not the phase-recording class: {type(conn)}"
    with trust_commit_phase(conn) as cell:
        before = conn.execute("SELECT total_changes()").fetchone()[0]
        conn.execute("BEGIN")
        conn.execute("INSERT INTO write_counter(user_id, n) VALUES ('rb', 1)")
        conn.rollback()
        assert conn.execute("SELECT total_changes()").fetchone()[0] > before    # the counter kept the rolled-back row
        assert conn.execute("SELECT count(*) FROM write_counter WHERE user_id = 'rb'").fetchone()[0] == 0
        assert cell == [], cell                                                  # S04
        assert conn._changes_mark == conn.execute("SELECT total_changes()").fetchone()[0]
        conn.execute("BEGIN")
        conn.execute("SELECT 1").fetchall()
        conn.commit()
        assert cell == [], cell                                                  # S05
        conn.execute("INSERT INTO write_counter(user_id, n) VALUES ('rb', 1)")
        conn.commit()
        assert len(cell) == 1, cell                                              # a real write still records
    m.close()
    fresh = sqlite3.connect(":memory:", factory=type(conn))
    try:
        assert fresh._changes_mark == fresh.execute("SELECT total_changes()").fetchone()[0]    # S06
        with trust_commit_phase(fresh) as cell:
            fresh.execute("BEGIN")
            fresh.execute("SELECT 1").fetchall()
            fresh.commit()
            assert cell == [], cell
    finally:
        fresh.close()


def test_a_failed_counter_read_never_replaces_a_rollbacks_cause_and_counts_the_next_commit(tmp_path):
    """Research's stage-1 note (b): the counter read runs inside `rollback()` and `commit()`. If it fails, the error
    that caused the rollback is the one that surfaces, and the mark is unknown, so the next commit counts as a write
    (fail-safe), even when that commit's own read fails too; once the mark is re-read, an empty commit is not a write
    again. Mutants: the read raising over the rollback; an unknown mark read as "nothing written"."""
    import sqlite3
    from veracium.store.sqlite import trust_commit_phase
    m = _mem(tmp_path)
    conn = m.store._conn
    assert hasattr(type(conn), "_changes"), f"the store's connection is not the phase-recording class: {type(conn)}"

    def unreadable():
        raise sqlite3.OperationalError("counter unreadable")
    conn.execute("BEGIN")
    conn.execute("INSERT INTO write_counter(user_id, n) VALUES ('zz', 1) ON CONFLICT(user_id) DO UPDATE SET n = n + 1")
    conn._changes = unreadable
    surfaced = None
    try:
        try:
            raise KeyError("the cause")
        except KeyError:
            conn.rollback()
            raise
    except BaseException as exc:                                # whatever surfaces is judged, never raised past
        surfaced = exc
    assert isinstance(surfaced, KeyError) and "the cause" in str(surfaced), repr(surfaced)
    assert not conn.in_transaction
    with trust_commit_phase(conn) as cell:                      # the commit's own read fails too
        conn.execute("BEGIN")
        conn.execute("SELECT 1").fetchall()
        conn.commit()
        assert len(cell) == 1, cell                             # the mark was unknown: counted, fail-safe
    del conn._changes
    with trust_commit_phase(conn) as cell:                      # readable again; the mark still unknown
        conn.execute("BEGIN")
        conn.execute("SELECT 1").fetchall()
        conn.commit()
        assert len(cell) == 1, cell
    with trust_commit_phase(conn) as cell:                      # re-read: an empty commit is not a write again
        conn.execute("BEGIN")
        conn.execute("SELECT 1").fetchall()
        conn.commit()
        assert cell == []


# ------------------------------------------------------------------ TT-R3-04 C: the frozen principal matrices, per adapter
# INV-TT16, INV-TT17 and INV-TT19 through the core and both real framework adapters (MCP stdio binds no principal, so
# it serves only the unscoped witnesses below), and round 2's four source witnesses on the actual tools. Each refusal
# is compared WHOLE against a literal payload, and its no-write claim is a digest of every row of every table.
PA, PB, PZ = Identity(None, "src-a"), Identity(None, "src-b"), Identity(None, "src-z")    # team-a, team-b, no group
GROUPS = {"team-a": [PA], "team-b": [PB]}
NOT_FOUND = {"ok": False, "refusal": "not_found_in_scope", "detail": "no such record in this scope"}
OUT_OF_SCOPE = {"ok": False, "refusal": "out_of_scope",
                "detail": "this record is visible here but not yours to change"}
PRINCIPAL_SCOPED = {"ok": False, "refusal": "principal_scoped",
                    "detail": "the whole-user erase is not available under a principal"}
SIX = {"redacted_kind", "target_id", "reason", "marker_version", "repeated", "recorded_at"}
PROJECTION = SIX | {"surviving_derived", "scope", "ok"}     # §4d's projection inside the tools' `ok` envelope
T14 = datetime(2026, 11, 14, 12, tzinfo=timezone.utc)


def _all_rows(m) -> str:
    return "\n".join(m.store._conn.iterdump())


def _src_edge(eid, obj, source, user=U, subject="user", rel="likes"):
    return Edge(id=eid, user_id=user, subject=subject, relation=rel, object=obj, valid_from=T14,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-" + eid,
                                      source_id=source, observed_at=T14))


def _scoped(tmp_path, cross_visible=False):
    tmp_path.mkdir(parents=True, exist_ok=True)
    return Memory(llm=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no model call")),
                  config=MemoryConfig(db_path=str(tmp_path / "v.db"), require_source_id=False,
                                      wiki_recompile_after_writes=0, scope_groups=GROUPS,
                                      cross_scope_visible=cross_visible))


# One record per source, the user-wide pool, another user's record, and an absorption survivor made UNRESOLVED by its
# host-path redaction (round 2's `redaction_repeat` seam). The class each principal sees is the independent table
# `_class` below, never the product's classifier.
SOURCES = {"e-a": "src-a", "e-b": "src-b", "e-z": "src-z", "e-s": None}


def _classed_store(tmp_path, cross_visible):
    m = _scoped(tmp_path, cross_visible)
    for eid, src in SOURCES.items():
        m.store.add_edge(_src_edge(eid, "v" + eid, src))
    m.store.add_edge(_src_edge("e-x", "soda", "src-a", user="someone-else"))
    m.store.add_edge(_src_edge("e-short", "Miso", "src-a", rel="has_pet"))
    graph.apply_supersession(m.store, _src_edge("e-full", "cat Miso", "src-a", rel="has_pet"), m.config.relations)
    m.redact(U, edge_id="e-full", reason="subject_request")
    return m


def _class(principal, eid, cross_visible):
    if eid == "e-full":
        return "UNRESOLVED"
    if eid == "e-x":
        return "OTHER_USER"
    if eid == "e-nope":
        return "UNKNOWN"
    src = SOURCES[eid]
    if src == principal.source_id:
        return "OWN"
    if src is None:
        return "SHARED"
    return "CROSS_VISIBLE" if cross_visible else "CROSS_HIDDEN"


EXPECTED = {"SHARED": OUT_OF_SCOPE, "CROSS_VISIBLE": OUT_OF_SCOPE, "CROSS_HIDDEN": NOT_FOUND,
            "UNRESOLVED": NOT_FOUND, "OTHER_USER": NOT_FOUND, "UNKNOWN": NOT_FOUND}
VERB_ARGS = {"correct_fact": lambda eid: {"edge_id": eid, "corrected_value": "coffee"},
             "dispute_fact": lambda eid: {"edge_id": eid, "reason": "not so"},
             "confirm_fact": lambda eid: {"edge_id": eid},
             "forget_fact": lambda eid: {"edge_id": eid}}


@pytest.mark.parametrize("verb", list(VERB_ARGS))
@pytest.mark.parametrize("cross_visible", [False, True], ids=["cross-hidden", "cross-visible"])
@pytest.mark.parametrize("principal", [PA, PB, PZ], ids=["in-team-a", "in-team-b", "in-no-group"])
@pytest.mark.parametrize("name", PRINCIPAL_SURFACES)
def test_the_decision_table_per_class_through_each_adapter(tmp_path, name, principal, cross_visible, verb):
    """INV-TT16 per adapter: OWN acted on; SHARED and CROSS_VISIBLE refused `out_of_scope`; CROSS_HIDDEN, UNRESOLVED,
    another user's id and an unknown id refused with ONE whole response; every refusal writes nothing. Principals in a
    group, in another group and in no group at all. Mutants: SHARED admitted; CROSS_VISIBLE admitted; a distinct
    response for an unknown id; the adapter not passing the principal (every class acted on)."""
    m = _classed_store(tmp_path, cross_visible)
    call = surface(m, name, principal=principal, source_id=principal.source_id)
    own = next(e for e, s in SOURCES.items() if s == principal.source_id)
    for eid in [e for e in (*SOURCES, "e-full", "e-x", "e-nope") if e != own]:
        before = _all_rows(m)
        got = call(verb, VERB_ARGS[verb](eid))
        assert got == ("ok", EXPECTED[_class(principal, eid, cross_visible)]), (eid, got)
        assert _all_rows(m) == before, eid
    before = _all_rows(m)
    channel, out = call(verb, VERB_ARGS[verb](own))                   # OWN: acted on, and the store moved
    assert channel == "ok" and "refusal" not in out and _all_rows(m) != before, out
    if verb == "forget_fact":
        assert set(out) == PROJECTION and out["ok"] is True and out["target_id"] == own, out


@pytest.mark.parametrize("tool", ["forget_everything_preview", "forget_everything_confirm"])
@pytest.mark.parametrize("name", PRINCIPAL_SURFACES)
def test_both_whole_user_tools_refuse_a_principal_through_each_adapter(tmp_path, name, tool):
    """INV-TT17 per adapter: under a principal both whole-user tools refuse `principal_scoped` and write nothing, even
    with a token the same surface issued with no principal (still valid: the unprincipaled binding then erases with
    it); the capability and erasure gates come first. Mutants: the refusal on the preview only; the refusal skipped
    when erasure is on; the adapter not passing the principal."""
    m = _scoped(tmp_path)
    m.store.add_edge(_src_edge("e-a", "tea", "src-a"))
    host = surface(m, name, source_id="src-a")
    token = _field(host("forget_everything_preview", {}), "preview_token")
    args = {} if tool == "forget_everything_preview" else {"preview_token": token}
    before = _all_rows(m)
    for erasure in (None, "on"):
        kw = {} if erasure is None else {"erasure": erasure}
        assert surface(m, name, principal=PA, source_id="src-a", **kw)(tool, args) == ("ok", PRINCIPAL_SCOPED)
        assert _all_rows(m) == before, erasure
    off = surface(m, name, principal=PA, source_id="src-a", erasure="off")(tool, args)
    assert off == ("ok", {"ok": False, "refusal": "erasure_disabled", "detail": "erasure through the agent is turned "
                          "off for this deployment (VERACIUM_MCP_ERASURE=off)"}), off
    assert _all_rows(m) == before
    if tool == "forget_everything_confirm":                     # the token was good: the gate, not the token, refused
        done = host("forget_everything_confirm", {"preview_token": token})
        assert _field(done, "ok") is True and _field(done, "edges") == 1, done


@pytest.mark.parametrize("tool", ["forget_everything_preview", "forget_everything_confirm"])
@pytest.mark.parametrize("name", PRINCIPAL_SURFACES)
def test_under_a_principal_the_capability_gate_still_comes_first(tmp_path, name, tool):
    m = _scoped(tmp_path)
    before = _all_rows(m)
    args = {} if tool == "forget_everything_preview" else {"preview_token": "x"}
    b = {"user_id": U, "capability": None, "principal": PA, "source_id": "src-a"}
    d = D.CoreDriver(_surface, m, b) if name == "core" else \
        {"langchain": D.LangChainDriver, "pydantic_ai": D.PydanticAIDriver}[name](_row(name), m, b)
    channel, out = d.decode(d.call(tool, args))
    assert channel == "ok" and out["refusal"] == "attempted_elevation", out
    assert _all_rows(m) == before


# ------------------------------------------------------------------ INV-TT19's absorption-descendant comparison
def _absorption(tmp_path, extended):
    """Round 2's `redaction_hidden_metadata` chain: source-A `Miso` absorbed into `cat Miso`; in the extended fixture
    only, that absorbed into `pet cat Miso`; then `cat Miso` redacted on the host path in both, which leaves the
    extended fixture a hidden UNRESOLVED descendant. The target `Miso` still classes OWN in both."""
    m = _scoped(tmp_path)
    m.store.add_edge(_src_edge("e-miso", "Miso", "src-a", rel="has_pet"))
    graph.apply_supersession(m.store, _src_edge("e-cat", "cat Miso", "src-a", rel="has_pet"), m.config.relations)
    if extended:
        graph.apply_supersession(m.store, _src_edge("e-pet", "pet cat Miso", "src-a", rel="has_pet"),
                                 m.config.relations)
    m.redact(U, edge_id="e-cat", reason="subject_request")
    return m


def test_the_absorption_chain_fixture_has_its_hidden_descendant_and_the_host_receipt_shows_it(tmp_path):
    """The comparison below is not vacuous: only the extended fixture holds an UNRESOLVED descendant, the target is
    OWN in both, and the HOST receipt (unchanged, whole) differs between the two in `fields_cleared`."""
    host = {}
    for ext in (False, True):
        m = _absorption(tmp_path / f"host-{ext}", ext)
        view = m._scope_view(U, PA)
        assert view.classification(m._find_edge(U, "e-miso")) == "OWN", ext
        if ext:
            assert view.classification(m._find_edge(U, "e-pet")) == "UNRESOLVED"
        host[ext] = m.redact(U, edge_id="e-miso", reason="subject_request").fields_cleared
    assert host[False] != host[True], host


@pytest.mark.parametrize("name", PRINCIPAL_SURFACES)
def test_two_absorption_chains_differing_only_in_a_hidden_descendant_answer_alike(tmp_path, name):
    """INV-TT19 per adapter: forget_fact on `Miso` under A returns identical results (recorded_at normalized) whether
    or not a hidden UNRESOLVED descendant exists. Mutants: `fields_cleared` kept; a hidden entry kept; a "hidden
    records exist" flag."""
    out = []
    for ext in (False, True):
        m = _absorption(tmp_path / str(ext), ext)
        channel, r = surface(m, name, principal=PA, source_id="src-a")("forget_fact", {"edge_id": "e-miso"})
        assert channel == "ok" and set(r) == PROJECTION and r["ok"] is True, r
        out.append({**r, "recorded_at": "<t>"})
    assert out[0] == out[1], out


# ------------------------------------------------------------------ round 2's four source witnesses, on the tools
@pytest.mark.parametrize("name", PRINCIPAL_SURFACES)
def test_redaction_repeat_through_each_adapter(tmp_path, name):
    """Round 2's `redaction_repeat`: a repeat under a principal passes a FRESH gate. A plain OWN record stays eligible
    (`repeated=True`, the same keys); an absorption survivor made UNRESOLVED by its own redaction is `not_found_in_scope`,
    whole, and writes nothing. Mutant: a repeat answered from the earlier receipt without the gate."""
    m = _scoped(tmp_path)
    m.store.add_edge(_src_edge("e-plain", "tea", "src-a"))
    m.store.add_edge(_src_edge("e-short", "Miso", "src-a", rel="has_pet"))
    graph.apply_supersession(m.store, _src_edge("e-full", "cat Miso", "src-a", rel="has_pet"), m.config.relations)
    call = surface(m, name, principal=PA, source_id="src-a")
    first = call("forget_fact", {"edge_id": "e-plain"})
    again = call("forget_fact", {"edge_id": "e-plain"})
    assert _field(first, "repeated") is False and _field(again, "repeated") is True, (first, again)
    assert set(again[1]) == set(first[1])
    assert _field(call("forget_fact", {"edge_id": "e-full"}), "repeated") is False
    before = _all_rows(m)
    assert call("forget_fact", {"edge_id": "e-full"}) == ("ok", NOT_FOUND)
    assert _all_rows(m) == before


@pytest.mark.parametrize("name, bound", [(s, "no-principal") for s in SURFACES]
                         + [(s, "principal") for s in PRINCIPAL_SURFACES])     # MCP stdio binds no principal (§4f.6)
def test_correction_refusal_is_committed_through_each_surface(tmp_path, name, bound):
    """Round 2's `correction_refusal`: correcting an edge about another subject reaches the standing OTHER-subject
    refusal, a COMMITTED refusal (supersession_refusals, supersession_operations and write_counter move) returned
    serialized; the target stays active. Under a principal too, on an OWN record. Mutant: the committed refusal rolled
    back, or raised to the transport."""
    m = _scoped(tmp_path)
    m.store.add_edge(_src_edge("e-bob", "Rome", "src-a", subject="person:bob", rel="located_at"))
    count = {t: m.store._conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
             for t in ("supersession_refusals", "supersession_operations")}
    b = {"principal": PA, "source_id": "src-a"} if bound == "principal" else {}
    channel, out = surface(m, name, **b)("correct_fact", {"edge_id": "e-bob", "corrected_value": "Oslo"})
    assert channel == "ok" and out.get("ok") is False and out.get("refusal") == "correction_refused", out
    for t, k in count.items():
        assert m.store._conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] > k, t
    assert next(e for e in m.store.edges(U) if e.id == "e-bob").active


@pytest.mark.parametrize("name", SURFACES)
def test_lookup_writes_and_keyset_replay_through_each_surface(tmp_path, name):
    """Round 2's `lookup_writes_and_keyset_replay`: on an empty user, find_facts writes one wiki row and a second
    lookup writes nothing; the erase token replays by key-set equality (store_changed after a successful erase of a
    non-empty set; the same id restored, it erases again). Mutants: every lookup republishing; a replay ignoring
    key-set equality."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    m = Memory(llm=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no model call")),
               config=MemoryConfig(db_path=str(tmp_path / "v.db"), require_source_id=False))
    call = surface(m, name)
    wiki = lambda: m.store._conn.execute("SELECT COUNT(*) FROM wiki").fetchone()[0]     # noqa: E731
    before = _all_rows(m)
    assert _field(call("find_facts", {"query": "empty"}), "ok") is True
    assert wiki() == 1
    once = _all_rows(m)
    assert once != before and _field(call("find_facts", {"query": "empty"}), "ok") is True and _all_rows(m) == once
    m.store.add_edge(_src_edge("e-1", "tea", None))
    tok = _field(call("forget_everything_preview", {}), "preview_token")
    assert _field(call("forget_everything_confirm", {"preview_token": tok}), "edges") == 1
    replay = call("forget_everything_confirm", {"preview_token": tok})
    assert _field(replay, "refusal") == "store_changed", replay
    m.store.add_edge(_src_edge("e-1", "tea", None))                           # the same id restored
    assert _field(call("forget_everything_confirm", {"preview_token": tok}), "edges") == 1
