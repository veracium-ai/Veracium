"""0007 §4d (I5), SA-R3-02: loaded by `attestation_job._run_suite` with `-p attestation_collect`, in the SAME pytest
invocation that writes the job's JUnit. It records the session's items as COLLECTED, before any deselection (`-k`,
`-m`, `--deselect`, or a conftest's own `pytest_collection_modifyitems`) can shrink them, and writes their node ids,
in collection order and with their multiplicity, to the file named by $VERACIUM_ATTESTATION_COLLECTED. The job then
requires the JUnit's cases to equal that list as a multiset: a node collected and not reported is missing, one
reported and not collected is unexpected, and a repeated one is a duplicate, each named.

What this cannot see, and why the job refuses it instead: an inherited option that shapes COLLECTION itself
(`-o python_functions=…`, `-p no:…`, a plugin through PYTEST_PLUGINS). Those reach this hook already shrunk, so the
job refuses any PYTEST_* variable, PYTHONPATH and PYTHONHOME in its own environment before the suite runs
(`attestation_job.environment_problem`). This file lives in its own directory so that the PYTHONPATH the job sets
for the child names this module and nothing else."""
import json
import os

import pytest

ENV = "VERACIUM_ATTESTATION_COLLECTED"


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    path = os.environ.get(ENV)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            json.dump([item.nodeid for item in items], f)
