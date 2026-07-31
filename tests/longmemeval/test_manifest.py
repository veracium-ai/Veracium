"""Tests for the run-manifest layer (benchmark policy G14-G17).

Each test names the incident it exists to prevent. A compliance mechanism whose
tests are generic is one nobody can tell has regressed.

    PYTHONPATH=src python -m pytest tests/longmemeval/test_manifest.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from manifest import (CompletionAttestation, EffectiveConfig, ManifestError,
                      Parameter, RunManifest, canonical_hash,
                      check_manifest_self_consistency, decision_eligibility,
                      eligibility_for_output, git_state, sha256_file)
from providers import (ACCOUNT_OR_QUOTA_FAILURE, DATA_OR_SCHEMA_FAILURE,
                       PERMANENT_REQUEST_FAILURE, TRANSIENT_RETRYABLE,
                       UNKNOWN_FAIL_CLOSED, classify_provider_error)


def _manifest(**kw):
    base = dict(experiment_name="test", arm_name="baseline", trust_arm="C",
                source={"commit": "abc123", "dirty": False},
                expected_item_ids=["q1", "q2"], expected_output_count=2)
    base.update(kw)
    return RunManifest(**base)


# --- G15: the effective-configuration triple -------------------------------

def test_requested_and_resolved_disagreeing_stops_the_run():
    """The retrieval-breadth ablation: requested 200, ran at 40, and the record
    asserted 200 for hours. A patch that silently does nothing must not be able
    to produce a record that looks deliberate."""
    cfg = EffectiveConfig(max_subgraph_edges=200)
    cfg.resolve(max_subgraph_edges=40)          # patch no-op'd
    with pytest.raises(ManifestError) as e:
        cfg.assert_consistent(stage="config construction")
    assert "max_subgraph_edges" in str(e.value)
    assert "200" in str(e.value) and "40" in str(e.value)


def test_construction_can_be_right_while_propagation_is_wrong():
    """Two enforcement points exist because they catch different bugs: the
    config object can hold the right value and the running code still not see
    it."""
    cfg = EffectiveConfig(max_subgraph_edges=200)
    cfg.resolve(max_subgraph_edges=200)
    cfg.assert_consistent(stage="config construction")   # passes
    cfg.observe(max_subgraph_edges=40)
    with pytest.raises(ManifestError):
        cfg.assert_consistent(stage="first processed item")


def test_agreement_across_all_three_is_clean():
    cfg = EffectiveConfig(max_subgraph_edges=40, coverage=0.0)
    cfg.resolve(max_subgraph_edges=40, coverage=0.0)
    cfg.observe(max_subgraph_edges=40, coverage=0.0)
    cfg.assert_consistent(stage="first processed item")
    assert cfg.disagreements() == {}


def test_zero_and_false_are_not_treated_as_missing():
    """coverage=0.0 is a real, meaningful setting (pure relevance). A truthiness
    check here would silently skip verifying the parameter we most recently
    shipped."""
    p = Parameter(requested=0.0, resolved=0.0, observed=0.0)
    assert p.agrees()
    bad = Parameter(requested=0.0, resolved=0.5)
    assert not bad.agrees()


# --- G14: immutable manifest ------------------------------------------------

def test_manifest_is_write_once(tmp_path):
    m = _manifest()
    m.write(tmp_path)
    with pytest.raises(ManifestError) as e:
        m.write(tmp_path)
    assert "written once" in str(e.value)


def test_edited_manifest_fails_its_own_hash(tmp_path):
    m = _manifest()
    m.write(tmp_path)
    p = m.path(tmp_path)
    body = json.loads(p.read_text())
    body["note"] = "adjusted after the fact"
    p.write_text(json.dumps(body))
    with pytest.raises(ManifestError) as e:
        check_manifest_self_consistency(m, tmp_path)
    assert "does not recompute" in str(e.value)


def test_unresolved_commit_is_a_precondition_failure(tmp_path):
    """No commit means 'same code state' can never be checked afterwards —
    which is exactly why the 3.3pp matched-pair claim was unprovable."""
    m = _manifest(source={"commit": "unknown", "dirty": False})
    m.write(tmp_path)
    with pytest.raises(ManifestError) as e:
        check_manifest_self_consistency(m, tmp_path)
    assert "commit unresolved" in str(e.value)


def test_item_count_must_match_the_item_set(tmp_path):
    m = _manifest(expected_output_count=44)
    m.write(tmp_path)
    with pytest.raises(ManifestError) as e:
        check_manifest_self_consistency(m, tmp_path)
    assert "expected_output_count" in str(e.value)


def test_duplicate_item_ids_are_rejected(tmp_path):
    m = _manifest(expected_item_ids=["q1", "q1"], expected_output_count=2)
    m.write(tmp_path)
    with pytest.raises(ManifestError) as e:
        check_manifest_self_consistency(m, tmp_path)
    assert "duplicates" in str(e.value)


def test_a_clean_manifest_passes(tmp_path):
    m = _manifest()
    m.write(tmp_path)
    assert check_manifest_self_consistency(m, tmp_path)["checked"]


def test_git_state_resolves_rather_than_remembers():
    st = git_state()
    assert st["commit"] != "unknown" and len(st["commit"]) == 40
    assert "dirty" in st and "dirty_fingerprint" in st


# --- G16: execution status vs validity status -------------------------------

def _attest(tmp_path, m, hyp, **kw):
    body = dict(run_id=m.run_id, manifest_hash=m.hash(),
                execution_status="completed", validity_status="valid",
                items_expected=2, items_succeeded=2,
                output_hashes={str(hyp): sha256_file(hyp)})
    body.update(kw)
    return CompletionAttestation(**body)


def _eligible(tmp_path, **kw):
    hyp = tmp_path / "hypotheses.jsonl"
    hyp.write_text('{"question_id": "q1"}\n')
    m = _manifest(freeze_artifact_id="freeze_001")
    m.write(tmp_path)
    return m, _attest(tmp_path, m, hyp, **kw), hyp


def test_a_complete_valid_frozen_run_is_decision_eligible(tmp_path):
    m, att, _ = _eligible(tmp_path)
    ok, detail = decision_eligibility(m, att, out_dir=tmp_path)
    assert ok, detail["why_not"]


def test_a_run_that_executed_perfectly_can_still_be_invalidated(tmp_path):
    """The no-op ablation. Execution status alone cannot express this, which is
    why validity is a second axis determined later."""
    m, att, _ = _eligible(tmp_path, validity_status="invalidated",
                          invalidation_reason="effective configuration mismatch")
    ok, detail = decision_eligibility(m, att, out_dir=tmp_path)
    assert not ok
    assert "effective configuration mismatch" in detail["why_not"]["validity_valid"]


def test_partial_runs_are_not_decision_eligible(tmp_path):
    m, att, _ = _eligible(tmp_path, execution_status="partial", items_succeeded=1,
                          items_failed=1)
    ok, _ = decision_eligibility(m, att, out_dir=tmp_path)
    assert not ok


def test_an_unfrozen_run_is_exploratory_not_confirmatory(tmp_path):
    """G3/G19: exploratory use of a run is legitimate; using one as an
    acceptance criterion without a frozen protocol is not."""
    hyp = tmp_path / "h.jsonl"
    hyp.write_text("{}\n")
    m = _manifest()                       # no freeze_artifact_id
    m.write(tmp_path)
    ok, detail = decision_eligibility(m, _attest(tmp_path, m, hyp), out_dir=tmp_path)
    assert not ok
    assert "exploratory" in detail["why_not"]["freeze_artifact_referenced"]


def test_editing_the_hypothesis_file_breaks_the_attestation(tmp_path):
    m, att, hyp = _eligible(tmp_path)
    hyp.write_text('{"question_id": "q1", "hypothesis": "edited"}\n')
    ok, detail = decision_eligibility(m, att, out_dir=tmp_path)
    assert not ok
    assert "changed or missing" in detail["why_not"]["outputs_hash_match"]


def test_attestation_pointing_at_a_different_manifest_is_caught(tmp_path):
    m, att, _ = _eligible(tmp_path)
    att.manifest_hash = canonical_hash({"something": "else"})
    ok, detail = decision_eligibility(m, att, out_dir=tmp_path)
    assert not ok
    assert "different manifest" in detail["why_not"]["manifest_hash_matches"]


def test_config_disagreement_recorded_in_the_manifest_blocks_eligibility(tmp_path):
    hyp = tmp_path / "h.jsonl"
    hyp.write_text("{}\n")
    cfg = EffectiveConfig(max_subgraph_edges=200)
    cfg.resolve(max_subgraph_edges=40)
    m = _manifest(freeze_artifact_id="f1", effective_config=cfg.as_dict())
    m.write(tmp_path)
    ok, detail = decision_eligibility(m, _attest(tmp_path, m, hyp), out_dir=tmp_path)
    assert not ok
    assert "max_subgraph_edges" in detail["why_not"]["effective_config_verified"]


def test_status_values_are_constrained():
    with pytest.raises(ValueError):
        CompletionAttestation(run_id="r", manifest_hash="h", execution_status="done")
    with pytest.raises(ValueError):
        CompletionAttestation(run_id="r", manifest_hash="h",
                              execution_status="completed", validity_status="fine")


def test_unattested_output_is_reported_as_unknown_not_as_ineligible(tmp_path):
    """Runs predating the manifest are not ineligible, they are unattested. The
    report must not resolve that either way on its own."""
    (tmp_path / "hypotheses_old.jsonl").write_text("{}\n")
    assert eligibility_for_output(tmp_path / "hypotheses_old.jsonl", tmp_path) is None


def test_eligibility_links_by_content_not_by_filename(tmp_path):
    m, att, hyp = _eligible(tmp_path)
    att.write(tmp_path)
    found = eligibility_for_output(hyp, tmp_path)
    assert found is not None and found[0] is True
    # a same-named file in another directory must not inherit the attestation
    other = tmp_path / "elsewhere"
    other.mkdir()
    (other / hyp.name).write_text(hyp.read_text())
    assert eligibility_for_output(other / hyp.name, other) is None


# --- G17: unknown errors fail closed ---------------------------------------

class _Err(Exception):
    pass


class RateLimitError(Exception):
    pass


class APIConnectionError(Exception):
    pass


class BadRequestError(Exception):
    pass


@pytest.mark.parametrize("exc,expected", [
    (RateLimitError("Rate limit reached for gpt-4.1"), TRANSIENT_RETRYABLE),
    (APIConnectionError("connection reset by peer"), TRANSIENT_RETRYABLE),
    # the incident: quota arrives dressed as a 429 and is terminal
    (RateLimitError("You exceeded your current quota, please check your plan"),
     ACCOUNT_OR_QUOTA_FAILURE),
    (_Err("insufficient_quota"), ACCOUNT_OR_QUOTA_FAILURE),
    (BadRequestError("Unknown parameter: 'foo'"), PERMANENT_REQUEST_FAILURE),
    (_Err("Invalid json_schema for response_format"), DATA_OR_SCHEMA_FAILURE),
    (_Err("something nobody has seen before"), UNKNOWN_FAIL_CLOSED),
])
def test_error_classification(exc, expected):
    assert classify_provider_error(exc) == expected


def test_quota_is_never_classified_as_retryable():
    """Retrying this produced a full set of empty hypotheses that looked like a
    completed run — the failure mode the whole attestation layer exists for."""
    for msg in ("You exceeded your current quota",
                "insufficient_quota: billing hard limit reached",
                "Your account is not active"):
        assert classify_provider_error(RateLimitError(msg)) == ACCOUNT_OR_QUOTA_FAILURE
