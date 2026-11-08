"""0044's campaign runner packs shards by measured weight (the owner's ruling of 2026-11-07, step 2): `assign` must run
every group exactly once, identically in every shard process, and `merge` must refuse any shard set that did not.
The cells drive the runner's own functions; the refusals are the reviewer's mutants, written first."""
from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNNER = ROOT / "specs" / "evidence" / "0044" / "campaign" / "run_campaign.py"


def _runner():
    spec = importlib.util.spec_from_file_location("run_campaign_packing", RUNNER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


RC = _runner()
LABELS = [f"g{k}" for k in range(13)]
WEIGHTS = {f"g{k}": float(w) for k, w in enumerate([5, 90, 3, 40, 40, 7, 1, 60, 2, 33, 8, 12])}   # g12 unweighted


@pytest.mark.parametrize("n", range(1, 11))
@pytest.mark.parametrize("weighted", [False, True])
def test_every_group_lands_in_exactly_one_shard(n, weighted):
    plan = RC.assign(LABELS, n, WEIGHTS if weighted else None)
    assert len(plan) == n
    assert sorted(k for p in plan for k in p) == list(range(len(LABELS)))
    assert all(p == sorted(p) for p in plan)


@pytest.mark.parametrize("n", range(1, 14))
def test_no_shard_is_left_empty_while_groups_remain(n):
    assert all(RC.assign(LABELS, n, WEIGHTS)), "LPT puts the next group on an EMPTY shard before a loaded one"


def test_the_plan_is_the_same_in_every_process_and_order_of_the_weights():
    a = RC.assign(LABELS, 4, WEIGHTS)
    b = RC.assign(LABELS, 4, dict(reversed(list(WEIGHTS.items()))))
    assert a == b
    assert RC.plan_digest(LABELS, a) == RC.plan_digest(LABELS, b)


def test_modulo_is_the_unweighted_plan():
    assert RC.assign(LABELS, 3) == [[k for k in range(13) if k % 3 == i] for i in range(3)]


def test_longest_first_onto_the_least_loaded_shard():
    w = {"a": 10.0, "b": 9.0, "c": 6.0, "d": 4.0, "e": 1.0}
    plan = RC.assign(list("abcde"), 2, w)
    loads = sorted(sum(w["abcde"[k]] for k in p) for p in plan)
    assert loads == [15.0, 15.0]          # a+d+e / b+c, where modulo gives 17 / 13
    assert RC.assign(list("abcde"), 2) == [[0, 2, 4], [1, 3]]


def test_an_unweighted_group_weighs_as_the_heaviest_named_one():
    # "new" weighs 50, so it is placed FIRST (ties by definition order); weighed as 0 it would go last, giving [[0, 1], [2]]
    assert RC.assign(["new", "x", "y"], 2, {"x": 50.0, "y": 50.0}) == [[0, 2], [1]]


def test_labels_must_be_unique():
    with pytest.raises(AssertionError, match="unique"):
        RC.assign(["a", "a"], 2)


def test_the_weights_refuse_a_label_twice(tmp_path):
    f = tmp_path / "w.json"
    f.write_text(json.dumps({"groups": [{"group": "a", "seconds": 1}, {"group": "a", "seconds": 2}]}))
    with pytest.raises(AssertionError, match="twice"):
        RC._weights(f)


def test_the_weights_refuse_a_group_without_seconds(tmp_path):
    f = tmp_path / "w.json"
    f.write_text(json.dumps({"groups": [{"group": "a"}]}))
    with pytest.raises(AssertionError, match="no measured seconds"):
        RC._weights(f)


@pytest.mark.parametrize("seconds", [-1, "12", None])
def test_the_weights_refuse_a_seconds_that_is_not_a_measurement(tmp_path, seconds):
    f = tmp_path / "w.json"
    f.write_text(json.dumps({"groups": [{"group": "a", "seconds": seconds}]}))
    with pytest.raises(AssertionError, match="no measured seconds"):
        RC._weights(f)


def _parts(tmp_path, n=3, weights=WEIGHTS):
    """A shard set exactly as `run` writes it, one group row each."""
    plan = RC.assign(LABELS, n, weights)
    assert all(plan), f"a shard of the fixture plan is empty: {plan}"
    paths = []
    for i, p in enumerate(plan):
        planned = [LABELS[k] for k in p]
        part = {"pin_digest": "PIN", "shard": f"{i}/{n}",
                "groups": [{"group": lab, "seconds": weights.get(lab, 0.0), "control_before": {"exit": 0},
                            "control_after": {"exit": 0}} for lab in planned],
                "rows": [{"group": lab, "mutant": f"m-{lab}", "outcome": "KILLED", "kill_kind": "assertion"}
                         for lab in planned],
                "assignment": {"method": "weight-lpt", "n": n, "all_groups": LABELS,
                               "plan_digest": RC.plan_digest(LABELS, plan), "planned": planned,
                               "weights_digest": "W", "unweighted": ["g12"]}}
        f = tmp_path / f"s{i}.json"
        f.write_text(json.dumps(part))
        paths.append(f)
    return paths


def _edit(path, fn):
    d = json.loads(path.read_text())
    fn(d)
    path.write_text(json.dumps(d))


def test_merge_accepts_the_shards_its_plan_names(tmp_path):
    paths = _parts(tmp_path)
    out = tmp_path / "result.json"
    assert RC.merge(out, [str(p) for p in paths]) == 0
    r = json.loads(out.read_text())
    assert sorted(g["group"] for g in r["groups"]) == sorted(LABELS)
    assert r["assignment"]["method"] == "weight-lpt" and len(r["assignment"]["shard_seconds"]) == 3
    assert r["summary"]["mutants"] == 13 and r["summary"]["killed"] == 13


def _refused(tmp_path, paths, match):
    with pytest.raises(AssertionError, match=match):
        RC.merge(tmp_path / "result.json", [str(p) for p in paths])
    assert not (tmp_path / "result.json").exists()


def test_merge_refuses_a_group_that_never_ran(tmp_path):
    paths = _parts(tmp_path)
    def drop(d):
        d["groups"].pop()
        d["rows"].pop()
        d["assignment"]["planned"].pop()
    _edit(paths[0], drop)
    _refused(tmp_path, paths, "exactly once")


def test_merge_refuses_a_group_that_ran_twice(tmp_path):
    paths = _parts(tmp_path)
    extra = json.loads(paths[1].read_text())["groups"][0]
    def dup(d):
        d["groups"].append(extra)
        d["assignment"]["planned"].append(extra["group"])
    _edit(paths[0], dup)
    _refused(tmp_path, paths, "exactly once")


def test_merge_refuses_a_shard_that_ran_off_its_plan(tmp_path):
    paths = _parts(tmp_path)
    _edit(paths[0], lambda d: d["groups"].reverse() if len(d["groups"]) > 1 else d["groups"].clear())
    _refused(tmp_path, paths, "did not run the groups its plan names")


def test_merge_refuses_two_plans(tmp_path):
    paths = _parts(tmp_path)
    _edit(paths[2], lambda d: d["assignment"].update(plan_digest="OTHER"))
    _refused(tmp_path, paths, "different plans")


def test_merge_refuses_two_weight_files(tmp_path):
    paths = _parts(tmp_path)
    _edit(paths[1], lambda d: d["assignment"].update(weights_digest="W2"))
    _refused(tmp_path, paths, "different plans")


def test_merge_refuses_a_row_outside_its_shards_groups(tmp_path):
    paths = _parts(tmp_path)
    _edit(paths[0], lambda d: d["rows"].append({"group": "elsewhere", "mutant": "x", "outcome": "KILLED"}))
    _refused(tmp_path, paths, "row outside its groups")


def test_merge_refuses_a_missing_shard(tmp_path):
    paths = _parts(tmp_path)
    _refused(tmp_path, paths[:2], "not exactly 0..N-1")


def test_merge_refuses_two_pins(tmp_path):
    paths = _parts(tmp_path)
    _edit(paths[1], lambda d: d.update(pin_digest="PIN2"))
    _refused(tmp_path, paths, "different pins")
