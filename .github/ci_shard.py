"""CI lane split: run one share of the suite in this process.

Loaded by the tests workflow as `-p ci_shard` with `.github` on PYTHONPATH and VERACIUM_CI_SHARD=<k>/<n>. Absent that
variable it does nothing, so a local run is unchanged.

Every shard COLLECTS THE WHOLE SUITE and deselects what is not its share, so collection-level guards (the 0042 runtime
leg's collection guard reads pytest_deselected) see a module either whole or not at all, never in part. The unit of
assignment is a test module, except that the seam-model files form ONE unit: their gate refuses under xdist and expects
to run in one process together (the rule suite-2phase.sh uses to find them). Units are packed by weight
(.github/ci-shard-durations.json, the capture's per-file seconds; an unlisted module weighs DEFAULT_SECONDS), largest
first onto the lightest shard, ties broken by name, so every shard computes the same assignment from the same collection.

Each shard writes VERACIUM_CI_SHARD_REPORT (if set): its k and n, the count and sha256 of ALL collected node ids, the
assignment's sha256, and the node ids it selected. The workflow's shard-check job reads every shard's report and refuses
unless all agree on the collection and the assignment, the selections are disjoint, and their union is the collection.
"""
import hashlib
import json
import os
import pathlib

import pytest

DEFAULT_SECONDS = 5.0
SEAM_MARK = 'PYTEST_XDIST_WORKER") is None'


def _spec():
    raw = os.environ.get("VERACIUM_CI_SHARD", "")
    if not raw:
        return None
    k, n = (int(x) for x in raw.split("/"))
    if not 1 <= k <= n:
        raise pytest.UsageError(f"VERACIUM_CI_SHARD={raw}: need 1 <= k <= n")
    return k, n


def _is_seam(path):
    return path.name.startswith("test_seam_model_") or SEAM_MARK in path.read_text(encoding="utf-8")


def assign(modules, weights, n, is_seam):
    """modules: sorted repo-relative module paths. Returns {module: shard index 0..n-1}."""
    seam = tuple(m for m in modules if is_seam(m))
    units = [(m,) for m in modules if m not in seam] + ([seam] if seam else [])
    weigh = lambda u: sum(weights.get(m, DEFAULT_SECONDS) for m in u)
    units.sort(key=lambda u: (-weigh(u), u))
    load = [0.0] * n
    out = {}
    for u in units:
        i = min(range(n), key=lambda j: (load[j], j))
        load[i] += weigh(u)
        for m in u:
            out[m] = i
    return out


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    spec = _spec()
    if spec is None:
        return
    k, n = spec
    root = pathlib.Path(str(config.rootpath))
    here = pathlib.Path(__file__).resolve().parent
    weights = json.loads((here / "ci-shard-durations.json").read_text(encoding="utf-8"))["seconds"]
    rel = {it.nodeid: it.path.resolve().relative_to(root).as_posix() for it in items}
    modules = sorted(set(rel.values()))
    table = assign(modules, weights, n, lambda m: _is_seam(root / m))
    keep = [it for it in items if table[rel[it.nodeid]] == k - 1]
    drop = [it for it in items if table[rel[it.nodeid]] != k - 1]
    all_ids = sorted(rel)
    report = {
        "shard": k, "of": n,
        "collected": len(all_ids),
        "collected_sha256": hashlib.sha256("\n".join(all_ids).encode()).hexdigest(),
        "assignment_sha256": hashlib.sha256(json.dumps(table, sort_keys=True).encode()).hexdigest(),
        "modules": sorted(m for m, i in table.items() if i == k - 1),
        "selected": sorted(it.nodeid for it in keep),
    }
    est = sum(weights.get(m, DEFAULT_SECONDS) for m in report["modules"])
    print(f"\nci-shard {k}/{n}: {len(report['modules'])} modules, {len(keep)} of {len(items)} items, "
          f"estimate {est / 60:.1f} min; assignment {report['assignment_sha256'][:16]}")
    out = os.environ.get("VERACIUM_CI_SHARD_REPORT")
    if out:
        pathlib.Path(out).write_text(json.dumps(report, indent=1), encoding="utf-8")
    if drop:
        config.hook.pytest_deselected(items=drop)
    items[:] = keep
