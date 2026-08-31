# 0027 V10 — frozen legacy-projection oracle

Captured 2026-08-31 at commit `bd5fdc0` — the last tree BEFORE any 0027
implementation touched `graph.subgraph_for_query` (the 0026 v7-oracle
pattern: the oracle predates the mechanism it judges).

`legacy_projections.json` maps six queries to the ordered edge-id list the
SHIPPED pre-feature `subgraph_for_query` returned over a fully deterministic
60-edge store (fixed ids, fixed timestamps; construction in
`generate_oracle.py`). The store exercises user-subject eligibility, entity
overlap scoring, the active bonus, recency tiebreaks, I8 collapse, the I6
reserve under truncation, `_cover` coverage, and a functional-contention
permutation.

V10 (`test_legacy_projection_identical_when_semantic_off_unscoped`) rebuilds
the same store against the LIVE pipeline with `principal=None` and semantic
off and requires the identical projections — so the `_lexical_scored`
extraction and the fused construction's degenerate path can never drift from
the shipped behaviour, however the code is refactored.

Do NOT regenerate after implementation lands; the committed JSON is the
frozen truth (`--check` exists for verifying at the capture commit only).
