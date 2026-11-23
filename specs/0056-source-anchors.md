# Feature spec: source anchors — a memory knows when the file it came from changed

Spec-Status: draft

| | |
|---|---|
| **Author / session** | research (veracium-research), candidate v0.4.1; adopted as a draft by dev 2026-11-23, a byte copy of research `b8b713bb` (sha256 `0ffba34f…2103`) with this cell the one declared delta. Dev owns this cell from adoption. |
| **Version** | **v0.4.1 — 2026-11-23: the owner's rulings on Q11 and Q13 folded in as decided**, first-hand to dev (dev's AskUserQuestion, 2026-11-23), relayed by dev: Q11 *"Refuse (Recommended)"*, Q13 *"No (Recommended)"*. No design change: both rulings take what v0.4 already specified. **Prior: v0.4 — 2026-11-23: dev's re-read of v0.3 folded in** (three BLOCKING items found in v0.3's folds, R1–R3, and N1–N5). R1: the record-quoting episodes 0041 already names as derived content (a `confirm()` episode, an outcome episode, a dispute episode) write derivation links to their target's anchors, so a withheld edge cannot go on being asserted through them. R2: protection is stored per survivor as rows naming the protector, and is recomputed when the protector is redacted or erased. R3: the observation implied by `remember(source=)` only moves anchors toward `changed`, never clears. N1: the policy row is store-level and never erased. N2: a policy switch is measured and audited. N3: the I19 digest-map sentence is dropped (dev's own correction). N4: D2 lists nine guarded files; briefings carry `flag`'s markers; MCP is unchanged. N5: §7 says "latest observation". **Prior: v0.3 — 2026-11-23** (research `3840b109`): dev's internal review of v0.2 folded in (five BLOCKING items B1–B5, the answers to Q3, Q5, Q8, Q9 and Q10, the §9 challenges and the smaller items; dev's review text, sent to research 2026-11-23). B1: an anchor conflict on a reused `evidence_ref` is refused. B2: a derived record's anchor set is decided at derivation and written as links, never re-walked from the ledger at read. B3: a withheld edge gets its own fence clause. B4: as-of reads the restriction from its own carrier, as a current restriction. B5: episodes are withheld too. The policy becomes a store fact (§9 challenge 2); `remember(source=)` counts as an observation; bindings are append-only; default import drops anchors. Every code citation re-read at `b256e348`. **Prior: v0.2 — 2026-11-23** (research `96de63a7`): the owner's four decisions folded in (Q1, Q2, Q6, Q7). **v0.1 — 2026-11-23** (research `27dcf794`): first draft. |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line at the top* |
| **Internal reviewers** | research (author) · dev (reviewed v0.2 on 2026-11-23: five BLOCKING, B1–B5, folded at v0.3; re-read v0.3 the same day: three BLOCKING found in the folds, R1–R3, and five notes, folded at v0.4; checked v0.4 the same day: R1–R3 answered, **dev's adoption hold lifted**; one pre-release note added to Q8) |
| **External review** | required: the change touches guarded files (D2: `GUARDED` holds 12 files at `b256e348`; the build touches nine: `src/veracium/schema.py`, `src/veracium/ingest.py`, `src/veracium/__init__.py`, `src/veracium/gate.py`, `src/veracium/graph.py`, `src/veracium/store/sqlite.py`, `src/veracium/portability.py`, `src/veracium/compile.py`, `src/veracium/proactive.py` (briefings carry `flag`'s markers, §4e). Unchanged: `src/veracium/mcp_server.py` (MCP `recall` returns the rendered context only, so markers reach it through the renderer and `Recall.sources` does not), `src/veracium/lifecycle.py`, `src/veracium/introspect.py`. The build also touches unguarded `src/veracium/redaction.py`, `src/veracium/scope_linkage.py` and the as-of carrier) · not yet sent |
| **Decision + date** | — (the owner's decisions on Q1, Q2, Q6, Q7, Q11 and Q13 are recorded in §10) |
| **Path** | full, by D2 (the list above, derived from `specs/check_spec_reference.py`'s `GUARDED` at `b256e348`) |

**Spec-Requires:** 0006 (`source_id` and its invariants I1, I5), 0008 (`confirm()` as the only path that clears
`needs_confirmation`, and its call-path audit), 0014 (the contribution ledger, read at derivation), 0021 (a
consolidation output clears inherited identity), 0023 (the grounded / fenced partition), 0028 (as-of's own carrier,
V-ONE-CLOCK), 0029 (the edge journal and `EDGE_WRITE_SITE_RULINGS`), 0041 (targeted redaction and its side-table
treatments), 0042 (INV-7's one-return rule on `Edge.assertable`), 0044 (erasure), 0047 (the wiki's `assertion_view`
eviction and bind), 0055 (credential screening and the I19 digest map).

**Read against:** dev's `origin/main` at `b256e348`, a `git archive` export; nothing run. Every code citation below
is to that commit.

---

## 1. Problem and motivation

A memory learned from a file or from code goes on being served after the file changes or is deleted. Veracium records
which event a fact came from (`Provenance.evidence_ref`, and `source_id` for the producing source), but neither is ever
tied to the content of an outside artifact or rechecked: `source_id` is "DIAGNOSTIC … grants no trust and changes no
answer" (0006 I5), and `evidence_ref` is an audit reference the host may set or reuse, generated only when absent
(`src/veracium/ingest.py:340`). A changed source reaches the store only if the host feeds it in again as a new event.

Three systems shipped a remedy in one week (research's parity catalog, row 19, research `05857deb`, read at source):
SuperLocalMemory fingerprints a memory's `source_file` at save and shows `source: changed / missing` at recall, and
states that a stale source "never retires or hides a memory"; OKF Agent Memory's `--drift-git` flags concepts whose
code references have newer commits; ClickHouse Loom's README says memories "linked to the code they are about … are
flagged when it changes". Marketing's Scan #20 also reports user demand for the neighbouring case: memories derived from
a deleted source that keep coming back.

**If we do nothing:** a coding or document agent built on Veracium asserts facts about a file that no longer says them,
with full user-grade authority, and the operator has no way to ask which facts rest on which file.

**What we add beyond parity:** the competitors flag. Veracium can also *withhold*: take facts that rest on a changed
source out of the assertable set until a person or a new event resolves them, and carry that through consolidation and
absorption, so a summary built from a stale file is not a way around it.

**Alternatives rejected:**
- **Veracium reads the files itself.** Rejected (the owner's decision, Q2): Veracium may run beside sources it cannot or
  must not open; it would put a file reader on the recall path (§7) and raise a privacy question. The host computes
  fingerprints; Veracium compares them, and ships a helper only the **host** calls (§4a, S8).
- **Anchor through `source_id`.** Rejected: 0006 I5 fixes it as diagnostic, and it names a producer, not an artifact
  version.
- **Reuse `needs_confirmation` for withholding.** Rejected: it does not affect assertability (`src/veracium/gate.py:170`
  partitions on `assertable` alone), and 0008 makes `confirm()` the only path that clears it.
- **Decide the withheld state at the gate, at read** (dev's §9 challenge 2, answered). Rejected: 0047's wiki eviction
  and bind run off `assertion_view` at each **write**, so a state decided at read is invisible to them and a cached
  wiki body would go on asserting; and 0029's journal records edge state per write, which gives as-of a carrier (B4).
  The state is materialised.
- **Find a derived record's anchors by walking the 0014 ledger at read.** Rejected (dev's B2): 0041 redaction CLEARs
  `contribution_ledger.evidence_ref_digest` (`src/veracium/redaction.py:112`, `:116`), pre-v8 absorption rows carry no
  `contributor_ref`, and 0021 prune rows name moved or missing contributors. Each would silently drop an anchor and
  un-withhold a derived record: fail-open. The set is decided at derivation and written as links (§4c).

---

## 2. Field contracts touched

Consumers were enumerated by **reading** the consuming code, not by text grep alone (dev's B4: a text grep of
`.assertable` hits docstrings and a keyword argument in as-of).

| field / table | read / written | its contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `Provenance.evidence_ref` | **read**: the anchor key, as 0014's `evidence_ref_digest(origin, evidence_ref)` | an audit reference, host-supplied or generated (`src/veracium/ingest.py:340`); **not unique**: no UNIQUE constraint, and the library itself passes fixed refs (`"trust-tools:source-probe"`, `src/veracium/__init__.py:2177`; `f"dispute:{edge_id}"`, `:2245`) | 21 files under `src/` | **yes**: read only. Its non-uniqueness is handled by B1's refusal (§4a) |
| `source_anchor` (new) | written at `remember(source=)`; read at recall, observation, derivation | an anchor id, `(user_id, evidence_ref_digest)`, and its bindings | — | n/a (new) |
| `source_anchor_binding` (new) | **append-only** `(anchor_id, seq, locator, fingerprint, bound_at, by)`; the current binding is the highest `seq` | what the anchor's locator and fingerprint are; `confirm_source` appends, never overwrites | — | n/a (new) |
| `source_observation` (new) | written by `observe_sources`, and by `remember(source=)` only toward `changed` (R3); read at every flip | the latest fingerprint the host reported for a locator, or its absence, plus a per-user `last_observed_at` | — | n/a (new) |
| `source_derivation_link` (new) | written at each derivation and by each record-quoting episode writer (§4c), in its own transaction | `(survivor_type, survivor_id, anchor_id)`: the survivor rests on the anchor | — | n/a (new). Carries opaque anchor ids only, so redaction leaves it alone |
| `source_protection` (new) | written at derivation; recomputed when a protector is redacted or erased | `(survivor_type, survivor_id, protector_ref)`: an unanchored user-authored contributor that keeps the survivor assertable (Q6). Stored per survivor, naming the protector, so removing the protector removes the protection (R2) | — | n/a (new) |
| `source_policy_change` (new) | written by `set_source_policy` | the audit row: who, when, from, to, records flipped | — | n/a (new) |
| `source_confirmation` (new) | written by `confirm_source` | the audit row: call path, time, the locator's anchor ids, count | — | n/a (new) |
| `source_policy` (new, a store fact) | written by `set_source_policy`; read by every flip | `flag` or `withhold`, recorded in the store; never per-process | — | n/a (new) |
| `Edge.source_withheld`, `Episode.source_withheld` (new) | written by every flip writer (§4d); read by `assertable`, `assertion_view`, the gate's fence and as-of's carrier | true when the record rests on an anchor whose current binding was last observed changed or missing, the store policy is `withhold`, and the survivor has no live `source_protection` row | below | changes `assertable` by one conjunct |
| `Edge.assertable` / `Episode.assertable` | read (changed definition) | `active and not quarantined and not use_only and valid_now` (`src/veracium/schema.py:995-1006`); a 0042 census site under INV-7's one-return rule | the gate (`src/veracium/gate.py:170`), the wiki compile's inputs (`src/veracium/compile.py:207`), proactive, scope reads, selfcheck, the store | under `withhold`, a withheld record is not assertable; the conjunct goes in both arms of INV-7's return. Under `flag`, unchanged |
| the gate's fence | read | fences `quarantined or (active and use_only)` (`src/veracium/gate.py:171`) | — | **gains a third clause**, `active and source_withheld` (B3) |
| `schema.assertion_view` | read (gains the field) | what a compiled wiki may assert from one record; a change evicts the wiki at the write (0047) | the store's eviction, the compile's bind (`_unbound_by`) | **the field is placed in the view**; `ASSERTION_VIEW_KEEPS` (`src/veracium/schema.py:1425`) refuses it otherwise |
| as-of `CurrentState` | gains a restriction | as-of never consults `assertable` (`src/veracium/asof/__init__.py:8`, 0028 V-ONE-CLOCK) | `recall(as_of=)`, `facts_valid_at` | gains a **current** source restriction, as REDACTED is (B4) |
| `contribution_ledger` | **read at derivation only** | 0014: a survivor's contributors | — | read only; never re-walked at recall |
| `Recall` | gains `sources` and `sources_last_observed_at` | new; no locator (Q7) | callers of `recall()` | additive |

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| host `SourceAnchor.locator` | refused (1–512 characters) | refused, nothing written | accepted as text; never opened | credential-shaped: refused by 0055's screen; a path naming a secret file is stored, never read by Veracium | **S1, S8** |
| host `SourceAnchor.fingerprint` | refused | refused unless 1–128 characters of `[A-Za-z0-9:._-]` | compared for byte equality only | credential-shaped: refused by 0055's screen | **S1** |
| host `evidence_ref` reused across remembers (B1) | — | — | — | a host that uses a file path as its `evidence_ref` remembers two file versions under one key: **refused** if the key already carries an anchor with a different current binding (`AnchorConflict`), nothing written | **S14** |
| host `observe_sources` batch | changes nothing, reports zero | one bad entry refuses the batch | a locator with no anchor is recorded and changes nothing now | a host component reporting "changed" everywhere withholds anchored facts under `withhold`: a denial of assertion, bounded, reported and reversible | **S3, S4, S6** |
| host `set_source_policy` | — | an unknown value refused | — | a switch recomputes every bit in the store, across users, in one transaction, and writes an audit row; no stale bit survives a switch | **S19, S24** |
| a queued or replayed `remember(source=)` at an older fingerprint (R3) | — | — | — | the host observed F2, then replays an event at F1: the implied observation only moves anchors toward `changed`, so nothing un-withholds | **S20** |
| extractor output | — | — | — | never supplies a locator, fingerprint or observation | **S2** |
| an agent over MCP | — | — | — | no tool takes a locator, fingerprint, observation or policy (absent by schema, v1) | **S7** |
| data written by an older version | no anchors: every record unanchored; `source_withheld` absent from JSON means false | — | — | — | **S5** |
| an import file, default import | — | an anchor row outside the grammar refuses the import | below the new format: no anchors | default import caps every record to THIRD_PARTY + USE_ONLY (`src/veracium/portability.py:24-28`); an imported locator could plant a path for the host's reread loop to open. **Anchors and links are dropped and counted (`capped`)**; `source_withheld` is stripped and recomputed | **S21** |
| an import file, `restore=True` | — | as above | — | anchors, bindings and links imported verbatim; observations are never exported, so restored anchors read `unchecked`; `source_withheld` stripped and recomputed | **S21** |
| the contribution ledger, at derivation | a survivor with no contributors: no links | — | an unreadable contributor author (pre-v8 absorption, a 0021 prune row) is **not USER**: it writes no protection row | — | **S6, S12** |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | result at `b256e348` |
|---|---|---|
| `.assertable` text hits | `grep -rln "\.assertable\b" src/` | 12 files. Dev's reading (2026-11-23): the two as-of hits are a docstring and a keyword argument, not property reads; as-of reads its own carrier |
| as-of never reads `assertable` | `sed -n 5,9p src/veracium/asof/__init__.py` | "the as-of branch never consults it (0028 V-ONE-CLOCK)" |
| the gate's partition and fence | `sed -n 165,175p src/veracium/gate.py` | line 170 grounds `e.assertable`; line 171 fences `e.quarantined or (e.active and e.use_only)` |
| the wiki compile takes assertable episodes | `sed -n 205,208p src/veracium/compile.py` | `episodes = [e for e in all_episodes if e.assertable and …]` |
| redaction clears the ledger's evidence digest | `sed -n 110,117p src/veracium/redaction.py` | `("contribution_ledger.evidence_ref_digest", CLEAR)` for edges and episodes |
| `evidence_ref` is reused by the library | `grep -n 'evidence_ref="trust-tools\|evidence_ref=f"dispute' src/veracium/__init__.py` | lines 2177 and 2245 |
| in native absorption the survivor is the incoming edge | `sed -n 562,569p src/veracium/graph.py` | `survivor_id=incoming.id, … contributor_id=prior.id` |
| the erasure table list | `sed -n 234,240p src/veracium/store/sqlite.py` | `_ERASE_TABLES`: the new tables are not in it today |
| `assertion_view` placement is a build gate | `sed -n 1423,1426p src/veracium/schema.py` | `ASSERTION_VIEW_KEEPS`: "a field in neither the view nor this table fails the import" |
| default import caps trust | `sed -n 24,28p src/veracium/portability.py` | THIRD_PARTY, floored to USE_ONLY |
| MCP `remember` takes no source argument | `sed -n 810,846p src/veracium/mcp_server.py` | text, author, event_type, date, derived_from |
| the schema and export versions | `grep -n "^SCHEMA_VERSION" src/veracium/store/schema_version.py; grep -n "^FORMAT_VERSION" src/veracium/portability.py` | 16; 15 |

---

## 3. Trust-class matrix — REQUIRED, blocking

Classes read from the enums at `b256e348`: `EvidenceAuthor` = user, third_party, system, assistant
(`src/veracium/schema.py:81-88`); `Disclosure` = mentionable, use_only, quarantined (`:91-94`).

**Write-time or maintain-time.** Anchoring rides the event's own ingest (write-time). Observation, `confirm_source` and
`set_source_policy` are maintain-time: they report about the artifact, not new evidence about the fact. A derivation
writes its links and its survivor's bit in its own transaction. None of them may raise confidence, refresh currency,
change author or disclosure, or clear `needs_confirmation`; they may only set or clear `source_withheld` (S4).

**One record (edge or episode), store policy `withhold`.** Under `flag` every "withheld" cell reads "marked; assertability
unchanged" (S11).

| record's evidence author | anchored source changed or missing, no live protection row | the same with a live protection row (Q6) | fresh again, or `confirm_source` | quarantined record | `use_only` record |
|---|---|---|---|---|---|
| user | **withheld**: fenced, not asserted | marked, still assertable | cleared | — | — |
| third_party | marked; already not assertable | — (a third-party record is never protected) | cleared | stays quarantined | — |
| system (consolidation output) | withheld if any linked anchor is changed or missing | marked, still assertable | cleared | stays | stays |
| assistant | marked; already `use_only` | — | cleared | — | stays `use_only` |
| **the event's episode** (B5) | **withheld** with its edges: the wiki compile and the gate read `Episode.assertable` | as user | cleared | — | — |

**Batch rule.** A derived record's anchors are the **union** of its contributors' anchors, transitively, decided at
derivation and written as `source_derivation_link` rows. It is withheld when **any** linked anchor is changed or
missing, unless it has a live `source_protection` row: the derivation found an **unanchored contributor whose author
reads `EvidenceAuthor.USER`** (the owner's decision, Q6), and that row names the contributor. Redacting or erasing the
protector deletes its row and recomputes the survivor (R2). A `confirm()` made before the file changed is not
protection: it attested the old content, and `confirm_source` is the route after a change (the owner's ruling, Q13,
2026-11-23: "No"). An author that cannot be read (dev's Q10: pre-v8 absorption rows,
0021 prune rows) is **not USER**, so it never protects. Under default import every author is THIRD_PARTY (0005's cap),
so an imported contributor never protects.

**Directional, native absorption** (dev's correction: the survivor is the **incoming** edge and the prior is the
absorbed contributor, `src/veracium/graph.py:562-568`):
- *survivor = unanchored user restatement, absorbed prior = anchored:* the survivor links the prior's anchor and is
  protected by itself (a protection row naming the survivor's own event): a file change marks it, does not withhold
  it.
- *survivor = anchored, absorbed prior = unanchored user fact:* linked to its own anchor, protected by the prior (a row
  naming the prior): marked only. Redact the prior and the survivor is withheld (S23).
- *survivor = anchored, absorbed prior = unanchored assistant or third-party record:* not protected: withheld.
- *survivor = unanchored assistant or system record, absorbed prior = anchored:* not protected: withheld.

**The Q6 exception is a host contract, not detection** (dev's §9 challenge 1). Veracium cannot tell a user's independent
statement from file text the host pasted into `remember()` without an anchor. §8 states the contract.

Answers:
- **Can a user-asserted fact become non-assertable?** Yes, under `withhold` only, when the host reports a changed or
  missing source for an anchor it rests on and it has no live protection row. Never under `flag`; never from extractor
  output or an agent (S2, S7).
- **Can non-user content gain user-grade authority, confidence or currency?** No (S4).
- **Can it clear `needs_confirmation`?** No (S4); `confirm_source` is not 0008's `confirm()`.
- **Does it merge, drop or overwrite provenance?** No. Bindings are append-only; `Provenance` is unchanged; edge and
  episode JSON is byte-identical while `source_withheld` is false, which it always is with no anchors (S5).

---

## 3b. Authorization and scope — *full specs only*

- **Boundaries crossed:** none. Anchors, observations, links and the policy are per `user_id` and per store (S3).
- **Who may see the affected state:** whoever may already see the record. `Recall.sources` carries state, anchor count
  and anchor ids, never a locator (Q7).
- **Newly visible:** the locator, only through `Memory.source_anchors(user_id, record_id)`, a host call, under the same
  0020 read scope as the record; a redacted record's anchor ids are refused there (§4f). Never rendered into the model
  context.
- **Import:** default import drops anchors, so a file cannot plant a locator for the host's reread loop (§2c).

---

## 4. Behaviour

### 4a. Interfaces

- `Memory.remember(..., source: Optional[SourceAnchor] = None)`; `SourceAnchor(locator: str, fingerprint: str)`.
  - The anchor key is `(user_id, evidence_ref_digest)`. If the key has no anchor, one is created with binding seq 1.
    If it has one whose current binding equals `(locator, fingerprint)`, the event joins it. **If its current binding
    differs, the call is refused (`AnchorConflict`) and nothing is written** (B1; the owner's ruling, Q11, 2026-11-23:
    "Refuse"). A host that reuses refs must give
    each file version its own `evidence_ref`.
  - `remember(source=)` is also an **observation** of that locator at that fingerprint, **in one direction only**
    (R3): it may move older anchors on the locator bound to another fingerprint to `changed`, and its own anchor is
    `fresh` at birth, but it never moves any anchor from `changed` or `missing` back to `fresh`. A queued event
    replayed at an old fingerprint therefore un-withholds nothing. Clearing is reserved for the two explicit acts,
    `observe_sources` and `confirm_source`. It is a flip writer (§4d).
- `Memory.observe_sources(user_id, observations: list[SourceObservation]) -> ObservationReport`;
  `SourceObservation(locator: str, fingerprint: Optional[str])`, `None` meaning absent. One transaction; a bad entry
  refuses the batch; a batch over `MAX_SOURCE_OBSERVATIONS` is refused (§5, Q8). The report: locators observed, anchors
  fresh / changed / missing, records whose bit flipped each way, and `last_observed_at`.
- `Memory.confirm_source(user_id, locator) -> ConfirmReport`: the host attests the facts still hold for the locator's
  current content. Each anchor on the locator gets a **new binding** (next seq) at the latest observed fingerprint, its
  records are recomputed, and a `source_confirmation` row records it (`HOST_API`). Refused when the latest observation is
  `missing`.
- `Memory.set_source_policy(policy: Literal["flag", "withhold"])`: the policy is a **store fact**, default `flag`
  (dev's §9 challenge 2). A change recomputes every record's bit in the store, across users, in one transaction, and
  writes a `source_policy_change` audit row (N2). `withhold` is **experimental**
  (the owner's decision, Q1) until S6 and S10 pass. No `Config` field: two processes on one store cannot disagree.
- `Recall.sources: dict[str, SourceStatus]` for anchored records only; `SourceStatus(state, anchors, anchor_ids)`,
  `state` one of `fresh | changed | missing | unchecked`. `Recall.sources_last_observed_at: Optional[datetime]`.
  **No locator** (Q7).
- `Memory.source_anchors(user_id, record_id) -> list[AnchorView]`: `AnchorView(anchor_id, locator, fingerprint,
  bound_at, state)`, the current binding. Same read scope as the record; refused for a redacted record.
- `veracium.sources.fingerprint_file(path) -> str`: a helper the **host** may call (`sha256:` + the hex digest of the
  bytes). No Veracium code path calls it (S8, Q2). Its output is a host-supplied value under S1's grammar like any
  other fingerprint. (v0.3 placed it in 0055's I19 digest map; dev corrected that: the I19 check is runtime and no
  Veracium path computes it, and a map row would amend an accepted spec's evidence. Not placed; a 0055 amendment would
  be a separate carrier.)
- **MCP and CLI:** no change in v1 (Q4).

### 4b. State

An anchor's state compares its **current binding** with the locator's latest observation: none, `unchecked`; equal,
`fresh`; different, `changed`; absent, `missing`. A record's state is the worst over its own anchor and its derivation
links (missing > changed > unchecked > fresh).

### 4c. Derivation links (B2)

The derivation writers are the four 0014 ledger sites (consolidation, native absorption, and the two plan sites,
imported-absorption and scope-attribution; `src/veracium/contribution.py:61`) **and the record-quoting episode
writers** that 0041 already names as derived content (`surviving_derived`, `src/veracium/store/sqlite.py:3919-3930`):
`confirm()`'s episode, whose USER-authored summary quotes the edge (`:1172-1182`, `evidence_ref` `confirm:{edge_id}`);
`record_outcome`'s outcome episode; and `dispute`'s episode (R1). Each writes, in its own transaction:
1. one `source_derivation_link` per anchor in the union of its contributors' (or its target's) anchors, their own and
   their links, so depth ≥ 2 is covered by construction;
2. one `source_protection` row per unanchored contributor whose author reads `EvidenceAuthor.USER`, naming it (§3).
   A record-quoting episode is never protected by its own USER authorship: it quotes its target, it is not independent
   evidence of it;
3. the survivor's materialised `source_withheld`, so a summary consolidated **after** a "changed" observation is born
   withheld, never born assertable.

Recall reads links; it never re-walks the ledger.

### 4d. Flip writers, and what each costs

Writers of `source_withheld`: `remember(source=)` (older anchors on the locator), `observe_sources`, `confirm_source`,
`set_source_policy`, the derivation sites, the record-quoting episode writers (R1), and protection recomputation at
redaction and erasure (R2). Each is:
- an edge-writing site, so it gets an `EDGE_WRITE_SITE_RULINGS` entry (`src/veracium/store/sqlite.py:252`) and journals
  one 0029 event per flipped edge (1,000 events at S10's scale);
- an episode writer journalled the same way (0041 v15's episode journal);
- an `assertion_view` change, so the store evicts the cached wiki in the flip's own transaction (0047), and the writer
  is classed in the 0047 wiki-bind writer census.

### 4e. What the reader sees (the exact rendering change)

- `flag`, `changed`: the line gains ` [its source changed since this was learned — reread it]`; `missing`:
  ` [its source is gone — confirm before relying on it]`.
- `withhold`: a withheld record moves to the fenced section through the gate's **third fence clause**
  (`active and source_withheld`, B3), as ` [withheld: its source changed]` or ` [withheld: its source is gone]`.
  Fenced, not suppressed: S16 asserts the line exists.
- A record with a live protection row under `withhold` renders as `flag` does.
- `unchecked`, `fresh`: no change. No marker names a locator.
- **Briefings** (`src/veracium/proactive.py`) carry the same markers beside its existing `needs_confirmation` rendering;
  under `withhold` a withheld record is not volunteered, since the volunteering gate reads `assertable`.
- **MCP:** `recall` returns the rendered context, so the markers reach MCP callers through the renderer;
  `Recall.sources` is not exposed over MCP.
- **As-of** (B4): `CurrentState` gains a current source restriction, as REDACTED is: a fact withheld now is withheld
  at every `as_of` date, since the file is changed now.

### 4f. Redaction and erasure (Q9)

- **Erasure:** `source_anchor`, `source_anchor_binding`, `source_observation`, `source_derivation_link`,
  `source_protection` and `source_confirmation` join `_ERASE_TABLES` (`src/veracium/store/sqlite.py:234`). The policy
  row and `source_policy_change` are store-level, "never per-user, and never erased" (the 0044 precedent at
  `:243-244`, N1).
- **Redaction:** an anchor is per event and shared by sibling records, so redacting one record does not delete it. A
  redacted record's anchor ids are refused by `source_anchors()`. When **no** unredacted record or link still rests on
  an anchor, its bindings' locator and fingerprint are REPLACEd with the redaction marker and its locator's observations
  are deleted. These are `SIDE_TABLE_TREATMENTS` rows, so the carrier paths and the generated treatment matrix carry
  them. Links carry anchor ids only and need no treatment. A `source_protection` row whose protector is redacted is
  deleted and its survivor recomputed in the redaction's transaction (R2).
- **Deferred:** `redact_source(user_id, locator)` for a path that is itself private (§8, Q12).

### 4g. Migration

Schema 16 → 17: the seven tables and the policy row, through `ALTERS_V16_TO_V17`, offline, as
`src/veracium/store/migration.py` does today. `source_withheld` is omitted from JSON while false (the 0025 / 0045 rule),
so every existing record's bytes are unchanged. Export format 15 → 16, stamped only when an anchor is present.
**Unrecoverable:** nothing.

---

## 5. Regime analysis — where does this behave differently?

- **Many records on one locator:** one observation flips them all, with one journal event per edge. S10 measures the
  transaction at 1,000 records; `MAX_SOURCE_OBSERVATIONS` is then set from that measurement (Q8), not chosen now.
- **Derivation depth:** links are the union at each derivation, so depth costs nothing at read. S6 reaches depth 2.
- **Recall cost:** an anchored record adds lookups through indexes on `(user_id, anchor_id)` and
  `(user_id, locator)`; unanchored stores pay nothing (S5).
- **Cached wiki:** evicted at each flip (0047); a store that flips often recompiles more often. S18 reaches it.
- **A policy switch** recomputes every anchored record in the store, across all users, in one transaction: the
  feature's largest. S24 measures it at a stated store size and bounds it; a switch that would exceed the bound is
  refused with its count (N2).
- **Release class:** anchoring is off until a host opts in; `flag` is the default policy; `withhold` is experimental
  (Q1). Making `withhold` the default or dropping its label needs a spec whose §5 reaches these regimes.

---

## 6. Invariants and executable checks — REQUIRED, blocking

The test module is written with the implementation; each check is shown RED against a deliberately wrong implementation
before acceptance.

| invariant | executable check | where it runs |
|---|---|---|
| **S1** a malformed or credential-shaped locator or fingerprint refuses the call; nothing written | parametrized over §2c's rows | CI |
| **S2** an anchor comes only from the host's argument | an extractor stub emitting locator-like text: no anchor | CI |
| **S3** an observation touches only its own user's anchors | two users, one locator string | CI |
| **S4** no flip writer changes author, disclosure, confidence, `valid_from` or `needs_confirmation` | snapshot every other field before and after each writer | CI |
| **S5** a store with no anchors is byte-identical in record JSON and recall output under both policies | the existing canaries, plus a byte comparison | CI + bench `--compare` |
| **S6** under `withhold`, a derived record is withheld when any linked anchor is changed, at depth 1 and 2, including one consolidated **after** the observation; and `confirm()`, then the file changes: the confirmation episode is withheld with its edge (R1), as are an outcome episode and a dispute episode | consolidation and quoting-episode fixtures | CI |
| **S7** no MCP tool accepts a locator, fingerprint, observation or policy | the served tools' schemas | CI |
| **S8** Veracium never opens, stats or hashes a locator, and never calls `fingerprint_file` | the anchor, observe, confirm, policy and recall paths run with `open`, `os.stat`, `pathlib.Path.stat` **and `fingerprint_file`** patched to raise: no call | CI |
| **S9** an import below format 16 carries no anchors | round trip at both versions | CI |
| **S10** 1,000 records on one locator flip in one observation and flip back on a fresh one; the transaction time is recorded | a scale fixture | CI |
| **S11** `flag` never changes `assertable`, the partition or as-of | S6's fixtures under `flag` | CI |
| **S12** an unanchored user-authored contributor writes a protection row naming it; an assistant, system, third-party or unreadable-author contributor, or a record-quoting episode, does not | §3's four absorption directions, a consolidation per class, a pre-v8 absorption row, a `confirm()` episode | CI |
| **S13** no `recall()` output carries a locator; `source_anchors` is scoped and refuses a redacted record | serialized recall searched for each locator; an out-of-scope and a redacted record | CI |
| **S14** a remember whose `evidence_ref` already carries an anchor with a different binding is refused, nothing written; the same binding joins | two remembers under one ref, two file versions | CI |
| **S15** redacting a contributor does not un-withhold its derived record | redact a consolidation input after a "changed" observation; the survivor stays withheld | CI |
| **S16** a withheld record appears in the fenced section, with its marker | gate output under `withhold` | CI |
| **S17** `recall(as_of=)` withholds a currently withheld fact at a past date | as-of fixtures | CI |
| **S18** a withheld episode leaves the next compile's inputs, and a cached wiki body drawn on a now-withheld record is evicted in the flip's transaction | 0047's bind and eviction fixtures | CI |
| **S19** a policy switch recomputes every bit in one transaction; two processes read one policy | switch withhold → flag → withhold; a second `Memory` on the same store | CI |
| **S20** `remember(source=)` at a new fingerprint marks older anchors on the locator `changed` and its own `fresh`; **and the mirror** (R3): observe F2, then remember at F1, and nothing un-withholds | a host observes F1, the file changes, the host remembers at F2; then a replay at F1 | CI |
| **S21** default import drops anchors and links and counts them `capped`; restore keeps them `unchecked`; `source_withheld` is stripped and recomputed either way | portability round trips | CI |
| **S22** erasure removes every new per-user table's rows, and leaves the store-level policy rows | the existing erasure test, plus a mutant that omits each new per-user table from `_ERASE_TABLES` and must fail | CI |
| **S23** redacting or erasing the protecting contributor withholds its survivor (R2, the mirror of S15) | protect a survivor with an unanchored user fact, observe "changed", redact the protector: the survivor becomes withheld | CI |
| **S24** a policy switch writes one audit row and stays within its measured bound; over the bound it is refused with its count | a store-wide switch at a stated size, timed | CI |
| **S25** a briefing carries `flag`'s marker for a changed source, and does not volunteer a withheld record under `withhold` | proactive fixtures | CI |

Standing checks that must not regress: injection asserts 0 · cross-user leaks 0 · trust canaries 0 · supersession
probes pass · malformed edges 0 · declared read-cost and latency ceilings.

---

## 7. Failure modes and reversibility

- **Silent failure:** the host never observes. Everything stays `unchecked`; `Recall.sources_last_observed_at` and
  `ObservationReport.last_observed_at` make that visible.
- **Reversibility:** complete. Bindings are append-only and the latest observation per locator is kept; every bit is
  recomputed from those two (N5). A fresh observation, `confirm_source` or a policy switch restores the prior partition; no record is deleted or
  superseded by this feature.
- **Partial failure:** each writer is one transaction; a refused entry refuses the batch.
- **New attack surface:** a host component that can observe can withhold anchored facts (denial of assertion, never an
  injection). Agents cannot reach it (S7). Locators are never opened by Veracium (S8), and default import cannot plant
  one (S21).

---

## 8. Claims and limits

- **What we will say:** "Veracium can tie a memory to the file it came from. When your application reports that the
  file changed or disappeared, recall marks the memory, or, with the experimental setting, stops asserting it until
  someone checks. Summaries built from that file follow the same rule."
- **What this does NOT establish:**
  - Veracium does not watch files; freshness is as current as the host's last observation.
  - It does not know what changed in a file; a changed fingerprint covers every fact anchored to it.
  - **Host contract (Q6):** text taken from a file and remembered **without** an anchor is indistinguishable from the
    user's own statement, and exempts the fact. Veracium does not detect this.
  - A locator that is itself private can be removed only with its records (redaction or erasure); `redact_source` is
    deferred (Q12).
  - `withhold` is experimental: its scale and depth regimes are untested until S6 and S10 pass.
- **Measurements:** none yet.

---

## 9. Brief for the external reviewer

- **Least sure of:** (1) the derivation writers: that every writer of a record derived from, or quoting, another writes
  its links. v0.4 takes the four 0014 sites and 0041's `surviving_derived` set (the `confirm()`, outcome and dispute
  episodes), which v0.3 had missed; a writer still missed is a fail-open path;
  (2) the cost of materialising: a journal event per flipped edge and a wiki eviction per flip; (3) B1's refusal: hosts
  that reuse `evidence_ref` will meet `AnchorConflict` and must change how they call.
- **Where we may have overstated:** "complete reversibility" rests on every flip writer recomputing from bindings and
  observations; a writer that sets the bit from anything else would break it.
- **What would change our minds:** evidence that hosts will not observe (then `flag` alone is the honest scope); a
  derivation site whose contributors cannot be enumerated at derivation.
- **Generalised for a reviewer-safe copy:** nothing; the competitors named in §1 are public.

---

## 10. Open questions

| # | question | who decides | by when | class |
|---|---|---|---|---|
| Q1 | Do both policies ship? **Decided 2026-11-23 (the owner): both; `flag` the default, `withhold` experimental.** v0.3 makes the policy a store fact (dev). | the owner | — | decided |
| Q2 | Who computes fingerprints? **Decided 2026-11-23 (the owner): the host only; a host-called `fingerprint_file` helper.** | the owner | — | decided |
| Q3 | The wiki. **Answered by dev (v0.2 review):** the wiki is one cached body per user view with no per-input lineage; withheld edges and episodes leave the next compile through `assertable`, and the cached body is evicted at each flip through `assertion_view` (0047 INV-R18). No ledger site needed. Folded (§4d, S18). | dev | — | answered |
| Q4 | An MCP surface for anchoring or observing. v1: none. | the owner | pre-release | deferred |
| Q5 | Default import. **Answered by dev:** drop anchors and links, count them `capped`; restore keeps them; observations never exported; `source_withheld` stripped and recomputed. Folded (§2c, S21). | dev | — | answered |
| Q6 | Does an unanchored user contributor keep a fact assertable? **Decided 2026-11-23 (the owner): yes, user-authored only, still marked.** v0.3: a host contract, not detection (§8). | the owner | — | decided |
| Q7 | A locator in recall? **Decided 2026-11-23 (the owner): no; `source_anchors` resolves ids.** | the owner | — | decided |
| Q8 | Caps. **Answered by dev:** a named `MAX_SOURCE_OBSERVATIONS`, set from S10's measured transaction time; a per-user `last_observed_at`, reported. Folded. The value itself is set at the build. **Dev, on v0.4 (a pre-release note):** as written, S24 means a store larger than the measured bound can never switch policy. Before `withhold` loses its experimental label it needs a path: a resumable switch with an explicit "switching" state that fences everything anchored until it completes, or a stated maximum store size. | dev | pre-release | pre-release |
| Q9 | Redaction and erasure. **Answered by dev:** the new tables join `_ERASE_TABLES`; redaction refuses a redacted record's anchor ids and REPLACEs an anchor's locator and fingerprint once nothing unredacted rests on it. Folded (§4f, S22). | dev | — | answered |
| Q10 | Can each contributor's author be read? **Answered by dev:** consolidation yes (the ledger's mandatory key); native absorption yes for v8+ rows through `contributor_ref`, not for pre-v8; imported-absorption yes but THIRD_PARTY under default import; scope-attribution yes except prune-moved and closure-incomplete rows. Unreadable means not USER (§3, S12). | dev | — | answered |
| Q11 | Should `AnchorConflict` (B1) instead let a record rest on both anchors? **Decided 2026-11-23 (the owner, first-hand to dev, relayed by dev): "Refuse (Recommended)".** Refuse, as v0.3 and v0.4 specify; dev's reason: resting on both attributes every record under a reused ref to both versions, so `withhold` withholds more than the host meant and `flag`'s markers mislead, while refusing surfaces the reuse at its first call. | the owner, with dev | — | decided |
| Q12 | `redact_source(user_id, locator)` for a path that is itself private. | the owner | pre-release | deferred |
| Q13 | Does a `confirm()` made **before** the file changed count as Q6 protection? **Decided 2026-11-23 (the owner, first-hand to dev, relayed by dev): "No (Recommended)".** It attested the old content; `confirm_source` is the route after a change. | the owner | — | decided |

---

## Reviewer checklist

- [ ] §3 has no unanswered cells, and is **directional** where the operation is
- [ ] §3's classes were read from the enums, not copied from the template
- [ ] Prohibitions AND the corresponding **permissions** are both tested — a guard drawn too broadly passes every
      prohibition test
- [ ] Every default fails **closed**: an unresolvable input costs assertability rather than granting it
- [ ] §2c has a row per uncontrolled input, and **no empty invariant cell**
- [ ] §2c-ii: every claim about what is reachable / exposed / licensed / available carries **the command**
- [ ] §2 consumers were enumerated by reading, not recall
- [ ] Every §6 invariant has a check that actually runs
- [ ] §5 regimes are reachable by tests, or the change is experimental, off by default, and §8 says so
- [ ] §3b: no principal can see anything they could not see before (full specs)
- [ ] §6 and §8 are filled in
- [ ] §10 questions each carry a class
- [ ] §8 states what this does *not* establish
- [ ] I have said where I think the **author's conclusion is wrong**, not only where the text is wrong
- [ ] I re-read the current version before reviewing, and I am quoting the version I approve
- [ ] §9 brief is written, and external review has been sent
