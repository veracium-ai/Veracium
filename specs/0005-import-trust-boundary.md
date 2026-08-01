# Feature spec: import has no trust boundary

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — split out of `0002` on 2026-08-01. Finding and fix were both
> already verified there. **This one carries a queued trigger:** the
> cross-project-inheritance docs recipe stays held until this ships.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 |
| **Status** | *see `Spec-Status:` — canonical.* Split from `0002` §M6/§11a, unchanged in substance. |
| **Internal reviewers** | research — **found the defect**; dev verified it is CLI-reachable, not host-facing only |
| **External review** | required — `portability.py` is guarded and this changes what an import means |
| **Decision + date** | — |
| **Path** | full |

> **Why this is its own spec, and why it is the most urgent of the three splits.**
> The other two are defects in shipped behaviour. **This one is a defect that a
> queued documentation change would actively recruit users into** — a recipe
> telling people to seed a new project from a team memory export. Shipping the
> recipe before the boundary gives third-party content a *supported, documented*
> path to enter as first-person testimony.

---

## 1. Problem and motivation

**Found by research, verified here.** `portability.import_memory` does
`Edge.model_validate(rec)` then `store.add_edge(edge)`: **every trust-bearing
field reconstructed from a file** — `author_of_evidence`, `disclosure`,
`confidence`, `valid_from`, `derived_from` — with no re-derivation, no capping,
and a raw store write, so the ingest path's trust machinery never runs. Against
this spec's own lens it re-derives **all four**, from a file. Reproduced:

```
import_memory(bob_store, alices_export.jsonl, user_id="bob")
  → author=user  disclosure=mentionable  derived_from=None  assertable=True
```

**Alice's testimony is now Bob's own assertable fact.**

**In the restore case this is correct** — preserving provenance is the point.
Three things compound to make it otherwise: `user_id=` exists *to remap records
into a different user*, i.e. its purpose is crossing a principal boundary; a
docs recipe is already queued recommending exactly that ("seed a new project
from a team memory export"); and the demand it answers is for **shared/inherited
memory**, so the population most likely to follow it is the population importing
content they did not author.

**⚠️ Correction (research, verified here): this is NOT host-facing only. It is
a shipped CLI verb.** `cli.py:278` registers `import`, `cli.py:280` adds
`--user` (*"remap the records into this user id"*), `cli.py:149` passes it
through. **`veracium import alices_export.jsonl --user bob` is available to
anyone with the package installed.** Record it as **CLI-reachable,
operator-initiated** — the earlier phrasing is what gets re-checked if this is
ever revisited.

**And the mechanism is sharper than "fails to cap".** `author_of_evidence=USER`
is a claim **relative to the store owner**, and `--user` changes what it is
relative to. Nothing is falsified or mis-parsed: Alice's edge honestly says
*"authored by the user of this store"*, and re-homing it makes that sentence
mean Bob. **The re-attribution is a side effect of the remap, not a missing
check** — which is exactly why grepping provenance assignments could never have
found it, and why it reads as correct on inspection. It also relocates the fix:
**the cap belongs at the remap**, the only place the referent changes.

**The finding is not "import is broken."** It is that import has no trust
boundary, the API has a parameter whose purpose is to cross one, and a queued
doc would tell users to. **Ship the recipe before the boundary and third-party
content has a supported path to enter as first-party assertable fact — working
as designed, no bug, no advisory to write.**

**Rule (research's, adopted):** no `user_id=` (restore) → preserve provenance
unchanged. With `user_id=` (cross-principal) → third-party by construction: cap
to `use_only`, set `derived_from=THIRD_PARTY`, unless the caller explicitly
asserts otherwise. Costs nothing in restore, needs no new concept, makes the
convenient call the safe one. **⏳ Hold the cross-project-inheritance docs recipe
until this lands.**

---

## 2c. Untrusted inputs — REQUIRED, blocking

**The export file is the untrusted input**, and this is the first spec where
that is true of a *file* rather than a field.

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant |
|---|---|---|---|---|---|
| **export file body** | `ValueError` | `json.loads` raises | unknown `record` kind skipped | **every trust field is attacker-chosen** — `author_of_evidence`, `disclosure`, `confidence`, `derived_from` all reconstructed verbatim by `model_validate` | **P1** — the cap is applied after validation, so a hand-written file cannot evade it |
| **`user_id=` remap** | header's `user_id` used | — | — | **the boundary crossing itself** — its documented purpose | **P1** applies exactly when it differs from the header |
| **export header `user_id`** | treated as no-remap | — | — | **attacker sets it equal to the target** to suppress the cap | ⚠️ **P2 — see W-Q1**; the header is attacker-controlled and the cap keys on it |
| **format version** | — | rejected | newer version rejected | — | unchanged (`FORMAT_VERSION`) |

**The third row is a real gap in the fix as designed and I am recording it
rather than quietly closing it** — see `I-Q1`. The cap triggers on *header
`user_id` ≠ target*, and the header ships inside the file the attacker wrote.

## 2c-ii. Assertions about reach

| assertion | command | result |
|---|---|---|
| import is a shipped CLI verb | `grep -n "add_parser" src/veracium/cli.py` | `:278` `import`, `:280` `--user` |
| every trust field is reconstructed | read `portability.py:87` | `Edge.model_validate(rec)`, then a raw `store.add_edge` |
| the ingest trust path is skipped | `grep -n "_disclosure_for" src/veracium/` | `ingest.py` only — import never calls it |
| `disclosure` is set in exactly one place | `grep -rn "disclosure *=" --include=*.py src/veracium/` | `ingest.py:117` |

---

## 4. Behaviour

**Where.** `portability.import_memory`, at the point `user_id=` is applied
(`portability.py:85`, `rec["user_id"] = target_uid`). Not at `add_edge`, and not
in `Edge.model_validate` — **the remap is the only place the referent changes**,
which is the whole mechanism of the finding.

**The rule.**

> When `user_id=` is supplied **and differs from the export header's
> `user_id`**, every imported edge is capped: `derived_from = THIRD_PARTY`
> (already-capped edges keep their own value — `min`, never raised).

**Restore is untouched** — no `user_id=`, or the same one, imports byte-for-byte
with provenance preserved. That case is the reason `import` exists and
preserving provenance there is correct.

**Why cap rather than rewrite `author_of_evidence`.** The record is not false.
Alice's edge honestly says *"authored by the user of this store"*; re-homing it
changes what that sentence refers to. Overwriting the author to `THIRD_PARTY`
would **destroy a true statement to fix a referent problem**, and it would lose
the fact that this was somebody's first-person testimony — which a later
operator may need. Capping leaves the record intact and makes the *effective*
trust correct, which is exactly the 0.1.7 contract: **`derived_from` may cap,
never raise.** No new machinery, and no dependency on `specs/0003`.

**Consequence, stated plainly:** after a remapping import, nothing from the file
is assertable in the target store. **That is the intended outcome** — the
population this feature serves is importing content it did not author. A host
that wants an imported fact asserted has the same answer `confirm()` gives:
that affirmation is new user-authored evidence and belongs in `remember()`.

**Checks.** `test_remapping_import_caps_trust` (Alice→Bob: `assertable` False,
`derived_from` `THIRD_PARTY`) · `test_restore_preserves_provenance_exactly`
(round-trip with no remap is byte-identical) · `test_import_cap_never_raises`
(an edge already carrying `derived_from=THIRD_PARTY` and `author=THIRD_PARTY` is
unchanged).

---

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **P1** a remapping import caps every edge | `test_remapping_import_caps_trust` — Alice→Bob: `assertable` False, `derived_from` `THIRD_PARTY` | CI |
| **P2** restore is byte-identical | `test_restore_preserves_provenance_exactly` — round-trip with no remap | CI |
| **P3** the cap never raises | `test_import_cap_never_raises` — an edge already at `THIRD_PARTY` is unchanged | CI |
| **P4** the cap survives a hand-written file | `test_handwritten_export_cannot_evade_the_cap` — trust fields set adversarially in the file, cap still applied | CI |

---

## 8. Claims and limits

**Claim:** content imported into a *different* user's store cannot enter as that
user's own testimony.

**Limits, both worth stating:**

**(1) The cap is keyed on a field inside the file.** `I-Q1` below. Until that is
resolved the claim holds against *accident* — the actual reported scenario, an
operator running the documented recipe — and not against a *crafted* export.

**(2) Nothing imported through a remap is assertable, at all.** That is
intended, not a side effect: the population this feature serves is importing
content it did not author. A host that wants an imported fact asserted has the
same answer `confirm()` already gives — that affirmation is new user-authored
evidence and belongs in `remember()`.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| **I-Q1** | **The header `user_id` is attacker-controlled and the cap keys on it.** Setting it equal to the target suppresses the cap. Options: cap on *every* import and make restore opt in explicitly (`--restore`); or bind the header with the export signature if one is ever added. **Dev leans cap-by-default + explicit `--restore`** — it moves the decision from the file to the operator. | **blocking** | research | before implementation |
| **I-Q2** | Should the docs recipe ship at all once the cap lands, given imported facts are then non-assertable? The recipe's value may have depended on the defect. | `pre-release` | marketing + dev | before the recipe publishes |
