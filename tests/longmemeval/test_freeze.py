"""Freeze-artifact verification — the four checks, and the two escalation rules.

The design under test is not "does it parse a file". It is:

  * a WRONG freeze id **aborts** — the operator believes something false about
    what is being run, and that must not proceed to a paid call;
  * everything else **downgrades to exploratory** and never blocks the run,
    because a verification step that can stop a run gets disabled the first time
    it misfires, while one that can only downgrade a label survives.

Each test names the thing it prevents.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from freeze import (FreezeError, REQUIRED_FIELDS, sha256_file, sha256_items,
                    verify)

RUN_START = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
ITEMS = ["q1", "q2", "q3"]


def _freeze(tmp_path, *, approved_at="2026-07-31T09:00:00Z", omit=(),
            item_hash=None, name="exp-01.md"):
    item_hash = item_hash if item_hash is not None else sha256_items(ITEMS)
    lines = {
        "experiment_name": "coverage-selection-balanced",
        "arm_name": "mmr-coverage-on",
        "hypothesis": "coverage-aware selection raises answer-turn hit rate",
        "primary_metric": "answer-turn hit rate (coverage level 2)",
        "secondary_metrics": "distinct-session coverage; read tokens",
        "thresholds": "minimum_improvement: +10pp",
        "analysis_plan": "unit = unique item; 3 replicates; >=2/3 improve",
        "mapping_procedure": "evidence_ref matches a turn marked has_answer",
        "item_set": "re-drawn MS + TR arms stratified on session-day diversity",
        "stop_rules": "if coverage rises and the metric does not, falsified",
        "approved_by": "research",
        "approved_at": approved_at,
    }
    for k in omit:
        lines.pop(k, None)
    body = "\n".join(f"{k}: {v}" for k, v in lines.items())
    body += f"\nitem_set_hash: {item_hash}\n"
    p = tmp_path / name
    p.write_text(body)
    return p


# --- check 1: the id must match the bytes, and that ABORTS -------------------

def test_wrong_freeze_id_aborts_before_any_paid_call():
    """Not a downgrade. The operator asserted this run is governed by a
    protocol, and it is not."""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    f = _freeze(tmp)
    with pytest.raises(FreezeError) as e:
        verify(f, freeze_id="0" * 64, run_started_at=RUN_START, item_ids=ITEMS)
    assert "does not match" in str(e.value)
    assert "before the first paid call" in str(e.value)


def test_missing_freeze_file_aborts():
    with pytest.raises(FreezeError) as e:
        verify("/nonexistent/exp-99.md", freeze_id="abc",
               run_started_at=RUN_START, item_ids=ITEMS)
    assert "does not exist" in str(e.value)


def test_correct_id_and_content_is_confirmatory(tmp_path):
    f = _freeze(tmp_path)
    v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
               item_ids=ITEMS)
    assert v.confirmatory, v.problems
    assert v.freeze_id == sha256_file(f)


# --- check 2: required fields ----------------------------------------------

@pytest.mark.parametrize("field", ["hypothesis", "primary_metric", "thresholds",
                                   "stop_rules", "approved_by"])
def test_a_missing_required_field_makes_the_run_exploratory(tmp_path, field):
    """An unstated threshold is what post-hoc reasoning fills in."""
    f = _freeze(tmp_path, omit=(field,))
    v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
               item_ids=ITEMS)
    assert not v.confirmatory
    assert field in " ".join(v.problems)


def test_required_field_list_matches_the_spec():
    for f in ("experiment_name", "arm_name", "hypothesis", "primary_metric",
              "thresholds", "analysis_plan", "mapping_procedure", "item_set",
              "stop_rules", "approved_by", "approved_at"):
        assert f in REQUIRED_FIELDS


# --- check 3: approved BEFORE the run ---------------------------------------

def test_a_freeze_approved_after_the_run_started_is_not_a_freeze(tmp_path):
    """The whole point of the mechanism. Content fixed after outcomes exist is
    a description, not a prediction."""
    late = (RUN_START + timedelta(minutes=1)).isoformat()
    f = _freeze(tmp_path, approved_at=late)
    v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
               item_ids=ITEMS)
    assert not v.confirmatory
    assert "not strictly before run start" in " ".join(v.problems)


def test_approval_exactly_at_run_start_is_rejected(tmp_path):
    """'Strictly earlier' — a tie means we cannot show which came first."""
    f = _freeze(tmp_path, approved_at=RUN_START.isoformat())
    v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
               item_ids=ITEMS)
    assert not v.confirmatory


def test_unparseable_approval_date_is_not_silently_accepted(tmp_path):
    f = _freeze(tmp_path, approved_at="last Tuesday")
    v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
               item_ids=ITEMS)
    assert not v.confirmatory
    assert "approved_at" in " ".join(v.problems)


# --- check 4: the denominator cannot move -----------------------------------

def test_item_set_mismatch_makes_the_run_exploratory(tmp_path):
    """G7: the denominator must not be able to move after the fact."""
    f = _freeze(tmp_path)
    v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
               item_ids=ITEMS + ["q4"])
    assert not v.confirmatory
    assert "item_set_hash mismatch" in " ".join(v.problems)


def test_item_set_hash_is_order_independent(tmp_path):
    f = _freeze(tmp_path)
    v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
               item_ids=list(reversed(ITEMS)))
    assert v.confirmatory, v.problems


def test_missing_item_set_hash_is_flagged(tmp_path):
    f = _freeze(tmp_path)
    f.write_text(f.read_text().split("item_set_hash")[0])
    v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
               item_ids=ITEMS)
    assert not v.confirmatory
    assert "item_set_hash" in " ".join(v.problems)


# --- the governing rule: never block a run ----------------------------------

def test_no_freeze_at_all_is_exploratory_not_an_error():
    """Most runs have no freeze and that is fine. The runner refuses to call a
    run confirmatory; it does not refuse to run it."""
    v = verify(None, freeze_id=None, run_started_at=RUN_START, item_ids=ITEMS)
    assert not v.confirmatory
    assert "no freeze artifact" in v.explain()
    assert "normal" in v.explain()


def test_every_failure_mode_downgrades_rather_than_raising(tmp_path):
    """Only a wrong id raises. Everything else must return a verdict, because a
    check that can stop a run gets disabled the first time it misfires."""
    cases = [
        _freeze(tmp_path, omit=("hypothesis",), name="a.md"),
        _freeze(tmp_path, approved_at="2027-01-01T00:00:00Z", name="b.md"),
        _freeze(tmp_path, item_hash="deadbeefdeadbeef", name="c.md"),
    ]
    for f in cases:
        v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
                   item_ids=ITEMS)
        assert not v.confirmatory
        assert v.problems and v.explain().startswith("exploratory")


def test_the_verdict_explains_itself(tmp_path):
    """A bare bool is useless six weeks later."""
    f = _freeze(tmp_path, omit=("thresholds",))
    v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
               item_ids=ITEMS)
    assert "thresholds" in v.explain()
    assert v.as_dict()["problems"]
