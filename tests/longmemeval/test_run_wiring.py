"""End-to-end wiring for the manifest layer, with a fake provider.

`test_manifest.py` tests the mechanism in isolation. This file tests that the
runner is actually *wired* to it — a distinction that matters here more than
usual, because the incident this guards against was a patch that edited nothing
while every component it touched kept working perfectly.

No network: the provider is a canned-JSON stub.

    PYTHONPATH=src python -m pytest tests/longmemeval/test_run_wiring.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from adapter import Item, Session, Turn
from manifest import ManifestError
import run_longmemeval as R

# Every test here drives a real run, and a run WRITES A MANIFEST whose git state must
# resolve (resolving rather than remembering is the manifest's G14 integrity feature).
# An extracted review archive is not a checkout, so the runs cannot execute there by
# design — skip the module rather than fail it (the spec-gate git tests' convention).
import subprocess as _subprocess
pytestmark = pytest.mark.skipif(
    _subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True,
                    cwd=Path(__file__).parent).returncode != 0,
    reason="not a git checkout; a run's manifest resolves git state by design")


class FakeProvider:
    """Canned extraction JSON for distill, a canned sentence for the answer."""

    def __init__(self):
        self.calls = 0
        self.retries = 0
        self.failures = 0
        self.error_classes: dict = {}

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        self.calls += 1
        if role == "distill":
            return json.dumps({"triples": [
                {"subject": "user", "relation": "prefers", "object": "tea"}]})
        return "According to confirmed records, you prefer tea."


def _items(n=2):
    session = Session(session_id="s1", stamp="2023/05/20 (Sat) 10:00",
                      iso="2023-05-20T10:00:00",
                      turns=(Turn(role="user", content="I prefer tea.", index=0),))
    return [Item(question_id=f"q{i}", question="What do I drink?",
                 question_date="2023/05/20 (Sat) 10:00", sessions=(session,))
            for i in range(n)]


def _run(tmp_path, **kw):
    kw.setdefault("cache_enabled", False)
    kw.setdefault("out_dir", tmp_path)
    kw.setdefault("data_path", tmp_path / "nonexistent-dataset.json")
    return R.run(_items(), provider=FakeProvider(), **kw)


def test_a_run_writes_a_manifest_and_an_attestation(tmp_path):
    rec = _run(tmp_path, experiment="wiring-test", freeze_id="freeze_test")
    man = json.loads((tmp_path / f"manifest_{rec['run_id']}.json").read_text())
    att = json.loads((tmp_path / f"attestation_{rec['run_id']}.json").read_text())

    assert man["experiment_name"] == "wiring-test"
    assert man["source"]["commit"] != "unknown"
    assert att["manifest_hash"] == man["manifest_hash"]
    assert att["execution_status"] == "completed"
    # the runner must not declare its own output valid: validity is a later
    # analytical call, which is the whole reason it is a separate axis
    assert att["validity_status"] == "unreviewed"
    assert not rec["decision_eligible"]


def test_the_record_no_longer_asserts_a_single_config_value(tmp_path):
    """The old record wrote `"max_subgraph_edges": <requested>`, which was
    false for hours. It must be gone, not merely supplemented."""
    rec = _run(tmp_path)
    assert "max_subgraph_edges" not in rec
    triple = rec["effective_config"]["max_subgraph_edges"]
    assert set(triple) == {"requested", "resolved", "observed"}
    assert triple["resolved"] == triple["observed"] == triple["requested"]


def test_an_override_that_does_not_propagate_aborts_the_run(tmp_path, monkeypatch):
    """The exact incident: the caller asks for 200 edges, the config silently
    ends up at 40, and previously the run completed and recorded 200.

    Simulated by making MemoryConfig ignore the assignment, which is what a
    no-op'd patch amounts to from the runner's point of view.
    """
    from veracium import MemoryConfig

    class StubbornConfig(MemoryConfig):
        @property
        def max_subgraph_edges(self):
            return 40

        @max_subgraph_edges.setter
        def max_subgraph_edges(self, value):
            pass                     # the patch that did nothing

    monkeypatch.setattr(R, "MemoryConfig", StubbornConfig)
    with pytest.raises(ManifestError) as e:
        _run(tmp_path, max_edges=200)
    assert "max_subgraph_edges" in str(e.value)
    assert "200" in str(e.value) and "40" in str(e.value)
    # and it must fail BEFORE writing hypotheses, not after paying for them
    assert not list(tmp_path.glob("hypotheses_*.jsonl"))


def test_a_real_override_is_recorded_in_all_three_forms(tmp_path):
    rec = _run(tmp_path, max_edges=200)
    triple = rec["effective_config"]["max_subgraph_edges"]
    assert triple == {"requested": 200, "resolved": 200, "observed": 200}


def test_coverage_zero_is_recorded_not_dropped(tmp_path):
    """0.0 is a real setting — pure relevance — and a truthiness check would
    quietly record it as 'default'."""
    rec = _run(tmp_path, coverage=0.0)
    assert rec["effective_config"]["subgraph_coverage_share"]["observed"] == 0.0


def test_two_runs_cannot_share_a_run_id(tmp_path):
    rec = _run(tmp_path)
    m = R.RunManifest(experiment_name="x", arm_name="baseline", trust_arm="C",
                      run_id=rec["run_id"])
    with pytest.raises(ManifestError):
        m.write(tmp_path)


def test_an_aborted_run_leaves_a_visibly_incomplete_attestation(tmp_path):
    """A run that dies must not look like 'nothing happened'."""
    class Dying(FakeProvider):
        def __call__(self, prompt, **kw):
            raise R.UnclassifiedProviderError("something new")

    with pytest.raises(R.UnclassifiedProviderError):
        R.run(_items(), provider=Dying(), out_dir=tmp_path, cache_enabled=False,
              data_path=tmp_path / "nope.json")
    att = json.loads(next(tmp_path.glob("attestation_*.json")).read_text())
    assert att["execution_status"] in ("failed", "partial")
    assert att["validity_status"] == "invalidated"
    assert "UnclassifiedProviderError" in att["invalidation_reason"]
