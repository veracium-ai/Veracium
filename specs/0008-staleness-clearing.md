# Feature spec: what may clear `needs_confirmation`

Spec-Status: accepted
Spec-Requires: 0007, 0013
Folds: 0047/0008-request-registry

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **accepted 2026-08-02 19:27 UTC** — under `PROCESS.md` §4a, after four external rounds in
> which **the clearing rule was approved every time**. Every finding is closed
> in *Review closure* with openable evidence. **`Spec-Requires: 0007` still
> blocks implementation**, which is the intended outcome: the rule is settled,
> the prerequisite is not.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v8 — THREE SENTENCES ADDED AT THE REGISTRY'S IMPLEMENTATION (dev's T3, `f20840f`), 2026-10-14.** They state what v7 left unstated and the implementation had to choose, as research's shape read answered it and dev implemented it. Nothing landed is reworded. (1) `written_at` is a write time on every registry row: the store's clock at the write (§6c), and the migration's one clock read on a backfilled row (§2a). (2) For `confirm()`, the terminal `request_redacted` is a named raise, `RequestRedacted`, because §6c freezes the return mapping (§6g). (3) The terminal rule precedes the verb check, so a request of another verb under a redacted id is refused as `request_redacted`, naming the holding verb (§6g). Disclosed to the external reviewer in the R-I package with v7. Prior: **v7 — TWO POST-ACCEPTANCE CORRECTIONS, 2026-10-14, before the registry is implemented.** **(D4, the owner's ruling “Undo is not an act row”, relayed first-hand by dev):** 0044's undo is a verb of the request registry but not an act: it writes no act row, takes no `act_seq` and has no `act_uid`. §2's act-rows and `act_counter` rows and §6f's counter sentence now name `confirm`/`reply` only, and §2's stale “0044's undo rows” names the outcome rows that record an undo (0044 §4g). **(N4, a research reading, dev's plan §5):** a `local` act's `act_uid` is DERIVED at each export from components fixed for the row's life, which meets §6e's “set once” byte for byte and keeps export read-only; the condition under which that stops holding is stated in §6e. Both are disclosed to the external reviewer in the R-I package. Prior: **v6 — THE REQUEST-REGISTRY FOLD (amendment `0047/0008-request-registry`, v1.10, sha16 `550abfaeb4c410fc`).** Its design was ACCEPTED at round 4 of both packages that carried it (0044; 0045–0047; verdicts 2026-10-13), and the owner ruled “Accept now, fold next” (2026-10-14). *Annotation (research, 2026-10-15; the sentence before it is kept as written): the bytes round 4 reviewed are the amendment's **v1.9**, sha16 `1c39f735013e1218`. The digest this cell names, `550abfaeb4c410fc`, is a post-verdict re-spin of them, carrying the round-4 verdict's history boundary (one file or successive complete source snapshots) and a consolidation of the amendment's version narratives. Every normative change from the reviewed bytes to the fold's source, with its cause, and the correspondence from that source to this document, are research's fold-correspondence record (research commit `106ddbff`), which the R-A package carries.* Folded: §2a (the registry's fields and the migration's carrier inventory), §2c's and §2c-ii's v6 rows, §3a (an act's origin as a trust class), §6b's record origin, §6c's request registry, §6d's SQLite line and two retention rows, C8 and C11, the v6 invariants, the new §6e–§6g, and the v6 regimes, failure modes and claims. Not folded: the amendment's review briefs, open questions and version history, which stay with its research file and `specs/reviews.py`. A version tag of the form vN.N inside the folded text is the amendment's own. Prior: **v5** — *re-read before editing; quote the version you approve.* **The clearing rule has been approved in every round; the deferrals are the contract around it.** |
| **Status** | *see `Spec-Status:` — canonical.* Split from `0002` §M3/§7b. **`0002` is a retrospective and must be closeable; this is a proposal and is not.** |
| **Internal reviewers** | research — **R2** (fail-closed rule) and **R3** (strict; not temporary) |
| **External review** | required — **counts are generated into `specs/STATUS.md` from `specs/reviews.py`; this row states none.** It said *"two rounds complete"* while `reviews.py` recorded three, in a project that built the generation to stop exactly that. |
| **Decision + date** | **ACCEPTED 2026-08-02, SCOPED** — external round 4: the clearing rule approved across all four rounds; the deferred surfaces (episode inputs, idempotency, storage/API shape, the `0007` interplay) moved to their owning specs rather than holding the rule. *(Row filled 2026-08-22 — the spec-table audit.)* **v6, 2026-10-14:** the amendment `0047/0008-request-registry`, its design accepted at round 4 (2026-10-13), folded on the owner's ruling “Accept now, fold next”. **v7, 2026-10-14:** D4 (the owner's ruling) and N4 (a research reading), corrections after acceptance; `Spec-Status` stays `accepted`. **v8, 2026-10-14:** three sentences added at the registry's implementation; `Spec-Status` stays `accepted`. |
| **Path** | full |

---

## 1. Problem and motivation

**A staleness flag addressed to the user can be cleared by something that is not
the user.**

`needs_confirmation` renders as `[possibly stale — confirm before relying on
it]` (`graph.py:358`). It is **a question addressed to whoever is entitled to reaffirm the fact** —
v1 said *"the party who stated it"*, and §6a establishes the mechanism cannot
prove the original speaker acted, only that an authorised principal did.

```python
if (prior.provenance.author_of_evidence
        == edge.provenance.author_of_evidence):
    prior.needs_confirmation = False
```

**Author class is not source identity and not evidence basis.** Two unrelated
`SYSTEM` processes are both `SYSTEM`; two unrelated third parties are both
`THIRD_PARTY`; and a system may restate a derived claim having observed nothing
new. **Same class ≠ same source · same speaker ≠ fresh evidence · repetition ≠
renewed observation.**

**This shipped in 0.4.5 as the fix for M3**, described as *"a staleness flag can
no longer be cleared by a different author"*. That is true and insufficient: it
closed cross-*class* clearing and left same-class clearing wide open, which is
the case that matters because **the host chooses the class**.

**The deeper defect, found by the second external review of `0002`.** The rule
that replaced it in `0002` §7b permitted *"a new user-authored observation"* to
clear the flag — while **§2c of the same document lists host-supplied `author`
as an uncontrolled input** whose adversarial case is *"host may claim
`system`"*. **The rule tested the very field we model as adversarial.** Both
sections were written by us, days apart, and neither was cross-read against the
other.

**Alternatives rejected.**

- **Same-class equality** (shipped). Closes the wrong half; see above.
- **Same `source_id`**, once `0006` lands. **Rejected by R3, and this is the
  subtle one:** *never model-supplied ≠ authenticated*. A host can give two
  unrelated statements one `source_id`, and same-source reinforcement would then
  clear staleness on evidence with **no common source**. It grants exactly what
  the strict rule withholds.
- **A `confirmed_by` parameter on `remember()`.** Rejected on the governing
  principle below — it is another field, and fields are what failed.

---

## 2. Field contracts touched

| field | read / written | contract | preserved? |
|---|---|---|---|
| `Edge.needs_confirmation` | set by `expire()`; **cleared by `confirm()` only, after this change** | "an **authorised principal** must explicitly reaffirm this edge through `confirm()`" — v1 said *"the party who stated this should re-affirm it"*, which the mechanism does not establish (§6a) | **restored** — currently cleared by parties that did not state it |
| `Provenance.author_of_evidence` | read by the rule being **removed** | authorship of evidence | **unchanged** — this spec stops *relying* on it for authority, it does not alter it |

### 2a. What the request registry adds (v6, amendment `0047/0008-request-registry`)

| site | before v6 | after |
|---|---|---|
| **`request_registry`** *(new table)*: `user_id`, `correlation_id`, `verb` ∈ {`confirm`, `reply`, `undo`} (`undo` is 0044's), **`target_edge_id`** (v1.2: the edge the request acted on, so a redaction can find it, §6g), `request_digest`, `result_ref`, `written_at`; **`UNIQUE(user_id, correlation_id)`** | — | written by **every verb of the id space, in that verb's own transaction**; read by every such verb **before any read of live edge state**; never exported; erased with the user |
| `confirmations` | no origin; `UNIQUE(user_id, correlation_id)` | **gains `origin` ∈ {`local`, `imported`, `restored`}** (NOT NULL, default and backfill `local`) **and `recorded_correlation_id`** (NULL for `local` rows). **The UNIQUE stays exactly as it is** (a table constraint; C8's backstop). An imported or restored act keeps the ORIGINAL request's id as evidence in `recorded_correlation_id`; its `correlation_id` is an internal `#act:` key outside the caller grammar (v1.2, §6e) and writes no registry row, so it never occupies or collides with this store's id space |
| `Store.confirm_edge` replay lookup (`sqlite.py` L701, L756 at `f98a3a0`) | `confirmations` only | **the registry first**: same id + same verb + same canonical request → the original result (`result_ref`); same id with a different verb or a different request → integrity conflict naming the verb that holds it |
| export / import of `confirmations` (§6d row; C11 `test_export_excludes_confirmations`) | **excluded** | **carried, with `origin`**, under 0047 §4f's matrix; the registry is never carried |
| `forget_user()` | deletes and counts confirmations | also deletes the user's registry rows, act rows and 0044's outcome, run and inventory rows (§6g's single rule); replay ends at erasure |
| **act rows** (`confirmations` and 0047's `replies`; **not** 0044's undo, which is recorded on its outcome row, 0044 §4g) | no portable identity; no position | **gain `act_uid` and `pos = (origin_store, act_seq)`** with `origin_user` as provenance (v1.2, §6e–§6f); an imported or restored act's `correlation_id` is an internal `#act:` key |
| **`act_counter`** *(new, one row per store)* | — | the store-wide, never-reset source of `act_seq`, incremented inside each act verb's `BEGIN IMMEDIATE` (`confirm`, `reply`; §6f); not user data, never erased |

**The migration, additive: the complete carrier inventory (v1.3).** One 0013 schema step writes every carrier this
amendment adds. v1.2's “one CREATE TABLE, two ADD COLUMN” predated the act identity, the position and the registry
target, and omitted them.

| carrier | statement | a row that exists before the step |
|---|---|---|
| `request_registry` (`user_id`, `correlation_id`, `verb`, `target_edge_id`, `request_digest`, `result_ref`, `written_at`; `UNIQUE(user_id, correlation_id)`) | `CREATE TABLE` | **backfilled: one `confirm` row per existing confirmation**: its `correlation_id`, `target_edge_id` = its edge, `result_ref` = the confirmation id, and `request_digest` copied, or **the marker if that confirmation is already redacted** (§6g, INV-Q7); *v8:* `written_at` is the migration's one clock read, a write time as on every registry row (§6c); the original request's time stays on the confirmation, through `result_ref` |
| `act_counter` (one row: `next_seq`) | `CREATE TABLE`, one row inserted | — (the counter starts at the step; no legacy act receives a value) |
| `confirmations.origin` | `ADD COLUMN … NOT NULL DEFAULT 'local'` | `local` |
| `confirmations.recorded_correlation_id` | `ADD COLUMN` | NULL |
| `confirmations.origin_store`, `.origin_user`, `.origin_act_id` (the `act_uid`, §6e) | `ADD COLUMN` ×3 | NULL for every `local` act, legacy or new: its identity is this store's, DERIVED at each export (§6e, v7) |
| `confirmations.act_seq` (with `origin_store`, the position, §6f) | `ADD COLUMN` | **NULL = an UNKNOWN position**, never synthesized (§6f) |

**Not in this step:** `replies` is created whole by 0047's own step (its act columns are this inventory's, §2's table),
and 0044's outcome rows, which record an undo as `undone_at` and `undo_request_ref` (0044 §4g), by the 0018 amendment's step. Without the registry backfill, a pre-upgrade confirmation's id could
be reused by a reply. The step's number is assigned at implementation: the 0018 amendment also takes a schema step,
and the two are ordered there.

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant |
|---|---|---|---|---|---|
| **host/model `author`** on `remember` | enum-rejected | enum-rejected | enum-rejected | **`author="user"` on model-authored text** — and `remember` is `@server.tool()`, so **the model reaches this directly** | **C1** — no value of `author` clears the flag |
| **`source_id`** (future, `0006`) | — | — | — | host reuses one id across unrelated sources | **C1** — no field clears the flag, whatever it is |
| **`actor`** on `confirm()` | defaults `user` | — | — | mislabelled | **C2** — `actor` is recorded, never load-bearing; the **call** is the evidence |
| **call frequency** | — | — | — | repeated `confirm()` to hold a fact fresh forever | **audited, not limited** (§6b). A host with API access can do this by design; the record makes it **visible**, which is the part veracium can provide. Rate limiting is host policy |

**v6's rows (the request registry):**

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant** |
|---|---|---|---|---|---|
| `correlation_id` on any verb (host-supplied) | generated and persisted (0008: no replay protection), and it takes a registry row | §6c's format check raises before any mutation (C9, unchanged) | — | an id already held by ANOTHER verb or request → integrity conflict; replay never returns another verb's result | **INV-Q1**, **INV-Q2** |
| an import file's confirmation rows (`origin`, `correlation_id`, fields) | none | shape refused, the whole file (0047 §4f) | an `origin` outside the three → refused | a default import cannot write `local` or `restored`; a trusted restore cannot upgrade a recorded `imported`; a file's correlation ids are kept in `recorded_correlation_id` and never enter this store's registry, and each imported act gets an internal `#act:` key outside the caller grammar, so a file cannot consume or collide with ids the host needs. **v1.2:** a default file claiming THIS store's origin is refused (§6e rule 0), so it cannot forge an order against a local act; a forged `act_uid` equal to a held act's is either an exact replay (a no-op) or a conflicting replay (the whole unit refused), never a second act | **INV-Q4′**, **INV-Q5**, **INV-I1..I3**, **INV-Q9** |

> **Template rule this spec is the first to follow** *(research, 2026-08-01;
> proposed as a `Process-Change`)*: **a rule that relies on an input listed in
> §2c must name that row and say why it is safe to rely on it here.** This spec
> relies on **none of them** — which is the whole design.

## 2c-ii. Assertions about reach

| assertion | command | result |
|---|---|---|
| the shipped rule compares class only | `sed -n '119,121p' src/veracium/graph.py` | `==` on `author_of_evidence` |
| `author` is model-reachable | `grep -n "@server.tool" src/veracium/mcp_server.py` | `remember` · `recall` · `answer` · `maintain` |
| **`confirm()` is not** | same command; `grep -n "add_parser" src/veracium/cli.py` | absent from both — **host API only** |
| the flag reaches the model | `grep -n "possibly stale" src/veracium/graph.py` | `:358` |

**v6's rows (the request registry).** Commands run from the repository root at `af1e564` (research, 2026-10-14). **EXECUTED** = run and read; **READ** = the cited lines. The amendment's rows 5 and 7 described this document's own text before the fold (that §6d excluded export, and that no `Folds:` line existed) and are not carried.

| # | assertion | command | result |
|---|---|---|---|
| 1 | replay is looked up in `confirmations` only (the first lookup, and C8's race re-read) | `grep -n "FROM confirmations WHERE user_id=? AND" src/veracium/store/sqlite.py` | READ: L701, L756 (L779 is `confirmations_for`, the audit read) |
| 2 | the id space's only constraint is the confirmations table's | `grep -n "UNIQUE(user_id, correlation_id)" src/veracium/store/schema_version.py` | READ: L170 (L163 is its comment) |
| 3 | C8's concurrency rests on that constraint | `grep -n "C8: a concurrent duplicate won the UNIQUE" src/veracium/store/sqlite.py` | READ: L752 |
| 4 | export carries no confirmation today | `grep -ci "confirmation" src/veracium/portability.py` | EXECUTED: `0` |
| 6 | user erasure covers `confirmations` | `grep -n "\"confirmations\", \"consolidation_ops\"," src/veracium/store/sqlite.py` | READ: L128 (`_ERASE_TABLES`) |

---

## 3. Trust-class matrix — REQUIRED, blocking

**Two effects, not one.** v1 wrote a single **BLOCK** column, which was
ambiguous: a restatement blocked from *clearing* the flag still advanced
liveness, and that decides whether the flag is ever **set** (§3d).

| candidate | clears the flag? | advances liveness? |
|---|---|---|
| **`confirm()`** — host API, not model-reachable | **yes** | yes |
| `remember(author="user")`, same value | **no** | **unchanged — `0012`** |
| `remember(author="system")`, same value | **no** | **unchanged — `0012`** |
| third-party restatement | **no** | **unchanged — `0012`** |
| cross-class restatement | no *(0.4.5)* | **unchanged — `0012`** |
| `expire()` · consolidation · dedup · wiki | **no** | no — maintenance never refreshes |
| same `source_id` *(future, `0006`)* | **no** | **unchanged — `0012`** |

**The liveness column says `unchanged` rather than a rule**, because this spec
does not have one. v2 filled it from the supersession ladder and the result
contradicted this very table in two rows — `third_party → third_party` and
`third_party → user` both renew under authority and are denied here.

> **The governing principle:** *an act through a dedicated entry point is
> evidence; a field asserting who acted is not.* **Add an entry point, not a
> parameter.**

**And a distinction integrators mistake:** a user who agrees with a third-party
claim has produced **new user evidence**, which belongs in `remember()`.
`confirm()` is not a mechanism for adopting untrusted content — it reaffirms
what is already there, at the trust it already has.


### 3a. An act's origin is a trust class (v6, amendment `0047/0008-request-registry`)

| act's origin | counts toward 0045's `g(e) = confirmed` | occupies this store's id space | exported as |
|---|---|---|---|
| **`local`** — made through this store's verb | **yes** | **yes** (registry row) | `local` |
| **`restored`** — a `local` act brought back by a trusted restore of its own history | **yes** | no (the request was made to another store) | `restored` |
| **`imported`** — any act arriving by default import, or recorded `imported` in a trusted restore | **no**: testimony, shown in `why` | no | `imported` |

- Can **testimony become proof**? No. A default import writes `imported`. A trusted restore reproduces the recorded
  origin and maps only `local → restored`, so the chain *local → export → default import → export → trusted restore*
  still reads `imported` (INV-Q5). A replay of an act already held never changes its stored label, up or down (§6e,
  v1.3).
- Can **an untrusted file deny the host an id**? No. An imported row's file id is evidence in
  `recorded_correlation_id`; its own `correlation_id` is an internal `#act:` key outside the caller grammar (§6e); it writes no registry
  row (INV-Q4′).
- **Positions are claims, too (v1.2).** A position in a default-import file orders acts only against acts of the same
  FOREIGN origin; this store's own origin is refused there (INV-Q9).
- **0044's migration outcomes use this matrix** (v1.2): `local` and `restored` outcomes are proof, `imported` is
  testimony, and no undo is possible from testimony (0044 §4i).
- **Trust classes not touched:** `EvidenceAuthor` and the gate are unchanged. `confirm()`'s authorization (0008 §6a)
  is unchanged. An import writes act rows and transitions no existing edge's `needs_confirmation` (C1 untouched).

**Authorization and scope (v6).** No new surface. `Memory.confirm()`'s signature and return shape (§6c) are unchanged; a conflict now also names the verb that holds the id. MCP gains no tool.

## 3d. Clearing is not the only way to defeat the flag — and that is `0012`

**Measured.** `expire()` ages against `observed_at` and reinforcement advances
`observed_at` unconditionally, so repeated restatement keeps a fact permanently
fresh and the flag never fires:

```
SLOW relation, lifetime 120 days, edge 200 days old
control, no restatement       -> needs_confirmation = True
4 THIRD_PARTY restatements    -> needs_confirmation = False
```

**A party that cannot clear the flag can prevent it appearing**, and the
restatements are the class §1 treats as adversarial.

**v2 tried to fix this here, with recorded effective authority, and the second
external review rejected it. Correctly.** Authority answers *how strongly may
this evidence affect trust decisions*; it does not answer *did this source
observe the fact again*. **That is this spec's own error one level up** — §1
rejects same-author-class because unrelated sources share a class, and unrelated
sources share an authority rung too. It also contradicted the matrix below and
depended on `0003`, which is not accepted.

> **Moved to `specs/0012`.** `0008` closes the clearing path and **claims
> nothing about liveness.** §8 says so.

**Why it cannot be a smaller fix here:** reinforcement **discards** the incoming
edge today, so *"store the incoming observation as its own evidence"* is a new
representation, not a narrower version of this change.

---


## 4. Behaviour

Delete the conditional at `graph.py:119-121`. Reinforcement continues to refresh
**liveness** (`observed_at`) **unchanged — that behaviour is `0012`'s subject,
neither endorsed nor altered here** — and to retain confidence per `0002` M5 T1;
it stops
touching `needs_confirmation`.

**`confirm()` is unchanged** and already carries the correct guard — only
assertable facts may be confirmed, because *"if the user affirms a claim, that
affirmation is new user-authored evidence and belongs in `remember()`"*.

**This is a restriction, and it is not temporary.** R3: `source_id` does not
lift it. What would is **provenance of the call, not of the claim** — recording
which entry point was used and requiring hosts to gate the privileged ones.
**That belongs in evidence-basis and is on no roadmap**; this spec should not
imply a relaxation it cannot deliver.

**Cost, stated plainly:** a genuine same-source restatement no longer clears the
flag, so a fact stays marked `[possibly stale]` until someone calls `confirm()`.
**The failure is additive and visible** — a caveat that should have gone away —
against **silent removal of a caveat that should have stayed**, which is what
ships today.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **C1** only `Store.confirm_edge()` may transition an **existing stored edge** from `needs_confirmation` `True → False` | **three checks.** `test_no_provenance_value_clears_staleness` — behavioural, over every provenance input · `test_add_edge_refuses_the_transition` — **runtime**: generic `add_edge()` rejects it, with **no context parameter that could authorise it** · `test_no_direct_writer_outside_confirm_edge` — AST inventory as *defence in depth*; it cannot see `model_copy(update=…)`, `setattr`, a reconstructed edge or deserialisation, which is why it is not the guard | CI |
| **C2** `confirm()` clears it | `test_confirm_clears_staleness` | CI |
| **C2a** `actor` is audit metadata and grants nothing | `test_actor_metadata_does_not_grant_confirmation_authority` — authority comes from the protected call path; v1's name (*"clears regardless of actor label"*) read as normalising arbitrary labels | CI |
| **C3** *(SUPERSEDED — `0012` accepted 2026-08-10 and LANDED: reinforcement transfers NOTHING; the prior's `observed_at` no longer moves; `0008`'s conclusion — only `confirm()` clears the flag — is unaffected)* | `test_reinforcement_no_longer_advances_observed_at` (the inversion `0012` §7b dispositioned) — original rationale, historical: — **the permission, not the prohibition.** A deletion drawn too broadly would remove liveness refresh along with the flag clearing, and no other test distinguishes them. **Whether this behaviour is right at all is `0012` — and `0012` RULED it (2026-08-08, Design 1): reinforcement should transfer NOTHING (not `observed_at`, not `confidence`), persisting the incoming edge instead. So this C3 mechanism is superseded by `0012` on `0012`'s landing; `0008`'s CONCLUSION (only `confirm()` clears the flag) is unaffected.** Marked temporary precisely so an accepted `0008` does not read as prohibiting that correction. |
| **C4** maintenance never clears | `test_no_maintenance_op_clears_staleness` — property-based over random op sequences, asserting its registry against the **maintenance entry points reachable from `maintain()`/`lifecycle`**, *not* the `@store_mutator` surface. **Those sets are not equal**: the manifest's 28 sites include `ingest_event`, `correct`, `forget` and `import_memory`. **After implementation** it must also contain `confirm_edge` — which is *allowed* to clear — and must **no longer** contain `confirm()`'s independent `add_edge` and `add_episode` sites. **The count will change; it is regenerated and verified then, not asserted now.** The two inventories cross-check ownership and are never equated | CI |
| **C5** the flag reaches the model when set | `test_stale_marker_renders` | CI |
| **C6** the 0.4.5 reproducer stays fixed | `test_cross_author_restatement_does_not_clear` — regression, cross-class was the half 0.4.5 got right | CI |
| **C7** confirmation is **all-or-nothing** | `test_confirmation_is_atomic` — a store wrapper that fails the record write; **every edge field unchanged**, no episode | CI |
| **C8** replay and collision | `test_replay_returns_the_original_success` · `test_same_id_different_request_conflicts` · `test_concurrent_duplicates_commit_once` — one mutation, one episode, one record; **plus** cross-verb: an id held by `reply` conflicts on `confirm`, and an id held by `confirm` conflicts on `reply`, in both orders and under concurrency | CI |
| **C9** audit metadata is validated **before** any mutation | `test_invalid_call_path_rejects` + `test_invalid_correlation_id_rejects_before_mutation` — closed enums, length and charset | CI |
| **C10** **every** `Store` backend refuses the transition through `add_edge()` | `test_add_edge_transition_guard` — a **backend conformance test** run against each implementation, not a SQLite detail | CI |
| **C11** retention, erasure and export | `test_forget_user_deletes_and_counts_confirmations` (and registry rows) · **export carries confirmations with origin** (replacing `test_export_excludes_confirmations`) · `test_invalidated_edge_keeps_its_confirmations` | CI |
| **C12** schema-version compatibility gate | `test_older_build_cannot_open_a_confirmations_store` — **`0007`**; without it an older build ignores the table and clears unaudited | CI |

**v6's invariants (v6, amendment `0047/0008-request-registry`):**

| | invariant | mechanism mutant that must fail |
|---|---|---|
| **INV-Q1** | one id space per user across verbs: an id held by one verb or request is an integrity conflict for any other, in both orders | each verb checks only its own table; check only the new verb's direction |
| **INV-Q2** | replay is decided from the registry before any live edge state is read, and returns the original result after the edge changed or was invalidated | read the edge first, then the registry |
| **INV-Q3** | the migration backfills every existing confirmation, so a pre-upgrade confirm id conflicts on `reply` | migrate without the backfill |
| **INV-Q4′** | every internal key fails §6c's caller grammar and every caller key passes it; imported and restored acts write no registry row and keep the ORIGINAL request's id in `recorded_correlation_id` (v1.2: R2-02 said absence from the registry alone did not establish non-collision) | let an imported row keep the file's id as its `correlation_id`; generate `imp-N` keys (the verdict's sequence: a restore, then a local confirm with caller id `imp-1` on another edge, must be ADMITTED) |
| **INV-Q5** | origin never upgrades: default import writes `imported`; trusted restore maps `local → restored` and keeps `imported` | trusted restore writes recorded acts as `local`; default import keeps the file's origin |
| **INV-Q6** | user erasure deletes registry rows atomically with the user's acts and 0044's outcome, run and inventory rows, and a post-erasure retry is not a replay | keep registry rows after erasure |
| **INV-Q7** | after an edge's redaction no digest of a request on it survives in any table, the id stays held, and a retry under it returns the terminal `request_redacted` **for every verb, `confirm`, `reply` and `undo`** (v1.3: the terminal rule precedes replay) | treat `replies.text` only (the verdict's); replay "same payload" by comparing against a treated digest; keep an undo's digest after redaction and replay its `result_ref` (the 0044 review's witness) |
| **INV-Q8** | `act_uid` and `outcome_uid` are hashed over a canonical JSON array: a separator inside a field, a NUL and an empty field each give distinct keys | a separator join (collides on the first probe) |
| **INV-Q9** | positions come from a store-wide counter that is never reset, are ordered only within one `origin_store`, and a default import cannot claim this store's origin | MAX over live rows (erase, recreate, act: the position collides with an exported one); compare positions without the origin check (a forged `act_seq` 0 orders before a local open challenge) |
| **INV-I1** | importing the same file twice, in either mode, leaves the destination byte-identical after the first | compare full rows (the destination's remapped origin and internal key make the second import fail or duplicate); omit rule 1 (a default repeat refuses); use an act's internal `#act:` key as its original request id (an act recorded with NO request id then differs from its own repeat: dev's model, a round-3 model defect). Controls include an act recorded with no request id |
| **INV-I2** | a changed row under a held `act_uid` refuses the whole unit | admit it as a new act |
| **INV-I3** | an exact replay never admits a different act on its target, and never exempts another new act in the unit from validation | let rule 1 admit any act on a target that already holds a replayed act; skip §6f's chronology for a unit that contains a replay |
| **INV-I4** | **(v1.3, R3-01)** equality is decided on the canonical treated projection under the staged union's coverage: an ordinary reply restored onto its held redacted target under a covering notice is written with BOTH content carriers treated, and the same file imported again is a no-op; in a trusted restore, a held ordinary act redacted at its source and arriving treated with its notice receives the treatment and nothing else (v1.4: restore only; INV-I7 is the default-mode half) | compare untreated incoming rows with treated held rows (the second import refuses, the reviewer's witness 1); treat `text` but keep `request_digest` (witness 1's first admission); refuse a treated arrival over a held untreated copy (witness 2) |
| **INV-I7** | **(v1.4)** in a default import, a treated arriving copy of a held untreated act, with its covering notice, is an exact replay (a no-op): the held row is byte-equal before and after, the notice is PENDING, and `confirm_notice` then treats the held row and every other held carrier of the target; **(v1.5; v1.6)** in a trusted restore, the notice treats held rows only when the unit carries the target's record already showing the redaction, or **(v1.8)**, with no copy in the unit, when the held record already shows it; a unit carrying it unredacted refuses the whole import | apply the authorized transition in default mode (v1.3's rule: an untrusted file's notice rewrites held content); refuse the replay (an unchanged redacted re-export of a held act no longer imports); in a restore, apply a notice whose unit carries the target's record untreated (a poisoned store's own export), or admit that unit; with no copy in the unit, attest only and leave a held act's content (the total treatment broken) |
| **INV-I5** | **(v1.3, R3-01)** the authorized transition changes content carriers only, and coverage is all or nothing per row | let the transition change a structural field (kind, target, actor, edge, position, `confirmed_at`); admit a row whose target's notice attests `text` but not `request_digest`; enlarge a foreign notice's `fields` to cover the row; treat only the arriving notice's attested carriers on HELD rows (an older notice leaves a held reply's text published) |
| **INV-I6** | **(v1.3)** HELD is the staged union: two differing copies of one `act_uid` in ONE unit refuse it, two equal copies are one act, and the result is the same under every row order, and for one file or successive complete source snapshots (an arbitrary split is not equivalent, §6f) | build the identity map from pre-import rows only (the reviewer's same-unit witness admits both); process rows in file order; admit a file row id that names two different rows of one unit (a reference becomes ambiguous) |
| **INV-Q10** | **(v1.3, R3-02)** chronology over the merged history: a confirmation made under a challenge that is unresolved in H is refused, a legitimate challenge → resolve → confirm history is admitted, and an order that cannot be established, a second resolve, a resolve before its challenge, or two acts at one position refuse the unit | check confirmations before installing the unit's challenges (the reviewer's one-file witness admits); check held challenges before applying the unit's resolves (the valid resolved-history restore refuses); judge only incoming confirmations (an incoming unresolved challenge ordered before a held same-origin confirmation is admitted); treat an unknown position as earliest; treat a tie as ordered |

**Controls each new row is run with (the round-3 verdict's lists):** ordinary replay; treated replay; notice-first and
record-first arrival; a valid redaction update; a second hop; for chronology, a confirmation before the challenge, a
valid resolution before the confirmation, ties, unknown positions, incomparable origins, remapping and input order.
Negative controls: a structural change under a held `act_uid`, incomplete coverage, and a new untrusted act over a
held target.

*MODEL: Treatment before equality for INV-I4 and INV-I5 is notice coverage (its G19). Dev's reference model II encodes the registry (its G11), the import origin matrix (its G10), user erasure (its G14), the key domains for INV-Q4′ (its G15), the act ordinal, rule 0 and the restore chronology for INV-Q9 (its G16), repeat import for INV-I1–I3 (its G17), redacted requests and the backfill for INV-Q7 (its G18), and the canonical encoding for INV-Q8 (its G20; model I's INV-M22 answers it too). **v1.3's rows, encoded at the round-4 adoption: INV-Q10 → G16; INV-I3 and I6 → G17; INV-Q7 → G18 for acts and model I's INV-M27 for `undo` (a row with two owners); INV-I4 and I5 → G19.** PRODUCT
tests at the implementation gate, including C8's cross-verb concurrency and C11's new export test.*

**C3 is the one to write first.** The change is a deletion, and a deletion that
over-reaches would remove liveness refresh along with the flag clearing — which
no test currently distinguishes.

---

## 6a. What `confirm()` proves, and what the host must supply

**Finding 4: `confirm()` is a call path, not proof that a user affirmed
anything.** v1 argued it is safe because it is absent from the bundled MCP tool
list and the CLI. **That is true and it is not the same claim.** A host service,
a background job, or a custom model-facing tool the host writes can all call the
same API.

> **The contract, stated conditionally because that is what is true:**
> **veracium treats a call to `confirm()` as confirmation.** The host must
> expose that operation **only** through an authenticated, intent-bound action
> by the principal whose edge is being changed.

**Host obligations — the integrator's half, and it is not optional:**

| obligation | why |
|---|---|
| authenticate the principal | veracium cannot; it sees a function call |
| authorise for **that store and that edge** | a principal may be authenticated and still not own the edge |
| bind to explicit intent | a background job is not a reaffirmation |
| replay protection | a re-sent request is not a second confirmation |
| **never expose it to model control** | the whole boundary; a model-callable `confirm()` returns us to 0.4.5 |

**`actor` remains audit metadata and grants nothing** (C2a). It is retained
rather than removed because `record_outcome` beside it validates actor↔outcome
pairing and a silent removal would break callers — **but a caller could
reasonably read it as authorisation, so the spec says plainly that it is not.**

**Finding 5 — the field's own meaning was overstated.** §2 defined
`needs_confirmation` as *"the party who stated this should re-affirm it"* —
**WITHDRAWN wording.** The mechanism proves no such thing: not that the original
speaker acted, not that a human did.

> **Narrowed:** *an authorised principal must explicitly reaffirm this edge
> through `confirm()`.*

**That matters for system-authored, third-party-derived, imported, and
non-human-principal edges**, where "the party who stated this" may not exist as
a caller at all.

---

## 6b. The confirmation audit record

**Finding 7: `confirm()` becomes the only clearing path, and v1 left its
auditability `pre-release`.** Making a transition the entire trust boundary and
leaving it unobservable is not a defensible pairing.

> **One primitive, and it is the only way the transition happens:**
> ```
> @store_mutator
> Store.confirm_edge(user_id, edge_id, confirmed_at, actor,
>                    call_path, correlation_id) -> Confirmation
> ```
> The **store** loads the edge, verifies ownership and current state, enforces
> the assertability rule, applies **every** confirmation mutation, and persists
> the record — **in one commit.**

**v3 defined two mechanisms and they were incompatible.** C1 named
`clear_needs_confirmation(edge, confirmation_context)`; §6b named
`confirm_edge(...)`. **A caller-constructible `confirmation_context` is another
field claiming authorisation** — exactly what §6a rejects — so it is gone.
**`add_edge()` refuses a `True → False` transition on an existing edge**, with no
context parameter that would let it through.

**Every trust-bearing mutation is inside the transaction**, not just the flag.
v3's operation covered the flag and the audit; `Memory.confirm()` also advances
`observed_at`, raises `confidence`, and writes an episode
(`__init__.py:507-517`), so a partial outcome was possible:

| inside the transaction | why |
|---|---|
| `needs_confirmation = False` | the transition being authorised |
| `observed_at = max(old, confirmed_at)` | confirmation *is* an observation; splitting it lets the flag clear while currency does not move |
| `confidence = max(old, 0.9)` | same |
| the **confirmation record** | mandatory; **if it cannot commit, the confirmation fails and the flag stays set** |
| the confirmation **episode** | part of confirmation behaviour today; dropping it silently would be a behaviour change nobody asked for |

**`actor` is in the request because the episode needs it.** Today's summary is
`f"({actor}) confirmed …"` (`__init__.py:513`), so a store handed only
`(user_id, edge_id, confirmed_at, call_path, correlation_id)` **cannot reproduce
existing behaviour** — v4 froze a signature that could not do its own job.

**And that exposed a hole I had left open.** `actor` was called audit metadata,
kept out of the mandatory record, and **embedded unconstrained in a
content-bearing episode** — so a host could put prose, or a memory, in `actor`
and bypass every constraint §6c places on `call_path` and `correlation_id`.
**`ConfirmationActor` is now a closed enum**, like `call_path`.

**`Memory.confirm()` is not "unchanged", and v3 said it was.** Its persistence
mechanism moves from four independent store calls to one operation.

**The existing optional `AuditLog` does not satisfy this.** It is best-effort and
swallows failures (`_record`), which is right for telemetry and wrong for the
sole clearing transition. **The `confirmations` table is separate and
mandatory.**

**C-Q1 is resolved by this**, not deferred.

**The confirmation record's origin (v6).** `origin` — `local` for every row `confirm_edge` writes; `imported` / `restored` only from import (§6d). `recorded_correlation_id` — NULL for `local`; for an imported or restored act, the id its file recorded.

---

## 6c. The public contract, frozen

**Finding 3: v3 changed the persistence mechanism and never said what callers
see.**

```python
Memory.confirm(
    user_id: str,
    edge_id: str,
    *,
    date: str | None = None,
    actor: str = "user",                       # audit metadata; grants nothing
    call_path: ConfirmationCallPath = ConfirmationCallPath.HOST_API,
    correlation_id: str | None = None,
) -> ConfirmationResult
```

**Backward compatible.** Existing callers keep working: both new parameters have
defaults. **`principal` is `user_id`** — the store is tenant-scoped, so a
separate principal would be a second identity with no source of truth.

**`correlation_id` is optional, and the cost of omitting it is stated rather
than hidden:** supplied, it gives replay protection across an unknown commit
outcome; absent, the library generates one and **there is none.** A host that
retries a request whose result it never saw needs to supply it.

### Idempotency — the request identity, frozen

**v4 said "same payload" without saying what the payload is**, and the gap has a
concrete failure: with `date` omitted, the server picks the time, so a retry
picks a *different* time. If the normalised instant is part of the identity the
retry conflicts; if only `(user_id, edge_id)` is, then a changed `call_path` or
`actor` is silently accepted as the same request.

> **The canonical request is:**
> ```
> user_id · edge_id · call_path · actor · rule_version
> caller_date  — the CALLER's string, or the sentinel OMITTED
> ```
> **The caller's input, never the derived instant.** `OMITTED` is a value, so
> two date-less retries are identical requests.

**The correlation id is checked before a timestamp is generated.** On replay the
**stored** `confirmed_at` is returned, not a fresh one. A digest of the canonical
request is persisted so a true replay is distinguishable from a collision.

| case | result |
|---|---|
| same id, same canonical request | **the original success**, `replayed=True` |
| same id, different canonical request | **integrity conflict** |
| concurrent duplicates | **exactly one** mutation, one episode, one record |

**The id space is the user's REQUEST REGISTRY (amendment `0047/0008-request-registry`).** Every verb that takes a
`correlation_id` — `confirm()`, 0047's `add_reply()`, and any later verb that declares it — writes one
`request_registry` row `(user_id, correlation_id, verb, request_digest, result_ref, written_at)` **in its own
transaction**, under one `UNIQUE(user_id, correlation_id)`. **The registry is read first, before any read of live
edge state:** same id + same verb + same canonical request → the original result, reconstructed from `result_ref`;
the same id under a different verb or a different request → **integrity conflict**, naming the verb that holds it.
Concurrent duplicates across verbs commit exactly once (the UNIQUE). *v8:* `written_at` is the store's clock at the write, the same meaning for every verb; it is never the caller's date (`confirm()`'s `confirmed_at` is derived from the caller's date, §6c's metadata table), and nothing orders by it (§6f). A generated id takes a registry row like a
supplied one. Registry rows are erased with the user, and **replay ends at erasure**: a request whose record was
erased is not replayed, and is not recreated in order to replay it.

**Scope: `UNIQUE(user_id, correlation_id)`, not global.** v4 made it global, and
with a `≤64 char` format that permits ordinary short strings **one tenant can
consume identifiers another needs** — a cross-tenant denial path, and the
differing conflict behaviour leaks that an id exists elsewhere. **The request is
already principal-scoped and a cross-principal retry is never the same request.**

### The return shape (finding 4)

**`confirm()` returns a dict today** (`__init__.py:525`), and callers subscript
it, `json.dumps` it, and type-check it. **v4 replaced it with an undefined
`ConfirmationResult` and called that backward compatible.** It is not.

> **The contract stays a mapping:**
> ```python
> {"confirmed": str, "valid_from": str, "confirmed_at": str,
>  "correlation_id": str, "replayed": bool}
> ```
> Three existing keys keep their meaning; two are added. **On replay every value
> is reconstructed from the stored record**, not from an edge that may have
> changed since — otherwise "the original success" is not what is returned.

### Audit metadata is constrained, not merely discouraged (finding 4)

**v3 called the record content-free while two of its fields were free-form host
strings.** A host could put a whole sentence — or a memory — in `call_path`, and
the table would quietly become a content store.

| field | constraint | rejection |
|---|---|---|
| `call_path` | **closed enum** `ConfirmationCallPath` — no free text | unknown value raises |
| `correlation_id` | opaque, **≤ 64 chars**, `[A-Za-z0-9._:-]` | anything else raises |
| `user_id` · `edge_id` | opaque identifiers, unchanged | — |
| `confirmed_at` | **the normalised UTC instant**, not the caller's string — following the 0.4.7/0.4.8 date fixes | — |

**A policy that hosts should not put content in strings is not a constraint.**
This is the same free-form-metadata problem `actor` already demonstrated.

---

## 6d. The store contract, and what it costs every backend

**Finding 6: `Store` is a replaceable interface**, so this is not a SQLite
change.

> **Two obligations, and v4 only stated the first:**
>
> 1. **`confirm_edge` joins the interface as `@store_mutator`.** A backend that
>    cannot write the edge and the confirmation atomically **must raise**, not
>    degrade.
> 2. **`add_edge()` must compare the persisted prior state and reject
>    `needs_confirmation: True → False`** when replacing an edge of the same id.
>    It must also **reject a change of `user_id`** — ownership is not
>    transferable through the upsert path.

**Both are backend conformance tests (C10), not SQLite implementation details.**
A custom store could implement an atomic `confirm_edge()` and still accept a
reconstructed edge with the flag cleared through `add_edge()` — satisfying the
new signature while **violating the headline invariant.**

**SQLite:** a `confirmations` table, **`UNIQUE(user_id, correlation_id)`** (unchanged), indexed on `edge_id`, with
`origin` ∈ {`local`, `imported`, `restored`} and `recorded_correlation_id` (an imported or restored act's file id,
kept as evidence; its `correlation_id` is an internal `#act:` key, §6e); and a `request_registry` table,
`UNIQUE(user_id, correlation_id)` (the id space, §6c). The step is additive (its carrier inventory is the
amendment's §2: two tables, six columns on `confirmations`), backfills one `confirm` row per existing confirmation
(with the marker as its digest where the confirmation is already redacted), and leaves every legacy position
unknown.
*(The v5 line read: a `confirmations` table, `UNIQUE(user_id, correlation_id)`, indexed on `edge_id`, created by the
`0013` v1→v2 migration.) (Corrected
2026-08-03: this line said `UNIQUE(correlation_id)` — global — while §6c's
round-4 ruling is explicitly tenant-scoped, and said `CREATE TABLE IF NOT
EXISTS` — the model `0007` replaced. Found by `0013`'s first external review;
§6c was always the ruling, this line had drifted from it.)*

| question | answer |
|---|---|
| edge invalidated | records **retained** — the confirmation happened |
| edge physically removed | records removed with it |
| `forget_user()` | deletes them **and counts them** in its result, **and deletes the user's registry rows** |
| export / import | **carried, with `origin`**, under 0047 §4f's default-import / trusted-restore matrix: a default import writes `imported`; a trusted restore preserves the recorded origin, mapping `local → restored`, and never upgrades `imported`. **The request registry is never exported**: a request's replay belongs to the store it was made to. *(Was: excluded. Changed by this amendment; C11's export clause changes with it.)* |
| audit inspection | `confirmations_for(user_id, edge_id)` — read-only |

> **Implementation prerequisite: `specs/0007` must be accepted, and ship first
> or atomically with this.** Declared as `Spec-Requires: 0007` at the top, and
> **the gate enforces it** — a commit citing an `accepted` `0008` fails while
> `0007` is unresolved.

**⚠️ This is load-bearing, not administrative.** `CREATE TABLE IF NOT EXISTS` is
not a migration story: an older build opens the newer store, **ignores the table, and clears the flag
unaudited through the old reinforcement path** — defeating both of this spec's
guarantees at once. **Accepting `0008` alone would authorise that cut.**
**Fifth spec to need `0007`, which has never been reviewed.**

---

*§6e–§6g are the constructions both packages use (the owner hosted them here, 2026-10-12T22:56Z): act identity and import precedence, operation order, and the registry's digests and single erasure rule. They were reviewed as the amendment `0047/0008-request-registry` and folded at v6.*

## 6e. Act identity and import precedence (v6)

*Closes 0047 R2-02 and R2-04; 0044 R2-05 and R2-06.*

**Two key domains, disjoint by grammar.** A caller's request key has §6c's grammar (`[A-Za-z0-9._:-]{1,64}`, checked
at the host entry) and takes a registry row. An imported or restored act's own `correlation_id` is an INTERNAL key:
`#act:` followed by the first 32 hex digits of `sha256` over its `act_uid`. `#` is outside the caller grammar, so no
caller can ever present an internal key. `UNIQUE(user_id, correlation_id)` is unchanged: the two domains share the
column and cannot collide. Such an act writes **no registry row**, and keeps the ORIGINAL request's id (as the origin
store recorded it, copied from the file's `recorded_correlation_id` when present, otherwise from a `local` row's
`correlation_id`) in `recorded_correlation_id`, as evidence only.

**Portable identity.** `act_uid = (origin_store, origin_user, origin_act_id)`: the store that first recorded the act
(its minted `local_origin()`), the user it was recorded for there, and its row id there. It is set once, when a
`local` act is first exported, and carried unchanged on every later hop. A store never mints an `act_uid` for an act
it did not originate. *v7, how “set once” is met:* for a `local` act (a confirmation or a reply) every component is
fixed for the row's life: `origin_store` is this store's `local_origin()`, durable (0006 I11) and rewritten by no writer, and
`origin_user` and `origin_act_id` are the row's own `user_id` and `id`, which no writer updates. So the export
DERIVES the identity at every export rather than writing it at the first: the bytes are identical on every
export, and export stays read-only. A `local` row's `origin_*` columns stay NULL; only an `imported` or `restored`
act stores its identity. **If any writer ever updates a local act's `id` or `user_id`, or the store's origin, the
equivalence fails**, and the identity must be written at the first export instead. 0044's portable outcome rows use the same form:
`outcome_uid = (origin_store, origin_user, plan_id, edge_ref)`. **Both are serialised as a JSON array of strings
(UTF-8, no whitespace) before hashing**, never joined with a separator, so no two distinct tuples share a key.

**HELD means the STAGED UNION (v1.3).** An import is preflighted whole: the destination's rows ∪ every row of the
arriving unit, after user and id remapping. **A file row id that names two rows of one unit refuses the unit,
unless the two rows are byte-identical (one row twice)**: every reference in the unit is remapped through those ids,
so a repeated one would make a reference ambiguous (v1.3, dev's model finding). Every rule below that says an identity, a target or a challenge is
“held” reads that union, never the destination before the import and never the rows processed so far. Rows of one
unit therefore meet each other exactly as they meet the destination's, and the result does not depend on the order
of rows in the file. Across files it holds for ONE file or SUCCESSIVE COMPLETE SOURCE SNAPSHOTS only; an arbitrary
split of a history is not equivalent (§6f).

**The canonical comparison projection** of an act is: its `act_uid`; its portable edge reference after user and id
remapping; its verb or kind; its `target` as a portable reference; `actor`; `call_path`; `confirmed_at` as the
accepted record stores it (0008 §6b's normalized UTC value, never the caller's original string);
`recorded_correlation_id`; its CONTENT CARRIERS, `text` (a reply's) and `request_digest`; and its position (§6f). It
EXCLUDES every destination-internal field: row id, internal key, registry state, write time, and the **trust
label** (`origin`). *The label is the destination's own judgement, made at the act's first admission from the mode
and the file's label (§6d's matrix). It is not part of the act, and it legitimately differs from hop to hop: an
act exported as `local` is stored `restored` by a trusted restore. So it is never compared, and a replay never
changes it, up or down (v1.3: the reviewer's recorded-origin carrier, closed by this normalization instead of a new
column).* Two rows are the same act iff their `act_uid`s are equal.

**Treatment before equality (v1.3, R3-01).** The COVERAGE of an act's target is the set of carrier paths that the
redaction notices for that target, held or arriving, attest (0041's notice `fields`). *(v1.4) Every notice counts,
whatever its state (applied, pending, standing or arriving): coverage decides admission and equality only, and
writes nothing. What writes held content is an APPLIED notice (the 0041 amendment v1.5 §4).* The **canonical treated
projection** under that coverage replaces every covered content carrier with the marker, and leaves every other
field as it is. Then:
- Two rows with the same `act_uid` are an **EXACT REPLAY** iff their canonical treated projections are equal. So a
  treated held row and an untreated arriving copy of the same act are a replay whenever the coverage treats the
  difference, and an unchanged file imports again as a no-op.
- **The one authorized transition.** An arriving act whose content carriers are the marker, under a coverage that
  attests them, replaces a held untreated copy's carriers with the marker, and changes nothing else. This is the
  held row receiving the redaction its notice attests, written by 0041's notice pipeline in the import's
  transaction. **(v1.4) It happens only where the notice is APPLIED: in a trusted restore, or at the user's
  `confirm_notice`.** In a default import the held target's notice is PENDING, so the treated arrival is an exact
  replay under the coverage (a no-op) and no held byte changes. **Structural fields** (identity, edge, kind, target, actor, call path, `confirmed_at`,
  `recorded_correlation_id`, position) **are never changed by it**. A difference in any of them is a conflicting
  replay.
- **Coverage is all or nothing per row.** When an arriving act's target is redacted, the coverage must attest
  EVERY non-NULL content carrier of that row (a reply's `text` and `request_digest`, a confirmation's
  `request_digest`). A coverage that attests some of them but not all refuses the unit: an ARRIVING carrier the
  notice does not attest is never admitted in its name, and an immutable foreign notice is never enlarged (0041's
  rule). An unredacted target needs no coverage. *This rule governs what an arriving row may be ADMITTED as; the next
  bullet governs what happens to what is already held.*
- **An APPLIED notice treats what is HELD, too (v1.4: applied, never merely arriving in a default file).** A notice
  whose target the destination holds is applied in a trusted restore, in the import's transaction, **when the unit
  carries the target's record already showing the redaction** (v1.5). A unit carrying it UNREDACTED refuses the whole
  import, in either mode, and with no copy in the unit the notice is applied only if the held record already shows the
  redaction, pending otherwise (v1.6; the 0041 amendment v1.8 §4), and in a default
  import only when the user confirms it (`confirm_notice`; the 0041 amendment v1.5 §4, where a default import
  records it PENDING). **Applying it is a redaction BY THIS STORE**, total over the target's carriers under this
  store's own treatment map, exactly as a local redaction is: every held carrier of the target is treated, held acts
  that are NOT in the unit included, **even when the notice is older or partial and does not attest them**. What the
  application treated is attested by this store, never written into the foreign notice, whose body is unchanged.
  *Why total: 0041's binding rule says content-derived divergence “is not grounds to keep content the source says
  was redacted”, and a held reply that restates a redacted edge is exactly that content (0047 §1c). Why never on a
  default file's word: origin is unauthenticated (0006 Q4), so a default file's notice could name any held record;
  v1.3's rule here let it, which widened the 0041 defect (accepted 0041 as implemented on main since `8ea59e7`, in no release; the hotfix `98327c2` fixed it). The coverage that ADMITS an arriving row is
  still the notices' fields alone (the bullet above). The import is one transaction, so a unit refused for an
  uncovered arriving row applies no redaction either (v1.3, dev's model questions).* The authorized transition
  above is the same treatment, met by an arriving treated copy.

**Import precedence, per arriving act, over the staged union:**

| # | condition | result |
|---|---|---|
| 0 | mode `default`, and the act's `origin_store` is THIS store's `local_origin()` | **refused**: only a trusted restore of its own history may carry this store's origin |
| 1 | `act_uid` held, canonical treated projections equal (a second copy in the same unit included) | **no-op** (exact replay), or, in a trusted restore only, the authorized transition above (v1.4); it admits nothing new on its target |
| 2 | `act_uid` held, canonical treated projections differ (two differing copies in one unit included) | **whole-unit refusal** (a conflicting replay), naming the act |
| 3 | `act_uid` new, its target edge held in the destination BEFORE this import, mode `default` | **refused**: a new untrusted act over a held fact (0047 §4f). *The one rule that reads the destination alone, by design: an edge arriving in the same file is the act's own context, not a local fact* |
| 4 | otherwise | admitted, its label under §6d's matrix, written treated where the coverage attests its carriers |

Rule 1 is checked before rule 3, so importing an unchanged file again is a no-op instead of a refusal, and rule 3
still refuses a NEW act over a held fact. Rule 1 exempts only the replayed row: **every new act in the unit is
still validated**, against the union, by rule 3 and by §6f's chronology. **Edges, episodes and outcome links keep
0009's collision rule** (record-equal → skipped; differing → the whole import refused; a valid notice → 0041's
rule, as the 0041 amendment v1.5 binds it). **Migration outcomes travel under the same origin matrix as acts:** `local` and `restored` are proof,
`imported` is testimony, and a trusted restore never upgrades `imported` (0044 §4l).

## 6f. Operation order (v6)

*Closes 0047 R2-03; supplies 0044 R2-04's episode.*

**An act's position** is `pos = (origin_store, act_seq)`, with `origin_user` carried beside it as provenance.
`act_seq` comes from a **store-wide counter that is never reset**: one counter row per store, incremented by every act
write (`confirmations`, `replies`) inside the verb's own `BEGIN IMMEDIATE` transaction, which is
0029's V-TXN-ALLOC discipline. 0029's own counter is untouched. The position is recorded on the row at write,
exported, and carried unchanged on every hop. **0044's undo is not an act** (the owner, 2026-10-14): it is a verb of
the request registry (§6g), but it writes no act row, takes no `act_seq` and has no `act_uid`; 0044 §4g records it
on the outcome row, store-local, and no rule here orders it.
- Two positions are **ordered iff their `origin_store` is equal**, across users too. Otherwise they are
  **incomparable**.
- Nothing is inferred from a caller's date, from `written_at` or from any clock. No position is synthesized, and an
  act recorded before this column existed has an UNKNOWN position, which is incomparable.
- One verb writes one act, under the write lock, so no two acts share a position.
- **Why not 0029's `txn`:** it is allocated only when an edge event is journaled (1 + MAX over `edge_event`), so an
  act that changes no edge has none, and stamping one would hand the next edge transaction the same number. **Why
  never reset:** a MAX over live rows would restart after `forget_user`, and a recreated user would reissue
  positions an erased incarnation had already exported.
- A default import cannot claim this store's origin (§6e rule 0), so a default file's positions order acts only
  against acts of the same FOREIGN origin.
- The rules that need an order (0047 §4b and §4f) read `pos` and **refuse what they cannot order**.

**Chronology is validated over the MERGED HISTORY (v1.3, R3-02).** H is the staged union's acts (§6e), one row per
`act_uid`, with every `target` and resolve reference remapped and resolved inside H BEFORE any decision. Write
`a < b` when `a` and `b` have the same `origin_store`, both positions are known, and `a`'s `act_seq` is lower. A
challenge `c` is **open at an act `k`** of the same origin when `c < k` and no `resolve` of `c` in H satisfies
`r < k`. Then, for every confirmation `k` and every challenge `c` of the same edge in H **of which at least one is
admitted by this import** (rule 4), so that an incoming challenge is judged against a HELD confirmation as much as an
incoming confirmation against a held challenge:

| `c` and `k` | `c` in H | result |
|---|---|---|
| ordered, `k < c` | any | consistent: `k` was made before the challenge |
| ordered, `c < k` | open at `k` | **the unit is refused**: the history has a confirmation made under an unresolved challenge, which 0047 §4c forbids |
| ordered, `c < k` | resolved by an `r` with `r < k` | consistent: resolution before confirmation |
| not ordered (another origin, or an unknown position) | unresolved in H | **the unit is refused**: the order cannot be established |
| not ordered | resolved in H | consistent: the challenge is closed in the represented history, and no order is needed (v1.2's rule, now read over H) |

**Resolves are validated in H too.** A `resolve` names a `challenge` of the same edge in H. A challenge is resolved
at most once in H, so a second, different resolve refuses the unit. A resolve ordered BEFORE its own challenge
refuses the unit. **Two different acts at one position** (equal `origin_store` and `act_seq`, different
`act_uid`s) refuse the unit: §6f's counter never issues a position twice, so a tie is a forged or corrupted history.
Because H is a set, the result is the same whatever order the rows have in the file, and whether a history arrives
in one file or as SUCCESSIVE COMPLETE SOURCE SNAPSHOTS (each file a whole export at some moment, so each represents a
history the source could have had). A history the source store could legitimately have produced (challenge,
resolve, then confirm) is admitted that way, and a confirmation made under an unresolved challenge is refused.
*An ARBITRARY split is not equivalent, by design: a file carrying the challenge and the confirmation without the
resolve that came between them represents a confirmation under an unresolved challenge, and it is refused, although
the whole history in one file is admitted (dev's model counterexample, 2026-10-13).*

## 6g. The registry's digests and its single erasure rule (v6)

*Closes 0047 R2-05 with the 0041 amendment; 0044 R2-04 and R2-07.*

**The registry row gains `target_edge_id`**, the edge the request acted on, so an edge's redaction can find its
requests. A redaction REPLACES `request_registry.request_digest` for those rows, as it does
`confirmations.request_digest` and `replies.request_digest` (the 0041 amendment's per-candidate map, generated from
the table). After it, a retry under that id returns the TERMINAL `request_redacted`, whatever its payload: it does
not replay the original (the verifier is gone), and it admits no new act (the id stays held, so another verb still
conflicts). The registry step backfills an already-redacted confirmation's registry row with the marker. *v8:* for `confirm()`, whose return is §6c's frozen mapping, the terminal is a named raise, `RequestRedacted` (a `ValueError`), with its own census site.

**0044's undo is a verb of this registry, `undo`.** The id space is shared by `confirm`, `reply` and `undo`, in both
directions and under concurrency.

**Replay, and the terminal rule's precedence (v1.3).** A completed request replays from `result_ref` without
reading the edge, so it replays after the edge is retired or changed. **The terminal rule comes first, for every
verb (`confirm`, `reply`, `undo`):** once a redaction has replaced a request's digest, a retry under its id returns
`request_redacted` and nothing else. *v8:* it precedes the verb check as well: a request of ANOTHER verb under a redacted id is refused as `request_redacted`, naming the verb that holds the id, and is never admitted (the refusal that “another verb still conflicts” receives above). A retained `result_ref` never authorizes a replay, because replay requires
verifying the request against a digest that no longer exists. After user erasure the id is free again (the erasure
rule below), and a retry is a new request.

**One erasure rule, for both packages:** `forget_user` deletes, atomically with the user's records, the user's
registry rows (every verb), act rows, and 0044's `migration_outcome`, `migration_run` (the run rows, which name the
0018 amendment's `op_id`), `arity_inventory` and `refusal_inventory` rows, and 0022's `source_revocations` rows (2026-10-29, the owner); every such table joins `_ERASE_TABLES`. A census gate holds it, by property: every table with a `user_id` column is in `_ERASE_TABLES`, and every table in it has one (`tests/test_0022_erasure.py`).
*The 0018 amendment's admission record, `migration_op`, is NOT per-user and holds no user content (an id, a mode, a
digest of declarations, a time), so erasure has nothing of it to remove (v1.3, corrected before adoption).* Replay and 0044's once-per-plan
end at erasure: a retry after erasure is a NEW request, and nothing erased is recreated in order to replay. The
store-wide counter is NOT erased, so a recreated user's acts never reuse a position.

### Regimes (v6, amendment `0047/0008-request-registry`)

| regime | behaviour |
|---|---|
| a store with confirmations only (today's) | the migration backfills their ids; every existing replay still replays; a reply cannot reuse a pre-upgrade confirm id |
| a host that never supplies ids | generated ids take registry rows; no replay protection, as 0008 states |
| default import of a file with confirmations | written `imported`; no registry rows; `g(e)` unaffected |
| trusted restore of own history | `local → restored`; `imported` stays `imported`; no registry rows |
| older build opening an upgraded store | refused by 0007's version gate, as for any schema step |

---

## 7. Failure modes and reversibility

**Failure mode is a caveat that outstays its welcome** — a fact stays marked
`[possibly stale]` until someone calls `confirm()`. Additive and visible,
against silent removal of a caveat that should have stayed.

**Reversibility, corrected.** v1 said *"no data is written or destroyed;
existing values stay exactly as they are"* and that was wrong in a way that
matters:

> **A new `confirmations` table and a new `Store` method** (§6b, §6d).
> `Memory.confirm()` gains two defaulted parameters — **additive, existing
> callers unaffected.** No existing table or field changes and no stored edge or
> episode is migrated. **The implementation is rollbackable, but behaviour
> during deployment changes persisted edge state**,
> and reverting does not reconstruct the counterfactual the old rule would have
> produced.

Before, reinforcement wrote `needs_confirmation=False`; after, it leaves `True`
persisted. **After a rollback we cannot tell which flags the old behaviour would
have cleared during the intervening period** — the safer flags simply remain set
until a later `confirm()` clears them — **reinforcement no longer changes the
flag at all.** **That is the
right direction to fail, and it is still not "no data changes".**


**v6 (the request registry):** A verb that cannot write its registry row fails whole, and its act is not written (0008 C7's all-or-nothing property, extended). The migration is additive; its backfill is derived from existing rows and can be re-derived.

## 8. Claims and limits

**Claim, and it is one sentence on purpose:** *only `Store.confirm_edge()` may
transition an **existing stored edge** from `needs_confirmation = True` to
`False`.*

**"Transition on an existing edge" is precise on purpose.** New edges are
created with `False`, and import and deserialisation load `False` values — those
are not clearing events, and v3's wording implied every `False` should have a
confirmation record behind it.

**Liveness is explicitly out of claim.** §3d measures a second way to defeat the
warning — repeated restatement prevents the flag being set at all — and **this
spec does not fix it.** `specs/0012` owns it. **A reader must not take this
spec as closing the staleness boundary; it closes one of its two doors.**

**v2 claimed both doors and the second external review rejected the mechanism**
— it used supersession authority as a proxy for renewed observation, which is
this spec's own error one level up.

**What this does NOT establish:**

- **Not that a user confirmed anything.** veracium sees a call, not a person.
  **The guarantee is conditional on the host obligations in §6a** — and if the
  host exposes `confirm()` to a model, this spec buys nothing.
- **Not per-author staleness.** `needs_confirmation` is one boolean for the
  whole edge; `0002` Q4 would dissolve this structurally rather than fence it.
- **Not why the flag was set.** `expire()`'s CONFIRM behaviour is untouched.
- **Not anything about liveness.** §3d's bypass is open and owned by `0012`.
  **v2 claimed this and the mechanism was rejected**; nothing replaced it here.


**v6 (the request registry):**

**Claimed:** within one store, one user's correlation ids name at most one request across every verb that takes
them. A replay returns that request's original result. An act's origin survives export and restore without
upgrading.
**NOT claimed:** replay across stores (the registry is not exported, by design). Proof that a `restored` act was
genuinely made by the user: it rests on 0005's explicit trust assumption for the restore, as 0047 §4f states.

## Review closure

**Set `accepted` 2026-08-02 19:27 UTC by dev, under `PROCESS.md` §4a: external review is
required and dev sets the status once the review's comments are satisfied.**

**Four external rounds. The clearing rule was approved in all four**; every
deferral was about the contract around it. Every finding raised is closed below
with something openable — a section, an invariant, a test, or a commit.

**What `accepted` does and does not mean here.** It authorises implementation of
**this spec's rule**. It does **not** mean the code can land: `Spec-Requires:
0007` is enforced by the gate, and `0007` is `draft`, so a commit citing this
spec still fails. **That is the intended outcome** — the invariant is settled,
the prerequisite is not.

### Round 1 — 7 findings

| # | finding | closed by |
|---|---|---|
| 1 | reinforcement can prevent the flag being set | §3d, **measured**; owner `specs/0012` |
| 2 | matrix conflates clearing with liveness | §3 — two columns |
| 3 | C1 tested only `EvidenceAuthor` | C1 — behavioural + runtime + AST |
| 4 | `confirm()` is a call path, not proof | §6a host obligations |
| 5 | field contract overstated the reaffirming party | §2 row, narrowed |
| 6 | reversibility claim incorrect | §7 |
| 7 | audit/rate policy unresolved | §6b; C-Q1 resolved |

### Round 2 — 11 findings

| # | finding | closed by |
|---|---|---|
| 1–3, 7 | authority is not entitlement to renew; contradicts the matrix; `0003` not accepted | **rule withdrawn**; `specs/0012` §2 |
| 4–6 | incoming-evidence representation · §4 contradiction · the withdrawn rule's test coverage | `specs/0012` §3 — the invariant those findings attached to no longer exists here |
| 8 | AST writer check bypassable | C1 — runtime guard, AST demoted |
| 9–10 | audit atomicity and schema | §6b, §6d |
| 11 | `call_path` undefined | §6c — closed enum |

### Round 3 — 8 findings

| # | finding | closed by |
|---|---|---|
| 1 | two incompatible mechanisms | `Store.confirm_edge()` sole primitive; context parameter removed |
| 2 | transaction omitted other effects | §6b table — flag, `observed_at`, `confidence`, episode, record |
| 3 | public API undefined | §6c |
| 4 | "content-free" fields were free-form | §6c constraints |
| 5 | replay under unknown commit | §6c idempotency |
| 6 | store contract incomplete | §6d |
| 7 | C4's boundary wrong | C4 — maintenance entry points, not the mutator surface |
| 8 | claim not transition-specific | §8 |

### Round 4 — 9 findings

| # | finding | closed by |
|---|---|---|
| 1 | signature could not write the episode | `actor` in the request; `ConfirmationActor` closed enum |
| 2 | idempotency identity undefined | §6c — canonical request, `OMITTED` sentinel |
| 3 | global correlation ids unsafe | `UNIQUE(user_id, correlation_id)` |
| 4 | return not backward compatible | §6c — mapping contract retained |
| 5 | storage contract untested | **C7–C12** |
| 6 | `add_edge()` guard not formalised | §6d — backend conformance, C10 |
| 7 | `0007` prerequisite | `Spec-Requires: 0007`, **gate-enforced** (`feb81ff`) |
| 8 | manifest claimed a future state | C4 — future tense |
| 9 | review metadata drifted | header row states no counts |

### What remains open, and is not claimed

- **The §3d liveness bypass** — measured, unfixed, `specs/0012`.
- **Nothing is implemented.** C1–C12 are unwritten; the source still clears on
  same-author reinforcement and the historical reproducer is `xfail`.
- **The guarantee is conditional** on the §6a host obligations.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~**C-Q1**~~ | **RESOLVED in §6b, not deferred.** Every `confirm()` writes a content-free audit record; repeated confirmation is allowed without limit, because veracium cannot distinguish a legitimate re-affirmation from an automated one and **a guessed limit would substitute our judgement for the host's while still not detecting misuse.** The record makes misuse visible, which is the part we can provide. | resolved | dev | — |
| ~~C-Q2~~ | **RULED 2026-08-01 (Quentin): no release-note correction.** The 0.4.5 note is accurate as written — cross-author clearing *was* closed. The residual same-class case is this spec's subject and ships as its own fix. **Not blocking.** | resolved | Quentin | — |

## Annotation — act portability as T11b implements it (2026-10-20; every row above is kept as written)

*Append-only. The accepted text above this section is byte-for-byte the text before this annotation was appended,
sha256 `473cfdce4079d45b9122c8b01c464c272f080c92722c6463ed48597d00464b28`. This annotation records two DESIGN CHANGES BY
RULING (the owner, Quentin, 2026-10-20, ledger `1899b67`), not a version of this spec, and R-II's brief names them as
such; and the readings T11b's implementation took where the frozen text left a choice. Implemented in T11b (dev's build
note sha16 d54b768f with addendum 1 sha16 7a820236; research's stage-1 read `READ-T11b-stage1.md`, research
`48750ecc`). Each narrowed sentence is quoted, then its reading.*

**R-D6, the act remap namespace (the owner's ruling).**
- §6e: "It is set once, when a `local` act is first exported, and carried unchanged on every later hop. A store never
  mints an `act_uid` for an act it did not originate" (L597–L599), §6f: "The position is recorded on the row at write,
  exported, and carried unchanged on every hop" (L694–L695), and §6e rule 0, "mode `default`, and the act's
  `origin_store` is THIS store's `local_origin()`" (L674) → unchanged on every hop EXCEPT a cross-user remap
  (`import_memory(..., user_id=)`), which moves each act into that import's REMAP NAMESPACE: `origin_store` becomes
  `"remap:"` + the first 32 hex digits of the canonical hash of (origin store, destination user, the import's operation
  id), `origin_user` the destination user, `origin_act_id` and `act_seq` kept; a resolve's target maps the same way.
  Rule 0 reads the act AS ADMITTED. Why: outcomes re-mint only user and edge (0044's annotation, L788–L790) because
  nothing orders them; an act also has a POSITION, and a second remapped copy at the source's positions would be two
  acts at one position, which §6f refuses. With the namespace a copy's acts duplicate exactly when its edges do, and the
  copy keeps its own internal order. **Limit, stated:** in a copy, the source store is readable only as the hash.

**R-M1, legacy order in a trusted restore (the owner's ruling).**
- §6f: "No position is synthesized, and an act recorded before this column existed has an UNKNOWN position, which is
  incomparable" (L700–L701) → in a TRUSTED RESTORE only, between two acts of one origin both recorded `local` or
  `restored`, an unknown position precedes every known one. Basis: §2a's "no legacy act receives a value" (L101) — the
  counter starts at the v16 step, so every unknown-position act of an origin predates every known one. Testimony
  (`imported`) stays incomparable (a relayed file could have nulled its position), two unknown positions stay
  incomparable, and a default import is unchanged. So a store's own backup holding a legacy confirmation and a LATER
  open challenge restores; its default import is refused WHOLE, at §6f's width (L724: "the unit is refused"), nothing
  written. It departs from IO-II-4's "not by inventing an order" in exactly this case.

**Readings T11b took (inside the frozen rules).**
- §6e's projection "EXCLUDES … write time" (L622) and 0047 §4b's "`written_at` is a local clock that does not travel as
  an order" (0047 L191–L192) with 0047 §4d's display order "challenges by `(written_at, id)`" (0047 L225) → a reply's
  `written_at` TRAVELS, is re-rendered as canonical UTC, is never compared and is never an OPERATION order; it is the
  DISPLAY order, and an arriving value later than the import's one clock read is stored as that read (research's M3),
  so no file can date a challenge ahead of a later local one. `confirmed_at` is in the projection and is canonicalised
  the same way before comparison and storage; an arriving time without a timezone refuses.
- §6e's "A file row id that names two rows of one unit refuses the unit" (L610–L611) → the wire carries no row id
  (destination-internal), so an act's file identity is its `act_uid` and the rule is rule 2 on one uid.
- 0047 §4b's "A `resolve` names ONE `challenge` row of the SAME edge, written by the same subject label" (0047 L177) →
  the actor may differ, as T10a's `add_reply` already reads it (the owner's ruling, 2026-10-19, ledger 11:56 UTC:
  labels are unauthenticated until 0050); import follows the writer.
- 0045 §4f's "trusted restore checks it refers to an episode in destination ∪ file" (0045 L292) → reduced to a SHAPE
  check (research's M4): a store's own backup holds a `src` whose episode was consumed by consolidation (alive only in a
  survivor's lineage) or deleted, and the owner's T9 F1(b) ruling reads a deleted source as naming nothing. A dangling
  `src` is admitted.
- 0045 §4e's "trusted restore: as recorded" with §6e's exclusion of the trust label → a restore over a held edge
  compares the grounding axis (a difference refuses, INV-G13), except where the held `attv` is `default-import`, this
  store's own judgement at a default import, which is kept and listed (research's M2).
- An act on a record a default import refuses PER RECORD (0037 §4e) is refused with it and counted, not treated as an
  orphan (0047 INV-R11), which would refuse the whole file. Rule 0 does not judge an act refused with its record: the
  drop runs first, and nothing of the act is written (research's T11b stage-2 A2).
