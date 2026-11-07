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
"""
from __future__ import annotations

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


def _pin(root, groups) -> str:
    om = _om(root)
    return om.tree_digest(om.pin_files(groups))


def run(root: pathlib.Path, out: pathlib.Path, shard: tuple) -> int:
    assert not (root / ".git").exists(), "run this on a git-less export of the pin"
    MK = _load(root / "specs" / "evidence" / "mutation_kinds.py", "mutation_kinds_campaign")
    ALL = _load(root / "specs" / "evidence" / "0044" / "campaign" / "defs.py", "campaign_defs").GROUPS
    i, n = shard
    GROUPS = [g for k, g in enumerate(ALL) if k % n == i]
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
                               "pin_digest": pin, "shard": f"{i}/{n}"}, indent=1, sort_keys=True) + "\n")
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
    rows = [r for p in parts for r in p["rows"]]
    groups = [g for p in parts for g in p["groups"]]
    out.write_text(json.dumps({"summary": _summary(rows, groups), "groups": groups, "rows": rows,
                               "pin_digest": pins.pop()}, indent=1, sort_keys=True) + "\n")
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
    sys.exit(run(pathlib.Path(a[1]).resolve(), pathlib.Path(a[2]), sh))
