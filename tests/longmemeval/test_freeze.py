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
        "environment": "extractor gpt-4.1-mini; answerer gpt-4.1; judge gpt-4o",
        "max_achievable": "10/12 items have baseline headroom",
        "tail_guardrail": "no item with baseline >=0.8 may lose more than 0.2",
        "replicate_rationale": "3 replicates absorb extractor sampling variance",
    }
    for k in omit:
        lines.pop(k, None)
    body = "\n".join(f"{k}: {v}" for k, v in lines.items())
    body += f"\nitem_set_hash: {item_hash}\n"
    # arm_config is a structured block, not a prose line — the whole point of
    # the cross-check is that the intervention is machine-comparable against
    # what the run observed.
    if "arm_config" not in omit:
        body += ("arm_config:\n"
                 "  baseline: {subgraph_coverage_share: 0.0, max_subgraph_edges: 40}\n"
                 "  treatment: {subgraph_coverage_share: 0.25, max_subgraph_edges: 40}\n")
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
                                   "stop_rules", "approved_by", "arm_config"])
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


def test_a_freeze_without_the_treatment_configuration_is_not_confirmatory():
    """The gap that four freezes and two reviewers missed: everything about the
    experiment was frozen except WHAT THE TREATMENT IS. An unfrozen treatment
    strength is a free parameter — a null invites "you should have used a
    larger reserve", and picking the value later is what G3 forbids."""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    f = _freeze(tmp, omit=("arm_config",))
    v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
               item_ids=ITEMS)
    assert not v.confirmatory
    assert "arm_config" in " ".join(v.problems)


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


# --- the cross-check: frozen INTENT vs observed ACTUAL ----------------------

def _with_arms(tmp_path, treatment="0.25", name="armed.md"):
    p = _freeze(tmp_path, name=name)
    if treatment != "0.25":
        p.write_text(p.read_text().replace(
            "subgraph_coverage_share: 0.25", f"subgraph_coverage_share: {treatment}"))
    return p


def test_arm_config_is_parsed_per_arm(tmp_path):
    from freeze import parse_arm_config
    arms = parse_arm_config(_with_arms(tmp_path).read_text())
    assert arms["baseline"]["subgraph_coverage_share"] == "0.0"
    assert arms["treatment"]["subgraph_coverage_share"] == "0.25"
    assert arms["treatment"]["max_subgraph_edges"] == "40"


def test_a_run_matching_its_freeze_has_no_conflicts(tmp_path):
    from freeze import config_conflicts, parse_arm_config
    arms = parse_arm_config(_with_arms(tmp_path).read_text())
    assert config_conflicts(arms["treatment"],
                            {"subgraph_coverage_share": 0.25,
                             "max_subgraph_edges": 40}, arm="treatment") == []


def test_a_run_contradicting_its_freeze_is_caught(tmp_path):
    """The failure this exists for: the freeze says 0.25, the run does 0.0 —
    i.e. it executes the BASELINE while claiming the treatment protocol."""
    from freeze import config_conflicts, parse_arm_config
    arms = parse_arm_config(_with_arms(tmp_path).read_text())
    c = config_conflicts(arms["treatment"],
                         {"subgraph_coverage_share": 0.0,
                          "max_subgraph_edges": 40}, arm="treatment")
    assert c and "freeze declares '0.25'" in c[0] and "observed 0.0" in c[0]


def test_default_is_not_a_value(tmp_path):
    """'0.4.2 behaviour' silently means something else after 0.5.0."""
    from freeze import config_conflicts
    c = config_conflicts({"subgraph_coverage_share": "default"},
                         {"subgraph_coverage_share": 0.0}, arm="treatment")
    assert c and "is not a value" in c[0]


def test_unparseable_arm_config_is_a_problem_not_a_skip(tmp_path):
    """A declaration that cannot be read is worse than an absent one: it reads
    as frozen."""
    p = _freeze(tmp_path, name="bad.md")
    body = p.read_text().split("arm_config:")[0] + "arm_config:\n\nnext_field: x\n"
    p.write_text(body)
    v = verify(p, freeze_id=sha256_file(p), run_started_at=RUN_START,
               item_ids=ITEMS)
    assert not v.confirmatory
    assert "unparseable" in " ".join(v.problems)


def test_environment_is_advisory_not_required():
    """Model pins and code version: a protocol frozen against unspecified code
    is not frozen, and zero of the five real freezes pin a model.

    But this is a DEV PROPOSAL that research has not adopted into the spec's
    required table. The verifier enforces the agreed spec — a rule one session
    invented an hour ago must not silently veto the other session's artifact.
    So it reports and does not block, until the spec adopts it.
    """
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    f = _freeze(tmp, omit=("environment",))
    v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
               item_ids=ITEMS)
    assert v.confirmatory, v.problems
    assert any("environment" in a for a in v.advisories)


def test_nested_arm_config_parses_like_the_real_artifact(tmp_path):
    """The real freeze writes arms as nested YAML, not inline braces. v1 of the
    parser handled only the inline form and returned
    {"treatment_primary": {"name": ...}} — it read the first sub-key and
    reported success. A parser that half-succeeds is worse than one that
    fails, because the cross-check then compares against nothing."""
    from freeze import parse_arm_config
    text = ("arm_config:\n"
            "  baseline:\n"
            "    subgraph_coverage_share: 0.0        # the shipped default\n"
            "    max_subgraph_edges: 40\n"
            "  treatment_primary:\n"
            "    name: mmr-coverage-on\n"
            "    subgraph_coverage_share: 0.25\n"
            "    max_subgraph_edges: 40\n"
            "\n  rationale_for_0_25: >\n"
            "    prose that is not an arm\n"
            "\nnext_top_level: x\n")
    arms = parse_arm_config(text)
    assert arms["baseline"]["subgraph_coverage_share"] == "0.0"
    assert arms["baseline"]["max_subgraph_edges"] == "40"
    assert arms["treatment_primary"]["subgraph_coverage_share"] == "0.25"
    assert "rationale_for_0_25" not in arms, "prose block captured as an arm"



# --- the three fields R2 earned -------------------------------------------

@pytest.mark.parametrize("field", ["max_achievable", "tail_guardrail",
                                   "replicate_rationale"])
def test_the_three_fields_r2_earned_are_required(tmp_path, field):
    f = _freeze(tmp_path, omit=(field,))
    v = verify(f, freeze_id=sha256_file(f), run_started_at=RUN_START,
               item_ids=ITEMS)
    assert not v.confirmatory
    assert field in " ".join(v.problems)


def test_an_unreachable_threshold_is_refused():
    """**R2's exact failure.** It froze "≥10/12 improve" against a sample where
    7 of 12 were already at a perfect score — max achievable 5/12, so
    P(confirm) = 0 before a single paid call. Six freezes and two reviewers
    walked past it. This makes it arithmetic instead of attention."""
    from freeze import reachability_problem
    bad = "max_achievable: 5/12 items have headroom\nminimum_improvement: 10/12 must improve\n"
    p = reachability_problem(bad)
    assert p and "UNREACHABLE" in p and "P(confirm) = 0" in p


def test_a_reachable_threshold_passes():
    from freeze import reachability_problem
    ok = "max_achievable: 12/12 items have headroom\nminimum_improvement: 10/12 must improve\n"
    assert reachability_problem(ok) is None


def test_reachability_is_silent_when_not_both_numeric():
    """Not every experiment states these as counts; the check must not invent a
    problem it cannot actually evaluate — the mistake that made 'fails closed on
    a recognised subject' unbuildable."""
    from freeze import reachability_problem
    assert reachability_problem("max_achievable: most items have headroom\n") is None


def test_r2s_own_freeze_would_now_be_refused():
    """The regression test that matters: the artifact we actually approved."""
    from freeze import reachability_problem
    assert reachability_problem(
        "max_achievable: 5/12\nthreshold: 10/12 improve\n") is not None
