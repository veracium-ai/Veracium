"""R2 sample draw — MS/TR stratified on session-day diversity.

    PYTHONPATH=src python tests/longmemeval/draw_r2.py

Deterministic and re-derivable by construction: fixed seed, sorted output, and
the item-set hash printed at the end is what goes into the freeze artifact. Run
it twice and you get the same hash, or the freeze means nothing.

**Why this draw exists.** The pilot's *scored* multi-session stratum had
session-day counts `[1, 1, 1, 1, 11, 11]` — **4 of 6 at minimum diversity,
against 23% (28/121) in the population.** That is what invalidated the
retrieval-collapse diagnosis: a coverage effect cannot show up on histories that
span a single day, and two thirds of the stratum spanned a single day. The draw
below fixes the *sampling*, not the metric.

**Bands are chosen from the population shape, not from convenience:**

  multi-session (n=121) is strongly BIMODAL — {1: 28, 9: 1, 10: 13, 11: 79}.
  There is no meaningful middle, so two bands.

  temporal-reasoning (n=127) is genuinely spread — 54 at one day, then a long
  tail to 38 (median 10). Three bands.

Equal draws per band, so the effect can be estimated **per band** rather than
averaged into a single number that hides where it came from. If coverage-aware
selection helps only on high-diversity histories, that is the finding, and a
proportional draw would have buried it.

Abstention items are excluded: they score in a separate bucket (`report.py`
routes `is_abstention` away from `per_type`), so including them would not test
the hypothesis.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from adapter import S_FILE, load, stratified_pilot

SEED = 20260801
PER_BAND = 6

BANDS = {
    "multi-session": (
        ("low", lambda d: d <= 1),
        ("high", lambda d: d >= 9),
    ),
    "temporal-reasoning": (
        ("low", lambda d: d <= 1),
        ("mid", lambda d: 2 <= d <= 15),
        ("high", lambda d: d >= 16),
    ),
}


def session_days(item) -> int:
    """Structural, model-facing metadata — no oracle content. The eval half is
    never consulted except for question_type, which selects the stratum and
    never reaches a provider."""
    return len({s.iso_day for s in item.sessions})


def draw(items, evals, *, seed: int = SEED, per_band: int = PER_BAND):
    rng = random.Random(seed)
    picked, detail = [], []
    for qtype, bands in BANDS.items():
        pool = [i for i in items
                if evals[i.question_id].question_type == qtype
                and not evals[i.question_id].is_abstention]
        for band_name, pred in bands:
            band = sorted((i for i in pool if pred(session_days(i))),
                          key=lambda i: i.question_id)
            take = rng.sample(band, min(per_band, len(band)))
            picked.extend(take)
            detail.append({
                "question_type": qtype, "band": band_name,
                "available": len(band), "drawn": len(take),
                "session_days": sorted(session_days(i) for i in take),
            })
    picked.sort(key=lambda i: i.question_id)
    return picked, detail


def item_set_hash(item_ids) -> str:
    """Order-independent, so the denominator cannot move without the hash
    moving. Same function the runner uses (`freeze.sha256_items`)."""
    return hashlib.sha256("\n".join(sorted(item_ids)).encode()).hexdigest()


def main() -> int:
    items, evals, _ = load(S_FILE, strict=False)
    picked, detail = draw(items, evals)
    ids = [i.question_id for i in picked]

    # exposure: what this draw costs the confirmatory set
    pilot = {i.question_id for i in stratified_pilot(items, evals)}
    already = [q for q in ids if q in pilot]

    print(f"seed={SEED}  per_band={PER_BAND}  items={len(ids)}")
    print()
    for d in detail:
        print(f"  {d['question_type']:<20} {d['band']:<5} "
              f"drawn {d['drawn']}/{d['available']:<3} days={d['session_days']}")
    print()
    print(f"  already exposed (in the 44-item pilot): {len(already)}"
          f"{' — ' + ', '.join(already) if already else ''}")
    print(f"  newly exposed, leaving the confirmatory set: {len(ids) - len(already)}")
    print()
    print(f"item_set_hash: {item_set_hash(ids)}")
    print()
    print(json.dumps({"seed": SEED, "per_band": PER_BAND,
                      "item_ids": ids,
                      "item_set_hash": item_set_hash(ids),
                      "bands": detail}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
