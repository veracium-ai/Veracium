*Verbatim external-review report, preserved per the round-3 artifact ask (the 0003 precedent: full round texts beside the compressed reviews.py entries). Received via the repo owner; package sha in the archives INDEX.*

# 0020/0021 external round 1 — RETURN FOR AMENDMENT (both + seam)

Reviewed package: 0020-v2-20260815T1526Z.tar.gz

## Review verdict

- 0020 — RETURN FOR AMENDMENT
- 0021 — RETURN FOR AMENDMENT
- Coupled seam — RETURN FOR AMENDMENT; atomic acceptance withheld

The archive checksum and candidate-spec hashes match, and the archive
contains no unsafe paths, links, duplicates, or special files. No invariant
surface is ready to freeze.

### Numbered findings (abridged headers; full dispositions in reviews.py)

1. The derivative-membership rule contradicts the implementation and fails
   across portability (_derive_output_metadata copies inputs[0]'s
   provenance without clearing origin/source_id; export/import destroys the
   ledger evidence). Specify legacy, imported, missing/incomplete-ledger,
   mixed-contributor, and in-flight outputs. Missing membership evidence
   cannot silently mean "shared."
2. 0020 does not mechanically define its new public types or grammars
   (Identity, ScopePolicy, rule shapes, filter grammar, decision table).
3. 0020's read-surface inventory is incomplete (answer(), queryless
   recall→proactive, Recall.edges/.episodes/.contested,
   ContestedGroup.exposed; full-response empty-vs-withheld equivalence).
4. 0021's consolidation construction is based on a false reach assertion
   (lifecycle.consolidate is one global pool; thresholds/order/aggregation/
   failure/concurrency/recovery undefined; no mechanical COMBINING_SITES).
5. Per-process policy conflicts with shared-store maintenance (an honest
   unscoped host defeats W1); choose an enforceable model; config-only
   reversibility fails after consolidation.
6. The coupled release requirement is prose-only (Spec-Requires
   incomplete; no machine-checked coupled acceptance).
7. The sealed archive fails its own package verifier (COLLECTED markers
   absent; the packaged-state gate never ran; briefs n/a).

### Additional artifacts requested
Executable reference + decision vectors; a generated combining-site
manifest; fixtures for legacy/mixed derivatives and shared-store configs;
a machine-readable dependency/coverage manifest.

### Archive changes requested
COLLECTED-first sealing with the packaged-state gate recorded; dual-spec
naming; a machine-readable review manifest; completed §9 briefs.
