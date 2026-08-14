# Feature spec: import has no trust boundary

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft v4** — split out of `0002` on 2026-08-01 (v1); matured to the ruled
> design 2026-08-13 (v2/v3) and **re-verified line-by-line against the shipped
> import machinery**; v4 folds external round 1 (seven findings — the cap gains
> its third lever) (FORMAT 5: the 0009 whole-file preflight + atomic commit, the
> 0010 X17–X19 shapes, the 0006 origin gates, the 0014 indexed-output identity
> gates — none of which existed when v1 was written). **This spec carries a
> queued trigger:** the cross-project-inheritance docs recipe stays held until
> this ships (I-Q2 decides whether it ships at all).

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v4 — EXTERNAL ROUND 1 FOLDED (7 bin-(a) + 2 editorial, 2026-08-14, classified before fixing): **R1-1 (C+D)** the two-lever cap left `author_of_evidence=USER` standing under remap — stored provenance and `introspect().by_author` repeated a claim whose referent had changed; **the cap gains its third lever** (author set to `THIRD_PARTY` on every default import) and §4c's "cap rather than rewrite" argument is withdrawn on this spec's own §1 logic. **R1-2 (F)** `restore` is now a closed predicate — `type(restore) is bool` or refuse (P13). **R1-3 (D+G)** "byte-faithful restore" was false against the shipped canonicalization (`portability.py:353` historical-id remap; 0006 origin materialisation) — reviewer-executed; restore is redefined as bypassing ONLY the trust cap (P2 rewritten trust-field-exact, both export shapes × both destinations). **R1-4 (D+C)** the §2c raise contract vs §4c cap-before-validation contradiction — the exact five-step sequence is now pinned (validate THEN cap; P14). **R1-5 (C)** P10's refusal message recruited operators toward `--restore`; the warning text is now pinned and the mixed-file case is the regression (P15). **R1-6 (F+E)** the call-site inventory was wrong (measured: 50 AST sites / 7 files, not "56/8") and prose — replaced by a mechanical per-callsite disposition manifest obligation. **R1-7 (E)** P1–P12 were labelled CI while zero existed — every §6 check is now labelled a stage-5 obligation. *(v3 history: internal review passed; N1/N2 folded, N3 recorded. v2: I-Q1 folded; the v1 one-lever defect corrected.)* |
| **Status** | *see `Spec-Status:` — canonical.* |
| **Internal reviewers** | research — **found the defect**, ruled I-Q1, and PASSED the internal review 2026-08-13 (adversarial; N1/N2 folded same-commit in v3, N3 recorded in §7b) |
| **External review** | required — `portability.py`, `__init__.py` are guarded and this changes what an import means |
| **Decision + date** | — |
| **Path** | full |
| **Spec-Requires** | `0006` (accepted — this spec discharges 0006's I7 test obligation and amends the path of its I6/I9 round-trip checks, §7b) |

> **Why this is its own spec.** The other 0002 splits were defects in shipped
> behaviour. **This one is a defect that a queued documentation change would
> actively recruit users into** — a recipe telling people to seed a new project
> from a team memory export. Shipping the recipe before the boundary gives
> third-party content a *supported, documented* path to enter as first-person
> testimony.

---

## 1. Problem and motivation

**Found by research, verified here — and re-verified against the FORMAT-5
import path on 2026-08-13: the finding still holds unchanged.** The import
boundary has gained four generations of *integrity* gates since v1 (topology,
origin, claimed-inputs, indexed-output identity — §2c cites each), and **not
one trust gate**. `portability.import_memory` still does
`Edge.model_validate(rec)` / `Episode.model_validate(rec)`
(`portability.py:404-405`) and commits via the atomic plan: **every
trust-bearing field is reconstructed from the file** — `author_of_evidence`,
`disclosure`, `confidence`, `derived_from`, `valid_from`, `observed_at` — with
no re-derivation and no capping. The ingest path's trust machinery
(`_disclosure_for`, `ingest.py:191` — the only disclosure-derivation site in
the codebase) never runs. Reproduced on current `main`:

```
import_memory(bob_store, alices_export.jsonl, user_id="bob")
  → author=user  disclosure=mentionable  derived_from=None  assertable=True
```

**Alice's testimony is now Bob's own assertable fact.**

**In the restore case this is correct** — preserving provenance is the point.
Three things compound to make it otherwise: `user_id=` exists *to remap records
into a different user*, i.e. its purpose is crossing a principal boundary; a
docs recipe is queued recommending exactly that ("seed a new project from a
team memory export"); and the demand it answers is for **shared/inherited
memory**, so the population most likely to follow it is the population
importing content it did not author.

**This is CLI-reachable, operator-initiated** (research's correction, kept from
v1): `cli.py:315` registers `import`, `:317` adds `--user` (*"remap the records
into this user id"*). `veracium import alices_export.jsonl --user bob` is
available to anyone with the package installed. It is **not** exposed over MCP
(`mcp_server.py` registers no import tool — verified §2c-ii).

**The mechanism is sharper than "fails to cap"** (kept from v1, still exact):
`author_of_evidence=USER` is a claim **relative to the store owner**, and
remapping changes what it is relative to. Nothing is falsified or mis-parsed —
re-homing a true sentence changes its referent. And since v1 the same holds one
channel over: **the episode channel**. The gate routes episodes into the
GROUNDED block by `provenance.third_party_influenced` (`gate.py:87-90`,
`schema.py:134`), so an imported episode claiming `author=user,
derived_from=None` renders as the user's own narrative — the same
maintenance-time laundering shape as GHSA-hcj3-8jqc-wqrp, delivered by file.

**The finding is not "import is broken."** It is that import has no trust
boundary, the API has a parameter whose purpose is to cross one, and a queued
doc would tell users to. Ship the recipe before the boundary and third-party
content has a supported path to enter as first-party assertable fact — working
as designed, no bug, no advisory to write.

---

## 2. Field contracts touched

| field | read / written | documented contract | consumers | change here |
|---|---|---|---|---|
| `Provenance.derived_from` | ingest (`_disclosure_for` input); **written by the import cap** | "may cap, never raise" (0.1.7) | `_disclosure_for`, `third_party_influenced`, 0003's capped ladder (`min(author, derived_from)`) | **written at the import boundary: `THIRD_PARTY` unless already set (min, never raised)** |
| `Provenance.disclosure` | derived at ingest (`ingest.py:191`), stored; **floored by the import cap** | routes the gate: `assertable` / `use_only` / `quarantined` key on it (`schema.py:271-284`) | gate partition, proactive, render | **floored at the import boundary to `USE_ONLY` (`QUARANTINED` stays `QUARANTINED` — never raised)** |
| `Provenance.author_of_evidence` | read everywhere — including reporting surfaces (`introspect().by_author`, `introspect.py:56`) | "who authored the evidence" — **a claim relative to the store owner (§1)** | disclosure routing, ladder, **introspect reporting** | **written at the import boundary (R1-1): set to `THIRD_PARTY` on every default import** (already-`THIRD_PARTY` unchanged — the floor is the bottom rung, never a raise). §4c says why the v3 keep-the-author design was withdrawn |
| `Edge.confidence`, `valid_from`, `observed_at`, `needs_confirmation` | imported verbatim | honest history | staleness, rendering | **unchanged** — capped records render in the unverified block at their own confidence (the 0.4.1 per-block contract); §4e states why currency needs no extra rule |
| `import_memory(...)` return | host API + CLI + `_record("import", ...)` | counts dict | `__init__.py:1063`, `cli.py` | **gains `"capped": <int>`** (0 under restore) — **counted over the parsed file BEFORE the 0009 record-equality skip (N1/P11)**, so it is a pure function of (file, flags), never of destination state. §3b runs the oracle lens on it |

---

## 2c. Untrusted inputs — REQUIRED, blocking

**The export file is the untrusted input** — a file, not a field. Every gate
that already exists at this boundary is an *integrity* gate; the rows below
name which spec owns each, and the two ⚠ rows are the trust gap this spec
closes.

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| **file body: trust fields** (`author_of_evidence`, `disclosure`, `derived_from`, `confidence`, timestamps) | field absent → pydantic defaults — **⚠ `disclosure` defaults to `MENTIONABLE` (`schema.py:115`), so *omitting* the field is as strong as forging it** | pydantic raises at §4c-ii step 2 — **before the cap, so a malformed value is refused, never normalized into a valid capped one (R1-4/P14)** | — | **every trust field is attacker-chosen, on edges AND episodes** | **⚠ THIS SPEC — P1/P4/P7/P14: the cap applies to the validated records before every comparison gate and trust consumer (§4c-ii), so neither a forged nor an absent field evades it** |
| **`--user` / `user_id=` remap** | header's `user_id` used | — | — | the boundary crossing itself — its documented purpose | **P5/P6**: the cap no longer keys on the remap at all (§4b); remap additionally mints fresh ids (copy semantics, 0009 §4c) |
| **export header `user_id`** | refused (no target) | `json.loads` raises | — | **attacker sets it equal to the target** — v1's suppression vector | **de-fanged (§4b): the header decides only copy-vs-same-id mechanics, never trust.** Integrity against id collision is 0009 §4c record-equality (differ → refuse) |
| **`--restore` flag** | absent → cap applies | **non-bool API value → `TypeError` (P13)** | — | **an attacker-supplied file handed to an operator who runs `--restore`** — and the subtler form (R1-5): a refusal message that *directs* the operator there on a tampered own-export | **`--restore` is the operator's explicit trust assertion — the decision this design moves from the file to the operator — and the pinned §4d warning is what the operator decides on.** P5 keeps it from composing with `--user`; P15 keeps the tampered-export case as the regression |
| **format version** | header absent → refused | non-int → refused | **newer → refused**; fields newer than the declared version **stripped** | version chosen to smuggle newer fields | shipped: `FORMAT_VERSION` check + 0006 I10 strip (`portability.py:251-253, 322-323`) |
| **`origin` / `source_id`** | v4+: absent origin → **rejected** (0006 I14) | — | — | forged foreign origin — namespacing, not authenticated | 0006 I2b/I10/I14 (shipped); **trust of a present foreign origin is THIS spec's cap, applied first — 0006 I7, discharged here (P9)** |
| **outcome chains** (`kind="outcome"`) | — | non-dense/branched/cycled → refuse | — | crafted history grafting onto destination chains | 0009 §4c/H5/H13 (shipped): prefix-extend-or-refuse, whole-import atomic |
| **`claimed_by`** | — | — | — | orphan a fake in-flight consolidation | 0010 X18 (shipped): refused |
| **`lineage` / `consolidation_output_index`** | — | explicit null → refused; non-historical lineage ids → refused | pre-v5 envelope → stripped | fabricated store-assigned identity | 0014 §2c/§4c (shipped): identity-domain uniqueness, projection-equal-or-reject |
| **`supersedes` links into the destination** | — | — | — | craft an edge whose `supersedes` names an existing destination edge, hoping to retire it | **inert (verified §2c-ii): import inserts rows; it never calls `invalidate_edge`/`apply_supersession` — a supersedes link is stored lineage, and the destination edge's `active` flag is untouched.** P8 pins this |

## 2c-ii. Assertions about reach — every claim re-run on current `main` (2026-08-13)

| assertion | command | result |
|---|---|---|
| import is a shipped CLI verb with `--user` | `grep -n "add_parser" src/veracium/cli.py` | `:315` `import`, `:317` `--user` |
| import is NOT an MCP tool | `grep -n "import_memory\|def.*import" src/veracium/mcp_server.py` | no tool registration — host API + CLI only |
| every trust field is reconstructed from the file | read `portability.py:404-405` | `Edge.model_validate` / `Episode.model_validate`, then the atomic plan commit — no trust derivation between |
| the ingest trust path is skipped | `grep -rn "_disclosure_for" src/veracium/` | `ingest.py` only — import never calls it |
| `disclosure` is derived in exactly one place | `grep -rn "disclosure *=" --include=*.py src/veracium/` (excl. reads) | `ingest.py:191` |
| `assertable` keys on stored `disclosure`, NOT on `derived_from` | read `schema.py:271-284` | `use_only` ≡ `disclosure == USE_ONLY`; `assertable` ≡ active ∧ ¬quarantined ∧ ¬use_only — **this is why the cap must floor `disclosure` too (§4c)** |
| episodes route into the model by trust | read `gate.py:87-90`, `schema.py:134` | `third_party_influenced` ≡ author=3P ∨ derived_from=3P decides GROUNDED vs UNVERIFIED |
| import never mutates an existing row | read `portability.py:426-517` | preflight: equal → skip, differ → refuse, new → insert; `commit_outcome_import_plan` takes inserts + expected-state only |
| host API routes through the same function | `grep -n "def import_memory" src/veracium/__init__.py src/veracium/portability.py` | `__init__.py:1063` delegates to `portability.py:172` — **one enforcement point covers both entry paths** |

---

## 3. Trust-class matrix — REQUIRED, blocking

**No new trust class.** The file's records already carry the existing classes
(`USER` / `SYSTEM` / `THIRD_PARTY` authorship, `derived_from`), and the entire
design reuses the two shipped levers whose contracts already say the right
thing: `derived_from` *may cap, never raise* (0.1.7), and `disclosure` is the
gate's routing key. What changes is **who the classes are relative to**: at a
principal boundary, another store's `USER` is this store's `THIRD_PARTY` — by
construction, not by suspicion. The §2c matrix is the per-input enumeration;
no cell grants anything.

## 3b. Authorization and scope

- **Who can call it:** the host API (`Memory.import_memory`) and the CLI verb —
  both operator surfaces. Not reachable by the model: no MCP tool (§2c-ii).
- **What the return newly reveals (the 0015 §3b lens — information, not
  carrier):** the new `"capped"` count is a **function of the incoming file and
  the flags alone** — and that is true **by construction, not by accident**
  (the internal review's N1: the claim held only for pre-skip counting, so the
  counting point is now pinned): `capped` is counted over the parsed records
  BEFORE the 0009 record-equality skip, never over the committed plan. P11
  asserts it — the same file yields the identical `capped` into an empty and a
  pre-populated destination. It therefore reveals nothing about prior store
  state. (The pre-existing `"skipped"` count does reflect destination state;
  that is shipped v0 behaviour, unchanged here and reachable only by the
  operator who owns the store — which is also why the N1 defect's net exposure
  was nil in both counting designs; what was unsound was the §3b *argument*.)
- **`--restore` is an authorization act,** not a parser flag: it is the
  operator asserting "this file is my own store's history." §8 states the
  limit that creates.

---

## 4. Behaviour

### 4a. The rule

> **Every import caps** (`restore=False`, the default — including same-user
> imports and imports whose header matches the target):
> for **every** imported record, edge and episode alike, **three levers**:
> `author_of_evidence = THIRD_PARTY` (R1-1 — already-`THIRD_PARTY` values keep
> it; the floor is the bottom rung, never a raise),
> `derived_from = THIRD_PARTY` (already-`THIRD_PARTY` values keep it — min,
> never raised) **and** `disclosure` is floored to `USE_ONLY`
> (`QUARANTINED` stays `QUARANTINED` — flooring never *raises* a stricter
> value).
>
> **`restore=True` (CLI `--restore`) opts out of the cap — and of nothing
> else** (R1-3): every trust field is preserved exactly as the file states it,
> which is the reason `import` exists. The accepted canonicalization still
> applies — restore is *trust-field-faithful*, not byte-faithful (§4c-ii).
>
> **`restore` must be a `bool`** (R1-2): the API refuses `type(restore) is not
> bool` with `TypeError` **before the mutual-exclusion check and before the
> file is opened** — no truthiness coercion, so `restore="false"` and
> `restore=1` are refused, never interpreted. The CLI flag is `store_true` and
> can only produce a real bool.
>
> **`restore` and `user_id`/`--user` are mutually exclusive** — supplying both
> refuses before the file is opened (`ValueError` at the API; argparse
> mutual-exclusion at the CLI).

### 4b. Ruled — why the cap is unconditional (I-Q1, 2026-08-01)

Kept verbatim from the ruling record: research took ownership of the v1 hole —
their M6 ruling said *cap at the remap*, and the remap signal compares
`--user` against the export header, **a field inside the attacker's file**
(*"I reasoned about where the semantics change and not about who supplies the
evidence that they changed"*). The ruled correction: **cap on every import;
`--restore` opts out; `--restore` and `--user` mutually exclusive.**

**The mutual exclusion is the load-bearing clause.** Without it,
`--restore --user bob` is the original defect wearing the restore flag — the
only path by which `--restore` becomes the new suppression vector. **The
decision moves from the file to the operator**, the one party we have any
basis to trust. The header now decides only *mechanics* (whether ids are
minted fresh for a cross-user copy, 0009 §4c) — a wrong header cannot
suppress the cap, and id collisions are refused by record-equality regardless.

### 4c. The mechanism — three levers (v1→v3 corrections + R1-1)

v1 capped only `derived_from` and claimed `assertable` would go false. **That
was unimplementable as written**: `assertable` keys on the *stored*
`disclosure` field (`schema.py:271-284`), which the file supplies — or worse,
omits, inheriting the `MENTIONABLE` default (`schema.py:115`). A capped-`derived_from`
edge with file-chosen `disclosure=MENTIONABLE` would remain fully assertable;
v1's own named check would have failed. v3 capped **both trust carriers**;
round 1 (R1-1) found the third: the *authorship claim itself*. The mechanism
caps **all three carriers of the same fact**, coherently:

- **`author_of_evidence = THIRD_PARTY`** (R1-1) — the stored claim is made
  true *relative to the target store owner*. Drives `third_party_influenced`'s
  first disjunct, the ladder's `author` operand — and the **reporting
  surfaces**: `introspect().by_author` on the target now reports imported
  material as third-party, never as the owner's own testimony.
- **`derived_from = THIRD_PARTY`** — drives `third_party_influenced`
  (the **episode** channel, `gate.py:87-90`) and 0003's capped authority
  `min(author, derived_from)` (an imported "user" fact can never outrank the
  real user's).
- **`disclosure` floored to `USE_ONLY`** — drives `assertable`/`use_only`
  (the **edge** channel). Flooring is monotone: `MENTIONABLE → USE_ONLY`,
  `USE_ONLY → USE_ONLY`, `QUARANTINED → QUARANTINED`. This is exactly what
  `_disclosure_for(author, relation, THIRD_PARTY)` would derive, taken at its
  most restrictive with the stored value — stated as a floor so the
  quarantined case is visibly never weakened.

**The v3 "cap rather than rewrite" argument is WITHDRAWN (R1-1)** — refuted by
this spec's own §1 mechanism statement. §1: `author_of_evidence=USER` is a
claim **relative to the store owner**, and re-homing changes the referent.
v3 drew only the trust consequence and left the stored claim standing; but a
claim whose referent has changed is no longer true where it now lives, and
every reader repeats it — the internal review swept the *trust-granting*
consumers and missed that §2's own contract row says the field is **read
everywhere**, including `introspect().by_author`, which reported Alice's
testimony as `{"user": 1}` *to Bob*. `derived_from=THIRD_PARTY` cannot carry
this alone: it means "the user relayed third-party material," not "another
principal authored this" (the reviewer's exact formulation). The rewrite is
unconditional for the same I-Q1 reason as the other levers: any conditional
form keys on evidence the attacker supplies (a header set equal to the target
reaches the target's id with no `--user` at all — §2c row 3). What the rewrite
costs is stated in §8 limit 5: the fact that the material was *first-person in
its source store* survives in the source export and on the `--restore` path,
not in a default-capped copy — and 0006's `(origin, source_id)` still records
*which store* it came from, non-authoritatively.

### 4c-ii. The exact sequence (R1-4) — and what restore does and does not skip (R1-3)

The v3 phrase "before validation into models" is withdrawn: capping *raw
parsed dicts* would **normalize malformed values into valid capped ones**
(flooring reads the value; reading `disclosure="banana"` and writing
`USE_ONLY` erases the malformation), contradicting §2c's malformed→raise
contract. The pinned sequence, both paths:

1. **Parse** — `json.loads` per line; malformed JSON refuses the whole import.
2. **Validate into models** — `Edge.model_validate` / `Episode.model_validate`
   (`portability.py:404-405`): a **malformed** trust-field value raises (the
   §2c contract — whole-import refusal, store untouched); an **explicit
   `null`** on a non-nullable field raises the same way; an **omitted** field
   takes the model default (`disclosure=MENTIONABLE`, `schema.py:115`).
3. **THE CAP** (`restore=False` only) — the three levers applied to the
   validated in-memory models. The omitted-field default from step 2 is
   capped here like any explicit value (P4's omission cell).
4. **Integrity gates** — 0006 origin, 0014 identity/projection, 0009
   record-equality preflight, topology. All of them see only capped records:
   0006 I7's "applies first" holds *with respect to every trust consumer and
   every comparison gate* — nothing downstream of step 3 can smuggle an
   uncapped form.
5. **Atomic commit** (0009/0010 machinery, unchanged).

**Restore skips step 3 and nothing else** (R1-3 — reviewer-executed against
the shipped machinery). The accepted canonicalization applies on both paths
and is not this spec's to amend: export **materialises** the resolved origin
(0006 §4 rule 3 — a fresh destination stores the source UUID where the source
stored local-absent `None`); import **remaps finalized consolidation
operation ids into the historical namespace** (`portability.py:353`,
`to_historical_id` — accepted 0010 X18/0014); 0006 resolve-at-read makes the
materialised origin compare equal to a local-absent original. "Byte-faithful"
was therefore false as written; the restore contract is:

> **Restore is trust-field-faithful:** `author_of_evidence`, `disclosure`,
> `derived_from`, `confidence`, `valid_from`, `observed_at`,
> `needs_confirmation` are preserved exactly as the file states them.
> Canonical *identity* transforms (origin materialisation, historical-id
> remap) apply as on every import.

Consequences, stated honestly (P2 tests all four cells): a restore into a
**fresh** destination lands trust-fields-exact with canonicalized identity; a
restore of an export **back into its source store** record-equal-skips for
ordinary records (resolve-at-read equality) but **refuses** for finalized
consolidation outputs whose stored `operation_id` is still live — the incoming
record's `hist:`-remapped form differs from the stored row, and 0009
record-equality refuses the whole import. That refusal is shipped, accepted
0014 behaviour, observable **today, before this spec**; 0005 neither causes
nor amends it. Restore-then-restore into the *same non-source* destination is
idempotent (the remapped form is stable).

### 4d. Consequences, stated plainly

- **After a default import, nothing from the file is assertable and every
  imported episode renders in the UNVERIFIED block.** Intended: the population
  this serves is importing content it did not author. A host that wants an
  imported fact asserted has the answer `confirm()` gives — that affirmation
  is new user-authored evidence and belongs in `remember()`.
- **Re-importing your own export now refuses by default** (the stored originals
  differ from the capped incoming form → 0009 record-equality refuses the
  whole import) **with a pinned message (R1-5).** A bare pointer at `--restore`
  would recruit the operator into the bypass: a file cannot prove it deserves
  restore — the reviewer's regression is a legitimate own-store export with
  **one attacker-added edge**, where the capped forms of the legitimate rows
  cause the refusal and a naive "use `--restore`" remedy would admit the added
  edge uncapped. The refusal message is therefore pinned to carry both halves,
  and P10 asserts both:

  > *import refused: existing records differ from the capped incoming form.
  > If — and only if — this file is your own store's export, `--restore`
  > imports it with trust preserved. `--restore` trusts **every record in the
  > file** exactly as written; use it only on a file you exported yourself or
  > have independently verified, record by record.*

  First contact teaches the distinction; nothing is silently half-imported
  (the atomic plan guarantees that already). P15 keeps the mixed-file case as
  the standing regression.
- **Idempotency is preserved within each path:** default-then-default re-import
  skips (capped == capped); restore-then-restore of the same file into the same
  non-source destination skips (the canonical form is stable — §4c-ii; the
  same-SOURCE-store consolidation-output cell refuses instead, a shipped 0014
  refusal predating this spec). **Mixing paths for the
  same records refuses** — an honest fail-closed outcome, recorded as a limit
  (§8), including for 0014's indexed-output projection (capped vs uncapped
  provenance is a projected difference → rejected, never merged).
- **Imported outcome chains still count as judgment history** on their (capped,
  non-assertable) edges — derived counters do not filter by trust. Another
  principal's judgments arrive as history about a fact this store will not
  assert; that is coherent, and `--restore` exists for the case where they are
  genuinely yours.

### 4e. N9t's currency half needs no new rule — structural, with a check

The N9t finding feared imports could "claim new currency." Two shipped facts
close it without a currency-specific mechanism, and P8 pins them: **import
never mutates an existing row** (preflight: equal-skip / differ-refuse /
new-insert — there is no update path), so no existing edge's
`observed_at`/staleness/confidence can move; and **import never runs the
reinforcement or supersession machinery** (no `apply_supersession`, no planner
— §2c's inert-supersedes row), so imported records cannot renew, retire, or
reinforce anything (0012's Design 1 closed the reinforcement-laundering half
at the ingest path). An imported record's own timestamps are honest history
about *itself*, rendered — post-cap — only ever as unverified material.

---

## 5. Regime analysis

| regime | behaviour |
|---|---|
| default, fresh target user | all records land capped; counts `{edges, episodes, skipped=0, capped=N}` |
| default, re-import of a default import | capped == capped → record-equal skip; `capped` reports the SAME value as the first import (pre-skip counting, P11 — the skip never deflates it) |
| default, target holds uncapped originals (own store round-trip) | **refuse whole import**; message names `--restore` |
| `--restore`, no `user_id` | trust-field-faithful (§4c-ii); `capped=0`; canonical identity transforms still apply; same-source round-trip: ordinary records skip, live-op consolidation outputs refuse (shipped 0014 behaviour); 0006 I6/I9 round-trip properties live here (§7b) |
| `restore=<non-bool>` (any value, any other args) | **refused with `TypeError` before anything else runs** — no truthiness; P13 |
| `--restore` + `--user` (any values) | **refused before the file is opened** — P5 |
| default + `--user` (cross-principal copy) | fresh ids minted (0009 §4c), every record capped — the original reported scenario, now safe by default |
| any path, integrity-gate failure (topology / origin / identity / claimed) | shipped refusals unchanged, and they all fire on **capped** records — the cap runs first |

---

## 6. Invariants and executable checks — REQUIRED, blocking

**Status of every check below (R1-7): STAGE-5 OBLIGATION — none of these tests
exists yet.** This spec is `draft`; the shipped suite validates the shipped
product, and a spec-proposed boundary has no CI presence until its
implementation commit. v3 labelled this column "CI", which claimed twelve
tests with zero matches under `tests/` — the self-certification failure this
repo has already catalogued (0015 R8-4). Every name below becomes a CI check
**in the implementation commit**, and the acceptance ledger holds the
implementation to exactly this list; until then, "obligation" is the honest
status. (§7b's P9 row already said this about 0006 I7 — the rule is now
applied to the whole table.)

| invariant | executable check | status |
|---|---|---|
| **P1** a default import caps every record — edges AND episodes — **and the target's reporting surfaces attribute none of it to the owner (R1-1)** | `test_default_import_caps_every_record` — Alice→Bob: every edge `assertable` False + `author_of_evidence` `THIRD_PARTY` + `derived_from` `THIRD_PARTY`; every episode `third_party_influenced` True; `introspect("bob").by_author` counts **zero** `user`/`system` among imported records | obligation — impl commit |
| **P2** restore is trust-field-faithful (R1-3) | `test_restore_preserves_trust_fields_exactly` — the seven §4c-ii trust fields equal file values, tested over the **four-cell matrix**: {ordinary export, finalized-consolidation-output export} × {fresh destination, same-store}; fresh cells assert canonical identity transforms applied (`hist:` remap, materialised origin); same-store: ordinary skips, live-op output refuses (the shipped 0014 refusal, asserted as such) | obligation — impl commit |
| **P3** the cap never raises | `test_import_cap_never_raises` — records already at `THIRD_PARTY`/`THIRD_PARTY`/`USE_ONLY` or `QUARANTINED` are unchanged by the cap (all three levers) | obligation — impl commit |
| **P4** a hand-written file cannot evade the cap — **including by omission** | `test_handwritten_export_cannot_evade_the_cap` — trust fields set adversarially AND omitted entirely (the `MENTIONABLE`-default cell); post-import nothing assertable, nothing owner-attributed | obligation — impl commit |
| **P5** `restore` and `user_id` are mutually exclusive | `test_restore_with_remap_is_refused` — API `ValueError` before the file is read; CLI exits non-zero on `--restore --user` | obligation — impl commit |
| **P6** the cap is unconditional without restore | `test_every_import_caps_by_default` — same-`user_id` import and a crafted header equal to the target both cap (all three levers) | obligation — impl commit |
| **P7** the episode channel is closed | `test_imported_episode_renders_unverified` — a default-imported `author=user` episode appears in the gate's UNVERIFIED partition, never GROUNDED | obligation — impl commit |
| **P8** import mutates nothing existing (N9t currency) | `test_import_never_mutates_existing_rows` — snapshot every destination row; run default import (success), refused import, and a crafted supersedes-into-destination import; assert byte-identical destination rows and unchanged `active` flags in all three | obligation — impl commit |
| **P9** source-identity fields do not bypass the cap — **0006 I7, discharged** | `test_imported_source_id_does_not_bypass_the_remap_cap` (0006's named test, written here) — a v5 file with foreign `(origin, source_id)`: records cap normally; grouping/digest run on capped records only | obligation — impl commit |
| **P10** the refusal carries the pinned warning, not a bare remedy (R1-5) | `test_own_store_reimport_refusal_names_restore` — the refusal message contains `--restore` AND the pinned §4d warning ("trusts every record", "exported yourself or have independently verified") | obligation — impl commit |
| **P11** `capped` is destination-blind (N1) | `test_capped_count_is_destination_blind` — the same file imported into an EMPTY store and into a PRE-POPULATED store yields the identical `capped`; the count is taken pre-skip, over the parsed file | obligation — impl commit |
| **P12** imported corroboration cannot promote (N2) | `test_imported_outcomes_cannot_promote_a_capped_edge` — a default import carrying a capped edge plus N fabricated `kind="outcome"` judgments on it: the edge stays non-assertable and outside the grounded block; only ordering within the unverified block may move | obligation — impl commit |
| **P13** `restore` is a closed predicate (R1-2) | `test_restore_rejects_non_bool_values` — `restore="false"`, `restore=1`, `restore=0`, `restore=None`, `restore=[]`, `restore=object()` each raise `TypeError` before the file is opened (a nonexistent path proves nothing was read); `restore=True`/`False` behave per §4a | obligation — impl commit |
| **P14** the validate-then-cap sequence is exact (R1-4) | `test_malformed_trust_fields_raise_never_normalize` — three separate cells: a **malformed** `disclosure` value refuses the whole import with the store untouched (never silently normalized into a valid capped value); an **explicit null** on a non-nullable trust field refuses identically; an **omitted** field takes the model default and is then capped (P4's cell, asserted at the sequence level) | obligation — impl commit |
| **P15** the mixed-file case stays refused and the operator warned (R1-5) | `test_tampered_own_export_refuses_with_warning` — a legitimate own-store export plus ONE attacker-added new edge: default import refuses whole (the legitimate rows' capped forms differ), the message is the pinned §4d text; the test documents that `--restore` on this file WOULD admit the added edge — the warning is the designed mitigation | obligation — impl commit |

---

## 7. Failure modes and reversibility

**Failure modes.** Every refusal in §5 is whole-import and pre-commit (the
0009 atomic plan) — a refused or half-validated import leaves the store
byte-identical (P8 asserts this for the refusal paths too). The cap itself
cannot partially apply: it is a pure transformation of the parsed in-memory
records, upstream of every persistence step.

**Reversibility.** The behaviour change is API-visible but not schema-visible:
**no schema change, no format change, no migration** (`FORMAT_VERSION` stays
5 — the file format is untouched; what changes is what importing one *means*).
Records imported under the default cap are ordinary rows; an operator who
capped by mistake re-imports with `--restore` into a fresh user (or restores a
backup) — nothing is destroyed, because the cap never touched the file.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `portability.import_memory(store, path, *, user_id=None)` (`portability.py:172`) | gains `restore: bool = False`; **checks in order: `type(restore) is bool` (`TypeError`, P13) → mutual exclusion (`ValueError`, P5) → open file**; the cap at §4c-ii step 3; return gains `"capped"` |
| `Memory.import_memory(self, path, *, user_id=None)` (`__init__.py:1063`) | mirrors the signature; docstring trust note rewritten (see docs row) |
| **local audit carrier** — `Memory.import_memory` → `_record("import", {...})` (`__init__.py:1070-1071`) | **specified (round-1 editorial): the audit payload keeps exactly its shipped field set `{edges, episodes, skipped}` — `capped` is deliberately NOT forwarded** (the return carries it to the operator; adding an audit/telemetry field is 0015-regime consent work this spec does not do). The impl commit adds a test asserting the audit payload's field set is unchanged by a capping import |
| CLI `import` (`cli.py:315-317`) | gains `--restore` in a mutually-exclusive group with `--user`; help text carries the one-line rule |
| `portability` module docstring | **currently states the pre-0005 world as policy** ("Importing a file grants its records whatever authorship and disclosure they claim — import only from sources you trust exactly as much as the database file itself") — becomes: that sentence is true **only under `--restore`**; the default import caps |
| `docs/api.md` import section + `docs/recipes.md` | updated to the rule; the cross-project recipe is I-Q2's decision |
| telemetry | **no change** — `_record("import", ...)` keeps its existing count fields; no new whitelisted field (0015's consent regime not touched) |
| MCP | **no change** — import is not a tool; the §3b lens found no new oracle in the return |
| CHANGELOG | behaviour-change entry: *default* imports now cap; `--restore` restores the old semantics; upgrade note for hosts that script imports |

### 7b. Cross-spec carriers (the accepted contracts this touches)

| accepted spec | touchpoint | disposition |
|---|---|---|
| **0006 I7** | "0005's import cap applies before any of this" — its named test `test_imported_source_id_does_not_bypass_the_remap_cap` **does not exist yet** (verified: zero matches in `tests/`); it was an obligation contingent on this spec | **discharged here as P9** — written with this spec's implementation, same commit |
| **0006 I9 / I6** | `test_local_source_survives_a_roundtrip_into_the_same_store` (`tests/test_0006_source_identity.py:283`) and the I6 round-trip check import into the same store **on the default path**, which now refuses | the I9/I6 *properties* are unchanged and live on the restore path — **the tests move to `restore=True` in the same commit as the implementation**, with a marked note in each citing this spec (the 0014 §7b same-commit rule) |
| **0009 §4c / 0010 X17-X19 / 0014 §2c** | machinery referenced, not amended — the cap runs strictly before all of them (§4c-ii step 4), and restore preserves their identity transforms untouched | their import-path test fixtures that round-trip same-store on the default path are updated to `restore=True` where they test *integrity* semantics; fixtures that test *trust* keep the default path. **Measured inventory (R1-6 — the v3 prose count was wrong): 50 `import_memory` call sites by AST across 7 test files (56 textual hits, same 7 files; v3 said "56 across 8" — a textual count with a miscounted file list). The prose inventory is replaced by a MECHANICAL obligation: the implementation commit adds a per-callsite disposition manifest test that AST-enumerates every `import_memory` call under `tests/` and asserts each site carries a recorded disposition (`stays-default-trust` / `relocated-restore` / `refusal-fixture`) — a new, unmapped site fails the manifest.** **Negative fixtures must assert their ORIGINAL refusal reason** (topology / origin / identity / claimed), not merely "refuses" — otherwise the new default-cap refusal makes them pass vacuously while testing nothing. The internal review's N3 flag stands, now mechanized: completeness is the manifest's job, not a checklist's |
| **0012** | reinforcement laundering closed at ingest — §4e leans on it | referenced only; no amendment |

---

## 8. Claims and limits

**Claim:** content imported without an explicit `--restore` cannot enter as
the target user's own testimony — not through the edge channel (nothing
assertable), not through the episode channel (nothing grounded) — regardless
of what the file claims, omits, or sets its header to. The v1 limit
("holds against accident, not craft") is **retired**: the cap no longer keys
on anything the attacker writes.

**Limits, stated plainly:**

1. **`--restore` is trust by operator assertion — and the design itself
   points operators at it (R1-5).** An operator who runs `--restore` on a file
   they did not export has asserted something false, and the import behaves
   accordingly — the exact scope of the ruling: the decision moved *to the
   operator*, not eliminated. Because the default-path refusal *names*
   `--restore` (§4d), the message is part of the trust boundary: it carries
   the pinned warning that restore trusts every record exactly as written and
   belongs only on files the operator exported or independently verified. A
   file cannot prove it deserves restore; P15's tampered-own-export case is
   the standing regression for what the warning protects against. The CLI
   help and docs carry the same sentence.
2. **Mixed-path imports of the same records refuse** (§4d) — including 0014's
   indexed-output projection treating capped-vs-uncapped provenance as a real
   difference. Fail-closed and loud, never merged; an operator hitting it is
   holding one file in two trust postures.
3. **Capped records still exist**: they occupy the unverified block, carry
   their own confidence, and count in outcome-chain history. The boundary
   controls *assertion*, not *presence* — presence is what import is for.
   **And presence cannot buy promotion (N2):** an attacker who imports a
   capped edge plus fabricated `kind="outcome"` judgments inflates its
   corroboration history, but assertability and grounded-block membership key
   on the two capped levers, never on outcome counts — inflated history is
   inert to promotion (it can at most reorder material *within* the
   unverified block). This is the trust × proof-count separation, one level
   up; P12 pins it.
4. **The cap does not authenticate `origin`** — 0006 R7's boundary stands;
   forged namespacing remains namespacing. This spec makes it *harmless*
   (grouping runs on capped records, P9), not *honest*.
5. **The author rewrite loses source-side first-person-ness in the capped
   copy (R1-1).** A default-imported record no longer states that it was
   somebody's first-person testimony in its source store — that fact survives
   in the source export itself and on the `--restore` path, and 0006's
   `(origin, source_id)` still records *which store* the material came from
   (non-authoritatively). The v3 design kept the claim in place to preserve
   it, and that preserved a false statement instead (§4c); target-relative
   honesty outranks provenance archaeology in a store whose reporting
   surfaces repeat what is stored.

---

## 9. Brief for the external reviewer

The finding, the ruling, and the mechanism are §§1, 4b, 4c; the fastest
adversarial entry points are: (a) §4c — try to construct a record shape whose
effective trust survives the two-lever cap (the v1 one-lever design died
exactly there); (b) the §5 regime table — try to reach a cell where a
non-restore import leaves anything assertable or grounded; (c) §7b — check the
accepted-spec touchpoints are complete (the 0006 I9 test relocation is the
kind of same-commit carrier this repo has repeatedly gotten wrong); (d) the §2c
`disclosure`-default cell — absence-as-forgery is the newest input class.
Every reach claim in §2c-ii was re-run on 2026-08-13; the commands are
reproducible as written.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~I-Q1~~ | **RULED 2026-08-01: cap on every import; `--restore` opts out; `--restore` and `--user` are mutually exclusive.** §4b (`proposals/S-I-H-Q1-rulings.md`). | resolved | research | — |
| **I-Q2** | Should the docs recipe ship at all once the cap lands, given imported facts are then non-assertable? The recipe's value may have depended on the defect. (The recipe can honestly become "seed *context*, not *testimony*" — imported material informs without being asserted — but whether that serves the original demand is the open half.) | `pre-release` | marketing + dev | before the recipe publishes |

---

## Review closure

*(PROCESS §4a — one row per finding; the round-1 package was
`0005-v3-20260813T1633Z.tar.gz`, sha `a2f5dd90…`, disposition RETURN FOR
AMENDMENT, 7 bin-(a) + 2 editorial.)*

| round | finding | class | disposition | evidence |
|---|---|---|---|---|
| 1 | R1-1 remap preserves a false author claim (`introspect().by_author` reports `{"user": 1}` to the target) | C+D | **folded (v4): the cap's third lever** — `author_of_evidence = THIRD_PARTY` on every default import, unconditional per I-Q1; the v3 "cap rather than rewrite" argument withdrawn in §4c; the loss recorded as §8 limit 5; P1 extended to the reporting surface | v4 §§2, 4a, 4c, 8; P1 |
| 1 | R1-2 `restore` lacks a closed validity predicate (truthiness bypass) | F | **folded (v4):** `type(restore) is bool` refused with `TypeError` before mutual exclusion and before the file opens; CLI `store_true` | v4 §4a, §7a; P13 |
| 1 | R1-3 "byte-faithful restore" contradicts the accepted canonicalization (reviewer-executed: `hist:` remap, origin materialisation, same-store refusal) | D+G | **folded (v4):** restore redefined — skips §4c-ii step 3 and nothing else; trust-field-faithful contract pinned; the four-cell matrix specified | v4 §4a, §4c-ii, §4d, §5; P2 |
| 1 | R1-4 malformed trust-field handling vs cap-before-validation | D+C | **folded (v4):** the five-step sequence pinned — validate (malformed/null raise) THEN cap (omitted→default→capped); "before validation into models" withdrawn | v4 §4c-ii, §2c; P14 |
| 1 | R1-5 P10 recruits operators into the bypass on tampered own-exports | C | **folded (v4):** the refusal message text pinned (names `--restore` AND the trusts-every-record warning); the mixed-file case is the standing regression | v4 §4d, §2c, §8 limit 1; P10, P15 |
| 1 | R1-6 the call-site inventory incorrect and non-executable (claimed 56/8; measured 50 AST / 7 files) | F+E | **folded (v4):** measured numbers stated; prose inventory replaced by the mechanical per-callsite disposition manifest obligation; negative fixtures must assert their original refusal reason | v4 §7b |
| 1 | R1-7 P1–P12 claimed as CI with zero existing tests | E | **folded (v4):** every §6 check labelled `obligation — impl commit`; the header states the rule and its 0015 R8-4 precedent | v4 §6 |
| 1 | (b) opening narrative said draft v2 on a v3 candidate | — | **folded (v4):** narrative tracks the version | v4 header |
| 1 | (b) the local audit carrier (`_record("import", ...)`) unspecified for `capped` | — | **folded (v4):** specified — audit payload keeps `{edges, episodes, skipped}`; `capped` deliberately not forwarded (0015-regime consent work out of scope); impl-commit test pinned | v4 §7a |
