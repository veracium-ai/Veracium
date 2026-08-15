*Verbatim external-review report, preserved per the round-3 artifact ask (the 0003 precedent: full round texts beside the compressed reviews.py entries). Received via the repo owner; package sha in the archives INDEX.*

# 0020/0021 external round 3 — RETURN FOR AMENDMENT (both + seam); Archive/integrity PASS

Reviewed package: 0020-0021-v4-20260815T1641Z.tar.gz

The architecture remains sound, but five found-in-fix construction gaps
prevent freezing the invariant surface.

### Findings (abridged headers; full dispositions in reviews.py)

1. 0020 policy validation remains bypassable (direct ScopePolicy
   construction; set accepted as sequence; vector coverage gaps — the
   "int bool" vector was a stringified "1"; duplicates).
2. The normative membership resolver consumes a ledger shape 0014 does
   not provide (ContributionRecord carries nullable one-way
   identity_digest, never Identity pairs; is_legacy_derivative used a
   fictional "consolidate:" prefix where real outputs use "op-…" —
   store-probed).
3. Legacy absorption defeats the mixed-version read-safety claim
   (executed: a pre-0021 absorption survivor carries identity A with B's
   .99 confidence and August observation; the resolver ignored its
   absorption ledger rows).
4. The per-pool result schema cannot represent the shared pool
   (digest(local, None) → None) and contradicts identity-free byte
   identity (the nested schema changes the public result).
5. The promised audit/telemetry carrier sweep is not implemented as a
   mechanical contract (one aggregate maintain event today; telemetry
   reads co["consolidated"]/co["into"]).

### Verification
Archive SHA-256 valid; candidate and vector hashes match the manifest;
verify_collected PASS; 44/44 vectors match subject to coverage defects;
261 members, no unsafe paths/caches/non-normalized ownership; sealed
command 1339 passed / 17 skipped; reconciliation exact vs 1342/14.
THIS FULLY CLOSES v3's archive/cache/ownership/reconciliation finding.

### Standing artifact/archive feedback
A self-executing vector harness + per-kind schema; a real-store resolver
adapter test over actual ContributionRecords; fixtures for legacy
absorption/consolidation and mixed writers; full prior-round reports;
reference_scope.py sha in the manifest; include and hash the harness and
its recorded result; a v(N-1)→vN change manifest.
