# Feature spec: maintenance attribution — a consumed contributor must leave a recoverable record

Spec-Status: draft
Spec-Requires: 0006, 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft (v2)** — dev stub, 2026-08-08. Written from research's `A3-source-revocation-design.md`
> §2 finding at dev's recommendation to **decouple the record from the `revoke_source()` feature**.
> This spec establishes the RECOVERABLE ATTRIBUTION RECORD only; the revocation set-computation
> (`A3`) and the derived-view reach (`0004`) consume it. **v2 folds research's response
> (`proposals/0014-research-response.md`, 2026-08-08): Q5 CONFIRMED, and the invariant is
> re-keyed from "state transfer" to CONSULT-AND-DISCARD** — research measured that an older/weaker
> contributor leaves every survivor value unchanged (`max()` never moves) yet still vanishes, so a
> transfer-keyed rule would miss it, and that omission is an attack path (stale-but-corroborating
> input becomes the unlogged channel). Q1–Q4 resolved (§10); a `0014 → 0006` dependency is named
> (key the ledger on a **digest** of `0006`'s **`(origin, source_id)` pair** — `0006` v2, R5: identity
> is the pair, `origin` store-minted so a revocation cannot reach another store's records; both
> host-free-form components and `evidence_ref` are digested).

*Fill this in **before** implementing. See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`), from research's A3 finding |
| **Version** | **v2 (stub)** — *re-read before editing; quote the version you approve.* Problem + finding + the CONSULT-AND-DISCARD invariant (§4) are concrete and research-confirmed; the mechanical contract (§6, §7a) is still a sketch pending design lock. |
| **Status** | *canonical state is the `Spec-Status:` line at the top; this row states none of it.* |
| **Internal reviewers** | dev · **research (finding owner) — reviewed 2026-08-08, decoupling CONFIRMED, invariant sharpened** (`proposals/0014-research-response.md`) |
| **External review** | required (full — it will touch guarded files: `graph.py`, `lifecycle.py`, `store/sqlite.py`). Not yet sent. |
| **Decision + date** | — (draft) |
| **Path** | full |

---

## 1. Problem and motivation

**Ordinary maintenance silently destroys the evidence that a source contributed to a fact.**
Veracium's whole guarantee is provenance you can trust — but maintenance operations transfer
*state* (liveness, confidence, disclosure, derivation, first-known date) from a **contributor**
record into a **survivor** record, and two of the three destroy the record that the contributor
ever existed. So for any surviving fact you **cannot** answer "which sources gave this its current
liveness and confidence?", and if a source later proves compromised you **cannot** compute — let
alone reverse — its contribution. Measured, no LLM, in research's A3 provenance-chain demo
(a3_provenance_chain_demo.py; lives in `veracium-research`, not this repo).

**What happens if we do nothing:** the provenance chain the product sells as complete is not
complete — it is complete *only until the first maintenance pass*. A compromised feed that
reinforces a fact can move its liveness forward by months and raise its confidence, invisibly and
irreversibly (`lifecycle.py` ages against `observed_at`, so a revoked source can keep a stale fact
alive forever). This is the **fourth instance of one pattern** — a maintenance-time operation
crossing a boundary the write path guards correctly (GHSA-r7j7-5jq9-3f5q / 0.4.1,
GHSA-hcj3-8jqc-wqrp / 0.4.4, `specs/0003`, and now this). The recurrence is the argument: point
fixes have not closed the class.

**This is NOT the revocation feature.** `revoke_source()` (research `A3`) and making a revocation
reach recall (`0004`) are the *consumers*; both are impossible while the set cannot be computed.
This spec is the **minimum that makes the class of finding go away** and has value whether or not
revocation is ever built — an attribution record that survives maintenance.

**Alternatives rejected.**
- **Fix each site independently** (patch reinforcement, patch consolidation, patch absorption).
  This is how the pattern recurred four times: three separate ad-hoc fixes with no shared invariant
  invite a fourth site to reintroduce it. A single invariant over "state transfer" is what closes
  the class.
- **Do it inside `A3`/`revoke_source`.** Couples a broadly-useful integrity property to one feature
  and one owner (`0004`); the property is worth having with no revocation feature at all (a host
  auditing "why is this fact live?" needs it). Decoupling is dev's explicit recommendation.
- **Reconstruct attribution lazily from existing fields at revocation time.** Measured to be
  impossible: reinforcement never persists the incoming edge (nothing to reconstruct from), and
  consolidation deletes its inputs (their provenance is gone, only opaque ids remain).

---

## 2. Field contracts touched — REQUIRED, blocking

*Draft — to be completed against the interface, not from recall (the method that missed three
surfaces in `specs/0002`). Enumerate mechanically before design lock:*

```
$ grep -nE "def (add_|invalidate_|delete_|forget_|set_)" src/veracium/store/base.py
$ grep -rn "add_edge\|invalidate_edge\|delete_episode\|apply_supersession_plan" src/veracium/ | grep -v test
```

Provisional: `Provenance.observed_at`, `Provenance.confidence`, `Edge.valid_from`,
`Provenance.disclosure`, `Provenance.derived_from` — each is *read from a contributor and written
onto a survivor* by at least one maintenance op (the payload).

> **`0014 → 0006` dependency (research Q1/F3, and `0006` v2 R5).** The ledger is keyed on **`0006`'s
> `(origin, source_id)` PAIR**, already the revocation key. `0006` v2 (R5) makes identity the pair —
> `origin` is store-minted, so an imported source cannot collide with a local one and **a revocation
> keyed on the pair is structurally incapable of reaching another store's records.** `0006`'s "opaque"
> is a host-convention, not enforced (`0006` §8, F3), so for a content-free surface the ledger stores a
> **deterministic digest of the pair**, never the raw value. The digest stays joinable:
> `A3`/`revoke_source`, given a pair to revoke, digests it the same way. `evidence_ref` is digested the
> same way. This makes `0006` (source identity) a prerequisite — hence `Spec-Requires: 0006, 0007,
> 0013`, and `0014`'s table is the `SCHEMA_VERSION` AFTER `0006`'s (v6, `0006` is the no-DDL v5). The
> scalar payload
> (`observed_at`/`confidence`/`valid_from`/`disclosure`/`derived_from` + their prior values) is
> timestamps/floats/closed enums — store-clear, so **content-free and reversible do not conflict**
> (Q1 resolved).

## 2c. Untrusted inputs — REQUIRED, blocking

*Draft.* The contributor whose attribution we record may itself be adversarial (a compromised feed
is the motivating case). The record must therefore be **fail-closed and content-free**: it records
*that* a contributor was consumed and *what state, if any,* moved, keyed on a **digest** of
`0006`'s `(origin, source_id)` pair and a digested `evidence_ref` (all host-supplied free-form, so all
digested — `0006` F3/R5), so a malicious contributor cannot smuggle memory content
into a durable audit surface, and a missing/absent record is treated as "attribution unknown → the
survivor is suspect", never "clean". **The adversary's cheapest evasion is the empty payload** — a
stale-but-corroborating input that moves no `max()` — which is exactly why the record is owed to the
consumption, not the transfer (§4).

---

## 3. The finding, at its current sites — REQUIRED, blocking

Three maintenance sites transfer contributor state into a survivor. Reproduce with research's A3
provenance-chain demo (a3_provenance_chain_demo.py, `veracium-research`). Status is stated **as of
0.6.0** (0010 partially moved §3.2 after
A3 was written):

| # | site (a maintenance op that consults a contributor then discards/merges/invalidates it) | contributor recoverable today? | payload (state it may transfer) |
|---|---|---|---|
| **3.1** | **reinforcement** — `graph._build_supersession_plan` reinforcement branch (`insert_incoming=False`; the incoming edge is never persisted, the prior absorbs `max(observed_at)`/`max(confidence)`) | **No** — nothing is written for the contributor. **Also when the payload is EMPTY:** an older/weaker contributor moves no `max()`, so the survivor is unchanged, and the consumption is *still* unrecorded (the case a transfer-keyed rule would miss; research measured it) | `observed_at`, `confidence` — or **none** |
| **3.2** | **consolidation** — `lifecycle.consolidate` deletes each claimed input; the summary carries `lineage` (0010) = the whole claimed set in the historical namespace | **Partial (improved by 0010) — VERIFIED 2026-08-08.** `lineage == the whole claimed input set == exactly the deleted inputs` (`lifecycle.py:142–156`), so every deleted contributor's ID is recorded; what is lost is **id→source** (the deleted episode's provenance). Not worse than "partial" | disclosure, confidence, `derived_from`, `observed_at` |
| **3.3** | **absorption** — `graph._build_supersession_plan` absorption branch retains the absorbed prior and links it by a free-text `note = "absorbed_by:<id>"` | **Partial** — retained + linked, but as a **string in a free-text field, not a queryable relation**, and inherited `min(valid_from)`/`max(observed_at)`/`max(confidence)` cannot be un-inherited | `valid_from`, `observed_at`, `confidence` |

**`specs/0003` did NOT close 3.1.** Its Slice-B rewrite preserved reinforcement semantics
byte-for-byte (`insert_incoming=False`, `prior_upserts=[refreshed]`) — deliberately, to avoid
regressing dedup — so the reinforcement source still vanishes. This is recorded as finding **M9**
(`specs/findings.py`, `owner=0002`, `open`). On adoption, **M9 and its siblings should be
repointed to `0014`.**

**What is NOT wrong (do not "fix" it):** reinforcement, consolidation and absorption are the
INTENDED mechanisms, and the cross-class guard (`graph.py`, "identity merges never cross trust
classes") and the 0002/N9b trust-envelope inheritance (min-disclosure, min-confidence,
third-party influence) are all correct. **The defect is only that consuming a contributor is
unattributed, so it cannot be audited or reversed.** This spec adds a record; it changes no
maintenance decision.

---

## 4. Behaviour — proposed direction (SKETCH, pending design lock)

> **The invariant (a sibling of `0002`'s maintenance-provenance-invariant), CONSULT-AND-DISCARD
> keyed — research's sharpening, 2026-08-08.** *Every maintenance operation that **consults** a
> contributor record and then **discards, merges or invalidates** it MUST leave a durable,
> queryable **contribution record** naming (i) the survivor, (ii) the contributor's opaque source
> identity, and (iii) a **payload** — the fields it transferred and their prior survivor values,
> **which may legitimately be empty** — **whether or not any of the survivor's values changed.***
>
> **Why keyed on the operation, not the transfer (measured).** Run reinforcement with the
> contributor OLDER and WEAKER: `max()` moves nothing, the survivor's `observed_at`/`confidence`
> are unchanged — and the contributor still vanishes. A *transfer*-keyed rule need not record that,
> yet "which sources support this fact?" omits it and any blast radius under-reports. It is not
> tidiness: an attacker contributes **invisibly** simply by ensuring no `max()` moves, so
> stale-but-corroborating input becomes the unlogged path. The record is owed to the **act of
> consuming a contributor**, and the value change is only its payload.

Sketch of the mechanism (provisional — the direction is agreed with research; the contract is not):

- **A durable contribution ledger**, one append-only record per consumed contributor:
  `(survivor_id, identity_digest, transferred_fields, prior_survivor_values, at)` — content-free by
  the 0003 discipline. **`identity_digest` = a deterministic DIGEST of `0006`'s `(origin, source_id)`
  pair** (already the revocation key; `origin` store-minted so cross-store revocation is structurally
  impossible, `0006` v2 R5; opacity is host-convention not a mechanism, F3, so it is digested — the
  digest stays joinable, `revoke_source` digests the same pair; see the `0014 → 0006` dependency, §2);
  `evidence_ref` is digested the same way, never stored raw (Q1). `transferred_fields`/
  `prior_survivor_values` are the payload and **may be empty** (a no-op-`max()` reinforcement still
  records the consumption). A new `SCHEMA_VERSION` object (v5→v6), so `Spec-Requires: 0006, 0007, 0013`.
- **3.1 reinforcement** → write a contribution record instead of silently dropping the incoming
  edge. Keep `insert_incoming=False` (no dedup regression); the ledger, not a duplicate edge,
  carries the attribution.
- **3.2 consolidation** → before deleting inputs, record each input's source attribution against
  the output's `lineage`, so `lineage`-id → source is recoverable after deletion.
- **3.3 absorption** → promote the free-text `note` link to the same ledger record (retire the
  string form as the queryable path).
- **Reads:** `contributions(survivor_id)` and `contributors_of_source(source)` — the exact queries
  `A3.revoke_source` and a host's "why is this fact live?" audit both need.

**Explicitly OUT of scope (the decoupling):** actually reversing a transfer, computing a
source's blast radius, and making a revocation reach recall — those are `A3` / `0004`. This spec
guarantees the *record exists and is queryable*; consuming it is theirs.

---

## 5. Regime analysis

**n/a — draft stub.** The regime is ordinary maintenance (reinforcement one `remember()` apart,
consolidation/absorption via `maintain()`); to be written with the invariant.

## 6. Invariants and executable checks — REQUIRED, blocking (SKETCH)

*Draft — names are provisional and MUST become real tests before acceptance (PROCESS §4a: a spec
is accepted only once these exist and pass at release, not before).*

| | invariant | check (to author) |
|---|---|---|
| **A1** | reinforcement leaves a contribution record naming the consumed source | `test_reinforcement_attributes_the_contributing_source` (the M9 test) |
| **A1a** | **it records the consumption EVEN WHEN THE PAYLOAD IS EMPTY** — an older/weaker contributor that moves no `max()` is still recorded (the consult-and-discard key; closes the attack path) | `test_reinforcement_records_the_contributor_even_when_no_value_moves` |
| **A2** | a consolidated summary's contributor SOURCES are recoverable after input deletion (not only the `lineage` ids) | `test_consolidation_contributors_survive_input_deletion` |
| **A3** | absorption's contributor link is queryable, not only a `note` string | `test_absorption_link_is_a_queryable_contribution` |
| **A4** | for any survivor, `contributions(survivor_id)` enumerates every CONSUMED CONTRIBUTOR (payload empty or not), across all three sites | `test_every_consumed_contributor_is_enumerable` (adversarial: inject at each site, including a no-payload consumption) |
| **A5** | the ledger is content-free — **the `(origin, source_id)` pair AND `evidence_ref` are all digested** (host-supplied free-form, `0006` F3/R5), no raw identity/`object`/`note`/`summary` ever recorded | `test_contribution_records_are_content_free` |
| **A6** | `forget_user` erases the ledger; export/import exclude it (Store-local, like 0003 refusals) | `test_forget_user_erases_the_contribution_ledger` |

**A4 is the one that decides whether the class is closed** — an exhaustive check over all three
sites *keyed on consumption, not value change*, so neither a fourth site nor an empty-payload
consumption (A1a) can reintroduce the finding.

## 7. Failure modes and reversibility

**n/a — draft stub.**

## 7a. Surfaces touched — the honest list (SKETCH)

- `src/veracium/graph.py` — `_build_supersession_plan` (reinforcement 3.1, absorption 3.3): emit a
  contribution record in the plan; the store persists it in the SAME atomic
  `apply_supersession_plan` commit (§0003 §4f already gives us the atomic carrier).
- `src/veracium/lifecycle.py` — `consolidate` (3.2): record input source attribution before deletion.
- `src/veracium/store/base.py` / `store/sqlite.py` — the ledger table, its reads, its erasure; the
  `SCHEMA_VERSION` v5→v6 migration that introduces it (`Spec-Requires: 0006, 0007, 0013`).
- `src/veracium/store/schema_version.py`, `store/migration.py` — the additive v5 object + migration.

**Schema:** likely **yes — one new content-free, user-linked table**, `SCHEMA_VERSION` v5→v6, the
same additive shape as 0003's refusal inventory. **This is a real cost** (another store version,
another migration) and §10 Q3 asks whether it is justified by attribution alone or only once a
revocation consumer (`A3`/`0004`) is committed.

---

## 8. Claims and limits

**Claims:** every maintenance-time *consumption of a contributor* — value change or not — becomes
auditable and (with a consumer) reversible; the recurring maintenance-provenance-loss pattern is
closed by one consult-and-discard invariant rather than three point fixes, and the empty-payload
evasion is closed with it.

**Does NOT claim:** it does not revoke a source, compute a blast radius, or make a revocation reach
recall (`A3`/`0004`); it does not change any maintenance *decision* (reinforcement still reinforces,
consolidation still consolidates); it does not authenticate the contributor's provenance labels
(that is the ingest boundary); it does not restore already-lost attribution in existing stores —
the migration starts the ledger empty and records transfers from v5 forward (pre-v5 loss is
unrecoverable, an honest limit to state loudly).

---

## 10. Open questions

*All five resolved by research 2026-08-08 (`proposals/0014-research-response.md`); kept here with
their rulings so the reasoning survives into design lock.*

- **Q1 — reversibility vs content-freeness — RESOLVED: no conflict.** The scalar payload
  (`observed_at`/`confidence`/`valid_from`/`disclosure`/`derived_from` + prior values) is
  timestamps/floats/closed enums — store-clear. The host-supplied free-form fields — `evidence_ref`
  AND the `(origin, source_id)` pair — are ALL **digested** (`0006` F3: opacity is a convention, not a
  mechanism, so identity cannot be stored raw on a content-free surface; `0006` v2 R5: identity is the
  pair, `origin` store-minted; the digest stays joinable for `revoke_source`). Keying on
  `digest(origin, source_id)` names the `0014 → 0006` dependency (§2).
- **Q2 — scope — RESOLVED: stop at the record.** All reversal / blast-radius / reach defers to
  `A3` / `0004`.
- **Q3 — new store version justified by attribution alone? — RESOLVED: yes, land now.** Deferring
  does NOT save the v5 bump — the ledger only attributes consumptions that happen *after* it exists,
  so waiting **permanently loses the interval** (and §1 already establishes history is not
  reconstructible). The audit value stands alone.
- **Q4 — interaction with `0012` — RESOLVED: do NOT block on it.** Under the consult-and-discard
  wording the invariant is *independent* of `0012`'s outcome — `0012` changes only the *payload*
  (whether reinforcement transfers liveness), not *whether a contributor was consumed*. (A
  transfer-keyed invariant WOULD have made `0014` `0012`-dependent — a concrete cost of the original
  wording, now avoided.)
- **Q5 — ownership / framing — RESOLVED: decoupling CONFIRMED**, and research judged dev's
  recurrence + standalone-audit arguments stronger than A3's original bundling. The one change —
  re-key to consult-and-discard — is folded into §4/§6. Remaining before `draft` → `in review`: a
  full mechanical contract (§6 tests real, §7a locked) and the `0006` acceptance it now depends on.

---

## 11. Review history

| version | verdict | findings | full disposition |
|---|---|---|---|
| v1 (stub) | draft — dev framing from research `A3` §2 | — | this document |
| **v2 (stub)** | **research reviewed: decoupling CONFIRMED; invariant re-keyed to consult-and-discard; Q1–Q5 resolved; `0014 → 0006` named** | 1 (the transfer-vs-consume sharpening) | `proposals/0014-research-response.md`; this document |
