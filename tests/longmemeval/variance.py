"""Extraction-variance protocol (spec §4, as specified by the external review).

The canonical run freezes ONE stochastic extraction draw per unique turn and
replays it everywhere. That is deliberate — it is what makes the cost tolerable
and runs comparable — but it hides how much of a score is extractor noise. This
measures exactly that hidden quantity.

Design (fixed before the pilot, not tuned to its result):
  * 14 questions: 2 per question type, plus abstention items
  * 3 independent end-to-end realizations, each with a FRESH cache, so
    extraction, the write path, answering and official judging all re-run
  * report: extraction-record agreement (edge-set Jaccard across realizations),
    final-answer agreement, official-score range, per-type instability

    PYTHONPATH=src python tests/longmemeval/variance.py --workers 14
    PYTHONPATH=src python tests/longmemeval/variance.py --judge-only   # after judging

Judging is not run here (same rule as the main runner): this writes one
hypothesis file per realization, `judge.sh` scores each, then `--judge-only`
aggregates the judged results.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from adapter import QUESTION_TYPES, S_FILE, load
from run_longmemeval import _provider, run

VAR_DIR = Path.home() / "Datasets" / "longmemeval" / "variance"
REALIZATIONS = 3
PER_TYPE = 2
ABSTENTIONS = 2


def subset(items, evals, *, seed: int = 0):
    """2 per question type + 2 abstention items, pinned seed."""
    rng = random.Random(seed)
    by_type: dict[str, list] = {t: [] for t in QUESTION_TYPES}
    abst = []
    for it in items:
        ev = evals[it.question_id]
        (abst if ev.is_abstention else by_type[ev.question_type]).append(it)
    picked = {}
    for t, pool in by_type.items():
        for it in rng.sample(pool, min(PER_TYPE, len(pool))):
            picked[it.question_id] = it
    for it in rng.sample(abst, min(ABSTENTIONS, len(abst))):
        picked[it.question_id] = it
    return sorted(picked.values(), key=lambda i: i.question_id)


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 1.0


def aggregate(paths: list[Path]) -> dict:
    """Compare realizations. Accepts raw hypothesis files (answer/extraction
    agreement) or judged .eval-results files (adds the score range)."""
    runs = []
    for p in paths:
        rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
        runs.append({r["question_id"]: r for r in rows})
    qids = sorted(set.intersection(*(set(r) for r in runs)))

    edge_agree, ans_agree, per_q = [], [], {}
    for qid in qids:
        sigs = [set(r[qid].get("edge_sig") or []) for r in runs]
        pairs = [_jaccard(a, b) for a, b in itertools.combinations(sigs, 2)]
        e = sum(pairs) / len(pairs) if pairs else 1.0
        hyps = [(r[qid].get("hypothesis") or "").strip().lower() for r in runs]
        labels = [r[qid].get("autoeval_label", {}).get("label") for r in runs]
        identical = len(set(hyps)) == 1
        judged_agree = None if any(l is None for l in labels) else len(set(labels)) == 1
        edge_agree.append(e)
        ans_agree.append(1.0 if identical else 0.0)
        per_q[qid] = {"edge_jaccard": round(e, 3), "answers_identical": identical,
                      "judged_labels": labels, "judged_agree": judged_agree}

    scores = []
    for r in runs:
        labels = [row.get("autoeval_label", {}).get("label") for row in r.values()]
        if all(l is not None for l in labels) and labels:
            scores.append(sum(1 for l in labels if l) / len(labels))
    out = {
        "realizations": len(runs), "questions": len(qids),
        "extraction_agreement_mean_jaccard": round(sum(edge_agree) / len(edge_agree), 3)
        if edge_agree else None,
        "identical_answer_rate": round(sum(ans_agree) / len(ans_agree), 3)
        if ans_agree else None,
        "per_question": per_q,
    }
    if scores:
        out["official_scores"] = [round(s, 4) for s in scores]
        out["official_score_range"] = round(max(scores) - min(scores), 4)
        unstable = [q for q, v in per_q.items() if v["judged_agree"] is False]
        out["questions_flipping_label"] = unstable
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--arm", choices=["T", "C"], default="C")
    ap.add_argument("--provider", default="openai")
    ap.add_argument("--judge-only", action="store_true",
                    help="aggregate existing (judged) realization files")
    args = ap.parse_args()

    VAR_DIR.mkdir(parents=True, exist_ok=True)
    if args.judge_only:
        judged = sorted(VAR_DIR.glob("**/hypotheses_*eval-results-gpt-4o"))
        plain = sorted(VAR_DIR.glob("**/hypotheses_*_veracium_*.jsonl"))
        paths = judged or plain
        if not paths:
            print("no realization files found in", VAR_DIR)
            return 1
        print(f"aggregating {len(paths)} realization files "
              f"({'judged' if judged else 'unjudged — answer/extraction agreement only'})")
        print(json.dumps(aggregate(paths), indent=2))
        return 0

    items, evals, _ = load(S_FILE, strict=True)
    picked = subset(items, evals)
    print(f"[variance] {len(picked)} questions x {REALIZATIONS} independent "
          f"realizations, fresh cache each", file=sys.stderr)
    for qid in [i.question_id for i in picked]:
        print(f"    {qid}  {evals[qid].question_type}"
              f"{'  [abstention]' if evals[qid].is_abstention else ''}", file=sys.stderr)

    out = []
    for r in range(1, REALIZATIONS + 1):
        d = VAR_DIR / f"r{r}"
        d.mkdir(exist_ok=True)
        print(f"\n[variance] realization {r}/{REALIZATIONS} (fresh cache)",
              file=sys.stderr)
        rec = run(picked, provider=_provider(args.provider), arm=args.arm,
                  arms=("veracium",), cache_enabled=True, context=True,
                  workers=args.workers, out_dir=d,
                  cache_path=d / "extractions.jsonl",
                  note=f"variance realization {r}/{REALIZATIONS}, arm {args.arm}")
        out.append(rec["results"]["veracium"]["hypotheses"])

    print("\n[variance] hypothesis files:")
    for p in out:
        print("   ", p)
    print("\nNow judge each, then re-run with --judge-only:")
    for p in out:
        print(f"    tests/longmemeval/judge.sh {p}")
    print(json.dumps(aggregate([Path(p) for p in out]), indent=2)[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
