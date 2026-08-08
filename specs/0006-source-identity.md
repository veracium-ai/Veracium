# Feature spec: source identity — `(origin, source_id)`

Spec-Status: in review
Spec-Requires: 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v2, 2026-08-08) — RETURNED FROM EXTERNAL REVIEW for amendment** (6 findings,
> all verified, none rejected; `proposals/0006-external-review-response.md`). v2 amends per
> research's round-2 rulings (`proposals/0006-rulings-round2.md`). **Three shape changes:**
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
> one (v6).** All open questions resolved (Q1/Q2/Q3, §10). **🔴 Do not resend until the `0006`↔`0014`
> interface is locked jointly with research — the `source_id` requirement has moved twice (raw →
> digest → pair) — and the brief is corrected.**

## 0b. 📥 Migrations are owned by `specs/0013`

> **UPDATE 2026-08-07: the migration contract EXISTS and is implemented.** `0013` is `accepted`
> and its offline v→v+1 migration is in production (`0008`/`confirmations` was the first user;
> `0003` took the store to `SCHEMA_VERSION` 4). **But R3 (external review) corrected what the
> migration is FOR here: there is NO DDL.** The `edges` row is `(id, user_id, subject, relation,
> object, active, quarantined, json TEXT NOT NULL)` (`store/schema_version.py:125`) — the whole
> `Edge`, `Provenance` included, lives in the `json` blob. Adding a `Provenance.source_id` field
> changes the **JSON payload only** and requires **no `SchemaObject`, no column, no ALTER.**
> **What the version bump is genuinely for (measured, R3):** `Provenance` is a Pydantic model with
> `extra` defaulting to **`ignore`**, so an older build reading a newer store **silently DISCARDS**
> `source_id` rather than failing. The bump exists to make that silent drop LOUD: it is a **no-DDL
> `SCHEMA_VERSION` bump v4 → v5**, and `0007` (`PRAGMA user_version`, accepted+implemented) makes an
> older build REFUSE a v5 store rather than round-trip it lossily. **`0014`'s contribution-ledger
> table is therefore the NEXT version, v6** — the earlier `0006`-and-`0014`-both-claim-v5 conflict
> the reviewer flagged is resolved this way.

**`0006` changes the on-disk PAYLOAD (a new `Provenance` field in the `json` blob), NOT the DDL —
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
| **Version** | **v2** — *amended after external review returned it (6 findings). One field (`source_id`), a new `(origin, source_id)` identity contract, no-DDL version bump; `evidence_basis` split out. Archive as `0006-v2-<…>`.* |
| **Status** | *see `Spec-Status:` — canonical.* Opened from `0002` R2; **deliberately not folded into `0002`**, which is being split precisely because it kept absorbing work. |
| **Internal reviewers** | research — **ruled that this is needed and that it needs its own spec** |
| **External review** | required — touches stored provenance; a no-DDL `SCHEMA_VERSION` v4→v5 + `FORMAT_VERSION` 3→4 bump. **Round 1 returned for amendment (6 findings, all verified); v2 amends. Do not resend until the `0006`↔`0014` interface is locked jointly and the brief is corrected.** |
| **Decision + date** | — |
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
because this spec defines an unforgeable source identity that is *already the revocation key*. So v1
ships the identity as **diagnostic + a stable, revocable ledger key**; the trust consumers that
motivated it are **deferred** (M3 relaxation and the `0003` ladder both wait on provenance-of-the-
*call*, §0, on no roadmap). This spec earns its v1 no-DDL version bump on `0014` — a §1→§3 reader
should not have to infer that.

**If we do nothing:** M3 stays permanently fail-closed — correct today, but it blocks same-source
reinforcement — `0003`'s ladder stays coarser than it needs to be, and **`0014` has no unforgeable,
revocable key to attribute maintenance to**, so the attribution ledger cannot name a source and the
recurring maintenance-provenance-loss class stays open.

---

## 2. Field contracts touched

**`0006` v1 adds ONE identity, as a PAIR: `(origin, source_id)`.** (The `evidence_basis` field is
split out to a successor spec — external-review R2.) No DDL: both live in the `Provenance` JSON
payload; the version bump exists only to make an older build refuse rather than silently drop them
(§0b, R3).

| field | change | contract |
|---|---|---|
| **`Provenance.source_id`** | **NEW**, optional | An opaque, stable identifier for *the source that produced this evidence* — a mailbox, a connector instance, a device, a named subsystem. Never a person's identity, never a display name. **Unique only WITHIN an `origin`** — on its own it is not an identity (R5). |
| **`Provenance.origin`** | **NEW**, optional, **STORE-minted** | An opaque value minted by the store at creation — **never host-supplied** (a host cannot name another store's origin; same rule as every trust field: not settable by the party it describes). The identity is the **pair `(origin, source_id)`**. Absent origin means *this store*; it is **materialised on export** so the file is self-describing (§4). |
| `Provenance.evidence_ref` | unchanged | Already identifies the *event*. `(origin, source_id)` identifies **who produces such events**; `evidence_ref` identifies **one**. Neither replaces the other. |
| `SCHEMA_VERSION` | **v4 → v5, NO DDL** | The provenance JSON gains `source_id`/`origin`; no table/column changes. The bump makes an older build (which `extra=ignore`s the unknown fields) REFUSE the store rather than silently drop them (§0b, R3, `0007`). `0014`'s ledger table is v6. |
| `FORMAT_VERSION` | **3 → 4** | Export/import must round-trip `source_id` AND the materialised `origin`. **`portability.py:37` is already `3`**, so this bumps **3 → 4**, not 2 → 3. (Distinct from `SCHEMA_VERSION` above — two counters.) |

**Both fields are optional and absent means unknown** (`source_id` unknown → no grouping; `origin`
absent → this store), which must behave as the **least** favourable value — see I3.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant |
|---|---|---|---|---|---|
| **`source_id`** | absent → treated as unknown → **no grouping** | rejected | — | **the model names a `source_id` to impersonate a trusted source**, or reuses the user's | **I1 — host-supplied only; never model-supplied, never extractor-derived** |
| **`origin`** | absent → *this store* | rejected | — | **a host supplies an `origin` to impersonate another store** and merge into its records | **I2 — STORE-minted only; never host-supplied, never extractor-derived. A host-supplied `origin` is ignored/rejected** |
| **older-store data** | both absent | — | — | — | **I3 — absence never relaxes a rule.** Also the `PRAGMA user_version` gap, see Q1 |
| **imported export** | — | version-checked | v4 file into a v3 build rejected | trust fields hand-written | **imported records KEEP their originating `origin` — they do NOT acquire the local one**, so `(A,"mailbox:primary") ≠ (B,"mailbox:primary")` and two hosts' ids cannot collide (R5). `0005`'s cap applies **first**; this adds no exemption |

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
  identity; `revoke_source` (`A3`/`0004`) is what acts on it, and a revocation keyed on the PAIR is
  *structurally incapable* of reaching another `origin`'s records.
- **Does anything become visible to a principal who could not see it before?** No. A host cannot set
  `origin` (I2), so it cannot name another store; a model cannot set `source_id` (I1).

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
`import_memory` (which remaps the user but preserves provenance) merges two unrelated sources that
both call themselves `"mailbox:primary"` into one; today that silently degrades grouping, but under
`0014` they collide in the attribution ledger and a future `revoke_source` would revoke both —
**one host's revocation reaching another host's data, a correctness failure.** So:

1. **`origin` is minted by the STORE at creation, never supplied by the host.** A host cannot name
   another store's origin — that is what makes the pair unforgeable where `source_id` alone is not
   (the same rule that governs every other trust field here).
2. **Local records need not store `origin`** — absent means *this store*. It is **materialised on
   export** so the file is self-describing (`FORMAT_VERSION` 3→4).
3. **On import, records KEEP their originating `origin`; they do NOT acquire the local one.** So
   `(A, "mailbox:primary") ≠ (B, "mailbox:primary")`, and the collision cannot occur. `0005`'s
   import cap applies **first**.
4. **Comparison is EXACT equality on BOTH components, with NO normalisation** — normalising can merge
   genuinely distinct opaque ids (the same failure inverted). `source_id` is non-empty with a length
   bound; `origin` likewise.

**Migration.** No DDL (§0b) — both fields live in the JSON payload; the `SCHEMA_VERSION` v4→v5 bump
only makes an older build refuse rather than silently drop them. `source_id`/`origin` are optional,
absent = unknown = least favourable; no backfill — an existing store keeps today's fail-closed
behaviour until a host starts supplying identities, which is the correct default for data whose
source we genuinely do not know.

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

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **I1** `source_id` is never set from model output | `test_source_id_is_not_reachable_from_the_extractor` — drive `ingest_event` with an extractor returning `source_id` in every triple; assert it is ignored | CI |
| **I2** `origin` is **STORE-minted, never host-supplied** | `test_origin_is_not_host_settable` — supply an `origin` through every ingest/import path; assert the store's own value is used, the host's ignored | CI |
| **I3** absence never relaxes a rule | `test_missing_source_id_keeps_the_flag` — over the §3 matrix, both-absent and one-absent | CI |
| **I4** the §3 matrix holds exactly — **every cell "flag stays"** | `test_staleness_clearing_matrix` — table-driven, all rows | CI |
| **I5** (affirmative, R1) `(origin, source_id)` affects **no** trust/authority/disclosure/staleness/supersession decision in v1 — it is only recorded, grouped, inspected | `test_source_id_affects_no_decision` — over the ladder, the gate, and staleness clearing, adding/changing `(origin, source_id)` changes no output | CI |
| **I6** export/import round-trips `source_id` AND the materialised `origin` | `test_v4_export_roundtrip` · `test_v4_file_into_v3_build_is_rejected` | CI |
| **I7** `0005`'s import cap applies before any of this | `test_imported_source_id_does_not_bypass_the_remap_cap` | CI |
| **I8** (R5) an imported record KEEPS its origin — two origins' equal `source_id`s never collide | `test_imported_origin_is_preserved_not_localised` — import a record with `(A,"mailbox:primary")` into a store whose origin is B; assert it stays `(A,"mailbox:primary")` and does not group with a local `(B,"mailbox:primary")` | CI |

**I5 is the one to watch.** The temptation once identity exists is to let a
"known good" `source_id` raise trust. **It must not** — I5 makes that a tested
prohibition, not a hope. Capping-only is the rule that has survived every one of
these specs, and identity is not entitlement.

---

## 7. Failure modes and reversibility

- **Silent failure — the one this spec's version bump exists to prevent.** An older build reading a
  v5 store `extra=ignore`s `source_id`/`origin` and silently drops them (R3). First symptom: a
  round-trip through an old build returns records that have quietly lost their identity, undetectably.
  **The no-DDL `SCHEMA_VERSION` v4→v5 bump makes it loud** — `0007` makes the old build REFUSE the
  store instead. That is the whole justification for the bump (§0b).
- **The R5 correctness failure, were the pair NOT adopted:** two origins' equal `source_id`s merge on
  import → collide in `0014`'s ledger → `revoke_source` revokes both, one host's revocation reaching
  another's data. Prevented structurally by `(origin, source_id)` + origin-preserving import (I8).
- **Reversibility:** `source_id`/`origin` are additive, optional metadata written once at ingest;
  there is no destructive maintenance operation on them, so there is nothing to reverse. (Attributing
  and reversing the *consumption* of a source is `0014`/`A3`, not this spec.)
- **Partial failure:** none introduced — writing the field is part of the ordinary edge/episode
  insert, which is already atomic; there is no new multi-step operation.
- **New attack surface:** the two adversarial inputs are (a) a **model** setting `source_id` to
  impersonate a source — blocked by I1 (never model-reachable); (b) a **host** setting `origin` to
  impersonate another store — blocked by I2 (store-minted only). Content smuggled into `source_id`
  (F3) is diagnostic and never surfaced; content-free consumers digest the pair (§8).

---

## 8. Claims and limits

**Claim:** distinct sources can be told apart — `(origin, source_id)` groups records by their
producing source without ever granting trust, and without an imported source colliding with a local
one.

**Limits:**

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
| ~~**Q3**~~ | **RESOLVED (dev ruled 2026-08-07, research CONFIRMED 2026-08-08; `proposals/0006-rulings-round2.md` §2a): KEEP `source_id` OUT of `0003`'s ladder in v1.** `0006` is a no-DDL payload change; `0003` later consuming the field is a pure CODE change (the ladder reads an existing field), **not a schema change** — so "avoids a second migration" is void, there is no second migration either way. Keeping it out keeps `0006` small and diagnostic-only (§8). `0003` may consume it whenever `0003` rules to. | **resolved** | dev + research | — |

**No open questions remain.**
