# U3b — the shipped predicate re-measured (the 0019 release gate's closing artifact)

**2026-08-15 · Research (the round-4 obligation executor).**

## Identity

- **Code:** `src/veracium/grounding.py::ungrounded` @ **`19765e1`**
  (imported and executed directly — not the reference; pure, zero-I/O).
- **Corpus:** the phase-1 measurement corpus — the longmemeval extraction
  caches (main + variance r1–r3) joined to their event texts by the
  established reconstruction (one extraction identity; keys recomputed per
  turn × author/etype). Concatenated-cache **sha256
  `see u3b_measurement.json`** (computed over the sorted cache files at
  measurement time). 42,161 pairs → **149,006 non-boolean objects checked**.

## The numbers

- **Flags: 440 → flag rate 0.30% of all objects** (the earlier 0.47% was
  over the 56k specifics-bearing subset; over that framing the shipped rate
  is comparable — the shipped date handling differs from the shadow
  reference's ±366-day window, see below).
- **Fresh 30-flag sample, hand-classified** (`u3b_flag_sample.json`,
  seed 20260815):
  - **Candidate-true ungrounded extractions: ~14/30 (~47%)** — including
    fresh instances of every acceptance-era defect class:
    answered-question-as-fact (the EBITDA "43%" itself resurfaced in the
    fresh draw), anticipatory generation (HTML syntax, warehouse properties,
    "iconic landmarks"), world-knowledge fill-in (Tony-award counts, JR-Pass
    blackout dates, regatta dates), and the added-year class (the Hong Kong
    "1 July 2023" again).
  - **Date-COMPOSITION artifacts: ~9/30 (~28%)** — the shipped
    resolution-set grounds pure relative-date resolution ("next Wednesday" →
    ISO) but flags YEAR-AUGMENTATION of partial stated dates ("May 13th" →
    "May 13th, 2023", the year legitimately from session context). This is
    the shipped predicate's dominant benign class. Recorded as an
    OBSERVATION for a possible v2 refinement — per the
    predicate-changes-are-spec-changes rule, nothing changes now.
  - Paraphrase/derivation/cross-lingual: ~5/30; uncertain: ~2/30.

## The verdict

**Precision ~47% at a 0.30% all-objects flag rate — within the
acceptance-pinned band (~40–50%) measured on the SHIPPED code.** The
operating point the spec promised is the operating point the implementation
delivers; the flag surface catches every defect class the campaign
documented, on a fresh sample, from the binary that ships.

*Research attests: measurement executed against 19765e1's importable
predicate; sample classified by hand without reference to the earlier
samples; the record and its JSON artifacts
(`u3b_measurement.json`, `u3b_flag_sample.json`) are the release gate's
closing evidence.*
