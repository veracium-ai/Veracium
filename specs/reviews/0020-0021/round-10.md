# 0020/0021 external review — round 10 (verbatim, received 2026-08-16)

Package reviewed: `0020-0021-v11-20260816T0106Z.tar.gz`
sha256 `719df4df15173ca9385c0e3edbc057138d67f7af35c092328cf73962e30593de`

[Full verdict as received — RETURN FOR AMENDMENT: 0020 return · 0021
return · coupled seam return · archive integrity pass · package verifier
contract return. V11 closes R9-2 and the normal-path portions of
R9-1/R9-3; the found-in-fix pass exposed four design blockers and one
verifier blocker.]

### R10-1 — Prune-time reparenting violates the frozen 0014 ledger contract

The new retention step mutates an existing flattened ledger row by adding
`reparented: true`; the SQL harness performs an
`UPDATE contribution_ledger SET payload=…`.

Accepted 0014 instead says a ledger row is inserted and never updated or
replaced, and its native `absorption` payload is the closed
`{base, contributor}` schema. The drafted amendment:

* does not amend that immutability rule;
* does not define a valid native `absorption` payload containing
  `flattened` or `reparented`;
* omits `reparented` from the imported marker vocabulary.

Thus W18/V19 is demonstrated only by bypassing the store's accepted
validator with raw SQL. The transition is not constructible under the
contract it must amend.

Acceptance requires either an explicit, complete 0014 amendment for
mutable reparenting or an immutable replacement construction, including
every payload schema, row identity/op-key consequence, exact-set
partition, and real-store validation path.

### R10-2 — The incompleteness marker becomes a clean export link

When the required flattened copy is missing, `prune_absorbed_record`
writes contributor_ref='A', payload={'closure': 'incomplete'} — but
`derive_absorbed_by` treats every non-`flattened` row as canonical.
Executed: derive_A_from_incomplete_marker: C. The marker described as
"failed closed forever" therefore materializes `absorbed_by_id=C`,
laundering a detected W14 violation into structured portable linkage.

Acceptance requires every consumer — closure, reverse derivation, export
and import — to recognize the marker consistently and refuse or omit
linkage. Add an export/import regression for the missing-copy prune path.

### R10-3 — `validate_row_plan` is not total over the amended logical row

The normative validator accepted: malformed evidence_ref_digest; missing
direct contributor_ref; contributor_type='episode'; undeclared reparented
payload. This contradicts 0021 §7b (total ten-field row,
contributor_type="edge", typed binding, valid evidence digest, closed
payload vocabulary).

Acceptance requires strict validation of every field and cross-field
combination, including both digests, contributor type/ref, exact boolean
marker values, unknown payload keys, and contributor/evidence binding.
Extend the negative matrix rather than adding only named examples.

### R10-4 — The 0019 rider is still a delta, not the requested final schema construction

Adding 0019 to `Spec-Requires` is correct. However, the purported
whole-clause rider defines the constructor as "the v7 CREATE TABLE with
two columns appended" and promises evidence regeneration later. Still
lacking: literal complete SCHEMA_V8 constructor DDL; measured ALTER-path
stored DDL; generated evidence for both manifestations; concrete
sha-pinned 0013 step evidence. Conflicts with accepted 0019's own R2-6
whole-clause discipline and the previous round's explicit artifact
request.

Acceptance requires the full literal constructor and executable
migration/evidence package, with the 0007/0013 carrier and sign-off edges
reviewable now.

### R10-5 — Invalid qualification results still become successful skips

verify_package says only `runtime_supported() == False` may skip, but
uses truthiness. Injecting `runtime_supported=lambda: None` produced an
unqualified skip and main_return 0. Its package-containment check also
uses string `startswith`; a module at the sibling path `<ROOT>-shadow/...`
was accepted as qualified.

Acceptance requires: `type(result) is bool`; only `result is False` may
skip; any other value is fatal; real path containment via
`Path.is_relative_to`, not string prefixing; retained exception,
non-boolean, preloaded-module and sibling-prefix fault tests.

## Verification

* Sidecar pass (sha above); archive pass (287 members, ownership 0:0);
  manifest 11/11; pure vectors 104/104; process gate 61 passed / 3
  skipped; reviewer-override: adapter 15+1 impl-gated, ledger 12/12;
  recorded qualified suite 1,342/14; local 3.53.1 reconciliation as v10.

## Next-round artifacts

* a real-store prune state-machine harness covering valid reparenting,
  missing-copy markers, duplicate canonical rows, and export/import after
  each state;
* an exhaustive ten-field row-validator matrix;
* the literal SCHEMA_V8 constructor plus generated dual-manifest/migration
  evidence;
* a verifier qualification fault matrix.

The archive layout itself is good. The five v10 reproductions were
treated as the acceptance baseline, which is what exposed these shallow
spots in the new fixes.
