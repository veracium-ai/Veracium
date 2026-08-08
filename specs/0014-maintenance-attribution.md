# Feature spec: maintenance attribution — a state transfer must leave a recoverable record

Spec-Status: draft
Spec-Requires: 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft (v1)** — dev stub, 2026-08-08. Written from research's `A3-source-revocation-design.md`
> §2 finding (2026-08-07) at dev's recommendation to **decouple the finding from the
> `revoke_source()` feature it was written to enable**. This spec establishes the RECOVERABLE
> ATTRIBUTION RECORD only; the revocation set-computation (`A3`) and the derived-view reach
> (`0004`) consume it. Offered for research/dev reaction, not yet designed to acceptance.

*Fill this in **before** implementing. See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`), from research's A3 finding |
| **Version** | **v1 (stub)** — *re-read before editing; quote the version you approve.* Problem + finding + direction are concrete; the mechanical contract (§4, §6, §7a) is deliberately a sketch pending review of the direction. |
| **Status** | *canonical state is the `Spec-Status:` line at the top; this row states none of it.* |
| **Internal reviewers** | dev · research (finding owner) — **research has not yet reviewed this framing** |
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
onto a survivor* by at least one maintenance op. The new record must reference contributors and
survivors by opaque id + a provenance digest, never by raw memory content (the 0003 refusal-record
discipline). **Open tension (§10 Q1): reversibility may require the contributor's PRIOR scalar
values, which are metadata, not content — to be confirmed.**

## 2c. Untrusted inputs — REQUIRED, blocking

*Draft.* The contributor whose attribution we record may itself be adversarial (a compromised feed
is the motivating case). The record must therefore be **fail-closed and content-free**: it records
*that* a transfer happened and *what state* moved, keyed on opaque ids and a provenance identity,
so a malicious contributor cannot smuggle memory content into a durable audit surface, and a
missing/absent record is treated as "attribution unknown → the survivor's transferred state is
suspect", never "clean".

---

## 3. The finding, at its current sites — REQUIRED, blocking

Three maintenance sites transfer contributor state into a survivor. Reproduce with research's A3
provenance-chain demo (a3_provenance_chain_demo.py, `veracium-research`). Status is stated **as of
0.6.0** (0010 partially moved §3.2 after
A3 was written):

| # | site | contributor recoverable today? | state transferred |
|---|---|---|---|
| **3.1** | **reinforcement** — `graph._build_supersession_plan` reinforcement branch (`insert_incoming=False`; the incoming edge is never persisted, the prior absorbs `max(observed_at)`/`max(confidence)`) | **No** — nothing is written for the contributor | `observed_at`, `confidence` |
| **3.2** | **consolidation** — `lifecycle.consolidate` deletes each input episode (`store.delete_episode`); the summary carries `lineage` (0010) = the input ids in the historical namespace | **Partial (improved by 0010).** `lineage` links a summary to its input IDs, but the inputs are deleted, so **id→source is not recoverable** without an independent index | disclosure, confidence, `derived_from`, `observed_at` |
| **3.3** | **absorption** — `graph._build_supersession_plan` absorption branch retains the absorbed prior and links it by a free-text `note = "absorbed_by:<id>"` | **Partial** — retained + linked, but as a **string in a free-text field, not a queryable relation**, and inherited `min(valid_from)`/`max(observed_at)`/`max(confidence)` cannot be un-inherited | `valid_from`, `observed_at`, `confidence` |

**`specs/0003` did NOT close 3.1.** Its Slice-B rewrite preserved reinforcement semantics
byte-for-byte (`insert_incoming=False`, `prior_upserts=[refreshed]`) — deliberately, to avoid
regressing dedup — so the reinforcement source still vanishes. This is recorded as finding **M9**
(`specs/findings.py`, `owner=0002`, `open`). On adoption, **M9 and its siblings should be
repointed to `0014`.**

**What is NOT wrong (do not "fix" it):** reinforcement, consolidation and absorption are the
INTENDED mechanisms, and the cross-class guard (`graph.py`, "identity merges never cross trust
classes") and the 0002/N9b trust-envelope inheritance (min-disclosure, min-confidence,
third-party influence) are all correct. **The defect is only that the transfer is unattributed,
so it cannot be audited or reversed.** This spec adds a record; it changes no maintenance decision.

---

## 4. Behaviour — proposed direction (SKETCH, pending review)

> **The invariant (a sibling of `0002`'s maintenance-provenance-invariant).** *Every maintenance-
> time transfer of state from a contributor into a survivor leaves a durable, queryable
> **contribution record** that names (i) the survivor, (ii) the contributor's provenance identity
> (source/`evidence_ref`/`author_of_evidence`/`derived_from`), (iii) the fields transferred, and
> (iv) enough to reverse the transfer.* Maintenance may transfer state; it may not transfer it
> **silently**.

Sketch of the mechanism (all deliberately provisional — the point of this stub is to agree the
*direction* before specifying the contract):

- **A durable contribution ledger**, one append-only record per transfer:
  `(survivor_id, contributor_provenance_digest, contributor_ref, transferred_fields,
  prior_survivor_values, at)` — content-free by the 0003 discipline (ids + digests, never raw
  `object`/`note`/`summary`). A new `SCHEMA_VERSION` object (v4→v5), so `Spec-Requires: 0007, 0013`.
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
| **A1** | reinforcement leaves a contribution record naming the incoming source | `test_reinforcement_attributes_the_contributing_source` (the M9 test) |
| **A2** | a consolidated summary's contributors are recoverable from its `lineage` after input deletion | `test_consolidation_contributors_survive_input_deletion` |
| **A3** | absorption's contributor link is queryable, not only a `note` string | `test_absorption_link_is_a_queryable_contribution` |
| **A4** | for any survivor, `contributions(survivor_id)` enumerates every state transfer into it | `test_every_maintenance_transfer_is_enumerable` (adversarial: inject at each of the 3 sites) |
| **A5** | the ledger is content-free — no `object`/`note`/`summary` ever recorded | `test_contribution_records_are_content_free` |
| **A6** | `forget_user` erases the ledger; export/import exclude it (Store-local, like 0003 refusals) | `test_forget_user_erases_the_contribution_ledger` |

**A4 is the one that decides whether the class is closed** — an exhaustive check over all three
sites, so a fourth transfer site added later must extend it rather than reintroduce the finding.

## 7. Failure modes and reversibility

**n/a — draft stub.**

## 7a. Surfaces touched — the honest list (SKETCH)

- `src/veracium/graph.py` — `_build_supersession_plan` (reinforcement 3.1, absorption 3.3): emit a
  contribution record in the plan; the store persists it in the SAME atomic
  `apply_supersession_plan` commit (§0003 §4f already gives us the atomic carrier).
- `src/veracium/lifecycle.py` — `consolidate` (3.2): record input source attribution before deletion.
- `src/veracium/store/base.py` / `store/sqlite.py` — the ledger table, its reads, its erasure; the
  `SCHEMA_VERSION` v4→v5 migration that introduces it (`Spec-Requires: 0007, 0013`).
- `src/veracium/store/schema_version.py`, `store/migration.py` — the additive v5 object + migration.

**Schema:** likely **yes — one new content-free, user-linked table**, `SCHEMA_VERSION` v4→v5, the
same additive shape as 0003's refusal inventory. **This is a real cost** (another store version,
another migration) and §10 Q3 asks whether it is justified by attribution alone or only once a
revocation consumer (`A3`/`0004`) is committed.

---

## 8. Claims and limits

**Claims:** every maintenance-time state transfer becomes auditable and (with a consumer)
reversible; the recurring maintenance-provenance-loss pattern is closed by one invariant rather
than three point fixes.

**Does NOT claim:** it does not revoke a source, compute a blast radius, or make a revocation reach
recall (`A3`/`0004`); it does not change any maintenance *decision* (reinforcement still reinforces,
consolidation still consolidates); it does not authenticate the contributor's provenance labels
(that is the ingest boundary); it does not restore already-lost attribution in existing stores —
the migration starts the ledger empty and records transfers from v5 forward (pre-v5 loss is
unrecoverable, an honest limit to state loudly).

---

## 10. Open questions

- **Q1 — reversibility vs content-freeness.** Reversing a transfer needs the survivor's PRIOR
  scalar values (`observed_at`, `confidence`, `valid_from`) — metadata, not memory content — but
  the contributor's `evidence_ref` may be sensitive. Can the ledger be both reversible AND
  content-free, or does reversal require a controlled non-content-free field? (Leaning: scalars +
  opaque refs are safe; resolve before design lock.)
- **Q2 — scope of reversal.** Confirm this spec stops at the *record* and defers all reversal to
  `A3`/`0004` (dev's recommendation), vs. including a minimal reverse primitive here.
- **Q3 — is a new store version justified by attribution alone?** Or should `0014` land only when a
  revocation consumer (`A3`/`0004`) is committed, to amortise the v5 bump? (Counter: the audit
  value — "why is this fact live?" — stands alone, and the schema cost is paid once regardless.)
- **Q4 — interaction with `0012` (observation-renewal).** `0012` asks whether reinforcement should
  refresh liveness *at all*; if it should not, 3.1's transfer partly disappears and the ledger's
  reinforcement record changes shape. Sequence `0014` against `0012`'s ruling.
- **Q5 — ownership.** These findings live in research-owned `A3`; this stub is dev's framing.
  Research to confirm the decoupling and the invariant before this leaves `draft`.

---

## 11. Review history

| version | verdict | findings | full disposition |
|---|---|---|---|
| v1 (stub) | draft — not yet reviewed | — | this document; from research `A3` §2 |
