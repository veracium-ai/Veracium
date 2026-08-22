# Feature spec: source identity — `(origin, source_id)`

Spec-Status: accepted
Spec-Requires: 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **✅ accepted (v6, 2026-08-09).** The external reviewer passed `0006`'s acceptance review (round 5); v6 folds the mechanical closure edits they required — **C1** (removed superseded "no-DDL" wording + refreshed the External-review row), **C2** (UUID entropy stated exactly — 122 random bits), and the **§11 Review closure** ledger — *no design change* from the reviewed v5. Earlier: the `0006`↔`0014` seven-point interface is FROZEN + reviewer-signed (independent of `0014`'s own acceptance); v5 folded F3 (v4-import absent-`origin` rejected, I14); v4 folded F1/F2; v3 folded R7–R11. **`Spec-Status: accepted` authorises implementation** (`Spec-Requires` 0007/0013 both accepted).
> The round-2 reviewer returned v2 for one more amendment; v3 folds all five: **R7** — `origin` is
> **collision-resistant NAMESPACING, not authenticated provenance** (it is materialised into exports
> and `0005` treats imports as untrusted, so an adversarial import can forge it; the strong "structurally
> incapable of reaching another store's records" reading holds only against HONEST exports — auth is
> out of scope, §8, future option Q4). **R8** — the local `origin` needs **durable state**: a new
> singleton `store_identity` row (minimal DDL, not the v2 "no DDL"), so absent-`origin` resolution has
> a persistent value; existing rows need NO backfill (§0b/§4.2/§5). **R9** — the origin invariant split
> into I2a (local caller can't set `origin`) and I2b (import PRESERVES foreign `origin`) — v2's single
> combined rule contradicted itself. **R10** — a field newer than an import's declared `FORMAT_VERSION` is STRIPPED (I10), closing
> the old-envelope-with-new-field capture. **R11** — the `0006`↔`0014` interface was AGREED but not
> "fully locked": `0014` was a `v2 (stub)`, so `0006` acceptance waited on `0014` reaching mechanical
> completeness + the interface freeze — **both SATISFIED 2026-08-09: `0014` is mechanically complete
> and the interface is frozen + reviewer-signed, so `0006` is now ACCEPTED** (rounds 3–5). Resolve-at-
> read + I9 (the v2 interface-lock fix) stand.
>
> _v2 (superseded) — the three shape changes carried forward:_
> **(1) `evidence_basis` is SPLIT OUT — `0006` v1 ships `source_id` ONLY.** The basis field had
> no v1 consumer, its `observed` value collides with `SourceType.OBSERVED` (same word, near-opposite
> meaning, same `Provenance` object), and its three-value contract (`derived`) was never reviewed —
> it becomes a successor spec, sequenced after the `A1` `SourceType` deletion and alongside `0001`.
> **(2) Source identity is `(origin, source_id)`** — `origin` is minted by the STORE, never host-
> supplied, so two hosts' `"mailbox:primary"` cannot collide on import (R5). **(3) The storage change
> is NO-DDL (§0b, R3):** the whole `Edge`/`Provenance` lives in a `json` blob, so adding `source_id`
> needs no column; the `SCHEMA_VERSION` bump **v4→v5** exists only to make an older build REFUSE
> rather than silently drop the new field (`Provenance` is `extra=ignore`). R3 also holds:
> `source_id` may GROUP, never GRANT — §3 is diagnostic-only (every cell *"flag stays"*), and I5
> states it affirmatively. **v1 consumer: `0014` (maintenance attribution), which keys its ledger on
> the `(origin, source_id)` pair (digested); `0014`'s table is the NEXT `SCHEMA_VERSION` after this
> one (v6).** All open questions resolved (Q1/Q2/Q3, §10). **✅ The `0006`↔`0014` interface is
> LOCKED — research re-ratified and the reviewer signed (2026-08-09); the `source_id` requirement is
> settled at the digested resolved pair (raw → digest → pair, F1/F2 folded). The interface sign-off is
> SEPARATE from `0006` acceptance — acceptance was held for F3 (v4-import absent-`origin`), folded in
> v5, then PASSED at round 5 → **v6 `accepted`** (v6 = v5 + mechanical closure C1/C2/§11).**

## 0b. 📥 Migrations are owned by `specs/0013`

> **UPDATE 2026-08-07/08: the migration contract EXISTS and is implemented.** `0013` is `accepted`
> and its offline v→v+1 migration is in production (`0008`/`confirmations` was the first user;
> `0003` took the store to `SCHEMA_VERSION` 4). **The `source_id`/`origin` provenance FIELDS need no
> DDL** — the `edges` row stores the whole `Edge`/`Provenance` in a `json TEXT` blob
> (`store/schema_version.py:125`), so they change the **JSON payload only**. The bump's purpose for
> the fields (measured, R3): `Provenance` is `extra=ignore`, so an older build **silently discards**
> them; `0007` makes an older build REFUSE a v5 store instead. **BUT v3-of-this-spec (R8) adds ONE
> piece of durable DDL: a singleton `store_identity` row** holding the local store's persistent
> `origin` (§4.2) — required because "absent `origin` = this store" must resolve to a value that
> survives reopen/backup. **So the v4→v5 migration is: create the `store_identity` singleton with a
> random origin (transactional), + the payload/version-gate for the fields. It is MINIMAL DDL — one
> new singleton, NO per-record change and NO backfill** (existing rows keep `origin` absent and
> resolve, §5). **`0014`'s contribution-ledger table is the NEXT version, v6** — resolving the
> `0006`-and-`0014`-both-claim-v5 conflict the reviewer flagged.

**The provenance FIELDS require no per-record DDL (a new `Provenance` field in the `json` blob); the ONLY DDL `0006` adds is the one `store_identity` singleton (minimal DDL, R8) —
but it still consumes a `SCHEMA_VERSION` so an older build refuses rather than silently drops it**
(R3). The migration/versioning contract is **`specs/0013`**+**`0007`**, not this spec.

It was briefly placed here when `0007` was cut on 2026-08-03. **The round-8
external reviewer was right that this was wrong**: `0006` is a `draft` whose §3
is falsified, and hanging every other schema-changing spec off it would make
them wait on an unrelated unresolved design — and the gate reads direct
`Spec-Requires:` entries, so it could not have expressed the dependency anyway.

`0006` now declares `Spec-Requires: 0007, 0013`. **The eight conclusions that
survived seven rounds of `0007` review are stated in full in `0013` §4**, not
left in an archive.

---

## 0. ⚠️ R3 overturns §3 — read this before the rest

**`source_id` may GROUP. It must never GRANT.** No authority, no staleness
clearing, no supersession entitlement keyed on it.

**My error, and it is worth stating exactly.** I posted R3 leaning *"(a) strict
**for now**"*, implying `source_id` would later relax it. **Research corrected
the premise: it cannot.** Their own constraint was *opaque and host-supplied,
never model-supplied* — and **never model-supplied ≠ authenticated**. A host that
sets `source_id` can give two unrelated statements the same one, and
same-source reinforcement would then clear staleness on evidence with **no
common source**. **That grants precisely what the strict rule withholds**, so
this spec as drafted would have re-opened the hole the second external review
found, one layer down and harder to see.

**The principle that replaces it, which we already had and neither of us
applied:** *an act through a dedicated entry point is evidence; a field
asserting who acted is not.* **Add an entry point, not a parameter.** Verified
independently: `author="user"` rides on `remember`, which is `@server.tool()`
and **model-reachable**; `confirm()` is host-API only — not an MCP tool
(`remember` · `recall` · `answer` · `maintain` are the four), not a CLI verb.

**What this spec became (v2):** `(origin, source_id)` is **diagnostic** — it answers *did these come
from the same place?* and improves grouping, dedup and inspection. **A lying host degrades grouping
quality instead of crossing a trust boundary.** The thing that would actually unblock staleness
relaxation is **provenance of the call, not of the claim** — recording which entry point was used and
requiring hosts to gate the privileged ones. That is a separate axis (the deferred `evidence_basis`
successor / `evidence-basis-design.md`), not a staleness rule's, and it is on no roadmap.

---


| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v6 — ACCEPTED 2026-08-09** — *the reviewer passed `0006`'s acceptance review (round 5, no further design round). v6 = v5 + the mechanical closure edits required for the status transition, no design change: **C1** removed the superseded "no-DDL" claims (§0b/§1/Q3) and refreshed the stale External-review row; **C2** stated the origin entropy exactly (a canonical UUIDv4 from a CSPRNG, **122 random bits** — not 128, UUIDv4 fixes 6 bits); **§11 Review closure** ledger added (PROCESS.md §4a). v5 folded F3 (v4-import absent-`origin` rejected as malformed, I14) + the origin-generation/store-lineage-identity amendments; v4 folded F1/F2 (nullable digest, one shared canonical `source_identity_digest`); v3 folded R7–R11. The `0006`↔`0014` interface freeze was reviewer-signed at round 4 and is independent of `0014`'s own acceptance.* |
| **Status** | *see `Spec-Status:` — canonical.* Opened from `0002` R2; **deliberately not folded into `0002`**, which is being split precisely because it kept absorbing work. |
| **Internal reviewers** | research — **ruled that this is needed and that it needs its own spec** |
| **External review** | required — touches stored provenance; a minimal-DDL `SCHEMA_VERSION` v4→v5 (one `store_identity` singleton) + `FORMAT_VERSION` 3→4 bump. **5 external rounds → ACCEPTED 2026-08-09.** R1: return, 6 findings → v2. R2: return, R7–R11 → v3. R3: interface-freeze disposition, F1/F2 + 2 cleanups → v4 (point 4 re-ratified by research). R4: interface freeze reviewer-SIGNED, acceptance held for F3 → v5. R5: **acceptance PASS**, mechanical closure (C1 stale no-DDL wording, C2 UUID entropy, this Review closure) → v6 `accepted`. Full ledger: §11 + `specs/reviews.py`. |
| **Decision + date** | **ACCEPTED 2026-08-09** — external round 5 (acceptance pass; no further architectural blocker). *(Row filled 2026-08-22 — the spec-table audit found it empty.)* |
| **Path** | full |

---

## 1. Problem and motivation

**`author_of_evidence` is a trust *class*. Three specs are using it as a source
*identity*, because there is nothing else to use.**

| spec | what it needs | what it uses | the compensating weakening |
|---|---|---|---|
| **`0002` M3** | *did the same source that stated this fact restate it?* | author-class equality | **the rule is now fail-closed** (§7b): `SYSTEM` repetition may never clear staleness, because we cannot tell two `SYSTEM` processes apart |
| **`0003`** | *is this party entitled to retire that fact?* | the author ladder | capped authority (`min(author, derived_from)`) — correct, but it cannot distinguish **which** third party, so a third party can still retire *its own* earlier claim, or another's |

*(v2: the third motivation — evidence basis, "is this new observation or a restatement?" — is
SPLIT OUT to a successor spec (external-review R2). It had no v1 consumer, and its `observed` value
collides with `SourceType.OBSERVED`; it must wait for the `A1` `SourceType` deletion. `0006` v1 is
`source_id` only.)*

**Same class ≠ same source · same speaker ≠ fresh evidence · repetition ≠
renewed observation.**

**This is the third instance of one shape, which is the argument for fixing the
cause rather than each symptom:**

- **`0001`** — *speaker ≠ witness* (who said it vs who is described)
- **`0003`** — *disclosure ≠ entitlement* (may this be asserted vs who may
  retire it)
- **`0002` M3** — *class ≠ identity*

Each was found separately and each was patched separately. **Those are the ORIGIN of the finding
— but be precise about v1: after R3, none of them READS `source_id` in v1.** R3 made the ruling
diagnostic-only (`source_id` may GROUP, never GRANT — §0), so M3 stays fail-closed and Q3 (§10)
defers `0003`'s ladder to a later pure-code change; neither consumes the field in v1.

**The concrete v1 consumer is `0014` (maintenance attribution).** It keys its content-free
contribution ledger on the **`(origin, source_id)` pair** (`Spec-Requires: 0006`) — precisely
because this spec defines a **stable, revocable** source identity that is *already the revocation
key* (stable and revocable is all the ledger needs; the identity is NOT unforgeable — §3b/I2a). So v1
ships the identity as **diagnostic + a stable, revocable ledger key**; the trust consumers that
motivated it are **deferred** (M3 relaxation and the `0003` ladder both wait on provenance-of-the-
*call*, §0, on no roadmap). This spec earns its v1 `SCHEMA_VERSION` v4→v5 schema change (one `store_identity` singleton, minimal DDL) on `0014` — a §1→§3 reader
should not have to infer that.

**If we do nothing:** M3 stays permanently fail-closed — correct today, but it blocks same-source
reinforcement — `0003`'s ladder stays coarser than it needs to be, and **`0014` has no stable,
revocable key to attribute maintenance to**, so the attribution ledger cannot name a source and the
recurring maintenance-provenance-loss class stays open.

---

## 2. Field contracts touched

**`0006` v1 adds ONE identity, as a PAIR: `(origin, source_id)`.** (The `evidence_basis` field is
split out to a successor spec — external-review R2.) The two provenance fields live in the JSON
payload (no DDL for them); the durable local `origin` lives in ONE new singleton `store_identity`
row (minimal DDL — R8, §0b).

| field | change | contract |
|---|---|---|
| **`Provenance.source_id`** | **NEW**, optional | An opaque, stable identifier for *the source that produced this evidence* — a mailbox, a connector instance, a device, a named subsystem. Never a person's identity, never a display name. **Unique only WITHIN an `origin`** — on its own it is not an identity (R5). |
| **`Provenance.origin`** | **NEW**, optional, **STORE-minted** | An opaque, store-generated **collision namespace** (R7 — *not* an authenticated identity). A **local** caller and the model never supply it (I2a); on **import** a record keeps its foreign `origin`. Absent = *this store* → resolves to the `store_identity` singleton (§4). The identity is the **pair `(origin, source_id)`**; materialised on export. |
| **`store_identity` (singleton row)** | **NEW table, one row** | Holds this store's **persistent** `origin` (§4.2, R8) — minted once at creation / v4→v5 migration as a **canonical UUIDv4 generated by a CSPRNG (122 random bits), one canonical textual encoding** (freezes the collision-resistance claim rather than leaving strength to implementation taste; 122 not 128 — UUIDv4 fixes 6 version/variant bits); survives reopen/backup; the value an absent record-`origin` resolves to. The ONLY DDL this spec adds. |
| `Provenance.evidence_ref` | unchanged | Already identifies the *event*. `(origin, source_id)` identifies **who produces such events**; `evidence_ref` identifies **one**. |
| `SCHEMA_VERSION` | **v4 → v5, MINIMAL DDL** | Adds the `store_identity` singleton (R8); the provenance JSON gains `source_id`/`origin` (no column). No per-record change, no backfill. The bump also makes an older build (`extra=ignore`) REFUSE the store rather than silently drop the fields (§0b, `0007`). `0014`'s ledger table is v6. |
| `FORMAT_VERSION` | **3 → 4** | Export/import must round-trip `source_id` AND the materialised (resolved) `origin`. **`portability.py:37` is already `3`**, so this bumps **3 → 4**, not 2 → 3. (Distinct from `SCHEMA_VERSION` — two counters.) |

**The provenance fields are optional and absent means unknown** (`source_id` unknown → no grouping;
`origin` absent → this store, resolved to the singleton), which must behave as the **least**
favourable value — see I3. The `store_identity` singleton, by contrast, is always present.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant |
|---|---|---|---|---|---|
| **`source_id`** | absent → treated as unknown → **no grouping** | rejected | — | **the model names a `source_id` to impersonate a trusted source**, or reuses the user's | **I1 — host-supplied only; never model-supplied, never extractor-derived** |
| **`origin` (LOCAL ingest/API)** | absent → resolves to the `store_identity` singleton | rejected | — | **a local caller supplies an `origin` to impersonate another store** | **I2a — a LOCAL caller/model can NEVER supply `origin`; the resolver uses the singleton** |
| **`origin` (valid v4-format IMPORT)** | **REJECTED as malformed (I14)** — a `FORMAT_VERSION` ≥ 4 record MUST carry `origin`; a missing one is NEVER resolved to the local singleton (that resolution is for LOCAL stored rows only, not interchange) | rejected | — | attacker hand-writes a file naming `origin=A` — **NOT prevented here (R7): `origin` is namespacing, not authenticated**; `0005`'s untrusted-import boundary governs it | **I2b — a current-format import with `origin` PRESENT preserves the foreign value** (does NOT localise it); **I14 — a current-format import with `origin` ABSENT is rejected** (never acquires the destination origin by omission); trust of a *present* foreign origin is `0005`'s, not this spec's |
| **older-store data** | both absent | — | — | — | **I3 — absence never relaxes a rule.** Also the `PRAGMA user_version` gap, see Q1 |
| **pre-v4-FORMAT import carrying the fields (R10)** | — | — | **a hand-written file labels itself an OLD `FORMAT_VERSION` but adds `source_id` and omits `origin`** | if accepted with "absent origin = this store", the attacker's source becomes `(local_origin, attacker_source_id)` — **the exact local-namespace capture `origin` exists to prevent** | **I10 — a field newer than the envelope's declared `FORMAT_VERSION` is STRIPPED/ignored on import** (its source identity is unknown), not trusted. "Reject newer versions" does not cover new fields in an OLD envelope |
| **imported export (honest)** | — | version-checked | v4 file into a v3 build rejected | — | imported records KEEP their `origin` (I2b), so two **honest** exports' `(A,"mailbox:primary")` and `(B,"mailbox:primary")` cannot ACCIDENTALLY collide (R5). `0005`'s cap applies **first** |

## 2c-ii. Assertions about reach

| assertion | command | result |
|---|---|---|
| `author_of_evidence` is the only identity-ish field today | read `Provenance` in `schema.py:51` | class enum, no id |
| M3 compares class equality | `sed -n '119,121p' src/veracium/graph.py` | `==` on `author_of_evidence` |
| there is no schema version pragma | `grep -rn "user_version" src/veracium/` | none — carried from `0001` Q3 |
| `FORMAT_VERSION` is checked on import | `portability.py:69` | newer-than-ours rejected |

---

## 3. Trust-class matrix — REQUIRED, blocking

> **The affirmative invariant (R1, the reviewer's wording).** *In v1, `(origin, source_id)` affects
> **no** trust, authority, disclosure, staleness-clearing or supersession decision. It may only be
> **recorded, grouped and inspected.*** It is diagnostic. (R3 overturned the original mechanism —
> `source_id` may GROUP, never GRANT; the earlier "only permits a fail-closed rule to open" framing
> and I5's "gates one rule" were pre-R3 remnants and are removed.)

The matrix therefore has one column of answers, and every cell is the same — that is the point:
identity changes no decision in v1.

| prior edge | reinforcing evidence | today (`0002` §7b) | with `(origin, source_id)` | rationale |
|---|---|---|---|---|
| USER, source A | USER, **same** source (same `(origin, source_id)`) | flag stays | **flag stays** | a matching id is not a confirmation — a host may give unrelated statements one `source_id`; nothing may clear on it |
| USER, source A | USER, **different** source | flag stays | **flag stays** | a different source is not a confirmation |
| SYSTEM, source A | SYSTEM, **same** source | flag stays | **flag stays** | M3 refuses this and `source_id` does not remove the reason |
| SYSTEM, source A | SYSTEM, **different** source | flag stays | **flag stays** | *"two unrelated `SYSTEM` processes"* — the exact case |
| any | **`source_id` absent** on either side | flag stays | **flag stays** | I3 |

**Every cell reads "flag stays."** That is not a placeholder — it is the invariant above, tabulated:
the field is grouped and inspected, never consulted by a trust decision. (Historical note: v1 of
this spec had a *"only ever moves cells toward clears"* paragraph here; R3 falsified it — that
property was what made it unsafe. Removed.)

---

## 3b. Authorization and scope — *full specs only*

- **Does this cross a user/tenant/scope boundary?** `source_id` is scoped to a source; **`origin`
  scopes it to a STORE** — that is the whole point of the pair (R5). It crosses a boundary in exactly
  one place: **export/import.** Without `origin`, an imported source could be conflated with a local
  one (correctness failure under `0014`); with it, imported records keep their originating `origin`
  and cannot (§2c, I8).
- **Who may see the affected state?** No one new. `source_id`/`origin` are provenance metadata on the
  edge/episode they belong to, and inherit that record's tenant scope. They are **never surfaced to
  the model** (I5: they affect no recall/answer decision), so they add no read surface.
- **Scope change (sharing, revocation, group join/leave)?** Out of scope for v1 — `0006` records the
  identity; `revoke_source` (`A3`/`0004`) is what acts on it, and a revocation keyed on the PAIR
  cannot reach another `origin`'s records **among honest stores** — an adversarial import CAN forge a
  foreign `origin` (R7/`0005`, §8), so this is a property of honest exports, not a structural guarantee
  against a forging importer.
- **Does anything become visible to a principal who could not see it before?** No. A **LOCAL** host
  cannot set `origin` (I2a), so a local caller cannot name another store; a model cannot set
  `source_id` (I1). (An adversarial IMPORT FILE can name a foreign `origin` — that is `0005`'s trust
  boundary, not this rule; §8.)

---

## 4. Behaviour

**`source_id` is opaque and host-supplied.** veracium never parses it, never
infers it, never derives it from content, and the extractor never sees it.

> **The constraint, and it is the whole spec:** if `source_id` were
> model-supplied, two "sources" would be whatever the extractor decided to call
> them — **and we would have rebuilt the subject bug a third time**, after
> `0001` and `0003`.

This is the same rule as `derived_from` and as I7's `_AUTHOR`: **a trust-bearing
field must not be settable by the party whose trust it describes.** Here that
rule finally has a mechanism instead of an aspiration.

### The `(origin, source_id)` contract (R5)

`source_id` alone is not an identity — it is an identity *within an origin*. Without the origin,
`import_memory` (which remaps the user but preserves provenance) merges two unrelated **honest**
exports that both call themselves `"mailbox:primary"` into one; today that silently degrades
grouping, but under `0014` they collide in the attribution ledger and a future `revoke_source` would
revoke both. So:

1. **`origin` is a store-generated COLLISION NAMESPACE — not an authenticated identity (R7).** The
   store mints it once at creation; a **local** caller (ingest/API) and the model can never supply it
   (I2a). It prevents **accidental** collisions between honest exports. **It is NOT unforgeable:**
   `origin` is materialised into exports (§2, so not secret), and `0005` treats an export file as
   **untrusted input** — an attacker who has seen an export from store A can hand-write a file naming
   `origin=A`, and nothing here (no signature, MAC, or store certificate) lets the importer tell that
   from a genuine A record. **Authentication of foreign origins is explicitly out of scope for v1**
   (§8); this is collision-resistant *namespacing*, and adversarial imports are the `0005`
   import-trust boundary's concern, applied **first**.
2. **The local store's own origin is DURABLE, persistent state (R8).** It lives in a **singleton
   store-identity object** (a one-row `store_identity` table), minted once at store creation / at the
   v4→v5 migration as a **canonical UUIDv4 generated by a CSPRNG (122 random bits) with one canonical
   textual encoding** — the collision-resistance the design claims is thereby mechanically earned, not
   left to implementation taste (122 not 128: UUIDv4 fixes 6 version/variant bits) — and it survives
   close-reopen and backup-restore. This is
   the value that "absent `origin` = this store" resolves to — so it must exist before any resolution.
3. **Local records need not store `origin`** — absent resolves to the singleton (point 2). It is
   **materialised on export** so the file is self-describing (`FORMAT_VERSION` 3→4).
4. **On import, records KEEP their originating `origin`; they do NOT acquire the local one.** So
   `(A, "mailbox:primary")` and a local `(B, "mailbox:primary")` stay distinct — an **accidental**
   collision between honest exports cannot occur. (An *adversarial* forgery of `origin=B` is not
   prevented here — that is R7 / `0005`, not this rule.) **🔴 A current-format (`FORMAT_VERSION` ≥ 4)
   imported record MUST carry `origin` (reviewer F3).** A v4 record with `origin` absent is
   **malformed and REJECTED — it is NEVER resolved to the destination singleton.** Rule 6's
   "absent → this store" resolution is for **LOCAL stored rows only**; an interchange record may not be
   origin-absent. Otherwise a hand-written `FORMAT_VERSION`-4 file that simply omits `origin` would
   become `(local_origin, attacker_source_id)` — the exact local-namespace capture `origin` exists to
   prevent, and the *current-format* sibling of the old-envelope case I10 already closes. This
   constrains ingress **before** a record can enter the "absent means local" regime; it does NOT alter
   the frozen seven-point interface. New invariant **I14**.
5. **Comparison is EXACT equality on BOTH components, with NO normalisation** — normalising can merge
   genuinely distinct opaque ids (the same failure inverted). `source_id` is non-empty with a length
   bound; `origin` likewise.
6. **🔴 All comparison, grouping and digest operations act on the RESOLVED pair.** `origin` absent
   resolves to the singleton (point 2) **before any comparison, digest or export**; **no consumer
   may compare or digest a STORED pair directly** (the joint `0006`↔`0014` interface lock). Without
   this, points 3 and 5 contradict: a local source is `(absent, "mailbox:primary")` before export and
   `(local_origin, "mailbox:primary")` after a round-trip, and exact equality reads those as two
   sources when they are one — grouping would split on this spec's own round trip, `0014` would hold
   two ledger keys for one source, and **`revoke_source` given the materialised pair would MISS every
   local row that stored `origin` absent — a silent under-report, the precise failure `A3` exists to
   prevent.** Resolution is at **ONE chokepoint** (this project's recurring failure is a rule enforced
   in three places and missed in a fourth). See I9 (round-trip) and §5 (the trade).
7. **🔴 The identity digest has ONE canonical construction, shared by every consumer (reviewer F2).**
   "Digest the resolved pair" is not mechanically complete — `digest(origin ‖ source_id)` by bare
   concatenation lets `("ab","c")` and `("a","bc")` collide, and two independently-coded consumers can
   pick different framing (tuple vs JSON vs separator) and silently stop joining, defeating the whole
   point of the pair being a *shared* key. So the construction is frozen as a **single library
   primitive** `source_identity_digest(origin, source_id)` = `SHA-256(` `b"veracium.source-id.v1"`
   (domain separation) `‖ u32be(len(origin_bytes)) ‖ origin_bytes ‖ u32be(len(source_id_bytes)) ‖
   source_id_bytes` `)`, components UTF-8, lengths fixed-width big-endian (length-framing, so no two
   distinct pairs share an encoding). **`0014` and `revoke_source` MUST call this one primitive** — no
   consumer may hand-roll a framing. Deterministic and **unsalted**, therefore enumerable for
   predictable ids: claimed as **hygiene, never confidentiality** (I5 keeps it off every trust
   decision). New invariant **I12**.
8. **🔴 No `source_id` ⇒ no source identity ⇒ no digest (reviewer F1).** `source_id` is optional and
   absent means UNKNOWN (§2, "no grouping"). Because identity is the PAIR, an absent `source_id` has no
   groupable identity, so `source_identity_digest` is **defined only when `source_id` is present**.
   A consumer that stores the digest (e.g. `0014`'s `identity_digest`) MUST make its column
   **nullable** and write **NULL** for an unknown source — **never** a `(resolved_origin, NULL)`
   digest, which would collapse every unknown-source record in a store into one false pseudo-source,
   the exact grouping §2 forbids. `revoke_source` / a blast-radius join (§8, `0014` A9) matches only
   **complete** identities; an unknown-source contribution is *recorded* but is **not revocable by
   source** (its contributing EVENT may still be identifiable via `evidence_ref` where present). New
   invariant **I13**.

**Migration.** **Minimal DDL (R8, corrected from v2's "no DDL"):** the v4→v5 migration creates ONE
new singleton `store_identity` row with a random `origin` (point 2), transactionally. **No per-record
change and no backfill** — existing edge rows keep `origin` absent and resolve to the singleton
(point 6), so R3's clean migration story survives without the record rewrite that stamp-at-write
would force (§5). The `source_id`/`origin` provenance fields still live in the JSON payload; the
`SCHEMA_VERSION` v4→v5 bump also makes an older build refuse rather than silently drop them. Fields
optional, absent = unknown = least favourable.

---

## 5. Regime analysis — where does this behave differently?

- **Scale/density/duration:** `source_id`/`origin` are per-record fields read by exact equality; there
  is **no scale-dependent behaviour** (unlike the query-blind recall regime — this field is not on the
  retrieval-scoring path, I5). Store size, edge count and history length do not change it.
- **The one regime that matters is the EXPORT/IMPORT boundary between two stores** (R5): the collision
  the pair prevents only manifests when a record from origin A is imported into a store of origin B.
  A single-store test never reaches it. **The tests MUST reach it** — I8 (`test_imported_origin_is_
  preserved_not_localised`) is the regime-reaching check; without it this behaviour is untested.
  This is a **stable (on-by-default)** field, so that regime **blocks** — I8 is required, not optional.
- **Thresholds/caps:** none — `source_id`/`origin` interact with no budget, cap or recompile threshold.
- **Cold vs warm store:** identical — the field does not touch the wiki cache (diagnostic-only).
- **Where the local origin lives — THREE options (R8 named the third; §4.2/§4.6).**
  **(a) resolve-at-read from an in-memory value:** broken — reopening changes every local source's
  identity. **(b) stamp `origin` at write time** so absence never exists: structurally safest (no path
  can forget to resolve), but it forces a **backfill of every existing row** on migration, turning the
  clean version bump into a full data rewrite. **(c) persistent singleton `store_identity` +
  resolve-at-read** (CHOSEN): one durable store-level row minted once, existing records keep `origin`
  absent and resolve to it at a single chokepoint — **no per-record backfill**, and the migration adds
  only that one row (minimal DDL, §0b). The cost of (c) is that resolution must be centralised, which
  I9's round-trip test pins. v2 posed this as an (a)-vs-(b) choice and missed (c) — the reviewer (R8)
  supplied it; recorded here so the trade is visibly deliberate.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **I1** `source_id` is never set from model output | `test_source_id_is_not_reachable_from_the_extractor` — drive `ingest_event` with an extractor returning `source_id` in every triple; assert it is ignored | CI |
| **I2a** (R9) a LOCAL caller/model can NEVER supply `origin` — the resolver uses the `store_identity` singleton | `test_local_caller_cannot_supply_origin` — supply an `origin` through every LOCAL ingest/API path; assert the singleton's value is used, the caller's ignored | CI |
| **I2b** (R9) a valid current-format IMPORT PRESERVES the file's foreign `origin`, does NOT localise it | `test_imported_origin_is_preserved_not_localised` — import `(A,"mailbox:primary")` into a store of origin B; assert it stays `(A,…)` and does not group with local `(B,…)`. (I2a and I2b differ by PATH — v2 combined the two into one rule that contradicted itself, R9.) | CI |
| **I3** absence never relaxes a rule | `test_missing_source_id_keeps_the_flag` — over the §3 matrix, both-absent and one-absent | CI |
| **I4** the §3 matrix holds exactly — **every cell "flag stays"** | `test_staleness_clearing_matrix` — table-driven, all rows | CI |
| **I5** (affirmative, R1) `(origin, source_id)` affects **no** trust/authority/disclosure/staleness/supersession decision in v1 — it is only recorded, grouped, inspected | `test_source_id_affects_no_decision` — over the ladder, the gate, and staleness clearing, adding/changing `(origin, source_id)` changes no output | CI |
| **I6** export/import round-trips `source_id` AND the resolved `origin` | `test_v4_export_roundtrip` · `test_v4_file_into_v3_build_is_rejected` | CI |
| **I7** `0005`'s import cap applies before any of this | `test_imported_source_id_does_not_bypass_the_remap_cap` | CI |
| **I8** (R5, R7) two HONEST exports' equal `source_id`s under different origins do not ACCIDENTALLY collide — *accidental* only; an adversarial forged `origin` is out of scope (R7, §8) | `test_two_honest_origins_do_not_collide` | CI |
| **I9** a source's identity survives export→import into the SAME store (the interface-lock fix, §4.6) | `test_local_source_survives_a_round_trip` — write a record with `origin` absent; export; import into the **same** store; assert the two rows **group as one source** and **digest identically** | CI |
| **I10** (R10) a field newer than an import's declared `FORMAT_VERSION` is STRIPPED on import | `test_source_id_in_a_pre_v4_envelope_is_ignored` — hand-write a `FORMAT_VERSION`-3 file carrying `source_id`; assert it is ignored (identity unknown), NOT accepted as `(local_origin, source_id)` | CI |
| **I11** (R8) the local `store_identity` origin is durable | `test_store_origin_survives_reopen` — create a store, note its origin, close, reopen; assert the same origin resolves | CI |
| **I12** (F2) the identity digest is the ONE shared canonical primitive (§4 rule 7) — length-framed and domain-separated, and every consumer re-derives it identically | `test_source_identity_digest_is_canonical_and_shared` — assert `source_identity_digest("ab","c") != source_identity_digest("a","bc")` (no concatenation collision), and that `0014`'s ledger write and `revoke_source`'s lookup produce the SAME digest for one pair | CI |
| **I13** (F1) an absent `source_id` yields NO digest — never a `(resolved_origin, NULL)` pseudo-source; unknown-source records do not group and are not revocable-by-source (§4 rule 8) | `test_absent_source_id_produces_no_groupable_digest` — record two contributors with distinct evidence but no `source_id`; assert neither gets a digest, they do NOT group into one source, and a `revoke_source` on any pair matches neither | CI |
| **I14** (F3) a current-format imported record never acquires the destination `origin` by omission — a `FORMAT_VERSION` ≥ 4 record with `origin` absent is rejected as malformed (§4 rule 4), never resolved to the local singleton | `test_v4_import_missing_origin_is_rejected` — hand-write a `FORMAT_VERSION`-4 file with a record omitting `origin`; assert the import is REJECTED, and the record does NOT enter the store as `(local_origin, source_id)` | CI |

**I5 is the one to watch.** The temptation once identity exists is to let a
"known good" `source_id` raise trust. **It must not** — I5 makes that a tested
prohibition, not a hope. Capping-only is the rule that has survived every one of
these specs, and identity is not entitlement.

---

## 7. Failure modes and reversibility

- **Silent failure — the one the version bump exists to prevent.** An older build reading a v5 store
  `extra=ignore`s `source_id`/`origin` and silently drops them (R3). First symptom: a round-trip
  through an old build returns records that quietly lost their identity, undetectably. **The
  `SCHEMA_VERSION` v4→v5 bump makes it loud** — `0007` makes the old build REFUSE the store instead.
- **🔴 Losing the `store_identity` singleton (R8).** If the singleton is missing (a broken restore, a
  migration that failed to create it), every absent-`origin` record resolves against *nothing* —
  grouping and digests become undefined, and `0014`'s keys shift. First visible symptom: I9's
  round-trip test fails, or recall grouping fragments. **Mitigation: the v4→v5 migration creates the
  singleton transactionally (all-or-nothing), and store open FAILS CLOSED if a v5 store has no
  singleton** rather than silently minting a new one (which would re-identify every local source).
- **The R5 correctness failure, were the pair NOT adopted:** two HONEST origins' equal `source_id`s
  merge on import → collide in `0014`'s ledger → `revoke_source` revokes both. Prevented for honest
  exports by origin-preserving import (I2b). (Adversarial forgery is R7, below — not prevented here.)
- **Reversibility:** `source_id`/`origin` are additive metadata written once; nothing to reverse.
- **Partial failure:** the field write is part of the ordinary atomic edge/episode insert; the only
  new multi-step state is the migration's singleton creation, which is transactional (above).
- **New attack surface:** (a) a **model** setting `source_id` — blocked by I1; (b) a **local caller**
  setting `origin` — blocked by I2a; (c) **an attacker hand-writing an import that forges `origin=A`
  or slips `source_id` into an old envelope** — R7/I10: NOT authenticated here, governed by `0005`'s
  untrusted-import boundary (applied first). Content smuggled into `source_id` (F3) is diagnostic and
  never surfaced; content-free consumers digest the resolved pair (§8).

---

## 8. Claims and limits

**Claim:** distinct sources can be told apart — `(origin, source_id)` groups records by their
producing source without ever granting trust, and without two **honest** exports' sources
accidentally colliding.

**Limits:**

- **🔴 `origin` is collision-resistant NAMESPACING, not authenticated provenance (R7).** It is
  store-generated and prevents *accidental* collisions between honest exports. It is **NOT
  unforgeable**: `origin` is materialised into exports (not secret), and `0005` treats an import file
  as untrusted, so an attacker who has seen an export from store A can hand-write a file naming
  `origin=A` — nothing here (no signature, MAC or store certificate) distinguishes that from a genuine
  A record. **Authentication of foreign origins is explicitly OUT OF SCOPE for v1.** Consequently the
  strong reading — *"a revocation keyed on the pair is structurally incapable of reaching another
  store's records"* — holds only against **honest** exports, not an adversarial import; that boundary
  is `0005`'s. Making it authenticated (signed exports, or import re-namespacing foreign origins under
  a locally-controlled id) is a future option, recorded in §10.
- **`origin` is store-LINEAGE identity, not per-instance identity (🟠 reviewer).** Because the
  singleton `origin` deliberately survives backup/restore, two clones of one backup **share an
  `origin`** — they are effectively **one namespace**. If such clones are then operated
  independently and diverge in what a given `source_id` means, equal ids can collide (the same
  `(origin, source_id)` denoting two different sources). This is the honest consequence of durability:
  the identity is of the store's *lineage*, not of a running instance. A future **"fork this copy into
  a new independent store"** operation (re-mint the `origin` on divergence) is **out of scope for v1**,
  recorded in §10.

- **`source_id` is only as good as the host's discipline.** A host that reuses
  one id for everything gets today's behaviour with extra steps. We cannot
  detect that, and should not claim to.
- **It is not authentication.** Nothing verifies that a source is who the host
  says it is. It distinguishes sources from each other, not sources from
  impostors — and the host is already trusted for `author_of_evidence`, so this
  adds no new trust assumption, but it adds no verification either.
- **This does not close `0003`.** Identity sharpens the ladder's input; the
  ladder's own rules are that spec's business.
- **A deliberate host-declared MERGE of two origins is out of scope (R5).** The
  `(origin, source_id)` contract makes two origins' ids *structurally distinct* so an
  accidental import collision cannot occur. A host that genuinely wants to declare "these
  two origins are the same source" is a separate, explicit operation this spec does not
  provide — and must not be inferred from equal `source_id`s.
- **`source_id` "opaque" is a CONTRACT, not a mechanism (internal round, F3).**
  §2c/§4 call it opaque, but the store keeps it host-supplied and **stores it raw** —
  nothing prevents a host writing content into it (`"email:alice@…/subject:Divorce
  papers"`). §8's reuse limit and §2c's forgery rule do not cover *content*. This
  spec therefore does **not** guarantee `source_id` is content-free; it guarantees
  only that it is host-supplied and never model-set (I1). **A consumer that stores or
  keys on `(origin, source_id)` and needs a content-free surface MUST digest the pair** —
  and `0014`, which keys its content-free ledger on the pair, does exactly that (`0014`
  §2/§4: the pair is the join key, but the stored key is a digest of it — the same
  treatment `0014` gives `evidence_ref`). Hosts that need the raw value content-free
  should hash it before supplying it.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~**Q1**~~ | **RULED 0006-Q1 (research, 2026-08-02 00:08): yes — `0007` lands first.** Cheap precisely because R3 means `source_id` does **not** lift the staleness restriction, so nothing urgent queues behind it. `FORMAT_VERSION` guards exports; nothing guards an on-disk store opened by a different build. | resolved | research | — |
| ~~**Q2**~~ | **MOOT for `0006` v1 — `evidence_basis` is SPLIT OUT (external-review R2).** Q2 was the `evidence_basis` default; with the field deferred to a successor spec, the question moves with it. Research re-decided it on the real three-value enum (`proposals/0006-rulings-round2.md`, Ruling 1) — the three values are NOT a total order (`observed`/`restated` = directness; `derived` = mechanism), so "least favourable attested value" is undefined; **unknown is a fourth state, stored absent, the FLOOR: no decision treats it more favourably than ANY attested basis; constraints are defined per-decision by the spec that first consumes the field.** That ruling travels to the successor spec; `0006` v1 has no `evidence_basis`. | moved to the successor spec | research | — |
| ~~**Q3**~~ | **RESOLVED (dev ruled 2026-08-07, research CONFIRMED 2026-08-08; `proposals/0006-rulings-round2.md` §2a): KEEP `source_id` OUT of `0003`'s ladder in v1.** `0006`'s provenance fields need no per-record DDL (the only DDL is the `store_identity` singleton); `0003` later consuming the already-present fields is a pure CODE change (the ladder reads an existing field), **not a further schema change** — so "avoids a second migration" is void, there is no second migration either way. Keeping it out keeps `0006` small and diagnostic-only (§8). `0003` may consume it whenever `0003` rules to. | **resolved** | dev + research | — |

| **Q4** | **Authenticated foreign origins (R7) — a FUTURE option, deferred, not a v1 blocker.** v1 treats `origin` as collision-resistant namespacing, not authenticated provenance (§8), so the strong revocation-isolation reading holds only against honest exports. If a future consumer needs it to hold against adversarial imports, foreign origins must be authenticated — signed exports under a persistent store identity, OR import re-namespacing a foreign origin under a locally-controlled id. Recorded so the boundary is a deliberate v1 choice, revisitable when a consumer actually needs the stronger property. | deferred (future) | dev + research | when a consumer needs it |

**No open question BLOCKS v1** (Q1/Q2/Q3 resolved); Q4 is a recorded future direction, not a gate.

---

## Review closure (PROCESS.md §4a) — §11, the `0006` acceptance ledger

*Dev sets `Spec-Status: accepted` once the external review's comments are satisfied. This ledger
records every round, its findings, the disposition, and openable evidence. The round-by-round
source of truth is `specs/reviews.py`; each round's exact reviewed package (with a `sha256`) is in
`specs/archives/INDEX.md`; every invariant below has an executable check (§6).*

| round | date | disposition | findings | folded in | evidence |
|---|---|---|---|---|---|
| internal 1 | 2026-08-08 | review-ready held for 3 dev fixes | F1 §1 payoff · F2 `FORMAT_VERSION` stale · F3 `source_id` opacity | v2 | `proposals/0006-review-package.md`; archive `0006-v1-*` |
| external 1 | 2026-08-08 | return for amendment | R1–R6 (all verified, none rejected) | v2 | archive `0006-v2-*` (INDEX `sha256`) |
| external 2 | 2026-08-08 | return for amendment | R7–R11 (namespacing-not-auth; `store_identity` singleton; I2a/I2b split; pre-v4 stripping; interface-lock) | v3 | archive `0006-v3-*` |
| external 3 | 2026-08-09 | interface-freeze disposition (reviewer half withheld) | F1 (absent `source_id` ⇒ nullable digest, I13) · F2 (one shared canonical `source_identity_digest`, I12) · 2 cleanups (§3b honest-export; `0014` §4.5→§4.6) | v4 | commit `75bca5f`; archive `0006-v4-*`; interface point 4 re-ratified by research (`proposals/0006-0014-point4-reratification.md`) |
| external 4 | 2026-08-09 | interface freeze reviewer-**SIGNED**; acceptance held for F3 | F3 (v4-import absent-`origin` REJECTED, never localised — I14) + origin-generation/store-lineage tightening | v5 | commit `1c0880f`; archive `0006-v5-*`; `proposals/0006-0014-interface-freeze.md` |
| external 5 | 2026-08-09 | **acceptance PASS** — no further design round | C1 (superseded no-DDL wording) · C2 (UUID entropy 122 bits) · Review closure required | v6 `accepted` (this revision — commit `sha` in `specs/archives/INDEX.md` / the package README) | this section + §0b/§1/Q3/External-review-row edits + the C2 edits |

**Executable acceptance surface (§6, all CI):** I1 (`source_id` never model-set) · I2a/I2b (origin local-vs-import) · I3 (absence never relaxes) · I4 (the §3 matrix, all "flag stays") · I5 (never surfaced to the model) · I6 (v4 export round-trip) · I9 (local source survives round-trip — the interface-lock fix) · I10 (new field in an old envelope stripped) · I11 (durable `store_identity`) · **I12** (one shared canonical digest; no concat collision) · **I13** (absent `source_id` ⇒ no digest, no pseudo-source) · **I14** (current-format import with absent `origin` rejected). Every row of §3 and §2c is table-driven.

**Interface-freeze note.** The seven-point `0006`↔`0014` interface was frozen by both owners (dev + research) and reviewer-signed at round 4; that sign-off is **independent of, and earlier than, this `0006` acceptance** (round 5) and of `0014`'s own eventual acceptance. The two `0014` full-review carry-forwards (multi-generation A→B→C attribution touching frozen point 5; the tombstone direction) are `0014`'s to close and do not gate `0006`.

**Not re-reviewed by design.** Round 5's C1/C2/closure edits are mechanical closure, not a design amendment (the reviewer said so explicitly); they change no contract and needed no further external round.
