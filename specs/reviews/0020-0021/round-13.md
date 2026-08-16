# 0020/0021 external review — round 13 (verbatim, received 2026-08-16)

Package reviewed: `0020-0021-v14-20260816T1053Z.tar.gz`
sha256 `6aa3ffd02ef39a12742e36f771755d1119a451f5349a1a77ba04096d8b416009`

## Round 13 disposition

0020 Return (its R12 defect is closed, but mutual Spec-Requires makes
acceptance atomic) · 0021 Return · seam Return · Package verifier PASS ·
Archive integrity PASS · Interface/design freeze not approved.

### R13-1 — The writer context is not bound to the row's operation key

The amended contract assigns each writer an operation-ID domain and
exact per-row key construction (0021 §7b), and says the store validates
everything. The executable construction does not enforce that boundary:
WRITER_CONTEXTS declares op_re for all three contexts — never consumed;
validate_row_plan requires only six semantic fields and checks the
(site, payload-class) cell, neither requiring nor examining op_key;
plan_row_id deliberately excludes op_key; the storage harness copies
row["op_key"] directly into the stored tuple.

Concrete reproduction, using an otherwise valid import row: missing
op_key ACCEPT; native-format import key ACCEPT; "not-an-operation-key"
ACCEPT; null op_key ACCEPT — all four produce the same valid
plan_row_id. A caller can select an arbitrary, cross-context, or null
operational key despite the matrix's claimed domain and construction.
The unique SQLite index prevents duplicate non-null keys; it does not
prove that a key belongs to the current operation or writer.

The "EXHAUSTIVE" 65-cell matrix also tests only 6 of the 10 invalid
writer × legal-payload cells (omitting native/reparented, native/marker,
prune/native-flattened, prune/import-flattened-reconstructed).

Required amendment: (1) preferably derive op_key inside each atomic
primitive from its store-owned operation ID and row coordinates —
alternatively pass the operation ID and survivor coordinates into
validation and require exact key equality; (2) enforce the writer's
operation-ID domain and reject absent, null, malformed, cross-context,
and incorrectly derived keys before projection or storage; (3) expand
the gate to the complete 3×5 writer/payload product plus key-presence,
domain, derivation, and insertion cases.

### Prior-round reconciliation

R12-1 writer/site/payload ownership repaired; operation-domain/key
ownership remains open as R13-1. R12-2 CLOSED. R12-3 CLOSED.

### Verification record

Archive sha matches; traversal/ownership/cache checks pass. Verifier: 16
hashes; 121/121 vectors; schema evidence and the 12-cell fault matrix
pass; store-backed checks explicitly skipped on local 3.53.1. Forced
qualified-path: adapter 15; ledger 13. Gate 61/3. Repo suite: the
expected runtime-gated collapse locally. External seal negative control:
after mutating 0020's matrix and updating its manifest hash,
verification exited 1 on SITE-MATRIX drift.

Additional artifact requested: an operation-aware row-construction
oracle covering the complete writer/payload/key product and exercising
the actual preflight-to-insert boundary. Archive-format change: none.
