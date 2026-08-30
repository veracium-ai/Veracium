# End-to-end over-gate fixture (SYNTHETIC)

The reviewer's round-7 requested artifact (0026-EVIDENCE-R7-1/R7-2): a
tiny, fully synthetic cache whose measured rate is far OVER the 2%
gate, so the whole live pipeline can be exercised end to end —

    measurement (bootstrap state, exit 3, aggregate + worklist emitted)
    → census labelling from the FULL-CONTENT worklist
    → independent co-verification census
    → final --aggregate verification (accepts only with BOTH bound)

`fixture_cache.jsonl` is invented content (20 grounded first-person
triples, 3 firing = 15%); `fixture_peer.json` is its matching
cross-anchor, used via `--peer-anchor` — FIXTURE TESTING ONLY: the
authoritative anchor is the real 0011/0025 subject aggregate and the
packaged verification uses it. The standing test
`test_the_over_gate_pipeline_end_to_end` drives every stage through
the real `main()`.
