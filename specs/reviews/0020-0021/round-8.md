# 0020/0021 external review — round 8 (verbatim, received 2026-08-15)

Package reviewed: `0020-0021-v9-20260815T2214Z.tar.gz`
sha256 `d3645ef8ffd74111abb1f54678afe953c4578d6ed556a4b6e464302aba9471ba`

---

# Review verdict: RETURN FOR AMENDMENT

* **0020:** return
* **0021:** return
* **Coupled seam:** return
* **Archive/integrity:** pass

V9 closes R7-4: policy snapshots now contain primitive strings, and
post-snapshot leaf mutation fails closed. The normal linked A→B→C closure
and improved legacy-note parsing also work. Three blocking construction
defects remain.

## Bin (a) — blocking

### R8-1 — Pruning erases both the intermediate record and the only closure link

The read-side closure works only while the intermediate's free-text
`absorbed_by:` note remains available.

Concrete reproduction:

1. A is absorbed into B.
2. B is absorbed into C.
3. B and C share a scope; A does not.
4. Retention physically prunes B.
5. C retains its direct B contribution row, but B's record—and therefore
   B's `absorbed_by:C` linkage—has disappeared.

`close_absorption_rows("C", direct_rows, {})` returns a closed set
containing C's own-scope digest instead of `None`. Scope membership
therefore classifies C as own-scope, contrary to 0020 §4a-iii and 0021's
"pruned intermediate → unwalkable → UNRESOLVED" rule.

The harness's pruning case deletes B's rows but artificially preserves
its link, so it does not model actual pruning.

Acceptance requires a durable typed contributor link or
closure-completeness marker that survives the intended retention
lifecycle, plus a real write → prune → reopen → classify regression.

### R8-2 — `absorbed_by_id` has no durable source or coordinated format contract

The shipped `Edge` model has no `absorbed_by_id`; real absorption and
export persist only the ambiguous note:

```text
Edge_has_absorbed_by_id False
export_has_absorbed_by_id False
only_durable_link absorbed_by:B
```

An exporter cannot reliably materialize a future structured field from
the same free text whose ambiguity motivated that field.

The carriers also conflict:

* 0020/0021 and the reference call it the next format bump or "FORMAT-7."
* 0020 still says v1 adds no field, schema/format change, or migration.
* 0020 says 0018 is not needed because there is no field.
* Accepted 0016/0018/0019 already freeze the FORMAT-7 shape, and these
  candidates do not amend that contract.

Acceptance requires the exact durable write-time carrier, `Edge`/schema
representation, migration and export derivation, allocated format
version, legacy-export refusal behavior, and corresponding
prerequisite/rider amendments.

### R8-3 — The "exact" import contribution amendment cannot construct or store its rows

0021 defines `ContributionRowPlan` over five fields, while
`ContributionRecord` requires additional fields not supplied or derivable
by the stated contract:

```text
helper_row_keys:
  identity_digest, op_key, site

missing ContributionRecord fields:
  created_at, evidence_ref_digest, id, payload,
  survivor_id, survivor_type, user_id
```

This is especially underdetermined for transitive contributors: an
identity digest does not identify which exported absorbed record supplies
`evidence_ref_digest`. The amendment simultaneously says the store
derives nothing.

There is also a direct schema contradiction. The amendment mandates one
identical `op-<12hex>` value on every row in an import, but the accepted
schema has:

```sql
CREATE UNIQUE INDEX ix_contribution_ledger_op_key
ON contribution_ledger(op_key)
WHERE op_key IS NOT NULL
```

A two-row import inserts the first row and raises `IntegrityError` on the
second. The proposed natural key additionally cannot deduplicate
`identity_digest IS NULL` using ordinary SQLite uniqueness.

The same amendment must precisely reconcile native transitive flattening
with 0014's direct-invalidation exact-set and payload/evidence rules.
`Spec-Requires` should also name 0009 if 0021 normatively amends it.

Acceptance requires a complete stored-row construction, contributor
binding, evidence/payload rules, row IDs/timestamps, workable per-row or
redesigned operation keys, exact DDL/migration, NULL uniqueness
semantics, and atomic multi-row/concurrent-import regressions.

## Bin (b) — nonblocking

* Vector counts drift: 0020 says 60 and `reviews.py` says 81, while the
  manifest and execution report 82/82.
* The reference membership documentation still enumerates only
  `absorption|consolidation`, omitting `imported-absorption`.

## Verification

* SHA-256 sidecar: **pass**,
  `d3645ef8ffd74111abb1f54678afe953c4578d6ed556a4b6e464302aba9471ba`
* Archive safety: **pass** — 280 ordinary files/directories, no links,
  special entries, duplicates, or unsafe paths.
* Vector evidence: **82/82 pass**, recorded result matched.
* Adapter evidence: under an explicit reviewer-only runtime override,
  **15 executed checks pass; 1 is honestly implementation-gated**.
* Process gate: **61 passed, 3 environment skips**.
* Full qualified suite: not reproducible on this host. The package
  qualifies SQLite 3.45.1; this host has 3.53.1. The unmodified run fails
  closed at store opening. A global diagnostic override reached **1,227
  passed, 18 skipped, 111 failed**, with failures concentrated in tests
  intentionally exercising runtime qualification and subprocesses where
  the override cannot propagate. I do not treat that diagnostic run as a
  candidate regression or as a qualified suite pass.

## Requested artifacts for the next round

* A real store fixture using the intended retention API: A→B→C,
  physically prune B, close/reopen, then classify C.
* An implementation-shaped import plan and SQL migration exercising
  multiple rows with one operation, unidentified contributors, idempotent
  re-import, and concurrent imports.
* A carrier/dependency diagram plus final exported record showing the
  structured linkage field, its allocated format version, and migration
  path.

For the archive, make unsupported SQLite an explicit verifier
**SKIP/unqualified-runtime result** instead of an opaque adapter failure,
or ship a reproducible qualified-runtime invocation. The current
execution-mode labels are useful and should remain.
