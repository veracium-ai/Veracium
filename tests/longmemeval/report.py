"""Turn judged hypothesis files into the internal report (spec §12).

    PYTHONPATH=src python tests/longmemeval/report.py \
        ~/Datasets/longmemeval/runs/hypotheses_*_veracium_C.jsonl.eval-results-gpt-4o \
        [more arms...]

Reports, in the order the spec asks for them:
  1. per-question-type accuracy with RAW numerators/denominators (knowledge-update
     and abstention first — the differentiated claims); no confidence intervals,
     because pilot-scale sampling does not support them
  2. control-arm deltas (veracium vs no-memory vs bare-model)
  3. read cost (context tokens per answer, an estimate — labeled as one)
  4. failure taxonomy on misses, when the run persisted rendered context:
       extraction-miss  the answer's distinctive tokens never reached memory
       recall-miss      they are in memory but not in the recalled context
       answer-miss      they were in the context and the answer still missed
     A coarse lexical split, deliberately: it is a triage signal for where to
     look, not a measurement.

Reads gold answers from the dataset via the evaluation-only half of the loader,
so nothing here can leak into a model path — this file never touches a provider.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from adapter import QUESTION_TYPES, S_FILE, load
from manifest import eligibility_for_output, explain_ineligibility

_WORD = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "on",
         "for", "and", "or", "at", "by", "with", "that", "this", "it", "as",
         "from", "user", "you", "your", "they", "their", "has", "have", "had",
         "will", "would", "about", "there", "then", "than", "been", "be"}


def _content_tokens(text) -> set[str]:
    # gold answers are not always strings — some are numbers (temporal
    # reasoning: "18") and those carry no long content tokens at all
    return {w for w in _WORD.findall(str(text).lower())
            if w not in _STOP and len(w) > 3}


def _pct(n: int, d: int) -> str:
    return f"{n}/{d} ({n / d * 100:5.1f}%)" if d else f"0/0 ( n/a )"


def load_arm(path: Path) -> tuple[str, dict]:
    """Label a column. control_arm alone is not unique — the trust arms and the
    retrieval-breadth ablation are all control_arm='veracium' — so the trust arm
    (from the filename) and any max-edges note are folded into the label."""
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    control = rows[0].get("control_arm", "?") if rows else "?"
    m = re.search(r"_(veracium|no-memory|bare-model)_([TC])\.jsonl", path.name)
    label = control if control != "veracium" else f"veracium-{m.group(2)}" if m else control
    # disambiguate an ablation run of the same arm by its stamp
    stamp = re.search(r"hypotheses_(\d{8}T\d{6})", path.name)
    return (label, stamp.group(1)[-6:] if stamp else ""), {r["question_id"]: r for r in rows}


def taxonomy(row: dict, gold: str) -> str:
    """Coarse triage for a miss. Needs the run to have persisted `context`."""
    ctx = row.get("context")
    if not ctx:
        return "unclassified (no context persisted)"
    want = _content_tokens(gold)
    if not want:
        return "unclassified (no distinctive answer tokens)"
    in_ctx = len(want & _content_tokens(ctx)) / len(want)
    if in_ctx >= 0.5:
        return "answer-miss (evidence was in context)"
    if row.get("recalled", {}).get("edges"):
        return "recall-miss (memory populated, context lacked it)"
    return "extraction-miss (nothing relevant recalled)"


def main(paths: list[str]) -> int:
    _, evals, manifest = load(S_FILE, strict=False)
    loaded = [load_arm(Path(p)) for p in paths]
    # keep labels unique: append the run stamp only when a label repeats
    counts = {}
    for (lab, _), _rows in loaded:
        counts[lab] = counts.get(lab, 0) + 1
    arms = {}
    for (lab, stamp), rows in loaded:
        arms[lab if counts[lab] == 1 else f"{lab}@{stamp}"] = rows
    if not arms:
        print("no arms given")
        return 1

    primary = "veracium" if "veracium" in arms else next(iter(arms))
    ids = sorted(arms[primary])

    print(f"\nLongMemEval V1-S — pilot report ({len(ids)} items)")
    print(f"dataset: {manifest['instances']} instances, "
          f"{manifest['turn_refs']} turns, {manifest['unique_sessions']} unique sessions")

    # -- 0. decision eligibility, before any number --------------------------
    # Printed first and unconditionally. The point of the policy is that "we
    # should have checked whether this run could support the claim" becomes
    # something the tool says out loud, at the top, every time.
    print("\ndecision eligibility (G16/G19):")
    for p in paths:
        # judged files are "<hypotheses>.eval-results-<judge>"; the attestation
        # hashes the hypothesis file the RUN wrote, so strip the judge suffix
        base = re.sub(r"\.eval-results-.*$", "", str(p))
        verdict = eligibility_for_output(base, Path(base).parent)
        if verdict is None:
            print(f"  {Path(base).name}: UNATTESTED — predates the run manifest, "
                  f"or its attestation is missing. Not the same as ineligible: "
                  f"eligibility is unknown and cannot be assumed either way.")
            continue
        eligible, detail = verdict
        print(f"  {Path(base).name}: "
              f"{'DECISION-ELIGIBLE' if eligible else explain_ineligibility(detail)}")

    # -- 1. per-type, differentiated claims first ---------------------------
    order = ["knowledge-update", "single-session-preference", "temporal-reasoning",
             "single-session-user", "single-session-assistant", "multi-session"]
    order = [t for t in order if t in QUESTION_TYPES]
    print(f"\n{'question type':<28}" + "".join(f"{a:>22}" for a in arms))
    per_type: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    abst: dict[str, list[int]] = defaultdict(list)
    for qid in ids:
        ev = evals.get(qid)
        if ev is None:
            continue
        for arm, rows in arms.items():
            row = rows.get(qid)
            if not row or "autoeval_label" not in row:
                continue
            ok = 1 if row["autoeval_label"]["label"] else 0
            (abst[arm] if ev.is_abstention else per_type[ev.question_type][arm]).append(ok)
    for t in order:
        line = f"{t:<28}"
        for arm in arms:
            v = per_type[t][arm]
            line += f"{_pct(sum(v), len(v)):>22}"
        print(line)
    line = f"{'abstention (_abs)':<28}"
    for arm in arms:
        line += f"{_pct(sum(abst[arm]), len(abst[arm])):>22}"
    print(line)
    line = f"{'ALL':<28}"
    for arm in arms:
        allv = [x for t in per_type for x in per_type[t][arm]] + abst[arm]
        line += f"{_pct(sum(allv), len(allv)):>22}"
    print(line)

    # -- 2. control deltas ---------------------------------------------------
    if len(arms) > 1 and primary in arms:
        print("\ncontrol deltas (percentage points vs veracium):")
        base = [x for t in per_type for x in per_type[t][primary]] + abst[primary]
        base_acc = sum(base) / len(base) * 100 if base else 0
        for arm in arms:
            if arm == primary:
                continue
            v = [x for t in per_type for x in per_type[t][arm]] + abst[arm]
            acc = sum(v) / len(v) * 100 if v else 0
            print(f"   {arm:<16} {acc:5.1f}%  ({acc - base_acc:+.1f} pp)")

    # -- 3. read cost --------------------------------------------------------
    ctx = [r.get("context_tokens_estimated", 0) for r in arms[primary].values()]
    ctx = [c for c in ctx if c]
    if ctx:
        ctx.sort()
        print(f"\nread cost ({primary}): median {ctx[len(ctx) // 2]} context tokens "
              f"(ESTIMATE, chars/4), max {ctx[-1]}")
    ing = [r.get("ingested", {}).get("facts", 0) for r in arms[primary].values()]
    if any(ing):
        ing.sort()
        print(f"facts written per item: median {ing[len(ing) // 2]}, max {ing[-1]}")

    # -- 4. failure taxonomy -------------------------------------------------
    misses = defaultdict(list)
    for qid in ids:
        row, ev = arms[primary].get(qid), evals.get(qid)
        if not row or not ev or "autoeval_label" not in row:
            continue
        if not row["autoeval_label"]["label"]:
            misses[taxonomy(row, ev.answer)].append(qid)
    if misses:
        print(f"\nfailure taxonomy ({primary}, {sum(len(v) for v in misses.values())} misses):")
        for kind, qids in sorted(misses.items(), key=lambda kv: -len(kv[1])):
            print(f"   {kind:<45} {len(qids):3d}   e.g. {', '.join(qids[:3])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
