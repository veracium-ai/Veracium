# specs/0003 — external review round 5 (2026-08-02)

*Round 5's full text was dispositioned in the spec itself (the v6 header narrative) rather
than a standalone proposal; this note carries the closure record so the acceptance package
is self-contained (round-10 acceptance-ledger blocker).*

**Verdict: narrow design affirmed; deferred — seven findings.** All seven were closed in v6
(`1ec7f3e` carried the v6→v8 line; v6 itself was the first close):

| # | round-5 finding | closed by |
|---|---|---|
| 1 | duplicated sections (0002's append-only failure mode) | v6 de-duplicated; a structural duplicate-heading check added (`test` in `tests/test_spec_gate.py`) |
| 2 | `ladder.py` not runtime-grounded (hard-coded classes incl. a non-existent `assistant`) | v6 derives the tables from the SHIPPED `EvidenceAuthor` enum + production `_disclosure_for` (144/44/8); `specs/render_ladder.py --check` |
| 3 | §4e did not establish a contention group arose from a refusal | v6 §4e froze "all active edges sharing a functional key" and stated the pre-existing-reordering consequence |
| 4 | the refusal log was not one atomic store operation | v6 §4f froze the single-commit primitive (later `apply_supersession_plan`) |
| 5 | §4f "Schema: none" while introducing a durable record | v6 §4f corrected; fully resolved at round 6 (schema v3→v4, `Spec-Requires: 0007, 0013`) |
| 6 | §7a did not list the real surfaces; the "one guard in one loop" framing | v6 §7a enumerated write/read/storage; the WITHDRAWN framing removed at round 6 |
| 7 | I6/I6a not parameterised over the product / all selection stages | v6 I6/I6a parameterised from `ladder.py` over the product and all three selection stages |
