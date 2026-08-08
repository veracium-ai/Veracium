# Feature spec: source identity and evidence basis

Spec-Status: in review
Spec-Requires: 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (2026-08-08) — R3 APPLIED; diagnostic-only; ALL open questions resolved
> (Q2 RULED 2026-08-08); awaiting external review.** Opened on research's R2 ruling; **R3 (2026-08-01 23:17 UTC)
> overturned its central mechanism** — `source_id` may GROUP, never GRANT. The §3
> matrix now reflects R3 (every cell is *"flag stays"*; the falsified relaxation is
> struck through and left visible rather than silently edited — house style, see
> §0), and §4/§6/§8 are consistent with the diagnostic-only reading: `source_id`
> and `evidence_basis` answer *"did these come from the same place?"* and improve
> grouping/dedup/inspection; a lying host degrades grouping quality, it does not
> cross a trust boundary (I5). **Prerequisites `0007`+`0013` are now accepted AND
> implemented (§0b), so the added column lands through the accepted migration path.
> Q1 is resolved, Q3's dev half is ruled, and **Q2 is now RULED (research, 2026-08-08 —
> default `restated` as interpretation-only; storage stays absent; enforced by new I8).
> No open questions remain — this spec is now `in review`; the remaining step is external
> review (the reviewer-safe package is the deployment authority's to send).** (§10)

## 0b. 📥 Migrations are owned by `specs/0013`

> **UPDATE 2026-08-07: the migration contract now EXISTS and is implemented.**
> `0013` is `accepted` (2026-08-07) and its offline v→v+1 migration operation is
> in production (`0008` was its first user — the `confirmations` table). So the
> `source_id`/`evidence_basis` column this spec adds lands through the same
> accepted, tested migration path — a `SchemaObject` added to a new `SCHEMA_Vn`
> installed by `migrate_store`, not a naked `ALTER`. `0007` (`PRAGMA user_version`)
> is `accepted` + implemented, so an older build refuses a store carrying the new
> column instead of silently misreading it. **Both `Spec-Requires:` deps are met;
> this spec is unblocked on infrastructure, and the last design gate (Q2) is now
> ruled (§10) — review-ready.**

**`0006` changes the on-disk shape (it adds a column), so it cannot land without
a migration contract.** That contract is **`specs/0013`**, not this spec.

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

**What v2 of this spec must become:** `source_id` and `evidence_basis` are
**diagnostic** — they answer *did these come from the same place?* and improve
grouping, dedup and inspection. **A lying host degrades grouping quality
instead of crossing a trust boundary.** The thing that would actually unblock
staleness relaxation is **provenance of the call, not of the claim** — recording
which entry point was used and requiring hosts to gate the privileged ones. That
is evidence-basis's territory, not a staleness rule's, and it is on no roadmap.

---


| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 |
| **Status** | *see `Spec-Status:` — canonical.* Opened from `0002` R2; **deliberately not folded into `0002`**, which is being split precisely because it kept absorbing work. |
| **Internal reviewers** | research — **ruled that this is needed and that it needs its own spec** |
| **External review** | required — schema change, bumps `FORMAT_VERSION`, touches the store |
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
| **`0002` §7d / evidence basis** | *is this new observation, or a restatement?* | nothing | *"a trust-bearing field must not be settable by the party whose trust it describes"* is **aspirational** without a basis field |

**Same class ≠ same source · same speaker ≠ fresh evidence · repetition ≠
renewed observation.**

**This is the third instance of one shape, which is the argument for fixing the
cause rather than each symptom:**

- **`0001`** — *speaker ≠ witness* (who said it vs who is described)
- **`0003`** — *disclosure ≠ entitlement* (may this be asserted vs who may
  retire it)
- **`0002` M3** — *class ≠ identity*

Each was found separately and each was patched separately. **Those three are the
ORIGIN of the finding — but be precise about v1: after R3, none of them READS
`source_id` in v1.** R3 made the ruling diagnostic-only (`source_id` may GROUP,
never GRANT — §0), so M3 stays fail-closed, and Q3 (§10) defers `0003`'s ladder
to a later pure-code change; neither consumes the column in v1, and evidence-basis
is the separate `evidence_basis` field, not `source_id`.

**The concrete v1 consumer is `0014` (maintenance attribution).** It keys its
content-free contribution ledger on `source_id` (`Spec-Requires: 0006`) — precisely
because this spec defines an opaque, host-supplied identifier that is *already the
revocation key*. So v1 ships the identity as **diagnostic + a stable, revocable
ledger key**; the three trust consumers that motivated it are **deferred** (M3
relaxation and the `0003` ladder both wait on provenance-of-the-*call*, §0, which is
on no roadmap). This spec earns its schema change in v1 on `0014` — a §1→§3 reader
should not have to infer that.

**If we do nothing:** M3 stays permanently fail-closed — correct today, but it
blocks same-source reinforcement — `0003`'s ladder stays coarser than it needs to
be, and **`0014` has no opaque, revocable key to attribute maintenance to**, so the
attribution ledger cannot name a source and the recurring maintenance-provenance-loss
class stays open.

---

## 2. Field contracts touched

| field | change | contract |
|---|---|---|
| **`Provenance.source_id`** | **NEW**, optional | An opaque, stable identifier for *the source that produced this evidence* — a mailbox, a connector instance, a device, a named subsystem. Never a person's identity, never a display name. |
| **`Provenance.evidence_basis`** | **NEW**, optional enum | `observed` (the source witnessed this) · `restated` (the source is repeating something it did not witness) · `derived` (produced by inference over other records). |
| `Provenance.evidence_ref` | unchanged | Already identifies the *event*. `source_id` identifies **who produces such events**; `evidence_ref` identifies **one**. Neither replaces the other. |
| `FORMAT_VERSION` | **3 → 4** | Export/import must round-trip both new fields. **`portability.py:37` is already `3`** (a prior release bumped it), so this spec bumps **3 → 4**, not 2 → 3. (The store `SCHEMA_VERSION` is a separate counter — currently 4 — do not conflate.) |

**Both fields are optional and absent means unknown**, which must behave as the
**least** favourable value — see I3.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant |
|---|---|---|---|---|---|
| **`source_id`** | absent → treated as unknown → **no relaxation** | rejected | — | **the model names a `source_id` to impersonate a trusted source**, or reuses the user's | **I1 — host-supplied only; never model-supplied, never extractor-derived** |
| **`evidence_basis`** | absent → *interpreted as* `restated` (least favourable) but **stored absent, never materialised — I8** | rejected | rejected | model declares `observed` to manufacture freshness | **I2 — host-supplied only; same rule as `source_id`** |
| **older-store data** | both absent | — | — | — | **I3 — absence never relaxes a rule.** Also the `PRAGMA user_version` gap, see Q1 |
| **imported export** | — | version-checked | v4 file into a v3 build rejected | trust fields hand-written | `0005`'s cap applies **first**; this adds no exemption |

## 2c-ii. Assertions about reach

| assertion | command | result |
|---|---|---|
| `author_of_evidence` is the only identity-ish field today | read `Provenance` in `schema.py:51` | class enum, no id |
| M3 compares class equality | `sed -n '119,121p' src/veracium/graph.py` | `==` on `author_of_evidence` |
| there is no schema version pragma | `grep -rn "user_version" src/veracium/` | none — carried from `0001` Q3 |
| `FORMAT_VERSION` is checked on import | `portability.py:69` | newer-than-ours rejected |

---

## 3. Trust-class matrix — REQUIRED, blocking

**`source_id` grants nothing on its own. It only permits a rule that is
currently fail-closed to open, and only for an exact match.**

| prior edge | reinforcing evidence | today (`0002` §7b) | with `source_id` | rationale |
|---|---|---|---|---|
| USER, source A | USER, **source A**, `observed` | flag stays | ~~clears~~ **flag stays — R3** | ⚠️ **falsified.** A host may give unrelated statements one `source_id`; this would clear on evidence with no common source |
| USER, source A | USER, source **B**, `observed` | flag stays | **flag stays** | a different source is not a confirmation |
| USER, source A | USER, source A, **`restated`** | flag stays | **flag stays** | repetition is not renewed observation |
| SYSTEM, source A | SYSTEM, source A, `observed` | flag stays | ~~clears~~ **flag stays — R3** | ⚠️ **falsified.** M3 refused this for a reason that `source_id` does not remove |
| SYSTEM, source A | SYSTEM, source **B** | flag stays | **flag stays** | *"two unrelated `SYSTEM` processes"* — the exact case |
| any | **`source_id` absent** on either side | flag stays | **flag stays** | I3 |

⚠️ **This paragraph was the tell and I wrote it as reassurance.** *"Only ever moves cells toward `clears`"* is the property that made it unsafe, not the one that made it safe. **Under R3 no cell moves at all.** Original text: *the change only ever moves cells from "flag stays" to "clears", never the reverse* — it is a relaxation of a deliberately over-strict rule, gated on
evidence we do not currently have.

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

**Migration.** Both fields optional, absent = unknown = least favourable. No
backfill: an existing store keeps today's fail-closed behaviour until a host
starts supplying identities, which is the correct default for data whose source
we genuinely do not know.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **I1** `source_id` is never set from model output | `test_source_id_is_not_reachable_from_the_extractor` — drive `ingest_event` with an extractor returning `source_id` in every triple; assert it is ignored | CI |
| **I2** `evidence_basis` is never set from model output | `test_evidence_basis_is_not_model_settable` | CI |
| **I3** absence never relaxes a rule | `test_missing_source_id_keeps_the_flag` — over the §3 matrix, both-absent and one-absent | CI |
| **I4** the §3 matrix holds exactly | `test_staleness_clearing_matrix` — table-driven, all six rows | CI |
| **I5** `source_id` never widens disclosure or authority | `test_source_id_does_not_affect_disclosure_or_the_ladder` — it gates **one** rule and nothing else | CI |
| **I6** export/import round-trips both fields | `test_v4_export_roundtrip` · `test_v4_file_into_v3_build_is_rejected` | CI |
| **I7** `0005`'s import cap applies before any of this | `test_imported_source_id_does_not_bypass_the_remap_cap` | CI |
| **I8** the `restated` default is **never materialised** — absence is interpreted as `restated` at every decision point but stored ABSENT (research's Q2 ruling, 2026-08-08) | `test_absent_evidence_basis_stays_absent` — ingest with no `evidence_basis`, read the row back and assert it is **stored absent**; then assert the §3 matrix outcome is IDENTICAL to an explicitly-`restated` record. The second half is the point: it pins behavioural equivalence alongside representational distinctness, so a future "optimisation" cannot write the default in | CI |

**I5 is the one to watch.** The temptation once identity exists is to let a
"known good" `source_id` raise trust. **It must not.** Capping-only is the rule
that has survived every one of these specs, and identity is not entitlement.

---

## 8. Claims and limits

**Claim:** same-source reinforcement can be distinguished from same-class
repetition.

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
- **`absent` means unknown — it is NOT evidence that a source restated anything**
  (Q2 ruling). `restated` is only how absence is *interpreted* at a decision point;
  no downstream analysis (`introspect()`, an auditor, an importer, a future
  `revoke_source`) may count an absent row as a `restated` observation. The two are
  distinct facts — absence = nobody attested; `restated` = the host affirmatively
  attested repetition — and the store keeps them distinct (I8).
- **`source_id` "opaque" is a CONTRACT, not a mechanism (internal round, F3).**
  §2c/§4 call it opaque, but the store keeps it host-supplied and **stores it raw** —
  nothing prevents a host writing content into it (`"email:alice@…/subject:Divorce
  papers"`). §8's reuse limit and §2c's forgery rule do not cover *content*. This
  spec therefore does **not** guarantee `source_id` is content-free; it guarantees
  only that it is host-supplied and never model-set (I1). **A consumer that stores or
  keys on `source_id` and needs a content-free surface MUST digest it** — and
  `0014`, which keys its content-free ledger on `source_id`, does exactly that
  (`0014` §2/§4: `source_id` is the join key, but any surface that must be
  content-free digests it, the same treatment `0014` gives `evidence_ref`). Hosts
  that need the raw value content-free should hash it before supplying it.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~**Q1**~~ | **RULED 0006-Q1 (research, 2026-08-02 00:08): yes — `0007` lands first.** Cheap precisely because R3 means `source_id` does **not** lift the staleness restriction, so nothing urgent queues behind it. `FORMAT_VERSION` guards exports; nothing guards an on-disk store opened by a different build. | resolved | research | — |
| ~~**Q2**~~ | **RULED 0006-Q2 (research, 2026-08-08; `proposals/0006-Q2-ruling.md`): default `restated`, but as INTERPRETATION ONLY — the stored value stays ABSENT when the host supplies nothing; the default is never materialised into the row.** Dev's reasoning is adopted in full (fail-closed, the easier host ask, consistent with I3, and "required when `source_id` present" couples two independent fields + adds a rejection path). **The binding qualification neither option as posed stated:** `absent` and `restated` are DIFFERENT facts — absent = nobody attested anything; `restated` = the host affirmatively attested that this source repeats something it did not witness. Materialising the default destroys that distinction permanently (no later reader can tell an attestation from a fill-in) — **the `SourceType` failure one axis over (`A1`); we must not re-create it in the field contract meant to replace it.** Safety is fully preserved: absence already behaves as least-favourable under I3, and §3's matrix row is reached identically whether the value is absent or stored. And a host that names a `source_id` often genuinely cannot know the basis — requiring it manufactures a guessed `observed`, which is *worse* than absent because `observed` is the value that relaxes. **Enforced by new invariant I8 (§6).** | **resolved** | research | — |
| **Q3** | Does `0003`'s ladder consume `source_id` in v1, or is that a follow-up? Keeping it out keeps this spec small; putting it in avoids a second migration. **DEV RULING 2026-08-07 (dev half — research to confirm): KEEP IT OUT of v1.** The "avoids a second migration" argument is now void: `0006`'s migration adds the `source_id`/`evidence_basis` COLUMNS; `0003` later consuming them is a pure CODE change (the ladder reads an existing column), **not a schema change** — so there is no second migration either way. Keeping it out keeps `0006` small and diagnostic-only, consistent with §8 (*"this does not close `0003`; the ladder's own rules are that spec's business"*). `0006` ships the column; `0003` may consume it whenever `0003` rules to, with no migration. | dev half ruled; research to confirm | dev + research | before implementation |
