# Feature spec: maintenance attribution — a consumed contributor must leave a recoverable record

Spec-Status: draft
Spec-Requires: 0006, 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft (v5, 2026-08-10) — round 1 folded: the reviewer ACCEPTED the two-bin protocol from
> round 1, RULED the §4f tombstone question (frozen point 5 RETAINED for v1 — no tombstone; the
> six unaffected interface points stay frozen; the point-5 change was NOT signed), and returned
> NINE bin-(a) findings, all folded:** input×output consolidation attribution with fence-keyed
> idempotent inserts (R1-1); the draft carries a TYPED consumed-row reference and the STORE
> derives identity from the authoritative row (R1-2); absorption drafts ENTER `0003`'s receipt
> digest — the derived reading is dead by counterexample (R1-3); consolidation payloads record
> each INPUT's own values and reversal is re-computation (R1-4); `survivor_type` joins the table
> key and both reads (R1-5); the tombstone is withdrawn per the ruling with transitive handling a
> named prerequisite for any future severance-capable site (R1-6); the defective test carriers
> are fixed to the v5 contract (min-batch, typed two-arg reads, digest semantics — R1-7); the
> evidence-reference digest gets its own frozen domain-separated construction and the payload a
> CLOSED per-site recursive schema (R1-8); the consumption-site set is a MECHANICAL registry +
> generated manifest + gate, and §7b gains the `0010` amendment and retention carriers (R1-9).
> v5 = the round-2 resubmission under the accepted protocol. Earlier (v4): REVIEW-READY —
> every prerequisite has LANDED.** Since v3:
> **`0006` is ACCEPTED + IMPLEMENTED** (schema v5 shipped; the shared `source_identity_digest`
> primitive is real code this spec's `identity_digest` calls — `src/veracium/source_identity.py`);
> **`0012` is ACCEPTED + IMPLEMENTED + its implementation independently REVIEWED AND ACCEPTED**
> (22 external rounds total), so the reinforcement excision in §3 is landed FACT — the two
> reinforcement tests now PASS as Design-1 attributions and the ONLY remaining attribution gaps
> in the whole suite are this spec's two strict xfails (A2/A3). v4 adds the §7b cross-spec
> carrier table (the `0012` reviews' recurring finding class, pre-empted), mechanizes the §4f
> tombstone CANDIDATE for the A→B→C transitive gap (explicitly the ONE open design question for
> round 1 — it touches frozen interface point 5, so any resolution runs the freeze protocol),
> and updates every stale prerequisite reference. **Review protocol: the two-bin boundary
> standard (accepted by the reviewer for `0012` and proven over 14+8 rounds) is PROPOSED from
> ROUND 1** — bin (a) contract-breaking, bin (b) recorded — see the review package COLLECTED.
> Earlier (v3): **DESIGN-COMPLETE mechanical contract (2026-08-08).** Matured from the v2 stub so the
> `0006`↔`0014` interface can be frozen: `0006` v3 R11 gates `0006` acceptance on `0014` reaching
> mechanical completeness, and this is that. §4 now specifies the `contribution_ledger` table
> (`SCHEMA_VERSION` v6), the `ContributionDraft` a site emits, the per-site ATOMIC write paths (riding
> 0003's plan commit and 0010's fenced txn), the two reads, and erasure/portability; §5 (growth +
> retention), §6 (A1–A10, incl. atomicity A7, append-only A8, the `revoke_source` join A9), §7
> (failure modes) and §7a are concrete. Still `draft` — acceptance needs `0006` accepted first and an
> external review of this contract; nothing implementable yet. Written from research's
> `A3-source-revocation-design.md`
> §2 finding at dev's recommendation to **decouple the record from the `revoke_source()` feature**.
> This spec establishes the RECOVERABLE ATTRIBUTION RECORD only; the revocation set-computation
> (`A3`) and the derived-view reach (`0004`) consume it. **v2 folds research's response
> (`proposals/0014-research-response.md`, 2026-08-08): Q5 CONFIRMED, and the invariant is
> re-keyed from "state transfer" to CONSULT-AND-DISCARD** — research measured that an older/weaker
> contributor leaves every survivor value unchanged (`max()` never moves) yet still vanishes, so a
> transfer-keyed rule would miss it, and that omission is an attack path (stale-but-corroborating
> input becomes the unlogged channel). Q1–Q4 resolved (§10); a `0014 → 0006` dependency is named
> (key the ledger on a **digest** of `0006`'s **`(origin, source_id)` pair** — `0006` v2, R5: identity
> is the pair, `origin` store-minted so a revocation does not reach another HONEST store's records
> (forged imports are `0005`/`0006` R7's boundary, not authenticated here); both
> `source_id` (host free-form) and `evidence_ref` are digested; `origin` is store-minted but digested
> too, as part of the one uniform key. `0014` digests the RESOLVED pair — `0006` §4.6 forbids
> digesting a stored `origin`-absent pair directly).

*Fill this in **before** implementing. See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`), from research's A3 finding |
| **Version** | **v3 (design-complete), amended 2026-08-09 for the reviewer's interface-freeze disposition** — *re-read before editing; quote the version you approve.* The CONSULT-AND-DISCARD invariant + the full mechanical contract (§4 ledger/primitives/reads, §5, §6 A1–A10, §7, §7a) are concrete. Reviewer amendments folded: **F1** `identity_digest` is NULLABLE (NULL iff `source_id` absent — never a `(origin, NULL)` pseudo-source; A4/A5/A9 reconciled); **F2** the digest is `0006`'s one shared `source_identity_digest` primitive (`0006` §4 rule 7/I12); the three stale `0006 §4.5` citations corrected to §4.6; a multi-generation transitive-attribution case (§7) carried into the full review. Still `draft`; the freeze is of the INTERFACE. Implementation waits on `0006` accepted. |
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

Enumerated mechanically from the interface (the method that missed three surfaces in `specs/0002`):
the maintenance ops that consult-and-discard a contributor are `graph._build_supersession_plan`
(absorption — reinforcement is no longer a site, `0012` Design 1) and `lifecycle.consolidate` (via
the 0010 fenced primitives) — see §3 for the sites and §7a for the full surface list. The **payload** fields — those *read from a
contributor and written onto a survivor* — are `Provenance.observed_at`, `Provenance.confidence`,
`Edge.valid_from`, `Provenance.disclosure`, `Provenance.derived_from`; the ledger stores their prior
and new values (all store-clear scalars, Q1) or nothing when no value moved (A1). The identity is
`0006`'s resolved `(origin, source_id)` pair, digested (below).

> **`0014 → 0006` dependency (research Q1/F3, and `0006` v3 R5/R7).** The ledger is keyed on **`0006`'s
> RESOLVED `(origin, source_id)` PAIR**, already the revocation key. `0006` (R5) makes identity the
> pair — `origin` store-minted — so among **HONEST** exports an imported source cannot collide with a
> local one and a revocation keyed on the pair does not reach another store's records. **NOT against
> an adversarial import (`0006` R7): `origin` is namespacing, not authenticated — forged imports are
> `0005`'s untrusted-import boundary, not a structural guarantee here.** `0014` v3 was
> design-complete; the interface was FROZEN (reviewer-signed 2026-08-09) and `0006` has since been
> ACCEPTED (2026-08-09) and IMPLEMENTED (schema v5 shipped) — the dependency is a landed fact, and
> the seven frozen points bind this spec's review (changes to a frozen point need both owners +
> the reviewer). `0006`'s "opaque"
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

The contributor whose attribution we record may itself be adversarial (a compromised feed
is the motivating case). The record must therefore be **fail-closed and content-free**: it records
*that* a contributor was consumed and *what state, if any,* moved, keyed on a **digest** of
`0006`'s **RESOLVED** `(origin, source_id)` pair and a digested `evidence_ref` (`source_id`/`evidence_ref`
are host free-form; `origin` is store-minted but digested too as part of the one opaque key that need
not appear in a durable surface — `0006` F3/R5/§4.6), so a malicious contributor cannot smuggle memory content
into a durable audit surface, and a missing/absent record is treated as "attribution unknown → the
survivor is suspect", never "clean". **The adversary's cheapest evasion is the empty payload** — a
stale-but-corroborating input that moves no `max()` — which is exactly why the record is owed to the
consumption, not the transfer (§4).

---

## 3. The finding, at its current sites — REQUIRED, blocking

Three maintenance sites were found to transfer contributor state into a survivor; **one
(reinforcement, §3.1) is now closed by `0012` Design 1, leaving TWO for `0014` — consolidation
(§3.2) and absorption (§3.3).** Reproduce with research's A3 provenance-chain demo
(a3_provenance_chain_demo.py, `veracium-research`). Status is stated **as of 0.6.0** (0010 partially
moved §3.2 after A3 was written):

| # | site (a maintenance op that consults a contributor then discards/merges/invalidates it) | contributor recoverable today? | payload (state it may transfer) |
|---|---|---|---|
| ~~**3.1**~~ | ~~**reinforcement**~~ — **CLOSED by `0012` Design 1 — LANDED (accepted 2026-08-10, implemented, implementation-review accepted; the two reinforcement tests PASS as Design-1 attributions in `tests/test_0014_maintenance_attribution.py`). NO LONGER a `0014` site.** `0012` Design 1 PERSISTS the reinforcing edge with its own provenance (transfers nothing), so reinforcement is a consult-and-**KEEP**, not a consult-and-discard — the persisted edge IS the attribution. Finding `M9` is repointed `0002`→`0012`. The two reinforcement `xfail`s move to `0012`. | ✅ 0012 | — |
| **3.2** | **consolidation** — `lifecycle.consolidate` deletes each claimed input; the summary carries `lineage` (0010) = the whole claimed set in the historical namespace | **Partial (improved by 0010) — VERIFIED 2026-08-08.** `lineage == the whole claimed input set == exactly the deleted inputs` (`lifecycle.py:142–156`), so every deleted contributor's ID is recorded; what is lost is **id→source** (the deleted episode's provenance). Not worse than "partial" | disclosure, confidence, `derived_from`, `observed_at` |
| **3.3** | **absorption** — `graph._build_supersession_plan` absorption branch retains the absorbed prior and links it by a free-text `note = "absorbed_by:<id>"` | **Partial** — retained + linked, but as a **string in a free-text field, not a queryable relation**, and inherited `min(valid_from)`/`max(observed_at)`/`max(confidence)` cannot be un-inherited | `valid_from`, `observed_at`, `confidence` |

**3.1 is now `0012`'s, not `0014`'s (research ruling, 2026-08-08).** `0003` deliberately preserved the
reinforcement semantics (`insert_incoming=False`), so the source vanished — but the FIX is
`0012` Design 1 (persist the reinforcing edge with its own provenance), not a `0014` ledger record.
Once the edge is stored it IS the attribution, and with "transfers nothing" there is no payload to
record. So **`0014` covers TWO sites — consolidation (3.2) and absorption (3.3).** The consult-and-
discard INVARIANT (§4) is unchanged; one of its three sites simply moved to `0012`. `M9` is repointed
`0002`→`0012` (`specs/findings.py`).

**What is NOT wrong (do not "fix" it):** reinforcement, consolidation and absorption are the
INTENDED mechanisms, and the cross-class guard (`graph.py`, "identity merges never cross trust
classes") and the 0002/N9b trust-envelope inheritance (min-disclosure, min-confidence,
third-party influence) are all correct. **The defect is only that consuming a contributor is
unattributed, so it cannot be audited or reversed.** This spec adds a record; it changes no
maintenance decision.

---

## 3b. Authorization and scope — *full specs only*

- **Cross a user/tenant/scope boundary?** No. Every ledger row carries `user_id` and is tenant-scoped
  by construction (the same isolation as edges/episodes); the two reads take `user_id`; there is no
  cross-tenant query. A contribution to user A's survivor is invisible to user B.
- **Who may see the affected state?** No principal that could not already. The ledger is **Store-local
  metadata** — like the 0003 refusal inventory, it is **never surfaced to the model** (not in recall,
  answer, or the wiki) and never exported (§4e). It is inspection/audit state for the host and
  `revoke_source`, read only through `contributions()`/`contributors_of_source()`.
- **Scope change (sharing, revocation, forget)?** `forget_user` erases the user's rows (A6);
  survivor deletion drops its rows (A10). Revocation itself is `A3`/`0004`, out of scope.
- **Does anything become visible to a principal who could not see it before?** No — identities are
  digests (A5), and the surface is host-side audit, not model-facing.

---

## 4. Behaviour — the mechanical contract (v3, design-complete)

> **The invariant (a sibling of `0002`'s maintenance-provenance-invariant), CONSULT-AND-DISCARD
> keyed — research's sharpening, 2026-08-08.** *Every maintenance operation that **consults** a
> contributor record and then **discards, merges or invalidates** it MUST leave a durable,
> queryable **contribution record** naming (i) the survivor, (ii) the contributor's opaque source
> identity, and (iii) a **payload** — the fields it transferred and their prior survivor values,
> **which may legitimately be empty** — **whether or not any of the survivor's values changed.***
>
> **Why keyed on the operation, not the transfer (measured).** Run an absorption with the
> contributor OLDER and WEAKER: `max()` moves nothing, the survivor's `observed_at`/`confidence`
> are unchanged — and the contributor still vanishes. A *transfer*-keyed rule need not record that,
> yet "which sources support this fact?" omits it and any blast radius under-reports. It is not
> tidiness: an attacker contributes **invisibly** simply by ensuring no `max()` moves, so
> stale-but-corroborating input becomes the unlogged path. The record is owed to the **act of
> consuming a contributor**, and the value change is only its payload.

### 4a. The ledger — one `SCHEMA_VERSION` v6 table (additive, content-free, user-linked)

```
contribution_ledger(
    id              TEXT PRIMARY KEY,     -- store-minted 'contrib-<uuid>'
    user_id         TEXT NOT NULL,        -- tenant scope; forget_user deletes by this
    survivor_type   TEXT NOT NULL,        -- 'edge' | 'episode' (R1-5: the two id namespaces
                                          --   are independent; an Edge and an Episode may
                                          --   legally share a raw id — reads and A10 deletion
                                          --   key on (user_id, survivor_type, survivor_id))
    survivor_id     TEXT NOT NULL,        -- the record that consumed the contributor
    site            TEXT NOT NULL,        -- 'absorption' | 'consolidation' — the CLOSED site
                                          --   set (validated; reinforcement is NOT a site —
                                          --   0012 Design 1; no 'severed' — §4f, the round-1
                                          --   ruling retains frozen point 5 with no tombstone)
    identity_digest TEXT,                 -- 0006 source_identity_digest(resolve(origin, source_id)); NULL iff source_id absent (unknown source — 0006 §4 rule 8, F1)
    evidence_ref_digest TEXT,             -- evidence_ref_digest(origin, evidence_ref) — §4a
                                          --   below (R1-8); NULL iff evidence_ref absent
    payload         TEXT NOT NULL,        -- the CLOSED per-site schema below (R1-8) — MAY be {}
    created_at      TEXT NOT NULL
)
INDEX ix_contribution_ledger_survivor (user_id, survivor_type, survivor_id)
INDEX ix_contribution_ledger_source   (user_id, identity_digest) -- revoke_source's blast-radius join
```

**The evidence-reference digest is its OWN domain-separated construction (R1-8)** — "digest it the
same way" was not a construction: `source_identity_digest` takes a resolved pair under the
source-identity domain. Frozen: `evidence_ref_digest = SHA-256(b"veracium.evidence-ref.v1" ||
len(origin) || origin || len(evidence_ref) || evidence_ref)` over the RESOLVED origin (the same
§4.6 resolution) — origin-scoped so equal host strings in different stores never collide — and
**NULL iff `evidence_ref` is absent**; never a digest of an empty string.

**The payload is a CLOSED, per-site, recursively-validated schema (R1-8) — never arbitrary JSON**
(arbitrary JSON cannot carry A5's content-free guarantee). The store VALIDATES on write,
fail-closed (an invalid payload aborts the whole maintenance transaction, A7):

- *absorption:* `{"fields": {<name>: {"prior": <v>, "new": <v>}}}` where `<name>` ∈ the CLOSED set
  {`observed_at`, `confidence`, `valid_from`, `disclosure`, `derived_from`} and `<v>` is the
  field's own scalar type (ISO timestamp / float / closed enum). Unknown keys, nested objects,
  strings outside the enums: REJECTED.
- *consolidation:* `{"input": {<name>: <v>}}` over the SAME closed field set — **the consumed
  input's OWN values** (R1-4: reversal = recomputation, below), plus `{"output_index": <int>}`.
- `{}` is legal at any site (the consult-and-discard empty payload, A1).

**Append-only** — a row is INSERTed, never UPDATEd or REPLACEd. **Content-free** by the 0003
discipline: the only identity fields are digests (§2/A5); `payload` carries scalar field names and
their prior/new timestamp/float/enum values (store-clear, Q1), never `object`/`note`/`summary`.
`identity_digest` is `0006`'s shared `source_identity_digest(resolve(origin, source_id))` primitive
(`0006` §4 rule 7 / I12 — ONE canonical, length-framed, domain-separated construction; `0014` and
`revoke_source` call the SAME primitive so they re-derive an identical key). It is **NULL when the
contributor has no `source_id`** (`0006` §4 rule 8 / I13 — unknown source, recorded but not
groupable/revocable; never a `(origin, NULL)` pseudo-source). The resolution `0006` §4.6 mandates
happens before the digest, so `revoke_source` (which digests the same resolved pair) joins on
`ix_contribution_ledger_source`. `payload` MAY be `{}` — an empty payload still records the
consumption (A1).

### 4b. `ContributionDraft` — what a site emits

A site hands the store a `ContributionDraft(site, survivor_type, survivor_id,
contributor_type, contributor_id, payload)` — **the contributor is a TYPED REFERENCE to the
authoritative consumed row, never caller-supplied identity strings (R1-2)**: the STORE, inside the
same transaction and BEFORE the row is deleted/invalidated, reads the referenced contributor row
itself, resolves its `(origin, source_id)` per `0006` §4.6, computes `identity_digest` and
`evidence_ref_digest` from what it read, mints the ledger id and `created_at`, validates the
payload against the closed §4a schema, and INSERTs. Hashing a forged caller value binds nothing;
deriving from the authoritative row does. A draft whose `contributor_type`/`contributor_id` does
not resolve to a row this transaction is consuming is an integrity error — the whole op aborts
(A7). `survivor_type`/`survivor_id` are likewise bound to a record the same commit writes.

### 4c. The write path — one commit with the maintenance op it attributes (atomic, per site)

The record MUST commit in the SAME transaction as the maintenance op, or a crash leaves a
consumption with no record (or a record for a consumption that rolled back). Each site already has an
atomic carrier; the draft rides it:

- **3.3 absorption** → `SupersessionPlan` (specs/0003 §4f) gains a
  `contributions: list[ContributionDraft]` field. `graph._build_supersession_plan` populates it (one
  draft per absorbed prior, referencing the absorbed row by type+id), and `apply_supersession_plan`
  derives+INSERTs inside its existing single-commit CAS transaction. **The drafts ENTER `0003`'s
  `_logical_request_digest` (R1-3 — a marked amendment on accepted `0003`): the reviewer's
  counterexample kills the "derivable" reading — two absorptions with different pre-transfer
  `observed_at` values can yield byte-identical final plans and identical receipt digests while
  their required `prior_survivor_values` differ, so a replay could silently attach the WRONG
  contribution record. The digest binds each draft's complete outcome (site, survivor type+id,
  contributor type+id, canonical payload JSON), alongside the fields it already binds.**
  Absorption keeps its `note` for back-compat but the LEDGER is the queryable path (A3).
  *(Reinforcement — the former 3.1 — is `0012`'s: it persists the edge, which is the attribution.)*
- **3.2 consolidation — the relation is INPUT × OUTPUT (R1-1), and the payload is the input's OWN
  values (R1-4).** A consolidation may write SEVERAL outputs, and `0010` X8 binds EVERY output's
  `lineage` to the WHOLE claimed set — so attribution is the full cross product: for M outputs over
  N claimed inputs, **N×M rows** — each output enumerates every contributor (A2/A4). Mechanically:
  `write_consolidation_output_if_current` (a marked additive amendment on accepted `0010`, §7b)
  derives-and-INSERTs, for the output row it writes, one ledger row PER CLAIMED INPUT — reading each
  input's `(origin, source_id)`/`evidence_ref`/scalar fields while the inputs still exist (deletion
  is X1-later) — all inside the SAME fenced transaction as the output write. **Retry-safe:** the
  insert is keyed idempotent under the fence — `(operation_id, output_index, contributor_id)`
  re-written under the SAME fence deletes-then-inserts its own rows, never duplicates; a takeover
  under a NEW fence starts from the recovery rules `0010` already defines. **The payload records
  the INPUT's own scalar values** (`{"input": {...}, "output_index": i}`) — an output is newly
  created (it HAS no prior values) and its trust fields are whole-set reductions (X8/X12/X23), so
  reversal is RE-COMPUTATION: remove contributor X, re-derive the reduction over the remaining
  inputs' recorded values (with confidences 0.1/0.2/0.9, dropping the 0.1 contributor recomputes
  min=0.2 from the ledger alone). §7/§8's reversibility claim is restated in exactly those terms.

**Failure rule (mirrors 0003 §4f):** if the maintenance op rolls back, its ledger rows roll back with
it — no partial state. A site that cannot emit atomically MUST NOT perform the consumption.

### 4d. The reads (Store-local, the exact queries the consumers need)

- `contributions(user_id, survivor_type, survivor_id) -> list[ContributionRecord]` — every
  contributor consumed into a survivor, newest first (type-keyed, R1-5 — an Edge and an Episode
  sharing a raw id never merge). The "why is this fact live?" audit (§1) and A4.
- `contributors_of_source(user_id, identity_digest) -> list[ContributionRecord]` — every survivor a
  source contributed to. **`revoke_source`'s blast-radius join** (`A3`) — given a `(origin, source_id)`
  to revoke, it resolves+digests and calls this. Read-only; `0014` computes no blast radius itself.

### 4e. Erasure and portability (Store-local metadata, like the 0003 refusal inventory)

`forget_user` deletes the user's ledger rows (A6). Export/import EXCLUDE it — a contribution is a
fact about *this store's* maintenance history, not the memory; importing one would assert a
consumption that never happened here. **No `FORMAT_VERSION` change** from the ledger itself.

**Explicitly OUT of scope (the decoupling):** actually reversing a transfer, computing a source's
blast radius, and making a revocation reach recall — those are `A3` / `0004`. `0014` guarantees the
record exists, is atomic with the consumption, and is queryable by the two reads above; acting on it
is theirs.

---

### 4f. The transitive gap — RESOLVED round 1: frozen point 5 retained; transitive handling is a
### named PREREQUISITE for any future severance-capable site

**RESOLVED — the round-1 ruling (reviewer, 2026-08-10): FROZEN POINT 5 IS RETAINED for v1;
there is NO tombstone.** The reviewer's grounds, accepted in full: (i) the proposed tombstone was
not mechanically viable — its join could not identify the deleted survivor (`identity_digest` is a
many-to-one SOURCE key and may be NULL; the payload carried no lineage field), the `severed` site
was absent from §4a's closed set, A5's grammar had no tombstone shape, and the reads had no
structured incomplete status; (ii) **the B→C severance path is PRESENTLY UNREACHABLE** — accepted
`0010` excludes consolidation outputs from later consolidation, so no v1 site can consume a
survivor that itself has contributors. **The standing REQUIREMENT this ruling creates:** any
future spec that adds a consumption site capable of consuming a survivor-with-contributors MUST
first land transitive handling (with typed contributor-record links and a defined query-result
status) as a named prerequisite — recorded in §7, §8, and the A4 site registry, so the gap cannot
arrive silently. The candidate text below is retained as REJECTED-FOR-V1 history.*

The gap (§7): `source A → survivor B → consolidation into survivor C`. B's hard-deletion drops the
`(survivor=B, contributor=A)` rows (A10), so A's contribution becomes undiscoverable from C — a
`revoke_source(A)` blast radius silently under-reports. Two candidates:

- **CANDIDATE (proposed): the SEVERANCE TOMBSTONE — make the gap visible, retain nothing more.**
  Mechanically: when a survivor's deletion would drop ledger rows in which that survivor is the
  `survivor_id` AND the survivor itself appears as a *contributor identity* in other LIVE rows
  (join: the deleted survivor's own resolved identity digest appears in any live row's
  `identity_digest`, or the survivor's id appears in a live row's `payload` lineage field), the
  SAME deleting transaction writes ONE tombstone row: `site='severed'`, `survivor_id` = the LIVE
  downstream survivor's id, `identity_digest` NULL, `payload` = `{"severed_rows": <n ≤ 999+>,
  "deleted_survivor": <id>}` — content-free, append-only (A8), retained under A10 by the DOWNSTREAM
  survivor. The two reads then report honestly: `contributions(C)` includes the tombstone, and any
  `contributors_of_source()` / future `revoke_source` join that touches a user with tombstones
  returns an explicit **"incomplete: N links severed"** marker instead of a confidently short
  answer. Cost: one row per severed link-set, bounded by deletions, no transitive retention.
- **REJECTED-BY-DEFAULT alternative: propagate inherited identities onto the downstream survivor's
  rows.** Retains MORE (unbounded transitive copying) — exactly what survivor-existence retention
  exists to prevent (research, 2026-08-09).

Acceptance criteria for whichever rule the review lands: **A4/A9/A10 gain the multi-generation
case** (A→B→C, delete B: either A remains reachable from C, or every consumer-visible query
honestly reports the severed link), and frozen point 5's wording is re-signed if it moves.

## 5. Regime analysis — where does this behave differently?

- **Growth is the regime that matters.** The ledger gains one row per maintenance CONSUMPTION —
  absorption fires ~one `remember()` apart, consolidation once per `maintain()` batch (one row per
  claimed input). Over a long-lived, high-write store this **accumulates without
  bound** if never pruned. **Retention rule (frozen): a ledger row is kept while its `survivor_id`
  exists; when the survivor is hard-deleted (`forget_user`, or a future hard-delete) its rows go**
  — the same "kept while the thing it describes exists" rule as the 0003 refusal inventory. This
  bounds the ledger to live survivors, not to all history. A row is never pruned merely for age: an
  old contribution is exactly what a late `revoke_source` needs.
- **Per-op cost is O(1)–O(batch).** Absorption adds one INSERT to an already-atomic
  supersession commit; consolidation adds one INSERT per claimed input to its already-atomic fenced
  transaction. No new round-trip, no budget/cap/recompile-threshold interaction (the ledger is off the
  recall and wiki paths entirely).
- **The regime a single-op test misses — and MUST reach (A4):** the empty-payload consumption
  (absorption where no `max()` moves, A1) and the delete-then-recover case (consolidation, A2). A
  test that only exercises a value-moving absorption would pass while the attack path (empty
  payload) stayed open — so A4 injects at every declared site INCLUDING a no-payload consumption. This is a
  **stable (on-by-default)** behaviour, so that regime blocks: A1/A2/A4 are required, not optional.
- **Cold vs warm store:** identical — the ledger does not touch the wiki cache or retrieval scoring.
- **Concurrency:** the ledger inherits the atomicity of the carrier it rides (0003's CAS commit,
  0010's fence) — two concurrent maintenance ops on the same survivor each write their own row under
  their own commit; rows are append-only and never contend (§6 A8).

## 6. Invariants and executable checks — REQUIRED, blocking

*The invariant names are frozen (v3). Per PROCESS §4a they become mandatory implementation/release
gates once the design is `accepted`; they are prospective here (unbuilt), like `0003`'s I1–I9 were.*

| | invariant | executable check |
|---|---|---|
| **A1** | a consumption is recorded **EVEN WHEN THE PAYLOAD IS EMPTY** — an older/weaker contributor that moves no `max()` is still recorded (the consult-and-discard key; closes the attack path). GENERAL over every `0014` site. *(Reinforcement's specific instance MOVED to `0012` — Design 1 persists the edge; its two `xfail`s are `0012`'s.)* | `test_absorption_records_the_contributor_even_when_no_value_moves` — an absorption whose absorbed prior is older/weaker moves no `max()` yet is recorded |
| **A2** | a consolidated summary's contributor SOURCES are recoverable after input deletion (not only the `lineage` ids) — over the FULL INPUT×OUTPUT relation (R1-1): with N claimed inputs and M outputs, EVERY output enumerates all N contributors (N×M rows) | `test_consolidation_contributors_survive_input_deletion` (`xfail` today; the flip asserts the cross product on a MULTI-output op — ≥ `consolidate_min_batch` inputs, 2 outputs, 2×N rows) |
| **A3** | absorption's contributor link is queryable via `contributions()`, not only a `note` string | `test_absorption_link_is_a_queryable_contribution` (`xfail` today) |
| **A4** | for any survivor, `contributions(user_id, survivor_type, survivor_id)` enumerates every CONSUMED CONTRIBUTOR (payload empty or not) across every `0014` site — and the site set is a MECHANICAL registry, not a remembered list (R1-9): a `CONSUMPTION_SITES` constant in code + a GENERATED consumption manifest (`specs/generated/0014-consumption-manifest.md`, the 0002 audit-manifest pattern) enumerating every code path that INSERTs a ledger row — incl. a branch inside an existing store mutator — with a gate test that fails when the code and the manifest disagree. A contributor with **no `source_id`** is still enumerated, `identity_digest` NULL (F1/I13) | `test_every_consumed_contributor_is_enumerable` — inject at each registered site incl. an absent-`source_id` contributor (NULL digest asserted) · `test_the_consumption_manifest_matches_the_code` — the generated-manifest gate: every ledger INSERT site is registered; an unregistered INSERT fails the gate |
| **A5** | content-free — `identity_digest` via the shared `0006` primitive; `evidence_ref_digest` via the frozen §4a evidence-reference construction (its OWN domain, origin-scoped, NULL iff absent — R1-8); `payload` VALIDATES against the CLOSED per-site recursive schema (§4a) — unknown keys/types/nesting REJECTED, the whole op aborting (A7); no `object`/`note`/`summary` ever | `test_contribution_records_are_content_free` · `test_a_malformed_or_adversarial_payload_aborts_the_op` — unknown keys, nested objects, non-enum strings, oversized values at EACH site: the op rolls back whole |
| **A6** | `forget_user` erases the user's ledger rows; export/import EXCLUDE the ledger (§4e) | `test_forget_user_erases_the_contribution_ledger` · `test_export_excludes_the_contribution_ledger` |
| **A7** | the record is ATOMIC with the maintenance op — if the op rolls back, its ledger rows roll back; no consumption without a record and no record without a consumption (§4c) | `test_a_rolled_back_maintenance_op_writes_no_ledger_row` — inject a failure after the op's writes but before commit at each site; assert neither the op nor its rows persist |
| **A8** | the ledger is APPEND-ONLY — a row is never UPDATEd or REPLACEd; concurrent ops each write their own row | `test_ledger_rows_are_append_only` · `test_concurrent_consumptions_each_write_one_row` |
| **A9** | `identity_digest` is the shared `source_identity_digest` over the RESOLVED pair (F2/I12) and JOINS with `revoke_source` — a source digested for revocation finds exactly its contribution rows. Applies to **COMPLETE identities only**: a NULL-digest (unknown-source) row NEVER joins a revocation (F1/I13) | `test_contributors_of_source_joins_a_revocation_pair` — write via a site, then look up by `source_identity_digest(resolve(origin, source_id))`; assert the row is found, and that an unknown-source row is NOT returned by any revocation join |
| **A10** | a ledger row is kept while its `(survivor_type, survivor_id)` exists and dropped when the survivor is (retention, §5; type-keyed — R1-5: an Edge and an Episode sharing a raw id delete independently) | `test_ledger_row_is_dropped_with_its_survivor` — incl. the same-raw-id Edge+Episode pair: deleting one leaves the other's rows |

**A4 is the one that decides whether the class is closed** — exhaustive over the declared sites *keyed on
consumption, not value change*, so neither a fourth site nor an empty-payload consumption (A1) can
reintroduce the finding. **A7 is what makes it crash-safe**; **A9 is what makes it usable by
`revoke_source`.**

## 7. Failure modes and reversibility

- **🔴 Silent failure — a NEW consumption site added later that does not emit.** This is the exact
  failure this spec exists to close, one level up: if a fourth maintenance path that consults-and-
  discards a contributor is added without emitting a draft, the finding returns and nothing complains.
  **Mitigation: the set of consumption sites is DECLARED, not remembered** — mirror the 0002 audit
  manifest, which enumerates every store mutator so a new one cannot hide. A4 iterates that declared
  set; adding a consumption path without registering it fails A4. First visible symptom otherwise: a
  survivor with a value that moved but `contributions()` empty.
- **Partial failure — a consumption without a record, or a record without a consumption.** Prevented
  by A7: the row commits in the SAME transaction as the op (0003's CAS commit / 0010's fenced txn), so
  a crash mid-op rolls back both. A site that cannot write the row atomically MUST NOT perform the
  consumption. (Permanent write errors must surface, never degrade to a silent success.)
- **Reversibility (restated per R1-4).** For ABSORPTION the record carries `prior_survivor_values`
  — direct restoration material. For CONSOLIDATION an output has no prior values and its trust
  fields are whole-set reductions, so the record carries each INPUT's own scalar values and
  reversal is RE-COMPUTATION: drop the revoked contributor's rows, re-derive the reduction over
  the remaining recorded inputs. `0014` guarantees the ledger is SUFFICIENT for both forms;
  performing either is `A3`/`0004`, not this spec (the decoupling).
- **🟠 Transitive attribution across generations — carry into the FULL `0014` review (reviewer +
  research; NOT an interface-freeze blocker NOW).** Chain `source A → survivor B → consolidation into
  survivor C`: A contributed to B, then B is itself consumed into C. Under survivor-existence retention
  (A10), hard-deleting B takes B's ledger rows with it — so A's contribution can become undiscoverable
  from C, and survivor-based retention silently erases *transitive* source attribution.
  **⚠️ This touches FROZEN INTERFACE POINT 5, not an unfrozen internal detail (research, 2026-08-09).**
  Point 5's *"retained only while its survivor exists"* is exactly what drops `(survivor=B,
  contributor=A)` on B's deletion. The *rule* is unchanged today, so "not a freeze blocker" holds — but
  **any resolution that alters the retention rule changes frozen point 5 and re-triggers the freeze
  protocol (both owners + reviewer); it must NOT be treated as an internal `0014` tidy-up.** An earlier
  draft of this note proposed *propagating inherited contribution identities onto the new survivor's
  rows*; that is **dispreferred — it RETAINS MORE, and survivor-existence retention is precisely what
  keeps the ledger from becoming an unbounded audit log.** **Leading candidate (research's early read):
  make the gap VISIBLE rather than retain more** — a hard-deleted survivor that still has downstream
  descendants leaves a **tombstone** recording that a link was severed, so a blast-radius / `revoke_source`
  query returns *"incomplete: a link was deleted"* instead of a confidently short answer. A revocation
  that knows it is incomplete is the `A3` argument; one that silently under-reports is the failure this
  spec exists to prevent. **A4/A9/A10 must gain a multi-generation case** (A→B→C, delete B, assert A is
  either still reachable from C OR the query honestly reports the gap) before `0014` is accepted.
  Recorded here so the full review does not miss it; the interface freeze proceeds without it.
- **New attack surface.** (a) A caller forging `survivor_id` or a foreign identity — blocked: the
  store binds `survivor_id` to a record it is writing in the same commit, and resolves+digests the
  identity itself (§4b). (b) Memory content smuggled into the ledger — blocked: identities are digests,
  `payload` is scalar field names + timestamp/float/enum values (A5). (c) An attacker staying invisible
  by ensuring no `max()` moves — closed by the consult-and-discard key (A1). (d) Unbounded ledger
  growth as resource exhaustion — bounded by survivor-existence retention (§5, A10); a consumption of a
  survivor that is later deleted takes its rows with it.

## 7a. Surfaces touched — the honest list

- `src/veracium/schema.py` — new `ContributionDraft` (a site emits) and `ContributionRecord` (read
  back); `SupersessionPlan` gains a `contributions: list[ContributionDraft]` field (§4c).
- `src/veracium/graph.py` — `_build_supersession_plan` populates `plan.contributions` for
  absorption (3.3) — one draft per consumed prior. No new mutator call site: it rides the existing
  `apply_supersession_plan`. (Reinforcement (3.1) is NOT a site — `0012` Design 1 persists the edge.)
- `src/veracium/lifecycle.py` / the 0010 consolidation primitives — `consolidate` (3.2) writes one
  draft per claimed input BEFORE `delete_claimed_inputs_if_current`, in the same fenced transaction.
- `src/veracium/store/base.py` / `store/sqlite.py` — `apply_supersession_plan` extended to INSERT
  `plan.contributions` in its existing commit; the consolidation primitive extended likewise; the two
  reads `contributions()` / `contributors_of_source()`; `forget_user` erases the ledger;
  `store_mutator` accounting for the new writes (0002 audit manifest). `identity_digest` is computed
  via `0006`'s single shared `source_identity_digest` primitive (F2/I12) — the SAME one `revoke_source`
  uses — and is NULL when the contributor has no `source_id` (F1/I13).
- `src/veracium/store/schema_version.py`, `store/migration.py` — the additive `contribution_ledger`
  table + its two indexes as `SCHEMA_VERSION` **v5→v6** (`0006` takes v5; `Spec-Requires: 0006, 0007,
  0013`), the v5→v6 migration, and evidence regeneration.
- `src/veracium/portability.py` — export/import EXCLUDE the ledger (§4e); **no `FORMAT_VERSION`
  change** from it.

**Schema:** **yes — one new content-free, user-linked table + two indexes**, `SCHEMA_VERSION` v5→v6
(after `0006`'s v5), the same additive shape as 0003's refusal inventory. The cost — another store
version + migration — is accepted (§10 Q3): the ledger cannot attribute a consumption that happened
before it existed, so deferring the schema **permanently loses the interval**, not just the work.

---

## 7b. Cross-spec carriers — what asserts TODAY'S behaviour and must move in the SAME commit

*The `0012` reviews' single most recurring finding class was carrier drift — a fix landing while
some test, docstring, or sibling-spec sentence still asserted the superseded behaviour. This table
pre-empts it: every known carrier of pre-`0014` behaviour, each to be inverted/extended in the SAME
implementation commit as the behaviour it describes.*

| carrier (asserts TODAY) | today's assertion | the same-commit disposition |
|---|---|---|
| `tests/test_0014_maintenance_attribution.py::test_consolidation_contributors_survive_input_deletion` | **strict xfail** — lineage ids resolve to nothing after input deletion (A2's finding, executably) | the marker comes OFF; the helper `_summary_contributor_sources` already prefers `store.contributions()` — the assertion flips to the recovered source set |
| `::test_absorption_link_is_a_queryable_contribution` | **strict xfail** — the contributor link is only the free-text `note` back-pointer (A3's finding) | the marker comes OFF; `_absorption_contributor_queryable` already probes `contributions()` — flips to the queryable record. **The `note` back-pointer STAYS** (presentation; the render-history exclusion keys on it) — the ledger row is the QUERYABLE record beside it, not a replacement |
| `src/veracium/store/schema_version.py` `SCHEMA_VERSION` + `accepted_digests` + the evidence files; every test pinning the head symbolically | head = v5 (`0006`) | v5→v6 with the additive `contribution_ledger` + two indexes; migration + regenerated evidence (the exact carrier path the `0006` v4→v5 bump walked) |
| `specs/generated/0002-audit-manifest.md` + `specs/audit_dispositions.py` | no ledger INSERT sites exist | the extended `apply_supersession_plan` / consolidation-primitive writes get dispositions; the manifest regenerates (a NEW mutator cannot hide — the same declared-set discipline §7 requires of consumption sites) |
| `src/veracium/portability.py` + its tests | a v4 export's content set | export/import EXCLUDE the ledger — a test asserts the export byte-set is unchanged by ledger rows; **no `FORMAT_VERSION` change** |
| `SupersessionPlan` docstring + `specs/0003` §4f plan-shape text | the plan carries incoming/upserts/invalidations/refusals | gains `contributions: list[ContributionDraft]` — BOTH carriers state it same-commit (a marked additive amendment on accepted `0003`; the store INSERTs it inside the existing CAS commit, A7) |
| `0003`'s receipt digest (`_logical_request_digest`) + `test_a_differing_resubmission_conflicts_field_by_field` | binds the complete logical outcome, WITHOUT contribution drafts | **R1-3 (the round-1 counterexample killed the derived reading): the drafts ENTER the digest** — site, survivor type+id, contributor type+id, canonical payload per draft — a marked amendment on accepted `0003`; the store test gains a contribution-field mutation case (same final plan, different prior_survivor_values → SupersessionIntegrityError, never a silent replay) |
| accepted `0010` `write_consolidation_output_if_current` + its X-invariant tests | writes one output + lineage under the fence; no ledger | a marked ADDITIVE amendment (R1-1/R1-9): the primitive derives-and-INSERTs the per-input ledger rows for the output it writes, idempotent under `(operation_id, output_index, contributor_id)` per fence; the X-suite gains the retry/takeover ledger cases |
| the store deletion/retention paths (`forget_user`, `invalidate_edge`, hard-delete, consolidation input deletion) + their tests | delete records without touching any ledger | A10's retention rides them: survivor deletion drops the survivor's rows (type-keyed); the deletion tests gain the ledger assertions (R1-9) |
| `CHANGELOG.md` + the release upgrade note | v5 store, one-call migration | the v6 note + the pending upgrade-recommendation release line (the platform point rides this) |

## 8. Claims and limits

**Claims:** every maintenance-time *consumption of a contributor* — value change or not — becomes
auditable and (with a consumer) reversible — by direct restoration at absorption, by
re-computation over the recorded per-input values at consolidation (R1-4); the recurring maintenance-provenance-loss pattern is
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
  timestamps/floats/closed enums — store-clear. `evidence_ref` and `source_id` are host free-form and
  are **digested**; `origin` is **store-minted** (`0006` §4.1) — not a content risk, but digested too
  as part of the one opaque key so a single `digest` covers the whole identity (`0006` F3/R5). The
  digest is over the **RESOLVED** pair — `0006` §4.6 forbids digesting a stored `origin`-absent pair —
  and stays joinable for `revoke_source`. Keying on `digest(resolved (origin, source_id))` names the
  `0014 → 0006` dependency (§2).
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
  re-key to consult-and-discard — is folded into §4/§6. The v3 remainder is MET as of v4: the mechanical contract is full (§4/§6/§7a/§7b), and `0006` is accepted + implemented — nothing gates the external review.

---

## 11. Review history

| version | verdict | findings | full disposition |
|---|---|---|---|
| v1 (stub) | draft — dev framing from research `A3` §2 | — | this document |
| **v2 (stub)** | **research reviewed: decoupling CONFIRMED; invariant re-keyed to consult-and-discard; Q1–Q5 resolved; `0014 → 0006` named** | 1 (the transfer-vs-consume sharpening) | `proposals/0014-research-response.md`; this document |
| **v3** | **design-complete mechanical contract; the `0006`↔`0014` interface FROZEN (reviewer-signed 2026-08-09; seven points; F1 nullable digest / F2 shared primitive / F3 §4.6 folded); the A→B→C transitive gap recorded against frozen point 5** | — | this document; the `0006` §11 closure |
| **v4** | **review-ready maturation (2026-08-10): prerequisites LANDED (`0006` accepted+implemented; `0012` accepted+implemented+impl-review-accepted — reinforcement excision is fact); §7b carrier table added; §4f tombstone CANDIDATE mechanized as the round-1 design question; two-bin protocol proposed from round 1** | — | this document |
| **v5** | **round 1 EXTERNAL (2026-08-10): the two-bin protocol ACCEPTED; the §4f question RULED (frozen point 5 retained, no tombstone, transitive handling = prerequisite for future severance-capable sites); NINE bin-(a) findings returned and folded (R1-1…R1-9)** | 9 | `specs/reviews.py`; this document |
