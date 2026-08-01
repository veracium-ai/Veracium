experiment_name: coverage-selection-balanced
arm_name: mmr-coverage-on
baseline_arm: current-selection (relevance-ranked subgraph, 0.4.2 behaviour)

approved_by: research
approved_at: 2026-08-01T14:38:03Z
supersedes: coverage-selection-balanced-02.md
  (sha256 7fa8ff64f3ef55a8bedf25cd38541b2b842a2c8680a5f8a3bb5bc9d84bfbaf40)
  which superseded coverage-selection-balanced-01.md
  (sha256 2891c2183d1eecfe61ada12a99c0ca78fa48b222b72b16915b87a160a3d660dd)

supersede_reason_03: >
  -02 CARRIED A FABRICATED APPROVAL TIMESTAMP. Its approved_at read
  2026-08-01T15:10:00Z; the file was written at 14:07:39Z and committed at
  14:07:51Z, so the approval claimed to precede the run by an hour that had
  not happened yet. I did not run `date -u` for -02 -- I carried a time
  forward from my own coordination-entry labels, which is the practice the
  project standing rule forbids ("run `date -u` and use that, never a date
  assumed from context"). This timestamp is now verified against the clock at
  the moment of writing.
  WHY THIS IS NOT A TYPO FIX. The verifier's third check is that approved_at
  is strictly earlier than run start. A future-dated approval passes that
  check while asserting the file was approved at a time it did not exist in
  that form -- the artifact would have certified its own integrity property
  using a value that was not measured. That is the failure mode freezes exist
  to prevent, so it gets a new file and a new hash like any other amendment.
  NO OUTCOME HAS BEEN INSPECTED and no run has started, so this remains
  CONFIRMATORY. item_set_hash is UNCHANGED; no redraw. All experimental
  content below is byte-identical to -02 apart from these two blocks.

supersede_reason: >
  The -01 pre-run check fired. -01 justified the negative control as "little to
  select across" on single-session-day items; that is FALSE — all 12 low-band
  items carry 41-51 sessions on their single day, and session counts are flat
  across every band (LOW median 46, MID/HIGH median 47). The control survives
  for a different and stronger reason (see negative_control), but the check
  -01 froze was a BAD PROXY for the mechanism, so this is a new device, not a
  corrected reading of the old one.
  NO OUTCOME HAS BEEN INSPECTED. Dev characterised item-set structure only —
  session counts, raw timestamps — never a run result. This run therefore
  remains CONFIRMATORY.
  item_set_hash is UNCHANGED: the draw was correct, only its rationale and
  labelling were wrong. No redraw.

# --- hypothesis -------------------------------------------------------------

hypothesis: >
  Coverage-aware selection raises necessary-evidence coverage on items whose
  facts span several distinct valid_from days. Direction: coverage UP on the
  high-diversity stratum. The pilot could not test this — its scored
  multi-session stratum had 4 of 6 items at minimum diversity against 23% in
  the population.

expected_direction: >
  Positive on the high-diversity stratum. EXACTLY ZERO on the low stratum —
  not merely null. See negative_control.

# --- metrics ----------------------------------------------------------------

primary_metric:
  name: answer-turn hit rate (coverage hierarchy level 2)
  definition: >
    Per item, the fraction of answer-bearing turns retrieved, where a turn
    counts as retrieved when at least one recalled record's evidence_ref
    matches a turn marked has_answer. evidence_ref = session_ref#turn_index.
    CONTINUOUS per item in [0,1] — not a binary improved/not.
  NOT: the 44-item end-to-end score.

secondary_metrics:
  - distinct-session coverage
  - read tokens (context)
  - irrelevant-context rate
  - final-answer correctness — REPORTED, NEVER DECIDING

# --- item set (UNCHANGED from -01) ------------------------------------------

item_set:
  n: 30
  draw: tests/longmemeval/draw_r2.py, seed 20260801, sorted output
  source_commit: 114ad82
  item_set_hash: e6dee16fb576a13a9ac34ab7dcd6183b73bfc068ad37fd1d48cf6b8e13d1d939
  stratification_variable: >
    RENAMED. -01 called this "session-days". That label is misleading: session
    COUNTS are flat across all bands (41-51 everywhere), so the bands do not
    differ in how much material an item has. What differs is the number of
    distinct DAYS the material falls on — which is the variable the code
    actually branches on. Bands are unchanged; only the name is corrected.
  bands:
    multi-session/low:        {n: 6, distinct_days: [1,1,1,1,1,1]}
    multi-session/high:       {n: 6, distinct_days: [10,11,11,11,11,11]}
    temporal-reasoning/low:   {n: 6, distinct_days: [1,1,1,1,1,1]}
    temporal-reasoning/mid:   {n: 6, distinct_days: [5,6,10,14,14,14]}
    temporal-reasoning/high:  {n: 6, distinct_days: [16,21,22,24,25,36]}

exposure:
  status: confirmatory
  overlap_with_pilot: 0
  ledger_effect: confirmatory set 445 -> 415 (all 30 newly exposed)
  recorded_before_run: REQUIRED — G1, before the first paid call.

# --- analysis plan ----------------------------------------------------------

analysis_plan:

  unit_of_analysis: unique item.

  replicate_handling: >
    3 replicates per item per arm, AVERAGED to a per-item mean per arm, then
    the paired per-item delta is computed. Replicates absorb matched-run
    instability; they are not a voting mechanism. (Supersedes the ">=2/3
    replicates improve" rule in the worked example of
    proposals/freeze-artifact-spec.md, which binarizes twice and discards most
    of the signal at this n.)

  strata: >
    THREE STRATA, ANALYSED SEPARATELY, NEVER POOLED INTO ONE NUMBER.

  primary_test:
    stratum: pooled high-diversity = multi-session/high + temporal-reasoning/high
    n: 12
    test: two-sided sign test on per-item paired deltas; Wilcoxon signed-rank
      reported alongside.
    decision_thresholds (pre-computed; no post-hoc choice of test):
      10/12 improve -> p = 0.0386
      11/12 improve -> p = 0.0063
      12/12 improve -> p = 0.0005
       9/12 improve -> p = 0.1460  (NOT sufficient)

  secondary_descriptive:
    stratum: temporal-reasoning/mid, n = 6. ESTIMATE ONLY, with uncertainty.
      No hypothesis test.

  negative_control:
    stratum: multi-session/low + temporal-reasoning/low, n = 12
    expectation: THE PAIRED DELTA IS EXACTLY ZERO.
    justification (structural, verified in code, not empirical): >
      graph._cover clusters on `e.valid_from.date()`, and its docstring states
      why: "session identity is a host concept that most callers never supply,
      so a session-based rule would be unimplementable outside a benchmark
      harness." With every edge on ONE valid_from day: the head is filled by
      relevance; `seen_days` then contains that single day; the first pass
      admits nothing because no candidate has an unseen day; and the backfill
      fills the reserve by relevance order. The output is therefore
      BIT-IDENTICAL to pure top-k. The treatment arm does not merely have
      little to do — it provably does nothing.
    interpretation: >
      Because the arms are identical by construction, a NONZERO delta here is
      not a weak effect and not noise — it is PIPELINE NONDETERMINISM (sampling,
      cache state, ordering). It must be quantified and explained BEFORE any
      number from the primary stratum is read, because it bounds how much of a
      primary-stratum delta is attributable to the same nondeterminism.
      This stratum is therefore a DETERMINISM CHECK, which is a stronger
      instrument than the defect signal -01 specified.

  REQUIRED_PRE_RUN_MEASUREMENT: >
    Measure and record DISTINCT valid_from DAYS PER ITEM, after extraction, for
    all 30 items. Do NOT infer it from session dates.
    Reason: -01 froze a check on sessions-per-day, which is a proxy, and the
    proxy was wrong. valid_from is the variable _cover branches on, and it is
    NOT guaranteed to equal the session date — a fact carrying a stated date
    ("since January") takes that date instead. If any low-band item has more
    than one distinct valid_from day, the inertness argument fails FOR THAT
    ITEM and it is excluded from the negative control, recorded, before
    outcomes are seen.
    Measure the variable the code branches on, not a proxy for it.

  per_band_inference: >
    OUT OF REACH, STATED IN ADVANCE. At n=6 no sign or rank test can produce
    p < 0.031, and only under unanimity. Per-band results are estimates with
    stated uncertainty; no per-band p-value will be reported.

  denominators: end-to-end (all 30) AND the evidence-available subset.

mapping_procedure: >
  An item counts as covered when >=1 recalled record's evidence_ref matches a
  turn marked has_answer. Frozen before outcomes; no post-hoc adjustment.

# --- interpretation limits (FROZEN, must appear in any write-up) ------------

interpretation_limits:
  adapter_deviation: >
    The low band's single valid_from day is partly an artifact of OUR adapter,
    not of the benchmark. The raw data carries 41-51 distinct timestamps on
    that day; we store day-granular dates because remember(date=...) is
    day-granular — our disclosed deviation. A different adapter choice would
    produce a different low band.
    CONSEQUENCE: a null on the negative control is evidence about DAY-CLUSTERED
    COVERAGE SELECTION UNDER DAY-GRANULAR STORAGE, not about coverage selection
    in general. This limit is frozen so it appears in the write-up rather than
    being found by a reviewer.

# --- thresholds -------------------------------------------------------------

thresholds:
  minimum_improvement: +10pp answer-turn hit rate, mean over the primary
    stratum, AND >=10/12 items improving. Both, not either.
  material_precision_loss: >5pp rise in irrelevant-context rate
  read_cost_ceiling: +25% context tokens
  cost_ceiling:
    procedure: run 2 items end-to-end first; record observed marginal cost per
      item-run in the run manifest before the remaining 178.
    abort: projected total >50% over the recorded estimate -> abort and
      re-approve. The original $3-6 queue estimate is WITHDRAWN; do not quote it.

# --- stop rules -------------------------------------------------------------

stop_rules:
  - If coverage rises on the primary stratum and the primary metric does not,
    the coverage hypothesis is FALSIFIED for this arm. Report and stop. Do not
    tune.
  - If the negative control shows a nonzero delta, quantify and explain it
    before reading the primary stratum.
  - If <10/12 improve on the primary stratum, the result is a null. A null is
    reportable, not a reason to redraw, resize, or re-band.
  - Sample size and item set are frozen. Any further change requires -03 with
    supersedes:, and if any outcome has been inspected by then, the resulting
    run is exploratory.
