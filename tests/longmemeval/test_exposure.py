"""G1 — the exposure ledger's contract."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import exposure


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(exposure, "LEDGER", tmp_path / "ledger.jsonl")


def test_machine_and_human_exposure_are_recorded_separately(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    exposure.record_exposure(["a", "b"], kind="machine", source="script")
    exposure.record_exposure(["b", "c"], kind="human", source="review")
    assert exposure.exposed_ids("machine") == {"a", "b"}
    assert exposure.exposed_ids("human") == {"b", "c"}
    assert exposure.exposed_ids() == {"a", "b", "c"}


def test_unknown_kind_is_refused_not_coerced(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    try:
        exposure.record_exposure(["x"], kind="auto", source="s")
        raise AssertionError("kind='auto' must be refused")
    except ValueError:
        pass
    assert exposure.exposed_ids() == set()


def test_snapshot_precedes_and_excludes_only_recorded_exposure(tmp_path, monkeypatch):
    """The pre-execution rule: a snapshot taken BEFORE an event does not know
    it; recording then shrinks the next snapshot. Order is observable."""
    _isolate(tmp_path, monkeypatch)
    universe = ["a", "b", "c", "d"]
    exposure.record_exposure(["a"], kind="machine", source="pilot")
    before = exposure.confirmatory_snapshot(universe)
    assert before["confirmatory"] == ["b", "c", "d"]
    exposure.record_exposure(["b"], kind="human", source="inspection")
    after = exposure.confirmatory_snapshot(universe)
    assert after["confirmatory"] == ["c", "d"]
    assert before["confirmatory_hash"] != after["confirmatory_hash"]
    assert after["by_kind"] == {"machine": 1, "human": 1}


def test_ledger_is_append_only_jsonl(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    exposure.record_exposure(["a"], kind="machine", source="s1")
    exposure.record_exposure(["b"], kind="human", source="s2", backfilled=True)
    lines = [json.loads(line) for line in
             (tmp_path / "ledger.jsonl").read_text().splitlines()]
    assert [ev["source"] for ev in lines] == ["s1", "s2"]
    assert lines[1]["backfilled"] is True
