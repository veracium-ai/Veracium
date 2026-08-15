*Verbatim external-review report, preserved per the round-3 artifact ask (the 0003 precedent: full round texts beside the compressed reviews.py entries). Received via the repo owner; package sha in the archives INDEX.*

# 0020/0021 external round 2 — RETURN FOR AMENDMENT (both + seam)

Reviewed package: 0020-0021-v3-20260815T1608Z.tar.gz

V3 materially improves the architecture: mutual dependencies,
policy-independent maintenance, explicit read carriers, per-pool
thresholds, completed reviewer briefs, and a normative reference are all
good corrections. The remaining blockers are mostly found-in-fix defects
in those new constructions.

### Findings (abridged headers; full dispositions in reviews.py)

1. 0020's normative identity model violates accepted 0006 absence
   semantics and is not closed (only (None,None) treated unidentified vs
   I13; "false" truthy; outer-frozen-only dataclass; vector coverage
   claims false).
2. Contradictory semantics for a principal supplied without policy rules.
3. The record-to-membership resolver remains unspecified at the central
   seam (and the recovery row is incorrect for OUTPUTS_DURABLE
   pre-feature operations — executed).
4. 0020's zero-change claim contradicts 0021's policy-independent
   maintenance rule.
5. 0021's per-pool failure and public-result construction is incomplete.
6. 0021 lacks a mixed-version shared-store regime.
7. The archive's sealed-state fix introduced new packaging defects
   (143 cache artifacts; author-path bytecode; UID/GID 1000; the
   COLLECTED inventory text semantically stale).
