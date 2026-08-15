# 0020/0021 external review — round 7 (verbatim, received 2026-08-15)

Package reviewed: `0020-0021-v8-20260815T2010Z.tar.gz`
sha256 `fd2dcdc3c725cfd8079349d1f44ff0c381ad03c9ed67f0b77802e54c1dc10fce`

---

## Verdict: RETURN FOR AMENDMENT

| Surface                   | Verdict |
| ------------------------- | ------- |
| 0020                      | RETURN  |
| 0021                      | RETURN  |
| Coupled seam              | RETURN  |
| Archive/integrity         | PASS    |
| Test-suite reconciliation | PASS    |

Four blocking bin-(a) findings; bin (b) is empty.

### R7-1 — Transitive absorption bypasses scope membership

This is the architectural blocker.

I reproduced a real store chain:

1. `A` has scope A.
2. `B`, scope B, absorbs `A`; `B` receives an absorption row containing A's digest.
3. `C`, also scope B, absorbs `B`; `C` receives only B's digest.

The resolver examines only `C`'s direct row. Because that digest equals C's own
scope, it classifies C as own-scope instead of `UNRESOLVED`. Export/import plus
v8 reconstruction produces the same result: separate `B ← A` and `C ← B` rows,
with no transitive membership.

This falsifies:

* 0020 §4a-iii's "contributors span scopes → UNRESOLVED" construction.
* 0021 §4d/W9's claim that pre-0021 absorption remains read-side fail-closed.
* Accepted 0014 §4f's premise that no v1 site can consume a
  survivor-with-contributors. Ordinary absorption can already do exactly that.

Acceptance requires an accepted transitive-attribution contract—either flatten
all ancestor identities onto the ultimate survivor or traverse typed
contributor links with a defined incomplete result. The 0014 site capability
must be updated accordingly. Add native-store and export/remap/reopen
`A → B → C` regressions.

### R7-2 — Reconstruction still rejects valid native exports

The regex in `reference_scope.py` treats note punctuation as linkage framing,
but `Edge.id` permits those characters.

I exercised actual store/export/import records with:

* Winner ID `winner (restated as id`
* Winner ID `winner; id`
* A pre-existing note containing `absorbed_by:ghost`, followed by the graph's
  genuine appended tag

The import committed successfully in each case; reconstruction then raised
`ImportLinkageError`. The third case fails because the helper requires earlier
incidental tags to resolve even though its own contract says the last tag
governs.

The corresponding "full import matrix" claim in `store_adapter_harness.py` is
also false: only the remap case calls `import_memory`, and reconstruction
occurs after commit. Whitespace, missing-tag, and unresolvable-tag cases call
the helper directly, so whole-import refusal and rollback are never tested.

Acceptance requires structured linkage or a complete, unambiguous grammar tied
to the allowed ID domain. The actual import path must reconstruct before
commit and prove malformed input leaves destination state unchanged.

### R7-3 — The imported-ledger atomic contract remains descriptive

The new `imported-absorption` direction is viable, but it is not yet a
mechanical construction.

The current primitive in `store/base.py` and `store/sqlite.py` accepts only
edges and episodes. Its expected-state checks cover edge presence, episode
records, and chain heads—not contribution state. Meanwhile reconstruction
emits partial dictionaries with `op_key=None`.

The candidate does not define:

* Complete import-plan row schema and store-side derivation.
* Deterministic row ID/op key.
* Expected ledger state and conflict rules.
* Duplicate/re-import semantics.
* Contribution return counts.
* Rollback and same-file concurrent-import behavior.

Consequently, "rollback, races, restart durability, idempotent re-import all
inherit the primitive's tests" does not follow from the existing 0009
contract.

Acceptance requires an exact 0009 primitive amendment and complete 0014 rider,
including the site registry/manifest, payload validator, transitive
capability, stable row identity, race handling, and durable reopen/re-import
tests.

### R7-4 — "Recursively immutable" and carrier-cleanup claims remain false

The registry now uses tuples and frozensets, but its group snapshot retains
the same `Identity` instances exposed through the policy. `object.__setattr__`
mutates both references, so the snapshot is not recursively immutable.

The behavior still fails closed because the independently stored digest
snapshot detects the mutation; this is not a boundary bypass. It is
nevertheless a false stated closure. Store primitive `(origin, source_id)`
values in the registry, or narrow the claim to the immutable digest anchor.

Two carrier contradictions also remain:

* `_revalidate` says the seal is recomputed over current state, but the code
  explicitly does not recompute it.
* 0021 §2b still says cross-scope reconstruction is "stated-not-built,"
  contradicting §2c, §7a, and `COLLECTED.txt`.

### Verification

* Sidecar: PASS
* SHA-256: `fd2dcdc3c725cfd8079349d1f44ff0c381ad03c9ed67f0b77802e54c1dc10fce`
* Archive: 249 files and 29 directories; no duplicates, unsafe paths, links,
  or special files; ownership normalized to `0:0`
* Package verifier: PASS—8 hashes, vectors `60/60`, adapter `7/7`,
  recorded/fresh comparison
* Local suite: `1339 passed, 17 skipped`
* Packaged result: `1342 passed, 14 skipped`
* Delta reconciled exactly: absent MCP SDK, absent host coordination file, and
  root-euid fixture

### Requested next-round artifacts

The most useful additions would be:

* A real pre-commit import harness covering refusal, rollback, concurrent
  same-file imports, idempotent re-import, and rows after reopen.
* Native and restored three-hop absorption regressions.
* The exact 0009/0014 amendment text plus generated consumption-site manifest
  changes.

The archive layout and hash coverage need no structural change.
`COLLECTED.txt` should, however, distinguish actual import-path executions
from helper-only probes so its evidence claims cannot overstate coverage.
