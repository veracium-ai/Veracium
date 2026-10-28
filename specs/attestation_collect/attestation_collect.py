"""0007 §4d (I5), SA-R3-02: loaded by `attestation_job._run_suite` with `-p attestation_collect`, in the SAME pytest
invocation that writes the job's JUnit. It records each item AS COLLECTED, in `pytest_itemcollected`, which pytest calls
once per item while collecting and before ANY `pytest_collection_modifyitems` runs, whatever its priority, and writes
the node ids, in collection order and with their multiplicity, to the file named by $VERACIUM_ATTESTATION_COLLECTED
when collection finishes. The job then requires the JUnit's cases to equal that list as a multiset: a node collected
and not reported is missing, one reported and not collected is unexpected, and a repeated one is a duplicate, each
named. So `-k`, `-m`, `--deselect` and a conftest's own modifyitems hook (tryfirst, trylast, unmarked or a wrapper)
cannot shrink the run unseen.

Research's stage 2 on 95c207c: the first form recorded in a tryfirst `pytest_collection_modifyitems`, and a CONFTEST's
tryfirst implementation runs before it (pluggy calls equal-priority implementations in reverse registration order,
and conftests register after `-p` plugins), so a conftest could drop a failing test before it was recorded.

What this cannot see, and why the job refuses it instead: an inherited option that shapes COLLECTION itself
(`-o python_functions=…`, `-p no:…`, a plugin through PYTEST_PLUGINS) reaches this hook already shrunk, so the job
refuses any PYTEST_* variable, PYTHONPATH and PYTHONHOME in its own environment before the suite runs
(`attestation_job.environment_problem`). Nor can it see an item that is never created: a conftest
`pytest_pycollect_makeitem` that declines a test function leaves no item to record (committed code in the reviewed
tree, like any test). This file lives in its own directory so that the PYTHONPATH the job sets for the child names
this module and nothing else."""
import json
import os

import pytest

ENV = "VERACIUM_ATTESTATION_COLLECTED"
_COLLECTED = []


def pytest_itemcollected(item):
    _COLLECTED.append(item.nodeid)


@pytest.hookimpl(trylast=True)
def pytest_collection_finish(session):
    path = os.environ.get(ENV)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_COLLECTED, f)
