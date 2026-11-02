# 0044 §4f-ii — the writer/lifetime matrix (GENERATED: `specs/evidence/0044/writer_lifetime_matrix.py`)

Each cell: `observed` (the inputs that produced it, by running them) or not observed, with its reason.

| ruling key (lifetime) | insert | none | reinstatement | retirement | re-retirement | redaction | erasure |
|---|---|---|---|---|---|---|---|
| `_upsert_edge_row` (choke-point) | **observed** (2) | **observed** (2) | **observed** (1) | **observed** (1) | **observed** (1) | — | — |
| `confirm_edge` (choke-point) | — | **observed** (1) | — | — | — | — | — |
| `_invalidate_edge_row` (choke-point) | — | — | — | **observed** (3) | **observed** (1) | — | — |
| `_reinstate_edge_row` (choke-point) | — | — | **observed** (2) | — | — | — | — |
| `_recompute_edge_row` (choke-point) | — | **observed** (1) | — | — | — | — | — |
| `commit_outcome_import_plan` (choke-point) | **observed** (2) | — | — | — | — | — | — |
| `_redact_in_txn` (choke-point) | — | **observed** (1) | — | — | — | **observed** (2) | — |
| `forget_user` (erasure) | — | — | — | — | — | — | **observed** (1) |

## The driven inputs and how each ended

| input | meant for | ending | hook calls (chain → transition) |
|---|---|---|---|
| add_edge: a new active edge | `_upsert_edge_row` | accepted | _upsert_edge_row → insert |
| add_edge: a new edge arriving retired | `_upsert_edge_row` | accepted | _upsert_edge_row → insert |
| add_edge: a new edge arriving with the marker | `_upsert_edge_row` | refused: ValueError at store/sqlite.py:_upsert_edge_row | — |
| add_edge: same id, retired -> active | `_upsert_edge_row` | accepted | _upsert_edge_row → reinstatement |
| add_edge: same id, active -> retired | `_upsert_edge_row` | accepted | _upsert_edge_row → retirement |
| add_edge: same id, a different retirement | `_upsert_edge_row` | accepted | _upsert_edge_row → re-retirement |
| add_edge: same id, the identical retirement | `_upsert_edge_row` | accepted | _upsert_edge_row → none |
| add_edge: same id, an ordinary mutation | `_upsert_edge_row` | accepted | _upsert_edge_row → none |
| add_edge: same id, the object replaced by the marker | `_upsert_edge_row` | refused: ValueError at store/sqlite.py:_upsert_edge_row | — |
| confirm (Memory.confirm) on an active edge | `confirm_edge` | accepted | confirm_edge → none |
| invalidate_edge on an active edge | `_invalidate_edge_row` | accepted | _invalidate_edge_row → retirement |
| invalidate_edge on a retired edge | `_invalidate_edge_row` | accepted | _invalidate_edge_row → re-retirement |
| undo_restoration of the restored value | `_invalidate_edge_row` | accepted | _invalidate_edge_row → retirement |
| the data migration's restoration (the base's own build: U's and V's retired values) | `_reinstate_edge_row` | accepted | _reinstate_edge_row → reinstatement; _reinstate_edge_row → reinstatement |
| revoke the source, then lift it | `_reinstate_edge_row` | accepted | _invalidate_edge_row → retirement; _invalidate_edge_row → retirement; _reinstate_edge_row → reinstatement; _reinstate_edge_row → reinstatement |
| recompute (driven directly) | `_recompute_edge_row` | accepted | _recompute_edge_row → none |
| redact an edge | `_redact_in_txn` | accepted | _redact_in_txn → redaction |
| import (default) of another store's edge | `commit_outcome_import_plan` | accepted | commit_outcome_import_plan → insert |
| restore of the store's own redacted export over its held copy | `commit_outcome_import_plan` | accepted | commit_outcome_import_plan → _redact_in_txn → redaction |
| import (default) of a record this store lacks, arriving redacted with its notice | `commit_outcome_import_plan` | accepted | commit_outcome_import_plan → insert; commit_outcome_import_plan → _redact_in_txn → none |
| forget_user | `forget_user` | accepted | forget_user → erasure |

## Callers

| ruling key | callers (AST over src/veracium) | callers seen in the run |
|---|---|---|
| `_upsert_edge_row` | store/sqlite.py:SqliteStore.add_edge, store/sqlite.py:SqliteStore.apply_supersession_plan, store/sqlite.py:SqliteStore.expiry_transition | store/sqlite.py:SqliteStore.add_edge |
| `confirm_edge` | __init__.py:Memory.confirm | __init__.py:Memory.confirm |
| `_invalidate_edge_row` | store/data_migration.py:undo_restoration, store/revocation.py:_apply_statement_effect, store/sqlite.py:SqliteStore.apply_supersession_plan, store/sqlite.py:SqliteStore.expiry_transition, store/sqlite.py:SqliteStore.invalidate_edge | store/data_migration.py:undo_restoration, store/revocation.py:_apply_statement_effect, store/sqlite.py:SqliteStore.invalidate_edge |
| `_reinstate_edge_row` | store/data_migration.py:convert_rows, store/revocation.py:_apply_statement_effect | store/data_migration.py:convert_rows, store/revocation.py:_apply_statement_effect |
| `_recompute_edge_row` | store/revocation.py:_apply_statement_effect | — |
| `commit_outcome_import_plan` | portability.py:_preflight_and_commit | portability.py:_preflight_and_commit |
| `_redact_in_txn` | store/sqlite.py:SqliteStore.commit_outcome_import_plan, store/sqlite.py:SqliteStore.confirm_notice, store/sqlite.py:SqliteStore.redact | store/sqlite.py:SqliteStore.redact |
| `forget_user` | __init__.py:Memory.forget, cli.py:_forget | — |

## Not-observed cells, with their reasons

- `_upsert_edge_row|redaction`: a local writer refuses the marker (0041 INV-11's mirror): redaction goes through `redact`
- `_upsert_edge_row|erasure`: a choke-point writer; erasure is `forget_user`'s disposition alone
- `confirm_edge|insert`: confirm rewrites an existing row: an absent edge refuses (`store.confirm.unknown-edge`)
- `confirm_edge|reinstatement`: confirm writes the confirmation flag only; it never changes `invalidated_at`
- `confirm_edge|retirement`: confirm writes the confirmation flag only; it never changes `invalidated_at`
- `confirm_edge|re-retirement`: confirm writes the confirmation flag only; it never changes `invalidated_at`
- `confirm_edge|redaction`: confirm writes the confirmation flag only; a redacted edge refuses confirmation
- `confirm_edge|erasure`: a choke-point writer; erasure is `forget_user`'s disposition alone
- `_invalidate_edge_row|insert`: the invalidate method writes an existing row only
- `_invalidate_edge_row|none`: the method is called on an active row; a retired row refuses before the write
- `_invalidate_edge_row|reinstatement`: the invalidate method only sets `invalidated_at`
- `_invalidate_edge_row|redaction`: the invalidate method writes no marker
- `_invalidate_edge_row|erasure`: a choke-point writer; erasure is `forget_user`'s disposition alone
- `_reinstate_edge_row|insert`: the reinstate method writes an existing row only
- `_reinstate_edge_row|none`: the method is called on a retired row (its callers select retired rows)
- `_reinstate_edge_row|retirement`: the reinstate method only clears `invalidated_at`
- `_reinstate_edge_row|re-retirement`: the reinstate method only clears `invalidated_at`
- `_reinstate_edge_row|redaction`: the reinstate method writes no marker
- `_reinstate_edge_row|erasure`: a choke-point writer; erasure is `forget_user`'s disposition alone
- `_recompute_edge_row|insert`: recompute rewrites valid_from/observed_at/confidence of an existing row
- `_recompute_edge_row|reinstatement`: recompute never touches `invalidated_at` (0044 L325–L328)
- `_recompute_edge_row|retirement`: recompute never touches `invalidated_at` (0044 L325–L328)
- `_recompute_edge_row|re-retirement`: recompute never touches `invalidated_at` (0044 L325–L328)
- `_recompute_edge_row|redaction`: recompute writes no marker
- `_recompute_edge_row|erasure`: a choke-point writer; erasure is `forget_user`'s disposition alone
- `commit_outcome_import_plan|none`: an import's own write is an insert; a held equal record is skipped, never rewritten
- `commit_outcome_import_plan|reinstatement`: an import inserts new ids; a held id is skipped or refused (0009 §4c), never rewritten
- `commit_outcome_import_plan|retirement`: an import inserts new ids; a held id is skipped or refused (0009 §4c), never rewritten
- `commit_outcome_import_plan|re-retirement`: an import inserts new ids; a held id is skipped or refused (0009 §4c), never rewritten
- `commit_outcome_import_plan|redaction`: an imported redaction runs through `_redact_in_txn` (the chain's inner key), never the import's own write
- `commit_outcome_import_plan|erasure`: a choke-point writer; erasure is `forget_user`'s disposition alone
- `_redact_in_txn|insert`: a redaction treats an existing record only
- `_redact_in_txn|reinstatement`: a redaction never clears `invalidated_at`
- `_redact_in_txn|retirement`: a redaction never sets `invalidated_at` on its own
- `_redact_in_txn|re-retirement`: a redaction never changes `invalidated_at`
- `_redact_in_txn|erasure`: a choke-point writer; erasure is `forget_user`'s disposition alone
- `forget_user|insert`: erasure deletes the user's rows (0008 §6g); it writes no edge through the choke point
- `forget_user|none`: erasure deletes the user's rows (0008 §6g); it writes no edge through the choke point
- `forget_user|reinstatement`: erasure deletes the user's rows (0008 §6g); it writes no edge through the choke point
- `forget_user|retirement`: erasure deletes the user's rows (0008 §6g); it writes no edge through the choke point
- `forget_user|re-retirement`: erasure deletes the user's rows (0008 §6g); it writes no edge through the choke point
- `forget_user|redaction`: erasure deletes the user's rows (0008 §6g); it writes no edge through the choke point
