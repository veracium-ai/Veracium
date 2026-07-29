# LongMemEval V1-S adapter

Implements `proposals/longmemeval-adapter-dev-spec.md` (v3, externally
reviewed twice). Dataset is **not** committed — download to
`~/Datasets/longmemeval/` (see `adapter.DATA_DIR`).

    PYTHONPATH=src python tests/longmemeval/run_longmemeval.py --pilot --workers 8
    PYTHONPATH=src python tests/longmemeval/run_longmemeval.py --limit 2   # wiring smoke

Offline tests (no dataset, no provider): `pytest tests/test_longmemeval.py`.

## Pieces

- `adapter.py` — loader + **oracle-annotation firewall**: model-facing `Item`
  (role/content only) vs evaluation-only `Eval` (`has_answer`,
  `answer_session_ids`, `question_type`, gold answer). Separate types, so a
  leak is a `TypeError`. Also: official date-sorted ordering, day-granularity
  precedence invariant, stratified pilot sampler.
- `cache.py` — `CachedComplete`: extraction cache keyed on the full extraction
  identity (content hashes of prompt + schema, model, decoding, serializer and
  context policy, author, event type, date). Thread-safe; single-process lock
  file. Replayable, not statistically reproducible — see the spec's variance
  protocol.
- `run_longmemeval.py` — per-turn ingestion with the versioned
  `[CONTEXT]`/`[CURRENT TURN]` serialization, assistant-trust arms (T/C),
  control arms (veracium / no-memory / bare-model), item-level parallelism,
  official hypothesis-file output.

Judging is deliberately **not** implemented here: emit hypotheses, then run the
benchmark's own `evaluate_qa.py gpt-4o <hyp> <data>` unmodified.

## Measured facts (S file, 2026-07-29)

500 instances · 23,867 session refs / **19,195 unique** (~20% sharing) ·
**246,750 turns** · 30 abstention items · 13 instances repeat a session id
(disclosed deviation, see `adapter._build`) · 1,475 sessions across 76
instances sit on the question's own day at a later clock time (why the
precedence invariant is day-level).

**Cost shape measured with the `claude` CLI provider:** ~18s/turn serial,
~5.5s/turn effective at 8 workers (sublinear: one process per call). At that
rate the 44-item pilot is ~24h and the full 500 ~270h — so a canonical run
needs an API-based extractor with real concurrency, not the CLI. Pin whatever
is used in the run record.
