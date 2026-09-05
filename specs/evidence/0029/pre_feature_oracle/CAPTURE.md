# 0029 V-COMPAT — the pre-feature oracle capture record

| | |
|---|---|
| **Captured from** | main `1fc357f4` (2026-09-05) — the tree BEFORE any journaling code, checked out as a separate worktree so the builder ran against pre-feature `src/` |
| **Builder** | `generate_oracle.py` (this directory; the copy that ran is byte-identical to the committed one) |
| **Artifact** | `pre_feature_capture.json` — sha256 `186a0909df6ac11dc20801800b59d1778e7073fa728f0e42f88a93f398edb947` |
| **Reproducibility** | two consecutive runs at the pre-feature tree, `cmp` byte-identical |
| **Surfaces** | recall (5 queries, grounded + unverified), context block (5), export (18 JSON Lines, verbatim), MCP (`recall_impl`, `answer_impl`, `maintain_impl` keys) |
| **Excluded, measured** | `provenance.origin` (17 export lines) and the header's `exported_at` (1 line): store identity and the export clock, substituted byte-wise with placeholders; recorded under `excluded` as field names and counts, never values |
| **Consumer** | `tests/test_0029_carrier.py::test_no_consumer_behavior_identical` pins the sha256 above and replays the builder against the journaling store |

Regenerating this file anywhere but the pre-feature tree defeats its purpose;
the pinned digest makes such a regeneration fail the suite rather than pass
silently.
