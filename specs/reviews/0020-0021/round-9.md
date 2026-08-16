# 0020/0021 external review — round 9 (verbatim, received 2026-08-16)

Package reviewed: `0020-0021-v10-20260816T0027Z.tar.gz`
sha256 `555a4c3263279af98af4cf24115ff7236566de223b6b37faffd81a5650f1712b`

---

# Review verdict: RETURN FOR AMENDMENT

* **0020:** return
* **0021:** return
* **Coupled seam:** return
* **Archive integrity:** pass
* **Package verifier contract:** return

V10 substantially closes R8-1's read-time pruning defect and supplies much
better implementation-shaped evidence. Four design blockers and one
verifier blocker remain.

## Bin (a) — blocking

### R9-1 — Flattening makes `absorbed_by_id` reverse derivation non-unique

For A→B→C, the normative reconstruction produces:

```text
contributor A → survivor B, direct
contributor A → survivor C, flattened
contributor B → survivor C, direct
```

Thus the specified exporter algorithm—"find the row whose
`contributor_ref` names this record → its survivor"—has two answers for
A: B and C.

Pruning B makes the opposite problem visible: only the flattened A→C row
remains. Filtering to direct rows then finds nothing, while accepting
flattened rows was ambiguous before pruning. The retention contract does
not specify reparenting A's direct linkage when B is removed.

This breaks the claimed exact durable source for the FORMAT linkage field
and restored-chain portability.

Acceptance requires an exact reverse-link algorithm distinguishing direct
from flattened rows, uniqueness/refusal rules, and explicit reparenting
or incompleteness behavior during pruning. Test both A→B→C before pruning
and A→B→C after B's A10 deletion.

### R9-2 — The per-row op-key encoding is not injective

The proposed key is:

```text
{import_op}:{survivor_id}:{contributor_ref}
```

Both IDs are unrestricted strings and may contain `:`. Two distinct legal
rows collide:

```text
survivor="a:b", contributor_ref="c"
survivor="a",   contributor_ref="b:c"
```

Both produce:

```text
op-1234abcd5678:a:b:c
```

Against the accepted unique index, the first row inserts and the second
raises:

```text
IntegrityError: UNIQUE constraint failed: contribution_ledger.op_key
```

This directly falsifies the "unique per row by construction" claim and
V18/W17.

Use a framed/domain-separated digest or another injective encoding, and
add delimiter-bearing IDs to the real-DDL harness.

### R9-3 — Import row identity and exact equality do not bind the full logical record

The amendment gives incompatible definitions of idempotent equality:

* Multiset equality compares only `(site, identity_digest,
  contributor_ref)`.
* The allegedly equivalent deterministic ID additionally includes
  `evidence_ref_digest`.
* Neither definition includes `payload`; `plan_row_id` also omits
  `contributor_type`.

Executed results:

```text
payload direct→flattened: same plan_row_id = True
evidence digest changed: same three-field tuple = True
evidence digest changed: same plan_row_id = False
```

`payload` is semantic: it decides whether a row is direct or flattened.
Consequently, a direct A→C history and a flattened A→B→C history can be
treated as the same existing row and silently skipped, contrary to
accepted 0009 H4's record-equality idempotency.

The closure reference exposes the related cross-field gap: a row marked
`flattened` but lacking `contributor_ref` bypasses legacy accounting and
classifies as own-scope instead of returning `None`.

Acceptance requires one canonical logical-row projection covering every
semantic field—canonical payload, evidence digest, contributor type/ref,
site and identity digest—excluding only genuinely operational fields such
as the reminted op key and commit timestamp. The validator must reject
contradictory combinations such as `flattened` without a typed
contributor link.

### R9-4 — The D2 rider still conflicts with the accepted frozen schema

V10 changes SCHEMA v8 from the accepted no-DDL refusal bump into a
migration adding two columns. But:

* Accepted 0019's complete final-form rider freezes SCHEMA v7→v8 as
  **no-DDL**.
* 0021 acknowledges the 0016/0018/0019 freeze but drafts a rider only to
  "0016 + 0018."
* `Spec-Requires` omits 0019.
* The candidate supplies two ALTER statements but not the final SCHEMA_V8
  constructor DDL, the complete v7→v8 migration contract, 0007/0013
  amendments, or regenerated schema evidence.

This remains a carrier-completeness failure under R8-2.

Acceptance requires a complete final-form amendment including 0019, the
constructor and migration manifestations, schema-policy/evidence changes,
and corresponding prerequisite/sign-off edges.

### R9-5 — Runtime-verifier defects are mislabeled as environment skips

`verify_package.py` catches every exception from runtime qualification
and converts it to an unqualified-runtime skip. Injecting an internal
defect produced:

```text
SKIP runtime: runtime qualification unreadable
...
NO FAILURES; not a full pass
main_return 0
```

A broken qualification implementation is not evidence that SQLite is
merely unsupported; this can suppress both store-backed harnesses while
returning success.

Only a successfully evaluated `runtime_supported() == False` should skip.
Import errors, malformed evidence, or predicate exceptions must fail
package verification.

## Bin (b)

* The `reference_scope.py` module header still says absence in an
  "append-only ledger means leaf," contradicting its own corrected
  survivor-lifetime model.
* `verify_package.py` still says it executes "both harnesses," although
  the package now has three.

The previous vector-count drift and missing `imported-absorption`
documentation are fixed.

## Verification

* Sidecar: **pass**, SHA-256
  `555a4c3263279af98af4cf24115ff7236566de223b6b37faffd81a5650f1712b`
* Archive: **pass** — 285 ordinary members; no unsafe paths, duplicates,
  links, or special entries.
* Manifest hashes: **11/11 pass**
* Pure vectors: **90/90 pass**
* Process gate: **61 passed, 3 skipped**
* Reviewer-only runtime override:
  * Store adapter: **15 executed checks pass; 1 implementation-gated**
  * Ledger-plan harness: **8/8 pass**
* Recorded qualified suite: **1,342 passed, 14 skipped**
* Local unqualified SQLite 3.53.1 run: **758 passed, 19 skipped, 548
  failed, 31 errors**, dominated by the expected store runtime refusal;
  it is not a comparable qualified run.

## Requested next-round artifacts

* An executable structured-export harness covering A→B→C both before and
  after pruning B.
* Adversarial ledger-plan cases for delimiter-bearing IDs,
  direct-vs-flattened history drift, evidence/payload drift, and
  malformed cross-field combinations.
* The complete final SCHEMA_V8 constructor/migration/evidence package and
  final-form 0019 rider.

For the archive, retain the explicit unsupported-runtime result, but make
qualification-evaluation errors fatal. The execution labels and real-DDL
harness are useful improvements.
