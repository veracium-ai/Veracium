# 0024 conflation baseline — RESULTS (pre-fix, main @ 1015e41)

**2026-08-23.** 48/48 probes, one replicate, gpt-4.1 @ temp 0. Dirty-tree
note: `tests/test_collected_header.py` (dev's C-plus work) was modified
mid-window; `src/` byte-clean at HEAD throughout — the measured surface
is intact. Raw per-probe records: `baseline_main_records.jsonl` (the
post-fix re-run pairs probe-for-probe against these).

## Expectations scored

- **E-B24-1 (the defect cell) HELD — at a rate that is itself the
  finding.** Exactly **1/16** cell-A probes triggered the conflation
  (A08, "my neighbor's oak tree…" → `third_party_claim`, QUARANTINED);
  the other 15 grounded. The L1 audit's historic trigger surface
  (41.5% of 3,945 cache triples) does NOT reproduce at this bait set
  on current main — **0025's closed vocabulary appears to have already
  absorbed most of L1's trigger surface** (the old unconstrained
  extractor emitted 12,575 relation strings; the registry now forces a
  choice among 19, and concrete relations win). Post-fix obligation:
  A08 moves to grounded; the movement cell is small but real.
- **E-B24-2 PARTIALLY REFUTED — and the refutation is the round's real
  finding.** 14/16 relays quarantined correctly, but **2/16 relays
  BYPASSED quarantine entirely**: B02 ("my doctor said my cholesterol
  is borderline") → `health_state`, MENTIONABLE; B07 ("the vet said
  Rex is allergic to chicken") → `has_diet`, MENTIONABLE — **with the
  note field reading "as stated by the vet"** while the relation
  launders the relay, and the answer asserting ("This was confirmed by
  the vet"). RELAY LAUNDERING: when the extractor chooses a concrete
  relation over `third_party_claim`, `_disclosure_for` never sees a
  quarantine-triggering relation and relayed testimony grounds. B07 is
  a live, controlled instance of exactly the note-vs-label
  disagreement dev task #107 proposes to check.
- **E-B24-3 HELD.** Canaries: 0 grounded edges, 0 asserted planted
  claims (7/8 quarantined `third_party_claim`; C07 extracted no edge
  and the answer abstained with an unverified-claim mention).
- **E-B24-4 HELD.** Controls: 8/8 grounded.

## Instrument limitation, disclosed

The answer-level HEDGE lexicon missed *told/stated/confirmed*, so
answer_class over-counts "asserted" in cell B; the store-level records
are the registered surface, and the post-fix re-run reuses the same
classifier so paired movement is unaffected.

## Consequence for the release (the gate this baseline opens)

The two-cell baseline the release gate names is BANKED — dev may
implement 0024. Two riders travel with it:
1. The fix's relay-preservation regression should test the REAL relay
   path, which this baseline shows sometimes never reaches
   `_disclosure_for` with `third_party_claim` at all (B02/B07 class).
   The 0024 decision-order fix is ORTHOGONAL to that laundering path
   and will not close it; it must also not be blamed for it.
2. Relay laundering is measured, pre-existing, and now on the record:
   routed to dev as evidence for #107's priority, not as a 0024
   blocker.


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
