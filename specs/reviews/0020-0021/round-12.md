# 0020/0021 external review — round 12 (verbatim, received 2026-08-16)

Package reviewed: `0020-0021-v13-20260816T0214Z.tar.gz`
sha256 `fdbf69f7ab17f0d11c48eac540b6b7913cc8a4b387ec06a81a849fe83a816b2f`

# Review disposition: RETURN FOR AMENDMENT

0020 Return · 0021 Return · Coupled seam Return · Package verifier
Return · Archive integrity Pass · Invariant/interface freeze not
accepted.

### R12-1 — The authoritative site matrix assigns writers to the wrong atomic primitive

The generated matrix says `commit_outcome_import_plan` writes
`scope-attribution` rows for native absorption, import, and future
pruning. That conflicts with:

* Accepted 0009: this is a purpose-built whole-import primitive, "NOT a
  general Store transaction API."
* The native path: `apply_supersession → apply_supersession_plan`.
* The exact amendment's own rule that import-plan rows derive only from
  `reconstruct_absorption_rows`, which emits direct reconstructed rows
  and imported transitive copies—not native flattened rows, reparented
  links, or markers.
* The public-surface inventory, which names no atomic writer for native
  flattened rows or future pruning.

Executed reproductions reinforce the contradiction:

* `validate_row_plan` accepts reparented, marker, and native-flattened
  classes as import-plan rows.
* `row_op_key("sup-edge-123", …)` refuses because it accepts only
  `op-<12hex>`, while native absorption uses `sup-{edge.id}`.

Thus W14/W16 do not have one implementable atomic contract. Split the
matrix by operation context: native `apply_supersession_plan`, import
`commit_outcome_import_plan`, and a separately named future prune
primitive. Each needs its allowed payload subset, operation-ID domain,
expected-state checks, and cross-product refusal tests.

### R12-2 — A stale reverse-link algorithm remains in 0020

0020 lines 336–338 still says to find "the row whose `contributor_ref`
names this record → its survivor." Under flattening, multiple rows can
name the contributor. The same document's earlier normative algorithm
correctly requires `derive_absorbed_by`: exactly one canonical
direct/reparented row, zero means omit, multiple means refuse. Replace
the stale sentence with that canonical-class algorithm and gate this
carrier too.

### R12-3 — The advertised matrix/dependency seal is not shipped or invoked

The three current matrix blocks are byte-identical and the manifest
dependencies presently match the headers. However, no executable code in
the archive compares them: verify_package.py never calls
render_site_matrix or parses Spec-Requires.

Negative control in a disposable copy: removed 0021 from 0020's
Spec-Requires; replaced 0020's matrix row with deliberately contradictory
text; updated only 0020's manifest hash; ran the verifier. Result: exit
0, "16 hashes verified … NO FAILURES." The claimed seal cannot be opened
or executed from the review package.

Integrate both checks into verify_package.py, and add mutation
self-tests proving either drift fails.

### Prior-finding reconciliation

R11-1 not closed (copies match, matrix substantively wrong, stale
carrier). R11-2 closed. R11-3 closed. R11-4 closed. R11-5
labels/dependency data corrected; the claimed dependency gate not closed
under R12-3.

### Verification results

Archive sha matches; 295 safe members. Verifier 16 hashes, vectors
121/121, normalized evidence matches; two store-harness skips on local
3.53.1. Manual: adapter 15+1; ledger 13. Gate 61/3. Full local suite the
expected unqualified collapse; the author's qualified 1342/14 remains
plausible, not independently reproduced.

Requested artifact: a writer-specific operation × site × payload × op-ID
× atomic-boundary matrix, executable from the one-command verifier. No
additional source-tree material is needed.
