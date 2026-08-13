# Feature spec: import has no trust boundary

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft v2** — split out of `0002` on 2026-08-01 (v1); matured to the ruled
> design 2026-08-13 and **re-verified line-by-line against the shipped import
> machinery** (FORMAT 5: the 0009 whole-file preflight + atomic commit, the
> 0010 X17–X19 shapes, the 0006 origin gates, the 0014 indexed-output identity
> gates — none of which existed when v1 was written). **This spec carries a
> queued trigger:** the cross-project-inheritance docs recipe stays held until
> this ships (I-Q2 decides whether it ships at all).

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v2 — v1's design question `I-Q1` was RULED 2026-08-01 (§4b, `proposals/S-I-H-Q1-rulings.md`); v2 folds the ruling, re-verifies every reach claim against the current code, and corrects a v1 mechanism defect found in that re-verification (§4c) |
| **Status** | *see `Spec-Status:` — canonical.* |
| **Internal reviewers** | research — **found the defect**; dev verified it is CLI-reachable; research ruled I-Q1 |
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
| `Provenance.author_of_evidence` | read everywhere | "who authored the evidence" | disclosure routing, ladder | **unchanged — deliberately.** The record is true; §4c says why we cap rather than rewrite |
| `Edge.confidence`, `valid_from`, `observed_at`, `needs_confirmation` | imported verbatim | honest history | staleness, rendering | **unchanged** — capped records render in the unverified block at their own confidence (the 0.4.1 per-block contract); §4e states why currency needs no extra rule |
| `import_memory(...)` return | host API + CLI + `_record("import", ...)` | counts dict | `__init__.py:1063`, `cli.py` | **gains `"capped": <int>`** (0 under restore). §3b runs the oracle lens on it |

---

## 2c. Untrusted inputs — REQUIRED, blocking

**The export file is the untrusted input** — a file, not a field. Every gate
that already exists at this boundary is an *integrity* gate; the rows below
name which spec owns each, and the two ⚠ rows are the trust gap this spec
closes.

| uncontrolled input | empty | malformed | unrecognised | adversarial | governing rule |
|---|---|---|---|---|---|
| **file body: trust fields** (`author_of_evidence`, `disclosure`, `derived_from`, `confidence`, timestamps) | field absent → pydantic defaults — **⚠ `disclosure` defaults to `MENTIONABLE` (`schema.py:115`), so *omitting* the field is as strong as forging it** | pydantic raises | — | **every trust field is attacker-chosen, on edges AND episodes** | **⚠ THIS SPEC — P1/P4/P7: the cap applies to the parsed records before any other consumer, so neither a forged nor an absent field evades it** |
| **`--user` / `user_id=` remap** | header's `user_id` used | — | — | the boundary crossing itself — its documented purpose | **P5/P6**: the cap no longer keys on the remap at all (§4b); remap additionally mints fresh ids (copy semantics, 0009 §4c) |
| **export header `user_id`** | refused (no target) | `json.loads` raises | — | **attacker sets it equal to the target** — v1's suppression vector | **de-fanged (§4b): the header decides only copy-vs-same-id mechanics, never trust.** Integrity against id collision is 0009 §4c record-equality (differ → refuse) |
| **`--restore` flag** | absent → cap applies | — | — | **an attacker-supplied file handed to an operator who runs `--restore`** | **out of scope by construction (§8): `--restore` is the operator's explicit trust assertion — the decision this design moves from the file to the operator.** P5 keeps it from composing with `--user` |
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
  the flags alone** — the caller could compute it from inputs it already holds.
  It reveals nothing about prior store state. (The pre-existing `"skipped"`
  count does reflect destination state; that is shipped v0 behaviour,
  unchanged here and reachable only by the operator who owns the store.)
- **`--restore` is an authorization act,** not a parser flag: it is the
  operator asserting "this file is my own store's history." §8 states the
  limit that creates.

---

## 4. Behaviour

### 4a. The rule

> **Every import caps** (`restore=False`, the default — including same-user
> imports and imports whose header matches the target):
> for **every** imported record, edge and episode alike,
> `derived_from = THIRD_PARTY` (already-`THIRD_PARTY` values keep it — min,
> never raised) **and** `disclosure` is floored to `USE_ONLY`
> (`QUARANTINED` stays `QUARANTINED` — flooring never *raises* a stricter
> value).
>
> **`restore=True` (CLI `--restore`) opts out** — byte-faithful,
> provenance-preserving import, the reason `import` exists.
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

### 4c. The mechanism — two levers, not one (v1 correction, found in re-verification)

v1 capped only `derived_from` and claimed `assertable` would go false. **That
was unimplementable as written**: `assertable` keys on the *stored*
`disclosure` field (`schema.py:271-284`), which the file supplies — or worse,
omits, inheriting the `MENTIONABLE` default (`schema.py:115`). A capped-`derived_from`
edge with file-chosen `disclosure=MENTIONABLE` would remain fully assertable;
v1's own named check would have failed. The corrected mechanism caps **both
carriers of the same fact**, coherently:

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

**Where it applies:** to the parsed in-memory records immediately after the
parse/remap step and **before every other consumer** — before the 0006 origin
gates, before 0014's projection comparisons, before 0009's record-equality
preflight, before validation into models. This is 0006 I7's "applies first,"
made operational: no downstream gate ever sees an uncapped record, so no
idempotency comparison, identity projection, or grouping can be used to smuggle
an uncapped form past the boundary.

**Why cap rather than rewrite `author_of_evidence`** (kept from v1 — still the
design's core): the record is not false. Alice's edge honestly says "authored
by the user of this store"; re-homing changes the referent, not the truth.
Overwriting the author would destroy a true statement to fix a referent
problem and lose the fact that this was somebody's first-person testimony —
which a later operator may need. Capping leaves the record intact and makes
the *effective* trust correct.

### 4d. Consequences, stated plainly

- **After a default import, nothing from the file is assertable and every
  imported episode renders in the UNVERIFIED block.** Intended: the population
  this serves is importing content it did not author. A host that wants an
  imported fact asserted has the answer `confirm()` gives — that affirmation
  is new user-authored evidence and belongs in `remember()`.
- **Re-importing your own export now refuses by default** (the stored originals
  differ from the capped incoming form → 0009 record-equality refuses the
  whole import) **with a message that names `--restore`.** First contact
  teaches the distinction; nothing is silently half-imported (the atomic plan
  guarantees that already).
- **Idempotency is preserved within each path:** default-then-default re-import
  skips (capped == capped); restore-then-restore skips. **Mixing paths for the
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
| default, re-import of a default import | capped == capped → record-equal skip; `capped` counts the incoming records that carried a cap-changing value |
| default, target holds uncapped originals (own store round-trip) | **refuse whole import**; message names `--restore` |
| `--restore`, no `user_id` | byte-faithful; provenance preserved; `capped=0`; 0006 I6/I9 round-trip properties live here (§7b) |
| `--restore` + `--user` (any values) | **refused before the file is opened** — P5 |
| default + `--user` (cross-principal copy) | fresh ids minted (0009 §4c), every record capped — the original reported scenario, now safe by default |
| any path, integrity-gate failure (topology / origin / identity / claimed) | shipped refusals unchanged, and they all fire on **capped** records — the cap runs first |

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **P1** a default import caps every record — edges AND episodes | `test_default_import_caps_every_record` — Alice→Bob: every edge `assertable` False + `derived_from` `THIRD_PARTY`; every episode `third_party_influenced` True | CI |
| **P2** restore is byte-faithful | `test_restore_preserves_provenance_exactly` — restore round-trip, field-for-field equality incl. `disclosure`, `derived_from` | CI |
| **P3** the cap never raises | `test_import_cap_never_raises` — records already at `THIRD_PARTY`/`USE_ONLY`/`QUARANTINED` are byte-unchanged by the cap | CI |
| **P4** a hand-written file cannot evade the cap — **including by omission** | `test_handwritten_export_cannot_evade_the_cap` — trust fields set adversarially AND omitted entirely (the `MENTIONABLE`-default cell); post-import nothing assertable | CI |
| **P5** `restore` and `user_id` are mutually exclusive | `test_restore_with_remap_is_refused` — API `ValueError` before the file is read; CLI exits non-zero on `--restore --user` | CI |
| **P6** the cap is unconditional without restore | `test_every_import_caps_by_default` — same-`user_id` import and a crafted header equal to the target both cap | CI |
| **P7** the episode channel is closed | `test_imported_episode_renders_unverified` — a default-imported `author=user` episode appears in the gate's UNVERIFIED partition, never GROUNDED | CI |
| **P8** import mutates nothing existing (N9t currency) | `test_import_never_mutates_existing_rows` — snapshot every destination row; run default import (success), refused import, and a crafted supersedes-into-destination import; assert byte-identical destination rows and unchanged `active` flags in all three | CI |
| **P9** source-identity fields do not bypass the cap — **0006 I7, discharged** | `test_imported_source_id_does_not_bypass_the_remap_cap` (0006's named test, written here) — a v5 file with foreign `(origin, source_id)`: records cap normally; grouping/digest run on capped records only | CI |
| **P10** the default-path refusal names the alternative | `test_own_store_reimport_refusal_names_restore` — the refusal message contains `--restore` | CI |

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
| `portability.import_memory(store, path, *, user_id=None)` (`portability.py:172`) | gains `restore: bool = False`; mutual-exclusion check first; the cap step; return gains `"capped"` |
| `Memory.import_memory(self, path, *, user_id=None)` (`__init__.py:1063`) | mirrors the signature; docstring trust note rewritten (see docs row) |
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
| **0009 §4c / 0010 X17-X19 / 0014 §2c** | machinery referenced, not amended — the cap runs strictly before all of them | their import-path test fixtures that round-trip same-store on the default path are updated to `restore=True` where they test *integrity* semantics; fixtures that test *trust* keep the default path. **56 `import_memory` call sites across 8 test files enumerated (2026-08-13); the sweep is an implementation obligation with this inventory as its checklist** |
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

1. **`--restore` is trust by operator assertion.** An operator who runs
   `--restore` on a file they did not export has asserted something false, and
   the import behaves accordingly — the exact scope of the ruling: the
   decision moved *to the operator*, not eliminated. The CLI help and docs
   say this in one sentence.
2. **Mixed-path imports of the same records refuse** (§4d) — including 0014's
   indexed-output projection treating capped-vs-uncapped provenance as a real
   difference. Fail-closed and loud, never merged; an operator hitting it is
   holding one file in two trust postures.
3. **Capped records still exist**: they occupy the unverified block, carry
   their own confidence, and count in outcome-chain history. The boundary
   controls *assertion*, not *presence* — presence is what import is for.
4. **The cap does not authenticate `origin`** — 0006 R7's boundary stands;
   forged namespacing remains namespacing. This spec makes it *harmless*
   (grouping runs on capped records, P9), not *honest*.

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
