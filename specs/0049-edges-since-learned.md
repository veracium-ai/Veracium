# Feature spec: `edges_since` means learned — transaction time, not event time

> 🔢 **Numbering note (added 2026-10-10).** This draft was numbered **0048** from 2026-09-24 and is now **0049**: 0048 was claimed three times by research (this, the authenticated-principals draft, and the decay spec), and the owner ruled 2026-10-10 that the DISPATCHED decay spec keeps 0048. The owner's words quoted below ("…with 0048") are kept verbatim and mean this spec. Its 2026-09-24 review package (`review-packages/0048-round1-review-package`, never dispatched; its patch was against 9fd5a71) is removed and must be rebuilt on 0049; it is recoverable at research `e0a4c285`.

Spec-Status: accepted

| | |
|---|---|
| **Author / session** | Adopted by dev 2026-11-15 from research `36a2fdff` (v2.2, sha256 `1e39d4e7…a764`), byte for byte but the status line, this cell, the Version, Internal reviewers and Decision cells, §12's adoption line, and two formatting fixes the accepted-spec gates require (research's agreement, 2026-11-15): §6's `| E3 |` → `| **E3** |` (an invariant id is defined in bold), and §12's two bare module names → their `tests/….py` paths (a module path, not a test-node name), and §12's heading, which the spec-reference gate reads as `## Review closure` (`## 12. Review closure (v2.2)` → `## Review closure (§12, v2.2)`). The candidate's author cell, kept: research (veracium-research-d5), the candidate's author. Research drafted the patch and its cells on a scratch `git archive` export of `9fd5a71`, for dev to apply and own. The ruling is the owner's. |
| **Version** | **ACCEPTED v2.2 — 2026-11-15: the owner's word, first-hand in the dev session: "Adopt and land (Recommended)"; no second design round (round 1: "Resolve and record the amendments before setting the spec to accepted").** Dev's scratch fixes `b86d6046` and `d51dbd1b`, which the v2.2 text cites, LANDED AS the commit that adds this file (`git log --diff-filter=A -- specs/0049-edges-since-learned.md`); the two ids exist only in dev's scratch clone. **v2.2 (candidate; its cells are named at dev's fix `d51dbd1b`, which research's stage 2 read)** — 2026-11-15: round 1's verdict, ACCEPT WITH AMENDMENTS (0049-R1-01 to R1-03, all medium; banked at coordination `9c6580c`), folded into the text. **R1-01:** steps 2–4 run in one read snapshot (§4, §5; cell E5). **R1-02:** E4's claim is narrowed to what its instruments check, and the instruments are a parser-based reference inventory and a SQLite authorizer (§2a; E4a, E4b). **R1-03:** FIRST is pinned across later writes to the same id (§4; cell E6). Also folded: the reviewer's answers on what FIRST means (§4), the episode wording (§8), the absorption example, the new-record and cursor limits (§4, §8), and introspect (§10 Q3: the owner ruled option (b) into this patch). Section 12 records the review closure. Prior: **v2.1** — 2026-11-15: the round-1 design-review package, pinned at veracium `d85b24cc` (the public main, with 0031 §4f's trust tools and the 0042 v12.17 and 0054 v0.7 folds). The patch was rebuilt to apply there byte-exact (the package's `0049.patch`). At the pin, the four cells are red, then green; the mutants M0–M4 give the same outcomes as at `a3dc06f3`; the touched modules and docs readers give 419 passed; and the full suite gives 32 failed, 9,048 passed: 20 are this patch's regeneration gates, and 12 are the test tree's missing history, all passing in a full clone (§2b). §9 Q1's `observed_at` sweep was re-run at the pin. The owner's 2026-11-15 path ruling is recorded in the External review row. Body otherwise v2's. Prior: **v2** — 2026-11-15: re-measured on veracium main `a3dc06f3` and dev's local `eb69dd4f` (one patch, `0049-v2/0049-v2-on-a3dc06f3.patch`, applies to both); the store reads timestamps only; E2's sibling refusal gets its own cell; every cell shown red by a named mutant; the carriers that name `edges_since` (0020, 0041, 0042, the writer inventory) answered in §2d; the full suite's gate list replaces v1's (§2b). Prior: v1 — drafted 2026-09-24 on the owner's ruling, "make edges_since mean 'learned'", which chose option (a) of research's finding (veracium-research, research's own repository [v2: its URL replaced by this name, so the owner is named by role], commit `9bf8eccd`, file FINDING-event-time-vs-record-time.md under proposals). |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line at the top* |
| **Internal reviewers** | research (author); research's stage 1 and stage 2 (research `55b21526`, recheck CLEAN at `d51dbd1b`); dev's application. |
| **External review** | **REQUESTED by the owner, 2026-09-24** ("let's do a quick external review to make sure we're not missing anything with 0048"). The brief is §9. **Confirmed 2026-11-15 (v2.1):** the owner, first-hand in the dev session, as dev relays it: "Quick external review (Recommended)". **Round 1 returned 2026-11-15: ACCEPT WITH AMENDMENTS** (0049-R1-01 to R1-03, medium; banked verbatim at coordination `9c6580c`; §12). |
| **Decision + date** | **ACCEPTED 2026-11-15**, the owner, first-hand in the dev session: "Adopt and land (Recommended)" (design accepted with amendments at external round 1, banked coordination `9c6580c`; the amendments 0049-R1-01..03 closed with executable evidence, §12). |
| **Path** | **full**: it touches `src/veracium/__init__.py`, which is on the GUARDED list. |
| **Scope** | One read-only host API, `Memory.edges_since`, plus one read-only store method, `Store.first_recorded_at`: their docstrings, the row in `docs/api.md`, the tests, and a CHANGELOG entry. **It amends specs/0029's V-INERT** (§2a). There is no schema change, no write path, no MCP surface, and no trust decision. **v2.2, the owner's ruling (2026-11-15):** `introspect()`'s `last_recorded` is renamed `last_observed` in this patch, and `last_recorded` stays as a deprecated alias for one release (§10 Q3). |

## 1. Problem and motivation

`Memory.edges_since(user_id, since)` is documented in its docstring, `docs/api.md` and `docs/recipes.md` as returning edges "*learned* after `since`", which is **when Veracium recorded the fact**. It has filtered on `provenance.observed_at`, and ingest sets that from the EVENT's own date (`ingest._event_dt`: "memory timestamps must reflect when facts held, not wall-clock ingest time"). So the implementation answers "occurred after", not "learned after".

**Measured at `9fd5a71`:** an event dated 2025-09-01, remembered at 2026-09-24T14:58Z, gives `valid_from` = `observed_at` = 2025-09-01, while its journal `recorded_at` is 2026-09-24T14:58Z. `edges_since(2026-09-23)` returned **0**, where the documentation promises 1.

**Still true at main `a3dc06f3` (v2):** the defect is pinned there by E1 as a strict-xfail tripwire (`tests/test_host_queries.py::test_edges_since_means_learned_not_occurred`, landed by dev from research's `0049-tripwire/`). Dev's two-phase suite at `a3dc06f3` reports it as the run's one xfail, and under this patch it passes with the marker removed (`0049-v2/full-suite-at-a3dc06f3.out`).

The documented use is change-detection ("what's new"). The defect silently drops every fact remembered late about an earlier event: backfills, imports and delayed ingest. Conversely, `confirm()` advances `observed_at`, which moved a long-held fact into "learned since".

**Why the test was green:** the superseded test (whose name described filtering on observed_at) remembered events dated 2026-07-01 and 2026-07-10 and queried by those same dates. Event time and learned time coincided in its fixture, so it could not tell the two meanings apart.

**How long:** since the function was added (`0dc62f7`, 2026-07-16).

**Why it was not caught when specs/0029 defined the axis:** 0029 §2 says `observed_at` "is observation metadata, not transaction time", but its consumer inventory for `observed_at` ("provenance, recency") was written by hand and omits `edges_since`.

**The substrate for the fix exists.** specs/0029 (implemented 2026-09-05) journals every edge write with a store-minted `recorded_at`, and no public API accepts it (0029 §4c).

## 2. Field contracts touched

| field / surface | access | meaning | change |
|---|---|---|---|
| `Memory.edges_since` return set | defines | edges whose FIRST journal event's `recorded_at` is after `since` | **changed**: it was `provenance.observed_at > since` |
| `edge_event.recorded_at` (0029) | READ | store-minted transaction time, one clock read per batch | none; read only |
| `provenance.observed_at` | **no longer read here** | caller-suppliable observation time (0029 §2) | none |
| `valid_from` | not read | valid time | none |

| `Store.first_recorded_at(user_id)` | **NEW**, read-only, in the store package | `{edge_id: recorded_at}` of each edge's first journal event: **timestamps only**, with no `state`, `reason` or `kind`. `None` when the store keeps no journal. | new; `store/base.py` (not guarded) |

No stored field, column or schema version changes.

**One pinned count moves, as its own rule requires** *(v1's measurement at `9fd5a71`, kept below as history; at `a3dc06f3` the same gate, `test_shared_attribute_inventory_over_src`, fails again under the v2 patch and is regenerated at landing by its own rule, after the rebase onto 0031 §4f's slices, which move it too. v2 does not restate numbers that the landing tree will change.)*: specs/0031's LIVE attribute partition (`specs/evidence/0031/connection_census.py`), `SRC_ATTRIBUTE_PARTITION`, is "regenerated from the measurement at every src change (an implementation consideration under the same rule)". The move: `dotted/dataflow` 6,800 → 6,812, `SRC_ATTRIBUTE_TOTAL` 7,244 → 7,256, and `SRC_DATA_DUNDERS_IN_DATAFLOW` 133 → 134 (`type(self.store).__name__` in the refusal). Each has its dated comment line, and the frozen at-acceptance row is untouched. `tests/test_0031_proposal_ddl.py::test_shared_attribute_inventory_over_src` caught the drift and passes on the regenerated row.

### 2a. The amendment to specs/0029 V-INERT — the question this spec most needs reviewed

0029 V-INERT: "events are trust-inert and store-local … never in recall/context/export/MCP". Its reason, from 0029 §4: the journal is CONTENT-BEARING (superseded, corrected and revoked states stay readable), and "this retention is acceptable precisely because the surface is operator/substrate-only". Its tripwire, `test_events_are_store_local_and_required`, allow-lists `why.py` and `doctor.py` as the only non-store readers.

**The first patch broke it.** It called `edge_events` from `Memory.edges_since`, which loaded content-bearing payloads into a host API's scope just to read their timestamps. The full suite caught it in `test_events_are_store_local_and_required`.

**The design now:** the journal read stays in the store package, and the host API receives TIMESTAMPS ONLY, through `Store.first_recorded_at`.

**Proposed 0029 text (for dev to fold, with a 0029 version bump).** v2 re-read 0029 at `a3dc06f3`: V-INERT has two carriers, the contract row ("events are trust-inert and store-local") and the §6 invariant row naming `test_events_are_store_local_and_required`. Both get the exception. The tripwire still allow-lists by a grep for `edge_events(` outside the store package, and it passes under the patch.
- **V-INERT row:** "events' CONTENT is trust-inert and store-local — never in recall/context/export/MCP. Exception (specs/0049): `Store.first_recorded_at` exposes each edge's first `recorded_at`, a timestamp carrying no content, to `Memory.edges_since`, its one non-store reader."
- **§4 data-handling:** add "(0049: the first-record timestamp, and nothing else, reaches the host API `edges_since`)".

**What the safeguard checks, and what it does not (v2.2; round 1, 0049-R1-02).** v2 called E4 "a tripwire that cannot be dodged by naming". That was false: E4 matched the text `first_recorded_at\(`. The reviewer's two surviving readers, `self.store.first_recorded_at (user_id)` and `read = self.store.first_recorded_at; read(user_id)`, pass it, and so does a query that reads `state`, then discards it. v2.2 replaces it with two instruments, and claims only what they check:
- **E4a, no second reader, by reference.** A parser-based inventory lists every static reference to `first_recorded_at` in the whole package, the store included, with its enclosing function, attribute references and aliases included. Exactly three are allowed: the two definitions and `Memory.edges_since`. (Research's stage 2 found that an inventory stopping at the store package passed a store method handing the timestamps on under another name. It now scans the store too.) Its negative controls are the reviewer's two survivors, and each must be found. **Limits, stated:** a dynamic access (`getattr` with a computed name, reflection) is outside any static inventory, and an `edge_event` re-query that bypasses the method is 0029's V-INERT inventory's subject, not E4a's. No general Python data flow is claimed.
- **E4b, no payload loaded and none returned.** "Returned" is checked on the values: each is a tz-aware ISO timestamp, two users' maps are isolated, and the map holds only that user's edge ids. "Loaded" is checked in the database: the store query runs under a SQLite authorizer that refuses any read of an `edge_event` column outside {`user_id`, `edge_id`, `seq`, `recorded_at`}. Those are the filter, the order and the two returned columns. A positive control asserts the authorizer saw the read. The reviewer's discarded-`state` mutant must fail it.
- **The 0029 fold** names this exception in every live 0029 carrier, the contract row, the §6 invariant row, and §4's data handling, with 0029's own version and review-closure record. It covers this exception alone.

### 2b. What the full suite says the patch still owes — named here, and left for dev and the reviewer

**v2.1, at the package's pin `d85b24cc`** (the package's `evidence-d85b24cc/full-suite.txt`; the same runner): **32 failed, 9,048 passed, 89 skipped**.
- **20 are this patch's, all other specs' gates:**
  - 9 mutation tables (this time the closure-mutants roll-up fails on two nodes);
  - 7 for 0042 (group 1);
  - 0044's map;
  - 0031's attribute inventory;
  - the audit manifest;
  - one closure command downstream of them.
  The writer inventory now passes, because the patch classes `first_recorded_at` as a READ.
- **12 are the test tree's missing git history.** The run used a `git archive`. All 12 pass in a full clone at the pin with the patch applied.
- The MCP-surface tests are among the skips: the offline runner has no `mcp` extra, and the patch touches no MCP code.

**v2, at main `a3dc06f3`** (`0049-v2/full-suite-at-a3dc06f3.out`; `run_offline.sh`, two-phase, 8 workers in phase 1, python 3.14.7): **20 failed, 8,898 passed, 70 skipped**. E1 passes unmarked. **All 20 are other specs' regeneration or classification gates, none is `edges_since` behaviour:**
- 8 mutation tables pinned to the three changed src files' digests ("stale — run --write"): 0003 obligations, 0003 within-episode, 0041 ×2, 0048 closure, 0048 implementation, C3-01, the closure-mutants roll-up;
- 7 for 0042's inventory, reconciliation and derived keys (group 1 below);
- 1 for 0044's obligation map (pin digest);
- 2 for 0031's attribute inventory and the spec gate's closure command that re-runs it;
- 1 for the audit manifest (group 2 below);
- 1 for the writer inventory, `tests/test_rii_r2_01_writer_inventory.py::test_every_public_store_method_is_classed` (new since v1): `first_recorded_at` is an unclassed public store method. **v2's patch classes it as a READ** (it writes nothing). With that line, the module passes 186/186; without it the gate names exactly `['first_recorded_at']`.

That run's patch predates E2, E2b, E4, the docs row and the writer-inventory line (§6). Those were run module by module, on `a3dc06f3` and on dev's `eb69dd4f` (§6). Every regeneration gate is dev's to re-run on the landing tree.

**v1, at `9fd5a71` (history):** research ran the WHOLE suite on the patched export (`9fd5a71` + the package's patch, CPython 3.12.3): **8 failed, 3,944 passed, 32 skipped**. The pin's own fresh-clone capture has 0 failures, so all 8 belong to this patch. None is a defect in `edges_since`'s behaviour. They are other specs' gates doing their job, in three groups:

1. **specs/0042's decision inventory (6 tests: `tests/test_0042_evidence.py`, `tests/test_0042_reconciliation.py`).**
   - 0042's review keys decisions by LINE. The lines this patch inserts into `src/veracium/__init__.py` shift about 36 later decisions, and the saved inventory reads stale.
   - That is 0042's regeneration workflow (`specs/evidence/0042/decision_site_inventory.py --write`, then the generated review), which is dev's.
   - **The judgement inside it is not mechanical.** The two new refusals in `edges_since` are newly DISCOVERED candidates, and each needs a decision. By 0042's own definition, "a site that can return a decision other than the caller's request (refuse …) enforcing a spec's stated guarantee at a product boundary" is an ENFORCEMENT POINT, and that would need a declared census site. The alternative is to class them as an `internal-invariant` NOT, because the store lacks a capability.
   - **§9 asks the reviewer.** Declaring sites would move 0042's counts, so this lands after 0042 round 15.
2. **The audit manifest (`tests/test_spec_gate.py::test_every_store_mutation_site_carries_a_verdict`).** It is stale because the store package changed. Regenerate with `specs/audit_manifest.py --write`, and give any new site a verdict in `specs/audit_dispositions.py`. `first_recorded_at` is read-only.
3. **Closure evidence (`tests/test_spec_gate.py::test_every_closure_evidence_command_actually_runs`).** This is downstream of group 1: 0042's R2-1 closure command runs the two inventory tests above. It follows once group 1 is regenerated.

### 2d. The carriers that name `edges_since` (v2: each read at `a3dc06f3`, and run where it runs)

Found by `git grep -n edges_since a3dc06f3 -- src specs tests docs`. The same grep over dev's `eb69dd4f` `src/`
finds only the definition: none of 0031 §4f's seven trust tools calls it.

| carrier | what it says | under this patch |
|---|---|---|
| 0020's read-surface disposition (`specs/read_surface_dispositions.py`, rendered in `specs/generated/0020-read-surfaces.md`) | `Memory.edges_since`: returns full `Edge` objects, principal `none`, "UNSCOPED IN v1 BY DECISION", the host's change-detection surface, not on MCP | **unchanged, and true as written.** The returned set is still a subset of `store.edges(user_id, active_only=False, include_quarantined=True)`, the same record objects; only the predicate moves. The return type, principal and MCP exposure are untouched, so no disposition field changes, and the 0020 gates pass in the full suite. |
| 0041's round-9 class sweep (`specs/evidence/0041/round9_sweeps.py`, row "E edges_since") | after a redaction, `edges_since(t - 1 day)` returns the redacted edge carrying the marker: OBSERVED, held by the owner | **the same row, byte for byte.** Run on `a3dc06f3` unpatched and patched (`0049-v2/round9-sweeps-unpatched.out`, `…-patched.out`). The outputs differ in one line only: the minted import ids in "C notice_id", which a second unpatched run shows also vary from run to run. Its edge is written through `add_edge`, which journals it, so the edge is learned at the write. The script is evidence, not a gate; no test runs it. |
| 0042's decision inventory (`reviewed_points.json`, key `__init__.py:Memory.edges_since:…:FILTER_RETURN`) | the filter's return, with a control-flow OVERRIDE | the filter now returns `out`, built in a loop, so the FILTER_RETURN candidate goes and **two RAISE candidates arrive**, the two refusals. Each needs a decision (§2b group 1, §9 Q5). |
| the RII-R2-01 writer inventory (`tests/test_rii_r2_01_writer_inventory.py`, `READS`) | every public `SqliteStore` method is classed as a READ or a WRITER | `first_recorded_at` joins `READS` (in the patch). On dev's `eb69dd4f` the same gate also names `erase_preview_snapshot`, 0031 slice 3's read. That one fails with or without this patch and belongs to that landing. |

## 2c. Untrusted inputs — REQUIRED, blocking

- **`since`** (caller). It is parsed by `datetime.fromisoformat`, as before, and a malformed value raises `ValueError`, as before. A naive value is read as UTC, as before. It is only ever compared, never stored.
- **`user_id`** (caller). It selects the user's rows, as before.
- **Event dates** supplied to `remember(date=…)` (caller). **This spec REMOVES their influence on this answer.** Before, a caller-supplied date decided whether an edge counted as "learned since". After, only the store's clock does.
- **`recorded_at`** is not an input: 0029 mints it from the store's clock, and no public API accepts it (0029 §4c).

### 2c-ii. Assertions about reach — REQUIRED

- `edges_since` is a **host API only**. It is not an MCP tool: `git grep edges_since` over `src/` finds only its definition, and `docs/api.md` says "neither is an MCP tool by design". That is a statement about the trees at `9fd5a71` (v1), and at `a3dc06f3` and dev's `eb69dd4f` (v2), which adds 0031 §4f's seven trust tools and the two framework adapters.
- The new refusals are reachable only through a store whose `edge_events` returns `None`, or that holds an edge without a journal event. The shipped `SqliteStore` journals every edge write (seven `_journal_edge_write` call sites). An import journals a `created` event at import time; I measured that with `export_memory` → `import_memory` on a controlled clock. So the shipped store does not reach the refusals **in the paths exercised here**. That is not a claim that no path could.

## 3. Trust-class matrix — REQUIRED, blocking

`edges_since` asserts nothing. It lists edges, including quarantined and use-only ones, exactly as before. Only the time filter changes.

| author class | effect |
|---|---|
| `user` | untouched: same inclusion rule, now by learned time |
| `third_party` | untouched, as for `user` |
| `system` | untouched, as for `user` |
| `assistant` | untouched, as for `user` |
| quarantined / use-only | still included (change-detection sees everything); no assertion path is touched |

## 3b. Authorization and scope

Unchanged. The caller already holds the `Memory` and names the `user_id`. No scope or entitlement check is added or removed.

## 4. Behaviour

**One snapshot (v2.2; round 1, 0049-R1-01).** Steps 2–4 (the timestamp map, the edge listing, the validation and the result) run inside one read snapshot, the store's existing `read_window(user_id)` or an equivalent single-snapshot operation. Two separate reads let a writer commit an edge and its `created` event between them, so step 4 refused a complete journal ("no journal event"). The fix is never to skip a missing entry, substitute event time, or retry without a bounded rule.

1. Parse `since` as before.
2. Ask the store for each edge's first-record time: `store.first_recorded_at(user_id)`. The store reads its journal in `seq` order and returns timestamps only.
   - **If it is `None`, REFUSE** with `NotImplementedError`, naming 0029: the store cannot supply first-record times. (v2.2: the reviewer's precision. A custom store may keep a raw journal and still return `None`, the inherited default, until it implements the projection.)
   - It never falls back to event time. This follows the 0027 receipt precedent: never a silent substitute.
3. For each edge id, "learned" is the `recorded_at` of its **first** event, first in `seq` order for this local id. It is not the minimum timestamp, and not the latest mutation. Confirming, updating, redacting or reinstating the same id never resets it (v2.2; round 1, Q2 and 0049-R1-03).
   - A `created` event is the store's own write.
   - An edge that predates the journal has a `baseline` first event, stamped at the migration, so it reads as **learned at or before** the migration.
4. Return every edge of the user (active or not, quarantined or not) whose learned time is **after** `since`.
   - An edge with no journal event **REFUSES** with `ValueError`, naming the edge. Its learned time is unknown, and it is not guessed.

**Consequences, all intended:**
- `confirm()` no longer moves an old fact into "learned since".
- A supersession creates a new edge, which reads as learned when the correction was recorded.
- **v2.2 corrects v2's absorption example (round 1, Q2).** v2 said "a re-mention absorbed into an existing edge is not new learning". In the shipped graph path, `Miso` followed by `cat Miso` creates a NEW survivor id and retires the prior, so the survivor qualifies. Reinforcement also persists a new incoming row. Same-id restatements and updates never qualify.
- **A new-record listing, not a change feed.** Deletions and modifications of old ids do not appear merely because they happened later, and the method is not a detector of semantically novel facts.
- **A strict timestamp cutoff is not a lossless cursor.** `recorded_at` is monotone-guarded but can be equal across transactions, and `seq`/`txn` remain the ordering authority (0029). A host polling with a cutoff can miss an edge recorded at the cutoff's exact instant in a later transaction. No cursor API is asked here.
- An import reads as learned when **this store** received it. (v2.2: both forms, measured by dev on `d85b24cc` + the patch. `import_memory` and `restore=True` each write one `created` event at this store's import time: 19:06:42.03Z and 19:06:42.12Z against the source's 19:06:40.69Z. A same-user import keeps the id, and a cross-user import mints one. A restore does not carry the source store's times. E6 pins all three.)

## 5. Regime analysis — where does this behave differently?

- **A fresh store:** every edge has a `created` event, and the answer is exact.
- **A store migrated to the journal (schema v13+):** pre-journal edges answer "learned at or before the migration". Right after a migration, a query with `since` earlier than the migration returns them all. That is loud and conservative for change-detection; it never silently drops them.
- **A host store without the journal:** it used to answer, wrongly. It now refuses. **This is a behaviour change for such hosts**, and it is reversible (§7).
- **The clock:** the store's own clock (`SqliteStore(clock=…)`), one read per batch (0029 §4c). A `remember` batch therefore shares one learned time.
- **Concurrent writers (v2.2):** a write committed while `edges_since` reads is either wholly before the snapshot (it appears) or wholly after it (it does not, until the next call). It never makes the method refuse. Under SQLite's journal mode the snapshot may affect writer waiting, as `read_window`'s contract already states.
- **Cost (round 1, Q4):** O(J) over the user's journal events, later mutations included, plus the edge listing. The map is O(E) in distinct ids. No index is added. High-frequency polling over long histories is a regime to measure before any claim of scale.

## 6. Invariants and executable checks — REQUIRED, blocking

| id | invariant | executable check | shown RED on the unpatched code |
|---|---|---|---|
| **E1** | "learned" is transaction time: event dates do not decide membership | `tests/test_host_queries.py::test_edges_since_means_learned_not_occurred`: events dated 2025 and 2024, remembered on a controlled store clock on 07-01 and 07-10. `since` 07-05 gives the 07-10 fact only, 07-11 gives none, 06-01 gives both. | **YES**: at `9fd5a71` with only this file replaced, `assert (0 == 1)`, because the unpatched filter read the 2024/2025 event dates |
| **E2** | no silent substitute: a store with no journal refuses | `tests/test_host_queries.py::test_edges_since_refuses_a_store_without_a_journal` | **YES**: unpatched, `Failed: DID NOT RAISE NotImplementedError` (v1). v2: the mutant that falls back to event time when `first_recorded_at` is `None` (M2) fails this cell alone |
| **E2b** (v2) | no guess: an edge the journal has no event for refuses by name | `tests/test_host_queries.py::test_edges_since_refuses_an_edge_without_a_journal_event` | **YES, by mutant**: skipping such an edge instead of refusing (M3) fails this cell alone |
| **E3** | the listing includes non-assertable material, as before | the `assertable` assertion inside E1's test | carried from the superseded test |
| **E4** (v2; replaced in v2.2 by E4a and E4b, round 1 R1-02) | the V-INERT amendment holds: `first_recorded_at` has exactly one non-store reader (`edges_since`), and every value it returns is a timestamp, not a payload | `tests/test_host_queries.py::test_journal_timestamps_reach_only_edges_since_and_carry_no_content` | **YES, by mutant**: `first_recorded_at` returning `ev.state` (a JSON string, so a plain `isinstance(str)` check would pass it) fails 2 tests. The pin requires each value to parse as a tz-aware ISO timestamp. v2 re-ran it on the v2 store query (selecting `state` for `recorded_at`, M1): E1 and E4 fail. A second non-store reader of `first_recorded_at` (M4) fails E4 alone. |
| **E4a** (v2.2) | every static reference to `first_recorded_at` in the whole package, the store included, is one of three: the two definitions (`Store.first_recorded_at`, `SqliteStore.first_recorded_at`) and the one caller (`Memory.edges_since`). Constant-string `getattr` is included. Limits: a computed name; an `edge_event` re-query that bypasses the method, which is 0029's V-INERT inventory's subject | `tests/test_host_queries.py``::test_journal_timestamps_reach_only_edges_since_and_carry_no_content`, `::test_the_reference_inventory_sees_every_static_form[*]` (9 forms), `::test_the_inventory_sees_a_store_method_handing_the_timestamps_on`, `::test_the_inventory_limit_is_a_computed_name` | **by negative controls,** each found: the reviewer's `first_recorded_at (user_id)` and alias forms, a class-level reference, a constant-string `getattr`, `operator.attrgetter`, `functools.partial`, a lambda wrapper, a module-level helper, an override outside the store, and (research's stage 2, S5) a store method handing the timestamps on under another name |
| **E4b** (v2.2) | no payload loaded and none returned: the store query reads only the `edge_event` columns {`user_id`, `edge_id`, `seq`, `recorded_at`} (a SQLite authorizer installed on the connection the query runs on), and every returned value is a tz-aware timestamp, isolated per user | `tests/test_host_queries.py``::test_edges_since_loads_no_journal_payload_column` (positive control: the authorizer saw the read of `recorded_at`), `::test_the_authorizer_refuses_every_query_shape_that_loads_a_payload_column[*]` (6 shapes) | **by mutant:** the reviewer's select-`state`-and-discard mutant, `SELECT *`, a JOIN into `edge_event`, a subquery and a CTE are each refused |
| **E5** (v2.2) | one snapshot: a concurrent writer never makes `edges_since` refuse | `tests/test_0049_edges_since_learned.py``::test_e5a_under_wal_a_writer_between_the_two_reads_is_not_a_missing_event`, `::test_e5b_under_the_default_journal_the_writer_waits_for_the_window`. Two cells, because `read_window` behaves differently by journal mode (`sqlite.py` `read_window`'s contract). **(a) WAL:** the reviewer's two-connection schedule, the writer committing between the reads: the pre-insert result, then the new edge on the next call. **(b) The default journal:** the writer on its own thread waits on the window, and is held until the window closes. The result is coherent, and the write's own outcome is asserted | **YES:** without the window, the two-read construction raises "no journal event" in both modes (dev's Phase 0) |
| **E7** (v2.2, the owner's ruling) | introspect: `last_observed` and the deprecated alias `last_recorded` carry the same value, `max(observed_at)` | `tests/test_0049_edges_since_learned.py``::test_e7_last_observed_is_max_observed_at_and_last_recorded_is_its_deprecated_alias`; the CLI line in `tests/test_introspect_cli.py` | **by mutant:** the alias dropped; the new key computed differently |
| **E6** (v2.2) | FIRST across the id's lifetime: confirm-later (created Jul 1, confirmed Jul 10, cutoff Jul 5: not returned), a same-id update and reinstatement, the strict-equality cutoff, and the baseline and import regimes | `tests/test_0049_edges_since_learned.py``::test_e6_a_later_confirm_does_not_make_an_old_edge_newly_learned`, `::test_e6_a_later_update_of_the_same_id_does_not_reset_learned`, `::test_e6_a_reinstatement_of_the_same_id_does_not_reset_learned`, `::test_e6_the_cutoff_is_strict`, `::test_e6_a_migration_baseline_is_an_upper_bound_on_learning`, `::test_e6_an_import_is_learned_when_this_store_received_it[import_memory, restore, cross-user]` | **by mutant:** LAST (`out[edge_id] = recorded_at`, dev's) fails three cells, and so does research's stage-2 spelling of it, `ORDER BY seq DESC` with `setdefault` kept |
| (0029) | V-INERT's own tripwire still holds: no non-store file calls `edge_events` except `why.py` and `doctor.py` | `tests/test_0029_carrier.py::test_events_are_store_local_and_required` | it FAILED on the first patch, which is how §2a was found |

**v2's red-then-green record** (`0049-v2/mutants-e2e4.out`). The v2 cells run on `a3dc06f3` + the patch: 5 passed. On unpatched `a3dc06f3` with the same test file: E1, E2, E2b and E4 fail, and only `test_list_entities_counts_per_user` passes. E2 fails there on the base `Store` lacking `first_recorded_at`, before it reaches the refusal; M2 shows the refusal itself. Mutants M1–M4 are killed as above, and a no-op control (M0) passes 5/5. On dev's `eb69dd4f` + the patch (it applies without conflict), `tests/test_host_queries.py`, the writer inventory and `tests/test_0029_carrier.py` give 210 passed and 1 failed: the writer inventory's `erase_preview_snapshot`, which fails identically without the patch (§2d).

The superseded test (whose name described filtering on observed_at) is **removed**. Its name pinned the mechanism, and its fixture could not tell the two meanings apart (§1).

## 7. Failure modes and reversibility

- **Fully reversible:** a single-commit revert restores the old filter. No stored state is written or migrated.
- **The failure mode introduced:** a host store without `edge_events` now refuses where it used to answer. It fails loudly and names the reason. The old answer was wrong for such a store, since it was event time presented as learned time, so a refusal is not a regression in correctness.
- **Cost:** one journal read per call. v2's store query selects `edge_id` and `recorded_at` only (`SELECT edge_id, recorded_at FROM edge_event WHERE user_id=? ORDER BY seq`), so no payload is read; v1 read the payloads. That is acceptable for a host/admin query. A per-edge "first recorded_at" index is a later optimisation if one is ever measured to be needed.

## 8. Claims and limits

- **Claim:** at this spec's pin, `edges_since` answers "recorded by this store after `since`", using the store's clock.
- **Limits:**
  - Pre-journal edges are known only to within "at or before the migration".
  - "Learned" is per store: an import is learned at import.
  - Reinforcement (`confirm`) is not learning.
  - Ordinary episodes do not have a general first-record-time carrier. (v2.2, round 1: v2 said "no transaction time at all", but `episode_event.recorded_at` exists for redaction at the pin.) A general one is out of scope here.
  - A new-record listing, not a change feed; a strict timestamp cutoff, not a lossless cursor (§4).
  - E4a and E4b check the properties they name. A dynamic access is outside the static inventory, and no claim covers general data flow (§2a).

## 9. Brief for the external reviewer

**The ask is narrow: are we missing anything?** The mechanism is one filter in one read-only host API. The patch, the cells shown red on the unpatched code, and the full suite on the patched tree ride in the package.

**The questions, most valuable first:**

0. **§2a: is the V-INERT amendment sound?**
   - Does a first-record TIMESTAMP reaching a host API reopen any of the reasons 0029 made the journal store-local?
   - Could it leak something through TIMING: for example, the existence or re-creation of a revoked or redacted edge?
   - Is E4 a tripwire that a future edit cannot dodge?
   - **Research's own reading, for the reviewer to attack:** the returned set is still a subset of `store.edges(user_id, active_only=False, include_quarantined=True)`, exactly as before. Only the predicate changes. So no row becomes newly visible. The only new information is the first-record time of rows the caller could already list, observable only through their inclusion or exclusion. Erased users' events are deleted by 0029 V-ERASE. A journal entry for an edge the store no longer lists is looked up by no one.

1. **Is `edges_since` the only consumer that reads event time as record time?** Research's derived sweep read every product reader of `provenance.observed_at` at `9fd5a71` (`git grep observed_at -- src/veracium`, excluding comments and writers).
   - All but two use it as OBSERVATION time: recency, age, "unrefreshed since", recall tie-breaks, absorption max/min.
   - **The second hit is `introspect()`'s `last_recorded`** (`src/veracium/introspect.py`, printed by the CLI as `first_known → last_recorded`). It reports `max(observed_at)`, which is observation time under a record-time name, beside `first_known = min(valid_from)`, which is valid time. So one printed span mixes two axes.
   - It is not on MCP, no spec freezes it, and its only test asserts presence. **We have not changed it** (§10 Q3). *(v2.1: re-run at the pin `d85b24cc`, the same command gives 93 lines against 81 at `9fd5a71`. The new hits are a migration writer, ordering tie-breaks, a field-description table that calls it "when it was observed", confirm and consolidation writers, and a moved liveness comment. None reads it as record time. 0031 §4f's trust tools read none. `last_recorded` is unchanged, at `introspect.py` lines 81 and 111. The package's `evidence-d85b24cc/observed-at-readers.txt` has the full listing.)* Is it the same defect? Is there a third one the sweep's method could not see, for example record time inferred from a field other than `observed_at`?
2. **Is "learned = the `recorded_at` of the edge's FIRST journal event" the right definition?**
   - A `reinstated` edge (invalidated, then revived under the same id) keeps its original learned time.
   - A re-mention absorbed into an existing edge is not new learning.
   - An import is learned at import.
   - A pre-journal edge is learned "at or before" its migration baseline.

   Which of these would a change-detection caller consider wrong?
3. **Is refusing the right failure** for a store without a journal, and for an edge without a journal event? Would a caller prefer a degraded answer with an explicit flag?
4. **Cost:** each call reads the user's whole journal (v2: its edge ids and timestamps, no payload). Is that acceptable for a host/admin query, or does it need an index?

5. **§2b.1: are the two refusals in `edges_since` 0042 enforcement points** (they refuse a caller to uphold 0049's "never answer from event time"), or internal-invariant NOTs (the store lacks a capability)? The answer decides whether this change declares census sites. **Research's leaning (v2): enforcement**, as two ids under 0049 §4 (E2 and E2b): they refuse a host's request to uphold a stated guarantee at a public API. The same reasoning appears in research's stage-1 classification of 0031 §4f's candidates (2026-11-15). A wrong NOT is caught by nothing downstream; a wrong enforcement costs one exercised site.

**What we are NOT asking:** whether 0029's journal is correct (it is accepted), or whether episodes should gain a record time (a separate question, recorded in research's finding).

## 10. Open questions

1. ~~The acceptance path.~~ **Ruled 2026-09-24: a quick external review**, confirmed 2026-11-15 (see the External review row).
2. **Whether the `Edge` a caller reads should carry a read-only `recorded_at`,** so that callers stop reaching for `observed_at`. That is out of scope here; the finding lists it.
3. **`introspect()`'s `last_recorded`** (§9 Q1). **Round 1 answered (b):** rename it to `last_observed`, with a compatibility transition for the existing key, and present valid time and observation time separately. Option (a) would be a different metric, and a second V-INERT consumer needing its own review. **RULED by the owner, 2026-11-15, first-hand in the dev session as dev relays it: inside the 0049 patch.** `last_observed` is the new key with the same value (`max(observed_at)`, observation time). `last_recorded` stays for one release as a **deprecated alias** carrying the identical value, with a CHANGELOG deprecation note, and is removed in a later release. **Check (E7):** both keys carry the same value. Two mutants must fail it: the alias dropped, and the new key computed differently. *(v2.1 text follows.)* Options: (a) the latest journal `recorded_at` for the user (a true record time); (b) rename it to `last_observed` and keep the value; (c) leave it. Research leans (a), and would also rename `first_known` or document it as valid time, so the CLI's span is on one axis. **This is held for the reviewer's answer; it is not in this patch.**

## 11. The CHANGELOG entry (v2: text for dev, who owns the heading it lands under)

- **Fixed: `edges_since` now means LEARNED, as documented (specs/0049).** It filtered on `provenance.observed_at`,
  which ingest sets from the EVENT's date, so a fact remembered today about last year's event was missing from
  `edges_since(yesterday)`: the documented use, change-detection, silently missed every backfill, import and delayed
  ingest. It now reads the `recorded_at` of each edge's first specs/0029 journal event (the store's transaction time)
  through the new read-only `Store.first_recorded_at`, which returns timestamps only, so the journal's content stays
  store-local (0029 V-INERT, amended by 0049). Edges older than the journal read as learned at or before the migration
  that added it. A store without the journal, and an edge with no journal event, refuse rather than answer from event
  time. The superseded test queried by the same dates it remembered with, so it could not tell event time from
  learned time; its replacement remembers past-dated events on a controlled store clock.

- **v2.2 additions (round 1):**
  - **One snapshot.** `edges_since` reads its timestamps and its edges in one read snapshot, so a concurrent writer no
    longer makes it refuse.
  - **A new-record listing, not a change feed.** It lists records this store first recorded after `since`. A strict
    timestamp cutoff is not a lossless polling cursor: two transactions can share a `recorded_at`. Edges older than the
    journal read as learned at or before the migration, an upper bound, not an exact learning time.
- **Deprecated: `introspect()`'s `last_recorded`.** It is renamed `last_observed`, with the same value, the latest
  observation time (`max(observed_at)`). It was never a record time. `last_recorded` remains for one release as a
  deprecated alias with the identical value, and is removed after that (specs/0049).

## Review closure (§12, v2.2)

**Round 1 (design), 2026-11-15: ACCEPT WITH AMENDMENTS.** Banked verbatim at coordination `9c6580c` (`outbox/archive/0049-round1-verdict-verbatim.md`). It accepted the first-local-record-time design and the narrow V-INERT exception. The patch was not ready to land.

| finding | what it blocks | where v2.2 answers it |
|---|---|---|
| 0049-R1-01 (medium): two reads can falsely report a missing event under a concurrent insert | the change as patched | §4's one snapshot; §5; E5 |
| 0049-R1-02 (medium): E4 misses equivalent reader forms and a payload that is loaded, then discarded | acceptance of the claimed safeguard | §2a narrowed; E4a, E4b; §8 |
| 0049-R1-03 (medium): LAST passes every test | acceptance of the regression coverage | §4 step 3; E6 |

**Research's stage 2** on dev's fix (`b86d6046`, then `d51dbd1b`): 564 passed. Research's own mutants were S2 (LAST by `ORDER BY seq DESC`), S4 (a discarded payload query), S5 (a timestamp map laundered through a store method) and S6 (a retirement naming an unrelated site). Each is killed at `d51dbd1b`, and the control is clean. S5 and S6 survived `b86d6046` and were fixed (SF1, SF2), with the docstring's "change-detection sees everything" removed (SF3). The record is `proposals/evidence-0049-v2.2-stage2/`.

**Text obligations, all folded:** §8's episode wording; the absorption example; the baseline caveat in the docs and the release note; the new-record and cursor limits; the 0029 fold into every live carrier. **Ruled by the owner:** introspect, option (b), into this patch (§10 Q3; E7). **Q5:** both refusals are ENFORCEMENT, as research's stage 1 classed them. Their census sites are declared and regenerated on the landing tree.

**Adopted 2026-11-15** by dev from research `36a2fdff` on the owner's word ("Adopt and land (Recommended)"), with 0042 v12.18 (research `f4bf9cb3`); the patch landed in the same commit as this file.
