# Absorption-linkage carriers — the dependency diagram (round-8 artifact ask)

*Answers R8-2's request: where the structured linkage field comes from,
which version carries each piece, and the migration path. One page; the
normative text lives in 0020 §4a-iii and 0021 §7b.*

## The carrier/dependency diagram

```
WRITE TIME (absorption commits, 0021 §4c)
  graph.py ContributionDraft ──contributor_type/contributor_id──┐
  (shipped TODAY — the store drops these fields at persist)     │
                                                                ▼
  contribution_ledger row  ·  + contributor_type, contributor_ref
  (SCHEMA v8 rider: two nullable ALTER COLUMNs — 0021 §7b (2))
  SURVIVOR-LIFETIME-KEYED (accepted 0014 A10 — not append-only): a
  record's rows live exactly as long as it does, so the SURVIVOR'S
  born-closed flattened set is the durable object; NULL on legacy rows
        │                                     │
        │ closure walk (typed refs,           │ exporter query:
        │ 0020 §4a-iii read-time closure;     │ "which survivor's row
        │ close_absorption_rows)              │  names this record?"
        ▼                                     ▼
  READ TIME membership                 EXPORT TIME (portability.py)
  own / SHARED / UNRESOLVED            absorbed_by_id materialised
  (None closure = UNRESOLVED)          FROM THE LEDGER — never from
        ▲                              the free-text note
        │                                     │
        │ import-time reconstruction          ▼
        │ (pre-commit; structured-first, FORMAT-7 RIDER export field
        │ legacy note rule as fallback)  (0021 §7b — rider to the
        └───── IMPORT TIME ◄──────────  0016/0018/0019-frozen shape)
          imported-absorption rows via
          the amended 0009 §4c primitive
          (per-row canonical op keys)
```

## Version allocation — ONE breaking window (0018 D2), three riders

| carrier | version | rider text |
|---|---|---|
| `contribution_ledger.contributor_type` / `.contributor_ref` | SCHEMA v8 | 0021 §7b (2) — exact ALTERs; nullable; legacy rows NULL |
| exported `absorbed_by_id` | FORMAT 7 rider | 0021 §7b (0016+0018 row) — extends the frozen v7 shape, same-commit landing |
| pre-0021 writer refusal (the §4d enforcement) | store-version bump | Q4, ruled round 2 — rides the same window |

No piece mints its own break. The READ feature (0020 v1) needs none of
them to *accept*; they are the coupled implementation's carriers.

## Migration path

1. **Before the window (today → D2):** ledger rows have no contributor
   columns; closure uses the legacy note-walk while absorbed records
   exist; pruned legacy chains are UNRESOLVED (fail-closed; the
   disclosed delta).
2. **At the window (one release):** SCHEMA v7→v8 adds the two nullable
   columns (no backfill — legacy rows stay NULL, the disclosed legacy
   class); FORMAT exports gain `absorbed_by_id` derived from the new
   column; pre-0021 writers are refused (Q4).
3. **After the window:** every new absorption row carries its typed
   link; closure walks the ledger; exports are structured; the legacy
   note rule remains only for old files and old rows, refusing on
   ambiguity.

## A final exported record, with the rider field

An `absorbed_duplicate` edge as a FORMAT-7-rider export writes it
(abridged to the linkage-relevant fields; `absorbed_by_id` is derived
from the ledger's `contributor_ref` column, present iff that row
exists):

```json
{"record": "edge", "id": "c-2", "user_id": "u1",
 "object": "cat Miso", "invalidation_reason": "absorbed_duplicate",
 "note": "absorbed_by:c-3 (restated as 'small cat Miso')",
 "absorbed_by_id": "c-3",
 "provenance": {"origin": "org-b", "source_id": "agent-b",
                "evidence_ref": "ev-c-2", "...": "..."}}
```

Legacy files are identical minus `absorbed_by_id` — they take 0020
§4a-iii's decidable note rule, and ambiguity refuses the whole import
pre-commit.
