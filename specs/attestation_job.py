#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0007_attestation_jobs.py::test_the_attestation_job_mutation_matrix
"""0007 §4d (I5): ONE attestation job, run in the matrix row's own interpreter. It decides a CLOSED outcome and writes
it, with this build's record when there is one, to `--out`.

    $PY specs/attestation_job.py --route R --runner-image I --expect-prefix P --run-id N --job-id K --out F

In order, stopping at the first step that decides (research's stage-1 read of I5, BLOCKING 1–4):
  0. the job is non-root (else **wrong-job-state**, red: INV-SA6's job-state assertion), and the row is the route it
     claims: Python >= 3.14, and realpath(sys.base_prefix) lies under the row's declared
     `--expect-prefix`; else **wrong-interpreter** (red);
  1. §4b verification, `sv.runtime_status()`: `refused` is **refused**, with the failing step. That is a census row, not a
     record, and the job exits 0 ("a job whose build fails verification records that result, it does not fail
     the matrix");
  2. `migrations_0013.py --check-evidence`: nonzero is **evidence-mismatch** (red; 0013 §5f.3, "a FAILED attestation
     job, named, never a record");
  3. the suite, by the one committed rule (`attestation_suite.py`), run ONCE in pytest's own order with
     pytest-randomly disabled, into a JUnit file; the JUnit must have run exactly the rule's modules, else
     **suite-mismatch** (red);
  4. skips, FROM THE SAME JUNIT: an xfail is never a skip; one mapping to no inventory entry is **unmapped-skip**
     (red);
  5. any failure or error is **failed-tests** (red), whether or not a job:runs condition also fired (exclusion means
     "not an input", never "not a failure"). Its digest is still written, as a member of its key's group;
  5b. a skip mapping to a `job:runs` entry is **excluded**, naming the entry: not an input and not a disagreement, so
     exit 0;
  6. otherwise **evidence**, unless the record would be malformed (a confinement probe failing on this build is
     **confinement-failed**, red, and never a record): the result digest over the sorted (node id, outcome) pairs, the sixteen confinement
     probes run live, and the record built HERE, in this process, by `attestation_writer.build_record` (the key is
     this build's own, W3).

Provenance `job_id` is the row's MATRIX INDEX within its run (`strategy.job-index`), not GitHub's numeric job id: unique
within one run, which is all §4d's ordering needs. Look a job up by run id and matrix index, never as a GitHub job id.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import secrets
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPECS = ROOT / "specs"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(SPECS))

import attestation_suite  # noqa: E402
import skip_inventory  # noqa: E402

OUTCOME_EXIT = {"evidence": 0, "bootstrap-pending": 0, "refused": 0, "unattestable": 0, "excluded": 0,
                "wrong-interpreter": 1, "wrong-job-state": 1, "evidence-mismatch": 1, "suite-mismatch": 1, "unmapped-skip": 1,
                "failed-tests": 1, "confinement-failed": 1}
"""The CLOSED outcome set, and each one's exit code. (`unavailable`, an interpreter that could not be installed, is
the workflow's: no job script ran, so the aggregator names the row from the workflow's matrix.)"""

PYTEST_ARGS = ("-p", "no:randomly", "-p", "no:cacheprovider", "-q")
COLLECT_PLUGIN_DIR = SPECS / "attestation_collect"
COLLECT_ENV = "VERACIUM_ATTESTATION_COLLECTED"
"""SA-R3-02: `-p attestation_collect` records the items as collected, in the same invocation (attestation_collect.py)."""
ENV_REFUSED = ("PYTHONPATH", "PYTHONHOME")
ENV_REFUSED_PREFIXES = ("PYTEST_",)
"""SA-R3-02 (and research's stage-1 read): the job's own environment must not shape pytest. PYTEST_ADDOPTS deselects
(`--deselect`) or shrinks collection itself (`-o python_functions=…`, which the same invocation's own collection then
agrees with), PYTEST_PLUGINS loads outcome-rewriting code, PYTHONPATH/PYTHONHOME change what is imported. Any of them
present REFUSES the job before anything runs; nothing is silently stripped. Every other variable is inherited, so
CI's own environment (which sets none of these) reaches the suite unchanged."""
COMPLETION_KEYS = ("returned", "exit_status", "nonce")
_CHILD = ("import json, sys\n"
          "import pytest\n"
          "path, nonce, args = sys.argv[1], sys.argv[2], sys.argv[3:]\n"
          "rc = int(pytest.main(args))\n"
          "with open(path, 'w', encoding='utf-8') as f:\n"
          "    json.dump({'returned': True, 'exit_status': rc, 'nonce': nonce}, f)\n"
          "sys.exit(rc)\n")
"""0007 round 4, SA-R4-01: the suite's POSITIVE completion signal, at the process boundary. The child runs pytest.main
and writes this record only if pytest.main RETURNED. A failure pytest does not catch, such as an exception escaping
pytest_sessionfinish after the JUnit was written (wrap_session calls it in its `finally` with no handler for an ordinary
exception, so it leaves pytest.main) or a raising pytest_unconfigure, leaves no record, whatever hook priority raised it:
no hook runs after pytest.main returns. A sessionfinish hookwrapper would not do, because a conftest's tryfirst wrapper
registers after a -p plugin and runs OUTSIDE it (research's stage-1 read; kept as a mutant). It proves pytest.main
returned against HONEST process failures; code inside the suite could forge it, which is outside the stated adversary."""
PYTEST_EXIT = {2: "interrupted", 3: "internal error", 4: "usage error", 5: "no tests collected"}
"""SA-R3-03: pytest's exit codes other than 0 (all passed) and 1 (tests failed), each named in the refusal."""

BOOTSTRAP = ("tests/test_migrations_0013.py::test_the_committed_path_evidence_was_generated_on_an_attested_build",)
"""0007 v21 (Quentin, 2026-10-27: "Two runs, bootstrap"): the ONE node exempt at a zero-current state. A10 asserts the
committed path evidence was generated on an ATTESTED build, which cannot hold while no current record exists, and the run
that would write one runs A10. So iff every record in the committed artifact is superseded (none at all counts), a JUnit
FAILURE of this node alone gives `bootstrap-pending`; an <error> on it, any other failing node, or any current, malformed
or future record gives `failed-tests`. This holds at EVERY zero-current state: the first run, and every manifest-algorithm
or schema-version bump. Such a run's records mean "the suite passed except the declared node, at a zero-current state";
they seed the path-evidence regeneration and never ship (the release check refuses them, by derivation)."""
"""BLOCKING 1: ONE ordering source. pytest-randomly is in the dev extra and reorders and reseeds per test, so two jobs
of one key could disagree on an order-dependent outcome."""


class Decided(Exception):
    def __init__(self, outcome, reason, **extra):
        assert outcome in OUTCOME_EXIT, outcome
        super().__init__(f"{outcome}: {reason}")
        self.outcome, self.reason, self.extra = outcome, reason, extra


def interpreter_problem(expect_prefix, base_prefix=None, version_info=None) -> str | None:
    """Step 0, BLOCKING 3: None, or why this interpreter is not the row's. The job runs in a venv, so the BASE install
    is what is compared: `sys.base_prefix`, resolved. (realpath(sys.executable) sees through a POSIX venv's symlink but
    not a Windows venv's copied python.exe.)"""
    version_info = sys.version_info if version_info is None else version_info
    if tuple(version_info[:2]) < (3, 14):
        return f"Python {version_info[0]}.{version_info[1]} is below the floor 3.14"
    real = os.path.realpath(sys.base_prefix if base_prefix is None else base_prefix)
    prefix = os.path.realpath(expect_prefix)
    try:
        under = os.path.commonpath([real, prefix]) == prefix
    except ValueError:                                     # different drives (Windows): not under
        under = False
    if not under:
        return f"the interpreter's base install {real} is not under the row's declared location {prefix}"
    return None


def junit_cases(junit_path) -> list:
    """[(node id, outcome, skip message or None)], outcome one of passed/failed/error/skipped/xfailed."""
    out = []
    for case in ET.parse(junit_path).getroot().iter("testcase"):
        parts = (case.get("classname") or "").split(".")
        mod = next(i for i, p in enumerate(parts) if p.startswith("test_"))
        nodeid = "::".join(["/".join(parts[:mod + 1]) + ".py", *parts[mod + 1:], case.get("name") or ""])
        kids = {c.tag: c for c in case}
        if "error" in kids:
            out.append((nodeid, "error", None))
        elif "failure" in kids:
            out.append((nodeid, "failed", None))
        elif "skipped" in kids:
            sk = kids["skipped"]
            if sk.get("type") == "pytest.xfail":
                out.append((nodeid, "xfailed", None))          # BLOCKING 4: an xfail is not a skip
            else:
                out.append((nodeid, "skipped", " ".join(filter(None, (sk.get("message"), sk.text)))))
        else:
            out.append((nodeid, "passed", None))
    return out


def result_digest(cases) -> str:
    """sha256 over the sorted (node id, outcome) pairs, without timings (§4d)."""
    pairs = sorted((n, o) for n, o, _ in cases)
    return hashlib.sha256(json.dumps(pairs, separators=(",", ":")).encode()).hexdigest()


def classify_skips(cases):
    """(job:runs entries that fired, skips that match no entry), from the JUnit's own skip messages."""
    fired, unmapped = [], []
    for nodeid, outcome, message in cases:
        if outcome != "skipped":
            continue
        entry = skip_inventory.entry_for(nodeid.split("::")[0], message or "")
        if entry is None:
            unmapped.append(f"{nodeid}: {(message or '')[:120]}")
        elif skip_inventory.attestation_class(entry) == "job:runs":
            fired.append(f"{entry[0]} [{entry[2]}] at {nodeid}")
    return sorted(set(fired)), unmapped


def _check_evidence() -> tuple:
    p = subprocess.run([sys.executable, str(SPECS / "migrations_0013.py"), "--check-evidence"], cwd=str(ROOT),
                       env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)[-2000:]


def collected_path(junit) -> pathlib.Path:
    junit = pathlib.Path(junit)
    return junit.with_name(junit.name + ".collected.json")


def completion_path(junit) -> pathlib.Path:
    junit = pathlib.Path(junit)
    return junit.with_name(junit.name + ".completion.json")


def nonce_path(junit) -> pathlib.Path:
    junit = pathlib.Path(junit)
    return junit.with_name(junit.name + ".nonce")


def _run_suite(junit) -> int:
    """The suite, ONCE, by the committed rule; returns pytest's exit status (SA-R3-03: decide consumes it). The child
    is `_CHILD` around pytest.main (SA-R4-01), handed the completion path and decide's nonce; the same arguments as
    before, the collection plugin included, which is still the only thing the job adds to the child's environment."""
    modules = attestation_suite.suite(ROOT)
    env = {**os.environ, "PYTHONPATH": str(COLLECT_PLUGIN_DIR), COLLECT_ENV: str(collected_path(junit))}
    return subprocess.run([sys.executable, "-c", _CHILD, str(completion_path(junit)), nonce_path(junit).read_text(),
                           *PYTEST_ARGS, "-p", "attestation_collect", f"--junitxml={junit}", *modules],
                          cwd=str(ROOT), env=env).returncode


def completion_problem(path, rc, nonce) -> str | None:
    """SA-R4-01: None iff the suite process COMPLETED: its completion record exists, holds exactly COMPLETION_KEYS,
    says pytest.main returned, carries THIS run's nonce (a stale record refuses) and the exit status the process
    exited with. Otherwise the reason, named."""
    path = pathlib.Path(path)
    head = "the suite process did not complete normally: "
    if not path.exists():
        return head + "no completion record (pytest.main did not return; e.g. a session-finish failure after the JUnit)"
    try:
        rec = json.loads(path.read_text())
    except ValueError as e:
        return head + f"its completion record is not JSON ({e})"
    if not isinstance(rec, dict) or set(rec) != set(COMPLETION_KEYS):
        return head + f"its completion record's keys are not {list(COMPLETION_KEYS)}"
    if rec["returned"] is not True:
        return head + "its completion record does not say pytest.main returned"
    if rec["nonce"] != nonce:
        return head + "its completion record is not this run's (the nonce differs)"
    if type(rec["exit_status"]) is not int or rec["exit_status"] != rc:
        return head + f"pytest.main returned {rec['exit_status']!r} but the process exited {rc!r}"
    return None


def _head() -> str:
    """The checkout's HEAD. A failed `git rev-parse` is the job's state, named (research's stage-1 read of SA-R3-03):
    its "" used to reach the record validator and read as confinement-failed."""
    import attestation_writer as aw
    rc, out = aw.run_git(["rev-parse", "HEAD"], ROOT)
    if rc != 0:
        raise Decided("wrong-job-state", f"git rev-parse HEAD exited {rc}: the job's checkout has no readable HEAD")
    return out


def environment_problem(environ=None) -> str | None:
    """SA-R3-02: None, or the inherited variables that would shape the suite (ENV_REFUSED, ENV_REFUSED_PREFIXES)."""
    environ = os.environ if environ is None else environ
    bad = sorted(k for k in environ if k in ENV_REFUSED or k.startswith(ENV_REFUSED_PREFIXES))
    return (f"the job's environment shapes pytest ({', '.join(bad)}): the suite must run by the committed rule alone"
            if bad else None)


def node_problems(cases, collected) -> list:
    """SA-R3-02: the JUnit's node ids must equal the invocation's own collection as a MULTISET (identity and
    multiplicity), each difference named. Module equality alone admitted a node deselected inside a present module."""
    if collected is None:
        return ["the suite left no collection record (attestation_collect did not run)"]
    got, want = Counter(n for n, _, _ in cases), Counter(collected)
    out = []
    for label, nodes in (("missing (collected, not reported)", want - got), ("unexpected (reported, not collected)",
                                                                             got - want)):
        if nodes:
            out.append(f"{sum(nodes.values())} {label}: " + ", ".join(sorted(nodes)[:20]))
    dup = sorted(n for n, c in got.items() if c > 1)
    if dup:
        out.append(f"{len(dup)} reported more than once: " + ", ".join(dup[:20]))
    return out


def exit_problem(rc, cases):
    """SA-R3-03: (outcome, reason) when pytest's exit status disagrees with its JUnit, else None. 0 means no failing
    case and 1 means at least one; a 1 with every case passing is a session-level failure (a hook raising after the
    report was written). Any other status is named; 5 (no tests collected) is what a fully shrunk collection gives."""
    failing = any(o in ("failed", "error") for _, o, _ in cases)
    if rc == 1 and not failing:
        return "failed-tests", "pytest exited 1 with no failing case in its JUnit: a session-level failure"
    if rc == 0 and failing:
        return "suite-mismatch", "pytest exited 0 while its JUnit has a failing case"
    if rc not in (0, 1):
        return "suite-mismatch", f"pytest exited {rc!r} ({PYTEST_EXIT.get(rc, 'not a pytest exit status')})"
    return None


def job_state_problem(euid=None) -> str | None:
    """INV-SA6's job-state assertion (§4d job:runs): the attestation job runs NON-root, so the geteuid entries cannot
    fire. A root job would skip the read-only-store tests and attest a suite it did not run, and two jobs of one key
    (one root, one not) would read as "the key does not identify the build". run_row.sh refuses root too; this is
    the check a matrix can mutate."""
    euid = (os.geteuid() if hasattr(os, "geteuid") else None) if euid is None else euid
    return "the attestation job is running as root (uid 0): it must run as a non-root user" if euid == 0 else None


def bootstrap_open(records=None) -> bool:
    """True iff EVERY record of the committed artifact is superseded (an empty artifact counts): a zero-current state,
    the only one the bootstrap exemption applies in. A current, malformed or future record closes it, so poisoning the
    artifact cannot re-open it, and an unreadable artifact is not "empty"."""
    from veracium.store import schema_version as sv
    import attestation_writer as aw
    try:
        records = sv.attestations() if records is None else records
    except (OSError, ValueError):
        return False
    return aw.zero_current(records)                    # v22 (N1): the ONE predicate the bootstrap derivation uses


def decide(args, *, runtime_status=None, check_evidence=_check_evidence, run_suite=_run_suite, probes=None,
           head=_head, euid=None, records=None, environ=None) -> dict:
    """The job's closed result. Every seam is injectable, so each outcome is a cell."""
    from veracium.store import schema_version as sv
    import attestation_writer as aw
    st = (sv.runtime_status if runtime_status is None else runtime_status)()
    result = {"outcome": None, "reason": "", "route": args.route, "runner_image": args.runner_image,
              "job_id": int(args.job_id),          # the aggregate names jobs by it (run 1 printed "job ?")
              "sqlite_version": st.sqlite_version, "source_id": st.source_id, "status": st.status,
              "key": None, "result_digest": None, "excluded_entries": [], "record": None}
    try:
        bad = interpreter_problem(args.expect_prefix)
        if bad:
            raise Decided("wrong-interpreter", bad)
        bad = job_state_problem(euid) or environment_problem(environ)
        if bad:
            raise Decided("wrong-job-state", bad)
        result["key"] = list(sv.attestation_key(sv.attestation_identity()) or []) or None
        if st.status == "refused":
            raise Decided("refused", st.reason or "refused")
        rc, tail = check_evidence()
        if rc != 0:
            raise Decided("evidence-mismatch", f"--check-evidence exited {rc}: {tail.strip()[-400:]}")
        # 0007 v22 §4d: AFTER the re-derivation (owed on every verifying build), a build whose key has an unreadable
        # field cannot be attested: a named census row, exit 0, and no suite.
        ident = sv.attestation_identity()
        if sv.attestation_key(ident) is None:
            raise Decided("unattestable", "this build's attestation key has an unreadable field: "
                                          + ", ".join(k for k in sv.KEY_FIELDS if ident.get(k) is None))
        with tempfile.TemporaryDirectory() as td:
            junit = pathlib.Path(td) / "junit.xml"
            nonce = secrets.token_hex(16)                 # SA-R4-01: this run's, so no other run's record can stand in
            nonce_path(junit).write_text(nonce)
            rc = run_suite(junit)
            if not junit.exists():
                raise Decided("suite-mismatch", f"the suite wrote no JUnit file (pytest exited {rc!r})")
            mismatch = attestation_suite.nodes_problems(junit, ROOT)      # the committed rule's modules, kept
            if mismatch:
                raise Decided("suite-mismatch", "; ".join(mismatch))
            cases = junit_cases(junit)
            cp = collected_path(junit)
            mismatch = node_problems(cases, json.loads(cp.read_text()) if cp.exists() else None)
            if mismatch:
                raise Decided("suite-mismatch", "; ".join(mismatch))
            bad = exit_problem(rc, cases)
            if bad:
                raise Decided(*bad)
            # SA-R4-01: BEFORE any outcome past the suite, so before every outcome that yields a record: the exempt
            # bootstrap failure explains exit 1 only if the process otherwise COMPLETED
            bad = completion_problem(completion_path(junit), rc, nonce)
            if bad:
                raise Decided("failed-tests", bad)
        result["result_digest"] = result_digest(cases)
        fired, unmapped = classify_skips(cases)
        if unmapped:
            raise Decided("unmapped-skip", f"{len(unmapped)} skip(s) match no inventory entry: " + "; ".join(unmapped))
        result["excluded_entries"] = fired
        # Failures FIRST (research's stage 2 on 84c512b): exclusion means "not an input", never "not a failure". A
        # job whose job:runs condition fired AND whose suite fails is red, and still names the fired entries.
        failing = [n for n, o, _ in cases if o in ("failed", "error")]
        pending = sorted(n for n, o, _ in cases if o == "failed" and n in BOOTSTRAP)       # a FAILURE, never an error
        open_ = bootstrap_open(records)
        if failing and (set(failing) - set(pending) or not open_):
            raise Decided("failed-tests", f"{len(failing)} failing: " + ", ".join(failing[:20])
                          + (f" (and {len(fired)} job:runs condition(s) fired)" if fired else "")
                          + (" (the bootstrap exemption is void: the artifact already holds a current record)"
                             if pending and not open_ else ""))
        if fired:
            raise Decided("excluded", f"{len(fired)} job:runs condition(s) fired: " + "; ".join(fired))
        live = (_live_probes if probes is None else probes)()
        commit = head()
        record = aw.build_record(result["result_digest"], live,
                                 [{"route": args.route, "runner_image": args.runner_image, "run_id": str(args.run_id),
                                   "job_id": int(args.job_id), "commit": commit}])
        problems = sv.attestation_record_problems(record)
        if problems:                                       # a failing confinement probe: never a record, and not a
            raise Decided("confinement-failed", f"the record would be malformed: {problems[0]}")   # failed TEST
        if pending:
            result.update(outcome="bootstrap-pending", record=record,
                          reason=f"bootstrap run: {', '.join(pending)} pending (no attestation record exists yet); this "
                                 f"record seeds the evidence regeneration and is never shipped")
        else:
            result.update(outcome="evidence", reason="", record=record)
    except Decided as d:
        result.update(outcome=d.outcome, reason=d.reason)
    return result


def _live_probes() -> dict:
    import migrations_0013
    return migrations_0013.authorizer_probes()


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    for a in ("--route", "--runner-image", "--expect-prefix", "--run-id", "--out"):
        ap.add_argument(a, required=True)
    ap.add_argument("--job-id", required=True, type=int)
    args = ap.parse_args(argv[1:])
    result = decide(args)
    pathlib.Path(args.out).write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(f"{result['outcome']}: {result['reason']}" if result["reason"] else result["outcome"])
    return OUTCOME_EXIT[result["outcome"]]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
