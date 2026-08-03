# Feature spec: source identity and evidence basis

Spec-Status: draft
Spec-Requires: 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft — §3 IS FALSIFIED AND MUST BE REWRITTEN.** Opened on research's R2
> ruling; **R3 (2026-08-01 23:17 UTC) overturns its central mechanism.** The §3 matrix
> below lets `source_id` **clear staleness**, and R3 rules that it must never
> grant anything. Left visible rather than silently edited — see §0.

## 0b. 📥 Migrations are owned by `specs/0013`

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

Each was found separately and each was patched separately. **Three consumers
justify the schema change that dissolves all three.**

**If we do nothing:** M3 stays permanently fail-closed — which is correct today
and blocks a real requirement, same-source reinforcement — and `0003`'s ladder
stays coarser than it needs to be.

---

## 2. Field contracts touched

| field | change | contract |
|---|---|---|
| **`Provenance.source_id`** | **NEW**, optional | An opaque, stable identifier for *the source that produced this evidence* — a mailbox, a connector instance, a device, a named subsystem. Never a person's identity, never a display name. |
| **`Provenance.evidence_basis`** | **NEW**, optional enum | `observed` (the source witnessed this) · `restated` (the source is repeating something it did not witness) · `derived` (produced by inference over other records). |
| `Provenance.evidence_ref` | unchanged | Already identifies the *event*. `source_id` identifies **who produces such events**; `evidence_ref` identifies **one**. Neither replaces the other. |
| `FORMAT_VERSION` | **2 → 3** | Export/import must round-trip both new fields. |

**Both fields are optional and absent means unknown**, which must behave as the
**least** favourable value — see I3.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant |
|---|---|---|---|---|---|
| **`source_id`** | absent → treated as unknown → **no relaxation** | rejected | — | **the model names a `source_id` to impersonate a trusted source**, or reuses the user's | **I1 — host-supplied only; never model-supplied, never extractor-derived** |
| **`evidence_basis`** | absent → `restated` (least favourable) | rejected | rejected | model declares `observed` to manufacture freshness | **I2 — host-supplied only; same rule as `source_id`** |
| **older-store data** | both absent | — | — | — | **I3 — absence never relaxes a rule.** Also the `PRAGMA user_version` gap, see Q1 |
| **imported export** | — | version-checked | v3 file into a v2 build rejected | trust fields hand-written | `0005`'s cap applies **first**; this adds no exemption |

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
| **I6** export/import round-trips both fields | `test_v3_export_roundtrip` · `test_v3_file_into_v2_build_is_rejected` | CI |
| **I7** `0005`'s import cap applies before any of this | `test_imported_source_id_does_not_bypass_the_remap_cap` | CI |

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

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~**Q1**~~ | **RULED 0006-Q1 (research, 2026-08-02 00:08): yes — `0007` lands first.** Cheap precisely because R3 means `source_id` does **not** lift the staleness restriction, so nothing urgent queues behind it. `FORMAT_VERSION` guards exports; nothing guards an on-disk store opened by a different build. | resolved | research | — |
| **Q2** | Should `evidence_basis` default to `restated` (least favourable, as specified) or be strictly required when `source_id` is present? Required is safer and is a harder ask of hosts. | `pre-release` | research | before implementation |
| **Q3** | Does `0003`'s ladder consume `source_id` in v1, or is that a follow-up? Keeping it out keeps this spec small; putting it in avoids a second migration. | `pre-release` | dev + research | before implementation |
