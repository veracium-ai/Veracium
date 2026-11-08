#!/usr/bin/env python3
"""The consolidated code-mutant campaign the obligation map cites (T12, addendum 1's M1 and P8): every tranche's
definitions (`defs.py`, generated with each source's digest), re-run at ONE pin on a git-less export, each kill
CLASSIFIED by the shared rule (specs/evidence/mutation_kinds.py: KILLED iff >=1 cell fails with `assertion` or
`expected-refusal-missing`, none fails otherwise and none errors). The runner is R-A's (`ra_mutants.py`) with three
additions: the PIN DIGEST of every file the cells and mutants read is recorded (and re-read after the last mutant: the
tree must be restored byte-identically); each row records the DIGEST of the definition it ran (obligation_map.py refuses
a row whose definition has since changed); groups can be SHARDED; and `merge` joins shards, refusing two pins.

    python run_campaign.py run <export-root> <out.json> [--shard I/N]
    python run_campaign.py merge <result.json> <shard.json>...

The export must be a `git archive` of the pin (plus, before the commit, the working tree's changed files). Each group
runs its CONTROL (the unmutated cells, all passing) before and after its mutants; each mutant's anchor must occur
EXACTLY ONCE in its file (P8: a stale anchor is an ANCHOR row and the run exits 1, never a silent skip), and the file is
restored byte-identically before the next. Every run imports veracium from THE EXPORT (PYTHONPATH, asserted).

    python run_campaign.py run <export-root> <out.json> --shard I/N --weights <earlier result.json>

PACKING (the owner's ruling of 2026-11-07, step 2): without `--weights` group k goes to shard k mod N. With it, each
group's measured `seconds` from an earlier merged result weighs it, and `assign` packs longest first onto the least
loaded shard (ties by definition order, then shard index), so every one of the N processes derives the same plan. A
group the weights do not name (added since) weighs as the heaviest named one. Weights move only WHERE a group runs,
never what it runs or how it is judged. Each shard records the whole plan's digest and the full group list, and `merge`
refuses unless every group ran exactly once, in the shard the plan put it in, under one plan.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent


def _strict_pairs(pairs):
    """0026's evidence-boundary rule: a duplicate key is a REFUSAL, never last-wins."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r}")
        out[k] = v
    return out


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _om(root):
    om = _load(root / "specs" / "evidence" / "0044" / "obligation_map.py", "obligation_map_pin")
    om.ROOT = root
    return om


def _weights(path) -> dict:
    """{group label: seconds} from an earlier MERGED result; a label twice is a refusal, never last-wins."""
    data = json.loads(pathlib.Path(path).read_text(), object_pairs_hook=_strict_pairs)
    out = {}
    for g in data["groups"]:
        assert g["group"] not in out, f"the weights name group {g['group']!r} twice"
        assert isinstance(g.get("seconds"), (int, float)) and g["seconds"] >= 0, f"no measured seconds for {g['group']!r}"
        out[g["group"]] = float(g["seconds"])
    assert out, "the weights file names no groups"
    return out


def assign(labels, n, weights=None) -> list:
    """The plan: for each of the N shards, the definition indices it runs, in definition order. Pure and deterministic,
    so every shard process computes the same one. Every index lands in exactly one shard (asserted)."""
    assert n >= 1 and len(set(labels)) == len(labels), "group labels must be unique, and N at least 1"
    if weights is None:
        plan = [[k for k in range(len(labels)) if k % n == i] for i in range(n)]
    else:
        heaviest = max(weights.values())
        w = [weights.get(lab, heaviest) for lab in labels]
        load, plan = [0.0] * n, [[] for _ in range(n)]
        for k in sorted(range(len(labels)), key=lambda k: (-w[k], k)):
            i = min(range(n), key=lambda i: (load[i], i))
            plan[i].append(k)
            load[i] += w[k]
        plan = [sorted(p) for p in plan]
    assert sorted(k for p in plan for k in p) == list(range(len(labels))), "the plan must run every group exactly once"
    return plan


def plan_digest(labels, plan) -> str:
    return hashlib.sha256(json.dumps([[labels[k] for k in p] for p in plan]).encode()).hexdigest()


def _pin(root, groups) -> str:
    om = _om(root)
    return om.tree_digest(om.pin_files(groups))


def run(root: pathlib.Path, out: pathlib.Path, shard: tuple, weights_path=None) -> int:
    assert not (root / ".git").exists(), "run this on a git-less export of the pin"
    MK = _load(root / "specs" / "evidence" / "mutation_kinds.py", "mutation_kinds_campaign")
    ALL = _load(root / "specs" / "evidence" / "0044" / "campaign" / "defs.py", "campaign_defs").GROUPS
    i, n = shard
    assert 0 <= i < n, f"shard {i}/{n}"
    labels = [g[0] for g in ALL]
    weights = _weights(weights_path) if weights_path else None
    plan = assign(labels, n, weights)
    GROUPS = [ALL[k] for k in plan[i]]
    assignment = {"method": "weight-lpt" if weights else "modulo", "n": n, "all_groups": labels,
                  "plan_digest": plan_digest(labels, plan), "planned": [labels[k] for k in plan[i]],
                  "weights_digest": hashlib.sha256(pathlib.Path(weights_path).read_bytes()).hexdigest() if weights else None,
                  "unweighted": sorted(lab for lab in labels if weights and lab not in weights)}
    pin = _pin(root, ALL)
    env = {**os.environ, "PYTHONPATH": str(root / "src"), "TMPDIR": os.environ.get("TMPDIR", "/dev/shm")}
    probe = subprocess.run([sys.executable, "-B", "-c", "import veracium, pathlib, sys; "
                            "assert pathlib.Path(veracium.__file__).resolve().is_relative_to(pathlib.Path(sys.argv[1])), "
                            "veracium.__file__", str(root / "src")], cwd=root, env=env, capture_output=True, text=True)
    assert probe.returncode == 0, probe.stderr

    def pytest(cells):
        with tempfile.TemporaryDirectory() as d:
            xml = pathlib.Path(d) / "j.xml"
            r = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:randomly", "-p", "no:cacheprovider",
                                f"--junitxml={xml}", *cells], cwd=root, env=env, capture_output=True, text=True)
            failed, errored, passed, kinds = [], [], 0, {}
            for tc in ET.parse(xml).iter("testcase"):
                node = f"{tc.get('classname', '').replace('.', '/')}.py::{tc.get('name')}"
                f = tc.find("failure")
                if f is not None:
                    failed.append(node)
                    kinds[node] = MK.failure_kind(f.get("message") or "")
                elif tc.find("error") is not None:
                    errored.append(node)
                elif tc.find("skipped") is None:
                    passed += 1
        return {"exit": r.returncode, "passed": passed, "failed": failed, "errored": errored, "kinds": kinds}

    rows, groups_out, bad = [], [], 0
    for label, cells, mutants in GROUPS:
        started = time.monotonic()           # each group's wall time, for packing shards by measured cost (owner's ruling, 2026-11-07)
        before = pytest(cells)
        g = {"group": label, "cells": cells, "control_before": {"exit": before["exit"], "passed": before["passed"]}}
        if before["exit"] != 0 or before["failed"] or before["errored"]:
            bad += 1
        for name, rel, anchor, replacement in mutants:
            p = root / rel
            orig = p.read_bytes()
            text = orig.decode()
            k = text.count(anchor)
            row = {"group": label, "mutant": name, "file": rel, "anchor_count": k,
                   "def_digest": _om(root).def_digest(label, (name, rel, anchor, replacement))}
            if k != 1:
                row.update(outcome="ANCHOR")
                bad += 1
                rows.append(row)
                continue
            p.write_text(text.replace(anchor, replacement))
            try:
                res = pytest(cells)
            finally:
                p.write_bytes(orig)
            assert p.read_bytes() == orig
            c = MK.classify(res["kinds"], res["failed"], res["errored"])
            row.update({k2: c[k2] for k2 in ("outcome", "kill_kind", "cells_failed", "cell_kinds")})
            if c["outcome"] != "KILLED":
                bad += 1
            rows.append(row)
            print(f"  {row['outcome']:12} {name[:70]:70} {row.get('kill_kind') or ''}", flush=True)   # progress
        after = pytest(cells)
        g["control_after"] = {"exit": after["exit"], "passed": after["passed"]}
        g["seconds"] = round(time.monotonic() - started, 1)   # an observation of this run, never a verdict input
        if after["exit"] != 0 or after["failed"] or after["errored"]:
            bad += 1
        groups_out.append(g)
    assert _pin(root, ALL) == pin, "the tree changed during the campaign"
    out.write_text(json.dumps({"summary": _summary(rows, groups_out), "groups": groups_out, "rows": rows,
                               "pin_digest": pin, "shard": f"{i}/{n}", "assignment": assignment},
                              indent=1, sort_keys=True) + "\n")
    print(json.dumps(_summary(rows, groups_out)))
    return 0 if bad == 0 else 1


def _summary(rows, groups) -> dict:
    return {"mutants": len(rows), "killed": sum(1 for r in rows if r.get("outcome") == "KILLED"), "groups": len(groups),
            "controls_green": all(g["control_before"]["exit"] == 0 and g["control_after"]["exit"] == 0 for g in groups),
            "kill_kinds": sorted({r["kill_kind"] for r in rows if r.get("kill_kind")})}


def merge(out: pathlib.Path, shards) -> int:
    parts = [json.loads(pathlib.Path(s).read_text(), object_pairs_hook=_strict_pairs) for s in shards]
    pins = {p["pin_digest"] for p in parts}
    assert len(pins) == 1, f"the shards ran at different pins: {sorted(pins)}"
    n = {int(p["shard"].split("/")[1]) for p in parts}
    assert len(n) == 1 and sorted(int(p["shard"].split("/")[0]) for p in parts) == list(range(n.pop())), \
        "the shards are not exactly 0..N-1 of one N"
    plans = {(p["assignment"]["plan_digest"], p["assignment"]["method"], p["assignment"]["weights_digest"],
              json.dumps(p["assignment"]["all_groups"])) for p in parts}
    assert len(plans) == 1, "the shards ran under different plans"
    a0 = parts[0]["assignment"]
    for p in parts:
        ran = [g["group"] for g in p["groups"]]
        assert ran == p["assignment"]["planned"], f"shard {p['shard']} did not run the groups its plan names"
        assert {r["group"] for r in p["rows"]} <= set(ran), f"shard {p['shard']} has a row outside its groups"
    ran = sorted(g["group"] for p in parts for g in p["groups"])
    assert ran == sorted(a0["all_groups"]), "every group must run exactly once across the shards"
    rows = [r for p in parts for r in p["rows"]]
    groups = [g for p in parts for g in p["groups"]]
    shard_seconds = [round(sum(g["seconds"] for g in p["groups"]), 1)
                     for p in sorted(parts, key=lambda p: int(p["shard"].split("/")[0]))]
    out.write_text(json.dumps({"summary": _summary(rows, groups), "groups": groups, "rows": rows,
                               "pin_digest": pins.pop(),
                               "assignment": {"method": a0["method"], "n": a0["n"], "plan_digest": a0["plan_digest"],
                                              "weights_digest": a0["weights_digest"], "unweighted": a0["unweighted"],
                                              "shard_seconds": shard_seconds}},
                              indent=1, sort_keys=True) + "\n")
    print(json.dumps(_summary(rows, groups)))
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "merge":
        sys.exit(merge(pathlib.Path(a[1]), a[2:]))
    sh = (0, 1)
    if "--shard" in a:
        s = a[a.index("--shard") + 1]
        sh = tuple(int(x) for x in s.split("/"))
    wp = a[a.index("--weights") + 1] if "--weights" in a else None
    sys.exit(run(pathlib.Path(a[1]).resolve(), pathlib.Path(a[2]), sh, wp))
