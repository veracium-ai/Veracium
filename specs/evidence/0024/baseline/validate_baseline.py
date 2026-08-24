#!/usr/bin/env python3
# Mutation-Matrix: tests/test_collected_header.py::test_baseline_validator_bites_on_a_planted_mutation
"""Recompute the baseline summaries AND the five load-bearing movements
from the shipped JSONL records — offline, no model, no network.

Round-15 reviewer suggestion, adopted: the measurement is independently
checkable from the archive alone. The summarisation rules are
RE-STATED here rather than imported from the harness, so a drift
between what the harness wrote and what these records support is a
failure, not an inheritance (the presumed-faking rule applied to the
summary itself).

Checks, all hard failures:
  1. each shipped summary equals the summary recomputed from its
     records (per-cell n / third_party_claim_probes /
     tpc_all_quarantined / grounded_probes / answers histogram, and the
     commit field against the records' own homogeneous commit);
  2. the probe-paired MOVEMENT SET — pre-fix quarantined
     third_party_claim, post-fix re-dispositioned
     (original_relation=third_party_claim, relation=unclassified,
     disclosure=mentionable) — is EXACTLY one cell-A probe (A08) and
     four cell-B probes (B06/B08/B10/B14): the 4:1 result;
  3. the relay floor moves 14/16 -> 10/16 (cell B tpc_all_quarantined);
  4. the frozen probe matrix is coherent with the paired runs (48
     probes; the runs' probe ids equal the matrix's; cells agree);
  5. the canary-subject records support the claim they ship for:
     exactly 8, ids == the matrix's cell-C ids, every edge subject
     PRESENT, string-typed and nonempty after canonicalization (round
     16, EVIDENCE-R16-1: absence is not evidence), NO subject
     canonicalizing to 'user', every third_party_claim edge QUARANTINED,
     and CANARY_SUBJECTS.md names the records file (research co-check,
     2026-08-24: the first validator predated this file and a
     canary-only mutation passed silently);
  6. CLOSURE OVER THE UNKNOWN: every digest-bound *.json/*.jsonl data
     file must be one this validator has a check for — a future bundle
     addition without a check is a red run, not a silent pass.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


def _records(name: str) -> list[dict]:
    return [json.loads(l)
            for l in (HERE / name).read_text().splitlines() if l.strip()]


def _summarise(recs: list[dict]) -> dict:
    cells = {}
    for cell in "ABCD":
        cr = [r for r in recs if r["cell"] == cell]
        tpc = [r for r in cr if any(e["relation"] == "third_party_claim"
                                    for e in r["edges"])]
        tpc_q = [r for r in tpc
                 if all(e["disclosure"] == "quarantined"
                        for e in r["edges"]
                        if e["relation"] == "third_party_claim")]
        cells[cell] = {
            "n": len(cr),
            "third_party_claim_probes": len(tpc),
            "tpc_all_quarantined": len(tpc_q),
            "grounded_probes": sum(
                1 for r in cr
                if any(e["disclosure"] == "mentionable"
                       for e in r["edges"])),
            "answers": {k: sum(1 for r in cr if r["answer_class"] == k)
                        for k in ("asserted", "hedged", "absent")},
        }
    return cells


DATA_CHECKED = {
    "baseline_main_records.jsonl", "postfix_records.jsonl",
    "baseline_main_summary.json", "postfix_summary.json",
    "probes.jsonl", "canary_subject_records.jsonl",
}
# prose and harness files carry no recomputable data claim — enumerated,
# not inferred, so a new data file cannot hide among them
NON_DATA = {".md", ".py"}


def main() -> int:
    problems = []
    runs = {}

    # 6 — unknown-member refusal, driven by the digest manifest itself
    for line in (HERE / "DIGESTS.sha256").read_text().splitlines():
        name = line.split(None, 1)[1].strip() if line.strip() else ""
        if not name:
            continue
        suffix = pathlib.Path(name).suffix
        if suffix in NON_DATA or name == "DIGESTS.sha256":
            continue
        if name not in DATA_CHECKED:
            problems.append(
                f"{name}: digest-bound data file with NO validator check "
                f"— coverage must grow with the bundle (research co-check "
                f"2026-08-24: the canary file rode one round unchecked)")
    for rec_name, sum_name in (
            ("baseline_main_records.jsonl", "baseline_main_summary.json"),
            ("postfix_records.jsonl", "postfix_summary.json")):
        recs = _records(rec_name)
        runs[rec_name] = recs
        shipped = json.loads((HERE / sum_name).read_text())
        recomputed = _summarise(recs)
        if shipped["cells"] != recomputed:
            problems.append(f"{sum_name} does not equal the summary "
                            f"recomputed from {rec_name}")
        commits = {r["commit"] for r in recs}
        if len(commits) != 1 or shipped.get("commit") not in commits:
            problems.append(f"{sum_name}: commit {shipped.get('commit')!r} "
                            f"vs record commits {sorted(commits)}")

    pre = {r["probe_id"]: r for r in runs["baseline_main_records.jsonl"]}
    post = {r["probe_id"]: r for r in runs["postfix_records.jsonl"]}
    if set(pre) != set(post):
        problems.append("the two runs are not probe-paired: id sets differ")
    moved = sorted(
        pid for pid in set(pre) & set(post)
        if any(e["relation"] == "third_party_claim"
               and e["disclosure"] == "quarantined"
               for e in pre[pid]["edges"])
        and any(e.get("original_relation") == "third_party_claim"
                and e["relation"] == "unclassified"
                and e["disclosure"] == "mentionable"
                for e in post[pid]["edges"]))
    expect = ["b24-A08", "b24-B06", "b24-B08", "b24-B10", "b24-B14"]
    if moved != expect:
        problems.append(f"the movement set is {moved}, expected {expect} "
                        f"(the 4:1 result's exact membership)")
    by_cell = {}
    for pid in moved:
        by_cell.setdefault(pre[pid]["cell"], []).append(pid)
    if len(by_cell.get("A", [])) != 1 or len(by_cell.get("B", [])) != 4:
        problems.append(f"movement by cell is "
                        f"{ {c: len(v) for c, v in by_cell.items()} }, "
                        f"expected A:1 B:4")

    floor_pre = _summarise(list(pre.values()))["B"]["tpc_all_quarantined"]
    floor_post = _summarise(list(post.values()))["B"]["tpc_all_quarantined"]
    if (floor_pre, floor_post) != (14, 10):
        problems.append(f"relay floor moved {floor_pre} -> {floor_post}, "
                        f"expected 14 -> 10")

    # 4 — the frozen matrix coheres with the paired runs
    probes = _records("probes.jsonl")
    if len(probes) != 48:
        problems.append(f"probes.jsonl holds {len(probes)}, expected 48")
    matrix = {pr["probe_id"]: pr["cell"] for pr in probes}
    if set(matrix) != set(pre):
        problems.append("the paired runs' probe ids differ from the matrix")
    else:
        bad = [pid for pid in pre if pre[pid]["cell"] != matrix[pid]]
        if bad:
            problems.append(f"cells disagree with the matrix for {bad}")

    # 5 — the canary-subject records support their claim
    canaries = _records("canary_subject_records.jsonl")
    c_ids = sorted(pid for pid, c in matrix.items() if c == "C")
    if sorted(r["probe_id"] for r in canaries) != c_ids or len(canaries) != 8:
        problems.append(
            f"canary records are {sorted(r['probe_id'] for r in canaries)}, "
            f"expected exactly the matrix's cell-C ids {c_ids}")
    md = (HERE / "CANARY_SUBJECTS.md").read_text()
    if "canary_subject_records.jsonl" not in md:
        problems.append("CANARY_SUBJECTS.md does not name the records file "
                        "it chains to")
    for r in canaries:
        for e in r["edges"]:
            subj = e.get("subject")
            if not isinstance(subj, str) or not subj.strip():
                problems.append(
                    f"{r['probe_id']}: a canary edge subject is absent, "
                    f"non-string, or empty after canonicalization — "
                    f"ABSENCE IS NOT EVIDENCE of a non-user claiming voice "
                    f"(round 16, EVIDENCE-R16-1: a silent '' default "
                    f"admitted exactly what this check exists to reject)")
            elif subj.strip().casefold() == "user":
                problems.append(
                    f"{r['probe_id']}: a canary edge subject canonicalizes "
                    f"to 'user' — the exact state this file ships to prove "
                    f"absent")
            if (e.get("relation") == "third_party_claim"
                    and e.get("disclosure") != "quarantined"):
                problems.append(
                    f"{r['probe_id']}: a third_party_claim canary edge is "
                    f"{e.get('disclosure')!r}, not quarantined")


    if problems:
        print("validate_baseline: FAILED\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    print(f"validate_baseline: summaries recomputed and equal; movement "
          f"set == {expect} (A:1, B:4 — the 4:1 result); relay floor "
          f"14 -> 10; matrix coherent (48); canary records support their "
          f"claim (8/8, no user-subject, all tpc quarantined); every "
          f"digest-bound data file checked. All from the shipped JSONL, "
          f"no model run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
