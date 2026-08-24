#!/usr/bin/env python3
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
  3. the relay floor moves 14/16 -> 10/16 (cell B tpc_all_quarantined).
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


def main() -> int:
    problems = []
    runs = {}
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

    if problems:
        print("validate_baseline: FAILED\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    print(f"validate_baseline: summaries recomputed and equal; movement "
          f"set == {expect} (A:1, B:4 — the 4:1 result); relay floor "
          f"14 -> 10. All from the shipped JSONL, no model run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
