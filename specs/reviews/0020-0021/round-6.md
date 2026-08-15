*Verbatim external-review report, preserved per the round-3 artifact ask. Received via the repo owner; package sha in the archives INDEX.*

# 0020/0021 external round 6 — RETURN FOR AMENDMENT

Reviewed package: 0020-0021-v7-20260815T1948Z.tar.gz
Verdicts: 0020 RETURN · 0021 RETURN · seam RETURN · archive PASS ·
package verifier PASS · full suite PASS reconciled. (The reviewer read
the embedded REVIEWER_GUIDE and PROCESS before reviewing.)

### Findings (abridged; full dispositions in reviews.py)

1. Import reconstruction still fails SUPPORTED inputs — executed: a
   user_id remap changes edge ids without rewriting notes (survivor
   imp-e-…, reconstructed key still the old id); a whitespace-bearing id
   breaks the \S+ grammar; an untagged absorbed_duplicate is silently
   treated as ordinary retirement despite its invalidation reason proving
   absorption. Required: post-remap keying, a grammar handling every
   valid id, fail-closed malformed/ambiguous treatment, and tests driving
   actual import_memory across the matrix.
2. "Writing real ledger rows" is NOT IMPLEMENTABLE under the governing
   contracts — the helper's rows lack seven ContributionRecord fields;
   accepted 0014 requires a total store-derived absorption payload with
   the pre-inheritance base image, which is not in the export and cannot
   be inferred; the dangling rules contradict "may arrive later"; the
   whole-import primitive carries only edges and episodes; the surface
   inventories omit portability/store/base/sqlite/the carrier; 0021 §7b
   still said stated-not-built. Required: an explicit compatible design —
   evidence in the export format OR a named 0014 amendment with a
   distinct imported-evidence site and its own integrity semantics — plus
   the primitive extension, full inventories, and durability tests.
3. Policy carrier wording internally stale — the "immutable" registry
   stored mutable dicts; the ScopePolicy docstring still described seal
   recomputation the registry implementation no longer performs.

### Verification
Sidecar valid; 247 files clean; verifier all-8-hashes + fresh-vs-recorded
PASS; vectors 60/60; adapter 4/4; suite 1339/17 reconciling exactly.

### Artifact ask
One real-store import/reconstruction harness over the full input matrix
verifying durable contribution rows after reopen; the consolidation-
output and recovery-state adapter cases.
