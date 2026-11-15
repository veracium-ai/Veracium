"""specs/0042 v12.18: specs/evidence/0042/retired_overrides.py — a plan-time OVERRIDE whose statement a code change
removed is dropped only by a DECLARED, CHECKED retirement; override_at_plan.py stays never-rewritten. Its mutation
matrix: the real retirement passes in its retiring generation and in the steady state; each forged retirement refuses
by name; and derive_keys with the retirement withdrawn still refuses the vanished group (the end-to-end control)."""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
E = ROOT / "specs" / "evidence" / "0042"


def _load():
    spec = importlib.util.spec_from_file_location("veracium_0042_retired_overrides", E / "retired_overrides.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ro = _load()
KEY = ("__init__.py", 1750)


def _inputs():
    plan_override = next(ast.literal_eval(n.value) for n in ast.parse((E / "override_at_plan.py").read_text()).body
                         if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "OVERRIDE")
    plan_inv = json.loads((E / "inventory_at_plan.json").read_text())["sites"]
    target_inv = json.loads((E / "decision_site_inventory_OUTPUT.json").read_text())["sites"]
    entry = ro.RETIRED_OVERRIDES[KEY]
    retiring = {"x": {"key": ":".join(entry["group"]) + ":1", "statement": entry["statement"]}}
    # where each declared site is fired, from the committed generation's reviewed points (module:qualname:kind:n)
    fired_in = {}
    for row in json.loads((E / "reviewed_points.json").read_text()).values():
        if row.get("site"):
            mod, qual = row["key"].split(":")[:2]
            fired_in.setdefault(row["site"], set()).add((mod, qual))
    return plan_override, plan_inv, target_inv, retiring, fired_in


@pytest.mark.parametrize("generation", ["retiring", "steady"])
def test_the_real_retirement_holds(generation):
    plan_override, plan_inv, target_inv, retiring, declared = _inputs()
    prev = retiring if generation == "retiring" else {}
    assert ro.check(ro.RETIRED_OVERRIDES, plan_override, plan_inv, target_inv, prev, declared) == {KEY}


def _forge(name):
    retired = copy.deepcopy(ro.RETIRED_OVERRIDES)
    plan_override, plan_inv, target_inv, prev, declared = _inputs()
    e = retired[KEY]
    if name == "a key the literal does not hold":
        retired[("__init__.py", 999999)] = retired.pop(KEY)
    elif name == "another class":
        e["class"] = "internal-invariant"
    elif name == "another group":
        e["group"] = ("__init__.py", "Memory.list_entities", "FILTER_RETURN")
    elif name == "a group that still exists (stale)":
        target_inv = target_inv + [{"module": "__init__.py", "qualname": "Memory.edges_since", "kind": "FILTER_RETURN",
                                    "line": 1}]
    elif name == "a different statement quoted":
        e["statement"] = "return []"
    elif name == "a different statement recorded":
        prev = {"x": {"key": ":".join(e["group"]) + ":1", "statement": "return [x for x in other]"}}
    elif name == "a replacement that is not declared":
        e["replaced_by"] = ("memory.edges-since.no-journal", "no.such.site")
    elif name == "an unrelated declared site (SF2)":
        e["replaced_by"] = ("memory.edges-since.no-journal", "memory.feedback.attested-target")
    elif name == "no replacement named":
        e["replaced_by"] = ()
    elif name == "none, with no reason":
        e["replaced_by"], e["reason"] = "none", ""
    return retired, plan_override, plan_inv, target_inv, prev, declared


FORGED = {
    "a key the literal does not hold": "no such entry",
    "another class": "the literal says",
    "another group": "the plan-time inventory places",
    "a group that still exists (stale)": "STALE",
    "a different statement quoted": "the previous generation recorded",
    "a different statement recorded": "the previous generation recorded",
    "a replacement that is not declared": "not declared",
    "an unrelated declared site (SF2)": "are not fired in",
    "no replacement named": "not declared",
    "none, with no reason": "no reason",
}


def test_each_forged_retirement_refuses_by_name():
    for name, want in FORGED.items():
        with pytest.raises(ro.RetirementRefused, match=want):
            ro.check(*_forge(name))
    # the control beside the forgeries: "none" WITH a reason is a valid retirement
    retired = copy.deepcopy(ro.RETIRED_OVERRIDES)
    retired[KEY]["replaced_by"] = "none"
    assert ro.check(retired, *_inputs()) == {KEY}


def test_derive_keys_without_the_retirement_still_refuses_the_vanished_group(tmp_path):
    """The end-to-end control: the same derive_keys over a copy of specs/evidence/0042 whose retired_overrides.py
    declares nothing refuses, so the drop is the declaration's doing and nothing else's."""
    copy_dir = tmp_path / "0042"
    shutil.copytree(E, copy_dir, ignore=shutil.ignore_patterns("__pycache__"))
    p = copy_dir / "retired_overrides.py"
    text = p.read_text()
    start = text.index("RETIRED_OVERRIDES = {")
    end = text.index("\n}\n", start) + 3
    p.write_text(text[:start] + "RETIRED_OVERRIDES = {}\n" + text[end:])
    out = tmp_path / "review.py"
    r = subprocess.run([sys.executable, "-B", str(copy_dir / "derive_keys.py"), str(ROOT / "src" / "veracium"),
                        str(E / "decision_site_inventory_OUTPUT.json"), str(E / "semantic_review.py"), str(out),
                        str(E / "reviewed_points.json")], capture_output=True, text=True)
    # the committed reviewed points are a LATER generation (they record nothing for the vanished group), so the
    # refusal is the plan-time hop's: the group has no candidate to land on
    assert r.returncode != 0 and "Memory.edges_since" in r.stderr, r.stdout[-500:] + r.stderr[-1500:]
    assert not out.exists()
