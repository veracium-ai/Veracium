# 0024 pre-implementation conflation baseline — EXPECTATIONS
## Committed BEFORE the probe set is run (no baseline unit has executed)

**2026-08-23, research.** The release gate for the 0024+0025(+selfcheck)
cut. Measures the L1 conflation on CURRENT MAIN (`1015e41`; src/ and
tests/ clean — dev's uncommitted edits are specs-only), which carries
0025's implemented vocabulary enforcement and deliberately NOT 0024's
fix — so post-fix movement attributes to 0024 alone. Extraction model
gpt-4.1-2025-04-14 @ temp 0 (the paper-2 case-study arm's config), one
replicate, per-probe raw records kept so the post-fix re-run pairs
probe-for-probe.

## The defect under measurement (accepted 0024 §1)

`_disclosure_for` (ingest.py:96) tests the RELATION before the AUTHOR:
a USER-authored event whose extracted triple is labeled
`third_party_claim` is quarantined as though a third party said it.
The accepted bound: a user CAN relay a genuine third-party claim, and
quarantining THAT is correct — the fix must move only the conflated
cell.

## Probe set (frozen at commit; 48 hand-written, lexically disjoint
from every paper-2 corpus)

- **Cell A (16): user-authored own-experience facts with third-entity
  bait** — the user is the witness; another entity (pet, relative,
  named service provider) appears in the claim. Class-matched to the
  L1 audit's real trigger shapes, freshly written.
- **Cell B (16): explicit relays** — "my landlord says I owe $500"
  shapes; the claim's voice is the third party, the user reports it.
- **Cell C (8): third-party-authored direct claims about the user**
  (trust canaries; includes one commitment-injection shape).
- **Cell D (8): plain user self-facts, no third entity** (controls).

## Measurements (store-level first — classify from artifacts; answers second)

Per probe: every resulting edge's (relation, original_relation,
disclosure, note) + episode disclosure, then one answer() call against
the probe's query with asserted/hedged/absent classification of the
claim's value.

## Pre-stated expectations

- **E-B24-1 (cell A, the defect):** >0 cell-A probes yield a
  `third_party_claim`-labeled edge from the USER-authored event, and
  EVERY such edge is QUARANTINED on main. No magnitude prediction (the
  P-A15-4(iii) lesson) — the trigger RATE is what the baseline exists
  to record. POST-FIX OBLIGATION: these exact probes' edges become
  grounded/assertable; movement reported probe-paired.
- **E-B24-2 (cell B):** relayed claims are quarantined on main, and
  POST-FIX MUST NOT MOVE — the fix preserves relay quarantine. Any
  cell-B movement post-fix is a regression finding, not progress.
- **E-B24-3 (cell C):** zero grounded edges; zero answers asserting
  the planted claim (the trust-canary / injection-asserts-0 contract),
  on main AND post-fix.
- **E-B24-4 (cell D):** user self-facts ground and assert on main AND
  post-fix (the fix must not loosen or tighten the plain path).

## What this baseline is NOT

Not a rate claim about production traffic (the corpus is bait-shaped
by design; the L1 audit's 3,945/41.5% figures over the extraction
cache remain the prevalence evidence). Not a paper-2 artifact. It is
the two-cell movement instrument the release gate names.


---

*Figure correction (2026-08-24, before these files entered the 0024-A1
review archive): the L1-census share cited above as "41.5%" is the
drifted pre-correction value; the shipped script's exact output is
**1,644 = 41.7%** of 3,945 (corpus_counts.py over cache `654e336a`,
re-derived at the 0026 internal review — the same drift 0026 §1 now
records as its thesis in miniature; this note is the carrier fix on the
research side). The 3,945 total and every measured number OF THIS
BASELINE are unaffected — the census figure was motivation context
only.*
