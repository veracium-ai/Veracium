*Verbatim external-review report, preserved per the round-3 artifact ask. Received via the repo owner; package sha in the archives INDEX.*

# 0020/0021 external round 4 — RETURN FOR AMENDMENT (both + seam); Archive/integrity PASS

Reviewed package: 0020-0021-v5-20260815T1901Z.tar.gz

Three blocking findings remain.

### Findings (abridged headers; full dispositions in reviews.py)

1. 0020 policy sealing is still bypassable — B+E (executed: direct
   construction with a canonical-looking inconsistent group_digests map
   classifies B as OWN; object.__setattr__ flips accepted; caller-owned
   backing dicts mutable behind MappingProxyType). Required: capability-
   controlled construction or full canonical-projection recomputation at
   consumption; adversarial vectors for all three.
2. 0021's identity-free compatibility claim still contradicts its result
   schema — D+C (executed: the additive result feeds the shipped
   robustness consumer, which rejects the pools dict — invariants.py
   requires non-negative-integer values). Required: narrow to
   stored-state/value compatibility; sweep the robustness checker,
   exact-result lifecycle tests, and API docs.
3. 0021's audit carrier remains mechanically incomplete — C+B (the
   shipped contract is one JSON line per operation with exact-sequence
   tests; per-pool events change cardinality unamended; error: str? can
   echo prompt/episode text, violating AuditLog's no-memory-text
   invariant). Required: amend the audit contract/tests/docs; a closed
   content-free error code; the adversarial planted-secret W12 cell.

### Confirmed closures
Digest-space membership matches the shipped construction; the real
op-<12 hex> id recognized; pool:unidentified noncolliding; the legacy
absorption leak logically closed (projected real contributions() rows
for an A survivor with a B contributor → UNRESOLVED); top-level counters
preserved for telemetry.

### Verification
Sidecar valid (67f5428f…); 269 members clean; all hashes matched;
verify_collected PASS; 56/56 vectors, all unique; sealed suite 1339/17
reconciling exactly. The standalone STATUS/archive-index staleness in a
source archive is checkout-dependent, not an integrity finding.

### Standing artifact/archive feedback
Still missing: the real-store adapter harness (actual ContributionRecord
construction and SqliteStore.contributions() queries; retain actual-store
regressions for absorption, consolidation, import, recovery). Archive:
add harness_result_sha256 to review_manifest.json; provide one command
verifying the entire manifest.
