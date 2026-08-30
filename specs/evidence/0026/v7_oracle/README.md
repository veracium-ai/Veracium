# V7 frozen pre-feature oracle (0026 §22 obligation 3)

`pre_feature_export.jsonl` was exported by the PRE-FEATURE code (commit 9fe16f8 tree, before any agreement mechanism existed in src/), from a deterministic marker-free 3-edge store. The V7 graduation test rebuilds the identical store with the CURRENT code and requires a byte-identical export — byte identity proven against a frozen artifact rather than against the feature's own output.
