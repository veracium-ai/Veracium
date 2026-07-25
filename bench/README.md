# bench/ — internal benchmark suite

Measures **the contract** (trust routing, supersession, abstention, duplication
drift) and **the engine's own overhead**, and records one JSON line per run in
`results.jsonl` so releases diff against a baseline. Internal instrument, not a
marketing artifact — external benchmarks (LoCoMo/LongMemEval) measure
category-comparable retrieval; this measures what they can't see.

```bash
PYTHONPATH=src python bench/run_bench.py              # engine tier (free, fake LLM)
PYTHONPATH=src python bench/run_bench.py --live       # + acceptance eval + robustness/T0
PYTHONPATH=src python bench/run_bench.py --compare    # regression gate (last 2 records)
```

- **engine** tier: zero-latency scripted model isolates veracium's code from
  model latency. Timing is machine-relative — compare records from one machine.
- **robustness** tier runs `--s4-samples 50` with duplicate-shape
  classification (subset/reorder/paraphrase) — the value-equivalence **T0**
  measurement.
- Thresholds live at the top of `run_bench.py`: hard metrics (injection
  asserts, leaks, crashes) fail the compare; soft metrics (latency, dup-rate,
  correctness ratio) flag beyond tolerance bands.
- `results.jsonl` is committed: aggregates only, content-free.

**Release checklist**: run `--live`, then `--compare`. No release with a hard
failure; soft flags need a written justification in the release notes.
