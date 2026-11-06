"""0018 adjacent rungs, T1: the kernel as one table. The refactor's own proof is specs/evidence/0018/rungs/t1_differential.py over
every fixture; these cells hold the table's shape, the plan it derives, and the census's fail-closed half."""
from __future__ import annotations

import functools
import hashlib
import importlib.util
import inspect
import json
import pathlib
import shutil
import subprocess
import sys

import pytest

import veracium.store.migration as M
from veracium.store import schema_version as sv

ROOT = pathlib.Path(__file__).resolve().parent.parent
CENSUS = ROOT / "specs/evidence/0018/head_bound_census.py"
FROZEN = ROOT / "specs/evidence/0018/rungs/superseded/migration_at_branch.py"
BASES = sorted(sv.SCHEMAS)
HEAD = sv.SCHEMA_VERSION
_S = "def _step_x(conn):\n    return SCHEMA_VERSION\n\n\n"


def _kinds(entries):
    return [e.kind for e in entries]


def test_the_frozen_body_is_the_branch_point_s():
    """The superseded body is read from this file, never from git at run time; the digest binds the copy."""
    assert hashlib.sha256(FROZEN.read_bytes()).hexdigest()[:16] == "be5542418a560310"


def test_the_table_holds_every_kind_the_spec_declares_and_no_other():
    assert set(_kinds(M.FORWARD_ENTRIES)) == {"read", "data", "check", "alter"}
    assert len(M.FORWARD_ENTRIES) == 78


@pytest.mark.parametrize("tuple_, lo, v", [(sv.ALTERS_V5_TO_V6, 4, 6), (sv.ALTERS_V7_TO_V8, 6, 8), (sv.ALTERS_V9_TO_V10, 4, 10),
                                           (sv.ALTERS_V15_TO_V16, 2, 16), (sv.ALTERS_V15_TO_V16_REDACTIONS, 15, 16)],
                         ids=["v6", "v8", "v10", "v16-confirmations", "v16-redactions"])
def test_each_alter_tuple_is_unrolled_with_its_guard(tuple_, lo, v):
    assert [e.step for e in M.FORWARD_ENTRIES if e.kind == "alter" and (e.lo, e.v) == (lo, v)] == list(tuple_)


@pytest.mark.parametrize("base", [b for b in BASES if b < HEAD])
def test_a_plan_starts_at_the_clock_and_ends_at_the_stamp(base):
    p = M.plan(base, HEAD)
    assert _kinds(p).count("clock") == 1 and p[0].kind == "clock"
    assert [e.step for e in p if e.kind == "stamp"] == [HEAD]
    assert _kinds(p)[-3:] == ["stamp", "read", "check"] and p[-1].step is M._check_stamp


@pytest.mark.parametrize("base", [b for b in BASES if b < HEAD])
def test_a_plan_adds_what_the_target_has_and_the_base_lacks_in_the_target_s_order(base):
    have = {o.key for o in sv.SCHEMAS[base]}
    assert [e.step for e in M.plan(base, HEAD) if e.kind == "add"] == [o for o in sv.SCHEMAS[HEAD] if o.key not in have]


@pytest.mark.parametrize("base", [b for b in BASES if b < HEAD])
def test_a_plan_is_exactly_the_guarded_entries_in_table_order(base):
    kept = [e for e in M.plan(base, HEAD) if e.kind not in ("clock", "add", "stamp")][:-2]
    assert kept == [e for e in M.FORWARD_ENTRIES if e.lo <= base < e.v <= HEAD]


def test_a_step_is_named_and_takes_the_connection_by_that_name():
    """Two cells read `f_locals["conn"]` from a step's frame, so the parameter's name is load-bearing."""
    for e in M.FORWARD_ENTRIES:
        if e.kind != "alter":
            assert inspect.isfunction(e.step) and e.step.__name__ != "<lambda>", e
            assert list(inspect.signature(e.step).parameters) == ["conn", "run"], e


def test_site_coverage_reads_every_step_the_table_runs():
    """SA10 reads coverage in a function it saw issue a call, so a step that normally issues none would hide a dead write. Each
    step is a root, whether or not it ran. `tree-unreached-write` in sa10_mutants.py is this cell's mutant."""
    spec = importlib.util.spec_from_file_location("veracium_sa10_gate_t1", ROOT / "specs/evidence/0013/sa10_gate.py")
    g = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = g
    spec.loader.exec_module(g)
    roots = g.table_steps()
    named = {n for _r, n, _l in roots}
    assert {e.step.__name__ for e in M.FORWARD_ENTRIES if e.kind != "alter"} | {"_read_stamped", "_check_stamp"} == named
    cov = g.site_coverage([], roots)
    assert cov["functions"] == len(roots) and any(":_data_registry:" in u for u in cov["unobserved"])


# ---- the census's fail-closed half: the callables the table really holds, against what the census reached -------------------

def _reached(tree):
    r = subprocess.run([sys.executable, "-I", str(CENSUS), str(tree), "--json"], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-300:]
    return set(json.loads(r.stdout)["reached"])


def _callable_of(entry):
    step = entry[-1]
    while isinstance(step, functools.partial):
        step = step.func
    return getattr(step, "__func__", step)


def _unreached(entries, module, reached):
    """Every table callable the census did not reach, by its `<module>:<qualname>`; a lambda has no name to reach, so it refuses."""
    out = []
    for e in entries:
        f = _callable_of(e)
        if not callable(f):
            continue
        if f.__name__ == "<lambda>":
            out.append("a lambda")
        elif f"{module}:{f.__qualname__}" not in reached:
            out.append(f"{module}:{f.__qualname__}")
    return out


def test_every_callable_the_table_holds_is_in_the_census_s_reach():
    assert _unreached(M.FORWARD_ENTRIES, "veracium.store.migration", _reached(ROOT)) == []


@pytest.mark.parametrize("plant", [
    _S + "FORWARD_ENTRIES = []\nFORWARD_ENTRIES.append(('p', _step_x))\n",
    _S + "FORWARD_ENTRIES = []\nFORWARD_ENTRIES.extend([('p', _step_x)])\n",
    "FORWARD_ENTRIES = []\n\n\ndef _entry(f):\n    FORWARD_ENTRIES.append(('p', f))\n    return f\n\n\n@_entry\n" + _S,
    _S + "_A, _B = (), (('p', _step_x),)\nFORWARD_ENTRIES = _A + _B\n",
    _S + "_FNS = (_step_x,)\nFORWARD_ENTRIES = tuple(('p', f) for f in _FNS)\n",
    "class _Steps:\n    def run(self, conn):\n        return SCHEMA_VERSION\n\n\n_S = _Steps()\nFORWARD_ENTRIES = (('p', _S.run),)\n",
], ids=["append", "extend", "a decorator", "unpacking", "a comprehension", "an instance's method"])
def test_a_table_shape_the_ast_misses_fails_on_the_callables_it_really_holds(plant, tmp_path):
    """Research's six AST-invisible shapes (read-c, plants2.py): the static census may miss them; the runtime comparison may not.
    A control beside them: the plain tuple, reached, reads clean."""
    tree = tmp_path / "t"
    shutil.copytree(ROOT / "src", tree / "src", ignore=shutil.ignore_patterns("__pycache__"))
    mig = tree / "src/veracium/store/migration.py"
    mig.write_text(mig.read_text() + "\n" + plant)
    ns = {"SCHEMA_VERSION": HEAD}
    exec(compile(plant, "<plant>", "exec"), ns)
    assert _unreached(ns["FORWARD_ENTRIES"], "veracium.store.migration", _reached(tree)) != [] or "SCHEMA_VERSION" in _census_diff(tree), plant


def _census_diff(tree):
    r = subprocess.run([sys.executable, "-I", str(CENSUS), str(tree), "--check", str(ROOT / "specs/evidence/0018/head_bound_census.expected.json")],
                       capture_output=True, text=True, timeout=120)
    return "SCHEMA_VERSION" if r.returncode == 1 else ""


def test_the_plain_tuple_is_the_control():
    ns = {"SCHEMA_VERSION": HEAD}
    exec(compile(_S + "FORWARD_ENTRIES = (('p', _step_x),)\n", "<plant>", "exec"), ns)
    assert _unreached(ns["FORWARD_ENTRIES"], "m", {"m:_step_x"}) == []


def test_a_lambda_refuses_as_an_entry_and_a_partial_is_unwrapped():
    def step(conn, run):
        return None
    assert _unreached([("p", lambda c, r: None)], "m", set()) == ["a lambda"]
    assert _unreached([("p", functools.partial(step, 1))], "m", {f"m:{step.__qualname__}"}) == []
