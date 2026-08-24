# The 0024 conflation baseline — provenance

Research's frozen 48-probe paired measurement, shipped at the external
reviewer's round-14 standing request ("a digest-bound copy of
RESULTS_POSTFIX.md, the frozen 48-probe classification matrix, and the
measurement harness that supports the 4:1 result"). Cleared for the
archive by research 2026-08-24: every probe is hand-written synthetic
bait, lexically disjoint from every gated corpus by construction; the
records are model outputs about those synthetic facts; the only gated-
corpus references are aggregate counts in prose (the counts-only rule).

The evidentiary chain is PAIRED, so both halves ship:
EXPECTATIONS.md (its commit, research repo `261c0b95`, PRE-DATES the
first baseline record — expectations were committed before any run) →
RESULTS.md + baseline_main_records.jsonl (pre-fix, main @ `1015e41`) →
RESULTS_POSTFIX.md + postfix_records.jsonl (post-fix, main @ `1b542b9`,
probe-paired). `probes.jsonl` is the frozen 48-probe matrix;
`run_baseline.py`/`run_postfix.py` are the harness.

Canary-subject records (added at round 15, EVIDENCE-R15-1): the
canary floor is artifact-verified BY THE SHIPPED 2026-08-24 records
(`canary_subject_records.jsonl`; chain and the one disclosed benign
drift in `CANARY_SUBJECTS.md`, research repo `fd3a6170`). The
2026-08-23 subject re-run printed to stdout and persisted nothing — it
is corroborating history in the research session transcript, NOT
shipped evidence; the fresh run agrees with it on every subject.
`validate_baseline.py` (also added this round) recomputes the summaries
and the five load-bearing movements from the shipped JSONL offline.

Figure-correction note: RESULTS.md and EXPECTATIONS.md carry research's
dated correction (`6f548f09`, 2026-08-24) moving the motivating L1
census citation to the script's exact output (1,644 = 41.7%) — the same
drift 0026's §1 records; the baseline's own measured numbers are
unaffected (the census was motivation context only).

DIGESTS.sha256 binds every file; verify with
`sha256sum -c DIGESTS.sha256` from this directory.
