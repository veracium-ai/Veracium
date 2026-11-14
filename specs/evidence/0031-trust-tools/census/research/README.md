# Research's independent write census of the trust verbs (for 0031 trust-tools v0.13)

Research, 2026-11-14 (UTC).

**What this answers.** The round-1 design review (TT-R1-01, TT-R1-02) found that v0.12 scoped each verb's target
without enumerating its writes or its returned fields. Before comparing with dev's list, made apart from it, research
MEASURED both on fresh stores: `probes/write_census.py`, output `write-census-at-544dacb1.out`.
- **The source:** veracium `544dacb1`. Its `src/` is byte-identical to the package pin `78a20f4a`.
- **How it was measured:** sqlite3's trace callback recorded every write statement, and each table was diffed before
  and after the call.
- **The fixture:** the product's own, with no model called.

**Found (all on a store with no scope configured, `source_id` absent):**
- **`correct`:**
  - a new edge, and the target invalidated (`edges`, `edge_event`, `supersession_operations`);
  - an audit episode quoting the OLD and the NEW value, with no `source_id`;
  - `wiki` and `write_counter`.
- **`dispute`:**
  - the target invalidated;
  - an audit episode quoting the fact and the reason, with no `source_id`;
  - `wiki` and `write_counter`.
- **`confirm`:**
  - a confirmations row (`call_path` column `host_api`), and the edge updated;
  - a quoting episode, `(user) confirmed '<relation>: <object>' still holds`, with no `source_id` (TT-R1-01,
    reproduced);
  - `request_registry`, `act_counter` and `write_counter`.
- **`redact`, edge:** writes to 12 tables (`redactions`, `edge_event`, `edge_embedding`, `replies`, `confirmations`,
  `contribution_ledger`, `request_registry`, `supersession_refusals`, `wiki`, `write_counter`, …). It returns a
  `RedactionReceipt` carrying `user_id`, `store_version_before`/`after`, `event_ref`, `receipt_domains` and
  `surviving_derived` (`kind`, `id`, `via`, `note`), which are TT-R1-02's carriers.
- **`redact`, episode:** writes to `redactions`, `episode_event`, `episodes`, `contribution_ledger`, `wiki` and
  `write_counter`, and returns the same receipt type.
- **`forget`:** writes to every erased table, and returns `edges`, `episodes`, `confirmations` and `replies` counts.

**What it means for v0.13.** All three audit episodes (`correct`, `dispute`, `confirm`) QUOTE the target, and today none
carries a source. Under a principal, each needs the binding's source (the review's answer to Q7). Otherwise a
principal's act on a private OWN record writes a quotation into the user-wide SHARED pool. v0.12 named the edge and the
correction and dispute episodes, and wrongly exempted `confirm`.

## Compared with dev's census (made apart from this one; dev's `census-78a20f4a.txt`, sha256 `45a8f84f…`)

**The two censuses agree:** the same tables for correct (7), dispute (6) and forget (21). The source-less replacement
edge and all three quoting audit episodes appear in both. Two writes appear in dev's census only, and each is
CONDITIONAL. v0.13 states each with its condition.
- **`redact` → `UPDATE source_revocations`** happens only when the target's provenance yields a source identity
  digest (`store/sqlite.py`, through `revocation.redact_revocation_reasons`, 0041 §11.2). It rewrites `reason` prose
  only, on that source's revoke and lift rows. Research read the call and agrees with dev's reading.
- **`confirm` → `INSERT edge_event` happens when the confirmation CHANGES the edge's stored serialization, not when
  the edge has a source.** Dev attributed it to `edge.src` and the 0045 path. That path, in `confirm_edge`, is a
  refusal (a redacted source blocks the confirmation), not a write. The journal choke point (`_journal_edge_write`)
  writes an event whenever the bytes change, and confirm changes them when the edge's confidence is below 0.9, its
  `observed_at` precedes the confirmation, or `needs_confirmation` was set.
  - **Measured** (`confirm-journal-condition.out`): an edge with NO source, at confidence 0.9, gets 0 `edge_event`
    inserts; the same edge at confidence 0.5 gets 1.
  - Dev's remembered facts presumably sat below 0.9.
- **Out of the store, from dev's census:** each verb calls `Memory._record` with the user id. `correct`, `dispute`
  and `confirm` send `feedback`; `redact` sends `redact`; `forget` sends `forget` and pops the usage accumulator.
  A configured host audit sink receives these.
- **Why the 0.9 case wrote no event, and the third trigger (dev's seed).** `Memory.confirm` with no `date` stamps
  `confirmed_at` at today's date (`_event_dt(_today_utc())`). The fixture's edges were made moments earlier that same
  day, so `max(observed_at, confirmed_at)` left `observed_at` alone. Confidence was already 0.9 and
  `needs_confirmation` was False, so no byte changed.
  - Dev's seed had confidence 0.9 and `observed_at` two days earlier, so its event came from `observed_at` moving
    forward.
  - The matrix row therefore names all three triggers: confidence below 0.9, `observed_at` earlier than the
    confirmation's instant, and `needs_confirmation` set.
  - The no-change case is an edge at confidence ≥ 0.9, observed on or after the confirmation's instant, and not
    flagged. Dev withdrew the `edge.src` attribution.

## The probes, committed and re-run (2026-11-14, for the 0031 fold)

Every output in this directory now comes from a committed script in `probes/`, re-run on fresh stores at veracium
`544dacb1`, whose `src/` equals the fold's pin. Three of the measurements had first been made by inline commands, and
those are now `census_ops.py`, `confirm_journal_condition.py` and `census_branches.py`.

`write_census.py` decodes JSON through `_strict_pairs`, a hook that refuses a duplicate key (the product's evidence-tree
rule, `test_no_plain_json_load_at_evidence_boundaries`). The gate's own counter finds 0 plain decodes in all four
probes.

**Re-run against the earlier outputs, with generated ids, times and scratch paths normalized:**
- `write-census`, `census-ops` and `confirm-journal-condition` are identical;
- `census-branches` gives the same seven results, with labels changed because one script now runs both wiki
  configurations.
