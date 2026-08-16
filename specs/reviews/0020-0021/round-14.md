# 0020/0021 external review — round 14 (verbatim, received 2026-08-16)

Package reviewed: `0020-0021-v15-20260816T1159Z.tar.gz`
sha256 `449a0624c999d7c32c5d65710ca4aa35b7f81181777ce1b2b1f71f7ae377b2d7`

## Round 14 disposition

0020 **Accept** · 0021 **Accept** · 0020↔0021 seam **Accept** · Package
verifier **Pass** · Archive integrity **Pass** · Coupled design freeze
**Approved**. No blocking findings remain.

### R13-1 reconciliation

**Closed.** The v15 construction derives op_key inside
construct_plan_row; requires the key before projection; consumes the
writer's operation-ID domain; recomputes and compares the exact
context-specific key; refuses missing, null, malformed, cross-context,
wrong-domain, and wrong-survivor-derived keys; enumerates all ten
invalid cells in the 3×5 writer/payload product. My prior reproduction
now refuses every attacked key. I also independently constructed and
inserted all five valid cells — native, two import, and two prune —
against the extracted real DDL: 5/5 inserted.

### Frozen invariant surface

The design is accepted and frozen on: 0020's V1–V19 read-boundary,
disclosure, membership-closure, portability, and reverse-link
invariants; 0021's W1–W18 maintenance partitioning, fail-closed
derivative, atomic import, retention, and ledger invariants; mutual
acceptance and deployment coupling; policy-independent maintenance
partitioning; transitive, survivor-resident membership evidence;
pre-commit linkage reconstruction and whole-import refusal; writer →
operation domain → site → payload class → derived key ownership;
canonical direct/reparented reverse-link semantics; the single 0018 D2
window carrying the schema, format, and writer-enforcement riders.

Reviewer sign-off is also given for the enumerated
0009/0014/0016/0018/0019 interface points. This does not replace the
separate owner sign-offs the candidates themselves require.

### Non-blocking implementation obligations

1. **Ship the five-valid-cell oracle.** The package says all five valid
   cells are constructor-built and inserted, but its product loop skips
   valid cells and there is no native-context constructor call in the
   shipped evidence. My independent oracle proves the construction
   works; retain that proof in the harness or narrow the claim.
2. **Make the operation-domain regex literally exact.** Python's current
   `^…$` plus `re.match` accepts an otherwise valid `op-<12hex>`
   followed by a terminal newline. Use `fullmatch` or an equivalent
   exact matcher and retain that malformed-ID cell.

### Verification record

Archive matches its sidecar; 299 unique safe members. Verifier: 16
hashes, 127/127 vectors, schema evidence, 12 verifier-fault
classifications. Store adapter 15; ledger 13 incl. 76/76 refusals. Gate
61/3. Author's qualified 1342/14. Local unqualified reconciliation as
expected. External seal mutation (candidate hash also updated): verifier
exited 1 on SITE-MATRIX drift.

Additional artifact still requested: the shipped five-valid-cell
constructor-to-real-DDL oracle. Archive-format change: none.
