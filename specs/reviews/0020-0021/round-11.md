# 0020/0021 external review — round 11 (verbatim, received 2026-08-16)

Package reviewed: `0020-0021-v12-20260816T0144Z.tar.gz`
sha256 `3c234a8d18d088315b3bfd188bd3404d8ca6a0078bac3ecbcbbbecd09ab8503a`

# Review disposition: RETURN FOR AMENDMENT

0020 Return · 0021 Return · Coupled seam Return · Verifier Return ·
Archive integrity Pass · Invariant/interface freeze Not accepted.
All 293 members extracted safely.

### R11-1 — The new site split is contradictory across normative carriers

The intended construction is sound in isolation: direct imported links
use `imported-absorption`, while transitive, reparented, and incomplete
rows use `scope-attribution`.

But 0021 §7b still contains an "EXACT" 0009 amendment saying:
* `imported-absorption` is the **only** site the import path may write;
* transitive rows add `flattened` to that site's payload;
* `import_row_op_key` hard-codes that site;
* the validator refuses "reparented without flattened."

The immediately following 0014 amendment and reference implementation
require the opposite. The field-contract table, import-population row,
public-surface inventory, and linkage-carrier diagram also retain the old
imported-only description.

Concrete failure: implementing the exact 0009 text either emits rows
illegal under the new 0014 vocabulary or cannot reproduce the package's
reference and harness results. W14/W15 therefore lack one implementable,
same-commit contract.

### R11-2 — `validate_row_plan` is still not total

The exact amendment says every plan row contains the complete stored
semantic field set. The validator nevertheless uses `row.get()` and
silently supplies a default contributor type: missing identity_digest
ACCEPT; missing evidence_ref_digest ACCEPT; missing contributor_type
ACCEPT (as "edge", projecting through plan_row_id). The 47-cell matrix
tests malformed values but not key deletion. Require presence separately
from allowing an explicit None value where permitted.

### R11-3 — The insert-only regression contains an always-passing assertion

Ledger harness lines 388–391: the byte-identical claim's assertion ends
in `... or True` and cannot fail. Later checks establish existence, not
byte equality. The recorded "byte-identical" conclusion is stronger than
the executable evidence.

### R11-4 — "Fresh-vs-recorded" verification compares only the final line

verify_package captures only the fresh process's last line and checks
whether it occurs anywhere in the recorded file. Reproduced with the
schema evidence: recorded sqlite_runtime 3.45.1, fresh 3.53.1, bytes
differ, verifier reports a match. The same logic would miss changed
constructor text, manifestation hashes, parity detail, or step hashes so
long as the generic final line remains. Compare machine-readable
semantic results, excluding explicitly environment-dependent fields.

### R11-5 — Package metadata does not mirror the candidate

review_manifest.json omits `0019` from 0021's `requires` while the
candidate header includes it — the wrong dependency graph for the
final-form schema rider. COLLECTED.txt says "both round-9 SENT rows";
this is the round-11 package.

## Prior-finding reconciliation

R10-1 substantively corrected (carriers inconsistent under R11-1).
R10-2 CLOSED. R10-3 not closed (R11-2/R11-3 reopen it). R10-4 generator
exists and is coherent (verifier inadequate under R11-4). R10-5
corrected; the verifier still returns under R11-4.

## Execution results

Gate 61/3 · vectors 115/115 · adapter 15+1 · ledger 13 · fault matrix
8/8 · one-command verifier exit 0 with 15 hashes (two store-backed
skips on local 3.53.1) · full local suite the expected unqualified
collapse; the qualified author record remains 1342/14.

## Requested artifacts and archive changes

* ONE authoritative matrix mapping every ledger site to its writers,
  payload classes, canonical status, exact-set participation, and op-key
  function; gate every prose/table/diagram carrier against it.
* Validator tests with field DELETION; remove tautological assertions.
* Verifier comparison of structured result data or semantic hashes.
* Generate review_manifest dependencies from candidate headers and gate
  equality. Correct the round label; include the verifier's own hash.

No additional source-tree material is needed.
