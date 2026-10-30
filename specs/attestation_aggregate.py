#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0007_attestation_jobs.py::test_the_attestation_aggregate_mutation_matrix
"""0007 §4d (v0.12, SA-R1-03; I5): aggregation within ONE CI run, deterministic.

    $PY specs/attestation_aggregate.py <results-dir> --rows <rows.json> --out <records.json> [--write]

1. The run's job results (attestation_job.py's JSON, one per row) are grouped by FULL attestation key. An `evidence`
   member's key is taken from ITS RECORD, never recomputed here: this runner is not that build (Q4).
2. A key whose members are all `evidence` with EQUAL evidence (result digest, confinement) and otherwise equal records
   emits ONE record. Its provenance is the union of the contributing jobs, sorted by route, then image, then job id.
3. Disagreement emits NO record for that key and FAILS the step, naming every job of the group. That covers different
   evidence; a `refused`, `failed-tests` or `evidence-mismatch` member beside an `evidence` one; and a key whose
   members are only `failed-tests` / `evidence-mismatch` (research Q5a: "attested" is never one red job away from
   silently empty). Other keys still emit.
4. `excluded` jobs are not inputs; an all-excluded key is listed, not a failure. `refused` alone is a census row.
   A row of `--rows` with no result is **unavailable** (its interpreter could not be installed), named so it can never
   read as attested.
`--write` hands the emitted records to `attestation_writer.write_records` (v19's order against the committed artifact).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "specs"))

from veracium.store import schema_version as sv  # noqa: E402

FAILING = ("failed-tests", "evidence-mismatch", "confinement-failed", "wrong-job-state")
"""Red job outcomes that still measured a key: members of their key's group, never a record (§4d step 3)."""
RECORD_OUTCOMES = ("evidence", "bootstrap-pending")
"""The job outcomes that carry a record, as this consumer reads them (research's stage 2 of round 5, F4): ONE carrier,
which the job's cells compare with the outcomes decide is observed to pair with a record."""


def _job(r) -> str:
    return f"{r.get('route')} on {r.get('runner_image')} (job {r.get('job_id', '?')}: {r.get('outcome')})"


def _evidence(rec) -> tuple:
    return rec["result_digest"], json.dumps(rec["confinement"], sort_keys=True)


def aggregate(results, rows=()) -> dict:
    """{records, disagreements, failed_keys, refused, excluded, unavailable, other_failures}."""
    groups, out = {}, {"records": [], "bootstrap_jobs": [], "disagreements": [], "failed_keys": [], "refused": [],
                       "unattestable": [], "excluded": [], "unavailable": [], "other_failures": []}
    seen_rows = set()
    for r in results:
        seen_rows.add((r.get("route"), r.get("runner_image")))
        outcome = r.get("outcome")
        if outcome == "unattestable":
            out["unattestable"].append(_job(r) + ": " + (r.get("reason") or ""))
            continue
        if outcome == "excluded":
            out["excluded"].append(_job(r) + ": " + "; ".join(r.get("excluded_entries") or []))
            continue
        if outcome in RECORD_OUTCOMES:
            rec = r.get("record")
            key = sv.attestation_key(rec) if isinstance(rec, dict) else None
            if key is None or sv.attestation_record_problems(rec):
                out["other_failures"].append(_job(r) + ": its record is malformed")
                continue
        elif outcome in FAILING or outcome == "refused":
            key = tuple(tuple(k) if isinstance(k, list) else k for k in r["key"]) if r.get("key") else None
            if key is None:                       # an unreadable key: nothing to group with, named
                (out["refused"] if outcome == "refused" else out["other_failures"]).append(_job(r) + ": no key")
                continue
        else:
            out["other_failures"].append(_job(r) + f": {r.get('reason', '')}"[:300])
            continue
        groups.setdefault(key, []).append(r)
    for row in rows:
        if (row["route"], row["runner_image"]) not in seen_rows:
            out["unavailable"].append(f"{row['route']} on {row['runner_image']}")
    for key, members in sorted(groups.items(), key=lambda kv: repr(kv[0])):
        kinds = {m["outcome"] for m in members}
        names = sorted(_job(m) for m in members)
        if kinds == {"refused"}:
            out["refused"] += names
            continue
        if not kinds & set(RECORD_OUTCOMES):
            out["failed_keys"].append({"key": repr(key), "jobs": names})
            continue
        if "bootstrap-pending" in kinds and kinds != {"bootstrap-pending"}:
            out["disagreements"].append({"key": repr(key), "why": "a bootstrap job beside a non-bootstrap one",
                                         "jobs": names})
            continue
        if kinds - set(RECORD_OUTCOMES):
            out["disagreements"].append({"key": repr(key), "why": "a verifying job beside a "
                                         + "/".join(sorted(kinds - {"evidence"})) + " one", "jobs": names})
            continue
        recs = [m["record"] for m in members]
        base = {k: v for k, v in recs[0].items() if k != "provenance"}
        if any({k: v for k, v in rec.items() if k != "provenance"} != base for rec in recs[1:]):
            why = ("different evidence" if len({_evidence(rec) for rec in recs}) > 1
                   else "records differ outside provenance")
            out["disagreements"].append({"key": repr(key), "why": why, "jobs": names})
            continue
        prov = sorted((j for rec in recs for j in rec["provenance"]),
                      key=lambda j: (j["route"], j["runner_image"], j["job_id"]))
        out["records"].append({**base, "provenance": prov})
        if kinds == {"bootstrap-pending"}:
            out["bootstrap_jobs"] += names            # named: the writer's --fresh refuses an aggregate that has any
    return out


def failed(summary) -> bool:
    return bool(summary["disagreements"] or summary["failed_keys"])


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv[1:])
    results = [json.loads(p.read_text()) for p in sorted(pathlib.Path(a.results).glob("*.json"))]
    summary = aggregate(results, json.loads(pathlib.Path(a.rows).read_text())["rows"])   # rows.json, the one carrier
    pathlib.Path(a.out).write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    for k in ("disagreements", "failed_keys", "other_failures", "unavailable", "refused", "unattestable", "excluded"):
        for item in summary[k]:
            print(f"{k}: {item}")
    print(f"{len(summary['records'])} record(s)")
    if a.write and summary["records"]:
        import attestation_writer as aw
        try:
            print(aw.write_records(summary["records"]))
        except aw.AttestationRefused as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 1
    return 1 if failed(summary) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
