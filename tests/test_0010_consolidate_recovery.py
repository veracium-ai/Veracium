"""specs/0010 §6 — consolidate() on the crash-safe state machine (Slice 3c).

The integrative layer: write-before-delete (X1), roll-forward recovery (X2), retry
idempotency incl. no-summary-of-summary (X3/X16), the crash sweep (X5), whole-batch
lineage (X6/X8/X12), read-only export (X17), and honest import shapes (X18/X19).
"""
import json
from datetime import datetime, timedelta, timezone

import pytest

from veracium.config import MemoryConfig
from veracium.lifecycle import consolidate
from veracium.portability import export_memory, import_memory
from veracium.schema import (ConsolidationOutputDraft, Episode, EvidenceAuthor, Provenance, to_historical_id)
from veracium.store.sqlite import SqliteStore

NOW = datetime(2026, 6, 1, tzinfo=timezone.utc)
CONF = MemoryConfig(consolidate_after_days=30, consolidate_min_batch=8)


class Clock:
    def __init__(self):
        self.t = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t = self.t + timedelta(seconds=s)


def _llm(n_records=2):
    def f(*a, **k):
        return json.dumps({"records": [
            {"date": "2026-01-01", "summary": f"merged {i}"} for i in range(n_records)]})
    return f


def _store(tmp_path, name="t.db"):
    clk = Clock()
    s = SqliteStore(str(tmp_path / name), clock=clk)
    s._clk = clk
    return s


def _seed_cold(store, n=8):
    ids = []
    for i in range(1, n + 1):
        eid = f"e{i}"
        store.add_episode(Episode(
            id=eid, user_id="u", date=f"2026-01-{i:02d}", summary=f"day {i}",
            provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                  evidence_ref=f"r{i}",
                                  observed_at=datetime(2026, 1, i, tzinfo=timezone.utc))))
        ids.append(eid)
    return ids


def _visible_outputs(store):
    return [e for e in store.episodes("u") if e.lineage]


# --- crash-injection proxy: run the primitive (it commits), THEN "crash" ------

class CrashAfter:
    """Delegates to a real store but, on the Nth call of `method`, lets it commit and
    then raises — simulating a process death immediately AFTER a durable step."""
    def __init__(self, real, method, nth=1):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_method", method)
        object.__setattr__(self, "_nth", nth)
        object.__setattr__(self, "_count", 0)

    def __getattr__(self, name):
        attr = getattr(self._real, name)
        if name != self._method:
            return attr

        def wrapped(*a, **k):
            object.__setattr__(self, "_count", self._count + 1)
            result = attr(*a, **k)
            if self._count == self._nth:
                raise RuntimeError(f"crash after {name} #{self._nth}")
            return result
        return wrapped


# --- X1: write-before-delete ------------------------------------------------

def test_consolidation_writes_before_deleting(tmp_path):
    store = _store(tmp_path)
    _seed_cold(store)
    # crash immediately after the input batch-delete: the outputs are ALREADY durable
    proxy = CrashAfter(store, "delete_claimed_inputs_if_current")
    with pytest.raises(RuntimeError):
        consolidate(proxy, _llm(), "u", CONF, now=NOW)
    # outputs are durable+visible; inputs gone — nothing was lost (write preceded delete)
    outs = _visible_outputs(store)
    assert outs, "outputs must be durable before any input is deleted"
    assert not any(e.id.startswith("e") and not e.lineage for e in store.episodes("u"))


# --- X2: roll-forward recovery after a committed delete ---------------------

def test_recovery_finalises_after_committed_delete(tmp_path):
    store = _store(tmp_path)
    _seed_cold(store)
    proxy = CrashAfter(store, "delete_claimed_inputs_if_current")
    with pytest.raises(RuntimeError):
        consolidate(proxy, _llm(), "u", CONF, now=NOW)
    assert store.pending_consolidations("u"), "an OUTPUTS_DURABLE op awaits finalize"
    # recovery rolls it FORWARD (idempotent re-delete + finalize) — never re-consolidates
    rep = consolidate(store, _llm(), "u", CONF, now=NOW)
    assert rep["recovered"] == 1
    assert store.pending_consolidations("u") == []
    assert _visible_outputs(store)


# --- X3 / X16: retry is idempotent — no summary-of-summary ------------------

def test_consolidation_retry_is_idempotent(tmp_path):
    store = _store(tmp_path)
    _seed_cold(store)
    r1 = consolidate(store, _llm(), "u", CONF, now=NOW)
    assert r1["consolidated"] == 8
    r2 = consolidate(store, _llm(), "u", CONF, now=NOW)
    assert r2 == {"consolidated": 0, "into": 0, "recovered": 0}


def test_finalized_outputs_are_not_reconsolidated(tmp_path):
    store = _store(tmp_path)
    _seed_cold(store, 16)
    consolidate(store, _llm(), "u", CONF, now=NOW)      # 16 → a few outputs
    outs = _visible_outputs(store)
    assert 0 < len(outs) < 16
    # the outputs' own compat date is old and there are >= min_batch of them, yet a
    # re-run selects NONE of them (non-empty lineage → never a candidate, X16/§4e)
    rep = consolidate(store, _llm(), "u", CONF, now=NOW)
    assert rep["consolidated"] == 0


def test_consolidated_output_is_not_a_candidate(tmp_path):
    store = _store(tmp_path)
    _seed_cold(store, 16)
    consolidate(store, _llm(), "u", CONF, now=NOW)
    assert consolidate(store, _llm(), "u", CONF, now=NOW)["consolidated"] == 0


def test_released_input_is_a_candidate_again(tmp_path):
    store = _store(tmp_path)
    _seed_cold(store)
    op = store.create_or_takeover_consolidation("u", [f"e{i}" for i in range(1, 9)],
                                                "w1", 60)
    store._clk.advance(120)                             # lease expires
    store.abandon_consolidation_if_current(op.operation_id, op.fence)  # inputs released
    # the released inputs are eligible cold candidates again (keying exclusion on
    # operation_id would strand them — X16)
    rep = consolidate(store, _llm(), "u", CONF, now=NOW)
    assert rep["consolidated"] == 8


# --- X5: no crash point loses an episode without a replacement --------------

@pytest.mark.parametrize("method,nth", [
    ("create_or_takeover_consolidation", 1),
    ("transition_consolidation_if_current", 1),   # →GENERATING
    ("write_consolidation_output_if_current", 1),
    ("transition_consolidation_if_current", 2),   # →OUTPUTS_DURABLE (the cutover)
    ("delete_claimed_inputs_if_current", 1),
    ("transition_consolidation_if_current", 3),   # →FINALIZED
], ids=lambda v: str(v))
def test_no_crash_point_loses_data(tmp_path, method, nth):
    store = _store(tmp_path, name=f"{method}{nth}.db")
    originals = _seed_cold(store)
    proxy = CrashAfter(store, method, nth)
    try:
        consolidate(proxy, _llm(), "u", CONF, now=NOW)
    except RuntimeError:
        pass
    # let any live pre-cutover lease expire so recovery may clean it, then recover
    store._clk.advance(400)
    consolidate(store, _llm(), "u", CONF, now=NOW)
    # every original input is represented — still present, OR absorbed into a visible
    # output's lineage. Never lost without a replacement.
    visible = store.episodes("u")
    present = {e.id for e in visible}
    absorbed = set().union(*[set(e.lineage) for e in visible if e.lineage]) \
        if any(e.lineage for e in visible) else set()
    for oid in originals:
        assert oid in present or to_historical_id(oid) in absorbed, \
            f"{oid} lost after a crash at {method}#{nth}"


# --- X6 / X8 / X12: every output carries the WHOLE claimed set as lineage -----

def test_lineage_is_the_whole_batch(tmp_path):
    store = _store(tmp_path)
    ids = _seed_cold(store)
    consolidate(store, _llm(3), "u", CONF, now=NOW)     # 8 → 3 outputs
    outs = _visible_outputs(store)
    assert len(outs) == 3
    whole = [to_historical_id(i) for i in ids]
    for o in outs:                                      # NO input→output partition
        assert o.lineage == whole, "each output must inherit the entire claimed set"


def test_summary_lineage_lists_every_absorbed_episode(tmp_path):
    store = _store(tmp_path)
    ids = _seed_cold(store)
    consolidate(store, _llm(1), "u", CONF, now=NOW)
    out = _visible_outputs(store)[0]
    assert set(out.lineage) == {to_historical_id(i) for i in ids}


# --- X17: export is read-only, refuses non-quiescent ------------------------

def test_export_refuses_nonquiescent_without_mutating(tmp_path):
    store = _store(tmp_path)
    _seed_cold(store)
    store.create_or_takeover_consolidation("u", ["e1", "e2"], "w1", 60)  # in flight
    before = {e.id: e.model_dump() for e in store.episodes("u")}
    with pytest.raises(ValueError, match="in flight"):
        export_memory(store, "u", str(tmp_path / "exp.jsonl"))
    after = {e.id: e.model_dump() for e in store.episodes("u")}
    assert after == before, "a refused export must mutate nothing"


def test_export_then_import_round_trips_a_finalized_output(tmp_path):
    src = _store(tmp_path, "src.db")
    _seed_cold(src)
    consolidate(src, _llm(1), "u", CONF, now=NOW)
    exp = str(tmp_path / "e.jsonl")
    export_memory(src, "u", exp)                        # quiescent → exports
    dst = _store(tmp_path, "dst.db")
    import_memory(dst, exp)
    out = _visible_outputs(dst)[0]
    assert out.lineage and out.summary.startswith("merged")


# --- X18: import refuses claimed-input + malformed-lineage shapes ------------

def _write_export(path, records, uid="u", version=3):
    with open(path, "w") as f:
        f.write(json.dumps({"kind": "veracium-export", "version": version,
                            "user_id": uid, "exported_at": "x"}) + "\n")
        for marker, obj in records:
            f.write(json.dumps({"record": marker, **obj}) + "\n")


def _out_rec(oid="epc-1", lineage=None, operation_id="op-src", uid="u"):
    return ("episode", {
        "id": oid, "user_id": uid, "date": "2026-01-01", "summary": "merged",
        "operation_id": operation_id,
        "lineage": lineage if lineage is not None else ["hist:e1", "hist:e2"],
        "date_start": "2026-01-01", "date_end": "2026-01-02",
        "provenance": {"author_of_evidence": "system",
                       "evidence_ref": operation_id,
                       "observed_at": "2026-01-02T00:00:00+00:00"}})


def test_import_refuses_claimed_input_shape(tmp_path):
    claimed = ("episode", {
        "id": "e1", "user_id": "u", "date": "2026-01-01", "summary": "s",
        "claimed_by": "op-x", "operation_id": "op-x",
        "provenance": {"author_of_evidence": "user",
                       "evidence_ref": "r"}})
    p = str(tmp_path / "x.jsonl")
    _write_export(p, [claimed])
    with pytest.raises(ValueError, match="CLAIMED input"):
        import_memory(_store(tmp_path, "d.db"), p)


def test_malformed_lineage_shape_is_refused(tmp_path):
    p = str(tmp_path / "x.jsonl")
    _write_export(p, [_out_rec(lineage=["e1", "e2"])])   # non-historical lineage ids
    with pytest.raises(ValueError, match="malformed lineage"):
        import_memory(_store(tmp_path, "d.db"), p)


# --- X19: operation_id is remapped to a non-colliding historical namespace ---

def test_imported_operation_id_cannot_collide_with_a_live_local_op(tmp_path):
    p = str(tmp_path / "x.jsonl")
    _write_export(p, [_out_rec(operation_id="op-src")])
    dst = _store(tmp_path, "d.db")
    import_memory(dst, p)
    out = _visible_outputs(dst)[0]
    # the imported output's operation_id is now HISTORICAL — no live "op-" op collides
    assert out.operation_id == "hist:op-src"
    assert not out.operation_id.startswith("op-")


def test_partial_then_retried_import_keeps_one_producer_group(tmp_path):
    p = str(tmp_path / "x.jsonl")
    _write_export(p, [_out_rec(operation_id="op-src")])
    dst = _store(tmp_path, "d.db")
    import_memory(dst, p)
    import_memory(dst, p)                               # deterministic remap → idempotent
    outs = _visible_outputs(dst)
    assert len(outs) == 1, "retry must not create a second producer group"
