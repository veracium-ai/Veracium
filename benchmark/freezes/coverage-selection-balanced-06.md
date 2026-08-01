experiment_name: coverage-selection-balanced
arm_name: mmr-coverage-on
baseline_arm: current-selection (relevance-ranked subgraph, 0.4.2 behaviour)

approved_by: research
approved_at: 2026-08-01T18:08:15Z
supersedes: coverage-selection-balanced-05.md
  (sha256 59df127d7c34f8c60e0fb52143ded45492c967b24e97a62c1dd938f6ae74fd6e)
  which superseded coverage-selection-balanced-01.md
  (sha256 2891c2183d1eecfe61ada12a99c0ca78fa48b222b72b16915b87a160a3d660dd)

supersede_reason_06: >
  -05 CLOSED ONE OF THREE GAPS. It added arm_config and missed `environment`:
  the models and the code under test were unfrozen, verified as zero mentions of
  gpt-4 / model: / extractor_model across ALL FIVE freezes including -05. And
  the single `source_commit: 114ad82` names the DRAW SCRIPT, sitting inside the
  item_set block -- it describes how items were chosen, not what code runs them.
  WE HAVE ALREADY BEEN BITTEN BY THIS UNDER ANOTHER NAME. The "matched pair"
  straddling ce66282 was two runs compared across a retrieval change. A protocol
  frozen against unspecified code is that same defect, declared in advance
  rather than discovered afterwards.
  THE STRUCTURAL DIAGNOSIS, WHICH IS DEV'S AND IS THE USEFUL PART. Read the
  required-content list as a set: hypothesis, metrics, thresholds, analysis
  plan, mapping, item set, exposure, stop rules, approvals. EVERY ENTRY IS
  ABOUT MEASUREMENT AND INFERENCE. NOT ONE IS ABOUT THE SYSTEM BEING MEASURED.
  That is the section-1 ownership split showing through: I wrote a spec that
  covers my half comprehensively and is silent on the half I do not own. -05
  patched an instance of that; -06 closes the category.
  item_set_hash UNCHANGED. No outcome inspected. Still CONFIRMATORY.

supersede_reason_05: >
  THE TREATMENT WAS NEVER SPECIFIED. -01 through -04 froze the hypothesis,
  metrics, thresholds, analysis plan, mapping, item set, exposure and stop
  rules -- and none of them stated `subgraph_coverage_share` for the treatment
  arm. Baseline was pinned only by prose ("0.4.2 behaviour"); the treatment
  carried a name and no number. Verified: zero mentions of coverage_share,
  subgraph_coverage, max_subgraph_edges or arm_config across all four files.
  THE ROOT CAUSE IS IN THE FREEZE SPEC, NOT IN THESE FILES. The required-content
  table of proposals/freeze-artifact-spec.md has eleven rows and no row for arm
  configuration, which is why the omission survived four rounds of review by
  both sessions. Fixing the instance without fixing the spec would guarantee a
  repeat, so the spec gains the row in the same change.
  Dev's framing, kept because it generalises: G15 made us able to prove what a
  run DID -- the manifest's requested/resolved/observed triple -- and nothing
  made us declare in advance what it SHOULD do. The manifest could have proved,
  precisely, that we ran a configuration nobody specified.
  item_set_hash UNCHANGED. No outcome inspected. Still CONFIRMATORY.

supersede_reason_04: >
  THE EXPOSURE LEDGER CAUGHT A PRIOR EXPOSURE ON ITS FIRST USE. draw_r2
  computed prior exposure against the 44-item pilot alone and missed the
  variance protocol's subset, which had already burned `6613b389`. R2 therefore
  newly exposes 29, not 30; confirmatory goes 445 -> 416, not 415.
  `6613b389` STAYS IN THE ITEM SET. Verified independently from the dataset
  rather than accepted: temporal-reasoning, 41 sessions, ONE distinct day ->
  TR-LOW band. It is therefore NOT in the primary confirmatory test, which is
  the pooled high-diversity stratum (MS-high + TR-high). It sits in the
  determinism check, which -03 establishes as a stratum where the treatment arm
  is PROVABLY INERT -- bit-identical to pure top-k -- so the measurement has no
  free parameter, nothing to tune toward, and no judgement to bias. A redraw
  would change item_set_hash and cost a fifth freeze to remove an item that
  cannot affect the conclusion.
  Secondary and deliberately not load-bearing: the freeze predates the
  discovery, so no tuning toward this item was possible. That is an argument
  about intent; the structural argument above is the one that decides it.
  TWO CONDITIONS, both binding -- see negative_control and reporting.
  item_set_hash UNCHANGED. No outcome from THIS experiment has been inspected,
  so R2 remains CONFIRMATORY for its own hypothesis. All experimental content is
  byte-identical to -03 apart from this block, the timestamp, the exposure
  figures, and the two conditions.

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
  source_commit: 114ad82        # the DRAW SCRIPT; code under test is in environment:
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
  ledger_effect: confirmatory set 445 -> 416 (29 newly exposed, not 30)
  previously_exposed_items:
    - id: 6613b389
      band: temporal-reasoning/low
      prior_event: variance protocol (3 realizations); outcome WAS observed
      disposition: retained; see supersede_reason_04 and the two conditions
  recorded_before_run: REQUIRED — G1, before the first paid call.

# --- arm configuration (NEW in -05; the treatment, stated) ------------------

arm_config:
  baseline:
    subgraph_coverage_share: 0.0        # the shipped default = "0.4.2 behaviour"
    max_subgraph_edges: 40              # pinned explicitly, not by default
  treatment_primary:
    name: mmr-coverage-on
    subgraph_coverage_share: 0.25
    max_subgraph_edges: 40

  rationale_for_0_25: >
    Mechanical, from graph._cover: reserve = int(max_edges * share), head =
    max_edges - reserve. At 40 edges: 0.10 -> reserve 4, 0.25 -> reserve 10,
    0.50 -> reserve 20.
    The primary stratum's distinct-day counts are MS-high [10,11,11,11,11,11]
    and TR-high [16,21,22,24,25,36]. A reserve of 4 can admit at most 4 unseen
    days, a small fraction of those counts, so 0.10 is UNDER-POWERED BY
    CONSTRUCTION -- it could fail the +10pp threshold even if the mechanism
    works exactly as hypothesised. A reserve of 20 spends half the budget on
    coverage and is the arm most likely to trip the >5pp irrelevant-context
    abort. A reserve of 10 is where the mechanism can express itself on the
    primary stratum without gutting relevance.

  DISCLOSED BIAS, stated before the run rather than conceded after: >
    A reserve of 10 approximately MATCHES MS-high's distinct-day count (10-11).
    Choosing it is therefore choosing the value most favourable to the
    hypothesis on half the primary stratum. That is a real selection effect and
    the dose arms below exist to bound it. If 0.25 improves coverage and 0.10
    and 0.50 do not, the honest report is a NARROW, TUNED effect -- not a
    general one -- and it must be written that way.

  dose_arms (EXPLORATORY, reported, never tested):
    - subgraph_coverage_share: 0.10
    - subgraph_coverage_share: 0.50
    status: >
      Run at 3 replicates each, reported as dose-response context. They carry
      NO hypothesis test and NO multiplicity correction is applied, because
      correcting for them would cost the primary test power it does not have
      (see per_band_inference). Pre-declaring them as exploratory is what keeps
      that legitimate.
    why they are worth ~$0.82: >
      A null on the primary invites "you should have used a larger reserve",
      and with a single arm nothing in the record could answer it. Extraction
      is one-time and shared across all arms, so the dose arms cost the answer
      path alone.

  effective_config_check: >
    The manifest's requested/resolved/observed triple must match these values
    for every arm. max_subgraph_edges is pinned explicitly BECAUSE its
    requested-vs-effective mismatch produced the invalid ablation once already;
    leaving it implicit is exactly how that happened.

cost:
  projection: ~$10.4 (extraction $8.80 one-time and shared + 12 arm-runs ~$1.64)
  basis: >
    The pilot's own run records -- 44 items, 13,136 fresh extractions, $12.91,
    i.e. $0.293/item -- not a 2-item probe. A larger and more representative
    sample than the probe would have given. The withdrawn $3-6 figure must not
    be quoted.
  supersedes_procedure: >
    -04's "2-item cost probe" is WITHDRAWN. Dev established it is a worse
    estimator than the pilot records already in hand, and it ran at 0.22
    extractions/s serially. Use --workers 8; serial is ~11h and not an option.

# --- environment (NEW in -06; the system under test) ------------------------

environment:
  code_under_test:
    repo: veracium
    commit: 10aec7f
    dirty_fingerprint: REQUIRED IN THE MANIFEST. A commit alone is, in dev's
      words, "a more confident lie than no commit" when the working tree does
      not match it -- most of this week's experiments ran from such a tree.
  models:
    extractor / distill: gpt-4.1-mini-2025-04-14
    answer / compile / gate: gpt-4.1-2025-04-14
    judge: gpt-4o-2024-08-06        # official LongMemEval pin
  decoding:
    temperature: 0.0
    max_tokens: 4096
  dataset:
    name: longmemeval_s_cleaned.json
    hash: RECORDED BY THE MANIFEST at run time and compared; not restated here,
      because a hash copied by hand is a hash that can be copied wrong.

  no_value_may_read "default": >
    Concrete values only. Defaults move between versions, so a freeze reading
    "0.4.2 behaviour" silently means something else after 0.5.0 and the frozen
    prediction then describes a configuration nobody can reconstruct. Adopted
    from dev's (b); it applies to `environment` exactly as it does to
    `arm_config`.

  deliberately NOT pinned, said explicitly rather than by silence: >
    Provider-side model weights behind a dated alias, and OS/library versions.
    We cannot pin them and should not imply we can. If a result ever hinges on
    one, that is a finding about reproducibility, not a footnote.

  cross_check: >
    Same mechanism as arm_config (dev's part (c), shipped 661b3c6): the freeze
    declares INTENDED, the manifest records ACTUAL, the runner compares before
    the first paid call. A run whose observed environment contradicts this
    block ABORTS -- see the abort-versus-downgrade ruling in the coordination
    entry accompanying this freeze.

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
    CONDITION A -- previously-exposed item. `6613b389` is in this stratum and
      its outcome was observed during the variance protocol. It is retained,
      and it MUST be flagged as previously exposed in the reported results
      table, not only in the exposure ledger. A reader must be able to see
      which items were exposed without opening another document; silent
      inclusion is what erodes a held-out claim.
    CONDITION B -- PRE-DECLARED BRANCH, fixed now precisely because deciding it
      after seeing the number would be unfalsifiable. IF the determinism check
      returns a NONZERO delta, then this stratum has produced a FINDING rather
      than a mechanical zero, and an item whose outcome is already known is no
      longer merely mechanical. In that case `6613b389` is reported separately
      and EXCLUDED from the nondeterminism bound applied to the primary
      stratum. If the delta is exactly zero, no exclusion applies and the
      retention costs nothing.

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
    procedure: SUPERSEDED -- see cost: above. The projection is $10.4, derived
      from the pilot's run records. Record observed cost in the manifest as the
      run proceeds.
    abort: actual total >50% over $10.4 -> abort and re-approve.

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
