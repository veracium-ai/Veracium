"""Regenerate the worked adjudication example DETERMINISTICALLY
(0026-PACKAGE-R6-1: the README claimed a generator the package did not
ship — the packaged test only read the artifacts. This script IS the
generator now; the standing test runs it into a scratch directory and
requires byte-identical output to the shipped files, so the example can
never drift from the code that defines the current schema).

Everything is derived: the population from a fixed name series, the
schema number from measure_false_positives.ADJUDICATION_SCHEMA (the one
carrier of the current revision), the digests from the artifacts
themselves. Nothing here is a live measurement — see README.md.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import measure_false_positives as M          # noqa: E402

FIRES, TOTAL, FP_LABELLED = 120, 4000, 20    # 3.0%: over-gate, on purpose


def generate(out_dir: pathlib.Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    real = M._strict_json((HERE.parent / "fp_aggregate.json").read_text())
    pop = sorted(hashlib.sha256(f"demo-fire-{i}".encode()).hexdigest()
                 for i in range(FIRES))
    agg = dict(schema=3, lexicon_version=M.L.LEXICON_VERSION,
               fire_digests=pop,
               manifest=real["manifest"],    # the anchor names the CACHE;
               grounded_first_person=dict(   # the population is synthetic
                   total=TOTAL, fires=FIRES, fires_ambiguous_only=0,
                   suppressed_by_direction_only=0,
                   markers={"said": FIRES}, ambiguous_markers={},
                   suppressed_markers={}),
               coverage=dict(third_party_claim_triples=200,
                             with_nonempty_note=180,
                             matched_by_lexicon=20))
    (out_dir / "demo_aggregate.json").write_text(
        json.dumps(agg, sort_keys=True, indent=1) + "\n")
    lines = "".join(
        json.dumps({"fire": f, "label": ("fp" if i < FP_LABELLED
                                         else "tp")}) + "\n"
        for i, f in enumerate(pop))
    (out_dir / "fp_adjudication_sample.jsonl").write_text(lines)
    # the INDEPENDENT co-verification census (0026-EVIDENCE-R7-2):
    # concurs on all but one fire — the disagreement goes fp in the
    # fail-closed union, demonstrating the combination rule
    co_lines = "".join(
        json.dumps({"fire": f,
                    "label": ("fp" if i < FP_LABELLED + 1 else "tp")})
        + "\n"
        for i, f in enumerate(pop))
    (out_dir / "fp_coverification_sample.jsonl").write_text(co_lines)
    adj = dict(schema=M.ADJUDICATION_SCHEMA,
               lexicon_version=agg["lexicon_version"], fires=FIRES,
               sample=dict(size=FIRES),      # a census: size == fires,
               verdict="accept",             # no seed exists
               aggregate_sha256=hashlib.sha256(
                   (json.dumps(agg, sort_keys=True, indent=1) + "\n")
                   .encode()).hexdigest(),
               sample_sha256=hashlib.sha256(lines.encode()).hexdigest(),
               coverification_sha256=hashlib.sha256(
                   co_lines.encode()).hexdigest())
    (out_dir / "fp_adjudication.json").write_text(
        json.dumps(adj, indent=1) + "\n")
    return agg


if __name__ == "__main__":
    out = (pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE)
    agg = generate(out)
    probs = M.validate_aggregate(
        agg, adj_path=out / "fp_adjudication.json")
    print("\n".join(probs) if probs else
          f"example generated into {out} and VALID")
    raise SystemExit(1 if probs else 0)
