*Verbatim external-review report, preserved per the round-3 artifact ask. Received via the repo owner; package sha in the archives INDEX.*

# 0020/0021 external round 5 — RETURN FOR AMENDMENT

Reviewed package: 0020-0021-v6-20260815T1926Z.tar.gz
Verdicts: 0020 RETURN · 0021 RETURN · seam RETURN · archive container PASS
· package verifier RETURN.

### Findings (abridged; full dispositions in reviews.py)

1. Imported absorption survivors still resolve by claimed identity — the
   spec claimed the reconstruction closed while the adapter's case 3
   carried no assertion and labelled own-identity fallback a residual;
   COLLECTED overclaimed. Required: an executable carrier (atomic
   contribution-row reconstruction inside import_memory), malformed/
   ambiguous/remapped cells, amended inventories, and the real-store
   regression asserting UNRESOLVED.
2. The sealed-policy construction remains re-signable — _seal and the
   nonce are ordinary module attributes; executed: flip + re-sign →
   CROSS_VISIBLE. Required: a validator-owned immutable snapshot or an
   explicit threat-claim narrowing; retain the re-sign attempt as a
   vector.
3. The identity-free byte-identity claim survived the narrowing in both
   §5 tables; the robustness checker still rejects the pools dict.
4. verify_package.py does not verify every manifest hash —
   store_adapter_result_sha256 was declared and never checked (executed:
   a tampered result file passed). Required: generic traversal;
   fresh-vs-recorded comparison; single adapter run.

### Verification
Sidecar valid (4a4f9bc9…); 274 members clean; hand-checked hashes match;
verify_collected PASS; 59/59 vectors unique and passing; suite 1339/17
reconciling exactly. R4-3's audit amendment satisfactorily closed.

### Artifact ask
Extend the real-store adapter to actual cleared-identity consolidation
outputs and every recovery state (explicitly deferred pending the 0021
implementation).
